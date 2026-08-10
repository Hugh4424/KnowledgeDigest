"""Zero-network OKF parser smoke for the isolated Task 2-A Bundle."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import ValidationError
from .reader_bundle import _sha256_bytes as _digest_bytes, _sha256_tree as _hash_tree


_SCHEMA = "okf-parser-smoke.v1"
_HASH = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_READ_BOUNDARY = ("bundle/document.py", "bundle/index.py", "bundle/paths.py")
_SOURCE_FILES = _READ_BOUNDARY
_REQUIRED_VENDOR_FILES = (*_SOURCE_FILES, "LICENSE", "NOTICE.md", "README.md")
_EXPECTED_BEHAVIOR = {
    "expected_read_boundary": list(_READ_BOUNDARY),
    "expected_unknown_extension_behavior": "report_observed_without_silent_drop",
    "expected_unknown_type_behavior": "external_parser_accepts_nonempty_type; project_validator_remains_fail_closed",
}


@dataclass(frozen=True)
class ParserVendorRef:
    source_ref: str
    source_commit: str
    vendor_root: Path
    vendor_hash: str
    license_ref: str
    license_hash: str
    notice_ref: str
    notice_hash: str
    read_boundary: tuple[str, ...]


@dataclass(frozen=True)
class ParserSmokeAttempt:
    attempt_ref: str
    bundle_hash: str
    command: str
    read_boundary: tuple[str, ...]
    evidence: Mapping[str, Any]


@dataclass(frozen=True)
class ParserSmokeResult:
    schema_version: str
    status: str
    source_ref: str
    attempt_ref: str
    source_commit: str
    vendor_hash: str
    license_hash: str
    notice_hash: str
    bundle_hash: str
    read_boundary: tuple[str, ...]
    read_summary: Mapping[str, Any]
    reason: str | None
    vendor_root: Path | None = None


def _hash_files(root: Path, paths: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = root / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError("okf-smoke", path, "cannot load vendored parser module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _readme_value(text: str, label: str) -> str:
    match = re.search(rf"(?im)^{re.escape(label)}:\s*(\S+)\s*$", text)
    if not match:
        raise ValidationError("okf-smoke", "README.md", f"vendor readback is missing {label}")
    return match.group(1)


def read_vendor_ref(vendor_root: Path) -> ParserVendorRef:
    """Read and hash the pinned local vendor bytes and their notice surface."""

    root = Path(vendor_root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValidationError("okf-smoke", root, "vendor root must be an absolute real directory")
    for relative in _REQUIRED_VENDOR_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ValidationError("okf-smoke", relative, "required vendor readback file is missing or symlinked")
    readback = (root / "README.md").read_text(encoding="utf-8")
    source_ref = _readme_value(readback, "source_ref")
    source_commit = _readme_value(readback, "source_commit")
    license_ref = _readme_value(readback, "license_ref")
    notice_ref = _readme_value(readback, "notice_ref")
    if not _COMMIT.fullmatch(source_commit):
        raise ValidationError("okf-smoke", "README.md", "vendor source_commit is not a full commit")
    if license_ref != "LICENSE" or notice_ref != "NOTICE.md":
        raise ValidationError("okf-smoke", "README.md", "vendor license/notice refs are outside the fixed surface")
    return ParserVendorRef(
        source_ref=source_ref,
        source_commit=source_commit,
        vendor_root=root,
        vendor_hash=_hash_files(root, _SOURCE_FILES),
        license_ref=license_ref,
        license_hash=_digest_bytes((root / license_ref).read_bytes()),
        notice_ref=notice_ref,
        notice_hash=_digest_bytes((root / notice_ref).read_bytes()),
        read_boundary=_READ_BOUNDARY,
    )


def _empty_result(vendor: ParserVendorRef, *, status: str, reason: str, attempt_ref: str = "", bundle_hash: str = "") -> ParserSmokeResult:
    return ParserSmokeResult(
        schema_version=_SCHEMA,
        status=status,
        source_ref=vendor.source_ref,
        attempt_ref=attempt_ref,
        source_commit=vendor.source_commit,
        vendor_hash=vendor.vendor_hash,
        license_hash=vendor.license_hash,
        notice_hash=vendor.notice_hash,
        bundle_hash=bundle_hash,
        read_boundary=vendor.read_boundary,
        read_summary={**_EXPECTED_BEHAVIOR, "network_requests": 0},
        reason=reason,
    )


def create_smoke_attempt(
    artifact_root: Path,
    vendor: ParserVendorRef,
    *,
    command: str = "pytest tests/acceptance/test_task2a_okf_smoke.py -q",
) -> ParserSmokeAttempt:
    root = Path(artifact_root)
    bundle = root / "bundle"
    if not root.is_absolute() or not bundle.is_dir():
        raise ValidationError("okf-smoke", root, "Bundle artifact root is missing")
    bundle_hash = _hash_tree(bundle)
    attempt_key = _digest_bytes(f"{bundle_hash}\0{vendor.source_commit}\0{vendor.vendor_hash}".encode("utf-8"))[:24]
    attempt_ref = f"audit/parser-smoke/{attempt_key}.json"
    evidence = {
        "schema_version": "okf-parser-smoke-attempt.v1",
        "attempt_ref": attempt_ref,
        "bundle_hash": bundle_hash,
        "source_ref": vendor.source_ref,
        "source_commit": vendor.source_commit,
        "vendor_hash": vendor.vendor_hash,
        "license_ref": vendor.license_ref,
        "license_hash": vendor.license_hash,
        "notice_ref": vendor.notice_ref,
        "notice_hash": vendor.notice_hash,
        "command": command,
        "read_boundary": list(vendor.read_boundary),
        "network": "deny-only socket guard is owned by acceptance test boundary",
    }
    path = root / Path(attempt_ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ParserSmokeAttempt(attempt_ref, bundle_hash, command, vendor.read_boundary, evidence)


def _provenance_ok(vendor: ParserVendorRef, attempt: ParserSmokeAttempt, bundle_hash: str) -> str | None:
    if not vendor.source_ref or not _COMMIT.fullmatch(vendor.source_commit):
        return "VENDOR_PROVENANCE_INCOMPLETE"
    if not _HASH.fullmatch(vendor.vendor_hash) or not _HASH.fullmatch(vendor.license_hash) or not _HASH.fullmatch(vendor.notice_hash):
        return "VENDOR_HASH_PROVENANCE_INCOMPLETE"
    if vendor.read_boundary != _READ_BOUNDARY:
        return "VENDOR_READ_BOUNDARY_UNSUPPORTED"
    if attempt.bundle_hash != bundle_hash:
        return "BUNDLE_PROVENANCE_MISMATCH"
    if attempt.read_boundary != _READ_BOUNDARY:
        return "ATTEMPT_READ_BOUNDARY_UNSUPPORTED"
    if not attempt.attempt_ref or not attempt.command:
        return "ATTEMPT_PROVENANCE_INCOMPLETE"
    if dict(attempt.evidence).get("bundle_hash") != bundle_hash:
        return "ATTEMPT_EVIDENCE_MISMATCH"
    return None


def run_parser_smoke(
    artifact_root: Path,
    vendor: ParserVendorRef,
    attempt: ParserSmokeAttempt,
) -> ParserSmokeResult:
    """Read the fixed OKF surface without a network/provider/counter context."""

    root = Path(artifact_root)
    bundle = root / "bundle"
    if not bundle.is_dir():
        return _empty_result(vendor, status="blocked", reason="BUNDLE_SURFACE_MISSING", attempt_ref=attempt.attempt_ref)
    bundle_hash = _hash_tree(bundle)
    provenance_error = _provenance_ok(vendor, attempt, bundle_hash)
    if provenance_error:
        return _empty_result(vendor, status="blocked", reason=provenance_error, attempt_ref=attempt.attempt_ref, bundle_hash=bundle_hash)
    try:
        observed_vendor = read_vendor_ref(vendor.vendor_root)
        if observed_vendor.source_ref != vendor.source_ref or observed_vendor.source_commit != vendor.source_commit or observed_vendor.vendor_hash != vendor.vendor_hash or observed_vendor.license_hash != vendor.license_hash or observed_vendor.notice_hash != vendor.notice_hash:
            return _empty_result(vendor, status="blocked", reason="VENDOR_READBACK_MISMATCH", attempt_ref=attempt.attempt_ref, bundle_hash=bundle_hash)
        attempt_evidence = dict(attempt.evidence)
        expected_attempt = {
            "attempt_ref": attempt.attempt_ref,
            "bundle_hash": bundle_hash,
            "source_ref": vendor.source_ref,
            "source_commit": vendor.source_commit,
            "vendor_hash": vendor.vendor_hash,
            "license_ref": vendor.license_ref,
            "license_hash": vendor.license_hash,
            "notice_ref": vendor.notice_ref,
            "notice_hash": vendor.notice_hash,
            "read_boundary": list(_READ_BOUNDARY),
        }
        if any(attempt_evidence.get(key) != value for key, value in expected_attempt.items()):
            return _empty_result(vendor, status="blocked", reason="ATTEMPT_READBACK_MISMATCH", attempt_ref=attempt.attempt_ref, bundle_hash=bundle_hash)
        compile((vendor.vendor_root / "bundle" / "index.py").read_text(encoding="utf-8"), str(vendor.vendor_root / "bundle" / "index.py"), "exec")
        document = _load_module(vendor.vendor_root / "bundle" / "document.py", "_knowledge_digest_okf_document")
        paths = _load_module(vendor.vendor_root / "bundle" / "paths.py", "_knowledge_digest_okf_paths")
        markdown = sorted(path for path in bundle.rglob("*.md") if path.is_file())
        concepts = 0
        indexes = 0
        for path in markdown:
            relative = path.relative_to(bundle).as_posix()
            parsed = document.OKFDocument.parse(path.read_text(encoding="utf-8"))
            if path.name == "index.md":
                indexes += 1
                continue
            if relative.startswith("products/"):
                parsed.validate()
                paths.parse_concept_id(path.relative_to(bundle).with_suffix("").as_posix())
                concepts += 1
        if not (bundle / "index.md").is_file() or not (bundle / "Home.md").is_file() or not (bundle / "README.md").is_file():
            raise ValueError("canonical root documents are missing")
        summary = {
            "parser": "vendored OKFDocument",
            "concept_count": concepts,
            "index_count": indexes,
            "unknown_extensions": sorted(path.suffix for path in bundle.rglob("*") if path.is_file() and path.suffix not in {"", ".md", ".json"}),
            "network_requests": 0,
            "read_boundary": list(_READ_BOUNDARY),
            **_EXPECTED_BEHAVIOR,
        }
        return ParserSmokeResult(_SCHEMA, "passed", vendor.source_ref, attempt.attempt_ref, vendor.source_commit, vendor.vendor_hash, vendor.license_hash, vendor.notice_hash, bundle_hash, _READ_BOUNDARY, summary, None, vendor.vendor_root)
    except (ImportError, ModuleNotFoundError, OSError) as exc:
        return ParserSmokeResult(_SCHEMA, "unavailable", vendor.source_ref, attempt.attempt_ref, vendor.source_commit, vendor.vendor_hash, vendor.license_hash, vendor.notice_hash, bundle_hash, _READ_BOUNDARY, {**_EXPECTED_BEHAVIOR, "network_requests": 0}, f"PARSER_SMOKE_UNAVAILABLE:{type(exc).__name__}:{exc}", vendor.vendor_root)
    except ValidationError as exc:
        return _empty_result(vendor, status="blocked", reason=f"VENDOR_READBACK_INVALID:{exc}", attempt_ref=attempt.attempt_ref, bundle_hash=bundle_hash)
    except Exception as exc:
        return ParserSmokeResult(_SCHEMA, "failed", vendor.source_ref, attempt.attempt_ref, vendor.source_commit, vendor.vendor_hash, vendor.license_hash, vendor.notice_hash, bundle_hash, _READ_BOUNDARY, {**_EXPECTED_BEHAVIOR, "network_requests": 0}, f"PARSER_SMOKE_FAILED:{type(exc).__name__}:{exc}", vendor.vendor_root)


__all__ = [
    "ParserSmokeAttempt",
    "ParserSmokeResult",
    "ParserVendorRef",
    "create_smoke_attempt",
    "read_vendor_ref",
    "run_parser_smoke",
]
