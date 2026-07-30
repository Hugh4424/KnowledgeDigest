"""Phase-one audit pipeline with fail-closed formal-write boundaries."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import uuid4

from .cluster import cluster
from .config import DigestSettings, RISK_RULE_VERSION
from .draft import draft
from .errors import ValidationError
from .embedding import EmbeddingError, resolve_similarity_backend
from .ingest import ingest
from .kb_structure import (
    DEFAULT_ROOTS,
    StructureContract,
    initialize_default_publication,
    inspect_structure,
)
from .jsonl import append_jsonl, read_jsonl, replace_jsonl, write_jsonl
from .identity import source_id
from .faithfulness import claim_entity_key
from .lock import kb_lock
from .paths import DigestPaths, is_new_kb_container
from .provenance import (
    archive_claim_records,
    audit_provenance,
)
from .page_layout import build_publication_navigation, build_topic_layouts, declared_managed_topics
from .queues import write_queues
from .retrieve import retrieve
from .text_similarity import EmbeddingScorer, JaccardScorer
from .writeback import targets_for_draft, writeback


def _formal_changes(writes: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = ("target_path", "action", "status", "archive_path")
    return [{key: row[key] for key in keys} for row in writes]


def _run_similarity_stages(
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
    settings: DigestSettings,
    *,
    publication: Any = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    effective_publication = publication
    if effective_publication is None and paths.structure_path.is_file():
        effective_publication = inspect_structure(paths.structure_path).publication
    try:
        resolution = resolve_similarity_backend(settings)
    except EmbeddingError as error:
        resolution = None
        resolution_failure = error
    else:
        resolution_failure = None
    if resolution_failure is not None:
        fallback = JaccardScorer()
        clusters = cluster(raw_items, run_dir, paths, roots, settings, persist_queues=False, scorer=fallback)
        decisions = retrieve(clusters, raw_items, run_dir, paths, roots, settings, scorer=fallback)
        return clusters, decisions, {
            "requested_backend": "embedding",
            "effective_backend": "jaccard",
            "reason_code": "embedding_probe_failed",
            "failure_type": type(resolution_failure).__name__,
            "fallback_restarted_from": "S2",
            "cache": {"entries": 0},
            "effective_thresholds": {
                "high": settings.high,
                "medium": settings.medium,
                "page_match_threshold": settings.page_match_threshold,
            },
        }
    assert resolution is not None
    scorer = (
        EmbeddingScorer(
            resolution.client,
            resolution.probe_fingerprint or "",
            run_dir / "embedding-cache.jsonl",
        )
        if resolution.effective_backend == "embedding"
        else JaccardScorer()
    )
    effective_settings = settings
    if resolution.thresholds is not None:
        effective_settings = replace(settings, **resolution.thresholds)
    try:
        if isinstance(scorer, EmbeddingScorer):
            scorer.prefetch([str(item["text"]) for item in raw_items])
        clusters = cluster(
            raw_items,
            run_dir,
            paths,
            roots,
            effective_settings,
            persist_queues=False,
            scorer=scorer,
        )
        if isinstance(scorer, EmbeddingScorer):
            by_id = {item["raw_id"]: item for item in raw_items}
            composite = [
                "\n".join(str(by_id[raw_id]["text"]) for raw_id in item["members"])
                for item in clusters
                if item.get("tier", item.get("cluster_tier")) != "insufficient_signal"
            ]
            if effective_publication is None:
                page_root = paths.kb_dir / roots[0]
                pages = [
                    path.read_text(encoding="utf-8")
                    for path in sorted(page_root.rglob("*.md"))
                    if path.is_file()
                ] if page_root.exists() else []
            else:
                pages = [
                    record["path"].read_text(encoding="utf-8")
                    for record in declared_managed_topics(paths, effective_publication)
                ]
            scorer.prefetch(composite + pages)
        decisions = retrieve(
            clusters,
            raw_items,
            run_dir,
            paths,
            roots,
            effective_settings,
            scorer=scorer,
        )
        return clusters, decisions, {
            "requested_backend": resolution.requested_backend,
            "effective_backend": resolution.effective_backend,
            "reason_code": resolution.reason_code,
            "fallback_restarted_from": None,
            "cache": getattr(scorer, "cache_stats", {"entries": 0}),
            "effective_thresholds": {
                "high": effective_settings.high,
                "medium": effective_settings.medium,
                "page_match_threshold": effective_settings.page_match_threshold,
            },
        }
    except EmbeddingError as error:
        fallback = JaccardScorer()
        clusters = cluster(
            raw_items,
            run_dir,
            paths,
            roots,
            settings,
            persist_queues=False,
            scorer=fallback,
        )
        decisions = retrieve(
            clusters,
            raw_items,
            run_dir,
            paths,
            roots,
            settings,
            scorer=fallback,
        )
        return clusters, decisions, {
            "requested_backend": "embedding",
            "effective_backend": "jaccard",
            "reason_code": "embedding_run_failed",
            "failure_type": type(error).__name__,
            "fallback_restarted_from": "S2",
            "cache": getattr(scorer, "cache_stats", {"entries": 0}),
            "effective_thresholds": {
                "high": settings.high,
                "medium": settings.medium,
                "page_match_threshold": settings.page_match_threshold,
            },
        }


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
    ceilings = [
        int(draft_record.get("planned_generator_calls", 1))
        for draft_record in drafts
    ]
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
            "generator_calls": sum(
                int(item.get("provider_call_count", 1)) for item in all_rounds
            ),
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


def _write_similarity_audit(
    report_path: Path, similarity_audit: dict[str, Any]
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["similarity"] = similarity_audit
    if "effective_thresholds" in similarity_audit and "settings" in report:
        report["settings"].update(similarity_audit["effective_thresholds"])
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
                    "page_match_threshold": settings.page_match_threshold,
                    "high": settings.high,
                    "medium": settings.medium,
                    "max_lines": settings.max_lines,
                    "max_doc_lines": settings.max_lines,
                    "risk_rule_version": settings.risk_rule_version,
                    "routing_rule_version": settings.routing_rule_version,
                    "llm_batch_max_claims": settings.llm_batch_max_claims,
                    "llm_batch_max_source_chars": settings.llm_batch_max_source_chars,
                    "llm_enabled": settings.llm_enabled,
                    "llm_summary_enabled": settings.llm_summary_enabled,
                },
                "risk_rule_version": RISK_RULE_VERSION,
                "routing_rule_version": settings.routing_rule_version,
                "benefit_status": "unmeasured",
                "structure_check": structure.as_dict(),
                "official_write": {
                    "allow_official_write": structure.allow_official_write,
                    "status": "pending",
                },
                "source_filter": {},
                "similarity": {
                    "requested_backend": settings.similarity.backend,
                    "effective_backend": "jaccard",
                    "reason_code": "not_resolved",
                },
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

    Lines are ordered oldest-first. A later line for the same source occurrence
    supersedes the earlier state, so a marker written after a claim wins without
    collapsing another identical line from that source.
    """
    folded: dict[tuple[str, str, str], dict[str, object]] = {}
    for record in records:
        identity = claim_entity_key(record)
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
            page_claims = [
                page_claim
                for page in draft_record.get("split_pages", [])
                for page_claim in page.get("claims", [])
                if page_claim.get("claim_fingerprint") == claim.get("claim_fingerprint")
                and page_claim.get("source_uri") == claim.get("source_uri")
                and page_claim.get("raw_id") == claim.get("raw_id")
                and page_claim.get("fragment_locator") == claim.get("fragment_locator")
            ]
            if len(page_claims) != 1:
                raise ValidationError(
                    "history",
                    claim.get("claim_fingerprint", "claim"),
                    "final layout must assign every claim to exactly one topic part",
                )
            page_claim = page_claims[0]
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
                        if (
                            page_claim.get("claim_fingerprint") == claim_fingerprint_value
                            and page_claim.get("source_uri") == claim.get("source_uri")
                            and page_claim.get("raw_id") == claim.get("raw_id")
                            and page_claim.get("fragment_locator") == claim.get("fragment_locator")
                        ):
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


def _write_source_index(paths: DigestPaths, run_dir: Path) -> None:
    """Materialize one compact, link-only record for every reachable source."""
    snapshots: dict[str, dict[str, object]] = {}
    for snapshot in read_jsonl(paths.kb_dir / "_digest" / "source-snapshots.jsonl"):
        uri = str(snapshot.get("source_uri", ""))
        if uri:
            snapshots[uri] = dict(snapshot)
    active_history = fold_claim_history(read_jsonl(paths.kb_dir / "_digest" / "claim-history.jsonl"))
    links_by_source: dict[str, set[str]] = {}
    for record in active_history:
        if record.get("verification_status") in {"removed", "superseded", "pending_review"} or record.get("superseded_by"):
            continue
        uri = str(record.get("source_uri", ""))
        target = str(record.get("target_path") or record.get("page_path") or "")
        if uri and target:
            links_by_source.setdefault(uri, set()).add(target)
    duplicate_of: dict[str, str] = {}
    for duplicate in read_jsonl(paths.kb_dir / "_digest" / "duplicates.jsonl"):
        uri = str(duplicate.get("source_uri", ""))
        canonical = str(duplicate.get("canonical_source_uri", ""))
        if uri and canonical:
            duplicate_of[uri] = canonical
    records: list[dict[str, object]] = []
    for uri, snapshot in sorted(snapshots.items()):
        if str(snapshot.get("validation_status", "")).lower() not in {"passed", "verified", "ok"}:
            continue
        canonical = duplicate_of.get(uri, uri)
        topic_paths = sorted(links_by_source.get(uri) or links_by_source.get(canonical, set()))
        if not topic_paths:
            continue
        records.append(
            {
                "source_id": source_id(uri),
                "source_uri": uri,
                "topic_paths": topic_paths,
            }
        )
    write_jsonl(run_dir / "s6" / "source-index.jsonl", records)
    if not records and not (paths.kb_dir / "_digest" / "source-index.jsonl").exists():
        return
    write_jsonl(paths.kb_dir / "_digest" / "source-index.jsonl", records)
    lines = ["# Source Index", ""]
    for record in records:
        lines.append(f"- `{record['source_uri']}`")
        for target in record["topic_paths"]:
            relative = Path(os.path.relpath(paths.kb_dir / str(target), paths.kb_dir / "_digest")).as_posix()
            lines.append(f"  - [{Path(str(target)).name}]({relative})")
    (run_dir / "s6" / "source-index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (paths.kb_dir / "_digest" / "source-index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_layout_artifacts(
    run_dir: Path,
    drafts: list[dict[str, Any]],
    publication_navigation: list[dict[str, Any]],
) -> None:
    """Replace provisional S4 paths with the final, auditable layout mapping."""
    write_jsonl(run_dir / "s4" / "final-layouts.jsonl", drafts)
    write_jsonl(run_dir / "s4" / "drafts.jsonl", drafts)
    write_jsonl(
        run_dir / "s4" / "coverage-mapping.jsonl",
        [row for draft_record in drafts for row in draft_record.get("coverage_mapping", [])],
    )
    # Keep the exact records used by the owned-file, archive-before-write
    # publication transaction for replay and audit.
    write_jsonl(run_dir / "s4" / "publication-navigation.jsonl", publication_navigation)


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
    topic_drafts: list[dict[str, Any]],
    navigation_records: list[dict[str, Any]],
    publication: Any,
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
    snapshots = read_jsonl(run_dir / "s1" / "source-snapshots.jsonl")
    append_jsonl(paths.kb_dir / "_digest" / "source-snapshots.jsonl", snapshots)
    append_jsonl(
        paths.kb_dir / "_digest" / "duplicates.jsonl",
        read_jsonl(run_dir / "s1" / "duplicates.jsonl"),
    )
    queue_root = roots[2] if len(roots) >= 3 else "_queues"
    write_queues(
        paths.kb_dir,
        queue_root,
        [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "needs_review"],
        [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "insufficient_signal"],
    )

    writes = writeback(
        [*topic_drafts, *navigation_records],
        run_dir,
        paths,
        roots,
        publication=publication,
    )
    audit_provenance(
        topic_drafts,
        writes,
        processable_items,
        run_dir,
        source_snapshots=read_jsonl(paths.kb_dir / "_digest" / "source-snapshots.jsonl"),
    )
    for draft_record in topic_drafts:
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
            topic_drafts,
            run_id=run_id,
            failed_snapshots=failed_snapshots,
        )
        if processable_items or failed_snapshots or topic_drafts
        else []
    )
    _write_source_index(paths, run_dir)
    return writes, pending, []


def audit_run(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...] = DEFAULT_ROOTS,
    *,
    dry_run: bool,
    generator: Any = None,
    allowed_content_paths: set[str] | None = None,
    cluster_plan: list[dict[str, Any]] | None = None,
    global_duplicates: dict[str, dict[str, str]] | None = None,
) -> tuple[Path, str]:
    """Run S1-S6 under a single-writer lock on the knowledge base."""
    with kb_lock(paths.kb_dir):
        return _audit_run_locked(
            paths,
            settings,
            roots,
            dry_run=dry_run,
            generator=generator,
            allowed_content_paths=allowed_content_paths,
            cluster_plan=cluster_plan,
            global_duplicates=global_duplicates,
        )


def _audit_run_locked(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...],
    *,
    dry_run: bool,
    generator: Any = None,
    allowed_content_paths: set[str] | None = None,
    cluster_plan: list[dict[str, Any]] | None = None,
    global_duplicates: dict[str, dict[str, str]] | None = None,
) -> tuple[Path, str]:
    """Run S1-S6 and write the formal outputs directly into the knowledge base."""
    if paths.initialize_new_kb:
        if dry_run:
            raise ValidationError("publication", paths.kb_dir, "dry-run must not initialize a new knowledge base")
        if not is_new_kb_container(paths.kb_dir):
            raise ValidationError("publication", paths.kb_dir, "new knowledge-base container is not empty")
        initialize_default_publication(paths.kb_dir)
    audit_root = paths.kb_dir / "_digest"
    if audit_root.is_symlink():
        raise ValidationError("audit_run", audit_root, "_digest must not be a symlink")
    if audit_root.exists() and not audit_root.is_dir():
        raise ValidationError("audit_run", audit_root, "_digest must be a directory")
    structure = inspect_structure(paths.structure_path)
    if structure.publication_errors:
        raise ValidationError(
            "publication",
            paths.structure_path,
            "; ".join(structure.publication_errors),
        )
    roots = structure.roots
    source_notes = sum(
        1
            for path in paths.items_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".md", ".txt", ".json"}
            and (allowed_content_paths is None or path.relative_to(paths.items_dir).as_posix() in allowed_content_paths)
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
        raw_items = ingest(
            paths,
            run_dir,
            persist_snapshot=False,
            allowed_content_paths=allowed_content_paths,
            global_duplicates=global_duplicates,
        )
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
                allowed_content_paths=allowed_content_paths,
                global_duplicates=global_duplicates,
            )
            clusters, decisions, similarity_audit = _run_similarity_stages(
                raw_items, planning_dir, paths, roots, settings, publication=structure.publication
            )
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
        _write_similarity_audit(report_path, similarity_audit)
        effective_thresholds = similarity_audit["effective_thresholds"]
        summary = (
            f"dry-run: audited {source_notes} source note(s); roots={', '.join(roots)}; "
            f"top_k={settings.top_k}; high={effective_thresholds['high']:.2f}; "
            f"medium={effective_thresholds['medium']:.2f}; "
            f"page_match_threshold={effective_thresholds['page_match_threshold']:.2f}; "
            f"max_lines={settings.max_lines}; no formal knowledge-base files written"
        )
        return report_path, summary

    raw_items = ingest(
        paths,
        run_dir,
        persist_snapshot=False,
        allowed_content_paths=allowed_content_paths,
        global_duplicates=global_duplicates,
    )
    failed_snapshots = _read_failed_snapshots(run_dir)
    clusters, decisions, similarity_audit = _run_similarity_stages(
        raw_items, run_dir, paths, roots, settings, publication=structure.publication
    )
    if cluster_plan is not None:
        by_id = {str(item["raw_id"]): item for item in raw_items}
        planned_clusters: list[dict[str, Any]] = []
        planned_members: set[str] = set()
        for planned in cluster_plan:
            members = [str(member) for member in planned.get("members", []) if str(member) in by_id]
            if not members:
                continue
            planned_members.update(members)
            planned_clusters.append(
                {
                    **planned,
                    "members": members,
                    "source_uris": [str(by_id[member]["source_uri"]) for member in members],
                    "source_ids": [str(by_id[member].get("source_id", "")) for member in members],
                    "source_count": len(members),
                }
            )
        unplanned = sorted(set(by_id) - planned_members)
        if unplanned:
            raise ValidationError("batch", ", ".join(unplanned), "batch source is absent from the fixed topic plan")
        clusters = planned_clusters
        write_jsonl(run_dir / "s2" / "clusters.jsonl", clusters)
        decisions = retrieve(clusters, raw_items, run_dir, paths, roots, settings)
    for decision in decisions:
        decision["page_root"] = roots[0]
    drafts = draft(decisions, clusters, raw_items, run_dir, settings, generator=generator)
    if structure.publication is None:
        raise ValidationError("publication", paths.structure_path, "publication contract is unavailable")
    drafts = build_topic_layouts(
        drafts,
        paths,
        roots,
        max_lines=settings.max_lines,
        publication=structure.publication,
    )
    publication_navigation = build_publication_navigation(drafts, paths, structure.publication) if drafts else []
    _write_layout_artifacts(run_dir, drafts, publication_navigation)
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
        _write_similarity_audit(report_path, similarity_audit)
        return report_path, "audit blocked: coverage mapping is incomplete; no formal knowledge-base files written"

    writes, pending, cleanup = _commit_outputs(
        topic_drafts=drafts,
        navigation_records=publication_navigation,
        publication=structure.publication,
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
    _write_similarity_audit(report_path, similarity_audit)
    effective_thresholds = similarity_audit["effective_thresholds"]
    summary = (
        f"audit committed: audited {source_notes} source note(s); roots={', '.join(roots)}; "
        f"top_k={settings.top_k}; high={effective_thresholds['high']:.2f}; "
        f"medium={effective_thresholds['medium']:.2f}; "
        f"page_match_threshold={effective_thresholds['page_match_threshold']:.2f}; "
        f"max_lines={settings.max_lines}; {len(writes)} formal output(s) committed"
    )
    return report_path, summary
