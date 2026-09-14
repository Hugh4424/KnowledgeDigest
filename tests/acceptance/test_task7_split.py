"""Task7 P1: lossless semantic block-splitting contract."""

from __future__ import annotations

from knowledge_digest.semantic_split import split_source


def _ranges(records: tuple[object, ...]) -> list[tuple[int, int, str]]:
    return [
        (int(record.line_start), int(record.line_end), str(record.text))
        for record in records
    ]


def _sequence_slice(lines: tuple[str, ...], start: int, end: int) -> str:
    text = "\n".join(lines[start - 1 : end])
    return text + ("\n" if end < len(lines) else "")


def test_task7_split_aggregates_table_and_preserves_bad_row_bytes() -> None:
    lines = (
        "## Parameters",
        "- table follows",
        "| Field | Value |",
        "| --- | --- |",
        "| threshold | > 10 |",
        "| malformed row with **unclosed markup",
        "- next list item",
    )

    result = split_source(lines, source_path="fixture.md", source_id="fixture-p1")
    table_records = [record for record in result.blocks if record.kind == "table"]

    assert len(table_records) == 1
    assert table_records[0].line_start == 3
    assert table_records[0].line_end == 6
    assert table_records[0].text == _sequence_slice(lines, 3, 6)
    assert "**unclosed" in table_records[0].text
    assert "- table follows" not in table_records[0].text


def test_task7_split_keeps_reference_unit_boundaries_and_priority() -> None:
    lines = (
        "| Field | Value |",
        "| --- | --- |",
        "| malformed row",
        "- first item",
        "  - nested item",
        "```python",
        "raise ValueError('raw')",
        "```",
        "![diagram](https://example.test/diagram.png)",
        "![attachment](https://example.test/file.pdf)",
        "ERROR_CODE=E42",
        "Traceback (most recent call last):",
        "ordinary prose",
    )

    result = split_source(lines, source_path="fixture.md", source_id="fixture-p1")

    assert _ranges(result.blocks) == [
        (1, 3, _sequence_slice(lines, 1, 3)),
        (4, 5, _sequence_slice(lines, 4, 5)),
        (6, 8, _sequence_slice(lines, 6, 8)),
        (9, 10, _sequence_slice(lines, 9, 10)),
        (11, 12, _sequence_slice(lines, 11, 12)),
        (13, 13, lines[12]),
    ]
    assert [record.kind for record in result.blocks] == [
        "table",
        "list",
        "code",
        "attachment_refs",
        "error_text",
        "narrative",
    ]


def test_task7_split_matches_independent_second_method_without_dropping_lines() -> None:
    lines = (
        "# Heading",
        "A paragraph line.",
        "A second paragraph line.",
        "| key | value |",
        "| --- | --- |",
        "| k | v |",
        "```",
        "raw code",
        "```",
        "[附件] manual.pdf",
        "ERROR: keep this exact line",
        "Error: keep this exact continuation",
    )

    result = split_source(lines, source_path="fixture.md", source_id="fixture-p1")

    assert result.differences == ()
    assert _ranges(result.blocks) == _ranges(result.independent_blocks)
    assert "".join(record.text for record in result.blocks) == "\n".join(lines)


def test_task7_split_keeps_unclosed_structure_raw_and_reports_one_blocker() -> None:
    lines = ("```python", "raise RuntimeError('keep')")

    result = split_source(lines, source_path="fixture.md", source_id="fixture-p1")

    assert result.differences == ()
    assert len(result.blocks) == 1
    assert result.blocks[0].kind == "code"
    assert result.blocks[0].text == "\n".join(lines)
    assert [item["reason"] for item in result.blockers] == ["unclosed_code_fence"]


def test_task7_split_conserves_raw_separators_and_blank_lines() -> None:
    source = "intro\r\n \r\n| key | value |\r\n| --- | --- |\r\n| bad row\r\n\r\nERROR: preserve\r\n"

    result = split_source(source, source_path="crlf.md", source_id="fixture-p1")

    assert result.differences == ()
    assert "".join(record.text for record in result.blocks) == source
    assert any(record.text == " \r\n" for record in result.blocks)
    assert result.blocks[0].content_hash == "17aa257c8dcb17871a7a15aa0acd16d629e1eb1fdc45a828992e02bf5bcb9612"

    trailing_cr = split_source(("trailing carriage return\r",), source_path="crlf.md", source_id="fixture-p1")
    assert "".join(record.text for record in trailing_cr.blocks) == "trailing carriage return\r"


def test_task7_split_groups_narrative_after_embedded_error_and_avoids_error_word_false_positive() -> None:
    lines = (
        "step one",
        "ERROR_CODE=E42",
        "step two",
        "step three",
        "at this point the worker restarts",
        "catch Exception and retry",
    )

    result = split_source(lines, source_path="embedded.md", source_id="fixture-p1")

    assert result.differences == ()
    assert [(record.kind, record.line_start, record.line_end) for record in result.blocks] == [
        ("narrative", 1, 1),
        ("error_text", 2, 2),
        ("narrative", 3, 6),
    ]


def test_task7_split_uses_same_attachment_grammar_in_both_scanners() -> None:
    lines = ("[附件]", "https://example.test/download")

    result = split_source(lines, source_path="attachments.md", source_id="fixture-p1")

    assert result.differences == ()
    assert [(record.kind, record.line_start, record.line_end) for record in result.blocks] == [
        ("attachment_refs", 1, 1),
        ("narrative", 2, 2),
    ]


def test_task7_split_requires_matching_long_fence_delimiters() -> None:
    lines = ("````python", "```", "raw", "````")

    result = split_source(lines, source_path="long-fence.md", source_id="fixture-p1")

    assert result.differences == ()
    assert result.blockers == ()
    assert [(record.kind, record.line_start, record.line_end) for record in result.blocks] == [
        ("code", 1, 4),
    ]


def test_task7_split_agrees_on_empty_atx_headings() -> None:
    result = split_source(("#", "following prose"), source_path="empty-heading.md", source_id="fixture-p1")

    assert result.differences == ()
    assert [record.kind for record in result.blocks] == ["heading", "narrative"]
