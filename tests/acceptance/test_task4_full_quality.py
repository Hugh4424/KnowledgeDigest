from __future__ import annotations

import json
from pathlib import Path

from knowledge_digest.task4_reader_quality import assess_reader_quality, compile_full_reader

from test_task4_full_compiler import _config, _source


def _candidate(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    (raw / "raw/位置字段.md").write_text(_source(1, title="位置字段筛选", topic="location-filter"), encoding="utf-8")
    (raw / "raw/终端管理.md").write_text(_source(2, title="终端设备管理", topic="terminal-management"), encoding="utf-8")
    output = tmp_path / "candidate"
    assert compile_full_reader(raw, output, _config(tmp_path, count=2))["status"] == "candidate"
    return output


def _companybrain(path: Path) -> Path:
    page = path / "products/GoInsight/模块/位置字段筛选.md"
    page.parent.mkdir(parents=True)
    (path / "Home.md").write_text("# CompanyBrain\n\n- [产品](products/index.md)\n", encoding="utf-8")
    (path / "products/index.md").write_text("# 产品\n\n- [GoInsight](GoInsight/index.md)\n", encoding="utf-8")
    (path / "products/GoInsight/index.md").write_text("# GoInsight\n\n- [模块](模块/index.md)\n", encoding="utf-8")
    (path / "products/GoInsight/模块/index.md").write_text("# 模块\n\n- [位置字段筛选](位置字段筛选.md)\n", encoding="utf-8")
    page.write_text(
        "# 位置字段筛选\n\n## Summary\n\n位置字段筛选用于定位设备。\n\n"
        "## 答案\n\n- 打开功能入口并选择目标对象。\n\n"
        "## 规则和边界\n\n- 权限不足时不能执行。\n\n"
        "## 来源\n\n- 文档来源可回查。\n",
        encoding="utf-8",
    )
    return path


def _quality_config(path: Path, *, companybrain_match: str = "products/GoInsight/模块/位置字段筛选.md") -> Path:
    value = {
        "schema_version": "task4-reader-quality.v1",
        "protocol_id": "reader-compare-v1",
        "evaluator_id": "reader-evaluator-v1",
        "source_coverage": {"manifest_id": "fixture-2", "expected_count": 2},
        "case_matrix": {
            "schema_version": "task4-reader-case-matrix.v1",
            "source_to_case_map": [
                {"source_uri": "raw/位置字段.md", "case_id": "case-location"},
                {"source_uri": "raw/终端管理.md", "case_id": "case-terminal"},
            ],
            "cases": [
                {
                    "case_id": "case-location",
                    "canonical_case_id": "location-filter",
                    "comparison_key": "goinsight/数据分析/位置字段筛选/操作/procedure",
                    "target_title": "位置字段筛选",
                    "page_type": "procedure",
                    "criticality": "critical",
                    "required_claims": ["打开功能入口", "选择目标对象"],
                    "required_boundaries": ["权限不足"],
                    "companybrain_entry_path": companybrain_match,
                },
                {
                    "case_id": "case-terminal",
                    "canonical_case_id": "terminal-management",
                    "comparison_key": "goinsight/数据分析/终端设备管理/操作/procedure",
                    "target_title": "终端设备管理",
                    "page_type": "procedure",
                    "criticality": "non_critical",
                    "required_claims": ["打开功能入口", "保存配置"],
                    "required_boundaries": ["权限不足"],
                    "companybrain_entry_path": None,
                    "companybrain_not_applicable_reason": "CompanyBrain基线没有该主题",
                },
            ],
        },
        "page_types": {"procedure": {"required_sections": ["Summary", "答案", "规则和边界", "相关主题", "来源（简表）"]}},
        "aggregation": {"path": "tuple_first_hit_then_hops", "answer": "fixed_m_average", "boundary": "fixed_m_average"},
    }
    config = path / "quality-config.json"
    config.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return config


def test_full_case_oracle_is_source_bound_and_not_a_placeholder_pair() -> None:
    root = Path(__file__).parents[2]
    matrix = json.loads((root / "config/task4-reader-case-matrix-89-input-oracle-v2.json").read_text(encoding="utf-8"))

    assert len(matrix["cases"]) == 89
    assert matrix["oracle"]["manual_review_required"] is False
    assert matrix["oracle"]["source_content_tree_hash"]
    assert len({tuple(case["required_claims"]) for case in matrix["cases"]}) > 20
    assert all(case["oracle_source"]["content_hash"] for case in matrix["cases"])


def test_machine_evaluator_covers_deduplicated_cases_without_human_table(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    companybrain = _companybrain(tmp_path / "CompanyBrain")
    result = assess_reader_quality(candidate, companybrain, _quality_config(tmp_path), tmp_path / "assessment")

    # Equal content and equal route is not an automatic "better" claim.
    assert result["status"] == "candidate"
    assert result["release_status"] == "not_released"
    assert result["machine_quality"]["source_count"] == 2
    assert result["comparison"]["case_count"] == 2
    assert result["comparison"]["not_applicable_cases"] == ["case-terminal"]
    assert result["comparison"]["strictly_better_axes"] == []
    assert "human_reviewed" not in json.dumps(result, ensure_ascii=False)
    assert not (tmp_path / "assessment/reports/human-review.json").exists()


def test_machine_evaluator_uses_source_map_before_canonical_case_id(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    companybrain = _companybrain(tmp_path / "CompanyBrain")
    config = _quality_config(tmp_path)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["case_matrix"]["cases"][0]["canonical_case_id"] = "case-id-not-used-by-topic-index"
    config.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    result = assess_reader_quality(candidate, companybrain, config, tmp_path / "assessment")

    first = next(row for row in result["comparison"]["rows"] if row["case_id"] == "case-location")
    assert first["knowledge_digest"]["status"] == "covered"


def test_title_only_source_case_is_neutral_not_undecidable(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    companybrain = _companybrain(tmp_path / "CompanyBrain")
    config = _quality_config(tmp_path)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["case_matrix"]["source_to_case_map"].append({"source_uri": "raw/空白页.md", "case_id": "case-empty"})
    value["case_matrix"]["cases"].append({
        "case_id": "case-empty",
        "canonical_case_id": "empty-source",
        "comparison_key": "source/empty/procedure",
        "target_title": "空白页",
        "page_type": "procedure",
        "criticality": "non_critical",
        "required_claims": ["不会执行"],
        "required_boundaries": ["来源留在 Audit"],
        "companybrain_entry_path": None,
        "source_status": "not_applicable",
        "source_status_reason": "原始页面为空，没有可比较的知识正文",
    })
    config.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    result = assess_reader_quality(candidate, companybrain, config, tmp_path / "assessment")

    row = next(item for item in result["comparison"]["rows"] if item["case_id"] == "case-empty")
    assert row["knowledge_digest"]["status"] == "not_applicable"
    assert row["companybrain"]["status"] == "not_applicable"
    assert "case_topic_mapping_missing" not in result["blocking_reasons"]
    assert "baseline_mapping_undecidable" not in result["blocking_reasons"]


def test_unknown_or_missing_case_oracle_is_undecidable(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    companybrain = _companybrain(tmp_path / "CompanyBrain")
    config = _quality_config(tmp_path)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["case_matrix"]["cases"][0].pop("required_claims")
    config.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    result = assess_reader_quality(candidate, companybrain, config, tmp_path / "assessment")

    assert result["status"] == "undecidable"
    assert "case_oracle_invalid" in result["blocking_reasons"]
    assert result["release_status"] == "not_released"


def test_companybrain_multipath_and_negative_kd_case_cannot_claim_better(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    companybrain = _companybrain(tmp_path / "CompanyBrain")
    config = _quality_config(tmp_path)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["case_matrix"]["cases"][0]["companybrain_entry_path"] = [
        "products/GoInsight/模块/位置字段筛选.md",
        "products/GoInsight/index.md",
    ]
    config.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    result = assess_reader_quality(candidate, companybrain, config, tmp_path / "assessment")

    assert result["status"] == "undecidable"
    assert "baseline_mapping_ambiguous" in result["blocking_reasons"]


def test_unmatched_companybrain_mapping_is_unknown_not_neutral_na(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    companybrain = _companybrain(tmp_path / "CompanyBrain")
    config = _quality_config(tmp_path)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["companybrain_mapping"] = {
        "companybrain_manifest": {"tree_hash": ""},
        "cases": [
            {"case_id": "case-location", "status": "unmatched", "entry_path": None},
            {"case_id": "case-terminal", "status": "not_applicable", "entry_path": None},
        ],
    }
    config.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    result = assess_reader_quality(candidate, companybrain, config, tmp_path / "assessment")

    row = next(row for row in result["comparison"]["rows"] if row["case_id"] == "case-location")
    assert row["companybrain"]["status"] == "unknown"
    assert row["companybrain"].get("unknown_reason")
    assert "baseline_mapping_unmatched" in result["blocking_reasons"]
    assert "case-location" not in result["comparison"]["not_applicable_cases"]


def test_not_released_candidate_is_undecidable_before_case_scoring(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    status = json.loads((candidate / "status.json").read_text(encoding="utf-8"))
    status["package_status"] = "not_released"
    (candidate / "status.json").write_text(json.dumps(status), encoding="utf-8")
    result = assess_reader_quality(candidate, _companybrain(tmp_path / "CompanyBrain"), _quality_config(tmp_path), tmp_path / "assessment")

    assert result["status"] == "undecidable"
    assert "candidate_not_released" in result["blocking_reasons"]


def test_quality_report_has_root_cause_dimensions_and_machine_receipt(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    companybrain = _companybrain(tmp_path / "CompanyBrain")
    result = assess_reader_quality(candidate, companybrain, _quality_config(tmp_path), tmp_path / "assessment")

    for name in ("machine-quality.json", "comparison-table.json", "evaluator-receipt.json", "root-cause.json", "release-summary.json"):
        assert (tmp_path / "assessment/reports" / name).is_file()
    comparison = json.loads((tmp_path / "assessment/reports/comparison-table.json").read_text(encoding="utf-8"))
    assert all(row["case_id"] and row["home"] and row["first_hit_page"] for row in comparison["rows"])
    causes = json.loads((tmp_path / "assessment/reports/root-cause.json").read_text(encoding="utf-8"))
    assert {row["dimension"] for row in causes["items"]} >= {"structure", "naming", "classification", "body", "relations", "navigation", "provenance"}
    assert all(row["symptom"] and row["evidence_refs"] and row["first_failing_stage"] for row in causes["items"])
    assert all(row["symptom"] != "机器报告按维度记录" for row in causes["items"])
    receipt = json.loads((tmp_path / "assessment/reports/evaluator-receipt.json").read_text(encoding="utf-8"))
    assert receipt["baseline_first"] is True
    assert receipt["network_disabled"] is True
    assert receipt["case_matrix_hash"]
    assert receipt["candidate_run_id"]
    assert receipt["candidate_input_manifest_generation"]
