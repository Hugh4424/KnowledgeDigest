"""Acceptance: real-world dirty documents survive the digest without losing content."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ITEMS = PROJECT_ROOT / "tests" / "fixtures" / "phase0_digest" / "new_dir" / "items"

DIRTY_FIXTURES = (
    "dirty-html-residue.md",
    "dirty-cjk-mixed.md",
    "dirty-malformed-frontmatter.md",
    "dirty-longline.md",
    "dirty-deep-structure.md",
)


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


def make_case(tmp_path: Path) -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    kb_dir.joinpath("kb.structure.md").write_text(
        "---\ncontract_version: phase1\nroots: [pages, _archive, _queues]\n"
        "why_field: why\nversion_field: version\n---\n",
        encoding="utf-8",
    )
    return new_dir, kb_dir


def write_source(new_dir: Path, name: str, text: str, uri: str) -> None:
    (new_dir / "items" / name).write_text(text, encoding="utf-8")
    source = {"content_path": name, "source_uri": uri, "captured_at": "2026-07-22T00:00:00Z"}
    (new_dir / "sources.jsonl").write_text(json.dumps(source) + "\n", encoding="utf-8")


def rendered_pages(kb_dir: Path) -> str:
    """Concatenate real on-disk page bodies with the Provenance section stripped."""
    return "\n".join(
        path.read_text(encoding="utf-8").split("\n\n## Provenance", 1)[0]
        for path in sorted((kb_dir / "pages").rglob("*.md"))
    )


def digest_dirty_fixture(tmp_path: Path, name: str) -> tuple[str, str]:
    """Run the digest over one dirty fixture and return (source text, rendered pages)."""
    new_dir, kb_dir = make_case(tmp_path)
    text = (FIXTURE_ITEMS / name).read_text(encoding="utf-8")
    write_source(new_dir, name, text, f"https://source.example/{name}")
    result = run_digest(str(new_dir), str(kb_dir))
    assert result.returncode == 0, result.stderr
    pages = list((kb_dir / "pages").rglob("*.md"))
    assert pages, f"{name} produced no official page"
    return text, rendered_pages(kb_dir)


def test_dirty_fixtures_exist() -> None:
    for name in DIRTY_FIXTURES:
        assert (FIXTURE_ITEMS / name).is_file(), name


@pytest.mark.parametrize("name", DIRTY_FIXTURES)
def test_dirty_fixture_survives_digest_line_by_line(tmp_path: Path, name: str) -> None:
    """Every non-blank source line must appear verbatim in the written pages."""
    text, rendered = digest_dirty_fixture(tmp_path, name)
    missing = [line for line in text.splitlines() if line.strip() and line not in rendered]
    assert not missing, f"{name} lost lines: {missing[:5]}"


def test_dirty_html_residue_keeps_markup_and_bom_characters(tmp_path: Path) -> None:
    text, rendered = digest_dirty_fixture(tmp_path, "dirty-html-residue.md")
    assert text.startswith("﻿")
    for token in ('<div class="content-body">', "&nbsp;", "<br/>", "<br />", "　", "</div>"):
        assert token in rendered, token


def test_dirty_cjk_mixed_keeps_punctuation_and_identifiers(tmp_path: Path) -> None:
    _, rendered = digest_dirty_fixture(tmp_path, "dirty-cjk-mixed.md")
    for token in ("E_FILTER_17", "E_CHART_09", "status=active", "page_size", "「全角引号」", "（全角括号）", "——"):
        assert token in rendered, token


def test_dirty_malformed_frontmatter_keeps_header_and_body(tmp_path: Path) -> None:
    text, rendered = digest_dirty_fixture(tmp_path, "dirty-malformed-frontmatter.md")
    assert text.count("status:") == 2 and text.count("version:") == 2
    assert "\t" in text
    for token in ("\ttags:\t[filter,\tchart]", 'name: unclosed quote "value', "E_FRONTMATTER_02"):
        assert token in rendered, token


def test_dirty_longline_is_not_rewrapped(tmp_path: Path) -> None:
    text, rendered = digest_dirty_fixture(tmp_path, "dirty-longline.md")
    long_line = max(text.splitlines(), key=len)
    assert len(long_line) > 800
    assert long_line in rendered
    assert "https://api.example/v2/filters?status=active&chart_type=bar&page_size=50&timeout=30" in rendered


def test_dirty_deep_structure_keeps_tables_lists_and_code_blocks(tmp_path: Path) -> None:
    text, rendered = digest_dirty_fixture(tmp_path, "dirty-deep-structure.md")
    table_rows = [line for line in text.splitlines() if line.startswith("|")]
    assert len(table_rows) >= 9
    for row in table_rows:
        assert row in rendered, row
    code_lines = [
        'payload = {"status": "active", "chart_type": "bar"}',
        'response = client.post("/v2/filters", json=payload, timeout=30)',
        "assert response.status_code == 200",
        '{"status": "active", "rows": 50, "truncated": false}',
    ]
    for line in code_lines:
        assert line in rendered, line
    assert rendered.count("```python") == 1 and rendered.count("```json") == 1
    for heading in ("### Filter fields", "#### Field limits", "### Error codes"):
        assert heading in rendered, heading
    for bullet in ("- status", "  - active", "    - visible in every chart type", "  - archived"):
        assert bullet in rendered, bullet
