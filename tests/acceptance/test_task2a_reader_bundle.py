from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from knowledge_digest.errors import ValidationError
from knowledge_digest.reader_bundle import (
    ArtifactRef,
    BundleArtifactPaths,
    ReaderBundleInputs,
    ReaderBundleStructureInputs,
    _atomic_commit,
    adapt_topic_index_row,
    check_entry_bindings,
    project_reader_bundle,
    _selected_page_type,
    validate_reader_bundle,
    write_entry_backfill_manifest,
)
from knowledge_digest.reader_frontmatter import parse_concept_document, serialize_concept_document


FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "task2a_reader_bundle"
PROJECT_ROOT = Path(__file__).parents[2]
REAL_ENTRY_ROOT = PROJECT_ROOT / "quality" / "evidence" / "task2-entry"


def _copy_structural_inputs(root: Path) -> None:
    root.mkdir(parents=True)
    for name in ("topic-index.json", "source-inventory.jsonl"):
        shutil.copy2(FIXTURE_ROOT / name, root / name)


def _ref(root: Path, name: str, kind: str, schema: str, version: str) -> ArtifactRef:
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


def _row() -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / "topic-index.json").read_text())["topics"][0]


def _full_inputs(tmp_path: Path) -> ReaderBundleInputs:
    root = tmp_path / "full-inputs"
    root.mkdir(parents=True)
    real_root = REAL_ENTRY_ROOT / "task1-real-corpus-20260806"
    for source, destination in (
        (real_root / "topic-index.json", root / "topic-index.json"),
        (real_root / "source-inventory.jsonl", root / "source-inventory.jsonl"),
        (REAL_ENTRY_ROOT / "knowledge-publication-task2-entry-backfill.v1.json", root / "entry-backfill.json"),
        (REAL_ENTRY_ROOT / "task2-entry-sample-coverage.v1.json", root / "sample-coverage.json"),
        (FIXTURE_ROOT / "claim-history.jsonl", root / "claim-history.jsonl"),
        (FIXTURE_ROOT / "fixture-selection.json", root / "fixture-selection.json"),
        (FIXTURE_ROOT / "product-overview.md", root / "product-overview.md"),
        (FIXTURE_ROOT / "module-capability.md", root / "module-capability.md"),
        (FIXTURE_ROOT / "procedure-rule.md", root / "procedure-rule.md"),
    ):
        shutil.copy2(source, destination)
    def ref(name: str, kind: str, schema: str, version: str, ident: str | None = None) -> ArtifactRef:
        path = root / name
        return ArtifactRef(kind, name, ident or f"fixture-{name}", hashlib.sha256(path.read_bytes()).hexdigest(), schema, version)
    return ReaderBundleInputs(
        schema_version="reader-bundle-inputs.v1",
        input_root=root,
        topic_index_ref=ref("topic-index.json", "topic-index", "2.0.0", "2.0.0", "real-topic-index"),
        source_inventory_ref=ref("source-inventory.jsonl", "source-inventory", "task1-real-corpus-verification.v1", "2026-08-06", "real-source-inventory"),
        entry_manifest_refs=(
            ref("entry-backfill.json", "entry-backfill", "knowledge-publication-task2-entry-backfill.v1", "2026-08-06", "entry-backfill"),
            ref("sample-coverage.json", "sample-coverage", "task2-entry-sample-coverage.v1", "2026-08-06", "sample-coverage"),
        ),
        offline_mode="no-llm",
        claim_records_ref=ref("claim-history.jsonl", "claim-history", "task0-claim-history.v1", "2026-08-06", "claim-history"),
        fixture_selection_ref=ref("fixture-selection.json", "fixture-selection", "task2a-fixture-selection.v1", "2026-08-09", "fixture-selection"),
    )


def test_bundle_projection_writes_canonical_root_and_no_nested_log(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    assert (artifacts.bundle_dir / "README.md").is_file()
    assert (artifacts.bundle_dir / "Home.md").is_file()
    assert (artifacts.bundle_dir / "index.md").is_file()
    assert (artifacts.bundle_dir / "log.md").is_file()
    assert (artifacts.bundle_dir / "products" / "index.md").is_file()
    assert (artifacts.bundle_dir / "products" / "fixture-product" / "modules" / "index.md").is_file()
    sources = artifacts.bundle_dir / "references" / "sources.md"
    assert sources.is_file()
    sources_text = sources.read_text(encoding="utf-8")
    assert not sources_text.startswith("---\n")
    assert "source-fixture-product" in sources_text
    assert "source-fixture-module" in sources_text
    assert "raw://fixture/product-overview.md" in sources_text
    assert "raw://fixture/module-capability.md" in sources_text
    readme = (artifacts.bundle_dir / "README.md").read_text(encoding="utf-8")
    assert "isolated Task 2-A projection" in readme
    assert "not released" in readme
    log = (artifacts.bundle_dir / "log.md").read_text(encoding="utf-8")
    assert "digest_release_status: `not_released`" in log
    assert "change: initial isolated projection" in log
    assert not list(artifacts.bundle_dir.glob("**/log.md"))[1:]


def test_product_only_adapter_does_not_invent_a_module() -> None:
    result = adapt_topic_index_row(
        _row(),
        source_ref=ArtifactRef("topic-index", "topic-index.json", "fixture", "a" * 64, "2.0.0", "2.0.0"),
        row_number=0,
    )
    assert result.branch == "product_only"
    assert result.module is None
    assert result.product == "Fixture Product"
    assert _selected_page_type(result, None) == "product_overview"


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda row: row.update(product=""), "PRODUCT_ONLY_MISSING_PRODUCT"),
        (lambda row: row.update(object_intent=""), "PRODUCT_ONLY_MISSING_OBJECT_INTENT"),
        (lambda row: row.update(module="invented"), "PRODUCT_ONLY_MODULE_FORBIDDEN"),
        (lambda row: row.update(status="degraded"), "PRODUCT_ONLY_INVALID_STATUS"),
    ],
)
def test_product_only_rejections_are_structured_degraded(change, expected: str) -> None:
    row = _row()
    change(row)
    result = adapt_topic_index_row(
        row,
        source_ref=ArtifactRef("topic-index", "topic-index.json", "fixture", "a" * 64, "2.0.0", "2.0.0"),
        row_number=0,
    )
    assert result.branch == "degraded"
    assert expected in result.error_codes


def test_validator_checks_status_layers_and_artifact_containment(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    report = project_reader_bundle(inputs, artifacts)
    assert report.report.release_status == "not_released"
    checked = validate_reader_bundle(artifacts, inputs)
    assert checked.status == "passed"
    assert checked.artifact_root_ref == str(artifacts.artifact_root)
    concept = next(path for path in (artifacts.bundle_dir / "products").rglob("*.md") if path.name != "index.md")
    frontmatter, _body = parse_concept_document(concept.read_text(encoding="utf-8"))
    assert frontmatter["status"] == "draft"
    assert frontmatter["digest_page_status"] == "published"
    assert frontmatter["digest_machine_pass"] is True
    assert frontmatter["generated"]["by"] == "knowledge-digest/reader-bundle/1"
    assert frontmatter.get("verified") in (None, [])
    for field in ("stale_after", "digest_release_status"):
        assert field not in frontmatter


def _concept_pages(artifacts: BundleArtifactPaths) -> list[Path]:
    return sorted(
        path
        for path in (artifacts.bundle_dir / "products").rglob("*.md")
        if path.name != "index.md"
    )


def test_full_fixture_emits_positive_trust_signals_and_audit_evidence(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    committed = project_reader_bundle(inputs, artifacts)
    assert committed.report.release_status == "not_released"
    assert validate_reader_bundle(artifacts, inputs).status == "passed"

    pages = _concept_pages(artifacts)
    assert len(pages) == 3
    for page in pages:
        frontmatter, _body = parse_concept_document(page.read_text(encoding="utf-8"))
        assert frontmatter["generated"]["by"] == "knowledge-digest/reader-bundle/1"
        assert frontmatter["generated"]["at"].endswith("Z")
        assert frontmatter["digest_machine_pass"] is True
        assert {event["event"] for event in frontmatter["verified"]} == {"source_hash_match", "locator_resolved"}
        for event in frontmatter["verified"]:
            assert event["actor"] == f"process:knowledge-digest-{event['event']}-v1"
            assert event["detector_version"] == "v1"
            assert event["input_fingerprints"]
            assert event["content_hash"] == frontmatter["digest_content_hash"]
            evidence = artifacts.artifact_root / event["evidence_ref"]
            assert evidence.is_file()
            audit = json.loads(evidence.read_text(encoding="utf-8"))
            assert audit["content_hash"] == frontmatter["digest_content_hash"]
            assert event in audit["events"]
        assert "stale_after" not in frontmatter
        assert all(event["actor"] != "human:reviewer" for event in frontmatter["verified"])


def test_trust_signals_fail_closed_after_content_or_event_mutation(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    concept = _concept_pages(artifacts)[0]
    frontmatter, body = parse_concept_document(concept.read_text(encoding="utf-8"))
    concept.write_text(serialize_concept_document(frontmatter, body + "\nMutation.\n"), encoding="utf-8")
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert "MANAGED_HASH_MISMATCH" in codes
    assert "TRUST_SIGNAL_CONTENT_HASH_MISMATCH" in codes

    second_inputs = _full_inputs(tmp_path / "second")
    second_artifacts = BundleArtifactPaths.from_root(tmp_path / "second-artifact-root")
    project_reader_bundle(second_inputs, second_artifacts)
    second_concept = _concept_pages(second_artifacts)[0]
    frontmatter, body = parse_concept_document(second_concept.read_text(encoding="utf-8"))
    frontmatter["verified"][0]["actor"] = "human:reviewer"
    second_concept.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    codes = validate_reader_bundle(second_artifacts, second_inputs).error_codes
    assert "TRUST_SIGNAL_ACTOR_FORBIDDEN" in codes
    assert "TRUST_SIGNAL_EVIDENCE_MISMATCH" in codes


@pytest.mark.parametrize("mutation", ["source_fingerprint", "locator", "target_path", "page_type"])
def test_trust_signals_reject_provenance_and_page_mutations(tmp_path: Path, mutation: str) -> None:
    inputs = _full_inputs(tmp_path / mutation)
    artifacts = BundleArtifactPaths.from_root(tmp_path / f"artifact-root-{mutation}")
    project_reader_bundle(inputs, artifacts)
    concept = _concept_pages(artifacts)[0]
    frontmatter, body = parse_concept_document(concept.read_text(encoding="utf-8"))
    if mutation == "source_fingerprint":
        frontmatter["sources"][0]["digest_content_fingerprint"] = "0" * 64
    elif mutation == "locator":
        frontmatter["sources"][0]["digest_claims"][0]["fragment_locator"] = "lines:999-999"
    elif mutation == "target_path":
        frontmatter["sources"][0]["digest_claims"][0]["target_path"] = "pages/mutated.md"
    else:
        frontmatter["digest_page_type"] = "procedure_or_rule"
    concept.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert "TRUST_SIGNAL_CONTENT_HASH_MISMATCH" in codes


def test_explicit_freshness_is_projected_and_invalid_date_fails(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path / "valid")
    inventory = inputs.input_root / "source-inventory.jsonl"
    rows = [json.loads(line) for line in inventory.read_text(encoding="utf-8").splitlines()]
    rows[0]["source_meta"] = {"stale_after": "2026-12-31"}
    inventory.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    valid_inputs = replace(inputs, source_inventory_ref=_ref(inputs.input_root, "source-inventory.jsonl", "source-inventory", "task1-real-corpus-verification.v1", "2026-08-06"))
    valid_artifacts = BundleArtifactPaths.from_root(tmp_path / "valid-artifacts")
    project_reader_bundle(valid_inputs, valid_artifacts)
    frontmatter = next(
        parse_concept_document(path.read_text(encoding="utf-8"))[0]
        for path in _concept_pages(valid_artifacts)
        if parse_concept_document(path.read_text(encoding="utf-8"))[0]["sources"][0]["id"] == "source-fixture-product"
    )
    assert frontmatter["stale_after"] == "2026-12-31"

    invalid_inventory = inputs.input_root / "source-inventory.jsonl"
    rows[0]["source_meta"] = {"stale_after": "2026-02-30"}
    invalid_inventory.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    invalid_inputs = replace(inputs, source_inventory_ref=_ref(inputs.input_root, "source-inventory.jsonl", "source-inventory", "task1-real-corpus-verification.v1", "2026-08-06"))
    with pytest.raises(ValidationError, match="explicit freshness date is invalid"):
        project_reader_bundle(invalid_inputs, BundleArtifactPaths.from_root(tmp_path / "invalid-artifacts"))


def test_validator_reconciles_frontmatter_and_audit_without_input_context(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    concept = _concept_pages(artifacts)[0]
    frontmatter, body = parse_concept_document(concept.read_text(encoding="utf-8"))
    del frontmatter["verified"]
    concept.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    assert "TRUST_SIGNAL_EVIDENCE_MISMATCH" in validate_reader_bundle(artifacts, None).error_codes


def test_entry_readback_reports_missing_refs_without_fabricating_success(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    check = check_entry_bindings(inputs)
    assert check.status == "backfill_required"
    artifacts = BundleArtifactPaths.from_root(tmp_path / "backfill-artifacts")
    result = write_entry_backfill_manifest(check, artifacts, run_id="run-test")
    manifest = artifacts.audit_dir / "entry-backfill" / "run-test.json"
    assert result.status == "backfill_required"
    assert result.path == "audit/entry-backfill/run-test.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["digest_release_status"] == "not_released"
    assert check.consumer == "reader-bundle"


def test_initial_commit_returns_real_base_hashes_and_cleans_staging(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    committed = project_reader_bundle(inputs, artifacts)
    assert committed.base_bundle_hash == hashlib.sha256(
        b"".join(
            path.relative_to(artifacts.bundle_dir).as_posix().encode() + b"\0" + path.read_bytes() + b"\0"
            for path in sorted(path for path in artifacts.bundle_dir.rglob("*") if path.is_file())
        )
    ).hexdigest()
    assert committed.base_projection_report_hash == hashlib.sha256(artifacts.projection_report_path.read_bytes()).hexdigest()
    assert committed.base_exit_manifest_hash == hashlib.sha256(artifacts.exit_manifest_path.read_bytes()).hexdigest()
    assert not (artifacts.artifact_root / ".staging").exists()
    exit_manifest = json.loads(artifacts.exit_manifest_path.read_text(encoding="utf-8"))
    assert exit_manifest["bundle_hash"] == committed.base_bundle_hash
    projection = json.loads(artifacts.projection_report_path.read_text(encoding="utf-8"))
    assert committed.report.entry_binding == projection["entry_binding"]
    assert committed.report.concept_count == projection["concept_count"]
    assert committed.report.source_count == projection["source_count"]
    assert committed.report.claim_count == projection["claim_count"]


def test_validator_rejects_hash_release_status_and_navigation_mutations(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    concept = next(path for path in (artifacts.bundle_dir / "products").rglob("*.md") if path.name != "index.md")
    frontmatter, body = parse_concept_document(concept.read_text(encoding="utf-8"))
    frontmatter["description"] = "mutated without updating the managed hash"
    concept.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    assert "MANAGED_HASH_MISMATCH" in validate_reader_bundle(artifacts, inputs).error_codes

    frontmatter, body = parse_concept_document(concept.read_text(encoding="utf-8"))
    frontmatter["digest_release_status"] = "released"
    concept.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert "RELEASE_STATUS_ON_CONCEPT" in codes

    (artifacts.bundle_dir / "Home.md").write_text("# Home\n\n[Reader index](../outside.md)\n", encoding="utf-8")
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert "LINK_ESCAPES_BUNDLE" in codes

    (artifacts.bundle_dir / "Home.md").write_text("# Home\n\n[Reader index](index.md)\n", encoding="utf-8")
    index = artifacts.bundle_dir / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\n[Section](#section)\n", encoding="utf-8")
    assert "LINK_ESCAPES_BUNDLE" not in validate_reader_bundle(artifacts, inputs).error_codes

    (artifacts.bundle_dir / "Home.md").write_text("---\ntype: KnowledgeDigest Product Overview\n---\n# Home\n\n[Reader index](index.md)\n", encoding="utf-8")
    assert "EXEMPT_FILE_FRONTMATTER" in validate_reader_bundle(artifacts, inputs).error_codes


def test_validator_rejects_audit_escape_empty_index_and_missing_target(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(inputs, artifacts)
    (artifacts.bundle_dir / "_digest").mkdir()
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert "BUNDLE_AUDIT_ESCAPE" in codes

    shutil.rmtree(artifacts.bundle_dir / "_digest")
    nested_audit = artifacts.bundle_dir / "products" / "fixture-product" / "_archive"
    nested_audit.mkdir(parents=True)
    assert "BUNDLE_AUDIT_ESCAPE" in validate_reader_bundle(artifacts, inputs).error_codes
    nested_audit.rmdir()
    (artifacts.bundle_dir / "index.md").write_text("# Reader index\n", encoding="utf-8")
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert any(code.startswith("EMPTY_INDEX:index.md") for code in codes)

    (artifacts.bundle_dir / "Home.md").write_text("# Home\n\n[Reader index](missing.md)\n", encoding="utf-8")
    assert "LINK_TARGET_MISSING" in validate_reader_bundle(artifacts, inputs).error_codes

    nested_log = artifacts.bundle_dir / "products" / "nested-log.md"
    nested_log.write_text("# nested\n", encoding="utf-8")
    nested_log.rename(nested_log.with_name("log.md"))
    nested_index = artifacts.bundle_dir / "products" / "nested-index.md"
    nested_index.write_text("---\ntype: KnowledgeDigest Product Overview\n---\n# nested\n", encoding="utf-8")
    nested_index.rename(nested_index.with_name("index.md"))
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert "NESTED_LOG_FORBIDDEN" in codes
    assert "NESTED_INDEX_FRONTMATTER" in codes

    (artifacts.bundle_dir / "index.md").write_text("---\ntype: KnowledgeDigest Product Overview\n---\n# Reader index\n", encoding="utf-8")
    assert "ROOT_INDEX_FRONTMATTER" in validate_reader_bundle(artifacts, inputs).error_codes


def test_entry_hash_path_and_symlink_fail_closed(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    stale = replace(inputs, entry_manifest_refs=(ArtifactRef("entry", "topic-index.json", "stale", "0" * 64, "entry.v1", "1"),))
    stale_check = check_entry_bindings(stale)
    assert stale_check.status == "blocked"
    assert stale_check.missing_refs

    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    symlink = inputs.input_root / "link.json"
    symlink.symlink_to(outside)
    escaped = replace(inputs, entry_manifest_refs=(ArtifactRef("entry", "../outside.json", "escape", "a" * 64, "entry.v1", "1"),))
    assert check_entry_bindings(escaped).status == "blocked"
    linked = replace(inputs, entry_manifest_refs=(ArtifactRef("entry", "link.json", "link", "a" * 64, "entry.v1", "1"),))
    assert check_entry_bindings(linked).status == "blocked"

    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
    (outside_dir / "source-inventory.jsonl").write_bytes((inputs.input_root / "source-inventory.jsonl").read_bytes())
    linked_dir = inputs.input_root / "linked-dir"
    linked_dir.symlink_to(outside_dir, target_is_directory=True)
    linked_parent = replace(inputs, source_inventory_ref=ArtifactRef(
        "source-inventory", "linked-dir/source-inventory.jsonl", "linked-parent",
        hashlib.sha256((outside_dir / "source-inventory.jsonl").read_bytes()).hexdigest(),
        "source-inventory.v1", "1",
    ))
    with pytest.raises(ValidationError, match="symlink"):
        project_reader_bundle(linked_parent, BundleArtifactPaths.from_root(tmp_path / "linked-parent-artifacts"))

    unsupported = inputs.input_root / "unsupported-entry.json"
    unsupported.write_text(json.dumps({"status": "mystery"}), encoding="utf-8")
    unsupported_inputs = replace(inputs, entry_manifest_refs=(ArtifactRef("entry", unsupported.name, "unsupported", hashlib.sha256(unsupported.read_bytes()).hexdigest(), "entry.v1", "1"),))
    unsupported_check = check_entry_bindings(unsupported_inputs)
    assert unsupported_check.missing_refs == ("unsupported-entry.json:ENTRY_STATUS_UNSUPPORTED",)
    assert unsupported_check.bindings[0]["error"] == "ENTRY_STATUS_UNSUPPORTED"


def test_entry_coverage_mismatch_fails_closed(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    coverage_path = inputs.input_root / "sample-coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage["inventory_coverage"]["source_count"] = 88
    coverage_path.write_text(json.dumps(coverage), encoding="utf-8")
    refs = tuple(
        replace(ref, hash=hashlib.sha256((inputs.input_root / ref.ref).read_bytes()).hexdigest())
        if ref.ref == "sample-coverage.json" else ref
        for ref in inputs.entry_manifest_refs
    )
    check = check_entry_bindings(replace(inputs, entry_manifest_refs=refs))
    assert check.status == "blocked"
    assert "sample-coverage.json:ENTRY_COVERAGE_MISMATCH" in check.missing_refs


def test_entry_producer_missing_fails_closed(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    backfill_path = inputs.input_root / "entry-backfill.json"
    backfill = json.loads(backfill_path.read_text(encoding="utf-8"))
    del backfill["generated_by"]["process"]
    backfill_path.write_text(json.dumps(backfill), encoding="utf-8")
    refs = tuple(
        replace(ref, hash=hashlib.sha256((inputs.input_root / ref.ref).read_bytes()).hexdigest())
        if ref.ref == "entry-backfill.json" else ref
        for ref in inputs.entry_manifest_refs
    )
    check = check_entry_bindings(replace(inputs, entry_manifest_refs=refs))
    assert check.status == "blocked"
    assert "entry-backfill.json:ENTRY_PRODUCER_MISSING" in check.missing_refs


def test_missing_description_degrades_instead_of_publishing_placeholder(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    topic_path = inputs.input_root / "topic-index.json"
    topic = json.loads(topic_path.read_text(encoding="utf-8"))
    topic["topics"][0]["description"] = None
    topic_path.write_text(json.dumps(topic), encoding="utf-8")
    updated = replace(inputs, topic_index_ref=_ref(inputs.input_root, "topic-index.json", "topic-index", "2.0.0", "2.0.0"))
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    project_reader_bundle(updated, artifacts)
    report = json.loads(artifacts.projection_report_path.read_text(encoding="utf-8"))
    assert any("TITLE_OR_DESCRIPTION_UNREADABLE" in row["error_codes"] for row in report["degraded_records"])
    assert all("for Fixture Product." not in path.read_text(encoding="utf-8") for path in (artifacts.bundle_dir / "products").rglob("*.md"))


def test_slug_path_collision_fails_closed(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    topic_path = inputs.input_root / "topic-index.json"
    topic = json.loads(topic_path.read_text(encoding="utf-8"))
    duplicate = dict(topic["topics"][0])
    duplicate["topic_id"] = "digest-topic-product-overview-duplicate"
    duplicate["digest_topic_id"] = "digest-topic-product-overview-duplicate"
    duplicate["topic_key"] = "v2/products/fixture-product/product-overview-duplicate"
    topic["topics"].append(duplicate)
    topic_path.write_text(json.dumps(topic), encoding="utf-8")
    updated = replace(inputs, topic_index_ref=_ref(inputs.input_root, "topic-index.json", "topic-index", "2.0.0", "2.0.0"))
    with pytest.raises(ValidationError, match="collides after slug normalization"):
        project_reader_bundle(updated, BundleArtifactPaths.from_root(tmp_path / "artifact-root"))


def test_changed_fixture_provenance_fails_closed_before_publishing(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    selection_path = inputs.input_root / "fixture-selection.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selection["fixtures"][0]["content_fingerprint"] = "0" * 64
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    mutated = replace(inputs, fixture_selection_ref=_ref(inputs.input_root, "fixture-selection.json", "fixture-selection", "task2a-fixture-selection.v1", "2026-08-09"))
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    with pytest.raises(ValidationError, match="fingerprint"):
        project_reader_bundle(mutated, artifacts)
    assert not artifacts.bundle_dir.exists()
    assert not (artifacts.artifact_root / ".staging").exists()


def test_malformed_fixture_selection_without_sample_id_is_structured(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    selection_path = inputs.input_root / "fixture-selection.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    del selection["fixtures"][0]["sample_id"]
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    mutated = replace(inputs, fixture_selection_ref=_ref(inputs.input_root, "fixture-selection.json", "fixture-selection", "task2a-fixture-selection.v1", "2026-08-09"))
    with pytest.raises(ValidationError, match="missing sample_id"):
        project_reader_bundle(mutated, BundleArtifactPaths.from_root(tmp_path / "artifact-root"))


def test_malformed_fixture_selection_without_selection_reason_is_structured(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    selection_path = inputs.input_root / "fixture-selection.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    del selection["fixtures"][0]["selection_reason"]
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    mutated = replace(inputs, fixture_selection_ref=_ref(inputs.input_root, "fixture-selection.json", "fixture-selection", "task2a-fixture-selection.v1", "2026-08-09"))
    with pytest.raises(ValidationError, match="missing selection_reason"):
        project_reader_bundle(mutated, BundleArtifactPaths.from_root(tmp_path / "artifact-root"))


def test_fixture_mapping_role_must_match_topic_branch(tmp_path: Path) -> None:
    adapter = adapt_topic_index_row(
        _row(),
        source_ref=ArtifactRef("topic-index", "topic-index.json", "fixture", "a" * 64, "2.0.0", "2.0.0"),
        row_number=0,
    )
    with pytest.raises(ValidationError, match="conflicts with TopicIndex branch"):
        _selected_page_type(adapter, {"mapping_role": "module_or_capability"})


def test_projection_is_replay_stable_and_mutated_provenance_fails_closed(tmp_path: Path) -> None:
    first_inputs = _inputs(tmp_path / "first")
    first_artifacts = BundleArtifactPaths.from_root(tmp_path / "first-artifacts")
    first = project_reader_bundle(first_inputs, first_artifacts)
    second_inputs = _inputs(tmp_path / "second")
    second_artifacts = BundleArtifactPaths.from_root(tmp_path / "second-artifacts")
    second = project_reader_bundle(second_inputs, second_artifacts)
    assert first.run_id != second.run_id
    assert (first_artifacts.bundle_dir / "index.md").read_bytes() == (second_artifacts.bundle_dir / "index.md").read_bytes()
    assert first.report.release_status == second.report.release_status == "not_released"


def test_commit_failure_rolls_back_all_artifact_surfaces(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifact-root")
    committed = project_reader_bundle(inputs, artifacts)
    old_hashes = {
        "bundle": committed.base_bundle_hash,
        "projection": committed.base_projection_report_hash,
        "exit": committed.base_exit_manifest_hash,
    }
    staging = artifacts.artifact_root / ".staging" / "run-next"
    for name in ("bundle", "audit", "reports"):
        (staging / name).mkdir(parents=True)
        (staging / name / "replacement.txt").write_text(name, encoding="utf-8")
    real_replace = __import__("os").replace

    def fail_audit_install(source: str, destination: str) -> None:
        if str(source).startswith(str(staging)) and str(destination).endswith("/audit"):
            raise OSError("injected audit install failure")
        real_replace(source, destination)

    monkeypatch.setattr("knowledge_digest.reader_bundle.os.replace", fail_audit_install)
    with pytest.raises(OSError, match="injected audit install failure"):
        _atomic_commit(staging, artifacts)
    assert hashlib.sha256(
        b"".join(path.relative_to(artifacts.bundle_dir).as_posix().encode() + b"\0" + path.read_bytes() + b"\0" for path in sorted(path for path in artifacts.bundle_dir.rglob("*") if path.is_file()))
    ).hexdigest() == old_hashes["bundle"]
    assert hashlib.sha256(artifacts.projection_report_path.read_bytes()).hexdigest() == old_hashes["projection"]
    assert hashlib.sha256(artifacts.exit_manifest_path.read_bytes()).hexdigest() == old_hashes["exit"]
    assert not (artifacts.artifact_root / ".staging").exists()


def test_existing_cli_offline_path_is_zero_provider(tmp_path: Path) -> None:
    new_dir = tmp_path / "new"
    kb_dir = tmp_path / "kb"
    (new_dir / "items").mkdir(parents=True)
    (new_dir / "items" / "note.md").write_text("# Note\n\nOffline fixture.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "note.md", "source_uri": "raw://fixture/note.md"}) + "\n",
        encoding="utf-8",
    )
    config = tmp_path / "offline.json"
    config.write_text(json.dumps({"similarity": {"backend": "jaccard"}, "llm_enabled": False, "llm_summary_enabled": False, "max_lines": 300}), encoding="utf-8")
    guard_dir = tmp_path / "socket-guard"
    guard_dir.mkdir()
    guard_result = guard_dir / "result.json"
    (guard_dir / "sitecustomize.py").write_text(
        "import atexit, hashlib, json, os, socket, sys\n"
        "from pathlib import Path\n"
        "attempts = 0\n"
        "def deny_connect(self, address):\n"
        "    global attempts\n"
        "    attempts += 1\n"
        "    raise OSError('deny-only socket guard')\n"
        "socket.socket.connect = deny_connect\n"
        "def write_result():\n"
        "    argv = ['<abs>' if value.startswith('/') else value for value in sys.argv]\n"
        "    argv_sha256 = hashlib.sha256(json.dumps(argv, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()\n"
        "    Path(os.environ['KNOWLEDGEDIGEST_SOCKET_GUARD_RESULT']).write_text(json.dumps({'attempt_ref': os.environ['KNOWLEDGEDIGEST_SOCKET_GUARD_ATTEMPT'], 'argv': argv, 'argv_sha256': argv_sha256, 'guard_mode': 'deny-only', 'connect_attempts': attempts}), encoding='utf-8')\n"
        "atexit.register(write_result)\n",
        encoding="utf-8",
    )
    argv = ["uv", "run", "--frozen", "digest", str(new_dir), str(kb_dir), "--config", str(config), "--no-llm"]
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{guard_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["KNOWLEDGEDIGEST_SOCKET_GUARD_RESULT"] = str(guard_result)
    env["KNOWLEDGEDIGEST_SOCKET_GUARD_ATTEMPT"] = "test-existing-cli-offline-path"
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    run_reports = sorted((kb_dir / "_digest" / "runs").glob("*/report.json"))
    assert run_reports
    runtime = json.loads(run_reports[-1].read_text(encoding="utf-8"))["runtime_audit"]
    assert runtime["calls"] == {"llm": 0, "embedding": 0}
    guard = json.loads(guard_result.read_text(encoding="utf-8"))
    assert guard["argv"][-1] == "--no-llm"
    assert "--config" in guard["argv"]
    assert len(guard["argv_sha256"]) == 64
    assert guard["argv_sha256"] == hashlib.sha256(json.dumps(guard["argv"], ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    assert guard["guard_mode"] == "deny-only"
    assert guard["connect_attempts"] == 0


def test_real_selected_fixtures_close_footnote_to_claim_and_replay(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    first_artifacts = BundleArtifactPaths.from_root(tmp_path / "real-artifacts")
    first = project_reader_bundle(inputs, first_artifacts)
    assert first.report.release_status == "not_released"
    projection = json.loads(first_artifacts.projection_report_path.read_text(encoding="utf-8"))
    assert projection["entry_binding"]["status"] == "passed"
    assert projection["entry_binding"]["backfill_ref"] is None
    checked = validate_reader_bundle(first_artifacts, inputs)
    assert checked.status == "passed", checked.error_codes
    assert checked.claim_count == 3
    pages = sorted((first_artifacts.bundle_dir / "products").rglob("*.md"))
    assert any("src-43-dc" in page.read_text(encoding="utf-8") for page in pages)
    assert any("src-16-dataset" in page.read_text(encoding="utf-8") for page in pages)
    assert any("src-17-build" in page.read_text(encoding="utf-8") for page in pages)
    selection = json.loads((FIXTURE_ROOT / "fixture-selection.json").read_text(encoding="utf-8"))
    expected_claims = {
        claim_id
        for fixture in selection["fixtures"]
        for claim_id in fixture["claim_ids"]
    }
    observed_claims: set[str] = set()
    for page in pages:
        if page.name == "index.md":
            continue
        frontmatter, body = parse_concept_document(page.read_text(encoding="utf-8"))
        assert frontmatter["digest_page_status"] == "published"
        if "[^" not in body:
            continue
        for source in frontmatter["sources"]:
            assert source["resource"]
            assert source["digest_content_fingerprint"]
            assert source["digest_claims"]
            for claim in source["digest_claims"]:
                observed_claims.add(claim["claim_id"])
                assert claim["fragment_locator"]
                assert claim["target_path"]
                assert claim["content_fingerprint"] == source["digest_content_fingerprint"]
    assert observed_claims == expected_claims
    for index in sorted((first_artifacts.bundle_dir / "products").glob("*/index.md")):
        product_index_text = index.read_text(encoding="utf-8")
        assert product_index_text.startswith("# ")
        assert "fixture-" not in product_index_text.splitlines()[0]
        module_links = [line for line in index.read_text(encoding="utf-8").splitlines() if "(modules/" in line]
        assert len(module_links) == len(set(module_links))
        assert all(" — " in line for line in module_links)
    modules_index = next(first_artifacts.bundle_dir.glob("products/*/modules/index.md"))
    assert "fixture-module" not in modules_index.read_text(encoding="utf-8").splitlines()[0]
    assert any("(16/index.md)" in line or "(17/index.md)" in line for line in modules_index.read_text(encoding="utf-8").splitlines())
    root_index = (first_artifacts.bundle_dir / "index.md").read_text(encoding="utf-8")
    product_links = [line for line in root_index.splitlines() if line.startswith("- [")]
    assert product_links
    assert all(" — " in line for line in product_links)
    assert all("fixture-" not in line.split("]", 1)[0] for line in product_links)


def test_validator_rejects_bundle_symlinks_and_non_allowlisted_files(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "allowlist-artifacts")
    project_reader_bundle(inputs, artifacts)
    (artifacts.bundle_dir / "provider-response.json").write_text("{}", encoding="utf-8")
    target = next(path for path in (artifacts.bundle_dir / "products").rglob("*.md") if path.name != "index.md")
    symlink = artifacts.bundle_dir / "products" / "linked.md"
    symlink.symlink_to(target)
    codes = validate_reader_bundle(artifacts, inputs).error_codes
    assert "BUNDLE_FILE_NOT_ALLOWLISTED" in codes
    assert "BUNDLE_SYMLINK_FORBIDDEN" in codes


def test_validator_rejects_incomplete_claim_provenance(tmp_path: Path) -> None:
    inputs = _full_inputs(tmp_path)
    artifacts = BundleArtifactPaths.from_root(tmp_path / "provenance-artifacts")
    project_reader_bundle(inputs, artifacts)
    concept = next(path for path in (artifacts.bundle_dir / "products").rglob("*.md") if path.name != "index.md")
    frontmatter, body = parse_concept_document(concept.read_text(encoding="utf-8"))
    frontmatter["sources"][0]["digest_claims"][0]["fragment_locator"] = ""
    concept.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
    assert "CLAIM_PROVENANCE_INCOMPLETE" in validate_reader_bundle(artifacts, inputs).error_codes
