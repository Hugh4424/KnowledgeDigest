"""Stage 5: validated, atomic page writes and retained archive records."""

from __future__ import annotations

import os
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .jsonl import write_jsonl
from .paths import DigestPaths
from .provenance import append_jsonl, now_utc, retention_deadline


def _safe_relative(path: str, kb_dir: Path) -> Path:
    """Return a KB-relative path without allowing a write outside the KB."""
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(kb_dir)
        except ValueError as error:
            raise ValidationError("s5", path, "target page is outside kb_dir") from error
    if not candidate.parts or ".." in candidate.parts:
        raise ValidationError("s5", path, "target page must be a safe kb-relative path")
    return candidate


def _atomic_write(path: Path, content: str) -> None:
    """Write complete UTF-8 content through a synced temporary sibling file."""
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
        raise ValidationError("s5", path, f"atomic write failed: {error}") from error


def _render_page(draft: dict[str, Any]) -> str:
    body = str(draft["final_body"]).strip()
    provenance_lines = []
    for claim in draft.get("claims", []):
        provenance_lines.append(
            "- "
            f"{claim['text']} — {claim['source_uri']} "
            f"(fragment_locator={claim.get('fragment_locator', '')}; "
            f"content_fingerprint={claim.get('content_fingerprint', '')})"
        )
    provenance = "\n".join(provenance_lines)
    return f"{body}\n\n## Provenance\n{provenance}\n"


def targets_for_draft(draft: dict[str, Any], page_root: str) -> list[Path]:
    targets = [Path(path) for path in draft.get("target_paths", [])]
    if targets:
        return targets
    return [Path(page_root) / "digest" / f"{draft['draft_id']}.md"]


def _expanded_pages(draft: dict[str, Any], page_root: str) -> list[dict[str, Any]]:
    pages = draft.get("split_pages")
    if isinstance(pages, list) and pages:
        return [dict(page, draft_id=draft["draft_id"], action=draft["action"]) for page in pages]
    target = targets_for_draft(draft, page_root)[0]
    return [
        {
            "draft_id": draft["draft_id"],
            "page_index": 1,
            "target_path": target.as_posix(),
            "final_body": draft["final_body"],
            "claims": draft.get("claims", []),
            "action": draft["action"],
        }
    ]


def _archive_page_record(
    *,
    paths: DigestPaths,
    archive_root: str,
    run_dir: Path,
    page: dict[str, Any],
    before_content: str,
    reason: str,
) -> dict[str, Any]:
    validate_archive_reason(reason)
    target = _safe_relative(str(page["target_path"]), paths.kb_dir)
    archive_base = Path(archive_root) / run_dir.name / target
    timestamp = now_utc()
    claims = page.get("claims", [])
    source_snapshots: list[dict[str, Any]] = []
    source_uris: list[str] = []
    seen_snapshot_keys: set[tuple[Any, ...]] = set()
    for claim in claims:
        source_uri = claim.get("source_uri")
        if isinstance(source_uri, str) and source_uri not in source_uris:
            source_uris.append(source_uri)
        snapshot = {
            "source_uri": source_uri,
            "source_snapshot_ref": claim.get("source_snapshot_ref"),
            "content_fingerprint": claim.get("content_fingerprint"),
            "fragment_locator": claim.get("fragment_locator"),
        }
        key = (
            snapshot["source_snapshot_ref"]
            or snapshot["source_uri"],
            snapshot["content_fingerprint"],
        )
        if key not in seen_snapshot_keys:
            source_snapshots.append(snapshot)
            seen_snapshot_keys.add(key)
    return {
        "operation": "replace",
        "operation_at": timestamp,
        "reason": reason,
        "claim_ids": [claim.get("claim_fingerprint") for claim in claims if claim.get("claim_fingerprint")],
        "page_path": target.as_posix(),
        "source_uri": source_uris,
        "source_snapshot_ref": [
            claim.get("source_snapshot_ref")
            for claim in claims
            if claim.get("source_snapshot_ref")
        ],
        "source_snapshot": source_snapshots,
        "content_fingerprint": sha256(before_content.encode("utf-8")).hexdigest(),
        "fragment_locator": claims[0].get("fragment_locator") if claims else None,
        "full_content": before_content,
        "snapshot_content": before_content,
        "archive_content_path": archive_base.as_posix(),
        "retain_content_until": retention_deadline(timestamp),
        "content_retained": True,
        "lineage": {
            "draft_id": page["draft_id"],
            "page_index": page.get("page_index", 1),
            "supersedes": [claim.get("supersedes") for claim in claims if claim.get("supersedes")],
            "superseded_by": [claim.get("superseded_by") for claim in claims if claim.get("superseded_by")],
        },
    }


def writeback(
    drafts: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Validate the complete batch, then materialize all formal pages."""
    page_root = roots[0]
    archive_root = roots[1] if len(roots) >= 2 else "_archive"
    pages = [page for draft in drafts for page in _expanded_pages(draft, page_root)]
    operations: list[dict[str, Any]] = []
    archive_records: list[dict[str, Any]] = []
    archive_paths: list[Path] = []
    original_contents: dict[Path, str | None] = {}
    for page in pages:
        claims = page.get("claims", [])
        target = _safe_relative(str(page["target_path"]), paths.kb_dir)
        target_path = paths.kb_dir / target
        if not claims or any(
            not claim.get("text")
            or not claim.get("source_uri")
            or not claim.get("claim_fingerprint")
            or not claim.get("content_fingerprint")
            or not claim.get("fragment_locator")
            for claim in claims
        ):
            failed = {
                "draft_id": page.get("draft_id", "draft"),
                "page_index": page.get("page_index", 1),
                "target_path": target.as_posix(),
                "action": page.get("action", "unknown"),
                "status": "failed",
                "archive_path": None,
                "archive_reason": None,
                "archive_snapshot_sha256": None,
            }
            write_jsonl(run_dir / "s5" / "write-report.jsonl", [failed])
            raise ValidationError(
                "s5",
                page.get("draft_id", "draft"),
                "atomic write failed: every written claim requires complete provenance",
            )
        if target_path.exists() and not target_path.is_file():
            raise ValidationError("s5", target_path, "target page must be a regular file")
        before = target_path.read_text(encoding="utf-8") if target_path.exists() else None
        original_contents[target_path] = before
        if before is not None:
            archive_record = _archive_page_record(
                paths=paths,
                archive_root=archive_root,
                run_dir=run_dir,
                page=page,
                before_content=before,
                reason=page.get("archive_reason") or "pre-write snapshot",
            )
            archive_records.append(archive_record)
            archive_paths.append(paths.kb_dir / archive_record["archive_content_path"])
        operations.append(
            {
                "draft_id": page["draft_id"],
                "page_index": page.get("page_index", 1),
                "target_path": target.as_posix(),
                "action": page["action"],
                "status": "pending",
                "archive_path": archive_records[-1]["archive_content_path"] if before is not None else None,
                "archive_reason": "pre-write snapshot" if before is not None else None,
                "archive_snapshot_sha256": sha256(before.encode("utf-8")).hexdigest() if before is not None else None,
            }
        )

    try:
        for page, operation in zip(pages, operations):
            target_path = paths.kb_dir / operation["target_path"]
            _atomic_write(target_path, _render_page(page))
            operation["status"] = "success"
        for archive_path, archive_record in zip(archive_paths, archive_records):
            _atomic_write(archive_path, str(archive_record["full_content"]))
    except ValidationError as original_error:
        rollback_failures: list[dict[str, str]] = []
        for target_path, before in original_contents.items():
            try:
                if before is None:
                    target_path.unlink(missing_ok=True)
                else:
                    _atomic_write(target_path, before)
            except (OSError, ValidationError) as error:
                rollback_failures.append(
                    {"operation": "restore_page", "path": str(target_path), "error": str(error)}
                )
        for archive_path in archive_paths:
            try:
                archive_path.unlink(missing_ok=True)
            except OSError as error:
                rollback_failures.append(
                    {"operation": "remove_archive", "path": str(archive_path), "error": str(error)}
                )
        for operation in operations:
            operation["status"] = "failed"
        write_jsonl(run_dir / "s5" / "write-report.jsonl", operations)
        if rollback_failures:
            write_jsonl(run_dir / "s5" / "rollback-failures.jsonl", rollback_failures)
            paths_text = ", ".join(item["path"] for item in rollback_failures)
            raise ValidationError(
                "s5",
                "rollback",
                f"batch write failed: {original_error}; rollback failed for: {paths_text}",
            ) from original_error
        raise

    write_jsonl(run_dir / "s5" / "write-report.jsonl", operations)
    write_jsonl(run_dir / "s5" / "archive-records.jsonl", archive_records)
    append_jsonl(paths.kb_dir / archive_root / "records.jsonl", archive_records)
    return operations


def validate_archive_reason(reason: str) -> None:
    if not reason or not reason.strip():
        raise ValidationError("archive", "reason", "archive reason must not be empty")
