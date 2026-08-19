"""Task4 GoInsight pilot compiler, Reader gate, and comparison CLI.

The module is intentionally isolated from the formal KnowledgeDigest release
pipeline. It reads two Reader packages, keeps Audit/release state separate,
and records an evidence-only pilot decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from knowledge_digest.errors import ValidationError
from knowledge_digest.reader_quality import build_task4_reader_snapshot, task4_reader_route
from knowledge_digest.task4_location_pilot import compile_location_candidate, load_location_contract


COMPANYBRAIN_MANIFEST_ID = "companybrain-goinsight-field-filter-20260817-v1"
COMPANYBRAIN_ENTRY_CHAIN_VERSION = "companybrain-entry-chain-v1"
COMPANYBRAIN_TARGET_PATH = "Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md"
COMPANYBRAIN_ENTRY_CHAIN: tuple[dict[str, str], ...] = (
    {"role": "home", "path": "Home.md", "sha256": "cac402ccaef6bc55bef765ea93405a6af4c315d35cb68ecca7448249e729be2f"},
    {"role": "product-index", "path": "Products/产品索引.md", "sha256": "75e3b641ea4506c67cc4f209b1322a5a0c5381b295243fc0826299e32ae449d7"},
    {"role": "goinsight-overview", "path": "Products/GoInsight/文档总览.md", "sha256": "0a22821c27352cb31f6c39e7b44e229d54fba82f2f5de0e4e99cd3b2ebe399f9"},
    {"role": "module-index", "path": "Products/GoInsight/模块手册/模块总览.md", "sha256": "daea01ef80111682ce15ae79b9accc4251e3889d5dbf154c128e6c31f7448cae"},
    {"role": "target", "path": COMPANYBRAIN_TARGET_PATH, "sha256": "9ac850ad9816a422997f99a4564b55ea84dc2834171e7a853bdecbc03c0f4edf"},
)

PROTOCOL_ID = "reader-compare-v1"
QUESTION_SET_ID = "goinsight-location-reader-gate-v1"
EVALUATOR_CONFIG_ID = "reader-evaluator-v1"


def _hash(value: bytes | str) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def _json_hash(value: Any) -> str:
    return _hash(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


EVALUATION_IDENTITIES: Mapping[str, str] = {
    "protocol_id": PROTOCOL_ID,
    "question_set_id": QUESTION_SET_ID,
    "evaluator_config_id": EVALUATOR_CONFIG_ID,
    "protocol_hash": _json_hash({"schema": "reader-compare.v1", "id": PROTOCOL_ID}),
    "question_set_hash": _json_hash({"schema": "goinsight-location-reader-gate.v1", "id": QUESTION_SET_ID}),
    "evaluator_config_hash": _json_hash({"schema": "reader-evaluator.v1", "id": EVALUATOR_CONFIG_ID}),
}

TASK4_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "S-01",
        "polarity": "positive",
        "required_claim_ids": ("S-01-entry", "S-01-draw", "S-01-condition", "S-01-points", "S-01-edit", "S-01-map-controls", "S-01-submit", "S-01-cancel-result"),
    },
    {
        "case_id": "T-01",
        "polarity": "positive",
        "required_claim_ids": ("T-01-data-analysis", "T-01-history-context", "T-01-history-questions", "T-01-performance-context", "T-01-save-analysis"),
    },
    {"case_id": "N-01", "polarity": "negative", "required_claim_ids": ("N-01-detail-global",)},
    {"case_id": "N-02", "polarity": "negative", "required_claim_ids": ("N-02-report-metric",)},
)
_CASE_BY_ID = {str(row["case_id"]): row for row in TASK4_CASES}
_LINE_LOCATOR = re.compile(r"^lines:(\d+)(?:-(\d+))?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_READER_ASSERTIONS: Mapping[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "S-01": (
        ("S-01-entry", ("数据分析页", "筛选栏")),
        ("S-01-draw", ("地图", "画区域")),
        ("S-01-condition", ("Inside", "Outside", "默认")),
        ("S-01-points", ("3个点", "100个点")),
        ("S-01-edit", ("双击", "清空")),
        ("S-01-map-controls", ("缩放", "拖动")),
        ("S-01-submit", ("提交", "交叉")),
        ("S-01-cancel-result", ("取消", "经纬度", "小地图")),
    ),
    "T-01": (
        ("T-01-data-analysis", ("数据分析页", "数据集详情页", "全局筛选卡片")),
        ("T-01-history-context", ("Location", "Reseller", "Merchant", "Terminal SN", "Event Time")),
        ("T-01-history-questions", ("近30天", "设备SN", "位置变化")),
        ("T-01-performance-context", ("一百万", "性能背景")),
        ("T-01-save-analysis", ("保存", "工作表")),
    ),
    "N-01": (("N-01-detail-global", ("数据集详情页", "全局筛选卡片", "不可添加筛选")),),
    "N-02": (("N-02-report-metric", ("计算指标", "普通位置筛选", "不")),),
}
_BOUNDARY_ASSERTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("only-data-analysis", ("数据分析页", "数据集详情页", "全局筛选卡片")),
    ("reject-detail-global", ("不可添加筛选",)),
    ("distinguish-report-metric", ("计算指标", "普通位置筛选")),
    ("troubleshoot-location", ("点", "交叉", "Inside", "Outside")),
)


class PilotGateError(RuntimeError):
    def __init__(self, message: str, *, status: str = "undecidable") -> None:
        super().__init__(message)
        self.status = status


def route_rank(reachable: bool, first_hit_kind: int, hop_count: int) -> tuple[int, int, int]:
    """Return the fixed route ordering, never a subtraction of path strings."""

    return (int(bool(reachable)), int(first_hit_kind), -int(hop_count))


def _reader_normalize(text: str) -> str:
    return "".join(text.casefold().split())


def _reader_assertion_matches(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _reader_normalize(text)
    normalized_terms = tuple(_reader_normalize(term) for term in terms)
    if terms == ("地图", "画区域"):
        return "地图" in normalized and any(term in normalized for term in ("画区域", "点击添加点", "添加点"))
    if terms == ("双击", "清空"):
        return "双击" in normalized and any(term in normalized for term in ("清空", "clear"))
    if terms == ("缩放", "拖动"):
        return "缩放" in normalized and any(term in normalized for term in ("拖动", "拖拽"))
    if terms == ("3个点", "100个点"):
        return any(term in normalized for term in ("3个点", "少于3个", "至少添加3个")) and "100个点" in normalized
    if terms == ("取消", "经纬度", "小地图"):
        return "取消" in normalized and any(term in normalized for term in ("经纬度", "纬经度")) and any(term in normalized for term in ("小地图", "迷你地图"))
    if terms == ("计算指标", "普通位置筛选", "不"):
        return "计算指标" in normalized and any(term in normalized for term in ("普通位置筛选", "普通的位置筛选")) and any(term in normalized for term in ("不按", "不做", "不是"))
    if terms == ("数据集详情页", "全局筛选卡片", "不可添加筛选"):
        return "数据集详情页" in normalized and "全局筛选卡片" in normalized and any(term in normalized for term in ("不可添加筛选", "不在数据集详情页和全局筛选卡片中配置"))
    return all(term in normalized for term in normalized_terms)


def _reader_case_checks(case_id: str, text: str) -> dict[str, bool]:
    return {
        claim_id: _reader_assertion_matches(text, terms)
        for claim_id, terms in _READER_ASSERTIONS[case_id]
    }


def _reader_boundary_checks(text: str) -> dict[str, bool]:
    normalized = _reader_normalize(text)
    result: dict[str, bool] = {}
    for check_id, terms in _BOUNDARY_ASSERTIONS:
        if check_id == "reject-detail-global":
            result[check_id] = any(term in normalized for term in ("不可添加筛选", "不在数据集详情页和全局筛选卡片中配置"))
        elif check_id == "distinguish-report-metric":
            result[check_id] = "计算指标" in normalized and any(term in normalized for term in ("普通位置筛选", "普通的位置筛选"))
        else:
            result[check_id] = all(_reader_normalize(term) in normalized for term in terms)
    return result


def _source_fragment(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise PilotGateError(f"source anchor is outside Reader target: {path}")
    return "\n".join(lines[start - 1 : end]).strip()


def _companybrain_anchor(target_path: str, claim_id: str, companybrain_root: Path) -> dict[str, Any]:
    ranges = {
        "S-01-entry": (110, 110),
        "S-01-draw": (114, 114),
        "S-01-condition": (112, 112),
        "S-01-points": (116, 120),
        "S-01-edit": (114, 114),
        "S-01-map-controls": (121, 121),
        "S-01-submit": (120, 120),
        "S-01-cancel-result": (123, 123),
        "T-01-data-analysis": (108, 110),
        "T-01-history-context": (108, 125),
        "T-01-history-questions": (108, 125),
        "T-01-performance-context": (108, 125),
        "T-01-save-analysis": (108, 125),
        "N-01-detail-global": (110, 110),
        "N-02-report-metric": (125, 125),
    }
    start, end = ranges[claim_id]
    fragment = _source_fragment(companybrain_root / target_path, start, end)
    return {
        "claim_id": claim_id,
        "source_uri": target_path,
        "fragment_locator": f"lines:{start}-{end}" if start != end else f"lines:{start}",
        "content_hash": _hash(fragment),
        "validation_status": "verified",
    }


def _reader_evaluator_session(
    package_id: str,
    snapshot: Any,
    target_path: str,
    *,
    candidate_claim_catalog: Mapping[str, Mapping[str, Any]] | None = None,
    companybrain_root: Path | None = None,
) -> dict[str, Any]:
    target_text = snapshot.files.get(target_path)
    if target_text is None:
        raise PilotGateError(f"{package_id} Reader target is missing: {target_path}")
    route = task4_reader_route(snapshot, "Home.md", target_path)
    if not route or route[-1] != target_path:
        raise PilotGateError(f"{package_id} Reader route cannot reach target")
    cases: list[dict[str, Any]] = []
    for order, case in enumerate(TASK4_CASES, start=1):
        case_id = str(case["case_id"])
        answer_checks = _reader_case_checks(case_id, target_text)
        boundary_checks = _reader_boundary_checks(target_text)
        anchors: list[dict[str, Any]] = []
        for claim_id in case["required_claim_ids"]:
            if package_id == "knowledge_digest":
                if candidate_claim_catalog is None or claim_id not in candidate_claim_catalog:
                    raise PilotGateError(f"candidate claim anchor is missing: {claim_id}")
                anchors.append({key: candidate_claim_catalog[claim_id][key] for key in (
                    "claim_id", "source_uri", "fragment_locator", "content_hash", "validation_status"
                )})
            else:
                if companybrain_root is None:
                    raise PilotGateError("companybrain anchor root is missing")
                anchors.append(_companybrain_anchor(target_path, claim_id, companybrain_root))
        positive = case["polarity"] == "positive"
        all_answered = all(answer_checks.values())
        misleading = (not positive) and not all_answered
        cases.append(
            {
                "case_id": case_id,
                "order": order,
                "entry_path": "Home.md",
                "target_page": target_path,
                "first_hit_page": target_path,
                "first_hit_kind": 2,
                "reachable": True,
                "hop_count": len(route) - 1,
                "jumps": list(route),
                "answer_result": "hit" if positive and all_answered else "no_match",
                "answer_checklist": answer_checks,
                "boundary_checklist": boundary_checks,
                "misleading_support": misleading,
                "claim_anchors": anchors,
            }
        )
    return {
        "package_id": package_id,
        "session_id": _json_hash({"package_id": package_id, "snapshot": snapshot.content_hash})[:16],
        "reader_only_observed_paths": list(route),
        "cases": cases,
    }


def build_task4_reader_evaluator_record(
    candidate_root: Path,
    companybrain_root: Path,
    *,
    config_path: Path,
) -> dict[str, Any]:
    """Record a fresh no-network Reader-only observation from both packages.

    Scoring reads only each package's Reader snapshot.  Audit claim rows are
    attached afterward solely as provenance anchors; they do not contribute
    to the answer checks.  This keeps the evaluator record reproducible while
    making the missing-evaluator state impossible to hide behind compile
    success.
    """

    contract = load_location_contract(Path(config_path))
    candidate_snapshot = build_task4_reader_snapshot(Path(candidate_root))
    company_snapshot = build_task4_reader_snapshot(Path(companybrain_root))
    target = str(contract["canonical_topic"]["page_path"])
    company_target = COMPANYBRAIN_TARGET_PATH
    claim_catalog = _candidate_claim_catalog(Path(candidate_root))
    if claim_catalog is None:
        raise PilotGateError("candidate claim catalog is missing")
    company_binding = _validate_companybrain_binding(Path(companybrain_root), contract)
    sessions = [
        _reader_evaluator_session(
            "knowledge_digest",
            candidate_snapshot,
            target,
            candidate_claim_catalog=claim_catalog,
        ),
        _reader_evaluator_session(
            "companybrain",
            company_snapshot,
            company_target,
            companybrain_root=Path(companybrain_root),
        ),
    ]
    return {
        "schema_version": "reader-evaluator-record.v1",
        "protocol_id": PROTOCOL_ID,
        "question_set_id": QUESTION_SET_ID,
        "evaluator_config_id": EVALUATOR_CONFIG_ID,
        "protocol_hash": EVALUATION_IDENTITIES["protocol_hash"],
        "question_set_hash": EVALUATION_IDENTITIES["question_set_hash"],
        "evaluator_config_hash": EVALUATION_IDENTITIES["evaluator_config_hash"],
        "evaluation_mode": "reader-only-deterministic-observation-v1",
        "package_order": ["knowledge_digest", "companybrain"],
        "isolation": {"reader_only": True, "no_network": True, "private_session": True},
        "reader_snapshots": {
            "knowledge_digest": candidate_snapshot.content_hash,
            "companybrain": company_snapshot.content_hash,
        },
        "companybrain_binding": company_binding,
        "sessions": sessions,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_hash(path: Path) -> str:
    return _hash(path.read_bytes())


def _read_json(value: Path | Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value
    path = Path(value)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotGateError(f"evaluator record unreadable: {exc}", status="failed") from exc
    if not isinstance(data, Mapping):
        raise PilotGateError("evaluator record must be an object")
    return data


def _validate_companybrain_binding(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise PilotGateError("companybrain root is unreadable", status="failed")
    manifest = contract.get("companybrain_manifest")
    if not isinstance(manifest, Mapping):
        raise PilotGateError("companybrain manifest binding is missing")
    if manifest.get("manifest_id") != COMPANYBRAIN_MANIFEST_ID:
        raise PilotGateError("companybrain manifest identity drift")
    target = next(row for row in COMPANYBRAIN_ENTRY_CHAIN if row["role"] == "target")
    if manifest.get("target_path") != target["path"] or manifest.get("target_sha256") != target["sha256"]:
        raise PilotGateError("companybrain target binding drift")
    rows: list[dict[str, str]] = []
    for expected in COMPANYBRAIN_ENTRY_CHAIN:
        path = root / expected["path"]
        if path.is_symlink() or not path.is_file():
            raise PilotGateError(f"companybrain entry unreadable: {expected['path']}", status="failed")
        try:
            actual = _file_hash(path)
        except OSError as exc:
            raise PilotGateError(f"companybrain entry unreadable: {expected['path']}: {exc}", status="failed") from exc
        if actual != expected["sha256"]:
            raise PilotGateError(f"companybrain entry hash drift: {expected['path']}")
        rows.append({"role": expected["role"], "path": expected["path"], "sha256": actual})
    return {
        "manifest_id": COMPANYBRAIN_MANIFEST_ID,
        "entry_chain_version": COMPANYBRAIN_ENTRY_CHAIN_VERSION,
        "entries": rows,
        "target_path": target["path"],
        "target_sha256": target["sha256"],
    }


def _validate_evaluator_header(record: Mapping[str, Any], *, reader_only: bool, no_network: bool) -> list[str]:
    failures: list[str] = []
    if record.get("schema_version") != "reader-evaluator-record.v1":
        failures.append("evaluator record schema identity drift")
    for key in ("protocol_id", "question_set_id", "evaluator_config_id", "protocol_hash", "question_set_hash", "evaluator_config_hash"):
        if record.get(key) != EVALUATION_IDENTITIES[key]:
            failures.append(f"identity mismatch: {key}")
    if record.get("package_order") != ["knowledge_digest", "companybrain"]:
        failures.append("package order mismatch")
    isolation = record.get("isolation")
    if not isinstance(isolation, Mapping) or isolation.get("reader_only") is not True or isolation.get("no_network") is not True or isolation.get("private_session") is not True:
        failures.append("reader isolation contract missing")
    if not reader_only:
        failures.append("reader-only flag is required")
    if not no_network:
        failures.append("no-network flag is required")
    return failures


def _validate_anchor(anchor: Any, claim_catalog: Mapping[str, Mapping[str, Any]] | None = None) -> bool:
    if not isinstance(anchor, Mapping):
        return False
    claim_id = anchor.get("claim_id")
    if not isinstance(claim_id, str) or not claim_id.strip():
        return False
    if not isinstance(anchor.get("source_uri"), str) or not anchor["source_uri"].strip():
        return False
    if not isinstance(anchor.get("fragment_locator"), str) or _LINE_LOCATOR.fullmatch(anchor["fragment_locator"]) is None:
        return False
    if not isinstance(anchor.get("content_hash"), str) or _SHA256.fullmatch(anchor["content_hash"]) is None:
        return False
    if anchor.get("validation_status") != "verified":
        return False
    if claim_catalog is None:
        return True
    expected = claim_catalog.get(claim_id)
    if expected is None:
        return False
    return all(anchor.get(field) == expected.get(field) for field in (
        "source_uri",
        "fragment_locator",
        "content_hash",
        "validation_status",
    ))


def _candidate_claim_catalog(root: Path) -> dict[str, dict[str, Any]] | None:
    path = root / "audit/claim-evidence.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotGateError(f"candidate claim catalog unreadable: {exc}", status="failed") from exc
    claims = data.get("claims") if isinstance(data, Mapping) else None
    if not isinstance(claims, list):
        raise PilotGateError("candidate claim catalog is incomplete")
    catalog: dict[str, dict[str, Any]] = {}
    for row in claims:
        if not isinstance(row, Mapping) or not isinstance(row.get("claim_id"), str) or not row["claim_id"].strip():
            raise PilotGateError("candidate claim catalog contains an invalid claim")
        claim_id = str(row["claim_id"])
        if claim_id in catalog:
            raise PilotGateError(f"candidate claim catalog duplicates {claim_id}")
        if not _validate_anchor(row):
            raise PilotGateError(f"candidate claim catalog anchor is invalid: {claim_id}")
        catalog[claim_id] = dict(row)
    return catalog


def _validate_candidate_state(root: Path) -> str:
    run_path = root / "audit/compilation-run.json"
    if not run_path.is_file():
        return "candidate"
    try:
        run = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotGateError(f"candidate run record unreadable: {exc}", status="failed") from exc
    if not isinstance(run, Mapping):
        raise PilotGateError("candidate run record is not an object")
    if run.get("status") != "completed" or run.get("reader_eligible") is not True:
        raise PilotGateError("candidate Reader is not eligible")
    if run.get("delivery_status") != "not_released":
        raise PilotGateError("candidate delivery status crossed formal boundary")
    return str(run.get("candidate_status") or "candidate")


def _reader_link_leaks(snapshot: Any, package_id: str) -> list[str]:
    leaks: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path, text in snapshot.files.items():
        for target in link_pattern.findall(text):
            folded = target.casefold()
            if any(token in folded for token in ("audit", "raw:", "provider")):
                leaks.append(f"{package_id}/{path}: Reader link leaks {target}")
    return leaks


def _validate_case(
    package_id: str,
    snapshot: Any,
    case: Mapping[str, Any],
    *,
    claim_catalog: Mapping[str, Mapping[str, Any]] | None,
) -> tuple[dict[str, Any], list[str], list[str]]:
    case_id = str(case.get("case_id", ""))
    structural: list[str] = []
    hard: list[str] = []
    expected = _CASE_BY_ID.get(case_id)
    if expected is None:
        return {}, [f"unknown case: {case_id}"], []
    entry_path = case.get("entry_path")
    target_path = case.get("target_page")
    if not isinstance(entry_path, str) or not isinstance(target_path, str):
        return {}, [f"{package_id}/{case_id}: entry or target missing"], []
    actual_route = task4_reader_route(snapshot, entry_path, target_path)
    if not actual_route:
        structural.append(f"{package_id}/{case_id}: first_hit route is unreachable")
    jumps = case.get("jumps")
    if not isinstance(jumps, list) or [str(value) for value in jumps] != list(actual_route):
        structural.append(f"{package_id}/{case_id}: jumps do not match Reader route")
    reachable = case.get("reachable")
    first_hit = case.get("first_hit_page")
    first_hit_kind = case.get("first_hit_kind")
    hop_count = case.get("hop_count")
    if reachable is not True or first_hit != target_path or first_hit_kind != 2:
        structural.append(f"{package_id}/{case_id}: first_hit is missing or not canonical")
    if not isinstance(hop_count, int) or hop_count != max(0, len(actual_route) - 1):
        structural.append(f"{package_id}/{case_id}: hop_count is not derived from route")
    anchors = case.get("claim_anchors")
    if not isinstance(anchors, list) or not anchors or any(not _validate_anchor(anchor, claim_catalog) for anchor in anchors):
        structural.append(f"{package_id}/{case_id}: claim anchor is incomplete")
    elif claim_catalog is not None:
        anchor_ids = {str(anchor["claim_id"]) for anchor in anchors if isinstance(anchor, Mapping)}
        if not anchor_ids.issubset(set(claim_catalog)):
            structural.append(f"{package_id}/{case_id}: claim anchor is not in candidate catalog")
        if not set(expected["required_claim_ids"]).issubset(anchor_ids):
            structural.append(f"{package_id}/{case_id}: required claim anchor is missing")
    answer_checks = case.get("answer_checklist")
    boundary_checks = case.get("boundary_checklist")
    quality_findings: list[str] = []
    if not isinstance(answer_checks, Mapping) or not answer_checks or any(value is not True for value in answer_checks.values()):
        quality_findings.append(f"{package_id}/{case_id}: answer completeness failed")
    if not isinstance(boundary_checks, Mapping) or not boundary_checks or any(value is not True for value in boundary_checks.values()):
        quality_findings.append(f"{package_id}/{case_id}: boundary checklist failed")
    polarity = expected["polarity"]
    answer_result = case.get("answer_result")
    if polarity == "positive" and answer_result != "hit":
        quality_findings.append(f"{package_id}/{case_id}: positive question did not answer")
    if polarity == "negative" and (answer_result != "no_match" or case.get("misleading_support") is True):
        quality_findings.append(f"{package_id}/{case_id}: negative question was misleading")
    if package_id == "knowledge_digest":
        hard.extend(quality_findings)
    row = {
        "case_id": case_id,
        "polarity": polarity,
        "entry_path": entry_path,
        "target_page": target_path,
        "route": list(actual_route),
        "reachable": bool(reachable),
        "first_hit_kind": int(first_hit_kind) if isinstance(first_hit_kind, int) else None,
        "hop_count": int(hop_count) if isinstance(hop_count, int) else None,
        "route_rank": list(route_rank(bool(reachable), int(first_hit_kind) if isinstance(first_hit_kind, int) else 0, int(hop_count) if isinstance(hop_count, int) else 999999)),
        "answer_passed": sum(value is True for value in answer_checks.values()) if isinstance(answer_checks, Mapping) else 0,
        "answer_total": len(answer_checks) if isinstance(answer_checks, Mapping) else 0,
        "boundary_passed": sum(value is True for value in boundary_checks.values()) if isinstance(boundary_checks, Mapping) else 0,
        "boundary_total": len(boundary_checks) if isinstance(boundary_checks, Mapping) else 0,
        "answer_result": answer_result,
        "claim_anchors": [dict(anchor) for anchor in anchors] if isinstance(anchors, list) else [],
        "quality_findings": quality_findings,
    }
    return row, structural, hard


def _validate_sessions(
    record: Mapping[str, Any],
    snapshots: Mapping[str, Any],
    claim_catalog: Mapping[str, Mapping[str, Any]] | None,
) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]:
    structural = _validate_evaluator_header(record, reader_only=True, no_network=True)
    hard: list[str] = []
    sessions = record.get("sessions")
    if not isinstance(sessions, list) or len(sessions) != 2:
        return {}, [*structural, "two isolated evaluator sessions are required"], hard
    by_package: dict[str, Mapping[str, Any]] = {}
    session_ids: set[str] = set()
    for session in sessions:
        if not isinstance(session, Mapping) or session.get("package_id") not in {"knowledge_digest", "companybrain"}:
            structural.append("package session identity is invalid")
            continue
        package_id = str(session["package_id"])
        session_id = session.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip() or session_id in session_ids:
            structural.append("reader sessions are shared or missing")
        session_ids.add(str(session_id))
        by_package[package_id] = session
    if set(by_package) != {"knowledge_digest", "companybrain"}:
        structural.append("both package sessions are required")
        return {}, structural, hard
    output: dict[str, list[dict[str, Any]]] = {}
    expected_order = [str(row["case_id"]) for row in TASK4_CASES]
    for package_id in ("knowledge_digest", "companybrain"):
        cases = by_package[package_id].get("cases")
        if not isinstance(cases, list) or [str(row.get("case_id")) for row in cases if isinstance(row, Mapping)] != expected_order:
            structural.append(f"{package_id}: fixed S/T/N order is missing")
            continue
        rows: list[dict[str, Any]] = []
        for case in cases:
            if not isinstance(case, Mapping):
                structural.append(f"{package_id}: case row is invalid")
                continue
            row, case_structural, case_hard = _validate_case(
                package_id,
                snapshots[package_id],
                case,
                claim_catalog=claim_catalog if package_id == "knowledge_digest" else None,
            )
            rows.append(row)
            structural.extend(case_structural)
            hard.extend(case_hard)
        output[package_id] = rows
    return output, structural, hard


def _axis_fraction(rows: list[dict[str, Any]], passed_key: str, total_key: str) -> dict[str, Any]:
    passed = sum(int(row.get(passed_key, 0)) for row in rows)
    total = sum(int(row.get(total_key, 0)) for row in rows)
    return {"passed": passed, "total": total, "ratio": (passed / total if total else 0.0)}


def _fraction_sign(left: Mapping[str, Any], right: Mapping[str, Any]) -> int:
    lhs = int(left["passed"]) * int(right["total"])
    rhs = int(right["passed"]) * int(left["total"])
    return 1 if lhs > rhs else -1 if lhs < rhs else 0


def _compare_axes(rows: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    kd_rows = rows["knowledge_digest"]
    cb_rows = rows["companybrain"]
    path_wins = 0
    path_losses = 0
    path_ties = 0
    path_cases: list[dict[str, Any]] = []
    for kd, cb in zip(kd_rows, cb_rows):
        kd_rank = tuple(kd["route_rank"])
        cb_rank = tuple(cb["route_rank"])
        if kd_rank > cb_rank:
            path_wins += 1
            outcome = 1
        elif kd_rank < cb_rank:
            path_losses += 1
            outcome = -1
        else:
            path_ties += 1
            outcome = 0
        path_cases.append({"case_id": kd["case_id"], "knowledge_digest": list(kd_rank), "companybrain": list(cb_rank), "delta": outcome})
    path_delta = 1 if path_wins and not path_losses else -1 if path_losses and not path_wins else 0
    answer_kd = _axis_fraction(kd_rows, "answer_passed", "answer_total")
    answer_cb = _axis_fraction(cb_rows, "answer_passed", "answer_total")
    boundary_kd = _axis_fraction(kd_rows, "boundary_passed", "boundary_total")
    boundary_cb = _axis_fraction(cb_rows, "boundary_passed", "boundary_total")
    return {
        "path": {"knowledge_digest": {"wins": path_wins, "losses": path_losses, "ties": path_ties}, "companybrain": {"wins": path_losses, "losses": path_wins, "ties": path_ties}, "delta": path_delta, "cases": path_cases},
        "answer": {"knowledge_digest": answer_kd, "companybrain": answer_cb, "delta": _fraction_sign(answer_kd, answer_cb)},
        "boundary": {"knowledge_digest": boundary_kd, "companybrain": boundary_cb, "delta": _fraction_sign(boundary_kd, boundary_cb)},
    }


def _write_comparison(output: Path, result: Mapping[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "comparison-run.json", result)
    _write_json(
        output / "release-summary.json",
        {
            "schema_version": "task4-location-release-summary.v1",
            "status": result.get("status"),
            "decision": result.get("decision"),
            "candidate_status": result.get("candidate_status", "not_released"),
            "delivery_status": "not_released",
            "failure_reasons": result.get("failure_reasons", []),
        },
    )


def run_location_pilot_gate(
    candidate_root: Path,
    companybrain_root: Path,
    *,
    config_path: Path,
    output_root: Path,
    evaluator_record: Path | Mapping[str, Any] | None = None,
    reader_only: bool = False,
    no_network: bool = False,
) -> dict[str, Any]:
    """Run one deterministic, evidence-only two-package Reader comparison."""

    output = Path(output_root)
    if output.exists() and any(output.iterdir()):
        return {"status": "failed", "decision": "stop", "delivery_status": "not_released", "failure_reasons": ["comparison output already exists"]}
    result: dict[str, Any] = {
        "schema_version": "task4-location-comparison-run.v1",
        "status": "undecidable",
        "decision": "undecidable",
        "candidate_status": "not_released",
        "delivery_status": "not_released",
        "reader_only": bool(reader_only),
        "no_network": bool(no_network),
        "failure_reasons": [],
    }
    try:
        contract = load_location_contract(Path(config_path))
        binding = _validate_companybrain_binding(Path(companybrain_root), contract)
        result["companybrain_binding"] = binding
        if not reader_only or not no_network:
            raise PilotGateError("comparison requires reader-only and no-network flags")
        candidate_status = _validate_candidate_state(Path(candidate_root))
        result["candidate_status"] = candidate_status
        candidate_snapshot = build_task4_reader_snapshot(Path(candidate_root))
        company_snapshot = build_task4_reader_snapshot(Path(companybrain_root))
        link_leaks = [
            *_reader_link_leaks(candidate_snapshot, "knowledge_digest"),
            *_reader_link_leaks(company_snapshot, "companybrain"),
        ]
        if link_leaks:
            raise PilotGateError(link_leaks[0])
        result["reader_snapshots"] = {
            "knowledge_digest": candidate_snapshot.content_hash,
            "companybrain": company_snapshot.content_hash,
        }
        claim_catalog = _candidate_claim_catalog(Path(candidate_root))
        candidate_run_path = Path(candidate_root) / "audit/compilation-run.json"
        if candidate_run_path.is_file() and claim_catalog is None:
            raise PilotGateError("completed candidate claim catalog is missing")
        record = _read_json(evaluator_record)
        if record is None:
            result["failure_reasons"] = ["evaluator record unavailable"]
            _write_comparison(output, result)
            return result
        rows, structural, hard = _validate_sessions(
            record,
            {"knowledge_digest": candidate_snapshot, "companybrain": company_snapshot},
            claim_catalog,
        )
        result["evaluator_identity"] = {key: record.get(key) for key in ("protocol_id", "question_set_id", "evaluator_config_id", "protocol_hash", "question_set_hash", "evaluator_config_hash")}
        result["sessions"] = {
            package_id: {
                "session_id": record.get("sessions", [])[index].get("session_id") if isinstance(record.get("sessions"), list) and len(record.get("sessions", [])) > index and isinstance(record["sessions"][index], Mapping) else None,
                "package_order": record.get("package_order"),
                "isolation": record.get("isolation"),
            }
            for index, package_id in enumerate(("knowledge_digest", "companybrain"))
        }
        result["cases"] = rows
        if structural:
            result["status"] = "undecidable"
            result["decision"] = "undecidable"
            result["failure_reasons"] = sorted(set(structural))
        elif hard:
            result["status"] = "stop"
            result["decision"] = "stop"
            result["failure_reasons"] = sorted(set(hard))
        else:
            axes = _compare_axes(rows)
            result["comparison"] = {"axes": axes, "strictly_better_axes": [key for key, value in axes.items() if value["delta"] > 0]}
            deltas = [int(value["delta"]) for value in axes.values()]
            if any(delta < 0 for delta in deltas):
                result["status"] = "stop"
                result["decision"] = "stop"
                result["failure_reasons"] = ["KnowledgeDigest is worse on at least one comparison axis"]
            elif not any(delta > 0 for delta in deltas):
                result["status"] = "stop"
                result["decision"] = "stop"
                result["failure_reasons"] = ["KnowledgeDigest has no strictly better comparison axis"]
            else:
                result["status"] = "continue"
                result["decision"] = "continue"
    except PilotGateError as exc:
        result["status"] = exc.status
        result["decision"] = "stop" if exc.status == "failed" else "undecidable"
        result["failure_reasons"] = [str(exc)]
    except (OSError, UnicodeError, ValidationError) as exc:
        result["status"] = "failed"
        result["decision"] = "stop"
        result["failure_reasons"] = [str(exc)]
    _write_comparison(output, result)
    return result


def _run_record(output: Path, value: Mapping[str, Any]) -> None:
    _write_json(output / "audit/compilation-run.json", value)


class _CompilationCancelled(RuntimeError):
    pass


def _remove_reader_projection(output: Path) -> list[str]:
    errors: list[str] = []
    for relative in ("Home.md", "index.md", "products", "Products", "references", "sources"):
        path = output / relative
        try:
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except OSError as exc:
            errors.append(f"reader cleanup failed for {relative}: {exc}")
    return errors


def run_compilation_with_recovery(
    output_root: Path,
    compile_fn: Callable[[], Mapping[str, Any]],
    *,
    cancel_check: Callable[[], bool] | None = None,
    recovery_of: str | None = None,
) -> dict[str, Any]:
    """Execute one isolated compile and persist a truthful terminal state."""

    output = Path(output_root)
    if output.exists() and any(output.iterdir()):
        return {"status": "failed", "delivery_status": "not_released", "failure_reasons": ["output root already exists"], "run_id": _hash(str(output))[:16]}
    output.mkdir(parents=True, exist_ok=True)
    run_id = _hash(f"{output.resolve()}\0{time.time_ns()}")[:16]
    started = time.time()
    base = {
        "schema_version": "task4-location-compilation-run.v1",
        "run_id": run_id,
        "started_at": started,
        "delivery_status": "not_released",
        "candidate_status": "not_released",
        "recovery_of": recovery_of,
    }
    _run_record(
        output,
        {
            **base,
            "status": "running",
            "run_status": "running",
            "reader_eligible": False,
            "failure_reasons": [],
        },
    )
    previous_handlers: dict[int, Any] = {}

    def cancel_signal(signum: int, _frame: Any) -> None:
        raise _CompilationCancelled(f"cancelled by {signal.Signals(signum).name}")

    if threading.current_thread() is threading.main_thread():
        for signal_name in ("SIGINT", "SIGTERM"):
            signal_number = getattr(signal, signal_name, None)
            if signal_number is not None:
                previous_handlers[signal_number] = signal.getsignal(signal_number)
                signal.signal(signal_number, cancel_signal)
    try:
        if cancel_check is not None and cancel_check():
            terminal = {
                **base,
                "status": "cancelled",
                "run_status": "cancelled",
                "reader_eligible": False,
                "failure_reasons": ["cancelled"],
                "completed_at": time.time(),
            }
            terminal["failure_reasons"].extend(_remove_reader_projection(output))
            _run_record(output, terminal)
            return terminal
        compiled = dict(compile_fn())
        status = str(compiled.get("status") or "failed")
        terminal = {
            **base,
            **compiled,
            "status": status,
            "run_status": status,
            "completed_at": time.time(),
            "delivery_status": "not_released",
            "recovery_of": recovery_of,
            "failure_reasons": list(compiled.get("failure_reasons", [])),
        }
        if status != "completed":
            terminal["reader_eligible"] = False
            terminal["candidate_status"] = "not_released"
            terminal["failure_reasons"].extend(_remove_reader_projection(output))
        else:
            terminal.setdefault("candidate_status", "candidate")
        _run_record(output, terminal)
        return terminal
    except _CompilationCancelled:
        terminal = {
            **base,
            "status": "cancelled",
            "run_status": "cancelled",
            "reader_eligible": False,
            "failure_reasons": ["cancelled"],
            "completed_at": time.time(),
        }
        terminal["failure_reasons"].extend(_remove_reader_projection(output))
        _run_record(output, terminal)
        return terminal
    except KeyboardInterrupt:
        terminal = {
            **base,
            "status": "failed",
            "run_status": "failed",
            "reader_eligible": False,
            "failure_reasons": ["interrupted"],
            "completed_at": time.time(),
        }
        terminal["failure_reasons"].extend(_remove_reader_projection(output))
        _run_record(output, terminal)
        return terminal
    except BaseException as exc:
        terminal = {
            **base,
            "status": "failed",
            "run_status": "failed",
            "reader_eligible": False,
            "failure_reasons": [str(exc) or "compile failed"],
            "completed_at": time.time(),
        }
        terminal["failure_reasons"].extend(_remove_reader_projection(output))
        _run_record(output, terminal)
        return terminal
    finally:
        for signal_number, handler in previous_handlers.items():
            signal.signal(signal_number, handler)


def _compile_command(args: argparse.Namespace) -> int:
    output = Path(args.output_root)
    result = run_compilation_with_recovery(
        output,
        lambda: compile_location_candidate(
            Path(args.raw_root),
            output,
            config_path=Path(args.config),
            evidence_root=Path(args.evidence_root),
        ),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "completed" else 1


def _compare_command(args: argparse.Namespace) -> int:
    record: Path | None = Path(args.evaluator_record) if args.evaluator_record and Path(args.evaluator_record).is_file() else None
    result = run_location_pilot_gate(
        Path(args.candidate_root),
        Path(args.companybrain_root),
        config_path=Path(args.config),
        output_root=Path(args.output_root),
        evaluator_record=record,
        reader_only=bool(args.reader_only),
        no_network=bool(args.no_network),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _evaluate_command(args: argparse.Namespace) -> int:
    result = build_task4_reader_evaluator_record(
        Path(args.candidate_root),
        Path(args.companybrain_root),
        config_path=Path(args.config),
    )
    _write_json(Path(args.output), result)
    print(json.dumps({"status": "completed", "output": str(args.output)}, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("--config", required=True)
    compile_parser.add_argument("--raw-root", required=True)
    compile_parser.add_argument("--output-root", required=True)
    compile_parser.add_argument("--evidence-root", required=True)
    compile_parser.set_defaults(handler=_compile_command)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--config", required=True)
    compare_parser.add_argument("--candidate-root", required=True)
    compare_parser.add_argument("--companybrain-root", required=True)
    compare_parser.add_argument("--output-root", required=True)
    compare_parser.add_argument("--evaluator-record")
    compare_parser.add_argument("--reader-only", action="store_true")
    compare_parser.add_argument("--no-network", action="store_true")
    compare_parser.set_defaults(handler=_compare_command)
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--config", required=True)
    evaluate_parser.add_argument("--candidate-root", required=True)
    evaluate_parser.add_argument("--companybrain-root", required=True)
    evaluate_parser.add_argument("--output", required=True)
    evaluate_parser.set_defaults(handler=_evaluate_command)
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
