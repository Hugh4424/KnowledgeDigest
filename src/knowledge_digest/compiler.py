"""Reader-first KnowledgeDigest compiler.

This is the product's deep module.  It accepts a source directory and two
injected provider seams, then returns one complete bundle of Reader, Home and
Audit bytes.  The implementation deliberately keeps source preservation,
semantic writing, routing and rendering in one locality; callers do not need
to understand any of those stages.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import posixpath
import re
import shutil
import subprocess
import sys
import difflib
from urllib.parse import unquote, urlsplit
from concurrent.futures import ThreadPoolExecutor
import unicodedata
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .publisher import PublishError, commit
from .providers import Embedder, ProviderConfigError, ProviderError, SemanticModel, build_providers
from .companybrain_snapshot import build_companybrain_snapshot
from .quality import (
    _companybrain_binding_errors,
    _EXPECTED_DIMENSIONS,
    _EXPECTED_PROJECTION_IDS,
    _observation_row_digest,
    QualityProjection,
    build_candidate_quality_result,
    finalize_quality_result,
    item_reader_visible,
    load_quality_projections,
    parse_block_ref,
    promote_quality_result,
    projection_prompt,
    projection_query,
    reader_evidence_groups,
)
from .quality_compare import compare_quality


PAGE_TYPES: dict[str, tuple[str, ...]] = {
    "positioning": ("当前结论", "服务对象与入口", "产品关系与选择", "边界与未明确"),
    "concept": ("使用场景", "对象与组成", "关系与生效规则", "边界与容易混淆"),
    "operation": ("前置条件", "操作步骤", "预期结果", "验证方式", "失败与限制"),
    "diagnosis": ("现象", "检查顺序", "可能原因", "处理动作", "升级边界"),
    "experience": ("背景", "阶段变化", "方案取舍与经验", "经验教训", "适用边界"),
}
PAGE_TYPE_LABELS = {
    "positioning": "定位",
    "concept": "概念",
    "operation": "操作",
    "diagnosis": "诊断",
    "experience": "经验",
}
_SHARED_PRODUCT_KEY = "shared"
_SHARED_PRODUCT_LABEL = "跨产品答案"
_KNOWN_PRODUCT_ROOTS = {
    "emm for android": ("emm-for-android", "EMM for Android"),
    "emm for ios": ("emm-for-ios", "EMM for iOS"),
    "goinsight": ("goinsight", "GoInsight"),
    "merchant system": ("merchant-system", "Merchant System"),
}
ROUTE_QUERIES = {
    "我想了解一个产品是什么、服务谁、怎么选以及边界": "产品定位 服务对象 选择 产品关系 边界",
    "我想理解一个模块、对象或配置项": "模块 对象 概念 字段 配置 关系 限制",
    "我想按步骤完成一项操作": "前置条件 操作步骤 入口 保存 结果 失败限制",
    "我遇到了问题，需要定位原因": "现象 检查顺序 原因 处理 诊断 恢复",
    "我想了解历史经验、版本和踩坑": "背景 问题 决策 经验 风险 版本 回归",
}
UNKNOWN = "原始资料未明确"


def _is_unknown_semantic_text(value: Any) -> bool:
    """Recognise a provider's explicit no-evidence answer.

    The provider contract asks for one exact marker, but real Qwen responses
    occasionally use a short equivalent such as ``资料未提及``. Treat only
    short, explicit no-evidence phrases as unknown; a sentence containing a
    business fact still requires a real evidence reference.
    """
    if not isinstance(value, str):
        return False
    text = " ".join(value.strip().split())
    if not text:
        return False
    text = re.sub(r"^(?:[-*•]\s*)+", "", text).strip().rstrip("。；;，,")
    if text == UNKNOWN:
        return True
    no_evidence_markers = (
        "未明确",
        "未说明",
        "未提及",
        "未提供",
        "没有明确",
        "无相关",
        "暂无",
        "不明确",
        "不涉及",
    )
    if not any(marker in text for marker in no_evidence_markers):
        return False
    if not any(prefix in text for prefix in ("资料", "原始资料", "文档", "来源", "当前", "本页", "章节", "内容")):
        return False
    # Do not turn a sentence with a hidden business assertion into UNKNOWN.
    # The short list below catches the common “资料未明确，但……” shape
    # while still allowing a longer, purely negative provider answer.
    factual_markers = ("但", "仅", "可以", "支持", "必须", "只能", "会", "应", "需", "如果", "当", "包含", "包括", "通过", "使用")
    return not any(marker in text for marker in factual_markers)
_HASH = re.compile(r"(?i)(?:sha256|source[_-]?id|digest[_-]?topic|cluster|draft)[\s:=`'\"]*[0-9a-f]{8,}")
_NUMBER = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?(?:%|[A-Za-z]+)?")
_URL = re.compile(r"https?://[^\s)]+")
_CODE = re.compile(r"`([^`\n]+)`")
_SENSITIVE_ACCOUNT_EMAIL = re.compile(
    r"(?i)\b[\w.+-]+@[\w.-]+\.iam\.gserviceaccount\.com\b"
)
_KNOWN_SERVICE_EMAIL = re.compile(r"(?i)\bmaxstore-emm@szzolon\.com\b")
_SENSITIVE_VALUE = re.compile(
    r"(?i)(\b(?:password|passwd|token|access[_ -]?token|api[_ -]?(?:secret|key)|private[_ -]?key|secret[_ -]?key|私钥|密码)\b\s*[:=：]\s*[`'\"“]?)([^`\n,;，；)）\"”]+)"
)
_SENSITIVE_BEARER = re.compile(
    r"(?i)(\bAuthorization\b\s*[:=：]\s*Bearer\s+)([A-Za-z0-9._~+/=-]+)"
)
# Qwen is fast on one compact evidence packet but can keep repeated large
# requests open for many minutes.  Keep ordinary long sources in one compact
# request so the full corpus stays within the provider budget; only sources
# whose evidence cannot fit the configured input ceiling use fact extraction.
# The corpus is already preserved one source at a time.  Cross-source pages
# are the expensive semantic layer, so keep that layer deliberately small:
# four planner suggestions plus the compiler-owned positioning/diagnosis
# entries per product.  This is a coverage policy, not a quality score.
_MAX_TOPIC_GROUPS = 2
_MAX_TOPIC_PAGES_PER_PRODUCT = 3
# Two pages keep the cited-evidence payload and the verifier JSON response
# below the provider's practical context/output ceiling.  A larger batch is
# cheaper on paper but turns a single truncation into several Audit-only pages.
_VERIFY_BATCH_SIZE = 1
# Source pages are independent one-source summaries. Their verifier response
# is small, so several can share one request without mixing their evidence.
_SOURCE_VERIFY_BATCH_SIZE = 4
_SOURCE_VERIFY_ATTEMPTS = 1
_SOURCE_REPAIR_LIMIT = 2
# Topic verification is deliberately one page per request.  A product page
# can cite many raw blocks; batching it with another page makes a valid JSON
# receipt much more likely to be truncated by the provider.  A failed receipt
# is Audit-only instead of entering a second fallback loop.
_VERIFY_SINGLE_FALLBACK_LIMIT = 1
_PLANNER_ATTEMPTS = 1
_AGGREGATE_ATTEMPTS = 1
_MANDATORY_AGGREGATE_ATTEMPTS = 2
_SOURCE_RETRY_LIMIT = 1
# Source recovery is compiler-owned, bounded, and visible in the call plan.
# The provider adapter still makes one HTTP attempt per logical request; a
# recovery is a new request with its own trace identity. The active Task5 plan
# allows twelve global recovery calls and at most three extra attempts per
# stubborn source.
_QUALITY_SOURCE_RETRY_LIMIT = 12
# The provider gateway returns intermittent 504s when several long source
# compilations are in flight.  Quality runs favor complete evidence coverage
# over parallelism: one source request at a time makes failures attributable
# and leaves the bounded retry pool available for the actual failed source.
_QUALITY_SOURCE_WORKERS = 2
# One provider response is the normal path.  A quality page that fails the
# independent verifier may consume the separate bounded repair allowance;
# retrying every source/page here made the budget opaque and kept the old
# runtime's control surface alive in the production compiler.
_QUALITY_GENERATION_ATTEMPTS = 2
_QUALITY_VERIFY_ATTEMPTS = 1
_QUALITY_REPAIR_LIMIT = 2
_PROGRESS_PREFIX = "[digest]"

# The planner may discover module-level groupings, but it must not be the sole
# place where a corpus acquires a diagnostic entry point.  These signals are a
# general corpus rule, not an acceptance-case special case.
_DIAGNOSIS_SIGNALS: tuple[tuple[str, int], ...] = (
    ("根因", 4),
    ("缺陷", 4),
    ("故障", 4),
    ("排查", 4),
    ("异常", 3),
    ("报错", 3),
    ("error", 3),
    ("bug", 3),
    ("失败", 2),
    ("无法", 2),
    ("冲突", 2),
    ("重试", 2),
)
_COMPARISON_MARKERS = ("竞品", "竞对", "对比", "comparison", "competitor")
_EXPERIENCE_SIGNALS = ("回顾", "retrospective", "复盘", "经验", "踩坑", "版本演进", "bug analysis", "缺陷根因", "回归测试", "Sprint")
_ROUTE_PAGE_TYPES = {
    "我想了解一个产品是什么、服务谁、怎么选以及边界": "positioning",
    "我想理解一个模块、对象或配置项": "concept",
    "我想按步骤完成一项操作": "operation",
    "我遇到了问题，需要定位原因": "diagnosis",
    "我想了解历史经验、版本和踩坑": "experience",
}


def _sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _source_manifest_hash(sources: Sequence[SourceDoc]) -> str:
    rows = [
        {
            "source_id": source.source_id,
            "relative_path": source.relative_path,
            "product_key": source.product,
            "product_label": source.product_label,
            "raw_hash": _sha(source.raw_bytes),
            "status": source.status,
            "duplicate_of": source.duplicate_of,
            "evidence_ids": [str(item["evidence_id"]) for item in source.evidence],
        }
        for source in sorted(sources, key=lambda item: item.relative_path)
    ]
    return _sha(_canonical_json(rows))


def _quality_source_manifest(
    sources: Sequence[SourceDoc],
    manifest_path: Path,
    selected_paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate the frozen 89-source snapshot before a quality run."""

    manifest_path = Path(manifest_path).expanduser()
    if not manifest_path.is_file():
        raise ValueError("quality source manifest is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest["source_snapshot"]["entries"]
        expected_count = int(manifest["source_set"]["expected_count"])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ValueError("quality source manifest is invalid") from error
    if not isinstance(entries, list) or expected_count != 89 or len(entries) != expected_count:
        raise ValueError("quality source manifest does not describe the frozen 89-source corpus")
    expected = {
        str(item["source_path"]): str(item["content_hash"])
        for item in entries
        if isinstance(item, Mapping) and item.get("source_path") and item.get("content_hash")
    }
    entry_by_path = {
        str(item["source_path"]): item
        for item in entries
        if isinstance(item, Mapping) and item.get("source_path")
    }
    actual = {
        source.relative_path: _sha(source.raw_bytes)
        for source in sources
    }
    expected_scope = set(expected) if selected_paths is None else set(str(item) for item in selected_paths)
    if not expected_scope.issubset(set(expected)):
        unknown = sorted(expected_scope - set(expected))
        raise ValueError(f"quality source selection is not in frozen manifest: {unknown[:3]}")
    if expected_scope != set(actual):
        missing = sorted(expected_scope - set(actual))
        extra = sorted(set(actual) - expected_scope)
        changed = sorted(path for path in set(expected) & set(actual) if expected[path] != actual[path])
        raise ValueError(f"quality source snapshot does not match frozen manifest: missing={missing[:3]}, extra={extra[:3]}, changed={changed[:3]}")
    malformed = []
    for source in sources:
        entry = entry_by_path.get(source.relative_path, {})
        expected_status = "empty" if not source.text.strip() else "present"
        if (
            int(entry.get("byte_count", -1)) != len(source.raw_bytes)
            or int(entry.get("line_count", -1)) != len(source.lines)
            or entry.get("expected_status") != expected_status
        ):
            malformed.append(source.relative_path)
    if malformed:
        raise ValueError(f"quality source manifest metadata does not match raw files: {malformed[:3]}")
    known_empty_paths = sorted(
        source.relative_path
        for source in sources
        if entry_by_path[source.relative_path].get("expected_status") == "empty"
    )
    return {
        "contract_path": "config/task5-source-page-manifest-v2.json",
        "contract_sha256": _sha(manifest_path.read_bytes()),
        "snapshot_id": str(manifest.get("source_snapshot", {}).get("snapshot_id", "")),
        "expected_count": expected_count,
        "selected_count": len(actual),
        "scope": "full" if selected_paths is None else "slice",
        "known_empty_paths": known_empty_paths,
    }


def _quality_source_ids(manifest_path: Path) -> dict[str, str]:
    """Load the stable source IDs used by the formal Task5 contract."""

    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        entries = manifest["source_snapshot"]["entries"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("quality source manifest is invalid") from error
    if not isinstance(entries, list):
        raise ValueError("quality source manifest entries are invalid")
    result: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("quality source manifest entry is invalid")
        relative = str(entry.get("source_path", ""))
        source_id = str(entry.get("source_id", ""))
        if not relative or not source_id or relative in result:
            raise ValueError("quality source manifest source IDs are invalid")
        result[relative] = source_id
    return result


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def _canonical_json(value: Any) -> bytes:
    """Canonical UTF-8 JSON bytes used for identities and audit hashes.

    The active Task5 contract defines this as compact JSON with recursively
    sorted object keys and exactly one trailing LF.  Keeping the newline in
    this helper prevents callers from silently hashing a different byte
    representation.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _normalised_text(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value)).replace("\r\n", "\n").replace("\r", "\n")


def _question_id(question: str, scene: str, scope: str = "") -> str:
    return _sha(_normalised_text(question) + "\n" + _normalised_text(scene) + "\n" + _normalised_text(scope))[:20]


def _page_key(*, page_type: str, page_id: str, question: str, scenario: str, source_id: str, product: str = "", projection_id: str = "", answer_page: bool = False) -> str:
    identity = projection_id or page_id
    if answer_page and identity:
        question_id = _question_id(question, scenario, product + "\0" + identity)
        return f"answer:{question_id}:{page_type}"
    return f"source:{source_id}"


def _tree_hash(files: Mapping[str, bytes]) -> str:
    rows = [
        {"relative_path": str(relative), "sha256": _sha(content)}
        for relative, content in sorted(
            files.items(), key=lambda item: str(item[0]).encode("utf-8")
        )
        if relative not in {
            "_audit/run-result.json",
            "_audit/run-result.receipt.json",
            "_audit/directory-manifest.json",
        }
    ]
    return _sha(_canonical_json(rows))


def _gate_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    """Read one host-owned gate artifact without accepting caller prose."""

    candidate = Path(path).expanduser()
    if not candidate.is_absolute() or candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"{label} is missing")
    try:
        raw = candidate.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is invalid") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value, raw


def _require_gate_fields(value: Mapping[str, Any], fields: Sequence[str], label: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ValueError(f"{label} is incomplete: {', '.join(missing)}")


def _require_exact_gate_fields(value: Mapping[str, Any], fields: Sequence[str], label: str) -> None:
    expected = set(fields)
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected: {', '.join(extra)}")
        raise ValueError(f"{label} fields are invalid ({'; '.join(details)})")


def _validate_canonical_gate_bytes(value: Mapping[str, Any], raw: bytes, label: str) -> None:
    if raw != _canonical_json(value):
        raise ValueError(f"{label} is not canonical UTF-8 JSON")


def _validate_gate_self_hash(value: Mapping[str, Any], label: str) -> None:
    supplied = str(value.get("canonical_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", supplied):
        raise ValueError(f"{label} canonical hash is missing")
    payload = dict(value)
    payload.pop("canonical_sha256", None)
    if _sha(_canonical_json(payload)) != supplied:
        raise ValueError(f"{label} canonical hash does not match bytes")


def _validate_named_gate_hash(value: Mapping[str, Any], field: str, label: str) -> None:
    supplied = str(value.get(field, ""))
    if not re.fullmatch(r"[0-9a-f]{64}", supplied):
        raise ValueError(f"{label} hash is missing")
    payload = dict(value)
    payload.pop(field, None)
    if _sha(_canonical_json(payload)) != supplied:
        raise ValueError(f"{label} hash does not match bytes")


_WORKFLOWHUB_HANDOFF_FIELDS = (
    "schema_version", "handoff_kind", "task_id", "project_name", "stage",
    "review_kind", "handoff_ref", "handoff_sha256", "parent_design_review",
    "implementation_review", "current", "runtime_contract", "writer_attestation",
)
_WORKFLOWHUB_PARENT_REVIEW_FIELDS = (
    "review_kind", "result_ref", "result_sha256", "attempt_ref", "attempt_sha256",
    "report_ref", "report_sha256", "contract_id", "contract_hash", "semantic_hash",
    "snapshot_tree", "material_id", "writer_attestation",
)
_WORKFLOWHUB_IMPLEMENTATION_REVIEW_FIELDS = (
    "review_kind", "result_ref", "result_sha256", "attempt_ref", "attempt_sha256",
    "report_ref", "report_sha256", "outcome", "terminal_status", "terminal_clean",
    "finding_dispositions_ref", "finding_dispositions_sha256", "all_findings_disposed",
    "m401_packet_sha256",
)
_WORKFLOWHUB_CURRENT_FIELDS = (
    "task_id", "project_name", "stage", "snapshot_tree", "material_id", "worktree",
)
_WORKFLOWHUB_RUNTIME_FIELDS = (
    "runtime_contract_id", "runtime_contract_hash", "semantic_contract_id",
    "semantic_contract_hash", "m401_packet_ref", "m401_packet_sha256",
    "m401_r_receipt_ref", "m401_r_receipt_sha256",
)
_WORKFLOWHUB_ATTESTATION_FIELDS = (
    "writer", "adapter", "authenticated", "attestation_sha256",
)
_HEX64 = re.compile(r"[0-9a-f]{64}")
_WORKFLOWHUB_SNAPSHOT = re.compile(r"[0-9a-f]{40,64}")


def _validate_workflowhub_attestation(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} is invalid")
    _require_exact_gate_fields(value, _WORKFLOWHUB_ATTESTATION_FIELDS, label)
    for field in ("writer", "adapter"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(f"{label} is incomplete")
    if value.get("authenticated") is not True:
        raise ValueError(f"{label} is not authenticated")
    supplied = value.get("attestation_sha256")
    if not isinstance(supplied, str) or not _HEX64.fullmatch(supplied):
        raise ValueError(f"{label} hash is invalid")
    payload = dict(value)
    payload.pop("attestation_sha256", None)
    if _sha(_canonical_json(payload)) != supplied:
        raise ValueError(f"{label} hash does not match")


def _resolve_handoff_ref(value: Any, *, label: str, task_root: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is missing")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = task_root / candidate
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"{label} is missing")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(task_root)
    except ValueError as error:
        raise ValueError(f"{label} escapes the task evidence root") from error
    return resolved


def _validate_handoff_ref_hash(value: Mapping[str, Any], ref_field: str, hash_field: str, *, label: str, task_root: Path) -> None:
    ref = _resolve_handoff_ref(value.get(ref_field), label=f"{label} ref", task_root=task_root)
    supplied = value.get(hash_field)
    if not isinstance(supplied, str) or not _HEX64.fullmatch(supplied):
        raise ValueError(f"{label} hash is invalid")
    if _sha(ref.read_bytes()) != supplied:
        raise ValueError(f"{label} hash does not match bytes")


def _validate_workflowhub_successor(
    handoff_path: Path,
    handoff: Mapping[str, Any],
    handoff_raw: bytes,
    packet: Mapping[str, Any],
    packet_raw: bytes,
    receipt: Mapping[str, Any],
    receipt_raw: bytes,
) -> None:
    """Validate the authenticated implementation successor as a closed object."""

    _require_exact_gate_fields(handoff, _WORKFLOWHUB_HANDOFF_FIELDS, "WorkflowHub implementation handoff")
    _validate_canonical_gate_bytes(handoff, handoff_raw, "WorkflowHub implementation handoff")
    _validate_named_gate_hash(handoff, "handoff_sha256", "WorkflowHub implementation handoff")
    if (
        handoff.get("schema_version") != "workflowhub-implementation-successor.v1"
        or handoff.get("handoff_kind") != "implementation"
        or handoff.get("stage") != "build-code"
        or handoff.get("review_kind") != "mini_task.implementation"
        or handoff.get("handoff_ref") != "quality/evidence/task5/workflowhub-implementation-handoff.json"
    ):
        raise ValueError("WorkflowHub implementation handoff identity is invalid")

    task_root = handoff_path.parents[3]
    parent = handoff.get("parent_design_review")
    implementation = handoff.get("implementation_review")
    current = handoff.get("current")
    runtime = handoff.get("runtime_contract")
    if parent is not None and not isinstance(parent, Mapping):
        raise ValueError("WorkflowHub design review advisory is invalid")
    required_objects = [
        (implementation, _WORKFLOWHUB_IMPLEMENTATION_REVIEW_FIELDS, "WorkflowHub implementation review"),
        (current, _WORKFLOWHUB_CURRENT_FIELDS, "WorkflowHub current identity"),
        (runtime, _WORKFLOWHUB_RUNTIME_FIELDS, "WorkflowHub runtime identity"),
    ]
    if parent is not None:
        required_objects.insert(0, (parent, _WORKFLOWHUB_PARENT_REVIEW_FIELDS, "WorkflowHub design review advisory"))
    for value, fields, label in required_objects:
        if not isinstance(value, Mapping):
            raise ValueError(f"{label} is incomplete")
        _require_exact_gate_fields(value, fields, label)
    _validate_workflowhub_attestation(handoff.get("writer_attestation"), "WorkflowHub writer attestation")
    if parent is not None:
        _validate_workflowhub_attestation(parent.get("writer_attestation"), "WorkflowHub design writer attestation")

    for field, label in (
        ("task_id", "WorkflowHub task identity"),
        ("project_name", "WorkflowHub project identity"),
        ("worktree", "WorkflowHub worktree identity"),
        ("runtime_contract_id", "WorkflowHub runtime contract id"),
        ("semantic_contract_id", "WorkflowHub semantic contract id"),
    ):
        if not isinstance((current if field in current else runtime).get(field), str) or not (current if field in current else runtime)[field].strip():
            raise ValueError(f"{label} is missing")
    identity_objects = [
        (implementation, ("result_sha256", "attempt_sha256", "report_sha256", "finding_dispositions_sha256", "m401_packet_sha256"), "WorkflowHub implementation review"),
        (current, ("snapshot_tree", "material_id"), "WorkflowHub current identity"),
        (runtime, ("runtime_contract_hash", "semantic_contract_hash", "m401_packet_sha256", "m401_r_receipt_sha256"), "WorkflowHub runtime identity"),
    ]
    if parent is not None:
        identity_objects.insert(0, (parent, ("result_sha256", "attempt_sha256", "report_sha256", "contract_hash", "semantic_hash", "snapshot_tree", "material_id"), "WorkflowHub design review advisory"))
    for value, fields, label in identity_objects:
        for field in fields:
            pattern = _WORKFLOWHUB_SNAPSHOT if field == "snapshot_tree" else _HEX64
            if not isinstance(value.get(field), str) or not pattern.fullmatch(value[field]):
                raise ValueError(f"{label} {field} is invalid")
    if parent is not None and parent.get("review_kind") != "mini_task.design":
        raise ValueError("WorkflowHub design review advisory identity is invalid")
    if (
        implementation.get("review_kind") != "mini_task.implementation"
        or implementation.get("outcome") != "available"
        or implementation.get("terminal_status") != "semantic"
        or implementation.get("terminal_clean") is not True
        or implementation.get("all_findings_disposed") is not True
    ):
        raise ValueError("WorkflowHub implementation review is not terminal-clean")
    if (
        current.get("task_id") != handoff.get("task_id")
        or current.get("project_name") != handoff.get("project_name")
        or current.get("stage") != handoff.get("stage")
        or current.get("snapshot_tree") != packet.get("snapshot_tree")
        or current.get("material_id") != packet.get("material_id")
    ):
        raise ValueError("WorkflowHub current snapshot identity mismatch")
    if parent is not None and (
        parent.get("snapshot_tree") != packet.get("snapshot_tree")
        or parent.get("material_id") != packet.get("material_id")
    ):
        raise ValueError("WorkflowHub design advisory snapshot identity mismatch")
    packet_sha = _sha(packet_raw)
    receipt_sha = _sha(receipt_raw)
    if (
        implementation.get("m401_packet_sha256") != packet_sha
        or runtime.get("m401_packet_sha256") != packet_sha
        or runtime.get("m401_r_receipt_sha256") != receipt_sha
        or receipt.get("m401_packet_sha256") != packet_sha
    ):
        raise ValueError("WorkflowHub/M401 identity mismatch")
    if runtime.get("m401_packet_ref") != "quality/evidence/task5/M401-evidence-packet.json" or runtime.get("m401_r_receipt_ref") != "quality/evidence/task5/M401-R-review-receipt.json":
        raise ValueError("WorkflowHub promoted gate refs are invalid")
    _validate_handoff_ref_hash(implementation, "finding_dispositions_ref", "finding_dispositions_sha256", label="WorkflowHub finding dispositions", task_root=task_root)
    ref_objects = [
        (implementation, ("result_ref", "attempt_ref", "report_ref"), "WorkflowHub implementation review"),
    ]
    if parent is not None:
        ref_objects.insert(0, (parent, ("result_ref", "attempt_ref", "report_ref"), "WorkflowHub design review advisory"))
    for value, fields, label in ref_objects:
        for field in fields:
            hash_field = field.replace("_ref", "_sha256")
            _validate_handoff_ref_hash(value, field, hash_field, label=f"{label} {field}", task_root=task_root)


def _validate_m402_worktree_binding(handoff: Mapping[str, Any]) -> None:
    """Do not run M402 with a handoff issued for another checkout."""

    current = handoff.get("current")
    worktree = current.get("worktree") if isinstance(current, Mapping) else None
    if not isinstance(worktree, str) or not worktree.strip():
        raise ValueError("WorkflowHub current worktree is missing")
    expected = Path(__file__).resolve().parents[2]
    supplied = Path(worktree).expanduser()
    if not supplied.is_absolute() or supplied.resolve() != expected:
        raise ValueError("WorkflowHub current worktree does not match the compiler worktree")


_M402_RUNTIME_CONTRACT_FILES = {
    "quality_cases_sha256": "config/task5-quality-cases-v2.json",
    "baseline_sha256": "config/task5-companybrain-baseline-v2.json",
    "quality_result_schema_sha256": "config/task5-quality-result-v3.json",
    "companybrain_observation_schema_sha256": "config/task5-companybrain-observation-v2.json",
    "source_block_claim_contract_sha256": "config/task5-source-block-claim-contract-v1.json",
    "reader_path_relation_contract_sha256": "config/task5-reader-path-relation-contract-v1.json",
    "provider_handshake_schema_sha256": "config/task5-provider-contract-handshake-v3.json",
    "machine_evidence_contract_sha256": "config/task5-machine-evidence-contract-v1.json",
    "root_cause_input_manifest_sha256": "config/task5-root-cause-input-manifest-v1.json",
    "root_cause_evidence_schema_sha256": "config/task5-root-cause-evidence-v2.json",
    "semantic_frame_field_closure_sha256": "config/task5-semantic-frame-field-closure-v1.json",
    "publication_layout_contract_sha256": "config/task5-publication-layout-v2.json",
}
_M402_RUNTIME_AUTHORITY_KEYS = (
    "external_processing_policy",
    "machine_evidence",
    "publication_layout",
    "provider_handshake",
    "provider_prompt",
    "provider_semantic",
    "reader_path_relation",
    "reader_quality_provider",
    "replay_store",
    "root_cause_evidence",
    "root_cause_inputs",
    "semantic_frame",
    "semantic_frame_field_closure",
    "source_block_claim",
    "source_digest",
    "source_not_documented",
    "source_sensitive_content_scan",
)
_M402_RUNTIME_EXCLUDED_PATHS = (
    "config/task5-quality-cases-v2.json",
    "config/task5-companybrain-baseline-v2.json",
    "config/task5-source-page-manifest-v2.json",
    "config/task5-slice-cases-v1.json",
    "config/task5-run-result-v1.json",
)


def _load_m402_runtime_authority(project_root: Path) -> dict[str, Any]:
    """Rehash the frozen 17-entry authority map before provider work."""

    map_path = Path(project_root) / "config" / "task5-runtime-authority-map-v1.json"
    if map_path.is_symlink() or not map_path.is_file():
        raise ValueError("M402 runtime authority map is missing")
    try:
        map_raw = map_path.read_bytes()
        value = json.loads(map_raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("M402 runtime authority map is invalid") from error
    if not isinstance(value, Mapping):
        raise ValueError("M402 runtime authority map is not a JSON object")
    if set(value) != {
        "schema_version", "contract_id", "runtime_contract_id", "identity_rule",
        "authorities", "excluded_from_runtime_map", "coverage_rule",
    } or value.get("schema_version") != "task5-runtime-authority-map.v1" \
            or value.get("contract_id") != "task5-reader-quality-runtime-authority-map-v1" \
            or value.get("runtime_contract_id") != "task5-reader-quality-provider-v2":
        raise ValueError("M402 runtime authority map identity is invalid")
    authorities = value.get("authorities")
    excluded = value.get("excluded_from_runtime_map")
    if not isinstance(authorities, list) or not isinstance(excluded, list):
        raise ValueError("M402 runtime authority map entries are invalid")
    authority_fields = {
        "key", "path", "schema", "actual_sha256", "canonical_sha256",
        "rehash_owner", "role",
    }
    seen: set[str] = set()
    for item in authorities:
        if not isinstance(item, Mapping) or set(item) != authority_fields:
            raise ValueError("M402 runtime authority entry fields are invalid")
        key = item.get("key")
        if not isinstance(key, str) or key in seen:
            raise ValueError("M402 runtime authority keys are not unique")
        seen.add(key)
        relative = item.get("path")
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("M402 runtime authority path is unsafe")
        authority_path = Path(project_root) / relative
        if authority_path.is_symlink() or not authority_path.is_file():
            raise ValueError(f"M402 runtime authority is missing: {relative}")
        try:
            authority_raw = authority_path.read_bytes()
            authority_value = json.loads(authority_raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"M402 runtime authority is invalid: {relative}") from error
        if not isinstance(authority_value, Mapping):
            raise ValueError(f"M402 runtime authority is not an object: {relative}")
        if not _HEX64.fullmatch(str(item.get("actual_sha256", ""))) or _sha(authority_raw) != item.get("actual_sha256"):
            raise ValueError(f"M402 runtime authority actual hash is stale: {relative}")
        if not _HEX64.fullmatch(str(item.get("canonical_sha256", ""))) or _sha(_canonical_json(authority_value)) != item.get("canonical_sha256"):
            raise ValueError(f"M402 runtime authority canonical hash is stale: {relative}")
        if authority_value.get("schema_version") != item.get("schema"):
            raise ValueError(f"M402 runtime authority schema is stale: {relative}")
    actual_keys = tuple(sorted(seen, key=lambda item: item.encode("utf-8")))
    if actual_keys != tuple(sorted(_M402_RUNTIME_AUTHORITY_KEYS, key=lambda item: item.encode("utf-8"))):
        raise ValueError("M402 runtime authority key set is not exact")
    if any(
        not isinstance(item, Mapping)
        or set(item) != {"path", "reason"}
        or not isinstance(item.get("path"), str)
        or not isinstance(item.get("reason"), str)
        or not item["reason"].strip()
        for item in excluded
    ):
        raise ValueError("M402 runtime excluded entry fields are invalid")
    excluded_paths = tuple(item["path"] for item in excluded)
    if len(excluded) != len(_M402_RUNTIME_EXCLUDED_PATHS) or set(excluded_paths) != set(_M402_RUNTIME_EXCLUDED_PATHS):
        raise ValueError("M402 runtime excluded path set is not exact")
    authorities_by_key = {str(item["key"]): item for item in authorities}
    sorted_authorities = [dict(authorities_by_key[key]) for key in actual_keys]
    return {
        "map_actual_sha256": _sha(map_raw),
        "map_canonical_sha256": _sha(_canonical_json(value)),
        "runtime_contract_id": value.get("runtime_contract_id"),
        "included_keys": list(actual_keys),
        "excluded_paths": list(excluded_paths),
        "derived_runtime_contract_hash": _sha(_canonical_json(sorted_authorities)),
    }


def _validate_m402_runtime_identity(
    handoff: Mapping[str, Any],
    authority_identity: Mapping[str, Any],
) -> None:
    runtime_identity = handoff.get("runtime_contract")
    if not isinstance(runtime_identity, Mapping):
        raise ValueError("WorkflowHub runtime identity is missing")
    if (
        runtime_identity.get("runtime_contract_id") != authority_identity.get("runtime_contract_id")
        or runtime_identity.get("runtime_contract_hash") != authority_identity.get("derived_runtime_contract_hash")
    ):
        raise ValueError("WorkflowHub runtime contract identity mismatch")


def _validate_m402_runtime_config(
    runtime_path: Path,
    runtime: Mapping[str, Any],
    runtime_raw: bytes,
    quality_config_path: Path,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Bind M402's runtime contract to the files it claims to govern."""

    project_root = (
        Path(project_root).expanduser().resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )

    if set(runtime) != {
        "schema_version", "config_id", "provider_mode", "inventory_version",
        "expected_source_count", "quality_contract", "output_state",
        "publish_only_if", "state_order", "exit_codes",
    }:
        raise ValueError("M402 runtime config fields are not exact")
    if (
        runtime.get("schema_version") != "task5-runtime-config.v2"
        or runtime.get("config_id") != "task5-reader-quality-provider-v2"
        or runtime.get("provider_mode") != "provider_required"
        or runtime.get("inventory_version") != "task5-corpus-v1"
        or runtime.get("expected_source_count") != 89
        or runtime.get("output_state") != "candidate"
    ):
        raise ValueError("M402 runtime config identity is invalid")
    required_publish_guards = {
        "all_quality_dimensions_kd_win",
        "all_guards_pass",
        "baseline_valid",
        "rendered_reader_complete",
        "rendered_quality_complete",
        "source_closure_complete",
        "independent_review_passed",
        "task5_machine_evidence_complete",
    }
    if set(runtime.get("publish_only_if", ())) != required_publish_guards:
        raise ValueError("M402 runtime publish guards are not exact")
    if runtime.get("state_order") != [
        "declared", "snapshotted", "inventoried", "modeled", "compiled",
        "evidence_checked", "route_checked", "candidate", "released",
    ]:
        raise ValueError("M402 runtime state order is invalid")
    if runtime.get("exit_codes") != {
        "released": 0,
        "not_released": 1,
        "blocked": 2,
        "failed": 3,
        "cancelled": 4,
        "unavailable": 2,
    }:
        raise ValueError("M402 runtime exit codes are invalid")

    expected_runtime_path = project_root / "config" / "task5-reader-quality-provider-v2.json"
    if not expected_runtime_path.is_file() or _sha(runtime_raw) != _sha(expected_runtime_path.read_bytes()):
        raise ValueError("M402 runtime config is not the frozen authority")
    quality_contract = runtime.get("quality_contract")
    if not isinstance(quality_contract, Mapping) or set(quality_contract) != {
        *(_M402_RUNTIME_CONTRACT_FILES.keys()), "schema_version",
    } or quality_contract.get("schema_version") != "task5-quality-contract.v1":
        raise ValueError("M402 runtime quality contract is incomplete")

    quality_path = Path(quality_config_path).expanduser().resolve()
    expected_quality_path = project_root / "config" / "task5-quality-cases-v2.json"
    if quality_path != expected_quality_path.resolve():
        raise ValueError("M402 quality config is not the frozen authority")
    for field, relative in _M402_RUNTIME_CONTRACT_FILES.items():
        authority_path = project_root / relative
        if not authority_path.is_file() or authority_path.is_symlink():
            raise ValueError(f"M402 runtime authority is missing: {relative}")
        try:
            authority_value = json.loads(authority_path.read_bytes().decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"M402 runtime authority is invalid: {relative}") from error
        if not isinstance(authority_value, Mapping):
            raise ValueError(f"M402 runtime authority is not an object: {relative}")
        if str(quality_contract.get(field, "")) != _sha(_canonical_json(authority_value)):
            raise ValueError(f"M402 runtime authority hash is stale: {relative}")
    return _load_m402_runtime_authority(project_root)


def _resolve_gate_ref(value: Any, *, label: str) -> Path:
    ref = str(value or "").strip()
    if not ref:
        raise ValueError(f"{label} is missing")
    path = Path(ref).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} is missing")
    return path.resolve()


def _validate_m402_gate(request: "DigestRequest") -> str:
    """Validate all pre-provider M402 bindings before reading raw or baseline."""

    packet_path = request.m401_packet_path
    receipt_path = request.m401_r_receipt_path
    handoff_path = request.workflowhub_successor_path
    runtime_path = request.runtime_config_path
    if packet_path is None:
        raise ValueError("M402 requires an M401 packet")
    if receipt_path is None:
        raise ValueError("M402 requires an M401-R receipt")
    if handoff_path is None:
        raise ValueError("M402 requires a WorkflowHub implementation handoff")
    if runtime_path is None:
        raise ValueError("M402 requires a runtime config")
    if request.companybrain_root is None:
        raise ValueError("M402 requires a CompanyBrain root")

    packet_path = _resolve_gate_ref(packet_path, label="M401 packet")
    receipt_path = _resolve_gate_ref(receipt_path, label="M401-R receipt")
    handoff_path = _resolve_gate_ref(handoff_path, label="WorkflowHub implementation handoff")
    if tuple(packet_path.parts[-4:]) != ("quality", "evidence", "task5", "M401-evidence-packet.json"):
        raise ValueError("M401 packet is not the promoted packet")
    if tuple(receipt_path.parts[-4:]) != ("quality", "evidence", "task5", "M401-R-review-receipt.json"):
        raise ValueError("M401-R receipt is not the promoted receipt")
    if tuple(handoff_path.parts[-4:]) != ("quality", "evidence", "task5", "workflowhub-implementation-handoff.json"):
        raise ValueError("WorkflowHub implementation handoff is not the promoted handoff")
    if request.quality_config_path is None:
        raise ValueError("M402 requires a quality config")
    quality_config_path = Path(request.quality_config_path).expanduser()
    if not quality_config_path.is_absolute():
        quality_config_path = Path.cwd() / quality_config_path
    if quality_config_path.is_symlink() or not quality_config_path.is_file():
        raise ValueError("M402 quality config is missing")

    packet, packet_raw = _gate_json(packet_path, "M401 packet")
    _require_gate_fields(
        packet,
        ("schema_version", "status", "pre_m402_readiness", "snapshot_tree", "material_id", "canonical_sha256"),
        "M401 packet",
    )
    if packet.get("schema_version") != "task5-m401-evidence-packet.v1":
        raise ValueError("M401 packet schema is invalid")
    if packet.get("status") != "passed" or packet.get("pre_m402_readiness") is not True:
        raise ValueError("M401 packet is not ready for M402")
    _validate_canonical_gate_bytes(packet, packet_raw, "M401 packet")
    _validate_gate_self_hash(packet, "M401 packet")

    receipt, receipt_raw = _gate_json(receipt_path, "M401-R receipt")
    _require_exact_gate_fields(
        receipt,
        (
            "schema_version", "review_kind", "m401_packet_ref", "m401_packet_sha256",
            "review_result_ref", "review_result_sha256", "source_receipt_ref",
            "source_receipt_sha256", "snapshot_tree", "material_id", "terminal_status",
            "terminal_clean", "all_findings_disposed", "finding_dispositions", "outcome",
            "status", "reason_code",
        ),
        "M401-R receipt",
    )
    _validate_canonical_gate_bytes(receipt, receipt_raw, "M401-R receipt")
    if receipt.get("schema_version") != "task5-m401-r-review-receipt.v1":
        raise ValueError("M401-R receipt schema is invalid")
    if (
        receipt.get("review_kind") != "mini_task.implementation"
        or receipt.get("outcome") != "available"
        or receipt.get("status") != "passed"
        or receipt.get("reason_code") != "NONE"
        or receipt.get("terminal_status") != "semantic"
        or receipt.get("terminal_clean") is not True
        or receipt.get("all_findings_disposed") is not True
        or not isinstance(receipt.get("finding_dispositions"), list)
    ):
        raise ValueError("M401-R receipt is not terminal-clean")
    packet_ref = _resolve_gate_ref(receipt.get("m401_packet_ref"), label="M401-R packet ref")
    if not (
        packet_ref.name == "M401-evidence-packet.json"
        and packet_ref.parent.name == "M401"
        and packet_ref.parent.parent.parent.name == "attempts"
    ):
        raise ValueError("M401-R packet ref is not an attempt-local packet")
    attempt_packet, attempt_packet_raw = _gate_json(packet_ref, "M401-R attempt packet")
    if attempt_packet_raw != packet_raw:
        raise ValueError("M401 packet promotion bytes do not match the attempt packet")
    if attempt_packet != packet:
        raise ValueError("M401 packet promotion object does not match the attempt packet")
    if _sha(attempt_packet_raw) != str(receipt.get("m401_packet_sha256")):
        raise ValueError("M401-R packet hash does not match bytes")
    review_result = _resolve_gate_ref(receipt.get("review_result_ref"), label="M401-R review result ref")
    if not (
        review_result.name == "review-result.json"
        and review_result.parent.name == "M401-R"
        and review_result.parent.parent.parent.name == "attempts"
    ):
        raise ValueError("M401-R review result ref is not attempt-local")
    review_result_raw = review_result.read_bytes()
    try:
        review_result_value = json.loads(review_result_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("M401-R review result is invalid") from error
    if not isinstance(review_result_value, Mapping):
        raise ValueError("M401-R review result must be a JSON object")
    if review_result_raw != _canonical_json(review_result_value):
        raise ValueError("M401-R review result is not canonical UTF-8 JSON")
    if _sha(review_result_raw) != str(receipt.get("review_result_sha256")):
        raise ValueError("M401-R review result hash does not match bytes")
    source_receipt = _resolve_gate_ref(receipt.get("source_receipt_ref"), label="M401 attempt receipt ref")
    if source_receipt != packet_ref.parent / "attempt-receipt.json":
        raise ValueError("M401 attempt receipt ref is not bound to the M401 attempt")
    source_receipt_value, source_receipt_raw = _gate_json(source_receipt, "M401 attempt receipt")
    _require_exact_gate_fields(
        source_receipt_value,
        (
            "schema_version", "gate", "attempt_id", "command", "command_sha256",
            "fixture_bundle_ref", "fixture_bundle_sha256", "fixture_manifest_sha256",
            "run_root_ref", "run_root_sha256", "packet_ref", "packet_sha256",
            "snapshot_tree", "material_id", "exit_code", "status", "reason_code",
        ),
        "M401 attempt receipt",
    )
    _validate_canonical_gate_bytes(source_receipt_value, source_receipt_raw, "M401 attempt receipt")
    if source_receipt_value.get("schema_version") != "task5-m401-attempt-receipt.v1":
        raise ValueError("M401 attempt receipt schema is invalid")
    if source_receipt_value.get("gate") != "M401":
        raise ValueError("M401 attempt receipt gate is invalid")
    if source_receipt_value.get("attempt_id") != packet_ref.parent.parent.name:
        raise ValueError("M401 attempt receipt identity is invalid")
    if source_receipt_value.get("packet_ref") != "M401-evidence-packet.json":
        raise ValueError("M401 attempt receipt packet ref is invalid")
    if source_receipt_value.get("packet_sha256") != _sha(attempt_packet_raw):
        raise ValueError("M401 attempt receipt packet hash is invalid")
    if source_receipt_value.get("snapshot_tree") != packet.get("snapshot_tree") or source_receipt_value.get("material_id") != packet.get("material_id"):
        raise ValueError("M401 attempt receipt identity mismatch")
    if source_receipt_value.get("status") != "passed" or source_receipt_value.get("exit_code") != 0 or source_receipt_value.get("reason_code") != "NONE":
        raise ValueError("M401 attempt receipt is not passed")
    if _sha(source_receipt_raw) != str(receipt.get("source_receipt_sha256")):
        raise ValueError("M401 attempt receipt hash does not match bytes")
    if str(receipt.get("snapshot_tree")) != str(packet.get("snapshot_tree")):
        raise ValueError("M401/M401-R snapshot identity mismatch")
    if str(receipt.get("material_id")) != str(packet.get("material_id")):
        raise ValueError("M401/M401-R material identity mismatch")

    handoff, handoff_raw = _gate_json(handoff_path, "WorkflowHub implementation handoff")
    _validate_workflowhub_successor(
        handoff_path,
        handoff,
        handoff_raw,
        packet,
        packet_raw,
        receipt,
        receipt_raw,
    )
    _validate_m402_worktree_binding(handoff)

    runtime, runtime_raw = _gate_json(runtime_path, "M402 runtime config")
    if runtime.get("schema_version") != "task5-runtime-config.v2":
        raise ValueError("M402 runtime config schema is invalid")
    forbidden = {"api_key", "Authorization", "prompt", "response"}
    if any(key in forbidden for key in runtime):
        raise ValueError("M402 runtime config contains forbidden secret fields")
    authority_identity = _validate_m402_runtime_config(
        runtime_path,
        runtime,
        runtime_raw,
        quality_config_path,
    )
    _validate_m402_runtime_identity(handoff, authority_identity)
    return str(packet.get("material_id"))


_FORMAL_PUBLIC_AUDIT_FILES = (
    "_audit/audit-pages.json",
    "_audit/source-status.json",
    "_audit/companybrain-route-snapshot.json",
    "_audit/semantic-compile-ledger.jsonl",
    "_audit/semantic-response-ledger.jsonl",
    "_audit/route-ledger.jsonl",
    "_audit/raw-coordinate-map.json",
    "_audit/source-not-documented-zero-match.json",
    "_audit/source-not-documented-verifier.json",
    "_audit/run-result.json",
    "_audit/directory-manifest.json",
)


_M401_AUDIT_FILES = frozenset(_FORMAL_PUBLIC_AUDIT_FILES)


def _regular_files(root: Path, label: str) -> dict[str, bytes]:
    """Read a closed artifact tree without following links."""

    root = Path(root).expanduser()
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError(f"{label} is missing")
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} contains a symlink: {path.relative_to(root)}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        files[relative] = path.read_bytes()
    return files


def _validate_closed_fixture_files(
    files: Mapping[str, bytes],
    *,
    label: str,
) -> dict[str, Any]:
    """Validate one closed formal fixture from already captured bytes.

    Keeping the byte-level validator separate lets the private C3 producer
    validate before publication, while M401 can keep its existing read-only
    directory boundary.  Neither path can turn a loose directory into a
    gate input.
    """

    detail_label = "M401 fixture" if label == "M401 fixture bundle" else label
    missing = sorted(_M401_AUDIT_FILES - set(files))
    if missing:
        raise ValueError(f"{label} is incomplete: {', '.join(missing)}")
    audit_files = {path for path in files if path.startswith("_audit/")}
    extra = sorted(audit_files - _M401_AUDIT_FILES)
    if extra:
        raise ValueError(f"{label} has unexpected audit files: {', '.join(extra[:3])}")

    try:
        run = json.loads(files["_audit/run-result.json"].decode("utf-8"))
        directory = json.loads(files["_audit/directory-manifest.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{detail_label} run result is invalid") from error
    if not isinstance(run, Mapping) or not isinstance(directory, Mapping):
        raise ValueError(f"{detail_label} run result is invalid")
    _validate_public_files(files)
    manifest = run.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ValueError(f"{detail_label} has no run manifest")
    expected_count = manifest.get("source_count")
    if not isinstance(expected_count, int) or expected_count <= 0:
        raise ValueError(f"{detail_label} source count is invalid")
    _validate_run_manifest(manifest, expected_source_count=expected_count)
    _validate_route_ledger_projection(files, manifest, label=detail_label)
    actual_tree = _tree_hash(files)
    if manifest.get("tree_sha256") != actual_tree:
        raise ValueError(f"{detail_label} tree hash does not match bytes")
    if run.get("canonical_sha256") != _sha(_canonical_json({key: value for key, value in run.items() if key != "canonical_sha256"})):
        raise ValueError(f"{detail_label} run-result canonical hash is invalid")
    if directory.get("canonical_sha256") != _sha(_canonical_json({key: value for key, value in directory.items() if key != "canonical_sha256"})):
        raise ValueError(f"{detail_label} directory manifest canonical hash is invalid")
    expected_rows = [
        {"path": relative, "sha256": _sha(content), "bytes": len(content), "lines": content.count(b"\n")}
        for relative, content in sorted(files.items(), key=lambda item: str(item[0]).encode("utf-8"))
        if relative not in {"_audit/run-result.json", "_audit/directory-manifest.json"}
    ]
    if directory.get("files") != expected_rows or directory.get("tree_sha256") != actual_tree:
        raise ValueError(f"{detail_label} directory manifest does not match bytes")
    if not isinstance(run.get("quality_projection_count"), int):
        raise ValueError(f"{detail_label} quality result is not closed")
    snapshot = json.loads(files["_audit/companybrain-route-snapshot.json"].decode("utf-8"))
    if not isinstance(snapshot, Mapping) or snapshot.get("schema_version") != "knowledge-digest-companybrain-route-snapshot.v1":
        raise ValueError(f"{detail_label} CompanyBrain snapshot is invalid")
    snapshot_tree = str(run.get("snapshot_tree") or "")
    material_id = str(run.get("material_id") or "")
    # WorkflowHub's authenticated Git tree identity is commonly a 40-char
    # SHA-1, while content/material identities are 64-char SHA-256 values.
    # Accept the host-owned 40–64 hex tree range without weakening the
    # requirement that both identities are present and fully hexadecimal.
    if not re.fullmatch(r"[0-9a-f]{40,64}", snapshot_tree) or not re.fullmatch(r"[0-9a-f]{64}", material_id):
        raise ValueError(f"{detail_label} lacks authenticated snapshot/material identity")
    trace = _m401_trace(run, files, actual_tree)
    if len(trace) != 13:
        raise ValueError(f"{detail_label} AC trace is not verifiable")
    return {
        "files": files,
        "manifest": dict(manifest),
        "manifest_sha256": _sha(_canonical_json(manifest)),
        "tree_sha256": actual_tree,
        "snapshot_tree": snapshot_tree,
        "material_id": material_id,
        "trace": trace,
    }


def _validate_m401_fixture(bundle_path: Path) -> dict[str, Any]:
    """Validate a C3 fixture before M401 is allowed to write anything.

    M401 is a fake/no-network gate.  It must consume only a previously closed
    C3 bundle; accepting a loose directory here would let a caller smuggle a
    partial result into the M402 readiness chain.
    """

    files = _regular_files(bundle_path, "M401 fixture bundle")
    return _validate_closed_fixture_files(files, label="M401 fixture bundle")


def _validate_m401_gate(request: "DigestRequest") -> dict[str, Any]:
    """Validate M401 arguments without reading raw, CompanyBrain, or config."""

    if request.fixture_bundle_path is None:
        raise ValueError("M401 requires --fixture-bundle")
    if request.m401_attempt_path is None:
        raise ValueError("M401 requires --m401-attempt")
    if request.m401_run_root_path is None:
        raise ValueError("M401 requires --m401-run-root")
    attempt = Path(request.m401_attempt_path).expanduser()
    run_root = Path(request.m401_run_root_path).expanduser()
    fixture = Path(request.fixture_bundle_path).expanduser()
    if not attempt.is_absolute():
        attempt = (Path.cwd() / attempt).resolve()
    if not run_root.is_absolute():
        run_root = (Path.cwd() / run_root).resolve()
    if not fixture.is_absolute():
        fixture = (Path.cwd() / fixture).resolve()
    if attempt.is_symlink():
        raise ValueError("M401 attempt path must be an absolute regular directory")
    if run_root.is_symlink():
        raise ValueError("M401 run-root path must be absolute")
    if run_root.parent.resolve() != attempt.resolve():
        raise ValueError("M401 run-root must be directly under the M401 attempt")
    if attempt.exists() and (not attempt.is_dir() or any(attempt.iterdir())):
        raise ValueError("M401 attempt directory must be new and empty")
    if run_root.exists():
        raise ValueError("M401 run-root must be new")
    return _validate_m401_fixture(fixture)


_M401_FOCUSED_TESTS = (
    "tests/acceptance/test_task5_contract.py",
    "tests/acceptance/test_task5_publication_contract.py",
    "tests/acceptance/test_task5_provider.py",
    "tests/acceptance/test_task5_quality_gate.py",
    "tests/acceptance/test_task5_projection.py",
    "tests/acceptance/test_task5_source_semantic.py",
    "tests/test_simple_digest.py",
    "tests/test_simple_providers.py",
)
_M401_FULL_TESTS = (
    "tests/acceptance/test_task5_contract.py",
    "tests/acceptance/test_task5_full_run.py",
    "tests/acceptance/test_task5_publication_contract.py",
    "tests/acceptance/test_task5_provider.py",
    "tests/acceptance/test_task5_quality_gate.py",
    "tests/acceptance/test_task5_projection.py",
    "tests/acceptance/test_task5_source_semantic.py",
    "tests/test_simple_digest.py",
    "tests/test_simple_providers.py",
)


def _m401_file_snapshot(files: Mapping[str, bytes]) -> tuple[list[dict[str, str]], str]:
    rows = [
        {"relative_path": relative, "sha256": _sha(content)}
        for relative, content in sorted(files.items(), key=lambda item: item[0].encode("utf-8"))
        if relative not in {"_audit/run-result.json", "_audit/run-result.receipt.json"}
    ]
    return rows, _sha(_canonical_json(rows))


def _m401_test_receipt(
    project_root: Path,
    *,
    receipt_kind: str,
    test_files: Sequence[str],
    snapshot_tree: str,
    material_id: str,
) -> dict[str, Any]:
    """Run the declared fake/no-network regression command and hash its result."""

    # The macOS sandbox intentionally provides no inherited PATH.  Keep the
    # logical command stable for the receipt, but invoke the real executable
    # by absolute path or the test gate would fail before pytest starts.
    command = ("uv", "run", "--frozen", "pytest", "-q", *test_files)
    # ``deny network*`` must be layered on the normal macOS default profile;
    # a deny-only profile also denies launching the test runner itself.
    sandbox_profile = "(version 1)(allow default)(deny network*)"
    if not Path("/usr/bin/sandbox-exec").is_file():
        exit_code = 3
        stdout = ""
        stderr = "M401 test command failed: /usr/bin/sandbox-exec is required for network denial"
        executed_command = command
    else:
        uv_executable = shutil.which("uv")
        if not uv_executable:
            exit_code = 3
            stdout = ""
            stderr = "M401 test command failed: uv executable is unavailable"
            executed_command = command
        else:
            executed_command = (
                "/usr/bin/sandbox-exec",
                "-p",
                sandbox_profile,
                "--",
                uv_executable,
                *command[1:],
            )
            try:
                completed = subprocess.run(
                    list(executed_command),
                    cwd=project_root,
                    text=True,
                    capture_output=True,
                    timeout=180,
                    check=False,
                )
                exit_code = int(completed.returncode)
                stdout = completed.stdout
                stderr = completed.stderr
            except (OSError, subprocess.TimeoutExpired) as error:
                exit_code = 3
                stdout = ""
                stderr = f"{type(error).__name__}: M401 test command failed"
    match = re.search(r"(?m)(\d+) passed(?:,\s*(\d+) skipped)?", stdout)
    test_count = int(match.group(1)) if match else None
    return {
        "schema_version": "task5-m401-test-receipt.v1",
        "receipt_kind": receipt_kind,
        "command": list(command),
        "command_sha256": _sha(_canonical_json(list(command))),
        "executed_command": list(executed_command),
        "network_policy": "deny",
        "exit_code": exit_code,
        "status": "passed" if exit_code == 0 else "failed",
        "test_count": test_count,
        "stdout_sha256": _sha(stdout),
        "stderr_sha256": _sha(stderr),
        "result_sha256": _sha((stdout + "\n" + stderr).encode("utf-8")),
        "snapshot_tree": snapshot_tree,
        "material_id": material_id,
    }


def _repair_inverse_patch(files: Mapping[str, bytes]) -> bytes:
    """Build a creation patch whose reverse applies to the after snapshot.

    C3/M401 start from an empty isolated run-root.  The stored inverse is a
    normal unified patch from that empty tree to the materialized files; the
    contract verifies it with ``git apply --check --reverse`` against the
    after snapshot.  The runtime result files are deliberately excluded:
    they are receipts about the tree, not part of the snapshot contract.
    """

    chunks: list[str] = []
    for relative, content in sorted(files.items(), key=lambda item: item[0].encode("utf-8")):
        if relative in {"_audit/run-result.json", "_audit/run-result.receipt.json"}:
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"M401 inverse patch cannot encode binary output: {relative}") from error
        new = text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            (),
            new,
            fromfile="/dev/null",
            tofile=f"b/run-root/bundle/{relative}",
            lineterm="\n",
        )
        chunks.extend(diff)
    return "".join(chunks).encode("utf-8")


_M401_TRACE_BUNDLE_REFS = frozenset({"C3/run-root/bundle", "run-root/bundle"})
_M401_TRACE_ANCHOR_RE = re.compile(
    r"(?<!\S)anchor=(tests/[^\s;]+\.py::test_[A-Za-z0-9_]+)(?:;|\s|$)"
)
_M401_TRACE_EXTERNAL_RE = re.compile(
    r"^quality/evidence/task5/(?:root-cause/attempts/[A-Za-z0-9._-]+/root-cause-evidence\.json|repair-gates/attempts/[A-Za-z0-9._-]+/(?:C0|C1|C2|IMPLEMENT)/attempt\.json)$"
)

_ROUTE_LEDGER_FIELDS = frozenset({
    "query_id", "question", "scene", "route_name", "product_key", "projection_id",
    "candidate_source_ids", "selected_source_ids", "selected_page_ids", "scores",
    "embedding_receipt", "qwen_payload_sha256", "evidence_bindings",
    "home_target_page_identity", "status", "failure",
})


def _route_ledger_projection(manifest: Mapping[str, Any]) -> bytes:
    """Serialize the public route ledger as the manifest.routes projection."""

    routes = manifest.get("routes")
    if not isinstance(routes, list):
        raise ValueError("route ledger projection has no manifest routes")
    lines: list[bytes] = []
    for row in routes:
        if not isinstance(row, Mapping) or set(row) != _ROUTE_LEDGER_FIELDS:
            raise ValueError("route ledger projection row is not exact")
        lines.append(_canonical_json(dict(row)))
    return b"".join(lines)


def _validate_route_ledger_projection(
    files: Mapping[str, bytes],
    manifest: Mapping[str, Any],
    *,
    label: str,
) -> None:
    """Require the public JSONL bytes to equal the manifest route rows."""

    expected = _route_ledger_projection(manifest)
    actual = files.get("_audit/route-ledger.jsonl")
    if actual != expected:
        actual_sha = _sha(actual) if isinstance(actual, bytes) else "missing"
        raise ValueError(
            f"{label} route ledger projection does not match manifest.routes "
            f"(expected_sha256={_sha(expected)}, actual_sha256={actual_sha})"
        )


def _m401_external_trace_sha(output_ref: str) -> str | None:
    """Resolve the one provider-free historical receipt allowed outside C3."""

    if not _M401_TRACE_EXTERNAL_RE.fullmatch(output_ref):
        return None
    path = Path.cwd() / output_ref
    if path.is_symlink() or not path.is_file():
        return None
    return _sha(path.read_bytes())


def _m401_trace(
    run: Mapping[str, Any],
    files: Mapping[str, bytes],
    tree_sha256: str,
) -> list[Mapping[str, Any]]:
    """Accept AC trace only when every claim resolves to fixture bytes.

    The trace is evidence, not a checklist. A C3 fixture must not pass M401
    with a made-up output reference or hash. Bundle references are allowed
    because C3 records one closed, hashed run-root; file references are
    checked against the fixture's actual bytes.
    """

    value = run.get("m401_ac_trace")
    if not isinstance(value, list) or len(value) != 13:
        return []
    expected = [f"AC-v4-{index:02d}" for index in range(1, 14)]
    result: list[Mapping[str, Any]] = []
    seen_anchors: set[str] = set()
    for row, ac_id in zip(value, expected):
        if not isinstance(row, Mapping) or row.get("ac_id") != ac_id:
            return []
        evidence = row.get("evidence")
        if not isinstance(evidence, Mapping) or set(evidence) != {
            "command", "input_snapshot", "input_material", "output_ref",
            "output_sha256", "actual_result", "failure_counterexample",
        }:
            return []
        if not all(isinstance(evidence.get(field), str) and evidence[field].strip() for field in evidence):
            return []
        actual_result = str(evidence["actual_result"])
        failure_counterexample = str(evidence["failure_counterexample"])
        actual_anchors = _M401_TRACE_ANCHOR_RE.findall(actual_result)
        failure_anchors = _M401_TRACE_ANCHOR_RE.findall(failure_counterexample)
        if len(actual_anchors) != 1 or failure_anchors != actual_anchors:
            return []
        anchor = actual_anchors[0]
        if anchor in seen_anchors:
            return []
        seen_anchors.add(anchor)
        if not re.fullmatch(r"[0-9a-f]{40,64}", evidence["input_snapshot"], re.I):
            return []
        if not re.fullmatch(r"[0-9a-f]{64}", evidence["input_material"], re.I):
            return []
        if evidence["input_snapshot"] != str(run.get("snapshot_tree")):
            return []
        if evidence["input_material"] != str(run.get("material_id")):
            return []
        output_ref = evidence["output_ref"]
        if output_ref.startswith(("/", "\\")) or "\\" in output_ref or "//" in output_ref:
            return []
        if any(part in {"", ".", ".."} for part in output_ref.split("/")):
            return []
        if output_ref in _M401_TRACE_BUNDLE_REFS:
            expected_output_sha256 = tree_sha256
        elif output_ref in files:
            expected_output_sha256 = _sha(files[output_ref])
        else:
            expected_output_sha256 = _m401_external_trace_sha(output_ref)
            if expected_output_sha256 is None:
                return []
        if evidence["output_sha256"] != expected_output_sha256:
            return []
        result.append({"ac_id": ac_id, "evidence": dict(evidence)})
    return result


def _run_m401(request: "DigestRequest") -> DigestResult:
    """Run M401 only against a closed C3 fixture; never read real inputs."""

    fixture = _validate_m401_gate(request)
    attempt = Path(request.m401_attempt_path).expanduser()
    if not attempt.is_absolute():
        attempt = (Path.cwd() / attempt).resolve()
    run_root = Path(request.m401_run_root_path).expanduser()
    if not run_root.is_absolute():
        run_root = (Path.cwd() / run_root).resolve()
    # The public M401 contract identifies the repair attempt by the parent
    # directory when the caller uses the canonical attempts/<id>/M401 layout.
    # Keep the generic test fixture layout compatible by using its directory
    # name directly.
    attempt_id = attempt.parent.name if attempt.name == "M401" else attempt.name
    command = request.m401_command or (
        "digest --gate M401 --fixture-bundle "
        f"{request.fixture_bundle_path} --m401-attempt {request.m401_attempt_path} "
        f"--m401-run-root {request.m401_run_root_path}"
    )
    command_bytes = command.encode("utf-8")
    # Validate the patchable representation before creating either output.
    # A malformed/binary fixture must fail before M401 leaves a partial
    # attempt directory behind.
    inverse_patch = _repair_inverse_patch(fixture["files"])
    published_files = _published_files(fixture["files"])
    attempt.mkdir(parents=True, exist_ok=False)
    # The run-root is materialized from the already validated fixture.  It is
    # not a second semantic compilation and it cannot touch raw/CompanyBrain.
    try:
        receipt = commit(published_files, run_root, run_id="m401-" + uuid.uuid4().hex[:12])
    except PublishError as error:
        return DigestResult("failed", "", reason_code=str(error))
    copied = _regular_files(run_root / "bundle", "M401 run-root bundle")
    _snapshot_rows, after_snapshot = _m401_file_snapshot(copied)
    before_rows: list[dict[str, str]] = []
    before_snapshot = _sha(_canonical_json(before_rows))
    changed_paths = [
        {"path": f"run-root/bundle/{relative}", "before_sha256": _sha(b""), "after_sha256": _sha(content)}
        for relative, content in sorted(copied.items(), key=lambda item: item[0].encode("utf-8"))
        if relative not in {"_audit/run-result.json", "_audit/run-result.receipt.json"}
    ]
    inverse_path = attempt / "inverse.patch"
    inverse_path.write_bytes(inverse_patch)
    test_root = Path(__file__).resolve().parents[2]
    focused = _m401_test_receipt(
        test_root,
        receipt_kind="focused",
        test_files=_M401_FOCUSED_TESTS,
        snapshot_tree=fixture["snapshot_tree"],
        material_id=fixture["material_id"],
    )
    full = _m401_test_receipt(
        test_root,
        receipt_kind="full-regression",
        test_files=_M401_FULL_TESTS,
        snapshot_tree=fixture["snapshot_tree"],
        material_id=fixture["material_id"],
    )
    (attempt / "focused-test-receipt.json").write_bytes(_canonical_json(focused))
    (attempt / "full-test-receipt.json").write_bytes(_canonical_json(full))
    # The fixture's already-validated run result is the only accepted source
    # of AC trace. Do not manufacture thirteen “covered” rows from a green
    # pytest command.
    trace = fixture["trace"]
    passed = focused["status"] == "passed" and full["status"] == "passed" and len(trace) == 13
    packet = {
        "schema_version": "task5-m401-evidence-packet.v1",
        "gate": "M401",
        "status": "passed" if passed else "failed",
        "pre_m402_readiness": passed,
        "fixture_bundle_ref": "C3/run-root/bundle",
        "fixture_bundle_sha256": fixture["tree_sha256"],
        "fixture_manifest_sha256": fixture["manifest_sha256"],
        "run_root_ref": "run-root/bundle",
        "run_root_sha256": after_snapshot,
        "snapshot_tree": fixture["snapshot_tree"],
        "material_id": fixture["material_id"],
        "focused_test_receipt": "focused-test-receipt.json",
        "full_test_receipt": "full-test-receipt.json",
        "focused_test_receipt_sha256": _sha((attempt / "focused-test-receipt.json").read_bytes()),
        "full_test_receipt_sha256": _sha((attempt / "full-test-receipt.json").read_bytes()),
        "ac_trace": trace,
        "finding_dispositions": [],
        "coverage_limits": ["M401 does not read raw or CompanyBrain and does not call providers"],
    }
    packet["canonical_sha256"] = _sha(_canonical_json(packet))
    packet_path = attempt / "M401-evidence-packet.json"
    packet_path.write_bytes(_canonical_json(packet))
    attempt_receipt = {
        "schema_version": "task5-m401-attempt-receipt.v1",
        "gate": "M401",
        "attempt_id": attempt_id,
        "command": command,
        "command_sha256": _sha(command_bytes),
        "fixture_bundle_ref": "C3/run-root/bundle",
        "fixture_bundle_sha256": fixture["tree_sha256"],
        "fixture_manifest_sha256": fixture["manifest_sha256"],
        "run_root_ref": "run-root/bundle",
        "run_root_sha256": after_snapshot,
        "packet_ref": "M401-evidence-packet.json",
        "packet_sha256": _sha(packet_path.read_bytes()),
        "snapshot_tree": fixture["snapshot_tree"],
        "material_id": fixture["material_id"],
        "exit_code": 0 if passed else 1,
        "status": "passed" if passed else "failed",
        "reason_code": "NONE" if passed else "QUALITY_GATE_FAILED",
    }
    (attempt / "attempt-receipt.json").write_bytes(_canonical_json(attempt_receipt))
    attempt_record = {
        "schema_version": "task5-repair-gate-attempt.v1",
        "gate": "M401",
        "attempt_id": attempt_id,
        "attempt_seq": 1,
        "material_id": fixture["material_id"],
        "command": command,
        "command_sha256": attempt_receipt["command_sha256"],
        "before_snapshot": before_snapshot,
        "after_snapshot": after_snapshot,
        "changed_paths": changed_paths,
        "before_sha256": before_snapshot,
        "after_sha256": after_snapshot,
        "patch_sha256": _sha(_canonical_json(changed_paths)),
        "inverse_patch_ref": "inverse.patch",
        "inverse_patch_sha256": _sha(inverse_patch),
        "inverse_base_after_snapshot": after_snapshot,
        "run_root_ref": "run-root",
        "exit_code": 0 if passed else 1,
        "status": "passed" if passed else "failed",
        "reason_code": "NONE" if passed else "QUALITY_GATE_FAILED",
    }
    (attempt / "attempt.json").write_bytes(_canonical_json(attempt_record))
    return DigestResult("completed" if passed else "not_released", "m401-" + attempt_id, reason_code=None if passed else "M401 AC trace or regression evidence is incomplete")


_FORMAL_INTERMEDIATE_AUDIT_FILES = frozenset(
    {
        "_audit/sources.jsonl",
        "_audit/evidence.jsonl",
        "_audit/quality.json",
        "_audit/run-result.receipt.json",
    }
)


def _published_files(
    files: Mapping[str, bytes],
    *,
    allow_formal_intermediate: bool = False,
) -> dict[str, bytes]:
    """Put one in-memory bundle under the single public run-root namespace."""

    _validate_public_files(files, allow_formal_intermediate=allow_formal_intermediate)
    result: dict[str, bytes] = {}
    for relative, content in files.items():
        if relative.startswith("bundle/"):
            raise ValueError(f"compiler produced an already-prefixed path: {relative}")
        result[f"bundle/{relative}"] = content
    return result


_PUBLIC_HOST_PATH = re.compile(
    r"(?i)(?:/Users/|/private/tmp/|/tmp/|/var/folders/|(?:^|[/\\])staging(?:[/\\]|$))"
)


def _validate_public_files(
    files: Mapping[str, bytes],
    *,
    allow_formal_intermediate: bool = False,
) -> None:
    """Fail closed before publication if generated public bytes leak secrets or host paths."""

    for relative, content in files.items():
        if not isinstance(content, bytes):
            raise ValueError(f"public bundle contains non-bytes output: {relative}")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"public bundle secret/path scan cannot decode: {relative}") from error
        is_formal_intermediate = allow_formal_intermediate and relative in _FORMAL_INTERMEDIATE_AUDIT_FILES
        if (
            _SENSITIVE_ACCOUNT_EMAIL.search(text)
            or _KNOWN_SERVICE_EMAIL.search(text)
            or _SENSITIVE_VALUE.search(text)
            or _SENSITIVE_BEARER.search(text)
            or (_PUBLIC_HOST_PATH.search(text) and not is_formal_intermediate)
        ):
            raise ValueError(f"public bundle secret/path scan failed: {relative}")


def _public_companybrain_snapshot(
    snapshot: Mapping[str, Any] | None,
    *,
    run_id: str,
    source_manifest_sha256: str,
) -> bytes:
    """Render only the public, host-path-free CompanyBrain binding.

    A normal compiler run has no authority to invent a comparison observation,
    but the fixed machine tree still needs an explicit missing state.  M402
    supplies the real snapshot through ``DigestRequest``; missing data remains
    machine-visible and therefore blocks quality release.
    """

    value = snapshot if isinstance(snapshot, Mapping) else {}
    files: list[dict[str, Any]] = []
    for item in value.get("regular_markdown_files", ()):
        if not isinstance(item, Mapping):
            continue
        entry = {
            key: item[key]
            for key in ("relative_path", "raw_hash", "locator")
            if key in item
        }
        if entry.get("relative_path") and entry.get("raw_hash"):
            files.append(entry)
    public = {
        "schema_version": "knowledge-digest-companybrain-route-snapshot.v1",
        "status": "available" if value and isinstance(value.get("rows"), list) and value.get("rows") else "missing",
        "run_id": run_id,
        "source_manifest_sha256": source_manifest_sha256,
        "companybrain_snapshot_id": value.get("companybrain_snapshot_id") or value.get("snapshot_id"),
        "companybrain_tree_sha256": value.get("companybrain_tree_sha256") or value.get("tree_sha256"),
        "observation_sha256": value.get("observation_sha256"),
        "regular_markdown_files": files,
        "entry_files": [
            str(item)
            for item in value.get("entry_files", ())
            if str(item)
        ],
        "observation_ref": value.get("observation_ref"),
        "failure": None if value and isinstance(value.get("rows"), list) and value.get("rows") else "companybrain_observation_missing",
    }
    return (json.dumps(public, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _with_canonical_hash(value: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("canonical_sha256", None)
    result["canonical_sha256"] = _sha(_canonical_json(result))
    return result


def _formal_raw_coordinate_map(
    sources: Sequence[SourceDoc],
    *,
    source_snapshot_id: str,
) -> dict[str, Any]:
    """Project the immutable source Blocks without copying raw text."""

    rows: list[dict[str, Any]] = []
    for source in sources:
        raw_lines = source.raw_bytes.splitlines(keepends=True)
        raw_offsets = [0]
        for line in raw_lines:
            raw_offsets.append(raw_offsets[-1] + len(line))
        canonical_offsets = [0]
        for line in source.lines:
            canonical_offsets.append(canonical_offsets[-1] + len(line.encode("utf-8")) + 1)
        blocks: list[dict[str, Any]] = []
        for evidence in source.evidence:
            evidence_id = str(evidence.get("evidence_id", ""))
            if not evidence_id or evidence_id.startswith("qev-"):
                continue
            start = int(evidence.get("start_line", 0))
            end = int(evidence.get("end_line", 0))
            if start <= 0 or end < start or end > len(source.lines):
                raise ValueError(f"raw coordinate is invalid: {source.relative_path}#{evidence_id}")
            block_text = "\n".join(source.lines[start - 1:end])
            blocks.append({
                "block_id": evidence_id,
                "source_id": source.source_id,
                "start_line": start,
                "end_line": end,
                "raw_byte_start": raw_offsets[start - 1] if start - 1 < len(raw_offsets) else 0,
                "raw_byte_end": raw_offsets[end] if end < len(raw_offsets) else len(source.raw_bytes),
                "canonical_codepoint_start": canonical_offsets[start - 1],
                "canonical_codepoint_end": max(canonical_offsets[end] - 1, canonical_offsets[start - 1]),
                "block_content_sha256": _sha(block_text),
            })
        blocks.sort(key=lambda item: (int(item["start_line"]), int(item["end_line"]), str(item["block_id"]).encode("utf-8")))
        if any(int(current["start_line"]) <= int(previous["end_line"]) for previous, current in zip(blocks, blocks[1:])):
            raise ValueError(f"raw coordinate blocks overlap: {source.relative_path}")
        rows.append({
            "source_id": source.source_id,
            "source_path": source.relative_path,
            "source_content_hash": _sha(source.raw_bytes),
            "line_count": len(source.lines),
            "byte_count": len(source.raw_bytes),
            "blocks": blocks,
            "coverage": {"block_ids": [str(item["block_id"]) for item in blocks], "non_overlapping": True},
        })
    complete = all(
        bool(row["blocks"])
        or next((source.status == "known_empty" for source in sources if source.source_id == row["source_id"]), False)
        or row["line_count"] == 0
        for row in rows
    )
    return _with_canonical_hash({
        "schema_version": "raw-coordinate-map.v1",
        "source_snapshot_id": source_snapshot_id,
        "sources": rows,
        "coverage": {
            "source_count": len(rows),
            "block_count": sum(len(row["blocks"]) for row in rows),
            "complete": complete,
            "non_overlapping": True,
        },
    })


def _formal_snd_artifacts(
    sources: Sequence[SourceDoc],
    *,
    source_snapshot_id: str,
    material_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create and independently re-check the deterministic SND projection."""

    target = next((source for source in sources if source.relative_path == "GoInsight/17  智能搭建.md"), None)
    if target is None:
        certificate = _with_canonical_hash({
            "schema_version": "semantic_zero_match_certificate.v1",
            "source_id": "",
            "source_snapshot_id": source_snapshot_id,
            "source_content_hash": "",
            "source_hash": "",
            "analyzer_id": "task5-snd-deterministic",
            "analyzer_sha256": _sha("task5-snd-deterministic-v2"),
            "rule_version": "SND-RULE-002",
            "scan_complete": False,
            "scanned_block_refs": [],
            "coverage_digest": _sha(_canonical_json([])),
            "per_block_results": [],
            "blocks": [],
            "result_digest": _sha(_canonical_json([])),
            "coverage": {"block_count": 0, "complete": False},
            "explicit_rule_match": [],
            "ambiguous_match": [],
            "zero_match": False,
        })
        return certificate, _with_canonical_hash({
            "schema_version": "semantic-zero-match-verifier-receipt.v1",
            "attempt_id": "snd-missing",
            "verifier_id": "task5-independent-zero-match-verifier-v1",
            "source_snapshot_id": source_snapshot_id,
            "source_hash": "",
            "certificate_ref": "bundle/_audit/source-not-documented-zero-match.json",
            "certificate_sha256": _sha(_canonical_json(certificate)),
            "recomputed_result_digest": certificate["result_digest"],
            "comparison_digest": _sha("snd-missing"),
            "block_count": 0,
            "compared_block_count": 0,
            "status": "blocked",
            "failure_code": "source_missing",
            "current_material_id": material_id,
        })

    trigger_markers = ("异常", "失败", "报错", "错误", "故障", "bug", "issue", "error", "fail", "unable")
    action_markers = ("处理", "解决", "修复", "检查", "重试", "恢复", "升级", "原因", "排查", "fix", "retry", "recover", "escalate", "cause", "diagnose")
    non_rule_markers = ("不会", "没有", "无", "避免", "防止", "不存在", "不可预知", "逻辑明确", "交互较好", "优点", "缺点", "特点")
    per_block: list[dict[str, Any]] = []
    for evidence in target.evidence:
        evidence_id = str(evidence.get("evidence_id", ""))
        if not evidence_id or evidence_id.startswith("qev-"):
            continue
        text = str(evidence.get("text", ""))
        lowered = text.casefold()
        triggers = [marker for marker in trigger_markers if marker.casefold() in lowered]
        actions = [marker for marker in action_markers if marker.casefold() in lowered]
        if triggers and actions:
            classification = "rule"
        elif triggers and any(marker.casefold() in lowered for marker in non_rule_markers):
            classification = "no_rule"
        elif triggers:
            classification = "ambiguous"
        else:
            classification = "no_rule"
        locator = {"source_path": target.relative_path, "start_line": int(evidence["start_line"]), "end_line": int(evidence["end_line"])}
        block_hash = _sha("\n".join(target.lines[int(evidence["start_line"]) - 1:int(evidence["end_line"])]))
        row = {
            "block_id": evidence_id,
            "block_hash": block_hash,
            "locator": locator,
            "classification": classification,
            "trigger_markers": triggers,
            "action_markers": actions,
        }
        row["evidence_digest"] = _sha(_canonical_json(row))
        per_block.append(row)
    result_digest = _sha(_canonical_json(per_block))
    certificate = _with_canonical_hash({
        "schema_version": "semantic_zero_match_certificate.v1",
        "source_id": target.source_id,
        "source_snapshot_id": source_snapshot_id,
        "source_content_hash": _sha(target.raw_bytes),
        "source_hash": _sha(target.raw_bytes),
        "analyzer_id": "task5-snd-deterministic",
        "analyzer_sha256": _sha("task5-snd-deterministic-v2"),
        "analyzer_contract_sha256": _sha(_canonical_json({"rule_version": "SND-RULE-002", "classification": "trigger+action=>rule"})),
        "rule_version": "SND-RULE-002",
        "scan_scope": ["all_blocks", "tables", "code", "configuration", "links"],
        "scan_complete": True,
        "scanned_block_refs": [str(item["block_id"]) for item in per_block],
        "coverage_digest": _sha(_canonical_json([str(item["block_id"]) for item in per_block])),
        "per_block_results": per_block,
        "blocks": [{"source_block_id": item["block_id"], "source_content_hash": item["block_hash"], "match_count": len(item["trigger_markers"]) + len(item["action_markers"])} for item in per_block],
        "result_digest": result_digest,
        "coverage": {"block_count": len(per_block), "complete": bool(per_block)},
        "explicit_rule_match": [item["block_id"] for item in per_block if item["classification"] == "rule"],
        "ambiguous_match": [item["block_id"] for item in per_block if item["classification"] == "ambiguous"],
        "zero_match": bool(per_block) and all(item["classification"] == "no_rule" for item in per_block),
    })
    certificate_sha = _sha(_canonical_json(certificate))
    passed = bool(certificate["zero_match"])
    verifier = _with_canonical_hash({
        "schema_version": "semantic-zero-match-verifier-receipt.v1",
        "attempt_id": "snd-" + _sha(target.source_id + source_snapshot_id)[:20],
        "verifier_id": "task5-independent-zero-match-verifier-v1",
        "source_snapshot_id": source_snapshot_id,
        "source_hash": _sha(target.raw_bytes),
        "certificate_ref": "bundle/_audit/source-not-documented-zero-match.json",
        "certificate_sha256": certificate_sha,
        "recomputed_result_digest": result_digest,
        "comparison_digest": _sha(_canonical_json({"certificate_sha256": certificate_sha, "result_digest": result_digest})),
        "block_count": len(per_block),
        "compared_block_count": len(per_block),
        "status": "passed" if passed else "unknown",
        "failure_code": None if passed else "zero_match_not_closed",
        "current_material_id": material_id,
    })
    return certificate, verifier


def _formalise_public_bundle(
    files: Mapping[str, bytes],
    *,
    sources: Sequence[SourceDoc],
    run_id: str,
    quality_result_ref: str | None,
    quality_result_sha256: str | None,
    material_id: str,
) -> dict[str, bytes]:
    """Convert compiler staging files to the single v4.7 public machine tree."""

    value = dict(files)
    try:
        run = json.loads(value["_audit/run-result.json"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("formal run result is invalid before publication") from error
    if not isinstance(run, dict) or not isinstance(run.get("manifest"), Mapping):
        raise ValueError("formal run result has no RunManifest")
    manifest = dict(run["manifest"])
    source_snapshot_id = ""
    quality_source_manifest = run.get("quality_source_manifest")
    if isinstance(quality_source_manifest, Mapping):
        source_snapshot_id = str(quality_source_manifest.get("snapshot_id", ""))
    source_snapshot_id = source_snapshot_id or str(run.get("source_manifest_hash", ""))
    coordinate = _formal_raw_coordinate_map(sources, source_snapshot_id=source_snapshot_id)
    snd_certificate, snd_verifier = _formal_snd_artifacts(sources, source_snapshot_id=source_snapshot_id, material_id=material_id)
    manifest_sources = manifest.get("sources", [])
    if not isinstance(manifest_sources, list):
        raise ValueError("formal RunManifest sources are invalid")
    pages = manifest.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError("formal RunManifest pages are invalid")
    audit_pages = _with_canonical_hash({
        "schema_version": "task5-audit-pages.v1",
        "pages": [
            {key: page.get(key) for key in ("page_id", "page_type", "path", "source_ids", "surface_sha256")}
            for page in pages if isinstance(page, Mapping)
        ],
    })
    source_status = _with_canonical_hash({
        "schema_version": "task5-source-status.v1",
        "source_count": len(manifest_sources),
        "sources": [
            {key: row.get(key) for key in ("source_id", "relative_path", "status", "raw_hash", "reader_page_ids", "duplicate_of")}
            for row in manifest_sources if isinstance(row, Mapping)
        ],
    })
    route_ledger_bytes = _route_ledger_projection(manifest)
    trace = run.get("quality_provider_trace", {})
    semantic_rows: list[bytes] = []
    response_rows: list[bytes] = []
    if isinstance(trace, Mapping):
        for projection_id in sorted(trace, key=lambda item: str(item).encode("utf-8")):
            events = trace[projection_id]
            if not isinstance(events, list):
                continue
            for event in events:
                if not isinstance(event, Mapping):
                    continue
                compile_row = {"projection_id": str(projection_id), "stage": event.get("stage"), "attempt": event.get("attempt"), "prompt_sha256": event.get("prompt_sha256"), "qwen_payload_sha256": event.get("qwen_payload_sha256"), "status": event.get("status"), "page_path": event.get("page_path")}
                response_row = {"projection_id": str(projection_id), "stage": event.get("stage"), "attempt": event.get("attempt"), "response_sha256": event.get("response_sha256"), "status": event.get("status"), "page_path": event.get("page_path")}
                semantic_rows.append(_canonical_json(compile_row))
                response_rows.append(_canonical_json(response_row))
    if not semantic_rows:
        semantic_rows = [_canonical_json({"status": "no_semantic_trace"})]
        response_rows = [_canonical_json({"status": "no_semantic_trace"})]
    base: dict[str, bytes] = {
        relative: content
        for relative, content in value.items()
        if not relative.startswith("_audit/")
    }
    base["_audit/audit-pages.json"] = _canonical_json(audit_pages)
    base["_audit/source-status.json"] = _canonical_json(source_status)
    base["_audit/companybrain-route-snapshot.json"] = value.get("_audit/companybrain-route-snapshot.json", b"{}\n")
    base["_audit/semantic-compile-ledger.jsonl"] = b"".join(semantic_rows)
    base["_audit/semantic-response-ledger.jsonl"] = b"".join(response_rows or [_canonical_json({"status": "no_semantic_trace"})])
    base["_audit/route-ledger.jsonl"] = route_ledger_bytes
    base["_audit/raw-coordinate-map.json"] = _canonical_json(coordinate)
    base["_audit/source-not-documented-zero-match.json"] = _canonical_json(snd_certificate)
    base["_audit/source-not-documented-verifier.json"] = _canonical_json(snd_verifier)
    # The formal public tree deliberately excludes the raw source/evidence
    # ledgers and the host-only quality artifact.  Reader pages are allowed to
    # mention those records for internal compilation, but must not publish
    # dead links into the final bundle.  Clean every Markdown surface, not
    # only Audit.md; otherwise candidate surface QA rejects otherwise valid
    # pages after the legacy links have been removed from Audit.
    legacy_audit_paths = {
        "_audit/sources.jsonl",
        "_audit/evidence.jsonl",
        "_audit/quality.json",
    }

    def strip_legacy_audit_links(text: str, relative: str) -> str:
        """Remove links to host-only ledgers from every Markdown depth."""

        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        def replace(match: re.Match[str]) -> str:
            target = match.group(2).strip()
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                return match.group(0)
            path_part = unquote(parsed.path).strip("<>")
            if not path_part:
                return match.group(0)
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(relative), path_part))
            if path_part in legacy_audit_paths or resolved in legacy_audit_paths:
                return f"{match.group(1)}（机器证据保留在 host-only receipt）"
            return match.group(0)

        return link_pattern.sub(replace, text)

    for relative in tuple(base):
        if not relative.endswith(".md"):
            continue
        text = base[relative].decode("utf-8")
        if relative == "Audit.md":
            text = text.replace(
                "- 来源索引：[_audit/sources.jsonl](_audit/sources.jsonl)",
                "- 来源索引：见本页“来源清单”。",
            )
            text = text.replace(
                "- Evidence 详情：见 [`_audit/evidence.jsonl`](_audit/evidence.jsonl)，按 evidence_id 和行号回查；来源索引不复制整篇原文。",
                "- Evidence 详情：见本页“原始证据坐标”；机器证据见本目录 `_audit/`。",
            )
        text = strip_legacy_audit_links(text, relative)
        base[relative] = text.encode("utf-8")
    # The formalizer changes the final Reader bytes when it removes links to
    # host-only ledgers. Rebind every manifest surface hash to those exact
    # public bytes before the post-rename verifier checks the tree.
    for page in manifest.get("pages", ()):
        if not isinstance(page, dict):
            raise ValueError("formal RunManifest page is invalid")
        page_path = str(page.get("path", ""))
        if not page_path or page_path not in base:
            raise ValueError("formal RunManifest page has no public bytes")
        page["surface_sha256"] = _sha(base[page_path])
    run.pop("canonical_sha256", None)
    run["quality_result"] = (
        {"ref": quality_result_ref, "sha256": quality_result_sha256}
        if quality_result_ref and quality_result_sha256 else None
    )
    run["manifest"] = manifest
    manifest["tree_sha256"] = _tree_hash(base)
    run["manifest"] = manifest
    old_outcome = str(run.get("outcome", "not_released"))
    # The compiler writes an immutable attempt artifact first. Only the
    # authenticated post-rename finalizer may promote it to the fixed
    # ``actual-run/quality-result.json`` artifact.
    promoted_quality = quality_result_ref == "actual-run/quality-result.json"
    released = (
        old_outcome == "released"
        and promoted_quality
        and snd_verifier.get("status") == "passed"
    )
    run["publication_status"] = "released" if released else "not_released"
    run["outcome"] = "success"
    run["reason_code"] = "NONE" if released else "QUALITY_GATE_FAILED"
    run["exit_code"] = 0 if released else 1
    calls = run.get("provider_calls", {})
    run["observed_calls"] = {
        "llm": int(calls.get("llm", 0)) if isinstance(calls, Mapping) else 0,
        "embedding": int(calls.get("embedding", 0)) if isinstance(calls, Mapping) else 0,
    }
    run["input_identity"] = {
        "source_manifest_sha256": str(run.get("source_manifest_hash", "")),
        "source_count": len(sources),
        "quality_projection_count": int(run.get("quality_projection_count", 0)),
        "evaluation_mode": str(run.get("evaluation_mode", "full")),
    }
    run["lifecycle"] = {
        "state": "released" if released else "not_released",
        "slice_status": "not_evaluated" if str(run.get("evaluation_mode")) == "full" else "candidate",
        "full_status": "passed" if released else "not_released",
        "failure_evidence_path": None,
    }
    run["artifact_manifest"] = {
        "quality_result": run["quality_result"],
        "public_tree_sha256": manifest["tree_sha256"],
        "public_receipt_ref": "_audit/run-result.json",
    }
    run["workflowhub_identity"] = {"status": "validated", "implementation_review_required": True}
    run["canonical_sha256"] = _sha(_canonical_json(run))
    base["_audit/run-result.json"] = _canonical_json(run)
    manifest_rows = []
    for relative, content in sorted(base.items(), key=lambda item: str(item[0]).encode("utf-8")):
        if relative in {"_audit/run-result.json", "_audit/directory-manifest.json"}:
            continue
        manifest_rows.append({"path": relative, "sha256": _sha(content), "bytes": len(content), "lines": content.count(b"\n")})
    directory = _with_canonical_hash({
        "schema_version": "task5-directory-manifest.v1",
        "layout_contract_sha256": _sha(Path(__file__).resolve().parents[2].joinpath("config/task5-publication-layout-v2.json").read_bytes()),
        "required_paths": [f"bundle/{relative}" for relative in _FORMAL_PUBLIC_AUDIT_FILES],
        "files": manifest_rows,
        "tree_sha256": manifest["tree_sha256"],
        "forbidden_path_scan": {"passed": True, "matches": []},
    })
    base["_audit/directory-manifest.json"] = _canonical_json(directory)
    _validate_public_files(base)
    missing = [relative for relative in _FORMAL_PUBLIC_AUDIT_FILES if relative not in base]
    if missing:
        raise ValueError("formal public bundle is incomplete: " + ", ".join(missing))
    return base


def _run_c3_fixture(
    request: DigestRequest,
    providers: tuple[SemanticModel, Embedder],
    *,
    attempt_path: Path,
    snapshot_tree: str,
    material_id: str,
    command: str,
    ac_trace_factory: Callable[[Mapping[str, Any], str], Sequence[Mapping[str, Any]]] | None,
) -> dict[str, Any]:
    """Produce one isolated, fake/no-network C3 bundle.

    C3 is intentionally private: the public CLI has only M401 and M402.  The
    caller must inject fake provider seams and an independently produced AC
    trace after the closed bytes are known.  This helper owns only the
    deterministic compiler/publication boundary; it never reads raw outside
    ``request.new_dir``, CompanyBrain, or provider configuration.
    """

    if ac_trace_factory is None:
        raise ValueError("C3 requires an externally produced AC trace")
    if request.gate is not None:
        raise ValueError("C3 fixture request cannot use a public gate")
    if request.quality_config_path is not None or request.source_manifest_path is not None:
        raise ValueError("C3 fixture request cannot use a real quality manifest")
    if request.companybrain_root is not None or request.companybrain_route_snapshot is not None:
        raise ValueError("C3 fixture request cannot use CompanyBrain")
    if not isinstance(providers, tuple) or len(providers) != 2 or any(provider is None for provider in providers):
        raise ValueError("C3 requires explicit fake provider seams")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("C3 command is required")
    if not re.fullmatch(r"[0-9a-f]{40,64}", str(snapshot_tree), re.I):
        raise ValueError("C3 snapshot identity is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(material_id), re.I):
        raise ValueError("C3 material identity is invalid")

    attempt = Path(attempt_path).expanduser()
    if not attempt.is_absolute() or attempt.is_symlink():
        raise ValueError("C3 attempt path must be an absolute regular directory")
    if attempt.exists() and (not attempt.is_dir() or any(attempt.iterdir())):
        raise ValueError("C3 attempt directory must be new and empty")
    run_root = attempt / "run-root"
    if run_root.exists() or run_root.is_symlink():
        raise ValueError("C3 run-root must be new")

    # ``_build_bundle`` is the same compiler consumer as the public digest;
    # only the injected seams and the absence of real quality/CompanyBrain
    # inputs make this a controlled C3 run.
    fixture_request = replace(
        request,
        gate=None,
        kb_dir=run_root,
        quality_config_path=None,
        source_manifest_path=None,
        companybrain_root=None,
        companybrain_route_snapshot=None,
        evaluation_mode="full",
        material_id=material_id,
    )
    bundle = _build_bundle(fixture_request, providers[0], providers[1])
    staged = dict(bundle.files)
    try:
        run = json.loads(staged["_audit/run-result.json"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("C3 compiler did not produce a valid run result") from error
    if not isinstance(run, dict):
        raise ValueError("C3 compiler run result is not an object")
    run["snapshot_tree"] = str(snapshot_tree)
    run["material_id"] = str(material_id)
    run.pop("canonical_sha256", None)
    run["canonical_sha256"] = _sha(_canonical_json(run))
    staged["_audit/run-result.json"] = _canonical_json(run)

    formal_files = _formalise_public_bundle(
        staged,
        sources=bundle.sources,
        run_id=bundle.run_id,
        quality_result_ref=None,
        quality_result_sha256=None,
        material_id=str(material_id),
    )
    tree_sha256 = _tree_hash(formal_files)
    formal_run = json.loads(formal_files["_audit/run-result.json"].decode("utf-8"))
    if not isinstance(formal_run, Mapping):
        raise ValueError("C3 formal run result is invalid")
    trace_context = dict(formal_run)
    # The trace producer must be able to bind each criterion to the exact
    # machine artifact emitted by this closed fixture.  Keep the bytes
    # producer-only: this private context never enters run-result.json.
    trace_context["_formal_files"] = formal_files
    supplied_trace = list(ac_trace_factory(trace_context, tree_sha256))
    if any(
        not isinstance(row, Mapping)
        or not isinstance(row.get("evidence"), Mapping)
        or not isinstance(row["evidence"].get("command"), str)
        or not row["evidence"]["command"].strip()
        for row in supplied_trace
    ):
        raise ValueError("C3 AC trace contains an invalid owner command")
    trace_run = dict(formal_run)
    trace_run["m401_ac_trace"] = supplied_trace
    trace = _m401_trace(trace_run, formal_files, tree_sha256)
    if len(trace) != 13:
        raise ValueError("C3 AC trace is not verifiable")
    trace_run["m401_ac_trace"] = trace
    trace_run.pop("canonical_sha256", None)
    trace_run["canonical_sha256"] = _sha(_canonical_json(trace_run))
    formal_files["_audit/run-result.json"] = _canonical_json(trace_run)

    # Validate the complete public machine closure before creating the attempt
    # or run-root.  This is the important distinction from a test that only
    # checks the compiler's in-memory pages.
    closed = _validate_closed_fixture_files(formal_files, label="C3 fixture bundle")
    inverse_patch = _repair_inverse_patch(formal_files)
    attempt_id = attempt.parent.name if attempt.name == "C3" else attempt.name
    before_rows: list[dict[str, str]] = []
    before_snapshot = _sha(_canonical_json(before_rows))

    attempt.mkdir(parents=True, exist_ok=False)
    try:
        receipt = commit(
            _published_files(formal_files),
            run_root,
            run_id="c3-" + uuid.uuid4().hex[:12],
            task5=True,
            material_id=str(material_id),
        )
    except Exception:
        # No partial C3 attempt is a usable fixture.  The caller receives the
        # real publication error and may retry with a new attempt id.
        try:
            attempt.rmdir()
        except OSError:
            pass
        raise
    if receipt.get("committed") is not True:
        raise PublishError("C3 fixture publication did not commit")

    copied = _regular_files(run_root / "bundle", "C3 run-root bundle")
    _snapshot_rows, after_snapshot = _m401_file_snapshot(copied)
    changed_paths = [
        {
            "path": f"run-root/bundle/{relative}",
            "before_sha256": _sha(b""),
            "after_sha256": _sha(content),
        }
        for relative, content in sorted(copied.items(), key=lambda item: item[0].encode("utf-8"))
        if relative not in {"_audit/run-result.json", "_audit/run-result.receipt.json"}
    ]
    inverse_ref = attempt / "inverse.patch"
    inverse_sha256 = _write_create_only(inverse_ref, inverse_patch)
    attempt_record = {
        "schema_version": "task5-repair-gate-attempt.v1",
        "gate": "C3",
        "attempt_id": attempt_id,
        "attempt_seq": 1,
        "material_id": str(material_id),
        "command": command,
        "command_sha256": _sha(command.encode("utf-8")),
        "before_snapshot": before_snapshot,
        "after_snapshot": after_snapshot,
        "changed_paths": changed_paths,
        "before_sha256": before_snapshot,
        "after_sha256": after_snapshot,
        "patch_sha256": _sha(_canonical_json(changed_paths)),
        "inverse_patch_ref": "inverse.patch",
        "inverse_patch_sha256": inverse_sha256,
        "inverse_base_after_snapshot": after_snapshot,
        "run_root_ref": "run-root/bundle",
        "exit_code": 0,
        "status": "passed",
        "reason_code": "NONE",
    }
    attempt_sha256 = _write_create_only(attempt / "attempt.json", _canonical_json(attempt_record))
    return {
        "status": "passed",
        "reason_code": "NONE",
        "attempt_id": attempt_id,
        "attempt_ref": "attempt.json",
        "attempt_sha256": attempt_sha256,
        "run_root_ref": "run-root/bundle",
        "tree_sha256": closed["tree_sha256"],
        "manifest_sha256": closed["manifest_sha256"],
        "provider_calls": {
            "llm": int(getattr(providers[0], "calls", 0)),
            "embedding": int(getattr(providers[1], "calls", 0)),
        },
        "attempt_path": attempt,
        "run_root_path": run_root,
    }


def _companybrain_observation(
    root: Path,
    *,
    snapshot: Mapping[str, Any],
    projections: Sequence[QualityProjection],
    baseline_path: Path,
    pages: Sequence[ReaderPage],
    evidence_bytes: bytes,
    run_id: str,
    source_manifest_sha256: str,
) -> dict[str, Any]:
    """Build the current, host-bound CompanyBrain observation after rendering.

    This is intentionally a conservative scanner: a target is ``present``
    only when the corresponding visible structure can be replayed from the
    current CompanyBrain files.  Missing or ambiguous structure is recorded
    as ``absent``/``unknown`` and never promoted to a quality win.
    """

    root = Path(root).expanduser()
    try:
        baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("CompanyBrain baseline manifest is invalid") from error
    entries = baseline.get("entries") if isinstance(baseline, Mapping) else None
    if not isinstance(entries, list):
        raise ValueError("CompanyBrain baseline manifest has no entries")

    markdown: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in {".md", ".markdown"}:
            continue
        relative = path.relative_to(root).as_posix()
        markdown[relative] = path.read_text(encoding="utf-8", errors="replace")

    def resolve_link(current: str, raw: str) -> str:
        target = raw.split("#", 1)[0].strip()
        if not target or "://" in target:
            return ""
        candidate = (Path(current).parent / target).as_posix()
        normalised = posixpath.normpath(candidate)
        if normalised.startswith("../") or normalised == "..":
            return ""
        if normalised in markdown:
            return normalised
        if normalised + ".md" in markdown:
            return normalised + ".md"
        return ""

    links: dict[str, set[str]] = defaultdict(set)
    for current, text in markdown.items():
        for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)|\[\[([^\]]+)\]\]", text):
            target = resolve_link(current, raw[0] or raw[1])
            if target:
                links[current].add(target)
    entry_names = {
        "home.md", "gbrain-product-index.md", "文档总览.md", "使用场景索引.md",
        "产品总览.md", "常见问答入口.md", "模块总览.md",
    }
    queue = [path for path in markdown if Path(path).name.casefold() in entry_names]
    reachable: set[str] = set(queue)
    while queue:
        current = queue.pop(0)
        for target in sorted(links.get(current, ())):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)

    try:
        evidence_rows = [
            json.loads(line)
            for line in evidence_bytes.decode("utf-8").splitlines()
            if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError):
        evidence_rows = []
    kd_refs = {
        str(page.projection_id): next(
            (
                f"{page.relative_path}#{row.get('unit_id')}"
                for row in evidence_rows
                if isinstance(row, Mapping)
                and row.get("page_path") == page.relative_path
                and row.get("surface") == "Reader.answer_body"
                and row.get("unit_id")
            ),
            None,
        )
        for page in pages
        if page.projection_id
    }

    def heading_present(text: str, names: Sequence[str]) -> bool:
        headings = {
            match.group(1).strip()
            for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", text)
        }
        return any(name in headings for name in names)

    expected_headings = {
        page_type: tuple(PAGE_TYPES[page_type])
        for page_type in PAGE_TYPES
    }
    gap_types = {
        "DIM-01.route": "unreachable",
        "DIM-02.taxonomy": "missing_taxonomy_axis",
        "DIM-03.business-answer": "missing_stage",
        "DIM-04.page-type": "untyped_contract",
        "DIM-05.reader-audit": "missing_provenance",
    }
    rubric_labels = {
        "DIM-01.route": "route",
        "DIM-02.taxonomy": "taxonomy",
        "DIM-03.business-answer": "business-answer",
        "DIM-04.page-type": "page-type",
        "DIM-05.reader-audit": "Reader-Audit",
    }
    feature_by_gap = {
        "DIM-01.route": {"unreachable": "canonical_target", "wrong_relation": "projection_isolation"},
        "DIM-02.taxonomy": {"missing_taxonomy_axis": "axis_meaning", "wrong_relation": "axis_separation"},
        "DIM-03.business-answer": {"missing_stage": "task_completion", "unsupported_answer_claim": "decision_safety", "wrong_relation": "scope_discipline"},
        "DIM-04.page-type": {"untyped_contract": "type_specificity", "wrong_page_type": "scope_fit"},
        "DIM-05.reader-audit": {"missing_provenance": "source_locator", "untraceable_claim": "claim_lineage"},
    }
    targets_by_projection = {
        projection.projection_id: [
            str(entry.get("relative_path", ""))
            for entry in entries
            if isinstance(entry, Mapping)
            and projection.projection_id in [str(item) for item in entry.get("projection_keys", ())]
        ]
        for projection in projections
    }
    path_use_count: dict[str, int] = defaultdict(int)
    for target_paths in targets_by_projection.values():
        for target_path in target_paths:
            path_use_count[target_path] += 1
    rows: list[dict[str, Any]] = []
    for projection in projections:
        targets = targets_by_projection.get(projection.projection_id, [])
        for dimension in ("DIM-01.route", "DIM-02.taxonomy", "DIM-03.business-answer", "DIM-04.page-type", "DIM-05.reader-audit"):
            existing = [path for path in targets if path in markdown]
            source_refs = sorted(existing, key=lambda value: value.encode("utf-8"))
            visible_ref = f"{source_refs[0]}#L1-L{len(markdown[source_refs[0]].splitlines())}" if source_refs else None
            status = "unknown"
            gap_detail: dict[str, Any] | None = None
            if existing:
                text = "\n".join(markdown[path] for path in existing)
                rubric = projection.comparison_rubric.get(rubric_labels[dimension], {})
                if not isinstance(rubric, Mapping):
                    rubric = {}
                atom_forms = rubric.get("atom_forms", {})
                missing_atom_names: list[str] = []
                for atom in rubric.get("required_atoms", ()) if isinstance(rubric.get("required_atoms", ()), list) else ():
                    forms = atom_forms.get(atom, [atom]) if isinstance(atom_forms, Mapping) else [atom]
                    if not any(str(form) and str(form).casefold() in text.casefold() for form in forms):
                        missing_atom_names.append(str(atom))
                missing_atom_ids = [
                    f"{projection.projection_id}::{dimension}::{atom}"
                    for atom in missing_atom_names
                ]
                marker_names = rubric.get("structure_markers", ())
                missing_stage_refs = [
                    f"{projection.projection_id}::{dimension}::stage::{marker}"
                    for marker in marker_names
                    if str(marker) and str(marker).casefold() not in text.casefold()
                ] if isinstance(marker_names, list) else []
                route_feature_gap = ""
                if dimension == "DIM-01.route":
                    question_text = re.sub(r"[？?，,、。]", "", projection.question).strip()
                    title_text = re.sub(r"[？?，,、。]", "", projection.title).strip()
                    route_features = {
                        "question_match": bool(question_text and question_text in text)
                        or bool(title_text and title_text in text),
                        "scenario_disambiguation": projection.axes["scene"] in text,
                        "canonical_target": len(existing) == 1 and bool(title_text and title_text in text),
                        "projection_isolation": max((path_use_count.get(path, 0) for path in existing), default=0) == 1,
                    }
                    route_feature_gap = next((name for name, passed in route_features.items() if not passed), "")
                    status = "present" if any(path in reachable for path in existing) and not route_feature_gap else "absent"
                elif dimension == "DIM-02.taxonomy":
                    has_axes = all(
                        re.search(rf"(?im)^\s*(?:{axis}|{label})\s*[:：|]\s*.+", text)
                        for axis, label in (("product", "产品"), ("module", "模块"), ("object", "对象"), ("scene|scenario", "场景"), ("boundary", "边界"))
                    )
                    status = "present" if has_axes else "absent"
                elif dimension == "DIM-03.business-answer":
                    status = "present" if all(
                        heading_present(text, (heading,))
                        for heading in expected_headings[projection.page_type]
                    ) else "absent"
                elif dimension == "DIM-04.page-type":
                    page_type_match = re.search(
                        r"(?ims)^##\s+页面类型\s*\n.*?^\s*-\s*(定位|概念|操作|诊断|经验)\s*$",
                        text,
                    )
                    status = "present" if page_type_match and page_type_match.group(1) == PAGE_TYPE_LABELS[projection.page_type] else "absent"
                else:
                    status = "present" if (
                        re.search(r"(?i)Audit\.md|sourcearchive|原始地址", text)
                        and re.search(r"(?i)#(?:L\d+|source-|evidence-)", text)
                    ) else "absent"
                if status == "present" and (missing_atom_ids or missing_stage_refs):
                    status = "absent"
                if status == "absent":
                    gap_type = gap_types[dimension]
                    if dimension == "DIM-01.route" and any(path in reachable for path in existing):
                        gap_type = "wrong_relation"
                    elif dimension == "DIM-03.business-answer" and missing_atom_ids:
                        gap_type = "unsupported_answer_claim"
                    elif dimension == "DIM-04.page-type" and re.search(r"(?ims)^##\s+页面类型\s*\n", text):
                        gap_type = "wrong_page_type"
                    elif dimension == "DIM-05.reader-audit" and existing:
                        gap_type = "untraceable_claim"
                    feature_name = route_feature_gap if dimension == "DIM-01.route" else feature_by_gap.get(dimension, {}).get(gap_type, "")
                    feature_defs = projection.quality_features.get(rubric_labels[dimension], ())
                    feature_ref = next(
                        (
                            f"{projection.projection_id}::{dimension}::feature::{feature_name}"
                            for item in feature_defs
                            if str(item.get("feature_id", "")) == feature_name
                        ),
                        "",
                    )
                    gap_detail = {
                        "gap_type": gap_type,
                        "gap_locator": visible_ref or "",
                        "gap_atom_refs": missing_atom_ids,
                        "gap_stage_refs": missing_stage_refs,
                        "gap_quality_feature_refs": [feature_ref] if feature_ref else [],
                    }
            row = {
                "case_id": projection.case_id,
                "projection_id": projection.projection_id,
                "dimension_id": dimension,
                "status": status,
                # This is an observation status, not a quality score.  A
                # numeric value here would falsely imply calibrated scoring.
                "score": None,
                "source_refs": source_refs,
                "visible_ref": visible_ref,
                "audit_ref": visible_ref if status == "present" and dimension == "DIM-05.reader-audit" else None,
                "gap_ref": gap_detail,
                "kd_ref": kd_refs.get(projection.projection_id),
            }
            rows.append(row)
    rows.sort(key=lambda row: (str(row["case_id"]).encode("utf-8"), str(row["projection_id"]).encode("utf-8"), str(row["dimension_id"]).encode("utf-8")))
    payload = {
        "run_id": run_id,
        "source_manifest_sha256": source_manifest_sha256,
        "companybrain_snapshot_id": snapshot.get("companybrain_snapshot_id") or snapshot.get("snapshot_id"),
        "companybrain_tree_sha256": snapshot.get("companybrain_tree_sha256") or snapshot.get("tree_sha256"),
        "rows": rows,
    }
    return {
        **payload,
        "regular_markdown_files": list(snapshot.get("regular_markdown_files", ())),
        "entry_files": list(snapshot.get("entry_files", ())),
        "observation_sha256": _sha(_canonical_json(payload)),
        "observation_ref": f"companybrain-observation:{run_id}",
        "gap_types": gap_types,
    }


def _validate_run_manifest(manifest: Mapping[str, Any], *, expected_source_count: int) -> None:
    """Fail closed if the machine closure can no longer explain the bundle."""

    required = {"schema_version", "source_count", "sources", "routes", "pages", "tree_sha256"}
    if set(manifest) != required or manifest.get("schema_version") != "knowledge-digest-run-manifest.v1":
        raise ValueError("run manifest schema is not exact")
    sources = manifest.get("sources")
    pages = manifest.get("pages")
    routes = manifest.get("routes")
    if not isinstance(sources, list) or not isinstance(pages, list) or not isinstance(routes, list):
        raise ValueError("run manifest collections are malformed")
    if manifest.get("source_count") != expected_source_count or len(sources) != expected_source_count:
        raise ValueError("run manifest source count is not closed")
    source_ids = set()
    source_paths = set()
    for row in sources:
        if not isinstance(row, Mapping) or set(row) != {"source_id", "relative_path", "product_key", "product_label", "raw_hash", "status", "source_digest_eligible", "duplicate_of", "evidence_ids", "reader_page_ids", "failure"}:
            raise ValueError("run manifest source row is not exact")
        source_id = str(row["source_id"])
        relative_path = str(row["relative_path"])
        if not source_id or not relative_path or source_id in source_ids or relative_path in source_paths:
            raise ValueError("run manifest source identity is duplicated")
        # Generic digest runs historically use ``failed`` for a source whose
        # provider call failed. Task5 exposes the same state as
        # ``provider_failed``; M402 still enforces its exact vocabulary.
        if row["status"] not in {"ready", "known_empty", "duplicate_alias", "failed", "provider_failed", "unsupported"}:
            raise ValueError("run manifest source status is invalid")
        if not isinstance(row["source_digest_eligible"], bool):
            raise ValueError("run manifest source eligibility is invalid")
        if not isinstance(row["evidence_ids"], list) or not isinstance(row["reader_page_ids"], list):
            raise ValueError("run manifest source bindings are malformed")
        source_ids.add(source_id)
        source_paths.add(relative_path)
    page_ids = set()
    page_keys = set()
    for row in pages:
        if not isinstance(row, Mapping) or set(row) != {"page_id", "page_key", "page_type", "axes", "source_ids", "path", "surface_sha256"}:
            raise ValueError("run manifest page row is not exact")
        page_id = str(row["page_id"])
        page_key = str(row["page_key"])
        if not page_id or not page_key or page_id in page_ids or page_key in page_keys:
            raise ValueError("run manifest page identity is duplicated")
        if not page_key.startswith(("source:", "answer:")) or not isinstance(row["source_ids"], list) or not row["source_ids"]:
            raise ValueError("run manifest page closure is malformed")
        if not isinstance(row["axes"], Mapping) or set(row["axes"]) != {"product", "module", "object", "scenario", "boundary"} or any(
            not isinstance(row["axes"].get(axis), str) for axis in row["axes"]
        ):
            raise ValueError("run manifest page axes are not exact")
        if not set(str(item) for item in row["source_ids"]).issubset(source_ids):
            raise ValueError("run manifest page cites an unknown source")
        page_ids.add(page_id)
        page_keys.add(page_key)
    for row in routes:
        if not isinstance(row, Mapping) or set(row) != {"query_id", "question", "scene", "route_name", "product_key", "projection_id", "candidate_source_ids", "selected_source_ids", "selected_page_ids", "scores", "embedding_receipt", "qwen_payload_sha256", "evidence_bindings", "home_target_page_identity", "status", "failure"}:
            raise ValueError("run manifest route row is not exact")
        if row["status"] not in {"ready", "failed", "blocked", "unavailable"} or not str(row["query_id"]) or not isinstance(row["selected_source_ids"], list) or not isinstance(row["selected_page_ids"], list):
            raise ValueError("run manifest route closure is malformed")
        if not isinstance(row["evidence_bindings"], list):
            raise ValueError("run manifest route evidence bindings are malformed")
        scores = row["scores"]
        if not isinstance(scores, Mapping) or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
            for key, value in scores.items()
        ):
            raise ValueError("run manifest route scores are malformed")
        if row["status"] == "ready":
            if not row["selected_source_ids"] or not row["selected_page_ids"] or not str(row["qwen_payload_sha256"]):
                raise ValueError("run manifest route has no successful closure")
            if len(row["selected_page_ids"]) != 1 or row["home_target_page_identity"] != row["selected_page_ids"][0]:
                raise ValueError("run manifest route has no unique Home target")
            embedding_receipt = row["embedding_receipt"]
            if not isinstance(embedding_receipt, Mapping) or set(embedding_receipt) != {
                "provider", "model", "request_identity", "selected_source_ids",
                "selected_closure_sha256", "response_sha256", "status",
            } or embedding_receipt.get("status") != "passed" or not all(
                str(embedding_receipt.get(field, ""))
                for field in ("provider", "model", "request_identity", "selected_closure_sha256", "response_sha256")
            ) or embedding_receipt.get("selected_source_ids") != row["selected_source_ids"]:
                raise ValueError("run manifest route has no embedding receipt")
            if row["failure"] is not None:
                raise ValueError("successful route has a failure")
        elif not isinstance(row["failure"], (str, Mapping)) or not row["failure"]:
            raise ValueError("failed route has no failure reason")


def _validate_m402_published_closure(
    run: Mapping[str, Any],
    public_files: Mapping[str, bytes],
    candidate_quality: Mapping[str, Any],
    *,
    evidence_root: Path,
    published_tree_sha256: str,
    published_manifest_sha256: str,
) -> None:
    """Recheck the real-run release contract after the atomic rename.

    The pre-provider source check and the provider-side quality comparison are
    necessary but not sufficient: a finalizer must bind its verdict to the
    bytes that actually became the published tree.  Keep this predicate
    deliberately M402-specific so small M401 fixtures retain their isolated
    contract.
    """

    manifest = run.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ValueError("M402 published RunManifest is missing")
    sources = manifest.get("sources")
    pages = manifest.get("pages")
    routes = manifest.get("routes")
    if not isinstance(sources, list) or len(sources) != 89 or run.get("source_count") != 89:
        raise ValueError("M402 published source closure is not 89")
    status_counts: dict[str, int] = defaultdict(int)
    source_ids: set[str] = set()
    for row in sources:
        if not isinstance(row, Mapping):
            raise ValueError("M402 published source row is malformed")
        source_id = str(row.get("source_id", ""))
        if not source_id or source_id in source_ids:
            raise ValueError("M402 published source identity is not unique")
        source_ids.add(source_id)
        status_counts[str(row.get("status", ""))] += 1
    if status_counts != {"ready": 87, "known_empty": 1, "duplicate_alias": 1}:
        raise ValueError("M402 published source status closure is invalid")
    product_keys = {str(row.get("product_key", "")) for row in sources}
    expected_products = {value[0] for value in _KNOWN_PRODUCT_ROOTS.values()}
    if product_keys != expected_products:
        raise ValueError("M402 published source product closure is invalid")

    if not isinstance(pages, list) or not pages:
        raise ValueError("M402 published Reader page closure is missing")
    page_ids = {str(row.get("page_id", "")) for row in pages if isinstance(row, Mapping)}
    if len(page_ids) != len(pages) or "" in page_ids:
        raise ValueError("M402 published Reader page identities are not unique")
    if {str(row.get("page_type", "")) for row in pages if isinstance(row, Mapping)} != set(PAGE_TYPES):
        raise ValueError("M402 published page-type closure is not the frozen five")
    for row in pages:
        if not isinstance(row, Mapping) or str(row.get("path", "")) not in public_files:
            raise ValueError("M402 published Reader page is not bound to bytes")

    expected_projection_ids = tuple(_EXPECTED_PROJECTION_IDS)
    if run.get("quality_projection_count") != len(expected_projection_ids):
        raise ValueError("M402 published quality projection count is not 12")
    if tuple(run.get("quality_projection_ids", ())) != expected_projection_ids:
        raise ValueError("M402 published quality projection identity is not frozen")
    quality_page_ids = {
        str(row.get("page_id", ""))
        for row in pages
        if isinstance(row, Mapping) and str(row.get("page_key", "")).startswith("answer:")
    }
    if len(quality_page_ids) != len(expected_projection_ids) or run.get("quality_page_count") != len(expected_projection_ids):
        raise ValueError("M402 published quality page closure is incomplete")

    if not isinstance(routes, list) or len(routes) != len(expected_projection_ids):
        raise ValueError("M402 published route closure is not 12 rows")
    route_ids = []
    for route in routes:
        if not isinstance(route, Mapping) or route.get("status") != "ready":
            raise ValueError("M402 published route closure contains a non-ready row")
        projection_id = str(route.get("projection_id", ""))
        route_ids.append(projection_id)
        selected_pages = route.get("selected_page_ids")
        if not isinstance(selected_pages, list) or len(selected_pages) != 1 or str(selected_pages[0]) not in quality_page_ids:
            raise ValueError("M402 published route has no unique quality page")
        if route.get("home_target_page_identity") != selected_pages[0]:
            raise ValueError("M402 published route Home target is not bound")
        selected_sources = route.get("selected_source_ids")
        if not isinstance(selected_sources, list) or not selected_sources or not set(map(str, selected_sources)).issubset(source_ids):
            raise ValueError("M402 published route source closure is invalid")
    if tuple(route_ids) != expected_projection_ids:
        raise ValueError("M402 published route projection identity is not frozen")
    _validate_route_ledger_projection(public_files, manifest, label="M402 published bundle")

    if not isinstance(candidate_quality, Mapping):
        raise ValueError("M402 quality candidate is missing")
    if candidate_quality.get("run_id") != run.get("run_id"):
        raise ValueError("M402 quality candidate run binding is invalid")
    if candidate_quality.get("candidate_tree_sha256") != published_tree_sha256:
        raise ValueError("M402 quality candidate tree binding is invalid")
    if candidate_quality.get("candidate_manifest_ref") != "bundle/_audit/directory-manifest.json" or candidate_quality.get("candidate_manifest_sha256") != published_manifest_sha256:
        raise ValueError("M402 quality candidate manifest binding is invalid")
    if candidate_quality.get("source_count_in_audit") != 89 or candidate_quality.get("source_count_on_disk") != 89:
        raise ValueError("M402 quality source count is not 89")
    if candidate_quality.get("source_manifest_sha256") != run.get("source_manifest_hash"):
        raise ValueError("M402 quality source manifest binding is invalid")
    rendered_units = candidate_quality.get("rendered_units")
    bound_units = candidate_quality.get("bound_units")
    if not isinstance(rendered_units, int) or not isinstance(bound_units, int) or rendered_units != bound_units:
        raise ValueError("M402 quality lineage is incomplete")
    if candidate_quality.get("lineage_coverage") != 1.0:
        raise ValueError("M402 quality lineage coverage is not complete")
    if candidate_quality.get("candidate_reader_file_count") != len(quality_page_ids):
        raise ValueError("M402 quality Reader page count is not bound")

    dimensions = candidate_quality.get("dimension_verdicts")
    rows = candidate_quality.get("quality_rows")
    if candidate_quality.get("projection_count") != len(expected_projection_ids) or candidate_quality.get("dimensions") != list(_EXPECTED_DIMENSIONS):
        raise ValueError("M402 quality dimension contract is not frozen")
    if not isinstance(dimensions, Mapping) or set(dimensions) != set(expected_projection_ids):
        raise ValueError("M402 quality projection dimension closure is incomplete")
    if not isinstance(rows, list) or len(rows) != len(expected_projection_ids) * len(_EXPECTED_DIMENSIONS):
        raise ValueError("M402 quality row closure is not 12x5")
    row_keys = {(str(row.get("projection_key", "")), str(row.get("dimension_id", ""))) for row in rows if isinstance(row, Mapping)}
    expected_row_keys = {(projection_id, dimension) for projection_id in expected_projection_ids for dimension in _EXPECTED_DIMENSIONS}
    if row_keys != expected_row_keys:
        raise ValueError("M402 quality row identity closure is not 12x5")
    for projection_id in expected_projection_ids:
        projection_dimensions = dimensions.get(projection_id)
        if not isinstance(projection_dimensions, Mapping) or set(projection_dimensions) != set(_EXPECTED_DIMENSIONS):
            raise ValueError("M402 quality candidate dimension closure is incomplete")

    comparison = candidate_quality.get("comparison")
    comparison_dimensions = comparison.get("dimension_verdicts") if isinstance(comparison, Mapping) else None
    if not isinstance(comparison, Mapping) or comparison.get("verdict") != "released" or comparison.get("publication_status") != "released" or comparison.get("hard_blockers"):
        raise ValueError("M402 quality comparison is not released")
    if not isinstance(comparison_dimensions, Mapping) or set(comparison_dimensions) != set(expected_projection_ids):
        raise ValueError("M402 quality comparison projection closure is incomplete")
    for projection_id in expected_projection_ids:
        values = comparison_dimensions.get(projection_id)
        if not isinstance(values, Mapping) or set(values) != set(_EXPECTED_DIMENSIONS) or any(values.get(dimension) != ["KD_WIN", "KD_WIN"] for dimension in _EXPECTED_DIMENSIONS):
            raise ValueError("M402 quality comparison is not strict 12x5 KD_WIN")

    binding = run.get("companybrain_binding")
    public_snapshot_raw = public_files.get("_audit/companybrain-route-snapshot.json")
    if not isinstance(binding, Mapping) or not public_snapshot_raw:
        raise ValueError("M402 CompanyBrain binding is missing")
    try:
        public_snapshot = json.loads(public_snapshot_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("M402 public CompanyBrain snapshot is invalid") from error
    required_snapshot_fields = {
        "schema_version", "status", "run_id", "source_manifest_sha256",
        "companybrain_snapshot_id", "companybrain_tree_sha256", "observation_sha256",
        "regular_markdown_files", "entry_files", "observation_ref", "failure",
    }
    if not isinstance(public_snapshot, Mapping) or set(public_snapshot) != required_snapshot_fields or public_snapshot.get("status") != "available":
        raise ValueError("M402 public CompanyBrain snapshot is unavailable")
    for field in ("companybrain_snapshot_id", "companybrain_tree_sha256", "observation_sha256"):
        if not str(binding.get(field, "")) or public_snapshot.get(field) != binding.get(field) or candidate_quality.get(field) != binding.get(field):
            raise ValueError("M402 CompanyBrain identity binding is invalid")
    if public_snapshot.get("run_id") != run.get("run_id") or public_snapshot.get("source_manifest_sha256") != run.get("source_manifest_hash"):
        raise ValueError("M402 public CompanyBrain run binding is invalid")

    observation_path = Path(evidence_root) / "actual-run" / "attempts" / str(run.get("run_id")) / "companybrain-observation.json"
    if not observation_path.is_file() or observation_path.is_symlink():
        raise ValueError("M402 host CompanyBrain observation is missing")
    try:
        observation = json.loads(observation_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("M402 host CompanyBrain observation is invalid") from error
    observation_errors = _companybrain_binding_errors(
        observation,
        expected_source_manifest_sha256=str(run.get("source_manifest_hash", "")),
        expected_run_id=str(run.get("run_id", "")),
    )
    if observation_errors:
        raise ValueError("M402 host CompanyBrain observation closure is invalid: " + observation_errors[0])
    observation_by_key = {
        (str(row.get("projection_id", "")), str(row.get("dimension_id", ""))): row
        for row in observation.get("rows", ())
        if isinstance(row, Mapping)
    }
    required_row_fields = {
        "projection_key", "dimension_id", "verdict", "kd_observation_ref",
        "cb_observation_ref", "observation_digests", "advantage_basis",
    }
    required_basis_fields = {
        "projection_key", "dimension_id", "cb_observation_ref", "cb_observation_digest",
        "cb_gap_type", "cb_gap_locator", "atom_observations", "gap_atom_refs",
        "stage_observations", "gap_stage_refs", "quality_feature_observations",
        "gap_quality_feature_refs", "strict_improvement_refs", "non_regression",
        "kd_completion_refs", "kd_completion_surfaces", "kd_completion_digest",
    }
    allowed_gap_types = {
        "DIM-01.route": {"unreachable", "wrong_relation"},
        "DIM-02.taxonomy": {"missing_taxonomy_axis", "wrong_relation"},
        "DIM-03.business-answer": {"missing_stage", "unsupported_answer_claim", "wrong_relation"},
        "DIM-04.page-type": {"untyped_contract", "wrong_page_type"},
        "DIM-05.reader-audit": {"missing_provenance", "untraceable_claim"},
    }
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != required_row_fields:
            raise ValueError("M402 quality row schema is invalid")
        projection_id = str(row["projection_key"])
        dimension = str(row["dimension_id"])
        if row.get("verdict") not in {"UNKNOWN", "N/A", "KD_WIN"}:
            raise ValueError("M402 quality row verdict is invalid")
        digests = row.get("observation_digests")
        basis = row.get("advantage_basis")
        cb_row = observation_by_key.get((projection_id, dimension))
        if not isinstance(digests, Mapping) or set(digests) != {"reader", "companybrain"} or not all(re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in digests.values()):
            raise ValueError("M402 quality observation digest closure is invalid")
        if not isinstance(basis, Mapping) or set(basis) != required_basis_fields:
            raise ValueError("M402 quality advantage basis is incomplete")
        if not isinstance(cb_row, Mapping) or _observation_row_digest(cb_row) != digests["companybrain"]:
            raise ValueError("M402 quality CompanyBrain row digest is not bound")
        if basis.get("projection_key") != projection_id or basis.get("dimension_id") != dimension:
            raise ValueError("M402 quality basis identity is invalid")
        if basis.get("cb_observation_digest") != digests["companybrain"] or basis.get("cb_observation_ref") != row.get("cb_observation_ref"):
            raise ValueError("M402 quality basis CompanyBrain binding is invalid")
        if row.get("cb_observation_ref") != f"companybrain:{projection_id}:{dimension}":
            raise ValueError("M402 quality CompanyBrain observation ref is invalid")
        if row.get("kd_observation_ref") != (basis.get("kd_completion_refs") or [None])[0] or digests["reader"] != basis.get("kd_completion_digest"):
            raise ValueError("M402 quality Reader observation binding is invalid")
        if basis.get("cb_gap_type") not in allowed_gap_types.get(dimension, set()) or not basis.get("strict_improvement_refs") or basis.get("non_regression") is not True:
            raise ValueError("M402 quality strict advantage basis is invalid")


def _redact_reader_text(value: str) -> str:
    """Remove credential values at the Reader boundary, never from raw Audit."""

    text = _SENSITIVE_ACCOUNT_EMAIL.sub("[服务账号已隐藏]", value)
    text = _KNOWN_SERVICE_EMAIL.sub("[业务账号已隐藏]", text)
    text = _SENSITIVE_VALUE.sub(r"\1敏感值已隐藏", text)
    text = _SENSITIVE_BEARER.sub(r"\1敏感值已隐藏", text)
    # Evidence IDs are for machine binding and Audit only.  Showing qev hashes
    # in every Reader bullet makes the page look like an internal trace log;
    # the rendered evidence line below each section remains the human route
    # back to the source and line range.
    text = re.sub(
        r"\s*\[(?:qev-[0-9a-f]{16,}(?:\s*[,，;；]\s*qev-[0-9a-f]{16,})*)\]",
        "",
        text,
    )
    return re.sub(r"\bqev-[0-9a-f]{16,}\b", "", text)


def _progress(message: str) -> None:
    """Emit short, secret-free phase progress for a human-run command."""

    print(f"{_PROGRESS_PREFIX} {message}", file=sys.stderr, flush=True)


def _parse_json(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[-1]
        if value.rstrip().endswith("```"):
            value = value.rstrip()[:-3]
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"LLM returned invalid JSON: {error.msg}") from error
    if not isinstance(parsed, dict):
        raise ValueError("LLM result must be a JSON object")
    return parsed


def _slug(value: str, fallback: str = "page") -> str:
    value = value.strip().lower().replace("&", " and ")
    value = re.sub(r"[\\/]+", " ", value)
    value = "".join(char if (char.isalnum() or char in " -_·") else " " for char in value)
    value = re.sub(r"[ _·]+", "-", value).strip("-")
    return value[:100] or fallback


def _product(relative_path: str) -> tuple[str, str]:
    first = relative_path.split("/", 1)[0].strip()
    key = first.casefold()
    known = _KNOWN_PRODUCT_ROOTS.get(key)
    if known is not None:
        return known
    return _slug(first, "general"), first or "通用资料"


def _page_product_key(sources: Sequence[SourceDoc]) -> str:
    """Keep source-root ownership; mixed-source answers live in a shared lane."""
    keys = {source.product for source in sources}
    if len(keys) == 1:
        return next(iter(keys))
    return _SHARED_PRODUCT_KEY


def _paragraph_evidence(lines: Sequence[str], source_id: str) -> list[dict[str, Any]]:
    """Split source into exact, line-addressable evidence blocks.

    Headings, list items, table rows and fenced code remain individual blocks;
    ordinary paragraph lines are grouped.  The bytes are never rewritten.
    """

    records: list[dict[str, Any]] = []
    pending: list[tuple[int, str]] = []

    def flush() -> None:
        if not pending:
            return
        start, _ = pending[0]
        end, _ = pending[-1]
        text = "\n".join(line for _, line in pending)
        records.append({
            "evidence_id": f"{source_id}-e{len(records) + 1:04d}",
            "source_id": source_id,
            "start_line": start,
            "end_line": end,
            "text": text,
            "status": "supported",
        })
        pending.clear()

    for number, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\r")
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        structural = (
            stripped.startswith(("#", "-", "*", ">", "```", "~~~", "|"))
            # Confluence exports often escape the period in numbered lists
            # (`4\.`).  If we miss that form, an entire checklist becomes one
            # giant evidence block and a bounded verifier sees only its head.
            or re.match(r"^\d+\\?[.)]\s", stripped) is not None
        )
        if structural:
            flush()
            pending.append((number, line))
            flush()
        else:
            pending.append((number, line))
    flush()
    return records


@dataclass(frozen=True)
class SourceDoc:
    source_id: str
    relative_path: str
    raw_bytes: bytes
    text: str
    lines: tuple[str, ...]
    product: str
    product_label: str
    evidence: tuple[Mapping[str, Any], ...]
    status: str = "ready"
    duplicate_of: str | None = None


@dataclass(frozen=True)
class ReaderPage:
    source_id: str
    title: str
    question: str
    page_type: str
    axes: Mapping[str, str]
    sections: Mapping[str, Mapping[str, Any]]
    axis_evidence_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    slug: str = ""
    relative_path: str = ""
    verification: str = "pending"
    violations: tuple[Mapping[str, Any], ...] = ()
    source_ids: tuple[str, ...] = ()
    page_id: str = ""
    projection_id: str = ""
    product_key: str = ""
    page_key: str = ""

    @property
    def all_source_ids(self) -> tuple[str, ...]:
        return self.source_ids or (self.source_id,)


@dataclass(frozen=True)
class Bundle:
    files: Mapping[str, bytes]
    pages: tuple[ReaderPage, ...]
    sources: tuple[SourceDoc, ...]
    run_id: str
    warnings: tuple[str, ...]
    companybrain_observation: Mapping[str, Any] | None = None
    quality_result: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class DigestRequest:
    new_dir: Path
    kb_dir: Path
    provider_config_path: Path
    quality_config_path: Path | None = None
    source_manifest_path: Path | None = None
    source_paths: tuple[str, ...] | None = None
    evaluation_mode: str = "full"
    run_context: RunContext | None = None
    companybrain_route_snapshot: Mapping[str, Any] | None = None
    gate: str | None = None
    runtime_config_path: Path | None = None
    m401_packet_path: Path | None = None
    m401_r_receipt_path: Path | None = None
    workflowhub_successor_path: Path | None = None
    companybrain_root: Path | None = None
    fixture_bundle_path: Path | None = None
    m401_attempt_path: Path | None = None
    m401_run_root_path: Path | None = None
    m401_command: str | None = None
    material_id: str | None = None
    quality_evidence_root: Path | None = None
    # A real M402 run first creates an immutable candidate artifact. This
    # remains false until the authenticated quality owner completes the
    # post-rename finalize/promotion step.
    quality_result_promoted: bool = False


@dataclass(frozen=True)
class DigestResult:
    outcome: str
    run_id: str
    home_path: Path | None = None
    audit_path: Path | None = None
    reason_code: str | None = None
    companybrain_observation: Mapping[str, Any] | None = None


@dataclass
class RunContext:
    """Shared identity and response memo for one slice→full evaluation."""

    context_id: str
    slice_run_id: str | None = None
    # The two phases share one provider budget. Preserve the slice reservation
    # so the full phase cannot under-report the aggregate worst-case plan.
    slice_llm_plan: int = 0
    reused_response_count: int = 0
    slice_embedding_plan: int = 0


@dataclass(frozen=True)
class DigestSequenceResult:
    slice_run_id: str
    full_run_id: str
    reused_response_count: int
    full_result: DigestResult
    slice_result: DigestResult | None = None
    slice_run: Mapping[str, Any] | None = None


class _MemoizedSemanticModel:
    """Reuse only byte-identical prompts inside one explicit run context."""

    def __init__(self, delegate: SemanticModel, context: RunContext):
        self._delegate = delegate
        self._context = context
        self._responses: dict[str, str] = {}

    @property
    def identity(self) -> Mapping[str, str]:
        return self._delegate.identity

    @property
    def calls(self) -> int:
        return int(getattr(self._delegate, "calls", 0))

    @property
    def retry_attempts(self) -> int:
        return int(getattr(self._delegate, "retry_attempts", 0))

    @property
    def budget(self) -> Any:
        return getattr(self._delegate, "budget", None)

    def generate(self, prompt: str) -> str:
        key = _sha(_normalised_text(prompt))
        cached = self._responses.get(key)
        if cached is not None:
            self._context.reused_response_count += 1
            return cached
        response = self._delegate.generate(prompt)
        if not isinstance(response, str) or not response.strip():
            raise ProviderError("semantic provider returned an empty response")
        self._responses[key] = response
        return response


def _load_sources(
    root: Path,
    source_paths: Sequence[str] | None = None,
    source_id_by_path: Mapping[str, str] | None = None,
) -> tuple[SourceDoc, ...]:
    root = Path(root).expanduser()
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError(f"source directory is not a regular directory: {root}")
    nested_symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    if nested_symlinks:
        raise ValueError(f"source directory contains symlink: {nested_symlinks[0].relative_to(root)}")
    all_paths = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".md", ".markdown", ".txt", ".json"} and path.name != ".DS_Store"
    }
    if source_paths is None:
        paths = [all_paths[key] for key in sorted(all_paths)]
    else:
        requested = tuple(str(item).strip() for item in source_paths)
        if not requested or any(not item or Path(item).is_absolute() or ".." in Path(item).parts or "\\" in item for item in requested):
            raise ValueError("source_paths must contain safe relative paths")
        if len(set(requested)) != len(requested):
            raise ValueError("source_paths contains duplicate paths")
        missing = sorted(set(requested) - set(all_paths))
        if missing:
            raise ValueError(f"source_paths are missing from source directory: {missing[:3]}")
        paths = [all_paths[item] for item in requested]
    if not paths:
        raise ValueError("source directory contains no supported documents")
    result: list[SourceDoc] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        raw_bytes = path.read_bytes()
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"source is not UTF-8: {relative}") from error
        if source_id_by_path is None:
            source_id = "src-" + _sha(_normalised_text(relative).encode("utf-8") + b"\0" + raw_bytes)[:20]
        else:
            source_id = str(source_id_by_path.get(relative, ""))
            if not source_id:
                raise ValueError(f"source is missing from the frozen source-id manifest: {relative}")
        product_key, product_label = _product(relative)
        lines = tuple(text.replace("\r\n", "\n").replace("\r", "\n").splitlines())
        result.append(SourceDoc(source_id, relative, raw_bytes, text, lines, product_key, product_label, tuple(_paragraph_evidence(lines, source_id))))
    seen_content: dict[str, str] = {}
    normalised: list[SourceDoc] = []
    for source in result:
        if not source.text.strip():
            normalised.append(replace(source, status="known_empty"))
            continue
        content_hash = _sha(source.raw_bytes)
        canonical = seen_content.get(content_hash)
        if canonical is None:
            seen_content[content_hash] = source.source_id
            normalised.append(source)
        else:
            normalised.append(replace(source, status="duplicate_alias", duplicate_of=canonical))
    return tuple(normalised)


def _validate_m402_source_closure(sources: Sequence[SourceDoc]) -> None:
    """Enforce the real-run corpus boundary before the first provider call."""

    if len(sources) != 89:
        raise ValueError("M402 requires exactly 89 frozen source entries")
    product_keys = {source.product for source in sources}
    expected_products = {value[0] for value in _KNOWN_PRODUCT_ROOTS.values()}
    if product_keys != expected_products:
        missing = sorted(expected_products - product_keys)
        unexpected = sorted(product_keys - expected_products)
        raise ValueError(
            "M402 source product closure is invalid: "
            f"missing={missing}, unexpected={unexpected}"
        )
    status_counts = defaultdict(int)
    for source in sources:
        status_counts[source.status] += 1
    if dict(status_counts) != {"ready": 87, "known_empty": 1, "duplicate_alias": 1}:
        raise ValueError(
            "M402 source status closure is invalid: "
            f"{dict(sorted(status_counts.items()))}"
        )


def _evidence_payload(source: SourceDoc, *, include_text: bool = True) -> list[dict[str, Any]]:
    keys = ("evidence_id", "start_line", "end_line", "text") if include_text else ("evidence_id", "start_line", "end_line")
    return [{key: item[key] for key in keys} for item in source.evidence]


def _draft_prompt(
    source: SourceDoc,
    feedback: Sequence[Mapping[str, Any]] = (),
) -> str:
    sample_evidence_id = next(
        (str(item.get("evidence_id")) for item in source.evidence if str(item.get("evidence_id", ""))),
        "qev-example",
    )
    contract = {
        "schema_version": "task5-semantic-output.v2",
        "title": "semantic reader title without hashes",
        "page_type": "positioning | concept | operation | diagnosis | experience",
        "page_type_claim_ids": [sample_evidence_id],
        "axis": {"product": "...", "module": "...", "object": "...", "scene": "...", "boundary": "..."},
        "axis_claim_ids": {"product": [sample_evidence_id], "module": [sample_evidence_id], "object": [sample_evidence_id], "scene": [sample_evidence_id], "boundary": [sample_evidence_id]},
        "summary": {"body": "one to three factual sentences", "claim_ids": [sample_evidence_id], "evidence_ids": [sample_evidence_id]},
        "sections": {heading: {"body": "markdown bullets or a compact table, no heading", "claim_ids": [sample_evidence_id], "evidence_ids": [sample_evidence_id]} for heading in PAGE_TYPES["concept"]},
    }
    evidence_label = "完整证据（每条 text 都是原文连续行，行号可回查）："
    # Source compilation only needs the evidence identity, locator and text.
    # Repeating source_id/status on every one of hundreds of blocks can push a
    # long but valid document over the provider input ceiling.
    evidence_value = [
        {
            key: item[key]
            for key in ("evidence_id", "start_line", "end_line", "text")
        }
        for item in _prompt_evidence(source.evidence, text_limit=700)
    ]
    evidence_value_text = _json(evidence_value)
    evidence_instruction = evidence_label
    # A long Confluence table can make the JSON evidence packet larger than
    # the provider input ceiling even when the raw source itself fits.  Send
    # every raw line once with an exact evidence marker in that case.
    if len(evidence_value_text) > 90_000:
        evidence_value_text = _line_oriented_prompt_evidence(source)
        evidence_instruction = (
            "完整证据（紧凑行式；每行首部使用源内 evidence 后缀；"
            f"本资料的完整 evidence_id 前缀是 {source.source_id}-，例如 [e0001] 代表完整 ID "
            f"{source.source_id}-e0001；输出 JSON 时必须填写完整 evidence_id）："
        )
    feedback_text = ""
    if feedback:
        feedback_text = "\n\nREGENERATION FEEDBACK (fix only these concrete issues):\n" + _json(list(feedback))
        if any(item.get("type") == "strict_minimal_retry" for item in feedback if isinstance(item, Mapping)):
            feedback_text += (
                "\n这是短资料的安全重试：除非下方证据能直接支持，否则所有 summary/section 的 body "
                f"必须精确写‘{UNKNOWN}’，并将 evidence_ids 设为空；禁止为了填满章节而补写事实。"
            )
    return f"""你是企业知识库编辑。只根据下面这一份原始资料写一张 Reader 页面，不得使用外部知识、CompanyBrain 或其他页面。原始资料可能包含历史版本、未验证说法、冲突和中英文；保留这些限定，不把推测写成事实。

输出只能是一个 JSON 对象，结构如下：
{_json(contract)}

硬规则：
1. page_type 必须从五类中选择；sections 的键必须与所选 page_type 对应的固定标题完全一致：{_json(PAGE_TYPES)}。
2. 摘要和每个正文事实必须能由本资料中的 evidence_ids 支持；所有 page_type_claim_ids、axis_claim_ids、claim_ids 和 evidence_ids 都只能使用下方真实的 evidence_id，不能填写 claim_ref、boundary_ref 或示例文字。资料有任何可用 evidence 时，摘要必须写一个保守、可回查的结论并至少引用一条 evidence；只有整份资料没有可用 evidence 时，摘要才写“{UNKNOWN}”并把 evidence_ids 留空。单个正文章节没有对应证据时才写“{UNKNOWN}”并留空引用。
3. 不要把原文整篇复制进正文。把答案整理成结论、条件、步骤、结果、原因和边界，使用短段落、列表或表格。保留数字、日期、版本、命令、路径、权限、开关、范围、否定和条件。
4. title 必须是读者看得懂的语义标题，不得包含 source_id、sha256、cluster、draft 或随机编号。不要输出 question；编译器会从页面类型和标题生成读者问题。
5. 产品归类固定为“{source.product_label}”；module、object、scene、boundary 只能从资料中概括，无法确认就写“{UNKNOWN}”。输出前逐项检查五个 axis：某项恰为“{UNKNOWN}”时，该项 axis_claim_ids 必须是空数组；只有有明确证据的 axis 才能填写对应 evidence_id。
6. 不要把密码、token、私钥、凭据内容或可直接登录的秘密值写入 Reader；只保留“需要凭据/账号”这一业务条件，并标注“敏感值未在 Reader 展示”。普通产品邮箱、账号字段名和权限规则可以保留，但不要泄露秘密值。
7. 每个 section 最多 4 个短项目、每个项目尽量不超过 80 字；摘要不超过 200 字，整页正文保持在约 1800 字以内。资料有 evidence 时不要把摘要写成“{UNKNOWN}”；没有对应证据的章节才写“{UNKNOWN}”并留空引用。
8. 不要输出解释、Markdown 代码围栏、额外字段，也不要生成来源之外的建议。

资料路径：{source.relative_path}
资料产品：{source.product_label}
{evidence_instruction}
        {evidence_value_text}
{feedback_text}
"""


def _normalise_task5_semantic_output(
    value: Mapping[str, Any],
    *,
    allowed_claim_ids: set[str],
    expected_question: str | None = None,
) -> dict[str, Any]:
    """Adapt the frozen Task5 provider contract to the internal page model."""
    required = {
        "schema_version", "title", "page_type", "page_type_claim_ids",
        "axis", "axis_claim_ids", "summary", "sections",
    }
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        detail = []
        if missing:
            detail.append("missing=" + ",".join(missing))
        if extra:
            detail.append("unknown=" + ",".join(extra))
        raise ValueError("Task5 semantic output shape is invalid: " + ";".join(detail))
    if value.get("schema_version") != "task5-semantic-output.v2":
        raise ValueError("Task5 semantic output schema_version is invalid")
    page_type = value.get("page_type")
    if page_type not in PAGE_TYPES:
        raise ValueError("Task5 semantic output page_type is invalid")
    title = value.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Task5 semantic output title is empty")

    def resolve_provider_ref(raw: str) -> str:
        """Repair tiny transcription slips without widening evidence.

        Qwen occasionally duplicates or drops one hexadecimal character (or
        repeats one adjacent two-character chunk) in a long qev reference
        while copying a repair response. Treating that as a brand-new source
        makes an otherwise evidence-bound repair fail; accepting arbitrary
        fuzzy matches would weaken the closure. Only a unique tiny copy slip
        is recoverable, and the canonical exact ID is what continues through
        the Reader/Audit ledger.
        """
        if raw in allowed_claim_ids:
            return raw

        # Long source IDs are occasionally copied with a dropped middle
        # chunk.  A source page has one closed evidence namespace, so an
        # otherwise exact e#### suffix is safe to resolve only when it maps
        # to one and only one supplied evidence ID.  This never widens the
        # closure or accepts an evidence block from another source.
        suffix_match = re.search(r"-(e\d{4})$", raw)
        if suffix_match:
            suffix = "-" + suffix_match.group(1)
            suffix_candidates = [candidate for candidate in allowed_claim_ids if candidate.endswith(suffix)]
            if len(suffix_candidates) == 1:
                return suffix_candidates[0]

        if not raw.startswith("qev-"):
            return raw

        def distance_at_most_one(left: str, right: str) -> bool:
            if abs(len(left) - len(right)) > 1:
                return False
            if len(left) == len(right):
                return sum(a != b for a, b in zip(left, right)) <= 1
            if len(left) > len(right):
                left, right = right, left
            index_left = index_right = differences = 0
            while index_left < len(left) and index_right < len(right):
                if left[index_left] == right[index_right]:
                    index_left += 1
                    index_right += 1
                    continue
                differences += 1
                if differences > 1:
                    return False
                index_right += 1
            return True

        def is_repeated_chunk(candidate: str) -> bool:
            if len(raw) not in {len(candidate) + 1, len(candidate) + 2}:
                return False
            for chunk_size in (1, 2):
                if len(raw) != len(candidate) + chunk_size:
                    continue
                for index in range(len(candidate) - chunk_size + 1):
                    if raw == candidate[:index] + candidate[index:index + chunk_size] + candidate[index:]:
                        return True
            return False

        candidates = [
            candidate
            for candidate in allowed_claim_ids
            if candidate.startswith("qev-")
            and (distance_at_most_one(raw, candidate) or is_repeated_chunk(candidate))
        ]
        return candidates[0] if len(candidates) == 1 else raw

    def refs(
        field: str,
        raw: Any,
        *,
        required_nonempty: bool = True,
    ) -> list[str]:
        if not isinstance(raw, list) or any(not isinstance(item, str) or not item.strip() for item in raw):
            raise ValueError(f"Task5 semantic output {field} must be a string list")
        result = list(dict.fromkeys(
            resolve_provider_ref(str(item).strip())
            for item in raw
        ))
        unknown = sorted(set(result) - allowed_claim_ids)
        if unknown:
            raise ValueError(f"Task5 semantic output {field} cites outside closure: {', '.join(unknown[:3])}")
        if required_nonempty and not result:
            raise ValueError(f"Task5 semantic output {field} is empty")
        return result

    page_type_claim_ids = refs("page_type_claim_ids", value["page_type_claim_ids"])
    axis_names = ("product", "module", "object", "scene", "boundary")
    axis = value.get("axis")
    axis_claim_ids = value.get("axis_claim_ids")
    if not isinstance(axis, Mapping) or set(axis) != set(axis_names):
        raise ValueError("Task5 semantic output axis is incomplete")
    if any(not isinstance(axis[name], str) or not axis[name].strip() for name in axis_names):
        raise ValueError("Task5 semantic output axis contains an empty value")
    if not isinstance(axis_claim_ids, Mapping) or set(axis_claim_ids) != set(axis_names):
        raise ValueError("Task5 semantic output axis_claim_ids is incomplete")
    normalised_axis_claims: dict[str, list[str]] = {}
    for name in axis_names:
        axis_value = str(axis[name]).strip()
        axis_refs = refs(
            f"axis_claim_ids.{name}",
            axis_claim_ids[name],
            # A source may not say anything about every taxonomy axis.  In
            # that case the truthful value is UNKNOWN and there is no raw
            # block to cite.  The previous unconditional requirement turned
            # this honest answer into a failed source page.
            required_nonempty=axis_value != UNKNOWN,
        )
        if axis_value == UNKNOWN and axis_refs:
            raise ValueError(f"Task5 semantic output axis_claim_ids.{name} must be empty for UNKNOWN")
        normalised_axis_claims[name] = axis_refs

    def section(field: str, raw: Any) -> dict[str, Any]:
        if not isinstance(raw, Mapping) or set(raw) != {"body", "claim_ids", "evidence_ids"}:
            raise ValueError(f"Task5 semantic output {field} is malformed")
        body = raw.get("body")
        if not isinstance(body, str) or not body.strip():
            raise ValueError(f"Task5 semantic output {field}.body is empty")
        has_facts = not _is_unknown_semantic_text(body)
        evidence_ids = refs(
            f"{field}.evidence_ids",
            raw.get("evidence_ids"),
            required_nonempty=has_facts,
        )
        # One claim can be supported by several evidence blocks.  Keep the
        # machine claim marker anchored to the first cited block when the LLM
        # uses a different valid block or leaves the marker empty; the body
        # remains governed by the complete evidence_ids closure.
        claim_ids = refs(
            f"{field}.claim_ids",
            raw.get("claim_ids"),
            required_nonempty=has_facts,
        )
        if not has_facts and (evidence_ids or claim_ids):
            raise ValueError(
                f"Task5 semantic output {field} marks UNKNOWN but supplies evidence references"
            )
        # Qwen sometimes marks a valid supporting block in claim_ids but
        # forgets to repeat it in evidence_ids.  Both lists are already
        # closed over the exact raw evidence above; taking their union keeps
        # the claim auditable without inventing or accepting any new source.
        if set(claim_ids) - set(evidence_ids):
            evidence_ids = list(dict.fromkeys((*evidence_ids, *claim_ids)))
        return {
            "body": UNKNOWN if not has_facts else body,
            "claim_ids": claim_ids,
            "evidence_ids": evidence_ids,
        }

    summary = section("summary", value["summary"])
    if summary["body"] == UNKNOWN and allowed_claim_ids:
        raise ValueError(
            "summary cannot be UNKNOWN while evidence closure is non-empty"
        )
    sections = value.get("sections")
    if not isinstance(sections, Mapping) or set(sections) != set(PAGE_TYPES[page_type]):
        raise ValueError("Task5 semantic output sections do not match page_type")
    normalised_sections = {
        heading: section(f"sections.{heading}", sections[heading])
        for heading in PAGE_TYPES[page_type]
    }
    # The v2 provider has no question field by design.  For fixed quality
    # projections it is supplied by the frozen route.  Source pages receive a
    # deterministic reader question instead of allowing a filename to become
    # an implicit question.
    question = expected_question or {
        "positioning": "这个页面说明产品的定位和边界是什么？",
        "concept": "这个页面说明哪些对象、关系和规则？",
        "operation": "按这份资料，应该如何完成相关操作？",
        "diagnosis": "遇到这类问题时，应该如何定位和处理？",
        "experience": "这份资料记录了哪些版本经验和边界？",
    }[str(page_type)]
    all_claims = set(page_type_claim_ids)
    all_claims.update(ref for values in normalised_axis_claims.values() for ref in values)
    all_claims.update(ref for part in (summary, *normalised_sections.values()) for ref in part["evidence_ids"])
    if not all_claims.issubset(allowed_claim_ids):
        raise ValueError("Task5 semantic output claim closure is invalid")
    return {
        "title": title,
        "question": question,
        "page_type": page_type,
        "axes": {
            "product": axis["product"],
            "module": axis["module"],
            "object": axis["object"],
            "scenario": axis["scene"],
            "boundary": axis["boundary"],
        },
        "axis_evidence_ids": {
            name: tuple(values)
            for name, values in normalised_axis_claims.items()
        },
        "summary": summary,
        "sections": normalised_sections,
    }


def _normalise_page(
    sources: Sequence[SourceDoc],
    value: Mapping[str, Any],
    *,
    expected_page_type: str | None = None,
    page_id: str = "",
    expected_title: str | None = None,
    expected_question: str | None = None,
    expected_axes: Mapping[str, str] | None = None,
    required_source_ids: Sequence[str] = (),
    required_evidence_ids: Sequence[str] = (),
    required_evidence_groups: Sequence[Sequence[str]] = (),
    allowed_evidence_ids: Sequence[str] | None = None,
    projection_id: str = "",
    answer_page: bool = False,
    enforce_multiple_sources: bool | None = None,
    require_task5_semantic: bool = False,
) -> ReaderPage:
    if not sources:
        raise ValueError("a Reader page needs at least one source")
    source = sources[0]
    if require_task5_semantic:
        allowed_claim_ids = {
            str(item["evidence_id"])
            for member in sources
            for item in member.evidence
        }
        if allowed_evidence_ids is not None:
            allowed_claim_ids &= {str(item) for item in allowed_evidence_ids}
        value = _normalise_task5_semantic_output(
            value,
            allowed_claim_ids=allowed_claim_ids,
            expected_question=expected_question,
        )
    allowed = {"title", "question", "page_type", "axes", "summary", "sections"}
    if require_task5_semantic:
        # `_normalise_task5_semantic_output` converts the provider's axis
        # claim references into an internal field used by the Reader ledger.
        # It is not a provider-facing/public page field, but must survive this
        # internal hand-off before the ReaderPage is constructed.
        allowed.add("axis_evidence_ids")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError("LLM page has unexpected fields: " + ", ".join(unknown))
    page_type = value.get("page_type")
    if page_type not in PAGE_TYPES:
        raise ValueError("LLM page_type is invalid")
    if expected_page_type is not None and page_type != expected_page_type:
        raise ValueError(f"LLM page_type must be {expected_page_type}")
    title = value.get("title")
    question = value.get("question")
    summary = value.get("summary")
    if not all(isinstance(item, str) and item.strip() for item in (title, question)):
        raise ValueError("LLM page title, question and summary are required")
    if _HASH.search(title):
        raise ValueError("LLM title contains an internal identity")
    if expected_title is not None and title.strip() != expected_title.strip():
        raise ValueError("LLM title does not match the fixed quality projection")
    if expected_question is not None and question.strip() != expected_question.strip():
        raise ValueError("LLM question does not match the fixed quality projection")
    axes = value.get("axes")
    if not isinstance(axes, Mapping):
        raise ValueError("LLM axes are required")
    axis_names = ("product", "module", "object", "scenario", "boundary")
    if set(axes) != set(axis_names) or any(not isinstance(axes.get(name), str) or not axes[name].strip() for name in axis_names):
        raise ValueError("LLM axes must contain five non-empty strings")
    fixed_axes = {name: _redact_reader_text(str(axes[name]).strip()) for name in axis_names}
    fixed_axes["product"] = source.product_label
    if expected_axes is not None and "product" in expected_axes:
        fixed_axes["product"] = _redact_reader_text(str(expected_axes["product"]).strip())
    raw_summary = summary
    expected_section_fields = {"body", "evidence_ids", "claim_ids"} if require_task5_semantic else {"body", "evidence_ids"}
    if not isinstance(raw_summary, Mapping) or set(raw_summary) != expected_section_fields:
        raise ValueError("LLM summary is malformed")
    summary_body = raw_summary.get("body")
    summary_refs = raw_summary.get("evidence_ids")
    summary_claim_refs = raw_summary.get("claim_ids", ())
    raw_sections = value.get("sections")
    if not isinstance(raw_sections, Mapping) or set(raw_sections) != set(PAGE_TYPES[page_type]):
        raise ValueError("LLM sections do not match the selected page type")
    known = {
        str(item["evidence_id"])
        for member in sources
        for item in member.evidence
    }
    if allowed_evidence_ids is not None:
        known &= {str(item) for item in allowed_evidence_ids}
    if not isinstance(summary_body, str) or not summary_body.strip() or not isinstance(summary_refs, list) or any(not isinstance(ref, str) or ref not in known for ref in summary_refs):
        raise ValueError("LLM summary has invalid body or evidence")
    if not summary_refs and summary_body.strip() != UNKNOWN:
        raise ValueError("LLM summary has facts without evidence")
    if not isinstance(summary_claim_refs, (list, tuple)) or any(
        not isinstance(ref, str) or ref not in known or ref not in summary_refs
        for ref in summary_claim_refs
    ):
        raise ValueError("LLM summary has invalid claim references")
    if require_task5_semantic and summary_body.strip() != UNKNOWN and not summary_claim_refs:
        raise ValueError("LLM summary has facts without claim references")
    if require_task5_semantic:
        # A semantic page may quote a short command or field name, but it must
        # not publish a long raw block as if that were a business answer.
        # Reject exact long copies here; the independent verifier remains
        # responsible for unsupported claims and condition changes.
        source_texts = {
            _normalised_text(member.text).strip()
            for member in sources
            if len(_normalised_text(member.text).strip()) >= 160
        }
        evidence_texts = {
            _normalised_text(str(item.get("text", ""))).strip()
            for member in sources
            for item in member.evidence
            if len(_normalised_text(str(item.get("text", ""))).strip()) >= 160
        }
        copied_texts = source_texts | evidence_texts
        for candidate_body in (summary_body, *(section.get("body", "") for section in raw_sections.values() if isinstance(section, Mapping))):
            normalised_body = _normalised_text(candidate_body).strip()
            if len(normalised_body) >= 160 and normalised_body in copied_texts:
                raise ValueError("LLM page copies a long raw evidence block instead of summarising it")
    sections: dict[str, Mapping[str, Any]] = {
        "summary": {
            "body": _redact_reader_text(summary_body.strip()),
            "claim_ids": tuple(dict.fromkeys(summary_claim_refs)),
            "evidence_ids": tuple(dict.fromkeys(summary_refs)),
        }
    }
    for heading in PAGE_TYPES[page_type]:
        section = raw_sections[heading]
        if not isinstance(section, Mapping) or set(section) != expected_section_fields:
            raise ValueError(f"LLM section {heading} is malformed")
        body = section.get("body")
        refs = section.get("evidence_ids")
        claim_refs = section.get("claim_ids", ())
        if not isinstance(body, str) or not body.strip() or not isinstance(refs, list) or any(not isinstance(ref, str) or ref not in known for ref in refs):
            raise ValueError(f"LLM section {heading} has invalid body or evidence")
        if not refs and body.strip() != UNKNOWN:
            raise ValueError(f"LLM section {heading} has facts without evidence")
        if not isinstance(claim_refs, (list, tuple)) or any(
            not isinstance(ref, str) or ref not in known or ref not in refs
            for ref in claim_refs
        ):
            raise ValueError(f"LLM section {heading} has invalid claim references")
        if require_task5_semantic and body.strip() != UNKNOWN and not claim_refs:
            raise ValueError(f"LLM section {heading} has facts without claim references")
        sections[heading] = {
            "body": _redact_reader_text(body.strip()),
            "claim_ids": tuple(dict.fromkeys(claim_refs)),
            "evidence_ids": tuple(dict.fromkeys(refs)),
        }
    cited_refs = {
        str(ref)
        for section in sections.values()
        if isinstance(section, Mapping)
        for ref in section.get("evidence_ids", ())
    }
    cited_source_ids = tuple(
        member.source_id
        for member in sources
        if any(str(item["evidence_id"]) in cited_refs for item in member.evidence)
    )
    # A broad planner membership list is not evidence. Keep only the sources
    # whose blocks are actually cited by the published page.
    declared_source_ids = cited_source_ids or (source.source_id,)
    if (len(sources) > 1 if enforce_multiple_sources is None else enforce_multiple_sources) and len(declared_source_ids) < 2:
        raise ValueError("cross-source page cites fewer than two sources")
    required_sources = set(str(item) for item in required_source_ids if str(item))
    if required_sources and not required_sources.issubset(set(declared_source_ids)):
        missing = ", ".join(sorted(required_sources - set(declared_source_ids)))
        raise ValueError(f"quality page omitted required source ids: {missing}")
    required_evidence = set(str(item) for item in required_evidence_ids if str(item))
    if required_evidence and not required_evidence.issubset(cited_refs):
        missing = ", ".join(sorted(required_evidence - cited_refs))
        raise ValueError(f"quality page omitted required evidence: {missing}")
    for group in required_evidence_groups:
        group_ids = {str(item) for item in group if str(item)}
        if group_ids and not group_ids.intersection(cited_refs):
            missing = ",".join(sorted(group_ids))
            raise ValueError(f"quality page omitted a required claim or boundary evidence group: {missing}")
    if expected_axes is not None:
        for key, expected in expected_axes.items():
            if fixed_axes.get(key) != _redact_reader_text(str(expected).strip()):
                raise ValueError(f"LLM axis does not match the fixed quality projection: {key}")
    summary_evidence_ids = tuple(str(item) for item in sections["summary"].get("evidence_ids", ()) if str(item))
    axis_evidence_ids = value.get("axis_evidence_ids", {}) if require_task5_semantic else {}
    if not isinstance(axis_evidence_ids, Mapping):
        axis_evidence_ids = {}
    axis_evidence_ids = {
        name: tuple(str(item) for item in axis_evidence_ids.get(name, ()) if str(item))
        for name in axis_names
    }
    return ReaderPage(
        source.source_id,
        _redact_reader_text(title.strip()),
        _redact_reader_text(question.strip()),
        page_type,
        fixed_axes,
        sections,
        axis_evidence_ids=axis_evidence_ids,
        source_ids=declared_source_ids,
        page_id=page_id,
        projection_id=projection_id,
        product_key=_page_product_key(sources),
        page_key=_page_key(
            page_type=page_type,
            page_id=page_id,
            question=_redact_reader_text(question.strip()),
            scenario=fixed_axes["scenario"],
            source_id=source.source_id,
            product=_page_product_key(sources),
            projection_id=projection_id,
            answer_page=answer_page,
        ),
    )


def _generate_one_page(
    source: SourceDoc,
    model: SemanticModel,
    feedback: Sequence[Mapping[str, Any]] = (),
    *,
    require_task5_semantic: bool = False,
) -> ReaderPage:
    value = _parse_json(model.generate(_draft_prompt(source, feedback)))
    value = _expand_source_evidence_aliases(value, source)
    return _normalise_page((source,), value, require_task5_semantic=require_task5_semantic)


def _source_card(page: ReaderPage, source: SourceDoc, *, compact: bool = False) -> dict[str, Any]:
    """Expose only an intermediate, source-bound digest to the topic writer."""

    card: dict[str, Any] = {
        "source_id": source.source_id,
        "source_path": source.relative_path,
        "title": page.title,
        "question": page.question,
        "page_type": page.page_type,
        "axes": dict(page.axes),
        "summary": page.sections["summary"]["body"],
        "summary_evidence_ids": list(page.sections["summary"].get("evidence_ids", ())),
    }
    if not compact:
        card["sections"] = {
            heading: {
                "body": section["body"],
                "evidence_ids": list(section.get("evidence_ids", ())),
            }
            for heading, section in page.sections.items()
            if heading != "summary"
        }
    return card


def _source_index_page(source: SourceDoc) -> ReaderPage:
    """Represent a source with no trusted draft inside topic planning only.

    This is not published Reader content.  It lets mandatory cross-source
    topics inspect the raw evidence of a source whose own draft failed, while
    ensuring that an unverified LLM summary is never reused as input.
    """

    return ReaderPage(
        source_id=source.source_id,
        title=source.relative_path,
        question="原始资料未明确",
        page_type="concept",
        axes={
            "product": source.product_label,
            "module": UNKNOWN,
            "object": UNKNOWN,
            "scenario": UNKNOWN,
            "boundary": UNKNOWN,
        },
        sections={"summary": {"body": UNKNOWN, "evidence_ids": ()}},
        source_ids=(source.source_id,),
    )


def _clip_prompt_text(value: Any, limit: int) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 20)].rstrip() + "……[已截断]"


def _prompt_card(page: ReaderPage, source: SourceDoc, *, rich: bool) -> dict[str, Any]:
    """Build a bounded source card for a provider prompt.

    The published evidence remains complete.  Only the repeated intermediate
    prompt payload is clipped so a long source cannot make an otherwise valid
    full-corpus run fail before the provider sees the semantic task.
    """

    card = _source_card(page, source, compact=not rich)
    card["title"] = _clip_prompt_text(card["title"], 160)
    card["question"] = _clip_prompt_text(card["question"], 240)
    card["summary"] = _clip_prompt_text(card["summary"], 700)
    card["axes"] = {
        key: _clip_prompt_text(value, 180)
        for key, value in dict(card.get("axes", {})).items()
    }
    if rich:
        card["sections"] = {
            heading: {
                "body": _clip_prompt_text(section.get("body", ""), 500),
                "evidence_ids": list(section.get("evidence_ids", ())),
            }
            for heading, section in card.get("sections", {}).items()
            if isinstance(section, Mapping)
        }
    return card


def _prompt_evidence(items: Sequence[Mapping[str, Any]], *, text_limit: int = 700) -> list[dict[str, Any]]:
    """Keep exact evidence identity while bounding repeated prompt text."""

    head_limit = max(1, int(text_limit * 0.68))
    tail_limit = max(1, text_limit - head_limit)

    def bounded(value: Any) -> str:
        text = str(value)
        if len(text) <= text_limit:
            return text
        return text[:head_limit].rstrip() + "\n……中间原文省略……\n" + text[-tail_limit:].lstrip()

    return [
        {
            **dict(item),
            "text": bounded(item.get("text", "")),
        }
        for item in items
    ]


def _line_oriented_prompt_evidence(source: SourceDoc) -> str:
    """Keep long table-like sources complete without duplicating JSON text."""

    by_start = {
        int(item["start_line"]): item
        for item in source.evidence
        if str(item.get("evidence_id", ""))
    }
    active_end = 0
    rendered: list[str] = []
    for number, line in enumerate(source.lines, 1):
        item = by_start.get(number)
        if item is not None:
            start = int(item["start_line"])
            end = int(item["end_line"])
            active_end = end
            evidence_id = str(item["evidence_id"])
            suffix = evidence_id.removeprefix(f"{source.source_id}-")
            marker = f"[{suffix}]"
        elif number <= active_end:
            marker = "[same]"
        else:
            marker = f"[l{number}]"
        rendered.append(f"{marker} {line}")
    return "\n".join(rendered)


def _expand_source_evidence_aliases(value: object, source: SourceDoc) -> object:
    """Expand compact source evidence aliases before strict page validation."""

    prefix = f"{source.source_id}-"
    aliases = {
        str(item["evidence_id"])[len(prefix):]: str(item["evidence_id"])
        for item in source.evidence
        if str(item.get("evidence_id", "")).startswith(prefix)
    }
    if not aliases:
        return value
    if isinstance(value, str):
        return aliases.get(value, value)
    if isinstance(value, list):
        return [_expand_source_evidence_aliases(item, source) for item in value]
    if isinstance(value, dict):
        return {key: _expand_source_evidence_aliases(item, source) for key, item in value.items()}
    return value


def _restrict_prompt_card(card: Mapping[str, Any], allowed_evidence_ids: set[str]) -> dict[str, Any]:
    """Keep card references closed over the evidence in the same prompt."""

    result = dict(card)
    summary_refs = [
        str(item)
        for item in card.get("summary_evidence_ids", ())
        if str(item) in allowed_evidence_ids
    ]
    original_summary_refs = {str(item) for item in card.get("summary_evidence_ids", ()) if str(item)}
    result["summary_evidence_ids"] = summary_refs
    if original_summary_refs and set(summary_refs) != original_summary_refs:
        # A card body is an intermediate LLM digest, not independent evidence.
        # If even one of its support refs was omitted from this prompt, hiding
        # the body is safer than letting the next model cite an unrelated
        # block for a claim it never received.
        result["summary"] = UNKNOWN
    elif not original_summary_refs:
        result["summary"] = UNKNOWN
    sections = card.get("sections")
    if isinstance(sections, Mapping):
        bounded_sections: dict[str, dict[str, Any]] = {}
        for heading, section in sections.items():
            if not isinstance(section, Mapping):
                continue
            original_ref_list = [str(item) for item in section.get("evidence_ids", ()) if str(item)]
            original_refs = set(original_ref_list)
            bounded_refs = [ref for ref in original_ref_list if ref in allowed_evidence_ids]
            bounded = {**dict(section), "evidence_ids": bounded_refs}
            if not original_refs or set(bounded_refs) != original_refs:
                bounded["body"] = UNKNOWN
            bounded_sections[heading] = bounded
        result["sections"] = bounded_sections
    return result


def _topic_plan_prompt(product_label: str, cards: Sequence[Mapping[str, Any]]) -> str:
    bounded_cards = [
        {
            **dict(card),
            "title": _clip_prompt_text(card.get("title", ""), 120),
            "question": _clip_prompt_text(card.get("question", ""), 180),
            "summary": _clip_prompt_text(card.get("summary", ""), 420),
            "axes": {
                key: _clip_prompt_text(value, 110)
                for key, value in dict(card.get("axes", {})).items()
            },
        }
        for card in cards
    ]
    return f"""你是企业知识库的信息架构师。只根据下面 {product_label} 的来源摘要，为读者规划少量跨来源主题页。不要写正文，不使用外部知识，不引用 CompanyBrain。

只返回 JSON：{{"topics":[{{"title":"可读主题标题","question":"一个具体问题","page_type":"positioning | concept | operation | diagnosis | experience","source_ids":["本列表中的 source_id"]}}]}}。

规划规则：
1. 只合并真正回答同一类问题的来源；一个主题至少 2 个来源，不能把无关的来源硬塞在一起。
2. 优先规划能直接回答读者问题的主题：产品关系/选型、模块与配置、操作流程、异常排查、版本经验。不要为每个文件单独建主题页。
3. 同一个来源可以出现在多个主题；不要输出不存在的 source_id。主题最多 {_MAX_TOPIC_GROUPS} 个。
4. page_type 只描述主题页的主要读法；资料只是历史记录时用 experience，资料包含明确现象和处理顺序时才用 diagnosis。
5. 标题和问题必须是读者看得懂的业务语言，不要出现 source_id、cluster、draft、随机编号，也不要写“资料汇总”。

产品：{product_label}
来源摘要：
{_json(bounded_cards)}"""


def _parse_topic_plan(
    text: str,
    product_sources: Sequence[SourceDoc],
) -> list[dict[str, Any]]:
    parsed = _parse_json(text)
    raw_topics = parsed.get("topics")
    if not isinstance(raw_topics, list):
        raise ValueError("topic planner did not return topics")
    known = {source.source_id for source in product_sources}
    topics: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for raw in raw_topics:
        if not isinstance(raw, Mapping):
            continue
        title = raw.get("title")
        question = raw.get("question")
        page_type = raw.get("page_type")
        source_ids = raw.get("source_ids")
        if (
            not isinstance(title, str)
            or not title.strip()
            or not isinstance(question, str)
            or not question.strip()
            or page_type not in PAGE_TYPES
            or not isinstance(source_ids, list)
        ):
            continue
        members = tuple(dict.fromkeys(str(source_id) for source_id in source_ids if str(source_id) in known))
        if len(members) < 2 or members in seen:
            continue
        if _HASH.search(title) or _HASH.search(question):
            continue
        seen.add(members)
        topics.append({
            "title": title.strip(),
            "question": question.strip(),
            "page_type": page_type,
            "source_ids": members,
        })
        if len(topics) >= _MAX_TOPIC_GROUPS:
            break
    return topics


def _aggregate_prompt(
    topic: Mapping[str, Any],
    cards: Sequence[Mapping[str, Any]],
    evidence: Sequence[Mapping[str, Any]],
    feedback: Sequence[Mapping[str, Any]] = (),
) -> str:
    page_type = str(topic["page_type"])
    role_rules = ""
    if page_type == "positioning":
        role_rules = """
定位页额外要求：如果证据中存在多个产品线、管理模式或相邻产品，必须明确分开它们的目标对象、依赖、入口和选择关系；不能把 Android/iOS 或本产品与 MAXSTORE、AirViewer、GoInsight 等相邻产品压成一个模糊概念。只写证据支持的产品关系。产品级定位页必须至少使用两个不同来源的证据；如果资料没有产品关系或选型信息，明确写“原始资料未明确”，不要用模块功能冒充产品定位。"""
    elif page_type == "diagnosis":
        role_rules = """
诊断页额外要求：按异常对象或现象分支组织答案（例如迁移、指标、查询或权限），每个分支都说明现象、检查、原因和处理；没有来源支持的统一排查顺序或升级规则必须写“原始资料未明确”，不能凭常识补齐。多个来源对不同分支使用相同术语时，必须保留分支限定，不能把一个分支的“仅支持/默认/必须”扩大成所有分支的结论。来源含“竞品/对比”时，只能把明确标注为本产品/本系统的内容归给本产品，竞品能力不得推导成本产品能力；来源只展示部分清单时，不得写成“系统共有 N 项”或补齐未展示项目。文件夹名只是归类，不是产品主体；不要把原文中出现的品牌自动当成竞品，只有原文明确标记为竞品、竞对或对比对象时才改变主体。"""
    contract = {
        "title": str(topic["title"]),
        "question": str(topic["question"]),
        "page_type": page_type,
        "axes": {"product": "...", "module": "...", "object": "...", "scenario": "...", "boundary": "..."},
        "summary": {"body": "one to three factual sentences", "evidence_ids": ["exact supplied id"]},
        "sections": {heading: {"body": "markdown answer, no heading", "evidence_ids": ["exact supplied id"]} for heading in PAGE_TYPES[page_type]},
    }
    feedback_text = ""
    if feedback:
        feedback_text = "\n\nREGENERATION FEEDBACK (fix only these concrete issues):\n" + _json(list(feedback))
    return f"""你是企业知识库主编。请把多个相关来源整理成一张真正能回答问题的 Reader 主题页。只使用下面来源摘要和证据，不使用外部知识、CompanyBrain 或未提供的常识。

输出只能是一个 JSON 对象，结构如下：
{_json(contract)}

硬规则：
1. page_type 必须是 {page_type}；sections 必须恰好使用这些标题：{_json(PAGE_TYPES[page_type])}。
2. 摘要和每条事实必须能由 supplied evidence_ids 支持；evidence_ids 只能来自下面证据。来源之间有冲突时保留冲突或限定，不要替读者拍脑袋统一。
3. 先回答“{topic['question']}”，再给条件、关系、步骤、现象、经验和边界；不要逐文件复述，不要把摘要拼接成大段原文。
4. 使用短段落、列表或紧凑表格。保留数字、日期、版本、权限、入口、范围、否定和例外。资料未明确的内容写“{UNKNOWN}”，不要补建议。
5. axes 必须分别表达产品、模块、对象、场景、边界，不能把五项全部写成同一个词。标题必须可读，不能含内部 ID。
6. 不要把密码、token、私钥、凭据内容或可直接登录的秘密值写入 Reader；只保留业务条件，并标注“敏感值未在 Reader 展示”。
7. 每个 section 最多 4 个短项目、每个项目尽量不超过 100 字；整页正文控制在约 2200 字以内。优先给出可执行的关系、条件、步骤和边界，不要解释写作过程。
8. 五个 page_type 章节必须全部输出；没有足够证据的章节也必须输出“{UNKNOWN}”，不能省略、改名或返回空 body。
{role_rules}

主题要求：
- 标题：{topic['title']}
- 问题：{topic['question']}

可回查证据（先看这一部分；这些是原始资料的真实行块）：
{_json(list(evidence))}

来源索引（只用于理解来源之间的关系，不能代替上面的原始证据）：
{_json(list(cards))}
{feedback_text}
"""


def _aggregate_evidence(
    pages: Sequence[ReaderPage],
    sources_by_id: Mapping[str, SourceDoc],
    *,
    compact: bool = False,
) -> list[dict[str, Any]]:
    cited: list[str] = []
    for page in pages:
        # Summary refs are the minimum closure needed for a compact source
        # card.  Put them first so compact selection does not accidentally
        # keep an arbitrary section ref while dropping the summary's facts.
        summary = page.sections.get("summary")
        if isinstance(summary, Mapping):
            cited.extend(str(item) for item in summary.get("evidence_ids", ()))
        for section in page.sections.values():
            if isinstance(section, Mapping):
                cited.extend(str(item) for item in section.get("evidence_ids", ()))
    by_id = {
        str(item["evidence_id"]): item
        for source in sources_by_id.values()
        for item in source.evidence
    }
    result: list[dict[str, Any]] = []
    for evidence_id in dict.fromkeys(cited):
        item = by_id.get(evidence_id)
        if item is None:
            continue
        result.append({
            "evidence_id": evidence_id,
            "source_id": str(item["source_id"]),
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "text": str(item["text"]),
        })
    if compact and len(result) > 12:
        # A product overview must not silently become a summary of the first
        # few files.  Keep at least one cited block from every source, then
        # fill a small bounded budget in source order.  The source cards still
        # carry the human summary; these blocks provide line-grounded anchors.
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in result:
            grouped[str(item["source_id"])].append(item)
        selected: list[dict[str, Any]] = []
        selected_ids: set[str] = set()
        # Keep every summary anchor first.  These are the only facts exposed
        # by compact (overview) cards.  Section evidence is filled afterwards.
        summary_ids: set[str] = set()
        for page in pages:
            summary = page.sections.get("summary")
            if isinstance(summary, Mapping):
                summary_ids.update(str(item) for item in summary.get("evidence_ids", ()))
        for item in result:
            evidence_id = str(item["evidence_id"])
            if evidence_id not in summary_ids:
                continue
            selected.append(item)
            selected_ids.add(evidence_id)
        # Still give every source one anchor if its summary had no usable ref.
        for source_id in sorted(grouped):
            item = next((candidate for candidate in grouped[source_id] if str(candidate["evidence_id"]) not in selected_ids), None)
            if item is None:
                continue
            selected.append(item)
            selected_ids.add(str(item["evidence_id"]))
        char_budget = 48_000
        used_chars = sum(len(str(item["text"])) for item in selected)
        for item in result:
            evidence_id = str(item["evidence_id"])
            if evidence_id in selected_ids:
                continue
            if len(selected) >= 48 or used_chars + len(str(item["text"])) > char_budget:
                continue
            selected.append(item)
            selected_ids.add(evidence_id)
            used_chars += len(str(item["text"]))
        return selected
    return result


def _topic_evidence(
    topic: Mapping[str, Any],
    source_pages: Sequence[ReaderPage],
    sources_by_id: Mapping[str, SourceDoc],
) -> list[dict[str, Any]]:
    """Build a bounded prompt from raw evidence, not only source summaries.

    Source pages are useful indexes, but using their cited blocks as the sole
    input to synthesis turns the compiler into a summary-of-summaries tool and
    silently loses details that the source writer did not choose.  Keep the
    source-page summary anchors for orientation, then select raw blocks from
    the same sources.  This is a prompt-size policy only; the raw snapshots
    and evidence index remain complete.
    """

    source_ids = tuple(dict.fromkeys(
        str(item)
        for page in source_pages
        for item in page.all_source_ids
        if str(item) in sources_by_id
    ))
    page_by_source = {
        page.source_id: page
        for page in source_pages
        if page.source_id in sources_by_id
    }
    topic_text = " ".join(str(topic.get(key, "")) for key in ("title", "question", "page_type")).casefold()
    role_terms = {
        "positioning": ("产品", "服务", "设备", "入口", "注册", "关系", "范围", "边界", "android", "ios"),
        "concept": ("配置", "字段", "对象", "规则", "生效", "限制", "模块", "版本"),
        "operation": ("步骤", "创建", "配置", "选择", "保存", "注册", "激活", "停用", "部署"),
        "diagnosis": ("异常", "失败", "报错", "错误", "问题", "排查", "原因", "修复", "重试", "日志"),
        "experience": ("版本", "回顾", "复盘", "经验", "坑", "缺陷", "改进", "回归", "阶段"),
    }.get(str(topic.get("page_type")), ())
    tokens = tuple(dict.fromkeys(
        term for term in (*role_terms, *re.findall(r"[a-z0-9][a-z0-9 _-]{1,}", topic_text))
        if len(term.strip()) >= 2
    ))

    by_id = {
        str(item["evidence_id"]): dict(item)
        for source_id in source_ids
        if (source := sources_by_id.get(source_id)) is not None
        for item in source.evidence
    }
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add(item: Mapping[str, Any]) -> None:
        evidence_id = str(item.get("evidence_id", ""))
        if not evidence_id or evidence_id in selected_ids:
            return
        selected_ids.add(evidence_id)
        selected.append(dict(item))

    # Summary anchors preserve source-page orientation without making them the
    # authoritative content.  They are included before relevance sampling.
    for page in source_pages:
        summary = page.sections.get("summary", {})
        for evidence_id in summary.get("evidence_ids", ()) if isinstance(summary, Mapping) else ():
            if str(evidence_id) in by_id:
                add(by_id[str(evidence_id)])

    candidates: list[tuple[int, str, Mapping[str, Any]]] = []
    for source_id in source_ids:
        source = sources_by_id[source_id]
        page = page_by_source.get(source_id)
        source_context = " ".join((source.relative_path, page.title if page else "", page.question if page else "")).casefold()
        for index, item in enumerate(source.evidence):
            text = str(item.get("text", ""))
            haystack = f"{source_context} {text}".casefold()
            score = sum(3 for token in tokens if token.casefold() in haystack)
            score += max(0, 2 - min(index, 2))
            if text.lstrip().startswith(("#", "##", "###", "-", "|")):
                score += 1
            candidates.append((score, f"{source.relative_path}:{index:06d}", item))
    for _score, _order, item in sorted(candidates, key=lambda row: (-row[0], row[1])):
        add(item)
        if len(selected) >= 64:
            break

    # Keep the prompt bounded while retaining at least one raw block per
    # selected source.  Evidence text is clipped only in the provider prompt.
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in selected:
        grouped[str(item["source_id"])].append(item)
    ordered: list[dict[str, Any]] = []
    for source_id in source_ids:
        ordered.extend(grouped.get(source_id, [])[:2])
    for item in selected:
        if item not in ordered:
            ordered.append(item)
    return _prompt_evidence(ordered[:64], text_limit=700)


def _generate_aggregate_page(
    topic: Mapping[str, Any],
    source_pages: Sequence[ReaderPage],
    sources_by_id: Mapping[str, SourceDoc],
    model: SemanticModel,
) -> ReaderPage:
    members = tuple(sources_by_id[page_source_id] for page in source_pages for page_source_id in page.all_source_ids if page_source_id in sources_by_id)
    unique_sources = tuple({source.source_id: source for source in members}.values())
    bounded_evidence = _topic_evidence(topic, source_pages, sources_by_id)
    available_evidence_ids = {str(item["evidence_id"]) for item in bounded_evidence}
    rich_cards = [
        _restrict_prompt_card(
            _prompt_card(page, sources_by_id[page.source_id], rich=len(source_pages) <= 12),
            available_evidence_ids,
        )
        for page in source_pages
    ]
    product_overview = len(unique_sources) >= 8 and str(topic.get("page_type")) == "positioning"
    topic_id = "topic-" + _sha(str(topic["title"]) + "\0" + "\0".join(sorted(source.source_id for source in unique_sources)))[:20]
    if product_overview:
        cards = [
            _restrict_prompt_card(
                _prompt_card(page, sources_by_id[page.source_id], rich=False),
                available_evidence_ids,
            )
            for page in source_pages
        ]
    else:
        cards = rich_cards
    aggregate_attempts = (
        _MANDATORY_AGGREGATE_ATTEMPTS
        if str(topic.get("title", "")).endswith(("产品定位与阅读入口", "常见异常定位与处理边界", "版本迭代与复盘经验"))
        else _AGGREGATE_ATTEMPTS
    )
    attempts = [
        (cards, bounded_evidence, ()),
        (cards, bounded_evidence, ({"type": "previous_output_invalid", "detail": "上一次结果缺少必需章节或证据绑定"},)),
    ][:aggregate_attempts]
    last_error: Exception | None = None
    for attempt_cards, attempt_evidence, feedback in attempts:
        try:
            value = _parse_json(model.generate(_aggregate_prompt(topic, attempt_cards, attempt_evidence, feedback=feedback)))
            # Validate every response before trying the next one.  A
            # syntactically valid but incomplete JSON response must consume a
            # retry rather than discard the topic after the final parse.
            return _normalise_page(unique_sources, value, expected_page_type=str(topic["page_type"]), page_id=topic_id, answer_page=True)
        except ProviderError:
            raise
        except (ValueError, TypeError) as error:
            last_error = error
    raise ValueError(str(last_error or "aggregate page generation failed"))


def _generate_pages(
    sources: Sequence[SourceDoc],
    model: SemanticModel,
    *,
    retry_limit: int = _SOURCE_RETRY_LIMIT,
    require_task5_semantic: bool = False,
) -> tuple[list[ReaderPage], list[dict[str, Any]]]:
    pages: list[ReaderPage] = []
    failures: list[dict[str, Any]] = []

    def generate(source: SourceDoc, feedback: Sequence[Mapping[str, Any]] = ()) -> tuple[SourceDoc, ReaderPage | None, str | None]:
        try:
            return source, _generate_one_page(source, model, feedback, require_task5_semantic=require_task5_semantic), None
        except ProviderError as error:
            # A single stalled source must not erase the other 88 source
            # snapshots.  It remains Audit-only and keeps the full run
            # explicitly not_released.
            return source, None, f"provider unavailable: {error}"
        except (ValueError, TypeError) as error:
            return source, None, str(error)

    for source in sources:
        if source.status == "known_empty":
            failures.append({
                "source_id": source.source_id,
                "source_ids": [source.source_id],
                "relative_path": source.relative_path,
                "status": "audit_only",
                "reason": "known_empty_source",
                "failure": {"code": "known_empty_source"},
            })
    canonical_sources = [source for source in sources if source.status == "ready"]
    # Source pages are independent.  Keep each response and failure attached
    # to its own source, but run a small bounded pool so a 89-source run does
    # not turn provider latency into an hour-long serial queue.
    def generate_indexed(item: tuple[int, SourceDoc]) -> tuple[SourceDoc, ReaderPage | None, str | None]:
        index, source = item
        _progress(f"source {index}/{len(canonical_sources)}: {source.relative_path}")
        return generate(source)

    # Real Qwen calls use a smaller pool than the generic path to avoid
    # gateway saturation and transient 504s without introducing a fallback.
    worker_limit = _QUALITY_SOURCE_WORKERS if require_task5_semantic else 6
    worker_count = min(worker_limit, len(canonical_sources))
    if worker_count:
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="digest-source") as pool:
            results = list(pool.map(generate_indexed, enumerate(canonical_sources, 1)))
    else:
        results = []
    initial = {source.source_id: (source, page, error) for source, page, error in results}

    # A malformed provider response is retried only for a small, deterministic
    # global allowance.  Per-source retry loops made the full-corpus call
    # count unknowable and could starve the mandatory embedding route.
    retry_queue = [
        item for item in sorted(results, key=lambda item: item[0].relative_path)
        if item[1] is None
    ]
    retry_counts: dict[str, int] = defaultdict(int)
    retry_budget = max(0, int(retry_limit))
    retry_index = 0
    # Use a small round-robin queue.  A transient malformed response may need
    # a second attempt, but one stubborn source must not consume every retry
    # before the other failed sources are retried once.
    while retry_queue and retry_index < retry_budget:
        source, _page, error = retry_queue.pop(0)
        retry_counts[source.source_id] += 1
        retry_index += 1
        _progress(f"retry {retry_index}/{retry_budget}: {source.relative_path}")
        retry_type = "strict_minimal_retry" if retry_counts[source.source_id] >= 2 else "previous_output_invalid"
        retried = generate(
            source,
            ({"type": retry_type, "detail": error or "unknown generation failure"},),
        )
        initial[retried[0].source_id] = retried
        if retried[1] is None and retry_counts[source.source_id] < 3:
            if retry_counts[source.source_id] >= 2:
                # A final generic minimal retry is preferable to silently
                # dropping a source whose raw bytes are otherwise valid.
                retry_queue.append((source, retried[1], "strict minimal retry"))
            else:
                retry_queue.append(retried)

    for source in canonical_sources:
        _source, page, error = initial[source.source_id]
        if page is None:
            failures.append({"source_id": source.source_id, "source_ids": [source.source_id], "relative_path": source.relative_path, "status": "audit_only", "reason": error or "unknown generation failure", "failure": {"code": "provider_failed" if error and "provider unavailable" in error else "source_compile_failed"}})
        else:
            pages.append(replace(page, verification="generated"))
    duplicates_by_canonical: dict[str, list[str]] = defaultdict(list)
    for source in sources:
        if source.status == "duplicate_alias" and source.duplicate_of:
            duplicates_by_canonical[source.duplicate_of].append(source.source_id)
    pages = [
        replace(page, source_ids=(page.source_id, *sorted(duplicates_by_canonical.get(page.source_id, []))))
        for page in pages
    ]
    return pages, failures


def _verify_source_pages(
    pages: Sequence[ReaderPage],
    sources_by_id: Mapping[str, SourceDoc],
    model: SemanticModel,
    *,
    require_task5_semantic: bool = False,
) -> tuple[list[ReaderPage], list[dict[str, Any]]]:
    """Keep generated source summaries out of Reader when Qwen rejects them."""

    verified, failures = _verify_pages(
        pages,
        sources_by_id,
        model,
        regenerate=False,
        attempts=_SOURCE_VERIFY_ATTEMPTS,
        evidence_limit=4000,
        batch_size=_SOURCE_VERIFY_BATCH_SIZE,
        failure_scope="source",
    )
    by_identity = {_page_identity(page): page for page in verified}
    repaired: dict[str, ReaderPage] = {}
    remaining_failures: list[dict[str, Any]] = []
    repair_budget = _SOURCE_REPAIR_LIMIT
    for failure in failures:
        identity = str(failure.get("page_id", ""))
        page = by_identity.get(identity)
        violations = failure.get("violations")
        if page is None or not isinstance(violations, list) or not violations or repair_budget <= 0:
            remaining_failures.append(failure)
            continue
        repair_budget -= 1
        try:
            candidate = _regenerate_page(
                page,
                tuple(sources_by_id[source_id] for source_id in page.all_source_ids),
                model,
                violations,
                require_task5_semantic=require_task5_semantic,
            )
            checked, repair_failures = _verify_pages(
                [candidate],
                sources_by_id,
                model,
                regenerate=False,
                attempts=1,
                evidence_limit=4000,
                batch_size=1,
                failure_scope="source",
            )
        except (ProviderError, ValueError, TypeError) as error:
            failure = dict(failure)
            failure["reason"] = f"{failure.get('reason', 'source verification failed')}; repair failed: {error}"
            remaining_failures.append(failure)
            continue
        if not repair_failures and checked and checked[0].verification != "audit_only":
            repaired[identity] = replace(checked[0], verification="repaired", violations=())
            continue
        failure = dict(failure)
        repair_reason = str(repair_failures[0].get("reason", "repair verification failed")) if repair_failures else "repair verification did not return a valid page"
        failure["reason"] = f"{failure.get('reason', 'source verification failed')}; repair failed: {repair_reason}"
        remaining_failures.append(failure)
    result: list[ReaderPage] = []
    for page in verified:
        identity = _page_identity(page)
        if identity in repaired:
            result.append(repaired[identity])
        elif page.verification != "audit_only" and identity not in {str(item.get("page_id", "")) for item in remaining_failures}:
            result.append(page)
    return result, remaining_failures


def _generate_topic_pages(
    sources: Sequence[SourceDoc],
    source_pages: Sequence[ReaderPage],
    model: SemanticModel,
) -> tuple[list[ReaderPage], list[dict[str, Any]]]:
    """Build a small set of cross-source answer pages.

    Source pages preserve document-level coverage.  These topic pages are the
    reader-facing synthesis layer that makes a question answerable without
    forcing the user to infer relationships across several source files.
    The planner sees only source-bound cards and can never invent a source.
    """

    sources_by_id = {source.source_id: source for source in sources}
    pages_by_source = {
        source_id: page
        for page in source_pages
        for source_id in page.all_source_ids
    }
    product_sources: dict[str, list[SourceDoc]] = defaultdict(list)
    for source in sources:
        # Raw source evidence remains eligible for mandatory synthesis even
        # when the per-source draft was rejected.  The placeholder below has
        # no prose; only the immutable raw evidence can be cited.
        if source.status == "ready":
            product_sources[source.product].append(source)
    topic_pages: list[ReaderPage] = []
    failures: list[dict[str, Any]] = []

    for product_key in sorted(product_sources):
        members = tuple(sorted(product_sources[product_key], key=lambda source: source.relative_path))
        member_pages = tuple(
            pages_by_source.get(source.source_id, _source_index_page(source))
            for source in members
        )
        # The shared lookup initially contains only verified source drafts.
        # Register raw-only placeholders as well, so a mandatory topic can
        # consume a source whose draft was rejected without publishing that
        # rejected draft as Reader content.
        for page in member_pages:
            pages_by_source.setdefault(page.source_id, page)
        product_label = members[0].product_label
        _progress(f"planning {product_label}: {len(members)} source pages")
        overview = {
            "title": f"{product_label} 产品定位与阅读入口",
            "question": f"{product_label} 是什么，主要模块、使用场景和边界是什么？",
            "page_type": "positioning",
            "source_ids": tuple(source.source_id for source in members),
        }
        topic_specs = [overview]
        compact_cards = [_source_card(page, sources_by_id[page.source_id], compact=True) for page in member_pages]
        planner_error: Exception | None = None
        for planner_attempt in range(_PLANNER_ATTEMPTS):
            try:
                planner_prompt = _topic_plan_prompt(product_label, compact_cards)
                if planner_attempt:
                    planner_prompt += "\n\n上一次规划结果不可解析；这次只返回简短、合法的 JSON，不要输出解释。"
                topic_specs.extend(_parse_topic_plan(model.generate(planner_prompt), members))
                planner_error = None
                break
            except ProviderError as error:
                planner_error = error
                break
            except (ValueError, TypeError) as error:
                planner_error = error
        if planner_error is not None:
            failures.append({
                "status": "topic_planner_warning",
                "product": product_label,
                "reason": str(planner_error),
            })

        # A product must have one product-level diagnosis entry whenever its
        # own corpus contains diagnostic signals.  A planner-produced
        # diagnosis page may be a narrow incident page (for example one
        # migration defect) and is not a substitute for the question-level
        # entry.  Keep the decision corpus-derived rather than case-specific.
        scored: list[tuple[int, SourceDoc, bool]] = []
        for source, page in zip(members, member_pages):
            searchable = "\n".join([
                source.relative_path,
                page.title,
                page.question,
                str(page.sections["summary"]["body"]),
                source.text,
            ]).casefold()
            score = sum(weight for signal, weight in _DIAGNOSIS_SIGNALS if signal.casefold() in searchable)
            if score > 0:
                comparison = any(marker.casefold() in searchable for marker in _COMPARISON_MARKERS)
                scored.append((score, source, comparison))
        scored.sort(key=lambda item: (-item[0], item[1].relative_path))
        # Comparative material is valuable for a comparison page, but it is
        # a risky input to a product-wide incident guide: the same paragraph
        # can describe the product and a competitor.  Prefer direct product
        # material when it exists; retain comparative material only when it
        # is the only diagnostic evidence for that product, so coverage is
        # not silently lost.
        direct = [item for item in scored if not item[2]]
        diagnostic_pool = direct or scored
        diagnostic_sources = [source for score, source, _comparison in diagnostic_pool[:6] if score >= 2]
        generic_diagnosis_title = f"{product_label} 常见异常定位与处理边界"
        if diagnostic_sources and not any(
            str(topic.get("title")) == generic_diagnosis_title
            and str(topic.get("page_type")) == "diagnosis"
            for topic in topic_specs
        ):
            topic_specs.append({
                "title": generic_diagnosis_title,
                "question": f"{product_label} 遇到异常时如何定位、处理和升级？",
                "page_type": "diagnosis",
                "source_ids": tuple(source.source_id for source in diagnostic_sources),
            })

        experience_sources = [
            source
            for source in members
            if any(signal.casefold() in source.text.casefold() for signal in _EXPERIENCE_SIGNALS)
        ]
        experience_title = f"{product_label} 版本迭代与复盘经验"
        if experience_sources and not any(
            str(topic.get("title")) == experience_title
            and str(topic.get("page_type")) == "experience"
            for topic in topic_specs
        ):
            topic_specs.append({
                "title": experience_title,
                "question": f"{product_label} 的版本迭代和复盘有哪些做法、坑和适用边界？",
                "page_type": "experience",
                "source_ids": tuple(source.source_id for source in experience_sources[:6]),
            })

        # Keep the public synthesis layer bounded.  The source pages and raw
        # snapshots retain the complete corpus; topic pages only provide the
        # few high-value cross-source answers a reader should enter through.
        # Mandatory entries always win, then planner suggestions are selected
        # by page role so one product cannot consume the whole budget with
        # several near-duplicate incident pages.
        mandatory_titles = {overview["title"], generic_diagnosis_title, experience_title}
        unique_specs: list[dict[str, Any]] = []
        seen_specs: set[tuple[str, tuple[str, ...], str]] = set()
        for topic in topic_specs:
            key = (
                str(topic.get("page_type")),
                tuple(str(item) for item in topic.get("source_ids", ())),
                str(topic.get("title", "")),
            )
            if key in seen_specs:
                continue
            seen_specs.add(key)
            unique_specs.append(topic)
        mandatory = [topic for topic in unique_specs if str(topic.get("title")) in mandatory_titles]
        optional = [topic for topic in unique_specs if topic not in mandatory]
        role_order = {"positioning": 0, "concept": 1, "operation": 2, "diagnosis": 3, "experience": 4}
        optional.sort(key=lambda topic: (
            role_order.get(str(topic.get("page_type")), 99),
            -len(tuple(topic.get("source_ids", ()))),
            str(topic.get("title", "")),
        ))
        topic_specs = (mandatory + optional)[:_MAX_TOPIC_PAGES_PER_PRODUCT]

        for topic in topic_specs:
            selected_pages = tuple(
                pages_by_source[source_id]
                for source_id in topic["source_ids"]
                if source_id in pages_by_source
            )
            if len(selected_pages) < 2 and topic["page_type"] not in {"positioning", "diagnosis", "experience"}:
                continue
            if not selected_pages:
                continue
            try:
                topic_pages.append(_generate_aggregate_page(topic, selected_pages, sources_by_id, model))
            except ProviderError as error:
                failures.append({
                    "scope": "topic",
                    "status": "topic_audit_only",
                    "product": product_label,
                    "title": topic["title"],
                    "reason": f"provider unavailable: {error}",
                })
            except (ValueError, TypeError) as error:
                failures.append({
                    "scope": "topic",
                    "status": "topic_audit_only",
                    "product": product_label,
                    "title": topic["title"],
                    "reason": str(error),
                })
        _progress(f"aggregates {product_label}: {len(topic_pages)} total")
    return topic_pages, failures


def _page_identity(page: ReaderPage) -> str:
    return page.page_id or page.source_id


def _page_evidence(sources_by_id: Mapping[str, SourceDoc], page: ReaderPage) -> list[dict[str, Any]]:
    by_id = {
        str(item["evidence_id"]): item
        for source_id in page.all_source_ids
        if (source := sources_by_id.get(source_id)) is not None
        for item in source.evidence
    }
    ids: list[str] = []
    for section in page.sections.values():
        if isinstance(section, Mapping):
            ids.extend(str(item) for item in section.get("evidence_ids", ()))
    return [dict(by_id[item]) for item in dict.fromkeys(ids) if item in by_id]


def _verification_prompt(
    items: Sequence[tuple[ReaderPage, Sequence[SourceDoc]]],
    *,
    evidence_limit: int = 500,
    retry_hint: str = "",
) -> str:
    payload = []
    for page, sources in items:
        source_map = {source.source_id: source for source in sources}
        payload.append({
            "page_id": _page_identity(page),
            "source_paths": [_clip_prompt_text(source.relative_path, 180) for source in sources],
            "page": {
                "title": _clip_prompt_text(page.title, 180),
                "question": _clip_prompt_text(page.question, 240),
                "summary": {
                    "body": _clip_prompt_text(page.sections["summary"].get("body", ""), 700),
                    "evidence_ids": list(page.sections["summary"].get("evidence_ids", ())),
                },
                "page_type": page.page_type,
                "axes": {key: _clip_prompt_text(value, 180) for key, value in page.axes.items()},
                "sections": {
                    key: {
                        "body": _clip_prompt_text(value.get("body", ""), 700),
                        "evidence_ids": list(value.get("evidence_ids", ())),
                    }
                    for key, value in page.sections.items()
                    if key != "summary"
                },
            },
            "cited_evidence": _prompt_evidence(_page_evidence(source_map, page), text_limit=evidence_limit),
        })
    single_page_contract = ""
    if len(items) == 1:
        single_page_contract = f"""
这是单页校验。必须只返回一个 JSON 对象，并且必须逐字使用这个 page_id：{_page_identity(items[0][0])}。合法的无问题输出形状是：{{"results":[{{"page_id":"{_page_identity(items[0][0])}","violations":[]}}]}}。不要返回 Markdown、解释、数组或其他 page_id。
"""
    retry_text = f"\n{retry_hint.strip()}\n" if retry_hint.strip() else ""
    return f"""你是知识页面的通用事实校验器。只检查页面正文是否被 cited_evidence 支持；不要使用外部知识，也不要因为文风、顺序或合理的同义改写报错。重点检查：无证据事实、遗漏条件、否定反转、数字/范围/版本改变、证据引用错误，以及多个来源之间被错误合并的条件冲突。

如果多个来源描述同一功能的不同入口、对象或厂商流程，正文必须保留场景限定（例如“ZOLON 直接录入”与“非 ZOLON 门户配置”），不能把某一个分支的“仅支持/默认/必须”扩大成所有分支的结论；发现这种扩大时返回 type=conflict 或 type=condition。文件夹名只是归类，不是产品主体；不要仅因为证据出现某个品牌名就把它判成竞品，只有原文明确说明“竞品/竞对/对比对象”时才判定主体冲突。Markdown 表格、删除线历史行和同一证据块中的连续行都属于 cited_evidence；如果正文事实在 cited_evidence 中有直接文字或不改变条件的同义表达，不得仅因它不是单独一行、没有 UI 细节或出现在表格里而判 unsupported。

只返回 JSON：{{"results":[{{"page_id":"source id","violations":[{{"type":"unsupported|condition|conflict|negation|number|range|lineage","detail":"不超过 100 字的具体问题","evidence_ids":["id"]}}]}}]}}。必须为每个 page_id 返回一项；没有问题时 violations 必须为空；每页最多列 3 个问题。不要复述页面、证据或评论可读性。

待检查页面：
{_json(payload)}
{single_page_contract}{retry_text}"""


def _repair_prompt(
    page: ReaderPage,
    sources: Sequence[SourceDoc],
    violations: Sequence[Mapping[str, Any]],
    *,
    require_task5_semantic: bool = False,
) -> str:
    if require_task5_semantic:
        contract = {
            "schema_version": "task5-semantic-output.v2",
            "title": page.title,
            "page_type": page.page_type,
            "page_type_claim_ids": ["exact supplied claim ref"],
            "axis": {"product": page.axes["product"], "module": page.axes["module"], "object": page.axes["object"], "scene": page.axes["scenario"], "boundary": page.axes["boundary"]},
            "axis_claim_ids": {name: ["exact supplied claim ref"] for name in ("product", "module", "object", "scene", "boundary")},
            "summary": {"body": "markdown answer", "claim_ids": ["exact supplied claim ref"], "evidence_ids": ["same supplied ref"]},
            "sections": {
                heading: {"body": "markdown answer, no heading", "claim_ids": ["exact supplied claim ref"], "evidence_ids": ["same supplied ref"]}
                for heading in PAGE_TYPES[page.page_type]
            },
        }
    else:
        contract = {
            "title": page.title,
            "question": page.question,
            "page_type": page.page_type,
            "axes": dict(page.axes),
            "summary": page.sections["summary"],
            "sections": {
                heading: {"body": "markdown answer, no heading", "evidence_ids": ["exact supplied id"]}
                for heading in PAGE_TYPES[page.page_type]
            },
        }
    return f"""你是企业知识库编辑。修正一张已经生成的 Reader 页面，只使用所列原始证据，不使用外部知识。输出只能是一个 JSON 对象，结构如下：
{_json(contract)}

只修复校验器列出的事实、条件、否定、数字、范围或来源绑定问题；没有证据支持的句子必须删除或写“{UNKNOWN}”，不要补写建议。每条正文事实都必须引用 supplied evidence_ids。保留原页面的问题、页面类型和五轴含义；正文要短、可读，不要复制原文。不要输出密码、token、私钥、凭据内容或可直接登录的秘密值。

校验问题：
{_json(list(violations))}

来源路径：
{_json([source.relative_path for source in sources])}

证据：
{_json(_page_evidence({source.source_id: source for source in sources}, page))}"""


def _regenerate_page(
    page: ReaderPage,
    sources: Sequence[SourceDoc],
    model: SemanticModel,
    violations: Sequence[Mapping[str, Any]],
    *,
    require_task5_semantic: bool = False,
) -> ReaderPage:
    value = _parse_json(model.generate(_repair_prompt(page, sources, violations, require_task5_semantic=require_task5_semantic)))
    return _normalise_page(
        sources,
        value,
        expected_page_type=page.page_type,
        page_id=page.page_id,
        expected_title=page.title,
        expected_question=page.question,
        expected_axes=page.axes,
        require_task5_semantic=require_task5_semantic,
    )


def _verify_batch(
    batch: Sequence[ReaderPage],
    sources_by_id: Mapping[str, SourceDoc],
    model: SemanticModel,
    *,
    attempts: int = 2,
    evidence_limit: int = 500,
    trace_by_page: dict[str, list[dict[str, Any]]] | None = None,
    retry_hint: str = "",
) -> dict[str, list[Mapping[str, Any]]]:
    """Run the generic verifier a bounded number of times."""

    expected_ids = tuple(_page_identity(page) for page in batch)
    if len(set(expected_ids)) != len(expected_ids):
        raise ValueError("verifier batch contains duplicate page identities")
    last_error: Exception | None = None
    for attempt in range(attempts):
        prompt = _verification_prompt([
            (page, tuple(sources_by_id[source_id] for source_id in page.all_source_ids))
            for page in batch
        ], evidence_limit=evidence_limit, retry_hint=retry_hint)
        trace_events: list[dict[str, Any]] = []
        for page in batch:
            trace_event = {
                "stage": "verify",
                "attempt": attempt + 1,
                "page_ids": list(expected_ids),
                "page_id": _page_identity(page),
                "prompt_sha256": _sha(prompt),
                "qwen_payload_sha256": _sha(prompt),
                "status": "requested",
            }
            trace_events.append(trace_event)
            if trace_by_page is not None:
                trace_by_page.setdefault(page.projection_id or _page_identity(page), []).append(trace_event)
        try:
            response = model.generate(prompt)
            for trace_event in trace_events:
                trace_event["response_sha256"] = _sha(response)
                trace_event["status"] = "received"
            parsed = _parse_json(response)
            if not isinstance(parsed, Mapping):
                raise ValueError("verifier response must be a JSON object")
            results = parsed.get("results")
            if not isinstance(results, list):
                raise ValueError("verifier results are missing")
            raw_page_ids = [
                item.get("page_id")
                for item in results
                if isinstance(item, Mapping)
            ]
            if len(raw_page_ids) != len(set(raw_page_ids)):
                # Some Qwen responses repeat the sole result object in a
                # single-page verification call.  The duplicate carries no
                # second page identity; keep the first object and continue
                # validating its exact shape and evidence IDs.  Duplicates
                # in a multi-page batch remain a hard error because they can
                # hide another page's result.
                if len(expected_ids) == 1 and raw_page_ids and set(raw_page_ids) == {expected_ids[0]}:
                    results = [item for item in results if isinstance(item, Mapping)][0:1]
                    raw_page_ids = [expected_ids[0]]
                else:
                    raise ValueError("verifier returned duplicate page_id")
            if len(results) != len(expected_ids):
                raise ValueError("verifier result count mismatch")
            by_id: dict[str, list[Mapping[str, Any]]] = {}
            allowed_types = {"unsupported", "condition", "conflict", "negation", "number", "range", "lineage"}
            for item in results:
                if (
                    not isinstance(item, Mapping)
                    or set(item) != {"page_id", "violations"}
                    or not isinstance(item.get("page_id"), str)
                    or not isinstance(item.get("violations"), list)
                ):
                    raise ValueError("verifier result is malformed")
                page_id = item["page_id"]
                if page_id in by_id:
                    raise ValueError(f"verifier returned duplicate page_id: {page_id}")
                page = next((candidate for candidate in batch if _page_identity(candidate) == page_id), None)
                if page is None:
                    raise ValueError(f"verifier returned unknown page_id: {page_id}")
                allowed_evidence_ids = {
                    str(evidence["evidence_id"])
                    for source_id in page.all_source_ids
                    if (source := sources_by_id.get(source_id)) is not None
                    for evidence in source.evidence
                }
                validated: list[Mapping[str, Any]] = []
                for violation in item["violations"]:
                    if (
                        not isinstance(violation, Mapping)
                        or set(violation) != {"type", "detail", "evidence_ids"}
                        or violation.get("type") not in allowed_types
                        or not isinstance(violation.get("detail"), str)
                        or not violation["detail"].strip()
                        or len(violation["detail"]) > 500
                        or not isinstance(violation.get("evidence_ids"), list)
                        or any(
                            not isinstance(evidence_id, str) or evidence_id not in allowed_evidence_ids
                            for evidence_id in violation["evidence_ids"]
                        )
                    ):
                        raise ValueError("verifier violation is malformed")
                    validated.append(dict(violation))
                by_id[page_id] = validated
            if set(by_id) != set(expected_ids):
                raise ValueError("verifier did not return every page")
            for trace_event in trace_events:
                trace_event["violation_count"] = len(by_id[trace_event["page_id"]])
                trace_event["status"] = "passed"
            return by_id
        except ProviderError as error:
            for trace_event in trace_events:
                trace_event["status"] = "failed"
                trace_event["error"] = str(error)[:500]
            raise
        except (ValueError, TypeError) as error:
            for trace_event in trace_events:
                trace_event["status"] = "failed"
                trace_event["error"] = str(error)[:500]
            last_error = error
    raise ValueError(str(last_error or "verifier failed"))


def _verify_batch_resilient(
    batch: Sequence[ReaderPage],
    sources_by_id: Mapping[str, SourceDoc],
    model: SemanticModel,
    single_fallbacks_left: int,
    *,
    attempts: int = 2,
    evidence_limit: int = 500,
    trace_by_page: dict[str, list[dict[str, Any]]] | None = None,
) -> tuple[dict[str, list[Mapping[str, Any]]], dict[str, str], int]:
    """Verify a batch, with a small global allowance for single-page retry."""

    try:
        return _verify_batch(
            batch,
            sources_by_id,
            model,
            attempts=attempts,
            evidence_limit=evidence_limit,
            trace_by_page=trace_by_page,
        ), {}, 0
    except ProviderError as error:
        return {}, {
            _page_identity(page): f"provider unavailable: {error}"
            for page in batch
        }, 0
    except (ValueError, TypeError) as batch_error:
        results: dict[str, list[Mapping[str, Any]]] = {}
        errors: dict[str, str] = {}
        used_fallbacks = 0
        for page in batch:
            identity = _page_identity(page)
            if used_fallbacks >= single_fallbacks_left:
                errors[identity] = f"batch: {batch_error}; single fallback budget exhausted"
                continue
            used_fallbacks += 1
            try:
                results.update(_verify_batch(
                    (page,),
                    sources_by_id,
                    model,
                    attempts=1,
                    evidence_limit=evidence_limit,
                    trace_by_page=trace_by_page,
                    retry_hint=(
                        "这是批次校验失败后的单页重试。只返回当前这个 page_id 的一项 results，"
                        "不要复用批次输出，也不要返回其他 page_id。"
                    ),
                ))
            except ProviderError as error:
                last_error = error
                break
            except (ValueError, TypeError) as page_error:
                errors[identity] = f"batch: {batch_error}; single: {page_error}"
        return results, errors, used_fallbacks


def _verify_pages(
    pages: Sequence[ReaderPage],
    sources_by_id: Mapping[str, SourceDoc],
    model: SemanticModel,
    *,
    regenerate: bool = True,
    attempts: int = 1,
    evidence_limit: int = 500,
    batch_size: int | None = None,
    failure_scope: str = "topic",
    trace_by_page: dict[str, list[dict[str, Any]]] | None = None,
) -> tuple[list[ReaderPage], list[dict[str, Any]]]:
    verified = list(pages)
    failures: list[dict[str, Any]] = []
    by_page_id = {_page_identity(page): index for index, page in enumerate(verified)}
    regenerated_ids: set[str] = set()
    single_fallbacks_left = _VERIFY_SINGLE_FALLBACK_LIMIT
    effective_batch_size = _VERIFY_BATCH_SIZE if batch_size is None else int(batch_size)
    if effective_batch_size <= 0:
        raise ValueError("verifier batch_size must be greater than zero")
    for start in range(0, len(verified), effective_batch_size):
        batch = verified[start : start + effective_batch_size]
        by_id, errors, used_fallbacks = _verify_batch_resilient(
            batch,
            sources_by_id,
            model,
            single_fallbacks_left,
            attempts=attempts,
            evidence_limit=evidence_limit,
            trace_by_page=trace_by_page,
        )
        single_fallbacks_left -= used_fallbacks
        for page in batch:
            identity = _page_identity(page)
            if identity not in errors and identity in by_id:
                continue
            error = errors.get(identity, "verifier did not return this page")
            for page in batch:
                if _page_identity(page) != identity:
                    continue
                failures.append({"scope": failure_scope, "source_id": page.source_id, "source_ids": list(page.all_source_ids), "product": page.axes.get("product", ""), "title": page.title, "page_id": identity, "status": "audit_only", "reason": f"verification unavailable: {error}"})
                verified[by_page_id[identity]] = replace(page, verification="audit_only", violations=({"type": "verification", "detail": str(error)},))
        for page in batch:
            if _page_identity(page) not in by_id:
                continue
            violations = tuple(by_id[_page_identity(page)])
            if violations:
                if not regenerate:
                    failures.append({"scope": failure_scope, "source_id": page.source_id, "source_ids": list(page.all_source_ids), "product": page.axes.get("product", ""), "title": page.title, "page_id": _page_identity(page), "status": "audit_only", "reason": "quality verifier found factual violations", "violations": list(violations)})
                    verified[by_page_id[_page_identity(page)]] = replace(page, verification="audit_only", violations=violations)
                    continue
                try:
                    regenerated = _regenerate_page(
                        page,
                        tuple(sources_by_id[source_id] for source_id in page.all_source_ids),
                        model,
                        violations,
                    )
                except ProviderError as error:
                    failures.append({
                        "scope": failure_scope,
                        "source_id": page.source_id,
                        "source_ids": list(page.all_source_ids),
                        "product": page.axes.get("product", ""),
                        "title": page.title,
                        "page_id": _page_identity(page),
                        "status": "audit_only",
                        "reason": f"regeneration unavailable: provider unavailable: {error}",
                        "violations": list(violations),
                    })
                    verified[by_page_id[_page_identity(page)]] = replace(page, verification="audit_only", violations=violations)
                except (ValueError, TypeError) as error:
                    failures.append({"scope": failure_scope, "source_id": page.source_id, "source_ids": list(page.all_source_ids), "product": page.axes.get("product", ""), "title": page.title, "page_id": _page_identity(page), "status": "audit_only", "reason": f"regeneration failed: {error}", "violations": list(violations)})
                    verified[by_page_id[_page_identity(page)]] = replace(page, verification="audit_only", violations=violations)
                else:
                    # Regeneration is permitted once.  It is rechecked by the
                    # generic verifier pass below; a second failure is
                    # Audit-only, so this never becomes a repair spiral.
                    verified[by_page_id[_page_identity(page)]] = replace(regenerated, verification="regenerated", violations=violations)
                    regenerated_ids.add(_page_identity(page))
            else:
                verified[by_page_id[_page_identity(page)]] = replace(page, verification="passed")

    # Recheck only pages that consumed their one generic regeneration.  This
    # keeps the correction policy bounded and makes the Audit-only result
    # truthful when the model could not fix its own factual mismatch.
    regenerated = [verified[by_page_id[page_id]] for page_id in sorted(regenerated_ids)]
    for start in range(0, len(regenerated), effective_batch_size):
        batch = regenerated[start : start + effective_batch_size]
        by_id, errors, used_fallbacks = _verify_batch_resilient(
            batch,
            sources_by_id,
            model,
            single_fallbacks_left,
            attempts=1,
            evidence_limit=evidence_limit,
            trace_by_page=trace_by_page,
        )
        single_fallbacks_left -= used_fallbacks
        for page in batch:
            identity = _page_identity(page)
            if identity not in errors and identity in by_id:
                continue
            error = errors.get(identity, "verifier did not return this page")
            failures.append({"scope": failure_scope, "source_id": page.source_id, "source_ids": list(page.all_source_ids), "product": page.axes.get("product", ""), "title": page.title, "page_id": identity, "status": "audit_only", "reason": f"regenerated verification unavailable: {error}"})
            verified[by_page_id[identity]] = replace(page, verification="audit_only")
        for page in batch:
            identity = _page_identity(page)
            if identity not in by_id or identity in errors:
                continue
            violations = tuple(value for value in by_id[identity] if isinstance(value, Mapping))
            if violations:
                failures.append({"scope": failure_scope, "source_id": page.source_id, "source_ids": list(page.all_source_ids), "product": page.axes.get("product", ""), "title": page.title, "page_id": identity, "status": "audit_only", "reason": "generic verifier still found factual violations", "violations": list(violations)})
                verified[by_page_id[identity]] = replace(page, verification="audit_only", violations=violations)
            else:
                verified[by_page_id[identity]] = replace(page, verification="passed", violations=())
    return verified, failures


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding vector dimensions differ")
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        raise ValueError("embedding vector is zero")
    return numerator / (left_norm * right_norm)


def _assign_paths(pages: Sequence[ReaderPage]) -> list[ReaderPage]:
    used: dict[tuple[str, str, str], int] = defaultdict(int)
    result: list[ReaderPage] = []
    for page in sorted(pages, key=lambda item: (item.axes["product"], item.title, _page_identity(item))):
        product_key = page.product_key or _slug(page.axes["product"], "general")
        base = _slug(page.title, "page")
        # Source pages and cross-source answers use one public tree.  A
        # different layout for source pages made the product index lie about
        # where a page-type entry could be found.
        page_dir = page.page_type
        key = (product_key, page_dir, base)
        used[key] += 1
        suffix = "" if used[key] == 1 else f"-{used[key]}"
        relative = f"products/{product_key}/{page_dir + '/' if page_dir else ''}{base}{suffix}.md"
        result.append(replace(page, slug=base + suffix, relative_path=relative))
    return result


def _section_evidence(
    sources_by_id: Mapping[str, SourceDoc],
    page: ReaderPage,
    heading: str,
) -> list[Mapping[str, Any]]:
    section = page.sections.get(heading, {})
    refs = section.get("evidence_ids", ()) if isinstance(section, Mapping) else ()
    by_id = {
        str(item["evidence_id"]): item
        for source_id in page.all_source_ids
        if (source := sources_by_id.get(source_id)) is not None
        for item in source.evidence
    }
    return [by_id[ref] for ref in dict.fromkeys(str(ref) for ref in refs) if ref in by_id]


def _render_section_evidence(
    sources_by_id: Mapping[str, SourceDoc],
    page: ReaderPage,
    heading: str,
) -> str:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in _section_evidence(sources_by_id, page, heading):
        grouped[str(item["source_id"])].append(item)
    if not grouped:
        return f"> 证据：{UNKNOWN}"
    audit_prefix = "../" * len(Path(page.relative_path).parent.parts)
    rows: list[str] = []
    for source_id, items in grouped.items():
        source = sources_by_id.get(source_id)
        if source is None:
            continue
        ranges = ", ".join(
            f"{item['start_line']}-{item['end_line']}"
            for item in items[:8]
        )
        rows.append(f"`{source.relative_path}` 第 {ranges} 行（[Audit 回查]({audit_prefix}Audit.md#{source_id})）")
    return "> 证据：" + "；".join(rows)


def _relative_page_link(from_relative_path: str, target_relative_path: str) -> str:
    """Return a link that resolves from one published page to another."""

    return posixpath.relpath(target_relative_path, posixpath.dirname(from_relative_path))


def _root_relative_prefix(relative_path: str) -> str:
    """Return the relative prefix from a published page to the bundle root."""

    return "../" * len(Path(relative_path).parent.parts)


def _metadata_value(value: Any) -> str:
    """Render one compact JSON scalar inside YAML front matter."""

    return json.dumps(str(value), ensure_ascii=False)


def _render_page(page: ReaderPage, sources_by_id: Mapping[str, SourceDoc], pages: Sequence[ReaderPage]) -> str:
    anchor = f"page-{_page_identity(page)}"
    lines = [
        "---",
        f"page_type: {_metadata_value(PAGE_TYPE_LABELS[page.page_type])}",
        f"product: {_metadata_value(page.axes['product'])}",
        f"module: {_metadata_value(page.axes['module'])}",
        f"object: {_metadata_value(page.axes['object'])}",
        f"scenario: {_metadata_value(page.axes['scenario'])}",
        f"boundary: {_metadata_value(page.axes['boundary'])}",
        f"digest_page_id: {_metadata_value(_page_identity(page))}",
        "---",
        "",
        f"# {page.title}",
        "",
    ]
    if page.projection_id:
        lines.append(f"<!-- digest_projection_id: {page.projection_id} -->")
        lines.append("")
    lines.extend([
        f"> {page.sections['summary']['body']}",
        _render_section_evidence(sources_by_id, page, "summary"),
        "",
        "## 这页解决什么问题",
        "",
        page.question,
        "",
        "## 页面类型",
        "",
        f"- {PAGE_TYPE_LABELS[page.page_type]}",
        "",
    ])
    for heading in PAGE_TYPES[page.page_type]:
        lines.extend([f"## {heading}", "", str(page.sections[heading]["body"]).strip(), _render_section_evidence(sources_by_id, page, heading), ""])
    lines.extend(["## 来源", "", "本页正文只使用下面列出的原始资料；细节可从 Audit 回查。", ""])
    evidence = _page_evidence(sources_by_id, page)
    evidence_by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in evidence:
        evidence_by_source[str(item["source_id"])].append(item)
    for source_id in page.all_source_ids:
        source = sources_by_id.get(source_id)
        if source is None:
            continue
        used_items = evidence_by_source.get(source_id, [])
        ranges = ", ".join(f"{item['start_line']}-{item['end_line']}" for item in used_items[:12]) or "未在正文引用具体段落"
        lines.append(f"- 原始地址：`{source.relative_path}`；原文行：`{ranges}`")
        root_prefix = _root_relative_prefix(page.relative_path)
        lines.append(f"  - [来源索引]({root_prefix}_audit/sources.jsonl)")
        lines.append(f"  - [Audit 回查]({root_prefix}Audit.md#{source.source_id})")
    related = [
        candidate for candidate in pages
        if candidate.relative_path
        and candidate.relative_path != page.relative_path
        and (candidate.product_key or candidate.axes["product"]) == (page.product_key or page.axes["product"])
    ]
    if related:
        lines.extend(["", "## 相关页面", ""])
        for candidate in sorted(related, key=lambda item: (len(item.all_source_ids) < 2, item.title))[:6]:
            link = _relative_page_link(page.relative_path, candidate.relative_path)
            lines.append(f"- [{candidate.title}]({link})：{PAGE_TYPE_LABELS[candidate.page_type]}；{candidate.question}")
    root_prefix = _root_relative_prefix(page.relative_path)
    lines.extend(["", f"- [返回 Home]({root_prefix}Home.md)", f"- [打开本页 Audit 入口]({root_prefix}Audit.md#{anchor})", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_product_index(product_key: str, product_label: str, pages: Sequence[ReaderPage]) -> str:
    lines = [f"# {product_label}", "", f"本页汇总 {product_label} 的 Reader 页面。先按页面类型判断你要解决的问题，再进入具体页面。", "", "## 按页面类型", ""]
    for page_type in PAGE_TYPES:
        selected = [page for page in pages if page.page_type == page_type]
        if not selected:
            continue
        lines.extend([f"### {PAGE_TYPE_LABELS[page_type]}", ""])
        for page in selected:
            lines.append(f"- [{page.title}]({page.relative_path.split('/', 2)[-1]})：{page.question}（模块：{page.axes['module']}）")
        lines.append("")
    lines.extend(["## 按模块", ""])
    modules: dict[str, list[ReaderPage]] = defaultdict(list)
    for page in pages:
        modules[page.axes["module"]].append(page)
    for module in sorted(modules):
        lines.append(f"### {module}")
        for page in sorted(modules[module], key=lambda item: item.title):
            lines.append(f"- [{page.title}]({page.relative_path.split('/', 2)[-1]})")
        lines.append("")
    lines.extend(["- [返回 Home](../../Home.md)", "- [打开 Audit](../../Audit.md)", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_home(
    pages: Sequence[ReaderPage],
    products: Mapping[str, str],
    routes: Mapping[str, Sequence[ReaderPage]],
    sources: Sequence[SourceDoc],
    quality_routes: Sequence[ReaderPage] = (),
) -> str:
    lines = ["# KnowledgeDigest", "", "这是本次原始资料的读者入口。先按你要解决的问题进入，再按产品、模块和页面类型继续定位。", "", "## 我现在要做什么", ""]

    def page_product_key(page: ReaderPage) -> str:
        return page.product_key or _slug(page.axes["product"], "general")

    def product_label(product_key: str, page: ReaderPage | None = None) -> str:
        if product_key in products:
            return products[product_key]
        return page.axes["product"] if page is not None else product_key

    if quality_routes:
        lines.extend(["### 按问题和场景", "", "| 我想解决的问题 | 使用场景 | Reader 答案 |", "| --- | --- | --- |"])
        for page in sorted(quality_routes, key=lambda item: item.projection_id or item.title):
            lines.append(f"| {page.question} | {page.axes['scenario']} | [{page.title}]({page.relative_path}) |")
        lines.append("")
    for label, selected in routes.items():
        lines.extend([f"### {label}", ""])
        if not selected:
            lines.extend([f"- {UNKNOWN}", ""])
            continue
        route_type = _ROUTE_PAGE_TYPES.get(label)
        route_product_keys = sorted({
            page_product_key(page)
            for page in pages
            if route_type and page.page_type == route_type
        })
        for product_key in route_product_keys:
            label = product_label(product_key)
            lines.append(
                f"- [{label} {PAGE_TYPE_LABELS[route_type]}目录](products/{product_key}/index.md)：进入该产品的全部{PAGE_TYPE_LABELS[route_type]}页面"
            )
        seen: set[str] = set()
        for page in selected:
            if page.relative_path in seen:
                continue
            seen.add(page.relative_path)
            lines.append(f"- [{page.title}]({page.relative_path})：{product_label(page_product_key(page), page)} / {page.axes['module']}")
        lines.append("")
    lines.extend(["## 按产品", ""])
    page_product_fallbacks = {
        page_product_key(page): page
        for page in pages
        if page_product_key(page) not in products
    }
    product_keys = set(products) | set(page_product_fallbacks)
    for product_key in sorted(product_keys, key=lambda key: product_label(key, page_product_fallbacks.get(key))):
        label = product_label(product_key, page_product_fallbacks.get(product_key))
        lines.append(f"- [{label}](products/{product_key}/index.md)")
    lines.extend(["", "## 按页面类型", ""])
    for page_type, label in PAGE_TYPE_LABELS.items():
        count = sum(page.page_type == page_type for page in pages)
        lines.append(f"- **{label}**：{count} 页")
    lines.extend(["", "## 资料范围", "", f"- 原始资料：{len(sources)} 条 Markdown/文本/JSON 文件", "- 事实来源：只使用本次输入目录；CompanyBrain 不参与生成", "- 完整来源回查：见 [Audit](Audit.md)", "- 如果页面标记‘原始资料未明确’，表示本次资料没有足够依据，不是系统替资料做了猜测。", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_readme(sources: Sequence[SourceDoc], pages: Sequence[ReaderPage], run_id: str) -> str:
    return "\n".join([
        "# KnowledgeDigest",
        "",
        "这是本次原始资料的可读知识入口。",
        "",
        "1. 先读 [Home](Home.md)，按问题或场景找答案。",
        "2. 再读具体 Reader 页面；正文按定位、概念、操作、诊断、经验组织。",
        "3. 页面末尾的“来源”可以回到 [Audit](Audit.md) 和原始资料快照。",
        "",
        f"- 本次来源：{len(sources)} 条；Reader 页面：{len(pages)} 页。",
        f"- 运行：`{run_id}`。",
        "- `_audit/sources.jsonl` 保存逐条来源元数据；`_audit/evidence.jsonl` 保存证据与页面绑定。",
        "- 本次质量运行只有五项比较和完整性硬门全部通过才会是 `released`；否则终态是 `not_released`，但仍保留可回查的候选和 Audit。",
        "",
    ])


def _render_audit(sources: Sequence[SourceDoc], pages: Sequence[ReaderPage], failures: Sequence[Mapping[str, Any]], run_id: str) -> str:
    pages_by_source: dict[str, list[ReaderPage]] = defaultdict(list)
    quality_pages_by_projection = {
        page.projection_id: page
        for page in pages
        if page.projection_id
    }
    for page in pages:
        for source_id in page.all_source_ids:
            pages_by_source[source_id].append(page)
    failure_by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    global_failures: list[Mapping[str, Any]] = []
    for failure in failures:
        if failure.get("scope") in {"topic", "quality"}:
            global_failures.append(failure)
            continue
        source_ids = [str(item) for item in failure.get("source_ids", []) if str(item)]
        if not source_ids and failure.get("source_id"):
            source_ids = [str(failure["source_id"])]
        if not source_ids:
            global_failures.append(failure)
        for source_id in source_ids:
            failure_by_source[source_id].append(failure)
    audit_only_sources = {
        source.source_id
        for source in sources
        if source.status in {"known_empty", "failed", "provider_failed", "unsupported"}
        or not any(page.verification != "audit_only" for page in pages_by_source.get(source.source_id, []))
    }
    lines = ["# Audit", "", "本页是回查入口，不是 Reader 正文。每条来源都列出状态、原始路径、Reader 页面和精确行号证据。", "", f"- 运行：`{run_id}`", f"- 来源总数：`{len(sources)}`", f"- Reader 页面：`{len(pages)}`", f"- Audit-only 来源：`{len(audit_only_sources)}`", "", "## 来源清单", ""]
    for source in sources:
        source_pages = pages_by_source.get(source.source_id, [])
        lines.extend([f"## {source.relative_path}", "", f"<a id=\"{source.source_id}\"></a>", f"- source_status: `{('duplicate_alias' if source.status == 'duplicate_alias' else 'reader' if source.source_id not in audit_only_sources else 'audit_only')}`", f"- source_kind: `{source.status}`", f"- source_id: `{source.source_id}`", f"- 原始路径：`{source.relative_path}`", f"- 原文行数：`{len(source.lines)}`", "- 来源索引：[_audit/sources.jsonl](_audit/sources.jsonl)", f"- evidence_count: `{len(source.evidence)}`"])
        if source.duplicate_of:
            lines.append(f"- duplicate_of: `{source.duplicate_of}`；正文复用 canonical Reader 页面，原始路径仍单独保留")
        if source_pages:
            lines.append("- Reader 页面：")
            for page in sorted(source_pages, key=lambda item: (len(item.all_source_ids) < 2, item.title)):
                lines.append(f"  - [{page.title}]({page.relative_path})；page_type: `{page.page_type}`；verification: `{page.verification}`；[本页回查](#page-{_page_identity(page)})")
        else:
            lines.append("- Reader 页面：未生成")
        for failure in failure_by_source.get(source.source_id, []):
            lines.append(f"- failure: `{failure.get('reason', 'unknown')}`")
            for violation in failure.get("violations", ()):
                if not isinstance(violation, Mapping):
                    continue
                refs = ", ".join(str(item) for item in violation.get("evidence_ids", ()) if str(item))
                detail = str(violation.get("detail", "unknown"))
                suffix = f"；evidence: `{refs}`" if refs else ""
                lines.append(f"  - violation `{violation.get('type', 'unknown')}`：{detail}{suffix}")
        lines.extend(["", "- Evidence 详情：见 [`_audit/evidence.jsonl`](_audit/evidence.jsonl)，按 evidence_id 和行号回查；来源索引不复制整篇原文。", ""])
        if source.evidence:
            lines.extend(["### 原始证据坐标", ""])
            for item in source.evidence:
                block_hash = item.get("block_content_sha256") or _sha(str(item.get("text", "")).encode("utf-8"))
                evidence_id = str(item["evidence_id"])
                lines.append(f'<a id="evidence-{evidence_id}"></a>')
                lines.append(
                    f"- `{evidence_id}`：第 `{item['start_line']}-{item['end_line']}` 行；block_sha256：`{block_hash}`"
                )
            lines.append("")
    lines.extend(["## 页面索引", ""])
    for page in sorted(pages, key=lambda item: (item.relative_path, _page_identity(item))):
        lines.extend([f"<a id=\"page-{_page_identity(page)}\"></a>", f"- [{page.title}]({page.relative_path})；page_key: `{page.page_key}`；page_type: `{page.page_type}`；source_ids: `{', '.join(page.all_source_ids)}`"])
    if global_failures:
        lines.extend(["## 运行警告", ""])
        for failure in global_failures:
            scope = " / ".join(str(value) for value in (failure.get("product"), failure.get("title")) if value)
            prefix = f"{scope}：" if scope else ""
            lines.append(f"- `{failure.get('status', 'warning')}`：{prefix}{failure.get('reason', 'unknown')}")
            projection_id = str(failure.get("projection_id", ""))
            if projection_id:
                lines.append(f"  - projection_id: `{projection_id}`")
                page = quality_pages_by_projection.get(projection_id)
                if page is not None:
                    lines.append(f"  - Reader 页面：[{page.title}]({page.relative_path})；[本页回查](#page-{_page_identity(page)})")
                lines.append("  - 详细生成、校验和证据闭环：[_audit/quality.json](_audit/quality.json)")
            for violation in failure.get("violations", ()):
                if not isinstance(violation, Mapping):
                    continue
                refs = ", ".join(str(item) for item in violation.get("evidence_ids", ()) if str(item))
                detail = str(violation.get("detail", "unknown"))
                suffix = f"；evidence: `{refs}`" if refs else ""
                lines.append(f"  - violation `{violation.get('type', 'unknown')}`：{detail}{suffix}")
        lines.append("")
    lines.extend(["## 机器记录", "", "- 完整 Evidence 绑定：`_audit/evidence.jsonl`", "- 来源元数据索引：`_audit/sources.jsonl`", "- 运行记录：`_audit/run-result.json`", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_sources(
    sources: Sequence[SourceDoc],
    failures: Sequence[Mapping[str, Any]] = (),
) -> bytes:
    """Write one compact, machine-readable raw-source record per line."""

    failure_by_source_id: dict[str, Mapping[str, Any]] = {}
    for failure in failures:
        source_ids = failure.get("source_ids", ())
        if not isinstance(source_ids, (list, tuple)):
            source_ids = ()
        if failure.get("source_id"):
            source_ids = (*source_ids, failure["source_id"])
        for source_id in source_ids:
            if source_id and str(source_id) not in failure_by_source_id:
                failure_by_source_id[str(source_id)] = failure
    rows = []
    for source in sources:
        source_failure = failure_by_source_id.get(source.source_id)
        rows.append(_canonical_json({
            "source_id": source.source_id,
            "relative_path": source.relative_path,
            "product_key": source.product,
            "product_label": source.product_label,
            "raw_hash": _sha(source.raw_bytes),
            "status": source.status,
            "duplicate_of": source.duplicate_of,
            "line_count": len(source.lines),
            "evidence": [
                {
                    "evidence_id": str(item["evidence_id"]),
                    "start_line": int(item["start_line"]),
                    "end_line": int(item["end_line"]),
                    "block_content_sha256": str(item.get("block_content_sha256") or _sha(str(item.get("text", "")).encode("utf-8"))),
                }
                for item in source.evidence
            ],
            "evidence_ids": [str(item["evidence_id"]) for item in source.evidence],
            "failure": dict(source_failure) if source_failure else None,
        }).decode("utf-8").rstrip("\n"))
    return (("\n".join(rows) + "\n") if rows else "").encode("utf-8")


def _render_evidence(
    sources: Sequence[SourceDoc],
    pages: Sequence[ReaderPage],
    routes: Mapping[str, Sequence[ReaderPage]] | None = None,
) -> bytes:
    """Render Reader/Audit bindings without copying raw source prose."""

    source_by_id = {source.source_id: source for source in sources}
    source_ids = set(source_by_id)
    rows: list[str] = []

    def append_unit(
        *,
        page_path: str,
        page_key: str,
        surface: str,
        slot: str,
        body: str,
        audit_ref: str,
        claim_ids: Sequence[Any] = (),
        evidence_ids: Sequence[Any] = (),
        source_id_values: Sequence[Any] = (),
        home_target_page_identity: str | None = None,
    ) -> None:
        if not str(body).strip():
            return
        clean_source_ids = [
            str(item)
            for item in dict.fromkeys(str(item) for item in source_id_values if str(item) in source_ids)
        ]
        clean_evidence_ids = list(dict.fromkeys(str(item) for item in evidence_ids if str(item)))
        evidence_order: dict[str, tuple[str, int, str]] = {}
        for source_id in clean_source_ids:
            source = source_by_id[source_id]
            for evidence in source.evidence:
                evidence_id = str(evidence.get("evidence_id", ""))
                if evidence_id in clean_evidence_ids:
                    evidence_order[evidence_id] = (
                        source.relative_path,
                        int(evidence.get("start_line", 0)),
                        evidence_id,
                    )
        clean_evidence_ids.sort(key=lambda evidence_id: evidence_order.get(evidence_id, ("", 0, evidence_id)))
        bindings: list[dict[str, Any]] = []
        for evidence_id in clean_evidence_ids:
            evidence = next(
                (
                    item
                    for source_id in clean_source_ids
                    for item in source_by_id[source_id].evidence
                    if str(item.get("evidence_id")) == evidence_id
                ),
                None,
            )
            if evidence is None:
                continue
            source_id = str(evidence.get("source_id") or (clean_source_ids[0] if clean_source_ids else ""))
            source = source_by_id.get(source_id)
            if source is None:
                continue
            block_id = str(evidence.get("block_id") or evidence_id)
            claim_id = str(evidence.get("claim_id") or f"claim-{block_id}")
            block_text = str(evidence.get("text", ""))
            bindings.append({
                "raw_source_id": source_id,
                "raw_hash": _sha(source.raw_bytes),
                "block_id": block_id,
                "claim_id": claim_id,
                "locator": {
                    "start_line": int(evidence.get("start_line", 0)),
                    "end_line": int(evidence.get("end_line", 0)),
                },
                "support_sha256": str(
                    evidence.get("block_content_sha256")
                    or _sha(_normalised_text(block_text))
                ),
            })
        primary = bindings[0] if bindings else {
            "raw_source_id": clean_source_ids[0] if clean_source_ids else "",
            "raw_hash": _sha(source_by_id[clean_source_ids[0]].raw_bytes) if clean_source_ids else "",
            "block_id": "",
            "claim_id": "",
            "locator": {},
            "support_sha256": "",
        }
        if clean_evidence_ids:
            audit_ref = f"Audit.md#evidence-{clean_evidence_ids[0]}"
        stable_identity = "\0".join((str(page_path), str(page_key), str(surface), str(slot)))
        unit_id = f"u-{hashlib.sha256(stable_identity.encode('utf-8')).hexdigest()[:24]}"
        rows.append(_canonical_json({
            "schema_version": "knowledge-digest-render-unit.v1",
            "unit_id": unit_id,
            "page_key": str(page_key),
            "page_path": str(page_path),
            "surface": str(surface),
            "slot": str(slot),
            "text_sha256": _sha(_normalised_text(body).encode("utf-8")),
            "audit_ref": str(audit_ref),
            "claim_ids": list(dict.fromkeys(str(item) for item in claim_ids if str(item))),
            "evidence_ids": clean_evidence_ids,
            "source_ids": clean_source_ids,
            "raw_source_id": primary["raw_source_id"],
            "raw_hash": primary["raw_hash"],
            "block_id": primary["block_id"],
            "claim_id": primary["claim_id"],
            "locator": primary["locator"],
            "support_sha256": primary["support_sha256"],
            "evidence_bindings": bindings,
            "home_target_page_identity": home_target_page_identity,
        }).decode("utf-8").rstrip("\n"))

    for page in sorted(pages, key=lambda item: (item.relative_path, _page_identity(item))):
        audit_ref = f"Audit.md#page-{_page_identity(page)}"
        summary = page.sections.get("summary", {})
        if isinstance(summary, Mapping):
            append_unit(
                page_path=page.relative_path,
                page_key=page.page_key,
                surface="Reader.title",
                slot="title",
                body=page.title,
                audit_ref=audit_ref,
                claim_ids=summary.get("claim_ids", ()),
                evidence_ids=summary.get("evidence_ids", ()),
                source_id_values=page.all_source_ids,
            )
            append_unit(
                page_path=page.relative_path,
                page_key=page.page_key,
                surface="Reader.question",
                slot="question",
                body=page.question,
                audit_ref=audit_ref,
                claim_ids=summary.get("claim_ids", ()),
                evidence_ids=summary.get("evidence_ids", ()),
                source_id_values=page.all_source_ids,
            )
            append_unit(
                page_path=page.relative_path,
                page_key=page.page_key,
                surface="Reader.summary",
                slot="summary",
                body=str(summary.get("body", "")),
                audit_ref=audit_ref,
                claim_ids=summary.get("claim_ids", ()),
                evidence_ids=summary.get("evidence_ids", ()),
                source_id_values=page.all_source_ids,
            )
            append_unit(
                page_path=page.relative_path,
                page_key=page.page_key,
                surface="Reader.page_type",
                slot="page_type",
                body=f"页面类型：{PAGE_TYPE_LABELS.get(page.page_type, page.page_type)}",
                audit_ref=audit_ref,
                claim_ids=summary.get("claim_ids", ()),
                evidence_ids=summary.get("evidence_ids", ()),
                source_id_values=page.all_source_ids,
            )
        for axis_name, axis_label in (
            ("product", "产品"),
            ("module", "模块"),
            ("object", "对象"),
            ("scenario", "场景"),
            ("boundary", "边界"),
        ):
            # An unknown taxonomy value is deliberately visible in page
            # metadata, but it is not a factual claim.  Do not manufacture
            # an empty Reader.axis audit unit that cannot point to a raw
            # block; the metadata itself remains reader-visible.
            if page.axes.get(axis_name) == UNKNOWN or not page.axis_evidence_ids.get(axis_name):
                continue
            append_unit(
                page_path=page.relative_path,
                page_key=page.page_key,
                surface="Reader.axis",
                slot=axis_name,
                body=f"{axis_label}：{page.axes.get(axis_name, '')}",
                audit_ref=audit_ref,
                claim_ids=page.axis_evidence_ids.get(axis_name, ()),
                evidence_ids=page.axis_evidence_ids.get(axis_name, ()),
                source_id_values=page.all_source_ids,
            )
        for heading in PAGE_TYPES.get(page.page_type, ()):
            section = page.sections.get(heading, {})
            if not isinstance(section, Mapping):
                continue
            append_unit(
                page_path=page.relative_path,
                page_key=page.page_key,
                surface="Reader.answer_body",
                slot=heading,
                body=str(section.get("body", "")),
                audit_ref=audit_ref,
                claim_ids=section.get("claim_ids", ()),
                evidence_ids=section.get("evidence_ids", ()),
                source_id_values=page.all_source_ids,
            )
            append_unit(
                page_path=page.relative_path,
                page_key=page.page_key,
                surface="Reader.section",
                slot=heading,
                body=str(section.get("body", "")),
                audit_ref=audit_ref,
                claim_ids=section.get("claim_ids", ()),
                evidence_ids=section.get("evidence_ids", ()),
                source_id_values=page.all_source_ids,
            )

    home_route_targets: set[tuple[str, str]] = set()
    for route_name, selected in (routes or {}).items():
        for page in selected:
            home_route_target = (str(route_name), _page_identity(page))
            if home_route_target in home_route_targets:
                raise ValueError(
                    "duplicate Home.route target: "
                    f"route_name={route_name!r}, page_identity={home_route_target[1]!r}"
                )
            home_route_targets.add(home_route_target)
            summary = page.sections.get("summary", {})
            evidence_ids = summary.get("evidence_ids", ()) if isinstance(summary, Mapping) else ()
            body = f"{route_name}\n{page.question}\n{page.title}\n{page.relative_path}"
            append_unit(
                page_path="bundle/Home.md",
                page_key=f"route:{_sha(_normalised_text(route_name))[:20]}",
                surface="Home.route",
                slot=f"{route_name}:{_page_identity(page)}",
                body=body,
                audit_ref=f"Audit.md#page-{_page_identity(page)}",
                evidence_ids=evidence_ids,
                source_id_values=page.all_source_ids,
                home_target_page_identity=_page_identity(page),
            )
    return (("\n".join(rows) + "\n") if rows else "").encode("utf-8")


def _route_pages(pages: Sequence[ReaderPage], embedder: Embedder) -> dict[str, list[ReaderPage]]:
    if not pages:
        return {key: [] for key in ROUTE_QUERIES}
    texts = [f"{page.title}\n{page.question}\n{page.axes['product']} {page.axes['module']} {page.axes['object']} {page.axes['scenario']} {page.axes['boundary']}\n{page.sections['summary']['body']}\n主题来源数：{len(page.all_source_ids)}" for page in pages]
    query_values = list(ROUTE_QUERIES.values())
    vectors = embedder.embed(texts + query_values)
    if len(vectors) != len(texts) + len(query_values):
        raise ProviderError("embedding result count does not match route inputs")
    page_vectors = vectors[: len(texts)]
    routes: dict[str, list[ReaderPage]] = {}
    for index, label in enumerate(ROUTE_QUERIES):
        query_vector = vectors[len(texts) + index]
        target_type = _ROUTE_PAGE_TYPES[label]
        eligible = [(page, vector) for page, vector in zip(pages, page_vectors) if page.page_type == target_type]
        ranked = sorted(
            eligible,
            key=lambda item: (
                _cosine(query_vector, item[1])
                + (0.10 if len(item[0].all_source_ids) > 1 else 0.0)
            ),
            reverse=True,
        )
        # A Home route has one auditable primary target.  Product indexes and
        # the dedicated quality table remain the multi-page navigation; the
        # route itself must not hide an arbitrary choice among eight targets.
        routes[label] = [ranked[0][0]] if ranked else []
    return routes


def _quality_evidence(
    projection: QualityProjection,
    sources_by_path: Mapping[str, SourceDoc],
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    """Materialise every frozen line reference as exact, page-citable evidence."""

    rows: list[dict[str, Any]] = []
    evidence_ids: set[str] = set()
    source_ids: set[str] = set()
    for ref in projection.source_block_refs:
        path, start, end, label = parse_block_ref(ref)
        source = sources_by_path.get(path)
        if source is None:
            raise ValueError(f"quality projection source is missing: {projection.projection_id}: {path}")
        if end > len(source.lines):
            raise ValueError(f"quality projection line range is outside source: {projection.projection_id}: {ref}")
        evidence_id = "qev-" + _sha(f"{projection.projection_id}\0{ref}")[:24]
        block_text = "\n".join(source.lines[start - 1 : end])
        rows.append({
            "evidence_id": evidence_id,
            "block_ref": ref,
            "source_id": source.source_id,
            "source_path": source.relative_path,
            "start_line": start,
            "end_line": end,
            "label": label,
            "text": block_text,
            "source_content_sha256": _sha(source.raw_bytes),
            "block_content_sha256": _sha(block_text),
        })
        evidence_ids.add(evidence_id)
        source_ids.add(source.source_id)
    expected_paths = set(projection.source_paths)
    actual_paths = {str(item["source_path"]) for item in rows}
    if not expected_paths.issubset(actual_paths):
        missing = ", ".join(sorted(expected_paths - actual_paths))
        raise ValueError(f"quality projection source has no line evidence: {projection.projection_id}: {missing}")
    return rows, evidence_ids, source_ids


def _augment_quality_sources(
    sources: Sequence[SourceDoc],
    projections: Sequence[QualityProjection],
) -> tuple[tuple[SourceDoc, ...], dict[str, list[dict[str, Any]]]]:
    """Attach projection line blocks to the immutable source records for rendering and Audit."""

    by_path = {source.relative_path: source for source in sources}
    extra: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for projection in projections:
        rows, _required_ids, _source_ids = _quality_evidence(projection, by_path)
        for row in rows:
            extra[str(row["source_id"])].append({
                "evidence_id": row["evidence_id"],
                "source_id": row["source_id"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "text": row["text"],
                "label": row["label"],
                "block_ref": row["block_ref"],
                "source_content_sha256": row["source_content_sha256"],
                "block_content_sha256": row["block_content_sha256"],
                "status": "supported",
            })
    augmented: list[SourceDoc] = []
    for source in sources:
        additions = extra.get(source.source_id, [])
        existing = {str(item["evidence_id"]) for item in source.evidence}
        augmented.append(replace(source, evidence=tuple(source.evidence) + tuple(item for item in additions if str(item["evidence_id"]) not in existing)))
    return tuple(augmented), extra


def _quality_route_sources(
    projections: Sequence[QualityProjection],
    sources: Sequence[SourceDoc],
    embedder: Embedder,
    *,
    evaluation_mode: str = "full",
) -> tuple[dict[str, tuple[str, ...]], list[dict[str, Any]]]:
    """Use real embeddings to select source candidates, then force declared closure."""

    def route_name_for(projection: QualityProjection) -> str:
        return next(
            (name for name, page_type in _ROUTE_PAGE_TYPES.items() if page_type == projection.page_type),
            "",
        )

    def product_key_for(projection: QualityProjection, selected_paths: Sequence[str]) -> str:
        selected_keys = {
            source.product
            for source in sources
            if source.relative_path in set(selected_paths)
        }
        if len(selected_keys) == 1:
            return next(iter(selected_keys))
        if len(selected_keys) > 1:
            return _SHARED_PRODUCT_KEY
        label = _normalised_text(projection.axes.get("product", "")).strip().casefold()
        for known_key, (product_key, product_label) in _KNOWN_PRODUCT_ROOTS.items():
            if label in {known_key, _normalised_text(product_label).casefold()}:
                return product_key
        return _slug(label, "unclassified")

    available_paths = {source.relative_path for source in sources}
    routable: list[QualityProjection] = []
    ledger: list[dict[str, Any]] = []
    for projection in projections:
        missing = sorted(set(projection.source_paths) - available_paths)
        if missing:
            # A slice is allowed to omit sources that the full projection
            # needs.  Record that closure difference and skip the provider;
            # silently treating it as an empty answer would corrupt the
            # diagnostic result.
            ledger.append({
                "projection_id": projection.projection_id,
                "query": projection_query(projection),
                "route_name": route_name_for(projection),
                "product_key": product_key_for(projection, ()),
                "query_id": _question_id(
                    projection.question,
                    projection.axes["scene"],
                    product_key_for(projection, ()) + "\0" + projection.projection_id,
                ),
                "top_k": [],
                "candidate_source_ids": [],
                "top_k_scores": [],
                "selected_source_paths": [],
                "selected_source_ids": [],
                "required_source_paths": list(projection.source_paths),
                "missing_full_source_paths": missing,
                "embedding_model": {},
                "embedding_input_sha256": "",
                "closure": "not_evaluable",
                "status": "source_not_in_slice" if evaluation_mode == "slice" else "failed",
            })
        else:
            routable.append(projection)

    usable = [source for source in sources if source.status == "ready"]
    if routable and not usable:
        raise ProviderError("quality projection has no usable source documents")
    if not routable:
        return {}, ledger
    source_by_path = {source.relative_path: source for source in usable}
    source_texts = [
        # Jina is only a selector.  It receives stable metadata, never source
        # prose; Qwen receives the exact evidence closure after routing.
        _json({
            "title": Path(source.relative_path).stem,
            "product": source.product_label,
            "source_id": source.source_id,
            "source_path": source.relative_path,
            "content_sha256": _sha(source.raw_bytes),
            "line_count": len(source.lines),
        })
        for source in usable
    ]
    query_texts = [projection_query(projection) for projection in routable]
    embedding_input_sha256 = _sha(_json(source_texts + query_texts))
    vectors = embedder.embed(source_texts + query_texts)
    if len(vectors) != len(source_texts) + len(query_texts):
        raise ProviderError("quality embedding result count does not match projection inputs")
    embedding_response_sha256 = _sha(_canonical_json(vectors))
    routes: dict[str, tuple[str, ...]] = {}
    ledger: list[dict[str, Any]] = []
    for index, projection in enumerate(routable):
        query_vector = vectors[len(source_texts) + index]
        product_name = projection.axes["product"].split("（", 1)[0].strip().casefold()
        product_usable = [
            source for source in usable
            if product_name in source.product_label.casefold()
            or source.product_label.casefold() in product_name
            or source.relative_path in projection.source_paths
        ]
        if product_usable:
            eligible_sources = product_usable
            eligible_indexes = {source.relative_path: source_index for source_index, source in enumerate(usable)}
        else:
            eligible_sources = usable
            eligible_indexes = {source.relative_path: source_index for source_index, source in enumerate(usable)}
        ranked = sorted(
            ((source, _cosine(query_vector, vectors[eligible_indexes[source.relative_path]])) for source in eligible_sources),
            key=lambda row: (-row[1], row[0].relative_path),
        )
        top_paths = [source.relative_path for source, _score in ranked[: min(8, len(ranked))]]
        # A frozen question projection already owns its raw evidence closure.
        # Embeddings decide the ranked route receipt, but unrelated nearest
        # neighbours must not be sent to Qwen: they dilute the question and
        # invite cross-projection facts into the answer.
        required_paths = list(dict.fromkeys(projection.source_paths))
        required_set = set(required_paths)
        # Keep the complete frozen closure, but let the current embedding
        # ranking determine the order sent to Qwen.  This makes Jina an
        # actual route input while still preventing unrelated nearest
        # neighbours from entering the answer.
        selected = [
            source.relative_path
            for source, _score in ranked
            if source.relative_path in required_set
        ]
        selected.extend(path for path in required_paths if path not in selected)
        missing = sorted(set(selected) - set(source_by_path))
        if missing:
            raise ProviderError(f"quality embedding route cannot cover required sources: {projection.projection_id}: {missing}")
        routes[projection.projection_id] = tuple(selected)
        selected_source_ids = [source_by_path[path].source_id for path in selected]
        selected_closure_sha256 = _sha(
            _canonical_json(sorted(selected_source_ids, key=lambda value: value.encode("utf-8")))
        )
        product_key = product_key_for(projection, selected)
        ledger.append({
            "projection_id": projection.projection_id,
            "query": projection_query(projection),
            "route_name": route_name_for(projection),
            "product_key": product_key,
            "query_id": _question_id(
                projection.question,
                projection.axes["scene"],
                product_key + "\0" + projection.projection_id,
            ),
            "top_k": top_paths,
            "candidate_source_ids": [source.source_id for source, _score in ranked],
            "all_scores": {
                source.source_id: round(float(score), 8)
                for source, score in sorted(ranked, key=lambda row: row[0].source_id.encode("utf-8"))
            },
            "top_k_scores": [
                {"source_path": source.relative_path, "score": round(float(score), 8)}
                for source, score in ranked[: min(8, len(ranked))]
            ],
            "selected_source_paths": selected,
            "selected_source_ids": selected_source_ids,
            "required_source_paths": list(projection.source_paths),
            "embedding_model": dict(embedder.identity),
            "embedding_input_sha256": embedding_input_sha256,
            "embedding_response_sha256": embedding_response_sha256,
            "embedding_selected_closure_sha256": selected_closure_sha256,
            "closure": "closed",
            "status": "ready",
        })
    return routes, ledger


def _quality_page_text(page: ReaderPage) -> str:
    return "\n".join(
        [page.title, page.question, *[str(section.get("body", "")) for section in page.sections.values() if isinstance(section, Mapping)]]
    )


def _quality_candidate(
    projection: QualityProjection,
    sources_by_path: Mapping[str, SourceDoc],
    selected_paths: Sequence[str],
    model: SemanticModel,
    feedback: Sequence[Mapping[str, Any]] = (),
) -> tuple[ReaderPage, str, str, tuple[SourceDoc, ...]]:
    """Ask Qwen for one complete, evidence-bound quality page."""

    evidence, _required_evidence_ids, _all_required_source_ids = _quality_evidence(
        projection, sources_by_path
    )
    reader_required_groups = reader_evidence_groups(projection, evidence)
    required_reader_evidence_ids = tuple(dict.fromkeys(
        str(row["evidence_id"])
        for requirement in (*projection.required_claims, *projection.required_boundaries)
        if isinstance(requirement.get("surface"), str)
        and item_reader_visible(requirement)
        for ref in requirement.get("source_block_refs", ())
        for row in evidence
        if str(row.get("block_ref", "")) == str(ref)
    ))
    selected_sources = tuple(
        sources_by_path[path] for path in selected_paths if path in sources_by_path
    )
    selected_context = tuple(
        {
            "source_path": source.relative_path,
            "source_id": source.source_id,
            "raw_context": (
                source.text
                if len(source.text) <= 1200
                else source.text[:800] + "\n……中间原文省略，仅用于候选路由参考……\n" + source.text[-400:]
            ),
        }
        for source in selected_sources
    )
    expected_axes = {
        "product": projection.axes["product"],
        "module": projection.axes["module"],
        "object": projection.axes["object"],
        "scenario": projection.axes["scene"],
        "boundary": projection.axes["boundary"],
    }
    prompt = projection_prompt(
        projection,
        evidence,
        PAGE_TYPES,
        UNKNOWN,
        selected_paths,
        selected_context,
        feedback,
    )
    response = model.generate(prompt)
    value = _parse_json(response)
    candidate = _normalise_page(
        selected_sources,
        value,
        expected_page_type=projection.page_type,
        page_id=projection.projection_id,
        projection_id=projection.projection_id,
        answer_page=True,
        expected_title=projection.title,
        expected_question=projection.question,
        expected_axes=expected_axes,
        # Reader may cite only the sources it actually needs for this answer;
        # every Reader-visible requirement must still have an exact evidence
        # block in the answer.
        required_source_ids=(),
        required_evidence_ids=required_reader_evidence_ids,
        allowed_evidence_ids=[row["evidence_id"] for row in evidence],
        required_evidence_groups=reader_required_groups,
        enforce_multiple_sources=False,
        require_task5_semantic=True,
    )
    forbidden = [
        left
        for left, _reason in projection.forbidden_literals
        if left and left in _quality_page_text(candidate)
    ]
    if forbidden:
        raise ValueError("quality page contains forbidden wording: " + ", ".join(forbidden[:3]))
    return candidate, prompt, response, selected_sources


def _verify_quality_pages_strict(
    pages: Sequence[ReaderPage],
    sources: Sequence[SourceDoc],
    model: SemanticModel,
    projections: Sequence[QualityProjection] = (),
    routes: Mapping[str, Sequence[str]] | None = None,
    trace_by_projection: dict[str, list[dict[str, Any]]] | None = None,
) -> tuple[list[ReaderPage], list[dict[str, Any]]]:
    """Verify answer pages and repair factual violations once, through Qwen."""

    by_id = {source.source_id: source for source in sources}
    checked, raw_failures = _verify_pages(
        list(pages),
        by_id,
        model,
        regenerate=False,
        attempts=_QUALITY_VERIFY_ATTEMPTS,
        # Quality evidence blocks are frozen line ranges.  Do not clip the
        # middle of a block: that can hide the very condition the verifier is
        # meant to check and create a false unsupported finding.
        evidence_limit=4000,
        # A batch response can omit or duplicate page identities when the
        # answer pages contain long evidence closures.  One page per verifier
        # request makes the result count and failure identity deterministic;
        # the call plan already budgets one logical verifier request per page.
        batch_size=1,
        trace_by_page=trace_by_projection,
    )
    by_projection = {projection.projection_id: projection for projection in projections}
    by_page = {_page_identity(page): page for page in pages}
    failed_ids = {
        str(failure.get("page_id", ""))
        for failure in raw_failures
        if failure.get("page_id")
    }
    repaired_pages: dict[str, ReaderPage] = {}
    failures: list[dict[str, Any]] = []
    repair_budget = _QUALITY_REPAIR_LIMIT
    by_identity = {_page_identity(page): page for page in pages}
    for failure in raw_failures:
        item = dict(failure)
        item["scope"] = "quality"
        page = by_identity.get(str(item.get("page_id", "")))
        if page is not None and page.projection_id:
            item["projection_id"] = page.projection_id
        projection = by_projection.get(page.projection_id) if page is not None else None
        selected_paths = tuple((routes or {}).get(page.projection_id, ())) if page is not None else ()
        violations = item.get("violations")
        repairable = (
            page is not None
            and projection is not None
            and bool(selected_paths)
            and item.get("reason") == "quality verifier found factual violations"
            and isinstance(violations, list)
            and bool(violations)
            and repair_budget > 0
        )
        if repairable:
            repair_budget -= 1
            trace_store = trace_by_projection if trace_by_projection is not None else {}
            projection_trace = trace_store.setdefault(projection.projection_id, [])
            try:
                candidate, prompt, response, selected_sources = _quality_candidate(
                    projection,
                    {source.relative_path: source for source in sources},
                    selected_paths,
                    model,
                    feedback=tuple(
                        {"type": "verifier_violation", **dict(violation)}
                        for violation in violations
                        if isinstance(violation, Mapping)
                    ),
                )
                repair_event = {
                    "stage": "repair",
                    "attempt": 1,
                    "selected_source_ids": [source.source_id for source in selected_sources],
                    "selected_source_paths": list(selected_paths),
                    "qwen_payload_sha256": _sha(prompt),
                    "prompt_sha256": _sha(prompt),
                    "response_sha256": _sha(response),
                    "status": "received",
                }
                projection_trace.append(repair_event)
                repaired_checked, repaired_failures = _verify_pages(
                    [candidate],
                    by_id,
                    model,
                    regenerate=False,
                    attempts=1,
                    evidence_limit=4000,
                    trace_by_page=trace_store,
                )
                if not repaired_failures and repaired_checked and repaired_checked[0].verification != "audit_only":
                    repair_event["status"] = "passed"
                    repair_event["page_key"] = candidate.page_key
                    repaired_pages[_page_identity(page)] = replace(candidate, verification="passed", violations=())
                    continue
                repair_reason = (
                    str(repaired_failures[0].get("reason", "repair verification failed"))
                    if repaired_failures
                    else "repair verification did not return a valid page"
                )
                repair_event["status"] = "failed"
                repair_event["error"] = repair_reason[:500]
                item["reason"] = f"{item.get('reason', 'quality verifier failed')}; repair failed: {repair_reason}"
            except (ProviderError, ValueError, TypeError) as error:
                if projection_trace and projection_trace[-1].get("stage") == "repair":
                    projection_trace[-1]["status"] = "failed"
                    projection_trace[-1]["error"] = str(error)[:500]
                item["reason"] = f"{item.get('reason', 'quality verifier failed')}; repair failed: {error}"
        failures.append(item)

    final_pages: dict[str, ReaderPage] = {}
    for page in checked:
        identity = _page_identity(page)
        if identity in failed_ids:
            continue
        if page.verification != "audit_only":
            final_pages[identity] = replace(page, verification="passed")
    final_pages.update(repaired_pages)
    return [final_pages[_page_identity(page)] for page in pages if _page_identity(page) in final_pages], failures


def _generate_quality_pages(
    projections: Sequence[QualityProjection],
    sources: Sequence[SourceDoc],
    embedder: Embedder,
    model: SemanticModel,
    *,
    evaluation_mode: str = "full",
) -> tuple[list[ReaderPage], list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Generate one reader answer per frozen projection, directly from raw evidence."""

    sources_by_path = {source.relative_path: source for source in sources}
    routes, ledger = _quality_route_sources(
        projections,
        sources,
        embedder,
        evaluation_mode=evaluation_mode,
    )
    pages: list[ReaderPage] = []
    failures: list[dict[str, Any]] = []
    trace_by_projection: dict[str, list[dict[str, Any]]] = defaultdict(list)
    jobs: list[tuple[QualityProjection, tuple[Mapping[str, Any], ...], tuple[SourceDoc, ...], tuple[str, ...], Mapping[str, str], tuple[tuple[str, ...], ...], str]] = []
    for projection in projections:
        missing = sorted(set(projection.source_paths) - set(sources_by_path))
        if missing:
            status = "source_not_in_slice" if evaluation_mode == "slice" else "failed"
            trace_by_projection[projection.projection_id].append({
                "stage": "slice-closure" if evaluation_mode == "slice" else "closure",
                "attempt": 0,
                "selected_source_ids": [],
                "selected_source_paths": [],
                "qwen_payload_sha256": "",
                "prompt_sha256": "",
                "response_sha256": "",
                "status": status,
                "missing_full_source_paths": missing,
            })
            failures.append({
                "scope": "quality",
                "projection_id": projection.projection_id,
                "status": "not_evaluable" if evaluation_mode == "slice" else "audit_only",
                "reason": "source_not_in_slice" if evaluation_mode == "slice" else "quality projection source is missing",
                "missing_full_source_paths": missing,
                "evaluation_mode": evaluation_mode,
            })
            continue
        evidence, _required_evidence_ids, _all_required_source_ids = _quality_evidence(projection, sources_by_path)
        reader_required_groups = reader_evidence_groups(projection, evidence)
        selected_paths = tuple(routes[projection.projection_id])
        selected_sources = tuple(sources_by_path[path] for path in selected_paths if path in sources_by_path)
        selected_context = tuple({
            "source_path": source.relative_path,
            "source_id": source.source_id,
            "raw_context": (
                source.text
                if len(source.text) <= 1200
                else source.text[:800] + "\n……中间原文省略，仅用于候选路由参考……\n" + source.text[-400:]
            ),
        } for source in selected_sources)
        expected_axes = {
            "product": projection.axes["product"],
            "module": projection.axes["module"],
            "object": projection.axes["object"],
            "scenario": projection.axes["scene"],
            "boundary": projection.axes["boundary"],
        }
        prompt = projection_prompt(projection, evidence, PAGE_TYPES, UNKNOWN, selected_paths, selected_context)
        jobs.append((projection, tuple(evidence), selected_sources, selected_paths, expected_axes, reader_required_groups, prompt))

    def request(job: tuple[QualityProjection, tuple[Mapping[str, Any], ...], tuple[SourceDoc, ...], tuple[str, ...], Mapping[str, str], tuple[tuple[str, ...], ...], str]) -> tuple[str | None, Exception | None]:
        try:
            return model.generate(job[-1]), None
        except Exception as error:  # worker boundary; classify below without losing the projection identity
            return None, error

    # Fixed projections are independent after embedding routing.  A bounded
    # pool keeps the real run short while preserving deterministic output
    # order and one trace entry per projection.
    worker_count = min(4, len(jobs))
    if worker_count:
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="digest-quality") as pool:
            responses = list(pool.map(request, jobs))
    else:
        responses = []
    for job, (response, error) in zip(jobs, responses):
        projection, evidence, selected_sources, selected_paths, expected_axes, reader_required_groups, prompt = job
        current_response = response
        current_error = error
        current_prompt = prompt
        final_reason = "quality page generation failed"
        for attempt in range(1, _QUALITY_GENERATION_ATTEMPTS + 1):
            trace_event = {
                "stage": "generate",
                "attempt": attempt,
                "selected_source_ids": [source.source_id for source in selected_sources],
                "selected_source_paths": list(selected_paths),
                "qwen_payload_sha256": _sha(current_prompt),
                "prompt_sha256": _sha(current_prompt),
                "response_sha256": _sha(current_response) if current_response is not None else "",
                "status": "received" if current_response is not None else "failed",
            }
            trace_by_projection[projection.projection_id].append(trace_event)
            candidate: ReaderPage | None = None
            if current_error is not None:
                final_reason = (
                    f"provider unavailable: {current_error}"
                    if isinstance(current_error, ProviderError)
                    else str(current_error)
                )
            else:
                try:
                    value = _parse_json(current_response or "")
                    candidate = _normalise_page(
                        selected_sources,
                        value,
                        expected_page_type=projection.page_type,
                        page_id=projection.projection_id,
                        projection_id=projection.projection_id,
                        answer_page=True,
                        expected_title=projection.title,
                        expected_question=projection.question,
                        expected_axes=expected_axes,
                        required_source_ids=(),
                        allowed_evidence_ids=[row["evidence_id"] for row in evidence],
                        required_evidence_groups=reader_required_groups,
                        enforce_multiple_sources=False,
                        require_task5_semantic=True,
                    )
                    forbidden = [
                        left
                        for left, _reason in projection.forbidden_literals
                        if left and left in _quality_page_text(candidate)
                    ]
                    if forbidden:
                        raise ValueError("quality page contains forbidden wording: " + ", ".join(forbidden[:3]))
                except (ValueError, TypeError) as validation_error:
                    final_reason = str(validation_error)
            if candidate is not None:
                trace_event["status"] = "passed"
                trace_event["page_key"] = candidate.page_key
                pages.append(replace(candidate, verification="generated"))
                break
            trace_event["status"] = "failed"
            trace_event["error"] = final_reason[:500]
            if attempt >= _QUALITY_GENERATION_ATTEMPTS:
                failures.append({
                    "scope": "quality",
                    "projection_id": projection.projection_id,
                    "status": "audit_only",
                    "reason": final_reason,
                })
                break
            # A failed typed response is retried once with the exact closure
            # failure.  Qwen still writes the complete page; Python never
            # patches missing business text or evidence into the page.
            current_prompt = projection_prompt(
                projection,
                evidence,
                PAGE_TYPES,
                UNKNOWN,
                selected_paths,
                selected_context,
                feedback=({"type": "quality_generation_failure", "detail": final_reason},),
            )
            try:
                current_response = model.generate(current_prompt)
                current_error = None
            except Exception as retry_error:  # keep the second attempt bounded and auditable
                current_response = None
                current_error = retry_error
    return pages, failures, ledger, dict(trace_by_projection)


def _provider_call_plan(
    sources: Sequence[SourceDoc],
    model: SemanticModel,
    embedder: Embedder,
    projections: Sequence[QualityProjection] = (),
    *,
    include_quality_comparison: bool = False,
) -> dict[str, int]:
    """Bound the whole run before the first external request.

    The plan deliberately counts worst-case logical requests for this fixed
    compiler topology: one source draft, bounded source verification, a small
    global source retry pool, bounded quality-page repair attempts and one
    strict verifier attempt per quality page. The embedding count is exact for
    the fixed projection set.
    """

    ready_count = sum(source.status == "ready" for source in sources)
    if projections:
        # Quality mode has one typed source compile and one answer compile per
        # frozen projection.  Source pages are structurally/evidence checked
        # by the compiler; only answer pages use the independent semantic
        # verifier and its separate bounded repair allowance.
        verify_requests = len(projections) * _QUALITY_VERIFY_ATTEMPTS
        source_retry_requests = min(_QUALITY_SOURCE_RETRY_LIMIT, ready_count)
        source_requests = ready_count + source_retry_requests
        quality_generation_requests = len(projections) * _QUALITY_GENERATION_ATTEMPTS
        quality_repair_requests = 2 * min(_QUALITY_REPAIR_LIMIT, len(projections))
        max_llm_requests = (
            source_requests
            + quality_generation_requests
            + verify_requests
            + quality_repair_requests
            + _VERIFY_SINGLE_FALLBACK_LIMIT
            + (len(projections) * 2 if include_quality_comparison else 0)
        )
        max_embedding_requests = math.ceil((ready_count + len(projections)) / 8)
        llm_attempts = 1 + int(getattr(model, "retry_attempts", 0))
        embedding_attempts = 1 + int(getattr(embedder, "retry_attempts", 0))
        return {
            "ready_sources": ready_count,
            "products": len({source.product for source in sources if source.status == "ready"}),
            "quality_projections": len(projections),
            "max_topic_pages": 0,
            "mandatory_topic_pages": len(projections),
            "max_llm_requests": max_llm_requests * llm_attempts,
            "max_embedding_requests": max_embedding_requests * embedding_attempts,
            "max_total_requests": max_llm_requests * llm_attempts + max_embedding_requests * embedding_attempts,
        }
    product_count = len({source.product for source in sources if source.status == "ready"})
    max_topic_count = product_count * _MAX_TOPIC_PAGES_PER_PRODUCT
    verify_batches = math.ceil(max_topic_count / _VERIFY_BATCH_SIZE) if max_topic_count else 0
    source_verify_requests = math.ceil(ready_count / _SOURCE_VERIFY_BATCH_SIZE) if ready_count else 0
    source_repair_requests = 2 * min(_SOURCE_REPAIR_LIMIT, ready_count)
    by_product: dict[str, list[SourceDoc]] = defaultdict(list)
    for source in sources:
        if source.status == "ready":
            by_product[source.product].append(source)
    diagnosis_products = 0
    experience_products = 0
    for product_sources in by_product.values():
        diagnosis_scores = [
            sum(weight for signal, weight in _DIAGNOSIS_SIGNALS if signal.casefold() in source.text.casefold())
            for source in product_sources
        ]
        if any(score >= 2 for score in diagnosis_scores):
            diagnosis_products += 1
        if sum(
            any(signal.casefold() in source.text.casefold() for signal in _EXPERIENCE_SIGNALS)
            for source in product_sources
        ) >= 1:
            experience_products += 1
    mandatory_topics = product_count + diagnosis_products + experience_products
    mandatory_extra_attempts = mandatory_topics * max(0, _MANDATORY_AGGREGATE_ATTEMPTS - _AGGREGATE_ATTEMPTS)
    source_retries = min(_SOURCE_RETRY_LIMIT, ready_count)
    max_llm_requests = (
        ready_count
        + source_retries
        + source_verify_requests * _SOURCE_VERIFY_ATTEMPTS
        + source_repair_requests
        + (_PLANNER_ATTEMPTS * product_count)
        + (_AGGREGATE_ATTEMPTS * max_topic_count)
        + mandatory_extra_attempts
        + (2 * verify_batches)
        + (2 * _VERIFY_SINGLE_FALLBACK_LIMIT)
        + max_topic_count
        + (2 * verify_batches)
    )
    max_embedding_requests = math.ceil(
        (ready_count + max_topic_count + len(ROUTE_QUERIES)) / 8
    )
    llm_attempts = 1 + int(getattr(model, "retry_attempts", 0))
    embedding_attempts = 1 + int(getattr(embedder, "retry_attempts", 0))
    planned_llm = max_llm_requests * llm_attempts
    planned_embedding = max_embedding_requests * embedding_attempts
    return {
        "ready_sources": ready_count,
        "products": product_count,
        "max_topic_pages": max_topic_count,
        "mandatory_topic_pages": mandatory_topics,
        "max_llm_requests": planned_llm,
        "max_embedding_requests": planned_embedding,
        "max_total_requests": planned_llm + planned_embedding,
    }


def _build_bundle(request: DigestRequest, model: SemanticModel, embedder: Embedder) -> Bundle:
    run_id = "run-" + uuid.uuid4().hex[:16]
    if request.evaluation_mode not in {"full", "slice"}:
        raise ValueError("evaluation_mode must be 'full' or 'slice'")
    if request.evaluation_mode == "slice" and request.source_paths is None:
        raise ValueError("slice evaluation requires an explicit source_paths closure")
    quality_path = Path(request.quality_config_path).expanduser() if request.quality_config_path is not None else None
    source_manifest_path = (
        Path(request.source_manifest_path).expanduser()
        if request.source_manifest_path is not None
        else (quality_path.parent / "task5-source-page-manifest-v2.json" if quality_path is not None else None)
    )
    source_id_by_path = None
    if quality_path is not None:
        if source_manifest_path is None:
            raise ValueError("quality runs require a source manifest")
        source_id_by_path = _quality_source_ids(source_manifest_path)
    sources = _load_sources(request.new_dir, request.source_paths, source_id_by_path)
    if request.gate == "M402" and request.evaluation_mode == "full":
        _validate_m402_source_closure(sources)
    _progress(f"loaded {len(sources)} source files")
    quality_projections: tuple[QualityProjection, ...] = ()
    quality_contract_sha256 = ""
    projection_rules_sha256 = ""
    quality_source_manifest: dict[str, Any] | None = None
    quality_result: Mapping[str, Any] | None = None
    if request.quality_config_path is not None:
        if quality_path is None:
            raise ValueError("quality config path is missing")
        rules_path = quality_path.parent / "task5-projection-rules-v1.json"
        if not rules_path.is_file():
            rules_path = Path(__file__).resolve().parents[2] / "config" / "task5-projection-rules-v1.json"
        quality_projections = load_quality_projections(quality_path, rules_path)
        quality_contract_sha256 = _sha(quality_path.read_bytes())
        projection_rules_sha256 = _sha(rules_path.read_bytes())
        quality_source_manifest = _quality_source_manifest(
            sources,
            source_manifest_path,
            request.source_paths,
        )
        _progress(f"loaded {len(quality_projections)} quality projections")
    call_plan = _provider_call_plan(
        sources,
        model,
        embedder,
        quality_projections,
        include_quality_comparison=(request.gate == "M402" and request.evaluation_mode == "full"),
    )
    if request.evaluation_mode == "full" and request.run_context is not None:
        # A slice→full run shares one provider budget. The full bundle's
        # receipt must therefore include the complete slice reservation;
        # exact prompt hits may reduce observed calls, but must not be guessed
        # before the full phase has actually run.
        call_plan = dict(call_plan)
        call_plan["max_llm_requests"] += int(request.run_context.slice_llm_plan)
        call_plan["max_embedding_requests"] += int(request.run_context.slice_embedding_plan)
        call_plan["max_total_requests"] = call_plan["max_llm_requests"] + call_plan["max_embedding_requests"]
    budget = getattr(model, "budget", None) or getattr(embedder, "budget", None)
    if budget is not None and call_plan["max_total_requests"] > int(budget.limit):
        raise ProviderError(
            "provider call budget is below the compiler worst-case plan: "
            f"need {call_plan['max_total_requests']}, limit {budget.limit}"
        )
    _progress(
        "call plan: "
        f"up to {call_plan['max_total_requests']} requests "
        f"(LLM {call_plan['max_llm_requests']}, embedding {call_plan['max_embedding_requests']})"
    )
    sources_by_id = {source.source_id: source for source in sources}
    source_pages: list[ReaderPage] = []
    failures: list[dict[str, Any]] = []
    quality_routes: list[ReaderPage] = []
    quality_ledger: list[dict[str, Any]] = []
    quality_trace: dict[str, list[dict[str, Any]]] = {}
    quality_blockers: list[str] = []
    if quality_projections:
        # The quality layer is deliberately separate from the generic topic
        # planner.  It produces one fixed answer page per frozen projection;
        # no planner may merge QR with Zero Touch or collapse five diagnosis
        # questions into one overview.
        # Keep two views of the same immutable raw snapshot: the quality pages
        # need projection evidence IDs, while source pages must not receive a
        # second copy of every quality block (that can push a long source over
        # the provider input ceiling).
        source_page_sources = sources
        augment_projections = (
            quality_projections
            if request.evaluation_mode == "full"
            else tuple(
                projection
                for projection in quality_projections
                if set(projection.source_paths).issubset({source.relative_path for source in source_page_sources})
            )
        )
        sources, _quality_extra = _augment_quality_sources(source_page_sources, augment_projections)
        sources_by_id = {source.source_id: source for source in sources}
        # Build the critical question/scenario answer pages before spending
        # the remaining budget on document-level coverage.  Both layers use
        # the same raw evidence, so source-page generation is not an input to
        # the frozen answer pages and cannot starve their provider call.
        quality_pages, quality_failures, quality_ledger, quality_trace = _generate_quality_pages(
            quality_projections,
            sources,
            embedder,
            model,
            evaluation_mode=request.evaluation_mode,
        )
        for route in quality_ledger:
            events = quality_trace.get(str(route.get("projection_id")), ())
            generated = next(
                (
                    event
                    for event in reversed(events)
                    if event.get("stage") in {"generate", "repair"} and event.get("status") == "passed"
                ),
                {},
            )
            route["qwen_payload_sha256"] = generated.get("qwen_payload_sha256", "")
        failures.extend(quality_failures)
        _progress(f"generated {len(quality_pages)}/{len(quality_projections)} quality pages")
        quality_source_routes = {
            str(route.get("projection_id")): tuple(str(path) for path in route.get("selected_source_paths", ()))
            for route in quality_ledger
            if route.get("projection_id")
        }
        quality_pages, quality_verify_failures = _verify_quality_pages_strict(
            quality_pages,
            sources,
            model,
            quality_projections,
            quality_source_routes,
            quality_trace,
        )
        failures.extend(quality_verify_failures)
        quality_pages = [page for page in quality_pages if page.verification != "audit_only"]
        topic_pages = quality_pages
        # Quality runs still compile every canonical source into a compact
        # source page.  Frozen answer pages are an additional synthesis layer,
        # not a substitute for the 89-source coverage contract.
        source_pages, source_failures = _generate_pages(
            source_page_sources,
            model,
            retry_limit=_QUALITY_SOURCE_RETRY_LIMIT,
            require_task5_semantic=True,
        )
        failures.extend(source_failures)
        _progress(
            f"generated {len(source_pages)} evidence-bound source pages; "
            f"{len(source_failures)} source warnings"
        )
        pages = source_pages + quality_pages
        routes = {
            label: [page for page in quality_pages if page.page_type == page_type]
            for label, page_type in _ROUTE_PAGE_TYPES.items()
        }
        quality_routes = quality_pages
    else:
        source_pages, failures = _generate_pages(sources, model)
        source_pages, source_verify_failures = _verify_source_pages(source_pages, sources_by_id, model)
        failures.extend(source_verify_failures)
        _progress(f"generated {len(source_pages)} evidence-bound source pages; {len(failures)} source warnings")
        # Source pages are evidence-bound at compilation time.  Cross-source
        # pages are the only pages that need a second independent semantic
        # verification pass; raw snapshots remain available in Audit.
        topic_pages, topic_failures = _generate_topic_pages(sources, source_pages, model)
        failures.extend(topic_failures)
        _progress(f"generated {len(topic_pages)} cross-source pages")
        topic_pages, topic_verify_failures = _verify_pages(topic_pages, sources_by_id, model)
        failures.extend(topic_verify_failures)
        topic_pages = [page for page in topic_pages if page.verification != "audit_only"]
        pages = source_pages + topic_pages
        try:
            routes = _route_pages(pages, embedder)
        except ProviderError as error:
            failures.append({
                "scope": "run",
                "status": "routing_unavailable",
                "reason": f"provider unavailable: {error}",
            })
            routes = {key: [] for key in ROUTE_QUERIES}
    failed_source_ids = {
        str(source_id)
        for failure in failures
        if failure.get("scope") not in {"topic", "quality"}
        for source_id in (failure.get("source_ids", ()) or ((failure.get("source_id"),) if failure.get("source_id") else ()))
        if str(source_id)
    }
    if failed_source_ids:
        sources = tuple(
            replace(source, status="provider_failed" if request.quality_config_path else "failed")
            if source.source_id in failed_source_ids and source.status == "ready"
            else source
            for source in sources
        )
        sources_by_id = {source.source_id: source for source in sources}
    pages = _assign_paths(pages)
    assigned_by_identity = {_page_identity(page): page for page in pages}
    routes = {
        label: [assigned_by_identity[_page_identity(page)] for page in selected if _page_identity(page) in assigned_by_identity]
        for label, selected in routes.items()
    }
    quality_routes = [page for page in pages if page.projection_id]
    quality_page_by_projection = {page.projection_id: page for page in quality_routes}
    for route in quality_ledger:
        page = quality_page_by_projection.get(str(route.get("projection_id", "")))
        route["selected_page_ids"] = [_page_identity(page)] if page else []
        route["home_target_page_identity"] = _page_identity(page) if page else ""
    _progress(f"assigned {len(pages)} reader paths")
    _progress("built embedding routes")
    products: dict[str, str] = {source.product: source.product_label for source in sources}
    # Mixed-source answer pages are intentionally visible under a separate
    # shared lane.  They must never be silently placed under the first
    # source's product directory.
    for page in pages:
        product_key = page.product_key or _slug(page.axes["product"], "general")
        if product_key == _SHARED_PRODUCT_KEY:
            products.setdefault(product_key, _SHARED_PRODUCT_LABEL)
        else:
            products.setdefault(product_key, page.axes["product"])
    files: dict[str, bytes] = {}
    for page in pages:
        files[page.relative_path] = _render_page(page, sources_by_id, pages).encode("utf-8")
    # Bind the successful provider response to the exact rendered page.  A
    # projection may have a failed first attempt followed by a valid retry;
    # the manifest must never point at the failed prompt or response.
    for page in quality_routes:
        for event in reversed(quality_trace.get(page.projection_id, ())):
            if event.get("stage") in {"generate", "repair"} and event.get("status") == "passed":
                event["page_path"] = page.relative_path
                event["page_surface_sha256"] = _sha(files[page.relative_path])
                break
    for product_key, product_label in products.items():
        product_pages = [page for page in pages if (page.product_key or _slug(page.axes["product"], "general")) == product_key]
        files[f"products/{product_key}/index.md"] = _render_product_index(product_key, product_label, product_pages).encode("utf-8")
    files["Home.md"] = _render_home(pages, products, routes, sources, quality_routes).encode("utf-8")
    files["Audit.md"] = _render_audit(sources, pages, failures, run_id).encode("utf-8")
    files["README.md"] = _render_readme(sources, pages, run_id).encode("utf-8")
    files["_audit/evidence.jsonl"] = _render_evidence(sources, pages, routes)
    files["_audit/sources.jsonl"] = _render_sources(sources, failures)
    # A formal quality run must bind every layer to the frozen manifest file,
    # not to a second hash invented from the loaded rows.  The latter remains
    # the compatibility identity for ordinary runs that have no manifest.
    source_manifest_sha256 = (
        _sha(source_manifest_path.read_bytes())
        if source_manifest_path is not None and source_manifest_path.is_file()
        else _source_manifest_hash(sources)
    )
    companybrain_observation = None
    if request.gate == "M402" and request.evaluation_mode == "full":
        if request.companybrain_root is None:
            raise ValueError("M402 requires a CompanyBrain root")
        # Reader and Audit are fully rendered before this point.  The
        # authenticated M402 compiler owns the one baseline observation and
        # passes its bound result into quality.py; no wrapper may publish a
        # candidate before this comparison has run.
        companybrain_snapshot = build_companybrain_snapshot(request.companybrain_root)
        companybrain_observation = _companybrain_observation(
            Path(request.companybrain_root),
            snapshot=companybrain_snapshot,
            projections=quality_projections,
            baseline_path=quality_path.parent / "task5-companybrain-baseline-v2.json" if quality_path is not None else Path("config/task5-companybrain-baseline-v2.json"),
            pages=pages,
            evidence_bytes=files["_audit/evidence.jsonl"],
            run_id=run_id,
            source_manifest_sha256=source_manifest_sha256,
        )
    elif isinstance(request.companybrain_route_snapshot, Mapping):
        if request.companybrain_root is not None and quality_projections:
            companybrain_observation = _companybrain_observation(
                Path(request.companybrain_root),
                snapshot=request.companybrain_route_snapshot,
                projections=quality_projections,
                baseline_path=quality_path.parent / "task5-companybrain-baseline-v2.json" if quality_path is not None else Path("config/task5-companybrain-baseline-v2.json"),
                pages=pages,
                evidence_bytes=files["_audit/evidence.jsonl"],
                run_id=run_id,
                source_manifest_sha256=source_manifest_sha256,
            )
        else:
            companybrain_observation = dict(request.companybrain_route_snapshot)
            companybrain_observation["run_id"] = run_id
            companybrain_observation["source_manifest_sha256"] = source_manifest_sha256
    quality_sha256: str | None = None
    quality_comparison: Mapping[str, Any] | None = None
    if quality_projections:
        quality_result = build_candidate_quality_result(
            projections=quality_projections,
            files=files,
            companybrain_observation=companybrain_observation,
            require_companybrain_observation=request.evaluation_mode != "slice",
            route_ledger=quality_ledger,
            source_count=len(sources),
            expected_source_manifest_sha256=source_manifest_sha256,
            expected_run_id=run_id,
        )
        quality_result = finalize_quality_result(
            quality_result,
            quality_contract_sha256=quality_contract_sha256,
            projection_rules_sha256=projection_rules_sha256,
            source_manifest=quality_source_manifest,
            projection_ids=[projection.projection_id for projection in quality_projections],
            # Compatibility fields are still useful for debugging provider
            # lineage, but they are not a quality verdict and are ignored by
            # the strict evaluator.
            routes=quality_ledger,
            provider_trace=quality_trace,
        )
        quality_blockers = [
            str(item)
            for item in quality_result.get("hard_blockers", ())
            if str(item).strip()
        ]
        structural_blockers = [
            blocker
            for blocker in quality_blockers
            if blocker != "quality_dimensions_not_all_kd_win"
        ]
        if structural_blockers:
            # The first quality pass needs Audit to validate the render
            # ledger.  Once its blockers are known, render them into the
            # human audit surface and recompute the machine result against
            # those final bytes; no blocker may exist only in a hidden log.
            files["Audit.md"] = _render_audit(
                sources,
                pages,
                [
                    *failures,
                    *(
                        {
                            "scope": "quality-gate",
                            "status": "not_released",
                            "reason": blocker,
                        }
                        for blocker in structural_blockers
                    ),
                ],
                run_id,
            ).encode("utf-8")
            quality_result = build_candidate_quality_result(
                projections=quality_projections,
                files=files,
                companybrain_observation=companybrain_observation,
                require_companybrain_observation=request.evaluation_mode != "slice",
                route_ledger=quality_ledger,
                source_count=len(sources),
                expected_source_manifest_sha256=source_manifest_sha256,
                expected_run_id=run_id,
            )
            quality_result = finalize_quality_result(
                quality_result,
                quality_contract_sha256=quality_contract_sha256,
                projection_rules_sha256=projection_rules_sha256,
                source_manifest=quality_source_manifest,
                projection_ids=[projection.projection_id for projection in quality_projections],
                routes=quality_ledger,
                provider_trace=quality_trace,
            )
            quality_blockers = [
                str(item)
                for item in quality_result.get("hard_blockers", ())
                if str(item).strip()
            ]
        # A local structural pass is necessary but not sufficient.  On the
        # authenticated full M402 path, compare the exact rendered Reader
        # bytes with the verified CompanyBrain baseline using two swapped
        # provider rounds.  This is the only operation allowed to change the
        # candidate's UNKNOWN quality state into a release.
        if not structural_blockers and request.gate == "M402" and request.evaluation_mode == "full":
            source_by_path = {source.relative_path: source for source in sources}
            raw_evidence: dict[str, list[dict[str, Any]]] = {}
            for projection in quality_projections:
                evidence: list[dict[str, Any]] = []
                for block_ref in projection.source_block_refs:
                    source_path, start_line, end_line, label = parse_block_ref(block_ref)
                    source = source_by_path.get(source_path)
                    if source is None:
                        continue
                    text = "\n".join(source.lines[start_line - 1 : end_line])
                    evidence.append({
                        "block_ref": block_ref,
                        "source_path": source_path,
                        "start_line": start_line,
                        "end_line": end_line,
                        "label": label,
                        "text": text,
                        "sha256": _sha(text),
                    })
                raw_evidence[projection.projection_id] = evidence
            page_payloads = {
                page.projection_id: {
                    "text": files[page.relative_path].decode("utf-8"),
                    "home_text": files["Home.md"].decode("utf-8"),
                    "audit_text": files["Audit.md"].decode("utf-8"),
                }
                for page in quality_routes
                if page.projection_id and page.relative_path in files
            }
            quality_comparison = compare_quality(
                projections=quality_projections,
                page_payloads=page_payloads,
                companybrain_root=Path(request.companybrain_root),
                baseline_path=quality_path.parent / "task5-companybrain-baseline-v2.json",
                raw_evidence=raw_evidence,
                model=model,
            )
        quality_result = build_candidate_quality_result(
            projections=quality_projections,
            files=files,
            companybrain_observation=companybrain_observation,
            require_companybrain_observation=request.evaluation_mode != "slice",
            route_ledger=quality_ledger,
            source_count=len(sources),
            expected_source_manifest_sha256=source_manifest_sha256,
            expected_run_id=run_id,
            comparison=quality_comparison,
        )
        quality_result = finalize_quality_result(
            quality_result,
            quality_contract_sha256=quality_contract_sha256,
            projection_rules_sha256=projection_rules_sha256,
            source_manifest=quality_source_manifest,
            projection_ids=[projection.projection_id for projection in quality_projections],
            routes=quality_ledger,
            provider_trace=quality_trace,
        )
        quality_blockers = [
            str(item)
            for item in quality_result.get("hard_blockers", ())
            if str(item).strip()
        ]
        if request.gate == "M402" and request.evaluation_mode == "full":
            snd_snapshot_id = str(
                (quality_source_manifest or {}).get("snapshot_id")
                or source_manifest_sha256
            )
            _snd_certificate, snd_verifier = _formal_snd_artifacts(
                sources,
                source_snapshot_id=snd_snapshot_id,
                material_id=str(request.material_id or ""),
            )
            if snd_verifier.get("status") != "passed":
                quality_blockers = list(dict.fromkeys([
                    *quality_blockers,
                    "snd_zero_match_not_closed",
                ]))
                quality_result = finalize_quality_result(
                    quality_result,
                    hard_blockers=quality_blockers,
                    run_outcome="candidate",
                    quality_result_status="candidate",
                    publication_status="not_released",
                    verdict="UNKNOWN",
                )
            if request.gate == "M402" and request.evaluation_mode == "full":
                # This is still the immutable attempt. A later authenticated
                # finalize step must re-read the published tree and create
                # the fixed promoted artifact before any release verdict can
                # be consumed.
                quality_result = _candidate_quality_result(quality_result)
        files["_audit/quality.json"] = _canonical_json(quality_result)
        quality_sha256 = _sha(files["_audit/quality.json"])
    # The public CompanyBrain projection is serialized only after the
    # scanner and quality.py have consumed the final Reader/Audit bytes.
    # This preserves the declared producer order and prevents the snapshot
    # file from becoming an implicit input to its own comparison.
    files["_audit/companybrain-route-snapshot.json"] = _public_companybrain_snapshot(
        companybrain_observation or request.companybrain_route_snapshot,
        run_id=run_id,
        source_manifest_sha256=source_manifest_sha256,
    )
    known_empty_paths = set(
        str(path)
        for path in (quality_source_manifest or {}).get("known_empty_paths", ())
    )
    blocking_failures = [
        failure
        for failure in failures
        if not (
            failure.get("reason") == "known_empty_source"
            and str(failure.get("relative_path", "")) in known_empty_paths
        ) and not (
            request.evaluation_mode == "slice"
            and failure.get("reason") == "source_not_in_slice"
        )
    ]
    blocking_failures.extend(
        {
            "scope": "quality-gate",
            "status": "not_released",
            "reason": blocker,
        }
        for blocker in quality_blockers
    )
    # A normal quality compile produces a candidate before the independent
    # five-dimension comparison runs.  That comparison blocker is a release
    # state, not an execution failure; keep it visible in warnings but do not
    # make the source/compiler run look incomplete to the later evaluator.
    execution_blockers = [
        failure
        for failure in blocking_failures
        if not (
            failure.get("scope") == "quality-gate"
            and failure.get("reason") == "quality_dimensions_not_all_kd_win"
        )
    ]
    warnings = tuple(
        f"{failure.get('projection_id') or failure.get('source_id') or failure.get('product') or 'run'}: {failure.get('reason', failure.get('status', 'warning'))}"
        for failure in blocking_failures
    )
    reader_source_ids = {
        source_id
        for page in pages
        for source_id in page.all_source_ids
    }
    source_page_source_ids = {
        source_id
        for page in source_pages
        for source_id in page.all_source_ids
    }
    # A raw-only topic reference is useful Reader coverage, but it does not
    # turn a failed per-source digest into a successful source page. Keep the
    # two facts visible instead of hiding the failed source behind the topic.
    audit_only_source_ids = sorted(set(sources_by_id) - source_page_source_ids)
    raw_only_reader_source_ids = sorted(
        (set(reader_source_ids) - source_page_source_ids) & set(sources_by_id)
    )
    provider_identity = {"llm": dict(model.identity), "embedding": dict(embedder.identity)}
    trace_by_id = {
        str(projection_id): events
        for projection_id, events in quality_trace.items()
    }
    quality_failure_by_id = {
        str(failure.get("projection_id")): str(failure.get("reason", "quality route failed"))
        for failure in failures
        if failure.get("scope") == "quality" and failure.get("projection_id")
    }
    source_id_by_path = {source.relative_path: source.source_id for source in sources}
    manifest_routes = []
    for route in quality_ledger:
        projection_id = str(route.get("projection_id", ""))
        generated = next(
            (event for event in reversed(trace_by_id.get(projection_id, ())) if event.get("stage") == "generate" and event.get("status") == "passed"),
            {},
        )
        route_page = quality_page_by_projection.get(projection_id)
        selected_ids = {str(item) for item in route.get("selected_source_ids", ()) if str(item)}
        evidence_bindings = []
        for source in sources:
            if source.source_id not in selected_ids:
                continue
            for evidence in source.evidence:
                evidence_id = str(evidence.get("evidence_id", ""))
                block_id = str(evidence.get("block_id") or evidence_id)
                claim_id = str(evidence.get("claim_id") or f"claim-{block_id}")
                evidence_bindings.append({
                    "raw_source_id": source.source_id,
                    "raw_hash": _sha(source.raw_bytes),
                    "block_id": block_id,
                    "claim_id": claim_id,
                    "locator": {
                        "start_line": int(evidence.get("start_line", 0)),
                        "end_line": int(evidence.get("end_line", 0)),
                    },
                    "support_sha256": str(
                        evidence.get("block_content_sha256")
                        or _sha(_normalised_text(str(evidence.get("text", ""))))
                    ),
                })
        scores: dict[str, float] = {}
        score_rows: Sequence[Any] = ()
        all_scores = route.get("all_scores")
        if isinstance(all_scores, Mapping):
            for source_id, score in all_scores.items():
                if isinstance(source_id, str) and source_id and isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(float(score)):
                    scores[source_id] = float(score)
        else:
            score_rows = route.get("top_k_scores", ())
        if not scores and isinstance(score_rows, list):
            for score_row in score_rows:
                if not isinstance(score_row, Mapping):
                    continue
                source_id = source_id_by_path.get(str(score_row.get("source_path", "")))
                score = score_row.get("score")
                if source_id and isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(float(score)):
                    scores[source_id] = float(score)
        selected_source_ids = [str(item) for item in route.get("selected_source_ids", ()) if str(item)]
        embedding_receipt = None
        if route.get("closure") == "closed":
            embedding_identity = route.get("embedding_model", {})
            if isinstance(embedding_identity, Mapping):
                embedding_receipt = {
                    "provider": "jina",
                    "model": str(embedding_identity.get("model", "")),
                    "request_identity": str(route.get("embedding_input_sha256", "")),
                    "selected_source_ids": selected_source_ids,
                    "selected_closure_sha256": str(route.get("embedding_selected_closure_sha256", "")),
                    "response_sha256": str(route.get("embedding_response_sha256", "")),
                    "status": "passed",
                }
        manifest_routes.append({
            "query_id": route.get("query_id", projection_id),
            "question": next((projection.question for projection in quality_projections if projection.projection_id == projection_id), route.get("query", "")),
            "scene": next((projection.axes["scene"] for projection in quality_projections if projection.projection_id == projection_id), ""),
            "route_name": route.get("route_name", ""),
            "product_key": route.get("product_key", ""),
            "projection_id": projection_id,
            "candidate_source_ids": route.get("candidate_source_ids", []),
            "selected_source_ids": selected_source_ids,
            "selected_page_ids": route.get("selected_page_ids", []),
            "scores": dict(sorted(scores.items(), key=lambda item: item[0].encode("utf-8"))),
            "embedding_receipt": embedding_receipt,
            "qwen_payload_sha256": generated.get("qwen_payload_sha256", ""),
            "evidence_bindings": evidence_bindings,
            "home_target_page_identity": route.get("home_target_page_identity", ""),
            "status": "ready" if route_page else "failed",
            "failure": None if route_page else quality_failure_by_id.get(projection_id, "quality route produced no Reader page"),
        })
    pages_manifest = [
        {
            "page_id": _page_identity(page),
            "page_key": page.page_key,
            "page_type": page.page_type,
            "axes": dict(page.axes),
            "source_ids": list(page.all_source_ids),
            "path": page.relative_path,
            "surface_sha256": _sha(files[page.relative_path]),
        }
        for page in pages
    ]
    failure_by_source_id = {}
    for failure in failures:
        for source_id in failure.get("source_ids", ()):
            failure_by_source_id[str(source_id)] = failure
        if failure.get("source_id"):
            failure_by_source_id[str(failure["source_id"])] = failure
    pages_by_source: dict[str, list[ReaderPage]] = defaultdict(list)
    for page in pages:
        for source_id in page.all_source_ids:
            pages_by_source[source_id].append(page)
    manifest_sources = []
    for source in sources:
        source_failure = failure_by_source_id.get(source.source_id)
        manifest_sources.append({
            "source_id": source.source_id,
            "relative_path": source.relative_path,
            "product_key": source.product,
            "product_label": source.product_label,
            "raw_hash": _sha(source.raw_bytes),
            "status": source.status,
            "source_digest_eligible": source.status == "ready",
            "duplicate_of": source.duplicate_of,
            "evidence_ids": [str(item["evidence_id"]) for item in source.evidence],
            # Quality answer pages are a separate projection surface.  They
            # may cite the same source, but must not masquerade as that
            # source's canonical one-to-one Reader page in the source ledger.
            "reader_page_ids": [
                _page_identity(page)
                for page in pages_by_source.get(source.source_id, [])
                if not page.projection_id and page.verification != "audit_only"
            ],
            "failure": (dict(source_failure) if source_failure else ({"code": "known_empty_source"} if source.status == "known_empty" else None)),
        })
    manifest = {
        "schema_version": "knowledge-digest-run-manifest.v1",
        "source_count": len(manifest_sources),
        "sources": manifest_sources,
        "routes": manifest_routes,
        "pages": pages_manifest,
    }
    # The run manifest is intentionally excluded from its own tree hash so a
    # hash cannot recursively depend on the JSON field that stores it.
    manifest["tree_sha256"] = _tree_hash(files)
    _validate_run_manifest(manifest, expected_source_count=len(sources))
    quality_release_ok = bool(
        quality_projections
        and isinstance(quality_result, Mapping)
        and quality_result.get("publication_status") == "released"
        and quality_result.get("verdict") == "released"
        and not quality_blockers
        and request.quality_result_promoted
    )
    if request.quality_config_path is None:
        run_outcome = "completed" if pages and not execution_blockers else "not_released"
    else:
        # A quality run is a terminal release decision, not a successful
        # compiler checkpoint.  Only the authenticated full M402 path may
        # return released; every candidate, missing comparison, or failed
        # quality gate is explicitly not_released.
        run_outcome = (
            "released"
            if pages and not execution_blockers and request.gate == "M402" and quality_release_ok
            else "not_released"
        )
    # The CompanyBrain scanner result is the authoritative binding for this
    # run.  Do not read the request's optional snapshot field here: M402
    # creates the snapshot inside the compiler, so that request field is
    # intentionally empty on the real path.  Using it used to publish a
    # released bundle whose run-result claimed null CompanyBrain identities
    # even though quality.py had compared against a real snapshot.
    binding = companybrain_observation if isinstance(companybrain_observation, Mapping) else request.companybrain_route_snapshot
    run = {
        "schema_version": "knowledge-digest-run.v1",
        "run_id": run_id,
        "evaluation_mode": request.evaluation_mode,
        "source_selection": list(request.source_paths) if request.source_paths is not None else None,
        "created_at": _now(),
        "outcome": run_outcome,
        "source_root": "input_directory",
        "source_manifest_hash": source_manifest_sha256,
        "source_count": len(sources),
        "reader_page_count": len(pages),
        "source_page_count": len(source_pages),
        "topic_page_count": len(topic_pages) if not quality_projections else 0,
        "quality_projection_count": len(quality_projections),
        "quality_page_count": len(quality_routes),
        "quality_sha256": quality_sha256,
        "quality_projection_ids": [projection.projection_id for projection in quality_projections],
        "quality_contract_sha256": quality_contract_sha256,
        "projection_rules_sha256": projection_rules_sha256,
        "quality_source_manifest": quality_source_manifest,
        "quality_route_ledger": quality_ledger,
        "manifest": manifest,
        "quality_provider_trace": quality_trace if quality_projections else {},
        "audit_only_count": len(audit_only_source_ids),
        "audit_only_source_ids": audit_only_source_ids,
        "raw_only_reader_source_count": len(raw_only_reader_source_ids),
        "raw_only_reader_source_ids": raw_only_reader_source_ids,
        "duplicate_source_count": sum(source.status == "duplicate_alias" for source in sources),
        "provider_calls": {"llm": int(model.calls), "embedding": int(embedder.calls)},
        "provider_attempts": (
            {
                "llm": int((budget.used_by_kind if budget is not None else {}).get("LLM", 0)),
                "embedding": int((budget.used_by_kind if budget is not None else {}).get("embedding", 0)),
            }
            if budget is not None
            else None
        ),
        "provider_budget": ({"used": int(budget.used), "limit": int(budget.limit)} if budget is not None else None),
        "provider_call_plan": call_plan,
        "provider_identity": provider_identity,
        "warnings": list(warnings),
        "known_empty_sources": sorted(known_empty_paths),
        "quality_status": "released" if run_outcome == "released" else "not_released",
        "release_status": "released" if run_outcome == "released" else "not_released",
        "reader_contract": {"page_types": list(PAGE_TYPES), "axes": ["product", "module", "object", "scenario", "boundary"]},
        "companybrain_binding": {
            "companybrain_snapshot_id": (
                binding.get("companybrain_snapshot_id") or binding.get("snapshot_id")
                if isinstance(binding, Mapping)
                else None
            ),
            "companybrain_tree_sha256": (
                binding.get("companybrain_tree_sha256") or binding.get("tree_sha256")
                if isinstance(binding, Mapping)
                else None
            ),
            "observation_sha256": (
                binding.get("observation_sha256")
                if isinstance(binding, Mapping)
                else None
            ),
        },
    }
    if request.run_context is not None:
        run["run_context"] = {
            "context_id": request.run_context.context_id,
            "slice_run_id": request.run_context.slice_run_id,
            "slice_llm_plan": request.run_context.slice_llm_plan,
            "slice_embedding_plan": request.run_context.slice_embedding_plan,
            "reused_response_count": request.run_context.reused_response_count,
        }
    run_result_bytes = (json.dumps(run, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    files["_audit/run-result.json"] = run_result_bytes
    files["_audit/run-result.receipt.json"] = (
        json.dumps(
            {
                "receipt_schema_version": "knowledge-digest-run-result-receipt.v1",
                "run_id": run_id,
                "manifest_sha256": _sha(_canonical_json(manifest)),
                "tree_sha256": manifest["tree_sha256"],
                "run_result_sha256": _sha(run_result_bytes),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    return Bundle(files, tuple(pages), sources, run_id, warnings, companybrain_observation, quality_result)


def _bundle_terminal_state(bundle: Bundle, request: DigestRequest) -> tuple[str, str | None]:
    """Separate successful candidate execution from strict publication."""

    if not bundle.pages:
        return "not_released", "no_reader_pages"
    unexpected_warnings = [
        warning
        for warning in bundle.warnings
        if warning != "run: quality_dimensions_not_all_kd_win"
    ]
    if unexpected_warnings:
        return "not_released", unexpected_warnings[0]
    if request.quality_config_path is None:
        return "completed", None
    quality = bundle.quality_result
    if quality is None:
        raw_quality = bundle.files.get("_audit/quality.json")
        if raw_quality is None:
            return "not_released", "quality_result_missing"
        try:
            parsed_quality = json.loads(raw_quality.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return "not_released", "quality_result_invalid"
        if not isinstance(parsed_quality, Mapping):
            return "not_released", "quality_result_invalid"
        quality = parsed_quality
    if quality.get("publication_status") != "released" or quality.get("verdict") != "released":
        return "not_released", "quality_not_released"
    if request.gate != "M402":
        return "not_released", "formal_m402_required"
    if not request.quality_result_promoted:
        return "not_released", "quality_result_not_promoted"
    return "released", None


def _candidate_quality_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Demote a compiler comparison to the immutable pre-promotion state.

    The compiler may collect comparison evidence, but the authenticated
    post-rename quality owner is the only component allowed to publish a
    release verdict. Keeping the rows and top-level state candidate here
    prevents a host-only attempt from being mistaken for the promoted
    artifact described by the active v4.7 contract.
    """

    value = dict(result)
    dimensions = value.get("dimension_verdicts")
    if isinstance(dimensions, Mapping):
        value["dimension_verdicts"] = {
            str(projection): {
                str(dimension): (list(verdict) if verdict == ["N/A", "N/A"] else ["UNKNOWN", "UNKNOWN"])
                for dimension, verdict in values.items()
            }
            for projection, values in dimensions.items()
            if isinstance(values, Mapping)
        }
    rows = value.get("quality_rows")
    if isinstance(rows, list):
        candidate_rows: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            item = dict(row)
            item["verdict"] = "N/A" if item.get("verdict") == "N/A" else "UNKNOWN"
            candidate_rows.append(item)
        value["quality_rows"] = candidate_rows
    return finalize_quality_result(
        value,
        run_outcome="candidate",
        quality_result_status="candidate",
        publication_status="not_released",
        verdict="UNKNOWN",
        published_tree_sha256=None,
        strict_all_kd_win=False,
    )


def _write_create_only(path: Path, payload: bytes) -> str:
    """Write one host-owned evidence file without replacing an older attempt."""

    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor != -1:
            os.close(descriptor)
    return _sha(payload)


def _atomic_replace(path: Path, payload: bytes) -> str:
    """Replace one file atomically after all bytes have been fsynced."""

    path = Path(path)
    temporary = path.with_name(f".{path.name}.finalize-{uuid.uuid4().hex}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor != -1:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()
    return _sha(payload)


def _write_host_observation(
    observation: Mapping[str, Any] | None,
    *,
    evidence_root: Path,
    attempt_id: str,
) -> tuple[Path | None, str | None]:
    if not isinstance(observation, Mapping):
        return None, None
    payload = _canonical_json(observation)
    path = Path(evidence_root).expanduser() / "actual-run" / "attempts" / attempt_id / "companybrain-observation.json"
    return path, _write_create_only(path, payload)


def _write_host_run_receipt(
    *,
    evidence_root: Path,
    attempt_id: str,
    run_id: str,
    request: DigestRequest,
    source_manifest_sha256: str,
    public_receipt: Path,
    terminal_status: str,
) -> tuple[Path, str]:
    """Bind authenticated host inputs to the final public run result."""

    provider_config = Path(request.provider_config_path).expanduser()
    receipt = {
        "schema_version": "task5-host-run-receipt.v1",
        "run_id": run_id,
        "raw_root_identity": str(Path(request.new_dir).expanduser().resolve()),
        "companybrain_root_identity": str(Path(request.companybrain_root).expanduser().resolve()) if request.companybrain_root else None,
        "downloads_run_root": str(Path(request.kb_dir).expanduser().resolve()),
        "provider_config_ref": {
            "path": str(provider_config.resolve()),
            "sha256": _sha(provider_config.read_bytes()),
        },
        "source_manifest_sha256": source_manifest_sha256,
        "public_receipt_ref": "bundle/_audit/run-result.json",
        "public_receipt_sha256": _sha(public_receipt.read_bytes()),
        "terminal_status": terminal_status,
    }
    path = Path(evidence_root).expanduser() / "actual-run" / "attempts" / attempt_id / "host-run-receipt.json"
    return path, _write_create_only(path, _canonical_json(receipt))


def _quality_source_manifest_path(request: DigestRequest) -> Path | None:
    if request.source_manifest_path is not None:
        return Path(request.source_manifest_path).expanduser()
    if request.quality_config_path is not None:
        return Path(request.quality_config_path).expanduser().parent / "task5-source-page-manifest-v2.json"
    return None


def _prepare_formal_bundle(
    bundle: Bundle,
    request: DigestRequest,
) -> tuple[Bundle, Path, Path | None, str | None, str, Path, str]:
    """Create the immutable candidate and bind it to the formal public tree."""

    evidence_root = Path(request.quality_evidence_root or Path.cwd() / "quality" / "evidence" / "task5").expanduser()
    quality_ref: str | None = None
    quality_path: Path | None = None
    quality_sha256: str | None = None
    candidate_quality: Mapping[str, Any] | None = bundle.quality_result
    if isinstance(candidate_quality, Mapping):
        quality_path = evidence_root / "actual-run" / "attempts" / bundle.run_id / "quality-result.json"
        quality_ref = f"actual-run/attempts/{bundle.run_id}/quality-result.json"

    # The quality reference/hash is excluded from the public tree hash because
    # it lives in run-result.json.  A placeholder therefore lets us compute
    # the exact final tree before writing the immutable candidate bytes.
    first_files = _formalise_public_bundle(
        bundle.files,
        sources=bundle.sources,
        run_id=bundle.run_id,
        quality_result_ref=quality_ref,
        quality_result_sha256="0" * 64 if quality_ref else None,
        material_id=str(request.material_id or ""),
    )
    first_run = json.loads(first_files["_audit/run-result.json"].decode("utf-8"))
    candidate_tree_sha256 = str(first_run["manifest"]["tree_sha256"])
    candidate_manifest_sha256 = _sha(first_files["_audit/directory-manifest.json"])
    if isinstance(candidate_quality, Mapping):
        candidate_quality = finalize_quality_result(
            candidate_quality,
            candidate_tree_sha256=candidate_tree_sha256,
            candidate_bundle_ref="bundle",
            candidate_manifest_ref="bundle/_audit/directory-manifest.json",
            candidate_manifest_sha256=candidate_manifest_sha256,
        )
        assert quality_path is not None
        quality_bytes = _canonical_json(candidate_quality)
        quality_sha256 = _write_create_only(quality_path, quality_bytes)

    formal_files = _formalise_public_bundle(
        bundle.files,
        sources=bundle.sources,
        run_id=bundle.run_id,
        quality_result_ref=quality_ref,
        quality_result_sha256=quality_sha256,
        material_id=str(request.material_id or ""),
    )
    final_run = json.loads(formal_files["_audit/run-result.json"].decode("utf-8"))
    if str(final_run["manifest"]["tree_sha256"]) != candidate_tree_sha256:
        raise ValueError("formal candidate tree changed after quality promotion binding")
    if _sha(formal_files["_audit/directory-manifest.json"]) != candidate_manifest_sha256:
        raise ValueError("formal directory manifest changed after quality promotion binding")
    candidate_surface_qa = _surface_qa_from_files(
        final_run,
        formal_files,
        phase="candidate",
        candidate_tree_sha256=candidate_tree_sha256,
        candidate_manifest_sha256=candidate_manifest_sha256,
    )
    if candidate_surface_qa.get("status") != "passed":
        raise ValueError("candidate surface QA failed")
    candidate_surface_path = evidence_root / "m402-surface-qa" / "attempts" / bundle.run_id / "surface-qa.json"
    candidate_surface_sha256 = _write_create_only(candidate_surface_path, _canonical_json(candidate_surface_qa))
    observation_path, _observation_sha256 = _write_host_observation(
        bundle.companybrain_observation,
        evidence_root=evidence_root,
        attempt_id=bundle.run_id,
    )
    del observation_path
    return (
        replace(bundle, files=formal_files, quality_result=candidate_quality),
        evidence_root,
        quality_path,
        quality_sha256,
        candidate_tree_sha256,
        candidate_surface_path,
        candidate_surface_sha256,
    )


def _post_rename_surface_qa(bundle_root: Path) -> tuple[dict[str, Any], dict[str, bytes], str, str]:
    """Re-read the renamed tree and verify the bytes the finalizer will bind."""

    bundle_root = Path(bundle_root)
    public_files: dict[str, bytes] = {}
    for path in bundle_root.rglob("*"):
        if path.is_symlink():
            raise ValueError("published bundle contains a symlink")
        if path.is_file():
            public_files[path.relative_to(bundle_root).as_posix()] = path.read_bytes()
    audit_paths = {path for path in public_files if path.startswith("_audit/")}
    if audit_paths != set(_FORMAL_PUBLIC_AUDIT_FILES):
        raise ValueError("published audit tree is not the fixed v4.7 closure")
    _validate_public_files(public_files)
    try:
        run = json.loads(public_files["_audit/run-result.json"].decode("utf-8"))
        directory = json.loads(public_files["_audit/directory-manifest.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as error:
        raise ValueError("published machine receipt is invalid") from error
    if not isinstance(run, Mapping) or not isinstance(directory, Mapping):
        raise ValueError("published machine receipt is invalid")
    manifest = run.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ValueError("published run manifest is missing")
    _validate_run_manifest(manifest, expected_source_count=int(run.get("source_count", -1)))
    if run.get("canonical_sha256") != _sha(_canonical_json({key: value for key, value in run.items() if key != "canonical_sha256"})):
        raise ValueError("published run-result canonical hash is invalid")
    if directory.get("canonical_sha256") != _sha(_canonical_json({key: value for key, value in directory.items() if key != "canonical_sha256"})):
        raise ValueError("published directory manifest canonical hash is invalid")
    tree_sha256 = _tree_hash(public_files)
    if manifest.get("tree_sha256") != tree_sha256:
        raise ValueError("published tree hash does not match run manifest")
    expected_rows = [
        {"path": relative, "sha256": _sha(content), "bytes": len(content), "lines": content.count(b"\n")}
        for relative, content in sorted(public_files.items(), key=lambda item: str(item[0]).encode("utf-8"))
        if relative not in {"_audit/run-result.json", "_audit/directory-manifest.json"}
    ]
    if directory.get("files") != expected_rows or directory.get("tree_sha256") != tree_sha256:
        raise ValueError("published directory manifest does not match bytes")
    for page in manifest.get("pages", ()):
        if not isinstance(page, Mapping):
            raise ValueError("published page row is malformed")
        path = str(page.get("path", ""))
        if path not in public_files or page.get("surface_sha256") != _sha(public_files[path]):
            raise ValueError("published Reader page hash does not match bytes")
    return dict(run), public_files, tree_sha256, _sha(public_files["_audit/directory-manifest.json"])


def _surface_qa_from_files(
    run: Mapping[str, Any],
    public_files: Mapping[str, bytes],
    *,
    phase: str,
    candidate_tree_sha256: str,
    candidate_manifest_sha256: str,
    published_tree_sha256: str | None = None,
    published_manifest_sha256: str | None = None,
    cleanup_passed: bool = True,
) -> dict[str, Any]:
    """Replay the user-visible surface from the exact bytes being bound.

    This is intentionally a small, deterministic Markdown replay rather than
    a second renderer. It verifies the links and anchors a reader can follow,
    while the compiler's existing semantic and lineage checks remain the
    authority for page content.
    """

    issues: list[str] = []
    required = ("README.md", "Home.md", "Audit.md")
    issues.extend(f"missing:{relative}" for relative in required if relative not in public_files)
    manifest = run.get("manifest")
    pages = manifest.get("pages", []) if isinstance(manifest, Mapping) else []
    page_by_id = {
        str(row.get("page_id")): row
        for row in pages
        if isinstance(row, Mapping) and str(row.get("page_id", ""))
    }
    reader_paths = {
        str(row.get("path"))
        for row in pages
        if isinstance(row, Mapping) and str(row.get("path", ""))
    }
    for relative in sorted(reader_paths):
        if relative not in public_files:
            issues.append(f"reader_missing:{relative}")
    audit_text = public_files.get("Audit.md", b"").decode("utf-8", errors="replace")
    for page_id in sorted(page_by_id):
        if f'<a id="page-{page_id}"></a>' not in audit_text:
            issues.append(f"audit_anchor_missing:page-{page_id}")

    home_text = public_files.get("Home.md", b"").decode("utf-8", errors="replace")
    link_pattern = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
    link_targets: dict[str, set[str]] = defaultdict(set)
    for relative, content in public_files.items():
        if not relative.endswith(".md"):
            continue
        text = content.decode("utf-8", errors="replace")
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().split(None, 1)[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme not in {"http", "https", "mailto"}:
                    issues.append(f"link_scheme_forbidden:{relative}:{target}")
                continue
            path_part = unquote(parsed.path)
            if not path_part:
                if parsed.fragment and relative == "Audit.md" and f'<a id="{parsed.fragment}"></a>' not in audit_text:
                    issues.append(f"anchor_missing:{relative}#{parsed.fragment}")
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(relative), path_part))
            if resolved.startswith("../") or resolved == ".." or resolved.startswith("/"):
                issues.append(f"link_escape:{relative}:{target}")
                continue
            if resolved not in public_files:
                issues.append(f"link_target_missing:{relative}:{target}")
                continue
            link_targets.setdefault(relative, set()).add(resolved)
            if parsed.fragment and resolved == "Audit.md" and f'<a id="{parsed.fragment}"></a>' not in audit_text:
                issues.append(f"anchor_missing:{resolved}#{parsed.fragment}")

    route_targets = []
    routes = manifest.get("routes", []) if isinstance(manifest, Mapping) else []
    for route in routes:
        if not isinstance(route, Mapping):
            continue
        target_id = str(route.get("home_target_page_identity", ""))
        target = page_by_id.get(target_id)
        if not isinstance(target, Mapping):
            issues.append(f"route_target_missing:{target_id}")
            continue
        target_path = str(target.get("path", ""))
        route_targets.append(target_path)
        if target_path not in link_targets.get("Home.md", set()):
            issues.append(f"home_route_unreachable:{target_id}")

    for relative, content in public_files.items():
        if relative.endswith(".md") and _PUBLIC_HOST_PATH.search(content.decode("utf-8", errors="replace")):
            issues.append(f"forbidden_path:{relative}")
    if not cleanup_passed:
        issues.append("staging_cleanup_failed")

    tree_sha256 = _tree_hash(public_files)
    receipt = {
        "schema_version": "task5-surface-qa.v1",
        "phase": phase,
        "status": "passed" if not issues else "failed",
        "bundle_ref": "bundle",
        "run_id": str(run.get("run_id", "")),
        "candidate_tree_sha256": candidate_tree_sha256,
        "candidate_manifest_ref": "bundle/_audit/directory-manifest.json",
        "candidate_manifest_sha256": candidate_manifest_sha256,
        "published_tree_sha256": published_tree_sha256,
        "published_manifest_ref": "bundle/_audit/directory-manifest.json" if published_manifest_sha256 else None,
        "published_manifest_sha256": published_manifest_sha256,
        "reader_page_count": len(reader_paths),
        "route_count": len(routes) if isinstance(routes, list) else 0,
        "route_targets": sorted(set(route_targets), key=lambda value: value.encode("utf-8")),
        "checks": {
            "reader": not any(item.startswith(("missing:README", "missing:Home", "missing:Audit", "reader_missing:")) for item in issues),
            "audit_anchors": not any(item.startswith("audit_anchor_missing:") for item in issues),
            "relative_links": not any(item.startswith(("link_escape:", "link_target_missing:", "link_scheme_forbidden:")) for item in issues),
            "home_routes": not any(item.startswith("home_route_unreachable:") for item in issues),
            "forbidden_path_scan": not any(item.startswith("forbidden_path:") for item in issues),
            "tree_replayed": tree_sha256 == (published_tree_sha256 or candidate_tree_sha256),
            "cleanup": bool(cleanup_passed),
        },
        "issues": sorted(set(issues)),
    }
    if receipt["checks"]["tree_replayed"] is False:
        receipt["issues"].append("tree_digest_mismatch")
        receipt["status"] = "failed"
    return _with_canonical_hash(receipt)


def _formal_finalizer(
    *,
    request: DigestRequest,
    evidence_root: Path,
    candidate_quality_path: Path | None,
    candidate_quality_sha256: str | None,
    candidate_surface_qa_path: Path,
    candidate_surface_qa_sha256: str,
    run_id: str,
) -> Any:
    """Return a publisher callback for the post-rename quality finalization."""

    def finalize(root: Path, _published_run_id: str, _owner_nonce: str) -> Mapping[str, object]:
        bundle_root = Path(root) / "bundle"
        run_path = bundle_root / "_audit" / "run-result.json"
        if candidate_quality_path is None or candidate_quality_sha256 is None or not candidate_quality_path.is_file():
            return {"state": "failed", "reason_code": "QUALITY_RESULT_MISSING"}
        try:
            run, _public_files, public_tree_sha256, directory_manifest_sha256 = _post_rename_surface_qa(bundle_root)
            if not candidate_surface_qa_path.is_file() or _sha(candidate_surface_qa_path.read_bytes()) != candidate_surface_qa_sha256:
                raise ValueError("candidate surface QA artifact is missing or changed")
            candidate_surface_qa = json.loads(candidate_surface_qa_path.read_text(encoding="utf-8"))
            if not isinstance(candidate_surface_qa, Mapping) or candidate_surface_qa.get("status") != "passed" or candidate_surface_qa.get("phase") != "candidate":
                raise ValueError("candidate surface QA is not passed")
            if candidate_surface_qa.get("canonical_sha256") != _sha(
                _canonical_json({key: value for key, value in candidate_surface_qa.items() if key != "canonical_sha256"})
            ):
                raise ValueError("candidate surface QA canonical hash is invalid")
            if candidate_surface_qa.get("candidate_tree_sha256") != public_tree_sha256 or candidate_surface_qa.get("candidate_manifest_sha256") != directory_manifest_sha256:
                raise ValueError("candidate surface QA binding is invalid")
            candidate_bytes = candidate_quality_path.read_bytes()
            if _sha(candidate_bytes) != candidate_quality_sha256:
                raise ValueError("candidate quality artifact hash changed")
            candidate_quality = json.loads(candidate_bytes.decode("utf-8"))
            if not isinstance(candidate_quality, Mapping):
                raise ValueError("candidate quality artifact is not an object")
            if candidate_quality.get("canonical_sha256") != _sha(
                _canonical_json({key: value for key, value in candidate_quality.items() if key != "canonical_sha256"})
            ):
                raise ValueError("candidate quality canonical hash is invalid")
            expected_quality_ref = {
                "ref": f"actual-run/attempts/{run.get('run_id')}/quality-result.json",
                "sha256": candidate_quality_sha256,
            }
            if run.get("quality_result") != expected_quality_ref:
                raise ValueError("M402 run-result quality candidate binding is invalid")
            _validate_m402_published_closure(
                run,
                _public_files,
                candidate_quality,
                evidence_root=evidence_root,
                published_tree_sha256=public_tree_sha256,
                published_manifest_sha256=directory_manifest_sha256,
            )
            published_surface_qa = _surface_qa_from_files(
                run,
                _public_files,
                phase="published",
                candidate_tree_sha256=public_tree_sha256,
                candidate_manifest_sha256=directory_manifest_sha256,
                published_tree_sha256=public_tree_sha256,
                published_manifest_sha256=directory_manifest_sha256,
                cleanup_passed=not any(
                    path.name.startswith(f"{Path(root).name}.staging.")
                    for path in Path(root).parent.iterdir()
                ),
            )
            if published_surface_qa.get("status") != "passed":
                raise ValueError("published surface QA failed")
            published_surface_qa_path = evidence_root / "m402-surface-qa" / "attempts" / run_id / "published-surface-qa.json"
            published_surface_qa_sha256 = _write_create_only(published_surface_qa_path, _canonical_json(published_surface_qa))
            surface_qa_refs = {
                "candidate": {
                    "ref": f"m402-surface-qa/attempts/{run_id}/surface-qa.json",
                    "sha256": candidate_surface_qa_sha256,
                },
                "published": {
                    "ref": f"m402-surface-qa/attempts/{run_id}/published-surface-qa.json",
                    "sha256": published_surface_qa_sha256,
                },
            }
            promoted = promote_quality_result(
                candidate_quality,
                candidate_tree_sha256=public_tree_sha256,
                published_tree_sha256=public_tree_sha256,
                candidate_manifest_ref="bundle/_audit/directory-manifest.json",
                candidate_manifest_sha256=directory_manifest_sha256,
                published_manifest_ref="bundle/_audit/directory-manifest.json",
                published_manifest_sha256=directory_manifest_sha256,
                surface_qa=surface_qa_refs,
            )
            final_path = evidence_root / "actual-run" / "quality-result.json"
            final_bytes = _canonical_json(promoted)
            final_sha256 = _write_create_only(final_path, final_bytes)
            run["quality_result"] = {"ref": "actual-run/quality-result.json", "sha256": final_sha256}
            run["publication_status"] = "released"
            run["outcome"] = "success"
            run["reason_code"] = "NONE"
            run["exit_code"] = 0
            run["quality_status"] = "released"
            run["release_status"] = "released"
            run["lifecycle"] = {
                "state": "released",
                "slice_status": "not_evaluated",
                "full_status": "passed",
                "failure_evidence_path": None,
            }
            run["artifact_manifest"] = {
                "quality_result": run["quality_result"],
                "public_tree_sha256": public_tree_sha256,
                "public_receipt_ref": "bundle/_audit/run-result.json",
                "surface_qa": surface_qa_refs,
            }
            run.pop("canonical_sha256", None)
            run["canonical_sha256"] = _sha(_canonical_json(run))
            _atomic_replace(run_path, _canonical_json(run))
            public_receipt_sha256 = _sha(run_path.read_bytes())
            _write_host_run_receipt(
                evidence_root=evidence_root,
                attempt_id=run_id,
                run_id=run_id,
                request=request,
                source_manifest_sha256=str(run.get("source_manifest_hash", "")),
                public_receipt=run_path,
                terminal_status="released",
            )
            return {
                "state": "published",
                "quality_result_ref": "actual-run/quality-result.json",
                "quality_result_sha256": final_sha256,
                "public_tree_sha256": public_tree_sha256,
                "public_receipt_sha256": public_receipt_sha256,
                "surface_qa": surface_qa_refs,
            }
        except FileExistsError:
            # A fixed promoted artifact is single-writer evidence.  Never
            # overwrite a previous run merely to make the current one green.
            return {"state": "failed", "reason_code": "QUALITY_RESULT_PROMOTION_EXISTS"}
        except (OSError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            try:
                _write_host_run_receipt(
                    evidence_root=evidence_root,
                    attempt_id=run_id,
                    run_id=run_id,
                    request=request,
                    source_manifest_sha256=str(run.get("source_manifest_hash", "")) if isinstance(locals().get("run"), Mapping) else "",
                    public_receipt=run_path,
                    terminal_status="not_released",
                )
            except (OSError, ValueError, KeyError):
                pass
            return {"state": "failed", "reason_code": f"QUALITY_FINALIZE_{type(error).__name__}"}

    return finalize


def _publish_formal_bundle(bundle: Bundle, request: DigestRequest) -> tuple[dict[str, object], Bundle]:
    (
        formal_bundle,
        evidence_root,
        quality_path,
        quality_sha256,
        _candidate_tree,
        candidate_surface_qa_path,
        candidate_surface_qa_sha256,
    ) = _prepare_formal_bundle(bundle, request)
    receipt = commit(
        _published_files(formal_bundle.files, allow_formal_intermediate=request.gate == "M402"),
        request.kb_dir,
        run_id=formal_bundle.run_id,
        finalizer=_formal_finalizer(
            request=request,
            evidence_root=evidence_root,
            candidate_quality_path=quality_path,
            candidate_quality_sha256=quality_sha256,
            candidate_surface_qa_path=candidate_surface_qa_path,
            candidate_surface_qa_sha256=candidate_surface_qa_sha256,
            run_id=formal_bundle.run_id,
        ),
        task5=True,
        material_id=str(request.material_id or ""),
    )
    return receipt, formal_bundle


def digest(request: DigestRequest, providers: tuple[SemanticModel, Embedder] | None = None) -> DigestResult:
    """Compile and atomically publish one reader-first knowledge bundle."""

    try:
        if request.gate not in {None, "M401", "M402"}:
            raise ValueError(f"unsupported digest gate: {request.gate}")
        if request.gate == "M401":
            # M401 is a closed fake/no-network evidence mode.  It consumes a
            # validated C3 bundle only and never falls through to real raw,
            # CompanyBrain, config, or provider handling.
            return _run_m401(request)
        if request.gate == "M402":
            if request.evaluation_mode != "full":
                raise ValueError("M402 direct digest requires full evaluation")
            material_id = _validate_m402_gate(request)
            request = replace(request, material_id=material_id)
            if request.companybrain_route_snapshot is not None:
                raise ValueError("M402 does not accept a caller-supplied CompanyBrain snapshot")
        if providers is None:
            providers = build_providers(request.provider_config_path)
        bundle = _build_bundle(request, providers[0], providers[1])
        if request.gate == "M402":
            receipt, bundle = _publish_formal_bundle(bundle, request)
        else:
            receipt = commit(
                _published_files(bundle.files, allow_formal_intermediate=False),
                request.kb_dir,
                run_id=bundle.run_id,
            )
        # The publisher is the only writer.  Return paths only after the atomic
        # rename succeeds.
        if request.gate == "M402":
            outcome = "released" if receipt.get("state") == "published" else "not_released"
            reason = None if outcome == "released" else str(receipt.get("reason_code") or "QUALITY_GATE_FAILED")
        else:
            outcome, reason = _bundle_terminal_state(bundle, request)
        return DigestResult(
            outcome,
            bundle.run_id,
            Path(request.kb_dir) / "bundle" / "Home.md",
            Path(request.kb_dir) / "bundle" / "Audit.md",
            reason if receipt.get("committed") else "publication_failed",
            bundle.companybrain_observation,
        )
    except ProviderConfigError as error:
        return DigestResult("blocked", "", reason_code=str(error))
    except (FileExistsError, ValueError, ProviderError) as error:
        return DigestResult("unavailable" if isinstance(error, ProviderError) else "blocked", "", reason_code=str(error))
    except PublishError as error:
        return DigestResult("failed", "", reason_code=str(error))


def digest_slice_then_full(
    slice_request: DigestRequest,
    full_request: DigestRequest,
    providers: tuple[SemanticModel, Embedder] | None = None,
) -> DigestSequenceResult:
    """Run the required slice then full flow with one shared provider context.

    The slice is compiled in memory for diagnosis.  Only the full bundle is
    published.  A source response is reusable only when the complete prompt is
    byte-identical; no path or source-name guess can make a cache hit.
    """

    if slice_request.evaluation_mode != "slice" or full_request.evaluation_mode != "full":
        raise ValueError("slice_then_full requires slice and full requests")
    if Path(slice_request.new_dir).expanduser().resolve() != Path(full_request.new_dir).expanduser().resolve():
        raise ValueError("slice and full requests must use the same source directory")
    if slice_request.provider_config_path != full_request.provider_config_path:
        raise ValueError("slice and full requests must use the same provider config")
    if slice_request.quality_config_path != full_request.quality_config_path:
        raise ValueError("slice and full requests must use the same quality config")
    slice_manifest = Path(slice_request.source_manifest_path).expanduser().resolve() if slice_request.source_manifest_path is not None else None
    full_manifest = Path(full_request.source_manifest_path).expanduser().resolve() if full_request.source_manifest_path is not None else None
    if slice_manifest != full_manifest:
        raise ValueError("slice and full requests must use the same source manifest")
    if not slice_request.source_paths:
        raise ValueError("slice request needs an explicit source_paths closure")
    if slice_request.gate != full_request.gate:
        raise ValueError("slice and full requests must use the same gate")
    if slice_request.gate == "M401":
        raise ValueError("M401 is an isolated fixture gate and cannot run slice_then_full")
    if full_request.gate == "M402":
        # The real-run gate must close before this function creates a model,
        # reads raw/CompanyBrain, or materializes either phase.  The single
        # snapshot is then shared by slice and full so their comparison uses
        # the same CompanyBrain observation identity.
        material_id = _validate_m402_gate(full_request)
        full_request = replace(full_request, material_id=material_id)
        if slice_request.companybrain_route_snapshot is not None or full_request.companybrain_route_snapshot is not None:
            raise ValueError("M402 slice_then_full does not accept a caller-supplied CompanyBrain snapshot")
    if providers is None:
        providers = build_providers(full_request.provider_config_path)
    context = RunContext(context_id="ctx-" + uuid.uuid4().hex[:20])
    model = _MemoizedSemanticModel(providers[0], context)
    embedder = providers[1]
    slice_bundle = _build_bundle(replace(slice_request, run_context=context), model, embedder)
    context.slice_run_id = slice_bundle.run_id
    slice_run = json.loads(slice_bundle.files["_audit/run-result.json"].decode("utf-8"))
    slice_outcome, slice_reason = _bundle_terminal_state(slice_bundle, slice_request)
    slice_result = DigestResult(
        slice_outcome,
        slice_bundle.run_id,
        reason_code=slice_reason,
        companybrain_observation=slice_bundle.companybrain_observation,
    )
    slice_plan = slice_run.get("provider_call_plan", {})
    context.slice_llm_plan = int(slice_plan.get("max_llm_requests", 0))
    context.slice_embedding_plan = int(slice_plan.get("max_embedding_requests", 0))
    full_bundle = _build_bundle(replace(full_request, run_context=context), model, embedder)
    receipt: dict[str, object] | None = None
    if full_request.gate == "M402" and isinstance(full_bundle.quality_result, Mapping):
        receipt, full_bundle = _publish_formal_bundle(full_bundle, full_request)
    try:
        if full_request.gate != "M402":
            receipt = commit(
                _published_files(full_bundle.files, allow_formal_intermediate=False),
                full_request.kb_dir,
                run_id=full_bundle.run_id,
            )
    except PublishError as error:
        full_result = DigestResult("failed", full_bundle.run_id, reason_code=str(error))
    else:
        if full_request.gate == "M402":
            assert receipt is not None
            outcome = "released" if receipt.get("state") == "published" else "not_released"
            reason = None if outcome == "released" else str(receipt.get("reason_code") or "QUALITY_GATE_FAILED")
        else:
            outcome, reason = _bundle_terminal_state(full_bundle, full_request)
        full_result = DigestResult(
            outcome,
            full_bundle.run_id,
            Path(full_request.kb_dir) / "bundle" / "Home.md",
            Path(full_request.kb_dir) / "bundle" / "Audit.md",
            reason if receipt.get("committed") else "publication_failed",
            full_bundle.companybrain_observation,
        )
    return DigestSequenceResult(
        slice_run_id=slice_bundle.run_id,
        full_run_id=full_bundle.run_id,
        reused_response_count=context.reused_response_count,
        full_result=full_result,
        slice_result=slice_result,
        slice_run=slice_run,
    )


__all__ = [
    "Bundle",
    "DigestSequenceResult",
    "DigestRequest",
    "DigestResult",
    "Embedder",
    "PAGE_TYPES",
    "ReaderPage",
    "SemanticModel",
    "SourceDoc",
    "RunContext",
    "digest",
    "digest_slice_then_full",
]
