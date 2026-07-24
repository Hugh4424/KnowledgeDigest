"""Durable run identity, single-writer locking, and prepare state.

The recovery files live under ``kb_dir/_digest/recovery``.  They are audit
metadata, not knowledge-base content.  A run is considered safe to take over
only after it reached ``prepared`` or ``committing`` and its previous writer
and declared sub-processes are gone.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from uuid import uuid4

from .errors import ValidationError
from .jsonl import read_jsonl
from .paths import DigestPaths


RECOVERY_SCHEMA_VERSION = "recovery-v1"
RECOVERY_ROOT = "_digest/recovery"
SAFE_TAKEOVER_STATUSES = frozenset({"prepared", "committing"})
RECOVERY_STATUSES = frozenset({"preparing", "prepared", "committing", "committed", "failed"})
REQUIRED_STATE_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "input_manifest_hash",
        "status",
        "prepared_at",
        "committing_at",
        "committed_at",
        "plan_hash",
        "staged_outputs",
        "completed_outputs",
        "recovery_attempts",
        "last_error",
        "execution_id",
        "pid",
        "target_kb",
        "started_at",
        "child_pids",
    }
)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_optional(value: bytes | None) -> str | None:
    return _sha256_bytes(value) if value is not None else None


def sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _relative_file_records(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    if not root.is_dir():
        return records
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
            }
        )
    return records


def _source_records(paths: DigestPaths) -> list[dict[str, Any]]:
    source_path = paths.new_dir / "sources.jsonl"
    if not source_path.is_file():
        return []
    rows = read_jsonl(source_path)
    return sorted(
        rows,
        key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )


def build_input_manifest(
    paths: DigestPaths,
    settings: Any,
    roots: tuple[str, ...],
) -> dict[str, Any]:
    """Build a path-independent manifest for one digest input.

    Timestamps and absolute workspace paths are intentionally excluded.  The
    source manifest is canonicalized by row so harmless input ordering does
    not create a different run identity.
    """
    settings_value = asdict(settings) if hasattr(settings, "__dataclass_fields__") else dict(settings)
    sources = _source_records(paths)
    return {
        "schema_version": RECOVERY_SCHEMA_VERSION,
        "inputs": {
            "items": _relative_file_records(paths.items_dir),
            "sources": sources,
            "sources_manifest_hash": _sha256_bytes(_canonical(sources)),
        },
        "structure_sha256": sha256_file(paths.structure_path),
        "roots": list(roots),
        "settings": settings_value,
    }


def manifest_hash(manifest: dict[str, Any]) -> str:
    return _sha256_bytes(_canonical(manifest))


def stable_run_id(manifest: dict[str, Any]) -> str:
    """Return the stable run identity derived from the normalized manifest."""
    return f"run-{manifest_hash(manifest)[:32]}"


def new_execution_id() -> str:
    return str(uuid4())


@dataclass(frozen=True)
class RecoveryPaths:
    root: Path
    state: Path
    lock: Path
    staging: Path

    @classmethod
    def for_run(cls, kb_dir: Path, run_id: str) -> "RecoveryPaths":
        root = kb_dir / RECOVERY_ROOT / run_id
        return cls(root=root, state=root / "state.json", lock=root / "lock.json", staging=root / "staging")


@dataclass(frozen=True)
class LockHandle:
    run_id: str
    execution_id: str
    path: Path


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValidationError("recovery", path, f"RECOVERY_STATE_INVALID: durable write failed: {error}") from error


def _read_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("recovery", path, f"RECOVERY_STATE_INVALID: {label} is not valid JSON") from error
    if not isinstance(value, dict):
        raise ValidationError("recovery", path, f"RECOVERY_STATE_INVALID: {label} must be an object")
    return value


def _pid_alive(pid: object) -> bool:
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _processes_alive(pids: Iterable[object]) -> bool:
    return any(_pid_alive(pid) for pid in pids)


def validate_recovery_state(state: dict[str, Any], *, run_id: str | None = None) -> dict[str, Any]:
    missing = sorted(REQUIRED_STATE_FIELDS - set(state))
    if missing:
        raise ValidationError("recovery", state.get("run_id", "state"), f"RECOVERY_STATE_INVALID: missing fields {', '.join(missing)}")
    if state.get("schema_version") != RECOVERY_SCHEMA_VERSION:
        raise ValidationError("recovery", state.get("run_id", "state"), "RECOVERY_STATE_INVALID: unsupported schema version")
    if run_id is not None and state.get("run_id") != run_id:
        raise ValidationError("recovery", run_id, "RECOVERY_STATE_INVALID: run_id mismatch")
    if state.get("status") not in RECOVERY_STATUSES:
        raise ValidationError("recovery", state.get("run_id", "state"), "RECOVERY_STATE_INVALID: unsupported state")
    if not isinstance(state.get("staged_outputs"), list) or not isinstance(state.get("completed_outputs"), list):
        raise ValidationError("recovery", state.get("run_id", "state"), "RECOVERY_STATE_INVALID: output lists must be arrays")
    if isinstance(state.get("recovery_attempts"), bool) or not isinstance(state.get("recovery_attempts"), int) or state["recovery_attempts"] < 0:
        raise ValidationError("recovery", state.get("run_id", "state"), "RECOVERY_STATE_INVALID: recovery_attempts must be a non-negative integer")
    seen_targets: set[str] = set()
    for output in state["staged_outputs"]:
        normalized = normalize_staged_output(output)
        if normalized["relative_target"] in seen_targets:
            raise ValidationError(
                "recovery",
                state.get("run_id", "state"),
                "RECOVERY_STATE_INVALID: staged output targets must be unique",
            )
        seen_targets.add(normalized["relative_target"])
    return state


def _safe_relative(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("recovery", label, "RECOVERY_STATE_INVALID: relative target is required")
    candidate = Path(value)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise ValidationError("recovery", value, "RECOVERY_STATE_INVALID: path must be relative to kb_dir")
    return candidate.as_posix()


def normalize_staged_output(output: object) -> dict[str, Any]:
    """Normalize Phase 2's output shape to the durable commit contract.

    ``target_path``/``action``/``size`` remain accepted so prepared states
    written by Phase 2 can be resumed without regenerating their outputs.
    """
    if not isinstance(output, dict):
        raise ValidationError("recovery", "staged_outputs", "RECOVERY_STATE_INVALID: output entry must be an object")
    operation = output.get("operation", output.get("action"))
    if operation not in {"replace", "delete"}:
        raise ValidationError("recovery", output.get("relative_target", output.get("target_path", "output")), "RECOVERY_STATE_INVALID: unsupported output operation")
    relative_target = _safe_relative(
        output.get("relative_target", output.get("target_path")),
        label="staged output",
    )
    staged_path = output.get("staged_path")
    if staged_path is not None and (not isinstance(staged_path, str) or not staged_path.strip()):
        raise ValidationError("recovery", relative_target, "RECOVERY_STATE_INVALID: staged path must be relative or null")
    if isinstance(staged_path, str):
        staged_path = _safe_relative(staged_path, label="staged output")
    before_sha256 = output.get("before_sha256")
    after_sha256 = output.get("after_sha256")
    for name, value in (("before_sha256", before_sha256), ("after_sha256", after_sha256)):
        if value is not None and (not isinstance(value, str) or len(value) != 64):
            raise ValidationError("recovery", relative_target, f"RECOVERY_STATE_INVALID: {name} must be a SHA-256 hex string or null")
    if operation == "delete" and (staged_path is not None or after_sha256 is not None):
        raise ValidationError("recovery", relative_target, "RECOVERY_STATE_INVALID: delete tombstone must not contain staged output or after hash")
    size_value = output.get("size_bytes", output.get("size", 0 if operation == "delete" else None))
    if isinstance(size_value, bool) or not isinstance(size_value, int) or size_value < 0:
        raise ValidationError("recovery", relative_target, "RECOVERY_STATE_INVALID: output size must be a non-negative integer")
    return {
        "operation": operation,
        "kind": str(output.get("kind") or "formal_output"),
        "relative_target": relative_target,
        "staged_path": staged_path,
        "size_bytes": size_value,
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
        "status": output.get("status", "pending"),
    }


def load_recovery_state(kb_dir: Path, run_id: str) -> dict[str, Any] | None:
    paths = RecoveryPaths.for_run(kb_dir, run_id)
    if not paths.state.exists():
        return None
    try:
        return validate_recovery_state(_read_json(paths.state, label="recovery state"), run_id=run_id)
    except ValidationError as error:
        if "RECOVERY_STATE_INVALID" in str(error):
            raise ValidationError("recovery", kb_dir, error.reason) from error
        raise


def _new_state(
    *,
    run_id: str,
    input_manifest_hash: str,
    execution_id: str,
    target_kb: Path,
    child_pids: list[int],
) -> dict[str, Any]:
    return {
        "schema_version": RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "input_manifest_hash": input_manifest_hash,
        "status": "preparing",
        "prepared_at": None,
        "committing_at": None,
        "committed_at": None,
        "plan_hash": None,
        "staged_outputs": [],
        "completed_outputs": [],
        "recovery_attempts": 0,
        "last_error": None,
        "execution_id": execution_id,
        "pid": os.getpid(),
        "target_kb": str(target_kb),
        "started_at": _now(),
        "child_pids": child_pids,
    }


def acquire_lock(
    kb_dir: Path,
    run_id: str,
    *,
    input_manifest_hash: str,
    target_kb: Path | None = None,
    child_pids: Iterable[int] = (),
) -> tuple[LockHandle, dict[str, Any]]:
    """Acquire the run lock or safely take over a prepared stale run."""
    paths = RecoveryPaths.for_run(kb_dir, run_id)
    paths.root.mkdir(parents=True, exist_ok=True)
    existing_state = load_recovery_state(kb_dir, run_id)
    if existing_state and existing_state.get("input_manifest_hash") != input_manifest_hash:
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: input manifest does not match run")

    existing_lock: dict[str, Any] | None = None
    if paths.lock.exists():
        try:
            existing_lock = _read_json(paths.lock, label="writer lock")
        except ValidationError as error:
            raise ValidationError("recovery", kb_dir, error.reason) from error
        if existing_lock.get("schema_version") != RECOVERY_SCHEMA_VERSION or existing_lock.get("run_id") != run_id:
            raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: writer lock identity does not match run")
        owner_alive = _pid_alive(existing_lock.get("pid")) or _processes_alive(existing_lock.get("child_pids", []))
        if owner_alive:
            raise ValidationError("recovery", kb_dir, "CONCURRENT_WRITER_NOT_ALLOWED: another writer owns this run")
        if existing_state is None or existing_state.get("status") not in SAFE_TAKEOVER_STATUSES:
            raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: stale writer is not safely recoverable")
        # The state and process checks above are the proof required before
        # removing a leftover lock.  O_EXCL below still arbitrates a race with
        # another safe taker-over.
        paths.lock.unlink(missing_ok=True)

    if existing_state and existing_state.get("status") not in SAFE_TAKEOVER_STATUSES:
        if existing_state.get("status") == "committed":
            raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: run is already committed")
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: run is not safely recoverable")

    execution_id = new_execution_id()
    lock = {
        "schema_version": RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "execution_id": execution_id,
        "pid": os.getpid(),
        "child_pids": sorted(set(int(pid) for pid in child_pids)),
        "started_at": _now(),
        "target_kb": str(target_kb or kb_dir),
    }
    # O_EXCL prevents two writers from replacing one another between reads.
    descriptor: int | None = None
    try:
        descriptor = os.open(paths.lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            json.dump(lock, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        directory_descriptor = os.open(paths.lock.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except FileExistsError:
        if descriptor is not None:
            os.close(descriptor)
        raise ValidationError("recovery", kb_dir, "CONCURRENT_WRITER_NOT_ALLOWED: another writer acquired the run lock")
    except OSError as error:
        if descriptor is not None:
            os.close(descriptor)
        raise ValidationError("recovery", paths.lock, f"RECOVERY_STATE_INVALID: cannot create writer lock: {error}") from error

    if existing_state is None:
        state = _new_state(
            run_id=run_id,
            input_manifest_hash=input_manifest_hash,
            execution_id=execution_id,
            target_kb=target_kb or kb_dir,
            child_pids=lock["child_pids"],
        )
    else:
        state = dict(existing_state)
        state.update(
            {
                "execution_id": execution_id,
                "pid": os.getpid(),
                "child_pids": lock["child_pids"],
                "started_at": lock["started_at"],
                "last_error": None,
                "recovery_attempts": int(existing_state["recovery_attempts"]) + 1,
            }
        )
    try:
        _atomic_json(paths.state, state)
    except Exception:
        paths.lock.unlink(missing_ok=True)
        raise
    return LockHandle(run_id, execution_id, paths.lock), state


def update_recovery_state(kb_dir: Path, state: dict[str, Any], **updates: Any) -> dict[str, Any]:
    updated = dict(state)
    updated.update(updates)
    validate_recovery_state(updated, run_id=str(updated.get("run_id")))
    paths = RecoveryPaths.for_run(kb_dir, str(updated["run_id"]))
    _atomic_json(paths.state, updated)
    return updated


def mark_prepared(
    kb_dir: Path,
    state: dict[str, Any],
    *,
    staged_outputs: list[dict[str, Any]],
    plan_hash: str,
) -> dict[str, Any]:
    normalized_outputs = [normalize_staged_output(output) for output in staged_outputs]
    return update_recovery_state(
        kb_dir,
        state,
        status="prepared",
        prepared_at=_now(),
        plan_hash=plan_hash,
        staged_outputs=normalized_outputs,
        completed_outputs=[],
        last_error=None,
    )


def record_recovery_error(kb_dir: Path, state: dict[str, Any], error: BaseException) -> dict[str, Any]:
    updates: dict[str, Any] = {"last_error": str(error)}
    if state.get("status") == "preparing":
        updates["status"] = "failed"
    return update_recovery_state(kb_dir, state, **updates)


def release_lock(handle: LockHandle) -> None:
    """Release only the lock owned by this execution."""
    try:
        current = _read_json(handle.path, label="writer lock")
    except ValidationError:
        return
    if current.get("execution_id") != handle.execution_id:
        return
    handle.path.unlink(missing_ok=True)


def write_staged_file(staging_root: Path, relative_target: str, content: bytes) -> str:
    relative_target = _safe_relative(relative_target, label="staged output")
    path = staging_root / "files" / relative_target
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValidationError("recovery", path, f"RECOVERY_STATE_INVALID: staging write failed: {error}") from error
    return path.relative_to(staging_root.parent).as_posix()


def output_plan_hash(outputs: list[dict[str, Any]]) -> str:
    material = []
    for output in outputs:
        row = normalize_staged_output(output)
        material.append(
            {
                key: row[key]
                for key in ("operation", "kind", "relative_target", "staged_path", "before_sha256", "after_sha256", "size_bytes")
            }
        )
    return _sha256_bytes(_canonical(material))


def _target_path(kb_dir: Path, relative_target: str) -> Path:
    relative_target = _safe_relative(relative_target, label="formal output")
    target = kb_dir / relative_target
    current = kb_dir
    for part in Path(relative_target).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: formal output parent must not be a symlink")
    return target


def _target_bytes(kb_dir: Path, relative_target: str) -> bytes | None:
    target = _target_path(kb_dir, relative_target)
    if not target.exists():
        return None
    if target.is_symlink() or not target.is_file():
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: formal output must be a regular file")
    return target.read_bytes()


def _atomic_replace(target: Path, content: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, target)
        directory_descriptor = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValidationError("recovery", target, f"RECOVERY_STATE_INVALID: commit replace failed: {error}") from error


def _unlink(target: Path) -> None:
    try:
        target.unlink()
        directory_descriptor = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as error:
        raise ValidationError("recovery", target, f"RECOVERY_STATE_INVALID: commit delete failed: {error}") from error


def _staged_bytes(recovery: RecoveryPaths, output: dict[str, Any], kb_dir: Path) -> bytes:
    staged_path = output.get("staged_path")
    if staged_path is None:
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: replace output has no staged path")
    candidate = (recovery.root / staged_path).resolve()
    if not candidate.is_relative_to(recovery.root.resolve()):
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: staged path escapes recovery directory")
    if not candidate.is_file():
        raise ValidationError("recovery", kb_dir, f"RECOVERY_OUTPUT_MISSING: staged output is missing: {output['relative_target']}")
    content = candidate.read_bytes()
    if len(content) != output["size_bytes"] or _sha256_bytes(content) != output["after_sha256"]:
        raise ValidationError("recovery", kb_dir, f"RECOVERY_OUTPUT_MISSING: staged output hash mismatch: {output['relative_target']}")
    return content


def commit_staged_outputs(
    kb_dir: Path,
    state: dict[str, Any],
    *,
    handle: LockHandle | None = None,
    on_output: Callable[[int, dict[str, Any]], None] | None = None,
    fail_after: int | None = None,
) -> dict[str, Any]:
    """Commit a prepared output list with before/after hash protection.

    The function is deliberately resumable: every completed item is durable
    before the next item is touched.  A caller that is terminated mid-loop
    leaves ``committing`` state for the next same-run invocation to continue.
    """
    validate_recovery_state(state, run_id=str(state.get("run_id")))
    if state.get("status") not in SAFE_TAKEOVER_STATUSES:
        if state.get("status") == "committed":
            return state
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: run is not prepared for commit")
    recovery = RecoveryPaths.for_run(kb_dir, str(state["run_id"]))
    if handle is not None and handle.execution_id != state.get("execution_id"):
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: commit execution does not own recovery state")
    if handle is not None:
        if not recovery.lock.exists():
            raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: commit lock is missing")
        lock = _read_json(recovery.lock, label="writer lock")
        if lock.get("execution_id") != handle.execution_id or lock.get("run_id") != state.get("run_id"):
            raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: commit lock identity does not match execution")
    outputs = [normalize_staged_output(output) for output in state["staged_outputs"]]
    if state.get("plan_hash") and output_plan_hash(outputs) != state["plan_hash"]:
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: output plan hash does not match state")
    completed = list(state.get("completed_outputs", []))
    state = update_recovery_state(kb_dir, state, status="committing", committing_at=state.get("committing_at") or _now(), last_error=None)
    for index, output in enumerate(outputs):
        current = _target_bytes(kb_dir, output["relative_target"])
        current_hash = _sha256_optional(current)
        if output["operation"] == "replace":
            staged = _staged_bytes(recovery, output, kb_dir)
            if current_hash == output["after_sha256"]:
                skipped = True
            elif current_hash == output["before_sha256"]:
                _atomic_replace(_target_path(kb_dir, output["relative_target"]), staged)
                skipped = False
            else:
                raise ValidationError("recovery", kb_dir, f"RECOVERY_STATE_INVALID: before/after hash conflict: {output['relative_target']}")
            observed_hash = output["after_sha256"]
        else:
            if current_hash is None:
                skipped = True
            elif current_hash == output["before_sha256"]:
                _unlink(_target_path(kb_dir, output["relative_target"]))
                skipped = False
            else:
                raise ValidationError("recovery", kb_dir, f"RECOVERY_STATE_INVALID: delete tombstone hash conflict: {output['relative_target']}")
            observed_hash = None
        completion = {
            **output,
            "status": "completed",
            "observed_sha256": observed_hash,
            "skipped": skipped,
        }
        completed = [item for item in completed if normalize_staged_output(item)["relative_target"] != output["relative_target"]]
        completed.append(completion)
        state = update_recovery_state(kb_dir, state, completed_outputs=completed, last_error=None)
        if on_output is not None:
            on_output(index, completion)
        if fail_after is not None and index + 1 >= fail_after:
            raise RuntimeError("simulated commit interruption")
    return update_recovery_state(
        kb_dir,
        state,
        status="committed",
        committed_at=_now(),
        completed_outputs=completed,
        last_error=None,
    )


def verify_committed_outputs(kb_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if a committed state no longer matches its durable outputs."""
    validate_recovery_state(state, run_id=str(state.get("run_id")))
    if state.get("status") != "committed":
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: run is not committed")
    outputs = [normalize_staged_output(output) for output in state["staged_outputs"]]
    if state.get("plan_hash") and output_plan_hash(outputs) != state["plan_hash"]:
        raise ValidationError("recovery", kb_dir, "RECOVERY_STATE_INVALID: output plan hash does not match state")
    recovery = RecoveryPaths.for_run(kb_dir, str(state["run_id"]))
    for output in outputs:
        relative_target = output["relative_target"]
        if output["operation"] == "replace":
            _staged_bytes(recovery, output, kb_dir)
            current = _target_bytes(kb_dir, relative_target)
            if _sha256_optional(current) != output["after_sha256"]:
                raise ValidationError(
                    "recovery",
                    kb_dir,
                    f"RECOVERY_STATE_INVALID: committed output hash mismatch: {relative_target}",
                )
        elif _target_bytes(kb_dir, relative_target) is not None:
            raise ValidationError(
                "recovery",
                kb_dir,
                f"RECOVERY_STATE_INVALID: committed tombstone target still exists: {relative_target}",
            )
    return state


# Names used by phase tests and older callers.
commit_run = commit_staged_outputs
resume_commit = commit_staged_outputs


# Short aliases for callers and acceptance tests.
compute_run_id = stable_run_id
recovery_paths = RecoveryPaths.for_run
