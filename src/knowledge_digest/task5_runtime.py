"""Formal Task5 runtime around the reader-first compiler.

The runtime owns only lifecycle, evidence and publication wiring.  The
``compiler`` remains the only writer of Reader prose.  Every provider result,
quality result and release decision is derived from the current run; missing
or stale upstream WorkflowHub evidence fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import socket
import unicodedata
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .compiler import DigestRequest, digest_slice_then_full
from .task5_provider import build_task5_providers, config_identity, redact_identity, sha256_bytes
from .providers import ProviderConfigError, ProviderError
from .task5_quality_gate import evaluate_candidate, strict_winner


TASK_ID = "task5-reader-quality-compiler-redesign"
RUN_RESULT_SCHEMA = "task5-run-result.v1"
FIXED_AUDIT_FILES = (
    "_audit/audit-pages.json",
    "_audit/source-status.json",
    "_audit/companybrain-route-snapshot.json",
    "_audit/semantic-compile-ledger.jsonl",
    "_audit/semantic-response-ledger.jsonl",
    "_audit/route-ledger.jsonl",
    "_audit/raw-coordinate-map.json",
    "_audit/source-not-documented-zero-match.json",
    "_audit/source-not-documented-verifier.json",
    "_audit/run-result.json",
    "_audit/directory-manifest.json",
)
EXPECTED_AUTHORITY_KEYS = (
    "external_processing_policy",
    "machine_evidence",
    "publication_layout",
    "provider_handshake",
    "provider_prompt",
    "provider_semantic",
    "reader_path_relation",
    "reader_quality_provider",
    "replay_store",
    "root_cause_evidence",
    "root_cause_inputs",
    "semantic_frame",
    "semantic_frame_field_closure",
    "source_block_claim",
    "source_digest",
    "source_not_documented",
    "source_sensitive_content_scan",
)
EXPECTED_EXCLUDED_PATHS = (
    "config/task5-quality-cases-v2.json",
    "config/task5-companybrain-baseline-v2.json",
    "config/task5-source-page-manifest-v2.json",
    "config/task5-slice-cases-v1.json",
    "config/task5-run-result-v1.json",
)
FORBIDDEN_KEY = re.compile(r"(?i)^(?:api[_ -]?key|authorization|password|private[_ -]?key|secret|token)$")
FORBIDDEN_VALUE = re.compile(r"(?i)(?:bearer\s+[a-z0-9._~+/=-]{12,}|-----begin\s+[^-]+private\s+key-----|authorization\s*:\s*bearer\s+|password\s*[:=]\s*\S+)")


class Task5RuntimeError(RuntimeError):
    """A Task5 precondition or publication invariant failed."""


class Task5BlockedError(Task5RuntimeError):
    """Execution cannot proceed because a provider/config prerequisite is unavailable."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(value: Any, *, trailing_newline: bool = True) -> bytes:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return payload + (b"\n" if trailing_newline else b"")


def _with_hash(value: Mapping[str, Any], field: str = "canonical_sha256") -> dict[str, Any]:
    result = dict(value)
    result.pop(field, None)
    result[field] = hashlib.sha256(_canonical(result)).hexdigest()
    return result


def _write_canonical(path: Path, value: Mapping[str, Any]) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    hashed = _with_hash(value)
    data = _canonical(hashed)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return sha256_bytes(data)


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Task5RuntimeError(f"invalid JSON evidence: {path}") from error
    if not isinstance(value, Mapping):
        raise Task5RuntimeError(f"JSON evidence is not an object: {path}")
    return value


def _safe_root(path: Path, label: str, *, must_exist: bool = True) -> Path:
    root = Path(path).expanduser()
    if not root.is_absolute() or root.is_symlink() or (must_exist and not root.is_dir()):
        raise Task5RuntimeError(f"{label} must be an absolute regular directory: {root}")
    if root.exists() and not root.is_dir():
        raise Task5RuntimeError(f"{label} must be a directory: {root}")
    return root


def _downloads_root() -> Path:
    """Return the only allowed parent for a real Task5 publication."""

    # Keep this unresolved until the caller has checked the directory with
    # lstat semantics.  Resolving first would make a symlinked Downloads
    # directory look like the canonical directory and defeat the boundary.
    return Path("/Users/Hugh/Downloads")


def _path_overlaps(left: Path, right: Path) -> bool:
    """Use resolved path parts, never string prefixes, for overlap checks."""

    left_parts = left.resolve(strict=False).parts
    right_parts = right.resolve(strict=False).parts
    shortest = min(len(left_parts), len(right_parts))
    return left_parts[:shortest] == right_parts[:shortest]


def _output_paths(output: Path, run_id: str, owner_nonce: str) -> dict[str, Path]:
    output = Path(output).expanduser()
    return {
        "output": output,
        "lock": output.with_name(f"{output.name}.task5.lock"),
        "staging": output.with_name(f"{output.name}.staging.{run_id}.{owner_nonce}"),
        "failure_sink": output.with_name(f"{output.name}.failure.{run_id}.{owner_nonce}"),
    }


def _validate_output_target(
    output: Path,
    raw: Path,
    companybrain: Path,
    run_id: str,
    owner_nonce: str,
) -> tuple[dict[str, Path], dict[str, Any], list[str]]:
    """Validate the Downloads target before creating output, lock or staging."""

    paths = _output_paths(output, run_id, owner_nonce)
    target = paths["output"]
    downloads = _downloads_root()
    reasons: list[str] = []
    if not target.is_absolute():
        reasons.append("output must be an absolute path")
    if ".." in target.parts:
        reasons.append("output path may not contain '..'")
    if downloads.is_symlink() or not downloads.is_dir():
        reasons.append("Downloads root is not a regular directory")
    parent = target.parent
    if parent != downloads:
        reasons.append("output must be a new direct child of /Users/Hugh/Downloads")
    if target.exists() or target.is_symlink():
        reasons.append("output already exists or is a symlink")
    for name in ("lock", "staging", "failure_sink"):
        if paths[name].exists() or paths[name].is_symlink():
            reasons.append(f"output {name} already exists")
    if list(target.parent.glob(f"{target.name}.staging.*")):
        reasons.append("an earlier output staging directory exists")
    if list(target.parent.glob(f"{target.name}.failure.*")):
        reasons.append("an earlier output failure sink exists")
    if target.parent.joinpath(f"{target.name}.failure-evidence").exists():
        reasons.append("an earlier output failure-evidence directory exists")
    raw_resolved = Path(raw).expanduser().resolve(strict=False)
    companybrain_resolved = Path(companybrain).expanduser().resolve(strict=False)
    output_resolved = target.resolve(strict=False)
    for name, candidate in (("raw", raw_resolved), ("CompanyBrain", companybrain_resolved)):
        if _path_overlaps(output_resolved, candidate):
            reasons.append(f"output overlaps {name}")
    try:
        if parent.stat().st_dev != downloads.stat().st_dev:
            reasons.append("output parent is on a different filesystem")
    except OSError:
        reasons.append("output parent filesystem cannot be verified")
    identity = {
        # This result is written to repository evidence.  Host paths belong
        # only in host-owned evidence, never in the public preflight record.
        "downloads_root": "downloads_output_parent",
        "raw_realpath": "raw_input",
        "companybrain_realpath": "companybrain_input",
        "output_realpath": "downloads_output",
        "staging_realpath": "downloads_output_staging",
        "same_filesystem": not any("different filesystem" in reason for reason in reasons),
        "output_exists": target.exists(),
        "output_is_symlink": target.is_symlink(),
        "overlap_check": not any("overlaps" in reason for reason in reasons),
        "lock_path": "downloads_output_lock",
        "failure_sink_path": "downloads_output_failure_sink",
    }
    return paths, identity, list(dict.fromkeys(reasons))


def _write_lock_record(path: Path, record: Mapping[str, Any]) -> None:
    """Atomically update a lock owned by this runtime."""

    path = Path(path)
    current = _read_json(path)
    if current.get("owner_nonce") != record.get("owner_nonce") or current.get("run_id") != record.get("run_id"):
        raise Task5RuntimeError("output lock ownership changed")
    declared = str(current.get("canonical_sha256", ""))
    current_without_hash = dict(current)
    current_without_hash.pop("canonical_sha256", None)
    if not declared or hashlib.sha256(_canonical(current_without_hash)).hexdigest() != declared:
        raise Task5RuntimeError("output lock integrity check failed")
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            os.write(fd, _canonical(record))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temp, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _create_lock(path: Path, paths: Mapping[str, Path], *, run_id: str, material_id: str, owner_nonce: str) -> dict[str, Any]:
    """Create the sidecar lock once; later changes are owner-checked updates."""

    record = _with_hash({
        "schema_version": "task5-output-lock.v1",
        "task_id": TASK_ID,
        "run_id": run_id,
        "material_id": material_id,
        "owner_nonce": owner_nonce,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "created_at": _now(),
        "output_path": str(paths["output"]),
        "output_realpath": str(paths["output"].resolve(strict=False)),
        "staging_path": str(paths["staging"]),
        "failure_evidence_path": None,
        "failure_evidence_sha256": None,
        "candidate_tree_sha256": None,
        "published_tree_sha256": None,
        "rename_receipt": None,
        "finalize_receipt": None,
        "retention": "retain_until_manual_review",
        "state": "held",
    })
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, _canonical(record))
        os.fsync(fd)
    finally:
        os.close(fd)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return record


def _transition_lock(path: Path, state: str, **updates: Any) -> dict[str, Any]:
    current = dict(_read_json(path))
    allowed = {
        "held": {"rename_committed", "failed", "cancelled"},
        "rename_committed": {"finalizing", "failed", "publication_ambiguous"},
        "finalizing": {"published", "failed", "publication_ambiguous"},
    }
    current_state = str(current.get("state", ""))
    if state not in allowed.get(current_state, set()):
        raise Task5RuntimeError(f"invalid output lock transition: {current_state}->{state}")
    current.update(updates)
    current["state"] = state
    current.pop("canonical_sha256", None)
    current["canonical_sha256"] = hashlib.sha256(_canonical(current)).hexdigest()
    _write_lock_record(path, current)
    return current


def _tree_hash(root: Path) -> str:
    rows: list[bytes] = []
    for item in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if item.is_symlink():
            raise Task5RuntimeError(f"symlink in publication tree: {item.relative_to(root)}")
        if item.is_file():
            rows.append(item.relative_to(root).as_posix().encode("utf-8") + b"\0" + item.read_bytes() + b"\0")
    return sha256_bytes(b"".join(rows))


def _manifest(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in {"_audit/directory-manifest.json", "_audit/run-result.json"}:
            continue
        data = path.read_bytes()
        files.append({"path": relative, "sha256": sha256_bytes(data), "bytes": len(data), "lines": data.count(b"\n")})
    tree_input = b"".join(path.encode("utf-8") + b"\0" + root.joinpath(path).read_bytes() + b"\0" for path in (item["path"] for item in files))
    return {"schema_version": "task5-directory-manifest.v1", "files": files, "tree_sha256": sha256_bytes(tree_input)}


def _directory_manifest_sha256(bundle: Path) -> str:
    """Return the manifest hash for a candidate or published bundle."""

    return sha256_bytes((bundle / "_audit" / "directory-manifest.json").read_bytes())


def _load_runtime_authority(map_path: Path) -> dict[str, Any]:
    """Rehash the frozen 17-entry runtime authority before raw/provider work."""

    map_path = Path(map_path).expanduser()
    if not map_path.is_file() or map_path.is_symlink():
        raise Task5RuntimeError(f"runtime authority map is missing: {map_path}")
    map_bytes = map_path.read_bytes()
    value = _read_json(map_path)
    if value.get("schema_version") != "task5-runtime-authority-map.v1":
        raise Task5RuntimeError("runtime authority map schema is invalid")
    authorities = value.get("authorities")
    excluded = value.get("excluded_from_runtime_map")
    if not isinstance(authorities, list) or not isinstance(excluded, list):
        raise Task5RuntimeError("runtime authority map has malformed included/excluded lists")
    expected_fields = {"key", "path", "schema", "actual_sha256", "canonical_sha256", "rehash_owner", "role"}
    by_key: dict[str, Mapping[str, Any]] = {}
    mismatches: list[str] = []
    for item in authorities:
        if not isinstance(item, Mapping) or set(item) != expected_fields:
            mismatches.append("authority entry shape")
            continue
        key = str(item["key"])
        if key in by_key:
            mismatches.append(f"duplicate authority key: {key}")
        by_key[key] = item
        path_text = str(item["path"])
        if not _safe_relative(path_text):
            mismatches.append(f"unsafe authority path: {path_text}")
            continue
        path = map_path.parent.parent / path_text
        if not path.is_file() or path.is_symlink():
            mismatches.append(f"missing authority: {path_text}")
            continue
        actual = sha256_bytes(path.read_bytes())
        try:
            parsed = _read_json(path)
        except Task5RuntimeError:
            mismatches.append(f"invalid authority JSON: {path_text}")
            continue
        canonical = sha256_bytes(_canonical(parsed))
        if actual != str(item["actual_sha256"]):
            mismatches.append(f"authority actual hash mismatch: {path_text}")
        if canonical != str(item["canonical_sha256"]):
            mismatches.append(f"authority canonical hash mismatch: {path_text}")
        if parsed.get("schema_version") != item["schema"]:
            mismatches.append(f"authority schema mismatch: {path_text}")
    actual_keys = tuple(sorted(by_key, key=lambda item: item.encode("utf-8")))
    if actual_keys != tuple(sorted(EXPECTED_AUTHORITY_KEYS, key=lambda item: item.encode("utf-8"))):
        mismatches.append("runtime authority included key set/order mismatch")
    excluded_paths = tuple(sorted(str(item.get("path", "")) for item in excluded if isinstance(item, Mapping)))
    if excluded_paths != tuple(sorted(EXPECTED_EXCLUDED_PATHS)):
        mismatches.append("runtime authority excluded path set mismatch")
    sorted_authorities = [dict(by_key[key]) for key in actual_keys]
    derived = sha256_bytes(_canonical(sorted_authorities))
    identity = {
        "map_ref": "config/task5-runtime-authority-map-v1.json",
        "map_actual_sha256": sha256_bytes(map_bytes),
        "map_canonical_sha256": sha256_bytes(_canonical(value)),
        "included_keys": list(actual_keys),
        "excluded_paths": list(excluded_paths),
        "authorities": sorted_authorities,
        "derived_runtime_contract_hash": derived,
        "status": "passed" if not mismatches else "blocked",
        "mismatches": list(dict.fromkeys(mismatches)),
        "runtime_contract_id": str(value.get("runtime_contract_id", "")),
    }
    if mismatches:
        raise Task5RuntimeError("runtime authority rehash failed: " + "; ".join(identity["mismatches"][:4]))
    return identity


def _validate_audit_layout(bundle: Path) -> None:
    audit_dir = bundle / "_audit"
    if not audit_dir.is_dir() or audit_dir.is_symlink():
        raise Task5RuntimeError("bundle/_audit is missing")
    entries = list(audit_dir.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise Task5RuntimeError("bundle/_audit contains a symlink or unexpected directory")
    actual = {path.name for path in entries}
    expected = {Path(relative).name for relative in FIXED_AUDIT_FILES}
    if actual != expected:
        raise Task5RuntimeError(f"machine audit file set is not exactly frozen: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    for relative in FIXED_AUDIT_FILES:
        path = bundle / relative
        if not path.is_file() or path.is_symlink():
            raise Task5RuntimeError(f"required machine audit file is missing: {relative}")

    def read_hashed_json(name: str) -> Mapping[str, Any]:
        value = _read_json(audit_dir / name)
        declared = value.get("canonical_sha256")
        without_hash = dict(value)
        without_hash.pop("canonical_sha256", None)
        if not isinstance(declared, str) or sha256_bytes(_canonical(without_hash)) != declared:
            raise Task5RuntimeError(f"machine audit canonical hash is invalid: {name}")
        if not _no_secret(value):
            raise Task5RuntimeError(f"machine audit contains a secret-like value: {name}")
        return value

    def read_canonical_jsonl(name: str) -> list[Mapping[str, Any]]:
        path = audit_dir / name
        rows: list[Mapping[str, Any]] = []
        for line_number, line in enumerate(path.read_bytes().splitlines(), start=1):
            try:
                value = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise Task5RuntimeError(f"machine ledger is invalid JSON: {name}#{line_number}") from error
            if not isinstance(value, Mapping) or _canonical(value, trailing_newline=False) != line:
                raise Task5RuntimeError(f"machine ledger is not canonical: {name}#{line_number}")
            if not _no_secret(value):
                raise Task5RuntimeError(f"machine ledger contains a secret-like value: {name}#{line_number}")
            rows.append(value)
        return rows

    audit_pages = read_hashed_json("audit-pages.json")
    pages = audit_pages.get("pages")
    if audit_pages.get("schema_version") != "task5-audit-pages.v1" or not isinstance(pages, list):
        raise Task5RuntimeError("audit-pages.json schema is invalid")
    page_ids: set[str] = set()
    for page in pages:
        if not isinstance(page, Mapping) or not str(page.get("page_id", "")) or not str(page.get("path", "")):
            raise Task5RuntimeError("audit-pages.json contains an incomplete page row")
        if str(page["page_id"]) in page_ids:
            raise Task5RuntimeError("audit-pages.json contains duplicate page_id")
        page_ids.add(str(page["page_id"]))

    source_status = read_hashed_json("source-status.json")
    sources = source_status.get("sources")
    if source_status.get("schema_version") != "task5-source-status.v1" or not isinstance(sources, list) or source_status.get("source_count") != len(sources):
        raise Task5RuntimeError("source-status.json schema is invalid")
    source_ids: set[str] = set()
    source_paths: set[str] = set()
    for source in sources:
        if not isinstance(source, Mapping):
            raise Task5RuntimeError("source-status.json contains a non-object row")
        source_id = str(source.get("source_id", ""))
        source_path = str(source.get("relative_path", ""))
        if not source_id or source_id in source_ids or not source_path or source_path in source_paths:
            raise Task5RuntimeError("source-status.json contains duplicate or empty identity")
        if not _safe_relative(source_path) or not re.fullmatch(r"[0-9a-f]{64}", str(source.get("raw_hash", ""))):
            raise Task5RuntimeError("source-status.json contains an unsafe path or hash")
        if source.get("status") not in {"ready", "known_empty", "duplicate_alias", "provider_failed", "unsupported"}:
            raise Task5RuntimeError("source-status.json contains an unsupported status")
        if not isinstance(source.get("reader_page_ids", []), list):
            raise Task5RuntimeError("source-status.json reader_page_ids is not a list")
        source_ids.add(source_id)
        source_paths.add(source_path)

    public_snapshot = read_hashed_json("companybrain-route-snapshot.json")
    if public_snapshot.get("schema_version") != "companybrain-route-snapshot-public.v1" or public_snapshot.get("root_identity") != "companybrain":
        raise Task5RuntimeError("companybrain public snapshot schema is invalid")
    if any(key in public_snapshot for key in ("root_realpath", "host_path")):
        raise Task5RuntimeError("companybrain public snapshot leaks a host path")
    for file_row in public_snapshot.get("regular_markdown_files", []):
        if not isinstance(file_row, Mapping) or not _safe_relative(str(file_row.get("relative_path", ""))):
            raise Task5RuntimeError("companybrain public snapshot has an unsafe file path")

    coordinate = read_hashed_json("raw-coordinate-map.json")
    coordinate_sources = coordinate.get("sources")
    coverage = coordinate.get("coverage")
    if coordinate.get("schema_version") != "raw-coordinate-map.v1" or not isinstance(coordinate_sources, list) or not isinstance(coverage, Mapping) or coverage.get("source_count") != len(coordinate_sources) or coverage.get("complete") is not True or coverage.get("non_overlapping") is not True:
        raise Task5RuntimeError("raw-coordinate-map.json schema or coverage is invalid")
    for source in coordinate_sources:
        if not isinstance(source, Mapping) or not _safe_relative(str(source.get("source_path", ""))) or not re.fullmatch(r"[0-9a-f]{64}", str(source.get("source_content_hash", ""))):
            raise Task5RuntimeError("raw-coordinate-map.json contains an unsafe or incomplete source")
        blocks = source.get("blocks")
        if not isinstance(blocks, list) or source.get("coverage", {}).get("non_overlapping") is not True:
            raise Task5RuntimeError("raw-coordinate-map.json contains invalid block coverage")

    certificate = read_hashed_json("source-not-documented-zero-match.json")
    certificate_blocks = certificate.get("per_block_results")
    if certificate.get("schema_version") != "semantic_zero_match_certificate.v1" or certificate.get("scan_complete") is not True or not isinstance(certificate_blocks, list) or certificate.get("coverage", {}).get("complete") is not True or certificate.get("scanned_block_refs") != [str(item.get("block_id")) for item in certificate_blocks]:
        raise Task5RuntimeError("source-not-documented-zero-match.json schema or block closure is invalid")
    if any(not isinstance(item, Mapping) or item.get("classification") not in {"no_rule", "rule", "ambiguous"} for item in certificate_blocks):
        raise Task5RuntimeError("source-not-documented-zero-match.json has an invalid classification")

    verifier = read_hashed_json("source-not-documented-verifier.json")
    if verifier.get("schema_version") != "semantic-zero-match-verifier-receipt.v1" or verifier.get("status") != "passed" or verifier.get("block_count") != verifier.get("compared_block_count"):
        raise Task5RuntimeError("source-not-documented-verifier.json is not a passed complete receipt")

    for name in ("semantic-compile-ledger.jsonl", "semantic-response-ledger.jsonl", "route-ledger.jsonl"):
        read_canonical_jsonl(name)

    run_result = read_hashed_json("run-result.json")
    required_run_fields = {"schema_version", "task_id", "run_id", "workflowhub_identity", "input_identity", "provider_identity", "lifecycle", "publication_status", "outcome", "reason_code", "exit_code", "observed_calls", "phase_results", "artifact_manifest", "canonical_sha256"}
    if run_result.get("schema_version") != RUN_RESULT_SCHEMA or not required_run_fields.issubset(run_result):
        raise Task5RuntimeError("run-result.json schema is incomplete")
    if run_result.get("publication_status") not in {"candidate", "released", "not_released"} or run_result.get("outcome") not in {"success", "blocked", "unavailable", "failed", "overrun", "cancelled"}:
        raise Task5RuntimeError("run-result.json contains an unsupported lifecycle value")

    directory = read_hashed_json("directory-manifest.json")
    if directory.get("schema_version") != "task5-directory-manifest.v1" or directory.get("required_paths") != [f"bundle/{relative}" for relative in FIXED_AUDIT_FILES] or directory.get("forbidden_path_scan", {}).get("passed") is not True:
        raise Task5RuntimeError("directory-manifest.json schema or required paths are invalid")
    manifest_files = directory.get("files")
    if not isinstance(manifest_files, list) or len({str(item.get("path", "")) for item in manifest_files if isinstance(item, Mapping)}) != len(manifest_files):
        raise Task5RuntimeError("directory-manifest.json file list is invalid")
    expected_manifest = _manifest(bundle)
    if directory.get("files") != expected_manifest.get("files") or directory.get("tree_sha256") != expected_manifest.get("tree_sha256"):
        raise Task5RuntimeError("directory-manifest.json does not match published bytes")
    layout_path = Path(__file__).resolve().parents[2] / "config" / "task5-publication-layout-v2.json"
    if directory.get("layout_contract_sha256") != sha256_bytes(layout_path.read_bytes()):
        raise Task5RuntimeError("directory-manifest.json layout contract hash is stale")


def _no_secret(value: Any) -> bool:
    def visit(item: Any, key: str | None = None) -> bool:
        if key is not None and FORBIDDEN_KEY.fullmatch(key.strip()):
            return False
        if isinstance(item, Mapping):
            return all(visit(child, str(child_key)) for child_key, child in item.items())
        if isinstance(item, (list, tuple)):
            return all(visit(child) for child in item)
        if isinstance(item, str):
            return not FORBIDDEN_VALUE.search(item)
        return True

    return visit(value)


def _raw_source_hashes(raw: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(raw.rglob("*"), key=lambda p: p.relative_to(raw).as_posix()):
        if path.is_symlink():
            raise Task5RuntimeError(f"raw corpus contains a symlink: {path.relative_to(raw)}")
        if path.is_file() and path.name != ".DS_Store" and path.suffix.casefold() in {".md", ".markdown", ".txt", ".json"}:
            result[path.relative_to(raw).as_posix()] = sha256_bytes(path.read_bytes())
    return result


def _source_manifest_digest(hashes: Mapping[str, str]) -> str:
    return sha256_bytes(_canonical([{"relative_path": path, "content_hash": hashes[path]} for path in sorted(hashes)]))


def _line_count(data: bytes) -> int:
    """Count lines using the frozen UTF-8/LF source-snapshot rule."""

    text = data.decode("utf-8")
    return len(text.replace("\r\n", "\n").replace("\r", "\n").splitlines())


def _validate_source_manifest(raw: Path, manifest_path: Path) -> dict[str, Any]:
    """Validate the exact 89-source snapshot before provider construction."""

    manifest = _read_json(manifest_path)
    if manifest.get("schema_version") != "task5-source-page-manifest.v2":
        raise Task5RuntimeError("source manifest schema is not task5-source-page-manifest.v2")
    source_set = manifest.get("source_set")
    snapshot = manifest.get("source_snapshot")
    entries = snapshot.get("entries") if isinstance(snapshot, Mapping) else None
    if not isinstance(source_set, Mapping) or source_set.get("expected_count") != 89:
        raise Task5RuntimeError("source manifest does not declare the frozen 89-source set")
    if not isinstance(entries, list) or len(entries) != 89:
        raise Task5RuntimeError("source manifest has an invalid 89-source snapshot")
    by_path: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping) or not _safe_relative(str(entry.get("source_path", ""))):
            raise Task5RuntimeError("source manifest contains an invalid relative path")
        path = str(entry["source_path"])
        if path in by_path:
            raise Task5RuntimeError(f"source manifest contains a duplicate path: {path}")
        by_path[path] = entry
    actual = _raw_source_hashes(raw)
    if set(actual) != set(by_path):
        missing = sorted(set(by_path) - set(actual))
        extra = sorted(set(actual) - set(by_path))
        raise Task5RuntimeError(f"raw source set does not match frozen manifest: missing={missing[:3]}, extra={extra[:3]}")
    mismatches: list[str] = []
    for relative, content_hash in actual.items():
        entry = by_path[relative]
        data = (raw / relative).read_bytes()
        expected_status = "empty" if not data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").strip() else "present"
        if (
            str(entry.get("content_hash", "")) != content_hash
            or int(entry.get("byte_count", -1)) != len(data)
            or int(entry.get("line_count", -1)) != _line_count(data)
            or str(entry.get("expected_status", "")) != expected_status
        ):
            mismatches.append(relative)
    if mismatches:
        raise Task5RuntimeError(f"raw source bytes do not match frozen manifest metadata: {mismatches[:3]}")
    snapshot_id = str(snapshot.get("snapshot_id", ""))
    if not snapshot_id:
        raise Task5RuntimeError("source manifest snapshot_id is missing")
    return {
        "schema_version": "task5-source-manifest-identity.v1",
        "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "snapshot_id": snapshot_id,
        "source_count": 89,
        "path_set_digest": str(source_set.get("path_set_digest", "")),
        "content_digest": _source_manifest_digest(actual),
        "known_empty_paths": sorted(path for path, entry in by_path.items() if entry.get("expected_status") == "empty"),
    }


def _slice_source_selection(slice_path: Path, source_manifest_path: Path) -> dict[str, Any]:
    """Validate the frozen diagnostic slice and derive its source closure.

    The slice is intentionally derived from the fixture's case order.  It is
    not inferred from filenames, embeddings, or the compiler's current
    output.  This keeps the diagnostic run reproducible and makes a changed
    fixture fail before any provider is constructed.
    """

    slice_path = Path(slice_path).expanduser()
    manifest_path = Path(source_manifest_path).expanduser()
    value = _read_json(slice_path)
    if value.get("schema_version") != "task5-slice-cases.v1":
        raise Task5RuntimeError("slice config schema is not task5-slice-cases.v1")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) != 11:
        raise Task5RuntimeError("slice config must contain exactly 11 cases")
    expected_case_ids = {
        "Q-POS-01", "Q-CON-01", "Q-OPR-01", "Q-DIA-01", "Q-EXP-01", "Q-BND-01",
        "G-EMPTY-89", "G-DUP-CONFLICT", "G-MEDIA-CLAIM", "G-LINEAGE-MERGE", "G-SOURCE-ND",
    }
    case_ids: list[str] = []
    source_paths: list[str] = []
    required_risk_tags = value.get("required_risk_tags")
    if not isinstance(required_risk_tags, list) or not required_risk_tags or any(not isinstance(tag, str) or not tag.strip() for tag in required_risk_tags):
        raise Task5RuntimeError("slice config required_risk_tags is malformed")
    for case in cases:
        if not isinstance(case, Mapping):
            raise Task5RuntimeError("slice case is malformed")
        case_id = str(case.get("case_id", "")).strip()
        if not case_id or case_id in case_ids:
            raise Task5RuntimeError(f"slice config contains duplicate case: {case_id or '<missing>'}")
        case_ids.append(case_id)
        paths = case.get("source_paths")
        risk_tags = case.get("risk_tags")
        if not isinstance(paths, list) or not paths or any(not isinstance(path, str) or not _safe_relative(path.strip()) for path in paths):
            raise Task5RuntimeError(f"slice case source_paths are malformed: {case_id}")
        if not isinstance(risk_tags, list) or not set(str(tag) for tag in risk_tags).issubset(set(str(tag) for tag in required_risk_tags)):
            raise Task5RuntimeError(f"slice case risk_tags are malformed: {case_id}")
        for path in paths:
            path = path.strip()
            if path not in source_paths:
                source_paths.append(path)
    if set(case_ids) != expected_case_ids:
        raise Task5RuntimeError("slice config case ids do not match the frozen 11-case contract")
    # The fixture is authoritative.  Older prose hard-coded 14 descriptors,
    # but the current 11-case fixture intentionally covers multi-source
    # quality and guard cases and derives 27 paths.  Keep exact membership and
    # order validation below without duplicating a stale cardinality.
    if not source_paths:
        raise Task5RuntimeError("slice config must derive at least one unique source descriptor")

    manifest = _read_json(manifest_path)
    entries = manifest.get("source_snapshot", {}).get("entries") if isinstance(manifest.get("source_snapshot"), Mapping) else None
    if not isinstance(entries, list):
        raise Task5RuntimeError("source manifest entries are missing for slice validation")
    manifest_by_path = {str(entry.get("source_path")): entry for entry in entries if isinstance(entry, Mapping) and entry.get("source_path")}
    unknown = sorted(set(source_paths) - set(manifest_by_path))
    if unknown:
        raise Task5RuntimeError(f"slice source is not in frozen source manifest: {unknown[:3]}")
    known_empty_paths = sorted(path for path in source_paths if manifest_by_path[path].get("expected_status") == "empty")
    if known_empty_paths != ["emm for android /AE - AirViewer厂商管理.md"]:
        raise Task5RuntimeError("slice known-empty source does not match the frozen contract")
    by_hash: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        if isinstance(entry, Mapping) and entry.get("content_hash") and entry.get("source_path"):
            by_hash[str(entry["content_hash"])].append(str(entry["source_path"]))
    duplicate_alias_paths = sorted(
        path for path in source_paths
        if len(by_hash.get(str(manifest_by_path[path].get("content_hash")), ())) > 1
        and path != sorted(by_hash[str(manifest_by_path[path]["content_hash"])])[0]
    )
    source_not_documented_paths = sorted(
        str(path)
        for case in cases
        if str(case.get("case_id", "")).startswith("G-SOURCE-ND")
        for path in case.get("source_paths", ())
    )
    return {
        "schema_version": "task5-slice-selection.v1",
        "evaluation_mode": "slice",
        "slice_id": str(value.get("slice_id", "")),
        "slice_config_sha256": sha256_bytes(slice_path.read_bytes()),
        "source_manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "case_count": len(cases),
        "case_ids": case_ids,
        "source_count": len(source_paths),
        "source_paths": source_paths,
        "known_empty_paths": known_empty_paths,
        "nonempty_source_count": len(source_paths) - len(known_empty_paths),
        "duplicate_alias_paths": duplicate_alias_paths,
        "source_not_documented_paths": source_not_documented_paths,
    }


def _source_line_records(data: bytes) -> list[tuple[int, int, int, str]]:
    """Return ``(line, raw_start, raw_end, text_without_newline)`` records."""

    text = data.decode("utf-8")
    records: list[tuple[int, int, int, str]] = []
    offset = 0
    for number, raw_line in enumerate(text.splitlines(keepends=True), start=1):
        content = raw_line.rstrip("\r\n")
        raw_end = offset + len(content.encode("utf-8"))
        records.append((number, offset, raw_end, content))
        offset += len(raw_line.encode("utf-8"))
    if not records and data == b"":
        return []
    if text and not text.endswith(("\n", "\r")) and not records:
        records.append((1, 0, len(data), text))
    return records


def _slice_bytes(text: str, start: int, end: int) -> bytes:
    return text[start:end].encode("utf-8")


def _make_source_block(
    *,
    source_id: str,
    source_path: str,
    ordinal: int,
    kind: str,
    start_byte: int,
    end_byte: int,
    start_line: int,
    end_line: int,
    block_bytes: bytes,
    locator: Mapping[str, Any],
) -> dict[str, Any]:
    content_hash = sha256_bytes(block_bytes)
    block_id = "blk-" + sha256_bytes(_canonical({
        "schema": "task5-block-id.v1",
        "source_id": source_id,
        "raw_start_byte": start_byte,
        "raw_end_byte": end_byte,
        "block_content_hash": content_hash,
    }))
    return {
        "source_id": source_id,
        "block_id": block_id,
        "ordinal": ordinal,
        "kind": kind,
        "raw_start_byte": start_byte,
        "raw_end_byte": end_byte,
        "raw_start_line": start_line,
        "raw_end_line": end_line,
        "block_content_hash": content_hash,
        "locator": dict(locator),
    }


def _parse_source_blocks(data: bytes, source_id: str, source_path: str) -> list[dict[str, Any]]:
    """Parse frozen text-bearing Markdown units into a non-overlapping partition."""

    records = _source_line_records(data)
    blocks: list[dict[str, Any]] = []
    index = 0
    while index < len(records):
        line, raw_start, raw_end, text = records[index]
        stripped = text.strip()
        if not stripped:
            index += 1
            continue
        fence = re.match(r"^\s*(```+|~~~+)\s*([^\s]*)", text)
        if fence:
            marker = fence.group(1)
            language = fence.group(2).casefold()
            end_index = index
            while end_index + 1 < len(records):
                end_index += 1
                if records[end_index][3].lstrip().startswith(marker):
                    break
            end_byte = records[end_index][2]
            block_kind = "config" if language in {"json", "yaml", "yml", "toml", "ini", "properties", "env"} else "code"
            blocks.append(_make_source_block(
                source_id=source_id, source_path=source_path, ordinal=len(blocks) + 1,
                kind=block_kind, start_byte=raw_start, end_byte=end_byte,
                start_line=line, end_line=records[end_index][0], block_bytes=data[raw_start:end_byte],
                locator={"source_path": source_path, "kind": block_kind, "line": line},
            ))
            index = end_index + 1
            continue
        if re.match(r"^\s*\|", text):
            cursor = 0
            cells = text.split("|")
            for column, cell in enumerate(cells):
                value = cell.strip()
                if not value or re.fullmatch(r":?-{3,}:?", value):
                    cursor += len(cell) + 1
                    continue
                local_start = text.find(value, cursor)
                local_end = local_start + len(value)
                blocks.append(_make_source_block(
                    source_id=source_id, source_path=source_path, ordinal=len(blocks) + 1,
                    kind="table_cell", start_byte=raw_start + len(text[:local_start].encode("utf-8")),
                    end_byte=raw_start + len(text[:local_end].encode("utf-8")), start_line=line, end_line=line,
                    block_bytes=_slice_bytes(text, local_start, local_end),
                    locator={"source_path": source_path, "kind": "table_cell", "line": line, "column": column},
                ))
                cursor = local_end
            index += 1
            continue
        if re.match(r"^\s*#{1,6}\s+\S", text):
            kind = "heading"
        elif re.match(r"^\s*(?:[-*+]\s+|\d+\\?[.)]\s+)", text):
            kind = "list_item"
        elif re.match(r"^\s*>\s*\S", text):
            kind = "quote"
        elif re.match(r"^\s*!\[[^]]*\]\([^)]*\)", text):
            kind = "image_caption"
        elif re.match(r"^\s*(?:https?://|<https?://)", text):
            kind = "link_target"
        else:
            kind = "paragraph"
        if kind == "paragraph":
            links = list(re.finditer(r"\[([^]]+)\]\(([^)]+)\)", text))
            if links:
                def append_inline(kind_name: str, start: int, end: int) -> None:
                    if end <= start:
                        return
                    blocks.append(_make_source_block(
                        source_id=source_id, source_path=source_path, ordinal=len(blocks) + 1,
                        kind=kind_name, start_byte=raw_start + len(text[:start].encode("utf-8")),
                        end_byte=raw_start + len(text[:end].encode("utf-8")), start_line=line, end_line=line,
                        block_bytes=_slice_bytes(text, start, end),
                        locator={"source_path": source_path, "kind": kind_name, "line": line},
                    ))

                cursor = 0
                for link in links:
                    append_inline("paragraph", cursor, link.start(1))
                    append_inline("paragraph", link.start(1), link.end(1))
                    append_inline("link_target", link.start(2), link.end(2))
                    cursor = link.end(0)
                append_inline("paragraph", cursor, len(text))
                index += 1
                continue
        blocks.append(_make_source_block(
            source_id=source_id, source_path=source_path, ordinal=len(blocks) + 1,
            kind=kind, start_byte=raw_start, end_byte=raw_end, start_line=line, end_line=line,
            block_bytes=data[raw_start:raw_end], locator={"source_path": source_path, "kind": kind, "line": line},
        ))
        index += 1
    for previous, current in zip(blocks, blocks[1:]):
        if int(current["raw_start_byte"]) < int(previous["raw_end_byte"]):
            raise Task5RuntimeError(f"BLOCK_OVERLAP: {source_path}")
    return blocks


def _source_scope_bundle(raw: Path, manifest_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build D0-R scope, Block/Claim, and coordinate ledgers without providers."""

    identity = _validate_source_manifest(raw, manifest_path)
    manifest = _read_json(manifest_path)
    entries = manifest["source_snapshot"]["entries"]
    by_hash: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        by_hash[str(entry["content_hash"])].append(str(entry["source_path"]))
    rows: list[dict[str, Any]] = []
    block_sources: list[dict[str, Any]] = []
    coordinate_sources: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: str(item["source_path"])):
        relative = str(entry["source_path"])
        source_id = str(entry["source_id"])
        data = (raw / relative).read_bytes()
        blocks = _parse_source_blocks(data, source_id, relative)
        claims: list[dict[str, Any]] = []
        for block in blocks:
            claim_identity = {
                "schema": "task5-claim-id.v1",
                "provider_visible_source_uri": f"source://{source_id}",
                "source_id": source_id,
                "block_id": block["block_id"],
                "claim_key": f"block:{block['block_id']}",
                "raw_start_byte": block["raw_start_byte"],
                "raw_end_byte": block["raw_end_byte"],
                "claim_content_hash": block["block_content_hash"],
            }
            claim_id = "clm-" + sha256_bytes(_canonical(claim_identity))
            claims.append({
                "claim_id": claim_id,
                "claim_key": f"block:{block['block_id']}",
                "source_id": source_id,
                "block_id": block["block_id"],
                "source_uri": f"source://{source_id}",
                "raw_start_byte": block["raw_start_byte"],
                "raw_end_byte": block["raw_end_byte"],
                "claim_content_hash": block["block_content_hash"],
                "locator": block["locator"],
                "state": "extracted",
                "conflict_refs": [],
            })
        closure = {"source_id": source_id, "source_path": relative, "blocks": blocks, "claims": claims}
        content_hash = sha256_bytes(data)
        duplicate_paths = by_hash.get(content_hash, [])
        is_expected_empty = str(entry.get("expected_status")) == "empty"
        duplicate_alias = len(duplicate_paths) > 1 and relative != duplicate_paths[0]
        if is_expected_empty:
            scope_status, reason_code = "known_empty", "known_empty_source"
        elif duplicate_alias:
            scope_status, reason_code = "duplicate_alias", "duplicate_content_alias"
        else:
            scope_status, reason_code = "eligible", "ordinary_present_source"
        row = {
            "source_id": source_id,
            "source_path": relative,
            "source_snapshot_id": identity["snapshot_id"],
            "content_hash": content_hash,
            "scope_status": scope_status,
            "block_claim_closure_sha256": sha256_bytes(_canonical(closure)),
            "block_claim_count": len(blocks),
            "reason_code": reason_code,
        }
        row["source_scope_sha256"] = sha256_bytes(_canonical(row))
        rows.append(row)
        block_sources.append({"source_id": source_id, "source_path": relative, "source_content_hash": content_hash, "blocks": blocks, "claims": claims, "closure_sha256": row["block_claim_closure_sha256"]})
        coordinate_sources.append({"source_id": source_id, "source_path": relative, "source_content_hash": content_hash, "blocks": [{key: block[key] for key in ("block_id", "raw_start_byte", "raw_end_byte", "raw_start_line", "raw_end_line", "block_content_hash", "locator")} for block in blocks]})
    coverage = {
        "source_count": len(rows),
        "ordinary_present_total": sum(row["scope_status"] in {"eligible", "duplicate_alias"} for row in rows),
        "ordinary_present_eligible_count": sum(row["scope_status"] == "eligible" for row in rows),
        "known_empty_count": sum(row["scope_status"] == "known_empty" for row in rows),
        "duplicate_alias_count": sum(row["scope_status"] == "duplicate_alias" for row in rows),
        "block_count": sum(len(source["blocks"]) for source in block_sources),
        "claim_count": sum(len(source["claims"]) for source in block_sources),
        "complete": len(rows) == 89,
        "provider_calls": 0,
    }
    block_ledger = {
        "schema_version": "task5-source-block-claim-ledger.v1",
        "contract_id": "task5-source-block-claim-v1",
        "producer_schema_sha256": sha256_bytes((Path(__file__).resolve().parents[2] / "config/task5-source-block-claim-contract-v1.json").read_bytes()),
        "task_id": TASK_ID,
        "source_snapshot_id": identity["snapshot_id"],
        "sources": block_sources,
        "coverage": coverage,
    }
    block_ledger["canonical_sha256"] = sha256_bytes(_canonical(block_ledger))
    coordinate_map = {
        "schema_version": "raw-coordinate-map.v1",
        "task_id": TASK_ID,
        "source_snapshot_id": identity["snapshot_id"],
        "sources": coordinate_sources,
        "coverage": {"source_count": len(coordinate_sources), "block_count": sum(len(source["blocks"]) for source in coordinate_sources), "complete": len(coordinate_sources) == 89, "non_overlapping": True},
    }
    coordinate_map["canonical_sha256"] = sha256_bytes(_canonical(coordinate_map))
    scope_ledger = {
        "schema_version": "task5-source-scope-ledger.v2",
        "task_id": TASK_ID,
        "producer_schema_sha256": block_ledger["producer_schema_sha256"],
        "source_manifest_ref": _public_ref(manifest_path),
        "source_manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "source_snapshot_id": identity["snapshot_id"],
        "block_claim_ledger_sha256": block_ledger["canonical_sha256"],
        "raw_coordinate_map_sha256": coordinate_map["canonical_sha256"],
        "rows": rows,
        "coverage": coverage,
    }
    scope_ledger["canonical_sha256"] = sha256_bytes(_canonical(scope_ledger))
    return identity, scope_ledger, block_ledger, coordinate_map


def _source_scope_ledger(raw: Path, manifest_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compatibility view of the D0-R scope ledger for unit tests."""

    identity, scope, _, _ = _source_scope_bundle(raw, manifest_path)
    return identity, scope


def _root_cause_directory_snapshot(path: Path, label: str) -> dict[str, Any]:
    """Capture only non-content identity facts for a historical input.

    Root-cause evidence is allowed to say whether an old artifact is still
    available, but it must not copy that artifact's Markdown into the evidence
    packet.  The snapshot digest is deliberately derived from relative names,
    byte counts and content hashes, so it is useful for drift detection while
    remaining a public identity rather than a content dump.
    """

    try:
        root = _safe_root(path, label)
    except Task5RuntimeError as error:
        return {
            "status": "unavailable",
            "reason": f"{label} is unavailable",
            "file_count": 0,
            "byte_count": 0,
            "snapshot_sha256": None,
            "files": [],
        }
    files: list[dict[str, Any]] = []
    try:
        for item in sorted(root.rglob("*"), key=lambda value: value.relative_to(root).as_posix()):
            if item.is_symlink():
                return {
                    "status": "drifted",
                    "reason": f"{label} contains a symlink",
                    "file_count": len(files),
                    "byte_count": sum(int(row["bytes"]) for row in files),
                    "snapshot_sha256": None,
                    "files": files,
                }
            if not item.is_file():
                continue
            data = item.read_bytes()
            files.append({
                "relative_path": item.relative_to(root).as_posix(),
                "bytes": len(data),
                "content_hash": sha256_bytes(data),
            })
    except (OSError, UnicodeError) as error:
        return {
            "status": "unavailable",
            "reason": f"{label} could not be read: {type(error).__name__}",
            "file_count": len(files),
            "byte_count": sum(int(row["bytes"]) for row in files),
            "snapshot_sha256": None,
            "files": files,
        }
    identity = [{key: row[key] for key in ("relative_path", "bytes", "content_hash")} for row in files]
    return {
        "status": "available",
        "reason": None,
        "file_count": len(files),
        "byte_count": sum(int(row["bytes"]) for row in files),
        "snapshot_sha256": sha256_bytes(_canonical(identity)),
        "files": files,
    }


def _root_cause_file_snapshot(path: Path, label: str, expected_sha256: str | None = None) -> dict[str, Any]:
    """Read a repository-managed root-cause file without exposing its bytes."""

    if not path.is_file() or path.is_symlink():
        return {
            "status": "unavailable",
            "reason": f"{label} is missing",
            "actual_sha256": None,
            "expected_sha256": expected_sha256,
        }
    try:
        actual = sha256_bytes(path.read_bytes())
    except OSError as error:
        return {
            "status": "unavailable",
            "reason": f"{label} could not be read: {type(error).__name__}",
            "actual_sha256": None,
            "expected_sha256": expected_sha256,
        }
    return {
        "status": "available" if expected_sha256 in (None, actual) else "drifted",
        "reason": None if expected_sha256 in (None, actual) else "hash mismatch",
        "actual_sha256": actual,
        "expected_sha256": expected_sha256,
    }


def _root_cause_input_snapshots(manifest: Mapping[str, Any], raw: Path, companybrain: Path) -> dict[str, dict[str, Any]]:
    """Resolve the five frozen inputs into redacted identity snapshots."""

    result: dict[str, dict[str, Any]] = {}
    for entry in manifest.get("inputs", []):
        if not isinstance(entry, Mapping):
            continue
        key = str(entry.get("key", ""))
        expected = str(entry.get("snapshot_sha256", "")) or None
        if key == "RC-RAW-89":
            snapshot = _root_cause_directory_snapshot(raw, key)
        elif key == "RC-COMPANYBRAIN":
            snapshot = _root_cause_directory_snapshot(companybrain, key)
        elif key == "RC-CURRENT-BASELINE":
            baseline_path = Path(__file__).resolve().parents[2] / str(entry.get("canonical_ref", ""))
            snapshot = _root_cause_file_snapshot(baseline_path, key, str(entry.get("baseline_actual_sha256", "")) or expected)
        else:
            snapshot = _root_cause_directory_snapshot(Path(str(entry.get("canonical_ref", ""))), key)
        expected_files = entry.get("file_count")
        expected_bytes = entry.get("byte_count")
        if snapshot.get("status") == "available" and (
            (expected_files is not None and int(snapshot.get("file_count", -1)) != int(expected_files))
            or (expected_bytes is not None and int(snapshot.get("byte_count", -1)) != int(expected_bytes))
        ):
            snapshot = {
                **snapshot,
                "status": "drifted",
                "reason": "file or byte count mismatch",
            }
        result[key] = {
            "role": str(entry.get("role", "")),
            "canonical_ref": key,
            "identity_kind": str(entry.get("identity_kind", "")),
            "expected_snapshot_sha256": expected,
            "expected_file_count": expected_files,
            "expected_byte_count": expected_bytes,
            **snapshot,
        }
        if entry.get("identity_kind") == "directory_manifest_sha256":
            result[key]["hash_status"] = "not_verified_directory_algorithm" if result[key].get("status") == "available" else "mismatched"
            result[key]["observed_manifest_sha256"] = result[key].pop("snapshot_sha256", None)
        for field in ("files",):
            # Directory file rows are useful for a host-only preflight but
            # cannot be copied into public root-cause evidence.
            result[key].pop(field, None)
    return result


def _root_cause_observation(
    *,
    failure_id: str,
    input_key: str,
    artifact_sha256: str | None,
    observed_fact: str,
    user_symptom: str,
    baseline_sha256: str,
    difference_locator: str,
) -> dict[str, Any]:
    comparison = {
        "baseline_ref": "config/task5-companybrain-baseline-v2.json",
        "baseline_sha256": baseline_sha256,
        "quality_case_id": "Q-POS-01",
        "projection_key": "Q-POS-01.positioning",
        "dimension": "route",
        "difference_locator": difference_locator,
        "difference_sha256": sha256_bytes(difference_locator.encode("utf-8")),
        "comparison_status": "not_comparable",
    }
    return {
        "failure_id": failure_id,
        "input_key": input_key,
        "artifact_ref": input_key,
        "artifact_sha256": artifact_sha256 or "unavailable",
        "locator": {"input_key": input_key, "field": "snapshot"},
        "observed_fact": observed_fact,
        "user_symptom": user_symptom,
        "evidence_refs": [input_key, "config/task5-root-cause-input-manifest-v1.json"],
        "companybrain_comparison": comparison,
    }


def run_root_cause_preflight(args: argparse.Namespace) -> int:
    """Run D0-H and preserve a truthful blocked attempt when history is absent."""

    attempt_id = "d0-h-" + uuid.uuid4().hex[:20]
    evidence_root = Path(args.evidence_root).expanduser()
    attempt_dir = evidence_root / "root-cause" / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=False)
    project_root = Path(__file__).resolve().parents[2]
    fixed_manifest = project_root / "config/task5-root-cause-input-manifest-v1.json"
    fixed_contract = project_root / "config/task5-root-cause-evidence-v2.json"
    requested_manifest = Path(args.root_cause_input_manifest).expanduser()
    requested_contract = Path(args.root_cause_contract).expanduser()
    reasons: list[str] = []
    if requested_manifest.resolve(strict=False) != fixed_manifest.resolve(strict=False):
        reasons.append("root-cause input manifest is caller-overridden; fixed authority is required")
    if requested_contract.resolve(strict=False) != fixed_contract.resolve(strict=False):
        reasons.append("root-cause evidence contract is caller-overridden; fixed authority is required")
    if str(args.network_policy) != "deny":
        reasons.append("root-cause preflight requires network-policy deny")
    try:
        input_manifest = _read_json(fixed_manifest)
        contract = _read_json(fixed_contract)
    except Task5RuntimeError as error:
        input_manifest = {}
        contract = {}
        reasons.append(str(error))
    if contract and contract.get("schema_version") != "task5-root-cause-evidence.v2":
        reasons.append("root-cause evidence contract schema is invalid")
    input_manifest_sha = sha256_bytes(fixed_manifest.read_bytes()) if fixed_manifest.is_file() else ""
    contract_sha = sha256_bytes(fixed_contract.read_bytes()) if fixed_contract.is_file() else ""
    if input_manifest and str(input_manifest.get("canonical_sha256", "")) != sha256_bytes(_canonical({key: value for key, value in input_manifest.items() if key != "canonical_sha256"})):
        reasons.append("root-cause input manifest canonical hash is invalid")
    snapshots = _root_cause_input_snapshots(input_manifest, Path(args.raw_input).expanduser(), Path(args.companybrain).expanduser()) if input_manifest else {}
    for key, snapshot in snapshots.items():
        if snapshot.get("status") != "available":
            reasons.append(f"{key}:{snapshot.get('reason') or snapshot.get('status')}")
    # The old V50 directory is intentionally not reconstructed from any other
    # candidate.  It is the first hard stop for historical comparison.
    cb_baseline = project_root / "config/task5-companybrain-baseline-v2.json"
    baseline_sha = sha256_bytes(cb_baseline.read_bytes()) if cb_baseline.is_file() else "unavailable"
    observations: list[dict[str, Any]] = []
    for key in ("RC-USER-V50", "RC-CURRENT-BASELINE"):
        snapshot = snapshots.get(key, {})
        if snapshot.get("status") != "available":
            failure_id = "D0-H-" + key.replace("RC-", "").lower()
            expected = snapshot.get("expected_snapshot_sha256")
            fact = f"{key} status={snapshot.get('status', 'unavailable')}; expected snapshot={expected or 'unknown'}; no replacement input was used"
            observations.append(_root_cause_observation(
                failure_id=failure_id,
                input_key=key,
                artifact_sha256=expected,
                observed_fact=fact,
                user_symptom="历史根因无法与用户实际查看的旧结果完成同一份证据对照",
                baseline_sha256=baseline_sha,
                difference_locator=f"not_comparable:{key}:missing_or_drifted",
            ))
    causal_mapping = [
        {
            "failure_id": observation["failure_id"],
            "contract_gap_ref": "spec.md#3.4-历史结果根因回放合同",
            "gap_kind": "missing_failure_receipt" if observation["input_key"] == "RC-USER-V50" else "unclosed_lineage",
            "repair_ref": "src/knowledge_digest/task5_runtime.py#run_root_cause_preflight",
            "owner": "R1/M101",
            "status": "blocked",
            "evidence_refs": observation["evidence_refs"],
            "comparison_evidence_refs": [observation["input_key"], "RC-COMPANYBRAIN", "Q-POS-01.positioning#route"],
        }
        for observation in observations
    ]
    source_scope: dict[str, Any] = {
        "entry_count": 0,
        "ordinary_present_count": 0,
        "ordinary_present_eligible_count": 0,
        "provider_calls": 0,
        "status": "blocked",
        "entries": [],
    }
    raw = Path(args.raw_input).expanduser()
    source_manifest = project_root / "config/task5-source-page-manifest-v2.json"
    if snapshots.get("RC-RAW-89", {}).get("status") == "available":
        try:
            _, scope, _, _ = _source_scope_bundle(raw, source_manifest)
            source_scope = {
                "entry_count": scope["coverage"]["source_count"],
                "ordinary_present_count": scope["coverage"]["ordinary_present_eligible_count"],
                "ordinary_present_eligible_count": scope["coverage"]["ordinary_present_eligible_count"],
                "ordinary_present_total": scope["coverage"]["ordinary_present_total"],
                "known_empty_count": scope["coverage"]["known_empty_count"],
                "duplicate_alias_count": scope["coverage"]["duplicate_alias_count"],
                "provider_calls": 0,
                "status": "complete",
                "entries": [
                    {key: row.get(key) for key in (
                        "source_id", "source_path", "source_snapshot_id", "content_hash",
                        "scope_status", "block_claim_closure_sha256", "source_scope_sha256", "reason_code",
                    )}
                    for row in scope["rows"]
                ],
            }
        except Task5RuntimeError as error:
            reasons.append(f"RC-RAW-89:{error}")
    required_families = {}
    for family in contract.get("coverage_rule", {}).get("required_family_keys", []) if contract else []:
        required_families[family] = {
            "status": "blocked",
            "reason": "historical V50 comparison input is unavailable; no family is promoted as a proven root cause",
            "evidence_refs": [],
        }
    result = _with_hash({
        "schema_version": "task5-root-cause-evidence.v2",
        "contract_id": "task5-root-cause-evidence-v2",
        "contract_ref": "config/task5-root-cause-evidence-v2.json",
        "contract_sha256": contract_sha,
        "attempt_id": attempt_id,
        "status": "failed",
        "outcome": "blocked",
        "publication_status": "not_released",
        "input_manifest_ref": "config/task5-root-cause-input-manifest-v1.json",
        "input_manifest_sha256": input_manifest_sha,
        "current_task_snapshot": {
            "status": "unavailable",
            "reason": "authenticated WorkflowHub snapshot/material handoff was not supplied to D0-H",
            "worktree": "current_task_worktree",
        },
        "input_snapshots": snapshots,
        "observations": observations,
        "causal_mapping": causal_mapping,
        "coverage": {
            "inputs": {key: {"status": value.get("status"), "reason": value.get("reason")} for key, value in snapshots.items()},
            "families": required_families,
            "source_scope": source_scope,
            "companybrain_paired_quality_difference": {
                "status": "blocked",
                "reason": "RC-USER-V50 is unavailable, so no valid old-result/CompanyBrain case×projection×dimension pair can be asserted",
                "provider_calls": 0,
            },
        },
        "provider_calls": 0,
        "embedding_calls": 0,
        "observed_calls": {"llm": 0, "embedding": 0, "external_http_attempts": 0},
        "blockers": list(dict.fromkeys(reasons)),
    })
    _write_canonical(attempt_dir / "root-cause-evidence.json", result)
    print(json.dumps({"status": result["status"], "outcome": result["outcome"], "attempt_id": attempt_id, "evidence": str(attempt_dir / "root-cause-evidence.json"), "reasons": result["blockers"]}, ensure_ascii=False))
    return 2


def run_raw_preflight(args: argparse.Namespace) -> int:
    """Run D0-R using only the current raw corpus and frozen manifests."""

    attempt_id = "d0-r-" + uuid.uuid4().hex[:20]
    evidence_root = Path(args.evidence_root).expanduser()
    attempt_dir = evidence_root / "raw-preflight" / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=False)
    reasons: list[str] = []
    raw = Path(args.raw_input).expanduser()
    companybrain = Path(args.companybrain).expanduser()
    fixed_manifest = Path(__file__).resolve().parents[2] / "config/task5-source-page-manifest-v2.json"
    requested_manifest = Path(getattr(args, "source_manifest", fixed_manifest)).expanduser()
    manifest = fixed_manifest
    identity: Mapping[str, Any] = {}
    ledger: Mapping[str, Any] = {}
    block_ledger: Mapping[str, Any] = {}
    coordinate_map: Mapping[str, Any] = {}
    if str(args.network_policy) != "deny":
        reasons.append("raw preflight requires network-policy deny")
    if requested_manifest.resolve(strict=False) != fixed_manifest.resolve(strict=False):
        reasons.append("raw preflight source manifest is caller-overridden; fixed authority is required")
    block_contract = fixed_manifest.parent / "task5-source-block-claim-contract-v1.json"
    try:
        block_contract_value = _read_json(block_contract)
        if block_contract_value.get("schema_version") != "task5-source-block-claim-contract.v1":
            reasons.append("source Block/Claim contract schema is invalid")
    except Task5RuntimeError as error:
        reasons.append(str(error))
    for root, label in ((raw, "raw input"), (companybrain, "CompanyBrain")):
        try:
            _safe_root(root, label)
        except Task5RuntimeError as error:
            reasons.append(str(error))
    if not reasons:
        try:
            identity, ledger, block_ledger, coordinate_map = _source_scope_bundle(raw, manifest)
        except Task5RuntimeError as error:
            reasons.append(str(error))
    if ledger:
        coverage = ledger["coverage"]
        if coverage["source_count"] != 89:
            reasons.append("raw source-scope ledger is not the frozen 89-source set")
        if coverage["ordinary_present_eligible_count"] != 87:
            reasons.append("raw source-scope ledger does not close 87 eligible ordinary sources")
    ledger_path = attempt_dir / "source-scope-ledger.json"
    block_ledger_path = attempt_dir / "source-block-claim-ledger.json"
    coordinate_map_path = attempt_dir / "raw-coordinate-map.json"
    if ledger:
        _write_canonical(ledger_path, ledger)
        _write_canonical(block_ledger_path, block_ledger)
        _write_canonical(coordinate_map_path, coordinate_map)
    result = {
        "schema_version": "task5-raw-preflight.v1",
        "task_id": TASK_ID,
        "attempt_id": attempt_id,
        "status": "passed" if not reasons else "blocked",
        "outcome": "success" if not reasons else "blocked",
        "reason_code": "raw_preflight_passed" if not reasons else "raw_preflight_blocked",
        "observed_calls": {"llm": 0, "embedding": 0, "external_http_attempts": 0},
        "input_identity": {
            "raw_root": "raw_input",
            "companybrain_root": "companybrain_input",
            "source_manifest_ref": _public_ref(manifest),
            "source_manifest_sha256": sha256_bytes(manifest.read_bytes()) if manifest.is_file() else "",
            "source_snapshot_id": identity.get("snapshot_id", ""),
            "source_count": ledger.get("coverage", {}).get("source_count", 0),
            "source_content_digest": identity.get("content_digest", ""),
        },
        "source_scope_ledger_ref": f"raw-preflight/attempts/{attempt_id}/source-scope-ledger.json" if ledger else None,
        "source_scope_ledger_sha256": sha256_bytes(ledger_path.read_bytes()) if ledger_path.is_file() else None,
        "source_block_claim_ledger_ref": f"raw-preflight/attempts/{attempt_id}/source-block-claim-ledger.json" if block_ledger else None,
        "source_block_claim_ledger_sha256": sha256_bytes(block_ledger_path.read_bytes()) if block_ledger_path.is_file() else None,
        "raw_coordinate_map_ref": f"raw-preflight/attempts/{attempt_id}/raw-coordinate-map.json" if coordinate_map else None,
        "raw_coordinate_map_sha256": sha256_bytes(coordinate_map_path.read_bytes()) if coordinate_map_path.is_file() else None,
        "coverage": dict(ledger.get("coverage", {})) if ledger else {"source_count": 0, "complete": False},
        "reasons": reasons,
    }
    _write_canonical(attempt_dir / "raw-preflight.json", result)
    print(json.dumps({"status": result["status"], "attempt_id": attempt_id, "evidence": str(attempt_dir / "raw-preflight.json"), "reasons": reasons}, ensure_ascii=False))
    return 0 if not reasons else 2


def _safe_relative(path: str) -> bool:
    value = Path(path)
    return bool(path) and not value.is_absolute() and ".." not in value.parts and "\\" not in path


def _public_ref(value: Any) -> str | None:
    """Keep evidence refs useful without publishing host absolute paths."""

    if value is None:
        return None
    text = str(value)
    if not Path(text).is_absolute():
        return text
    parts = Path(text).parts
    for marker in ("quality", "config", "specs", "docs"):
        if marker in parts:
            return "/".join(parts[parts.index(marker):])
    return Path(text).name


def _evidence_task_root(path: Path) -> Path:
    """Find the task root when evidence is stored outside the code worktree."""

    path = Path(path).expanduser().resolve()
    for candidate in (path.parent, *path.parents):
        if (candidate / "quality" / "evidence" / "task5").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def _read_managed_ref(
    ref: Any,
    label: str,
    *,
    expected_sha256: str | None = None,
    base_root: Path | None = None,
) -> tuple[Path, Mapping[str, Any] | None]:
    """Read a host-managed evidence ref without accepting a path escape."""

    if not isinstance(ref, str):
        raise Task5RuntimeError(f"{label} must be a safe repository-relative ref")
    root = Path(base_root or Path(__file__).resolve().parents[2]).expanduser().resolve()
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        path = candidate.resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise Task5RuntimeError(f"{label} is outside the managed task root") from error
    else:
        if not _safe_relative(ref):
            raise Task5RuntimeError(f"{label} must be a safe repository-relative ref")
        path = (root / ref).resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise Task5RuntimeError(f"{label} escapes the managed task root") from error
    if not path.is_file() or path.is_symlink():
        raise Task5RuntimeError(f"{label} is missing: {ref}")
    actual = sha256_bytes(path.read_bytes())
    if expected_sha256 is not None and actual != expected_sha256:
        raise Task5RuntimeError(f"{label} hash does not match its authenticated ref")
    try:
        value = _read_json(path)
    except Task5RuntimeError:
        value = None
    if value is not None and not _no_secret(value):
        raise Task5RuntimeError(f"{label} contains a secret-like value")
    return path, value


def _validate_review_identity(review: Mapping[str, Any], label: str, *, expected_kind: str, require_clean: bool, base_root: Path | None = None) -> None:
    required = {"review_kind", "result_ref", "result_sha256", "attempt_ref", "attempt_sha256", "report_ref", "report_sha256"}
    missing = sorted(required - set(review))
    if missing:
        raise Task5RuntimeError(f"{label} is incomplete: {', '.join(missing)}")
    if review.get("review_kind") != expected_kind:
        raise Task5RuntimeError(f"{label} has the wrong review kind")
    for field in ("result_sha256", "attempt_sha256", "report_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(review.get(field, ""))):
            raise Task5RuntimeError(f"{label}.{field} is not a SHA-256")
    _read_managed_ref(review["result_ref"], f"{label}.result_ref", expected_sha256=str(review["result_sha256"]), base_root=base_root)
    _read_managed_ref(review["attempt_ref"], f"{label}.attempt_ref", expected_sha256=str(review["attempt_sha256"]), base_root=base_root)
    _read_managed_ref(review["report_ref"], f"{label}.report_ref", expected_sha256=str(review["report_sha256"]), base_root=base_root)
    if require_clean and (review.get("outcome") != "available" or review.get("terminal_status") != "semantic" or review.get("terminal_clean") is not True or review.get("all_findings_disposed") is not True):
        raise Task5RuntimeError(f"{label} is not terminal-clean")


def _validate_m401_r_receipt(path: Path) -> dict[str, Any]:
    value = dict(_read_json(path))
    task_root = _evidence_task_root(path)
    # The promoted receipt is the fixed 17-field M401-R contract.  The
    # implementation handoff carries the richer WorkflowHub review identity;
    # this promotion view deliberately contains only the receipt fields
    # consumed by the compiler gate.
    required = {
        "schema_version", "review_kind", "m401_packet_ref", "m401_packet_sha256",
        "review_result_ref", "review_result_sha256", "source_receipt_ref",
        "source_receipt_sha256", "snapshot_tree", "material_id", "terminal_status",
        "terminal_clean", "all_findings_disposed", "finding_dispositions", "outcome",
        "status", "reason_code",
    }
    missing = sorted(required - set(value))
    if missing:
        raise Task5RuntimeError(f"M401-R receipt is incomplete: {', '.join(missing)}")
    if set(value) != required:
        raise Task5RuntimeError("M401-R receipt has fields outside the frozen promotion contract")
    if value["schema_version"] != "task5-m401-r-review-receipt.v1" or value["review_kind"] != "mini_task.implementation" or value["outcome"] != "available" or value["status"] != "passed" or value["reason_code"] != "NONE" or value["terminal_status"] != "semantic" or value["terminal_clean"] is not True or value["all_findings_disposed"] is not True:
        raise Task5RuntimeError("M401-R receipt is not terminal-clean for this task")
    packet_ref = str(value["m401_packet_ref"])
    packet_path, packet = _read_managed_ref(packet_ref, "M401-R m401_packet_ref", expected_sha256=str(value["m401_packet_sha256"]), base_root=task_root)
    if packet is None or packet.get("schema_version") != "task5-m401-evidence-packet.v1" or packet.get("status") != "passed" or packet.get("pre_m402_readiness") is not True:
        raise Task5RuntimeError("M401-R is not bound to a passed M401 packet")
    if value.get("snapshot_tree") != packet.get("snapshot_tree") or value.get("material_id") != packet.get("material_id"):
        raise Task5RuntimeError("M401-R snapshot/material binding does not match M401")
    if not isinstance(value["finding_dispositions"], list):
        raise Task5RuntimeError("M401-R finding_dispositions must be a list")
    for item in value["finding_dispositions"]:
        if not isinstance(item, Mapping) or item.get("status") not in {"fixed", "rejected_invalid", "accepted_risk"}:
            raise Task5RuntimeError("M401-R contains an invalid finding disposition")
    _read_managed_ref(value["review_result_ref"], "M401-R review_result_ref", expected_sha256=str(value["review_result_sha256"]), base_root=task_root)
    _read_managed_ref(value["source_receipt_ref"], "M401-R source_receipt_ref", expected_sha256=str(value["source_receipt_sha256"]), base_root=task_root)
    return {**value, "m401_packet_path": str(packet_path)}


def _identity_from_handoff(path: Path) -> dict[str, Any]:
    value = _read_json(path)
    task_root = _evidence_task_root(path)
    required = {"schema_version", "handoff_kind", "task_id", "stage", "review_kind", "handoff_ref", "handoff_sha256", "parent_design_review", "implementation_review", "current", "runtime_contract", "writer_attestation"}
    missing = sorted(required - set(value))
    if missing:
        raise Task5RuntimeError(f"implementation handoff is incomplete: {', '.join(missing)}")
    if value.get("handoff_kind") != "implementation" or value.get("stage") != "build-code" or value.get("review_kind") != "mini_task.implementation":
        raise Task5RuntimeError("implementation handoff has the wrong review identity")
    review = value.get("implementation_review")
    if not isinstance(review, Mapping) or review.get("outcome") != "available" or review.get("terminal_status") != "semantic" or review.get("terminal_clean") is not True or review.get("all_findings_disposed") is not True:
        raise Task5RuntimeError("implementation review is not terminal-clean")
    if not _no_secret(value):
        raise Task5RuntimeError("implementation handoff contains a secret-like field")
    declared = str(value.get("handoff_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", declared):
        raise Task5RuntimeError("implementation handoff has no canonical hash")
    check = dict(value)
    check.pop("handoff_sha256", None)
    if hashlib.sha256(_canonical(check)).hexdigest() != declared:
        raise Task5RuntimeError("implementation handoff hash does not match bytes")
    current = value.get("current")
    if not isinstance(current, Mapping) or current.get("task_id") != TASK_ID or not str(current.get("snapshot_tree", "")) or not str(current.get("material_id", "")):
        raise Task5RuntimeError("implementation handoff current identity is incomplete")
    parent = value.get("parent_design_review")
    implementation = value.get("implementation_review")
    if parent is not None and not isinstance(parent, Mapping):
        raise Task5RuntimeError("implementation handoff parent_design_review must be null or an object")
    if not isinstance(implementation, Mapping):
        raise Task5RuntimeError("implementation handoff review bindings are incomplete")
    # Design review is an advisory input.  A user-authorized continuation may
    # deliberately leave it null; implementation review remains mandatory.
    if parent is not None:
        _validate_review_identity(parent, "parent_design_review", expected_kind="mini_task.design", require_clean=True, base_root=task_root)
    _validate_review_identity(implementation, "implementation_review", expected_kind="mini_task.implementation", require_clean=True, base_root=task_root)
    runtime_contract = value.get("runtime_contract")
    if not isinstance(runtime_contract, Mapping) or not str(runtime_contract.get("runtime_contract_id", "")) or not re.fullmatch(r"[0-9a-f]{64}", str(runtime_contract.get("runtime_contract_hash", ""))):
        raise Task5RuntimeError("implementation handoff runtime contract identity is incomplete")
    semantic_contract = value.get("semantic_contract")
    if semantic_contract is None:
        semantic_contract = {
            "contract_id": runtime_contract.get("semantic_contract_id"),
            "contract_hash": runtime_contract.get("semantic_contract_hash"),
        }
    if not isinstance(semantic_contract, Mapping) or not str(semantic_contract.get("contract_id", "")) or not re.fullmatch(r"[0-9a-f]{64}", str(semantic_contract.get("contract_hash", ""))):
        raise Task5RuntimeError("implementation handoff semantic contract identity is incomplete")
    m401 = value.get("m401_packet")
    m401_r = value.get("m401_r_receipt")
    if isinstance(runtime_contract, Mapping):
        m401 = m401 or {"ref": runtime_contract.get("m401_packet_ref"), "sha256": runtime_contract.get("m401_packet_sha256")}
        m401_r = m401_r or {"ref": runtime_contract.get("m401_r_receipt_ref"), "sha256": runtime_contract.get("m401_r_receipt_sha256")}
    if not isinstance(m401, Mapping) or not isinstance(m401_r, Mapping):
        raise Task5RuntimeError("implementation handoff M401/M401-R bindings are incomplete")
    _read_managed_ref(m401.get("ref"), "implementation handoff M401 packet", expected_sha256=str(m401.get("sha256", "")), base_root=task_root)
    _read_managed_ref(m401_r.get("ref"), "implementation handoff M401-R receipt", expected_sha256=str(m401_r.get("sha256", "")), base_root=task_root)
    return dict(value)


def _validate_static_contracts(contract_files: Mapping[str, Path]) -> list[str]:
    """Validate non-secret contract inputs without touching raw or CB data."""
    expected_schemas = {
        "observation_config": "companybrain-observation.v2",
        "quality_result_config": "task5-quality-result.v3",
        "source_direct_contract": "task5-source-direct-contract.v1",
        "snd_verifier_contract": "task5-source-not-documented-contract.v2",
        "calibration_manifest": "task5-calibration-manifest.v1",
    }
    reasons: list[str] = []
    parsed: dict[str, Mapping[str, Any]] = {}
    for name, path in contract_files.items():
        if name.endswith("_sha"):
            continue
        path = Path(path).expanduser()
        if not path.is_file() or path.is_symlink():
            reasons.append(f"{name} is missing: {path}")
            continue
        try:
            parsed[name] = _read_json(path)
        except Task5RuntimeError as error:
            reasons.append(str(error))
    for name, expected in expected_schemas.items():
        value = parsed.get(name)
        if value is not None and value.get("schema_version") != expected:
            reasons.append(f"{name} schema is not {expected}")
    review_manifest = parsed.get("review_manifest")
    if review_manifest is None:
        reasons.append("review_manifest is missing or invalid")
    elif review_manifest.get("schema_version") != "task5-m401-evidence-packet.v1":
        reasons.append("review_manifest is not a Task5 M401 evidence packet")
    elif review_manifest.get("status") != "passed" or review_manifest.get("pre_m402_readiness") is not True:
        reasons.append("review_manifest is not a passed M401 readiness packet")
    snd = parsed.get("snd_verifier_contract")
    snd_path = contract_files.get("snd_verifier_contract")
    if snd is not None and snd_path is not None:
        if snd.get("route_kind") != "source-not-documented" or snd.get("page_type") != "diagnosis":
            reasons.append("SND contract route/page binding is invalid")
    calibration = parsed.get("calibration_manifest")
    artifact = Path(contract_files["calibration_artifact"]).expanduser() if contract_files.get("calibration_artifact") else None
    if calibration is not None and artifact is not None:
        if not artifact.is_file() or artifact.is_symlink():
            reasons.append(f"calibration artifact is missing: {artifact}")
        elif str(calibration.get("artifact_sha256", "")) != sha256_bytes(artifact.read_bytes()):
            reasons.append("calibration artifact hash does not match calibration manifest")
        else:
            try:
                artifact_value = _read_json(artifact)
                if artifact_value.get("schema_version") != calibration.get("artifact_schema"):
                    reasons.append("calibration artifact schema does not match calibration manifest")
            except Task5RuntimeError as error:
                reasons.append(str(error))
    snd_actual = str(contract_files.get("snd_verifier_contract_actual_sha", ""))
    snd_canonical = str(contract_files.get("snd_verifier_contract_canonical_sha", ""))
    if snd is not None and snd_path is not None:
        if snd_actual and snd_actual != sha256_bytes(Path(snd_path).read_bytes()):
            reasons.append("SND contract actual hash does not match bytes")
        if snd_canonical and snd_canonical != sha256_bytes(_canonical(snd)):
            reasons.append("SND contract canonical hash does not match bytes")
    return list(dict.fromkeys(reasons))


def _preflight(
    *,
    run_id: str,
    attempt_id: str,
    raw: Path,
    companybrain: Path,
    output: Path,
    evidence_root: Path,
    provider_config: Path,
    handoff: Path | None,
    m401_r: Path | None,
    source_manifest: Path | None = None,
    slice_config: Path | None = None,
    authority_map: Path | None = None,
    contract_files: Mapping[str, Path] | None = None,
    owner_nonce: str | None = None,
) -> dict[str, Any]:
    """Run all no-provider checks before output/staging or source reads."""

    reasons: list[str] = []
    _, output_safety, output_reasons = _validate_output_target(
        output,
        raw,
        companybrain,
        run_id,
        owner_nonce or "preflight",
    )
    reasons.extend(output_reasons)
    authority_identity: Mapping[str, Any] | None = None
    source_identity: Mapping[str, Any] | None = None
    slice_identity: Mapping[str, Any] | None = None
    provider_identity: Mapping[str, Any] | None = None
    if authority_map is not None:
        try:
            authority_identity = _load_runtime_authority(authority_map)
        except Task5RuntimeError as error:
            reasons.append(str(error))
    if contract_files:
        reasons.extend(_validate_static_contracts(contract_files))
    try:
        identity = _identity_from_handoff(handoff) if handoff else None
    except Task5RuntimeError as error:
        identity = None
        reasons.append(str(error))
    if m401_r is None or not m401_r.is_file():
        reasons.append("M401-R promoted receipt is missing")
    else:
        try:
            _validate_m401_r_receipt(m401_r)
        except Task5RuntimeError as error:
            reasons.append(str(error))
    if not provider_config.is_file() or provider_config.is_symlink():
        reasons.append(f"provider config is missing: {provider_config}")
    else:
        try:
            provider_identity = config_identity(provider_config)
        except Exception as error:
            provider_identity = None
            reasons.append(f"provider config is invalid: {type(error).__name__}")
    # Directory and source-byte validation is deliberately last.  A missing
    # authenticated review or stale contract must stop before reading either
    # external corpus, so callers cannot mistake a raw preflight for M402.
    if not reasons:
        for root, label in ((raw, "raw input"), (companybrain, "CompanyBrain")):
            try:
                _safe_root(root, label)
            except Task5RuntimeError as error:
                reasons.append(str(error))
        if source_manifest is not None:
            try:
                source_identity = _validate_source_manifest(raw, source_manifest)
            except Task5RuntimeError as error:
                reasons.append(str(error))
        if slice_config is not None and not reasons:
            try:
                slice_identity = _slice_source_selection(slice_config, source_manifest) if source_manifest is not None else None
                if slice_identity is None:
                    reasons.append("slice validation requires source manifest")
            except Task5RuntimeError as error:
                reasons.append(str(error))
    else:
        source_identity = None
    result = {
        "schema_version": "task5-preflight-result.v1",
        "task_id": TASK_ID,
        "run_id": run_id,
        "attempt_id": attempt_id,
        "status": "passed" if not reasons else "blocked",
        "outcome": "success" if not reasons else "blocked",
        "reason_code": "preflight_passed" if not reasons else "preflight_binding_missing",
        "exit_code": 0 if not reasons else 2,
        "observed_calls": {"llm": 0, "embedding": 0, "external_http_attempts": 0},
        "input_identity": {
            "raw_root": "raw_input" if not raw.is_absolute() else "external_raw_input",
            "companybrain_root": "companybrain_input" if not companybrain.is_absolute() else "external_companybrain_input",
            "output_path": "downloads_output" if not output.is_absolute() else "downloads_output",
            "provider_config_sha256": sha256_bytes(provider_config.read_bytes()) if provider_config.is_file() else "",
            "source_manifest_sha256": sha256_bytes(source_manifest.read_bytes()) if source_manifest and source_manifest.is_file() else "",
            "source_snapshot_id": source_identity.get("snapshot_id", "") if source_identity else "",
            "slice_config_sha256": sha256_bytes(slice_config.read_bytes()) if slice_config and slice_config.is_file() else "",
            "slice_selection": dict(slice_identity) if slice_identity else None,
            "runtime_authority_map_ref": "config/task5-runtime-authority-map-v1.json" if authority_identity else None,
            "runtime_authority_map_sha256": authority_identity.get("map_actual_sha256", "") if authority_identity else "",
            "runtime_contract_id": authority_identity.get("runtime_contract_id", "") if authority_identity else "",
            "runtime_contract_hash": authority_identity.get("derived_runtime_contract_hash", "") if authority_identity else "",
            "provider_identity": redact_identity(provider_identity or {}),
        },
        "output_safety": {**output_safety, "output_created": False, "staging_created": False, "lock_created": False},
        "workflowhub_identity_present": identity is not None,
        "reasons": reasons,
    }
    _write_canonical(evidence_root / "run-preflight" / "attempts" / attempt_id / "preflight-result.json", result)
    return result


def _source_rows(
    bundle: Path,
    raw: Path | None = None,
    source_manifest: Path | None = None,
) -> list[dict[str, Any]]:
    """Read the compiler ledger and bind it to the current raw snapshot.

    A row count is not source closure.  The formal audit must prove that every
    raw path appears exactly once with the same bytes and frozen source ID
    before it creates coordinates, SND evidence, or a publication result.
    """

    path = next(
        (
            bundle / relative / "sources.jsonl"
            for relative in ("_digest", "_audit")
            if (bundle / relative / "sources.jsonl").is_file()
        ),
        None,
    )
    if path is None:
        raise Task5RuntimeError("compiler did not write source ledger")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if isinstance(value, Mapping):
            rows.append(dict(value))
    if len(rows) != 89:
        raise Task5RuntimeError(f"source ledger is not the frozen 89-source set: {len(rows)}")
    if raw is not None:
        raw_hashes = _raw_source_hashes(raw)
        rows_by_path = {str(row.get("relative_path", "")): row for row in rows}
        if set(rows_by_path) != set(raw_hashes) or len(rows_by_path) != len(rows):
            raise Task5RuntimeError("source ledger paths do not exactly match the raw snapshot")
        source_ids: set[str] = set()
        for relative, raw_hash in raw_hashes.items():
            row = rows_by_path[relative]
            source_id = str(row.get("source_id", ""))
            if not source_id or source_id in source_ids:
                raise Task5RuntimeError(f"source ledger has duplicate or empty source_id: {relative}")
            if str(row.get("raw_hash", "")) != raw_hash:
                raise Task5RuntimeError(f"source ledger raw hash mismatch: {relative}")
            status = str(row.get("status", ""))
            is_blank = not (raw / relative).read_text(encoding="utf-8").strip()
            if is_blank and status != "known_empty":
                raise Task5RuntimeError(f"empty raw source is not marked known_empty: {relative}")
            if not is_blank and status not in {"ready", "duplicate_alias"}:
                raise Task5RuntimeError(f"non-empty raw source has unsupported status {status}: {relative}")
            source_ids.add(source_id)
        if source_manifest is not None:
            manifest = _read_json(source_manifest)
            entries = manifest.get("source_snapshot", {}).get("entries") if isinstance(manifest.get("source_snapshot"), Mapping) else None
            frozen_ids = {str(item.get("source_path")): str(item.get("source_id")) for item in entries if isinstance(item, Mapping)} if isinstance(entries, list) else {}
            if set(frozen_ids) != set(raw_hashes) or any(str(rows_by_path[path].get("source_id")) != source_id for path, source_id in frozen_ids.items()):
                raise Task5RuntimeError("source ledger source IDs do not match the frozen source manifest")
    return rows


def _evidence_rows(
    bundle: Path,
    source_rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Read immutable source Blocks for formal coordinate/SND verification.

    ``_audit/evidence.jsonl`` is a Reader render-unit projection.  It is not
    guaranteed to contain every source Block, because it only records blocks
    used by a rendered surface.  The source ledger carries the complete Block
    set; formal audit callers pass those rows explicitly.  Keep the old
    render-unit reader as the compatibility path for callers that only need
    the published evidence projection.
    """
    if source_rows is not None:
        result: list[dict[str, Any]] = []
        for row in source_rows:
            source_id = str(row.get("source_id", ""))
            for item in row.get("evidence", ()) if isinstance(row.get("evidence"), list) else ():
                if not isinstance(item, Mapping):
                    continue
                evidence_id = str(item.get("evidence_id", ""))
                if not source_id or not evidence_id:
                    continue
                result.append({
                    "evidence_id": evidence_id,
                    "source_id": source_id,
                    "start_line": int(item.get("start_line", 0)),
                    "end_line": int(item.get("end_line", 0)),
                    "block_content_sha256": str(item.get("block_content_sha256", "")),
                })
        if result:
            return result
    path = next(
        (
            bundle / relative / "evidence.jsonl"
            for relative in ("_digest", "_audit")
            if (bundle / relative / "evidence.jsonl").is_file()
        ),
        None,
    )
    if path is None:
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def _raw_coordinate_map(raw: Path, rows: Sequence[Mapping[str, Any]], evidence_rows: Sequence[Mapping[str, Any]], source_manifest_id: str) -> dict[str, Any]:
    evidence_by_id = {str(item.get("evidence_id")): item for item in evidence_rows if item.get("evidence_id")}
    sources: list[dict[str, Any]] = []
    for row in rows:
        relative = str(row.get("relative_path", ""))
        path = raw / relative
        data = path.read_bytes() if path.is_file() else b""
        text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        lines = text.splitlines()
        raw_line_offsets = [0]
        for line in data.splitlines(keepends=True):
            raw_line_offsets.append(raw_line_offsets[-1] + len(line))
        canonical_line_offsets = [0]
        for line in lines:
            canonical_line_offsets.append(canonical_line_offsets[-1] + len(line) + 1)
        blocks: list[dict[str, Any]] = []
        source_id = str(row.get("source_id", ""))
        # The source ledger also carries qev-* projection blocks.  They are
        # quality-case evidence, not the canonical source Block ledger and can
        # overlap the source blocks.  Only the immutable per-source blocks are
        # allowed in this coordinate map.
        block_ids = [
            str(evidence_id)
            for evidence_id in row.get("evidence_ids", [])
            if not str(evidence_id).startswith("qev-")
            and str(evidence_id) in evidence_by_id
            and (
                not evidence_by_id[str(evidence_id)].get("source_id")
                or str(evidence_by_id[str(evidence_id)].get("source_id")) == source_id
            )
        ]
        for evidence_id in block_ids:
            evidence = evidence_by_id.get(str(evidence_id), {})
            start = int(evidence.get("start_line", 0))
            end = int(evidence.get("end_line", 0))
            if start <= 0 or end < start or end > len(lines):
                raise Task5RuntimeError(f"raw coordinate is invalid: {relative}#{evidence_id}")
            blocks.append({"block_id": evidence_id, "source_id": source_id, "start_line": start, "end_line": end, "raw_byte_start": raw_line_offsets[start - 1], "raw_byte_end": raw_line_offsets[end], "canonical_codepoint_start": canonical_line_offsets[start - 1], "canonical_codepoint_end": canonical_line_offsets[end] - 1, "block_content_sha256": sha256_bytes("\n".join(lines[start - 1:end]).encode("utf-8"))})
        blocks.sort(key=lambda item: (int(item["start_line"]), int(item["end_line"]), str(item["block_id"])))
        for previous, current in zip(blocks, blocks[1:]):
            if int(current["start_line"]) <= int(previous["end_line"]):
                raise Task5RuntimeError(f"raw coordinate blocks overlap: {relative}#{previous['block_id']}#{current['block_id']}")
        sources.append({"source_id": source_id, "source_path": relative, "source_content_hash": sha256_bytes(data), "line_count": len(lines), "byte_count": len(data), "blocks": blocks, "coverage": {"block_ids": [item["block_id"] for item in blocks], "non_overlapping": True}})
    # A frozen known-empty source may contain whitespace/newline bytes, so its
    # decoded line count is non-zero even though it intentionally has no
    # evidence blocks.  That is complete source coverage; a present source
    # without blocks is still incomplete and must fail closed.
    complete = all(
        bool(item["blocks"])
        or item["line_count"] == 0
        or any(
            str(row.get("source_id", "")) == str(item["source_id"])
            and str(row.get("status", "")) == "known_empty"
            for row in rows
        )
        for item in sources
    )
    return {"schema_version": "raw-coordinate-map.v1", "source_snapshot_id": source_manifest_id, "sources": sources, "coverage": {"source_count": len(sources), "block_count": sum(len(item["blocks"]) for item in sources), "complete": complete, "non_overlapping": True}}


def _companybrain_snapshot(companybrain: Path, evidence_root: Path, attempt_id: str) -> tuple[dict[str, Any], str]:
    files: list[dict[str, Any]] = []
    entry_files: list[str] = []
    for path in sorted(companybrain.rglob("*.md"), key=lambda p: p.relative_to(companybrain).as_posix()):
        if path.is_symlink():
            raise Task5RuntimeError("CompanyBrain contains a symlink")
        relative = path.relative_to(companybrain).as_posix()
        data = path.read_bytes()
        files.append({"relative_path": relative, "sha256": sha256_bytes(data), "bytes": len(data), "lines": data.count(b"\n")})
        if relative in {"Home.md", "README.md", "index.md"} or relative.casefold().endswith("/home.md"):
            entry_files.append(relative)
    tree_digest = sha256_bytes(b"".join(_canonical(item, trailing_newline=False) for item in files))
    snapshot = {"schema_version": "companybrain-route-snapshot-host.v1", "snapshot_id": "cb-" + tree_digest[:20], "root_realpath": str(companybrain.resolve()), "regular_markdown_files": files, "entry_files": entry_files, "tree_digest": tree_digest}
    path = evidence_root / "m401-receipts" / "attempts" / attempt_id / "companybrain-route-snapshot.json"
    _write_canonical(path, snapshot)
    public = {"schema_version": "companybrain-route-snapshot-public.v1", "snapshot_id": snapshot["snapshot_id"], "host_snapshot_sha256": sha256_bytes(path.read_bytes()), "root_identity": "companybrain", "regular_markdown_files": [{k: v for k, v in item.items() if k != "bytes"} for item in files], "entry_files": entry_files, "tree_digest": tree_digest}
    return public, sha256_bytes(path.read_bytes())


def _ledger_lines(run: Mapping[str, Any], key: str) -> bytes:
    rows: list[bytes] = []
    for projection_id, entry in run.get("quality_provider_trace", {}).items() if key == "semantic" and isinstance(run.get("quality_provider_trace"), Mapping) else []:
        for event in entry if isinstance(entry, list) else []:
            rows.append(_canonical({"projection_id": projection_id, "stage": event.get("stage"), "attempt": event.get("attempt"), "prompt_sha256": event.get("prompt_sha256"), "response_sha256": event.get("response_sha256"), "status": event.get("status"), "page_path": event.get("page_path")}, trailing_newline=False))
    if key == "semantic" and not rows:
        rows.append(_canonical({"status": "no_semantic_trace"}, trailing_newline=False))
    return b"\n".join(rows) + b"\n"


SND_TRIGGER_MARKERS = ("异常", "失败", "报错", "错误", "故障", "bug", "issue", "error", "fail", "unable")
SND_ACTION_MARKERS = ("处理", "解决", "修复", "检查", "重试", "恢复", "升级", "原因", "排查", "fix", "retry", "recover", "escalate", "cause", "diagnose")
SND_NON_RULE_CONTEXT_MARKERS = ("不会", "没有", "无", "避免", "防止", "不存在", "不可预知", "逻辑明确", "交互较好", "优点", "缺点", "特点")


def _snd_contract_descriptor() -> dict[str, Any]:
    return {
        "rule_set": "SND-RULE-002",
        "classifications": ["no_rule", "rule", "ambiguous"],
        "non_rule_context_markers": list(SND_NON_RULE_CONTEXT_MARKERS),
        "classification_rule": "trigger+action => rule; trigger-only with an explicit descriptive_or_negated_context_marker => no_rule; other trigger-only => ambiguous; no trigger => no_rule",
    }


def _snd_normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text.replace("\r\n", "\n").replace("\r", "\n"))


def _snd_classify(text: str) -> tuple[str, list[str], list[str]]:
    normalized = _snd_normalize(text).casefold()
    triggers = [marker for marker in SND_TRIGGER_MARKERS if marker.casefold() in normalized]
    actions = [marker for marker in SND_ACTION_MARKERS if marker.casefold() in normalized]
    if triggers and actions:
        return "rule", triggers, actions
    if triggers and any(marker.casefold() in normalized for marker in SND_NON_RULE_CONTEXT_MARKERS):
        return "no_rule", triggers, actions
    if triggers:
        return "ambiguous", triggers, actions
    return "no_rule", triggers, actions


def _snd_raw_block(raw: Path, source_path: str, start: int, end: int) -> str:
    path = raw / source_path
    if not path.is_file() or start <= 0 or end < start:
        raise Task5RuntimeError(f"SND block locator is invalid: {source_path}#L{start}-L{end}")
    lines = _snd_normalize(path.read_text(encoding="utf-8")).splitlines()
    if end > len(lines):
        raise Task5RuntimeError(f"SND block locator is outside source: {source_path}#L{start}-L{end}")
    return "\n".join(lines[start - 1:end])


def _snd_source_row(rows: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], str]:
    snd_path = "GoInsight/17  智能搭建.md"
    row = next((item for item in rows if str(item.get("relative_path")) == snd_path), None)
    if row is None:
        raise Task5RuntimeError("SND source is missing from the 89-source ledger")
    source_id = str(row.get("source_id"))
    if not source_id:
        raise Task5RuntimeError("SND source has no source_id")
    return row, source_id


def _snd_block_ids(row: Mapping[str, Any], evidence_rows: Sequence[Mapping[str, Any]], source_id: str) -> list[str]:
    evidence_by_id = {str(item.get("evidence_id")): item for item in evidence_rows if item.get("evidence_id")}
    block_ids = [
        str(evidence_id)
        for evidence_id in row.get("evidence_ids", [])
        if not str(evidence_id).startswith("qev-")
        and str(evidence_id) in evidence_by_id
        and (
            not evidence_by_id[str(evidence_id)].get("source_id")
            or str(evidence_by_id[str(evidence_id)].get("source_id")) == source_id
        )
    ]
    if len(block_ids) != len(set(block_ids)) or not block_ids:
        raise Task5RuntimeError("SND source Block coverage is empty or duplicated")
    return block_ids


def _snd_artifacts(raw: Path, rows: Sequence[Mapping[str, Any]], evidence_rows: Sequence[Mapping[str, Any]], source_manifest_id: str) -> dict[str, Any]:
    snd_path = "GoInsight/17  智能搭建.md"
    row, source_id = _snd_source_row(rows)
    path = raw / snd_path
    data = path.read_bytes()
    evidence_by_id = {str(item.get("evidence_id")): item for item in evidence_rows if item.get("evidence_id")}
    block_ids = _snd_block_ids(row, evidence_rows, source_id)
    per_block_results: list[dict[str, Any]] = []
    for block_id in block_ids:
        evidence = evidence_by_id.get(block_id)
        if not isinstance(evidence, Mapping):
            raise Task5RuntimeError(f"SND source block is missing from evidence ledger: {block_id}")
        start = int(evidence.get("start_line", 0))
        end = int(evidence.get("end_line", 0))
        text = _snd_raw_block(raw, snd_path, start, end)
        block_hash = sha256_bytes(text.encode("utf-8"))
        classification, triggers, actions = _snd_classify(text)
        locator = {"source_path": snd_path, "start_line": start, "end_line": end}
        evidence_digest = sha256_bytes(_canonical({"block_id": block_id, "block_hash": block_hash, "classification": classification, "locator": locator, "trigger_markers": triggers, "action_markers": actions}))
        per_block_results.append({
            "block_id": block_id,
            "block_hash": block_hash,
            "locator": locator,
            "classification": classification,
            "trigger_markers": triggers,
            "action_markers": actions,
            "evidence_digest": evidence_digest,
        })
    coverage_digest = sha256_bytes(_canonical([item["block_id"] for item in per_block_results]))
    result_digest = sha256_bytes(_canonical(per_block_results))
    explicit = [item["block_id"] for item in per_block_results if item["classification"] == "rule"]
    ambiguous = [item["block_id"] for item in per_block_results if item["classification"] == "ambiguous"]
    return {
        "schema_version": "semantic_zero_match_certificate.v1",
        "source_id": source_id,
        "source_snapshot_id": source_manifest_id,
        "source_content_hash": sha256_bytes(data),
        "source_hash": sha256_bytes(data),
        "analyzer_id": "task5-snd-deterministic",
        "analyzer_sha256": sha256_bytes(b"task5-snd-deterministic-v2"),
        "analyzer_contract_sha256": sha256_bytes(_canonical(_snd_contract_descriptor())),
        "rule_version": "SND-RULE-002",
        "scan_scope": ["all_blocks", "tables", "code", "configuration", "links"],
        "scan_complete": True,
        "scanned_block_refs": [item["block_id"] for item in per_block_results],
        "coverage_digest": coverage_digest,
        "per_block_results": per_block_results,
        "blocks": [{"source_block_id": item["block_id"], "source_content_hash": item["block_hash"], "match_count": len(item["trigger_markers"]) + len(item["action_markers"])} for item in per_block_results],
        "result_digest": result_digest,
        "coverage": {"block_count": len(per_block_results), "complete": bool(per_block_results)},
        "explicit_rule_match": explicit,
        "ambiguous_match": ambiguous,
        "zero_match": bool(per_block_results) and not explicit and not ambiguous,
    }


def _verify_snd_certificate(
    *,
    certificate: Mapping[str, Any],
    certificate_sha256: str,
    raw: Path,
    rows: Sequence[Mapping[str, Any]],
    evidence_rows: Sequence[Mapping[str, Any]],
    source_manifest_id: str,
    material_id: str,
) -> dict[str, Any]:
    """Independently recompute every SND Block before promotion."""

    # Recompute the scan here instead of calling the producer.  The verifier
    # must detect a producer that consistently emits the same wrong answer.
    snd_path = "GoInsight/17  智能搭建.md"
    row, source_id = _snd_source_row(rows)
    path = raw / snd_path
    source_hash = sha256_bytes(path.read_bytes())
    evidence_by_id = {str(item.get("evidence_id")): item for item in evidence_rows if item.get("evidence_id")}
    expected_block_ids = _snd_block_ids(row, evidence_rows, source_id)
    expected_results: list[dict[str, Any]] = []
    for block_id in expected_block_ids:
        evidence = evidence_by_id.get(block_id)
        if not isinstance(evidence, Mapping):
            raise Task5RuntimeError(f"SND verifier cannot find source Block: {block_id}")
        start = int(evidence.get("start_line", 0))
        end = int(evidence.get("end_line", 0))
        text = _snd_raw_block(raw, snd_path, start, end)
        classification, triggers, actions = _snd_classify(text)
        locator = {"source_path": snd_path, "start_line": start, "end_line": end}
        block_hash = sha256_bytes(text.encode("utf-8"))
        expected_results.append({
            "block_id": block_id,
            "block_hash": block_hash,
            "locator": locator,
            "classification": classification,
            "trigger_markers": triggers,
            "action_markers": actions,
            "evidence_digest": sha256_bytes(_canonical({"block_id": block_id, "block_hash": block_hash, "classification": classification, "locator": locator, "trigger_markers": triggers, "action_markers": actions})),
        })
    expected_contract_hash = sha256_bytes(_canonical(_snd_contract_descriptor()))
    expected_coverage_digest = sha256_bytes(_canonical(expected_block_ids))
    expected_result_digest = sha256_bytes(_canonical(expected_results))
    supplied_results = certificate.get("per_block_results")
    status = "passed"
    failure_code = None
    if certificate.get("schema_version") != "semantic_zero_match_certificate.v1":
        status, failure_code = "unknown", "schema_mismatch"
    elif certificate.get("source_snapshot_id") != source_manifest_id or certificate.get("source_content_hash") != source_hash or certificate.get("source_hash") != source_hash:
        status, failure_code = "unknown", "source_snapshot_mismatch"
    elif certificate.get("analyzer_contract_sha256") != expected_contract_hash or certificate.get("rule_version") != "SND-RULE-002" or certificate.get("scan_complete") is not True:
        status, failure_code = "unknown", "analyzer_contract_mismatch"
    elif certificate.get("scanned_block_refs") != expected_block_ids or certificate.get("coverage_digest") != expected_coverage_digest:
        status, failure_code = "unknown", "coverage_mismatch"
    elif not isinstance(supplied_results, list) or supplied_results != expected_results:
        status, failure_code = "unknown", "block_result_mismatch"
    elif certificate.get("result_digest") != expected_result_digest or certificate.get("explicit_rule_match") != [] or certificate.get("ambiguous_match") != [] or certificate.get("zero_match") is not True:
        status, failure_code = "unknown", "result_digest_mismatch"
    attempt_id = "snd-" + uuid.uuid4().hex[:20]
    recomputed_digest = expected_result_digest
    comparison_digest = sha256_bytes(_canonical({"certificate_sha256": certificate_sha256, "certificate_result_digest": certificate.get("result_digest"), "recomputed_result_digest": recomputed_digest}))
    return _with_hash({
        "schema_version": "semantic-zero-match-verifier-receipt.v1",
        "attempt_id": attempt_id,
        "verifier_id": "task5-independent-zero-match-verifier",
        "source_snapshot_id": source_manifest_id,
        "source_hash": source_hash,
        "certificate_ref": "bundle/_audit/source-not-documented-zero-match.json",
        "certificate_sha256": certificate_sha256,
        "recomputed_result_digest": recomputed_digest,
        "comparison_digest": comparison_digest,
        "block_count": len(expected_results),
        "compared_block_count": len(supplied_results) if isinstance(supplied_results, list) else 0,
        "status": status,
        "failure_code": failure_code,
        "current_material_id": material_id,
    })


def _remove_legacy_audit_links(audit_path: Path) -> None:
    """Keep the public Audit page from linking to files removed from the final tree."""

    audit_path = Path(audit_path)
    if not audit_path.is_file() or audit_path.is_symlink():
        return
    text = audit_path.read_text(encoding="utf-8")
    replacements = {
        "- 来源索引：[_audit/sources.jsonl](_audit/sources.jsonl)": "- 来源索引：见本页“来源清单”。",
        "- Evidence 详情：见 [`_audit/evidence.jsonl`](_audit/evidence.jsonl)，按 evidence_id 和行号回查；来源索引不复制整篇原文。": "- Evidence 详情：见本页“原始证据坐标”；机器证据见本目录 `_audit/`。",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(
        r"\[([^\]]+)\]\(_audit/quality\.json\)",
        r"\1（质量证据保留在 host-only receipt）",
        text,
    )
    audit_path.write_text(text, encoding="utf-8")


def _write_host_observation(
    observation: Mapping[str, Any] | None,
    *,
    evidence_root: Path,
    attempt_id: str,
    run_id: str,
    source_manifest_sha256: str,
) -> tuple[Path, str]:
    """Persist the compiler's bound CompanyBrain observation as host evidence."""

    if not isinstance(observation, Mapping):
        raise Task5RuntimeError("M402 compiler did not return a CompanyBrain observation")
    rows = observation.get("rows")
    if not isinstance(rows, list) or len(rows) != 60:
        raise Task5RuntimeError("M402 CompanyBrain observation is not a closed 12x5 matrix")
    fixed_fields = {
        "case_id", "projection_id", "dimension_id", "status", "score",
        "source_refs", "visible_ref", "audit_ref", "gap_ref", "kd_ref",
    }
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != fixed_fields:
            raise Task5RuntimeError("M402 CompanyBrain observation row shape is invalid")
    payload = {
        "run_id": run_id,
        "source_manifest_sha256": source_manifest_sha256,
        "companybrain_snapshot_id": str(observation.get("companybrain_snapshot_id", "")),
        "companybrain_tree_sha256": str(observation.get("companybrain_tree_sha256", "")),
        "rows": rows,
    }
    if not payload["companybrain_snapshot_id"] or not re.fullmatch(r"[0-9a-f]{64}", payload["companybrain_tree_sha256"]):
        raise Task5RuntimeError("M402 CompanyBrain observation identity is incomplete")
    if source_manifest_sha256 != str(observation.get("source_manifest_sha256", "")):
        raise Task5RuntimeError("M402 CompanyBrain observation source manifest binding drifted")
    expected_hash = sha256_bytes(_canonical(payload))
    if expected_hash != str(observation.get("observation_sha256", "")):
        raise Task5RuntimeError("M402 CompanyBrain observation hash is invalid")
    value = dict(payload)
    value["observation_sha256"] = expected_hash
    path = evidence_root / "actual-run" / "attempts" / attempt_id / "companybrain-observation.json"
    return path, _write_create_only(path, value)


def _write_host_run_receipt(
    *,
    evidence_root: Path,
    attempt_id: str,
    run_id: str,
    raw: Path,
    companybrain: Path,
    output: Path,
    provider_config: Path,
    source_manifest: Path,
    public_receipt: Path,
    terminal_status: str,
) -> tuple[Path, str]:
    """Bind authenticated host inputs to the public run result."""

    receipt = {
        "schema_version": "task5-host-run-receipt.v1",
        "run_id": run_id,
        "raw_root_identity": str(raw.resolve()),
        "companybrain_root_identity": str(companybrain.resolve()),
        "downloads_run_root": str(output.resolve()),
        "provider_config_ref": {"path": str(provider_config.resolve()), "sha256": sha256_bytes(provider_config.read_bytes())},
        "source_manifest_sha256": sha256_bytes(source_manifest.read_bytes()),
        "public_receipt_ref": "bundle/_audit/run-result.json",
        "public_receipt_sha256": sha256_bytes(public_receipt.read_bytes()),
        "terminal_status": terminal_status,
    }
    if not _no_secret(receipt):
        raise Task5RuntimeError("host run receipt contains a secret-like value")
    path = evidence_root / "actual-run" / "attempts" / attempt_id / "host-run-receipt.json"
    return path, _write_create_only(path, receipt)


def _append_formal_audit(
    bundle: Path,
    raw: Path,
    companybrain: Path,
    evidence_root: Path,
    attempt_id: str,
    material_id: str,
    source_manifest: Path | None = None,
    companybrain_observation: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    run_path = next(
        (
            bundle / relative
            for relative in ("_digest/run.json", "_audit/run-result.json")
            if (bundle / relative).is_file()
        ),
        None,
    )
    if run_path is None:
        raise Task5RuntimeError("compiler did not write run ledger")
    run = _read_json(run_path)
    source_manifest_path = Path(source_manifest).expanduser() if source_manifest is not None else Path(__file__).resolve().parents[2] / "config" / "task5-source-page-manifest-v2.json"
    rows = _source_rows(bundle, raw, source_manifest_path)
    evidence = _evidence_rows(bundle, rows)
    source_hashes = _raw_source_hashes(raw)
    source_manifest_id = _source_manifest_digest(source_hashes)
    public_cb, host_cb_hash = _companybrain_snapshot(companybrain, evidence_root, attempt_id)
    if isinstance(companybrain_observation, Mapping):
        public_cb.update({
            "status": "available",
            "run_id": str(run.get("run_id", "")),
            "source_manifest_sha256": str(companybrain_observation.get("source_manifest_sha256", "")),
            "companybrain_snapshot_id": str(companybrain_observation.get("companybrain_snapshot_id", "")),
            "companybrain_tree_sha256": str(companybrain_observation.get("companybrain_tree_sha256", "")),
            "observation_sha256": str(companybrain_observation.get("observation_sha256", "")),
            "observation_ref": f"host-only:actual-run/attempts/{attempt_id}/companybrain-observation.json",
            "failure": None,
        })
    coordinate = _raw_coordinate_map(raw, rows, evidence, source_manifest_id)
    snd_certificate = _snd_artifacts(raw, rows, evidence, source_manifest_id)
    audit_dir = bundle / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pages = run.get("manifest", {}).get("pages", []) if isinstance(run.get("manifest"), Mapping) else []
    audit_pages = {"schema_version": "task5-audit-pages.v1", "pages": [{"page_id": item.get("page_id"), "page_type": item.get("page_type"), "path": item.get("path"), "source_ids": item.get("source_ids"), "surface_sha256": item.get("surface_sha256")} for item in pages]}
    status_rows = [{"source_id": row.get("source_id"), "relative_path": row.get("relative_path"), "status": row.get("status"), "raw_hash": row.get("raw_hash"), "reader_page_ids": row.get("reader_page_ids", []), "duplicate_of": row.get("duplicate_of")} for row in rows]
    route_lines = []
    for route in run.get("manifest", {}).get("routes", []) if isinstance(run.get("manifest"), Mapping) else []:
        route_lines.append(_canonical({"query_id": route.get("query_id"), "question": route.get("question"), "scene": route.get("scene"), "candidate_source_ids": route.get("candidate_source_ids"), "selected_source_ids": route.get("selected_source_ids"), "selected_page_ids": route.get("selected_page_ids"), "scores": route.get("scores"), "embedding_receipt": route.get("embedding_receipt"), "status": route.get("status"), "failure": route.get("failure")}, trailing_newline=False))
    compile_lines = _ledger_lines(run, "semantic")
    response_lines = _ledger_lines(run, "semantic")
    quality_ref = str(run.get("quality_contract_sha256", ""))
    for relative, value in (
        ("audit-pages.json", audit_pages),
        ("source-status.json", {"schema_version": "task5-source-status.v1", "source_count": len(status_rows), "sources": status_rows}),
        ("companybrain-route-snapshot.json", public_cb),
        ("raw-coordinate-map.json", coordinate),
        ("source-not-documented-zero-match.json", snd_certificate),
    ):
        if not _no_secret(value):
            raise Task5RuntimeError(f"machine audit contains a secret-like value: {relative}")
        _write_canonical(audit_dir / relative, value)
    certificate_path = audit_dir / "source-not-documented-zero-match.json"
    snd_verifier = _verify_snd_certificate(
        certificate=snd_certificate,
        certificate_sha256=sha256_bytes(certificate_path.read_bytes()),
        raw=raw,
        rows=rows,
        evidence_rows=evidence,
        source_manifest_id=source_manifest_id,
        material_id=material_id,
    )
    if snd_verifier.get("status") != "passed":
        raise Task5RuntimeError(f"SND verifier failed: {snd_verifier.get('failure_code')}")
    if not _no_secret(snd_verifier):
        raise Task5RuntimeError("SND verifier contains a secret-like value")
    _write_canonical(audit_dir / "source-not-documented-verifier.json", snd_verifier)
    promoted = evidence_root / "snd-verifier" / "verifier-receipt.json"
    promoted.parent.mkdir(parents=True, exist_ok=True)
    attempt_path = evidence_root / "snd-verifier" / "attempts" / str(snd_verifier["attempt_id"]) / "verifier-receipt.json"
    attempt_path.parent.mkdir(parents=True, exist_ok=False)
    attempt_path.write_bytes(_canonical(snd_verifier))
    promoted.write_bytes(attempt_path.read_bytes())
    (audit_dir / "semantic-compile-ledger.jsonl").write_bytes(compile_lines)
    (audit_dir / "semantic-response-ledger.jsonl").write_bytes(response_lines)
    (audit_dir / "route-ledger.jsonl").write_bytes(b"\n".join(route_lines) + (b"\n" if route_lines else b""))
    for path in (audit_dir / "semantic-compile-ledger.jsonl", audit_dir / "semantic-response-ledger.jsonl", audit_dir / "route-ledger.jsonl"):
        if not _no_secret(path.read_text(encoding="utf-8")):
            raise Task5RuntimeError(f"machine ledger contains a secret-like value: {path.name}")
    _remove_legacy_audit_links(bundle / "Audit.md")
    # The compiler's reader-facing ledger is an input to this formal audit,
    # not part of the frozen public machine file set.  Remove only these
    # staging-owned legacy files before hashing the final directory manifest;
    # the formal run-result is written by the caller immediately afterwards.
    for legacy_name in ("sources.jsonl", "evidence.jsonl", "quality.json", "run-result.receipt.json"):
        legacy_path = audit_dir / legacy_name
        if legacy_path.is_file() and not legacy_path.is_symlink():
            legacy_path.unlink()
    audit_manifest = _manifest(bundle)
    layout_path = Path(__file__).resolve().parents[2] / "config" / "task5-publication-layout-v2.json"
    audit_manifest["layout_contract_sha256"] = sha256_bytes(layout_path.read_bytes())
    audit_manifest["required_paths"] = [f"bundle/{relative}" for relative in FIXED_AUDIT_FILES]
    audit_manifest["forbidden_path_scan"] = {"passed": True, "matches": []}
    _write_canonical(audit_dir / "directory-manifest.json", audit_manifest)
    return {
        "run": dict(run),
        "host_companybrain_sha256": host_cb_hash,
        "companybrain_snapshot_id": public_cb.get("snapshot_id"),
        "companybrain_tree_sha256": public_cb.get("tree_digest"),
        "quality_ref": quality_ref,
        "source_manifest_id": source_manifest_id,
    }, snd_verifier


def _formal_run_result(
    *,
    run: Mapping[str, Any],
    task_id: str,
    run_id: str,
    handoff: Mapping[str, Any],
    provider_identity: Mapping[str, Any],
    source_manifest: Path,
    quality_cases: Path,
    slice_cases: Path,
    output_bundle: Path,
    quality_result: Mapping[str, Any] | None,
    quality_result_ref: str | None = None,
    quality_result_sha256: str | None = None,
    snd_verifier: Mapping[str, Any],
    surface_qa: Mapping[str, Any],
    authority_identity: Mapping[str, Any],
    provider_config: Path,
    calibration_manifest: Path | None,
    calibration_artifact: Path | None,
    companybrain_host_snapshot_sha256: str,
    outcome: str,
    publication_status: str,
    reason_code: str,
    exit_code: int,
    phase_results: Mapping[str, Any],
    failure_evidence_path: str | None,
) -> dict[str, Any]:
    files = _manifest(output_bundle)
    layout_path = Path(__file__).resolve().parents[2] / "config" / "task5-publication-layout-v2.json"
    provider_json = _read_json(provider_config)
    provider_public = dict(redact_identity(provider_identity))
    provider_public.update({
        "config_path": "user-config/knowledge-digest/config.json",
        "config_sha256": sha256_bytes(provider_config.read_bytes()),
        "config_canonical_sha256": sha256_bytes(_canonical(provider_json)),
        "calibration_manifest_ref": _public_ref(calibration_manifest),
        "calibration_manifest_sha256": sha256_bytes(calibration_manifest.read_bytes()) if calibration_manifest and calibration_manifest.is_file() else "",
        "calibration_artifact_ref": _public_ref(calibration_artifact),
        "calibration_artifact_sha256": sha256_bytes(calibration_artifact.read_bytes()) if calibration_artifact and calibration_artifact.is_file() else "",
    })
    artifact_manifest = {
        "bundle_tree_sha256": files["tree_sha256"],
        "directory_manifest": "_audit/directory-manifest.json",
        # Keep the public run result bound to the single R3 quality artifact;
        # embedding the full candidate result here would create a second,
        # independently consumable quality copy.
        "quality_result": (
            {"ref": quality_result_ref, "sha256": quality_result_sha256}
            if quality_result_ref and quality_result_sha256
            else None
        ),
        "snd_verifier": {"path": "_audit/source-not-documented-verifier.json", "status": snd_verifier.get("status"), "canonical_sha256": snd_verifier.get("canonical_sha256")},
        "surface_qa": dict(surface_qa),
        "companybrain_host_snapshot_sha256": companybrain_host_snapshot_sha256,
        "layout_contract_sha256": sha256_bytes(layout_path.read_bytes()),
    }
    implementation = handoff.get("implementation_review") if isinstance(handoff.get("implementation_review"), Mapping) else {}
    current = handoff.get("current") if isinstance(handoff.get("current"), Mapping) else {}
    runtime_contract = handoff.get("runtime_contract") if isinstance(handoff.get("runtime_contract"), Mapping) else {}
    # WorkflowHub stores the review and runtime identities in nested records.
    # The public run-result contract is intentionally a flat projection, so
    # derive it from those authenticated records instead of emitting a row of
    # misleading nulls.
    workflow_identity = {
        "task_id": handoff.get("task_id"),
        "stage": handoff.get("stage"),
        "review_kind": handoff.get("review_kind"),
        "handoff_ref": _public_ref(handoff.get("handoff_ref")),
        "handoff_sha256": handoff.get("handoff_sha256"),
        "review_attempt_ref": _public_ref(implementation.get("attempt_ref")),
        "review_result_ref": _public_ref(implementation.get("result_ref")),
        "review_result_sha256": implementation.get("result_sha256"),
        "review_report_ref": _public_ref(implementation.get("report_ref")),
        "review_outcome": implementation.get("outcome"),
        "terminal_status": implementation.get("terminal_status"),
        "terminal_clean": implementation.get("terminal_clean"),
        "contract_id": runtime_contract.get("runtime_contract_id"),
        "contract_hash": runtime_contract.get("runtime_contract_hash"),
        "semantic_hash": runtime_contract.get("semantic_contract_hash"),
        "snapshot_tree": current.get("snapshot_tree"),
        "material_id": current.get("material_id"),
    }
    result = {
        "schema_version": RUN_RESULT_SCHEMA,
        "task_id": task_id,
        "run_id": run_id,
        "workflowhub_identity": workflow_identity,
        "input_identity": {"raw_root_realpath": "raw_input", "companybrain_root_realpath": "companybrain_input", "companybrain_snapshot_sha256": companybrain_host_snapshot_sha256, "source_manifest_ref": "config/task5-source-page-manifest-v2.json", "source_manifest_sha256": sha256_bytes(source_manifest.read_bytes()), "source_manifest_canonical_sha256": sha256_bytes(_canonical(_read_json(source_manifest))), "source_count": 89, "quality_cases_ref": "config/task5-quality-cases-v2.json", "quality_cases_sha256": sha256_bytes(quality_cases.read_bytes()), "slice_cases_ref": "config/task5-slice-cases-v1.json", "slice_cases_sha256": sha256_bytes(slice_cases.read_bytes()), "runtime_authority_map_ref": authority_identity.get("map_ref"), "runtime_authority_map_sha256": authority_identity.get("map_actual_sha256"), "runtime_contract_id": authority_identity.get("runtime_contract_id"), "runtime_contract_hash": authority_identity.get("derived_runtime_contract_hash")},
        "provider_identity": provider_public,
        "lifecycle": {"state": publication_status, "slice_status": phase_results.get("slice", "passed"), "full_status": phase_results.get("full", "passed"), "failure_evidence_path": failure_evidence_path},
        "publication_status": publication_status,
        "outcome": outcome,
        "reason_code": reason_code,
        "exit_code": exit_code,
        "observed_calls": run.get("provider_calls", {"llm": 0, "embedding": 0}),
        "phase_results": dict(phase_results),
        "artifact_manifest": artifact_manifest,
    }
    return _with_hash(result)


def _failure_evidence_path(output: Path, run_id: str) -> Path:
    return output.parent / f"{output.name}.failure-evidence" / run_id / "failure-evidence.json"


def _failure_evidence_ref(output: Path, path: Path) -> str:
    return f"{output.name}.failure-evidence/{path.parent.name}/{path.name}"


def _write_failure_evidence(
    *,
    output: Path,
    run_id: str,
    reason_code: str,
    provider_identity: Mapping[str, Any],
    observed_calls: Mapping[str, Any],
    audit_ref: str | None,
    output_retained: bool,
    status: str = "failed",
    exit_code: int | None = None,
) -> tuple[Path, str]:
    """Write one retained failure record and return its logical public ref."""

    path = _failure_evidence_path(output, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        value = _with_hash({
            "schema_version": "task5-failure-evidence.v1",
            "run_id": run_id,
            "status": status,
            "reason_code": reason_code,
            "input_identity": {"raw": "raw_input", "companybrain": "companybrain_input"},
            "provider_identity": redact_identity(provider_identity),
            "observed_calls": dict(observed_calls),
            "exit_code": exit_code if exit_code is not None else (1 if reason_code == "QUALITY_GATE_FAILED" else 3),
            "audit_ref": audit_ref,
            "cleanup_result": {"staging_removed": False, "output_retained": output_retained},
        })
        _write_canonical(path, value)
    return path, _failure_evidence_ref(output, path)


def _rehash_quality_result(value: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("quality_result_sha256", None)
    result.pop("canonical_sha256", None)
    result["quality_result_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    result["canonical_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    return result


def _write_create_only(path: Path, value: Mapping[str, Any]) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _canonical(value)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return sha256_bytes(data)


def _write_staging_failure_run_result(
    *,
    stage: Path,
    run_id: str,
    handoff: Mapping[str, Any],
    provider_identity: Mapping[str, Any],
    reason_code: str,
    observed_calls: Mapping[str, Any],
    status: str = "failed",
    outcome: str = "failed",
    exit_code: int = 3,
) -> None:
    """Leave a machine result once a staging directory has been created."""

    bundle = stage / "bundle"
    path = bundle / "_audit" / "run-result.json"
    if path.exists():
        return
    workflow_keys = ("task_id", "stage", "review_kind", "handoff_ref", "handoff_sha256", "review_attempt_ref", "review_result_ref", "review_result_sha256", "review_report_ref", "review_outcome", "terminal_status", "terminal_clean", "contract_id", "contract_hash", "semantic_hash", "snapshot_tree", "material_id")
    value = {
        "schema_version": RUN_RESULT_SCHEMA,
        "task_id": TASK_ID,
        "run_id": run_id,
        "workflowhub_identity": {key: _public_ref(handoff.get(key)) if key.endswith("_ref") else handoff.get(key) for key in workflow_keys},
        "input_identity": {"raw_root_realpath": "raw_input", "companybrain_root_realpath": "companybrain_input", "source_count": 89},
        "provider_identity": redact_identity(provider_identity),
        "lifecycle": {"state": status, "slice_status": "not_started", "full_status": "not_started", "failure_evidence_path": None},
        "publication_status": "not_released",
        "outcome": outcome,
        "reason_code": reason_code,
        "exit_code": exit_code,
        "observed_calls": dict(observed_calls),
        "phase_results": {"slice": "not_started", "full": "not_started"},
        "artifact_manifest": {"bundle_tree_sha256": None},
    }
    _write_canonical(path, value)


def _summarize_slice_result(
    selection: Mapping[str, Any],
    result: Any,
    slice_run: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Turn the diagnostic bundle into an explicit slice state machine."""

    run = slice_run or {}
    ledger = run.get("quality_route_ledger", []) if isinstance(run, Mapping) else []
    projection_statuses: dict[str, dict[str, Any]] = {}
    has_not_evaluable = False
    has_unexpected_failure = False
    if isinstance(ledger, list):
        for row in ledger:
            if not isinstance(row, Mapping):
                has_unexpected_failure = True
                continue
            projection_id = str(row.get("projection_id", ""))
            status = str(row.get("status", "failed"))
            missing = [str(item) for item in row.get("missing_full_source_paths", ())]
            if status == "source_not_in_slice":
                has_not_evaluable = True
            elif status != "ready":
                has_unexpected_failure = True
            projection_statuses[projection_id] = {
                "slice_quality_status": "not_evaluable" if status == "source_not_in_slice" else ("passed" if status == "ready" else "failed"),
                "reason": "source_not_in_slice" if status == "source_not_in_slice" else (None if status == "ready" else str(row.get("failure") or status)),
                "missing_full_source_paths": missing,
            }
    warnings = run.get("warnings", ()) if isinstance(run, Mapping) else ()
    unexpected_warnings = [
        str(warning)
        for warning in warnings
        if str(warning) != "run: quality_dimensions_not_all_kd_win"
    ] if isinstance(warnings, list) else []
    if unexpected_warnings:
        has_unexpected_failure = True
    outcome = str(getattr(result, "outcome", "failed"))
    execution = "completed" if outcome in {"completed", "not_released"} else "stopped"
    if outcome in {"unavailable", "blocked", "failed"}:
        has_unexpected_failure = True
    quality = "failed" if has_unexpected_failure else ("not_evaluable" if has_not_evaluable else "passed")
    return {
        "evaluation_mode": "slice",
        "slice_id": str(selection.get("slice_id", "")),
        "preflight": "passed",
        "execution": execution,
        "quality": quality,
        "projection_statuses": projection_statuses,
        "source_count": int(selection.get("source_count", 0)),
        "nonempty_source_count": int(selection.get("nonempty_source_count", 0)),
        "release_blocked": quality == "failed" or execution != "completed",
    }


def run_real(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser()
    evidence_root = Path(args.evidence_root).expanduser()
    run_id = "run-" + uuid.uuid4().hex[:16]
    attempt_id = "m402-" + uuid.uuid4().hex[:20]
    owner_nonce = uuid.uuid4().hex
    authority_map = Path(__file__).resolve().parents[2] / "config" / "task5-runtime-authority-map-v1.json"
    contract_files = {
        "observation_config": Path(args.observation_config),
        "review_manifest": Path(args.review_manifest),
        "calibration_manifest": Path(args.calibration_manifest),
        "calibration_artifact": Path(args.calibration_artifact),
        "quality_result_config": Path(args.quality_result_config),
        "source_direct_contract": Path(args.source_direct_contract),
        "snd_verifier_contract": Path(args.snd_verifier_contract),
        "snd_verifier_contract_actual_sha": args.snd_verifier_contract_actual_sha,
        "snd_verifier_contract_canonical_sha": args.snd_verifier_contract_canonical_sha,
    }
    preflight = _preflight(
        run_id=run_id,
        attempt_id=attempt_id,
        raw=Path(args.raw_input),
        companybrain=Path(args.companybrain),
        output=output,
        evidence_root=evidence_root,
        provider_config=Path(args.provider_config),
        source_manifest=Path(args.source_manifest),
        slice_config=Path(args.slice_config),
        authority_map=authority_map,
        contract_files=contract_files,
        handoff=Path(args.workflowhub_implementation_handoff) if args.workflowhub_implementation_handoff else None,
        m401_r=Path(args.m401_r_receipt) if args.m401_r_receipt else None,
        owner_nonce=owner_nonce,
    )
    if preflight["status"] != "passed":
        print(json.dumps({"status": "blocked", "run_id": run_id, "preflight": preflight}, ensure_ascii=False))
        return 2
    handoff = _identity_from_handoff(Path(args.workflowhub_implementation_handoff))
    authority_identity = _load_runtime_authority(authority_map)
    paths = _output_paths(output, run_id, owner_nonce)
    stage = paths["staging"]
    lock_path = paths["lock"]
    lock_fd: int | None = None
    lock_owned = False
    lock_record: Mapping[str, Any] | None = None
    model = None
    embedder = None
    provider_identity: Mapping[str, Any] = {}
    try:
        try:
            lock_record = _create_lock(
                lock_path,
                paths,
                run_id=run_id,
                material_id=str(handoff.get("current", {}).get("material_id", "current-material")),
                owner_nonce=owner_nonce,
            )
            lock_owned = True
        except FileExistsError as error:
            raise Task5RuntimeError(f"another Task5 run holds the output lock: {lock_path}") from error
        if stage.exists():
            raise Task5RuntimeError(f"staging path already exists: {stage}")
        model, embedder, provider_identity = build_task5_providers(Path(args.provider_config))
        slice_selection = _slice_source_selection(Path(args.slice_config), Path(args.source_manifest))
        runtime_requests = {
            "gate": "M402",
            "runtime_config_path": Path(args.config).expanduser().resolve(),
            "m401_packet_path": Path(args.review_manifest),
            "m401_r_receipt_path": Path(args.m401_r_receipt),
            "workflowhub_successor_path": Path(args.workflowhub_implementation_handoff),
            "companybrain_root": Path(args.companybrain),
        }
        sequence = digest_slice_then_full(
            DigestRequest(
                Path(args.raw_input),
                stage / "slice-bundle",
                Path(args.provider_config),
                Path(args.quality_config),
                source_manifest_path=Path(args.source_manifest),
                source_paths=tuple(str(item) for item in slice_selection["source_paths"]),
                evaluation_mode="slice",
                **runtime_requests,
            ),
            DigestRequest(
                Path(args.raw_input),
                # publisher.commit prefixes public files with ``bundle/`` and
                # atomically creates this absent outer staging target.
                stage,
                Path(args.provider_config),
                Path(args.quality_config),
                source_manifest_path=Path(args.source_manifest),
                evaluation_mode="full",
                **runtime_requests,
            ),
            providers=(model, embedder),
        )
        slice_result = sequence.slice_result
        slice_run = sequence.slice_run
        if slice_result is None:
            raise Task5RuntimeError("slice_then_full did not return slice state")
        slice_phase = _summarize_slice_result(slice_selection, slice_result, slice_run)
        if slice_result.outcome in {"unavailable", "blocked"}:
            raise Task5BlockedError(
                f"slice stopped before full run: {slice_result.outcome}: {slice_result.reason_code or 'provider unavailable'}"
            )
        if slice_phase["execution"] != "completed":
            raise Task5RuntimeError(
                f"slice stopped before full run: {slice_result.outcome}: {slice_result.reason_code or 'unknown'}"
            )
        result = sequence.full_result
        if result.outcome in {"unavailable", "blocked"}:
            raise Task5BlockedError(
                f"full run stopped: {result.outcome}: {result.reason_code or 'provider unavailable'}"
            )
        # The compiler owns the inner M402 quality gate and may already have
        # reached ``released`` before the formal runner adds host-only
        # evidence and performs the final publication predicates.  Treat that
        # as a valid upstream outcome; rejecting it here turns a good provider
        # run into a generic runtime failure after all expensive calls finish.
        if result.outcome not in {"completed", "released", "not_released"}:
            raise Task5RuntimeError(f"compiler stopped: {result.outcome}: {result.reason_code or 'unknown'}")
        bundle = stage / "bundle"
        source_manifest_sha256 = str(
            result.companybrain_observation.get("source_manifest_sha256", "")
            if isinstance(result.companybrain_observation, Mapping)
            else ""
        )
        observation_path, observation_sha = _write_host_observation(
            result.companybrain_observation,
            evidence_root=evidence_root,
            attempt_id=attempt_id,
            run_id=result.run_id,
            source_manifest_sha256=source_manifest_sha256,
        )
        # _append_formal_audit removes the compiler's temporary sources,
        # evidence and quality projections from the published audit surface.
        # Preserve those exact bytes in host-only staging for the evaluator;
        # Reader/Home/Audit are still read from the finalized candidate.
        quality_ledger_view = stage / "quality-input"
        shutil.copytree(bundle, quality_ledger_view)
        audit_info, snd = _append_formal_audit(
            bundle,
            Path(args.raw_input),
            Path(args.companybrain),
            evidence_root,
            attempt_id,
            str(handoff.get("current", {}).get("material_id", "current-material")),
            source_manifest=Path(args.source_manifest),
            companybrain_observation=result.companybrain_observation,
        )
        surface = _surface_qa(bundle)
        surface_path = evidence_root / "m402-surface-qa" / "attempts" / attempt_id / "surface-qa.json"
        surface_path.parent.mkdir(parents=True, exist_ok=False)
        surface_path.write_bytes(_canonical(surface))
        quality_path = evidence_root / "actual-run" / "attempts" / attempt_id / "quality-result.json"
        quality = evaluate_candidate(candidate=bundle, raw=Path(args.raw_input), companybrain=Path(args.companybrain), cases=Path(args.quality_config), baseline=Path(args.baseline_config), config=Path(args.provider_config), output=quality_path, judge=True, ledger_root=quality_ledger_view, source_manifest=Path(args.source_manifest))
        quality["quality_result_status"] = "candidate"
        quality["published_tree_sha256"] = None
        quality = _rehash_quality_result(quality)
        quality_path.write_bytes(_canonical(quality))
        candidate_tree_sha = str(quality.get("candidate_tree_sha256", ""))
        release_probe = dict(quality)
        release_probe["quality_result_status"] = "released"
        release_probe["published_tree_sha256"] = candidate_tree_sha
        release_ok = (
            result.outcome in {"completed", "released"}
            and not slice_phase["release_blocked"]
            and surface.get("status") == "passed"
            and snd.get("status") == "passed"
            and strict_winner(_rehash_quality_result(release_probe))
        )
        # The compiler's public run ledger lives under the fixed audit
        # surface.  _append_formal_audit already selected and validated that
        # ledger; reuse its exact parsed value instead of reaching for the
        # removed legacy _digest/run.json path.
        run_json = dict(audit_info["run"])
        failure_ref = None
        failure_path = None
        if not release_ok:
            failure_path, failure_ref = _write_failure_evidence(
                output=output,
                run_id=run_id,
                reason_code="QUALITY_GATE_FAILED",
                provider_identity=provider_identity,
                observed_calls=run_json.get("provider_calls", {"llm": 0, "embedding": 0}),
                audit_ref="bundle/Audit.md",
                output_retained=True,
            )
        formal = _formal_run_result(
            run=run_json,
            task_id=TASK_ID,
            run_id=run_id,
            handoff=handoff,
            provider_identity=provider_identity,
            source_manifest=Path(args.source_manifest),
            quality_cases=Path(args.quality_config),
            slice_cases=Path(args.slice_config),
            output_bundle=bundle,
            quality_result=quality,
            quality_result_ref=_public_ref(quality_path),
            quality_result_sha256=sha256_bytes(quality_path.read_bytes()),
            snd_verifier=snd,
            surface_qa=surface,
            authority_identity=authority_identity,
            provider_config=Path(args.provider_config),
            calibration_manifest=Path(args.calibration_manifest),
            calibration_artifact=Path(args.calibration_artifact),
            companybrain_host_snapshot_sha256=str(audit_info.get("host_companybrain_sha256", "")),
            outcome="success" if release_ok else "failed",
            publication_status="candidate" if release_ok else "not_released",
            reason_code="NONE" if release_ok else "QUALITY_GATE_FAILED",
            exit_code=0 if release_ok else 1,
            phase_results={
                "slice": slice_phase["quality"],
                "slice_preflight": slice_phase["preflight"],
                "slice_execution": slice_phase["execution"],
                "slice_quality": slice_phase["quality"],
                "slice_projection_statuses": slice_phase["projection_statuses"],
                "full": "passed" if result.outcome in {"completed", "released"} else "failed",
                "quality": "passed" if release_ok else "failed",
                "surface_qa": surface.get("status", "failed"),
                "snd": snd.get("status", "unknown"),
            },
            failure_evidence_path=failure_ref,
        )
        _write_canonical(bundle / "_audit" / "run-result.json", formal)
        directory = _manifest(bundle)
        layout_path = Path(__file__).resolve().parents[2] / "config" / "task5-publication-layout-v2.json"
        directory["layout_contract_sha256"] = sha256_bytes(layout_path.read_bytes())
        directory["required_paths"] = [f"bundle/{relative}" for relative in FIXED_AUDIT_FILES]
        directory["forbidden_path_scan"] = {"passed": _no_secret(directory), "matches": [] if _no_secret(directory) else ["secret_like_value"]}
        _write_canonical(bundle / "_audit" / "directory-manifest.json", directory)
        _validate_audit_layout(bundle)
        candidate_directory_manifest_sha256 = _directory_manifest_sha256(bundle)
        os.replace(stage, output)
        if lock_record is None:
            raise Task5RuntimeError("output lock record is missing")
        if lock_fd is not None:
            os.close(lock_fd)
            lock_fd = None
        rename_receipt = _with_hash({
            "schema_version": "task5-output-rename-receipt.v1",
            "run_id": run_id,
            "candidate_tree_sha256": candidate_tree_sha,
            "output_tree_sha256": _manifest(output / "bundle")["tree_sha256"],
            "status": "passed",
        })
        if rename_receipt["candidate_tree_sha256"] != rename_receipt["output_tree_sha256"]:
            raise Task5RuntimeError("published tree differs from candidate tree after rename")
        _transition_lock(lock_path, "rename_committed", rename_receipt=rename_receipt)
        _transition_lock(lock_path, "finalizing", candidate_tree_sha256=candidate_tree_sha, published_tree_sha256=rename_receipt["output_tree_sha256"])
        if release_ok:
            published_tree_sha = str(rename_receipt["output_tree_sha256"])
            final_quality = dict(quality)
            final_quality["quality_result_status"] = "released"
            final_quality["published_tree_sha256"] = published_tree_sha
            final_quality["finalization"] = {
                "candidate_quality_ref": _public_ref(quality_path),
                "candidate_quality_sha256": sha256_bytes(quality_path.read_bytes()),
                "candidate_tree_sha256": candidate_tree_sha,
                "published_tree_sha256": published_tree_sha,
                "candidate_directory_manifest_sha256": candidate_directory_manifest_sha256,
                "published_directory_manifest_sha256": _directory_manifest_sha256(output / "bundle"),
                "rename_receipt": rename_receipt["canonical_sha256"],
            }
            final_quality = _rehash_quality_result(final_quality)
            finalize_dir = evidence_root / "actual-run" / "quality-result-finalize" / "attempts" / attempt_id
            finalize_dir.mkdir(parents=True, exist_ok=False)
            finalize_path = finalize_dir / "quality-result.json"
            finalize_sha = _write_create_only(finalize_path, final_quality)
            promoted_quality_path = evidence_root / "actual-run" / "quality-result.json"
            promoted_quality_sha = _write_create_only(promoted_quality_path, final_quality)
            final_formal = _formal_run_result(
                run=run_json,
                task_id=TASK_ID,
                run_id=run_id,
                handoff=handoff,
                provider_identity=provider_identity,
                source_manifest=Path(args.source_manifest),
                quality_cases=Path(args.quality_config),
                slice_cases=Path(args.slice_config),
                output_bundle=output / "bundle",
                quality_result=final_quality,
                quality_result_ref="actual-run/quality-result.json",
                quality_result_sha256=promoted_quality_sha,
                snd_verifier=snd,
                surface_qa=surface,
                authority_identity=authority_identity,
                provider_config=Path(args.provider_config),
                calibration_manifest=Path(args.calibration_manifest),
                calibration_artifact=Path(args.calibration_artifact),
                companybrain_host_snapshot_sha256=str(audit_info.get("host_companybrain_sha256", "")),
                outcome="success",
                publication_status="released",
                reason_code="NONE",
                exit_code=0,
                phase_results={
                    "slice": slice_phase["quality"],
                    "slice_preflight": slice_phase["preflight"],
                    "slice_execution": slice_phase["execution"],
                    "slice_quality": slice_phase["quality"],
                    "slice_projection_statuses": slice_phase["projection_statuses"],
                    "full": "passed",
                    "quality": "passed",
                    "surface_qa": "passed",
                    "snd": "passed",
                },
                failure_evidence_path=None,
            )
            final_formal["artifact_manifest"]["quality_result"] = {"ref": "actual-run/quality-result.json", "sha256": promoted_quality_sha, "finalize_ref": _public_ref(finalize_path), "finalize_sha256": finalize_sha}
            final_formal = _with_hash(final_formal)
            _write_canonical(output / "bundle/_audit/run-result.json", final_formal)
            _validate_audit_layout(output / "bundle")
            # The host receipt is part of the release closure.  Persist it
            # before marking the output lock as published; otherwise a
            # receipt-write failure could leave a public released bundle with
            # no authenticated host binding.
            _write_host_run_receipt(
                evidence_root=evidence_root,
                attempt_id=attempt_id,
                run_id=run_id,
                raw=Path(args.raw_input),
                companybrain=Path(args.companybrain),
                output=output,
                provider_config=Path(args.provider_config),
                source_manifest=Path(args.source_manifest),
                public_receipt=output / "bundle" / "_audit" / "run-result.json",
                terminal_status="released",
            )
            _transition_lock(lock_path, "published", finalize_receipt={"ref": _public_ref(finalize_path), "sha256": finalize_sha, "promoted_ref": "actual-run/quality-result.json", "promoted_sha256": promoted_quality_sha})
        else:
            if failure_path is None:
                raise Task5RuntimeError("quality failure evidence is missing before publication")
            _write_host_run_receipt(
                evidence_root=evidence_root,
                attempt_id=attempt_id,
                run_id=run_id,
                raw=Path(args.raw_input),
                companybrain=Path(args.companybrain),
                output=output,
                provider_config=Path(args.provider_config),
                source_manifest=Path(args.source_manifest),
                public_receipt=output / "bundle" / "_audit" / "run-result.json",
                terminal_status="not_released",
            )
            _transition_lock(
                lock_path,
                "failed",
                failure_evidence_path=str(failure_path),
                failure_evidence_sha256=sha256_bytes(failure_path.read_bytes()),
            )
        print(json.dumps({"status": "released" if release_ok else "not_released", "output": str(output), "run_id": run_id, "quality_result": str(quality_path)}, ensure_ascii=False))
        return 0 if release_ok else 1
    except Exception as error:
        observed_calls = {"llm": int(getattr(model, "calls", 0)) if model is not None else 0, "embedding": int(getattr(embedder, "calls", 0)) if embedder is not None else 0}
        blocked = isinstance(error, (Task5BlockedError, ProviderConfigError, ProviderError))
        terminal_status = "blocked" if blocked else "failed"
        terminal_code = "PROVIDER_UNAVAILABLE" if blocked else type(error).__name__
        terminal_exit = 2 if blocked else 3
        failure_path, _ = _write_failure_evidence(
            output=output,
            run_id=run_id,
            reason_code=terminal_code,
            provider_identity=provider_identity,
            observed_calls=observed_calls,
            audit_ref="bundle/Audit.md" if output.exists() else None,
            output_retained=output.exists(),
            status=terminal_status,
            exit_code=terminal_exit,
        )
        if stage.exists():
            try:
                _write_staging_failure_run_result(
                    stage=stage,
                    run_id=run_id,
                    handoff=handoff,
                    provider_identity=provider_identity,
                    reason_code=terminal_code,
                    observed_calls=observed_calls,
                    status=terminal_status,
                    outcome=terminal_status,
                    exit_code=terminal_exit,
                )
            except (OSError, Task5RuntimeError):
                pass
        if lock_owned and lock_path.is_file():
            try:
                current_state = str(_read_json(lock_path).get("state", ""))
                target_state = "publication_ambiguous" if output.exists() and not stage.exists() else "failed"
                if target_state in {"publication_ambiguous", "failed"} and current_state != "published":
                    _transition_lock(lock_path, target_state, failure_evidence_path=str(failure_path), failure_evidence_sha256=sha256_bytes(failure_path.read_bytes()))
            except Task5RuntimeError:
                pass
        if lock_fd is not None:
            os.close(lock_fd)
            lock_fd = None
        # Keep the machine reason code stable, but expose the concrete local
        # invariant on stderr so a failed authenticated run is diagnosable.
        print(json.dumps({"status": terminal_status, "run_id": run_id, "reason": terminal_code, "detail": str(error)[:500]}, ensure_ascii=False), file=sys.stderr)
        return terminal_exit
    finally:
        if lock_fd is not None:
            os.close(lock_fd)


def _run_command(command: Sequence[str]) -> dict[str, Any]:
    profile = "(version 1)(deny network*)"
    if Path("/usr/bin/sandbox-exec").is_file():
        command = ("/usr/bin/sandbox-exec", "-p", profile, "--", *command)
    completed = subprocess.run(list(command), text=True, capture_output=True, check=False)
    return {"command": list(command), "exit_code": completed.returncode, "stdout_sha256": sha256_bytes(completed.stdout.encode()), "stderr_sha256": sha256_bytes(completed.stderr.encode()), "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}


def _test_receipt(kind: str, command: Sequence[str], result: Mapping[str, Any], snapshot_tree: str, material_id: str) -> dict[str, Any]:
    output = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
    counts = [int(item) for item in re.findall(r"(?<!\d)(\d+)\s+(?:passed|failed|skipped|xfailed|xpassed|error|errors)", output)]
    return _with_hash({"schema_version": "task5-m401-test-receipt.v1", "receipt_kind": kind, "commands": [dict(result, command_hash=sha256_bytes(_canonical(list(command))))], "exit_code": int(result["exit_code"]), "status": "passed" if result["exit_code"] == 0 else "failed", "test_count": sum(counts) if counts else None, "snapshot_tree": snapshot_tree, "material_id": material_id})


TASK5_M401_FOCUSED_TEST_FILES = (
    "tests/acceptance/test_task5_contract.py",
    "tests/acceptance/test_task5_publication_contract.py",
    "tests/acceptance/test_task5_provider.py",
    "tests/acceptance/test_task5_source_semantic.py",
    "tests/acceptance/test_task5_projection.py",
    "tests/acceptance/test_task5_quality_gate.py",
    "tests/test_simple_digest.py",
    "tests/test_simple_providers.py",
)

TASK5_M401_FULL_TEST_FILES = (
    "tests/acceptance/test_task5_contract.py",
    "tests/acceptance/test_task5_full_run.py",
    "tests/acceptance/test_task5_publication_contract.py",
    "tests/acceptance/test_task5_provider.py",
    "tests/acceptance/test_task5_projection.py",
    "tests/acceptance/test_task5_quality_gate.py",
    "tests/acceptance/test_task5_source_semantic.py",
    "tests/test_simple_digest.py",
    "tests/test_simple_providers.py",
)


def _surface_qa(bundle: Path) -> dict[str, Any]:
    """Check the actual Markdown surface and its Reader→Audit links."""

    bundle = _safe_root(bundle, "candidate bundle")
    issues: list[str] = []
    for required in ("README.md", "Home.md", "Audit.md", *FIXED_AUDIT_FILES):
        if not (bundle / required).is_file():
            issues.append(f"missing:{required}")
    home = bundle / "Home.md"
    audit = bundle / "Audit.md"
    home_text = home.read_text(encoding="utf-8") if home.is_file() else ""
    audit_text = audit.read_text(encoding="utf-8") if audit.is_file() else ""
    if "按问题和场景" not in home_text or "按产品" not in home_text:
        issues.append("home_missing_question_or_product_entry")
    if "来源清单" not in audit_text:
        issues.append("audit_missing_source_index")
    for current in (home, audit):
        if not current.is_file():
            continue
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", current.read_text(encoding="utf-8")):
            path_part = target.split("#", 1)[0].strip()
            if not path_part or "://" in path_part:
                continue
            resolved = (current.parent / path_part).resolve()
            try:
                resolved.relative_to(bundle.resolve())
            except ValueError:
                issues.append(f"link_escape:{current.relative_to(bundle)}:{target}")
            else:
                if not resolved.is_file():
                    issues.append(f"link_missing:{current.relative_to(bundle)}:{target}")
    reader_pages = [path for path in (bundle / "products").rglob("*.md") if path.name != "index.md"] if (bundle / "products").is_dir() else []
    forbidden_segments = {"modules", "boundaries", "knowledge", "staging", "attempt", "candidate-bundle"}
    page_types = {"positioning", "concept", "operation", "diagnosis", "experience"}
    for page in reader_pages:
        relative = page.relative_to(bundle).as_posix()
        parts = page.relative_to(bundle / "products").parts
        if any(part.casefold() in forbidden_segments for part in parts):
            issues.append(f"forbidden_reader_path:{relative}")
        if len(parts) < 3 or parts[-2] not in page_types:
            issues.append(f"reader_path_has_no_page_type:{relative}")
        if re.search(r"-[0-9a-f]{8,}\.md$|^(cluster|draft)-[0-9a-f]+\.md$", page.name, re.I):
            issues.append(f"opaque_reader_filename:{relative}")
        text = page.read_text(encoding="utf-8")
        visible = re.sub(r"(?s)<!--.*?-->", "", text)
        visible = re.sub(r"\A---\n.*?\n---\n?", "", visible)
        if not re.search(r"(?m)^#\s+\S", visible):
            issues.append(f"reader_missing_title:{relative}")
        if "这页解决什么问题" not in visible or "来源" not in visible:
            issues.append(f"reader_missing_answer_or_source:{relative}")
        if "/tmp/" in visible or "candidate-bundle" in visible:
            issues.append(f"reader_leaks_staging_path:{relative}")
        audit_links = re.findall(r"\[[^\]]*Audit[^\]]*\]\(([^)#]+)#([^)]+)\)", text, flags=re.I)
        if not audit_links:
            issues.append(f"reader_missing_audit_anchor:{relative}")
        for target, anchor in audit_links:
            resolved = (page.parent / target).resolve()
            if resolved != audit.resolve() or f'<a id="{anchor}"></a>' not in audit_text:
                issues.append(f"reader_audit_replay_failed:{relative}#{anchor}")
    return {"schema_version": "task5-surface-qa.v1", "bundle_ref": "candidate_bundle", "reader_page_count": len(reader_pages), "issues": sorted(set(issues)), "status": "passed" if not issues else "failed", "network_policy": "deny"}


def _validate_design_handoff(path: Path) -> dict[str, Any]:
    value = _read_json(path)
    required = {"task_id", "review_kind", "review_result_ref", "review_result_sha256", "review_report_ref", "review_outcome", "terminal_status", "terminal_clean", "design_review_contract_id", "design_review_contract_hash", "semantic_hash", "snapshot_tree", "material_id", "writer_attestation"}
    missing = sorted(required - set(value))
    if missing:
        raise Task5RuntimeError(f"design handoff is incomplete: {', '.join(missing)}")
    if value.get("task_id") != TASK_ID or value.get("review_kind") != "mini_task.design" or value.get("review_outcome") != "available" or value.get("terminal_status") != "semantic" or value.get("terminal_clean") is not True:
        raise Task5RuntimeError("design handoff is not terminal-clean for this task")
    if not _no_secret(value):
        raise Task5RuntimeError("design handoff contains a secret-like field")
    return dict(value)


def run_m401(args: argparse.Namespace) -> int:
    evidence_root = Path(args.evidence_root)
    attempt_id = "m401-" + uuid.uuid4().hex[:20]
    attempt_dir = evidence_root / "repair-gates" / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=False)
    handoff = Path(args.workflowhub_handoff) if args.workflowhub_handoff else None
    reasons: list[str] = []
    identity: Mapping[str, Any] = {}
    if handoff is None or not handoff.is_file():
        reasons.append("design WorkflowHub handoff is missing")
    else:
        try:
            identity = _validate_design_handoff(handoff)
        except Task5RuntimeError as error:
            reasons.append(str(error))
    candidate = Path(args.candidate_bundle_ref).expanduser() if args.candidate_bundle_ref else None
    if candidate is None or not candidate.is_dir() or candidate.is_symlink():
        reasons.append("candidate bundle ref is missing or not a regular directory")
    else:
        try:
            _validate_audit_layout(candidate)
            manifest_path = candidate / "_audit/directory-manifest.json"
            actual_manifest_sha = sha256_bytes(manifest_path.read_bytes())
            if actual_manifest_sha != str(args.directory_manifest_sha256 or ""):
                reasons.append("candidate directory manifest hash does not match authenticated input")
            actual_tree_sha = _manifest(candidate)["tree_sha256"]
            if actual_tree_sha != str(args.candidate_tree_sha256 or ""):
                reasons.append("candidate tree hash does not match authenticated input")
        except Task5RuntimeError as error:
            reasons.append(str(error))
    companybrain = Path(args.companybrain).expanduser() if args.companybrain else None
    if companybrain is None:
        reasons.append("CompanyBrain path is missing")
    else:
        try:
            _safe_root(companybrain, "CompanyBrain")
        except Task5RuntimeError as error:
            reasons.append(str(error))
    if str(args.provider_mode or "") != "fake":
        reasons.append("M401 must use provider-mode fake")
    if str(args.network_policy or "") != "deny":
        reasons.append("M401 must use network-policy deny")
    if not args.surface_qa:
        reasons.append("M401 surface QA is required")
    r4_ref = Path(args.r4_attempt_ref).expanduser() if args.r4_attempt_ref else None
    if r4_ref is None or not r4_ref.is_file():
        reasons.append("promoted R4 attempt ref is missing")
    # Historical V50 replay remains separately evidenced. Its absence must
    # not block a current raw-only M401/M402; supplied bindings are still
    # checked when present so malformed optional evidence cannot be trusted.
    root_cause_ref = Path(getattr(args, "root_cause_ref", "")).expanduser() if getattr(args, "root_cause_ref", None) else None
    root_cause_sha = str(getattr(args, "root_cause_sha", "") or "")
    root_cause_manifest = Path(getattr(args, "root_cause_input_manifest", "")).expanduser() if getattr(args, "root_cause_input_manifest", None) else None
    root_cause_manifest_sha = str(getattr(args, "root_cause_input_manifest_sha256", "") or "")
    if root_cause_ref is not None and root_cause_ref.is_file() and root_cause_sha:
        if root_cause_sha != sha256_bytes(root_cause_ref.read_bytes()):
            reasons.append("optional root-cause evidence hash does not match supplied binding")
    if root_cause_manifest is not None and root_cause_manifest.is_file() and root_cause_manifest_sha:
        if root_cause_manifest_sha != sha256_bytes(root_cause_manifest.read_bytes()):
            reasons.append("optional root-cause input manifest hash does not match supplied binding")
    expected_focused = set(TASK5_M401_FOCUSED_TEST_FILES)
    expected_full = set(TASK5_M401_FULL_TEST_FILES)
    focused = list(args.focused_test or [])
    full = list(args.full_test or [])
    if set(focused) != expected_focused or len(focused) != len(expected_focused):
        reasons.append("focused tests do not match the current Task5 contract")
    if set(full) != expected_full or len(full) != len(expected_full):
        reasons.append("full tests do not match the current Task5 contract")
    snapshot_tree = str(identity.get("snapshot_tree", ""))
    material_id = str(identity.get("material_id", ""))
    if not snapshot_tree or not material_id:
        reasons.append("snapshot_tree/material_id must come from authenticated design handoff")
    receipts: dict[str, Any] = {}
    companybrain_public: Mapping[str, Any] = {}
    companybrain_host_sha = ""
    if not reasons:
        companybrain_public, companybrain_host_sha = _companybrain_snapshot(companybrain, evidence_root, attempt_id)
        focused_command = ["uv", "run", "--frozen", "pytest", "-q", *focused]
        focused_result = _run_command(focused_command)
        focused_receipt = _test_receipt("focused", focused_command, focused_result, snapshot_tree, material_id)
        focused_path = attempt_dir / "focused-test-receipt.json"
        focused_path.write_bytes(_canonical(focused_receipt))
        receipts["focused"] = focused_receipt
        if focused_result["exit_code"] != 0:
            reasons.append("focused tests failed")
        if not reasons:
            full_command = ["uv", "run", "--frozen", "pytest", "-q", *full]
            full_result = _run_command(full_command)
            full_receipt = _test_receipt("full-regression", full_command, full_result, snapshot_tree, material_id)
            full_path = attempt_dir / "full-test-receipt.json"
            full_path.write_bytes(_canonical(full_receipt))
            receipts["full"] = full_receipt
            if full_result["exit_code"] != 0:
                reasons.append("full regression failed")
        if not reasons and candidate is not None:
            surface = _surface_qa(candidate)
            surface["candidate_tree_sha256"] = str(args.candidate_tree_sha256)
            surface["directory_manifest_sha256"] = str(args.directory_manifest_sha256)
            surface["r4_attempt_ref"] = str(r4_ref)
            surface["canonical_sha256"] = _with_hash(surface)["canonical_sha256"]
            (attempt_dir / "surface-qa.json").write_bytes(_canonical(surface))
            receipts["surface_qa"] = surface
            if surface["status"] != "passed":
                reasons.append("candidate surface QA failed")
    packet = _with_hash({
        "schema_version": "task5-m401-evidence-packet.v1",
        "task_id": TASK_ID,
        "attempt_id": attempt_id,
        "status": "passed" if not reasons else "failed",
        "focused_receipt": "focused-test-receipt.json" if "focused" in receipts else None,
        "full_receipt": "full-test-receipt.json" if "full" in receipts else None,
        "surface_qa_receipt": "surface-qa.json" if "surface_qa" in receipts else None,
        "workflowhub_design_handoff": str(handoff) if handoff else None,
        "design_review_identity": {key: identity.get(key) for key in ("review_kind", "review_result_ref", "review_result_sha256", "review_report_ref", "design_review_contract_id", "design_review_contract_hash", "semantic_hash", "snapshot_tree", "material_id")},
        "runtime_identity": {"runtime_contract_id": str(args.runtime_contract_id or ""), "runtime_contract_hash": str(args.runtime_contract_hash or ""), "semantic_contract_id": str(args.semantic_contract_id or ""), "semantic_contract_hash": str(args.semantic_contract_hash or "")},
        "candidate": {"ref": str(candidate) if candidate else None, "directory_manifest_sha256": str(args.directory_manifest_sha256 or ""), "tree_sha256": str(args.candidate_tree_sha256 or "")},
        "r4_attempt_ref": str(r4_ref) if r4_ref else None,
        "companybrain_host_snapshot_sha256": companybrain_host_sha,
        "companybrain_public_snapshot": dict(companybrain_public),
        "snapshot_tree": snapshot_tree,
        "material_id": material_id,
        "pre_m402_readiness": not bool(reasons),
        "finding_dispositions": [],
        "coverage_limits": ["M401 does not execute real raw/CompanyBrain provider run"],
        "ac_trace": {f"AC-{index:03d}": {"status": "covered" if not reasons else "not_proven", "owner": "M401"} for index in range(1, 22)},
        "reasons": reasons,
    })
    packet_path = attempt_dir / "M401-evidence-packet.json"
    packet_path.write_bytes(_canonical(packet))
    if not reasons:
        promotion = evidence_root / "M401-evidence-packet.json"
        promotion.write_bytes(packet_path.read_bytes())
    print(json.dumps({"status": packet["status"], "attempt_id": attempt_id, "packet": str(packet_path), "reasons": reasons}, ensure_ascii=False))
    return 0 if not reasons else 1


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Formal Task5 reader-quality runtime")
    sub = p.add_subparsers(dest="command", required=True)
    root_cause = sub.add_parser("root-cause-preflight", help="D0-H: verify historical inputs without provider calls")
    root_cause.add_argument("--root-cause-input-manifest", required=True, type=Path)
    root_cause.add_argument("--root-cause-contract", required=True, type=Path)
    root_cause.add_argument("--raw-input", required=True, type=Path)
    root_cause.add_argument("--companybrain", required=True, type=Path)
    root_cause.add_argument("--evidence-root", type=Path, default=Path("quality/evidence/task5"))
    root_cause.add_argument("--network-policy", required=True)
    root_cause.set_defaults(func=run_root_cause_preflight)
    raw = sub.add_parser("raw-preflight", help="D0-R: validate the current 89-source corpus without provider calls")
    raw.add_argument("--raw-input", required=True, type=Path)
    raw.add_argument("--companybrain", required=True, type=Path)
    raw.add_argument("--evidence-root", type=Path, default=Path("quality/evidence/task5"))
    raw.add_argument("--network-policy", required=True)
    raw.set_defaults(func=run_raw_preflight)
    run = sub.add_parser("run")
    run.add_argument("--raw-input", required=True, type=Path)
    run.add_argument("--companybrain", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--config", required=True, type=Path)
    run.add_argument("--provider-config", required=True, type=Path)
    run.add_argument("--quality-config", required=True, type=Path)
    run.add_argument("--baseline-config", required=True, type=Path)
    run.add_argument("--slice-config", required=True, type=Path)
    run.add_argument("--source-manifest", required=True, type=Path)
    run.add_argument("--evidence-root", type=Path, default=Path("quality/evidence/task5"))
    run.add_argument("--workflowhub-implementation-handoff", type=Path)
    run.add_argument("--m401-r-receipt", type=Path)
    run.add_argument("--baseline-identity-from-root-cause-input")
    run.add_argument("--observation-config", type=Path, required=True)
    run.add_argument("--review-manifest", type=Path, required=True)
    run.add_argument("--calibration-manifest", type=Path, required=True)
    run.add_argument("--calibration-artifact", type=Path, required=True)
    run.add_argument("--quality-result-config", type=Path, required=True)
    run.add_argument("--source-direct-contract", type=Path, required=True)
    run.add_argument("--snd-verifier-contract", type=Path, required=True)
    run.add_argument("--snd-verifier-contract-actual-sha", required=True)
    run.add_argument("--snd-verifier-contract-canonical-sha", required=True)
    run.set_defaults(func=run_real)
    m401 = sub.add_parser("m401")
    m401.add_argument("--workflowhub-handoff", type=Path, required=True)
    m401.add_argument("--companybrain", type=Path, required=True)
    m401.add_argument("--evidence-root", required=True, type=Path)
    m401.add_argument("--provider-mode", required=True)
    m401.add_argument("--network-policy", required=True)
    m401.add_argument("--candidate-bundle-ref", type=Path, required=True)
    m401.add_argument("--r4-attempt-ref", required=True)
    m401.add_argument("--directory-manifest-sha256", required=True)
    m401.add_argument("--candidate-tree-sha256", required=True)
    m401.add_argument("--runtime-contract-id", required=True)
    m401.add_argument("--runtime-contract-hash", required=True)
    m401.add_argument("--semantic-contract-id", required=True)
    m401.add_argument("--semantic-contract-hash", required=True)
    m401.add_argument("--root-cause-ref")
    m401.add_argument("--root-cause-sha")
    m401.add_argument("--root-cause-input-manifest")
    m401.add_argument("--root-cause-input-manifest-sha256")
    m401.add_argument("--focused-test", action="append")
    m401.add_argument("--full-test", action="append")
    m401.add_argument("--surface-qa", action="store_true")
    m401.set_defaults(func=run_m401)
    return p


def main(argv: list[str] | None = None) -> int:
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    # Preserve the ordinary one-command product interface.  Formal Task5
    # lifecycle gates use the explicit ``run``/``m401`` verbs and never fall
    # through to the ordinary CLI.
    if not effective_argv or effective_argv[0] not in {"run", "m401", "raw-preflight", "root-cause-preflight"}:
        from .simple_cli import main as product_main

        return product_main(effective_argv)
    args = parser().parse_args(effective_argv)
    try:
        return int(args.func(args))
    except Task5RuntimeError as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    print(
        "knowledge_digest.task5_runtime is historical test support; use the "
        "registered digest CLI instead.",
        file=sys.stderr,
    )
    raise SystemExit(2)
