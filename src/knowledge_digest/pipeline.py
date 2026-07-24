"""Phase-one audit pipeline with fail-closed formal-write boundaries."""

from __future__ import annotations

import json
import hashlib
import shutil
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
from .jsonl import read_jsonl, write_jsonl
from .paths import DigestPaths
from .provenance import (
    append_jsonl,
    archive_claim_records,
    audit_provenance,
    cleanup_expired_archives,
    source_index_records,
)
from .queues import write_queues
from .recovery import (
    RecoveryPaths,
    acquire_lock,
    build_input_manifest,
    commit_staged_outputs,
    load_recovery_state,
    mark_prepared,
    manifest_hash,
    output_plan_hash,
    record_recovery_error,
    release_lock,
    stable_run_id,
    verify_committed_outputs,
    write_staged_file,
)
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
    """Project replayable risk, round, quality, and cost facts into report.json."""
    risk_decisions = [
        decision["risk_decision"]
        for decision in decisions
        if isinstance(decision.get("risk_decision"), dict)
    ]
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
            "risk_decision": draft_record.get("risk_decision"),
            "rounds": draft_record.get("rounds", []),
            "selected_round": draft_record.get("selected_round"),
            "round_count": draft_record.get("round_count", 0),
            "max_rounds": draft_record.get("max_rounds"),
            "rethink_status": draft_record.get("rethink_status"),
            "fallback_reason": draft_record.get("fallback_reason"),
            "quality": draft_record.get("quality", {}),
        }
        for draft_record in drafts
    ]
    ceilings = [int(item.get("max_rounds", 0)) for item in round_groups]
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
        "risk_rule_version": RISK_RULE_VERSION,
        "risk_decisions": risk_decisions,
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


def _update_claim_history(
    paths: DigestPaths,
    drafts: list[dict[str, object]],
    *,
    run_id: str,
    failed_snapshots: list[dict[str, object]],
    persist: bool = True,
) -> list[dict[str, object]]:
    """Append verified claims and retain old claims as pending on later failures."""
    from .jsonl import read_jsonl, write_jsonl

    history_path = paths.kb_dir / "_digest" / "claim-history.jsonl"
    history = read_jsonl(history_path)
    active_by_key: dict[tuple[str, str], dict[str, object]] = {}
    for record in history:
        if record.get("verification_status") not in {"pending_review", "removed"}:
            key = (str(record.get("source_uri")), str(record.get("fragment_locator")))
            if not record.get("superseded_by"):
                active_by_key[key] = record

    new_records: list[dict[str, object]] = []
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
            key = (str(claim.get("source_uri")), str(claim.get("fragment_locator")))
            previous = active_by_key.get(key)
            if previous and previous.get("claim_fingerprint") != claim.get("claim_fingerprint"):
                previous["superseded_by"] = claim.get("claim_fingerprint")
                claim["supersedes"] = previous.get("claim_fingerprint")
                previous["verification_status"] = "superseded"
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

    if persist:
        write_jsonl(history_path, [*history, *new_records])
        write_jsonl(paths.kb_dir / "_digest" / "pending-review.jsonl", pending)
    return pending


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


_STAGED_DIGEST_FILES = frozenset(
    {
        "_digest/claim-history.jsonl",
        "_digest/pending-review.jsonl",
        "_digest/source-index.jsonl",
        "_digest/source-snapshots.jsonl",
    }
)


def _formal_snapshot_paths(kb_dir: Path, roots: tuple[str, ...]) -> set[str]:
    """Return only formal KB files; run reports and recovery state stay local."""
    paths: set[str] = set(_STAGED_DIGEST_FILES)
    for root in dict.fromkeys((*roots, "_archive", "_queues")):
        root_path = kb_dir / root
        if root_path.is_dir():
            paths.update(
                path.relative_to(kb_dir).as_posix()
                for path in root_path.rglob("*")
                if path.is_file() and not path.is_symlink()
            )
    return paths


def _file_bytes(path: Path) -> bytes | None:
    if path.is_symlink():
        raise ValidationError("recovery", path, "RECOVERY_STATE_INVALID: formal output must be a regular file")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValidationError("recovery", path, "RECOVERY_STATE_INVALID: formal output must be a regular file")
    return path.read_bytes()


def _output_kind(relative_target: str) -> str:
    if relative_target == "_archive/records.jsonl":
        return "archive_records"
    if relative_target.startswith("_archive/"):
        return "archive_content"
    if relative_target.startswith("_queues/"):
        return "queue"
    if relative_target.startswith("_digest/"):
        return "digest_metadata"
    return "page"


def _stage_formal_diff(
    *,
    original_kb: Path,
    prepared_kb: Path,
    recovery: RecoveryPaths,
    roots: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Stage every formal replacement and deletion from the simulated KB."""
    relative_paths = _formal_snapshot_paths(original_kb, roots) | _formal_snapshot_paths(prepared_kb, roots)
    outputs: list[dict[str, Any]] = []
    for relative_target in sorted(relative_paths):
        before = _file_bytes(original_kb / relative_target)
        after = _file_bytes(prepared_kb / relative_target)
        if before == after:
            continue
        if after is None:
            outputs.append(
                {
                    "operation": "delete",
                    "kind": _output_kind(relative_target),
                    "relative_target": relative_target,
                    "staged_path": None,
                    "size_bytes": 0,
                    "before_sha256": hashlib.sha256(before).hexdigest() if before is not None else None,
                    "after_sha256": None,
                    "status": "pending",
                }
            )
            continue
        staged_path = write_staged_file(recovery.staging, relative_target, after)
        outputs.append(
            {
                "operation": "replace",
                "kind": _output_kind(relative_target),
                "relative_target": relative_target,
                "staged_path": staged_path,
                "size_bytes": len(after),
                "before_sha256": hashlib.sha256(before).hexdigest() if before is not None else None,
                "after_sha256": hashlib.sha256(after).hexdigest(),
                "status": "pending",
            }
        )
    return outputs


def _prepare_formal_outputs(
    *,
    drafts: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    failed_snapshots: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
    run_id: str,
    recovery: RecoveryPaths,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Render all formal side effects against a temporary KB clone.

    The existing writeback/provenance helpers remain the single rendering
    implementation.  The clone makes their result observable as bytes without
    allowing any formal KB mutation before a later commit phase.
    """
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
    with tempfile.TemporaryDirectory(prefix="knowledge-digest-prepare-") as temporary:
        prepared_kb = Path(temporary) / "kb"
        shutil.copytree(paths.kb_dir, prepared_kb, symlinks=True)
        prepared_paths = DigestPaths(
            new_dir=paths.new_dir,
            items_dir=paths.items_dir,
            kb_dir=prepared_kb,
            structure_path=prepared_kb / paths.structure_path.relative_to(paths.kb_dir),
        )
        processable_input_paths = {str(item.get("input_path")) for item in processable_items}
        snapshots = [
            snapshot
            for snapshot in read_jsonl(run_dir / "s1" / "source-snapshots.jsonl")
            if str(snapshot.get("input_path")) in processable_input_paths
        ]
        append_jsonl(prepared_kb / "_digest" / "source-snapshots.jsonl", snapshots)
        queue_root = roots[2] if len(roots) >= 3 else "_queues"
        write_queues(
            prepared_kb,
            queue_root,
            [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "needs_review"],
            [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "insufficient_signal"],
        )

        writes = writeback(drafts, run_dir, prepared_paths, roots)
        audit_provenance(drafts, writes, processable_items, run_dir)
        if processable_items:
            _write_source_index(prepared_paths, run_dir, source_index_records(processable_items, run_dir))
        else:
            write_jsonl(run_dir / "s6" / "source-index.jsonl", [])
        for draft_record in drafts:
            removed = draft_record.get("removed_claims", [])
            if removed:
                archive_claim_records(
                    prepared_kb,
                    removed,
                    operation="remove_claim",
                    reason="claim failed local faithfulness validation",
                    run_id=run_id,
                    archive_root=roots[1] if len(roots) > 1 else "_archive",
                )
        pending = (
            _update_claim_history(
                prepared_paths,
                drafts,
                run_id=run_id,
                failed_snapshots=failed_snapshots,
            )
            if processable_items or failed_snapshots or drafts
            else []
        )
        cleanup = cleanup_expired_archives(
            prepared_kb,
            roots[1] if len(roots) > 1 else "_archive",
            run_dir=run_dir,
        )
        outputs = _stage_formal_diff(
            original_kb=paths.kb_dir,
            prepared_kb=prepared_kb,
            recovery=recovery,
            roots=roots,
        )
    return writes, pending, cleanup, outputs


def _mark_report_committed(report_path: Path, state: dict[str, Any], *, status: str) -> None:
    if not report_path.exists():
        raise ValidationError("recovery", report_path.parent, "RECOVERY_STATE_INVALID: run report is missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["official_write"] = {
        **report.get("official_write", {}),
        "status": status,
        "allow_official_write": status == "written",
    }
    report["recovery"] = {
        "run_id": state.get("run_id"),
        "status": state.get("status"),
        "recovery_attempts": state.get("recovery_attempts", 0),
        "completed_outputs": len(state.get("completed_outputs", [])),
        "staged_outputs": len(state.get("staged_outputs", [])),
        "last_error": state.get("last_error"),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit_run(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...] = DEFAULT_ROOTS,
    *,
    dry_run: bool,
) -> tuple[Path, str]:
    """Run S1-S6, prepare a closed output list, then commit or resume it."""
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
    manifest = build_input_manifest(paths, settings, roots)
    input_manifest_hash = manifest_hash(manifest)
    run_id = stable_run_id(manifest)
    effective_run_id = run_id if not dry_run else f"{run_id}-dry-{uuid4().hex[:12]}"
    run_dir = audit_root / "runs" / effective_run_id
    recovery = RecoveryPaths.for_run(paths.kb_dir, run_id)

    existing_state = None if dry_run else load_recovery_state(paths.kb_dir, run_id)
    if existing_state is not None:
        if existing_state.get("input_manifest_hash") != input_manifest_hash:
            raise ValidationError("recovery", paths.kb_dir, "RECOVERY_STATE_INVALID: input manifest does not match run")
        if existing_state.get("status") == "committed":
            if recovery.lock.exists():
                raise ValidationError("recovery", paths.kb_dir, "RECOVERY_STATE_INVALID: committed run still has a writer lock")
            verify_committed_outputs(paths.kb_dir, existing_state)
            report_path = run_dir / "report.json"
            _mark_report_committed(report_path, existing_state, status="written")
            return report_path, f"already_committed: run_id={run_id}; no formal knowledge-base files changed"
        if existing_state.get("status") not in {"prepared", "committing"}:
            raise ValidationError("recovery", paths.kb_dir, "RECOVERY_STATE_INVALID: run is not safely recoverable")

        # A prepared/committing run already contains the complete generated
        # output list.  Recovery must not re-run ingest, retrieve, or rethink.
        handle, state = acquire_lock(
            paths.kb_dir,
            run_id,
            input_manifest_hash=input_manifest_hash,
            target_kb=paths.kb_dir,
        )
        try:
            state = commit_staged_outputs(paths.kb_dir, state, handle=handle)
            _mark_report_committed(run_dir / "report.json", state, status="written")
            return run_dir / "report.json", f"audit committed: recovered run_id={run_id}; formal outputs committed"
        except BaseException as error:
            current_state = load_recovery_state(paths.kb_dir, run_id) or state
            try:
                record_recovery_error(paths.kb_dir, current_state, error)
            except Exception:
                pass
            raise
        finally:
            release_lock(handle)

    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = _initial_report(
        run_dir,
        dry_run=dry_run,
        source_notes=source_notes,
        roots=roots,
        settings=settings,
        structure=structure,
    )
    writes: list[dict[str, object]] = []
    pending: list[dict[str, object]] = []
    cleanup: list[dict[str, object]] = []
    plan: dict[str, object] | None = None

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

    handle, state = acquire_lock(
        paths.kb_dir,
        run_id,
        input_manifest_hash=input_manifest_hash,
        target_kb=paths.kb_dir,
    )
    try:
        raw_items = ingest(paths, run_dir, persist_snapshot=False)
        failed_snapshots = _read_failed_snapshots(run_dir)
        clusters = cluster(raw_items, run_dir, paths, roots, settings, persist_queues=False)
        decisions = retrieve(clusters, raw_items, run_dir, paths, roots, settings)
        for decision in decisions:
            decision["page_root"] = roots[0]
        drafts = draft(decisions, clusters, raw_items, run_dir, settings)
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
            record_recovery_error(
                paths.kb_dir,
                state,
                ValidationError("s4", run_id, "coverage mapping is incomplete"),
            )
            return report_path, "audit blocked: coverage mapping is incomplete; no formal knowledge-base files written"

        # Link changed claims to predecessors before the temporary archive
        # snapshot is built. Nothing below writes to the formal KB.
        _update_claim_history(
            paths,
            drafts,
            run_id=run_id,
            failed_snapshots=failed_snapshots,
            persist=False,
        )
        writes, pending, cleanup, staged_outputs = _prepare_formal_outputs(
            drafts=drafts,
            clusters=clusters,
            raw_items=raw_items,
            failed_snapshots=failed_snapshots,
            run_dir=run_dir,
            paths=paths,
            roots=roots,
            run_id=run_id,
            recovery=recovery,
        )
        plan = {
            "formal_kb_changes": _formal_changes(writes),
            "staged_outputs": staged_outputs,
            "plan_hash": output_plan_hash(staged_outputs),
        }
        state = mark_prepared(
            paths.kb_dir,
            state,
            staged_outputs=staged_outputs,
            plan_hash=str(plan["plan_hash"]),
        )
        _finalize_report(
            report_path,
            writes=writes,
            pending=pending,
            cleanup=cleanup,
            raw_items=raw_items,
            failed_snapshots=failed_snapshots,
            plan=plan,
            official_status="prepared",
        )
        _update_digest_report(report_path, drafts, decisions, clusters, dry_run=False)
        state = commit_staged_outputs(paths.kb_dir, state, handle=handle)
        _mark_report_committed(report_path, state, status="written")
        summary = (
            f"audit committed: audited {source_notes} source note(s); roots={', '.join(roots)}; "
            f"top_k={settings.top_k}; high={settings.high:.2f}; medium={settings.medium:.2f}; "
            f"max_lines={settings.max_lines}; {len(staged_outputs)} formal output(s) committed"
        )
        return report_path, summary
    except BaseException as error:
        try:
            current_state = load_recovery_state(paths.kb_dir, run_id) or state
            record_recovery_error(paths.kb_dir, current_state, error)
        except Exception:
            pass
        raise
    finally:
        release_lock(handle)
