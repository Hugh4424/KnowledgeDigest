"""Task7 P6: machine-readable audit artifacts, status, and coverage contracts."""

from __future__ import annotations

import json

import pytest


try:
    from knowledge_digest.semantic_audit import build_audit, derive_source_status, write_audit
except (ImportError, ModuleNotFoundError):
    # Keep the RED assertions collectable before T012 adds the module.
    build_audit = None
    derive_source_status = None
    write_audit = None


def _require_api():
    assert build_audit is not None, "semantic_audit.build_audit is not implemented"
    return build_audit


def _require_write_api():
    assert write_audit is not None, "semantic_audit.write_audit is not implemented"
    return write_audit


def _block(source_path: str, block_id: str, text: str, *, content_hash: str, kind: str = "table") -> dict[str, object]:
    return {
        "source_path": source_path,
        "block_id": block_id,
        "content_hash": content_hash,
        "kind": kind,
        "line_start": 1,
        "line_end": 1,
        "text": text,
        "heading_path": ("Payments", "Authentication", "Login"),
    }


def _fixtures(*, audit_page: bool = False) -> dict[str, object]:
    canonical = _block(
        "payments/login.md",
        "block-login",
        "| request | response |",
        content_hash="block-hash-login",
    )
    duplicate = _block(
        "billing/login-copy.md",
        "block-copy",
        "| request | response |",
        content_hash="block-hash-login",
    )
    audit_block = _block(
        "payments/audit-notes.md",
        "block-audit",
        "audit only evidence",
        content_hash="block-hash-audit",
        kind="narrative",
    )
    empty = {
        "source_path": "payments/empty.md",
        "content_hash": "source-hash-empty",
        "readable": True,
        "blocks": [],
    }
    sources = [
        {
            "source_path": "payments/login.md",
            "content_hash": "source-hash-login",
            "readable": True,
            "blocks": [canonical],
        },
        empty,
        {
            "source_path": "billing/login-copy.md",
            "content_hash": "source-hash-login",
            "readable": True,
            "blocks": [duplicate],
        },
        {
            "source_path": "payments/audit-notes.md",
            "content_hash": "source-hash-audit",
            "readable": True,
            "blocks": [audit_block],
        },
    ]
    pages = [
        {
            "topic_key": "payments:login",
            "page_path": "products/payments/authentication/login.md",
            "source_paths": ["payments/login.md"],
            "block_ids": ["block-login"],
            "claim_ids": ["claim-supported", "claim-unknown"],
        }
    ]
    if audit_page:
        pages.append(
            {
                "topic_key": "payments:audit",
                "page_path": "products/payments/authentication/audit.md",
                "source_paths": ["payments/audit-notes.md"],
                "block_ids": ["block-audit"],
                "claim_ids": [],
            }
        )
    claims = [
        {
            "claim_id": "claim-supported",
            "source_path": "payments/login.md",
            "content_hash": "block-hash-login",
            "line_start": 1,
            "line_end": 1,
            "char_start": 0,
            "char_end": 9,
            "page_path": "products/payments/authentication/login.md",
            "page_anchor": "claim-1",
            "span_start": 0,
            "span_end": 9,
            "claim_kind": "narrative",
            "status": "sourced",
            "text": "支持登录。",
            "retrieval_evidence": [],
        },
        {
            "claim_id": "claim-unknown",
            "source_path": "payments/login.md",
            "content_hash": "block-hash-login",
            "line_start": None,
            "line_end": None,
            "char_start": None,
            "char_end": None,
            "page_path": "products/payments/authentication/login.md",
            "page_anchor": "intro",
            "span_start": None,
            "span_end": None,
            "claim_kind": "intro",
            "status": "原文未明确",
            "text": "原文未明确",
            "retrieval_evidence": [{"query": "登录", "matched": False}],
        },
    ]
    return {
        "blocks": [canonical, duplicate, audit_block],
        "claims": claims,
        "pages": pages,
        "source_records": sources,
        "block_anchors": {
            "block-login": {
                "page_path": "products/payments/authentication/login.md",
                "page_anchor": "reference-1",
            }
        },
        "audit_only_sources": ["payments/audit-notes.md"],
        "source_snapshot": {
            "manifest_id": "task5-source-snapshot-v2",
            "entries": [
                {"source_path": row["source_path"], "content_hash": row["content_hash"]}
                for row in sources
            ],
        },
        "attempt_id": "attempt-audit-1",
        "model_suggestions": [
            {"product": "payments", "from": "login", "to": "session", "confidence": 0.91}
        ],
        "metrics": {
            "elapsed_ms": 0,
            "provider_calls": 0,
            "provider_tokens": 0,
            "cache_hits": 1,
            "planned_provider_calls": 4,
            "actual_provider_calls": 0,
            "reasons": {
                "elapsed_ms": "cache_hit",
                "provider_calls": "cache_hit",
                "provider_tokens": "cache_hit",
            },
        },
    }


def _run(**overrides: object) -> object:
    build_audit_api = _require_api()
    values = _fixtures()
    values.update(overrides)
    return build_audit_api(**values)


def test_task7_audit_emits_exact_five_machine_readable_artifacts() -> None:
    bundle = _run()
    files = getattr(bundle, "files")
    assert set(files) == {
        "_audit/reference-blocks.jsonl",
        "_audit/sources.jsonl",
        "_audit/page-manifest.json",
        "_audit/run-metrics.json",
        "_audit/suspected-synonyms.md",
    }

    reference_rows = [json.loads(line) for line in files["_audit/reference-blocks.jsonl"].splitlines()]
    assert reference_rows
    assert {"block_id", "source_path", "content_hash", "block_kind", "line_start", "line_end", "page_path", "page_anchor", "status"} <= set(reference_rows[0])

    source_rows = [json.loads(line) for line in files["_audit/sources.jsonl"].splitlines()]
    assert {"claim_id", "source_path", "content_hash", "line_start", "line_end", "char_start", "char_end", "page_path", "page_anchor", "span_start", "span_end", "claim_kind", "status"} <= set(source_rows[0])

    manifest = json.loads(files["_audit/page-manifest.json"])
    assert manifest["publish_status"] == "not_released"
    assert manifest["run_status"] == "complete"
    assert manifest["attempt_id"] == "attempt-audit-1"
    assert {"source_snapshot", "blockers", "pages", "source_to_pages", "source_ledger"} <= set(manifest)

    metrics = json.loads(files["_audit/run-metrics.json"])
    assert {"elapsed_ms", "provider_calls", "provider_tokens", "cache_hits", "planned_provider_calls", "actual_provider_calls", "reasons", "blockers"} <= set(metrics)
    assert "# 疑似同义主题" in files["_audit/suspected-synonyms.md"]


def test_task7_audit_derives_source_four_states_and_claim_unknown_separately() -> None:
    bundle = _run()
    statuses = getattr(bundle, "source_statuses")
    assert statuses == {
        "billing/login-copy.md": "duplicate_alias",
        "payments/audit-notes.md": "audit_only",
        "payments/empty.md": "known_empty",
        "payments/login.md": "ready",
    }
    assert getattr(bundle, "fact_claim_count") == 1
    source_rows = getattr(bundle, "source_rows")
    unknown = next(row for row in source_rows if row["claim_id"] == "claim-unknown")
    assert unknown["status"] == "原文未明确"
    assert unknown["claim_kind"] == "intro"
    assert unknown["retrieval_evidence"]
    assert unknown["claim_id"] not in getattr(bundle, "fact_claim_ids")


def test_task7_audit_only_source_does_not_steal_duplicate_canonical() -> None:
    assert derive_source_status is not None
    shared_hash = "shared-content-hash"
    source_records = [
        {
            "source_path": "payments/audit-first.md",
            "content_hash": shared_hash,
            "blocks": [_block("payments/audit-first.md", "audit-first", "same", content_hash=shared_hash, kind="narrative")],
        },
        {
            "source_path": "payments/product-copy.md",
            "content_hash": shared_hash,
            "blocks": [_block("payments/product-copy.md", "product-copy", "same", content_hash=shared_hash, kind="narrative")],
        },
    ]

    statuses = derive_source_status(source_records, audit_only_sources=("payments/audit-first.md",))

    assert statuses == {
        "payments/audit-first.md": "audit_only",
        "payments/product-copy.md": "ready",
    }


def test_task7_audit_alias_reuses_canonical_anchor_and_coverage_is_two_way() -> None:
    bundle = _run()
    rows = getattr(bundle, "reference_rows")
    canonical = next(row for row in rows if row["block_id"] == "block-login")
    alias = next(row for row in rows if row["block_id"] == "block-copy")
    assert canonical["status"] == "ready"
    assert alias["status"] == "duplicate_alias"
    assert alias["alias_of"] == "payments/login.md"
    assert alias["canonical_block_id"] == "block-login"
    assert alias["page_path"] == canonical["page_path"]
    assert alias["page_anchor"] == canonical["page_anchor"]
    assert getattr(bundle, "coverage_ok") is True

    duplicate_page = dict(_fixtures()["pages"][0])
    duplicate_page["page_path"] = "products/payments/authentication/duplicate.md"
    duplicate_page["block_ids"] = ["block-login"]
    with pytest.raises(ValueError, match="coverage"):
        _run(pages=[_fixtures()["pages"][0], duplicate_page])


def test_task7_audit_blocks_declared_audit_only_source_when_it_enters_products() -> None:
    bundle = _run(pages=_fixtures(audit_page=True)["pages"])
    manifest = getattr(bundle, "manifest")
    assert manifest["run_status"] == "blocked"
    assert any(
        blocker.get("source_path") == "payments/audit-notes.md"
        and "audit_only" in blocker.get("reason", "")
        for blocker in manifest["blockers"]
    )


@pytest.mark.parametrize(
    ("source_path", "reason"),
    (
        ("payments/not-declared.md", "page_references_unknown_source"),
        ("payments/empty.md", "known_empty_source_entered_products"),
    ),
)
def test_task7_audit_blocks_page_sources_outside_the_declared_product_ledger(
    source_path: str,
    reason: str,
) -> None:
    values = _fixtures()
    page = dict(values["pages"][0])
    page["source_paths"] = [source_path]
    page["block_ids"] = []
    page["claim_ids"] = []

    bundle = _run(pages=[page])
    manifest = getattr(bundle, "manifest")

    assert manifest["run_status"] == "blocked"
    assert any(
        blocker.get("source_path") == source_path and blocker.get("reason") == reason
        for blocker in manifest["blockers"]
    )


def test_task7_audit_does_not_infer_audit_only_from_missing_page_output() -> None:
    values = _fixtures()
    unaccounted = _block(
        "payments/unaccounted.md",
        "block-unaccounted",
        "unaccounted evidence",
        content_hash="block-hash-unaccounted",
    )
    values["blocks"] = [*values["blocks"], unaccounted]
    values["source_records"] = [
        *values["source_records"],
        {
            "source_path": "payments/unaccounted.md",
            "content_hash": "source-hash-unaccounted",
            "readable": True,
            "blocks": [unaccounted],
        },
    ]
    values["audit_only_sources"] = []
    bundle = _run(**values)
    assert getattr(bundle, "source_statuses")["payments/unaccounted.md"] == "ready"
    manifest = getattr(bundle, "manifest")
    assert manifest["run_status"] == "blocked"
    assert any(
        blocker.get("source_path") == "payments/unaccounted.md"
        and "audit_only" not in blocker.get("reason", "")
        for blocker in manifest["blockers"]
    )


def test_task7_audit_records_real_zero_costs_with_reason_and_enforces_budget() -> None:
    bundle = _run()
    metrics = getattr(bundle, "metrics")
    assert metrics["elapsed_ms"] == 0
    assert metrics["provider_calls"] == 0
    assert metrics["provider_tokens"] == 0
    assert metrics["reasons"]["provider_calls"] == "cache_hit"
    assert metrics["reasons"]["provider_tokens"] == "cache_hit"
    assert metrics["planned_provider_calls"] <= len(_fixtures()["pages"]) * 2 + 20
    assert metrics["actual_provider_calls"] <= metrics["planned_provider_calls"] * 1.5


def test_task7_audit_rejects_release_and_preserves_explicit_blocked_status() -> None:
    with pytest.raises(ValueError, match="not_released"):
        _run(publish_status="released")

    bundle = _run(run_status="blocked")
    assert getattr(bundle, "manifest")["publish_status"] == "not_released"
    assert getattr(bundle, "manifest")["run_status"] == "blocked"


def test_task7_audit_requires_complete_provenance_for_sourced_claims() -> None:
    values = _fixtures()
    claim = dict(values["claims"][0])
    claim["content_hash"] = ""
    claim["span_start"] = None
    values["claims"] = [claim, values["claims"][1]]
    with pytest.raises(ValueError, match="sourced claim"):
        _run(**values)


def test_task7_audit_rejects_anchor_outside_emitted_page_parts() -> None:
    values = _fixtures()
    values["block_anchors"] = {
        "block-login": {
            "page_path": "products/payments/authentication/not-emitted.md",
            "page_anchor": "reference-1",
        }
    }
    with pytest.raises(ValueError, match="coverage"):
        _run(**values)


def test_task7_audit_writes_surrogateescaped_text_as_valid_utf8_json(tmp_path) -> None:
    values = _fixtures()
    claim = dict(values["claims"][0])
    claim["text"] = "原文字节：\udc80"
    values["claims"] = [claim, values["claims"][1]]

    write_audit_api = _require_write_api()
    result = write_audit_api(tmp_path, **values)
    output = (tmp_path / "_audit" / "sources.jsonl").read_bytes()
    assert output.isascii()
    rows = [json.loads(line) for line in output.decode("utf-8").splitlines()]
    sourced = next(row for row in rows if row["claim_id"] == "claim-supported")
    assert sourced["text"] == "原文字节：\udc80"
    assert set(result.files) == {
        "_audit/reference-blocks.jsonl",
        "_audit/sources.jsonl",
        "_audit/page-manifest.json",
        "_audit/run-metrics.json",
        "_audit/suspected-synonyms.md",
    }
