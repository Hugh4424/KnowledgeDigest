"""Small atomic publisher for a completed in-memory digest bundle."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping


class PublishError(RuntimeError):
    """The bundle could not be installed without risking an existing KB."""


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def commit(
    files: Mapping[str, bytes],
    kb_dir: Path,
    *,
    run_id: str | None = None,
    finalizer: Callable[[Path, str, str], Mapping[str, object]] | None = None,
    task5: bool = False,
    material_id: str | None = None,
) -> dict[str, object]:
    """Install one bundle with an exclusive lock and atomic directory rename.

    The lock is deliberately outside the target.  A competing run therefore
    fails before it can create a target or touch an existing one.  The lock
    contains only a short state record and is removed only when this publisher
    owns it; stale or foreign locks are never guessed away.
    """

    root = Path(kb_dir).expanduser()
    if not root.is_absolute():
        raise PublishError("knowledge-base path must be absolute")
    if root.exists() and (root.is_symlink() or not root.is_dir() or any(root.iterdir())):
        raise PublishError(f"knowledge-base path must be a new empty directory: {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    lock = root.parent / (f"{root.name}.task5.lock" if task5 else f".{root.name}.lock")
    legacy_lock = root.parent / f".{root.name}.lock"
    task5_lock = root.parent / f"{root.name}.task5.lock"
    run_token = str(run_id or uuid.uuid4().hex)
    owner_nonce = uuid.uuid4().hex[:20]
    stage = (
        root.parent / f"{root.name}.staging.{run_token}.{owner_nonce}"
        if task5
        else root.parent / f".{root.name}.staging-{run_token}-{uuid.uuid4().hex[:8]}"
    )
    lock_fd: int | None = None
    lock_owned = False
    lifecycle_state = "held"
    failure_path: Path | None = None

    def write_lock(state: str, **extra: object) -> None:
        nonlocal lifecycle_state
        lifecycle_state = state
        value = {
            "schema_version": "task5-output-lock.v1" if task5 else "knowledge-digest-publication-lock.v1",
            "task_id": "task5-reader-quality-compiler-redesign" if task5 else "knowledge-digest",
            "run_id": run_token,
            "material_id": material_id,
            "owner_nonce": owner_nonce,
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "state": state,
            "target": root.name,
            "output_realpath": str(root.resolve()),
            "staging_path": str(stage),
            "failure_evidence_path": None,
            **extra,
        }
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with lock.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

    def quarantine(reason: str) -> Path | None:
        nonlocal failure_path
        if not root.exists():
            return None
        target = root.parent / f"{root.name}.failure.{run_token}.{owner_nonce}"
        try:
            os.replace(root, target)
            bundle = target / "bundle"
            if bundle.exists():
                shutil.rmtree(bundle)
            failure = {
                "run_id": run_token,
                "state": "failed",
                "status": "failed",
                "reason_code": reason,
                "input_identity": {"run_id": run_token},
                "provider_identity": None,
                "observed_calls": None,
                "exit_code": 1,
                "audit_ref": None,
                "cleanup_result": {"bundle_removed": True, "failure_sink_written": True},
            }
            failure["canonical_sha256"] = hashlib.sha256(
                json.dumps(failure, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                .encode("utf-8")
                + b"\n"
            ).hexdigest()
            (target / "failure.json").write_text(
                json.dumps(failure, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            _fsync_file(target / "failure.json")
            _fsync_directory(target)
            failure_path = target
            return target
        except OSError:
            return None
    try:
        try:
            conflict = task5_lock if not task5 else legacy_lock
            if conflict.exists():
                raise PublishError(f"publication lock exists: {conflict}")
            lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            lock_owned = True
        except FileExistsError as error:
            raise PublishError(f"publication lock exists: {lock}") from error
        assert lock_fd is not None
        with os.fdopen(lock_fd, "w", encoding="utf-8") as handle:
            lock_fd = None
            handle.write(
                json.dumps(
                    {
                        "schema_version": "task5-output-lock.v1" if task5 else "knowledge-digest-publication-lock.v1",
                        "task_id": "task5-reader-quality-compiler-redesign" if task5 else "knowledge-digest",
                        "run_id": run_token,
                        "material_id": material_id,
                        "owner_nonce": owner_nonce,
                        "pid": os.getpid(),
                        "host": socket.gethostname(),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "state": "held",
                        "target": root.name,
                        "output_realpath": str(root.resolve()),
                        "staging_path": str(stage),
                        "failure_evidence_path": None,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        stage.mkdir(mode=0o700)
        manifest: dict[str, str] = {}
        for relative, content in sorted(files.items()):
            target = Path(relative)
            if target.is_absolute() or ".." in target.parts or not relative or "\\" in relative:
                raise PublishError(f"invalid output path: {relative}")
            if not isinstance(content, bytes):
                raise PublishError(f"output content must be bytes: {relative}")
            path = stage / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            _fsync_file(path)
            manifest[relative] = hashlib.sha256(content).hexdigest()
        manifest_hash = hashlib.sha256(
            "\n".join(
                f"{digest}  {relative}" for relative, digest in sorted(manifest.items())
            ).encode("utf-8")
        ).hexdigest()
        _fsync_directory(stage)
        if root.exists():
            raise PublishError(f"knowledge-base target appeared during publication: {root}")
        os.replace(stage, root)
        _fsync_directory(root.parent)
        if finalizer is not None:
            write_lock("rename_committed")
            write_lock("finalizing")
            try:
                final = dict(finalizer(root, run_token, owner_nonce))
            except Exception as error:
                quarantine(f"FINALIZE_EXCEPTION_{type(error).__name__}")
                if failure_path is None:
                    write_lock("publication_ambiguous", failure_evidence_path=None)
                    raise PublishError("publication finalization is ambiguous") from error
                write_lock("failed", failure_evidence_path=str(failure_path))
                return {
                    "committed": False,
                    "state": "failed",
                    "reason_code": f"FINALIZE_EXCEPTION_{type(error).__name__}",
                    "failure_path": str(failure_path),
                    "run_id": run_token,
                }
            if final.get("state") != "published":
                reason = str(final.get("reason_code") or "FINALIZE_FAILED")
                quarantine(reason)
                if failure_path is None:
                    write_lock("publication_ambiguous", failure_evidence_path=None)
                    raise PublishError("publication finalization is ambiguous")
                write_lock("failed", failure_evidence_path=str(failure_path))
                return {
                    "committed": False,
                    "state": "failed",
                    "reason_code": reason,
                    "failure_path": str(failure_path),
                    "run_id": run_token,
                    **final,
                }
            write_lock("published")
            return {
                "committed": True,
                "state": "published",
                "manifest_hash": manifest_hash,
                "run_id": run_token,
                **final,
            }
        lifecycle_state = "committed"
        return {
            "committed": True,
            "state": "committed",
            "manifest_hash": manifest_hash,
            "file_count": len(manifest),
            "run_id": run_token,
        }
    except PublishError:
        raise
    except OSError as error:
        raise PublishError(f"atomic publication failed: {type(error).__name__}") from error
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if lock_owned and lifecycle_state != "publication_ambiguous":
            try:
                lock.unlink()
                _fsync_directory(lock.parent)
            except FileNotFoundError:
                pass


__all__ = ["PublishError", "commit"]
