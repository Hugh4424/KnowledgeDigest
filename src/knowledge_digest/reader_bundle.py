"""Isolated, deterministic Task 2-A Reader Bundle projection.

This module deliberately does not connect to the formal S1-S6 pipeline or the
``digest`` CLI.  It projects already-audited control-plane facts into a fresh
artifact root and keeps failures in an audit/degraded surface.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping

import yaml

from .errors import ValidationError
from .identity import readable_slug
from .reader_frontmatter import managed_content_hash, parse_concept_document, serialize_concept_document


TOPIC_INDEX_SCHEMA = "2.0.0"
STRUCTURE_INPUT_SCHEMA = "reader-bundle-structure-inputs.v1"
FULL_INPUT_SCHEMA = "reader-bundle-inputs.v1"
EXEMPT_FILES = {"README.md", "Home.md", "references/sources.md"}
CONCEPT_TYPES = {
    "product_overview": "KnowledgeDigest Product Overview",
    "module_or_capability": "KnowledgeDigest Module or Capability",
    "procedure_or_rule": "KnowledgeDigest Procedure or Rule",
}
_FIXED_PAGE_TYPE_MAPPING = {
    ("products", "product_only"): "product_overview",
    ("products", "standard"): "module_or_capability",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_SEGMENT = re.compile(r"^[^/\\.][^/\\]*$")
_ENTRY_BINDING_CONSUMER = "reader-bundle"
_ENTRY_RECHECK_COMMAND = "uv run --frozen digest NEW_DIR KB_DIR --config CONFIG --no-llm"
_AC08_BLOCKED = "blocked"
_NOT_RELEASED = "not_released"
_TRUST_SCHEMA = "reader-bundle-trust-signals.v1"
_TRUST_DETECTOR_VERSION = "v1"
_TRUST_EVENTS = frozenset({"source_hash_match", "locator_resolved"})
_TRUST_GENERATOR = "knowledge-digest/reader-bundle/1"
_ACCEPTED_ENTRY_STATUSES = frozenset({
    "not_released",
    "passed",
    "verified",
    "verified_source_precheck",
    "reconciled_for_task2a_entry",
})


@dataclass(frozen=True)
class ArtifactRef:
    artifact_kind: str
    ref: str
    id: str
    hash: str
    schema_version: str
    version: str


@dataclass(frozen=True)
class ReaderBundleStructureInputs:
    schema_version: Literal["reader-bundle-structure-inputs.v1"]
    input_root: Path
    topic_index_ref: ArtifactRef
    source_inventory_ref: ArtifactRef
    entry_manifest_refs: tuple[ArtifactRef, ...]
    offline_mode: Literal["no-llm"]


@dataclass(frozen=True)
class ReaderBundleInputs(ReaderBundleStructureInputs):
    schema_version: Literal["reader-bundle-inputs.v1"]
    claim_records_ref: ArtifactRef
    fixture_selection_ref: ArtifactRef


@dataclass(frozen=True)
class BundleArtifactPaths:
    artifact_root: Path
    bundle_dir: Path
    audit_dir: Path
    reports_dir: Path
    projection_report_path: Path
    exit_manifest_path: Path

    @classmethod
    def from_root(cls, artifact_root: Path) -> "BundleArtifactPaths":
        root = Path(artifact_root)
        if not root.is_absolute():
            raise ValidationError("reader-bundle", root, "artifact root must be absolute")
        if root.exists():
            if root.is_symlink():
                raise ValidationError("reader-bundle", root, "artifact root must not be a symlink")
            if any(root.iterdir()):
                raise ValidationError("reader-bundle", root, "artifact root must be new and empty")
        else:
            root.mkdir(parents=True)
        return cls(
            artifact_root=root,
            bundle_dir=root / "bundle",
            audit_dir=root / "audit",
            reports_dir=root / "reports",
            projection_report_path=root / "reports" / "projection-report.json",
            exit_manifest_path=root / "reports" / "exit-manifest.json",
        )


@dataclass(frozen=True)
class TopicIndexAdapterResult:
    branch: Literal["standard", "product_only", "degraded"]
    digest_topic_key: str | None
    digest_topic_id: str | None
    product: str | None
    module: str | None
    object_intent: str | None
    published_path: str | None
    error_codes: tuple[str, ...] = ()
    row: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class EntryBindingCheck:
    schema_version: str
    status: Literal["passed", "backfill_required", "blocked"]
    consumer: str
    bindings: tuple[Mapping[str, Any], ...]
    missing_refs: tuple[str, ...]
    recheck_command: str


@dataclass(frozen=True)
class EntryBackfillResult:
    schema_version: str
    status: str
    path: str
    digest_release_status: str
    missing_refs: tuple[str, ...]


@dataclass(frozen=True)
class BundleReport:
    schema_version: str
    run_id: str
    profile: str | None
    ac08_result: str
    release_status: str
    bundle_ref: str
    audit_ref: str
    projection_report_ref: str
    exit_manifest_ref: str
    degraded_records: tuple[Mapping[str, Any], ...]
    input_readback: tuple[Mapping[str, Any], ...]
    entry_binding: Mapping[str, Any]
    concept_count: int
    source_count: int
    claim_count: int


@dataclass(frozen=True)
class BundleValidationReport:
    schema_version: str
    status: Literal["passed", "failed"]
    checked_paths: tuple[str, ...]
    error_codes: tuple[str, ...]
    entry_count: int
    source_count: int
    claim_count: int
    degraded_match_count: int
    artifact_root_ref: str


@dataclass(frozen=True)
class CommittedBundleRun:
    artifact_root: Path
    run_id: str
    base_bundle_hash: str
    base_projection_report_hash: str
    base_exit_manifest_hash: str
    report: BundleReport

    @property
    def profile(self) -> str | None:
        return self.report.profile

    @property
    def ac08_result(self) -> str:
        return self.report.ac08_result


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_relative(root: Path, ref: str, *, label: str) -> Path:
    candidate = Path(ref)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValidationError("reader-bundle", label, "reference must stay inside input root")
    current = root
    for part in candidate.parts:
        current /= part
        if current.is_symlink():
            raise ValidationError("reader-bundle", label, "reference must not traverse a symlink")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValidationError("reader-bundle", label, "reference escapes input root")
    if (root / candidate).is_symlink():
        raise ValidationError("reader-bundle", label, "reference must not be a symlink")
    if not resolved.is_file():
        raise ValidationError("reader-bundle", label, "reference does not exist")
    return resolved


def _validate_ref(root: Path, ref: ArtifactRef, *, seen: set[str]) -> tuple[Path, Mapping[str, Any]]:
    if not ref.id or ref.id in seen:
        raise ValidationError("reader-bundle", ref.id, "artifact reference id is missing or duplicated")
    for field in ("artifact_kind", "schema_version", "version"):
        if not isinstance(getattr(ref, field), str) or not getattr(ref, field).strip():
            raise ValidationError("reader-bundle", ref.ref, f"artifact reference {field} is missing")
    seen.add(ref.id)
    if not _SHA256.fullmatch(ref.hash):
        raise ValidationError("reader-bundle", ref.ref, "artifact reference hash must be SHA-256")
    path = _safe_relative(root, ref.ref, label=ref.ref)
    observed = _sha256_path(path)
    if observed != ref.hash:
        raise ValidationError("reader-bundle", ref.ref, "artifact reference hash is stale")
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        value = None
    return path, {"artifact_kind": ref.artifact_kind, "ref": ref.ref, "id": ref.id, "declared_hash": ref.hash, "observed_hash": observed, "schema_version": ref.schema_version, "version": ref.version, "consumer": _ENTRY_BINDING_CONSUMER, "status": "passed", "value": value}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("reader-bundle", path, f"invalid JSONL at line {line_no}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValidationError("reader-bundle", path, f"JSONL line {line_no} must be an object")
        rows.append(row)
    return rows


def _entry_producer(value: Mapping[str, Any]) -> Mapping[str, Any] | None:
    producer = value.get("generated_by") or value.get("producer")
    if not isinstance(producer, Mapping) or not isinstance(producer.get("process"), str) or not producer["process"].strip():
        return None
    return {key: producer[key] for key in ("process", "baseline_commit", "source_run") if key in producer}


def _entry_coverage(
    value: Mapping[str, Any],
    ref: ArtifactRef,
    *,
    source_inventory: list[dict[str, Any]],
    source_inventory_hash: str,
    topic_index_hash: str,
) -> tuple[tuple[str, ...], Mapping[str, Any]]:
    errors: list[str] = []
    observed_source_count = len(source_inventory)
    observed_types = dict(sorted(Counter(str(row.get("knowledge_type")) for row in source_inventory).items()))
    facts: dict[str, Any] = {"observed_source_count": observed_source_count, "observed_knowledge_type_counts": observed_types}
    if ref.schema_version == "task2-entry-sample-coverage.v1":
        coverage = value.get("inventory_coverage")
        if not isinstance(coverage, Mapping):
            return ("ENTRY_COVERAGE_MISSING",), facts
        declared_count = coverage.get("source_count")
        declared_types = coverage.get("knowledge_type_counts")
        if not isinstance(declared_count, int) or isinstance(declared_count, bool) or declared_count != observed_source_count:
            errors.append("ENTRY_COVERAGE_MISMATCH")
        if coverage.get("source_inventory_sha256") != source_inventory_hash:
            errors.append("ENTRY_COVERAGE_SOURCE_HASH_MISMATCH")
        if not isinstance(declared_types, Mapping) or dict(sorted((str(key), value) for key, value in declared_types.items())) != observed_types:
            errors.append("ENTRY_COVERAGE_TYPE_COUNTS_MISMATCH")
        facts["declared_source_count"] = declared_count
        facts["declared_knowledge_type_counts"] = dict(declared_types) if isinstance(declared_types, Mapping) else None
        return tuple(sorted(set(errors))), facts
    if ref.schema_version == "knowledge-publication-task2-entry-backfill.v1":
        input_snapshot = value.get("input_snapshot")
        task0_runtime = (value.get("task0") or {}).get("runtime_evidence") if isinstance(value.get("task0"), Mapping) else None
        task1 = value.get("task1")
        task1_source_count = task1.get("source_count") if isinstance(task1, Mapping) else None
        declared_counts = {
            "input_snapshot.source_count": input_snapshot.get("source_count") if isinstance(input_snapshot, Mapping) else None,
            "task0.runtime_evidence.source_count": task0_runtime.get("source_count") if isinstance(task0_runtime, Mapping) else None,
            "task1.source_count": task1_source_count,
        }
        if any(not isinstance(count, int) or isinstance(count, bool) for count in declared_counts.values()):
            errors.append("ENTRY_COVERAGE_MISSING")
        elif any(count != observed_source_count for count in declared_counts.values()):
            errors.append("ENTRY_COVERAGE_MISMATCH")
        artifacts = task1.get("artifacts") if isinstance(task1, Mapping) else None
        artifact_by_kind = {
            str(item.get("kind")): item
            for item in artifacts
            if isinstance(artifacts, list) and isinstance(item, Mapping) and item.get("kind")
        }
        source_artifact = artifact_by_kind.get("source_inventory")
        topic_artifact = artifact_by_kind.get("topic_index")
        if not isinstance(source_artifact, Mapping) or source_artifact.get("sha256") != source_inventory_hash:
            errors.append("ENTRY_COVERAGE_SOURCE_HASH_MISMATCH")
        if not isinstance(topic_artifact, Mapping) or topic_artifact.get("sha256") != topic_index_hash:
            errors.append("ENTRY_COVERAGE_TOPIC_HASH_MISMATCH")
        facts["declared_source_counts"] = declared_counts
        facts["linked_source_inventory_hash"] = source_artifact.get("sha256") if isinstance(source_artifact, Mapping) else None
        facts["linked_topic_index_hash"] = topic_artifact.get("sha256") if isinstance(topic_artifact, Mapping) else None
        return tuple(sorted(set(errors))), facts
    return ("ENTRY_COVERAGE_SCHEMA_UNSUPPORTED",), facts


def _slug(value: str, label: str) -> str:
    try:
        return readable_slug(value)
    except ValidationError:
        fallback = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"segment-{fallback}"


def _base_adapter(row: Mapping[str, Any], *, source_ref: ArtifactRef) -> tuple[list[str], str | None, str | None]:
    errors: list[str] = []
    if not isinstance(row, Mapping):
        return ["TOPIC_ROW_SCHEMA_UNSUPPORTED"], None, None
    if not isinstance(row.get("topic_key"), str) or not row["topic_key"].strip():
        errors.append("TOPIC_ROW_MISSING_IDENTITY")
    if not any(isinstance(row.get(key), str) and row[key].strip() for key in ("digest_topic_id", "topic_id", "topic_key")):
        errors.append("TOPIC_ROW_MISSING_IDENTITY")
    evidence = row.get("evidence_refs")
    if not isinstance(evidence, list) or not evidence:
        errors.append("TOPIC_ROW_MISSING_EVIDENCE")
    else:
        for item in evidence:
            if not isinstance(item, Mapping) or not item.get("source_uri") or not item.get("content_fingerprint"):
                errors.append("TOPIC_ROW_MISSING_EVIDENCE")
                break
    if row.get("status") not in {"published", "degraded"}:
        errors.append("TOPIC_ROW_SCHEMA_UNSUPPORTED")
    if row.get("published_path") is not None and isinstance(row.get("published_path"), str):
        path = PurePosixPath(row["published_path"])
        if path.is_absolute() or ".." in path.parts:
            errors.append("TOPIC_ROW_CONFLICT")
    identity = next((row[key] for key in ("digest_topic_id", "topic_id", "topic_key") if isinstance(row.get(key), str) and row[key].strip()), None)
    return errors, identity, row.get("topic_key") if isinstance(row.get("topic_key"), str) else None


def adapt_topic_index_row(
    row: Mapping[str, Any], *, source_ref: ArtifactRef, row_number: int
) -> TopicIndexAdapterResult:
    errors, identity, topic_key = _base_adapter(row, source_ref=source_ref)
    if errors:
        return TopicIndexAdapterResult("degraded", topic_key, identity, None, None, None, None, tuple(sorted(set(errors))), row)
    kind = row.get("knowledge_type")
    product = row.get("product")
    module = row.get("module")
    intent = row.get("object_intent")
    status = row.get("status")
    product_only = kind == "products" and (
        module is None or str(intent or "").strip().casefold() in {"overview", "product overview"}
    )
    if product_only:
        if not isinstance(product, str) or not product.strip():
            errors.append("PRODUCT_ONLY_MISSING_PRODUCT")
        if not isinstance(intent, str) or not intent.strip():
            errors.append("PRODUCT_ONLY_MISSING_OBJECT_INTENT")
        if module is not None:
            errors.append("PRODUCT_ONLY_MODULE_FORBIDDEN")
        if status != "published":
            errors.append("PRODUCT_ONLY_INVALID_STATUS")
        if errors:
            return TopicIndexAdapterResult("degraded", topic_key, identity, product if isinstance(product, str) else None, None, intent if isinstance(intent, str) else None, None, tuple(sorted(set(errors))), row)
        return TopicIndexAdapterResult("product_only", topic_key, identity, product, None, intent, row.get("published_path"), (), row)
    if status == "degraded":
        return TopicIndexAdapterResult("degraded", topic_key, identity, None, None, None, None, ("TOPIC_ROW_UNCERTAIN",), row)
    if kind != "products":
        errors.append("TOPIC_ROW_UNCERTAIN")
    if not isinstance(product, str) or not product.strip():
        errors.append("PRODUCT_ONLY_MISSING_PRODUCT")
    if not isinstance(module, str) or not module.strip():
        errors.append("TOPIC_ROW_CONFLICT")
    if not isinstance(intent, str) or not intent.strip():
        errors.append("TOPIC_ROW_CONFLICT")
    if errors:
        return TopicIndexAdapterResult("degraded", topic_key, identity, product if isinstance(product, str) else None, module if isinstance(module, str) else None, intent if isinstance(intent, str) else None, None, tuple(sorted(set(errors))), row)
    return TopicIndexAdapterResult("standard", topic_key, identity, product, module, intent, row.get("published_path"), (), row)


def _load_inputs(inputs: ReaderBundleStructureInputs | ReaderBundleInputs) -> tuple[dict[str, Any], list[dict[str, Any]], tuple[Mapping[str, Any], ...], EntryBindingCheck, dict[str, Any]]:
    root = Path(inputs.input_root)
    if root.is_symlink() or not root.is_dir():
        raise ValidationError("reader-bundle", root, "input root must be a real directory")
    if inputs.schema_version not in {STRUCTURE_INPUT_SCHEMA, FULL_INPUT_SCHEMA}:
        raise ValidationError("reader-bundle", inputs.schema_version, "unsupported input schema")
    if inputs.offline_mode != "no-llm":
        raise ValidationError("reader-bundle", inputs.offline_mode, "only no-llm input mode is allowed")
    refs = [inputs.topic_index_ref, inputs.source_inventory_ref, *inputs.entry_manifest_refs]
    if isinstance(inputs, ReaderBundleInputs):
        refs.extend([inputs.claim_records_ref, inputs.fixture_selection_ref])
    seen: set[str] = set()
    loaded: dict[str, Any] = {}
    readback: list[Mapping[str, Any]] = []
    for ref in refs:
        path, record = _validate_ref(root, ref, seen=seen)
        readback.append({key: value for key, value in record.items() if key != "value"})
        if ref is inputs.topic_index_ref:
            value = record.get("value")
            if not isinstance(value, dict):
                raise ValidationError("reader-bundle", ref.ref, "topic index must be a JSON object")
            loaded["topic_index"] = value
        elif ref is inputs.source_inventory_ref:
            loaded["source_inventory"] = _read_jsonl(path)
        elif isinstance(inputs, ReaderBundleInputs) and ref is inputs.claim_records_ref:
            loaded["claims"] = _read_jsonl(path)
        elif isinstance(inputs, ReaderBundleInputs) and ref is inputs.fixture_selection_ref:
            value = record.get("value")
            if not isinstance(value, dict):
                raise ValidationError("reader-bundle", ref.ref, "fixture selection must be a JSON object")
            loaded["selection"] = value
    check = check_entry_bindings(inputs, source_inventory=loaded["source_inventory"])
    return loaded["topic_index"], loaded["source_inventory"], tuple(readback), check, loaded


def check_entry_bindings(inputs: ReaderBundleStructureInputs, *, source_inventory: list[dict[str, Any]] | None = None) -> EntryBindingCheck:
    if not inputs.entry_manifest_refs:
        return EntryBindingCheck(
            "reader-bundle-entry-binding.v1", "backfill_required", _ENTRY_BINDING_CONSUMER, (), ("entry_manifest_refs",),
            _ENTRY_RECHECK_COMMAND,
        )
    seen: set[str] = set()
    bindings: list[Mapping[str, Any]] = []
    missing: list[str] = []
    if source_inventory is None:
        try:
            source_path, _source_record = _validate_ref(inputs.input_root, inputs.source_inventory_ref, seen=set())
            source_inventory = _read_jsonl(source_path)
        except ValidationError as exc:
            source_inventory = []
            missing.append(f"{inputs.source_inventory_ref.ref}:{exc.reason}")
    producer_processes: set[str] = set()
    for ref in inputs.entry_manifest_refs:
        try:
            path, record = _validate_ref(inputs.input_root, ref, seen=seen)
        except ValidationError as exc:
            missing.append(f"{ref.ref}:{exc.reason}")
            bindings.append({"ref": ref.ref, "status": "blocked", "error": exc.reason, "consumer": _ENTRY_BINDING_CONSUMER})
            continue
        bindings.append({key: value for key, value in record.items() if key != "value"})
        value = record.get("value")
        if not isinstance(value, dict) or value.get("status") not in _ACCEPTED_ENTRY_STATUSES:
            missing.append(f"{ref.ref}:ENTRY_STATUS_UNSUPPORTED")
            bindings[-1] = {**bindings[-1], "status": "blocked", "error": "ENTRY_STATUS_UNSUPPORTED", "observed_status": value.get("status") if isinstance(value, dict) else None}
            continue
        producer = _entry_producer(value)
        coverage_errors, coverage_facts = _entry_coverage(
            value,
            ref,
            source_inventory=source_inventory,
            source_inventory_hash=inputs.source_inventory_ref.hash,
            topic_index_hash=inputs.topic_index_ref.hash,
        )
        if producer is None:
            missing.append(f"{ref.ref}:ENTRY_PRODUCER_MISSING")
        else:
            producer_processes.add(str(producer["process"]))
        for error in coverage_errors:
            missing.append(f"{ref.ref}:{error}")
        bindings[-1] = {
            **bindings[-1],
            "producer": dict(producer) if producer is not None else None,
            "coverage": coverage_facts,
            "status": "blocked" if producer is None or coverage_errors else "passed",
            **({"error_codes": list(coverage_errors) + (["ENTRY_PRODUCER_MISSING"] if producer is None else [])} if producer is None or coverage_errors else {}),
        }
    if len(producer_processes) > 1:
        missing.append("entry_manifests:ENTRY_PRODUCER_MISMATCH")
        bindings = tuple({**binding, "status": "blocked", "error_codes": [*binding.get("error_codes", []), "ENTRY_PRODUCER_MISMATCH"]} for binding in bindings)
    return EntryBindingCheck(
        "reader-bundle-entry-binding.v1", "blocked" if missing else "passed", _ENTRY_BINDING_CONSUMER, tuple(bindings), tuple(missing),
        _ENTRY_RECHECK_COMMAND,
    )


def write_entry_backfill_manifest(check: EntryBindingCheck, artifacts: BundleArtifactPaths, *, run_id: str) -> EntryBackfillResult:
    path = artifacts.audit_dir / "entry-backfill" / f"{run_id}.json"
    canonical_ref = f"audit/entry-backfill/{run_id}.json"
    value = {
        "schema_version": "reader-bundle-entry-backfill.v1",
        "status": check.status,
        "digest_release_status": "not_released",
        "missing_refs": list(check.missing_refs),
        "bindings": list(check.bindings),
        "recheck_command": check.recheck_command,
        "evidence_ref": canonical_ref,
    }
    _write_json(path, value)
    return EntryBackfillResult(value["schema_version"], check.status, canonical_ref, "not_released", check.missing_refs)


def _concept_path(adapter: TopicIndexAdapterResult) -> str:
    product = _slug(str(adapter.product), "product")
    intent = _slug(str(adapter.object_intent), "object_intent")
    if adapter.branch == "product_only":
        return f"products/{product}/{intent}.md"
    module = _slug(str(adapter.module), "module")
    return f"products/{product}/modules/{module}/{intent}.md"


def _title_description(
    row: Mapping[str, Any],
    adapter: TopicIndexAdapterResult,
    *,
    body: str = "",
    source_row: Mapping[str, Any] | None = None,
) -> tuple[str, str] | None:
    h1 = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ") and line[2:].strip()), None)
    sentences = re.split(r"(?<=[.!?。！？])\s+", " ".join(line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")))
    first_sentence = next((sentence.strip() for sentence in sentences if len(sentence.strip()) >= 8), None)
    source_row = source_row or {}
    title_candidates = (
        row.get("title"),
        row.get("metadata_title"),
        source_row.get("title"),
        source_row.get("metadata_title"),
        row.get("h1"),
        source_row.get("h1"),
        h1,
        _readable_filename(source_row.get("content_path") or row.get("published_path")),
    )
    title = next((candidate for candidate in title_candidates if isinstance(candidate, str) and candidate.strip()), None)
    description = row.get("description") or row.get("summary") or source_row.get("description") or source_row.get("summary") or first_sentence
    if not isinstance(title, str) or not title.strip() or not isinstance(description, str) or not description.strip():
        return None
    return _normalize_readable(title), _normalize_readable(description).splitlines()[0]


def _normalize_readable(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()
    normalized = re.sub(r"\s*([,，:：;；!?！？])\s*", r"\1", normalized)
    return normalized.strip(" -_")


def _readable_filename(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    stem = PurePosixPath(value).stem
    return re.sub(r"[-_]+", " ", stem).strip() or None


def _source_rows(source_inventory: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in source_inventory:
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            continue
        if row.get("validation_status") not in {"passed", "verified", "ok"}:
            continue
        result[source_id] = row
    return result


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("reader-bundle", label, "required provenance text is missing")
    return value


def _generated_record() -> dict[str, str]:
    return {
        "by": _TRUST_GENERATOR,
        "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _explicit_stale_after(source: Mapping[str, Any] | None) -> str | None:
    if not isinstance(source, Mapping):
        return None
    containers = [source]
    source_meta = source.get("source_meta")
    if isinstance(source_meta, Mapping):
        containers.append(source_meta)
    for container in containers:
        for key in ("stale_after", "valid_until", "review_after"):
            value = container.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValidationError("reader-bundle", key, "explicit freshness date must be YYYY-MM-DD")
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValidationError("reader-bundle", key, "explicit freshness date is invalid") from exc
            return value
    return None


def _trust_audit_ref(page_path: str) -> str:
    stem = PurePosixPath(page_path).with_suffix("").as_posix().replace("/", "-")
    return f"audit/trust-signals/{_slug(stem, 'trust-page')}.json"


def _trust_fingerprints(frontmatter: Mapping[str, Any], selection: Mapping[str, Any]) -> tuple[dict[str, Any], bool, bool]:
    source_entries = frontmatter.get("sources")
    if not isinstance(source_entries, list) or len(source_entries) != 1 or not isinstance(source_entries[0], Mapping):
        return {}, False, False
    source = source_entries[0]
    source_fingerprint = source.get("digest_content_fingerprint")
    selected_fingerprint = selection.get("content_fingerprint")
    claims = source.get("digest_claims")
    claim_fingerprints = {
        str(claim.get("claim_id")): claim.get("content_fingerprint")
        for claim in claims
        if isinstance(claim, Mapping) and claim.get("claim_id")
    } if isinstance(claims, list) else {}
    fingerprints = {
        "source_inventory": source_fingerprint,
        "fixture_selection": selected_fingerprint,
        "claim_records": claim_fingerprints,
        "fixture_bytes": selection.get("fixture_sha256"),
    }
    source_hash_match = (
        isinstance(source_fingerprint, str)
        and source_fingerprint
        and source_fingerprint == selected_fingerprint
        and bool(claim_fingerprints)
        and all(value == source_fingerprint for value in claim_fingerprints.values())
    )
    footnote = str(source.get("id") or "")
    footnotes = set(re.findall(r"\[\^([A-Za-z0-9._-]+)\]", str(selection.get("fixture_body") or "")))
    locator_resolved = (
        bool(footnote)
        and footnote in footnotes
        and isinstance(claims, list)
        and bool(claims)
        and all(
            isinstance(claim, Mapping)
            and isinstance(claim.get("fragment_locator"), str)
            and bool(claim["fragment_locator"].strip())
            and re.fullmatch(r"lines:\d+(?:-\d+)?", claim["fragment_locator"].strip()) is not None
            and isinstance(claim.get("target_path"), str)
            and bool(claim["target_path"].strip())
            and not PurePosixPath(claim["target_path"]).is_absolute()
            and ".." not in PurePosixPath(claim["target_path"]).parts
            for claim in claims
        )
    )
    return fingerprints, bool(source_hash_match), locator_resolved


def _trust_events(
    frontmatter: Mapping[str, Any],
    body: str,
    selection: Mapping[str, Any] | None,
    *,
    content_hash: str,
    evidence_ref: str,
) -> list[dict[str, Any]]:
    if selection is None:
        return []
    selection_with_body = dict(selection)
    selection_with_body["fixture_body"] = body
    fingerprints, source_hash_match, locator_resolved = _trust_fingerprints(frontmatter, selection_with_body)
    events: list[dict[str, Any]] = []
    for event, passed in (("source_hash_match", source_hash_match), ("locator_resolved", locator_resolved)):
        if not passed:
            continue
        events.append({
            "event": event,
            "actor": f"process:knowledge-digest-{event}-{_TRUST_DETECTOR_VERSION}",
            "detector_version": _TRUST_DETECTOR_VERSION,
            "input_fingerprints": fingerprints,
            "content_hash": content_hash,
            "evidence_ref": evidence_ref,
        })
    return events


def _read_trust_audit(artifacts: BundleArtifactPaths, evidence_ref: str) -> tuple[Mapping[str, Any] | None, str | None]:
    relative = PurePosixPath(evidence_ref)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:2] != ("audit", "trust-signals"):
        return None, "TRUST_SIGNAL_EVIDENCE_PATH_INVALID"
    path = artifacts.audit_dir.joinpath(*relative.parts[1:])
    if path.is_symlink() or not path.is_file() or not path.is_relative_to(artifacts.audit_dir):
        return None, "TRUST_SIGNAL_EVIDENCE_MISSING"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "TRUST_SIGNAL_EVIDENCE_INVALID"
    if not isinstance(value, Mapping):
        return None, "TRUST_SIGNAL_EVIDENCE_INVALID"
    return value, None


def _validate_trust_signals(
    path: Path,
    frontmatter: Mapping[str, Any],
    body: str,
    artifacts: BundleArtifactPaths,
    expected: ReaderBundleStructureInputs | ReaderBundleInputs | None,
) -> list[str]:
    errors: list[str] = []
    generated = frontmatter.get("generated")
    if not isinstance(generated, Mapping) or not isinstance(generated.get("by"), str) or not generated["by"].strip() or not isinstance(generated.get("at"), str) or not generated["at"].strip():
        errors.append("GENERATED_METADATA_INVALID")
    elif isinstance(generated["at"], str):
        try:
            datetime.fromisoformat(generated["at"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("GENERATED_TIMESTAMP_INVALID")
    machine_pass = frontmatter.get("digest_machine_pass")
    if machine_pass is not True:
        errors.append("MACHINE_PASS_INVALID")
    if machine_pass is not True:
        return errors
    relative_page = path.relative_to(artifacts.bundle_dir).as_posix()
    expected_ref = _trust_audit_ref(relative_page)
    audit, audit_error = _read_trust_audit(artifacts, expected_ref)
    if audit_error:
        errors.append(audit_error)
    if audit is not None:
        if audit.get("schema_version") != _TRUST_SCHEMA or audit.get("page_path") != relative_page or audit.get("topic_id") != frontmatter.get("digest_topic_id") or audit.get("machine_pass") is not True:
            errors.append("TRUST_SIGNAL_EVIDENCE_INVALID")
        if audit.get("generated") != generated:
            errors.append("TRUST_SIGNAL_GENERATED_MISMATCH")
    current_hash = managed_content_hash(frontmatter, body)
    verified = frontmatter.get("verified")
    if verified is None:
        verified = []
    if not isinstance(verified, list):
        errors.append("TRUST_SIGNAL_LIST_INVALID")
        verified = []
    event_names = [repr(item.get("event")) for item in verified if isinstance(item, Mapping)]
    if len(event_names) != len(set(event_names)):
        errors.append("TRUST_SIGNAL_EVENT_DUPLICATED")
    if isinstance(expected, ReaderBundleInputs) and {item.get("event") for item in verified if isinstance(item, Mapping)} != _TRUST_EVENTS:
        errors.append("TRUST_SIGNAL_REQUIRED_EVENT_MISSING")
    if audit is not None and audit.get("content_hash") != current_hash:
        errors.append("TRUST_SIGNAL_CONTENT_HASH_MISMATCH")
    audit_events = audit.get("events") if isinstance(audit, Mapping) and isinstance(audit.get("events"), list) else []
    if audit is not None and verified != audit_events:
        errors.append("TRUST_SIGNAL_EVIDENCE_MISMATCH")
    canonical_fingerprints: Mapping[str, Any] | None = None
    if isinstance(expected, ReaderBundleInputs):
        try:
            _raw_index, source_inventory, _readback, _entry_check, loaded = _load_inputs(expected)
            selection_map = _selection_map(loaded.get("selection"))
            claim_map = _claim_map(loaded.get("claims", []))
            topic_id = str(frontmatter.get("digest_topic_id") or "")
            selection = next((item for item in selection_map.values() if str(item.get("topic_id")) == topic_id), None)
            if selection is not None:
                source = _source_rows(source_inventory).get(str(selection.get("source_id")))
                claims = [claim_map[str(claim_id)] for claim_id in selection.get("claim_ids", []) if str(claim_id) in claim_map]
                canonical_fingerprints = {
                    "source_inventory": source.get("content_fingerprint") if source else None,
                    "fixture_selection": selection.get("content_fingerprint"),
                    "claim_records": {str(claim.get("claim_id")): claim.get("content_fingerprint") for claim in claims},
                    "fixture_bytes": selection.get("fixture_sha256"),
                }
        except ValidationError:
            errors.append("TRUST_SIGNAL_FINGERPRINTS_UNAVAILABLE")
    for item in verified:
        if not isinstance(item, Mapping):
            errors.append("TRUST_SIGNAL_EVENT_INVALID")
            continue
        event = item.get("event")
        if event not in _TRUST_EVENTS:
            errors.append("TRUST_SIGNAL_EVENT_UNSUPPORTED")
        actor = item.get("actor")
        if not isinstance(actor, str) or actor.startswith("human:") or actor.startswith("agent_assisted") or actor != f"process:knowledge-digest-{event}-{_TRUST_DETECTOR_VERSION}":
            errors.append("TRUST_SIGNAL_ACTOR_FORBIDDEN")
        if item.get("detector_version") != _TRUST_DETECTOR_VERSION:
            errors.append("TRUST_SIGNAL_DETECTOR_INVALID")
        if not isinstance(item.get("input_fingerprints"), Mapping) or not item["input_fingerprints"]:
            errors.append("TRUST_SIGNAL_FINGERPRINTS_MISSING")
        elif canonical_fingerprints is not None and dict(item["input_fingerprints"]) != dict(canonical_fingerprints):
            errors.append("TRUST_SIGNAL_FINGERPRINTS_MISMATCH")
        if item.get("content_hash") != current_hash:
            errors.append("TRUST_SIGNAL_CONTENT_HASH_MISMATCH")
        evidence_ref = item.get("evidence_ref")
        if evidence_ref != expected_ref:
            errors.append("TRUST_SIGNAL_EVIDENCE_PATH_INVALID")
        if audit is not None and item not in (audit.get("events") if isinstance(audit.get("events"), list) else []):
            errors.append("TRUST_SIGNAL_EVIDENCE_MISMATCH")
    stale_after = frontmatter.get("stale_after")
    if stale_after is not None:
        if not isinstance(stale_after, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", stale_after):
            errors.append("STALE_AFTER_INVALID")
        else:
            try:
                date.fromisoformat(stale_after)
            except ValueError:
                errors.append("STALE_AFTER_INVALID")
    if stale_after is not None and expected is None:
        errors.append("STALE_AFTER_EVIDENCE_MISSING")
    if stale_after is not None and expected is not None:
        try:
            _raw_index, source_inventory, _readback, _entry_check, _loaded = _load_inputs(expected)
            source_entries = frontmatter.get("sources")
            source_entry = source_entries[0] if isinstance(source_entries, list) and source_entries and isinstance(source_entries[0], Mapping) else {}
            matched_source = next(
                (
                    row for row in source_inventory
                    if row.get("source_uri") == source_entry.get("resource")
                    and row.get("content_fingerprint") == source_entry.get("digest_content_fingerprint")
                ),
                None,
            )
            if _explicit_stale_after(matched_source) != stale_after:
                errors.append("STALE_AFTER_EVIDENCE_MISSING")
        except ValidationError:
            errors.append("STALE_AFTER_EVIDENCE_MISSING")
    return errors


def _concept_frontmatter(adapter: TopicIndexAdapterResult, row: Mapping[str, Any], source_map: Mapping[str, Mapping[str, Any]], *, page_type: str, title: str, description: str) -> dict[str, Any]:
    source_ids = list(row.get("source_members") or row.get("source_ids") or [])
    sources: list[dict[str, Any]] = []
    for source_id in source_ids:
        source = source_map.get(source_id)
        if source is None:
            continue
        sources.append({"id": source_id, "resource": source.get("source_uri"), "title": source.get("title") or source.get("content_path"), "digest_content_fingerprint": source.get("content_fingerprint"), "digest_claims": []})
    return {
        "type": CONCEPT_TYPES[page_type],
        "title": title,
        "description": description,
        "sources": sources,
        "status": "draft",
        "digest_topic_key": adapter.digest_topic_key,
        "digest_topic_id": adapter.digest_topic_id,
        "digest_page_type": page_type,
        "digest_page_status": "published",
        "digest_machine_pass": False,
    }


def _claim_map(claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for claim in claims:
        claim_id = claim.get("claim_id")
        if isinstance(claim_id, str) and claim_id:
            if claim_id in result:
                raise ValidationError("reader-bundle", claim_id, "claim id is duplicated")
            result[claim_id] = claim
    return result


def _selection_map(value: Any) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(value, Mapping) or value.get("schema_version") != "task2a-fixture-selection.v1":
        raise ValidationError("reader-bundle", "fixture-selection", "unsupported fixture selection schema")
    rows = value.get("fixtures")
    if not isinstance(rows, list) or not rows:
        raise ValidationError("reader-bundle", "fixture-selection", "fixture selection must contain fixtures")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValidationError("reader-bundle", "fixture-selection", "fixture selection row must be an object")
        pair = (str(row.get("topic_id") or ""), str(row.get("object_intent") or ""))
        if not pair[0] or not pair[1] or pair in result:
            raise ValidationError("reader-bundle", "fixture-selection", "topic_id/object_intent pair must be unique")
        if row.get("mapping_role") not in CONCEPT_TYPES or row.get("digest_page_type") != row.get("mapping_role"):
            raise ValidationError("reader-bundle", pair, "fixture mapping role and page type disagree")
        for field in ("sample_id", "source_id", "source_fragment_id", "content_fingerprint", "fixture_path", "fixture_sha256", "selection_reason"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValidationError("reader-bundle", pair, f"fixture selection missing {field}")
        result[pair] = dict(row)
    return result


def _fixture_body(root: Path, selection: Mapping[str, Any]) -> str:
    path = _safe_relative(root, str(selection["fixture_path"]), label=str(selection["fixture_path"]))
    observed = _sha256_path(path)
    if observed != selection["fixture_sha256"]:
        raise ValidationError("reader-bundle", path, "fixture selection hash is stale")
    return path.read_text(encoding="utf-8")


def _selected_frontmatter(
    adapter: TopicIndexAdapterResult,
    row: Mapping[str, Any],
    source_map: Mapping[str, Mapping[str, Any]],
    claim_map: Mapping[str, Mapping[str, Any]],
    selection: Mapping[str, Any],
    *,
    page_type: str,
    title: str,
    description: str,
) -> dict[str, Any]:
    source_id = str(selection["source_id"])
    source = source_map.get(source_id)
    if source is None:
        raise ValidationError("reader-bundle", source_id, "fixture source is absent from source inventory")
    row_source_ids = {str(value) for value in (row.get("source_members") or row.get("source_ids") or [])}
    if source_id not in row_source_ids:
        raise ValidationError("reader-bundle", source_id, "fixture source is not a member of the selected TopicIndex row")
    source_uri = _required_text(source.get("source_uri"), source_id)
    source_fingerprint = _required_text(source.get("content_fingerprint"), source_id)
    if source_fingerprint != selection["content_fingerprint"]:
        raise ValidationError("reader-bundle", source_id, "fixture source fingerprint does not match selection")
    evidence_refs = row.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not any(
        isinstance(item, Mapping)
        and item.get("source_uri") == source_uri
        and item.get("content_fingerprint") == source_fingerprint
        for item in evidence_refs
    ):
        raise ValidationError("reader-bundle", source_id, "fixture source is not backed by TopicIndex evidence")
    claim_ids = selection.get("claim_ids")
    if not isinstance(claim_ids, list) or not claim_ids:
        raise ValidationError("reader-bundle", selection.get("sample_id", "<unknown>"), "fixture must select at least one claim")
    digest_claims: list[dict[str, Any]] = []
    for claim_id in claim_ids:
        claim = claim_map.get(str(claim_id))
        if claim is None:
            raise ValidationError("reader-bundle", claim_id, "fixture claim is absent from claim history")
        if claim.get("source_uri") != source_uri or claim.get("content_fingerprint") != source_fingerprint:
            raise ValidationError("reader-bundle", claim_id, "claim source/fingerprint does not match fixture source")
        digest_claims.append({
            "claim_id": _required_text(claim.get("claim_id"), str(claim_id)),
            "fragment_locator": _required_text(claim.get("fragment_locator"), str(claim_id)),
            "target_path": _required_text(claim.get("target_path"), str(claim_id)),
            "content_fingerprint": _required_text(claim.get("content_fingerprint"), str(claim_id)),
        })
    value = _concept_frontmatter(adapter, row, source_map, page_type=page_type, title=title, description=description)
    value["sources"] = [{"id": _required_text(selection["source_fragment_id"], "source_fragment_id"), "resource": source_uri, "title": source.get("title") or source.get("content_path"), "digest_content_fingerprint": source_fingerprint, "digest_claims": digest_claims}]
    return value


def _selected_page_type(adapter: TopicIndexAdapterResult, selection: Mapping[str, Any] | None) -> str:
    if selection is not None:
        role = str(selection["mapping_role"])
        if role not in CONCEPT_TYPES:
            raise ValidationError("reader-bundle", role, "fixture mapping role is unsupported")
        if adapter.branch == "product_only" and role != "product_overview":
            raise ValidationError("reader-bundle", role, "fixture mapping role conflicts with TopicIndex branch")
        return role
    page_type = _FIXED_PAGE_TYPE_MAPPING.get((str((adapter.row or {}).get("knowledge_type") or ""), adapter.branch))
    if page_type is None:
        raise ValidationError("reader-bundle", adapter.branch, "TopicIndex knowledge_type/branch has no fixed page type mapping")
    return page_type


def _validate_attribution(path: Path, frontmatter: Mapping[str, Any], body: str, claims: Mapping[str, Mapping[str, Any]]) -> tuple[int, list[str]]:
    source_entries = frontmatter.get("sources")
    if not isinstance(source_entries, list):
        return 0, ["SOURCE_PROJECTION_INVALID"]
    errors: list[str] = []
    by_id: dict[str, Mapping[str, Any]] = {}
    for item in source_entries:
        if not isinstance(item, Mapping) or not item.get("id"):
            errors.append("SOURCE_ENTRY_INVALID")
            continue
        source_id = str(item["id"])
        if source_id in by_id:
            errors.append("SOURCE_ID_DUPLICATED")
        by_id[source_id] = item
    footnotes = set(re.findall(r"\[\^([A-Za-z0-9._-]+)\]", body))
    if not footnotes:
        return 0, []
    for footnote in footnotes:
        if footnote not in by_id:
            errors.append("FOOTNOTE_SOURCE_UNRESOLVED")
    count = 0
    for source in source_entries:
        if not isinstance(source, Mapping) or not source.get("digest_claims"):
            errors.append("SOURCE_CLAIM_CHAIN_MISSING")
            continue
        source_uri = source.get("resource")
        source_fingerprint = source.get("digest_content_fingerprint")
        if not isinstance(source_uri, str) or not source_uri.strip() or not isinstance(source_fingerprint, str) or not source_fingerprint.strip():
            errors.append("SOURCE_PROVENANCE_INCOMPLETE")
        for item in source["digest_claims"]:
            claim_id = item.get("claim_id") if isinstance(item, Mapping) else None
            if not isinstance(item, Mapping) or not all(isinstance(item.get(field), str) and item[field].strip() for field in ("claim_id", "fragment_locator", "target_path", "content_fingerprint")):
                errors.append("CLAIM_PROVENANCE_INCOMPLETE")
                continue
            if claim_id not in claims:
                errors.append("CLAIM_NOT_FOUND")
            elif item.get("content_fingerprint") != source_fingerprint or claims[claim_id].get("content_fingerprint") != source_fingerprint:
                errors.append("CLAIM_FINGERPRINT_MISMATCH")
            else:
                count += 1
    return count, errors


def _degraded_record(adapter: TopicIndexAdapterResult, row_number: int) -> dict[str, Any]:
    stable = adapter.digest_topic_id or adapter.digest_topic_key or f"row-{row_number}"
    stable_id = re.sub(r"[^A-Za-z0-9._-]+", "-", stable).strip("-") or f"row-{row_number}"
    evidence = (adapter.row or {}).get("evidence_refs") if adapter.row else []
    fingerprint = next((item.get("content_fingerprint") for item in evidence if isinstance(item, Mapping) and item.get("content_fingerprint")), "unknown")
    return {"stable_id": stable_id, "reason": ",".join(adapter.error_codes) or "TOPIC_ROW_UNCERTAIN", "error_codes": list(adapter.error_codes), "input_fingerprint": fingerprint, "recovery_path": "recheck TopicIndex evidence and product/module assignment", "audit_target": f"audit/_digest/degraded/{stable_id}.md", "row_number": row_number}


def _write_degraded(artifacts: BundleArtifactPaths, record: Mapping[str, Any]) -> None:
    relative = PurePosixPath(str(record["audit_target"]))
    if not relative.parts or relative.parts[0] != "audit":
        raise ValidationError("reader-bundle", record.get("audit_target"), "degraded audit target must be under audit")
    target = artifacts.audit_dir.joinpath(*relative.parts[1:])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Degraded projection\n\n" + json.dumps(dict(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _markdown_link_targets(text: str) -> list[str]:
    return re.findall(r"\[[^]]*\]\(([^)]+)\)", text)


def _link_label(value: str) -> str:
    return value.replace("[", "").replace("]", "").strip() or "untitled"


def _relative_target(source: Path, target: str, bundle: Path) -> Path:
    if target.startswith("#"):
        return source
    if "://" in target:
        raise ValidationError("reader-bundle", target, "links must be local Markdown links")
    candidate = (source.parent / target).resolve()
    bundle_resolved = bundle.resolve()
    if candidate != bundle_resolved and bundle_resolved not in candidate.parents:
        raise ValidationError("reader-bundle", target, "link escapes Bundle")
    return candidate


def _atomic_commit(staging: Path, artifacts: BundleArtifactPaths) -> None:
    names = ("bundle", "audit", "reports")
    staging_parent = staging.parent
    for stale in staging_parent.glob(".rollback-*"):
        if stale.is_symlink():
            stale.unlink()
        elif stale.is_dir():
            shutil.rmtree(stale)
    rollback = staging_parent / f".rollback-{staging.name}"
    rollback.mkdir(parents=True, exist_ok=False)
    installed: list[str] = []
    try:
        for name in names:
            destination = artifacts.artifact_root / name
            previous = rollback / name
            if destination.exists() or destination.is_symlink():
                os.replace(destination, previous)
            os.replace(staging / name, destination)
            installed.append(name)
    except Exception:
        for name in reversed(names):
            destination = artifacts.artifact_root / name
            previous = rollback / name
            if name in installed and (destination.exists() or destination.is_symlink()):
                if destination.is_dir() and not destination.is_symlink():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            if previous.exists() or previous.is_symlink():
                os.replace(previous, destination)
        raise
    finally:
        shutil.rmtree(rollback, ignore_errors=True)
        shutil.rmtree(staging, ignore_errors=True)
        if staging_parent.is_dir() and not any(staging_parent.iterdir()):
            staging_parent.rmdir()


def project_reader_bundle(
    inputs: ReaderBundleStructureInputs | ReaderBundleInputs,
    artifacts: BundleArtifactPaths,
) -> CommittedBundleRun:
    if artifacts.artifact_root.is_symlink():
        raise ValidationError("reader-bundle", artifacts.artifact_root, "artifact root must not be a symlink")
    run_id = f"run-{uuid.uuid4().hex[:16]}"
    staging = artifacts.artifact_root / ".staging" / run_id
    staging.mkdir(parents=True)
    staged = BundleArtifactPaths(
        artifacts.artifact_root,
        staging / "bundle",
        staging / "audit",
        staging / "reports",
        staging / "reports" / "projection-report.json",
        staging / "reports" / "exit-manifest.json",
    )
    try:
        raw_index, source_inventory, input_readback, entry_check, loaded = _load_inputs(inputs)
        if raw_index.get("schema_version") != TOPIC_INDEX_SCHEMA or not isinstance(raw_index.get("topics"), list):
            raise ValidationError("reader-bundle", "topic-index", "unsupported TopicIndex envelope")
        source_map = _source_rows(source_inventory)
        claim_map: dict[str, dict[str, Any]] = {}
        selection_map: dict[tuple[str, str], dict[str, Any]] = {}
        if isinstance(inputs, ReaderBundleInputs):
            claim_map = _claim_map(loaded.get("claims", []))
            selection_map = _selection_map(loaded.get("selection"))
        staged.bundle_dir.mkdir(parents=True)
        (staged.bundle_dir / "references").mkdir()
        (staged.bundle_dir / "Home.md").write_text("# Home\n\n[Reader index](index.md)\n", encoding="utf-8")
        (staged.bundle_dir / "README.md").write_text("# Reader Bundle\n\nThis isolated Task 2-A projection is not released.\n", encoding="utf-8")
        (staged.bundle_dir / "log.md").write_text(f"# Projection log\n\n- digest_release_status: `{_NOT_RELEASED}`\n- change: initial isolated projection\n", encoding="utf-8")
        degraded: list[dict[str, Any]] = []
        concepts: list[tuple[str, str, str, str]] = []
        source_projection: list[dict[str, Any]] = []
        matched_selection_keys: set[tuple[str, str]] = set()
        projected_paths: set[str] = set()
        product_labels: dict[str, str] = {}
        product_descriptions: dict[str, str] = {}
        module_labels: dict[tuple[str, str], tuple[str, str]] = {}
        for row_number, row in enumerate(raw_index["topics"]):
            adapter = adapt_topic_index_row(row, source_ref=inputs.topic_index_ref, row_number=row_number)
            if adapter.branch == "degraded":
                record = _degraded_record(adapter, row_number)
                degraded.append(record)
                _write_degraded(staged, record)
                continue
            selection_key = (str((adapter.row or {}).get("topic_id") or (adapter.row or {}).get("topic_key") or (adapter.row or {}).get("digest_topic_id") or ""), str((adapter.row or {}).get("object_intent") or ""))
            selection = selection_map.get(selection_key)
            if selection is not None:
                matched_selection_keys.add(selection_key)
            body = _fixture_body(inputs.input_root, selection) if selection else ""
            source_row = next((source_map.get(str(source_id)) for source_id in (row.get("source_members") or row.get("source_ids") or []) if source_map.get(str(source_id))), None)
            selected = _title_description(row, adapter, body=body, source_row=source_row)
            if selected is None:
                record = _degraded_record(TopicIndexAdapterResult("degraded", adapter.digest_topic_key, adapter.digest_topic_id, adapter.product, adapter.module, adapter.object_intent, None, ("TITLE_OR_DESCRIPTION_UNREADABLE",), row), row_number)
                degraded.append(record)
                _write_degraded(staged, record)
                continue
            title, description = selected
            page_type = _selected_page_type(adapter, selection)
            rel = _concept_path(adapter)
            if rel in projected_paths:
                raise ValidationError("reader-bundle", rel, "projected concept path collides after slug normalization")
            projected_paths.add(rel)
            target = staged.bundle_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            body = body if selection else f"# {title}\n\n{description}\n"
            frontmatter = _selected_frontmatter(adapter, row, source_map, claim_map, selection, page_type=page_type, title=title, description=description) if selection else _concept_frontmatter(adapter, row, source_map, page_type=page_type, title=title, description=description)
            frontmatter["generated"] = _generated_record()
            frontmatter["digest_machine_pass"] = True
            stale_after = _explicit_stale_after(source_row)
            if stale_after is not None:
                frontmatter["stale_after"] = stale_after
            evidence_ref = _trust_audit_ref(rel)
            content_hash = managed_content_hash(frontmatter, body)
            events = _trust_events(frontmatter, body, selection, content_hash=content_hash, evidence_ref=evidence_ref)
            if events:
                frontmatter["verified"] = events
            audit_ref = staged.audit_dir / PurePosixPath(evidence_ref).relative_to("audit")
            _write_json(audit_ref, {
                "schema_version": _TRUST_SCHEMA,
                "version": "1",
                "page_path": rel,
                "topic_id": adapter.digest_topic_id,
                "generated": frontmatter["generated"],
                "machine_pass": True,
                "content_hash": content_hash,
                "events": events,
            })
            frontmatter["digest_content_hash"] = content_hash
            target.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
            concepts.append((rel, title, description, page_type))
            product_key = _slug(str(adapter.product), "product")
            product_labels.setdefault(product_key, _normalize_readable(str(adapter.product)))
            if page_type == "product_overview":
                product_descriptions[product_key] = description
            else:
                product_descriptions.setdefault(product_key, description)
            if adapter.module:
                module_key = _slug(str(adapter.module), "module")
                module_labels.setdefault((product_key, module_key), (_normalize_readable(str(adapter.module)), description))
            for source_id in row.get("source_members") or row.get("source_ids") or []:
                source = source_map.get(source_id)
                if source:
                    source_projection.append({"id": source_id, "resource": source.get("source_uri"), "title": source.get("title") or source.get("content_path"), "digest_content_fingerprint": source.get("content_fingerprint")})
        if selection_map:
            unmatched = sorted(set(selection_map) - matched_selection_keys)
            if unmatched:
                raise ValidationError("reader-bundle", unmatched[0], "fixture selection has no matching TopicIndex concept")
        product_dirs: dict[str, list[tuple[str, str, str, str]]] = {}
        module_dirs: dict[tuple[str, str], list[tuple[str, str, str, str]]] = {}
        for rel, title, description, page_type in concepts:
            parts = PurePosixPath(rel).parts
            product = parts[1]
            product_dirs.setdefault(product, []).append((rel, title, description, page_type))
            if page_type != "product_overview":
                module_dirs.setdefault((product, parts[3]), []).append((rel, title, description, page_type))
                module_labels.setdefault((product, parts[3]), (title, description))
        products_root = staged.bundle_dir / "products"
        products_root.mkdir(parents=True, exist_ok=True)
        root_lines = ["# Reader index", "", "## Products", "", "- [Products](products/index.md) — Published products"]
        products_index_lines = ["# Products", ""]
        for product in sorted(product_dirs):
            product_index = staged.bundle_dir / "products" / product / "index.md"
            product_index.parent.mkdir(parents=True, exist_ok=True)
            product_label = product_labels.get(product, _normalize_readable(product))
            product_description = product_descriptions.get(product, "")
            products_index_lines.append(f"- [{_link_label(product_label)}]({product}/index.md) — {product_description}")
            lines = [f"# {product_label}", ""]
            for rel, title, description, page_type in sorted(product_dirs[product]):
                parts = PurePosixPath(rel).parts
                if page_type == "product_overview":
                    target = PurePosixPath(rel).relative_to(PurePosixPath("products") / product)
                    lines.append(f"- [{_link_label(title)}]({target.as_posix()}) — {description}")
            modules = sorted({PurePosixPath(rel).parts[3] for rel, _title, _description, page_type in product_dirs[product] if page_type != "product_overview"})
            if modules:
                lines.append(f"- [Modules](modules/index.md) — {len(modules)} published module(s)")
            product_index.write_text("\n".join(lines) + "\n", encoding="utf-8")
        (products_root / "index.md").write_text("\n".join(products_index_lines) + "\n", encoding="utf-8")
        for product in sorted({product for product, _module in module_dirs}):
            modules_index = products_root / product / "modules" / "index.md"
            modules_index.parent.mkdir(parents=True, exist_ok=True)
            module_lines = ["# Modules", ""]
            for (module_product, module), _items in sorted(module_dirs.items()):
                if module_product != product:
                    continue
                module_title, module_description = module_labels[(product, module)]
                module_lines.append(f"- [{_link_label(module_title)}]({module}/index.md) — {module_description}")
            modules_index.write_text("\n".join(module_lines) + "\n", encoding="utf-8")
        for (product, module), items in sorted(module_dirs.items()):
            module_index = staged.bundle_dir / "products" / product / "modules" / module / "index.md"
            module_index.parent.mkdir(parents=True, exist_ok=True)
            module_title, _module_description = module_labels.get((product, module), (_normalize_readable(module), ""))
            lines = [f"# {module_title}", ""]
            for rel, title, description, _page_type in sorted(items):
                target = PurePosixPath(rel).relative_to(PurePosixPath("products") / product / "modules" / module)
                lines.append(f"- [{_link_label(title)}]({target.as_posix()}) — {description}")
            module_index.write_text("\n".join(lines) + "\n", encoding="utf-8")
        (staged.bundle_dir / "index.md").write_text("\n".join(root_lines) + "\n", encoding="utf-8")
        source_lines = ["# Sources", "", "<!-- projected from the same audit records -->", ""]
        for source in sorted({json.dumps(item, ensure_ascii=False, sort_keys=True): item for item in source_projection}.values(), key=lambda item: item["id"]):
            source_lines.append(f"- `{source['id']}`: {source['title']} ({source['resource']})")
        (staged.bundle_dir / "references" / "sources.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")
        entry_backfill = write_entry_backfill_manifest(entry_check, staged, run_id=run_id) if entry_check.status != "passed" else None
        report_value = {
            "schema_version": "reader-bundle-report.v1",
            "run_id": run_id,
            "ac08_result": _AC08_BLOCKED,
            "digest_release_status": _NOT_RELEASED,
            "bundle_ref": "bundle",
            "audit_ref": "audit",
            "projection_report_ref": "reports/projection-report.json",
            "exit_manifest_ref": "reports/exit-manifest.json",
            "degraded_records": degraded,
            "input_readback": list(input_readback),
            "entry_binding": {"status": entry_check.status, "missing_refs": list(entry_check.missing_refs), "backfill_ref": entry_backfill.path if entry_backfill else None},
            "concept_count": len(concepts),
            "source_count": len(source_projection),
            "claim_count": len(claim_map),
        }
        _write_json(staged.projection_report_path, report_value)
        bundle_hash = _sha256_tree(staged.bundle_dir)
        _write_json(staged.exit_manifest_path, {"schema_version": "reader-bundle-exit-manifest.v1", "run_id": run_id, "ac08_result": _AC08_BLOCKED, "digest_release_status": _NOT_RELEASED, "bundle_hash": bundle_hash, "reason": "parser smoke is owned by Phase 3"})
        initial = BundleArtifactPaths(artifacts.artifact_root, staged.bundle_dir, staged.audit_dir, staged.reports_dir, staged.projection_report_path, staged.exit_manifest_path)
        validation = validate_reader_bundle(initial, inputs)
        if validation.status != "passed":
            raise ValidationError("reader-bundle", artifacts.artifact_root, "staged Bundle validation failed: " + ",".join(validation.error_codes))
        _atomic_commit(staging, artifacts)
        report = BundleReport(
            schema_version="reader-bundle-report.v1",
            run_id=run_id,
            profile=report_value.get("profile"),
            ac08_result=report_value["ac08_result"],
            release_status=report_value["digest_release_status"],
            bundle_ref=report_value["bundle_ref"],
            audit_ref=report_value["audit_ref"],
            projection_report_ref=report_value["projection_report_ref"],
            exit_manifest_ref=report_value["exit_manifest_ref"],
            degraded_records=tuple(degraded),
            input_readback=tuple(input_readback),
            entry_binding=report_value["entry_binding"],
            concept_count=report_value["concept_count"],
            source_count=report_value["source_count"],
            claim_count=report_value["claim_count"],
        )
        return CommittedBundleRun(
            artifact_root=artifacts.artifact_root,
            run_id=run_id,
            base_bundle_hash=_sha256_tree(artifacts.bundle_dir),
            base_projection_report_hash=_sha256_path(artifacts.projection_report_path),
            base_exit_manifest_hash=_sha256_path(artifacts.exit_manifest_path),
            report=report,
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        staging_parent = artifacts.artifact_root / ".staging"
        if staging_parent.is_dir() and not any(staging_parent.iterdir()):
            staging_parent.rmdir()
        raise


def _valid_okf_root_index(text: str) -> bool:
    if not text.startswith("---\n"):
        return False
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return False
    try:
        frontmatter = yaml.safe_load(parts[0][4:])
    except yaml.YAMLError:
        return False
    return isinstance(frontmatter, dict) and frontmatter == {"okf_version": "0.2"}


def validate_reader_bundle(
    artifacts: BundleArtifactPaths,
    expected: ReaderBundleStructureInputs | ReaderBundleInputs | None,
) -> BundleValidationReport:
    errors: list[str] = []
    checked: list[str] = []
    bundle = artifacts.bundle_dir
    if not bundle.is_dir() or not artifacts.audit_dir.is_dir() or not artifacts.reports_dir.is_dir():
        errors.append("ARTIFACT_SURFACE_MISSING")
        return BundleValidationReport("reader-bundle-validation.v1", "failed", (), tuple(errors), 0, 0, 0, 0, str(artifacts.artifact_root))
    for required in ("README.md", "Home.md", "index.md", "log.md", "references/sources.md"):
        path = bundle / required
        checked.append(required)
        if not path.is_file():
            errors.append("BUNDLE_REQUIRED_FILE_MISSING")
    allowed_root_files = {"README.md", "Home.md", "index.md", "log.md", "references/sources.md"}
    for path in sorted(bundle.rglob("*")):
        rel = path.relative_to(bundle).as_posix()
        if path.is_symlink():
            errors.append("BUNDLE_SYMLINK_FORBIDDEN")
            continue
        if path.is_file() and (rel not in allowed_root_files and (not rel.startswith("products/") or path.suffix != ".md")):
            errors.append("BUNDLE_FILE_NOT_ALLOWLISTED")
    if (bundle / "Home.md").is_file():
        home_targets = _markdown_link_targets((bundle / "Home.md").read_text(encoding="utf-8"))
        if len(home_targets) != 1 or home_targets[0] != "index.md":
            errors.append("HOME_TARGET_INVALID")
    if any(path.is_dir() and path.name in {"_digest", "_archive"} for path in bundle.rglob("*")):
        errors.append("BUNDLE_AUDIT_ESCAPE")
    concepts = 0
    expected_claims: dict[str, dict[str, Any]] = {}
    if isinstance(expected, ReaderBundleInputs):
        try:
            _raw_index, _source_inventory, _readback, _entry_check, loaded = _load_inputs(expected)
            expected_claims = _claim_map(loaded.get("claims", []))
        except ValidationError:
            errors.append("INPUT_READBACK_INVALID")
    for path in sorted(bundle.rglob("*.md")):
        rel = path.relative_to(bundle).as_posix()
        checked.append(rel)
        if rel in EXEMPT_FILES:
            if path.read_text(encoding="utf-8").startswith("---\n"):
                errors.append("EXEMPT_FILE_FRONTMATTER")
            continue
        if path.name in {"index.md", "log.md"}:
            continue
        concepts += 1
        try:
            frontmatter, body = parse_concept_document(path.read_text(encoding="utf-8"))
        except ValidationError:
            errors.append("CONCEPT_FRONTMATTER_INVALID")
            continue
        if frontmatter.get("type") not in set(CONCEPT_TYPES.values()):
            errors.append("CONCEPT_TYPE_UNSUPPORTED")
        if not isinstance(frontmatter.get("title"), str) or not frontmatter["title"].strip():
            errors.append("CONCEPT_TITLE_UNREADABLE")
        if not isinstance(frontmatter.get("description"), str) or not frontmatter["description"].strip() or "\n" in frontmatter["description"]:
            errors.append("CONCEPT_DESCRIPTION_UNREADABLE")
        if frontmatter.get("digest_page_status") != "published":
            errors.append("PAGE_STATUS_INVALID")
        if frontmatter.get("digest_release_status") is not None:
            errors.append("RELEASE_STATUS_ON_CONCEPT")
        if frontmatter.get("digest_content_hash") != managed_content_hash(frontmatter, body):
            errors.append("MANAGED_HASH_MISMATCH")
        errors.extend(_validate_trust_signals(path, frontmatter, body, artifacts, expected))
        if isinstance(expected, ReaderBundleInputs):
            _count, attribution_errors = _validate_attribution(path, frontmatter, body, expected_claims)
            errors.extend(attribution_errors)
    for path in sorted(bundle.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(bundle).as_posix()
        if path.name == "log.md" and rel != "log.md":
            errors.append("NESTED_LOG_FORBIDDEN")
        if path.name == "index.md" and text.startswith("---\n"):
            if path.parent != bundle:
                errors.append("NESTED_INDEX_FRONTMATTER")
            elif not _valid_okf_root_index(text):
                errors.append("ROOT_INDEX_FRONTMATTER")
        if path.name == "index.md" and not re.search(r"\[[^]]+\]\([^)]+\)", text):
            errors.append(f"EMPTY_INDEX:{rel}")
        for target in _markdown_link_targets(text):
            try:
                if not _relative_target(path, target, bundle).is_file():
                    errors.append("LINK_TARGET_MISSING")
            except ValidationError:
                errors.append("LINK_ESCAPES_BUNDLE")
    report_path = artifacts.projection_report_path
    if not report_path.is_file() or not artifacts.exit_manifest_path.is_file():
        errors.append("REPORT_SURFACE_MISSING")
        return BundleValidationReport("reader-bundle-validation.v1", "failed", tuple(checked), tuple(sorted(set(errors))), 0, 0, 0, 0, str(artifacts.artifact_root))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    exit_manifest = json.loads(artifacts.exit_manifest_path.read_text(encoding="utf-8"))
    if report.get("digest_release_status") != "not_released" or exit_manifest.get("digest_release_status") != "not_released":
        errors.append("RELEASE_STATUS_INVALID")
    degraded = report.get("degraded_records") if isinstance(report.get("degraded_records"), list) else []
    matched = 0
    for record in degraded:
        target_ref = PurePosixPath(str(record.get("audit_target", "")))
        target = artifacts.audit_dir.joinpath(*target_ref.parts[1:]) if target_ref.parts and target_ref.parts[0] == "audit" else artifacts.artifact_root / "invalid-degraded-target"
        if target.is_file() and target.is_relative_to(artifacts.artifact_root):
            matched += 1
        else:
            errors.append("DEGRADED_AUDIT_TARGET_MISSING")
    backfill = report.get("entry_binding", {})
    if backfill.get("status") != "passed" and not backfill.get("backfill_ref"):
        errors.append("ENTRY_BACKFILL_MISSING")
    return BundleValidationReport("reader-bundle-validation.v1", "failed" if errors else "passed", tuple(checked), tuple(sorted(set(errors))), concepts, int(report.get("source_count", 0)), int(report.get("claim_count", 0)), matched, str(artifacts.artifact_root))


def _existing_artifacts(root: Path) -> BundleArtifactPaths:
    return BundleArtifactPaths(root, root / "bundle", root / "audit", root / "reports", root / "reports" / "projection-report.json", root / "reports" / "exit-manifest.json")


def _smoke_result_dict(smoke: Any) -> dict[str, Any]:
    return {
        "schema_version": smoke.schema_version,
        "status": smoke.status,
        "source_ref": smoke.source_ref,
        "attempt_ref": smoke.attempt_ref,
        "source_commit": smoke.source_commit,
        "vendor_hash": smoke.vendor_hash,
        "license_hash": smoke.license_hash,
        "notice_hash": smoke.notice_hash,
        "bundle_hash": smoke.bundle_hash,
        "read_boundary": list(smoke.read_boundary),
        "read_summary": dict(smoke.read_summary),
        "reason": smoke.reason,
    }


def _validate_smoke_provenance(run: CommittedBundleRun, smoke: Any) -> None:
    if smoke.schema_version != "okf-parser-smoke.v1":
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke schema is unsupported")
    if smoke.status not in {"passed", "failed", "unavailable", "blocked"}:
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke status is ambiguous")
    if not isinstance(smoke.source_ref, str) or not smoke.source_ref.strip() or not re.fullmatch(r"[0-9a-f]{40}", str(smoke.source_commit)):
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke source provenance is incomplete")
    for field in ("vendor_hash", "license_hash", "notice_hash", "bundle_hash"):
        if not isinstance(getattr(smoke, field), str) or not _SHA256.fullmatch(getattr(smoke, field)):
            raise ValidationError("reader-bundle", run.artifact_root, f"parser smoke {field} provenance is incomplete")
    if smoke.bundle_hash != run.base_bundle_hash:
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke bundle hash does not match committed Bundle")
    if tuple(smoke.read_boundary) != ("bundle/document.py", "bundle/index.py", "bundle/paths.py"):
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke read boundary is unsupported")
    if not isinstance(smoke.attempt_ref, str) or not smoke.attempt_ref.startswith("audit/parser-smoke/"):
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke attempt provenance is incomplete")
    attempt_path = run.artifact_root / PurePosixPath(smoke.attempt_ref)
    if not attempt_path.is_file() or not attempt_path.is_relative_to(run.artifact_root):
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke attempt evidence is missing")
    try:
        attempt_evidence = json.loads(attempt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke attempt evidence is unreadable") from exc
    expected_attempt = {
        "attempt_ref": smoke.attempt_ref,
        "bundle_hash": smoke.bundle_hash,
        "source_ref": smoke.source_ref,
        "source_commit": smoke.source_commit,
        "vendor_hash": smoke.vendor_hash,
        "license_hash": smoke.license_hash,
        "notice_hash": smoke.notice_hash,
        "read_boundary": list(smoke.read_boundary),
    }
    if any(attempt_evidence.get(key) != value for key, value in expected_attempt.items()):
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke attempt evidence does not match result")
    if smoke.status in {"failed", "unavailable"} and (not isinstance(smoke.reason, str) or not smoke.reason.strip()):
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke downgrade reason is missing")
    if smoke.status == "passed" and smoke.reason is not None:
        raise ValidationError("reader-bundle", run.artifact_root, "parser smoke pass cannot carry a failure reason")


def finalize_bundle_profile(run: CommittedBundleRun, smoke: Any) -> BundleReport:
    """Atomically attach the parser profile to one already-committed Bundle."""

    artifacts = _existing_artifacts(Path(run.artifact_root))
    current_hashes = (
        _sha256_tree(artifacts.bundle_dir),
        _sha256_path(artifacts.projection_report_path),
        _sha256_path(artifacts.exit_manifest_path),
    )
    expected_hashes = (run.base_bundle_hash, run.base_projection_report_hash, run.base_exit_manifest_hash)
    if current_hashes != expected_hashes:
        raise ValidationError("reader-bundle", run.artifact_root, "committed Bundle base hashes changed before parser finalize")
    blocked = smoke.status == "blocked"
    if not blocked:
        _validate_smoke_provenance(run, smoke)
    base_validation = validate_reader_bundle(artifacts, None)
    if base_validation.status != "passed":
        raise ValidationError("reader-bundle", run.artifact_root, "committed Bundle validation failed: " + ",".join(base_validation.error_codes))
    staging_parent = artifacts.artifact_root / ".staging"
    staging = staging_parent / f"parser-profile-{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        for name in ("bundle", "audit", "reports"):
            shutil.copytree(artifacts.artifact_root / name, staging / name)
        projection_path = staging / "reports" / "projection-report.json"
        exit_path = staging / "reports" / "exit-manifest.json"
        projection = json.loads(projection_path.read_text(encoding="utf-8"))
        if smoke.status == "passed":
            from .okf_smoke import create_smoke_attempt, read_vendor_ref, run_parser_smoke

            profile = "OKF-compatible"
            ac08_result = "compatibility_passed"
            root_index = staging / "bundle" / "index.md"
            original_root_index = root_index.read_bytes()
            if not _valid_okf_root_index(root_index.read_text(encoding="utf-8")):
                root_index.write_bytes(b"---\nokf_version: \"0.2\"\n---\n" + original_root_index)
            vendor_root = getattr(smoke, "vendor_root", None)
            if not isinstance(vendor_root, Path) or not vendor_root.is_absolute():
                raise ValidationError("reader-bundle", staging, "parser smoke vendor root is unavailable for final-byte recheck")
            try:
                vendor = read_vendor_ref(vendor_root)
            except ValidationError as exc:
                raise ValidationError("reader-bundle", staging, "parser smoke vendor readback failed during final-byte recheck") from exc
            final_attempt = create_smoke_attempt(staging, vendor)
            final_smoke = run_parser_smoke(staging, vendor, final_attempt)
            if final_smoke.status != "passed":
                root_index.write_bytes(original_root_index)
                raise ValidationError("reader-bundle", staging, "final Bundle bytes failed parser smoke recheck")
            smoke_for_manifest = final_smoke
            reason = "parser smoke passed"
        elif blocked:
            blocked_attempt_ref = getattr(smoke, "attempt_ref", "")
            if blocked_attempt_ref:
                blocked_attempt_path = artifacts.artifact_root / PurePosixPath(str(blocked_attempt_ref))
                if not str(blocked_attempt_ref).startswith("audit/parser-smoke/") or not blocked_attempt_path.is_file() or not blocked_attempt_path.is_relative_to(artifacts.artifact_root):
                    raise ValidationError("reader-bundle", run.artifact_root, "blocked parser smoke attempt evidence is invalid")
            profile = run.report.profile
            ac08_result = _AC08_BLOCKED
            smoke_for_manifest = smoke
            reason = f"parser smoke blocked: {smoke.reason or 'PARSER_SMOKE_BLOCKED'}"
        else:
            profile = "OKF-inspired profile"
            ac08_result = "honest_downgrade_passed"
            smoke_for_manifest = smoke
            reason = f"parser smoke {smoke.status}: {smoke.reason}"
        projection["profile"] = profile
        projection["ac08_result"] = ac08_result
        projection["parser_smoke"] = _smoke_result_dict(smoke_for_manifest)
        _write_json(projection_path, projection)
        exit_manifest = json.loads(exit_path.read_text(encoding="utf-8"))
        exit_manifest.update({"profile": profile, "ac08_result": ac08_result, "reason": reason, "parser_smoke": _smoke_result_dict(smoke_for_manifest)})
        exit_manifest["bundle_hash"] = _sha256_tree(staging / "bundle")
        _write_json(exit_path, exit_manifest)
        staged = _existing_artifacts(staging)
        validation = validate_reader_bundle(staged, None)
        if validation.status != "passed":
            raise ValidationError("reader-bundle", staging, "parser profile validation failed: " + ",".join(validation.error_codes))
        _atomic_commit(staging, artifacts)
        return BundleReport(
            schema_version=run.report.schema_version,
            run_id=run.report.run_id,
            profile=profile,
            ac08_result=ac08_result,
            release_status=run.report.release_status,
            bundle_ref=run.report.bundle_ref,
            audit_ref=run.report.audit_ref,
            projection_report_ref=run.report.projection_report_ref,
            exit_manifest_ref=run.report.exit_manifest_ref,
            degraded_records=run.report.degraded_records,
            input_readback=run.report.input_readback,
            entry_binding=run.report.entry_binding,
            concept_count=run.report.concept_count,
            source_count=run.report.source_count,
            claim_count=run.report.claim_count,
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        if staging_parent.is_dir() and not any(staging_parent.iterdir()):
            staging_parent.rmdir()
        raise
