"""Task7 P2: deterministic topic grouping and explicit mapping contract."""

from __future__ import annotations

import hashlib
from pathlib import Path


try:
    from knowledge_digest.semantic_group import group_topics, load_topic_map
except (ImportError, ModuleNotFoundError):
    # Keep the RED test collectable before the new production module exists.
    group_topics = None
    load_topic_map = None


REPO_ROOT = Path(__file__).resolve().parents[2]


def _block(
    source_path: str,
    block_id: str,
    title: str,
    *,
    product_heading: str | None = None,
    module_heading: str = "Authentication",
) -> dict[str, object]:
    product = product_heading or source_path.split("/", 1)[0]
    return {
        "source_path": source_path,
        "block_id": block_id,
        "content_hash": f"hash-{block_id}",
        "kind": "narrative",
        "line_start": 1,
        "line_end": 1,
        "text": f"facts for {title}",
        "heading_path": (product, module_heading, title),
    }


def _require_api():
    assert group_topics is not None, "semantic_group.group_topics is not implemented"
    assert load_topic_map is not None, "semantic_group.load_topic_map is not implemented"
    return group_topics, load_topic_map


def _groups(result: object) -> tuple[object, ...]:
    groups = getattr(result, "groups", None)
    assert groups is not None, "group_topics must return a result with groups"
    return tuple(groups)


def _member_id(member: object) -> str:
    if hasattr(member, "block_id"):
        return str(getattr(member, "block_id"))
    return str(member["block_id"])


def _group_signature(result: object) -> tuple[tuple[object, ...], ...]:
    signature: list[tuple[object, ...]] = []
    for group in _groups(result):
        signature.append(
            (
                str(getattr(group, "key")),
                str(getattr(group, "product")),
                str(getattr(group, "module_anchor")),
                tuple(sorted(_member_id(member) for member in getattr(group, "members"))),
            )
        )
    return tuple(signature)


def test_task7_group_normalizes_titles_scopes_products_and_is_order_independent() -> None:
    group_topics_api, _ = _require_api()
    blocks = [
        _block("payments/login-a.md", "p-a", "  Login   API  "),
        _block("payments/login-b.md", "p-b", "login api"),
        _block("billing/login.md", "b-a", "LOGIN API", product_heading="Billing"),
        _block("payments/other.md", "p-c", "Other topic"),
    ]

    first = group_topics_api(blocks)
    second = group_topics_api(tuple(reversed(blocks)))

    assert _group_signature(first) == _group_signature(second)
    assert len(_groups(first)) == 3

    payment_login = next(
        group
        for group in _groups(first)
        if getattr(group, "product") == "payments"
        and {_member_id(member) for member in getattr(group, "members")} == {"p-a", "p-b"}
    )
    assert getattr(payment_login, "module_anchor") == "authentication"
    assert {
        getattr(group, "product")
        for group in _groups(first)
        if getattr(group, "key").endswith("login api")
    } == {"payments", "billing"}


def test_task7_group_applies_explicit_aliases_and_reads_audit_only_sources() -> None:
    group_topics_api, load_topic_map_api = _require_api()
    config_path = REPO_ROOT / "config" / "task7-topic-map.json"
    assert load_topic_map_api(config_path) == {
        "topic_aliases": {},
        "audit_only_sources": [],
    }

    blocks = [
        _block("payments/sign-in.md", "sign-in", " Sign   In "),
        _block("payments/login.md", "login", "Login"),
    ]
    result = group_topics_api(
        blocks,
        topic_map={
            "topic_aliases": {" sign in ": "Login"},
            "audit_only_sources": ["payments/sign-in.md"],
        },
    )

    groups = _groups(result)
    assert len(groups) == 1
    assert {_member_id(member) for member in getattr(groups[0], "members")} == {"sign-in", "login"}
    assert getattr(groups[0], "key") == "payments:login"
    assert tuple(getattr(result, "audit_only_sources")) == ("payments/sign-in.md",)


def test_task7_group_model_suggestions_are_report_only_and_do_not_change_members() -> None:
    group_topics_api, _ = _require_api()
    blocks = [
        _block("payments/login.md", "login", "Login"),
        _block("payments/session.md", "session", "Session"),
    ]

    without_suggestions = group_topics_api(blocks)
    with_suggestions = group_topics_api(
        blocks,
        model_suggestions=(
            {
                "product": "payments",
                "from": "login",
                "to": "session",
                "confidence": 0.91,
            },
        ),
    )

    assert _group_signature(with_suggestions) == _group_signature(without_suggestions)
    assert tuple(getattr(with_suggestions, "suggestions")) == (
        {
            "product": "payments",
            "from": "login",
            "to": "session",
            "confidence": 0.91,
        },
    )


def test_task7_group_slugs_top_level_product_without_trailing_directory_space() -> None:
    group_topics_api, _ = _require_api()
    result = group_topics_api(
        (
            _block(
                "emm for android /login.md",
                "android-login",
                "Login",
            ),
        )
    )

    groups = _groups(result)
    assert len(groups) == 1
    assert getattr(groups[0], "product") == "emm-for-android"


def test_task7_group_keeps_distinct_raw_products_separate_after_slug_collision() -> None:
    group_topics_api, _ = _require_api()
    result = group_topics_api(
        (
            _block("foo bar/topic.md", "space-product", "Same topic"),
            _block("foo-bar/topic.md", "hyphen-product", "Same topic"),
        )
    )

    groups = _groups(result)
    assert len(groups) == 2
    assert {
        tuple(sorted(_member_id(member) for member in getattr(group, "members")))
        for group in groups
    } == {("space-product",), ("hyphen-product",)}


def test_task7_group_product_collision_suffix_cannot_consume_another_base_slug() -> None:
    group_topics_api, _ = _require_api()
    hashed_product = "a-b-p" + hashlib.sha256("a_b".encode()).hexdigest()[:10]
    result = group_topics_api(
        (
            _block("a_b/topic.md", "underscore", "Same topic"),
            _block("a-b/topic.md", "hyphen", "Same topic"),
            _block(f"{hashed_product}/topic.md", "ordinary", "Same topic"),
        )
    )

    groups = _groups(result)
    products = {str(getattr(group, "product")) for group in groups}
    assert len(groups) == 3
    assert len(products) == 3
    assert hashed_product in products


def test_task7_group_uses_general_module_when_h2_anchors_are_not_all_identical() -> None:
    group_topics_api, _ = _require_api()
    first = _block("payments/a.md", "h2-a", "Same topic", module_heading="Foo Bar")
    second = _block("payments/b.md", "h2-b", "same topic", module_heading="Foo-Bar")
    third = _block("payments/c.md", "h2-c", "SAME TOPIC")
    third["heading_path"] = ("Payments",)
    third["title"] = "SAME TOPIC"

    result = group_topics_api((first, second, third))

    groups = _groups(result)
    assert len(groups) == 1
    assert getattr(groups[0], "module_anchor") == "_general"


def test_task7_group_disambiguates_distinct_module_titles_with_the_same_slug() -> None:
    group_topics_api, _ = _require_api()
    blocks = (
        _block("payments/topic-a.md", "topic-a", "Topic A", module_heading="Foo Bar"),
        _block("payments/topic-b.md", "topic-b", "Topic B", module_heading="Foo-Bar"),
    )
    first = group_topics_api(blocks)
    second = group_topics_api(tuple(reversed(blocks)))
    first_anchors = {getattr(group, "key"): getattr(group, "module_anchor") for group in getattr(first, "groups")}
    second_anchors = {getattr(group, "key"): getattr(group, "module_anchor") for group in getattr(second, "groups")}
    assert first_anchors == second_anchors
    assert len(set(first_anchors.values())) == 2
    assert all(anchor.startswith("foo-bar-m") for anchor in first_anchors.values())
