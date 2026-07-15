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


def test_s1_ingest_module_exports_ingest() -> None:
    from knowledge_digest.ingest import ingest

    assert callable(ingest)


def test_s2_cluster_module_exports_cluster() -> None:
    from knowledge_digest.cluster import cluster

    assert callable(cluster)


def test_s3_retrieve_module_exports_retrieve() -> None:
    from knowledge_digest.retrieve import retrieve

    assert callable(retrieve)


def test_s4_draft_module_exports_draft() -> None:
    from knowledge_digest.draft import draft

    assert callable(draft)


def test_jsonl_module_exports_read_write() -> None:
    from knowledge_digest.jsonl import read_jsonl, write_jsonl

    assert callable(write_jsonl)
    assert callable(read_jsonl)


def test_queues_module_exports_write_queues() -> None:
    from knowledge_digest.queues import write_queues

    assert callable(write_queues)


def test_faithfulness_module_verifies_claims() -> None:
    from knowledge_digest.faithfulness import faithfulness_check, verify_claims

    assert callable(verify_claims)
    assert callable(faithfulness_check)


def test_phase0_digest_fixture_files_exist() -> None:
    fixture_root = PROJECT_ROOT / "tests" / "fixtures" / "phase0_digest"
    assert (fixture_root / "new_dir" / "items" / "filter-update.md").exists()
    assert (fixture_root / "new_dir" / "items" / "chart-faq.md").exists()
    assert (fixture_root / "new_dir" / "items" / "empty-shell.md").exists()
    assert (fixture_root / "new_dir" / "items" / "long-release.md").exists()
    assert (fixture_root / "new_dir" / "items" / "filter-duplicate.md").exists()
    assert (fixture_root / "new_dir" / "sources.jsonl").exists()
    assert (fixture_root / "kb_dir" / "pages" / "goinsight" / "filtering.md").exists()
    assert (fixture_root / "kb_dir" / "pages" / "goinsight" / "chart-types.md").exists()


def test_digest_runs_s1_through_s4_with_traceable_outputs(tmp_path: Path) -> None:
    """The runnable slice keeps source material through ingest, decisions, and drafts."""
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (kb_dir / "kb.structure.md").write_text("---\npage_root: pages\n---\n", encoding="utf-8")
    items = new_dir / "items"
    (items / "filter-update.md").write_text(
        "# Filter update\nfilter field supports status=active.\n"
        "FAQ: Why is my filter empty?\nError E_FILTER_17.\n"
        "See https://design.example/filter.\n",
        encoding="utf-8",
    )
    (items / "filter-duplicate.md").write_text(
        (items / "filter-update.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (items / "chart-faq.md").write_text(
        "# Chart and filter FAQ\nChart type filtering uses the filter field.\n"
        "FAQ: Which chart type supports active filters?\n",
        encoding="utf-8",
    )
    (items / "empty-shell.md").write_text("Home | Navigation | Login\n", encoding="utf-8")
    (items / "long-release.md").write_text(
        "\n".join(f"release detail {number}" for number in range(6)) + "\n",
        encoding="utf-8",
    )
    (new_dir / "sources.jsonl").write_text(
        "\n".join(
            json.dumps({"content_path": name, "source_uri": f"https://source.example/{name}"})
            for name in ("filter-update.md", "filter-duplicate.md", "chart-faq.md", "empty-shell.md", "long-release.md")
        )
        + "\n",
        encoding="utf-8",
    )
    pages = kb_dir / "pages" / "goinsight"
    pages.mkdir(parents=True)
    (pages / "filtering.md").write_text("# Filtering\nfilter field and status options\n", encoding="utf-8")
    (pages / "chart-types.md").write_text("# Chart types\nchart type options and rules\n", encoding="utf-8")

    result = run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "3")

    assert result.returncode == 0, result.stderr
    run_dir = next((kb_dir / "_digest" / "runs").iterdir())
    raw_items = [json.loads(line) for line in (run_dir / "s1" / "raw-items.jsonl").read_text(encoding="utf-8").splitlines()]
    duplicates = [json.loads(line) for line in (run_dir / "s1" / "duplicates.jsonl").read_text(encoding="utf-8").splitlines()]
    failures = [json.loads(line) for line in (run_dir / "s1" / "ingest-failed.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(raw_items) == 3
    assert len(duplicates) == 1
    assert failures[0]["path"].endswith("empty-shell.md")
    assert all("empty-shell" not in item["source_uri"] for item in raw_items)

    clusters = [json.loads(line) for line in (run_dir / "s2" / "clusters.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(cluster["tier"] and cluster["decision_reason"] for cluster in clusters)
    decisions = [json.loads(line) for line in (run_dir / "s3" / "evolution-decisions.jsonl").read_text(encoding="utf-8").splitlines()]
    merge = next(decision for decision in decisions if decision["action"] == "merge_multiple")
    assert len(merge["candidate_paths"]) >= 2
    assert len(merge["candidate_paths"]) == len(merge["candidate_scores"])

    drafts = [json.loads(line) for line in (run_dir / "s4" / "drafts.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(draft["claims"] and draft["provenance"] for draft in drafts)
    assert all("empty-shell" not in uri for draft in drafts for uri in draft["provenance"])
    split_suggestions = [json.loads(line) for line in (run_dir / "s4" / "split-suggestions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert split_suggestions and split_suggestions[0]["reason"] == "max_doc_lines exceeded"
