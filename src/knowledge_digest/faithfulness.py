"""Claim extraction and faithfulness checking for draft bodies."""

from __future__ import annotations

from typing import Any


def verify_claims(items: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Extract supported and unsupported claims from raw items."""
    claims: list[dict[str, str]] = []
    unsupported: list[dict[str, str]] = []
    for item in items:
        for line in item["text"].splitlines():
            claim = line.strip()
            if not claim or claim.startswith("#"):
                continue
            record = {"text": claim, "source_uri": item["source_uri"]}
            if claim.lower().startswith("unsupported:"):
                unsupported.append(record)
            else:
                claims.append(record)
    return claims, unsupported


def faithfulness_check(claims: list[dict[str, Any]], final_body: str) -> tuple[str, str]:
    """Verify that every claim is represented in the draft body.

    Returns a tuple of (body, status). If the original body is missing any claim,
    fall back to a bullet list. If the fallback is also missing a claim, mark failed.
    """
    if all(claim["text"] in final_body for claim in claims):
        return final_body, "faithful"
    fallback_body = "\n".join(f"- {claim['text']}" for claim in claims)
    if all(claim["text"] in fallback_body for claim in claims):
        return fallback_body, "fallback_claim_concat"
    return fallback_body, "failed"
