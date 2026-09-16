"""Small, deterministic file fixtures for the Task9 K3 publish channel."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any

from knowledge_digest.kb_structure import default_publication_structure


DEFAULT_PAGES: dict[str, str] = {
    "products/Acme/overview.md": "# Acme overview\n\nThe fixture page is managed by KnowledgeDigest.\n",
    "products/Acme/settings.md": "# Acme settings\n\nThe fixture page contains stable settings evidence.\n",
}


def _write_bytes(root: Path, relative: str, value: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8") if isinstance(value, str) else value)


def make_batch_with_nav(
    root: Path,
    *,
    pages: Mapping[str, str | bytes] | None = None,
    extra_files: Mapping[str, str | bytes] | None = None,
    run_status: str = "complete",
    publish_status: str = "not_released",
    navigation_status: str = "generated_ok",
    blockers: Sequence[object] = (),
    attempt_id: str = "fixture-attempt",
    run_metrics: Mapping[str, object] | None = None,
) -> Path:
    """Write a K1/K2-shaped batch with controllable navigation and blockers."""
    batch = root / "batch"
    page_values = dict(DEFAULT_PAGES if pages is None else pages)
    page_rows: list[dict[str, Any]] = []
    for index, (relative, content) in enumerate(sorted(page_values.items()), start=1):
        _write_bytes(batch, relative, content)
        page_rows.append(
            {
                "topic_key": f"fixture:{Path(relative).stem}",
                "page_path": relative,
                "page_paths": [relative],
                "source_paths": [f"fixture/{relative}"],
                "block_count": 1,
                "claim_count": 1,
                "block_ids": [f"fixture-block-{index}"],
                "claim_ids": [f"fixture-claim-{index}"],
            }
        )
    for relative, content in (extra_files or {}).items():
        _write_bytes(batch, relative, content)

    audit = batch / "_audit"
    audit.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "task7-page-manifest.v1",
        "publish_status": publish_status,
        "run_status": run_status,
        "attempt_id": attempt_id,
        "navigation": {
            "navigation_status": navigation_status,
            "success_pages": len(page_rows) if navigation_status == "generated_ok" else 0,
            "blocked_sources": len(blockers),
            "blocked_reasons": [str(item) for item in blockers],
        },
        "blockers": list(blockers),
        "pages": page_rows,
    }
    (audit / "page-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (audit / "run-metrics.json").write_text(
        json.dumps(
            dict(
                run_metrics
                or {
                    "elapsed_ms": 7,
                    "provider_calls": 2,
                    "provider_tokens": 13,
                    "reasons": {},
                }
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (audit / "reference-blocks.jsonl").write_text("", encoding="utf-8")
    (audit / "sources.jsonl").write_text("", encoding="utf-8")
    (audit / "suspected-synonyms.md").write_text("# Fixture synonyms\n", encoding="utf-8")
    (batch / "README.md").write_text("# Task9 fixture batch\n", encoding="utf-8")
    return batch


def make_kb(
    root: Path,
    *,
    name: str = "knowledge-base",
    structure: bool = True,
    files: Mapping[str, str | bytes] | None = None,
) -> Path:
    """Create a target KB fixture, optionally with the default declaration."""
    kb = root / name
    kb.mkdir(parents=True, exist_ok=True)
    if structure:
        declaration = default_publication_structure()
        declaration = declaration.replace(
            "\n---\n",
            "\nmanaged_paths:\n  - products\n  - Home.md\n  - Index.md\n---\n",
            1,
        )
        (kb / "kb.structure.md").write_text(declaration, encoding="utf-8")
    for relative, content in (files or {}).items():
        _write_bytes(kb, relative, content)
    return kb


__all__ = ["DEFAULT_PAGES", "make_batch_with_nav", "make_kb"]
