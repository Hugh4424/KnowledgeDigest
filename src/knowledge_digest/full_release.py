"""Task 3 package-level quality summary and release boundary."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .errors import ValidationError
from .lock import kb_lock
from .reader_bundle import BundleArtifactPaths, validate_reader_bundle
from .reader_frontmatter import parse_concept_document
from .reader_quality import ReaderQualityPolicy, _canonical_question_set_hash


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CONFIRMATION_MAX_AGE = timedelta(hours=24)
_TASK0_QUESTION_SET_PATH = Path(__file__).resolve().parents[2] / "config" / "task0-question-set.v1.json"
_COMPARISON_DIMENSIONS = (
    "saved_integrity",
    "machine_quality",
    "reader_readability",
    "trust_freshness",
    "failures",
    "performance",
    "cost",
    "limitations",
)
_FORMAL_ROOT_REQUIRED_PATHS = (
    "bundle/README.md",
    "bundle/index.md",
    "audit/source-manifest.json",
    "reports/projection-report.json",
    "reports/exit-manifest.json",
)


@dataclass(frozen=True)
class SummaryConfirmation:
    run_id: str
    summary_sha256: str
    actor: str
    confirmed_at: str
    meaning: str = "automatic-summary-confirmation"
    summary_file_sha256: str | None = None


@dataclass(frozen=True)
class FullReleaseEvidence:
    run_id: str
    snapshot: Mapping[str, Any]
    quality: Any
    delivery: Mapping[str, Any]
    mode: str
    candidate_root: Path | None = None
    formal_root: Path | None = None
    # Kept for positional/API compatibility with earlier evidence adapters.
    # prepare_full_release derives protection from the formal-root preflight;
    # it does not trust this caller-supplied flag.
    old_package_protected: bool = False
    comparison: Mapping[str, Any] | None = None
    expected_source_manifest: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class PreparedFullRelease:
    status: str
    summary: Mapping[str, Any]
    summary_sha256: str
    hard_failures: tuple[str, ...]
    warnings: tuple[str, ...]
    unknowns: tuple[str, ...]
    candidate_tree_hash: str | None = None
    summary_path: Path | None = None
    summary_file_sha256: str | None = None


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _quality_scorecard_hash(quality: Any) -> str | None:
    """Recompute the Task 3 scorecard binding from the supplied result."""

    scorecard_hash = _quality_field(quality, "scorecard_hash", None)
    if not isinstance(scorecard_hash, str) or not _SHA256.fullmatch(scorecard_hash):
        return None
    records = _quality_field(quality, "records", ())
    record_list = list(records) if isinstance(records, (list, tuple)) else []
    provenance = _quality_field(quality, "provenance", {})
    provenance = dict(provenance) if isinstance(provenance, Mapping) else {}
    canonical_scorecard = {
        "schema_version": "task3-quality-scorecard.v1",
        "policy": ReaderQualityPolicy().as_dict(),
        "summary": dict(_quality_field(quality, "summary", {})) if isinstance(_quality_field(quality, "summary", {}), Mapping) else {},
        "title_check": dict(_quality_field(quality, "title_check", {})) if isinstance(_quality_field(quality, "title_check", {}), Mapping) else {},
        "ownership_check": dict(_quality_field(quality, "ownership_check", {})) if isinstance(_quality_field(quality, "ownership_check", {}), Mapping) else {},
        "hard_failures": sorted(set(str(item) for item in _quality_field(quality, "hard_failures", ()) or ())),
        "warnings": sorted(set(str(item) for item in _quality_field(quality, "warnings", ()) or ())),
        "unknowns": sorted(set(str(item) for item in _quality_field(quality, "unknowns", ()) or ())),
        "provenance": provenance,
        "replay": dict(_quality_field(quality, "replay", {})) if isinstance(_quality_field(quality, "replay", {}), Mapping) else {},
    }
    record_hash = hashlib.sha256(json.dumps(record_list, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if provenance.get("question_hash") != record_hash:
        return None
    return _hash(canonical_scorecard)


def _source_manifest_hash(manifest: Mapping[str, Any]) -> str:
    return _hash(dict(manifest))


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _has_unsupported_nodes(root: Path) -> bool:
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        try:
            mode = path.lstat().st_mode
        except OSError:
            return True
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            return True
    return False


def inspect_formal_root(formal_root: Path | None) -> dict[str, Any]:
    """Return a read-only, hash-bound preflight for the release target.

    A missing target is valid only for an explicitly supplied first release
    path whose parent already exists.  An existing target must be a complete,
    regular-file package.  This keeps ``old_package_protected`` from being a
    caller-supplied claim about an arbitrary directory.
    """

    if formal_root is None:
        return {"status": "missing", "protected": False, "tree_hash": None, "reason": "formal root was not supplied"}
    root = Path(formal_root)
    if root.is_symlink():
        return {"status": "invalid", "protected": False, "tree_hash": None, "reason": "formal root is a symlink"}
    if not root.exists():
        parent = root.parent
        if parent.is_symlink() or not parent.is_dir():
            return {"status": "invalid", "protected": False, "tree_hash": None, "reason": "formal root parent is not an existing directory"}
        return {"status": "absent", "protected": True, "tree_hash": None, "reason": "no previous formal package exists"}
    if not root.is_dir() or _has_unsupported_nodes(root) or any(path.is_symlink() for path in root.rglob("*")):
        return {"status": "invalid", "protected": False, "tree_hash": None, "reason": "formal root contains an unsupported node"}
    missing = [relative for relative in _FORMAL_ROOT_REQUIRED_PATHS if not (root / relative).is_file()]
    if missing:
        return {
            "status": "invalid",
            "protected": False,
            "tree_hash": None,
            "reason": "formal package is incomplete: " + ", ".join(missing),
        }
    try:
        tree_hash = _tree_hash(root)
    except OSError:
        return {"status": "invalid", "protected": False, "tree_hash": None, "reason": "formal package cannot be hashed"}
    return {"status": "existing", "protected": True, "tree_hash": tree_hash, "reason": "existing formal package is hash-bound"}


def _quality_field(quality: Any, field: str, default: Any) -> Any:
    if isinstance(quality, Mapping):
        return quality.get(field, default)
    return getattr(quality, field, default)


def _candidate_replay_path(candidate_root: Path, reference: Any) -> Path | None:
    if not isinstance(reference, str) or not reference.strip():
        return None
    try:
        relative = PurePosixPath(reference)
    except (TypeError, ValueError):
        return None
    if relative.is_absolute() or ".." in relative.parts or "\\" in reference:
        return None
    candidate = candidate_root.joinpath(*relative.parts)
    if candidate.is_symlink() or not candidate.is_file():
        return None
    try:
        if not candidate.resolve().is_relative_to(candidate_root.resolve()):
            return None
    except OSError:
        return None
    return candidate


def summary_sha256(summary: Mapping[str, Any]) -> str:
    value = {key: item for key, item in summary.items() if key != "summary_sha256"}
    return _hash(value)


def build_release_summary(
    *,
    run_id: str,
    quality: Any,
    delivery: Mapping[str, Any],
    mode: str,
    old_package_protected: bool,
) -> dict[str, Any]:
    quality_summary = _quality_field(quality, "summary", {})
    title_check = _quality_field(quality, "title_check", {})
    ownership_check = _quality_field(quality, "ownership_check", {})
    hard_failures = list(_quality_field(quality, "hard_failures", ())) + list(delivery.get("hard_failures", ()))
    warnings = list(_quality_field(quality, "warnings", ())) + list(delivery.get("warnings", ()))
    unknowns = list(_quality_field(quality, "unknowns", ())) + list(delivery.get("unknowns", ()))
    quality_status = _quality_field(quality, "status", "failed")
    delivery_status = str(delivery.get("status") or "failed")
    completion = "complete" if quality_status == "passed" and delivery_status == "passed" and not hard_failures and not unknowns else "incomplete"
    records = _quality_field(quality, "records", ())
    provenance = _quality_field(quality, "provenance", {})
    reader_quality = dict(quality_summary) if isinstance(quality_summary, Mapping) else {}
    reader_quality.update(
        {
            "run_id": run_id,
            "scorecard_hash": _quality_field(quality, "scorecard_hash", None),
            "question_count": len(records) if isinstance(records, (list, tuple)) else 0,
            "records_hash": provenance.get("question_hash") if isinstance(provenance, Mapping) else None,
            "provenance": dict(provenance) if isinstance(provenance, Mapping) else {},
            "hard_failures": list(_quality_field(quality, "hard_failures", ())),
            "warnings": list(_quality_field(quality, "warnings", ())),
            "unknowns": list(_quality_field(quality, "unknowns", ())),
        }
    )
    summary: dict[str, Any] = {
        "schema_version": "task3-release-summary.v1",
        "run_id": run_id,
        "completion": completion,
        "quality_status": quality_status,
        "delivery_status": delivery_status,
        "hard_failures": sorted(set(str(value) for value in hard_failures)),
        "warnings": sorted(set(str(value) for value in warnings)),
        "unknowns": sorted(set(str(value) for value in unknowns)),
        "reader_quality": reader_quality,
        "accuracy": {"title": dict(title_check) if isinstance(title_check, Mapping) else {}, "ownership": dict(ownership_check) if isinstance(ownership_check, Mapping) else {}},
        "delivery": {key: value for key, value in delivery.items() if key not in {"hard_failures", "warnings", "unknowns"}},
        "mode": mode,
        "old_package_protected": old_package_protected is True,
        "confirmation_required": True,
        "confirmation_meaning": "summary is complete and has no hard failure; it is not content review",
        "digest_release_status": "not_released",
        "agent_only": True,
        "machine_provenance": dict(_quality_field(quality, "provenance", {})),
    }
    summary["summary_sha256"] = summary_sha256(summary)
    return summary


def validate_summary_confirmation(
    confirmation: SummaryConfirmation | Mapping[str, Any] | None,
    *,
    summary: Mapping[str, Any],
    summary_path: Path | None = None,
) -> bool:
    if confirmation is None or not isinstance(summary, Mapping):
        return False
    if isinstance(confirmation, SummaryConfirmation):
        values = confirmation.__dict__
    elif isinstance(confirmation, Mapping):
        values = confirmation
    else:
        return False
    if "human_reviewed" in values or values.get("meaning") != "automatic-summary-confirmation":
        return False
    if not all(isinstance(values.get(field), str) and str(values[field]).strip() for field in ("run_id", "summary_sha256", "actor", "confirmed_at")):
        return False
    if not str(values["actor"]).startswith("human:"):
        return False
    try:
        confirmed_at = datetime.fromisoformat(str(values["confirmed_at"]).replace("Z", "+00:00"))
    except ValueError:
        return False
    if confirmed_at.tzinfo is None:
        return False
    now = datetime.now(timezone.utc)
    confirmed_at = confirmed_at.astimezone(timezone.utc)
    if confirmed_at > now or now - confirmed_at > _CONFIRMATION_MAX_AGE:
        return False
    if summary_path is not None:
        path = Path(summary_path)
        if not path.is_file() or path.is_symlink():
            return False
        declared_file_hash = values.get("summary_file_sha256")
        if not isinstance(declared_file_hash, str) or not _SHA256.fullmatch(declared_file_hash):
            return False
        if hashlib.sha256(path.read_bytes()).hexdigest() != declared_file_hash:
            return False
    return (
        values["run_id"] == summary.get("run_id")
        and values["summary_sha256"] == summary.get("summary_sha256")
        and values["summary_sha256"] == summary_sha256(summary)
        and re_releaseable_summary(summary)
    )


def re_releaseable_summary(summary: Mapping[str, Any]) -> bool:
    forbidden = {"human_reviewed", "verified"}
    if any(key in summary for key in forbidden):
        return False
    return (
        summary.get("completion") == "complete"
        and summary.get("quality_status") == "passed"
        and summary.get("delivery_status") == "passed"
        and summary.get("hard_failures") == []
        and summary.get("unknowns") == []
        and summary.get("mode") == "semantic"
        and summary.get("digest_release_status") == "not_released"
        and summary.get("old_package_protected") is True
        and summary.get("agent_only") is True
    )


def write_release_summary(summary: Mapping[str, Any], output_path: Path) -> str:
    """Persist the one-page machine summary and return its bound hash."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        raw = (json.dumps(dict(summary), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    else:
        lines = [
            "# Task 3 Release Summary",
            "",
            f"- run_id: `{summary.get('run_id')}`",
            f"- completion: `{summary.get('completion')}`",
            f"- digest_release_status: `{summary.get('digest_release_status')}`",
            f"- mode: `{summary.get('mode')}`",
            f"- old_package_protected: `{summary.get('old_package_protected')}`",
            "",
            f"## Hard failures ({len(summary.get('hard_failures', []))})",
            "",
        ]
        lines.extend(f"- `{item}`" for item in summary.get("hard_failures", []))
        lines.extend(["", f"## Warnings ({len(summary.get('warnings', []))})", ""])
        lines.extend(f"- `{item}`" for item in summary.get("warnings", []))
        lines.extend(["", f"## Unknowns ({len(summary.get('unknowns', []))})", ""])
        lines.extend(f"- `{item}`" for item in summary.get("unknowns", []))
        lines.extend([
            "",
            "## Reader quality",
            "",
            f"- 17+3: `{summary.get('reader_quality', {}).get('positive_passed')}/{summary.get('reader_quality', {}).get('positive_count')}`; negative false positives: `{summary.get('reader_quality', {}).get('negative_false_positives')}`",
            f"- title accuracy: `{summary.get('accuracy', {}).get('title', {}).get('rate')}`",
            f"- ownership accuracy: `{summary.get('accuracy', {}).get('ownership', {}).get('rate')}`",
            "",
            "This confirmation is a machine-summary confirmation, not content review.",
            "",
        ])
        raw = "\n".join(lines).encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def release_decision(
    summary: Mapping[str, Any],
    confirmation: SummaryConfirmation | Mapping[str, Any] | None,
    *,
    summary_path: Path | None = None,
) -> str:
    return "released" if validate_summary_confirmation(confirmation, summary=summary, summary_path=summary_path) else "not_released"


def validate_delivery_hard_gates(
    candidate_root: Path,
    *,
    expected: Any = None,
    expected_run_id: str | None = None,
    expected_source_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-read the candidate Reader/Audit surface and return classified facts."""

    root = Path(candidate_root)
    artifact_root = root if (root / "bundle").is_dir() else root.parent if (root.name == "bundle") else root
    bundle = artifact_root / "bundle"
    audit = artifact_root / "audit"
    hard_failures: list[str] = []
    warnings: list[str] = []
    unknowns: list[str] = []
    pages: list[Path] = []
    claim_ids: set[str] = set()
    required_trust_events = {"source_hash_match", "locator_resolved"}
    reports = artifact_root / "reports"
    if root.is_symlink() or artifact_root.is_symlink():
        hard_failures.append("CANDIDATE_ROOT_SYMLINK")
    if artifact_root.is_dir() and _has_unsupported_nodes(artifact_root):
        hard_failures.append("CANDIDATE_SPECIAL_NODE_PRESENT")
        return {
            "status": "failed",
            "hard_failures": hard_failures,
            "warnings": warnings,
            "unknowns": unknowns,
            "reader_hash": None,
            "audit_hash": None,
            "run_id": None,
            "page_count": 0,
            "claim_count": 0,
            "replay_material": False,
        }
    if not bundle.is_dir() or bundle.is_symlink() or not audit.is_dir() or audit.is_symlink() or not reports.is_dir() or reports.is_symlink():
        hard_failures.append("READER_BUNDLE_MISSING")
    else:
        if any(path.is_symlink() for path in artifact_root.rglob("*")):
            hard_failures.append("CANDIDATE_SYMLINK_PRESENT")
        validation = validate_reader_bundle(BundleArtifactPaths(artifact_root, bundle, audit, reports, reports / "projection-report.json", reports / "exit-manifest.json"), expected)
        hard_failures.extend(validation.error_codes)
        pages = [page for page in sorted(bundle.joinpath("products").rglob("*.md")) if page.name != "index.md"] if (bundle / "products").is_dir() else []
        if not pages:
            hard_failures.append("READER_PAGES_MISSING")
        for page in pages:
            if page.name == "index.md":
                continue
            try:
                frontmatter, body = parse_concept_document(page.read_text(encoding="utf-8"))
            except (OSError, ValidationError):
                hard_failures.append("CONCEPT_PAGE_UNREADABLE")
                continue
            if frontmatter.get("digest_page_status") != "published" or frontmatter.get("digest_machine_pass") is not True:
                hard_failures.append("READER_PAGE_NOT_MACHINE_PUBLISHED")
            verified = frontmatter.get("verified")
            if not isinstance(verified, list) or {item.get("event") for item in verified if isinstance(item, Mapping)} != required_trust_events:
                hard_failures.append("READER_TRUST_GATE_INCOMPLETE")
            if len(body.splitlines()) > 120:
                hard_failures.append("BODY_LINES_EXCEEDED")
            if len(page.read_text(encoding="utf-8").splitlines()) > 300:
                hard_failures.append("PAGE_LINES_EXCEEDED")
            sources = frontmatter.get("sources")
            if not isinstance(sources, list) or not sources:
                hard_failures.append("SOURCE_CHAIN_BROKEN")
                continue
            for source in sources:
                claims = source.get("digest_claims") if isinstance(source, Mapping) else None
                if not isinstance(claims, list) or not claims:
                    hard_failures.append("CLAIM_CHAIN_BROKEN")
                    continue
                for claim in claims:
                    if not isinstance(claim, Mapping) or not isinstance(claim.get("claim_id"), str) or not claim["claim_id"]:
                        hard_failures.append("CLAIM_FIELDS_MISSING")
                        continue
                    if claim.get("target_path") != page.relative_to(bundle).as_posix() or not isinstance(claim.get("source_uri"), str) or not claim["source_uri"].strip():
                        hard_failures.append("CLAIM_FIELDS_INVALID")
                    if claim["claim_id"] in claim_ids:
                        hard_failures.append("CLAIM_ID_DUPLICATED")
                    claim_ids.add(claim["claim_id"])
            if frontmatter.get("digest_page_status") == "degraded":
                warnings.append("DEGRADED_PAGE_AUDIT_ONLY")
    source_manifest_path = audit / "source-manifest.json"
    source_manifest: Mapping[str, Any] | None = None
    source_by_id: dict[str, Mapping[str, Any]] = {}
    if not source_manifest_path.is_file() or source_manifest_path.is_symlink():
        hard_failures.append("SOURCE_MANIFEST_MISSING")
    else:
        try:
            loaded_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded_manifest = None
        if not isinstance(loaded_manifest, Mapping) or not isinstance(loaded_manifest.get("entries"), list) or loaded_manifest.get("source_count") != len(loaded_manifest.get("entries", [])):
            hard_failures.append("SOURCE_MANIFEST_INVALID")
        else:
            source_manifest = loaded_manifest
            if loaded_manifest.get("source_count") != 89:
                hard_failures.append("SOURCE_MANIFEST_COUNT_INVALID")
            for entry in loaded_manifest["entries"]:
                if not isinstance(entry, Mapping) or not isinstance(entry.get("source_id"), str) or not isinstance(entry.get("source_uri"), str) or not isinstance(entry.get("content_fingerprint"), str) or not _SHA256.fullmatch(entry["content_fingerprint"]):
                    hard_failures.append("SOURCE_MANIFEST_ENTRY_INVALID")
                    continue
                if entry["source_id"] in source_by_id:
                    hard_failures.append("SOURCE_MANIFEST_ID_DUPLICATED")
                source_by_id[entry["source_id"]] = entry
    replay_files = (reports / "projection-report.json", reports / "exit-manifest.json")
    if any(not path.is_file() for path in replay_files):
        hard_failures.append("REPLAY_MATERIAL_MISSING")
    if any(path.is_symlink() for path in replay_files):
        hard_failures.append("REPLAY_MATERIAL_SYMLINK")
    try:
        projection = json.loads((reports / "projection-report.json").read_text(encoding="utf-8"))
        exit_manifest = json.loads((reports / "exit-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        projection = exit_manifest = None
    if isinstance(projection, Mapping) and isinstance(exit_manifest, Mapping):
        if projection.get("digest_release_status") != "not_released" or exit_manifest.get("digest_release_status") != "not_released":
            hard_failures.append("CANDIDATE_RELEASE_STATUS_INVALID")
        if projection.get("digest_release_status") != exit_manifest.get("digest_release_status"):
            hard_failures.append("PACKAGE_STATUS_PROJECTION_MISMATCH")
        if projection.get("run_id") != exit_manifest.get("run_id"):
            hard_failures.append("PACKAGE_RUN_ID_MISMATCH")
        if expected_run_id is not None and projection.get("run_id") != expected_run_id:
            hard_failures.append("CANDIDATE_RUN_ID_MISMATCH")
        if source_manifest is not None and source_manifest.get("run_id") != projection.get("run_id"):
            hard_failures.append("SOURCE_MANIFEST_RUN_ID_MISMATCH")
        if expected_source_manifest is not None and dict(source_manifest or {}) != dict(expected_source_manifest):
            hard_failures.append("SOURCE_MANIFEST_EXTERNAL_BINDING_INVALID")
    for page in pages:
        try:
            frontmatter, _body = parse_concept_document(page.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            continue
        sources = frontmatter.get("sources") if isinstance(frontmatter, Mapping) else None
        if not isinstance(sources, list):
            continue
        page_claim_fingerprints: dict[str, str] = {}
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            source_id = source.get("id")
            source_uri = source.get("resource")
            fingerprint = source.get("digest_content_fingerprint")
            manifest_entry = source_by_id.get(str(source_id)) if isinstance(source_id, str) else None
            if manifest_entry is None or manifest_entry.get("source_uri") != source_uri or manifest_entry.get("content_fingerprint") != fingerprint or not isinstance(fingerprint, str) or not _SHA256.fullmatch(fingerprint):
                hard_failures.append("SOURCE_CHAIN_NOT_IN_MANIFEST")
            for claim in source.get("digest_claims", []) if isinstance(source.get("digest_claims"), list) else []:
                locator = claim.get("fragment_locator") if isinstance(claim, Mapping) else None
                if (
                    not isinstance(claim, Mapping)
                    or claim.get("source_uri") != source_uri
                    or claim.get("content_fingerprint") != fingerprint
                    or not isinstance(claim.get("content_fingerprint"), str)
                    or not _SHA256.fullmatch(claim["content_fingerprint"])
                    or not isinstance(locator, str)
                    or re.fullmatch(r"lines:\d+(?:-\d+)?", locator.strip()) is None
                ):
                    hard_failures.append("CLAIM_SOURCE_NOT_IN_MANIFEST")
                elif isinstance(claim.get("claim_id"), str):
                    page_claim_fingerprints[claim["claim_id"]] = claim["content_fingerprint"]
        if len(sources) != 1:
            hard_failures.append("TRUST_SOURCE_CARDINALITY_INVALID")
            continue
        source = sources[0]
        source_fingerprint = source.get("digest_content_fingerprint") if isinstance(source, Mapping) else None
        canonical_event_fields = {
            "source_inventory": source_fingerprint,
            "fixture_selection": source_fingerprint,
            "claim_records": page_claim_fingerprints,
        }
        verified = frontmatter.get("verified") if isinstance(frontmatter, Mapping) else None
        trust_refs: list[Path] = []
        if not isinstance(verified, list):
            hard_failures.append("TRUST_SIGNAL_LIST_INVALID")
            continue
        for event in verified:
            if not isinstance(event, Mapping):
                hard_failures.append("TRUST_SIGNAL_EVENT_INVALID")
                continue
            fingerprints = event.get("input_fingerprints")
            if (
                not isinstance(fingerprints, Mapping)
                or any(fingerprints.get(key) != value for key, value in canonical_event_fields.items())
                or not isinstance(fingerprints.get("fixture_bytes"), str)
                or not _SHA256.fullmatch(fingerprints["fixture_bytes"])
            ):
                hard_failures.append("TRUST_SIGNAL_FINGERPRINTS_NOT_BOUND")
            evidence_ref = event.get("evidence_ref")
            evidence_path = _candidate_replay_path(Path(candidate_root), evidence_ref)
            if evidence_path is None:
                hard_failures.append("TRUST_SIGNAL_EVIDENCE_MISSING")
                continue
            trust_refs.append(evidence_path)
            try:
                evidence_value = json.loads(evidence_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                evidence_value = None
            if not isinstance(evidence_value, Mapping) or evidence_value.get("events") != verified:
                hard_failures.append("TRUST_SIGNAL_EVIDENCE_MISMATCH")
        if len(set(trust_refs)) != 1:
            hard_failures.append("TRUST_SIGNAL_EVIDENCE_REFERENCE_INVALID")
    return {
        "status": "passed" if not hard_failures and not unknowns else "failed",
        "hard_failures": sorted(set(hard_failures)),
        "warnings": sorted(set(warnings)),
        "unknowns": sorted(set(unknowns)),
        "reader_hash": _tree_hash(bundle) if bundle.is_dir() else None,
        "audit_hash": _tree_hash(audit) if audit.is_dir() else None,
        "run_id": projection.get("run_id") if isinstance(projection, Mapping) else None,
        "page_count": len(pages) if bundle.is_dir() else 0,
        "claim_count": len(claim_ids) if bundle.is_dir() else 0,
        "replay_material": not any(not path.is_file() for path in replay_files),
    }


def _quality_binding_failures(
    quality: Any,
    snapshot: Mapping[str, Any],
    candidate_root: Path,
    delivery: Mapping[str, Any],
    *,
    expected_mode: str | None = None,
    expected_source_manifest: Mapping[str, Any] | None = None,
) -> list[str]:
    """Prove that the scorecard describes this candidate, not just valid JSON."""

    failures: list[str] = []
    policy = ReaderQualityPolicy()
    quality_status = _quality_field(quality, "status", None)
    if quality_status != "passed":
        failures.append("QUALITY_STATUS_NOT_PASSED")
    quality_summary = _quality_field(quality, "summary", {})
    if not isinstance(quality_summary, Mapping):
        quality_summary = {}
    if expected_mode is not None and quality_summary.get("mode") != expected_mode:
        failures.append("QUALITY_MODE_MISMATCH")
    recomputed_scorecard_hash = _quality_scorecard_hash(quality)
    declared_scorecard_hash = _quality_field(quality, "scorecard_hash", None)
    if recomputed_scorecard_hash is None or declared_scorecard_hash != recomputed_scorecard_hash:
        failures.append("QUALITY_SCORECARD_HASH_MISMATCH")
    provenance = _quality_field(quality, "provenance", {})
    if not isinstance(provenance, Mapping) or provenance.get("snapshot_hash") != _hash(snapshot):
        failures.append("QUALITY_SNAPSHOT_BINDING_INVALID")
    expected_execution_mode = "real_semantic" if expected_mode == "semantic" else "offline_no_llm"
    if not isinstance(provenance, Mapping) or provenance.get("execution_mode") != expected_execution_mode:
        failures.append("QUALITY_EXECUTION_MODE_BINDING_INVALID")
    if not quality_summary:
        failures.append("QUALITY_SUMMARY_MISSING")
    source_manifest_path = Path(candidate_root) / "audit" / "source-manifest.json"
    try:
        manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = None
    if not isinstance(manifest, Mapping) or manifest.get("source_count") != snapshot.get("source_count"):
        failures.append("QUALITY_SOURCE_SNAPSHOT_MISMATCH")
    elif manifest.get("run_id") != delivery.get("run_id"):
        failures.append("QUALITY_SOURCE_RUN_ID_MISMATCH")
    elif snapshot.get("source_manifest_hash") != _source_manifest_hash(manifest):
        failures.append("QUALITY_SOURCE_MANIFEST_HASH_MISMATCH")
    if expected_mode == "semantic":
        if not isinstance(expected_source_manifest, Mapping):
            failures.append("QUALITY_EXPECTED_SOURCE_MANIFEST_MISSING")
        elif not isinstance(manifest, Mapping) or dict(expected_source_manifest) != dict(manifest):
            failures.append("QUALITY_EXPECTED_SOURCE_MANIFEST_MISMATCH")
    if quality_summary.get("source_count") != snapshot.get("source_count"):
        failures.append("QUALITY_SUMMARY_SOURCE_COUNT_MISMATCH")
    try:
        question_set = json.loads(_TASK0_QUESTION_SET_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        question_set = None
    if (
        not isinstance(question_set, Mapping)
        or question_set.get("schema_version") != "task0-question-set.v1"
        or question_set.get("question_set_hash") != _canonical_question_set_hash(question_set)
    ):
        failures.append("QUALITY_QUESTION_SET_SOURCE_INVALID")
        question_set = None
    else:
        if snapshot.get("question_set_hash") != question_set.get("question_set_hash"):
            failures.append("QUALITY_QUESTION_SET_HASH_INVALID")
        if not isinstance(provenance, Mapping) or provenance.get("question_set_hash") != question_set.get("question_set_hash"):
            failures.append("QUALITY_PROVENANCE_QUESTION_SET_INVALID")
    records = _quality_field(quality, "records", ())
    record_list = list(records) if isinstance(records, (list, tuple)) else []
    if len(record_list) != policy.question_count:
        failures.append("QUALITY_QUESTION_COUNT_INVALID")
    expected_question_ids = {
        *(f"positive-{index:02d}" for index in range(1, policy.positive_count + 1)),
        *(f"negative-{index:02d}" for index in range(1, policy.negative_count + 1)),
    }
    expected_question_polarity = {
        **{f"positive-{index:02d}": "positive" for index in range(1, policy.positive_count + 1)},
        **{f"negative-{index:02d}": "negative" for index in range(1, policy.negative_count + 1)},
    }
    actual_question_ids = {record.get("question_id") for record in record_list if isinstance(record, Mapping)}
    if actual_question_ids != expected_question_ids:
        failures.append("QUALITY_QUESTION_ID_SET_INVALID")
    if any(
        isinstance(record, Mapping)
        and expected_question_polarity.get(record.get("question_id")) != record.get("polarity")
        for record in record_list
    ):
        failures.append("QUALITY_QUESTION_POLARITY_BINDING_INVALID")
    actual_positive = [record for record in record_list if isinstance(record, Mapping) and record.get("polarity") == "positive"]
    actual_negative = [record for record in record_list if isinstance(record, Mapping) and record.get("polarity") == "negative"]
    if len(actual_positive) != policy.positive_count or len(actual_negative) != policy.negative_count:
        failures.append("QUALITY_POLARITY_COUNTS_INVALID")
    if any(
        not isinstance(record, Mapping)
        or record.get("answer_result") not in {"hit", "no_match"}
        or record.get("source_recheck_result") not in {"passed", "not_applicable"}
        for record in record_list
    ):
        failures.append("QUALITY_QUESTION_RESULT_INVALID")
    expected_questions = {
        str(item.get("question_id")): item
        for item in (question_set.get("questions", []) if isinstance(question_set, Mapping) and isinstance(question_set.get("questions"), list) else [])
        if isinstance(item, Mapping) and isinstance(item.get("question_id"), str)
    }
    if len(expected_questions) != policy.question_count:
        failures.append("QUALITY_QUESTION_SET_SOURCE_INVALID")
    actual_positive_passed = sum(
        1
        for record in actual_positive
        if record.get("answer_found") is True
        and record.get("answer_result") == "hit"
        and isinstance(record.get("first_hit_page"), str)
        and bool(record.get("first_hit_page"))
        and record.get("answer_complete") is True
        and record.get("boundary_version_accurate") is True
        and record.get("source_attribution") is True
        and record.get("navigation") == "passed"
        and record.get("source_chain") == "passed"
        and record.get("source_recheck_result") == "passed"
        and not record.get("failure_reason")
    )
    actual_negative_false_positives = sum(
        1 for record in actual_negative if record.get("answer_result") == "hit" or record.get("first_hit_page") is not None
    )
    if actual_positive_passed < policy.positive_minimum:
        failures.append("QUALITY_POSITIVE_HIT_THRESHOLD")
    if actual_negative_false_positives > policy.negative_false_positive_maximum:
        failures.append("QUALITY_NEGATIVE_FALSE_POSITIVE")
    if quality_summary.get("positive_count") != len(actual_positive) or quality_summary.get("negative_count") != len(actual_negative):
        failures.append("QUALITY_SUMMARY_POLARITY_COUNTS_MISMATCH")
    if quality_summary.get("positive_passed") != actual_positive_passed or quality_summary.get("negative_false_positives") != actual_negative_false_positives:
        failures.append("QUALITY_SUMMARY_VERDICT_MISMATCH")
    required_string_fields = ("question_id", "polarity", "entry_path", "actor", "model", "rule", "seed", "answer_result", "source_chain", "source_recheck_result")
    for record in record_list:
        if not isinstance(record, Mapping):
            failures.append("QUALITY_QUESTION_FIELDS_INVALID")
            continue
        if any(field not in record for field in ("question_id", "polarity", "entry_path", "first_hit_page", "answer_found", "answer_result", "answer_complete", "boundary_version_accurate", "source_attribution", "navigation", "source_chain", "actor", "model", "rule", "seed", "reader_input_hash", "source_recheck_result", "failure_reason")):
            failures.append("QUALITY_QUESTION_FIELDS_MISSING")
        if any(not isinstance(record.get(field), str) or not str(record[field]).strip() for field in required_string_fields):
            failures.append("QUALITY_QUESTION_FIELDS_INVALID")
        if not isinstance(record.get("answer_complete"), bool) or not isinstance(record.get("boundary_version_accurate"), bool):
            failures.append("QUALITY_QUESTION_FIELDS_INVALID")
        if not isinstance(record.get("answer_found"), bool) or not isinstance(record.get("source_attribution"), bool) or record.get("navigation") != "passed":
            failures.append("QUALITY_QUESTION_FIELDS_INVALID")
        if record.get("first_hit_page") is not None and (not isinstance(record.get("first_hit_page"), str) or not str(record["first_hit_page"]).strip()):
            failures.append("QUALITY_QUESTION_FIELDS_INVALID")
        if record.get("failure_reason") is not None and (not isinstance(record.get("failure_reason"), str) or not str(record["failure_reason"]).strip()):
            failures.append("QUALITY_QUESTION_FIELDS_INVALID")
        if not isinstance(record.get("reader_input_hash"), str) or not _SHA256.fullmatch(record["reader_input_hash"]):
            failures.append("QUALITY_QUESTION_FIELDS_INVALID")
        if expected_mode == "semantic" and not isinstance(record.get("provider_response"), Mapping):
            failures.append("QUALITY_PROVIDER_RESPONSE_MISSING")
        expected_question = expected_questions.get(record.get("question_id"))
        if expected_question is None or any(
            record.get(field) != expected_question.get(expected_field)
            for field, expected_field in (
                ("polarity", "polarity"),
                ("question", "original_text"),
                ("entry_path", "entry_path"),
                ("expected_topic_or_product", "expected_topic_or_product"),
            )
        ):
            failures.append("QUALITY_FIXED_QUESTION_BINDING_INVALID")
    score_seeds: set[str] = set()
    for label, scores in (("title", _quality_field(quality, "title_check", {})), ("ownership", _quality_field(quality, "ownership_check", {}))):
        passed = scores.get("passed") if isinstance(scores, Mapping) else None
        sample_size = scores.get("sample_size") if isinstance(scores, Mapping) else None
        if (
            not isinstance(passed, int)
            or isinstance(passed, bool)
            or not isinstance(sample_size, int)
            or isinstance(sample_size, bool)
            or sample_size <= 0
            or passed < 0
            or passed > sample_size
            or passed / sample_size < getattr(policy, f"{label}_accuracy_minimum")
            or any(not isinstance(scores.get(field), str) or not scores[field].strip() for field in ("actor", "rule", "seed"))
        ):
            failures.append(f"QUALITY_{label.upper()}_SCORE_INVALID")
        elif isinstance(scores, Mapping):
            score_seeds.add(str(scores["seed"]))
    question_seeds = {str(record.get("seed")) for record in record_list if isinstance(record, Mapping) and isinstance(record.get("seed"), str) and record.get("seed").strip()}
    provenance_seed = _quality_field(quality, "provenance", {}).get("seed") if isinstance(_quality_field(quality, "provenance", {}), Mapping) else None
    if len(score_seeds) != 1 or len(question_seeds) != 1 or score_seeds != question_seeds or provenance_seed not in score_seeds:
        failures.append("QUALITY_SCORE_SEED_MISMATCH")
    replay = _quality_field(quality, "replay", {})
    replay_fields = ("manifest_ref", "quality_ref", "config_ref")
    replay_refs = [replay.get(field) for field in replay_fields] if isinstance(replay, Mapping) else []
    if not isinstance(replay, Mapping) or any(_candidate_replay_path(candidate_root, replay.get(field)) is None for field in replay_fields):
        failures.append("QUALITY_REPLAY_REFERENCE_INVALID")
    elif replay.get("execution_mode") != ("real_semantic" if expected_mode == "semantic" else "offline_no_llm"):
        failures.append("QUALITY_REPLAY_MODE_DECLARATION_INVALID")
    elif len(set(replay_refs)) != len(replay_fields):
        failures.append("QUALITY_REPLAY_REFERENCE_DUPLICATED")
    elif (
        not str(replay["manifest_ref"]).startswith("audit/")
        or not str(replay["quality_ref"]).startswith("reports/")
        or not str(replay["config_ref"]).startswith("audit/")
        or PurePosixPath(str(replay["manifest_ref"])).name != "run-manifest.json"
        or PurePosixPath(str(replay["quality_ref"])).name not in {"quality.json", "quality-scorecard.json", "scorecard.json"}
        or PurePosixPath(str(replay["config_ref"])).name != "config.json"
    ):
        failures.append("QUALITY_REPLAY_REFERENCE_ROLE_INVALID")
    elif dict(quality_summary.get("replay") or {}) != dict(replay):
        failures.append("QUALITY_REPLAY_SUMMARY_MISMATCH")
    else:
        replay_values: dict[str, Any] = {}
        for field in ("manifest_ref", "quality_ref", "config_ref"):
            replay_path = _candidate_replay_path(candidate_root, replay[field])
            try:
                replay_values[field] = json.loads(replay_path.read_text(encoding="utf-8")) if replay_path is not None else None
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                replay_values[field] = None
        manifest_value = replay_values.get("manifest_ref")
        quality_value = replay_values.get("quality_ref")
        config_value = replay_values.get("config_ref")
        declared_scorecard_hash = _quality_field(quality, "scorecard_hash", None)
        if not isinstance(manifest_value, Mapping) or manifest_value.get("run_id") != delivery.get("run_id") or manifest_value.get("source_manifest_hash") != snapshot.get("source_manifest_hash"):
            failures.append("QUALITY_REPLAY_MANIFEST_BINDING_INVALID")
        if not isinstance(quality_value, Mapping) or quality_value.get("run_id") != delivery.get("run_id") or quality_value.get("scorecard_hash") != declared_scorecard_hash:
            failures.append("QUALITY_REPLAY_SCORECARD_BINDING_INVALID")
        if not isinstance(quality_value, Mapping) or quality_value.get("mode") != expected_mode:
            failures.append("QUALITY_REPLAY_MODE_BINDING_INVALID")
        if not isinstance(quality_value, Mapping) or quality_value.get("execution_mode") != expected_execution_mode:
            failures.append("QUALITY_REPLAY_EXECUTION_MODE_BINDING_INVALID")
        expected_quality_payload = quality.as_dict() if hasattr(quality, "as_dict") else dict(quality) if isinstance(quality, Mapping) else {}
        if not isinstance(quality_value, Mapping) or any(quality_value.get(field) != expected_quality_payload.get(field) for field in ("schema_version", "status", "hard_failures", "warnings", "unknowns", "records", "summary", "title_check", "ownership_check", "provenance", "replay", "scorecard_hash")):
            failures.append("QUALITY_REPLAY_CONTENT_BINDING_INVALID")
        provider_receipt_ref = quality_value.get("provider_receipt_ref") if isinstance(quality_value, Mapping) else None
        provider_receipt_path = _candidate_replay_path(candidate_root, provider_receipt_ref)
        provider_receipt = None
        if provider_receipt_path is not None:
            try:
                provider_receipt = json.loads(provider_receipt_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                provider_receipt = None
        quality_records_by_id = {
            record.get("question_id"): record
            for record in record_list
            if isinstance(record, Mapping) and isinstance(record.get("question_id"), str)
        }
        provider_receipt_valid = (
            isinstance(quality_value, Mapping)
            and isinstance(quality_value.get("provider_calls"), int)
            and not isinstance(quality_value.get("provider_calls"), bool)
            and quality_value.get("provider_calls") > 0
            and provider_receipt_path is not None
            and isinstance(provider_receipt, Mapping)
            and provider_receipt.get("run_id") == delivery.get("run_id")
            and provider_receipt.get("execution_mode") == "real_semantic"
            and provider_receipt.get("provider_calls") == quality_value.get("provider_calls")
            and provider_receipt.get("provider") == quality_value.get("provider")
            and provider_receipt.get("model") == quality_value.get("model")
            and all(record.get("model") == quality_value.get("model") for record in record_list if isinstance(record, Mapping))
            and isinstance(config_value, Mapping)
            and provider_receipt.get("config_hash") == config_value.get("config_hash")
            and isinstance(provider_receipt.get("calls"), list)
            and len(provider_receipt.get("calls")) == quality_value.get("provider_calls")
            and all(
                isinstance(call, Mapping)
                and call.get("provider") == quality_value.get("provider")
                and call.get("model") == quality_value.get("model")
                and call.get("status") == "completed"
                and isinstance(call.get("question_id"), str)
                and isinstance(call.get("request_hash"), str)
                and _SHA256.fullmatch(call.get("request_hash")) is not None
                and isinstance(call.get("response_hash"), str)
                and _SHA256.fullmatch(call.get("response_hash")) is not None
                and isinstance(call.get("response"), Mapping)
                and call.get("response_hash") == _hash(call.get("response"))
                and call.get("response") == quality_records_by_id.get(call.get("question_id"), {}).get("provider_response")
                for call in provider_receipt.get("calls", [])
            )
            and {call.get("question_id") for call in provider_receipt.get("calls", []) if isinstance(call, Mapping)} == {record.get("question_id") for record in record_list if isinstance(record, Mapping)}
            and all(
                isinstance(call, Mapping)
                and isinstance(quality_records_by_id.get(call.get("question_id")), Mapping)
                and call.get("record_hash") == _hash(quality_records_by_id[call.get("question_id")])
                and call.get("request_hash") == _hash({
                    "question_id": call.get("question_id"),
                    "question": quality_records_by_id[call.get("question_id")].get("question"),
                    "entry_path": quality_records_by_id[call.get("question_id")].get("entry_path"),
                    "expected_topic_or_product": quality_records_by_id[call.get("question_id")].get("expected_topic_or_product"),
                    "provider": quality_value.get("provider"),
                    "model": quality_value.get("model"),
                    "config_hash": config_value.get("config_hash") if isinstance(config_value, Mapping) else None,
                })
                for call in provider_receipt.get("calls", [])
            )
        )
        if not provider_receipt_valid:
            failures.append("QUALITY_PROVIDER_RECEIPT_INVALID")
        if not isinstance(manifest_value, Mapping) or manifest_value.get("execution_mode") != expected_execution_mode:
            failures.append("QUALITY_REPLAY_MANIFEST_MODE_INVALID")
        config_binding_valid = (
            isinstance(config_value, Mapping)
            and config_value.get("run_id") == delivery.get("run_id")
            and config_value.get("snapshot_hash") == _hash(snapshot)
            and config_value.get("execution_mode") == expected_execution_mode
            and config_value.get("llm_enabled") == (expected_execution_mode == "real_semantic")
            and isinstance(config_value.get("model"), str)
            and bool(config_value["model"].strip())
            and isinstance(config_value.get("provider"), str)
            and bool(config_value["provider"].strip())
            and isinstance(quality_value, Mapping)
            and quality_value.get("provider") == config_value.get("provider")
            and quality_value.get("model") == config_value.get("model")
            and config_value.get("config_hash") == snapshot.get("provider_config_hash")
            and isinstance(config_value.get("endpoint"), str)
            and bool(config_value["endpoint"].strip())
            and isinstance(config_value.get("budget"), Mapping)
            and isinstance(config_value.get("budget", {}).get("max_calls"), int)
            and isinstance(quality_value, Mapping)
            and config_value.get("budget", {}).get("max_calls") >= quality_value.get("provider_calls", 0)
        )
        if not config_binding_valid:
            failures.append("QUALITY_REPLAY_CONFIG_BINDING_INVALID")
    for field in ("page_count", "claim_count"):
        if quality_summary.get(field) != delivery.get(field):
            failures.append(f"QUALITY_SUMMARY_{field.upper()}_MISMATCH")
    if not isinstance(records, (list, tuple)) or not records:
        failures.append("QUALITY_RECORDS_MISSING")
    reader_hash = delivery.get("reader_hash")
    if not isinstance(reader_hash, str) or not _SHA256.fullmatch(reader_hash):
        failures.append("QUALITY_READER_HASH_MISSING")
    else:
        for record in records if isinstance(records, (list, tuple)) else ():
            if not isinstance(record, Mapping) or record.get("reader_input_hash") != reader_hash:
                failures.append("QUALITY_READER_HASH_MISMATCH")
                break
    if isinstance(snapshot.get("reader_hash"), str) and snapshot.get("reader_hash") != reader_hash:
        failures.append("SNAPSHOT_READER_HASH_MISMATCH")
    return sorted(set(failures))


def prepare_full_release(evidence: FullReleaseEvidence) -> PreparedFullRelease:
    delivery = validate_delivery_hard_gates(
        evidence.candidate_root,
        expected_run_id=evidence.run_id,
        expected_source_manifest=evidence.expected_source_manifest,
    ) if evidence.candidate_root is not None else {
        "status": "failed",
        "hard_failures": ["CANDIDATE_ROOT_MISSING"],
        "warnings": [],
        "unknowns": [],
        "reader_hash": None,
        "audit_hash": None,
        "run_id": None,
        "replay_material": False,
    }
    candidate = Path(evidence.candidate_root) if evidence.candidate_root is not None else None
    if candidate is not None and candidate.is_dir():
        delivery["hard_failures"] = sorted(set(list(delivery.get("hard_failures", ())) + _quality_binding_failures(evidence.quality, evidence.snapshot, candidate, delivery, expected_mode=evidence.mode, expected_source_manifest=evidence.expected_source_manifest)))
    if not isinstance(evidence.comparison, Mapping):
        delivery["hard_failures"] = sorted(set(list(delivery.get("hard_failures", ())) + ["COMPARISON_MISSING"]))
    elif evidence.comparison.get("release_decision") != "not_a_release_decision":
        delivery["hard_failures"] = sorted(set(list(delivery.get("hard_failures", ())) + ["COMPARISON_BOUNDARY_INVALID"]))
    elif candidate is not None:
        binding = evidence.comparison.get("binding")
        expected_bundle_hash = _tree_hash(candidate / "bundle") if (candidate / "bundle").is_dir() else None
        dimensions = evidence.comparison.get("dimensions")
        sources = evidence.comparison.get("sources")
        comparison_shape_valid = (
            evidence.comparison.get("schema_version") == "kd-task3-comparison.v1"
            and isinstance(sources, Mapping)
            and set(sources) == {"task2", "companybrain", "task3"}
            and all(
                isinstance(sources[name], Mapping)
                and isinstance(sources[name].get("saved_integrity"), Mapping)
                and sources[name]["saved_integrity"].get("status") in {"comparable", "N/A"}
                and isinstance(sources[name]["saved_integrity"].get("basis"), str)
                and bool(sources[name]["saved_integrity"]["basis"].strip())
                for name in ("task2", "companybrain", "task3")
            )
            and isinstance(sources.get("task3"), Mapping)
            and isinstance(sources["task3"].get("binding"), Mapping)
            and sources["task3"]["binding"].get("run_id") == evidence.run_id
            and sources["task3"]["binding"].get("bundle_hash") == (_tree_hash(candidate / "bundle") if candidate is not None and (candidate / "bundle").is_dir() else None)
            and isinstance(sources["task3"].get("claim_count"), int)
            and sources["task3"].get("claim_count") > 0
            and all(
                isinstance(sources["task3"].get(dimension), Mapping)
                and sources["task3"][dimension].get("status") == "comparable"
                for dimension in ("saved_integrity", "machine_quality", "reader_readability", "trust_freshness", "failures")
            )
            and isinstance(dimensions, Mapping)
            and set(dimensions) == set(_COMPARISON_DIMENSIONS)
            and all(
                isinstance(dimensions.get(dimension), Mapping)
                and set(dimensions[dimension]) == {"task2", "companybrain", "task3"}
                and all(
                    isinstance(dimensions[dimension].get(name), Mapping)
                    and dimensions[dimension][name].get("comparability") in {"comparable", "N/A"}
                    and isinstance(dimensions[dimension][name].get("basis"), str)
                    and bool(dimensions[dimension][name]["basis"].strip())
                    for name in ("task2", "companybrain", "task3")
                )
                for dimension in _COMPARISON_DIMENSIONS
            )
        )
        if not comparison_shape_valid:
            delivery["hard_failures"] = sorted(set(list(delivery.get("hard_failures", ())) + ["COMPARISON_SHAPE_INVALID"]))
        if not isinstance(binding, Mapping) or binding.get("run_id") != evidence.run_id or binding.get("bundle_hash") != expected_bundle_hash:
            delivery["hard_failures"] = sorted(set(list(delivery.get("hard_failures", ())) + ["COMPARISON_BINDING_INVALID"]))
    formal = Path(evidence.formal_root) if evidence.formal_root is not None else None
    formal_state = inspect_formal_root(formal)
    actual_old_package_protected = bool(formal_state["protected"])
    delivery["formal_root_state"] = formal_state["status"]
    delivery["formal_root_tree_hash"] = formal_state["tree_hash"]
    if formal_state["status"] == "missing":
        delivery["hard_failures"] = sorted(set(list(delivery.get("hard_failures", ())) + ["FORMAL_ROOT_REQUIRED"]))
    elif not actual_old_package_protected:
        delivery["hard_failures"] = sorted(set(list(delivery.get("hard_failures", ())) + ["OLD_PACKAGE_NOT_PROTECTED"]))
    summary = build_release_summary(
        run_id=evidence.run_id,
        quality=evidence.quality,
        delivery=delivery,
        mode=evidence.mode,
        old_package_protected=actual_old_package_protected,
    )
    summary_path = candidate / "reports" / "release-summary.json" if candidate is not None and candidate.is_dir() else None
    summary_file_hash = write_release_summary(summary, summary_path) if summary_path is not None else None
    return PreparedFullRelease(
        status="not_released",
        summary=summary,
        summary_sha256=str(summary["summary_sha256"]),
        hard_failures=tuple(summary["hard_failures"]),
        warnings=tuple(summary["warnings"]),
        unknowns=tuple(summary["unknowns"]),
        candidate_tree_hash=_tree_hash(evidence.candidate_root) if evidence.candidate_root is not None and evidence.candidate_root.is_dir() else None,
        summary_path=summary_path,
        summary_file_sha256=summary_file_hash,
    )


def release_with_confirmation(prepared: PreparedFullRelease, confirmation: SummaryConfirmation | Mapping[str, Any] | None) -> str:
    return release_decision(prepared.summary, confirmation, summary_path=prepared.summary_path)


def _validate_release_status_projection(root: Path, *, status: str, require_release_artifacts: bool = False) -> None:
    reports = root / "reports"
    values: dict[str, Mapping[str, Any]] = {}
    for name in ("projection-report.json", "exit-manifest.json"):
        path = reports / name
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError("task3-release", path, "release status projection is unreadable") from exc
        if not isinstance(value, Mapping) or value.get("digest_release_status") != status:
            raise ValidationError("task3-release", path, "release status projection is inconsistent")
        values[name] = value
    if values["projection-report.json"].get("run_id") != values["exit-manifest.json"].get("run_id"):
        raise ValidationError("task3-release", reports, "release status projections use different runs")
    exit_bundle_hash = values["exit-manifest.json"].get("bundle_hash")
    if exit_bundle_hash != _tree_hash(root / "bundle"):
        raise ValidationError("task3-release", reports / "exit-manifest.json", "release bundle hash readback mismatch")
    summary_path = reports / "release-summary.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not isinstance(summary, Mapping) or summary.get("digest_release_status") != status:
            raise ValidationError("task3-release", summary_path, "release summary status is inconsistent")
    for relative, marker in (("bundle/log.md", f"digest_release_status: `{status}`"), ("bundle/README.md", f"digest_release_status: `{status}`")):
        path = root / relative
        if not path.is_file() or path.read_text(encoding="utf-8").count(marker) != 1:
            raise ValidationError("task3-release", path, "human-readable status projection is inconsistent")
    if require_release_artifacts:
        for name in ("release-manifest.json", "release-receipt.json"):
            path = reports / name
            value = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
            if not isinstance(value, Mapping) or value.get("digest_release_status") != status:
                raise ValidationError("task3-release", path, "release receipt projection is inconsistent")


def _set_release_status(root: Path, *, status: str, prepared: PreparedFullRelease, confirmation: SummaryConfirmation | Mapping[str, Any]) -> str:
    """Update every package status projection from one final package fact."""

    if status != "released":
        raise ValidationError("task3-release", root, "unsupported final package status")
    reports = root / "reports"
    for name in ("projection-report.json", "exit-manifest.json"):
        path = reports / name
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError("task3-release", path, "release status projection is unreadable") from exc
        if not isinstance(value, dict):
            raise ValidationError("task3-release", path, "release status projection must be an object")
        value["digest_release_status"] = status
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = reports / "release-summary.json"
    final_summary_hash: str | None = None
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError("task3-release", summary_path, "release summary is unreadable") from exc
        if not isinstance(summary, dict):
            raise ValidationError("task3-release", summary_path, "release summary must be an object")
        summary["digest_release_status"] = status
        summary["summary_sha256"] = summary_sha256(summary)
        final_summary_hash = str(summary["summary_sha256"])
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log_path = root / "bundle" / "log.md"
    readme_path = root / "bundle" / "README.md"
    for path in (log_path, readme_path):
        if not path.is_file():
            raise ValidationError("task3-release", path, "human-readable status projection is missing")
        text = path.read_text(encoding="utf-8")
        old_marker = "digest_release_status: `not_released`"
        if text.count(old_marker) != 1:
            raise ValidationError("task3-release", path, "human-readable status projection has no unique candidate marker")
        path.write_text(text.replace(old_marker, "digest_release_status: `released`"), encoding="utf-8")
    exit_path = reports / "exit-manifest.json"
    exit_value = json.loads(exit_path.read_text(encoding="utf-8"))
    if not isinstance(exit_value, dict):
        raise ValidationError("task3-release", exit_path, "exit manifest must be an object")
    exit_value["bundle_hash"] = _tree_hash(root / "bundle")
    exit_path.write_text(json.dumps(exit_value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    confirmation_values = confirmation.__dict__ if isinstance(confirmation, SummaryConfirmation) else dict(confirmation)
    if final_summary_hash is None:
        raise ValidationError("task3-release", summary_path, "release summary is missing")
    (reports / "release-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "task3-release-manifest.v1",
                "run_id": prepared.summary["run_id"],
                "digest_release_status": status,
                "confirmed_summary_sha256": confirmation_values.get("summary_sha256"),
                "final_summary_sha256": final_summary_hash,
                "confirmed_summary_file_sha256": prepared.summary_file_sha256,
                "final_summary_file_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                "confirmation": {"actor": confirmation_values.get("actor"), "confirmed_at": confirmation_values.get("confirmed_at")},
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return final_summary_hash


def atomic_release(
    prepared: PreparedFullRelease,
    confirmation: SummaryConfirmation | Mapping[str, Any] | None,
    *,
    candidate_root: Path,
    formal_root: Path,
    lock_root: Path | None = None,
    replace_fn: Any = None,
) -> str:
    """Copy one candidate root and swap it under one lock-protected root."""

    if release_decision(prepared.summary, confirmation, summary_path=prepared.summary_path) != "released":
        return "not_released"
    candidate = Path(candidate_root)
    formal = Path(formal_root)
    if (
        prepared.candidate_tree_hash is None
        or not candidate.is_dir()
        or candidate.is_symlink()
        or formal == candidate
        or candidate.resolve() == formal.resolve()
    ):
        return "not_released"
    if _has_unsupported_nodes(candidate) or _tree_hash(candidate) != prepared.candidate_tree_hash:
        return "not_released"
    parent = formal.parent
    parent.mkdir(parents=True, exist_ok=True)
    replacer = replace_fn or os.replace
    stage = parent / f".task3-release-{uuid.uuid4().hex}"
    rollback = parent / f".task3-rollback-{uuid.uuid4().hex}"
    lock_dir = Path(lock_root) if lock_root is not None else parent
    try:
        with kb_lock(lock_dir):
            formal_state = inspect_formal_root(formal)
            expected_formal_state = prepared.summary.get("delivery", {}).get("formal_root_state")
            expected_formal_hash = prepared.summary.get("delivery", {}).get("formal_root_tree_hash")
            if (
                not formal_state["protected"]
                or formal_state["status"] != expected_formal_state
                or formal_state["tree_hash"] != expected_formal_hash
            ):
                return "not_released"
            # The pre-lock check only rejects an obviously stale candidate. A
            # cooperating writer can still change it while we wait for the
            # lock, so bind the actual copy to the same hash inside the lock.
            if _tree_hash(candidate) != prepared.candidate_tree_hash:
                return "not_released"
            if candidate.is_symlink() or any(path.is_symlink() for path in candidate.rglob("*")) or _has_unsupported_nodes(candidate):
                return "not_released"
            # Preserve links during the copy so a late path swap cannot make
            # the release reader follow a link outside the candidate root.
            shutil.copytree(candidate, stage, symlinks=True)
            if any(path.is_symlink() for path in stage.rglob("*")) or _tree_hash(stage) != prepared.candidate_tree_hash:
                raise ValidationError("task3-release", stage, "candidate changed during locked copy")
            reports = stage / "reports"
            reports.mkdir(parents=True, exist_ok=True)
            if prepared.summary_path is not None:
                staged_summary = reports / prepared.summary_path.name
                if not staged_summary.is_file() or hashlib.sha256(staged_summary.read_bytes()).hexdigest() != prepared.summary_file_sha256:
                    raise ValidationError("task3-release", staged_summary, "summary file changed after confirmation")
            final_summary_hash = _set_release_status(stage, status="released", prepared=prepared, confirmation=confirmation)
            confirmation_values = confirmation.__dict__ if isinstance(confirmation, SummaryConfirmation) else dict(confirmation)
            receipt = {
                "schema_version": "task3-release-receipt.v1",
                "run_id": prepared.summary["run_id"],
                "digest_release_status": "released",
                "confirmed_summary_sha256": confirmation_values.get("summary_sha256"),
                "summary_sha256": final_summary_hash,
                "confirmed_summary_file_sha256": prepared.summary_file_sha256,
                "final_summary_file_sha256": hashlib.sha256((stage / "reports" / "release-summary.json").read_bytes()).hexdigest(),
                "confirmation": {
                    "actor": confirmation.actor if isinstance(confirmation, SummaryConfirmation) else confirmation.get("actor"),
                    "confirmed_at": confirmation.confirmed_at if isinstance(confirmation, SummaryConfirmation) else confirmation.get("confirmed_at"),
                },
            }
            (reports / "release-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            _validate_release_status_projection(stage, status="released", require_release_artifacts=True)
            staged_formal_hash = _tree_hash(stage)
            old_hash = formal_state["tree_hash"]
            moved_old = False
            installed_new = False
            restored = False
            try:
                if formal.exists() or formal.is_symlink():
                    replacer(formal, rollback)
                    moved_old = True
                replacer(stage, formal)
                installed_new = True
                if not formal.is_dir() or formal.is_symlink() or _tree_hash(formal) != staged_formal_hash:
                    raise ValidationError("task3-release", formal, "formal root readback does not match staged release")
                _validate_release_status_projection(formal, status="released", require_release_artifacts=True)
            except Exception as install_error:
                if installed_new and (formal.exists() or formal.is_symlink()):
                    if formal.is_dir() and not formal.is_symlink():
                        shutil.rmtree(formal)
                    else:
                        formal.unlink()
                if moved_old and (rollback.exists() or rollback.is_symlink()):
                    try:
                        replacer(rollback, formal)
                        restored = bool(formal.is_dir() and not formal.is_symlink() and (old_hash is None or _tree_hash(formal) == old_hash))
                    except Exception:
                        # Keep the only old package backup in place.  The
                        # caller receives not_released and a recoverable
                        # rollback directory instead of silent data loss.
                        restored = False
                if not restored and moved_old and (rollback.exists() or rollback.is_symlink()):
                    failure_path = parent / f".task3-release-failure-{uuid.uuid4().hex}.json"
                    failure_path.write_text(
                        json.dumps(
                            {
                                "schema_version": "task3-release-failure.v1",
                                "status": "not_released",
                                "reason": "rollback_failed",
                                "rollback_path": rollback.name,
                                "old_package_hash": old_hash,
                                "install_error": str(install_error),
                                "recovery": "restore rollback_path to formal_root after stopping writers",
                            },
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                raise
            finally:
                if restored and (rollback.exists() or rollback.is_symlink()):
                    if rollback.is_dir() and not rollback.is_symlink():
                        shutil.rmtree(rollback)
                    else:
                        rollback.unlink()
                if stage.exists():
                    shutil.rmtree(stage)
        return "released"
    except (OSError, ValidationError):
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        return "not_released"
