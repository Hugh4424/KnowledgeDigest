"""Task7 P7: command switching, batch orchestration, and end-to-end facts."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest


try:
    from knowledge_digest.semantic_compiler import (
        BASELINE_REGRESSION_CAUSES,
        BASELINE_REGRESSION_NODES,
        configured_provider_from_env,
        compile_batch,
    )
except (ImportError, ModuleNotFoundError):
    BASELINE_REGRESSION_CAUSES = None
    BASELINE_REGRESSION_NODES = None
    configured_provider_from_env = None
    compile_batch = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "task7_e2e"
ITEMS_ROOT = FIXTURE_ROOT / "items"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"

EXPECTED_NODES = (
    "tests/acceptance/test_task0_runtime_audit.py::test_runtime_audit_records_frozen_calibration_hash",
    "tests/acceptance/test_task2a_reader_bundle.py::test_full_fixture_emits_positive_trust_signals_and_audit_evidence",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_fail_closed_after_content_or_event_mutation",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[source_fingerprint]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[locator]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[target_path]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_trust_signals_reject_provenance_and_page_mutations[page_type]",
    "tests/acceptance/test_task2a_reader_bundle.py::test_validator_reconciles_frontmatter_and_audit_without_input_context",
    "tests/acceptance/test_task2a_reader_bundle.py::test_entry_coverage_mismatch_fails_closed",
    "tests/acceptance/test_task2a_reader_bundle.py::test_entry_producer_missing_fails_closed",
    "tests/acceptance/test_task2a_reader_bundle.py::test_changed_fixture_provenance_fails_closed_before_publishing",
    "tests/acceptance/test_task2a_reader_bundle.py::test_malformed_fixture_selection_without_sample_id_is_structured",
    "tests/acceptance/test_task2a_reader_bundle.py::test_malformed_fixture_selection_without_selection_reason_is_structured",
    "tests/acceptance/test_task2a_reader_bundle.py::test_real_selected_fixtures_close_footnote_to_claim_and_replay",
    "tests/acceptance/test_task2a_reader_bundle.py::test_validator_rejects_bundle_symlinks_and_non_allowlisted_files",
    "tests/acceptance/test_task2a_reader_bundle.py::test_validator_rejects_incomplete_claim_provenance",
)


class FakeProvider:
    """Small provider seam used only by the in-process E2E tests."""

    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.calls = 0

    def complete(self) -> dict[str, str]:
        if not self.available:
            raise RuntimeError("provider unavailable")
        self.calls += 1
        return {
            "title": "Cached semantic page",
            "slug": "cached-semantic-page",
            "intro": "Login supports token authentication.",
            "provider_tokens": 12,
        }


class MixedIntroProvider(FakeProvider):
    def complete(self) -> dict[str, object]:
        self.calls += 1
        return {
            "title": "Mixed intro page",
            "slug": "mixed-intro-page",
            "intro": [
                "Login supports token authentication.",
                "This sentence is not in the source.",
            ],
            "provider_tokens": 12,
        }


class EmptyIntroProvider(FakeProvider):
    def complete(self) -> dict[str, object]:
        self.calls += 1
        return {
            "title": "Empty intro page",
            "slug": "empty-intro-page",
            "intro": [],
            "provider_tokens": 12,
        }


class MissingUsageProvider(FakeProvider):
    def complete(self) -> dict[str, object]:
        self.calls += 1
        return {
            "title": "Missing usage page",
            "slug": "missing-usage-page",
            "intro": ["Login supports token authentication."],
        }


@pytest.mark.parametrize(
    "payload",
    (
        {"title": 7, "slug": "invalid-title", "intro": [], "provider_tokens": 12},
        {"title": "Invalid slug", "slug": "../escape", "intro": [], "provider_tokens": 12},
        {"title": "Invalid intro", "slug": "invalid-intro", "intro": [7], "provider_tokens": 12},
        {"title": "Missing intro", "slug": "missing-intro", "provider_tokens": 12},
        {"title": "Multiline\ntitle", "slug": "multiline-title", "intro": [], "provider_tokens": 12},
    ),
)
def test_task7_e2e_invalid_semantic_provider_result_is_blocked_before_cache(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    class InvalidSemanticProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self) -> dict[str, object]:
            self.calls += 1
            return dict(payload)

    provider = InvalidSemanticProvider()
    result = _run(tmp_path, provider=provider)
    batch = Path(result.output_dir)
    manifest = _read_json(batch / "_audit" / "page-manifest.json")

    assert result.outcome == "blocked"
    assert provider.calls == 2
    assert _read_json(batch / "_audit" / "run-metrics.json")["provider_calls"] == 2
    assert any(
        row.get("reason") == "provider_invalid_result"
        for row in manifest["blockers"]
    )
    assert not (tmp_path / "cache" / "model-cache" / "entries.jsonl").exists()


def _require_api():
    assert compile_batch is not None, "semantic_compiler.compile_batch is not implemented"
    assert BASELINE_REGRESSION_NODES is not None, "Task7 regression baseline is not frozen"
    return compile_batch


def _source_bytes(relative: str) -> bytes:
    return (ITEMS_ROOT / relative).read_bytes()


def _manifest_payload() -> dict[str, Any]:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = []
    for entry in raw["entries"]:
        value = dict(entry)
        relative = str(value["source_uri"])
        payload = _source_bytes(relative)
        value["content_hash"] = hashlib.sha256(payload).hexdigest()
        value["byte_count"] = len(payload)
        entries.append(value)
    raw["entries"] = entries
    return raw


def _write_manifest(path: Path, *, mutate: str | None = None) -> Path:
    payload = _manifest_payload()
    if mutate == "hash":
        payload["entries"][0]["content_hash"] = "0" * 64
    if mutate == "missing":
        payload["entries"] = payload["entries"][:-1]
        payload["expected_count"] = 5
    if mutate == "missing-file":
        payload["entries"][0]["source_uri"] = "Payments/missing-file.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _run(tmp_path: Path, *, provider: object | None = None, mutate: str | None = None, **kwargs: Any):
    manifest = _write_manifest(tmp_path / "manifest.json", mutate=mutate)
    kwargs.setdefault("cache_root", tmp_path / "cache" / "model-cache")
    topic_map_path = kwargs.pop("topic_map_path", PROJECT_ROOT / "config" / "task7-topic-map.json")
    return _require_api()(
        ITEMS_ROOT.parent,
        manifest_path=manifest,
        output_parent=tmp_path / "batches",
        provider=provider,
        topic_map_path=topic_map_path,
        today="2026-09-14",
        **kwargs,
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_batch_files(batch: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in sorted(batch.joinpath("products").rglob("*")) if (batch / "products").exists() else ():
        if path.is_file():
            result[path.relative_to(batch).as_posix()] = path.read_bytes()
    for name in (
        "_audit/reference-blocks.jsonl",
        "_audit/sources.jsonl",
        "_audit/suspected-synonyms.md",
    ):
        result[name] = (batch / name).read_bytes()
    manifest = _read_json(batch / "_audit/page-manifest.json")
    manifest.pop("attempt_id", None)
    manifest.pop("run_status", None)
    result["_audit/page-manifest.json"] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    return result


def test_task7_e2e_success_writes_reader_pages_and_exact_five_audit_files(tmp_path: Path) -> None:
    provider = FakeProvider()
    result = _run(tmp_path, provider=provider)
    batch = Path(result.output_dir)

    assert result.outcome == "not_released"
    assert batch.name == "2026-09-14-1"
    assert (batch / "README.md").is_file()
    assert (batch / "products").is_dir()
    assert {path.name for path in (batch / "_audit").iterdir()} == {
        "reference-blocks.jsonl",
        "sources.jsonl",
        "page-manifest.json",
        "run-metrics.json",
        "suspected-synonyms.md",
    }
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert manifest["publish_status"] == "not_released"
    assert manifest["run_status"] == "complete"
    assert manifest["pages"]
    assert provider.calls == len(manifest["pages"])
    assert "2026-09-14-1" not in (batch / "README.md").read_text(encoding="utf-8")


def test_task7_e2e_reconciliation_failure_leaves_blocked_skeleton_and_zero_calls(tmp_path: Path) -> None:
    provider = FakeProvider()
    result = _run(tmp_path, provider=provider, mutate="hash")
    batch = Path(result.output_dir)

    assert result.outcome == "blocked"
    assert not (batch / "products").exists()
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert manifest["publish_status"] == "not_released"
    assert manifest["run_status"] == "blocked"
    assert manifest["pages"] == []
    assert manifest["blockers"]
    metrics = _read_json(batch / "_audit" / "run-metrics.json")
    assert metrics["provider_calls"] == 0
    assert metrics["actual_provider_calls"] == 0
    assert metrics["elapsed_ms"] >= 0
    assert metrics["reasons"]["elapsed_ms"] == "reconciliation_failed"
    assert metrics["reasons"]["provider_calls"] == "no_provider_call_yet"
    assert provider.calls == 0


def test_task7_e2e_blocked_manifest_keeps_missing_source_in_audit_ledger(tmp_path: Path) -> None:
    result = _run(tmp_path, provider=FakeProvider(), mutate="missing-file")
    batch = Path(result.output_dir)
    manifest = _read_json(batch / "_audit" / "page-manifest.json")

    missing = next(row for row in manifest["source_ledger"] if row["source_path"] == "Payments/missing-file.md")
    assert missing["source_status"] == "blocked"
    assert missing["pages"] == []
    assert any(
        row.get("source_path") == "Payments/missing-file.md"
        and row.get("reason") == "source_missing"
        for row in manifest["blockers"]
    )


def test_task7_e2e_topic_map_setup_failure_is_a_blocked_audited_batch(tmp_path: Path) -> None:
    topic_map = tmp_path / "malformed-topic-map.json"
    topic_map.write_text("{not-json", encoding="utf-8")

    result = _run(tmp_path, provider=FakeProvider(), topic_map_path=topic_map)
    batch = Path(result.output_dir)

    assert result.outcome == "blocked"
    assert not (batch / "products").exists()
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert manifest["run_status"] == "blocked"
    assert any(row.get("reason") == "preflight_failed" for row in manifest["blockers"])
    assert "Traceback" not in (batch / "README.md").read_text(encoding="utf-8")


def test_task7_e2e_cache_root_setup_failure_is_a_blocked_audited_batch(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache-root-file"
    cache_root.write_text("not-a-directory", encoding="utf-8")

    result = _run(tmp_path, provider=FakeProvider(), cache_root=cache_root)
    batch = Path(result.output_dir)

    assert result.outcome == "blocked"
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert manifest["run_status"] == "blocked"
    assert any(row.get("reason") == "preflight_failed" for row in manifest["blockers"])
    assert _read_json(batch / "_audit" / "run-metrics.json")["provider_calls"] == 0


def test_task7_e2e_cache_corruption_is_blocked_and_not_provider_unavailable(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache" / "model-cache"
    cache_root.mkdir(parents=True)
    (cache_root / "entries.jsonl").write_text("not-json\n", encoding="utf-8")

    result = _run(tmp_path, provider=FakeProvider(), cache_root=cache_root)
    batch = Path(result.output_dir)
    manifest = _read_json(batch / "_audit" / "page-manifest.json")

    assert result.outcome == "blocked"
    assert manifest["run_status"] == "blocked"
    assert any(row.get("reason") == "cache_integrity_failure" for row in manifest["blockers"])
    assert not any(row.get("reason") == "model_unavailable_no_cache" for row in manifest["blockers"])
    assert _read_json(batch / "_audit" / "run-metrics.json")["provider_calls"] == 0
    claims = [
        json.loads(line)
        for line in (batch / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    fallback_claims = [claim for claim in claims if claim.get("claim_kind") == "intro"]
    assert fallback_claims
    assert all(claim["status"] == "原文未明确" for claim in fallback_claims)
    assert any(
        evidence.get("reason") == "cache_integrity_failure"
        for claim in fallback_claims
        for evidence in claim.get("retrieval_evidence", [])
    )


def test_task7_e2e_cache_write_integrity_failure_renders_fallback_not_provider_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_root = tmp_path / "cache" / "model-cache"
    real_open = Path.open

    def fail_cache_append(path: Path, *args: object, **kwargs: object):
        mode = kwargs.get("mode", args[0] if args else "r")
        if path == cache_root / "entries.jsonl" and mode == "a":
            raise OSError("simulated cache persistence failure")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_cache_append)
    result = _run(tmp_path, provider=FakeProvider(), cache_root=cache_root)
    batch = Path(result.output_dir)
    assert result.outcome == "blocked"
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert any(row.get("reason") == "cache_integrity_failure" for row in manifest["blockers"])
    claims = [
        json.loads(line)
        for line in (batch / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    intro_claims = [claim for claim in claims if claim.get("claim_kind") == "intro"]
    assert intro_claims
    assert all(claim["status"] == "原文未明确" for claim in intro_claims)


def test_task7_e2e_provider_matrix_cache_hit_miss_and_unavailable_is_explicit(tmp_path: Path) -> None:
    first_provider = FakeProvider()
    first = _run(tmp_path / "miss", provider=first_provider)
    assert first_provider.calls > 0

    hit_provider = FakeProvider()
    hit = _run(tmp_path / "hit", provider=hit_provider, cache_root=tmp_path / "miss" / "cache" / "model-cache")
    assert hit_provider.calls == 0
    hit_metrics = _read_json(Path(hit.output_dir) / "_audit" / "run-metrics.json")
    assert hit_metrics["cache_hits"] == len(_read_json(Path(hit.output_dir) / "_audit" / "page-manifest.json")["pages"])

    unavailable = _run(tmp_path / "unavailable", provider=FakeProvider(available=False))
    unavailable_manifest = _read_json(Path(unavailable.output_dir) / "_audit" / "page-manifest.json")
    assert unavailable_manifest["run_status"] == "complete"
    assert any(row.get("reason") == "model_unavailable_no_cache" for row in unavailable_manifest["blockers"])
    unavailable_metrics = _read_json(Path(unavailable.output_dir) / "_audit" / "run-metrics.json")
    assert unavailable_metrics["provider_calls"] == len(unavailable_manifest["pages"])
    assert unavailable_metrics["actual_provider_calls"] == len(unavailable_manifest["pages"])
    assert all(row.get("provider_called") is True for row in unavailable_manifest["blockers"])
    assert "原文未明确" in "\n".join(
        path.read_text(encoding="utf-8")
        for path in (Path(unavailable.output_dir) / "products").rglob("*.md")
    )


def test_task7_e2e_mixed_intro_does_not_leave_unrendered_sourced_claims(tmp_path: Path) -> None:
    result = _run(tmp_path, provider=MixedIntroProvider())
    batch = Path(result.output_dir)
    claims = [
        json.loads(line)
        for line in (batch / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    intro_claims = [claim for claim in claims if claim["claim_kind"] == "intro"]
    assert intro_claims
    assert all(claim["status"] == "原文未明确" for claim in intro_claims)
    assert all(claim["text"] == "原文未明确" for claim in intro_claims)
    assert all(claim["span_start"] == 0 for claim in intro_claims)
    assert all(claim["span_end"] == len("原文未明确") for claim in intro_claims)
    page_text = "\n".join(path.read_text(encoding="utf-8") for path in (batch / "products").rglob("*.md"))
    assert "## 导读\n原文未明确" in page_text


def test_task7_e2e_empty_provider_intro_has_audited_fail_closed_claim(tmp_path: Path) -> None:
    result = _run(tmp_path, provider=EmptyIntroProvider())
    batch = Path(result.output_dir)
    claims = [
        json.loads(line)
        for line in (batch / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    intro_claims = [claim for claim in claims if claim["claim_kind"] == "intro"]

    assert intro_claims
    assert all(claim["status"] == "原文未明确" for claim in intro_claims)
    assert all(
        evidence.get("reason") == "empty_provider_intro"
        for claim in intro_claims
        for evidence in claim.get("retrieval_evidence", [])
    )
    page_text = "\n".join(path.read_text(encoding="utf-8") for path in (batch / "products").rglob("*.md"))
    assert "## 导读\n原文未明确" in page_text


def test_task7_e2e_missing_provider_usage_is_not_reported_as_cache_hit(tmp_path: Path) -> None:
    result = _run(tmp_path, provider=MissingUsageProvider())
    batch = Path(result.output_dir)
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    metrics = _read_json(batch / "_audit" / "run-metrics.json")

    assert result.outcome == "blocked"
    assert any(row.get("reason") == "provider_usage_unavailable" for row in manifest["blockers"])
    assert metrics["provider_calls"] == len(manifest["pages"])
    assert metrics["provider_tokens"] == 0
    assert metrics["reasons"]["provider_tokens"] == "provider_usage_unavailable"


def test_task7_e2e_same_input_has_stable_products_and_audit_projection(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache" / "model-cache"
    first = _run(tmp_path / "one", provider=FakeProvider(), cache_root=cache_root)
    second = _run(tmp_path / "two", provider=FakeProvider(), cache_root=cache_root)
    assert _stable_batch_files(Path(first.output_dir)) == _stable_batch_files(Path(second.output_dir))


def test_task7_e2e_claim_paths_follow_the_concrete_multipart_page(tmp_path: Path) -> None:
    root = tmp_path / "multipart"
    source_path = root / "items" / "Payments" / "large.md"
    source_path.parent.mkdir(parents=True)
    payload = ("# Large source\n\n" + "\n".join(f"Fact {index}." for index in range(220)) + "\n").encode()
    source_path.write_bytes(payload)
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "input_manifest_id": "task7-multipart-claims",
                "expected_count": 1,
                "entries": [
                    {
                        "source_uri": "Payments/large.md",
                        "source_id": "large",
                        "content_hash": hashlib.sha256(payload).hexdigest(),
                        "byte_count": len(payload),
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = compile_batch(
        root,
        manifest_path=manifest,
        output_parent=tmp_path / "batches",
        cache_root=tmp_path / "cache",
        provider=FakeProvider(),
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
    )
    batch = Path(result.output_dir)
    page_manifest = _read_json(batch / "_audit" / "page-manifest.json")
    page_paths = tuple(page_manifest["pages"][0]["page_paths"])
    assert len(page_paths) >= 2

    claims = [
        json.loads(line)
        for line in (batch / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sourced_claims = [claim for claim in claims if claim["status"] == "sourced"]
    assert sourced_claims
    assert any(claim["page_path"].endswith(".part-002.md") for claim in sourced_claims)
    for claim in sourced_claims:
        assert claim["page_path"] in page_paths
        assert claim["text"] in (batch / claim["page_path"]).read_text(encoding="utf-8")


def test_task7_e2e_repeated_blocks_keep_claim_and_block_anchors_across_parts(tmp_path: Path) -> None:
    root = tmp_path / "repeated-blocks"
    source_path = root / "items" / "Payments" / "repeated.md"
    source_path.parent.mkdir(parents=True)
    lines = ["# Repeated", "", "## Authentication", ""]
    for _ in range(190):
        lines.extend(("### Login", "Same fact.", ""))
    payload = "\n".join(lines).encode()
    source_path.write_bytes(payload)
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "input_manifest_id": "task7-repeated-blocks",
                "expected_count": 1,
                "entries": [
                    {
                        "source_uri": "Payments/repeated.md",
                        "source_id": "repeated",
                        "content_hash": hashlib.sha256(payload).hexdigest(),
                        "byte_count": len(payload),
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = compile_batch(
        root,
        manifest_path=manifest,
        output_parent=tmp_path / "batches",
        cache_root=tmp_path / "cache",
        provider=FakeProvider(),
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
    )
    batch = Path(result.output_dir)
    page_manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert len(page_manifest["pages"]) == 1
    page_row = page_manifest["pages"][0]
    assert len(page_row["page_paths"]) >= 2

    claim_paths: dict[str, str] = {}
    materialized_block_anchors: set[str] = set()
    for part in result.pages[0].parts:
        materialized_block_anchors.update(
            anchor for anchor in getattr(part, "anchor_ids") if anchor.startswith("block-")
        )
        for claim_id in getattr(part, "claim_ids"):
            assert claim_id not in claim_paths
            claim_paths[claim_id] = part.relative_path
    claims = [
        json.loads(line)
        for line in (batch / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    repeated_claims = [claim for claim in claims if claim["text"] == "Same fact."]
    assert repeated_claims
    assert all(claim.get("source_block_id") for claim in repeated_claims)
    assert all(
        claim["page_path"] == claim_paths[claim["claim_id"]]
        for claim in repeated_claims
    )
    assert len({claim["page_path"] for claim in repeated_claims}) >= 2
    assert len(materialized_block_anchors) == len(page_row["block_ids"])
    assert all(
        any(f'<a id="{anchor}"></a>' in part.text for part in result.pages[0].parts)
        for anchor in materialized_block_anchors
    )


def test_task7_e2e_interrupted_recovery_keeps_claims_on_completed_later_parts(tmp_path: Path) -> None:
    root = tmp_path / "interrupted-multipart"
    items = root / "items" / "Payments"
    items.mkdir(parents=True)
    large_payload = (
        "# Large\n\n" + "\n".join(f"Large fact {index}." for index in range(220)) + "\n"
    ).encode()
    other_payload = b"# Other\n\nOther fact.\n"
    (items / "large.md").write_bytes(large_payload)
    (items / "other.md").write_bytes(other_payload)
    entries = [
        {
            "source_uri": "Payments/large.md",
            "source_id": "large",
            "content_hash": hashlib.sha256(large_payload).hexdigest(),
            "byte_count": len(large_payload),
        },
        {
            "source_uri": "Payments/other.md",
            "source_id": "other",
            "content_hash": hashlib.sha256(other_payload).hexdigest(),
            "byte_count": len(other_payload),
        },
    ]
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps({"input_manifest_id": "task7-interrupted-multipart", "expected_count": 2, "entries": entries}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    baseline = compile_batch(
        root,
        manifest_path=manifest,
        output_parent=tmp_path / "baseline-batches",
        cache_root=tmp_path / "cache",
        provider=FakeProvider(),
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
    )
    baseline_manifest = _read_json(Path(baseline.output_dir) / "_audit" / "page-manifest.json")
    large_row = next(row for row in baseline_manifest["pages"] if row["topic_key"] == "payments:large")
    assert len(large_row["page_paths"]) >= 2

    interrupted = compile_batch(
        root,
        manifest_path=manifest,
        output_parent=tmp_path / "interrupted-batches",
        cache_root=tmp_path / "cache",
        provider=FakeProvider(),
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
        write_failure_after=len(large_row["page_paths"]) + 1,
    )
    batch = Path(interrupted.output_dir)
    assert interrupted.outcome == "interrupted"
    partial_manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert any(row["topic_key"] == "payments:large" for row in partial_manifest["pages"])
    claims = [
        json.loads(line)
        for line in (batch / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(
        claim["source_path"] == "Payments/large.md"
        and claim["page_path"].endswith(".part-002.md")
        for claim in claims
    )


def test_task7_e2e_write_interruption_is_not_a_completed_batch(tmp_path: Path) -> None:
    result = _run(tmp_path, provider=FakeProvider(), write_failure_after=1)
    batch = Path(result.output_dir)
    assert result.outcome == "interrupted"
    assert (batch / "products").exists()
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert manifest["publish_status"] == "not_released"
    assert manifest["run_status"] in {"interrupted", "blocked"}
    assert manifest["run_status"] != "complete"


def test_task7_e2e_provider_plan_is_visible_before_first_provider_call(tmp_path: Path) -> None:
    output = io.StringIO()
    observations: list[str] = []

    class PlanAwareProvider(FakeProvider):
        def complete(self) -> dict[str, str]:
            observations.append(output.getvalue())
            return super().complete()

    _run(tmp_path, provider=PlanAwareProvider(), stdout=output)
    assert observations
    assert observations[0].startswith("Task7 semantic plan:")


def test_task7_e2e_render_failure_records_blocked_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import knowledge_digest.semantic_compiler as compiler_module

    def fail_render(*args: object, **kwargs: object) -> object:
        raise ValueError("render invariant failed")

    monkeypatch.setattr(compiler_module, "render_pages", fail_render)
    result = _run(tmp_path, provider=FakeProvider())
    batch = Path(result.output_dir)

    assert result.outcome == "blocked"
    assert not (batch / "products").exists()
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert manifest["run_status"] == "blocked"
    assert any(row.get("reason") == "render_failed" for row in manifest["blockers"])
    assert "complete" not in (batch / "README.md").read_text(encoding="utf-8")


def test_task7_e2e_real_write_failure_records_interrupted_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import knowledge_digest.semantic_compiler as compiler_module

    original_write = compiler_module._write_text
    failure = {"raised": False}

    def fail_product_write(path: Path, text: str) -> None:
        if "products" in path.parts and not failure["raised"]:
            failure["raised"] = True
            raise OSError("simulated disk full")
        original_write(path, text)

    monkeypatch.setattr(compiler_module, "_write_text", fail_product_write)
    result = _run(tmp_path, provider=FakeProvider())
    batch = Path(result.output_dir)

    assert result.outcome == "interrupted"
    manifest = _read_json(batch / "_audit" / "page-manifest.json")
    assert manifest["run_status"] == "interrupted"
    assert any(row.get("reason") == "write_failed" for row in manifest["blockers"])
    assert "run_status: `complete`" not in (batch / "README.md").read_text(encoding="utf-8")


def test_task7_e2e_interrupted_large_batch_can_write_its_partial_audit(tmp_path: Path) -> None:
    root = tmp_path / "many"
    items = root / "items" / "Payments"
    items.mkdir(parents=True)
    entries: list[dict[str, object]] = []
    for index in range(25):
        relative = f"Payments/topic-{index:02d}.md"
        payload = f"# Topic {index}\n\nThis source contains unique fact {index}.\n".encode()
        target = root / "items" / relative
        target.write_bytes(payload)
        entries.append({
            "source_uri": relative,
            "source_id": f"many-{index:02d}",
            "content_hash": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
        })
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps({"input_manifest_id": "task7-many", "expected_count": len(entries), "entries": entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    result = compile_batch(
        root,
        manifest_path=manifest,
        output_parent=tmp_path / "batches",
        cache_root=tmp_path / "cache",
        provider=FakeProvider(),
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
        write_failure_after=1,
    )
    manifest_output = _read_json(Path(result.output_dir) / "_audit" / "page-manifest.json")

    assert result.outcome == "interrupted"
    assert manifest_output["run_status"] == "interrupted"
    assert any(row.get("reason") == "write_interrupted" for row in manifest_output["blockers"])


def test_task7_e2e_heading_only_source_is_known_empty_not_a_coverage_blocker(tmp_path: Path) -> None:
    root = tmp_path / "heading-only"
    target = root / "items" / "Payments" / "heading-only.md"
    target.parent.mkdir(parents=True)
    payload = b"# Heading only\n\n"
    target.write_bytes(payload)
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps({
            "input_manifest_id": "task7-heading-only",
            "expected_count": 1,
            "entries": [{
                "source_uri": "Payments/heading-only.md",
                "source_id": "heading-only",
                "content_hash": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }],
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    result = compile_batch(
        root,
        manifest_path=manifest,
        output_parent=tmp_path / "batches",
        cache_root=tmp_path / "cache",
        provider=FakeProvider(),
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
    )
    output_manifest = _read_json(Path(result.output_dir) / "_audit" / "page-manifest.json")

    assert result.outcome == "not_released"
    assert output_manifest["run_status"] == "complete"
    assert output_manifest["source_ledger"][0]["source_status"] == "known_empty"
    assert not output_manifest["blockers"]


def test_task7_e2e_plan_has_mechanical_provider_budget_and_real_cost_fields(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = _run(tmp_path, provider=FakeProvider())
    printed = capsys.readouterr().out
    assert "sources=" in printed
    assert "topics=" in printed
    assert "pages=" in printed
    assert "provider_calls=" in printed
    plan = result.plan
    assert plan["planned_provider_calls"] <= plan["topic_count"] * 2 + 20
    metrics = _read_json(Path(result.output_dir) / "_audit" / "run-metrics.json")
    assert metrics["elapsed_ms"] is not None
    assert metrics["provider_calls"] is not None
    assert metrics["provider_tokens"] is not None
    assert metrics["actual_provider_calls"] <= metrics["planned_provider_calls"] * 1.5


def test_task7_e2e_freezes_the_exact_non_digest_regression_nodes_and_causes() -> None:
    _require_api()
    assert tuple(BASELINE_REGRESSION_NODES) == EXPECTED_NODES
    assert set(BASELINE_REGRESSION_CAUSES) == set(EXPECTED_NODES)
    assert all(BASELINE_REGRESSION_CAUSES[node] for node in EXPECTED_NODES)


def test_task7_e2e_default_digest_dispatches_semantic_cli_and_rejects_legacy_flags(tmp_path: Path) -> None:
    cli_manifest = _write_manifest(tmp_path / "cli" / "manifest.json")
    cli_env = os.environ.copy()
    cli_env["KNOWLEDGEDIGEST_TASK7_OUTPUT_PARENT"] = str(tmp_path / "cli" / "batches")
    cli_env["KNOWLEDGEDIGEST_TASK7_CACHE_ROOT"] = str(tmp_path / "cli" / "cache")
    cli_env["KD_PROVIDER_CONFIG"] = str(tmp_path / "cli" / "no-provider-config.json")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "knowledge_digest.simple_cli",
            str(ITEMS_ROOT.parent),
            "--manifest",
            str(cli_manifest),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=cli_env,
        check=False,
    )
    assert result.returncode in {0, 1, 2}
    assert "semantic" in (result.stdout + result.stderr).lower()

    legacy = subprocess.run(
        [sys.executable, "-m", "knowledge_digest.simple_cli", str(ITEMS_ROOT.parent), "--no-llm"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert legacy.returncode == 2
    assert "legacy_digest_reference.py" in (legacy.stdout + legacy.stderr)

    semantic_legacy = subprocess.run(
        [sys.executable, "-m", "knowledge_digest.semantic_cli", str(ITEMS_ROOT.parent), "--no-llm"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=cli_env,
    )
    assert semantic_legacy.returncode == 2
    assert "legacy_digest_reference.py" in (semantic_legacy.stdout + semantic_legacy.stderr)


def test_task7_e2e_semantic_cli_stdout_is_one_machine_readable_json_document(tmp_path: Path) -> None:
    cli_manifest = _write_manifest(tmp_path / "cli-json" / "manifest.json")
    cli_env = os.environ.copy()
    cli_env["KNOWLEDGEDIGEST_TASK7_OUTPUT_PARENT"] = str(tmp_path / "cli-json" / "batches")
    cli_env["KNOWLEDGEDIGEST_TASK7_CACHE_ROOT"] = str(tmp_path / "cli-json" / "cache")
    cli_env["KD_PROVIDER_CONFIG"] = str(tmp_path / "cli-json" / "no-provider-config.json")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "knowledge_digest.semantic_cli",
            str(ITEMS_ROOT.parent),
            "--manifest",
            str(cli_manifest),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        env=cli_env,
        check=False,
    )

    assert result.returncode in {1, 2}
    summary = json.loads(result.stdout)
    assert summary["outcome"] in {"not_released", "blocked"}
    assert "Task7 semantic plan:" not in result.stdout
    assert "Task7 semantic plan:" in result.stderr


def test_task7_e2e_legacy_reference_script_is_independently_invocable() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/legacy_digest_reference.py", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "new_dir" in result.stdout


@pytest.mark.skipif(
    not os.environ.get("KNOWLEDGEDIGEST_TASK7_RAW_CORPUS"),
    reason="real corpus acceptance requires KNOWLEDGEDIGEST_TASK7_RAW_CORPUS=1",
)
def test_task7_e2e_real_corpus_can_be_enabled_explicitly(tmp_path: Path) -> None:
    real_root = Path("/Users/Hugh/Downloads/confluence 原始数据")
    if not real_root.exists():
        pytest.skip("real frozen 89-source corpus is not available in this environment")
    assert configured_provider_from_env is not None
    provider = configured_provider_from_env()
    first = compile_batch(
        real_root,
        manifest_path=PROJECT_ROOT / "config" / "task4-source-coverage-89-input.v1.json",
        output_parent=tmp_path / "first",
        cache_root=tmp_path / "cache" / "model-cache",
        provider=provider,
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
    )
    first_batch = Path(first.output_dir)
    first_manifest = _read_json(first_batch / "_audit" / "page-manifest.json")
    assert first_manifest["source_snapshot"]["expected_count"] == 89
    assert len(first_manifest["source_snapshot"]["entries"]) == 89
    assert len(first_manifest["source_ledger"]) == 89
    assert first_manifest["run_status"] == "complete"
    assert first_manifest["pages"]

    second = compile_batch(
        real_root,
        manifest_path=PROJECT_ROOT / "config" / "task4-source-coverage-89-input.v1.json",
        output_parent=tmp_path / "second",
        cache_root=tmp_path / "cache" / "model-cache",
        provider=configured_provider_from_env(),
        topic_map_path=PROJECT_ROOT / "config" / "task7-topic-map.json",
        today="2026-09-14",
    )
    assert _stable_batch_files(first_batch) == _stable_batch_files(Path(second.output_dir))


_WORKFLOWHUB_AC_IDS = tuple(f"AC-{index:02d}" for index in range(1, 14))
_WORKFLOWHUB_FAST_COMMAND = (
    "tests/acceptance/test_task7_split.py",
    "tests/acceptance/test_task7_group.py",
    "tests/acceptance/test_task7_claims.py",
    "tests/acceptance/test_task7_pages.py",
    "tests/acceptance/test_task7_cache.py",
    "tests/acceptance/test_task7_audit.py",
    "tests/acceptance/test_task7_e2e.py",
)


def _workflowhub_acceptance_json(*, real_corpus: bool) -> int:
    """Run the declared acceptance command and emit its machine oracle.

    WorkflowHub consumes JSON on stdout and keeps the test runner's normal
    diagnostics on stderr.  The suite is the single declared oracle for all
    Task7 ACs; the per-AC rows make that shared oracle explicit without
    inventing a second implementation or a claimed verdict.
    """

    if real_corpus:
        command = [sys.executable, "-m", "pytest", "tests/acceptance/test_task7_e2e.py", "-q", "-k", "real_corpus"]
    else:
        command = [sys.executable, "-m", "pytest", * _WORKFLOWHUB_FAST_COMMAND, "-q"]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        stdout=sys.stderr,
        stderr=sys.stderr,
        check=False,
        env=os.environ.copy(),
    )
    payload = {
        "entries": [
            {
                "acceptance_criterion_id": acceptance_criterion_id,
                "assertions": [
                    {
                        "id": "task7_pytest_exit_code",
                        "expected": 0,
                        "actual": result.returncode,
                    }
                ],
            }
            for acceptance_criterion_id in _WORKFLOWHUB_AC_IDS
        ]
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return result.returncode


if __name__ == "__main__" and "--workflowhub-json" in sys.argv:
    raise SystemExit(_workflowhub_acceptance_json(real_corpus="--real-corpus" in sys.argv))
