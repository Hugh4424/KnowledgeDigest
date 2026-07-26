"""Phase 2.5 B2 acceptance: append-only ledgers and archive-before-overwrite.

Every test here guards a data-loss path that used to truncate or reorder writes:
- claim-history.jsonl / records.jsonl must only ever grow (O_APPEND).
- pending-review.jsonl must merge, not truncate.
- Archives must be durable on disk before any target page is overwritten.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from knowledge_digest.errors import ValidationError
from knowledge_digest.jsonl import append_jsonl, read_jsonl
from knowledge_digest.paths import STRUCTURE_FILENAME


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_digest(*args: str) -> subprocess.CompletedProcess[str]:
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


def make_case(tmp_path: Path) -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    fields = [
        "contract_version: phase1",
        "roots: [pages, _archive, _queues]",
        "why_field: why",
        "version_field: version",
    ]
    (kb_dir / STRUCTURE_FILENAME).write_text("---\n" + "\n".join(fields) + "\n---\n", encoding="utf-8")
    return new_dir, kb_dir


def write_source(new_dir: Path, name: str, body: str, source_uri: str, **meta: object) -> None:
    (new_dir / "items" / name).write_text(body, encoding="utf-8")
    row = {"content_path": name, "source_uri": source_uri, "captured_at": "2026-07-22T00:00:00Z", **meta}
    (new_dir / "sources.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")


def lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_claim_history_grows_monotonically_and_keeps_first_run_lines(tmp_path: Path) -> None:
    """C1: two runs must never rewrite the first run's history lines."""
    new_dir, kb_dir = make_case(tmp_path)
    history_path = kb_dir / "_digest" / "claim-history.jsonl"

    write_source(new_dir, "good.md", "First run claim body.\n", "https://source.example/append")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    first_lines = lines(history_path)
    assert first_lines

    write_source(new_dir, "good.md", "Second run replaces the body.\n", "https://source.example/append")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    second_lines = lines(history_path)

    assert len(second_lines) > len(first_lines)
    # Append-only: the original bytes are still the file prefix, untouched.
    assert second_lines[: len(first_lines)] == first_lines
    texts = [json.loads(line).get("text") for line in second_lines]
    assert "First run claim body." in texts
    assert "Second run replaces the body." in texts


def test_previous_pending_entry_survives_a_run_whose_sources_pass(tmp_path: Path) -> None:
    """H5: pending-review.jsonl merges instead of truncating unrelated entries."""
    new_dir, kb_dir = make_case(tmp_path)
    pending_path = kb_dir / "_digest" / "pending-review.jsonl"

    write_source(new_dir, "keep.md", "Claim that will go pending.\n", "https://source.example/pending")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    write_source(
        new_dir,
        "keep.md",
        "Claim that will go pending.\n",
        "https://source.example/pending",
        source_status="failed",
    )
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    pending_after_failure = read_jsonl(pending_path)
    assert pending_after_failure
    stale_key = (
        pending_after_failure[0]["source_uri"],
        pending_after_failure[0]["fragment_locator"],
    )

    # A later run over a completely different, healthy source must not wipe it.
    write_source(new_dir, "other.md", "Unrelated healthy claim.\n", "https://source.example/other")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    kept = {(row["source_uri"], row["fragment_locator"]) for row in read_jsonl(pending_path)}
    assert stale_key in kept


def test_archive_is_durable_before_target_page_is_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """H2/H1: when the page write fails, the original is already whole in _archive."""
    from knowledge_digest import writeback as writeback_module

    new_dir, kb_dir = make_case(tmp_path)
    write_source(new_dir, "good.md", "Original page content to protect.\n", "https://source.example/archived")
    assert run_digest(str(new_dir), str(kb_dir)).returncode == 0
    page_path = next((kb_dir / "pages").rglob("*.md"))
    original = page_path.read_text(encoding="utf-8")

    real_atomic_write = writeback_module._atomic_write
    write_calls: list[Path] = []

    def fail_on_target(path: Path, content: str) -> None:
        write_calls.append(path)
        if "_archive" in Path(path).parts:
            real_atomic_write(path, content)
            return
        raise ValidationError("s5", path, "atomic write failed: injected target failure")

    monkeypatch.setattr(writeback_module, "_atomic_write", fail_on_target)

    from knowledge_digest.config import DigestSettings
    from knowledge_digest.kb_structure import parse_roots
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.pipeline import audit_run

    write_source(new_dir, "good.md", "Replacement content that must not land.\n", "https://source.example/archived")
    paths = validate_paths(new_dir, kb_dir)
    roots = parse_roots(paths.structure_path)
    with pytest.raises(ValidationError):
        audit_run(paths, DigestSettings(), roots, dry_run=False)

    assert write_calls, "_atomic_write was never called; stub was not exercised"
    assert any("_archive" not in path.parts for path in write_calls)

    # The failing write left the original in place and archived it in full.
    assert page_path.read_text(encoding="utf-8") == original
    archived = list((kb_dir / "_archive").rglob(page_path.name))
    assert archived, "pre-write archive must exist before the target write is attempted"
    assert any(candidate.read_text(encoding="utf-8") == original for candidate in archived)
    records = read_jsonl(kb_dir / "_archive" / "records.jsonl")
    assert any(record.get("full_content") == original for record in records)


def test_records_jsonl_keeps_earlier_lines_when_a_later_append_fails(tmp_path: Path) -> None:
    """C2: append_jsonl is O_APPEND, so an interrupted write cannot drop history."""
    path = tmp_path / "_archive" / "records.jsonl"
    append_jsonl(path, [{"claim_id": "a"}, {"claim_id": "b"}])
    before = lines(path)
    assert len(before) == 2

    class Exploding:
        """A record json.dumps refuses to serialize, aborting the append."""

    with pytest.raises(TypeError):
        append_jsonl(path, [{"claim_id": "c"}, {"claim_id": Exploding()}])

    # Serialization failed before any bytes reached the file: nothing lost, nothing partial.
    assert lines(path) == before

    append_jsonl(path, [{"claim_id": "c"}])
    after = lines(path)
    assert after[:2] == before
    assert [json.loads(line)["claim_id"] for line in after] == ["a", "b", "c"]


def test_truncated_trailing_line_does_not_destroy_earlier_records(tmp_path: Path) -> None:
    """C2: a half-written tail line is the only casualty; the ledger stays readable."""
    path = tmp_path / "_archive" / "records.jsonl"
    append_jsonl(path, [{"claim_id": "a"}, {"claim_id": "b"}])
    with path.open("a", encoding="utf-8") as stream:
        stream.write('{"claim_id": "hal')  # simulate a crash mid-line

    # Replay must survive the torn tail rather than raising on it: an
    # unreadable ledger would defeat the point of append-only history.
    assert [record["claim_id"] for record in read_jsonl(path)] == ["a", "b"]

    append_jsonl(path, [{"claim_id": "c"}])
    raw = lines(path)
    assert json.loads(raw[0])["claim_id"] == "a"
    assert json.loads(raw[1])["claim_id"] == "b"
    assert json.loads(raw[-1])["claim_id"] == "c"
    # The torn tail must be discarded (ftruncate), not sealed with "\n": sealing
    # would turn a tolerated, skippable last-line torn tail into a permanent
    # mid-file corruption that read_jsonl can never self-heal from again.
    assert len(raw) == 3
    assert [json.loads(line)["claim_id"] for line in raw] == ["a", "b", "c"]


def test_torn_tail_is_discarded_not_sealed_so_the_ledger_self_heals(tmp_path: Path) -> None:
    """BLOCKER fix: append_jsonl must ftruncate a torn tail, not seal it with "\\n".

    Sealing the tail with a newline turns a torn *last* line (tolerated by
    read_jsonl) into a permanent *middle* line, which read_jsonl can never
    tolerate. Since the ledger is append-only and never rewritten, that one
    corrupt append would make every future read_jsonl call raise forever.
    Discarding the torn bytes instead keeps the append idempotent with
    read_jsonl's own tolerance for a torn last line.
    """
    path = tmp_path / "_digest" / "claim-history.jsonl"
    append_jsonl(path, [{"claim_id": "a"}, {"claim_id": "b"}])

    # Simulate a crash mid-write: a half-written record with no trailing "\n".
    with path.open("a", encoding="utf-8") as stream:
        stream.write('{"claim_id": "torn", "text": "half-writ')

    # Appending a new record after the crash must repair the ledger: the
    # torn bytes are dropped, and the new record lands cleanly.
    append_jsonl(path, [{"claim_id": "c"}])

    # The ledger must be fully replayable with no ValidationError and no
    # trace of the torn record's data.
    records = read_jsonl(path)
    assert [record["claim_id"] for record in records] == ["a", "b", "c"]

    raw = lines(path)
    assert len(raw) == 3
    assert "half-writ" not in path.read_text(encoding="utf-8")
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_append_jsonl_writes_every_byte_when_the_kernel_accepts_short_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C2: POSIX write() may accept fewer bytes; the record must still land whole."""
    path = tmp_path / "_archive" / "records.jsonl"
    real_write = os.write
    write_calls = 0

    def short_write(descriptor: int, data: bytes) -> int:
        nonlocal write_calls
        write_calls += 1
        return real_write(descriptor, data[:7])

    monkeypatch.setattr(os, "write", short_write)
    append_jsonl(path, [{"claim_id": "a", "payload": "x" * 500}, {"claim_id": "b"}])
    monkeypatch.undo()

    assert write_calls > 1, "short_write stub was never exercised across multiple chunks"
    records = read_jsonl(path)
    assert [record["claim_id"] for record in records] == ["a", "b"]
    assert records[0]["payload"] == "x" * 500


def test_pending_review_rewrite_is_atomic_so_a_failed_write_keeps_old_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """H5: a crash mid-rewrite must leave the previous queue intact, not truncated."""
    from knowledge_digest import pipeline as pipeline_module

    pending_path = tmp_path / "_digest" / "pending-review.jsonl"
    stale = {
        "source_uri": "https://source.example/stale",
        "fragment_locator": "lines:1-1",
        "verification_status": "pending_review",
    }
    append_jsonl(pending_path, [stale])
    before = pending_path.read_text(encoding="utf-8")

    real_replace = os.replace
    replace_calls = 0

    def fail_replace(source: object, destination: object) -> None:
        nonlocal replace_calls
        replace_calls += 1
        raise OSError("injected replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError):
        pipeline_module._merge_pending_review(
            pending_path,
            [
                {
                    "source_uri": "https://source.example/new",
                    "fragment_locator": "lines:2-2",
                    "verification_status": "pending_review",
                }
            ],
            resolved=set(),
        )
    monkeypatch.setattr(os, "replace", real_replace)

    assert replace_calls >= 1, "os.replace stub was never called"
    # No truncation, no partial queue: the old pending set is byte-identical.
    assert pending_path.read_text(encoding="utf-8") == before
    assert [row["source_uri"] for row in read_jsonl(pending_path)] == [stale["source_uri"]]
    # No temp litter left behind.
    assert not list(pending_path.parent.glob(".*.tmp"))


def test_last_line_valid_but_non_object_json_still_fails_loudly(tmp_path: Path) -> None:
    """Torn-tail tolerance covers JSONDecodeError only, not well-formed non-objects.

    A torn tail is always a prefix of ``{...}`` and can never parse as valid
    non-dict JSON, so a final ``[1, 2, 3]`` is real foreign corruption. Silently
    skipping it would swallow data loss the reader is supposed to surface.
    """
    path = tmp_path / "ledger.jsonl"
    path.write_text('{"claim_id": "a"}\n[1, 2, 3]\n', encoding="utf-8")

    with pytest.raises(ValidationError):
        read_jsonl(path)

    for tail in ("null", '"x"', "42"):
        path.write_text('{"claim_id": "a"}\n' + tail + "\n", encoding="utf-8")
        with pytest.raises(ValidationError):
            read_jsonl(path)

    # The genuine torn tail is still tolerated, so this did not over-tighten.
    path.write_text('{"claim_id": "a"}\n{"claim_id": "b', encoding="utf-8")
    assert [record["claim_id"] for record in read_jsonl(path)] == ["a"]


def test_replace_jsonl_leaves_no_temp_file_when_the_write_phase_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed write or fsync must unlink its temp sibling, not accumulate .tmp litter."""
    from knowledge_digest import jsonl as jsonl_module

    path = tmp_path / "_digest" / "queue.jsonl"
    append_jsonl(path, [{"source_uri": "https://source.example/stale"}])
    before = path.read_text(encoding="utf-8")

    def fail_write(descriptor: int, data: bytes) -> None:
        raise OSError("injected write failure")

    write_calls = 0
    real_fail_write = fail_write

    def counted_fail_write(descriptor: int, data: bytes) -> None:
        nonlocal write_calls
        write_calls += 1
        real_fail_write(descriptor, data)

    monkeypatch.setattr(jsonl_module, "_write_all", counted_fail_write)
    with pytest.raises(OSError):
        jsonl_module.replace_jsonl(path, [{"source_uri": "https://source.example/new"}])
    monkeypatch.undo()

    assert write_calls >= 1, "_write_all stub was never called"
    assert path.read_text(encoding="utf-8") == before
    assert not list(path.parent.glob(".*.tmp"))

    fsync_calls = 0

    def fail_fsync(descriptor: int) -> None:
        nonlocal fsync_calls
        fsync_calls += 1
        raise OSError("injected fsync failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    with pytest.raises(OSError):
        jsonl_module.replace_jsonl(path, [{"source_uri": "https://source.example/new"}])
    monkeypatch.undo()

    assert fsync_calls >= 1, "os.fsync stub was never called"
    assert path.read_text(encoding="utf-8") == before
    assert not list(path.parent.glob(".*.tmp"))
