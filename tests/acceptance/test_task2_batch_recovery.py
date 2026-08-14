"""Acceptance contracts for Task2 publication transactions and resumable batches."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest


def _paths(tmp_path: Path):
    from knowledge_digest.paths import DigestPaths

    new_dir = tmp_path / "new"
    items_dir = new_dir / "items"
    items_dir.mkdir(parents=True)
    return DigestPaths(new_dir, items_dir, tmp_path / "kb", tmp_path / "kb" / "kb.structure.md")


def _publication():
    from knowledge_digest import kb_structure

    publication, errors = kb_structure._publication_contract(
        kb_structure.default_publication_structure(), require_taxonomy=True
    )
    assert not errors and publication is not None
    return publication


def test_navigation_and_source_index_share_one_writeback_transaction(tmp_path: Path) -> None:
    """All reader records must be accepted by the same archive-before-write boundary."""
    from knowledge_digest.navigation import build_publication_navigation
    from knowledge_digest.writeback import writeback

    paths = _paths(tmp_path)
    paths.kb_dir.mkdir()
    publication = _publication()
    records = build_publication_navigation(
        [],
        paths,
        publication,
        topic_universe=set(),
        source_index={"schema_version": "1.0.0", "entries": []},
    )

    writes = writeback(
        records,
        tmp_path / "run",
        paths,
        ("pages", "_archive", "_queues"),
        publication=publication,
    )

    assert {row["status"] for row in writes} == {"success"}
    assert (paths.kb_dir / "README.md").is_file()
    assert (paths.kb_dir / publication.home_path).is_file()
    assert not (paths.kb_dir / publication.source_index_path).exists()


def test_batch_manifest_is_v3_with_resume_identity_and_budget_fields(tmp_path: Path) -> None:
    from knowledge_digest.batch_run import _manifest

    paths = _paths(tmp_path)
    (paths.items_dir / "one.md").write_text("one\n", encoding="utf-8")
    (paths.items_dir / "two.md").write_text("two\n", encoding="utf-8")
    (paths.new_dir / "sources.jsonl").write_text(
        "".join(
            json.dumps({"content_path": name, "source_uri": f"https://source.example/{name}"}) + "\n"
            for name in ("one.md", "two.md")
        ),
        encoding="utf-8",
    )

    state = _manifest(paths, 2)

    assert state["schema_version"] == 3
    assert all(
        {"attempt", "split_from", "planned_calls"}.issubset(batch)
        for batch in state["batches"]
    )


def test_batch_runtime_policy_missing_limit_blocks_before_state_creation(tmp_path: Path) -> None:
    from knowledge_digest.config import DigestSettings, RuntimePolicy
    from knowledge_digest.batch_run import run_batched

    paths = _paths(tmp_path)
    state_path = tmp_path / "invalid-runtime-state.json"
    settings = DigestSettings(
        runtime=RuntimePolicy(
            max_provider_calls=10,
            max_replay_calls=None,
            request_timeout_seconds=None,
            max_wall_seconds=None,
            concurrency=None,
            source="config:runtime",
        )
    )

    with pytest.raises(Exception, match="runtime policy max_replay_calls"):
        run_batched(paths, settings, batch_size=1, state_path=state_path, resume=False)

    report_path = state_path.with_name("invalid-runtime-state.json.failure-report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["execution"]["status"] == "blocked"
    assert report["plan"]["preflight"]["status"] == "blocked"
    assert report["cost"]["provider_calls_observed"] == 0
    assert not state_path.exists()


def test_resume_rejects_partial_persisted_runtime_policy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from knowledge_digest import batch_run
    from knowledge_digest.config import DigestSettings

    paths = _paths(tmp_path)
    state = {
        "budget": {
            "max_provider_calls": 180,
            "request_timeout_seconds": 180,
            "max_wall_seconds": 3600,
            "concurrency": 4,
        }
    }
    monkeypatch.setattr(batch_run, "_load_or_create_state", lambda *args, **kwargs: state)

    with pytest.raises(Exception, match="persisted runtime policy max_replay_calls"):
        batch_run.run_batched(
            paths,
            DigestSettings(),
            batch_size=1,
            state_path=tmp_path / "partial-runtime-state.json",
            dry_run=False,
            resume=True,
        )


def test_failed_multi_source_batch_is_split_and_resumed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    from knowledge_digest import batch_run
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.errors import ValidationError

    paths = _paths(tmp_path)
    state_path = tmp_path / "batch-state.json"
    state = {
        "schema_version": 3,
        "sources": [{"content_path": "one.md"}, {"content_path": "two.md"}],
        "batches": [
            {
                "batch_id": "batch-001",
                "source_paths": ["one.md", "two.md"],
                "status": "pending",
                "attempt": 0,
                "split_from": None,
                "planned_calls": 2,
                "report_path": None,
                "error": None,
            }
        ],
        "budget": {
            "max_wall_seconds": 3600,
            "started_monotonic": None,
            "provider_calls": 0,
            "max_provider_calls": 8,
            "run_status": "pending",
            "pause_reason": None,
        },
    }
    monkeypatch.setattr(batch_run, "_load_or_create_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(batch_run, "_fixed_plan", lambda *args, **kwargs: ([], {}))
    monkeypatch.setattr(batch_run, "_planned_generator_calls", lambda *args, **kwargs: (1, tmp_path / "preflight.json"))
    monkeypatch.setattr(
        batch_run,
        "inspect_structure",
        lambda *args, **kwargs: SimpleNamespace(publication=SimpleNamespace(categories=("products", "other"))),
        raising=False,
    )
    calls = {"count": 0}

    def fake_audit(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValidationError("s4", "batch-001", "provider output is malformed")
        report = tmp_path / f"report-{calls['count']}.json"
        report.write_text("{}\n", encoding="utf-8")
        return report, "ok"

    monkeypatch.setattr(batch_run, "audit_run", fake_audit)

    report, _summary = batch_run.run_batched(
        paths,
        DigestSettings(),
        batch_size=2,
        state_path=state_path,
        dry_run=False,
        resume=False,
    )

    assert report.is_file()
    assert state["batches"][0]["status"] == "failed"
    children = state["batches"][1:]
    assert [child["split_from"] for child in children] == ["batch-001", "batch-001"]
    assert [child["source_paths"] for child in children] == [["one.md"], ["two.md"]]
    assert all(child["status"] == "succeeded" for child in children)


def test_provider_budget_exhaustion_pauses_before_next_batch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    from knowledge_digest import batch_run
    from knowledge_digest.config import DigestSettings

    paths = _paths(tmp_path)
    state_path = tmp_path / "budget-state.json"
    state = {
        "schema_version": 3,
        "sources": [{"content_path": "one.md"}],
        "batches": [
            {
                "batch_id": "batch-001",
                "source_paths": ["one.md"],
                "status": "pending",
                "attempt": 0,
                "split_from": None,
                "planned_calls": 1,
                "report_path": None,
                "error": None,
            }
        ],
        "budget": {
            "max_wall_seconds": 3600,
            "started_monotonic": None,
            "provider_calls": 0,
            "max_provider_calls": 0,
            "run_status": "pending",
            "pause_reason": None,
        },
    }
    monkeypatch.setattr(batch_run, "_load_or_create_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(batch_run, "_fixed_plan", lambda *args, **kwargs: ([], {}))
    monkeypatch.setattr(batch_run, "_planned_generator_calls", lambda *args, **kwargs: (1, tmp_path / "preflight.json"))
    monkeypatch.setattr(
        batch_run,
        "inspect_structure",
        lambda *args, **kwargs: SimpleNamespace(publication=SimpleNamespace(categories=("products", "other"))),
        raising=False,
    )
    monkeypatch.setattr(batch_run, "audit_run", lambda *args, **kwargs: pytest.fail("budget must stop before audit_run"))

    with pytest.raises(Exception, match="provider call budget"):
        batch_run.run_batched(
            paths,
            DigestSettings(llm_enabled=True),
            batch_size=1,
            state_path=state_path,
            dry_run=False,
            resume=False,
        )
    assert state["budget"]["run_status"] == "paused"


def test_planned_generator_call_hard_stop_happens_before_provider(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from types import SimpleNamespace

    from knowledge_digest import batch_run
    from knowledge_digest.config import DigestSettings

    paths = _paths(tmp_path)
    state_path = tmp_path / "planned-state.json"
    state = {
        "schema_version": 3,
        "manifest_sha256": "manifest",
        "runtime_identity": {"llm_model": "qwen3.6"},
        "sources": [{"content_path": "one.md"}],
        "batches": [{
            "batch_id": "batch-001", "source_paths": ["one.md"], "status": "pending",
            "attempt": 0, "split_from": None, "planned_calls": 1, "report_path": None, "error": None,
        }],
        "budget": {
            "max_wall_seconds": 3600, "started_at": None, "started_monotonic": None,
            "provider_calls": 0, "max_provider_calls": 8, "run_status": "pending", "pause_reason": None,
        },
    }
    monkeypatch.setattr(batch_run, "_load_or_create_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(batch_run, "_fixed_plan", lambda *args, **kwargs: ([], {}))
    monkeypatch.setattr(batch_run, "_planned_generator_calls", lambda *args, **kwargs: (181, tmp_path / "preflight.json"))
    monkeypatch.setattr(
        batch_run,
        "inspect_structure",
        lambda *args, **kwargs: SimpleNamespace(publication=SimpleNamespace(categories=("products", "other"))),
        raising=False,
    )
    monkeypatch.setattr(batch_run, "audit_run", lambda *args, **kwargs: pytest.fail("provider must not run after planned-call hard stop"))

    with pytest.raises(Exception, match="planned provider calls exceed 8"):
        batch_run.run_batched(
            paths,
            DigestSettings(llm_enabled=True),
            batch_size=1,
            state_path=state_path,
            dry_run=False,
            resume=False,
        )
    assert state["budget"]["planned_generator_calls"] == 181
    assert state["budget"]["run_status"] == "paused"
    failure = json.loads(state_path.with_name("planned-state.json.failure-report.json").read_text(encoding="utf-8"))
    assert failure["budget"]["max_planned_generator_calls"] == 8


def test_resume_uses_persisted_wall_clock_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    from knowledge_digest import batch_run
    from knowledge_digest.config import DigestSettings, RuntimePolicy

    paths = _paths(tmp_path)
    state = {
        "schema_version": 3,
        "sources": [{"content_path": "one.md"}],
        "batches": [{
            "batch_id": "batch-001", "source_paths": ["one.md"], "status": "pending",
            "attempt": 1, "split_from": None, "planned_calls": 1, "report_path": None, "error": None,
        }],
        "budget": {
            "max_wall_seconds": 10,
            "max_replay_calls": 1,
            "request_timeout_seconds": 180,
            "concurrency": 4,
            "started_at": 1000.0,
            "started_monotonic": 1000.0,
            "provider_calls": 0,
            "max_provider_calls": 4,
            "run_status": "paused",
            "pause_reason": "previous interruption",
        },
    }
    monkeypatch.setattr(batch_run, "_load_or_create_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(batch_run, "_fixed_plan", lambda *args, **kwargs: ([], {}))
    monkeypatch.setattr(
        batch_run,
        "inspect_structure",
        lambda *args, **kwargs: SimpleNamespace(publication=SimpleNamespace(categories=("products", "other"))),
        raising=False,
    )
    monkeypatch.setattr(batch_run.time, "time", lambda: 1020.0)
    monkeypatch.setattr(batch_run.time, "monotonic", lambda: 5000.0)
    monkeypatch.setattr(batch_run, "audit_run", lambda *args, **kwargs: pytest.fail("expired wall-clock budget must stop before audit_run"))

    with pytest.raises(Exception, match="wall-clock budget"):
        batch_run.run_batched(
            paths,
            DigestSettings(
                runtime=RuntimePolicy(max_provider_calls=4, max_wall_seconds=10),
            ),
            batch_size=1,
            state_path=tmp_path / "wall-clock-state.json",
            dry_run=False,
            resume=True,
        )


def test_failed_provider_attempt_is_counted_before_resume(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    from knowledge_digest import batch_run
    from knowledge_digest.config import DigestSettings, RuntimePolicy
    from knowledge_digest.errors import ValidationError

    paths = _paths(tmp_path)
    state = {
        "schema_version": 3,
        "sources": [{"content_path": "one.md"}],
        "batches": [{
            "batch_id": "batch-001", "source_paths": ["one.md"], "status": "pending",
            "attempt": 0, "split_from": None, "planned_calls": 1, "report_path": None, "error": None,
        }],
        "budget": {
            "max_wall_seconds": 3600,
            "max_replay_calls": 1,
            "request_timeout_seconds": 180,
            "concurrency": 4,
            "started_at": None,
            "started_monotonic": None,
            "provider_calls": 0,
            "max_provider_calls": 1,
            "run_status": "pending",
            "pause_reason": None,
        },
    }
    monkeypatch.setattr(batch_run, "_load_or_create_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(batch_run, "_fixed_plan", lambda *args, **kwargs: ([], {}))
    monkeypatch.setattr(batch_run, "_planned_generator_calls", lambda *args, **kwargs: (1, tmp_path / "preflight.json"))
    monkeypatch.setattr(
        batch_run,
        "inspect_structure",
        lambda *args, **kwargs: SimpleNamespace(publication=SimpleNamespace(categories=("products", "other"))),
        raising=False,
    )

    def fail_audit(*args, **kwargs):
        raise ValidationError("s4", "batch-001", "provider output is malformed")

    monkeypatch.setattr(batch_run, "audit_run", fail_audit)
    with pytest.raises(ValidationError, match="malformed"):
        batch_run.run_batched(
            paths,
            DigestSettings(
                llm_enabled=True,
                runtime=RuntimePolicy(max_provider_calls=1),
            ),
            batch_size=1,
            state_path=tmp_path / "failed-call-state.json",
            dry_run=False,
            resume=False,
        )

    assert state["budget"]["provider_calls"] == 1
    with pytest.raises(ValidationError, match="provider call budget"):
        batch_run.run_batched(
            paths,
            DigestSettings(
                llm_enabled=True,
                runtime=RuntimePolicy(max_provider_calls=1),
            ),
            batch_size=1,
            state_path=tmp_path / "failed-call-state.json",
            dry_run=False,
            resume=True,
        )


def test_failed_provider_attempt_writes_durable_failure_cost_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from types import SimpleNamespace

    from knowledge_digest import batch_run
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.errors import ValidationError

    paths = _paths(tmp_path)
    state_path = tmp_path / "failure-state.json"
    state = {
        "schema_version": 3,
        "manifest_sha256": "manifest",
        "runtime_identity": {"llm_model": "qwen3.6"},
        "sources": [{"content_path": "one.md"}],
        "batches": [{
            "batch_id": "batch-001", "source_paths": ["one.md"], "status": "pending",
            "attempt": 0, "split_from": None, "planned_calls": 1, "report_path": None, "error": None,
        }],
        "budget": {
            "max_wall_seconds": 3600, "started_at": None, "started_monotonic": None,
            "provider_calls": 0, "max_provider_calls": 1, "run_status": "pending", "pause_reason": None,
        },
    }
    monkeypatch.setattr(batch_run, "_load_or_create_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(batch_run, "_fixed_plan", lambda *args, **kwargs: ([], {}))
    monkeypatch.setattr(batch_run, "_planned_generator_calls", lambda *args, **kwargs: (1, tmp_path / "preflight.json"))
    monkeypatch.setattr(
        batch_run,
        "inspect_structure",
        lambda *args, **kwargs: SimpleNamespace(publication=SimpleNamespace(categories=("products", "other"))),
        raising=False,
    )
    def fail_audit(audit_paths, *args, **kwargs):
        report_path = audit_paths.kb_dir / "_digest" / "runs" / "run-failed" / "report.json"
        report_path.parent.mkdir(parents=True)
        report_path.write_text(
            json.dumps({"official_write": {"allow_official_write": True, "status": "pending"}}) + "\n",
            encoding="utf-8",
        )
        raise ValidationError("llm", "batch-001", "provider output is not JSON")

    monkeypatch.setattr(batch_run, "audit_run", fail_audit)

    with pytest.raises(ValidationError, match="not JSON"):
        batch_run.run_batched(
            paths,
            DigestSettings(llm_enabled=True),
            batch_size=1,
            state_path=state_path,
            dry_run=False,
            resume=False,
        )

    report_path = state_path.with_name(f"{state_path.name}.failure-report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "batch-failure-report.v1"
    assert report["status"] == "failed"
    assert report["status_semantics"] == "historical_failure"
    assert report["final_status"] == "failed"
    assert report["budget"]["provider_calls_planned"] is None
    assert report["budget"]["provider_calls_reserved"] == 1
    assert report["budget"]["provider_calls_observed"] is None
    assert report["budget"]["failed_calls"] == 1
    assert report["budget"]["replay_calls"] == 0
    assert "provider output is not JSON" in report["batches"][0]["error"]
    run_report = json.loads(
        (paths.kb_dir / "_digest" / "runs" / "run-failed" / "report.json").read_text(encoding="utf-8")
    )
    assert run_report["official_write"]["status"] == "failed_provider"
    assert run_report["failure"]["stage"] == "llm"
    assert run_report["failure"]["review_status"] == "needs-review"
    assert run_report["replay"]["status"] == "pending"
    assert run_report["fallback"]["used"] is False
    assert run_report["cost"]["provider_calls_planned"] is None
    assert run_report["cost"]["provider_calls_reserved"] == 1
    assert run_report["cost"]["provider_calls_observed"] is None
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["budget"]["failure_report_path"] == report_path.as_posix()
    assert persisted["batches"][0]["report_path"].endswith("run-failed/report.json")


def test_source_index_keeps_duplicate_alias_from_snapshot_manifest(tmp_path: Path) -> None:
    """A duplicate source is still a declared source and inherits the canonical link."""
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.kb_structure import parse_source_index_markdown
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.pipeline import audit_run

    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    content = "# Dashboard\n\nThe dashboard supports merchant operations.\n"
    (items / "canonical.md").write_text(content, encoding="utf-8")
    (items / "alias.md").write_text(content, encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        "".join(
            json.dumps({"content_path": name, "source_uri": uri}) + "\n"
            for name, uri in (("items/canonical.md", "confluence://canonical"), ("items/alias.md", "confluence://alias"))
        ),
        encoding="utf-8",
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    paths = validate_paths(new_dir, kb_dir, allow_new_kb=True)
    audit_run(paths, DigestSettings(), dry_run=False)
    source_index = parse_source_index_markdown((kb_dir / "indexes/sources.md").read_text(encoding="utf-8"))
    assert {row["source_uri"] for row in source_index["entries"]} == {"confluence://canonical", "confluence://alias"}


def test_batched_source_index_keeps_prior_sources(tmp_path: Path) -> None:
    """Each committed batch must extend, not replace, the reader source index."""
    from knowledge_digest.batch_run import run_batched
    from knowledge_digest.config import DigestSettings, SimilaritySettings
    from knowledge_digest.kb_structure import initialize_default_publication, parse_source_index_markdown
    from knowledge_digest.paths import validate_paths

    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    rows = []
    for name in ("one.md", "two.md", "three.md"):
        (items / name).write_text(f"# {name}\n\nEvidence for {name}.\n", encoding="utf-8")
        rows.append({"content_path": f"items/{name}", "source_uri": f"confluence://{name}"})
    (new_dir / "sources.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    initialize_default_publication(kb_dir)
    paths = validate_paths(new_dir, kb_dir)
    run_batched(
        paths,
        DigestSettings(
            llm_enabled=False,
            llm_summary_enabled=False,
            similarity=SimilaritySettings(backend="jaccard"),
        ),
        batch_size=1,
        state_path=tmp_path / "batch-state.json",
    )

    source_index = parse_source_index_markdown(
        (kb_dir / "indexes/sources.md").read_text(encoding="utf-8")
    )
    assert {row["source_uri"] for row in source_index["entries"]} == {
        "confluence://one.md",
        "confluence://two.md",
        "confluence://three.md",
    }


def test_topic_index_records_published_topic_identity(tmp_path: Path) -> None:
    from knowledge_digest.config import DigestSettings
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.pipeline import audit_run

    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    (items / "topic.md").write_text("# Payment API\n\nThe payment API supports v2.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "items/topic.md", "source_uri": "confluence://topic"}) + "\n",
        encoding="utf-8",
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    paths = validate_paths(new_dir, kb_dir, allow_new_kb=True)
    audit_run(paths, DigestSettings(), dry_run=False)
    value = json.loads((kb_dir / "_digest/topic-index.json").read_text(encoding="utf-8"))
    assert value["topics"]
    assert all(row["published_path"].startswith("pages/") for row in value["topics"])


def test_fixed_batch_plan_keeps_topic_identity_when_similarity_finds_old_page(tmp_path: Path) -> None:
    """A cross-batch candidate must not steal the planned topic identity."""
    from knowledge_digest.config import DigestSettings, SimilaritySettings
    from knowledge_digest.identity import source_id
    from knowledge_digest.kb_structure import initialize_default_publication
    from knowledge_digest.paths import validate_paths
    from knowledge_digest.retrieve import retrieve

    new_dir = tmp_path / "new"
    items = new_dir / "items"
    items.mkdir(parents=True)
    (items / "merchant.md").write_text("# Merchant processor\n\nSupports reseller operations.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "items/merchant.md", "source_uri": "confluence://merchant"}) + "\n",
        encoding="utf-8",
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    initialize_default_publication(kb_dir)
    old_page = kb_dir / "pages" / "customers" / "old.md"
    old_page.parent.mkdir(parents=True)
    old_page.write_text(
        "---\nmanaged_by: KnowledgeDigest\ndigest_kind: topic\ndigest_topic_id: topic-old\n"
        "digest_published_path: pages/customers/old.md\ndigest_part: 1\n---\n"
        "# Old topic\n\nMerchant processor content.\n",
        encoding="utf-8",
    )
    paths = validate_paths(new_dir, kb_dir)
    settings = DigestSettings(
        llm_enabled=False,
        llm_summary_enabled=False,
        page_match_threshold=0.01,
        similarity=SimilaritySettings(backend="jaccard"),
    )
    raw_item = {
        "raw_id": "raw-merchant",
        "source_uri": "confluence://merchant",
        "source_id": source_id("confluence://merchant"),
        "text": "# Merchant processor\n\nSupports reseller operations.\n",
    }
    decisions = retrieve(
        [{
            "cluster_id": "cluster-21",
            "topic_id": "topic-planned",
            "tier": "auto",
            "members": ["raw-merchant"],
        }],
        [raw_item],
        tmp_path / "run",
        paths,
        ("pages", "_archive", "_queues"),
        settings,
        preserve_cluster_identity=True,
    )
    assert decisions[0]["topic_id"] == "topic-planned"


def test_source_index_fails_closed_when_snapshot_manifest_is_missing(tmp_path: Path) -> None:
    from knowledge_digest.errors import ValidationError
    from knowledge_digest.pipeline import _source_index_for_navigation

    run_dir = tmp_path / "run"
    (run_dir / "s1").mkdir(parents=True)
    (run_dir / "s1" / "duplicates.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(ValidationError, match="snapshot manifest is missing or empty"):
        _source_index_for_navigation(
            drafts=[],
            raw_items=[{"source_uri": "confluence://declared", "content_fingerprint": "a" * 64}],
            run_dir=run_dir,
        )
