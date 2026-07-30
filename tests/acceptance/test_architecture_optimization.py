"""Acceptance tests for the stable identity, final layout and batch seams."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_digest.batch_run import run_batched
from knowledge_digest.config import DigestSettings
from knowledge_digest.errors import ValidationError
from knowledge_digest.kb_structure import parse_roots
from knowledge_digest.paths import validate_paths
from knowledge_digest.pipeline import audit_run


def _case(tmp_path: Path, name: str = "case") -> tuple[Path, Path]:
    new_dir = tmp_path / name / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / name / "kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(
        "---\nroots: [pages, _archive, _queues]\nwhy_field: why\nversion_field: version\n---\n",
        encoding="utf-8",
    )
    return new_dir, kb_dir


def _sources(new_dir: Path, rows: list[tuple[str, str, str]]) -> None:
    (new_dir / "sources.jsonl").write_text(
        "\n".join(json.dumps({"content_path": path, "source_uri": uri}) for path, uri, _text in rows) + "\n",
        encoding="utf-8",
    )
    for path, _uri, text in rows:
        target = new_dir / "items" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def _run(new_dir: Path, kb_dir: Path) -> Path:
    paths = validate_paths(new_dir, kb_dir)
    report, _summary = audit_run(paths, DigestSettings(), parse_roots(paths.structure_path), dry_run=False)
    return report


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _topic_paths(kb_dir: Path) -> set[str]:
    return {
        path.relative_to(kb_dir).as_posix()
        for path in (kb_dir / "pages" / "digest").glob("topic-*.md")
    }


def test_topic_identity_and_paths_ignore_source_enumeration_order(tmp_path: Path) -> None:
    first_new, first_kb = _case(tmp_path, "first")
    second_new, second_kb = _case(tmp_path, "second")
    _sources(
        first_new,
        [
            ("z.md", "https://source.example/a", "# Alpha\nAlpha evidence.\n"),
            ("a.md", "https://source.example/b", "# Beta\nBeta evidence.\n"),
        ],
    )
    _sources(
        second_new,
        [
            ("a.md", "https://source.example/a", "# Alpha\nAlpha evidence.\n"),
            ("z.md", "https://source.example/b", "# Beta\nBeta evidence.\n"),
        ],
    )

    _run(first_new, first_kb)
    _run(second_new, second_kb)

    assert _topic_paths(first_kb) == _topic_paths(second_kb)


def test_final_layout_enforces_300_lines_and_keeps_each_claim_once(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    evidence = "\n".join(f"Evidence line {index}." for index in range(360)) + "\n"
    _sources(new_dir, [("long.md", "https://source.example/long", "# Long\n" + evidence)])

    report = _run(new_dir, kb_dir)
    run_dir = report.parent
    pages = sorted((kb_dir / "pages" / "digest").glob("*.md"))
    audit = _jsonl(run_dir / "s6" / "provenance-audit.jsonl")

    assert len(pages) > 1
    assert all(len(page.read_text(encoding="utf-8").splitlines()) <= 300 for page in pages)
    assert len(audit) == 360
    assert len({(row["claim_fingerprint"], row["fragment_locator"]) for row in audit}) == 360
    assert all("## Summary" in page.read_text(encoding="utf-8") and "## Evidence" in page.read_text(encoding="utf-8") and "## Provenance" in page.read_text(encoding="utf-8") for page in pages)


def test_repeated_identical_lines_keep_distinct_claim_locations(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _sources(
        new_dir,
        [("repeat.md", "https://source.example/repeat", "Repeated source claim.\nRepeated source claim.\n")],
    )

    report = _run(new_dir, kb_dir)
    audit = _jsonl(report.parent / "s6" / "provenance-audit.jsonl")
    coverage = _jsonl(report.parent / "s4" / "coverage-mapping.jsonl")

    assert len(audit) == 2
    assert {row["fragment_locator"] for row in audit} == {"lines:1-1", "lines:2-2"}
    assert len({row["output_fragment_locator"] for row in coverage}) == 2


def test_conflicting_content_for_the_same_source_uri_fails_before_write(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _sources(
        new_dir,
        [
            ("first.md", "https://source.example/shared", "First source version.\n"),
            ("second.md", "https://source.example/shared", "Conflicting source version.\n"),
        ],
    )

    with pytest.raises(ValidationError, match="same source_uri declares conflicting content"):
        _run(new_dir, kb_dir)

    assert not (kb_dir / "pages").exists()


def test_content_revision_replaces_current_evidence_but_keeps_history(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    uri = "https://source.example/revision"
    _sources(
        new_dir,
        [("revision.md", uri, "# Old source heading\nStable current evidence.\nStable current evidence.\n")],
    )
    _run(new_dir, kb_dir)

    _sources(
        new_dir,
        [("revision.md", uri, "# New source heading\nStable current evidence.\nUpdated current evidence.\n")],
    )
    _run(new_dir, kb_dir)
    rendered = "\n".join(page.read_text(encoding="utf-8") for page in (kb_dir / "pages" / "digest").glob("*.md"))
    history = _jsonl(kb_dir / "_digest" / "claim-history.jsonl")

    assert "Updated current evidence." in rendered
    assert rendered.count("Stable current evidence.") == 1
    assert "# New source heading" in rendered
    assert "# Old source heading" not in rendered
    assert any(row.get("verification_status") == "superseded" for row in history)


def test_multi_part_write_failure_restores_previously_written_parts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from knowledge_digest import writeback as writeback_module
    from knowledge_digest.writeback import writeback

    new_dir, kb_dir = _case(tmp_path)
    first = kb_dir / "pages" / "digest" / "topic-test.md"
    second = kb_dir / "pages" / "digest" / "topic-test.part-002.md"
    first.parent.mkdir(parents=True)
    first.write_text("old first\n", encoding="utf-8")
    second.write_text("old second\n", encoding="utf-8")

    def claim(index: int) -> dict[str, str]:
        return {
            "text": f"Evidence {index}.",
            "source_uri": f"https://source.example/{index}",
            "claim_fingerprint": f"claim-{index}",
            "content_fingerprint": f"content-{index}",
            "fragment_locator": "lines:1-1",
            "raw_id": f"raw-{index}",
        }

    def page(path: Path, index: int) -> dict[str, object]:
        current = claim(index)
        return {
            "page_index": index,
            "target_path": path.relative_to(kb_dir).as_posix(),
            "final_body": current["text"],
            "rendered_content": f"## Summary\n\n## Evidence\n{current['text']}\n\n## Provenance\n- proof\n",
            "claims": [current],
            "layout_finalized": True,
        }

    original_write = writeback_module._atomic_write
    writes_to_pages = 0

    def fail_second_page(path: Path, content: str) -> None:
        nonlocal writes_to_pages
        if path in {first, second}:
            writes_to_pages += 1
            if writes_to_pages == 2:
                raise ValidationError("test", path, "forced page write failure")
        original_write(path, content)

    monkeypatch.setattr(writeback_module, "_atomic_write", fail_second_page)
    paths = validate_paths(new_dir, kb_dir)
    draft = {
        "draft_id": "layout-topic-test",
        "action": "layout",
        "layout_finalized": True,
        "split_pages": [page(first, 1), page(second, 2)],
    }
    with pytest.raises(ValidationError, match="restored prior formal pages"):
        writeback([draft], kb_dir / "_digest" / "runs" / "rollback", paths, ("pages", "_archive", "_queues"))

    assert first.read_text(encoding="utf-8") == "old first\n"
    assert second.read_text(encoding="utf-8") == "old second\n"


def test_source_index_is_link_only_and_duplicate_source_inherits_topic_link(tmp_path: Path) -> None:
    new_dir, kb_dir = _case(tmp_path)
    same = "# Shared\nShared source evidence.\n"
    _sources(
        new_dir,
        [
            ("one.md", "https://source.example/one", same),
            ("two.md", "https://source.example/two", same),
            ("empty.md", "https://source.example/empty", "Home | Navigation | Login\n"),
        ],
    )

    _run(new_dir, kb_dir)
    records = _jsonl(kb_dir / "_digest" / "source-index.jsonl")
    markdown = (kb_dir / "_digest" / "source-index.md").read_text(encoding="utf-8")

    assert [row["source_uri"] for row in records] == ["https://source.example/one", "https://source.example/two"]
    assert all(len(row["topic_paths"]) == 1 for row in records)
    assert "Shared source evidence." not in markdown
    assert "## Evidence" not in markdown and "## Provenance" not in markdown
    for row in records:
        for target in row["topic_paths"]:
            assert (kb_dir / str(target)).is_file()
            assert "../pages/digest/" in markdown


def test_batch_resume_skips_completed_batches_and_rejects_changed_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _sources(
        new_dir,
        [
            ("a.md", "https://source.example/a", "A evidence.\n"),
            ("b.md", "https://source.example/b", "B evidence.\n"),
            ("c.md", "https://source.example/c", "C evidence.\n"),
        ],
    )
    paths = validate_paths(new_dir, kb_dir)
    state_path = tmp_path / "batch-state.json"
    calls: list[tuple[str, ...]] = []

    def fake_audit(*_args: object, allowed_content_paths: set[str] | None = None, **_kwargs: object) -> tuple[Path, str]:
        call = tuple(sorted(allowed_content_paths or set()))
        calls.append(call)
        if len(calls) == 2:
            raise ValidationError("test", "batch", "forced failure")
        report = tmp_path / f"report-{len(calls)}.json"
        report.write_text("{}\n", encoding="utf-8")
        return report, "ok"

    monkeypatch.setattr("knowledge_digest.batch_run.audit_run", fake_audit)
    with pytest.raises(ValidationError, match="forced failure"):
        run_batched(paths, DigestSettings(), batch_size=1, state_path=state_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert [batch["status"] for batch in state["batches"]] == ["succeeded", "failed", "pending"]
    assert state["cluster_plan"] and state["plan_sha256"]

    monkeypatch.setattr(
        "knowledge_digest.batch_run._global_plan",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("resume must use the saved topic plan")),
    )
    report, _summary = run_batched(
        paths, DigestSettings(), batch_size=None, state_path=state_path, resume=True
    )
    assert report.is_file()
    assert calls[2:] == [(state["batches"][1]["source_paths"][0],), (state["batches"][2]["source_paths"][0],)]

    (new_dir / "items" / "a.md").write_text("A changed evidence.\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="manifest changed"):
        run_batched(paths, DigestSettings(), batch_size=None, state_path=state_path, resume=True)


def test_batch_runner_preserves_full_manifest_topics_and_global_duplicates(tmp_path: Path) -> None:
    full_new, full_kb = _case(tmp_path, "full")
    new_dir, kb_dir = _case(tmp_path, "batched")
    shared = " ".join(f"shared{index}" for index in range(20))
    rows = [
        ("one.md", "https://source.example/one", shared + " one\n"),
        ("two.md", "https://source.example/two", shared + " two\n"),
        ("duplicate.md", "https://source.example/duplicate", shared + " one\n"),
    ]
    _sources(full_new, rows)
    _sources(
        new_dir,
        rows,
    )
    full_report = _run(full_new, full_kb)
    paths = validate_paths(new_dir, kb_dir)
    state_path = tmp_path / "actual-batch-state.json"

    report, _summary = run_batched(paths, DigestSettings(), batch_size=1, state_path=state_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert report.is_file()
    assert [batch["status"] for batch in state["batches"]] == ["succeeded"] * 3
    assert _topic_paths(kb_dir) == _topic_paths(full_kb)
    assert len(_jsonl(report.parent / "s6" / "provenance-audit.jsonl")) == len(
        _jsonl(full_report.parent / "s6" / "provenance-audit.jsonl")
    )
    assert {row["source_uri"] for row in _jsonl(kb_dir / "_digest" / "source-index.jsonl")} == {
        "https://source.example/one",
        "https://source.example/two",
        "https://source.example/duplicate",
    }


def test_offline_settings_never_construct_an_llm_generator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    new_dir, kb_dir = _case(tmp_path)
    _sources(new_dir, [("one.md", "https://source.example/one", "Offline source has enough evidence.\n")])
    paths = validate_paths(new_dir, kb_dir)

    def forbidden_generator(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("LLM generator must not be constructed")

    monkeypatch.setattr("knowledge_digest.llm.generator_from_env", forbidden_generator)
    report, _summary = audit_run(
        paths,
        DigestSettings(llm_enabled=False),
        parse_roots(paths.structure_path),
        dry_run=False,
    )
    assert _jsonl(report.parent / "s6" / "provenance-audit.jsonl")
