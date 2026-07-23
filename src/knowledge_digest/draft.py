"""Stage 4: faithful claims and deterministic long-document reorganization."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .config import DigestSettings
from .faithfulness import faithfulness_check, verify_claims
from .jsonl import write_jsonl


_HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
_FAQ_RE = re.compile(r"^\s*(?:FAQ|Q(?:uestion)?)[\s:：]", re.IGNORECASE)
_ERROR_RE = re.compile(r"^\s*(?:Error\s+)?[A-Z][A-Z0-9_-]*\d+[\s:：-]", re.IGNORECASE)
_PARAM_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:parameter|param|argument)\b[^:：]*[:：]", re.IGNORECASE)


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


def draft(
    decisions: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    settings: DigestSettings,
) -> list[dict[str, Any]]:
    """Generate traceable drafts and complete split plans without truncation."""
    by_id = {item["raw_id"]: item for item in raw_items}
    clusters_by_id = {cluster["cluster_id"]: cluster for cluster in clusters}
    drafts: list[dict[str, Any]] = []
    unsupported_records: list[dict[str, Any]] = []
    split_suggestions: list[dict[str, Any]] = []
    for decision in decisions:
        items = [by_id[raw_id] for raw_id in clusters_by_id[decision["cluster_id"]]["members"]]
        claims, unsupported = verify_claims(items)
        filtered_lines = [
            line
            for item in items
            for line in item["text"].splitlines()
            if not _is_unsupported(line)
        ]
        initial_body = "\n".join(filtered_lines).strip()
        final_body, faithfulness_status = faithfulness_check(claims, initial_body)
        provenance = sorted({claim["source_uri"] for claim in claims})
        draft_id = f"draft-{len(drafts) + 1}"
        default_root = str(decision.get("page_root", "pages"))
        base_target = str(decision["target_paths"][0]) if decision.get("target_paths") else f"{default_root}/digest/{draft_id}.md"
        has_long_item = any(len(item["text"].splitlines()) > settings.max_lines for item in items)
        if has_long_item:
            pages, suggestion = _build_pages(
                items,
                claims,
                max_lines=settings.max_lines,
                base_target=base_target,
                draft_id=draft_id,
            )
            split_suggestions.append(suggestion)
        else:
            pages = [
                {
                    "page_index": 1,
                    "target_path": base_target,
                    "final_body": final_body,
                    "claims": [dict(claim, page_index=1, target_path=base_target) for claim in claims],
                    "components": [],
                    "oversized_components": [],
                }
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

        draft_record = {
            "draft_id": draft_id,
            "cluster_id": decision["cluster_id"],
            "action": decision["action"],
            "target_paths": [page["target_path"] for page in pages],
            "final_body": final_body,
            "claims": claims,
            "removed_claims": removed,
            "provenance": provenance,
            "faithfulness_status": faithfulness_status,
            "split_suggestion": split_suggestions[-1] if has_long_item else None,
            "split_pages": pages,
            "component_coverage": (split_suggestions[-1]["component_coverage"] if has_long_item else []),
            "coverage_mapping": (split_suggestions[-1]["coverage_mapping"] if has_long_item else [
                {
                    "raw_id": claim.get("raw_id"),
                    "source_uri": claim.get("source_uri"),
                    "input_fragment": claim.get("fragment_locator"),
                    "output_page": base_target,
                    "fragment_locator": claim.get("fragment_locator"),
                    "claim_fingerprint": claim.get("claim_fingerprint"),
                }
                for claim in claims
            ]),
        }
        drafts.append(draft_record)

    write_jsonl(run_dir / "s4" / "drafts.jsonl", drafts)
    write_jsonl(run_dir / "s4" / "unsupported-claims.jsonl", unsupported_records)
    write_jsonl(run_dir / "s4" / "split-suggestions.jsonl", split_suggestions)
    write_jsonl(run_dir / "s4" / "coverage-mapping.jsonl", [row for draft_record in drafts for row in draft_record["coverage_mapping"]])
    write_jsonl(run_dir / "s4" / "component-coverage.jsonl", [row for draft_record in drafts for row in draft_record.get("component_coverage", [])])
    return drafts
