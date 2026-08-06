"""Small, resumable wrapper around the existing one-shot digest pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from .config import DigestSettings
from .errors import ValidationError
from .identity import source_id
from .ingest import ingest
from .jsonl import read_jsonl
from .kb_structure import DEFAULT_ROOTS, inspect_structure
from .paths import DigestPaths
from .pipeline import _run_similarity_stages, audit_run


_INGESTIBLE_SUFFIXES = {".md", ".txt", ".json"}
BATCH_STATE_SCHEMA_VERSION = 3
BATCH_WALL_CLOCK_SECONDS = 60 * 60
BATCH_MAX_PLANNED_GENERATOR_CALLS = 180


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_rows(paths: DigestPaths) -> list[dict[str, str]]:
    """Freeze the declared input set before S1 is allowed to process it."""
    declared: dict[str, dict[str, Any]] = {}
    declared_uris: dict[str, str] = {}
    for record in read_jsonl(paths.new_dir / "sources.jsonl"):
        raw_path = record.get("content_path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValidationError("manifest", "sources.jsonl", "content_path must be a non-empty string")
        content_path = raw_path.replace("\\", "/").removeprefix("items/")
        path = Path(content_path)
        if not content_path or path.is_absolute() or ".." in path.parts or "." in path.parts:
            raise ValidationError("manifest", raw_path, "content_path must stay inside new_dir/items")
        if content_path in declared:
            raise ValidationError("manifest", content_path, "source declaration is duplicated")
        source_uri = record.get("source_uri")
        if not isinstance(source_uri, str):
            source_uri = ""
        if source_uri and source_uri in declared_uris:
            raise ValidationError(
                "manifest",
                source_uri,
                f"source URI is declared for both {declared_uris[source_uri]} and {content_path}",
            )
        declared[content_path] = record
        if source_uri:
            declared_uris[source_uri] = content_path

    actual: dict[str, Path] = {}
    for path in sorted(paths.items_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in _INGESTIBLE_SUFFIXES:
            actual[path.relative_to(paths.items_dir).as_posix()] = path
    actual_paths = set(actual)
    declared_paths = set(declared)
    missing = sorted(actual_paths - declared_paths)
    extra = sorted(declared_paths - actual_paths)
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing declarations: {', '.join(missing)}")
        if extra:
            details.append(f"extra declarations: {', '.join(extra)}")
        raise ValidationError("manifest", paths.new_dir / "sources.jsonl", "; ".join(details))

    sources: list[dict[str, str]] = []
    for content_path, path in actual.items():
        record = declared[content_path]
        source_uri = str(record.get("source_uri") or "")
        identity = source_id(source_uri) if source_uri else f"invalid-{hashlib.sha256(content_path.encode('utf-8')).hexdigest()[:20]}"
        sources.append(
            {
                "content_path": content_path,
                "source_uri": source_uri,
                "source_id": identity,
                "content_fingerprint": _sha256_file(path),
            }
        )
    sources.sort(key=lambda row: (row["source_id"], row["content_path"]))
    return sources


def build_input_manifest(
    paths: DigestPaths,
    *,
    run_id: str,
    config_identity: str,
    snapshots: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
    allowed_content_paths: set[str] | None = None,
) -> dict[str, Any]:
    """Join the frozen input rows with the S1 facts for one run."""
    rows = [
        row for row in _source_rows(paths)
        if allowed_content_paths is None or row["content_path"] in allowed_content_paths
    ]
    snapshots_by_path: dict[str, dict[str, Any]] = {}
    for row in snapshots:
        raw_path = row.get("content_path") or row.get("input_path")
        if not raw_path:
            continue
        candidate = Path(str(raw_path))
        try:
            content_path = (
                candidate.relative_to(paths.items_dir).as_posix()
                if candidate.is_absolute()
                else candidate.as_posix().removeprefix("items/")
            )
        except ValueError as error:
            raise ValidationError("manifest", raw_path, "snapshot path is outside input items") from error
        snapshots_by_path[content_path] = row
    duplicates_by_path = {
        Path(str(row.get("path", ""))).relative_to(paths.items_dir).as_posix(): row
        for row in duplicates
        if row.get("path")
    }
    sources: list[dict[str, Any]] = []
    for row in rows:
        snapshot = snapshots_by_path.get(row["content_path"])
        if snapshot is None:
            raise ValidationError("manifest", row["content_path"], "source snapshot is missing")
        if snapshot.get("validation_status") not in {"failed", "degraded"} and snapshot.get("content_fingerprint") != row["content_fingerprint"]:
            raise ValidationError("manifest", row["content_path"], "snapshot fingerprint differs from input manifest")
        duplicate = duplicates_by_path.get(row["content_path"])
        fingerprint = snapshot.get("content_fingerprint") or row["content_fingerprint"]
        sources.append(
            {
                **row,
                "content_fingerprint": fingerprint,
                "snapshot_id": snapshot.get("snapshot_id"),
                "validated_at": snapshot.get("validated_at"),
                "validation_status": snapshot.get("validation_status"),
                "validation_reason": snapshot.get("validation_reason"),
                "duplicate_of": duplicate.get("duplicate_of") if duplicate else None,
                "canonical_source_uri": duplicate.get("canonical_source_uri") if duplicate else None,
                "canonical_source_id": duplicate.get("canonical_source_id") if duplicate else None,
            }
        )
    canonical = json.dumps(
        {"config_identity": config_identity, "sources": sources},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "schema_version": "input-manifest.v1",
        "run_id": run_id,
        "config_identity": config_identity,
        "manifest_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "sources": sources,
    }


def _manifest(paths: DigestPaths, batch_size: int) -> dict[str, Any]:
    if batch_size < 1:
        raise ValidationError("batch", "batch_size", "must be at least 1")
    sources = _source_rows(paths)
    canonical = json.dumps(sources, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    batches = [
        {
            "batch_id": f"batch-{index:03d}",
            "source_paths": [source["content_path"] for source in sources[start : start + batch_size]],
            "status": "pending",
            "attempt": 0,
            "split_from": None,
            "planned_calls": max(1, len(sources[start : start + batch_size])),
            "report_path": None,
            "error": None,
        }
        for index, start in enumerate(range(0, len(sources), batch_size), start=1)
    ]
    return {
        "schema_version": BATCH_STATE_SCHEMA_VERSION,
        "manifest_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "batch_size": batch_size,
        "sources": sources,
        "batches": batches,
    }


def _runtime_identity(paths: DigestPaths, settings: DigestSettings) -> dict[str, Any]:
    publication = inspect_structure(paths.structure_path).publication
    return {
        "llm_model": os.environ.get("KD_LLM_MODEL", "") if settings.llm_enabled else None,
        "llm_base_url": os.environ.get("KD_LLM_BASE_URL", "") if settings.llm_enabled else None,
        "llm_format": settings.llm_format if settings.llm_enabled else None,
        "similarity_backend": settings.similarity.backend,
        "embedding_model": settings.similarity.embedding.model if settings.similarity.embedding else None,
        "taxonomy_version": publication.taxonomy_version if publication else None,
        "publication_prompt_contract": "task2-publication-v1" if publication else None,
        "llm_batch_max_claims": settings.llm_batch_max_claims if settings.llm_enabled else None,
        "llm_batch_max_source_chars": settings.llm_batch_max_source_chars if settings.llm_enabled else None,
        "llm_summary_enabled": settings.llm_summary_enabled if settings.llm_enabled else None,
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValidationError("batch", path, f"unable to persist batch state: {error}") from error


def _failure_report_path(state_path: Path) -> Path:
    """Return the durable failure/cost report beside the caller-owned state."""
    return state_path.with_name(f"{state_path.name}.failure-report.json")


def _sync_budget_elapsed(budget: dict[str, Any], *, now: float | None = None) -> None:
    started_at = budget.get("started_at")
    if isinstance(started_at, (int, float)):
        budget["elapsed_seconds"] = round(max(0.0, (time.time() if now is None else now) - float(started_at)), 3)


def _cost_summary(state: dict[str, Any]) -> dict[str, Any]:
    budget = state.setdefault("budget", {})
    report_costs: list[dict[str, Any]] = []
    for batch in state.get("batches", []):
        report_path = batch.get("report_path")
        if not report_path:
            continue
        try:
            report = json.loads(Path(str(report_path)).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if report.get("dry_run") or not isinstance(report.get("cost"), dict):
            continue
        cost = report["cost"]
        if isinstance(cost.get("generator_calls"), int):
            report_costs.append(cost)
    observed_values = [cost.get("provider_calls_observed") for cost in report_costs]
    observed = sum(int(value) for value in observed_values) if report_costs and all(isinstance(value, int) for value in observed_values) else None
    reported_planned = [cost.get("planned_generator_calls") for cost in report_costs]
    planned = sum(int(value) for value in reported_planned) if report_costs and all(isinstance(value, int) for value in reported_planned) else None
    token_values = [cost.get("total_provider_tokens") for cost in report_costs]
    provider_tokens = sum(int(value) for value in token_values) if report_costs and all(isinstance(value, int) for value in token_values) else None
    generator_total = sum(int(cost["generator_calls"]) for cost in report_costs)
    fallback_weight = sum(
        float(cost["fallback_ratio"]) * int(cost["generator_calls"])
        for cost in report_costs
        if isinstance(cost.get("fallback_ratio"), (int, float))
    )
    fallback_total = (
        round(fallback_weight / generator_total, 6)
        if generator_total and len([cost for cost in report_costs if isinstance(cost.get("fallback_ratio"), (int, float))]) == len(report_costs)
        else None
    )
    reported_failed = sum(int(cost.get("failed_calls", 0)) for cost in report_costs if isinstance(cost.get("failed_calls", 0), int))
    failed_calls = max(int(budget.get("failed_calls", 0)), reported_failed)
    return {
        "schema_version": "batch-cost-summary.v1",
        "status": str(budget.get("run_status", "unknown")),
        "planned_generator_calls": budget.get("planned_generator_calls"),
        "planned_generator_calls_basis": budget.get("planned_generator_calls_basis"),
        "max_planned_generator_calls": budget.get("max_planned_generator_calls", BATCH_MAX_PLANNED_GENERATOR_CALLS),
        "planned_generator_report_path": budget.get("planned_generator_report_path"),
        "provider_calls_planned": planned,
        "provider_calls_planned_basis": "sum of committed audit reports" if planned is not None else "unknown until an audit report is returned",
        "provider_calls_reserved": int(budget.get("provider_calls", 0)),
        "provider_calls_observed": observed,
        "generator_calls": generator_total if report_costs else None,
        "failed_calls": failed_calls,
        "run_failures": int(budget.get("run_failures", 0)),
        "replay_calls": int(budget.get("replay_calls", 0)),
        "elapsed_seconds": budget.get("elapsed_seconds"),
        "provider_tokens": provider_tokens,
        "fallback_ratio": fallback_total if fallback_total is not None else budget.get("fallback_ratio"),
        "failed_batches": [
            str(batch.get("batch_id"))
            for batch in state.get("batches", [])
            if batch.get("status") == "failed"
        ],
    }


def _write_failure_report(state: dict[str, Any], state_path: Path) -> Path:
    """Persist provider failure/cost facts even when audit_run raises.

    ``audit_run`` intentionally fails closed before returning a report path on
    malformed provider output.  The batch state is still authoritative for
    recovery, so this sidecar makes the failure observable without pretending
    that a formal KB write succeeded.
    """
    budget = state.setdefault("budget", {})
    _sync_budget_elapsed(budget)
    report_path = _failure_report_path(state_path)
    _atomic_json(
        report_path,
        {
            "schema_version": "batch-failure-report.v1",
            "status": "failed" if any(batch.get("status") == "failed" for batch in state.get("batches", [])) else str(budget.get("run_status", "unknown")),
            "status_semantics": "historical_failure",
            "final_status": str(budget.get("run_status", "unknown")),
            "latest_run_status": str(budget.get("run_status", "unknown")),
            "resolved_by_replay": str(budget.get("run_status")) == "completed" and any(
                batch.get("split_from") and batch.get("status") == "succeeded"
                for batch in state.get("batches", [])
            ),
            "manifest_sha256": state.get("manifest_sha256"),
            "runtime_identity": state.get("runtime_identity", {}),
            "budget": {
                "planned_generator_calls": budget.get("planned_generator_calls"),
                "planned_generator_calls_basis": budget.get("planned_generator_calls_basis"),
                "max_planned_generator_calls": budget.get("max_planned_generator_calls", BATCH_MAX_PLANNED_GENERATOR_CALLS),
                "planned_generator_report_path": budget.get("planned_generator_report_path"),
                "provider_calls_planned": None,
                "provider_calls_planned_basis": "unknown until an audit report is returned",
                "provider_calls_reserved": int(budget.get("provider_calls", 0)),
                "provider_calls_observed": None,
                "failed_calls": int(budget.get("failed_calls", 0)),
                "run_failures": int(budget.get("run_failures", 0)),
                "replay_calls": int(budget.get("replay_calls", 0)),
                "elapsed_seconds": budget.get("elapsed_seconds"),
                "fallback_ratio": budget.get("fallback_ratio"),
                "run_status": budget.get("run_status"),
                "pause_reason": budget.get("pause_reason"),
            },
            "batches": [
                {
                    "batch_id": batch.get("batch_id"),
                    "source_paths": batch.get("source_paths", []),
                    "status": batch.get("status"),
                    "attempt": int(batch.get("attempt", 0)),
                    "split_from": batch.get("split_from"),
                    "error": batch.get("error"),
                    "review_status": "needs-review" if batch.get("status") == "failed" else None,
                    "report_path": batch.get("report_path"),
                }
                for batch in state.get("batches", [])
            ],
        },
    )
    budget["failure_report_path"] = report_path.as_posix()
    state["cost_summary"] = _cost_summary(state)
    return report_path


def _run_report_paths(paths: DigestPaths) -> set[Path]:
    runs = paths.kb_dir / "_digest" / "runs"
    return {path for path in runs.glob("*/report.json") if path.is_file()} if runs.is_dir() else set()


def _update_failed_run_report(
    report_path: Path,
    *,
    batch: dict[str, Any],
    error: Exception,
    elapsed_ms: int,
) -> None:
    """Make the already-created audit report truthful after provider failure."""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return
    provider_failure = getattr(error, "stage", "") == "llm"
    report["official_write"] = {
        **(report.get("official_write") if isinstance(report.get("official_write"), dict) else {}),
        "allow_official_write": False,
        "status": "failed_provider" if provider_failure else "failed",
    }
    report["failure"] = {
        "stage": getattr(error, "stage", "unknown"),
        "failed_input": getattr(error, "failed_input", ",".join(str(path) for path in batch.get("source_paths", []))),
        "reason": getattr(error, "reason", str(error)),
        "exception_type": type(error).__name__,
        "batch_id": batch.get("batch_id"),
        "source_paths": list(batch.get("source_paths", [])),
        "review_status": "needs-review",
    }
    report["timing"] = {"elapsed_ms": elapsed_ms, "elapsed_seconds": round(elapsed_ms / 1000, 3)}
    report["replay"] = {
        "status": "pending",
        "failed_batch_id": batch.get("batch_id"),
        "successful_batches_skipped": True,
    }
    report["fallback"] = {
        "used": False,
        "reason": "provider failure; no formal write",
    }
    report["cost"] = {
        "provider_calls_planned": None,
        "provider_calls_planned_basis": "unknown; audit failed before generator plan was returned",
        "provider_calls_reserved": int(batch.get("planned_calls", 1)),
        "provider_calls_observed": None,
        "failed_calls": 1 if provider_failure else 0,
        "run_failures": 1,
        "replay_calls": max(0, int(batch.get("attempt", 1)) - 1),
        "elapsed_ms": elapsed_ms,
        "elapsed_seconds": round(elapsed_ms / 1000, 3),
        "provider_tokens": None,
        "fallback_ratio": None,
    }
    _atomic_json(report_path, report)


def _load_or_create_state(
    paths: DigestPaths,
    state_path: Path,
    batch_size: int | None,
    settings: DigestSettings,
    *,
    resume: bool,
) -> dict[str, Any]:
    if state_path.exists():
        if not resume:
            raise ValidationError("batch", state_path, "batch state already exists; pass --resume or choose a new state path")
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("batch", state_path, f"invalid batch state ({error})") from error
        if not isinstance(state, dict) or state.get("schema_version") != BATCH_STATE_SCHEMA_VERSION:
            raise ValidationError("batch", state_path, "unsupported batch state")
        expected_size = int(state.get("batch_size", 0))
        if batch_size is not None and batch_size != expected_size:
            raise ValidationError("batch", state_path, "batch size differs from the fixed manifest")
        actual = _manifest(paths, expected_size)
        if actual["manifest_sha256"] != state.get("manifest_sha256") or actual["sources"] != state.get("sources"):
            raise ValidationError("batch", state_path, "source manifest changed; start a new batch state")
        if state.get("runtime_identity") != _runtime_identity(paths, settings):
            raise ValidationError("batch", state_path, "runtime identity changed; start a new batch state")
        return state
    if resume:
        raise ValidationError("batch", state_path, "cannot resume because batch state is missing")
    if batch_size is None:
        raise ValidationError("batch", state_path, "--batch-size is required when creating batch state")
    state = _manifest(paths, batch_size)
    state["runtime_identity"] = _runtime_identity(paths, settings)
    state["budget"] = {
        "max_wall_seconds": BATCH_WALL_CLOCK_SECONDS,
        "started_at": None,
        "started_monotonic": None,
        "provider_calls": 0,
        "max_provider_calls": max(1, len(state["sources"]) * 4),
        "failed_calls": 0,
        "run_failures": 0,
        "replay_calls": 0,
        "elapsed_seconds": 0.0,
        "fallback_ratio": None,
        "run_status": "pending",
        "pause_reason": None,
    }
    _atomic_json(state_path, state)
    return state


def _global_plan(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    """Calculate topic membership and duplicate ownership from the full manifest."""
    with tempfile.TemporaryDirectory(prefix="knowledge-digest-batch-plan-") as temporary:
        planning_dir = Path(temporary)
        raw_items = ingest(paths, planning_dir, persist_snapshot=False)
        clusters, _decisions, _similarity = _run_similarity_stages(
            raw_items, planning_dir, paths, roots, settings
        )
        duplicates: dict[str, dict[str, str]] = {}
        for record in read_jsonl(planning_dir / "s1" / "duplicates.jsonl"):
            source_path = Path(str(record["path"]))
            try:
                content_path = source_path.relative_to(paths.items_dir).as_posix()
            except ValueError as error:
                raise ValidationError("batch", source_path, "duplicate path is outside input items") from error
            duplicates[content_path] = {
                "duplicate_of": str(record["duplicate_of"]),
                "canonical_source_uri": str(record["canonical_source_uri"]),
                "canonical_source_id": str(record["canonical_source_id"]),
            }
    return clusters, duplicates


def _plan_sha256(cluster_plan: list[dict[str, Any]], global_duplicates: dict[str, dict[str, str]]) -> str:
    payload = json.dumps(
        {"cluster_plan": cluster_plan, "global_duplicates": global_duplicates},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _fixed_plan(
    state: dict[str, Any],
    state_path: Path,
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...],
    *,
    resume: bool,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    """Persist the full-run plan before any batch can commit output."""
    persisted_clusters = state.get("cluster_plan")
    persisted_duplicates = state.get("global_duplicates")
    persisted_hash = state.get("plan_sha256")
    if persisted_clusters is None and persisted_duplicates is None and persisted_hash is None:
        if resume:
            raise ValidationError("batch", state_path, "fixed topic plan is missing; start a new batch state")
        cluster_plan, global_duplicates = _global_plan(paths, settings, roots)
        state["cluster_plan"] = cluster_plan
        state["global_duplicates"] = global_duplicates
        state["plan_sha256"] = _plan_sha256(cluster_plan, global_duplicates)
        _atomic_json(state_path, state)
        return cluster_plan, global_duplicates
    if (
        not isinstance(persisted_clusters, list)
        or not isinstance(persisted_duplicates, dict)
        or not isinstance(persisted_hash, str)
        or _plan_sha256(persisted_clusters, persisted_duplicates) != persisted_hash
    ):
        raise ValidationError("batch", state_path, "fixed topic plan is invalid")
    return persisted_clusters, persisted_duplicates


def _planned_generator_calls(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...],
    source_paths: set[str],
    cluster_plan: list[dict[str, Any]],
    global_duplicates: dict[str, dict[str, str]],
) -> tuple[int, Path]:
    """Run the provider-free planner and return its generator-call ceiling."""
    report_path, _summary = audit_run(
        paths,
        settings,
        roots,
        dry_run=True,
        allowed_content_paths=source_paths,
        cluster_plan=cluster_plan,
        global_duplicates=global_duplicates,
    )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        planned = report.get("cost", {}).get("planned_generator_calls")
        if not isinstance(planned, int) or planned < 0:
            raise ValueError("planned_generator_calls is missing or invalid")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValidationError("batch", report_path, f"dry-run planned-call report is invalid ({error})") from error
    return planned, report_path


def run_batched(
    paths: DigestPaths,
    settings: DigestSettings,
    *,
    batch_size: int | None,
    state_path: Path,
    roots: tuple[str, ...] = DEFAULT_ROOTS,
    dry_run: bool = False,
    resume: bool = False,
) -> tuple[Path, str]:
    """Run only failed/pending batches against an immutable input manifest."""
    if dry_run:
        raise ValidationError("batch", "dry_run", "batch recovery requires a real run")
    from .topic_axis import read_topic_axis_settings

    if read_topic_axis_settings(paths.structure_path)["enabled"]:
        raise ValidationError(
            "batch",
            paths.structure_path,
            "Task1 topic-axis runs use one fixed manifest; batch mode is not supported",
        )
    state = _load_or_create_state(paths, state_path, batch_size, settings, resume=resume)
    budget = state.setdefault(
        "budget",
        {
            "max_wall_seconds": BATCH_WALL_CLOCK_SECONDS,
            "started_at": None,
            "started_monotonic": None,
            "provider_calls": 0,
            "max_provider_calls": max(1, len(state.get("sources", [])) * 4),
            "failed_calls": 0,
            "run_failures": 0,
            "replay_calls": 0,
            "elapsed_seconds": 0.0,
            "fallback_ratio": None,
            "run_status": "pending",
            "pause_reason": None,
        },
    )
    for key, default in (
        ("failed_calls", 0),
        ("run_failures", 0),
        ("replay_calls", 0),
        ("elapsed_seconds", 0.0),
        ("fallback_ratio", None),
    ):
        budget.setdefault(key, default)
    started_at = time.time()
    if budget.get("started_at") is None:
        budget["started_at"] = started_at
    if budget.get("started_monotonic") is None:
        # Retain the v3 field for readable state compatibility; elapsed checks
        # use the persisted wall-clock timestamp above so resume is bounded.
        budget["started_monotonic"] = budget["started_at"]
        budget["run_status"] = "running"
        _atomic_json(state_path, state)
    publication = inspect_structure(paths.structure_path).publication
    split_mode = bool(publication and len(publication.categories) > 1)
    cluster_plan, global_duplicates = _fixed_plan(
        state, state_path, paths, settings, roots, resume=resume
    )
    if settings.llm_enabled:
        # Do not even run a provider-free planner when a resumed state has
        # already exhausted its caller-owned reservation budget.
        if int(budget.get("provider_calls", 0)) >= int(
            budget.get("max_provider_calls", max(1, len(state.get("sources", [])) * 4))
        ):
            budget["run_status"] = "paused"
            budget["pause_reason"] = "provider call budget exceeded"
            state["cost_summary"] = _cost_summary(state)
            _atomic_json(state_path, state)
            _write_failure_report(state, state_path)
            _atomic_json(state_path, state)
            raise ValidationError("batch", state_path, "provider call budget exceeded")
        planned = budget.get("planned_generator_calls")
        preflight_report_path = budget.get("planned_generator_report_path")
        if planned is None:
            planned, preflight_report = _planned_generator_calls(
                paths,
                settings,
                roots,
                {str(source["content_path"]) for source in state.get("sources", [])},
                cluster_plan,
                global_duplicates,
            )
            budget["planned_generator_calls"] = planned
            budget["planned_generator_calls_basis"] = "full-manifest dry-run"
            budget["planned_generator_report_path"] = preflight_report.as_posix()
            preflight_report_path = preflight_report.as_posix()
            _atomic_json(state_path, state)
        if int(planned) > BATCH_MAX_PLANNED_GENERATOR_CALLS:
            budget["run_status"] = "paused"
            budget["pause_reason"] = "planned generator calls exceed 180"
            budget["max_planned_generator_calls"] = BATCH_MAX_PLANNED_GENERATOR_CALLS
            state["cost_summary"] = _cost_summary(state)
            _atomic_json(state_path, state)
            _write_failure_report(state, state_path)
            _atomic_json(state_path, state)
            raise ValidationError(
                "batch",
                preflight_report_path or state_path,
                f"planned generator calls exceed {BATCH_MAX_PLANNED_GENERATOR_CALLS}; no provider request was sent",
            )
    last_report: Path | None = None
    index = 0
    while index < len(state["batches"]):
        batch = state["batches"][index]
        index += 1
        if batch.get("status") == "succeeded":
            continue
        if time.time() - float(budget.get("started_at", started_at)) > float(
            budget.get("max_wall_seconds", BATCH_WALL_CLOCK_SECONDS)
        ):
            budget["run_status"] = "paused"
            budget["pause_reason"] = "wall-clock budget exceeded"
            state["cost_summary"] = _cost_summary(state)
            _atomic_json(state_path, state)
            _write_failure_report(state, state_path)
            _atomic_json(state_path, state)
            raise ValidationError("batch", state_path, "60 minute wall-clock budget exceeded")
        planned_calls = int(batch.get("planned_calls", 1))
        if settings.llm_enabled and int(budget.get("provider_calls", 0)) + planned_calls > int(
            budget.get("max_provider_calls", max(1, len(state.get("sources", [])) * 4))
        ):
            budget["run_status"] = "paused"
            budget["pause_reason"] = "provider call budget exceeded"
            state["cost_summary"] = _cost_summary(state)
            _atomic_json(state_path, state)
            _write_failure_report(state, state_path)
            _atomic_json(state_path, state)
            raise ValidationError("batch", state_path, "provider call budget exceeded")
        if settings.llm_enabled:
            budget["provider_calls"] = int(budget.get("provider_calls", 0)) + planned_calls
            _atomic_json(state_path, state)
        batch["status"] = "running"
        is_replay = int(batch.get("attempt", 0)) > 0 or bool(batch.get("split_from"))
        batch["attempt"] = int(batch.get("attempt", 0)) + 1
        batch["error"] = None
        if is_replay:
            budget["replay_calls"] = int(budget.get("replay_calls", 0)) + 1
        _atomic_json(state_path, state)
        reports_before = _run_report_paths(paths)
        attempt_started = time.time()
        try:
            report, _summary = audit_run(
                paths,
                settings,
                roots,
                dry_run=False,
                allowed_content_paths=set(batch["source_paths"]),
                cluster_plan=cluster_plan,
                global_duplicates=global_duplicates,
            )
        except Exception as error:
            elapsed_ms = int(round(max(0.0, time.time() - attempt_started) * 1000))
            batch["status"] = "failed"
            batch["error"] = f"{type(error).__name__}: {error}"
            batch["elapsed_ms"] = elapsed_ms
            budget["run_status"] = "failed"
            budget["run_failures"] = int(budget.get("run_failures", 0)) + 1
            if settings.llm_enabled and getattr(error, "stage", "") == "llm":
                budget["failed_calls"] = int(budget.get("failed_calls", 0)) + 1
            _sync_budget_elapsed(budget)
            state["cost_summary"] = _cost_summary(state)
            _atomic_json(state_path, state)
            new_reports = sorted(_run_report_paths(paths) - reports_before)
            if new_reports:
                batch["report_path"] = new_reports[-1].as_posix()
                _update_failed_run_report(
                    new_reports[-1],
                    batch=batch,
                    error=error,
                    elapsed_ms=elapsed_ms,
                )
                _atomic_json(state_path, state)
            _write_failure_report(state, state_path)
            _atomic_json(state_path, state)
            if split_mode and len(batch.get("source_paths", [])) > 1 and not batch.get("split_done"):
                batch["split_done"] = True
                children = [
                    {
                        "batch_id": f"{batch['batch_id']}-split-{split_index:03d}",
                        "source_paths": [source_path],
                        "status": "pending",
                        "attempt": 0,
                        "split_from": batch["batch_id"],
                        "planned_calls": 1,
                        "report_path": None,
                        "error": None,
                    }
                    for split_index, source_path in enumerate(batch["source_paths"], start=1)
                ]
                state["batches"][index:index] = children
                budget["run_status"] = "running"
                _atomic_json(state_path, state)
                continue
            raise
        batch["status"] = "succeeded"
        batch["report_path"] = report.as_posix()
        last_report = report
        _atomic_json(state_path, state)
    if last_report is None:
        reports = [batch.get("report_path") for batch in state["batches"] if batch.get("report_path")]
        if not reports:
            raise ValidationError("batch", state_path, "batch manifest contains no source files")
        last_report = Path(str(reports[-1]))
    budget["run_status"] = "completed"
    budget["pause_reason"] = None
    _sync_budget_elapsed(budget)
    state["cost_summary"] = _cost_summary(state)
    _atomic_json(state_path, state)
    if budget.get("failure_report_path"):
        _write_failure_report(state, state_path)
        _atomic_json(state_path, state)
    return last_report, f"batch audit committed: {len(state['batches'])} batch(es) succeeded; state={state_path}"
