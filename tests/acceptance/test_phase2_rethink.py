"""Phase 1 acceptance coverage for risk routing and bounded rethink."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from knowledge_digest.config import DigestSettings, evaluate_risk
from knowledge_digest.draft import draft
from knowledge_digest.paths import DigestPaths
from knowledge_digest.recovery import (
    RecoveryPaths,
    acquire_lock,
    build_input_manifest,
    commit_staged_outputs,
    load_recovery_state,
    manifest_hash,
    mark_prepared,
    output_plan_hash,
    release_lock,
    stable_run_id,
    write_staged_file,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_digest(*args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "knowledge_digest.cli", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def _case(tmp_path: Path) -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(
        "---\ncontract_version: phase2\nroots: [pages, _archive, _queues]\nwhy_field: why\nversion_field: version\n---\n",
        encoding="utf-8",
    )
    return new_dir, kb_dir


def _write_source(new_dir: Path, text: str) -> None:
    (new_dir / "items" / "source.md").write_text(text, encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "source.md", "source_uri": "https://source.example/phase2"}) + "\n",
        encoding="utf-8",
    )


def _cluster(*, tier: str = "auto") -> list[dict[str, object]]:
    return [
        {
            "cluster_id": "cluster-1",
            "tier": tier,
            "cluster_tier": tier,
            "members": ["raw-1"],
            "decision_reason": "test fixture",
        }
    ]


def _items() -> list[dict[str, object]]:
    return [
        {
            "raw_id": "raw-1",
            "text": "Claim one.\nClaim two.\n",
            "source_uri": "https://source.example/one",
            "validation_status": "passed",
        }
    ]


def _decision(**overrides: object) -> list[dict[str, object]]:
    value: dict[str, object] = {
        "cluster_id": "cluster-1",
        "action": "new",
        "target_paths": [],
        "source_count": 1,
        "target_page_count": 0,
    }
    value.update(overrides)
    return [value]


def test_risk_rules_cover_boundaries_and_preserve_double_high_match() -> None:
    medium = evaluate_risk(
        {
            "cluster_tier": "auto",
            "action": "revise",
            "source_count": 1,
            "target_page_count": 0,
            "source_line_count": 225,
            "structured_line_ratio": 0.15,
            "coverage_risk": False,
            "estimated_claim_count": 8,
            "estimated_component_count": 4,
            "max_doc_lines": 300,
        }
    )
    assert medium["risk_level"] == "medium"
    assert medium["max_rounds"] == 1
    assert "structured_line_ratio.ge_0.15" in medium["rules_triggered"]

    high = evaluate_risk(
        {
            "cluster_tier": "auto",
            "action": "merge_multiple",
            "source_count": 1,
            "target_page_count": 2,
            "source_line_count": 1,
            "structured_line_ratio": 0.0,
            "coverage_risk": False,
            "estimated_claim_count": 1,
            "estimated_component_count": 1,
            "max_doc_lines": 300,
        }
    )
    assert high["risk_level"] == "high"
    assert high["max_rounds"] == 3
    assert {"action.merge_multiple", "target_page_count.ge_2"} <= set(high["rules_triggered"])


def test_high_risk_stops_after_newline_only_convergence(tmp_path: Path) -> None:
    def generator(context: dict[str, object]) -> str:
        return "Claim one.\nClaim two." if context["round_number"] == 1 else "Claim one.\r\nClaim two."

    result = draft(
        _decision(action="revise", target_paths=["pages/one.md"]),
        _cluster(tier="needs_review"),
        _items(),
        tmp_path,
        DigestSettings(),
        generator=generator,
    )[0]

    assert result["risk_decision"]["risk_level"] == "high"
    assert result["round_count"] == 2
    assert result["rethink_status"] == "converged"
    assert result["rounds"][-1]["stop_reason"] == "converged"


def test_invalid_round_consumes_budget_but_does_not_write_back(tmp_path: Path) -> None:
    def generator(context: dict[str, object]) -> dict[str, object]:
        if context["round_number"] == 2:
            return {"final_body": "missing source claim"}
        return {"final_body": "Claim one.\nClaim two."}

    result = draft(
        _decision(action="revise", target_paths=["pages/one.md"]),
        _cluster(tier="needs_review"),
        _items(),
        tmp_path,
        DigestSettings(),
        generator=generator,
    )[0]

    assert [row["status"] for row in result["rounds"]] == ["valid", "invalid", "valid"]
    assert result["selected_round"] == 3
    assert result["rounds"][1]["stop_reason"] == "candidate failed faithfulness hard gate"
    assert result["fallback_reason"] == "invalid round rejected; retained latest valid round"


def test_all_invalid_rounds_use_claim_fallback(tmp_path: Path) -> None:
    result = draft(
        _decision(action="revise", target_paths=["pages/one.md"]),
        _cluster(tier="needs_review"),
        _items(),
        tmp_path,
        DigestSettings(),
        generator=lambda _context: {"final_body": "not sourced"},
    )[0]

    assert result["rethink_status"] == "fallback"
    assert result["selected_round"] is None
    assert result["fallback_reason"] == "no valid round; used claim fallback"
    assert "Claim one." in result["final_body"]
    assert "Claim two." in result["final_body"]
    rounds = json.loads((tmp_path / "s4" / "rounds.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert rounds["benefit_status"] == "unmeasured"


def test_run_identity_is_stable_and_tracks_input_and_settings(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _write_source(new_dir, "Stable source claim.\n")
    paths = DigestPaths(new_dir, new_dir / "items", kb_dir, kb_dir / "kb.structure.md")
    first_manifest = build_input_manifest(paths, DigestSettings(), ("pages", "_archive", "_queues"))
    second_manifest = build_input_manifest(paths, DigestSettings(), ("pages", "_archive", "_queues"))
    assert stable_run_id(first_manifest) == stable_run_id(second_manifest)
    assert manifest_hash(first_manifest) == manifest_hash(second_manifest)

    _write_source(new_dir, "Changed source claim.\n")
    changed_manifest = build_input_manifest(paths, DigestSettings(), ("pages", "_archive", "_queues"))
    assert stable_run_id(changed_manifest) != stable_run_id(first_manifest)

    changed_settings = build_input_manifest(paths, DigestSettings(top_k=3), ("pages", "_archive", "_queues"))
    assert stable_run_id(changed_settings) != stable_run_id(changed_manifest)


def test_commit_persists_state_and_staged_output_hashes(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _write_source(new_dir, "Prepare must not mutate the formal knowledge base.\n")
    before = {
        path.relative_to(kb_dir).as_posix(): path.read_bytes()
        for path in kb_dir.rglob("*")
        if path.is_file()
    }

    result = _run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 0, result.stderr
    assert "committed" in result.stdout
    after_formal = {
        path.relative_to(kb_dir).as_posix(): path.read_bytes()
        for path in kb_dir.rglob("*")
        if path.is_file() and "_digest/runs/" not in path.relative_to(kb_dir).as_posix()
        and "_digest/recovery/" not in path.relative_to(kb_dir).as_posix()
    }
    assert after_formal != before
    assert (kb_dir / "pages" / "digest" / "draft-1.md").is_file()

    recovery_root = kb_dir / "_digest" / "recovery"
    run_id = next(path.name for path in recovery_root.iterdir() if path.is_dir())
    recovery = RecoveryPaths.for_run(kb_dir, run_id)
    state = json.loads(recovery.state.read_text(encoding="utf-8"))
    assert state["status"] == "committed"
    assert state["staged_outputs"]
    for output in state["staged_outputs"]:
        staged = recovery.root / str(output["staged_path"])
        assert output["operation"] == "replace"
        assert hashlib.sha256(staged.read_bytes()).hexdigest() == output["after_sha256"]
    assert len(state["completed_outputs"]) == len(state["staged_outputs"])


def test_second_writer_is_rejected_and_safe_prepare_can_be_taken_over(tmp_path: Path) -> None:
    _, kb_dir = _case(tmp_path)
    first, state = acquire_lock(kb_dir, "run-lock", input_manifest_hash="manifest", target_kb=kb_dir)
    try:
        try:
            acquire_lock(kb_dir, "run-lock", input_manifest_hash="manifest", target_kb=kb_dir)
        except ValueError as error:
            assert "CONCURRENT_WRITER_NOT_ALLOWED" in str(error)
        else:
            raise AssertionError("second writer unexpectedly acquired the lock")
        state = mark_prepared(kb_dir, state, staged_outputs=[], plan_hash="empty-plan")
    finally:
        release_lock(first)

    second, recovered = acquire_lock(kb_dir, "run-lock", input_manifest_hash="manifest", target_kb=kb_dir)
    try:
        assert recovered["recovery_attempts"] == 1
        assert recovered["execution_id"] != state["execution_id"]
    finally:
        release_lock(second)


def test_dry_run_does_not_create_lock_or_recovery_state(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _write_source(new_dir, "Dry-run must not create recovery state.\n")
    result = _run_digest(str(new_dir), str(kb_dir), "--dry-run")
    assert result.returncode == 0, result.stderr
    assert not (kb_dir / "_digest" / "recovery").exists()
    assert not (kb_dir / "pages").exists()


def _formal_snapshot(kb_dir: Path) -> dict[str, bytes]:
    return {
        path.relative_to(kb_dir).as_posix(): path.read_bytes()
        for path in kb_dir.rglob("*")
        if path.is_file()
        and "_digest/runs/" not in path.relative_to(kb_dir).as_posix()
        and "_digest/recovery/" not in path.relative_to(kb_dir).as_posix()
    }


def _manual_output(
    kb_dir: Path,
    run_id: str,
    relative_target: str,
    *,
    before: bytes | None,
    after: bytes | None,
) -> dict[str, object]:
    target = kb_dir / relative_target
    if before is None:
        target.unlink(missing_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before)
    recovery = RecoveryPaths.for_run(kb_dir, run_id)
    staged_path = None
    if after is not None:
        staged_path = write_staged_file(recovery.staging, relative_target, after)
    return {
        "operation": "replace" if after is not None else "delete",
        "kind": "archive_cleanup" if after is None else "page",
        "relative_target": relative_target,
        "staged_path": staged_path,
        "size_bytes": len(after) if after is not None else 0,
        "before_sha256": hashlib.sha256(before).hexdigest() if before is not None else None,
        "after_sha256": hashlib.sha256(after).hexdigest() if after is not None else None,
        "status": "pending",
    }


def test_partial_commit_resumes_without_replacing_completed_output(tmp_path: Path) -> None:
    _, kb_dir = _case(tmp_path)
    run_id = "run-partial"
    handle, state = acquire_lock(kb_dir, run_id, input_manifest_hash="manifest", target_kb=kb_dir)
    outputs = [
        _manual_output(kb_dir, run_id, "pages/one.md", before=b"old one", after=b"new one"),
        _manual_output(kb_dir, run_id, "pages/two.md", before=None, after=b"new two"),
    ]
    state = mark_prepared(kb_dir, state, staged_outputs=outputs, plan_hash=output_plan_hash(outputs))
    release_lock(handle)

    with pytest.raises(RuntimeError, match="simulated commit interruption"):
        commit_staged_outputs(kb_dir, state, fail_after=1)

    interrupted = load_recovery_state(kb_dir, run_id)
    assert interrupted is not None
    assert interrupted["status"] == "committing"
    assert (kb_dir / "pages/one.md").read_bytes() == b"new one"
    assert not (kb_dir / "pages/two.md").exists()

    resumed_handle, resumed = acquire_lock(kb_dir, run_id, input_manifest_hash="manifest", target_kb=kb_dir)
    try:
        committed = commit_staged_outputs(kb_dir, resumed, handle=resumed_handle)
    finally:
        release_lock(resumed_handle)
    assert committed["status"] == "committed"
    assert (kb_dir / "pages/one.md").read_bytes() == b"new one"
    assert (kb_dir / "pages/two.md").read_bytes() == b"new two"
    assert len(committed["completed_outputs"]) == 2


def test_commit_rejects_baseline_conflict_and_missing_staged_output(tmp_path: Path) -> None:
    _, kb_dir = _case(tmp_path)
    run_id = "run-invalid"
    handle, state = acquire_lock(kb_dir, run_id, input_manifest_hash="manifest", target_kb=kb_dir)
    output = _manual_output(kb_dir, run_id, "pages/conflict.md", before=b"before", after=b"after")
    state = mark_prepared(kb_dir, state, staged_outputs=[output], plan_hash=output_plan_hash([output]))
    release_lock(handle)
    (kb_dir / "pages/conflict.md").write_bytes(b"external change")
    with pytest.raises(ValueError, match="RECOVERY_STATE_INVALID") as conflict:
        commit_staged_outputs(kb_dir, state)
    assert "before/after hash conflict" in str(conflict.value)
    assert (kb_dir / "pages/conflict.md").read_bytes() == b"external change"

    missing_run_id = "run-missing"
    missing_handle, missing_state = acquire_lock(
        kb_dir, missing_run_id, input_manifest_hash="manifest", target_kb=kb_dir
    )
    missing = _manual_output(kb_dir, missing_run_id, "pages/missing.md", before=None, after=b"after")
    staged_path = RecoveryPaths.for_run(kb_dir, missing_run_id).root / str(missing["staged_path"])
    missing_state = mark_prepared(
        kb_dir,
        missing_state,
        staged_outputs=[missing],
        plan_hash=output_plan_hash([missing]),
    )
    release_lock(missing_handle)
    staged_path.unlink()
    with pytest.raises(ValueError, match="RECOVERY_OUTPUT_MISSING"):
        commit_staged_outputs(kb_dir, missing_state)
    assert not (kb_dir / "pages/missing.md").exists()


def test_delete_tombstone_is_idempotent_and_preserves_metadata_file(tmp_path: Path) -> None:
    _, kb_dir = _case(tmp_path)
    target = kb_dir / "_archive" / "expired" / "page.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"expired body")
    metadata = kb_dir / "_archive" / "records.jsonl"
    metadata.write_text('{"content_retained": true}\n', encoding="utf-8")
    run_id = "run-tombstone"
    handle, state = acquire_lock(kb_dir, run_id, input_manifest_hash="manifest", target_kb=kb_dir)
    output = _manual_output(
        kb_dir,
        run_id,
        "_archive/expired/page.md",
        before=b"expired body",
        after=None,
    )
    state = mark_prepared(kb_dir, state, staged_outputs=[output], plan_hash=output_plan_hash([output]))
    release_lock(handle)
    resumed_handle, resumed = acquire_lock(kb_dir, run_id, input_manifest_hash="manifest", target_kb=kb_dir)
    try:
        committed = commit_staged_outputs(kb_dir, resumed, handle=resumed_handle)
    finally:
        release_lock(resumed_handle)
    assert committed["status"] == "committed"
    assert not target.exists()
    assert metadata.read_text(encoding="utf-8") == '{"content_retained": true}\n'


def test_same_input_after_commit_returns_already_committed_without_formal_duplicates(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _write_source(new_dir, "Idempotent source claim.\n")
    first = _run_digest(str(new_dir), str(kb_dir))
    assert first.returncode == 0, first.stderr
    before = _formal_snapshot(kb_dir)
    second = _run_digest(str(new_dir), str(kb_dir))
    assert second.returncode == 0, second.stderr
    assert "already_committed" in second.stdout
    assert _formal_snapshot(kb_dir) == before


def test_phase4_regression_targets_and_cli_boundary_remain_explicit() -> None:
    """Keep the legacy regression entry points and the CLI scope auditable."""
    assert (PROJECT_ROOT / "tests/acceptance/test_phase0_digest.py").is_file()
    assert (PROJECT_ROOT / "tests/acceptance/test_phase1_loss_prevention.py").is_file()

    help_result = subprocess.run(
        [sys.executable, "-m", "knowledge_digest.cli", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")},
    )
    assert help_result.returncode == 0
    for option in ("--config", "--dry-run", "--max-doc-lines"):
        assert option in help_result.stdout
    for out_of_scope_option in ("--resume", "--run-id"):
        assert out_of_scope_option not in help_result.stdout

    cli_source = (PROJECT_ROOT / "src/knowledge_digest/cli.py").read_text(encoding="utf-8")
    assert "scheduler" not in cli_source.casefold()
    assert "daemon" not in cli_source.casefold()
    assert "model judge" not in cli_source.casefold()


def test_insufficient_signal_only_commits_its_queue_entry(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    (new_dir / "items" / "weak.md").write_text("one two\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "weak.md", "source_uri": "https://source.example/weak"}) + "\n",
        encoding="utf-8",
    )
    result = _run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 0, result.stderr
    assert not list((kb_dir / "pages").rglob("*.md"))
    assert (kb_dir / "_queues" / "insufficient_signal.md").read_text(encoding="utf-8").count("cluster-1") == 1
    assert not (kb_dir / "_digest" / "source-index.jsonl").exists()
    assert not (kb_dir / "_digest" / "claim-history.jsonl").exists()
