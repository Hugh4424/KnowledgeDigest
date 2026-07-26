"""JSONL persistence helpers with validation."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError


def _write_all(descriptor: int, data: bytes) -> None:
    """Write every byte. POSIX write() may accept fewer bytes than requested."""
    offset = 0
    while offset < len(data):
        written = os.write(descriptor, data[offset:])
        if written <= 0:
            raise OSError(f"write made no progress after {offset} of {len(data)} bytes")
        offset += written


def _fsync_directory(directory: Path) -> None:
    """Persist a directory entry so a new or replaced file survives a crash."""
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Persist one JSON object per line, including a valid empty result file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def replace_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Replace a whole ledger atomically: temp sibling, fsync, then os.replace.

    Used for the few ledgers that are genuinely rewritten (merged, not appended).
    A crash can only leave either the complete old file or the complete new one,
    never a truncated queue.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary_path = Path(temporary_name)
    try:
        try:
            _write_all(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except BaseException:
        # The temp sibling is unusable once the write or fsync failed; leaving it
        # behind would accumulate hidden .tmp files next to the real ledger.
        temporary_path.unlink(missing_ok=True)
        raise
    try:
        os.replace(temporary_path, path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise
    _fsync_directory(path.parent)


def append_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Append records with O_APPEND + fsync so existing lines are never rewritten."""
    values = list(records)
    if not values:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize everything before opening the file: a bad record must fail before
    # any bytes land, never halfway through the ledger.
    payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in values)
    is_new = not path.exists()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        # A crash can leave the previous line unterminated (a torn tail). Discard
        # it instead of closing it off with a newline: read_jsonl only tolerates a
        # torn *last* line, so sealing it with "\n" would turn a self-healing,
        # skippable tail into a permanent mid-file corruption that fails every
        # future read. Truncating drops exactly the bytes read_jsonl would have
        # ignored anyway, keeping this append idempotent with that tolerance.
        if os.lseek(descriptor, 0, os.SEEK_END) > 0:
            existing = path.read_bytes()
            if not existing.endswith(b"\n"):
                truncate_at = existing.rfind(b"\n") + 1
                os.ftruncate(descriptor, truncate_at)
        _write_all(descriptor, payload.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if is_new:
        # A fsynced file is still loseable if its directory entry never landed.
        _fsync_directory(path.parent)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file, skipping blank lines and validating each record.

    A crash can leave a half-written *final* line. That single torn tail is
    dropped so the append-only ledger stays replayable; any malformed line
    before the tail is real corruption and still fails loudly.
    """
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    last_index = len(raw_lines) - 1
    for number, line in enumerate(raw_lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            if number - 1 == last_index:
                continue
            raise ValidationError("ingest", path, f"invalid JSONL at line {number}: {error.msg}") from error
        if not isinstance(value, dict):
            # A torn tail is a prefix of "{...}" and can never parse as valid
            # non-dict JSON, so tolerance stops at JSONDecodeError. Reaching here
            # means real foreign corruption, which must still fail loudly.
            raise ValidationError("ingest", path, f"JSONL line {number} must be an object")
        records.append(value)
    return records
