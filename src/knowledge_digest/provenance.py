"""Durable source, claim, and archive lineage helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError
from .jsonl import read_jsonl, write_jsonl


_DISALLOWED_SOURCE_STATUSES = {"empty", "empty_shell", "failed", "shell", "invalid", "inconsistent", "no_body"}
ARCHIVE_RETENTION_DAYS = 90


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def retention_deadline(started_at: str | None = None) -> str:
    if started_at:
        value = started_at.replace("Z", "+00:00")
        try:
            start = datetime.fromisoformat(value)
        except ValueError:
            start = datetime.now(UTC)
    else:
        start = datetime.now(UTC)
    return (start + timedelta(days=ARCHIVE_RETENTION_DAYS)).isoformat().replace("+00:00", "Z")


def append_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    values = list(records)
    if values:
        write_jsonl(path, [*read_jsonl(path), *values])


def _source_statuses(raw_items: list[dict[str, Any]], run_dir: Path) -> dict[str, dict[str, Any]]:
    snapshots = {row.get("source_uri"): row for row in read_jsonl(run_dir / "s1" / "source-snapshots.jsonl")}
    for item in raw_items:
        snapshots.setdefault(
            item.get("source_uri"),
            {
                "source_uri": item.get("source_uri"),
                "content_fingerprint": item.get("content_fingerprint"),
                "validation_status": item.get("validation_status", "passed"),
                "validated_at": item.get("validated_at"),
            },
        )
    return {str(key): value for key, value in snapshots.items() if key}


def source_index_records(raw_items: list[dict[str, Any]], run_dir: Path) -> list[dict[str, Any]]:
    """Return only validated source snapshots suitable for a formal index."""
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_uri, snapshot in _source_statuses(raw_items, run_dir).items():
        if str(snapshot.get("validation_status", "")).lower() not in {"passed", "verified", "ok"}:
            continue
        if source_uri in seen:
            continue
        seen.add(source_uri)
        result.append(
            {
                "source_uri": source_uri,
                "captured_at": snapshot.get("captured_at"),
                "validated_at": snapshot.get("validated_at"),
                "content_fingerprint": snapshot.get("content_fingerprint"),
                "validation_status": snapshot.get("validation_status"),
                "validation_reason": snapshot.get("validation_reason"),
                "input_path": snapshot.get("input_path"),
                "source_snapshot_ref": snapshot.get("snapshot_id"),
            }
        )
    return result


def audit_provenance(
    drafts: list[dict[str, Any]],
    writes: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
) -> list[dict[str, Any]]:
    """Emit one complete source record for every claim on a formal page."""
    statuses = _source_statuses(raw_items, run_dir)
    successful = {(write["draft_id"], write.get("page_index", 1)): write for write in writes if write["status"] == "success"}
    records: list[dict[str, Any]] = []
    for draft in drafts:
        pages = draft.get("split_pages")
        if not isinstance(pages, list) or not pages:
            pages = [{"page_index": 1, "target_path": None, "claims": draft.get("claims", [])}]
        for page in pages:
            if not isinstance(page, dict):
                continue
            page_index = int(page.get("page_index", 1))
            page_claims = page.get("claims")
            if not isinstance(page_claims, list):
                page_claims = []
            for claim in page_claims:
                if not isinstance(claim, dict):
                    continue
                # Split pages carry the authoritative page enrichment. Never
                # fall back to page 1: that would misattribute later claims.
                claim_page_index = claim.get("page_index")
                if claim_page_index is not None and int(claim_page_index) != page_index:
                    raise ValidationError("s6", draft.get("draft_id", "draft"), "claim page index does not match split page")
                source_uri = claim.get("source_uri")
                snapshot = statuses.get(str(source_uri), {})
                source_status = str(snapshot.get("validation_status", "unknown")).lower()
                if not source_uri or source_status in _DISALLOWED_SOURCE_STATUSES or source_status not in {"passed", "verified", "ok"}:
                    raise ValidationError("s6", draft.get("draft_id", "draft"), "final claims require a validated local source snapshot")
                write = successful.get((draft["draft_id"], page_index))
                if write is None:
                    raise ValidationError("s6", draft.get("draft_id", "draft"), "claim has no successful output page")
                records.append(
                    {
                        "claim_id": f"{draft['draft_id']}-claim-{len(records) + 1}",
                        "claim_body": claim["text"],
                        "claim_fingerprint": claim.get("claim_fingerprint"),
                        "source_uri": source_uri,
                        "source_status": source_status,
                        "content_fingerprint": claim.get("content_fingerprint") or snapshot.get("content_fingerprint"),
                        "fragment_locator": claim.get("fragment_locator"),
                        "verification_status": claim.get("verification_status", "verified"),
                        "source_snapshot_ref": claim.get("source_snapshot_ref") or snapshot.get("snapshot_id"),
                        "page_index": page_index,
                        "target_path": write["target_path"],
                        "supersedes": claim.get("supersedes"),
                        "superseded_by": claim.get("superseded_by"),
                    }
                )
    write_jsonl(run_dir / "s6" / "provenance-audit.jsonl", records)
    return records


def archive_claim_records(
    kb_dir: Path,
    claims: Iterable[dict[str, Any]],
    *,
    operation: str,
    reason: str,
    run_id: str | None = None,
    archive_root: str = "_archive",
) -> list[dict[str, Any]]:
    """Persist removed/replaced claim lineage without requiring a page write."""
    if not reason or not reason.strip():
        raise ValidationError("archive", operation, "archive reason must not be empty")
    timestamp = now_utc()
    records: list[dict[str, Any]] = []
    for claim in claims:
        original = claim.get("text") or claim.get("original_text") or claim.get("claim_body")
        if not original:
            continue
        record = {
            "operation": operation,
            "operation_at": timestamp,
            "reason": reason,
            "claim_fingerprint": claim.get("claim_fingerprint"),
            "claim_id": claim.get("claim_id"),
            "page_path": claim.get("target_path") or claim.get("page_path"),
            "source_uri": claim.get("source_uri"),
            "source_snapshot_ref": claim.get("source_snapshot_ref"),
            "source_snapshot": claim.get("source_snapshot") or {
                "source_uri": claim.get("source_uri"),
                "content_fingerprint": claim.get("content_fingerprint"),
                "fragment_locator": claim.get("fragment_locator"),
            },
            "content_fingerprint": claim.get("content_fingerprint"),
            "fragment_locator": claim.get("fragment_locator"),
            "verification_status": claim.get("verification_status", "removed"),
            "original_text": original,
            "full_content": original,
            "snapshot_content": claim.get("snapshot_content") or original,
            "retain_content_until": retention_deadline(timestamp),
            "lineage": {
                "supersedes": claim.get("supersedes"),
                "superseded_by": claim.get("superseded_by"),
                "run_id": run_id,
            },
        }
        records.append(record)
    append_jsonl(kb_dir / archive_root / "records.jsonl", records)
    return records


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def cleanup_expired_archives(
    kb_dir: Path,
    archive_root: str = "_archive",
    *,
    now: datetime | None = None,
    run_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Delete retained body/snapshot fields and files while preserving lineage."""
    current = now or datetime.now(UTC)
    record_path = kb_dir / archive_root / "records.jsonl"
    records = read_jsonl(record_path)
    cleaned: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    for record in records:
        deadline = _parse_time(record.get("retain_content_until"))
        if deadline is None or deadline > current or record.get("content_retained") is False:
            cleaned.append(record)
            continue
        updated = dict(record)
        for key in ("full_content", "snapshot_content", "content"):
            updated.pop(key, None)
        archive_content_path = record.get("archive_content_path")
        if isinstance(archive_content_path, str) and archive_content_path.strip():
            archive_path = (kb_dir / archive_content_path).resolve()
            archive_root_path = (kb_dir / archive_root).resolve()
            if archive_path.is_relative_to(archive_root_path) and archive_path.is_file():
                archive_path.unlink()
            updated.pop("archive_content_path", None)
        updated["content_retained"] = False
        updated["content_expired_at"] = current.isoformat().replace("+00:00", "Z")
        cleaned.append(updated)
        expired.append(
            {
                "operation": record.get("operation"),
                "claim_fingerprint": record.get("claim_fingerprint"),
                "page_path": record.get("page_path"),
                "content_retained": False,
                "metadata_retained": True,
            }
        )
    if records:
        write_jsonl(record_path, cleaned)

    snapshot_path = kb_dir / "_digest" / "source-snapshots.jsonl"
    snapshots = read_jsonl(snapshot_path)
    cleaned_snapshots: list[dict[str, Any]] = []
    for snapshot in snapshots:
        deadline = _parse_time(snapshot.get("retain_content_until"))
        if deadline is None or deadline > current:
            cleaned_snapshots.append(snapshot)
            continue
        updated_snapshot = dict(snapshot)
        for key in ("content", "full_content"):
            updated_snapshot.pop(key, None)
        updated_snapshot["content_retained"] = False
        updated_snapshot["content_expired_at"] = current.isoformat().replace("+00:00", "Z")
        cleaned_snapshots.append(updated_snapshot)
        expired.append(
            {
                "operation": "source_snapshot_cleanup",
                "source_uri": snapshot.get("source_uri"),
                "snapshot_id": snapshot.get("snapshot_id"),
                "content_retained": False,
                "metadata_retained": True,
            }
        )
    if snapshots:
        write_jsonl(snapshot_path, cleaned_snapshots)
    if run_dir is not None:
        write_jsonl(run_dir / "s5" / "archive-cleanup.jsonl", expired)
    return expired
