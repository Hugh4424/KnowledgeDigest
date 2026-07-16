"""Stage 1: ingest new source notes into raw items."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .jsonl import read_jsonl, write_jsonl
from .paths import DigestPaths


INGESTIBLE_SUFFIXES = {".md", ".txt", ".json"}
_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def _source_index(new_dir: Path) -> dict[str, dict[str, Any]]:
    """Build a lookup from multiple path forms to the source record."""
    sources_path = new_dir / "sources.jsonl"
    result: dict[str, dict[str, Any]] = {}
    for source in read_jsonl(sources_path):
        content_path = source.get("content_path")
        if not isinstance(content_path, str) or not content_path:
            continue
        normalized = content_path.replace("\\", "/")
        keys = {normalized}
        if normalized.startswith("items/"):
            keys.add(normalized[len("items/"):])
        keys.add(Path(normalized).name)
        for key in keys:
            result[key] = source
    return result


def _source_for(path: Path, items_dir: Path, source_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    relative = path.relative_to(items_dir).as_posix()
    source = source_index.get(relative, source_index.get(path.name, {}))
    source_uri = source.get("source_uri") if isinstance(source.get("source_uri"), str) else path.resolve().as_uri()
    return {
        "source_uri": source_uri,
        "source_meta": {key: value for key, value in source.items() if key not in {"content_path", "source_uri", "fetched_at", "source_status"}},
        "fetched_at": source.get("fetched_at"),
        "source_status": source.get("source_status", "ok"),
    }


def _is_empty_shell(text: str, source_status: object) -> bool:
    if isinstance(source_status, str) and source_status.lower() in {"failed", "empty", "shell"}:
        return True
    normalized = " ".join(text.lower().split())
    if not normalized:
        return True
    shell_words = {"home", "navigation", "login", "menu", "skip", "content", "search", "footer"}
    tokens = set(_TOKEN_RE.findall(normalized))
    return bool(tokens) and tokens <= shell_words


def _non_text_refs(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)>]+", text)


def ingest(paths: DigestPaths, run_dir: Path) -> list[dict[str, Any]]:
    """Read ingestible files from ``items_dir`` and emit raw items."""
    source_index = _source_index(paths.new_dir)
    raw_items: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for path in sorted(paths.items_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in INGESTIBLE_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            failures.append({"path": str(path), "reason": f"unreadable: {error}"})
            continue
        source = _source_for(path, paths.items_dir, source_index)
        if _is_empty_shell(text, source["source_status"]):
            failures.append({"path": str(path), "reason": "empty shell content", "source_uri": source["source_uri"]})
            continue
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if content_hash in seen:
            duplicates.append({"path": str(path), "content_hash": content_hash, "duplicate_of": seen[content_hash]})
            continue
        raw_id = f"raw-{len(raw_items) + 1}"
        seen[content_hash] = raw_id
        raw_items.append(
            {
                "raw_id": raw_id,
                "content_hash": content_hash,
                "text": text,
                "source_uri": source["source_uri"],
                "source_meta": source["source_meta"],
                "fetched_at": source["fetched_at"],
                "non_text_refs": _non_text_refs(text),
                "source_status": source["source_status"],
            }
        )
    s1 = run_dir / "s1"
    write_jsonl(s1 / "raw-items.jsonl", raw_items)
    write_jsonl(s1 / "duplicates.jsonl", duplicates)
    write_jsonl(s1 / "ingest-failed.jsonl", failures)
    if any(failure["reason"].startswith("unreadable") for failure in failures):
        raise ValidationError("s1", paths.items_dir, "one or more input files could not be read")
    return raw_items
