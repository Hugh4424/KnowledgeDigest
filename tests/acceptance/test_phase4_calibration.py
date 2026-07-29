from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from knowledge_digest.calibration import (
    CalibrationBlocked,
    build_calibration_result,
    coverage_audit,
    feature_separation,
    strict_lineage_split,
)
from knowledge_digest.calibration_cli import main
from knowledge_digest.errors import ValidationError


def _case(
    case_id: str,
    lineage: str,
    stage: str,
    label: str,
    jaccard: float,
    embedding: float,
    *,
    stratum: dict[str, object],
    split: str | None = None,
    jaccard_correct: bool = True,
    embedding_correct: bool = True,
) -> dict[str, object]:
    result: dict[str, object] = {
        "case_id": case_id,
        "lineage_id": lineage,
        "content_identity": hashlib.sha256(case_id.encode()).hexdigest(),
        "label_version": "v1",
        "stage": stage,
        "label": label,
        "stratum": stratum,
        "confirmed": True,
        "gold_action": stratum.get("action"),
        "vector_hashes": {
            "left": hashlib.sha256(f"{case_id}:left".encode()).hexdigest(),
            "right": hashlib.sha256(f"{case_id}:right".encode()).hexdigest(),
        },
        "vector_manifest_hash": "f" * 64,
        "gold_case_hash": hashlib.sha256(f"{case_id}:gold".encode()).hexdigest(),
        "query_id": case_id,
        "scores": {"jaccard": jaccard, "embedding": embedding},
        "outcomes": {
            "jaccard": {"correct": jaccard_correct, "error": not jaccard_correct},
            "embedding": {"correct": embedding_correct, "error": not embedding_correct},
        },
    }
    if split is not None:
        result["split"] = split
    return result


def _complete_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    index = 0
    for split, suffix in (("calibration", "c"), ("holdout", "h")):
        strata = [
            (
                "S2",
                "positive" if relation == "mergeable" else "negative",
                {"relation": relation, "similarity_band": band},
            )
            for relation in ("mergeable", "not_mergeable")
            for band in ("high", "medium", "low")
        ] + [
            (
                "S3",
                "positive" if target else "negative",
                {"action": action, "target_in_top_k": target},
            )
            for action in ("new", "revise", "merge_multiple")
            for target in (False, True)
        ]
        for stage, label, stratum in strata:
            scores = (0.72, 0.90) if label == "positive" else (0.28, 0.10)
            stratum_id = "-".join(str(value) for value in stratum.values())
            for repetition in range(2):
                index += 1
                rows.append(
                    _case(
                        f"{suffix}-{stage}-{stratum_id}-{repetition}",
                        f"lineage-{index}",
                        stage,
                        label,
                        scores[0],
                        scores[1],
                        stratum=stratum,
                        split=split,
                        jaccard_correct=not (
                            split == "holdout" and label == "negative"
                        ),
                    )
                )
    return rows


def _binding_hashes(cases: list[dict[str, object]]) -> tuple[str, str]:
    ordered = sorted(cases, key=lambda item: str(item["case_id"]))
    gold = [case["gold_case_hash"] for case in ordered]
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical(gold)).hexdigest(), str(ordered[0]["vector_manifest_hash"])


def test_feature_separation_is_recomputable_and_thresholds_ignore_holdout() -> None:
    cases = _complete_cases()
    first = build_calibration_result(cases)
    assert first["adoption_status"] == "adopted"
    assert set(first["thresholds"]) == {"high", "medium", "page_match_threshold"}
    assert first["metrics"]["feature_separation"] == feature_separation(cases, "calibration")
    assert first["metrics"]["new_errors"] == {"S2": [], "S3": []}
    assert first["metrics"]["tier_distribution"]["gate_effect"] == "diagnostic_only"
    assert set(first["metrics"]["tier_distribution"]) == {
        "basis",
        "gate_effect",
        "jaccard",
        "embedding",
    }

    changed_holdout = copy.deepcopy(cases)
    for case in changed_holdout:
        if case["split"] == "holdout":
            case["scores"] = {"jaccard": 0.01, "embedding": 0.99}
    second = build_calibration_result(changed_holdout)
    assert second["thresholds"] == first["thresholds"]


def test_adoption_fails_closed_for_missing_cells_leakage_or_new_errors() -> None:
    cases = _complete_cases()
    incomplete = build_calibration_result(
        [
            case
            for case in cases
            if not (
                case["split"] == "holdout"
                and case["stage"] == "S3"
                and case["label"] == "negative"
            )
        ]
    )
    assert incomplete["adoption_status"] == "not_adopted"
    assert "thresholds" not in incomplete
    audit = incomplete["metrics"]["coverage"]
    assert audit["undecidable_cells"] == audit["missing_cells"]
    assert all("split=holdout" in cell for cell in audit["undecidable_cells"])

    leaked = copy.deepcopy(cases)
    leaked[-1]["lineage_id"] = leaked[0]["lineage_id"]
    with pytest.raises(ValidationError, match="lineage"):
        build_calibration_result(leaked)

    worse = copy.deepcopy(cases)
    holdout_s2 = next(
        case
        for case in worse
        if case["split"] == "holdout"
        and case["stage"] == "S2"
        and case["label"] == "positive"
    )
    holdout_s2["outcomes"]["embedding"] = {"correct": False, "error": True}
    result = build_calibration_result(worse)
    assert result["adoption_status"] == "not_adopted"
    assert "thresholds" not in result
    assert result["metrics"]["new_errors"]["S2"] == [holdout_s2["case_id"]]


def test_zero_metric_denominator_lists_expansion_and_stays_not_adopted() -> None:
    cases = _complete_cases()
    for case in cases:
        if case["split"] == "holdout":
            case["outcomes"]["embedding"] = {
                "predicted_positive": False,
                "correct": case["label"] == "negative",
                "error": case["label"] == "positive",
            }
    result = build_calibration_result(cases)
    assert result["adoption_status"] == "not_adopted"
    assert "thresholds" not in result
    assert result["metrics"]["status"] == "zero_metric_denominator"
    assert result["metrics"]["coverage"]["all_metric_denominators_nonzero"] is False
    assert result["metrics"]["coverage"]["undecidable_cells"] == [
        "S2|embedding|precision|predicted_positive",
        "S3|embedding|precision|predicted_positive",
    ]


def test_tier_distribution_deduplicates_observed_clusters() -> None:
    cases = _complete_cases()
    for case in cases:
        if case["split"] == "holdout" and case["stage"] == "S2":
            for backend in ("jaccard", "embedding"):
                case["outcomes"][backend]["observed_clusters"] = [
                    {"cluster_id": f"{backend}-shared", "tier": "needs_review"}
                ]
    distribution = build_calibration_result(cases)["metrics"]["tier_distribution"]
    assert distribution["basis"] == "holdout-s2-observed-unique-cluster-tiers.v1"
    assert distribution["jaccard"]["counts"] == {
        "auto": 0,
        "needs_review": 1,
        "insufficient_signal": 0,
    }
    assert distribution["embedding"]["counts"] == distribution["jaccard"]["counts"]


def test_split_is_deterministic_stratified_and_confirmed_only() -> None:
    unsplit = []
    for n in range(4):
        unsplit.append(
            _case(
                f"a-{n}",
                f"la-{n}",
                "S2",
                "positive",
                0.7,
                0.9,
                stratum={"relation": "mergeable", "similarity_band": "high"},
            )
        )
        unsplit.append(
            _case(
                f"b-{n}",
                f"lb-{n}",
                "S2",
                "negative",
                0.2,
                0.1,
                stratum={"relation": "not_mergeable", "similarity_band": "high"},
            )
        )
        unsplit.append(
            _case(
                f"c-{n}",
                f"lc-{n}",
                "S3",
                "positive",
                0.7,
                0.9,
                stratum={"action": "new", "target_in_top_k": True},
            )
        )
        unsplit.append(
            _case(
                f"d-{n}",
                f"ld-{n}",
                "S3",
                "negative",
                0.2,
                0.1,
                stratum={"action": "new", "target_in_top_k": False},
            )
        )
    assert strict_lineage_split(unsplit) == strict_lineage_split(list(reversed(unsplit)))
    bad = copy.deepcopy(unsplit)
    bad[0]["confirmed"] = False
    with pytest.raises(ValidationError, match="confirmed"):
        strict_lineage_split(bad)


def test_single_lineage_cell_becomes_not_adopted_expansion_evidence() -> None:
    unsplit = [
        {key: value for key, value in case.items() if key != "split"}
        for case in _complete_cases()
        if case["split"] == "calibration"
    ]
    single_cell = unsplit[0]["stratum"]
    reduced = [
        case
        for index, case in enumerate(unsplit)
        if case["stratum"] != single_cell or index == 0
    ]
    split = strict_lineage_split(reduced)
    audit = coverage_audit(split)
    assert audit["undecidable_cells"]
    result = build_calibration_result(split)
    assert result["adoption_status"] == "not_adopted"
    assert result["metrics"]["coverage"]["undecidable_cells"] == audit["undecidable_cells"]


def test_service_unavailable_is_blocked_not_an_artifact() -> None:
    with pytest.raises(CalibrationBlocked) as caught:
        build_calibration_result(_complete_cases(), service_failure_code="service_unavailable")
    assert caught.value.evidence == {
        "result": "BLOCKED",
        "reason_code": "service_unavailable",
    }


def test_cli_writes_exact_artifact_and_preserves_explicit_jaccard(
    tmp_path: Path,
) -> None:
    cases_path = tmp_path / "cases.json"
    artifact_path = tmp_path / "artifact.json"
    split_audit = tmp_path / "split-audit.json"
    config = tmp_path / "config.json"
    recommendation = tmp_path / "recommendation.json"
    complete = _complete_cases()
    cases_path.write_text(json.dumps({"cases": complete}), encoding="utf-8")
    config.write_text(
        json.dumps(
            {
                "similarity": {
                    "backend": "jaccard",
                    "embedding": {"model": "approved-model"},
                }
            }
        ),
        encoding="utf-8",
    )
    recommendation.write_bytes(config.read_bytes())
    before = recommendation.read_bytes()
    digest = "a" * 64
    gold_hash, vectors_hash = _binding_hashes(complete)

    assert (
        main(
            [
                "calibrate",
                "--cases",
                str(cases_path),
                "--output",
                str(artifact_path),
                "--split-audit",
                str(split_audit),
                "--endpoint-identity",
                "https://llm.paxszapp.com:443/v1",
                "--model",
                "approved-model",
                "--dimension",
                "4",
                "--probe-fingerprint",
                digest,
                "--corpus-hash",
                digest,
                "--gold-hash",
                gold_hash,
                "--vectors-hash",
                vectors_hash,
                "--config",
                str(config),
                "--recommended-config",
                str(recommendation),
            ]
        )
        == 0
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert set(artifact) == {
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
        "thresholds",
    }
    assert recommendation.read_bytes() == before
    audit = json.loads(split_audit.read_text(encoding="utf-8"))
    assert audit["lineage_intersection"] == []
    assert audit["undecidable_cells"] == []


def test_cli_blocked_writes_no_artifact(tmp_path: Path) -> None:
    cases = tmp_path / "cases.json"
    artifact = tmp_path / "artifact.json"
    evidence = tmp_path / "BLOCKED.json"
    cases.write_text(json.dumps({"cases": _complete_cases()}), encoding="utf-8")
    digest = "b" * 64
    exit_code = main(
        [
            "calibrate",
            "--cases",
            str(cases),
            "--output",
            str(artifact),
            "--split-audit",
            str(tmp_path / "split.json"),
            "--endpoint-identity",
            "http://127.0.0.1:8000/v1",
            "--model",
            "local",
            "--dimension",
            "4",
            "--probe-fingerprint",
            digest,
            "--corpus-hash",
            digest,
            "--gold-hash",
            digest,
            "--vectors-hash",
            digest,
            "--service-failure-code",
            "service_unavailable",
            "--blocked-evidence",
            str(evidence),
        ]
    )
    assert exit_code == 2
    assert not artifact.exists()
    assert json.loads(evidence.read_text(encoding="utf-8"))["result"] == "BLOCKED"
