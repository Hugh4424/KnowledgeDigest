"""Task8 K2 acceptance tests, implemented as RED/GREEN vertical slices."""

from __future__ import annotations

import json
import inspect
from hashlib import sha256
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest

TESTS_ROOT = Path(__file__).resolve().parents[1]
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from fixtures.task8_nav import make_batch


try:
    from knowledge_digest.semantic_navigation import NavigationInputError, reconcile_pages
except (ImportError, ModuleNotFoundError):
    NavigationInputError = None
    reconcile_pages = None

try:
    from knowledge_digest.semantic_navigation import build_mount_tree
except (ImportError, ModuleNotFoundError):
    build_mount_tree = None

try:
    from knowledge_digest.semantic_navigation import build_index, build_module_indexes
except (ImportError, ModuleNotFoundError):
    build_index = None
    build_module_indexes = None

try:
    from knowledge_digest.semantic_navigation import build_navigation_frontmatter
except (ImportError, ModuleNotFoundError):
    build_navigation_frontmatter = None

try:
    from knowledge_digest.semantic_navigation import infer_module_title
except (ImportError, ModuleNotFoundError):
    infer_module_title = None

try:
    from knowledge_digest.semantic_navigation import build_home
except (ImportError, ModuleNotFoundError):
    build_home = None

try:
    from knowledge_digest.semantic_navigation import build_navigation_cache_key
except (ImportError, ModuleNotFoundError):
    build_navigation_cache_key = None

try:
    from knowledge_digest.semantic_navigation import resolve_cached_output
except (ImportError, ModuleNotFoundError):
    resolve_cached_output = None

try:
    from knowledge_digest.semantic_navigation import validate_model_output
except (ImportError, ModuleNotFoundError):
    validate_model_output = None

try:
    from knowledge_digest.semantic_navigation import build_navigation_metrics, validate_query_suggestions
except (ImportError, ModuleNotFoundError):
    build_navigation_metrics = None
    validate_query_suggestions = None

try:
    from knowledge_digest.semantic_navigation import check_coverage_three
except (ImportError, ModuleNotFoundError):
    check_coverage_three = None

try:
    from knowledge_digest.semantic_navigation import check_description_criteria
except (ImportError, ModuleNotFoundError):
    check_description_criteria = None

try:
    from knowledge_digest.semantic_navigation import check_query_paths
except (ImportError, ModuleNotFoundError):
    check_query_paths = None

try:
    from knowledge_digest.semantic_navigation import compile_batch_navigation
except (ImportError, ModuleNotFoundError):
    compile_batch_navigation = None

try:
    from knowledge_digest.semantic_navigation import build_navigation_dependencies
except (ImportError, ModuleNotFoundError):
    build_navigation_dependencies = None


def _require_reconcile_api():
    assert reconcile_pages is not None, "semantic_navigation.reconcile_pages is not implemented"
    return reconcile_pages


def _require_mount_tree_api():
    assert build_mount_tree is not None, "semantic_navigation.build_mount_tree is not implemented"
    return build_mount_tree


def _require_mechanical_indexes_api():
    assert build_index is not None, "semantic_navigation.build_index is not implemented"
    assert build_module_indexes is not None, "semantic_navigation.build_module_indexes is not implemented"
    return build_index, build_module_indexes


def _require_frontmatter_api():
    assert build_navigation_frontmatter is not None, "semantic_navigation.build_navigation_frontmatter is not implemented"
    return build_navigation_frontmatter


def _require_module_title_api():
    assert infer_module_title is not None, "semantic_navigation.infer_module_title is not implemented"
    return infer_module_title


def _require_home_api():
    assert build_home is not None, "semantic_navigation.build_home is not implemented"
    return build_home


def _require_cache_key_api():
    assert build_navigation_cache_key is not None, "semantic_navigation.build_navigation_cache_key is not implemented"
    return build_navigation_cache_key


def _require_cached_output_api():
    assert resolve_cached_output is not None, "semantic_navigation.resolve_cached_output is not implemented"
    return resolve_cached_output


def _require_model_output_api():
    assert validate_model_output is not None, "semantic_navigation.validate_model_output is not implemented"
    return validate_model_output


def _require_suggestion_metrics_api():
    assert validate_query_suggestions is not None, "semantic_navigation.validate_query_suggestions is not implemented"
    assert build_navigation_metrics is not None, "semantic_navigation.build_navigation_metrics is not implemented"
    return validate_query_suggestions, build_navigation_metrics


def _require_coverage_api():
    assert check_coverage_three is not None, "semantic_navigation.check_coverage_three is not implemented"
    return check_coverage_three


def _require_description_check_api():
    assert check_description_criteria is not None, "semantic_navigation.check_description_criteria is not implemented"
    return check_description_criteria


def _require_query_path_api():
    assert check_query_paths is not None, "semantic_navigation.check_query_paths is not implemented"
    return check_query_paths


def _require_compile_api():
    assert compile_batch_navigation is not None, "semantic_navigation.compile_batch_navigation is not implemented"
    return compile_batch_navigation


def _require_production_dependencies_api():
    assert build_navigation_dependencies is not None, "semantic_navigation.build_navigation_dependencies is not implemented"
    return build_navigation_dependencies


def test_reconcile_happy_对账(tmp_path: Path) -> None:
    reconcile = _require_reconcile_api()
    pages = reconcile(make_batch(tmp_path))

    assert tuple(page.page_path for page in pages) == (
        "products/GoInsight/authentication/login.md",
        "products/GoInsight/billing/invoice.md",
        "products/emm-android/authentication/device-login.md",
    )
    assert {(page.product, page.section) for page in pages} == {
        ("GoInsight", "authentication"),
        ("GoInsight", "billing"),
        ("emm-android", "authentication"),
    }


@pytest.mark.parametrize("missing_field", ("run_status", "blockers", "source_ledger"))
def test_reconcile_manifest_missing_field_缺字段(tmp_path: Path, missing_field: str) -> None:
    reconcile = _require_reconcile_api()
    assert NavigationInputError is not None, "semantic_navigation.NavigationInputError is not implemented"
    batch = make_batch(tmp_path)
    manifest_path = batch / "_audit" / "page-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest[missing_field]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(NavigationInputError) as caught:
        reconcile(batch)

    assert caught.value.reason == f"missing-manifest-field:{missing_field}"


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    (
        ("manifest_file_missing", "manifest-page-file-missing"),
        ("products_file_undeclared", "products-page-undeclared"),
        ("index_name_conflict", "nav-index-name-conflict"),
    ),
)
def test_reconcile_bidirectional_双向对账三态(tmp_path: Path, case: str, expected_reason: str) -> None:
    reconcile = _require_reconcile_api()
    assert NavigationInputError is not None, "semantic_navigation.NavigationInputError is not implemented"
    batch = make_batch(tmp_path)
    manifest_path = batch / "_audit" / "page-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first = manifest["pages"][0]
    first_path = batch / first["page_path"]

    if case == "manifest_file_missing":
        first_path.unlink()
    elif case == "products_file_undeclared":
        extra = batch / "products" / "GoInsight" / "authentication" / "not-in-manifest.md"
        extra.write_text("---\ntitle: extra\n---\n\n# extra\n", encoding="utf-8")
    else:
        index_path = "products/GoInsight/authentication/Index.md"
        first["page_path"] = index_path
        first["page_paths"] = [index_path]
        first_path.unlink()
        (batch / index_path).write_bytes(
            (batch / "products/GoInsight/billing/invoice.md").read_bytes()
        )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(NavigationInputError) as caught:
        reconcile(batch)

    assert caught.value.reason == expected_reason


def test_build_mount_tree_挂载树生成(tmp_path: Path) -> None:
    pages = _require_reconcile_api()(make_batch(tmp_path))
    tree = _require_mount_tree_api()(pages)

    assert tuple(tree) == ("GoInsight", "emm-android")
    assert tuple(tree["GoInsight"]) == ("authentication", "billing")
    authentication = tree["GoInsight"]["authentication"]
    assert tuple(entry.wikilink for entry in authentication) == (
        "[[products/GoInsight/authentication/login|登录认证]]",
    )
    assert authentication[0].description is None
    build_global_index, build_modules = _require_mechanical_indexes_api()
    index = build_global_index(tree)
    module_indexes = build_modules(tree)
    assert "## GoInsight" in index.text
    assert "- [[products/GoInsight/authentication/Index|authentication]]" in index.text
    assert tuple(module_indexes) == (
        "products/GoInsight/authentication/Index.md",
        "products/GoInsight/billing/Index.md",
        "products/emm-android/authentication/Index.md",
    )
    assert "[[products/GoInsight/authentication/login|登录认证]]" in module_indexes[
        "products/GoInsight/authentication/Index.md"
    ].text
    assert "description: <!-- description:pending -->" in module_indexes[
        "products/GoInsight/authentication/Index.md"
    ].text


def test_build_frontmatter_contract_frontmatter() -> None:
    build_frontmatter = _require_frontmatter_api()
    common = {
        "type": "reference",
        "page_model": "derived",
        "scope": "company",
        "trust": "medium",
        "source_status": "compiled",
        "quality_status": "formal",
        "created": "2026-01-01",
        "updated": "2026-01-06",
        "generated_by": "knowledge_digest_semantic_navigation.py",
        "tags": ["company", "navigation"],
        "source": "batch",
    }

    home = build_frontmatter(
        title="批次入口",
        product="navigation",
        section="navigation",
        module="navigation",
        tier=1,
        created="2026-01-01",
        updated="2026-01-06",
    )
    index = build_frontmatter(
        title="知识索引",
        product="navigation",
        section="navigation",
        module="navigation",
        tier=1,
        created="2026-01-01",
        updated="2026-01-06",
    )
    module = build_frontmatter(
        title="认证模块",
        product="GoInsight",
        section="authentication",
        module="authentication",
        tier=2,
        created="2026-01-01",
        updated="2026-01-06",
    )

    assert tuple(home) == (
        "title", "type", "page_model", "scope", "product", "section", "module", "tier",
        "trust", "source_status", "quality_status", "created", "updated", "generated_by", "tags", "source",
    )
    assert dict(home) == {"title": "批次入口", "product": "navigation", "section": "navigation", "module": "navigation", "tier": 1, **common}
    assert dict(index) == {"title": "知识索引", "product": "navigation", "section": "navigation", "module": "navigation", "tier": 1, **common}
    assert dict(module) == {"title": "认证模块", "product": "GoInsight", "section": "authentication", "module": "authentication", "tier": 2, **common}


def test_module_title_inference_模块中文名推断() -> None:
    infer = _require_module_title_api()

    assert infer(("终端-设备管理", "设备管理-终端", "终端-激活")) == "终端"
    assert infer(("Beta-Alpha", "Alpha-Beta")) == "Alpha"
    assert infer(("单页标题",)) == "单页标题"
    assert infer(()) == "模块"


def test_home_mechanical_sections(tmp_path: Path) -> None:
    pages = _require_reconcile_api()(make_batch(tmp_path))
    tree = _require_mount_tree_api()(pages)
    home = _require_home_api()(tree, success_pages=3, blocked_sources=0)

    assert home.relative_path == "Home.md"
    assert "nav: success_pages=3 blocked_sources=0" in home.text
    assert "- [[Index|知识索引]]" in home.text
    assert "- [[Index#GoInsight|GoInsight]]" in home.text
    assert "- [[Index#emm-android|emm-android]]" in home.text
    assert "<!-- query-suggestions:pending -->" in home.text
    assert "本目录为临时对照产物；正式入口归 K3。" in home.text
    assert "fixture" not in home.text.lower()
    assert "2026-01-01" not in home.body


def test_cache_key_contract_缓存键契约() -> None:
    build_key = _require_cache_key_api()
    base = {
        "kind": "description",
        "input_bytes": b"page bytes v1",
        "model_id": "qwen3.8",
        "prompt_version": "task8-desc-v1",
        "topic_map_version": "task8-map-v1",
    }
    original = build_key(**base)

    assert original.startswith("task8-desc:")
    assert len(original.removeprefix("task8-desc:")) == 64
    assert build_key(**{**base, "kind": "suggestion"}).startswith("task8-suggest:")
    assert build_key(**{**base, "input_bytes": b"page bytes v2"}) != original
    assert build_key(**{**base, "model_id": "qwen3.9"}) != original
    assert build_key(**{**base, "prompt_version": "task8-desc-v2"}) != original
    assert build_key(**{**base, "topic_map_version": "task8-map-v2"}) != original


def test_cache_hit_no_call_缓存命中零调用() -> None:
    resolve = _require_cached_output_api()

    class DictCache:
        def __init__(self, values: dict[str, str] | None = None) -> None:
            self.values = values or {}

        def get(self, key: str) -> str | None:
            return self.values.get(key)

        def set(self, key: str, value: str) -> None:
            self.values[key] = value

    class FakeGateway:
        def __init__(self, value: str) -> None:
            self.value = value
            self.calls = 0

        def complete(self, prompt: str) -> str:
            self.calls += 1
            return self.value

    hit_cache = DictCache({"task8-desc:hit": "cached description"})
    hit_gateway = FakeGateway("fresh description")
    assert resolve(cache=hit_cache, gateway=hit_gateway, cache_key="task8-desc:hit", prompt="describe") == "cached description"
    assert hit_gateway.calls == 0

    miss_cache = DictCache()
    miss_gateway = FakeGateway("fresh description")
    assert resolve(cache=miss_cache, gateway=miss_gateway, cache_key="task8-desc:miss", prompt="describe") == "fresh description"
    assert miss_gateway.calls == 1
    assert miss_cache.values == {"task8-desc:miss": "fresh description"}


def test_jsonl_cache_entry_keeps_input_fingerprint(tmp_path: Path) -> None:
    from knowledge_digest.semantic_navigation import JsonlNavigationCache

    cache = JsonlNavigationCache(
        tmp_path / "model-cache",
        model_id="qwen3.8",
        prompt_version="task8-navigation-v1",
        topic_map_version="task8-topic-map-v1",
    )
    material = b"page bytes"
    key = _require_cache_key_api()(
        kind="description",
        input_bytes=material,
        model_id="qwen3.8",
        prompt_version="task8-navigation-v1",
        topic_map_version="task8-topic-map-v1",
    )
    resolve_cached_output = _require_cached_output_api()
    resolve_cached_output(
        cache=cache,
        gateway=_SequenceGateway(["这页帮助你完成登录配置。"]),
        cache_key=key,
        prompt="describe",
        created_from_fingerprint=sha256(material).hexdigest(),
    )

    entry = json.loads(cache.path.read_text(encoding="utf-8"))
    assert entry["cache_key"] == key
    assert entry["created_from_fingerprint"] == sha256(material).hexdigest()
    assert entry["model_id"] == "qwen3.8"

    cache.set_with_fingerprint(key, "冲突结果", fingerprint=sha256(material).hexdigest())
    with pytest.raises(NavigationInputError) as caught:
        cache.get(key)
    assert caught.value.reason == "cache-invalid"


def test_model_output_validation_模型输出校验_空_拒绝词() -> None:
    validate = _require_model_output_api()

    for value in ("", "   "):
        with pytest.raises(NavigationInputError) as caught:
            validate(value)
        assert caught.value.reason == "model-output-missing"

    with pytest.raises(NavigationInputError) as caught:
        validate("这是最佳方案")
    assert caught.value.reason == "model-output-rejected"
    assert validate("这页帮助你完成登录配置") == "这页帮助你完成登录配置"


def test_description_output_rejects_question_and_allows_long_single_sentence() -> None:
    from knowledge_digest.semantic_navigation import validate_description_output

    with pytest.raises(NavigationInputError):
        validate_description_output("如何配置登录？")
    long_description = "这页帮助你完成登录认证配置并核对设备状态和异常处理流程以便后续排查问题并支持后续审计与维护工作同时说明相关字段来源和变更影响"
    assert len(long_description) > 60
    assert validate_description_output(long_description)


def test_suggestion_count_and_metrics_建议数与预算记账() -> None:
    validate_suggestions, build_metrics = _require_suggestion_metrics_api()

    assert validate_suggestions(("如何登录？", "登录需要什么？", "登录失败查哪里？", "登录配置在哪？")) == (
        "如何登录？",
        "登录需要什么？",
        "登录失败查哪里？",
        "登录配置在哪？",
    )
    with pytest.raises(NavigationInputError) as caught:
        validate_suggestions(("只有一条", "只有两条"))
    assert caught.value.reason == "query-suggestions-missing"

    metrics = build_metrics(page_count=3, provider_calls=4, cache_hits=1)
    assert metrics["planned_provider_calls"] == 4
    assert metrics["provider_calls"] == 4
    assert metrics["cache_hits"] == 1


def test_check_coverage_three_覆盖判定三件套() -> None:
    check = _require_coverage_api()
    pages = (
        "products/GoInsight/authentication/login.md",
        "products/GoInsight/authentication/orphan.md",
    )
    base = {
        "Home.md": "[[Index]]",
        "Index.md": "[[products/GoInsight/authentication/Index]]",
        "products/GoInsight/authentication/Index.md": "[[products/GoInsight/authentication/login]]",
    }

    orphan_reasons = check(page_paths=pages, documents=base)
    assert any(reason.startswith("coverage-orphan:") for reason in orphan_reasons)

    dead_link_reasons = check(
        page_paths=pages[:1],
        documents={
            **base,
            "products/GoInsight/authentication/Index.md": "[[products/GoInsight/authentication/missing]]",
        },
    )
    assert any(reason.startswith("coverage-dead-link:") for reason in dead_link_reasons)

    outside_manifest_reasons = check(
        page_paths=pages[:1],
        documents={
            **base,
            "products/GoInsight/authentication/Index.md": "[[products/foreign/foreign]]",
            "products/foreign/foreign.md": "",
        },
    )
    assert any(reason.startswith("coverage-outside-manifest:") for reason in outside_manifest_reasons)


def test_check_description_criteria_描述四判据() -> None:
    check = _require_description_check_api()
    metadata = {
        "p1": {"title": "登录", "product": "GoInsight", "section": "认证"},
        "p2": {"title": "设备", "product": "GoInsight", "section": "认证"},
        "p3": {"title": "账号", "product": "GoInsight", "section": "认证"},
    }

    exact = check(
        descriptions={"p1": "登录流程！", "p2": "登录流程!"},
        page_metadata={"p1": metadata["p1"], "p2": metadata["p2"]},
    )
    assert any(reason.startswith("description-exact-duplicate:") for reason in exact)

    skeleton = check(
        descriptions={
            "p1": "登录页面用于配置认证流程。",
            "p2": "设备页面用于配置认证流程。",
            "p3": "账号页面用于配置认证流程。",
        },
        page_metadata=metadata,
    )
    assert any(reason.startswith("description-skeleton-duplicate:") for reason in skeleton)

    question = check(
        descriptions={
            "p1": "如何配置登录？",
            "p2": "如何配置设备？",
            "p3": "如何配置账号？",
        },
        page_metadata=metadata,
    )
    assert any(reason.startswith("description-question-template:") for reason in question)

    empty = check(
        descriptions={"p1": "  "},
        page_metadata={"p1": metadata["p1"]},
    )
    assert any(reason.startswith("description-empty:p1") for reason in empty)


def test_check_description_criteria_疑问模板跨前缀合计() -> None:
    check = _require_description_check_api()
    metadata = {
        "p1": {"title": "登录", "product": "GoInsight", "section": "认证"},
        "p2": {"title": "设备", "product": "GoInsight", "section": "认证"},
        "p3": {"title": "账号", "product": "GoInsight", "section": "认证"},
        "p4": {"title": "发票", "product": "GoInsight", "section": "账单"},
    }

    reasons = check(
        descriptions={
            "p1": "如何配置登录？",
            "p2": "如何配置设备？",
            "p3": "什么是账号？",
            "p4": "什么是发票？",
        },
        page_metadata=metadata,
    )

    assert "description-question-template:aggregate" in reasons


def test_path_sample_and_gate_路径抽查_n10(tmp_path: Path) -> None:
    check = _require_query_path_api()
    query_fixture = tmp_path / "queries.json"
    query_fixture.write_text(
        json.dumps(
            {
                "schema_version": "task8-query-paths.v1",
                "status": "frozen",
                "queries": [
                    {"id": f"QP-{index:02d}", "query": "如何找到目标？", "target_slug": "target"}
                    for index in range(1, 11)
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    page_paths = ("products/GoInsight/authentication/target.md",)
    short_documents = {
        "Home.md": "[[Index]]",
        "Index.md": "[[products/GoInsight/authentication/Index]]",
        "products/GoInsight/authentication/Index.md": "[[products/GoInsight/authentication/target]]",
    }
    long_documents = {
        "Home.md": "[[Index]]",
        "Index.md": "[[products/GoInsight/one/Index]]",
        "products/GoInsight/one/Index.md": "[[products/GoInsight/two/Index]]",
        "products/GoInsight/two/Index.md": "[[products/GoInsight/three/Index]]",
        "products/GoInsight/three/Index.md": "[[products/GoInsight/authentication/target]]",
    }

    passed = check(documents=short_documents, page_paths=page_paths, query_fixture=query_fixture)
    assert passed.status == "passed"
    assert passed.checked == 10
    assert passed.reasons == ()

    blocked = check(documents=long_documents, page_paths=page_paths, query_fixture=query_fixture)
    assert blocked.status == "blocked"
    assert any(reason.startswith("query-path-too-long:QP-01") for reason in blocked.reasons)

    incomplete = check(documents=short_documents, page_paths=page_paths, query_fixture=None)
    assert incomplete.status == "incomplete"
    assert incomplete.reasons == ("query-fixture-missing",)


def test_e2e_incomplete_query_fixture_blocks_navigation(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    batch = make_batch(tmp_path / "incomplete-query")
    query_fixture = tmp_path / "incomplete-query.json"
    query_fixture.write_text(
        json.dumps(
            {
                "schema_version": "task8-query-paths.v1",
                "status": "frozen",
                "queries": [
                    {"id": f"QP-{index:02d}", "query": "如何找到目标？"}
                    for index in range(1, 11)
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = compile_navigation(
        batch,
        cache=_StringCache(),
        gateway=_SequenceGateway(_valid_model_outputs()),
        query_fixture=query_fixture,
    )

    assert result.navigation_status == "blocked"
    assert "query-target-slug-missing:QP-01" in result.blocked_reasons
    assert not (batch / "Home.md").exists()
    assert not (batch / "Index.md").exists()
    assert not (batch / "_audit" / "nav-staging").exists()
    manifest = json.loads((batch / "_audit" / "page-manifest.json").read_text(encoding="utf-8"))
    assert manifest["navigation"]["navigation_status"] == "blocked"


class _StringCache:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


class _SequenceGateway:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return self.outputs.pop(0)


class _UnavailableGateway:
    def complete(self, prompt: str) -> str:
        raise RuntimeError("provider unavailable")


def _valid_model_outputs() -> list[str]:
    return [
        "帮助你完成登录认证配置。",
        "帮助你核对发票字段与账单设置。",
        "帮助你完成设备认证步骤。",
        json.dumps(["如何完成登录认证配置？", "哪里查看发票字段？", "设备认证失败怎么排查？"], ensure_ascii=False),
    ]


def test_e2e_manifest_and_cleanup_e2e(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    outputs = [
        "帮助你完成登录认证配置。",
        "帮助你核对发票字段与账单设置。",
        "帮助你完成设备认证步骤。",
        json.dumps(["如何完成登录认证配置？", "哪里查看发票字段？", "设备认证失败怎么排查？"], ensure_ascii=False),
    ]
    cache = _StringCache()
    gateway = _SequenceGateway(outputs)
    batch = make_batch(tmp_path / "success")

    result = compile_navigation(batch, cache=cache, gateway=gateway, query_fixture=None)

    assert result.navigation_status == "generated_ok"
    assert result.success_pages == 3
    assert result.blocked_sources == 0
    assert result.blocked_reasons == ()
    assert (batch / "Home.md").is_file()
    assert (batch / "Index.md").is_file()
    assert len(list(batch.glob("products/*/*/Index.md"))) == 3
    assert "帮助你完成登录认证配置。" in (batch / "products/GoInsight/authentication/Index.md").read_text(encoding="utf-8")
    assert "如何完成登录认证配置？" in (batch / "Home.md").read_text(encoding="utf-8")
    assert not (batch / "_audit" / "nav-staging").exists()
    manifest = json.loads((batch / "_audit" / "page-manifest.json").read_text(encoding="utf-8"))
    assert manifest["navigation"] == {
        "navigation_status": "generated_ok",
        "success_pages": 3,
        "blocked_sources": 0,
        "blocked_reasons": [],
    }
    metrics = json.loads((batch / "_audit" / "run-metrics.json").read_text(encoding="utf-8"))
    assert metrics["task8_navigation"]["planned_provider_calls"] == 4
    assert metrics["task8_navigation"]["description_calls"] == 3
    assert metrics["task8_navigation"]["actual_provider_calls"] == 4
    assert gateway.calls == 4

    blocked = make_batch(tmp_path / "blocked")
    blocked_manifest_path = blocked / "_audit" / "page-manifest.json"
    before = json.loads(blocked_manifest_path.read_text(encoding="utf-8"))
    staging = blocked / "_audit" / "nav-staging"
    staging.mkdir(parents=True)
    (staging / "old.md").write_text("old staging", encoding="utf-8")
    blocked_result = compile_navigation(
        blocked,
        cache=_StringCache(),
        gateway=_SequenceGateway(["", "unused"]),
        query_fixture=None,
    )

    assert blocked_result.navigation_status == "blocked"
    assert any(reason == "model-output-missing" for reason in blocked_result.blocked_reasons)
    assert not (blocked / "Home.md").exists()
    assert not (blocked / "Index.md").exists()
    assert not (blocked / "_audit" / "nav-staging").exists()
    after = json.loads(blocked_manifest_path.read_text(encoding="utf-8"))
    assert {key: value for key, value in after.items() if key != "navigation"} == before
    assert after["navigation"]["navigation_status"] == "blocked"


def test_e2e_rerun_bytes_同输入双跑字节一致(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    outputs = [
        "帮助你完成登录认证配置。",
        "帮助你核对发票字段与账单设置。",
        "帮助你完成设备认证步骤。",
        json.dumps(["如何完成登录认证配置？", "哪里查看发票字段？", "设备认证失败怎么排查？"], ensure_ascii=False),
    ]
    cache = _StringCache()
    first_gateway = _SequenceGateway(outputs)
    first = make_batch(tmp_path / "first")
    first_result = compile_navigation(first, cache=cache, gateway=first_gateway, query_fixture=None)

    second_gateway = _SequenceGateway([])
    second = make_batch(tmp_path / "second")
    second_result = compile_navigation(second, cache=cache, gateway=second_gateway, query_fixture=None)

    assert first_result.navigation_status == "generated_ok"
    assert second_result.navigation_status == "generated_ok"
    assert first_gateway.calls == 4
    assert second_gateway.calls == 0
    relative_paths = (
        "Home.md",
        "Index.md",
        "products/GoInsight/authentication/Index.md",
        "products/GoInsight/billing/Index.md",
        "products/emm-android/authentication/Index.md",
    )
    assert {path: (first / path).read_bytes() for path in relative_paths} == {
        path: (second / path).read_bytes() for path in relative_paths
    }


def test_e2e_write_audit_写路径审计(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    batch = make_batch(tmp_path / "batch")
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    before_outside = {path: path.read_bytes() for path in outside.rglob("*") if path.is_file()}
    result = compile_navigation(
        batch,
        cache=_StringCache(),
        gateway=_SequenceGateway(
            [
                "帮助你完成登录认证配置。",
                "帮助你核对发票字段与账单设置。",
                "帮助你完成设备认证步骤。",
                json.dumps(["如何完成登录认证配置？", "哪里查看发票字段？", "设备认证失败怎么排查？"], ensure_ascii=False),
            ]
        ),
        query_fixture=None,
    )

    assert result.navigation_status == "generated_ok"
    allowed_new = {
        "Home.md",
        "Index.md",
        "_audit/page-manifest.json",
        "_audit/run-metrics.json",
        "products/GoInsight/authentication/Index.md",
        "products/GoInsight/billing/Index.md",
        "products/emm-android/authentication/Index.md",
    }
    original_paths = {
        path.relative_to(batch).as_posix()
        for path in batch.rglob("*")
        if path.is_file()
    }
    new_paths = original_paths - {
        "README.md",
        "_audit/reference-blocks.jsonl",
        "_audit/sources.jsonl",
        "_audit/page-manifest.json",
        "_audit/run-metrics.json",
        "_audit/suspected-synonyms.md",
        "products/GoInsight/authentication/login.md",
        "products/GoInsight/billing/invoice.md",
        "products/emm-android/authentication/device-login.md",
    }
    assert new_paths <= allowed_new
    assert {path: path.read_bytes() for path in outside.rglob("*") if path.is_file()} == before_outside
    assert not (batch / "_audit" / "nav-staging").exists()


def test_e2e_commit_failure_rolls_back_without_manifest(tmp_path: Path, monkeypatch) -> None:
    import knowledge_digest.semantic_navigation as semantic_navigation

    batch = make_batch(tmp_path / "commit-failure")
    manifest_path = batch / "_audit" / "page-manifest.json"
    metrics_path = batch / "_audit" / "run-metrics.json"
    original_manifest = manifest_path.read_bytes()
    original_metrics = metrics_path.read_bytes()
    existing_navigation = {
        "Home.md": b"old home\n",
        "Index.md": b"old index\n",
        "products/GoInsight/authentication/Index.md": b"old authentication\n",
        "products/GoInsight/billing/Index.md": b"old billing\n",
        "products/emm-android/authentication/Index.md": b"old device\n",
    }
    for relative_path, content in existing_navigation.items():
        path = batch / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def fail_metrics(*args, **kwargs):
        raise OSError("simulated metrics write failure")

    monkeypatch.setattr(semantic_navigation, "_write_navigation_metrics", fail_metrics)
    result = semantic_navigation.compile_batch_navigation(
        batch,
        cache=_StringCache(),
        gateway=_SequenceGateway(_valid_model_outputs()),
        query_fixture=None,
    )

    assert result.navigation_status == "blocked"
    assert "navigation-commit-failed" in result.blocked_reasons
    assert manifest_path.read_bytes() == original_manifest
    assert metrics_path.read_bytes() == original_metrics
    assert {relative_path: (batch / relative_path).read_bytes() for relative_path in existing_navigation} == existing_navigation
    assert not (batch / "_audit" / "nav-staging").exists()


def test_e2e_partial_success_部分成功对账(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    batch = make_batch(tmp_path / "batch")
    manifest_path = batch / "_audit" / "page-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["blockers"] = [
        {"source_path": "missing/one.md", "reason": "blocked"},
        {"source_path": "missing/two.md", "reason": "blocked"},
    ]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = compile_navigation(
        batch,
        cache=_StringCache(),
        gateway=_SequenceGateway(
            [
                "帮助你完成登录认证配置。",
                "帮助你核对发票字段与账单设置。",
                "帮助你完成设备认证步骤。",
                json.dumps(["如何完成登录认证配置？", "哪里查看发票字段？", "设备认证失败怎么排查？"], ensure_ascii=False),
            ]
        ),
        query_fixture=None,
    )

    assert result.navigation_status == "generated_ok"
    assert result.success_pages == 3
    assert result.blocked_sources == 2
    assert "nav: success_pages=3 blocked_sources=2" in (batch / "Home.md").read_text(encoding="utf-8")
    after = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert after["navigation"]["success_pages"] == 3
    assert after["navigation"]["blocked_sources"] == 2
    assert after["navigation"]["blocked_reasons"] == []


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    (
        ("model_unavailable", "model-gateway-failed"),
        ("empty_output", "model-output-missing"),
        ("rejection_word", "model-output-rejected"),
        ("k1_blocked", "K1-run-not-complete"),
        ("reconciliation_violation", "manifest-page-file-missing"),
        ("frontmatter_missing", "nav-frontmatter-incomplete"),
        ("zero_pages", "zero-page-batch"),
    ),
)
def test_e2e_blocked_matrix_blocked(tmp_path: Path, case: str, expected_reason: str) -> None:
    compile_navigation = _require_compile_api()
    batch = make_batch(tmp_path / case)
    manifest_path = batch / "_audit" / "page-manifest.json"
    before = json.loads(manifest_path.read_text(encoding="utf-8"))
    staging = batch / "_audit" / "nav-staging"
    staging.mkdir(parents=True)
    (staging / "stale.md").write_text("stale", encoding="utf-8")

    if case == "k1_blocked":
        manifest = dict(before)
        manifest["run_status"] = "blocked"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif case == "reconciliation_violation":
        first = batch / before["pages"][0]["page_path"]
        first.unlink()
    elif case == "frontmatter_missing":
        first = batch / before["pages"][0]["page_path"]
        first.write_text(first.read_text(encoding="utf-8").replace('product: "GoInsight"\n', ""), encoding="utf-8")
    elif case == "zero_pages":
        for page in (batch / "products").rglob("*.md"):
            page.unlink()
        manifest = dict(before)
        manifest["pages"] = []
        manifest["source_to_pages"] = {}
        manifest["source_ledger"] = []
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    expected_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    gateway: object
    if case == "model_unavailable":
        gateway = _UnavailableGateway()
    elif case == "empty_output":
        gateway = _SequenceGateway(["", "unused"])
    elif case == "rejection_word":
        gateway = _SequenceGateway(["这是最佳方案", "unused"])
    else:
        gateway = _SequenceGateway(_valid_model_outputs())
    result = compile_navigation(batch, cache=_StringCache(), gateway=gateway, query_fixture=None)

    assert result.navigation_status == "blocked"
    assert any(reason == expected_reason or reason.startswith(expected_reason + ":") for reason in result.blocked_reasons)
    assert not (batch / "Home.md").exists()
    assert not (batch / "Index.md").exists()
    assert not (batch / "_audit" / "nav-staging").exists()
    after = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {key: value for key, value in after.items() if key != "navigation"} == {
        key: value for key, value in expected_manifest.items() if key != "navigation"
    }
    assert after["navigation"]["navigation_status"] == "blocked"


def test_e2e_interrupted_manifest_does_not_write_e2e(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    batch = make_batch(tmp_path / "interrupted")
    manifest_path = batch / "_audit" / "page-manifest.json"
    original = manifest_path.read_bytes()
    manifest_path.write_bytes(b"{not-json\n")
    result = compile_navigation(
        batch,
        cache=_StringCache(),
        gateway=_SequenceGateway(_valid_model_outputs()),
        query_fixture=None,
    )

    assert result.navigation_status == "blocked"
    assert any(reason == "manifest-invalid" for reason in result.blocked_reasons)
    assert manifest_path.read_bytes() == b"{not-json\n"
    assert not (batch / "Home.md").exists()
    assert not (batch / "Index.md").exists()
    assert not (batch / "_audit" / "nav-staging").exists()
    assert original != manifest_path.read_bytes()


def test_production_wiring_生产接线(tmp_path: Path) -> None:
    build_dependencies = _require_production_dependencies_api()
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "llm": {
                    "api_format": "openai",
                    "base_url": "https://example.invalid/v1",
                    "api_key": "test-only-secret",
                    "model": "qwen3.8",
                    "timeout_seconds": 1,
                }
            }
        ),
        encoding="utf-8",
    )
    query_fixture = Path("tests/fixtures/task8_nav/query_fixture_sample.json")
    dependencies = build_dependencies(
        cache_root=tmp_path / "cache" / "model-cache",
        provider_config_path=config,
        query_fixture=query_fixture,
    )

    assert dependencies.gateway.model_id == "qwen3.8"
    assert dependencies.cache.path == tmp_path / "cache" / "model-cache" / "entries.jsonl"
    assert dependencies.query_fixture == query_fixture
    signature = inspect.signature(_require_compile_api())
    assert signature.parameters["cache"].default is inspect.Parameter.empty
    assert signature.parameters["gateway"].default is inspect.Parameter.empty
    assert signature.parameters["query_fixture"].default is inspect.Parameter.empty

    missing = build_dependencies(
        cache_root=tmp_path / "missing-provider-cache",
        provider_config_path=tmp_path / "missing-provider.json",
        query_fixture=None,
    )
    with pytest.raises(NavigationInputError) as caught:
        missing.gateway.complete("describe")
    assert caught.value.reason == "provider-config-missing"

    blocked_batch = make_batch(tmp_path / "missing-provider-batch")
    blocked_manifest_path = blocked_batch / "_audit" / "page-manifest.json"
    blocked_manifest = json.loads(blocked_manifest_path.read_text(encoding="utf-8"))
    blocked_manifest["run_status"] = "blocked"
    blocked_manifest_path.write_text(json.dumps(blocked_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    blocked_result = _require_compile_api()(
        blocked_batch,
        cache=missing.cache,
        gateway=missing.gateway,
        query_fixture=None,
    )
    assert blocked_result.blocked_reasons == ("K1-run-not-complete",)
    assert json.loads(blocked_manifest_path.read_text(encoding="utf-8"))["navigation"]["blocked_reasons"] == [
        "K1-run-not-complete"
    ]


def test_cli_invokes_navigation_after_compile_cli_hook(tmp_path: Path, monkeypatch, capsys) -> None:
    import knowledge_digest.semantic_cli as semantic_cli
    import knowledge_digest.semantic_navigation as semantic_navigation

    items = tmp_path / "items"
    items.mkdir()
    batch = tmp_path / "compiled-batch"
    calls: list[tuple[Path, dict[str, object]]] = []

    class FakeBatchResult:
        output_dir = batch
        outcome = "completed"
        run_status = "complete"
        publish_status = "not_released"
        plan: dict[str, object] = {}
        provider_calls = 0
        cache_hits = 0

    def fake_compile(*args, **kwargs):
        return FakeBatchResult()

    def probe(batch_dir: Path, **kwargs):
        calls.append((Path(batch_dir), kwargs))
        return SimpleNamespace(
            as_dict=lambda: {
                "navigation_status": "generated_ok",
                "success_pages": 1,
                "blocked_sources": 0,
                "blocked_reasons": [],
                "nav_files": ["Home.md"],
            }
        )

    monkeypatch.setattr(semantic_cli, "compile_batch", fake_compile)
    monkeypatch.setattr(semantic_cli, "configured_provider_from_env", lambda: object())
    monkeypatch.setattr(
        semantic_cli,
        "build_navigation_dependencies",
        lambda **kwargs: SimpleNamespace(cache="cache", gateway="gateway", query_fixture="fixture"),
        raising=False,
    )
    monkeypatch.setattr(semantic_navigation, "compile_batch_navigation", probe)

    exit_code = semantic_cli.main([str(items)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][0] == batch
    assert set(calls[0][1]) == {"cache", "gateway", "query_fixture"}
    assert output["navigation"]["navigation_status"] == "generated_ok"


@pytest.mark.parametrize(
    ("outcome", "run_status", "expected_exit"),
    (("failed", "blocked", 3), ("cancelled", "interrupted", 4), ("unavailable", "blocked", 2)),
)
def test_cli_preserves_noncomplete_terminal_outcome_when_navigation_is_blocked(
    tmp_path: Path,
    monkeypatch,
    capsys,
    outcome: str,
    run_status: str,
    expected_exit: int,
) -> None:
    import knowledge_digest.semantic_cli as semantic_cli

    items = tmp_path / "items"
    items.mkdir()
    batch = tmp_path / "compiled-batch"

    class FakeBatchResult:
        output_dir = batch
        publish_status = "not_released"
        plan: dict[str, object] = {}
        provider_calls = 0
        cache_hits = 0

        def __init__(self) -> None:
            self.outcome = outcome
            self.run_status = run_status

    monkeypatch.setattr(semantic_cli, "compile_batch", lambda *args, **kwargs: FakeBatchResult())
    monkeypatch.setattr(semantic_cli, "configured_provider_from_env", lambda: object())

    exit_code = semantic_cli.main([str(items)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == expected_exit
    assert output["outcome"] == outcome


def test_reconcile_rejects_frontmatter_path_escape(tmp_path: Path) -> None:
    reconcile = _require_reconcile_api()
    batch = make_batch(tmp_path / "escape")
    page = batch / "products/GoInsight/authentication/login.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace('product: "GoInsight"', 'product: ".."'),
        encoding="utf-8",
    )
    with pytest.raises(NavigationInputError) as caught:
        reconcile(batch)
    assert caught.value.reason == "nav-frontmatter-path-invalid"


def test_navigation_rejects_symlinked_audit_parent(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    batch = make_batch(tmp_path / "audit-link")
    external = tmp_path / "external"
    external.mkdir()
    original_manifest = (batch / "_audit" / "page-manifest.json").read_bytes()
    shutil.rmtree(batch / "_audit")
    (batch / "_audit").symlink_to(external, target_is_directory=True)

    result = compile_navigation(
        batch,
        cache=_StringCache(),
        gateway=_SequenceGateway(_valid_model_outputs()),
        query_fixture=None,
    )

    assert result.navigation_status == "blocked"
    assert "batch-path-symlink" in result.blocked_reasons
    assert not (external / "page-manifest.json").exists()
    assert original_manifest != (batch / "_audit" / "page-manifest.json").read_bytes() if (batch / "_audit" / "page-manifest.json").exists() else True


def test_multipart_manifest_pages_are_all_navigable(tmp_path: Path) -> None:
    compile_navigation = _require_compile_api()
    batch = make_batch(tmp_path / "multipart")
    manifest_path = batch / "_audit" / "page-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first = manifest["pages"][0]
    part = batch / "products/GoInsight/authentication/login.part-002.md"
    part.write_bytes((batch / first["page_path"]).read_bytes())
    first["page_paths"].append("products/GoInsight/authentication/login.part-002.md")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = compile_navigation(
        batch,
        cache=_StringCache(),
        gateway=_SequenceGateway(_valid_model_outputs() + ["unused"]),
        query_fixture=None,
    )

    assert result.navigation_status == "generated_ok"
    assert result.success_pages == 4
    module = (batch / "products/GoInsight/authentication/Index.md").read_text(encoding="utf-8")
    assert "[[products/GoInsight/authentication/login.part-002|登录认证]]" in module


def test_invalid_model_output_is_not_cached(tmp_path: Path) -> None:
    resolve = _require_cached_output_api()
    cache = _StringCache()
    calls = {"count": 0}

    class Gateway:
        def __init__(self, value: str) -> None:
            self.value = value

        def complete(self, prompt: str) -> str:
            calls["count"] += 1
            return self.value

    with pytest.raises(NavigationInputError):
        resolve(
            cache=cache,
            gateway=Gateway(""),
            cache_key="task8-desc:poison",
            prompt="describe",
            validator=validate_model_output,
        )
    assert cache.values == {}

    assert resolve(
        cache=cache,
        gateway=Gateway("这页帮助你完成登录配置。"),
        cache_key="task8-desc:poison",
        prompt="describe",
        validator=validate_model_output,
    ) == "这页帮助你完成登录配置。"
    assert calls["count"] == 2
