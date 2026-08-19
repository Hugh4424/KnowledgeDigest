from __future__ import annotations

from pathlib import Path

from knowledge_digest.companybrain_mapping import build_mapping


def _case(case_id: str, title: str, source_id: str) -> dict[str, str]:
    return {"case_id": case_id, "target_title": title, "source_snapshot_id": source_id}


def _manifest(source_id: str, *, status: str = "valid") -> dict[str, object]:
    return {"entries": [{"source_id": source_id, "source_snapshot_id": source_id, "status": status, "product": "GoInsight", "module": "模块手册/字段与筛选"}]}


def test_mapping_prefers_semantic_page_and_binds_product(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    exact = root / "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"
    distractor = root / "Products/GoInsight/模块手册/字段与筛选/时间字段筛选配置.md"
    exact.parent.mkdir(parents=True)
    exact.write_text("# 文本、数值与位置筛选\n\n位置字段筛选规则。\n", encoding="utf-8")
    distractor.write_text("# 时间字段筛选配置\n\n时间字段规则。\n", encoding="utf-8")

    result = build_mapping(root, [_case("case-1", "位置字段筛选", "source-1")], _manifest("source-1"))

    row = result["cases"][0]
    assert row["status"] == "unique"
    assert row["entry_path"] == "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"
    assert result["companybrain_manifest"]["page_count"] == 2
    assert result["companybrain_manifest"]["file_count"] == 2
    assert result["companybrain_manifest"]["scope"] == "all_regular_non_dotname_files"


def test_manifest_freezes_non_markdown_files_but_ignores_system_noise(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    page = root / "Products/GoInsight/位置字段筛选.md"
    page.parent.mkdir(parents=True)
    page.write_text("# 位置字段筛选\n", encoding="utf-8")
    (root / "_config.json").write_text("{}\n", encoding="utf-8")
    (root / "settings.json").write_text("{}\n", encoding="utf-8")
    (root / ".DS_Store").write_bytes(b"system")

    result = build_mapping(root, [_case("case-1", "位置字段筛选", "source-1")], _manifest("source-1"))

    manifest = result["companybrain_manifest"]
    assert manifest["file_count"] == 3
    assert {entry["path"] for entry in manifest["entries"]} == {
        "Products/GoInsight/位置字段筛选.md",
        "_config.json",
        "settings.json",
    }


def test_failed_source_context_is_not_guessed_as_companybrain_match(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    page = root / "Products/GoInsight/位置字段筛选.md"
    page.parent.mkdir(parents=True)
    page.write_text("# 位置字段筛选\n", encoding="utf-8")

    result = build_mapping(root, [_case("case-1", "位置字段筛选", "source-1")], _manifest("source-1", status="failed"))

    row = result["cases"][0]
    assert row["status"] == "undecidable"
    assert row["entry_path"] is None
    assert row["basis"] == ["source_context_unavailable"]


def test_exact_mapping_uses_explicit_subtopic_heading_not_fuzzy_page_title(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    page = root / "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"
    page.parent.mkdir(parents=True)
    page.write_text("# 文本、数值与位置筛选\n\n## 位置字段筛选\n最少 3 个点。\n", encoding="utf-8")
    case = {
        **_case("case-1", "位置字段筛选", "source-1"),
        "product_or_domain": "GoInsight",
        "module": "模块手册/字段与筛选",
        "object_or_scenario": "位置字段",
        "task": "filter",
        "page_type": "procedure",
    }
    from knowledge_digest.companybrain_mapping import comparison_key
    case["comparison_key"] = comparison_key(
        product_or_domain=case["product_or_domain"],
        module=case["module"],
        object_or_scenario=case["object_or_scenario"],
        task=case["task"],
        page_type=case["page_type"],
    )
    result = build_mapping(root, [case], _manifest("source-1"))
    row = result["cases"][0]
    assert result["mapping_mode"] == "exact_semantic_key_v1"
    assert row["status"] == "unique"
    assert row["entry_path"] == "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"
    assert row["identity_evidence_refs"][0]["line_start"] == 3


def test_exact_mapping_hashes_typed_identity_and_marks_absence_only_in_exhaustive_scope(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    page = root / "Products/GoInsight/模块手册/字段与筛选/位置字段筛选.md"
    page.parent.mkdir(parents=True)
    page.write_text("# 位置字段筛选\n", encoding="utf-8")
    from knowledge_digest.companybrain_mapping import comparison_key
    base = {
        **_case("case-1", "位置字段筛选", "source-1"),
        "product_or_domain": "GoInsight",
        "module": "模块手册/字段与筛选",
        "object_or_scenario": "位置字段",
        "task": "filter",
        "page_type": "procedure",
    }
    base["comparison_key"] = comparison_key(**{key: base[key] for key in ("product_or_domain", "module", "object_or_scenario", "task", "page_type")})
    changed = dict(base, case_id="case-2", source_snapshot_id="source-1", comparison_key=comparison_key(product_or_domain="GoInsight", module="模块手册/字段与筛选", object_or_scenario="时间字段", task="filter", page_type="procedure"))
    result = build_mapping(root, [base, changed], _manifest("source-1"))
    assert result["cases"][0]["status"] == "unique"
    assert result["cases"][1]["status"] == "not_applicable"
    assert result["cases"][0]["comparison_key"].startswith("ck1:")
    assert result["companybrain_manifest"]["reader_page_scope"]["exhaustive"] is True


def test_equal_semantic_candidates_are_ambiguous(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    for suffix in ("a", "b"):
        page = root / f"Products/GoInsight/{suffix}/位置字段筛选.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("# 位置字段筛选\n位置字段筛选规则。\n", encoding="utf-8")

    result = build_mapping(root, [_case("case-1", "位置字段筛选", "source-1")], _manifest("source-1"))

    row = result["cases"][0]
    assert row["status"] == "ambiguous"
    assert row["entry_path"] is None


def test_source_content_can_break_a_title_tie_without_guessing(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    first = root / "Products/GoInsight/模块手册/报告/报告创建.md"
    second = root / "Products/GoInsight/模块手册/报告/报告管理.md"
    first.parent.mkdir(parents=True)
    first.write_text("# 报告创建\n\n设备报告的筛选器和快照导出规则。\n", encoding="utf-8")
    second.write_text("# 报告管理\n\n报告列表和权限管理。\n", encoding="utf-8")
    manifest = _manifest("source-1")
    manifest["entries"][0]["source_text"] = "设备报告筛选器支持快照导出。"

    result = build_mapping(root, [_case("case-1", "报告", "source-1")], manifest)

    row = result["cases"][0]
    assert row["status"] == "unique"
    assert row["entry_path"] == "Products/GoInsight/模块手册/报告/报告创建.md"


def test_non_action_claim_in_baseline_title_is_identity_evidence(tmp_path: Path) -> None:
    root = tmp_path / "CompanyBrain"
    page = root / "Products/GoInsight/技术实现/ClickHouse多集群与数据迁移.md"
    page.parent.mkdir(parents=True)
    page.write_text("# GoInsight：ClickHouse 多集群与数据迁移\n\n迁移任务列表和数据迁移边界。\n", encoding="utf-8")

    result = build_mapping(
        root,
        [{"case_id": "case-1", "target_title": "迁移任务列表", "source_snapshot_id": "source-1", "required_claims": ["迁移", "任务"]}],
        _manifest("source-1"),
    )

    row = result["cases"][0]
    assert row["status"] == "unique"
    assert row["entry_path"] == "Products/GoInsight/技术实现/ClickHouse多集群与数据迁移.md"
