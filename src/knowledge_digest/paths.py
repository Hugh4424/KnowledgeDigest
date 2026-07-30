"""Filesystem validation and permitted audit-output path construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import ValidationError


STRUCTURE_FILENAME = "kb.structure.md"


@dataclass(frozen=True)
class DigestPaths:
    new_dir: Path
    items_dir: Path
    kb_dir: Path
    structure_path: Path
    initialize_new_kb: bool = False


def _require_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise ValidationError("paths", path, f"{label} is missing")
    if not path.is_dir():
        raise ValidationError("paths", path, f"{label} must be a directory")


def is_new_kb_container(kb_dir: Path) -> bool:
    return all(entry.name == ".digest.lock" for entry in kb_dir.iterdir())


def validate_paths(
    new_dir: Path,
    kb_dir: Path,
    *,
    allow_new_kb: bool = False,
) -> DigestPaths:
    """Validate inputs and, only when requested, prepare an empty KB container.

    Creating the directory is deliberately not publication: the caller must
    acquire the single-writer lock and revalidate emptiness before it creates
    any owned Markdown file.
    """
    _require_directory(new_dir, "new_dir")
    items_dir = new_dir / "items"
    _require_directory(items_dir, "new_dir/items")
    if kb_dir.is_symlink():
        raise ValidationError("paths", kb_dir, "kb_dir must not be a symlink")
    if not kb_dir.exists():
        if not allow_new_kb:
            raise ValidationError("paths", kb_dir, "kb_dir is missing")
        try:
            kb_dir.mkdir(parents=True, exist_ok=False)
        except OSError as error:
            raise ValidationError("paths", kb_dir, f"cannot prepare new kb_dir ({error})") from error
    _require_directory(kb_dir, "kb_dir")
    structure_path = kb_dir / STRUCTURE_FILENAME
    if structure_path.is_symlink():
        raise ValidationError("paths", structure_path, "kb.structure.md must not be a symlink")
    if not structure_path.exists():
        if not allow_new_kb or not is_new_kb_container(kb_dir):
            raise ValidationError("paths", structure_path, "kb.structure.md is missing")
        return DigestPaths(new_dir, items_dir, kb_dir, structure_path, initialize_new_kb=True)
    if not structure_path.is_file():
        raise ValidationError("paths", structure_path, "kb.structure.md must be a regular file")
    return DigestPaths(new_dir, items_dir, kb_dir, structure_path)
