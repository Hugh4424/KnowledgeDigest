"""Phase 1 acceptance coverage for risk routing and bounded rethink."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from knowledge_digest.config import DigestSettings
from knowledge_digest.draft import draft
from knowledge_digest.paths import DigestPaths


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


def test_valid_single_round_is_selected_without_fallback(tmp_path: Path) -> None:
    result = draft(
        _decision(action="revise", target_paths=["pages/one.md"]),
        _cluster(tier="needs_review"),
        _items(),
        tmp_path,
        DigestSettings(),
        generator=lambda _context: "Claim one.\nClaim two.",
    )[0]

    assert result["round_count"] == 1
    assert result["rethink_status"] == "completed"
    assert result["selected_round"] == 1
    assert result["fallback_reason"] is None
    assert [row["status"] for row in result["rounds"]] == ["valid"]


def test_invalid_candidate_is_rejected_and_recorded(tmp_path: Path) -> None:
    result = draft(
        _decision(action="revise", target_paths=["pages/one.md"]),
        _cluster(tier="needs_review"),
        _items(),
        tmp_path,
        DigestSettings(),
        generator=lambda _context: {"final_body": "missing source claim"},
    )[0]

    assert [row["status"] for row in result["rounds"]] == ["invalid"]
    assert result["rounds"][0]["stop_reason"] == "candidate failed faithfulness hard gate"
    assert result["selected_round"] is None


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


def test_writeback_lands_pages_directly_in_the_real_kb(tmp_path: Path) -> None:
    """Formal outputs must appear in kb_dir itself, not in a staged clone."""
    new_dir, kb_dir = _case(tmp_path)
    _write_source(new_dir, "Direct writes must land in the formal knowledge base.\n")
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
    }
    assert after_formal != before
    assert (kb_dir / "pages" / "digest" / "draft-1.md").is_file()
    assert (kb_dir / "_digest" / "claim-history.jsonl").is_file()


def test_dry_run_writes_no_formal_knowledge_base_files(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _write_source(new_dir, "Dry-run must not touch the formal knowledge base.\n")
    result = _run_digest(str(new_dir), str(kb_dir), "--dry-run")
    assert result.returncode == 0, result.stderr
    assert not (kb_dir / "pages").exists()
    assert not (kb_dir / "_digest" / "claim-history.jsonl").exists()


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
