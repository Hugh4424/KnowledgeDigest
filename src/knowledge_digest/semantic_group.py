"""Deterministic topic grouping for the Task7 semantic compiler.

Grouping is deliberately mechanical.  A model may provide suspected-synonym
records to the caller, but those records are never consulted while deciding
which blocks belong to a page.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from types import MappingProxyType
import unicodedata
from typing import Any, Iterable, Mapping

from .semantic_split import Block


_DEFAULT_TOPIC_MAP: dict[str, Any] = {
    "topic_aliases": {},
    "audit_only_sources": [],
}
_MISSING = object()
_WHITESPACE_RE = re.compile(r"\s+")
_SLUG_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class TopicGroup:
    """One deterministic page membership set."""

    key: str
    product: str
    title: str
    module_anchor: str
    members: tuple[Block, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "product": self.product,
            "title": self.title,
            "module_anchor": self.module_anchor,
            "members": [member.as_dict() for member in self.members],
        }


@dataclass(frozen=True)
class GroupingResult:
    """Groups plus report-only inputs consumed by later audit stages."""

    groups: tuple[TopicGroup, ...]
    suggestions: tuple[Mapping[str, Any], ...] = ()
    audit_only_sources: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "groups": [group.as_dict() for group in self.groups],
            "suggestions": [dict(item) for item in self.suggestions],
            "audit_only_sources": list(self.audit_only_sources),
        }


def normalize_topic_title(value: str) -> str:
    """Apply the four FR-GRP-001 title normalization operations."""

    if not isinstance(value, str):
        raise TypeError("topic title must be a string")
    normalized = unicodedata.normalize("NFC", value).strip()
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    # The contract says ASCII case normalization, not Unicode case folding.
    return "".join(
        chr(ord(character) + 32)
        if "A" <= character <= "Z"
        else character
        for character in normalized
    )


def _slug_component(value: str, fallback: str) -> str:
    """Create the ASCII, path-safe slug used for product/module components."""

    normalized = unicodedata.normalize("NFKC", value).strip()
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = _SLUG_SEPARATOR_RE.sub("-", ascii_value).strip("-")
    if slug:
        return slug
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{fallback}-{digest}"


def product_slug_from_source_path(source_path: str) -> str:
    """Return the slug of the source file's top-level directory."""

    if not isinstance(source_path, str) or not source_path.strip():
        raise ValueError("source_path must be a non-empty string")
    path = PurePosixPath(source_path.replace("\\", "/"))
    if path.is_absolute():
        raise ValueError(f"source_path must be relative: {source_path!r}")
    parts = tuple(part for part in path.parts if part not in {"", "."})
    if not parts or parts[0] == "..":
        raise ValueError(f"source_path must be relative and non-empty: {source_path!r}")
    return _slug_component(parts[0], "product")


def _raw_product_name(source_path: str) -> str:
    """Return the canonical raw top-level name used for collision detection."""

    if not isinstance(source_path, str) or not source_path.strip():
        raise ValueError("source_path must be a non-empty string")
    path = PurePosixPath(source_path.replace("\\", "/"))
    if path.is_absolute():
        raise ValueError(f"source_path must be relative: {source_path!r}")
    parts = tuple(part for part in path.parts if part not in {"", "."})
    if not parts or parts[0] == "..":
        raise ValueError(f"source_path must be relative and non-empty: {source_path!r}")
    value = unicodedata.normalize("NFKC", parts[0]).strip()
    return "".join(
        chr(ord(character) + 32)
        if "A" <= character <= "Z"
        else character
        for character in value
    )


def _product_slugs(source_paths: Iterable[str]) -> dict[str, str]:
    """Build collision-safe product slugs without changing ordinary names."""

    raw_names = {_raw_product_name(path) for path in source_paths}
    by_slug: dict[str, list[str]] = {}
    for raw_name in raw_names:
        by_slug.setdefault(_slug_component(raw_name, "product"), []).append(raw_name)
    result: dict[str, str] = {}
    reserved_bases = set(by_slug)
    used_slugs: set[str] = set()

    # Keep every non-colliding product's ordinary slug first.  Generated
    # collision suffixes must never consume one of those ordinary names.
    for base_slug, names in sorted(by_slug.items()):
        if len(names) != 1:
            continue
        raw_name = names[0]
        result[raw_name] = base_slug
        used_slugs.add(base_slug)

    for base_slug, names in sorted(by_slug.items()):
        if len(names) == 1:
            continue
        for raw_name in sorted(names):
            suffix = hashlib.sha256(raw_name.encode("utf-8")).hexdigest()[:10]
            candidate = f"{base_slug}-p{suffix}"
            ordinal = 2
            while candidate in reserved_bases or candidate in used_slugs:
                candidate = f"{base_slug}-p{suffix}-{ordinal}"
                ordinal += 1
            result[raw_name] = candidate
            used_slugs.add(candidate)
    return result


def _read_field(value: object, name: str, default: object = _MISSING) -> object:
    if isinstance(value, Mapping):
        result = value.get(name, default)
    else:
        result = getattr(value, name, default)
    if result is _MISSING:
        raise ValueError(f"block is missing {name!r}")
    return result


def _coerce_block(value: object) -> Block:
    """Accept the frozen Block seam or a mapping-shaped test/IO record."""

    if isinstance(value, Block):
        return value
    source_path = _read_field(value, "source_path")
    block_id = _read_field(value, "block_id")
    text = _read_field(value, "text", "")
    if not isinstance(source_path, str) or not source_path:
        raise ValueError("block.source_path must be a non-empty string")
    if not isinstance(block_id, str) or not block_id:
        raise ValueError("block.block_id must be a non-empty string")
    if not isinstance(text, str):
        raise TypeError("block.text must be a string")
    heading_path = _read_field(value, "heading_path", ())
    if isinstance(heading_path, str):
        heading_path = (heading_path,)
    else:
        heading_path = tuple(str(item) for item in heading_path)
    content_hash = _read_field(value, "content_hash", "")
    if not isinstance(content_hash, str):
        raise TypeError("block.content_hash must be a string")
    line_start = int(_read_field(value, "line_start", 1))
    line_end = int(_read_field(value, "line_end", line_start))
    if line_start < 1 or line_end < line_start:
        raise ValueError("block line range is invalid")
    kind = str(_read_field(value, "kind", "narrative"))
    return Block(
        source_path=source_path,
        block_id=block_id,
        content_hash=content_hash
        or hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest(),
        kind=kind,
        line_start=line_start,
        line_end=line_end,
        text=text,
        heading_path=heading_path,
    )


def _topic_title(value: object, block: Block) -> str:
    explicit = _read_field(value, "title", None)
    if explicit is not None:
        if not isinstance(explicit, str):
            raise TypeError("block.title must be a string")
        normalized = normalize_topic_title(explicit)
        if normalized:
            return normalized
    for heading in reversed(block.heading_path):
        normalized = normalize_topic_title(heading)
        if normalized:
            return normalized
    stem = PurePosixPath(block.source_path).stem
    return normalize_topic_title(stem) or "untitled"


def _h2_title(block: Block) -> str | None:
    # semantic_split.heading_path is a level-indexed tuple; an H2 title lives
    # at index 1 even when the source skipped H1 (the splitter leaves a blank
    # placeholder).  Compare this normalized title before slugging so two
    # distinct titles cannot collapse to one module anchor.
    if len(block.heading_path) < 2:
        return None
    candidate = block.heading_path[1]
    normalized = normalize_topic_title(candidate)
    return normalized or None


def _common_module_anchor(members: Iterable[Block]) -> str:
    title = _common_module_title(members)
    if title is None:
        return "_general"
    return _slug_component(title, "module")


def _common_module_title(members: Iterable[Block]) -> str | None:
    titles = [_h2_title(member) for member in members]
    if not titles or any(title is None for title in titles):
        return None
    unique_titles = {title for title in titles if title is not None}
    if len(unique_titles) != 1:
        return None
    return next(iter(unique_titles))


def _normalize_topic_map(topic_map: Mapping[str, Any] | None) -> tuple[dict[str, str], tuple[str, ...]]:
    if not topic_map:
        return {}, ()
    raw_aliases = topic_map.get("topic_aliases", {})
    raw_audit = topic_map.get("audit_only_sources", [])
    if raw_aliases is None:
        raw_aliases = {}
    if raw_audit is None:
        raw_audit = []
    if not isinstance(raw_aliases, Mapping):
        raise ValueError("topic_map.topic_aliases must be an object")
    if (
        isinstance(raw_audit, (str, bytes, Mapping))
        or not isinstance(raw_audit, Iterable)
    ):
        raise ValueError("topic_map.audit_only_sources must be an array")
    aliases: dict[str, str] = {}
    for raw_alias, raw_canonical in raw_aliases.items():
        if not isinstance(raw_alias, str) or not isinstance(raw_canonical, str):
            raise ValueError("topic aliases must map strings to strings")
        alias = normalize_topic_title(raw_alias)
        canonical = normalize_topic_title(raw_canonical)
        if not alias or not canonical:
            raise ValueError("topic aliases cannot contain empty titles")
        aliases[alias] = canonical
    audit_sources: set[str] = set()
    for source in raw_audit:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("audit_only_sources must contain non-empty strings")
        audit_sources.add(source)
    return aliases, tuple(sorted(audit_sources))


def _resolve_alias(title: str, aliases: Mapping[str, str]) -> str:
    current = title
    seen: set[str] = set()
    while current in aliases:
        if current in seen:
            raise ValueError(f"topic alias cycle detected at {current!r}")
        seen.add(current)
        current = aliases[current]
    return current


def _suggestion_copy(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("model_suggestions entries must be objects")
    copied = dict(value)
    # A read-only view prevents a caller from mutating the result and making a
    # later audit disagree with the grouping decision.
    return MappingProxyType(copied)


def load_topic_map(path: str | Path) -> dict[str, Any]:
    """Read the human-edited map; missing or empty files mean no mappings."""

    target = Path(path)
    if not target.exists() or target.stat().st_size == 0:
        return {"topic_aliases": {}, "audit_only_sources": []}
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read topic map {target}: {error}") from error
    if not isinstance(raw, Mapping):
        raise ValueError("topic map root must be a JSON object")
    aliases = raw.get("topic_aliases", {})
    audit_sources = raw.get("audit_only_sources", [])
    _normalize_topic_map({"topic_aliases": aliases, "audit_only_sources": audit_sources})
    return {
        "topic_aliases": dict(aliases),
        "audit_only_sources": list(audit_sources),
    }


def group_topics(
    blocks: Iterable[object],
    *,
    topic_map: Mapping[str, Any] | str | Path | None = None,
    model_suggestions: Iterable[Mapping[str, Any]] = (),
) -> GroupingResult:
    """Group blocks deterministically within product scope.

    ``topic_map`` is a deterministic human-edited input.  ``model_suggestions``
    is copied and exposed only as report data; it is intentionally absent from
    the grouping key calculation.
    """

    if isinstance(topic_map, (str, Path)):
        topic_map = load_topic_map(topic_map)
    if topic_map is not None and not isinstance(topic_map, Mapping):
        raise TypeError("topic_map must be a mapping or JSON path")
    aliases, audit_only_sources = _normalize_topic_map(topic_map)

    prepared_blocks: list[tuple[object, Block]] = []
    seen_ids: set[tuple[str, str]] = set()
    for raw_block in blocks:
        block = _coerce_block(raw_block)
        identity = (block.source_path, block.block_id)
        if identity in seen_ids:
            raise ValueError(f"duplicate block identity: {block.source_path}:{block.block_id}")
        seen_ids.add(identity)
        prepared_blocks.append((raw_block, block))

    product_slugs = _product_slugs(block.source_path for _, block in prepared_blocks)
    grouped: dict[str, dict[str, Any]] = {}
    for raw_block, block in prepared_blocks:
        title = _resolve_alias(_topic_title(raw_block, block), aliases)
        product = product_slugs[_raw_product_name(block.source_path)]
        key = f"{product}:{title}"
        bucket = grouped.setdefault(
            key,
            {"product": product, "title": title, "members": []},
        )
        bucket["members"].append(block)

    group_rows: list[tuple[str, str, str, tuple[Block, ...], str | None, str]] = []
    for key in sorted(grouped):
        bucket = grouped[key]
        members = tuple(
            sorted(
                bucket["members"],
                key=lambda member: (
                    member.source_path,
                    member.line_start,
                    member.line_end,
                    member.block_id,
                    member.content_hash,
                ),
            )
        )
        module_title = _common_module_title(members)
        base_module = _common_module_anchor(members)
        group_rows.append((key, bucket["product"], bucket["title"], members, module_title, base_module))

    module_names: dict[tuple[str, str], set[str]] = defaultdict(set)
    for _, product, _, _, module_title, base_module in group_rows:
        if module_title is not None:
            module_names[(product, base_module)].add(module_title)
    module_anchors: dict[tuple[str, str, str], str] = {}
    for (product, base_module), titles in sorted(module_names.items()):
        if len(titles) == 1:
            continue
        for title in sorted(titles):
            digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]
            module_anchors[(product, base_module, title)] = f"{base_module}-m{digest}"

    groups: list[TopicGroup] = []
    for key, product, title, members, module_title, base_module in group_rows:
        module_anchor = module_anchors.get((product, base_module, module_title), base_module) if module_title is not None else base_module
        groups.append(
            TopicGroup(
                key=key,
                product=product,
                title=title,
                module_anchor=module_anchor,
                members=members,
            )
        )

    copied_suggestions = tuple(
        sorted(
            (_suggestion_copy(item) for item in model_suggestions),
            key=lambda item: json.dumps(dict(item), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
    )
    return GroupingResult(
        groups=tuple(groups),
        suggestions=copied_suggestions,
        audit_only_sources=audit_only_sources,
    )


__all__ = [
    "GroupingResult",
    "TopicGroup",
    "group_topics",
    "load_topic_map",
    "normalize_topic_title",
    "product_slug_from_source_path",
]
