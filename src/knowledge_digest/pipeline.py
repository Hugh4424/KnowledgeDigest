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
from typing import Any, Mapping
from uuid import uuid4

from .cluster import cluster
from .config import DigestSettings, RISK_RULE_VERSION
from .draft import draft
from .errors import ValidationError
from .embedding import EmbeddingError, normalize_endpoint_identity, resolve_similarity_backend
from .ingest import ingest
from .llm import (
    PUBLICATION_LLM_BASE_URL,
    PUBLICATION_LLM_MODEL,
    validate_section_response,
)
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
from .identity import source_id, topic_id
from .faithfulness import claim_entity_key
from .lock import kb_lock
from .paths import DigestPaths, is_new_kb_container
from .provenance import (
    archive_claim_records,
    audit_provenance,
    validate_prewrite_provenance,
)
from .page_layout import (
    build_publication_navigation,
    build_semantic_parts,
    build_topic_layouts,
    declared_managed_topics,
    evaluate_section_impact,
    protect_old_page_on_failure,
    validate_semantic_parts,
)
from .navigation import build_topic_part_navigation
from .publication import validate_body_gate
from .queues import write_queues
from .retrieve import retrieve
from .text_similarity import EmbeddingScorer, JaccardScorer
from .writeback import targets_for_draft, writeback
from .topic_axis import read_topic_axis_settings, run_topic_axis


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


def _existing_reader_page(
    paths: DigestPaths,
    draft_record: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return the current managed Reader page for compiler failure protection.

    The compiler must receive the last formal page before attempting a new
    body.  Only paths already attached to the draft are considered; no page
    is discovered by scanning arbitrary KB files.
    """
    candidates: list[str] = []
    for value in [
        draft_record.get("published_path"),
        *(draft_record.get("target_paths") or []),
    ]:
        if isinstance(value, str) and value and value not in candidates:
            candidates.append(value)
    for raw_path in candidates:
        path = Path(raw_path)
        if path.is_absolute():
            try:
                path = path.relative_to(paths.kb_dir)
            except ValueError:
                continue
        if not path.parts or ".." in path.parts:
            continue
        candidate = paths.kb_dir / path
        if not candidate.is_file() or candidate.is_symlink():
            continue
        try:
            body = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        return {
            "status": "published",
            "reader_eligible": True,
            "body": body,
            "target_path": path.as_posix(),
        }
    return None


def _reader_record_is_eligible(record: Mapping[str, Any]) -> bool:
    """Allow writeback only when the compiler's Reader projection is safe."""
    if record.get("page_status") == "degraded" or record.get("provider_failure"):
        return False
    projection = record.get("reader_projection")
    if isinstance(projection, Mapping):
        return bool(projection.get("reader_eligible"))
    return bool(record.get("reader_eligible", True))


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
    raw_existing: dict[str, Any] | None = None
    if target.is_file():
        try:
            raw_existing = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("publication", target, f"topic-index cannot be read ({error})") from error
        if raw_existing.get("schema_version") == "2.0.0":
            # Task1 owns the semantic index.  The older reader pipeline must
            # not rebuild it from five legacy fields and silently erase axes.
            validated = validate_topic_index(raw_existing)
            encoded = json.dumps(validated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            run_target = run_dir / "s6" / "topic-index.json"
            run_target.parent.mkdir(parents=True, exist_ok=True)
            run_target.write_text(encoded, encoding="utf-8")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".tmp")
            temporary.write_text(encoded, encoding="utf-8")
            os.replace(temporary, target)
            return
    existing: dict[str, Any] = {"schema_version": "1.0.0", "topics": []}
    if raw_existing is not None:
        try:
            existing = validate_topic_index(raw_existing)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise ValidationError("publication", target, f"topic-index is invalid ({error})") from error
    # Convert the normalized migration view back to the old reader shape for
    # this legacy-only pipeline.  This preserves old path locks while keeping
    # the Task1 2.0.0 projection protected above.
    by_topic = {
        str(row["topic_id"]): {
            "topic_id": str(row["topic_id"]),
            "source_ids": sorted({str(item) for item in row.get("source_ids", row.get("source_members", [])) if item}),
            "category_id": str(row.get("category_id") or "pending"),
            "published_path": str(row.get("legacy_published_path") or row.get("published_path") or ""),
            "product_slug": row.get("product_slug"),
        }
        for row in existing["topics"]
    }
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
    legacy_value = {"schema_version": "1.0.0", "topics": sorted(by_topic.values(), key=lambda row: row["topic_id"])}
    validate_topic_index(legacy_value)
    encoded = json.dumps(legacy_value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
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
    write_jsonl(
        run_dir / "s4" / "section-dependency-records.jsonl",
        [
            {
                "topic_id": draft_record.get("topic_id"),
                "section_id": section_id,
                "dependency_record": record,
                "impact_result": draft_record.get("impact_result"),
            }
            for draft_record in drafts
            for section_id, record in (draft_record.get("section_dependency_records") or {}).items()
            if isinstance(record, Mapping)
        ],
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
    reader_topic_drafts = [record for record in topic_drafts if _reader_record_is_eligible(record)]
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
        reader_topic_drafts = [record for record in topic_drafts if _reader_record_is_eligible(record)]
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


def _typed_body_gate_payload(
    draft_record: Mapping[str, Any],
    typed_response: Mapping[str, Any],
    *,
    duplicate_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Render a deterministic gate input from typed sections and trusted claims."""
    evidence_claims = [
        dict(claim)
        for claim in draft_record.get("claims", [])
        if isinstance(claim, Mapping)
    ]
    claim_ids: dict[str, dict[str, Any]] = {}
    for claim in evidence_claims:
        claim_id = str(claim.get("claim_id") or claim.get("claim_fingerprint"))
        # Preserve the first source occurrence as the deterministic Reader
        # footnote representative; the full evidence list remains lossless.
        claim_ids.setdefault(claim_id, claim)
    sections = typed_response.get("sections", {})
    body_lines: list[str] = []
    section_states: list[dict[str, Any]] = []
    referenced: set[str] = set()
    typed_claim_ids: set[str] = set()
    if isinstance(sections, Mapping):
        for section_id, raw_section in sections.items():
            if not isinstance(raw_section, Mapping):
                continue
            body_lines.append(f"## {section_id}")
            body = str(raw_section.get("body", "")).strip()
            section_states.append(
                {
                    "section_id": str(section_id),
                    "page_type": str(draft_record.get("typed_page_draft", {}).get("page_type") or "")
                    if isinstance(draft_record.get("typed_page_draft"), Mapping)
                    else "",
                    "status": str(raw_section.get("status") or "documented"),
                    "body": body,
                    "claim_ids": list(raw_section.get("claim_ids", []))
                    if isinstance(raw_section.get("claim_ids", []), list)
                    else raw_section.get("claim_ids"),
                    "source_audit": dict(raw_section.get("source_audit"))
                    if isinstance(raw_section.get("source_audit"), Mapping)
                    else None,
                }
            )
            if body:
                body_lines.append(body)
            raw_ids = raw_section.get("claim_ids", [])
            if isinstance(raw_ids, list):
                for raw_id in raw_ids:
                    claim_id = str(raw_id)
                    claim = claim_ids.get(claim_id)
                    if claim is None:
                        continue
                    canonical_id = str(claim.get("claim_id") or claim.get("claim_fingerprint"))
                    referenced.add(canonical_id)
                    typed_claim_ids.add(canonical_id)
                    if f"[^{canonical_id}]" not in body:
                        body_lines.append(f"[^{canonical_id}]")
    for claim_id in sorted(referenced):
        claim = claim_ids[claim_id]
        body_lines.append(
            f"[^{claim_id}]: {claim.get('source_uri', '')}#{claim.get('fragment_locator', '')}"
        )
    # The complete evidence ledger intentionally keeps repeated identical
    # source occurrences (their fragment locators differ).  The Reader body
    # gate, however, addresses claims by the stable fingerprint because one
    # footnote cannot distinguish repeated occurrences.  Project each
    # referenced fingerprint once for that gate while leaving
    # ``evidence_claims`` untouched.
    body_claims = [claim_ids[claim_id] for claim_id in sorted(referenced)]
    source_fragments = (draft_record.get("typed_page_draft") or {}).get("source_fragments", [])
    evidence_body = "\n".join(
        str(fragment.get("text", ""))
        for fragment in source_fragments
        if isinstance(fragment, Mapping) and fragment.get("text")
    )
    payload = {
        "body": "\n".join(body_lines).strip(),
        "evidence_body": evidence_body,
        # Only claims that the reader-facing body actually states belong to
        # the body gate.  The complete source Claim ledger remains available
        # as evidence and on the draft record; forcing every source Claim into
        # the provider response made large, otherwise valid topics impossible
        # to compile without turning the Reader page back into an Evidence dump.
        "claims": body_claims,
        "evidence_claims": evidence_claims,
        "typed_claim_ids": sorted(typed_claim_ids),
        "section_states": section_states,
        "source_fragments": [
            dict(fragment)
            for fragment in source_fragments
            if isinstance(fragment, Mapping)
        ],
        "provider_status": "ok" if not draft_record.get("provider_failure") else "failed",
    }
    if isinstance(duplicate_context, Mapping):
        payload["duplicate_context"] = {
            "same_page": [
                str(value)
                for value in duplicate_context.get("same_page", [])
                if str(value).strip()
            ],
            "cross_page": [
                str(value)
                for value in duplicate_context.get("cross_page", [])
                if str(value).strip()
            ],
            "denominator": int(duplicate_context.get("denominator", 0)),
            "detector_version": str(
                duplicate_context.get("detector_version", "jaccard-5gram.v1")
            ),
            "seed": duplicate_context.get("seed"),
        }
    return payload


def _semantic_section_claim_owners(
    sections: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Assign each reader claim to one semantic part owner.

    A provider may legitimately cite one fact in more than one section.  The
    reader body keeps those references, while the semantic-part ledger needs a
    single owner so a claim is not counted as entering multiple parts.
    Preserve section order as the deterministic ownership rule.
    """
    owned_claim_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for section in sections:
        item = dict(section)
        claim_ids: list[str] = []
        for raw_claim_id in section.get("claim_ids", []):
            claim_id = str(raw_claim_id)
            if claim_id in owned_claim_ids:
                continue
            owned_claim_ids.add(claim_id)
            claim_ids.append(claim_id)
        item["claim_ids"] = claim_ids
        normalized.append(item)
    return normalized


def _previous_section_dependency_records(
    paths: DigestPaths,
    topic_id: str,
) -> list[dict[str, Any]]:
    runs = paths.kb_dir / "_digest" / "runs"
    if not runs.is_dir():
        return []
    candidates = sorted(
        (path for path in runs.glob("*/s4/final-layouts.jsonl") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        for record in read_jsonl(path):
            if str(record.get("topic_id", "")) != topic_id:
                continue
            rows = record.get("section_dependency_records")
            if isinstance(rows, Mapping):
                content_hashes = record.get("section_content_hashes", {})
                target_paths = record.get("section_target_paths", {})
                typed_sections: dict[str, Mapping[str, Any]] = {}
                for response in record.get("typed_responses", []) if isinstance(record.get("typed_responses"), list) else []:
                    if not isinstance(response, Mapping):
                        continue
                    for section_id, section in (response.get("sections") or {}).items():
                        if isinstance(section, Mapping):
                            typed_sections[str(section_id)] = section
                return [
                    {
                        "section_id": str(section_id),
                        "dependency_record": dict(value),
                        "signal_status": "verified",
                        **(
                            {"body": str(typed_sections[section_id].get("body", ""))}
                            if section_id in typed_sections
                            else {}
                        ),
                        **(
                            {"claim_ids": list(typed_sections[section_id].get("claim_ids", []))}
                            if section_id in typed_sections and isinstance(typed_sections[section_id].get("claim_ids"), list)
                            else {}
                        ),
                        **(
                            {"content_hash": str(content_hashes[section_id])}
                            if isinstance(content_hashes, Mapping) and content_hashes.get(section_id)
                            else {}
                        ),
                        **(
                            {"target_path": str(target_paths[section_id])}
                            if isinstance(target_paths, Mapping) and target_paths.get(section_id)
                            else {}
                        ),
                    }
                    for section_id, value in rows.items()
                    if isinstance(value, Mapping) and value.get("schema_version") == "section-dependency-record.v1"
                ]
    return []


def _reuse_unchanged_typed_sections(
    typed_response: Mapping[str, Any],
    old_sections: list[Mapping[str, Any]],
    reused_sections: list[str],
) -> dict[str, Any]:
    """Keep only proven unchanged section bodies from the prior Reader run."""
    old_by_id = {
        str(section.get("section_id")): section
        for section in old_sections
        if isinstance(section, Mapping) and section.get("section_id")
    }
    sections = {
        str(section_id): dict(section)
        for section_id, section in (typed_response.get("sections") or {}).items()
        if isinstance(section, Mapping)
    }
    for section_id in reused_sections:
        old = old_by_id.get(str(section_id))
        current = sections.get(str(section_id))
        if not old or not current or not str(old.get("body", "")).strip():
            continue
        current["body"] = str(old["body"])
        if isinstance(old.get("claim_ids"), list) and old["claim_ids"]:
            current["claim_ids"] = [str(value) for value in old["claim_ids"] if str(value).strip()]
        sections[str(section_id)] = current
    return {**dict(typed_response), "sections": sections}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.is_dir():
        return digest.hexdigest()
    for path in sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(_sha256_file(path).encode("ascii"))
    return digest.hexdigest()


def _task2b_sample_manifest() -> tuple[dict[str, Any], str | None, str | None]:
    relative = Path("quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json")
    candidates = [Path.cwd() / relative]
    manifest_path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if manifest_path is None:
        return {
            "path": relative.as_posix(),
            "sample_count": None,
            "sampling_seed": None,
            "required_categories": ["long_text", "table_image", "bilingual", "multi_source"],
            "covered_categories": [],
            "excluded_categories": [],
        }, None, None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "path": relative.as_posix(),
            "sample_count": None,
            "sampling_seed": None,
            "required_categories": ["long_text", "table_image", "bilingual", "multi_source"],
            "covered_categories": [],
            "excluded_categories": [],
        }, manifest_path.as_posix(), None
    sample = manifest.get("sample", {}) if isinstance(manifest, Mapping) else {}
    inventory = manifest.get("inventory_coverage", {}) if isinstance(manifest, Mapping) else {}
    features = inventory.get("observed_features", {}) if isinstance(inventory, Mapping) else {}
    seed_label = str(sample.get("seed", ""))
    seed_value = int(hashlib.sha256(seed_label.encode("utf-8")).hexdigest()[:8], 16) if seed_label else None
    covered = ["table_image", "bilingual", "multi_source"]
    excluded = [
        {
            "category": "long_text",
            "reason": "source manifest does not expose a long-document feature; no semantic coverage is claimed",
        }
    ]
    if features.get("long_document") not in {None, "not_exposed_by_current_inventory_schema"}:
        covered.append("long_text")
        excluded = []
    return {
        "path": relative.as_posix(),
        "content_hash": _sha256_file(manifest_path),
        "sample_count": sample.get("sample_size"),
        "sampling_seed": seed_value,
        "sampling_seed_label": seed_label,
        "required_categories": ["long_text", "table_image", "bilingual", "multi_source"],
        "covered_categories": covered,
        "excluded_categories": excluded,
        "source_count": sample.get("source_count", inventory.get("source_count")),
    }, manifest_path.as_posix(), manifest.get("sample", {}).get("source_run_sha256") if isinstance(manifest, Mapping) else None


_TASK2B_PAGE_TYPES = frozenset(
    {"product_overview", "module_or_capability", "procedure_or_rule"}
)


def _attach_task2b_topic_mapping(
    *,
    decisions: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    paths: DigestPaths,
) -> None:
    """Bind existing TopicIndex rows to the typed body compiler.

    Task 1 owns the persisted topic rows.  This adapter only projects the
    already-frozen row into the Task 2-B PageDraft seam; it never infers a
    procedure page from prose.  An explicit ``page_type`` is required for
    that third type, while the two Task 2-A branches keep their fixed mapping.
    """
    topic_index_path = paths.kb_dir / "_digest" / "topic-index.json"
    if not topic_index_path.is_file():
        return
    try:
        raw_index = json.loads(topic_index_path.read_text(encoding="utf-8"))
        topic_index = validate_topic_index(raw_index)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("publication", topic_index_path, f"topic-index cannot be read ({error})") from error

    rows = [row for row in topic_index.get("topics", []) if isinstance(row, Mapping)]
    by_cluster = {
        str(cluster.get("cluster_id")): cluster
        for cluster in clusters
        if isinstance(cluster, Mapping) and cluster.get("cluster_id")
    }
    by_raw_id = {str(item.get("raw_id")): item for item in raw_items if item.get("raw_id")}

    for decision in decisions:
        cluster = by_cluster.get(str(decision.get("cluster_id")))
        if cluster is None:
            continue
        member_ids = [str(member) for member in cluster.get("members", [])]
        source_ids = {
            str(by_raw_id[member].get("source_id") or source_id(str(by_raw_id[member].get("source_uri", ""))))
            for member in member_ids
            if member in by_raw_id
        }
        matches = [
            row for row in rows
            if source_ids and source_ids.issubset({str(value) for value in row.get("source_members", [])})
        ]
        if len(matches) != 1:
            continue
        row = dict(matches[0])
        explicit_page_type = str(row.get("page_type") or "").strip()
        if explicit_page_type:
            page_type = explicit_page_type if explicit_page_type in _TASK2B_PAGE_TYPES else None
            mapping_status = "mapped" if page_type else "unmapped"
        elif row.get("status") != "published":
            page_type = None
            mapping_status = "degraded"
        elif row.get("knowledge_type") == "products" and (
            row.get("module") is None
            or str(row.get("object_intent") or "").strip().casefold() in {"overview", "product overview"}
        ):
            page_type = "product_overview"
            mapping_status = "mapped"
        elif row.get("knowledge_type") == "products" and row.get("module") and row.get("object_intent"):
            page_type = "module_or_capability"
            mapping_status = "mapped"
        else:
            page_type = None
            mapping_status = "unmapped"

        topic_index_id = str(row.get("digest_topic_id") or row.get("topic_id") or row.get("topic_key") or "")
        stable_topic_id = str(decision.get("topic_id") or "")
        if not stable_topic_id and source_ids:
            stable_topic_id = topic_id(source_ids)
        if not stable_topic_id:
            mapping_status = "unmapped"
        title = str(row.get("title") or row.get("topic_key") or topic_index_id or stable_topic_id or "Untitled")
        decision["topic_id"] = stable_topic_id or topic_index_id or decision.get("topic_id")
        decision["topic_index"] = {
            **row,
            "topic_id": stable_topic_id or topic_index_id,
            "topic_index_id": topic_index_id or None,
            "title": title,
            "page_type": page_type,
            "mapping_status": mapping_status,
        }


_TASK2B_ANSWERABILITY_SUPPORT: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "positive-01": (("product_overview",), ("positioning", "use_cases")),
    "positive-02": (("product_overview",), ("positioning", "use_cases")),
    "positive-03": (
        ("product_overview", "module_or_capability", "procedure_or_rule"),
        ("entry", "entry_prerequisites", "prerequisites"),
    ),
    "positive-04": (("procedure_or_rule",), ("steps_rules",)),
    "positive-05": (("module_or_capability",), ("capabilities", "limitations")),
    "positive-06": (("procedure_or_rule",), ("exceptions",)),
    "positive-07": (
        ("product_overview", "module_or_capability", "procedure_or_rule"),
        ("sources",),
    ),
    "positive-08": (
        ("product_overview", "module_or_capability", "procedure_or_rule"),
        ("version",),
    ),
    "positive-09": (("module_or_capability",), ("relationships",)),
    "positive-10": (("module_or_capability",), ("capabilities", "limitations")),
    "positive-11": (
        ("module_or_capability", "procedure_or_rule"),
        ("entry_prerequisites", "prerequisites", "steps_rules"),
    ),
    "positive-12": (("module_or_capability",), ("capabilities", "limitations")),
    "positive-13": (
        ("product_overview", "module_or_capability", "procedure_or_rule"),
        ("version",),
    ),
    "positive-14": (("product_overview", "module_or_capability", "procedure_or_rule"), ()),
    "positive-15": (
        ("product_overview", "module_or_capability", "procedure_or_rule"),
        ("sources",),
    ),
    "positive-16": (("product_overview", "module_or_capability", "procedure_or_rule"), ()),
    "positive-17": (("product_overview", "module_or_capability", "procedure_or_rule"), ()),
}


def _task2b_answerability_subset(
    *,
    question_set: Mapping[str, Any],
    concepts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Derive machine first-hit facts from published typed sections.

    This is deliberately a structural machine oracle, not a reader-quality
    claim.  Human answerability remains outside Task 2-B and is disclosed in
    the evidence reason.
    """
    passing = [
        concept
        for concept in concepts
        if concept.get("status") == "machine-passing"
    ]
    questions: list[dict[str, Any]] = []
    for question in question_set.get("questions", []):
        if not isinstance(question, Mapping):
            continue
        question_id = str(question.get("question_id") or "")
        if str(question.get("polarity")) == "negative":
            questions.append(
                {
                    "question_id": question_id,
                    "polarity": "negative",
                    "answerable": False,
                    "first_hit": None,
                }
            )
            continue
        page_types, sections = _TASK2B_ANSWERABILITY_SUPPORT.get(
            question_id,
            (("product_overview", "module_or_capability", "procedure_or_rule"), ()),
        )
        first_hit = None
        for concept in passing:
            if concept.get("page_type") not in page_types:
                continue
            if sections and not set(sections).intersection(set(concept.get("section_ids", []))):
                continue
            if question_id == "positive-06" and concept.get("section_statuses", {}).get("exceptions") == "source_not_documented":
                # The fixed section exists, but the source did not document an
                # exception rule.  Do not turn that structural state into an
                # answer to the exception-specific question.
                continue
            first_hit = str(concept.get("concept_id") or "") or None
            if first_hit:
                break
        questions.append(
            {
                "question_id": question_id,
                "polarity": "positive",
                "answerable": first_hit is not None,
                "first_hit": first_hit,
            }
        )
    return {
        "id": str(question_set.get("question_set_id") or "task0-question-set-v1"),
        "content_hash": str(question_set.get("question_set_hash") or ""),
        "questions": questions,
        "method": "section-presence-v1",
        "reason": "machine first-hit from typed sections; this is not human reader review",
    }


def write_semantic_evidence_file(
    *,
    paths: DigestPaths,
    settings: DigestSettings,
    result: tuple[Path, str] | None,
    error: str | None = None,
) -> Path | None:
    """Persist a truthful, run-bound semantic evidence record when requested."""
    raw_path = os.environ.get("KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE", "").strip()
    if not raw_path:
        return None
    # The evidence path is an explicit output of the frozen sample run, not a
    # global switch for every library-level audit_run call.  T014 reuses the
    # same process environment for regression tests; bind the writer to the
    # declared sample input/KB so unrelated fixtures cannot try to overwrite
    # the one-shot evidence target.
    sample_input = os.environ.get("KNOWLEDGEDIGEST_TASK2B_SAMPLE_INPUT", "").strip()
    sample_kb = os.environ.get("KNOWLEDGEDIGEST_TASK2B_SAMPLE_KB", "").strip()
    if not sample_input or not sample_kb:
        return None
    if (
        Path(sample_input).expanduser().resolve() != paths.new_dir.resolve()
        or Path(sample_kb).expanduser().resolve() != paths.kb_dir.resolve()
    ):
        return None
    output_path = Path(raw_path).expanduser().resolve()
    if output_path.exists():
        reason = "semantic evidence target must not be a symlink" if output_path.is_symlink() else "semantic evidence target must not already exist"
        raise ValidationError("semantic", output_path, reason)
    report_path = result[0].resolve() if result else None
    run_id = report_path.parent.name if report_path else f"run-unavailable-{uuid4().hex}"
    sample_manifest, manifest_path, source_run_hash = _task2b_sample_manifest()
    input_fingerprint = _sha256_tree(paths.new_dir)
    kb_fingerprint = _sha256_tree(paths.kb_dir)
    run_dir = report_path.parent if report_path else None
    drafts = read_jsonl(run_dir / "s4" / "drafts.jsonl") if run_dir and (run_dir / "s4" / "drafts.jsonl").is_file() else []
    concepts: list[dict[str, Any]] = []
    evidence_backtrace: list[dict[str, Any]] = []
    section_completeness: list[dict[str, Any]] = []
    failure_reasons: list[str] = []
    for record in drafts:
        compiler_results = record.get("compiler_results")
        if isinstance(compiler_results, list):
            compiler_candidates = [item for item in compiler_results if isinstance(item, Mapping)]
        else:
            compiler_candidates = [record.get("compiler_result")]
        compiler = next(
            (
                item
                for item in compiler_candidates
                if isinstance(item, Mapping) and item.get("status") == "published"
            ),
            None,
        )
        if isinstance(compiler, Mapping) and compiler.get("status") == "published":
            topic_id = str(record.get("topic_id") or compiler.get("stable_topic_id") or "")
            candidate = compiler.get("candidate") or {}
            page_type = str(candidate.get("page_type") or "")
            concept_id = topic_id or str(record.get("draft_id", ""))
            sections = candidate.get("sections") or {}
            section_statuses = {
                str(section_id): str(section.get("status"))
                for section_id, section in sections.items()
                if isinstance(section, Mapping) and section.get("status")
            }
            concepts.append(
                {
                    "concept_id": concept_id,
                    "page_type": page_type,
                    "status": "machine-passing",
                    "section_ids": sorted(str(section_id) for section_id in sections),
                    "section_statuses": section_statuses,
                }
            )
            for claim in record.get("claims", []):
                if isinstance(claim, Mapping):
                    evidence_backtrace.append(
                        {
                            "concept_id": concept_id,
                            "claim_id": claim.get("claim_id") or claim.get("claim_fingerprint"),
                            "fragment_locator": claim.get("fragment_locator"),
                        }
                    )
            section_completeness.append(
                {
                    "concept_id": concept_id,
                    "sections": sorted(str(section_id) for section_id in sections),
                    "complete": bool(sections),
                }
            )
        elif record.get("provider_failure") or record.get("page_status") == "degraded":
            for failure in record.get("provider_failures", []):
                if isinstance(failure, Mapping) and failure.get("reason"):
                    failure_reasons.append(str(failure["reason"]))
    if error:
        failure_reasons.append(error)
    if not settings.llm_enabled:
        failure_reasons.append("semantic run did not use a provider; offline/Jaccard-only output is not semantic evidence")
    if not evidence_backtrace:
        failure_reasons.append("semantic evidence backtrace is unavailable")
    question_set_path = Path.cwd() / "config" / "task0-question-set.v1.json"
    question_set_hash = _sha256_file(question_set_path) if question_set_path.is_file() else None
    question_set: dict[str, Any] = {}
    if question_set_path.is_file():
        try:
            loaded_question_set = json.loads(question_set_path.read_text(encoding="utf-8"))
            if isinstance(loaded_question_set, Mapping):
                question_set = dict(loaded_question_set)
                question_set["question_set_hash"] = question_set_hash
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            question_set = {}
    cost = {}
    if run_dir is not None and (run_dir / "report.json").is_file():
        try:
            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            if isinstance(report, Mapping) and isinstance(report.get("cost"), Mapping):
                cost = dict(report["cost"])
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            cost = {}
    execution_mode = "real_semantic" if settings.llm_enabled else "jaccard_only"
    provider = {
        "provider": "qwen3.6" if settings.llm_enabled else "none",
        "model": os.environ.get("KD_LLM_MODEL") if settings.llm_enabled else None,
        "base_url": os.environ.get("KD_LLM_BASE_URL") if settings.llm_enabled else None,
        "credential": "environment-only",
    }
    evidence = {
        "schema_version": "task2b-semantic-evidence.v1",
        "run_id": run_id,
        "run_status": "completed" if not error and result else "incomplete",
        "execution_mode": execution_mode,
        "run_identity": {
            "run_id": run_id,
            "sample_fingerprint": sample_manifest.get("content_hash") or "missing",
            "kb_fingerprint": kb_fingerprint,
            "input_fingerprint": input_fingerprint,
            "source_run_hash": source_run_hash,
            "manifest_path": manifest_path,
        },
        "output_path": str(output_path),
        "delivery_status": "not_released",
        "sample_manifest": sample_manifest,
        "provider": provider,
        "detector": {
            "name": "task2b-publication-gate.v1",
            "version": "jaccard-5gram.v1",
        },
        "budget": {
            "provider_calls": cost.get("provider_calls_observed"),
            "provider_calls_planned": cost.get("provider_calls_planned"),
            "max_tokens": 8192,
            "source": "DigestSettings/current environment",
        },
        "threshold": {
            "answerability": 1.0,
            "section_completeness": 1.0,
            "max_body_lines": 120,
            "max_page_lines": 300,
        },
        "answerability_source": "task0-question-set.v1" if question_set_hash else "missing",
        "answerability_subset": _task2b_answerability_subset(
            question_set=question_set,
            concepts=concepts,
        ) if question_set else {
            "id": "not-computed",
            "content_hash": question_set_hash,
            "questions": [],
            "reason": "task0 question set is unavailable",
        },
        "concepts": concepts,
        "evidence_backtrace": evidence_backtrace,
        "section_completeness": section_completeness,
        "failure_reasons": sorted(set(failure_reasons)),
        "contract_revision": 1,
        "revision_ledger": [
            {"revision": 0, "reason": "initial accepted body contract"},
            {
                "revision": 1,
                "id": "SR-20260811-task2b-procedure-source-gap",
                "reason": "procedure_or_rule.exceptions source_not_documented section state",
            },
        ],
        "ac_bindings": {
            "AC-01": "structure-evidence",
            "AC-03": "claim-backtrace",
            "AC-05": "impact-closure",
            "AC-07": "status-navigation",
            "AC-09": "sample-coverage",
            "AC-10": "run-identity",
            "AC-11": "machine-bottom-line",
            "AC-12": "revision-ledger",
            "AC-13": "source-gap-section-state",
        },
    }
    _atomic_json(output_path, evidence)
    return output_path


def _compiler_failure(
    page_draft: Mapping[str, Any],
    reason: str,
    *,
    old_page: Mapping[str, Any] | None,
) -> dict[str, Any]:
    candidate = {
        "status": "degraded",
        "reader_eligible": False,
        "topic_id": page_draft.get("topic_id"),
        "page_type": page_draft.get("page_type"),
        "sections": {},
        "body": "",
        "reason": reason,
        "audit_record": {"destination": "Audit", "reason": reason},
    }
    if old_page is not None:
        protected = protect_old_page_on_failure(old_page, candidate)
        reader_projection = dict(protected["reader_projection"])
    else:
        reader_projection = {
            "status": "degraded",
            "reader_eligible": False,
            "body": "",
            "target_path": None,
        }
    return {
        "status": "degraded",
        "stable_topic_id": page_draft.get("topic_id"),
        "candidate": candidate,
        "reader_projection": reader_projection,
        "navigation_records": [],
        "audit_record": candidate["audit_record"],
    }


def compile_publication_candidate(
    *,
    page_draft: Mapping[str, Any],
    provider_payload: Any,
    body_gate_payload: Mapping[str, Any] | None = None,
    old_page: Mapping[str, Any] | None = None,
    frozen_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply the Task 2-B compiler gates at the formal pipeline boundary.

    This adapter is deliberately pure: it returns Reader/Audit projections for
    the existing single writer.  It never writes a page and never splices a
    failed candidate into an old Reader page.
    """
    if frozen_input is not None:
        if frozen_input.get("required") and not frozen_input.get("available"):
            return _compiler_failure(
                page_draft,
                "frozen input is missing",
                old_page=old_page,
            )
        expected = frozen_input.get("expected_fingerprint")
        actual = frozen_input.get("actual_fingerprint")
        if expected is not None and actual is not None and expected != actual:
            return _compiler_failure(
                page_draft,
                "frozen input fingerprint mismatch",
                old_page=old_page,
            )

    if page_draft.get("status") != "draft":
        audit = page_draft.get("audit_record")
        reason = str(audit.get("reason") if isinstance(audit, Mapping) else "page draft is not publishable")
        return _compiler_failure(page_draft, reason, old_page=old_page)

    validation_payload: Any = provider_payload
    if isinstance(provider_payload, Mapping) and provider_payload.get("_validated_typed_response") is True:
        # draft.py already validated this object. Strip only trusted internal
        # lineage fields before the second contract check; provider-originated
        # payloads never receive this marker because it is rejected above.
        validation_payload = {
            "page_type": provider_payload.get("page_type"),
            "sections": {
                str(section_id): {
                    "body": section.get("body", ""),
                    "claim_ids": list(section.get("claim_ids", [])),
                }
                for section_id, section in (provider_payload.get("sections") or {}).items()
                if isinstance(section, Mapping)
            },
        }
    typed = validate_section_response(page_draft, validation_payload)
    if typed.get("status") != "draft":
        return _compiler_failure(page_draft, str(typed.get("reason") or "typed section validation failed"), old_page=old_page)

    if body_gate_payload is None:
        return _compiler_failure(page_draft, "publication body gate input is missing", old_page=old_page)
    body_gate = validate_body_gate(body_gate_payload)
    if not body_gate.get("reader_eligible"):
        reason = "; ".join(str(item) for item in body_gate.get("reasons", [])) or "publication body gate rejected candidate"
        return _compiler_failure(page_draft, reason, old_page=old_page)

    sections = [
        dict(section, section_id=section_id)
        for section_id, section in typed.get("sections", {}).items()
        if isinstance(section, Mapping)
    ]
    sections = _semantic_section_claim_owners(sections)
    claims = [
        dict(claim)
        for claim in body_gate_payload.get("claims", [])
        if isinstance(claim, Mapping)
    ]
    semantic = build_semantic_parts(
        topic_id=str(page_draft.get("topic_id") or ""),
        title=str(page_draft.get("title") or page_draft.get("topic_id") or "Untitled"),
        page_type=str(page_draft.get("page_type") or ""),
        sections=sections,
        claims=claims,
    )
    semantic_check = validate_semantic_parts(semantic)
    if not semantic_check.get("valid"):
        reason = "; ".join(str(item) for item in semantic_check.get("reasons", [])) or "semantic parts failed validation"
        return _compiler_failure(page_draft, reason, old_page=old_page)

    navigation_records = build_topic_part_navigation(
        semantic["parts"],
        overview_path=str(semantic["overview"]["target_path"]),
        related_key=str(semantic["related_key"]),
    )
    candidate = {
        **typed,
        "status": "published",
        "reader_eligible": True,
        "body": body_gate["body"],
        "evidence_body": body_gate["evidence_body"],
        "claims": claims,
        "evidence": body_gate["evidence"],
        "semantic": semantic,
        "audit_record": None,
    }
    return {
        "status": "published",
        "stable_topic_id": page_draft.get("topic_id"),
        "candidate": candidate,
        "reader_projection": {
            "status": "published",
            "reader_eligible": True,
            "body": body_gate["body"],
            "target_path": semantic["overview"]["target_path"],
        },
        "navigation_records": navigation_records,
        "audit_record": None,
    }


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
        try:
            result = _audit_run_locked(
                paths,
                settings,
                roots,
                dry_run=dry_run,
                generator=generator,
                allowed_content_paths=allowed_content_paths,
                cluster_plan=cluster_plan,
                global_duplicates=global_duplicates,
            )
        except Exception as error:
            write_semantic_evidence_file(
                paths=paths,
                settings=settings,
                result=None,
                error=str(error),
            )
            raise
        write_semantic_evidence_file(paths=paths, settings=settings, result=result)
        return result


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
    topic_axis_settings = read_topic_axis_settings(paths.structure_path)
    if not dry_run and topic_axis_settings["enabled"]:
        # Task1 is an explicit opt-in structural run.  It writes only the
        # four rebuildable _digest projections and never enters the reader
        # publication pipeline.
        return run_topic_axis(paths, topic_root=topic_axis_settings.get("topic_root"))
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
    _attach_task2b_topic_mapping(
        decisions=decisions,
        clusters=clusters,
        raw_items=raw_items,
        paths=paths,
    )
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
    typed_duplicate_contexts: list[dict[str, Any]] = []
    for draft_record in drafts:
        typed_response = draft_record.get("typed_response")
        if not isinstance(typed_response, Mapping) or typed_response.get("status") != "draft":
            continue
        sections = typed_response.get("sections")
        if not isinstance(sections, Mapping):
            continue
        section_bodies = [
            str(section.get("body", ""))
            for section in sections.values()
            if isinstance(section, Mapping) and str(section.get("body", "")).strip()
        ]
        typed_duplicate_contexts.append(
            {
                "topic_id": str(draft_record.get("topic_id") or ""),
                "same_page": section_bodies,
                "body": "\n".join(section_bodies),
            }
        )
    for draft_record in drafts:
        typed_page_draft = draft_record.get("typed_page_draft")
        typed_response = draft_record.get("typed_response")
        if (
            not isinstance(typed_page_draft, Mapping)
            or not isinstance(typed_response, Mapping)
            or typed_response.get("status") != "draft"
        ):
            continue
        topic_id = str(draft_record.get("topic_id") or "")
        current_duplicate = next(
            (
                item
                for item in typed_duplicate_contexts
                if item.get("topic_id") == topic_id
            ),
            {"same_page": [], "body": ""},
        )
        body_gate_payload = _typed_body_gate_payload(
            draft_record,
            typed_response,
            duplicate_context={
                "same_page": current_duplicate.get("same_page", []),
                "cross_page": [
                    str(item.get("body", ""))
                    for item in typed_duplicate_contexts
                    if item is not current_duplicate and str(item.get("body", "")).strip()
                ],
                "denominator": sum(
                    len(item.get("same_page", []))
                    + (1 if str(item.get("body", "")).strip() else 0)
                    for item in typed_duplicate_contexts
                ),
                "detector_version": "jaccard-5gram.v1",
                "seed": 0,
            },
        )
        target_path = str(
            draft_record.get("published_path")
            or (draft_record.get("target_paths") or [""])[0]
        )
        new_dependency_sections = [
            {
                "section_id": str(section_id),
                "dependency_record": dict(section.get("dependency_record")),
                "signal_status": "verified",
                "body": str(section.get("body", "")),
                "content_hash": hashlib.sha256(str(section.get("body", "")).encode("utf-8")).hexdigest(),
                **({"target_path": target_path} if target_path else {}),
            }
            for section_id, section in (typed_response.get("sections") or {}).items()
            if isinstance(section, Mapping) and isinstance(section.get("dependency_record"), Mapping)
        ]
        old_dependency_sections = _previous_section_dependency_records(
            paths,
            str(draft_record.get("topic_id") or typed_page_draft.get("topic_id") or ""),
        )
        impact_result = (
            evaluate_section_impact(old_dependency_sections, new_dependency_sections)
            if old_dependency_sections
            else {
                "status": "initial",
                "uncertain": False,
                "recompile_scope": "page",
                "affected_sections": sorted(row["section_id"] for row in new_dependency_sections),
                "reused_sections": [],
                "safe_reuse_proof": {},
                "old_signal_invalidated": [],
                "reason": "no prior section dependency record",
            }
        )
        if not impact_result.get("uncertain") and impact_result.get("reused_sections"):
            typed_response = _reuse_unchanged_typed_sections(
                typed_response,
                old_dependency_sections,
                [str(section_id) for section_id in impact_result["reused_sections"]],
            )
            body_gate_payload = _typed_body_gate_payload(
                draft_record,
                typed_response,
                duplicate_context=body_gate_payload.get("duplicate_context"),
            )
        old_page = _existing_reader_page(paths, draft_record)
        compiler_result = compile_publication_candidate(
            page_draft=typed_page_draft,
            provider_payload=typed_response,
            body_gate_payload=body_gate_payload,
            old_page=old_page,
        )
        draft_record["typed_response"] = dict(typed_response)
        draft_record["compiler_result"] = compiler_result
        draft_record["reader_projection"] = dict(compiler_result.get("reader_projection") or {})
        draft_record["page_status"] = compiler_result["status"]
        draft_record["reader_eligible"] = bool(compiler_result["candidate"].get("reader_eligible"))
        draft_record["section_dependency_records"] = {
            str(section_id): dict(section.get("dependency_record"))
            for section_id, section in (typed_response.get("sections") or {}).items()
            if isinstance(section, Mapping) and isinstance(section.get("dependency_record"), Mapping)
        }
        draft_record["section_content_hashes"] = {
            str(section_id): hashlib.sha256(str(section.get("body", "")).encode("utf-8")).hexdigest()
            for section_id, section in (typed_response.get("sections") or {}).items()
            if isinstance(section, Mapping)
        }
        target_path = str(
            draft_record.get("published_path")
            or (draft_record.get("target_paths") or [""])[0]
        )
        draft_record["section_target_paths"] = {
            str(section_id): target_path
            for section_id in draft_record["section_dependency_records"]
            if target_path
        }
        new_dependency_sections = [
            {
                "section_id": str(section_id),
                "dependency_record": dict(record),
                "signal_status": "verified",
                "content_hash": draft_record["section_content_hashes"].get(str(section_id)),
                **({"target_path": target_path} if target_path else {}),
            }
            for section_id, record in draft_record["section_dependency_records"].items()
        ]
        old_dependency_sections = _previous_section_dependency_records(
            paths,
            str(draft_record.get("topic_id") or typed_page_draft.get("topic_id") or ""),
        )
        draft_record["impact_result"] = (
            evaluate_section_impact(old_dependency_sections, new_dependency_sections)
            if old_dependency_sections
            else {
                "status": "initial",
                "uncertain": False,
                "recompile_scope": "page",
                "affected_sections": sorted(row["section_id"] for row in new_dependency_sections),
                "reused_sections": [],
                "safe_reuse_proof": {},
                "old_signal_invalidated": [],
                "reason": "no prior section dependency record",
            }
        )
        if compiler_result["status"] == "published":
            draft_record["final_body"] = str(compiler_result["candidate"].get("body", draft_record.get("final_body", "")))
        else:
            draft_record["provider_failure"] = True
            failure = {
                "kind": "publication_compiler",
                "stage": "publication",
                "reason": str(compiler_result["audit_record"].get("reason", "publication compiler rejected candidate")),
            }
            draft_record.setdefault("provider_failures", []).append(failure)
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
