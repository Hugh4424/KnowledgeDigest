"""Reader-surface tests for the K3 projection boundary.

These tests intentionally exercise the batch-to-Reader seam with a tiny K1
batch.  The raw K1 pages remain evidence material; the K3 candidate is the
only surface allowed to look like a user knowledge base.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from knowledge_digest.kb_publish import load_batch_manifest
from knowledge_digest.reader_projection import compile_reader_candidate


def _sha_line(text: str) -> str:
    return hashlib.sha256((text + "\n").encode("utf-8")).hexdigest()


def _write_batch(root: Path) -> None:
    source_path = "demo/操作说明.md"
    source_line = "进入设备列表，选择目标设备并点击激活。"
    page_path = "products/demo/_general/demo-source.md"
    audit = root / "_audit"
    audit.mkdir(parents=True)
    (root / "products/demo/_general").mkdir(parents=True)
    (root / "products/demo/_general/demo-source.md").write_text(
        "---\n"
        "title: \"demo-source\"\n"
        "type: reference\n"
        "generated_by: knowledge_digest_semantic_compiler.py\n"
        "---\n\n"
        "# demo-source\n\n"
        "## 参考内容\n\n"
        f"{source_line}\n来源：操作说明.md\n",
        encoding="utf-8",
    )
    (audit / "sources.jsonl").write_text(
        json.dumps(
            {
                "claim_id": "cl-demo-1",
                "claim_kind": "narrative",
                "content_hash": _sha_line(source_line),
                "line_start": 12,
                "line_end": 12,
                "page_anchor": "narrative",
                "page_path": page_path,
                "source_block_id": "source-demo-b0001",
                "source_path": source_path,
                "status": "sourced",
                "text": source_line,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (audit / "reference-blocks.jsonl").write_text("", encoding="utf-8")
    (audit / "page-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "task7-page-manifest.v1",
                "attempt_id": "attempt-demo",
                "run_status": "complete",
                "publish_status": "not_released",
                "blockers": [],
                "pages": [
                    {
                        "page_path": page_path,
                        "page_paths": [page_path],
                        "source_paths": [source_path],
                        "topic_key": "demo:操作说明",
                    }
                ],
                "navigation": {"navigation_status": "generated_ok"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


class _FakeReaderProvider:
    def complete_reader(self, prompt: str) -> dict[str, object]:
        assert "cl-demo-1" in prompt
        return {
            "title": "设备激活操作指南",
            "question": "如何激活一台设备？",
            "page_type": "operation",
            "product": "Demo",
            "module": "设备管理",
            "object": "目标设备",
            "scenario": "设备入网",
            "boundary": "仅适用于已进入设备列表的设备",
            "summary": "进入设备列表选择目标设备，然后执行激活操作。",
            "sections": {
                "前置条件": ["目标设备已经出现在设备列表中。"],
                "操作步骤": ["进入设备列表，选择目标设备并点击激活。"],
                "预期结果": ["设备完成激活。"],
                "验证方式": ["回到设备列表确认设备状态已更新。"],
                "失败与限制": ["原始资料未明确"],
            },
            "evidence": {
                "summary": ["cl-demo-1"],
                "前置条件": ["cl-demo-1"],
                "操作步骤": ["cl-demo-1"],
                "预期结果": ["cl-demo-1"],
                "验证方式": ["cl-demo-1"],
                "失败与限制": [],
            },
            "provider_tokens": 12,
        }


def test_reader_projection_separates_reader_from_k1_audit(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    _write_batch(batch)

    result = compile_reader_candidate(
        batch,
        provider=_FakeReaderProvider(),
        cache_root=tmp_path / "cache",
    )

    assert result.status == "candidate"
    candidate = result.output_dir
    assert (candidate / "Home.md").is_file()
    assert (candidate / "Index.md").is_file()
    assert (candidate / "Audit.md").is_file()
    assert (candidate / "_audit/k1/page-manifest.json").is_file()

    pages = list((candidate / "products").rglob("*.md"))
    reader_page = next(path for path in pages if "/operation/" in path.as_posix())
    text = reader_page.read_text(encoding="utf-8")
    assert "page_type:" in text
    assert "## 操作步骤" in text
    assert "## 失败与限制" in text
    assert "来源：" not in text
    assert "generated_by: knowledge_digest_semantic_compiler.py" not in text

    manifest = load_batch_manifest(candidate)
    assert manifest["status"] == "ready"
    candidate_manifest = json.loads((candidate / "_audit/page-manifest.json").read_text(encoding="utf-8"))
    reader_paths = [
        item["page_path"]
        for item in candidate_manifest["pages"]
        if isinstance(item, dict) and isinstance(item.get("page_path"), str)
    ]
    assert any(path.startswith("products/demo/operation/") for path in reader_paths)

    reader_audit = [
        json.loads(line)
        for line in (candidate / "_audit/sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert reader_audit
    assert all(row["source_path"] == "demo/操作说明.md" for row in reader_audit)
    assert all(row["line_start"] == 12 and row["line_end"] == 12 for row in reader_audit)
    assert all(str(row["page_path"]).startswith("products/demo/operation/") for row in reader_audit)


def test_reader_audit_rebinds_hash_to_frozen_source_span_without_changing_cache_identity(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    _write_batch(batch)
    input_root = tmp_path / "input"
    source = input_root / "demo/操作说明.md"
    source.parent.mkdir(parents=True)
    source.write_text("\n".join(["空行"] * 11 + ["进入设备列表，选择目标设备并点击激活。  "]) + "\n", encoding="utf-8")

    result = compile_reader_candidate(
        batch,
        provider=_FakeReaderProvider(),
        cache_root=tmp_path / "cache",
        input_root=input_root,
    )

    assert result.status == "candidate"
    row = json.loads((result.output_dir / "_audit/sources.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["content_hash"] == _sha_line("进入设备列表，选择目标设备并点击激活。  ")
    assert row["content_hash"] != _sha_line("进入设备列表，选择目标设备并点击激活。")


def test_reader_projection_blocks_when_semantic_provider_is_unavailable(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    _write_batch(batch)

    result = compile_reader_candidate(batch, provider=None, cache_root=tmp_path / "cache")

    assert result.status == "blocked"
    assert result.publish_status == "not_released"
    assert not list((result.output_dir / "products").rglob("*.md"))
    assert result.blockers


def test_reader_seed_promotion_rebinds_current_k1_and_rejects_hash_drift(tmp_path: Path) -> None:
    from knowledge_digest.reader_projection import ReaderProjectionError, promote_reader_seed

    batch = tmp_path / "batch"
    _write_batch(batch)
    input_root = tmp_path / "input"
    source = input_root / "demo/操作说明.md"
    source.parent.mkdir(parents=True)
    raw = "\n".join(["空行"] * 11 + ["进入设备列表，选择目标设备并点击激活。  "]) + "\n"
    source.write_text(raw, encoding="utf-8")
    manifest_path = batch / "_audit/page-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_snapshot"] = {
        "entries": [{
            "source_id": "source-demo",
            "source_path": "demo/操作说明.md",
            "source_uri": "demo/操作说明.md",
            "content_hash": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "byte_count": len(raw.encode("utf-8")),
        }]
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8")

    seed = tmp_path / "seed"
    (seed / "_audit").mkdir(parents=True)
    (seed / "products/demo/operation").mkdir(parents=True)
    (seed / "products/demo/index.md").write_text("# Demo\n", encoding="utf-8")
    (seed / "Home.md").write_text("# Home\n", encoding="utf-8")
    (seed / "Audit.md").write_text("# Audit\n", encoding="utf-8")
    (seed / "_audit/source-status.json").write_text(
        json.dumps({"sources": [{"relative_path": "demo/操作说明.md", "raw_hash": hashlib.sha256(raw.encode("utf-8")).hexdigest()}]})
        + "\n",
        encoding="utf-8",
    )
    (seed / "products/demo/operation/demo.md").write_text(
        "---\npage_type: 操作\ndigest_page_id: demo-page\n---\n\n"
        "# Demo\n\n## Summary\n\n> 激活设备。\n"
        "> 证据：`demo/操作说明.md` 第 12-12 行\n\n"
        "## 这页解决什么问题\n\n如何激活设备？\n\n## 来源\n\n- `demo/操作说明.md`\n",
        encoding="utf-8",
    )

    promoted = promote_reader_seed(seed, batch, tmp_path / "candidate", input_root=input_root)
    assert promoted.status == "candidate"
    assert (promoted.output_dir / "_audit/k1/page-manifest.json").is_file()
    audit_row = json.loads((promoted.output_dir / "_audit/sources.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert audit_row["source_path"] == "demo/操作说明.md"
    assert audit_row["content_hash"] == hashlib.sha256(("进入设备列表，选择目标设备并点击激活。  \n").encode("utf-8")).hexdigest()

    drifted = tmp_path / "drifted-seed"
    import shutil

    shutil.copytree(seed, drifted)
    (drifted / "_audit/source-status.json").write_text(
        json.dumps({"sources": [{"relative_path": "demo/操作说明.md", "raw_hash": "0" * 64}]}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReaderProjectionError, match="source hashes"):
        promote_reader_seed(drifted, batch, tmp_path / "drifted-candidate", input_root=input_root)
