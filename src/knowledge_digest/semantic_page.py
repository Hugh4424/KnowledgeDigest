"""Deterministic semantic pages for the Task7 compiler.

This module only renders an in-memory page set.  It deliberately does not
decide batch state, audit status, or filesystem publication.  Those concerns
belong to the compiler and audit layers, while this layer owns the bytes and
paths that a page will contain.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import PurePosixPath
import re
from types import MappingProxyType
import unicodedata
from typing import Any, Iterable, Mapping, Sequence


PAGE_FRONTMATTER_FIELDS = (
    "title",
    "type",
    "page_model",
    "scope",
    "product",
    "section",
    "module",
    "tier",
    "trust",
    "source_status",
    "quality_status",
    "created",
    "updated",
    "generated_by",
    "tags",
    "source",
)

MAX_NARRATIVE_LINES = 300
ATTACHMENT_MARKER = "外部资源链接（原样保留；不下载、不改写、不删除）"
_MISSING = object()
_WHITESPACE_RE = re.compile(r"\s+")
_MD_SUFFIX_RE = re.compile(r"\.mdx?$", re.IGNORECASE)


@dataclass(frozen=True)
class PagePart:
    """One physical Markdown page part, including its rendered bytes."""

    part_number: int
    relative_path: str
    body: str
    text: str
    oversized_reference_block: bool = False
    source_block_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    anchor_ids: tuple[str, ...] = ()

    @property
    def body_line_count(self) -> int:
        """Return the line count used by the 300-line body contract."""

        return len(self.body.splitlines())

    def as_dict(self) -> dict[str, Any]:
        return {
            "part_number": self.part_number,
            "relative_path": self.relative_path,
            "body_line_count": self.body_line_count,
            "oversized_reference_block": self.oversized_reference_block,
            "body": self.body,
        }


@dataclass(frozen=True)
class RenderedPage:
    """One topic page and all of its deterministic physical parts."""

    topic_key: str
    title: str
    slug: str
    relative_path: str
    frontmatter: Mapping[str, Any]
    parts: tuple[PagePart, ...]

    @property
    def text(self) -> str:
        """Return the first physical page part for convenient consumers."""

        if not self.parts:
            return ""
        return self.parts[0].text

    @property
    def page_paths(self) -> tuple[str, ...]:
        return tuple(part.relative_path for part in self.parts)

    @property
    def all_text(self) -> str:
        return "\n".join(part.text for part in self.parts)

    def as_dict(self) -> dict[str, Any]:
        return {
            "topic_key": self.topic_key,
            "title": self.title,
            "slug": self.slug,
            "relative_path": self.relative_path,
            "frontmatter": dict(self.frontmatter),
            "parts": [part.as_dict() for part in self.parts],
        }


@dataclass(frozen=True)
class _SourceBlock:
    source_path: str
    block_id: str
    content_hash: str
    kind: str
    line_start: int
    line_end: int
    text: str
    heading_path: tuple[str, ...]
    source_mtime: object


@dataclass(frozen=True)
class _PageDraft:
    topic_key: str
    group_title: str
    product: str
    section: str
    members: tuple[_SourceBlock, ...]
    model: Mapping[str, Any]
    title: str
    base_slug: str
    slug: str


@dataclass(frozen=True)
class _Unit:
    text: str
    reference_block: bool = False
    source_block_id: str | None = None
    claim_id: str | None = None
    anchor_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class _PartitionedBody:
    text: str
    source_block_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    anchor_ids: tuple[str, ...] = ()


def _read_field(value: object, name: str, default: object = _MISSING) -> object:
    if isinstance(value, Mapping):
        result = value.get(name, default)
    else:
        result = getattr(value, name, default)
    if result is _MISSING:
        raise ValueError(f"value is missing {name!r}")
    return result


def _optional_field(value: object, name: str, default: object = _MISSING) -> object:
    """Read a field without turning the sentinel into a required-field error."""

    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def gbrain_slug(segment: str) -> str:
    """Apply gbrain's exact single-segment slug algorithm.

    gbrain uses NFD rather than a transliteration library: accents are removed,
    non-ASCII characters are deleted, spaces become hyphens, and dots,
    underscores, and existing hyphens remain valid.
    """

    if not isinstance(segment, str):
        raise TypeError("slug segment must be a string")
    value = unicodedata.normalize("NFD", segment)
    value = re.sub(r"[\u0300-\u036f]", "", value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9.\s_-]", "", value)
    value = re.sub(r"[\s]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return re.sub(r"^-|-+$", "", value)


def _encode_text(text: str) -> bytes:
    return text.encode("utf-8", "surrogateescape")


def _coerce_source_path(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("block.source_path must be a non-empty string")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"block.source_path must be relative: {value!r}")
    return "/".join(part for part in path.parts if part not in {"", "."})


def _coerce_source_mtime(value: object) -> object:
    if value is _MISSING or value is None:
        return _MISSING
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, tz=timezone.utc).date()
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return _MISSING
        try:
            return date.fromisoformat(candidate[:10])
        except ValueError as exc:
            raise ValueError(f"invalid source mtime: {value!r}") from exc
    raise TypeError(f"unsupported source mtime type: {type(value).__name__}")


def _mtime_for(source_path: str, block: object, source_mtimes: Mapping[object, object] | None) -> object:
    declared = _optional_field(block, "source_mtime", _MISSING)
    if declared is _MISSING:
        declared = _optional_field(block, "mtime", _MISSING)
    if declared is _MISSING and source_mtimes is not None:
        declared = source_mtimes.get(source_path, _MISSING)
        if declared is _MISSING:
            declared = source_mtimes.get(PurePosixPath(source_path), _MISSING)
    result = _coerce_source_mtime(declared)
    if result is _MISSING:
        raise ValueError(f"source mtime is required for {source_path!r}")
    return result


def _coerce_block(value: object, source_mtimes: Mapping[object, object] | None) -> _SourceBlock:
    source_path = _coerce_source_path(_read_field(value, "source_path"))
    block_id = _read_field(value, "block_id", "block")
    if not isinstance(block_id, str) or not block_id:
        raise ValueError("block.block_id must be a non-empty string")
    raw_text = _read_field(value, "text", "")
    if isinstance(raw_text, bytes):
        text = raw_text.decode("utf-8", "surrogateescape")
    elif isinstance(raw_text, str):
        text = raw_text
    else:
        raise TypeError("block.text must be a string or bytes")
    declared_hash = _read_field(value, "content_hash", "")
    if not isinstance(declared_hash, str):
        raise TypeError("block.content_hash must be a string")
    content_hash = declared_hash or hashlib.sha256(_encode_text(text)).hexdigest()
    kind = str(_read_field(value, "kind", "narrative"))
    line_start = int(_read_field(value, "line_start", 1))
    line_end = int(_read_field(value, "line_end", max(line_start, len(text.splitlines()))))
    if line_start < 1 or line_end < line_start:
        raise ValueError("block line range is invalid")
    heading_path = _read_field(value, "heading_path", ())
    if isinstance(heading_path, str):
        heading_values = (heading_path,)
    else:
        heading_values = tuple(str(item) for item in heading_path)
    return _SourceBlock(
        source_path=source_path,
        block_id=block_id,
        content_hash=content_hash,
        kind=kind,
        line_start=line_start,
        line_end=line_end,
        text=text,
        heading_path=heading_values,
        source_mtime=_mtime_for(source_path, value, source_mtimes),
    )


def _coerce_group(value: object, source_mtimes: Mapping[object, object] | None) -> tuple[str, str, str, tuple[_SourceBlock, ...]]:
    topic_key = _optional_field(value, "key", _MISSING)
    if topic_key is _MISSING:
        topic_key = _read_field(value, "topic_key")
    product = _read_field(value, "product")
    title = _read_field(value, "title")
    module_anchor = _read_field(value, "module_anchor", _read_field(value, "module", "_general"))
    members = _read_field(value, "members")
    if not isinstance(topic_key, str) or not topic_key:
        raise ValueError("group.key must be a non-empty string")
    if not isinstance(product, str) or not product:
        raise ValueError("group.product must be a non-empty string")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("group.title must be a non-empty string")
    if not isinstance(module_anchor, str) or not module_anchor:
        raise ValueError("group.module_anchor must be a non-empty string")
    if isinstance(members, (str, bytes, Mapping)):
        raise TypeError("group.members must be an iterable of blocks")
    coerced = tuple(_coerce_block(member, source_mtimes) for member in members)
    if not coerced:
        raise ValueError(f"group {topic_key!r} must contain at least one member")
    ordered = tuple(
        sorted(
            coerced,
            key=lambda block: (block.source_path, block.line_start, block.line_end, block.block_id),
        )
    )
    return topic_key, product, title, module_anchor, ordered


def _mapping_like(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    result: dict[str, Any] = {}
    for name in ("title", "intro", "slug", "slug_candidate", "page_slug", "intro_result"):
        candidate = getattr(value, name, _MISSING)
        if candidate is not _MISSING:
            result[name] = candidate
    return result


def _model_row(model_results: object, topic_key: str) -> Mapping[str, Any]:
    if model_results is None:
        return MappingProxyType({})
    row: object = _MISSING
    if isinstance(model_results, Mapping):
        row = model_results.get(topic_key, _MISSING)
    elif not isinstance(model_results, (str, bytes)):
        for candidate in model_results:
            candidate_key = _optional_field(candidate, "topic_key", _MISSING)
            if candidate_key is _MISSING:
                candidate_key = _optional_field(candidate, "key", _MISSING)
            if candidate_key == topic_key:
                row = candidate
                break
    if row is _MISSING or row is None:
        return MappingProxyType({})
    if not isinstance(row, Mapping) and hasattr(row, "result"):
        row = getattr(row, "result")
    data = _mapping_like(row)
    nested = data.get("result")
    if isinstance(nested, Mapping) and not any(key in data for key in ("title", "intro", "slug", "slug_candidate", "page_slug")):
        data = dict(nested)
    intro_result = data.get("intro_result")
    if "intro" not in data and intro_result is not None:
        rendered = getattr(intro_result, "rendered_text", _MISSING)
        if rendered is _MISSING and isinstance(intro_result, Mapping):
            rendered = intro_result.get("rendered_text", _MISSING)
        if rendered is not _MISSING:
            data["intro"] = rendered
    return MappingProxyType(data)


def _candidate_slug(model: Mapping[str, Any], model_title: str | None) -> str:
    for field in ("slug", "slug_candidate", "page_slug"):
        value = model.get(field)
        if value is not None:
            if not isinstance(value, str):
                raise TypeError(f"model {field} must be a string")
            result = gbrain_slug(value)
            if result:
                return result
    if model_title:
        result = gbrain_slug(model_title)
        if result:
            return result
    return ""


def _filename_slug(source_path: str) -> str:
    filename = PurePosixPath(source_path).name
    filename = _MD_SUFFIX_RE.sub("", filename)
    return gbrain_slug(filename)


def _slug_with_fallback(model: Mapping[str, Any], model_title: str | None, members: Sequence[_SourceBlock]) -> str:
    primary = _candidate_slug(model, model_title)
    if primary:
        return primary
    for member in members:
        fallback = _filename_slug(member.source_path)
        if fallback:
            return fallback
    raise ValueError("slug_fallback_exhausted: no ASCII model or source filename segment")


def _claim_items(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    fact_claims = getattr(value, "fact_claims", _MISSING)
    if fact_claims is not _MISSING:
        return tuple(fact_claims)
    if isinstance(value, Mapping):
        nested = value.get("claims", _MISSING)
        if nested is not _MISSING and not any(key in value for key in ("text", "claim_id")):
            return tuple(nested)
        return (value,)
    if isinstance(value, (str, bytes)):
        raise TypeError("claims must be an iterable of claim records")
    return tuple(value)


def _claims_for(claims_by_topic: object, topic_key: str) -> tuple[object, ...]:
    if claims_by_topic is None:
        return ()
    if isinstance(claims_by_topic, Mapping):
        return _claim_items(claims_by_topic.get(topic_key))
    return ()


def _claim_status(claim: object) -> object:
    return _read_field(claim, "status", "sourced")


def _claim_text(claim: object) -> str:
    text = _read_field(claim, "text")
    if isinstance(text, bytes):
        return text.decode("utf-8", "surrogateescape")
    if not isinstance(text, str):
        raise TypeError("claim.text must be a string")
    return text


def _claim_source_path(claim: object) -> str:
    value = _read_field(claim, "source_path")
    return _coerce_source_path(value)


def _claim_sort_key(claim: object) -> tuple[object, ...]:
    return (
        _claim_source_path(claim),
        int(_read_field(claim, "span_start", _read_field(claim, "char_start", 0))),
        str(_read_field(claim, "claim_id", "")),
        _claim_text(claim),
    )


def _claim_span(claim: object) -> tuple[int, int] | None:
    start = _optional_field(claim, "span_start", _MISSING)
    if start is _MISSING:
        start = _optional_field(claim, "char_start", _MISSING)
    end = _optional_field(claim, "span_end", _MISSING)
    if end is _MISSING:
        end = _optional_field(claim, "char_end", _MISSING)
    if start is _MISSING or end is _MISSING or start is None or end is None:
        return None
    return int(start), int(end)


def _claim_anchor(
    claim: object,
    members: Sequence[_SourceBlock],
) -> tuple[_SourceBlock, int, int] | None:
    """Resolve a claim to one concrete block and exact local text span."""

    source_path = _claim_source_path(claim)
    claim_text = _claim_text(claim)
    declared_hash = _optional_field(claim, "content_hash", _MISSING)
    if declared_hash is not _MISSING and declared_hash is not None and not isinstance(declared_hash, str):
        raise TypeError("claim.content_hash must be a string")
    span = _claim_span(claim)
    claim_line_start = _optional_field(claim, "line_start", _MISSING)
    claim_line_end = _optional_field(claim, "line_end", _MISSING)
    declared_block_id = _optional_field(claim, "source_block_id", _MISSING)
    candidates = [member for member in members if member.source_path == source_path]
    if declared_block_id not in {_MISSING, None, ""}:
        candidates = [member for member in candidates if member.block_id == declared_block_id]
    for member in candidates:
        if declared_hash not in {_MISSING, None, ""} and member.content_hash != declared_hash:
            continue
        if claim_line_start not in {_MISSING, None} and int(claim_line_start) < member.line_start:
            continue
        if claim_line_end not in {_MISSING, None} and int(claim_line_end) > member.line_end:
            continue
        if span is None:
            start = member.text.find(claim_text)
            if start < 0:
                continue
            end = start + len(claim_text)
        else:
            start, end = span
            if start < 0 or end <= start or end > len(member.text):
                continue
            if member.text[start:end] != claim_text:
                continue
        return member, start, end
    return None


def _attribution(source_path: str, heading_path: Iterable[str] = ()) -> str:
    filename = PurePosixPath(source_path).name
    titles = tuple(str(item).strip() for item in heading_path if str(item).strip())
    if titles:
        return f"来源：{filename} — {' > '.join(titles)}"
    return f"来源：{filename}"


def _append_attribution(raw_text: str, attribution: str) -> str:
    separator = "" if raw_text.endswith(("\n", "\r")) else "\n"
    return f"{raw_text}{separator}{attribution}"


def _block_attribution(block: _SourceBlock) -> str:
    return _attribution(block.source_path, block.heading_path)


def _intro_source_block(claim: object, members: Sequence[_SourceBlock]) -> _SourceBlock | None:
    source_path = _claim_source_path(claim)
    declared_hash = _optional_field(claim, "content_hash", _MISSING)
    declared_block_id = _optional_field(claim, "source_block_id", _MISSING)
    line_start = _optional_field(claim, "line_start", _MISSING)
    line_end = _optional_field(claim, "line_end", _MISSING)
    candidates = [member for member in members if member.source_path == source_path]
    if declared_block_id not in {_MISSING, None, ""}:
        candidates = [member for member in candidates if member.block_id == declared_block_id]
    if declared_hash not in {_MISSING, None, ""}:
        candidates = [member for member in candidates if member.content_hash == declared_hash]
    if line_start not in {_MISSING, None}:
        candidates = [member for member in candidates if int(line_start) >= member.line_start]
    if line_end not in {_MISSING, None}:
        candidates = [member for member in candidates if int(line_end) <= member.line_end]
    return candidates[0] if len(candidates) == 1 else None


def _intro_attributions(claims: Sequence[object], members: Sequence[_SourceBlock]) -> tuple[str, ...]:
    result: list[str] = []
    for claim in claims:
        if _claim_status(claim) != "sourced":
            continue
        if _optional_field(claim, "claim_kind", "narrative") != "intro":
            continue
        source_block = _intro_source_block(claim, members)
        if source_block is None:
            continue
        attribution = _block_attribution(source_block)
        if attribution not in result:
            result.append(attribution)
    return tuple(result)


def _reference_unit(block: _SourceBlock, anchor_id: str) -> _Unit:
    if block.kind == "attachment_refs":
        raw_text = f"> {ATTACHMENT_MARKER}\n{block.text}"
    else:
        raw_text = block.text
    rendered = _append_attribution(raw_text, _block_attribution(block))
    return _Unit(
        rendered,
        reference_block=True,
        source_block_id=block.block_id,
        anchor_ids=(anchor_id,),
    )


def _claim_heading_path(claim: object, by_source: Mapping[str, _SourceBlock]) -> tuple[str, ...]:
    declared = _optional_field(claim, "heading_path", _MISSING)
    if declared is not _MISSING:
        if isinstance(declared, str):
            return (declared,)
        return tuple(str(item) for item in declared)
    block = by_source.get(_claim_source_path(claim))
    return block.heading_path if block is not None else ()


def _narrative_units(
    members: Sequence[_SourceBlock],
    claims: Sequence[object],
    block_anchor_ids: Mapping[str, str],
) -> tuple[_Unit, tuple[str, ...]]:
    sourced_claims = tuple(
        sorted(
            (
                claim
                for claim in claims
                if _claim_status(claim) == "sourced"
                and _optional_field(claim, "claim_kind", "narrative") == "narrative"
            ),
            key=_claim_sort_key,
        )
    )
    anchored: list[tuple[object, _SourceBlock, int, int]] = []
    unanchored_sources: set[str] = set()
    for claim in sourced_claims:
        anchor = _claim_anchor(claim, members)
        if anchor is None:
            # Keep the original source block visible below, but do not render
            # an unbound claim under a guessed heading or page location.
            unanchored_sources.add(_claim_source_path(claim))
            continue
        anchored.append((claim, *anchor))

    claim_units: list[tuple[tuple[object, ...], _Unit]] = []
    narrative_texts: list[str] = []
    narrative_members = tuple(member for member in members if member.kind == "narrative")
    for block_index, block in enumerate(narrative_members):
        block_anchor = block_anchor_ids[block.block_id]
        block_claims = [item for item in anchored if item[1] is block]
        if block.source_path in unanchored_sources:
            block_claims = []
        block_claims.sort(key=lambda item: (item[2], item[3], _claim_sort_key(item[0])))
        if not block_claims:
            narrative_texts.append(block.text)
            claim_units.append(
                (
                    (block.source_path, block.line_start, block_index, 0),
                    _Unit(
                        _append_attribution(block.text, _block_attribution(block)),
                        source_block_id=block.block_id,
                        anchor_ids=(block_anchor, "narrative"),
                    ),
                )
            )
            continue

        cursor = 0
        valid = True
        anchor_pending = True
        pieces: list[tuple[int, _Unit]] = []
        for claim, _, start, end in block_claims:
            if start < cursor:
                valid = False
                break
            gap = block.text[cursor:start]
            if gap:
                pieces.append(
                    (
                        cursor,
                        _Unit(
                            _append_attribution(gap, _block_attribution(block)),
                            source_block_id=block.block_id,
                            anchor_ids=(block_anchor, "narrative") if anchor_pending else ("narrative",),
                        ),
                    )
                )
                anchor_pending = False
            claim_text = _claim_text(claim)
            pieces.append(
                (
                    start,
                    _Unit(
                        _append_attribution(claim_text, _block_attribution(block)),
                        source_block_id=block.block_id,
                        claim_id=str(_read_field(claim, "claim_id")),
                        anchor_ids=(block_anchor, "narrative") if anchor_pending else ("narrative",),
                    ),
                )
            )
            anchor_pending = False
            cursor = end
        tail = block.text[cursor:]
        if valid and tail:
            pieces.append(
                (
                    cursor,
                    _Unit(
                        _append_attribution(tail, _block_attribution(block)),
                        source_block_id=block.block_id,
                        anchor_ids=(block_anchor, "narrative") if anchor_pending else ("narrative",),
                    ),
                )
            )
            anchor_pending = False
        if not valid:
            narrative_texts.append(block.text)
            claim_units.append(
                (
                    (block.source_path, block.line_start, block_index, 0),
                    _Unit(
                        _append_attribution(block.text, _block_attribution(block)),
                        source_block_id=block.block_id,
                        anchor_ids=(block_anchor, "narrative"),
                    ),
                )
            )
            continue
        narrative_texts.extend(block.text[start:end] for start, end in ((0, len(block.text)),))
        for offset, unit in pieces:
            claim_units.append(((block.source_path, block.line_start, block_index, offset), unit))

    claim_units.sort(key=lambda item: item[0])
    return tuple(unit for _, unit in claim_units), tuple(narrative_texts)


def _line_count(text: str) -> int:
    return len(text.splitlines())


def _render_unit(unit: _Unit, seen_anchors: set[str] | None = None) -> str:
    seen = seen_anchors if seen_anchors is not None else set()
    fresh = [anchor for anchor in unit.anchor_ids if anchor not in seen]
    seen.update(fresh)
    if not fresh:
        return unit.text
    marker = "\n".join(f'<a id="{anchor}"></a>' for anchor in fresh)
    return f"{marker}\n{unit.text}" if unit.text else marker


def _join_units(units: Sequence[str]) -> str:
    return "\n\n".join(units)


def _frontmatter_value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(_frontmatter_value(item) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _render_frontmatter(frontmatter: Mapping[str, Any]) -> str:
    if tuple(frontmatter) != PAGE_FRONTMATTER_FIELDS:
        raise ValueError("frontmatter must contain the exact Task7 16-field order")
    rows = ["---"]
    rows.extend(f"{field}: {_frontmatter_value(frontmatter[field])}" for field in PAGE_FRONTMATTER_FIELDS)
    rows.append("---")
    return "\n".join(rows)


def _standard_body_units(
    draft: _PageDraft,
    claims: Sequence[object],
    target_paths: Mapping[str, str],
    intro_text: str | None,
) -> tuple[tuple[_Unit, ...], tuple[_Unit, ...]]:
    block_anchor_ids = {
        member.block_id: f"block-{index}"
        for index, member in enumerate(draft.members, start=1)
    }
    reference_units: list[_Unit] = []
    oversized_units: list[_Unit] = []
    for block in draft.members:
        if block.kind == "narrative":
            continue
        unit = _reference_unit(block, block_anchor_ids[block.block_id])
        if _line_count(_render_unit(unit)) > MAX_NARRATIVE_LINES:
            oversized_units.append(unit)
        else:
            reference_units.append(unit)

    narrative_units, narrative_texts = _narrative_units(
        draft.members,
        claims,
        block_anchor_ids,
    )
    units: list[_Unit] = []
    if intro_text:
        intro_unit = f"## 导读\n{intro_text}"
        for attribution in _intro_attributions(claims, draft.members):
            intro_unit = _append_attribution(intro_unit, attribution)
        units.append(_Unit(intro_unit, anchor_ids=("intro",)))
    if reference_units:
        units.append(_Unit("## 参考内容"))
        units.extend(reference_units)
    if narrative_units:
        units.append(_Unit("## 叙述内容", anchor_ids=("narrative",)))
        units.extend(narrative_units)

    related: list[tuple[str, str, str]] = []
    searchable = "\n".join(narrative_texts)
    for other_key, other_path in sorted(target_paths.items()):
        if other_key == draft.topic_key:
            continue
        other_title = target_paths.get(f"{other_key}::title")
        if other_title and other_title in searchable:
            related.append((other_key, other_path, other_title))
    if related:
        units.append(_Unit("## 相关页面"))
        units.extend(
            _Unit(f"- [[{path.removesuffix('.md')}|{title}]]")
            for _, path, title in related
        )
    return tuple(units), tuple(oversized_units)


def _part_heading(title: str, part_number: int) -> str:
    if part_number == 1:
        return f"# {title}"
    return f"# {title}（第 {part_number} 部分）"


def _unit_texts(units: Sequence[_Unit]) -> tuple[str, ...]:
    seen_anchors: set[str] = set()
    return tuple(_render_unit(unit, seen_anchors) for unit in units)


def _partitioned_body(units: Sequence[_Unit]) -> _PartitionedBody:
    block_ids: list[str] = []
    claim_ids: list[str] = []
    anchor_ids: list[str] = []
    for unit in units:
        if unit.source_block_id and unit.source_block_id not in block_ids:
            block_ids.append(unit.source_block_id)
        if unit.claim_id and unit.claim_id not in claim_ids:
            claim_ids.append(unit.claim_id)
        for anchor in unit.anchor_ids:
            if anchor not in anchor_ids:
                anchor_ids.append(anchor)
    return _PartitionedBody(
        text=_join_units(_unit_texts(units)),
        source_block_ids=tuple(block_ids),
        claim_ids=tuple(claim_ids),
        anchor_ids=tuple(anchor_ids),
    )


def _partition_standard_units(title: str, units: Sequence[_Unit]) -> tuple[_PartitionedBody, ...]:
    if not units:
        return (_PartitionedBody(_part_heading(title, 1)),)
    parts: list[_PartitionedBody] = []
    current: list[_Unit] = [_Unit(_part_heading(title, 1))]
    for unit in units:
        if _line_count(_render_unit(unit)) > MAX_NARRATIVE_LINES:
            raise ValueError("non-reference page unit exceeds 300 lines")
        candidate = _join_units(_unit_texts((*current, unit)))
        if _line_count(candidate) > MAX_NARRATIVE_LINES:
            if len(current) == 1:
                raise ValueError("page unit cannot fit within 300 lines without splitting a claim")
            parts.append(_partitioned_body(current))
            current = [_Unit(_part_heading(title, len(parts) + 1)), unit]
            if _line_count(_join_units(_unit_texts(current))) > MAX_NARRATIVE_LINES:
                raise ValueError("page unit cannot fit within 300 lines without splitting a claim")
        else:
            current.append(unit)
    parts.append(_partitioned_body(current))
    return tuple(parts)


def _source_dates(members: Sequence[_SourceBlock]) -> tuple[str, str]:
    values = [member.source_mtime for member in members]
    if not values or any(not isinstance(value, date) for value in values):
        raise ValueError("all page sources must have a normalized mtime")
    return min(values).isoformat(), max(values).isoformat()


def _build_frontmatter(
    draft: _PageDraft,
    source_root_name: str,
) -> Mapping[str, Any]:
    created, updated = _source_dates(draft.members)
    sources = sorted({member.source_path for member in draft.members})
    source_value = "; ".join(f"{source_root_name}/{path}" for path in sources)
    values: dict[str, Any] = {
        "title": draft.title,
        "type": "reference",
        "page_model": "derived",
        "scope": "company",
        "product": draft.product,
        "section": draft.section,
        "module": draft.section,
        "tier": 2,
        "trust": "medium",
        "source_status": "compiled",
        "quality_status": "formal",
        "created": created,
        "updated": updated,
        "generated_by": "knowledge_digest_semantic_compiler.py",
        "tags": ["company", draft.product, draft.section],
        "source": source_value,
    }
    return MappingProxyType(values)


def _make_part(
    draft: _PageDraft,
    frontmatter: Mapping[str, Any],
    body: str,
    part_number: int,
    *,
    oversized: bool = False,
    source_block_ids: tuple[str, ...] = (),
    claim_ids: tuple[str, ...] = (),
    anchor_ids: tuple[str, ...] = (),
) -> PagePart:
    suffix = "" if part_number == 1 else f".part-{part_number:03d}"
    relative_path = f"products/{draft.product}/{draft.section}/{draft.slug}{suffix}.md"
    rendered_body = body
    if oversized:
        rendered_body = _join_units(
            (
                _part_heading(f"{draft.title} 参考附录", part_number),
                "oversized_reference_block: true",
                body,
            )
        )
    else:
        rendered_body = body
    text = _render_frontmatter(frontmatter) + "\n\n" + rendered_body + "\n"
    return PagePart(
        part_number=part_number,
        relative_path=relative_path,
        body=rendered_body,
        text=text,
        oversized_reference_block=oversized,
        source_block_ids=source_block_ids,
        claim_ids=claim_ids,
        anchor_ids=anchor_ids,
    )


def _drafts(
    groups: Iterable[object],
    model_results: object,
    source_mtimes: Mapping[object, object] | None,
) -> tuple[_PageDraft, ...]:
    raw: list[tuple[str, str, str, str, tuple[_SourceBlock, ...], Mapping[str, Any], str, str]] = []
    for group in groups:
        topic_key, product, group_title, module_anchor, members = _coerce_group(group, source_mtimes)
        model = _model_row(model_results, topic_key)
        model_title = model.get("title")
        if model_title is not None and not isinstance(model_title, str):
            raise TypeError("model title must be a string")
        title = model_title.strip() if isinstance(model_title, str) and model_title.strip() else group_title.strip()
        base_slug = _slug_with_fallback(model, title if model_title else None, members)
        product_slug = gbrain_slug(product)
        section_slug = gbrain_slug(module_anchor)
        if not product_slug or not section_slug:
            raise ValueError(f"product/module slug fallback exhausted for {topic_key!r}")
        raw.append((topic_key, group_title, product_slug, section_slug, members, model, title, base_slug))

    by_base: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in raw:
        by_base[(row[2], row[3], row[-1])].append(row[0])
    suffixes: dict[tuple[tuple[str, str, str], str], str] = {}
    reserved_bases = set(by_base)
    used_slugs: set[tuple[str, str, str]] = set()
    for product, section, base in sorted(by_base):
        keys = by_base[(product, section, base)]
        for index, key in enumerate(sorted(keys)):
            if index == 0 and (product, section, base) not in used_slugs:
                candidate = base
            else:
                ordinal = 2
                candidate = f"{base}-{ordinal}"
                while (product, section, candidate) in used_slugs or (product, section, candidate) in reserved_bases:
                    ordinal += 1
                    candidate = f"{base}-{ordinal}"
            used_slugs.add((product, section, candidate))
            suffixes[((product, section, base), key)] = candidate.removeprefix(base)

    drafts = [
        _PageDraft(
            topic_key=topic_key,
            group_title=group_title,
            product=product_slug,
            section=section_slug,
            members=members,
            model=model,
            title=title,
            base_slug=base_slug,
            slug=base_slug + suffixes[((product_slug, section_slug, base_slug), topic_key)],
        )
        for topic_key, group_title, product_slug, section_slug, members, model, title, base_slug in raw
    ]
    return tuple(sorted(drafts, key=lambda draft: draft.topic_key))


def render_pages(
    groups: Iterable[object],
    *,
    model_results: object = None,
    claims_by_topic: object = None,
    source_root_name: str = "raw",
    source_mtimes: Mapping[object, object] | None = None,
    intro_texts: Mapping[str, str] | None = None,
) -> tuple[RenderedPage, ...]:
    """Render deterministic pages from TopicGroups, claims, and cached model rows.

    ``source_mtimes`` is required for every source unless the block itself
    carries ``source_mtime``/``mtime``.  Requiring that fact prevents the page
    layer from inventing runtime dates.  The function returns pages in topic-key
    order, while each page's physical parts use deterministic paths.
    """

    if not isinstance(source_root_name, str) or not source_root_name.strip() or "/" in source_root_name or "\\" in source_root_name:
        raise ValueError("source_root_name must be one non-empty directory name")
    drafts = _drafts(groups, model_results, source_mtimes)
    if not drafts:
        return ()

    target_paths: dict[str, str] = {}
    for draft in drafts:
        target_paths[draft.topic_key] = f"products/{draft.product}/{draft.section}/{draft.slug}.md"
        target_paths[f"{draft.topic_key}::title"] = draft.title

    rendered: list[RenderedPage] = []
    for draft in drafts:
        claims = _claims_for(claims_by_topic, draft.topic_key)
        intro_text = None if intro_texts is None else intro_texts.get(draft.topic_key)
        units, oversized = _standard_body_units(draft, claims, target_paths, intro_text)
        standard_bodies = _partition_standard_units(draft.title, units)
        frontmatter = _build_frontmatter(draft, source_root_name.strip())
        parts: list[PagePart] = [
            _make_part(
                draft,
                frontmatter,
                body.text,
                index,
                source_block_ids=body.source_block_ids,
                claim_ids=body.claim_ids,
                anchor_ids=body.anchor_ids,
            )
            for index, body in enumerate(standard_bodies, start=1)
        ]
        for unit in oversized:
            rendered_unit = _render_unit(unit)
            parts.append(
                _make_part(
                    draft,
                    frontmatter,
                    rendered_unit,
                    len(parts) + 1,
                    oversized=True,
                    source_block_ids=(unit.source_block_id,) if unit.source_block_id else (),
                    claim_ids=(unit.claim_id,) if unit.claim_id else (),
                    anchor_ids=unit.anchor_ids,
                )
            )
        first_path = parts[0].relative_path if parts else target_paths[draft.topic_key]
        rendered.append(
            RenderedPage(
                topic_key=draft.topic_key,
                title=draft.title,
                slug=draft.slug,
                relative_path=first_path,
                frontmatter=frontmatter,
                parts=tuple(parts),
            )
        )
    return tuple(rendered)


__all__ = [
    "ATTACHMENT_MARKER",
    "MAX_NARRATIVE_LINES",
    "PAGE_FRONTMATTER_FIELDS",
    "PagePart",
    "RenderedPage",
    "gbrain_slug",
    "render_pages",
]
