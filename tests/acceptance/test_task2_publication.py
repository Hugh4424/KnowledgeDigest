"""Phase 1 RED/GREEN contracts for the publication taxonomy and indexes."""

from __future__ import annotations

import pytest
from knowledge_digest import llm

from knowledge_digest import kb_structure
from knowledge_digest.config import DigestSettings
from knowledge_digest.draft import draft
from knowledge_digest.errors import ValidationError


def test_default_taxonomy_has_parent_leaf_and_pending_contract() -> None:
    structure = kb_structure.default_publication_structure()
    contract, errors = kb_structure._publication_contract(structure)
    assert not errors
    assert contract is not None
    assert contract.taxonomy_version == "1.0.0"
    assert len(contract.categories) >= 20
    assert contract.pending_category.parent_id == "other"
    assert all(category.parent_id for category in contract.categories)


def test_taxonomy_requires_version_for_official_publication(tmp_path) -> None:
    path = tmp_path / "kb.structure.md"
    path.write_text(
        "---\n"
        "roots: [pages, _archive, _queues]\n"
        "why_field: why\n"
        "version_field: version\n"
        "publication_home: Home.md\n"
        "publication_index_root: indexes\n"
        "publication_categories:\n"
        "  - id: pending\n"
        "    title: 待归类\n"
        "    topic_dir: pages/待归类\n"
        "---\n",
        encoding="utf-8",
    )
    inspected = kb_structure.inspect_structure(path, require_taxonomy=True)
    assert not inspected.allow_official_write
    assert any("taxonomy_version" in error for error in inspected.publication_errors)


def test_topic_index_rejects_duplicate_source_membership() -> None:
    with pytest.raises(Exception, match="source_ids|duplicate|topic"):
        kb_structure.validate_topic_index(
            {
                "schema_version": "1.0.0",
                "topics": [
                    {"topic_id": "topic-a", "source_ids": ["source-1"], "category_id": "pending", "published_path": "pages/待归类/a.md", "product_slug": None},
                    {"topic_id": "topic-b", "source_ids": ["source-1"], "category_id": "pending", "published_path": "pages/待归类/b.md", "product_slug": None},
                ],
            }
        )


def test_source_index_has_fixed_markdown_schema() -> None:
    value = {
        "schema_version": "1.0.0",
        "entries": [
            {
                "source_uri": "https://example.test/a|b",
                "content_fingerprint": "a" * 64,
                "status": "published",
                "target_paths": ["pages/products/a.md"],
            }
        ],
    }
    encoded = kb_structure.serialize_source_index(value)
    assert "| source_uri | content_fingerprint | status | target_paths |" in encoded
    assert kb_structure.parse_source_index_markdown(encoded) == value


def test_source_index_rejects_legacy_human_link_list() -> None:
    with pytest.raises(Exception, match="managed header"):
        kb_structure.parse_source_index_markdown(
            "# Source Index\n\n- `file:///tmp/source.md`\n  - [Topic](../pages/topic.md)\n"
        )


def _publication_contract():
    structure = kb_structure.default_publication_structure()
    contract, errors = kb_structure._publication_contract(structure, require_taxonomy=True)
    assert not errors and contract is not None
    return contract


def _claims():
    return [
        {"claim_fingerprint": "a" * 64, "text": "API version v2 supports 99% of cases.", "title": "API capability"},
        {"claim_fingerprint": "b" * 64, "text": "The API is used by engineering teams."},
    ]


def _publication_module():
    import importlib

    return importlib.import_module("knowledge_digest.publication")


def test_pub_object_missing_falls_back_field_by_field_and_marks_review() -> None:
    metadata = _publication_module().validate_publication_suggestion(
        None,
        claims=_claims(),
        publication=_publication_contract(),
        stable_topic_id="topic-api",
    )
    assert metadata.needs_review
    assert metadata.category_id == "pending"
    assert set(metadata.claim_refs) == {"a" * 64, "b" * 64}
    assert all(metadata.field_status[field] == "fallback" for field in ("title", "category_id", "summary", "why", "version"))
    assert metadata.summary == "来源未提供摘要；请阅读 Evidence。"
    assert metadata.why == "来源未说明"
    assert "product_slug" not in metadata.as_dict()


def test_pub_object_invalid_category_and_unbound_field_refs_do_not_pass() -> None:
    metadata = _publication_module().validate_publication_suggestion(
        {
            "title": "API capability",
            "slug": "api-capability",
            "category_id": "not-declared",
            "summary": "99% coverage",
            "why": "Useful for engineering teams.",
            "version": "v2",
            "claim_refs": ["a" * 64],
            "field_refs": {"summary": ["a" * 64], "why": ["missing"]},
        },
        claims=_claims(),
        publication=_publication_contract(),
        stable_topic_id="topic-api",
    )
    assert metadata.needs_review
    assert metadata.category_id == "pending"
    assert any("why" in reason or "category_id" in reason for reason in metadata.fallback_reasons)


def test_provider_contract_identity_is_qwen_only() -> None:
    llm.validate_publication_provider_identity(
        model="qwen3.6",
        base_url="https://dashscope.in.whatspos.cn/v1",
    )
    with pytest.raises(ValidationError, match="qwen3.6"):
        llm.validate_publication_provider_identity(model="deepseek-v4-flash", base_url="https://api.deepseek.com/v1")


def test_provider_contract_prompt_is_explicitly_semantic_and_fail_closed() -> None:
    prompt = llm.build_prompt(
        {
            "publication_enabled": True,
            "publication_contract": {"taxonomy_version": "1.0.0", "categories": [{"id": "engineering", "title": "研发"}]},
            "claims": [{"claim_fingerprint": "a" * 64, "text": "API v2", "line_start": 1}],
            "source_text": "API v2",
            "target_page": "pages/engineering/api.md",
            "summary_enabled": True,
        },
        target_page="pages/engineering/api.md",
    )
    assert "semantic publication suggestions" in prompt
    assert "Do not create facts" in prompt
    assert '"publication"' in prompt
    assert "MUST include the top-level publication object" in prompt
    assert "FINAL REMINDER" in prompt


def test_publication_only_prompt_is_compact_and_does_not_require_body_echo() -> None:
    prompt = llm.build_prompt(
        {
            "publication_enabled": True,
            "publication_only": True,
            "claims": [{"claim_fingerprint": "a" * 64, "text": "API v2", "source_uri": "u", "fragment_locator": "lines:1-1"}],
            "source_text": "API v2",
            "target_page": "pages/engineering/api.md",
            "summary_enabled": True,
            "allowed_taxonomy": [{"id": "engineering", "title": "研发", "parent_id": None, "aliases": []}],
        },
        target_page="pages/engineering/api.md",
    )
    assert "publication-only" in prompt
    assert "Do not return final_body" in prompt
    assert '"publication"' in prompt
    assert '"summary_id":"summary-1"' in prompt
    assert '"supports":[{"claim_fingerprint":"..."}]' in prompt


def test_draft_passes_allowed_taxonomy_as_a_plain_category_list(tmp_path) -> None:
    seen: list[dict[str, object]] = []

    def generator(context: dict[str, object]) -> str:
        seen.append(context)
        return "Claim one.\nClaim two."

    result = draft(
        [{"cluster_id": "cluster-1", "action": "new", "target_paths": [], "source_count": 1, "target_page_count": 0}],
        [{"cluster_id": "cluster-1", "tier": "auto", "cluster_tier": "auto", "members": ["raw-1"], "decision_reason": "test"}],
        [{"raw_id": "raw-1", "text": "Claim one.\nClaim two.\n", "source_uri": "https://source.example/one", "validation_status": "passed"}],
        tmp_path,
        DigestSettings(llm_enabled=True),
        generator=generator,
        publication=_publication_contract(),
    )

    assert result
    assert isinstance(seen[0]["allowed_taxonomy"], list)
    assert all(isinstance(category, dict) for category in seen[0]["allowed_taxonomy"])


def test_draft_keeps_publication_suggestion_when_claim_batches_are_merged(tmp_path) -> None:
    claims = [
        {"raw_id": "raw-1", "claim_fingerprint": "a" * 64, "text": "API v2", "source_uri": "u", "fragment_locator": "lines:1-1"},
        {"raw_id": "raw-1", "claim_fingerprint": "b" * 64, "text": "API is stable.", "source_uri": "u", "fragment_locator": "lines:2-2"},
    ]

    def generator(context: dict[str, object]) -> dict[str, object]:
        batch_claims = list(context["claims"])
        refs = [str(claim["claim_fingerprint"]) for claim in batch_claims]
        return {
            "final_body": "\n".join(str(claim["text"]) for claim in batch_claims),
            "claims": batch_claims,
            "publication": {
                "title": "API capability",
                "slug": "api-capability",
                "category_id": "implementation",
                "summary": "API v2 is stable.",
                "why": "Useful for engineering.",
                "version": "v2",
                "related_topics": [],
                "claim_refs": refs,
                "field_refs": {field: refs for field in ("title", "category_id", "summary", "why", "version")},
            },
        }

    result = draft(
        [{"cluster_id": "cluster-1", "action": "new", "target_paths": [], "source_count": 1, "target_page_count": 0}],
        [{"cluster_id": "cluster-1", "tier": "auto", "cluster_tier": "auto", "members": ["raw-1"], "decision_reason": "test"}],
        [{"raw_id": "raw-1", "text": "API v2\nAPI is stable.\n", "source_uri": "u", "validation_status": "passed"}],
        tmp_path,
        DigestSettings(llm_enabled=True, llm_batch_max_claims=1),
        generator=generator,
        publication=_publication_contract(),
    )

    assert result[0]["publication"] is not None
    assert result[0]["publication"]["title"] == "API capability"


def test_layout_removes_generated_summary_shell_from_evidence() -> None:
    page_layout = __import__("knowledge_digest.page_layout", fromlist=["_evidence_lines"])
    assert page_layout._evidence_lines("## Summary\n- concise\n\n## Evidence\nAPI v2\n") == ["API v2"]


def test_all_live_topics_use_publication_only_prompt_after_provider_resolution(monkeypatch, tmp_path) -> None:
    draft_module = __import__("knowledge_digest.draft", fromlist=["resolve_generator"])
    seen: list[bool] = []

    def generator(context: dict[str, object]) -> dict[str, object]:
        seen.append(bool(context.get("publication_only")))
        claims = list(context["claims"])
        return {"final_body": "\n".join(str(claim["text"]) for claim in claims), "claims": claims}

    monkeypatch.setattr(draft_module, "resolve_generator", lambda _settings: generator)
    decisions = [
        {"cluster_id": "cluster-1", "action": "new", "target_paths": [], "source_count": 1, "target_page_count": 0},
        {"cluster_id": "cluster-2", "action": "new", "target_paths": [], "source_count": 1, "target_page_count": 0},
    ]
    clusters = [
        {"cluster_id": "cluster-1", "tier": "auto", "cluster_tier": "auto", "members": ["raw-1"], "decision_reason": "test"},
        {"cluster_id": "cluster-2", "tier": "auto", "cluster_tier": "auto", "members": ["raw-2"], "decision_reason": "test"},
    ]
    raw_items = [
        {"raw_id": "raw-1", "text": "API v2", "source_uri": "u1", "validation_status": "passed"},
        {"raw_id": "raw-2", "text": "API v3", "source_uri": "u2", "validation_status": "passed"},
    ]
    draft(decisions, clusters, raw_items, tmp_path, DigestSettings(llm_enabled=True), publication=_publication_contract())
    assert seen == [True, True]


def test_topic_identity_uses_ascii_slug_and_locks_first_path() -> None:
    from knowledge_digest.identity import resolve_topic_identity

    topic = "topic-1234567890abcdef"
    index = {
        "schema_version": "1.0.0",
        "topics": [
            {
                "topic_id": topic,
                "source_ids": ["source-a"],
                "category_id": "product-capability",
                "published_path": "pages/product-capability/payment-api.md",
                "product_slug": None,
            }
        ],
    }

    locked = resolve_topic_identity(
        index,
        stable_topic_id=topic,
        source_ids=["source-a"],
        category_id="product-capability",
        title="支付 API v2",
        topic_dir="pages/product-capability",
    )
    assert locked["published_path"] == "pages/product-capability/payment-api.md"
    assert locked["category_id"] == "product-capability"
    assert locked["needs_review"] is False

    moved = resolve_topic_identity(
        index,
        stable_topic_id=topic,
        source_ids=["source-a"],
        category_id="engineering",
        title="Changed title",
        topic_dir="pages/engineering",
    )
    assert moved["published_path"] == "pages/product-capability/payment-api.md"
    assert moved["category_id"] == "product-capability"
    assert moved["needs_review"] is True


def test_topic_identity_disambiguates_same_ascii_slug_without_input_order() -> None:
    from knowledge_digest.identity import resolve_topic_identity

    index = {"schema_version": "1.0.0", "topics": []}
    first = resolve_topic_identity(
        index,
        stable_topic_id="topic-aaaaaaaaaaaaaaaa",
        source_ids=["source-a"],
        category_id="product-capability",
        title="Payment API",
        topic_dir="pages/product-capability",
    )
    index["topics"].append(first["topic_index_entry"])
    second = resolve_topic_identity(
        index,
        stable_topic_id="topic-bbbbbbbbbbbbbbbb",
        source_ids=["source-b"],
        category_id="product-capability",
        title="Payment API",
        topic_dir="pages/product-capability",
    )
    assert first["published_path"] == "pages/product-capability/payment-api.md"
    assert second["published_path"] == "pages/product-capability/payment-api-bbbbbbbb.md"
    assert second["needs_review"] is True


def test_layout_consumes_publication_identity_and_keeps_claims_once(tmp_path) -> None:
    from knowledge_digest.identity import topic_id
    from knowledge_digest.page_layout import build_topic_layouts
    from knowledge_digest.paths import DigestPaths

    source = "https://source.example/payment"
    stable_topic_id = topic_id(["source-aaaaaaaaaaaaaaaaaaaa"])
    claim = {
        "claim_fingerprint": "c" * 64,
        "text": "Payment API v2 supports refunds.",
        "source_uri": source,
        "content_fingerprint": "d" * 64,
        "fragment_locator": "lines:1-1",
        "raw_id": "raw-1",
    }
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    paths = DigestPaths(tmp_path / "new", tmp_path / "new" / "items", kb_dir, kb_dir / "kb.structure.md")
    structure, errors = kb_structure._publication_contract(
        kb_structure.default_publication_structure(), require_taxonomy=True
    )
    assert not errors and structure is not None

    layouts = build_topic_layouts(
        [
            {
                "cluster_id": "cluster-1",
                "topic_id": stable_topic_id,
                "claims": [claim],
                "final_body": "Payment API v2 supports refunds.\n",
                "publication": {
                    "title": "Payment API",
                    "slug": "payment-api",
                    "category_id": "product-capability",
                    "summary": "提供支付退款能力。",
                    "why": "用于处理客户退款。",
                    "version": "v2",
                    "related_topics": [],
                    "claim_refs": [claim["claim_fingerprint"]],
                    "field_refs": {
                        "title": [claim["claim_fingerprint"]],
                        "category_id": [claim["claim_fingerprint"]],
                        "summary": [claim["claim_fingerprint"]],
                        "why": [claim["claim_fingerprint"]],
                        "version": [claim["claim_fingerprint"]],
                    },
                },
            }
        ],
        paths,
        ("pages",),
        max_lines=300,
        publication=structure,
    )

    layout = layouts[0]
    assert layout["title"] == "Payment API"
    assert layout["publication_category_id"] == "product-capability"
    assert layout["publication"]["title"] == "Payment API"
    category = next(item for item in structure.categories if item.category_id == "product-capability")
    assert layout["split_pages"][0]["target_path"] == f"{category.topic_dir}/payment-api.md"
    rendered = layout["split_pages"][0]["rendered_content"]
    assert "## Summary" in rendered
    assert "提供支付退款能力。" in rendered
    assert "## Why" in rendered
    assert "用于处理客户退款。" in rendered
    assert "## Version" in rendered
    assert "v2" in rendered
    assert "## Related topics" in rendered
    assert "field_refs.summary" in rendered
    assert sum(page["rendered_content"].count(claim["text"]) for page in layout["split_pages"]) == 1


def test_navigation_has_readme_parent_leaf_source_index_and_bounded_related_links(tmp_path) -> None:
    from knowledge_digest.navigation import build_publication_navigation
    from knowledge_digest.paths import DigestPaths

    publication, errors = kb_structure._publication_contract(
        kb_structure.default_publication_structure(), require_taxonomy=True
    )
    assert not errors and publication is not None
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    paths = DigestPaths(tmp_path / "new", tmp_path / "new" / "items", kb_dir, kb_dir / "kb.structure.md")
    topic_id = "topic-aaaaaaaaaaaaaaaa"
    source_index = {
        "schema_version": "1.0.0",
        "entries": [
            {
                "source_uri": "https://source.example/payment",
                "content_fingerprint": "d" * 64,
                "status": "published",
                "target_paths": ["pages/products/product-capability/payment-api.md"],
            }
        ],
    }
    layouts = [
        {
            "topic_id": topic_id,
            "title": "Payment API",
            "publication_category_id": "product-capability",
            "publication": {"product_slug": "terminal"},
            "summary": "Refund support.",
            "split_pages": [
                {
                    "target_path": "pages/products/product-capability/payment-api.md",
                    "page_index": 1,
                    "title": "Payment API",
                }
            ],
            "related_topics": ["topic-missing"],
        }
    ]

    records = build_publication_navigation(
        layouts,
        paths,
        publication,
        topic_universe={topic_id},
        source_index=source_index,
    )
    by_path = {record["target_path"]: record for record in records}
    assert "README.md" in by_path
    assert "managed_by: KnowledgeDigest" in by_path["README.md"]["rendered_content"]
    assert "Home.md" in by_path
    assert "indexes/products.md" in by_path
    assert "indexes/product-capability.md" in by_path
    assert "indexes/sources.md" in by_path
    assert "indexes/products.md" in by_path["Home.md"]["rendered_content"]
    assert "payment-api.md" in by_path["indexes/product-capability.md"]["rendered_content"]
    assert "topic-missing" not in by_path["indexes/product-capability.md"]["rendered_content"]
    assert "## Evidence" not in by_path["indexes/sources.md"]["rendered_content"]
