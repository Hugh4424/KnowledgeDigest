"""Orchestrate the Task7 lossless semantic compiler.

The module is intentionally the only layer that knows how the six Task7
building blocks become a dated batch.  It reconciles the frozen source
manifest before doing any model work, keeps model results behind the task
cache, writes deterministic reader pages, and hands all machine-readable
status to :mod:`semantic_audit`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time
from typing import Any, TextIO
import unicodedata
import urllib.request

from .llm import (
    OPENAI_FORMAT,
    SUPPORTED_FORMATS,
    _endpoint as _llm_endpoint,
    _request_in_child as _llm_request_in_child,
    _request_payload as _llm_request_payload,
)
from .provider_config import configured_provider_config_path, load_provider_config
from .semantic_audit import AuditResult, write_audit
from .semantic_cache import CacheIntegrityError, ModelCache
from .semantic_claims import Claim, extract_claims
from .semantic_group import GroupingResult, TopicGroup, group_topics, load_topic_map
from .semantic_page import PagePart, RenderedPage, gbrain_slug, render_pages
from .semantic_split import Block, SplitResult, split_source


_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = _REPO_ROOT / "config" / "task4-source-coverage-89-input.v1.json"
DEFAULT_OUTPUT_PARENT = Path("/Users/Hugh/Downloads/KD测试")
DEFAULT_CACHE_ROOT = _REPO_ROOT / "cache" / "model-cache"
DEFAULT_MODEL_ID = "task7-semantic-model"
DEFAULT_PROMPT_VERSION = "task7-semantic-compiler-v1"
DEFAULT_TOPIC_MAP_PATH = _REPO_ROOT / "config" / "task7-topic-map.json"
DEFAULT_PROVIDER_MAX_TOKENS = 8192
DEFAULT_PROVIDER_MAX_INPUT_CHARS = 120000
_BATCH_NAME_RE = re.compile(r"^(?P<day>\d{4}-\d{2}-\d{2})-(?P<sequence>[1-9]\d*)$")
_MISSING = object()


BASELINE_REGRESSION_NODES = (
    "tests/acceptance/test_task0_runtime_audit.py::test_runtime_audit_records_frozen_calibration_hash",
    "tests/acceptance/test_task2a_reader_bundle.py::test_full_fixture_emits_positive_trust_signals_and_audit_evidence",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_fail_closed_after_content_or_event_mutation",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[source_fingerprint]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[locator]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[target_path]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[page_type]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_validator_reconciles_frontmatter_and_audit_without_input_context",
    "tests/acceptance/test_task2a_reader_bundle.py::test_entry_coverage_mismatch_fails_closed",
    "tests/acceptance/test_task2a_reader_bundle.py::test_entry_producer_missing_fails_closed",
    "tests/acceptance/test_task2a_reader_bundle.py::test_changed_fixture_provenance_fails_closed_before_publishing",
    "tests/acceptance/test_task2a_reader_bundle.py::test_malformed_fixture_selection_without_sample_id_is_structured",
    "tests/acceptance/test_task2a_reader_bundle.py::test_malformed_fixture_selection_without_selection_reason_is_structured",
    "tests/acceptance/test_task2a_reader_bundle.py::test_real_selected_fixtures_close_footnote_to_claim_and_replay",
    "tests/acceptance/test_task2a_reader_bundle.py::test_validator_rejects_bundle_symlinks_and_non_allowlisted_files",
    "tests/acceptance/test_task2a_reader_bundle.py::test_validator_rejects_incomplete_claim_provenance",
)
BASELINE_REGRESSION_CAUSES = {
    BASELINE_REGRESSION_NODES[0]: "external evidence/phase4/calibration-artifact.json is missing",
    **{
        node: "external quality/evidence/task2-entry records are missing; this is a non-code baseline failure"
        for node in BASELINE_REGRESSION_NODES[1:]
    },
}


class ProviderUnavailable(RuntimeError):
    """Raised internally when a cache miss cannot reach a provider."""

    def __init__(
        self,
        message: str,
        *,
        provider_called: bool = False,
        reason: str = "provider_unavailable",
    ) -> None:
        super().__init__(message)
        self.provider_called = provider_called
        self.reason = reason


class InjectedWriteFailure(RuntimeError):
    """Controlled failure seam used by the interruption acceptance fixture."""


@dataclass(frozen=True)
class ConfiguredSemanticProvider:
    """Small provider adapter for the approved user-scoped LLM configuration."""

    api_format: str
    base_url: str
    api_key: str
    model: str
    timeout: int
    max_tokens: int
    max_input_chars: int

    def complete(self, prompt: str) -> Mapping[str, Any]:
        if len(prompt) > self.max_input_chars:
            raise ProviderUnavailable(
                f"semantic provider prompt exceeds configured limit ({len(prompt)} > {self.max_input_chars})"
            )
        if self.api_format not in SUPPORTED_FORMATS:
            raise ProviderUnavailable(f"unsupported provider format: {self.api_format}")
        if not self.base_url or not self.model or not self.api_key:
            raise ProviderUnavailable("provider configuration is incomplete")
        request_body = _llm_request_payload(
            self.api_format,
            self.model,
            prompt,
            max_tokens=self.max_tokens,
            json_mode=True,
        )
        headers = {"content-type": "application/json"}
        if self.api_format == OPENAI_FORMAT:
            headers["authorization"] = f"Bearer {self.api_key}"
        else:
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        request = urllib.request.Request(
            _llm_endpoint(self.base_url, self.api_format),
            data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            raw = _llm_request_in_child(request, timeout=self.timeout)
            envelope = json.loads(raw)
            if self.api_format == OPENAI_FORMAT:
                content = envelope["choices"][0]["message"]["content"]
            else:
                content = envelope["content"][0]["text"]
            result = json.loads(str(content))
        except ProviderUnavailable:
            raise
        except (KeyError, IndexError, TypeError, UnicodeDecodeError, json.JSONDecodeError, OSError, ValueError) as error:
            raise ProviderUnavailable(f"provider returned invalid semantic JSON ({type(error).__name__})") from error
        if not isinstance(result, Mapping):
            raise ProviderUnavailable("provider semantic result must be a JSON object")
        nested = result.get("result")
        if isinstance(nested, Mapping) and not any(key in result for key in ("title", "slug", "intro")):
            result = nested
        allowed = {"title", "slug", "intro"}
        normalized = {key: result[key] for key in allowed if key in result}
        if "title" in normalized and not isinstance(normalized["title"], str):
            raise ProviderUnavailable("provider title must be a string")
        if "slug" in normalized and not isinstance(normalized["slug"], str):
            raise ProviderUnavailable("provider slug must be a string")
        if "intro" in normalized and not isinstance(normalized["intro"], (str, list, tuple)):
            raise ProviderUnavailable("provider intro must be text or a sentence array")
        usage = envelope.get("usage", {})
        tokens = _usage_tokens(usage)
        if tokens is None:
            raise ProviderUnavailable(
                "provider response did not include usage tokens",
                reason="provider_usage_unavailable",
            )
        normalized["provider_tokens"] = tokens
        return normalized


def _usage_tokens(value: object) -> int | None:
    if not isinstance(value, Mapping):
        return None
    total = value.get("total_tokens")
    if isinstance(total, int) and not isinstance(total, bool) and total >= 0:
        return total
    prompt_tokens = value.get("prompt_tokens")
    completion_tokens = value.get("completion_tokens")
    if all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in (prompt_tokens, completion_tokens)):
        return int(prompt_tokens) + int(completion_tokens)
    for key in ("tokens", "total", "completion"):
        candidate = value.get(key)
        if isinstance(candidate, int) and not isinstance(candidate, bool) and candidate >= 0:
            return candidate
    return None


def configured_provider_from_env(
    provider_config_path: str | Path | None = None,
) -> ConfiguredSemanticProvider | None:
    """Load the user-scoped provider without exposing credentials to outputs."""

    path = Path(provider_config_path).expanduser() if provider_config_path is not None else configured_provider_config_path()
    config = load_provider_config(path)
    section = config.get("llm", {}) if isinstance(config, Mapping) else {}
    if not isinstance(section, Mapping):
        section = {}
    env = dict(os.environ)

    def value(name: str, env_name: str, default: str = "") -> str:
        candidate = section.get(name)
        if candidate is None or not str(candidate).strip():
            candidate = env.get(env_name, default)
        return str(candidate).strip()

    api_key = value("api_key", "KD_LLM_API_KEY")
    api_key_env = section.get("api_key_env")
    if not api_key and isinstance(api_key_env, str) and api_key_env.strip():
        api_key = env.get(api_key_env.strip(), "").strip()
    api_format = value("api_format", "KD_LLM_FORMAT", OPENAI_FORMAT)
    base_url = value("base_url", "KD_LLM_BASE_URL")
    model = value("model", "KD_LLM_MODEL")
    if not any((api_key, base_url, model)):
        return None

    def positive_int(name: str, env_name: str, default: int) -> int:
        candidate = section.get(name, env.get(env_name, default))
        try:
            result = int(candidate)
        except (TypeError, ValueError) as error:
            raise ValueError(f"provider {name} must be an integer") from error
        if result <= 0:
            raise ValueError(f"provider {name} must be greater than zero")
        return result

    return ConfiguredSemanticProvider(
        api_format=api_format,
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout=positive_int("timeout_seconds", "KD_LLM_TIMEOUT_SECONDS", 60),
        max_tokens=positive_int("max_tokens", "KD_LLM_MAX_TOKENS", DEFAULT_PROVIDER_MAX_TOKENS),
        max_input_chars=positive_int("max_input_chars", "KD_LLM_MAX_INPUT_CHARS", DEFAULT_PROVIDER_MAX_INPUT_CHARS),
    )


@dataclass(frozen=True)
class SourceInput:
    source_path: str
    source_id: str
    expected_hash: str
    expected_byte_count: int
    expected_status: str | None
    physical_path: Path | None
    content_hash: str
    byte_count: int
    text: str
    split: SplitResult | None
    blocked_reason: str | None = None

    @property
    def blocks(self) -> tuple[Block, ...]:
        return self.split.blocks if self.split is not None else ()

    @property
    def has_narrative(self) -> bool:
        return any(block.kind == "narrative" and bool(block.text.strip()) for block in self.blocks)

    def source_record(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "source_path": self.source_path,
            "content_hash": self.content_hash or self.expected_hash,
            "readable": self.physical_path is not None and self.split is not None,
            "blocks": [block.as_dict() for block in self.blocks],
            "has_narrative": self.has_narrative,
        }
        if not row["readable"]:
            row["blocked_reason"] = self.blocked_reason or (
                "source_unreadable" if self.physical_path is None else "source_split_failed"
            )
        if self.expected_status:
            row["expected_status"] = self.expected_status
        return row


@dataclass(frozen=True)
class ReconciliationResult:
    manifest_id: str
    manifest_hash: str | None
    expected_count: int
    entries: tuple[Mapping[str, Any], ...]
    sources: tuple[SourceInput, ...]
    differences: tuple[Mapping[str, Any], ...]
    manifest_path: Path

    @property
    def ok(self) -> bool:
        return not self.differences

    @property
    def source_snapshot(self) -> Mapping[str, Any]:
        result: dict[str, Any] = {
            "input_manifest_id": self.manifest_id,
            "expected_count": self.expected_count,
            "entries": [dict(entry) for entry in self.entries],
        }
        if self.manifest_hash:
            result["manifest_hash"] = self.manifest_hash
        return result


@dataclass(frozen=True)
class BatchPlan:
    source_count: int
    topic_count: int
    page_count: int
    planned_provider_calls: int

    def as_dict(self) -> dict[str, int]:
        return {
            "source_count": self.source_count,
            "topic_count": self.topic_count,
            "page_count": self.page_count,
            "planned_provider_calls": self.planned_provider_calls,
        }


@dataclass(frozen=True)
class BatchResult:
    output_dir: Path
    outcome: str
    plan: Mapping[str, int]
    pages: tuple[RenderedPage, ...]
    audit: AuditResult
    attempt_id: str
    provider_calls: int
    cache_hits: int

    @property
    def run_status(self) -> str:
        return str(self.audit.manifest["run_status"])

    @property
    def publish_status(self) -> str:
        return str(self.audit.manifest["publish_status"])


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalise_relative_path(value: object, *, field: str = "source_path") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field} must be relative: {value!r}")
    parts = tuple(part for part in path.parts if part not in {"", "."})
    if not parts:
        raise ValueError(f"{field} must be non-empty: {value!r}")
    return "/".join(parts)


def _manifest_entries(payload: Mapping[str, Any]) -> tuple[tuple[dict[str, Any], ...], list[dict[str, Any]], int]:
    differences: list[dict[str, Any]] = []
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        return (), [{"reason": "manifest_entries_invalid", "impact": "frozen source reconciliation cannot start"}], 0
    expected_count_raw = payload.get("expected_count", len(raw_entries))
    try:
        expected_count = int(expected_count_raw)
    except (TypeError, ValueError):
        expected_count = len(raw_entries)
        differences.append({
            "reason": "manifest_expected_count_invalid",
            "expected": expected_count_raw,
            "impact": "manifest count cannot be reconciled",
        })
    if expected_count != len(raw_entries):
        differences.append({
            "reason": "manifest_count_mismatch",
            "expected_count": expected_count,
            "actual_count": len(raw_entries),
            "impact": "the frozen source set is not the declared size",
        })

    entries: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, Mapping):
            differences.append({
                "reason": "manifest_entry_invalid",
                "entry_index": index,
                "impact": "source entry is not an object",
            })
            continue
        raw_path = raw.get("source_uri", raw.get("source_path"))
        try:
            source_path = _normalise_relative_path(raw_path)
        except ValueError:
            differences.append({
                "reason": "manifest_entry_invalid",
                "entry_index": index,
                "source_path": str(raw_path),
                "impact": "source path is unsafe or empty",
            })
            continue
        source_id = raw.get("source_id")
        expected_hash = raw.get("content_hash")
        expected_bytes = raw.get("byte_count")
        valid = True
        if not isinstance(source_id, str) or not source_id:
            differences.append({
                "reason": "manifest_entry_invalid",
                "source_path": source_path,
                "impact": "source_id is missing",
            })
            valid = False
        if not isinstance(expected_hash, str) or not expected_hash:
            differences.append({
                "reason": "manifest_entry_invalid",
                "source_path": source_path,
                "impact": "content_hash is missing",
            })
            valid = False
        try:
            expected_byte_count = int(expected_bytes)
            if expected_byte_count < 0:
                raise ValueError
        except (TypeError, ValueError):
            differences.append({
                "reason": "manifest_entry_invalid",
                "source_path": source_path,
                "impact": "byte_count is invalid",
            })
            valid = False
            expected_byte_count = 0
        if source_path in seen_paths:
            differences.append({
                "reason": "duplicate_manifest_source",
                "source_path": source_path,
                "impact": "one source path cannot have two frozen identities",
            })
            valid = False
        seen_paths.add(source_path)
        if not valid:
            continue
        entry = {
            "source_path": source_path,
            "source_uri": source_path,
            "source_id": source_id,
            "content_hash": expected_hash,
            "byte_count": expected_byte_count,
        }
        if isinstance(raw.get("expected_status"), str) and raw["expected_status"]:
            entry["expected_status"] = raw["expected_status"]
        entries.append(entry)
    return tuple(entries), differences, expected_count


def _load_manifest(path: Path) -> tuple[Mapping[str, Any] | None, list[dict[str, Any]]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, [{
            "reason": "manifest_unreadable",
            "manifest_path": str(path),
            "impact": "frozen source reconciliation cannot start",
            "error_type": type(error).__name__,
        }]
    if not isinstance(raw, Mapping):
        return None, [{
            "reason": "manifest_root_invalid",
            "manifest_path": str(path),
            "impact": "frozen source reconciliation cannot start",
        }]
    return raw, []


def _resolve_source_file(new_dir: Path, source_path: str) -> tuple[Path | None, dict[str, Any] | None]:
    root = new_dir.resolve(strict=False)
    candidates = (new_dir / "items" / Path(source_path), new_dir / Path(source_path))
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=False)
        except OSError:
            continue
        if not resolved.is_relative_to(root):
            return None, {
                "reason": "source_path_escapes_input",
                "source_path": source_path,
                "impact": "source path is outside the frozen input directory",
            }
        if resolved.is_file():
            return resolved, None
    return None, {
        "reason": "source_missing",
        "source_path": source_path,
        "impact": "frozen source cannot be split or published",
    }


def reconcile_manifest(new_dir: str | Path, manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> ReconciliationResult:
    """Read the frozen manifest and compare every declared source byte hash."""

    input_root = Path(new_dir)
    manifest = Path(manifest_path)
    payload, differences = _load_manifest(manifest)
    if payload is None:
        return ReconciliationResult(
            manifest_id="unknown",
            manifest_hash=None,
            expected_count=0,
            entries=(),
            sources=(),
            differences=tuple(differences),
            manifest_path=manifest,
        )
    entries, entry_differences, expected_count = _manifest_entries(payload)
    differences.extend(entry_differences)
    manifest_id = payload.get("input_manifest_id")
    if not isinstance(manifest_id, str) or not manifest_id:
        differences.append({
            "reason": "manifest_identity_missing",
            "impact": "the frozen source snapshot has no input_manifest_id",
        })
        manifest_id = "unknown"
    manifest_hash = payload.get("manifest_hash")
    if not isinstance(manifest_hash, str) or not manifest_hash:
        manifest_hash = None

    sources: list[SourceInput] = []
    for entry in entries:
        source_path = str(entry["source_path"])
        physical_path, resolve_difference = _resolve_source_file(input_root, source_path)
        if resolve_difference:
            differences.append(resolve_difference)
            sources.append(SourceInput(
                source_path=source_path,
                source_id=str(entry["source_id"]),
                expected_hash=str(entry["content_hash"]),
                expected_byte_count=int(entry["byte_count"]),
                expected_status=entry.get("expected_status"),
                physical_path=None,
                content_hash="",
                byte_count=0,
                text="",
                split=None,
                blocked_reason=str(resolve_difference.get("reason", "source_unreadable")),
            ))
            continue
        assert physical_path is not None
        try:
            raw_bytes = physical_path.read_bytes()
        except (OSError, UnicodeError) as error:
            differences.append({
                "reason": "source_unreadable",
                "source_path": source_path,
                "impact": "source bytes cannot be reconciled",
                "error_type": type(error).__name__,
            })
            sources.append(SourceInput(
                source_path=source_path,
                source_id=str(entry["source_id"]),
                expected_hash=str(entry["content_hash"]),
                expected_byte_count=int(entry["byte_count"]),
                expected_status=entry.get("expected_status"),
                physical_path=None,
                content_hash="",
                byte_count=0,
                text="",
                split=None,
                blocked_reason="source_unreadable",
            ))
            continue
        actual_hash = _sha256_bytes(raw_bytes)
        actual_bytes = len(raw_bytes)
        if actual_hash != entry["content_hash"]:
            differences.append({
                "reason": "content_hash_mismatch",
                "source_path": source_path,
                "expected_hash": entry["content_hash"],
                "actual_hash": actual_hash,
                "impact": "source content changed after the frozen snapshot",
            })
        if actual_bytes != entry["byte_count"]:
            differences.append({
                "reason": "byte_count_mismatch",
                "source_path": source_path,
                "expected_byte_count": entry["byte_count"],
                "actual_byte_count": actual_bytes,
                "impact": "source byte length changed after the frozen snapshot",
            })
        text_value = raw_bytes.decode("utf-8", "surrogateescape")
        try:
            split_result = split_source(text_value, source_path=source_path, source_id=str(entry["source_id"]))
        except Exception as error:
            differences.append({
                "reason": "source_split_failed",
                "source_path": source_path,
                "impact": "source bytes were read but could not be classified",
                "error_type": type(error).__name__,
            })
            split_result = None
        sources.append(SourceInput(
            source_path=source_path,
            source_id=str(entry["source_id"]),
            expected_hash=str(entry["content_hash"]),
            expected_byte_count=int(entry["byte_count"]),
            expected_status=entry.get("expected_status"),
            physical_path=physical_path,
            content_hash=actual_hash,
            byte_count=actual_bytes,
            text=text_value,
            split=split_result,
            blocked_reason=("source_split_failed" if split_result is None else None),
        ))
        if split_result is not None:
            for item in split_result.differences:
                differences.append({
                    "reason": "split_cross_check_mismatch",
                    "source_path": source_path,
                    "detail": dict(item),
                    "impact": "primary and independent block scans disagree",
                })

    return ReconciliationResult(
        manifest_id=manifest_id,
        manifest_hash=manifest_hash,
        expected_count=expected_count,
        entries=entries,
        sources=tuple(sources),
        differences=tuple(sorted((dict(item) for item in differences), key=_stable_json)),
        manifest_path=manifest,
    )


def allocate_batch_dir(parent: str | Path = DEFAULT_OUTPUT_PARENT, *, today: str | date | None = None) -> Path:
    """Create the next direct child ``YYYY-MM-DD-N`` under the frozen parent."""

    root = Path(parent)
    root.mkdir(parents=True, exist_ok=True)
    if today is None:
        day = date.today()
    elif isinstance(today, date):
        day = today
    else:
        day = date.fromisoformat(str(today)[:10])
    day_text = day.isoformat()
    used = [
        int(match.group("sequence"))
        for child in root.iterdir()
        if (match := _BATCH_NAME_RE.fullmatch(child.name)) and match.group("day") == day_text
    ]
    sequence = max(used, default=0) + 1
    target = root / f"{day_text}-{sequence}"
    target.mkdir()
    return target


def _source_statuses(
    sources: Iterable[SourceInput],
    *,
    audit_only_sources: Iterable[str] = (),
) -> dict[str, str]:
    declared_audit_only = set(audit_only_sources)
    seen_hashes: dict[str, str] = {}
    result: dict[str, str] = {}
    for source in sources:
        if source.expected_status == "audit_only" or source.source_path in declared_audit_only:
            status = "audit_only"
        elif source.content_hash and source.content_hash in seen_hashes:
            status = "duplicate_alias"
        elif not any(
            block.kind != "heading" and bool(block.text.strip())
            for block in source.blocks
        ):
            status = "known_empty"
        else:
            status = "ready"
        result[source.source_path] = status
        if status != "audit_only" and source.content_hash and source.content_hash not in seen_hashes:
            seen_hashes[source.content_hash] = source.source_path
    return result


def _source_mtimes(sources: Iterable[SourceInput]) -> dict[str, float]:
    result: dict[str, float] = {}
    for source in sources:
        if source.physical_path is not None:
            result[source.source_path] = source.physical_path.stat().st_mtime
    return result


def _topic_map_and_version(path: str | Path | None) -> tuple[Mapping[str, Any], str]:
    if path is None:
        path = DEFAULT_TOPIC_MAP_PATH
    target = Path(path)
    if not target.exists():
        return {"topic_aliases": {}, "audit_only_sources": []}, "empty-topic-map"
    loaded = load_topic_map(target)
    version = _sha256_bytes(target.read_bytes())
    return loaded, version


def _claim_normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def _claim_id(
    source_path: str,
    line_start: int | None,
    line_end: int | None,
    char_start: int | None,
    char_end: int | None,
    occurrence_index: int,
    normalized_text: str,
    claim_kind: str,
) -> str:
    payload = "\x1f".join(
        (
            source_path,
            str(line_start),
            str(line_end),
            str(char_start),
            str(char_end),
            str(occurrence_index),
            claim_kind,
            normalized_text,
        )
    )
    return "cl_" + hashlib.sha256(payload.encode("utf-8", "surrogateescape")).hexdigest()[:12]


def _group_page_members(group: TopicGroup) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "topic_key": group.key,
            "source_path": member.source_path,
            "content_hash": member.content_hash,
            "block_id": member.block_id,
            "member_order": index,
            "line_start": member.line_start,
            "line_end": member.line_end,
            "kind": member.kind,
            "text": member.text if member.kind == "narrative" else "",
        }
        for index, member in enumerate(group.members)
    )


def _provider_prompt(group: TopicGroup, *, prompt_version: str, topic_map_version: str) -> str:
    material = {
        "prompt_version": prompt_version,
        "topic_map_version": topic_map_version,
        "topic_key": group.key,
        "product": group.product,
        "title": group.title,
        "members": [
            {
                "source_path": member.source_path,
                "content_hash": member.content_hash,
                "line_start": member.line_start,
                "line_end": member.line_end,
                "kind": member.kind,
                "text": member.text if member.kind == "narrative" else "",
            }
            for member in group.members
        ],
        "requested_fields": ["title", "intro", "slug", "provider_tokens"],
    }
    return (
        "Task7 semantic page compilation. Return only one JSON object with string "
        "title, lowercase ASCII slug, and intro as an array of sentences. "
        "Every intro sentence must be copied exactly from a supplied narrative "
        "member; if no safe sentence is available return an empty array. Never "
        "rewrite or omit source content.\n"
        + _stable_json(material)
    )


def _invoke_provider(provider: object, prompt: str) -> object:
    target = getattr(provider, "complete", None)
    if not callable(target):
        target = provider
    if not callable(target):
        raise ProviderUnavailable("provider is not callable")
    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError):
        return target(prompt)
    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind in {parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD}
    ]
    has_varargs = any(parameter.kind == parameter.VAR_POSITIONAL for parameter in signature.parameters.values())
    if positional or has_varargs:
        return target(prompt)
    return target()


def _provider_tokens(result: Mapping[str, Any]) -> int | None:
    for key in ("provider_tokens", "tokens", "token_count"):
        value = result.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    usage = result.get("usage")
    if isinstance(usage, Mapping):
        for key in ("total_tokens", "tokens", "total"):
            value = usage.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return value
    return None


def _validated_semantic_result(result: object) -> dict[str, Any]:
    """Validate the semantic model contract before cache or page use.

    The cache validates JSON shape and credential absence, but it deliberately
    does not know the page compiler's semantic fields.  Keep this validation at
    the compiler seam so both fresh provider results and old cache hits obey the
    same title/slug/intro contract.
    """

    if not isinstance(result, Mapping):
        raise ProviderUnavailable(
            "provider semantic result must be a JSON object",
            reason="provider_invalid_result",
        )
    normalized = dict(result)
    nested = normalized.get("result")
    if isinstance(nested, Mapping) and not any(
        key in normalized for key in ("title", "slug", "intro")
    ):
        metadata = {key: value for key, value in normalized.items() if key != "result"}
        normalized = {**dict(nested), **metadata}

    missing = [field for field in ("title", "slug", "intro") if field not in normalized]
    if missing:
        raise ProviderUnavailable(
            f"provider semantic result is missing fields: {', '.join(missing)}",
            reason="provider_invalid_result",
        )

    title = normalized["title"]
    if not isinstance(title, str) or not title.strip():
        raise ProviderUnavailable(
            "provider title must be a non-empty string",
            reason="provider_invalid_result",
        )
    if any(character in title for character in "\r\n"):
        raise ProviderUnavailable(
            "provider title must be a single-line string",
            reason="provider_invalid_result",
        )

    slug = normalized["slug"]
    if not isinstance(slug, str):
        raise ProviderUnavailable(
            "provider slug must be a string",
            reason="provider_invalid_result",
        )
    candidate = slug.strip()
    if not candidate or "/" in candidate or "\\" in candidate:
        raise ProviderUnavailable(
            "provider slug must be a non-empty path-safe segment",
            reason="provider_invalid_result",
        )
    canonical = gbrain_slug(candidate)
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", canonical):
        raise ProviderUnavailable(
            "provider slug is not a safe lowercase ASCII segment",
            reason="provider_invalid_result",
        )
    normalized["slug"] = canonical

    intro = normalized["intro"]
    if isinstance(intro, str):
        # The historical adapter accepted one string.  Normalize it at the
        # provider seam so downstream claim extraction always consumes the
        # declared sentence-array shape.
        normalized["intro"] = [intro] if intro else []
    elif isinstance(intro, (list, tuple)) and all(isinstance(item, str) for item in intro):
        normalized["intro"] = list(intro)
    else:
        raise ProviderUnavailable(
            "provider intro must be text or a string sentence array",
            reason="provider_invalid_result",
        )

    if _provider_tokens(normalized) is None:
        raise ProviderUnavailable(
            "provider response did not include usage tokens",
            reason="provider_usage_unavailable",
        )
    return normalized


def _fallback_model(group: TopicGroup) -> dict[str, str]:
    return {"title": group.title, "slug": "", "intro": ""}


def _model_results(
    groups: tuple[TopicGroup, ...],
    *,
    cache: ModelCache,
    provider: object | None,
    model_id: str,
    prompt_version: str,
    topic_map_version: str,
) -> tuple[dict[str, Mapping[str, Any]], list[dict[str, Any]], int, int, int, dict[str, str]]:
    results: dict[str, Mapping[str, Any]] = {}
    blockers: list[dict[str, Any]] = []
    provider_calls = 0
    cache_hits = 0
    provider_tokens = 0
    unavailable_reasons: dict[str, str] = {}
    for group in groups:
        prompt = _provider_prompt(group, prompt_version=prompt_version, topic_map_version=topic_map_version)
        if provider is None:
            provider_call = lambda: (_ for _ in ()).throw(ProviderUnavailable("provider unavailable"))
        else:
            def provider_call(prompt: str = prompt) -> object:
                try:
                    result = _invoke_provider(provider, prompt)
                    return _validated_semantic_result(result)
                except ProviderUnavailable as error:
                    raise ProviderUnavailable(
                        str(error),
                        provider_called=True,
                        reason=error.reason,
                    ) from error
                except Exception as error:
                    raise ProviderUnavailable(
                        f"provider call failed ({type(error).__name__})",
                        provider_called=True,
                    ) from error
        try:
            cached = cache.get_or_call(
                model_id=model_id,
                prompt_version=prompt_version,
                topic_map_version=topic_map_version,
                topic_key=group.key,
                members=_group_page_members(group),
                provider=provider_call,
            )
            validated_cached = _validated_semantic_result(cached.result)
        except CacheIntegrityError as error:
            provider_result = error.provider_result
            unavailable_reasons[group.key] = "cache_integrity_failure"
            if error.provider_called:
                provider_calls += 1
                if isinstance(provider_result, Mapping):
                    tokens = _provider_tokens(provider_result)
                    if tokens is not None:
                        provider_tokens += tokens
            blockers.append({
                "topic_key": group.key,
                "reason": "cache_integrity_failure",
                "cause": str(error),
                "provider_called": error.provider_called,
                "impact": "cache evidence is not trustworthy; the batch remains blocked",
            })
            # Cache integrity failure makes the provider result untrusted for
            # rendering, even when the provider call itself succeeded. Keep
            # it only in diagnostics/metrics and render the deterministic
            # fail-closed model instead.
            results[group.key] = _fallback_model(group)
            continue
        except ProviderUnavailable as error:
            blocker_reason = (
                "model_unavailable_no_cache"
                if error.reason == "provider_unavailable"
                else error.reason
            )
            unavailable_reasons[group.key] = blocker_reason
            if error.provider_called:
                provider_calls += 1
            blockers.append({
                "topic_key": group.key,
                "reason": blocker_reason,
                "cause": str(error),
                "provider_called": error.provider_called,
                "impact": "title/slug use deterministic fallback and the intro is marked 原文未明确",
            })
            results[group.key] = _fallback_model(group)
            continue
        results[group.key] = validated_cached
        cached_tokens = _provider_tokens(validated_cached)
        assert cached_tokens is not None
        if cached.hit:
            cache_hits += 1
        if cached.called:
            provider_calls += 1
            provider_tokens += cached_tokens
    return results, blockers, provider_calls, cache_hits, provider_tokens, unavailable_reasons


def _narrative_claims(
    groups: tuple[TopicGroup, ...],
    page_paths: Mapping[str, str],
    *,
    occurrence_registry: MutableMapping[tuple[str, str], int] | None = None,
) -> dict[str, tuple[Claim, ...]]:
    registry = occurrence_registry if occurrence_registry is not None else {}
    result: dict[str, tuple[Claim, ...]] = {}
    for group in groups:
        claims: list[Claim] = []
        for member in group.members:
            if member.kind != "narrative":
                continue
            claims.extend(
                replace(claim, page_path=page_paths[group.key], page_anchor="narrative")
                for claim in extract_claims(member, occurrence_registry=registry).claims
            )
        result[group.key] = tuple(claims)
    return result


def _claim_member(group: TopicGroup, claim: Claim) -> Any | None:
    declared_block_id = getattr(claim, "source_block_id", None)
    for member in group.members:
        if declared_block_id and member.block_id != declared_block_id:
            continue
        if member.source_path != claim.source_path:
            continue
        if claim.content_hash and member.content_hash != claim.content_hash:
            continue
        if claim.line_start is not None and claim.line_start < member.line_start:
            continue
        if claim.line_end is not None and claim.line_end > member.line_end:
            continue
        return member
    return None


def _member_attribution(member: Any) -> str:
    filename = PurePosixPath(member.source_path).name
    headings = tuple(str(item).strip() for item in member.heading_path if str(item).strip())
    if headings:
        return f"来源：{filename} — {' > '.join(headings)}"
    return f"来源：{filename}"


def _claim_part_path(
    group: TopicGroup,
    page: RenderedPage,
    claim: Claim,
    *,
    occurrence_index: int | None = None,
) -> str:
    if not page.parts:
        raise ValueError(f"claim page has no physical parts: {claim.claim_id}")
    first_path = page.parts[0].relative_path
    if claim.claim_kind == "intro":
        return first_path
    member = _claim_member(group, claim)
    if member is None:
        raise ValueError(f"claim source block cannot be resolved: {claim.claim_id}")
    claim_id = claim.claim_id
    scoped_parts = [
        part for part in page.parts if member.block_id in part.source_block_ids
    ]
    exact_parts = [part for part in scoped_parts if claim_id in part.claim_ids]
    if len(exact_parts) == 1:
        return exact_parts[0].relative_path
    if len(exact_parts) > 1:
        raise ValueError(f"claim rendered in multiple concrete page parts: {claim.claim_id}")
    separator = "" if claim.text.endswith(("\n", "\r")) else "\n"
    needle = f"{claim.text}{separator}{_member_attribution(member)}"
    matches: list[str] = []
    search_parts = scoped_parts or list(page.parts)
    for part in search_parts:
        start = 0
        while True:
            position = part.body.find(needle, start)
            if position < 0:
                break
            matches.append(part.relative_path)
            start = position + max(1, len(needle))
    occurrence = claim.occurrence_index - 1 if occurrence_index is None else occurrence_index
    if 0 <= occurrence < len(matches):
        return matches[occurrence]
    raise ValueError(f"claim source span was not rendered in a concrete page part: {claim.claim_id}")


def _claims_on_concrete_parts(
    groups: tuple[TopicGroup, ...],
    pages: tuple[RenderedPage, ...],
    claims_by_topic: Mapping[str, tuple[Claim, ...]],
) -> dict[str, tuple[Claim, ...]]:
    page_by_key = {page.topic_key: page for page in pages}
    result: dict[str, tuple[Claim, ...]] = {}
    for group in groups:
        page = page_by_key[group.key]
        local_occurrences: dict[tuple[str, str, str], int] = {}
        normalized_claims: list[Claim] = []
        for claim in claims_by_topic.get(group.key, ()):
            member = _claim_member(group, claim)
            occurrence_index: int | None = None
            if member is not None:
                occurrence_key = (member.block_id, claim.source_path, claim.text)
                occurrence_index = local_occurrences.get(occurrence_key, 0)
                local_occurrences[occurrence_key] = occurrence_index + 1
            normalized_claims.append(
                replace(
                    claim,
                    page_path=_claim_part_path(
                        group,
                        page,
                        claim,
                        occurrence_index=occurrence_index,
                    ),
                )
            )
        result[group.key] = tuple(normalized_claims)
    return result


def _intro_claims(
    group: TopicGroup,
    *,
    sentences: Iterable[str],
    narrative_claims: tuple[Claim, ...],
    page_path: str,
    unavailable: bool,
    unavailable_reason: str | None = None,
    occurrence_registry: MutableMapping[tuple[str, str], int] | None = None,
) -> tuple[tuple[Claim, ...], str]:
    sentence_values = tuple(sentence.strip() for sentence in sentences if isinstance(sentence, str) and sentence.strip())
    empty_intro = not sentence_values
    if unavailable and empty_intro:
        sentence_values = ("模型导读不可用",)
    elif empty_intro:
        sentence_values = ("模型导读为空",)
    by_text: dict[str, list[Claim]] = {}
    registry = occurrence_registry if occurrence_registry is not None else {}
    fallback_occurrences: dict[tuple[str, str], int] = {}
    for claim in narrative_claims:
        key = claim.text
        by_text.setdefault(key, []).append(claim)
        registry_key = (claim.source_path, _claim_normalize(claim.text))
        registry[registry_key] = max(
            registry.get(registry_key, 0), claim.occurrence_index
        )

    claims: list[Claim] = []
    rendered: list[str] = []
    cursor = 0
    unsupported = empty_intro
    fallback_member = next(iter(group.members), None)
    if fallback_member is None:
        return (), "原文未明确"
    for sentence in sentence_values:
        normalized = _claim_normalize(sentence)
        matches = () if empty_intro else by_text.get(sentence, ())
        if len(matches) == 1:
            source = matches[0]
            key = (source.source_path, _claim_normalize(source.text))
            occurrence = registry.get(key, 0) + 1
            registry[key] = occurrence
            claim = Claim(
                claim_id=_claim_id(
                    source.source_path,
                    source.line_start,
                    source.line_end,
                    source.char_start,
                    source.char_end,
                    occurrence,
                    normalized,
                    "intro",
                ),
                source_path=source.source_path,
                content_hash=source.content_hash,
                line_start=source.line_start,
                line_end=source.line_end,
                char_start=source.char_start,
                char_end=source.char_end,
                page_path=page_path,
                page_anchor="intro",
                span_start=cursor,
                span_end=cursor + len(sentence),
                claim_kind="intro",
                status="sourced",
                text=sentence,
                occurrence_index=occurrence,
                source_block_id=source.source_block_id,
            )
            rendered.append(sentence)
        else:
            unsupported = True
            occurrence_key = (page_path, normalized)
            occurrence = fallback_occurrences.get(occurrence_key, 0) + 1
            fallback_occurrences[occurrence_key] = occurrence
            claim = Claim(
                claim_id=_claim_id(
                    page_path, None, None, None, None, occurrence, normalized, "intro"
                ),
                source_path=fallback_member.source_path,
                content_hash=fallback_member.content_hash,
                line_start=None,
                line_end=None,
                char_start=None,
                char_end=None,
                page_path=page_path,
                page_anchor="intro",
                span_start=cursor,
                span_end=cursor + len(sentence),
                claim_kind="intro",
                status="原文未明确",
                text=sentence,
                occurrence_index=occurrence,
                retrieval_evidence=(
                    {
                        "query": sentence,
                        "matched": False,
                        "searched_sources": sorted({member.source_path for member in group.members}),
                        "reason": (
                            unavailable_reason
                            or (
                                "provider_unavailable"
                                if unavailable
                                else (
                                    "empty_provider_intro"
                                    if empty_intro
                                    else (
                                        "ambiguous source claim matches"
                                        if len(matches) > 1
                                        else "no exact source claim matched"
                                    )
                                )
                            )
                        ),
                    },
                ),
            )
        claims.append(claim)
        cursor += len(sentence) + 1
    if unsupported:
        # The page shows one fail-closed fallback instead of the candidate
        # intro. Keep one audit claim whose page span addresses that actual
        # fallback, while retaining every rejected sentence as evidence.
        fallback_text = "原文未明确"
        evidence = tuple(
            evidence_item
            for claim in claims
            if claim.status == "原文未明确"
            for evidence_item in claim.retrieval_evidence
        )
        fallback = Claim(
            claim_id=_claim_id(
                page_path,
                None,
                None,
                None,
                None,
                1,
                _claim_normalize(fallback_text),
                "intro",
            ),
            source_path=fallback_member.source_path,
            content_hash=fallback_member.content_hash,
            line_start=None,
            line_end=None,
            char_start=None,
            char_end=None,
            page_path=page_path,
            page_anchor="intro",
            span_start=0,
            span_end=len(fallback_text),
            claim_kind="intro",
            status="原文未明确",
            text=fallback_text,
            occurrence_index=1,
            retrieval_evidence=evidence or (
                {
                    "query": " ".join(sentence_values),
                    "matched": False,
                    "searched_sources": sorted({member.source_path for member in group.members}),
                    "reason": unavailable_reason or (
                        "provider_unavailable"
                        if unavailable
                        else ("empty_provider_intro" if empty_intro else "no exact source claim matched")
                    ),
                },
            ),
        )
        return (fallback,), fallback_text
    return tuple(claims), "原文未明确" if unsupported else " ".join(rendered)


def _page_audit_rows(
    groups: tuple[TopicGroup, ...],
    pages: tuple[RenderedPage, ...],
    claims_by_topic: Mapping[str, tuple[Claim, ...]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    page_by_key = {page.topic_key: page for page in pages}
    rows: list[dict[str, Any]] = []
    all_anchors: dict[str, dict[str, Any]] = {}
    for group in groups:
        page = page_by_key[group.key]
        block_anchors: dict[str, dict[str, str]] = {}
        for index, member in enumerate(group.members, start=1):
            selected_path = page.parts[0].relative_path
            for part in page.parts:
                if member.block_id in part.source_block_ids:
                    selected_path = part.relative_path
                    break
            block_anchors[member.block_id] = {
                "page_path": selected_path,
                "page_anchor": f"block-{index}",
            }
            all_anchors[member.block_id] = dict(block_anchors[member.block_id])
        rows.append({
            "topic_key": group.key,
            "page_path": page.relative_path,
            "page_paths": list(page.page_paths),
            "source_paths": sorted({member.source_path for member in group.members}),
            "block_ids": [member.block_id for member in group.members],
            "claim_ids": [claim.claim_id for claim in claims_by_topic.get(group.key, ())],
            "block_anchors": block_anchors,
        })
    return rows, all_anchors


def _readme(
    *,
    status: str,
    source_count: int,
    topic_count: int,
    page_count: int,
    blockers: Iterable[Mapping[str, Any]],
) -> str:
    rows = [
        "# KnowledgeDigest 语义编译批次",
        "",
        "本目录由 Task7 语义编译器生成，发布状态为 `not_released`。",
        "",
        f"- run_status: `{status}`",
        f"- source_count: `{source_count}`",
        f"- topic_count: `{topic_count}`",
        f"- page_count: `{page_count}`",
        "",
    ]
    normalized = sorted((dict(item) for item in blockers), key=_stable_json)
    if normalized:
        rows.extend(("## 阻塞项", "", *[f"- `{_stable_json(item)}`" for item in normalized], ""))
    else:
        rows.extend(("当前没有编译阻塞项。", ""))
    return "\n".join(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8", "surrogateescape"))


def _attempt_id(batch: Path) -> str:
    return "attempt-" + hashlib.sha256(str(batch).encode("utf-8")).hexdigest()[:24]


def _zero_reason(
    *,
    provider_errors: bool,
    provider_calls: int,
    cache_hits: int,
    provider_usage_unavailable: bool = False,
) -> str:
    if provider_usage_unavailable:
        return "provider_usage_unavailable"
    if provider_errors:
        return "provider_unavailable"
    if provider_calls == 0 and cache_hits:
        return "cache_hit"
    if provider_calls == 0:
        return "no_provider_call_yet"
    return "provider_call_observed"


def _metrics(
    *,
    elapsed_ms: int,
    provider_calls: int,
    provider_tokens: int,
    cache_hits: int,
    planned: int,
    planned_topic_count: int | None = None,
    provider_errors: bool,
    provider_usage_unavailable: bool = False,
) -> dict[str, Any]:
    if planned_topic_count is None:
        planned_topic_count = planned
    reason = _zero_reason(
        provider_errors=provider_errors,
        provider_calls=provider_calls,
        cache_hits=cache_hits,
        provider_usage_unavailable=provider_usage_unavailable,
    )
    reasons: dict[str, str] = {}
    for name, value in (
        ("elapsed_ms", elapsed_ms),
        ("provider_calls", provider_calls),
        ("provider_tokens", provider_tokens),
        ("cache_hits", cache_hits),
        ("planned_provider_calls", planned),
        ("actual_provider_calls", provider_calls),
        ("planned_topic_count", planned_topic_count),
    ):
        if value == 0:
            reasons[name] = "no_provider_call_yet" if name in {"planned_provider_calls", "planned_topic_count"} else reason
    return {
        "elapsed_ms": elapsed_ms,
        "provider_calls": provider_calls,
        "provider_tokens": provider_tokens,
        "cache_hits": cache_hits,
        "planned_provider_calls": planned,
        "actual_provider_calls": provider_calls,
        "planned_topic_count": planned_topic_count,
        "reasons": reasons,
    }


def _write_audit(
    batch: Path,
    *,
    reconciliation: ReconciliationResult,
    all_blocks: Iterable[Block],
    all_claims: Iterable[Claim],
    pages: Iterable[Mapping[str, Any]],
    anchors: Mapping[str, Mapping[str, Any]],
    suggestions: Iterable[Mapping[str, Any]],
    blockers: Iterable[Mapping[str, Any]],
    metrics: Mapping[str, Any],
    attempt_id: str,
    run_status: str,
    audit_only_sources: Iterable[str],
) -> AuditResult:
    return write_audit(
        batch,
        blocks=[block.as_dict() for block in all_blocks],
        claims=[claim.as_dict() for claim in all_claims],
        pages=list(pages),
        source_records=[source.source_record() for source in reconciliation.sources],
        block_anchors=dict(anchors),
        source_snapshot=reconciliation.source_snapshot,
        attempt_id=attempt_id,
        audit_only_sources=tuple(audit_only_sources),
        model_suggestions=tuple(suggestions),
        metrics=dict(metrics),
        blockers=tuple(blockers),
        run_status=run_status,
        publish_status="not_released",
    )


def compile_batch(
    new_dir: str | Path,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    output_parent: str | Path = DEFAULT_OUTPUT_PARENT,
    topic_map_path: str | Path | None = DEFAULT_TOPIC_MAP_PATH,
    cache_root: str | Path = DEFAULT_CACHE_ROOT,
    provider: object | None = None,
    model_id: str = DEFAULT_MODEL_ID,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    today: str | date | None = None,
    write_failure_after: int | None = None,
    stdout: TextIO | None = None,
) -> BatchResult:
    """Compile one frozen source set into a new, not-yet-released batch."""

    started = time.monotonic()
    reconciliation = reconcile_manifest(new_dir, manifest_path)
    batch = allocate_batch_dir(output_parent, today=today)
    attempt_id = _attempt_id(batch)
    out = stdout or sys.stdout
    if not reconciliation.ok:
        blockers = tuple(dict(item) for item in reconciliation.differences)
        _write_text(
            batch / "README.md",
            _readme(
                status="blocked",
                source_count=len(reconciliation.entries),
                topic_count=0,
                page_count=0,
                blockers=blockers,
            ),
        )
        audit = _write_audit(
            batch,
            reconciliation=reconciliation,
            all_blocks=(),
            all_claims=(),
            pages=(),
            anchors={},
            suggestions=(),
            blockers=blockers,
            metrics={
                "elapsed_ms": max(0, int((time.monotonic() - started) * 1000)),
                "provider_calls": 0,
                "provider_tokens": 0,
                "cache_hits": 0,
                "planned_provider_calls": 0,
                "actual_provider_calls": 0,
                "reasons": {
                    "elapsed_ms": "reconciliation_failed",
                    "provider_calls": "no_provider_call_yet",
                    "provider_tokens": "no_provider_call_yet",
                    "cache_hits": "no_provider_call_yet",
                    "planned_provider_calls": "no_provider_call_yet",
                    "actual_provider_calls": "no_provider_call_yet",
                },
            },
            attempt_id=attempt_id,
            run_status="blocked",
            audit_only_sources=(),
        )
        return BatchResult(batch, "blocked", BatchPlan(len(reconciliation.entries), 0, 0, 0).as_dict(), (), audit, attempt_id, 0, 0)

    sources = reconciliation.sources
    all_blocks = tuple(block for source in sources for block in source.blocks)
    all_blockers: list[dict[str, Any]] = []
    for source in sources:
        if source.split is not None:
            all_blockers.extend(
                {
                    **dict(item),
                    "source_path": source.source_path,
                }
                for item in source.split.blockers
            )

    grouping: GroupingResult | None = None
    groups: tuple[TopicGroup, ...] = ()
    source_mtimes: dict[str, float] = {}
    topic_map_version = "unavailable"
    planned_plan = BatchPlan(
        source_count=len(sources),
        topic_count=0,
        page_count=0,
        planned_provider_calls=0,
    )
    try:
        topic_map, topic_map_version = _topic_map_and_version(topic_map_path)
        topic_map_audit_only = topic_map.get("audit_only_sources", ()) if isinstance(topic_map, Mapping) else ()
        statuses = _source_statuses(sources, audit_only_sources=topic_map_audit_only)
        canonical_sources = {
            source_path
            for source_path, status in statuses.items()
            if status not in {"duplicate_alias", "audit_only", "known_empty"}
        }
        group_blocks = tuple(
            block
            for block in all_blocks
            if block.source_path in canonical_sources
            and block.kind != "heading"
            and bool(block.text.strip())
        )
        grouping = group_topics(group_blocks, topic_map=topic_map)
        groups = tuple(grouping.groups)
        source_mtimes = _source_mtimes(sources)
        planned_plan = BatchPlan(
            source_count=len(sources),
            topic_count=len(groups),
            page_count=len(groups),
            planned_provider_calls=len(groups),
        )
        cache = ModelCache(cache_root)
    except Exception as error:
        failure = {
            "reason": "preflight_failed",
            "error_type": type(error).__name__,
            "cause": str(error),
            "impact": "semantic batch setup failed before model work and is not publishable",
        }
        failure_blockers = [*all_blockers, failure]
        _write_text(
            batch / "README.md",
            _readme(
                status="blocked",
                source_count=planned_plan.source_count,
                topic_count=planned_plan.topic_count,
                page_count=0,
                blockers=failure_blockers,
            ),
        )
        audit = _write_audit(
            batch,
            reconciliation=reconciliation,
            all_blocks=all_blocks,
            all_claims=(),
            pages=(),
            anchors={},
            suggestions=grouping.suggestions if grouping is not None else (),
            blockers=failure_blockers,
            metrics=_metrics(
                elapsed_ms=max(0, int((time.monotonic() - started) * 1000)),
                provider_calls=0,
                provider_tokens=0,
                cache_hits=0,
                planned=planned_plan.planned_provider_calls,
                planned_topic_count=planned_plan.topic_count,
                provider_errors=False,
            ),
            attempt_id=attempt_id,
            run_status="blocked",
            audit_only_sources=grouping.audit_only_sources if grouping is not None else (),
        )
        return BatchResult(
            batch,
            "blocked",
            planned_plan.as_dict(),
            (),
            audit,
            attempt_id,
            0,
            0,
        )

    print(
        "Task7 semantic plan: "
        f"sources={planned_plan.source_count} topics={planned_plan.topic_count} "
        f"pages=estimated:{planned_plan.page_count} "
        f"provider_calls={planned_plan.planned_provider_calls}",
        file=out,
    )

    model_results: dict[str, Mapping[str, Any]] = {}
    model_blockers: list[dict[str, Any]] = []
    provider_calls = 0
    cache_hits = 0
    provider_tokens = 0
    unavailable_reasons: dict[str, str] = {}
    materialization_stage = "model"
    try:
        model_results, model_blockers, provider_calls, cache_hits, provider_tokens, unavailable_reasons = _model_results(
            groups,
            cache=cache,
            provider=provider,
            model_id=model_id,
            prompt_version=prompt_version,
            topic_map_version=topic_map_version,
        )
        all_blockers.extend(dict(item) for item in model_blockers)
        materialization_stage = "render"
        preliminary = render_pages(
            groups,
            model_results=model_results,
            claims_by_topic={},
            source_root_name=Path(new_dir).name or "raw",
            source_mtimes=source_mtimes,
        )
        preliminary_paths = {page.topic_key: page.relative_path for page in preliminary}
        claim_occurrence_registry: dict[tuple[str, str], int] = {}
        narrative_by_topic = _narrative_claims(
            groups,
            preliminary_paths,
            occurrence_registry=claim_occurrence_registry,
        )
        all_claims_by_topic: dict[str, tuple[Claim, ...]] = {}
        intro_texts: dict[str, str] = {}
        for group in groups:
            model = model_results.get(group.key, {})
            raw_intro = model.get("intro") if isinstance(model, Mapping) else None
            if isinstance(raw_intro, str):
                intro_sentences: tuple[str, ...] = (raw_intro,)
            elif isinstance(raw_intro, (list, tuple)):
                intro_sentences = tuple(str(item) for item in raw_intro)
            else:
                intro_sentences = ()
            intro_claims, intro_text = _intro_claims(
                group,
                sentences=intro_sentences,
                narrative_claims=narrative_by_topic[group.key],
                page_path=preliminary_paths[group.key],
                unavailable=group.key in unavailable_reasons,
                unavailable_reason=unavailable_reasons.get(group.key),
                occurrence_registry=claim_occurrence_registry,
            )
            intro_texts[group.key] = intro_text or "原文未明确"
            all_claims_by_topic[group.key] = narrative_by_topic[group.key] + intro_claims
        rendered = render_pages(
            groups,
            model_results=model_results,
            claims_by_topic=all_claims_by_topic,
            source_root_name=Path(new_dir).name or "raw",
            source_mtimes=source_mtimes,
            intro_texts=intro_texts,
        )
        final_claims_by_topic = _claims_on_concrete_parts(groups, rendered, all_claims_by_topic)
        materialization_stage = "audit"
        audit_pages, anchors = _page_audit_rows(groups, rendered, final_claims_by_topic)
        all_claims = tuple(claim for topic in sorted(final_claims_by_topic) for claim in final_claims_by_topic[topic])
    except Exception as error:
        failure = {
            "reason": "render_failed" if materialization_stage in {"render", "audit"} else "compile_failed",
            "error_type": type(error).__name__,
            "cause": str(error),
            "impact": "semantic batch could not be materialized and is not publishable",
        }
        failure_blockers = [*all_blockers, failure]
        _write_text(
            batch / "README.md",
            _readme(
                status="blocked",
                source_count=planned_plan.source_count,
                topic_count=planned_plan.topic_count,
                page_count=0,
                blockers=failure_blockers,
            ),
        )
        audit = _write_audit(
            batch,
            reconciliation=reconciliation,
            all_blocks=all_blocks,
            all_claims=(),
            pages=(),
            anchors={},
            suggestions=grouping.suggestions,
            blockers=failure_blockers,
            metrics=_metrics(
                elapsed_ms=max(0, int((time.monotonic() - started) * 1000)),
                provider_calls=provider_calls,
                provider_tokens=provider_tokens,
                cache_hits=cache_hits,
                planned=planned_plan.planned_provider_calls,
                planned_topic_count=planned_plan.topic_count,
                provider_errors=bool(model_blockers),
                provider_usage_unavailable=any(
                    item.get("reason") == "provider_usage_unavailable" for item in model_blockers
                ),
            ),
            attempt_id=attempt_id,
            run_status="blocked",
            audit_only_sources=grouping.audit_only_sources,
        )
        return BatchResult(batch, "blocked", planned_plan.as_dict(), (), audit, attempt_id, provider_calls, cache_hits)

    plan = BatchPlan(
        source_count=planned_plan.source_count,
        topic_count=planned_plan.topic_count,
        page_count=len(rendered),
        planned_provider_calls=planned_plan.planned_provider_calls,
    )
    fatal_blockers = [
        item for item in all_blockers
        if item.get("reason") != "model_unavailable_no_cache"
    ]
    written_parts = 0
    complete_pages: list[RenderedPage] = []
    try:
        # The batch is visibly in progress until every product and audit file
        # has been materialized and the final README can be written.
        _write_text(
            batch / "README.md",
            _readme(
                status="in_progress",
                source_count=plan.source_count,
                topic_count=plan.topic_count,
                page_count=0,
                blockers=all_blockers,
            ),
        )
        for page in rendered:
            for part in page.parts:
                target = batch / part.relative_path
                if not target.resolve(strict=False).is_relative_to(batch.resolve()):
                    raise ValueError(f"page path escapes batch: {part.relative_path}")
                _write_text(target, part.text)
                written_parts += 1
                if write_failure_after is not None and written_parts >= write_failure_after:
                    # A single-part page is fully materialized at this point;
                    # retain it in the interrupted manifest so duplicate
                    # aliases can still reuse its canonical anchor.  A
                    # multi-part page remains absent until every part lands.
                    if part is page.parts[-1]:
                        complete_pages.append(page)
                    raise InjectedWriteFailure("injected write failure")
            complete_pages.append(page)
        final_metrics = _metrics(
            elapsed_ms=max(0, int((time.monotonic() - started) * 1000)),
            provider_calls=provider_calls,
            provider_tokens=provider_tokens,
            cache_hits=cache_hits,
            planned=plan.planned_provider_calls,
            planned_topic_count=plan.topic_count,
            provider_errors=bool(model_blockers),
            provider_usage_unavailable=any(
                item.get("reason") == "provider_usage_unavailable" for item in model_blockers
            ),
        )
        audit = _write_audit(
            batch,
            reconciliation=reconciliation,
            all_blocks=all_blocks,
            all_claims=all_claims,
            pages=audit_pages,
            anchors=anchors,
            suggestions=grouping.suggestions,
            blockers=all_blockers,
            metrics=final_metrics,
            attempt_id=attempt_id,
            run_status="blocked" if fatal_blockers else "complete",
            audit_only_sources=grouping.audit_only_sources,
        )
        final_run_status = str(audit.manifest["run_status"])
        _write_text(
            batch / "README.md",
            _readme(
                status=final_run_status,
                source_count=plan.source_count,
                topic_count=plan.topic_count,
                page_count=plan.page_count,
                blockers=audit.blockers,
            ),
        )
        outcome = "blocked" if final_run_status == "blocked" else "not_released"
        return BatchResult(batch, outcome, plan.as_dict(), rendered, audit, attempt_id, provider_calls, cache_hits)
    except Exception as error:
        interruption = {
            "reason": "write_interrupted" if isinstance(error, InjectedWriteFailure) else "write_failed",
            "error_type": type(error).__name__,
            "cause": str(error),
            "impact": "batch contains a partial products tree and is not publishable",
        }
        interruption_blockers = [*all_blockers, interruption]
        complete_keys = {page.topic_key for page in complete_pages}
        partial_audit_pages = [row for row in audit_pages if row["topic_key"] in complete_keys]
        partial_anchors = {
            block_id: value
            for row in partial_audit_pages
            for block_id, value in row["block_anchors"].items()
        }
        complete_page_paths = {
            page_path
            for row in partial_audit_pages
            for page_path in row.get("page_paths", (row.get("page_path"),))
            if page_path
        }
        partial_claims = tuple(
            claim for claim in all_claims if claim.page_path in complete_page_paths
        )
        try:
            _write_text(
                batch / "README.md",
                _readme(
                    status="interrupted",
                    source_count=plan.source_count,
                    topic_count=plan.topic_count,
                    page_count=len(complete_pages),
                    blockers=interruption_blockers,
                ),
            )
            audit = _write_audit(
                batch,
                reconciliation=reconciliation,
                all_blocks=all_blocks,
                all_claims=partial_claims,
                pages=partial_audit_pages,
                anchors=partial_anchors,
                suggestions=grouping.suggestions,
                blockers=interruption_blockers,
                metrics=_metrics(
                    elapsed_ms=max(0, int((time.monotonic() - started) * 1000)),
                    provider_calls=provider_calls,
                    provider_tokens=provider_tokens,
                    cache_hits=cache_hits,
                    planned=plan.planned_provider_calls,
                    planned_topic_count=plan.topic_count,
                    provider_errors=bool(model_blockers),
                    provider_usage_unavailable=any(
                        item.get("reason") == "provider_usage_unavailable" for item in model_blockers
                    ),
                ),
                attempt_id=attempt_id,
                run_status="interrupted",
                audit_only_sources=grouping.audit_only_sources,
            )
        except Exception as recovery_error:
            raise error from recovery_error
        return BatchResult(batch, "interrupted", plan.as_dict(), tuple(complete_pages), audit, attempt_id, provider_calls, cache_hits)


__all__ = [
    "BASELINE_REGRESSION_CAUSES",
    "BASELINE_REGRESSION_NODES",
    "BatchPlan",
    "BatchResult",
    "ConfiguredSemanticProvider",
    "ReconciliationResult",
    "SourceInput",
    "allocate_batch_dir",
    "compile_batch",
    "configured_provider_from_env",
    "reconcile_manifest",
]
