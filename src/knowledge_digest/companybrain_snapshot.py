"""Read-only CompanyBrain snapshot for a real Task5 comparison run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(value: Any, *, newline: bool = False) -> bytes:
    data = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return data + (b"\n" if newline else b"")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_companybrain_snapshot(root: Path) -> dict[str, Any]:
    """Scan CompanyBrain without modifying it or copying its prose.

    The public bundle receives only hashes, paths and locators.  The actual
    baseline pages stay at the caller-supplied host path for the comparison
    evaluator.
    """

    root = Path(root).expanduser()
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError(f"CompanyBrain root is not a regular directory: {root}")
    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    if symlinks:
        raise ValueError(f"CompanyBrain contains symlink: {symlinks[0].relative_to(root)}")

    files = [
        path
        for path in sorted(
            root.rglob("*"),
            key=lambda item: item.relative_to(root).as_posix().encode("utf-8"),
        )
        if path.is_file()
        and not path.name.startswith(".")
        and path.suffix.casefold() in {".md", ".markdown"}
    ]
    entries = [
        {
            "relative_path": path.relative_to(root).as_posix(),
            "sha256": _sha(path.read_bytes()),
        }
        for path in files
    ]
    # The CompanyBrain tree and snapshot ID deliberately use the same
    # canonical file-list bytes as the KnowledgeDigest publication tree.
    # A second payload with scope/file-count metadata would make identical
    # files produce different identities and permit cross-run comparison drift.
    file_list_sha256 = _sha(_canonical(entries, newline=True))
    tree_sha256 = file_list_sha256
    markdown_files = [
        {
            "relative_path": entry["relative_path"],
            "raw_hash": entry["sha256"],
            "locator": {"relative_path": entry["relative_path"]},
        }
        for entry in entries
        if str(entry["relative_path"]).casefold().endswith((".md", ".markdown"))
    ]
    snapshot_id = f"cb-{file_list_sha256[:24]}"
    observation_payload = {
        "companybrain_snapshot_id": snapshot_id,
        "companybrain_tree_sha256": tree_sha256,
        "regular_markdown_files": markdown_files,
    }
    return {
        "schema_version": "knowledge-digest-companybrain-snapshot.v1",
        "companybrain_snapshot_id": snapshot_id,
        "companybrain_tree_sha256": tree_sha256,
        "observation_sha256": _sha(_canonical(observation_payload, newline=True)),
        "regular_markdown_files": markdown_files,
        "entry_files": [item["relative_path"] for item in markdown_files],
    }


__all__ = ["build_companybrain_snapshot"]
