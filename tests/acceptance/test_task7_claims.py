"""Task7 P3: claim spans, stable IDs, and rejected intro provenance."""

from __future__ import annotations


try:
    from knowledge_digest.semantic_claims import compile_intro, extract_claims
    from knowledge_digest.semantic_compiler import _intro_claims, _narrative_claims
    from knowledge_digest.semantic_group import TopicGroup
    from knowledge_digest.semantic_split import Block
except (ImportError, ModuleNotFoundError):
    # Keep RED behavior assertions collectable before T006 adds the module.
    compile_intro = None
    extract_claims = None
    _intro_claims = None
    _narrative_claims = None
    TopicGroup = None
    Block = None


def _block(text: str) -> dict[str, object]:
    return {
        "source_path": "payments/login.md",
        "block_id": "login-narrative-1",
        "content_hash": "source-hash-login",
        "kind": "narrative",
        "line_start": 10,
        "line_end": 12,
        "text": text,
        "heading_path": ("Payments", "Authentication", "Login"),
    }


def _require_claim_api():
    assert extract_claims is not None, "semantic_claims.extract_claims is not implemented"
    assert compile_intro is not None, "semantic_claims.compile_intro is not implemented"
    return extract_claims, compile_intro


def _claims(result: object) -> tuple[object, ...]:
    claims = getattr(result, "claims", None)
    assert claims is not None, "extract_claims must return a result with claims"
    return tuple(claims)


def test_task7_claims_split_sentences_and_keep_exact_line_char_spans() -> None:
    extract_claims_api, _ = _require_claim_api()
    text = "同一事实。重复句。重复句。\n第二行包含两个事实；还在同一行！\n"
    block = _block(text)

    first = _claims(extract_claims_api(block))
    second = _claims(extract_claims_api(block))

    assert first == second
    assert len(first) == 5
    assert len({getattr(claim, "claim_id") for claim in first}) == len(first)
    assert [getattr(claim, "occurrence_index") for claim in first] == [1, 1, 2, 1, 1]

    for claim in first:
        char_start = int(getattr(claim, "char_start"))
        char_end = int(getattr(claim, "char_end"))
        assert getattr(claim, "text") == text[char_start:char_end]
        assert getattr(claim, "span_start") == char_start
        assert getattr(claim, "span_end") == char_end
        assert getattr(claim, "source_path") == block["source_path"]
        assert getattr(claim, "content_hash") == block["content_hash"]
        assert int(getattr(claim, "line_start")) >= 10
        assert int(getattr(claim, "line_end")) >= int(getattr(claim, "line_start"))
        assert getattr(claim, "claim_kind") == "narrative"
        assert getattr(claim, "status") == "sourced"

    same_line_claims = [claim for claim in first if getattr(claim, "line_start") == 11]
    assert len(same_line_claims) == 2
    assert same_line_claims[0].char_end <= same_line_claims[1].char_start


def test_task7_claims_reject_unsupported_intro_as_anchored_non_fact() -> None:
    _, compile_intro_api = _require_claim_api()
    source = _block("原文明确的导读事实。")
    result = compile_intro_api(
        ("原文明确的导读事实。", "模型臆测但原文没有这句话。"),
        source_blocks=(source,),
        page_source_path="payments/login.md",
        page_content_hash="page-intro-hash",
    )

    assert getattr(result, "rendered_text") == "原文未明确"
    claims = _claims(result)
    assert len(claims) == 2
    rejected = next(claim for claim in claims if getattr(claim, "status") == "原文未明确")
    assert getattr(rejected, "claim_kind") == "intro"
    assert getattr(rejected, "page_anchor") == "intro"
    assert getattr(rejected, "retrieval_evidence")
    assert rejected in tuple(getattr(result, "rejected_claims"))
    assert rejected not in tuple(getattr(result, "fact_claims"))


def test_task7_claims_do_not_treat_unanchored_intro_as_supported() -> None:
    _, compile_intro_api = _require_claim_api()
    result = compile_intro_api(
        ("没有来源的结论。",),
        source_blocks=(),
        page_source_path="payments/login.md",
        page_content_hash="page-intro-hash",
    )

    claim = _claims(result)[0]
    assert getattr(result, "rendered_text") == "原文未明确"
    assert getattr(claim, "status") == "原文未明确"
    assert getattr(claim, "page_anchor") == "intro"
    assert getattr(claim, "retrieval_evidence")


def test_task7_claims_intro_requires_exact_source_text_not_whitespace_normalization() -> None:
    _, compile_intro_api = _require_claim_api()
    result = compile_intro_api(
        ("第一段事实。",),
        source_blocks=(_block("第一段 事实。"),),
        page_source_path="payments/login.md",
        page_content_hash="page-intro-hash",
    )

    claim = _claims(result)[0]
    assert getattr(result, "rendered_text") == "原文未明确"
    assert getattr(claim, "status") == "原文未明确"


def test_task7_claims_do_not_split_periods_inside_versions_urls_or_filenames() -> None:
    extract_claims_api, _ = _require_claim_api()
    text = (
        "支持 Android 8.0，版本 v1.2.3，文件 a.pdf，"
        "配置 config/task4-source-coverage-89-input.v1.json，"
        "地址 https://example.com/v1.2。"
    )

    claims = _claims(extract_claims_api(_block(text)))

    assert [getattr(claim, "text") for claim in claims] == [text]


def test_task7_claims_do_not_split_common_abbreviations_before_the_next_word() -> None:
    extract_claims_api, _ = _require_claim_api()
    text = "See e.g. Mr. Smith. This sentence is separate."

    claims = _claims(extract_claims_api(_block(text)))

    assert [getattr(claim, "text") for claim in claims] == [
        "See e.g. Mr. Smith.",
        "This sentence is separate.",
    ]


def test_task7_claims_accept_surrogateescaped_source_bytes_for_claim_ids() -> None:
    extract_claims_api, _ = _require_claim_api()
    text = "\udc80 原始字节。"

    claim = _claims(extract_claims_api(_block(text)))[0]

    assert getattr(claim, "claim_id").startswith("cl_")
    assert getattr(claim, "text") == text


def test_task7_claims_skip_punctuation_only_spans_after_repeated_boundaries() -> None:
    extract_claims_api, _ = _require_claim_api()

    claims = _claims(extract_claims_api(_block("好！！")))

    assert [getattr(claim, "text") for claim in claims] == ["好！"]


def _topic_group(key: str, *blocks: object) -> object:
    assert TopicGroup is not None
    return TopicGroup(
        key=key,
        product="payments",
        title=key,
        module_anchor=key.replace(":", "-"),
        members=tuple(blocks),
    )


def _block_object(payload: dict[str, object]) -> object:
    assert Block is not None
    return Block(
        source_path=str(payload["source_path"]),
        block_id=str(payload["block_id"]),
        content_hash=str(payload["content_hash"]),
        kind=str(payload["kind"]),
        line_start=int(payload["line_start"]),
        line_end=int(payload["line_end"]),
        text=str(payload["text"]),
        heading_path=tuple(payload.get("heading_path", ())),
    )


def test_task7_claims_ambiguous_intro_match_fails_closed_with_reason() -> None:
    extract_claims_api, _ = _require_claim_api()
    assert _intro_claims is not None
    first = _block_object(_block("重复句。"))
    second_payload = _block("重复句。")
    second_payload["block_id"] = "login-narrative-2"
    second_payload["line_start"] = 20
    second_payload["line_end"] = 20
    second = _block_object(second_payload)
    group = _topic_group("payments:login", first, second)
    narrative = tuple(
        (*_claims(extract_claims_api(first)), *_claims(extract_claims_api(second)))
    )

    claims, rendered = _intro_claims(
        group,
        sentences=("重复句。",),
        narrative_claims=narrative,
        page_path="products/payments/login.md",
        unavailable=False,
    )

    assert rendered == "原文未明确"
    assert len(claims) == 1
    assert claims[0].status == "原文未明确"
    assert claims[0].retrieval_evidence[0]["reason"] == "ambiguous source claim matches"


def test_task7_claims_intro_ids_use_shared_occurrence_registry_across_topics() -> None:
    extract_claims_api, _ = _require_claim_api()
    assert _intro_claims is not None
    assert _narrative_claims is not None
    first = _block_object(_block("同一句。"))
    second_payload = _block("同一句。")
    second_payload["block_id"] = "login-narrative-2"
    second = _block_object(second_payload)
    groups = (_topic_group("payments:login", first), _topic_group("payments:session", second))
    registry: dict[tuple[str, str], int] = {}
    narratives = _narrative_claims(
        groups,
        {
            "payments:login": "products/payments/login.md",
            "payments:session": "products/payments/session.md",
        },
        occurrence_registry=registry,
    )
    first_intro, _ = _intro_claims(
        groups[0],
        sentences=("同一句。",),
        narrative_claims=narratives["payments:login"],
        page_path="products/payments/login.md",
        unavailable=False,
        occurrence_registry=registry,
    )
    second_intro, _ = _intro_claims(
        groups[1],
        sentences=("同一句。",),
        narrative_claims=narratives["payments:session"],
        page_path="products/payments/session.md",
        unavailable=False,
        occurrence_registry=registry,
    )

    assert first_intro[0].claim_id != second_intro[0].claim_id
