"""Stage 1: capture and validate local source snapshots."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .jsonl import append_jsonl, read_jsonl, write_jsonl
from .paths import DigestPaths
from .provenance import retention_deadline


INGESTIBLE_SUFFIXES = {".md", ".txt", ".json"}
_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)
_FAILED_STATUSES = {"failed", "empty", "empty_shell", "shell", "invalid", "inconsistent", "no_body"}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _source_index(new_dir: Path) -> dict[str, dict[str, Any]]:
    """Build a lookup from multiple path forms to the source record."""
    sources_path = new_dir / "sources.jsonl"
    result: dict[str, dict[str, Any]] = {}
    for source in read_jsonl(sources_path):
        content_path = source.get("content_path")
        if not isinstance(content_path, str) or not content_path:
            continue
        normalized = content_path.replace("\\", "/")
        keys = {normalized, Path(normalized).name}
        if normalized.startswith("items/"):
            keys.add(normalized[len("items/") :])
        for key in keys:
            result[key] = source
    return result


def _source_for(
    path: Path,
    items_dir: Path,
    source_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    relative = path.relative_to(items_dir).as_posix()
    source = source_index.get(relative, source_index.get(path.name, {}))
    source_uri = source.get("source_uri") if isinstance(source.get("source_uri"), str) else ""
    captured_at = source.get("captured_at") or source.get("fetched_at") or _now()
    return {
        "source_uri": source_uri,
        "source_meta": {
            key: value
            for key, value in source.items()
            if key not in {"content_path", "source_uri", "fetched_at", "captured_at", "source_status"}
        },
        "fetched_at": source.get("fetched_at"),
        "captured_at": captured_at,
        "source_status": source.get("source_status", "ok"),
        "declared_content_fingerprint": (
            source.get("content_fingerprint")
            or source.get("content_hash")
            or source.get("snapshot_fingerprint")
        ),
        "input_path": str(path),
    }


def _is_empty_shell(text: str, source_status: object) -> bool:
    if isinstance(source_status, str) and source_status.lower() in _FAILED_STATUSES:
        return True
    normalized = " ".join(text.lower().split())
    if not normalized:
        return True
    shell_words = {"home", "navigation", "login", "menu", "skip", "content", "search", "footer"}
    tokens = set(_TOKEN_RE.findall(normalized))
    return bool(tokens) and tokens <= shell_words


def _non_text_refs(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)>]+", text)


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snapshot_id(source: dict[str, Any], text: str) -> str:
    """Build an identifier stable across runs for one local source snapshot."""
    payload = "\n".join(
        (
            str(source.get("source_uri", "")),
            str(source.get("input_path", "")),
            _fingerprint(text),
        )
    )
    return f"snapshot-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def _snapshot(
    source: dict[str, Any],
    text: str,
    *,
    status: str,
    reason: str,
    validated_at: str,
) -> dict[str, Any]:
    fingerprint = _fingerprint(text)
    return {
        "snapshot_id": _snapshot_id(source, text),
        "source_uri": source["source_uri"],
        "captured_at": source["captured_at"],
        "validated_at": validated_at,
        "retain_content_until": retention_deadline(validated_at),
        "content_fingerprint": fingerprint,
        "validation_status": status,
        "validation_reason": reason,
        "input_path": source["input_path"],
        # Keep both names: content is the stable snapshot contract and
        # full_content makes the retention boundary explicit to readers.
        "content": text,
        "full_content": text,
        "source_status": source.get("source_status", "ok"),
        "source_meta": source.get("source_meta", {}),
    }


def ingest(
    paths: DigestPaths,
    run_dir: Path,
    *,
    persist_snapshot: bool = True,
) -> list[dict[str, Any]]:
    """Read local notes and retain a snapshot for every source, including failures.
    """
    source_index = _source_index(paths.new_dir)
    raw_items: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for path in sorted(paths.items_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in INGESTIBLE_SUFFIXES:
            continue
        source = _source_for(
            path,
            paths.items_dir,
            source_index,
        )
        validated_at = _now()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            reason = f"unreadable: {error}"
            snapshot = _snapshot(source, "", status="failed", reason=reason, validated_at=validated_at)
            snapshots.append(snapshot)
            failures.append(
                {
                    "path": str(path),
                    "source_uri": source["source_uri"],
                    "reason": reason,
                    "retry_status": "retry_next_manual_run",
                    "snapshot_id": snapshot["snapshot_id"],
                }
            )
            continue

        content_fingerprint = _fingerprint(text)
        declared = source.get("declared_content_fingerprint")
        if declared and declared != content_fingerprint:
            reason = "content fingerprint is inconsistent with the supplied local snapshot"
            status = "failed"
        elif _is_empty_shell(text, source["source_status"]):
            reason = "empty shell content" if text.strip() else "source has no body"
            status = "failed"
        elif not source["source_uri"].strip():
            reason = "source_uri is missing"
            status = "failed"
        else:
            reason = "local snapshot validated"
            status = "passed"

        snapshot = _snapshot(source, text, status=status, reason=reason, validated_at=validated_at)
        snapshots.append(snapshot)
        if status != "passed":
            failures.append(
                {
                    "path": str(path),
                    "source_uri": source["source_uri"],
                    "reason": reason,
                    "retry_status": "retry_next_manual_run",
                    "snapshot_id": snapshot["snapshot_id"],
                }
            )
            continue

        if content_fingerprint in seen:
            duplicates.append(
                {
                    "path": str(path),
                    "content_hash": content_fingerprint,
                    "duplicate_of": seen[content_fingerprint],
                    "source_uri": source["source_uri"],
                    "snapshot_id": snapshot["snapshot_id"],
                }
            )
            continue

        raw_id = f"raw-{len(raw_items) + 1}"
        seen[content_fingerprint] = raw_id
        raw_items.append(
            {
                "raw_id": raw_id,
                "content_hash": content_fingerprint,
                "content_fingerprint": content_fingerprint,
                "text": text,
                "source_uri": source["source_uri"],
                "source_meta": source["source_meta"],
                "fetched_at": source["fetched_at"],
                "captured_at": source["captured_at"],
                "validated_at": validated_at,
                "validation_status": "passed",
                "validation_reason": reason,
                "source_status": source["source_status"],
                "source_snapshot_ref": f"s1/source-snapshots.jsonl#{snapshot['snapshot_id']}",
                "snapshot_id": snapshot["snapshot_id"],
                "input_path": str(path),
                "non_text_refs": _non_text_refs(text),
            }
        )

    s1 = run_dir / "s1"
    write_jsonl(s1 / "raw-items.jsonl", raw_items)
    write_jsonl(s1 / "duplicates.jsonl", duplicates)
    write_jsonl(s1 / "ingest-failed.jsonl", failures)
    write_jsonl(s1 / "source-snapshots.jsonl", snapshots)
    if persist_snapshot:
        append_jsonl(paths.kb_dir / "_digest" / "source-snapshots.jsonl", snapshots)
    return raw_items
