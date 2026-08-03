"""Stage 5: validated, atomic page writes and retained archive records."""

from __future__ import annotations

import os
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .jsonl import append_jsonl, write_jsonl
from .kb_structure import PublicationContract
from .paths import DigestPaths
from .provenance import now_utc, retention_deadline


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
    resolved_kb = kb_dir.resolve()
    resolved_candidate = (kb_dir / candidate).resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_kb)
    except ValueError as error:
        raise ValidationError("s5", path, "target page is outside kb_dir") from error
    return candidate


def _frontmatter_values(content: str) -> dict[str, str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() in {"---", "..."}:
            break
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip("\"'")
    return values


def _publication_target_kind(target: Path, publication: PublicationContract) -> tuple[str, str | None]:
    target_text = target.as_posix()
    if target_text == "README.md":
        return "readme", None
    if target_text == publication.source_index_path:
        return "source-index", None
    if target_text == publication.home_path:
        return "home", None
    for category in publication.categories:
        if target.as_posix() == publication.category_index_path(category.category_id):
            return "category", category.category_id
        if category.parent_id and target_text == f"{publication.index_root}/{category.parent_id}.md":
            return "parent-index", category.parent_id
        topic_dir = Path(category.topic_dir)
        if topic_dir in target.parents:
            return "topic", category.category_id
    raise ValidationError("publication", target, "target is outside the declared publication paths")


def _validate_publication_header(
    *,
    target: Path,
    content: str,
    expected_kind: str,
    category_id: str | None,
    existing: bool,
) -> None:
    values = _frontmatter_values(content)
    subject = "existing managed page" if existing else "publication content"
    if expected_kind == "readme" and not values and content.lstrip().startswith("# Knowledge Digest"):
        return
    if expected_kind == "source-index" and not values:
        if content.lstrip().startswith("# Source Index") or "digest_kind: source-index" in content:
            return
    if values.get("managed_by") != "KnowledgeDigest":
        raise ValidationError("publication", target, f"{subject} must declare managed_by: KnowledgeDigest")
    if values.get("digest_kind") != expected_kind:
        raise ValidationError("publication", target, f"{subject} has an invalid digest_kind")
    if expected_kind == "topic":
        if not values.get("digest_topic_id"):
            raise ValidationError("publication", target, f"{subject} is missing digest_topic_id")
        if values.get("digest_published_path") != target.as_posix():
            raise ValidationError(
                "publication",
                target,
                f"{subject} digest_published_path must match its actual path",
            )
        try:
            part = int(values.get("digest_part", ""))
        except ValueError as error:
            raise ValidationError("publication", target, f"{subject} digest_part must be a positive integer") from error
        if part < 1:
            raise ValidationError("publication", target, f"{subject} digest_part must be a positive integer")
    if expected_kind == "category" and values.get("digest_category_id") != category_id:
        raise ValidationError("publication", target, f"{subject} has an invalid digest_category_id")
    if expected_kind == "parent-index" and values.get("digest_parent_id") != category_id:
        raise ValidationError("publication", target, f"{subject} has an invalid digest_parent_id")


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


def _split_existing_page(content: str) -> tuple[str, str, str]:
    """Separate an exact leading YAML frontmatter block from page content."""
    frontmatter = ""
    body = content
    lines = content.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                end = index + 1
                frontmatter = "".join(lines[:end])
                body = "".join(lines[end:])
                break
    offset = 0
    provenance_start: int | None = None
    provenance_heading_end: int | None = None
    for line in body.splitlines(keepends=True):
        if line.strip() == "## Provenance":
            provenance_start = offset
            provenance_heading_end = offset + len(line)
            break
        offset += len(line)
    if provenance_start is None or provenance_heading_end is None:
        return frontmatter, body.strip(), ""
    return (
        frontmatter,
        body[:provenance_start].strip(),
        body[provenance_heading_end:].strip(),
    )


def _normalized_line(value: object) -> str:
    return " ".join(str(value).split()).casefold()


def _claim_line_key(value: object) -> str:
    """Normalize only Markdown wrappers around a claim line."""
    line = _normalized_line(value)
    if len(line) >= 2 and line[:2] in {"- ", "* ", "+ "}:
        line = line[2:].strip()
    for marker in ("**", "__"):
        if line.startswith(marker) and line.endswith(marker) and len(line) >= len(marker) * 2:
            line = line[len(marker) : -len(marker)].strip()
    return line


def _contribution_body(
    page: dict[str, Any],
    *,
    seen_claims: set[str],
    seen_claim_texts: set[str],
    existing_lines: set[str],
) -> str:
    """Keep formatting, but render each already-seen claim at most once."""
    claims_by_text = {
        _claim_line_key(claim.get("text")): str(claim.get("claim_fingerprint"))
        for claim in page.get("claims", [])
        if claim.get("text") and claim.get("claim_fingerprint")
    }
    existing_claims = {
        fingerprint
        for text, fingerprint in claims_by_text.items()
        if text in existing_lines
    }
    claim_fingerprints = set(claims_by_text.values())
    if claim_fingerprints and claim_fingerprints <= existing_claims:
        return ""
    local_claims: set[str] = set()
    local_claim_texts: set[str] = set()
    lines: list[str] = []
    for line in str(page.get("final_body", "")).splitlines():
        claim_text = _claim_line_key(line)
        fingerprint = claims_by_text.get(claim_text)
        if fingerprint and (
            fingerprint in seen_claims
            or fingerprint in local_claims
            or claim_text in local_claim_texts
            or claim_text in seen_claim_texts
            or fingerprint in existing_claims
        ):
            continue
        if fingerprint:
            local_claims.add(fingerprint)
            local_claim_texts.add(claim_text)
        lines.append(line)
    return "\n".join(lines).strip()


def _archive_content_path(base: Path, content: str, kb_dir: Path) -> Path:
    """Reuse an identical snapshot or allocate a collision-safe replay path."""
    candidate = base
    for index in range(0, 10000):
        resolved_kb = kb_dir.resolve()
        try:
            candidate.resolve(strict=False).relative_to(resolved_kb)
        except ValueError as error:
            raise ValidationError("s5", candidate, "archive destination is outside kb_dir") from error
        if not candidate.exists():
            return candidate
        try:
            if candidate.is_file() and candidate.read_text(encoding="utf-8") == content:
                return candidate
        except OSError:
            pass
        index += 1
        candidate = Path(f"{base}.replay-{index}")
    raise ValidationError("s5", base, "archive replay path exhaustion")


def targets_for_draft(draft: dict[str, Any], page_root: str) -> list[Path]:
    targets = [Path(path) for path in draft.get("target_paths", [])]
    if targets:
        return targets
    return [Path(page_root) / "digest" / f"{draft['draft_id']}.md"]


def _expanded_pages(draft: dict[str, Any], page_root: str) -> list[dict[str, Any]]:
    pages = draft.get("split_pages")
    if isinstance(pages, list) and pages:
        return [
            dict(
                page,
                draft_id=draft["draft_id"],
                action=draft["action"],
                digest_kind=page.get("digest_kind", draft.get("digest_kind")),
            )
            for page in pages
        ]
    targets = targets_for_draft(draft, page_root)
    return [
        {
            "draft_id": draft["draft_id"],
            "page_index": index,
            "target_path": target.as_posix(),
            "final_body": draft["final_body"],
            "claims": [dict(claim, page_index=index, target_path=target.as_posix()) for claim in draft.get("claims", [])],
            "action": draft["action"],
        }
        for index, target in enumerate(targets, start=1)
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
    archive_base = paths.kb_dir / Path(archive_root) / run_dir.name / target
    archive_content_path = _archive_content_path(archive_base, before_content, paths.kb_dir).relative_to(paths.kb_dir)
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
        "archive_content_path": archive_content_path.as_posix(),
        "retain_content_until": retention_deadline(timestamp),
        "content_retained": True,
        "lineage": {
            "draft_id": page["draft_id"],
            "page_index": page.get("page_index", 1),
            "contributors": page.get("contributors", []),
            "supersedes": [claim.get("supersedes") for claim in claims if claim.get("supersedes")],
            "superseded_by": [claim.get("superseded_by") for claim in claims if claim.get("superseded_by")],
        },
    }


def writeback(
    drafts: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
    *,
    publication: PublicationContract | None = None,
) -> list[dict[str, Any]]:
    """Validate the complete batch, then materialize all formal pages."""
    page_root = roots[0]
    archive_root = roots[1] if len(roots) >= 2 else "_archive"
    pages = [page for draft in drafts for page in _expanded_pages(draft, page_root)]
    for draft in drafts:
        for target_path in draft.get("obsolete_target_paths", []):
            if publication is not None:
                raise ValidationError("publication", target_path, "incremental publication does not delete old topic parts")
            pages.append(
                {
                    "draft_id": draft["draft_id"],
                    "page_index": 0,
                    "target_path": str(target_path),
                    "action": "remove",
                    "claims": [],
                    "remove_only": True,
                }
            )
    grouped: dict[str, dict[str, Any]] = {}
    for page in pages:
        target = _safe_relative(str(page["target_path"]), paths.kb_dir)
        if publication is not None:
            if target.suffix.lower() != ".md":
                raise ValidationError("publication", target, "publication target must be a Markdown file")
            expected_kind, category_id = _publication_target_kind(target, publication)
            if page.get("digest_kind") != expected_kind:
                raise ValidationError("publication", target, "publication record has an invalid digest_kind")
            page["publication_category_id"] = category_id
        target_key = target.as_posix()
        group = grouped.setdefault(
            target_key,
            {
                "target_path": target_key,
                "pages": [],
                "contributors": [],
                "draft_id": page.get("draft_id", "draft"),
                "page_index": page.get("page_index", 1),
                "action": page.get("action", "unknown"),
            },
        )
        group["pages"].append(page)
        group["contributors"].append(
            {
                "draft_id": page.get("draft_id", "draft"),
                "action": page.get("action", "unknown"),
                "page_index": page.get("page_index", 1),
                "target_path": target_key,
            }
        )

    aggregates: list[dict[str, Any]] = []
    for group in grouped.values():
        target = _safe_relative(str(group["target_path"]), paths.kb_dir)
        target_path = paths.kb_dir / target
        parent = target_path.parent
        while parent != paths.kb_dir:
            if parent.is_symlink():
                raise ValidationError("s5", parent, "target parent directory must not be a symlink")
            parent = parent.parent
        if target_path.is_symlink():
            raise ValidationError("s5", target_path, "target page must not be a symlink")
        if target_path.exists() and not target_path.is_file():
            raise ValidationError("s5", target_path, "target page must be a regular file")
        before = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
        if publication is not None and target_path.exists():
            expected_kind, category_id = _publication_target_kind(target, publication)
            _validate_publication_header(
                target=target,
                content=before,
                expected_kind=expected_kind,
                category_id=category_id,
                existing=True,
            )
        if any(page.get("remove_only") for page in group["pages"]):
            if len(group["pages"]) != 1:
                raise ValidationError("s5", target, "removed topic part cannot receive new content")
            aggregate = dict(group)
            aggregate.update(
                {
                    "remove_only": True,
                    "claims": [],
                    "before_content": before or None,
                    "final_body": "",
                    "frontmatter": "",
                    "existing_provenance": "",
                    "new_provenance": [],
                }
            )
            aggregates.append(aggregate)
            continue
        if any(page.get("layout_finalized") for page in group["pages"]):
            if len(group["pages"]) != 1 or not group["pages"][0].get("layout_finalized"):
                raise ValidationError("s5", target, "final topic layout must own one complete target page")
            page = group["pages"][0]
            page_claims = page.get("claims", [])
            rendered = page.get("rendered_content")
            if not isinstance(rendered, str) or not rendered.strip():
                raise ValidationError("s5", target, "final topic layout is missing rendered content")
            if publication is not None:
                expected_kind, category_id = _publication_target_kind(target, publication)
                if target_path.exists():
                    _validate_publication_header(
                        target=target,
                        content=before,
                        expected_kind=expected_kind,
                        category_id=category_id,
                        existing=True,
                    )
                _validate_publication_header(
                    target=target,
                    content=rendered,
                    expected_kind=expected_kind,
                    category_id=category_id,
                    existing=False,
                )
                if expected_kind in {"readme", "home", "category", "parent-index", "source-index"}:
                    if page_claims != []:
                        raise ValidationError("publication", target, "navigation publication must not contain claims")
                elif not isinstance(page_claims, list) or any(
                    not claim.get("text")
                    or not claim.get("source_uri")
                    or not claim.get("claim_fingerprint")
                    or not claim.get("content_fingerprint")
                    or not claim.get("fragment_locator")
                    for claim in page_claims
                ):
                    raise ValidationError("s5", target, "final topic layout requires complete claim provenance")
            elif not isinstance(page_claims, list) or any(
                not claim.get("text")
                or not claim.get("source_uri")
                or not claim.get("claim_fingerprint")
                or not claim.get("content_fingerprint")
                or not claim.get("fragment_locator")
                for claim in page_claims
            ):
                raise ValidationError("s5", target, "final topic layout requires complete claim provenance")
            aggregate = dict(group)
            aggregate.update(
                {
                    "claims": [dict(claim, target_path=target.as_posix()) for claim in page_claims],
                    "before_content": before or None,
                    "frontmatter": "",
                    "existing_provenance": "",
                    "new_provenance": [],
                    "final_body": str(page.get("final_body", "")),
                    "rendered_content": rendered,
                    "layout_finalized": True,
                }
            )
            aggregates.append(aggregate)
            continue
        frontmatter, existing_body, existing_provenance = _split_existing_page(before)
        existing_lines = {_claim_line_key(line) for line in existing_body.splitlines() if line.strip()}
        seen_claims: set[str] = set()
        seen_claim_texts: set[str] = set()
        claims: list[dict[str, Any]] = []
        contribution_bodies: list[str] = []
        provenance_blocks: list[str] = []
        for page in group["pages"]:
            page_claims = page.get("claims", [])
            if not isinstance(page_claims, list) or not page_claims or any(
                not claim.get("text")
                or not claim.get("source_uri")
                or not claim.get("claim_fingerprint")
                or not claim.get("content_fingerprint")
                or not claim.get("fragment_locator")
                for claim in page_claims
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
            contribution = _contribution_body(
                page,
                seen_claims=seen_claims,
                existing_lines=existing_lines,
                seen_claim_texts=seen_claim_texts,
            )
            if contribution:
                contribution_bodies.append(contribution)
            for claim in page_claims:
                fingerprint = str(claim["claim_fingerprint"])
                claim_text = _claim_line_key(claim.get("text"))
                if fingerprint in seen_claims or claim_text in seen_claim_texts:
                    continue
                seen_claims.add(fingerprint)
                seen_claim_texts.add(claim_text)
                claims.append(dict(claim, target_path=target.as_posix()))
                provenance_blocks.append(
                    "- "
                    f"{claim['text']} — {claim['source_uri']} "
                    f"(fragment_locator={claim.get('fragment_locator', '')}; "
                    f"content_fingerprint={claim.get('content_fingerprint', '')})"
                )
        body_parts = [part for part in [*contribution_bodies, existing_body] if part]
        aggregate = dict(group)
        aggregate["final_body"] = "\n\n".join(body_parts).strip()
        aggregate["frontmatter"] = frontmatter
        aggregate["claims"] = claims
        aggregate["existing_provenance"] = existing_provenance
        existing_provenance_lines = set(existing_provenance.splitlines())
        aggregate["new_provenance"] = list(
            dict.fromkeys(
                line for line in provenance_blocks if line not in existing_provenance_lines
            )
        )
        aggregate["before_content"] = before or None
        aggregates.append(aggregate)

    operations: list[dict[str, Any]] = []
    archive_records: list[dict[str, Any]] = []
    archive_paths: list[Path] = []
    for page in aggregates:
        target = _safe_relative(str(page["target_path"]), paths.kb_dir)
        before = page["before_content"]
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
                "contributors": page.get("contributors", []),
                "status": "pending",
                "archive_path": archive_records[-1]["archive_content_path"] if before is not None else None,
                "archive_reason": "pre-write snapshot" if before is not None else None,
                "archive_snapshot_sha256": sha256(before.encode("utf-8")).hexdigest() if before is not None else None,
            }
        )

    # Archive every original page, and record its lineage, before any target is
    # overwritten. `_atomic_write` fsyncs both the file and its parent directory and
    # `append_jsonl` fsyncs the ledger, so a failure while writing the target pages
    # below always leaves the original content recoverable under `_archive/` *with*
    # the record that points at it. This ordering replaces the former batch rollback.
    for archive_path, archive_record in zip(archive_paths, archive_records):
        if not (
            archive_path.exists()
            and archive_path.is_file()
            and archive_path.read_text(encoding="utf-8") == archive_record["full_content"]
        ):
            _atomic_write(archive_path, str(archive_record["full_content"]))
    write_jsonl(run_dir / "s5" / "archive-records.jsonl", archive_records)
    append_jsonl(paths.kb_dir / archive_root / "records.jsonl", archive_records)
    rendered_operations: list[tuple[dict[str, Any], dict[str, Any], Path, str | None]] = []
    for page, operation in zip(aggregates, operations):
        target_path = paths.kb_dir / operation["target_path"]
        if page.get("remove_only"):
            rendered_operations.append((page, operation, target_path, None))
            continue
        if page.get("layout_finalized"):
            rendered_operations.append((page, operation, target_path, str(page["rendered_content"])))
            continue
        provenance = []
        if page.get("existing_provenance"):
            provenance.append(str(page["existing_provenance"]).strip())
        if page.get("new_provenance"):
            provenance.append("\n".join(page["new_provenance"]))
        provenance_text = "\n".join(provenance)
        prefix = str(page.get("frontmatter", ""))
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        rendered_operations.append(
            (page, operation, target_path, f"{prefix}{page['final_body']}\n\n## Provenance\n{provenance_text}\n")
        )

    written: list[tuple[dict[str, Any], dict[str, Any], Path]] = []
    try:
        for page, operation, target_path, rendered in rendered_operations:
            if rendered is None:
                if target_path.exists():
                    target_path.unlink()
            else:
                _atomic_write(target_path, rendered)
            written.append((page, operation, target_path))
    except (OSError, ValidationError) as error:
        rollback_error: Exception | None = None
        for written_page, written_operation, written_path in reversed(written):
            try:
                before = written_page.get("before_content")
                if before is None:
                    written_path.unlink(missing_ok=True)
                else:
                    _atomic_write(written_path, str(before))
                written_operation["status"] = "rolled_back"
            except (OSError, ValidationError) as restore_error:
                rollback_error = restore_error
                written_operation["status"] = "rollback_failed"
        for _page, operation, _target, _rendered in rendered_operations[len(written) :]:
            operation["status"] = "failed"
        write_jsonl(run_dir / "s5" / "write-report.jsonl", operations)
        if rollback_error is not None:
            raise ValidationError("s5", "writeback", f"write failed ({error}); rollback also failed ({rollback_error})") from error
        raise ValidationError("s5", "writeback", f"write failed; restored prior formal pages ({error})") from error

    for _page, operation, _target in written:
        operation["status"] = "success"

    write_jsonl(run_dir / "s5" / "write-report.jsonl", operations)
    return operations


def validate_archive_reason(reason: str) -> None:
    if not reason or not reason.strip():
        raise ValidationError("archive", "reason", "archive reason must not be empty")
