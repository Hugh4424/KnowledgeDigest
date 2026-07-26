"""Threshold defaults and the small JSON configuration contract."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ValidationError


DEFAULT_TOP_K = 5
DEFAULT_HIGH = 0.90
DEFAULT_MEDIUM = 0.80
DEFAULT_MAX_LINES = 300
RISK_RULE_VERSION = "risk-rules-v1"
SUPPORTED_LLM_FORMATS = ("openai", "anthropic")
_CONFIG_KEYS = frozenset(
    {
        "top_k",
        "high",
        "medium",
        "max_lines",
        "cluster_auto_threshold",
        "cluster_review_threshold",
        "max_doc_lines",
        "llm_enabled",
        "llm_format",
    }
)
_CONFIG_ALIASES = {
    "cluster_auto_threshold": "high",
    "cluster_review_threshold": "medium",
    "max_doc_lines": "max_lines",
}


@dataclass(frozen=True)
class DigestSettings:
    top_k: int = DEFAULT_TOP_K
    high: float = DEFAULT_HIGH
    medium: float = DEFAULT_MEDIUM
    max_lines: int = DEFAULT_MAX_LINES
    risk_rule_version: str = RISK_RULE_VERSION
    llm_enabled: bool = False
    llm_format: str = "openai"


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


def resolve_settings(
    config_path: Path | None,
    *,
    top_k: int | None,
    high: float | None,
    medium: float | None,
    max_lines: int | None,
    llm_enabled: bool | None = None,
    llm_format: str | None = None,
    env: dict[str, str] | None = None,
) -> DigestSettings:
    """Apply bundled defaults, JSON defaults, environment, then CLI overrides."""
    values: dict[str, Any] = {
        "top_k": DEFAULT_TOP_K,
        "high": DEFAULT_HIGH,
        "medium": DEFAULT_MEDIUM,
        "max_lines": DEFAULT_MAX_LINES,
        "llm_enabled": False,
        "llm_format": "openai",
    }
    values.update(_load_json(config_path))

    source = dict(os.environ if env is None else env)
    if source.get("KD_LLM_FORMAT"):
        values["llm_format"] = source["KD_LLM_FORMAT"]
        values["llm_enabled"] = True

    cli_values = {
        "top_k": top_k,
        "high": high,
        "medium": medium,
        "max_lines": max_lines,
        "llm_enabled": llm_enabled,
        "llm_format": llm_format,
    }
    values.update({name: value for name, value in cli_values.items() if value is not None})

    settings = DigestSettings(
        top_k=_require_int("top_k", values["top_k"]),
        high=_require_float("high", values["high"]),
        medium=_require_float("medium", values["medium"]),
        max_lines=_require_int("max_lines", values["max_lines"]),
        llm_enabled=_require_bool("llm_enabled", values["llm_enabled"]),
        llm_format=str(values["llm_format"]),
    )
    if settings.llm_format not in SUPPORTED_LLM_FORMATS:
        raise ValidationError(
            "config", "llm_format", f"must be one of {', '.join(SUPPORTED_LLM_FORMATS)}"
        )
    if settings.top_k < 1:
        raise ValidationError("config", "top_k", "must be at least 1")
    if settings.max_lines < 1:
        raise ValidationError("config", "max_lines", "must be at least 1")
    if not 0 <= settings.medium <= 1:
        raise ValidationError("config", "medium", "must be between 0 and 1")
    if not 0 <= settings.high <= 1:
        raise ValidationError("config", "high", "must be between 0 and 1")
    if settings.high < settings.medium:
        raise ValidationError("config", "high", "must be greater than or equal to medium")
    return settings
