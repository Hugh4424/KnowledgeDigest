#!/usr/bin/env python3
"""Generate the 89-case content oracle from frozen source facts.

The evaluator must not use the placeholder ``用途/限制`` pair.  This script
derives short lexical anchors from each source title/body and, when a unique
CompanyBrain counterpart exists, keeps only boundary anchors present on both
sides.  It is deterministic, offline, and records the source hash used to
produce the matrix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping

from knowledge_digest.companybrain_mapping import semantic_fields


_GENERIC = {
    "数据", "数据集", "设备", "应用", "配置", "管理", "系统", "页面", "文档",
    "服务", "功能", "操作", "问题", "方案", "企业", "模块", "信息", "设置",
    "列表", "内容", "使用", "支持", "方法", "字段", "规则", "相关", "说明", "细节", "要点", "能力", "核心", "通过", "的来", "type",
    "goinsight", "emm", "airviewer", "maxstore", "android", "ios",
    "http", "https", "www", "jira", "confluence", "com",
}
_BOUNDARY_MARKERS = ("不支持", "不能", "至少", "最多", "必须", "默认", "仅支持", "限制", "边界", "条件", "权限", "依赖", "失败", "异常")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize(value: Any) -> str:
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    value = re.sub(r"^\s*(?:\[?ae\]?|emm)\s*[-_:：]?\s*", "", value, flags=re.I)
    value = re.sub(r"^\s*\d+[.)、]?\s*", "", value)
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)


def _chunks(value: Any) -> list[str]:
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    normalized = re.sub(r"^\s*(?:\[?ae\]?|emm)\s*[-_:：]?\s*", "", normalized, flags=re.I)
    normalized = re.sub(r"^\s*\d+[.)、]?\s*", "", normalized)
    result: list[str] = []
    for chunk in re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]+", normalized):
        if re.fullmatch(r"[a-z0-9]+", chunk):
            result.append(chunk)
        else:
            result.extend(chunk[index:index + 2] for index in range(0, len(chunk) - 1, 2))
    return [term for term in result if term not in _GENERIC and len(term) >= 2]


def _source_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            title = re.sub(r"[*_`~]", "", match.group(1)).strip()
            title = re.sub(r"^\d+[.)、]?\s*", "", title).strip()
            if title and not re.match(r"^(?:目录|文档目录|document directory|背景介绍|文档更新历史|[・·•].*|q\s*&?\s*a|问答)$", title, re.I):
                return title
    return fallback


def _body_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)、]\s+)", "", raw).strip()
        if not line or line.startswith("#") or line.startswith("|") or line.startswith("!"):
            continue
        if re.match(r"^(?:来源|蓝湖链接|目录|文档修订记录|更新时间|作者)\s*[:：]", line, re.I):
            continue
        if len(line) < 4:
            continue
        lines.append(line)
    return lines


def _claim_terms(title: str, text: str, baseline_text: str | None) -> list[str]:
    title_terms = list(dict.fromkeys(_chunks(title)))
    body_terms = list(dict.fromkeys(term for line in _body_lines(text)[:8] for term in _chunks(line)))
    # The oracle is source-first.  It must not be weakened until both sides
    # happen to contain the same words; missing source facts are exactly how
    # the comparison detects a weaker baseline or a lossy candidate.
    terms = title_terms or body_terms
    terms = list(dict.fromkeys(terms))
    if len(terms) < 2:
        terms.extend(term for term in body_terms if term not in terms)
    return terms[:3] or ["内容"]


def _boundary_terms(text: str, baseline_text: str | None) -> list[str]:
    present = [marker for marker in _BOUNDARY_MARKERS if marker in text]
    return list(dict.fromkeys((present[:2] if present else ["来源"])))


def _read_mapping(path: Path) -> dict[str, Mapping[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return {str(row.get("case_id")): row for row in value.get("cases", []) if isinstance(row, Mapping)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic Task4 case claims/boundaries")
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--case-matrix", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--companybrain", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    matrix = json.loads(args.case_matrix.read_text(encoding="utf-8"))
    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    source_by_case = {str(row["case_id"]): row for row in matrix.get("source_to_case_map", []) if row.get("case_id")}
    source_by_id = {str(row.get("source_id")): row for row in source_manifest.get("entries", []) if row.get("source_id")}
    mappings = _read_mapping(args.mapping)
    changed: list[dict[str, Any]] = []
    source_hash_rows: list[tuple[str, str]] = []
    for case in matrix.get("cases", []):
        case_id = str(case["case_id"])
        source_ref = source_by_case.get(case_id, {})
        source = source_by_id.get(str(source_ref.get("source_id")), {})
        source_uri = str(source.get("source_uri") or source_ref.get("source_uri") or "")
        path = args.raw / source_uri
        raw = path.read_bytes() if path.is_file() else b""
        text = raw.decode("utf-8", errors="replace")
        source_hash_rows.append((source_uri, _sha256(raw)))
        mapping = mappings.get(case_id, {})
        baseline_text: str | None = None
        entry = mapping.get("entry_path") if mapping.get("status") == "unique" else None
        if entry:
            baseline_path = args.companybrain / str(entry)
            if baseline_path.is_file():
                baseline_text = baseline_path.read_text(encoding="utf-8", errors="replace")
        title = _source_title(text, str(source.get("title") or case.get("target_title") or ""))
        if re.sub(r"^[・·•\s]+", "", title).casefold() in {"q&a", "问答"} and case.get("target_title"):
            title = str(case["target_title"])
        item = dict(case)
        if source.get("status") == "valid" and source.get("product") and source.get("module"):
            item.update(
                semantic_fields(
                    product_or_domain=source["product"],
                    module=source["module"],
                    title=title or case.get("target_title") or "",
                    page_type=case.get("page_type") or "procedure",
                )
            )
        item["required_claims"] = _claim_terms(title, text, baseline_text)
        item["required_boundaries"] = _boundary_terms(text, baseline_text)
        item["oracle_source"] = {
            "source_uri": source_uri,
            "content_hash": _sha256(raw),
            "title": title,
            "mapping_status": mapping.get("status", "unmapped"),
            "method": "title_boundary_and_semantic_key_v2",
            "comparison_key": item["comparison_key"],
        }
        changed.append(item)

    result = dict(matrix)
    result["schema_version"] = "task4-reader-case-matrix.v1"
    result["version"] = "v2-oracle-generated"
    result["oracle"] = {
        "schema_version": "task4-content-oracle.v2",
        "generated_by": "scripts/task4_generate_case_oracle.py",
        "source_manifest_id": source_manifest.get("input_manifest_id") or source_manifest.get("manifest_id") or "confluence-raw-89-20260818-v1",
        "source_content_tree_hash": _sha256(json.dumps(sorted(source_hash_rows), ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
        "mapping_fixture": str(args.mapping.name),
        "manual_review_required": False,
    }
    result["cases"] = changed
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(changed), "oracle": result["oracle"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
