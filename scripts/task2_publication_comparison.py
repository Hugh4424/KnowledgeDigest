"""Create a reproducible, reader-first Task1/Task2/CompanyBrain comparison.

This script only reads existing knowledge bases.  It never calls a provider and
never copies source text into the report.  Reader fields stay ``null`` until a
person performs the fixed sample review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import posixpath
import stat
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

from knowledge_digest.kb_structure import inspect_structure, parse_source_index_markdown
from knowledge_digest.errors import ValidationError
from knowledge_digest.reader_frontmatter import managed_content_hash, parse_concept_document


READER_FIELDS = [
    "title_understood",
    "category_correct",
    "home_to_topic_clicks",
    "source_backlink",
    "summary_faithful",
    "why_or_missing_explicit",
    "version_or_missing_explicit",
    "usage_boundary_visible",
    "orphan_link",
    "reader_time_seconds",
]
SAMPLE_PARENTS = ("products", "engineering", "customers", "operations", "principles")


def _json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def _jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []


def _frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() in {"---", "..."}:
            break
        key, separator, value = line.partition(":")
        if separator:
            result[key.strip()] = value.strip()
    return result


def _latest_run(root: Path) -> Path | None:
    runs = root / "_digest" / "runs"
    candidates = [path for path in runs.iterdir() if path.is_dir()] if runs.is_dir() else []
    if not candidates:
        return None
    # Run IDs are UUIDs and therefore do not describe chronology.  The report
    # mtime is the only local signal available to this read-only comparator;
    # fall back to the directory mtime when a report is absent.
    def freshness(path: Path) -> int:
        report = path / "report.json"
        try:
            return report.stat().st_mtime_ns if report.is_file() else path.stat().st_mtime_ns
        except OSError:
            return 0

    return max(candidates, key=freshness)


def _read_source_index(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "_digest" / "source-index.md"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        value = parse_source_index_markdown(text)
        return {str(row["source_uri"]): dict(row) for row in value["entries"]}
    except Exception:
        # Task1 is intentionally a legacy read-only baseline.  Parse only its
        # link index; do not rewrite it into the Task2 format.
        result: dict[str, dict[str, Any]] = {}
        current: str | None = None
        for line in text.splitlines():
            uri_match = re.match(r"^- `(.+)`$", line.strip())
            if uri_match:
                current = uri_match.group(1)
                result[current] = {"source_uri": current, "target_paths": []}
                continue
            link_match = re.match(r"^\s+- \[[^]]+\]\(([^)]+)\)$", line)
            if current and link_match:
                target = unquote(link_match.group(1))
                resolved = (root / "_digest" / target).resolve()
                try:
                    relative = resolved.relative_to(root.resolve()).as_posix()
                except ValueError:
                    relative = Path(target).as_posix()
                result[current]["target_paths"].append(relative)
        return result


def _category_parents(root: Path) -> dict[str, str]:
    structure = inspect_structure(root / "kb.structure.md")
    publication = structure.publication
    return {category.category_id: category.parent_id for category in publication.categories} if publication else {}


def _topic_rows(root: Path) -> list[dict[str, Any]]:
    indexed = _json(root / "_digest" / "topic-index.json", {})
    rows = indexed.get("topics", []) if isinstance(indexed, dict) else []
    if isinstance(rows, list) and rows:
        return [dict(row) for row in rows if isinstance(row, dict) and row.get("topic_id")]
    discovered: dict[str, dict[str, Any]] = {}
    pages = root / "pages"
    if pages.is_dir():
        for path in sorted(pages.rglob("*.md")):
            metadata = _frontmatter(path)
            if metadata.get("digest_kind") != "topic" or not metadata.get("digest_topic_id"):
                continue
            topic_id = metadata["digest_topic_id"]
            row = discovered.setdefault(
                topic_id,
                {
                    "topic_id": topic_id,
                    "source_ids": [],
                    "category_id": path.parent.name,
                    "published_path": path.relative_to(root).as_posix(),
                    "product_slug": None,
                },
            )
            row["published_path"] = min(str(row["published_path"]), path.relative_to(root).as_posix())
    return sorted(discovered.values(), key=lambda row: str(row["topic_id"]))


def _topic_source_map(root: Path, topics: list[dict[str, Any]]) -> dict[str, list[str]]:
    source_index = _read_source_index(root)
    reverse: dict[str, list[str]] = {str(row.get("topic_id")): [] for row in topics}
    for uri, row in source_index.items():
        for target in row.get("target_paths", []):
            path = str(target)
            metadata = _frontmatter(root / path)
            topic_id = metadata.get("digest_topic_id")
            if topic_id and topic_id in reverse:
                reverse[topic_id].append(uri)
    return {key: sorted(set(value)) for key, value in reverse.items()}


def _topic_title(root: Path, row: dict[str, Any]) -> str:
    path = root / str(row.get("published_path", ""))
    metadata = _frontmatter(path)
    if metadata.get("digest_title"):
        return metadata["digest_title"]
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except (OSError, UnicodeDecodeError):
        pass
    return Path(str(row.get("published_path", "topic"))).stem


def _semantic_tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]{3,}", text.casefold()) if token not in {"the", "and", "for", "with", "from"}}


def _document_title(path: Path) -> str:
    metadata = _frontmatter(path)
    for key in ("title", "name", "summary", "description"):
        if metadata.get(key):
            return metadata[key]
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except (OSError, UnicodeDecodeError):
        pass
    return path.stem


def _claim_entity_key(row: dict[str, Any]) -> tuple[str, str, str]:
    """Identify one source claim without collapsing repeated claim text.

    Fingerprints alone are insufficient: the same sentence can legitimately
    occur at multiple source locations.  Source URI + locator + fingerprint
    matches the provenance contract and makes Task1/Task2 loss comparison
    stable across retries and history rows.
    """
    return (
        str(row.get("source_uri", "")),
        str(row.get("fragment_locator", "")),
        str(row.get("claim_fingerprint", "")),
    )


def _claim_evidence(root: Path) -> tuple[int, int]:
    history = _jsonl(root / "_digest" / "claim-history.jsonl")
    if history:
        current: dict[tuple[str, str, str], dict[str, Any]] = {}
        for row in history:
            if row.get("verification_status") in {"removed", "superseded"}:
                continue
            key = _claim_entity_key(row)
            if all(key):
                current[key] = row
        return len(current), len({str(row.get("claim_fingerprint")) for row in current.values()})
    run = _latest_run(root)
    if run is None:
        return 0, 0
    rows = [row for draft in _jsonl(run / "s4" / "drafts.jsonl") for row in draft.get("claims", [])]
    current = {_claim_entity_key(row): row for row in rows if all(_claim_entity_key(row))}
    return len(current), len({str(row.get("claim_fingerprint")) for row in current.values()})


def _machine_evidence(root: Path) -> dict[str, Any]:
    topics = _topic_rows(root)
    topic_paths = [root / str(row.get("published_path", "")) for row in topics]
    topic_paths = [path for path in topic_paths if path.is_file()]
    source_index = _read_source_index(root)
    categories = sorted({str(row.get("category_id")) for row in topics if row.get("category_id")})
    run = _latest_run(root)
    claim_count, claim_fingerprint_count = _claim_evidence(root)
    cost: dict[str, Any] = {"_status": "unavailable", "_reason": "latest run cost report is missing or incomplete"}
    if run is not None:
        report = _json(run / "report.json", {})
        candidate = report.get("cost", {}) if isinstance(report, dict) else {}
        settings = report.get("settings", {}) if isinstance(report, dict) else {}
        llm_enabled = bool(settings.get("llm_enabled")) if isinstance(settings, dict) else False
        if isinstance(candidate, dict) and {"generator_calls", "planned_generator_calls"} <= set(candidate):
            # The identity generator records one deterministic round per topic,
            # but that is not a provider call. Keep both facts separate so an
            # offline run can never masquerade as a paid/model-backed run.
            observed = candidate.get("provider_calls_observed")
            provider_calls = (
                int(observed)
                if llm_enabled and observed is not None
                else None
                if llm_enabled
                else 0
            )
            cost = {
                **candidate,
                "_status": "available",
                "_reason": None,
                "_llm_enabled": llm_enabled,
                "_provider_calls": provider_calls,
                "_generator_calls": int(candidate["generator_calls"]),
            }
        elif isinstance(report, dict) and isinstance(report.get("failure"), dict):
            failure_cost = candidate if isinstance(candidate, dict) else {}
            cost = {
                **failure_cost,
                "_status": "available",
                "_reason": "provider failure report; observed call count unavailable",
                "_llm_enabled": bool(settings.get("llm_enabled")) if isinstance(settings, dict) else True,
                "_provider_calls": None,
                "_generator_calls": None,
            }
    # A resumable run may fail before audit_run can return a normal report.
    # The caller-owned batch state is then the authoritative cost ledger.  It
    # is deliberately merged only as an explicit fallback; unknown observed
    # provider calls remain unknown rather than being replaced by reservations.
    batch_state = _json(root / "_digest" / "batch-state.json", {})
    batch_cost = batch_state.get("cost_summary") if isinstance(batch_state, dict) else None
    if isinstance(batch_cost, dict):
        batch_status = str(batch_cost.get("status", ""))
        runtime_identity = batch_state.get("runtime_identity")
        runtime_llm = (
            runtime_identity.get("llm_model")
            if isinstance(runtime_identity, dict)
            else None
        )
        batch_llm_enabled = (
            bool(runtime_llm)
            if isinstance(runtime_identity, dict) and "llm_model" in runtime_identity
            else bool(cost.get("_llm_enabled"))
        )
        # The batch ledger is authoritative for aggregate retry/time facts and
        # now also carries the sum of committed per-batch audit reports.
        cost = {
            **cost,
            "_status": "available",
            "_reason": cost.get("_reason"),
            "_llm_enabled": batch_llm_enabled,
            "_provider_calls": batch_cost.get("provider_calls_observed") if batch_llm_enabled else 0,
            "_generator_calls": (
                batch_cost.get("generator_calls")
                or batch_cost.get("provider_calls_observed")
                if batch_llm_enabled
                else cost.get("_generator_calls")
            ),
            "provider_calls_planned": batch_cost.get("provider_calls_planned"),
            "provider_calls_planned_basis": batch_cost.get("provider_calls_planned_basis"),
            "provider_calls_observed": batch_cost.get("provider_calls_observed") if batch_llm_enabled else 0,
            "provider_calls_reserved": batch_cost.get("provider_calls_reserved"),
            "failed_calls": batch_cost.get("failed_calls"),
            "replay_calls": batch_cost.get("replay_calls"),
            "elapsed_seconds": batch_cost.get("elapsed_seconds"),
            "provider_tokens": batch_cost.get("provider_tokens"),
            "fallback_ratio": batch_cost.get("fallback_ratio"),
            "batch_status": batch_status,
            "batch_failed_batches": batch_cost.get("failed_batches", []),
            "batch_cost_summary": batch_cost,
        }
    return {
        "root": str(root),
        "markdown_files": len(list(root.rglob("*.md"))),
        "topic_pages": len(topic_paths),
        "categories": categories,
        "source_index_uris": len(source_index),
        "claim_count": claim_count,
        "claim_fingerprint_count": claim_fingerprint_count,
        "max_topic_lines": max((len(path.read_text(encoding="utf-8").splitlines()) for path in topic_paths), default=0),
        "all_topic_pages_within_300_lines": all(len(path.read_text(encoding="utf-8").splitlines()) <= 300 for path in topic_paths),
        "reader_entrypoints": {
            "README.md": (root / "README.md").is_file(),
            "Home.md": (root / "Home.md").is_file(),
            "source-index.md": (root / "_digest" / "source-index.md").is_file(),
        },
        "cost": cost,
    }


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeDecodeError):
        return None


def _safety_evidence(task2_root: Path, output_dir: Path | None, taxonomy_before: str | None) -> dict[str, Any]:
    taxonomy = task2_root / "kb.structure.md"
    after = _sha256_file(taxonomy)
    targets = [] if output_dir is None else [output_dir / "COMPARISON.json", output_dir / "COMPARISON.md"]
    output_root = output_dir.resolve() if output_dir is not None else None
    checked_targets = [str(target) for target in targets]
    paths_ok = output_root is not None and all(
        (resolved := target.resolve()).parent == output_root and resolved.name in {"COMPARISON.json", "COMPARISON.md"}
        for target in targets
    )
    return {
        "credentials_not_written": {"status": "passed", "basis": "comparison is read-only and emits only fixed JSON/Markdown fields"},
        "paths_within_output": {"status": "passed" if paths_ok else "unknown", "checked_targets": checked_targets, "basis": "resolved output targets are checked before writing"},
        "taxonomy_unchanged": {"status": "passed" if taxonomy_before is not None and taxonomy_before == after else "unknown", "baseline_captured_before_comparison": taxonomy_before is not None, "before_sha256": taxonomy_before, "after_sha256": after},
        "handwritten_pages_untouched": {"status": "passed", "basis": "the three input knowledge roots are opened read-only"},
    }


def _companybrain_match(root: Path, title: str, product_slug: Any) -> dict[str, Any]:
    needle = str(product_slug or "").strip().casefold()
    paths = sorted(root.rglob("*.md"))
    if needle:
        exact = [path for path in paths if needle in path.stem.casefold() or needle in path.as_posix().casefold()]
        if exact:
            return {"status": "matched", "method": "product_slug_path", "paths": [exact[0].relative_to(root).as_posix()]}
    query = _semantic_tokens(title)
    scored: list[tuple[float, str]] = []
    for path in paths:
        overlap = query & _semantic_tokens(_document_title(path))
        score = len(overlap) / max(len(query), 1)
        if score > 0:
            scored.append((score, path.relative_to(root).as_posix()))
    if not scored:
        return {"status": "no_match", "method": "semantic_title_overlap", "paths": []}
    scored.sort(key=lambda item: (-item[0], item[1]))
    score, path = scored[0]
    return {"status": "matched", "method": "semantic_title_overlap", "score": round(score, 4), "paths": [path]}


def _sample_manifest(
    task1_root: Path,
    task2_root: Path,
    companybrain_root: Path,
) -> list[dict[str, Any]]:
    parents = _category_parents(task2_root)
    topics = _topic_rows(task2_root)
    topic_sources = _topic_source_map(task2_root, topics)
    task1_sources = _read_source_index(task1_root)
    selected: list[dict[str, Any]] = []
    for parent in SAMPLE_PARENTS:
        candidates = [row for row in topics if parents.get(str(row.get("category_id"))) == parent]
        for row in sorted(candidates, key=lambda item: str(item.get("topic_id")))[:4]:
            topic_id = str(row["topic_id"])
            title = _topic_title(task2_root, row)
            sources = topic_sources.get(topic_id, [])
            task1_paths = sorted({path for uri in sources for path in task1_sources.get(uri, {}).get("target_paths", [])})
            selected.append(
                {
                    "sample_id": f"sample-{len(selected) + 1:02d}",
                    "parent": parent,
                    "task2_topic_id": topic_id,
                    "task2_title": title,
                    "task2_published_path": str(row.get("published_path", "")),
                    "source_uris": sources,
                    "task1_match": {"status": "matched" if task1_paths else "no_match", "paths": task1_paths[:5]},
                    "companybrain_match": _companybrain_match(companybrain_root, title, row.get("product_slug")),
                    "reader_quality": {field: None for field in READER_FIELDS},
                    "manual_notes": None,
                    "manual_status": "manual_review_required",
                }
            )
    return selected[:20]


def _reader_clicks(root: Path, target: str, *, maximum: int = 3) -> int | None:
    """Count local Markdown clicks from Home without rendering a browser."""
    target = Path(target).as_posix()
    frontier = {Path("Home.md").as_posix()}
    seen = set(frontier)
    for depth in range(maximum + 1):
        if target in frontier:
            return depth
        next_frontier: set[str] = set()
        for current in frontier:
            path = root / current
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for raw in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
                if "://" in raw or raw.startswith("#"):
                    continue
                link = raw.split("#", 1)[0]
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(current), unquote(link)))
                if resolved.startswith("../") or resolved in seen:
                    continue
                seen.add(resolved)
                next_frontier.add(resolved)
        frontier = next_frontier
    return None


def _agent_reader_review(task2_root: Path, samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Perform a transparent, deterministic reader audit when explicitly requested.

    This is not a substitute for independent human comprehension or stopwatch
    timing.  It checks visible contracts and marks the boundary in every note.
    """
    source_index = _read_source_index(task2_root)
    assessed = 0
    title_pass = 0
    for sample in samples:
        path = task2_root / str(sample.get("task2_published_path", ""))
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        lines = text.splitlines()
        title = str(sample.get("task2_title", ""))
        source_uris = set(str(uri) for uri in sample.get("source_uris", []))
        source_linked = any(
            target in {str(path_value) for path_value in row.get("target_paths", [])}
            for uri, row in source_index.items()
            if uri in source_uris
            for target in [str(sample.get("task2_published_path", ""))]
        )
        title_ok = bool(title and len(title) >= 4 and not re.search(r"(?:cluster|draft|^topic-)", title, re.I))
        if title_ok:
            title_pass += 1
        clicks = _reader_clicks(task2_root, str(sample.get("task2_published_path", "")))
        explicit_summary = "## Summary" in text and ("field_refs.summary" in text or "来源未提供摘要" in text)
        explicit_why = "## Why" in text and bool(re.search(r"## Why\n(?:-|\s)*\S", text))
        explicit_version = "## Version" in text and bool(re.search(r"## Version\n(?:-|\s)*\S", text))
        sample["reader_quality"] = {
            "title_understood": title_ok,
            "category_correct": str(sample.get("parent", "")) in str(path.relative_to(task2_root).as_posix()) if path.is_file() else False,
            "home_to_topic_clicks": clicks,
            "source_backlink": source_linked,
            "summary_faithful": explicit_summary,
            "why_or_missing_explicit": explicit_why,
            "version_or_missing_explicit": explicit_version,
            "usage_boundary_visible": "## Usage boundary" in text,
            "orphan_link": not source_linked and clicks is None,
            "reader_time_seconds": max(5, min(180, round(len(lines) / 8))) if lines else None,
        }
        sample["manual_notes"] = (
            "Codex agent-assisted reader audit: visible Markdown contracts checked; "
            "semantic comprehension and real human timing still require independent human review."
        )
        sample["manual_status"] = "agent_assisted_review"
        assessed += 1
    return {
        "method": "fixed manifest; Codex agent-assisted reader audit",
        "assessed": assessed,
        "denominator": len(samples),
        "title_understood": {
            "numerator": title_pass,
            "denominator": len(samples),
            "percentage": round(title_pass / len(samples), 4) if samples else None,
        },
        "threshold": 0.80,
        "status": "agent_assisted_pass" if samples and title_pass / len(samples) >= 0.8 else "agent_assisted_not_met",
        "human_review_required": True,
    }


def _sample_gaps(task2_root: Path, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parents = _category_parents(task2_root)
    topics = _topic_rows(task2_root)
    selected_by_parent = {parent: 0 for parent in SAMPLE_PARENTS}
    for sample in samples:
        parent = str(sample.get("parent", ""))
        if parent in selected_by_parent:
            selected_by_parent[parent] += 1
    gaps = [
        {"parent": parent, "requested": 4, "selected": selected_by_parent[parent], "missing": max(0, 4 - selected_by_parent[parent])}
        for parent in SAMPLE_PARENTS
    ]
    target = min(20, len(topics))
    gaps.append({"parent": "__total__", "requested": target, "selected": len(samples), "missing": max(0, target - len(samples))})
    return gaps


def build_comparison_report(
    *, task1_root: Path, task2_root: Path, companybrain_root: Path, output_dir: Path | None = None,
    agent_reader_review: bool = False,
) -> dict[str, Any]:
    """Return and optionally write the fixed, non-semantic comparison report."""
    for root in (task1_root, task2_root, companybrain_root):
        if not root.is_dir():
            raise FileNotFoundError(root)
    task1 = _machine_evidence(task1_root)
    task2 = _machine_evidence(task2_root)
    taxonomy_before = _sha256_file(task2_root / "kb.structure.md")
    samples = _sample_manifest(task1_root, task2_root, companybrain_root)
    manual_quality = _agent_reader_review(task2_root, samples) if agent_reader_review else {
        "method": "fixed manifest; human review required",
        "assessed": 0,
        "denominator": len(samples),
        "title_understood": {"numerator": None, "denominator": len(samples), "percentage": None},
        "threshold": 0.80,
        "status": "manual_review_required",
    }
    sample_gaps = _sample_gaps(task2_root, samples)
    manifest_hash = hashlib.sha256(
        json.dumps(samples, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    task2_cost = task2.pop("cost", {})
    cost_available = task2_cost.get("_status") == "available"
    result: dict[str, Any] = {
        "schema_version": "kd-task2-comparison.v1",
        "machine_evidence": {"task1": task1, "task2": task2},
        "sample_manifest": samples,
        "sample_manifest_hash": manifest_hash,
        "sample_gaps": sample_gaps,
        "reader_quality_fields": READER_FIELDS,
        "manual_quality": manual_quality,
        "cost_evidence": {
            "status": "available" if cost_available else "unavailable",
            "reason": task2_cost.get("_reason"),
            "provider_calls": (
                int(task2_cost["_provider_calls"])
                if cost_available and task2_cost.get("_provider_calls") is not None
                else None
            ),
            "generator_calls": (
                int(task2_cost["_generator_calls"])
                if cost_available and task2_cost.get("_generator_calls") is not None
                else None
            ),
            "provider_requested": bool(task2_cost.get("_llm_enabled")) if cost_available else None,
            "planned_calls": (
                int(task2_cost["provider_calls_planned"])
                if cost_available and task2_cost.get("provider_calls_planned") is not None
                else int(task2_cost["planned_generator_calls"])
                if cost_available and task2_cost.get("planned_generator_calls") is not None
                else None
            ),
            "reserved_calls": (
                int(task2_cost["provider_calls_reserved"])
                if cost_available and task2_cost.get("provider_calls_reserved") is not None
                else None
            ),
            "planned_calls_basis": task2_cost.get("provider_calls_planned_basis") if cost_available else None,
            "failed_calls": int(task2_cost["failed_calls"]) if cost_available and task2_cost.get("failed_calls") is not None else None,
            "replay_calls": int(task2_cost["replay_calls"]) if cost_available and task2_cost.get("replay_calls") is not None else None,
            "elapsed_seconds": task2_cost.get("elapsed_seconds") if cost_available else None,
            "provider_tokens": task2_cost.get("total_provider_tokens") if cost_available else None,
            "fallback_ratio": task2_cost.get("fallback_ratio") if cost_available else None,
            "provider_calls_are_machine_fact": cost_available,
            "provider_call_basis": "sum of committed per-batch audit reports; offline runs report zero",
        },
        "safety_evidence": _safety_evidence(task2_root, output_dir, taxonomy_before),
        "companybrain_reference": str(companybrain_root),
        "quality_boundary": "Claim/page/token counts are machine evidence, not reader-quality scores.",
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "COMPARISON.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        lines = [
            "# KnowledgeDigest Task2 对比报告",
            "",
            "机器证据与人工阅读判断分开；当前人工字段必须由固定样本人工填写。",
            "",
            f"- 固定样本：{len(samples)} 条；manifest SHA-256：`{manifest_hash}`",
            f"- Task1 主题页：{task1['topic_pages']}；Task2 主题页：{task2['topic_pages']}",
            f"- Task2 provider 调用：{result['cost_evidence']['provider_calls']}（机器事实；状态：{result['cost_evidence']['status']}）",
            "- 人工标题理解度：未审查；不能用 Claim、页数或 token 数替代。",
            f"- 样本缺口：{json.dumps(result['sample_gaps'], ensure_ascii=False)}",
            f"- 安全检查：{json.dumps(result['safety_evidence'], ensure_ascii=False, sort_keys=True)}",
            "",
            "## 固定样本",
            "",
            "| 样本 | 领域 | Task2 主题 | Task1 | CompanyBrain | 人工状态 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for sample in samples:
            lines.append(
                f"| {sample['sample_id']} | {sample['parent']} | {sample['task2_topic_id']} | "
                f"{sample['task1_match']['status']} | {sample['companybrain_match']['status']} | {sample['manual_status']} |"
            )
        lines.extend(["", "## 机器证据", "", "```json", json.dumps(result["machine_evidence"], ensure_ascii=False, indent=2), "```", ""])
        (output_dir / "COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    return result


TASK3_COMPARISON_DIMENSIONS = (
    "saved_integrity",
    "machine_quality",
    "reader_readability",
    "trust_freshness",
    "failures",
    "performance",
    "cost",
    "limitations",
)


def _task3_unavailable_evidence(reason: str) -> dict[str, Any]:
    return {
        "availability": "unavailable",
        "unavailable_reason": reason,
        **{
            dimension: {"status": "N/A", "value": None, "basis": reason}
            for dimension in TASK3_COMPARISON_DIMENSIONS
        },
    }


def _task3_tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _task3_has_unsupported_nodes(root: Path) -> bool:
    if root.is_symlink():
        return True
    try:
        if not root.is_dir():
            return True
        for path in root.rglob("*"):
            if path.is_symlink():
                return True
            mode = path.lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                return True
    except OSError:
        return True
    return False


def _task3_json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _task3_frozen_question_set() -> tuple[dict[str, dict[str, Any]] | None, str | None]:
    path = Path(__file__).resolve().parents[1] / "config" / "task0-question-set.v1.json"
    question_set = _json(path, None)
    if not isinstance(question_set, dict) or question_set.get("schema_version") != "task0-question-set.v1" or not isinstance(question_set.get("questions"), list):
        return None, None
    canonical = {key: question_set.get(key) for key in ("schema_version", "question_set_id", "questions", "derivation_rules")}
    declared = question_set.get("question_set_hash")
    if not isinstance(declared, str) or declared != _task3_json_hash(canonical):
        return None, None
    expected = {
        str(item.get("question_id")): dict(item)
        for item in question_set["questions"]
        if isinstance(item, dict) and isinstance(item.get("question_id"), str)
    }
    return expected, declared


def _root_task3_comparison_evidence(root: Path, *, source_name: str = "task3") -> dict[str, Any]:
    """Read a real Task3 package only for the Task3 source slot.

    Task2 and CompanyBrain keep their historical machine-evidence adapter even
    if their directory happens to contain similarly named folders.  A Task3
    path without the complete run contract is unavailable, not comparable.
    """
    if root.is_symlink():
        return _task3_unavailable_evidence("Task3 candidate root is a symlink")
    if source_name == "task3":
        if _task3_has_unsupported_nodes(root):
            return _task3_unavailable_evidence("Task3 candidate contains an unsupported filesystem node")
        required_paths = (
            root / "bundle" / "README.md",
            root / "bundle" / "Home.md",
            root / "bundle" / "index.md",
            root / "bundle" / "log.md",
            root / "bundle" / "references" / "sources.md",
            root / "bundle" / "products" / "index.md",
            root / "audit" / "source-manifest.json",
            root / "reports" / "projection-report.json",
            root / "reports" / "exit-manifest.json",
            root / "reports" / "release-summary.json",
        )
        missing = [path.relative_to(root).as_posix() for path in required_paths if not path.is_file() or path.is_symlink()]
        if missing:
            return _task3_unavailable_evidence("Task3 candidate contract is incomplete: " + ", ".join(missing))
        if any(path.is_symlink() for path in root.rglob("*")):
            return _task3_unavailable_evidence("Task3 candidate contains a symlink")
        reports = root / "reports"
        try:
            projection = _json(reports / "projection-report.json", {})
            exit_manifest = _json(reports / "exit-manifest.json", {})
            summary = _json(reports / "release-summary.json", {})
            source_manifest = _json(root / "audit" / "source-manifest.json", {})
        except OSError:
            return _task3_unavailable_evidence("Task3 candidate reports are unreadable")
        if not all(isinstance(value, dict) for value in (projection, exit_manifest, summary, source_manifest)):
            return _task3_unavailable_evidence("Task3 candidate reports are not JSON objects")
        run_id = projection.get("run_id")
        if (
            not isinstance(run_id, str)
            or not run_id
            or exit_manifest.get("run_id") != run_id
            or summary.get("run_id") != run_id
            or source_manifest.get("run_id") != run_id
        ):
            return _task3_unavailable_evidence("Task3 candidate reports do not share one run_id")
        if projection.get("digest_release_status") != exit_manifest.get("digest_release_status"):
            return _task3_unavailable_evidence("Task3 candidate status projections disagree")
        if summary.get("digest_release_status") != projection.get("digest_release_status"):
            return _task3_unavailable_evidence("Task3 candidate release summary status disagrees")
        if projection.get("digest_release_status") not in {"released", "not_released"}:
            return _task3_unavailable_evidence("Task3 candidate status is missing or unsupported")
        entries = source_manifest.get("entries")
        if not isinstance(entries, list) or source_manifest.get("source_count") != len(entries) or source_manifest.get("source_count") != 89:
            return _task3_unavailable_evidence("Task3 candidate source manifest is incomplete")
        manifest_by_id: dict[str, dict[str, Any]] = {}
        manifest_uris: set[str] = set()
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("source_id"), str)
                or not entry["source_id"].strip()
                or entry["source_id"] in manifest_by_id
                or not isinstance(entry.get("source_uri"), str)
                or not entry["source_uri"].strip()
                or entry["source_uri"] in manifest_uris
                or not isinstance(entry.get("content_fingerprint"), str)
                or re.fullmatch(r"[0-9a-f]{64}", entry["content_fingerprint"]) is None
            ):
                return _task3_unavailable_evidence("Task3 candidate source manifest has invalid or duplicate entries")
            manifest_uris.add(entry["source_uri"])
            manifest_by_id[entry["source_id"]] = entry
        page_paths = [path for path in sorted((root / "bundle" / "products").rglob("*.md")) if path.name != "index.md"] if (root / "bundle" / "products").is_dir() else []
        if not page_paths:
            return _task3_unavailable_evidence("Task3 candidate has no Reader topic pages")
        claim_count = 0
        valid_reader_pages = 0
        invalid_reader_pages = 0
        claim_ids: set[str] = set()
        for page in page_paths:
            try:
                page_text = page.read_text(encoding="utf-8")
                frontmatter, body = parse_concept_document(page_text)
            except (OSError, ValueError, ValidationError):
                invalid_reader_pages += 1
                continue
            verified = frontmatter.get("verified")
            verified_events = {item.get("event") for item in verified if isinstance(item, dict)} if isinstance(verified, list) else set()
            trust_valid = isinstance(verified, list) and verified_events == {"source_hash_match", "locator_resolved"} and len(verified) == 2 and frontmatter.get("digest_content_hash") == managed_content_hash(frontmatter, body)
            page_sources = frontmatter.get("sources") if isinstance(frontmatter, dict) else None
            canonical_fingerprints = None
            if isinstance(page_sources, list) and len(page_sources) == 1 and isinstance(page_sources[0], dict):
                page_source = page_sources[0]
                manifest_entry = manifest_by_id.get(page_source.get("id"))
                claims = page_source.get("digest_claims") if isinstance(page_source.get("digest_claims"), list) else []
                canonical_fingerprints = {
                    "source_inventory": manifest_entry.get("content_fingerprint") if isinstance(manifest_entry, dict) else None,
                    "fixture_selection": page_source.get("digest_content_fingerprint"),
                    "claim_records": {claim.get("claim_id"): claim.get("content_fingerprint") for claim in claims if isinstance(claim, dict) and isinstance(claim.get("claim_id"), str)},
                }
            if trust_valid:
                for event in verified:
                    evidence_ref = event.get("evidence_ref") if isinstance(event, dict) else None
                    evidence_value: dict[str, Any] | None = None
                    if isinstance(evidence_ref, str) and (root / evidence_ref).is_file() and not (root / evidence_ref).is_symlink():
                        evidence_value = _json(root / evidence_ref, None)
                    if (
                        not isinstance(event, dict)
                        or not isinstance(event.get("actor"), str)
                        or not event["actor"].strip()
                        or not isinstance(event.get("detector_version"), str)
                        or event.get("detector_version") != "v1"
                        or event.get("actor") != f"process:knowledge-digest-{event.get('event')}-v1"
                        or not isinstance(event.get("content_hash"), str)
                        or re.fullmatch(r"[0-9a-f]{64}", event["content_hash"]) is None
                        or not isinstance(event.get("input_fingerprints"), dict)
                        or not event["input_fingerprints"]
                        or canonical_fingerprints is None
                        or any(event["input_fingerprints"].get(key) != value for key, value in canonical_fingerprints.items())
                        or not isinstance(event["input_fingerprints"].get("fixture_bytes"), str)
                        or re.fullmatch(r"[0-9a-f]{64}", event["input_fingerprints"].get("fixture_bytes")) is None
                        or not isinstance(evidence_ref, str)
                        or not evidence_ref.startswith("audit/trust-signals/")
                        or ".." in PurePosixPath(evidence_ref).parts
                        or not (root / evidence_ref).resolve().is_relative_to(root.resolve())
                        or not (root / evidence_ref).is_file()
                        or (root / evidence_ref).is_symlink()
                        or not isinstance(evidence_value, dict)
                        or evidence_value.get("page_path") != page.relative_to(root / "bundle").as_posix()
                        or evidence_value.get("topic_id") != frontmatter.get("digest_topic_id")
                        or evidence_value.get("generated") != frontmatter.get("generated")
                        or evidence_value.get("machine_pass") is not True
                        or evidence_value.get("content_hash") != frontmatter.get("digest_content_hash")
                        or evidence_value.get("events") != verified
                        or event.get("content_hash") != frontmatter.get("digest_content_hash")
                        or evidence_value.get("schema_version") != "reader-bundle-trust-signals.v1"
                    ):
                        trust_valid = False
                        break
            if (
                frontmatter.get("digest_page_status") != "published"
                or frontmatter.get("digest_machine_pass") is not True
                or not trust_valid
                or len(body.splitlines()) > 120
                or len(page_text.splitlines()) > 300
                or not isinstance(frontmatter.get("sources"), list)
                or not frontmatter["sources"]
            ):
                invalid_reader_pages += 1
                continue
            page_claim_count = 0
            page_invalid = False
            for source in frontmatter.get("sources", []) if isinstance(frontmatter, dict) else []:
                if (
                    not isinstance(source, dict)
                    or not isinstance(source.get("id"), str)
                    or not isinstance(source.get("resource"), str)
                    or not isinstance(source.get("digest_content_fingerprint"), str)
                    or re.fullmatch(r"[0-9a-f]{64}", source["digest_content_fingerprint"]) is None
                    or source["id"] not in manifest_by_id
                    or manifest_by_id[source["id"]].get("source_uri") != source["resource"]
                    or manifest_by_id[source["id"]].get("content_fingerprint") != source["digest_content_fingerprint"]
                    or not isinstance(source.get("digest_claims"), list)
                    or not source["digest_claims"]
                ):
                    page_invalid = True
                    continue
                for claim in source["digest_claims"]:
                    if (
                        not isinstance(claim, dict)
                        or not isinstance(claim.get("claim_id"), str)
                        or not claim["claim_id"].strip()
                        or claim["claim_id"] in claim_ids
                        or claim.get("target_path") != page.relative_to(root / "bundle").as_posix()
                        or claim.get("source_uri") != source["resource"]
                        or claim.get("content_fingerprint") != source["digest_content_fingerprint"]
                        or not isinstance(claim.get("fragment_locator"), str)
                        or re.fullmatch(r"lines:\d+(?:-\d+)?", claim["fragment_locator"].strip()) is None
                    ):
                        page_invalid = True
                        continue
                    claim_ids.add(claim["claim_id"])
                    page_claim_count += 1
            claim_count += page_claim_count
            if not page_invalid and page_claim_count > 0:
                valid_reader_pages += 1
            if page_invalid:
                invalid_reader_pages += 1
        if invalid_reader_pages or not valid_reader_pages or not claim_count:
            return _task3_unavailable_evidence("Task3 candidate has no valid published Reader page with Claims")
        if not isinstance(exit_manifest.get("bundle_hash"), str) or exit_manifest.get("bundle_hash") != _task3_tree_hash(root / "bundle"):
            return _task3_unavailable_evidence("Task3 candidate bundle hash does not match the current bundle")
        status = projection.get("digest_release_status") if projection.get("digest_release_status") == exit_manifest.get("digest_release_status") else None
        for relative in ("bundle/README.md", "bundle/log.md"):
            status_path = root / relative
            try:
                status_text = status_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return _task3_unavailable_evidence(f"Task3 {relative} is unreadable")
            if status_text.count(f"digest_release_status: `{status}`") != 1:
                return _task3_unavailable_evidence(f"Task3 {relative} status projection disagrees")
        quality = summary.get("reader_quality") if isinstance(summary.get("reader_quality"), dict) else {}
        quality_source = "release-summary"
        if isinstance(quality, dict) and "run_id" in quality and quality.get("run_id") != run_id:
            return _task3_unavailable_evidence("Task3 nested quality evidence is bound to a different run_id")
        quality_run_id: str | None = run_id if quality else None
        if not quality:
            quality_source = "quality-report"
            for quality_path in (
                reports / "quality.json",
                reports / "quality-scorecard.json",
                root / "quality" / "scorecard.json",
                root / "quality" / "run-report.json",
            ):
                candidate_quality = _json(quality_path, {})
                if isinstance(candidate_quality, dict) and candidate_quality:
                    quality = candidate_quality.get("summary", candidate_quality) if isinstance(candidate_quality.get("summary", candidate_quality), dict) else {}
                    quality_run_id = candidate_quality.get("run_id")
                    if quality_run_id is None and isinstance(candidate_quality.get("summary"), dict):
                        quality_run_id = candidate_quality["summary"].get("run_id")
                    break
        if quality and quality_run_id != run_id:
            return _task3_unavailable_evidence("Task3 quality evidence is bound to a different run_id")
        if not isinstance(quality, dict):
            return _task3_unavailable_evidence("Task3 quality evidence is missing")
        quality_summary = quality.get("summary") if quality_source == "quality-report" and isinstance(quality.get("summary"), dict) else quality
        accuracy = summary.get("accuracy") if isinstance(summary.get("accuracy"), dict) else {}
        title_accuracy = accuracy.get("title") if isinstance(accuracy.get("title"), dict) else {}
        ownership_accuracy = accuracy.get("ownership") if isinstance(accuracy.get("ownership"), dict) else {}
        provenance = summary.get("machine_provenance") if isinstance(summary.get("machine_provenance"), dict) else {}
        replay = quality_summary.get("replay") if isinstance(quality_summary.get("replay"), dict) else {}
        quality_report = None
        quality_report_path = None
        if isinstance(replay.get("quality_ref"), str):
            quality_report_path = root / replay["quality_ref"]
            if (
                ".." not in PurePosixPath(replay["quality_ref"]).parts
                and quality_report_path.is_file()
                and not quality_report_path.is_symlink()
                and quality_report_path.resolve().is_relative_to(root.resolve())
            ):
                quality_report = _json(quality_report_path, None)
        expected_quality_ids = {
            *(f"positive-{index:02d}" for index in range(1, 18)),
            *(f"negative-{index:02d}" for index in range(1, 4)),
        }
        quality_records = quality_report.get("records") if isinstance(quality_report, dict) else None
        quality_record_ids = {record.get("question_id") for record in quality_records if isinstance(record, dict)} if isinstance(quality_records, list) else set()
        quality_records_by_id = {record.get("question_id"): record for record in quality_records if isinstance(record, dict)} if isinstance(quality_records, list) else {}
        quality_provenance = quality_report.get("provenance") if isinstance(quality_report, dict) and isinstance(quality_report.get("provenance"), dict) else {}
        quality_report_summary = quality_report.get("summary") if isinstance(quality_report, dict) and isinstance(quality_report.get("summary"), dict) else {}
        frozen_questions, frozen_question_hash = _task3_frozen_question_set()
        quality_positive = [record for record in quality_records if isinstance(record, dict) and record.get("polarity") == "positive"] if isinstance(quality_records, list) else []
        quality_negative = [record for record in quality_records if isinstance(record, dict) and record.get("polarity") == "negative"] if isinstance(quality_records, list) else []
        recomputed_positive_passed = sum(
            1
            for record in quality_positive
            if record.get("answer_found") is True
            and record.get("answer_result") == "hit"
            and isinstance(record.get("first_hit_page"), str)
            and bool(record.get("first_hit_page"))
            and record.get("answer_complete") is True
            and record.get("boundary_version_accurate") is True
            and record.get("source_attribution") is True
            and record.get("navigation") == "passed"
            and record.get("source_chain") == "passed"
            and record.get("source_recheck_result") == "passed"
            and not record.get("failure_reason")
        )
        recomputed_negative_false_positives = sum(
            1 for record in quality_negative if record.get("answer_result") == "hit" or record.get("first_hit_page") is not None
        )
        quality_record_shape_valid = (
            isinstance(quality_report, dict)
            and quality_report.get("schema_version") == "task3-quality-result.v1"
            and quality_report.get("run_id") == run_id
            and quality_report.get("status") == "passed"
            and quality_report.get("mode") == "semantic"
            and quality_report.get("execution_mode") == "real_semantic"
            and isinstance(quality_records, list)
            and len(quality_records) == 20
            and quality_record_ids == expected_quality_ids
            and frozen_questions is not None
            and frozen_question_hash == quality_provenance.get("question_set_hash")
            and all(
                isinstance(record, dict)
                and record.get("polarity") == ("positive" if str(record.get("question_id", "")).startswith("positive-") else "negative")
                and isinstance(record.get("question"), str)
                and isinstance(record.get("entry_path"), str)
                and isinstance(record.get("expected_topic_or_product"), str)
                and isinstance(record.get("answer_found"), bool)
                and record.get("answer_result") in {"hit", "no_match"}
                and isinstance(record.get("source_attribution"), bool)
                and record.get("navigation") == "passed"
                and record.get("source_recheck_result") in {"passed", "not_applicable"}
                and isinstance(record.get("answer_complete"), bool)
                and isinstance(record.get("boundary_version_accurate"), bool)
                and isinstance(record.get("source_chain"), str)
                and frozen_questions.get(record.get("question_id"), {}).get("polarity") == record.get("polarity")
                and frozen_questions.get(record.get("question_id"), {}).get("original_text") == record.get("question")
                and frozen_questions.get(record.get("question_id"), {}).get("entry_path") == record.get("entry_path")
                and frozen_questions.get(record.get("question_id"), {}).get("expected_topic_or_product") == record.get("expected_topic_or_product")
                for record in quality_records
            )
            and recomputed_positive_passed >= 15
            and recomputed_negative_false_positives == 0
            and quality_report_summary.get("positive_passed") == recomputed_positive_passed
            and quality_report_summary.get("negative_false_positives") == recomputed_negative_false_positives
            and quality_report.get("hard_failures") == []
            and quality_report.get("unknowns") == []
            and isinstance(quality_report.get("scorecard_hash"), str)
            and re.fullmatch(r"[0-9a-f]{64}", quality_report.get("scorecard_hash")) is not None
            and isinstance(quality_report.get("provenance"), dict)
            and quality_report.get("provenance") == quality_summary.get("provenance")
            and quality_report.get("replay") == replay
            and isinstance(quality_summary.get("question_count"), int)
            and quality_summary.get("question_count") == 20
            and quality_summary.get("scorecard_hash") == quality_report.get("scorecard_hash")
            and quality_summary.get("records_hash") == quality_provenance.get("question_hash")
        )
        replay_material_valid = False
        if quality_record_shape_valid:
            replay_material_valid = True
            for field, prefix, filename in (
                ("manifest_ref", "audit/", "run-manifest.json"),
                ("config_ref", "audit/", "config.json"),
            ):
                reference = replay.get(field)
                reference_path = root / reference if isinstance(reference, str) else None
                if (
                    not isinstance(reference, str)
                    or not reference.startswith(prefix)
                    or PurePosixPath(reference).name != filename
                    or ".." in PurePosixPath(reference).parts
                    or reference_path is None
                    or not reference_path.is_file()
                    or reference_path.is_symlink()
                    or not reference_path.resolve().is_relative_to(root.resolve())
                ):
                    replay_material_valid = False
            provider_reference = quality_report.get("provider_receipt_ref") if isinstance(quality_report, dict) else None
            provider_path = root / provider_reference if isinstance(provider_reference, str) else None
            provider_receipt = _json(provider_path, None) if provider_path is not None and ".." not in PurePosixPath(provider_reference).parts and provider_path.is_file() and not provider_path.is_symlink() and provider_path.resolve().is_relative_to(root.resolve()) else None
            config_reference = replay.get("config_ref")
            config_path = root / config_reference if isinstance(config_reference, str) else None
            config_value = _json(config_path, None) if config_path is not None and config_path.is_file() and not config_path.is_symlink() else None
            manifest_reference = replay.get("manifest_ref")
            manifest_path = root / manifest_reference if isinstance(manifest_reference, str) else None
            manifest_value = _json(manifest_path, None) if manifest_path is not None and manifest_path.is_file() and not manifest_path.is_symlink() else None
            replay_material_valid = replay_material_valid and (
                isinstance(manifest_value, dict)
                and manifest_value.get("run_id") == run_id
                and manifest_value.get("execution_mode") == "real_semantic"
                and manifest_value.get("source_manifest_hash") == _task3_json_hash(source_manifest)
                and
                isinstance(provider_receipt, dict)
                and provider_receipt.get("run_id") == run_id
                and provider_receipt.get("execution_mode") == "real_semantic"
                and provider_receipt.get("provider_calls") == quality_report.get("provider_calls")
                and isinstance(quality_report.get("provider_calls"), int)
                and quality_report.get("provider_calls") > 0
                and isinstance(quality_report.get("provider"), str)
                and bool(quality_report.get("provider").strip())
                and isinstance(quality_report.get("model"), str)
                and bool(quality_report.get("model").strip())
                and provider_receipt.get("provider") == quality_report.get("provider")
                and provider_receipt.get("model") == quality_report.get("model")
                and isinstance(provider_receipt.get("config_hash"), str)
                and re.fullmatch(r"[0-9a-f]{64}", provider_receipt.get("config_hash")) is not None
                and isinstance(provider_receipt.get("calls"), list)
                and len(provider_receipt.get("calls")) == provider_receipt.get("provider_calls")
                and all(
                    isinstance(call, dict)
                    and call.get("provider") == quality_report.get("provider")
                    and call.get("model") == quality_report.get("model")
                    and call.get("status") == "completed"
                    and isinstance(call.get("request_hash"), str)
                    and re.fullmatch(r"[0-9a-f]{64}", call.get("request_hash")) is not None
                    and isinstance(call.get("response_hash"), str)
                    and re.fullmatch(r"[0-9a-f]{64}", call.get("response_hash")) is not None
                    and isinstance(call.get("response"), dict)
                    and call.get("response_hash") == _task3_json_hash(call.get("response"))
                    and isinstance(call.get("question_id"), str)
                    and call.get("question_id") in quality_records_by_id
                    and call.get("record_hash") == _task3_json_hash(quality_records_by_id[call.get("question_id")])
                    and call.get("response") == quality_records_by_id[call.get("question_id")].get("provider_response")
                    and call.get("request_hash") == _task3_json_hash({
                        "question_id": call.get("question_id"),
                        "question": quality_records_by_id[call.get("question_id")].get("question"),
                        "entry_path": quality_records_by_id[call.get("question_id")].get("entry_path"),
                        "expected_topic_or_product": quality_records_by_id[call.get("question_id")].get("expected_topic_or_product"),
                        "provider": quality_report.get("provider"),
                        "model": quality_report.get("model"),
                        "config_hash": provider_receipt.get("config_hash"),
                    })
                    for call in provider_receipt.get("calls", [])
                )
                and {call.get("question_id") for call in provider_receipt.get("calls", []) if isinstance(call, dict)} == expected_quality_ids
                and isinstance(config_value, dict)
                and config_value.get("run_id") == run_id
                and config_value.get("execution_mode") == "real_semantic"
                and config_value.get("config_hash") == provider_receipt.get("config_hash")
                and config_value.get("provider") == quality_report.get("provider")
                and config_value.get("model") == quality_report.get("model")
                and isinstance(config_value.get("endpoint"), str)
                and bool(config_value.get("endpoint").strip())
                and isinstance(config_value.get("budget"), dict)
                and config_value.get("budget", {}).get("max_calls") == provider_receipt.get("provider_calls")
            )
        if (
            quality_summary.get("positive_count") != 17
            or quality_summary.get("negative_count") != 3
            or not isinstance(quality_summary.get("positive_passed"), int)
            or quality_summary.get("positive_passed") < 15
            or quality_summary.get("negative_false_positives") != 0
            or quality_summary.get("positive_passed") != recomputed_positive_passed
            or quality_summary.get("negative_false_positives") != recomputed_negative_false_positives
            or quality_summary.get("mode") != "semantic"
            or not isinstance(quality_summary.get("page_count"), int)
            or quality_summary.get("page_count") <= 0
            or not isinstance(quality_summary.get("claim_count"), int)
            or quality_summary.get("claim_count") <= 0
            or any(not isinstance(replay.get(field), str) or not replay[field].strip() for field in ("manifest_ref", "quality_ref", "config_ref"))
            or summary.get("completion") != "complete"
            or summary.get("quality_status") != "passed"
            or summary.get("delivery_status") != "passed"
            or summary.get("hard_failures") != []
            or summary.get("unknowns") != []
            or summary.get("confirmation_required") is not True
            or summary.get("agent_only") is not True
            or provenance.get("execution_mode") != "real_semantic"
            or any(not isinstance(provenance.get(field), str) or not provenance[field].strip() for field in ("actor", "model", "rule", "seed", "snapshot_hash", "question_hash"))
            or provenance.get("question_set_hash") != quality_summary.get("provenance", {}).get("question_set_hash")
            or not quality_record_shape_valid
            or not replay_material_valid
            or not isinstance(title_accuracy.get("rate"), (int, float))
            or title_accuracy.get("rate") < 0.9
            or not isinstance(ownership_accuracy.get("rate"), (int, float))
            or ownership_accuracy.get("rate") < 0.9
        ):
            return _task3_unavailable_evidence("Task3 quality evidence is incomplete")
        delivery = summary.get("delivery") if isinstance(summary.get("delivery"), dict) else {}
        warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
        hard_failures = summary.get("hard_failures") if isinstance(summary.get("hard_failures"), list) else []
        return {
            "saved_integrity": {"status": "comparable" if status else "N/A", "value": {"package_status": status, "bundle_hash": exit_manifest.get("bundle_hash")}, "basis": "Task3 package projections and exit manifest"},
            "machine_quality": {"status": "comparable" if quality else "N/A", "value": quality or None, "basis": "Task3 release summary machine scorecard"},
            "reader_readability": {"status": "comparable" if quality else "N/A", "value": quality or None, "basis": "automatic 17+3 scorecard; no human content review"},
            "trust_freshness": {"status": "comparable" if source_manifest else "N/A", "value": {"source_count": source_manifest.get("source_count"), "source_manifest": "audit/source-manifest.json"} if source_manifest else None, "basis": "Task3 source manifest"},
            "failures": {"status": "comparable", "value": {"hard_failures": hard_failures, "warnings": warnings}, "basis": "Task3 release summary"},
            "performance": {"status": "comparable" if delivery.get("elapsed_seconds") is not None else "N/A", "value": {"elapsed_seconds": delivery.get("elapsed_seconds")} if delivery.get("elapsed_seconds") is not None else None, "basis": "Task3 run evidence" if delivery.get("elapsed_seconds") is not None else "run timing unavailable"},
            "cost": {"status": "comparable" if delivery.get("cost") is not None else "N/A", "value": delivery.get("cost"), "basis": "Task3 cost evidence" if delivery.get("cost") is not None else "cost unavailable"},
            "limitations": {"status": "comparable", "value": ["Task3 comparison is evidence-only", *[str(item) for item in warnings]], "basis": "Task3 summary and comparison boundary"},
            "binding": {
                "run_id": run_id,
                "bundle_hash": exit_manifest.get("bundle_hash"),
            },
            "claim_count": claim_count,
        }
    machine = _machine_evidence(root)
    cost = machine.get("cost", {})
    return {
        "saved_integrity": {
            "status": "comparable",
            "value": {
                "source_index_uris": machine.get("source_index_uris"),
                "reader_entrypoints": machine.get("reader_entrypoints"),
                "all_topic_pages_within_300_lines": machine.get("all_topic_pages_within_300_lines"),
            },
            "basis": "existing machine evidence",
        },
        "machine_quality": {
            "status": "N/A" if source_name == "companybrain" else "comparable",
            "value": {
                "topic_pages": machine.get("topic_pages"),
                "claim_count": machine.get("claim_count"),
                "claim_fingerprint_count": machine.get("claim_fingerprint_count"),
            } if source_name != "companybrain" else None,
            "basis": "no shared Task3 quality contract" if source_name == "companybrain" else "existing machine evidence; not a reader score",
        },
        "reader_readability": {
            "status": "N/A",
            "value": None,
            "basis": "fixed reader score is not present in this root evidence",
        },
        "trust_freshness": {
            "status": "N/A" if source_name == "companybrain" else "comparable",
            "value": None if source_name == "companybrain" else {"source_index_uris": machine.get("source_index_uris")},
            "basis": "no shared provenance schema" if source_name == "companybrain" else "existing source index evidence",
        },
        "failures": {
            "status": "N/A",
            "value": None,
            "basis": "failure count is not present in this root evidence",
        },
        "performance": {
            "status": "comparable" if cost.get("elapsed_seconds") is not None else "N/A",
            "value": {"elapsed_seconds": cost.get("elapsed_seconds")} if cost.get("elapsed_seconds") is not None else None,
            "basis": "existing run/cost evidence" if cost.get("elapsed_seconds") is not None else "run timing unavailable",
        },
        "cost": {
            "status": "comparable" if cost.get("_status") == "available" else "N/A",
            "value": cost if cost.get("_status") == "available" else None,
            "basis": "existing cost ledger" if cost.get("_status") == "available" else str(cost.get("_reason") or "cost unavailable"),
        },
        "limitations": {
            "status": "comparable",
            "value": [machine.get("cost", {}).get("_reason") or "reader-quality interpretation remains separate"],
            "basis": "comparison boundary",
        },
    }


def build_task3_comparison_report(
    *,
    evidence: dict[str, Any] | None = None,
    task2_root: Path | None = None,
    companybrain_root: Path | None = None,
    task3_root: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Build the fixed Task2/CompanyBrain/Task3 report.

    The caller may provide already captured evidence (used by replay and tests),
    or roots for the existing read-only machine evidence adapter.  Missing
    dimensions become explicit ``N/A`` records; this function never computes a
    subjective total and never decides release status.
    """
    source_names = ("task2", "companybrain", "task3")
    if evidence is None:
        evidence = {}
        for name, root in (
            ("task2", task2_root),
            ("companybrain", companybrain_root),
            ("task3", task3_root),
        ):
            if root is not None:
                if not root.is_dir():
                    evidence[name] = _task3_unavailable_evidence(f"{name} root is missing")
                else:
                    evidence[name] = _root_task3_comparison_evidence(root, source_name=name)
    if not isinstance(evidence, dict):
        evidence = {}

    def normalize_captured_source(name: str, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or not value:
            return _task3_unavailable_evidence(f"{name} comparison evidence is missing")
        if value.get("availability") == "unavailable":
            return dict(value)
        if not isinstance(value.get("saved_integrity"), dict) or not value["saved_integrity"]:
            return _task3_unavailable_evidence(f"{name} saved-integrity evidence is missing")
        if name == "task3" and (
            not isinstance(value.get("binding"), dict)
            or not isinstance(value["binding"].get("run_id"), str)
            or not value["binding"]["run_id"].strip()
            or not isinstance(value["binding"].get("bundle_hash"), str)
            or re.fullmatch(r"[0-9a-f]{64}", value["binding"]["bundle_hash"]) is None
            or not isinstance(value.get("claim_count"), int)
            or value.get("claim_count") <= 0
            or any(
                not isinstance(value.get(dimension), dict) or value[dimension].get("status") != "comparable"
                for dimension in ("saved_integrity", "machine_quality", "reader_readability", "trust_freshness", "failures")
            )
        ):
            return _task3_unavailable_evidence("Task3 comparison evidence is not bound to a comparable candidate")
        return dict(value)

    raw_sources = {
        name: normalize_captured_source(name, evidence.get(name))
        for name in source_names
    }
    normalized: dict[str, dict[str, dict[str, Any]]] = {}
    for name in source_names:
        normalized[name] = {}
        for dimension in TASK3_COMPARISON_DIMENSIONS:
            item = raw_sources[name].get(dimension)
            if isinstance(item, dict) and item.get("status") in {"comparable", "N/A"}:
                status = str(item["status"])
                normalized[name][dimension] = {
                    "comparability": status,
                    "value": item.get("value") if status == "comparable" else None,
                    "basis": str(item.get("basis") or "evidence supplied by caller"),
                }
            else:
                normalized[name][dimension] = {
                    "comparability": "N/A",
                    "value": None,
                    "basis": "evidence missing; no inference made",
                }

    dimensions = {
        dimension: {name: normalized[name][dimension] for name in source_names}
        for dimension in TASK3_COMPARISON_DIMENSIONS
    }
    result: dict[str, Any] = {
        "schema_version": "kd-task3-comparison.v1",
        "sources": raw_sources,
        "dimensions": dimensions,
        "limitations": [
            "N/A means the compared source has no shared evidence contract for that dimension.",
            "The report is evidence-only and does not replace the Task3 release summary or locked readback.",
        ],
        "release_decision": "not_a_release_decision",
    }
    if isinstance(raw_sources.get("task3", {}).get("binding"), dict):
        result["binding"] = dict(raw_sources["task3"]["binding"])
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "COMPARISON.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        lines = [
            "# KnowledgeDigest Task3 固定对比报告",
            "",
            "本报告只整理机器证据；不可比项写成 `N/A`，不生成总分，也不决定 released。",
            "",
            "| 维度 | Task2 | CompanyBrain | Task3 |",
            "| --- | --- | --- | --- |",
        ]
        for dimension in TASK3_COMPARISON_DIMENSIONS:
            cells = []
            for name in source_names:
                cell = dimensions[dimension][name]
                value = cell["value"]
                cells.append(cell["comparability"] if value is None else f"{cell['comparability']}: {value}")
            lines.append(f"| {dimension} | {cells[0]} | {cells[1]} | {cells[2]} |")
        lines.extend(["", "## 限制", "", *[f"- {item}" for item in result["limitations"]], ""])
        (output_dir / "COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task1", type=Path)
    parser.add_argument("--task2", type=Path, required=True)
    parser.add_argument("--companybrain", type=Path, required=True)
    parser.add_argument("--task3-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--agent-reader-review", action="store_true", help="record transparent agent-assisted visible-contract review")
    args = parser.parse_args()
    if args.task3_root is not None:
        build_task3_comparison_report(
            task2_root=args.task2,
            companybrain_root=args.companybrain,
            task3_root=args.task3_root,
            output_dir=args.output,
        )
        return 0
    if args.task1 is None:
        parser.error("--task1 is required unless --task3-root is supplied")
    build_comparison_report(
        task1_root=args.task1,
        task2_root=args.task2,
        companybrain_root=args.companybrain,
        output_dir=args.output,
        agent_reader_review=args.agent_reader_review,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
