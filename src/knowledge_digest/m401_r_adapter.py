"""Authenticated WorkflowHub -> Task5 M401-R promotion bridge.

The generic WorkflowHub review route owns provider execution and canonical
review records.  This module owns only the Task5-specific, host-side binding:
it verifies those records against the current M401 attempt, mirrors their
bytes into the task evidence root, and promotes the fixed gate artifacts.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

from .compiler import _canonical_json, _load_m402_runtime_authority, _sha, _validate_workflowhub_successor


TASK_ID = "task5-reader-quality-compiler-redesign"
REVIEW_KIND = "mini_task.implementation"
REVIEW_SCHEMA = "wh-review-result.v1"
REVIEW_PROJECTION_SCHEMA = "workflowhub-mini-task-review-result.v1"
M401_PACKET_SCHEMA = "task5-m401-evidence-packet.v1"
M401_R_SCHEMA = "task5-m401-r-review-receipt.v1"
HANDOFF_SCHEMA = "workflowhub-implementation-successor.v1"
M401_R_FIELDS = frozenset(
    {
        "schema_version",
        "review_kind",
        "m401_packet_ref",
        "m401_packet_sha256",
        "review_result_ref",
        "review_result_sha256",
        "source_receipt_ref",
        "source_receipt_sha256",
        "snapshot_tree",
        "material_id",
        "terminal_status",
        "terminal_clean",
        "all_findings_disposed",
        "finding_dispositions",
        "outcome",
        "status",
        "reason_code",
    }
)
DISPOSITION_STATUSES = frozenset({"fixed", "rejected_invalid", "accepted_risk"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class M401RAdapterError(ValueError):
    """The authenticated review cannot be promoted for this M401 attempt."""


def _canonical(value: Any) -> bytes:
    return _canonical_json(value)


def _workflowhub_canonical(value: Any) -> bytes:
    """Match WorkflowHub's canonical review writer (ordered pretty JSON + LF)."""

    try:
        return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise M401RAdapterError("WorkflowHub review record contains non-JSON values") from error


def _read_json_value(path: Path, *, label: str) -> tuple[Any, bytes]:
    candidate = Path(path).expanduser()
    if candidate.is_symlink() or not candidate.is_file():
        raise M401RAdapterError(f"{label} is missing: {candidate}")
    try:
        raw = candidate.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise M401RAdapterError(f"{label} is invalid: {candidate}") from error
    return value, raw


def _read_json(path: Path, *, label: str) -> tuple[dict[str, Any], bytes]:
    value, raw = _read_json_value(path, label=label)
    if not isinstance(value, dict):
        raise M401RAdapterError(f"{label} must be a JSON object")
    return value, raw


def _sha_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(task_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(task_root.resolve()).as_posix()
    except ValueError as error:
        raise M401RAdapterError(f"managed ref escapes task root: {path}") from error


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise M401RAdapterError(f"promotion target already exists: {path}") from error
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def _replace_promotion_set(items: Sequence[tuple[Path, bytes]]) -> None:
    """Replace one complete promotion view after all new bytes are staged.

    Promotion views are derived views; the immutable attempt remains the
    source of truth.  Stage all bytes first so a validation or write failure
    cannot leave a newly-created target half populated.  Existing bytes are
    restored if a later replacement fails.
    """

    staged: list[tuple[Path, Path]] = []
    originals: dict[Path, bytes | None] = {}
    replaced: list[Path] = []
    try:
        for target, data in items:
            if target.is_symlink():
                raise M401RAdapterError(f"promotion target is a symlink: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            originals[target] = target.read_bytes() if target.exists() else None
            temporary = target.with_name(f".{target.name}.promotion-{uuid.uuid4().hex}.tmp")
            _write_exclusive(temporary, data)
            staged.append((target, temporary))
        for target, temporary in staged:
            os.replace(temporary, target)
            replaced.append(target)
    except Exception:
        for target in reversed(replaced):
            original = originals[target]
            if original is None:
                try:
                    target.unlink()
                except FileNotFoundError:
                    pass
            else:
                rollback = target.with_name(f".{target.name}.rollback-{uuid.uuid4().hex}.tmp")
                try:
                    _write_exclusive(rollback, original)
                    os.replace(rollback, target)
                finally:
                    try:
                        rollback.unlink()
                    except FileNotFoundError:
                        pass
        raise
    finally:
        for _, temporary in staged:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _creation_patch(files: Mapping[str, bytes]) -> bytes:
    """Build the inverse patch for the two promoted M401-R source files."""

    chunks: list[str] = []
    for relative, content in sorted(files.items(), key=lambda item: item[0].encode("utf-8")):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise M401RAdapterError(f"M401-R inverse patch cannot encode binary output: {relative}") from error
        chunks.extend(
            difflib.unified_diff(
                (),
                text.splitlines(keepends=True),
                fromfile="/dev/null",
                tofile=f"b/{relative}",
                lineterm="\n",
            )
        )
    return "".join(chunks).encode("utf-8")


def _snapshot(files: Mapping[str, bytes]) -> str:
    rows = [
        {"relative_path": relative, "sha256": _sha(content)}
        for relative, content in sorted(files.items(), key=lambda item: item[0].encode("utf-8"))
    ]
    return _sha(_canonical(rows))


def _verify_inverse_patch(attempt_dir: Path, inverse_path: Path) -> None:
    try:
        completed = subprocess.run(
            ["git", "apply", "--check", "--reverse", str(inverse_path.name)],
            cwd=attempt_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError as error:
        raise M401RAdapterError("M401-R inverse patch check is unavailable") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise M401RAdapterError(f"M401-R inverse patch check failed: {detail}")


def _validate_m401_attempt(task_root: Path, attempt_root: Path) -> tuple[dict[str, Any], bytes, dict[str, Any], bytes]:
    if attempt_root.is_symlink():
        raise M401RAdapterError("M401 attempt must not be a symlink")
    attempt_root = attempt_root.resolve()
    expected_root = task_root.resolve() / "quality" / "evidence" / "task5" / "repair-gates" / "attempts"
    try:
        attempt_root.relative_to(expected_root)
    except ValueError as error:
        raise M401RAdapterError("M401 attempt must be under repair-gates/attempts") from error
    packet_path = attempt_root / "M401" / "M401-evidence-packet.json"
    source_receipt_path = attempt_root / "M401" / "attempt-receipt.json"
    attempt_path = attempt_root / "M401" / "attempt.json"
    inverse_path = attempt_root / "M401" / "inverse.patch"
    packet, packet_raw = _read_json(packet_path, label="M401 packet")
    receipt, receipt_raw = _read_json(source_receipt_path, label="M401 attempt receipt")
    attempt, attempt_raw = _read_json(attempt_path, label="M401 attempt record")
    if packet.get("schema_version") != M401_PACKET_SCHEMA or packet.get("gate") != "M401" or packet.get("status") != "passed" or packet.get("pre_m402_readiness") is not True:
        raise M401RAdapterError("M401 attempt packet is not passed/pre-M402-ready")
    if packet_raw != _canonical(packet):
        raise M401RAdapterError("M401 attempt packet is not canonical UTF-8 JSON")
    if packet.get("canonical_sha256") != _sha(_canonical({k: v for k, v in packet.items() if k != "canonical_sha256"})):
        raise M401RAdapterError("M401 attempt packet self-hash is invalid")
    required_attempt = {
        "schema_version", "gate", "attempt_id", "attempt_seq", "material_id", "command",
        "command_sha256", "before_snapshot", "after_snapshot", "changed_paths",
        "before_sha256", "after_sha256", "patch_sha256", "inverse_patch_ref",
        "inverse_patch_sha256", "inverse_base_after_snapshot", "run_root_ref", "exit_code",
        "status", "reason_code",
    }
    if set(attempt) != required_attempt or attempt_raw != _canonical(attempt):
        raise M401RAdapterError("M401 attempt record is incomplete or not canonical UTF-8 JSON")
    if (
        attempt.get("schema_version") != "task5-repair-gate-attempt.v1"
        or attempt.get("gate") != "M401"
        or attempt.get("attempt_id") != attempt_root.name
        or attempt.get("material_id") != packet.get("material_id")
        or attempt.get("status") != "passed"
        or attempt.get("exit_code") != 0
        or attempt.get("reason_code") != "NONE"
        or attempt.get("inverse_patch_ref") != "inverse.patch"
        or attempt.get("before_snapshot") != attempt.get("before_sha256")
        or attempt.get("after_snapshot") != attempt.get("after_sha256")
        or attempt.get("inverse_base_after_snapshot") != attempt.get("after_sha256")
    ):
        raise M401RAdapterError("M401 attempt record is not passed or is not bound to the packet")
    if inverse_path.is_symlink() or not inverse_path.is_file() or _sha_bytes(inverse_path) != attempt.get("inverse_patch_sha256"):
        raise M401RAdapterError("M401 inverse patch is missing or hash-mismatched")
    if packet.get("run_root_sha256") and attempt.get("after_sha256") != packet.get("run_root_sha256"):
        raise M401RAdapterError("M401 attempt after hash does not match packet run-root hash")
    required_receipt = {
        "schema_version", "gate", "attempt_id", "command", "command_sha256",
        "fixture_bundle_ref", "fixture_bundle_sha256", "fixture_manifest_sha256",
        "run_root_ref", "run_root_sha256", "packet_ref", "packet_sha256",
        "snapshot_tree", "material_id", "exit_code", "status", "reason_code",
    }
    if set(receipt) != required_receipt or receipt.get("schema_version") != "task5-m401-attempt-receipt.v1" or receipt_raw != _canonical(receipt):
        raise M401RAdapterError("M401 attempt receipt is incomplete")
    if receipt.get("gate") != "M401" or receipt.get("attempt_id") != attempt_root.name or receipt.get("packet_ref") != "M401-evidence-packet.json" or receipt.get("status") != "passed" or receipt.get("exit_code") != 0 or receipt.get("reason_code") != "NONE":
        raise M401RAdapterError("M401 attempt receipt is not passed")
    if (
        receipt.get("packet_sha256") != _sha(packet_raw)
        or receipt.get("snapshot_tree") != packet.get("snapshot_tree")
        or receipt.get("material_id") != packet.get("material_id")
        or receipt.get("run_root_sha256") != attempt.get("after_sha256")
        or attempt.get("attempt_id") != receipt.get("attempt_id")
    ):
        raise M401RAdapterError("M401 packet/attempt receipt identity mismatch")
    return packet, packet_raw, receipt, receipt_raw


def _validate_review_source(
    *,
    task_root: Path,
    task_id: str,
    snapshot_tree: str,
    material_id: str,
    result_path: Path,
    attempt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    result, result_raw = _read_json(result_path, label="WorkflowHub review result")
    attempt, attempt_raw = _read_json(attempt_path, label="WorkflowHub review attempt")
    if result.get("version") != REVIEW_SCHEMA or result.get("task_id") != task_id or result.get("stage") != "build-code" or result.get("review_kind") != REVIEW_KIND:
        raise M401RAdapterError("WorkflowHub review result identity is invalid")
    if not isinstance(result.get("attempt_ref"), str) or not result["attempt_ref"].strip():
        raise M401RAdapterError("WorkflowHub review result attempt ref is missing")
    if result_raw != _workflowhub_canonical(result):
        raise M401RAdapterError("WorkflowHub review result is not canonical WorkflowHub JSON")
    if result.get("snapshot_tree") != snapshot_tree or result.get("material_id") != material_id:
        raise M401RAdapterError("WorkflowHub review result is not bound to current M401 snapshot/material")
    projection = result.get("semantic_projection")
    if (
        not isinstance(projection, Mapping)
        or projection.get("projection_version") != "wh-review-semantic-projection.v1"
        or not isinstance(projection.get("surface"), str)
        or projection.get("surface") != "mini-task/implementation"
        or not isinstance(projection.get("contract_id"), str)
        or not projection.get("contract_id", "").strip()
        or not isinstance(projection.get("contract_hash"), str)
        or not SHA256.fullmatch(projection.get("contract_hash", ""))
        or not isinstance(projection.get("semantic_hash"), str)
        or not SHA256.fullmatch(projection.get("semantic_hash", ""))
    ):
        raise M401RAdapterError("WorkflowHub review result contract identity is missing or invalid")
    attempt_projection = attempt.get("semantic_projection")
    if attempt_projection != projection:
        raise M401RAdapterError("WorkflowHub review result/attempt contract identity mismatch")
    if attempt_raw != _workflowhub_canonical(attempt):
        raise M401RAdapterError("WorkflowHub review attempt is not canonical WorkflowHub JSON")
    if attempt.get("version") != "wh-review-attempt.v1" or attempt.get("task_id") != task_id or attempt.get("stage") != "build-code" or attempt.get("review_kind") != REVIEW_KIND or attempt.get("snapshot_tree") != snapshot_tree or attempt.get("material_id") != material_id:
        raise M401RAdapterError("WorkflowHub review attempt identity is stale or mismatched")
    if not isinstance(attempt.get("attempt_id"), str) or attempt_path.parent.name != attempt["attempt_id"]:
        raise M401RAdapterError("WorkflowHub review attempt path identity is invalid")
    if attempt.get("terminal_status") != "semantic" or attempt.get("error") is not None:
        raise M401RAdapterError("WorkflowHub review attempt is not terminal semantic")
    if not isinstance(result.get("findings"), list):
        raise M401RAdapterError("WorkflowHub review result findings must be a list")
    provider_results = result.get("provider_results")
    provider_attempts = attempt.get("provider_attempts")
    if (
        not isinstance(provider_results, list)
        or not provider_results
        or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("provider"), str)
            or not item.get("provider", "").strip()
            or not isinstance(item.get("output"), Mapping)
            or not isinstance(item["output"].get("findings"), list)
            for item in provider_results
        )
        or not isinstance(provider_attempts, list)
        or not provider_attempts
        or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("provider"), str)
            or item.get("status") != "completed"
            or item.get("error") is not None
            or not isinstance(item.get("output_ref"), str)
            or not item.get("output_ref", "").strip()
            for item in provider_attempts
        )
        or [item["provider"] for item in provider_results] != [item["provider"] for item in provider_attempts]
    ):
        raise M401RAdapterError("WorkflowHub review provider results are incomplete")
    for provider_result, provider_attempt in zip(provider_results, provider_attempts):
        output_ref = provider_attempt["output_ref"]
        output_path = Path(output_ref)
        if output_path.is_absolute():
            raise M401RAdapterError("WorkflowHub provider output ref must be repository-relative")
        output_path = (task_root / output_path).resolve()
        _relative(task_root, output_path)
        output, _ = _read_json(output_path, label="WorkflowHub provider output")
        if (
            output.get("schema_version") != "wh-review-provider-output.v1"
            or output.get("task_id") != task_id
            or output.get("stage") != "build-code"
            or output.get("attempt_id") != attempt.get("attempt_id")
            or output.get("provider") != provider_attempt.get("provider")
            or not isinstance(output.get("content"), str)
            or output.get("content_hash") != _sha(output["content"].encode("utf-8"))
        ):
            raise M401RAdapterError("WorkflowHub provider output provenance is invalid")
        try:
            provider_content = json.loads(output["content"])
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise M401RAdapterError("WorkflowHub provider output content is not JSON") from error
        if not isinstance(provider_content, Mapping) or not isinstance(provider_content.get("findings"), list):
            raise M401RAdapterError("WorkflowHub provider output findings are invalid")
        if not isinstance(provider_result.get("output"), Mapping) or not isinstance(provider_result["output"].get("findings"), list):
            raise M401RAdapterError("WorkflowHub provider result findings are invalid")
    if result.get("attempt_ref") and str(attempt.get("attempt_id")) not in str(result.get("attempt_ref")):
        raise M401RAdapterError("WorkflowHub review result is not bound to the supplied attempt")
    return result, attempt, result_raw, attempt_raw


def _build_review_projection(
    *,
    result: Mapping[str, Any],
    attempt: Mapping[str, Any],
    dispositions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the Task5 result projection from authenticated WorkflowHub facts.

    The generic WorkflowHub record remains the source of truth and is retained
    through the handoff refs.  M401-R's local result has its own frozen schema;
    all fields below are copied from, or deterministically derived from, the
    already-bound result/attempt and disposition set.
    """

    return {
        "schema_version": REVIEW_PROJECTION_SCHEMA,
        "task_id": result["task_id"],
        "stage": result["stage"],
        "review_kind": result["review_kind"],
        "review_attempt_id": attempt["attempt_id"],
        "review_outcome": "available",
        "terminal_status": attempt["terminal_status"],
        "terminal_clean": True,
        "findings": result["findings"],
        "finding_dispositions": [dict(item) for item in dispositions],
        "snapshot_tree": result["snapshot_tree"],
        "material_id": result["material_id"],
        "contract_id": result["semantic_projection"]["contract_id"],
        "contract_hash": result["semantic_projection"]["contract_hash"],
        "semantic_hash": result["semantic_projection"]["semantic_hash"],
    }


def _validate_existing_m401_r_attempt(
    attempt_dir: Path,
    *,
    attempt_id: str,
    material_id: str,
    projected_result_raw: bytes,
    receipt_raw: bytes,
) -> None:
    """Validate an immutable local attempt before resuming promotion.

    This is deliberately byte-bound: a resumed promotion must consume the
    exact attempt that was already written, never regenerate a replacement
    review result or receipt under the same attempt id.
    """

    if attempt_dir.is_symlink() or not attempt_dir.is_dir():
        raise M401RAdapterError(f"M401-R attempt is missing: {attempt_dir}")
    expected_names = {"review-result.json", "M401-R-review-receipt.json", "attempt.json", "inverse.patch"}
    actual_names = {path.name for path in attempt_dir.iterdir()}
    if actual_names != expected_names:
        raise M401RAdapterError("existing M401-R attempt has an unexpected file set")

    local_result = attempt_dir / "review-result.json"
    local_receipt = attempt_dir / "M401-R-review-receipt.json"
    if local_result.read_bytes() != projected_result_raw:
        raise M401RAdapterError("existing M401-R review result bytes differ from authenticated projection")
    if local_receipt.read_bytes() != receipt_raw:
        raise M401RAdapterError("existing M401-R receipt bytes differ from authenticated receipt")

    attempt_record, attempt_raw = _read_json(attempt_dir / "attempt.json", label="existing M401-R attempt")
    required = {
        "schema_version", "gate", "attempt_id", "attempt_seq", "material_id", "command",
        "command_sha256", "before_snapshot", "after_snapshot", "changed_paths",
        "before_sha256", "after_sha256", "patch_sha256", "inverse_patch_ref",
        "inverse_patch_sha256", "inverse_base_after_snapshot", "run_root_ref", "exit_code",
        "status", "reason_code",
    }
    if set(attempt_record) != required or attempt_raw != _canonical(attempt_record):
        raise M401RAdapterError("existing M401-R attempt record is incomplete or not canonical")
    changed_files = {
        "review-result.json": projected_result_raw,
        "M401-R-review-receipt.json": receipt_raw,
    }
    changed_paths = [
        {
            "path": relative,
            "before_sha256": _sha(b""),
            "after_sha256": _sha(data),
        }
        for relative, data in sorted(changed_files.items(), key=lambda item: item[0].encode("utf-8"))
    ]
    inverse_path = attempt_dir / "inverse.patch"
    if (
        attempt_record.get("schema_version") != "task5-repair-gate-attempt.v1"
        or attempt_record.get("gate") != "M401-R"
        or attempt_record.get("attempt_id") != attempt_id
        or attempt_record.get("attempt_seq") != 1
        or attempt_record.get("material_id") != material_id
        or attempt_record.get("changed_paths") != changed_paths
        or attempt_record.get("before_snapshot") != _snapshot({})
        or attempt_record.get("before_sha256") != _snapshot({})
        or attempt_record.get("after_snapshot") != _snapshot(changed_files)
        or attempt_record.get("after_sha256") != _snapshot(changed_files)
        or attempt_record.get("patch_sha256") != _sha(_canonical(changed_paths))
        or attempt_record.get("inverse_patch_ref") != "inverse.patch"
        or attempt_record.get("inverse_base_after_snapshot") != _snapshot(changed_files)
        or attempt_record.get("run_root_ref") is not None
        or attempt_record.get("exit_code") != 0
        or attempt_record.get("status") != "passed"
        or attempt_record.get("reason_code") != "NONE"
        or inverse_path.is_symlink()
        or not inverse_path.is_file()
        or _sha_bytes(inverse_path) != attempt_record.get("inverse_patch_sha256")
    ):
        raise M401RAdapterError("existing M401-R attempt is not a passed authenticated attempt")
    _verify_inverse_patch(attempt_dir, inverse_path)


def _validate_dispositions(findings: Sequence[Any], value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise M401RAdapterError("finding dispositions must be a JSON list")
    finding_ids: list[str] = []
    for finding in findings:
        if not isinstance(finding, Mapping) or not isinstance(finding.get("id"), str) or not finding["id"].strip():
            raise M401RAdapterError("WorkflowHub finding has no stable id")
        finding_ids.append(finding["id"])
    if len(set(finding_ids)) != len(finding_ids):
        raise M401RAdapterError("WorkflowHub findings repeat an id")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) - {"finding_id", "status", "owner", "consequence", "next_action", "evidence_ref", "original_fact", "consumer", "retain_or_delete", "source"}:
            raise M401RAdapterError("finding disposition contains unsupported fields")
        finding_id = item.get("finding_id")
        if finding_id not in finding_ids or finding_id in seen:
            raise M401RAdapterError("finding disposition does not match exactly one review finding")
        if item.get("status") not in DISPOSITION_STATUSES:
            raise M401RAdapterError("finding disposition status is invalid")
        seen.add(finding_id)
        normalized.append(dict(item))
    if seen != set(finding_ids):
        missing = sorted(set(finding_ids) - seen)
        raise M401RAdapterError(f"finding dispositions are incomplete: {', '.join(missing)}")
    return normalized


def _runtime_contract(task_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    authority = _load_m402_runtime_authority(task_root)
    semantic = json.loads((task_root / "config" / "task5-semantic-frame-v1.json").read_text(encoding="utf-8"))
    semantic_hash = next(
        item["canonical_sha256"]
        for item in json.loads((task_root / "config" / "task5-runtime-authority-map-v1.json").read_text(encoding="utf-8"))["authorities"]
        if item["key"] == "semantic_frame"
    )
    runtime = {
        "runtime_contract_id": authority["runtime_contract_id"],
        "runtime_contract_hash": authority["derived_runtime_contract_hash"],
        "semantic_contract_id": semantic["frame_id"],
        "semantic_contract_hash": semantic_hash,
    }
    return runtime, authority


def promote_m401_r(
    *,
    task_root: Path,
    m401_attempt: Path,
    review_result: Path,
    review_attempt: Path,
    review_report: Path,
    finding_dispositions: Path,
    task_id: str = TASK_ID,
    project_name: str = "KnowledgeDigest",
    worktree: Path | None = None,
    writer: str = "KnowledgeDigest M401-R host adapter",
    adapter: str = "workflowhub-task-kernel",
    resume_existing_attempt: bool = False,
    replace_existing_promotion: bool = False,
) -> dict[str, str]:
    """Promote one current, authenticated semantic review.

    The normal path is create-only.  Recovery after a promotion-view conflict
    must explicitly opt into both ``resume_existing_attempt`` and
    ``replace_existing_promotion``; the existing attempt is revalidated by
    bytes before any fixed view is replaced.
    """

    if replace_existing_promotion and not resume_existing_attempt:
        raise M401RAdapterError(
            "replace_existing_promotion requires resume_existing_attempt"
        )

    task_root = Path(task_root).resolve()
    packet, packet_raw, m401_receipt, m401_receipt_raw = _validate_m401_attempt(task_root, Path(m401_attempt))
    result, attempt, result_raw, attempt_raw = _validate_review_source(
        task_root=task_root,
        task_id=task_id,
        snapshot_tree=str(packet["snapshot_tree"]),
        material_id=str(packet["material_id"]),
        result_path=Path(review_result),
        attempt_path=Path(review_attempt),
    )
    report_path = Path(review_report).expanduser()
    if report_path.is_symlink() or not report_path.is_file():
        raise M401RAdapterError(f"WorkflowHub review report is missing: {report_path}")
    report_raw = report_path.read_bytes()
    result_ref = _relative(task_root, Path(review_result).resolve())
    attempt_ref = _relative(task_root, Path(review_attempt).resolve())
    report_ref = _relative(task_root, report_path.resolve())
    if result.get("attempt_ref") != attempt_ref or result.get("report_ref") != report_ref:
        raise M401RAdapterError("WorkflowHub review result refs do not match supplied authenticated records")
    dispositions_ref = _relative(task_root, Path(finding_dispositions).resolve())
    dispositions_value, _ = _read_json_value(Path(finding_dispositions), label="finding dispositions")
    dispositions = _validate_dispositions(result["findings"], dispositions_value if isinstance(dispositions_value, list) else dispositions_value.get("finding_dispositions") if isinstance(dispositions_value, dict) else None)
    projected_result = _build_review_projection(result=result, attempt=attempt, dispositions=dispositions)
    projected_result_raw = _canonical(projected_result)

    attempt_id = str(attempt.get("attempt_id") or "").strip()
    if not attempt_id:
        raise M401RAdapterError("WorkflowHub review attempt_id is missing")
    attempt_dir = task_root / "quality" / "evidence" / "task5" / "repair-gates" / "attempts" / attempt_id / "M401-R"
    attempt_preexisted = attempt_dir.exists()
    if attempt_preexisted and not resume_existing_attempt:
        raise M401RAdapterError(f"M401-R attempt already exists: {attempt_dir}")
    created: list[Path] = []
    try:
        packet_ref = _relative(task_root, Path(m401_attempt).resolve() / "M401" / "M401-evidence-packet.json")
        source_receipt_ref = _relative(task_root, Path(m401_attempt).resolve() / "M401" / "attempt-receipt.json")
        local_result = attempt_dir / "review-result.json"
        local_result_ref = _relative(task_root, local_result)
        receipt = {
            "schema_version": M401_R_SCHEMA,
            "review_kind": REVIEW_KIND,
            "m401_packet_ref": packet_ref,
            "m401_packet_sha256": _sha(packet_raw),
            "review_result_ref": local_result_ref,
            "review_result_sha256": _sha(projected_result_raw),
            "source_receipt_ref": source_receipt_ref,
            "source_receipt_sha256": _sha(m401_receipt_raw),
            "snapshot_tree": packet["snapshot_tree"],
            "material_id": packet["material_id"],
            "terminal_status": "semantic",
            "terminal_clean": True,
            "all_findings_disposed": True,
            "finding_dispositions": dispositions,
            "outcome": "available",
            "status": "passed",
            "reason_code": "NONE",
        }
        if set(receipt) != M401_R_FIELDS:
            raise M401RAdapterError("internal M401-R receipt field contract drift")
        local_receipt = attempt_dir / "M401-R-review-receipt.json"
        receipt_raw = _canonical(receipt)

        changed_files = {
            local_result.name: projected_result_raw,
            local_receipt.name: receipt_raw,
        }
        if attempt_preexisted:
            _validate_existing_m401_r_attempt(
                attempt_dir,
                attempt_id=attempt_id,
                material_id=str(packet["material_id"]),
                projected_result_raw=projected_result_raw,
                receipt_raw=receipt_raw,
            )
        else:
            attempt_dir.mkdir(parents=True)
            _write_exclusive(local_result, projected_result_raw)
            created.append(local_result)
            changed_paths = [
                {
                    "path": relative,
                    "before_sha256": _sha(b""),
                    "after_sha256": _sha(data),
                }
                for relative, data in sorted(changed_files.items(), key=lambda item: item[0].encode("utf-8"))
            ]
            inverse_patch = _creation_patch(changed_files)
            inverse_path = attempt_dir / "inverse.patch"
            _write_exclusive(local_receipt, receipt_raw)
            created.append(local_receipt)
            _write_exclusive(inverse_path, inverse_patch)
            created.append(inverse_path)
            _verify_inverse_patch(attempt_dir, inverse_path)
            before_snapshot = _snapshot({})
            after_snapshot = _snapshot(changed_files)
            command = json.dumps(
                ["workflowhub-task-kernel", "promote-m401-r", result_ref, attempt_ref, report_ref, dispositions_ref],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            attempt_record = {
                "schema_version": "task5-repair-gate-attempt.v1",
                "gate": "M401-R",
                "attempt_id": attempt_id,
                "attempt_seq": 1,
                "material_id": packet["material_id"],
                "command": command,
                "command_sha256": _sha(command.encode("utf-8")),
                "before_snapshot": before_snapshot,
                "after_snapshot": after_snapshot,
                "changed_paths": changed_paths,
                "before_sha256": before_snapshot,
                "after_sha256": after_snapshot,
                "patch_sha256": _sha(_canonical(changed_paths)),
                "inverse_patch_ref": "inverse.patch",
                "inverse_patch_sha256": _sha(inverse_patch),
                "inverse_base_after_snapshot": after_snapshot,
                "run_root_ref": None,
                "exit_code": 0,
                "status": "passed",
                "reason_code": "NONE",
            }
            attempt_path_local = attempt_dir / "attempt.json"
            _write_exclusive(attempt_path_local, _canonical(attempt_record))
            created.append(attempt_path_local)

        runtime, _ = _runtime_contract(task_root)
        implementation = {
            "review_kind": REVIEW_KIND,
            "result_ref": result_ref,
            "result_sha256": _sha(result_raw),
            "attempt_ref": attempt_ref,
            "attempt_sha256": _sha(attempt_raw),
            "report_ref": report_ref,
            "report_sha256": _sha(report_raw),
            "outcome": "available",
            "terminal_status": "semantic",
            "terminal_clean": True,
            "finding_dispositions_ref": dispositions_ref,
            "finding_dispositions_sha256": _sha(Path(finding_dispositions).read_bytes()),
            "all_findings_disposed": True,
            "m401_packet_sha256": _sha(packet_raw),
        }
        current = {
            "task_id": task_id,
            "project_name": project_name,
            "stage": "build-code",
            "snapshot_tree": packet["snapshot_tree"],
            "material_id": packet["material_id"],
            "worktree": str((worktree or task_root).resolve()),
        }
        runtime = {
            **runtime,
            "m401_packet_ref": "quality/evidence/task5/M401-evidence-packet.json",
            "m401_packet_sha256": _sha(packet_raw),
            "m401_r_receipt_ref": "quality/evidence/task5/M401-R-review-receipt.json",
            "m401_r_receipt_sha256": _sha(receipt_raw),
        }
        attestation = {"writer": writer, "adapter": adapter, "authenticated": True}
        attestation["attestation_sha256"] = _sha(_canonical(attestation))
        handoff = {
            "schema_version": HANDOFF_SCHEMA,
            "handoff_kind": "implementation",
            "task_id": task_id,
            "project_name": project_name,
            "stage": "build-code",
            "review_kind": REVIEW_KIND,
            "handoff_ref": "quality/evidence/task5/workflowhub-implementation-handoff.json",
            "handoff_sha256": "",
            "parent_design_review": None,
            "implementation_review": implementation,
            "current": current,
            "runtime_contract": runtime,
            "writer_attestation": attestation,
        }
        handoff["handoff_sha256"] = _sha(_canonical({k: v for k, v in handoff.items() if k != "handoff_sha256"}))
        handoff_raw = _canonical(handoff)
        promoted_packet = task_root / "quality" / "evidence" / "task5" / "M401-evidence-packet.json"
        promoted_receipt = task_root / "quality" / "evidence" / "task5" / "M401-R-review-receipt.json"
        promoted_handoff = task_root / "quality" / "evidence" / "task5" / "workflowhub-implementation-handoff.json"
        # Validate with the final promotion path so the compiler resolves
        # relative managed refs against the repository root, while no
        # promotion bytes have been written yet.
        _validate_workflowhub_successor(promoted_handoff, handoff, handoff_raw, packet, packet_raw, receipt, receipt_raw)
        promotion_items = (
            (promoted_packet, packet_raw),
            (promoted_receipt, receipt_raw),
            (promoted_handoff, handoff_raw),
        )
        expected_promotion = dict(promotion_items)
        for path in expected_promotion:
            if path.exists() and path.read_bytes() != expected_promotion[path] and not replace_existing_promotion:
                raise M401RAdapterError(f"existing promotion has different bytes: {path}")
        if replace_existing_promotion:
            _replace_promotion_set(promotion_items)
        else:
            for path, data in promotion_items:
                if not path.exists():
                    _write_exclusive(path, data)
                    created.append(path)
        return {
            "attempt_id": attempt_id,
            "m401_packet_ref": _relative(task_root, promoted_packet),
            "m401_r_receipt_ref": _relative(task_root, promoted_receipt),
            "handoff_ref": _relative(task_root, promoted_handoff),
            "snapshot_tree": str(packet["snapshot_tree"]),
            "material_id": str(packet["material_id"]),
        }
    except Exception:
        # Keep the immutable attempt evidence for diagnosis; remove only
        # promotion bytes created by this invocation if validation failed.
        for path in reversed(created):
            if path in {task_root / "quality" / "evidence" / "task5" / "M401-evidence-packet.json", task_root / "quality" / "evidence" / "task5" / "M401-R-review-receipt.json", task_root / "quality" / "evidence" / "task5" / "workflowhub-implementation-handoff.json"}:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
        raise
