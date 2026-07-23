"""Acceptance contract for the first runnable KnowledgeDigest slice."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


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
    structure_text = structure.read_text(encoding="utf-8")
    structure_text = structure_text.replace(
        "---\n", "---\nwhy_field: why\nversion_field: version\n", 1
    )
    (kb_dir / "kb.structure.md").write_text(structure_text, encoding="utf-8")
    declare_sources(new_dir)
    return new_dir, kb_dir


def declare_sources(new_dir: Path, *content_paths: str) -> None:
    rows = [
        json.dumps(
            {
                "content_path": content_path,
                "source_uri": f"https://source.example/{content_path}",
            }
        )
        for content_path in content_paths
    ]
    (new_dir / "sources.jsonl").write_text(
        "\n".join(rows) + ("\n" if rows else ""), encoding="utf-8"
    )


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
    declare_sources(new_dir, "items/note.md", "items/transcript.txt", "items/metadata.json")

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
        "---\npage_root: pages-custom\narchive_root: archive-custom\n"
        "queue_root: queue-custom\nwhy_field: why\nversion_field: version\n---\n",
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
    (kb_dir / "kb.structure.md").write_text(
        "---\npage_root: pages\nwhy_field: why\nversion_field: version\n---\n",
        encoding="utf-8",
    )
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
    declare_sources(
        new_dir,
        "filter-update.md",
        "filter-duplicate.md",
        "chart-faq.md",
        "empty-shell.md",
        "long-release.md",
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


def test_s5_writeback_reports_completed_atomic_page_writes(tmp_path: Path) -> None:
    """A completed run records every formal page write and leaves a complete page."""
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (new_dir / "items" / "release.md").write_text(
        "# Release note\nThe digest command supports source provenance.\n",
        encoding="utf-8",
    )
    declare_sources(new_dir, "release.md")

    result = run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 0, result.stderr
    run_dir = next((kb_dir / "_digest" / "runs").iterdir())
    write_report = run_dir / "s5" / "write-report.jsonl"
    assert write_report.is_file()
    writes = [json.loads(line) for line in write_report.read_text(encoding="utf-8").splitlines()]
    assert writes
    assert all({"target_path", "action", "status"} <= write.keys() for write in writes)
    assert all(write["status"] == "success" for write in writes)
    for write in writes:
        target_path = Path(write["target_path"])
        target = target_path if target_path.is_absolute() else kb_dir / target_path
        assert target.is_file()
        assert target.read_text(encoding="utf-8").strip()


def test_s6_provenance_audit_keeps_only_valid_final_sources(tmp_path: Path) -> None:
    """Final claims are auditable and never retain an empty-shell source."""
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    items_dir = new_dir / "items"
    (items_dir / "supported.md").write_text(
        "# Supported change\nThe filter accepts status=active.\n",
        encoding="utf-8",
    )
    (items_dir / "empty-shell.md").write_text("Home | Navigation | Login\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        "\n".join(
            (
                json.dumps(
                    {
                        "content_path": "supported.md",
                        "source_uri": "https://source.example/supported",
                    }
                ),
                json.dumps(
                    {
                        "content_path": "empty-shell.md",
                        "source_uri": "https://source.example/empty-shell",
                    }
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 0, result.stderr
    run_dir = next((kb_dir / "_digest" / "runs").iterdir())
    provenance_audit = run_dir / "s6" / "provenance-audit.jsonl"
    assert provenance_audit.is_file()
    audit_rows = [json.loads(line) for line in provenance_audit.read_text(encoding="utf-8").splitlines()]
    assert audit_rows
    assert all(
        {"claim_id", "claim_body", "source_uri", "source_status", "target_path"} <= row.keys()
        for row in audit_rows
    )
    assert all(row["source_uri"] for row in audit_rows)
    assert all(row["source_status"] != "empty_shell" for row in audit_rows)
    assert all("empty-shell" not in row["source_uri"] for row in audit_rows)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _single_run_dir(kb_dir: Path) -> Path:
    run_dirs = list((kb_dir / "_digest" / "runs").iterdir())
    assert len(run_dirs) == 1
    return run_dirs[0]


def test_s5_atomic_failure_keeps_original_page_and_records_failed_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S5 failure must leave no half-written page and must remain auditable."""
    from knowledge_digest.errors import ValidationError
    from knowledge_digest.paths import DigestPaths
    from knowledge_digest.writeback import writeback
    import knowledge_digest.writeback as writeback_module

    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    target = kb_dir / "notes" / "existing.md"
    target.parent.mkdir()
    original = "# Original\n\ncomplete old page\n"
    target.write_text(original, encoding="utf-8")
    run_dir = kb_dir / "_digest" / "runs" / "atomic-failure"
    real_replace = writeback_module.os.replace

    def fail_target_replace(source: object, destination: object) -> None:
        if Path(destination) == target:
            raise OSError("simulated replace failure")
        real_replace(source, destination)

    monkeypatch.setattr(writeback_module.os, "replace", fail_target_replace)
    paths = DigestPaths(
        new_dir=new_dir,
        items_dir=new_dir / "items",
        kb_dir=kb_dir,
        structure_path=kb_dir / "kb.structure.md",
    )
    draft = {
        "draft_id": "draft-failure",
        "action": "revise",
        "target_paths": ["notes/existing.md"],
        "final_body": "replacement body",
        "claims": [{"text": "replacement body", "source_uri": "https://source.example/failure"}],
    }

    with pytest.raises(ValidationError, match="atomic write failed"):
        writeback([draft], run_dir, paths, ("notes", "_archive", "_queues"))

    assert target.read_text(encoding="utf-8") == original
    assert not list(target.parent.glob(".existing.md.*.tmp"))
    failed_report = _read_jsonl(run_dir / "s5" / "write-report.jsonl")
    assert len(failed_report) == 1
    assert failed_report[0]["draft_id"] == "draft-failure"
    assert failed_report[0]["target_path"] == "notes/existing.md"
    assert failed_report[0]["action"] == "revise"
    assert failed_report[0]["status"] == "failed"


def test_non_dry_run_report_matches_s5_formal_changes(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (new_dir / "items" / "release.md").write_text(
        "# Release\nDigest pages preserve provenance.\n", encoding="utf-8"
    )
    declare_sources(new_dir, "release.md")

    result = run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 0, result.stderr
    run_dir = _single_run_dir(kb_dir)
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    writes = _read_jsonl(run_dir / "s5" / "write-report.jsonl")
    assert report["dry_run"] is False
    assert report["formal_kb_changes"] == [
        {key: row[key] for key in ("target_path", "action", "status", "archive_path")}
        for row in writes
    ]


def test_s2_low_confidence_clusters_are_written_to_review_queues(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    items = new_dir / "items"
    (items / "low-a.md").write_text("alpha beta gamma delta\n", encoding="utf-8")
    (items / "low-b.md").write_text("alpha beta gamma epsilon\n", encoding="utf-8")
    declare_sources(new_dir, "low-a.md", "low-b.md")

    result = run_digest(
        str(new_dir),
        str(kb_dir),
        "--cluster-auto-threshold",
        "0.90",
        "--cluster-review-threshold",
        "0.50",
    )

    assert result.returncode == 0, result.stderr
    clusters = _read_jsonl(_single_run_dir(kb_dir) / "s2" / "clusters.jsonl")
    review = next(cluster for cluster in clusters if cluster["tier"] == "needs_review")
    queue = (kb_dir / "_queues" / "needs_review.md").read_text(encoding="utf-8")
    assert review["cluster_id"] in queue
    assert review["decision_reason"] in queue


def test_s3_covers_new_revise_merge_multiple_and_respects_top_k(tmp_path: Path) -> None:
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.paths import DigestPaths
    from knowledge_digest.retrieve import retrieve

    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    pages = kb_dir / "pages"
    pages.mkdir()
    (pages / "alpha.md").write_text("alpha beta common\n", encoding="utf-8")
    (pages / "beta.md").write_text("beta gamma common\n", encoding="utf-8")
    raw_items = [
        {"raw_id": "raw-new", "text": "zeta eta theta", "source_uri": "source:new"},
        {"raw_id": "raw-revise", "text": "alpha", "source_uri": "source:revise"},
        {"raw_id": "raw-merge", "text": "alpha beta gamma common", "source_uri": "source:merge"},
    ]
    clusters = [
        {"cluster_id": f"cluster-{index}", "tier": "auto", "members": [item["raw_id"]]}
        for index, item in enumerate(raw_items, start=1)
    ]
    paths = DigestPaths(
        new_dir=new_dir,
        items_dir=new_dir / "items",
        kb_dir=kb_dir,
        structure_path=kb_dir / "kb.structure.md",
    )
    run_dir = kb_dir / "_digest" / "runs" / "s3-actions"

    decisions = retrieve(
        clusters,
        raw_items,
        run_dir,
        paths,
        ("pages", "_archive", "_queues"),
        DigestSettings(top_k=2),
    )

    assert {decision["action"] for decision in decisions} == {"new", "revise", "merge_multiple"}
    assert all(len(decision["candidate_paths"]) <= 2 for decision in decisions)
    assert all(len(decision["candidate_paths"]) == len(decision["candidate_scores"]) for decision in decisions)


def test_s4_unsupported_claims_are_reported_but_never_written_to_page(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (new_dir / "items" / "claims.md").write_text(
        "# Claims\nSupported statement.\nUnsupported: invented statement.\n",
        encoding="utf-8",
    )
    declare_sources(new_dir, "claims.md")

    result = run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 0, result.stderr
    run_dir = _single_run_dir(kb_dir)
    unsupported = _read_jsonl(run_dir / "s4" / "unsupported-claims.jsonl")
    writes = _read_jsonl(run_dir / "s5" / "write-report.jsonl")
    rendered = "\n".join((kb_dir / str(write["target_path"])).read_text(encoding="utf-8") for write in writes)
    assert any("invented statement" in str(row["text"]) for row in unsupported)
    assert "invented statement" not in rendered
    assert "Supported statement" in rendered


def test_complete_run_has_six_of_six_traceable_stage_artifacts(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    source_uri = "https://source.example/trace-six"
    (new_dir / "items" / "trace.md").write_text(
        "# Trace\nTraceable claim reaches the formal page.\n", encoding="utf-8"
    )
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "trace.md", "source_uri": source_uri}) + "\n",
        encoding="utf-8",
    )

    result = run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 0, result.stderr
    run_dir = _single_run_dir(kb_dir)
    required = {
        "s1": "raw-items.jsonl",
        "s2": "clusters.jsonl",
        "s3": "evolution-decisions.jsonl",
        "s4": "drafts.jsonl",
        "s5": "write-report.jsonl",
        "s6": "provenance-audit.jsonl",
    }
    assert sum((run_dir / stage / artifact).is_file() for stage, artifact in required.items()) == 6
    audit = _read_jsonl(run_dir / "s6" / "provenance-audit.jsonl")
    assert audit and all(row["source_uri"] == source_uri for row in audit)
    assert all((kb_dir / str(row["target_path"])).is_file() for row in audit)


def test_long_document_is_kept_complete_and_emits_split_suggestion(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    lines = [f"release detail {number}" for number in range(12)]
    (new_dir / "items" / "long.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    declare_sources(new_dir, "long.md")

    result = run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "5")

    assert result.returncode == 0, result.stderr
    run_dir = _single_run_dir(kb_dir)
    drafts = _read_jsonl(run_dir / "s4" / "drafts.jsonl")
    suggestions = _read_jsonl(run_dir / "s4" / "split-suggestions.jsonl")
    assert suggestions and suggestions[0]["line_count"] == len(lines)
    assert suggestions[0]["reason"] == "max_doc_lines exceeded"
    assert all(line in str(drafts[0]["final_body"]) for line in lines)


def test_ac011_out_of_scope_integrations_are_not_created(tmp_path: Path) -> None:
    """Phase 0 remains filesystem-only: no publisher, scheduler, or remote sync artifacts."""
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (new_dir / "items" / "local.md").write_text("# Local\nLocal digest only.\n", encoding="utf-8")
    declare_sources(new_dir, "local.md")

    result = run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 0, result.stderr
    forbidden_names = {"publish.json", "remote-sync.json", "schedule.json", "notifications.json"}
    assert not any(path.name in forbidden_names for path in tmp_path.rglob("*"))
    assert "http" not in result.stdout.lower()


def test_dry_run_report_contains_stable_write_plan_snapshot(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (new_dir / "items" / "planned.md").write_text("# Planned\nPlanned digest claim.\n", encoding="utf-8")
    declare_sources(new_dir, "planned.md")

    first = run_digest(str(new_dir), str(kb_dir), "--dry-run")
    second = run_digest(str(new_dir), str(kb_dir), "--dry-run")

    assert first.returncode == second.returncode == 0
    reports = sorted((kb_dir / "_digest" / "runs").glob("*/report.json"))
    snapshots = [json.loads(path.read_text(encoding="utf-8"))["write_plan_snapshot"] for path in reports]
    assert len(snapshots) == 2
    assert snapshots[0] == snapshots[1]
    assert snapshots[0]["formal_kb_changes"]
    assert not (kb_dir / "notes").exists()


def test_revise_write_archives_exact_before_snapshot_with_reason(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    page = kb_dir / "notes" / "existing.md"
    page.parent.mkdir()
    original = "# Existing\n\nalpha beta existing behavior\n"
    page.write_text(original, encoding="utf-8")
    (new_dir / "items" / "revision.md").write_text(
        "# Revision\nalpha beta existing behavior now includes gamma.\n", encoding="utf-8"
    )
    declare_sources(new_dir, "revision.md")

    result = run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 0, result.stderr
    writes = _read_jsonl(_single_run_dir(kb_dir) / "s5" / "write-report.jsonl")
    revised = next(row for row in writes if row["archive_path"])
    archive = kb_dir / str(revised["archive_path"])
    assert archive.read_text(encoding="utf-8") == original
    assert revised["archive_reason"] == "pre-write snapshot"
    assert revised["archive_snapshot_sha256"]


def test_rerun_is_idempotent_for_pages_and_queue_entries(tmp_path: Path) -> None:
    new_dir, kb_dir = copy_fixture_layout(tmp_path)
    (new_dir / "items" / "stable.md").write_text(
        "# Stable\nStable alpha beta digest claim.\n", encoding="utf-8"
    )
    declare_sources(new_dir, "stable.md")

    first = run_digest(str(new_dir), str(kb_dir))
    assert first.returncode == 0, first.stderr
    page_snapshot = {
        path.relative_to(kb_dir): path.read_text(encoding="utf-8")
        for path in (kb_dir / "notes").rglob("*.md")
    }
    queue_snapshot = {
        path.relative_to(kb_dir): path.read_text(encoding="utf-8")
        for path in (kb_dir / "_queues").glob("*.md")
    }

    second = run_digest(str(new_dir), str(kb_dir))

    assert second.returncode == 0, second.stderr
    assert {
        path.relative_to(kb_dir): path.read_text(encoding="utf-8")
        for path in (kb_dir / "notes").rglob("*.md")
    } == page_snapshot
    assert {
        path.relative_to(kb_dir): path.read_text(encoding="utf-8")
        for path in (kb_dir / "_queues").glob("*.md")
    } == queue_snapshot
