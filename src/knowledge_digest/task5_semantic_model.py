"""Typed semantic response checks used by the Task5 runtime.

The production compiler already performs the full page/evidence validation.
This module provides a narrow, dependency-free boundary check so a malformed
provider response can never be mistaken for a raw-source fallback.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from .compiler import PAGE_TYPES


class SemanticContractError(ValueError):
    """Provider output is not a Task5 typed semantic response."""


def parse_typed_response(payload: str | bytes) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SemanticContractError("provider response is not valid JSON") from error
    if not isinstance(value, dict):
        raise SemanticContractError("provider response must be a JSON object")
    required = {
        "schema_version", "title", "page_type", "page_type_claim_ids",
        "axis", "axis_claim_ids", "summary", "sections",
    }
    if set(value) != required:
        raise SemanticContractError("provider response has unknown or missing fields")
    if value.get("schema_version") != "task5-semantic-output.v2":
        raise SemanticContractError("provider response has an invalid schema_version")
    if value.get("page_type") not in PAGE_TYPES:
        raise SemanticContractError("provider response has an invalid page_type")
    if not isinstance(value.get("title"), str) or not str(value["title"]).strip():
        raise SemanticContractError("provider response title is empty")
    def refs(field: str, raw: Any, *, required_nonempty: bool = True) -> list[str]:
        if not isinstance(raw, list) or any(not isinstance(item, str) or not item.strip() for item in raw):
            raise SemanticContractError(f"provider response {field} is malformed")
        result = list(dict.fromkeys(str(item).strip() for item in raw))
        if required_nonempty and not result:
            raise SemanticContractError(f"provider response {field} is empty")
        return result

    refs("page_type_claim_ids", value.get("page_type_claim_ids"))
    axis = value.get("axis")
    axis_claim_ids = value.get("axis_claim_ids")
    axis_names = {"product", "module", "object", "scene", "boundary"}
    if not isinstance(axis, Mapping) or set(axis) != axis_names:
        raise SemanticContractError("provider response axis is incomplete")
    if any(not isinstance(axis[name], str) or not axis[name].strip() for name in axis):
        raise SemanticContractError("provider response axis contains an empty value")
    if not isinstance(axis_claim_ids, Mapping) or set(axis_claim_ids) != axis_names:
        raise SemanticContractError("provider response axis_claim_ids are incomplete")
    for name in sorted(axis_names):
        refs(f"axis_claim_ids.{name}", axis_claim_ids[name])
    summary = value.get("summary")
    if not isinstance(summary, Mapping) or set(summary) != {"body", "claim_ids", "evidence_ids"}:
        raise SemanticContractError("provider response summary is malformed")
    sections = value.get("sections")
    expected = set(PAGE_TYPES[str(value["page_type"])])
    if not isinstance(sections, Mapping) or set(sections) != expected:
        raise SemanticContractError("provider response sections do not match page_type")
    for label, section in (("summary", summary), *sections.items()):
        if not isinstance(section, Mapping) or set(section) != {"body", "claim_ids", "evidence_ids"}:
            raise SemanticContractError(f"provider response section is malformed: {label}")
        if not isinstance(section["body"], str) or not section["body"].strip():
            raise SemanticContractError(f"provider response section is empty: {label}")
        if not isinstance(section["evidence_ids"], list) or any(not isinstance(item, str) for item in section["evidence_ids"]):
            raise SemanticContractError(f"provider response evidence_ids are malformed: {label}")
        claim_ids = refs(f"{label}.claim_ids", section["claim_ids"], required_nonempty=section["body"].strip() != "原始资料未明确")
        evidence_ids = refs(f"{label}.evidence_ids", section["evidence_ids"], required_nonempty=section["body"].strip() != "原始资料未明确")
        if set(claim_ids) != set(evidence_ids):
            raise SemanticContractError(f"provider response claim/evidence refs diverge: {label}")
    return value


def validate_evidence_closure(value: Mapping[str, Any], evidence_ids: Sequence[str]) -> None:
    allowed = set(str(item) for item in evidence_ids)
    provider_claims = set(str(item) for item in value["page_type_claim_ids"])
    provider_claims.update(
        str(ref)
        for refs in value["axis_claim_ids"].values()
        for ref in refs
    )
    for section in (value["summary"], *value["sections"].values()):
        refs = section["evidence_ids"]
        claim_refs = section["claim_ids"]
        provider_claims.update(str(ref) for ref in claim_refs)
        if any(str(ref) not in allowed for ref in (*refs, *claim_refs)):
            raise SemanticContractError("provider response cites evidence outside the supplied closure")
    if not provider_claims.issubset(allowed):
        raise SemanticContractError("provider response cites a Claim outside the supplied closure")


__all__ = ["SemanticContractError", "parse_typed_response", "validate_evidence_closure"]
