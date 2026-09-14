"""Machine-readable audit facts for the Task7 semantic compiler.

The audit layer consumes facts already produced by the split, claim, cache, and
page layers.  It does not render page content and it never infers a source
status from a missing output alone.  ``build_audit`` is pure; ``write_audit``
adds the small filesystem adapter needed by the later batch compiler.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence


SOURCE_STATUSES = frozenset({"ready", "known_empty", "duplicate_alias", "audit_only", "blocked"})
CLAIM_STATUSES = frozenset({"sourced", "原文未明确"})
CLAIM_KINDS = frozenset({"narrative", "intro"})
REFERENCE_KINDS = frozenset({"table", "list", "code", "error_text", "attachment_refs"})
ZERO_REASONS = frozenset(
    {
        "cache_hit",
        "no_provider_call_yet",
        "provider_unavailable",
        "provider_usage_unavailable",
        "provider_call_observed",
        "reconciliation_failed",
    }
)
# A model cache miss with an unavailable provider is an explicit, page-local
# degradation.  The reader page and complete evidence ledger still exist, so
# it must remain distinguishable from a fatal input/coverage/write blocker.
NON_FATAL_BLOCKER_REASONS = frozenset({"model_unavailable_no_cache"})
AUDIT_FILES = (
    "_audit/reference-blocks.jsonl",
    "_audit/sources.jsonl",
    "_audit/page-manifest.json",
    "_audit/run-metrics.json",
    "_audit/suspected-synonyms.md",
)
_MISSING = object()


@dataclass(frozen=True)
class AuditResult:
    """All deterministic audit rows plus their serialized five-file view."""

    files: Mapping[str, str]
    reference_rows: tuple[Mapping[str, Any], ...]
    source_rows: tuple[Mapping[str, Any], ...]
    manifest: Mapping[str, Any]
    metrics: Mapping[str, Any]
    source_statuses: Mapping[str, str]
    blockers: tuple[Mapping[str, Any], ...]
    coverage_ok: bool
    fact_claim_ids: frozenset[str]

    @property
    def fact_claim_count(self) -> int:
        return len(self.fact_claim_ids)

    @property
    def pages(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self.manifest.get("pages", ()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "files": dict(self.files),
            "reference_rows": [dict(row) for row in self.reference_rows],
            "source_rows": [dict(row) for row in self.source_rows],
            "manifest": dict(self.manifest),
            "metrics": dict(self.metrics),
            "source_statuses": dict(self.source_statuses),
            "blockers": [dict(row) for row in self.blockers],
            "coverage_ok": self.coverage_ok,
            "fact_claim_ids": sorted(self.fact_claim_ids),
        }


def _optional(value: object, name: str, default: object = _MISSING) -> object:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _required(value: object, name: str) -> object:
    result = _optional(value, name, _MISSING)
    if result is _MISSING:
        raise ValueError(f"audit input is missing {name!r}")
    return result


def _record(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        result = as_dict()
        if isinstance(result, Mapping):
            return dict(result)
    result: dict[str, Any] = {}
    for name in (
        "block_id",
        "source_path",
        "content_hash",
        "kind",
        "line_start",
        "line_end",
        "text",
        "heading_path",
        "claim_id",
        "source_block_id",
        "char_start",
        "char_end",
        "span_start",
        "span_end",
        "claim_kind",
        "status",
        "page_path",
        "page_anchor",
        "retrieval_evidence",
        "topic_key",
        "relative_path",
        "source_paths",
        "block_ids",
        "claim_ids",
        "page_paths",
    ):
        candidate = _optional(value, name, _MISSING)
        if candidate is not _MISSING:
            result[name] = candidate
    return result


def _source_path(value: object) -> str:
    raw = _required(value, "source_path")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("source_path must be a non-empty string")
    normalized = raw.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"source_path must be relative: {raw!r}")
    return "/".join(part for part in path.parts if part not in {"", "."})


def _stable_json(value: object) -> str:
    # Audit files may carry surrogateescaped source text from the lossless
    # ingest seam. ASCII escaping keeps JSON UTF-8-safe without changing the
    # stored content hash or the in-memory text.
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _jsonl(rows: Iterable[Mapping[str, Any]]) -> str:
    values = [_stable_json(dict(row)) for row in rows]
    return "\n".join(values) + ("\n" if values else "")


def _json_document(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"


def _normalize_block(value: object) -> dict[str, Any]:
    row = _record(value)
    row["source_path"] = _source_path(row)
    block_id = row.get("block_id")
    if not isinstance(block_id, str) or not block_id:
        raise ValueError(f"block {row['source_path']!r} is missing block_id")
    content_hash = row.get("content_hash", "")
    if not isinstance(content_hash, str):
        raise TypeError("block.content_hash must be a string")
    text = row.get("text", "")
    if isinstance(text, bytes):
        text = text.decode("utf-8", "surrogateescape")
    if not isinstance(text, str):
        raise TypeError("block.text must be a string")
    if not content_hash:
        content_hash = hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()
    row["content_hash"] = content_hash
    row["kind"] = str(row.get("kind", "narrative"))
    row["line_start"] = int(row.get("line_start", 1))
    row["line_end"] = int(row.get("line_end", max(row["line_start"], len(text.splitlines()))))
    row["text"] = text
    if row["line_start"] < 1 or row["line_end"] < row["line_start"]:
        raise ValueError(f"block line range is invalid: {block_id!r}")
    return row


def _normalize_claim(value: object) -> dict[str, Any]:
    row = _record(value)
    row["source_path"] = _source_path(row)
    required = {
        "claim_id",
        "content_hash",
        "line_start",
        "line_end",
        "char_start",
        "char_end",
        "page_path",
        "page_anchor",
        "span_start",
        "span_end",
        "claim_kind",
        "status",
    }
    if not isinstance(row.get("claim_id"), str) or not row["claim_id"]:
        raise ValueError("claim_id must be a non-empty string")
    if row.get("status") not in CLAIM_STATUSES:
        raise ValueError(f"unsupported claim status: {row.get('status')!r}")
    if row.get("claim_kind") not in CLAIM_KINDS:
        raise ValueError(f"unsupported claim kind: {row.get('claim_kind')!r}")
    for name in required - {"claim_id", "content_hash", "page_path", "page_anchor", "claim_kind", "status"}:
        if name not in row:
            row[name] = None
        elif row[name] is not None:
            row[name] = int(row[name])
    if not isinstance(row.get("content_hash", ""), str):
        raise TypeError("claim.content_hash must be a string")
    if "text" not in row:
        row["text"] = ""
    if not isinstance(row["text"], str) or not row["text"]:
        raise ValueError(f"claim.text must be non-empty: {row['claim_id']}")
    if row["status"] == "sourced":
        required_sourced = (
            "content_hash",
            "line_start",
            "line_end",
            "char_start",
            "char_end",
            "page_path",
            "page_anchor",
            "span_start",
            "span_end",
        )
        for name in required_sourced:
            candidate = row.get(name)
            if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
                raise ValueError(f"sourced claim is missing {name}: {row['claim_id']}")
        if row["line_end"] < row["line_start"] or row["char_end"] < row["char_start"]:
            raise ValueError(f"sourced claim has invalid source span: {row['claim_id']}")
        if row["span_end"] < row["span_start"]:
            raise ValueError(f"sourced claim has invalid page span: {row['claim_id']}")
    if row["status"] == "原文未明确":
        evidence = row.get("retrieval_evidence")
        if not isinstance(evidence, (list, tuple)) or not evidence:
            raise ValueError(f"unsupported claim needs retrieval_evidence: {row['claim_id']}")
        row["retrieval_evidence"] = [dict(item) if isinstance(item, Mapping) else item for item in evidence]
    # Keep the source identity in the serialized claim ledger.  It is the
    # join key for the source/block/page coverage checks; dropping it here
    # would make the later sort and every downstream audit consumer fail.
    field_order = (
        "claim_id",
        "source_path",
        "source_block_id",
        "content_hash",
        "line_start",
        "line_end",
        "char_start",
        "char_end",
        "page_path",
        "page_anchor",
        "span_start",
        "span_end",
        "claim_kind",
        "status",
        "retrieval_evidence",
        "text",
    )
    return {key: row[key] for key in field_order if key in row}


def _normalize_source_records(
    source_records: Iterable[object] | Mapping[object, object] | None,
    blocks: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    if source_records is None:
        values: list[object] = []
    elif isinstance(source_records, Mapping):
        values = []
        for source_path, raw in source_records.items():
            row = _record(raw)
            row.setdefault("source_path", str(source_path))
            values.append(row)
    else:
        values = list(source_records)
    if not values:
        by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for block in blocks:
            by_source[block["source_path"]].append(block)
        values = [
            {
                "source_path": source_path,
                "content_hash": hashlib.sha256(
                    "\x1f".join(block["content_hash"] for block in sorted(rows, key=lambda item: str(item["block_id"]))).encode("utf-8")
                ).hexdigest(),
                "readable": True,
                "blocks": list(rows),
            }
            for source_path, rows in sorted(by_source.items())
        ]
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    blocks_by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for block in blocks:
        blocks_by_source[block["source_path"]].append(block)
    for value in values:
        row = _record(value)
        row["source_path"] = _source_path(row)
        if row["source_path"] in seen:
            raise ValueError(f"duplicate source record: {row['source_path']}")
        seen.add(row["source_path"])
        if row.get("readable", True) is not True:
            row["readable"] = False
            row["content_hash"] = str(row.get("content_hash", ""))
            row["blocks"] = []
            row["has_narrative"] = False
            row.setdefault("blocked_reason", "source_unreadable")
            result.append(row)
            continue
        row["content_hash"] = str(row.get("content_hash", ""))
        declared_blocks = row.get("blocks", _MISSING)
        if declared_blocks is _MISSING:
            row["blocks"] = list(blocks_by_source.get(row["source_path"], ()))
        else:
            row["blocks"] = [_normalize_block(block) for block in declared_blocks]
        row["has_narrative"] = bool(row.get("has_narrative", any(block.get("kind") == "narrative" for block in row["blocks"])))
        result.append(row)
    for source_path, source_blocks in sorted(blocks_by_source.items()):
        if source_path not in seen:
            result.append(
                {
                    "source_path": source_path,
                    "content_hash": hashlib.sha256(
                        "\x1f".join(block["content_hash"] for block in source_blocks).encode("utf-8")
                    ).hexdigest(),
                    "readable": True,
                    "blocks": list(source_blocks),
                    "has_narrative": any(block.get("kind") == "narrative" for block in source_blocks),
                }
            )
    # Preserve the deterministic source-snapshot order.  Besides keeping the
    # manifest stable, that order is the already-declared canonical order for
    # duplicate content; sorting here would let a lexical alias silently take
    # over the canonical source.
    return tuple(result)


def _normalize_pages(pages: Iterable[object]) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    for value in pages:
        row = _record(value)
        topic_key = row.get("topic_key", row.get("key"))
        if not isinstance(topic_key, str) or not topic_key:
            raise ValueError("page.topic_key must be a non-empty string")
        paths = row.get("page_paths")
        if paths is None:
            parts = row.get("parts", ())
            paths = [
                _record(part).get("relative_path")
                for part in parts
                if _record(part).get("relative_path")
            ]
        if not paths:
            path = row.get("page_path", row.get("relative_path"))
            paths = [path] if path else []
        paths = tuple(str(path) for path in paths if path)
        if not paths:
            raise ValueError(f"page {topic_key!r} is missing page path")
        source_paths = tuple(sorted({_source_path({"source_path": path}) for path in row.get("source_paths", ())}))
        block_ids = tuple(sorted({str(item) for item in row.get("block_ids", ()) if str(item)}))
        claim_ids = tuple(sorted({str(item) for item in row.get("claim_ids", ()) if str(item)}))
        block_anchors = row.get("block_anchors", {})
        if not isinstance(block_anchors, Mapping):
            raise TypeError("page.block_anchors must be an object")
        result.append(
            {
                "topic_key": topic_key,
                "page_path": paths[0],
                "page_paths": paths,
                "source_paths": source_paths,
                "block_ids": block_ids,
                "claim_ids": claim_ids,
                "block_anchors": dict(block_anchors),
            }
        )
    return tuple(sorted(result, key=lambda row: row["topic_key"]))


def _declared_audit_only(
    source_records: Sequence[Mapping[str, Any]],
    audit_only_sources: Iterable[str],
) -> frozenset[str]:
    values = {_source_path({"source_path": source}) for source in audit_only_sources}
    for row in source_records:
        if row.get("expected_status") == "audit_only":
            values.add(row["source_path"])
    return frozenset(values)


def derive_source_status(
    source_records: Iterable[object] | Mapping[object, object],
    *,
    audit_only_sources: Iterable[str] = (),
) -> Mapping[str, str]:
    """Derive the four source-level statuses without consulting page output."""

    normalized = _normalize_source_records(source_records, ())
    declared = _declared_audit_only(normalized, audit_only_sources)
    by_hash: dict[str, str] = {}
    result: dict[str, str] = {}
    for row in normalized:
        path = row["source_path"]
        digest = row.get("content_hash", "")
        if row.get("readable", True) is False:
            result[path] = "blocked"
        elif path in declared:
            result[path] = "audit_only"
        elif digest and digest in by_hash:
            result[path] = "duplicate_alias"
        elif not any(
            str(block.get("kind", "heading")) != "heading"
            and bool(str(block.get("text", "")).strip())
            for block in row["blocks"]
        ):
            result[path] = "known_empty"
        else:
            result[path] = "ready"
        if result[path] not in {"audit_only", "blocked"} and digest and digest not in by_hash:
            by_hash[digest] = path
    return MappingProxyType(dict(sorted(result.items())))


def _source_statuses(
    source_records: Sequence[Mapping[str, Any]],
    declared_audit_only: frozenset[str],
) -> tuple[dict[str, str], dict[str, str | None]]:
    by_hash: dict[str, str] = {}
    statuses: dict[str, str] = {}
    aliases: dict[str, str | None] = {}
    for row in source_records:
        path = row["source_path"]
        digest = row.get("content_hash", "")
        if row.get("readable", True) is False:
            statuses[path] = "blocked"
            aliases[path] = None
        elif path in declared_audit_only:
            statuses[path] = "audit_only"
            aliases[path] = None
        elif digest and digest in by_hash:
            statuses[path] = "duplicate_alias"
            aliases[path] = by_hash[digest]
        elif not any(
            str(block.get("kind", "heading")) != "heading"
            and bool(str(block.get("text", "")).strip())
            for block in row["blocks"]
        ):
            statuses[path] = "known_empty"
            aliases[path] = None
        else:
            statuses[path] = "ready"
            aliases[path] = None
        if statuses[path] not in {"audit_only", "blocked"} and digest and digest not in by_hash:
            by_hash[digest] = path
    return statuses, aliases


def _page_source_paths(pages: Sequence[Mapping[str, Any]]) -> Mapping[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for page in pages:
        for source_path in page["source_paths"]:
            current = set(result.get(source_path, ()))
            current.update(page["page_paths"])
            result[source_path] = tuple(sorted(current))
    return MappingProxyType(dict(sorted(result.items())))


def _page_rows(pages: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "topic_key": page["topic_key"],
            "page_path": page["page_path"],
            "page_paths": list(page["page_paths"]),
            "source_paths": list(page["source_paths"]),
            "block_count": len(page["block_ids"]),
            "claim_count": len(page["claim_ids"]),
            "block_ids": list(page["block_ids"]),
            "claim_ids": list(page["claim_ids"]),
        }
        for page in pages
    )


def _anchor_map(
    pages: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, tuple[str, str]], dict[tuple[str, str], list[str]]]:
    by_block: dict[str, tuple[str, str]] = {}
    by_anchor: dict[tuple[str, str], list[str]] = defaultdict(list)
    for page in pages:
        explicit = page["block_anchors"]
        for index, block_id in enumerate(page["block_ids"], start=1):
            value = explicit.get(block_id)
            if isinstance(value, Mapping):
                page_path = str(value.get("page_path") or page["page_path"])
                page_anchor = str(value.get("page_anchor") or f"block-{index}")
            else:
                page_path = page["page_path"]
                page_anchor = f"block-{index}"
            if page_path not in page["page_paths"]:
                raise ValueError(
                    f"coverage: anchor page path {page_path!r} is not an emitted part of "
                    f"page {page['topic_key']!r}"
                )
            if block_id in by_block:
                previous = by_block[block_id]
                raise ValueError(
                    f"coverage: block {block_id!r} is emitted at multiple anchors: "
                    f"{previous!r} and {(page_path, page_anchor)!r}"
                )
            by_block[block_id] = (page_path, page_anchor)
            by_anchor[(page_path, page_anchor)].append(block_id)
    return by_block, by_anchor


def _canonical_block_for_alias(
    block: Mapping[str, Any],
    canonical_source: str,
    blocks: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    candidates = [
        candidate
        for candidate in blocks
        if candidate["source_path"] == canonical_source
        and candidate["kind"] == block["kind"]
        and candidate["content_hash"] == block["content_hash"]
    ]
    if not candidates:
        candidates = [candidate for candidate in blocks if candidate["source_path"] == canonical_source]
    return min(candidates, key=lambda candidate: (candidate["line_start"], candidate["line_end"], candidate["block_id"])) if candidates else None


def _block_rows(
    blocks: Sequence[Mapping[str, Any]],
    statuses: Mapping[str, str],
    aliases: Mapping[str, str | None],
    pages: Sequence[Mapping[str, Any]],
    initial_blockers: list[dict[str, Any]],
) -> tuple[tuple[dict[str, Any], ...], bool]:
    block_by_id: dict[str, Mapping[str, Any]] = {}
    for block in blocks:
        block_id = block["block_id"]
        if block_id in block_by_id:
            raise ValueError(f"coverage: duplicate block_id {block_id!r}")
        block_by_id[block_id] = block
    for page in pages:
        for block_id in page["block_ids"]:
            block = block_by_id.get(block_id)
            if block is None:
                raise ValueError(f"coverage: page {page['topic_key']!r} references unknown block {block_id!r}")
            if block["source_path"] not in page["source_paths"]:
                raise ValueError(
                    f"coverage: block {block_id!r} source {block['source_path']!r} "
                    f"is not declared by page {page['topic_key']!r}"
                )
    anchor_by_block, anchor_by_position = _anchor_map(pages)
    non_alias_positions: dict[tuple[str, str], str] = {}
    rows: list[dict[str, Any]] = []
    coverage_ok = True
    for position, block_id_list in sorted(anchor_by_position.items()):
        if len(block_id_list) > 1:
            distinct = sorted(set(block_id_list))
            if len(distinct) > 1:
                raise ValueError(f"coverage: multiple blocks share page anchor {position!r}: {distinct}")
    for block in sorted(blocks, key=lambda item: (item["source_path"], item["line_start"], item["line_end"], item["block_id"])):
        if block["kind"] not in REFERENCE_KINDS:
            continue
        source_path = block["source_path"]
        status = statuses[source_path]
        page_path: str | None = None
        page_anchor: str | None = None
        alias_of: str | None = None
        canonical_block_id: str | None = None
        if status == "duplicate_alias":
            alias_of = aliases[source_path]
            canonical = _canonical_block_for_alias(block, alias_of or "", blocks)
            if canonical is not None:
                canonical_block_id = canonical["block_id"]
                canonical_anchor = anchor_by_block.get(canonical_block_id)
                if canonical_anchor:
                    page_path, page_anchor = canonical_anchor
            if not alias_of or not canonical_block_id or not page_path or not page_anchor:
                coverage_ok = False
                initial_blockers.append(
                    {
                        "block_id": block["block_id"],
                        "source_path": source_path,
                        "reason": "duplicate_alias_missing_canonical_anchor",
                        "impact": "alias coverage cannot be reverse-resolved",
                    }
                )
        elif status == "audit_only":
            # The block is intentionally retained in the audit ledger without
            # a products/ anchor.  The declaration was checked before this
            # branch; missing declaration is never inferred from this shape.
            pass
        else:
            anchor = anchor_by_block.get(block["block_id"])
            if anchor:
                page_path, page_anchor = anchor
                position = (page_path, page_anchor)
                if position in non_alias_positions and non_alias_positions[position] != block["block_id"]:
                    raise ValueError(f"coverage: non-alias anchor collision at {position!r}")
                non_alias_positions[position] = block["block_id"]
            else:
                coverage_ok = False
                initial_blockers.append(
                    {
                        "block_id": block["block_id"],
                        "source_path": source_path,
                        "reason": "coverage_missing_page_anchor",
                        "impact": "reference block is not represented in products/",
                    }
                )
        row: dict[str, Any] = {
            "block_id": block["block_id"],
            "source_path": source_path,
            "content_hash": block["content_hash"],
            "block_kind": block["kind"],
            "line_start": block["line_start"],
            "line_end": block["line_end"],
            "page_path": page_path,
            "page_anchor": page_anchor,
            "status": status,
        }
        if alias_of is not None:
            row["alias_of"] = alias_of
        if canonical_block_id is not None:
            row["canonical_block_id"] = canonical_block_id
        rows.append(row)
    return tuple(rows), coverage_ok


def validate_block_coverage(
    reference_rows: Iterable[Mapping[str, Any]],
    *,
    blockers: Iterable[Mapping[str, Any]] = (),
) -> bool:
    """Validate the no-third-state block coverage rule."""

    blocked_ids = {str(row.get("block_id")) for row in blockers if row.get("block_id")}
    positions: dict[tuple[str, str], str] = {}
    for row in reference_rows:
        status = row.get("status")
        block_id = str(row.get("block_id", ""))
        if status == "duplicate_alias":
            if not row.get("alias_of") or not row.get("canonical_block_id") or not row.get("page_path") or not row.get("page_anchor"):
                if block_id not in blocked_ids:
                    raise ValueError(f"coverage: invalid duplicate alias {block_id!r}")
            continue
        if status == "audit_only":
            continue
        page_path = row.get("page_path")
        page_anchor = row.get("page_anchor")
        if not page_path or not page_anchor:
            if block_id not in blocked_ids:
                raise ValueError(f"coverage: block {block_id!r} has neither anchor nor blocker")
            continue
        position = (str(page_path), str(page_anchor))
        if position in positions and positions[position] != block_id:
            raise ValueError(f"coverage: anchor {position!r} is shared by non-alias blocks")
        positions[position] = block_id
    return True


def _normalized_blockers(rows: Iterable[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    unique: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = {str(key): value for key, value in dict(raw).items()}
        if not row.get("reason"):
            raise ValueError("blocker.reason must be non-empty")
        key = _stable_json(row)
        unique[key] = row
    return tuple(unique[key] for key in sorted(unique))


def _has_fatal_blocker(rows: Iterable[Mapping[str, Any]]) -> bool:
    return any(
        str(row.get("reason", "")) not in NON_FATAL_BLOCKER_REASONS
        for row in rows
    )


def _normalize_metrics(metrics: Mapping[str, Any], topic_count: int, blockers: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    def value(*names: str, default: object = _MISSING) -> object:
        for name in names:
            if name in metrics:
                return metrics[name]
        if default is not _MISSING:
            return default
        raise ValueError(f"run metrics missing {names[0]!r}")

    elapsed_ms = value("elapsed_ms", "duration_ms")
    provider_calls = value("provider_calls", "provider_calls_observed")
    provider_tokens = value("provider_tokens", "total_provider_tokens", "tokens")
    cache_hits = value("cache_hits", "cache_hit_count", default=0)
    planned = value("planned_provider_calls", "provider_calls_planned", default=provider_calls)
    actual = value("actual_provider_calls", "provider_calls_observed", "provider_calls", default=provider_calls)
    planned_topic_count = value("planned_topic_count", "topic_count", default=topic_count)
    normalized = {
        "elapsed_ms": elapsed_ms,
        "provider_calls": provider_calls,
        "provider_tokens": provider_tokens,
        "cache_hits": cache_hits,
        "planned_provider_calls": planned,
        "actual_provider_calls": actual,
        "planned_topic_count": planned_topic_count,
        "reasons": dict(metrics.get("reasons", {})),
        "blockers": [dict(row) for row in blockers],
    }
    for name in ("elapsed_ms", "provider_calls", "provider_tokens", "cache_hits", "planned_provider_calls", "actual_provider_calls", "planned_topic_count"):
        if not isinstance(normalized[name], int) or isinstance(normalized[name], bool) or normalized[name] < 0:
            raise ValueError(f"run metrics {name} must be a non-negative integer")
        if normalized[name] == 0:
            reason = normalized["reasons"].get(name)
            if reason is None and name == "planned_topic_count":
                reason = "no_provider_call_yet"
            if reason is None and name == "actual_provider_calls":
                reason = normalized["reasons"].get("provider_calls")
            if reason is None and name == "provider_tokens":
                reason = normalized["reasons"].get("provider_tokens")
            if reason not in ZERO_REASONS:
                raise ValueError(f"zero run metric {name} needs a valid reason")
            normalized["reasons"].setdefault(name, reason)
    if normalized["planned_provider_calls"] > normalized["planned_topic_count"] * 2 + 20:
        raise ValueError("planned provider calls exceed topic-count budget")
    if normalized["actual_provider_calls"] > normalized["planned_provider_calls"] * 1.5:
        raise ValueError("actual provider calls exceed planned-call budget")
    return normalized


def build_run_metrics(
    metrics: Mapping[str, Any],
    *,
    topic_count: int,
    blockers: Sequence[Mapping[str, Any]] = (),
) -> Mapping[str, Any]:
    """Validate and normalize the FR-AUD-005 cost record."""

    return MappingProxyType(_normalize_metrics(metrics, topic_count, blockers))


def _synonyms(suggestions: Iterable[Mapping[str, Any]]) -> str:
    rows = [dict(item) for item in suggestions]
    rows.sort(key=_stable_json)
    lines = ["# 疑似同义主题", "", "<!-- 仅报告建议；不改变页面成员。 -->", ""]
    if not rows:
        lines.append("暂无建议。")
    else:
        for row in rows:
            lines.append(f"- {_stable_json(row)}")
    return "\n".join(lines) + "\n"


def _manifest(
    *,
    attempt_id: str,
    source_snapshot: Mapping[str, Any],
    pages: Sequence[Mapping[str, Any]],
    source_records: Sequence[Mapping[str, Any]],
    statuses: Mapping[str, str],
    aliases: Mapping[str, str | None],
    blockers: Sequence[Mapping[str, Any]],
    run_status: str,
    publish_status: str,
) -> dict[str, Any]:
    page_rows = _page_rows(pages)
    direct_source_pages = _page_source_paths(pages)
    source_to_pages: dict[str, list[str]] = {}
    ledger: list[dict[str, Any]] = []
    for source in source_records:
        path = source["source_path"]
        status = statuses[path]
        canonical = aliases[path]
        if status == "duplicate_alias" and canonical:
            page_paths = list(direct_source_pages.get(canonical, ()))
        else:
            page_paths = list(direct_source_pages.get(path, ()))
        source_to_pages[path] = page_paths
        row: dict[str, Any] = {
            "source_path": path,
            "content_hash": source.get("content_hash", ""),
            "source_status": status,
            "pages": page_paths,
        }
        if canonical:
            row["alias_of"] = canonical
        ledger.append(row)
    return {
        "schema_version": "task7-page-manifest.v1",
        "publish_status": publish_status,
        "run_status": run_status,
        "attempt_id": attempt_id,
        "source_snapshot": dict(source_snapshot),
        "blockers": [dict(row) for row in blockers],
        "pages": page_rows,
        "source_to_pages": dict(sorted(source_to_pages.items())),
        "source_ledger": ledger,
    }


def build_audit(
    *,
    blocks: Iterable[object],
    claims: Iterable[object],
    pages: Iterable[object],
    source_records: Iterable[object] | Mapping[object, object] | None = None,
    block_anchors: Mapping[str, Mapping[str, Any]] | None = None,
    source_snapshot: Mapping[str, Any] | None = None,
    attempt_id: str = "",
    audit_only_sources: Iterable[str] = (),
    model_suggestions: Iterable[Mapping[str, Any]] = (),
    metrics: Mapping[str, Any] | None = None,
    blockers: Iterable[Mapping[str, Any]] = (),
    run_status: str = "complete",
    publish_status: str = "not_released",
) -> AuditResult:
    """Build and validate the five Task7 audit artifacts in memory."""

    if not isinstance(attempt_id, str) or not attempt_id:
        raise ValueError("attempt_id must be a non-empty string")
    if publish_status not in {"not_released", "released"}:
        raise ValueError(f"unsupported publish_status: {publish_status!r}")
    if publish_status == "released":
        raise ValueError("semantic audit cannot publish released output; use not_released")
    if run_status not in {"complete", "blocked", "interrupted"}:
        raise ValueError(f"unsupported run_status: {run_status!r}")
    normalized_blocks = tuple(sorted((_normalize_block(block) for block in blocks), key=lambda row: (row["source_path"], row["line_start"], row["line_end"], row["block_id"])))
    normalized_claims = tuple(sorted((_normalize_claim(claim) for claim in claims), key=lambda row: (row["source_path"], row["line_start"] or 0, row["char_start"] or 0, row["claim_id"])))
    normalized_pages = _normalize_pages(pages)
    normalized_sources = _normalize_source_records(source_records, normalized_blocks)
    declared_audit_only = _declared_audit_only(normalized_sources, audit_only_sources)
    statuses, aliases = _source_statuses(normalized_sources, declared_audit_only)
    working_blockers = [dict(row) for row in blockers]
    for row in normalized_sources:
        if row.get("readable", True) is False:
            working_blockers.append(
                {
                    "source_path": row["source_path"],
                    "reason": str(row.get("blocked_reason") or "source_unreadable"),
                    "impact": "frozen source cannot be reconciled or published",
                }
            )
    explicit_anchors = block_anchors or {}
    if not isinstance(explicit_anchors, Mapping):
        raise TypeError("block_anchors must be an object")
    if explicit_anchors:
        # Page-local anchors remain authoritative, but callers may provide the
        # same map directly when pages were materialized by another layer.
        for page in normalized_pages:
            for block_id, anchor in explicit_anchors.items():
                if block_id in page["block_ids"] and block_id not in page["block_anchors"]:
                    page["block_anchors"][block_id] = dict(anchor)

    direct_source_pages = _page_source_paths(normalized_pages)
    # A page manifest is a consumer of the declared source ledger.  Validate
    # that join before deriving reverse coverage so an arbitrary page source
    # cannot bypass the source status machine (especially known_empty and
    # blocked sources) and still look like a complete product page.
    for page in normalized_pages:
        for source_path in page["source_paths"]:
            status = statuses.get(source_path)
            if status is None:
                working_blockers.append(
                    {
                        "topic_key": page["topic_key"],
                        "source_path": source_path,
                        "reason": "page_references_unknown_source",
                        "impact": "page source is not present in the declared source ledger",
                    }
                )
            elif status == "known_empty":
                working_blockers.append(
                    {
                        "topic_key": page["topic_key"],
                        "source_path": source_path,
                        "reason": "known_empty_source_entered_products",
                        "impact": "known-empty source cannot provide a product page",
                    }
                )
            elif status == "blocked":
                working_blockers.append(
                    {
                        "topic_key": page["topic_key"],
                        "source_path": source_path,
                        "reason": "blocked_source_entered_products",
                        "impact": "unreadable source cannot provide a product page",
                    }
                )
    for source_path, status in statuses.items():
        if status == "ready" and not direct_source_pages.get(source_path):
            working_blockers.append(
                {
                    "source_path": source_path,
                    "reason": "ready_source_has_no_product_page",
                    "impact": "source content would be absent from the reader surface",
                }
            )
        if status == "audit_only" and direct_source_pages.get(source_path):
            working_blockers.append(
                {
                    "source_path": source_path,
                    "reason": "audit_only_source_entered_products",
                    "impact": "declared audit-only content entered a product page",
                }
            )
        if status == "duplicate_alias" and direct_source_pages.get(source_path):
            working_blockers.append(
                {
                    "source_path": source_path,
                    "reason": "duplicate_alias_source_entered_products",
                    "impact": "duplicate source must reuse canonical pages",
                }
            )

    reference_rows, block_coverage_ok = _block_rows(
        normalized_blocks,
        statuses,
        aliases,
        normalized_pages,
        working_blockers,
    )
    normalized_blockers = _normalized_blockers(working_blockers)
    try:
        validate_block_coverage(reference_rows, blockers=normalized_blockers)
    except ValueError:
        raise
    source_rows = tuple(normalized_claims)
    fact_claim_ids = frozenset(row["claim_id"] for row in source_rows if row["status"] == "sourced")
    if source_snapshot is None or not isinstance(source_snapshot, Mapping):
        raise ValueError("source_snapshot must be a mapping")
    if metrics is None or not isinstance(metrics, Mapping):
        raise ValueError("metrics must be a mapping with real cost facts")
    normalized_metrics = dict(_normalize_metrics(metrics, len(normalized_pages), normalized_blockers))
    if run_status == "interrupted":
        final_run_status = "interrupted"
    elif run_status == "blocked":
        final_run_status = "blocked"
    else:
        final_run_status = "blocked" if _has_fatal_blocker(normalized_blockers) else "complete"
    manifest = _manifest(
        attempt_id=attempt_id,
        source_snapshot=source_snapshot,
        pages=normalized_pages,
        source_records=normalized_sources,
        statuses=statuses,
        aliases=aliases,
        blockers=normalized_blockers,
        run_status=final_run_status,
        publish_status=publish_status,
    )
    normalized_metrics["blockers"] = [dict(row) for row in normalized_blockers]
    files = {
        AUDIT_FILES[0]: _jsonl(reference_rows),
        AUDIT_FILES[1]: _jsonl(source_rows),
        AUDIT_FILES[2]: _json_document(manifest),
        AUDIT_FILES[3]: _json_document(normalized_metrics),
        AUDIT_FILES[4]: _synonyms(model_suggestions),
    }
    return AuditResult(
        files=MappingProxyType(files),
        reference_rows=tuple(MappingProxyType(dict(row)) for row in reference_rows),
        source_rows=tuple(MappingProxyType(dict(row)) for row in source_rows),
        manifest=MappingProxyType(manifest),
        metrics=MappingProxyType(normalized_metrics),
        source_statuses=MappingProxyType(dict(sorted(statuses.items()))),
        blockers=tuple(MappingProxyType(dict(row)) for row in normalized_blockers),
        coverage_ok=block_coverage_ok and not any(row.get("reason", "").startswith("coverage_") for row in normalized_blockers),
        fact_claim_ids=fact_claim_ids,
    )


def write_audit(output_dir: str | Path, **kwargs: Any) -> AuditResult:
    """Write the five audit files, replacing the manifest last."""

    result = build_audit(**kwargs)
    root = Path(output_dir)
    audit_dir = root / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    temporary: list[tuple[Path, Path]] = []
    try:
        for relative, content in result.files.items():
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            handle, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=str(destination.parent))
            with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.append((Path(temp_name), destination))
        for temporary_path, destination in temporary:
            if destination.name == "page-manifest.json":
                continue
            os.replace(temporary_path, destination)
        for temporary_path, destination in temporary:
            if destination.name == "page-manifest.json":
                os.replace(temporary_path, destination)
        return result
    finally:
        for temporary_path, _ in temporary:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


__all__ = [
    "AUDIT_FILES",
    "AuditResult",
    "build_audit",
    "build_run_metrics",
    "derive_source_status",
    "validate_block_coverage",
    "write_audit",
]
