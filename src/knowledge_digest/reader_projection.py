"""Compile the K1/K2 batch into a reader-first K3 candidate.

K1/K2 pages are intentionally evidence material.  They preserve source blocks,
claims, and machine navigation, but they are not a user knowledge base.  This
module is the missing projection boundary: it consumes those facts, asks the
approved semantic provider for a typed Reader answer, and writes a separate
candidate whose public pages contain concise answers while the exact K1/K2
bytes remain under ``_audit/k1``.

The module does not publish.  ``kb_publish`` remains the atomic K3 writer and
``kb_accept`` remains the offline acceptance boundary.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
from typing import Any, Iterable, Mapping, Sequence

from .semantic_cache import CacheIntegrityError, ModelCache


MAX_PAGE_LINES = 300
READER_MODEL_ID = "task10-reader-model"
READER_PROMPT_VERSION = "task10-reader-projection-v1"
READER_TOPIC_MAP_VERSION = "task10-reader-page-contract-v1"
UNKNOWN = "原始资料未明确"

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
PRODUCT_LABELS = {
    "emm-for-android": "EMM for Android",
    "emm-for-ios": "EMM for iOS",
    "goinsight": "GoInsight",
    "merchant-system": "Merchant System",
    "shared": "跨产品答案",
}
AGGREGATE_SPECS = (
    {
        "slug": "emm-产品定位与关系边界",
        "title": "EMM 产品定位与关系边界",
        "question": "EMM 是什么、服务谁、怎么选，以及与相邻产品的边界是什么？",
        "page_type": "positioning",
        "terms": ("EMM介绍", "EMM服务订阅", "iOS-终端管理", "设备详情页远程控制", "AirViewer"),
    },
    {
        "slug": "策略与配置对象关系总览",
        "title": "策略与配置对象关系总览",
        "question": "Android 与 iOS 的策略、配置项和设备对象之间是什么关系？",
        "page_type": "concept",
        "terms": ("通信和网络配置", "策略", "系统配置", "安全配置", "Store App"),
    },
    {
        "slug": "设备入网与应用管理操作总览",
        "title": "设备入网与应用管理操作总览",
        "question": "如何完成 Android 设备入网、应用审核和策略配置？",
        "page_type": "operation",
        "terms": ("二维码注册", "Zero Touch", "应用详情", "应用参数", "设备注册"),
    },
    {
        "slug": "平台异常定位与处理入口",
        "title": "平台异常定位与处理入口",
        "question": "遇到迁移、指标、权限或设备状态异常时，应该先查什么？",
        "page_type": "diagnosis",
        "terms": ("bug analysis", "迁移", "指标详情", "异常", "激活&停用", "权限"),
    },
    {
        "slug": "版本迭代与方案复盘经验",
        "title": "版本迭代与方案复盘经验",
        "question": "现有资料记录了哪些版本变化、方案取舍和经验教训？",
        "page_type": "experience",
        "terms": ("Sprint", "Retrospective", "bug analysis", "版本", "复盘", "智能搭建"),
    },
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_INTERNAL = re.compile(r"(?i)(?:cluster|draft|source[_-]?id|content[_-]?hash|digest[_-]?topic|provider[_-]?tokens)")
_READER_INTERNAL_REF = re.compile(
    r"\s*\[(?:(?:cl|source|block|evidence)[_-][A-Za-z0-9_-]+)\]",
    re.IGNORECASE,
)
_SENSITIVE = re.compile(
    r"(?i)(\b(?:password|passwd|token|access[_ -]?token|api[_ -]?(?:secret|key)|private[_ -]?key|secret[_ -]?key|私钥|密码)\b\s*[:=：]\s*[`'\"“]?)([^`\n,;，；)）\"”]+)"
)
_ACCOUNT_EMAIL = re.compile(r"(?i)\b[\w.+-]+@[\w.-]+\.iam\.gserviceaccount\.com\b")


class ReaderProjectionError(RuntimeError):
    """The K3 Reader candidate cannot be trusted."""


class ReaderProviderUnavailable(ReaderProjectionError):
    """No cached Reader result exists and the semantic provider is unavailable."""


@dataclass(frozen=True)
class ReaderProjectionResult:
    output_dir: Path
    status: str
    publish_status: str
    source_count: int
    reader_page_count: int
    provider_calls: int
    cache_hits: int
    provider_tokens: int
    blockers: tuple[Mapping[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "publish_status": self.publish_status,
            "output_dir": str(self.output_dir),
            "source_count": self.source_count,
            "reader_page_count": self.reader_page_count,
            "provider_calls": self.provider_calls,
            "cache_hits": self.cache_hits,
            "provider_tokens": self.provider_tokens,
            "blockers": [dict(item) for item in self.blockers],
        }


@dataclass(frozen=True)
class _Evidence:
    evidence_id: str
    source_path: str
    source_block_id: str | None
    content_hash: str
    line_start: int
    line_end: int
    text: str
    original_page_path: str
    # K1's content_hash identifies the extracted evidence block and is part of
    # the Reader cache key.  K3 acceptance, however, verifies the cited source
    # line span against the frozen input bytes.  Keep that audit-only identity
    # separate so fixing the citation does not invalidate a valid semantic
    # cache entry or rewrite the preserved K1 facts.
    audit_content_hash: str | None = None

    def cache_member(self, topic_key: str, order: int) -> dict[str, Any]:
        return {
            "topic_key": topic_key,
            "source_path": self.source_path,
            "content_hash": self.content_hash,
            "block_id": self.source_block_id or self.evidence_id,
            "text": self.text,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "member_order": order,
        }

    def as_audit(self, page_path: str, surface: str) -> dict[str, Any]:
        return {
            "claim_id": self.evidence_id,
            "claim_kind": "narrative",
            "content_hash": self.audit_content_hash or self.content_hash,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "page_anchor": "reader",
            "page_path": page_path,
            "reader_surface": surface,
            "source_block_id": self.source_block_id,
            "source_path": self.source_path,
            "source_uri": self.source_path,
            "span_start": 0,
            "span_end": len(self.text),
            "status": "sourced",
            "text": self.text,
        }


@dataclass(frozen=True)
class _BatchPage:
    original_path: str
    product: str
    source_paths: tuple[str, ...]
    source_ids: tuple[str, ...]
    title: str
    raw_text: str
    evidence: tuple[_Evidence, ...]


@dataclass(frozen=True)
class _ReaderPage:
    page_id: str
    relative_path: str
    title: str
    question: str
    page_type: str
    product: str
    product_label: str
    module: str
    object_name: str
    scenario: str
    boundary: str
    summary: str
    sections: Mapping[str, tuple[str, ...]]
    evidence_by_surface: Mapping[str, tuple[str, ...]]
    evidence: Mapping[str, _Evidence]
    source_paths: tuple[str, ...]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _safe_slug(value: str, fallback: str = "page") -> str:
    value = str(value).strip().lower().replace("&", " and ")
    value = re.sub(r"[\\/]+", " ", value)
    value = re.sub(r"[^0-9a-z\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af._ -]+", " ", value)
    value = re.sub(r"[\s_-]+", "-", value).strip("-.")
    return value[:100] or fallback


def _redact(value: str) -> str:
    value = _ACCOUNT_EMAIL.sub("[服务账号已隐藏]", value)
    value = _SENSITIVE.sub(r"\1敏感值已隐藏", value)
    # Evidence IDs remain in the audit ledger, but must not leak into a
    # reader-facing sentence when a provider echoes a prompt packet.
    value = _READER_INTERNAL_REF.sub("", value)
    return value.strip()


def _frontmatter_value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(value, ensure_ascii=False)


def _frontmatter(values: Mapping[str, object]) -> str:
    return "---\n" + "\n".join(f"{key}: {_frontmatter_value(value)}" for key, value in values.items()) + "\n---\n"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReaderProjectionError(f"invalid JSON: {path}: {type(error).__name__}") from error


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ReaderProjectionError(f"invalid JSONL {path}:{number}") from error
        if not isinstance(value, dict):
            raise ReaderProjectionError(f"JSONL row is not an object: {path}:{number}")
        rows.append(value)
    return rows


def _copy_audit(batch: Path, candidate: Path) -> None:
    source = batch / "_audit"
    destination = candidate / "_audit" / "k1"
    if not source.is_dir() or source.is_symlink():
        raise ReaderProjectionError("K1 audit directory is missing")
    for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix().encode("utf-8")):
        if path.is_symlink():
            raise ReaderProjectionError(f"K1 audit contains a symbolic link: {path}")
        if path.is_file():
            relative = path.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _product_for_path(path: str) -> tuple[str, str]:
    parts = PurePosixPath(path).parts
    product = parts[1] if len(parts) > 1 and parts[0] == "products" else "shared"
    return product, PRODUCT_LABELS.get(product, product.replace("-", " ").title())


def _page_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("title:"):
            candidate = stripped.partition(":")[2].strip().strip("'\"")
            if candidate:
                return candidate
        if stripped.startswith("# ") and stripped[2:].strip():
            return stripped[2:].strip()
    return PurePosixPath(fallback).stem.replace("-", " ").replace("_", " ").strip() or "未命名主题"


def _normalise_evidence(row: Mapping[str, Any], original_page_path: str, index: int) -> _Evidence | None:
    status = row.get("status")
    if status not in {"sourced", "ready"}:
        return None
    source_path = row.get("source_path")
    content_hash = row.get("content_hash")
    text = row.get("text")
    line_start = row.get("line_start")
    line_end = row.get("line_end")
    if not isinstance(source_path, str) or not source_path.strip():
        return None
    if not isinstance(content_hash, str) or not _SHA256.fullmatch(content_hash):
        return None
    if not isinstance(text, str) or not text.strip():
        return None
    if not isinstance(line_start, int) or not isinstance(line_end, int) or line_start < 1 or line_end < line_start:
        return None
    evidence_id = str(row.get("claim_id") or row.get("block_id") or f"evidence-{index}")
    return _Evidence(
        evidence_id=evidence_id,
        source_path=source_path.replace("\\", "/"),
        source_block_id=str(row.get("source_block_id") or row.get("block_id") or "") or None,
        content_hash=content_hash,
        line_start=line_start,
        line_end=line_end,
        text=text.strip(),
        original_page_path=original_page_path,
    )


def _bind_audit_hash(evidence: _Evidence, input_root: Path | None) -> _Evidence:
    """Bind a Reader citation to the exact frozen source line span.

    K1's ``content_hash`` is intentionally a block-level identity.  The K3
    acceptance contract checks a citation by hashing the source lines named by
    ``line_start``/``line_end``.  Those values can differ when K1 extracted a
    block, especially when the source line has trailing whitespace.  Reader
    cache identity must continue to use the K1 block hash; only the emitted
    K3 audit row receives this source-span hash.
    """

    if input_root is None:
        return evidence
    relative = PurePosixPath(evidence.source_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        return evidence
    source = input_root.joinpath(*relative.parts)
    if source.is_symlink() or not source.is_file():
        return evidence
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return evidence
    if evidence.line_end > len(lines):
        return evidence
    span = "\n".join(lines[evidence.line_start - 1 : evidence.line_end])
    return replace(evidence, audit_content_hash=_sha(span + "\n"))


def _load_batch(batch: Path, *, input_root: Path | None = None) -> tuple[dict[str, Any], list[_BatchPage], dict[str, Any]]:
    if batch.is_symlink() or not batch.is_dir():
        raise ReaderProjectionError("K1 batch must be an existing real directory")
    manifest = _read_json(batch / "_audit/page-manifest.json")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "task7-page-manifest.v1":
        raise ReaderProjectionError("K1 page manifest schema is not supported")
    if manifest.get("run_status") != "complete" or manifest.get("publish_status") != "not_released":
        raise ReaderProjectionError("K1 batch is not a complete unreleased candidate")
    if manifest.get("blockers"):
        raise ReaderProjectionError("K1 batch has blockers")
    source_rows = _read_jsonl(batch / "_audit/sources.jsonl")
    reference_rows = _read_jsonl(batch / "_audit/reference-blocks.jsonl")
    by_page: dict[str, list[_Evidence]] = defaultdict(list)
    by_page_ids: dict[str, set[str]] = defaultdict(set)
    for index, row in enumerate(source_rows, start=1):
        page_path = row.get("page_path")
        if not isinstance(page_path, str):
            continue
        evidence = _normalise_evidence(row, page_path, index)
        if evidence is not None:
            evidence = _bind_audit_hash(evidence, input_root)
        if evidence is not None and evidence.evidence_id not in by_page_ids[page_path]:
            by_page[page_path].append(evidence)
            by_page_ids[page_path].add(evidence.evidence_id)
    for index, raw_row in enumerate(reference_rows, start=1):
        page_path = raw_row.get("page_path")
        if not isinstance(page_path, str):
            continue
        # Keep the original K1 claim identity stable when claims already
        # exist. Reference blocks are a lossless recovery path only for a
        # page whose claim extraction produced no usable evidence; otherwise
        # adding them would invalidate an already-good Reader cache entry.
        if by_page.get(page_path):
            continue
        row = dict(raw_row)
        if (not isinstance(row.get("text"), str) or not str(row.get("text")).strip()) and input_root is not None:
            source_path = row.get("source_path")
            start = row.get("line_start")
            end = row.get("line_end")
            if isinstance(source_path, str) and isinstance(start, int) and isinstance(end, int) and start >= 1 and end >= start:
                raw_source = input_root / PurePosixPath(source_path)
                if raw_source.is_file() and not raw_source.is_symlink():
                    source_lines = raw_source.read_text(encoding="utf-8").splitlines()
                    if end <= len(source_lines):
                        row["text"] = "\n".join(source_lines[start - 1 : end])
                        row["status"] = "ready"
        evidence = _normalise_evidence(row, page_path, index)
        if evidence is not None:
            evidence = _bind_audit_hash(evidence, input_root)
        if evidence is not None and evidence.evidence_id not in by_page_ids[page_path]:
            by_page[page_path].append(evidence)
            by_page_ids[page_path].add(evidence.evidence_id)
    pages: list[_BatchPage] = []
    raw_pages = manifest.get("pages")
    if not isinstance(raw_pages, list):
        raise ReaderProjectionError("K1 page manifest pages are missing")
    for item in raw_pages:
        if not isinstance(item, Mapping):
            continue
        page_path = item.get("page_path")
        if not isinstance(page_path, str) or not page_path.startswith("products/") or not page_path.endswith(".md"):
            continue
        source_path = batch / page_path
        if source_path.is_symlink() or not source_path.is_file():
            raise ReaderProjectionError(f"K1 page is missing: {page_path}")
        product, _label = _product_for_path(page_path)
        page_paths = item.get("page_paths") if isinstance(item.get("page_paths"), list) else [page_path]
        evidence: list[_Evidence] = []
        for raw_path in page_paths:
            if isinstance(raw_path, str):
                for row in by_page.get(raw_path, ()):
                    if row.evidence_id not in {entry.evidence_id for entry in evidence}:
                        evidence.append(row)
        source_paths = tuple(dict.fromkeys(str(value) for value in item.get("source_paths", ()) if str(value)))
        source_ids = tuple(
            str(entry.get("source_id"))
            for entry in manifest.get("source_snapshot", {}).get("entries", ())
            if isinstance(entry, Mapping) and entry.get("source_path") in source_paths and entry.get("source_id")
        )
        pages.append(
            _BatchPage(
                original_path=page_path,
                product=product,
                source_paths=source_paths,
                source_ids=source_ids,
                title=_page_title(source_path.read_text(encoding="utf-8"), page_path),
                raw_text=source_path.read_text(encoding="utf-8"),
                evidence=tuple(evidence),
            )
        )
    if not pages:
        raise ReaderProjectionError("K1 batch has no product pages")
    source_snapshot = manifest.get("source_snapshot")
    if not isinstance(source_snapshot, Mapping):
        source_snapshot = {"entries": []}
    return manifest, pages, dict(source_snapshot)


def _prompt(page: _BatchPage, evidence: Sequence[_Evidence], feedback: str = "") -> str:
    product_label = PRODUCT_LABELS.get(page.product, page.product)
    contract = {
        "title": "可读的业务标题",
        "question": "这页要直接回答的一个问题",
        "page_type": "positioning | concept | operation | diagnosis | experience",
        "module": "模块或功能域",
        "object": "对象或配置对象",
        "scenario": "使用场景",
        "boundary": "适用范围、限制或资料缺口",
        "summary": "一到三句直接回答",
        "sections": {heading: ["短句或 Markdown 列表项"] for heading in PAGE_TYPES["operation"]},
        "evidence": {"summary": ["证据 ID"], "前置条件": ["证据 ID"]},
    }
    evidence_packet = [
        {
            "evidence_id": item.evidence_id,
            "source_path": item.source_path,
            "lines": f"{item.line_start}-{item.line_end}",
            "text": item.text[:1200],
        }
        for item in evidence[:80]
    ]
    aggregate_instruction = ""
    if page.product == "shared":
        aggregate_instruction = f"\n这是跨来源答案页。固定页面类型：{page.raw_text.splitlines()[0].split('：', 1)[-1]}；必须直接回答：{page.raw_text.splitlines()[1].split('：', 1)[-1]}。\n"
    return f"""你是企业知识库主编。请把一份 K1 证据页编辑成一张真正可读的 Reader 页面。只使用 supplied evidence，不使用外部知识，不补常识，不把原文逐段复制出来。

只返回一个 JSON 对象，结构参考：
{json.dumps(contract, ensure_ascii=False)}

硬规则：
1. page_type 只能是 positioning、concept、operation、diagnosis、experience 之一；根据资料的主要用途选择，不要默认全部是 concept。
2. sections 必须恰好使用所选 page_type 对应的章节：{json.dumps({key: list(value) for key, value in PAGE_TYPES.items()}, ensure_ascii=False)}。
3. 每条事实都必须引用 evidence 中真实存在的 evidence_id。没有证据时只能写“{UNKNOWN}”并返回空引用，不得猜测。
4. summary 也必须有证据；每个非“{UNKNOWN}”章节至少引用一条证据。保留数字、版本、权限、入口、否定条件和例外。
5. title、question、module、object、scenario、boundary 都必须是读者能懂的业务语言，不得出现 source_id、cluster、draft、hash、provider 等内部字段。
6. sections 的每项是短句列表，不要输出章节标题，不要输出“来源：文件名”标签，不要把证据 ID 写入正文。
7. 一张页面控制在 2200 个中文字符以内；操作页写前置条件/步骤/结果/验证/失败，诊断页写现象/检查/原因/处理/升级边界；没有内容的章节写“{UNKNOWN}”。
8. 任何密码、token、私钥、服务账号或凭据值都不能进入 Reader；只保留业务条件并写“敏感值未在 Reader 展示”。

产品：{product_label}
K1 原始主题标题：{page.title}
K1 页面：{page.original_path}
{aggregate_instruction}
证据：
{json.dumps(evidence_packet, ensure_ascii=False)}
{feedback}
"""


def _parse_provider_result(value: object) -> dict[str, Any]:
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.rstrip().endswith("```"):
                text = text.rstrip()[:-3]
        try:
            value = json.loads(text)
        except json.JSONDecodeError as error:
            raise ReaderProjectionError("Reader provider returned invalid JSON") from error
    if not isinstance(value, Mapping):
        raise ReaderProjectionError("Reader provider result must be an object")
    result = dict(value)
    nested = result.get("result")
    if isinstance(nested, Mapping) and "title" not in result:
        result = dict(nested)
        if "provider_tokens" in value:
            result["provider_tokens"] = value["provider_tokens"]
    return result


def _call_provider(provider: object, prompt: str) -> Mapping[str, Any]:
    try:
        method = getattr(provider, "complete_reader", None)
        if callable(method):
            return _parse_provider_result(method(prompt))
        if callable(provider):
            return _parse_provider_result(provider(prompt))
        method = getattr(provider, "complete", None)
        if callable(method):
            return _parse_provider_result(method(prompt))
    except ReaderProviderUnavailable:
        raise
    except Exception as error:
        raise ReaderProviderUnavailable(f"Reader provider transport failed: {type(error).__name__}") from error
    raise ReaderProviderUnavailable("Reader provider is not callable")


def _list_values(value: object) -> list[str]:
    if isinstance(value, str):
        values = [line.strip().lstrip("-*•0123456789. ") for line in value.splitlines() if line.strip()]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = [str(item).strip() for item in value if str(item).strip()]
    else:
        values = []
    return [_redact(item) for item in values if item]


def _normalise_draft(value: Mapping[str, Any], page: _BatchPage, evidence: Sequence[_Evidence]) -> dict[str, Any]:
    known = {item.evidence_id: item for item in evidence}
    page_type = value.get("page_type")
    if page_type not in PAGE_TYPES:
        raise ReaderProjectionError("Reader page_type is invalid")
    title = _redact(str(value.get("title") or page.title).strip()) or page.title
    question = _redact(str(value.get("question") or f"这页说明{title}的主要内容和使用边界。").strip())
    module = _redact(str(value.get("module") or "未分类模块").strip()) or "未分类模块"
    object_name = _redact(str(value.get("object") or title).strip()) or title
    scenario = _redact(str(value.get("scenario") or "资料查阅").strip()) or "资料查阅"
    boundary = _redact(str(value.get("boundary") or UNKNOWN).strip()) or UNKNOWN
    summary = _redact(str(value.get("summary") or UNKNOWN).strip()) or UNKNOWN
    if _INTERNAL.search(title) or _INTERNAL.search(question):
        raise ReaderProjectionError("Reader title contains an internal identity")
    sections = value.get("sections")
    sections = sections if isinstance(sections, Mapping) else {}
    evidence_value = value.get("evidence")
    evidence_value = evidence_value if isinstance(evidence_value, Mapping) else {}
    expected_surfaces = ("summary", *PAGE_TYPES[page_type])
    normalised_sections: dict[str, list[str]] = {}
    refs_by_surface: dict[str, list[str]] = {}
    for surface in expected_surfaces:
        if surface == "summary":
            body_values = [summary]
        else:
            body_values = _list_values(sections.get(surface, UNKNOWN))
        if not body_values:
            body_values = [UNKNOWN]
        refs = evidence_value.get(surface, ())
        if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes, bytearray)):
            refs = ()
        # Providers occasionally mutate one short claim ID while copying a
        # long evidence packet.  Drop only those unknown IDs; the page still
        # has to retain at least one exact, K1-bound citation for every
        # non-unknown answer.  A section with no surviving evidence remains a
        # hard contract failure and cannot be published.
        ref_values = [str(item) for item in refs if str(item) in known]
        if any(item != UNKNOWN for item in body_values) and not ref_values:
            # Keep the page structurally complete but never publish an
            # unsupported sentence. The audit layer still shows that this
            # section had no surviving evidence binding.
            body_values = [UNKNOWN]
        if surface == "summary":
            normalised_sections[surface] = body_values
        else:
            normalised_sections[surface] = body_values[:8]
        refs_by_surface[surface] = list(dict.fromkeys(ref_values))
    return {
        "title": title,
        "question": question,
        "page_type": page_type,
        "module": module,
        "object": object_name,
        "scenario": scenario,
        "boundary": boundary,
        "summary": normalised_sections["summary"][0],
        "sections": {key: tuple(values) for key, values in normalised_sections.items() if key != "summary"},
        "evidence": {key: tuple(values) for key, values in refs_by_surface.items()},
        "provider_tokens": int(value.get("provider_tokens", 0)) if isinstance(value.get("provider_tokens", 0), int) else 0,
    }


def _evidence_line(page: _ReaderPage, refs: Sequence[str]) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for ref in refs:
        item = page.evidence.get(ref)
        if item is None:
            continue
        grouped[item.source_path].append(f"{item.line_start}-{item.line_end}")
    if not grouped:
        return ""
    chunks = [f"`{path}` 第 {', '.join(dict.fromkeys(lines))} 行" for path, lines in sorted(grouped.items())]
    return "> 证据：" + "；".join(chunks) + f"（[Audit 回查](../../../Audit.md#reader-page-{page.page_id})）"


def _render_page(page: _ReaderPage) -> str:
    values = {
        "managed_by": "KnowledgeDigest",
        "digest_kind": "topic",
        "digest_topic_id": page.page_id,
        "digest_published_path": page.relative_path,
        "digest_part": 1,
        "page_type": PAGE_TYPE_LABELS[page.page_type],
        "product": page.product_label,
        "module": page.module,
        "object": page.object_name,
        "scenario": page.scenario,
        "boundary": page.boundary,
        "digest_page_id": page.page_id,
        "source_status": "reader",
        "quality_status": "candidate",
    }
    lines = [
        _frontmatter(values).rstrip("\n"),
        "",
        f"# {page.title}",
        "",
        f"> {page.summary}",
        _evidence_line(page, page.evidence_by_surface.get("summary", ())),
        "",
        "## Summary",
        "",
        page.summary,
        "",
        "## 这页解决什么问题",
        "",
        page.question,
        "",
        "## 页面类型",
        "",
        f"- {PAGE_TYPE_LABELS[page.page_type]}",
        "",
    ]
    for heading in PAGE_TYPES[page.page_type]:
        lines.extend([f"## {heading}", ""])
        for item in page.sections[heading]:
            lines.append(item if item == UNKNOWN else f"- {item}")
        lines.extend([_evidence_line(page, page.evidence_by_surface.get(heading, ())), ""])
    lines.extend([
        "## Evidence",
        "",
        "本页事实的来源 URI、内容指纹、原文行号和 Claim 绑定统一保存在 Audit；正文不重复列出原始文件名。",
        "",
        "## Provenance",
        "",
        "本页由 K1/K2 语义事实投影而来；K1/K2 原始审计保存在 `_audit/k1/`。",
        "",
        "## 相关入口",
        "",
        "- [返回 Home](../../../Home.md)",
        "- [打开本页 Audit 入口](../../../Audit.md#reader-page-" + page.page_id + ")",
        "",
    ])
    return "\n".join(line for line in lines if line is not None).rstrip() + "\n"


def _page_from_draft(page: _BatchPage, draft: Mapping[str, Any], evidence: Sequence[_Evidence], slug: str) -> _ReaderPage:
    page_id = "reader-" + _sha(page.original_path + "\0" + "\0".join(item.evidence_id for item in evidence))[:20]
    product_label = PRODUCT_LABELS.get(page.product, page.product.replace("-", " ").title())
    rel = f"products/{page.product}/{draft['page_type']}/{slug}.md"
    evidence_by_id = {item.evidence_id: item for item in evidence}
    refs = {key: tuple(value) for key, value in draft["evidence"].items()}
    return _ReaderPage(
        page_id=page_id,
        relative_path=rel,
        title=str(draft["title"]),
        question=str(draft["question"]),
        page_type=str(draft["page_type"]),
        product=page.product,
        product_label=product_label,
        module=str(draft["module"]),
        object_name=str(draft["object"]),
        scenario=str(draft["scenario"]),
        boundary=str(draft["boundary"]),
        summary=str(draft["summary"]),
        sections=draft["sections"],
        evidence_by_surface=refs,
        evidence=evidence_by_id,
        source_paths=page.source_paths,
    )


def _render_home(pages: Sequence[_ReaderPage], source_count: int) -> str:
    route_labels = {
        "positioning": "我想了解产品是什么、服务谁、怎么选以及边界",
        "concept": "我想理解一个模块、对象或配置项",
        "operation": "我想按步骤完成一项操作",
        "diagnosis": "我遇到了问题，需要定位原因",
        "experience": "我想了解历史经验、版本和踩坑",
    }
    lines = [
        "# KnowledgeDigest",
        "",
        "这是本次资料的读者入口。先按要解决的问题进入，再按产品和页面类型定位答案。",
        "",
        "## 我现在要做什么",
        "",
    ]
    for page_type, label in route_labels.items():
        rows = [page for page in pages if page.page_type == page_type]
        lines.extend([f"### {label}", ""])
        if not rows:
            lines.extend([f"- {UNKNOWN}", ""])
            continue
        for page in sorted(rows, key=lambda item: (0 if item.product == "shared" else 1, item.product, item.title.casefold()))[:18]:
            lines.append(f"- [{page.title}]({page.relative_path})：{page.scenario}；{page.boundary}")
        if len(rows) > 18:
            lines.append(f"- 其余 {len(rows) - 18} 页见对应产品索引。")
        lines.append("")
    lines.extend(["## 按产品", ""])
    for product in sorted({page.product for page in pages}):
        label = PRODUCT_LABELS.get(product, product)
        lines.append(f"- [{label}](products/{product}/index.md)")
    lines.extend(["", "## 资料范围", "", f"- K1/K2 来源：{source_count} 条", f"- Reader 页面：{len(pages)} 页", "- 完整证据回查：见 [Audit](Audit.md)", "- 资料没有明确说明的内容会标为‘原始资料未明确’，不会由系统补猜。", ""])
    return "\n".join(lines)


def _render_index(pages: Sequence[_ReaderPage]) -> str:
    lines = ["# 知识索引", "", "按产品和页面类型进入 Reader。", ""]
    for product in sorted({page.product for page in pages}):
        label = PRODUCT_LABELS.get(product, product)
        rows = [page for page in pages if page.product == product]
        lines.extend([f"## [{label}](products/{product}/index.md)", ""])
        for page_type in PAGE_TYPES:
            count = sum(page.page_type == page_type for page in rows)
            if count:
                lines.append(f"- {PAGE_TYPE_LABELS[page_type]}：{count} 页")
        lines.append("")
    return "\n".join(lines)


def _render_product_index(product: str, pages: Sequence[_ReaderPage]) -> str:
    label = PRODUCT_LABELS.get(product, product)
    lines = [f"# {label}", "", "按页面类型阅读；每页都保留到 Audit 的证据回查入口。", ""]
    for page_type in PAGE_TYPES:
        rows = sorted((page for page in pages if page.page_type == page_type), key=lambda item: item.title.casefold())
        if not rows:
            continue
        lines.extend([f"## {PAGE_TYPE_LABELS[page_type]}", ""])
        for page in rows:
            page_name = PurePosixPath(page.relative_path).name
            lines.append(f"- [{page.title}]({page_type}/{page_name}) — {page.question}")
        lines.append("")
    lines.extend(["- [返回 Home](../../Home.md)", ""])
    return "\n".join(lines)


def _render_audit(pages: Sequence[_ReaderPage], source_snapshot: Mapping[str, Any], result_status: str) -> str:
    entries = source_snapshot.get("entries") if isinstance(source_snapshot.get("entries"), list) else []
    pages_by_source: dict[str, list[_ReaderPage]] = defaultdict(list)
    for page in pages:
        for source in page.source_paths:
            pages_by_source[source].append(page)
    lines = [
        "# Audit",
        "",
        "这是机器证据回查入口，不是 Reader 正文。K1/K2 原始审计文件完整保留在 `_audit/k1/`。",
        "",
        f"- Reader 状态：`{result_status}`",
        f"- 来源总数：`{len(entries)}`",
        f"- Reader 页面：`{len(pages)}`",
        "",
        "## 来源清单",
        "",
    ]
    for entry in sorted((row for row in entries if isinstance(row, Mapping)), key=lambda row: str(row.get("source_path", "")).casefold()):
        source_path = str(entry.get("source_path", ""))
        source_id = str(entry.get("source_id", ""))
        status = str(entry.get("source_status", "unknown"))
        lines.extend([f"## {source_path}", "", f"- source_id: `{source_id}`", f"- source_status: `{status}`"])
        linked = pages_by_source.get(source_path, [])
        if linked:
            lines.append("- Reader 页面：")
            for page in linked:
                lines.append(f"  - [{page.title}]({page.relative_path})；page_type: `{PAGE_TYPE_LABELS[page.page_type]}`；[本页回查](#reader-page-{page.page_id})")
        else:
            lines.append(f"- Reader 页面：`{UNKNOWN}`")
        lines.extend(["", "### 原始证据坐标", ""])
        evidence = {item.evidence_id: item for page in linked for item in page.evidence.values() if item.source_path == source_path}
        for item in sorted(evidence.values(), key=lambda value: (value.line_start, value.line_end, value.evidence_id)):
            lines.append(f"- `{item.evidence_id}`：第 `{item.line_start}-{item.line_end}` 行；content_hash: `{item.audit_content_hash or item.content_hash}`")
        lines.append("")
    lines.extend(["## Reader 页面回查", ""])
    for page in sorted(pages, key=lambda item: item.relative_path):
        lines.extend([f"<a id=\"reader-page-{page.page_id}\"></a>", f"### {page.title}", "", f"- 页面：`{page.relative_path}`", f"- page_type: `{PAGE_TYPE_LABELS[page.page_type]}`", f"- 问题：{page.question}", f"- 模块：{page.module}", ""])
    return "\n".join(lines)


def _compile_aggregate_pages(
    batch_pages: Sequence[_BatchPage],
    *,
    cache: ModelCache,
    provider: object | None,
    model_id: str,
    prompt_version: str,
    used_paths: set[str],
) -> tuple[list[_ReaderPage], int, int, int, list[dict[str, Any]]]:
    """Compile a small set of cross-source answer pages for Home routes."""

    if provider is None:
        return [], 0, 0, 0, []
    pages: list[_ReaderPage] = []
    warnings: list[dict[str, Any]] = []
    provider_calls = 0
    cache_hits = 0
    provider_tokens = 0
    for spec in AGGREGATE_SPECS:
        terms = tuple(str(item).casefold() for item in spec["terms"])
        ranked: list[tuple[int, str, _BatchPage]] = []
        for page in batch_pages:
            haystack = " ".join((page.title, page.original_path, *page.source_paths)).casefold()
            score = sum(3 for term in terms if term in haystack)
            score += min(2, len(page.evidence) // 20)
            if score:
                ranked.append((score, page.original_path, page))
        selected = [row[2] for row in sorted(ranked, key=lambda row: (-row[0], row[1]))[:6]]
        if not selected:
            warnings.append({"aggregate": spec["slug"], "reason": "no_matching_sources"})
            continue
        source_paths = tuple(dict.fromkeys(path for page in selected for path in page.source_paths))
        evidence: list[_Evidence] = []
        seen: set[str] = set()
        for page in selected:
            for item in page.evidence:
                if item.evidence_id not in seen:
                    evidence.append(item)
                    seen.add(item.evidence_id)
                if len(evidence) >= 72:
                    break
            if len(evidence) >= 72:
                break
        if not evidence:
            warnings.append({"aggregate": spec["slug"], "reason": "no_evidence"})
            continue
        synthetic = _BatchPage(
            original_path=f"aggregate/{spec['slug']}.md",
            product="shared",
            source_paths=source_paths,
            source_ids=tuple(dict.fromkeys(source_id for page in selected for source_id in page.source_ids)),
            title=str(spec["title"]),
            raw_text=f"固定页面类型：{spec['page_type']}\n问题：{spec['question']}",
            evidence=tuple(evidence),
        )
        topic = f"reader-answer:{spec['slug']}"
        members = [item.cache_member(topic, index) for index, item in enumerate(evidence)]
        try:
            cached = cache.get_or_call(
                model_id=model_id,
                prompt_version=f"{prompt_version}-aggregate-v1",
                topic_map_version=READER_TOPIC_MAP_VERSION,
                topic_key=topic,
                members=members,
                provider=lambda synthetic=synthetic: _normalise_provider_result(
                    _call_provider(provider, _prompt(synthetic, synthetic.evidence)),
                    synthetic,
                    synthetic.evidence,
                ),
                allow_provider=True,
            )
            draft = _normalise_draft(cached.result, synthetic, synthetic.evidence)
            if draft["page_type"] != spec["page_type"]:
                raise ReaderProjectionError(f"aggregate page_type mismatch: {draft['page_type']}")
            page = _page_from_draft(synthetic, draft, synthetic.evidence, str(spec["slug"]))
            if page.relative_path in used_paths:
                warnings.append({"aggregate": spec["slug"], "reason": "path_collision"})
                continue
            used_paths.add(page.relative_path)
            pages.append(page)
            if cached.called:
                provider_calls += 1
            if cached.hit:
                cache_hits += 1
            provider_tokens += int(cached.result.get("provider_tokens", 0)) if isinstance(cached.result.get("provider_tokens", 0), int) else 0
        except (CacheIntegrityError, ReaderProjectionError, ReaderProviderUnavailable) as error:
            warnings.append({"aggregate": spec["slug"], "reason": "aggregate_compile_failed", "cause": str(error)})
    return pages, provider_calls, cache_hits, provider_tokens, warnings


def _write_candidate(
    candidate: Path,
    pages: Sequence[_ReaderPage],
    source_snapshot: Mapping[str, Any],
    k1_manifest: Mapping[str, Any],
    *,
    provider_calls: int,
    cache_hits: int,
    provider_tokens: int,
    warnings: Sequence[Mapping[str, Any]] = (),
) -> None:
    candidate.mkdir(parents=True, exist_ok=True)
    by_product: dict[str, list[_ReaderPage]] = defaultdict(list)
    for page in pages:
        by_product[page.product].append(page)
        target = candidate / page.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_render_page(page), encoding="utf-8")
    (candidate / "Home.md").write_text(_render_home(pages, len(source_snapshot.get("entries", ()))), encoding="utf-8")
    (candidate / "Index.md").write_text(_render_index(pages), encoding="utf-8")
    for product, rows in by_product.items():
        target = candidate / "products" / product / "index.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_render_product_index(product, rows), encoding="utf-8")
    (candidate / "Audit.md").write_text(_render_audit(pages, source_snapshot, "candidate"), encoding="utf-8")
    reader_rows: list[dict[str, Any]] = []
    for page in pages:
        for surface, refs in page.evidence_by_surface.items():
            for ref in refs:
                item = page.evidence.get(ref)
                if item is not None:
                    reader_rows.append(item.as_audit(page.relative_path, surface))
        if not any(page.evidence_by_surface.values()) and page.evidence:
            # A sparse source may not support a semantic sentence. Preserve a
            # source-presence audit row so K3 can prove where the page came
            # from without pretending that the unknown sections are facts.
            first = next(iter(page.evidence.values()))
            reader_rows.append(first.as_audit(page.relative_path, "source_presence"))
    unique_rows: dict[tuple[object, ...], dict[str, Any]] = {}
    for row in reader_rows:
        key = (
            row.get("page_path"),
            row.get("claim_id"),
            row.get("source_path"),
            row.get("line_start"),
            row.get("line_end"),
            row.get("content_hash"),
        )
        unique_rows.setdefault(key, row)
    reader_rows = list(unique_rows.values())
    reader_rows.sort(key=lambda row: (str(row["page_path"]).encode("utf-8"), str(row["source_path"]).encode("utf-8"), int(row["line_start"]), str(row["claim_id"])))
    _jsonl(candidate / "_audit/sources.jsonl", reader_rows)
    _jsonl(candidate / "_audit/reference-blocks.jsonl", [])
    source_id_by_path = {
        str(entry.get("source_path")): str(entry.get("source_id"))
        for entry in source_snapshot.get("entries", ())
        if isinstance(entry, Mapping) and entry.get("source_path") and entry.get("source_id")
    }
    source_ledger = []
    for entry in source_snapshot.get("entries", ()) if isinstance(source_snapshot.get("entries"), list) else ():
        if not isinstance(entry, Mapping):
            continue
        source_path = str(entry.get("source_path", ""))
        source_ledger.append({
            "content_hash": entry.get("content_hash"),
            "pages": sorted({page.relative_path for page in pages if source_path in page.source_paths}),
            "source_path": source_path,
            "source_status": entry.get("expected_status", "ready"),
        })
    manifest_pages: list[dict[str, Any]] = [
        {
            "page_path": page.relative_path,
            "page_paths": [page.relative_path],
            "source_paths": list(page.source_paths),
            "source_ids": [source_id_by_path[path] for path in page.source_paths if path in source_id_by_path],
            "topic_key": page.page_id,
        }
        for page in pages
    ]
    manifest_pages.extend({"page_path": name, "page_paths": [name], "source_paths": [], "topic_key": name} for name in ("Home.md", "Index.md", "Audit.md"))
    manifest = {
        "schema_version": "task7-page-manifest.v1",
        "attempt_id": f"reader-{k1_manifest.get('attempt_id', 'unknown')}",
        "run_status": "complete",
        "publish_status": "not_released",
        "blockers": [],
        "pages": manifest_pages,
        "source_ledger": source_ledger,
        "source_snapshot": dict(source_snapshot),
        "navigation": {"navigation_status": "generated_ok", "success_pages": len(pages), "blocked_sources": 0, "blocked_reasons": []},
        "reader_surface": {"schema_version": "task10-reader-surface.v1", "status": "candidate", "page_types": sorted(set(page.page_type for page in pages)), "raw_k1_manifest": "_audit/k1/page-manifest.json"},
    }
    _json(candidate / "_audit/page-manifest.json", manifest)
    _json(candidate / "_audit/reader-manifest.json", {
        "schema_version": "task10-reader-manifest.v1",
        "status": "candidate",
        "generated_at": _now(),
        "source_count": len(source_snapshot.get("entries", ())),
        "reader_page_count": len(pages),
        "provider_calls": provider_calls,
        "cache_hits": cache_hits,
        "provider_tokens": provider_tokens,
        "k1_attempt_id": k1_manifest.get("attempt_id"),
        "page_ids": [page.page_id for page in pages],
        "warnings": [dict(item) for item in warnings],
    })
    _json(candidate / "_audit/run-metrics.json", {
        "elapsed_ms": 0,
        "provider_calls": provider_calls,
        "provider_tokens": provider_tokens,
        "cache_hits": cache_hits,
        "planned_provider_calls": len(pages),
        "actual_provider_calls": provider_calls,
        "reasons": {
            "elapsed_ms": "no_provider_call_yet",
            **({"provider_calls": "no_provider_call_yet"} if not provider_calls else {}),
            **({"provider_tokens": "no_provider_call_yet"} if not provider_tokens else {}),
        },
        "reader_projection": {"provider_calls": provider_calls, "cache_hits": cache_hits, "provider_tokens": provider_tokens},
    })
    (candidate / "README.md").write_text(
        "# KnowledgeDigest Reader candidate\n\n"
        "这是 K3 发布前的 Reader candidate。K1/K2 原始批次和完整审计事实位于 `_audit/k1/`；本目录只有经过语义投影的用户阅读层。\n\n"
        "- reader_status: `candidate`\n"
        "- publish_status: `not_released`\n"
        f"- source_count: `{len(source_snapshot.get('entries', ()))}`\n"
        f"- reader_page_count: `{len(pages)}`\n",
        encoding="utf-8",
    )


def _seed_tree_hash(root: Path) -> str:
    """Hash a verified Reader seed without trusting its old receipt."""

    rows: list[bytes] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        if path.is_symlink():
            raise ReaderProjectionError(f"Reader seed contains a symbolic link: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            rows.append(f"{relative}:{_sha(path.read_bytes())}\n".encode("utf-8"))
    return _sha(b"".join(rows))


def _frontmatter_bounds(text: str) -> tuple[int, int] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return 0, index
    return None


def _seed_page_metadata(text: str, relative_path: str, *, input_root: Path | None = None) -> str:
    """Add the stable K3 managed-page fields while preserving seed content."""

    bounds = _frontmatter_bounds(text)
    citations = _seed_citations(text)
    source_paths = tuple(dict.fromkeys(source for source, _start, _end in citations))
    page_id = "seed-" + _sha(relative_path)[:20]
    if bounds is None:
        frontmatter = _frontmatter(
            {
                "managed_by": "KnowledgeDigest",
                "digest_kind": "topic",
                "digest_topic_id": page_id,
                "digest_published_path": relative_path,
                "digest_part": 1,
            }
        ).rstrip("\n")
        return frontmatter + "\n\n" + _seed_reader_structure(text.lstrip())
    start, end = bounds
    rows = text.splitlines()
    existing: dict[str, str] = {}
    for line in rows[start + 1 : end]:
        key, separator, value = line.partition(":")
        if separator and key.strip():
            existing[key.strip()] = value.strip()
    raw_page_id = existing.get("digest_page_id") or existing.get("digest_topic_id")
    if raw_page_id:
        page_id = raw_page_id.strip("'\"")
    page_type = existing.get("page_type", "概念").strip("'\"")
    type_map = {"定位": "product-copy", "概念": "concept", "操作": "operation", "诊断": "diagnosis", "经验": "experience"}
    product = existing.get("product", "KnowledgeDigest").strip("'\"")
    module = existing.get("module", existing.get("section", "未分类模块")).strip("'\"")
    h1 = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), relative_path.rsplit("/", 1)[-1].removesuffix(".md"))
    raw_dates: list[str] = []
    if input_root is not None:
        for source_path in source_paths:
            source = input_root / PurePosixPath(source_path)
            if source.is_file() and not source.is_symlink():
                raw_dates.append(datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).date().isoformat())
    additions = {
        "title": h1,
        "type": type_map.get(page_type, "concept"),
        "page_model": "derived",
        "scope": "company",
        "section": module,
        "tier": 2,
        "trust": "medium",
        "source_status": "compiled",
        "quality_status": "machine_passed",
        "generated_by": "knowledge_digest_reader_projection.py",
        "tags": ["company", product, module],
        "source": "; ".join(source_paths),
        **({"created": min(raw_dates), "updated": max(raw_dates)} if raw_dates else {}),
        "managed_by": "KnowledgeDigest",
        "digest_kind": "topic",
        "digest_topic_id": page_id,
        "digest_published_path": relative_path,
        "digest_part": 1,
        "source_status": "reader",
        "quality_status": "machine_passed",
    }
    missing = [f"{key}: {_frontmatter_value(value)}" for key, value in additions.items() if key not in existing]
    if missing:
        rows[end:end] = missing
    return "\n".join(rows[: end + len(missing) + 1]).rstrip() + "\n\n" + _seed_reader_structure(
        "\n".join(rows[end + len(missing) + 1 :]).lstrip()
    )


def _seed_reader_structure(text: str) -> str:
    """Expose the formal Reader contract without rewriting seed prose."""

    rows = text.splitlines()
    citation_rows = _seed_citations(text)
    if not any(line.strip() == "## Summary" for line in rows):
        summary_index = next((index for index, line in enumerate(rows) if line.startswith("> ") and not line.startswith("> 证据")), None)
        if summary_index is not None:
            rows[summary_index:summary_index] = ["## Summary", ""]
    if not any(line.strip() == "## Evidence" for line in rows):
        question_index = next((index for index, line in enumerate(rows) if line.strip() == "## 这页解决什么问题"), None)
        if question_index is not None:
            rows[question_index:question_index] = [
                "## Evidence",
                "",
                f"本页正文绑定当前资料中的 {len(citation_rows)} 个证据片段；每条证据均可回查到原文行号。",
                "",
            ]
    grouped: dict[str, list[str]] = defaultdict(list)
    for source_path, start, end in citation_rows:
        grouped[source_path].append(f"{start}-{end}" if start != end else str(start))
    provenance = [
        "## Provenance",
        "",
        "本页只列出当前页面实际引用的原始资料，不包含其他模块或全局审计文件。",
        "",
        "| 原始资料 | 引用行 |",
        "| --- | --- |",
    ]
    if grouped:
        provenance.extend(
            f"| `{source_path}` | `{', '.join(dict.fromkeys(ranges))}` |"
            for source_path, ranges in sorted(grouped.items())
        )
    else:
        provenance.append("| 原始资料未明确 | — |")
    provenance.append("")
    provenance_index = next((index for index, line in enumerate(rows) if line.strip() == "## Provenance"), None)
    source_index = next((index for index, line in enumerate(rows) if line.strip() == "## 来源"), None)
    if provenance_index is not None:
        end = next((index for index in range(provenance_index + 1, len(rows)) if rows[index].startswith("## ")), len(rows))
        rows[provenance_index:end] = provenance
    elif source_index is not None:
        end = next((index for index in range(source_index + 1, len(rows)) if rows[index].startswith("## ")), len(rows))
        rows[source_index:end] = provenance
    else:
        related_index = next((index for index, line in enumerate(rows) if line.strip() == "## 相关入口"), len(rows))
        rows[related_index:related_index] = provenance
    return "\n".join(rows).rstrip() + "\n"


def _seed_citations(text: str) -> list[tuple[str, int, int]]:
    citations: list[tuple[str, int, int]] = []
    pattern = re.compile(r"`([^`]+)`\s*第\s*([^`]+?)\s*行")
    for match in pattern.finditer(text):
        source_path = match.group(1).strip().replace("\\", "/")
        for token in re.findall(r"\d+\s*-\s*\d+|\d+", match.group(2)):
            if "-" in token:
                start_text, end_text = re.split(r"\s*-\s*", token, maxsplit=1)
                start, end = int(start_text), int(end_text)
            else:
                start = end = int(token)
            citations.append((source_path, start, end))
    return citations


def _seed_audit_rows(
    seed: Path,
    current_rows: Sequence[Mapping[str, Any]],
    reference_rows: Sequence[Mapping[str, Any]],
    input_root: Path,
    page_path: str,
    page_text: str,
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in (*current_rows, *reference_rows):
        source_path = row.get("source_path")
        if isinstance(source_path, str):
            by_source[source_path.replace("\\", "/")].append(row)
    result: list[dict[str, Any]] = []
    source_paths: list[str] = []
    for source_path, start, end in _seed_citations(page_text):
        relative = PurePosixPath(source_path)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise ReaderProjectionError(f"Reader seed citation path is unsafe: {source_path}")
        raw_source = input_root.joinpath(*relative.parts)
        if raw_source.is_symlink() or not raw_source.is_file():
            raise ReaderProjectionError(f"Reader seed citation source is missing: {source_path}")
        lines = raw_source.read_text(encoding="utf-8").splitlines()
        if start < 1 or end < start or end > len(lines):
            raise ReaderProjectionError(f"Reader seed citation line range is invalid: {source_path}:{start}-{end}")
        span = "\n".join(lines[start - 1 : end])
        candidates = [
            row
            for row in by_source.get(source_path, ())
            if isinstance(row.get("line_start"), int)
            and isinstance(row.get("line_end"), int)
            and row["line_start"] <= start
            and row["line_end"] >= end
            and row.get("status") in {"sourced", "ready"}
        ]
        candidates.sort(key=lambda row: (int(row.get("line_end", 10**9)) - int(row.get("line_start", 0)), str(row.get("claim_id", row.get("block_id", "")))))
        bound = candidates[0] if candidates else {}
        claim_id = str(bound.get("claim_id") or bound.get("block_id") or "seed-" + _sha(f"{source_path}\0{start}\0{end}")[:20])
        source_block_id = str(bound.get("source_block_id") or bound.get("block_id") or "") or None
        result.append(
            {
                "claim_id": claim_id,
                "claim_kind": "narrative",
                "content_hash": _sha(span + "\n"),
                "line_start": start,
                "line_end": end,
                "page_anchor": "reader",
                "page_path": page_path,
                "reader_surface": "seed-citation",
                "source_block_id": source_block_id,
                "source_path": source_path,
                "source_uri": source_path,
                "span_start": 0,
                "span_end": len(span),
                "status": "sourced",
                "text": span,
            }
        )
        source_paths.append(source_path)
    return result, tuple(dict.fromkeys(source_paths))


def promote_reader_seed(
    seed_dir: str | Path,
    batch_dir: str | Path,
    output_dir: str | Path,
    *,
    input_root: str | Path,
) -> ReaderProjectionResult:
    """Promote a same-corpus semantic Reader seed into the current K3 chain.

    This is a recovery seam for the K4 regression: it accepts a prior Reader
    semantic surface only after checking every one of the 89 raw source hashes
    against the current K1 snapshot.  It then rebuilds the K3 audit rows from
    the current frozen input, copies the current K1/K2 audit under ``k1``, and
    writes a fresh K3 manifest.  Old seed receipts are not trusted as current
    release or acceptance facts.
    """

    seed = Path(seed_dir).expanduser().resolve()
    batch = Path(batch_dir).expanduser().resolve()
    candidate = Path(output_dir).expanduser().resolve()
    raw_input = Path(input_root).expanduser().resolve()
    if seed.is_symlink() or not seed.is_dir():
        raise ReaderProjectionError("Reader seed must be a real directory")
    manifest, _batch_pages, source_snapshot = _load_batch(batch, input_root=raw_input)
    seed_status = _read_json(seed / "_audit/source-status.json")
    seed_entries = seed_status.get("sources") if isinstance(seed_status, Mapping) else None
    if not isinstance(seed_entries, list):
        raise ReaderProjectionError("Reader seed source-status is missing")
    current_entries = {
        str(entry.get("source_path")): str(entry.get("content_hash"))
        for entry in source_snapshot.get("entries", ())
        if isinstance(entry, Mapping) and entry.get("source_path") and entry.get("content_hash")
    }
    seed_hashes = {
        str(entry.get("relative_path")): str(entry.get("raw_hash"))
        for entry in seed_entries
        if isinstance(entry, Mapping) and entry.get("relative_path") and entry.get("raw_hash")
    }
    if seed_hashes != current_entries:
        raise ReaderProjectionError("Reader seed source hashes do not match the current K1 snapshot")
    if candidate.exists():
        if candidate.is_symlink() or not candidate.is_dir():
            raise ReaderProjectionError("Reader seed candidate path is not a real directory")
        shutil.rmtree(candidate)
    candidate.mkdir(parents=True, exist_ok=True)
    _copy_audit(batch, candidate)
    for name in ("Home.md", "Index.md", "Audit.md"):
        source = seed / name
        if name == "Index.md" and not source.exists():
            product_indexes = sorted(
                path.relative_to(seed).as_posix()
                for path in seed.glob("products/*/index.md")
                if path.is_file() and not path.is_symlink()
            )
            generated_index = "# 知识索引\n\n按产品进入 Reader。\n\n" + "\n".join(
                f"- [{PurePosixPath(path).parent.name}]({path})" for path in product_indexes
            ) + "\n"
            (candidate / name).write_text(generated_index, encoding="utf-8")
            continue
        if not source.is_file() or source.is_symlink():
            raise ReaderProjectionError(f"Reader seed file is missing: {name}")
        (candidate / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    for source in sorted(seed.glob("products/**/*.md"), key=lambda item: item.relative_to(seed).as_posix().encode("utf-8")):
        if source.is_symlink() or not source.is_file():
            raise ReaderProjectionError(f"Reader seed contains an invalid page: {source}")
        relative = source.relative_to(seed).as_posix()
        target = candidate / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source_text = source.read_text(encoding="utf-8")
        target.write_text(
            source_text if relative.endswith("/index.md") else _seed_page_metadata(source_text, relative, input_root=raw_input),
            encoding="utf-8",
        )
    current_rows = _read_jsonl(batch / "_audit/sources.jsonl")
    reference_rows = _read_jsonl(batch / "_audit/reference-blocks.jsonl")
    source_id_by_path = {
        str(entry.get("source_path")): str(entry.get("source_id"))
        for entry in source_snapshot.get("entries", ())
        if isinstance(entry, Mapping) and entry.get("source_path") and entry.get("source_id")
    }
    reader_rows: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    page_types: set[str] = set()
    for page_file in sorted(candidate.glob("products/**/*.md"), key=lambda item: item.relative_to(candidate).as_posix().encode("utf-8")):
        relative = page_file.relative_to(candidate).as_posix()
        if relative.endswith("/index.md"):
            continue
        page_text = page_file.read_text(encoding="utf-8")
        rows, source_paths = _seed_audit_rows(seed, current_rows, reference_rows, raw_input, relative, page_text)
        if not rows:
            raise ReaderProjectionError(f"Reader seed page has no evidence citations: {relative}")
        reader_rows.extend(rows)
        frontmatter = _frontmatter_bounds(page_text)
        page_id = "seed-" + _sha(relative)[:20]
        page_type = "concept"
        if frontmatter is not None:
            for line in page_text.splitlines()[frontmatter[0] + 1 : frontmatter[1]]:
                key, separator, value = line.partition(":")
                if separator and key.strip() == "digest_topic_id":
                    page_id = value.strip().strip("'\"") or page_id
                if separator and key.strip() == "page_type":
                    label = value.strip().strip("'\"")
                    page_type = next((key for key, item in PAGE_TYPE_LABELS.items() if item == label), label)
        page_types.add(page_type)
        pages.append({
            "page_path": relative,
            "page_paths": [relative],
            "source_paths": list(source_paths),
            "source_ids": [source_id_by_path[path] for path in source_paths if path in source_id_by_path],
            "topic_key": page_id,
        })
    unique_rows: dict[tuple[object, ...], dict[str, Any]] = {}
    for row in reader_rows:
        key = (row["page_path"], row["claim_id"], row["source_path"], row["line_start"], row["line_end"], row["content_hash"])
        unique_rows.setdefault(key, row)
    reader_rows = sorted(unique_rows.values(), key=lambda row: (str(row["page_path"]).encode("utf-8"), str(row["source_path"]).encode("utf-8"), int(row["line_start"]), str(row["claim_id"])))
    _jsonl(candidate / "_audit/sources.jsonl", reader_rows)
    _jsonl(candidate / "_audit/reference-blocks.jsonl", [])
    for name in ("Home.md", "Index.md", "Audit.md"):
        pages.append({"page_path": name, "page_paths": [name], "source_paths": [], "source_ids": [], "topic_key": name})
    source_ledger = [
        {
            "content_hash": entry.get("content_hash"),
            "pages": sorted({page["page_path"] for page in pages if str(entry.get("source_path")) in page.get("source_paths", [])}),
            "source_path": entry.get("source_path"),
            "source_status": entry.get("expected_status", "ready"),
        }
        for entry in source_snapshot.get("entries", ())
        if isinstance(entry, Mapping)
    ]
    seed_hash = _seed_tree_hash(seed)
    _json(candidate / "_audit/seed-binding.json", {
        "schema_version": "task10-reader-seed-binding.v1",
        "seed_tree_sha256": seed_hash,
        "source_count": len(current_entries),
        "source_hashes_match_current_k1": True,
    })
    _json(candidate / "_audit/page-manifest.json", {
        "schema_version": "task7-page-manifest.v1",
        "attempt_id": f"reader-seed-{manifest.get('attempt_id', 'unknown')}",
        "run_status": "complete",
        "publish_status": "not_released",
        "blockers": [],
        "pages": pages,
        "source_ledger": source_ledger,
        "source_snapshot": dict(source_snapshot),
        "navigation": {"navigation_status": "generated_ok", "success_pages": len(pages) - 3, "blocked_sources": 0, "blocked_reasons": []},
        "reader_surface": {
            "schema_version": "task10-reader-surface.v1",
            "status": "machine_passed",
            "page_types": sorted(page_types),
            "raw_k1_manifest": "_audit/k1/page-manifest.json",
            "semantic_seed_binding": "_audit/seed-binding.json",
        },
    })
    _json(candidate / "_audit/reader-manifest.json", {
        "schema_version": "task10-reader-manifest.v1",
        "status": "machine_passed",
        "publish_status": "not_released",
        "generated_at": _now(),
        "source_count": len(current_entries),
        "reader_page_count": len(pages) - 3,
        "provider_calls": 0,
        "cache_hits": 0,
        "provider_tokens": 0,
        "k1_attempt_id": manifest.get("attempt_id"),
        "projection_mode": "verified_seed_promotion",
        "seed_tree_sha256": seed_hash,
        "page_ids": [page["topic_key"] for page in pages if page["page_path"].startswith("products/") and not page["page_path"].endswith("/index.md")],
    })
    _json(candidate / "_audit/run-metrics.json", {
        "elapsed_ms": 0,
        "provider_calls": 0,
        "provider_tokens": 0,
        "cache_hits": 0,
        "planned_provider_calls": 0,
        "actual_provider_calls": 0,
        "reasons": {"elapsed_ms": "no_provider_call_yet", "provider_calls": "no_provider_call_yet", "provider_tokens": "no_provider_call_yet"},
        "reader_projection": {"provider_calls": 0, "cache_hits": 0, "provider_tokens": 0, "projection_mode": "verified_seed_promotion"},
    })
    (candidate / "README.md").write_text(
        "# KnowledgeDigest Reader\n\n"
        "这是 K3 Reader 用户知识层。语义正文复用已绑定到同一 89 条原文哈希的 Reader seed；本次重新生成 K3 manifest、证据坐标和 K1/K2 审计绑定。发布版本与原子切换记录由知识库旁的 K3 release receipt 管理。\n\n"
        "- reader_status: `machine_passed`\n- publish_status: `release-receipt-bound`\n"
        f"- source_count: `{len(current_entries)}`\n- reader_page_count: `{len(pages) - 3}`\n",
        encoding="utf-8",
    )
    return ReaderProjectionResult(candidate, "candidate", "not_released", len(current_entries), len(pages) - 3, 0, 0, 0)


def _write_blocked_candidate(candidate: Path, reason: str, k1_manifest: Mapping[str, Any], source_snapshot: Mapping[str, Any]) -> None:
    candidate.mkdir(parents=True, exist_ok=True)
    _json(candidate / "_audit/page-manifest.json", {
        "schema_version": "task7-page-manifest.v1",
        "attempt_id": f"reader-{k1_manifest.get('attempt_id', 'unknown')}",
        "run_status": "blocked",
        "publish_status": "not_released",
        "blockers": [{"reason": "reader_projection_failed", "cause": reason}],
        "pages": [],
        "source_ledger": [],
        "source_snapshot": dict(source_snapshot),
        "navigation": {"navigation_status": "blocked", "success_pages": 0, "blocked_sources": len(source_snapshot.get("entries", ())), "blocked_reasons": [reason]},
        "reader_surface": {"schema_version": "task10-reader-surface.v1", "status": "blocked"},
    })
    _json(candidate / "_audit/reader-manifest.json", {"schema_version": "task10-reader-manifest.v1", "status": "blocked", "reason": reason, "k1_attempt_id": k1_manifest.get("attempt_id")})
    (candidate / "README.md").write_text(f"# KnowledgeDigest Reader candidate\n\n状态：`blocked`\n\n- 原因：{reason}\n- publish_status: `not_released`\n", encoding="utf-8")


def compile_reader_candidate(
    batch_dir: str | Path,
    output_dir: str | Path | None = None,
    *,
    provider: object | None = None,
    cache_root: str | Path | None = None,
    input_root: str | Path | None = None,
    force: bool = False,
    model_id: str = READER_MODEL_ID,
    prompt_version: str = READER_PROMPT_VERSION,
) -> ReaderProjectionResult:
    """Compile one complete K1/K2 batch into an isolated Reader candidate."""

    batch = Path(batch_dir).expanduser().resolve()
    candidate = Path(output_dir).expanduser().resolve() if output_dir is not None else batch / "_reader-candidate"
    raw_input_root = Path(input_root).expanduser().resolve() if input_root is not None else None
    manifest, batch_pages, source_snapshot = _load_batch(batch, input_root=raw_input_root)
    if candidate.exists():
        if candidate.is_symlink() or not candidate.is_dir():
            raise ReaderProjectionError("Reader candidate path is not a real directory")
        existing = candidate / "_audit/reader-manifest.json"
        if existing.is_file():
            value = _read_json(existing)
            if not force and isinstance(value, Mapping) and value.get("status") == "candidate" and value.get("k1_attempt_id") == manifest.get("attempt_id"):
                return ReaderProjectionResult(candidate, "candidate", "not_released", len(source_snapshot.get("entries", ())), int(value.get("reader_page_count", 0)), int(value.get("provider_calls", 0)), int(value.get("cache_hits", 0)), int(value.get("provider_tokens", 0)))
        shutil.rmtree(candidate)
    candidate.mkdir(parents=True, exist_ok=True)
    _copy_audit(batch, candidate)
    cache = ModelCache(cache_root or (batch / "_reader-cache"))
    reader_pages: list[_ReaderPage] = []
    blockers: list[dict[str, Any]] = []
    provider_calls = 0
    cache_hits = 0
    provider_tokens = 0
    aggregate_warnings: list[dict[str, Any]] = []
    used_paths: set[str] = set()
    for page in batch_pages:
        if not page.evidence:
            blockers.append({"page_path": page.original_path, "reason": "reader_evidence_missing"})
            continue
        topic_key = f"reader:{page.original_path}"
        value: Mapping[str, Any] | None = None
        last_error = ""
        for attempt in range(2):
            cache_topic_key = topic_key if attempt == 0 else f"{topic_key}:repair-v2"
            cache_prompt_version = prompt_version if attempt == 0 else f"{prompt_version}-repair-v2"
            members = [item.cache_member(cache_topic_key, index) for index, item in enumerate(page.evidence)]
            feedback = f"\n上一次结果无效，请修正：{last_error}\n" if last_error else ""
            try:
                cached = cache.get_or_call(
                    model_id=model_id,
                    prompt_version=cache_prompt_version,
                    topic_map_version=READER_TOPIC_MAP_VERSION,
                    topic_key=cache_topic_key,
                    members=members,
                    provider=lambda page=page, feedback=feedback: _normalise_provider_result(_call_provider(provider, _prompt(page, page.evidence, feedback)), page, page.evidence),
                    allow_provider=provider is not None,
                )
                value = cached.result
                # Cache hits must pass the same final Reader contract as fresh
                # provider responses. A pre-repair cache entry with no usable
                # citation therefore takes the repair namespace on attempt 2.
                _normalise_draft(value, page, page.evidence)
                if cached.called:
                    provider_calls += 1
                if cached.hit:
                    cache_hits += 1
                provider_tokens += int(value.get("provider_tokens", 0)) if isinstance(value.get("provider_tokens", 0), int) else 0
                break
            except (CacheIntegrityError, ReaderProjectionError, ReaderProviderUnavailable) as error:
                last_error = str(error)
                if isinstance(error, CacheIntegrityError) and error.provider_called:
                    provider_calls += 1
                if isinstance(error, ReaderProviderUnavailable):
                    break
        if value is None:
            blockers.append({"page_path": page.original_path, "reason": "reader_provider_failed", "cause": last_error})
            continue
        try:
            draft = _normalise_draft(value, page, page.evidence)
            base = _safe_slug(str(draft["title"]), _safe_slug(page.title, "page"))
            slug = base
            index = 2
            while f"products/{page.product}/{draft['page_type']}/{slug}.md" in used_paths:
                slug = f"{base}-{index}"
                index += 1
            target = f"products/{page.product}/{draft['page_type']}/{slug}.md"
            used_paths.add(target)
            reader_pages.append(_page_from_draft(page, draft, page.evidence, slug))
        except ReaderProjectionError as error:
            blockers.append({"page_path": page.original_path, "reason": "reader_contract_failed", "cause": str(error)})
    source_page_count = len(reader_pages)
    aggregate_pages, aggregate_calls, aggregate_hits, aggregate_tokens, aggregate_warnings = _compile_aggregate_pages(
        batch_pages,
        cache=cache,
        provider=provider,
        model_id=model_id,
        prompt_version=prompt_version,
        used_paths=used_paths,
    )
    reader_pages.extend(aggregate_pages)
    provider_calls += aggregate_calls
    cache_hits += aggregate_hits
    provider_tokens += aggregate_tokens
    if blockers or source_page_count != len(batch_pages):
        reason = f"{len(blockers)} Reader pages failed semantic projection"
        _write_blocked_candidate(candidate, reason, manifest, source_snapshot)
        return ReaderProjectionResult(candidate, "blocked", "not_released", len(source_snapshot.get("entries", ())), len(reader_pages), provider_calls, cache_hits, provider_tokens, tuple(blockers))
    for page in reader_pages:
        rendered = _render_page(page)
        if len(rendered.splitlines()) > MAX_PAGE_LINES:
            blockers.append({"page_path": page.relative_path, "reason": "reader_page_over_300_lines"})
    if blockers:
        reason = f"{len(blockers)} Reader pages failed final surface validation"
        _write_blocked_candidate(candidate, reason, manifest, source_snapshot)
        return ReaderProjectionResult(candidate, "blocked", "not_released", len(source_snapshot.get("entries", ())), len(reader_pages), provider_calls, cache_hits, provider_tokens, tuple(blockers))
    _write_candidate(
        candidate,
        reader_pages,
        source_snapshot,
        manifest,
        provider_calls=provider_calls,
        cache_hits=cache_hits,
        provider_tokens=provider_tokens,
        warnings=aggregate_warnings,
    )
    return ReaderProjectionResult(candidate, "candidate", "not_released", len(source_snapshot.get("entries", ())), len(reader_pages), provider_calls, cache_hits, provider_tokens)


def _normalise_provider_result(value: Mapping[str, Any], page: _BatchPage, evidence: Sequence[_Evidence]) -> dict[str, Any]:
    # Validate and return the cacheable form before ModelCache writes it.  A
    # malformed provider response therefore cannot poison a future retry.
    draft = _normalise_draft(value, page, evidence)
    return {
        "title": draft["title"],
        "question": draft["question"],
        "page_type": draft["page_type"],
        "module": draft["module"],
        "object": draft["object"],
        "scenario": draft["scenario"],
        "boundary": draft["boundary"],
        "summary": draft["summary"],
        "sections": {key: list(values) for key, values in draft["sections"].items()},
        "evidence": {key: list(values) for key, values in draft["evidence"].items()},
        "provider_tokens": int(value.get("provider_tokens", 0)) if isinstance(value.get("provider_tokens", 0), int) else 0,
    }


__all__ = [
    "MAX_PAGE_LINES",
    "PAGE_TYPES",
    "ReaderProjectionResult",
    "compile_reader_candidate",
    "promote_reader_seed",
]
