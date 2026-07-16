"""Stage 4: draft evolution outputs from decisions and clusters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import DigestSettings
from .faithfulness import faithfulness_check, verify_claims
from .jsonl import write_jsonl


def draft(
    decisions: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    settings: DigestSettings,
) -> list[dict[str, Any]]:
    """Generate draft bodies, unsupported-claim records, and split suggestions."""
    by_id = {item["raw_id"]: item for item in raw_items}
    clusters_by_id = {cluster["cluster_id"]: cluster for cluster in clusters}
    drafts: list[dict[str, Any]] = []
    unsupported_records: list[dict[str, Any]] = []
    split_suggestions: list[dict[str, Any]] = []
    for decision in decisions:
        items = [by_id[raw_id] for raw_id in clusters_by_id[decision["cluster_id"]]["members"]]
        claims, unsupported = verify_claims(items)
        initial_body = "\n".join(claim["text"] for claim in claims)
        final_body, faithfulness_status = faithfulness_check(claims, initial_body)
        provenance = sorted({claim["source_uri"] for claim in claims})
        draft_record = {
            "draft_id": f"draft-{len(drafts) + 1}",
            "cluster_id": decision["cluster_id"],
            "action": decision["action"],
            "target_paths": decision["target_paths"],
            "final_body": final_body,
            "claims": claims,
            "removed_claims": unsupported,
            "provenance": provenance,
            "faithfulness_status": faithfulness_status,
            "split_suggestion": None,
        }
        for item in items:
            line_count = len(item["text"].splitlines())
            if line_count > settings.max_lines:
                suggestion = {"draft_id": draft_record["draft_id"], "raw_id": item["raw_id"], "line_count": line_count, "reason": "max_doc_lines exceeded"}
                split_suggestions.append(suggestion)
                draft_record["split_suggestion"] = suggestion
        drafts.append(draft_record)
        unsupported_records.extend({"draft_id": draft_record["draft_id"], **claim} for claim in unsupported)
    s4 = run_dir / "s4"
    write_jsonl(s4 / "drafts.jsonl", drafts)
    write_jsonl(s4 / "unsupported-claims.jsonl", unsupported_records)
    write_jsonl(s4 / "split-suggestions.jsonl", split_suggestions)
    return drafts
