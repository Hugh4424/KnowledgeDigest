"""Task0 Phase 3 acceptance: clean Reader/Audit navigation."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, unquote


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
    path.write_text(json.dumps({"similarity": {"backend": "jaccard"}, "llm_enabled": False}), encoding="utf-8")
    return path


def _input(tmp_path: Path, *, with_source: bool = True) -> Path:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    if with_source:
        (new_dir / "items" / "good.md").write_text(
            "# Good topic\nA stable source claim for the Reader package.\n",
            encoding="utf-8",
        )
        (new_dir / "sources.jsonl").write_text(
            json.dumps({"content_path": "good.md", "source_uri": "https://source.example/good"}) + "\n",
            encoding="utf-8",
        )
    return new_dir


def _reader_files(kb_dir: Path) -> list[Path]:
    return [
        path
        for path in kb_dir.rglob("*")
        if path.is_file()
        and path.relative_to(kb_dir).parts[0] in {"README.md", "Home.md", "indexes", "pages"}
    ]


def _assert_links_resolve(kb_dir: Path) -> None:
    for page in _reader_files(kb_dir):
        for raw_target in re.findall(r"\]\(([^)#]+)(?:#[^)]+)?\)", page.read_text(encoding="utf-8")):
            if "://" in raw_target:
                continue
            target = (page.parent / unquote(raw_target)).resolve()
            assert target.is_file(), f"broken Reader link {page.relative_to(kb_dir)} -> {raw_target}"


def _markdown_links(page: Path) -> list[str]:
    return [target for target in re.findall(r"\]\(([^)#]+)(?:#[^)]+)?\)", page.read_text(encoding="utf-8")) if "://" not in target]


def test_complete_reader_journey_reaches_source_and_audit_facts(tmp_path: Path) -> None:
    """Exercise the whole Task0 reader-to-audit path, not only link syntax."""
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr

    readme = kb_dir / "README.md"
    home = kb_dir / "Home.md"
    assert _markdown_links(readme) == ["Home.md"]
    assert home.is_file()

    parent = (home.parent / _markdown_links(home)[0]).resolve()
    category = (parent.parent / _markdown_links(parent)[0]).resolve()
    topic = (category.parent / _markdown_links(category)[0]).resolve()
    assert parent.relative_to(kb_dir).as_posix() == "indexes/other.md"
    assert category.relative_to(kb_dir).as_posix() == "indexes/pending.md"
    assert topic.relative_to(kb_dir).as_posix().startswith("pages/")
    assert "## Evidence" in topic.read_text(encoding="utf-8")
    assert "## Provenance" in topic.read_text(encoding="utf-8")

    source_index = kb_dir / "indexes" / "sources.md"
    assert source_index.is_file()
    source_text = source_index.read_text(encoding="utf-8")
    assert "https://source.example/good" in source_text
    encoded_topic_path = quote(topic.relative_to(kb_dir).as_posix(), safe="/._-")
    assert encoded_topic_path in source_text
    source_links = _markdown_links(source_index)
    assert source_links and all((source_index.parent / unquote(link)).resolve().is_file() for link in source_links)
    assert any((topic.parent / link).resolve() == source_index.resolve() for link in _markdown_links(topic))

    manifest = json.loads((kb_dir / "_digest" / "source-manifest.json").read_text(encoding="utf-8"))
    ledger = [json.loads(line) for line in (kb_dir / "_digest" / "source-audit-ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    claims = [json.loads(line) for line in (kb_dir / "_digest" / "claim-history.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert manifest["sources"][0]["source_uri"] == "https://source.example/good"
    assert ledger[0]["source_uri"] == manifest["sources"][0]["source_uri"]
    assert any(
        claim["source_uri"] == "https://source.example/good"
        and claim["target_path"] == topic.relative_to(kb_dir).as_posix()
        and claim["verification_status"] == "verified"
        for claim in claims
    )


def test_failed_source_stays_in_audit_and_out_of_reader_navigation(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    (new_dir / "items" / "failed.md").write_text("", encoding="utf-8")
    sources = (new_dir / "sources.jsonl").read_text(encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        sources + json.dumps({"content_path": "failed.md", "source_uri": "https://source.example/failed"}) + "\n",
        encoding="utf-8",
    )
    kb_dir = tmp_path / "kb"

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    reader_text = "\n".join(path.read_text(encoding="utf-8") for path in _reader_files(kb_dir))
    assert "https://source.example/good" in reader_text
    assert "https://source.example/failed" not in reader_text
    manifest = json.loads((kb_dir / "_digest" / "source-manifest.json").read_text(encoding="utf-8"))
    ledger = [
        json.loads(line)
        for line in (kb_dir / "_digest" / "source-audit-ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(row["source_uri"] == "https://source.example/failed" for row in manifest["sources"])
    assert any(
        row["source_uri"] == "https://source.example/failed"
        and row.get("validation_status") in {"failed", "degraded"}
        for row in ledger
    )


def test_new_run_projects_sources_into_reader_and_not_legacy_digest_index(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    assert (kb_dir / "indexes" / "sources.md").is_file()
    assert not (kb_dir / "_digest" / "source-index.md").exists()
    assert not (kb_dir / "_digest" / "source-index.jsonl").exists()


def test_reader_has_no_empty_category_pages_and_links_are_real(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    assert (kb_dir / "indexes" / "pending.md").is_file()
    assert "indexes/pending.md" in (kb_dir / "Home.md").read_text(encoding="utf-8")
    assert not (kb_dir / "indexes" / "architecture.md").exists()
    assert not (kb_dir / "indexes" / "product-overview.md").exists()
    assert "products.md" not in (kb_dir / "Home.md").read_text(encoding="utf-8")
    assert all("_digest" not in path.relative_to(kb_dir).parts for path in _reader_files(kb_dir))
    _assert_links_resolve(kb_dir)


def test_stale_source_target_fails_closed_before_reader_projection(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)
    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert first.returncode == 0, first.stderr
    topic = next(path for path in (kb_dir / "pages").rglob("*.md"))
    topic.unlink()

    empty_new_dir = tmp_path / "empty-new"
    (empty_new_dir / "items").mkdir(parents=True)
    second = _run_digest(str(empty_new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert second.returncode == 1
    assert "source index target page is missing" in second.stderr


def test_empty_new_run_does_not_create_an_empty_pending_entry(tmp_path: Path) -> None:
    new_dir = _input(tmp_path, with_source=False)
    kb_dir = tmp_path / "kb"
    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 0, result.stderr
    assert (kb_dir / "Home.md").is_file()
    assert not (kb_dir / "indexes" / "pending.md").exists()
    assert "pending.md" not in (kb_dir / "Home.md").read_text(encoding="utf-8")
