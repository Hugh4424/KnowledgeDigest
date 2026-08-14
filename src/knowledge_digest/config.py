"""Threshold defaults and the small JSON configuration contract."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ValidationError


DEFAULT_TOP_K = 5
DEFAULT_PAGE_MATCH_THRESHOLD = 0.15
DEFAULT_HIGH = 0.90
DEFAULT_MEDIUM = 0.80
DEFAULT_MAX_LINES = 300
DEFAULT_LLM_BATCH_MAX_CLAIMS = 20
DEFAULT_LLM_BATCH_MAX_SOURCE_CHARS = 3000
DEFAULT_LLM_BATCH_CONCURRENCY = 4
DEFAULT_RUNTIME_MAX_PROVIDER_CALLS = 180
DEFAULT_RUNTIME_MAX_REPLAY_CALLS = 1
DEFAULT_RUNTIME_REQUEST_TIMEOUT_SECONDS = 180
DEFAULT_RUNTIME_MAX_WALL_SECONDS = 3600
RISK_RULE_VERSION = "risk-rules-v1"
ROUTING_RULE_VERSION = "routing-jaccard-v2"
SUPPORTED_LLM_FORMATS = ("openai", "anthropic")
_CONFIG_KEYS = frozenset(
    {
        "top_k",
        "page_match_threshold",
        "high",
        "medium",
        "max_lines",
        "cluster_auto_threshold",
        "cluster_review_threshold",
        "max_doc_lines",
        "llm_enabled",
        "llm_format",
        "llm_summary_enabled",
        "llm_batch_max_claims",
        "llm_batch_max_source_chars",
        "llm_batch_concurrency",
        "runtime",
        "similarity",
    }
)
_CONFIG_ALIASES = {
    "cluster_auto_threshold": "high",
    "cluster_review_threshold": "medium",
    "max_doc_lines": "max_lines",
}


@dataclass(frozen=True)
class EmbeddingSettings:
    base_url: str
    model: str
    expected_dimension: int
    calibration_artifact: Path
    api_key_env: str


@dataclass(frozen=True)
class SimilaritySettings:
    backend: str = "jaccard"
    embedding: EmbeddingSettings | None = None


@dataclass(frozen=True)
class RuntimePolicy:
    max_provider_calls: object = DEFAULT_RUNTIME_MAX_PROVIDER_CALLS
    max_replay_calls: object = DEFAULT_RUNTIME_MAX_REPLAY_CALLS
    request_timeout_seconds: object = DEFAULT_RUNTIME_REQUEST_TIMEOUT_SECONDS
    max_wall_seconds: object = DEFAULT_RUNTIME_MAX_WALL_SECONDS
    concurrency: object = DEFAULT_LLM_BATCH_CONCURRENCY
    source: str = "bundled-defaults"


@dataclass(frozen=True)
class DigestSettings:
    top_k: int = DEFAULT_TOP_K
    page_match_threshold: float = DEFAULT_PAGE_MATCH_THRESHOLD
    high: float = DEFAULT_HIGH
    medium: float = DEFAULT_MEDIUM
    max_lines: int = DEFAULT_MAX_LINES
    risk_rule_version: str = RISK_RULE_VERSION
    routing_rule_version: str = ROUTING_RULE_VERSION
    llm_enabled: bool = False
    llm_format: str = "openai"
    llm_summary_enabled: bool = False
    llm_batch_max_claims: int = DEFAULT_LLM_BATCH_MAX_CLAIMS
    llm_batch_max_source_chars: int = DEFAULT_LLM_BATCH_MAX_SOURCE_CHARS
    llm_batch_concurrency: int = DEFAULT_LLM_BATCH_CONCURRENCY
    runtime: RuntimePolicy = RuntimePolicy()
    similarity: SimilaritySettings = SimilaritySettings()


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.is_file():
        raise ValidationError("config", path, "config file is missing or is not a regular file")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("config", path, f"invalid JSON config ({error})") from error
    if not isinstance(loaded, dict):
        raise ValidationError("config", path, "JSON config must contain an object")
    unknown = sorted(set(loaded) - _CONFIG_KEYS)
    if unknown:
        raise ValidationError("config", path, f"unknown config field(s): {', '.join(unknown)}")
    return {_CONFIG_ALIASES.get(name, name): value for name, value in loaded.items()}


def _require_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("config", name, "must be an integer")
    return value


def _require_float(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("config", name, "must be a number")
    return float(value)


def _require_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValidationError("config", name, "must be a boolean")
    return value


def _similarity_settings(value: Any) -> SimilaritySettings:
    if value is None:
        return SimilaritySettings()
    if not isinstance(value, dict):
        raise ValidationError("config", "similarity", "must be an object")
    unknown = sorted(set(value) - {"backend", "embedding"})
    if unknown:
        raise ValidationError("config", "similarity", f"unknown field(s): {', '.join(unknown)}")
    backend = value.get("backend")
    if backend not in {"jaccard", "embedding"}:
        raise ValidationError("config", "similarity.backend", "must be jaccard or embedding")
    raw_embedding = value.get("embedding")
    if raw_embedding is None:
        if backend == "embedding":
            raise ValidationError("config", "similarity.embedding", "is required for embedding")
        return SimilaritySettings(backend=backend)
    if not isinstance(raw_embedding, dict):
        raise ValidationError("config", "similarity.embedding", "must be an object")
    required = {
        "base_url",
        "model",
        "expected_dimension",
        "calibration_artifact",
        "api_key_env",
    }
    unknown = sorted(set(raw_embedding) - required)
    missing = sorted(required - set(raw_embedding))
    if unknown or missing:
        details = []
        if missing:
            details.append(f"missing field(s): {', '.join(missing)}")
        if unknown:
            details.append(f"unknown field(s): {', '.join(unknown)}")
        raise ValidationError("config", "similarity.embedding", "; ".join(details))
    for field in ("base_url", "model", "calibration_artifact", "api_key_env"):
        if not isinstance(raw_embedding[field], str) or not raw_embedding[field].strip():
            raise ValidationError("config", f"similarity.embedding.{field}", "must be a non-empty string")
    dimension = _require_int(
        "similarity.embedding.expected_dimension",
        raw_embedding["expected_dimension"],
    )
    if dimension < 1:
        raise ValidationError(
            "config", "similarity.embedding.expected_dimension", "must be at least 1"
        )
    return SimilaritySettings(
        backend=backend,
        embedding=EmbeddingSettings(
            base_url=raw_embedding["base_url"],
            model=raw_embedding["model"],
            expected_dimension=dimension,
            calibration_artifact=Path(raw_embedding["calibration_artifact"]),
            api_key_env=raw_embedding["api_key_env"],
        ),
    )


def _runtime_policy(value: Any) -> RuntimePolicy:
    if value is None:
        return RuntimePolicy()
    if not isinstance(value, dict):
        return RuntimePolicy(
            max_provider_calls=None,
            max_replay_calls=None,
            request_timeout_seconds=None,
            max_wall_seconds=None,
            concurrency=None,
            source="config:invalid",
        )
    allowed = {
        "max_provider_calls",
        "max_replay_calls",
        "request_timeout_seconds",
        "max_wall_seconds",
        "concurrency",
    }
    unknown = sorted(set(value) - allowed)
    if unknown:
        return RuntimePolicy(
            max_provider_calls=None,
            max_replay_calls=None,
            request_timeout_seconds=None,
            max_wall_seconds=None,
            concurrency=None,
            source=f"config:runtime-unknown:{','.join(unknown)}",
        )
    values = {key: value.get(key) for key in allowed}
    return RuntimePolicy(**values, source="config:runtime")


def resolve_settings(
    config_path: Path | None,
    *,
    top_k: int | None,
    high: float | None,
    medium: float | None,
    max_lines: int | None,
    page_match_threshold: float | None = None,
    llm_enabled: bool | None = None,
    llm_format: str | None = None,
    llm_summary_enabled: bool | None = None,
    llm_batch_max_claims: int | None = None,
    llm_batch_max_source_chars: int | None = None,
    llm_batch_concurrency: int | None = None,
    env: dict[str, str] | None = None,
) -> DigestSettings:
    """Apply bundled defaults, JSON defaults, environment, then CLI overrides."""
    values: dict[str, Any] = {
        "top_k": DEFAULT_TOP_K,
        "page_match_threshold": DEFAULT_PAGE_MATCH_THRESHOLD,
        "high": DEFAULT_HIGH,
        "medium": DEFAULT_MEDIUM,
        "max_lines": DEFAULT_MAX_LINES,
        "llm_enabled": False,
        "llm_format": "openai",
        "llm_summary_enabled": False,
        "llm_batch_max_claims": DEFAULT_LLM_BATCH_MAX_CLAIMS,
        "llm_batch_max_source_chars": DEFAULT_LLM_BATCH_MAX_SOURCE_CHARS,
        "llm_batch_concurrency": DEFAULT_LLM_BATCH_CONCURRENCY,
        "runtime": None,
        "similarity": None,
    }
    values.update(_load_json(config_path))

    source = dict(os.environ if env is None else env)
    if source.get("KD_LLM_FORMAT"):
        values["llm_format"] = source["KD_LLM_FORMAT"]
        values["llm_enabled"] = True

    cli_values = {
        "top_k": top_k,
        "page_match_threshold": page_match_threshold,
        "high": high,
        "medium": medium,
        "max_lines": max_lines,
        "llm_enabled": llm_enabled,
        "llm_format": llm_format,
        "llm_summary_enabled": llm_summary_enabled,
        "llm_batch_max_claims": llm_batch_max_claims,
        "llm_batch_max_source_chars": llm_batch_max_source_chars,
        "llm_batch_concurrency": llm_batch_concurrency,
    }
    values.update({name: value for name, value in cli_values.items() if value is not None})

    settings = DigestSettings(
        top_k=_require_int("top_k", values["top_k"]),
        page_match_threshold=_require_float(
            "page_match_threshold", values["page_match_threshold"]
        ),
        high=_require_float("high", values["high"]),
        medium=_require_float("medium", values["medium"]),
        max_lines=_require_int("max_lines", values["max_lines"]),
        llm_enabled=_require_bool("llm_enabled", values["llm_enabled"]),
        llm_format=str(values["llm_format"]),
        llm_summary_enabled=_require_bool(
            "llm_summary_enabled", values["llm_summary_enabled"]
        ),
        llm_batch_max_claims=_require_int(
            "llm_batch_max_claims", values["llm_batch_max_claims"]
        ),
        llm_batch_max_source_chars=_require_int(
            "llm_batch_max_source_chars", values["llm_batch_max_source_chars"]
        ),
        llm_batch_concurrency=_require_int(
            "llm_batch_concurrency", values["llm_batch_concurrency"]
        ),
        runtime=_runtime_policy(values["runtime"]),
        similarity=_similarity_settings(values["similarity"]),
    )
    if settings.llm_format not in SUPPORTED_LLM_FORMATS:
        raise ValidationError(
            "config", "llm_format", f"must be one of {', '.join(SUPPORTED_LLM_FORMATS)}"
        )
    if settings.top_k < 1:
        raise ValidationError("config", "top_k", "must be at least 1")
    if not 0 < settings.page_match_threshold <= 1:
        raise ValidationError(
            "config", "page_match_threshold", "must be greater than 0 and at most 1"
        )
    if settings.max_lines < 1:
        raise ValidationError("config", "max_lines", "must be at least 1")
    if settings.llm_batch_max_claims < 1:
        raise ValidationError("config", "llm_batch_max_claims", "must be at least 1")
    if settings.llm_batch_max_source_chars < 1:
        raise ValidationError(
            "config", "llm_batch_max_source_chars", "must be at least 1"
        )
    if settings.llm_batch_concurrency < 1:
        raise ValidationError("config", "llm_batch_concurrency", "must be at least 1")
    if not 0 <= settings.medium <= 1:
        raise ValidationError("config", "medium", "must be between 0 and 1")
    if not 0 <= settings.high <= 1:
        raise ValidationError("config", "high", "must be between 0 and 1")
    if settings.high < settings.medium:
        raise ValidationError("config", "high", "must be greater than or equal to medium")
    return settings
