"""Phase-one audit pipeline with fail-closed formal-write boundaries."""

from __future__ import annotations

import json
import hashlib
import os
import tempfile
import time
from urllib.parse import urlsplit, urlunsplit
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import uuid4

from .cluster import cluster
from .config import DigestSettings, RISK_RULE_VERSION
from .draft import draft
from .errors import ValidationError
from .embedding import EmbeddingError, normalize_endpoint_identity, resolve_similarity_backend
from .ingest import ingest
from .llm import PUBLICATION_LLM_BASE_URL, PUBLICATION_LLM_MODEL
from .kb_structure import (
    DEFAULT_ROOTS,
    StructureContract,
    initialize_default_publication,
    inspect_structure,
    serialize_source_index,
    validate_source_index,
    validate_topic_index,
)
from .jsonl import append_jsonl, read_jsonl, replace_jsonl, write_jsonl
from .identity import source_id
from .faithfulness import claim_entity_key
from .lock import kb_lock
from .paths import DigestPaths, is_new_kb_container
from .provenance import (
    archive_claim_records,
    audit_provenance,
    validate_prewrite_provenance,
)
from .page_layout import build_publication_navigation, build_topic_layouts, declared_managed_topics
from .queues import write_queues
from .retrieve import retrieve
from .text_similarity import EmbeddingScorer, JaccardScorer
from .writeback import targets_for_draft, writeback


def _formal_changes(writes: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = ("target_path", "action", "status", "archive_path")
    return [{key: row[key] for key in keys} for row in writes]


def _config_identity(settings: DigestSettings, structure: StructureContract) -> str:
    embedding = settings.similarity.embedding
    payload = {
        "settings": {
            "top_k": settings.top_k,
            "page_match_threshold": settings.page_match_threshold,
            "high": settings.high,
            "medium": settings.medium,
            "max_lines": settings.max_lines,
            "risk_rule_version": settings.risk_rule_version,
            "routing_rule_version": settings.routing_rule_version,
            "llm_enabled": settings.llm_enabled,
            "llm_format": settings.llm_format,
            "llm_summary_enabled": settings.llm_summary_enabled,
            "llm_batch_max_claims": settings.llm_batch_max_claims,
            "llm_batch_max_source_chars": settings.llm_batch_max_source_chars,
            "llm_batch_concurrency": settings.llm_batch_concurrency,
            "similarity_backend": settings.similarity.backend,
            "embedding_model": embedding.model if embedding else None,
            "embedding_dimension": embedding.expected_dimension if embedding else None,
        },
        "publication": structure.as_dict().get("publication"),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _merge_jsonl_unique(path: Path, records: list[dict[str, Any]], key_fields: tuple[str, ...]) -> None:
    merged: dict[tuple[str, ...], dict[str, Any]] = {}
    order: list[tuple[str, ...]] = []
    for record in [*read_jsonl(path), *records]:
        key = tuple(str(record.get(field, "")) for field in key_fields)
        if key not in merged:
            order.append(key)
        merged[key] = record
    replace_jsonl(path, [merged[key] for key in order])


def _source_audit_ledger(
    manifest: dict[str, Any],
    snapshots: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    duplicate_by_uri = {
        str(row.get("source_uri")): row
        for row in duplicates
        if row.get("source_uri")
    }
    claims_by_uri: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        uri = str(claim.get("source_uri") or "")
        if uri:
            claims_by_uri.setdefault(uri, []).append(claim)
    rows: list[dict[str, Any]] = []
    for source in manifest["sources"]:
        uri = str(source.get("source_uri") or "")
        snapshot = next(
            (row for row in snapshots if str(row.get("source_uri") or "") == uri and row.get("content_fingerprint") == source.get("content_fingerprint")),
            None,
        )
        claims = claims_by_uri.get(uri, [])
        duplicate = duplicate_by_uri.get(uri)
        canonical_uri = str(duplicate.get("canonical_source_uri")) if duplicate else uri
        if not claims and canonical_uri != uri:
            claims = claims_by_uri.get(canonical_uri, [])
        rows.append(
            {
                "content_path": source["content_path"],
                "source_id": source["source_id"],
                "source_uri": uri,
                "content_fingerprint": source["content_fingerprint"],
                "snapshot_id": source.get("snapshot_id"),
                "validation_status": (snapshot or {}).get("validation_status", "failed"),
                "validation_reason": (snapshot or {}).get("validation_reason"),
                "duplicate_of": duplicate.get("duplicate_of") if duplicate else None,
                "canonical_source_uri": canonical_uri,
                "target_paths": sorted({str(claim.get("target_path") or "") for claim in claims if claim.get("target_path")}),
                "claim_ids": sorted({str(claim.get("claim_fingerprint")) for claim in claims if claim.get("claim_fingerprint")}),
            }
        )
    return rows


def _claim_records(topic_drafts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract the same claim set for both prewrite validation and the ledger."""
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for draft_record in topic_drafts:
        candidates = [
            dict(claim)
            for claim in draft_record.get("claims", [])
            if isinstance(claim, dict)
        ]
        for page in draft_record.get("split_pages", []) or []:
            if not isinstance(page, dict):
                continue
            for claim in page.get("claims", []) or []:
                if not isinstance(claim, dict):
                    continue
                enriched = dict(claim)
                if page.get("target_path"):
                    enriched.setdefault("target_path", page["target_path"])
                candidates.append(enriched)
        for claim in candidates:
            key = str(
                claim.get("claim_fingerprint")
                or f"{claim.get('source_uri', '')}|{claim.get('fragment_locator', '')}|{claim.get('text', '')}"
            )
            if key not in merged:
                order.append(key)
                merged[key] = claim
            else:
                merged[key] = {**merged[key], **claim}
    return [merged[key] for key in order]


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
    llm_enabled: bool,
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

    timeout_markers = {
        "timeout",
        "timed_out",
        "deadline_exceeded",
        "provider_timeout",
    }

    def is_timeout_record(record: dict[str, Any]) -> bool:
        if record.get("timeout_exceeded") is True:
            return True
        for field in ("status", "timeout_status", "error_code"):
            value = record.get(field)
            if isinstance(value, str) and value.strip().lower().replace("-", "_") in timeout_markers:
                return True
        for child in record.get("batches", []) if isinstance(record.get("batches"), list) else []:
            if isinstance(child, dict) and is_timeout_record(child):
                return True
        return False

    timeout_exceeded = any(is_timeout_record(record) for record in all_rounds)
    if dry_run:
        quality: dict[str, object] = {
            "coverage_ratio": None,
            "retained_input_unit_ratio": None,
            "unsupported_claim_rate": None,
            "faithfulness_status": None,
        }
        cost: dict[str, object] = {
            "generator_calls": 0,
            "planned_generator_calls": sum(ceilings) if llm_enabled else 0,
            "provider_calls_planned": sum(ceilings) if llm_enabled else 0,
            "provider_calls_observed": 0,
            "failed_calls": 0,
            "replay_calls": 0,
            "timeout_exceeded": False,
            "elapsed_seconds": 0.0,
            "fallback_ratio": None,
            "status": "dry_run",
            "total_input_chars": 0,
            "total_output_chars": 0,
            "total_provider_tokens": None,
            "round_count": 0,
            "deterministic_rounds": 0,
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
            ) if llm_enabled else 0,
            "planned_generator_calls": sum(ceilings) if llm_enabled else 0,
            "provider_calls_planned": sum(ceilings) if llm_enabled else 0,
            "provider_calls_observed": sum(
                int(item.get("provider_call_count", 1)) for item in all_rounds
            ) if llm_enabled else 0,
            "failed_calls": sum(1 for item in all_rounds if item.get("status") == "invalid"),
            "replay_calls": sum(
                max(0, int(item.get("provider_attempt_count", 1)) - 1)
                for item in all_rounds
            ),
            "timeout_exceeded": timeout_exceeded,
            "elapsed_seconds": round(
                sum(int(item.get("elapsed_ms", 0)) for item in all_rounds) / 1000,
                3,
            ),
            "fallback_ratio": round(
                sum(1 for draft_record in drafts if draft_record.get("fallback_reason")) / len(drafts),
                6,
            ) if drafts else 0.0,
            "status": "completed",
            "total_input_chars": sum(int(item.get("input_chars", 0)) for item in all_rounds),
            "total_output_chars": sum(int(item.get("output_chars", 0)) for item in all_rounds),
            "total_provider_tokens": total_tokens,
            "round_count": len(all_rounds),
            "deterministic_rounds": len(all_rounds) if not llm_enabled else 0,
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
    llm_enabled: bool,
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report.update(_digest_metrics(drafts, decisions, clusters, dry_run=dry_run, llm_enabled=llm_enabled))
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


_TASK0_QUESTION_SET_PATH = Path(__file__).resolve().parents[2] / "config" / "task0-question-set.v1.json"
_TASK0_TIMEOUT_SECONDS = 180
_TASK0_REPLAY_LIMIT = 1
_TASK0_PROVIDER_CALL_MULTIPLIER = 4
_TASK0_GENERATOR_HARD_CAP = 180
_TASK0_WALL_TARGET_SECONDS = 1800
_TASK0_WALL_HARD_CAP_SECONDS = 3600


def _task0_question_set_facts() -> dict[str, Any]:
    try:
        value = json.loads(_TASK0_QUESTION_SET_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("runtime_audit", _TASK0_QUESTION_SET_PATH, f"question set is unreadable ({error})") from error
    if not isinstance(value, dict) or value.get("schema_version") != "task0-question-set.v1":
        raise ValidationError("runtime_audit", _TASK0_QUESTION_SET_PATH, "question set schema is invalid")
    questions = value.get("questions")
    if not isinstance(questions, list) or len(questions) != 20:
        raise ValidationError("runtime_audit", _TASK0_QUESTION_SET_PATH, "question set must contain exactly 20 questions")
    positive = sum(isinstance(row, dict) and row.get("polarity") == "positive" for row in questions)
    negative = sum(isinstance(row, dict) and row.get("polarity") == "negative" for row in questions)
    if positive != 17 or negative != 3:
        raise ValidationError("runtime_audit", _TASK0_QUESTION_SET_PATH, "question set must contain 17 positive and 3 negative questions")
    canonical = {
        key: value.get(key)
        for key in ("schema_version", "question_set_id", "questions", "derivation_rules")
    }
    expected_hash = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if value.get("question_set_hash") != expected_hash:
        raise ValidationError("runtime_audit", _TASK0_QUESTION_SET_PATH, "question set hash does not match canonical content")
    return {
        "path": _TASK0_QUESTION_SET_PATH.relative_to(_TASK0_QUESTION_SET_PATH.parents[1]).as_posix(),
        "question_set_id": value.get("question_set_id"),
        "question_set_hash": expected_hash,
        "positive_count": positive,
        "negative_count": negative,
        "sample_seed": value.get("sample_seed"),
        "reviewer": value.get("reviewer"),
    }


def _task0_canonical_endpoint(value: str) -> str:
    try:
        normalized = normalize_endpoint_identity(value)
    except ValueError:
        return value.rstrip("/")
    parsed = urlsplit(normalized)
    host = parsed.hostname or ""
    netloc = host if parsed.port == 443 and parsed.scheme == "https" else parsed.netloc
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def _task0_budget_status(cost: dict[str, Any], *, source_count: int) -> str:
    planned = int(cost.get("planned_generator_calls") or 0)
    observed = int(cost.get("provider_calls_observed") or 0)
    replay_calls = int(cost.get("replay_calls") or 0)
    elapsed = float(cost.get("wall_clock_elapsed_seconds", cost.get("elapsed_seconds")) or 0.0)
    if (
        planned > _TASK0_GENERATOR_HARD_CAP
        or observed > source_count * _TASK0_PROVIDER_CALL_MULTIPLIER
        or replay_calls > _TASK0_REPLAY_LIMIT
        or bool(cost.get("timeout_exceeded"))
        or elapsed > _TASK0_WALL_HARD_CAP_SECONDS
    ):
        return "exceeded"
    if elapsed > _TASK0_WALL_TARGET_SECONDS:
        return "target_exceeded"
    return "within_budget"


def _task0_llm_allowlist(settings: DigestSettings) -> bool:
    if not settings.llm_enabled:
        return True
    return (
        os.environ.get("KD_LLM_MODEL") == PUBLICATION_LLM_MODEL
        and os.environ.get("KD_LLM_BASE_URL", "").rstrip("/") == PUBLICATION_LLM_BASE_URL
    )


def _task0_embedding_allowlist(settings: DigestSettings) -> bool:
    embedding = settings.similarity.embedding
    if embedding is None:
        return True
    return (
        embedding.model == "jina-embeddings"
        and _task0_canonical_endpoint(embedding.base_url) == "https://llm.paxszapp.com/v1"
    )


def _task0_runtime_audit(
    settings: DigestSettings,
    similarity_audit: dict[str, Any],
    *,
    source_count: int,
    cost: dict[str, Any],
    page_statuses: list[str],
    writes: bool,
) -> dict[str, Any]:
    requested_backend = str(similarity_audit.get("requested_backend") or settings.similarity.backend)
    effective_backend = str(similarity_audit.get("effective_backend") or settings.similarity.backend)
    fallback_used = requested_backend != effective_backend
    embedding = settings.similarity.embedding
    calibration_sha256 = None
    if embedding and embedding.calibration_artifact.is_file():
        calibration_sha256 = hashlib.sha256(embedding.calibration_artifact.read_bytes()).hexdigest()
    embedding_provider = {
        "model": embedding.model if embedding else None,
        "endpoint": _task0_canonical_endpoint(embedding.base_url) if embedding else None,
        "dimension": embedding.expected_dimension if embedding else None,
        "probe_fingerprint": similarity_audit.get("probe_fingerprint") if embedding else None,
        "calibration_sha256": calibration_sha256,
        "credential_source": f"environment:{embedding.api_key_env}" if embedding else None,
        "allowlist": "passed" if _task0_embedding_allowlist(settings) else "failed",
    }
    page_status = None if not page_statuses else "published" if all(status == "published" for status in page_statuses) else "degraded"
    if not writes and page_status == "published":
        page_status = "degraded"
    provider_calls = int(cost.get("provider_calls_observed") or 0) if settings.llm_enabled else 0
    embedding_calls = int(similarity_audit.get("provider_calls_observed") or 0)
    budget_status = _task0_budget_status(cost, source_count=source_count)
    if budget_status != "within_budget" and page_status == "published":
        page_status = "degraded"
    llm_model = os.environ.get("KD_LLM_MODEL") if settings.llm_enabled else None
    llm_endpoint = _task0_canonical_endpoint(os.environ.get("KD_LLM_BASE_URL", "")) if settings.llm_enabled else None
    llm_allowlist = _task0_llm_allowlist(settings)
    return {
        "schema_version": "task0-runtime-audit.v1",
        "provider": {
            "llm": {
                "model": llm_model,
                "endpoint": llm_endpoint,
                "credential_source": "environment:KD_LLM_API_KEY" if settings.llm_enabled else None,
                "allowlist": "passed" if llm_allowlist else "failed",
            },
            "embedding": embedding_provider,
        },
        "backend": {
            "requested": requested_backend,
            "effective": effective_backend,
        },
        "fallback": {
            "used": fallback_used,
            "from": requested_backend if fallback_used else None,
            "to": effective_backend if fallback_used else None,
            "reason": str(similarity_audit.get("reason_code")) if fallback_used else None,
        },
        "calls": {"llm": provider_calls, "embedding": embedding_calls},
        "budget": {
            "timeout_seconds": _TASK0_TIMEOUT_SECONDS,
            "replay_limit": _TASK0_REPLAY_LIMIT,
            "provider_call_budget": source_count * _TASK0_PROVIDER_CALL_MULTIPLIER,
            "planned_generator_calls": cost.get("planned_generator_calls"),
            "provider_calls_observed": cost.get("provider_calls_observed"),
            "replay_calls": cost.get("replay_calls"),
            "timeout_exceeded": bool(cost.get("timeout_exceeded")),
            "wall_clock_elapsed_seconds": cost.get("wall_clock_elapsed_seconds"),
            "planned_generator_hard_cap": _TASK0_GENERATOR_HARD_CAP,
            "wall_clock_target_seconds": _TASK0_WALL_TARGET_SECONDS,
            "wall_clock_hard_cap_seconds": _TASK0_WALL_HARD_CAP_SECONDS,
        },
        "budget_status": budget_status,
        "question_set": _task0_question_set_facts(),
        "page_status": page_status,
        "delivery_status": "not_released",
        "reason": (
            "provider not allowlisted"
            if not llm_allowlist
            else "semantic fallback"
            if fallback_used
            else None
        ),
    }


def _business_counts(kb_dir: Path) -> dict[str, int]:
    def jsonl_count(relative: str) -> int:
        path = kb_dir / relative
        return len(read_jsonl(path)) if path.is_file() else 0

    runs = kb_dir / "_digest" / "runs"
    return {
        "source_snapshots": jsonl_count("_digest/source-snapshots.jsonl"),
        "claims": jsonl_count("_digest/claim-history.jsonl"),
        "duplicates": jsonl_count("_digest/duplicates.jsonl"),
        "archive_records": jsonl_count("_archive/records.jsonl"),
        "run_reports": len([path for path in runs.glob("*/report.json") if path.is_file()]) if runs.is_dir() else 0,
    }


def _manifest_identity(kb_dir: Path) -> dict[str, str | None]:
    path = kb_dir / "_digest" / "source-manifest.json"
    if not path.is_file():
        return {"manifest_sha256": None, "config_identity": None}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"manifest_sha256": None, "config_identity": None}
    return {
        "manifest_sha256": value.get("manifest_sha256") if isinstance(value.get("manifest_sha256"), str) else None,
        "config_identity": value.get("config_identity") if isinstance(value.get("config_identity"), str) else None,
    }


def _growth_records(kb_dir: Path, baseline: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    files = {
        "source_snapshots": "_digest/source-snapshots.jsonl",
        "claims": "_digest/claim-history.jsonl",
        "duplicates": "_digest/duplicates.jsonl",
        "archive_records": "_archive/records.jsonl",
    }
    records: dict[str, list[dict[str, Any]]] = {}
    for key, relative in files.items():
        rows = read_jsonl(kb_dir / relative)
        start = int(baseline.get(key, 0) or 0)
        records[key] = [
            {
                "ref": f"{relative}#line-{index + 1}",
                **{
                    field: row.get(field)
                    for field in (
                        "source_id",
                        "snapshot_id",
                        "claim_fingerprint",
                        "duplicate_of",
                        "canonical_source_id",
                        "archive_key",
                        "target_path",
                    )
                    if row.get(field) is not None
                },
            }
            for index, row in enumerate(rows[start:], start=start)
        ]
    return records


def _write_task0_runtime_audit(
    report_path: Path,
    settings: DigestSettings,
    similarity_audit: dict[str, Any],
    *,
    kb_dir: Path,
    config_identity: str,
    source_count: int,
    page_statuses: list[str],
    writes: bool,
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    started_monotonic = report.pop("_task0_started_monotonic", None)
    if started_monotonic is not None:
        cost = dict(report.get("cost", {}))
        cost["wall_clock_elapsed_seconds"] = round(
            max(0.0, time.monotonic() - float(started_monotonic)), 3
        )
        report["cost"] = cost
    runtime = _task0_runtime_audit(
        settings,
        similarity_audit,
        source_count=source_count,
        cost=report.get("cost", {}),
        page_statuses=page_statuses,
        writes=writes,
    )
    status = {
        "provider_transport": "not_requested" if not settings.llm_enabled else "completed" if not report.get("cost", {}).get("failed_calls") else "failed",
        "claim_verification": "not_run" if not page_statuses else "passed" if runtime["page_status"] == "published" and writes else "degraded",
        "written": bool(writes),
        "writeback": "written" if writes else "not_written",
        "machine_pass": (
            bool(writes)
            and runtime["budget_status"] == "within_budget"
            and runtime["page_status"] != "degraded"
            and runtime["provider"]["llm"]["allowlist"] == "passed"
            and runtime["provider"]["embedding"]["allowlist"] == "passed"
        ),
        "agent_assisted": False,
        "human_reviewed": False,
        "page_status": runtime["page_status"],
        "delivery_status": "not_released",
        "fallback": runtime["fallback"]["used"],
        "reason": runtime["reason"],
        "budget_status": runtime["budget_status"],
    }
    report["runtime_audit"] = runtime
    report["status"] = status
    growth = report.get("growth_audit", {})
    baseline = growth.get("baseline", {})
    after = _business_counts(kb_dir)
    business_keys = ("source_snapshots", "claims", "duplicates", "archive_records")
    current_identity = _manifest_identity(kb_dir)
    current_identity["config_identity"] = config_identity
    business_delta = {key: after[key] - int(baseline.get(key, 0)) for key in business_keys}
    same_input = (
        baseline.get("manifest_sha256") is not None
        and baseline.get("manifest_sha256") == current_identity.get("manifest_sha256")
        and baseline.get("config_identity") == current_identity.get("config_identity")
    )
    abnormal_growth = same_input and any(value > 0 for value in business_delta.values())
    report["growth_audit"] = {
        "baseline": baseline,
        "after": after,
        "current_identity": current_identity,
        "same_input_snapshot_and_config": same_input,
        "business_delta": business_delta,
        "run_delta": after["run_reports"] - int(baseline.get("run_reports", 0)),
        "anomaly": {
            "status": "detected" if abnormal_growth else "none",
            "basis": "content-level source/claim/duplicate/archive counts; run records are separate",
            "records": _growth_records(kb_dir, baseline) if abnormal_growth else {},
        },
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_paths = [report_path.parent / "s1" / "source-manifest.json", kb_dir / "_digest" / "source-manifest.json"]
    for manifest_path in manifest_paths:
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["runtime_audit"] = runtime
        _atomic_json(manifest_path, manifest)


def _initial_report(
    run_dir: Path,
    *,
    dry_run: bool,
    source_notes: int,
    roots: tuple[str, ...],
    settings: DigestSettings,
    structure: StructureContract,
    started_monotonic: float | None = None,
) -> Path:
    report_path = run_dir / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "_task0_started_monotonic": (
                    time.monotonic() if started_monotonic is None else started_monotonic
                ),
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
                "status": {
                    "provider_transport": "pending",
                    "claim_verification": "pending",
                    "written": False,
                    "writeback": "pending",
                    "machine_pass": False,
                    "agent_assisted": False,
                    "human_reviewed": False,
                    "page_status": None,
                    "delivery_status": "not_released",
                    "fallback": False,
                    "reason": None,
                    "budget_status": "pending",
                },
                "growth_audit": {
                    "baseline": {
                        **_business_counts(run_dir.parents[2]),
                        **_manifest_identity(run_dir.parents[2]),
                    }
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
    config_identity: str | None = None,
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
    provider_pending: list[dict[str, object]] = []
    for draft_record in drafts:
        draft_provider_failures = draft_record.get("provider_failures", [])
        has_provider_failure = bool(draft_record.get("provider_failure"))
        provider_reason = "provider output requires review"
        if isinstance(draft_provider_failures, list) and draft_provider_failures:
            first_failure = draft_provider_failures[0]
            if isinstance(first_failure, dict):
                provider_reason = str(first_failure.get("reason") or provider_reason)
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
                "verification_status": "pending_review" if has_provider_failure else "verified",
                "validation_status": "failed" if has_provider_failure else "passed",
                "config_identity": config_identity,
            }
            if (
                previous
                and previous.get("claim_fingerprint") == record.get("claim_fingerprint")
                and previous.get("target_path") == record.get("target_path")
                and previous.get("content_fingerprint") == record.get("content_fingerprint")
                and previous.get("source_snapshot_ref") == record.get("source_snapshot_ref")
                and previous.get("verification_status") == record.get("verification_status")
                and previous.get("config_identity") == record.get("config_identity")
            ):
                if has_provider_failure:
                    provider_pending.append(dict(previous))
                continue
            if has_provider_failure:
                record.update(
                    {
                        "validation_reason": provider_reason,
                        "retry_status": "retry_next_batch_run",
                        "provider_failure": True,
                    }
                )
                provider_pending.append(dict(record))
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
            if not any(
                marker.get("source_uri") == record.get("source_uri")
                and marker.get("fragment_locator") == record.get("fragment_locator")
                and marker.get("verification_status") == "pending_review"
                and marker.get("validation_reason") == record.get("validation_reason")
                for marker in supersede_markers
            ):
                supersede_markers.append(dict(record))

    append_jsonl(history_path, [*supersede_markers, *new_records])
    pending.extend(provider_pending)
    _merge_pending_review(
        paths.kb_dir / "_digest" / "pending-review.jsonl",
        pending,
        resolved={
            _history_key(record)
            for record in new_records
            if record.get("verification_status") == "verified"
        },
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


def _write_source_index(paths: DigestPaths, run_dir: Path, publication: Any = None) -> None:
    """Materialize one compact, link-only record for every reachable source."""
    snapshots: dict[str, dict[str, object]] = {}
    for snapshot in read_jsonl(paths.kb_dir / "_digest" / "source-snapshots.jsonl"):
        uri = str(snapshot.get("source_uri", ""))
        if uri:
            snapshots[uri] = dict(snapshot)
    active_history = fold_claim_history(read_jsonl(paths.kb_dir / "_digest" / "claim-history.jsonl"))
    links_by_source: dict[str, set[str]] = {}
    review_by_source: dict[str, list[str]] = {}
    for record in active_history:
        if record.get("verification_status") in {"removed", "superseded"} or record.get("superseded_by"):
            continue
        if record.get("verification_status") == "pending_review" or record.get("provider_failure"):
            review_by_source.setdefault(
                str(record.get("source_uri", "")),
                [str(record.get("validation_reason") or "provider output requires review")],
            )
            continue
        uri = str(record.get("source_uri", ""))
        target = str(record.get("target_path") or record.get("page_path") or "")
        if uri and target:
            links_by_source.setdefault(uri, set()).add(target)
            if record.get("verification_status") == "pending_review" or record.get("provider_failure"):
                review_by_source.setdefault(uri, []).append(str(record.get("validation_reason") or "provider output requires review"))
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
                "needs_review": uri in review_by_source,
            }
        )
    write_jsonl(run_dir / "s6" / "source-index.jsonl", records)
    if publication is None:
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
        return
    snapshot_fingerprints = {
        str(snapshot.get("source_uri")): str(snapshot.get("content_fingerprint"))
        for snapshot in snapshots.values()
        if snapshot.get("source_uri") and snapshot.get("content_fingerprint")
    }
    duplicate_status = {uri for uri, canonical in duplicate_of.items() if uri != canonical}
    entries = [
        {
            "source_uri": str(record["source_uri"]),
            "content_fingerprint": snapshot_fingerprints.get(str(record["source_uri"]), ""),
            "status": (
                "duplicate"
                if str(record["source_uri"]) in duplicate_status
                else "needs-review"
                if record.get("needs_review")
                else "published"
            ),
            "target_paths": list(record["topic_paths"]),
        }
        for record in records
    ]
    if all(len(entry["content_fingerprint"]) == 64 for entry in entries):
        canonical = serialize_source_index({"schema_version": "1.0.0", "entries": entries})
        (run_dir / "s6" / "source-index.md").write_text(canonical, encoding="utf-8")


def _source_index_for_navigation(
    drafts: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    *,
    persisted_root: Path | None = None,
) -> dict[str, Any]:
    """Build the compact source index before navigation enters writeback.

    A batch run publishes one increment at a time, so the reader-facing index
    must combine the immutable source snapshots and active claim history from
    prior increments with the current run.  The optional root keeps the direct
    unit seam run-local while the pipeline uses the cumulative KB state.
    """
    paths_by_source: dict[str, set[str]] = {}
    review_sources: set[str] = set()
    for draft_record in drafts:
        degraded = draft_record.get("page_status") == "degraded" or draft_record.get("provider_failure")
        if degraded:
            review_sources.update(
                str(claim.get("source_uri", ""))
                for claim in draft_record.get("claims", [])
                if claim.get("source_uri")
            )
        if degraded:
            continue
        for page in draft_record.get("split_pages", []):
            target = str(page.get("target_path", ""))
            for claim in page.get("claims", []):
                source_uri = str(claim.get("source_uri", ""))
                if source_uri and target:
                    paths_by_source.setdefault(source_uri, set()).add(target)
    duplicate_of: dict[str, str] = {}
    for record in read_jsonl(run_dir / "s1" / "duplicates.jsonl"):
        uri = str(record.get("source_uri", ""))
        canonical = str(record.get("canonical_source_uri", ""))
        if uri and canonical:
            duplicate_of[uri] = canonical
    history_rows: list[dict[str, Any]] = []
    snapshot_rows: list[dict[str, Any]] = []
    if persisted_root is not None:
        history_rows = fold_claim_history(
            read_jsonl(persisted_root / "_digest" / "claim-history.jsonl")
        )
        for record in read_jsonl(persisted_root / "_digest" / "duplicates.jsonl"):
            uri = str(record.get("source_uri", ""))
            canonical = str(record.get("canonical_source_uri", ""))
            if uri and canonical:
                duplicate_of[uri] = canonical
        snapshot_rows.extend(read_jsonl(persisted_root / "_digest" / "source-snapshots.jsonl"))
    current_snapshot_rows = read_jsonl(run_dir / "s1" / "source-snapshots.jsonl")
    snapshot_rows.extend(current_snapshot_rows)
    for record in read_jsonl(run_dir / "s1" / "duplicates.jsonl"):
        uri = str(record.get("source_uri", ""))
        canonical = str(record.get("canonical_source_uri", ""))
        if uri and canonical:
            duplicate_of[uri] = canonical
    snapshots = {
        str(item.get("source_uri")): str(item.get("content_fingerprint", ""))
        for item in snapshot_rows
        if item.get("source_uri")
    }
    planned_targets = {
        str(page.get("target_path"))
        for draft in drafts
        for page in draft.get("split_pages", [])
        if isinstance(page, dict) and page.get("target_path")
    }
    if raw_items and not current_snapshot_rows:
        raise ValidationError(
            "publication",
            run_dir / "s1" / "source-snapshots.jsonl",
            "immutable source snapshot manifest is missing or empty",
        )
    for record in history_rows:
        if record.get("verification_status") in {"removed", "superseded"}:
            continue
        source_uri = str(record.get("source_uri", ""))
        pending_review = record.get("verification_status") == "pending_review" or record.get("provider_failure")
        if pending_review:
            review_sources.add(source_uri)
        if pending_review or str(record.get("validation_status", "passed")).lower() not in {"passed", "verified", "ok"}:
            continue
        target = str(record.get("target_path") or record.get("page_path") or "")
        if source_uri and target:
            paths_by_source.setdefault(source_uri, set()).add(target)
    entries: list[dict[str, Any]] = []
    for source_uri, fingerprint in sorted(snapshots.items()):
        canonical = duplicate_of.get(source_uri, source_uri)
        target_paths = sorted(paths_by_source.get(source_uri) or paths_by_source.get(canonical, set()))
        if not target_paths and source_uri not in review_sources:
            continue
        entries.append(
            {
                "source_uri": source_uri,
                "content_fingerprint": fingerprint,
                "status": (
                    "duplicate"
                    if canonical != source_uri
                    else "needs-review"
                    if source_uri in review_sources
                    else "published"
                ),
                "target_paths": target_paths,
            }
        )
    source_index = validate_source_index({"schema_version": "1.0.0", "entries": entries})
    if persisted_root is not None:
        for entry in source_index["entries"]:
            for target in entry["target_paths"]:
                if target in planned_targets:
                    continue
                target_path = persisted_root / target
                if not target_path.is_file():
                    raise ValidationError(
                        "publication",
                        target,
                        "source index target page is missing from the Reader Package",
                    )
    return source_index


def _write_topic_index(paths: DigestPaths, drafts: list[dict[str, Any]], run_dir: Path) -> None:
    """Persist the stable topic/category/path lock separately from reader pages."""
    target = paths.kb_dir / "_digest" / "topic-index.json"
    existing: dict[str, Any] = {"schema_version": "1.0.0", "topics": []}
    if target.is_file():
        try:
            existing = validate_topic_index(json.loads(target.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise ValidationError("publication", target, f"topic-index is invalid ({error})") from error
    by_topic = {str(row["topic_id"]): dict(row) for row in existing["topics"]}
    for draft_record in drafts:
        entry = draft_record.get("topic_index_entry")
        if not isinstance(entry, dict) and draft_record.get("topic_id"):
            entry = {
                "topic_id": draft_record.get("topic_id"),
                "source_ids": sorted(
                    {
                        str(claim.get("source_id") or source_id(str(claim.get("source_uri"))))
                        for claim in draft_record.get("claims", [])
                        if claim.get("source_id") or claim.get("source_uri")
                    }
                ),
                "category_id": draft_record.get("publication_category_id") or "pending",
                "published_path": draft_record.get("published_path", ""),
                "product_slug": None,
            }
        if isinstance(entry, dict):
            by_topic[str(entry["topic_id"])] = {
                "topic_id": str(entry["topic_id"]),
                "source_ids": sorted({str(item) for item in entry.get("source_ids", []) if item}),
                "category_id": str(entry.get("category_id") or "pending"),
                "published_path": str(entry.get("published_path") or draft_record.get("published_path", "")),
                "product_slug": entry.get("product_slug"),
            }
    value = validate_topic_index({"schema_version": "1.0.0", "topics": sorted(by_topic.values(), key=lambda row: row["topic_id"])})
    encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    run_target = run_dir / "s6" / "topic-index.json"
    run_target.parent.mkdir(parents=True, exist_ok=True)
    run_target.write_text(encoded, encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, target)


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
    config_identity: str,
    allowed_content_paths: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Write every formal side effect straight into the real knowledge base."""
    from .batch_run import build_input_manifest
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
    duplicates = read_jsonl(run_dir / "s1" / "duplicates.jsonl")
    manifest_snapshots = snapshots
    manifest_duplicates = duplicates
    manifest_paths = allowed_content_paths
    if allowed_content_paths is not None:
        # A later batch may refresh a page whose claims include sources from
        # earlier batches.  The prewrite contract must therefore bind the
        # cumulative processed snapshot set, while never admitting an
        # unprocessed source from the full input manifest.
        persisted_snapshots = read_jsonl(paths.kb_dir / "_digest" / "source-snapshots.jsonl")
        persisted_duplicates = read_jsonl(paths.kb_dir / "_digest" / "duplicates.jsonl")

        def snapshot_path(row: dict[str, Any]) -> str | None:
            raw = row.get("content_path") or row.get("input_path")
            if not raw:
                return None
            candidate = Path(str(raw))
            if not candidate.is_absolute():
                return candidate.as_posix()
            try:
                return candidate.relative_to(paths.items_dir).as_posix()
            except ValueError:
                return None

        prior_paths = {
            path
            for path in (snapshot_path(row) for row in persisted_snapshots)
            if path
        }
        manifest_paths = set(allowed_content_paths) | prior_paths
        snapshots_by_path: dict[str, dict[str, Any]] = {}
        for row in [*persisted_snapshots, *snapshots]:
            path = snapshot_path(row)
            if path:
                snapshots_by_path[path] = row
        manifest_snapshots = list(snapshots_by_path.values())
        manifest_duplicates = [*persisted_duplicates, *duplicates]
    source_manifest = build_input_manifest(
        paths,
        run_id=run_id,
        config_identity=config_identity,
        snapshots=manifest_snapshots,
        duplicates=manifest_duplicates,
        allowed_content_paths=manifest_paths,
    )
    for snapshot in snapshots:
        input_path = Path(str(snapshot.get("input_path", "")))
        try:
            snapshot["content_path"] = input_path.relative_to(paths.items_dir).as_posix()
        except ValueError as error:
            raise ValidationError("manifest", input_path, "snapshot path is outside input items") from error
    for record in topic_drafts:
        record.setdefault("delivery_status", "not_released")
        record["config_identity"] = config_identity
        record.setdefault("page_status", "degraded" if record.get("provider_failure") else "published")
    for record in navigation_records:
        record.setdefault("delivery_status", "not_released")
        record["config_identity"] = config_identity
    # A provider/source failure remains in Audit and pending history, but its
    # degraded topic must not enter the Reader Package or abort unrelated
    # validated topics in the same transaction.
    reader_topic_drafts = [
        record for record in topic_drafts if record.get("page_status") != "degraded"
    ]
    reader_navigation_records = [
        record for record in navigation_records if record.get("page_status") != "degraded"
    ]
    claims = _claim_records(reader_topic_drafts)
    snapshot_by_uri = {
        str(snapshot.get("source_uri")): snapshot
        for snapshot in manifest_snapshots
        if snapshot.get("source_uri")
    }
    failed_claim_uris = {
        str(claim.get("source_uri"))
        for claim in claims
        if claim.get("source_uri")
        and str(snapshot_by_uri.get(str(claim.get("source_uri")), {}).get("validation_status", "")).lower()
        not in {"passed", "verified", "ok"}
    }
    if failed_claim_uris:
        for record in topic_drafts:
            record_claim_uris = {str(claim.get("source_uri")) for claim in _claim_records([record]) if claim.get("source_uri")}
            if record_claim_uris & failed_claim_uris:
                record["page_status"] = "degraded"
        reader_topic_drafts = [
            record for record in topic_drafts if record.get("page_status") != "degraded"
        ]
        claims = _claim_records(reader_topic_drafts)
    historical_claims = [
        row
        for row in fold_claim_history(read_jsonl(paths.kb_dir / "_digest" / "claim-history.jsonl"))
        if row.get("verification_status") not in {"removed", "superseded"}
        and not row.get("superseded_by")
    ]
    source_audit_ledger = _source_audit_ledger(
        source_manifest,
        manifest_snapshots,
        manifest_duplicates,
        [*historical_claims, *claims],
    )
    validate_prewrite_provenance(
        source_manifest,
        manifest_snapshots,
        source_audit_ledger,
        claims,
        [*reader_topic_drafts, *reader_navigation_records],
    )
    _atomic_json(run_dir / "s1" / "source-manifest.json", source_manifest)
    _atomic_json(paths.kb_dir / "_digest" / "source-manifest.json", source_manifest)
    write_jsonl(run_dir / "s1" / "source-audit-ledger.jsonl", source_audit_ledger)
    _merge_jsonl_unique(
        paths.kb_dir / "_digest" / "source-audit-ledger.jsonl",
        source_audit_ledger,
        ("content_path", "source_id", "content_fingerprint"),
    )
    _merge_jsonl_unique(paths.kb_dir / "_digest" / "source-snapshots.jsonl", snapshots, ("snapshot_id",))
    _merge_jsonl_unique(
        paths.kb_dir / "_digest" / "duplicates.jsonl",
        duplicates,
        ("path", "content_hash", "canonical_source_uri"),
    )
    has_audit_queue = any(
        cluster.get("cluster_tier", cluster.get("tier")) in {"needs_review", "insufficient_signal"}
        for cluster in clusters
    )
    if not topic_drafts and not navigation_records and not failed_snapshots and not has_audit_queue:
        return [], [], []
    queue_root = roots[2] if len(roots) >= 3 else "_queues"
    write_queues(
        paths.kb_dir,
        queue_root,
        [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "needs_review"],
        [item for item in clusters if item.get("cluster_tier", item.get("tier")) == "insufficient_signal"],
    )

    writes = writeback(
        [*reader_topic_drafts, *reader_navigation_records],
        run_dir,
        paths,
        roots,
        publication=publication,
    )
    audit_provenance(
        reader_topic_drafts,
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
            config_identity=config_identity,
        )
        if processable_items or failed_snapshots or topic_drafts
        else []
    )
    provider_review_sources: dict[str, dict[str, Any]] = {}
    for record in pending:
        if not record.get("provider_failure") and record.get("verification_status") != "pending_review":
            continue
        uri = str(record.get("source_uri", "")).strip()
        if not uri:
            continue
        item = provider_review_sources.setdefault(
            uri,
            {
                "source_uri": uri,
                "reason": str(record.get("validation_reason") or "provider output requires review"),
                "target_paths": [],
            },
        )
        target = str(record.get("target_path") or record.get("page_path") or "")
        if target and target not in item["target_paths"]:
            item["target_paths"].append(target)
    if provider_review_sources:
        write_queues(
            paths.kb_dir,
            queue_root,
            [],
            [],
            provider_sources=list(provider_review_sources.values()),
        )
    _write_source_index(paths, run_dir, publication)
    _write_topic_index(paths, topic_drafts, run_dir)
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
    from .batch_run import _source_rows
    run_started_monotonic = time.monotonic()

    # Validate the frozen declaration before a new KB receives its first
    # managed Reader files.  Batch runs still validate the complete source set;
    # the current batch is narrowed later by ``allowed_content_paths``.
    _source_rows(paths)
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
        started_monotonic=run_started_monotonic,
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
        _update_digest_report(
            report_path, drafts, decisions, clusters, dry_run=True, llm_enabled=settings.llm_enabled
        )
        _write_similarity_audit(report_path, similarity_audit)
        _write_task0_runtime_audit(
            report_path,
            settings,
            similarity_audit,
            kb_dir=paths.kb_dir,
            config_identity=_config_identity(settings, structure),
            source_count=source_notes,
            page_statuses=[],
            writes=False,
        )
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
        decisions = retrieve(
            clusters,
            raw_items,
            run_dir,
            paths,
            roots,
            settings,
            preserve_cluster_identity=True,
        )
    for decision in decisions:
        decision["page_root"] = roots[0]
    topic_universe = {
        str(record.get("topic_id"))
        for record in declared_managed_topics(paths, structure.publication)
        if record.get("topic_id")
    }
    drafts = draft(
        decisions,
        clusters,
        raw_items,
        run_dir,
        settings,
        generator=generator,
        publication=structure.publication,
        topic_universe=topic_universe,
    )
    if structure.publication is None:
        raise ValidationError("publication", paths.structure_path, "publication contract is unavailable")
    drafts = build_topic_layouts(
        drafts,
        paths,
        roots,
        max_lines=settings.max_lines,
        publication=structure.publication,
    )
    topic_universe = {
        str(record.get("topic_id"))
        for record in declared_managed_topics(paths, structure.publication)
        if record.get("topic_id")
    }
    topic_universe.update(str(draft_record.get("topic_id")) for draft_record in drafts if draft_record.get("topic_id"))
    failed_uris = {
        str(snapshot.get("source_uri"))
        for snapshot in failed_snapshots
        if snapshot.get("source_uri")
    }
    for draft_record in drafts:
        claim_uris = {
            str(claim.get("source_uri"))
            for claim in draft_record.get("claims", [])
            if claim.get("source_uri")
        }
        if draft_record.get("provider_failure") or claim_uris & failed_uris:
            draft_record["page_status"] = "degraded"
    reader_drafts = [
        draft_record for draft_record in drafts if draft_record.get("page_status") != "degraded"
    ]
    reader_topic_universe = set(topic_universe)
    reader_topic_universe.update(
        str(draft_record.get("topic_id"))
        for draft_record in reader_drafts
        if draft_record.get("topic_id")
    )
    source_index = _source_index_for_navigation(
        drafts,
        raw_items,
        run_dir,
        persisted_root=paths.kb_dir,
    )
    publication_navigation = (
        build_publication_navigation(
            reader_drafts,
            paths,
            structure.publication,
            topic_universe=reader_topic_universe,
            source_index=source_index,
        )
        if reader_drafts or source_index.get("entries")
        else []
    )
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
        _update_digest_report(
            report_path, drafts, decisions, clusters, dry_run=False, llm_enabled=settings.llm_enabled
        )
        _write_similarity_audit(report_path, similarity_audit)
        _write_task0_runtime_audit(
            report_path,
            settings,
            similarity_audit,
            kb_dir=paths.kb_dir,
            config_identity=_config_identity(settings, structure),
            source_count=source_notes,
            page_statuses=[str(draft_record.get("page_status", "published")) for draft_record in drafts],
            writes=False,
        )
        return report_path, "audit blocked: coverage mapping is incomplete; no formal knowledge-base files written"

    prospective_cost = _digest_metrics(
        drafts,
        decisions,
        clusters,
        dry_run=False,
        llm_enabled=settings.llm_enabled,
    )["cost"]
    prospective_cost["wall_clock_elapsed_seconds"] = round(
        max(0.0, time.monotonic() - run_started_monotonic), 3
    )
    prospective_budget = _task0_budget_status(prospective_cost, source_count=source_notes)
    if prospective_budget != "within_budget":
        _finalize_report(
            report_path,
            writes=[],
            pending=[],
            cleanup=[],
            raw_items=raw_items,
            failed_snapshots=failed_snapshots,
            official_status="blocked_budget",
        )
        _update_digest_report(
            report_path, drafts, decisions, clusters, dry_run=False, llm_enabled=settings.llm_enabled
        )
        _write_similarity_audit(report_path, similarity_audit)
        _write_task0_runtime_audit(
            report_path,
            settings,
            similarity_audit,
            kb_dir=paths.kb_dir,
            config_identity=_config_identity(settings, structure),
            source_count=source_notes,
            page_statuses=[str(draft_record.get("page_status", "published")) for draft_record in drafts],
            writes=False,
        )
        return report_path, f"audit blocked: Task0 budget status={prospective_budget}; no formal knowledge-base files written"

    if not _task0_llm_allowlist(settings) or not _task0_embedding_allowlist(settings):
        _finalize_report(
            report_path,
            writes=[],
            pending=[],
            cleanup=[],
            raw_items=raw_items,
            failed_snapshots=failed_snapshots,
            official_status="blocked_provider",
        )
        _update_digest_report(
            report_path, drafts, decisions, clusters, dry_run=False, llm_enabled=settings.llm_enabled
        )
        _write_similarity_audit(report_path, similarity_audit)
        _write_task0_runtime_audit(
            report_path,
            settings,
            similarity_audit,
            kb_dir=paths.kb_dir,
            config_identity=_config_identity(settings, structure),
            source_count=source_notes,
            page_statuses=[str(draft_record.get("page_status", "published")) for draft_record in drafts],
            writes=False,
        )
        return report_path, "audit blocked: provider is not allowlisted; no formal knowledge-base files written"

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
        config_identity=_config_identity(settings, structure),
        allowed_content_paths=allowed_content_paths,
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
    _update_digest_report(
        report_path, drafts, decisions, clusters, dry_run=False, llm_enabled=settings.llm_enabled
    )
    _write_similarity_audit(report_path, similarity_audit)
    _write_task0_runtime_audit(
        report_path,
        settings,
        similarity_audit,
        kb_dir=paths.kb_dir,
        config_identity=_config_identity(settings, structure),
        source_count=source_notes,
        page_statuses=[str(draft_record.get("page_status", "published")) for draft_record in drafts],
        writes=bool(writes),
    )
    effective_thresholds = similarity_audit["effective_thresholds"]
    summary = (
        f"audit committed: audited {source_notes} source note(s); roots={', '.join(roots)}; "
        f"top_k={settings.top_k}; high={effective_thresholds['high']:.2f}; "
        f"medium={effective_thresholds['medium']:.2f}; "
        f"page_match_threshold={effective_thresholds['page_match_threshold']:.2f}; "
        f"max_lines={settings.max_lines}; {len(writes)} formal output(s) committed"
    )
    return report_path, summary
