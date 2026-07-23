"""Phase-one audit pipeline with fail-closed formal-write boundaries."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .cluster import cluster
from .config import DigestSettings
from .draft import draft
from .errors import ValidationError
from .ingest import ingest
from .kb_structure import DEFAULT_ROOTS, StructureContract, inspect_structure
from .jsonl import write_jsonl
from .paths import DigestPaths
from .provenance import (
    archive_claim_records,
    audit_provenance,
    cleanup_expired_archives,
    source_index_records,
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
        targets = [page.get("target_path") for page in pages] if pages else [
            targets_for_draft(item, roots[0])[0].as_posix()
        ]
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


def _run_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:12]}"


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
                },
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


def audit_run(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...] = DEFAULT_ROOTS,
    *,
    dry_run: bool,
) -> tuple[Path, str]:
    """Run S1-S6, stopping before formal writes when a prerequisite fails."""
    audit_root = paths.kb_dir / "_digest"
    if audit_root.is_symlink():
        raise ValidationError("audit_run", audit_root, "_digest must not be a symlink")
    if audit_root.exists() and not audit_root.is_dir():
        raise ValidationError("audit_run", audit_root, "_digest must be a directory")
    run_dir = audit_root / "runs" / _run_id()
    run_dir.mkdir(parents=True)
    structure = inspect_structure(paths.structure_path)
    source_notes = sum(
        1
        for path in paths.items_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
    )
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
            drafts = draft(decisions, clusters, raw_items, planning_dir, settings)
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
        summary = (
            f"dry-run: audited {source_notes} source note(s); roots={', '.join(roots)}; "
            f"top_k={settings.top_k}; high={settings.high:.2f}; medium={settings.medium:.2f}; "
            f"max_lines={settings.max_lines}; no formal knowledge-base files written"
        )
        return report_path, summary

    raw_items = ingest(
        paths,
        run_dir,
    )
    failed_snapshots = _read_failed_snapshots(run_dir)
    clusters = cluster(raw_items, run_dir, paths, roots, settings)
    decisions = retrieve(clusters, raw_items, run_dir, paths, roots, settings)
    for decision in decisions:
        decision["page_root"] = roots[0]
    drafts = draft(decisions, clusters, raw_items, run_dir, settings)
    coverage = [row for draft_record in drafts for row in draft_record.get("coverage_mapping", [])]
    covered = {(row.get("raw_id"), row.get("input_fragment")) for row in coverage}
    all_claims = {(claim.get("raw_id"), claim.get("fragment_locator")) for draft_record in drafts for claim in draft_record.get("claims", [])}
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
        return report_path, "audit blocked: coverage mapping is incomplete; no formal knowledge-base files written"

    # Link a changed claim to its predecessor before the archive snapshot is
    # created. The durable history is committed only after page writes pass.
    _update_claim_history(
        paths,
        drafts,
        run_id=run_dir.name,
        failed_snapshots=failed_snapshots,
        persist=False,
    )
    writes = writeback(drafts, run_dir, paths, roots)
    audit_provenance(drafts, writes, raw_items, run_dir)
    _write_source_index(paths, run_dir, source_index_records(raw_items, run_dir))
    for draft_record in drafts:
        removed = draft_record.get("removed_claims", [])
        if removed:
            archive_claim_records(
                paths.kb_dir,
                removed,
                operation="remove_claim",
                reason="claim failed local faithfulness validation",
                run_id=run_dir.name,
                archive_root=roots[1] if len(roots) > 1 else "_archive",
            )
    pending = _update_claim_history(
        paths,
        drafts,
        run_id=run_dir.name,
        failed_snapshots=failed_snapshots,
    )
    cleanup = cleanup_expired_archives(paths.kb_dir, roots[1] if len(roots) > 1 else "_archive", run_dir=run_dir)
    _finalize_report(
        report_path,
        writes=writes,
        pending=pending,
        cleanup=cleanup,
        raw_items=raw_items,
        failed_snapshots=failed_snapshots,
        official_status="written",
    )
    summary = (
        f"audit: audited {source_notes} source note(s); roots={', '.join(roots)}; "
        f"top_k={settings.top_k}; high={settings.high:.2f}; medium={settings.medium:.2f}; "
        f"max_lines={settings.max_lines}; {len(writes)} formal knowledge-base file(s) written"
    )
    return report_path, summary
