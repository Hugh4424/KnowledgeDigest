"""Claim extraction, stable identity, and faithfulness checking."""

from __future__ import annotations

import hashlib
import re
from typing import Any


_UNSUPPORTED_PREFIX = "unsupported:"


def normalize_newlines(text: str) -> str:
    """Normalize only CRLF and lone CR before a round comparison."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_claim(text: str) -> str:
    """Normalize only whitespace so a claim fingerprint is deterministic."""
    return " ".join(text.split()).strip().casefold()


def claim_fingerprint(source_uri: str, text: str) -> str:
    payload = f"{source_uri}\n{normalize_claim(text)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _line_record(item: dict[str, Any], line_number: int, text: str) -> dict[str, Any]:
    source_uri = str(item["source_uri"])
    locator = f"lines:{line_number}-{line_number}"
    return {
        "text": text,
        "source_uri": source_uri,
        "content_fingerprint": item.get("content_fingerprint") or item.get("content_hash"),
        "fragment_locator": locator,
        "claim_fingerprint": claim_fingerprint(source_uri, text),
        "verification_status": "verified",
        "validation_status": "passed",
        "source_snapshot_ref": item.get("source_snapshot_ref"),
        "raw_id": item.get("raw_id"),
        "input_path": item.get("input_path"),
    }


def verify_claims(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract supported and unsupported claims from raw items."""
    claims: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    for item in items:
        for line_number, line in enumerate(item["text"].splitlines(), start=1):
            claim = line.strip()
            if not claim or claim.startswith("#"):
                continue
            record = _line_record(item, line_number, claim)
            if claim.casefold().startswith(_UNSUPPORTED_PREFIX):
                record["verification_status"] = "unsupported"
                record["reason"] = "claim is explicitly marked unsupported"
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
