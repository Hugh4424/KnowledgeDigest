from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_digest.reader_compiler import MAX_PAGE_LINES, compile_reader_bundle


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_compiler_creates_product_module_and_clean_reader_tree(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _write(raw, "GoInsight/指标详情页.md", "## 背景\n\n指标详情页用于查看数据。\n\n### 操作\n\n- 打开详情页\n")
    _write(raw, "merchant system/激活&停用终端_Terminal.md", "## 背景\n\n管理员可以激活或停用终端。\n")
    _write(raw, "loose.md", "## 说明\n\n这条资料没有产品目录。\n")
    output = tmp_path / "candidate"

    result = compile_reader_bundle(raw, output)

    assert result["status"] == "candidate"
    assert result["source_count"] == 3
    assert (output / "bundle/products/goinsight/overview.md").is_file()
    assert (output / "bundle/products/merchant-system/modules/device-management/index.md").is_file()
    assert (output / "bundle/products/unclassified/modules/general/index.md").is_file()
    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["entries"]) == 3
    assert all(entry["reader_paths"] for entry in manifest["entries"])
    for page in (output / "bundle").rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        assert "digest_content_hash" not in text
        assert "content_fingerprint" not in text
        assert "Reader signals" not in text
        assert len(text.splitlines()) <= MAX_PAGE_LINES
    quality = json.loads((output / "reports/quality.json").read_text(encoding="utf-8"))
    assert quality["reader_quality_proxy_passed"] is True
    assert quality["score"] >= 80


def test_compiler_splits_long_source_without_truncating_it(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    lines = ["## 长资料", "", "开头事实。"] + [f"- 事实 {i}" for i in range(700)]
    original = "\n".join(lines) + "\n"
    _write(raw, "GoInsight/long.md", original)
    output = tmp_path / "candidate"

    compile_reader_bundle(raw, output)

    parts = sorted((output / "bundle/products/goinsight/modules/general/knowledge").glob("long-part-*.md"))
    assert len(parts) >= 3
    assert all(len(path.read_text(encoding="utf-8").splitlines()) <= MAX_PAGE_LINES for path in parts)
    combined = "\n".join(path.read_text(encoding="utf-8") for path in parts)
    assert "事实 0" in combined
    assert "事实 699" in combined
    assert "下一部分" in parts[0].read_text(encoding="utf-8")
    assert "上一部分" in parts[-1].read_text(encoding="utf-8")


def test_compiler_rejects_existing_nonempty_output(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _write(raw, "GoInsight/a.md", "内容\n")
    output = tmp_path / "candidate"
    output.mkdir()
    (output / "old.txt").write_text("old package", encoding="utf-8")

    with pytest.raises(ValueError, match="new and empty"):
        compile_reader_bundle(raw, output)


def test_semantic_candidate_is_used_only_when_fingerprint_matches(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    source = "## 原文\n\n原始事实。\n"
    _write(raw, "GoInsight/a.md", source)
    candidate = tmp_path / "semantic"
    page = candidate / "bundle/products/goinsight/modules/data-and-analytics/semantic.md"
    page.parent.mkdir(parents=True)
    fingerprint = __import__("hashlib").sha256(source.encode("utf-8")).hexdigest()
    page.write_text(
        "---\n"
        "description: 语义摘要\n"
        "digest_content_fingerprint: " + fingerprint + "\n"
        "sources:\n"
        "- resource: raw://confluence/GoInsight/a.md\n"
        "  digest_content_fingerprint: " + fingerprint + "\n"
        "status: draft\n"
        "title: a\n"
        "type: KnowledgeDigest Knowledge\n"
        "---\n\n# 语义正文\n\n整理后的事实。\n",
        encoding="utf-8",
    )
    output = tmp_path / "candidate"

    compile_reader_bundle(raw, output, semantic_candidate=candidate)

    page_text = next((output / "bundle/products/goinsight").rglob("knowledge/*.md")).read_text(encoding="utf-8")
    assert "整理后的事实" in page_text
    assert "semantic_candidate" in json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))["entries"][0]["semantic_status"]


def test_reader_paths_are_exact_and_raw_relative_links_are_repaired(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _write(raw, "GoInsight/a.md", "## A\n\n请看 [B](b.md)。\n")
    _write(raw, "GoInsight/b.md", "## B\n\nB 的事实。\n")
    output = tmp_path / "candidate"

    compile_reader_bundle(raw, output)

    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["entries"]:
        assert len(entry["reader_paths"]) == 1
        assert (output / "bundle" / entry["reader_paths"][0]).is_file()
    a_page = next((output / "bundle/products/goinsight").rglob("knowledge/a.md"))
    assert "B](b.md)" in a_page.read_text(encoding="utf-8")
    quality = json.loads((output / "reports/quality.json").read_text(encoding="utf-8"))
    assert quality["link_violations"] == []


def test_empty_source_is_audit_failure_without_placeholder_reader_page(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _write(raw, "GoInsight/empty.md", "---\nsource_id: source-empty\n---\n\n")
    output = tmp_path / "candidate"

    result = compile_reader_bundle(raw, output)

    assert result["source_count"] == 1
    assert result["failure_count"] == 1
    assert not list((output / "bundle").glob("products/*/modules/*/knowledge/*.md"))
    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["failures"][0]["reason"] == "empty_content"
    assert json.loads((output / "audit/run-manifest.json").read_text(encoding="utf-8"))["status"] == "degraded"


def test_semantic_fact_loss_falls_back_and_is_recorded(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    source = "## 操作\n\n```bash\ncurl https://example.test/v1\n```\n\n端口 8080。\n"
    _write(raw, "GoInsight/api.md", source)
    candidate = tmp_path / "semantic"
    page = candidate / "bundle/products/goinsight/modules/api/semantic.md"
    page.parent.mkdir(parents=True)
    fingerprint = __import__("hashlib").sha256(source.encode("utf-8")).hexdigest()
    page.write_text(
        "---\n"
        "description: 语义摘要\n"
        "sources:\n"
        "- resource: raw://confluence/GoInsight/api.md\n"
        f"  digest_content_fingerprint: {fingerprint}\n"
        "status: draft\n"
        "title: api\n"
        "type: KnowledgeDigest Knowledge\n"
        "---\n\n# 语义正文\n\n只保留了一句总结。\n",
        encoding="utf-8",
    )
    output = tmp_path / "candidate"

    compile_reader_bundle(raw, output, semantic_candidate=candidate)

    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["failures"][0]["reason"] == "semantic_content_integrity_failed"
    assert manifest["entries"][0]["semantic_status"] == "semantic_fact_loss_fallback"
    page_text = next((output / "bundle/products/goinsight").rglob("knowledge/*.md")).read_text(encoding="utf-8")
    assert "curl https://example.test/v1" in page_text
    assert "8080" in page_text


def test_reader_rejects_semantic_candidate_marked_as_truncated(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    source = "## 长资料\n\n开头事实。\n" + ("完整事实。\n" * 300)
    _write(raw, "GoInsight/long.md", source)
    candidate = tmp_path / "semantic"
    page = candidate / "bundle/products/goinsight/modules/general/long.md"
    page.parent.mkdir(parents=True)
    fingerprint = __import__("hashlib").sha256(source.encode("utf-8")).hexdigest()
    page.write_text(
        "---\n"
        "description: 不应采用\n"
        "sources:\n"
        "- resource: raw://confluence/GoInsight/long.md\n"
        f"  digest_content_fingerprint: {fingerprint}\n"
        "status: draft\n"
        "title: long\n"
        "type: KnowledgeDigest Knowledge\n"
        "---\n\n# 不应采用\n\n模型只看到了开头。\n",
        encoding="utf-8",
    )
    audit = candidate / "audit"
    audit.mkdir()
    (audit / "semantic-manifest.json").write_text(json.dumps({
        "schema_version": "task3-semantic-candidate.v1",
        "source_count": 1,
        "semantic_candidate_count": 0,
        "failure_count": 1,
        "max_chars_per_source": 10,
        "truncated_count": 1,
        "entries": [],
        "failures": [{
            "source_uri": "raw://confluence/GoInsight/long.md",
            "relative_path": "GoInsight/long.md",
            "status": "semantic_truncated_fallback",
            "input_chars": len(source),
            "max_chars_per_source": 10,
        }],
    }, ensure_ascii=False), encoding="utf-8")

    output = tmp_path / "candidate"
    compile_reader_bundle(raw, output, semantic_candidate=candidate)

    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    entry = manifest["entries"][0]
    assert entry["semantic_status"] == "semantic_truncated_fallback"
    assert entry["semantic_input_chars"] == len(source)
    assert entry["semantic_max_chars_per_source"] == 10
    page_text = next((output / "bundle/products/goinsight").rglob("knowledge/*.md")).read_text(encoding="utf-8")
    assert "模型只看到了开头" not in page_text
    assert "完整事实。" in page_text


def test_reader_rejects_overlong_candidate_with_legacy_manifest(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    source = "## 长资料\n\n开头事实。\n" + ("完整事实。\n" * 1800)
    _write(raw, "GoInsight/legacy.md", source)
    candidate = tmp_path / "semantic"
    page = candidate / "bundle/products/goinsight/modules/general/legacy.md"
    page.parent.mkdir(parents=True)
    fingerprint = __import__("hashlib").sha256(source.encode("utf-8")).hexdigest()
    page.write_text(
        "---\n"
        "description: 旧清单不应绕过门禁\n"
        "sources:\n"
        "- resource: raw://confluence/GoInsight/legacy.md\n"
        f"  digest_content_fingerprint: {fingerprint}\n"
        "status: draft\n"
        "title: legacy\n"
        "type: KnowledgeDigest Knowledge\n"
        "---\n\n# 旧清单候选\n\n模型只看到了开头。\n",
        encoding="utf-8",
    )
    audit = candidate / "audit"
    audit.mkdir(parents=True)
    (audit / "semantic-manifest.json").write_text(json.dumps({
        "schema_version": "task3-semantic-candidate.v1",
        "entries": [{"source_uri": "raw://confluence/GoInsight/legacy.md"}],
        "failures": [],
    }), encoding="utf-8")

    output = tmp_path / "candidate"
    compile_reader_bundle(raw, output, semantic_candidate=candidate)

    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["entries"][0]["semantic_status"] == "semantic_truncated_fallback"
    assert manifest["failures"][0]["reason"] == "candidate_manifest_missing_or_failed_to_record_truncation"
    page_text = next((output / "bundle/products/goinsight").rglob("knowledge/*.md")).read_text(encoding="utf-8")
    assert "模型只看到了开头" not in page_text
    assert "完整事实。" in page_text


def test_reader_rejects_candidate_when_semantic_manifest_is_invalid(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    source = "## 资料\n\n完整来源内容。\n"
    _write(raw, "GoInsight/broken.md", source)
    candidate = tmp_path / "semantic"
    page = candidate / "bundle/products/goinsight/modules/general/broken.md"
    page.parent.mkdir(parents=True)
    fingerprint = __import__("hashlib").sha256(source.encode("utf-8")).hexdigest()
    page.write_text(
        "---\n"
        "sources:\n"
        "- resource: raw://confluence/GoInsight/broken.md\n"
        f"  digest_content_fingerprint: {fingerprint}\n"
        "title: broken\n"
        "type: KnowledgeDigest Knowledge\n"
        "---\n\n# 错误候选\n\n不应采用。\n",
        encoding="utf-8",
    )
    audit = candidate / "audit"
    audit.mkdir(parents=True)
    (audit / "semantic-manifest.json").write_text("{not-json", encoding="utf-8")

    output = tmp_path / "candidate"
    compile_reader_bundle(raw, output, semantic_candidate=candidate)

    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["entries"][0]["semantic_status"] == "semantic_manifest_unavailable"
    assert manifest["failures"][0]["status"] == "semantic_manifest_unavailable"
    page_text = next((output / "bundle/products/goinsight").rglob("knowledge/*.md")).read_text(encoding="utf-8")
    assert "不应采用" not in page_text
    assert "完整来源内容。" in page_text


def test_reader_audits_invalid_semantic_manifest_without_candidate_pages(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _write(raw, "GoInsight/a.md", "## 资料\n\n原始内容。\n")
    candidate = tmp_path / "semantic"
    (candidate / "bundle").mkdir(parents=True)
    (candidate / "audit").mkdir(parents=True)
    (candidate / "audit/semantic-manifest.json").write_text("{not-json", encoding="utf-8")

    output = tmp_path / "candidate"
    compile_reader_bundle(raw, output, semantic_candidate=candidate)

    manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["failures"][0]["status"] == "semantic_manifest_unavailable"
    assert manifest["failures"][0]["relative_path"] == "audit/semantic-manifest.json"
