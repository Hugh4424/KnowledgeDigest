"""Deterministic, confirmed-only threshold calibration and adoption gate."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any, Iterable

from .config import DEFAULT_HIGH, DEFAULT_MEDIUM
from .errors import ValidationError

BACKENDS = ("jaccard", "embedding")
STAGES = ("S2", "S3")
LABELS = ("positive", "negative")
_CASE_FIELDS = frozenset(
    {
        "case_id",
        "lineage_id",
        "content_identity",
        "label_version",
        "stage",
        "label",
        "stratum",
        "confirmed",
        "scores",
        "outcomes",
        "gold_action",
        "split",
        "vector_hashes",
        "vector_manifest_hash",
        "gold_case_hash",
        "query_id",
    }
)
_OUTCOME_FIELDS = frozenset(
    {
        "correct",
        "error",
        "predicted_positive",
        "action_correct",
        "predicted_action",
        "predicted_tier",
        "tier_high",
        "tier_medium",
        "observed_clusters",
    }
)
_S2_RELATIONS = {"mergeable", "not_mergeable"}
_SIMILARITY_BANDS = {"high", "medium", "low"}
_S3_ACTIONS = {"new", "revise", "merge_multiple"}


class CalibrationBlocked(RuntimeError):
    """The approved embedding service was unavailable; no artifact is valid."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.evidence = {"result": "BLOCKED", "reason_code": reason_code}


def _finite_score(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("calibration", field, "score must be numeric")
    score = float(value)
    if not math.isfinite(score):
        raise ValidationError("calibration", field, "score must be finite")
    return score


def _validate_stratum(case: dict[str, Any]) -> None:
    stratum = case.get("stratum")
    if not isinstance(stratum, dict):
        raise ValidationError("calibration", case["case_id"], "stratum must be an object")
    if case["stage"] == "S2":
        if (
            set(stratum) != {"relation", "similarity_band"}
            or stratum["relation"] not in _S2_RELATIONS
            or stratum["similarity_band"] not in _SIMILARITY_BANDS
        ):
            raise ValidationError("calibration", case["case_id"], "invalid S2 stratum")
        expected_label = "positive" if stratum["relation"] == "mergeable" else "negative"
    else:
        if (
            set(stratum) != {"action", "target_in_top_k"}
            or stratum["action"] not in _S3_ACTIONS
            or not isinstance(stratum["target_in_top_k"], bool)
        ):
            raise ValidationError("calibration", case["case_id"], "invalid S3 stratum")
        expected_label = "positive" if stratum["target_in_top_k"] else "negative"
    if case["label"] != expected_label:
        raise ValidationError("calibration", case["case_id"], "label conflicts with stratum")


def _quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValidationError("calibration", "quantile", "distribution is empty")
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _distribution(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "quantiles": {
            "p25": _quantile(values, 0.25),
            "p50": _quantile(values, 0.50),
            "p75": _quantile(values, 0.75),
        },
    }


def _validate_cases(cases: Iterable[dict[str, Any]], *, require_split: bool) -> list[dict[str, Any]]:
    materialized = list(cases)
    if not materialized:
        raise ValidationError("calibration", "cases", "must not be empty")
    seen_ids: set[str] = set()
    for case in materialized:
        if not isinstance(case, dict):
            raise ValidationError("calibration", "case", "must be an object")
        expected_fields = _CASE_FIELDS if require_split else _CASE_FIELDS - {"split"}
        if set(case) != expected_fields:
            raise ValidationError(
                "calibration", "case", "case fields must match the exact schema"
            )
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in seen_ids:
            raise ValidationError("calibration", "case_id", "must be unique and non-empty")
        seen_ids.add(case_id)
        if case.get("confirmed") is not True:
            raise ValidationError("calibration", case_id, "only confirmed gold is allowed")
        if not isinstance(case.get("lineage_id"), str) or not case["lineage_id"]:
            raise ValidationError("calibration", case_id, "lineage_id is required")
        content_identity = case.get("content_identity")
        if (
            not isinstance(content_identity, str)
            or len(content_identity) != 64
            or any(ch not in "0123456789abcdef" for ch in content_identity)
        ):
            raise ValidationError(
                "calibration", case_id, "content_identity must be sha256"
            )
        if not isinstance(case.get("label_version"), str) or not case["label_version"]:
            raise ValidationError("calibration", case_id, "label_version is required")
        if case.get("stage") not in STAGES or case.get("label") not in LABELS:
            raise ValidationError("calibration", case_id, "invalid stage or label")
        _validate_stratum(case)
        scores = case.get("scores")
        if not isinstance(scores, dict) or set(scores) != set(BACKENDS):
            raise ValidationError("calibration", case_id, "both backend scores are required")
        for backend in BACKENDS:
            _finite_score(scores[backend], f"{case_id}.{backend}")
        outcomes = case.get("outcomes")
        if not isinstance(outcomes, dict) or set(outcomes) != set(BACKENDS):
            raise ValidationError(
                "calibration", case_id, "both backend outcomes are required"
            )
        for backend in BACKENDS:
            outcome = outcomes[backend]
            if not isinstance(outcome, dict) or not set(outcome) <= _OUTCOME_FIELDS:
                raise ValidationError(
                    "calibration", case_id, f"invalid {backend} outcome"
                )
        hashes = case["vector_hashes"]
        if not isinstance(hashes, dict) or set(hashes) != {"left", "right"}:
            raise ValidationError("calibration", case_id, "vector_hashes are invalid")
        for item in hashes.values():
            if not isinstance(item, str) or len(item) != 64 or any(ch not in "0123456789abcdef" for ch in item):
                raise ValidationError("calibration", case_id, "vector hash must be sha256")
        for field in ("gold_case_hash", "vector_manifest_hash"):
            item = case[field]
            if not isinstance(item, str) or len(item) != 64 or any(ch not in "0123456789abcdef" for ch in item):
                raise ValidationError("calibration", case_id, f"{field} must be sha256")
        if not isinstance(case["query_id"], str) or not case["query_id"]:
            raise ValidationError("calibration", case_id, "query_id is required")
        if require_split and case.get("split") not in {"calibration", "holdout"}:
            raise ValidationError("calibration", case_id, "split is required")
    return materialized


def _stratum_key(case: dict[str, Any]) -> str:
    return json.dumps(case["stratum"], sort_keys=True, separators=(",", ":"))


def strict_lineage_split(cases: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Split every stratum by lineage with deterministic ordering and no leakage."""
    rows = _validate_cases(cases, require_split=False)
    lineages: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lineage_strata: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for case in rows:
        lineage = case["lineage_id"]
        lineages[lineage].append(case)
        lineage_strata[lineage].add((case["stage"], case["label"], _stratum_key(case)))
    by_stratum: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for lineage, strata in lineage_strata.items():
        for cell in strata:
            by_stratum[cell].append(lineage)
    coverable_strata = {
        cell: members
        for cell, members in by_stratum.items()
        if len(set(members)) >= 2
    }
    ordered_lineages = sorted(
        lineages,
        key=lambda value: (
            -len(lineage_strata[value]),
            hashlib.sha256(value.encode("utf-8")).hexdigest(),
            value,
        ),
    )
    assignment: dict[str, str] = {}

    def search(index: int) -> bool:
        if index == len(ordered_lineages):
            return all(
                {assignment[lineage] for lineage in members} == {"calibration", "holdout"}
                for members in coverable_strata.values()
            )
        lineage = ordered_lineages[index]
        preferred = (
            "calibration"
            if int(hashlib.sha256(lineage.encode()).hexdigest(), 16) % 2 == 0
            else "holdout"
        )
        for split in (preferred, "holdout" if preferred == "calibration" else "calibration"):
            assignment[lineage] = split
            impossible = False
            for members in coverable_strata.values():
                assigned = {assignment[item] for item in members if item in assignment}
                if len(assigned) == 1 and all(item in assignment for item in members):
                    impossible = True
                    break
            if not impossible and search(index + 1):
                return True
        assignment.pop(lineage, None)
        return False

    if not search(0):
        raise ValidationError(
            "calibration", "coverage", "strict lineage split cannot cover both sets"
        )
    return [
        {**case, "split": assignment[case["lineage_id"]]}
        for case in sorted(rows, key=lambda item: item["case_id"])
    ]


def _coverage_audit(cases: list[dict[str, Any]]) -> dict[str, Any]:
    calibration_lineages = {
        case["lineage_id"] for case in cases if case["split"] == "calibration"
    }
    holdout_lineages = {case["lineage_id"] for case in cases if case["split"] == "holdout"}
    intersection = sorted(calibration_lineages & holdout_lineages)
    if intersection:
        raise ValidationError("calibration", "lineage", "lineage crosses split boundary")
    cells: dict[str, dict[str, int]] = {}
    for case in cases:
        key = f"{case['stage']}|{case['label']}|{_stratum_key(case)}"
        cells.setdefault(key, {"calibration": 0, "holdout": 0})
        cells[key][case["split"]] += 1
    missing = sorted(
        f"{key}|split={split}"
        for key, counts in cells.items()
        for split, count in counts.items()
        if count == 0
    )
    required_cells = {
        f"S2|{label}|{json.dumps({'relation': relation, 'similarity_band': band}, sort_keys=True, separators=(',', ':'))}"
        for relation, label in (("mergeable", "positive"), ("not_mergeable", "negative"))
        for band in sorted(_SIMILARITY_BANDS)
    } | {
        f"S3|{'positive' if target else 'negative'}|{json.dumps({'action': action, 'target_in_top_k': target}, sort_keys=True, separators=(',', ':'))}"
        for action in sorted(_S3_ACTIONS)
        for target in (False, True)
    }
    missing_required_cells = sorted(
        f"{key}|split={split}"
        for key in required_cells - set(cells)
        for split in ("calibration", "holdout")
    )
    # Exact strict cells are the expansion contract; stage/label gaps are
    # derivable from them and would only duplicate the requested work.
    undecidable = sorted(set(missing + missing_required_cells))
    return {
        "schema_version": "split-coverage-audit.v1",
        "lineage_intersection": intersection,
        "cells": {key: cells[key] for key in sorted(cells)},
        "missing_cells": undecidable,
        "undecidable_cells": undecidable,
        "all_metric_denominators_nonzero": not undecidable,
    }


def coverage_audit(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return the strict split expansion contract without running metrics."""
    return _coverage_audit(_validate_cases(cases, require_split=True))


def feature_separation(
    cases: Iterable[dict[str, Any]], split: str = "calibration"
) -> dict[str, Any]:
    rows = _validate_cases(cases, require_split=True)
    if split not in {"calibration", "holdout"}:
        raise ValidationError("calibration", "split", "invalid split")
    result: dict[str, Any] = {}
    for stage in STAGES:
        result[stage] = {}
        for backend in BACKENDS:
            positive = [
                _finite_score(case["scores"][backend], backend)
                for case in rows
                if case["split"] == split
                and case["stage"] == stage
                and case["label"] == "positive"
            ]
            negative = [
                _finite_score(case["scores"][backend], backend)
                for case in rows
                if case["split"] == split
                and case["stage"] == stage
                and case["label"] == "negative"
            ]
            if not positive or not negative:
                raise ValidationError("calibration", "coverage", "score class is empty")
            overlap_count = sum(
                1 for score in positive if score <= max(negative)
            ) + sum(1 for score in negative if score >= min(positive))
            result[stage][backend] = {
                "positive": _distribution(positive),
                "negative": _distribution(negative),
                "overlap_count": overlap_count,
                "overlap_rate": overlap_count / (len(positive) + len(negative)),
                "margin": min(positive) - max(negative),
            }
    return result


def _predicted_positive(case: dict[str, Any], backend: str) -> bool:
    outcome = case.get("outcomes", {}).get(backend, {})
    if isinstance(outcome.get("predicted_positive"), bool):
        return outcome["predicted_positive"]
    correct = outcome.get("correct")
    if not isinstance(correct, bool):
        raise ValidationError(
            "calibration", case["case_id"], "outcome correctness is required"
        )
    positive = case["label"] == "positive"
    return positive if correct else not positive


def _classification_metrics(cases: list[dict[str, Any]], backend: str) -> dict[str, float]:
    true_positive = false_positive = false_negative = 0
    for case in cases:
        actual = case["label"] == "positive"
        predicted = _predicted_positive(case, backend)
        true_positive += int(actual and predicted)
        false_positive += int(not actual and predicted)
        false_negative += int(actual and not predicted)
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    if precision_denominator == 0 or recall_denominator == 0:
        raise ValidationError("calibration", "metrics", "metric denominator is zero")
    precision = true_positive / precision_denominator
    recall = true_positive / recall_denominator
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def _metric_denominator_gaps(cases: list[dict[str, Any]]) -> list[str]:
    gaps: list[str] = []
    holdout = [case for case in cases if case["split"] == "holdout"]
    for stage in STAGES:
        stage_cases = [case for case in holdout if case["stage"] == stage]
        for backend in BACKENDS:
            true_positive = false_positive = false_negative = 0
            for case in stage_cases:
                actual = case["label"] == "positive"
                predicted = _predicted_positive(case, backend)
                true_positive += int(actual and predicted)
                false_positive += int(not actual and predicted)
                false_negative += int(actual and not predicted)
            if true_positive + false_positive == 0:
                gaps.append(f"{stage}|{backend}|precision|predicted_positive")
            if true_positive + false_negative == 0:
                gaps.append(f"{stage}|{backend}|recall|gold_positive")
    return gaps


def _complete_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    holdout = [case for case in cases if case["split"] == "holdout"]
    metrics: dict[str, Any] = {"S2": {}, "S3": {}}
    for backend in BACKENDS:
        s2 = [case for case in holdout if case["stage"] == "S2"]
        s3 = [case for case in holdout if case["stage"] == "S3"]
        metrics["S2"][backend] = _classification_metrics(s2, backend)
        page = _classification_metrics(s3, backend)
        action_by_query: dict[str, bool] = {}
        for case in s3:
            outcome = case.get("outcomes", {}).get(backend, {})
            if "predicted_action" in outcome and "gold_action" in case:
                value = outcome["predicted_action"] == case["gold_action"]
            else:
                value = outcome.get("action_correct", outcome.get("correct"))
            if not isinstance(value, bool):
                raise ValidationError(
                    "calibration", case["case_id"], "S3 action outcome is required"
                )
            query_id = case.get("query_id")
            if not isinstance(query_id, str) or not query_id:
                raise ValidationError("calibration", case["case_id"], "S3 query_id is required")
            if query_id in action_by_query and action_by_query[query_id] != value:
                raise ValidationError("calibration", query_id, "query action outcomes conflict")
            action_by_query[query_id] = value
        metrics["S3"][backend] = {
            "page_precision": page["precision"],
            "page_recall": page["recall"],
            "page_f1": page["f1"],
            "action_exact_accuracy": sum(action_by_query.values()) / len(action_by_query),
        }
    return metrics


def _thresholds(separation: dict[str, Any]) -> tuple[dict[str, float], dict[str, Any]]:
    s2 = separation["S2"]["embedding"]
    s3 = separation["S3"]["embedding"]
    s2_midpoint = (s2["positive"]["min"] + s2["negative"]["max"]) / 2
    s3_midpoint = (s3["positive"]["min"] + s3["negative"]["max"]) / 2
    high = s2["positive"]["quantiles"]["p50"]
    values = {
        "high": high,
        "medium": min(high, s2_midpoint),
        "page_match_threshold": s3_midpoint,
    }
    provenance = {
        "source_split": "calibration",
        "method": "deterministic-positive-median-and-class-midpoint.v1",
        "candidates": {
            "high": {"stage": "S2", "statistic": "positive.p50", "value": high},
            "medium": {"stage": "S2", "statistic": "class_midpoint", "value": values["medium"]},
            "page_match_threshold": {
                "stage": "S3",
                "statistic": "class_midpoint",
                "value": s3_midpoint,
            },
        },
    }
    return values, provenance


def _partial_feature_separation(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep incomplete calibration evidence machine-readable without inventing data."""
    result: dict[str, Any] = {}
    for stage in STAGES:
        result[stage] = {}
        for backend in BACKENDS:
            classes: dict[str, Any] = {}
            for label in LABELS:
                values = [
                    _finite_score(case["scores"][backend], backend)
                    for case in cases
                    if case["split"] == "calibration"
                    and case["stage"] == stage
                    and case["label"] == label
                ]
                classes[label] = _distribution(values) if values else None
            result[stage][backend] = {
                **classes,
                "status": "insufficient_coverage",
                "overlap_count": None,
                "overlap_rate": None,
                "margin": None,
            }
    return result


def _tier_distribution(
    cases: list[dict[str, Any]], thresholds: dict[str, float]
) -> dict[str, Any]:
    """Diagnostic-only S2 holdout pair score bands for both backends."""

    def counts(backend: str, high: float, medium: float) -> tuple[dict[str, int], bool]:
        result = {"auto": 0, "needs_review": 0, "insufficient_signal": 0}
        observed: dict[str, str] = {}
        pair_cases: list[dict[str, Any]] = []
        for case in cases:
            if case["split"] != "holdout" or case["stage"] != "S2":
                continue
            pair_cases.append(case)
            clusters = case["outcomes"][backend].get("observed_clusters")
            if isinstance(clusters, list):
                for cluster in clusters:
                    if (
                        isinstance(cluster, dict)
                        and isinstance(cluster.get("cluster_id"), str)
                        and cluster.get("tier") in result
                    ):
                        existing = observed.setdefault(
                            cluster["cluster_id"], cluster["tier"]
                        )
                        if existing != cluster["tier"]:
                            raise ValidationError(
                                "calibration",
                                cluster["cluster_id"],
                                "cluster tier conflicts across cases",
                            )
        if observed:
            for tier in observed.values():
                result[tier] += 1
            return result, True
        for case in pair_cases:
            tier = case["outcomes"][backend].get("predicted_tier")
            if tier not in result:
                score = _finite_score(case["scores"][backend], backend)
                tier = (
                    "auto"
                    if score >= high
                    else "needs_review"
                    if score >= medium
                    else "insufficient_signal"
                )
            result[tier] += 1
        return result, False

    def recorded_threshold(backend: str, name: str, fallback: float) -> float:
        values = {
            case["outcomes"][backend].get(name)
            for case in cases
            if case["split"] == "holdout" and case["stage"] == "S2"
        }
        numeric = {
            float(value)
            for value in values
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        return next(iter(numeric)) if len(numeric) == 1 else fallback

    jaccard_high = recorded_threshold("jaccard", "tier_high", DEFAULT_HIGH)
    jaccard_medium = recorded_threshold("jaccard", "tier_medium", DEFAULT_MEDIUM)
    jaccard_counts, jaccard_actual = counts(
        "jaccard", jaccard_high, jaccard_medium
    )
    embedding_counts, embedding_actual = counts(
        "embedding", thresholds["high"], thresholds["medium"]
    )
    return {
        "basis": (
            "holdout-s2-observed-unique-cluster-tiers.v1"
            if jaccard_actual and embedding_actual
            else "holdout-s2-pair-score-bands.v1"
        ),
        "gate_effect": "diagnostic_only",
        "jaccard": {
            "thresholds": {"high": jaccard_high, "medium": jaccard_medium},
            "counts": jaccard_counts,
        },
        "embedding": {
            "thresholds": {
                "high": thresholds["high"],
                "medium": thresholds["medium"],
            },
            "counts": embedding_counts,
        },
    }


def _new_errors(cases: list[dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"S2": [], "S3": []}
    for case in cases:
        if case["split"] != "holdout":
            continue
        outcomes = case.get("outcomes", {})
        jaccard = outcomes.get("jaccard", {})
        embedding = outcomes.get("embedding", {})
        jaccard_error = _outcome_error(case, "jaccard")
        embedding_error = _outcome_error(case, "embedding")
        if embedding_error and not jaccard_error:
            result[case["stage"]].append(case["case_id"])
    return {stage: sorted(ids) for stage, ids in result.items()}


def _outcome_error(case: dict[str, Any], backend: str) -> bool:
    outcome = case["outcomes"][backend]
    if isinstance(outcome.get("error"), bool):
        return outcome["error"]
    if isinstance(outcome.get("correct"), bool):
        return not outcome["correct"]
    return _predicted_positive(case, backend) != (case["label"] == "positive")


def _adoption_allowed(metrics: dict[str, Any], new_errors: dict[str, list[str]]) -> bool:
    if any(new_errors.values()):
        return False
    pairs: list[tuple[float, float]] = []
    for metric in ("precision", "recall", "f1"):
        pairs.append((metrics["S2"]["jaccard"][metric], metrics["S2"]["embedding"][metric]))
    for metric in ("page_precision", "page_recall", "page_f1", "action_exact_accuracy"):
        pairs.append((metrics["S3"]["jaccard"][metric], metrics["S3"]["embedding"][metric]))
    return all(embedding >= jaccard for jaccard, embedding in pairs) and any(
        embedding > jaccard for jaccard, embedding in pairs
    )


def build_calibration_result(
    cases: Iterable[dict[str, Any]],
    *,
    service_failure_code: str | None = None,
) -> dict[str, Any]:
    """Build deterministic metrics and adoption status from frozen scored cases."""
    if service_failure_code is not None:
        if not isinstance(service_failure_code, str) or not service_failure_code:
            raise ValidationError("calibration", "service_failure_code", "must be non-empty")
        raise CalibrationBlocked(service_failure_code)
    rows = _validate_cases(cases, require_split=True)
    coverage = _coverage_audit(rows)
    if coverage["undecidable_cells"]:
        return {
            "adoption_status": "not_adopted",
            "metrics": {
                "feature_separation": _partial_feature_separation(rows),
                "threshold_provenance": None,
                "holdout": None,
                "new_errors": {"S2": [], "S3": []},
                "coverage": coverage,
                "tier_distribution": None,
                "status": "insufficient_coverage",
            },
            "cases": sorted(rows, key=lambda case: case["case_id"]),
        }
    separation = feature_separation(rows, "calibration")
    thresholds, provenance = _thresholds(separation)
    denominator_gaps = _metric_denominator_gaps(rows)
    if denominator_gaps:
        coverage["all_metric_denominators_nonzero"] = False
        coverage["undecidable_cells"] = denominator_gaps
        coverage["missing_cells"] = denominator_gaps
        return {
            "adoption_status": "not_adopted",
            "metrics": {
                "feature_separation": separation,
                "threshold_provenance": provenance,
                "holdout": None,
                "new_errors": {"S2": [], "S3": []},
                "coverage": coverage,
                "tier_distribution": _tier_distribution(rows, thresholds),
                "status": "zero_metric_denominator",
            },
            "cases": sorted(rows, key=lambda case: case["case_id"]),
        }
    try:
        complete = _complete_metrics(rows)
    except ValidationError as exc:
        if exc.failed_input != "metrics" or exc.reason != "metric denominator is zero":
            raise
        coverage["all_metric_denominators_nonzero"] = False
        coverage["undecidable_cells"] = ["holdout|unknown_metric_denominator"]
        coverage["missing_cells"] = ["holdout|unknown_metric_denominator"]
        return {
            "adoption_status": "not_adopted",
            "metrics": {
                "feature_separation": separation,
                "threshold_provenance": provenance,
                "holdout": None,
                "new_errors": {"S2": [], "S3": []},
                "coverage": coverage,
                "tier_distribution": _tier_distribution(rows, thresholds),
                "status": "zero_metric_denominator",
            },
            "cases": sorted(rows, key=lambda case: case["case_id"]),
        }
    errors = _new_errors(rows)
    adopted = _adoption_allowed(complete, errors)
    metrics = {
        "feature_separation": separation,
        "threshold_provenance": provenance,
        "holdout": complete,
        "new_errors": errors,
        "coverage": coverage,
        "tier_distribution": _tier_distribution(rows, thresholds),
        "status": "complete",
    }
    result: dict[str, Any] = {
        "adoption_status": "adopted" if adopted else "not_adopted",
        "metrics": metrics,
        "cases": sorted(rows, key=lambda case: case["case_id"]),
    }
    if adopted:
        result["thresholds"] = thresholds
    return result
