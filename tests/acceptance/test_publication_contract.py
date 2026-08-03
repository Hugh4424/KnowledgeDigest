"""Acceptance contract for reader publication structure and safe initialization."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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


def _new_input(tmp_path: Path, *, with_source: bool) -> Path:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    if with_source:
        (items / "note.md").write_text("Published source evidence.\n", encoding="utf-8")
        (new_dir / "sources.jsonl").write_text(
            json.dumps({"content_path": "note.md", "source_uri": "https://source.example/note"}) + "\n",
            encoding="utf-8",
        )
    else:
        (new_dir / "sources.jsonl").write_text("", encoding="utf-8")
    return new_dir


def _new_titled_input(
    tmp_path: Path,
    *,
    name: str,
    text: str,
    source_uri: str = "https://source.example/note",
    metadata_title: str | None = None,
) -> Path:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    (items / name).write_text(text, encoding="utf-8")
    source = {"content_path": name, "source_uri": source_uri}
    if metadata_title is not None:
        source["title"] = metadata_title
    (new_dir / "sources.jsonl").write_text(json.dumps(source) + "\n", encoding="utf-8")
    return new_dir


def _publication_structure() -> str:
    return """---
roots: [pages, _archive, _queues]
why_field: why
version_field: version
publication_home: Home.md
publication_index_root: indexes
publication_categories:
  - id: pending
    title: 待归类
    topic_dir: pages/待归类
---
"""


def _formal_bytes(kb_dir: Path) -> dict[str, bytes]:
    return {
        path.relative_to(kb_dir).as_posix(): path.read_bytes()
        for path in kb_dir.rglob("*.md")
        if "_digest" not in path.parts and "_archive" not in path.parts and "_queues" not in path.parts
    }


def _latest_run(kb_dir: Path) -> Path:
    return max((kb_dir / "_digest" / "runs").iterdir(), key=lambda path: path.stat().st_mtime_ns)


def test_initialization_creates_default_publication_structure_inside_new_kb(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=True)
    kb_dir = tmp_path / "new-kb"

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    structure = (kb_dir / "kb.structure.md").read_text(encoding="utf-8")
    assert "publication_home: Home.md" in structure
    assert "publication_index_root: indexes" in structure
    assert structure.count("id: pending") == 1
    assert "title: 待归类" in structure
    assert "topic_dir: pages/待归类" in structure
    assert "managed_by: KnowledgeDigest" in (kb_dir / "Home.md").read_text(encoding="utf-8")
    assert "digest_kind: home" in (kb_dir / "Home.md").read_text(encoding="utf-8")
    pending = kb_dir / "indexes" / "pending.md"
    assert "managed_by: KnowledgeDigest" in pending.read_text(encoding="utf-8")
    assert "digest_kind: category" in pending.read_text(encoding="utf-8")


def test_structure_conflict_fails_before_formal_publication_changes(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=True)
    kb_dir = tmp_path / "old-kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(
        _publication_structure().replace("publication_index_root: indexes", "publication_index_root: Home.md"),
        encoding="utf-8",
    )
    (kb_dir / "handwritten.md").write_text("Do not touch.\n", encoding="utf-8")
    before = _formal_bytes(kb_dir)

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert "publication" in result.stderr.lower()
    assert _formal_bytes(kb_dir) == before


def test_structure_reports_missing_fields_and_malformed_category_together(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=True)
    kb_dir = tmp_path / "old-kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(
        "---\nroots: [pages, _archive, _queues]\nwhy_field: why\nversion_field: version\npublication_categories:\n  malformed\n---\n",
        encoding="utf-8",
    )

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert "publication_home is missing" in result.stderr
    assert "publication_index_root is missing" in result.stderr
    assert "must contain a YAML list" in result.stderr


def test_structure_rejects_nonempty_old_kb_without_declaration(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=True)
    kb_dir = tmp_path / "old-kb"
    kb_dir.mkdir()
    handwritten = kb_dir / "handwritten.md"
    handwritten.write_text("Do not touch.\n", encoding="utf-8")
    before = handwritten.read_bytes()

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert "kb.structure.md" in result.stderr
    assert handwritten.read_bytes() == before
    assert not (kb_dir / "Home.md").exists()


def test_structure_rejects_empty_legacy_kb_without_publication_declaration(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=False)
    kb_dir = tmp_path / "legacy-empty-kb"
    kb_dir.mkdir()
    structure_path = kb_dir / "kb.structure.md"
    structure_path.write_text(
        "---\nroots: [pages, _archive, _queues]\nwhy_field: why\nversion_field: version\n---\n",
        encoding="utf-8",
    )
    before = structure_path.read_bytes()

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert "publication_home is missing" in result.stderr
    assert structure_path.read_bytes() == before
    assert not (kb_dir / "Home.md").exists()


def test_structure_does_not_backfill_when_any_old_kb_file_exists(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=False)
    kb_dir = tmp_path / "legacy-old-kb"
    kb_dir.mkdir()
    structure = kb_dir / "kb.structure.md"
    structure.write_text(
        "---\nroots: [pages, _archive, _queues]\nwhy_field: why\nversion_field: version\n---\n",
        encoding="utf-8",
    )
    handwritten = kb_dir / "handwritten.md"
    handwritten.write_text("Do not touch.\n", encoding="utf-8")
    before = {"structure": structure.read_bytes(), "handwritten": handwritten.read_bytes()}

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert structure.read_bytes() == before["structure"]
    assert handwritten.read_bytes() == before["handwritten"]
    assert not (kb_dir / "Home.md").exists()


def test_empty_input_keeps_existing_formal_reader_files_byte_identical(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=False)
    kb_dir = tmp_path / "old-kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(_publication_structure(), encoding="utf-8")
    (kb_dir / "Home.md").write_text(
        "---\nmanaged_by: KnowledgeDigest\ndigest_kind: home\n---\n# Home\n",
        encoding="utf-8",
    )
    (kb_dir / "indexes").mkdir()
    (kb_dir / "indexes" / "pending.md").write_text(
        "---\nmanaged_by: KnowledgeDigest\ndigest_kind: category\n---\n# 待归类\n",
        encoding="utf-8",
    )
    before = _formal_bytes(kb_dir)

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    assert _formal_bytes(kb_dir) == before


def test_initialization_dry_run_never_creates_a_new_kb(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=True)
    kb_dir = tmp_path / "new-kb"

    result = _run_digest(
        str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm", "--dry-run"
    )

    assert result.returncode == 1
    assert not kb_dir.exists()


def test_initialization_rejects_batch_before_creating_a_new_kb(tmp_path: Path) -> None:
    new_dir = _new_input(tmp_path, with_source=True)
    kb_dir = tmp_path / "new-kb"

    result = _run_digest(
        str(new_dir),
        str(kb_dir),
        "--config",
        str(_offline_config(tmp_path)),
        "--no-llm",
        "--batch-size",
        "1",
    )

    assert result.returncode == 1
    assert "new knowledge-base initialization" in result.stderr
    assert not kb_dir.exists()


def test_offline_title_priority_creates_readable_published_paths(tmp_path: Path) -> None:
    cases = (
        ("source.md", "# H1 title\n\nSource evidence.", "Metadata title", "Metadata title", "metadata-title.md"),
        ("source.md", "# H1 title\n\nSource evidence.", None, "H1 title", "h1-title.md"),
        ("file-name.md", "Source evidence without a heading.\n", None, "file-name", "file-name.md"),
    )
    for index, (name, text, metadata_title, expected_title, expected_name) in enumerate(cases):
        case_dir = tmp_path / str(index)
        case_dir.mkdir()
        new_dir = _new_titled_input(
            case_dir,
            name=name,
            text=text,
            metadata_title=metadata_title,
        )
        kb_dir = case_dir / "kb"
        result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(case_dir)), "--no-llm")

        assert result.returncode == 0, result.stderr
        pages = sorted((kb_dir / "pages" / "待归类").glob("*.md"))
        assert [path.name for path in pages] == [expected_name]
        page = pages[0].read_text(encoding="utf-8")
        assert "managed_by: KnowledgeDigest" in page
        assert "digest_kind: topic" in page
        assert f"digest_published_path: pages/待归类/{expected_name}" in page
        assert f"# {expected_title}" in page
        assert "## Summary" in page
        assert "## Evidence" in page
        assert "## Provenance" in page
        assert len(page.splitlines()) <= 300


def test_published_path_stays_locked_to_existing_managed_topic(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="source.md",
        text="# Initial H1\n\nInitial source evidence.\n",
        metadata_title="Initial title",
    )
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)

    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert first.returncode == 0, first.stderr
    first_path = next((kb_dir / "pages" / "待归类").glob("*.md"))

    (new_dir / "items" / "source.md").write_text(
        "# Changed H1\n\nChanged source evidence.\n", encoding="utf-8"
    )
    (new_dir / "sources.jsonl").write_text(
        json.dumps(
            {
                "content_path": "source.md",
                "source_uri": "https://source.example/note",
                "title": "Changed title",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    second = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert second.returncode == 0, second.stderr
    pages = sorted((kb_dir / "pages" / "待归类").glob("*.md"))
    assert pages == [first_path]
    page = first_path.read_text(encoding="utf-8")
    assert "# Initial title" in page
    assert "Changed source evidence." in page


def test_published_path_adds_identity_only_for_a_same_title_collision() -> None:
    from knowledge_digest.identity import publication_topic_part_path, published_part_path

    topic = "topic-1234567890abcdef"
    assert publication_topic_part_path("pages/待归类", "Same title", topic, 1) == "pages/待归类/same-title.md"
    assert publication_topic_part_path(
        "pages/待归类", "Same title", topic, 1, disambiguate=True
    ) == "pages/待归类/same-title-12345678.md"
    assert published_part_path("pages/待归类/same-title.md", 2) == "pages/待归类/same-title.part-002.md"


def test_navigation_records_are_artifacts_not_direct_formal_writes(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="source.md",
        text="# Release notes\n\nSource evidence.\n",
        metadata_title="Release notes",
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(_publication_structure(), encoding="utf-8")

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    run_dirs = sorted((kb_dir / "_digest" / "runs").iterdir())
    records = [
        json.loads(line)
        for line in (run_dirs[-1] / "s4" / "publication-navigation.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [record["digest_kind"] for record in records] == ["home", "category", "source-index"]
    assert records[0]["target_path"] == "Home.md"
    assert "[待归类](indexes/pending.md)" in records[0]["rendered_content"]
    assert records[1]["target_path"] == "indexes/pending.md"
    assert "[Release notes](../pages/待归类/release-notes.md)" in records[1]["rendered_content"]
    for record in records:
        assert record["layout_finalized"] is True
        assert record["claims"] == []
        assert "## Evidence" not in record["rendered_content"]
        assert "## Provenance" not in record["rendered_content"]
    assert (kb_dir / "Home.md").read_text(encoding="utf-8") == records[0]["rendered_content"]
    assert (kb_dir / "indexes" / "pending.md").read_text(encoding="utf-8") == records[1]["rendered_content"]


def test_handwritten_home_fails_before_any_formal_publication_change(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="source.md",
        text="# Managed topic\n\nSource evidence.\n",
        metadata_title="Managed topic",
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(_publication_structure(), encoding="utf-8")
    (kb_dir / "Home.md").write_text("# Handwritten home\n", encoding="utf-8")
    before = _formal_bytes(kb_dir)

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert "managed_by" in result.stderr
    assert _formal_bytes(kb_dir) == before


def test_empty_existing_home_is_not_taken_over(tmp_path: Path) -> None:
    new_dir = _new_titled_input(tmp_path, name="source.md", text="# Managed topic\n\nSource evidence.\n", metadata_title="Managed topic")
    kb_dir = tmp_path / "kb"; kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(_publication_structure(), encoding="utf-8")
    (kb_dir / "Home.md").write_text("", encoding="utf-8")
    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")
    assert result.returncode == 1
    assert "managed_by" in result.stderr
    assert (kb_dir / "Home.md").read_text(encoding="utf-8") == ""


def test_structure_symlink_is_rejected(tmp_path: Path) -> None:
    new_dir = _new_titled_input(tmp_path, name="source.md", text="# Topic\n\nEvidence.\n", metadata_title="Topic")
    kb_dir = tmp_path / "kb"; kb_dir.mkdir()
    outside = tmp_path / "outside.md"; outside.write_text(_publication_structure(), encoding="utf-8")
    (kb_dir / "kb.structure.md").symlink_to(outside)
    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")
    assert result.returncode == 1
    assert "symlink" in result.stderr


def test_managed_topic_header_path_mismatch_fails_before_formal_changes(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="source.md",
        text="# Fresh topic\n\nSource evidence.\n",
        metadata_title="Fresh topic",
    )
    kb_dir = tmp_path / "kb"
    topic_dir = kb_dir / "pages" / "待归类"
    topic_dir.mkdir(parents=True)
    (kb_dir / "kb.structure.md").write_text(_publication_structure(), encoding="utf-8")
    (topic_dir / "mismatch.md").write_text(
        "---\nmanaged_by: KnowledgeDigest\ndigest_kind: topic\ndigest_topic_id: topic-bad\n"
        "digest_published_path: pages/待归类/not-mismatch.md\ndigest_part: 1\n---\n\n# Broken\n",
        encoding="utf-8",
    )
    before = _formal_bytes(kb_dir)

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert "digest_published_path" in result.stderr
    assert _formal_bytes(kb_dir) == before


def test_handwritten_topic_is_not_a_managed_retrieve_candidate(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="source.md",
        text="# Published topic\n\nUnique publishable evidence.\n",
        metadata_title="Published topic",
    )
    kb_dir = tmp_path / "kb"
    topic_dir = kb_dir / "pages" / "待归类"
    topic_dir.mkdir(parents=True)
    (kb_dir / "kb.structure.md").write_text(_publication_structure(), encoding="utf-8")
    handwritten = topic_dir / "manual.md"
    handwritten.write_text("# Manual\n\nUnique publishable evidence.\n", encoding="utf-8")
    before = handwritten.read_bytes()

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    assert handwritten.read_bytes() == before
    assert (topic_dir / "published-topic.md").is_file()


def test_managed_navigation_keeps_topics_not_in_the_current_increment(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="alpha.md",
        text="# Alpha topic\n\nZebra lantern atlas evidence.\n",
        source_uri="https://source.example/alpha",
        metadata_title="Alpha topic",
    )
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)
    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert first.returncode == 0, first.stderr
    (new_dir / "items" / "alpha.md").unlink()
    (new_dir / "items" / "beta.md").write_text("# Beta topic\n\nQuantum orchard compass evidence.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps(
            {
                "content_path": "beta.md",
                "source_uri": "https://source.example/beta",
                "title": "Beta topic",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    second = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert second.returncode == 0, second.stderr
    category = (kb_dir / "indexes" / "pending.md").read_text(encoding="utf-8")
    assert "[Alpha topic](../pages/待归类/alpha-topic.md)" in category
    assert "[Beta topic](../pages/待归类/beta-topic.md)" in category


def test_managed_topic_updates_in_its_declared_existing_category(tmp_path: Path) -> None:
    from knowledge_digest.identity import source_id, topic_id

    uri = "https://source.example/team"
    stable_topic_id = topic_id([source_id(uri)])
    new_dir = _new_titled_input(
        tmp_path,
        name="team.md",
        text="# New source title\n\nTeam source evidence.\n",
        source_uri=uri,
        metadata_title="New source title",
    )
    kb_dir = tmp_path / "kb"
    structure = _publication_structure().replace(
        "    topic_dir: pages/待归类\n---\n",
        "    topic_dir: pages/待归类\n  - id: team\n    title: 团队\n    topic_dir: pages/team\n---\n",
    )
    team_page = kb_dir / "pages" / "team" / "team-topic.md"
    team_page.parent.mkdir(parents=True)
    (kb_dir / "kb.structure.md").write_text(structure, encoding="utf-8")
    team_page.write_text(
        "---\nmanaged_by: KnowledgeDigest\ndigest_kind: topic\n"
        f"digest_topic_id: {stable_topic_id}\ndigest_published_path: pages/team/team-topic.md\ndigest_part: 1\n"
        "---\n\n# Existing team topic\n\n## Summary\n- Existing.\n\n## Evidence\nTeam source evidence.\n"
        "\n## Provenance\n",
        encoding="utf-8",
    )

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    assert team_page.is_file()
    assert "# Existing team topic" in team_page.read_text(encoding="utf-8")
    assert "[Existing team topic](../pages/team/team-topic.md)" in (kb_dir / "indexes" / "team.md").read_text(
        encoding="utf-8"
    )
    assert "Existing team topic" not in (kb_dir / "indexes" / "pending.md").read_text(encoding="utf-8")


def test_shrink_keeps_old_part_but_removes_it_from_current_navigation(tmp_path: Path) -> None:
    original = "# Long topic\n\n" + "\n".join(f"Evidence line {index}." for index in range(360)) + "\n"
    new_dir = _new_titled_input(tmp_path, name="source.md", text=original, metadata_title="Long topic")
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)

    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert first.returncode == 0, first.stderr
    pages = sorted((kb_dir / "pages" / "待归类").glob("*.md"))
    assert len(pages) >= 2
    old_part = next(path for path in pages if ".part-002.md" in path.name)

    (new_dir / "items" / "source.md").write_text("# Long topic\n\nShort replacement.\n", encoding="utf-8")
    second = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert second.returncode == 0, second.stderr
    assert old_part.exists()
    category = (kb_dir / "indexes" / "pending.md").read_text(encoding="utf-8")
    assert old_part.name not in category


def test_transaction_archives_topic_home_and_category_before_update(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="source.md",
        text="# Transaction topic\n\nOriginal source evidence.\n",
        metadata_title="Transaction topic",
    )
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)
    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert first.returncode == 0, first.stderr
    topic = next((kb_dir / "pages" / "待归类").glob("*.md"))
    (new_dir / "items" / "source.md").write_text(
        "# Transaction topic\n\nUpdated source evidence.\n", encoding="utf-8"
    )

    second = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert second.returncode == 0, second.stderr
    archives = [
        json.loads(line)
        for line in (_latest_run(kb_dir) / "s5" / "archive-records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert {record["page_path"] for record in archives} >= {
        "Home.md",
        "indexes/pending.md",
        topic.relative_to(kb_dir).as_posix(),
    }


def test_provenance_and_history_exclude_navigation_records(tmp_path: Path) -> None:
    new_dir = _new_titled_input(
        tmp_path,
        name="source.md",
        text="# Provenance topic\n\nSource evidence.\n",
        metadata_title="Provenance topic",
    )
    kb_dir = tmp_path / "kb"

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    history = [
        json.loads(line)
        for line in (kb_dir / "_digest" / "claim-history.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert history
    assert all(record["target_path"].startswith("pages/待归类/") for record in history)
    from knowledge_digest.kb_structure import parse_source_index_markdown

    source_index = parse_source_index_markdown(
        (kb_dir / "_digest" / "source-index.md").read_text(encoding="utf-8")
    )
    assert source_index["entries"] and all(
        path.startswith("pages/待归类/")
        for record in source_index["entries"]
        for path in record["target_paths"]
    )
