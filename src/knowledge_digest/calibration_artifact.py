"""Strict, replayable Phase 4 calibration artifact contract."""

from __future__ import annotations

import json
import math
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_COMMON_FIELDS = {
    "schema_version",
    "adoption_status",
    "endpoint_identity",
    "model",
    "dimension",
    "probe_fingerprint",
    "corpus_hash",
    "gold_hash",
    "split_hash",
    "vectors_hash",
    "metrics",
    "cases",
    "tool_version",
}
_HASH_FIELDS = {"probe_fingerprint", "corpus_hash", "gold_hash", "split_hash", "vectors_hash"}


@dataclass(frozen=True)
class CalibrationArtifact:
    value: dict[str, Any]

    @property
    def adoption_status(self) -> str:
        return str(self.value["adoption_status"])

    def __getitem__(self, key: str) -> Any:
        return self.value[key]


def validate_calibration_artifact(value: Any) -> CalibrationArtifact:
    if not isinstance(value, dict):
        raise ValueError("calibration artifact must be an object")
    status = value.get("adoption_status")
    if status not in {"adopted", "not_adopted"}:
        raise ValueError("invalid adoption_status")
    expected = _COMMON_FIELDS | ({"thresholds"} if status == "adopted" else set())
    if set(value) != expected:
        raise ValueError("calibration artifact fields do not match the exact schema")
    if value["schema_version"] != "calibration-artifact.v1":
        raise ValueError("unsupported calibration artifact schema")
    if not isinstance(value["endpoint_identity"], str) or not value["endpoint_identity"]:
        raise ValueError("endpoint_identity is required")
    if not isinstance(value["model"], str) or not value["model"]:
        raise ValueError("model is required")
    if isinstance(value["dimension"], bool) or not isinstance(value["dimension"], int) or value["dimension"] < 1:
        raise ValueError("dimension must be a positive integer")
    for field in _HASH_FIELDS:
        item = value[field]
        if not isinstance(item, str) or len(item) != 64 or any(ch not in "0123456789abcdef" for ch in item):
            raise ValueError(f"{field} must be sha256")
    if not isinstance(value["metrics"], dict) or "feature_separation" not in value["metrics"]:
        raise ValueError("metrics.feature_separation is required")
    if not isinstance(value["cases"], list) or not value["cases"]:
        raise ValueError("cases must be a non-empty list")
    if not isinstance(value["tool_version"], str) or not value["tool_version"]:
        raise ValueError("tool_version is required")
    if status == "adopted":
        thresholds = value["thresholds"]
        if not isinstance(thresholds, dict) or set(thresholds) != {
            "high",
            "medium",
            "page_match_threshold",
        }:
            raise ValueError("adopted thresholds do not match the exact schema")
        if any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(float(item))
            or not 0 <= float(item) <= 1
            for item in thresholds.values()
        ):
            raise ValueError("thresholds must be finite values between 0 and 1")
        if float(thresholds["high"]) < float(thresholds["medium"]):
            raise ValueError("high threshold must be greater than or equal to medium")
    try:
        from .calibration import build_calibration_result

        recomputed = build_calibration_result(value["cases"])
    except Exception as error:
        raise ValueError("calibration artifact cases are not recomputable") from error
    if recomputed["adoption_status"] != status or recomputed["metrics"] != value["metrics"]:
        raise ValueError("calibration artifact metrics or adoption status mismatch")
    if status == "adopted" and recomputed.get("thresholds") != value["thresholds"]:
        raise ValueError("calibration artifact thresholds mismatch")
    ordered = sorted(value["cases"], key=lambda item: item["case_id"])
    split_binding = [
        {
            "case_id": case["case_id"],
            "lineage_id": case["lineage_id"],
            "split": case["split"],
        }
        for case in ordered
    ]
    gold_binding = [case.get("gold_case_hash") for case in ordered]
    vector_manifest_hashes = {case.get("vector_manifest_hash") for case in ordered}
    canonical = lambda item: json.dumps(
        item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if hashlib.sha256(canonical(split_binding)).hexdigest() != value["split_hash"]:
        raise ValueError("calibration artifact split_hash mismatch")
    if any(not isinstance(item, str) for item in gold_binding) or hashlib.sha256(canonical(gold_binding)).hexdigest() != value["gold_hash"]:
        raise ValueError("calibration artifact gold_hash mismatch")
    if vector_manifest_hashes != {value["vectors_hash"]}:
        raise ValueError("calibration artifact vectors_hash mismatch")
    return CalibrationArtifact(dict(value))


def load_calibration_artifact(path: Path) -> CalibrationArtifact:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("calibration artifact is unreadable") from error
    return validate_calibration_artifact(value)
