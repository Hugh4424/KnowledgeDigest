"""Task0 Phase 4 acceptance: runtime facts, question set and growth audit."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_digest(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "knowledge_digest.cli", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _offline_config(tmp_path: Path) -> Path:
    path = tmp_path / "offline.json"
    path.write_text(
        json.dumps(
            {
                "similarity": {"backend": "jaccard"},
                "llm_enabled": False,
                "llm_summary_enabled": False,
            }
        ),
        encoding="utf-8",
    )
    return path


def _input(tmp_path: Path) -> Path:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    (items / "note.md").write_text("Runtime audit source evidence.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "note.md", "source_uri": "https://source.example/runtime"}) + "\n",
        encoding="utf-8",
    )
    return new_dir


def _latest_report(kb_dir: Path) -> dict[str, object]:
    runs = sorted((kb_dir / "_digest" / "runs").iterdir(), key=lambda path: path.stat().st_mtime_ns)
    return json.loads((runs[-1] / "report.json").read_text(encoding="utf-8"))


def test_question_set_has_replayable_17_plus_3_manifest() -> None:
    path = PROJECT_ROOT / "config" / "task0-question-set.v1.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["schema_version"] == "task0-question-set.v1"
    assert value["question_set_id"] == "knowledge-digest-task0-v1"
    assert len(value["questions"]) == 20
    assert sum(row["polarity"] == "positive" for row in value["questions"]) == 17
    assert sum(row["polarity"] == "negative" for row in value["questions"]) == 3
    assert value["sample_seed"] == "knowledge-digest-task0-v1"
    assert value["reviewer"] == "task3-independent-human-reviewer"
    assert value["derivation_rules"]
    required = {
        "question_id",
        "polarity",
        "original_text",
        "entry_path",
        "expected_topic_or_product",
        "covered_roles",
        "negative_design",
    }
    assert all(required <= set(row) for row in value["questions"])
    canonical = {
        key: value[key]
        for key in ("schema_version", "question_set_id", "questions", "derivation_rules")
    }
    expected_hash = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert value["question_set_hash"] == expected_hash


def test_offline_run_records_zero_calls_independent_statuses_and_not_released(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    llm_secret = "llm-key-7f0e9b1c3d5a8e2f"
    embedding_secret = "embedding-key-4c8a1e6f2b9d7e0a"
    monkeypatch.setenv("KD_LLM_API_KEY", llm_secret)
    monkeypatch.setenv("KD_PHASE4_EMBEDDING_KEY", embedding_secret)
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    report = _latest_report(kb_dir)
    runtime = report["runtime_audit"]
    assert runtime["calls"] == {"llm": 0, "embedding": 0}
    assert runtime["fallback"]["used"] is False
    assert runtime["budget_status"] == "within_budget"
    assert report["status"]["written"] is True
    assert report["status"]["writeback"] == "written"
    assert report["status"]["page_status"] == "published"
    assert report["status"]["provider_transport"] == "not_requested"
    assert report["status"]["claim_verification"] == "passed"
    assert report["runtime_audit"]["provider"]["llm"]["allowlist"] == "passed"
    assert report["runtime_audit"]["provider"]["embedding"]["allowlist"] == "passed"
    assert report["status"]["delivery_status"] == "not_released"
    assert report["status"]["agent_assisted"] is False
    assert report["status"]["human_reviewed"] is False
    assert report["status"]["machine_pass"] is True
    assert report["runtime_audit"]["question_set"]["positive_count"] == 17
    assert report["runtime_audit"]["question_set"]["negative_count"] == 3
    budget = report["runtime_audit"]["budget"]
    assert budget["timeout_seconds"] == 180
    assert budget["replay_limit"] == 1
    assert budget["provider_call_budget"] == 180
    assert budget["planned_generator_calls"] == 0
    assert budget["provider_calls_observed"] == 0
    assert budget["replay_calls"] == 0
    assert budget["timeout_exceeded"] is False
    assert budget["planned_generator_hard_cap"] == 180
    assert budget["wall_clock_target_seconds"] == 1800
    assert budget["wall_clock_hard_cap_seconds"] == 3600
    assert budget["wall_clock_elapsed_seconds"] >= 0
    serialized = json.dumps(report, ensure_ascii=False)
    assert "KD_PHASE4_EMBEDDING_KEY" in serialized or "credential_source" in serialized
    assert llm_secret not in serialized
    assert embedding_secret not in serialized
    assert "secret" not in serialized.lower()


def test_runtime_audit_preserves_fallback_as_not_released(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from knowledge_digest import pipeline
    from knowledge_digest.config import DigestSettings, EmbeddingSettings, SimilaritySettings
    from knowledge_digest.embedding import BackendResolution

    settings = DigestSettings(
        similarity=SimilaritySettings(
            backend="embedding",
            embedding=EmbeddingSettings(
                base_url="https://llm.paxszapp.com/v1",
                model="jina-embeddings",
                expected_dimension=1024,
                calibration_artifact=tmp_path / "calibration.json",
                api_key_env="KD_PHASE4_EMBEDDING_KEY",
            ),
        )
    )
    monkeypatch.setattr(
        pipeline,
        "resolve_similarity_backend",
        lambda _settings: BackendResolution(
            "embedding", "jaccard", "probe_identity_mismatch", probe_fingerprint="a" * 64
        ),
    )
    audit = pipeline._task0_runtime_audit(
        settings,
        {
            "requested_backend": "embedding",
            "effective_backend": "jaccard",
            "reason_code": "probe_identity_mismatch",
            "probe_fingerprint": "a" * 64,
        },
        source_count=1,
        cost={"provider_calls_observed": 0, "planned_generator_calls": 0, "elapsed_seconds": 1.0},
        page_statuses=["published"],
        writes=True,
    )
    assert audit["fallback"] == {
        "used": True,
        "from": "embedding",
        "to": "jaccard",
        "reason": "probe_identity_mismatch",
    }
    assert audit["delivery_status"] == "not_released"
    assert audit["provider"]["embedding"]["probe_fingerprint"] == "a" * 64


def test_runtime_budget_overflow_is_not_success() -> None:
    from knowledge_digest import pipeline
    from knowledge_digest.config import DigestSettings

    status = pipeline._task0_budget_status(
        {
            "planned_generator_calls": 181,
            "provider_calls_observed": 5,
            "replay_calls": 2,
            "timeout_exceeded": True,
            "elapsed_seconds": 3601,
        },
        source_count=1,
    )
    assert status == "exceeded"
    assert pipeline._task0_budget_status(
        {"elapsed_seconds": 1, "wall_clock_elapsed_seconds": 3601}, source_count=1
    ) == "exceeded"
    audit = pipeline._task0_runtime_audit(
        DigestSettings(),
        {"requested_backend": "jaccard", "effective_backend": "jaccard", "provider_calls_observed": 0},
        source_count=1,
        cost={"replay_calls": 2, "timeout_exceeded": True, "elapsed_seconds": 1.0},
        page_statuses=["published"],
        writes=True,
    )
    assert audit["budget_status"] == "exceeded"
    assert audit["page_status"] == "degraded"
    assert audit["budget"]["replay_calls"] == 2
    assert audit["budget"]["timeout_exceeded"] is True

    not_written = pipeline._task0_runtime_audit(
        DigestSettings(),
        {"requested_backend": "jaccard", "effective_backend": "jaccard", "provider_calls_observed": 0},
        source_count=1,
        cost={},
        page_statuses=["published"],
        writes=False,
    )
    assert not_written["page_status"] == "degraded"


def test_timeout_budget_reads_structured_round_status_only() -> None:
    from knowledge_digest import pipeline

    source_round = {
        "status": "valid",
        "stop_reason": "the source text mentions timeout but the call succeeded",
        "elapsed_ms": 1,
    }
    assert pipeline._digest_metrics(
        [{"draft_id": "d1", "planned_generator_calls": 1, "rounds": [source_round], "quality": {"faithfulness_status": "faithful"}}],
        [],
        [],
        dry_run=False,
        llm_enabled=True,
    )["cost"]["timeout_exceeded"] is False
    timeout_round = {**source_round, "status": "deadline_exceeded"}
    assert pipeline._digest_metrics(
        [{"draft_id": "d1", "planned_generator_calls": 1, "rounds": [timeout_round], "quality": {"faithfulness_status": "failed"}}],
        [],
        [],
        dry_run=False,
        llm_enabled=True,
    )["cost"]["timeout_exceeded"] is True


def test_runtime_audit_rejects_unallowlisted_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    from knowledge_digest import pipeline
    from knowledge_digest.config import DigestSettings

    monkeypatch.setenv("KD_LLM_MODEL", "unapproved-model")
    monkeypatch.setenv("KD_LLM_BASE_URL", "https://unapproved.example/v1")
    settings = DigestSettings(llm_enabled=True)
    assert pipeline._task0_llm_allowlist(settings) is False
    audit = pipeline._task0_runtime_audit(
        settings,
        {"requested_backend": "jaccard", "effective_backend": "jaccard"},
        source_count=1,
        cost={},
        page_statuses=["published"],
        writes=False,
    )
    assert audit["provider"]["llm"]["allowlist"] == "failed"
    assert audit["page_status"] == "degraded"


def test_runtime_audit_records_frozen_calibration_hash() -> None:
    from knowledge_digest import pipeline
    from knowledge_digest.config import DigestSettings, EmbeddingSettings, SimilaritySettings

    settings = DigestSettings(
        similarity=SimilaritySettings(
            backend="embedding",
            embedding=EmbeddingSettings(
                base_url="https://llm.paxszapp.com/v1",
                model="jina-embeddings",
                expected_dimension=1024,
                calibration_artifact=PROJECT_ROOT / "evidence/phase4/calibration-artifact.json",
                api_key_env="KD_PHASE4_EMBEDDING_KEY",
            ),
        )
    )
    audit = pipeline._task0_runtime_audit(
        settings,
        {
            "requested_backend": "embedding",
            "effective_backend": "embedding",
            "probe_fingerprint": "cc7ae744e79a19a32ca64d3274e11b3e2ea0611cf4c0f58cebc49e950fc6ed2c",
            "provider_calls_observed": 0,
        },
        source_count=1,
        cost={"provider_calls_observed": 0, "planned_generator_calls": 0, "elapsed_seconds": 1.0},
        page_statuses=["published"],
        writes=True,
    )
    assert audit["provider"]["embedding"] == {
        "model": "jina-embeddings",
        "endpoint": "https://llm.paxszapp.com/v1",
        "dimension": 1024,
        "probe_fingerprint": "cc7ae744e79a19a32ca64d3274e11b3e2ea0611cf4c0f58cebc49e950fc6ed2c",
        "calibration_sha256": "c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06",
        "credential_source": "environment:KD_PHASE4_EMBEDDING_KEY",
        "allowlist": "passed",
    }
    assert audit["provider"]["embedding"]["calibration_sha256"] == "c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06"
    assert audit["budget"]["wall_clock_target_seconds"] == 1800
    assert audit["budget"]["wall_clock_hard_cap_seconds"] == 3600


def test_growth_report_separates_business_growth_from_run_history(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)
    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    second = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    report = _latest_report(kb_dir)
    growth = report["growth_audit"]
    assert growth["anomaly"]["status"] == "none"
    assert growth["business_delta"]["source_snapshots"] == 0
    assert growth["business_delta"]["claims"] == 0
    assert growth["business_delta"]["duplicates"] == 0
    assert growth["business_delta"]["archive_records"] == 0
    assert growth["run_delta"] == 1


def test_growth_audit_locates_same_input_business_growth(tmp_path: Path) -> None:
    from knowledge_digest import pipeline
    from knowledge_digest.config import DigestSettings

    kb_dir = tmp_path / "kb"
    run_dir = kb_dir / "_digest" / "runs" / "run-2"
    run_dir.mkdir(parents=True)
    (kb_dir / "_digest" / "source-snapshots.jsonl").write_text(
        json.dumps({"source_id": "src-1", "snapshot_id": "snap-1"}) + "\n",
        encoding="utf-8",
    )
    (kb_dir / "_digest" / "source-manifest.json").write_text(
        json.dumps({"manifest_sha256": "manifest-1", "config_identity": "config-1"}),
        encoding="utf-8",
    )
    report_path = run_dir / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "cost": {},
                "growth_audit": {
                    "baseline": {
                        "source_snapshots": 0,
                        "claims": 0,
                        "duplicates": 0,
                        "archive_records": 0,
                        "run_reports": 1,
                        "manifest_sha256": "manifest-1",
                        "config_identity": "config-1",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    pipeline._write_task0_runtime_audit(
        report_path,
        DigestSettings(),
        {"requested_backend": "jaccard", "effective_backend": "jaccard", "provider_calls_observed": 0},
        kb_dir=kb_dir,
        config_identity="config-1",
        source_count=1,
        page_statuses=[],
        writes=False,
    )
    growth = json.loads(report_path.read_text(encoding="utf-8"))["growth_audit"]
    assert growth["same_input_snapshot_and_config"] is True
    assert growth["anomaly"]["status"] == "detected"
    assert growth["anomaly"]["records"]["source_snapshots"] == [
        {"ref": "_digest/source-snapshots.jsonl#line-1", "source_id": "src-1", "snapshot_id": "snap-1"}
    ]
