"""The single YAML/frontmatter boundary for Task 2-A Reader concepts."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
import re
from typing import Any

import yaml

from .errors import ValidationError


_MANAGED_FIELDS = (
    "type",
    "title",
    "description",
    "tags",
    "sources",
    "status",
    "stale_after",
    "digest_topic_key",
    "digest_topic_id",
    "digest_page_type",
)
_FRONTMATTER_RE = re.compile(r"\A---\n(?P<frontmatter>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)


def _normalized_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _normalized_body(body: str) -> str:
    normalized = _normalized_text(body)
    return normalized if normalized.endswith("\n") else normalized + "\n"


def _validated_mapping(frontmatter: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(frontmatter, Mapping):
        raise ValidationError("reader-frontmatter", "frontmatter", "must be a YAML mapping")
    values = dict(frontmatter)
    if not isinstance(values.get("type"), str) or not values["type"].strip():
        raise ValidationError("reader-frontmatter", "type", "must be a non-empty string")
    return values


def _safe_dump(values: Mapping[str, Any]) -> str:
    try:
        return yaml.safe_dump(
            dict(values),
            allow_unicode=True,
            default_flow_style=False,
            indent=2,
            sort_keys=True,
            width=100,
            line_break="\n",
        )
    except yaml.YAMLError as exc:
        raise ValidationError("reader-frontmatter", "frontmatter", f"cannot serialize safely: {exc}") from exc

def parse_concept_document(text: str) -> tuple[dict[str, Any], str]:
    """Parse a concept document into frontmatter and Markdown body."""

    if not isinstance(text, str):
        raise ValidationError("reader-frontmatter", "document", "must be text")
    match = _FRONTMATTER_RE.fullmatch(_normalized_text(text))
    if match is None:
        raise ValidationError("reader-frontmatter", "document", "must start with a closed YAML frontmatter block")
    try:
        parsed = yaml.safe_load(match.group("frontmatter"))
    except yaml.YAMLError as exc:
        raise ValidationError("reader-frontmatter", "document", f"invalid safe YAML: {exc}") from exc
    values = _validated_mapping(parsed if isinstance(parsed, Mapping) else {})
    return values, match.group("body")


def serialize_concept_document(frontmatter: Mapping[str, Any], body: str) -> str:
    """Serialize concept frontmatter and Markdown body."""

    if not isinstance(body, str):
        raise ValidationError("reader-frontmatter", "body", "must be text")
    values = _validated_mapping(frontmatter)
    return f"---\n{_safe_dump(values)}---\n{_normalized_body(body)}"


def managed_content_hash(frontmatter: Mapping[str, Any], body: str) -> str:
    """Calculate the managed content hash for a concept document."""

    if not isinstance(body, str):
        raise ValidationError("reader-frontmatter", "body", "must be text")
    values = _validated_mapping(frontmatter)
    managed = {key: values[key] for key in _MANAGED_FIELDS if key in values}
    payload = f"{_safe_dump(managed)}---\n{_normalized_body(body)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
