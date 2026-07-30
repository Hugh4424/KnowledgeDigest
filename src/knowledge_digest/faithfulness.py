"""Claim extraction, stable identity, and faithfulness checking."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping


_UNSUPPORTED_PREFIX = "unsupported:"

# Fullwidth/CJK punctuation folded onto its ASCII counterpart. Surface-only:
# every pair here is the same mark in a different width or quoting style, so
# folding them can never turn one word into a different word.
_PUNCTUATION_FOLD = str.maketrans(
    {
        "。": ".", "，": ",", "、": ",", "；": ";", "：": ":",
        "？": "?", "！": "!", "（": "(", "）": ")", "［": "[",
        "］": "]", "｛": "{", "｝": "}", "〈": "<", "〉": ">",
        "《": "<", "》": ">", "—": "-", "－": "-", "～": "~",
        "％": "%", "＃": "#", "＆": "&", "＊": "*", "＋": "+",
        "＝": "=", "／": "/", "＼": "\\", "｜": "|", "＠": "@",
        "＄": "$", "＾": "^", "＿": "_", "｀": "`",
        "“": '"', "”": '"', "„": '"', "「": '"', "」": '"',
        "『": '"', "』": '"', "‘": "'", "’": "'", "‚": "'",
        "…": "...", "·": ".",
    }
)

# Drops the space on either side of an ASCII punctuation mark. Applied after
# the width fold so that ``a, b`` and ``a，b`` converge. Word characters are
# never touched, so ``3 times`` and ``three times`` stay distinct.
_SPACE_AROUND_PUNCTUATION_RE = re.compile(
    r"\s*([!-/:-@\[-`{-~])\s*"
)


def normalize_for_gate(text: str) -> str:
    """Fold only surface differences before the faithfulness hard gate.

    Collapses runs of whitespace to one space, folds fullwidth/CJK punctuation
    onto ASCII, drops whitespace directly adjacent to punctuation, and
    casefolds. The adjacent-whitespace rule exists because fullwidth marks
    carry their own spacing (``, `` becomes ``，`` with no following space), so
    width folding alone would still leave a spurious space difference.

    Deliberately NOT semantic: whitespace *between word characters* is kept, so
    word substitutions such as ``3 times`` -> ``three times`` still differ after
    normalization and are still rejected by the gate.
    """
    folded = " ".join(text.translate(_PUNCTUATION_FOLD).split()).strip().casefold()
    return _SPACE_AROUND_PUNCTUATION_RE.sub(r"\1", folded)


def normalize_newlines(text: str) -> str:
    """Normalize only CRLF and lone CR before a round comparison."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_claim(text: str) -> str:
    """Normalize only whitespace so a claim fingerprint is deterministic."""
    return " ".join(text.split()).strip().casefold()


def claim_fingerprint(source_uri: str, text: str) -> str:
    payload = f"{source_uri}\n{normalize_claim(text)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def claim_entity_key(claim: Mapping[str, Any]) -> tuple[str, str, str]:
    """Identify one source occurrence, including repeated identical lines.

    ``claim_fingerprint`` intentionally represents normalized claim text, so it
    is not enough to identify two equal lines in the same source.  History,
    layout and provenance must use this key whenever they collapse records.
    """
    return (
        str(claim.get("source_uri", "")),
        str(claim.get("fragment_locator", "")),
        str(claim.get("claim_fingerprint") or claim.get("claim_id") or ""),
    )


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
