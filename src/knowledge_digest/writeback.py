"""Stage 5: durable Markdown page writes and pre-write archives."""

from __future__ import annotations

import os
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .jsonl import write_jsonl
from .paths import DigestPaths


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
    provenance = "\n".join(
        f"- {claim['text']} — {claim['source_uri']}" for claim in draft["claims"]
    )
    return f"{body}\n\n## Provenance\n{provenance}\n"


def _targets_for_draft(draft: dict[str, Any], page_root: str) -> list[Path]:
    targets = [Path(path) for path in draft["target_paths"]]
    if targets:
        # merge_multiple preserves the first selected formal page and archives the
        # remaining candidates instead of silently overwriting each page with one body.
        return [targets[0]]
    return [Path(page_root) / "digest" / f"{draft['draft_id']}.md"]


def writeback(
    drafts: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Archive old pages then atomically materialize each complete formal draft."""
    page_root = roots[0]
    archive_root = roots[1] if len(roots) >= 2 else "_archive"
    writes: list[dict[str, Any]] = []

    for draft in drafts:
        claims = draft.get("claims", [])
        if not claims or any(not claim.get("text") or not claim.get("source_uri") for claim in claims):
            raise ValidationError("s5", draft.get("draft_id", "draft"), "every written claim requires source_uri")
        target = _safe_relative(str(_targets_for_draft(draft, page_root)[0]), paths.kb_dir)
        target_path = paths.kb_dir / target
        archive_path: Path | None = None
        archive_snapshot_sha256: str | None = None
        if target_path.exists():
            if not target_path.is_file():
                raise ValidationError("s5", target_path, "target page must be a regular file")
            archive_path = Path(archive_root) / run_dir.name / target
            before_snapshot = target_path.read_text(encoding="utf-8")
            archive_snapshot_sha256 = sha256(before_snapshot.encode("utf-8")).hexdigest()
            _atomic_write(paths.kb_dir / archive_path, before_snapshot)
        try:
            _atomic_write(target_path, _render_page(draft))
        except ValidationError:
            writes.append(
                {
                    "draft_id": draft["draft_id"],
                    "target_path": target.as_posix(),
                    "action": draft["action"],
                    "status": "failed",
                    "archive_path": archive_path.as_posix() if archive_path else None,
                    "archive_reason": "pre-write snapshot" if archive_path else None,
                    "archive_snapshot_sha256": archive_snapshot_sha256,
                }
            )
            write_jsonl(run_dir / "s5" / "write-report.jsonl", writes)
            raise
        writes.append(
            {
                "draft_id": draft["draft_id"],
                "target_path": target.as_posix(),
                "action": draft["action"],
                "status": "success",
                "archive_path": archive_path.as_posix() if archive_path else None,
                "archive_reason": "pre-write snapshot" if archive_path else None,
                "archive_snapshot_sha256": archive_snapshot_sha256,
            }
        )

    write_jsonl(run_dir / "s5" / "write-report.jsonl", writes)
    return writes
