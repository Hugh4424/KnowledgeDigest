"""Stage 2: cluster raw items by complete-linkage similarity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import DigestSettings
from .identity import source_id, topic_id
from .jsonl import write_jsonl
from .paths import DigestPaths
from .queues import write_queues
from .text_similarity import JaccardScorer, SimilarityScorer, _tokens


def _resolve_queue_root(roots: tuple[str, ...]) -> str:
    return roots[2] if len(roots) >= 3 else "_queues"


def cluster(
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
    settings: DigestSettings,
    *,
    persist_queues: bool = True,
    scorer: SimilarityScorer | None = None,
) -> list[dict[str, Any]]:
    """Group raw items into complete-linkage clusters and assign tiers."""
    active_scorer = scorer or JaccardScorer()
    pending = sorted(raw_items, key=lambda item: (str(item.get("source_id", "")), str(item["raw_id"])))
    clusters: list[dict[str, Any]] = []
    while pending:
        seed = pending.pop(0)
        members = [seed]
        for candidate in list(pending):
            similarities = [active_scorer.score(candidate["text"], member["text"]) for member in members]
            if similarities and min(similarities) >= settings.medium:
                members.append(candidate)
                pending.remove(candidate)
        pair_scores = [active_scorer.score(a["text"], b["text"]) for index, a in enumerate(members) for b in members[index + 1 :]]
        min_pair = min(pair_scores) if pair_scores else 1.0
        token_count = len(_tokens("\n".join(member["text"] for member in members)))
        if token_count < 3:
            tier, reason = "insufficient_signal", "fewer than three distinct content tokens"
        elif min_pair >= settings.high:
            tier, reason = "auto", f"complete-linkage minimum {min_pair:.2f} meets auto threshold"
        elif min_pair >= settings.medium:
            tier, reason = "needs_review", f"complete-linkage minimum {min_pair:.2f} needs review"
        else:
            tier, reason = "insufficient_signal", f"complete-linkage minimum {min_pair:.2f} below review threshold"
        member_source_ids = [
            str(member.get("source_id") or source_id(str(member["source_uri"])))
            for member in members
        ]
        clusters.append(
            {
                "cluster_id": f"cluster-{len(clusters) + 1}",
                "topic_id": topic_id(member_source_ids),
                "tier": tier,
                "cluster_tier": tier,
                "members": [member["raw_id"] for member in members],
                "min_pair_similarity": min_pair,
                "decision_reason": reason,
                "source_uris": [member["source_uri"] for member in members],
                "source_ids": sorted(member_source_ids),
            }
        )
    write_jsonl(run_dir / "s2" / "clusters.jsonl", clusters)
    if persist_queues:
        queue_root = _resolve_queue_root(roots)
        write_queues(
            paths.kb_dir,
            queue_root,
            [item for item in clusters if item["tier"] == "needs_review"],
            [item for item in clusters if item["tier"] == "insufficient_signal"],
        )
    return clusters
