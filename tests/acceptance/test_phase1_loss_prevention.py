"""Phase 1 acceptance: local snapshots, lineage, retention, and lossless splits."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


_PUBLICATION_DECLARATION = [
    "publication_home: Home.md",
    "publication_index_root: indexes",
    "publication_categories:",
    "  - id: pending",
    "    title: 待归类",
    "    topic_dir: pages/待归类",
]


def run_digest(*args: str) -> subprocess.CompletedProcess[str]:
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


def make_case(tmp_path: Path, *, why: str | None = "why", version: str | None = "version") -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    fields = [
        "contract_version: phase1",
        "roots: [pages, _archive, _queues]",
        *_PUBLICATION_DECLARATION,
    ]
    if why is not None:
        fields.append(f"why_field: {why}")
    if version is not None:
        fields.append(f"version_field: {version}")
    (kb_dir / "kb.structure.md").write_text("---\n" + "\n".join(fields) + "\n---\n", encoding="utf-8")
    return new_dir, kb_dir


def write_source(new_dir: Path, name: str, text: str, uri: str, **meta: object) -> None:
    (new_dir / "items" / name).write_text(text, encoding="utf-8")
    source = {"content_path": name, "source_uri": uri, "captured_at": "2026-07-22T00:00:00Z", **meta}
    (new_dir / "sources.jsonl").write_text(json.dumps(source) + "\n", encoding="utf-8")


def jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def latest_run(kb_dir: Path) -> Path:
    return sorted((kb_dir / "_digest" / "runs").iterdir())[-1]


def test_ac01_local_snapshot_contract_is_complete(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "A high density claim.\nSee https://docs.example/a\n", "https://source.example/good")
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 0, result.stderr
    snapshot = jsonl(latest_run(kb_dir) / "s1" / "source-snapshots.jsonl")[0]
    assert {"source_uri", "captured_at", "validated_at", "content_fingerprint", "validation_status", "validation_reason", "input_path", "full_content"} <= snapshot.keys()
    assert snapshot["validation_status"] == "passed"


def test_ac01_failed_snapshot_has_a_stable_id(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    (new_dir / "items" / "broken.md").write_bytes(b"\xff")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "broken.md", "source_uri": "https://source.example/broken"}) + "\n",
        encoding="utf-8",
    )

    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    first_run = latest_run(kb_dir)
    first_snapshot = jsonl(first_run / "s1" / "source-snapshots.jsonl")[0]
    assert first_snapshot["validation_status"] == "failed"
    assert str(first_snapshot["snapshot_id"]).startswith("snapshot-")

    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    second_snapshot = jsonl(latest_run(kb_dir) / "s1" / "source-snapshots.jsonl")[0]
    assert second_snapshot["snapshot_id"] == first_snapshot["snapshot_id"]


def test_ac02_missing_source_uri_is_failed_without_synthetic_file_uri(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    (new_dir / "items" / "missing-uri.md").write_text("A claim without a declared source.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "missing-uri.md"}) + "\n",
        encoding="utf-8",
    )

    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    run = latest_run(kb_dir)
    snapshot = jsonl(run / "s1" / "source-snapshots.jsonl")[0]
    assert snapshot["source_uri"] == ""
    assert snapshot["validation_status"] == "failed"
    assert not jsonl(run / "s6" / "source-index.jsonl")
    assert not list((kb_dir / "pages").rglob("*.md"))


def test_ac02_missing_source_manifest_does_not_synthesize_file_uri(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    (new_dir / "items" / "unmapped.md").write_text("No manifest source.", encoding="utf-8")

    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode != 0
    assert "missing declarations" in result.stdout
    assert not (kb_dir / "pages").exists()


def test_ac02_failed_and_shell_sources_are_not_formal_sources(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    (new_dir / "items" / "good.md").write_text("Useful supported claim.\n", encoding="utf-8")
    (new_dir / "items" / "shell.md").write_text("Home | Navigation | Login\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {"content_path": "good.md", "source_uri": "https://source.example/good"},
                {"content_path": "shell.md", "source_uri": "https://source.example/shell", "source_status": "failed"},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 0, result.stderr
    indexed = jsonl(latest_run(kb_dir) / "s6" / "source-index.jsonl")
    assert [row["source_uri"] for row in indexed] == ["https://source.example/good"]
    assert "https://source.example/shell" not in (kb_dir / "indexes" / "sources.md").read_text(encoding="utf-8")


def _replay_fragment(source_text: str, locator: object) -> str:
    """Return the exact source slice named by a ``lines:start-end`` locator."""
    text = str(locator)
    assert text.startswith("lines:"), f"expected lines: locator, got {locator!r}"
    start_s, end_s = text.split(":", 1)[1].split("-", 1)
    start, end = int(start_s), int(end_s)
    lines = source_text.splitlines()
    assert 1 <= start <= end <= len(lines), f"locator {locator!r} out of range for {len(lines)} lines"
    return "\n".join(lines[start - 1 : end])


def test_ac03_every_final_claim_has_replayable_lineage(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "A supported claim.\nA second claim.\n", "https://source.example/good")
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 0, result.stderr
    run = latest_run(kb_dir)
    claims = jsonl(run / "s6" / "provenance-audit.jsonl")
    assert claims
    snapshots = {
        str(row["source_uri"]): str(row["full_content"])
        for row in jsonl(run / "s1" / "source-snapshots.jsonl")
        if row.get("full_content") is not None
    }
    for claim in claims:
        assert {"claim_fingerprint", "source_uri", "content_fingerprint", "fragment_locator", "verification_status", "claim_body"} <= claim.keys()
        assert claim["verification_status"] == "verified"
        assert str(claim["fragment_locator"]).startswith("lines:")
        # "Replayable" means the locator actually recovers claim_body from the
        # captured source — a prefix check alone never exercises the lineage.
        replayed = _replay_fragment(snapshots[str(claim["source_uri"])], claim["fragment_locator"])
        assert replayed == str(claim["claim_body"])


def test_ac04_content_change_creates_bidirectional_version_relation(tmp_path: Path) -> None:
    from knowledge_digest.pipeline import fold_claim_history

    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "Original versioned claim.\n", "https://source.example/versioned")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    write_source(new_dir, "good.md", "Revised versioned claim.\n", "https://source.example/versioned")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    # claim-history.jsonl is append-only: the superseded claim's later state is a
    # separate line, so the bidirectional relation is read through the fold.
    history = fold_claim_history(jsonl(kb_dir / "_digest" / "claim-history.jsonl"))
    old = next(row for row in history if row["text"] == "Original versioned claim.")
    new = next(row for row in history if row["text"] == "Revised versioned claim.")
    assert new["supersedes"] == old["claim_fingerprint"]
    assert old["superseded_by"] == new["claim_fingerprint"]
    assert old["verification_status"] == "superseded"


def test_ac05_later_validation_failure_keeps_claim_pending(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "Keep this claim.\n", "https://source.example/retry")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    page_before = next((kb_dir / "pages").rglob("*.md")).read_text(encoding="utf-8")
    write_source(new_dir, "good.md", "Keep this claim.\n", "https://source.example/retry", source_status="failed")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    assert next((kb_dir / "pages").rglob("*.md")).read_text(encoding="utf-8") == page_before
    pending = jsonl(kb_dir / "_digest" / "pending-review.jsonl")
    assert pending and pending[0]["verification_status"] == "pending_review"
    assert pending[0]["retry_status"] == "retry_next_manual_run"


def test_ac06_replace_archive_contains_content_reason_and_lineage(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "Before archive replacement.\n", "https://source.example/archive")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    write_source(new_dir, "good.md", "After archive replacement.\n", "https://source.example/archive")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    records = jsonl(kb_dir / "_archive" / "records.jsonl")
    record = records[0]
    assert {"operation", "operation_at", "reason", "page_path", "source_uri", "full_content", "snapshot_content", "retain_content_until", "lineage"} <= record.keys()
    assert record["full_content"] and record["reason"]


def test_ac08_unexpired_archive_is_recoverable(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "Recoverable old body content.\n", "https://source.example/recover")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    write_source(new_dir, "good.md", "Replacement body content.\n", "https://source.example/recover")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    record = jsonl(kb_dir / "_archive" / "records.jsonl")[0]
    assert "Recoverable old body content." in str(record["full_content"])
    assert record["content_retained"] is True


@pytest.mark.parametrize("missing", ["why", "version"])
def test_ac09_ac10_missing_structure_declaration_is_fail_closed(tmp_path: Path, missing: str) -> None:
    new_dir, kb_dir = make_case(tmp_path, why=None if missing == "why" else "why", version=None if missing == "version" else "version")
    write_source(new_dir, "good.md", "Must not be written.\n", "https://source.example/blocked")
    before = set(kb_dir.rglob("*.md"))
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 1
    assert "no formal knowledge-base files written" in result.stdout
    assert set(kb_dir.rglob("*.md")) == before
    report = json.loads((latest_run(kb_dir) / "report.json").read_text(encoding="utf-8"))
    assert report["official_write"]["status"] == "blocked_structure"
    assert any(missing in str(value).lower() for value in report["structure_check"]["missing_fields"])


def test_ac09_ac10_both_structure_declarations_missing_is_fail_closed(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path, why=None, version=None)
    write_source(new_dir, "good.md", "Must not be written.", "https://source.example/blocked-both")
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 1
    report = json.loads((latest_run(kb_dir) / "report.json").read_text(encoding="utf-8"))
    assert report["official_write"]["status"] == "blocked_structure"
    assert report["structure_check"]["allow_official_write"] is False
    assert set(report["structure_check"]["missing_fields"]) == {"Why", "version history"}


@pytest.mark.parametrize(
    "structure",
    [
        "---\ncontract_version: phase1\nroots:\n  - pages\n  - _archive\n  - _queues\n"
        + "\n".join(_PUBLICATION_DECLARATION)
        + "\n---\n",
        "---\ncontract_version: phase1\npage_root: pages\narchive_root: _archive\nqueue_root: _queues\n"
        + "\n".join(_PUBLICATION_DECLARATION)
        + "\n---\n",
    ],
)
def test_ac09_ac10_phase0_root_layout_remains_fail_closed(tmp_path: Path, structure: str) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    (kb_dir / "kb.structure.md").write_text(structure, encoding="utf-8")
    write_source(new_dir, "legacy.md", "Must remain blocked.\n", "https://source.example/legacy-gate")
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 1
    report = json.loads((latest_run(kb_dir) / "report.json").read_text(encoding="utf-8"))
    assert report["structure_check"]["allow_official_write"] is False
    assert report["official_write"]["status"] == "blocked_structure"
    assert not list((kb_dir / "pages").rglob("*.md"))
    assert set(report["structure_check"]["missing_fields"]) == {"Why", "version history"}


def test_ac11_complete_structure_allows_official_write(tmp_path: Path) -> None:
    from knowledge_digest.kb_structure import inspect_structure, parse_structure_contract, structure_contract

    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "Allowed structure claim.\n", "https://source.example/allowed")
    assert parse_structure_contract(kb_dir / "kb.structure.md") == inspect_structure(kb_dir / "kb.structure.md")
    assert structure_contract(kb_dir / "kb.structure.md") == inspect_structure(kb_dir / "kb.structure.md")
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 0, result.stderr
    report = json.loads((latest_run(kb_dir) / "report.json").read_text(encoding="utf-8"))
    assert report["structure_check"]["allow_official_write"] is True
    assert list((kb_dir / "pages").rglob("*.md"))


def test_ac12_long_document_is_reorganized_without_loss(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    lines = [f"Long source line {index}." for index in range(12)]
    write_source(new_dir, "long.md", "\n".join(lines) + "\n", "https://source.example/long")
    result = run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "3")
    assert result.returncode == 0, result.stderr
    run = latest_run(kb_dir)
    suggestion = jsonl(run / "s4" / "split-suggestions.jsonl")[0]
    assert suggestion["not_truncated"] is True and suggestion["coverage_complete"] is True
    rendered = "\n".join(
        path.read_text(encoding="utf-8").split("\n\n## Provenance", 1)[0]
        for path in (kb_dir / "pages").rglob("*.md")
    )
    assert all(line in rendered for line in lines)
    coverage = jsonl(run / "s4" / "coverage-mapping.jsonl")
    assert len(coverage) == len(lines)
    assert all(row["output_fragment_locator"].startswith("lines:") for row in coverage)
    component_coverage = jsonl(run / "s4" / "component-coverage.jsonl")
    assert component_coverage and all(row["coverage_kind"] == "component" for row in component_coverage)
    assert all(row["output_fragment_locator"].startswith("lines:") for row in component_coverage)
    expected_pages = {
        claim["fragment_locator"]: page["target_path"]
        for draft in jsonl(run / "s4" / "drafts.jsonl")
        for page in draft["split_pages"]
        for claim in page["claims"]
    }
    actual_pages = {
        claim["fragment_locator"]: claim["target_path"]
        for claim in jsonl(run / "s6" / "provenance-audit.jsonl")
    }
    assert actual_pages == expected_pages


def test_ac13_atomic_components_share_an_output_page(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    text = "FAQ: What happens?\nThe complete answer stays with the question.\nError E17: invalid input\nError explanation stays adjacent.\nParameter timeout: seconds\nParameter explanation.\nBefore code.\n```python\nprint('ok')\n```\nAfter code.\n"
    write_source(new_dir, "components.md", text, "https://source.example/components")
    assert run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "3").returncode == 0
    suggestions = jsonl(latest_run(kb_dir) / "s4" / "split-suggestions.jsonl")[0]
    by_kind: dict[str, set[str]] = {}
    for page in suggestions["pages"]:
        for component in page["components"]:
            by_kind.setdefault(str(component["kind"]), set()).add(str(page["target_path"]))
    assert len(by_kind["faq"]) == 1
    assert len(by_kind["error_code"]) == 1
    assert len(by_kind["parameter"]) == 1
    assert len(by_kind["code"]) == 1


def test_ac13_multipart_atomic_components_and_code_explanation_are_lossless(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    text = (
        "FAQ: Multi-paragraph question?\n"
        "First answer paragraph.\n\n"
        "Second answer paragraph.\n"
        "Before code.\n"
        "```python\n"
        "print('ok')\n"
        "```\n"
        "After code.\n"
    )
    write_source(new_dir, "components.md", text, "https://source.example/components-lossless")
    assert run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "3").returncode == 0
    rendered = "\n".join(
        path.read_text(encoding="utf-8").split("\n\n## Provenance", 1)[0]
        for path in (kb_dir / "pages").rglob("*.md")
    )
    for line in ("First answer paragraph.", "Second answer paragraph.", "Before code.", "print('ok')", "After code."):
        assert rendered.count(line) == 1


def test_ac13_code_block_keeps_preceding_explanation_atomic(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    text = (
        "FAQ: How is this run?\n"
        "The answer is traceable.\n"
        "Before code.\n"
        "```python\n"
        "print('ok')\n"
        "```\n"
        "After code.\n"
    )
    write_source(new_dir, "code-context.md", text, "https://source.example/code-context")

    result = run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "3")
    assert result.returncode == 0, result.stderr
    suggestion = jsonl(latest_run(kb_dir) / "s4" / "split-suggestions.jsonl")[0]
    code_components = [
        component
        for page in suggestion["pages"]
        for component in page["components"]
        if component["kind"] == "code"
    ]
    assert len(code_components) == 1
    assert code_components[0]["input_locator"].startswith("lines:3-")


def test_ac13_heading_block_stays_contiguous_until_next_heading(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    text = "# Section\nfirst section line\nsecond section line\nthird section line\n# Next\nnext section line\n"
    write_source(new_dir, "headings.md", text, "https://source.example/headings")

    assert run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "2").returncode == 0
    section_lines = ["# Section", "first section line", "second section line", "third section line"]
    pages = [path.read_text(encoding="utf-8") for path in (kb_dir / "pages").rglob("*.md")]
    containing = [page for page in pages if "# Section" in page]
    assert len(containing) == 1
    assert all(line in containing[0] for line in section_lines)


def test_ac13_heading_sections_split_at_nested_headings(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    text = (
        "# Guide\nintro line\n"
        "## First\nfirst line one\nfirst line two\n"
        "## Second\nsecond line one\nsecond line two\n"
    )
    write_source(new_dir, "nested-headings.md", text, "https://source.example/nested-headings")

    assert run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "3").returncode == 0
    suggestion = jsonl(latest_run(kb_dir) / "s4" / "split-suggestions.jsonl")[0]
    assert all(not page["unsplittable_components"] for page in suggestion["pages"])
    pages = [path.read_text(encoding="utf-8") for path in (kb_dir / "pages").rglob("*.md")]
    assert any("# Guide" in page and "intro line" in page for page in pages)
    assert any("## First" in page and "first line two" in page for page in pages)
    assert any("## Second" in page and "second line two" in page for page in pages)


def test_ac14_oversized_atomic_component_is_visible_and_complete(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    answer = "FAQ: Large question?\n" + "\n".join(f"answer line {i}" for i in range(6)) + "\n"
    write_source(new_dir, "faq.md", answer, "https://source.example/faq")
    assert run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "2").returncode == 0
    suggestion = jsonl(latest_run(kb_dir) / "s4" / "split-suggestions.jsonl")[0]
    assert suggestion["not_truncated"] is True
    assert suggestion["pages"][0]["unsplittable_components"]
    assert all(line in next((kb_dir / "pages").rglob("*.md")).read_text(encoding="utf-8") for line in answer.splitlines())


def test_ac15_structure_failure_leaves_existing_formal_page_untouched(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "Existing atomic claim.\n", "https://source.example/atomic")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    page = next((kb_dir / "pages").rglob("*.md"))
    before = page.read_text(encoding="utf-8")
    snapshots_path = kb_dir / "_digest" / "source-snapshots.jsonl"
    snapshots_before = snapshots_path.read_text(encoding="utf-8")
    (kb_dir / "kb.structure.md").write_text(
        "---\ncontract_version: phase1\nroots: [pages, _archive, _queues]\nwhy_field: why\n"
        + "\n".join(_PUBLICATION_DECLARATION)
        + "\n---\n",
        encoding="utf-8",
    )
    write_source(new_dir, "good.md", "Would be blocked.\n", "https://source.example/atomic")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 1
    assert page.read_text(encoding="utf-8") == before
    assert snapshots_path.read_text(encoding="utf-8") == snapshots_before


def test_ac06_multi_source_page_archive_keeps_all_snapshot_refs(tmp_path: Path) -> None:
    from knowledge_digest.paths import DigestPaths
    from knowledge_digest.writeback import writeback

    new_dir, kb_dir = make_case(tmp_path)
    paths = DigestPaths(new_dir, new_dir / "items", kb_dir, kb_dir / "kb.structure.md")
    run_one = kb_dir / "_digest" / "runs" / "first"
    run_two = kb_dir / "_digest" / "runs" / "second"
    claim_a = {
        "text": "Source A claim",
        "source_uri": "https://source.example/a",
        "source_snapshot_ref": "snapshot-a",
        "content_fingerprint": "content-a",
        "fragment_locator": "lines:1-1",
        "claim_fingerprint": "claim-a",
    }
    claim_b = {
        "text": "Source B claim",
        "source_uri": "https://source.example/b",
        "source_snapshot_ref": "snapshot-b",
        "content_fingerprint": "content-b",
        "fragment_locator": "lines:1-1",
        "claim_fingerprint": "claim-b",
    }
    draft = {
        "draft_id": "mixed",
        "action": "new",
        "target_paths": ["pages/mixed.md"],
        "final_body": "Source A claim\nSource B claim",
        "claims": [claim_a, claim_b],
    }
    writeback([draft], run_one, paths, ("pages", "_archive", "_queues"))

    replacement = dict(draft, final_body="Replacement", action="revise")
    writeback([replacement], run_two, paths, ("pages", "_archive", "_queues"))
    record = jsonl(kb_dir / "_archive" / "records.jsonl")[0]
    assert isinstance(record["source_snapshot"], list)
    assert {row["source_snapshot_ref"] for row in record["source_snapshot"]} == {"snapshot-a", "snapshot-b"}
    assert record["source_uri"] == ["https://source.example/a", "https://source.example/b"]


def test_ac06_failed_batch_archives_originals_before_overwriting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A half-written batch must leave every original recoverable from _archive/."""
    from knowledge_digest.paths import DigestPaths
    from knowledge_digest.writeback import writeback
    import knowledge_digest.writeback as writeback_module

    new_dir, kb_dir = make_case(tmp_path)
    paths = DigestPaths(new_dir, new_dir / "items", kb_dir, kb_dir / "kb.structure.md")
    first = kb_dir / "pages" / "first.md"
    second = kb_dir / "pages" / "second.md"
    first.parent.mkdir(parents=True)
    first.write_text("old first", encoding="utf-8")
    second.write_text("old second", encoding="utf-8")
    run_dir = kb_dir / "_digest" / "runs" / "archive-rollback"
    claim = {
        "text": "replacement",
        "source_uri": "https://source.example/rollback",
        "source_snapshot_ref": "snapshot-rollback",
        "content_fingerprint": "content-rollback",
        "fragment_locator": "lines:1-1",
        "claim_fingerprint": "claim-rollback",
    }
    draft = {
        "draft_id": "rollback",
        "action": "revise",
        "split_pages": [
            {"page_index": 1, "target_path": "pages/first.md", "final_body": "new first", "claims": [claim]},
            {"page_index": 2, "target_path": "pages/second.md", "final_body": "new second", "claims": [claim]},
        ],
    }
    real_atomic_write = writeback_module._atomic_write
    write_calls: list[Path] = []

    def fail_second(path: Path, content: str) -> None:
        write_calls.append(path)
        if path == second and content.startswith("new second"):
            raise ValidationError("s5", path, "simulated batch failure")
        real_atomic_write(path, content)

    from knowledge_digest.errors import ValidationError

    monkeypatch.setattr(writeback_module, "_atomic_write", fail_second)
    with pytest.raises(ValidationError, match="simulated batch failure"):
        writeback([draft], run_dir, paths, ("pages", "_archive", "_queues"))

    assert write_calls, "_atomic_write was never called; stub was not exercised"
    assert second in write_calls

    # No rollback: the interrupted batch may leave a half-written knowledge base.
    # The loss-prevention guarantee is that both originals were durably archived
    # before any target page was touched, so both remain recoverable.
    archive_root = kb_dir / "_archive" / "archive-rollback" / "pages"
    assert (archive_root / "first.md").read_text(encoding="utf-8") == "old first"
    assert (archive_root / "second.md").read_text(encoding="utf-8") == "old second"
    assert second.read_text(encoding="utf-8") == "old second"

    # Rerun recovers: restore from archive, then a clean writeback lands both pages.
    first.write_text((archive_root / "first.md").read_text(encoding="utf-8"), encoding="utf-8")
    second.write_text((archive_root / "second.md").read_text(encoding="utf-8"), encoding="utf-8")
    assert first.read_text(encoding="utf-8") == "old first"
    monkeypatch.setattr(writeback_module, "_atomic_write", real_atomic_write)
    retry_dir = kb_dir / "_digest" / "runs" / "archive-rollback-retry"
    writeback([draft], retry_dir, paths, ("pages", "_archive", "_queues"))
    assert first.read_text(encoding="utf-8").startswith("new first")
    assert second.read_text(encoding="utf-8").startswith("new second")


def test_ac16_mixed_acceptance_run_has_all_canonical_evidence(tmp_path: Path) -> None:
    new_dir, kb_dir = make_case(tmp_path)
    (new_dir / "items" / "mixed.md").write_text(
        "# Mixed\nFAQ: Why?\nBecause it is traceable.\nError E42: invalid.\nParameter limit: 10\nSee https://docs.example/mixed\n"
        + "\n".join(f"detail {i}" for i in range(8))
        + "\n",
        encoding="utf-8",
    )
    (new_dir / "items" / "failed.md").write_text("Home | Navigation | Login\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {"content_path": "mixed.md", "source_uri": "https://source.example/mixed"},
                {"content_path": "failed.md", "source_uri": "https://source.example/failed", "source_status": "failed"},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_digest(str(new_dir), str(kb_dir), "--max-doc-lines", "4")
    assert result.returncode == 0, result.stderr
    run = latest_run(kb_dir)
    for stage, artifact in (("s1", "source-snapshots.jsonl"), ("s2", "clusters.jsonl"), ("s3", "evolution-decisions.jsonl"), ("s4", "drafts.jsonl"), ("s5", "write-report.jsonl"), ("s6", "provenance-audit.jsonl")):
        assert (run / stage / artifact).is_file()
    report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    assert report["source_filter"]["rejected_source_uris"] == ["https://source.example/failed"]
    assert report["official_write"]["status"] == "written"
