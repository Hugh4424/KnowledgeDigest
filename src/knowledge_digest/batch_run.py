"""Small, resumable wrapper around the existing one-shot digest pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .config import DigestSettings
from .errors import ValidationError
from .identity import source_id
from .ingest import ingest
from .jsonl import read_jsonl
from .kb_structure import DEFAULT_ROOTS
from .paths import DigestPaths
from .pipeline import _run_similarity_stages, audit_run


_INGESTIBLE_SUFFIXES = {".md", ".txt", ".json"}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _declared_sources(new_dir: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(new_dir / "sources.jsonl"):
        content_path = record.get("content_path")
        if isinstance(content_path, str) and content_path:
            result[content_path.replace("\\", "/").removeprefix("items/")] = record
    return result


def _manifest(paths: DigestPaths, batch_size: int) -> dict[str, Any]:
    if batch_size < 1:
        raise ValidationError("batch", "batch_size", "must be at least 1")
    declared = _declared_sources(paths.new_dir)
    sources: list[dict[str, str]] = []
    for path in sorted(paths.items_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _INGESTIBLE_SUFFIXES:
            continue
        content_path = path.relative_to(paths.items_dir).as_posix()
        source_uri = str(declared.get(content_path, {}).get("source_uri", ""))
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
    canonical = json.dumps(sources, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    batches = [
        {
            "batch_id": f"batch-{index:03d}",
            "source_paths": [source["content_path"] for source in sources[start : start + batch_size]],
            "status": "pending",
            "report_path": None,
            "error": None,
        }
        for index, start in enumerate(range(0, len(sources), batch_size), start=1)
    ]
    return {
        "schema_version": 2,
        "manifest_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "batch_size": batch_size,
        "sources": sources,
        "batches": batches,
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


def _load_or_create_state(
    paths: DigestPaths,
    state_path: Path,
    batch_size: int | None,
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
        if not isinstance(state, dict) or state.get("schema_version") != 2:
            raise ValidationError("batch", state_path, "unsupported batch state")
        expected_size = int(state.get("batch_size", 0))
        if batch_size is not None and batch_size != expected_size:
            raise ValidationError("batch", state_path, "batch size differs from the fixed manifest")
        actual = _manifest(paths, expected_size)
        if actual["manifest_sha256"] != state.get("manifest_sha256") or actual["sources"] != state.get("sources"):
            raise ValidationError("batch", state_path, "source manifest changed; start a new batch state")
        return state
    if resume:
        raise ValidationError("batch", state_path, "cannot resume because batch state is missing")
    if batch_size is None:
        raise ValidationError("batch", state_path, "--batch-size is required when creating batch state")
    state = _manifest(paths, batch_size)
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
    state = _load_or_create_state(paths, state_path, batch_size, resume=resume)
    cluster_plan, global_duplicates = _fixed_plan(
        state, state_path, paths, settings, roots, resume=resume
    )
    last_report: Path | None = None
    for batch in state["batches"]:
        if batch.get("status") == "succeeded":
            continue
        batch["status"] = "running"
        batch["error"] = None
        _atomic_json(state_path, state)
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
            batch["status"] = "failed"
            batch["error"] = f"{type(error).__name__}: {error}"
            _atomic_json(state_path, state)
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
    return last_report, f"batch audit committed: {len(state['batches'])} batch(es) succeeded; state={state_path}"
