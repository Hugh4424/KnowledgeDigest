"""Lossless, line-addressable semantic blocks for the Task7 compiler."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Mapping, Sequence

_HEADING_RE = re.compile(r"^\s*(#{1,6})(?:\s+(.*?)\s*|$)")
_LIST_RE = re.compile(r"^\s*(?P<marker>(?:[-+*]|\d+[.)]))(?:\s+|$)")
_TABLE_RE = re.compile(r"^\s*\|")
_ATTACHMENT_RE = re.compile(
    r"^\s*(?:!\[[^\]]*\]\([^)]*\)|\[附件\].*|(?:https?|ftp)://\S+\.(?:png|jpe?g|gif|svg|pdf|zip|docx?)(?:\?\S*)?)\s*$",
    re.IGNORECASE,
)
_ERROR_RE = re.compile(
    r"(?:^\s*(?:ERROR|Error|FATAL|Exception|Traceback)(?:\s*[:=]|\s|$)"
    r"|^\s*(?:ERROR[A-Z0-9_]*|[A-Z][A-Z0-9_]*ERROR[A-Z0-9_]*)(?:\s*[:=]|\s|$)"
    r"|^\s*E\d{2,}\b|^\s*at\s+[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\s*\("
    r"|^\s*File \".+\", line \d+)",
)

# Keep tokenization separate from the primary scanner.  The second pass may
# agree on the current contract while still exposing a future classifier bug.
_SECOND_HEADING_RE = re.compile(r"^\s*#{1,6}(?:\s+|$)(.*?)\s*$")
_SECOND_LIST_RE = re.compile(r"^\s*(?P<marker>[-+*]|\d+[.)])(?:\s+|$)")
_SECOND_TABLE_RE = re.compile(r"^\s*\|")
_SECOND_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?:[^`~].*)?$")
_SECOND_ATTACHMENT_RE = re.compile(
    r"^\s*(?:!\[[^\]]*\]\([^)]*\)|\[附件\].*|(?:https?|ftp)://\S+\.(?:png|jpe?g|gif|svg|pdf|zip|docx?)(?:\?\S*)?)\s*$",
    re.IGNORECASE,
)
_SECOND_ERROR_RE = re.compile(
    r"(?:^\s*(?:ERROR|Error|FATAL|Exception|Traceback)(?:\s*[:=]|\s|$)"
    r"|^\s*(?:ERROR[A-Z0-9_]*|[A-Z][A-Z0-9_]*ERROR[A-Z0-9_]*)(?:\s*[:=]|\s|$)"
    r"|^\s*E\d{2,}\b|^\s*at\s+[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\s*\("
    r"|^\s*File \".+\", line \d+)",
)


@dataclass(frozen=True)
class Block:
    """One unchanged logical source unit."""

    source_path: str
    block_id: str
    content_hash: str
    kind: str
    line_start: int
    line_end: int
    text: str
    heading_path: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "block_id": self.block_id,
            "content_hash": self.content_hash,
            "kind": self.kind,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "text": self.text,
            "heading_path": list(self.heading_path),
        }


@dataclass(frozen=True)
class SplitResult:
    """Primary blocks plus an independently scanned comparison."""

    blocks: tuple[Block, ...]
    independent_blocks: tuple[Block, ...]
    differences: tuple[Mapping[str, Any], ...] = ()
    blockers: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class _RawRange:
    start: int
    end: int
    kind: str
    heading_path: tuple[str, ...]


def _encode_text(text: str) -> bytes:
    """Encode text while retaining bytes represented by surrogate escapes."""

    return text.encode("utf-8", "surrogateescape")


def _split_raw_text(raw: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return exact line slices and line contents for raw source text."""

    parts: list[str] = []
    contents: list[str] = []
    start = 0
    index = 0
    while index < len(raw):
        if raw[index] not in "\r\n":
            index += 1
            continue
        ending_start = index
        if raw[index] == "\r" and index + 1 < len(raw) and raw[index + 1] == "\n":
            index += 2
        else:
            index += 1
        parts.append(raw[start:index])
        contents.append(raw[start:ending_start])
        start = index
    if start < len(raw):
        parts.append(raw[start:])
        contents.append(raw[start:])
    return tuple(parts), tuple(contents)


def _source_lines(lines: Sequence[str] | str | bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Normalize supported inputs without stripping source content."""

    if isinstance(lines, bytes):
        return _split_raw_text(lines.decode("utf-8", "surrogateescape"))
    if isinstance(lines, str):
        return _split_raw_text(lines)
    values = tuple(
        item.decode("utf-8", "surrogateescape") if isinstance(item, bytes) else str(item)
        for item in lines
    )
    # A keepends sequence already carries exact separators.  A plain line
    # sequence is the existing compiler seam: infer LF between items, but keep
    # every character in each item, including a lone trailing CR.  Newline
    # characters are unambiguous evidence that the sequence already carries
    # separators; a lone CR in a line item remains source content.
    if any("\n" in item for item in values):
        return _split_raw_text("".join(values))
    if not values:
        return (), ()
    parts = tuple(item + ("\n" if index < len(values) - 1 else "") for index, item in enumerate(values))
    return parts, values


def _heading_path_update(path: list[str], line: str) -> tuple[str, ...]:
    match = _HEADING_RE.match(line)
    if match is None:
        return tuple(path)
    level = len(match.group(1))
    title = (match.group(2) or "").strip()
    del path[level:]
    while len(path) < level:
        path.append("")
    path[level - 1] = title
    return tuple(path)


def _list_family(line: str) -> str | None:
    match = _LIST_RE.match(line)
    if match is None:
        return None
    marker = match.group("marker")
    return "ordered" if marker[0].isdigit() else "bullet"


def _fence(line: str) -> str | None:
    match = re.match(r"^\s*(?P<fence>`{3,}|~{3,})(?:[^`~].*)?$", line)
    if match is None:
        return None
    return match.group("fence")


def _fence_closes(line: str, opening: str) -> bool:
    match = re.match(r"^\s*(?P<fence>`+|~+)\s*$", line)
    return (
        match is not None
        and match.group("fence")[0] == opening[0]
        and len(match.group("fence")) >= len(opening)
    )


def _is_attachment(line: str) -> bool:
    return _ATTACHMENT_RE.match(line) is not None


def _is_error(line: str) -> bool:
    return _ERROR_RE.search(line) is not None


def _line_kind(line: str) -> str | None:
    if _HEADING_RE.match(line):
        return "heading"
    if _TABLE_RE.match(line):
        return "table"
    if _list_family(line) is not None:
        return "list"
    if _fence(line) is not None:
        return "code"
    if _is_attachment(line):
        return "attachment_refs"
    if _is_error(line):
        return "error_text"
    return None


def _primary_scan(lines: tuple[str, ...]) -> tuple[list[_RawRange], list[dict[str, Any]]]:
    """Extend the existing exact-line evidence into semantic units."""

    ranges: list[_RawRange] = []
    blockers: list[dict[str, Any]] = []
    heading_path: list[str] = []
    index = 0

    while index < len(lines):
        if not lines[index].strip():
            start = index
            while index < len(lines) and not lines[index].strip():
                index += 1
            ranges.append(_RawRange(start, index, "narrative", tuple(heading_path)))
            continue

        start = index
        kind = _line_kind(lines[index])
        if kind == "heading":
            current = _heading_path_update(heading_path, lines[index])
            ranges.append(_RawRange(start, index + 1, kind, current))
            index += 1
            continue

        current = tuple(heading_path)
        if kind == "table":
            index += 1
            while index < len(lines) and _TABLE_RE.match(lines[index]):
                index += 1
        elif kind == "list":
            family = _list_family(lines[index])
            index += 1
            while index < len(lines) and _list_family(lines[index]) == family:
                index += 1
        elif kind == "code":
            fence = _fence(lines[start])
            index += 1
            closed = False
            while index < len(lines):
                if fence is not None and _fence_closes(lines[index], fence):
                    index += 1
                    closed = True
                    break
                index += 1
            if not closed:
                blockers.append({
                    "kind": "unparsed_structure",
                    "reason": "unclosed_code_fence",
                    "line_start": start + 1,
                    "line_end": index,
                    "impact": "code block remains byte-preserved but requires review",
                })
        elif kind == "attachment_refs":
            index += 1
            while index < len(lines) and _is_attachment(lines[index]):
                index += 1
        elif kind == "error_text":
            index += 1
            while index < len(lines) and _is_error(lines[index]):
                index += 1
        else:
            # A higher-priority unit embedded in a paragraph must not split
            # its remaining prose into one-line blocks.  Exported Markdown
            # can place a styled prose line at the end of one legacy range
            # and its continuation at the start of the next, so those ranges
            # cannot be a hard boundary for the lossless scanner.
            index += 1
            while index < len(lines) and lines[index].strip() and _line_kind(lines[index]) is None:
                index += 1

        ranges.append(_RawRange(start, index, kind or "narrative", current))

    return ranges, blockers


def _independent_token(line: str) -> tuple[str, str | None]:
    """Second scanner tokenizes lines independently of `_primary_scan`."""

    if _SECOND_HEADING_RE.match(line):
        return "heading", None
    if _SECOND_TABLE_RE.match(line):
        return "table", None
    list_match = _SECOND_LIST_RE.match(line)
    if list_match:
        marker = list_match.group("marker")
        return "list", "ordered" if marker[0].isdigit() else "bullet"
    fence_match = _SECOND_FENCE_RE.match(line)
    fence = fence_match.group("fence") if fence_match else None
    if fence:
        return "code", fence
    if _SECOND_ATTACHMENT_RE.match(line):
        return "attachment_refs", None
    if _SECOND_ERROR_RE.search(line):
        return "error_text", None
    return "narrative", None


def _independent_scan(lines: tuple[str, ...]) -> tuple[list[_RawRange], list[dict[str, Any]]]:
    """State-machine scan used only for primary/secondary cross-checking."""

    ranges: list[_RawRange] = []
    blockers: list[dict[str, Any]] = []
    heading_path: list[str] = []
    start: int | None = None
    mode: str | None = None
    family: str | None = None
    fence: str | None = None

    def flush(end: int) -> None:
        nonlocal start, mode, family, fence
        if start is not None and mode is not None:
            ranges.append(_RawRange(
                start,
                end,
                "narrative" if mode == "blank" else mode,
                tuple(heading_path),
            ))
        start = None
        mode = None
        family = None
        fence = None

    for index, line in enumerate(lines):
        if mode == "code":
            closing_match = re.match(r"^\s*(?P<delimiter>`+|~+)\s*$", line)
            if (
                fence is not None
                and closing_match is not None
                and closing_match.group("delimiter")[0] == fence[0]
                and len(closing_match.group("delimiter")) >= len(fence)
            ):
                flush(index + 1)
            continue

        if not line.strip():
            if mode == "blank" and start is not None:
                continue
            flush(index)
            start = index
            mode = "blank"
            continue

        token, token_value = _independent_token(line)
        if token == "heading":
            flush(index)
            start = index
            mode = "heading"
            _heading_path_update(heading_path, line)
            flush(index + 1)
            continue

        if start is None:
            start = index
            mode = token
            family = token_value if token == "list" else None
            fence = token_value if token == "code" else None
            continue

        if mode == "blank":
            flush(index)
            start = index
            mode = token
            family = token_value if token == "list" else None
            fence = token_value if token == "code" else None
            continue

        same_unit = (
            token == mode
            and (token != "list" or token_value == family)
            and token not in {"code", "heading"}
        )
        if same_unit:
            continue

        flush(index)
        start = index
        mode = token
        family = token_value if token == "list" else None
        fence = token_value if token == "code" else None

    if mode == "code" and start is not None:
        blockers.append({
            "kind": "unparsed_structure",
            "reason": "unclosed_code_fence",
            "line_start": start + 1,
            "line_end": len(lines),
            "impact": "code block remains byte-preserved but requires review",
        })
    flush(len(lines))
    return ranges, blockers


def _materialize(
    ranges: Sequence[_RawRange],
    raw_parts: tuple[str, ...],
    source_path: str,
    source_id: str,
) -> tuple[Block, ...]:
    blocks: list[Block] = []
    for number, item in enumerate(ranges, 1):
        text = "".join(raw_parts[item.start : item.end])
        blocks.append(Block(
            source_path=source_path,
            block_id=f"{source_id}-b{number:04d}",
            content_hash=hashlib.sha256(_encode_text(text)).hexdigest(),
            kind=item.kind,
            line_start=item.start + 1,
            line_end=item.end,
            text=text,
            heading_path=item.heading_path,
        ))
    return tuple(blocks)


def _compare(primary: Sequence[Block], secondary: Sequence[Block]) -> tuple[Mapping[str, Any], ...]:
    differences: list[Mapping[str, Any]] = []
    for index in range(max(len(primary), len(secondary))):
        left = primary[index] if index < len(primary) else None
        right = secondary[index] if index < len(secondary) else None
        left_signature = None if left is None else (left.kind, left.line_start, left.line_end, left.text)
        right_signature = None if right is None else (right.kind, right.line_start, right.line_end, right.text)
        if left_signature != right_signature:
            differences.append({
                "index": index,
                "primary": left_signature,
                "independent": right_signature,
                "reason": "primary and independent block signatures differ",
            })
    return tuple(differences)


def split_source(
    lines: Sequence[str] | str | bytes,
    *,
    source_path: str,
    source_id: str | None = None,
) -> SplitResult:
    """Split source lines without rewriting or silently dropping bytes."""

    if not isinstance(source_path, str) or not source_path.strip():
        raise ValueError("source_path must be a non-empty string")
    raw_parts, normalized = _source_lines(lines)
    stable_id = source_id or "src-" + hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:20]

    primary_ranges, primary_blockers = _primary_scan(normalized)
    secondary_ranges, secondary_blockers = _independent_scan(normalized)
    blocks = _materialize(primary_ranges, raw_parts, source_path, stable_id)
    independent_blocks = _materialize(secondary_ranges, raw_parts, source_path, stable_id)
    differences = _compare(blocks, independent_blocks)
    blockers: list[Mapping[str, Any]] = []
    seen_blockers: set[tuple[Any, ...]] = set()
    for blocker in [*primary_blockers, *secondary_blockers]:
        key = (
            blocker.get("kind"),
            blocker.get("reason"),
            blocker.get("line_start"),
            blocker.get("line_end"),
        )
        if key in seen_blockers:
            continue
        seen_blockers.add(key)
        blockers.append(blocker)
    if differences:
        blockers.append({
            "kind": "split_mismatch",
            "reason": "independent scanner disagrees with primary scanner",
            "impact": "reference block coverage is not releaseable",
            "difference_count": len(differences),
        })
    return SplitResult(
        blocks=blocks,
        independent_blocks=independent_blocks,
        differences=differences,
        blockers=tuple(blockers),
    )
