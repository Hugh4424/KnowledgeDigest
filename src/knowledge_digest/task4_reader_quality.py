"""Task4: semantic Reader compiler and machine-only comparison.

The module keeps the sample denominator in configuration.  The compiler is a
generic source -> semantic node -> Reader/Audit adapter; it does not contain
the 89-source directory map or a human-review queue.
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import unquote

import fcntl

from .companybrain_mapping import source_manifest_hash as _companybrain_source_manifest_hash
from .companybrain_mapping import tree_hash as _companybrain_tree_hash


SCHEMA_VERSION = "task4-reader-quality.v1"
NOT_RELEASED = "not_released"
_PLACEHOLDER_RE = re.compile(r"^(?:todo|tbd|待补充|暂无|略|内容待补充|placeholder)[。.!！。\s]*$", re.I)
_META_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$")
# A document mentioning that a UI action can report a conflict is not itself
# contradictory evidence.  Only an explicit evidence annotation can block a
# semantic node; this keeps ordinary requirement prose publishable while
# preserving the fixture's deliberate ``冲突版本：...`` case.
_CONFLICT_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:冲突版本|矛盾证据|conflict\s+evidence|contradictory\s+evidence)\s*[:：]")
_BOUNDARY_RE = re.compile(r"规则|边界|限制|不支持|注意|条件|权限|失败|异常|约束|supported|limit", re.I)
# These are internal fields only when rendered as a field/metadata line.  A
# source may legitimately discuss a provider or a fingerprint as ordinary
# product terminology; matching any occurrence would reject good source text.
_LEAK_RE = re.compile(r"(?im)^\s*(?:source_uri|content_hash|fingerprint|provider|claim_id|source_snapshot_id|fragment_locator|target_path|classification_status)\s*:")


class Task4ReaderError(RuntimeError):
    def __init__(self, message: str, *, code: str = "task4_error") -> None:
        super().__init__(message)
        self.code = code


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%S%fZ")


def _load_config(config: Path | Mapping[str, Any] | None) -> dict[str, Any]:
    config_dir: Path | None = None
    if config is None:
        value: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "source_extensions": [".md", ".txt", ".json"],
            "excluded_names": [".DS_Store"],
            "max_page_lines": 300,
        }
    elif isinstance(config, Mapping):
        value = dict(config)
    else:
        path = Path(config)
        config_dir = path.parent
        if path.is_symlink() or not path.is_file():
            raise Task4ReaderError(f"config is not a regular file: {path}", code="config_missing")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise Task4ReaderError(f"cannot read config: {exc}", code="config_invalid") from exc
    if value.get("schema_version") != SCHEMA_VERSION:
        raise Task4ReaderError("unexpected Task4 config schema", code="config_invalid")
    extensions = value.get("source_extensions", [".md", ".txt", ".json"])
    if not isinstance(extensions, list) or not all(isinstance(item, str) and item.startswith(".") for item in extensions):
        raise Task4ReaderError("source_extensions must be a list of suffixes", code="config_invalid")
    coverage = value.get("source_coverage", {})
    if coverage is None:
        coverage = {}
    if not isinstance(coverage, Mapping):
        raise Task4ReaderError("source_coverage must be an object", code="config_invalid")
    # Backward-compatible input only: unlike the old implementation, there
    # is no default 89 here.
    if "expected_source_count" in value and "expected_count" not in coverage:
        coverage = {**coverage, "expected_count": value["expected_source_count"]}
    expected = coverage.get("expected_count")
    if expected is not None and (not isinstance(expected, int) or expected < 1):
        raise Task4ReaderError("source_coverage.expected_count must be a positive integer", code="config_invalid")
    if not isinstance(value.get("excluded_names", []), list):
        raise Task4ReaderError("excluded_names must be a list", code="config_invalid")
    empty_source_policy = value.get("empty_source_policy", "fail")
    if empty_source_policy not in {"fail", "audit_only"}:
        raise Task4ReaderError("empty_source_policy must be fail or audit_only", code="config_invalid")
    empty_source_allowlist = value.get("empty_source_allowlist", [])
    if not isinstance(empty_source_allowlist, list) or any(
        not isinstance(item, Mapping) or not item.get("source_uri") or not item.get("content_hash")
        for item in empty_source_allowlist
    ):
        raise Task4ReaderError("empty_source_allowlist must contain source_uri and content_hash", code="config_invalid")
    if not isinstance(value.get("taxonomy", {}), Mapping):
        raise Task4ReaderError("taxonomy must be an object", code="config_invalid")
    value["source_extensions"] = extensions
    value["source_coverage"] = dict(coverage)
    fixture_ref = value["source_coverage"].get("fixture")
    if fixture_ref and config_dir is not None:
        fixture_path = config_dir / str(fixture_ref)
        fixture = _read_json(fixture_path)
        if fixture.get("input_manifest_id") != value["source_coverage"].get("manifest_id"):
            raise Task4ReaderError("source coverage fixture manifest id mismatch", code="config_invalid")
        if fixture.get("expected_count") != value["source_coverage"].get("expected_count"):
            raise Task4ReaderError("source coverage fixture count mismatch", code="config_invalid")
        value["source_coverage_fixture_data"] = fixture
    page_type_fixture = value.get("page_type_fixture")
    if page_type_fixture and config_dir is not None:
        registry = _read_json(config_dir / str(page_type_fixture))
        page_types = registry.get("page_types", registry) if isinstance(registry, Mapping) else None
        if not isinstance(page_types, Mapping) or not page_types:
            raise Task4ReaderError("page type fixture must contain page_types", code="config_invalid")
        value["page_types"] = dict(page_types)
    value.setdefault("semantic", {})
    value.setdefault("page_types", {"procedure": {"required_sections": ["Summary", "答案", "规则和边界", "相关主题", "来源（简表）"]}})
    value["config_generation"] = str(value.get("config_generation") or _sha256_json({k: v for k, v in value.items() if k != "config_generation"}))
    return value


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    marker = text.find("\n---\n", 4)
    if marker < 0:
        return {}, text
    metadata: dict[str, str] = {}
    for line in text[4:marker].splitlines():
        match = _META_RE.match(line)
        if match:
            metadata[match.group(1)] = match.group(2).strip().strip("'\"")
    return metadata, text[marker + 5 :]


def _source_title(text: str, path: Path, metadata: Mapping[str, str]) -> str:
    if metadata.get("title"):
        return metadata["title"].strip()
    # Keep export separators long enough for _display_title to remove
    # breadcrumb suffixes such as ``_Merchant Management_Reseller Portal``.
    filename_title = path.stem.strip()
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            heading = re.sub(r"\*+", "", match.group(1)).strip().strip("#").strip()
            if heading and not re.match(r"^(?:\d+[.)、]?\s*)?(?:背景介绍|目录|文档目录|document\s+directory|[・·•].*|q\s*&?\s*a|问答)$", heading, re.I):
                return heading
    return filename_title or "未命名主题"


def _clean_segment(value: Any) -> str:
    value = unicodedata.normalize("NFKC", str(value)).strip()
    value = re.sub(r"[\\/:*?\"<>|#\[\]{}()（）【】、，。；：]+", "-", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip(".-")
    return value[:100] or "topic"


def _module_path_parts(value: Any) -> list[str]:
    """Return reader directory parts without flattening the taxonomy.

    Taxonomy rules may already provide a CompanyBrain-style path such as
    ``模块手册/字段与筛选``.  A short module label remains a short module
    label; the compiler never invents a ``modules/<label>`` bucket or a
    fake ``通用`` category.
    """
    parts = [_clean_segment(part) for part in str(value or "").split("/") if str(part).strip()]
    if not parts:
        return ["待分类"]
    return parts


def _topic_page_path(topic: Mapping[str, Any]) -> str:
    return (
        PurePosixPath("products")
        / _clean_segment(topic["product"])
        / PurePosixPath(*_module_path_parts(topic["module"]))
        / f"{_topic_slug(topic)}.md"
    ).as_posix()


def _normal_key(value: Any) -> str:
    """Normalize exported directory labels before applying taxonomy rules."""
    return unicodedata.normalize("NFKC", str(value)).strip().casefold()


def _display_title(source_title: str, source: Mapping[str, Any], config: Mapping[str, Any]) -> tuple[str, str]:
    semantic = config.get("semantic", {})
    rules = semantic.get("title_rules", []) if isinstance(semantic, Mapping) else []
    haystack = "\n".join(str(source.get(key, "")) for key in ("source_uri", "title", "body")).casefold()
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, Mapping) or not rule.get("title"):
                continue
            terms = rule.get("any", [])
            if isinstance(terms, str):
                terms = [terms]
            if isinstance(terms, list) and terms and any(str(term).casefold() in haystack for term in terms):
                return str(rule["title"]).strip(), str(rule.get("id") or "title-rule")
    cleaned = re.sub(r"\*+", "", source_title).strip()
    cleaned = re.sub(r"^\[?ae\]?\s*[-_:：]?\s*", "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"^\d+[.)、]\s*", "", cleaned).strip()
    cleaned = re.sub(r"^\d{1,3}\s+", "", cleaned).strip()
    if "_" in cleaned:
        cleaned = cleaned.split("_", 1)[0].strip()
    cleaned = re.sub(r"^(?:来源|文档|page|export)\s*[-_:：]?\s*", "", cleaned, flags=re.I).strip()
    return cleaned or "未命名主题", "derived-title"


def _taxonomy(relative: str, title: str, body: str, metadata: Mapping[str, str], config: Mapping[str, Any]) -> dict[str, str]:
    parts = PurePosixPath(relative).parts
    root = parts[0] if parts else ""
    normalized_root = _normal_key(root)
    taxonomy = config.get("taxonomy", {})
    aliases = taxonomy.get("root_aliases", {}) if isinstance(taxonomy, Mapping) else {}
    alias = {}
    if isinstance(aliases, Mapping):
        alias = next((value for key, value in aliases.items() if _normal_key(key) == normalized_root and isinstance(value, Mapping)), {})
    product = str(metadata.get("product") or alias.get("product") or (parts[0] if len(parts) > 1 else ""))
    if metadata.get("module"):
        return {"product": product or "待定", "module": metadata["module"], "classification_status": "classified", "classification_rule_id": "metadata", "classification_basis": "metadata"}
    match_title_only = bool(taxonomy.get("match_title_only")) if isinstance(taxonomy, Mapping) else False
    haystack = "\n".join((relative, title) if match_title_only else (relative, title, body)).casefold()
    rules = taxonomy.get("rules", []) if isinstance(taxonomy, Mapping) else []
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, Mapping):
                continue
            roots = rule.get("roots", [])
            if isinstance(roots, list) and roots and normalized_root not in {_normal_key(item) for item in roots}:
                continue
            any_terms = rule.get("any", [])
            if isinstance(any_terms, str):
                any_terms = [any_terms]
            if isinstance(any_terms, list) and any_terms and not any(str(term).casefold() in haystack for term in any_terms):
                continue
            all_terms = rule.get("all", [])
            if isinstance(all_terms, str):
                all_terms = [all_terms]
            if isinstance(all_terms, list) and any(str(term).casefold() not in haystack for term in all_terms):
                continue
            return {"product": str(rule.get("product") or product or "待定"), "module": str(rule.get("module") or "待定"), "classification_status": "classified", "classification_rule_id": str(rule.get("id") or "rule"), "classification_basis": "config_rule"}
    return {"product": product or "待定", "module": "待定", "classification_status": "unclassified", "classification_rule_id": "unmatched", "classification_basis": "no_matching_rule"}


_NOISE_LABEL_RE = re.compile(r"^(?:文档目录|文档修订记录|版本/时间|修订记录/修订人|document\s+directory|revision\s+history)$", re.I)
_NOISE_HEADING_RE = re.compile(r"目录|修订记录|revision|document\s+directory", re.I)


def _clean_content_line(raw: str) -> str:
    """Turn one source line into reader text without flattening table columns."""
    line = raw.strip()
    if _NOISE_LABEL_RE.fullmatch(line):
        return ""
    line = line.replace("\u00a0", " ").replace("<br />", "；").replace("<br/>", "；")
    line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
    line = re.sub(r"https?://\S+", "", line)
    line = re.sub(r"(?:蓝湖链接|lanhu\s+link)", "", line, flags=re.I)
    line = re.sub(r"[*_`~]", "", line)
    line = re.sub(r"^(?:[-*+]\s+|\d+[.)、]\s+)", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return re.sub(r"[；;、,，]\s*$", "", line).strip()


def _table_cells(raw: str) -> list[str] | None:
    line = raw.strip()
    if line.count("|") < 2:
        return None
    cells = [_clean_content_line(cell) for cell in line.strip("|").split("|")]
    if cells and all(not cell or set(cell) <= {"-", ":"} for cell in cells):
        return []
    return cells


def _section_kind(heading: str) -> str:
    if _NOISE_HEADING_RE.search(heading):
        return "ignored"
    if re.search(r"排查|故障|异常|问题|错误|失败|验证|检查|troubleshoot|diagnostic|faq|常见问题", heading, re.I):
        return "diagnostic"
    if _BOUNDARY_RE.search(heading):
        return "boundary"
    if re.search(r"背景|用途|适用|功能介绍|概述|目标|场景|overview|introduction", heading, re.I):
        return "usage"
    if re.search(r"入口|步骤|操作|配置|页面|内容|添加|新增|编辑|删除|列表|弹窗|筛选|设置|管理|procedure|action", heading, re.I):
        return "procedure"
    return "detail"


def _sections(body: str) -> list[dict[str, Any]]:
    """Parse source into typed blocks while retaining source line locations."""
    result: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_table: dict[str, Any] | None = None

    def flush_table() -> None:
        nonlocal pending_table
        if pending_table is not None and pending_table.get("rows"):
            current["blocks"].append(pending_table)
        pending_table = None

    def start_section(line_no: int, heading: str) -> None:
        nonlocal current
        flush_table()
        raw_heading = heading.strip()
        cleaned_heading = _clean_content_line(raw_heading)
        kind = "ignored" if _NOISE_LABEL_RE.fullmatch(raw_heading) else _section_kind(cleaned_heading)
        current = {"line_no": line_no, "heading": cleaned_heading, "kind": kind, "blocks": []}
        result.append(current)

    for line_no, raw in enumerate(body.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("<!--") or line == "---":
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            start_section(line_no, match.group(1))
            continue
        if current is None:
            start_section(line_no, "概览")
        if _NOISE_LABEL_RE.fullmatch(line):
            start_section(line_no, line)
            continue
        cells = _table_cells(line)
        if cells == []:
            if pending_table is not None and not pending_table["rows"] and pending_table.get("headers"):
                # Confluence exports FAQ rows as ``| 1 | question | answer |``
                # followed by a separator, without a real header row.  Keep
                # that row instead of silently dropping the only boundary
                # evidence in the table.
                first_cell = str(pending_table["headers"][0]).strip()
                if re.fullmatch(r"\d+", first_cell):
                    values = list(pending_table["headers"])
                    pending_table["headers"] = [f"字段{index}" for index in range(1, len(values) + 1)]
                    pending_table["rows"].append({"line_no": int(pending_table["line_start"]), "cells": values})
            continue
        if cells is not None:
            if current["kind"] == "ignored":
                continue
            if pending_table is None:
                pending_table = {"kind": "table", "line_start": line_no, "line_end": line_no, "headers": cells, "rows": []}
            elif not pending_table["rows"]:
                pending_table["line_end"] = line_no
                # The first row is the header; a separator was already skipped.
                if cells != pending_table["headers"]:
                    pending_table["rows"].append({"line_no": line_no, "cells": cells})
            else:
                pending_table["line_end"] = line_no
                pending_table["rows"].append({"line_no": line_no, "cells": cells})
            continue
        flush_table()
        cleaned = _clean_content_line(line)
        if not cleaned or re.fullmatch(r"[；|\-:：\s]+", cleaned) or current["kind"] == "ignored":
            continue
        block = {"kind": "text", "line_no": line_no, "text": cleaned}
        if not current["blocks"] or current["blocks"][-1] != block:
            current["blocks"].append(block)
    flush_table()
    return [section for section in result if section["kind"] != "ignored" and section["blocks"]]


def _content_lines(sections: list[Mapping[str, Any]]) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for section in sections:
        for block in section.get("blocks", []):
            if block.get("kind") == "text":
                row = (int(block["line_no"]), str(block["text"]))
                if not rows or rows[-1][1] != row[1]:
                    rows.append(row)
            elif block.get("kind") == "table":
                for row in block.get("rows", []):
                    cells = [str(cell) for cell in row.get("cells", []) if str(cell).strip()]
                    if cells:
                        value = " | ".join(cells)
                        item = (int(row["line_no"]), value)
                        if not rows or rows[-1][1] != value:
                            rows.append(item)
    return rows


def _extract_content(source: Mapping[str, Any]) -> dict[str, Any]:
    body = str(source["body"])
    sections = _sections(body)
    meaningful = _content_lines(sections)
    if not meaningful:
        raise Task4ReaderError(f"source has no readable content: {source['source_uri']}", code="empty_body")
    if all(_PLACEHOLDER_RE.fullmatch(line) for _, line in meaningful):
        raise Task4ReaderError(f"source is placeholder-only: {source['source_uri']}", code="placeholder_body")
    answer: list[tuple[int, str]] = []
    boundary: list[tuple[int, str]] = []
    diagnostic: list[tuple[int, str]] = []
    usage: list[tuple[int, str]] = []
    procedure: list[tuple[int, str]] = []
    for section in sections:
        rows = _content_lines([section])
        kind = section["kind"]
        if kind == "boundary":
            boundary.extend(rows)
        elif kind == "diagnostic":
            diagnostic.extend(rows)
        elif kind == "usage":
            usage.extend(rows)
            answer.extend(rows)
        elif kind in {"procedure", "detail"}:
            procedure.extend(rows)
            answer.extend(rows)
    if not answer:
        answer = meaningful[:]
    if not boundary:
        boundary = [(no, line) for no, line in meaningful if re.search(r"不能|不可|不支持|仅|必须|限制|注意|条件|权限", line)]
    claims: list[dict[str, Any]] = []
    for ordinal, (line_no, line) in enumerate(meaningful, start=1):
        claims.append({
            "claim_id": f"claim-{source['source_id']}-{ordinal:04d}",
            "source_snapshot_id": source["source_id"],
            "source_id": source["source_id"],
            "source_uri": source["source_uri"],
            "content_hash": source["content_hash"],
            "fragment_locator": f"line:{line_no}",
            "line_start": line_no,
            "line_end": line_no,
            "normalized_claim_text": line.casefold(),
            "text": line,
            "verification_status": "verified",
            "relation_id": None,
        })
    summary = (usage[0][1] if usage else meaningful[0][1])
    return {
        "summary": summary,
        "answer": answer[:120],
        "boundary": boundary[:80],
        "usage": usage[:80],
        "procedure": procedure[:120],
        "diagnostic": diagnostic[:80],
        "sections": sections,
        "claims": claims,
    }


def _merge_content(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    contents = [row["content"] for row in rows]
    merged: dict[str, Any] = {
        "summary": str(contents[0]["summary"]),
        "answer": [], "boundary": [], "usage": [], "procedure": [], "diagnostic": [], "sections": [], "claims": [],
    }
    seen_lines: set[tuple[str, int, str]] = set()
    for content in contents:
        for key in ("answer", "boundary", "usage", "procedure", "diagnostic"):
            for item in content.get(key, []):
                value = (str(item[1]), int(item[0]))
                if value not in {(str(existing[1]), int(existing[0])) for existing in merged[key]}:
                    merged[key].append(item)
        for section in content.get("sections", []):
            section_copy = dict(section)
            section_copy["blocks"] = list(section.get("blocks", []))
            section_key = (str(section_copy.get("heading")), int(section_copy.get("line_no", 0)), str(rows[0].get("source_id", "")))
            if section_key not in seen_lines:
                merged["sections"].append(section_copy)
                seen_lines.add(section_key)
        merged["claims"].extend(content.get("claims", []))
    if not merged["answer"]:
        merged["answer"] = merged["procedure"] or merged["usage"]
    return merged


def _source_row(raw_root: Path, path: Path, *, ordinal: int, config: Mapping[str, Any]) -> dict[str, Any]:
    relative = path.relative_to(raw_root).as_posix()
    data = path.read_bytes()
    text = data.decode("utf-8")
    metadata, body = _parse_frontmatter(text)
    raw_title = _source_title(body, path, metadata)
    classification = _taxonomy(relative, raw_title, body, metadata, config)
    title, title_rule = _display_title(raw_title, {"source_uri": relative, "title": raw_title, "body": body}, config)
    topic_key = metadata.get("topic_key") or f"{classification['product']}/{classification['module']}/{title}"
    source_id = f"source-{_sha256_bytes(relative.encode('utf-8'))[:16]}"
    row = {
        "source_id": source_id,
        "source_snapshot_id": source_id,
        "source_uri": relative,
        "title": title,
        "raw_title": raw_title,
        "product": classification["product"],
        "module": classification["module"],
        "topic_key": topic_key,
        "content_hash": _sha256_bytes(data),
        "byte_count": len(data),
        "line_count": len(text.splitlines()),
        "ordinal": ordinal,
        "text": text,
        "body": body,
        "metadata": metadata,
        "title_rule_id": title_rule,
        "lineage": {"source_uri": relative, "content_hash": _sha256_bytes(data), "source_snapshot_id": source_id},
        **classification,
    }
    row["status"] = "valid"
    try:
        row["content"] = _extract_content(row)
    except Task4ReaderError as exc:
        allowlisted_empty_source = any(
            isinstance(item, Mapping)
            and str(item.get("source_uri")) == relative
            and str(item.get("content_hash")) == row["content_hash"]
            for item in config.get("empty_source_allowlist", [])
        )
        if exc.code != "empty_body" or config.get("empty_source_policy", "fail") != "audit_only" or not allowlisted_empty_source:
            raise
        # A Confluence title-only page is a real input artifact, but it is not
        # knowledge. Keep it in the 89-row audit manifest and snapshot; do not
        # invent a Reader page or claims from the filename.
        row["status"] = "not_applicable"
        row["reason_code"] = exc.code
        row["reason"] = str(exc)
        row["content"] = {
            "summary": "",
            "answer": [],
            "boundary": [],
            "diagnostic": [],
            "usage": [],
            "procedure": [],
            "sections": [],
            "claims": [],
        }
    return row


def _collect_sources(raw_root: Path, config: Mapping[str, Any], *, cancel_check: Callable[[], bool] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise Task4ReaderError(f"raw input is not a regular directory: {raw_root}", code="source_unreadable")
    extensions = {str(item).casefold() for item in config["source_extensions"]}
    excluded = {str(item) for item in config.get("excluded_names", [])}
    sources: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    paths = [path for path in sorted(raw_root.rglob("*")) if path.is_file() and not path.is_symlink() and path.name not in excluded and path.suffix.casefold() in extensions]
    for ordinal, path in enumerate(paths):
        if cancel_check and cancel_check():
            raise KeyboardInterrupt
        relative = path.relative_to(raw_root).as_posix()
        try:
            sources.append(_source_row(raw_root, path, ordinal=ordinal, config=config))
        except (OSError, UnicodeError, Task4ReaderError) as exc:
            try:
                data = path.read_bytes()
            except OSError:
                data = b""
            failures.append({
                "source_id": f"source-{_sha256_bytes(relative.encode('utf-8'))[:16]}",
                "source_snapshot_id": f"source-{_sha256_bytes(relative.encode('utf-8'))[:16]}",
                "source_uri": relative,
                "content_hash": _sha256_bytes(data),
                "byte_count": len(data),
                "status": "failed",
                "reason_code": getattr(exc, "code", "source_unreadable"),
                "reason": str(exc),
                "lineage": {"source_uri": relative, "content_hash": _sha256_bytes(data)},
            })
    return sources, failures


def _relative_link(from_path: PurePosixPath, to_path: PurePosixPath) -> str:
    return posixpath.relpath(to_path.as_posix(), start=from_path.parent.as_posix())


def _topic_slug(topic: Mapping[str, Any]) -> str:
    return _clean_segment(str(topic.get("title") or str(topic.get("topic_key", "topic")).split("/")[-1]))


def _page_type(config: Mapping[str, Any], source: Mapping[str, Any]) -> str:
    value = source.get("metadata", {}).get("page_type") if isinstance(source.get("metadata"), Mapping) else None
    page_type = str(value or "procedure")
    registry = config.get("page_types", {})
    if isinstance(registry, Mapping) and page_type not in registry:
        raise Task4ReaderError(f"unknown page type: {page_type}", code="page_type_invalid")
    return page_type


def _semantic_node(topic_key: str, rows: list[dict[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    canonical = rows[0]
    claims: list[dict[str, Any]] = []
    for row in rows:
        claims.extend(row["content"]["claims"])
    unique_keys = {(c["source_snapshot_id"], c["fragment_locator"], c["normalized_claim_text"], c.get("relation_id")) for c in claims}
    conflicts = [row["source_uri"] for row in rows if _CONFLICT_RE.search(str(row.get("body", "")))]
    candidate = {
        "candidate_name": canonical["title"],
        "product": canonical["product"],
        "module": canonical["module"],
        "object": canonical["title"],
        "topic_key": topic_key,
    }
    status = "supported"
    reasons: list[str] = []
    if canonical.get("classification_status") != "classified":
        status = "pending"
        reasons.append("classification_unresolved")
    if not canonical.get("title") or canonical["title"].casefold() in {"未命名主题", "unknown"}:
        status = "pending"
        reasons.append("name_missing")
    # A short, classified product-introduction page can be a valid atomic
    # knowledge item.  Keep the evidence floor for unresolved material, where
    # publishing one sentence would otherwise create a falsely confident page.
    if len(unique_keys) < 2 and canonical.get("classification_status") != "classified":
        status = "pending"
        reasons.append("supporting_fragments_below_two")
    if conflicts:
        status = "conflict"
        reasons.append("contradictory_evidence")
    return {
        "node_id": f"node-{_sha256_bytes(topic_key.encode('utf-8'))[:16]}",
        "topic_key": topic_key,
        **candidate,
        "status": status,
        "classification_status": canonical.get("classification_status"),
        "page_type": _page_type(config, canonical),
        "supporting_evidence": claims,
        "supporting_fragment_count": len(unique_keys),
        "conflict_sources": conflicts,
        "reasons": reasons,
        "lineage": [row["lineage"] for row in rows],
    }


def _related(topic: Mapping[str, Any], topics: list[dict[str, Any]], config: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups = config.get("related_topic_groups", [])
    if isinstance(groups, list):
        for group in groups:
            if not isinstance(group, Mapping) or group.get("topic_key") != topic.get("topic_key"):
                continue
            keys = {str(key) for key in group.get("related_topic_keys", [])} if isinstance(group.get("related_topic_keys", []), list) else set()
            return [row for row in topics if row.get("topic_key") in keys]
    return []


def _render_blocks(lines: list[str], sections: Iterable[Mapping[str, Any]]) -> None:
    for section in sections:
        heading = str(section.get("heading") or "").strip()
        if heading:
            lines.extend([f"### {heading}", ""])
        for block in section.get("blocks", []):
            if block.get("kind") == "text":
                text = str(block["text"])
                if re.fullmatch(r"[^。！？!?]{1,40}[：:]", text):
                    lines.extend([f"#### {text.rstrip('：:')}", ""])
                else:
                    lines.append(f"- {text}")
            elif block.get("kind") == "table":
                headers = [str(cell) for cell in block.get("headers", [])]
                if headers:
                    lines.append("| " + " | ".join(headers) + " |")
                    lines.append("| " + " | ".join("---" for _ in headers) + " |")
                    for row in block.get("rows", []):
                        cells = [str(cell) for cell in row.get("cells", [])]
                        if len(cells) < len(headers):
                            cells.extend([""] * (len(headers) - len(cells)))
                        lines.append("| " + " | ".join(cells[:len(headers)]) + " |")


def _answer_highlights(content: Mapping[str, Any]) -> list[str]:
    rows = [item for item in content.get("answer", []) if isinstance(item, (list, tuple)) and len(item) == 2]
    keywords = re.compile(r"在|拖入|选择|默认|点击|保存|配置|至少|最多|不能|不可|不支持|提交|取消|入口|用于|支持", re.I)
    ranked: list[tuple[int, int, str]] = []
    for index, (_, text) in enumerate(rows):
        value = str(text).strip()
        if not value or value.endswith(("：", ":")):
            continue
        score = 2 if keywords.search(value) else 0
        if re.search(r"\d|inside|outside|wifi|vpn|bluetooth", value, re.I):
            score += 1
        if score:
            ranked.append((-score, index, value))
    selected = [value for _, _, value in sorted(ranked)[:10]]
    return selected or [str(text) for _, text in rows[:6]]


def _render_page(topic: Mapping[str, Any], related: list[dict[str, Any]], source_entries: list[dict[str, Any]], max_lines: int, page_types: Mapping[str, Any]) -> str:
    content = topic["content"]
    sections = content.get("sections", [])
    usage_sections = [section for section in sections if section.get("kind") == "usage"]
    procedure_sections = [section for section in sections if section.get("kind") in {"procedure", "detail"}]
    diagnostic_sections = [section for section in sections if section.get("kind") == "diagnostic"]
    boundary_sections = [section for section in sections if section.get("kind") == "boundary"]
    lines = [f"# {topic['title']}", "", "## Summary", "", f"本主题说明：{content['summary']}"]
    if topic.get("page_type") == "diagnostic":
        lines.extend(["", "## 排查路径", ""])
        if diagnostic_sections:
            _render_blocks(lines, diagnostic_sections)
        elif content.get("diagnostic"):
            lines.extend(f"- {line}" for _, line in content["diagnostic"])
        else:
            lines.append("- 来源没有单独给出排查路径，本页不额外推断。")
    else:
        lines.extend(["", "## 答案", ""])
        lines.extend(f"- {line}" for line in _answer_highlights(content))
        if usage_sections:
            lines.extend(["", "## 使用场景", ""])
            _render_blocks(lines, usage_sections)
        if procedure_sections:
            lines.extend(["", "## 操作/配置", ""])
            _render_blocks(lines, procedure_sections)
        elif content["answer"]:
            lines.extend(["", "## 操作/配置", ""])
            lines.extend(f"- {line}" for _, line in content["answer"])
        if diagnostic_sections:
            lines.extend(["", "## 排查路径", ""])
            _render_blocks(lines, diagnostic_sections)
    lines.extend(["", "## 规则和边界", ""])
    if boundary_sections:
        _render_blocks(lines, boundary_sections)
    elif content["boundary"]:
        lines.extend(f"- {line}" for _, line in content["boundary"])
    else:
        lines.append("- 来源没有单独给出边界，本页不额外推断。")
    lines.extend(["", "## 相关主题", ""])
    if related:
        for row in related:
            href = _relative_link(PurePosixPath(topic["page_path"]), PurePosixPath(row["page_path"]))
            lines.append(f"- [{row['title']}]({href})")
    else:
        lines.append("- 当前没有已确认的直接相关主题。")
    lines.extend(["", "## 来源（简表）", ""])
    for source in source_entries:
        ref = PurePosixPath("references/sources") / f"{source['source_id']}.md"
        lines.append(f"- [{source['title']}]({_relative_link(PurePosixPath(topic['page_path']), ref)})")
    body = "\n".join(lines).rstrip() + "\n"
    registry = page_types.get(str(topic.get("page_type")), {}) if isinstance(page_types, Mapping) else {}
    required_sections = registry.get("required_sections", []) if isinstance(registry, Mapping) else []
    missing_sections = [section for section in required_sections if f"## {section}" not in body]
    if missing_sections:
        raise Task4ReaderError(f"page type {topic.get('page_type')} missing sections: {', '.join(missing_sections)}", code="page_type_sections_missing")
    if len(body.splitlines()) > max_lines:
        raise Task4ReaderError(f"topic page exceeds {max_lines} lines: {topic['page_path']}", code="page_limit")
    if _LEAK_RE.search(body):
        raise Task4ReaderError(f"Reader field leakage: {topic['page_path']}", code="reader_leakage")
    return body


def _split_rendered_page(topic: Mapping[str, Any], body: str, max_lines: int) -> list[tuple[str, str]]:
    """Split an edited page at section/subsection boundaries, never at table rows when avoidable."""
    lines = body.rstrip().splitlines()
    title = lines[:1]
    sections: list[tuple[str, list[str]]] = []
    current: list[str] = []
    heading = ""
    for line in lines[1:]:
        if line.startswith("## "):
            if current:
                sections.append((heading, current))
            heading = line[3:].strip()
            current = [line]
        elif current:
            current.append(line)
    if current:
        sections.append((heading, current))
    if not sections:
        return [(str(topic["page_path"]), body)]
    summary = [section for section in sections if section[0] in {"Summary", "答案"}]
    footer = [section for section in sections if section[0] in {"相关主题", "来源（简表）"}]
    content = [section for section in sections if section not in summary and section not in footer]
    priority = {"使用场景": 0, "规则和边界": 1, "排查路径": 2, "操作/配置": 3}
    content.sort(key=lambda item: (priority.get(item[0], 4), sections.index(item)))
    reserved = 12
    chunks: list[list[str]] = []
    current_chunk = [*title]
    for heading, section_lines in [*summary, *content]:
        if len(current_chunk) + len(section_lines) + reserved <= max_lines or current_chunk == title:
            if len(current_chunk) + len(section_lines) + reserved <= max_lines:
                current_chunk.extend(section_lines)
                continue
        chunks.append(current_chunk)
        current_chunk = [*title, *section_lines]
        if len(current_chunk) + reserved > max_lines:
            # A single section can still be large.  Split only between lines;
            # Markdown table rows stay intact because every row is one line.
            footer_budget = sum(len(section_lines) + 2 for _, section_lines in footer)
            body_budget = max(1, max_lines - reserved - footer_budget - 2)
            for offset in range(0, len(section_lines), body_budget):
                fragment = [*title, *section_lines[offset:offset + body_budget]]
                if current_chunk == [*title, *section_lines]:
                    current_chunk = fragment
                else:
                    chunks.append(current_chunk)
                    current_chunk = fragment
    if current_chunk != title:
        chunks.append(current_chunk)
    if not chunks:
        chunks = [title]
    base = str(topic["page_path"])
    stem, suffix = base.rsplit(".", 1)
    paths = [base if index == 0 else f"{stem}.part-{index + 1}.{suffix}" for index in range(len(chunks))]
    links = [f"- [{index + 1}]({Path(paths[index]).name})" for index in range(len(paths))]
    rendered: list[tuple[str, str]] = []
    for index, chunk in enumerate(chunks):
        page_lines = list(chunk)
        if len(chunks) > 1 and index == 0:
            page_lines.extend(["", "## 分段阅读", "", *links])
        if len(chunks) > 1 and index > 0:
            page_lines.extend(["", "## 分段阅读", "", f"- [第 1 段]({Path(paths[0]).name})"])
        # Keep a source anchor on every part so the entry page remains a valid
        # comparison target while deeper parts carry the full body.
        for heading, section_lines in footer:
            page_lines.extend(["", *section_lines])
        rendered.append((paths[index], "\n".join(page_lines).rstrip() + "\n"))
    if any(len(page.splitlines()) > max_lines for _, page in rendered):
        raise Task4ReaderError(f"cannot safely split topic page: {topic['page_path']}", code="page_limit")
    return rendered


def _write_failure(output: Path, run: Mapping[str, Any], failures: list[Mapping[str, Any]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    # A failed or cancelled rerun must not destroy the last readable bundle.
    # The status explicitly says that the preserved bundle is not the current
    # run's release, so callers cannot mistake it for a successful publish.
    preserved = (output / "bundle").exists() or (output / "bundle").is_symlink()
    _write_json(output / "reports/run-manifest.json", run)
    _write_json(output / "status.json", {"schema_version": SCHEMA_VERSION, "reader_bundle_preserved": preserved, **dict(run)})
    _write_jsonl(output / "audit/failures.jsonl", failures)


def _publish(staging: Path, output: Path, names: Iterable[str]) -> None:
    # Stage all replacements under the same output filesystem and keep a
    # rollback copy until every requested top-level tree is installed.  This
    # avoids a half-published Reader when one replacement fails.
    publish_backup = staging / ".publish-backup"
    publish_backup.mkdir(parents=True, exist_ok=True)
    backed_up: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for name in names:
            destination = output / name
            source = staging / name
            backup = publish_backup / name
            if destination.exists() or destination.is_symlink():
                backup.parent.mkdir(parents=True, exist_ok=True)
                # Register the rollback intent before the rename.  A signal
                # can arrive after os.replace moved the old tree but before
                # Python gets to the next statement.
                backed_up.append((destination, backup))
                os.replace(destination, backup)
            if source.exists() or source.is_symlink():
                # Register before the rename for the same signal window: if
                # the new tree was installed, rollback must remove it.
                installed.append(destination)
                os.replace(source, destination)
        shutil.rmtree(publish_backup, ignore_errors=True)
    except BaseException:
        for destination in reversed(installed):
            if destination.is_symlink() or destination.is_file():
                destination.unlink()
            elif destination.is_dir():
                shutil.rmtree(destination)
        for destination, backup in reversed(backed_up):
            if backup.exists() or backup.is_symlink():
                os.replace(backup, destination)
        raise


def compile_full_reader(raw_input: Path, output: Path, config: Path | Mapping[str, Any] | None = None, *, cancel_check: Callable[[], bool] | None = None) -> dict[str, Any]:
    raw_root = Path(raw_input)
    out = Path(output)
    run_id = _run_id()
    lock_handle = None
    lock_acquired = False
    staging: Path | None = None
    base_reader_generation: str | None = None
    try:
        contract = _load_config(config)
        if out.exists() and not out.is_dir():
            raise Task4ReaderError(f"output is not a directory: {out}", code="output_unwritable")
        out.mkdir(parents=True, exist_ok=True)
        lock_path = out / ".staging/.compile.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_handle = lock_path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_handle.close()
            lock_handle = None
            return {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "failed", "package_status": NOT_RELEASED, "reason_code": "output_busy", "reason": f"another compile is using {out}"}
        lock_acquired = True
        if (out / "status.json").is_file():
            try:
                previous_status = _read_json(out / "status.json")
            except Task4ReaderError as exc:
                raise Task4ReaderError(f"current Reader status is invalid: {exc}", code="base_reader_invalid") from exc
            value = previous_status.get("input_manifest_generation")
            base_reader_generation = str(value) if value else None
        if cancel_check and cancel_check():
            run = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "cancelled", "package_status": NOT_RELEASED, "reason_code": "cancelled"}
            _write_failure(out, run, [{"reason_code": "cancelled", "reason": "cancelled before source read"}])
            return run
        sources, failures = _collect_sources(raw_root, contract, cancel_check=cancel_check)
        if cancel_check and cancel_check():
            raise KeyboardInterrupt
        expected = contract["source_coverage"].get("expected_count")
        manifest_rows = [{key: value for key, value in row.items() if key not in {"text", "body", "metadata", "content"}} for row in sources]
        manifest_rows.extend(failures)
        manifest_rows.sort(key=lambda row: str(row.get("source_uri", "")))
        input_manifest_generation = _sha256_json([(row.get("source_uri"), row.get("content_hash"), row.get("source_id")) for row in manifest_rows])
        coverage_failures: list[dict[str, Any]] = []
        if expected is not None and len(manifest_rows) != expected:
            coverage_failures.append({"reason_code": "source_count_mismatch", "expected": expected, "actual": len(manifest_rows)})
        expected_hash = contract["source_coverage"].get("manifest_hash")
        fixture = contract.get("source_coverage_fixture_data")
        if isinstance(fixture, Mapping) and isinstance(fixture.get("entries"), list):
            observed_entries = [
                {key: row.get(key) for key in ("source_uri", "source_id", "content_hash", "byte_count")}
                for row in manifest_rows
            ]
            expected_entries = [
                {key: row.get(key) for key in ("source_uri", "source_id", "content_hash", "byte_count")}
                for row in fixture["entries"]
                if isinstance(row, Mapping)
            ]
            observed_entries.sort(key=lambda row: str(row.get("source_uri", "")))
            expected_entries.sort(key=lambda row: str(row.get("source_uri", "")))
            if observed_entries != expected_entries:
                coverage_failures.append({"reason_code": "manifest_drift", "expected_manifest_hash": fixture.get("manifest_hash"), "expected_count": len(expected_entries), "observed_count": len(observed_entries), "actual_generation": input_manifest_generation})
        elif expected_hash and expected_hash != input_manifest_generation:
            coverage_failures.append({"reason_code": "manifest_drift", "expected": expected_hash, "actual": input_manifest_generation})
        failures.extend(coverage_failures)

        grouped: dict[str, list[dict[str, Any]]] = {}
        for source in sources:
            if cancel_check and cancel_check():
                raise KeyboardInterrupt
            if source.get("status") == "not_applicable":
                continue
            grouped.setdefault(str(source["topic_key"]), []).append(source)
        nodes: list[dict[str, Any]] = []
        topics: list[dict[str, Any]] = []
        relations: list[dict[str, Any]] = []
        for topic_key, rows in sorted(grouped.items()):
            if cancel_check and cancel_check():
                raise KeyboardInterrupt
            node = _semantic_node(topic_key, rows, contract)
            nodes.append(node)
            if node["status"] != "supported":
                failures.append({"reason_code": "topic_conflict" if node["status"] == "conflict" else "semantic_pending", "topic_key": topic_key, "reasons": node["reasons"], "source_uris": [row["source_uri"] for row in rows]})
                continue
            canonical = rows[0]
            topic = {
                "topic_id": f"topic-{_sha256_bytes(topic_key.encode('utf-8'))[:16]}",
                "canonical_case_id": str(canonical.get("metadata", {}).get("canonical_case_id") or topic_key),
                "topic_key": topic_key,
                "title": canonical["title"],
                "product": canonical["product"],
                "module": canonical["module"],
                "page_type": node["page_type"],
                "source_ids": [row["source_id"] for row in rows],
                "sources": rows,
                "content": _merge_content(rows),
            }
            topic["page_path"] = _topic_page_path(topic)
            topics.append(topic)
        for topic in topics:
            if cancel_check and cancel_check():
                raise KeyboardInterrupt
            for related in _related(topic, topics, contract):
                source_evidence = [
                    {
                        "source_id": source["source_id"],
                        "source_uri": source["source_uri"],
                        "content_hash": source.get("content_hash"),
                        "snapshot_ref": f"audit/source-snapshots/{source['source_id']}{Path(source['source_uri']).suffix}",
                    }
                    for source in topic["sources"]
                ]
                target_evidence = [
                    {
                        "source_id": source["source_id"],
                        "source_uri": source["source_uri"],
                        "content_hash": source.get("content_hash"),
                        "snapshot_ref": f"audit/source-snapshots/{source['source_id']}{Path(source['source_uri']).suffix}",
                    }
                    for source in related["sources"]
                ]
                relations.append({
                    "relation_id": f"relation-{topic['topic_id']}-{related['topic_id']}",
                    "relation_type": "related",
                    "source_topic_id": topic["topic_id"],
                    "target_topic_id": related["topic_id"],
                    "evidence_status": "configured",
                    "evidence": {"source_topic": source_evidence, "target_topic": target_evidence},
                })
        for row in manifest_rows:
            match = next((topic for topic in topics if row.get("source_id") in topic["source_ids"]), None)
            row["target_path"] = match["page_path"] if match else None
            row["canonical_topic_id"] = match["topic_id"] if match else None
        package_status = "candidate" if not failures and topics else NOT_RELEASED
        run = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "status": "completed",
            "package_status": package_status,
            "source_count": len(manifest_rows),
            "expected_source_count": expected,
            "reader_source_count": sum(1 for row in manifest_rows if row.get("target_path")),
            "topic_count": len(topics),
            "failure_count": len(failures),
            "input_manifest_generation": input_manifest_generation,
            "config_generation": contract["config_generation"],
            "base_reader_generation": base_reader_generation,
            "bundle_ref": "bundle" if package_status == "candidate" else None,
        }
        staging = out / ".staging" / run_id
        root = staging / "bundle"
        (root / "references/sources").mkdir(parents=True, exist_ok=True)
        (staging / "audit/source-snapshots").mkdir(parents=True, exist_ok=True)
        topic_rows: list[dict[str, Any]] = []
        claim_rows: list[dict[str, Any]] = []
        if package_status == "candidate":
            for topic in topics:
                if cancel_check and cancel_check():
                    raise KeyboardInterrupt
                related = _related(topic, topics, contract)
                max_page_lines = int(contract.get("max_page_lines", 300))
                # Render the complete edited body first.  Only then split it
                # into reader parts; no source block is silently truncated.
                full_body = _render_page(topic, related, topic["sources"], 10**9, contract.get("page_types", {}))
                page_specs = [(topic["page_path"], full_body)]
                if len(full_body.splitlines()) > max_page_lines:
                    page_specs = _split_rendered_page(topic, full_body, max_page_lines)
                page_paths: list[str] = []
                for page_path, body in page_specs:
                    if cancel_check and cancel_check():
                        raise KeyboardInterrupt
                    page = root / page_path
                    page.parent.mkdir(parents=True, exist_ok=True)
                    page.write_text(body, encoding="utf-8")
                    page_paths.append(page_path)
                topic_rows.append({**{key: topic[key] for key in ("topic_id", "canonical_case_id", "topic_key", "title", "product", "module", "page_type", "page_path", "source_ids")}, "page_paths": page_paths})
                for source in topic["sources"]:
                    if cancel_check and cancel_check():
                        raise KeyboardInterrupt
                    snapshot = staging / "audit/source-snapshots" / f"{source['source_id']}{Path(source['source_uri']).suffix}"
                    snapshot.write_text(source["text"], encoding="utf-8")
                    ref = root / "references/sources" / f"{source['source_id']}.md"
                    ref.write_text(f"# {source['title']}\n\n本来源支撑主题：{topic['title']}。\n\n此页只保留读者可见的来源说明。\n", encoding="utf-8")
                    for claim in source["content"]["claims"]:
                        claim_rows.append({**claim, "topic_id": topic["topic_id"], "target_path": topic["page_path"], "ownership": "canonical"})
            for source in sources:
                if source.get("status") != "not_applicable":
                    continue
                snapshot = staging / "audit/source-snapshots" / f"{source['source_id']}{Path(source['source_uri']).suffix}"
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                snapshot.write_text(source["text"], encoding="utf-8")
        else:
            for source in sources:
                snapshot = staging / "audit/source-snapshots" / f"{source['source_id']}{Path(source['source_uri']).suffix}"
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                snapshot.write_text(source["text"], encoding="utf-8")
        # Candidate navigation is generated only after every topic page is ready.
        if package_status == "candidate":
            products: dict[str, list[dict[str, Any]]] = {}
            for topic in topics:
                products.setdefault(_clean_segment(topic["product"]), []).append(topic)
            (root / "Home.md").write_text("# Home\n\n- [产品入口](products/index.md)\n", encoding="utf-8")
            (root / "README.md").write_text("# Reader\n\n这是本次运行生成的候选 Reader。\n", encoding="utf-8")
            product_root = root / "products"
            product_root.mkdir(parents=True, exist_ok=True)
            product_lines = ["# 产品", ""]
            for product_slug, product_topics in sorted(products.items()):
                product_dir = product_root / product_slug
                product_dir.mkdir(parents=True, exist_ok=True)
                product_index_path = PurePosixPath(f"products/{product_slug}/index.md")
                product_lines.append(f"- [{product_topics[0]['product']}]({product_slug}/index.md)")
                module_groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
                for topic in product_topics:
                    parts = tuple(_module_path_parts(topic["module"]))
                    for depth in range(1, len(parts) + 1):
                        module_groups.setdefault(parts[:depth], [])
                    module_groups[parts].append(topic)

                # Build indexes for every taxonomy prefix.  This keeps the
                # reader route hierarchical even when a rule has three
                # levels (for example EMM/Android/策略与配置).
                for module_parts in sorted(module_groups):
                    module_dir = product_dir.joinpath(*module_parts)
                    module_dir.mkdir(parents=True, exist_ok=True)
                    module_index_path = PurePosixPath(f"products/{product_slug}", *module_parts, "index.md")
                    module_index = [f"# {module_parts[-1]}", ""]
                    child_prefixes = sorted(
                        child for child in module_groups
                        if len(child) == len(module_parts) + 1 and child[: len(module_parts)] == module_parts
                    )
                    for child in child_prefixes:
                        child_path = PurePosixPath(f"products/{product_slug}", *child, "index.md")
                        module_index.append(f"- [{child[-1]}]({_relative_link(module_index_path, child_path)})")
                    for topic in sorted(module_groups[module_parts], key=lambda item: item["title"]):
                        module_index.append(f"- [{topic['title']}]({_relative_link(module_index_path, PurePosixPath(topic['page_path']))})")
                    (module_dir / "index.md").write_text("\n".join(module_index) + "\n", encoding="utf-8")

                product_index = [f"# {product_topics[0]['product']}", ""]
                for module_parts in sorted(module_groups):
                    if len(module_parts) != 1:
                        continue
                    module_path = PurePosixPath(f"products/{product_slug}", *module_parts, "index.md")
                    product_index.append(f"- [{module_parts[0]}]({_relative_link(product_index_path, module_path)})")
                (product_dir / "index.md").write_text("\n".join(product_index) + "\n", encoding="utf-8")
            (product_root / "index.md").write_text("\n".join(product_lines) + "\n", encoding="utf-8")
        reports = staging / "reports"
        _write_json(reports / "source-manifest.json", {"schema_version": "task4-source-manifest.v2", "run_id": run_id, "source_count": len(manifest_rows), "entries": manifest_rows})
        _write_json(reports / "topic-index.json", {"schema_version": "task4-topic-index.v2", "run_id": run_id, "topics": topic_rows})
        _write_json(reports / "claim-ledger.json", {"schema_version": "task4-claim-ledger.v2", "run_id": run_id, "claim_count": len(claim_rows), "claims": claim_rows})
        _write_json(reports / "relation-ledger.json", {"schema_version": "task4-relation-ledger.v1", "run_id": run_id, "relations": relations})
        _write_json(reports / "semantic-nodes.json", {"schema_version": "task4-semantic-nodes.v1", "run_id": run_id, "nodes": nodes})
        _write_json(staging / "audit/semantic-nodes.json", {"schema_version": "task4-semantic-nodes.v1", "run_id": run_id, "nodes": nodes})
        relation_source_ids = {
            str(source.get("source_id"))
            for relation in relations
            for side in ("source_topic", "target_topic")
            for source in relation.get("evidence", {}).get(side, [])
            if source.get("source_id")
        }
        relation_evidence_valid = all(
            relation.get("evidence_status") == "configured"
            and all(source.get("source_id") and source.get("source_uri") and source.get("content_hash") and source.get("snapshot_ref") for side in ("source_topic", "target_topic") for source in relation.get("evidence", {}).get(side, []))
            for relation in relations
        )
        coverage_rows = []
        for row in manifest_rows:
            coverage_status = "not_applicable" if row.get("status") == "not_applicable" else ("passed" if row.get("target_path") else "failed")
            coverage_rows.append({"source_id": row.get("source_id"), "source_uri": row.get("source_uri"), "target_path": row.get("target_path"), "checks": {"coverage": bool(row.get("source_id")), "title": bool(row.get("title")), "classification": row.get("classification_status") == "classified", "body": row.get("status") not in {"failed", "not_applicable"}, "relations": row.get("source_id") not in relation_source_ids or relation_evidence_valid, "navigation": bool(row.get("target_path")), "provenance": bool(row.get("content_hash"))}, "status": coverage_status, "reason_code": row.get("reason_code")})
            _write_json(reports / "coverage-report.json", {"schema_version": "task4-coverage-report.v1", "run_id": run_id, "source_count": len(manifest_rows), "rows": coverage_rows})
        _write_json(reports / "taxonomy-report.json", {"schema_version": "task4-taxonomy-report.v1", "run_id": run_id, "rows": [{key: row.get(key) for key in ("source_id", "source_uri", "title", "product", "module", "classification_status", "classification_rule_id", "target_path")} for row in manifest_rows]})
        _write_json(reports / "run-manifest.json", run)
        _write_json(staging / "audit/package-status.json", {"schema_version": "task4-package-status.v2", "status": package_status, "run_id": run_id, "reason": [failure.get("reason_code") for failure in failures]})
        _write_json(staging / "status.json", {"schema_version": SCHEMA_VERSION, "reader_bundle_preserved": package_status != "candidate" and ((out / "bundle").exists() or (out / "bundle").is_symlink()), **run})
        _write_jsonl(staging / "audit/failures.jsonl", failures)
        _write_jsonl(staging / "audit/semantic-decisions.jsonl", nodes)
        if cancel_check and cancel_check():
            raise KeyboardInterrupt
        if base_reader_generation is not None and (out / "status.json").is_file():
            current_status = _read_json(out / "status.json")
            if current_status.get("input_manifest_generation") != base_reader_generation:
                raise Task4ReaderError("Reader baseline changed during compile", code="base_reader_changed")
        if package_status == "candidate":
            _publish(staging, out, ("bundle", "audit", "reports", "status.json"))
        else:
            # Keep any previous bundle as an explicitly non-current snapshot;
            # a failed rerun must not erase the last readable result.
            _publish(staging, out, ("audit", "reports", "status.json"))
        shutil.rmtree(staging, ignore_errors=True)
        return {**run, "status": package_status}
    except KeyboardInterrupt:
        run = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "cancelled", "package_status": NOT_RELEASED, "reason_code": "cancelled"}
        # The status file is installed last.  If an interrupt arrives after
        # that point, the publish transaction is already complete; rewriting
        # status/audit here would create a new bundle with a cancelled run.
        try:
            current_status = _read_json(out / "status.json") if (out / "status.json").is_file() else {}
        except Task4ReaderError:
            current_status = {}
        if current_status.get("run_id") == run_id:
            package_status = str(current_status.get("package_status") or NOT_RELEASED)
            return {**run, "status": package_status, "package_status": package_status, "reason_code": "post_publish_interrupt", "bundle_ref": "bundle" if package_status == "candidate" else None}
        _write_failure(out, run, [{"reason_code": "cancelled", "reason": "cancelled or interrupted"}])
        return run
    except (Task4ReaderError, OSError, UnicodeError) as exc:
        run = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "failed", "package_status": NOT_RELEASED, "reason_code": getattr(exc, "code", "io_error"), "reason": str(exc)}
        if not out.exists() or out.is_dir():
            _write_failure(out, run, [{"reason_code": run["reason_code"], "reason": str(exc)}])
        return run
    finally:
        if lock_acquired:
            if staging and staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            if lock_handle is not None:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
                lock_handle.close()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Task4ReaderError(f"cannot read JSON artifact: {path}: {exc}", code="artifact_invalid") from exc
    if not isinstance(value, dict):
        raise Task4ReaderError(f"JSON artifact must be an object: {path}", code="artifact_invalid")
    return value


def _assessment_root(candidate: Path) -> Path:
    candidate = Path(candidate)
    if (candidate / "reports/topic-index.json").is_file() and (candidate / "bundle").is_dir():
        return candidate / "bundle"
    if (candidate / "reports/topic-index.json").is_file():
        return candidate
    raise Task4ReaderError(f"candidate reports are missing: {candidate}", code="candidate_invalid")


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            rows.append((path.relative_to(root).as_posix(), _sha256_bytes(path.read_bytes())))
    return _sha256_json(rows)


def _reader_links(path: str, text: str) -> list[str]:
    targets: list[str] = []
    for raw in re.findall(r"\]\(([^)]+)\)", text):
        target = raw.split("#", 1)[0].strip()
        if target.startswith(("http:", "https:", "/", "mailto:")):
            continue
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), unquote(target)))
        if resolved.endswith(".md"):
            targets.append(resolved)
    for raw in re.findall(r"(?<!!)\[\[([^\]]+)\]\]", text):
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if not target or target.startswith(("/", "http:")):
            continue
        if not target.endswith(".md"):
            target += ".md"
        targets.append(posixpath.normpath(posixpath.join(posixpath.dirname(path), target)))
    return list(dict.fromkeys(targets))


def _route(root: Path, target: Path | str | None) -> dict[str, Any]:
    root = Path(root)
    if target is None:
        return {"reachable": False, "first_hit_page": None, "hop_count": None, "path": []}
    target_rel = Path(target).relative_to(root).as_posix() if Path(target).is_absolute() else str(target).replace("\\", "/")
    files = {path.relative_to(root).as_posix(): path for path in root.rglob("*.md") if path.is_file() and not path.is_symlink()}
    if "Home.md" not in files or target_rel not in files:
        return {"reachable": False, "first_hit_page": target_rel, "hop_count": None, "path": []}
    queue: list[tuple[str, list[str]]] = [("Home.md", ["Home.md"])]
    seen = {"Home.md"}
    while queue:
        current, route = queue.pop(0)
        if current == target_rel:
            return {"reachable": True, "first_hit_page": target_rel, "hop_count": len(route) - 1, "path": route, "first_hit": target_rel}
        for link in _reader_links(current, files[current].read_text(encoding="utf-8")):
            if link in files and link not in seen:
                seen.add(link)
                queue.append((link, route + [link]))
    return {"reachable": False, "first_hit_page": target_rel, "hop_count": None, "path": [], "first_hit": "no_match"}


def _page_text(root: Path, relative: str | None) -> tuple[Path | None, str]:
    if not relative:
        return None, ""
    path = root / relative
    if not path.is_file() or path.is_symlink():
        return None, ""
    return path, path.read_text(encoding="utf-8")


def _load_quality_config(path: Path) -> tuple[dict[str, Any], str]:
    value = _read_json(path)
    if value.get("schema_version") != SCHEMA_VERSION:
        raise Task4ReaderError("quality config schema is invalid", code="quality_config_invalid")
    config_dir = path.parent
    for key, fixture_key in (("source_coverage", "source_coverage_fixture"), ("case_matrix", "case_matrix_fixture")):
        fixture = value.get(fixture_key)
        if not fixture:
            continue
        fixture_value = _read_json(config_dir / str(fixture))
        if key == "source_coverage":
            value[key] = {**fixture_value, **dict(value.get(key) or {})}
        else:
            value[key] = fixture_value
    evaluator_fixture = value.get("evaluator_fixture")
    if evaluator_fixture:
        value["evaluator"] = _read_json(config_dir / str(evaluator_fixture))
    page_type_fixture = value.get("page_type_fixture")
    if page_type_fixture:
        page_registry = _read_json(config_dir / str(page_type_fixture))
        value["page_types"] = page_registry.get("page_types", page_registry)
    mapping_fixture = value.get("companybrain_mapping_fixture")
    if mapping_fixture:
        mapping = _read_json(config_dir / str(mapping_fixture))
        if mapping.get("schema_version") not in {"task4-companybrain-mapping.v1", "task4-companybrain-mapping.v2", "task4-companybrain-mapping.v3"} or not isinstance(mapping.get("cases"), list):
            raise Task4ReaderError("CompanyBrain mapping fixture is invalid", code="quality_config_invalid")
        value["companybrain_mapping"] = mapping
    matrix = value.get("case_matrix")
    cases = matrix.get("cases") if isinstance(matrix, Mapping) else None
    source_map = matrix.get("source_to_case_map") if isinstance(matrix, Mapping) else None
    if not isinstance(cases, list) or not cases or not isinstance(source_map, list):
        raise Task4ReaderError("case matrix is missing cases or source map", code="case_oracle_invalid")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, Mapping) or not case.get("case_id") or case.get("case_id") in seen:
            raise Task4ReaderError("case matrix has duplicate or invalid case", code="case_oracle_invalid")
        seen.add(str(case["case_id"]))
        if not isinstance(case.get("required_claims"), list) or not case["required_claims"] or not isinstance(case.get("required_boundaries"), list) or not case["required_boundaries"]:
            raise Task4ReaderError(f"case oracle is incomplete: {case.get('case_id')}", code="case_oracle_invalid")
        if case.get("source_status") not in {None, "not_applicable"}:
            raise Task4ReaderError(f"case oracle has unsupported source status: {case.get('case_id')}", code="case_oracle_invalid")
        if case.get("source_status") == "not_applicable" and not case.get("source_status_reason"):
            raise Task4ReaderError(f"case oracle missing source status reason: {case.get('case_id')}", code="case_oracle_invalid")
    return value, _sha256_json(value)


def _score_terms(text: str, terms: list[Any]) -> tuple[float, list[dict[str, Any]]]:
    checks = [{"term": str(term), "status": "covered" if str(term).casefold() in text.casefold() else "missing"} for term in terms]
    return (sum(row["status"] == "covered" for row in checks) / len(checks) if checks else 0.0), checks


def _has_source_anchor(text: str) -> bool:
    return bool(re.search(r"(?im)^##\s+(?:来源(?:索引|线索)?(?:（简表）)?|sources?)\s*$", text))


def _case_side(
    root: Path,
    target_path: str | None,
    case: Mapping[str, Any],
    *,
    home: str,
    additional_paths: Iterable[str] = (),
    baseline: bool = False,
) -> dict[str, Any]:
    if target_path is None:
        return {"status": "not_applicable", "home": home, "first_hit_page": None, "route": [], "hop_count": None, "answer_score": 0.0, "boundary_score": 0.0, "claim_checks": [], "boundary_checks": [], "source_anchor": False}
    page, text = _page_text(root, target_path)
    # A long topic is one reader unit even when the compiler split its body
    # into bounded parts.  Score the complete topic while keeping the main
    # page as the canonical first-hit route target.
    for extra_path in additional_paths:
        if str(extra_path) == target_path:
            continue
        extra_page, extra_text = _page_text(root, str(extra_path))
        if extra_page is not None:
            text += "\n" + extra_text
    route = _route(root, target_path)
    answer_score, claim_checks = _score_terms(text, list(case.get("required_claims", [])))
    boundary_score, boundary_checks = _score_terms(text, list(case.get("required_boundaries", [])))
    # The comparison contract requires the same explicit short-source section
    # on both sides.  A generic ``## 来源`` heading is not enough evidence.
    source_anchor = _has_source_anchor(text)
    boundary_checks.append({"term": "source_anchor", "status": "covered" if source_anchor else "missing"})
    boundary_score = (sum(row["status"] == "covered" for row in boundary_checks) / len(boundary_checks)) if boundary_checks else 0.0
    if not page:
        status = "missing"
    elif not route.get("reachable"):
        # The page exists, but the frozen baseline reader does not expose it
        # from Home.  That is an observed baseline navigation defect, not an
        # unknown mapping; retain it so KD can be measured against the real
        # baseline behavior.
        status = "issue"
    else:
        covered = all(row["status"] == "covered" for row in claim_checks + boundary_checks)
        status = "covered" if covered else ("issue" if baseline else "missing")
    return {"status": status, "home": home, "first_hit_page": target_path if page else None, "route": route.get("path", []), "hop_count": route.get("hop_count"), "answer_score": answer_score, "boundary_score": boundary_score, "claim_checks": claim_checks, "boundary_checks": boundary_checks, "source_anchor": source_anchor}


def _root_cause_items(candidate: Path, rows: list[Mapping[str, Any]], blocking: list[str]) -> list[dict[str, Any]]:
    """Write observed causes, not a fixed list of generic audit labels."""
    candidate = Path(candidate)
    missing_reports: list[str] = []

    def read_report(relative: str, default: Mapping[str, Any]) -> Mapping[str, Any]:
        path = candidate / relative
        if not path.is_file():
            missing_reports.append(relative)
            return default
        try:
            value = _read_json(path)
        except (Task4ReaderError, OSError, UnicodeError):
            missing_reports.append(relative)
            return default
        return value

    coverage = read_report("reports/coverage-report.json", {})
    topic_index = read_report("reports/topic-index.json", {})
    taxonomy = read_report("reports/taxonomy-report.json", {})
    relation_ledger = read_report("reports/relation-ledger.json", {})
    failures = []
    failure_path = candidate / "audit/failures.jsonl"
    if failure_path.is_file():
        try:
            failures = [json.loads(line) for line in failure_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, UnicodeError, json.JSONDecodeError):
            missing_reports.append("audit/failures.jsonl")
    else:
        missing_reports.append("audit/failures.jsonl")

    topic_rows = [row for row in topic_index.get("topics", []) if isinstance(row, Mapping)]
    coverage_rows = [row for row in coverage.get("rows", []) if isinstance(row, Mapping)]
    taxonomy_rows = [row for row in taxonomy.get("rows", []) if isinstance(row, Mapping)]
    source_refs = [str(row.get("source_uri")) for row in failures if row.get("source_uri")]
    source_count = len(coverage_rows)
    failed_sources = [row for row in coverage_rows if row.get("status") != "passed"]
    opaque_names = [
        str(row.get("page_path"))
        for row in topic_rows
        if any(token in str(row.get("page_path")) for token in ("ae-", "cluster-", "draft-"))
    ]
    generic_paths = [
        str(row.get("target_path"))
        for row in taxonomy_rows
        if "通用" in str(row.get("module")) or "/通用/" in str(row.get("target_path"))
    ]
    body_issue_cases = [
        str(row.get("case_id"))
        for row in rows
        if row.get("knowledge_digest", {}).get("status") != "covered"
        or any(check.get("status") != "covered" for check in row.get("knowledge_digest", {}).get("claim_checks", []))
    ]
    navigation_issue_cases = [
        str(row.get("case_id"))
        for row in rows
        if not row.get("knowledge_digest", {}).get("route")
        or row.get("knowledge_digest", {}).get("first_hit_page") is None
    ]
    provenance_issue_cases = [
        str(row.get("case_id"))
        for row in rows
        if not row.get("knowledge_digest", {}).get("source_anchor")
    ]
    relations = [row for row in relation_ledger.get("relations", []) if isinstance(row, Mapping)]
    relation_issue_ids = [
        str(row.get("relation_id"))
        for row in relations
        if row.get("evidence_status") != "configured"
        or not row.get("evidence", {}).get("source_topic")
        or not row.get("evidence", {}).get("target_topic")
    ]
    run_manifest = read_report("reports/run-manifest.json", {})
    source_manifest = read_report("reports/source-manifest.json", {})
    run_id = str(run_manifest.get("run_id") or source_manifest.get("run_id") or "")
    config_generation = str(run_manifest.get("config_generation") or "")
    source_identity = _companybrain_source_manifest_hash(source_manifest)
    input_issue = bool(missing_reports)

    def item(
        dimension: str,
        symptom: str,
        evidence_refs: list[str],
        first_failing_stage: str,
        case_refs: list[str],
        source_refs_for_item: list[str],
        issue: bool,
    ) -> dict[str, Any]:
        if input_issue:
            first_failing_stage = "root_cause_input" if first_failing_stage == "none_observed" else first_failing_stage
            issue = True
        return {
            "dimension": dimension,
            "symptom": symptom,
            "evidence_ref": evidence_refs[0] if evidence_refs else None,
            "evidence_refs": evidence_refs,
            "first_failing_stage": first_failing_stage,
            "case_refs": sorted(set(case_refs)),
            "source_refs": sorted(set(source_refs_for_item)),
            "change_ref": "task4-reader-quality-compiler:current-machine-run",
            "rerun_result": (
                "blocked: missing or invalid " + ", ".join(sorted(set(missing_reports)))
                if input_issue
                else "issue remains in current run" if issue else "current run has no observed issue"
            ),
            "status": "issue" if issue else "pass",
            "run_id": run_id or None,
            "config_generation": config_generation or None,
            "source_manifest_hash": source_identity,
        }

    return [
        item(
            "structure",
            f"输入 {source_count} 条，{len(topic_rows)} 条进入 Reader，{len(failed_sources)} 条未进入。",
            ["reports/coverage-report.json", "audit/failures.jsonl"],
            "ingest/coverage" if failed_sources else "none_observed",
            [],
            source_refs,
            bool(failed_sources) or "source_count_mismatch" in blocking,
        ),
        item(
            "naming",
            f"{len(opaque_names)} 个主题路径仍含内部或不透明命名片段。",
            ["reports/topic-index.json"],
            "semantic_title_and_path" if opaque_names else "none_observed",
            [],
            opaque_names,
            bool(opaque_names),
        ),
        item(
            "classification",
            f"{len(generic_paths)} 个主题仍落入通用分类。",
            ["reports/taxonomy-report.json"],
            "semantic_classification" if generic_paths else "none_observed",
            [],
            generic_paths,
            bool(generic_paths),
        ),
        item(
            "body",
            f"{len(body_issue_cases)} 个对照案例的 Reader 正文未完整覆盖机器要求。",
            ["reports/comparison-table.json"],
            "reader_body_evaluator" if body_issue_cases else "none_observed",
            body_issue_cases,
            [],
            bool(body_issue_cases) or "case_evidence_missing" in blocking,
        ),
        item(
            "relations",
            f"共 {len(relations)} 条关系，{len(relation_issue_ids)} 条缺少来源绑定证据。",
            ["reports/relation-ledger.json"],
            "relation_evidence_binding" if relation_issue_ids else "none_observed",
            relation_issue_ids,
            [],
            bool(relation_issue_ids),
        ),
        item(
            "navigation",
            f"{len(navigation_issue_cases)} 个案例没有从 Home 到达 Reader 首页。",
            ["reports/comparison-table.json", "bundle/Home.md"],
            "reader_navigation_evaluator" if navigation_issue_cases else "none_observed",
            navigation_issue_cases,
            [],
            bool(navigation_issue_cases),
        ),
        item(
            "provenance",
            f"{len(provenance_issue_cases)} 个案例缺少正文来源锚点。",
            ["reports/comparison-table.json", "reports/claim-ledger.json"],
            "reader_provenance_evaluator" if provenance_issue_cases else "none_observed",
            provenance_issue_cases,
            [],
            bool(provenance_issue_cases),
        ),
    ]


def assess_reader_quality(candidate: Path, companybrain: Path, quality_config: Path, output: Path) -> dict[str, Any]:
    out = Path(output)
    try:
        config, config_hash = _load_quality_config(Path(quality_config))
        candidate_root = _assessment_root(Path(candidate))
        baseline_root = Path(companybrain)
        if not baseline_root.is_dir() or baseline_root.is_symlink():
            raise Task4ReaderError("CompanyBrain baseline is missing", code="companybrain_invalid")
        candidate_status = _read_json(Path(candidate) / "status.json")
        if candidate_status.get("package_status") != "candidate":
            raise Task4ReaderError("candidate Reader package is not released for assessment", code="candidate_not_released")
        topic_index = _read_json(Path(candidate) / "reports/topic-index.json")
        topics = topic_index.get("topics", [])
        by_case = {str(row.get("canonical_case_id")): row for row in topics if isinstance(row, Mapping)}
        by_title = {str(row.get("title")): row for row in topics if isinstance(row, Mapping)}
        cases = config["case_matrix"]["cases"]
        source_map_by_case: dict[str, set[str]] = {}
        for mapping in config["case_matrix"].get("source_to_case_map", []):
            if not isinstance(mapping, Mapping) or not mapping.get("case_id"):
                continue
            source_id = mapping.get("source_id")
            if not source_id and mapping.get("source_uri"):
                source_id = f"source-{_sha256_bytes(str(mapping['source_uri']).encode('utf-8'))[:16]}"
            if source_id:
                source_map_by_case.setdefault(str(mapping["case_id"]), set()).add(str(source_id))
        rows: list[dict[str, Any]] = []
        blocking: list[str] = []
        mapping_fixture = config.get("companybrain_mapping")
        mapping_by_case = {str(row.get("case_id")): row for row in mapping_fixture.get("cases", []) if isinstance(row, Mapping)} if isinstance(mapping_fixture, Mapping) else {}
        observed_source_hash = None
        if isinstance(mapping_fixture, Mapping):
            baseline_manifest_hash = str(mapping_fixture.get("companybrain_manifest", {}).get("tree_hash") or "")
            if baseline_manifest_hash != _companybrain_tree_hash(baseline_root):
                blocking.append("baseline_manifest_drift")
            baseline_entries = mapping_fixture.get("companybrain_manifest", {}).get("entries")
            baseline_entries_by_path = {
                str(entry.get("path")): entry
                for entry in baseline_entries
                if isinstance(entry, Mapping) and entry.get("path")
            } if isinstance(baseline_entries, list) else {}
            if not baseline_entries_by_path:
                blocking.append("baseline_manifest_entries_missing")
            reader_page_scope = mapping_fixture.get("companybrain_manifest", {}).get("reader_page_scope", {})
            if not isinstance(reader_page_scope, Mapping) or reader_page_scope.get("exhaustive") is not True:
                blocking.append("baseline_reader_page_scope_not_exhaustive")
            frozen_source_hash = str(mapping_fixture.get("source_manifest_hash") or "")
            candidate_manifest_path = Path(candidate) / "reports/source-manifest.json"
            if candidate_manifest_path.is_file():
                observed_source_hash = _companybrain_source_manifest_hash(_read_json(candidate_manifest_path))
            if not frozen_source_hash or not observed_source_hash or frozen_source_hash != observed_source_hash:
                blocking.append("source_manifest_mapping_drift")
        else:
            baseline_manifest_hash = _tree_hash(baseline_root)
            baseline_entries_by_path = {}
        for case in cases:
            case_id = str(case["case_id"])
            source_status = str(case.get("source_status") or "")
            expected_source_ids = set() if source_status == "not_applicable" else set(source_map_by_case.get(case_id, set()))
            if case.get("source_snapshot_id"):
                expected_source_ids.add(str(case["source_snapshot_id"]))
            if source_status == "not_applicable":
                mapping_row = mapping_by_case.get(case_id)
                kd = _case_side(candidate_root, None, case, home="Home.md")
                cb = {"status": "not_applicable", "home": "Home.md", "first_hit_page": None, "route": [], "hop_count": None, "answer_score": 0.0, "boundary_score": 0.0, "claim_checks": [], "boundary_checks": [], "source_anchor": False, "na_reason": str(case["source_status_reason"])}
                rows.append({"case_id": case_id, "canonical_case_id": case.get("canonical_case_id"), "comparison_key": case.get("comparison_key"), "criticality": case.get("criticality", "non_critical"), "baseline_mapping_status": "not_applicable", "home": {"knowledge_digest": kd["home"], "companybrain": cb["home"]}, "first_hit_page": {"knowledge_digest": kd["first_hit_page"], "companybrain": cb["first_hit_page"]}, "knowledge_digest": kd, "companybrain": cb, "axis_delta": {"path": 0, "answer_completeness": 0.0, "boundary_source_clarity": 0.0}, "failure_reason": None})
                continue
            mapped_topics = [
                row for row in topics
                if isinstance(row, Mapping) and expected_source_ids.intersection({str(item) for item in row.get("source_ids", [])})
            ]
            if len(mapped_topics) > 1:
                blocking.append("case_topic_mapping_ambiguous")
            kd_topic = (mapped_topics[0] if len(mapped_topics) == 1 else None) or by_case.get(str(case.get("canonical_case_id"))) or by_title.get(str(case.get("target_title")))
            if expected_source_ids and not mapped_topics and kd_topic is None:
                blocking.append("case_topic_mapping_missing")
            kd_path = str(kd_topic.get("page_path")) if kd_topic else None
            kd = _case_side(candidate_root, kd_path, case, home="Home.md", additional_paths=kd_topic.get("page_paths", []) if kd_topic else [])
            mapping_row = mapping_by_case.get(case_id)
            mapping_status = str(mapping_row.get("status")) if mapping_row else None
            baseline_entry = mapping_row.get("entry_path") if mapping_status == "unique" else case.get("companybrain_entry_path")
            if mapping_status == "ambiguous" or isinstance(baseline_entry, list):
                blocking.append("baseline_mapping_ambiguous")
                cb = {"status": "unknown", "home": "Home.md", "first_hit_page": None, "route": [], "hop_count": None, "answer_score": 0.0, "boundary_score": 0.0, "claim_checks": [], "boundary_checks": [], "source_anchor": False}
            elif mapping_status in {"unmatched", "undecidable"}:
                # ``unmatched`` means the mapper could not prove a unique
                # baseline page.  It is not proof that CompanyBrain lacks the
                # topic.  Treating it as neutral N/A would inflate the KD
                # delta by turning mapping failure into a baseline advantage.
                blocking.append("baseline_mapping_undecidable" if mapping_status == "undecidable" else "baseline_mapping_unmatched")
                cb = {"status": "unknown", "home": "Home.md", "first_hit_page": None, "route": [], "hop_count": None, "answer_score": 0.0, "boundary_score": 0.0, "claim_checks": [], "boundary_checks": [], "source_anchor": False, "unknown_reason": "automatic mapping did not prove a unique CompanyBrain counterpart"}
            elif mapping_status == "unique" and isinstance(mapping_row, Mapping):
                frozen_entry = baseline_entries_by_path.get(str(baseline_entry))
                if not frozen_entry or not frozen_entry.get("sha256") or not mapping_row.get("entry_sha256"):
                    blocking.append("baseline_entry_hash_missing")
                else:
                    current_entry = baseline_root / str(baseline_entry)
                    if not current_entry.is_file() or _sha256_bytes(current_entry.read_bytes()) != str(frozen_entry["sha256"]) or str(mapping_row["entry_sha256"]) != str(frozen_entry["sha256"]):
                        blocking.append("baseline_entry_hash_mismatch")
                cb = _case_side(baseline_root, str(baseline_entry), case, home="Home.md", baseline=True)
            elif mapping_status == "not_applicable":
                reader_page_scope = mapping_fixture.get("companybrain_manifest", {}).get("reader_page_scope", {}) if isinstance(mapping_fixture, Mapping) else {}
                if not isinstance(reader_page_scope, Mapping) or reader_page_scope.get("exhaustive") is not True:
                    blocking.append("baseline_not_applicable_scope_unproven")
                    cb = {"status": "unknown", "home": "Home.md", "first_hit_page": None, "route": [], "hop_count": None, "answer_score": 0.0, "boundary_score": 0.0, "claim_checks": [], "boundary_checks": [], "source_anchor": False, "unknown_reason": "baseline reader page scope is not exhaustive"}
                else:
                    cb = {"status": "not_applicable", "home": "Home.md", "first_hit_page": None, "route": [], "hop_count": None, "answer_score": 0.0, "boundary_score": 0.0, "claim_checks": [], "boundary_checks": [], "source_anchor": False, "na_reason": mapping_row.get("not_applicable_reason") if isinstance(mapping_row, Mapping) else None}
            elif baseline_entry is None:
                cb = {"status": "not_applicable", "home": "Home.md", "first_hit_page": None, "route": [], "hop_count": None, "answer_score": 0.0, "boundary_score": 0.0, "claim_checks": [], "boundary_checks": [], "source_anchor": False, "na_reason": case.get("companybrain_not_applicable_reason")}
            else:
                cb = _case_side(baseline_root, str(baseline_entry), case, home="Home.md", baseline=True)
            if kd["status"] in {"missing", "unknown"}:
                blocking.append("case_evidence_missing")
            if cb["status"] == "missing" and isinstance(mapping_fixture, Mapping):
                blocking.append("baseline_entry_missing")
            if case.get("criticality") == "critical" and cb["status"] == "not_applicable":
                blocking.append("critical_case_not_applicable")
            path_delta = 0
            if cb["status"] == "not_applicable":
                path_delta = 0
            elif kd["status"] == "covered" and cb["status"] == "covered":
                kd_rank = (1, -(kd["hop_count"] or 0))
                cb_rank = (1, -(cb["hop_count"] or 0))
                path_delta = 1 if kd_rank > cb_rank else (-1 if kd_rank < cb_rank else 0)
            elif kd["status"] == "covered":
                path_delta = 1
            else:
                path_delta = -1
            answer_delta = 0.0 if cb["status"] == "not_applicable" else kd["answer_score"] - cb["answer_score"]
            boundary_delta = 0.0 if cb["status"] == "not_applicable" else kd["boundary_score"] - cb["boundary_score"]
            rows.append({"case_id": case_id, "canonical_case_id": case.get("canonical_case_id"), "comparison_key": case.get("comparison_key"), "criticality": case.get("criticality", "non_critical"), "baseline_mapping_status": mapping_status or ("configured" if baseline_entry else "not_configured"), "home": {"knowledge_digest": kd["home"], "companybrain": cb["home"]}, "first_hit_page": {"knowledge_digest": kd["first_hit_page"], "companybrain": cb["first_hit_page"]}, "knowledge_digest": kd, "companybrain": cb, "axis_delta": {"path": path_delta, "answer_completeness": answer_delta, "boundary_source_clarity": boundary_delta}, "failure_reason": None if kd["status"] == "covered" else "evidence_missing"})
        axes = ("path", "answer_completeness", "boundary_source_clarity")
        axis_delta = {axis: sum(float(row["axis_delta"][axis]) for row in rows) / (len(rows) or 1) for axis in axes}
        strictly_better = [axis for axis in axes if axis_delta[axis] > 0]
        not_worse = [axis for axis in axes if axis_delta[axis] >= 0]
        if blocking:
            status = "undecidable"
        elif not strictly_better or len(not_worse) != len(axes):
            status = "candidate"
            blocking.append("three_axis_strict_delta_not_satisfied")
        else:
            status = "better_than_companybrain"
        comparison = {"schema_version": "task4-comparison-table.v2", "case_count": len(rows), "row_count": len(rows), "source_count": config.get("source_coverage", {}).get("expected_count"), "axis_delta": axis_delta, "strictly_better_axes": strictly_better, "not_worse_axes": not_worse, "not_applicable_cases": [row["case_id"] for row in rows if row["companybrain"]["status"] == "not_applicable"], "rows": rows}
        machine = {"schema_version": "task4-machine-quality.v2", "evidence_type": "machine", "source_count": comparison["source_count"], "case_count": len(rows), "coverage_status": "pass" if not blocking else "incomplete", "blocking_reasons": sorted(set(blocking))}
        receipt = {"schema_version": "task4-evaluator-receipt.v2", "protocol_id": config.get("protocol_id", "reader-compare-v1"), "evaluator_id": config.get("evaluator_id", "reader-evaluator-v1"), "evaluator_config_hash": config_hash, "case_matrix_hash": _sha256_json(config["case_matrix"]), "companybrain_manifest_hash": baseline_manifest_hash, "candidate_run_id": candidate_status.get("run_id"), "candidate_input_manifest_generation": candidate_status.get("input_manifest_generation"), "candidate_source_manifest_hash": observed_source_hash, "baseline_first": True, "network_disabled": True, "machine_only": True, "question_order": [row["case_id"] for row in rows]}
        root_causes = _root_cause_items(Path(candidate), rows, blocking)
        out.mkdir(parents=True, exist_ok=True)
        _write_json(out / "reports/machine-quality.json", machine)
        _write_json(out / "reports/comparison-table.json", comparison)
        _write_json(out / "reports/evaluator-receipt.json", receipt)
        _write_json(out / "reports/root-cause.json", {"schema_version": "task4-root-cause.v2", "items": root_causes})
        summary = {"schema_version": "task4-release-summary.v2", "status": status, "release_status": NOT_RELEASED, "blocking_reasons": sorted(set(blocking)), "machine_quality_status": machine["coverage_status"], "comparison_status": status}
        _write_json(out / "reports/release-summary.json", summary)
        return {"status": status, "release_status": NOT_RELEASED, "blocking_reasons": sorted(set(blocking)), "machine_quality": machine, "comparison": comparison, "evaluator_receipt": receipt, "root_cause": root_causes}
    except (Task4ReaderError, OSError, UnicodeError) as exc:
        result = {"status": "undecidable", "release_status": NOT_RELEASED, "blocking_reasons": [getattr(exc, "code", "assessment_error")], "reason": str(exc)}
        _write_json(out / "reports/release-summary.json", result)
        return result


# Kept as a small compatibility helper for existing local callers.  It reads
# the compiler's report and never invents an expected 89 denominator.
def _machine_quality(candidate: Path, expected_count: int | None = None) -> dict[str, Any]:
    root = Path(candidate)
    report = _read_json(root / "reports/source-manifest.json")
    count = len(report.get("entries", []))
    return {"schema_version": "task4-machine-quality.v2", "evidence_type": "machine", "source_count": count, "expected_source_count": expected_count, "coverage_status": "pass" if expected_count is None or count == expected_count else "incomplete"}
