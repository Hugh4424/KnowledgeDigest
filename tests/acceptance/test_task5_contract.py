from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from knowledge_digest.compiler import _validate_workflowhub_successor
from knowledge_digest.task5_runtime import (
    Task5RuntimeError,
    _formal_run_result,
    _identity_from_handoff,
    _load_runtime_authority,
    _slice_source_selection,
    _validate_source_manifest,
    _write_host_observation,
    _write_host_run_receipt,
)


PROJECT_ROOT = Path(__file__).parents[2]
RAW_ROOT = Path("/Users/Hugh/Downloads/confluence 原始数据")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _sha(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def test_runtime_authority_rehashes_the_frozen_included_and_excluded_sets() -> None:
    identity = _load_runtime_authority(PROJECT_ROOT / "config/task5-runtime-authority-map-v1.json")

    assert identity["status"] == "passed"
    assert identity["runtime_contract_id"] == "task5-reader-quality-provider-v2"
    assert len(identity["included_keys"]) == 17
    assert len(identity["excluded_paths"]) == 5
    assert identity["derived_runtime_contract_hash"]


def test_runtime_authority_rejects_actual_hash_drift(tmp_path: Path) -> None:
    source = PROJECT_ROOT / "config/task5-runtime-authority-map-v1.json"
    value = json.loads(source.read_text(encoding="utf-8"))
    for item in value["authorities"]:
        source_path = PROJECT_ROOT / str(item["path"])
        target_path = tmp_path / str(item["path"])
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    value["authorities"][0]["actual_sha256"] = "0" * 64
    map_path = tmp_path / "config/task5-runtime-authority-map-v1.json"
    map_path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(Task5RuntimeError, match="authority actual hash mismatch"):
        _load_runtime_authority(map_path)


def test_real_source_manifest_and_slice_derive_the_frozen_contract_closure() -> None:
    manifest = PROJECT_ROOT / "config/task5-source-page-manifest-v2.json"
    source_identity = _validate_source_manifest(RAW_ROOT, manifest)
    slice_identity = _slice_source_selection(
        PROJECT_ROOT / "config/task5-slice-cases-v1.json",
        manifest,
    )

    assert source_identity["source_count"] == 89
    assert source_identity["known_empty_paths"] == ["emm for android /AE - AirViewer厂商管理.md"]
    assert slice_identity["case_count"] == 11
    assert slice_identity["source_count"] == 27
    assert len(slice_identity["source_paths"]) == len(set(slice_identity["source_paths"]))


def test_slice_contract_rejects_unknown_source_path(tmp_path: Path) -> None:
    slice_path = PROJECT_ROOT / "config/task5-slice-cases-v1.json"
    value = json.loads(slice_path.read_text(encoding="utf-8"))
    value["cases"][0]["source_paths"].append("unknown/product.md")
    changed = tmp_path / "slice.json"
    changed.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(Task5RuntimeError, match="slice source is not in frozen source manifest"):
        _slice_source_selection(changed, PROJECT_ROOT / "config/task5-source-page-manifest-v2.json")


def test_workflowhub_successor_rejects_noncanonical_bytes_before_nested_refs(tmp_path: Path) -> None:
    fields = (
        "schema_version", "handoff_kind", "task_id", "project_name", "stage",
        "review_kind", "handoff_ref", "handoff_sha256", "parent_design_review",
        "implementation_review", "current", "runtime_contract", "writer_attestation",
    )
    handoff = {field: {} for field in fields}
    handoff_path = tmp_path / "task" / "quality" / "evidence" / "task5" / "workflowhub-implementation-handoff.json"
    handoff_path.parent.mkdir(parents=True)

    with pytest.raises(ValueError, match="not canonical UTF-8 JSON"):
        _validate_workflowhub_successor(
            handoff_path,
            handoff,
            b"{}\n",
            {},
            b"{}",
            {},
            b"{}",
        )


def test_workflowhub_successor_rejects_top_level_schema_expansion(tmp_path: Path) -> None:
    handoff = {
        "schema_version": "workflowhub-implementation-successor.v1",
        "handoff_kind": "implementation",
        "task_id": "task5-reader-quality-compiler-redesign",
        "project_name": "KnowledgeDigest",
        "stage": "build-code",
        "review_kind": "mini_task.implementation",
        "handoff_ref": "quality/evidence/task5/workflowhub-implementation-handoff.json",
        "handoff_sha256": "0" * 64,
        "parent_design_review": {},
        "implementation_review": {},
        "current": {},
        "runtime_contract": {},
        "writer_attestation": {},
        "unexpected": True,
    }
    handoff_path = tmp_path / "task" / "quality" / "evidence" / "task5" / "workflowhub-implementation-handoff.json"
    handoff_path.parent.mkdir(parents=True)

    with pytest.raises(ValueError, match="unexpected: unexpected"):
        _validate_workflowhub_successor(
            handoff_path,
            handoff,
            b"{}\n",
            {},
            b"{}",
            {},
            b"{}",
        )


def test_workflowhub_successor_allows_null_design_advisory(tmp_path: Path) -> None:
    task_root = tmp_path / "task"
    handoff_path = task_root / "quality" / "evidence" / "task5" / "workflowhub-implementation-handoff.json"
    handoff_path.parent.mkdir(parents=True)
    evidence_root = task_root / "quality" / "evidence" / "task5" / "implementation"
    evidence_root.mkdir(parents=True)

    def write_ref(name: str, data: bytes) -> tuple[str, str]:
        path = evidence_root / name
        path.write_bytes(data)
        return f"quality/evidence/task5/implementation/{name}", _sha(data)

    result_ref, result_sha = write_ref("review-result.json", b"implementation-result")
    attempt_ref, attempt_sha = write_ref("attempt.json", b"implementation-attempt")
    report_ref, report_sha = write_ref("report.json", b"implementation-report")
    finding_ref, finding_sha = write_ref("finding-dispositions.json", b"finding-dispositions")
    packet_raw = b"m401-packet"
    receipt_raw = b"m401-r-receipt"
    # WorkflowHub owns a Git tree OID; the local host currently emits its
    # 40-character form. Task5 file-list hashes remain 64-character SHA-256.
    snapshot_tree = "a" * 40
    material_id = "b" * 64
    packet = {"snapshot_tree": snapshot_tree, "material_id": material_id}
    receipt = {"m401_packet_sha256": _sha(packet_raw)}

    def attestation(writer: str) -> dict[str, object]:
        value: dict[str, object] = {
            "writer": writer,
            "adapter": "workflowhub-authenticated-adapter",
            "authenticated": True,
            "attestation_sha256": "",
        }
        value["attestation_sha256"] = _sha(_canonical({key: item for key, item in value.items() if key != "attestation_sha256"}))
        return value

    implementation = {
        "review_kind": "mini_task.implementation",
        "result_ref": result_ref,
        "result_sha256": result_sha,
        "attempt_ref": attempt_ref,
        "attempt_sha256": attempt_sha,
        "report_ref": report_ref,
        "report_sha256": report_sha,
        "outcome": "available",
        "terminal_status": "semantic",
        "terminal_clean": True,
        "finding_dispositions_ref": finding_ref,
        "finding_dispositions_sha256": finding_sha,
        "all_findings_disposed": True,
        "m401_packet_sha256": _sha(packet_raw),
    }
    current = {
        "task_id": "task5-reader-quality-compiler-redesign",
        "project_name": "KnowledgeDigest",
        "stage": "build-code",
        "snapshot_tree": snapshot_tree,
        "material_id": material_id,
        "worktree": str(tmp_path / "worktree"),
    }
    runtime = {
        "runtime_contract_id": "rt-test",
        "runtime_contract_hash": "c" * 64,
        "semantic_contract_id": "semantic-test",
        "semantic_contract_hash": "d" * 64,
        "m401_packet_ref": "quality/evidence/task5/M401-evidence-packet.json",
        "m401_packet_sha256": _sha(packet_raw),
        "m401_r_receipt_ref": "quality/evidence/task5/M401-R-review-receipt.json",
        "m401_r_receipt_sha256": _sha(receipt_raw),
    }
    handoff: dict[str, object] = {
        "schema_version": "workflowhub-implementation-successor.v1",
        "handoff_kind": "implementation",
        "task_id": "task5-reader-quality-compiler-redesign",
        "project_name": "KnowledgeDigest",
        "stage": "build-code",
        "review_kind": "mini_task.implementation",
        "handoff_ref": "quality/evidence/task5/workflowhub-implementation-handoff.json",
        "handoff_sha256": "",
        "parent_design_review": None,
        "implementation_review": implementation,
        "current": current,
        "runtime_contract": runtime,
        "writer_attestation": attestation("workflowhub-test-writer"),
    }
    handoff["handoff_sha256"] = _sha(_canonical({key: item for key, item in handoff.items() if key != "handoff_sha256"}))

    _validate_workflowhub_successor(
        handoff_path,
        handoff,
        _canonical(handoff),
        packet,
        packet_raw,
        receipt,
        receipt_raw,
    )


def test_runtime_accepts_implementation_handoff_without_design_review(tmp_path: Path, monkeypatch) -> None:
    import knowledge_digest.task5_runtime as runtime

    monkeypatch.setattr(runtime, "_validate_review_identity", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "_read_managed_ref", lambda *args, **kwargs: (Path("/tmp/ref"), {}))
    handoff = {
        "schema_version": "workflowhub-implementation-successor.v1",
        "handoff_kind": "implementation",
        "task_id": "task5-reader-quality-compiler-redesign",
        "stage": "build-code",
        "review_kind": "mini_task.implementation",
        "handoff_ref": "quality/evidence/task5/workflowhub-implementation-handoff.json",
        "handoff_sha256": "",
        "parent_design_review": None,
        "implementation_review": {"outcome": "available", "terminal_status": "semantic", "terminal_clean": True, "all_findings_disposed": True},
        "current": {
            "task_id": "task5-reader-quality-compiler-redesign",
            "snapshot_tree": "a" * 64,
            "material_id": "b" * 64,
        },
        "runtime_contract": {
            "runtime_contract_id": "runtime",
            "runtime_contract_hash": "c" * 64,
            "semantic_contract_id": "semantic",
            "semantic_contract_hash": "d" * 64,
            "m401_packet_ref": "quality/evidence/task5/M401-evidence-packet.json",
            "m401_packet_sha256": "e" * 64,
            "m401_r_receipt_ref": "quality/evidence/task5/M401-R-review-receipt.json",
            "m401_r_receipt_sha256": "f" * 64,
        },
        "writer_attestation": {"authenticated": True},
    }
    handoff["handoff_sha256"] = _sha(_canonical({key: item for key, item in handoff.items() if key != "handoff_sha256"}))
    path = tmp_path / "workflowhub-implementation-handoff.json"
    path.write_bytes(_canonical(handoff))

    identity = _identity_from_handoff(path)

    assert identity["parent_design_review"] is None
    assert identity["implementation_review"]["terminal_clean"] is True


def _observation_fixture() -> dict[str, object]:
    fields = {
        "case_id", "projection_id", "dimension_id", "status", "score",
        "source_refs", "visible_ref", "audit_ref", "gap_ref", "kd_ref",
    }
    rows = []
    for case_index in range(12):
        for dimension_index in range(5):
            row = {
                "case_id": f"case-{case_index:02d}",
                "projection_id": f"projection-{case_index:02d}",
                "dimension_id": f"dimension-{dimension_index:02d}",
                "status": "absent",
                "score": None,
                "source_refs": [],
                "visible_ref": None,
                "audit_ref": None,
                "gap_ref": None,
                "kd_ref": None,
            }
            assert set(row) == fields
            rows.append(row)
    rows.sort(key=lambda value: (value["case_id"], value["projection_id"], value["dimension_id"]))
    return {
        "run_id": "compiler-run",
        "source_manifest_sha256": "1" * 64,
        "companybrain_snapshot_id": "cb-test",
        "companybrain_tree_sha256": "2" * 64,
        "rows": rows,
    }


def test_host_observation_is_immutable_and_hash_bound(tmp_path: Path) -> None:
    observation = _observation_fixture()
    observation["observation_sha256"] = _sha(_canonical(observation))

    path, digest = _write_host_observation(
        observation,
        evidence_root=tmp_path / "evidence",
        attempt_id="m402-test",
        run_id="compiler-run",
        source_manifest_sha256="1" * 64,
    )

    value = json.loads(path.read_text(encoding="utf-8"))
    assert path == tmp_path / "evidence/actual-run/attempts/m402-test/companybrain-observation.json"
    assert digest == _sha(path.read_bytes())
    assert set(value) == {
        "run_id", "source_manifest_sha256", "companybrain_snapshot_id",
        "companybrain_tree_sha256", "rows", "observation_sha256",
    }
    with pytest.raises(FileExistsError):
        _write_host_observation(
            observation,
            evidence_root=tmp_path / "evidence",
            attempt_id="m402-test",
            run_id="compiler-run",
            source_manifest_sha256="1" * 64,
        )


def test_host_run_receipt_binds_inputs_without_copying_credentials(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    companybrain = tmp_path / "companybrain"
    output = tmp_path / "Downloads" / "run"
    provider = tmp_path / "config.json"
    source_manifest = tmp_path / "source-manifest.json"
    public_receipt = output / "bundle/_audit/run-result.json"
    for directory in (raw, companybrain, output, public_receipt.parent):
        directory.mkdir(parents=True, exist_ok=True)
    provider.write_text(json.dumps({"api_key": "private-test-value"}), encoding="utf-8")
    source_manifest.write_text("source manifest", encoding="utf-8")
    public_receipt.write_text("public run result", encoding="utf-8")

    path, digest = _write_host_run_receipt(
        evidence_root=tmp_path / "evidence",
        attempt_id="m402-test",
        run_id="formal-run",
        raw=raw,
        companybrain=companybrain,
        output=output,
        provider_config=provider,
        source_manifest=source_manifest,
        public_receipt=public_receipt,
        terminal_status="released",
    )

    value = json.loads(path.read_text(encoding="utf-8"))
    assert digest == _sha(path.read_bytes())
    assert value["schema_version"] == "task5-host-run-receipt.v1"
    assert value["terminal_status"] == "released"
    assert value["provider_config_ref"]["sha256"] == _sha(provider.read_bytes())
    assert value["public_receipt_sha256"] == _sha(public_receipt.read_bytes())
    assert "private-test-value" not in path.read_text(encoding="utf-8")


def test_formal_run_result_projects_nested_workflowhub_identity(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "README.md").write_text("reader", encoding="utf-8")
    provider = tmp_path / "provider.json"
    source_manifest = tmp_path / "source-manifest.json"
    quality_cases = tmp_path / "quality-cases.json"
    slice_cases = tmp_path / "slice-cases.json"
    provider.write_text("{}", encoding="utf-8")
    source_manifest.write_text("{}", encoding="utf-8")
    quality_cases.write_text("{}", encoding="utf-8")
    slice_cases.write_text("{}", encoding="utf-8")
    quality_artifact = tmp_path / "quality-result.json"
    quality_artifact.write_text("candidate", encoding="utf-8")
    handoff = {
        "task_id": "task5-reader-quality-compiler-redesign",
        "stage": "build-code",
        "review_kind": "mini_task.implementation",
        "handoff_ref": "quality/evidence/task5/workflowhub-implementation-handoff.json",
        "handoff_sha256": "a" * 64,
        "implementation_review": {
            "attempt_ref": "quality/reviews/attempt.json",
            "result_ref": "quality/reviews/result.json",
            "result_sha256": "b" * 64,
            "report_ref": "quality/reviews/report.json",
            "outcome": "available",
            "terminal_status": "semantic",
            "terminal_clean": True,
        },
        "current": {"snapshot_tree": "c" * 64, "material_id": "d" * 64},
        "runtime_contract": {
            "runtime_contract_id": "runtime",
            "runtime_contract_hash": "e" * 64,
            "semantic_contract_hash": "f" * 64,
        },
    }
    result = _formal_run_result(
        run={"provider_calls": {"llm": 1, "embedding": 1}},
        task_id="task5-reader-quality-compiler-redesign",
        run_id="formal-run",
        handoff=handoff,
        provider_identity={},
        source_manifest=source_manifest,
        quality_cases=quality_cases,
        slice_cases=slice_cases,
        output_bundle=bundle,
        quality_result=None,
        quality_result_ref="actual-run/quality-result.json",
        quality_result_sha256=_sha(quality_artifact.read_bytes()),
        snd_verifier={"status": "passed", "canonical_sha256": "1" * 64},
        surface_qa={"status": "passed"},
        authority_identity={"map_ref": "config/task5-runtime-authority-map-v1.json"},
        provider_config=provider,
        calibration_manifest=None,
        calibration_artifact=None,
        companybrain_host_snapshot_sha256="2" * 64,
        outcome="success",
        publication_status="released",
        reason_code="all_release_predicates_passed",
        exit_code=0,
        phase_results={},
        failure_evidence_path=None,
    )

    identity = result["workflowhub_identity"]
    assert identity["review_attempt_ref"] == "quality/reviews/attempt.json"
    assert identity["review_result_ref"] == "quality/reviews/result.json"
    assert identity["review_report_ref"] == "quality/reviews/report.json"
    assert identity["contract_id"] == "runtime"
    assert identity["semantic_hash"] == "f" * 64
    assert identity["snapshot_tree"] == "c" * 64
    assert result["artifact_manifest"]["quality_result"] == {
        "ref": "actual-run/quality-result.json",
        "sha256": _sha(quality_artifact.read_bytes()),
    }
