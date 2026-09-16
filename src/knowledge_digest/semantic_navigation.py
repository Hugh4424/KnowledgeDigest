"""Batch-local Task8 navigation compiler and its fail-closed commit boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Mapping, Sequence

# This module is the stable façade; deterministic support moved here when the
# compiler crossed the frozen size boundary.
from .semantic_nav_check import (
    _safe_batch_path,
    ConfiguredNavigationGateway, JsonlNavigationCache, MANIFEST_SCHEMA_VERSION, MountEntry,
    NAVIGATION_GENERATED_BY, NavigationDependencies, NavigationDocument, NavigationInputError,
    NavigationResult, REJECTION_WORDS, ReconciledPage, build_index, build_home, build_module_indexes,
    build_mount_tree, build_navigation_cache_key, build_navigation_dependencies, build_navigation_frontmatter,
    build_navigation_metrics, check_coverage_three, check_description_criteria, check_query_paths,
    infer_module_title, load_and_validate, reconcile_pages, resolve_cached_output, validate_model_output,
    validate_query_suggestions, validate_description_output, _generate_model_outputs, _home_document, _module_documents,
)


def _staging_path(batch: Path) -> Path:
    audit = batch / "_audit"
    if audit.is_symlink() or not audit.is_dir():
        raise NavigationInputError("batch-path-symlink", "batch _audit directory must be real")
    return audit / "nav-staging"


def _remove_staging(batch: Path) -> None:
    audit = batch / "_audit"
    if audit.is_symlink():
        return
    staging = audit / "nav-staging"
    if staging.is_symlink() or staging.is_file():
        staging.unlink()
    elif staging.exists():
        shutil.rmtree(staging)


def _atomic_write(path: Path, content: str) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise NavigationInputError("batch-path-symlink", f"write target must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise NavigationInputError("batch-path-symlink", f"write target must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def _write_staging(batch: Path, documents: Mapping[str, NavigationDocument]) -> None:
    staging = _staging_path(batch)
    staging.mkdir(parents=True, exist_ok=True)
    for relative_path, document in documents.items():
        _safe_batch_path(batch, f"_audit/nav-staging/{relative_path}", field="staging-path")
        _atomic_write(staging / relative_path, document.text)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            raise NavigationInputError("run-metrics-missing", "run-metrics.json is required")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NavigationInputError("run-metrics-invalid", "run-metrics.json is not valid JSON") from exc
    if not isinstance(value, dict):
        raise NavigationInputError("run-metrics-invalid", "run-metrics.json must contain an object")
    return value


def _write_navigation_metrics(
    batch: Path,
    *,
    page_count: int,
    provider_calls: int,
    cache_hits: int,
    provider_tokens: int = 0,
    provider_token_observations: int = 0,
    elapsed_ms: int = 0,
) -> None:
    metrics_path = _safe_batch_path(batch, "_audit/run-metrics.json", field="metrics-path")
    metrics = _read_json_object(metrics_path)
    task8_metrics = dict(
        build_navigation_metrics(
            page_count=page_count,
            provider_calls=provider_calls,
            cache_hits=cache_hits,
        )
    )
    task8_metrics["elapsed_ms"] = max(0, int(elapsed_ms))
    task8_metrics["actual_provider_calls"] = provider_calls
    task8_metrics["provider_tokens"] = max(0, int(provider_tokens))
    task8_metrics["actual_provider_tokens"] = max(0, int(provider_tokens))
    task8_metrics["provider_token_observations"] = max(0, int(provider_token_observations))
    # This is a new per-run projection. Never inherit diagnostic reasons from
    # an earlier blocked attempt when the current run has positive metrics.
    reasons: dict[str, str] = {}
    task8_metrics["reasons"] = reasons
    if task8_metrics["elapsed_ms"] == 0:
        reasons["elapsed_ms"] = "no_provider_call_yet"
    if provider_calls == 0:
        reasons["provider_calls"] = "cache_hit" if cache_hits else "no_provider_call_yet"
    if provider_tokens == 0:
        reasons["provider_tokens"] = "cache_hit" if provider_calls == 0 and cache_hits else (
            "no_provider_call_yet" if provider_calls == 0 else "provider_usage_unavailable"
        )
    metrics["task8_navigation"] = task8_metrics
    _atomic_write(
        metrics_path,
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
    )


def _navigation_payload(
    *,
    status: str,
    success_pages: int,
    blocked_sources: int,
    reasons: Sequence[str],
) -> dict[str, Any]:
    return {
        "navigation_status": status,
        "success_pages": success_pages,
        "blocked_sources": blocked_sources,
        "blocked_reasons": list(dict.fromkeys(str(reason) for reason in reasons)),
    }


def _write_manifest_navigation(batch: Path, manifest: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    updated = dict(manifest)
    updated["navigation"] = dict(payload)
    _atomic_write(
        batch / "_audit" / "page-manifest.json",
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
    )


def _raw_manifest(batch: Path) -> Mapping[str, Any] | None:
    try:
        manifest_path = _safe_batch_path(batch, "_audit/page-manifest.json", field="manifest-path")
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _blocked_sources(manifest: Mapping[str, Any] | None) -> int:
    blockers = manifest.get("blockers", ()) if manifest is not None else ()
    return len(blockers) if isinstance(blockers, list) else 0


def _snapshot_files(batch: Path, relative_paths: Sequence[str]) -> dict[str, bytes | None]:
    snapshot: dict[str, bytes | None] = {}
    for relative_path in relative_paths:
        path = _safe_batch_path(batch, relative_path, field="navigation-path")
        if path.exists() and not path.is_file():
            raise NavigationInputError("navigation-commit-failed", f"navigation target is not a file: {relative_path}")
        snapshot[relative_path] = path.read_bytes() if path.exists() else None
    return snapshot


def _restore_files(batch: Path, snapshot: Mapping[str, bytes | None]) -> tuple[str, ...]:
    errors: list[str] = []
    for relative_path, content in snapshot.items():
        path = _safe_batch_path(batch, relative_path, field="navigation-path")
        try:
            if content is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write_bytes(path, content)
        except (OSError, TypeError, ValueError) as error:
            errors.append(f"{relative_path}:{type(error).__name__}")
    return tuple(errors)


def _blocked_result(
    batch: Path,
    *,
    reasons: Sequence[str],
    manifest: Mapping[str, Any] | None,
    page_count: int,
    provider_calls: int,
    cache_hits: int,
    provider_tokens: int = 0,
    provider_token_observations: int = 0,
    elapsed_ms: int = 0,
    write_manifest: bool,
) -> NavigationResult:
    _remove_staging(batch)
    unique_reasons = tuple(dict.fromkeys(str(reason) for reason in reasons))
    if manifest is not None and write_manifest:
        try:
            _write_navigation_metrics(
                batch,
                page_count=page_count,
                provider_calls=provider_calls,
                cache_hits=cache_hits,
                provider_tokens=provider_tokens,
                provider_token_observations=provider_token_observations,
                elapsed_ms=elapsed_ms,
            )
        except (OSError, TypeError, ValueError, NavigationInputError):
            try:
                _write_manifest_navigation(
                    batch,
                    manifest,
                    _navigation_payload(
                        status="blocked",
                        success_pages=page_count,
                        blocked_sources=_blocked_sources(manifest),
                        reasons=unique_reasons + ("navigation-metrics-write-failed",),
                    ),
                )
            except (OSError, TypeError, ValueError, NavigationInputError):
                pass
            return NavigationResult(
                navigation_status="blocked",
                success_pages=page_count,
                blocked_sources=_blocked_sources(manifest),
                blocked_reasons=unique_reasons + ("navigation-metrics-write-failed",),
                nav_files=(),
            )
        _write_manifest_navigation(
            batch,
            manifest,
            _navigation_payload(
                status="blocked",
                success_pages=page_count,
                blocked_sources=_blocked_sources(manifest),
                reasons=unique_reasons,
            ),
        )
    return NavigationResult(
        navigation_status="blocked",
        success_pages=page_count,
        blocked_sources=_blocked_sources(manifest),
        blocked_reasons=unique_reasons,
        nav_files=(),
    )


def compile_batch_navigation(
    batch_dir: str | Path,
    *,
    cache: Any,
    gateway: Any,
    query_fixture: str | Path | None,
) -> NavigationResult:
    """Compile one K1 batch into fail-closed, batch-local navigation."""

    batch = Path(batch_dir)
    _remove_staging(batch)
    manifest: Mapping[str, Any] | None = None
    try:
        manifest = load_and_validate(batch)
    except NavigationInputError as error:
        raw_manifest = None
        try:
            raw_manifest = _raw_manifest(batch)
        except NavigationInputError:
            raw_manifest = None
        return _blocked_result(
            batch,
            reasons=(error.reason,),
            manifest=raw_manifest,
            page_count=0,
            provider_calls=0,
            cache_hits=0,
            write_manifest=raw_manifest is not None,
        )

    blockers = manifest.get("blockers", ())
    if not isinstance(blockers, list):
        return _blocked_result(
            batch,
            reasons=("manifest-blockers-invalid",),
            manifest=manifest,
            page_count=0,
            provider_calls=0,
            cache_hits=0,
            write_manifest=True,
        )
    if manifest.get("run_status") != "complete":
        return _blocked_result(
            batch,
            reasons=("K1-run-not-complete",),
            manifest=manifest,
            page_count=0,
            provider_calls=0,
            cache_hits=0,
            write_manifest=True,
        )

    try:
        pages = reconcile_pages(batch)
    except NavigationInputError as error:
        return _blocked_result(
            batch,
            reasons=(error.reason,),
            manifest=manifest,
            page_count=0,
            provider_calls=0,
            cache_hits=0,
            write_manifest=True,
        )
    if not pages:
        return _blocked_result(
            batch,
            reasons=("zero-page-batch",),
            manifest=manifest,
            page_count=0,
            provider_calls=0,
            cache_hits=0,
            write_manifest=True,
        )

    stats = {"provider_calls": 0, "cache_hits": 0, "provider_tokens": 0, "provider_token_observations": 0}
    navigation_started = time.monotonic()
    try:
        tree = build_mount_tree(pages)
        index = build_index(tree)
        mechanical_home = build_home(
            tree,
            success_pages=sum(len(page.page_paths) for page in pages),
            blocked_sources=len(blockers),
        )
        descriptions, suggestions, _ = _generate_model_outputs(
            pages=pages,
            index=index,
            cache=cache,
            gateway=gateway,
            stats=stats,
        )
        modules = _module_documents(tree, descriptions)
        home = _home_document(mechanical_home, suggestions)
        documents: dict[str, str] = {
            "Home.md": home.text,
            "Index.md": index.text,
            **{path: document.text for path, document in modules.items()},
        }
        documents.update({path: "" for page in pages for path in page.page_paths})
        coverage_reasons = check_coverage_three(
            page_paths=tuple(path for page in pages for path in page.page_paths),
            documents=documents,
        )
        description_reasons = check_description_criteria(
            descriptions=descriptions,
            page_metadata={
                page.page_path: {
                    "title": page.title,
                    "product": page.product,
                    "section": page.section,
                }
                for page in pages
            },
        )
        query_result = check_query_paths(
            documents=documents,
            page_paths=tuple(path for page in pages for path in page.page_paths),
            query_fixture=query_fixture,
        )
        check_reasons = (*coverage_reasons, *description_reasons)
        # A caller-provided query fixture is part of the K2 gate: an
        # incomplete result means the fixture cannot prove the required
        # paths, so navigation must not be published.  Keep the plan's
        # explicit ``query_fixture=None`` contract as an incomplete,
        # non-blocking direct-library mode for callers that have not supplied
        # the optional gate input yet.
        if query_fixture is not None and query_result.status != "passed":
            check_reasons += query_result.reasons
        if check_reasons:
            return _blocked_result(
                batch,
                reasons=check_reasons,
                manifest=manifest,
                page_count=len(pages),
                provider_calls=stats["provider_calls"],
                cache_hits=stats["cache_hits"],
                provider_tokens=stats["provider_tokens"],
                provider_token_observations=stats["provider_token_observations"],
                elapsed_ms=int((time.monotonic() - navigation_started) * 1000),
                write_manifest=True,
            )
    except (NavigationInputError, TypeError, ValueError, OSError, RuntimeError, KeyError, IndexError) as error:
        reason = error.reason if isinstance(error, NavigationInputError) else "navigation-input-invalid" if isinstance(error, (KeyError, IndexError)) else "model-gateway-failed"
        if isinstance(error, NavigationInputError) and error.reason == "model-output-invalid":
            reason = f"model-output-invalid:{error}"
        return _blocked_result(
            batch,
            reasons=(reason,),
            manifest=manifest,
            page_count=len(locals().get("pages", ())),
            provider_calls=stats.get("provider_calls", 0),
            cache_hits=stats.get("cache_hits", 0),
            provider_tokens=stats.get("provider_tokens", 0),
            provider_token_observations=stats.get("provider_token_observations", 0),
            elapsed_ms=int((time.monotonic() - navigation_started) * 1000),
            write_manifest=True,
        )

    final_documents = {
        "Home.md": home,
        "Index.md": index,
        **modules,
    }
    final_paths = tuple(sorted(final_documents))
    commit_snapshot: dict[str, bytes | None] = {}
    try:
        commit_snapshot = _snapshot_files(
            batch,
            (*final_paths, "_audit/run-metrics.json", "_audit/page-manifest.json"),
        )
        _write_staging(batch, final_documents)
        staging = _staging_path(batch)
        for relative_path in final_paths:
            source = _safe_batch_path(batch, f"_audit/nav-staging/{relative_path}", field="staging-path")
            destination = _safe_batch_path(batch, relative_path, field="navigation-path")
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)
        _write_navigation_metrics(
            batch,
            page_count=len(pages),
            provider_calls=stats["provider_calls"],
            cache_hits=stats["cache_hits"],
            provider_tokens=stats["provider_tokens"],
            provider_token_observations=stats["provider_token_observations"],
            elapsed_ms=int((time.monotonic() - navigation_started) * 1000),
        )
        _write_manifest_navigation(
            batch,
            manifest,
            _navigation_payload(
                status="generated_ok",
                success_pages=sum(len(page.page_paths) for page in pages),
                blocked_sources=len(blockers),
                reasons=(),
            ),
        )
        _remove_staging(batch)
    except (OSError, TypeError, ValueError, NavigationInputError) as error:
        rollback_errors = _restore_files(batch, commit_snapshot)
        _remove_staging(batch)
        reason = error.reason if isinstance(error, NavigationInputError) else "navigation-commit-failed"
        return _blocked_result(
            batch,
            reasons=(reason, *(f"navigation-rollback-failed:{item}" for item in rollback_errors)),
            manifest=manifest,
            page_count=len(pages),
            provider_calls=stats["provider_calls"],
            cache_hits=stats["cache_hits"],
            provider_tokens=stats["provider_tokens"],
            provider_token_observations=stats["provider_token_observations"],
            elapsed_ms=int((time.monotonic() - navigation_started) * 1000),
            write_manifest=False,
        )
    return NavigationResult(
        navigation_status="generated_ok",
        success_pages=sum(len(page.page_paths) for page in pages),
        blocked_sources=len(blockers),
        blocked_reasons=(),
        nav_files=final_paths,
    )


__all__ = [
    "ConfiguredNavigationGateway",
    "JsonlNavigationCache",
    "MANIFEST_SCHEMA_VERSION",
    "MountEntry",
    "NavigationDocument",
    "NavigationDependencies",
    "NAVIGATION_GENERATED_BY",
    "NavigationInputError",
    "NavigationResult",
    "REJECTION_WORDS",
    "ReconciledPage",
    "build_index",
    "build_home",
    "build_mount_tree",
    "build_navigation_cache_key",
    "build_navigation_dependencies",
    "build_navigation_frontmatter",
    "build_navigation_metrics",
    "build_module_indexes",
    "check_coverage_three",
    "check_description_criteria",
    "check_query_paths",
    "compile_batch_navigation",
    "infer_module_title",
    "load_and_validate",
    "reconcile_pages",
    "resolve_cached_output",
    "validate_query_suggestions",
    "validate_model_output",
    "validate_description_output",
]
