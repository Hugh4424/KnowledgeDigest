"""Stable business identities for sources and digest topics.

Run-local identifiers (``raw-N``, ``cluster-N`` and ``draft-N``) remain useful
for audit files, but must never select a formal knowledge page.  The identities
here are deliberately derived only from durable source facts.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path
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


def readable_slug(title: str) -> str:
    """Return a stable human-readable filename stem without path semantics."""
    normalized = unicodedata.normalize("NFKC", title).casefold().strip()
    value = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-_")
    if not value:
        raise ValidationError("identity", "title", "topic title cannot produce an empty filename")
    return value[:80].rstrip("-_")


def publication_topic_part_path(
    topic_dir: str,
    title: str,
    stable_topic_id: str,
    part_number: int,
    *,
    disambiguate: bool = False,
) -> str:
    """Return a readable topic path, with an identity suffix only on collision."""
    if part_number < 1:
        raise ValidationError("identity", "part_number", "topic part number must be positive")
    if not stable_topic_id.startswith("topic-"):
        raise ValidationError("identity", "topic", "topic ID is malformed")
    stem = readable_slug(title)
    if disambiguate:
        stem = f"{stem}-{stable_topic_id.removeprefix('topic-')[:8]}"
    suffix = "" if part_number == 1 else f".part-{part_number:03d}"
    return (Path(topic_dir) / f"{stem}{suffix}.md").as_posix()


def published_part_path(first_path: str, part_number: int) -> str:
    """Keep a locked first path while deriving deterministic readable part paths."""
    if part_number < 1:
        raise ValidationError("identity", "part_number", "topic part number must be positive")
    if part_number == 1:
        return first_path
    path = Path(first_path)
    if path.suffix.lower() != ".md":
        raise ValidationError("identity", first_path, "published topic path must be Markdown")
    return path.with_name(f"{path.stem}.part-{part_number:03d}.md").as_posix()
