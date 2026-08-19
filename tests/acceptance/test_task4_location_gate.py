from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

_PILOT_SPEC = importlib.util.spec_from_file_location("task4_location_pilot", Path("scripts/task4_location_pilot.py"))
assert _PILOT_SPEC is not None and _PILOT_SPEC.loader is not None
pilot = importlib.util.module_from_spec(_PILOT_SPEC)
_PILOT_SPEC.loader.exec_module(pilot)


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reader_package(root: Path, *, target: str, prefix: str = "products/GoInsight") -> None:
    _write(root, "Home.md", "# Home\n\n- [GoInsight](products/GoInsight/index.md)\n")
    _write(root, "products/GoInsight/index.md", "# GoInsight\n\n- [字段与筛选](字段与筛选/index.md)\n")
    _write(
        root,
        "products/GoInsight/字段与筛选/index.md",
        f"# 字段与筛选\n\n- [位置字段筛选]({Path(target).name})\n",
    )
    _write(
        root,
        target,
        "---\nmanaged_by: KnowledgeDigest\nreader_eligible: true\n---\n"
        "# 位置字段筛选\n\n## 先看：怎么用\n\n- 在数据分析页面操作。\n\n"
        "## 再看：规则和边界\n\n- 不支持错误页面；报告指标不是普通筛选。\n",
    )


def _companybrain_package(root: Path) -> dict[str, str]:
    paths = {
        "Home.md": "# Home\n\n- [产品](Products/产品索引.md)\n",
        "Products/产品索引.md": "# 产品\n\n- [GoInsight](GoInsight/文档总览.md)\n",
        "Products/GoInsight/文档总览.md": "# GoInsight\n\n- [模块](模块手册/模块总览.md)\n",
        "Products/GoInsight/模块手册/模块总览.md": "# 模块\n\n- [字段与筛选](字段与筛选/文本、数值与位置筛选.md)\n",
        "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md": (
            "# 文本、数值与位置筛选\n\n## 操作\n\n- 位置筛选规则。\n\n## 边界\n\n- 报告指标不是普通筛选。\n"
        ),
    }
    for relative, text in paths.items():
        _write(root, relative, text)
    return {relative: _sha(root / relative) for relative in paths}


def _config(tmp_path: Path, company_hash: str) -> Path:
    source = Path("config/task4-location-pilot.v1.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    data["companybrain_manifest"]["target_sha256"] = company_hash
    path = tmp_path / "task4-config.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _patch_entry_chain(monkeypatch: pytest.MonkeyPatch, hashes: dict[str, str]) -> None:
    monkeypatch.setattr(
        pilot,
        "COMPANYBRAIN_ENTRY_CHAIN",
        tuple({"role": role, "path": path, "sha256": hashes[path]} for role, path in (
            ("home", "Home.md"),
            ("product-index", "Products/产品索引.md"),
            ("goinsight-overview", "Products/GoInsight/文档总览.md"),
            ("module-index", "Products/GoInsight/模块手册/模块总览.md"),
            ("target", "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"),
        )),
    )


def _record(package_id: str, target: str, *, session: str, hops: int = 3, answer_score: int = 2, boundary_score: int = 2) -> dict[str, Any]:
    cases = []
    for index, case_id in enumerate(("S-01", "T-01", "N-01", "N-02"), start=1):
        negative = case_id.startswith("N-")
        checks = {f"{case_id}-check-{i}": True for i in range(answer_score if not negative else 1)}
        boundaries = {f"{case_id}-boundary-{i}": True for i in range(boundary_score if not negative else 1)}
        anchors = [
            {
                "claim_id": claim_id,
                "source_uri": "GoInsight/位置字段筛选.md",
                "fragment_locator": "lines:22-24",
                "content_hash": "a" * 64,
                "validation_status": "verified",
            }
            for claim_id in checks
        ]
        jumps = (
            ["Home.md", "products/GoInsight/index.md", "products/GoInsight/字段与筛选/index.md", target]
            if package_id == "knowledge_digest"
            else ["Home.md", "Products/产品索引.md", "Products/GoInsight/文档总览.md", "Products/GoInsight/模块手册/模块总览.md", target]
        )
        cases.append({
            "case_id": case_id,
            "order": index,
            "entry_path": "Home.md",
            "target_page": target,
            "first_hit_page": target,
            "first_hit_kind": 2,
            "reachable": True,
            "hop_count": hops,
            "jumps": jumps,
            "answer_result": "no_match" if negative else "hit",
            "answer_checklist": checks,
            "boundary_checklist": boundaries,
            "misleading_support": False,
            "claim_anchors": anchors,
        })
    return {
        "schema_version": "reader-evaluator-record.v1",
        "protocol_id": "reader-compare-v1",
        "question_set_id": "goinsight-location-reader-gate-v1",
        "evaluator_config_id": "reader-evaluator-v1",
        "protocol_hash": pilot.EVALUATION_IDENTITIES["protocol_hash"],
        "question_set_hash": pilot.EVALUATION_IDENTITIES["question_set_hash"],
        "evaluator_config_hash": pilot.EVALUATION_IDENTITIES["evaluator_config_hash"],
        "package_id": package_id,
        "session_id": session,
        "package_order": ["knowledge_digest", "companybrain"],
        "isolation": {"reader_only": True, "no_network": True, "private_session": True},
        "cases": cases,
    }


def _evaluator_record(kd_root: Path, cb_root: Path, *, kd_hops: int = 2, cb_hops: int = 4) -> dict[str, Any]:
    return {
        "schema_version": "reader-evaluator-record.v1",
        "protocol_id": "reader-compare-v1",
        "question_set_id": "goinsight-location-reader-gate-v1",
        "evaluator_config_id": "reader-evaluator-v1",
        "protocol_hash": pilot.EVALUATION_IDENTITIES["protocol_hash"],
        "question_set_hash": pilot.EVALUATION_IDENTITIES["question_set_hash"],
        "evaluator_config_hash": pilot.EVALUATION_IDENTITIES["evaluator_config_hash"],
        "package_order": ["knowledge_digest", "companybrain"],
        "isolation": {"reader_only": True, "no_network": True, "private_session": True},
        "sessions": [
            _record("knowledge_digest", "products/GoInsight/字段与筛选/位置字段筛选.md", session="kd-session", hops=kd_hops),
            _record("companybrain", "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md", session="cb-session", hops=cb_hops),
        ],
    }


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, Path, dict[str, Any]]:
    kd = tmp_path / "kd"
    cb = tmp_path / "cb"
    target = "products/GoInsight/字段与筛选/位置字段筛选.md"
    _reader_package(kd, target=target)
    hashes = _companybrain_package(cb)
    _patch_entry_chain(monkeypatch, hashes)
    config = _config(tmp_path, hashes["Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"])
    record = _evaluator_record(kd, cb, kd_hops=3, cb_hops=4)
    return kd, cb, config, tmp_path / "comparison", record


def test_gate_success_records_continue_and_three_axis_comparison(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "continue"
    assert result["decision"] == "continue"
    assert result["delivery_status"] == "not_released"
    assert result["comparison"]["axes"]["path"]["delta"] == 1
    assert result["comparison"]["strictly_better_axes"]
    assert (output / "comparison-run.json").is_file()


def test_comparison_requires_companybrain_five_entry_hash_binding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    (cb / "Products/GoInsight/文档总览.md").write_text("漂移\n", encoding="utf-8")
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "undecidable"
    assert "companybrain" in " ".join(result["failure_reasons"])
    assert result["delivery_status"] == "not_released"


@pytest.mark.parametrize("field", ["protocol_id", "question_set_id", "evaluator_config_id"])
def test_comparison_rejects_protocol_question_or_evaluator_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    record[field] = "drifted"
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "undecidable"
    assert "identity" in " ".join(result["failure_reasons"])


def test_comparison_rejects_shared_session_and_missing_first_hit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    record["sessions"][1]["session_id"] = record["sessions"][0]["session_id"]
    record["sessions"][0]["cases"][0]["first_hit_page"] = None
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "undecidable"
    assert any("session" in item or "first_hit" in item for item in result["failure_reasons"])


def test_comparison_stops_on_axis_regression_and_negative_misleading(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    record["sessions"][0]["cases"][2]["answer_result"] = "hit"
    record["sessions"][0]["cases"][2]["misleading_support"] = True
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "stop"
    assert result["decision"] == "stop"
    assert result["delivery_status"] == "not_released"


def test_comparison_stops_on_route_axis_regression(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    target = "products/GoInsight/字段与筛选/位置字段筛选.md"
    _write(kd, "products/GoInsight/字段与筛选/中间一.md", "# 中间一\n\n- [中间二](中间二.md)\n")
    _write(kd, "products/GoInsight/字段与筛选/中间二.md", f"# 中间二\n\n- [目标]({Path(target).name})\n")
    _write(kd, "products/GoInsight/字段与筛选/index.md", "# 字段与筛选\n\n- [中间一](中间一.md)\n")
    for case in record["sessions"][0]["cases"]:
        case["jumps"] = ["Home.md", "products/GoInsight/index.md", "products/GoInsight/字段与筛选/index.md", "products/GoInsight/字段与筛选/中间一.md", "products/GoInsight/字段与筛选/中间二.md", target]
        case["hop_count"] = 5
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "stop"
    assert result["comparison"]["axes"]["path"]["delta"] == -1


def test_comparison_requires_claim_anchors_and_reader_only_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    record["sessions"][0]["cases"][0]["claim_anchors"] = []
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=False, no_network=True)

    assert result["status"] == "undecidable"
    assert any("reader-only" in item or "anchor" in item for item in result["failure_reasons"])


def test_completed_candidate_rejects_forged_claim_anchor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    claims = []
    for case in pilot.TASK4_CASES:
        for claim_id in case["required_claim_ids"]:
            claims.append(
                {
                    "claim_id": claim_id,
                    "source_uri": "GoInsight/位置字段筛选.md",
                    "fragment_locator": "lines:22-24",
                    "content_hash": "a" * 64,
                    "validation_status": "verified",
                }
            )
    _write(kd, "audit/claim-evidence.json", json.dumps({"claims": claims}, ensure_ascii=False))
    _write(
        kd,
        "audit/compilation-run.json",
        json.dumps({"status": "completed", "reader_eligible": True, "delivery_status": "not_released"}, ensure_ascii=False),
    )
    for case, expected in zip(record["sessions"][0]["cases"], pilot.TASK4_CASES):
        case["claim_anchors"] = [
            {
                "claim_id": claim_id,
                "source_uri": "GoInsight/位置字段筛选.md",
                "fragment_locator": "lines:22-24",
                "content_hash": "a" * 64,
                "validation_status": "verified",
            }
            for claim_id in expected["required_claim_ids"]
        ]
    record["sessions"][0]["cases"][0]["claim_anchors"][0]["content_hash"] = "b" * 64

    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "undecidable"
    assert any("claim anchor" in item for item in result["failure_reasons"])


def test_comparison_rejects_reader_link_to_audit_or_raw(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    _write(kd, "Home.md", "# Home\n\n- [错误 Audit](audit/compilation-run.json)\n- [GoInsight](products/GoInsight/index.md)\n")
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "undecidable"
    assert "leaks" in " ".join(result["failure_reasons"])


def test_task4_route_accepts_companybrain_wikilinks(tmp_path: Path) -> None:
    _write(tmp_path, "Home.md", "# Home\n\n[[Products/产品索引]]\n")
    _write(tmp_path, "Products/产品索引.md", "# 产品\n\n[[GoInsight/文档总览]]\n")
    _write(tmp_path, "Products/GoInsight/文档总览.md", "# GoInsight\n\n[[模块手册/模块总览]]\n")
    _write(tmp_path, "Products/GoInsight/模块手册/模块总览.md", "# 模块\n\n[[字段与筛选/文本、数值与位置筛选]]\n")
    target = "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"
    _write(tmp_path, target, "# 位置筛选\n")

    snapshot = pilot.build_task4_reader_snapshot(tmp_path)

    assert pilot.task4_reader_route(snapshot, "Home.md", target) == (
        "Home.md",
        "Products/产品索引.md",
        "Products/GoInsight/文档总览.md",
        "Products/GoInsight/模块手册/模块总览.md",
        target,
    )


def test_gate_permission_or_unreadable_reader_is_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kd, cb, config, output, record = _setup(tmp_path, monkeypatch)
    page = kd / "products/GoInsight/字段与筛选/位置字段筛选.md"
    page.unlink()
    page.symlink_to(tmp_path / "missing-page.md")
    result = pilot.run_location_pilot_gate(kd, cb, config_path=config, output_root=output, evaluator_record=record, reader_only=True, no_network=True)

    assert result["status"] == "failed"
    assert result["decision"] == "stop"
    assert result["delivery_status"] == "not_released"


def test_cancelled_run_writes_terminal_state_and_no_reader(tmp_path: Path) -> None:
    output = tmp_path / "cancelled"
    formal = tmp_path / "formal.md"
    formal.write_text("old formal sentinel\n", encoding="utf-8")
    result = pilot.run_compilation_with_recovery(output, lambda: {"status": "completed"}, cancel_check=lambda: True)

    assert result["status"] == "cancelled"
    assert result["delivery_status"] == "not_released"
    assert not (output / "Home.md").exists()
    assert formal.read_text(encoding="utf-8") == "old formal sentinel\n"
    assert json.loads((output / "audit/compilation-run.json").read_text(encoding="utf-8"))["status"] == "cancelled"


def test_interrupted_run_is_failed_and_recovery_uses_new_run(tmp_path: Path) -> None:
    first = tmp_path / "interrupted"
    interrupted = pilot.run_compilation_with_recovery(first, lambda: (_ for _ in ()).throw(KeyboardInterrupt()))

    assert interrupted["status"] == "failed"
    assert interrupted["failure_reasons"] == ["interrupted"]
    second = tmp_path / "recovery"
    recovered = pilot.run_compilation_with_recovery(second, lambda: {"status": "completed", "delivery_status": "not_released"}, recovery_of=interrupted["run_id"])

    assert recovered["status"] == "completed"
    assert recovered["run_id"] != interrupted["run_id"]
    assert recovered["recovery_of"] == interrupted["run_id"]


def test_recovery_writes_running_state_and_removes_partial_reader(tmp_path: Path) -> None:
    output = tmp_path / "partial"
    observed: dict[str, Any] = {}

    def compile_partial() -> dict[str, Any]:
        observed.update(json.loads((output / "audit/compilation-run.json").read_text(encoding="utf-8")))
        _write(output, "Home.md", "# partial\n")
        return {"status": "failed", "failure_reasons": ["compile failed"]}

    result = pilot.run_compilation_with_recovery(output, compile_partial)

    assert observed["status"] == "running"
    assert result["status"] == "failed"
    assert not (output / "Home.md").exists()
    assert json.loads((output / "audit/compilation-run.json").read_text(encoding="utf-8"))["status"] == "failed"
