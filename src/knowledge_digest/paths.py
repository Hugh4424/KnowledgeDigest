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


def _require_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise ValidationError("paths", path, f"{label} is missing")
    if not path.is_dir():
        raise ValidationError("paths", path, f"{label} must be a directory")


def validate_paths(new_dir: Path, kb_dir: Path) -> DigestPaths:
    _require_directory(new_dir, "new_dir")
    items_dir = new_dir / "items"
    _require_directory(items_dir, "new_dir/items")
    _require_directory(kb_dir, "kb_dir")
    structure_path = kb_dir / STRUCTURE_FILENAME
    if not structure_path.exists():
        raise ValidationError("paths", structure_path, "kb.structure.md is missing")
    if not structure_path.is_file():
        raise ValidationError("paths", structure_path, "kb.structure.md must be a regular file")
    return DigestPaths(new_dir, items_dir, kb_dir, structure_path)
