from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

from knowledge_digest.reader_frontmatter import managed_content_hash, parse_concept_document, serialize_concept_document


ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "task3_full_release" / "closeout-cases.json"


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _case() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_task3_comparison_has_three_sources_all_fixed_dimensions_and_explicit_na() -> None:
    module = _load_script("task2_publication_comparison", ROOT / "scripts" / "task2_publication_comparison.py")
    builder = getattr(module, "build_task3_comparison_report", None)
    assert callable(builder)

    result = builder(evidence=_case()["comparison_inputs"])

    assert result["schema_version"] == "kd-task3-comparison.v1"
    assert set(result["sources"]) == {"task2", "companybrain", "task3"}
    dimensions = {
        "saved_integrity",
        "machine_quality",
        "reader_readability",
        "trust_freshness",
        "failures",
        "performance",
        "cost",
        "limitations",
    }
    assert set(result["dimensions"]) == dimensions
    for dimension in dimensions:
        assert set(result["dimensions"][dimension]) == {"task2", "companybrain", "task3"}
        for value in result["dimensions"][dimension].values():
            assert value["comparability"] in {"comparable", "N/A"}
            assert "basis" in value
    assert result["dimensions"]["machine_quality"]["companybrain"]["comparability"] == "N/A"
    assert "overall_score" not in result
    assert result["release_decision"] == "not_a_release_decision"


def test_task3_comparison_writes_machine_report_without_making_missing_baseline_comparable(tmp_path: Path) -> None:
    module = _load_script("task2_publication_comparison", ROOT / "scripts" / "task2_publication_comparison.py")
    result = module.build_task3_comparison_report(
        evidence=_case()["comparison_inputs"],
        output_dir=tmp_path,
    )

    assert (tmp_path / "COMPARISON.json").is_file()
    assert (tmp_path / "COMPARISON.md").is_file()
    assert result["dimensions"]["cost"]["companybrain"]["comparability"] == "N/A"
    assert "N/A" in (tmp_path / "COMPARISON.md").read_text(encoding="utf-8")


def test_task3_comparison_reads_actual_bundle_audit_reports_root(tmp_path: Path) -> None:
    module = _load_script("task2_publication_comparison_root", ROOT / "scripts" / "task2_publication_comparison.py")
    root = tmp_path / "task3-root"
    (root / "bundle" / "products").mkdir(parents=True)
    (root / "audit").mkdir()
    (root / "reports").mkdir()
    (root / "reports" / "projection-report.json").write_text(json.dumps({"run_id": "run-root", "digest_release_status": "not_released"}), encoding="utf-8")
    (root / "reports" / "exit-manifest.json").write_text(json.dumps({"run_id": "run-root", "digest_release_status": "not_released", "bundle_hash": "bundle-root"}), encoding="utf-8")
    (root / "reports" / "release-summary.json").write_text(json.dumps({
        "run_id": "run-root", "digest_release_status": "not_released", "completion": "complete",
        "quality_status": "passed", "delivery_status": "passed", "hard_failures": [], "unknowns": [],
        "confirmation_required": True, "agent_only": True,
        "reader_quality": {"positive_count": 17, "positive_passed": 17, "negative_count": 3, "negative_false_positives": 0, "page_count": 1, "claim_count": 1, "mode": "semantic", "replay": {"manifest_ref": "audit/run-manifest.json", "quality_ref": "reports/quality.json", "config_ref": "audit/config.json"}},
        "accuracy": {"title": {"rate": 0.9}, "ownership": {"rate": 0.9}},
        "machine_provenance": {"actor": "process:fixture", "model": "fixture-model", "rule": "fixture-rule", "seed": "fixture-seed", "snapshot_hash": "0" * 64, "question_hash": "0" * 64, "execution_mode": "real_semantic"},
    }), encoding="utf-8")
    (root / "audit" / "source-manifest.json").write_text(
        json.dumps({
            "run_id": "run-root",
            "source_count": 89,
            "entries": [
                {"source_id": "source-0", "source_uri": "raw://fixture.md", "content_fingerprint": "0" * 64},
                *[{"source_id": str(index), "source_uri": f"raw://fixture-{index}.md", "content_fingerprint": f"{index:064x}"} for index in range(1, 89)],
            ],
        }),
        encoding="utf-8",
    )
    for relative in ("README.md", "Home.md", "index.md", "log.md", "references/sources.md", "products/index.md"):
        path = root / "bundle" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n- digest_release_status: `not_released`\n" if relative in {"README.md", "log.md"} else "# fixture\n", encoding="utf-8")
    (root / "bundle" / "products" / "fixture.md").write_text(
        "---\n"
        "type: KnowledgeDigest Module or Capability\n"
        "title: Fixture\n"
        "digest_page_status: published\n"
            "digest_machine_pass: true\n"
            "digest_topic_id: topic-fixture\n"
            "generated:\n"
            "  by: fixture\n"
            "  at: '2026-08-13T00:00:00Z'\n"
        "digest_content_hash: '" + "0" * 64 + "'\n"
        "verified:\n"
        "  - event: source_hash_match\n"
        "    actor: process:knowledge-digest-source_hash_match-v1\n"
        "    detector_version: v1\n"
        "    content_hash: '" + "0" * 64 + "'\n"
            "    input_fingerprints: {source_inventory: '" + "0" * 64 + "', fixture_selection: '" + "0" * 64 + "', claim_records: {claim-0: '" + "0" * 64 + "'}, fixture_bytes: '" + "0" * 64 + "'}\n"
        "    evidence_ref: audit/trust-signals/fixture.json\n"
        "  - event: locator_resolved\n"
        "    actor: process:knowledge-digest-locator_resolved-v1\n"
        "    detector_version: v1\n"
        "    content_hash: '" + "0" * 64 + "'\n"
            "    input_fingerprints: {source_inventory: '" + "0" * 64 + "', fixture_selection: '" + "0" * 64 + "', claim_records: {claim-0: '" + "0" * 64 + "'}, fixture_bytes: '" + "0" * 64 + "'}\n"
        "    evidence_ref: audit/trust-signals/fixture.json\n"
        "sources:\n"
        "  - id: source-0\n"
        "    resource: raw://fixture.md\n"
        "    digest_content_fingerprint: '" + "0" * 64 + "'\n"
        "    digest_claims:\n"
        "      - claim_id: claim-0\n"
        "        target_path: products/fixture.md\n"
        "        source_uri: raw://fixture.md\n"
        "        content_fingerprint: '" + "0" * 64 + "'\n"
        "        fragment_locator: lines:1-1\n"
        "---\n\n# fixture\n",
        encoding="utf-8",
    )
    trust_events = [
        {"event": "source_hash_match", "actor": "process:knowledge-digest-source_hash_match-v1", "detector_version": "v1", "content_hash": "0" * 64, "input_fingerprints": {"source_inventory": "0" * 64, "fixture_selection": "0" * 64, "claim_records": {"claim-0": "0" * 64}, "fixture_bytes": "0" * 64}, "evidence_ref": "audit/trust-signals/fixture.json"},
        {"event": "locator_resolved", "actor": "process:knowledge-digest-locator_resolved-v1", "detector_version": "v1", "content_hash": "0" * 64, "input_fingerprints": {"source_inventory": "0" * 64, "fixture_selection": "0" * 64, "claim_records": {"claim-0": "0" * 64}, "fixture_bytes": "0" * 64}, "evidence_ref": "audit/trust-signals/fixture.json"},
    ]
    (root / "audit" / "trust-signals").mkdir(parents=True, exist_ok=True)
    (root / "audit" / "trust-signals" / "fixture.json").write_text(json.dumps({"schema_version": "reader-bundle-trust-signals.v1", "page_path": "products/fixture.md", "machine_pass": True, "content_hash": "0" * 64, "events": trust_events}) + "\n", encoding="utf-8")
    page_path = root / "bundle" / "products" / "fixture.md"
    page_frontmatter, page_body = parse_concept_document(page_path.read_text(encoding="utf-8"))
    page_hash = managed_content_hash(page_frontmatter, page_body)
    page_frontmatter["digest_content_hash"] = page_hash
    for event in trust_events:
        event["content_hash"] = page_hash
    page_path.write_text(serialize_concept_document(page_frontmatter, page_body), encoding="utf-8")
    (root / "audit" / "trust-signals" / "fixture.json").write_text(json.dumps({"schema_version": "reader-bundle-trust-signals.v1", "page_path": "products/fixture.md", "topic_id": page_frontmatter["digest_topic_id"], "generated": page_frontmatter["generated"], "machine_pass": True, "content_hash": page_hash, "events": trust_events}) + "\n", encoding="utf-8")
    replay = {"manifest_ref": "audit/run-manifest.json", "quality_ref": "reports/quality.json", "config_ref": "audit/config.json", "execution_mode": "real_semantic"}
    question_set = json.loads((ROOT / "config" / "task0-question-set.v1.json").read_text(encoding="utf-8"))
    records = [{"question_id": item["question_id"], "polarity": item["polarity"], "question": item["original_text"], "entry_path": item["entry_path"], "expected_topic_or_product": item["expected_topic_or_product"], "first_hit_page": "products/fixture.md" if item["polarity"] == "positive" else None, "answer_result": "hit" if item["polarity"] == "positive" else "no_match", "answer_complete": True, "boundary_version_accurate": True, "source_chain": "passed" if item["polarity"] == "positive" else "not_applicable", "source_recheck_result": "passed" if item["polarity"] == "positive" else "not_applicable", "failure_reason": None, "actor": "process:task3-reader-v1", "model": "fixture-model", "rule": "fixture-reader", "seed": "fixture-seed", "reader_input_hash": "0" * 64} for item in question_set["questions"]]
    question_hash = hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    provenance = {"actor": "process:task3-quality-v1", "model": "deterministic-policy", "rule": "task3-reader-quality-policy.v1", "seed": "fixture-seed", "snapshot_hash": "0" * 64, "question_hash": question_hash, "question_set_hash": question_set["question_set_hash"], "execution_mode": "real_semantic"}
    quality_summary = {"source_count": 89, "positive_count": 17, "positive_passed": 17, "negative_count": 3, "negative_false_positives": 0, "page_count": 1, "claim_count": 1, "mode": "semantic", "replay": replay}
    quality_report = {"schema_version": "task3-quality-result.v1", "run_id": "run-root", "status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "records": records, "summary": quality_summary, "title_check": {"passed": 9, "sample_size": 10, "rate": 0.9, "actor": "process:title", "rule": "title", "seed": "fixture-seed"}, "ownership_check": {"passed": 9, "sample_size": 10, "rate": 0.9, "actor": "process:ownership", "rule": "ownership", "seed": "fixture-seed"}, "provenance": provenance, "replay": replay, "scorecard_hash": "1" * 64, "mode": "semantic", "execution_mode": "real_semantic", "provider_calls": 20, "provider": "fixture-provider", "model": "fixture-model", "provider_receipt_ref": "audit/provider-receipt.json"}
    reader_quality = {**quality_summary, "run_id": "run-root", "scorecard_hash": quality_report["scorecard_hash"], "question_count": 20, "records_hash": question_hash, "provenance": provenance}
    (root / "reports" / "quality.json").write_text(json.dumps(quality_report) + "\n", encoding="utf-8")
    (root / "audit" / "run-manifest.json").write_text(json.dumps({"run_id": "run-root", "source_manifest_hash": "0" * 64, "execution_mode": "real_semantic"}) + "\n", encoding="utf-8")
    (root / "audit" / "config.json").write_text(json.dumps({"run_id": "run-root", "execution_mode": "real_semantic", "config_hash": "f" * 64, "provider": "fixture-provider", "model": "fixture-model", "endpoint": "https://fixture.invalid/v1", "budget": {"max_calls": 20}}) + "\n", encoding="utf-8")
    provider_calls = [{"provider": "fixture-provider", "model": "fixture-model", "status": "completed", "request_hash": f"{index + 1:064x}", "response_hash": f"{index + 101:064x}"} for index in range(20)]
    (root / "audit" / "provider-receipt.json").write_text(json.dumps({"run_id": "run-root", "execution_mode": "real_semantic", "provider_calls": 20, "provider": "fixture-provider", "model": "fixture-model", "config_hash": "f" * 64, "calls": provider_calls}) + "\n", encoding="utf-8")
    summary = json.loads((root / "reports" / "release-summary.json").read_text(encoding="utf-8")) if (root / "reports" / "release-summary.json").is_file() else {}
    summary.update({"run_id": "run-root", "digest_release_status": "not_released", "completion": "complete", "quality_status": "passed", "delivery_status": "passed", "hard_failures": [], "unknowns": [], "confirmation_required": True, "agent_only": True, "reader_quality": reader_quality, "accuracy": {"title": {"rate": 0.9}, "ownership": {"rate": 0.9}}, "machine_provenance": provenance})
    (root / "reports" / "release-summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")
    (root / "reports" / "exit-manifest.json").write_text(json.dumps({"run_id": "run-root", "digest_release_status": "not_released", "bundle_hash": module._task3_tree_hash(root / "bundle")}), encoding="utf-8")
    result = module.build_task3_comparison_report(task3_root=root, output_dir=tmp_path / "comparison")
    assert result["release_decision"] == "not_a_release_decision"
    assert result["sources"]["task3"]["availability"] == "unavailable"
    assert result["dimensions"]["saved_integrity"]["task3"]["comparability"] == "N/A"


def test_task3_comparison_marks_missing_candidate_unavailable(tmp_path: Path) -> None:
    module = _load_script("task2_publication_comparison_missing", ROOT / "scripts" / "task2_publication_comparison.py")
    root = tmp_path / "not-a-candidate"
    (root / "bundle").mkdir(parents=True)
    (root / "audit").mkdir()
    (root / "reports").mkdir()
    result = module.build_task3_comparison_report(task3_root=root)
    assert result["dimensions"]["saved_integrity"]["task3"]["comparability"] == "N/A"
    assert result["sources"]["task3"]["availability"] == "unavailable"


def test_task3_comparison_does_not_use_task3_parser_for_companybrain_shape(tmp_path: Path) -> None:
    module = _load_script("task2_publication_comparison_companybrain_shape", ROOT / "scripts" / "task2_publication_comparison.py")
    root = tmp_path / "companybrain"
    (root / "bundle").mkdir(parents=True)
    (root / "audit").mkdir()
    (root / "reports").mkdir()
    result = module.build_task3_comparison_report(companybrain_root=root)
    assert result["dimensions"]["machine_quality"]["companybrain"]["comparability"] == "N/A"
    assert result["dimensions"]["trust_freshness"]["companybrain"]["comparability"] == "N/A"


def test_task3_entrypoint_orders_existing_seams_and_hands_off_real_not_released_state(tmp_path: Path) -> None:
    script_path = ROOT / "scripts" / "task3_full_release.py"
    assert script_path.is_file()
    module = _load_script("task3_full_release", script_path)
    runner = getattr(module, "run_task3_full_release", None)
    assert callable(runner)
    record = _case()["entrypoint"]
    calls: list[str] = []

    def step(name: str, status: str = "passed") -> dict[str, object]:
        calls.append(name)
        return {"status": status, "run_id": "run-task3-fixture", "evidence_ref": f"{name}.json"}

    steps = {name: (lambda name=name: step(name)) for name in record["expected_sequence"]}
    steps["confirmation"] = lambda: step("confirmation", "confirmed")
    steps["readback"] = lambda: step("readback", "not_released")
    result = runner(
        steps=steps,
        output_dir=tmp_path,
        deferred_items=record["deferred"],
        risk_items=[{"id": "RISK-001", "status": "open"}],
    )

    assert calls == record["expected_sequence"]
    assert result["status"] == record["expected_status"]
    assert result["handoff"]["status"] == "not_released"
    assert result["handoff"]["deferred_items"] == record["deferred"]
    assert result["handoff"]["risk_items"]
    assert "human_reviewed" not in json.dumps(result)
    assert (tmp_path / "closeout-handoff.json").is_file()


def test_task3_entrypoint_stops_after_a_failed_step(tmp_path: Path) -> None:
    module = _load_script("task3_full_release_fail_fast", ROOT / "scripts" / "task3_full_release.py")
    calls: list[str] = []

    def step(name: str, status: str = "passed") -> dict[str, object]:
        calls.append(name)
        return {"status": status}

    steps = {name: (lambda name=name: step(name)) for name in ["freeze", "candidate", "quality", "comparison", "summary", "confirmation", "readback"]}
    steps["quality"] = lambda: step("quality", "failed")
    result = module.run_task3_full_release(steps=steps, output_dir=tmp_path)
    assert calls == ["freeze", "candidate", "quality"]
    assert result["status"] == "not_released"
    assert result["stopped_at"] == "quality"
    assert result["steps"]["comparison"]["status"] == "not_run"


def test_task3_entrypoint_cli_replays_captured_adapter_facts(tmp_path: Path) -> None:
    module = _load_script("task3_full_release_cli", ROOT / "scripts" / "task3_full_release.py")
    captured = tmp_path / "steps.json"
    captured.write_text(json.dumps({"steps": {name: {"status": "not_released" if name == "readback" else "confirmed" if name == "confirmation" else "passed"} for name in module.TASK3_SEQUENCE}}), encoding="utf-8")
    result = module.run_task3_full_release_from_json(captured, output_dir=tmp_path / "out")
    assert result["sequence"] == list(module.TASK3_SEQUENCE)
    assert result["status"] == "not_released"
    assert result["steps"]["readback"]["status"] == "not_released"
    assert result["handoff"]["status"] == "not_released"
    assert result["handoff"]["actual_result"]["status"] == "not_released"
    assert (tmp_path / "out" / "closeout-handoff.json").is_file()


def test_task3_entrypoint_replay_downgrade_is_written_once_without_released_fields(tmp_path: Path) -> None:
    module = _load_script("task3_full_release_replay_downgrade", ROOT / "scripts" / "task3_full_release.py")
    captured = tmp_path / "steps-released.json"
    captured.write_text(json.dumps({"steps": {name: {"status": "released" if name == "readback" else "confirmed" if name == "confirmation" else "passed", "nested": {"status": "released"}} for name in module.TASK3_SEQUENCE}}), encoding="utf-8")
    output = tmp_path / "out"
    result = module.run_task3_full_release_from_json(captured, output_dir=output)
    saved = json.loads((output / "closeout-handoff.json").read_text(encoding="utf-8"))
    assert result["status"] == "not_released"
    assert saved["status"] == "not_released"
    assert saved["actual_result"]["status"] == "not_released"
    assert saved["actual_result"]["steps"]["readback"]["status"] == "not_released"
    assert saved["actual_result"]["steps"]["readback"]["nested"]["status"] == "not_released"
