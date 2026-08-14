"""Atomic run progress and bounded whole-run heartbeat."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any


_ACTIVE_STATUS: "RunStatus | None" = None



def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


class RunStatus:
    """Persist progress without changing the main pipeline's exception flow."""

    def __init__(self, run_dir: Path, *, total_batches: int, heartbeat_seconds: int = 10) -> None:
        self.run_dir = run_dir
        self.progress_path = run_dir / "progress.json"
        self.total_batches = total_batches
        self.heartbeat_seconds = heartbeat_seconds
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._value: dict[str, Any] = {
            "schema_version": "knowledge-digest-run-progress.v1",
            "run_id": run_dir.name,
            "execution_status": "preflight",
            "phase": "preflight",
            "completed_batches": 0,
            "total_batches": total_batches,
            "succeeded_batches": 0,
            "failed_batches": 0,
            "provider_calls_observed": 0,
            "replay_calls": 0,
            "last_error": None,
            "last_update": time.time(),
            "last_update_reason": "created",
        }
        self._write("created")

    def _write(self, reason: str) -> None:
        with self._lock:
            self._value["last_update"] = time.time()
            self._value["last_update_reason"] = reason
            _atomic_json(self.progress_path, dict(self._value))
            if reason == "heartbeat":
                print(
                    "progress: "
                    f"phase={self._value['phase']} "
                    f"batches={self._value['completed_batches']}/{self._value['total_batches']} "
                    f"provider_calls={self._value['provider_calls_observed']} "
                    f"replays={self._value['replay_calls']}",
                    flush=True,
                )

    def update(self, *, reason: str, **fields: Any) -> None:
        with self._lock:
            self._value.update(fields)
        self._write(reason)

    def set_error(self, error: str) -> None:
        self.update(reason="error", last_error=error)

    def record_batch(self, *, provider_calls: int, replay_calls: int, failed: bool) -> None:
        with self._lock:
            self._value["completed_batches"] += 1
            self._value["provider_calls_observed"] += provider_calls
            self._value["replay_calls"] += replay_calls
            if failed:
                self._value["failed_batches"] += 1
            else:
                self._value["succeeded_batches"] += 1
        self._write("batch_finished")

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._value)

    def start(self) -> None:
        global _ACTIVE_STATUS
        self.update(reason="running", execution_status="running", phase="running")
        self._thread = threading.Thread(target=self._heartbeat, name=f"digest-heartbeat-{self.run_dir.name}", daemon=True)
        self._thread.start()
        _ACTIVE_STATUS = self

    def _heartbeat(self) -> None:
        while not self._stop.wait(self.heartbeat_seconds):
            try:
                self._write("heartbeat")
            except Exception:
                # A failed side-channel write must not replace the main error.
                continue

    def finish(self, *, status: str, phase: str, error: str | None = None) -> None:
        global _ACTIVE_STATUS
        self._stop.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=max(1, self.heartbeat_seconds))
        self.update(reason="finished", execution_status=status, phase=phase, last_error=error)
        if _ACTIVE_STATUS is self:
            _ACTIVE_STATUS = None


def finish_active(*, status: str, phase: str, error: str | None = None) -> None:
    active = _ACTIVE_STATUS
    if active is not None:
        active.finish(status=status, phase=phase, error=error)
