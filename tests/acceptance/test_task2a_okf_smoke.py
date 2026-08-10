from __future__ import annotations

import hashlib
import json
import shutil
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from knowledge_digest.errors import ValidationError
from knowledge_digest.okf_smoke import (
    ParserSmokeResult,
    ParserVendorRef,
    create_smoke_attempt,
    read_vendor_ref,
    run_parser_smoke,
)
from knowledge_digest.reader_bundle import (
    ArtifactRef,
    BundleArtifactPaths,
    BundleReport,
    CommittedBundleRun,
    ReaderBundleStructureInputs,
    finalize_bundle_profile,
    project_reader_bundle,
)


FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "task2a_reader_bundle"
VENDOR_ROOT = Path(__file__).parents[2] / "tests" / "vendor" / "okf_reference_agent"


@pytest.fixture(autouse=True)
def deny_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden in parser smoke acceptance")

    monkeypatch.setattr(socket, "socket", denied_socket)
    monkeypatch.setattr(socket, "create_connection", denied_socket)
    monkeypatch.setattr(socket, "getaddrinfo", denied_socket)


def _bundle(tmp_path: Path) -> BundleArtifactPaths:
    inputs_root = tmp_path / "inputs"
    inputs_root.mkdir()
    for name in ("topic-index.json", "source-inventory.jsonl"):
        shutil.copy2(FIXTURE_ROOT / name, inputs_root / name)

    def ref(name: str, kind: str, schema: str) -> ArtifactRef:
        path = inputs_root / name
        return ArtifactRef(kind, name, f"fixture-{name}", hashlib.sha256(path.read_bytes()).hexdigest(), schema, "test")

    inputs = ReaderBundleStructureInputs(
        schema_version="reader-bundle-structure-inputs.v1",
        input_root=inputs_root,
        topic_index_ref=ref("topic-index.json", "topic-index", "2.0.0"),
        source_inventory_ref=ref("source-inventory.jsonl", "source-inventory", "task1-real-corpus-verification.v1"),
        entry_manifest_refs=(),
        offline_mode="no-llm",
    )
    artifacts = BundleArtifactPaths.from_root(tmp_path / "artifacts")
    project_reader_bundle(inputs, artifacts)
    return artifacts


def _vendor(tmp_path: Path, *, failing: bool = False) -> ParserVendorRef:
    root = tmp_path / "vendor"
    (root / "bundle").mkdir(parents=True)
    document = (
        "from dataclasses import dataclass\n"
        "import yaml\n"
        "@dataclass\n"
        "class OKFDocument:\n"
        "    frontmatter: dict\n"
        "    body: str\n"
        "    @classmethod\n"
        "    def parse(cls, text):\n"
        + ("        raise ValueError('fixture parser failure')\n" if failing else "        lines = text.splitlines()\n        if lines and lines[0].strip() == '---':\n            end = lines.index('---', 1)\n            return cls(yaml.safe_load('\\n'.join(lines[1:end])) or {}, '\\n'.join(lines[end + 1:]))\n        return cls({}, text)\n")
        + "    def validate(self):\n        if not self.frontmatter.get('type'):\n            raise ValueError('missing type')\n"
    )
    (root / "bundle" / "document.py").write_text(document, encoding="utf-8")
    (root / "bundle" / "index.py").write_text("# local parser fixture\n", encoding="utf-8")
    (root / "bundle" / "paths.py").write_text("def parse_concept_id(value):\n    return tuple(value.split('/'))\n", encoding="utf-8")
    (root / "LICENSE").write_text("local license fixture\n", encoding="utf-8")
    (root / "NOTICE.md").write_text("local notice fixture\n", encoding="utf-8")
    (root / "README.md").write_text(
        "source_ref: https://example.invalid/okf\n"
        "source_commit: " + "1" * 40 + "\n"
        "license_ref: LICENSE\n"
        "notice_ref: NOTICE.md\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256()
    for relative in ("bundle/document.py", "bundle/index.py", "bundle/paths.py"):
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update((root / relative).read_bytes())
        digest.update(b"\0")
    return ParserVendorRef(
        source_ref="https://example.invalid/okf",
        source_commit="1" * 40,
        vendor_root=root,
        vendor_hash=digest.hexdigest(),
        license_ref="LICENSE",
        license_hash=hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest(),
        notice_ref="NOTICE.md",
        notice_hash=hashlib.sha256((root / "NOTICE.md").read_bytes()).hexdigest(),
        read_boundary=("bundle/document.py", "bundle/index.py", "bundle/paths.py"),
    )


def test_parser_compatible_writes_profile_and_version(tmp_path: Path) -> None:
    artifacts = _bundle(tmp_path)
    vendor = _vendor(tmp_path)
    attempt = create_smoke_attempt(artifacts.artifact_root, vendor)
    result = run_parser_smoke(artifacts.artifact_root, vendor, attempt)
    assert result.status == "passed"
    assert result.source_commit == vendor.source_commit
    assert result.vendor_hash == vendor.vendor_hash
    assert result.license_hash == vendor.license_hash
    assert result.notice_hash == vendor.notice_hash


def test_pinned_vendor_readback_and_compatibility_profile(tmp_path: Path) -> None:
    artifacts = _bundle(tmp_path)
    committed = _committed_for_recovery(artifacts)
    vendor = read_vendor_ref(VENDOR_ROOT)
    assert vendor.source_commit == "930b65fc3f5619d5d0591f88c72ebae8b848d60d"
    assert vendor.license_hash == "8c6db340475136df3c1201d458fa5755698eace76e510471ecc9d857d6083dac"
    attempt = create_smoke_attempt(committed.artifact_root, vendor)
    result = run_parser_smoke(committed.artifact_root, vendor, attempt)
    assert result.status == "passed"
    report = finalize_bundle_profile(committed, result)
    assert report.profile == "OKF-compatible"
    assert report.ac08_result == "compatibility_passed"
    assert "okf_version: \"0.2\"" in (artifacts.bundle_dir / "index.md").read_text(encoding="utf-8")
    manifest = json.loads(artifacts.exit_manifest_path.read_text(encoding="utf-8"))
    assert manifest["ac08_result"] == "compatibility_passed"
    assert manifest["parser_smoke"]["bundle_hash"] == manifest["bundle_hash"]
    assert manifest["parser_smoke"]["attempt_ref"] != attempt.attempt_ref
    assert manifest["parser_smoke"]["read_summary"]["expected_unknown_extension_behavior"] == "report_observed_without_silent_drop"
    assert manifest["parser_smoke"]["read_summary"]["expected_unknown_type_behavior"].startswith("external_parser_accepts_nonempty_type")


def test_parser_downgrade_is_honest_and_not_compatibility(tmp_path: Path) -> None:
    artifacts = _bundle(tmp_path)
    downgrade_inputs = tmp_path / "downgrade-inputs"
    downgrade_inputs.mkdir()
    for name in ("topic-index.json", "source-inventory.jsonl"):
        shutil.copy2(FIXTURE_ROOT / name, downgrade_inputs / name)
    committed = project_reader_bundle(
        ReaderBundleStructureInputs(
            schema_version="reader-bundle-structure-inputs.v1",
            input_root=downgrade_inputs,
            topic_index_ref=ArtifactRef("topic-index", "topic-index.json", "fixture-topic-index.json", hashlib.sha256((downgrade_inputs / "topic-index.json").read_bytes()).hexdigest(), "2.0.0", "test"),
            source_inventory_ref=ArtifactRef("source-inventory", "source-inventory.jsonl", "fixture-source-inventory.jsonl", hashlib.sha256((downgrade_inputs / "source-inventory.jsonl").read_bytes()).hexdigest(), "task1-real-corpus-verification.v1", "test"),
            entry_manifest_refs=(),
            offline_mode="no-llm",
        ),
        BundleArtifactPaths.from_root(tmp_path / "downgrade-artifacts"),
    )
    failing_vendor = _vendor(tmp_path / "failing", failing=True)
    attempt = create_smoke_attempt(committed.artifact_root, failing_vendor)
    result = run_parser_smoke(committed.artifact_root, failing_vendor, attempt)
    assert result.status in {"failed", "unavailable"}
    assert result.reason
    from knowledge_digest.reader_bundle import finalize_bundle_profile

    report = finalize_bundle_profile(committed, result)
    assert report.profile == "OKF-inspired profile"
    assert report.ac08_result == "honest_downgrade_passed"
    committed_bundle = Path(committed.artifact_root) / "bundle"
    downgraded_index = (committed_bundle / "index.md").read_text(encoding="utf-8")
    assert "okf_version" not in downgraded_index
    manifest = json.loads((Path(committed.artifact_root) / "reports" / "exit-manifest.json").read_text(encoding="utf-8"))
    assert manifest["ac08_result"] == "honest_downgrade_passed"
    assert manifest["profile"] == "OKF-inspired profile"
    assert manifest["reason"].startswith("parser smoke failed:")


def test_parser_finalize_recovery_rejects_incomplete_provenance_without_writes(tmp_path: Path) -> None:
    artifacts = _bundle(tmp_path)
    before = {
        path.relative_to(artifacts.artifact_root).as_posix(): path.read_bytes()
        for path in artifacts.artifact_root.rglob("*")
        if path.is_file()
    }
    incomplete = ParserSmokeResult(
        schema_version="okf-parser-smoke.v1",
        status="passed",
        source_ref="",
        attempt_ref="",
        source_commit="",
        vendor_hash="",
        license_hash="",
        notice_hash="",
        bundle_hash="",
        read_boundary=(),
        read_summary={},
        reason=None,
    )
    with pytest.raises(ValidationError):
        from knowledge_digest.reader_bundle import finalize_bundle_profile

        finalize_bundle_profile(_committed_for_recovery(artifacts), incomplete)
    after = {
        path.relative_to(artifacts.artifact_root).as_posix(): path.read_bytes()
        for path in artifacts.artifact_root.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_parser_finalize_records_blocked_fact_without_claiming_downgrade(tmp_path: Path) -> None:
    artifacts = _bundle(tmp_path)
    blocked = ParserSmokeResult(
        schema_version="okf-parser-smoke.v1",
        status="blocked",
        source_ref="",
        attempt_ref="",
        source_commit="",
        vendor_hash="",
        license_hash="",
        notice_hash="",
        bundle_hash="",
        read_boundary=(),
        read_summary={},
        reason="VENDOR_PROVENANCE_INCOMPLETE",
    )
    report = finalize_bundle_profile(_committed_for_recovery(artifacts), blocked)
    assert report.ac08_result == "blocked"
    projection = json.loads(artifacts.projection_report_path.read_text(encoding="utf-8"))
    manifest = json.loads(artifacts.exit_manifest_path.read_text(encoding="utf-8"))
    assert projection["parser_smoke"]["reason"] == "VENDOR_PROVENANCE_INCOMPLETE"
    assert manifest["ac08_result"] == "blocked"
    assert manifest["reason"] == "parser smoke blocked: VENDOR_PROVENANCE_INCOMPLETE"


def test_parser_finalize_recovery_rejects_base_hash_mismatch_without_writes(tmp_path: Path) -> None:
    artifacts = _bundle(tmp_path)
    committed = _committed_for_recovery(artifacts)
    vendor = read_vendor_ref(VENDOR_ROOT)
    attempt = create_smoke_attempt(committed.artifact_root, vendor)
    result = run_parser_smoke(committed.artifact_root, vendor, attempt)
    (artifacts.bundle_dir / "index.md").write_text("# mutated\n", encoding="utf-8")
    before = {
        path.relative_to(artifacts.artifact_root).as_posix(): path.read_bytes()
        for path in artifacts.artifact_root.rglob("*")
        if path.is_file()
    }
    with pytest.raises(ValidationError, match="base hashes"):
        finalize_bundle_profile(committed, replace(result, bundle_hash=committed.base_bundle_hash))
    after = {
        path.relative_to(artifacts.artifact_root).as_posix(): path.read_bytes()
        for path in artifacts.artifact_root.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert not (artifacts.artifact_root / ".staging").exists()


def test_parser_finalize_recovery_rejects_validator_failure_without_writes(tmp_path: Path) -> None:
    artifacts = _bundle(tmp_path)
    (next(path for path in (artifacts.bundle_dir / "products").rglob("*.md") if path.name != "index.md")).write_text("# malformed\n", encoding="utf-8")
    committed = _committed_for_recovery(artifacts)
    vendor = read_vendor_ref(VENDOR_ROOT)
    attempt = create_smoke_attempt(committed.artifact_root, vendor)
    result = run_parser_smoke(committed.artifact_root, vendor, attempt)
    assert result.status == "failed"
    before = {
        path.relative_to(artifacts.artifact_root).as_posix(): path.read_bytes()
        for path in artifacts.artifact_root.rglob("*")
        if path.is_file()
    }
    with pytest.raises(ValidationError, match="validation failed"):
        finalize_bundle_profile(committed, result)
    after = {
        path.relative_to(artifacts.artifact_root).as_posix(): path.read_bytes()
        for path in artifacts.artifact_root.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert not (artifacts.artifact_root / ".staging").exists()


def _committed_for_recovery(artifacts: BundleArtifactPaths):
    """Rehydrate the committed fixture without changing its bytes."""
    projection = json.loads(artifacts.projection_report_path.read_text(encoding="utf-8"))
    report = BundleReport(
        schema_version=projection["schema_version"],
        run_id=projection["run_id"],
        profile=projection.get("profile"),
        ac08_result=projection["ac08_result"],
        release_status=projection["digest_release_status"],
        bundle_ref=projection["bundle_ref"],
        audit_ref=projection["audit_ref"],
        projection_report_ref=projection["projection_report_ref"],
        exit_manifest_ref=projection["exit_manifest_ref"],
        degraded_records=tuple(projection["degraded_records"]),
        input_readback=tuple(projection["input_readback"]),
        entry_binding=projection["entry_binding"],
        concept_count=projection["concept_count"],
        source_count=projection["source_count"],
        claim_count=projection["claim_count"],
    )
    def file_hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    tree_digest = hashlib.sha256()
    # Keep this recovery digest independent from production helpers so the
    # unchanged-byte assertion can detect a helper regression as well.
    for path in sorted(item for item in artifacts.bundle_dir.rglob("*") if item.is_file()):
        tree_digest.update(path.relative_to(artifacts.bundle_dir).as_posix().encode())
        tree_digest.update(b"\0")
        tree_digest.update(path.read_bytes())
        tree_digest.update(b"\0")
    return CommittedBundleRun(artifacts.artifact_root, report.run_id, tree_digest.hexdigest(), file_hash(artifacts.projection_report_path), file_hash(artifacts.exit_manifest_path), report)
