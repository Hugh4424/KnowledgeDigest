"""Stage 6: final claim-to-source audit records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .jsonl import write_jsonl


_DISALLOWED_SOURCE_STATUSES = {"empty", "empty_shell", "failed", "shell"}


def audit_provenance(
    drafts: list[dict[str, Any]],
    writes: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
) -> list[dict[str, Any]]:
    """Emit one valid source record for every claim that reached a formal page."""
    statuses = {
        item["source_uri"]: str(item.get("source_status", "ok")).lower()
        for item in raw_items
        if item.get("source_uri")
    }
    targets = {write["draft_id"]: write["target_path"] for write in writes if write["status"] == "success"}
    records: list[dict[str, Any]] = []
    for draft in drafts:
        target_path = targets.get(draft["draft_id"])
        if target_path is None:
            continue
        for index, claim in enumerate(draft["claims"], start=1):
            source_uri = claim.get("source_uri")
            source_status = statuses.get(source_uri, "unknown")
            if not source_uri or source_status in _DISALLOWED_SOURCE_STATUSES:
                raise ValidationError(
                    "s6",
                    draft["draft_id"],
                    "final claims require a non-empty, non-shell source_uri",
                )
            records.append(
                {
                    "claim_id": f"{draft['draft_id']}-claim-{index}",
                    "claim_body": claim["text"],
                    "source_uri": source_uri,
                    "source_status": source_status,
                    "target_path": target_path,
                }
            )
    write_jsonl(run_dir / "s6" / "provenance-audit.jsonl", records)
    return records
