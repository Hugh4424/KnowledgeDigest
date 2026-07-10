"""Acceptance contract for the first runnable KnowledgeDigest slice."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_digest(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    source_root = str(PROJECT_ROOT / "src")
    env["PYTHONPATH"] = source_root + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "knowledge_digest.cli", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def copy_fixture_layout(tmp_path: Path) -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    new_dir.mkdir()
    (new_dir / "items").mkdir()
    (new_dir / "entry.md").write_text("# Candidate\n", encoding="utf-8")
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    structure = PROJECT_ROOT / "tests" / "fixtures" / "phase0_digest" / "kb.structure.md"
    (kb_dir / "kb.structure.md").write_text(structure.read_text(encoding="utf-8"), encoding="utf-8")
    return new_dir, kb_dir


def test_digest_cli_contract_accepts_new_and_kb_directories() -> None:
    result = run_digest("--help")

    assert result.returncode == 0, result.stderr
    assert "usage" in result.stdout.lower()
    assert "new_dir" in result.stdout
    assert "kb_dir" in result.stdout


def test_digest_missing_inputs_reports_validation_error_for_missing_positionals() -> None:
    result = run_digest("--dry-run")

    assert result.returncode == 1
    assert "validate" in result.stderr.lower()
    assert "new_dir" in result.stderr
    assert "kb_dir" in result.stderr


def test_digest_missing_inputs_reports_actionable_validation_errors(tmp_path: Path) -> None:
    missing_new_dir = tmp_path / "missing-new"
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    result = run_digest(str(missing_new_dir), str(kb_dir), "--dry-run")

    assert result.returncode == 1
    assert "validate" in result.stderr.lower()
    assert str(missing_new_dir) in result.stderr
    assert "missing" in result.stderr.lower()
    assert "rerun" in result.stderr.lower()

    new_dir = tmp_path / "new"
    new_dir.mkdir()
    (new_dir / "items").mkdir()
    result = run_digest(str(new_dir), str(kb_dir), "--dry-run")

    assert result.returncode == 1
    assert "validate" in result.stderr.lower()
    assert str(kb_dir / "kb.structure.md") in result.stderr
    assert "missing" in result.stderr.lower()
    assert "rerun" in result.stderr.lower()


def test_digest_cli_contract_reads_json_config_defaults_and_options(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    config_path = tmp_path / "digest.json"
    config_path.write_text("{}", encoding="utf-8")

    result = run_digest(str(new_dir), str(kb_dir), "--config", str(config_path), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "top_k=5" in result.stdout
    assert "high=0.90" in result.stdout
    assert "medium=0.80" in result.stdout
    assert "max_lines=300" in result.stdout

    config_path.write_text(
        json.dumps({"top_k": 3, "high": 0.95, "medium": 0.85, "max_lines": 120}),
        encoding="utf-8",
    )
    result = run_digest(str(new_dir), str(kb_dir), "--config", str(config_path), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "top_k=3" in result.stdout
    assert "high=0.95" in result.stdout
    assert "medium=0.85" in result.stdout
    assert "max_lines=120" in result.stdout


def test_digest_cli_contract_reports_validation_error_for_invalid_json_config(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    config_path = tmp_path / "digest.json"
    config_path.write_text("{not-json}", encoding="utf-8")

    result = run_digest(str(new_dir), str(kb_dir), "--config", str(config_path), "--dry-run")

    assert result.returncode == 1
    assert "validate" in result.stderr.lower()
    assert str(config_path) in result.stderr
    assert "json" in result.stderr.lower()


def test_digest_cli_contract_validation_errors_identify_the_failing_stage(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    arguments_result = run_digest("--dry-run")

    assert arguments_result.returncode == 1
    assert "stage=arguments" in arguments_result.stderr

    config_path = tmp_path / "digest.json"
    config_path.write_text("{not-json}", encoding="utf-8")

    config_result = run_digest(str(new_dir), str(kb_dir), "--config", str(config_path), "--dry-run")

    assert config_result.returncode == 1
    assert "stage=config" in config_result.stderr

    missing_path_result = run_digest(str(tmp_path / "missing-new"), str(kb_dir), "--dry-run")

    assert missing_path_result.returncode == 1
    assert "stage=paths" in missing_path_result.stderr

    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, kb_dir / "_digest", target_is_directory=True)
    audit_result = run_digest(str(new_dir), str(kb_dir), "--dry-run")

    assert audit_result.returncode == 1
    assert "stage=audit_run" in audit_result.stderr


def test_digest_dry_run_contract_audits_structure_with_defaults_without_writing(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}

    result = run_digest(str(new_dir), str(kb_dir), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout.lower()
    assert "notes" in result.stdout
    assert "top_k=5" in result.stdout
    assert "high=0.90" in result.stdout
    assert "medium=0.80" in result.stdout
    assert "max_lines=300" in result.stdout
    report_paths = list((kb_dir / "_digest" / "runs").glob("*/report.json"))
    assert len(report_paths) == 1
    assert json.loads(report_paths[0].read_text(encoding="utf-8"))["roots"] == ["notes"]
    assert not (kb_dir / "notes").exists()

    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    run_dir = report_paths[0].parent.relative_to(tmp_path)
    assert after - before == {
        Path("kb/_digest"),
        Path("kb/_digest/runs"),
        run_dir,
        report_paths[0].relative_to(tmp_path),
    }


def test_digest_dry_run_contract_counts_only_ingestible_item_types(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    items_dir = new_dir / "items"
    (items_dir / "note.md").write_text("# Note\n", encoding="utf-8")
    (items_dir / "transcript.txt").write_text("Transcript\n", encoding="utf-8")
    (items_dir / "metadata.json").write_text("{}\n", encoding="utf-8")
    (items_dir / "ignored.pdf").write_bytes(b"not an ingestible source")

    result = run_digest(str(new_dir), str(kb_dir), "--dry-run")

    assert result.returncode == 0, result.stderr
    report_path = next((kb_dir / "_digest" / "runs").glob("*/report.json"))
    assert json.loads(report_path.read_text(encoding="utf-8"))["source_notes"] == 3
    assert "audited 3 source note(s)" in result.stdout


def test_digest_cli_contract_accepts_required_threshold_option_names_and_config_keys(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    config_path = tmp_path / "digest.json"
    config_path.write_text(
        json.dumps(
            {
                "top_k": 4,
                "cluster_auto_threshold": 0.93,
                "cluster_review_threshold": 0.83,
                "max_doc_lines": 111,
            }
        ),
        encoding="utf-8",
    )

    result = run_digest(
        str(new_dir),
        str(kb_dir),
        "--config",
        str(config_path),
        "--cluster-auto-threshold",
        "0.96",
        "--cluster-review-threshold",
        "0.86",
        "--max-doc-lines",
        "222",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert "top_k=4" in result.stdout
    assert "high=0.96" in result.stdout
    assert "medium=0.86" in result.stdout
    assert "max_lines=222" in result.stdout


def test_digest_cli_contract_reads_page_archive_and_queue_root_keys(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (kb_dir / "kb.structure.md").write_text(
        "---\npage_root: pages-custom\narchive_root: archive-custom\nqueue_root: queue-custom\n---\n",
        encoding="utf-8",
    )

    result = run_digest(str(new_dir), str(kb_dir), "--dry-run")

    assert result.returncode == 0, result.stderr
    report_path = next((kb_dir / "_digest" / "runs").glob("*/report.json"))
    assert json.loads(report_path.read_text(encoding="utf-8"))["roots"] == [
        "pages-custom",
        "archive-custom",
        "queue-custom",
    ]


def test_digest_dry_run_contract_rejects_escaping_digest_symlink(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, kb_dir / "_digest", target_is_directory=True)

    result = run_digest(str(new_dir), str(kb_dir), "--dry-run")

    assert result.returncode == 1
    assert "validate" in result.stderr.lower()
    assert str(kb_dir / "_digest") in result.stderr
    assert "symlink" in result.stderr.lower()
    assert "rerun" in result.stderr.lower()
    assert list(outside.iterdir()) == []
