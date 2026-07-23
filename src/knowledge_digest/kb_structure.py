"""Dependency-free parser and write gate for ``kb.structure.md``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_ROOTS = ("pages", "_archive", "_queues")


@dataclass(frozen=True)
class StructureContract:
    """The small structure contract needed before a formal write."""

    roots: tuple[str, ...]
    why_field: str | None
    version_field: str | None
    missing_fields: tuple[str, ...]
    suggestions: tuple[str, ...]
    allow_official_write: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "roots": list(self.roots),
            "why_field": self.why_field,
            "version_field": self.version_field,
            "missing_fields": list(self.missing_fields),
            "suggestions": list(self.suggestions),
            "allow_official_write": self.allow_official_write,
        }


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def _frontmatter_lines(text: str) -> list[str] | None:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            return lines[1:index]
    return None


def _frontmatter_values(text: str) -> dict[str, str]:
    lines = _frontmatter_lines(text)
    if lines is None:
        return {}
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        values[key.strip()] = _unquote(value)
    return values


def parse_roots(structure_path: Path) -> tuple[str, ...]:
    """Read roots from YAML-like frontmatter, with safe layout defaults."""
    frontmatter = _frontmatter_lines(structure_path.read_text(encoding="utf-8"))
    if frontmatter is None:
        return DEFAULT_ROOTS

    roots: list[str] = []
    named_roots: dict[str, str] = {}
    for index, line in enumerate(frontmatter):
        stripped = line.strip()
        for key in ("page_root", "archive_root", "queue_root"):
            if stripped.startswith(f"{key}:"):
                candidate = _unquote(stripped.partition(":")[2])
                if candidate:
                    named_roots[key] = candidate
        if not stripped.startswith("roots:"):
            continue
        inline = stripped.partition(":")[2].strip()
        if inline.startswith("[") and inline.endswith("]"):
            roots = [_unquote(item) for item in inline[1:-1].split(",") if _unquote(item)]
            break
        if inline:
            candidate = _unquote(inline)
            roots = [candidate] if candidate else []
            break
        for child in frontmatter[index + 1 :]:
            if child and not child[0].isspace():
                break
            item = child.strip()
            if item.startswith("- "):
                candidate = _unquote(item[2:])
                if candidate:
                    roots.append(candidate)
            elif item:
                break
        break
    if roots:
        return tuple(roots)
    if named_roots:
        return (
            named_roots.get("page_root", DEFAULT_ROOTS[0]),
            named_roots.get("archive_root", DEFAULT_ROOTS[1]),
            named_roots.get("queue_root", DEFAULT_ROOTS[2]),
        )
    return DEFAULT_ROOTS


def inspect_structure(structure_path: Path) -> StructureContract:
    """Read the roots and required Why/version declarations used by the write gate."""
    text = structure_path.read_text(encoding="utf-8")
    values = _frontmatter_values(text)
    why_field = values.get("why_field") or None
    version_field = values.get("version_field") or None
    missing: list[str] = []
    suggestions: list[str] = []
    if not why_field:
        missing.append("Why")
        suggestions.append("在 kb.structure.md frontmatter 增加非空 why_field，例如 why_field: why")
    if not version_field:
        missing.append("version history")
        suggestions.append(
            "在 kb.structure.md frontmatter 增加非空 version_field，例如 version_field: version"
        )
    roots = parse_roots(structure_path)
    return StructureContract(
        roots=roots,
        why_field=why_field,
        version_field=version_field,
        missing_fields=tuple(missing),
        suggestions=tuple(suggestions),
        allow_official_write=not missing,
    )


def validate_structure(structure_path: Path) -> dict[str, Any]:
    """Return a JSON-ready structure check without raising on missing fields."""
    return inspect_structure(structure_path).as_dict()


# Clear aliases for callers that prefer the noun form.
parse_structure_contract = inspect_structure
structure_contract = inspect_structure
