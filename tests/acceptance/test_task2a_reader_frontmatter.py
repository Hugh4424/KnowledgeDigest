"""Task 2-A acceptance tests for nested Reader concept frontmatter."""

from __future__ import annotations

from copy import deepcopy

import pytest

from knowledge_digest.errors import ValidationError
from knowledge_digest.reader_frontmatter import (
    managed_content_hash,
    parse_concept_document,
    serialize_concept_document,
)


def _document() -> str:
    return """---
type: KnowledgeDigest Product Overview
title: Reader Bundle
description: A reader-facing package.
sources:
  - id: src-reader
    resource: https://source.example/reader
    locator:
      kind: heading
      value: Overview
generated:
  at: 2026-08-09T00:00:00Z
  producer: knowledge-digest/2a
verified:
  - event: source_hash_match
    actor: process:knowledge-digest-source_hash_match-v1
status: stable
digest_topic_key: v2/product_overview/reader-bundle
digest_topic_id: topic-reader
digest_page_type: product_overview
digest_page_status: published
digest_machine_pass: true
x-reader-extension:
  owner: docs
  nested:
    - keep: this
---
# Reader Bundle

The body remains Markdown.
"""


def test_nested_unknown_fields_round_trip_without_flattening() -> None:
    frontmatter, body = parse_concept_document(_document())

    assert frontmatter["sources"][0]["locator"]["kind"] == "heading"
    assert frontmatter["verified"][0]["event"] == "source_hash_match"
    assert frontmatter["x-reader-extension"]["nested"][0]["keep"] == "this"
    assert body == "# Reader Bundle\n\nThe body remains Markdown.\n"

    rendered = serialize_concept_document(frontmatter, body)
    reparsed_frontmatter, reparsed_body = parse_concept_document(rendered)

    assert reparsed_frontmatter == frontmatter
    assert reparsed_body == body


def test_managed_hash_excludes_volatile_fields_but_tracks_business_fields() -> None:
    frontmatter, body = parse_concept_document(_document())
    baseline = managed_content_hash(frontmatter, body)

    volatile = deepcopy(frontmatter)
    volatile["generated"]["at"] = "2026-08-10T00:00:00Z"
    volatile["verified"].append({"event": "locator_resolved", "actor": "process:test-v1"})
    volatile["digest_page_status"] = "degraded"
    volatile["digest_machine_pass"] = False
    volatile["digest_content_hash"] = "0" * 64

    assert managed_content_hash(volatile, body) == baseline

    changed = deepcopy(frontmatter)
    changed["description"] = "A changed reader-facing package."
    assert managed_content_hash(changed, body) != baseline


@pytest.mark.parametrize(
    "document",
    [
        "# missing frontmatter\n",
        "---\ntype: [\n---\nbody\n",
        "---\ntype: \"\"\n---\nbody\n",
    ],
)
def test_parse_rejects_missing_invalid_or_empty_type_frontmatter(document: str) -> None:
    with pytest.raises(ValidationError):
        parse_concept_document(document)


def test_parse_and_serialize_reject_non_text_inputs() -> None:
    with pytest.raises(ValidationError):
        parse_concept_document(None)  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        serialize_concept_document({"type": "KnowledgeDigest Product Overview"}, None)  # type: ignore[arg-type]


def test_serialize_normalizes_body_without_trailing_newline() -> None:
    rendered = serialize_concept_document(
        {"type": "KnowledgeDigest Product Overview"},
        "# Reader Bundle",
    )

    _, body = parse_concept_document(rendered)
    assert body == "# Reader Bundle\n"
