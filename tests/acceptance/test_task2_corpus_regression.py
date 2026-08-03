"""Task2's fixed 89-source, offline publication and comparison contracts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path

import pytest

from knowledge_digest.config import DigestSettings, SimilaritySettings
from knowledge_digest.kb_structure import parse_source_index_markdown
from knowledge_digest.paths import validate_paths
from knowledge_digest.pipeline import audit_run


TASK1_BASELINE = Path("/Users/Hugh/Downloads/KnowledgeDigest-task1-baseline-nd5n6s")
TASK2_REFERENCE = Path("/Users/Hugh/Downloads/KnowledgeDigest-task2-publication-offline-after-v4/company-kb")
COMPANY_BRAIN = Path("/Users/Hugh/Hugh/Knowledge/CompanyBrain")


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _copy_fixed_input(tmp_path: Path) -> tuple[Path, Path]:
    new_dir = tmp_path / "new-input"
    shutil.copytree(TASK1_BASELINE / "new-input", new_dir)
    kb_dir = tmp_path / "task2-kb"
    kb_dir.mkdir()
    return new_dir, kb_dir


def _run_offline(new_dir: Path, kb_dir: Path) -> Path:
    paths = validate_paths(new_dir, kb_dir, allow_new_kb=True)
    settings = DigestSettings(similarity=SimilaritySettings(backend="jaccard"), llm_enabled=False, llm_summary_enabled=False)
    report, _summary = audit_run(paths, settings, dry_run=False)
    return report


def _claim_signature(run_dir: Path) -> set[tuple[str, str, str, str, str]]:
    rows = _jsonl(run_dir / "s4" / "drafts.jsonl")
    return {
        (
            str(claim.get("claim_fingerprint", "")),
            str(claim.get("source_uri", "")),
            str(claim.get("content_fingerprint", "")),
            str(claim.get("fragment_locator", "")),
            str(claim.get("validation_status", "")),
        )
        for draft in rows
        for claim in draft.get("claims", [])
    }


def _latest_run(kb_dir: Path) -> Path:
    return sorted((kb_dir / "_digest" / "runs").iterdir())[-1]


def _source_manifest(new_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _jsonl(new_dir / "sources.jsonl"):
        relative = str(row["content_path"]).removeprefix("items/")
        result[str(row["source_uri"])] = hashlib.sha256((new_dir / "items" / relative).read_bytes()).hexdigest()
    return result


def test_corpus_contract_is_fixed_and_structured(tmp_path: Path) -> None:
    """The real 89-source run must be lossless and reader-navigable."""
    assert TASK1_BASELINE.is_dir(), f"missing fixed Task1 baseline: {TASK1_BASELINE}"
    before_manifest = _source_manifest(TASK1_BASELINE / "new-input")
    new_dir, kb_dir = _copy_fixed_input(tmp_path)
    report = _run_offline(new_dir, kb_dir)
    assert report.is_file()
    assert _source_manifest(new_dir) == before_manifest
    report_cost = json.loads(report.read_text(encoding="utf-8"))["cost"]
    assert report_cost["provider_calls_planned"] == 0
    assert report_cost["provider_calls_observed"] == 0
    assert report_cost["deterministic_rounds"] == report_cost["round_count"]

    structure = kb_dir / "kb.structure.md"
    assert (kb_dir / "README.md").is_file()
    assert (kb_dir / "Home.md").is_file()
    source_index = parse_source_index_markdown((kb_dir / "_digest" / "source-index.md").read_text(encoding="utf-8"))
    assert len(source_index["entries"]) == 88

    topic_index = json.loads((kb_dir / "_digest" / "topic-index.json").read_text(encoding="utf-8"))
    topics = topic_index["topics"]
    assert topics, "published topics must be persisted in the stable topic index"
    assert len({str(topic["category_id"]) for topic in topics}) > 1
    sample_page = (kb_dir / str(topics[0]["published_path"])).read_text(encoding="utf-8")
    assert "## Summary" in sample_page
    assert "## Why" in sample_page
    assert "来源未说明" in sample_page or "field_refs.why" in sample_page
    assert "## Version" in sample_page
    assert "未提供版本信息" in sample_page or "field_refs.version" in sample_page
    assert "## Related topics" in sample_page
    category_counts = {}
    for topic in topics:
        category_counts[str(topic["category_id"])] = category_counts.get(str(topic["category_id"]), 0) + 1
        published = kb_dir / str(topic["published_path"])
        assert published.is_file()
        assert published.read_text(encoding="utf-8").count("\n") <= 300
    other_count = category_counts.get("other", 0)
    assert other_count / len(topics) <= 0.20
    assert "pending" in category_counts or (kb_dir / "indexes" / "pending.md").is_file()
    assert not list((kb_dir / "pages" / "digest").glob("*.md")) if (kb_dir / "pages" / "digest").is_dir() else True

    baseline_run = _latest_run(TASK1_BASELINE / "company-kb")
    current_run = _latest_run(kb_dir)
    assert _claim_signature(current_run) == _claim_signature(baseline_run)
    assert all((kb_dir / str(entry["target_paths"][0])).is_file() for entry in source_index["entries"])


def test_comparison_contract_requires_fixed_manifest_and_reader_fields(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    if "corpus" in str(request.config.option.keyword):
        pytest.skip("comparison contract is exercised by the later -k comparison gate")
    module_path = Path(__file__).parents[2] / "scripts" / "task2_publication_comparison.py"
    spec = importlib.util.spec_from_file_location("task2_publication_comparison", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build_comparison_report = module.build_comparison_report

    result = build_comparison_report(
        task1_root=TASK1_BASELINE / "company-kb",
        task2_root=TASK2_REFERENCE,
        companybrain_root=COMPANY_BRAIN,
        output_dir=tmp_path,
    )
    assert result["sample_manifest"]
    assert result["sample_manifest_hash"]
    assert set(result["reader_quality_fields"]) >= {
        "title_understood",
        "category_correct",
        "home_to_topic_clicks",
        "source_backlink",
        "summary_faithful",
        "why_or_missing_explicit",
        "version_or_missing_explicit",
        "usage_boundary_visible",
        "orphan_link",
        "reader_time_seconds",
    }
    assert result["sample_gaps"]
    assert all({"parent", "requested", "selected", "missing"} <= set(gap) for gap in result["sample_gaps"])
    assert all("manual_notes" in sample for sample in result["sample_manifest"])
    assert set(result["safety_evidence"]) >= {
        "credentials_not_written",
        "paths_within_output",
        "taxonomy_unchanged",
        "handwritten_pages_untouched",
    }
    assert result["safety_evidence"]["taxonomy_unchanged"]["baseline_captured_before_comparison"] is True
    assert result["safety_evidence"]["paths_within_output"]["checked_targets"]
    assert result["cost_evidence"]["status"] in {"available", "unavailable"}
    assert result["machine_evidence"]["task2"]["claim_count"] >= 0
    assert result["cost_evidence"]["provider_calls"] >= 0
    if result["cost_evidence"]["status"] == "available" and not result["cost_evidence"]["provider_requested"]:
        assert result["cost_evidence"]["provider_calls"] == 0


def test_comparison_uses_freshest_report_and_batch_failure_ledger(tmp_path: Path) -> None:
    """UUID run names must not hide the latest failed provider attempt."""
    module_path = Path(__file__).parents[2] / "scripts" / "task2_publication_comparison.py"
    spec = importlib.util.spec_from_file_location("task2_publication_comparison_failure", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    runs = tmp_path / "_digest" / "runs"
    old_report = runs / "z-old" / "report.json"
    fresh_report = runs / "a-fresh" / "report.json"
    old_report.parent.mkdir(parents=True)
    fresh_report.parent.mkdir(parents=True)
    old_report.write_text(json.dumps({"settings": {"llm_enabled": False}}) + "\n", encoding="utf-8")
    fresh_report.write_text(
        json.dumps(
            {
                "settings": {"llm_enabled": True},
                "failure": {"stage": "llm"},
                "cost": {
                    "planned_generator_calls": 2,
                    "provider_calls_observed": None,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(old_report, (1000, 1000))
    os.utime(fresh_report, (2000, 2000))
    (tmp_path / "_digest" / "batch-state.json").write_text(
        json.dumps(
            {
                "runtime_identity": {"llm_model": "qwen3.6"},
                "cost_summary": {
                    "status": "failed",
                    "provider_calls_planned": None,
                    "provider_calls_reserved": 3,
                    "provider_calls_observed": None,
                    "failed_calls": 1,
                    "replay_calls": 0,
                    "elapsed_seconds": 12.5,
                    "provider_tokens": None,
                    "fallback_ratio": None,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = module._machine_evidence(tmp_path)
    assert evidence["cost"]["_status"] == "available"
    assert evidence["cost"]["_llm_enabled"] is True
    assert evidence["cost"]["_provider_calls"] is None
    assert evidence["cost"]["provider_calls_planned"] is None
    assert evidence["cost"]["provider_calls_reserved"] == 3
    assert evidence["cost"]["failed_calls"] == 1
    assert evidence["cost"]["elapsed_seconds"] == 12.5
