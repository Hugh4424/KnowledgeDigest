"""Task0 Phase 1 acceptance: input manifest, snapshots and source relations."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_digest(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "knowledge_digest.cli", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _offline_config(tmp_path: Path) -> Path:
    path = tmp_path / "offline.json"
    path.write_text(
        json.dumps({"similarity": {"backend": "jaccard"}, "llm_enabled": False}),
        encoding="utf-8",
    )
    return path


def _input(tmp_path: Path) -> Path:
    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    (items / "good.md").write_text("A source with usable evidence.\n", encoding="utf-8")
    (items / "duplicate.md").write_text("A source with usable evidence.\n", encoding="utf-8")
    (items / "failed.md").write_text("home navigation menu\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {"content_path": "good.md", "source_uri": "https://source.example/good"},
                {"content_path": "duplicate.md", "source_uri": "https://source.example/duplicate"},
                {"content_path": "failed.md", "source_uri": "https://source.example/failed"},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return new_dir


def _jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_manifest_snapshot_and_ledger_close_over_success_duplicate_and_failure(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert result.returncode == 0, result.stderr
    manifest = json.loads((kb_dir / "_digest" / "source-manifest.json").read_text(encoding="utf-8"))
    snapshots = _jsonl(kb_dir / "_digest" / "source-snapshots.jsonl")
    ledger = _jsonl(kb_dir / "_digest" / "source-audit-ledger.jsonl")
    duplicates = _jsonl(kb_dir / "_digest" / "duplicates.jsonl")
    assert manifest["schema_version"] == "input-manifest.v1"
    assert {row["source_uri"] for row in manifest["sources"]} == {
        "https://source.example/good",
        "https://source.example/duplicate",
        "https://source.example/failed",
    }
    assert len(snapshots) == len(manifest["sources"])
    assert len(ledger) == len(manifest["sources"])
    assert {row["source_uri"] for row in ledger} == {row["source_uri"] for row in manifest["sources"]}
    assert {row["source_id"] for row in ledger} == {row["source_id"] for row in manifest["sources"]}
    assert {row["content_fingerprint"] for row in ledger} == {row["content_fingerprint"] for row in manifest["sources"]}
    assert all(row.get("validated_at", "").endswith("Z") for row in snapshots)
    assert len(duplicates) == 1
    assert duplicates[0]["source_uri"] in {
        "https://source.example/good",
        "https://source.example/duplicate",
    }
    assert all(row.get("source_id") for row in manifest["sources"])
    assert all(row.get("content_fingerprint") for row in manifest["sources"])


def test_missing_or_extra_source_declaration_fails_before_formal_write(tmp_path: Path) -> None:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    (new_dir / "items" / "note.md").write_text("usable evidence\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "other.md", "source_uri": "https://source.example/other"}) + "\n",
        encoding="utf-8",
    )
    kb_dir = tmp_path / "kb"

    result = _run_digest(str(new_dir), str(kb_dir), "--config", str(_offline_config(tmp_path)), "--no-llm")

    assert result.returncode == 1
    assert "manifest" in result.stderr.lower()
    assert not (kb_dir / "Home.md").exists()


def test_same_snapshot_does_not_duplicate_source_or_duplicate_relations(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)

    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert first.returncode == 0, first.stderr
    snapshot_path = kb_dir / "_digest" / "source-snapshots.jsonl"
    duplicate_path = kb_dir / "_digest" / "duplicates.jsonl"
    ledger_path = kb_dir / "_digest" / "source-audit-ledger.jsonl"
    first_counts = (len(_jsonl(snapshot_path)), len(_jsonl(duplicate_path)), len(_jsonl(ledger_path)))

    second = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")

    assert second.returncode == 0, second.stderr
    assert (len(_jsonl(snapshot_path)), len(_jsonl(duplicate_path)), len(_jsonl(ledger_path))) == first_counts
