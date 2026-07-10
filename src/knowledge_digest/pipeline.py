"""Phase-one audit run creation without formal knowledge-base writes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .config import DigestSettings
from .errors import ValidationError
from .kb_structure import DEFAULT_ROOTS
from .paths import DigestPaths


INGESTIBLE_SUFFIXES = {".md", ".txt", ".json"}


def _run_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:12]}"


def audit_run(
    paths: DigestPaths,
    settings: DigestSettings,
    roots: tuple[str, ...] = DEFAULT_ROOTS,
    *,
    dry_run: bool,
) -> tuple[Path, str]:
    """Write a single audit report under the allowed run directory.

    Phase one deliberately never writes pages, archives, queues, or source inputs.
    """
    audit_root = paths.kb_dir / "_digest"
    if audit_root.is_symlink():
        raise ValidationError("audit_run", audit_root, "_digest must not be a symlink")
    if audit_root.exists() and not audit_root.is_dir():
        raise ValidationError("audit_run", audit_root, "_digest must be a directory")
    run_dir = audit_root / "runs" / _run_id()
    run_dir.mkdir(parents=True)
    source_notes = sum(
        1
        for path in paths.items_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in INGESTIBLE_SUFFIXES
    )
    report_path = run_dir / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "dry_run": dry_run,
                "source_notes": source_notes,
                "roots": list(roots),
                "settings": {
                    "top_k": settings.top_k,
                    "high": settings.high,
                    "medium": settings.medium,
                    "max_lines": settings.max_lines,
                },
                "formal_kb_changes": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    prefix = "dry-run" if dry_run else "audit"
    summary = (
        f"{prefix}: audited {source_notes} source note(s); roots={', '.join(roots)}; "
        f"top_k={settings.top_k}; high={settings.high:.2f}; "
        f"medium={settings.medium:.2f}; max_lines={settings.max_lines}; "
        "no formal knowledge-base files written"
    )
    return report_path, summary
