from __future__ import annotations

import json
import hashlib
import importlib.util
from pathlib import Path

import pytest

from knowledge_digest.task5_runtime import (
    Task5RuntimeError,
    _create_lock,
    _manifest,
    _remove_legacy_audit_links,
    _output_paths,
    _parse_source_blocks,
    _preflight,
    _read_json,
    run_root_cause_preflight,
    _slice_source_selection,
    _source_scope_ledger,
    _transition_lock,
    _write_failure_evidence,
    _validate_source_manifest,
    _summarize_slice_result,
    _directory_manifest_sha256,
)


def test_formal_audit_removes_links_to_ledgers_not_published_in_final_tree(tmp_path: Path) -> None:
    audit = tmp_path / "Audit.md"
    audit.write_text(
        "- 来源索引：[_audit/sources.jsonl](_audit/sources.jsonl)\n"
        "- Evidence 详情：见 [`_audit/evidence.jsonl`](_audit/evidence.jsonl)，按 evidence_id 和行号回查；来源索引不复制整篇原文。\n",
        encoding="utf-8",
    )

    _remove_legacy_audit_links(audit)

    text = audit.read_text(encoding="utf-8")
    assert "(_audit/sources.jsonl)" not in text
    assert "(_audit/evidence.jsonl)" not in text
    assert "见本页“来源清单”" in text
    assert "机器证据见本目录 `_audit/`" in text


def test_formal_audit_removes_quality_link_to_host_only_evidence(tmp_path: Path) -> None:
    audit = tmp_path / "Audit.md"
    audit.write_text(
        "- 详细生成、校验和证据闭环：[_audit/quality.json](_audit/quality.json)\n",
        encoding="utf-8",
    )

    _remove_legacy_audit_links(audit)

    text = audit.read_text(encoding="utf-8")
    assert "(_audit/quality.json)" not in text
    assert "质量证据保留在 host-only receipt" in text


def test_provider_unavailability_can_be_recorded_as_blocked_exit_two(tmp_path: Path) -> None:
    output = tmp_path / "candidate"
    path, _ = _write_failure_evidence(
        output=output,
        run_id="run-provider-unavailable",
        reason_code="provider_unavailable",
        provider_identity={},
        observed_calls={"llm": 0, "embedding": 0},
        audit_ref=None,
        output_retained=False,
        status="blocked",
        exit_code=2,
    )

    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["status"] == "blocked"
    assert value["exit_code"] == 2


def test_directory_manifest_hash_survives_candidate_rename(tmp_path: Path) -> None:
    stage = tmp_path / "candidate-stage"
    output = tmp_path / "published"
    bundle = stage / "bundle"
    manifest = bundle / "_audit" / "directory-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"schema_version":"task5-directory-manifest.v1"}\n', encoding="utf-8")

    candidate_sha256 = _directory_manifest_sha256(bundle)
    stage.replace(output)

    assert _directory_manifest_sha256(output / "bundle") == candidate_sha256
from knowledge_digest.compiler import _load_sources

_evaluator_spec = importlib.util.spec_from_file_location(
    "task5_reader_quality_evaluator",
    Path(__file__).parents[2] / "scripts/evaluate_reader_candidate.py",
)
assert _evaluator_spec and _evaluator_spec.loader
_evaluator = importlib.util.module_from_spec(_evaluator_spec)
_evaluator_spec.loader.exec_module(_evaluator)
_source_page_closure = _evaluator._source_page_closure


def test_slice_summary_ignores_expected_unreleased_quality_comparison_warning():
    result = _summarize_slice_result(
        {"slice_id": "fixture", "source_count": 25, "nonempty_source_count": 24},
        type("Result", (), {"outcome": "not_released"})(),
        {
            "warnings": ["run: quality_dimensions_not_all_kd_win"],
            "quality_route_ledger": [
                {"projection_id": "Q-POS-01.positioning", "status": "ready"}
            ],
        },
    )

    assert result["quality"] == "passed"
    assert result["release_blocked"] is False


def test_real_run_stops_before_raw_or_provider_when_m401r_is_missing(tmp_path):
    raw = tmp_path / "raw"
    companybrain = tmp_path / "companybrain"
    raw.mkdir()
    companybrain.mkdir()
    provider_config = tmp_path / "provider.json"
    provider_config.write_text(json.dumps({"llm": {}, "embedding": {}}), encoding="utf-8")
    output = tmp_path / "output"
    result = _preflight(
        run_id="run-test",
        attempt_id="m402-test",
        raw=raw,
        companybrain=companybrain,
        output=output,
        evidence_root=tmp_path / "evidence",
        provider_config=provider_config,
        handoff=None,
        m401_r=None,
    )
    assert result["status"] == "blocked"
    assert result["observed_calls"] == {"llm": 0, "embedding": 0, "external_http_attempts": 0}
    assert not output.exists()
    assert (tmp_path / "evidence/run-preflight/attempts/m402-test/preflight-result.json").is_file()


def test_real_run_rejects_output_outside_downloads_before_provider_or_output_creation(tmp_path):
    raw = tmp_path / "raw"
    companybrain = tmp_path / "companybrain"
    raw.mkdir()
    companybrain.mkdir()
    provider_config = tmp_path / "provider.json"
    provider_config.write_text(json.dumps({"llm": {}, "embedding": {}}), encoding="utf-8")
    result = _preflight(
        run_id="run-outside-downloads",
        attempt_id="m402-outside-downloads",
        raw=raw,
        companybrain=companybrain,
        output=tmp_path / "output",
        evidence_root=tmp_path / "evidence",
        provider_config=provider_config,
        handoff=None,
        m401_r=None,
    )
    assert result["status"] == "blocked"
    assert any("Downloads" in reason for reason in result["reasons"])
    assert result["observed_calls"] == {"llm": 0, "embedding": 0, "external_http_attempts": 0}
    assert not (tmp_path / "output").exists()


def test_frozen_source_manifest_matches_real_89_source_snapshot():
    identity = _validate_source_manifest(
        Path("/Users/Hugh/Downloads/confluence 原始数据"),
        Path("config/task5-source-page-manifest-v2.json"),
    )
    assert identity["source_count"] == 89
    assert identity["known_empty_paths"] == ["emm for android /AE - AirViewer厂商管理.md"]


def test_quality_source_loader_uses_frozen_source_ids_for_formal_runs(tmp_path: Path):
    source_root = tmp_path / "raw"
    source_root.mkdir()
    (source_root / "Product.md").write_text("# Product\n", encoding="utf-8")

    sources = _load_sources(
        source_root,
        source_id_by_path={"Product.md": "source-frozen-id"},
    )

    assert len(sources) == 1
    assert sources[0].source_id == "source-frozen-id"
    assert sources[0].evidence[0]["evidence_id"].startswith("source-frozen-id-")


def test_source_and_evidence_ledgers_can_be_read_from_compiler_audit_dir(tmp_path: Path):
    raw = tmp_path / "raw"
    raw.mkdir()
    manifest = json.loads(Path("config/task5-source-page-manifest-v2.json").read_text(encoding="utf-8"))
    entries = manifest["source_snapshot"]["entries"]
    rows = []
    for entry in entries:
        source_path = raw / entry["source_path"]
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(b"" if entry["expected_status"] == "empty" else b"content\n")
        rows.append({
            "relative_path": entry["source_path"],
            "source_id": entry["source_id"],
            "raw_hash": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "status": "known_empty" if entry["expected_status"] == "empty" else "ready",
        })
    audit = tmp_path / "bundle" / "_audit"
    audit.mkdir(parents=True)
    (audit / "sources.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    (audit / "evidence.jsonl").write_text("", encoding="utf-8")

    from knowledge_digest.task5_runtime import _evidence_rows, _source_rows

    assert len(_source_rows(tmp_path / "bundle", raw, Path("config/task5-source-page-manifest-v2.json"))) == 89
    assert _evidence_rows(tmp_path / "bundle") == []


def test_formal_evidence_reader_uses_complete_source_blocks_not_render_projection(tmp_path: Path):
    from knowledge_digest.task5_runtime import _evidence_rows

    bundle = tmp_path / "bundle"
    audit = bundle / "_audit"
    audit.mkdir(parents=True)
    (audit / "evidence.jsonl").write_text(
        json.dumps({"block_id": "source-1-e0001", "page_path": "products/p.md"}) + "\n",
        encoding="utf-8",
    )
    source_rows = [{
        "source_id": "source-1",
        "evidence": [
            {"evidence_id": "source-1-e0001", "start_line": 1, "end_line": 2, "block_content_sha256": "a" * 64},
            {"evidence_id": "source-1-e0002", "start_line": 4, "end_line": 5, "block_content_sha256": "b" * 64},
        ],
    }]

    assert _evidence_rows(bundle, source_rows) == [
        {"evidence_id": "source-1-e0001", "source_id": "source-1", "start_line": 1, "end_line": 2, "block_content_sha256": "a" * 64},
        {"evidence_id": "source-1-e0002", "source_id": "source-1", "start_line": 4, "end_line": 5, "block_content_sha256": "b" * 64},
    ]


def test_raw_source_scope_ledger_closes_89_sources_without_provider_calls():
    identity, ledger = _source_scope_ledger(
        Path("/Users/Hugh/Downloads/confluence 原始数据"),
        Path("config/task5-source-page-manifest-v2.json"),
    )
    assert identity["source_count"] == 89
    assert ledger["schema_version"] == "task5-source-scope-ledger.v2"
    assert ledger["coverage"]["source_count"] == 89
    assert ledger["coverage"]["block_count"] > 89
    assert ledger["coverage"]["claim_count"] == ledger["coverage"]["block_count"]
    assert ledger["coverage"]["ordinary_present_total"] == 88
    assert ledger["coverage"]["ordinary_present_eligible_count"] == 87
    assert ledger["coverage"]["known_empty_count"] == 1
    assert ledger["coverage"]["duplicate_alias_count"] == 1
    assert ledger["coverage"]["provider_calls"] == 0
    assert all("canonical_text" not in row for row in ledger["rows"])


def test_raw_source_scope_ledger_is_replay_stable():
    _, first = _source_scope_ledger(
        Path("/Users/Hugh/Downloads/confluence 原始数据"),
        Path("config/task5-source-page-manifest-v2.json"),
    )
    _, second = _source_scope_ledger(
        Path("/Users/Hugh/Downloads/confluence 原始数据"),
        Path("config/task5-source-page-manifest-v2.json"),
    )
    assert first == second


def test_current_slice_fixture_derives_its_exact_source_closure():
    selection = _slice_source_selection(
        Path("config/task5-slice-cases-v1.json"),
        Path("config/task5-source-page-manifest-v2.json"),
    )
    assert selection["case_count"] == 11
    assert selection["source_count"] == 27
    assert len(selection["source_paths"]) == 27
    assert selection["source_paths"] == list(dict.fromkeys(selection["source_paths"]))


def test_frozen_slice_selection_rejects_duplicate_case_or_unknown_source(tmp_path: Path):
    value = json.loads(Path("config/task5-slice-cases-v1.json").read_text(encoding="utf-8"))
    value["cases"].append(dict(value["cases"][0]))
    path = tmp_path / "slice.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    try:
        _slice_source_selection(path, Path("config/task5-source-page-manifest-v2.json"))
    except Task5RuntimeError as error:
        assert "11 cases" in str(error) or "duplicate case" in str(error)
    else:
        raise AssertionError("slice fixture drift must be rejected")


def test_root_cause_preflight_keeps_missing_v50_blocked_without_promotion(tmp_path: Path):
    raw = tmp_path / "raw"
    companybrain = tmp_path / "companybrain"
    raw.mkdir()
    companybrain.mkdir()
    evidence_root = tmp_path / "evidence"
    from argparse import Namespace

    result = run_root_cause_preflight(Namespace(
        root_cause_input_manifest=Path("config/task5-root-cause-input-manifest-v1.json"),
        root_cause_contract=Path("config/task5-root-cause-evidence-v2.json"),
        raw_input=raw,
        companybrain=companybrain,
        evidence_root=evidence_root,
        network_policy="deny",
    ))
    assert result == 2
    attempts = list((evidence_root / "root-cause" / "attempts").glob("*/root-cause-evidence.json"))
    assert len(attempts) == 1
    evidence = json.loads(attempts[0].read_text(encoding="utf-8"))
    assert evidence["status"] == "failed"
    assert evidence["outcome"] == "blocked"
    assert evidence["observed_calls"] == {"llm": 0, "embedding": 0, "external_http_attempts": 0}
    assert evidence["input_snapshots"]["RC-USER-V50"]["status"] == "unavailable"
    assert evidence["coverage"]["source_scope"]["provider_calls"] == 0
    assert not (evidence_root / "root-cause" / "root-cause-evidence.json").exists()
    assert str(tmp_path) not in attempts[0].read_text(encoding="utf-8")


def test_source_block_parser_preserves_code_tables_lists_and_link_targets():
    raw = (
        "# 标题\r\n"
        "说明文字 [文档](https://example.test/a)\r\n"
        "- 步骤一\r\n"
        "| 名称 | 值 |\r\n"
        "| --- | --- |\r\n"
        "| 开关 | 开启 |\r\n"
        "```json\r\n"
        "{\"enabled\":true}\r\n"
        "```\r\n"
    ).encode("utf-8")
    blocks = _parse_source_blocks(raw, "source-test", "Product/source.md")
    assert {block["kind"] for block in blocks} == {"heading", "paragraph", "link_target", "list_item", "table_cell", "config"}
    assert len(blocks) == len({block["block_id"] for block in blocks})
    assert all(block["raw_start_byte"] < block["raw_end_byte"] for block in blocks)
    assert all(raw[block["raw_start_byte"]:block["raw_end_byte"]].decode("utf-8") for block in blocks)
    assert all(block["raw_start_line"] <= block["raw_end_line"] for block in blocks)


def test_frozen_source_manifest_rejects_changed_raw_bytes(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(Path("config/task5-source-page-manifest-v2.json").read_text(encoding="utf-8"), encoding="utf-8")
    raw = tmp_path / "raw"
    raw.mkdir()
    for entry in json.loads(manifest.read_text(encoding="utf-8"))["source_snapshot"]["entries"]:
        path = raw / entry["source_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    try:
        _validate_source_manifest(raw, manifest)
    except Task5RuntimeError as error:
        assert "raw source set" in str(error) or "metadata" in str(error)
    else:
        raise AssertionError("changed source bytes must be rejected")


def test_source_ledger_requires_exact_raw_path_and_hash_closure(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "_digest").mkdir(parents=True)
    raw = tmp_path / "raw"
    raw.mkdir()
    entries = json.loads(Path("config/task5-source-page-manifest-v2.json").read_text(encoding="utf-8"))["source_snapshot"]["entries"]
    for entry in entries:
        path = raw / entry["source_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"" if entry["expected_status"] == "empty" else b"content\n")
    (bundle / "_digest" / "sources.jsonl").write_text("\n".join(json.dumps({
        "relative_path": entry["source_path"],
        "source_id": entry["source_id"],
        "raw_hash": "0" * 64,
        "status": "known_empty" if entry["expected_status"] == "empty" else "ready",
    }) for entry in entries) + "\n", encoding="utf-8")
    try:
        from knowledge_digest.task5_runtime import _source_rows
        _source_rows(bundle, raw, Path("config/task5-source-page-manifest-v2.json"))
    except Task5RuntimeError as error:
        assert "raw hash" in str(error)
    else:
        raise AssertionError("source ledger must be bound to raw hashes")


def test_source_page_closure_does_not_count_quality_page_as_source_page():
    raw_hash = "a" * 64
    run_state = {
        "manifest": {
            "sources": [{
                "source_id": "src-1",
                "relative_path": "Product/source.md",
                "raw_hash": raw_hash,
                "status": "ready",
                "reader_page_ids": ["src-1"],
                "duplicate_of": None,
            }],
            "pages": [
                    {"page_id": "Q-POS-01.positioning", "projection_id": "Q-POS-01.positioning", "path": "products/shared/positioning/answer.md", "source_ids": ["src-1"]},
                {"page_id": "src-1", "path": "products/product/concept/source.md", "source_ids": ["src-1"]},
            ],
        }
    }
    pages = {
        "products/shared/positioning/answer.md": {"projection_id": "Q-POS-01.positioning"},
        "products/product/concept/source.md": {},
    }
    source_rows = {"Product/source.md": {"source_id": "src-1", "status": "ready", "raw_hash": raw_hash}}

    assert _source_page_closure({"Product/source.md": raw_hash}, source_rows, run_state, pages, {"Q-POS-01.positioning"}) == []


def test_output_lock_is_canonical_owner_bound_and_retained_after_publish(tmp_path):
    output = tmp_path / "candidate"
    paths = _output_paths(output, "run-lock", "owner-lock")
    paths["lock"].parent.mkdir(parents=True, exist_ok=True)
    record = _create_lock(paths["lock"], paths, run_id="run-lock", material_id="material-1", owner_nonce="owner-lock")
    assert record["schema_version"] == "task5-output-lock.v1"
    assert record["state"] == "held"
    assert record["failure_evidence_path"] is None
    _transition_lock(paths["lock"], "rename_committed")
    _transition_lock(paths["lock"], "finalizing")
    _transition_lock(paths["lock"], "published")
    lock = _read_json(paths["lock"])
    assert lock["state"] == "published"
    assert lock["owner_nonce"] == "owner-lock"
    assert paths["lock"].is_file()


def test_quality_candidate_tree_identity_matches_publication_manifest(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "_audit").mkdir(parents=True)
    (bundle / "products" / "goinsight" / "operation").mkdir(parents=True)
    (bundle / "products" / "goinsight" / "operation" / "page.md").write_text("# page\n", encoding="utf-8")
    (bundle / "_audit" / "directory-manifest.json").write_text("candidate manifest\n", encoding="utf-8")
    (bundle / "_audit" / "run-result.json").write_text("candidate run result\n", encoding="utf-8")

    from knowledge_digest.task5_quality_gate import _tree_digest
    assert _tree_digest(bundle) == _manifest(bundle)["tree_sha256"]
