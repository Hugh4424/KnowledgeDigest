"""Stage 3: retrieve candidate KB pages and make evolution decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import DigestSettings
from .identity import source_id, topic_id
from .jsonl import write_jsonl
from .kb_structure import inspect_structure
from .page_layout import declared_managed_topics
from .paths import DigestPaths
from .text_similarity import JaccardScorer, SimilarityScorer


def _page_records(paths: DigestPaths, page_root: str) -> list[tuple[Path, str]]:
    """Expose only declared, internally-consistent managed topic pages to S3."""
    # Legacy direct-call tests exercise S2/S3 in isolation without a structure
    # contract. The formal pipeline reaches this function only after validating
    # one, so this compatibility branch cannot widen formal publication scope.
    if not paths.structure_path.is_file():
        root = paths.kb_dir / page_root
        return [(path, path.read_text(encoding="utf-8")) for path in sorted(root.rglob("*.md")) if path.is_file()] if root.exists() else []
    structure = inspect_structure(paths.structure_path)
    if structure.publication is None:
        return []
    return [
        (record["path"], record["path"].read_text(encoding="utf-8"))
        for record in declared_managed_topics(paths, structure.publication)
    ]


def _stored_topic_id(page_text: str) -> str | None:
    """Read the small metadata marker written on canonical digest pages."""
    lines = page_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator and key.strip() == "digest_topic_id" and value.strip():
            return value.strip()
    return None


def retrieve(
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
    settings: DigestSettings,
    *,
    scorer: SimilarityScorer | None = None,
    preserve_cluster_identity: bool = False,
) -> list[dict[str, Any]]:
    """For each processable cluster, decide whether to merge, revise, or create a page.

    ``insufficient_signal`` is intentionally left to the queue.  ``needs_review``
    is processable, but its risk route is upgraded to high by the preflight rules.
    """
    active_scorer = scorer or JaccardScorer()
    by_id = {item["raw_id"]: item for item in raw_items}
    pages = _page_records(paths, roots[0])
    decisions: list[dict[str, Any]] = []
    for cluster in clusters:
        if cluster.get("tier", cluster.get("cluster_tier")) == "insufficient_signal":
            continue
        text = "\n".join(by_id[raw_id]["text"] for raw_id in cluster["members"])
        ranked = sorted(((path, active_scorer.score(text, page_text)) for path, page_text in pages), key=lambda item: (-item[1], str(item[0])))[: settings.top_k]
        scored = [(path, round(score, 6)) for path, score in ranked]
        candidate_paths = [str(path.relative_to(paths.kb_dir)) for path, _ in scored]
        candidate_scores = [score for _, score in scored]
        selected = [
            (path, score)
            for path, score in scored
            if score >= settings.page_match_threshold
        ]
        threshold_note = f"page_match_threshold={settings.page_match_threshold:.6f}"
        if len(selected) >= 2:
            action, reason = "merge_multiple", f"multiple top-k pages met {threshold_note}"
        elif len(selected) == 1:
            action, reason = "revise", f"one top-k page met {threshold_note}"
        else:
            action, reason = "new", f"no top-k page met {threshold_note}"
        selected_topic_ids = sorted(
            {
                stored
                for path, _score in selected
                if (stored := _stored_topic_id(path.read_text(encoding="utf-8")))
            }
        )
        cluster_source_ids = [
            str(by_id[raw_id].get("source_id") or source_id(str(by_id[raw_id]["source_uri"])))
            for raw_id in cluster["members"]
        ]
        decisions.append(
            {
                "cluster_id": cluster["cluster_id"],
                "action": action,
                "target_paths": [str(path.relative_to(paths.kb_dir)) for path, _ in selected],
                "candidate_paths": candidate_paths,
                "candidate_scores": candidate_scores,
                "reason": reason,
                "cluster_tier": cluster.get("cluster_tier", cluster.get("tier")),
                "source_count": len(cluster.get("members", [])),
                "target_page_count": len(selected),
                # A fixed full-run batch plan owns topic identity. Without
                # that contract, an existing page may retain its identity
                # when a source is being revised. Never let a similarity
                # candidate overwrite a precomputed cross-batch topic: doing
                # so can merge unrelated sources into the candidate page.
                "topic_id": (
                    cluster.get("topic_id", topic_id(cluster_source_ids))
                    if preserve_cluster_identity
                    else selected_topic_ids[0] if selected_topic_ids else cluster.get("topic_id", topic_id(cluster_source_ids))
                ),
                "candidate_topic_ids": selected_topic_ids,
                "routing_rule_version": settings.routing_rule_version,
            }
        )
    write_jsonl(run_dir / "s3" / "evolution-decisions.jsonl", decisions)
    return decisions
