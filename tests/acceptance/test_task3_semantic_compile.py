from __future__ import annotations

import json
import importlib.util
from pathlib import Path

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
