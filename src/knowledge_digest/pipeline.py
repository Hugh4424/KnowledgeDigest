"""Phase-one audit run creation without formal knowledge-base writes."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .cluster import cluster
from .config import DigestSettings
from .draft import draft
from .errors import ValidationError
from .ingest import ingest
from .kb_structure import DEFAULT_ROOTS
from .paths import DigestPaths
from .provenance import audit_provenance
from .retrieve import retrieve
from .writeback import writeback
from .writeback import _targets_for_draft


def _formal_changes(writes: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = ("target_path", "action", "status", "archive_path")
    return [{key: row[key] for key in keys} for row in writes]


def _write_plan(drafts: list[dict[str, object]], paths: DigestPaths, roots: tuple[str, ...]) -> dict[str, object]:
    changes = []
    for item in drafts:
        target = _targets_for_draft(item, roots[0])[0]
        changes.append(
            {
                "target_path": target.as_posix(),
                "action": item["action"],
                "archive_required": (paths.kb_dir / target).is_file(),
            }
        )
    return {"formal_kb_changes": changes}


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

    A non-dry run writes S1-S6 artifacts, formal pages, and pre-write archives.
    A dry run is limited to the run report.
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
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
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
    writes: list[dict[str, object]] = []
    write_plan_snapshot: dict[str, object] | None = None
    if not dry_run:
        raw_items = ingest(paths, run_dir)
        clusters = cluster(raw_items, run_dir, paths, roots, settings)
        decisions = retrieve(clusters, raw_items, run_dir, paths, roots, settings)
        drafts = draft(decisions, clusters, raw_items, run_dir, settings)
        writes = writeback(drafts, run_dir, paths, roots)
        audit_provenance(drafts, writes, raw_items, run_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="knowledge-digest-plan-") as temporary:
            planning_dir = Path(temporary)
            raw_items = ingest(paths, planning_dir)
            clusters = cluster(
                raw_items, planning_dir, paths, roots, settings, persist_queues=False
            )
            decisions = retrieve(clusters, raw_items, planning_dir, paths, roots, settings)
            drafts = draft(decisions, clusters, raw_items, planning_dir, settings)
            write_plan_snapshot = _write_plan(drafts, paths, roots)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["formal_kb_changes"] = _formal_changes(writes)
    if write_plan_snapshot is not None:
        report["write_plan_snapshot"] = write_plan_snapshot
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    prefix = "dry-run" if dry_run else "audit"
    summary = (
        f"{prefix}: audited {source_notes} source note(s); roots={', '.join(roots)}; "
        f"top_k={settings.top_k}; high={settings.high:.2f}; "
        f"medium={settings.medium:.2f}; max_lines={settings.max_lines}; "
        + (
            "no formal knowledge-base files written"
            if dry_run
            else f"{len(writes)} formal knowledge-base file(s) written"
        )
    )
    return report_path, summary
