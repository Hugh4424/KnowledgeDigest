"""Stable business identities for sources and digest topics.

Run-local identifiers (``raw-N``, ``cluster-N`` and ``draft-N``) remain useful
for audit files, but must never select a formal knowledge page.  The identities
here are deliberately derived only from durable source facts.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit

from .errors import ValidationError


def normalize_source_uri(source_uri: str) -> str:
    """Normalize harmless URI surface differences without changing its meaning."""
    value = source_uri.strip()
    if not value:
        raise ValidationError("identity", "source_uri", "source URI must not be empty")
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        value = urlunsplit(
            (
                parsed.scheme.casefold(),
                parsed.netloc.casefold(),
                parsed.path or "/",
                parsed.query,
                "",
            )
        )
    return value


def source_id(source_uri: str) -> str:
    """Return a stable opaque identifier for one declared source URI."""
    digest = hashlib.sha256(normalize_source_uri(source_uri).encode("utf-8")).hexdigest()
    return f"source-{digest[:20]}"


def topic_id(source_ids: Iterable[str]) -> str:
    """Choose one deterministic topic anchor from its member sources.

    A topic may gain sources incrementally.  Anchoring it on the lexicographically
    first source ID keeps the result stable when input enumeration changes, and
    a batch runner always enumerates the fixed manifest in that same order.
    """
    values = sorted({value for value in source_ids if value})
    if not values:
        raise ValidationError("identity", "topic", "topic requires at least one source ID")
    anchor = values[0]
    if not anchor.startswith("source-"):
        raise ValidationError("identity", "topic", "topic source ID is malformed")
    return f"topic-{anchor.removeprefix('source-')}"


def topic_part_path(page_root: str, stable_topic_id: str, part_number: int) -> str:
    """Return the canonical relative Markdown path for a topic part."""
    if part_number < 1:
        raise ValidationError("identity", "part_number", "topic part number must be positive")
    suffix = "" if part_number == 1 else f".part-{part_number:03d}"
    return f"{page_root}/digest/{stable_topic_id}{suffix}.md"
