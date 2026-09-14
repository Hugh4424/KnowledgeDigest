"""Task7 P5: semantic page structure, naming, links, and lossless layout."""

from __future__ import annotations

from datetime import datetime


try:
    from knowledge_digest.semantic_page import (
        PAGE_FRONTMATTER_FIELDS,
        gbrain_slug,
        render_pages,
    )
except (ImportError, ModuleNotFoundError):
    # Keep the RED assertions collectable before T010 adds the module.
    PAGE_FRONTMATTER_FIELDS = None
    gbrain_slug = None
    render_pages = None


def _block(
    source_path: str,
    block_id: str,
    text: str,
    *,
    kind: str = "narrative",
    heading_path: tuple[str, ...] = ("Payments", "Authentication", "Login"),
    content_hash: str | None = None,
) -> dict[str, object]:
    return {
        "source_path": source_path,
        "block_id": block_id,
        "content_hash": content_hash or f"hash-{block_id}",
        "kind": kind,
        "line_start": 1,
        "line_end": max(1, len(text.splitlines())),
        "text": text,
        "heading_path": heading_path,
    }


def _group(
    key: str,
    title: str,
    members: tuple[dict[str, object], ...],
    *,
    product: str = "payments",
    module_anchor: str = "authentication",
) -> dict[str, object]:
    return {
        "key": key,
        "product": product,
        "title": title,
        "module_anchor": module_anchor,
        "members": members,
    }


def _require_api():
    assert PAGE_FRONTMATTER_FIELDS is not None, "semantic_page is not implemented"
    assert gbrain_slug is not None, "semantic_page.gbrain_slug is not implemented"
    assert render_pages is not None, "semantic_page.render_pages is not implemented"
    return PAGE_FRONTMATTER_FIELDS, gbrain_slug, render_pages


def _page_by_key(pages: tuple[object, ...], key: str) -> object:
    return next(page for page in pages if getattr(page, "topic_key") == key)


def test_task7_page_has_exact_16_field_frontmatter_and_reader_attribution() -> None:
    fields, _, render_pages_api = _require_api()
    primary = _block(
        "payments/login.md",
        "login-reference",
        "| request | response |\n| --- | --- |\n| token | ok |",
        kind="table",
    )
    secondary = _block(
        "payments/session.md",
        "session-narrative",
        "登录流程支持 Android 8.0。",
        heading_path=("Payments", "Authentication", "Session"),
    )
    pages = render_pages_api(
        (_group("payments:login", "登录流程", (primary, secondary)),),
        model_results={
            "payments:login": {
                "title": "登录流程",
                "slug": "Login Flow",
                "intro": "原文明确支持登录流程。",
            }
        },
        claims_by_topic={
            "payments:login": (
                {
                    "claim_id": "claim-login",
                    "source_path": "payments/session.md",
                    "status": "sourced",
                    "text": "登录流程支持 Android 8.0。",
                },
            )
        },
        source_root_name="confluence-raw",
        source_mtimes={
            "payments/login.md": datetime(2026, 1, 2, 10, 0),
            "payments/session.md": datetime(2026, 1, 4, 10, 0),
        },
    )

    assert len(pages) == 1
    page = pages[0]
    assert tuple(getattr(page, "frontmatter")) == tuple(fields)
    assert getattr(page, "frontmatter") == {
        "title": "登录流程",
        "type": "reference",
        "page_model": "derived",
        "scope": "company",
        "product": "payments",
        "section": "authentication",
        "module": "authentication",
        "tier": 2,
        "trust": "medium",
        "source_status": "compiled",
        "quality_status": "formal",
        "created": "2026-01-02",
        "updated": "2026-01-04",
        "generated_by": "knowledge_digest_semantic_compiler.py",
        "tags": ["company", "payments", "authentication"],
        "source": "confluence-raw/payments/login.md; confluence-raw/payments/session.md",
    }
    assert getattr(page, "relative_path") == "products/payments/authentication/login-flow.md"
    assert "来源：login.md — Payments > Authentication > Login" in getattr(page, "text")
    assert "来源：session.md — Payments > Authentication > Session" in getattr(page, "text")
    assert "line_start" not in getattr(page, "text")
    assert "2026-01-02" in getattr(page, "text")


def test_task7_page_adds_reader_attribution_for_sourced_intro_claim() -> None:
    _, _, render_pages_api = _require_api()
    source = _block(
        "payments/login.md",
        "login-narrative",
        "登录流程支持令牌。",
        heading_path=("Payments", "Authentication", "Login"),
    )
    intro = "登录流程支持令牌。"
    page = render_pages_api(
        (_group("payments:login", "登录流程", (source,)),),
        model_results={"payments:login": {"title": "登录流程", "slug": "login", "intro": intro}},
        claims_by_topic={
            "payments:login": (
                {
                    "claim_id": "narrative-login",
                    "source_path": "payments/login.md",
                    "content_hash": source["content_hash"],
                    "line_start": 1,
                    "line_end": 1,
                    "char_start": 0,
                    "char_end": len(intro),
                    "span_start": 0,
                    "span_end": len(intro),
                    "claim_kind": "narrative",
                    "status": "sourced",
                    "text": intro,
                },
                {
                    "claim_id": "intro-login",
                    "source_path": "payments/login.md",
                    "source_block_id": "login-narrative",
                    "content_hash": source["content_hash"],
                    "line_start": 1,
                    "line_end": 1,
                    "char_start": 0,
                    "char_end": len(intro),
                    "span_start": 0,
                    "span_end": len(intro),
                    "claim_kind": "intro",
                    "status": "sourced",
                    "text": intro,
                },
            )
        },
        source_root_name="raw",
        source_mtimes={"payments/login.md": datetime(2026, 1, 2)},
        intro_texts={"payments:login": intro},
    )[0]

    assert f"## 导读\n{intro}" in getattr(page, "text")
    assert "来源：login.md — Payments > Authentication > Login" in getattr(page, "text")


def test_task7_page_slug_is_gbrain_fixed_point_and_collision_order_independent() -> None:
    _, gbrain_slug_api, render_pages_api = _require_api()
    group_a = _group(
        "payments:a",
        "A",
        (_block("payments/a.md", "a", "A。"),),
    )
    group_b = _group(
        "payments:b",
        "B",
        (_block("payments/b.md", "b", "B。"),),
    )
    model_results = {
        "payments:a": {"title": "A", "slug": "Shared Page"},
        "payments:b": {"title": "B", "slug": "Shared Page"},
    }
    first = render_pages_api(
        (group_b, group_a),
        model_results=model_results,
        source_mtimes={"payments/a.md": datetime(2026, 1, 1), "payments/b.md": datetime(2026, 1, 1)},
    )
    second = render_pages_api(
        (group_a, group_b),
        model_results=model_results,
        source_mtimes={"payments/a.md": datetime(2026, 1, 1), "payments/b.md": datetime(2026, 1, 1)},
    )

    first_paths = {getattr(page, "topic_key"): getattr(page, "relative_path") for page in first}
    second_paths = {getattr(page, "topic_key"): getattr(page, "relative_path") for page in second}
    assert first_paths == second_paths
    assert first_paths == {
        "payments:a": "products/payments/authentication/shared-page.md",
        "payments:b": "products/payments/authentication/shared-page-2.md",
    }
    for page in first:
        slug = getattr(page, "slug")
        assert slug == gbrain_slug_api(slug)
    assert len({getattr(page, "relative_path") for page in first}) == 2


def test_task7_page_slug_collision_does_not_consume_another_topic_base_slug() -> None:
    _, _, render_pages_api = _require_api()
    groups = (
        _group("payments:a", "A", (_block("payments/a.md", "a", "A。"),)),
        _group("payments:b", "B", (_block("payments/b.md", "b", "B。"),)),
        _group("payments:c", "C", (_block("payments/c.md", "c", "C。"),)),
    )
    pages = render_pages_api(
        groups,
        model_results={
            "payments:a": {"title": "A", "slug": "Foo"},
            "payments:b": {"title": "B", "slug": "Foo"},
            "payments:c": {"title": "C", "slug": "Foo-2"},
        },
        source_mtimes={
            "payments/a.md": datetime(2026, 1, 1),
            "payments/b.md": datetime(2026, 1, 1),
            "payments/c.md": datetime(2026, 1, 1),
        },
    )
    paths = {getattr(page, "topic_key"): getattr(page, "relative_path") for page in pages}
    assert paths == {
        "payments:a": "products/payments/authentication/foo.md",
        "payments:b": "products/payments/authentication/foo-3.md",
        "payments:c": "products/payments/authentication/foo-2.md",
    }


def test_task7_page_binds_claims_to_exact_same_source_block_heading() -> None:
    _, _, render_pages_api = _require_api()
    first = _block(
        "payments/source.md",
        "first",
        "第一段事实。",
        heading_path=("Payments", "Authentication", "First"),
        content_hash="hash-first",
    )
    second = _block(
        "payments/source.md",
        "second",
        "第二段事实。",
        heading_path=("Payments", "Authentication", "Second"),
        content_hash="hash-second",
    )
    second["line_start"] = 3
    second["line_end"] = 3
    page = render_pages_api(
        (_group("payments:source", "来源说明", (first, second)),),
        model_results={"payments:source": {"title": "来源说明", "slug": "source"}},
        claims_by_topic={
            "payments:source": (
                {
                    "claim_id": "first-claim",
                    "source_path": "payments/source.md",
                    "content_hash": "hash-first",
                    "line_start": 1,
                    "line_end": 1,
                    "span_start": 0,
                    "span_end": len("第一段事实。"),
                    "status": "sourced",
                    "text": "第一段事实。",
                },
                {
                    "claim_id": "second-claim",
                    "source_path": "payments/source.md",
                    "content_hash": "hash-second",
                    "line_start": 3,
                    "line_end": 3,
                    "span_start": 0,
                    "span_end": len("第二段事实。"),
                    "status": "sourced",
                    "text": "第二段事实。",
                },
            )
        },
        source_mtimes={"payments/source.md": datetime(2026, 1, 1)},
    )[0]
    text = getattr(page, "text")
    assert "来源：source.md — Payments > Authentication > First" in text
    assert "来源：source.md — Payments > Authentication > Second" in text
    assert text.count("第一段事实。") == 1
    assert text.count("第二段事实。") == 1


def test_task7_page_preserves_whitespace_only_narrative_tail_and_materializes_anchors() -> None:
    _, _, render_pages_api = _require_api()
    block = _block(
        "payments/whitespace.md",
        "whitespace-block",
        "第一句。\t",
        heading_path=("Payments", "Authentication", "Whitespace"),
    )
    page = render_pages_api(
        (_group("payments:whitespace", "空白保留", (block,)),),
        model_results={"payments:whitespace": {"title": "空白保留", "slug": "whitespace"}},
        claims_by_topic={
            "payments:whitespace": (
                {
                    "claim_id": "whitespace-claim",
                    "source_path": "payments/whitespace.md",
                    "content_hash": block["content_hash"],
                    "line_start": 1,
                    "line_end": 1,
                    "span_start": 0,
                    "span_end": len("第一句。"),
                    "status": "sourced",
                    "text": "第一句。",
                },
            )
        },
        source_mtimes={"payments/whitespace.md": datetime(2026, 1, 1)},
        intro_texts={"payments:whitespace": "原文未明确"},
    )[0]

    assert "\t" in getattr(page, "text")
    assert '<a id="intro"></a>' in getattr(page, "text")
    assert '<a id="narrative"></a>' in getattr(page, "text")
    assert '<a id="block-1"></a>' in getattr(page, "text")


def test_task7_page_reserves_limit_for_intro_before_partitioning() -> None:
    _, _, render_pages_api = _require_api()
    members = tuple(
        _block(
            "payments/full.md",
            f"block-{index}",
            f"事实 {index}。",
            heading_path=("Payments", "Authentication", "Full"),
        )
        for index in range(110)
    )
    claims = tuple(
        {
            "claim_id": f"claim-{index}",
            "source_path": "payments/full.md",
            "content_hash": f"hash-block-{index}",
            "line_start": 1,
            "line_end": 1,
            "span_start": 0,
            "span_end": len(f"事实 {index}。"),
            "status": "sourced",
            "text": f"事实 {index}。",
        }
        for index in range(110)
    )
    pages = render_pages_api(
        (_group("payments:full", "完整页面", members),),
        model_results={"payments:full": {"title": "完整页面", "slug": "full"}},
        claims_by_topic={"payments:full": claims},
        source_mtimes={"payments/full.md": datetime(2026, 1, 1)},
        intro_texts={"payments:full": "导读内容。"},
    )

    assert pages
    assert all(getattr(part, "body_line_count") <= 300 for part in getattr(pages[0], "parts"))
    assert '<a id="intro"></a>' in getattr(pages[0], "text")


def test_task7_page_rejects_normal_first_unit_that_cannot_fit_300_lines() -> None:
    _, _, render_pages_api = _require_api()
    long_text = "\n".join(f"line {index}" for index in range(299))
    try:
        render_pages_api(
            (_group("payments:too-long", "Too Long", (_block("payments/long.md", "long", long_text),)),),
            model_results={"payments:too-long": {"title": "Too Long", "slug": "too-long"}},
            source_mtimes={"payments/long.md": datetime(2026, 1, 1)},
        )
    except ValueError as error:
        assert "300 lines" in str(error)
    else:
        raise AssertionError("a normal first unit must not exceed the 300-line body limit")


def test_task7_page_related_wikilinks_resolve_to_pages_from_narrative_text() -> None:
    _, _, render_pages_api = _require_api()
    login = _group(
        "payments:login",
        "登录流程",
        (_block("payments/login.md", "login", "参见会话管理。"),),
    )
    session = _group(
        "payments:session",
        "会话管理",
        (_block("payments/session.md", "session", "会话管理保存令牌。"),),
    )
    pages = render_pages_api(
        (session, login),
        model_results={
            "payments:login": {"title": "登录说明", "slug": "login-guide"},
            "payments:session": {"title": "会话管理", "slug": "session-management"},
        },
        claims_by_topic={
            "payments:login": (
                {"claim_id": "login-claim", "source_path": "payments/login.md", "status": "sourced", "text": "参见会话管理。"},
            ),
            "payments:session": (
                {"claim_id": "session-claim", "source_path": "payments/session.md", "status": "sourced", "text": "会话管理保存令牌。"},
            ),
        },
        source_mtimes={"payments/login.md": datetime(2026, 1, 1), "payments/session.md": datetime(2026, 1, 1)},
    )

    login_page = _page_by_key(pages, "payments:login")
    assert "## 相关页面" in getattr(login_page, "text")
    assert "[[products/payments/authentication/session-management|会话管理]]" in getattr(login_page, "text")


def test_task7_page_paginates_losslessly_and_marks_oversized_reference_appendix() -> None:
    _, _, render_pages_api = _require_api()
    oversized = "\n".join(f"| {index} | value |" for index in range(305))
    table = _block("payments/table.md", "large-table", oversized, kind="table")
    attachment = _block(
        "payments/image.md",
        "attachment",
        "https://example.com/manual.png?download=1",
        kind="attachment_refs",
        heading_path=("Payments", "Authentication", "Images"),
    )
    narrative = _block(
        "payments/notes.md",
        "notes",
        "普通说明。",
        heading_path=("Payments", "Authentication", "Notes"),
    )
    pages = render_pages_api(
        (_group("payments:large", "大表说明", (table, attachment, narrative)),),
        model_results={"payments:large": {"title": "大表说明", "slug": "large-reference"}},
        claims_by_topic={
            "payments:large": (
                {"claim_id": "notes-claim", "source_path": "payments/notes.md", "status": "sourced", "text": "普通说明。"},
            )
        },
        source_mtimes={
            "payments/table.md": datetime(2026, 1, 1),
            "payments/image.md": datetime(2026, 1, 2),
            "payments/notes.md": datetime(2026, 1, 3),
        },
    )

    page = pages[0]
    parts = tuple(getattr(page, "parts"))
    normal_parts = [part for part in parts if not getattr(part, "oversized_reference_block")]
    appendix_parts = [part for part in parts if getattr(part, "oversized_reference_block")]
    assert normal_parts
    assert all(getattr(part, "body_line_count") <= 300 for part in normal_parts)
    assert len(appendix_parts) == 1
    appendix = appendix_parts[0]
    assert "oversized_reference_block: true" in getattr(appendix, "text")
    assert oversized in getattr(appendix, "text")
    assert getattr(appendix, "text").count(oversized) == 1
    assert "外部资源链接（原样保留；不下载、不改写、不删除）" in getattr(page, "text")
    assert "https://example.com/manual.png?download=1" in getattr(page, "text")
    assert "来源：image.md — Payments > Authentication > Images" in getattr(page, "text")
