"""Stage 4: faithful claims and deterministic long-document reorganization."""

from __future__ import annotations

import hashlib
import inspect
import re
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from .config import DigestSettings, risk_decision
from .faithfulness import faithfulness_check, normalize_newlines, verify_claims
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


def default_generator(context: dict[str, Any]) -> dict[str, Any]:
    """The local generation boundary used until a provider is supplied.

    Keeping this as a callable makes the round controller testable without
    introducing a provider dependency.  The default remains deterministic and
    faithful to the existing claim concatenation behavior.
    """
    return {"final_body": context["initial_body"]}


def _invoke_generator(generator: Generator, context: dict[str, Any]) -> Any:
    """Call supported generator shapes without hiding generator exceptions."""
    try:
        parameters = list(inspect.signature(generator).parameters.values())
    except (TypeError, ValueError):
        parameters = []
    positional = [
        parameter
        for parameter in parameters
        if parameter.kind in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
    ]
    if len(positional) <= 1:
        return generator(context)
    if len(positional) == 2:
        return generator(context["items"], context)
    return generator(context["items"], context["previous_body"], context)


def _candidate_from_result(
    result: Any,
    *,
    initial_body: str,
    claims: list[dict[str, Any]],
    target: str,
) -> dict[str, Any]:
    if isinstance(result, str):
        result = {"final_body": result}
    if not isinstance(result, Mapping):
        result = {"final_body": initial_body, "valid": False, "invalid_reason": "generator returned a non-object"}
    body = str(result.get("final_body", result.get("body", initial_body)))
    candidate_claims = [dict(claim) for claim in result.get("claims", claims)]
    coverage = result.get("coverage_mapping")
    if coverage is None:
        coverage = _coverage_for_claims(candidate_claims, target)
    else:
        coverage = [dict(row) for row in coverage if isinstance(row, Mapping)]
    faithfulness_status = str(result.get("faithfulness_status", result.get("faithfulness", "")))
    explicit_invalid = result.get("valid") is False or result.get("status") == "invalid"
    if faithfulness_status.casefold() in {"failed", "invalid", "unfaithful"}:
        explicit_invalid = True
    return {
        "final_body": body,
        "claims": candidate_claims,
        "coverage_mapping": coverage,
        "component_coverage": [dict(row) for row in result.get("component_coverage", []) if isinstance(row, Mapping)],
        "faithfulness_status": faithfulness_status,
        "explicit_invalid": explicit_invalid,
        "invalid_reason": result.get("invalid_reason") or result.get("reason"),
        "provider_input_tokens": result.get("provider_input_tokens", result.get("input_tokens")),
        "provider_output_tokens": result.get("provider_output_tokens", result.get("output_tokens")),
    }


def _validate_candidate(
    candidate: dict[str, Any],
    *,
    source_claims: list[dict[str, Any]],
) -> tuple[bool, str | None, float, float, int]:
    """Apply source, coverage, and faithfulness hard gates to one candidate."""
    if candidate["explicit_invalid"]:
        return False, str(candidate.get("invalid_reason") or "candidate marked invalid"), 0.0, 0.0, 0
    source_fingerprints = {claim.get("claim_fingerprint") for claim in source_claims}
    candidate_claims = candidate["claims"]
    if any(claim.get("claim_fingerprint") not in source_fingerprints for claim in candidate_claims):
        return False, "candidate contains a claim not present in the source", 0.0, 0.0, 0
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
    if not all(claim["text"] in candidate["final_body"] for claim in candidate_claims):
        return False, "candidate failed faithfulness hard gate", coverage_ratio, 0.0, 0
    eligible = len(source_claims)
    retained = len(candidate_claims)
    retained_ratio = retained / eligible if eligible else 1.0
    unsupported_count = max(0, len(source_claims) - len(candidate_claims))
    return True, None, coverage_ratio, retained_ratio, unsupported_count


def _round_record(
    *,
    round_number: int,
    candidate: dict[str, Any],
    valid: bool,
    reason: str | None,
    coverage_ratio: float,
    retained_ratio: float,
    unsupported_count: int,
    input_chars: int,
    elapsed_ms: int,
    stop_reason: str | None,
) -> dict[str, Any]:
    claims = candidate["claims"]
    candidate_count = len(claims)
    unsupported_rate = unsupported_count / candidate_count if candidate_count else 0.0
    faithfulness_status = candidate.get("faithfulness_status") or ("passed" if valid else "failed")
    return {
        "round_number": round_number,
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
        "elapsed_ms": elapsed_ms,
        "stop_reason": stop_reason or reason,
    }


def _planned_draft(
    decision: Mapping[str, Any],
    risk: dict[str, Any],
    *,
    default_root: str,
    draft_id: str,
) -> dict[str, Any]:
    targets = [str(path) for path in decision.get("target_paths", [])]
    if not targets:
        targets = [f"{default_root}/digest/{draft_id}.md"]
    return {
        "draft_id": draft_id,
        "cluster_id": decision["cluster_id"],
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
        "risk_decision": risk,
        "rounds": [],
        "selected_round": None,
        "round_count": 0,
        "max_rounds": risk["max_rounds"],
        "rethink_status": "planned",
        "fallback_reason": None,
        "benefit_status": "unmeasured",
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
) -> list[dict[str, Any]]:
    """Generate traceable drafts with bounded, auditable rethink rounds.

    The optional ``generator`` is a local seam for deterministic providers and
    tests.  It receives a context object and may return a body string or a
    mapping containing ``final_body`` plus optional quality facts.
    """
    by_id = {item["raw_id"]: item for item in raw_items}
    clusters_by_id = {cluster["cluster_id"]: cluster for cluster in clusters}
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
        base_target = str(decision["target_paths"][0]) if decision.get("target_paths") else f"{default_root}/digest/{draft_id}.md"
        risk = risk_decision(
            cluster=clusters_by_id[decision["cluster_id"]],
            decision=decision,
            items=items,
            max_doc_lines=settings.max_lines,
        )
        decision["risk_decision"] = risk
        if dry_run:
            drafts.append(_planned_draft(decision, risk, default_root=default_root, draft_id=draft_id))
            continue

        max_rounds = int(risk["max_rounds"])
        rounds: list[dict[str, Any]] = []
        selected: dict[str, Any] | None = None
        selected_round: int | None = None
        previous_body = ""
        generator = generator or default_generator
        last_round_valid = False
        for round_number in range(1, max_rounds + 1):
            context = {
                "items": items,
                "source_text": "\n".join(str(item.get("text", "")) for item in items),
                "initial_body": initial_body,
                "previous_body": previous_body,
                "risk_decision": risk,
                "round_number": round_number,
                "claims": [dict(claim) for claim in claims],
                "old_target_body": str(decision.get("old_target_body", "")),
            }
            started = time.perf_counter()
            result = _invoke_generator(generator, context)
            elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
            candidate = _candidate_from_result(
                result,
                initial_body=initial_body,
                claims=claims,
                target=base_target,
            )
            valid, reason, coverage_ratio, retained_ratio, unsupported_count = _validate_candidate(
                candidate,
                source_claims=claims,
            )
            stop_reason: str | None = None
            if valid and last_round_valid and normalize_newlines(candidate["final_body"]).encode("utf-8") == normalize_newlines(previous_body).encode("utf-8"):
                stop_reason = "converged"
            elif round_number == max_rounds:
                stop_reason = "max_rounds"
            record = _round_record(
                round_number=round_number,
                candidate=candidate,
                valid=valid,
                reason=reason,
                coverage_ratio=coverage_ratio,
                retained_ratio=retained_ratio,
                unsupported_count=unsupported_count,
                input_chars=len(context["source_text"] + context["old_target_body"] + previous_body),
                elapsed_ms=elapsed_ms,
                stop_reason=stop_reason,
            )
            rounds.append(record)
            if valid:
                selected = candidate
                selected_round = round_number
                previous_body = candidate["final_body"]
                last_round_valid = True
            else:
                last_round_valid = False
            if stop_reason:
                break

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
            }
            fallback_reason = "no valid round; used claim fallback"
            rethink_status = "fallback"
        elif rounds[-1]["stop_reason"] == "converged":
            rethink_status = "converged"
        else:
            rethink_status = "max_rounds" if len(rounds) == max_rounds else "completed"
            if any(round_record["status"] == "invalid" for round_record in rounds):
                fallback_reason = "invalid round rejected; retained latest valid round"

        final_body = selected["final_body"]
        final_claims = selected["claims"]
        final_coverage = selected["coverage_mapping"]
        faithfulness_status = selected.get("faithfulness_status") or "passed"
        has_long_item = any(len(item["text"].splitlines()) > settings.max_lines for item in items)
        if has_long_item:
            pages, suggestion = _build_pages(
                items,
                final_claims,
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
                    "claims": [dict(claim, page_index=1, target_path=base_target) for claim in final_claims],
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
            "claims": final_claims,
            "removed_claims": removed,
            "provenance": provenance,
            "faithfulness_status": faithfulness_status,
            "split_suggestion": split_suggestions[-1] if has_long_item else None,
            "split_pages": pages,
            "component_coverage": (split_suggestions[-1]["component_coverage"] if has_long_item else []),
            "coverage_mapping": (split_suggestions[-1]["coverage_mapping"] if has_long_item else final_coverage),
            "risk_decision": risk,
            "rounds": rounds,
            "selected_round": selected_round,
            "round_count": len(rounds),
            "max_rounds": max_rounds,
            "rethink_status": rethink_status,
            "fallback_reason": fallback_reason,
            "benefit_status": "unmeasured",
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
                "risk_decision": draft_record.get("risk_decision"),
                "rounds": draft_record.get("rounds", []),
                "selected_round": draft_record.get("selected_round"),
                "round_count": draft_record.get("round_count", 0),
                "max_rounds": draft_record.get("max_rounds"),
                "rethink_status": draft_record.get("rethink_status"),
                "fallback_reason": draft_record.get("fallback_reason"),
                "benefit_status": draft_record.get("benefit_status", "unmeasured"),
                "quality": draft_record.get("quality", {}),
            }
            for draft_record in drafts
        ],
    )
    return drafts
