"""Queue file helpers for review and insufficient-signal clusters."""

from __future__ import annotations

import re
import hashlib
from pathlib import Path
from typing import Any


_QUEUE_LINE_RE = re.compile(r"^-\s*(?P<cluster_id>\S+):\s*(?P<reason>.+)$")


def _parse_existing_entries(path: Path) -> dict[str, str]:
    """Return existing cluster_id -> reason entries, preserving only the latest reason."""
    if not path.exists():
        return {}
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _QUEUE_LINE_RE.match(line)
        if match:
            entries[match.group("cluster_id")] = match.group("reason").strip()
    return entries


def write_queues(
    kb_dir: Path,
    queue_root: str,
    needs_review_clusters: list[dict[str, Any]],
    insufficient_signal_clusters: list[dict[str, Any]],
    *,
    append: bool = True,
    provider_sources: list[dict[str, Any]] | None = None,
) -> None:
    """Write or append cluster and provider-review queues.

    Provider failures are source-scoped rather than cluster-scoped.  They are
    kept in the same reader-visible queue with a stable synthetic key so a
    later batch cannot silently erase an earlier review item.
    """
    queue_dir = kb_dir / queue_root
    queue_dir.mkdir(parents=True, exist_ok=True)
    for name, clusters in (("needs_review.md", needs_review_clusters), ("insufficient_signal.md", insufficient_signal_clusters)):
        path = queue_dir / name
        existing: dict[str, str] = _parse_existing_entries(path) if append and path.exists() else {}
        for cluster in clusters:
            existing[cluster["cluster_id"]] = cluster["decision_reason"]
        if name == "needs_review.md" and provider_sources:
            for source in provider_sources:
                uri = str(source.get("source_uri", "")).strip()
                if not uri:
                    continue
                key = "provider-source-" + hashlib.sha256(uri.encode("utf-8")).hexdigest()[:12]
                reason = str(source.get("reason", "provider output requires review")).strip()
                targets = ", ".join(str(path) for path in source.get("target_paths", []) if path)
                if targets:
                    reason = f"{reason}; pages: {targets}"
                existing[key] = f"{uri} — {reason}"
        title = name.removesuffix(".md").replace("_", " ")
        lines = [f"# {title}", ""]
        lines.extend(f"- {cluster_id}: {reason}" for cluster_id, reason in existing.items())
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
