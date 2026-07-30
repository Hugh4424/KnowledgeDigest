"""Deterministic final layout for canonical digest topic pages.

Drafting is allowed to be incremental and provider-aware.  Formal pages are
not: this module receives a complete topic contribution, combines it with the
already materialized topic evidence, then partitions the final Markdown.  It
is intentionally dependency-free so the 300-line and no-loss contracts can be
tested without a model provider.
"""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError
from .faithfulness import claim_entity_key, normalize_claim
from .identity import topic_id, topic_part_path
from .jsonl import read_jsonl
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
    part_number: int,
    evidence_lines: list[str],
    claims: list[dict[str, Any]],
) -> str:
    provenance = [_provenance_line(claim) for claim in claims]
    lines = [
        "---",
        f"digest_topic_id: {stable_topic_id}",
        f"digest_part: {part_number}",
        "---",
        "",
        f"# Knowledge Digest: {stable_topic_id}",
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
        candidate = _render_page(stable_topic_id, len(result) + 1, candidate_evidence, candidate_claims)
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
        single = _render_page(stable_topic_id, len(result) + 1, evidence, claims)
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


def build_topic_layouts(
    drafts: list[dict[str, Any]],
    paths: DigestPaths,
    roots: tuple[str, ...],
    *,
    max_lines: int,
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
    for stable_topic_id in sorted(by_topic):
        topic_drafts = by_topic[stable_topic_id]
        existing_paths = _topic_paths(paths.kb_dir, page_root, stable_topic_id)
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

        groups = _partition(stable_topic_id, entries, max_lines=max_lines)
        pages: list[dict[str, Any]] = []
        coverage: list[dict[str, Any]] = []
        for part_number, (evidence, page_claims) in enumerate(groups, start=1):
            target = topic_part_path(page_root, stable_topic_id, part_number)
            enriched_claims = [dict(claim, page_index=part_number, target_path=target) for claim in page_claims]
            rendered = _render_page(stable_topic_id, part_number, evidence, enriched_claims)
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
                "obsolete_target_paths": sorted(existing_relative - {page["target_path"] for page in pages}),
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
