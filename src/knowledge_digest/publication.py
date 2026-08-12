"""Semantic publication metadata and fail-closed field validation.

The provider may suggest reader-facing wording, but this module remains the
authority for taxonomy membership, claim references, deterministic fallbacks,
and the needs-review boundary.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .errors import ValidationError
from .faithfulness import claim_fingerprint, normalize_for_gate
from .identity import readable_slug
from .kb_structure import PublicationContract


_SCHEMA_FIELDS = ("title", "slug", "category_id", "summary", "why", "version", "related_topics", "claim_refs", "field_refs")
_FIELD_REF_NAMES = ("title", "category_id", "summary", "why", "version")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_NUMERIC_RE = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?%?(?![A-Za-z0-9_])")
_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9_-]{2,}\b")
_FAITHFUL_TOKEN_RE = re.compile(r"[a-z0-9]+%?|[\u4e00-\u9fff]")

# Task 2-B's body contract is intentionally deterministic.  The provider may
# fill these sections, but it cannot add a new page type or section.
PAGE_TYPE_SECTION_MATRIX: dict[str, tuple[str, ...]] = {
    "product_overview": (
        "positioning",
        "use_cases",
        "capability_boundaries",
        "entry",
        "sources",
    ),
    "module_or_capability": (
        "purpose",
        "capabilities",
        "entry_prerequisites",
        "relationships",
        "limitations",
        "version",
        "sources",
    ),
    "procedure_or_rule": (
        "prerequisites",
        "steps_rules",
        "exceptions",
        "limitations",
        "version",
        "sources",
    ),
}

PAGE_TYPE_OPTIONAL_SECTIONS: dict[str, tuple[str, ...]] = {
    "product_overview": ("version",),
    "module_or_capability": (),
    "procedure_or_rule": (),
}

SOURCE_AUDIT_VERSION = "procedure-exceptions-audit.v1"
_SOURCE_HASH_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
_EXCEPTION_SIGNAL_RE = re.compile(
    r"(?:exception|error|failure|fail|failed|fallback|recovery|rollback|alternate|branch|"
    r"异常|错误|失败|出错|故障|回滚|恢复|备用|分支)",
    re.IGNORECASE,
)
_EXPLICIT_EXCEPTION_RULE_RE = (
    re.compile(
        r"(?:if|when|in\s+case|on)\b[^\n.!?]{0,120}"
        r"(?:exception|error|failure|fail|failed)\b[^\n.!?]{0,160}"
        r"(?:then|should|must|keep|retry|record|rollback|recover|switch|use)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:如果|当|出现|发生|遇到)[^\n。！？!?]{0,100}"
        r"(?:异常|错误|失败|出错|故障)[^\n。！？!?]{0,120}"
        r"(?:则|应|需要|保留|重试|记录|回滚|恢复|切换|处理)",
    ),
    re.compile(
        r"(?:exception|error|failure|异常|错误|失败)[^\n。！？!?]{0,80}"
        r"(?:handling|fallback|recovery|rollback|处理|恢复|回滚|备用|分支)",
        re.IGNORECASE,
    ),
)


def _source_audit_dependency(fragment: Mapping[str, Any]) -> dict[str, str] | None:
    source_uri = str(fragment.get("source_uri") or "").strip()
    content_hash = str(
        fragment.get("content_fingerprint")
        or fragment.get("content_hash")
        or ""
    ).strip()
    locator = str(
        fragment.get("fragment_locator")
        or fragment.get("source_locator")
        or ""
    ).strip()
    if not source_uri or not locator or not _SOURCE_HASH_RE.fullmatch(content_hash):
        return None
    return {
        "source_uri": source_uri,
        "content_hash": content_hash,
        "fragment_locator": locator,
    }


def audit_procedure_exceptions_source(
    fragments: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    """Classify the frozen source for the fixed procedure exceptions section.

    This is deliberately conservative and source-only.  A provider cannot
    turn a mapping failure or an incomplete lineage record into
    ``source_not_documented``.
    """
    source_rows = [
        dict(fragment)
        for fragment in fragments
        if isinstance(fragment, Mapping)
    ]
    dependencies = []
    incomplete = False
    explicit_rule_fragments: list[str] = []
    signal_fragments: list[str] = []
    for fragment in source_rows:
        dependency = _source_audit_dependency(fragment)
        if dependency is None:
            incomplete = True
        else:
            dependencies.append(dependency)
        text = str(fragment.get("text") or "")
        if _EXCEPTION_SIGNAL_RE.search(text):
            locator = str(fragment.get("fragment_locator") or fragment.get("source_locator") or "")
            signal_fragments.append(locator)
        if any(pattern.search(text) for pattern in _EXPLICIT_EXCEPTION_RULE_RE):
            locator = str(fragment.get("fragment_locator") or fragment.get("source_locator") or "")
            explicit_rule_fragments.append(locator)
    dependencies = sorted(
        {json.dumps(row, ensure_ascii=False, sort_keys=True): row for row in dependencies}.values(),
        key=lambda row: (row["source_uri"], row["fragment_locator"]),
    )
    if not source_rows or incomplete or not dependencies:
        status = "audit_incomplete"
        reason = "source URI, content hash, or fragment locator is missing"
    elif explicit_rule_fragments:
        status = "documented"
        reason = "explicit exception handling or recovery rule is present in the frozen source"
    else:
        status = "source_not_documented"
        reason = "frozen source has no explicit exception trigger, handling, branch, or recovery rule"
    return {
        "audit_version": SOURCE_AUDIT_VERSION,
        "section_id": "exceptions",
        "status": status,
        "reason": reason,
        "source_deps": dependencies,
        "signal_fragment_locators": sorted(set(signal_fragments)),
        "explicit_rule_fragment_locators": sorted(set(explicit_rule_fragments)),
        "question_status": "not_answerable" if status == "source_not_documented" else None,
    }


def required_sections_for_page_type(page_type: str) -> tuple[str, ...]:
    """Return the immutable section contract for one accepted page type."""
    try:
        return PAGE_TYPE_SECTION_MATRIX[page_type]
    except KeyError as error:
        raise ValidationError("publication", page_type, "unknown page type") from error


def optional_sections_for_page_type(page_type: str) -> tuple[str, ...]:
    """Return optional sections whose presence still requires source evidence."""
    if page_type not in PAGE_TYPE_SECTION_MATRIX:
        raise ValidationError("publication", page_type, "unknown page type")
    return PAGE_TYPE_OPTIONAL_SECTIONS.get(page_type, ())


def _five_grams(text: str) -> set[str]:
    words = normalize_for_gate(text).split()
    return {" ".join(words[index:index + 5]) for index in range(max(0, len(words) - 4))}


def _five_gram_jaccard(left: str, right: str) -> float:
    left_grams = _five_grams(left)
    right_grams = _five_grams(right)
    if not left_grams and not right_grams:
        return 1.0
    return len(left_grams & right_grams) / max(1, len(left_grams | right_grams))


def _claim_is_supported_by_body(claim_text: str, body: str) -> bool:
    """Allow conservative paraphrases without trusting a claim id by itself."""
    # Ordered-list markers are source formatting, not facts. A provider may
    # turn ``2. fact`` into a sentence inside a paragraph; keep the fact and
    # token checks while ignoring only that leading marker.
    claim_without_list_marker = re.sub(
        r"^\s*(?:[-*+]\s+|\d+\s*[.)、]\s*)",
        "",
        str(claim_text),
    )
    claim = normalize_for_gate(claim_without_list_marker)
    rendered = normalize_for_gate(body)
    if claim and claim in rendered:
        return True
    claim_numbers = set(_NUMERIC_RE.findall(claim))
    if claim_numbers and not claim_numbers.issubset(set(_NUMERIC_RE.findall(rendered))):
        return False
    claim_identifiers = {value.casefold() for value in _IDENTIFIER_RE.findall(claim_text)}
    body_identifiers = {value.casefold() for value in _IDENTIFIER_RE.findall(body)}
    if claim_identifiers and not claim_identifiers.issubset(body_identifiers):
        return False
    claim_tokens = set(_FAITHFUL_TOKEN_RE.findall(claim))
    body_tokens = set(_FAITHFUL_TOKEN_RE.findall(rendered))
    if not claim_tokens or len(claim_tokens) < 3:
        return False
    overlap = len(claim_tokens & body_tokens)
    return overlap >= max(3, (len(claim_tokens) + 1) // 2)


_COPY_EXCEPTION_TYPES = {
    "code",
    "table",
    "bilingual",
    "public_template",
    "template",
    "attribution_quote",
}


def _sentences(value: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?。！？；;])\s+|\n+", value)
        if normalize_for_gate(sentence)
    ]


def _is_copy_exception(candidate: str, payload: Mapping[str, Any]) -> bool:
    normalized_candidate = normalize_for_gate(candidate)
    for row in payload.get("source_fragments", []):
        if not isinstance(row, Mapping):
            continue
        if str(row.get("content_type", "")).casefold() not in _COPY_EXCEPTION_TYPES:
            continue
        source_text = normalize_for_gate(str(row.get("text", "")))
        if source_text and source_text in normalized_candidate:
            return True
    for row in payload.get("copy_exceptions", []):
        if not isinstance(row, Mapping):
            continue
        kind = str(row.get("kind", "")).casefold()
        source_text = normalize_for_gate(str(row.get("text", "")))
        if kind in _COPY_EXCEPTION_TYPES and source_text and source_text in normalized_candidate:
            return True
    return False


def _continuous_source_block_check(
    body: str,
    evidence_body: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Reject long verbatim source runs while retaining explicit exceptions."""
    duplicate_context = payload.get("duplicate_context")
    check = {
        "denominator": 0,
        "detector_version": "source-block.v1",
        "seed": duplicate_context.get("seed") if isinstance(duplicate_context, Mapping) else None,
        "max_sentences": 3,
        "max_chars": 240,
        "failed_samples": [],
    }
    source_sentences = _sentences(evidence_body)
    if not source_sentences:
        return check
    normalized_body = normalize_for_gate(body)
    for start in range(len(source_sentences)):
        candidate_sentences: list[str] = []
        for end in range(start, len(source_sentences)):
            candidate_sentences.append(source_sentences[end])
            candidate = " ".join(candidate_sentences)
            normalized_candidate = normalize_for_gate(candidate)
            if not normalized_candidate or normalized_candidate not in normalized_body:
                continue
            check["denominator"] += 1
            exceeds_limit = (
                len(candidate_sentences) > check["max_sentences"]
                or len(normalized_candidate) > check["max_chars"]
            )
            if exceeds_limit and not _is_copy_exception(candidate, payload):
                check["failed_samples"].append(
                    {
                        "sample": len(check["failed_samples"]) + 1,
                        "sentence_count": len(candidate_sentences),
                        "char_count": len(normalized_candidate),
                    }
                )
                break
            if len(candidate_sentences) >= check["max_sentences"] and len(normalized_candidate) >= check["max_chars"]:
                break
    return check


def _body_gate_failure(
    payload: Mapping[str, Any],
    reasons: list[str],
    checks: dict[str, Any],
) -> dict[str, Any]:
    unique_reasons = list(dict.fromkeys(reasons))
    return {
        "status": "degraded",
        "reader_eligible": False,
        "body": str(payload.get("body", "")),
        "evidence_body": str(payload.get("evidence_body", "")),
        "reasons": unique_reasons,
        "checks": checks,
        "evidence": {"claim_backtrace": []},
        "audit_record": {
            "destination": "Audit",
            "reason": "; ".join(unique_reasons) or "publication gate rejected body",
        },
    }


def _source_not_documented_state_error(state: Mapping[str, Any]) -> str | None:
    if str(state.get("section_id") or "") != "exceptions":
        return "source_not_documented is only allowed for procedure_or_rule.exceptions"
    if str(state.get("page_type") or "") != "procedure_or_rule":
        return "source_not_documented requires procedure_or_rule"
    if str(state.get("status") or "") != "source_not_documented":
        return "source_not_documented section status is missing"
    if str(state.get("body") or "").strip() or state.get("claim_ids"):
        return "source_not_documented exceptions section must not contain body facts or claims"
    audit = state.get("source_audit")
    if not isinstance(audit, Mapping) or audit.get("audit_version") != SOURCE_AUDIT_VERSION:
        return "source_not_documented audit version is missing"
    source_deps = audit.get("source_deps")
    if not isinstance(source_deps, list) or not source_deps:
        return "source_not_documented source binding is missing"
    for dependency in source_deps:
        if not isinstance(dependency, Mapping):
            return "source_not_documented source binding is invalid"
        if (
            not str(dependency.get("source_uri") or "").strip()
            or not str(dependency.get("fragment_locator") or "").strip()
            or not _SOURCE_HASH_RE.fullmatch(str(dependency.get("content_hash") or ""))
        ):
            return "source_not_documented source binding is incomplete"
    if audit.get("question_status") != "not_answerable":
        return "source_not_documented question status is missing"
    return None


def validate_body_gate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Run the deterministic body/evidence/provenance publication gate."""
    body = str(payload.get("body", ""))
    evidence_body = str(payload.get("evidence_body", ""))
    claims = [claim for claim in payload.get("claims", []) if isinstance(claim, Mapping)]
    reasons: list[str] = []
    checks: dict[str, Any] = {
        "attribution": {"passed": True, "failed_claims": []},
        "tokens": {"passed": True, "missing": []},
        "duplicate": {
            "denominator": 0,
            "detector_version": "jaccard-5gram.v1",
            "seed": None,
            "failed_samples": [],
        },
        "continuous_source_block": {
            "denominator": 0,
            "detector_version": "source-block.v1",
            "seed": None,
            "max_sentences": 3,
            "max_chars": 240,
            "failed_samples": [],
        },
    }
    if str(payload.get("provider_status", "ok")) != "ok":
        reasons.append(f"provider failure: {payload.get('provider_status')}")
    if not body.strip():
        reasons.append("body is empty")
    if evidence_body.strip() and normalize_for_gate(body) == normalize_for_gate(evidence_body):
        reasons.append("body is an Evidence dump, not a reader answer")

    section_states = payload.get("section_states")
    if section_states is not None:
        if not isinstance(section_states, list):
            reasons.append("section states are invalid")
        else:
            for state in section_states:
                if not isinstance(state, Mapping):
                    reasons.append("section state is invalid")
                    continue
                if state.get("status") == "source_not_documented":
                    state_error = _source_not_documented_state_error(state)
                    if state_error:
                        reasons.append(state_error)

    claim_backtrace: list[dict[str, Any]] = []
    seen_claim_ids: set[str] = set()
    typed_claim_ids: set[str] | None = None
    if "typed_claim_ids" in payload:
        raw_typed_claim_ids = payload.get("typed_claim_ids")
        if not isinstance(raw_typed_claim_ids, list) or not all(
            isinstance(value, str) and value.strip() for value in raw_typed_claim_ids
        ):
            reasons.append("typed claim mapping is invalid")
        else:
            typed_claim_ids = {value.strip() for value in raw_typed_claim_ids}
            supplied_claim_ids = {
                str(claim.get("claim_id") or claim.get("claim_fingerprint") or "")
                for claim in claims
            }
            if typed_claim_ids != supplied_claim_ids:
                reasons.append("typed claim mapping is incomplete")
    for index, claim in enumerate(claims, start=1):
        claim_id = str(claim.get("claim_id") or claim.get("claim_fingerprint") or f"claim-{index}")
        if claim_id in seen_claim_ids:
            reasons.append(f"claim attribution is not unique: {claim_id}")
            checks["attribution"]["failed_claims"].append(claim_id)
            continue
        seen_claim_ids.add(claim_id)
        claim_text = str(claim.get("text", ""))
        source_uri = str(claim.get("source_uri", ""))
        fragment_locator = str(claim.get("fragment_locator", ""))
        content_fingerprint = str(
            claim.get("content_fingerprint") or claim.get("content_hash") or ""
        )
        if source_uri and claim_text:
            expected_fingerprint = claim_fingerprint(source_uri, claim_text)
            if claim.get("claim_fingerprint") and claim.get("claim_fingerprint") != expected_fingerprint:
                reasons.append(f"claim fingerprint mismatch: {claim_id}")
        if (
            not claim_text
            or not source_uri
            or not fragment_locator
            or not re.fullmatch(r"[0-9a-fA-F]{64}", content_fingerprint)
        ):
            reasons.append(f"attribution is incomplete: {claim_id}")
            checks["attribution"]["failed_claims"].append(claim_id)
            continue
        supports_claim = (
            normalize_for_gate(claim_text) in normalize_for_gate(body)
            if typed_claim_ids is None
            else _claim_is_supported_by_body(claim_text, body)
        )
        if not supports_claim:
            reasons.append(f"token or faithfulness mismatch: {claim_id}")
            checks["tokens"]["missing"].append(claim_id)
        if not re.search(r"\[\^" + re.escape(claim_id) + r"\]", body):
            reasons.append(f"attribution footnote is missing: {claim_id}")
            checks["attribution"]["failed_claims"].append(claim_id)
        claim_backtrace.append(
            {
                "claim_id": claim_id,
                "source_uri": source_uri,
                "content_fingerprint": content_fingerprint,
                "fragment_locator": fragment_locator,
                "claim_fingerprint": claim.get("claim_fingerprint") or claim_fingerprint(source_uri, claim_text),
            }
        )
    checks["attribution"]["passed"] = not checks["attribution"]["failed_claims"]
    checks["tokens"]["passed"] = not checks["tokens"]["missing"]
    if not claims:
        reasons.append("claim attribution is missing")

    duplicate_context = payload.get("duplicate_context")
    if isinstance(duplicate_context, Mapping):
        candidates = [
            *[str(value) for value in duplicate_context.get("same_page", [])],
            *[str(value) for value in duplicate_context.get("cross_page", [])],
        ]
        checks["duplicate"]["denominator"] = int(
            duplicate_context.get("denominator", len(candidates))
        )
        checks["duplicate"]["detector_version"] = str(
            duplicate_context.get("detector_version", "jaccard-5gram.v1")
        )
        checks["duplicate"]["seed"] = duplicate_context.get("seed")
        if len(body) > 80:
            for candidate_index, candidate in enumerate(candidates, start=1):
                score = _five_gram_jaccard(body, candidate)
                if score >= 0.92:
                    checks["duplicate"]["failed_samples"].append(
                        {"sample": candidate_index, "jaccard": round(score, 6)}
                    )
        sentence_parts = [
            normalize_for_gate(value)
            for value in re.split(r"(?<=[.!?])\s+", body)
            if normalize_for_gate(value)
        ]
        if len(sentence_parts) > 1 and len(set(sentence_parts)) < len(sentence_parts):
            checks["duplicate"]["failed_samples"].append({"sample": "body-repeat", "jaccard": 1.0})
        if checks["duplicate"]["failed_samples"]:
            reasons.append("near duplicate detected")

    checks["continuous_source_block"] = _continuous_source_block_check(
        body,
        evidence_body,
        payload,
    )
    if checks["continuous_source_block"]["failed_samples"]:
        reasons.append("continuous source block exceeds 3 sentences or 240 characters")

    if reasons:
        return _body_gate_failure(payload, reasons, checks)
    return {
        "status": "published",
        "reader_eligible": True,
        "body": body,
        "evidence_body": evidence_body,
        "reasons": [],
        "checks": checks,
        "evidence": {"claim_backtrace": claim_backtrace},
        "audit_record": None,
    }


SEMANTIC_EVIDENCE_REQUIRED_FIELDS = (
    "schema_version",
    "run_id",
    "run_status",
    "execution_mode",
    "run_identity",
    "output_path",
    "sample_manifest",
    "provider",
    "detector",
    "budget",
    "threshold",
    "answerability_source",
    "answerability_subset",
    "concepts",
    "evidence_backtrace",
    "section_completeness",
    "failure_reasons",
    "contract_revision",
    "revision_ledger",
    "ac_bindings",
)
SEMANTIC_AC_BINDINGS = (
    "AC-01",
    "AC-03",
    "AC-05",
    "AC-07",
    "AC-09",
    "AC-10",
    "AC-11",
    "AC-12",
    "AC-13",
)


def validate_semantic_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the machine semantic exit without turning it into release."""
    reasons: list[str] = []
    if not isinstance(evidence, Mapping):
        return {
            "valid": False,
            "machine_exit_passed": False,
            "delivery_status": "not_released",
            "reader_eligible": False,
            "sample_count": None,
            "page_type_counts": {},
            "ac_bindings": {},
            "reasons": ["semantic evidence must be an object"],
        }
    missing = [field for field in SEMANTIC_EVIDENCE_REQUIRED_FIELDS if field not in evidence]
    if missing:
        reasons.append("missing semantic evidence fields: " + ", ".join(missing))
    if evidence.get("schema_version") != "task2b-semantic-evidence.v1":
        reasons.append("semantic evidence schema is invalid")
    run_identity = evidence.get("run_identity")
    if not isinstance(run_identity, Mapping) or not all(
        run_identity.get(field) for field in ("run_id", "sample_fingerprint", "kb_fingerprint", "input_fingerprint")
    ):
        reasons.append("semantic run identity is incomplete")
    elif any(
        not isinstance(run_identity.get(field), str)
        or re.fullmatch(r"[0-9a-f]{64}", run_identity[field], re.IGNORECASE) is None
        for field in ("sample_fingerprint", "kb_fingerprint", "input_fingerprint")
    ):
        reasons.append("semantic run identity fingerprints must be SHA-256 values")
    if not isinstance(evidence.get("output_path"), str) or not evidence.get("output_path"):
        reasons.append("semantic evidence output_path is missing")
    if evidence.get("run_status") != "completed":
        reasons.append("semantic run is not completed")
    if evidence.get("execution_mode") != "real_semantic":
        reasons.append("semantic exit requires real_semantic execution; offline fixtures are structural test data only")
    provider = evidence.get("provider")
    if not isinstance(provider, Mapping) or not all(
        isinstance(provider.get(field), str) and provider.get(field).strip()
        for field in ("provider", "model", "base_url")
    ):
        reasons.append("semantic provider identity is incomplete")
    elif (
        provider["provider"].strip().lower() in {"fixture", "offline", "test"}
        or "fixture" in provider["model"].strip().lower()
        or ".invalid" in provider["base_url"].strip().lower()
    ):
        reasons.append("real semantic evidence must identify a non-fixture provider")
    sample_manifest = evidence.get("sample_manifest")
    if not isinstance(sample_manifest, Mapping):
        reasons.append("sample manifest is missing")
        sample_manifest = {}
    sample_count = sample_manifest.get("sample_count")
    if not isinstance(sample_count, int) or not 12 <= sample_count <= 20:
        reasons.append("sample_count must be between 12 and 20")
    if not isinstance(sample_manifest.get("sampling_seed"), int):
        reasons.append("sampling_seed is missing")
    if re.fullmatch(r"[0-9a-f]{64}", str(sample_manifest.get("content_hash", "")), re.IGNORECASE) is None:
        reasons.append("sample manifest content_hash must be a SHA-256 value")
    required_categories = set(sample_manifest.get("required_categories", []))
    covered_categories = set(sample_manifest.get("covered_categories", []))
    excluded_categories = sample_manifest.get("excluded_categories", [])
    if not isinstance(excluded_categories, list):
        excluded_categories = []
    uncovered = sorted(required_categories - covered_categories)
    if uncovered and not all(
        isinstance(item, Mapping) and item.get("category") in uncovered and item.get("reason")
        for item in excluded_categories
    ):
        reasons.append("inventory category coverage is incomplete")

    concepts = evidence.get("concepts")
    if not isinstance(concepts, list):
        concepts = []
        reasons.append("concepts are missing")
    passing = [
        concept
        for concept in concepts
        if isinstance(concept, Mapping) and concept.get("status") == "machine-passing"
    ]
    if len(passing) < 6:
        reasons.append("machine-passing concept count is below 6")
    page_type_counts: dict[str, int] = {}
    for concept in passing:
        page_type = str(concept.get("page_type", ""))
        page_type_counts[page_type] = page_type_counts.get(page_type, 0) + 1
    for page_type in PAGE_TYPE_SECTION_MATRIX:
        if page_type_counts.get(page_type, 0) < 1:
            reasons.append(f"page type coverage is missing: {page_type}")

    subset = evidence.get("answerability_subset")
    if not isinstance(subset, Mapping):
        reasons.append("answerability subset is missing")
        subset = {}
    questions = subset.get("questions")
    if not isinstance(questions, list) or not questions:
        reasons.append("answerability questions are missing")
    else:
        for question in questions:
            if not isinstance(question, Mapping) or "answerable" not in question or (
                question.get("answerable") and not question.get("first_hit")
            ):
                reasons.append("answerability first_hit is incomplete")
                break
        if re.fullmatch(r"[0-9a-f]{64}", str(subset.get("content_hash", "")), re.IGNORECASE) is None:
            reasons.append("answerability subset content_hash must be a SHA-256 value")
    backtrace = evidence.get("evidence_backtrace")
    if not isinstance(backtrace, list) or any(
        not isinstance(row, Mapping) or not row.get("claim_id") or not row.get("fragment_locator")
        for row in backtrace
    ):
        reasons.append("evidence backtrace is incomplete")
    completeness = evidence.get("section_completeness")
    if not isinstance(completeness, list) or any(
        not isinstance(row, Mapping) or row.get("complete") is not True
        for row in completeness
    ):
        reasons.append("section completeness is incomplete")

    revision = evidence.get("contract_revision")
    ledger = evidence.get("revision_ledger")
    if revision not in {0, 1} or not isinstance(ledger, list) or not ledger:
        reasons.append("contract revision ledger is invalid")
    bindings = evidence.get("ac_bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != set(SEMANTIC_AC_BINDINGS):
        reasons.append("semantic AC bindings are incomplete")
    if evidence.get("delivery_status") != "not_released":
        reasons.append("Task 2-B semantic evidence must remain not_released")
    return {
        "valid": not reasons,
        "machine_exit_passed": not reasons,
        "delivery_status": "not_released",
        "reader_eligible": False,
        "sample_count": sample_count,
        "page_type_counts": page_type_counts,
        "ac_bindings": dict(bindings) if isinstance(bindings, Mapping) else {},
        "reasons": list(dict.fromkeys(reasons)),
    }


def validate_semantic_evidence_file(
    path: str | Path,
    *,
    expected_run_id: str | None = None,
    expected_output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Read and validate one run-bound semantic evidence file."""
    evidence_path = Path(path)
    if not evidence_path.is_file():
        return {
            "valid": False,
            "machine_exit_passed": False,
            "delivery_status": "not_released",
            "reader_eligible": False,
            "sample_count": None,
            "page_type_counts": {},
            "ac_bindings": {},
            "reasons": ["semantic evidence file is missing"],
        }
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return {
            "valid": False,
            "machine_exit_passed": False,
            "delivery_status": "not_released",
            "reader_eligible": False,
            "sample_count": None,
            "page_type_counts": {},
            "ac_bindings": {},
            "reasons": [f"semantic evidence file cannot be read: {error}"],
        }
    result = validate_semantic_evidence(evidence)
    reasons = list(result.get("reasons", []))
    if expected_run_id is not None and evidence.get("run_id") != expected_run_id:
        reasons.append("semantic evidence run_id does not match current run")
    if expected_output_path is not None and evidence.get("output_path") != str(Path(expected_output_path).resolve()):
        reasons.append("semantic evidence output_path does not match expected path")
    result["valid"] = not reasons
    result["machine_exit_passed"] = not reasons
    result["reasons"] = list(dict.fromkeys(reasons))
    return result


@dataclass(frozen=True)
class PublicationMetadata:
    title: str
    slug: str
    category_id: str
    summary: str
    why: str
    version: str
    related_topics: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = ()
    field_refs: dict[str, tuple[str, ...]] = field(default_factory=dict)
    field_status: dict[str, str] = field(default_factory=dict)
    needs_review: bool = False
    fallback_reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "category_id": self.category_id,
            "summary": self.summary,
            "why": self.why,
            "version": self.version,
            "related_topics": list(self.related_topics),
            "claim_refs": list(self.claim_refs),
            "field_refs": {key: list(value) for key, value in self.field_refs.items()},
            "field_status": dict(self.field_status),
            "needs_review": self.needs_review,
            "fallback_reasons": list(self.fallback_reasons),
        }


def deterministic_category_id(text: str, publication: PublicationContract) -> str:
    """Choose a conservative reader category when no provider suggestion exists.

    This is deliberately a small, auditable fallback rather than an attempt to
    replace semantic classification.  Unknown material remains in ``pending``;
    known product/engineering/customer/operations/principle terms are routed to
    the most specific declared leaf whose aliases match.
    """
    normalized = str(text or "").casefold()
    if not normalized or len(publication.categories) <= 1:
        return publication.pending_category.category_id
    # Source paths/titles are intentionally included by the caller.  These
    # rules are conservative and explainable: a category wins only when its
    # domain terms outscore the others; otherwise the item stays reviewable.
    leaf_terms = {
        "architecture": ("架构", "architecture", "部署方案", "deployment", "系统设计"),
        "implementation": ("api", "接口", "代码", "sdk", "token", "auth", "实现", "开发者"),
        "operations-troubleshooting": ("bug", "error", "故障", "排障", "日志", "监控", "问题分析"),
        "development-practice": ("sprint", "迭代", "研发实践", "retrospective", "开发流程"),
        "project": ("项目", "project", "方案", "里程碑"),
        "management": ("权限", "角色", "管理", "组织", "global system"),
        "people": ("年假", "annual leave", "人员", "team", "会议", "meeting"),
        "competitor": ("竞品", "competitor"),
        "event": ("活动", "event", "发布会"),
        "customer-case": ("客户案例", "customer case", "商户需求", "售后"),
        "customer-overview": ("客户", "商户", "用户", "merchant", "customer"),
        "market-feedback": ("市场", "反馈", "调研", "feedback"),
        "product-overview": ("产品概览", "产品介绍", "product overview"),
        "product-capability": ("功能", "模块", "终端", "设备", "应用", "支付", "产品能力"),
        "product-operations": ("安装", "使用", "运营", "配置", "收费"),
        "product-boundary": ("边界", "限制", "不支持", "兼容"),
        "business-principle": ("原则", "规范", "标准", "制度"),
        "content-standard": ("文档规范", "内容规范", "模板", "邮件模板"),
        "delivery-standard": ("交付", "上线", "发布规范", "验收"),
        "unclassified": ("其他",),
    }
    scores = {
        category.category_id: sum(
            1 for term in leaf_terms.get(category.category_id, ()) if term.casefold() in normalized
        )
        for category in publication.categories
        if category.category_id != publication.pending_category.category_id
    }
    best = max(scores.values(), default=0)
    if best <= 0:
        return publication.pending_category.category_id
    winners = sorted(category_id for category_id, score in scores.items() if score == best)
    return winners[0]


def _claim_key(claim: Mapping[str, Any]) -> str:
    return str(claim.get("claim_fingerprint") or claim.get("raw_id") or "").strip()


def _claim_text(claim: Mapping[str, Any]) -> str:
    return str(claim.get("text") or "")


def _fallback_title(claims: list[Mapping[str, Any]], explicit: str | None) -> str:
    candidates = [explicit, *(str(claim.get("title") or "").strip() for claim in claims)]
    for candidate in candidates:
        if candidate and len(candidate) >= 4:
            return candidate[:80].strip()
    for claim in claims:
        text = _claim_text(claim).strip()
        if text:
            return text[:80].strip()
    return "未命名知识主题"


def _slug_for(title: str, stable_topic_id: str | None = None) -> str:
    try:
        slug = readable_slug(title).encode("ascii", "ignore").decode("ascii")
    except (UnicodeEncodeError, ValidationError):
        slug = ""
    slug = re.sub(r"[^a-z0-9-]+", "-", slug.casefold()).strip("-")[:64]
    if len(slug) < 3:
        suffix = re.sub(r"[^a-z0-9]+", "", (stable_topic_id or "topic"))[-8:] or "topic"
        slug = f"topic-{suffix}"[:64]
    return slug


def _fallback_refs(claims: list[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(key for key in (_claim_key(claim) for claim in claims) if key)


def _field_has_supported_facts(value: str, refs: list[str], by_key: dict[str, Mapping[str, Any]]) -> bool:
    text = "\n".join(_claim_text(by_key[ref]) for ref in refs if ref in by_key)
    for token in (*_NUMERIC_RE.findall(value), *_IDENTIFIER_RE.findall(value)):
        if token not in text:
            return False
    return True


def _fallback_metadata(
    claims: list[Mapping[str, Any]],
    publication: PublicationContract,
    *,
    title: str | None,
    category_id: str | None,
    stable_topic_id: str | None,
    reasons: list[str],
) -> PublicationMetadata:
    claim_refs = _fallback_refs(claims)
    safe_title = _fallback_title(claims, title)
    safe_category = category_id if category_id in {item.category_id for item in publication.categories} else publication.pending_category.category_id
    safe_slug = _slug_for(safe_title, stable_topic_id)
    claim_texts = [text.strip() for text in (_claim_text(claim) for claim in claims) if text.strip()]
    summary = "来源未提供摘要；请阅读 Evidence。"
    version_match = re.search(r"\b(?:v|version|版本)\s*[0-9]+(?:\.[0-9]+){0,3}\b", " ".join(claim_texts), re.IGNORECASE)
    version = version_match.group(0) if version_match else "未提供版本信息"
    fields = {
        "title": claim_refs,
        "category_id": claim_refs,
        "summary": claim_refs,
        "why": claim_refs,
        "version": claim_refs,
    }
    return PublicationMetadata(
        title=safe_title,
        slug=safe_slug,
        category_id=safe_category,
        summary=summary,
        why="来源未说明",
        version=version,
        claim_refs=claim_refs,
        field_refs=fields,
        field_status={name: "fallback" for name in _FIELD_REF_NAMES},
        needs_review=True,
        fallback_reasons=tuple(dict.fromkeys(reasons or ["publication suggestion missing"])),
    )


def validate_publication_suggestion(
    raw: Any,
    *,
    claims: list[dict[str, Any]],
    publication: PublicationContract,
    topic_universe: set[str] | None = None,
    fallback_title: str | None = None,
    stable_topic_id: str | None = None,
    fallback_category_id: str | None = None,
) -> PublicationMetadata:
    """Validate one provider object and fall back field-by-field on defects."""
    if not isinstance(publication, PublicationContract):
        raise ValidationError("publication", "contract", "PublicationContract is required")
    claim_rows = [claim for claim in claims if isinstance(claim, Mapping)]
    by_key = {_claim_key(claim): claim for claim in claim_rows if _claim_key(claim)}
    if not isinstance(raw, Mapping):
        return _fallback_metadata(
            claim_rows,
            publication,
            title=fallback_title,
            category_id=fallback_category_id,
            stable_topic_id=stable_topic_id,
            reasons=["publication object is missing"],
        )
    reasons: list[str] = []
    unknown = sorted(set(raw) - set(_SCHEMA_FIELDS))
    if unknown:
        reasons.append(f"unknown fields: {', '.join(unknown)}")
    raw_refs = raw.get("claim_refs")
    claim_refs = [str(value).strip() for value in raw_refs] if isinstance(raw_refs, list) and all(isinstance(value, str) for value in raw_refs) else []
    if not claim_refs or len(claim_refs) > 80 or any(ref not in by_key for ref in claim_refs) or len(set(claim_refs)) != len(claim_refs):
        reasons.append("claim_refs are not a subset of the current claims")
        claim_refs = list(_fallback_refs(claim_rows))
    ref_set = set(claim_refs)
    field_refs_raw = raw.get("field_refs")
    field_refs: dict[str, tuple[str, ...]] = {}
    if not isinstance(field_refs_raw, Mapping) or set(field_refs_raw) != set(_FIELD_REF_NAMES):
        reasons.append("field_refs schema is invalid")
        field_refs = {name: tuple(claim_refs) for name in _FIELD_REF_NAMES}
    else:
        for name in _FIELD_REF_NAMES:
            value = field_refs_raw.get(name)
            refs = [str(item).strip() for item in value] if isinstance(value, list) and all(isinstance(item, str) for item in value) else []
            if not refs or len(refs) > 16 or any(ref not in ref_set for ref in refs) or len(set(refs)) != len(refs):
                reasons.append(f"field_refs.{name} is invalid")
                refs = list(claim_refs)
            field_refs[name] = tuple(refs)

    def text_field(name: str, maximum: int, fallback: str) -> tuple[str, str]:
        value = raw.get(name)
        refs = list(field_refs[name])
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
            reasons.append(f"{name} is invalid")
            return fallback, "fallback"
        value = value.strip()
        if not _field_has_supported_facts(value, refs, by_key):
            reasons.append(f"{name} contains unsupported facts")
            return fallback, "fallback"
        return value, "validated"

    title_raw = raw.get("title")
    if not isinstance(title_raw, str) or not 4 <= len(title_raw.strip()) <= 80:
        reasons.append("title is invalid")
        title = _fallback_title(claim_rows, fallback_title)
        title_status = "fallback"
    else:
        title, title_status = title_raw.strip(), "validated"
    slug_raw = raw.get("slug")
    if not isinstance(slug_raw, str) or not _SLUG_RE.fullmatch(slug_raw.strip()):
        reasons.append("slug is invalid")
        slug, slug_status = _slug_for(title, stable_topic_id), "fallback"
    else:
        slug, slug_status = slug_raw.strip(), "validated"
    category_raw = raw.get("category_id")
    allowed_categories = {item.category_id for item in publication.categories}
    if not isinstance(category_raw, str) or category_raw.strip() not in allowed_categories:
        reasons.append("category_id is not declared")
        category_id, category_status = (
            fallback_category_id if fallback_category_id in allowed_categories else publication.pending_category.category_id,
            "fallback",
        )
    else:
        category_id, category_status = category_raw.strip(), "validated"
    summary, summary_status = text_field("summary", 420, "来源未提供摘要；请阅读 Evidence。")
    why, why_status = text_field("why", 280, "来源未说明")
    version, version_status = text_field("version", 120, "未提供版本信息")
    related_raw = raw.get("related_topics")
    related = [str(item).strip() for item in related_raw] if isinstance(related_raw, list) and all(isinstance(item, str) for item in related_raw) else []
    if len(related) > 8:
        related = related[:8]
        reasons.append("related_topics exceeded maxItems")
    universe = topic_universe or set()
    valid_related = tuple(item for item in related if not universe or item in universe)
    if len(valid_related) != len(related):
        reasons.append("unknown related topic was discarded")
    statuses = {"title": title_status, "category_id": category_status, "summary": summary_status, "why": why_status, "version": version_status}
    return PublicationMetadata(
        title=title,
        slug=slug,
        category_id=category_id,
        summary=summary,
        why=why,
        version=version,
        related_topics=valid_related,
        claim_refs=tuple(claim_refs),
        field_refs=field_refs,
        field_status=statuses,
        needs_review=bool(reasons),
        fallback_reasons=tuple(dict.fromkeys(reasons)),
    )
