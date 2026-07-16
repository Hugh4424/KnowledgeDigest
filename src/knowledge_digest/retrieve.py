"""Stage 3: retrieve candidate KB pages and make evolution decisions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .config import DigestSettings
from .jsonl import write_jsonl
from .paths import DigestPaths


_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _similarity(left: str, right: str) -> float:
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _page_records(kb_dir: Path, page_root: str) -> list[tuple[Path, str]]:
    root = kb_dir / page_root
    if not root.exists():
        return []
    return [(path, path.read_text(encoding="utf-8")) for path in sorted(root.rglob("*.md")) if path.is_file()]


def retrieve(
    clusters: list[dict[str, Any]],
    raw_items: list[dict[str, Any]],
    run_dir: Path,
    paths: DigestPaths,
    roots: tuple[str, ...],
    settings: DigestSettings,
) -> list[dict[str, Any]]:
    """For each auto cluster, decide whether to merge, revise, or create a page."""
    by_id = {item["raw_id"]: item for item in raw_items}
    pages = _page_records(paths.kb_dir, roots[0])
    decisions: list[dict[str, Any]] = []
    for cluster in clusters:
        if cluster["tier"] != "auto":
            continue
        text = "\n".join(by_id[raw_id]["text"] for raw_id in cluster["members"])
        ranked = sorted(((path, _similarity(text, page_text)) for path, page_text in pages), key=lambda item: (-item[1], str(item[0])))[: settings.top_k]
        candidate_paths = [str(path.relative_to(paths.kb_dir)) for path, _ in ranked]
        candidate_scores = [round(score, 6) for _, score in ranked]
        selected = [(path, score) for path, score in ranked if score > 0]
        if len(selected) >= 2:
            action, reason = "merge_multiple", "multiple related pages retained from top-k retrieval"
        elif len(selected) == 1:
            action, reason = "revise", "one related page retained from top-k retrieval"
        else:
            action, reason = "new", "no related page in top-k retrieval"
        decisions.append(
            {
                "cluster_id": cluster["cluster_id"],
                "action": action,
                "target_paths": [str(path.relative_to(paths.kb_dir)) for path, _ in selected],
                "candidate_paths": candidate_paths,
                "candidate_scores": candidate_scores,
                "reason": reason,
            }
        )
    write_jsonl(run_dir / "s3" / "evolution-decisions.jsonl", decisions)
    return decisions
