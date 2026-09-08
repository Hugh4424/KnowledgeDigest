from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from knowledge_digest.compiler import _validate_workflowhub_successor
from knowledge_digest.task5_runtime import _validate_m401_r_receipt
from knowledge_digest.m401_r_adapter import M401RAdapterError, promote_m401_r


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: object) -> bytes:
    data = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def write_workflowhub_json(path: Path, value: object) -> bytes:
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def make_packet(root: Path) -> tuple[Path, Path, dict]:
    packet = {
        "schema_version": "task5-m401-evidence-packet.v1",
        "gate": "M401",
        "status": "passed",
        "pre_m402_readiness": True,
        "snapshot_tree": "a" * 40,
        "material_id": "b" * 64,
        "run_root_ref": "run-root/bundle",
        "run_root_sha256": "c" * 64,
    }
    packet["canonical_sha256"] = sha(canonical({**packet}))
    packet_path = root / "quality/evidence/task5/repair-gates/attempts/m401-test/M401/M401-evidence-packet.json"
    packet_raw = write_json(packet_path, packet)
    receipt = {
        "schema_version": "task5-m401-attempt-receipt.v1",
        "gate": "M401",
        "attempt_id": "m401-test",
        "command": ["digest", "--gate", "M401"],
        "command_sha256": sha(canonical(["digest", "--gate", "M401"])),
        "fixture_bundle_ref": "fixture/bundle",
        "fixture_bundle_sha256": "d" * 64,
        "fixture_manifest_sha256": "e" * 64,
        "run_root_ref": "run-root",
        "run_root_sha256": packet["run_root_sha256"],
        "packet_ref": "M401-evidence-packet.json",
        "packet_sha256": sha(packet_raw),
        "snapshot_tree": packet["snapshot_tree"],
        "material_id": packet["material_id"],
        "exit_code": 0,
        "status": "passed",
        "reason_code": "NONE",
    }
    receipt_path = packet_path.parent / "attempt-receipt.json"
    write_json(receipt_path, receipt)
    inverse = b"fixture inverse patch\n"
    (packet_path.parent / "inverse.patch").write_bytes(inverse)
    write_json(
        packet_path.parent / "attempt.json",
        {
            "schema_version": "task5-repair-gate-attempt.v1",
            "gate": "M401",
            "attempt_id": "m401-test",
            "attempt_seq": 1,
            "material_id": packet["material_id"],
            "command": receipt["command"],
            "command_sha256": receipt["command_sha256"],
            "before_snapshot": "f" * 64,
            "after_snapshot": packet["run_root_sha256"],
            "changed_paths": [],
            "before_sha256": "f" * 64,
            "after_sha256": packet["run_root_sha256"],
            "patch_sha256": "0" * 64,
            "inverse_patch_ref": "inverse.patch",
            "inverse_patch_sha256": sha(inverse),
            "inverse_base_after_snapshot": packet["run_root_sha256"],
            "run_root_ref": "run-root",
            "exit_code": 0,
            "status": "passed",
            "reason_code": "NONE",
        },
    )
    return packet_path.parent.parent, packet_path, packet


def make_review(root: Path, packet: dict, *, finding: bool = False) -> tuple[Path, Path, Path, Path]:
    finding_value = {
        "id": "F-test",
        "provider": "fixture/provider",
        "severity": "minor",
        "path": "materials/spec.md",
        "issue": "test finding",
    }
    result = {
        "version": "wh-review-result.v1",
        "task_id": "task5-reader-quality-compiler-redesign",
        "stage": "build-code",
        "review_kind": "mini_task.implementation",
        "attempt_ref": "quality/reviews/attempts/review-test/attempt.json",
        "report_ref": "quality/reviews/reports/review-test.md",
        "snapshot_tree": packet["snapshot_tree"],
        "material_id": packet["material_id"],
        "semantic_projection": {
            "projection_version": "wh-review-semantic-projection.v1",
            "surface": "mini-task/implementation",
            "contract_id": "mini-task-implementation",
            "contract_hash": "c" * 64,
            "semantic_hash": "d" * 64,
        },
        "findings": [finding_value] if finding else [],
        "provider_results": [{"provider": "fixture/provider", "output": {"findings": [finding_value] if finding else []}}],
    }
    attempt = {
        "version": "wh-review-attempt.v1",
        "attempt_id": "review-test",
        "task_id": result["task_id"],
        "stage": "build-code",
        "review_kind": result["review_kind"],
        "snapshot_tree": packet["snapshot_tree"],
        "material_id": packet["material_id"],
        "semantic_projection": result["semantic_projection"],
        "provider_attempts": [{"provider": "fixture/provider", "status": "completed", "error": None, "output_ref": "quality/reviews/attempts/review-test/providers/fixture.output.json"}],
        "terminal_status": "semantic",
        "error": None,
    }
    result_path = root / "quality/reviews/results/review-test.json"
    attempt_path = root / "quality/reviews/attempts/review-test/attempt.json"
    report_path = root / "quality/reviews/attempts/review-test/report.md"
    disposition_path = root / "quality/reviews/attempts/review-test/dispositions.json"
    write_workflowhub_json(result_path, result)
    write_workflowhub_json(attempt_path, attempt)
    provider_content = json.dumps({"findings": [finding_value] if finding else []}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    write_workflowhub_json(
        root / "quality/reviews/attempts/review-test/providers/fixture.output.json",
        {
            "schema_version": "wh-review-provider-output.v1",
            "task_id": result["task_id"],
            "stage": result["stage"],
            "attempt_id": attempt["attempt_id"],
            "provider": "fixture/provider",
            "content": provider_content,
            "content_hash": sha(provider_content.encode()),
        },
    )
    report_path = root / "quality/reviews/reports/review-test.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("review report\n", encoding="utf-8")
    write_json(disposition_path, [{"finding_id": "F-test", "status": "rejected_invalid"}] if finding else [])
    return result_path, attempt_path, report_path, disposition_path


def test_m401_r_promotes_current_authenticated_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet)
    config = Path(__file__).parents[2] / "config"
    # The adapter derives the current authority from the task root.
    for path in config.glob("task5-*.json"):
        target = task_root / "config" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    outcome = promote_m401_r(
        task_root=task_root,
        m401_attempt=attempt_root,
        review_result=result,
        review_attempt=attempt,
        review_report=report,
        finding_dispositions=dispositions,
    )
    assert outcome["attempt_id"] == "review-test"
    receipt = task_root / "quality/evidence/task5/M401-R-review-receipt.json"
    handoff = task_root / "quality/evidence/task5/workflowhub-implementation-handoff.json"
    assert receipt.is_file()
    assert handoff.is_file()
    attempt_dir = task_root / "quality/evidence/task5/repair-gates/attempts/review-test/M401-R"
    assert {path.name for path in attempt_dir.iterdir()} == {
        "review-result.json",
        "M401-R-review-receipt.json",
        "attempt.json",
        "inverse.patch",
    }
    attempt_record = json.loads((attempt_dir / "attempt.json").read_text())
    assert attempt_record["schema_version"] == "task5-repair-gate-attempt.v1"
    assert attempt_record["gate"] == "M401-R"
    assert attempt_record["run_root_ref"] is None
    assert attempt_record["status"] == "passed"
    assert attempt_record["inverse_patch_sha256"] == sha((attempt_dir / "inverse.patch").read_bytes())
    local_result = json.loads((attempt_dir / "review-result.json").read_text())
    assert local_result["schema_version"] == "workflowhub-mini-task-review-result.v1"
    assert local_result["review_attempt_id"] == "review-test"
    assert local_result["review_outcome"] == "available"
    assert local_result["terminal_status"] == "semantic"
    assert local_result["terminal_clean"] is True
    assert local_result["finding_dispositions"] == []
    assert local_result["contract_id"] == "mini-task-implementation"
    assert local_result["contract_hash"] == "c" * 64
    assert local_result["semantic_hash"] == "d" * 64
    receipt_value = json.loads(receipt.read_text())
    assert receipt_value["review_result_sha256"] == sha((attempt_dir / "review-result.json").read_bytes())
    value = json.loads(handoff.read_text())
    _validate_m401_r_receipt(receipt)
    _validate_workflowhub_successor(
        handoff,
        value,
        handoff.read_bytes(),
        json.loads((attempt_root / "M401/M401-evidence-packet.json").read_text()),
        (attempt_root / "M401/M401-evidence-packet.json").read_bytes(),
        json.loads(receipt.read_text()),
        receipt.read_bytes(),
    )


def test_m401_r_rejects_unresolved_findings_without_promotion(tmp_path: Path) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet, finding=True)
    dispositions.write_bytes(canonical([]))
    config = Path(__file__).parents[2] / "config"
    for path in config.glob("task5-*.json"):
        target = task_root / "config" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    with pytest.raises(M401RAdapterError, match="finding dispositions are incomplete"):
        promote_m401_r(
            task_root=task_root,
            m401_attempt=attempt_root,
            review_result=result,
            review_attempt=attempt,
            review_report=report,
            finding_dispositions=dispositions,
        )
    assert not (task_root / "quality/evidence/task5/M401-R-review-receipt.json").exists()


def test_m401_r_rejects_review_bound_to_stale_snapshot(tmp_path: Path) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet)
    stale = json.loads(result.read_text())
    stale["snapshot_tree"] = "z" * 40
    result.write_bytes((json.dumps(stale, ensure_ascii=False, indent=2) + "\n").encode())
    with pytest.raises(M401RAdapterError, match="current M401 snapshot/material"):
        promote_m401_r(
            task_root=task_root,
            m401_attempt=attempt_root,
            review_result=result,
            review_attempt=attempt,
            review_report=report,
            finding_dispositions=dispositions,
        )
    assert not list((task_root / "quality/evidence/task5/repair-gates/attempts").glob("*/M401-R"))


def test_m401_r_rejects_review_without_authenticated_contract_identity(tmp_path: Path) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet)
    value = json.loads(result.read_text())
    value.pop("semantic_projection")
    write_workflowhub_json(result, value)
    with pytest.raises(M401RAdapterError, match="contract identity"):
        promote_m401_r(
            task_root=task_root,
            m401_attempt=attempt_root,
            review_result=result,
            review_attempt=attempt,
            review_report=report,
            finding_dispositions=dispositions,
        )
    assert not list((task_root / "quality/evidence/task5/repair-gates/attempts").glob("*/M401-R"))


def test_m401_r_rejects_unverifiable_provider_output(tmp_path: Path) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet)
    provider_output = task_root / "quality/reviews/attempts/review-test/providers/fixture.output.json"
    value = json.loads(provider_output.read_text())
    value["content_hash"] = "0" * 64
    write_workflowhub_json(provider_output, value)
    with pytest.raises(M401RAdapterError, match="provider output provenance"):
        promote_m401_r(
            task_root=task_root,
            m401_attempt=attempt_root,
            review_result=result,
            review_attempt=attempt,
            review_report=report,
            finding_dispositions=dispositions,
        )
    assert not list((task_root / "quality/evidence/task5/repair-gates/attempts").glob("*/M401-R"))


def test_m401_r_rejects_provider_attempt_that_is_not_completed(tmp_path: Path) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet)
    value = json.loads(attempt.read_text())
    value["provider_attempts"][0]["status"] = "failed"
    value["provider_attempts"][0]["error"] = {"code": "PROVIDER_UNAVAILABLE"}
    attempt.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    with pytest.raises(M401RAdapterError, match="provider results are incomplete"):
        promote_m401_r(
            task_root=task_root,
            m401_attempt=attempt_root,
            review_result=result,
            review_attempt=attempt,
            review_report=report,
            finding_dispositions=dispositions,
        )
    assert not list((task_root / "quality/evidence/task5/repair-gates/attempts").glob("*/M401-R"))


def test_m401_r_does_not_overwrite_conflicting_promotion(tmp_path: Path) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet)
    config = Path(__file__).parents[2] / "config"
    for path in config.glob("task5-*.json"):
        target = task_root / "config" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    promoted_packet = task_root / "quality/evidence/task5/M401-evidence-packet.json"
    promoted_packet.parent.mkdir(parents=True, exist_ok=True)
    promoted_packet.write_bytes(b"stale promotion\n")
    with pytest.raises(M401RAdapterError, match="existing promotion has different bytes"):
        promote_m401_r(
            task_root=task_root,
            m401_attempt=attempt_root,
            review_result=result,
            review_attempt=attempt,
            review_report=report,
            finding_dispositions=dispositions,
        )
    assert promoted_packet.read_bytes() == b"stale promotion\n"
    assert not (task_root / "quality/evidence/task5/M401-R-review-receipt.json").exists()


def test_m401_r_can_resume_existing_attempt_and_replace_stale_promotion(
    tmp_path: Path,
) -> None:
    task_root = tmp_path / "task"
    attempt_root, _, packet = make_packet(task_root)
    result, attempt, report, dispositions = make_review(task_root, packet)
    config = Path(__file__).parents[2] / "config"
    for path in config.glob("task5-*.json"):
        target = task_root / "config" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())

    promote_m401_r(
        task_root=task_root,
        m401_attempt=attempt_root,
        review_result=result,
        review_attempt=attempt,
        review_report=report,
        finding_dispositions=dispositions,
    )
    promoted_packet = task_root / "quality/evidence/task5/M401-evidence-packet.json"
    promoted_packet.write_bytes(b"stale v38 promotion\n")

    with pytest.raises(M401RAdapterError, match="existing promotion has different bytes"):
        promote_m401_r(
            task_root=task_root,
            m401_attempt=attempt_root,
            review_result=result,
            review_attempt=attempt,
            review_report=report,
            finding_dispositions=dispositions,
            resume_existing_attempt=True,
        )

    outcome = promote_m401_r(
        task_root=task_root,
        m401_attempt=attempt_root,
        review_result=result,
        review_attempt=attempt,
        review_report=report,
        finding_dispositions=dispositions,
        resume_existing_attempt=True,
        replace_existing_promotion=True,
    )
    assert outcome["attempt_id"] == "review-test"
    assert promoted_packet.read_bytes() == (attempt_root / "M401/M401-evidence-packet.json").read_bytes()
    assert (task_root / "quality/evidence/task5/M401-R-review-receipt.json").is_file()
    assert (task_root / "quality/evidence/task5/workflowhub-implementation-handoff.json").is_file()
