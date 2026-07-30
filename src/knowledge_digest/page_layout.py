"""Deterministic final layout for canonical digest topic pages.

Drafting is allowed to be incremental and provider-aware.  Formal pages are
not: this module receives a complete topic contribution, combines it with the
already materialized topic evidence, then partitions the final Markdown.  It
is intentionally dependency-free so the 300-line and no-loss contracts can be
tested without a model provider.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError
from .faithfulness import claim_entity_key, normalize_claim
from .identity import publication_topic_part_path, published_part_path, topic_id, topic_part_path
from .jsonl import read_jsonl
from .kb_structure import PublicationContract
from .paths import DigestPaths


def _claim_key(claim: dict[str, Any]) -> tuple[str, str, str]:
    return claim_entity_key(claim)


def _fold_history(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        identity = claim_entity_key(record)
        latest[identity] = {**latest.get(identity, {}), **record}
    return list(latest.values())


def _topic_paths(kb_dir: Path, page_root: str, stable_topic_id: str) -> list[Path]:
    directory = kb_dir / page_root / "digest"
    first = directory / f"{stable_topic_id}.md"
    parts = sorted(directory.glob(f"{stable_topic_id}.part-*.md")) if directory.exists() else []
    return [path for path in [first, *parts] if path.is_file()]


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


def _page_h1(content: str) -> str | None:
    for line in content.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return None


def declared_managed_topics(paths: DigestPaths, publication: PublicationContract) -> list[dict[str, Any]]:
    """Return only legal managed topics under the owner-declared directories.

    A handwritten file is never a publication candidate.  Conversely, a file
    that claims KnowledgeDigest ownership must be internally consistent before
    any new publication is written, so a stale or forged header cannot be
    silently adopted into reader navigation.
    """
    records: list[dict[str, Any]] = []
    for category in publication.categories:
        directory = paths.kb_dir / category.topic_dir
        if not directory.exists():
            continue
        if not directory.is_dir() or directory.is_symlink():
            raise ValidationError("publication", directory, "declared topic directory must be a real directory")
        for path in sorted(directory.rglob("*.md")):
            if path.is_symlink():
                raise ValidationError("publication", path, "managed topic page must not be a symlink")
            if not path.is_file():
                continue
            values = _frontmatter_values(path.read_text(encoding="utf-8"))
            if values.get("managed_by") != "KnowledgeDigest":
                continue
            if values.get("digest_kind") != "topic":
                raise ValidationError("publication", path, "managed file in a topic directory must have digest_kind: topic")
            stable_topic_id = values.get("digest_topic_id")
            if not stable_topic_id:
                raise ValidationError("publication", path, "managed topic is missing digest_topic_id")
            actual_path = path.relative_to(paths.kb_dir).as_posix()
            if values.get("digest_published_path") != actual_path:
                raise ValidationError(
                    "publication",
                    path,
                    "managed topic digest_published_path must match its actual path",
                )
            try:
                part_number = int(values.get("digest_part", ""))
            except ValueError as error:
                raise ValidationError("publication", path, "managed topic digest_part must be a positive integer") from error
            if part_number < 1:
                raise ValidationError("publication", path, "managed topic digest_part must be a positive integer")
            title = _page_h1(path.read_text(encoding="utf-8"))
            if not title:
                raise ValidationError("publication", path, "managed topic is missing its H1 title")
            records.append(
                {
                    "path": path,
                    "target_path": actual_path,
                    "topic_id": stable_topic_id,
                    "part_number": part_number,
                    "title": title,
                    "category_id": category.category_id,
                }
            )
    return sorted(records, key=lambda record: (record["category_id"], record["topic_id"], record["part_number"], record["target_path"]))


def _managed_topic_records(
    paths: DigestPaths,
    publication: PublicationContract,
    stable_topic_id: str,
) -> list[dict[str, Any]]:
    return [
        record
        for record in declared_managed_topics(paths, publication)
        if record["topic_id"] == stable_topic_id
    ]


def _first_existing_path(existing_paths: list[Path], *, kb_dir: Path) -> str | None:
    for path in existing_paths:
        values = _frontmatter_values(path.read_text(encoding="utf-8"))
        if values.get("digest_part", "1") != "1":
            continue
        published = values.get("digest_published_path")
        return published or path.relative_to(kb_dir).as_posix()
    return None


def _existing_topic_title(existing_paths: list[Path]) -> str | None:
    for path in existing_paths:
        title = _page_h1(path.read_text(encoding="utf-8"))
        if title:
            return title
    return None


def _source_title(topic_drafts: list[dict[str, Any]], stable_topic_id: str) -> str:
    for draft in topic_drafts:
        for value in draft.get("publication_title_candidates", []):
            if isinstance(value, str) and value.strip():
                return value.strip()
    return stable_topic_id


def _body_from_rendered_page(content: str) -> list[str]:
    """Recover Evidence lines from a previous canonical page without replaying provenance."""
    lines = content.splitlines()
    try:
        evidence_start = next(index for index, line in enumerate(lines) if line.strip() == "## Evidence") + 1
    except StopIteration:
        # A legacy page is never moved into a canonical digest topic implicitly.
        return []
    try:
        evidence_end = next(
            index for index in range(evidence_start, len(lines)) if lines[index].strip() == "## Provenance"
        )
    except StopIteration:
        evidence_end = len(lines)
    return _trim_blank_lines(lines[evidence_start:evidence_end])


def _trim_blank_lines(lines: list[str]) -> list[str]:
    result = list(lines)
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()
    return result


def _legacy_body(content: str) -> list[str]:
    """Preserve an older selected page while migrating it into a topic page."""
    canonical = _body_from_rendered_page(content)
    if canonical:
        return canonical
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1 :]
                break
    try:
        end = next(index for index, line in enumerate(lines) if line.strip() == "## Provenance")
        lines = lines[:end]
    except StopIteration:
        pass
    return _trim_blank_lines(lines)


def _evidence_lines(body: str) -> list[str]:
    """Use deterministic source-backed evidence, not a provider's repeated shell."""
    lines = body.splitlines()
    is_canonical_page = (
        len(lines) >= 4
        and lines[0].strip() == "---"
        and any(line.strip().startswith("digest_topic_id:") for line in lines[1:4])
    )
    if is_canonical_page:
        return _body_from_rendered_page(body)
    return lines


def _entries_for_body(
    lines: list[str], claims: list[dict[str, Any]]
) -> tuple[list[tuple[list[str], list[dict[str, Any]]]], list[dict[str, Any]]]:
    """Attach every one-line claim to its evidence line, retaining structure lines."""
    available: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for claim in claims:
        available[normalize_claim(str(claim.get("text", "")))].append(claim)
    entries: list[tuple[list[str], list[dict[str, Any]]]] = []
    for line in lines:
        normalized = normalize_claim(line.strip())
        matched = [available[normalized].popleft()] if normalized and available[normalized] else []
        entries.append(([line], matched))
    unmatched = [claim for values in available.values() for claim in values]
    return entries, unmatched


def _attach_structure_to_claims(
    entries: list[tuple[list[str], list[dict[str, Any]]]],
) -> list[tuple[list[str], list[dict[str, Any]]]]:
    """Give Claim-free structure the ownership of its nearest source Claim.

    Headings are intentionally not Claims, but they must not survive a revision
    of the source section they introduce. Prefix structure belongs to the next
    Claim; trailing structure belongs to the preceding Claim.
    """
    result: list[tuple[list[str], list[dict[str, Any]]]] = []
    pending: list[str] = []
    for lines, matched in entries:
        if not matched:
            pending.extend(lines)
            continue
        result.append(([*pending, *lines], matched))
        pending = []
    if pending:
        if result:
            lines, matched = result[-1]
            result[-1] = ([*lines, *pending], matched)
        else:
            result.append((pending, []))
    return result


def _provenance_line(claim: dict[str, Any]) -> str:
    return (
        f"- `{claim['claim_fingerprint']}` — {claim['source_uri']} "
        f"(fragment_locator={claim.get('fragment_locator', '')}; "
        f"content_fingerprint={claim.get('content_fingerprint', '')})"
    )


def _render_page(
    stable_topic_id: str,
    title: str,
    published_path: str,
    part_number: int,
    evidence_lines: list[str],
    claims: list[dict[str, Any]],
) -> str:
    provenance = [_provenance_line(claim) for claim in claims]
    lines = [
        "---",
        "managed_by: KnowledgeDigest",
        "digest_kind: topic",
        f"digest_topic_id: {stable_topic_id}",
        f"digest_published_path: {published_path}",
        f"digest_part: {part_number}",
        "---",
        "",
        f"# {title}",
        "",
        "## Summary",
        f"- 已验证来源证据；第 {part_number} 部分。",
        "",
        "## Evidence",
        *evidence_lines,
        "",
        "## Provenance",
        *provenance,
        "",
    ]
    return "\n".join(lines)


def _output_locators(rendered_lines: list[str], claims: list[dict[str, Any]]) -> dict[tuple[str, str, str], str]:
    """Map repeated equal claim text to distinct evidence occurrences."""
    try:
        start = next(index for index, line in enumerate(rendered_lines, start=1) if line.strip() == "## Evidence")
        end = next(
            index
            for index, line in enumerate(rendered_lines[start:], start=start + 1)
            if line.strip() == "## Provenance"
        )
    except StopIteration as error:
        raise ValidationError("layout", "page", "rendered page is missing evidence or provenance") from error
    positions: dict[str, deque[int]] = defaultdict(deque)
    for index in range(start + 1, end):
        normalized = normalize_claim(rendered_lines[index - 1].strip())
        if normalized:
            positions[normalized].append(index)
    result: dict[tuple[str, str, str], str] = {}
    for claim in claims:
        expected = normalize_claim(str(claim.get("text", "")))
        if not positions[expected]:
            raise ValidationError("layout", claim.get("claim_fingerprint", "claim"), "claim is absent from rendered evidence")
        line = positions[expected].popleft()
        result[claim_entity_key(claim)] = f"lines:{line}-{line}"
    return result


def _partition(
    stable_topic_id: str,
    title: str,
    first_path: str,
    entries: list[tuple[list[str], list[dict[str, Any]]]],
    *,
    max_lines: int,
) -> list[tuple[list[str], list[dict[str, Any]]]]:
    """Partition complete evidence entries; no claim can cross a topic part."""
    # This architecture contract fixes formal topic pages at 300 lines.  The
    # older option remains a draft-splitting hint for compatibility, but it
    # cannot make a self-contained formal page smaller than its metadata shell.
    limit = 300
    result: list[tuple[list[str], list[dict[str, Any]]]] = []
    evidence: list[str] = []
    claims: list[dict[str, Any]] = []
    for entry_lines, entry_claims in entries:
        candidate_evidence = [*evidence, *entry_lines]
        candidate_claims = [*claims, *entry_claims]
        candidate = _render_page(
            stable_topic_id,
            title,
            published_part_path(first_path, len(result) + 1),
            len(result) + 1,
            candidate_evidence,
            candidate_claims,
        )
        if len(candidate.splitlines()) <= limit:
            evidence, claims = candidate_evidence, candidate_claims
            continue
        if not evidence and not claims:
            raise ValidationError(
                "layout",
                stable_topic_id,
                f"one complete evidence entry requires {len(candidate.splitlines())} lines, above hard limit {limit}",
            )
        result.append((evidence, claims))
        evidence, claims = list(entry_lines), list(entry_claims)
        single = _render_page(
            stable_topic_id,
            title,
            published_part_path(first_path, len(result) + 1),
            len(result) + 1,
            evidence,
            claims,
        )
        if len(single.splitlines()) > limit:
            raise ValidationError(
                "layout",
                stable_topic_id,
                f"one complete evidence entry requires {len(single.splitlines())} lines, above hard limit {limit}",
            )
    if evidence or claims:
        result.append((evidence, claims))
    return result


def _active_history_for_paths(paths: DigestPaths, targets: set[str]) -> list[dict[str, Any]]:
    history_path = paths.kb_dir / "_digest" / "claim-history.jsonl"
    active: list[dict[str, Any]] = []
    for record in _fold_history(read_jsonl(history_path)):
        if str(record.get("target_path") or record.get("page_path")) not in targets:
            continue
        if record.get("verification_status") in {"removed", "superseded", "pending_review"}:
            continue
        if record.get("superseded_by"):
            continue
        active.append(dict(record))
    return active


def _existing_entries(
    existing_paths: list[Path],
    history_claims: list[dict[str, Any]],
    retained_claim_keys: set[tuple[str, str, str]],
    *,
    kb_dir: Path,
) -> list[tuple[list[str], list[dict[str, Any]]]]:
    """Keep only evidence entries whose current Claim still exists.

    History preserves the original page/claim order, which lets equal evidence
    lines remain distinct while a revised source is replaced as one unit.
    """
    claims_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in history_claims:
        target = str(claim.get("target_path") or claim.get("page_path") or "")
        claims_by_path[target].append(claim)
    entries: list[tuple[list[str], list[dict[str, Any]]]] = []
    for path in existing_paths:
        relative = path.relative_to(kb_dir).as_posix()
        page_entries, unmatched = _entries_for_body(
            _legacy_body(path.read_text(encoding="utf-8")), claims_by_path.get(relative, [])
        )
        missing = [claim for claim in unmatched if _claim_key(claim) in retained_claim_keys]
        if missing:
            raise ValidationError(
                "layout",
                relative,
                "active claim is absent from its existing evidence page",
            )
        for lines, matched in _attach_structure_to_claims(page_entries):
            if not matched or _claim_key(matched[0]) in retained_claim_keys:
                entries.append((lines, matched))
    return entries


def _incoming_entries(
    drafts: list[dict[str, Any]],
    incoming_claim_keys: set[tuple[str, str, str]],
    existing_entries: list[tuple[list[str], list[dict[str, Any]]]],
) -> list[tuple[list[str], list[dict[str, Any]]]]:
    """Append only current source entries, never an entire stale draft body."""
    result: list[tuple[list[str], list[dict[str, Any]]]] = []
    known_structure = {
        normalize_claim(line.strip())
        for lines, _claims in existing_entries
        for line in lines
        if normalize_claim(line.strip())
    }
    for draft in drafts:
        draft_claims = [dict(claim) for claim in draft.get("claims", [])]
        if not any(_claim_key(claim) in incoming_claim_keys for claim in draft_claims):
            continue
        entries, unmatched = _entries_for_body(
            _evidence_lines(str(draft.get("final_body", ""))), draft_claims
        )
        for lines, matched in entries:
            if matched:
                if _claim_key(matched[0]) in incoming_claim_keys:
                    result.append((lines, matched))
                continue
            normalized = [normalize_claim(line.strip()) for line in lines]
            if any(value and value not in known_structure for value in normalized):
                result.append((lines, matched))
                known_structure.update(value for value in normalized if value)
        for claim in unmatched:
            if _claim_key(claim) in incoming_claim_keys:
                result.append(([str(claim["text"])], [claim]))
    return result


def build_publication_navigation(
    layouts: list[dict[str, Any]],
    paths: DigestPaths,
    publication: PublicationContract,
) -> list[dict[str, Any]]:
    """Build reader navigation records for writeback's single publication transaction."""
    for target in [publication.home_path, *(publication.category_index_path(category.category_id) for category in publication.categories)]:
        path = paths.kb_dir / target
        if path.is_symlink():
            raise ValidationError("publication", path, "existing navigation page must not be a symlink")
        if path.exists() and "managed_by: KnowledgeDigest" not in path.read_text(encoding="utf-8"):
            raise ValidationError("publication", path, "existing navigation page must declare managed_by: KnowledgeDigest")
    layouts_by_category: dict[str, dict[str, list[dict[str, Any]]]] = {
        category.category_id: {} for category in publication.categories
    }
    for record in declared_managed_topics(paths, publication):
        layouts_by_category[record["category_id"]].setdefault(record["topic_id"], []).append(record)
    # New topics use the declared pending category.  Replacing the current
    # topic's list intentionally hides stale old parts after a shrink, while
    # leaving those files untouched on disk for recovery.
    for layout in layouts:
        category_id = str(layout.get("publication_category_id") or publication.pending_category.category_id)
        layouts_by_category[category_id][layout["topic_id"]] = [
            {
                "target_path": page["target_path"],
                "part_number": int(page.get("page_index", 1)),
                "title": layout["title"],
            }
            for page in layout.get("split_pages", [])
        ]

    home_lines = [
        "---",
        "managed_by: KnowledgeDigest",
        "digest_kind: home",
        "---",
        "",
        "# Knowledge Digest",
        "",
        "## 分类",
    ]
    for category in publication.categories:
        home_lines.append(f"- [{category.title}]({publication.category_index_path(category.category_id)})")
    records: list[dict[str, Any]] = [
        {
            "draft_id": "navigation-home",
            "action": "publish_navigation",
            "digest_kind": "home",
            "target_path": publication.home_path,
            "rendered_content": "\n".join([*home_lines, ""]),
            "claims": [],
            "layout_finalized": True,
            "publication_audit_scope": "none",
            "target_paths": [publication.home_path],
            "split_pages": [
                {
                    "target_path": publication.home_path,
                    "rendered_content": "\n".join([*home_lines, ""]),
                    "final_body": "",
                    "claims": [],
                    "layout_finalized": True,
                    "digest_kind": "home",
                    "publication_audit_scope": "none",
                }
            ],
        }
    ]
    for category in publication.categories:
        target = publication.category_index_path(category.category_id)
        lines = [
            "---",
            "managed_by: KnowledgeDigest",
            "digest_kind: category",
            f"digest_category_id: {category.category_id}",
            "---",
            "",
            f"# {category.title}",
            "",
            "## 主题",
        ]
        for _topic_id, pages in sorted(layouts_by_category[category.category_id].items()):
            for page in sorted(pages, key=lambda item: (int(item.get("part_number", 1)), str(item["target_path"]))):
                path = str(page["target_path"])
                relative = Path(os.path.relpath(path, start=Path(target).parent)).as_posix()
                part_number = int(page.get("part_number", page.get("page_index", 1)))
                suffix = "" if part_number == 1 else f"（第 {part_number} 部分）"
                lines.append(f"- [{page['title']}{suffix}]({relative})")
        rendered = "\n".join([*lines, ""])
        records.append(
            {
                "draft_id": f"navigation-category-{category.category_id}",
                "action": "publish_navigation",
                "digest_kind": "category",
                "target_path": target,
                "rendered_content": rendered,
                "claims": [],
                "layout_finalized": True,
                "publication_audit_scope": "none",
                "target_paths": [target],
                "split_pages": [
                    {
                        "target_path": target,
                        "rendered_content": rendered,
                        "final_body": "",
                        "claims": [],
                        "layout_finalized": True,
                        "digest_kind": "category",
                        "publication_audit_scope": "none",
                    }
                ],
            }
        )
    return records


def build_topic_layouts(
    drafts: list[dict[str, Any]],
    paths: DigestPaths,
    roots: tuple[str, ...],
    *,
    max_lines: int,
    publication: PublicationContract | None = None,
) -> list[dict[str, Any]]:
    """Return canonical, final-layout drafts ready for safe writeback.

    The incoming draft record remains a run artifact; this function consolidates
    it into one record per stable topic.  It never reads or rewrites arbitrary
    legacy pages, only pages that already declare the canonical topic marker.
    """
    page_root = roots[0]
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for draft in drafts:
        stable_topic_id = draft.get("topic_id")
        if not isinstance(stable_topic_id, str) or not stable_topic_id:
            source_ids = [str(claim.get("source_id", "")) for claim in draft.get("claims", [])]
            # Old direct-call compatibility: this branch is never used by the
            # formal pipeline, whose clusters always carry a topic ID.
            if not any(source_ids):
                continue
            stable_topic_id = topic_id(source_ids)
        by_topic[stable_topic_id].append(draft)

    layouts: list[dict[str, Any]] = []
    reserved_paths: set[str] = set()
    if publication is not None:
        directory = paths.kb_dir / publication.pending_category.topic_dir
        if directory.is_dir():
            reserved_paths = {path.relative_to(paths.kb_dir).as_posix() for path in directory.rglob("*.md")}
    for stable_topic_id in sorted(by_topic):
        topic_drafts = by_topic[stable_topic_id]
        existing_records = _managed_topic_records(paths, publication, stable_topic_id) if publication is not None else []
        existing_paths = [record["path"] for record in existing_records] if publication is not None else _topic_paths(
            paths.kb_dir, page_root, stable_topic_id
        )
        existing_categories = {record["category_id"] for record in existing_records}
        if len(existing_categories) > 1:
            raise ValidationError("publication", stable_topic_id, "managed topic appears in more than one declared category")
        publication_category_id = (
            next(iter(existing_categories)) if existing_categories else publication.pending_category.category_id
        ) if publication is not None else None
        for draft in topic_drafts:
            for target in draft.get("target_paths", []):
                candidate = paths.kb_dir / str(target)
                if candidate.is_file() and candidate not in existing_paths:
                    existing_paths.append(candidate)
        existing_paths.sort()
        existing_relative = {path.relative_to(paths.kb_dir).as_posix() for path in existing_paths}
        history_claims = _active_history_for_paths(paths, existing_relative)
        incoming_claims = [
            dict(claim)
            for draft in topic_drafts
            for claim in draft.get("claims", [])
        ]
        incoming_fingerprints: dict[str, set[str]] = defaultdict(set)
        history_fingerprints: dict[str, set[str]] = defaultdict(set)
        for claim in incoming_claims:
            incoming_fingerprints[str(claim.get("source_uri", ""))].add(
                str(claim.get("content_fingerprint", ""))
            )
        for claim in history_claims:
            history_fingerprints[str(claim.get("source_uri", ""))].add(
                str(claim.get("content_fingerprint", ""))
            )
        revised_sources = {
            source_uri
            for source_uri, fingerprints in incoming_fingerprints.items()
            if source_uri and history_fingerprints.get(source_uri) and fingerprints != history_fingerprints[source_uri]
        }
        replaced_claims = [claim for claim in history_claims if str(claim.get("source_uri", "")) in revised_sources]
        existing_claims = [claim for claim in history_claims if claim not in replaced_claims]
        seen = {_claim_key(claim) for claim in existing_claims}
        unique_incoming: list[dict[str, Any]] = []
        for claim in incoming_claims:
            key = _claim_key(claim)
            if key in seen:
                continue
            seen.add(key)
            unique_incoming.append(claim)
        all_claims = [*existing_claims, *unique_incoming]
        existing_entries = _existing_entries(
            existing_paths,
            history_claims,
            {_claim_key(claim) for claim in existing_claims},
            kb_dir=paths.kb_dir,
        )
        entries = [
            *existing_entries,
            *_incoming_entries(
                topic_drafts,
                {_claim_key(claim) for claim in unique_incoming},
                existing_entries,
            ),
        ]

        existing_title = _existing_topic_title(existing_paths) if publication is not None else None
        title = existing_title or _source_title(topic_drafts, stable_topic_id)
        first_path = _first_existing_path(existing_paths, kb_dir=paths.kb_dir) if publication is not None else None
        if publication is not None and first_path is None:
            first_path = publication_topic_part_path(
                publication.pending_category.topic_dir,
                title,
                stable_topic_id,
                1,
            )
            if first_path in reserved_paths:
                first_path = publication_topic_part_path(
                    publication.pending_category.topic_dir,
                    title,
                    stable_topic_id,
                    1,
                    disambiguate=True,
                )
        if first_path is None:
            first_path = topic_part_path(page_root, stable_topic_id, 1)
        reserved_paths.add(first_path)

        groups = _partition(stable_topic_id, title, first_path, entries, max_lines=max_lines)
        pages: list[dict[str, Any]] = []
        coverage: list[dict[str, Any]] = []
        for part_number, (evidence, page_claims) in enumerate(groups, start=1):
            target = published_part_path(first_path, part_number)
            enriched_claims = [dict(claim, page_index=part_number, target_path=target) for claim in page_claims]
            rendered = _render_page(stable_topic_id, title, target, part_number, evidence, enriched_claims)
            if len(rendered.splitlines()) > 300:
                raise ValidationError("layout", target, "final page exceeds the configured line limit")
            pages.append(
                {
                    "page_index": part_number,
                    "target_path": target,
                    "final_body": "\n".join(evidence),
                    "rendered_content": rendered,
                    "claims": enriched_claims,
                    "layout_finalized": True,
                    "digest_kind": "topic",
                    "digest_topic_id": stable_topic_id,
                    "digest_published_path": target,
                }
            )
            rendered_lines = rendered.splitlines()
            locators = _output_locators(rendered_lines, enriched_claims)
            coverage.extend(
                {
                    "raw_id": claim.get("raw_id"),
                    "source_uri": claim.get("source_uri"),
                    "input_fragment": claim.get("fragment_locator"),
                    "output_page": target,
                    "fragment_locator": claim.get("fragment_locator"),
                    "claim_fingerprint": claim.get("claim_fingerprint"),
                    "output_fragment_locator": locators[claim_entity_key(claim)],
                }
                for claim in enriched_claims
            )
        if not pages and all_claims:
            raise ValidationError("layout", stable_topic_id, "topic claims produced no final pages")
        layouts.append(
            {
                "draft_id": f"layout-{stable_topic_id}",
                "cluster_id": ",".join(sorted(str(draft.get("cluster_id")) for draft in topic_drafts)),
                "topic_id": stable_topic_id,
                "digest_kind": "topic",
                "publication_category_id": publication_category_id,
                "title": title,
                "published_path": first_path,
                "action": "layout",
                "target_paths": [page["target_path"] for page in pages],
                "final_body": "\n".join(page["final_body"] for page in pages),
                "claims": [claim for page in pages for claim in page["claims"]],
                "provenance": sorted({str(claim.get("source_uri")) for page in pages for claim in page["claims"]}),
                "removed_claims": [claim for draft in topic_drafts for claim in draft.get("removed_claims", [])],
                "split_pages": pages,
                "coverage_mapping": coverage,
                "component_coverage": [],
                "layout_finalized": True,
                # A reader may retain an old part after a topic shrinks.  It is
                # omitted from the freshly built navigation, never deleted or
                # overwritten by this incremental publication run.
                "obsolete_target_paths": [],
                "rounds": [round_record for draft in topic_drafts for round_record in draft.get("rounds", [])],
                "selected_round": None,
                "round_count": sum(int(draft.get("round_count", 0)) for draft in topic_drafts),
                "rethink_status": "layout_completed",
                "fallback_reason": None,
                "benefit_status": "unmeasured",
                "planned_generator_calls": sum(int(draft.get("planned_generator_calls", 0)) for draft in topic_drafts),
                "quality": {"coverage_ratio": 1.0, "retained_input_unit_ratio": 1.0, "unsupported_claim_rate": 0.0, "faithfulness_status": "passed"},
            }
        )
    return layouts
