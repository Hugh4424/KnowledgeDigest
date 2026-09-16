"""Freeze, judge, and replay the Task9 K3 acceptance boundary offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import time
import uuid
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import ValidationError
from .kb_publish import _copy_file_no_follow, kb_tree_hash, kb_write_lock, sidecar_path


FREEZE_SCHEMA_VERSION = "task9-freeze-manifest.v1"
REQUIRED_INPUT_MD_COUNT = 89
SNAPSHOT_ROOTS = {
    "input": "input",
    "release4": "release4",
    "comparison": "comparison",
}
FREEZE_EXCLUSIONS = {
    "skip_dotfiles": True,
    "skip_gbrain": True,
    "rules": ["path components beginning with '.'", "path components named '_gbrain'"],
}
INPUT_POLICY = {"extension": ".md", "required_file_count": REQUIRED_INPUT_MD_COUNT}
_FROZEN_ID = re.compile(r"[0-9a-f]{64}\Z")
JUDGE_RULES_VERSION = "k3-v1"
QUESTION_GENERATOR_VERSION = "k3-question-generator-v1"
COMPARISON_MAPPING_SCHEMA_VERSION = "task9-comparison-mapping.v1"
MAPPED_QUESTION_GENERATOR_VERSION = "k3-question-generator-mapped-v1"
QUESTION_TEMPLATES = ("{} 是什么", "{} 怎么配置", "{} 的参数有哪些")
QUESTION_GENERATOR_POLICY = {
    "version": QUESTION_GENERATOR_VERSION,
    "templates": list(QUESTION_TEMPLATES),
    "module_rule": "products/<product>/<module>/; page parent is the module",
    "questions_per_module": 2,
    "page_order": "relative POSIX path sorted by UTF-8 bytes",
    "template_index": "i mod 3",
    "fallbacks": ["filename slug", "page narrative first sentence"],
}
MAPPED_QUESTION_GENERATOR_POLICY = {
    "version": MAPPED_QUESTION_GENERATOR_VERSION,
    "base_generator_version": QUESTION_GENERATOR_VERSION,
    "templates": list(QUESTION_TEMPLATES),
    "module_rule": "comparison mapping logical_module; target page remains the published page",
    "questions_per_module": 2,
    "page_order": "comparison page, source id, then target page sorted by UTF-8 bytes",
    "target_page_reuse": "one question per target page",
    "source_binding": "source_id, source_uri, and source_sha256 must match the current freeze",
}


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


QUESTION_GENERATOR_RULES_SHA256 = _json_sha256(QUESTION_GENERATOR_POLICY)
MAPPED_QUESTION_GENERATOR_RULES_SHA256 = _json_sha256(MAPPED_QUESTION_GENERATOR_POLICY)


def _utf8_key(value: str) -> bytes:
    return value.encode("utf-8")


def _validate_source(path: Path, field: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise ValidationError("freeze", path, f"{field} must be an existing regular directory")
    return path


def _excluded_name(name: str) -> bool:
    return name.startswith(".") or name == "_gbrain"


def _relative_is_safe(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if any(ord(character) < 32 or ord(character) == 127 or character in "\u2028\u2029" for character in value):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in path.parts)
        and value == path.as_posix()
    )


def _walk_files(root: Path, role: str, *, reject_excluded: bool) -> list[Path]:
    """Walk regular files without following symlinks."""
    files: list[Path] = []
    for directory, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        kept_directories: list[str] = []
        for name in sorted(directory_names, key=_utf8_key):
            candidate = directory_path / name
            if candidate.is_symlink():
                raise ValidationError("freeze", candidate, "symbolic links are not allowed in a snapshot")
            if _excluded_name(name):
                if reject_excluded:
                    raise ValidationError("freeze-preflight", candidate, "excluded path is present in a snapshot")
                continue
            if not candidate.is_dir():
                raise ValidationError("freeze", candidate, "snapshot contains a non-directory entry")
            kept_directories.append(name)
        directory_names[:] = kept_directories

        for name in sorted(file_names, key=_utf8_key):
            candidate = directory_path / name
            if candidate.is_symlink():
                raise ValidationError("freeze", candidate, "symbolic links are not allowed in a snapshot")
            if _excluded_name(name):
                if reject_excluded:
                    raise ValidationError("freeze-preflight", candidate, "excluded path is present in a snapshot")
                continue
            if not candidate.is_file():
                raise ValidationError("freeze", candidate, "snapshot contains a non-regular file")
            if role == "input" and candidate.suffix != ".md":
                if reject_excluded:
                    raise ValidationError("freeze-preflight", candidate, "input snapshot contains a non-Markdown file")
                continue
            files.append(candidate)
    return sorted(files, key=lambda item: _utf8_key(item.relative_to(root).as_posix()))


def _source_files(source: Path, role: str) -> list[tuple[str, Path]]:
    return [(path.relative_to(source).as_posix(), path) for path in _walk_files(source, role, reject_excluded=False)]


def _snapshot_files(root: Path, role: str) -> list[Path]:
    return _walk_files(root, role, reject_excluded=True)


def _file_records(root: Path, role: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in _snapshot_files(root, role):
        relative = path.relative_to(root).as_posix()
        records.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return records


def _copy_snapshot(entries: Sequence[tuple[str, Path]], destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for relative, source in entries:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        _copy_file_no_follow(source, target, stage="freeze")


def _snapshot_descriptor(role: str, source: Path, destination: Path) -> dict[str, object]:
    records = _file_records(destination, role)
    return {
        "root": SNAPSHOT_ROOTS[role],
        "source_path": str(source.resolve()),
        "file_count": len(records),
        "files": records,
        "tree_hash": kb_tree_hash(destination),
    }


def _identity_payload(snapshots: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    return {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "input_policy": INPUT_POLICY,
        "exclusions": FREEZE_EXCLUSIONS,
        "question_generator": {
            **QUESTION_GENERATOR_POLICY,
            "rules_sha256": QUESTION_GENERATOR_RULES_SHA256,
        },
        "snapshots": {
            role: {
                "root": snapshots[role].get("root"),
                "file_count": snapshots[role].get("file_count"),
                "files": snapshots[role].get("files"),
                "tree_hash": snapshots[role].get("tree_hash"),
            }
            for role in SNAPSHOT_ROOTS
        },
    }


def _manifest_sha256(manifest: Mapping[str, object]) -> str:
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    return _json_sha256(unsigned)


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _resolved_path(path: Path) -> Path:
    try:
        return Path(path).resolve(strict=False)
    except OSError:
        return Path(path).absolute()


def _validate_output_path(output: Path, protected_roots: Sequence[Path]) -> None:
    """Keep acceptance result writes outside all inputs being fingerprinted."""
    if output.is_symlink():
        raise ValidationError("accept", output, "output path must not be a symbolic link")
    candidate = _resolved_path(output)
    for root in protected_roots:
        protected = _resolved_path(root)
        if candidate == protected or protected in candidate.parents:
            raise ValidationError("accept", output, "output path is inside protected acceptance state")


def _freeze_result(frozen_dir: Path, manifest: Mapping[str, object]) -> dict[str, object]:
    snapshots = manifest.get("snapshots")
    file_counts = {
        role: snapshots[role].get("file_count")
        for role in SNAPSHOT_ROOTS
        if isinstance(snapshots, Mapping) and isinstance(snapshots.get(role), Mapping)
    }
    return {
        "status": "frozen",
        "frozen_id": manifest.get("frozen_id"),
        "freeze_dir": str(frozen_dir),
        "manifest_path": str(frozen_dir / "manifest.json"),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "file_counts": file_counts,
    }


def freeze(
    input_dir: Path | str | None = None,
    release4_dir: Path | str | None = None,
    comparison_dir: Path | str | None = None,
    freeze_root: Path | str | None = None,
    *,
    output_dir: Path | str | None = None,
    before_dir: Path | str | None = None,
    comparison_kb_dir: Path | str | None = None,
) -> dict[str, object]:
    """Create the three content snapshots and their deterministic manifest."""
    if release4_dir is None:
        release4_dir = before_dir
    if comparison_dir is None:
        comparison_dir = comparison_kb_dir
    if freeze_root is None:
        freeze_root = output_dir
    if input_dir is None or release4_dir is None or comparison_dir is None:
        raise ValidationError("freeze", "arguments", "input, release4, comparison, and output roots are required")

    sources = {
        "input": _validate_source(Path(input_dir), "input source"),
        "release4": _validate_source(Path(release4_dir), "release4 source"),
        "comparison": _validate_source(Path(comparison_dir), "comparison source"),
    }
    source_entries = {role: _source_files(source, role) for role, source in sources.items()}
    if len(source_entries["input"]) != REQUIRED_INPUT_MD_COUNT:
        raise ValidationError(
            "freeze",
            sources["input"],
            f"input source must contain exactly {REQUIRED_INPUT_MD_COUNT} .md files",
        )

    if freeze_root is None:
        freeze_root = sources["comparison"].parent / "freeze"
    output_root = Path(freeze_root)
    if output_root.is_symlink():
        raise ValidationError("freeze", output_root, "freeze root must not be a symbolic link")
    output_resolved = output_root.resolve()
    for role, source in sources.items():
        source_resolved = source.resolve()
        if output_resolved == source_resolved or source_resolved in output_resolved.parents:
            raise ValidationError("freeze", output_root, f"freeze root must be outside the {role} source")
    output_root.mkdir(parents=True, exist_ok=True)
    if not output_root.is_dir():
        raise ValidationError("freeze", output_root, "freeze root must be a directory")

    temporary = output_root / f".{os.getpid()}.freeze.tmp"
    if temporary.exists() or temporary.is_symlink():
        raise ValidationError("freeze", temporary, "temporary freeze path already exists")
    temporary.mkdir()
    try:
        for role, source in sources.items():
            _copy_snapshot(source_entries[role], temporary / SNAPSHOT_ROOTS[role])

        descriptors = {
            role: _snapshot_descriptor(role, source, temporary / SNAPSHOT_ROOTS[role])
            for role, source in sources.items()
        }
        identity = _identity_payload(descriptors)
        frozen_id = _json_sha256(identity)
        manifest: dict[str, object] = {
            **identity,
            "snapshots": descriptors,
            "frozen_id": frozen_id,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        manifest["manifest_sha256"] = _manifest_sha256(manifest)
        _atomic_write_json(temporary / "manifest.json", manifest)

        frozen_dir = output_root / frozen_id
        if frozen_dir.exists() or frozen_dir.is_symlink():
            existing = _verify_freeze_directory(frozen_dir, frozen_id, {})
            if existing["status"] != "ready":
                raise ValidationError("freeze", frozen_dir, "existing frozen snapshot is not valid")
            return _freeze_result(frozen_dir, existing["manifest"])
        os.replace(temporary, frozen_dir)
        return _freeze_result(frozen_dir, manifest)
    finally:
        if temporary.exists() or temporary.is_symlink():
            shutil.rmtree(temporary, ignore_errors=True)


def _blocked(
    frozen_id: str | None,
    reasons: Sequence[str],
    *,
    manifest_path: Path | None = None,
    reason_code: str = "freeze_preflight_blocked",
    message: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "status": "blocked",
        "reason_code": reason_code,
        "reasons": list(dict.fromkeys(str(reason) for reason in reasons)),
        "frozen_id": frozen_id,
        "results": [],
        "question_results": [],
        "conclusions": [],
    }
    if manifest_path is not None:
        result["manifest_path"] = str(manifest_path)
    if message is not None:
        result["message"] = message
    return result


def _resolve_freeze_dir(
    frozen_id: str | Path,
    freeze_root: Path | str | None,
    *,
    freeze_dir: Path | str | None = None,
    target_kb: Path | str | None = None,
) -> tuple[str, Path]:
    raw_id = str(frozen_id)
    locator = None
    if not _FROZEN_ID.fullmatch(raw_id):
        candidate = Path(raw_id)
        if candidate.is_file() or candidate.is_dir():
            locator = candidate
    if locator is not None:
        if locator.name == "manifest.json":
            return locator.parent.name, locator.parent
        if locator.is_dir() and (locator / "manifest.json").exists():
            return locator.name, locator

    requested_id = raw_id
    if freeze_dir is not None:
        return requested_id, Path(freeze_dir)

    candidates: list[Path] = []
    if freeze_root is not None:
        root = Path(freeze_root)
        if root.name == requested_id and (root / "manifest.json").exists():
            candidates.append(root)
        candidates.append(root / requested_id)
    if target_kb is not None:
        target = Path(target_kb)
        candidates.append(sidecar_path(target) / "freeze" / requested_id)
    candidates.append(Path("freeze") / requested_id)

    for candidate in candidates:
        if candidate.exists() or candidate.is_symlink():
            return requested_id, candidate
    return requested_id, candidates[0]


def _cached_tree_hash(root: Path, cache: MutableMapping[str, str]) -> str:
    key = str(root.resolve())
    if key not in cache:
        cache[key] = kb_tree_hash(root)
    return cache[key]


def _declared_records(value: object, role: str) -> tuple[list[dict[str, str]], list[str]]:
    if not isinstance(value, list):
        return [], [f"{role}.files"]
    records: list[dict[str, str]] = []
    reasons: list[str] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            reasons.append(f"{role}.files[{index}]")
            continue
        path = row.get("path")
        digest = row.get("sha256")
        if not _relative_is_safe(path):
            reasons.append(f"{role}.files[{index}].path")
            continue
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            reasons.append(f"{role}.files[{index}].sha256")
            continue
        records.append({"path": path, "sha256": digest})
    paths = [row["path"] for row in records]
    if paths != sorted(paths, key=_utf8_key):
        reasons.append(f"{role}.files.order")
    if len(set(paths)) != len(paths):
        reasons.append(f"{role}.files.duplicate_path")
    return records, reasons


def _verify_freeze_directory(
    frozen_dir: Path,
    requested_id: str,
    tree_hash_cache: MutableMapping[str, str],
) -> dict[str, object]:
    manifest_path = frozen_dir / "manifest.json"
    if frozen_dir.is_symlink() or not frozen_dir.is_dir():
        return _blocked(requested_id, ["freeze_directory_missing"], manifest_path=manifest_path)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return _blocked(requested_id, ["manifest_missing"], manifest_path=manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _blocked(requested_id, ["manifest_invalid"], manifest_path=manifest_path)
    if not isinstance(manifest, dict):
        return _blocked(requested_id, ["manifest_not_object"], manifest_path=manifest_path)

    reasons: list[str] = []
    if manifest.get("schema_version") != FREEZE_SCHEMA_VERSION:
        reasons.append("schema_version")
    if manifest.get("frozen_id") != requested_id:
        reasons.append("frozen_id")
    if manifest.get("manifest_sha256") != _manifest_sha256(manifest):
        reasons.append("manifest_sha256")
    if manifest.get("exclusions") != FREEZE_EXCLUSIONS:
        reasons.append("exclusions")
    if manifest.get("input_policy") != INPUT_POLICY:
        reasons.append("input_policy")
    if manifest.get("question_generator") != {
        **QUESTION_GENERATOR_POLICY,
        "rules_sha256": QUESTION_GENERATOR_RULES_SHA256,
    }:
        reasons.append("question_generator")
    if not isinstance(manifest.get("generated_at"), str) or not manifest["generated_at"].strip():
        reasons.append("generated_at")

    expected_entries = {"manifest.json", *SNAPSHOT_ROOTS.values()}
    actual_entries = {entry.name for entry in frozen_dir.iterdir()}
    if actual_entries != expected_entries:
        reasons.append("freeze_path_whitelist")

    snapshots = manifest.get("snapshots")
    if not isinstance(snapshots, Mapping):
        reasons.append("snapshots")
        return _blocked(requested_id, reasons, manifest_path=manifest_path)

    actual_hashes: dict[str, str] = {}
    for role, expected_root in SNAPSHOT_ROOTS.items():
        descriptor = snapshots.get(role)
        if not isinstance(descriptor, Mapping):
            reasons.append(f"{role}.descriptor")
            continue
        if descriptor.get("root") != expected_root:
            reasons.append(f"{role}.root")
        if not isinstance(descriptor.get("source_path"), str) or not descriptor["source_path"].strip():
            reasons.append(f"{role}.source_path")
        file_count = descriptor.get("file_count")
        if isinstance(file_count, bool) or not isinstance(file_count, int) or file_count < 0:
            reasons.append(f"{role}.file_count")
        snapshot_root = frozen_dir / expected_root
        if snapshot_root.is_symlink() or not snapshot_root.is_dir():
            reasons.append(f"{role}.snapshot_missing")
            continue
        try:
            actual_records = _file_records(snapshot_root, role)
        except (OSError, ValueError) as error:
            reasons.append(f"{role}.snapshot_invalid:{error}")
            continue
        declared_records, record_reasons = _declared_records(descriptor.get("files"), role)
        reasons.extend(record_reasons)
        if actual_records != declared_records:
            declared_by_path = {row["path"]: row["sha256"] for row in declared_records}
            if [row["path"] for row in actual_records] != list(declared_by_path):
                reasons.append(f"{role}.file_set")
            for row in actual_records:
                if declared_by_path.get(row["path"]) != row["sha256"]:
                    reasons.append(f"{role}.file_hash:{row['path']}")
        if descriptor.get("file_count") != len(actual_records):
            reasons.append(f"{role}.file_count")
        if role == "input" and len(actual_records) != REQUIRED_INPUT_MD_COUNT:
            reasons.append("input.required_file_count")
        try:
            actual_hash = _cached_tree_hash(snapshot_root, tree_hash_cache)
            actual_hashes[role] = actual_hash
            if descriptor.get("tree_hash") != actual_hash:
                reasons.append(f"{role}.tree_hash")
        except (OSError, ValueError) as error:
            reasons.append(f"{role}.tree_hash:{error}")

    try:
        identity = _identity_payload(snapshots)  # type: ignore[arg-type]
        if _json_sha256(identity) != requested_id:
            reasons.append("frozen_id_recalculation")
    except (KeyError, TypeError):
        reasons.append("frozen_id_recalculation")

    if reasons:
        return _blocked(requested_id, reasons, manifest_path=manifest_path)
    return {
        "status": "ready",
        "frozen_id": requested_id,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "tree_hashes": actual_hashes,
        "manifest": manifest,
        "results": [],
        "question_results": [],
        "conclusions": [],
    }


def preflight(
    frozen_id: str | Path,
    freeze_root: Path | str | None = None,
    *,
    freeze_dir: Path | str | None = None,
    target_kb: Path | str | None = None,
    tree_hash_cache: MutableMapping[str, str] | None = None,
) -> dict[str, object]:
    """Validate a frozen package without consulting any live comparison path."""
    requested_id, frozen_dir = _resolve_freeze_dir(
        frozen_id,
        freeze_root,
        freeze_dir=freeze_dir,
        target_kb=target_kb,
    )
    if not _FROZEN_ID.fullmatch(requested_id):
        return _blocked(requested_id, ["frozen_id_format"], manifest_path=frozen_dir / "manifest.json")
    cache = tree_hash_cache if tree_hash_cache is not None else {}
    return _verify_freeze_directory(frozen_dir, requested_id, cache)


def _target_version(kb_dir: Path) -> Path | None:
    kb_dir = Path(kb_dir).absolute()
    current = kb_dir / "current"
    if not current.is_symlink():
        return None
    target = current.resolve(strict=True)
    expected_parent = sidecar_path(kb_dir) / "versions"
    if target.parent != expected_parent or not target.is_dir():
        raise ValidationError("accept", current, "current pointer does not target a version directory")
    return target


def _field(value: object, name: str, default: object = None) -> object:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _frontmatter_values(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, object] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, raw = line.partition(":")
        if not separator or not key.strip():
            continue
        raw = raw.strip().strip("'\"")
        result[key.strip()] = raw
    return result


def _page_text(page: object) -> str:
    if isinstance(page, Path):
        return page.read_text(encoding="utf-8")
    for name in ("text", "content", "body", "answer"):
        value = _field(page, name)
        if isinstance(value, str):
            return value
    return ""


def _page_path(page: object, fallback: str | None = None) -> str | None:
    for name in ("page_path", "path", "expected_page", "entry_path"):
        value = _field(page, name)
        if isinstance(value, str) and value.strip():
            return value.strip().replace("\\", "/")
    return fallback


def _page_title(page: object, text: str, path: str) -> str:
    for name in ("title", "page_title", "name"):
        value = _field(page, name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    frontmatter = _frontmatter_values(text)
    title = frontmatter.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    for line in text.splitlines():
        stripped = re.sub(r"^\s*<a[^>]*>\s*</a>\s*$", "", line).strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                return heading
    return PurePosixPath(path).stem


def _first_sentence(text: str) -> str:
    in_frontmatter = False
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not lines and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue
        if not stripped or stripped.startswith("#") or stripped.startswith("<a "):
            continue
        if stripped.startswith(("来源：", "Source:", "## Provenance")):
            continue
        lines.append(re.sub(r"^[-*>]\s*", "", stripped))
    text_value = " ".join(lines).strip()
    if not text_value:
        return ""
    match = re.search(r"[。！？!?；;.]", text_value)
    return text_value[: match.end()] if match else text_value


def _reference_text(page: object, text: str) -> str:
    for name in ("reference", "reference_text", "reference_block", "evidence"):
        value = _field(page, name)
        if isinstance(value, str) and value.strip():
            return value.strip().splitlines()[0]
        if isinstance(value, Mapping):
            for nested in ("text", "content", "first_line"):
                candidate = value.get(nested)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip().splitlines()[0]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                candidate = _reference_text(item, "")
                if candidate:
                    return candidate
    lines = text.splitlines()
    in_reference = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{1,6}\s+", stripped):
            in_reference = bool(re.search(r"evidence|reference|参考|证据", stripped, re.I))
            continue
        if in_reference and stripped and not stripped.startswith("<a "):
            return stripped
    return _first_sentence(text)


def _module_path(path: str) -> str:
    parts = PurePosixPath(path).parts
    try:
        product_index = parts.index("products")
    except ValueError:
        return PurePosixPath(path).parent.as_posix()
    parent = parts[: len(parts) - 1]
    if len(parent) <= product_index + 1:
        return PurePosixPath(path).parent.as_posix()
    return PurePosixPath(*parent).as_posix()


def _page_rows(value: object) -> list[dict[str, object]]:
    if isinstance(value, Path):
        return [
            {"page_path": path.relative_to(value).as_posix(), "text": path.read_text(encoding="utf-8")}
            for path in sorted(value.rglob("*.md"), key=lambda item: _utf8_key(item.relative_to(value).as_posix()))
            if not any(part.startswith(".") or part == "_gbrain" for part in path.relative_to(value).parts)
            and not path.is_symlink()
        ]
    if isinstance(value, Mapping):
        pages = value.get("pages")
        if isinstance(pages, Sequence) and not isinstance(pages, (str, bytes, bytearray)):
            return _page_rows(list(pages))
        path = _page_path(value)
        if path is not None:
            return [dict(value)]
        rows: list[dict[str, object]] = []
        for key, item in value.items():
            if not isinstance(key, str) or not key.endswith(".md"):
                continue
            if isinstance(item, Mapping):
                row = dict(item)
                row.setdefault("page_path", key)
            else:
                row = {"page_path": key, "text": str(item)}
            rows.append(row)
        return rows
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        rows = []
        for item in value:
            if isinstance(item, Mapping):
                path = _page_path(item)
                if path is not None:
                    rows.append(dict(item))
            elif isinstance(item, Path):
                path = item.as_posix()
                rows.append({"page_path": path, "text": item.read_text(encoding="utf-8")})
        return rows
    return []


def _source_id_from_block_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(.+)-b\d+", value)
    return match.group(1) if match else None


def _page_source_ids(page: Mapping[str, object]) -> set[str]:
    """Return source ids asserted by a published page's audit evidence."""
    source_ids: set[str] = set()
    for name in ("source_id", "source_snapshot_id"):
        value = page.get(name)
        if isinstance(value, str) and value.strip():
            source_ids.add(value.strip())
    for name in ("evidence", "citations", "provenance", "source_records", "references"):
        value = page.get(name)
        rows = [value] if isinstance(value, Mapping) else value
        if not isinstance(rows, Iterable) or isinstance(rows, (str, bytes, bytearray)):
            continue
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            for field in ("source_id", "source_snapshot_id", "source_block_id", "block_id"):
                source_id = _source_id_from_block_id(row.get(field))
                if source_id is not None:
                    source_ids.add(source_id)
                value = row.get(field)
                if field in {"source_id", "source_snapshot_id"} and isinstance(value, str) and value.strip():
                    source_ids.add(value.strip())
    return source_ids


def _mapping_entries(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Mapping) or not isinstance(value.get("entries"), list):
        return []
    return [dict(row) for row in value["entries"] if isinstance(row, Mapping)]


def generate_questions(manifest_pages: object, module_rule: object | None = None) -> dict[str, object]:
    """Generate the frozen, deterministic two-question-per-module set."""
    del module_rule  # The rule is frozen in QUESTION_GENERATOR_POLICY.
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in _page_rows(manifest_pages):
        path = _page_path(row)
        if path is None or not path.endswith(".md") or not path.startswith("products/"):
            continue
        module = _module_path(path)
        row = dict(row)
        row["page_path"] = path
        row["module"] = module
        grouped.setdefault(module, []).append(row)

    questions: list[dict[str, object]] = []
    degraded_modules: list[str] = []
    for module in sorted(grouped, key=_utf8_key):
        candidates = sorted(grouped[module], key=lambda row: _utf8_key(str(row["page_path"])))
        selected = candidates[:2]
        if len(selected) < 2:
            degraded_modules.append(module)
        for index, row in enumerate(selected):
            path = str(row["page_path"])
            text = _page_text(row)
            title = _page_title(row, text, path)
            reference = _reference_text(row, text)
            template_index = index % len(QUESTION_TEMPLATES)
            prompt = QUESTION_TEMPLATES[template_index].format(title)
            question_id = "q-" + hashlib.sha256(
                f"{module}\n{path}\n{template_index}\n{title}\n{reference}".encode("utf-8")
            ).hexdigest()[:24]
            question: dict[str, object] = {
                "question_id": question_id,
                "module": module,
                "page_path": path,
                "expected_page": path,
                "title": title,
                "reference": reference,
                "template_index": template_index,
                "template": QUESTION_TEMPLATES[template_index],
                "prompt": prompt,
                "question": prompt,
                "generator_version": QUESTION_GENERATOR_VERSION,
            }
            for name in (
                "page_anchor",
                "source_snapshot",
                "source_uri",
                "source_path",
                "content_hash",
                "content_fingerprint",
                "line_start",
                "line_end",
            ):
                value = _field(row, name)
                if value is not None:
                    question[name] = value
            questions.append(question)
    question_hash = _json_sha256(questions)
    return {
        "schema_version": "task9-question-set.v1",
        "generator_version": QUESTION_GENERATOR_VERSION,
        "rules_sha256": QUESTION_GENERATOR_RULES_SHA256,
        "module_count": len(grouped),
        "questions": questions,
        "question_set_sha256": question_hash,
        "question_set_hash": question_hash,
        "degraded_modules": degraded_modules,
    }


def generate_mapped_questions(manifest_pages: object, comparison_mapping: object) -> dict[str, object]:
    """Generate a deterministic question set from an explicit page mapping.

    The default generator remains frozen at the physical target module.  This
    opt-in generator is for a target whose published path layout is known to be
    different from the frozen comparison layout.  It still samples at most two
    distinct target pages per mapped logical module and never invents a page or
    source binding.
    """
    mapping_id = str(_field(comparison_mapping, "mapping_id", ""))
    entries = _mapping_entries(comparison_mapping)
    page_rows = _page_rows(manifest_pages)
    pages_by_path: dict[str, dict[str, object]] = {}
    pages_by_source: dict[str, set[str]] = {}
    for row in page_rows:
        path = _page_path(row)
        if path is None or not path.startswith("products/") or not path.endswith(".md"):
            continue
        normalized = dict(row)
        normalized["page_path"] = path
        pages_by_path.setdefault(path, normalized)
        for source_id in _page_source_ids(normalized):
            pages_by_source.setdefault(source_id, set()).add(path)

    grouped: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        module = entry.get("logical_module")
        if isinstance(module, str) and module.strip():
            grouped.setdefault(module, []).append(entry)

    questions: list[dict[str, object]] = []
    degraded_modules: list[str] = []
    skipped_source_ids: list[str] = []
    used_target_pages: set[str] = set()
    for module in sorted(grouped, key=_utf8_key):
        selected_count = 0
        for entry in sorted(
            grouped[module],
            key=lambda row: (
                str(row.get("comparison_page", "")).encode("utf-8"),
                str(row.get("source_id", "")).encode("utf-8"),
            ),
        ):
            source_id = entry.get("source_id")
            comparison_page = entry.get("comparison_page")
            if not isinstance(source_id, str) or not isinstance(comparison_page, str):
                continue
            candidates = sorted(pages_by_source.get(source_id, set()), key=_utf8_key)
            target_path = next((path for path in candidates if path not in used_target_pages), None)
            if target_path is None:
                skipped_source_ids.append(source_id)
                continue
            used_target_pages.add(target_path)
            row = pages_by_path[target_path]
            text = _page_text(row)
            title = _page_title(row, text, target_path)
            reference = _reference_text(row, text)
            template_index = selected_count % len(QUESTION_TEMPLATES)
            prompt = QUESTION_TEMPLATES[template_index].format(title)
            question_id = "q-" + hashlib.sha256(
                f"{mapping_id}\n{module}\n{source_id}\n{target_path}\n"
                f"{comparison_page}\n{template_index}\n{title}\n{reference}".encode("utf-8")
            ).hexdigest()[:24]
            question: dict[str, object] = {
                "question_id": question_id,
                "module": module,
                "target_module": _module_path(target_path),
                "page_path": target_path,
                "expected_page": target_path,
                "title": title,
                "reference": reference,
                "template_index": template_index,
                "template": QUESTION_TEMPLATES[template_index],
                "prompt": prompt,
                "question": prompt,
                "generator_version": MAPPED_QUESTION_GENERATOR_VERSION,
                "source_snapshot": "target",
                "source_id": source_id,
                "source_uri": entry.get("source_uri"),
                "source_sha256": entry.get("source_sha256"),
                "comparison_mapping_id": mapping_id,
                "comparison_page": comparison_page,
                "comparison_sha256": entry.get("comparison_sha256"),
            }
            for name in ("page_anchor", "line_start", "line_end"):
                value = _field(row, name)
                if value is not None:
                    question[name] = value
            questions.append(question)
            selected_count += 1
            if selected_count >= 2:
                break
        if selected_count < 2:
            degraded_modules.append(module)

    mapping_hash = _json_sha256(comparison_mapping)
    question_hash = _json_sha256(questions)
    return {
        "schema_version": "task9-question-set.v1",
        "generator_version": MAPPED_QUESTION_GENERATOR_VERSION,
        "rules_sha256": MAPPED_QUESTION_GENERATOR_RULES_SHA256,
        "mapping_id": mapping_id,
        "comparison_mapping_sha256": mapping_hash,
        "module_count": len(grouped),
        "mapping_entry_count": len(entries),
        "selected_entry_count": len(questions),
        "skipped_source_ids": skipped_source_ids,
        "questions": questions,
        "question_set_sha256": question_hash,
        "question_set_hash": question_hash,
        "degraded_modules": degraded_modules,
    }


def _page_has_source_uri(page: Mapping[str, object], source_uri: str) -> bool:
    expected = source_uri.strip().replace("\\", "/")
    for name in ("evidence", "citations", "provenance", "source_records", "references"):
        value = page.get(name)
        rows = [value] if isinstance(value, Mapping) else value
        if not isinstance(rows, Iterable) or isinstance(rows, (str, bytes, bytearray)):
            continue
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            candidate = row.get("source_uri", row.get("source_path"))
            if isinstance(candidate, str) and candidate.strip().replace("\\", "/") == expected:
                return True
    return False


def _validate_comparison_mapping(
    value: object,
    *,
    manifest: Mapping[str, object],
    frozen_id: str,
    freeze_dir: Path,
    target_pages: Mapping[str, Mapping[str, object]],
    comparison_pages: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object] | None, list[str]]:
    """Validate an explicit source-to-comparison mapping at the freeze boundary."""
    if not isinstance(value, Mapping):
        return None, ["comparison_mapping_missing"]
    mapping = dict(value)
    reasons: list[str] = []
    if mapping.get("schema_version") != COMPARISON_MAPPING_SCHEMA_VERSION:
        reasons.append("comparison_mapping.schema_version")
    mapping_id = mapping.get("mapping_id")
    if not isinstance(mapping_id, str) or not mapping_id.strip() or any(
        ord(character) < 32 or ord(character) == 127 for character in mapping_id
    ):
        reasons.append("comparison_mapping.mapping_id")

    snapshots = manifest.get("snapshots")
    snapshot_values = snapshots if isinstance(snapshots, Mapping) else {}
    input_descriptor = snapshot_values.get("input")
    comparison_descriptor = snapshot_values.get("comparison")
    input_tree_hash = input_descriptor.get("tree_hash") if isinstance(input_descriptor, Mapping) else None
    comparison_tree_hash = comparison_descriptor.get("tree_hash") if isinstance(comparison_descriptor, Mapping) else None
    manifest_hash = manifest.get("manifest_sha256")
    expected_scalars = {
        "source_manifest_sha256": manifest_hash,
        "source_snapshot_tree_hash": input_tree_hash,
        "comparison_frozen_id": frozen_id,
        "comparison_tree_hash": comparison_tree_hash,
    }
    for name, expected in expected_scalars.items():
        if not isinstance(expected, str) or not expected:
            reasons.append(f"comparison_mapping.expected_{name}")
        elif mapping.get(name) != expected:
            reasons.append(f"comparison_mapping.{name}")

    raw_entries = mapping.get("entries")
    entries = _mapping_entries(mapping)
    if not isinstance(raw_entries, list) or not entries:
        reasons.append("comparison_mapping.entries")
    entry_count = mapping.get("entry_count")
    if isinstance(entry_count, bool) or not isinstance(entry_count, int) or entry_count != len(entries):
        reasons.append("comparison_mapping.entry_count")

    input_records: dict[str, str] = {}
    if isinstance(input_descriptor, Mapping) and isinstance(input_descriptor.get("files"), list):
        for row in input_descriptor["files"]:
            if isinstance(row, Mapping) and isinstance(row.get("path"), str) and isinstance(row.get("sha256"), str):
                input_records[row["path"]] = row["sha256"]

    target_by_source: dict[str, list[str]] = {}
    for path, page in target_pages.items():
        for source_id in _page_source_ids(page):
            target_by_source.setdefault(source_id, []).append(path)

    seen_source_ids: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"comparison_mapping.entries[{index}]"
        source_id = entry.get("source_id")
        source_uri = entry.get("source_uri")
        source_sha256 = entry.get("source_sha256")
        comparison_page = entry.get("comparison_page")
        comparison_sha256 = entry.get("comparison_sha256")
        logical_module = entry.get("logical_module")
        if not isinstance(source_id, str) or not source_id.strip():
            reasons.append(f"{prefix}.source_id")
        elif source_id in seen_source_ids:
            reasons.append(f"{prefix}.duplicate_source_id")
        else:
            seen_source_ids.add(source_id)
        if not isinstance(source_uri, str) or not _relative_is_safe(source_uri):
            reasons.append(f"{prefix}.source_uri")
        elif input_records.get(source_uri) != source_sha256:
            reasons.append(f"{prefix}.source_binding")
        if not isinstance(source_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            reasons.append(f"{prefix}.source_sha256")
        if not isinstance(comparison_page, str) or not _relative_is_safe(comparison_page):
            reasons.append(f"{prefix}.comparison_page")
        else:
            expected_module = PurePosixPath(comparison_page).parent.as_posix()
            if logical_module != expected_module:
                reasons.append(f"{prefix}.logical_module")
            comparison_path = freeze_dir / SNAPSHOT_ROOTS["comparison"] / comparison_page
            if comparison_page not in comparison_pages or not str(comparison_pages[comparison_page].get("text", "")).strip():
                reasons.append(f"{prefix}.comparison_missing")
            elif comparison_path.is_symlink() or not comparison_path.is_file():
                reasons.append(f"{prefix}.comparison_file")
            elif hashlib.sha256(comparison_path.read_bytes()).hexdigest() != comparison_sha256:
                reasons.append(f"{prefix}.comparison_binding")
        if not isinstance(comparison_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", comparison_sha256):
            reasons.append(f"{prefix}.comparison_sha256")
        if not isinstance(logical_module, str) or not _relative_is_safe(logical_module):
            reasons.append(f"{prefix}.logical_module")
        if isinstance(source_id, str) and source_id.strip():
            candidates = target_by_source.get(source_id, [])
            if not candidates:
                reasons.append(f"{prefix}.target_source_missing")
            elif isinstance(source_uri, str) and not any(
                _page_has_source_uri(target_pages[path], source_uri) for path in candidates
            ):
                reasons.append(f"{prefix}.target_source_binding")

    if reasons:
        return None, list(dict.fromkeys(reasons))
    return mapping, []


def _mapped_question_shape_reasons(
    questions: Sequence[Mapping[str, object]],
    mapping: Mapping[str, object],
) -> list[str]:
    """Validate generated mapped questions without trusting caller-supplied counts."""
    reasons: list[str] = []
    entries = {str(row["source_id"]): row for row in _mapping_entries(mapping) if isinstance(row.get("source_id"), str)}
    mapping_id = mapping.get("mapping_id")
    module_counts: dict[str, int] = {}
    page_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for index, question in enumerate(questions):
        prefix = f"questions[{index}]"
        path = question.get("page_path")
        if not isinstance(path, str) or not _relative_is_safe(path) or not path.startswith("products/") or not path.endswith(".md"):
            reasons.append(f"{prefix}.page_path")
        source_id = question.get("source_id")
        entry = entries.get(source_id) if isinstance(source_id, str) else None
        if entry is None:
            reasons.append(f"{prefix}.source_id")
            continue
        if question.get("comparison_mapping_id") != mapping_id:
            reasons.append(f"{prefix}.comparison_mapping_id")
        for name in ("source_uri", "source_sha256", "comparison_page", "comparison_sha256"):
            if question.get(name) != entry.get(name):
                reasons.append(f"{prefix}.{name}")
        module = question.get("module")
        if not isinstance(module, str) or module != entry.get("logical_module"):
            reasons.append(f"{prefix}.module")
        else:
            module_counts[module] = module_counts.get(module, 0) + 1
        if isinstance(path, str):
            page_counts[path.casefold()] = page_counts.get(path.casefold(), 0) + 1
        source_counts[source_id] = source_counts.get(source_id, 0) + 1
    for module, count in module_counts.items():
        if count > 2:
            reasons.append(f"questions.mapped_module_overrepresented:{module}")
    for path, count in page_counts.items():
        if count > 1:
            reasons.append(f"questions.page_repeated:{path}")
    for source_id, count in source_counts.items():
        if count > 1:
            reasons.append(f"questions.source_repeated:{source_id}")
    return reasons


def _question_list(value: object) -> tuple[list[dict[str, object]], list[str]]:
    raw = value.get("questions") if isinstance(value, Mapping) else value
    if not isinstance(raw, list):
        return [], ["questions_missing"]
    questions: list[dict[str, object]] = []
    reasons: list[str] = []
    seen: set[str] = set()
    seen_semantic: set[tuple[str, str]] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            reasons.append(f"questions[{index}]")
            continue
        row = dict(item)
        question_id = row.get("question_id")
        prompt = row.get("prompt", row.get("question", row.get("original_text")))
        path = row.get("page_path", row.get("expected_page"))
        if not isinstance(question_id, str) or not question_id.strip():
            reasons.append(f"questions[{index}].question_id")
        elif question_id in seen:
            reasons.append(f"questions[{index}].duplicate_id")
        else:
            seen.add(question_id)
        if not isinstance(prompt, str) or not prompt.strip():
            reasons.append(f"questions[{index}].prompt")
        elif isinstance(path, str) and _relative_is_safe(path):
            semantic_key = (path.casefold(), prompt.strip().casefold())
            if semantic_key in seen_semantic:
                reasons.append(f"questions[{index}].duplicate_semantic_question")
            seen_semantic.add(semantic_key)
        if not isinstance(path, str) or not _relative_is_safe(path):
            reasons.append(f"questions[{index}].page_path")
        else:
            row["page_path"] = path
            row.setdefault("expected_page", path)
        questions.append(row)
    if not questions:
        reasons.append("question_set_empty")
    return questions, reasons


def _question_shape_reasons(questions: Sequence[Mapping[str, object]]) -> list[str]:
    """Reject caller-supplied question sets that over-sample one page/module."""
    reasons: list[str] = []
    module_counts: dict[str, int] = {}
    page_counts: dict[str, int] = {}
    for index, question in enumerate(questions):
        path = question.get("page_path")
        if not isinstance(path, str) or not _relative_is_safe(path):
            continue
        if not path.startswith("products/") or not path.endswith(".md"):
            reasons.append(f"questions[{index}].page_path")
            continue
        module = _module_path(path)
        declared_module = question.get("module")
        if declared_module is not None and (
            not isinstance(declared_module, str) or declared_module != module
        ):
            reasons.append(f"questions[{index}].module")
        module_counts[module] = module_counts.get(module, 0) + 1
        page_counts[path.casefold()] = page_counts.get(path.casefold(), 0) + 1
    for module, count in module_counts.items():
        if count > 2:
            reasons.append(f"questions.module_overrepresented:{module}")
    for path, count in page_counts.items():
        if count > 1:
            reasons.append(f"questions.page_repeated:{path}")
    return reasons


def _jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file() or path.is_symlink():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _load_page_corpus(root: Path) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    root = Path(root)
    pages: dict[str, dict[str, object]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: _utf8_key(item.relative_to(root).as_posix())):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValidationError("accept", path, "symbolic links are not allowed in the page corpus")
        if not path.is_file() or not relative.endswith(".md"):
            continue
        if any(part.startswith(".") or part == "_gbrain" for part in Path(relative).parts):
            continue
        pages[relative] = {"page_path": relative, "text": path.read_text(encoding="utf-8")}
    evidence = _jsonl(root / "_audit" / "sources.jsonl") + _jsonl(root / "_audit" / "reference-blocks.jsonl")
    for row in evidence:
        path = _page_path(row)
        if path is not None and path in pages:
            pages[path].setdefault("evidence", []).append(row)
    return pages, evidence


def _normalise_page_corpus(value: object) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    if isinstance(value, Path):
        return _load_page_corpus(value)
    if isinstance(value, Mapping) and isinstance(value.get("root"), (str, Path)):
        return _normalise_page_corpus(Path(value["root"]))
    global_evidence: list[dict[str, object]] = []
    if isinstance(value, Mapping):
        raw_evidence = value.get("evidence", value.get("source_records", []))
        if isinstance(raw_evidence, list):
            global_evidence.extend(row for row in raw_evidence if isinstance(row, Mapping))
    pages: dict[str, dict[str, object]] = {}
    for row in _page_rows(value):
        path = _page_path(row)
        if path is not None:
            pages[path] = row
    for row in global_evidence:
        path = _page_path(row)
        if path is not None and path in pages:
            pages[path].setdefault("evidence", []).append(dict(row))
    return pages, global_evidence


def _source_value_records(value: object) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    if isinstance(value, str):
        candidate = Path(value)
        if candidate.exists():
            value = candidate
    if isinstance(value, Path):
        if value.is_file():
            value = {value.name: value.read_text(encoding="utf-8")}
        elif value.is_dir():
            for path in sorted(value.rglob("*"), key=lambda item: _utf8_key(item.relative_to(value).as_posix())):
                relative = path.relative_to(value).as_posix()
                if path.is_symlink():
                    raise ValidationError("accept", path, "symbolic links are not allowed in a source snapshot")
                if path.is_file() and not any(part.startswith(".") or part == "_gbrain" for part in Path(relative).parts):
                    raw = path.read_bytes()
                    try:
                        text_value = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    records[relative] = {
                        "source_uri": relative,
                        "source_path": relative,
                        "text": text_value,
                        "raw": raw,
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
            return records
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or key in {"input", "comparison", "release4", "pages", "evidence"}:
                continue
            if isinstance(item, Mapping):
                text_value = item.get("text", item.get("content", ""))
                if not isinstance(text_value, str):
                    continue
                raw = text_value.encode("utf-8")
                row = dict(item)
            else:
                text_value = str(item)
                raw = text_value.encode("utf-8")
                row = {}
            row.update({"source_uri": row.get("source_uri", key), "source_path": row.get("source_path", key), "text": text_value, "raw": raw, "sha256": row.get("sha256", hashlib.sha256(raw).hexdigest())})
            records[key] = row
    return records


def _source_root(value: object, role: str) -> object:
    if isinstance(value, Path):
        if (value / "manifest.json").is_file():
            return value / role
        return value
    if isinstance(value, Mapping):
        if role in value:
            return value[role]
        key = f"{role}_dir"
        if key in value:
            return value[key]
    return value


def _source_records(value: object, role: str = "input") -> dict[str, dict[str, object]]:
    return _source_value_records(_source_root(value, role))


def _lookup_source(records: Mapping[str, Mapping[str, object]], uri: object) -> Mapping[str, object] | None:
    if not isinstance(uri, str) or not uri.strip():
        return None
    needle = uri.strip().replace("\\", "/")
    for key, record in records.items():
        if needle == key or needle == str(record.get("source_uri", "")) or needle == str(record.get("source_path", "")):
            return record
    candidates: list[Mapping[str, object]] = []
    if "://" not in needle or needle.startswith("file://") or needle.startswith("/"):
        for key, record in records.items():
            if needle.endswith("/" + key) or key.endswith("/" + needle):
                candidates.append(record)
    return candidates[0] if len(candidates) == 1 else None


def _citation_values(page: Mapping[str, object], evidence: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for row in evidence:
        values.append(dict(row))
    for name in ("evidence", "citations", "provenance", "source_records", "references"):
        raw = page.get(name)
        if isinstance(raw, Mapping):
            values.append(dict(raw))
        elif isinstance(raw, list):
            values.extend(dict(item) for item in raw if isinstance(item, Mapping))
    if any(page.get(name) is not None for name in ("source_uri", "source_path", "content_hash", "content_fingerprint")):
        values.append(dict(page))
    if values:
        return values
    # A small fallback for hand-authored fixture pages.  It deliberately
    # requires the fingerprint and line range to be present; text overlap is
    # never treated as provenance.
    for line in str(page.get("text", "")).splitlines():
        source_match = re.search(r"(?:source_uri|source_path|来源)\s*[:=：]\s*[`\"]?([^`\"\s,)]+)", line, re.I)
        fingerprint_match = re.search(r"(?:content_hash|content_fingerprint|sha256)\s*[:=：]\s*([0-9a-f]{64})", line, re.I)
        range_match = re.search(r"(?:line_start|lines?)\s*[:=：]\s*(\d+)(?:\s*[-~]\s*(\d+))?", line, re.I)
        if source_match and fingerprint_match and range_match:
            values.append({
                "source_uri": source_match.group(1),
                "content_fingerprint": fingerprint_match.group(1),
                "line_start": int(range_match.group(1)),
                "line_end": int(range_match.group(2) or range_match.group(1)),
            })
    return values


def _valid_citation(citation: Mapping[str, object], sources: Mapping[str, Mapping[str, object]]) -> dict[str, object] | None:
    uri = citation.get("source_uri", citation.get("source_path", citation.get("uri", citation.get("path"))))
    source = _lookup_source(sources, uri)
    if source is None:
        return None
    try:
        start = int(citation.get("line_start", citation.get("source_line_start")))
        end = int(citation.get("line_end", citation.get("source_line_end", start)))
    except (TypeError, ValueError):
        return None
    lines = str(source.get("text", "")).splitlines()
    if start < 1 or end < start or end > len(lines):
        return None
    fingerprint = next(
        (
            citation.get(name)
            for name in ("content_fingerprint", "content_hash", "sha256", "fingerprint")
            if citation.get(name) is not None
        ),
        None,
    )
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        return None
    span = "\n".join(lines[start - 1 : end]).encode("utf-8")
    accepted = {
        hashlib.sha256(span).hexdigest(),
        hashlib.sha256((span.decode("utf-8") + "\n").encode("utf-8")).hexdigest(),
    }
    if fingerprint not in accepted:
        return None
    return {
        "source_uri": str(uri),
        "line_start": start,
        "line_end": end,
        "content_fingerprint": fingerprint,
    }


def _citation_matches_location(citation: Mapping[str, object], question: Mapping[str, object]) -> bool:
    expected_path = _page_path(question)
    citation_path = _page_path(citation)
    if expected_path is None or citation_path is None or citation_path != expected_path:
        return False
    expected_anchor = question.get("page_anchor", question.get("anchor"))
    if not isinstance(expected_anchor, str) or not expected_anchor.strip():
        return True
    citation_anchor = citation.get("page_anchor", citation.get("anchor"))
    return isinstance(citation_anchor, str) and citation_anchor.strip() == expected_anchor.strip()


def _location_valid(page: Mapping[str, object], question: Mapping[str, object], evidence: Iterable[Mapping[str, object]]) -> bool:
    if not any(_citation_matches_location(row, question) for row in evidence):
        return False
    anchor = question.get("page_anchor", question.get("anchor"))
    if not isinstance(anchor, str) or not anchor.strip():
        return True
    anchor = anchor.strip()
    text = str(page.get("text", ""))
    if f'id="{anchor}"' in text or f"id='{anchor}'" in text:
        return True
    anchors = page.get("anchors", page.get("block_anchors", []))
    if isinstance(anchors, Mapping):
        return anchor in anchors or anchor in {str(item) for item in anchors.values()}
    if isinstance(anchors, Sequence) and not isinstance(anchors, (str, bytes, bytearray)):
        return anchor in {str(item) for item in anchors}
    return False


def _comparison_pages(value: object) -> dict[str, dict[str, object]]:
    if isinstance(value, Mapping) and "comparison_pages" in value:
        pages, _ = _normalise_page_corpus(value["comparison_pages"])
        return pages
    if isinstance(value, Mapping) and isinstance(value.get("snapshots"), Mapping):
        pages, _ = _normalise_page_corpus(value["snapshots"].get("comparison", {}))
        return pages
    root = _source_root(value, "comparison")
    pages, _ = _normalise_page_corpus(root)
    return pages


def _release4_pages(value: object) -> dict[str, dict[str, object]]:
    if isinstance(value, Mapping) and "release4_pages" in value:
        pages, _ = _normalise_page_corpus(value["release4_pages"])
        return pages
    if isinstance(value, Mapping) and isinstance(value.get("snapshots"), Mapping):
        pages, _ = _normalise_page_corpus(value["snapshots"].get("release4", {}))
        return pages
    root = _source_root(value, "release4")
    pages, _ = _normalise_page_corpus(root)
    return pages


def _snapshot_has_match(question: Mapping[str, object], pages: Mapping[str, Mapping[str, object]]) -> bool:
    return _comparison_has_match(question, pages)


def _comparison_has_match(question: Mapping[str, object], pages: Mapping[str, Mapping[str, object]]) -> bool:
    expected = question.get("comparison_page", question.get("expected_comparison_page", question.get("page_path")))
    if isinstance(expected, str) and expected in pages and str(pages[expected].get("text", "")).strip():
        return True
    if isinstance(expected, str):
        expected_folded = expected.casefold()
        if any(path.casefold() == expected_folded and str(page.get("text", "")).strip() for path, page in pages.items()):
            return True
    module = question.get("module")
    title = question.get("title")
    if isinstance(module, str) and isinstance(title, str):
        for path, page in pages.items():
            candidate_module = _module_path(path).casefold().replace("/modules/", "/")
            expected_module = module.casefold().replace("/modules/", "/")
            candidate_title = _page_title(page, str(page.get("text", "")), path).casefold()
            if candidate_module == expected_module and candidate_title == title.strip().casefold():
                return True
    return False


def judge(question: Mapping[str, object], kb_pages: object, frozen_sources: object) -> dict[str, object]:
    """Produce the four machine-defined results for one question."""
    questions, reasons = _question_list([question])
    if reasons or not questions:
        raise ValidationError("accept", "question", "; ".join(reasons))
    question = questions[0]
    pages, global_evidence = _normalise_page_corpus(kb_pages)
    path = str(question["page_path"])
    page = pages.get(path)
    evidence: list[Mapping[str, object]] = [row for row in global_evidence if _page_path(row) == path]
    if page is not None:
        evidence.extend(row for row in page.get("evidence", []) if isinstance(row, Mapping))
    sources = _source_records(frozen_sources, "input")
    release4_pages = _release4_pages(frozen_sources)
    comparison_pages = _comparison_pages(frozen_sources)
    citations = _citation_values(page or {"text": ""}, evidence)
    bound_citations = [citation for citation in citations if _citation_matches_location(citation, question)]
    valid = [proof for citation in bound_citations if (proof := _valid_citation(citation, sources)) is not None]
    expected_uri = question.get("source_uri", question.get("source_path"))
    if isinstance(expected_uri, str) and expected_uri.strip():
        expected_uri = expected_uri.strip().replace("\\", "/")
        valid = [
            proof
            for proof in valid
            if proof["source_uri"] == expected_uri
            or str(proof["source_uri"]).endswith("/" + expected_uri)
            or expected_uri.endswith("/" + str(proof["source_uri"]))
        ]
    location_valid = page is not None and _location_valid(page, question, bound_citations)
    source_correct = bool(valid)
    answer_hit = bool(page is not None and location_valid and valid)
    snapshot_matches = {
        "release4": _snapshot_has_match(question, release4_pages),
        "comparison": _snapshot_has_match(question, comparison_pages),
    }
    comparison_uncovered = not snapshot_matches["comparison"]
    hard_failure = bool(not comparison_uncovered and (page is None or not source_correct))
    if comparison_uncovered:
        failure_reason = "comparison_uncovered"
    elif page is None:
        failure_reason = "answer_missing"
    elif not location_valid:
        failure_reason = "location_invalid"
    elif not source_correct:
        failure_reason = "source_incorrect"
    elif not answer_hit:
        failure_reason = "answer_missing"
    else:
        failure_reason = None
    return {
        "question_id": question["question_id"],
        "prompt": question.get("prompt", question.get("question")),
        "page_path": path,
        "answer_hit": answer_hit,
        "location_valid": location_valid,
        "source_correct": source_correct,
        "comparison_uncovered": comparison_uncovered,
        "snapshot_matches": snapshot_matches,
        "question_source_snapshot": question.get("source_snapshot"),
        "hard_failure": hard_failure,
        "failure_reason": failure_reason,
        "evidence": valid,
        "judge_rules_version": JUDGE_RULES_VERSION,
    }


def summarize(results: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Apply the frozen effective-denominator and hard-failure rules."""
    rows = [dict(row) for row in results]
    effective = [row for row in rows if not bool(row.get("comparison_uncovered"))]
    hard_failures = [row for row in effective if bool(row.get("hard_failure")) or not bool(row.get("source_correct"))]
    correct = [row for row in effective if bool(row.get("answer_hit")) and bool(row.get("source_correct"))]
    effective_count = len(effective)
    if effective_count == 0:
        status = "fail"
        reason_code = "no_effective_questions"
    elif effective_count < 10:
        status = "blocked"
        reason_code = "insufficient_effective_questions"
    elif hard_failures:
        status = "fail"
        reason_code = "hard_failures"
    elif len(correct) / effective_count < 0.8:
        status = "fail"
        reason_code = "answer_or_source_rate_below_threshold"
    else:
        status = "pass"
        reason_code = None
    return {
        "status": status,
        "verdict": status,
        "reason_code": reason_code,
        "question_count": len(rows),
        "effective_question_count": effective_count,
        "uncovered_question_count": len(rows) - effective_count,
        "hard_failure_count": len(hard_failures),
        "answer_hit_count": sum(bool(row.get("answer_hit")) for row in effective),
        "source_correct_count": sum(bool(row.get("source_correct")) for row in effective),
        "correct_count": len(correct),
        "correct_rate": (len(correct) / effective_count) if effective_count else 0.0,
        "threshold": {"hard_failures": 0, "correct_rate": 0.8, "minimum_effective_questions": 10},
    }


def _read_json_input(value: object) -> object:
    if isinstance(value, (str, Path)):
        path = Path(value)
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return value


def _accept_blocked(
    frozen_id: str | None,
    reasons: Sequence[str],
    *,
    manifest_path: Path | None = None,
    target_hash: str | None = None,
    question_hash: str | None = None,
    message: str | None = None,
    reason_code: str = "accept_preflight_blocked",
) -> dict[str, object]:
    result = _blocked(
        frozen_id,
        reasons,
        manifest_path=manifest_path,
        reason_code=reason_code,
        message=message,
    )
    if target_hash is not None:
        result["target_kb_tree_hash"] = target_hash
    if question_hash is not None:
        result["question_set_sha256"] = question_hash
    return result


def accept(
    frozen_id: str | Path | None = None,
    kb_dir: Path | str | None = None,
    *,
    freeze: bool = False,
    output: Path | str | None = None,
    freeze_root: Path | str | None = None,
    input_dir: Path | str | None = None,
    release4_dir: Path | str | None = None,
    comparison_dir: Path | str | None = None,
    question_set: object | None = None,
    comparison_mapping: object | None = None,
    replay: object | None = None,
    record: object | None = None,
    run_id: str | None = None,
) -> dict[str, object]:
    """Run freeze or a complete, offline, bound acceptance evaluation."""
    if freeze:
        return globals()["freeze"](
            input_dir if input_dir is not None else frozen_id,
            release4_dir if release4_dir is not None else kb_dir,
            comparison_dir,
            output if output is not None else freeze_root,
        )

    protected_output_roots: list[Path] = []
    if kb_dir is not None:
        target_path = Path(kb_dir)
        protected_output_roots.extend((target_path, sidecar_path(target_path)))
    if freeze_root is not None:
        protected_output_roots.append(Path(freeze_root))

    def finish(value: dict[str, object]) -> dict[str, object]:
        if output is not None:
            output_path = Path(output)
            _validate_output_path(output_path, protected_output_roots)
            _atomic_write_json(output_path, value)
        return value

    if frozen_id is None:
        return finish(_accept_blocked(None, ["frozen_id_missing"]))
    if kb_dir is None:
        return finish(_accept_blocked(str(frozen_id), ["target_kb_missing"]))

    cache: dict[str, str] = {}
    preflight_result = preflight(
        frozen_id,
        freeze_root,
        target_kb=kb_dir,
        tree_hash_cache=cache,
    )
    manifest_path = Path(str(preflight_result.get("manifest_path", "manifest.json")))
    protected_output_roots.append(manifest_path.parent)
    if preflight_result.get("status") != "ready":
        return finish(preflight_result)
    canonical_frozen_id = str(preflight_result.get("frozen_id", frozen_id))
    freeze_dir = manifest_path.parent
    target = Path(kb_dir)
    supplied_question_set = _read_json_input(question_set)
    supplied_comparison_mapping = _read_json_input(comparison_mapping)
    replay_value = _read_json_input(replay if replay is not None else record)
    evaluation_id = run_id or uuid.uuid4().hex
    started = time.monotonic()
    try:
        expected_freeze_hashes = preflight_result.get("tree_hashes", {})
        fresh_freeze_hashes = {
            role: kb_tree_hash(freeze_dir / SNAPSHOT_ROOTS[role])
            for role in SNAPSHOT_ROOTS
        }
        if fresh_freeze_hashes != expected_freeze_hashes:
            return finish(_accept_blocked(
                canonical_frozen_id,
                ["freeze_snapshot_changed"],
                manifest_path=manifest_path,
                message="冻结物已变，不可复跑",
                reason_code="accept_snapshot_changed",
            ))
        with kb_write_lock(target):
            version = _target_version(target)
            if version is None:
                return finish(_accept_blocked(canonical_frozen_id, ["target_current_missing"], manifest_path=manifest_path))
            target_hash = kb_tree_hash(version)
            page_map, _ = _load_page_corpus(version)
            current_has_products = any(path.startswith("products/") for path in page_map)
            if supplied_question_set is None and not current_has_products:
                return finish({
                    **preflight_result,
                    "status": "not_evaluated",
                    "reason_code": "acceptance_not_evaluated",
                    "reasons": ["target_products_missing"],
                    "acceptance_status": "not_evaluated",
                    "target_kb_tree_hash": target_hash,
                    "results": [],
                    "question_results": [],
                    "conclusions": [],
                })
            comparison_page_map, _ = _load_page_corpus(freeze_dir / SNAPSHOT_ROOTS["comparison"])
            release4_page_map, _ = _load_page_corpus(freeze_dir / SNAPSHOT_ROOTS["release4"])
            # Questions must address the pages in the published version being
            # evaluated.  The frozen release4/comparison maps remain separate
            # named inputs to judge(), so comparison coverage cannot silently
            # replace the target page paths.
            target_question_pages = [
                {**page, "source_snapshot": "target"}
                for page in page_map.values()
            ]
            validated_mapping: dict[str, object] | None = None
            mapping_hash: str | None = None
            if supplied_comparison_mapping is not None:
                validated_mapping, mapping_reasons = _validate_comparison_mapping(
                    supplied_comparison_mapping,
                    manifest=preflight_result["manifest"],  # type: ignore[arg-type]
                    frozen_id=canonical_frozen_id,
                    freeze_dir=freeze_dir,
                    target_pages=page_map,
                    comparison_pages=comparison_page_map,
                )
                if mapping_reasons or validated_mapping is None:
                    return finish(_accept_blocked(
                        canonical_frozen_id,
                        mapping_reasons or ["comparison_mapping_invalid"],
                        manifest_path=manifest_path,
                        target_hash=target_hash,
                        reason_code="comparison_mapping_blocked",
                    ))
                mapping_hash = _json_sha256(validated_mapping)

            generated = (
                generate_mapped_questions(target_question_pages, validated_mapping)
                if validated_mapping is not None
                else (generate_questions(target_question_pages) if supplied_question_set is None else None)
            )
            question_source = generated if generated is not None else supplied_question_set
            questions, question_reasons = _question_list(question_source)
            if validated_mapping is not None and supplied_question_set is not None:
                supplied_questions, supplied_reasons = _question_list(supplied_question_set)
                if supplied_reasons or _canonical_json(supplied_questions) != _canonical_json(questions):
                    question_reasons.extend(supplied_reasons or ["comparison_mapping_question_set_mismatch"])
            if isinstance(question_source, Mapping):
                declared_hash = question_source.get("question_set_sha256", question_source.get("question_set_hash"))
                if declared_hash is not None and declared_hash != _json_sha256(questions):
                    question_reasons.append("question_set_sha256")
            if validated_mapping is not None:
                question_reasons.extend(_mapped_question_shape_reasons(questions, validated_mapping))
            else:
                question_reasons.extend(_question_shape_reasons(questions))
            if question_reasons:
                return finish(_accept_blocked(
                    canonical_frozen_id,
                    question_reasons,
                    manifest_path=manifest_path,
                    target_hash=target_hash,
                ))
            question_hash = _json_sha256(questions)
            discrimination = discrimination_check(
                freeze_dir,
                _default_discrimination_fixture(freeze_dir),
            )
            if discrimination.get("status") != "passed":
                return finish(_accept_blocked(
                    canonical_frozen_id,
                    ["discrimination_failed"],
                    manifest_path=manifest_path,
                    target_hash=target_hash,
                    question_hash=question_hash,
                    reason_code="discrimination_blocked",
                ))
            binding = {
                "target_kb_tree_hash": target_hash,
                "question_set_sha256": question_hash,
                "judge_rules_version": JUDGE_RULES_VERSION,
                "frozen_id": canonical_frozen_id,
            }
            if mapping_hash is not None:
                binding["comparison_mapping_sha256"] = mapping_hash
            if replay_value is not None:
                if not isinstance(replay_value, Mapping):
                    return finish(_accept_blocked(canonical_frozen_id, ["replay_record_invalid"], manifest_path=manifest_path))
                recorded_mapping_hash = replay_value.get("comparison_mapping_sha256")
                if recorded_mapping_hash is not None and recorded_mapping_hash != mapping_hash:
                    return finish(_accept_blocked(
                        canonical_frozen_id,
                        ["replay_binding:comparison_mapping_sha256"],
                        manifest_path=manifest_path,
                        target_hash=target_hash,
                        question_hash=question_hash,
                        message="映射题集已变，不可复跑",
                    ))
                missing_binding = [key for key in binding if key not in replay_value]
                if missing_binding:
                    return finish(_accept_blocked(
                        canonical_frozen_id,
                        [f"replay_binding_missing:{key}" for key in missing_binding],
                        manifest_path=manifest_path,
                        message="判定记录不完整，不可复跑",
                        reason_code="replay_record_incomplete",
                    ))
                replay_id = str(replay_value.get("run_id", replay_value.get("record_id", "")))
                ledger_rows = read_ledger(sidecar_path(target))
                if replay_id and _ledger_record_is_void(ledger_rows, replay_id):
                    return finish(_accept_blocked(canonical_frozen_id, ["record_void"], manifest_path=manifest_path))
                mismatches = [
                    key for key, expected in binding.items()
                    if replay_value.get(key) != expected
                ]
                if mismatches:
                    return finish(_accept_blocked(
                        canonical_frozen_id,
                        [f"replay_binding:{key}" for key in mismatches],
                        manifest_path=manifest_path,
                        target_hash=target_hash,
                        question_hash=question_hash,
                        message="被测对象已变，不可复跑",
                    ))

            sources = {
                "input": _source_records(freeze_dir / SNAPSHOT_ROOTS["input"]),
                "snapshots": {
                    "release4": release4_page_map,
                    "comparison": comparison_page_map,
                },
                "release4_pages": release4_page_map,
                "comparison_pages": comparison_page_map,
            }
            judged = [judge(question, page_map, sources) for question in questions]
            final_version = _target_version(target)
            final_target_hash = kb_tree_hash(final_version) if final_version is not None else None
            final_freeze_hashes = {
                role: kb_tree_hash(freeze_dir / SNAPSHOT_ROOTS[role])
                for role in SNAPSHOT_ROOTS
            }
            if final_version != version or final_target_hash != target_hash:
                return finish(_accept_blocked(
                    canonical_frozen_id,
                    ["target_snapshot_changed"],
                    manifest_path=manifest_path,
                    target_hash=target_hash,
                    question_hash=question_hash,
                    message="被测对象已变，不可复跑",
                    reason_code="accept_snapshot_changed",
                ))
            if final_freeze_hashes != fresh_freeze_hashes:
                return finish(_accept_blocked(
                    canonical_frozen_id,
                    ["freeze_snapshot_changed"],
                    manifest_path=manifest_path,
                    target_hash=target_hash,
                    question_hash=question_hash,
                    message="冻结物已变，不可复跑",
                    reason_code="accept_snapshot_changed",
                ))
            if replay_value is not None:
                previous = replay_value.get("question_results", replay_value.get("results"))
                if not isinstance(previous, list) or _canonical_json(previous) != _canonical_json(judged):
                    return finish(_accept_blocked(
                        canonical_frozen_id,
                        ["replay_result_mismatch"],
                        manifest_path=manifest_path,
                        target_hash=target_hash,
                        question_hash=question_hash,
                        message="判定结果已变，不可复跑",
                    ))
            verdict = summarize(judged)
            elapsed_ms = max(0, int((time.monotonic() - started) * 1000))
            result: dict[str, object] = {
                "schema_version": "task9-acceptance-record.v1",
                "run_id": evaluation_id,
                "status": verdict["status"],
                "reason_code": verdict["reason_code"],
                "frozen_id": canonical_frozen_id,
                "target_kb_tree_hash": target_hash,
                "question_set_sha256": question_hash,
                "judge_rules_version": JUDGE_RULES_VERSION,
                "question_set": {
                    "schema_version": "task9-question-set.v1",
                    "generator_version": generated.get("generator_version", QUESTION_GENERATOR_VERSION)
                    if generated is not None
                    else QUESTION_GENERATOR_VERSION,
                    "rules_sha256": generated.get("rules_sha256", QUESTION_GENERATOR_RULES_SHA256)
                    if generated is not None
                    else QUESTION_GENERATOR_RULES_SHA256,
                    "questions": questions,
                },
                "question_results": judged,
                "results": judged,
                "conclusions": judged,
                "discrimination": discrimination,
                "verdict": verdict,
                "elapsed_ms": elapsed_ms,
                "provider_calls": 0,
                "provider_tokens": 0,
                "reasons": {
                    "provider_calls": "no_provider_call_yet",
                    "provider_tokens": "no_provider_call_yet",
                },
                "provider": {"calls": 0, "tokens": 0, "reason": "no_provider_call_yet"},
            }
            if generated is not None:
                result["degraded_modules"] = generated.get("degraded_modules", [])
            if validated_mapping is not None:
                result["comparison_mapping"] = {
                    "schema_version": COMPARISON_MAPPING_SCHEMA_VERSION,
                    "mapping_id": validated_mapping.get("mapping_id"),
                    "sha256": mapping_hash,
                    "entry_count": validated_mapping.get("entry_count"),
                    "selected_entry_count": generated.get("selected_entry_count", len(questions))
                    if generated is not None
                    else len(questions),
                }
                result["comparison_mapping_sha256"] = mapping_hash
            if replay_value is not None:
                result["replayed_from"] = replay_value.get("run_id", replay_value.get("record_id"))
            return finish(result)
    except (OSError, TypeError, ValueError) as error:
        return finish(_accept_blocked(
            canonical_frozen_id,
            [f"accept_failed:{error}"],
            manifest_path=manifest_path,
        ))


def _ledger_path(value: Path | str) -> Path:
    path = Path(value)
    if path.name.endswith(".kd"):
        return path / "ledger.jsonl"
    return sidecar_path(path) / "ledger.jsonl"


def append_ledger(value: Path | str, entry: Mapping[str, object]) -> dict[str, object]:
    """Append one validated defect-ledger row without rewriting old rows."""
    required = ("id", "severity", "evidence", "fixed_by_this_card", "repair_batch_hash")
    missing = [name for name in required if name not in entry]
    if missing:
        raise ValidationError("ledger", value, "missing fields: " + ", ".join(missing))
    if not isinstance(entry["id"], str) or not entry["id"].strip():
        raise ValidationError("ledger", value, "id must be non-empty")
    if not isinstance(entry["severity"], str) or not entry["severity"].strip():
        raise ValidationError("ledger", value, "severity must be non-empty")
    if not isinstance(entry["evidence"], (str, Mapping, list)):
        raise ValidationError("ledger", value, "evidence must be structured")
    if not isinstance(entry["fixed_by_this_card"], bool):
        raise ValidationError("ledger", value, "fixed_by_this_card must be boolean")
    repair_hash = entry["repair_batch_hash"]
    if repair_hash is not None and (not isinstance(repair_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", repair_hash)):
        raise ValidationError("ledger", value, "repair_batch_hash must be null or sha256")
    row = dict(entry)
    row.setdefault("type", "defect")
    row.setdefault("recorded_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    path = _ledger_path(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return row


def read_ledger(value: Path | str) -> list[dict[str, object]]:
    path = _ledger_path(value)
    return _jsonl(path)


def void_record(value: Path | str, record_id: str, reason: str) -> dict[str, object]:
    if not isinstance(record_id, str) or not record_id.strip() or not isinstance(reason, str) or not reason.strip():
        raise ValidationError("ledger", value, "void record requires record_id and reason")
    path = _ledger_path(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "type": "void",
        "record_id": record_id,
        "reason": reason,
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return row


def _ledger_record_is_void(rows: Iterable[Mapping[str, object]], record_id: str) -> bool:
    return any(row.get("type") == "void" and row.get("record_id") == record_id for row in rows)


def discrimination_check(frozen_dir: Path | str, fixture: object | None = None) -> dict[str, object]:
    """Run the known-bad bindings and positive control against frozen input."""
    root = Path(frozen_dir)
    if root.is_file() and root.name == "manifest.json":
        root = root.parent
    fixture_value = _read_json_input(fixture)
    if fixture_value is None:
        for candidate in (root / "discrimination.json", root / "discrimination-fixture.json", root / "fixtures" / "discrimination.json"):
            if candidate.is_file():
                fixture_value = _read_json_input(candidate)
                break
    if not isinstance(fixture_value, Mapping) or not isinstance(fixture_value.get("samples"), list):
        return {"status": "blocked", "reason_code": "discrimination_fixture_missing", "samples": [], "conclusions": []}
    samples_out: list[dict[str, object]] = []
    all_ok = True
    positive_control_count = 0
    sources = {"input": root / "input", "comparison": root / "comparison"}
    for sample in fixture_value["samples"]:
        if not isinstance(sample, Mapping):
            all_ok = False
            continue
        sample_id = str(sample.get("sample_id", sample.get("id", "")))
        rows, reasons = _question_list(sample.get("questions", []))
        pages = sample.get("pages", sample.get("page_map", {}))
        judged = [] if reasons else [judge(question, pages, sources) for question in rows]
        expected = sample.get("expected_failure_reasons", sample.get("failure_reasons", []))
        expected_set = {str(item) for item in expected} if isinstance(expected, list) else set()
        # Discrimination asks whether the known-bad sample is rejected by the
        # answer gate.  A bad location can be a soft verdict failure (so the
        # aggregate rate threshold remains meaningful) without becoming a
        # hard provenance failure.
        failures = [row for row in judged if not bool(row.get("answer_hit"))]
        actual_reasons = [str(row.get("failure_reason")) for row in judged]
        must_fail = bool(sample.get("must_fail", sample.get("expect_failure", True)))
        if not must_fail:
            positive_control_count += 1
        reasons_ok = not must_fail or (isinstance(expected, list) and bool(expected_set) and (
            actual_reasons == [str(item) for item in expected]
            or expected_set == set(actual_reasons)
        ))
        sample_ok = (
            not reasons
            and len(rows) >= 2
            and ((len(failures) == len(rows)) if must_fail else not failures)
            and reasons_ok
        )
        all_ok = all_ok and sample_ok
        samples_out.append({"sample_id": sample_id, "status": "passed" if sample_ok else "failed", "results": judged, "reasons": reasons})
    if not samples_out:
        all_ok = False
    if positive_control_count == 0:
        all_ok = False
    if not all_ok and positive_control_count == 0:
        reason_code = "discrimination_positive_control_missing"
    elif not all_ok:
        reason_code = "discrimination_failed"
    else:
        reason_code = None
    return {
        "status": "passed" if all_ok else "failed",
        "reason_code": reason_code,
        "samples": samples_out,
        "positive_control_count": positive_control_count,
        "fixture_sha256": _json_sha256(fixture_value),
        "conclusions": samples_out,
    }


def _default_discrimination_fixture(frozen_dir: Path) -> dict[str, object]:
    frozen_root = Path(frozen_dir)
    comparison_snapshot = frozen_root / SNAPSHOT_ROOTS["comparison"]
    comparison_root = comparison_snapshot / "products"
    candidates = sorted(
        (path for path in comparison_root.rglob("*.md") if not path.is_symlink()),
        key=lambda path: _utf8_key(path.relative_to(comparison_snapshot).as_posix()),
    ) if comparison_root.is_dir() else []
    path = (
        candidates[0].relative_to(comparison_snapshot).as_posix()
        if candidates
        else "products/__control__/page.md"
    )

    def questions(prefix: str, anchor: str | None = None) -> list[dict[str, object]]:
        return [
            {
                "question_id": f"{prefix}-1",
                "prompt": f"{prefix} q1",
                "page_path": path,
                **({"page_anchor": anchor} if anchor else {}),
            },
            {
                "question_id": f"{prefix}-2",
                "prompt": f"{prefix} q2",
                "page_path": path,
                **({"page_anchor": anchor} if anchor else {}),
            },
        ]

    samples: list[dict[str, object]] = [
        {
            "sample_id": "missing-table",
            "must_fail": True,
            "questions": questions("missing-table", "reference-1"),
            "pages": {path: {"page_path": path, "text": "# Missing table\n"}},
            "expected_failure_reasons": ["location_invalid", "location_invalid"],
        },
        {
            "sample_id": "wrong-citation",
            "must_fail": True,
            "questions": questions("wrong-citation"),
            "pages": {
                path: {
                    "page_path": path,
                    "text": '<a id="reference-1"></a>\n# Wrong citation\n',
                    "evidence": [{
                        "page_path": path,
                        "source_uri": "wrong://citation",
                        "content_hash": "0" * 64,
                        "line_start": 1,
                        "line_end": 1,
                    }],
                }
            },
            "expected_failure_reasons": ["source_incorrect", "source_incorrect"],
        },
        {
            "sample_id": "orphan-page",
            "must_fail": True,
            "questions": questions("orphan-page"),
            "pages": {},
            "expected_failure_reasons": ["answer_missing", "answer_missing"],
        },
    ]

    input_snapshot = frozen_root / SNAPSHOT_ROOTS["input"]
    input_candidates = sorted(
        (candidate for candidate in input_snapshot.rglob("*.md") if not candidate.is_symlink()),
        key=lambda candidate: _utf8_key(candidate.relative_to(input_snapshot).as_posix()),
    ) if input_snapshot.is_dir() else []
    if candidates and input_candidates:
        source_path = input_candidates[0]
        source_text = source_path.read_text(encoding="utf-8")
        source_lines = source_text.splitlines()
        if source_lines:
            source_uri = source_path.relative_to(input_snapshot).as_posix()
            span = "\n".join(source_lines)
            samples.append({
                "sample_id": "correct-control",
                "must_fail": False,
                "questions": questions("correct-control"),
                "pages": {
                    path: {
                        "page_path": path,
                        "text": "# Correct control\nA valid acceptance control.\n",
                        "evidence": [{
                            "page_path": path,
                            "source_uri": source_uri,
                            "content_hash": hashlib.sha256(span.encode("utf-8")).hexdigest(),
                            "line_start": 1,
                            "line_end": len(source_lines),
                        }],
                    }
                },
            })
    return {"samples": samples}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knowledge-digest-accept")
    parser.add_argument("frozen_id", nargs="?")
    parser.add_argument("kb_dir", nargs="?", type=Path)
    parser.add_argument("extra_paths", nargs="*", type=Path)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-root", type=Path)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--release4-dir", "--before-dir", dest="release4_dir", type=Path)
    parser.add_argument("--comparison-dir", "--comparison-kb-dir", dest="comparison_dir", type=Path)
    parser.add_argument("--question-set", type=Path)
    parser.add_argument("--comparison-map", "--comparison-mapping", dest="comparison_mapping", type=Path)
    parser.add_argument("--replay", "--record", dest="replay", type=Path)
    parser.add_argument("--run-id")
    return parser


def _error_result(error: BaseException) -> dict[str, object]:
    return _blocked(None, [str(error)])


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.freeze:
            input_dir = args.input_dir or args.frozen_id
            release4_dir = args.release4_dir or args.kb_dir
            comparison_dir = args.comparison_dir or (args.extra_paths[0] if args.extra_paths else None)
            output = args.output or args.freeze_root or (args.extra_paths[1] if len(args.extra_paths) > 1 else None)
            result = globals()["freeze"](input_dir, release4_dir, comparison_dir, output)
        else:
            result = accept(
                args.frozen_id,
                args.kb_dir,
                freeze_root=args.freeze_root,
                output=args.output,
                question_set=args.question_set,
                comparison_mapping=args.comparison_mapping,
                replay=args.replay,
                run_id=args.run_id,
            )
    except (OSError, TypeError, ValueError) as error:
        result = _error_result(error)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in {"frozen", "ready", "pass"} else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "JUDGE_RULES_VERSION",
    "QUESTION_GENERATOR_POLICY",
    "QUESTION_GENERATOR_RULES_SHA256",
    "QUESTION_TEMPLATES",
    "COMPARISON_MAPPING_SCHEMA_VERSION",
    "MAPPED_QUESTION_GENERATOR_RULES_SHA256",
    "MAPPED_QUESTION_GENERATOR_VERSION",
    "accept",
    "append_ledger",
    "discrimination_check",
    "freeze",
    "generate_questions",
    "generate_mapped_questions",
    "judge",
    "main",
    "preflight",
    "read_ledger",
    "summarize",
    "void_record",
]
