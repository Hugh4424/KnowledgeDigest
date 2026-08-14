from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace

import pytest
from pathlib import Path

from knowledge_digest.reader_bundle import (
    ArtifactRef,
    BundleArtifactPaths,
    SemanticReaderBundleInputs,
    project_reader_bundle,
    validate_reader_bundle,
)
from knowledge_digest.errors import ValidationError
from knowledge_digest.reader_frontmatter import managed_content_hash, parse_concept_document, serialize_concept_document


PROJECT_ROOT = Path(__file__).parents[2]
TASK2A_FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "task2a_reader_bundle"
TASK3_FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "task3_full_release"


def _ref(root: Path, name: str, kind: str, schema: str, version: str, ident: str) -> ArtifactRef:
    path = root / name
    return ArtifactRef(kind, name, ident, hashlib.sha256(path.read_bytes()).hexdigest(), schema, version)


def _semantic_inputs(tmp_path: Path) -> SemanticReaderBundleInputs:
    root = tmp_path / "inputs"
    root.mkdir()
    topic_index = json.loads((TASK2A_FIXTURE_ROOT / "topic-index.json").read_text(encoding="utf-8"))
    other = dict(topic_index["topics"][1])
    other.update(
        {
            "digest_topic_id": "digest-topic-other-product",
            "topic_id": "digest-topic-other-product",
            "topic_key": "v2/products/other-product/other-module/module-capability",
            "product": "Other Product",
            "product_slug": "other-product",
            "module": "Other Module",
            "published_path": "pages/topics/products/other-product/other-module/module-capability.md",
            "source_ids": ["source-fixture-other"],
            "source_members": ["source-fixture-other"],
            "evidence_refs": [
                {
                    "content_fingerprint": "c" * 64,
                    "line_number": 3,
                    "source_uri": "raw://fixture/other.md",
                }
            ],
            "description": "The other product is intentionally separate.",
        }
    )
    degraded = dict(other)
    degraded.update(
        {
            "digest_topic_id": "digest-topic-degraded",
            "topic_id": "digest-topic-degraded",
            "topic_key": "v2/products/broken/broken-module/broken",
            "product": "Broken Product",
            "product_slug": "broken-product",
            "module": "Broken Module",
            "evidence_refs": [],
            "source_ids": [],
            "source_members": [],
            "description": "This row must stay in Audit.",
        }
    )
    topic_index["topics"].extend([other, degraded])
    topic_index["topics"][0]["old_path_mapping"] = [{
        "old_path": "pages/legacy/fixture-overview.md",
        "relation": "rename",
        "evidence_refs": [{"content_fingerprint": "a" * 64, "line_number": 1, "source_uri": "raw://fixture/product-overview.md"}],
    }]
    topic_index["topics"][1]["old_path_mapping"] = [{
        "old_path": "pages/legacy/missing-module.md",
        "relation": "unmappable",
        "evidence_refs": [{"content_fingerprint": "b" * 64, "line_number": 2, "source_uri": "raw://fixture/module-capability.md"}],
    }]
    (root / "topic-index.json").write_text(json.dumps(topic_index, indent=2) + "\n", encoding="utf-8")

    source_rows = (TASK2A_FIXTURE_ROOT / "source-inventory.jsonl").read_text(encoding="utf-8")
    source_rows += json.dumps(
        {
            "content_fingerprint": "c" * 64,
            "content_path": "fixture/other.md",
            "evidence_refs": [{"content_fingerprint": "c" * 64, "line_number": 3, "source_uri": "raw://fixture/other.md"}],
            "knowledge_type": "products",
            "source_id": "source-fixture-other",
            "source_uri": "raw://fixture/other.md",
            "title": "Other Product Capability",
            "validation_status": "passed",
        }
    ) + "\n"
    (root / "source-inventory.jsonl").write_text(source_rows, encoding="utf-8")

    bodies = {
        "product-overview.md": "# Fixture Product Overview\n\nThe product boundary is documented here.[^src-product]\n",
        "module-capability.md": "# Fixture Module Capability\n\nThe module capability is documented here.[^src-module]\n",
        "other.md": "# Other Product Capability\n\nThe other product capability is documented here.[^src-other]\n",
    }
    for name, body in bodies.items():
        (root / name).write_text(body, encoding="utf-8")
    claims = [
        {"claim_id": "claim-product", "source_uri": "raw://fixture/product-overview.md", "content_fingerprint": "a" * 64, "fragment_locator": "lines:1-1", "target_path": "products/fixture-product/product-overview.md"},
        {"claim_id": "claim-module", "source_uri": "raw://fixture/module-capability.md", "content_fingerprint": "b" * 64, "fragment_locator": "lines:1-1", "target_path": "products/fixture-product/modules/fixture-module/module-capability.md"},
        {"claim_id": "claim-other", "source_uri": "raw://fixture/other.md", "content_fingerprint": "c" * 64, "fragment_locator": "lines:1-1", "target_path": "products/other-product/modules/other-module/module-capability.md"},
    ]
    (root / "claim-history.jsonl").write_text("\n".join(json.dumps(row) for row in claims) + "\n", encoding="utf-8")

    snapshot = json.loads((TASK3_FIXTURE_ROOT / "projection-cases.json").read_text(encoding="utf-8"))
    (root / "semantic-snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    selections = {
        "schema_version": "task2a-fixture-selection.v1",
        "fixtures": [],
    }
    for sample_id, topic, intent, role, source_id, fragment_id, fingerprint, filename, claim_id in (
        ("fixture-product", "digest-topic-product-overview", "product overview", "product_overview", "source-fixture-product", "src-product", "a" * 64, "product-overview.md", "claim-product"),
        ("fixture-module", "digest-topic-module", "module capability", "module_or_capability", "source-fixture-module", "src-module", "b" * 64, "module-capability.md", "claim-module"),
        ("fixture-other", "digest-topic-other-product", "module capability", "module_or_capability", "source-fixture-other", "src-other", "c" * 64, "other.md", "claim-other"),
    ):
        path = root / filename
        selections["fixtures"].append({
            "sample_id": sample_id,
            "fixture_path": filename,
            "fixture_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "topic_id": topic,
            "object_intent": intent,
            "mapping_role": role,
            "digest_page_type": role,
            "source_id": source_id,
            "source_fragment_id": fragment_id,
            "content_fingerprint": fingerprint,
            "claim_ids": [claim_id],
            "selection_reason": "fixture evidence",
        })
    (root / "fixture-selection.json").write_text(json.dumps(selections, indent=2) + "\n", encoding="utf-8")
    return SemanticReaderBundleInputs(
        schema_version="reader-bundle-semantic-inputs.v1",
        input_root=root,
        topic_index_ref=_ref(root, "topic-index.json", "topic-index", "2.0.0", "2.0.0", "topic-index"),
        source_inventory_ref=_ref(root, "source-inventory.jsonl", "source-inventory", "task1-real-corpus-verification.v1", "2026-08-06", "source-inventory"),
        entry_manifest_refs=(),
        offline_mode="no-llm",
        semantic_snapshot_ref=_ref(root, "semantic-snapshot.json", "semantic-snapshot", "reader-bundle-semantic-snapshot.v1", "1", "semantic-snapshot"),
        claim_records_ref=_ref(root, "claim-history.jsonl", "claim-history", "task0-claim-history.v1", "1", "claim-history"),
        fixture_selection_ref=_ref(root, "fixture-selection.json", "fixture-selection", "task2a-fixture-selection.v1", "1", "fixture-selection"),
    )


def _concepts(artifacts: BundleArtifactPaths) -> dict[str, tuple[Path, str, str]]:
    result = {}
    for path in sorted((artifacts.bundle_dir / "products").rglob("*.md")):
        if path.name == "index.md":
            continue
        frontmatter, body = parse_concept_document(path.read_text(encoding="utf-8"))
        result[str(frontmatter["digest_topic_id"])] = (path, frontmatter["title"], body)
    return result


def test_semantic_projection_keeps_candidate_split_and_canonical_navigation(tmp_path: Path) -> None:
    inputs = _semantic_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifacts")

    committed = project_reader_bundle(inputs, artifacts)

    assert committed.report.release_status == "not_released"
    assert json.loads(artifacts.projection_report_path.read_text(encoding="utf-8"))["digest_release_status"] == "not_released"
    assert (artifacts.bundle_dir / "Home.md").read_text(encoding="utf-8") == "# Home\n\n[Reader index](index.md)\n"
    assert (artifacts.bundle_dir / "index.md").is_file()
    assert (artifacts.bundle_dir / "products" / "index.md").is_file()
    assert (artifacts.bundle_dir / "products" / "fixture-product" / "index.md").is_file()
    assert (artifacts.bundle_dir / "products" / "fixture-product" / "modules" / "fixture-module" / "index.md").is_file()
    assert (artifacts.bundle_dir / "references" / "sources.md").is_file()
    assert (artifacts.bundle_dir / "log.md").is_file()
    assert "Task 2-A" not in (artifacts.bundle_dir / "README.md").read_text(encoding="utf-8")
    assert validate_reader_bundle(artifacts, inputs).status == "passed"

    concepts = _concepts(artifacts)
    assert "digest-topic-degraded" not in concepts
    assert {"digest-topic-product-overview", "digest-topic-module", "digest-topic-other-product"} <= concepts.keys()
    degraded = json.loads(artifacts.projection_report_path.read_text(encoding="utf-8"))["degraded_records"]
    assert {item["stable_id"] for item in degraded} == {"digest-topic-degraded"}
    assert (artifacts.audit_dir / "_digest" / "degraded" / "digest-topic-degraded.md").is_file()
    for path, _title, _body in concepts.values():
        frontmatter, _ = parse_concept_document(path.read_text(encoding="utf-8"))
        source = frontmatter["sources"][0]
        assert all(claim["source_uri"] == source["resource"] for claim in source["digest_claims"])


def test_semantic_projection_sanitizes_bracketed_related_link_labels(tmp_path: Path) -> None:
    inputs = _semantic_inputs(tmp_path)
    fixture_path = inputs.input_root / "module-capability.md"
    fixture_path.write_text(
        "# [Fixture] Module Capability\n\nThe module capability is documented here.[^src-module]\n",
        encoding="utf-8",
    )
    selection_path = inputs.input_root / "fixture-selection.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    for row in selection["fixtures"]:
        if row["sample_id"] == "fixture-module":
            row["fixture_sha256"] = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    selection_path.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
    inputs = replace(
        inputs,
        fixture_selection_ref=_ref(
            inputs.input_root,
            "fixture-selection.json",
            "fixture-selection",
            "task2a-fixture-selection.v1",
            "1",
            "fixture-selection",
        ),
    )
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifacts-bracketed-title")

    project_reader_bundle(inputs, artifacts)

    assert validate_reader_bundle(artifacts, inputs).status == "passed"
    product_page = artifacts.bundle_dir / "products" / "fixture-product" / "product-overview.md"
    body = product_page.read_text(encoding="utf-8")
    assert "[[Fixture] Module Capability]" not in body
    assert "[Fixture Module Capability]" in body


def test_semantic_projection_only_emits_evidence_backed_bidirectional_related(tmp_path: Path) -> None:
    inputs = _semantic_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifacts")
    project_reader_bundle(inputs, artifacts)

    concepts = _concepts(artifacts)
    overview_body = concepts["digest-topic-product-overview"][2]
    module_body = concepts["digest-topic-module"][2]
    other_body = concepts["digest-topic-other-product"][2]
    assert "## Related" in overview_body
    assert "Fixture Module Capability" in overview_body
    assert "## Related" in module_body
    assert "Fixture Product Overview" in module_body
    assert "## Related" not in other_body

    relation_audit = json.loads((artifacts.audit_dir / "relations.json").read_text(encoding="utf-8"))
    assert relation_audit["edges"] == [
        {
            "from_topic_id": "digest-topic-module",
            "reason": ["explicit_cross_reference", "same_product"],
            "to_topic_id": "digest-topic-product-overview",
            "evidence_refs": [{
                "target_topic_id": "digest-topic-module",
                "source_id": "source-fixture-product",
                "source_uri": "raw://fixture/product-overview.md",
                "content_fingerprint": "a" * 64,
                "fragment_locator": "lines:1-1",
            }],
        }
    ]


def test_semantic_projection_records_alias_or_deprecated_for_every_old_path(tmp_path: Path) -> None:
    inputs = _semantic_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifacts")
    project_reader_bundle(inputs, artifacts)

    mapping = json.loads((artifacts.audit_dir / "old-path-mapping.json").read_text(encoding="utf-8"))
    statuses = {item["old_path"]: item for item in mapping["mappings"]}
    assert statuses["pages/legacy/fixture-overview.md"] == {
        "old_path": "pages/legacy/fixture-overview.md",
        "relation": "rename",
        "evidence_refs": [{"content_fingerprint": "a" * 64, "line_number": 1, "source_uri": "raw://fixture/product-overview.md"}],
        "reason": "canonical topic target",
        "status": "alias",
        "target_path": "products/fixture-product/product-overview.md",
    }
    assert statuses["pages/legacy/missing-module.md"]["status"] == "deprecated"
    assert statuses["pages/legacy/missing-module.md"]["target_path"] is None
    assert statuses["pages/legacy/missing-module.md"]["reason"]
    assert (artifacts.bundle_dir / "pages/legacy/fixture-overview.md").is_file()
    assert "canonical page" in (artifacts.bundle_dir / "pages/legacy/fixture-overview.md").read_text(encoding="utf-8")
    assert (artifacts.bundle_dir / "pages/legacy/missing-module.md").is_file()
    compatibility = (artifacts.bundle_dir / "references" / "old-paths.md").read_text(encoding="utf-8")
    assert "fixture-overview.md" in compatibility
    assert "missing-module.md" in compatibility


def test_semantic_validator_rechecks_claims_and_trust_events(tmp_path: Path) -> None:
    inputs = _semantic_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifacts")
    project_reader_bundle(inputs, artifacts)
    page = artifacts.bundle_dir / "products" / "fixture-product" / "product-overview.md"
    frontmatter, body = parse_concept_document(page.read_text(encoding="utf-8"))
    frontmatter["sources"][0]["digest_claims"] = []
    frontmatter["verified"] = []
    frontmatter["digest_content_hash"] = managed_content_hash(frontmatter, body)
    page.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    trust = artifacts.audit_dir / "trust-signals" / "products-fixture-product-product-overview.json"
    value = json.loads(trust.read_text(encoding="utf-8"))
    value["content_hash"] = frontmatter["digest_content_hash"]
    value["events"] = []
    trust.write_text(json.dumps(value) + "\n", encoding="utf-8")
    report = validate_reader_bundle(artifacts, inputs)
    assert report.status == "failed"
    assert {"SOURCE_CLAIM_CHAIN_MISSING", "TRUST_SIGNAL_REQUIRED_EVENT_MISSING"} <= set(report.error_codes)


@pytest.mark.parametrize("target", ["digest-topic-product-overview", "digest-topic-unknown"])
def test_semantic_related_refs_reject_self_or_unknown_targets(tmp_path: Path, target: str) -> None:
    inputs = _semantic_inputs(tmp_path)
    snapshot_path = inputs.input_root / "semantic-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["topics"][0]["related_topic_refs"][0]["target_topic_id"] = target
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    inputs = replace(inputs, semantic_snapshot_ref=_ref(inputs.input_root, "semantic-snapshot.json", "semantic-snapshot", "reader-bundle-semantic-snapshot.v1", "1", "semantic-snapshot"))
    with pytest.raises(ValidationError, match="related topic target"):
        project_reader_bundle(inputs, BundleArtifactPaths.from_root(tmp_path / "artifacts"))


def test_semantic_related_ref_locator_is_structured(tmp_path: Path) -> None:
    inputs = _semantic_inputs(tmp_path)
    snapshot_path = inputs.input_root / "semantic-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["topics"][0]["related_topic_refs"][0]["fragment_locator"] = "not-a-locator"
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    inputs = replace(inputs, semantic_snapshot_ref=_ref(inputs.input_root, "semantic-snapshot.json", "semantic-snapshot", "reader-bundle-semantic-snapshot.v1", "1", "semantic-snapshot"))
    with pytest.raises(ValidationError, match="locator is invalid"):
        project_reader_bundle(inputs, BundleArtifactPaths.from_root(tmp_path / "artifacts"))


def test_semantic_old_path_split_is_rejected_instead_of_overwriting_stub(tmp_path: Path) -> None:
    inputs = _semantic_inputs(tmp_path)
    topic_index_path = inputs.input_root / "topic-index.json"
    topic_index = json.loads(topic_index_path.read_text(encoding="utf-8"))
    topic_index["topics"][1]["old_path_mapping"] = topic_index["topics"][0]["old_path_mapping"]
    topic_index_path.write_text(json.dumps(topic_index, indent=2) + "\n", encoding="utf-8")
    inputs = replace(inputs, topic_index_ref=_ref(inputs.input_root, "topic-index.json", "topic-index", "2.0.0", "2.0.0", "topic-index"))
    with pytest.raises(ValidationError, match="one old path cannot map to multiple targets"):
        project_reader_bundle(inputs, BundleArtifactPaths.from_root(tmp_path / "artifacts"))
