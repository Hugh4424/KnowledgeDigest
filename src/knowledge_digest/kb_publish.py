"""CLI surface and publish primitives for the Task9 K3 release channel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

from .errors import ValidationError
from .kb_structure import default_publication_structure, inspect_structure
from .lock import kb_lock


SIDECAR_DIRECTORIES = ("versions", "staging", "lkg", "releases", "receipts", "freeze")
_VERSION_NAME = re.compile(r"(?P<date>\d{8})-\d{6}-(?P<seq>\d{3})\Z")
_SAFE_RELATIVE = re.compile(r"^[^/\\]+(?:/[^/\\]+)*\Z")
_SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_DEFAULT_COPY_FILE = shutil.copy2
_COPY_CHUNK_SIZE = 1024 * 1024


def _command_from_program(program: str) -> str:
    return "rollback" if Path(program).name.endswith("rollback") else "publish"


def _parser(command: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"knowledge-digest-{command}")
    if command == "publish":
        parser.add_argument("batch_dir", type=Path)
        parser.add_argument("kb_dir", type=Path)
    else:
        parser.add_argument("kb_dir", type=Path)
    return parser


def sidecar_path(kb_dir: Path) -> Path:
    """Return the hidden sibling directory that stores release state."""
    # Canonicalize only the parent.  macOS commonly exposes /var through a
    # symlink to /private/var; resolving the current pointer but not this
    # parent would make a valid pointer look like it escaped the sidecar.
    target = Path(kb_dir)
    if not target.name:
        raise ValidationError("sidecar", target, "knowledge base path must have a name")
    return target.parent.resolve(strict=False) / f".{target.name}.kd"


def ensure_sidecar(sidecar: Path) -> Path:
    """Create the fixed sidecar directory layout and return its root."""
    sidecar = Path(sidecar)
    if sidecar.is_symlink():
        raise ValidationError("sidecar", sidecar, "symbolic links are not allowed")
    sidecar.mkdir(parents=True, exist_ok=True)
    if not sidecar.is_dir():
        raise ValidationError("sidecar", sidecar, "sidecar path must be a directory")
    for name in SIDECAR_DIRECTORIES:
        child = sidecar / name
        child.mkdir(exist_ok=True)
        if child.is_symlink() or not child.is_dir():
            raise ValidationError("sidecar", child, "sidecar entry must be a directory")
    return sidecar


@contextmanager
def kb_write_lock(kb_dir: Path) -> Iterator[Path]:
    """Hold the existing lock against the knowledge-base parent directory."""
    target = Path(kb_dir)
    with kb_lock(target.parent) as lock_path:
        yield lock_path


def new_version_id(sidecar: Path, *, now: datetime | None = None) -> str:
    """Create a UTC timestamped version id with the next same-day sequence."""
    sidecar = Path(sidecar)
    versions = sidecar / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    date = current.strftime("%Y%m%d")
    sequence = 0
    for entry in versions.iterdir():
        match = _VERSION_NAME.fullmatch(entry.name)
        if match and match.group("date") == date:
            sequence = max(sequence, int(match.group("seq")))
    sequence += 1
    if sequence > 999:
        raise ValidationError("version_id", sidecar, "same-day version sequence exhausted")
    return f"{date}-{current.strftime('%H%M%S')}-{sequence:03d}"


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _safe_relative_path(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("publish", field, "path must be a non-empty relative path")
    if any(ord(character) < 32 or ord(character) == 127 or character in "\u2028\u2029" for character in value):
        raise ValidationError("publish", field, "path must not contain control characters")
    normalized = value.strip().replace("\\", "/")
    path = Path(normalized)
    if normalized in {".", ".."} or normalized.startswith("/") or any(part in {".", ".."} for part in path.parts) or not _SAFE_RELATIVE.fullmatch(normalized):
        raise ValidationError("publish", field, "path must stay within the knowledge base")
    return normalized


def _prepare_run_id(value: str | None, *, stage: str) -> tuple[str, ValidationError | None]:
    if value is None:
        return uuid.uuid4().hex, None
    if isinstance(value, str) and _SAFE_RUN_ID.fullmatch(value):
        return value, None
    safe_id = uuid.uuid4().hex
    return safe_id, ValidationError(stage, value, "run_id must be one safe path component")


def _frontmatter_bounds(text: str) -> tuple[int, int] | None:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return 1, index
    return None


def _declared_paths(structure_path: Path) -> set[str]:
    """Read the small managed-path extension plus existing structure roots."""
    text = structure_path.read_text(encoding="utf-8")
    bounds = _frontmatter_bounds(text)
    if bounds is None:
        raise ValidationError("publish", structure_path, "kb.structure.md requires frontmatter")
    lines = text.splitlines()
    start, end = bounds
    declared: set[str] = set()
    managed = False
    for index in range(start, end):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("managed_paths:"):
            inline = stripped.partition(":")[2].strip()
            managed = True
            if inline.startswith("[") and inline.endswith("]"):
                for item in inline[1:-1].split(","):
                    if item.strip():
                        declared.add(_safe_relative_path(item.strip().strip("'\""), field="managed_paths"))
            continue
        if managed and lines[index][:1].isspace() and stripped.startswith("-"):
            declared.add(_safe_relative_path(stripped[1:].strip().strip("'\""), field="managed_paths"))
            continue
        if managed and not lines[index][:1].isspace():
            managed = False
        key, separator, value = stripped.partition(":")
        if separator and key in {"roots", "publication_home", "publication_index_root", "publication_source_index", "topic_dir"}:
            value = value.strip()
            if key == "roots" and value.startswith("[") and value.endswith("]"):
                values = value[1:-1].split(",")
            else:
                values = [value]
            for item in values:
                item = item.strip().strip("'\"")
                if item:
                    declared.add(_safe_relative_path(item, field=key))
    return declared


def _with_managed_paths(text: str, paths: Sequence[str]) -> str:
    normalized = sorted({_safe_relative_path(path, field="managed_paths") for path in paths})
    if not normalized:
        return text
    lines = text.splitlines(keepends=True)
    bounds = _frontmatter_bounds(text)
    if bounds is None:
        raise ValidationError("publish", "kb.structure.md", "kb.structure.md requires frontmatter")
    _, end = bounds
    managed_index = next((index for index, line in enumerate(lines[:end]) if line.strip().startswith("managed_paths:")), None)
    existing: set[str] = set()
    if managed_index is not None:
        cursor = managed_index + 1
        while cursor < end and (not lines[cursor].strip() or lines[cursor].lstrip().startswith("-")):
            item = lines[cursor].strip()
            if item.startswith("-"):
                existing.add(item[1:].strip().strip("'\""))
            cursor += 1
    additions = [f"  - {path}\n" for path in normalized if path not in existing]
    if not additions:
        return text
    if managed_index is None:
        lines[end:end] = ["managed_paths:\n", *additions]
    else:
        insert_at = managed_index + 1
        while insert_at < end and (not lines[insert_at].strip() or lines[insert_at].lstrip().startswith("-")):
            insert_at += 1
        lines[insert_at:insert_at] = additions
    return "".join(lines)


def _manifest_page_paths(manifest: dict[str, object]) -> tuple[str, ...]:
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        raise ValidationError("publish", "pages", "manifest pages must be a list")
    paths: set[str] = set()
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValidationError("publish", f"pages[{index}]", "manifest page must be an object")
        candidates = page.get("page_paths")
        if candidates is None:
            candidates = [page.get("page_path")] if page.get("page_path") is not None else []
        if not isinstance(candidates, list):
            raise ValidationError("publish", f"pages[{index}].page_paths", "page_paths must be a list")
        for candidate in candidates:
            normalized = _safe_relative_path(candidate, field=f"pages[{index}].page_path")
            allowed_root = normalized.startswith(("products/", "indexes/"))
            allowed_file = normalized in {"Home.md", "Index.md", "Audit.md"}
            if not normalized.endswith(".md") or not (allowed_root or allowed_file):
                raise ValidationError("publish", normalized, "manifest page path is outside publication roots")
            paths.add(normalized)
    return tuple(sorted(paths))


def _hash_file_no_follow(path: Path, *, stage: str) -> str:
    """Hash a regular file through a no-follow descriptor."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    digest = hashlib.sha256()
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow)
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValidationError(stage, path, "copy source must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            while chunk := stream.read(_COPY_CHUNK_SIZE):
                digest.update(chunk)
    except ValidationError:
        raise
    except OSError as error:
        raise ValidationError(stage, path, "file cannot be read without following a symlink") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return digest.hexdigest()


def _copy_file_no_follow(source: Path, destination: Path, *, stage: str) -> None:
    """Copy one regular file from a stable source descriptor.

    The source is opened with O_NOFOLLOW before any bytes are read.  This
    keeps a path replacement between the directory walk and the copy from
    redirecting the copy outside the frozen/published tree.
    """
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    source_descriptor: int | None = None
    destination_descriptor: int | None = None
    source_digest = hashlib.sha256()
    try:
        source_descriptor = os.open(source, os.O_RDONLY | nofollow)
        source_stat = os.fstat(source_descriptor)
        if not stat.S_ISREG(source_stat.st_mode):
            raise ValidationError(stage, source, "copy source must be a regular file")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination_descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC | nofollow,
            stat.S_IMODE(source_stat.st_mode),
        )
        with (
            os.fdopen(source_descriptor, "rb", closefd=False) as source_stream,
            os.fdopen(destination_descriptor, "wb", closefd=False) as destination_stream,
        ):
            while chunk := source_stream.read(_COPY_CHUNK_SIZE):
                source_digest.update(chunk)
                destination_stream.write(chunk)
            destination_stream.flush()
            os.fsync(destination_descriptor)
        after_stat = os.fstat(source_descriptor)
        if (
            (after_stat.st_dev, after_stat.st_ino, after_stat.st_size, after_stat.st_mtime_ns)
            != (source_stat.st_dev, source_stat.st_ino, source_stat.st_size, source_stat.st_mtime_ns)
        ):
            raise ValidationError(stage, source, "copy source changed during read")
    except ValidationError:
        raise
    except OSError as error:
        raise ValidationError(stage, source, "safe file copy failed") from error
    finally:
        if source_descriptor is not None:
            os.close(source_descriptor)
        if destination_descriptor is not None:
            os.close(destination_descriptor)
    if _hash_file_no_follow(destination, stage=stage) != source_digest.hexdigest():
        raise ValidationError(stage, destination, "copy verification failed")


def _copy_file_verified(
    source: Path,
    destination: Path,
    *,
    copy_file: Callable[[Path, Path], object],
) -> None:
    source_stat = os.lstat(source)
    if not stat.S_ISREG(source_stat.st_mode):
        raise ValidationError("publish", source, "copy source must be a regular file")
    if copy_file is _DEFAULT_COPY_FILE:
        _copy_file_no_follow(source, destination, stage="publish")
        return
    copy_file(source, destination)
    after_stat = os.lstat(source)
    if (
        not stat.S_ISREG(after_stat.st_mode)
        or (after_stat.st_dev, after_stat.st_ino) != (source_stat.st_dev, source_stat.st_ino)
    ):
        raise ValidationError("publish", source, "copy source changed during copy")
    if not destination.is_file() or destination.is_symlink() or destination.read_bytes() != source.read_bytes():
        raise ValidationError("publish", destination, "copy verification failed")


def _copy_tree(source: Path, destination: Path, *, copy_file: Callable[[Path, Path], object] | None = None) -> None:
    copy_file = copy_file or _DEFAULT_COPY_FILE
    if source.is_symlink():
        raise ValidationError("publish", source, "symbolic links are not allowed in a version")
    if not source.is_dir():
        raise ValidationError("publish", source, "version source must be a directory")
    destination.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix().encode("utf-8")):
        relative = entry.relative_to(source)
        target = destination / relative
        if entry.is_symlink():
            raise ValidationError("publish", entry, "symbolic links are not allowed in a version")
        if entry.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif entry.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            _copy_file_verified(entry, target, copy_file=copy_file)
        else:
            raise ValidationError("publish", entry, "version contains a non-regular file")


def _current_target(kb_dir: Path) -> Path | None:
    target_root = Path(kb_dir).absolute()
    current = target_root / "current"
    if not current.exists() and not current.is_symlink():
        return None
    if not current.is_symlink():
        raise ValidationError("publish", current, "current_name_conflict")
    try:
        target = current.resolve(strict=True)
    except OSError as error:
        raise ValidationError("publish", current, "current pointer target is missing") from error
    if not target.is_dir():
        raise ValidationError("publish", current, "current pointer must target a directory")
    if target.parent != sidecar_path(target_root) / "versions":
        raise ValidationError("publish", current, "current pointer escapes the versions directory")
    return target


def _validate_structure(structure_path: Path) -> None:
    if structure_path.is_symlink() or not structure_path.is_file():
        raise ValidationError("publish", structure_path, "kb.structure.md is missing or not a regular file")
    contract = inspect_structure(structure_path)
    if not contract.allow_official_write:
        raise ValidationError("publish", structure_path, "kb.structure.md is not a valid publication structure")
    _declared_paths(structure_path)


def ensure_target_kb(kb_dir: Path, sidecar: Path | None = None) -> dict[str, object]:
    """Validate an existing target or create its default declaration when empty."""
    target = Path(kb_dir)
    if sidecar is not None:
        ensure_sidecar(sidecar)
    if target.is_symlink():
        raise ValidationError("publish", target, "target knowledge base must not be a symlink")
    if not target.exists():
        if not target.parent.is_dir():
            raise ValidationError("publish", target.parent, "knowledge base parent must exist")
        target.mkdir()
    if not target.is_dir():
        raise ValidationError("publish", target, "knowledge base target must be a directory")
    current_target = _current_target(target)
    if current_target is not None:
        structure = current_target / "kb.structure.md"
        _validate_structure(structure)
        return {
            "status": "existing",
            "base_dir": current_target,
            "structure_path": structure,
            "structure_sha256": hashlib.sha256(structure.read_bytes()).hexdigest(),
        }

    entries = list(target.iterdir())
    structure = target / "kb.structure.md"
    if not entries:
        _atomic_write_text(
            structure,
            _with_managed_paths(default_publication_structure(), ("products", "Home.md", "Index.md")),
        )
        return {
            "status": "initialized",
            "base_dir": target,
            "structure_path": structure,
            "structure_sha256": hashlib.sha256(structure.read_bytes()).hexdigest(),
        }
    _validate_structure(structure)
    return {
        "status": "existing",
        "base_dir": target,
        "structure_path": structure,
        "structure_sha256": hashlib.sha256(structure.read_bytes()).hexdigest(),
    }


def construct_staging(
    kb_dir: Path,
    batch_dir: Path,
    manifest: dict[str, object],
    sidecar: Path,
    *,
    run_id: str = "staging-run",
    copy_file: Callable[[Path, Path], object] | None = None,
) -> dict[str, object]:
    """Build a complete candidate version without touching the reader entry."""
    target = Path(kb_dir)
    batch = Path(batch_dir)
    safe_run_id, run_id_error = _prepare_run_id(run_id, stage="publish")
    if run_id_error is not None:
        raise run_id_error
    run_id = safe_run_id
    sidecar = ensure_sidecar(sidecar)
    copy_file = copy_file or _DEFAULT_COPY_FILE
    if not batch.is_dir():
        raise ValidationError("publish", batch, "batch directory must exist")
    state = ensure_target_kb(target, sidecar)
    base_dir = Path(state["base_dir"])
    staging = sidecar / "staging" / run_id
    if staging.exists():
        raise ValidationError("publish", staging, "staging run already exists")
    staging.mkdir(parents=True)
    try:
        _copy_tree(base_dir, staging, copy_file=copy_file)
        structure_path = staging / "kb.structure.md"
        page_paths = _manifest_page_paths(manifest)
        if not structure_path.is_file():
            _atomic_write_text(
                structure_path,
                _with_managed_paths(default_publication_structure(), ("products", "Home.md", "Index.md")),
            )
        for page_path in page_paths:
            source = batch / page_path
            if source.is_symlink() or not source.is_file():
                raise ValidationError("publish", page_path, "manifest page is missing or not a regular file")
        structure_text = structure_path.read_text(encoding="utf-8")
        _atomic_write_text(structure_path, _with_managed_paths(structure_text, page_paths))
        declared = _declared_paths(structure_path)
        copied_page_paths: set[str] = set()
        for source in sorted(batch.rglob("*"), key=lambda item: item.relative_to(batch).as_posix().encode("utf-8")):
            if source.is_symlink():
                raise ValidationError("publish", source, "symbolic links are not allowed in a batch")
            if not source.is_file():
                continue
            relative = source.relative_to(batch).as_posix()
            if relative in {"kb.structure.md", "current"} or relative.startswith("."):
                raise ValidationError("publish", relative, "control path is not batch-writable")
            allowed = relative == "README.md" or relative.startswith("_audit/") or relative in page_paths
            allowed = allowed or any(relative == path or relative.startswith(f"{path}/") for path in declared)
            if not allowed:
                reason = "path_collision_unmanaged" if (base_dir / relative).exists() else "path_outside_allowed"
                raise ValidationError("publish", relative, reason)
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            _copy_file_verified(source, destination, copy_file=copy_file)
            if relative in page_paths:
                copied_page_paths.add(relative)
        missing_page_paths = sorted(set(page_paths) - copied_page_paths)
        if missing_page_paths:
            raise ValidationError(
                "publish",
                "pages",
                "manifest pages were not copied: " + ", ".join(missing_page_paths),
            )
        _validate_structure(structure_path)
        tree_hash = kb_tree_hash(staging)
        return {"staging_dir": staging, "tree_hash": tree_hash, "base_dir": base_dir, "state": state}
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def kb_tree_hash(root: Path) -> str:
    """Hash a version tree using the frozen path-and-file digest algorithm."""
    root = Path(root)
    if root.is_symlink():
        raise ValidationError("kb_tree_hash", root, "symbolic links are not allowed")
    if not root.is_dir():
        raise ValidationError("kb_tree_hash", root, "version root must be an existing directory")

    files: list[Path] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in [*directory_names, *file_names]:
            candidate = directory_path / name
            if candidate.is_symlink():
                raise ValidationError("kb_tree_hash", candidate, "symbolic links are not allowed")
        files.extend(directory_path / name for name in file_names)

    rows: list[bytes] = []
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        if not path.is_file():
            raise ValidationError("kb_tree_hash", path, "version tree contains a non-regular file")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(root).as_posix()
        rows.append(f"{relative}:{digest}\n".encode("utf-8"))
    return hashlib.sha256(b"".join(rows)).hexdigest()


def load_batch_manifest(batch_dir: Path) -> dict[str, object]:
    """Read and explicitly validate the K1/K2 release whitelist fields."""
    manifest_path = Path(batch_dir) / "_audit" / "page-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"status": "blocked", "reasons": ["manifest"], "manifest": None}
    if not isinstance(manifest, dict):
        return {"status": "blocked", "reasons": ["manifest"], "manifest": manifest}

    reasons: list[str] = []
    if manifest.get("schema_version") != "task7-page-manifest.v1":
        reasons.append("schema_version")
    if not isinstance(manifest.get("attempt_id"), str) or not manifest["attempt_id"].strip():
        reasons.append("attempt_id")
    if manifest.get("run_status") != "complete":
        reasons.append("run_status")
    if manifest.get("publish_status") != "not_released":
        reasons.append("publish_status")
    navigation = manifest.get("navigation")
    if not isinstance(navigation, dict) or navigation.get("navigation_status") != "generated_ok":
        reasons.append("navigation.navigation_status")
    blockers = manifest.get("blockers")
    if not isinstance(blockers, list) or blockers:
        reasons.append("blockers")
    return {
        "status": "ready" if not reasons else "blocked",
        "reasons": reasons,
        "manifest": manifest,
    }


class _PublishBlocked(RuntimeError):
    def __init__(self, reasons: Sequence[str]) -> None:
        self.reasons = tuple(reasons)
        self.reason_code = "batch_not_publishable"
        super().__init__("batch is not publishable: " + ", ".join(self.reasons))


class _Cancelled(RuntimeError):
    reason_code = "cancelled"


class _RollbackPointerInvalid(RuntimeError):
    reason_code = "rollback_pointer_invalid"


def _default_compile_metrics() -> dict[str, object]:
    return {
        "elapsed_ms": 0,
        "provider_calls": 0,
        "provider_tokens": 0,
        "reasons": {
            "elapsed_ms": "no_provider_call_yet",
            "provider_calls": "no_provider_call_yet",
            "provider_tokens": "no_provider_call_yet",
        },
    }


def _read_compile_metrics(batch_dir: Path) -> dict[str, object]:
    path = Path(batch_dir) / "_audit" / "run-metrics.json"
    if not path.is_file():
        return _default_compile_metrics()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("cost", path, "run-metrics.json is invalid") from error
    if not isinstance(value, dict):
        raise ValidationError("cost", path, "run-metrics.json must be an object")
    if not any(key in value for key in ("elapsed_ms", "provider_calls", "provider_tokens")) and not isinstance(value.get("task8_navigation"), dict):
        return _default_compile_metrics()

    def component(source: dict[str, object], label: str, *, required: bool) -> dict[str, object]:
        raw_reasons = source.get("reasons", {})
        if not isinstance(raw_reasons, dict):
            raise ValidationError("cost", path, f"{label}.reasons must be an object")
        normalized: dict[str, object] = {"reasons": {}}
        for key in ("elapsed_ms", "provider_calls", "provider_tokens"):
            metric = source.get(key)
            if metric is None and label == "task8_navigation" and key == "provider_calls":
                metric = source.get("actual_provider_calls")
            if metric is None and label == "task8_navigation" and key == "provider_tokens":
                metric = source.get("actual_provider_tokens")
            if metric is None:
                if required:
                    raise ValidationError("cost", path, f"{label}.{key} is missing")
                metric = 0
            if isinstance(metric, bool) or not isinstance(metric, int) or metric < 0:
                raise ValidationError("cost", path, f"{label}.{key} must be a non-negative integer")
            normalized[key] = metric
            reason = raw_reasons.get(key)
            if reason is not None:
                if not isinstance(reason, str) or not reason.strip():
                    raise ValidationError("cost", path, f"{label}.{key} has an invalid reason")
                if reason == "provider_usage_unavailable":
                    reason = "provider_unavailable"
                if reason not in {"cache_hit", "no_provider_call_yet", "provider_unavailable"}:
                    raise ValidationError("cost", path, f"{label}.{key} has an unsupported reason")
                if metric != 0:
                    raise ValidationError("cost", path, f"{label}.{key} has a zero-value reason with a positive count")
                normalized["reasons"][key] = reason
            elif metric == 0:
                raise ValidationError("cost", path, f"{label}.{key}=0 requires a reason")
        return normalized

    top = component(value, "compile", required=True)
    navigation = value.get("task8_navigation")
    if navigation is not None and not isinstance(navigation, dict):
        raise ValidationError("cost", path, "task8_navigation must be an object")
    if navigation is None:
        return top
    task8 = component(navigation, "task8_navigation", required=True)
    normalized = {"reasons": {}}
    for key in ("elapsed_ms", "provider_calls", "provider_tokens"):
        total = int(top[key]) + int(task8[key])
        normalized[key] = total
        if total == 0:
            component_reasons = [
                dict(top["reasons"]).get(key),
                dict(task8["reasons"]).get(key),
            ]
            reason = next((item for item in component_reasons if item == "provider_unavailable"), None)
            reason = reason or next((item for item in component_reasons if item == "cache_hit"), None)
            reason = reason or next((item for item in component_reasons if item == "no_provider_call_yet"), None)
            if reason is None:
                raise ValidationError("cost", path, f"aggregated {key}=0 requires a reason")
            normalized["reasons"][key] = reason
    return normalized


def build_run_record(
    *,
    run_id: str,
    command: str,
    batch_attempt_id: str | None,
    target_kb_tree_hash: str | None,
    compile_metrics: dict[str, object],
    publish_elapsed_ms: int,
    reason_code: str | None,
    exit_code: int,
) -> dict[str, object]:
    """Build the shared run/receipt schema with compile-side attribution."""
    compile_reasons = dict(compile_metrics.get("reasons", {}))
    compile_elapsed = int(compile_metrics["elapsed_ms"])
    compile_calls = int(compile_metrics["provider_calls"])
    compile_tokens = int(compile_metrics["provider_tokens"])
    publish_elapsed_ms = max(0, int(publish_elapsed_ms))
    total_calls = compile_calls
    total_tokens = compile_tokens
    reasons = dict(compile_reasons)
    if compile_elapsed == 0 and "elapsed_ms" not in reasons:
        reasons["elapsed_ms"] = "no_provider_call_yet"
    if total_calls == 0 and "provider_calls" not in reasons:
        reasons["provider_calls"] = "no_provider_call_yet"
    if total_tokens == 0 and "provider_tokens" not in reasons:
        reasons["provider_tokens"] = "no_provider_call_yet"
    return {
        "run_id": run_id,
        "command": command,
        "target_kb_tree_hash": target_kb_tree_hash,
        "batch_attempt_id": batch_attempt_id,
        "elapsed_ms": compile_elapsed + publish_elapsed_ms,
        "provider_calls": total_calls,
        "provider_tokens": total_tokens,
        "compile": {
            "elapsed_ms": compile_elapsed,
            "provider_calls": compile_calls,
            "provider_tokens": compile_tokens,
            "inherited_from_compile": True,
        },
        "publish": {
            "elapsed_ms": publish_elapsed_ms,
            "provider_calls": 0,
            "provider_tokens": 0,
            "reasons": {
                "provider_calls": "no_provider_call_yet",
                "provider_tokens": "no_provider_call_yet",
            },
        },
        "reasons": reasons,
        "reason_code": reason_code,
        "exit_code": int(exit_code),
    }


def _atomic_write_json(path: Path, value: object) -> None:
    _atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _version_id_from_target(target: Path) -> str:
    return target.name if target.parent.name == "versions" else "bootstrap"


def _source_batch_attempt(sidecar: Path, target: Path | None) -> str | None:
    """Recover the batch identity that produced an existing version."""
    if target is None:
        return None
    version_id = _version_id_from_target(target)
    if version_id == "bootstrap":
        return None
    release_path = Path(sidecar) / "releases" / f"{version_id}.json"
    try:
        value = json.loads(release_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    attempt_id = value.get("batch_attempt_id") if isinstance(value, dict) else None
    return attempt_id if isinstance(attempt_id, str) and attempt_id else None


def _cleanup_staging(sidecar: Path, *, keep: str | None = None) -> None:
    """Remove only owned staging children left by an earlier run."""
    staging_root = Path(sidecar) / "staging"
    if not staging_root.is_dir() or staging_root.is_symlink():
        return
    for entry in staging_root.iterdir():
        if keep is not None and entry.name == keep:
            continue
        _remove_path(entry)


def _replace_current(kb_dir: Path, version_id: str, run_id: str, replace_file: Callable[[Path, Path], object]) -> None:
    current = Path(kb_dir) / "current"
    temporary = Path(kb_dir) / f".current.{run_id}.tmp"
    temporary.unlink(missing_ok=True)
    try:
        temporary.symlink_to(f"../{sidecar_path(kb_dir).name}/versions/{version_id}")
        replace_file(temporary, current)
    finally:
        temporary.unlink(missing_ok=True)


def _restore_current_after_failure(
    kb_dir: Path,
    *,
    old_link_value: str | None,
    fallback_version_id: str | None,
    fallback_tree_hash: str | None,
    run_id: str,
) -> tuple[bool, str | None, bool]:
    """Restore the old pointer or retain a verified new pointer after failure.

    A failed restore must never be followed by deleting the version that the
    current link may still reference.  If restoring the old link fails, keep
    the new version and verify it instead; an unverified recovery remains
    explicit in the caller's result while the version stays recoverable.
    """
    try:
        if old_link_value is not None:
            restore_id = Path(old_link_value).name
            _replace_current(kb_dir, restore_id, f"restore-{run_id}", os.replace)
        else:
            current = Path(kb_dir) / "current"
            if current.is_symlink():
                current.unlink()
        return False, None, True
    except OSError as restore_error:
        warning = f"current restore failed: {restore_error}"
        try:
            if not isinstance(fallback_version_id, str) or not fallback_version_id:
                raise ValidationError("publish", Path(kb_dir) / "current", "fallback version id is missing")
            fallback = sidecar_path(kb_dir) / "versions" / fallback_version_id
            if not fallback.is_dir():
                raise ValidationError("publish", fallback, "fallback version is missing")
            try:
                current_target = _current_target(Path(kb_dir))
            except (OSError, ValueError, ValidationError):
                current_target = None
            if current_target is None or _version_id_from_target(current_target) != fallback_version_id:
                _replace_current(kb_dir, fallback_version_id, f"retain-{run_id}", os.replace)
            current_target = _current_target(Path(kb_dir))
            if current_target is None or _version_id_from_target(current_target) != fallback_version_id:
                raise ValidationError("publish", Path(kb_dir) / "current", "fallback current target is invalid")
            if fallback_tree_hash is not None and kb_tree_hash(current_target) != fallback_tree_hash:
                raise ValidationError("publish", Path(kb_dir) / "current", "fallback current tree hash mismatch")
        except (OSError, ValueError, ValidationError) as fallback_error:
            return True, f"{warning}; fallback current validation failed: {fallback_error}", False
        return True, f"{warning}; retained verified fallback current", True


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _clear_bootstrap_root(kb_dir: Path) -> None:
    for entry in Path(kb_dir).iterdir():
        if entry.name != "current":
            _remove_path(entry)


def _prune_lkg(sidecar: Path, keep: str | None) -> None:
    lkg = Path(sidecar) / "lkg"
    for entry in lkg.iterdir():
        if entry.name == "pointer.json" or entry.name == keep:
            continue
        _remove_path(entry)


def _check_injection(
    point: str,
    *,
    cancel: Callable[[], bool] | None,
    fault: Callable[[str], object] | None,
) -> None:
    if cancel is not None and cancel():
        raise _Cancelled("publish cancelled at " + point)
    if fault is not None:
        fault(point)


def _result_from_record(
    *,
    status: str,
    record: dict[str, object],
    old_tree_hash: str | None,
    new_tree_hash: str | None,
    version_id: str | None,
    no_op: bool,
    verified: bool,
    receipt_path: Path | None = None,
) -> dict[str, object]:
    return {
        **record,
        "status": status,
        "old_tree_hash": old_tree_hash,
        "new_tree_hash": new_tree_hash,
        "version_id": version_id,
        "no_op": no_op,
        "verified": verified,
        **({"receipt_path": str(receipt_path)} if receipt_path is not None else {}),
    }


def publish(
    batch_dir: Path,
    kb_dir: Path,
    *,
    cancel: Callable[[], bool] | None = None,
    run_id: str | None = None,
    now: datetime | None = None,
    copy_file: Callable[[Path, Path], object] | None = None,
    replace_file: Callable[[Path, Path], object] | None = None,
    fault: Callable[[str], object] | None = None,
) -> dict[str, object]:
    """Publish one valid batch through a lock, staging tree and fixed pointer."""
    target = Path(kb_dir)
    batch = Path(batch_dir)
    run_id, run_id_error = _prepare_run_id(run_id, stage="publish")
    copy_file = copy_file or _DEFAULT_COPY_FILE
    replace_file = replace_file or os.replace
    sidecar = sidecar_path(target)
    started = time.monotonic()
    compile_metrics: dict[str, object] = _default_compile_metrics()
    manifest: dict[str, object] | None = None
    initial_entries: list[Path] = []
    created_target = False
    initialized = False
    old_target: Path | None = None
    old_link_value: str | None = None
    old_pointer_raw: str | None = None
    version_path: Path | None = None
    lkg_temp: Path | None = None
    lkg_path: Path | None = None
    lkg_preexisting = False
    staging_path: Path | None = None
    switched = False
    preserve_version_path = False
    recovery_warning: str | None = None
    recovery_verified = True
    pointer_written = False
    pointer_restore_failed = False
    old_tree_hash: str | None = None
    new_tree_hash: str | None = None
    version_id: str | None = None
    try:
        if run_id_error is not None:
            raise run_id_error
        with kb_write_lock(target):
            ensure_sidecar(sidecar)
            _cleanup_staging(sidecar)
            if not target.exists():
                created_target = True
            target_exists_before = target.exists()
            if target_exists_before and target.is_dir():
                initial_entries = list(target.iterdir())
            if not target_exists_before or (target_exists_before and target.is_dir() and not initial_entries):
                # The empty target is still a real, reproducible pre-publish
                # state. Keep its hash for failure receipts and rollback
                # diagnostics even if initialization is later reverted.
                old_tree_hash = hashlib.sha256(b"").hexdigest()
            current = target / "current"
            if current.is_symlink():
                old_link_value = os.readlink(current)
                old_target = _current_target(target)
            decision = load_batch_manifest(batch)
            candidate = decision.get("manifest")
            if isinstance(candidate, dict):
                manifest = candidate
            try:
                compile_metrics = _read_compile_metrics(batch)
            except ValidationError:
                compile_metrics = _default_compile_metrics()
                raise
            if decision["status"] != "ready":
                raise _PublishBlocked(decision["reasons"])
            state_before = ensure_target_kb(target, sidecar)
            initialized = state_before["status"] == "initialized" and not initial_entries
            if old_target is None and initial_entries:
                old_target = target
            if old_target is not None:
                old_tree_hash = kb_tree_hash(old_target)
            pointer = sidecar / "lkg" / "pointer.json"
            if pointer.exists():
                old_pointer_raw = pointer.read_text(encoding="utf-8")
            _check_injection("before_staging", cancel=cancel, fault=fault)
            staging_path = sidecar / "staging" / run_id
            staged = construct_staging(
                target,
                batch,
                manifest,
                sidecar,
                run_id=run_id,
                copy_file=copy_file,
            )
            staging = Path(staged["staging_dir"])
            new_tree_hash = str(staged["tree_hash"])
            if (
                old_target is not None
                and _version_id_from_target(old_target) != "bootstrap"
                and old_tree_hash == new_tree_hash
            ):
                record = build_run_record(
                    run_id=run_id,
                    command="publish",
                    batch_attempt_id=str(manifest.get("attempt_id")),
                    target_kb_tree_hash=old_tree_hash,
                    compile_metrics=compile_metrics,
                    publish_elapsed_ms=int((time.monotonic() - started) * 1000),
                    reason_code=None,
                    exit_code=0,
                )
                release_id = _version_id_from_target(old_target)
                release = _result_from_record(
                    status="released",
                    record=record,
                    old_tree_hash=old_tree_hash,
                    new_tree_hash=new_tree_hash,
                    version_id=release_id,
                    no_op=True,
                    verified=True,
                )
                shutil.rmtree(Path(staged["staging_dir"]), ignore_errors=True)
                _atomic_write_json(sidecar / "releases" / f"noop-{run_id}.json", release)
                return release
            _check_injection("before_version_move", cancel=cancel, fault=fault)
            version_id = new_version_id(sidecar, now=now)
            version_path = sidecar / "versions" / version_id
            replace_file(staging, version_path)
            if kb_tree_hash(version_path) != new_tree_hash:
                raise ValidationError("publish", version_path, "version tree hash changed during move")
            if old_target is not None:
                old_version_id = _version_id_from_target(old_target)
                lkg_path = sidecar / "lkg" / old_version_id
                lkg_temp = sidecar / "lkg" / f".{old_version_id}.{run_id}.tmp"
                lkg_preexisting = lkg_path.exists() or lkg_path.is_symlink()
                if lkg_preexisting:
                    raise ValidationError("publish", lkg_path, "LKG slot already exists")
                _remove_path(lkg_temp)
                _copy_tree(old_target, lkg_temp, copy_file=copy_file)
                if kb_tree_hash(lkg_temp) != old_tree_hash:
                    raise ValidationError("publish", lkg_temp, "LKG tree hash changed during copy")
            _check_injection("before_switch", cancel=cancel, fault=fault)
            _replace_current(target, version_id, run_id, replace_file)
            switched = True
            _check_injection("after_switch", cancel=cancel, fault=fault)
            current_target = _current_target(target)
            if current_target is None or kb_tree_hash(current_target) != new_tree_hash:
                raise ValidationError("publish", target / "current", "readback tree hash mismatch")
            if lkg_temp is not None and lkg_path is not None:
                replace_file(lkg_temp, lkg_path)
                pointer_value = {
                    "version_id": lkg_path.name,
                    "tree_hash": old_tree_hash,
                    "batch_attempt_id": _source_batch_attempt(sidecar, old_target),
                    "written_at": (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
                _atomic_write_json(sidecar / "lkg" / "pointer.json", pointer_value)
                pointer_written = True
            _check_injection("before_release_record", cancel=cancel, fault=fault)
            record = build_run_record(
                run_id=run_id,
                command="publish",
                batch_attempt_id=str(manifest.get("attempt_id")),
                target_kb_tree_hash=new_tree_hash,
                compile_metrics=compile_metrics,
                publish_elapsed_ms=int((time.monotonic() - started) * 1000),
                reason_code=None,
                exit_code=0,
            )
            release = _result_from_record(
                status="released",
                record=record,
                old_tree_hash=old_tree_hash,
                new_tree_hash=new_tree_hash,
                version_id=version_id,
                no_op=False,
                verified=True,
            )
            _atomic_write_json(sidecar / "releases" / f"{version_id}.json", release)
            cleanup_warnings: list[str] = []
            try:
                _check_injection("before_root_cleanup", cancel=cancel, fault=fault)
                _clear_bootstrap_root(target)
            except Exception as cleanup_error:
                cleanup_warnings.append(f"root_cleanup:{cleanup_error}")
            try:
                _prune_lkg(sidecar, lkg_path.name if lkg_path is not None else None)
            except Exception as cleanup_error:
                cleanup_warnings.append(f"lkg_prune:{cleanup_error}")
            if cleanup_warnings:
                release["cleanup_warnings"] = cleanup_warnings
                try:
                    _atomic_write_json(sidecar / "releases" / f"{version_id}.json", release)
                except (OSError, TypeError, ValueError):
                    pass
            return release
    except Exception as error:
        if staging_path is not None and staging_path.exists():
            _remove_path(staging_path)
        if switched:
            preserve_version_path, recovery_warning, recovery_verified = _restore_current_after_failure(
                target,
                old_link_value=old_link_value,
                fallback_version_id=version_id,
                fallback_tree_hash=new_tree_hash,
                run_id=run_id,
            )
        if pointer_written and not preserve_version_path:
            pointer = sidecar / "lkg" / "pointer.json"
            try:
                if old_pointer_raw is None:
                    pointer.unlink(missing_ok=True)
                else:
                    _atomic_write_text(pointer, old_pointer_raw)
            except OSError:
                pointer_restore_failed = True
        if not preserve_version_path and version_path is not None and version_path.exists():
            shutil.rmtree(version_path, ignore_errors=True)
        if lkg_temp is not None and (lkg_temp.exists() or lkg_temp.is_symlink()):
            _remove_path(lkg_temp)
        if lkg_path is not None and not preserve_version_path and not pointer_restore_failed and not lkg_preexisting and (lkg_path.exists() or lkg_path.is_symlink()):
            _remove_path(lkg_path)
        if initialized and not initial_entries and target.exists():
            for entry in list(target.iterdir()):
                _remove_path(entry)
            if created_target:
                target.rmdir()
        reason_code = getattr(error, "reason_code", None)
        if reason_code is None:
            reason_code = error.reason if isinstance(error, ValidationError) else "publish_failed"
        if recovery_warning is not None and not recovery_verified:
            reason_code = "restore_uncertain"
        status = "blocked" if isinstance(error, (ValidationError, _PublishBlocked)) else "failed"
        exit_code = 2 if status == "blocked" else 1
        batch_attempt_id = str(manifest.get("attempt_id")) if manifest is not None and manifest.get("attempt_id") is not None else None
        target_hash = old_tree_hash
        try:
            current_target = _current_target(target)
            if current_target is not None:
                target_hash = kb_tree_hash(current_target)
        except (OSError, ValueError):
            target_hash = old_tree_hash
        record = build_run_record(
            run_id=run_id,
            command="publish",
            batch_attempt_id=batch_attempt_id,
            target_kb_tree_hash=target_hash,
            compile_metrics=compile_metrics,
            publish_elapsed_ms=int((time.monotonic() - started) * 1000),
            reason_code=str(reason_code),
            exit_code=exit_code,
        )
        if recovery_warning is not None:
            record["recovery_warning"] = recovery_warning
            record["recovery_verified"] = recovery_verified
        receipt = {**record, "receipt": True, "error": str(error)}
        receipt_path = sidecar / "receipts" / f"{run_id}.json"
        try:
            ensure_sidecar(sidecar)
            _atomic_write_json(receipt_path, receipt)
        except (OSError, TypeError, ValueError) as sink_error:
            receipt = {
                **receipt,
                "reason_code": "receipt_sink_unavailable",
                "receipt_sink_error": str(sink_error),
                "original_reason_code": str(reason_code),
            }
            receipt_path = None
        return _result_from_record(
            status=status,
            record=receipt,
            old_tree_hash=old_tree_hash,
            new_tree_hash=new_tree_hash,
            version_id=version_id,
            no_op=False,
            verified=False,
            receipt_path=receipt_path,
        )


def rollback(
    kb_dir: Path,
    *,
    cancel: Callable[[], bool] | None = None,
    run_id: str | None = None,
    now: datetime | None = None,
    copy_file: Callable[[Path, Path], object] | None = None,
    replace_file: Callable[[Path, Path], object] | None = None,
    fault: Callable[[str], object] | None = None,
) -> dict[str, object]:
    """Restore the LKG version while applying the same atomic swap protocol."""
    target = Path(kb_dir)
    run_id, run_id_error = _prepare_run_id(run_id, stage="rollback")
    copy_file = copy_file or _DEFAULT_COPY_FILE
    replace_file = replace_file or os.replace
    sidecar = sidecar_path(target)
    started = time.monotonic()
    compile_metrics = _default_compile_metrics()
    old_target: Path | None = None
    old_link_value: str | None = None
    old_pointer_raw: str | None = None
    pointer_value: dict[str, object] | None = None
    version_path: Path | None = None
    lkg_temp: Path | None = None
    lkg_path: Path | None = None
    lkg_preexisting = False
    staging_path: Path | None = None
    switched = False
    pointer_written = False
    preserve_version_path = False
    recovery_warning: str | None = None
    recovery_verified = True
    old_tree_hash: str | None = None
    new_tree_hash: str | None = None
    version_id: str | None = None
    pointer_restore_failed = False
    try:
        if run_id_error is not None:
            raise run_id_error
        with kb_write_lock(target):
            ensure_sidecar(sidecar)
            _cleanup_staging(sidecar)
            current = target / "current"
            if not current.is_symlink():
                raise ValidationError("rollback", current, "current pointer is missing")
            old_link_value = os.readlink(current)
            old_target = _current_target(target)
            if old_target is None or old_target.parent != sidecar / "versions":
                raise ValidationError("rollback", current, "current pointer escapes the versions directory")
            old_tree_hash = kb_tree_hash(old_target)
            pointer_path = sidecar / "lkg" / "pointer.json"
            try:
                old_pointer_raw = pointer_path.read_text(encoding="utf-8")
                pointer_value = json.loads(old_pointer_raw)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise _RollbackPointerInvalid("LKG pointer is not valid JSON") from error
            if not isinstance(pointer_value, dict):
                raise _RollbackPointerInvalid("LKG pointer must be an object")
            desired_id = pointer_value.get("version_id")
            expected_hash = pointer_value.get("tree_hash")
            if not isinstance(desired_id, str) or desired_id != Path(desired_id).name or desired_id in {".", ".."}:
                raise _RollbackPointerInvalid("LKG pointer version_id is invalid")
            if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                raise _RollbackPointerInvalid("LKG pointer tree_hash is invalid")
            desired = sidecar / "lkg" / desired_id
            if not desired.is_dir() or kb_tree_hash(desired) != expected_hash:
                raise _RollbackPointerInvalid("LKG pointer target is missing or hash does not match")
            new_tree_hash = expected_hash
            if new_tree_hash == old_tree_hash:
                record = build_run_record(
                    run_id=run_id,
                    command="rollback",
                    batch_attempt_id=str(pointer_value.get("batch_attempt_id")) if pointer_value.get("batch_attempt_id") is not None else None,
                    target_kb_tree_hash=old_tree_hash,
                    compile_metrics=compile_metrics,
                    publish_elapsed_ms=int((time.monotonic() - started) * 1000),
                    reason_code=None,
                    exit_code=0,
                )
                result = _result_from_record(
                    status="rolled_back",
                    record=record,
                    old_tree_hash=old_tree_hash,
                    new_tree_hash=new_tree_hash,
                    version_id=_version_id_from_target(old_target),
                    no_op=True,
                    verified=True,
                )
                _atomic_write_json(sidecar / "releases" / f"rollback-{run_id}.json", result)
                return result
            _check_injection("before_staging", cancel=cancel, fault=fault)
            staging = sidecar / "staging" / run_id
            staging_path = staging
            staging.mkdir(parents=True)
            try:
                _copy_tree(desired, staging, copy_file=copy_file)
                if kb_tree_hash(staging) != expected_hash:
                    raise ValidationError("rollback", staging, "staging tree hash mismatch")
                _check_injection("before_version_move", cancel=cancel, fault=fault)
                version_id = new_version_id(sidecar, now=now)
                version_path = sidecar / "versions" / version_id
                replace_file(staging, version_path)
                if kb_tree_hash(version_path) != expected_hash:
                    raise ValidationError("rollback", version_path, "version tree hash changed during move")
                lkg_id = _version_id_from_target(old_target)
                lkg_path = sidecar / "lkg" / lkg_id
                lkg_temp = sidecar / "lkg" / f".{lkg_id}.{run_id}.tmp"
                lkg_preexisting = lkg_path.exists() or lkg_path.is_symlink()
                if lkg_preexisting:
                    raise ValidationError("rollback", lkg_path, "LKG slot already exists")
                _copy_tree(old_target, lkg_temp, copy_file=copy_file)
                if kb_tree_hash(lkg_temp) != old_tree_hash:
                    raise ValidationError("rollback", lkg_temp, "LKG tree hash changed during copy")
                _check_injection("before_switch", cancel=cancel, fault=fault)
                _replace_current(target, version_id, run_id, replace_file)
                switched = True
                _check_injection("after_switch", cancel=cancel, fault=fault)
                current_target = _current_target(target)
                if current_target is None or kb_tree_hash(current_target) != expected_hash:
                    raise ValidationError("rollback", current, "readback tree hash mismatch")
                replace_file(lkg_temp, lkg_path)
                next_pointer = {
                    "version_id": lkg_id,
                    "tree_hash": old_tree_hash,
                    "batch_attempt_id": _source_batch_attempt(sidecar, old_target),
                    "written_at": (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
                _atomic_write_json(sidecar / "lkg" / "pointer.json", next_pointer)
                pointer_written = True
                record = build_run_record(
                    run_id=run_id,
                    command="rollback",
                    batch_attempt_id=str(pointer_value.get("batch_attempt_id")) if pointer_value.get("batch_attempt_id") is not None else None,
                    target_kb_tree_hash=expected_hash,
                    compile_metrics=compile_metrics,
                    publish_elapsed_ms=int((time.monotonic() - started) * 1000),
                    reason_code=None,
                    exit_code=0,
                )
                result = _result_from_record(
                    status="rolled_back",
                    record=record,
                    old_tree_hash=old_tree_hash,
                    new_tree_hash=expected_hash,
                    version_id=version_id,
                    no_op=False,
                    verified=True,
                )
                _atomic_write_json(sidecar / "releases" / f"{version_id}.json", result)
                _prune_lkg(sidecar, lkg_path.name)
                return result
            except BaseException:
                shutil.rmtree(staging, ignore_errors=True)
                raise
    except Exception as error:
        if staging_path is not None and staging_path.exists():
            _remove_path(staging_path)
        if switched:
            preserve_version_path, recovery_warning, recovery_verified = _restore_current_after_failure(
                target,
                old_link_value=old_link_value,
                fallback_version_id=version_id,
                fallback_tree_hash=new_tree_hash,
                run_id=run_id,
            )
        if pointer_written and old_pointer_raw is not None and not preserve_version_path:
            try:
                _atomic_write_text(sidecar / "lkg" / "pointer.json", old_pointer_raw)
            except OSError:
                pointer_restore_failed = True
        if not preserve_version_path and version_path is not None and version_path.exists():
            shutil.rmtree(version_path, ignore_errors=True)
        if lkg_temp is not None and (lkg_temp.exists() or lkg_temp.is_symlink()):
            _remove_path(lkg_temp)
        if lkg_path is not None and not preserve_version_path and not pointer_restore_failed and not lkg_preexisting and (lkg_path.exists() or lkg_path.is_symlink()):
            _remove_path(lkg_path)
        target_hash = old_tree_hash
        try:
            current_target = _current_target(target)
            if current_target is not None:
                target_hash = kb_tree_hash(current_target)
        except (OSError, ValueError):
            target_hash = old_tree_hash
        reason_code = getattr(error, "reason_code", None)
        if reason_code is None:
            reason_code = error.reason if isinstance(error, ValidationError) else "rollback_failed"
        if recovery_warning is not None and not recovery_verified:
            reason_code = "restore_uncertain"
        status = "blocked" if isinstance(error, (ValidationError, _RollbackPointerInvalid)) else "failed"
        exit_code = 2 if status == "blocked" else 1
        record = build_run_record(
            run_id=run_id,
            command="rollback",
            batch_attempt_id=str(pointer_value.get("batch_attempt_id")) if pointer_value and pointer_value.get("batch_attempt_id") is not None else None,
            target_kb_tree_hash=target_hash,
            compile_metrics=compile_metrics,
            publish_elapsed_ms=int((time.monotonic() - started) * 1000),
            reason_code=str(reason_code),
            exit_code=exit_code,
        )
        if recovery_warning is not None:
            record["recovery_warning"] = recovery_warning
            record["recovery_verified"] = recovery_verified
        receipt = {**record, "receipt": True, "error": str(error)}
        receipt_path = sidecar / "receipts" / f"{run_id}.json"
        try:
            ensure_sidecar(sidecar)
            _atomic_write_json(receipt_path, receipt)
        except (OSError, TypeError, ValueError) as sink_error:
            receipt = {
                **receipt,
                "reason_code": "receipt_sink_unavailable",
                "receipt_sink_error": str(sink_error),
                "original_reason_code": str(reason_code),
            }
            receipt_path = None
        return _result_from_record(
            status=status,
            record=receipt,
            old_tree_hash=old_tree_hash,
            new_tree_hash=new_tree_hash,
            version_id=version_id,
            no_op=False,
            verified=False,
            receipt_path=receipt_path,
        )


def main(argv: Sequence[str] | None = None) -> int:
    command = _command_from_program(sys.argv[0])
    args = _parser(command).parse_args(list(argv) if argv is not None else None)
    result = publish(args.batch_dir, args.kb_dir) if command == "publish" else rollback(args.kb_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return int(result.get("exit_code", 0))


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SIDECAR_DIRECTORIES",
    "ensure_sidecar",
    "build_run_record",
    "construct_staging",
    "ensure_target_kb",
    "kb_tree_hash",
    "kb_write_lock",
    "load_batch_manifest",
    "main",
    "new_version_id",
    "publish",
    "rollback",
    "sidecar_path",
]
