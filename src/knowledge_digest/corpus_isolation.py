"""Create and remove a content-isolated Markdown corpus copy."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from .errors import ValidationError


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _absolute_directory(path: Path, label: str, *, must_exist: bool = True) -> Path:
    if not path.is_absolute():
        raise ValidationError("corpus", label, "path must be absolute")
    resolved = path.resolve(strict=must_exist)
    if must_exist and not resolved.is_dir():
        raise ValidationError("corpus", resolved, "must be a directory")
    return resolved


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def tree_manifest(root: Path, *, markdown_only: bool = False) -> dict[str, Any]:
    """Return a stable, content-free manifest for regular files below ``root``."""
    root = _absolute_directory(root, "manifest_root")
    files: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            raise ValidationError("corpus", path, "symbolic links are not allowed")
        if not path.is_file():
            continue
        if markdown_only and path.suffix.lower() != ".md":
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
        )
    manifest_hash = hashlib.sha256(_canonical_bytes(files)).hexdigest()
    return {"files": files, "file_count": len(files), "manifest_hash": manifest_hash}


def prepare_disposable_corpus(
    source_root: Path,
    formal_kb_root: Path,
    disposable_root: Path,
) -> dict[str, Any]:
    """Copy only Markdown files while proving both authoritative trees stayed unchanged."""
    source = _absolute_directory(source_root, "source_root")
    formal_kb = _absolute_directory(formal_kb_root, "formal_kb_root")
    disposable = _absolute_directory(disposable_root, "disposable_root", must_exist=False)
    for authoritative in (source, formal_kb):
        if _is_within(disposable, authoritative) or _is_within(authoritative, disposable):
            raise ValidationError(
                "corpus", disposable, "disposable root must not overlap authoritative roots"
            )
    if disposable.exists():
        raise ValidationError("corpus", disposable, "disposable root already exists")

    source_before = tree_manifest(source)
    source_markdown_before = tree_manifest(source, markdown_only=True)
    kb_before = tree_manifest(formal_kb)
    try:
        disposable.mkdir(parents=True, exist_ok=False)
        for row in source_markdown_before["files"]:
            relative = Path(str(row["path"]))
            target = disposable / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target, follow_symlinks=False)
        copy_manifest = tree_manifest(disposable, markdown_only=True)
        source_after = tree_manifest(source)
        kb_after = tree_manifest(formal_kb)
        if source_after != source_before:
            raise ValidationError("corpus", source, "source changed while it was copied")
        if kb_after != kb_before:
            raise ValidationError("corpus", formal_kb, "formal KB changed while corpus was copied")
        if copy_manifest != source_markdown_before:
            raise ValidationError("corpus", disposable, "copy manifest does not match source")
    except BaseException:
        if disposable.exists():
            shutil.rmtree(disposable)
        raise

    return {
        "schema_version": "corpus-isolation.v1",
        "source_root": str(source),
        "formal_kb_root": str(formal_kb),
        "disposable_root": str(disposable),
        "source_before": source_before,
        "source_after": source_after,
        "formal_kb_before": kb_before,
        "formal_kb_after": kb_after,
        "source_markdown_manifest": source_markdown_before,
        "copy_manifest": copy_manifest,
        "corpus_hash": copy_manifest["manifest_hash"],
        "markdown_count": copy_manifest["file_count"],
        "excluded_non_markdown_count": source_before["file_count"]
        - source_markdown_before["file_count"],
        "cleanup": {"owner": "knowledge-digest-calibrate", "required": True},
    }


def cleanup_disposable_corpus(
    disposable_root: Path, preparation: dict[str, Any]
) -> dict[str, Any]:
    """Remove only the owned copy after revalidating its binding and read-only inputs."""
    disposable = _absolute_directory(disposable_root, "disposable_root")
    if preparation.get("schema_version") != "corpus-isolation.v1":
        raise ValidationError("corpus", "preparation", "unsupported preparation schema")
    if preparation.get("disposable_root") != str(disposable):
        raise ValidationError("corpus", disposable, "cleanup root is not bound to preparation")
    if preparation.get("cleanup") != {
        "owner": "knowledge-digest-calibrate",
        "required": True,
    }:
        raise ValidationError("corpus", disposable, "copy is not owned by calibration")
    if tree_manifest(disposable) != preparation.get("copy_manifest"):
        raise ValidationError("corpus", disposable, "copy changed before cleanup")
    source = Path(str(preparation["source_root"]))
    formal_kb = Path(str(preparation["formal_kb_root"]))
    if tree_manifest(source) != preparation.get("source_before"):
        raise ValidationError("corpus", source, "source changed before cleanup")
    if tree_manifest(formal_kb) != preparation.get("formal_kb_before"):
        raise ValidationError("corpus", formal_kb, "formal KB changed before cleanup")
    shutil.rmtree(disposable)
    return {
        "schema_version": "corpus-cleanup.v1",
        "disposable_root": str(disposable),
        "corpus_hash": preparation["corpus_hash"],
        "cleanup_complete": not disposable.exists(),
        "source_unchanged": tree_manifest(source) == preparation["source_before"],
        "formal_kb_unchanged": tree_manifest(formal_kb) == preparation["formal_kb_before"],
    }
