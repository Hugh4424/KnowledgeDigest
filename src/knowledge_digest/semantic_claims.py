"""Sentence-level claims with exact source spans for the Task7 compiler."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Iterable, Mapping, MutableMapping
import unicodedata

from .semantic_split import Block


_MISSING = object()
_BOUNDARY_RE = re.compile(r"(?:\r\n|[\r\n]|[。！？!?；;\.])")
_WHITESPACE_RE = re.compile(r"\s+")
_BOUNDARY_ONLY_CHARS = frozenset("\r\n。！？!?；;.")
_COMMON_ABBREVIATIONS = frozenset(
    {
        "approx",
        "capt",
        "dept",
        "dr",
        "etc",
        "fig",
        "jr",
        "mr",
        "mrs",
        "ms",
        "prof",
        "rev",
        "sr",
        "st",
        "vs",
    }
)


@dataclass(frozen=True)
class Claim:
    """A narrative or intro sentence and its source/page span."""

    claim_id: str
    source_path: str
    content_hash: str
    line_start: int | None
    line_end: int | None
    char_start: int | None
    char_end: int | None
    page_path: str | None
    page_anchor: str | None
    span_start: int
    span_end: int
    claim_kind: str
    status: str
    text: str
    occurrence_index: int
    retrieval_evidence: tuple[Mapping[str, Any], ...] = ()
    source_block_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "claim_id": self.claim_id,
            "source_path": self.source_path,
            "content_hash": self.content_hash,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "page_path": self.page_path,
            "page_anchor": self.page_anchor,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "claim_kind": self.claim_kind,
            "status": self.status,
            "text": self.text,
            "occurrence_index": self.occurrence_index,
        }
        if self.source_block_id is not None:
            result["source_block_id"] = self.source_block_id
        if self.retrieval_evidence:
            result["retrieval_evidence"] = [dict(item) for item in self.retrieval_evidence]
        return result


@dataclass(frozen=True)
class ClaimResult:
    claims: tuple[Claim, ...]

    @property
    def fact_claims(self) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if claim.status == "sourced")

    @property
    def rejected_claims(self) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if claim.status == "原文未明确")


@dataclass(frozen=True)
class IntroResult:
    claims: tuple[Claim, ...]
    rendered_text: str

    @property
    def fact_claims(self) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if claim.status == "sourced")

    @property
    def rejected_claims(self) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if claim.status == "原文未明确")


def _read_field(value: object, name: str, default: object = _MISSING) -> object:
    if isinstance(value, Mapping):
        result = value.get(name, default)
    else:
        result = getattr(value, name, default)
    if result is _MISSING:
        raise ValueError(f"block is missing {name!r}")
    return result


def _coerce_block(value: object) -> Block:
    if isinstance(value, Block):
        return value
    source_path = _read_field(value, "source_path")
    block_id = _read_field(value, "block_id", "claim-block")
    text = _read_field(value, "text", "")
    if not isinstance(source_path, str) or not source_path:
        raise ValueError("block.source_path must be a non-empty string")
    if not isinstance(block_id, str) or not block_id:
        raise ValueError("block.block_id must be a non-empty string")
    if not isinstance(text, str):
        raise TypeError("block.text must be a string")
    line_start = int(_read_field(value, "line_start", 1))
    line_end = int(_read_field(value, "line_end", line_start))
    if line_start < 1 or line_end < line_start:
        raise ValueError("block line range is invalid")
    content_hash = _read_field(value, "content_hash", "")
    if not isinstance(content_hash, str):
        raise TypeError("block.content_hash must be a string")
    heading_path = _read_field(value, "heading_path", ())
    if isinstance(heading_path, str):
        heading_path = (heading_path,)
    else:
        heading_path = tuple(str(item) for item in heading_path)
    if not content_hash:
        content_hash = hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()
    return Block(
        source_path=source_path,
        block_id=block_id,
        content_hash=content_hash,
        kind=str(_read_field(value, "kind", "narrative")),
        line_start=line_start,
        line_end=line_end,
        text=text,
        heading_path=heading_path,
    )


def _normalize_claim_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    return _WHITESPACE_RE.sub(" ", normalized).strip()


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _line_for_offset(text: str, offset: int, base_line: int) -> int:
    line = base_line
    index = 0
    limit = max(0, min(offset, len(text)))
    while index < limit:
        if text[index] == "\r":
            line += 1
            if index + 1 < limit and text[index + 1] == "\n":
                index += 1
        elif text[index] == "\n":
            line += 1
        index += 1
    return line


def _claim_id(
    source_path: str,
    line_start: int | None,
    line_end: int | None,
    char_start: int | None,
    char_end: int | None,
    occurrence_index: int,
    normalized_text: str,
    claim_kind: str,
) -> str:
    payload = "\x1f".join(
        (
            source_path,
            str(line_start),
            str(line_end),
            str(char_start),
            str(char_end),
            str(occurrence_index),
            claim_kind,
            normalized_text,
        )
    )
    return "cl_" + hashlib.sha256(payload.encode("utf-8", "surrogateescape")).hexdigest()[:12]


def _is_abbreviation_period(text: str, match: re.Match[str]) -> bool:
    """Return whether a period is part of an abbreviation before a next word."""

    before = text[: match.start()]
    token_match = re.search(r"(?:[A-Za-z]\.)+[A-Za-z]$", before)
    if token_match is not None:
        token = token_match.group()
    else:
        token_match = re.search(r"[A-Za-z]{1,8}$", before)
        if token_match is None or token_match.group().casefold() not in _COMMON_ABBREVIATIONS:
            return False
        token = token_match.group()

    next_index = match.end()
    while next_index < len(text) and text[next_index].isspace():
        next_index += 1
    # An abbreviation at the end of a block can still be a sentence boundary;
    # only suppress it when another word follows it.
    return bool(token) and next_index < len(text) and text[next_index].isalnum()


def _sentence_spans(text: str) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in _BOUNDARY_RE.finditer(text):
        if match.group() == ".":
            previous = text[match.start() - 1] if match.start() else ""
            following = text[match.end()] if match.end() < len(text) else ""
            # A period between word characters is part of a token (versions,
            # host names, filenames, and abbreviations), not a sentence end.
            if (previous.isalnum() and following.isalnum()) or _is_abbreviation_period(text, match):
                continue
        candidate_start, candidate_end = _trim_span(text, start, match.end())
        if candidate_start < candidate_end and any(
            character not in _BOUNDARY_ONLY_CHARS
            and not character.isspace()
            for character in text[candidate_start:candidate_end]
        ):
            spans.append((candidate_start, candidate_end))
        start = match.end()
    candidate_start, candidate_end = _trim_span(text, start, len(text))
    if candidate_start < candidate_end and any(
        character not in _BOUNDARY_ONLY_CHARS and not character.isspace()
        for character in text[candidate_start:candidate_end]
    ):
        spans.append((candidate_start, candidate_end))
    return tuple(spans)


def extract_claims(
    block: object,
    *,
    occurrence_registry: MutableMapping[tuple[str, str], int] | None = None,
    page_path: str | None = None,
    page_anchor: str | None = None,
) -> ClaimResult:
    """Split a narrative block while keeping every claim tied to its span."""

    source = _coerce_block(block)
    registry = occurrence_registry if occurrence_registry is not None else {}
    claims: list[Claim] = []
    for char_start, char_end in _sentence_spans(source.text):
        claim_text = source.text[char_start:char_end]
        normalized = _normalize_claim_text(claim_text)
        registry_key = (source.source_path, normalized)
        occurrence_index = registry.get(registry_key, 0) + 1
        registry[registry_key] = occurrence_index
        line_start = _line_for_offset(source.text, char_start, source.line_start)
        line_end = _line_for_offset(source.text, char_end - 1, source.line_start)
        claims.append(
            Claim(
                claim_id=_claim_id(
                    source.source_path,
                    line_start,
                    line_end,
                    char_start,
                    char_end,
                    occurrence_index,
                    normalized,
                    "narrative",
                ),
                source_path=source.source_path,
                content_hash=source.content_hash,
                line_start=line_start,
                line_end=line_end,
                char_start=char_start,
                char_end=char_end,
                page_path=page_path,
                page_anchor=page_anchor,
                span_start=char_start,
                span_end=char_end,
                claim_kind="narrative",
                status="sourced",
                text=claim_text,
                occurrence_index=occurrence_index,
                source_block_id=source.block_id,
            )
        )
    return ClaimResult(claims=tuple(claims))


def compile_intro(
    sentences: Iterable[str],
    *,
    source_blocks: Iterable[object],
    page_source_path: str,
    page_content_hash: str,
) -> IntroResult:
    """Ground intro candidates; one unsupported sentence blanks the intro."""

    if not isinstance(page_source_path, str) or not page_source_path:
        raise ValueError("page_source_path must be a non-empty string")
    if not isinstance(page_content_hash, str) or not page_content_hash:
        raise ValueError("page_content_hash must be a non-empty string")

    source_claims: list[Claim] = []
    occurrence_registry: dict[tuple[str, str], int] = {}
    for source_block in source_blocks:
        source_claims.extend(
            extract_claims(source_block, occurrence_registry=occurrence_registry).claims
        )
    by_text: dict[str, list[Claim]] = {}
    for claim in source_claims:
        by_text.setdefault(claim.text, []).append(claim)

    intro_claims: list[Claim] = []
    intro_occurrences: dict[tuple[str, str], int] = {}
    rendered_parts: list[str] = []
    page_cursor = 0
    for raw_sentence in sentences:
        if not isinstance(raw_sentence, str):
            raise TypeError("intro sentences must be strings")
        sentence = raw_sentence.strip()
        if not sentence:
            continue
        normalized = _normalize_claim_text(sentence)
        registry_key = (page_source_path, sentence)
        occurrence_index = intro_occurrences.get(registry_key, 0) + 1
        intro_occurrences[registry_key] = occurrence_index
        matches = by_text.get(sentence, [])
        if len(matches) == 1:
            source_claim = matches[0]
            status = "sourced"
            source_path = source_claim.source_path
            content_hash = source_claim.content_hash
            line_start = source_claim.line_start
            line_end = source_claim.line_end
            char_start = source_claim.char_start
            char_end = source_claim.char_end
            retrieval_evidence: tuple[Mapping[str, Any], ...] = ()
            rendered_parts.append(sentence)
        else:
            status = "原文未明确"
            source_path = page_source_path
            content_hash = page_content_hash
            line_start = None
            line_end = None
            char_start = None
            char_end = None
            retrieval_evidence = (
                {
                    "query": sentence,
                    "matched": False,
                    "searched_sources": sorted({claim.source_path for claim in source_claims}),
                    "reason": (
                        "ambiguous source claim matches"
                        if len(matches) > 1
                        else "no exact source claim matched"
                    ),
                },
            )
        span_start = page_cursor
        span_end = page_cursor + len(sentence)
        intro_claims.append(
            Claim(
                claim_id=_claim_id(
                    source_path,
                    line_start,
                    line_end,
                    char_start,
                    char_end,
                    occurrence_index,
                    normalized,
                    "intro",
                ),
                source_path=source_path,
                content_hash=content_hash,
                line_start=line_start,
                line_end=line_end,
                char_start=char_start,
                char_end=char_end,
                page_path=None,
                page_anchor="intro",
                span_start=span_start,
                span_end=span_end,
                claim_kind="intro",
                status=status,
                text=sentence,
                occurrence_index=occurrence_index,
                retrieval_evidence=retrieval_evidence,
                source_block_id=(source_claim.source_block_id if len(matches) == 1 else None),
            )
        )
        page_cursor = span_end + 1

    result_claims = tuple(intro_claims)
    rendered_text = "原文未明确" if any(
        claim.status == "原文未明确" for claim in result_claims
    ) else " ".join(rendered_parts)
    return IntroResult(claims=result_claims, rendered_text=rendered_text)


__all__ = ["Claim", "ClaimResult", "IntroResult", "compile_intro", "extract_claims"]
