from __future__ import annotations

import json
import importlib.util
from pathlib import Path

from knowledge_digest.reader_compiler import compile_reader_bundle

_MODULE_PATH = Path(__file__).parents[2] / "scripts" / "task3_semantic_compile.py"
_SPEC = importlib.util.spec_from_file_location("task3_semantic_compile", _MODULE_PATH)
assert _SPEC and _SPEC.loader
compiler = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(compiler)


def test_semantic_compile_batches_without_replay_and_records_candidate(tmp_path: Path, monkeypatch) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "GoInsight").mkdir()
    (raw / "GoInsight" / "a.md").write_text("## A\n\nA fact.\n", encoding="utf-8")
    (raw / "GoInsight" / "b.md").write_text("## B\n\nB fact.\n", encoding="utf-8")
    calls = 0

    def fake_call(prompt: str, **_kwargs: object) -> str:
        nonlocal calls
        calls += 1
        assert "Return exactly one item" in prompt
        return json.dumps({
            "items": [
                {"source_uri": "raw://confluence/GoInsight/a.md", "title": "A", "summary": "A summary", "module": "device-management", "knowledge_type": "module-manual", "body": "## Key facts\n\nA fact."},
                {"source_uri": "raw://confluence/GoInsight/b.md", "title": "B", "summary": "B summary", "module": "device-management", "knowledge_type": "module-manual", "body": "## Key facts\n\nB fact."},
            ]
        })

    monkeypatch.setattr(compiler, "call_llm", fake_call)
    result = compiler.compile_semantic_candidates(raw, tmp_path / "semantic", api_key="test", base_url="https://example.invalid/v1", model="qwen3.6", batch_size=2)

    assert calls == 1
    assert result["semantic_candidate_count"] == 2
    assert result["failure_count"] == 0
    assert result["replays"] == 0
    report = json.loads((tmp_path / "semantic/reports/semantic-compile.json").read_text(encoding="utf-8"))
    assert report["batch_count"] == 1
    assert len(list((tmp_path / "semantic/bundle").rglob("*.md"))) == 2


def test_semantic_compile_marks_a_failed_batch_without_retry(tmp_path: Path, monkeypatch) -> None:
    raw = tmp_path / "raw"
    (raw / "GoInsight").mkdir(parents=True)
    (raw / "GoInsight" / "a.md").write_text("内容\n", encoding="utf-8")
    calls = 0

    def failing_call(_prompt: str, **_kwargs: object) -> str:
        nonlocal calls
        calls += 1
        raise RuntimeError("provider down")

    monkeypatch.setattr(compiler, "call_llm", failing_call)
    result = compiler.compile_semantic_candidates(raw, tmp_path / "semantic", api_key="test", base_url="https://example.invalid/v1", model="qwen3.6", batch_size=1)

    assert calls == 1
    assert result["semantic_candidate_count"] == 0
    assert result["failure_count"] == 1
    assert result["status"] == "degraded"
    assert result["replays"] == 0


def test_semantic_compile_excludes_overlong_sources_without_provider_call(tmp_path: Path, monkeypatch) -> None:
    raw = tmp_path / "raw"
    (raw / "GoInsight").mkdir(parents=True)
    (raw / "GoInsight" / "short.md").write_text("短资料\n", encoding="utf-8")
    (raw / "GoInsight" / "long.md").write_text("长资料\n" + ("完整内容。" * 20), encoding="utf-8")
    calls = 0

    def fake_call(prompt: str, **_kwargs: object) -> str:
        nonlocal calls
        calls += 1
        assert "raw://confluence/GoInsight/short.md" in prompt
        assert "raw://confluence/GoInsight/long.md" not in prompt
        return json.dumps({"items": [{
            "source_uri": "raw://confluence/GoInsight/short.md",
            "title": "short",
            "summary": "summary",
            "module": "general",
            "knowledge_type": "module-manual",
            "body": "## Key facts\n\n短资料。",
        }]})

    monkeypatch.setattr(compiler, "call_llm", fake_call)
    result = compiler.compile_semantic_candidates(
        raw,
        tmp_path / "semantic",
        api_key="test",
        base_url="https://example.invalid/v1",
        model="qwen3.6",
        batch_size=2,
        max_chars_per_source=10,
    )

    assert calls == 1
    assert result["semantic_candidate_count"] == 1
    assert result["truncated_count"] == 1
    assert result["failure_count"] == 1
    report = json.loads((tmp_path / "semantic/reports/semantic-compile.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "semantic/audit/semantic-manifest.json").read_text(encoding="utf-8"))
    assert report["max_chars_per_source"] == 10
    assert manifest["failures"][0]["status"] == "semantic_truncated_fallback"


def test_truncation_fields_match_across_compile_report_manifest_and_reader_manifest(tmp_path: Path, monkeypatch) -> None:
    raw = tmp_path / "raw"
    (raw / "GoInsight").mkdir(parents=True)
    (raw / "GoInsight" / "short.md").write_text("短资料\n", encoding="utf-8")
    long_source = "长资料\n" + ("完整内容。\n" * 20)
    (raw / "GoInsight" / "long.md").write_text(long_source, encoding="utf-8")

    def fake_call(_prompt: str, **_kwargs: object) -> str:
        return json.dumps({"items": [{
            "source_uri": "raw://confluence/GoInsight/short.md",
            "title": "short",
            "summary": "summary",
            "module": "general",
            "knowledge_type": "module-manual",
            "body": "## Key facts\n\n短资料。",
        }]})

    monkeypatch.setattr(compiler, "call_llm", fake_call)
    semantic = tmp_path / "semantic"
    compiler.compile_semantic_candidates(
        raw,
        semantic,
        api_key="test",
        base_url="https://example.invalid/v1",
        model="qwen3.6",
        batch_size=2,
        max_chars_per_source=10,
    )
    output = tmp_path / "reader"
    compile_reader_bundle(raw, output, semantic_candidate=semantic)

    report = json.loads((semantic / "reports/semantic-compile.json").read_text(encoding="utf-8"))
    semantic_manifest = json.loads((semantic / "audit/semantic-manifest.json").read_text(encoding="utf-8"))
    reader_manifest = json.loads((output / "audit/source-manifest.json").read_text(encoding="utf-8"))
    report_failure = next(item for item in report["failures"] if item["relative_path"] == "GoInsight/long.md")
    semantic_failure = next(item for item in semantic_manifest["failures"] if item["relative_path"] == "GoInsight/long.md")
    reader_entry = next(item for item in reader_manifest["entries"] if item["relative_path"] == "GoInsight/long.md")
    reader_failure = next(item for item in reader_manifest["failures"] if item["relative_path"] == "GoInsight/long.md")
    assert {report_failure["source_uri"], report_failure["relative_path"], report_failure["input_chars"], report_failure["max_chars_per_source"]} == {
        semantic_failure["source_uri"], semantic_failure["relative_path"], semantic_failure["input_chars"], semantic_failure["max_chars_per_source"]
    }
    assert {
        reader_entry["source_uri"], reader_entry["relative_path"], reader_entry["semantic_input_chars"], reader_entry["semantic_max_chars_per_source"]
    } == {
        semantic_failure["source_uri"], semantic_failure["relative_path"], semantic_failure["input_chars"], semantic_failure["max_chars_per_source"]
    }
    assert reader_failure["status"] == "semantic_truncated_fallback"
