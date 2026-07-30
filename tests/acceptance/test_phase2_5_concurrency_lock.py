"""Phase 2.5 acceptance: one digest run at a time per knowledge base."""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _case(tmp_path: Path) -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(
        "---\n"
        "contract_version: phase2\n"
        "roots: [pages, _archive, _queues]\n"
        "why_field: why\n"
        "version_field: version\n"
        "publication_home: Home.md\n"
        "publication_index_root: indexes\n"
        "publication_categories:\n"
        "  - id: pending\n"
        "    title: 待归类\n"
        "    topic_dir: pages/待归类\n"
        "---\n",
        encoding="utf-8",
    )
    (new_dir / "items" / "note.md").write_text(
        "Concurrency guard keeps knowledge-base writes serialized.\n", encoding="utf-8"
    )
    (new_dir / "sources.jsonl").write_text(
        json.dumps(
            {
                "content_path": "note.md",
                "source_uri": "https://example.com/lock",
                "captured_at": "2026-07-26T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return new_dir, kb_dir


def _run_digest(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "knowledge_digest.cli", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_second_digest_fails_fast_while_lock_is_held(tmp_path: Path) -> None:
    """A real competing lock holder must make the CLI exit immediately, not wait."""
    new_dir, kb_dir = _case(tmp_path)
    lock_path = kb_dir / ".digest.lock"
    with lock_path.open("a+", encoding="utf-8") as holder:
        fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = _run_digest(str(new_dir), str(kb_dir))

    assert result.returncode == 1
    assert "stage=kb_lock" in result.stderr
    assert "another digest run is processing this knowledge base" in result.stderr
    assert str(lock_path) in result.stderr
    assert not (kb_dir / "pages").exists()


def test_lock_is_released_after_a_successful_run(tmp_path: Path) -> None:
    """The lock must not leak, so a later run can acquire it."""
    new_dir, kb_dir = _case(tmp_path)
    first = _run_digest(str(new_dir), str(kb_dir))
    assert first.returncode == 0, first.stderr

    lock_path = kb_dir / ".digest.lock"
    with lock_path.open("a+", encoding="utf-8") as probe:
        fcntl.flock(probe.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(probe.fileno(), fcntl.LOCK_UN)


def test_lock_is_released_when_the_run_raises(tmp_path: Path) -> None:
    """An exception inside the pipeline must still release the lock."""
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.errors import ValidationError
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.pipeline import audit_run

    new_dir, kb_dir = _case(tmp_path)
    paths = validate_paths(new_dir, kb_dir)
    (kb_dir / "_digest").write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        audit_run(paths, DigestSettings(), ("pages", "_archive", "_queues"), dry_run=False)

    lock_path = kb_dir / ".digest.lock"
    with lock_path.open("a+", encoding="utf-8") as probe:
        fcntl.flock(probe.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(probe.fileno(), fcntl.LOCK_UN)


def test_concurrent_digest_processes_do_not_both_commit(tmp_path: Path) -> None:
    """Two real processes racing the same kb: successes are serialized, never interleaved."""
    new_dir, kb_dir = _case(tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    command = [sys.executable, "-m", "knowledge_digest.cli", str(new_dir), str(kb_dir)]
    processes = [
        subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for _ in range(2)
    ]
    results = [process.communicate() for process in processes]
    codes = [process.returncode for process in processes]

    # Each process either commits (0) or is rejected by the lock (1); no other outcome.
    assert set(codes) <= {0, 1}, (codes, results)
    for code, (_stdout, stderr) in zip(codes, results):
        if code == 1:
            assert "another digest run is processing this knowledge base" in stderr
    # One run directory per process that actually held the lock.
    runs = sorted((kb_dir / "_digest" / "runs").iterdir())
    assert len(runs) == codes.count(0)
    assert codes.count(0) >= 1
