"""Durable source, claim, and archive lineage helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError
from .faithfulness import claim_entity_key
from .jsonl import append_jsonl, read_jsonl, write_jsonl


_DISALLOWED_SOURCE_STATUSES = {"empty", "empty_shell", "failed", "shell", "invalid", "inconsistent", "no_body"}
ARCHIVE_RETENTION_DAYS = 90
_VALID_PAGE_STATUSES = {"published", "degraded"}
_VALID_DELIVERY_STATUSES = {"released", "not_released"}
_VALID_SOURCE_STATUSES = {"passed", "verified", "ok", "failed", "pending", "degraded"}


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


def _content_path(value: object) -> str:
    return str(value or "").replace("\\", "/").removeprefix("items/")


def _planned_targets(planned_writes: Iterable[dict[str, Any]]) -> set[str]:
    targets: set[str] = set()
    for record in planned_writes:
        direct = record.get("target_path")
        if direct:
            targets.add(str(direct))
        for page in record.get("split_pages", []) if isinstance(record.get("split_pages"), list) else []:
            if isinstance(page, dict) and page.get("target_path"):
                targets.add(str(page["target_path"]))
        for target in record.get("target_paths", []) if isinstance(record.get("target_paths"), list) else []:
            if target:
                targets.add(str(target))
    return targets


def _is_reader_target(target: str) -> bool:
    path = Path(target)
    return (
        target in {"README.md", "Home.md"}
        or (len(path.parts) == 2 and path.parts[0] == "indexes")
        or (len(path.parts) >= 2 and path.parts[0] == "pages")
    )


def validate_prewrite_provenance(
    source_manifest: dict[str, Any],
    snapshots: list[dict[str, Any]],
    source_audit_ledger: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    planned_writes: list[dict[str, Any]],
) -> None:
    """Fail closed before any durable source, queue, archive, or page write."""
    if not isinstance(source_manifest, dict) or source_manifest.get("schema_version") != "input-manifest.v1":
        raise ValidationError("prewrite", "source-manifest", "input manifest is missing or unsupported")
    manifest_sources = source_manifest.get("sources")
    if not isinstance(manifest_sources, list):
        raise ValidationError("prewrite", "source-manifest.sources", "must contain the frozen source set")
    by_path: dict[str, dict[str, Any]] = {}
    for source in manifest_sources:
        if not isinstance(source, dict):
            raise ValidationError("prewrite", "source-manifest.sources", "source row must be an object")
        path = _content_path(source.get("content_path"))
        if not path or path in by_path:
            raise ValidationError("prewrite", path or "source", "source path is missing or duplicated")
        if not source.get("source_id") or not source.get("content_fingerprint"):
            raise ValidationError("prewrite", path, "source identity and fingerprint are required")
        by_path[path] = source

    snapshot_by_path: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        path = _content_path(snapshot.get("content_path") or snapshot.get("input_path"))
        if path:
            if path in snapshot_by_path:
                raise ValidationError("prewrite", path, "source snapshot is duplicated in the current run")
            snapshot_by_path[path] = snapshot
    if set(snapshot_by_path) != set(by_path):
        raise ValidationError("prewrite", "source-snapshots", "snapshot source set differs from input manifest")
    for path, source in by_path.items():
        snapshot = snapshot_by_path[path]
        if snapshot.get("source_uri") != source.get("source_uri"):
            raise ValidationError("prewrite", path, "snapshot source URI differs from input manifest")
        if snapshot.get("content_fingerprint") != source.get("content_fingerprint"):
            raise ValidationError("prewrite", path, "snapshot fingerprint differs from input manifest")
        if not snapshot.get("validated_at"):
            raise ValidationError("prewrite", path, "snapshot validated_at is required")
        source_status = str(snapshot.get("validation_status", "")).lower()
        if source_status not in _VALID_SOURCE_STATUSES:
            raise ValidationError("prewrite", path, f"unsupported source status: {source_status}")

    ledger_by_path: dict[str, dict[str, Any]] = {}
    for row in source_audit_ledger:
        path = _content_path(row.get("content_path"))
        if not path or path in ledger_by_path:
            raise ValidationError("prewrite", path or "source-audit-ledger", "source ledger row is missing or duplicated")
        ledger_by_path[path] = row
    if set(ledger_by_path) != set(by_path):
        raise ValidationError("prewrite", "source-audit-ledger", "ledger source set differs from input manifest")
    for path, source in by_path.items():
        row = ledger_by_path[path]
        if row.get("source_uri") != source.get("source_uri"):
            raise ValidationError("prewrite", path, "ledger source URI differs from input manifest")
        if row.get("source_id") != source.get("source_id") or row.get("content_fingerprint") != source.get("content_fingerprint"):
            raise ValidationError("prewrite", path, "ledger identity differs from input manifest")

    targets = _planned_targets(planned_writes)
    if not targets and claims:
        raise ValidationError("prewrite", "planned_writes", "formal write plan is empty")
    for target in targets:
        path = Path(target)
        if path.is_absolute() or ".." in path.parts or not target.endswith(".md"):
            raise ValidationError("prewrite", target, "planned target is not a safe Markdown path")
        if not _is_reader_target(target):
            raise ValidationError("prewrite", target, "audit or provider material cannot enter Reader Package")

    for record in [*planned_writes, *claims]:
        page_status = record.get("page_status")
        if page_status is not None and page_status not in _VALID_PAGE_STATUSES:
            raise ValidationError("prewrite", "page_status", f"unsupported page status: {page_status}")
        if page_status == "degraded":
            for target in _planned_targets([record]):
                if _is_reader_target(target):
                    raise ValidationError("prewrite", target, "degraded page cannot enter Reader Package")
        delivery_status = record.get("delivery_status")
        if delivery_status is not None and delivery_status not in _VALID_DELIVERY_STATUSES:
            raise ValidationError("prewrite", "delivery_status", f"unsupported delivery status: {delivery_status}")
        if delivery_status == "released":
            raise ValidationError("prewrite", "delivery_status", "Task0 cannot release a delivery package")

    for claim in claims:
        source_uri = str(claim.get("source_uri") or "")
        content_fingerprint = claim.get("content_fingerprint")
        matching = [
            (path, source)
            for path, source in by_path.items()
            if source.get("source_uri") == source_uri
        ]
        if not matching:
            raise ValidationError("prewrite", source_uri or "claim", "claim source is absent from input manifest")
        if not claim.get("text") or not claim.get("claim_fingerprint") or not claim.get("fragment_locator"):
            raise ValidationError("prewrite", source_uri, "claim provenance is incomplete")
        path, source = matching[0]
        snapshot = snapshot_by_path[path]
        if content_fingerprint != source.get("content_fingerprint"):
            raise ValidationError("prewrite", source_uri, "claim fingerprint does not match source snapshot")
        target = str(claim.get("target_path") or claim.get("page_path") or "")
        if target and target not in targets:
            raise ValidationError("prewrite", target, "claim target is absent from the write plan")


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


def audit_provenance(
    drafts: list[dict[str, Any]],
    writes: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    *,
    source_snapshots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Emit one complete source record for every claim on a formal page."""
    statuses = _source_statuses(raw_items, run_dir)
    for snapshot in source_snapshots or []:
        source_uri = snapshot.get("source_uri")
        if source_uri:
            statuses[str(source_uri)] = dict(snapshot)
    successful = {
        str(write["target_path"]): write
        for write in writes
        if write["status"] == "success"
    }
    records: list[dict[str, Any]] = []
    seen_claims: set[tuple[str, tuple[str, str, str]]] = set()
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
                target_path = str(
                    claim.get("target_path")
                    or page.get("target_path")
                    or (draft.get("target_paths") or [""])[0]
                )
                write = successful.get(target_path)
                if write is None:
                    raise ValidationError("s6", draft.get("draft_id", "draft"), "claim has no successful output page")
                claim_key = (target_path, claim_entity_key(claim))
                if claim_key in seen_claims:
                    continue
                seen_claims.add(claim_key)
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
                        "target_path": target_path,
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
