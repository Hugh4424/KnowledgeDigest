"""Minimal, dependency-free parser for kb.structure.md frontmatter."""

from __future__ import annotations

from pathlib import Path


DEFAULT_ROOTS = ("pages", "_archive", "_queues")


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
