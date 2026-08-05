"""Task0 Phase 2 acceptance: write-before gates and business idempotency."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from knowledge_digest.errors import ValidationError
from knowledge_digest.provenance import validate_prewrite_provenance


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


def _jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    (items / "good.md").write_text(
        "# Good source\nA stable claim that can be published and traced.\n",
        encoding="utf-8",
    )
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "good.md", "source_uri": "https://source.example/good"}) + "\n",
        encoding="utf-8",
    )
    return new_dir


def test_same_snapshot_rerun_does_not_grow_archive_or_claim_history(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)

    first = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert first.returncode == 0, first.stderr
    archive_path = kb_dir / "_archive" / "records.jsonl"
    history_path = kb_dir / "_digest" / "claim-history.jsonl"
    first_counts = (len(_jsonl(archive_path)), len(_jsonl(history_path)))
    first_pages = {
        path.relative_to(kb_dir).as_posix(): path.read_bytes()
        for path in kb_dir.rglob("*.md")
        if "_digest" not in path.relative_to(kb_dir).parts
        and "_archive" not in path.relative_to(kb_dir).parts
    }

    second = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert second.returncode == 0, second.stderr

    assert (len(_jsonl(archive_path)), len(_jsonl(history_path))) == first_counts
    assert {
        path.relative_to(kb_dir).as_posix(): path.read_bytes()
        for path in kb_dir.rglob("*.md")
        if "_digest" not in path.relative_to(kb_dir).parts
        and "_archive" not in path.relative_to(kb_dir).parts
    } == first_pages


def test_prewrite_gate_rejects_audit_and_release_targets() -> None:
    source = {
        "content_path": "good.md",
        "source_uri": "https://source.example/good",
        "source_id": "src-good",
        "content_fingerprint": "f" * 64,
    }
    manifest = {"schema_version": "input-manifest.v1", "sources": [source]}
    snapshot = {
        **source,
        "input_path": "good.md",
        "snapshot_id": "snap-good",
        "validated_at": "2026-08-04T00:00:00Z",
        "validation_status": "passed",
    }
    ledger = [{**source, "validation_status": "passed"}]

    with pytest.raises(ValidationError, match="Reader Package"):
        validate_prewrite_provenance(
            manifest,
            [snapshot],
            ledger,
            [],
            [{"target_path": "_queues/provider.md", "digest_kind": "home"}],
        )

    with pytest.raises(ValidationError, match="Reader Package"):
        validate_prewrite_provenance(
            manifest,
            [snapshot],
            ledger,
            [],
            [{"target_path": "_digest/source-index.md", "digest_kind": "source-index"}],
        )

    with pytest.raises(ValidationError, match="cannot release"):
        validate_prewrite_provenance(
            manifest,
            [snapshot],
            ledger,
            [],
            [{"target_path": "Home.md", "digest_kind": "home", "delivery_status": "released"}],
        )

    with pytest.raises(ValidationError, match="degraded page"):
        validate_prewrite_provenance(
            manifest,
            [snapshot],
            ledger,
            [],
            [{"target_path": "pages/degraded.md", "page_status": "degraded"}],
        )

    validate_prewrite_provenance(
        manifest,
        [snapshot],
        ledger,
        [],
        [
            {"target_path": "pages/provider-guide.md", "digest_kind": "topic"},
            {"target_path": "indexes/reports.md", "digest_kind": "category"},
        ],
    )


@pytest.mark.parametrize("mismatch", ["snapshot", "ledger"])
def test_prewrite_gate_rejects_source_uri_mismatch(mismatch: str) -> None:
    source = {
        "content_path": "good.md",
        "source_uri": "https://source.example/good",
        "source_id": "src-good",
        "content_fingerprint": "f" * 64,
    }
    manifest = {"schema_version": "input-manifest.v1", "sources": [source]}
    snapshot = {
        **source,
        "input_path": "good.md",
        "snapshot_id": "snap-good",
        "validated_at": "2026-08-04T00:00:00Z",
        "validation_status": "passed",
    }
    ledger = [{**source, "validation_status": "passed"}]
    if mismatch == "snapshot":
        snapshot["source_uri"] = "https://source.example/wrong"
    else:
        ledger[0]["source_uri"] = "https://source.example/wrong"

    with pytest.raises(ValidationError, match="source URI differs"):
        validate_prewrite_provenance(
            manifest,
            [snapshot],
            ledger,
            [],
            [{"target_path": "pages/provider-guide.md", "digest_kind": "topic"}],
        )


@pytest.mark.parametrize("missing", ["text", "claim_fingerprint", "fragment_locator"])
def test_prewrite_gate_rejects_incomplete_claim_provenance(missing: str) -> None:
    source = {
        "content_path": "good.md",
        "source_uri": "https://source.example/good",
        "source_id": "src-good",
        "content_fingerprint": "f" * 64,
    }
    manifest = {"schema_version": "input-manifest.v1", "sources": [source]}
    snapshot = {
        **source,
        "input_path": "good.md",
        "snapshot_id": "snap-good",
        "validated_at": "2026-08-04T00:00:00Z",
        "validation_status": "passed",
    }
    ledger = [{**source, "validation_status": "passed"}]
    claim = {
        "text": "A verified claim.",
        "source_uri": source["source_uri"],
        "content_fingerprint": source["content_fingerprint"],
        "claim_fingerprint": "claim-good",
        "fragment_locator": "lines:1-1",
        "target_path": "pages/good.md",
    }
    claim.pop(missing)

    with pytest.raises(ValidationError, match="claim provenance is incomplete"):
        validate_prewrite_provenance(
            manifest,
            [snapshot],
            ledger,
            [claim],
            [{"target_path": "pages/good.md", "digest_kind": "topic"}],
        )


def test_prewrite_gate_rejects_claim_fingerprint_mismatch() -> None:
    source = {
        "content_path": "good.md",
        "source_uri": "https://source.example/good",
        "source_id": "src-good",
        "content_fingerprint": "f" * 64,
    }
    manifest = {"schema_version": "input-manifest.v1", "sources": [source]}
    snapshot = {
        **source,
        "input_path": "good.md",
        "snapshot_id": "snap-good",
        "validated_at": "2026-08-04T00:00:00Z",
        "validation_status": "passed",
    }
    ledger = [{**source, "validation_status": "passed"}]
    claim = {
        "text": "A claim with the wrong source fingerprint.",
        "source_uri": source["source_uri"],
        "content_fingerprint": "e" * 64,
        "claim_fingerprint": "claim-good",
        "fragment_locator": "lines:1-1",
        "target_path": "pages/good.md",
    }

    with pytest.raises(ValidationError, match="claim fingerprint does not match"):
        validate_prewrite_provenance(
            manifest,
            [snapshot],
            ledger,
            [claim],
            [{"target_path": "pages/good.md", "digest_kind": "topic"}],
        )


def test_degraded_source_isolated_from_other_validated_sources() -> None:
    good = {
        "content_path": "good.md",
        "source_uri": "https://source.example/good",
        "source_id": "src-good",
        "content_fingerprint": "a" * 64,
    }
    failed = {
        "content_path": "failed.md",
        "source_uri": "https://source.example/failed",
        "source_id": "src-failed",
        "content_fingerprint": "b" * 64,
    }
    snapshots = [
        {**good, "snapshot_id": "snap-good", "validated_at": "2026-08-04T00:00:00Z", "validation_status": "passed"},
        {**failed, "snapshot_id": "snap-failed", "validated_at": "2026-08-04T00:00:00Z", "validation_status": "failed"},
    ]
    ledger = [{**good, "validation_status": "passed"}, {**failed, "validation_status": "failed"}]
    claims = [
        {
            "text": "good claim",
            "source_uri": good["source_uri"],
            "content_fingerprint": good["content_fingerprint"],
            "claim_fingerprint": "claim-good",
            "fragment_locator": "lines:1-1",
            "target_path": "pages/good.md",
        }
    ]

    validate_prewrite_provenance(
        {"schema_version": "input-manifest.v1", "sources": [good, failed]},
        snapshots,
        ledger,
        claims,
        [{"target_path": "pages/good.md", "page_status": "published", "delivery_status": "not_released"}],
    )


def test_prewrite_failure_preserves_existing_reader_and_queue_bytes(tmp_path: Path) -> None:
    new_dir = _input(tmp_path)
    kb_dir = tmp_path / "kb"
    config = _offline_config(tmp_path)
    seed = _run_digest(str(new_dir), str(kb_dir), "--config", str(config), "--no-llm")
    assert seed.returncode == 0, seed.stderr
    home = kb_dir / "Home.md"
    queue = kb_dir / "_queues" / "insufficient_signal.md"
    before_home = home.read_bytes()
    before_queue = queue.read_bytes()
    audit_paths = [
        kb_dir / "_digest" / "source-manifest.json",
        kb_dir / "_digest" / "source-audit-ledger.jsonl",
        kb_dir / "_digest" / "source-snapshots.jsonl",
        kb_dir / "_digest" / "duplicates.jsonl",
    ]
    before_audit = {path: path.read_bytes() for path in audit_paths}

    from knowledge_digest.config import resolve_settings
    from knowledge_digest.paths import DigestPaths
    from knowledge_digest.pipeline import audit_run

    paths = DigestPaths(new_dir, new_dir / "items", kb_dir, kb_dir / "kb.structure.md")
    settings = resolve_settings(config, top_k=None, high=None, medium=None, max_lines=None)

    def reject(*_args: object, **_kwargs: object) -> None:
        raise ValidationError("prewrite", "test", "injected gate failure")

    with patch("knowledge_digest.pipeline.validate_prewrite_provenance", side_effect=reject):
        with pytest.raises(ValidationError, match="injected gate failure"):
            audit_run(paths, settings, dry_run=False)

    assert home.read_bytes() == before_home
    assert queue.read_bytes() == before_queue
    assert {path: path.read_bytes() for path in audit_paths} == before_audit
