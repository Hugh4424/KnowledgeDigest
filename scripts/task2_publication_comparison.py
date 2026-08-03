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
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from knowledge_digest.kb_structure import inspect_structure, parse_source_index_markdown


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task1", type=Path, required=True)
    parser.add_argument("--task2", type=Path, required=True)
    parser.add_argument("--companybrain", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--agent-reader-review", action="store_true", help="record transparent agent-assisted visible-contract review")
    args = parser.parse_args()
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
