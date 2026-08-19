from __future__ import annotations

import json
import fcntl
import hashlib
import re
from pathlib import Path

import knowledge_digest.task4_reader_quality as task4_module
from knowledge_digest.task4_reader_quality import compile_full_reader


def _config(path: Path, *, count: int | None = 89, title_rules: list[dict[str, object]] | None = None, empty_source_policy: str | None = None, empty_source_allowlist: list[dict[str, str]] | None = None) -> Path:
    value: dict[str, object] = {
        "schema_version": "task4-reader-quality.v1",
        "source_extensions": [".md", ".txt", ".json"],
        "excluded_names": [".DS_Store"],
        "max_page_lines": 300,
        "taxonomy": {
            "root_aliases": {"raw": {"product": "GoInsight", "fallback_module": "数据分析"}},
            "rules": [
                {"id": "raw-analysis", "roots": ["raw"], "any": ["数据分析", "位置字段"], "module": "数据分析"},
                {"id": "raw-device", "roots": ["raw"], "any": ["设备", "终端"], "module": "设备管理"},
            ],
        },
        "semantic": {"title_rules": title_rules or []},
        "page_types": {
            "procedure": {"required_sections": ["Summary", "答案", "规则和边界", "相关主题", "来源（简表）"]}
        },
    }
    if count is not None:
        value["source_coverage"] = {"manifest_id": f"fixture-{count}", "expected_count": count}
    if empty_source_policy is not None:
        value["empty_source_policy"] = empty_source_policy
    if empty_source_allowlist is not None:
        value["empty_source_allowlist"] = empty_source_allowlist
    config = path / "config.json"
    config.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return config


def _source(index: int, *, title: str | None = None, topic: str | None = None, extra: str = "") -> str:
    title = title or f"主题 {index:02d}"
    topic = topic or f"topic-{index:02d}"
    return (
        f"---\ntopic_key: {topic}\nproduct: GoInsight\nmodule: 数据分析\n---\n"
        f"# {title}\n\n这是 {title} 的用途和适用范围。\n\n"
        "## 操作步骤\n\n- 打开功能入口并选择目标对象。\n- 保存配置后检查处理结果。\n\n"
        "## 规则和边界\n\n- 只对当前模块支持，权限不足时不能执行。\n"
        f"{extra}"
    )


def _write_corpus(root: Path, *, count: int = 89, invalid: bool = False, conflict: bool = False) -> Path:
    raw = root / "raw"
    for index in range(count):
        shared = index in ({0, 1} if conflict else {0, 2})
        title = "共享主题" if shared else ("ae-通信和网络配置" if index == 3 else f"主题 {index:02d}")
        topic = "shared-topic" if shared else f"topic-{index:02d}"
        extra = "\n- 冲突版本：同一主题的规则不同。\n" if conflict and index == 1 else ""
        path = raw / "raw" / f"来源-{index:02d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_source(index, title=title, topic=topic, extra=extra), encoding="utf-8")
    if invalid:
        (raw / "raw" / "来源-00.md").write_bytes(b"\xff\xfe not utf8")
    return raw


def _manifest(output: Path) -> dict[str, object]:
    return json.loads((output / "reports/source-manifest.json").read_text(encoding="utf-8"))


def test_full_compile_is_configured_for_89_but_not_hardcoded(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path)
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path))

    assert result["status"] == "candidate"
    assert result["source_count"] == 89
    manifest = _manifest(tmp_path / "out")
    assert len(manifest["entries"]) == 89
    assert all(row["source_id"] and row["content_hash"] and row["target_path"] for row in manifest["entries"])
    assert json.loads((tmp_path / "out/reports/coverage-report.json").read_text(encoding="utf-8"))["source_count"] == 89


def test_production_compiler_accepts_a_different_source_count(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path, count=2)
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path, count=None))

    assert result["status"] == "candidate"
    assert result["source_count"] == 2
    assert result["expected_source_count"] is None


def test_any_source_failure_is_a_full_hard_gate(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path, invalid=True)
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path))

    assert result["status"] == "not_released"
    assert result["failure_count"] >= 1
    assert not (tmp_path / "out/bundle/Home.md").exists()
    failures = (tmp_path / "out/audit/failures.jsonl").read_text(encoding="utf-8")
    assert "source_unreadable" in failures


def test_configured_empty_source_stays_in_audit_without_blocking_valid_reader(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path, count=2)
    empty = raw / "raw/AE - AirViewer厂商管理.md"
    empty.write_bytes(b"  \n  ")

    result = compile_full_reader(
        raw,
        tmp_path / "out",
        _config(
            tmp_path,
            count=3,
            empty_source_policy="audit_only",
            empty_source_allowlist=[
                {
                    "source_uri": "raw/AE - AirViewer厂商管理.md",
                    "content_hash": hashlib.sha256(b"  \n  ").hexdigest(),
                }
            ],
        ),
    )

    assert result["status"] == "candidate"
    assert result["source_count"] == 3
    assert result["reader_source_count"] == 2
    assert result["failure_count"] == 0
    manifest = _manifest(tmp_path / "out")
    row = next(item for item in manifest["entries"] if item["source_uri"] == "raw/AE - AirViewer厂商管理.md")
    assert row["status"] == "not_applicable"
    assert row["reason_code"] == "empty_body"
    coverage = json.loads((tmp_path / "out/reports/coverage-report.json").read_text(encoding="utf-8"))
    coverage_row = next(item for item in coverage["rows"] if item["source_uri"] == row["source_uri"])
    assert coverage_row["status"] == "not_applicable"
    assert (tmp_path / "out/audit/source-snapshots" / f"{row['source_id']}.md").read_bytes() == b"  \n  "


def test_failed_or_cancelled_rerun_preserves_previous_bundle(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path)
    output = tmp_path / "out"
    first = compile_full_reader(raw, output, _config(tmp_path))
    assert first["status"] == "candidate"
    home_before = (output / "bundle/Home.md").read_text(encoding="utf-8")

    _write_corpus(tmp_path, invalid=True)
    failed = compile_full_reader(raw, output, _config(tmp_path))
    assert failed["status"] == "not_released"
    assert (output / "bundle/Home.md").read_text(encoding="utf-8") == home_before
    failed_status = json.loads((output / "status.json").read_text(encoding="utf-8"))
    assert failed_status["reader_bundle_preserved"] is True

    cancelled = compile_full_reader(raw, output, _config(tmp_path), cancel_check=lambda: True)
    assert cancelled["status"] == "cancelled"
    assert (output / "bundle/Home.md").read_text(encoding="utf-8") == home_before
    cancelled_status = json.loads((output / "status.json").read_text(encoding="utf-8"))
    assert cancelled_status["reader_bundle_preserved"] is True


def test_concurrent_compile_is_rejected_without_touching_current_bundle(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path)
    output = tmp_path / "out"
    assert compile_full_reader(raw, output, _config(tmp_path))["status"] == "candidate"
    home_before = (output / "bundle/Home.md").read_text(encoding="utf-8")
    lock_path = output / ".staging/.compile.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = compile_full_reader(raw, output, _config(tmp_path))
    assert result["status"] == "failed"
    assert result["reason_code"] == "output_busy"
    assert (output / "bundle/Home.md").read_text(encoding="utf-8") == home_before


def test_publish_interrupt_rolls_back_before_failure_status_is_written(tmp_path: Path, monkeypatch) -> None:
    raw = _write_corpus(tmp_path)
    output = tmp_path / "out"
    assert compile_full_reader(raw, output, _config(tmp_path))["status"] == "candidate"
    home_before = (output / "bundle/Home.md").read_text(encoding="utf-8")

    real_replace = task4_module.os.replace
    replace_calls = {"count": 0}

    def interrupt_during_publish(source, destination):
        replace_calls["count"] += 1
        if replace_calls["count"] == 1:
            real_replace(source, destination)
            raise KeyboardInterrupt
        return real_replace(source, destination)

    monkeypatch.setattr(task4_module.os, "replace", interrupt_during_publish)
    interrupted = compile_full_reader(raw, output, _config(tmp_path))

    assert interrupted["status"] == "cancelled"
    assert (output / "bundle/Home.md").read_text(encoding="utf-8") == home_before
    assert not (output / ".staging/.publish-backup").exists()
    assert (output / ".staging/.compile.lock").exists()


def test_interrupt_after_status_install_keeps_published_bundle_consistent(tmp_path: Path, monkeypatch) -> None:
    raw = _write_corpus(tmp_path)
    output = tmp_path / "out"
    assert compile_full_reader(raw, output, _config(tmp_path))["status"] == "candidate"

    real_publish = task4_module._publish

    def publish_then_interrupt(staging, destination, names):
        real_publish(staging, destination, names)
        raise KeyboardInterrupt

    monkeypatch.setattr(task4_module, "_publish", publish_then_interrupt)
    interrupted = compile_full_reader(raw, output, _config(tmp_path))

    assert interrupted["status"] == "candidate"
    assert interrupted["reason_code"] == "post_publish_interrupt"
    status = json.loads((output / "status.json").read_text(encoding="utf-8"))
    assert status["package_status"] == "candidate"
    assert status["run_id"] == interrupted["run_id"]
    assert (output / "bundle/Home.md").exists()


def test_cancel_and_conflict_do_not_leave_a_reader_entry(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path, conflict=True)
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path))

    assert result["status"] == "not_released"
    assert not (tmp_path / "out/bundle/Home.md").exists()
    assert "topic_conflict" in (tmp_path / "out/audit/failures.jsonl").read_text(encoding="utf-8")

    cancelled = compile_full_reader(raw, tmp_path / "cancelled", _config(tmp_path), cancel_check=lambda: True)
    assert cancelled["status"] == "cancelled"
    assert not (tmp_path / "cancelled/bundle/Home.md").exists()

    calls = {"count": 0}

    def cancel_during_read() -> bool:
        calls["count"] += 1
        return calls["count"] >= 2

    interrupted = compile_full_reader(raw, tmp_path / "interrupted", _config(tmp_path), cancel_check=cancel_during_read)
    assert interrupted["status"] == "cancelled"
    assert not (tmp_path / "interrupted/bundle/Home.md").exists()


def test_semantic_title_path_body_and_reader_links_are_clean(tmp_path: Path) -> None:
    raw = _write_corpus(tmp_path, count=4)
    config = _config(
        tmp_path,
        count=4,
        title_rules=[{"id": "android-network", "any": ["通信和网络配置"], "title": "Android 安全通信网络配置项字典"}],
    )
    result = compile_full_reader(raw, tmp_path / "out", config)
    assert result["status"] == "candidate"

    topic_index = json.loads((tmp_path / "out/reports/topic-index.json").read_text(encoding="utf-8"))
    pages = [tmp_path / "out/bundle" / row["page_path"] for row in topic_index["topics"]]
    assert pages
    all_text = "\n".join(page.read_text(encoding="utf-8") for page in pages)
    assert all(not row["title"].lower().startswith("ae-") for row in topic_index["topics"])
    assert "source_uri:" not in all_text
    assert "fingerprint" not in all_text.lower()
    assert "provider" not in all_text.lower()
    assert all("/modules/待分类/" not in row["page_path"] for row in topic_index["topics"])
    assert all("/modules/" not in row["page_path"] for row in topic_index["topics"])
    android = next(row for row in topic_index["topics"] if row["title"] == "Android 安全通信网络配置项字典")
    assert android["page_path"].startswith("products/GoInsight/数据分析/")
    assert all(re.search(r"## Summary|## 答案", page.read_text(encoding="utf-8")) for page in pages)


def test_generic_q_and_a_heading_does_not_replace_semantic_filename(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "emm").mkdir(parents=True)
    (raw / "emm/EMM售前确认.md").write_text(
        "---\ntopic_key: emm-presales\nproduct: GoInsight\nmodule: 数据分析\n---\n"
        "# ・Q&A\n\nGoogle 企业注册和应用能力需要确认。\n\n"
        "## 操作步骤\n\n- 核对企业注册状态并确认应用能力。\n\n"
        "## 规则和边界\n\n- 权限不足时不能执行。\n",
        encoding="utf-8",
    )

    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path, count=1))

    assert result["status"] == "candidate"
    topic = json.loads((tmp_path / "out/reports/topic-index.json").read_text(encoding="utf-8"))["topics"][0]
    assert topic["title"] == "EMM售前确认"
    assert topic["page_path"].endswith("/EMM售前确认.md")


def test_title_only_taxonomy_does_not_classify_by_incidental_body_terms(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    (raw / "raw/位置字段筛选.md").write_text(
        "# 位置字段筛选\n\n正文会提到创建设备报告，但主题本身是位置字段筛选。\n",
        encoding="utf-8",
    )
    config = json.loads(_config(tmp_path, count=1).read_text(encoding="utf-8"))
    config["taxonomy"]["match_title_only"] = True
    config["taxonomy"]["rules"] = [
        {"id": "report", "roots": ["raw"], "any": ["创建设备报告"], "module": "报告与快照"},
        {"id": "location", "roots": ["raw"], "any": ["位置字段筛选"], "module": "字段与筛选"},
    ]
    path = tmp_path / "title-only.json"
    path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    result = compile_full_reader(raw, tmp_path / "out", path)

    assert result["status"] == "candidate"
    report = json.loads((tmp_path / "out/reports/taxonomy-report.json").read_text(encoding="utf-8"))
    assert report["rows"][0]["classification_rule_id"] == "location"


def test_evidence_insufficient_is_pending_not_common_bucket(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    (raw / "raw/unknown.md").write_text("# 未知对象\n\n只有一条事实。\n", encoding="utf-8")
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path, count=1))

    assert result["status"] == "not_released"
    nodes = json.loads((tmp_path / "out/audit/semantic-nodes.json").read_text(encoding="utf-8"))
    assert nodes["nodes"][0]["status"] == "pending"
    assert nodes["nodes"][0]["module"] != "通用"
    assert not (tmp_path / "out/bundle/Home.md").exists()


def test_config_variant_keeps_stable_lineage_without_89_paths(tmp_path: Path) -> None:
    raw = tmp_path / "variant-input"
    (raw / "domain").mkdir(parents=True)
    (raw / "domain/one.txt").write_text(_source(1, title="变体主题", topic="variant-topic"), encoding="utf-8")
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path, count=None))

    assert result["status"] == "candidate"
    row = _manifest(tmp_path / "out")["entries"][0]
    assert row["source_uri"] == "domain/one.txt"
    assert row["lineage"]["source_uri"] == "domain/one.txt"


def test_related_topics_are_real_relation_ledger_entries(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    for title, topic in (("位置字段筛选", "location-filter"), ("数据分析", "data-analysis")):
        (raw / "raw" / f"{title}.md").write_text(_source(1, title=title, topic=topic), encoding="utf-8")
    config = json.loads(_config(tmp_path, count=2).read_text(encoding="utf-8"))
    config["related_topic_groups"] = [{"topic_key": "location-filter", "related_topic_keys": ["data-analysis"]}]
    config_path = tmp_path / "related-config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    result = compile_full_reader(raw, tmp_path / "out", config_path)

    assert result["status"] == "candidate"
    relations = json.loads((tmp_path / "out/reports/relation-ledger.json").read_text(encoding="utf-8"))["relations"]
    assert relations and relations[0]["relation_type"] == "related"
    assert relations[0]["evidence"]["source_topic"][0]["source_id"]
    assert relations[0]["evidence"]["target_topic"][0]["snapshot_ref"].startswith("audit/source-snapshots/")
    location = next(row for row in json.loads((tmp_path / "out/reports/topic-index.json").read_text(encoding="utf-8"))["topics"] if row["topic_key"] == "location-filter")
    page = (tmp_path / "out/bundle" / location["page_path"]).read_text(encoding="utf-8")
    assert "数据分析" in page


def test_page_type_fixture_controls_compile_and_required_sections(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    (raw / "raw/排查.md").write_text(
        "---\ntopic_key: diagnostic-topic\npage_type: diagnostic\n---\n"
        "# 排查主题\n\n出现异常时检查配置和权限。\n\n"
        "## 规则和边界\n\n- 权限不足时不能执行。\n",
        encoding="utf-8",
    )
    registry = tmp_path / "page-types.json"
    registry.write_text(json.dumps({"page_types": {"diagnostic": {"required_sections": ["Summary", "排查路径", "规则和边界", "来源（简表）"]}}}, ensure_ascii=False), encoding="utf-8")
    config = json.loads(_config(tmp_path, count=1).read_text(encoding="utf-8"))
    config.pop("page_types")
    config["taxonomy"]["rules"].append({"id": "raw-diagnostic", "roots": ["raw"], "any": ["排查主题"], "module": "排障"})
    config["page_type_fixture"] = registry.name
    config_path = tmp_path / "fixture-config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    result = compile_full_reader(raw, tmp_path / "out", config_path)

    assert result["status"] == "candidate"
    topic = json.loads((tmp_path / "out/reports/topic-index.json").read_text(encoding="utf-8"))["topics"][0]
    page = tmp_path / "out/bundle" / topic["page_path"]
    text = page.read_text(encoding="utf-8")
    assert "## 排查路径" in text


def test_reader_body_is_structured_and_preserves_table_cells(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    (raw / "raw/位置筛选.md").write_text(
        "## **适用场景**\n\n"
        "管理员需要按地图区域筛选设备。\n\n"
        "## **配置步骤**\n\n"
        "* 在数据分析页面把位置字段拖入筛选栏。\n"
        "* 选择 Inside 或 Outside 后提交。\n\n"
        "| 配置项 | 默认值 | 限制 |\n"
        "| --- | --- | --- |\n"
        "| 区域模式 | Inside | 至少 3 个点 |\n\n"
        "## **限制和边界**\n\n"
        "* 点位最多 100 个，区域不能交叉。\n\n"
        "## **排查**\n\n"
        "* 点数不足时不能提交，请先添加 3 个点。\n\n"
        "文档目录\n\n"
        "| 版本/时间 | 修订记录/修订人 |\n"
        "| --- | --- |\n"
        "| V1 | 不应进入 Reader |\n",
        encoding="utf-8",
    )
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path, count=1))

    assert result["status"] == "candidate"
    topic = json.loads((tmp_path / "out/reports/topic-index.json").read_text(encoding="utf-8"))["topics"][0]
    page = (tmp_path / "out/bundle" / topic["page_path"]).read_text(encoding="utf-8")
    assert "## 使用场景" in page
    assert "## 操作/配置" in page
    assert "## 规则和边界" in page
    assert "## 排查路径" in page
    assert "| 配置项 | 默认值 | 限制 |" in page
    assert "；默认值；限制" not in page
    assert "文档目录" not in page
    assert "修订记录" not in page
    claims = json.loads((tmp_path / "out/reports/claim-ledger.json").read_text(encoding="utf-8"))["claims"]
    assert any(row["fragment_locator"] == "line:12" for row in claims)


def test_diagnostic_path_does_not_repeat_procedure_content(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    (raw / "raw/故障排查.md").write_text(
        "---\npage_type: diagnostic\ntopic_key: diagnostic-topic\nmodule: 排障\n---\n"
        "# 故障排查\n\n"
        "## 操作步骤\n\n* 打开设置并保存配置。\n\n"
        "## 排查路径\n\n* 保存失败时先检查权限，再检查网络。\n\n"
        "## 规则和边界\n\n* 权限不足时不能执行。\n",
        encoding="utf-8",
    )
    registry = tmp_path / "page-types.json"
    registry.write_text(json.dumps({"page_types": {"diagnostic": {"required_sections": ["Summary", "排查路径", "规则和边界", "来源（简表）"]}}}, ensure_ascii=False), encoding="utf-8")
    config = json.loads(_config(tmp_path, count=1).read_text(encoding="utf-8"))
    config.pop("page_types")
    config["page_type_fixture"] = registry.name
    config_path = tmp_path / "diagnostic-config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    result = compile_full_reader(raw, tmp_path / "out", config_path)

    assert result["status"] == "candidate"
    topic = json.loads((tmp_path / "out/reports/topic-index.json").read_text(encoding="utf-8"))["topics"][0]
    page = (tmp_path / "out/bundle" / topic["page_path"]).read_text(encoding="utf-8")
    diagnostic = page.split("## 排查路径", 1)[1].split("## 规则和边界", 1)[0]
    assert "保存失败时先检查权限" in diagnostic
    assert "打开设置并保存配置" not in diagnostic


def test_confluence_faq_table_is_not_dropped(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "raw").mkdir(parents=True)
    (raw / "raw/位置字段筛选.md").write_text(
        "# 位置字段筛选\n\n## FAQ\n\n"
        "| 1 | 为什么看不到位置筛选？ | 私人分组不支持位置筛选，只能查看权限范围内的内容。 |\n"
        "| - | --- | --- |\n",
        encoding="utf-8",
    )
    result = compile_full_reader(raw, tmp_path / "out", _config(tmp_path, count=1))

    assert result["status"] == "candidate"
    topic = json.loads((tmp_path / "out/reports/topic-index.json").read_text(encoding="utf-8"))["topics"][0]
    page = (tmp_path / "out/bundle" / topic["page_path"]).read_text(encoding="utf-8")
    assert "## 排查路径" in page
    assert "私人分组不支持位置筛选" in page
