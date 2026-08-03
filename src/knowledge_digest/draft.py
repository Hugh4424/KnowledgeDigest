"""Stage 4: faithful claims and deterministic long-document reorganization."""

from __future__ import annotations

import hashlib
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
from .publication import deterministic_category_id, validate_publication_suggestion


_HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
_TITLE_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")
_FAQ_RE = re.compile(r"^\s*(?:FAQ|Q(?:uestion)?)[\s:：]", re.IGNORECASE)
_ERROR_RE = re.compile(r"^\s*(?:Error\s+)?[A-Z][A-Z0-9_-]*\d+[\s:：-]", re.IGNORECASE)
_PARAM_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:parameter|param|argument)\b[^:：]*[:：]", re.IGNORECASE)
_SUMMARY_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?")


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
    """
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

        def run_batch(
            batch_index: int, context: dict[str, Any]
        ) -> tuple[int, dict[str, Any], dict[str, Any], bool, str | None, dict[str, Any] | None]:
            started = time.perf_counter()
            provider_failure: dict[str, Any] | None = None
            try:
                result = _invoke_generator(generator, context)
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
            return batch_index, batch_candidate, batch_record, batch_valid, batch_reason, provider_failure

        worker_count = min(settings.llm_batch_concurrency, len(generation_contexts))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(run_batch, batch_index, context)
                for batch_index, context in enumerate(generation_contexts, start=1)
            ]
            for future in futures:
                batch_index, batch_candidate, batch_record, batch_valid, batch_reason, provider_failure = future.result()
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
