"""Threshold defaults and the small JSON configuration contract."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import ValidationError


DEFAULT_TOP_K = 5
DEFAULT_HIGH = 0.90
DEFAULT_MEDIUM = 0.80
DEFAULT_MAX_LINES = 300
RISK_RULE_VERSION = "risk-rules-v1"
HIGH_RISK_MAX_ROUNDS = 3
SINGLE_RISK_MAX_ROUNDS = 1
_CONFIG_KEYS = frozenset(
    {
        "top_k",
        "high",
        "medium",
        "max_lines",
        "cluster_auto_threshold",
        "cluster_review_threshold",
        "max_doc_lines",
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


_STRUCTURED_LINE_PATTERNS = (
    re.compile(r"^\s*(?:FAQ|Q(?:uestion)?)[\s:：]", re.IGNORECASE),
    re.compile(r"^\s*(?:Error\s+)?[A-Z][A-Z0-9_-]*\d+[\s:：-]", re.IGNORECASE),
    re.compile(r"^\s*(?:[-*]\s*)?(?:parameter|param|argument)\b[^:：]*[:：]", re.IGNORECASE),
    re.compile(r"^\s*```"),
)


def _is_structured_line(line: str) -> bool:
    stripped = line.strip()
    return bool(
        stripped
        and (
            any(pattern.search(line) for pattern in _STRUCTURED_LINE_PATTERNS)
            or "https://" in line
            or "http://" in line
            or "|" in line
            or re.fullmatch(r"\s*[-:| ]{3,}\s*", line) is not None
        )
    )


def _candidate_claim_count(items: list[Mapping[str, Any]]) -> int:
    return sum(
        1
        for item in items
        for line in str(item.get("text", "")).splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
        and not line.strip().casefold().startswith("unsupported:")
    )


def _component_count(items: list[Mapping[str, Any]]) -> int:
    """Count deterministic content units without semantic/model judgment."""
    count = 0
    for item in items:
        previous_blank = True
        for line in str(item.get("text", "")).splitlines():
            stripped = line.strip()
            if not stripped:
                previous_blank = True
                continue
            marker = (
                stripped.startswith("#")
                or any(pattern.search(line) for pattern in _STRUCTURED_LINE_PATTERNS)
            )
            if previous_blank or marker:
                count += 1
            previous_blank = False
    return count


def build_risk_signals(
    cluster: Mapping[str, Any],
    decision: Mapping[str, Any] | None = None,
    items: list[Mapping[str, Any]] | None = None,
    *,
    max_doc_lines: int = DEFAULT_MAX_LINES,
) -> dict[str, Any]:
    """Build replayable, generation-free signals for one digest cluster."""
    decision = decision or {}
    items = items or []
    source_count = int(decision.get("source_count", cluster.get("source_count", len(items))))
    source_line_count = int(
        decision.get(
            "source_line_count",
            cluster.get("source_line_count", sum(len(str(item.get("text", "")).splitlines()) for item in items)),
        )
    )
    non_empty_lines = [
        line
        for item in items
        for line in str(item.get("text", "")).splitlines()
        if line.strip()
    ]
    structured_line_count = sum(_is_structured_line(line) for line in non_empty_lines)
    structured_line_ratio = (
        round(structured_line_count / len(non_empty_lines), 6) if non_empty_lines else 0.0
    )
    target_paths = decision.get("target_paths", cluster.get("target_paths", []))
    target_page_count = int(
        decision.get("target_page_count", cluster.get("target_page_count", len(target_paths) if isinstance(target_paths, list) else 0))
    )
    statuses = {str(item.get("validation_status", item.get("source_status", "passed"))).casefold() for item in items}
    action = str(decision.get("action", cluster.get("action", "new")))
    coverage_risk = bool(decision.get("coverage_risk", cluster.get("coverage_risk", False)))
    if statuses - {"passed", "verified", "ok"}:
        coverage_risk = True
    if action in {"revise", "merge_multiple"} and not target_paths:
        coverage_risk = True
    return {
        "cluster_tier": str(cluster.get("cluster_tier", cluster.get("tier", "insufficient_signal"))),
        "action": action,
        "source_count": source_count,
        "target_page_count": target_page_count,
        "source_line_count": source_line_count,
        "structured_line_ratio": structured_line_ratio,
        "coverage_risk": coverage_risk,
        "estimated_claim_count": int(
            decision.get("estimated_claim_count", cluster.get("estimated_claim_count", _candidate_claim_count(items)))
        ),
        "estimated_component_count": int(
            decision.get("estimated_component_count", cluster.get("estimated_component_count", _component_count(items)))
        ),
        "max_doc_lines": max_doc_lines,
    }


def evaluate_risk(signals: Mapping[str, Any], *, rule_version: str = RISK_RULE_VERSION) -> dict[str, Any]:
    """Apply the fixed risk-rules-v1 table and return a JSON-ready decision."""
    if rule_version != RISK_RULE_VERSION:
        raise ValueError(f"unsupported risk rule version: {rule_version}")
    high_rules: list[str] = []
    if signals.get("action") == "merge_multiple":
        high_rules.append("action.merge_multiple")
    if int(signals.get("target_page_count", 0)) >= 2:
        high_rules.append("target_page_count.ge_2")
    if int(signals.get("source_count", 0)) >= 3:
        high_rules.append("source_count.ge_3")
    if int(signals.get("source_line_count", 0)) > int(signals.get("max_doc_lines", DEFAULT_MAX_LINES)):
        high_rules.append("source_line_count.over_max_doc_lines")
    if float(signals.get("structured_line_ratio", 0.0)) >= 0.30:
        high_rules.append("structured_line_ratio.ge_0.30")
    if bool(signals.get("coverage_risk")):
        high_rules.append("coverage_risk")
    if signals.get("cluster_tier") == "needs_review":
        high_rules.append("cluster_tier.needs_review")

    medium_rules: list[str] = []
    if signals.get("action") == "revise":
        medium_rules.append("action.revise")
    if int(signals.get("source_count", 0)) == 2:
        medium_rules.append("source_count.eq_2")
    ratio = float(signals.get("structured_line_ratio", 0.0))
    if 0.15 <= ratio < 0.30:
        medium_rules.append("structured_line_ratio.ge_0.15")
    line_count = int(signals.get("source_line_count", 0))
    max_lines = int(signals.get("max_doc_lines", DEFAULT_MAX_LINES))
    if 0.75 * max_lines < line_count <= max_lines:
        medium_rules.append("source_line_count.ge_75pct")
    if int(signals.get("estimated_claim_count", 0)) >= 8:
        medium_rules.append("estimated_claim_count.ge_8")
    if int(signals.get("estimated_component_count", 0)) >= 5:
        medium_rules.append("estimated_component_count.ge_5")

    if high_rules:
        risk_level = "high"
        rules_triggered = high_rules
        max_rounds = HIGH_RISK_MAX_ROUNDS
    elif medium_rules:
        risk_level = "medium"
        rules_triggered = medium_rules
        max_rounds = SINGLE_RISK_MAX_ROUNDS
    else:
        risk_level = "low"
        rules_triggered = []
        max_rounds = SINGLE_RISK_MAX_ROUNDS
    reason = f"{risk_level}: " + ("; ".join(rules_triggered) if rules_triggered else "no elevated rule matched")
    return {
        "risk_rule_version": rule_version,
        "signals": dict(signals),
        "rules_triggered": rules_triggered,
        "risk_level": risk_level,
        "max_rounds": max_rounds,
        "decision_reason": reason,
        "max_doc_lines": max_lines,
    }


def risk_decision(
    signals: Mapping[str, Any] | None = None,
    *,
    cluster: Mapping[str, Any] | None = None,
    decision: Mapping[str, Any] | None = None,
    items: list[Mapping[str, Any]] | None = None,
    max_doc_lines: int = DEFAULT_MAX_LINES,
) -> dict[str, Any]:
    """Public risk decision helper used by the pipeline and acceptance tests."""
    if signals is None:
        if cluster is None:
            raise ValueError("cluster is required when signals are not supplied")
        signals = build_risk_signals(
            cluster,
            decision,
            items,
            max_doc_lines=max_doc_lines,
        )
    return evaluate_risk(signals)


# Concise aliases for callers that want to name the rule table directly.
risk_rules = evaluate_risk
preflight_signals = build_risk_signals


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


def resolve_settings(
    config_path: Path | None,
    *,
    top_k: int | None,
    high: float | None,
    medium: float | None,
    max_lines: int | None,
) -> DigestSettings:
    """Apply bundled defaults, JSON defaults, then explicit CLI overrides."""
    values: dict[str, Any] = {
        "top_k": DEFAULT_TOP_K,
        "high": DEFAULT_HIGH,
        "medium": DEFAULT_MEDIUM,
        "max_lines": DEFAULT_MAX_LINES,
    }
    values.update(_load_json(config_path))
    cli_values = {"top_k": top_k, "high": high, "medium": medium, "max_lines": max_lines}
    values.update({name: value for name, value in cli_values.items() if value is not None})

    settings = DigestSettings(
        top_k=_require_int("top_k", values["top_k"]),
        high=_require_float("high", values["high"]),
        medium=_require_float("medium", values["medium"]),
        max_lines=_require_int("max_lines", values["max_lines"]),
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
