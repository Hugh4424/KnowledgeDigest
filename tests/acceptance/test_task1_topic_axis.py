"""Task1 structural topic-axis contracts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

from knowledge_digest import kb_structure
from knowledge_digest.errors import ValidationError
from knowledge_digest.paths import validate_paths
from knowledge_digest.topic_axis import (
    affected_set,
    build_source_inventory,
    build_knowledge_type_registry,
    build_source_product_gazetteer,
    build_topic_plan,
    build_topic_examples,
    find_managed_conflicts,
    load_knowledge_type_registry,
    load_product_gazetteer,
    run_topic_axis,
    write_product_gazetteer,
    write_knowledge_type_registry,
    topic_index_from_plan,
    topic_key_v1,
    topic_key_v2,
)


GAZETTEER = {
    "schema_version": "1.0.0",
    "owner": "KnowledgeDigest maintainers",
    "match_order": ["canonical", "alias", "parent_path", "h1_title", "candidate"],
    "entries": [
        {"kind": "product", "canonical": "Atlas", "aliases": ["AT"], "object_intents": ["billing"], "owner": "team-a", "source_refs": ["fixture:1"], "status": "canonical", "reason": "controlled"},
        {"kind": "module", "canonical": "Checkout", "aliases": ["Pay"], "object_intents": ["billing"], "owner": "team-a", "source_refs": ["fixture:1"], "status": "canonical", "reason": "controlled"},
        {"kind": "product", "canonical": "Beacon", "aliases": [], "object_intents": ["export"], "owner": "team-b", "source_refs": ["fixture:2"], "status": "canonical", "reason": "controlled"},
        {"kind": "module", "canonical": "Reports", "aliases": [], "object_intents": ["export"], "owner": "team-b", "source_refs": ["fixture:2"], "status": "canonical", "reason": "controlled"},
        {"kind": "product", "canonical": "Candidate Product", "aliases": [], "object_intents": [], "owner": "", "source_refs": [], "status": "candidate", "reason": "needs confirmation"},
    ],
}

_REAL_SOURCE_PAGE_TYPES = {
    "GoInsight/12. GoInsight DC部署方案.md": "product_overview",
    "GoInsight/16 问数自动识别数据集.md": "module_or_capability",
    "GoInsight/17  智能搭建.md": "procedure_or_rule",
}


def _override_manifest_hash(rows: list[dict[str, object]]) -> str:
    payload = [
        {key: value for key, value in row.items() if key != "manifest_sha256"}
        for row in rows
    ]
    payload.sort(key=lambda row: (str(row.get("path")), str(row.get("override_ref"))))
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source_fixture(tmp_path: Path, *, count: int = 2, reverse: bool = False) -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    rows = []
    for index in range(count):
        name = f"topic-{index:02d}.md"
        extras = []
        if index % 2 == 0:
            extras.append("## FAQ\n\nQ: How?\nA: This is the answer.\n")
        if index % 3 == 0:
            extras.append("![diagram](assets/diagram.png)\n")
        if index % 4 == 0:
            extras.append("中文说明 / English description\n")
        if index % 5 == 0:
            extras.append("Version 1.2\n")
        if index % 7 == 0:
            extras.append("TODO draft noise marker\n")
        (items / name).write_text(
            f"# Billing {index}\n\n| key | value |\n| --- | --- |\n| v | v2 |\n\n{''.join(extras)}See [next](topic-{(index + 1) % count:02d}.md).\n",
            encoding="utf-8",
        )
        rows.append({"content_path": name, "source_uri": f"https://source.example/{index}", "knowledge_type": "products", "product": "Atlas", "module": "Checkout", "object_intent": "billing", "parent_path": "products/atlas/modules/checkout"})
    if reverse:
        rows.reverse()
    (new_dir / "sources.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    structure = (
        "---\nroots: [pages, _archive, _queues]\nwhy_field: why\nversion_field: version\n"
        "topic_axis_enabled: true\ntopic_axis_root: pages/topics\n---\n"
    )
    (kb_dir / "kb.structure.md").write_text(structure, encoding="utf-8")
    write_product_gazetteer(kb_dir / "kb.structure.md", GAZETTEER)
    return new_dir, kb_dir


def test_schema_topic_index_migration() -> None:
    legacy = {
        "schema_version": "1.0.0",
        "topics": [{"topic_id": "topic-old", "source_ids": ["source-a"], "category_id": "pending", "published_path": "pages/old.md", "product_slug": None}],
    }
    migrated = kb_structure.validate_topic_index(legacy)
    assert migrated["schema_version"] == "2.0.0"
    assert migrated["topics"][0]["digest_topic_id"] == "topic-old"
    assert migrated["topics"][0]["published_path"] is None
    assert migrated["topics"][0]["legacy_published_path"] == "pages/old.md"
    assert migrated["topics"][0]["old_path_mapping"][0]["relation"] == "unmappable"
    assert migrated["topics"][0]["status"] == "degraded"


def test_schema_rejects_degraded_empty_axis_and_duplicate_members() -> None:
    with pytest.raises(ValidationError, match="JSON null"):
        kb_structure.validate_topic_index(
            {"schema_version": "2.0.0", "topics": [{"topic_key": "degraded/x", "knowledge_type": "products", "product": "", "module": None, "object_intent": None, "source_members": ["source-a"], "published_path": None, "old_path_mapping": [], "status": "degraded", "topic_plan_version": "1.0.0", "reason": "unknown", "evidence_refs": [{"source_uri": "u"}]}]}
        )


def test_schema_rejects_duplicate_published_path() -> None:
    evidence = {"source_uri": "https://example/a", "content_fingerprint": "a" * 64, "line_number": 1}
    topic = {
        "topic_key": "v1/atlas/checkout/billing",
        "knowledge_type": "products",
        "product": "Atlas", "module": "Checkout", "object_intent": "billing",
        "source_members": ["source-a"], "published_path": "pages/topics/atlas/checkout/billing.md",
        "old_path_mapping": [], "status": "published", "topic_plan_version": "1.0.0", "reason": "",
        "evidence_refs": [evidence],
    }
    duplicate = {**topic, "topic_key": "v1/nova/checkout/billing", "product": "Nova", "source_members": ["source-b"]}
    with pytest.raises(ValidationError, match="published path is duplicated"):
        kb_structure.validate_topic_index({"schema_version": "2.0.0", "topics": [topic, duplicate]})


def test_inventory_and_link_edges(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)
    rows = build_source_inventory(new_dir)
    assert len(rows) == 2
    assert all(row["content_fingerprint"] for row in rows)
    assert all("table" in row["structure_features"] for row in rows)
    assert all(row["link_edges"][0]["target_source_uri"] for row in rows)
    assert rows[0]["link_edges"][0]["line_number"] > 0


def test_explicit_source_page_type_is_preserved_in_topic_authority(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=1)
    declaration = json.loads((new_dir / "sources.jsonl").read_text(encoding="utf-8"))
    declaration["page_type"] = "procedure_or_rule"
    (new_dir / "sources.jsonl").write_text(json.dumps(declaration) + "\n", encoding="utf-8")

    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    index = topic_index_from_plan(plan)

    assert plan["topics"][0]["page_type"] == "procedure_or_rule"
    assert index["topics"][0]["page_type"] == "procedure_or_rule"


def test_conflicting_explicit_page_types_fail_closed_for_merged_topic(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)
    declarations = [json.loads(line) for line in (new_dir / "sources.jsonl").read_text(encoding="utf-8").splitlines()]
    declarations[0]["page_type"] = "product_overview"
    declarations[1]["page_type"] = "procedure_or_rule"
    (new_dir / "sources.jsonl").write_text("".join(json.dumps(row) + "\n" for row in declarations), encoding="utf-8")

    inventory = build_source_inventory(new_dir)
    with pytest.raises(ValidationError, match="page_type metadata conflicts"):
        build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")


def test_inventory_uses_h1_not_an_earlier_h2(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=1)
    (new_dir / "items/topic-00.md").write_text("## Section noise\n\n# Stable H1\n\nBody\n", encoding="utf-8")

    rows = build_source_inventory(new_dir)

    assert rows[0]["h1"] == "Stable H1"


def test_knowledge_type_is_explicit_and_registry_is_not_companybrain_seeded(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)

    inventory = build_source_inventory(new_dir)
    registry = build_knowledge_type_registry(inventory)

    assert {row["knowledge_type"] for row in inventory} == {"products"}
    assert [entry["canonical"] for entry in registry["entries"]] == ["products"]
    entry = registry["entries"][0]
    assert entry["owner"]
    assert entry["source_refs"]
    assert entry["status"] == "canonical"
    assert not {"customers", "engineering", "operations", "principles", "product-boundaries"}.intersection(
        item["canonical"] for item in registry["entries"]
    )


def test_inventory_requires_explicit_knowledge_type(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=1)
    row = json.loads((new_dir / "sources.jsonl").read_text(encoding="utf-8"))
    row.pop("knowledge_type")
    (new_dir / "sources.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="knowledge_type"):
        build_source_inventory(new_dir)


def test_non_products_do_not_read_product_gazetteer(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=1)
    inventory = build_source_inventory(new_dir)
    non_product = dict(inventory[0], knowledge_type="engineering")
    plan = build_topic_plan([non_product], {"entries": "not-read"}, topic_root="pages/topics")

    topic = plan["topics"][0]
    assert topic["knowledge_type"] == "engineering"
    assert topic["status"] == "degraded"
    assert topic["product"] is None
    assert topic["module"] is None
    assert "ProductGazetteer" in topic["reason"]


def test_knowledge_type_registry_roundtrip_is_source_derived(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=2)
    registry = build_knowledge_type_registry(build_source_inventory(new_dir))
    write_knowledge_type_registry(kb_dir / "kb.structure.md", registry)

    loaded = load_knowledge_type_registry(kb_dir / "kb.structure.md")
    assert loaded == registry
    assert loaded["owner"] == "KnowledgeDigest source compiler"
    assert loaded["entries"][0]["source_refs"]


def test_current_topic_index_requires_knowledge_type() -> None:
    evidence = {"source_uri": "https://example/a", "content_fingerprint": "a" * 64, "line_number": 1}
    topic = {
        "topic_key": "v1/atlas/checkout/billing",
        "product": "Atlas", "module": "Checkout", "object_intent": "billing",
        "source_members": ["source-a"], "published_path": "pages/topics/atlas/checkout/billing.md",
        "old_path_mapping": [], "status": "published", "topic_plan_version": "1.0.0", "reason": "",
        "evidence_refs": [evidence],
    }

    with pytest.raises(ValidationError, match="knowledge_type"):
        kb_structure.validate_topic_index({"schema_version": "2.0.0", "topics": [topic]})


def test_inventory_link_edges_ignore_images_and_normalize_parent_links(tmp_path: Path) -> None:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    (items / "guide").mkdir(parents=True)
    (items / "guide/a.md").write_text("# A\n\n![diagram](images/diagram.png)\n\n[up](../b.md)\n", encoding="utf-8")
    (items / "b.md").write_text("# B\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        "".join(
            json.dumps(row) + "\n"
            for row in [
                {"content_path": "guide/a.md", "source_uri": "https://source.example/a", "knowledge_type": "products", "parent_path": "products/atlas", "product": "Atlas", "module": "Checkout", "object_intent": "billing"},
                {"content_path": "b.md", "source_uri": "https://source.example/b", "knowledge_type": "products", "parent_path": "products/atlas", "product": "Atlas", "module": "Checkout", "object_intent": "billing"},
            ]
        ),
        encoding="utf-8",
    )
    rows = build_source_inventory(new_dir)
    assert rows[0]["structure_features"]["image"] is True
    assert rows[0]["link_edges"] == [{"target_path": "b.md", "target_source_uri": "https://source.example/b", "line_number": 5}]


def test_inventory_ignores_host_relative_web_links(tmp_path: Path) -> None:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    (items / "a.md").write_text("# A\n\n[Confluence](/wiki/spaces/PROJECT/pages/14494340)\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "a.md", "source_uri": "https://source.example/a", "knowledge_type": "products"}) + "\n",
        encoding="utf-8",
    )
    assert build_source_inventory(new_dir)[0]["link_edges"] == []


def test_inventory_requires_declared_sources(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=1)
    (new_dir / "items" / "unlisted.md").write_text("# Missing\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="absent from sources"):
        build_source_inventory(new_dir)


def test_inventory_89_fixture_and_gazetteer_roundtrip(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "task1_topic_axis_89"
    copied = tmp_path / "task1_topic_axis_89"
    shutil.copytree(fixture, copied)
    new_dir, kb_dir = copied / "new_dir", copied / "kb_dir"
    inventory = build_source_inventory(new_dir, expected_count=89)
    assert len(inventory) == 89
    assert [row["source_uri"] for row in inventory] == sorted(row["source_uri"] for row in inventory)
    assert all(any(row["structure_features"][key] for row in inventory) for key in ("parent_child", "table", "faq", "image", "bilingual", "version", "noise"))

    write_product_gazetteer(kb_dir / "kb.structure.md", GAZETTEER)
    assert load_product_gazetteer(kb_dir / "kb.structure.md")["entries"] == sorted(
        GAZETTEER["entries"], key=lambda item: (item["kind"], item["canonical"].casefold())
    )
    paths = validate_paths(new_dir, kb_dir)
    report, _summary = run_topic_axis(paths, rebuild=True, run_id="run-gazetteer-roundtrip")
    record = json.loads(report.read_text(encoding="utf-8"))
    assert record["artifacts"]["topic_plan"] == "_digest/topic-plan.json"
    topic_plan = json.loads((kb_dir / record["artifacts"]["topic_plan"]).read_text(encoding="utf-8"))
    assert topic_plan["topics"][0]["status"] == "published"


def test_source_derived_gazetteer_is_source_canonical_and_traceable(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)
    inventory = build_source_inventory(new_dir)

    gazetteer = build_source_product_gazetteer(inventory)

    assert gazetteer["owner"] == "KnowledgeDigest source compiler"
    assert {entry["kind"] for entry in gazetteer["entries"]} == {"product", "module"}
    assert len([entry for entry in gazetteer["entries"] if entry["kind"] == "product"]) == 1
    assert len([entry for entry in gazetteer["entries"] if entry["kind"] == "module"]) == 1
    assert all(entry["status"] == "canonical" for entry in gazetteer["entries"])
    assert all("source-canonical" in entry["reason"] for entry in gazetteer["entries"])
    assert all(entry["source_refs"] for entry in gazetteer["entries"])
    assert all(
        ref["source_uri"] in {row["source_uri"] for row in inventory}
        for entry in gazetteer["entries"]
        for ref in entry["source_refs"]
    )
    assert not any("CompanyBrain" in json.dumps(entry, ensure_ascii=False) for entry in gazetteer["entries"])


def test_run_topic_axis_generates_missing_gazetteer(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=1)
    structure_path = kb_dir / "kb.structure.md"
    structure = structure_path.read_text(encoding="utf-8")
    structure_path.write_text(structure[: structure.index("<!-- KnowledgeDigest:ProductGazetteer -->")].rstrip() + "\n", encoding="utf-8")
    paths = validate_paths(new_dir, kb_dir)

    report, _summary = run_topic_axis(paths, rebuild=True, run_id="run-generated-gazetteer")

    persisted = load_product_gazetteer(structure_path)
    assert persisted["entries"]
    assert all(entry["status"] == "canonical" for entry in persisted["entries"])
    record = json.loads(report.read_text(encoding="utf-8"))
    assert record["gazetteer_generated"] is True
    assert record["gazetteer_entry_count"] == len(persisted["entries"])


def test_gazetteer_and_canonical_gate(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=1)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    assert plan["topics"][0]["status"] == "published"
    assert plan["topics"][0]["topic_key"] == "v2/products/atlas/checkout/billing"
    assert plan["topics"][0]["published_path"] == "pages/topics/products/atlas/checkout/billing.md"
    candidate = dict(inventory[0], source_meta={"product": "Candidate Product", "module": "Checkout", "object_intent": "billing"})
    degraded = build_topic_plan([candidate], GAZETTEER, topic_root="pages/topics")
    assert degraded["topics"][0]["status"] == "degraded"
    assert degraded["topics"][0]["product"] is None
    assert degraded["topics"][0]["published_path"] is None


def test_unknown_product_or_module_is_a_degraded_fact_not_a_runtime_error(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=1)
    inventory = build_source_inventory(new_dir)
    unknown = dict(inventory[0], source_meta={}, parent_path="products/unknown", title=None, h1=None)

    plan = build_topic_plan([unknown], GAZETTEER, topic_root="pages/topics")

    assert plan["topics"][0]["status"] == "degraded"
    assert plan["topics"][0]["single_source_checks"]["topic_axis_explicit"] is False

    # ProductGazetteer.object_intents is retained evidence, not a publish
    # whitelist.  A deterministic source seed may be published even when the
    # controlled entry has not listed that seed yet.
    unlisted_object = dict(inventory[0], source_meta={"product": "Atlas", "module": "Checkout", "object_intent": "settlement"})
    published = build_topic_plan([unlisted_object], GAZETTEER, topic_root="pages/topics")
    assert published["topics"][0]["status"] == "published"
    assert published["topics"][0]["object_intent"] == "settlement"

    conflict_gazetteer = {
        **GAZETTEER,
        "entries": [*GAZETTEER["entries"], {**GAZETTEER["entries"][0], "owner": "conflict-owner", "source_refs": ["fixture:conflict"]}],
    }
    conflict = build_topic_plan(inventory, conflict_gazetteer, topic_root="pages/topics")["topics"][0]
    assert conflict["status"] == "degraded"
    assert conflict["single_source_checks"]["fact_conflict_free"] is False


def test_single_source_predicates() -> None:
    assert topic_key_v1("Atlas", "Checkout", "billing") == "v1/atlas/checkout/billing"
    assert topic_key_v1("Atlas", "Checkout", "index") == "v1/atlas/checkout/x-index"


def test_identity_topic_key_v2_puts_knowledge_type_before_products_axis() -> None:
    assert topic_key_v2("products", "Atlas", "Checkout", "billing") == "v2/products/atlas/checkout/billing"


def test_reserved_escape_collision_degrades() -> None:
    with pytest.raises(ValidationError, match="ASCII"):
        topic_key_v1("Atlas", "Checkout", "index", reserved={"index", "x-index"})


def test_identity_and_slug() -> None:
    assert topic_key_v1("ATLAS", "Checkout", "Billing API") == "v1/atlas/checkout/billing-api"
    with pytest.raises(ValidationError, match="ASCII"):
        topic_key_v1("产品", "Checkout", "Billing")


def test_topic_key_and_path_collisions_fail_closed(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)
    inventory = build_source_inventory(new_dir)
    collision_gazetteer = {
        **GAZETTEER,
        "entries": [
            *GAZETTEER["entries"],
            {"kind": "product", "canonical": "index", "aliases": [], "object_intents": ["billing"], "owner": "team-b", "source_refs": ["fixture:a"], "status": "canonical", "reason": "controlled"},
            {"kind": "product", "canonical": "x-index", "aliases": [], "object_intents": ["billing"], "owner": "team-c", "source_refs": ["fixture:b"], "status": "canonical", "reason": "controlled"},
        ],
    }
    collision_inventory = [
        dict(inventory[0], parent_path="products/index-a", source_meta={**inventory[0]["source_meta"], "product": "index"}),
        dict(inventory[1], parent_path="products/x-index-b", source_meta={**inventory[1]["source_meta"], "product": "x-index"}),
    ]
    with pytest.raises(ValidationError, match="PUBLISHED_PATH_COLLISION"):
        build_topic_plan(collision_inventory, collision_gazetteer, topic_root="pages/topics")

    degraded_inventory = [
        dict(inventory[0], source_id="source-a", parent_path="unmapped", source_meta={}),
        dict(inventory[0], source_id="source-b", parent_path="unmapped", source_meta={}),
    ]
    with pytest.raises(ValidationError, match="DEGRADED_KEY_COLLISION"):
        build_topic_plan(degraded_inventory, GAZETTEER, topic_root="pages/topics")

    same_parent_inventory = [
        dict(inventory[0], source_id="source-a", content_path="products/same/中文一.md", parent_path="products/same", source_meta={}),
        dict(inventory[1], source_id="source-b", content_path="products/same/中文二.md", parent_path="products/same", source_meta={}),
    ]
    same_parent_plan = build_topic_plan(same_parent_inventory, GAZETTEER, topic_root="pages/topics")
    assert len(same_parent_plan["topics"]) == 2
    assert same_parent_plan["topics"][0]["topic_key"] != same_parent_plan["topics"][1]["topic_key"]


def test_reserved_escape_collision_fails_closed() -> None:
    gazetteer = {
        **GAZETTEER,
        "entries": [
            *GAZETTEER["entries"],
            {"kind": "product", "canonical": "index", "aliases": [], "object_intents": ["billing"], "owner": "team-index", "source_refs": ["fixture:index"], "status": "canonical", "reason": "controlled"},
            {"kind": "product", "canonical": "x-index", "aliases": [], "object_intents": ["billing"], "owner": "team-x-index", "source_refs": ["fixture:x-index"], "status": "canonical", "reason": "controlled"},
        ],
    }
    base = {
        "source_uri": "https://source.example/",
        "content_path": "source.md",
        "content_fingerprint": "a" * 64,
        "knowledge_type": "products",
        "title": "Billing",
        "h1": "Billing",
        "validation_status": "passed",
        "structure_features": {"parent_child": True, "table": False, "faq": False, "image": False, "bilingual": False, "version": False, "noise": False},
        "link_edges": [],
        "evidence_refs": [{"source_uri": "https://source.example/", "content_fingerprint": "a" * 64, "line_number": 1}],
        "source_meta": {"module": "Checkout", "object_intent": "billing"},
    }
    inventory = [
        {**base, "source_id": "source-index", "source_uri": "https://source.example/index", "parent_path": "products/index", "evidence_refs": [{"source_uri": "https://source.example/index", "content_fingerprint": "a" * 64, "line_number": 1}], "source_meta": {**base["source_meta"], "product": "index"}},
        {**base, "source_id": "source-x-index", "source_uri": "https://source.example/x-index", "parent_path": "products/x-index", "evidence_refs": [{"source_uri": "https://source.example/x-index", "content_fingerprint": "a" * 64, "line_number": 1}], "source_meta": {**base["source_meta"], "product": "x-index"}},
    ]
    with pytest.raises(ValidationError, match="PUBLISHED_PATH_COLLISION"):
        build_topic_plan(inventory, gazetteer, topic_root="pages/topics")


def test_declared_reader_root_is_reserved_for_topic_axis() -> None:
    base = {
        "source_uri": "https://source.example/",
        "content_path": "source.md",
        "content_fingerprint": "a" * 64,
        "knowledge_type": "products",
        "title": "Billing",
        "h1": "Billing",
        "validation_status": "passed",
        "structure_features": {"parent_child": True, "table": False, "faq": False, "image": False, "bilingual": False, "version": False, "noise": False},
        "link_edges": [],
        "evidence_refs": [{"source_uri": "https://source.example/", "content_fingerprint": "a" * 64, "line_number": 1}],
        "source_meta": {"module": "Checkout", "object_intent": "billing"},
    }
    inventory = [
        {**base, "source_id": "source-pages", "source_uri": "https://source.example/pages", "parent_path": "products/pages", "evidence_refs": [{"source_uri": "https://source.example/pages", "content_fingerprint": "a" * 64, "line_number": 1}], "source_meta": {**base["source_meta"], "product": "pages"}},
        {**base, "source_id": "source-x-pages", "source_uri": "https://source.example/x-pages", "parent_path": "products/x-pages", "evidence_refs": [{"source_uri": "https://source.example/x-pages", "content_fingerprint": "a" * 64, "line_number": 1}], "source_meta": {**base["source_meta"], "product": "x-pages"}},
    ]
    gazetteer = {
        **GAZETTEER,
        "entries": [
            *GAZETTEER["entries"],
            {"kind": "product", "canonical": "pages", "aliases": [], "object_intents": ["billing"], "owner": "team-pages", "source_refs": ["fixture:pages"], "status": "canonical", "reason": "controlled"},
            {"kind": "product", "canonical": "x-pages", "aliases": [], "object_intents": ["billing"], "owner": "team-x-pages", "source_refs": ["fixture:x-pages"], "status": "canonical", "reason": "controlled"},
        ],
    }
    with pytest.raises(ValidationError, match="PUBLISHED_PATH_COLLISION"):
        build_topic_plan(inventory, gazetteer, topic_root="pages/topics", reserved={"pages"})


def test_topic_plan_and_object_intent() -> None:
    inventory = [{
        "source_id": "source-a", "source_uri": "https://example/a", "content_path": "a.md", "content_fingerprint": "a" * 64, "knowledge_type": "products",
            "title": "Billing", "h1": "Billing", "parent_path": "products/atlas", "validation_status": "passed",
            "structure_features": {"parent_child": True, "table": False, "faq": False, "image": False, "bilingual": False, "version": False, "noise": False},
        "link_edges": [], "evidence_refs": [{"source_uri": "https://example/a", "content_fingerprint": "a" * 64, "line_number": 1}],
        "source_meta": {"product": "Atlas", "module": "Checkout", "object_intent": "billing"},
    }]
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    assert plan["provider_boundary"] == "before_provider"
    assert plan["topics"][0]["source_members"] == ["source-a"]
    assert plan["topics"][0]["single_source_checks"]["fact_conflict_free"]


def test_single_source_required_fields_fail_closed() -> None:
    inventory = [{
        "source_id": "source-a", "source_uri": "https://example/a", "content_path": "a.md", "content_fingerprint": "a" * 64,
        "knowledge_type": "products",
        "title": "Billing", "h1": "Billing", "parent_path": "products/atlas", "validation_status": "passed",
        "structure_features": {"parent_child": True, "table": True, "faq": False, "image": False, "bilingual": False, "version": False, "noise": False},
        "link_edges": [], "evidence_refs": [{"source_uri": "https://example/a", "content_fingerprint": "a" * 64, "line_number": 1}],
        "source_meta": {"product": "Atlas", "module": "Checkout", "object_intent": "billing"},
    }]
    incomplete = dict(inventory[0], parent_path=None)
    missing_evidence = dict(inventory[0], evidence_refs=[{"content_fingerprint": "a" * 64}])
    incomplete_topic = build_topic_plan([incomplete], GAZETTEER, topic_root="pages/topics")["topics"][0]
    missing_evidence_topic = build_topic_plan([missing_evidence], GAZETTEER, topic_root="pages/topics")["topics"][0]
    assert incomplete_topic["status"] == "degraded"
    assert incomplete_topic["single_source_checks"]["资料完整"] is False
    assert missing_evidence_topic["status"] == "degraded"
    assert missing_evidence_topic["single_source_checks"]["required_evidence"] is False

    missing_seed = dict(inventory[0], source_meta={"product": "Atlas", "module": "Checkout"}, title=None, h1=None, parent_path=None)
    missing_seed_topic = build_topic_plan([missing_seed], GAZETTEER, topic_root="pages/topics")["topics"][0]
    assert missing_seed_topic["status"] == "degraded"
    assert missing_seed_topic["single_source_checks"]["fact_conflict_free"] is True


def test_topic_index_and_old_path_mapping() -> None:
    inventory = [{
        "source_id": "source-a", "source_uri": "https://example/a", "content_path": "a.md", "content_fingerprint": "a" * 64, "knowledge_type": "products",
        "title": "Billing", "h1": "Billing", "parent_path": "products/atlas", "validation_status": "passed",
        "structure_features": {"parent_child": True, "table": False, "faq": False, "image": False, "bilingual": False, "version": False, "noise": False},
        "link_edges": [], "evidence_refs": [{"source_uri": "https://example/a", "content_fingerprint": "a" * 64, "line_number": 1}],
        "source_meta": {"product": "Atlas", "module": "Checkout", "object_intent": "billing"},
    }]
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    index = topic_index_from_plan(plan, old_topic_index={"topics": [{"topic_id": "topic-old", "topic_key": "v1/atlas/checkout/billing", "published_path": "pages/legacy/billing.md", "source_ids": ["source-a"]}]})
    assert index["topics"][0]["digest_topic_id"] == "topic-old"
    assert index["topics"][0]["topic_key"] == "v2/products/atlas/checkout/billing"
    assert index["topics"][0]["old_path_mapping"][0]["relation"] == "rename"

    same_path = topic_index_from_plan(plan, old_topic_index={"topics": [{
        "digest_topic_id": "legacy-id",
        "topic_key": "legacy-topic-key",
        "published_path": plan["topics"][0]["published_path"],
        "source_ids": ["source-a"],
    }]})
    assert same_path["topics"][0]["digest_topic_id"] == "legacy-id"
    assert same_path["topics"][0]["old_path_mapping"] == []


def test_topic_index_merge_and_split_mapping() -> None:
    inventory = [{
        "source_id": "source-a", "source_uri": "https://example/a", "content_path": "a.md", "content_fingerprint": "a" * 64,
        "knowledge_type": "products",
        "title": "Billing", "h1": "Billing", "parent_path": "products/atlas", "validation_status": "passed",
        "structure_features": {"parent_child": True, "table": True, "faq": False, "image": False, "bilingual": False, "version": False, "noise": False},
        "link_edges": [], "evidence_refs": [{"source_uri": "https://example/a", "content_fingerprint": "a" * 64, "line_number": 1}],
        "source_meta": {"product": "Atlas", "module": "Checkout", "object_intent": "billing"},
    }, {
        "source_id": "source-b", "source_uri": "https://example/b", "content_path": "b.md", "content_fingerprint": "b" * 64,
        "knowledge_type": "products",
        "title": "Billing", "h1": "Billing", "parent_path": "products/atlas", "validation_status": "passed",
        "structure_features": {"parent_child": True, "table": True, "faq": False, "image": False, "bilingual": False, "version": False, "noise": False},
        "link_edges": [], "evidence_refs": [{"source_uri": "https://example/b", "content_fingerprint": "b" * 64, "line_number": 1}],
        "source_meta": {"product": "Atlas", "module": "Checkout", "object_intent": "billing"},
    }]
    merged_plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    merged_index = topic_index_from_plan(merged_plan, old_topic_index={"topics": [
        {"topic_id": "old-a", "published_path": "pages/old-a.md", "source_ids": ["source-a"]},
        {"topic_id": "old-b", "published_path": "pages/old-b.md", "source_ids": ["source-b"]},
    ]})
    assert {mapping["relation"] for mapping in merged_index["topics"][0]["old_path_mapping"]} == {"merge"}

    split_gazetteer = {**GAZETTEER, "entries": [
        *GAZETTEER["entries"],
        {"kind": "product", "canonical": "Nova", "aliases": [], "object_intents": ["billing"], "owner": "team-n", "source_refs": ["fixture:n"], "status": "canonical", "reason": "controlled"},
    ]}
    split_inventory = [inventory[0], dict(inventory[1], source_meta={**inventory[1]["source_meta"], "product": "Nova"})]
    split_plan = build_topic_plan(split_inventory, split_gazetteer, topic_root="pages/topics")
    split_index = topic_index_from_plan(split_plan, old_topic_index={"topics": [{
        "topic_id": "old", "published_path": "pages/legacy.md", "source_ids": ["source-a", "source-b"]
    }]})
    assert len(split_index["topics"]) == 2
    assert all(mapping["relation"] == "split" for topic in split_index["topics"] for mapping in topic["old_path_mapping"])


def test_batch_invariance(tmp_path: Path) -> None:
    first_dir, _kb = _source_fixture(tmp_path / "a", count=3)
    second_dir, _kb2 = _source_fixture(tmp_path / "b", count=3, reverse=True)
    inventory = build_source_inventory(first_dir)
    reordered = build_source_inventory(second_dir)
    old_topic_index = {"topics": [{
        "topic_id": "topic-locked",
        "published_path": "pages/topics/products/atlas/checkout/billing.md",
        "source_ids": [row["source_id"] for row in inventory],
    }]}

    def snapshot(batch_size: int, rows: list[dict[str, object]]) -> dict[str, object]:
        # Task1 deliberately plans the fixed manifest before transport.  The
        # batch size is recorded here as the transport input, but cannot enter
        # the pure planner or change its TopicIndex projection.
        assert batch_size in {1, 20}
        plan = build_topic_plan(rows, GAZETTEER, topic_root="pages/topics")
        return {"topic_plan": plan, "topic_index": topic_index_from_plan(plan, old_topic_index=old_topic_index)}

    snapshots = [snapshot(1, inventory), snapshot(20, inventory), snapshot(20, reordered), snapshot(1, inventory)]
    canonical = [json.dumps(value, ensure_ascii=False, sort_keys=True) for value in snapshots]
    assert len(set(canonical)) == 1
    assert snapshots[0]["topic_index"]["topics"][0]["old_path_mapping"] == []


def test_affected_set_and_rebuild(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    empty = affected_set(inventory, plan, previous_inventory=inventory, previous_plan=plan)
    assert empty["empty"]
    rebuilt = affected_set(inventory, plan, rebuild=True)
    assert rebuilt["affected_source_ids"]
    assert set(rebuilt["affected_topic_keys"]) == {plan["topics"][0]["topic_key"]}


def test_affected_set_includes_removed_links_and_gazetteer_match_changes(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    changed_plan = json.loads(json.dumps(plan))
    changed_plan["matches"][0]["product"]["owner"] = "new-owner"
    changed = affected_set(inventory, changed_plan, previous_inventory=inventory, previous_plan=plan)
    assert inventory[0]["source_id"] in changed["affected_source_ids"]
    assert plan["topics"][0]["topic_key"] in changed["affected_topic_keys"]

    current_inventory = [inventory[0]]
    current_plan = build_topic_plan(current_inventory, GAZETTEER, topic_root="pages/topics")
    removed = affected_set(current_inventory, current_plan, previous_inventory=inventory, previous_plan=plan)
    assert inventory[0]["source_id"] in removed["related_source_ids"]
    assert plan["topics"][0]["topic_key"] in removed["affected_topic_keys"]

    deleted_link_inventory = [dict(inventory[0], link_edges=[])]
    deleted_link_plan = build_topic_plan(deleted_link_inventory, GAZETTEER, topic_root="pages/topics")
    deleted_link = affected_set(deleted_link_inventory, deleted_link_plan, previous_inventory=inventory, previous_plan=plan)
    assert inventory[0]["source_id"] in deleted_link["related_source_ids"]

    current_index = topic_index_from_plan(plan, old_topic_index={"topics": [{
        "topic_id": "old", "published_path": "pages/old.md", "source_ids": [row["source_id"] for row in inventory]
    }]})
    previous_index = topic_index_from_plan(plan, old_topic_index={"topics": [{
        "topic_id": "old", "published_path": "pages/older.md", "source_ids": [row["source_id"] for row in inventory]
    }]})
    mapping_changed = affected_set(inventory, plan, previous_inventory=inventory, previous_plan=plan, current_index=current_index, previous_index=previous_index)
    assert plan["topics"][0]["topic_key"] in mapping_changed["affected_topic_keys"]


def test_affected_set_includes_metadata_only_topic_changes(tmp_path: Path) -> None:
    new_dir, _kb_dir = _source_fixture(tmp_path, count=2)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    changed_plan = json.loads(json.dumps(plan))
    changed_plan["topics"][0]["reason"] = "metadata-only plan revision"
    changed = affected_set(inventory, changed_plan, previous_inventory=inventory, previous_plan=plan)
    topic_key = plan["topics"][0]["topic_key"]
    assert topic_key in changed["affected_topic_keys"]
    assert set(plan["topics"][0]["source_members"]).issubset(changed["affected_source_ids"])


def test_task1_opt_in_rejects_legacy_batch_write(tmp_path: Path) -> None:
    from knowledge_digest.batch_run import run_batched
    from knowledge_digest.config import DigestSettings

    new_dir, kb_dir = _source_fixture(tmp_path, count=2)
    paths = validate_paths(new_dir, kb_dir)
    with pytest.raises(ValidationError, match="batch mode is not supported"):
        run_batched(paths, DigestSettings(), batch_size=1, state_path=tmp_path / "batch-state.json")


def test_managed_conflict_and_override(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=1)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    path = kb_dir / plan["topics"][0]["published_path"]
    path.parent.mkdir(parents=True)
    path.write_text("---\nmanaged_content_hash: " + "0" * 64 + "\n---\nmanual\n", encoding="utf-8")
    conflicts = find_managed_conflicts(kb_dir, plan, run_id="run-1")
    assert conflicts[0]["code"] == "MANAGED_CONTENT_CONFLICT"
    actual = hashlib.sha256(b"manual\n").hexdigest()
    override = {"topic_key": plan["topics"][0]["topic_key"], "path": plan["topics"][0]["published_path"], "managed_content_hash": "0" * 64, "actual_content_hash": actual, "operator_note": "reconcile", "reason": "approved", "override_ref": "ref-1"}
    invalid_manifest_override = {**override, "manifest_sha256": "0" * 64}
    assert find_managed_conflicts(kb_dir, plan, run_id="run-1", override_manifest=[invalid_manifest_override])[0]["code"] == "MANAGED_CONTENT_CONFLICT"
    override["manifest_sha256"] = _override_manifest_hash([override])
    assert find_managed_conflicts(kb_dir, plan, run_id="run-1", override_manifest=[override])[0]["code"] == "MANAGED_CONTENT_OVERRIDE"


def test_managed_page_with_matching_hash_is_not_a_conflict(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=1)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    path = kb_dir / plan["topics"][0]["published_path"]
    path.parent.mkdir(parents=True)
    body = b"managed page\n"
    path.write_bytes(b"---\nmanaged_content_hash: " + hashlib.sha256(body).hexdigest().encode() + b"\n---\n" + body)
    assert find_managed_conflicts(kb_dir, plan, run_id="run-matching-hash") == []


def test_managed_page_without_hash_is_not_silently_skipped(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=1)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    path = kb_dir / plan["topics"][0]["published_path"]
    path.parent.mkdir(parents=True)
    path.write_text("---\nmanaged_by: KnowledgeDigest\n---\nmanual\n", encoding="utf-8")
    conflicts = find_managed_conflicts(kb_dir, plan, run_id="run-missing-hash")
    assert conflicts[0]["code"] == "MANAGED_CONTENT_CONFLICT"
    assert conflicts[0]["reason"] == "existing published path has no valid managed content hash"


def test_unmanaged_existing_page_is_not_silently_skipped(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=1)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    path = kb_dir / plan["topics"][0]["published_path"]
    path.parent.mkdir(parents=True)
    path.write_text("# human page\n", encoding="utf-8")
    conflicts = find_managed_conflicts(kb_dir, plan, run_id="run-unmanaged-page")
    assert conflicts[0]["code"] == "MANAGED_CONTENT_CONFLICT"
    assert conflicts[0]["managed_content_hash"] is None


def test_run_records_conflict_and_explicit_override(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=1)
    paths = validate_paths(new_dir, kb_dir)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    path = kb_dir / plan["topics"][0]["published_path"]
    path.parent.mkdir(parents=True)
    path.write_text("---\nmanaged_content_hash: " + "0" * 64 + "\n---\nmanual\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="MANAGED_CONTENT_CONFLICT"):
        run_topic_axis(paths, run_id="run-conflict")
    conflict_record = json.loads((kb_dir / "_digest/runs/run-conflict.json").read_text(encoding="utf-8"))
    assert conflict_record["conflicts"][0]["action"] == "preserve_and_stop"
    actual = hashlib.sha256(b"manual\n").hexdigest()
    override = {"topic_key": plan["topics"][0]["topic_key"], "path": plan["topics"][0]["published_path"], "managed_content_hash": "0" * 64, "actual_content_hash": actual, "operator_note": "reconcile", "reason": "approved", "override_ref": "ref-2"}
    override["manifest_sha256"] = _override_manifest_hash([override])
    report, _summary = run_topic_axis(paths, run_id="run-override", override_manifest=[override])
    override_record = json.loads(report.read_text(encoding="utf-8"))
    assert override_record["conflicts"][0]["code"] == "MANAGED_CONTENT_OVERRIDE"


def test_declared_override_manifest_is_used_by_task1_entrypoint(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=1)
    structure_path = kb_dir / "kb.structure.md"
    structure_path.write_text(structure_path.read_text(encoding="utf-8") + "topic_axis_override_manifest: _digest/override-manifest.json\n", encoding="utf-8")
    paths = validate_paths(new_dir, kb_dir)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    path = kb_dir / plan["topics"][0]["published_path"]
    path.parent.mkdir(parents=True)
    path.write_text("---\nmanaged_content_hash: " + "0" * 64 + "\n---\nmanual\n", encoding="utf-8")
    actual = hashlib.sha256(b"manual\n").hexdigest()
    manifest = [{"topic_key": plan["topics"][0]["topic_key"], "path": plan["topics"][0]["published_path"], "managed_content_hash": "0" * 64, "actual_content_hash": actual, "operator_note": "reconcile", "reason": "approved", "override_ref": "declared-ref"}]
    manifest[0]["manifest_sha256"] = _override_manifest_hash(manifest)
    manifest_path = kb_dir / "_digest/override-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report, _summary = run_topic_axis(paths, run_id="run-declared-override")
    record = json.loads(report.read_text(encoding="utf-8"))
    assert record["conflicts"][0]["code"] == "MANAGED_CONTENT_OVERRIDE"


def test_run_topic_axis_reuses_previous_plan_for_empty_affected_set(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=2)
    paths = validate_paths(new_dir, kb_dir)
    run_topic_axis(paths, rebuild=True, run_id="run-first")
    report, _summary = run_topic_axis(paths, run_id="run-repeat")
    record = json.loads(report.read_text(encoding="utf-8"))
    assert record["affected_set"]["empty"] is True


def test_offline_and_audit_outputs(tmp_path: Path) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=2)
    paths = validate_paths(new_dir, kb_dir)
    report, summary = run_topic_axis(paths, rebuild=True, run_id="run-task1")
    assert report == kb_dir / "_digest/runs/run-task1.json"
    assert "not_released" in summary
    assert (kb_dir / "_digest/source-inventory.jsonl").is_file()
    assert (kb_dir / "_digest/topic-plan.json").is_file()
    assert (kb_dir / "_digest/topic-index.json").is_file()
    assert not (kb_dir / "Home.md").exists()
    record = json.loads(report.read_text(encoding="utf-8"))
    assert record["reader_package_changed"] is False
    for key, relative in record["artifacts"].items():
        assert record["artifact_sha256"][key] == hashlib.sha256((kb_dir / relative).read_bytes()).hexdigest()


def test_real_corpus_isolation_and_delivery_boundary(tmp_path: Path) -> None:
    raw_root_value = os.environ.get("KNOWLEDGEDIGEST_TASK1_RAW_CORPUS")
    if not raw_root_value:
        pytest.skip("set KNOWLEDGEDIGEST_TASK1_RAW_CORPUS to run the external 89-source corpus check")
    raw_root = Path(raw_root_value)
    assert raw_root.is_dir()
    new_dir = tmp_path / "new"
    items_dir = new_dir / "items"
    items_dir.mkdir(parents=True)
    declarations = []
    for raw_path in sorted(raw_root.rglob("*.md"), key=lambda path: path.relative_to(raw_root).as_posix()):
        relative = raw_path.relative_to(raw_root)
        content_path = Path("products") / relative
        target = items_dir / content_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raw_path, target)
        declarations.append(
            {
                "content_path": content_path.as_posix(),
                "source_uri": f"raw://confluence/{relative.as_posix()}",
                "knowledge_type": "products",
                **({"page_type": _REAL_SOURCE_PAGE_TYPES[relative.as_posix()]} if relative.as_posix() in _REAL_SOURCE_PAGE_TYPES else {}),
            }
        )
    (new_dir / "sources.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in declarations),
        encoding="utf-8",
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(
        "---\nroots: [pages, _archive, _queues]\nwhy_field: why\nversion_field: version\n"
        "topic_axis_enabled: true\ntopic_axis_root: pages/topics\n---\n",
        encoding="utf-8",
    )
    home = kb_dir / "Home.md"
    home.write_text("# Existing reader home\n\nDo not rewrite me.\n", encoding="utf-8")
    existing_page = kb_dir / "pages" / "existing.md"
    existing_page.parent.mkdir()
    existing_page.write_text("# Existing reader page\n", encoding="utf-8")
    reader_before = {path: path.read_bytes() for path in (home, existing_page)}

    paths = validate_paths(new_dir, kb_dir)
    report_path, summary = run_topic_axis(paths, rebuild=True, run_id="run-real-corpus")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["source_count"] == 89
    assert "not_released" in summary
    assert report["reader_package_changed"] is False
    assert 12 <= len(report["examples"]) <= 20
    assert (kb_dir / "_digest/source-inventory.jsonl").is_file()
    assert (kb_dir / "_digest/topic-plan.json").is_file()
    assert (kb_dir / "_digest/topic-index.json").is_file()
    assert report_path.is_file()
    topic_index = json.loads((kb_dir / "_digest/topic-index.json").read_text(encoding="utf-8"))
    assert {
        row["page_type"]
        for row in topic_index["topics"]
        if row.get("page_type")
    } == {"product_overview", "module_or_capability", "procedure_or_rule"}
    gazetteer = load_product_gazetteer(kb_dir / "kb.structure.md")
    assert gazetteer["entries"]
    assert all(entry["status"] == "canonical" for entry in gazetteer["entries"])
    assert len([entry for entry in gazetteer["entries"] if entry["kind"] == "product"]) == 4
    assert len([entry for entry in gazetteer["entries"] if entry["kind"] == "module"]) == 89
    assert all(entry["source_refs"] for entry in gazetteer["entries"])
    assert "CompanyBrain" not in (kb_dir / "_digest/topic-plan.json").read_text(encoding="utf-8")
    assert {path: path.read_bytes() for path in reader_before} == reader_before


def test_offline_topic_axis_makes_no_network_calls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    new_dir, kb_dir = _source_fixture(tmp_path, count=2)
    paths = validate_paths(new_dir, kb_dir)

    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Task1 offline path attempted a network call")

    monkeypatch.setattr(socket.socket, "connect", fail_network)
    monkeypatch.setattr(socket, "create_connection", fail_network)
    run_topic_axis(paths, rebuild=True, run_id="run-zero-network")


def test_cli_offline_fixture_runs_structural_task1(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "task1_topic_axis_89"
    copied = tmp_path / "task1_topic_axis_89"
    shutil.copytree(fixture, copied)
    result = subprocess.run(
        ["uv", "run", "--frozen", "digest", str(copied / "new_dir"), str(copied / "kb_dir"), "--config", str(copied / "offline.json"), "--no-llm"],
        cwd=Path(__file__).parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "not_released" in result.stdout
    assert not (copied / "kb_dir" / "Home.md").exists()


def test_examples_and_failure_matrix(tmp_path: Path) -> None:
    new_dir, _kb = _source_fixture(tmp_path, count=12)
    inventory = build_source_inventory(new_dir)
    plan = build_topic_plan(inventory, GAZETTEER, topic_root="pages/topics")
    examples = build_topic_examples(inventory, GAZETTEER, topic_root="pages/topics", include_failure_matrix=True)
    assert 12 <= len(examples) <= 20
    kinds = {example["kind"] for example in examples}
    assert {"normal_merge", "unknown", "conflict_degraded"} <= kinds
    unknown = build_topic_plan([dict(inventory[0], source_meta={}, parent_path="products/unknown", title=None, h1=None)], GAZETTEER, topic_root="pages/topics")["topics"][0]
    assert unknown["status"] == "degraded"
    failures = {example["failed_check"] for example in examples if example["kind"] == "single_source_failure"}
    assert {"资料完整", "topic_axis_explicit", "meaningful_structure", "required_evidence", "fact_conflict_free"} <= failures
    assert all(example["topic"]["single_source_checks"][example["failed_check"]] is False for example in examples if example["kind"] == "single_source_failure")
    assert all(example["evidence_refs"] for example in examples)
    assert all(
        {"source_uri", "content_fingerprint", "line_number"} <= set(ref)
        for example in examples
        for ref in example["evidence_refs"]
    )

    readable_noise = dict(
        inventory[0],
        title="Readable title",
        h1=None,
        parent_path=None,
        structure_features={key: (key == "noise") for key in ("parent_child", "table", "faq", "image", "bilingual", "version", "noise")},
    )
    readable_noise_topic = build_topic_plan([readable_noise], GAZETTEER, topic_root="pages/topics")["topics"][0]
    assert readable_noise_topic["single_source_checks"]["meaningful_structure"] is True

    production_examples = build_topic_examples(inventory, GAZETTEER, topic_root="pages/topics", include_failure_matrix=False)
    assert not any(example["kind"] == "single_source_failure" for example in production_examples)


def test_degraded_key_uses_first_ascii_evidence_in_spec_order() -> None:
    row = {
        "source_id": "source-degraded",
        "source_uri": "https://source.example/fallback-page",
        "content_path": "fallback.md",
        "content_fingerprint": "a" * 64,
        "knowledge_type": "products",
        "title": "English Fallback",
        "h1": "中文标题",
        "parent_path": None,
        "structure_features": {"parent_child": False, "noise": False},
        "link_edges": [],
        "evidence_refs": [{"source_uri": "https://source.example/fallback-page", "content_fingerprint": "a" * 64, "line_number": 1}],
        "source_meta": {},
    }
    topic = build_topic_plan([row], GAZETTEER, topic_root="pages/topics")["topics"][0]
    assert topic["status"] == "degraded"
    assert topic["topic_key"] == "degraded/english-fallback"
