"""JSONL persistence helpers with validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Persist one JSON object per line, including a valid empty result file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file, skipping blank lines and validating each record."""
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError("ingest", path, f"invalid JSONL at line {number}: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValidationError("ingest", path, f"JSONL line {number} must be an object")
        records.append(value)
    return records
