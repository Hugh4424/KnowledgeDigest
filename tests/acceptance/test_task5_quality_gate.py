from __future__ import annotations

from knowledge_digest.quality import load_quality_projections
from knowledge_digest.task5_quality_gate import DIMENSIONS, EXPECTED_PROJECTION_IDS, _public_result, strict_winner

import importlib.util
from pathlib import Path


_evaluator_spec = importlib.util.spec_from_file_location(
    "task5_reader_quality_evaluator",
    Path(__file__).parents[2] / "scripts" / "evaluate_reader_candidate.py",
)
assert _evaluator_spec and _evaluator_spec.loader
_evaluator = importlib.util.module_from_spec(_evaluator_spec)
_evaluator_spec.loader.exec_module(_evaluator)


def _winning_result():
    rows = []
    gap_types = {
        "DIM-01.route": "wrong_relation",
        "DIM-02.taxonomy": "missing_taxonomy_axis",
        "DIM-03.business-answer": "missing_stage",
        "DIM-04.page-type": "untyped_contract",
        "DIM-05.reader-audit": "missing_provenance",
    }
    for projection_id in EXPECTED_PROJECTION_IDS:
        for dimension in DIMENSIONS:
            rows.append({
                "projection_key": projection_id,
                "dimension_id": dimension,
                "verdict": "KD_WIN",
                "kd_observation_ref": "reader-observation",
                "cb_observation_ref": "companybrain-observation",
                "observation_digests": {"reader": "c" * 64, "companybrain": "b" * 64},
                "advantage_basis": {
                    "projection_key": projection_id,
                    "dimension_id": dimension,
                    "cb_observation_ref": "companybrain-observation",
                    "cb_observation_digest": "b" * 64,
                    "cb_gap_type": gap_types[dimension],
                    "cb_gap_locator": "CompanyBrain/page#anchor",
                    "atom_observations": [{"atom_id": "atom", "applicable": True, "cb_status": "absent", "kd_status": "present", "cb_evidence_refs": ["cb"], "kd_evidence_refs": ["kd"], "relation": "strict_improvement"}],
                    "gap_atom_refs": ["atom"],
                    "stage_observations": [],
                    "gap_stage_refs": [],
                    "quality_feature_observations": [],
                    "gap_quality_feature_refs": [],
                    "strict_improvement_refs": ["atom"],
                    "non_regression": True,
                    "judge_decisions": ["KD_WIN", "KD_WIN"],
                    "kd_completion_refs": ["kd"],
                    "kd_completion_surfaces": ["Reader", "Audit"],
                    "kd_completion_digest": "c" * 64,
                },
            })
    return {
        "schema_version": "task5-quality-result.v3",
        "dimension_verdicts": {projection_id: {dimension: ["KD_WIN", "KD_WIN"] for dimension in DIMENSIONS} for projection_id in EXPECTED_PROJECTION_IDS},
        "quality_rows": rows,
        "candidate_tree_sha256": "d" * 64,
        "published_tree_sha256": "d" * 64,
        "quality_result_status": "released",
        "verdict": "released",
        "hard_blockers": [],
        "judge_errors": [],
    }


def test_quality_gate_requires_every_dimension_to_win_twice():
    result = _winning_result()
    assert strict_winner(result)
    result["dimension_verdicts"][EXPECTED_PROJECTION_IDS[0]]["DIM-01.route"] = ["KD_WIN", "UNKNOWN"]
    assert not strict_winner(result)


def test_quality_gate_requires_exact_projection_dimension_matrix():
    result = _winning_result()
    assert strict_winner(result)

    missing = _winning_result()
    missing["quality_rows"].pop()
    assert not strict_winner(missing)

    duplicate = _winning_result()
    duplicate["quality_rows"].append(dict(duplicate["quality_rows"][0]))
    assert not strict_winner(duplicate)

    extra = _winning_result()
    extra["quality_rows"].append({"projection_key": "unexpected", "dimension_id": "DIM-01.route", "verdict": "KD_WIN"})
    assert not strict_winner(extra)

    not_applicable = _winning_result()
    not_applicable["quality_rows"][0]["verdict"] = "N/A"
    assert not strict_winner(not_applicable)


def test_evaluator_uses_frozen_manifest_file_hash_for_formal_runs(tmp_path):
    manifest = tmp_path / "source-manifest.json"
    manifest.write_bytes(b'{"frozen":true}\n')

    expected = _evaluator._expected_source_manifest_hash(
        {"manifest": {"sources": []}}, manifest
    )

    import hashlib

    assert expected == hashlib.sha256(manifest.read_bytes()).hexdigest()


def test_frozen_projection_product_matches_its_source_ownership():
    root = Path(__file__).parents[2]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )
    by_id = {projection.projection_id: projection for projection in projections}
    assert by_id["Q-POS-01.positioning"].axes["product"] == "EMM"
    assert by_id["Q-CON-01.concept"].axes["product"] == "EMM for Android"
    assert by_id["Q-OPR-01.qr.operation"].axes["product"] == "EMM for Android"
    assert by_id["Q-OPR-01.zero-touch.operation"].axes["product"] == "EMM for Android"
    assert by_id["Q-BND-01.operation"].axes["product"] == "Merchant System"
    assert by_id["Q-BND-01.diagnosis"].axes["product"] == "Merchant System"


def test_quality_gate_rejects_static_basis_without_blind_judge_receipt():
    result = _winning_result()
    result["quality_rows"][0]["advantage_basis"].pop("judge_decisions")
    assert not strict_winner(result)


def test_quality_gate_rejects_legacy_judge_only_result():
    result = {"verdict": "released", "hard_blockers": [], "judge_errors": [], "dimension_verdicts": {"Q-1": {dimension: ["KD_WIN", "KD_WIN"] for dimension in DIMENSIONS}}}
    assert not strict_winner(result)


def test_quality_gate_rejects_missing_advantage_basis():
    result = _winning_result()
    result["quality_rows"][0]["advantage_basis"] = None
    assert not strict_winner(result)


def test_public_result_does_not_promote_judge_only_result():
    projections = []
    rounds = [[], []]
    dimension_verdicts = {}
    for projection_id in EXPECTED_PROJECTION_IDS:
        projection = {
            "projection_id": projection_id,
            "candidate_page_paths": [f"products/shared/operation/{projection_id}.md"],
            "companybrain_page_paths": [f"Products/{projection_id}.md"],
            "companybrain_baseline_checks": [{"baseline_id": f"cb-{projection_id}", "exists": True, "hash_matches": True, "applicability": "present"}],
            "structural_observation": {dimension: {"passed": True} for dimension in ("route", "taxonomy", "business-answer", "page-type", "Reader-Audit")},
        }
        projections.append(projection)
        dimension_verdicts[projection_id] = {dimension: ["KD_WIN", "KD_WIN"] for dimension in DIMENSIONS}
        for round_items in rounds:
            round_items.append({
                "projection_id": projection_id,
                "dimensions": {dimension: {"verdict": "KD_WIN", "reason": "候选页直接回答并保留边界"} for dimension in ("route", "taxonomy", "business-answer", "page-type", "Reader-Audit")},
            })
    result = _public_result({
        "projections": projections,
        "projection_count": len(projections),
        "dimension_verdicts": dimension_verdicts,
        "judgements": rounds,
        "verdict": "released",
        "hard_blockers": [],
        "judge_errors": [],
    })
    result["candidate_tree_sha256"] = "d" * 64
    result["published_tree_sha256"] = "e" * 64
    assert all(row["verdict"] == "UNKNOWN" for row in result["quality_rows"])
    assert not strict_winner(result)


def test_public_result_promotes_only_dimension_bound_basis():
    source_basis = _winning_result()["quality_rows"][0]["advantage_basis"]
    projections = []
    rounds = [[], []]
    for projection_id in EXPECTED_PROJECTION_IDS:
        basis_by_dimension = {}
        for dimension in DIMENSIONS:
            basis = dict(source_basis)
            basis["projection_key"] = projection_id
            basis["dimension_id"] = dimension
            basis_by_dimension[{
                "DIM-01.route": "route",
                "DIM-02.taxonomy": "taxonomy",
                "DIM-03.business-answer": "business-answer",
                "DIM-04.page-type": "page-type",
                "DIM-05.reader-audit": "Reader-Audit",
            }[dimension]] = basis
        projections.append({
            "projection_id": projection_id,
            "structural_observation": {
                "route": {"passed": True},
                "taxonomy": {"passed": True},
                "business-answer": {"passed": True},
                "page-type": {"passed": True},
                "Reader-Audit": {"passed": True},
            },
            "advantage_basis_by_dimension": basis_by_dimension,
        })
        for round_items in rounds:
            round_items.append({
                "projection_id": projection_id,
                "dimensions": {
                    "route": {"verdict": "KD_WIN", "reason": "有具体页面和来源证据"},
                    "taxonomy": {"verdict": "KD_WIN", "reason": "有具体页面和来源证据"},
                    "business-answer": {"verdict": "KD_WIN", "reason": "有具体页面和来源证据"},
                    "page-type": {"verdict": "KD_WIN", "reason": "有具体页面和来源证据"},
                    "Reader-Audit": {"verdict": "KD_WIN", "reason": "有具体页面和来源证据"},
                },
            })
    result = _public_result({
        "projections": projections,
        "projection_count": len(projections),
        "judgements": rounds,
        "verdict": "released",
        "hard_blockers": [],
        "judge_errors": [],
    })

    assert all(row["verdict"] == "KD_WIN" for row in result["quality_rows"])


def test_public_result_keeps_legacy_or_missing_judge_as_unknown():
    result = _public_result({"projections": [{"projection_id": EXPECTED_PROJECTION_IDS[0]}]})
    assert len(result["quality_rows"]) == len(EXPECTED_PROJECTION_IDS) * len(DIMENSIONS)
    assert all(row["verdict"] == "UNKNOWN" for row in result["quality_rows"])


def test_source_bound_basis_is_recomputed_from_companybrain_and_reader_bytes():
    root = Path(__file__).parents[2]
    projection = _evaluator.load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )[0]
    rubric = projection.comparison_rubric["route"]
    candidate_text = "\n".join(
        [
            *rubric["required_atoms"],
            *rubric["structure_markers"],
            "原始地址：`source.md`",
        ]
    )
    material = {
        "projection_id": projection.projection_id,
        "candidate_page_paths": ["products/shared/positioning/answer.md"],
        "companybrain_page_paths": ["Products/EMM/产品定位/产品总览.md"],
        "companybrain_baseline_checks": [
            {
                "baseline_id": "cb-test",
                "path": "Products/EMM/产品定位/产品总览.md",
                "exists": True,
                "hash_matches": True,
                "applicability": "present",
            }
        ],
        "candidate_text": candidate_text,
        "companybrain_text": "",
        "kd_observation_ref": "products/shared/positioning/answer.md#u-test",
        "audit_ref": "Audit.md#evidence-test",
        "structural_observation": {
            "route": {"passed": True},
            "taxonomy": {"passed": True},
            "business-answer": {"passed": True},
            "page-type": {"passed": True},
            "Reader-Audit": {"passed": True},
        },
    }

    basis = _evaluator._build_source_bound_advantage_basis(
        projection, "route", material
    )

    assert basis is not None
    assert basis["projection_key"] == projection.projection_id
    assert basis["dimension_id"] == "DIM-01.route"
    assert basis["cb_gap_type"] == "unreachable"
    assert basis["kd_completion_refs"] == [
        "products/shared/positioning/answer.md#u-test",
        "Audit.md#evidence-test",
    ]
    assert basis["kd_completion_surfaces"] == ["Reader", "Audit"]
    assert basis["strict_improvement_refs"]
    assert all(
        atom["cb_status"] == "absent" and atom["kd_status"] == "present"
        for atom in basis["atom_observations"]
    )
