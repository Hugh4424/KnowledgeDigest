from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest
import knowledge_digest.reader_bundle as reader_bundle_module

from knowledge_digest.reader_bundle import (
    ArtifactRef,
    BundleArtifactPaths,
    ReaderBundleInputs,
    ReaderBundleStructureInputs,
    derive_reader_signals,
    project_reader_bundle,
    validate_reader_bundle,
)
from knowledge_digest.reader_quality import (
    build_reader_snapshot,
    derive_task2c_questions,
    run_reader_quality_gate,
    _manifest_pages,
    _invoke_agent,
    _reachable_reader_paths,
    _scorecard_content_hash,
)
from knowledge_digest.reader_frontmatter import parse_concept_document


FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "task2a_reader_bundle"
TASK2C_FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "task2c_reader_quality"
PROJECT_ROOT = Path(__file__).parents[2]


def _copy_structural_inputs(root: Path) -> None:
    root.mkdir(parents=True)
    for name in ("topic-index.json", "source-inventory.jsonl"):
        (root / name).write_bytes((FIXTURE_ROOT / name).read_bytes())


def _ref(root: Path, name: str, kind: str, schema: str, version: str) -> ArtifactRef:
    import hashlib

    data = (root / name).read_bytes()
    return ArtifactRef(kind, name, f"fixture-{name}", hashlib.sha256(data).hexdigest(), schema, version)


def _inputs(tmp_path: Path) -> ReaderBundleStructureInputs:
    root = tmp_path / "inputs"
    _copy_structural_inputs(root)
    return ReaderBundleStructureInputs(
        schema_version="reader-bundle-structure-inputs.v1",
        input_root=root,
        topic_index_ref=_ref(root, "topic-index.json", "topic-index", "2.0.0", "2.0.0"),
        source_inventory_ref=_ref(root, "source-inventory.jsonl", "source-inventory", "task1-real-corpus-verification.v1", "2026-08-06"),
        entry_manifest_refs=(),
        offline_mode="no-llm",
    )


def _full_inputs(tmp_path: Path) -> ReaderBundleInputs:
    root = tmp_path / "full-inputs"
    root.mkdir(parents=True)
    for name in ("topic-index.json", "source-inventory.jsonl", "claim-history.jsonl", "fixture-selection.json", "product-overview.md", "module-capability.md", "procedure-rule.md"):
        source = TASK2C_FIXTURE_ROOT / name
        destination = root / name
        destination.write_bytes(source.read_bytes())
    fixture_dir = root / "coverage-fixtures"
    fixture_dir.mkdir()
    for name in ("multi-source.json", "failed-degraded.json", "long-document.json", "long-document-evidence.json"):
        (fixture_dir / name).write_bytes((TASK2C_FIXTURE_ROOT / "coverage-fixtures" / name).read_bytes())
    for name, target in (
        ("product-overview.md", "product-overview.md"),
        ("module-capability.md", "module-capability.md"),
        ("procedure-rule.md", "procedure-rule.md"),
    ):
        evidence = root / "pages" / "pending" / target
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_bytes((root / name).read_bytes())

    def ref(name: str, kind: str, schema: str, version: str, ident: str) -> ArtifactRef:
        path = root / name
        import hashlib

        return ArtifactRef(kind, name, ident, hashlib.sha256(path.read_bytes()).hexdigest(), schema, version)

    return ReaderBundleInputs(
        schema_version="reader-bundle-inputs.v1",
        input_root=root,
        topic_index_ref=ref("topic-index.json", "topic-index", "2.0.0", "2.0.0", "real-topic-index"),
        source_inventory_ref=ref("source-inventory.jsonl", "source-inventory", "task1-real-corpus-verification.v1", "2026-08-06", "real-source-inventory"),
        entry_manifest_refs=(),
        offline_mode="no-llm",
        claim_records_ref=ref("claim-history.jsonl", "claim-history", "task0-claim-history.v1", "2026-08-06", "claim-history"),
        fixture_selection_ref=ref("fixture-selection.json", "fixture-selection", "task2a-fixture-selection.v1", "2026-08-09", "fixture-selection"),
    )


def _concept_pages(artifacts: BundleArtifactPaths) -> list[Path]:
    return sorted(path for path in (artifacts.bundle_dir / "products").rglob("*.md") if path.name != "index.md")


def test_reader_signal_projection_is_visible_from_page_and_indexes(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)

    pages = _concept_pages(artifacts)
    assert len(pages) == 3
    for page in pages:
        frontmatter, _body = parse_concept_document(page.read_text(encoding="utf-8"))
        signals = frontmatter["reader_signals"]
        assert signals["page_type"] == frontmatter["digest_page_type"]
        assert signals["description"] == frontmatter["description"]
        assert signals["source_count"] == len(frontmatter["sources"])
        assert signals["generated_at"] == frontmatter["generated"]["at"]
        assert signals["trust_tier"] == "machine-confirmed"
        assert signals["status"] == "published"
        assert signals["lifecycle"] == "current"

    indexes = (
        artifacts.bundle_dir / "index.md",
        artifacts.bundle_dir / "products" / "alpha-product" / "index.md",
        artifacts.bundle_dir / "products" / "alpha-product" / "modules" / "core" / "index.md",
    )
    for index in indexes:
        index_text = index.read_text(encoding="utf-8")
        for label in ("page_type", "description", "source_count", "generated_at", "trust_tier", "status", "lifecycle"):
            assert f"{label}:" in index_text, index


def test_production_projection_uses_absolute_date_for_stale_signal(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    source_inventory = inputs.input_root / "source-inventory.jsonl"
    rows = [json.loads(line) for line in source_inventory.read_text(encoding="utf-8").splitlines()]
    rows[0]["stale_after"] = (date.today() - timedelta(days=1)).isoformat()
    source_inventory.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    source_ref = ArtifactRef(
        "source-inventory",
        "source-inventory.jsonl",
        "real-source-inventory-stale",
        hashlib.sha256(source_inventory.read_bytes()).hexdigest(),
        "task1-real-corpus-verification.v1",
        "2026-08-06",
    )
    inputs = replace(inputs, source_inventory_ref=source_ref)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)

    page = artifacts.bundle_dir / "products" / "alpha-product" / "product-overview.md"
    frontmatter, _body = parse_concept_document(page.read_text(encoding="utf-8"))
    assert frontmatter["reader_signals"]["lifecycle"] == "stale"
    assert frontmatter["reader_signals"]["lifecycle_as_of"] == date.today().isoformat()
    assert frontmatter["digest_page_status"] == "published"
    assert "lifecycle: `stale`" in (artifacts.bundle_dir / "index.md").read_text(encoding="utf-8")
    assert validate_reader_bundle(artifacts, inputs).status == "passed"


def test_current_stale_after_signal_replays_after_wall_clock_moves(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _full_inputs(tmp_path)
    source_inventory = inputs.input_root / "source-inventory.jsonl"
    rows = [json.loads(line) for line in source_inventory.read_text(encoding="utf-8").splitlines()]
    rows[0]["stale_after"] = "2026-12-31"
    source_inventory.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    inputs = replace(
        inputs,
        source_inventory_ref=ArtifactRef(
            "source-inventory",
            "source-inventory.jsonl",
            "current-before-stale",
            hashlib.sha256(source_inventory.read_bytes()).hexdigest(),
            "task1-real-corpus-verification.v1",
            "2026-08-06",
        ),
    )
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    page = artifacts.bundle_dir / "products" / "alpha-product" / "product-overview.md"
    frontmatter, _body = parse_concept_document(page.read_text(encoding="utf-8"))
    assert frontmatter["reader_signals"]["lifecycle"] == "current"
    frozen_as_of = frontmatter["reader_signals"]["lifecycle_as_of"]
    assert frozen_as_of == date.today().isoformat()

    class LaterDate:
        @classmethod
        def today(cls) -> date:
            return date(2027, 1, 1)

        @classmethod
        def fromisoformat(cls, value: str) -> date:
            return date.fromisoformat(value)

    monkeypatch.setattr(reader_bundle_module, "date", LaterDate)
    assert validate_reader_bundle(artifacts, inputs).status == "passed"


@pytest.mark.parametrize(
    ("verified", "expected"),
    [
        ({"event": "source_hash_match"}, "machine-confirmed"),
        ([{"event": "locator_resolved"}], "machine-confirmed"),
        (None, "unverified"),
    ],
)
def test_verified_mapping_list_and_missing_verification_normalize_to_one_signal(
    verified: object, expected: str
) -> None:
    frontmatter = {
        "digest_page_type": "module_or_capability",
        "description": "A readable description.",
        "sources": [{"id": "source-1"}],
        "generated": {"at": "2026-08-12T00:00:00Z"},
        "digest_machine_pass": True,
        "digest_page_status": "published",
    }
    if verified is not None:
        frontmatter["verified"] = verified
    assert derive_reader_signals(frontmatter, as_of="2026-08-12")["trust_tier"] == expected


def test_human_review_event_is_not_projected_as_a_reader_trust_tier() -> None:
    frontmatter = {
        "verified": [{"event": "human_reviewed", "actor": "human:reviewer"}],
        "digest_page_type": "module_or_capability",
        "description": "A readable description.",
        "sources": [{"id": "source-1"}],
        "generated": {"at": "2026-08-12T00:00:00Z"},
        "digest_machine_pass": True,
        "digest_page_status": "published",
    }
    assert derive_reader_signals(frontmatter, as_of="2026-08-12")["trust_tier"] == "unverified"


@pytest.mark.parametrize(
    ("status", "stale_after", "expected_lifecycle"),
    [("published", "2026-08-11", "stale"), ("published", "2026-12-31", "current"), ("deprecated", None, "deprecated")],
)
def test_stale_and_deprecated_are_signals_not_automatic_degraded(
    status: str, stale_after: str | None, expected_lifecycle: str
) -> None:
    frontmatter = {
        "digest_page_type": "procedure_or_rule",
        "description": "A readable description.",
        "sources": [{"id": "source-1"}],
        "generated": {"at": "2026-08-12T00:00:00Z"},
        "digest_machine_pass": True,
        "digest_page_status": "published",
        "status": status,
    }
    if stale_after is not None:
        frontmatter["stale_after"] = stale_after
    signals = derive_reader_signals(frontmatter, as_of="2026-08-12")
    assert signals["lifecycle"] == expected_lifecycle
    assert signals["status"] == "published"
    assert signals["status"] != "degraded"


def test_degraded_topic_is_not_added_to_default_reader_navigation(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    topic_index = json.loads((inputs.input_root / "topic-index.json").read_text(encoding="utf-8"))
    topic_index["topics"][0]["status"] = "degraded"
    topic_index_path = inputs.input_root / "topic-index.json"
    topic_index_path.write_text(json.dumps(topic_index), encoding="utf-8")
    degraded_inputs = replace(inputs, topic_index_ref=_ref(inputs.input_root, "topic-index.json", "topic-index", "2.0.0", "2.0.0"))
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(degraded_inputs, artifacts)
    report = validate_reader_bundle(artifacts, degraded_inputs)
    assert report.status == "passed"
    product_index = (artifacts.bundle_dir / "products" / "fixture-product" / "index.md").read_text(encoding="utf-8")
    assert "product overview defines the reader-facing product boundary" not in product_index
    assert "modules/index.md" in product_index


def test_deprecated_page_keeps_path_but_is_hidden_from_default_navigation(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    topic_index = json.loads((inputs.input_root / "topic-index.json").read_text(encoding="utf-8"))
    topic_index["topics"][0]["reader_status"] = "deprecated"
    topic_index_path = inputs.input_root / "topic-index.json"
    topic_index_path.write_text(json.dumps(topic_index), encoding="utf-8")
    deprecated_inputs = replace(inputs, topic_index_ref=_ref(inputs.input_root, "topic-index.json", "topic-index", "2.0.0", "2.0.0"))
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(deprecated_inputs, artifacts)
    report = validate_reader_bundle(artifacts, deprecated_inputs)
    assert report.status == "passed", report.error_codes
    product_index = (artifacts.bundle_dir / "products" / "alpha-product" / "index.md").read_text(encoding="utf-8")
    assert "product-overview.md" not in product_index
    assert "modules/index.md" in product_index
    assert (artifacts.bundle_dir / "products" / "alpha-product" / "product-overview.md").is_file()


def test_reader_signals_are_additive_for_legacy_bundle(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    concept = next(path for path in _concept_pages(artifacts) if path.name != "index.md")
    frontmatter, body = parse_concept_document(concept.read_text(encoding="utf-8"))
    frontmatter.pop("reader_signals")
    from knowledge_digest.reader_frontmatter import serialize_concept_document
    concept.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    assert validate_reader_bundle(artifacts, inputs).status == "passed"


def test_reader_index_signal_projection_is_checked_against_page_fact(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    index = artifacts.bundle_dir / "index.md"
    index.write_text(index.read_text(encoding="utf-8").replace("trust_tier: `machine-confirmed`", "trust_tier: `human-reviewed`", 1), encoding="utf-8")
    report = validate_reader_bundle(artifacts, inputs)
    assert report.status == "failed"
    assert "READER_INDEX_SIGNALS_MISMATCH" in report.error_codes


def test_reader_navigation_ignores_markdown_image_embeds(tmp_path: Path) -> None:
    bundle = tmp_path / "reader"
    page = bundle / "products" / "alpha" / "overview.md"
    page.parent.mkdir(parents=True)
    (bundle / "Home.md").write_text(
        "# Home\n\n![diagram](products/alpha/diagram.png)\n\n[Overview](products/alpha/overview.md)\n",
        encoding="utf-8",
    )
    page.write_text("# Overview\n\nReader-facing content.\n", encoding="utf-8")

    snapshot = build_reader_snapshot(bundle)
    reachable, missing = _reachable_reader_paths(snapshot, "Home.md")

    assert reachable == ("Home.md", "products/alpha/overview.md")
    assert missing == ()


def _quality_manifest() -> dict[str, object]:
    handoff = json.loads((TASK2C_FIXTURE_ROOT / "task2b-handoff-recheck.json").read_text(encoding="utf-8"))
    config = {
        "pages": [
            {"path": "products/alpha-product/product-overview.md", "topic_id": "topic-43e930851b8bb3f5bdef", "page_type": "product_overview", "product": "Alpha Product", "module": None, "section_ids": ["positioning", "use_cases", "entry", "sources", "version"]},
            {"path": "products/alpha-product/modules/core/module-capability.md", "topic_id": "topic-0d3521f85e4411b86970", "page_type": "module_or_capability", "product": "Alpha Product", "module": "Core", "section_ids": ["capabilities", "limitations", "relationships", "entry_prerequisites", "sources", "version"]},
            {"path": "products/beta-product/modules/rules/procedure-rule.md", "topic_id": "topic-520b6110d7a4abd4dd8b", "page_type": "procedure_or_rule", "product": "Beta Product", "module": "Rules", "section_ids": ["steps_rules", "exceptions", "entry", "sources", "version"]},
        ],
        "task2b_handoff": handoff,
        "inventory_coverage": {
            "inventory_files": {
                "source_inventory": "source-inventory.jsonl",
                "topic_index": "topic-index.json",
            },
            "long_document": "not_exposed_by_current_inventory_schema",
        },
        "category_samples": {
            "table_or_image": ["products/alpha-product/product-overview.md"],
            "bilingual": ["products/alpha-product/modules/core/module-capability.md"],
            "multi_source": [],
            "failed_degraded": [],
            "long_document": [],
        },
        "category_fixtures": {
            "long_document": {
                "fixture": "coverage-fixtures/long-document.json",
            },
            "failed_degraded": {"fixture": "coverage-fixtures/failed-degraded.json"},
            "multi_source": {
                "fixture": "coverage-fixtures/multi-source.json",
            },
        },
    }
    return config


def test_inventory_coverage_is_machine_derived_not_manifest_self_report(tmp_path: Path) -> None:
    manifest = _quality_manifest()
    manifest["inventory_coverage"]["observed_features"] = {}
    manifest["category_samples"] = {}
    manifest["category_fixtures"] = {}
    (tmp_path / "source-inventory.jsonl").write_text(
        json.dumps({"structure_features": {"table": True, "bilingual": True}}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "topic-index.json").write_text(
        json.dumps({"topics": [{"source_members": ["a", "b"], "status": "degraded"}]}),
        encoding="utf-8",
    )
    questions, coverage = derive_task2c_questions(
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        manifest,
        seed="knowledge-digest-task0-v1",
        inventory_root=tmp_path,
    )
    assert questions
    assert coverage["table_or_image"]["status"] == "failed"
    assert coverage["bilingual"]["status"] == "failed"


def test_inventory_feature_counts_are_treated_as_present(tmp_path: Path) -> None:
    manifest = _quality_manifest()
    manifest["category_samples"] = {}
    manifest["category_fixtures"] = {}
    (tmp_path / "source-inventory.jsonl").write_text(
        json.dumps({"structure_features": {"table": 2, "image": 0, "bilingual": 1}}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "topic-index.json").write_text(
        json.dumps({"topics": []}),
        encoding="utf-8",
    )

    _questions, coverage = derive_task2c_questions(
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        manifest,
        seed="knowledge-digest-task0-v1",
        inventory_root=tmp_path,
        reader_root=TASK2C_FIXTURE_ROOT,
    )

    assert coverage["table_or_image"]["status"] == "failed"
    assert coverage["bilingual"]["status"] == "failed"


def test_unexposed_long_document_requires_a_real_fixture(tmp_path: Path) -> None:
    manifest = _quality_manifest()
    manifest["category_fixtures"].pop("long_document")
    manifest["category_samples"] = {}
    (tmp_path / "source-inventory.jsonl").write_text(
        json.dumps({"structure_features": {"table": False, "bilingual": False}}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "topic-index.json").write_text(json.dumps({"topics": []}), encoding="utf-8")

    _questions, coverage = derive_task2c_questions(
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        manifest,
        seed="knowledge-digest-task0-v1",
        inventory_root=tmp_path,
        reader_root=TASK2C_FIXTURE_ROOT,
    )

    assert coverage["long_document"]["status"] == "failed"
    assert "positive sample or machine fixture" in coverage["long_document"]["reason"]


def test_mapping_manifest_excludes_degraded_pages_before_category_sampling() -> None:
    manifest = _quality_manifest()
    degraded_path = "products/beta-product/modules/rules/procedure-rule.md"
    manifest["pages"][2]["reader_signals"] = {"status": "degraded", "lifecycle": "current"}
    manifest["category_samples"]["failed_degraded"] = [degraded_path]

    pages = _manifest_pages(manifest)

    assert degraded_path not in {page["path"] for page in pages}


def test_task2c_question_derivation_is_frozen_and_explains_inventory_gaps() -> None:
    questions, coverage = derive_task2c_questions(
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        _quality_manifest(),
        seed="knowledge-digest-task0-v1",
        inventory_root=TASK2C_FIXTURE_ROOT,
        reader_root=TASK2C_FIXTURE_ROOT,
    )
    assert [question.question_id for question in questions] == [
        "positive-01", "positive-02", "positive-03", "positive-04", "positive-05", "positive-07", "positive-09", "positive-10",
        "negative-01",
        "negative-02",
        "negative-03",
    ]
    assert {question.polarity for question in questions} == {"positive", "negative"}
    assert len({question.page_type for question in questions if question.polarity == "positive"}) >= 2
    assert len({question.module for question in questions if question.module}) >= 2
    assert coverage["long_document"]["status"] == "excluded"
    assert coverage["long_document"]["fixture"] == "coverage-fixtures/long-document.json"
    assert "inventory schema" in coverage["long_document"]["reason"]
    for category in ("table_or_image", "bilingual", "multi_source", "failed_degraded"):
        assert coverage[category]["status"] in {"sampled", "excluded"}
        assert coverage[category]["reason"]


def test_question_set_hash_and_task2b_handoff_bind_to_frozen_bytes(tmp_path: Path) -> None:
    question_set = json.loads((TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json").read_text(encoding="utf-8"))
    question_set["question_set_hash"] = "0" * 64
    path = tmp_path / "question-set.json"
    path.write_text(json.dumps(question_set, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(Exception, match="canonical question-set"):
        derive_task2c_questions(
            path,
            _quality_manifest(),
            seed="knowledge-digest-task0-v1",
            inventory_root=TASK2C_FIXTURE_ROOT,
            reader_root=TASK2C_FIXTURE_ROOT,
        )


def test_category_sample_must_exhibit_the_declared_reader_feature() -> None:
    manifest = _quality_manifest()
    manifest["category_samples"]["table_or_image"] = [
        "products/alpha-product/modules/core/module-capability.md"
    ]
    _questions, coverage = derive_task2c_questions(
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        manifest,
        seed="knowledge-digest-task0-v1",
        inventory_root=TASK2C_FIXTURE_ROOT,
        reader_root=TASK2C_FIXTURE_ROOT,
    )
    assert coverage["table_or_image"]["status"] == "failed"
    assert "does not exhibit" in coverage["table_or_image"]["reason"]


def test_machine_fixture_must_resolve_to_evidence(tmp_path: Path) -> None:
    manifest = _quality_manifest()
    manifest["category_fixtures"]["multi_source"]["fixture"] = "coverage-fixtures/missing.json"
    _questions, coverage = derive_task2c_questions(
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        manifest,
        seed="knowledge-digest-task0-v1",
        inventory_root=TASK2C_FIXTURE_ROOT,
        reader_root=TASK2C_FIXTURE_ROOT,
    )
    assert coverage["multi_source"]["status"] == "failed"
    assert coverage["multi_source"]["reason"] == "machine fixture file is missing"


def test_actual_bundle_manifest_overrides_caller_page_metadata(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    manifest = _quality_manifest()
    manifest["pages"][0]["page_type"] = "procedure_or_rule"
    questions, _coverage = derive_task2c_questions(
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        manifest,
        seed="knowledge-digest-task0-v1",
        inventory_root=inputs.input_root,
        reader_root=artifacts.bundle_dir,
    )
    overview = next(question for question in questions if question.question_id == "positive-01")
    assert overview.page_type == "product_overview"


def test_task2b_handoff_recheck_is_bound_to_local_hash_summary() -> None:
    handoff = json.loads((TASK2C_FIXTURE_ROOT / "task2b-handoff-recheck.json").read_text(encoding="utf-8"))
    assert handoff["status"] == "verified"
    assert handoff["task2b_commit"] == "2369a853adb4bc70709036c563233cae361222be"
    assert handoff["concept_machine_passing"] == 12
    assert handoff["delivery_status"] == "not_released"
    assert all(len(item["sha256"]) == 64 for item in handoff["evidence"])
    subset = handoff["answerability_subset"]
    assert subset["method"] == "section-presence-v1"
    assert len(subset["questions"]) == 20
    assert sum(row["answerable"] and row["polarity"] == "positive" for row in subset["questions"]) >= 8


def test_task2c_requires_task2b_answerability_handoff() -> None:
    manifest = _quality_manifest()
    manifest.pop("task2b_handoff")
    with pytest.raises(Exception, match="Task 2-B handoff"):
        derive_task2c_questions(
            TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
            manifest,
            seed="knowledge-digest-task0-v1",
            inventory_root=TASK2C_FIXTURE_ROOT,
        )


def test_task2c_rejects_a_first_hit_that_is_not_in_reader_manifest() -> None:
    manifest = _quality_manifest()
    manifest["task2b_handoff"]["answerability_subset"]["questions"][0]["first_hit"] = "topic-not-in-reader"
    with pytest.raises(Exception, match="first-hit topic"):
        derive_task2c_questions(
            TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
            manifest,
            seed="knowledge-digest-task0-v1",
            inventory_root=TASK2C_FIXTURE_ROOT,
        )


def test_project_llm_adapter_maps_the_runtime_provider_contract() -> None:
    calls: list[dict[str, object]] = []

    def provider(
        prompt: str,
        *,
        api_format: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        calls.append({
            "prompt": prompt,
            "api_format": api_format,
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "timeout": timeout,
            "max_tokens": max_tokens,
            "json_mode": json_mode,
        })
        return json.dumps({"answer_result": "hit"})

    provider.__name__ = "call_llm"
    provider.__module__ = "knowledge_digest.llm"
    response = _invoke_agent(
        provider,
        "reader prompt",
        {
            "api_format": "openai",
            "base_url": "https://provider.invalid/v1",
            "api_key": "in-memory-test-key",
            "model": "qwen3.6",
            "timeout": 17,
            "max_tokens": 1234,
        },
    )
    assert response["answer_result"] == "hit"
    assert calls == [{
        "prompt": "reader prompt",
        "api_format": "openai",
        "base_url": "https://provider.invalid/v1",
        "api_key": "in-memory-test-key",
        "model": "qwen3.6",
        "timeout": 17,
        "max_tokens": 1234,
        "json_mode": True,
    }]


def test_project_llm_adapter_uses_signature_contract_not_function_identity() -> None:
    calls: list[dict[str, object]] = []

    def renamed_provider(
        prompt: str,
        *,
        api_format: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        calls.append({
            "prompt": prompt,
            "api_format": api_format,
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "timeout": timeout,
            "max_tokens": max_tokens,
            "json_mode": json_mode,
        })
        return json.dumps({"answer_result": "hit"})

    response = _invoke_agent(
        renamed_provider,
        "reader prompt",
        {
            "api_format": "openai",
            "base_url": "https://provider.invalid/v1",
            "api_key": "in-memory-test-key",
            "model": "deepseek-v4-flash",
            "timeout": 17,
            "max_tokens": 1234,
        },
    )
    assert response["answer_result"] == "hit"
    assert calls[0]["prompt"] == "reader prompt"
    assert calls[0]["json_mode"] is True


def test_reader_agent_prompt_freezes_response_contract_and_optional_json_mode() -> None:
    calls: list[dict[str, object]] = []

    def provider(
        prompt: str,
        *,
        api_format: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        calls.append({
            "prompt": prompt,
            "api_format": api_format,
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "timeout": timeout,
            "max_tokens": max_tokens,
            "json_mode": json_mode,
        })
        return json.dumps({"answer_result": "hit"})

    provider.__name__ = "call_llm"
    provider.__module__ = "knowledge_digest.llm"
    _invoke_agent(
        provider,
        '{"question":"what?"}',
        {
            "api_format": "openai",
            "base_url": "https://provider.invalid/v1",
            "api_key": "in-memory-test-key",
            "model": "deepseek-v4-flash",
            "timeout": 17,
            "max_tokens": 4096,
            "json_mode": True,
        },
    )
    assert calls[0]["json_mode"] is True


def test_project_llm_adapter_forces_json_mode_when_legacy_config_omits_it() -> None:
    calls: list[dict[str, object]] = []

    def provider(
        prompt: str,
        *,
        api_format: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        calls.append({
            "prompt": prompt,
            "api_format": api_format,
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "timeout": timeout,
            "max_tokens": max_tokens,
            "json_mode": json_mode,
        })
        return json.dumps({"answer_result": "hit"})

    provider.__name__ = "call_llm"
    provider.__module__ = "knowledge_digest.llm"
    _invoke_agent(
        provider,
        "reader prompt",
        {
            "api_format": "openai",
            "base_url": "https://provider.invalid/v1",
            "api_key": "in-memory-test-key",
            "model": "deepseek-v4-flash",
            "timeout": 17,
            "max_tokens": 4096,
        },
    )
    assert calls[0]["json_mode"] is True


def test_reader_only_agent_gate_records_replayable_fields_and_not_released_exit(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    (artifacts.audit_dir / "hidden-answer.md").write_text("HIDDEN AUDIT ANSWER", encoding="utf-8")
    prompts: list[str] = []

    def jumps_for(prompt: str) -> list[str]:
        if '"target_page": "products/alpha-product/modules/core/module-capability.md"' in prompt:
            return [
                "Home.md", "index.md", "products/index.md", "products/alpha-product/index.md",
                "products/alpha-product/modules/index.md", "products/alpha-product/modules/core/index.md",
                "products/alpha-product/modules/core/module-capability.md",
            ]
        if '"target_page": "products/beta-product/modules/rules/procedure-rule.md"' in prompt:
            return [
                "Home.md", "index.md", "products/index.md", "products/beta-product/index.md",
                "products/beta-product/modules/index.md", "products/beta-product/modules/rules/index.md",
                "products/beta-product/modules/rules/procedure-rule.md",
            ]
        return ["Home.md", "index.md", "products/index.md", "products/alpha-product/index.md", "products/alpha-product/product-overview.md"]

    def fake_agent(prompt: str, **_kwargs: object) -> dict[str, object]:
        prompts.append(prompt)
        negative = "语料中没有出现" in prompt or "另一个产品" in prompt or "退休" in prompt
        return {
            "answer_found": not negative,
            "first_hit_page": next((path for path in ("products/alpha-product/product-overview.md", "products/alpha-product/modules/core/module-capability.md", "products/beta-product/modules/rules/procedure-rule.md") if f'\"target_page\": \"{path}\"' in prompt), None) if not negative else None,
            "jumps": jumps_for(prompt),
            "answer_complete": True,
            "boundary_version_accurate": True,
            "source_attribution": not negative,
            "answer_result": "no_match" if negative else "hit",
            "source_recheck_result": "passed" if not negative else "not_applicable",
        }

    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "quality-output",
        config={
            "seed": "knowledge-digest-task0-v1",
            "reader_manifest": _quality_manifest(),
            "model": "fake-reader",
            "call_budget": 11,
            "wall_clock_budget_seconds": 30,
            "review_date": "2026-08-12",
            "evidence_root": str(inputs.input_root),
            "credential_source": "environment",
            "commit": "test-commit",
        },
        llm_call=fake_agent,
    )
    assert result.status == "passed"
    assert result.delivery_status == "not_released"
    assert len(result.records) == 11
    assert prompts and all("HIDDEN AUDIT ANSWER" not in prompt for prompt in prompts)
    assert all("digest_release_status" not in prompt for prompt in prompts)
    assert all('"target_context"' in prompt for prompt in prompts)
    assert all('"canonical_route_reader_files"' in prompt for prompt in prompts)
    assert all('"reader_files"' not in prompt for prompt in prompts)
    negative_prompts = [
        prompt for prompt in prompts
        if any(text in prompt for text in ("另一个产品", "语料中没有出现", "退休"))
    ]
    assert len(negative_prompts) == 3
    assert all('"negative_question_rule"' in prompt for prompt in negative_prompts)
    assert all("Do not infer support from similar words" in prompt for prompt in negative_prompts)
    required = {
        "question", "entry_path", "first_hit_page", "jumps", "answer_found", "answer_complete",
        "boundary_version_accurate", "source_attribution", "reviewer", "review_date",
        "seed", "agent_assisted", "review_mode", "gate_actor", "model", "prompt_hash",
        "reader_input_hash", "answer_result", "source_recheck_result", "provider_response", "failure_reason",
        "scorecard_hash",
    }
    assert required <= set(result.records[0])
    assert result.records[0]["agent_assisted"] is True
    assert result.records[0]["review_mode"] == "agent_only"
    assert result.records[0]["gate_actor"] == "agent"
    assert "human_reviewed" not in result.records[0]
    assert set(result.records[0]["provider_response"]) >= {
        "answer_found", "first_hit_page", "jumps", "answer_result", "source_recheck_result",
    }
    manifest = json.loads((tmp_path / "quality-output" / "exit-manifest.json").read_text(encoding="utf-8"))
    assert manifest["delivery_status"] == "not_released"
    assert manifest["agent_assisted"] is True
    assert manifest["review_mode"] == "agent_only"
    assert manifest["gate_actor"] == "agent"
    assert manifest["credential_source"] == "environment"
    assert manifest["commit"] == "test-commit"
    assert manifest["concept_contract"] == "reader-bundle-trust-signals.v1"
    assert set(manifest["page_types"]) >= {"product_overview", "module_or_capability", "procedure_or_rule"}
    assert set(manifest["signal_fields"]) >= {"trust_tier", "lifecycle", "source_count"}
    assert manifest["question_derivation"]["question_set_id"] == "knowledge-digest-task0-v1"
    assert manifest["question_derivation"]["question_set_hash"] == "41080f16f2955df27b9437df72e3a95c5c437a122abc514ad3abf09e9ab9d2e7"
    assert manifest["thresholds"] == {
        "positive_minimum": 8,
        "positive_hit_rate": 1.0,
        "negative_count": 3,
        "negative_false_positive_maximum": 0,
    }
    scorecard = json.loads((tmp_path / "quality-output" / "scorecard.json").read_text(encoding="utf-8"))
    assert _scorecard_content_hash(scorecard) == manifest["scorecard_hash"]


def test_reader_prompt_keeps_prose_that_mentions_internal_paths_but_redacts_internal_links() -> None:
    from knowledge_digest.reader_quality import _reader_prompt_text

    text = (
        "This page explains why _digest/ is not a reader source.\n"
        "See [audit evidence](../../audit/run.json) only in the audit package.\n"
        "The literal string _archive/ is part of this explanation.\n"
    )
    rendered = _reader_prompt_text(text, source_path="products/alpha/page.md")
    assert "This page explains why _digest/ is not a reader source." in rendered
    assert "The literal string _archive/ is part of this explanation." in rendered
    assert "../../audit/run.json" not in rendered
    assert "[audit evidence](internal link omitted)" in rendered


def test_reader_snapshot_allowlist_and_missing_answer_fields_fail_closed(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    (artifacts.audit_dir / "answer.md").write_text("hidden", encoding="utf-8")
    snapshot = build_reader_snapshot(artifacts.bundle_dir)
    assert snapshot.paths
    assert all(not path.startswith("audit/") for path in snapshot.paths)

    def incomplete_agent(_prompt: str, **_kwargs: object) -> dict[str, object]:
        return {"answer_found": True}

    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "quality-output",
        config={"reader_manifest": _quality_manifest(), "seed": "knowledge-digest-task0-v1", "review_date": "2026-08-12", "evidence_root": str(inputs.input_root), "call_budget": 11, "wall_clock_budget_seconds": 30, "credential_source": "environment", "commit": "test-commit"},
        llm_call=incomplete_agent,
    )
    assert result.status == "failed"
    assert result.delivery_status == "not_released"
    assert any("missing" in reason for reason in result.failure_reasons)


def test_broken_evidence_file_fails_the_reader_source_chain(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    (inputs.input_root / "pages" / "pending" / "product-overview.md").unlink()
    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "broken-evidence",
        config=_quality_config(inputs.input_root),
        llm_call=_passing_agent,
    )
    assert result.status == "failed"
    assert any("evidence_file_missing" in reason for reason in result.failure_reasons)


def test_missing_inventory_manifest_and_contradictory_answer_fail_closed(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    missing_manifest_config = _quality_config(inputs.input_root)
    missing_manifest_config.pop("reader_manifest")
    missing = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "missing-manifest",
        config=missing_manifest_config,
        llm_call=_passing_agent,
    )
    assert missing.status == "failed"
    assert any("inventory coverage" in reason for reason in missing.failure_reasons)

    def contradictory_agent(prompt: str, **_kwargs: object) -> dict[str, object]:
        response = _passing_agent(prompt, **_kwargs)
        if "语料中没有出现" in prompt or "另一个产品" in prompt or "退休" in prompt:
            response["answer_found"] = False
            response["answer_result"] = "not_found"
        else:
            response["answer_result"] = "no_match"
        return response

    contradictory = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "contradictory",
        config=_quality_config(inputs.input_root),
        llm_call=contradictory_agent,
    )
    assert contradictory.status == "failed"
    assert any("gate failed" in reason for reason in contradictory.failure_reasons)


def test_negative_answer_must_not_claim_attribution_or_recheck(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)

    def contradictory_negative(prompt: str, **kwargs: object) -> dict[str, object]:
        response = _passing_agent(prompt, **kwargs)
        if response["answer_result"] == "no_match":
            response["source_attribution"] = True
        return response

    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "negative-contract",
        config=_quality_config(inputs.input_root),
        llm_call=contradictory_negative,
    )
    assert result.status == "failed"
    assert any("negative false-positive gate failed" in reason for reason in result.failure_reasons)


def test_missing_negative_response_is_not_counted_as_semantic_false_positive(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)

    def missing_negative_response(prompt: str, **kwargs: object) -> dict[str, object]:
        if any(text in prompt for text in ("另一个产品", "语料中没有出现", "退休")):
            return {}
        return _passing_agent(prompt, **kwargs)

    output = tmp_path / "missing-negative-response"
    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        output,
        config=_quality_config(inputs.input_root),
        llm_call=missing_negative_response,
    )

    assert result.status == "failed"
    scorecard = json.loads((output / "scorecard.json").read_text(encoding="utf-8"))
    assert scorecard["summary"]["negative_false_positives"] == 0
    assert any("missing response fields" in reason for reason in result.failure_reasons)


def test_positive_summary_requires_navigation_and_source_chain(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)

    def broken_chain_agent(prompt: str, **kwargs: object) -> dict[str, object]:
        response = _passing_agent(prompt, **kwargs)
        if '"target_page": "products/alpha-product/product-overview.md"' in prompt:
            response["jumps"] = ["Home.md"]
        return response

    output = tmp_path / "broken-positive-summary"
    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        output,
        config=_quality_config(inputs.input_root),
        llm_call=broken_chain_agent,
    )

    assert result.status == "failed"
    scorecard = json.loads((output / "scorecard.json").read_text(encoding="utf-8"))
    assert scorecard["summary"]["positive_passed"] < scorecard["summary"]["positive_count"]


def test_negative_gate_requires_machine_referent_absence(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    home = artifacts.bundle_dir / "Home.md"
    home.write_text(home.read_text(encoding="utf-8") + "\n另一个产品中的同名的能力仅用于测试边界。\n", encoding="utf-8")

    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "negative-referent-present",
        config=_quality_config(inputs.input_root),
        llm_call=_passing_agent,
    )

    assert result.status == "failed"
    assert any("negative referent is present" in reason for reason in result.failure_reasons)


def test_wall_clock_budget_records_current_call_and_stops_before_next_question(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    calls = 0

    def slow_agent(prompt: str, **kwargs: object) -> dict[str, object]:
        nonlocal calls
        calls += 1
        time.sleep(0.02)
        return _passing_agent(prompt, **kwargs)

    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "wall-budget",
        config={**_quality_config(inputs.input_root), "wall_clock_budget_seconds": 0.001},
        llm_call=slow_agent,
    )
    assert result.status == "failed"
    assert calls == 1
    assert len(result.records) == 1
    assert "wall-clock budget exceeded" in result.failure_reasons


def _passing_agent(prompt: str, **_kwargs: object) -> dict[str, object]:
    negative = "语料中没有出现" in prompt or "另一个产品" in prompt or "退休" in prompt
    if '"target_page": "products/alpha-product/modules/core/module-capability.md"' in prompt:
        jumps = ["Home.md", "index.md", "products/index.md", "products/alpha-product/index.md", "products/alpha-product/modules/index.md", "products/alpha-product/modules/core/index.md", "products/alpha-product/modules/core/module-capability.md"]
        target = "products/alpha-product/modules/core/module-capability.md"
    elif '"target_page": "products/beta-product/modules/rules/procedure-rule.md"' in prompt:
        jumps = ["Home.md", "index.md", "products/index.md", "products/beta-product/index.md", "products/beta-product/modules/index.md", "products/beta-product/modules/rules/index.md", "products/beta-product/modules/rules/procedure-rule.md"]
        target = "products/beta-product/modules/rules/procedure-rule.md"
    else:
        jumps = ["Home.md", "index.md", "products/index.md", "products/alpha-product/index.md", "products/alpha-product/product-overview.md"]
        target = "products/alpha-product/product-overview.md"
    return {
        "answer_found": not negative,
        "first_hit_page": target if not negative else None,
        "jumps": jumps,
        "answer_complete": True,
        "boundary_version_accurate": True,
        "source_attribution": not negative,
        "answer_result": "no_match" if negative else "hit",
        "source_recheck_result": "passed" if not negative else "not_applicable",
    }


def _quality_config(evidence_root: Path | None = None) -> dict[str, object]:
    config = {
        "seed": "knowledge-digest-task0-v1",
        "reader_manifest": _quality_manifest(),
        "model": "fake-reader",
        "call_budget": 11,
        "wall_clock_budget_seconds": 30,
        "review_date": "2026-08-12",
        "credential_source": "environment",
        "commit": "test-commit",
    }
    if evidence_root is not None:
        config["evidence_root"] = str(evidence_root)
    return config


def test_provider_failure_cancel_and_quality_failure_leave_old_bundle_unchanged(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    committed = project_reader_bundle(inputs, artifacts)
    old_hashes = (committed.base_bundle_hash, committed.base_projection_report_hash, committed.base_exit_manifest_hash)

    def provider_failure(_prompt: str, **_kwargs: object) -> object:
        raise RuntimeError("provider unavailable")

    failed = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "provider-failure",
        config=_quality_config(inputs.input_root),
        llm_call=provider_failure,
    )
    assert failed.status == "failed"
    assert failed.delivery_status == "not_released"
    failed_manifest = json.loads((tmp_path / "provider-failure" / "exit-manifest.json").read_text(encoding="utf-8"))
    assert failed_manifest["status"] != "released"
    assert failed_manifest["delivery_status"] == "not_released"
    assert {
        "concept_contract", "page_types", "signal_fields", "template", "question_derivation",
        "thresholds", "provider", "call_budget", "wall_clock_budget_seconds", "credential_source",
        "commit", "reader_input_hash",
    } <= set(failed_manifest)
    assert failed_manifest["question_derivation"]["question_set_id"] == "knowledge-digest-task0-v1"

    def cancelled(_prompt: str, **_kwargs: object) -> object:
        raise KeyboardInterrupt()

    cancelled_result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "cancelled",
        config=_quality_config(inputs.input_root),
        llm_call=cancelled,
    )
    assert cancelled_result.status == "failed"
    assert any("run_cancelled" in reason for reason in cancelled_result.failure_reasons)
    cancelled_manifest = json.loads((tmp_path / "cancelled" / "exit-manifest.json").read_text(encoding="utf-8"))
    assert {
        "concept_contract", "page_types", "signal_fields", "template", "question_derivation",
        "thresholds", "provider", "call_budget", "wall_clock_budget_seconds", "credential_source",
        "commit", "reader_input_hash",
    } <= set(cancelled_manifest)
    assert not list(tmp_path.glob(".cancelled.staging-*"))
    assert old_hashes == (committed.base_bundle_hash, committed.base_projection_report_hash, committed.base_exit_manifest_hash)


def test_same_input_replay_is_stable_and_same_output_is_single_writer(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    first = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "run-one",
        config=_quality_config(inputs.input_root),
        llm_call=_passing_agent,
    )
    second = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        tmp_path / "run-two",
        config=_quality_config(inputs.input_root),
        llm_call=_passing_agent,
    )
    assert first.status == second.status == "passed"
    assert (tmp_path / "run-one" / "scorecard.json").read_bytes() == (tmp_path / "run-two" / "scorecard.json").read_bytes()
    assert first.exit_manifest["run_id"] == second.exit_manifest["run_id"]
    assert first.exit_manifest["scorecard_hash"] == first.scorecard_hash
    assert all(record["scorecard_hash"] == first.scorecard_hash for record in first.records)

    concurrent_output = tmp_path / "concurrent"
    entered = threading.Event()

    def slow_agent(prompt: str, **kwargs: object) -> dict[str, object]:
        entered.set()
        time.sleep(0.02)
        return _passing_agent(prompt, **kwargs)

    results: list[object] = []

    def run_one() -> None:
        results.append(run_reader_quality_gate(artifacts.bundle_dir, TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json", concurrent_output, config=_quality_config(inputs.input_root), llm_call=slow_agent))

    first_thread = threading.Thread(target=run_one)
    second_thread = threading.Thread(target=run_one)
    first_thread.start()
    entered.wait(timeout=2)
    second_thread.start()
    first_thread.join()
    second_thread.join()
    assert sorted(result.status for result in results) == ["failed", "passed"]
    assert not list(tmp_path.glob(".concurrent.staging-*"))
    assert (tmp_path / ".digest.lock").is_file()


def test_lock_receives_exception_context_when_output_write_fails(monkeypatch, tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    observed: list[tuple[object, object, object]] = []

    class RecordingLock:
        def __enter__(self):
            return tmp_path / ".digest.lock"

        def __exit__(self, exc_type, exc_value, traceback):
            observed.append((exc_type, exc_value, traceback))
            return False

    monkeypatch.setattr("knowledge_digest.reader_quality.kb_lock", lambda _path: RecordingLock())

    def broken_write(*_args, **_kwargs):
        raise RuntimeError("write failed")

    monkeypatch.setattr("knowledge_digest.reader_quality._write_output", broken_write)
    with pytest.raises(RuntimeError, match="write failed"):
        run_reader_quality_gate(
            artifacts.bundle_dir,
            TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
            tmp_path / "quality-output",
            config=_quality_config(inputs.input_root),
            llm_call=lambda *_args, **_kwargs: {},
        )
    assert observed and observed[0][0] is RuntimeError
    assert str(observed[0][1]) == "write failed"


def test_dead_lock_owner_is_recovered_on_rerun(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path / "inputs")
    artifacts = BundleArtifactPaths.from_root(tmp_path / "bundle-artifacts")
    project_reader_bundle(inputs, artifacts)
    output = tmp_path / "recovered"
    lock = tmp_path / ".digest.lock"
    lock.write_text("stale lock file from a previous process\n", encoding="utf-8")
    result = run_reader_quality_gate(
        artifacts.bundle_dir,
        TASK2C_FIXTURE_ROOT / "task0-question-set.v1.json",
        output,
        config=_quality_config(inputs.input_root),
        llm_call=_passing_agent,
    )
    assert result.status == "passed"
    assert lock.is_file()
