"""Phase-one audit pipeline with fail-closed formal-write boundaries."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from .cluster import cluster
from .config import DigestSettings, RISK_RULE_VERSION
from .draft import draft
from .errors import ValidationError
from .ingest import ingest
from .kb_structure import DEFAULT_ROOTS, StructureContract, inspect_structure
from .jsonl import append_jsonl, read_jsonl, replace_jsonl, write_jsonl
from .lock import kb_lock
from .paths import DigestPaths
from .provenance import (
    archive_claim_records,
    audit_provenance,
    source_index_records,
)
from .queues import write_queues
from .retrieve import retrieve
from .writeback import targets_for_draft, writeback


def _formal_changes(writes: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = ("target_path", "action", "status", "archive_path")
    return [{key: row[key] for key in keys} for row in writes]


def _write_plan(drafts: list[dict[str, object]], paths: DigestPaths, roots: tuple[str, ...]) -> dict[str, object]:
    changes = []
    for item in drafts:
        pages = item.get("split_pages") if isinstance(item.get("split_pages"), list) else []
        targets = (
            [page.get("target_path") for page in pages]
            if pages
            else [target.as_posix() for target in targets_for_draft(item, roots[0])]
        )
        for target_value in targets:
            target = Path(str(target_value))
            changes.append(
                {
                    "target_path": target.as_posix(),
                    "action": item["action"],
                    "archive_required": (paths.kb_dir / target).is_file(),
                }
            )
    return {"formal_kb_changes": changes}


def _digest_metrics(
    drafts: list[dict[str, object]],
    decisions: list[dict[str, object]],
    clusters: list[dict[str, object]],
    *,
    dry_run: bool,
) -> dict[str, object]:
    """Project replayable round, quality, and cost facts into report.json."""
    skipped = [
        {
            "cluster_id": cluster.get("cluster_id"),
            "cluster_tier": cluster.get("cluster_tier", cluster.get("tier")),
            "reason": cluster.get("decision_reason"),
        }
        for cluster in clusters
        if cluster.get("cluster_tier", cluster.get("tier")) == "insufficient_signal"
    ]
    round_groups = [
        {
            "draft_id": draft_record.get("draft_id"),
            "cluster_id": draft_record.get("cluster_id"),
            "rounds": draft_record.get("rounds", []),
            "selected_round": draft_record.get("selected_round"),
            "round_count": draft_record.get("round_count", 0),
            "rethink_status": draft_record.get("rethink_status"),
            "fallback_reason": draft_record.get("fallback_reason"),
            "quality": draft_record.get("quality", {}),
        }
        for draft_record in drafts
    ]
    ceilings = [1 for _ in round_groups]
    all_rounds = [
        round_record
        for group in round_groups
        for round_record in group.get("rounds", [])
        if isinstance(round_record, dict)
    ]
    if dry_run:
        quality: dict[str, object] = {
            "coverage_ratio": None,
            "retained_input_unit_ratio": None,
            "unsupported_claim_rate": None,
            "faithfulness_status": None,
        }
        cost: dict[str, object] = {
            "generator_calls": 0,
            "planned_generator_calls": sum(ceilings),
            "total_input_chars": 0,
            "total_output_chars": 0,
            "total_provider_tokens": None,
            "round_count": 0,
            "cost_ceiling_sum": sum(ceilings),
        }
    else:
        def average(name: str) -> float:
            values = [float(item[name]) for item in all_rounds if item.get(name) is not None]
            return round(sum(values) / len(values), 6) if values else 0.0

        statuses = [str(group.get("quality", {}).get("faithfulness_status")) for group in round_groups]
        quality = {
            "coverage_ratio": average("coverage_ratio"),
            "retained_input_unit_ratio": average("retained_input_unit_ratio"),
            "unsupported_claim_rate": average("unsupported_claim_rate"),
            "faithfulness_status": (
                None
                if not statuses
                else "passed"
                if all(status in {"faithful", "passed"} for status in statuses)
                else statuses[0]
                if len(set(statuses)) == 1
                else "mixed"
            ),
        }
        token_values = [item.get("provider_input_tokens") for item in all_rounds] + [
            item.get("provider_output_tokens") for item in all_rounds
        ]
        total_tokens = sum(int(value) for value in token_values) if token_values and all(value is not None for value in token_values) else None
        cost = {
            "generator_calls": len(all_rounds),
            "planned_generator_calls": sum(ceilings),
            "total_input_chars": sum(int(item.get("input_chars", 0)) for item in all_rounds),
            "total_output_chars": sum(int(item.get("output_chars", 0)) for item in all_rounds),
            "total_provider_tokens": total_tokens,
            "round_count": len(all_rounds),
            "cost_ceiling_sum": sum(ceilings),
        }
    return {
        "risk_rule_version": RISK_RULE_VERSION,  # frozen label; risk engine removed in B3
        "risk_decisions": [],
        "skipped_clusters": skipped,
        "rounds": round_groups,
        "rethink": round_groups,
        "quality": quality,
        "cost": cost,
        "benefit_status": "unmeasured",
    }


def _update_digest_report(
    report_path: Path,
    drafts: list[dict[str, object]],
    decisions: list[dict[str, object]],
    clusters: list[dict[str, object]],
    *,
    dry_run: bool,
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report.update(_digest_metrics(drafts, decisions, clusters, dry_run=dry_run))
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _initial_report(
    run_dir: Path,
    *,
    dry_run: bool,
    source_notes: int,
    roots: tuple[str, ...],
    settings: DigestSettings,
    structure: StructureContract,
) -> Path:
    report_path = run_dir / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "dry_run": dry_run,
                "source_notes": source_notes,
                "roots": list(roots),
                "settings": {
                    "top_k": settings.top_k,
                    "high": settings.high,
                    "medium": settings.medium,
                    "max_lines": settings.max_lines,
                    "max_doc_lines": settings.max_lines,
                    "risk_rule_version": settings.risk_rule_version,
                },
                "risk_rule_version": RISK_RULE_VERSION,
                "benefit_status": "unmeasured",
                "structure_check": structure.as_dict(),
                "official_write": {
                    "allow_official_write": structure.allow_official_write,
                    "status": "pending",
                },
                "source_filter": {},
                "pending_review": [],
                "archive_cleanup": [],
                "formal_kb_changes": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if not dry_run:
        (run_dir / "structure-check.json").write_text(
            json.dumps(structure.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report_path


def _read_failed_snapshots(run_dir: Path) -> list[dict[str, object]]:
    path = run_dir / "s1" / "source-snapshots.jsonl"
    if not path.exists():
        return []
    from .jsonl import read_jsonl

    return [row for row in read_jsonl(path) if row.get("validation_status") not in {"passed", "verified", "ok"}]


def _history_key(record: dict[str, object]) -> tuple[str, str]:
    return (str(record.get("source_uri")), str(record.get("fragment_locator")))


def fold_claim_history(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Collapse an append-only history into the latest state of each claim.

    Lines are ordered oldest-first. A later line with the same claim_fingerprint
    supersedes the earlier state of that claim, so `supersede` marker lines
    written after a claim's original record win.
    """
    folded: dict[str, dict[str, object]] = {}
    for record in records:
        identity = str(record.get("claim_fingerprint") or record.get("claim_id"))
        previous = folded.get(identity)
        folded[identity] = {**previous, **record} if previous else dict(record)
    return list(folded.values())


def _update_claim_history(
    paths: DigestPaths,
    drafts: list[dict[str, object]],
    *,
    run_id: str,
    failed_snapshots: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Append verified claims and retain old claims as pending on later failures."""
    history_path = paths.kb_dir / "_digest" / "claim-history.jsonl"
    history = fold_claim_history(read_jsonl(history_path))
    active_by_key: dict[tuple[str, str], dict[str, object]] = {}
    for record in history:
        if record.get("verification_status") not in {"pending_review", "removed"}:
            if not record.get("superseded_by"):
                active_by_key[_history_key(record)] = record

    new_records: list[dict[str, object]] = []
    supersede_markers: list[dict[str, object]] = []
    for draft_record in drafts:
        for claim in draft_record.get("claims", []):
            claim = dict(claim)
            page_claim = next(
                (
                    page_claim
                    for page in draft_record.get("split_pages", [])
                    for page_claim in page.get("claims", [])
                    if page_claim.get("claim_fingerprint") == claim.get("claim_fingerprint")
                ),
                None,
            )
            if page_claim:
                claim["target_path"] = page_claim.get("target_path")
                claim["page_index"] = page_claim.get("page_index", 1)
            key = _history_key(claim)
            previous = active_by_key.get(key)
            if previous and previous.get("claim_fingerprint") != claim.get("claim_fingerprint"):
                previous["superseded_by"] = claim.get("claim_fingerprint")
                claim["supersedes"] = previous.get("claim_fingerprint")
                previous["verification_status"] = "superseded"
                # Append-only: emit the superseded claim's new state as its own
                # line instead of rewriting the original line in place.
                supersede_markers.append(dict(previous))
                claim_fingerprint_value = claim.get("claim_fingerprint")
                for page in draft_record.get("split_pages", []):
                    for page_claim in page.get("claims", []):
                        if page_claim.get("claim_fingerprint") == claim_fingerprint_value:
                            page_claim["supersedes"] = claim.get("supersedes")
                            page_claim["superseded_by"] = claim.get("superseded_by")
            record = {
                **claim,
                "claim_id": f"{draft_record['draft_id']}-{len(new_records) + 1}",
                "run_id": run_id,
                "page_path": claim.get("target_path"),
                "verification_status": "verified",
                "validation_status": "passed",
            }
            new_records.append(record)
            active_by_key[key] = record

    failed_uris = {str(row.get("source_uri")) for row in failed_snapshots if row.get("source_uri")}
    pending: list[dict[str, object]] = []
    for record in history:
        if str(record.get("source_uri")) in failed_uris and record.get("verification_status") not in {"removed", "superseded"}:
            record["verification_status"] = "pending_review"
            record["validation_status"] = "failed"
            record["validation_reason"] = next(
                (row.get("validation_reason") for row in failed_snapshots if row.get("source_uri") == record.get("source_uri")),
                "local source validation failed",
            )
            record["retry_status"] = "retry_next_manual_run"
            pending.append(dict(record))
            supersede_markers.append(dict(record))

    append_jsonl(history_path, [*supersede_markers, *new_records])
    _merge_pending_review(
        paths.kb_dir / "_digest" / "pending-review.jsonl",
        pending,
        resolved={_history_key(record) for record in new_records},
    )
    return pending


def _merge_pending_review(
    pending_path: Path,
    pending: list[dict[str, object]],
    *,
    resolved: set[tuple[str, str]],
) -> None:
    """Keep earlier pending entries; only this run's re-verified claims clear."""
    merged: dict[tuple[str, str], dict[str, object]] = {}
    for record in read_jsonl(pending_path):
        key = _history_key(record)
        if key not in resolved:
            merged[key] = record
    for record in pending:
        merged[_history_key(record)] = record
    # The queue is merged, not appended, so the rewrite must be atomic: a crash
    # mid-write would otherwise truncate every entry still awaiting review.
    replace_jsonl(pending_path, list(merged.values()))


def _write_source_index(paths: DigestPaths, run_dir: Path, records: list[dict[str, object]]) -> None:
    write_jsonl(run_dir / "s6" / "source-index.jsonl", records)
    write_jsonl(paths.kb_dir / "_digest" / "source-index.jsonl", records)


def _finalize_report(
    report_path: Path,
    *,
    writes: list[dict[str, object]],
    pending: list[dict[str, object]],
    cleanup: list[dict[str, object]],
    raw_items: list[dict[str, object]],
    failed_snapshots: list[dict[str, object]],
    plan: dict[str, object] | None = None,
    official_status: str = "written",
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["formal_kb_changes"] = _formal_changes(writes)
    report["official_write"] = {
        **report.get("official_write", {}),
        "status": official_status,
        "allow_official_write": official_status == "written",
    }
    report["source_filter"] = {
        "accepted_source_uris": sorted({str(item["source_uri"]) for item in raw_items}),
        "rejected_source_uris": sorted({str(row.get("source_uri")) for row in failed_snapshots if row.get("source_uri")}),
        "rejected_count": len(failed_snapshots),
        "final_index_excludes_rejected": True,
    }
    report["pending_review"] = pending
    report["archive_cleanup"] = cleanup
    if plan is not None:
        report["write_plan_snapshot"] = plan
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _commit_outputs(
    *,
    drafts: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    failed_snapshots: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
    run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Write every formal side effect straight into the real knowledge base."""
    processable_cluster_ids = {
        cluster.get("cluster_id")
        for cluster in clusters
        if cluster.get("cluster_tier", cluster.get("tier")) != "insufficient_signal"
    }
    processable_raw_ids = {
        member
        for cluster in clusters
        if cluster.get("cluster_id") in processable_cluster_ids
        for member in cluster.get("members", [])
    }
    processable_items = [item for item in raw_items if item.get("raw_id") in processable_raw_ids]
    processable_input_paths = {str(item.get("input_path")) for item in processable_items}
    snapshots = [
        snapshot
        for snapshot in read_jsonl(run_dir / "s1" / "source-snapshots.jsonl")
        if str(snapshot.get("input_path")) in processable_input_paths
    ]
    append_jsonl(paths.kb_dir / "_digest" / "source-snapshots.jsonl", snapshots)
    queue_root = roots[2] if len(roots) >= 3 else "_queues"
    write_queues(
        paths.kb_dir,
        queue_root,
        [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "needs_review"],
        [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "insufficient_signal"],
    )

    writes = writeback(drafts, run_dir, paths, roots)
    audit_provenance(drafts, writes, processable_items, run_dir)
    if processable_items:
        _write_source_index(paths, run_dir, source_index_records(processable_items, run_dir))
    else:
        write_jsonl(run_dir / "s6" / "source-index.jsonl", [])
    for draft_record in drafts:
        removed = draft_record.get("removed_claims", [])
        if removed:
            archive_claim_records(
                paths.kb_dir,
                removed,
                operation="remove_claim",
                reason="claim failed local faithfulness validation",
                run_id=run_id,
                archive_root=roots[1] if len(roots) > 1 else "_archive",
            )
    pending = (
        _update_claim_history(
            paths,
            drafts,
            run_id=run_id,
            failed_snapshots=failed_snapshots,
        )
        if processable_items or failed_snapshots or drafts
        else []
    )
    return writes, pending, []


def audit_run(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...] = DEFAULT_ROOTS,
    *,
    dry_run: bool,
    generator: Any = None,
) -> tuple[Path, str]:
    """Run S1-S6 under a single-writer lock on the knowledge base."""
    with kb_lock(paths.kb_dir):
        return _audit_run_locked(paths, settings, roots, dry_run=dry_run, generator=generator)


def _audit_run_locked(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...],
    *,
    dry_run: bool,
    generator: Any = None,
) -> tuple[Path, str]:
    """Run S1-S6 and write the formal outputs directly into the knowledge base."""
    audit_root = paths.kb_dir / "_digest"
    if audit_root.is_symlink():
        raise ValidationError("audit_run", audit_root, "_digest must not be a symlink")
    if audit_root.exists() and not audit_root.is_dir():
        raise ValidationError("audit_run", audit_root, "_digest must be a directory")
    structure = inspect_structure(paths.structure_path)
    source_notes = sum(
        1
        for path in paths.items_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
    )
    run_id = f"run-{uuid4().hex}"
    effective_run_id = run_id if not dry_run else f"{run_id}-dry"
    run_dir = audit_root / "runs" / effective_run_id

    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = _initial_report(
        run_dir,
        dry_run=dry_run,
        source_notes=source_notes,
        roots=roots,
        settings=settings,
        structure=structure,
    )

    if not dry_run and not structure.allow_official_write:
        raw_items = ingest(paths, run_dir, persist_snapshot=False)
        failed_snapshots = _read_failed_snapshots(run_dir)
        _finalize_report(
            report_path,
            writes=[],
            pending=[],
            cleanup=[],
            raw_items=raw_items,
            failed_snapshots=failed_snapshots,
            official_status="blocked_structure",
        )
        missing = ", ".join(structure.missing_fields)
        return report_path, f"audit blocked: missing structure declarations ({missing}); no formal knowledge-base files written"

    if dry_run:
        with tempfile.TemporaryDirectory(prefix="knowledge-digest-plan-") as temporary:
            planning_dir = Path(temporary)
            raw_items = ingest(
                paths,
                planning_dir,
                persist_snapshot=False,
            )
            clusters = cluster(raw_items, planning_dir, paths, roots, settings, persist_queues=False)
            decisions = retrieve(clusters, raw_items, planning_dir, paths, roots, settings)
            for decision in decisions:
                decision["page_root"] = roots[0]
            drafts = draft(decisions, clusters, raw_items, planning_dir, settings, dry_run=True)
            plan = _write_plan(drafts, paths, roots)
            failed_snapshots = _read_failed_snapshots(planning_dir)
        _finalize_report(
            report_path,
            writes=[],
            pending=[],
            cleanup=[],
            raw_items=raw_items,
            failed_snapshots=failed_snapshots,
            plan=plan,
            official_status="dry_run",
        )
        _update_digest_report(report_path, drafts, decisions, clusters, dry_run=True)
        summary = (
            f"dry-run: audited {source_notes} source note(s); roots={', '.join(roots)}; "
            f"top_k={settings.top_k}; high={settings.high:.2f}; medium={settings.medium:.2f}; "
            f"max_lines={settings.max_lines}; no formal knowledge-base files written"
        )
        return report_path, summary

    raw_items = ingest(paths, run_dir, persist_snapshot=False)
    failed_snapshots = _read_failed_snapshots(run_dir)
    clusters = cluster(raw_items, run_dir, paths, roots, settings, persist_queues=False)
    decisions = retrieve(clusters, raw_items, run_dir, paths, roots, settings)
    for decision in decisions:
        decision["page_root"] = roots[0]
    drafts = draft(decisions, clusters, raw_items, run_dir, settings, generator=generator)
    coverage = [row for draft_record in drafts for row in draft_record.get("coverage_mapping", [])]
    covered = {(row.get("raw_id"), row.get("input_fragment")) for row in coverage}
    all_claims = {
        (claim.get("raw_id"), claim.get("fragment_locator"))
        for draft_record in drafts
        for claim in draft_record.get("claims", [])
    }
    if covered != all_claims:
        write_jsonl(run_dir / "s4" / "coverage-failed.jsonl", [{"reason": "claim has no output page mapping"}])
        _finalize_report(
            report_path,
            writes=[],
            pending=[],
            cleanup=[],
            raw_items=raw_items,
            failed_snapshots=failed_snapshots,
            official_status="blocked_coverage",
        )
        _update_digest_report(report_path, drafts, decisions, clusters, dry_run=False)
        return report_path, "audit blocked: coverage mapping is incomplete; no formal knowledge-base files written"

    writes, pending, cleanup = _commit_outputs(
        drafts=drafts,
        clusters=clusters,
        raw_items=raw_items,
        failed_snapshots=failed_snapshots,
        run_dir=run_dir,
        paths=paths,
        roots=roots,
        run_id=run_id,
    )
    plan = {"formal_kb_changes": _formal_changes(writes)}
    _finalize_report(
        report_path,
        writes=writes,
        pending=pending,
        cleanup=cleanup,
        raw_items=raw_items,
        failed_snapshots=failed_snapshots,
        plan=plan,
        official_status="written",
    )
    _update_digest_report(report_path, drafts, decisions, clusters, dry_run=False)
    summary = (
        f"audit committed: audited {source_notes} source note(s); roots={', '.join(roots)}; "
        f"top_k={settings.top_k}; high={settings.high:.2f}; medium={settings.medium:.2f}; "
        f"max_lines={settings.max_lines}; {len(writes)} formal output(s) committed"
    )
    return report_path, summary
