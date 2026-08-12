"""Stage 4: faithful claims and deterministic long-document reorganization."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Mapping

from .config import DigestSettings
from .errors import ValidationError
from .identity import topic_part_path
from .faithfulness import claim_entity_key, claim_fingerprint, faithfulness_check, normalize_for_gate, verify_claims
from .jsonl import write_jsonl
from .kb_structure import PublicationContract
from .publication import (
    PAGE_TYPE_OPTIONAL_SECTIONS,
    PAGE_TYPE_SECTION_MATRIX,
    audit_procedure_exceptions_source,
    deterministic_category_id,
    validate_publication_suggestion,
)


_HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
_TITLE_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")
_FAQ_RE = re.compile(r"^\s*(?:FAQ|Q(?:uestion)?)[\s:：]", re.IGNORECASE)
_ERROR_RE = re.compile(r"^\s*(?:Error\s+)?[A-Z][A-Z0-9_-]*\d+[\s:：-]", re.IGNORECASE)
_PARAM_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:parameter|param|argument)\b[^:：]*[:：]", re.IGNORECASE)
_SUMMARY_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_VERSION_RE = re.compile(
    r"\b(?:version|release|released|版本)\s*(?:(?:[:：]\s*)|(?=[vV]?\d))"
    r"([A-Za-z0-9][A-Za-z0-9._-]*)",
    re.IGNORECASE,
)
_VERSION_SEMVER_RE = re.compile(r"^v?\d+(?:\.\d+){1,3}$", re.IGNORECASE)
_VERSION_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BILINGUAL_RE = re.compile(r"(?:[A-Za-z]{2,}.*[/|｜].*[\u4e00-\u9fff]|[\u4e00-\u9fff].*[/|｜].*[A-Za-z]{2,})")
_TABLE_RE = re.compile(r"^\s*\|")
_NOISE_RE = re.compile(r"^\s*(?:noise|unsupported|generated footer)\s*[:：]", re.IGNORECASE)


def _normalized_version_value(text: str) -> str:
    """Strip a source label while preserving the declared version literal."""
    match = _VERSION_RE.search(text)
    return match.group(1) if match else text.strip()


def _version_contract_value(text: str) -> tuple[str | None, str | None]:
    """Accept only a version literal or an explicitly labelled release value."""
    normalized = _normalized_version_value(text)
    if _VERSION_SEMVER_RE.fullmatch(normalized) or _VERSION_DATE_RE.fullmatch(normalized):
        return normalized, None
    if re.search(r"\b(?:release|released|发布)\s*[:：]", text, re.IGNORECASE) and normalized:
        return normalized, None
    return None, "version is not a semver, date, or explicit release label"


def _structure_fragment(
    item: Mapping[str, Any],
    *,
    start: int,
    end: int,
    text: str,
    content_type: str,
    parent_locator: str | None,
    heading_level: int | None = None,
) -> dict[str, Any]:
    """Build one stable, source-addressable structure fragment."""
    locator = f"lines:{start}-{end}"
    fragment: dict[str, Any] = {
        "fragment_id": f"{item.get('raw_id', 'raw')}-{start}-{end}",
        "raw_id": item.get("raw_id"),
        "source_uri": item.get("source_uri"),
        "content_fingerprint": item.get("content_fingerprint"),
        "source_locator": locator,
        "fragment_locator": locator,
        "text": text,
        "content_type": content_type,
        "parent_locator": parent_locator,
        "relation_type": "child_of" if parent_locator else None,
    }
    if heading_level is not None:
        fragment["heading_level"] = heading_level
    if not fragment["source_uri"]:
        fragment["exclusion_reason"] = "source URI is missing"
    return fragment


def normalize_structure(raw_items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize source lines into typed, traceable fragments."""
    fragments: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        lines = str(item.get("text", "")).splitlines()
        heading_stack: list[tuple[int, str]] = []
        index = 0
        while index < len(lines):
            raw_line = lines[index]
            if not raw_line.strip():
                index += 1
                continue
            heading = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", raw_line)
            if heading:
                level = len(heading.group(1))
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                locator = f"lines:{index + 1}-{index + 1}"
                fragments.append(
                    _structure_fragment(
                        item,
                        start=index + 1,
                        end=index + 1,
                        text=raw_line,
                        content_type="heading",
                        parent_locator=heading_stack[-1][1] if heading_stack else None,
                        heading_level=level,
                    )
                )
                heading_stack.append((level, locator))
                index += 1
                continue

            start = index
            content_type = "text"
            if _TABLE_RE.match(raw_line):
                content_type = "table"
                while index + 1 < len(lines) and _TABLE_RE.match(lines[index + 1]):
                    index += 1
            elif _FAQ_RE.match(raw_line):
                content_type = "faq"
                while (
                    index + 1 < len(lines)
                    and lines[index + 1].strip()
                    and not _HEADING_RE.match(lines[index + 1])
                ):
                    if _TABLE_RE.match(lines[index + 1]) or _IMAGE_RE.search(lines[index + 1]):
                        break
                    index += 1
            elif _IMAGE_RE.search(raw_line):
                content_type = "image"
            elif _VERSION_RE.search(raw_line):
                content_type = "version"
            elif _BILINGUAL_RE.search(raw_line):
                content_type = "bilingual"
            elif _NOISE_RE.match(raw_line) or _is_unsupported(raw_line):
                content_type = "noise"
            elif raw_line.strip().startswith(chr(96) * 3):
                content_type = "code"
                while index + 1 < len(lines):
                    index += 1
                    if lines[index].strip().startswith(chr(96) * 3):
                        break
            end = index + 1
            parent_locator = heading_stack[-1][1] if heading_stack else None
            fragments.append(
                _structure_fragment(
                    item,
                    start=start + 1,
                    end=end,
                    text="\n".join(lines[start:end]),
                    content_type=content_type,
                    parent_locator=parent_locator,
                )
            )
            index += 1
    return fragments


def _degraded_page_draft(
    topic_index: Mapping[str, Any],
    fragments: list[Mapping[str, Any]],
    reason: str,
) -> dict[str, Any]:
    return {
        "topic_id": topic_index.get("topic_id"),
        "title": topic_index.get("title"),
        "page_type": topic_index.get("page_type"),
        "required_sections": [],
        "optional_sections": [],
        "sections": {},
        "source_fragments": [dict(fragment) for fragment in fragments],
        "status": "degraded",
        "reader_eligible": False,
        "audit_record": {"destination": "Audit", "reason": reason},
    }


def _claim_identity(claim: Mapping[str, Any]) -> str:
    return str(claim.get("claim_id") or claim.get("claim_fingerprint") or "").strip()


def _section_dependency_record(
    *,
    topic_id: str,
    page_type: str,
    section_id: str,
    fragments: list[Mapping[str, Any]],
    claims: list[Mapping[str, Any]],
    dependency_scope: str,
    source_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind a section only to the source and claims named by that section."""
    from .page_layout import build_section_dependency_record

    claim_keys = {_claim_identity(claim) for claim in claims if _claim_identity(claim)}
    selected_fragments: list[Mapping[str, Any]] = []
    unresolved = dependency_scope != "resolved"
    for claim in claims:
        raw_id = claim.get("raw_id")
        locator = str(claim.get("fragment_locator") or "")
        matches = [
            fragment
            for fragment in fragments
            if fragment.get("raw_id") == raw_id
            and str(fragment.get("fragment_locator") or "") == locator
        ]
        if not matches:
            unresolved = True
        for fragment in matches:
            if fragment not in selected_fragments:
                selected_fragments.append(fragment)
    if section_id == "version" and not selected_fragments:
        selected_fragments = [
            fragment
            for fragment in fragments
            if fragment.get("content_type") == "version"
        ]

    source_deps = [
        {
            "source_uri": fragment.get("source_uri"),
            "content_hash": fragment.get("content_fingerprint"),
            "fragment_locator": fragment.get("fragment_locator"),
        }
        for fragment in selected_fragments
        if fragment.get("source_uri") and fragment.get("fragment_locator")
    ]
    if str((source_audit or {}).get("status") or "") == "source_not_documented":
        source_deps = [
            dict(row)
            for row in (source_audit or {}).get("source_deps", [])
            if isinstance(row, Mapping)
        ]
    source_deps = list({
        json.dumps(row, ensure_ascii=False, sort_keys=True): row
        for row in source_deps
    }.values())
    structure_fragments = list(selected_fragments)
    if str((source_audit or {}).get("status") or "") == "source_not_documented":
        structure_fragments = list(fragments)
    selected_parent_locators = {
        str(fragment.get("parent_locator"))
        for fragment in selected_fragments
        if fragment.get("parent_locator")
    }
    for fragment in fragments:
        if str(fragment.get("fragment_locator") or "") in selected_parent_locators and fragment not in structure_fragments:
            structure_fragments.append(fragment)
    structure_deps = [
        {
            "fragment_locator": fragment.get("fragment_locator"),
            "relation_type": fragment.get("relation_type"),
            "structure_hash": hashlib.sha256(
                json.dumps(
                    {
                        "parent_locator": fragment.get("parent_locator"),
                        "content_type": fragment.get("content_type"),
                        "heading_level": fragment.get("heading_level"),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        }
        for fragment in structure_fragments
        if fragment.get("fragment_locator")
    ]
    claim_deps = [
        {
            "claim_id": _claim_identity(claim),
            "claim_fingerprint": str(claim.get("claim_fingerprint") or "").strip(),
            "source_uri": str(claim.get("source_uri") or "").strip(),
            "fragment_locator": str(claim.get("fragment_locator") or "").strip(),
            "content_fingerprint": str(
                claim.get("content_fingerprint") or claim.get("content_hash") or ""
            ).strip(),
        }
        for claim in claims
        if _claim_identity(claim)
    ]
    attribution_deps = [
        {
            "claim_id": _claim_identity(claim),
            "source_uri": str(claim.get("source_uri") or "").strip(),
            "fragment_locator": str(claim.get("fragment_locator") or "").strip(),
            "content_fingerprint": str(
                claim.get("content_fingerprint") or claim.get("content_hash") or ""
            ).strip(),
        }
        for claim in claims
        if _claim_identity(claim)
    ]
    version_deps = []
    if section_id == "version":
        version_deps = [
            {
                "field": "version",
                "normalized_value": _normalized_version_value(str(fragment.get("text", ""))),
                "claim_id": None,
            }
            for fragment in selected_fragments
            if fragment.get("content_type") == "version"
        ]
    return build_section_dependency_record(
        topic_id=topic_id,
        page_type=page_type,
        section_id=section_id,
        source_deps=source_deps,
        claim_deps=claim_deps,
        version_deps=version_deps,
        structure_deps=structure_deps,
        attribution_deps=attribution_deps,
        dependency_scope="unresolved" if unresolved else "resolved",
    )


def _bind_typed_section_dependencies(
    page_draft: Mapping[str, Any],
    typed_response: Mapping[str, Any],
    claims: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Replace pre-provider dependency shells with claim-mapped records."""
    fragments = [
        fragment
        for fragment in page_draft.get("source_fragments", [])
        if isinstance(fragment, Mapping)
    ]
    all_claims = [claim for claim in claims if isinstance(claim, Mapping)]
    by_id = {_claim_identity(claim): claim for claim in all_claims if _claim_identity(claim)}
    bound = dict(typed_response)
    bound_sections: dict[str, Any] = {}
    for section_id, raw_section in (typed_response.get("sections") or {}).items():
        if not isinstance(raw_section, Mapping):
            bound_sections[str(section_id)] = raw_section
            continue
        claim_ids = [str(value).strip() for value in raw_section.get("claim_ids", []) if str(value).strip()]
        section_claims = [by_id[claim_id] for claim_id in claim_ids if claim_id in by_id]
        source_audit = (
            page_draft.get("section_audits", {}).get(str(section_id))
            if isinstance(page_draft.get("section_audits"), Mapping)
            else None
        )
        record = _section_dependency_record(
            topic_id=str(page_draft.get("topic_id") or ""),
            page_type=str(page_draft.get("page_type") or ""),
            section_id=str(section_id),
            fragments=fragments,
            claims=section_claims,
            dependency_scope=(
                "resolved"
                if isinstance(source_audit, Mapping)
                and source_audit.get("status") == "source_not_documented"
                else "resolved"
                if len(section_claims) == len(claim_ids) and claim_ids
                else "unresolved"
            ),
            source_audit=source_audit if isinstance(source_audit, Mapping) else None,
        )
        section_value = {**dict(raw_section), "dependency_record": record}
        if isinstance(source_audit, Mapping) and source_audit.get("status") == "source_not_documented":
            section_value["status"] = "source_not_documented"
            section_value["source_audit"] = dict(source_audit)
        bound_sections[str(section_id)] = section_value
        trusted_section = page_draft.get("sections", {}).get(section_id) if isinstance(page_draft.get("sections"), Mapping) else None
        if isinstance(trusted_section, dict):
            trusted_section["dependency_record"] = record
    bound["sections"] = bound_sections
    return bound


def build_page_draft(
    *,
    topic_index: Mapping[str, Any],
    fragments: list[Mapping[str, Any]],
    claims: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the trusted typed PageDraft shell from TopicIndex and fragments."""
    mapping_status = str(topic_index.get("mapping_status", "mapped"))
    page_type = topic_index.get("page_type")
    if mapping_status != "mapped":
        return _degraded_page_draft(
            topic_index,
            fragments,
            f"topic index mapping is {mapping_status}",
        )
    if page_type not in PAGE_TYPE_SECTION_MATRIX:
        return _degraded_page_draft(
            topic_index,
            fragments,
            f"unknown page type: {page_type}",
        )
    required = list(PAGE_TYPE_SECTION_MATRIX[page_type])
    optional = list(PAGE_TYPE_OPTIONAL_SECTIONS.get(page_type, ()))
    has_version_fragment = any(
        str(fragment.get("content_type")) == "version" and str(fragment.get("text", "")).strip()
        for fragment in fragments
    )
    if page_type in {"module_or_capability", "procedure_or_rule"} and not has_version_fragment:
        required = [section_id for section_id in required if section_id != "version"]
    version_values: list[tuple[str, str]] = []
    for fragment in fragments:
        if fragment.get("content_type") != "version":
            continue
        value, error = _version_contract_value(str(fragment.get("text", "")))
        if error:
            return _degraded_page_draft(topic_index, fragments, error)
        if value:
            version_values.append((value, str(fragment.get("source_locator") or "unknown")))
    version_keys = {re.sub(r"^v", "", value, flags=re.IGNORECASE).casefold() for value, _ in version_values}
    if len(version_keys) > 1:
        locations = ", ".join(locator for _, locator in version_values)
        return _degraded_page_draft(
            topic_index,
            fragments,
            f"conflicting version facts at {locations}",
        )
    available_optional = optional if has_version_fragment else []
    section_ids = [*required, *available_optional]
    section_audits: dict[str, dict[str, Any]] = {}
    if page_type == "procedure_or_rule":
        section_audits["exceptions"] = audit_procedure_exceptions_source(fragments)
    supplied_claims = [claim for claim in claims or [] if isinstance(claim, Mapping)]
    explicit_section_claims = {
        str(claim.get("section_id")): []
        for claim in supplied_claims
        if str(claim.get("section_id") or "").strip()
    }
    for claim in supplied_claims:
        section_id = str(claim.get("section_id") or "").strip()
        if section_id in explicit_section_claims:
            explicit_section_claims[section_id].append(claim)
    has_explicit_mapping = bool(explicit_section_claims)
    section_records = {}
    for index, section_id in enumerate(section_ids):
        if has_explicit_mapping:
            section_claims = explicit_section_claims.get(section_id, [])
            scope = "resolved" if all(
                str(claim.get("section_id") or "").strip() in section_ids
                for claim in supplied_claims
            ) else "unresolved"
        else:
            # Before provider output there is no trustworthy section mapping.
            # Keep the lineage visible on the first shell for compatibility,
            # but mark every shell unresolved so impact evaluation can only
            # choose whole-page recompilation until claim_ids bind the sections.
            section_claims = supplied_claims if index == 0 else []
            scope = "unresolved"
        section_records[section_id] = _section_dependency_record(
            topic_id=str(topic_index.get("topic_id") or ""),
            page_type=str(page_type),
            section_id=section_id,
            fragments=[fragment for fragment in fragments if isinstance(fragment, Mapping)],
            claims=section_claims,
            dependency_scope=(
                "resolved"
                if section_id == "exceptions"
                and section_audits.get(section_id, {}).get("status") == "source_not_documented"
                else scope
            ),
            source_audit=section_audits.get(section_id),
        )
    return {
        "topic_id": topic_index.get("topic_id"),
        "title": topic_index.get("title"),
        "page_type": page_type,
        "required_sections": required,
        "optional_sections": available_optional,
        "sections": {
            section_id: {
                "section_id": section_id,
                "body": "",
                "status": "pending",
                "fragment_locators": [],
                "dependency_record": section_records[section_id],
                **(
                    {
                        "source_audit": section_audits[section_id],
                        "status": "source_not_documented",
                    }
                    if section_audits.get(section_id, {}).get("status") == "source_not_documented"
                    else {}
                ),
            }
            for section_id in [*required, *available_optional]
        },
        "source_fragments": [dict(fragment) for fragment in fragments],
        "section_audits": section_audits,
        "status": "draft",
        "reader_eligible": False,
        "audit_record": None,
    }


def _marker(line: str) -> str | None:
    if _HEADING_RE.match(line):
        return "heading"
    if _FAQ_RE.match(line):
        return "faq"
    if _ERROR_RE.match(line):
        return "error_code"
    if _PARAM_RE.match(line):
        return "parameter"
    if line.strip().startswith("```"):
        return "code"
    return None


def _is_unsupported(line: str) -> bool:
    return line.strip().casefold().startswith("unsupported:")


def _publication_title_candidates(items: list[dict[str, Any]]) -> list[str]:
    """Collect deterministic reader-title candidates in source order.

    Page-layout owns the existing managed-title check.  Drafting only records
    source facts, so an offline run needs neither a provider nor a heuristic
    classification step to create a useful reader-facing title.
    """
    values: list[str] = []
    for item in items:
        metadata = item.get("source_meta")
        if isinstance(metadata, Mapping):
            title = metadata.get("title")
            if isinstance(title, str) and title.strip():
                values.append(title.strip())
        for line in str(item.get("text", "")).splitlines():
            match = _TITLE_H1_RE.match(line)
            if match and match.group(1).strip():
                values.append(match.group(1).strip())
                break
        input_path = item.get("input_path")
        if isinstance(input_path, str) and input_path.strip():
            values.append(Path(input_path).stem)
    return list(dict.fromkeys(values))


def _code_component_end(lines: list[str], start: int) -> int:
    """Return the end of a fenced code block plus one adjacent explanation."""
    end = start + 1
    while end < len(lines):
        if lines[end].strip().startswith("```") and end > start:
            end += 1
            break
        end += 1
    if end < len(lines) and lines[end].strip() and _marker(lines[end]) is None:
        end += 1
    return end


def _component_spans(lines: list[str]) -> list[dict[str, Any]]:
    """Create stable, contiguous component spans while keeping atomic pairs."""
    spans: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        start = index
        marker = _marker(lines[index])
        end = index + 1
        atomic = marker in {"faq", "error_code", "parameter", "code"}
        if marker is None and index + 1 < len(lines) and _marker(lines[index + 1]) == "code":
            # Consume an immediately preceding explanation with the code block
            # here, so the component stays atomic without overlapping spans.
            marker = "code"
            atomic = True
            end = _code_component_end(lines, index + 1)
        if marker == "code":
            if end == start + 1:
                end = _code_component_end(lines, start)
        elif marker in {"faq", "error_code", "parameter"}:
            while end < len(lines):
                candidate = lines[end]
                if _marker(candidate) is not None or (
                    end + 1 < len(lines) and _marker(lines[end + 1]) == "code"
                ):
                    break
                end += 1
        elif marker == "heading":
            # Keep a heading and its direct content together. A nested heading
            # starts a new component so oversized sections can be split at
            # their subordinate headings before being marked unsplittable.
            while end < len(lines):
                candidate_marker = _marker(lines[end])
                if candidate_marker in {"faq", "error_code", "parameter", "code"} or (
                    end + 1 < len(lines) and _marker(lines[end + 1]) == "code"
                ):
                    break
                if candidate_marker == "heading":
                    break
                end += 1

        # Merge a blank separator into the preceding component. This preserves
        # readable pages without making blank lines an uncovered fragment.
        while end < len(lines) and not lines[end].strip():
            end += 1
        spans.append(
            {
                "component_id": f"component-{len(spans) + 1}",
                "kind": marker or "text",
                "line_start": start + 1,
                "line_end": end,
                "lines": lines[start:end],
                "atomic": atomic,
            }
        )
        index = end
    return spans


def _page_groups(spans: list[dict[str, Any]], max_lines: int) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_lines = 0
    for span in spans:
        span_lines = len(span["lines"])
        if current and current_lines + span_lines > max_lines:
            groups.append(current)
            current = []
            current_lines = 0
        current.append(span)
        current_lines += span_lines
        if span_lines > max_lines:
            span["oversized"] = True
            if current:
                groups.append(current)
                current = []
                current_lines = 0
    if current:
        groups.append(current)
    return groups


def _build_pages(
    items: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    *,
    max_lines: int,
    base_target: str,
    draft_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for item in items:
        for span in _component_spans(item["text"].splitlines()):
            span = dict(span)
            span["raw_id"] = item["raw_id"]
            span["source_uri"] = item["source_uri"]
            span["input_locator"] = f"lines:{span['line_start']}-{span['line_end']}"
            spans.append(span)

    groups = _page_groups(spans, max_lines)
    pages: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    component_coverage: list[dict[str, Any]] = []
    for page_number, group in enumerate(groups, start=1):
        rendered_rows = [
            {
                "component_id": span["component_id"],
                "source_line": span["line_start"] + offset,
                "text": line,
            }
            for span in group
            for offset, line in enumerate(span["lines"])
            if not _is_unsupported(line)
        ]
        page_lines = [row["text"] for row in rendered_rows]
        body = "\n".join(page_lines).strip()
        visible_rows = [index for index, row in enumerate(rendered_rows) if row["text"].strip()]
        first_visible = visible_rows[0] if visible_rows else None

        def output_locator(span: dict[str, Any], source_start: int, source_end: int) -> str | None:
            if first_visible is None:
                return None
            output_rows = [
                index
                for index, row in enumerate(rendered_rows)
                if row["component_id"] == span["component_id"]
                and source_start <= row["source_line"] <= source_end
                and row["text"].strip()
            ]
            if not output_rows:
                return None
            return f"lines:{output_rows[0] - first_visible + 1}-{output_rows[-1] - first_visible + 1}"

        if page_number == 1:
            target = base_target
        elif base_target.endswith(".md"):
            target = f"{base_target[:-3]}-part-{page_number}.md"
        else:
            target = f"{base_target}-part-{page_number}.md"
        page_claims: list[dict[str, Any]] = []
        for span in group:
            rendered_lines = [line for line in span["lines"] if line.strip() and not _is_unsupported(line)]
            span_output_locator = output_locator(span, span["line_start"], span["line_end"])
            component_coverage.append(
                {
                    "coverage_kind": "component",
                    "component_id": span["component_id"],
                    "raw_id": span.get("raw_id"),
                    "source_uri": span.get("source_uri"),
                    "input_fragment": span["input_locator"],
                    "output_page": target if rendered_lines else None,
                    "fragment_locator": span["input_locator"],
                    "output_fragment_locator": span_output_locator,
                    "omitted": not rendered_lines,
                    "omission_reason": "unsupported content filtered" if not rendered_lines else None,
                }
            )
            for claim in claims:
                if claim.get("raw_id") != span.get("raw_id"):
                    continue
                start = int(str(claim["fragment_locator"]).split(":", 1)[1].split("-", 1)[0])
                if span["line_start"] <= start <= span["line_end"]:
                    enriched = dict(claim)
                    enriched["page_index"] = page_number
                    enriched["target_path"] = target
                    claim_end = int(str(claim["fragment_locator"]).split(":", 1)[1].split("-", 1)[-1])
                    enriched["output_fragment_locator"] = output_locator(
                        span, start, claim_end
                    )
                    page_claims.append(enriched)
                    coverage.append(
                        {
                            "raw_id": claim.get("raw_id"),
                            "source_uri": claim.get("source_uri"),
                            "input_fragment": claim.get("fragment_locator"),
                            "output_page": target,
                            "fragment_locator": claim.get("fragment_locator"),
                            "output_fragment_locator": enriched["output_fragment_locator"],
                            "claim_fingerprint": claim.get("claim_fingerprint"),
                        }
                    )
        pages.append(
            {
                "page_index": page_number,
                "target_path": target,
                "final_body": body,
                "claims": page_claims,
                "components": [
                    {
                        "component_id": span["component_id"],
                        "kind": span["kind"],
                        "raw_id": span["raw_id"],
                        "input_locator": span["input_locator"],
                        "line_count": len(span["lines"]),
                        "oversized": bool(span.get("oversized", False)),
                    }
                    for span in group
                ],
                "oversized_components": [span["component_id"] for span in group if span.get("oversized")],
            }
        )

    total_lines = sum(len(item["text"].splitlines()) for item in items)
    suggestion = {
        "draft_id": draft_id,
        "raw_id": items[0]["raw_id"] if len(items) == 1 else None,
        "line_count": total_lines,
        "reason": "max_doc_lines exceeded",
        "output_pages": [page["target_path"] for page in pages],
        "pages": [
            {
                "page_index": page["page_index"],
                "target_path": page["target_path"],
                "components": page["components"],
                "unsplittable_components": page["oversized_components"],
            }
            for page in pages
        ],
        "coverage_mapping": coverage,
        "component_coverage": component_coverage,
        "coverage_complete": (
                {
                    (row.get("raw_id"), row.get("input_fragment"))
                    for row in coverage
                }
            >= {(claim.get("raw_id"), claim.get("fragment_locator")) for claim in claims}
            and {
                (row.get("raw_id"), row.get("input_fragment"))
                for row in component_coverage
            }
            >= {(span.get("raw_id"), span.get("input_locator")) for span in spans}
        ),
        "not_truncated": True,
    }
    return pages, suggestion


Generator = Callable[[dict[str, Any]], Any]


def _body_sha256(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _coverage_for_claims(claims: list[dict[str, Any]], target: str) -> list[dict[str, Any]]:
    return [
        {
            "raw_id": claim.get("raw_id"),
            "source_uri": claim.get("source_uri"),
            "input_fragment": claim.get("fragment_locator"),
            "output_page": target,
            "fragment_locator": claim.get("fragment_locator"),
            "claim_fingerprint": claim.get("claim_fingerprint"),
        }
        for claim in claims
    ]


def _dedupe_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the first occurrence of each claim fingerprint."""
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for claim in claims:
        identity = claim_entity_key(claim)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(dict(claim))
    return result


def _claim_line_start(claim: Mapping[str, Any]) -> int:
    locator = str(claim.get("fragment_locator", "lines:0-0"))
    try:
        return int(locator.split(":", 1)[1].split("-", 1)[0])
    except (IndexError, ValueError):
        return 0


def _generation_contexts(
    items: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    *,
    base_context: dict[str, Any],
    max_claims: int,
    max_chars: int,
    summary_enabled: bool = False,
) -> list[dict[str, Any]]:
    """Split a provider request at source-component boundaries.

    Ordinary prose may be split further when one section exceeds a limit.
    Atomic FAQ/error/parameter/code components stay whole for the legacy body
    refinement path. Summary mode can split an oversized atomic component into
    claim-sized provider inputs because the complete source is rendered later
    as deterministic Evidence; this keeps the provider request bounded without
    dropping any source content from the formal page.

    Typed body compilation is different from the legacy body-refinement path:
    every request must see the complete PageDraft claim set. Splitting a typed
    page into claim batches while retaining the page-wide required-section
    contract makes each batch unable to support sections whose claims are in a
    different batch. Keep one complete typed request so the provider can assign
    every section from the same trusted input. If that request is too large or
    fails, the existing fail-closed provider/degraded path remains the recovery
    boundary.
    """
    if isinstance(base_context.get("typed_section_contract"), Mapping):
        typed_body = str(base_context.get("initial_body") or base_context.get("source_text") or "").strip()
        return [
            {
                **base_context,
                "source_text": typed_body,
                "initial_body": typed_body,
                "claims": [dict(claim) for claim in claims],
                "batch_index": 1,
                "batch_count": 1,
                "batch_oversized_atomic": False,
            }
        ]

    units: list[dict[str, Any]] = []
    claims_by_raw: dict[Any, list[dict[str, Any]]] = {}
    for claim in claims:
        claims_by_raw.setdefault(claim.get("raw_id"), []).append(dict(claim))

    for item in items:
        raw_claims = claims_by_raw.get(item.get("raw_id"), [])
        for span in _component_spans(str(item.get("text", "")).splitlines()):
            body = "\n".join(
                line for line in span["lines"] if not _is_unsupported(line)
            ).strip()
            span_claims = [
                claim
                for claim in raw_claims
                if span["line_start"] <= _claim_line_start(claim) <= span["line_end"]
            ]
            if not span_claims and not _required_structure_lines(body):
                continue
            oversized = len(span_claims) > max_claims or len(body) > max_chars
            if span.get("atomic") and oversized and summary_enabled and span_claims:
                structure_lines = _required_structure_lines(body)
                claim_texts = {str(claim.get("text", "")).strip() for claim in span_claims}
                for claim in span_claims:
                    claim_text = str(claim.get("text", "")).strip()
                    parts = [line for line in structure_lines if line not in claim_texts]
                    if claim_text:
                        parts.append(claim_text)
                    units.append(
                        {
                            "body": "\n".join(parts),
                            "claims": [dict(claim)],
                            "oversized_atomic": False,
                        }
                    )
                continue
            if (
                not span.get("atomic")
                and (
                    oversized
                )
            ):
                claim_texts = {
                    str(claim.get("text", "")).strip() for claim in span_claims
                }
                units.extend(
                    {
                        "body": line,
                        "claims": [],
                        "oversized_atomic": False,
                    }
                    for line in _required_structure_lines(body)
                    if line not in claim_texts
                )
                units.extend(
                    {
                        "body": str(claim.get("text", "")),
                        "claims": [dict(claim)],
                        "oversized_atomic": False,
                    }
                    for claim in span_claims
                )
            else:
                units.append(
                    {
                        "body": body,
                        "claims": span_claims,
                        "oversized_atomic": bool(
                            span.get("atomic")
                            and (
                                len(span_claims) > max_claims
                                or len(body) > max_chars
                            )
                        ),
                    }
                )

    if not units:
        return [dict(base_context)]

    grouped: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_claims = 0
    current_chars = 0
    for unit in units:
        unit_claims = len(unit["claims"])
        unit_chars = len(unit["body"])
        if current and (
            current_claims + unit_claims > max_claims
            or current_chars + unit_chars > max_chars
        ):
            grouped.append(current)
            current = []
            current_claims = 0
            current_chars = 0
        current.append(unit)
        current_claims += unit_claims
        current_chars += unit_chars
        if unit["oversized_atomic"]:
            grouped.append(current)
            current = []
            current_claims = 0
            current_chars = 0
    if current:
        grouped.append(current)

    contexts: list[dict[str, Any]] = []
    batch_count = len(grouped)
    for index, group in enumerate(grouped, start=1):
        body = "\n\n".join(unit["body"] for unit in group if unit["body"]).strip()
        batch_claims = [
            dict(claim)
            for unit in group
            for claim in unit["claims"]
        ]
        contexts.append(
            {
                **base_context,
                "source_text": body,
                "initial_body": body,
                "claims": batch_claims,
                "batch_index": index,
                "batch_count": batch_count,
                "batch_oversized_atomic": any(
                    unit["oversized_atomic"] for unit in group
                ),
            }
        )
    return contexts


def _sum_optional_int(values: list[Any]) -> int | None:
    return sum(int(value) for value in values) if values and all(value is not None for value in values) else None


def _merge_typed_responses(
    page_draft: Mapping[str, Any],
    batch_candidates: list[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Merge typed sections returned for a source-split topic.

    A large topic can require several provider calls.  Each call receives a
    source slice but must still return the same typed section contract.  Keep
    all section bodies and claim ids, then validate the merged response
    against the complete trusted PageDraft before handing it to the compiler.
    """
    responses = [
        response
        for candidate in batch_candidates
        for response in [candidate.get("typed_response")]
        if isinstance(response, Mapping)
    ]
    if len(responses) != len(batch_candidates) or not responses:
        return None

    page_type = page_draft.get("page_type")
    merged_sections: dict[str, dict[str, Any]] = {}
    for response in responses:
        if response.get("status") != "draft" or response.get("page_type") != page_type:
            return None
        sections = response.get("sections")
        if not isinstance(sections, Mapping):
            return None
        for section_id, raw_section in sections.items():
            if not isinstance(raw_section, Mapping):
                return None
            section_key = str(section_id)
            body = str(raw_section.get("body", "")).strip()
            source_audit = (
                page_draft.get("section_audits", {}).get(section_key)
                if isinstance(page_draft.get("section_audits"), Mapping)
                else None
            )
            if not body and not (
                isinstance(source_audit, Mapping)
                and source_audit.get("status") == "source_not_documented"
            ):
                return None
            merged = merged_sections.setdefault(
                section_key,
                {
                    "body_parts": [],
                    "claim_ids": [],
                },
            )
            merged["body_parts"].append(body)
            for claim_id in raw_section.get("claim_ids", []):
                value = str(claim_id).strip()
                if value and value not in merged["claim_ids"]:
                    merged["claim_ids"].append(value)

    payload = {
        "page_type": page_type,
        "sections": {
            section_id: {
                "body": "\n\n".join(values["body_parts"]),
                "claim_ids": values["claim_ids"],
            }
            for section_id, values in merged_sections.items()
        },
    }
    from .llm import validate_section_response

    validated = validate_section_response(page_draft, payload)
    return validated if validated.get("status") == "draft" else None


def _required_structure_lines(body: str) -> list[str]:
    return [
        line.strip()
        for line in body.splitlines()
        if line.strip()
        and (
            _marker(line) in {"heading", "code"}
            or line.lstrip().startswith("|")
        )
    ]


def default_generator(context: dict[str, Any]) -> dict[str, Any]:
    """The local generation boundary used until a provider is supplied.

    Keeping this as a callable makes the round controller testable without
    introducing a provider dependency.  The default remains deterministic and
    faithful to the existing claim concatenation behavior.
    """
    return {"final_body": context["initial_body"]}


def resolve_generator(settings: DigestSettings) -> Generator:
    """Pick the identity generator or a live provider based on configuration.

    Provider construction is imported lazily so the offline path never touches
    the network module, and provider failures surface as ``ValidationError``
    rather than a silent downgrade back to the identity generator.
    """
    if not getattr(settings, "llm_enabled", False):
        return default_generator
    from .llm import generator_from_env

    return generator_from_env(api_format=settings.llm_format)


def _invoke_generator(generator: Generator, context: dict[str, Any]) -> Any:
    """Call the generator with the single supported shape: ``generator(context)``."""
    return generator(context)


def _candidate_from_result(
    result: Any,
    *,
    initial_body: str,
    claims: list[dict[str, Any]],
    target: str,
    summary_enabled: bool = False,
    evidence_body: str | None = None,
) -> dict[str, Any]:
    if isinstance(result, str):
        result = {"final_body": result}
    if not isinstance(result, Mapping):
        result = {"final_body": initial_body, "valid": False, "invalid_reason": "generator returned a non-object"}
    body = str(result.get("final_body", result.get("body", initial_body)))
    # Provider output is adversarial input here too: a non-list ``claims`` (or a
    # list holding non-mappings) must fail validation, not crash the whole run
    # before the existing fallback path can take over.
    raw_claims = result.get("claims", claims)
    if not isinstance(raw_claims, list) or any(not isinstance(claim, Mapping) for claim in raw_claims):
        return {
            "final_body": initial_body,
            "claims": [dict(claim) for claim in claims],
            "coverage_mapping": _coverage_for_claims(claims, target),
            "component_coverage": [],
            "faithfulness_status": "",
            "explicit_invalid": True,
            "invalid_reason": "generator returned a malformed claims field",
            "provider_input_tokens": None,
            "provider_output_tokens": None,
            "provider_attempt_count": result.get("provider_attempt_count", 1),
        }
    candidate_claims = [dict(claim) for claim in raw_claims]
    summary = result.get("summary") if summary_enabled else None
    if isinstance(summary, Mapping):
        normalized_summary = dict(summary)
        normalized_segments: list[dict[str, Any]] = []
        for segment in summary.get("segments", []):
            if not isinstance(segment, Mapping):
                normalized_segments.append(segment)  # validation reports the shape
                continue
            normalized_segment = dict(segment)
            supports = segment.get("supports")
            if isinstance(supports, list):
                normalized_segment["supports"] = [
                    {"claim_fingerprint": support}
                    if isinstance(support, str)
                    else support
                    for support in supports
                ]
            normalized_segments.append(normalized_segment)
        normalized_summary["segments"] = normalized_segments
        summary = normalized_summary
    coverage = result.get("coverage_mapping")
    if coverage is None:
        coverage = _coverage_for_claims(candidate_claims, target)
    else:
        coverage = [dict(row) for row in coverage if isinstance(row, Mapping)]
    faithfulness_status = str(result.get("faithfulness_status", result.get("faithfulness", "")))
    explicit_invalid = result.get("valid") is False or result.get("status") == "invalid"
    if faithfulness_status.casefold() in {"failed", "invalid", "unfaithful"}:
        explicit_invalid = True
    publication = result.get("publication")
    if publication is None and any(field in result for field in ("title", "slug", "category_id", "summary", "why", "version")):
        publication = {field: result.get(field) for field in ("title", "slug", "category_id", "summary", "why", "version", "related_topics", "claim_refs", "field_refs") if field in result}
    return {
        "final_body": evidence_body if summary_enabled and evidence_body is not None else body,
        "claims": candidate_claims,
        "coverage_mapping": coverage,
        "component_coverage": [dict(row) for row in result.get("component_coverage", []) if isinstance(row, Mapping)],
        "summary": summary,
        "publication": publication,
        "faithfulness_status": faithfulness_status,
        "explicit_invalid": explicit_invalid,
        "invalid_reason": result.get("invalid_reason") or result.get("reason"),
        "provider_input_tokens": result.get("provider_input_tokens", result.get("input_tokens")),
        "provider_output_tokens": result.get("provider_output_tokens", result.get("output_tokens")),
        "provider_attempt_count": result.get("provider_attempt_count", 1),
    }


def _validate_summary(
    summary: Any,
    *,
    source_claims: list[dict[str, Any]],
    target: str,
) -> tuple[bool, str | None]:
    """Validate that every generated summary statement points to source claims."""
    if not isinstance(summary, Mapping):
        return False, "summary is missing or not an object"
    if summary.get("status") != "validated":
        return False, "summary status is not validated"
    segments = summary.get("segments")
    if not isinstance(segments, list) or not segments:
        return False, "summary segments are missing or empty"
    source_fingerprints = {
        str(claim.get("claim_fingerprint"))
        for claim in source_claims
        if claim.get("claim_fingerprint")
    }
    referenced: set[str] = set()
    for segment in segments:
        if not isinstance(segment, Mapping) or not str(segment.get("summary_id", "")).strip():
            return False, "summary segment is missing summary_id"
        if not str(segment.get("text", "")).strip():
            return False, "summary segment is missing text"
        supports = segment.get("supports")
        if not isinstance(supports, list) or not supports:
            return False, "summary segment has no supports"
        for support in supports:
            if not isinstance(support, Mapping):
                return False, "summary support is not an object"
            fingerprint = str(support.get("claim_fingerprint", ""))
            if fingerprint not in source_fingerprints:
                return False, "summary references a claim outside the source batch"
            support_target = support.get("target_path")
            if support_target not in (None, "", target):
                return False, "summary support targets a different page"
            referenced.add(fingerprint)
    if referenced != source_fingerprints:
        return False, "summary does not reference every source claim"
    summary_text = "\n".join(
        str(segment.get("text", ""))
        for segment in segments
        if isinstance(segment, Mapping)
    )
    protected_numbers = {
        number
        for claim in source_claims
        for number in _SUMMARY_NUMBER_RE.findall(str(claim.get("text", "")))
    }
    missing_numbers = sorted(
        number for number in protected_numbers if number not in summary_text
    )
    if missing_numbers:
        return False, f"summary omitted protected number(s): {', '.join(missing_numbers)}"
    protected_identifiers = {
        identifier
        for claim in source_claims
        for identifier in re.findall(r"`([^`]+)`", str(claim.get("text", "")))
        if (
            "/" in identifier
            or "://" in identifier
            or identifier.startswith("--")
            or identifier.endswith("()")
            or identifier.endswith((".py", ".md", ".yaml"))
            or identifier.startswith("ov ")
        )
    }
    missing_identifiers = sorted(
        identifier for identifier in protected_identifiers if identifier not in summary_text
    )
    if missing_identifiers:
        return False, (
            "summary omitted protected identifier(s): "
            + ", ".join(missing_identifiers)
        )
    return True, None


def _repair_summary(
    summary: Any,
    *,
    source_claims: list[dict[str, Any]],
    target: str,
) -> Any:
    """Add exact source wording when a model summary drops protected details.

    The provider may compress a limit such as "at most 3" into "a few".  The
    source claim is trusted; copying it into a clearly marked repair segment is
    safer than accepting the vague wording or deleting the Summary entirely.
    Evidence remains the complete deterministic source body.
    """
    if not isinstance(summary, Mapping) or not isinstance(summary.get("segments"), list):
        return summary
    repaired = dict(summary)
    segments = [dict(segment) for segment in summary["segments"] if isinstance(segment, Mapping)]
    summary_text = "\n".join(str(segment.get("text", "")) for segment in segments)
    protected_identifiers = {
        identifier
        for claim in source_claims
        for identifier in re.findall(r"`([^`]+)`", str(claim.get("text", "")))
        if (
            "/" in identifier
            or "://" in identifier
            or identifier.startswith("--")
            or identifier.endswith("()")
            or identifier.endswith((".py", ".md", ".yaml"))
            or identifier.startswith("ov ")
        )
    }
    protected_numbers = {
        number
        for claim in source_claims
        for number in _SUMMARY_NUMBER_RE.findall(str(claim.get("text", "")))
    }
    missing_numbers = {number for number in protected_numbers if number not in summary_text}
    missing_identifiers = {
        identifier for identifier in protected_identifiers if identifier not in summary_text
    }
    repair_index = 1
    for claim in source_claims:
        text = str(claim.get("text", "")).strip()
        claim_numbers = set(_SUMMARY_NUMBER_RE.findall(text))
        claim_identifiers = set(re.findall(r"`([^`]+)`", text)) & protected_identifiers
        if not ((claim_numbers & missing_numbers) or (claim_identifiers & missing_identifiers)):
            continue
        segments.append(
            {
                "summary_id": f"summary-repair-{repair_index}",
                "text": f"关键保真细节：{text}",
                "supports": [
                    {
                        "claim_fingerprint": claim.get("claim_fingerprint"),
                        "target_path": target,
                    }
                ],
            }
        )
        repair_index += 1
    repaired["segments"] = segments
    return repaired


def _render_summary(summary: Mapping[str, Any], evidence_body: str) -> str:
    """Render model summaries above a deterministic, lossless evidence body."""
    lines = ["## Summary", ""]
    for segment in summary.get("segments", []):
        lines.append(f"- {str(segment['text']).strip()} [{segment['summary_id']}]")
    lines.extend(["", "## Evidence", "", evidence_body.strip()])
    return "\n".join(lines).strip()


def _validate_candidate(
    candidate: dict[str, Any],
    *,
    source_claims: list[dict[str, Any]],
    required_structure_lines: list[str] | None = None,
) -> tuple[bool, str | None, float, float, int]:
    """Apply source, coverage, and faithfulness hard gates to one candidate."""
    if candidate["explicit_invalid"]:
        return False, str(candidate.get("invalid_reason") or "candidate marked invalid"), 0.0, 0.0, 0
    source_fingerprints = Counter(claim.get("claim_fingerprint") for claim in source_claims)
    # Lineage the generator hands back is metadata too. Bind each fingerprint to
    # the raw_id/fragment_locator the source actually recorded so a self-consistent
    # forged locator cannot mis-attribute a real claim to another line.
    source_lineage: dict[Any, set[tuple[Any, Any]]] = {}
    for claim in source_claims:
        source_lineage.setdefault(claim.get("claim_fingerprint"), set()).add(
            (claim.get("raw_id"), claim.get("fragment_locator"))
        )
    candidate_claims = candidate["claims"]
    # A fingerprint is metadata the generator supplies; on its own it proves
    # nothing. Recompute it from the claim's own source_uri and text so a copied
    # fingerprint cannot be pasted onto replacement or inverted text and still
    # satisfy retention, lineage, coverage, and the faithfulness hard gate.
    for claim in candidate_claims:
        source_uri = claim.get("source_uri")
        text = claim.get("text")
        if not isinstance(source_uri, str) or not isinstance(text, str):
            return False, "candidate claim is missing source lineage", 0.0, 0.0, 0
        recomputed = claim_fingerprint(source_uri, text)
        if recomputed != claim.get("claim_fingerprint"):
            return False, "candidate claim fingerprint does not match its own text", 0.0, 0.0, 0
    if any(
        claim.get("claim_fingerprint") not in source_fingerprints for claim in candidate_claims
    ):
        return False, "candidate contains a claim not present in the source", 0.0, 0.0, 0
    # Membership passed, so every fingerprint has a source record. Now require the
    # candidate's own lineage to equal what that source record says, otherwise a
    # real claim can be self-consistently mis-attributed to another line.
    for claim in candidate_claims:
        if (claim.get("raw_id"), claim.get("fragment_locator")) not in source_lineage[claim.get("claim_fingerprint")]:
            return False, "candidate claim lineage does not match the source record", 0.0, 0.0, 0
    candidate_fingerprints = Counter(claim.get("claim_fingerprint") for claim in candidate_claims)
    # Multiset, not set: two identical source lines share one fingerprint, so a
    # single candidate claim must not be able to stand in for both of them.
    missing = source_fingerprints - candidate_fingerprints
    if missing:
        return False, "candidate dropped a source claim", 0.0, 0.0, sum(missing.values())
    claim_keys = {
        (claim.get("raw_id"), claim.get("fragment_locator"))
        for claim in candidate_claims
    }
    covered_keys = {
        (row.get("raw_id"), row.get("input_fragment"))
        for row in candidate["coverage_mapping"]
        if row.get("output_page")
    }
    coverage_ratio = len(claim_keys & covered_keys) / len(claim_keys) if claim_keys else 1.0
    if covered_keys < claim_keys:
        return False, "candidate coverage mapping is incomplete", coverage_ratio, 0.0, 0
    if any(not claim.get("text") or not claim.get("source_uri") for claim in candidate_claims):
        return False, "candidate claim is missing source lineage", coverage_ratio, 0.0, 0
    normalized_body = normalize_for_gate(candidate["final_body"])
    if not all(normalize_for_gate(claim["text"]) in normalized_body for claim in candidate_claims):
        return False, "candidate failed faithfulness hard gate", coverage_ratio, 0.0, 0
    candidate_lines = Counter(
        line.strip() for line in candidate["final_body"].splitlines() if line.strip()
    )
    required_lines = Counter(required_structure_lines or [])
    if required_lines - candidate_lines:
        return False, "candidate dropped source structure", coverage_ratio, 0.0, 0
    eligible = len(source_claims)
    retained = len(candidate_claims)
    retained_ratio = retained / eligible if eligible else 1.0
    unsupported_count = max(0, len(source_claims) - len(candidate_claims))
    return True, None, coverage_ratio, retained_ratio, unsupported_count


def _round_record(
    *,
    candidate: dict[str, Any],
    valid: bool,
    reason: str | None,
    coverage_ratio: float,
    retained_ratio: float,
    unsupported_count: int,
    input_chars: int,
    elapsed_ms: int,
) -> dict[str, Any]:
    claims = candidate["claims"]
    candidate_count = len(claims)
    unsupported_rate = unsupported_count / candidate_count if candidate_count else 0.0
    faithfulness_status = candidate.get("faithfulness_status") or ("passed" if valid else "failed")
    return {
        "round_number": 1,
        "status": "valid" if valid else "invalid",
        "body_sha256": _body_sha256(candidate["final_body"]),
        "candidate_claim_count": candidate_count,
        "final_claim_count": candidate_count if valid else 0,
        "unsupported_claim_count": unsupported_count,
        "unsupported_claim_rate": round(unsupported_rate, 6),
        "coverage_ratio": round(coverage_ratio, 6),
        "retained_input_unit_ratio": round(retained_ratio, 6),
        "faithfulness_status": faithfulness_status,
        "input_chars": input_chars,
        "output_chars": len(candidate["final_body"]),
        "provider_input_tokens": candidate.get("provider_input_tokens"),
        "provider_output_tokens": candidate.get("provider_output_tokens"),
        "provider_attempt_count": candidate.get("provider_attempt_count", 1),
        "elapsed_ms": elapsed_ms,
        "stop_reason": reason,
    }


def _planned_draft(
    decision: Mapping[str, Any],
    *,
    default_root: str,
    draft_id: str,
    planned_generator_calls: int,
) -> dict[str, Any]:
    targets = [str(path) for path in decision.get("target_paths", [])]
    stable_topic_id = decision.get("topic_id")
    if isinstance(stable_topic_id, str) and stable_topic_id:
        targets = [topic_part_path(default_root, stable_topic_id, 1)]
    if not targets:
        targets = [f"{default_root}/digest/{draft_id}.md"]
    return {
        "draft_id": draft_id,
        "cluster_id": decision["cluster_id"],
        "topic_id": stable_topic_id,
        "action": decision["action"],
        "target_paths": targets,
        "final_body": "",
        "claims": [],
        "removed_claims": [],
        "provenance": [],
        "faithfulness_status": None,
        "split_suggestion": None,
        "split_pages": [],
        "component_coverage": [],
        "coverage_mapping": [],
        "rounds": [],
        "selected_round": None,
        "round_count": 0,
        "rethink_status": "planned",
        "fallback_reason": None,
        "benefit_status": "unmeasured",
        "planned_generator_calls": planned_generator_calls,
        "quality": {
            "coverage_ratio": None,
            "retained_input_unit_ratio": None,
            "unsupported_claim_rate": None,
            "faithfulness_status": None,
        },
    }


def draft(
    decisions: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    settings: DigestSettings,
    *,
    generator: Generator | None = None,
    dry_run: bool = False,
    publication: PublicationContract | None = None,
    topic_universe: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate traceable drafts with bounded, auditable rethink rounds.

    The optional ``generator`` is a local seam for deterministic providers and
    tests.  It receives a context object and may return a body string or a
    mapping containing ``final_body`` plus optional quality facts.
    """
    by_id = {item["raw_id"]: item for item in raw_items}
    clusters_by_id = {cluster["cluster_id"]: cluster for cluster in clusters}
    provider_supplied = generator is not None
    drafts: list[dict[str, Any]] = []
    unsupported_records: list[dict[str, Any]] = []
    split_suggestions: list[dict[str, Any]] = []
    for decision in decisions:
        items = [by_id[raw_id] for raw_id in clusters_by_id[decision["cluster_id"]]["members"]]
        claims, unsupported = verify_claims(items)
        filtered_lines = [line for item in items for line in item["text"].splitlines() if not _is_unsupported(line)]
        initial_body = "\n".join(filtered_lines).strip()
        provenance = sorted({claim["source_uri"] for claim in claims})
        draft_id = f"draft-{len(drafts) + 1}"
        default_root = str(decision.get("page_root", "pages"))
        stable_topic_id = decision.get("topic_id")
        base_target = (
            topic_part_path(default_root, stable_topic_id, 1)
            if isinstance(stable_topic_id, str) and stable_topic_id
            else str(decision["target_paths"][0])
            if decision.get("target_paths")
            else f"{default_root}/digest/{draft_id}.md"
        )
        base_context = {
            "items": items,
            "source_text": "\n".join(str(item.get("text", "")) for item in items),
            "initial_body": initial_body,
            "claims": [dict(claim) for claim in claims],
            "old_target_body": str(decision.get("old_target_body", "")),
            "target_page": base_target,
            "summary_enabled": settings.llm_summary_enabled,
            "publication_enabled": publication is not None,
            "publication_only": publication is not None and settings.llm_enabled and not provider_supplied,
            # Explicit test/fake generators are a supported seam.  The live
            # Task2 CLI path must use the approved qwen endpoint, while a
            # caller-supplied generator is validated by its own test contract.
            "publication_provider_enforced": publication is not None and settings.llm_enabled and not provider_supplied,
            "allowed_taxonomy": (
                [
                    {
                        "id": category.category_id,
                        "title": category.title,
                        "parent_id": category.parent_id,
                        "aliases": list(category.aliases),
                    }
                    for category in publication.categories
                ]
                if publication is not None
                else []
            ),
        }
        topic_index = decision.get("topic_index")
        if isinstance(topic_index, Mapping):
            base_context["page_draft"] = build_page_draft(
                topic_index=topic_index,
                fragments=normalize_structure(items),
                claims=claims,
            )
            base_context["page_draft"]["claims"] = [dict(claim) for claim in claims]
            base_context["typed_section_contract"] = {
                "page_type": base_context["page_draft"].get("page_type"),
                "required_sections": list(base_context["page_draft"].get("required_sections", [])),
                "optional_sections": list(base_context["page_draft"].get("optional_sections", [])),
                "section_audits": {
                    str(section_id): dict(audit)
                    for section_id, audit in (base_context["page_draft"].get("section_audits") or {}).items()
                    if isinstance(audit, Mapping)
                },
            }
            if base_context["page_draft"].get("status") == "draft":
                # A mapped Task 2-B page must ask the provider for the typed
                # body contract. Publication-only metadata is reserved for
                # topics that cannot safely enter the body compiler.
                base_context["publication_only"] = False
        page_draft = base_context.get("page_draft")
        page_draft_failure: str | None = None
        if settings.llm_enabled and isinstance(page_draft, Mapping) and page_draft.get("status") != "draft":
            # A TopicIndex row without a safe page type is already a trusted
            # degraded outcome. Do not spend provider calls on a page that the
            # compiler is forbidden to publish, and do not let publication
            # metadata make an unmapped page look reader-eligible.
            audit_record = page_draft.get("audit_record")
            page_draft_failure = str(
                audit_record.get("reason")
                if isinstance(audit_record, Mapping)
                else "page draft is not publishable"
            )
            generation_contexts = []
        else:
            generation_contexts = (
                _generation_contexts(
                    items,
                    claims,
                    base_context=base_context,
                    max_claims=settings.llm_batch_max_claims,
                    max_chars=settings.llm_batch_max_source_chars,
                    summary_enabled=settings.llm_summary_enabled,
                )
                if settings.llm_enabled
                else [base_context]
            )
        if dry_run:
            drafts.append(
                _planned_draft(
                    decision,
                    default_root=default_root,
                    draft_id=draft_id,
                    planned_generator_calls=len(generation_contexts),
                )
            )
            continue

        generator = generator or resolve_generator(settings)
        batch_candidates: list[dict[str, Any]] = []
        batch_records: list[dict[str, Any]] = []
        failure_reason: str | None = None
        provider_failures: list[dict[str, Any]] = []

        if page_draft_failure is not None:
            skipped_candidate = _candidate_from_result(
                {
                    "final_body": initial_body,
                    "claims": claims,
                    "coverage_mapping": _coverage_for_claims(claims, base_target),
                    "valid": False,
                    "invalid_reason": page_draft_failure,
                    "provider_attempt_count": 0,
                },
                initial_body=initial_body,
                claims=claims,
                target=base_target,
                summary_enabled=settings.llm_summary_enabled,
                evidence_body=initial_body,
            )
            skipped_candidate["explicit_invalid"] = True
            skipped_candidate["invalid_reason"] = page_draft_failure
            skipped_candidate["typed_page_draft"] = dict(page_draft)
            skipped_candidate["typed_response"] = {
                "status": "degraded",
                "reader_eligible": False,
                "page_type": page_draft.get("page_type"),
                "sections": {},
                "reason": page_draft_failure,
                "audit_record": dict(page_draft.get("audit_record") or {}),
            }
            batch_candidates.append(skipped_candidate)
            batch_records.append(
                _round_record(
                    candidate=skipped_candidate,
                    valid=False,
                    reason=page_draft_failure,
                    coverage_ratio=0.0,
                    retained_ratio=0.0,
                    unsupported_count=len(claims),
                    input_chars=0,
                    elapsed_ms=0,
                )
            )
            batch_records[-1].update(
                {
                    "batch_index": 0,
                    "batch_count": 0,
                    "oversized_atomic": False,
                    "provider_call_skipped": True,
                    "provider_skip_reason": page_draft_failure,
                }
            )
            failure_reason = page_draft_failure
            provider_failures.append(
                {
                    "kind": "typed_section_contract",
                    "stage": "publication",
                    "reason": page_draft_failure,
                    "provider_call_skipped": True,
                }
            )

        def run_batch(
            batch_index: int, context: dict[str, Any]
        ) -> tuple[int, dict[str, Any], dict[str, Any], bool, str | None, dict[str, Any] | None]:
            started = time.perf_counter()
            provider_failure: dict[str, Any] | None = None
            typed_response: dict[str, Any] | None = None
            try:
                result = _invoke_generator(generator, context)
                page_draft = context.get("page_draft")
                if (
                    settings.llm_enabled
                    and not context.get("publication_only")
                    and isinstance(page_draft, Mapping)
                    and isinstance(result, (Mapping, str))
                ):
                    from .llm import validate_section_response

                    validation_input = result
                    if isinstance(result, Mapping):
                        validation_input = {
                            key: value
                            for key, value in result.items()
                            if key not in {
                                "provider_attempt_count",
                                "provider_input_tokens",
                                "provider_output_tokens",
                            }
                        }
                    typed_response = validate_section_response(page_draft, validation_input)
                    if typed_response.get("status") == "draft":
                        typed_response = _bind_typed_section_dependencies(
                            page_draft,
                            typed_response,
                            [
                                claim
                                for claim in page_draft.get("claims", context.get("claims", []))
                                if isinstance(claim, Mapping)
                            ],
                        )
                    if typed_response.get("status") != "draft":
                        provider_failure = {
                            "kind": "typed_section_contract",
                            "stage": "llm",
                            "reason": str(typed_response.get("reason") or "typed section contract failed"),
                        }
                        if isinstance(result, Mapping):
                            result = {
                                **dict(result),
                                "valid": False,
                                "invalid_reason": provider_failure["reason"],
                            }
            except ValidationError as error:
                # Provider output is untrusted. Preserve deterministic source
                # evidence, but mark this source for replay instead of
                # aborting unrelated sources in the same run.
                provider_failure = {
                    "kind": "provider_error",
                    "stage": error.stage,
                    "reason": error.reason,
                }
                result = {
                    "final_body": context["initial_body"],
                    "claims": context["claims"],
                    "coverage_mapping": _coverage_for_claims(context["claims"], base_target),
                    "valid": False,
                    "invalid_reason": error.reason,
                    "provider_input_tokens": None,
                    "provider_output_tokens": None,
                    "provider_attempt_count": 1,
                }
            elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
            batch_candidate = _candidate_from_result(
                result,
                initial_body=context["initial_body"],
                claims=context["claims"],
                target=base_target,
                summary_enabled=settings.llm_summary_enabled,
                evidence_body=context["initial_body"],
            )
            if settings.llm_summary_enabled and not batch_candidate["explicit_invalid"]:
                batch_candidate["summary"] = _repair_summary(
                    batch_candidate.get("summary"),
                    source_claims=context["claims"],
                    target=base_target,
                )
                summary_valid, summary_reason = _validate_summary(
                    batch_candidate.get("summary"),
                    source_claims=context["claims"],
                    target=base_target,
                )
                if not summary_valid:
                    batch_candidate["explicit_invalid"] = True
                    batch_candidate["invalid_reason"] = summary_reason
            (
                batch_valid,
                batch_reason,
                batch_coverage_ratio,
                batch_retained_ratio,
                batch_unsupported_count,
            ) = _validate_candidate(
                batch_candidate,
                source_claims=context["claims"],
                required_structure_lines=_required_structure_lines(
                    context["initial_body"]
                ),
            )
            batch_record = _round_record(
                candidate=batch_candidate,
                valid=batch_valid,
                reason=batch_reason,
                coverage_ratio=batch_coverage_ratio,
                retained_ratio=batch_retained_ratio,
                unsupported_count=batch_unsupported_count,
                input_chars=len(context["source_text"] + context["old_target_body"]),
                elapsed_ms=elapsed_ms,
            )
            batch_record.update(
                {
                    "batch_index": batch_index,
                    "batch_count": len(generation_contexts),
                    "oversized_atomic": bool(
                        context.get("batch_oversized_atomic", False)
                    ),
                }
            )
            if not batch_valid and provider_failure is None and settings.llm_enabled:
                provider_failure = {
                    "kind": "invalid_output",
                    "stage": "llm",
                    "reason": str(batch_reason or "provider output failed local validation"),
                }
            if provider_failure is not None:
                batch_record["provider_failure"] = provider_failure
            if typed_response is not None and typed_response.get("status") == "draft":
                batch_candidate["typed_response"] = typed_response
                batch_candidate["typed_page_draft"] = dict(context.get("page_draft", {}))
            return batch_index, batch_candidate, batch_record, batch_valid, batch_reason, provider_failure

        results: list[tuple[int, dict[str, Any], dict[str, Any], bool, str | None, dict[str, Any] | None]] = []
        if generation_contexts:
            worker_count = min(settings.llm_batch_concurrency, len(generation_contexts))
            if worker_count == 1:
                results = [
                    run_batch(batch_index, context)
                    for batch_index, context in enumerate(generation_contexts, start=1)
                ]
            else:
                with ThreadPoolExecutor(max_workers=worker_count) as executor:
                    futures = [
                        executor.submit(run_batch, batch_index, context)
                        for batch_index, context in enumerate(generation_contexts, start=1)
                    ]
                    results = [future.result() for future in futures]
        for batch_index, batch_candidate, batch_record, batch_valid, batch_reason, provider_failure in results:
            batch_candidates.append(batch_candidate)
            batch_records.append(batch_record)
            if provider_failure is not None:
                provider_failures.append(
                    {
                        **provider_failure,
                        "batch_index": batch_index,
                        "batch_count": len(generation_contexts),
                    }
                )
            if not batch_valid and failure_reason is None:
                failure_reason = (
                    str(batch_reason)
                    if len(generation_contexts) == 1
                    else f"batch {batch_index}: {batch_reason}"
                )

        publication_candidates = [
            dict(batch.get("publication"))
            for batch in batch_candidates
            if isinstance(batch.get("publication"), Mapping)
        ]
        merged_typed_response = None
        if (
            failure_reason is None
            and isinstance(page_draft, Mapping)
            and page_draft.get("status") == "draft"
        ):
            merged_typed_response = _merge_typed_responses(page_draft, batch_candidates)
            if isinstance(merged_typed_response, Mapping):
                merged_typed_response = _bind_typed_section_dependencies(
                    page_draft,
                    merged_typed_response,
                    [claim for claim in claims if isinstance(claim, Mapping)],
                )
            if merged_typed_response is None:
                failure_reason = "typed section responses could not be merged"
                provider_failures.append(
                    {
                        "kind": "typed_section_contract",
                        "stage": "llm",
                        "reason": failure_reason,
                    }
                )
        merged_publication: dict[str, Any] | None = None
        if publication_candidates:
            merged_publication = dict(publication_candidates[0])
            for field in ("claim_refs", "related_topics"):
                merged: list[str] = []
                for publication_candidate in publication_candidates:
                    values = publication_candidate.get(field, [])
                    if isinstance(values, list):
                        for value in values:
                            item = str(value)
                            if item and item not in merged:
                                merged.append(item)
                merged_publication[field] = merged
            field_refs: dict[str, list[str]] = {}
            for publication_candidate in publication_candidates:
                raw_field_refs = publication_candidate.get("field_refs", {})
                if not isinstance(raw_field_refs, Mapping):
                    continue
                for field, values in raw_field_refs.items():
                    if not isinstance(values, list):
                        continue
                    field_refs.setdefault(str(field), [])
                    for value in values:
                        item = str(value)
                        if item and item not in field_refs[str(field)]:
                            field_refs[str(field)].append(item)
            if field_refs:
                merged_publication["field_refs"] = field_refs

        candidate = {
            "final_body": "\n\n".join(
                batch["final_body"] for batch in batch_candidates if batch["final_body"]
            ).strip(),
            "claims": [
                dict(claim)
                for batch in batch_candidates
                for claim in batch["claims"]
            ],
            "coverage_mapping": [
                dict(row)
                for batch in batch_candidates
                for row in batch["coverage_mapping"]
            ],
            "component_coverage": [
                dict(row)
                for batch in batch_candidates
                for row in batch.get("component_coverage", [])
            ],
            "faithfulness_status": (
                "passed"
                if batch_candidates
                and all(
                    (batch.get("faithfulness_status") or "passed")
                    in {"faithful", "passed"}
                    for batch in batch_candidates
                )
                else ""
            ),
            "explicit_invalid": False,
            "invalid_reason": failure_reason,
            "provider_input_tokens": _sum_optional_int(
                [batch.get("provider_input_tokens") for batch in batch_candidates]
            ),
            "provider_output_tokens": _sum_optional_int(
                [batch.get("provider_output_tokens") for batch in batch_candidates]
            ),
            "provider_attempt_count": sum(
                int(batch.get("provider_attempt_count", 1)) for batch in batch_candidates
            ),
            "publication": merged_publication,
            "summary": (
                {
                    "status": "validated",
                    "segments": [
                        dict(segment)
                        for batch in batch_candidates
                        for segment in (batch.get("summary") or {}).get("segments", [])
                    ],
                }
                if settings.llm_summary_enabled and failure_reason is None
                else None
            ),
            "provider_failures": provider_failures,
            "typed_response": (
                dict(merged_typed_response)
                if isinstance(merged_typed_response, Mapping)
                else (
                    dict(batch_candidates[0].get("typed_response"))
                    if len(batch_candidates) == 1 and isinstance(batch_candidates[0].get("typed_response"), Mapping)
                    else None
                )
            ),
            "typed_page_draft": (
                dict(page_draft)
                if isinstance(merged_typed_response, Mapping) and isinstance(page_draft, Mapping)
                else (
                    dict(batch_candidates[0].get("typed_page_draft"))
                    if len(batch_candidates) == 1 and isinstance(batch_candidates[0].get("typed_page_draft"), Mapping)
                    else None
                )
            ),
        }
        if settings.llm_summary_enabled and candidate.get("summary"):
            for index, segment in enumerate(candidate["summary"]["segments"], start=1):
                segment["summary_id"] = f"summary-{index}"
                segment["supports"] = [
                    dict(support, target_path=base_target)
                    for support in segment.get("supports", [])
                ]
            candidate["final_body"] = _render_summary(candidate["summary"], initial_body)
        if failure_reason is None:
            (
                valid,
                reason,
                coverage_ratio,
                retained_ratio,
                unsupported_count,
            ) = _validate_candidate(
                candidate,
                source_claims=claims,
                required_structure_lines=_required_structure_lines(initial_body),
            )
        else:
            valid = False
            reason = failure_reason
            coverage_ratio = 0.0
            retained_ratio = 0.0
            unsupported_count = max(0, len(claims) - len(candidate["claims"]))
        round_record = _round_record(
            candidate=candidate,
            valid=valid,
            reason=reason,
            coverage_ratio=coverage_ratio,
            retained_ratio=retained_ratio,
            unsupported_count=unsupported_count,
            input_chars=sum(
                int(record.get("input_chars", 0)) for record in batch_records
            ),
            elapsed_ms=sum(
                int(record.get("elapsed_ms", 0)) for record in batch_records
            ),
        )
        round_record["provider_call_count"] = sum(
            int(record.get("provider_attempt_count", 1)) for record in batch_records
        )
        round_record["batches"] = batch_records
        rounds = [round_record]
        selected: dict[str, Any] | None = candidate if valid else None
        selected_round: int | None = 1 if valid else None

        fallback_reason: str | None = None
        if selected is None:
            fallback_body, fallback_status = faithfulness_check(claims, initial_body)
            selected = {
                "final_body": fallback_body,
                "claims": [dict(claim) for claim in claims],
                "coverage_mapping": _coverage_for_claims(claims, base_target),
                "component_coverage": [],
                "faithfulness_status": fallback_status,
                "provider_input_tokens": None,
                "provider_output_tokens": None,
                "summary": {"status": "rejected", "segments": []}
                if settings.llm_summary_enabled
                else None,
            }
            fallback_reason = "no valid round; used claim fallback"
            rethink_status = "fallback"
        else:
            rethink_status = "completed"

        final_body = selected["final_body"]
        final_claims = _dedupe_claims(selected["claims"])
        final_coverage = selected["coverage_mapping"]
        faithfulness_status = selected.get("faithfulness_status") or "passed"
        has_long_item = any(len(item["text"].splitlines()) > settings.max_lines for item in items)
        requested_targets = [str(path) for path in decision.get("target_paths", [])]
        if has_long_item:
            pages, suggestion = _build_pages(
                items,
                final_claims,
                max_lines=settings.max_lines,
                base_target=base_target,
                draft_id=draft_id,
            )
            if len(requested_targets) > 1:
                # A multi-target merge is a contribution to every retrieved
                # page. Keep the long source whole on each requested page;
                # single-target runs retain the existing split suggestion.
                original_component_rows = [
                    dict(row) for row in suggestion.get("component_coverage", [])
                ]
                original_components = [
                    dict(component)
                    for page in suggestion.get("pages", [])
                    for component in page.get("components", [])
                ]
                pages = [
                    {
                        "page_index": index,
                        "target_path": target,
                        "final_body": final_body,
                        "claims": [dict(claim, page_index=index, target_path=target) for claim in final_claims],
                        "components": original_components,
                        "oversized_components": [],
                    }
                    for index, target in enumerate(requested_targets, start=1)
                ]
                suggestion["output_pages"] = requested_targets
                suggestion["pages"] = [
                    {
                        "page_index": page["page_index"],
                        "target_path": page["target_path"],
                        "components": page["components"],
                        "unsplittable_components": page["oversized_components"],
                    }
                    for page in pages
                ]
                suggestion["component_coverage"] = [
                    dict(row, output_page=target)
                    for target in requested_targets
                    for row in original_component_rows
                ]
                suggestion["coverage_mapping"] = [
                    row
                    for target in requested_targets
                    for row in _coverage_for_claims(final_claims, target)
                ]
                target_set = set(requested_targets)
                suggestion["coverage_complete"] = bool(
                    target_set
                    and all(
                        row.get("output_page") in target_set
                        for row in suggestion["coverage_mapping"]
                        + suggestion["component_coverage"]
                    )
                    and {
                        (row.get("raw_id"), row.get("input_fragment"))
                        for row in suggestion["coverage_mapping"]
                    }
                    >= {
                        (claim.get("raw_id"), claim.get("fragment_locator"))
                        for claim in final_claims
                    }
                )
            split_suggestions.append(suggestion)
        else:
            targets = requested_targets or [base_target]
            pages = [
                {
                    "page_index": index,
                    "target_path": target,
                    "final_body": final_body,
                    "claims": [dict(claim, page_index=index, target_path=target) for claim in final_claims],
                    "components": [],
                    "oversized_components": [],
                }
                for index, target in enumerate(targets, start=1)
            ]

        removed = []
        for claim in unsupported:
            record = dict(claim)
            record.update(
                {
                    "original_text": claim["text"],
                    "reason": claim.get("reason") or "claim failed local faithfulness validation",
                    "verification_status": "pending_review",
                }
            )
            removed.append(record)
            unsupported_records.append({"draft_id": draft_id, **record})

        publication_metadata = None
        if publication is not None:
            publication_metadata = validate_publication_suggestion(
                selected.get("publication"),
                claims=final_claims,
                publication=publication,
                topic_universe=topic_universe,
                fallback_title=(_publication_title_candidates(items) or [None])[0],
                stable_topic_id=stable_topic_id,
                fallback_category_id=(
                    deterministic_category_id(
                        "\n".join(
                            " ".join(
                                [
                                    str(item.get("text", "")),
                                    str(item.get("input_path", "")),
                                    " ".join(
                                        str(value)
                                        for value in (item.get("source_meta") or {}).values()
                                        if isinstance(value, (str, int, float))
                                    ),
                                ]
                            )
                            for item in items
                        ),
                        publication,
                    )
                    if len(publication.categories) > 1
                    else None
                ),
            )

        draft_record = {
            "draft_id": draft_id,
            "cluster_id": decision["cluster_id"],
            "topic_id": stable_topic_id,
            "publication_title_candidates": _publication_title_candidates(items),
            "publication": publication_metadata.as_dict() if publication_metadata is not None else None,
            "action": decision["action"],
            "target_paths": [page["target_path"] for page in pages],
            "final_body": final_body,
            "claims": final_claims,
            "summary": selected.get("summary"),
            "removed_claims": removed,
            "provenance": provenance,
            "faithfulness_status": faithfulness_status,
            "split_suggestion": split_suggestions[-1] if has_long_item else None,
            "split_pages": pages,
            "component_coverage": (split_suggestions[-1]["component_coverage"] if has_long_item else []),
            "coverage_mapping": (
                split_suggestions[-1]["coverage_mapping"]
                if has_long_item and len(requested_targets) <= 1
                else [
                    row
                    for page in pages
                    for row in _coverage_for_claims(page["claims"], page["target_path"])
                ]
                if pages
                else final_coverage
            ),
            "rounds": rounds,
            "selected_round": selected_round,
            "round_count": len(rounds),
            "rethink_status": rethink_status,
            "fallback_reason": fallback_reason,
            "provider_failure": bool(provider_failures),
            "provider_failures": provider_failures,
            "typed_response": candidate.get("typed_response"),
            "typed_page_draft": candidate.get("typed_page_draft"),
            "benefit_status": "unmeasured",
            "planned_generator_calls": len(generation_contexts),
            "quality": {
                "coverage_ratio": rounds[selected_round - 1]["coverage_ratio"] if selected_round else 0.0,
                "retained_input_unit_ratio": rounds[selected_round - 1]["retained_input_unit_ratio"] if selected_round else 0.0,
                "unsupported_claim_rate": rounds[selected_round - 1]["unsupported_claim_rate"] if selected_round else 0.0,
                "faithfulness_status": faithfulness_status,
            },
        }
        drafts.append(draft_record)

    write_jsonl(run_dir / "s4" / "drafts.jsonl", drafts)
    write_jsonl(run_dir / "s4" / "unsupported-claims.jsonl", unsupported_records)
    write_jsonl(run_dir / "s4" / "split-suggestions.jsonl", split_suggestions)
    write_jsonl(run_dir / "s4" / "coverage-mapping.jsonl", [row for draft_record in drafts for row in draft_record["coverage_mapping"]])
    write_jsonl(run_dir / "s4" / "component-coverage.jsonl", [row for draft_record in drafts for row in draft_record.get("component_coverage", [])])
    write_jsonl(
        run_dir / "s4" / "rounds.jsonl",
        [
            {
                "draft_id": draft_record["draft_id"],
                "cluster_id": draft_record["cluster_id"],
                "rounds": draft_record.get("rounds", []),
                "selected_round": draft_record.get("selected_round"),
                "round_count": draft_record.get("round_count", 0),
                "rethink_status": draft_record.get("rethink_status"),
                "fallback_reason": draft_record.get("fallback_reason"),
                "benefit_status": draft_record.get("benefit_status", "unmeasured"),
                "quality": draft_record.get("quality", {}),
            }
            for draft_record in drafts
        ],
    )
    return drafts
