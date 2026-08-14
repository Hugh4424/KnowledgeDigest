"""Mini-task Phase 1: preflight plan and explicit execution policy."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
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


def _input(tmp_path: Path) -> Path:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    (items / "note.md").write_text("Preflight source evidence.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "note.md", "source_uri": "https://source.example/preflight"}) + "\n",
        encoding="utf-8",
    )
    return new_dir


def _config(tmp_path: Path, *, runtime: dict[str, object] | None = None) -> Path:
    value: dict[str, object] = {
        "similarity": {"backend": "jaccard"},
        "llm_enabled": False,
        "llm_summary_enabled": False,
    }
    if runtime is not None:
        value["runtime"] = runtime
    path = tmp_path / "config.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _three_input(tmp_path: Path) -> Path:
    new_dir = tmp_path / "three-new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    rows = []
    for index in range(3):
        name = f"note-{index}.md"
        sections = [
            f"## Section {index}-{section}\nEvidence {index}-{section}."
            for section in range(1, 7 if index == 0 else 6)
        ]
        (items / name).write_text("\n\n".join(sections) + "\n", encoding="utf-8")
        rows.append({"content_path": name, "source_uri": f"https://source.example/{name}"})
    (new_dir / "sources.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    return new_dir


def _latest_run(kb_dir: Path) -> Path:
    runs = sorted((kb_dir / "_digest" / "runs").iterdir(), key=lambda path: path.stat().st_mtime_ns)
    return runs[-1]


def test_offline_run_writes_plan_before_completion(tmp_path: Path) -> None:
    result = _run_digest(
        str(_input(tmp_path)),
        str(tmp_path / "kb"),
        "--config",
        str(_config(tmp_path)),
        "--no-llm",
    )

    assert result.returncode == 0, result.stderr
    run_dir = _latest_run(tmp_path / "kb")
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert plan["preflight"]["status"] == "passed"
    assert plan["planned_provider_calls"] == 0
    assert set(plan["policy"]) >= {
        "max_provider_calls",
        "max_replay_calls",
        "request_timeout_seconds",
        "max_wall_seconds",
        "concurrency",
    }
    assert report["execution"]["status"] == "completed"
    assert progress["completed_batches"] == len(plan["logical_batches"])
    assert progress["succeeded_batches"] == len(plan["logical_batches"])
    assert progress["failed_batches"] == 0
    serialized = (run_dir / "plan.json").read_text(encoding="utf-8")
    assert "Authorization" not in serialized
    assert "api_key" not in serialized.lower()


def test_missing_runtime_limit_blocks_before_provider(tmp_path: Path) -> None:
    result = _run_digest(
        str(_input(tmp_path)),
        str(tmp_path / "kb"),
        "--config",
        str(
            _config(
                tmp_path,
                runtime={
                    "max_provider_calls": 10,
                },
            )
        ),
        "--no-llm",
    )

    assert result.returncode != 0
    run_dir = _latest_run(tmp_path / "kb")
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert plan["preflight"]["status"] == "blocked"
    assert report["execution"]["status"] == "blocked"
    assert report["cost"]["provider_calls_observed"] == 0
    assert "missing" in result.stderr.lower() or "blocked" in result.stdout.lower()


def test_three_source_plan_counts_logical_batches_without_provider(tmp_path: Path) -> None:
    config = _config(tmp_path, runtime={
        "max_provider_calls": 15,
        "max_replay_calls": 1,
        "request_timeout_seconds": 30,
        "max_wall_seconds": 60,
        "concurrency": 2,
    })
    config.write_text(
        json.dumps({
            "similarity": {"backend": "jaccard"},
            "llm_enabled": True,
            "llm_format": "openai",
            "llm_batch_max_claims": 1,
            "runtime": json.loads(config.read_text(encoding="utf-8"))["runtime"],
        }),
        encoding="utf-8",
    )
    result = _run_digest(
        str(_three_input(tmp_path)),
        str(tmp_path / "three-kb"),
        "--config",
        str(config),
    )

    assert result.returncode != 0
    assert "planned_provider_calls=16" in result.stdout
    run_dir = _latest_run(tmp_path / "three-kb")
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert plan["source_count"] == 3
    assert plan["planned_provider_calls"] == 16
    assert len(plan["logical_batches"]) == 16
    assert report["cost"]["provider_calls_observed"] == 0
    assert report["execution"]["status"] == "blocked"


def test_heartbeat_updates_during_long_local_step(tmp_path: Path, monkeypatch) -> None:
    from knowledge_digest.runtime_status import RunStatus

    run_dir = tmp_path / "run"
    status = RunStatus(run_dir, total_batches=1, heartbeat_seconds=1)
    status.start()
    first = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))["last_update"]
    time.sleep(1.25)
    heartbeat = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    status.finish(status="completed", phase="completed")
    assert heartbeat["last_update"] > first
    assert heartbeat["last_update_reason"] == "heartbeat"


def test_provider_exception_finishes_progress_without_swallowing_error(tmp_path: Path) -> None:
    from knowledge_digest.runtime_status import RunStatus

    run_dir = tmp_path / "run"
    status = RunStatus(run_dir, total_batches=1, heartbeat_seconds=1)
    status.start()
    error = "provider failed for test"
    status.finish(status="failed", phase="provider", error=error)
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["execution_status"] == "failed"
    assert progress["last_error"] == error
    assert progress["last_update_reason"] == "finished"


def test_provider_failure_is_not_reported_as_completed(tmp_path: Path, monkeypatch) -> None:
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.errors import ValidationError
    from knowledge_digest.kb_structure import DEFAULT_ROOTS, parse_roots
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.pipeline import audit_run

    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "provider-failure-kb"
    paths = validate_paths(new_dir, kb_dir, allow_new_kb=True)
    monkeypatch.setenv("KD_LLM_MODEL", "qwen3.6")
    monkeypatch.setenv("KD_LLM_BASE_URL", "https://dashscope.in.whatspos.cn/v1")
    monkeypatch.setenv("KD_LLM_API_KEY", "test-key")

    def failing_generator(_context):
        raise ValidationError("llm", "provider", "provider request failed (test timeout)")

    report_path, _summary = audit_run(
        paths,
        DigestSettings(llm_enabled=True),
        DEFAULT_ROOTS if paths.initialize_new_kb else parse_roots(paths.structure_path),
        dry_run=False,
        generator=failing_generator,
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    progress = json.loads((report_path.parent / "progress.json").read_text(encoding="utf-8"))
    assert report["execution"]["status"] == "failed"
    assert report["execution"]["phase"] == "provider"
    assert report["status"]["page_status"] == "degraded"
    assert progress["execution_status"] == "failed"
    assert progress["failed_batches"] == 1


def test_integrated_provider_heartbeat_updates_before_fifteen_seconds(tmp_path: Path, monkeypatch) -> None:
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.kb_structure import DEFAULT_ROOTS
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.pipeline import audit_run

    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "slow-provider-kb"
    paths = validate_paths(new_dir, kb_dir, allow_new_kb=True)
    monkeypatch.setenv("KD_LLM_MODEL", "qwen3.6")
    monkeypatch.setenv("KD_LLM_BASE_URL", "https://dashscope.in.whatspos.cn/v1")
    monkeypatch.setenv("KD_LLM_API_KEY", "test-key")
    result: dict[str, object] = {}

    def slow_generator(context):
        time.sleep(11)
        return str(context["initial_body"])

    def run() -> None:
        result["value"] = audit_run(
            paths,
            DigestSettings(llm_enabled=True),
            DEFAULT_ROOTS,
            dry_run=False,
            generator=slow_generator,
        )

    worker = threading.Thread(target=run)
    worker.start()
    observed_heartbeat = False
    progress_path: Path | None = None
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and worker.is_alive():
        candidates = list((kb_dir / "_digest" / "runs").glob("*/progress.json"))
        if candidates:
            progress_path = candidates[0]
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            if progress["last_update_reason"] == "heartbeat":
                observed_heartbeat = True
                break
        time.sleep(0.1)
    worker.join(timeout=20)
    assert not worker.is_alive()
    assert observed_heartbeat
    assert progress_path is not None
    assert result["value"]


def test_keyboard_interrupt_finishes_as_cancelled(tmp_path: Path, monkeypatch) -> None:
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.kb_structure import DEFAULT_ROOTS
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.pipeline import audit_run

    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "cancelled-kb"
    paths = validate_paths(new_dir, kb_dir, allow_new_kb=True)
    monkeypatch.setenv("KD_LLM_MODEL", "qwen3.6")
    monkeypatch.setenv("KD_LLM_BASE_URL", "https://dashscope.in.whatspos.cn/v1")
    monkeypatch.setenv("KD_LLM_API_KEY", "test-key")

    def interrupting_generator(_context):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        audit_run(
            paths,
            DigestSettings(llm_enabled=True),
            DEFAULT_ROOTS,
            dry_run=False,
            generator=interrupting_generator,
        )
    run_dir = _latest_run(kb_dir)
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert report["execution"]["status"] == "cancelled"
    assert progress["execution_status"] == "cancelled"


def test_invalid_manifest_writes_failed_run_and_returns_nonzero(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    # The declared path no longer matches the actual input file.
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "missing.md", "source_uri": "https://source.example/missing"}) + "\n",
        encoding="utf-8",
    )
    result = _run_digest(
        str(new_dir),
        str(tmp_path / "kb"),
        "--config",
        str(_config(tmp_path)),
        "--no-llm",
    )
    assert result.returncode != 0
    run_dir = _latest_run(tmp_path / "kb")
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert plan["preflight"]["status"] == "failed"
    assert report["execution"]["status"] == "failed"
    assert report["execution"]["phase"] == "manifest"
    assert progress["execution_status"] == "failed"
    assert report["cost"]["provider_calls_observed"] == 0
