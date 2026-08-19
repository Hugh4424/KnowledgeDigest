"""Task4 GoInsight location-field pilot compiler.

This is a deliberately isolated compiler seam. It consumes a frozen, small
source manifest and produces a candidate Reader package plus an Audit record.
It does not call the formal KnowledgeDigest pipeline and it never writes a
formal knowledge base.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "task4-location-pilot.v1"
PROVIDER_SCHEMA_VERSION = "task4-location-provider.v1"
READER_PAGE_STATUS = "published"
DELIVERY_STATUS = "not_released"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UNSUPPORTED_WORDS = ("不可", "不支持", "暂时不做", "不能", "不按")


class LocationPilotError(RuntimeError):
    """A fail-closed Task4 compiler error with a stable reason code."""

    def __init__(self, message: str, *, code: str = "contract", details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


def _json_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _line_count(path: Path) -> int:
    """Use the frozen manifest's wc -l convention for source identity."""

    return path.read_bytes().count(b"\n")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LocationPilotError("relative path is empty", code="invalid_path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise LocationPilotError(f"path escapes the pilot root: {value}", code="invalid_path")
    if value.startswith("./"):
        raise LocationPilotError(f"path is not canonical: {value}", code="invalid_path")
    return path.as_posix()


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LocationPilotError(f"{label} must be an object", code="invalid_contract")
    return value


def _claim_direction(claim: Mapping[str, Any]) -> str:
    explicit = claim.get("direction")
    if explicit in {"supported", "unsupported", "context", "deferred"}:
        return str(explicit)
    claim_id = str(claim.get("claim_id", ""))
    return "unsupported" if claim_id.startswith("N-") else "supported"


def load_location_contract(config_path: Path) -> Mapping[str, Any]:
    """Load and validate the immutable pilot contract."""

    path = Path(config_path)
    if not path.is_file() or path.is_symlink():
        raise LocationPilotError(f"config is not a regular file: {path}", code="config_missing")
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocationPilotError(f"cannot read config: {exc}", code="config_invalid") from exc
    contract = _require_mapping(contract, "contract")
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise LocationPilotError("unexpected Task4 contract schema", code="invalid_contract")
    if not isinstance(contract.get("manifest_id"), str) or not contract["manifest_id"].strip():
        raise LocationPilotError("manifest_id is required", code="invalid_contract")

    required = contract.get("required_sources")
    excluded = contract.get("excluded_sources", [])
    if not isinstance(required, list) or not required:
        raise LocationPilotError("required_sources must be a non-empty list", code="invalid_contract")
    if contract.get("required_source_count") != len(required):
        raise LocationPilotError("required_source_count does not match required_sources", code="manifest_drift")
    if len(required) != 3:
        raise LocationPilotError("Task4 pilot requires exactly three primary sources", code="manifest_drift")
    if not isinstance(excluded, list):
        raise LocationPilotError("excluded_sources must be a list", code="invalid_contract")

    seen_sources: set[str] = set()
    for group_name, rows in (("required_sources", required), ("excluded_sources", excluded)):
        for row_value in rows:
            row = _require_mapping(row_value, group_name)
            source_uri = _safe_relative(row.get("source_uri"))
            if source_uri in seen_sources:
                raise LocationPilotError(f"duplicate source row: {source_uri}", code="manifest_drift")
            seen_sources.add(source_uri)
            if not isinstance(row.get("line_count"), int) or row["line_count"] < 1:
                raise LocationPilotError(f"invalid line_count for {source_uri}", code="invalid_contract")
            if not isinstance(row.get("sha256"), str) or not _SHA256.fullmatch(row["sha256"]):
                raise LocationPilotError(f"invalid sha256 for {source_uri}", code="invalid_contract")

    duplicates = contract.get("duplicate_sources", [])
    if not isinstance(duplicates, list):
        raise LocationPilotError("duplicate_sources must be a list", code="invalid_contract")
    for duplicate_value in duplicates:
        duplicate = _require_mapping(duplicate_value, "duplicate source")
        source_uri = _safe_relative(duplicate.get("source_uri"))
        canonical_uri = _safe_relative(duplicate.get("canonical_source_uri"))
        if source_uri in seen_sources or canonical_uri not in {str(row["source_uri"]) for row in required}:
            raise LocationPilotError(f"invalid duplicate binding: {source_uri}", code="duplicate_binding")
        seen_sources.add(source_uri)
        if not isinstance(duplicate.get("line_count"), int) or duplicate["line_count"] < 1:
            raise LocationPilotError(f"invalid duplicate line_count: {source_uri}", code="invalid_contract")
        if not isinstance(duplicate.get("sha256"), str) or not _SHA256.fullmatch(duplicate["sha256"]):
            raise LocationPilotError(f"invalid duplicate sha256: {source_uri}", code="invalid_contract")

    topic = _require_mapping(contract.get("canonical_topic"), "canonical_topic")
    for key in ("topic_id", "title", "category_path", "page_path", "index_path"):
        if not isinstance(topic.get(key), str) or not topic[key].strip():
            raise LocationPilotError(f"canonical_topic.{key} is required", code="invalid_contract")
    for key in ("category_path", "page_path", "index_path"):
        _safe_relative(topic[key])
    if any(token in str(topic["page_path"]) for token in ("cluster-", "draft-")):
        raise LocationPilotError("canonical page path contains a run identity", code="invalid_contract")

    claims = contract.get("claims")
    sections = contract.get("sections")
    if not isinstance(claims, list) or not claims:
        raise LocationPilotError("claims must be a non-empty list", code="invalid_contract")
    if not isinstance(sections, list) or not sections:
        raise LocationPilotError("sections must be a non-empty list", code="invalid_contract")
    required_uris = {str(row["source_uri"]) for row in required}
    claim_ids: set[str] = set()
    claim_by_id: dict[str, Mapping[str, Any]] = {}
    for claim_value in claims:
        claim = _require_mapping(claim_value, "claim")
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip() or claim_id in claim_ids:
            raise LocationPilotError(f"invalid or duplicate claim_id: {claim_id}", code="invalid_contract")
        claim_ids.add(claim_id)
        claim_by_id[claim_id] = claim
        source_uri = _safe_relative(claim.get("source_uri"))
        if source_uri not in required_uris:
            raise LocationPilotError(f"claim points at undeclared source: {source_uri}", code="invalid_contract")
        if not isinstance(claim.get("text"), str) or not claim["text"].strip():
            raise LocationPilotError(f"claim has no text: {claim_id}", code="invalid_contract")
        if not isinstance(claim.get("line_start"), int) or not isinstance(claim.get("line_end"), int):
            raise LocationPilotError(f"claim has no line anchor: {claim_id}", code="invalid_contract")
        if claim["line_start"] < 1 or claim["line_end"] < claim["line_start"]:
            raise LocationPilotError(f"invalid line anchor: {claim_id}", code="invalid_contract")

    section_ids: set[str] = set()
    assigned_claims: list[str] = []
    for section_value in sections:
        section = _require_mapping(section_value, "section")
        section_id = section.get("section_id")
        layer = section.get("layer")
        if not isinstance(section_id, str) or not section_id.strip() or section_id in section_ids:
            raise LocationPilotError(f"invalid or duplicate section_id: {section_id}", code="invalid_contract")
        if layer not in {"usage", "rules"}:
            raise LocationPilotError(f"unsupported section layer: {layer}", code="invalid_contract")
        section_ids.add(section_id)
        section_claims = section.get("claim_ids")
        if not isinstance(section_claims, list) or not section_claims:
            raise LocationPilotError(f"section has no claim_ids: {section_id}", code="invalid_contract")
        for claim_id in section_claims:
            if claim_id not in claim_ids:
                raise LocationPilotError(f"unknown claim in section {section_id}: {claim_id}", code="unknown_claim")
            if claim_by_id[claim_id].get("layer", layer) != layer:
                raise LocationPilotError(f"claim layer mismatch: {claim_id}", code="claim_direction")
            assigned_claims.append(str(claim_id))
    if sorted(assigned_claims) != sorted(claim_ids) or len(assigned_claims) != len(set(assigned_claims)):
        raise LocationPilotError("each claim must belong to exactly one section", code="claim_mapping")

    related = topic.get("related_topics")
    if not isinstance(related, list) or len(related) < 2:
        raise LocationPilotError("at least two related topics are required", code="invalid_contract")
    for related_value in related:
        related_row = _require_mapping(related_value, "related topic")
        for key in ("topic_id", "title", "page_path"):
            if not isinstance(related_row.get(key), str) or not related_row[key].strip():
                raise LocationPilotError(f"related topic missing {key}", code="invalid_contract")
        _safe_relative(related_row["page_path"])

    companybrain = _require_mapping(contract.get("companybrain_manifest"), "companybrain_manifest")
    if not isinstance(companybrain.get("target_path"), str) or not _SHA256.fullmatch(str(companybrain.get("target_sha256", ""))):
        raise LocationPilotError("CompanyBrain binding is incomplete", code="invalid_contract")
    return contract


def _source_file(raw_root: Path, source_uri: str) -> Path:
    relative = Path(_safe_relative(source_uri))
    path = raw_root / relative
    if path.is_symlink() or not path.is_file():
        raise LocationPilotError(f"source is missing or symlinked: {source_uri}", code="source_unreadable")
    return path


def freeze_location_sources(raw_root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    """Verify the declared source snapshot and return immutable audit rows."""

    root = Path(raw_root)
    if root.is_symlink() or not root.is_dir():
        raise LocationPilotError(f"raw root is not a regular directory: {root}", code="source_unreadable")
    required_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for row_value in contract["required_sources"]:
        row = dict(_require_mapping(row_value, "required source"))
        source_uri = str(row["source_uri"])
        path = _source_file(root, source_uri)
        actual_hash = _file_hash(path)
        actual_lines = _line_count(path)
        if actual_hash != row["sha256"] or actual_lines != row["line_count"]:
            raise LocationPilotError(
                f"source manifest drift: {source_uri}",
                code="manifest_drift",
                details={
                    "source_uri": source_uri,
                    "expected_sha256": row["sha256"],
                    "actual_sha256": actual_hash,
                    "expected_line_count": row["line_count"],
                    "actual_line_count": actual_lines,
                },
            )
        required_rows.append(
            {
                **row,
                "status": "valid",
                "source_uri": source_uri,
                "content_hash": actual_hash,
                "actual_line_count": actual_lines,
                "source_id": row.get("source_id") or _json_hash({"source_uri": source_uri})[:16],
            }
        )
    for row_value in contract.get("excluded_sources", []):
        row = dict(_require_mapping(row_value, "excluded source"))
        source_uri = str(row["source_uri"])
        path = _source_file(root, source_uri)
        actual_hash = _file_hash(path)
        actual_lines = _line_count(path)
        if actual_hash != row["sha256"] or actual_lines != row["line_count"]:
            raise LocationPilotError(
                f"excluded source manifest drift: {source_uri}",
                code="manifest_drift",
                details={"source_uri": source_uri, "expected_sha256": row["sha256"], "actual_sha256": actual_hash},
            )
        excluded_rows.append(
            {
                **row,
                "status": "excluded",
                "source_uri": source_uri,
                "content_hash": actual_hash,
                "actual_line_count": actual_lines,
            }
        )
    duplicate_rows: list[dict[str, Any]] = []
    required_by_uri = {str(row["source_uri"]): row for row in required_rows}
    for row_value in contract.get("duplicate_sources", []):
        row = dict(_require_mapping(row_value, "duplicate source"))
        source_uri = str(row["source_uri"])
        canonical_uri = str(row["canonical_source_uri"])
        path = _source_file(root, source_uri)
        actual_hash = _file_hash(path)
        actual_lines = _line_count(path)
        if actual_hash != row["sha256"] or actual_lines != row["line_count"]:
            raise LocationPilotError(
                f"duplicate source manifest drift: {source_uri}",
                code="manifest_drift",
                details={"source_uri": source_uri, "expected_sha256": row["sha256"], "actual_sha256": actual_hash},
            )
        canonical = required_by_uri[canonical_uri]
        duplicate_rows.append(
            {
                **row,
                "status": "duplicate",
                "content_hash": actual_hash,
                "actual_line_count": actual_lines,
                "canonical_source_id": canonical["source_id"],
                "redirect_target_path": contract["canonical_topic"]["page_path"],
                "redirect_status": "canonical",
            }
        )
    manifest = {
        "schema_version": "task4-location-source-manifest.v1",
        "manifest_id": contract["manifest_id"],
        "raw_root": "external-input",
        "required_sources": required_rows,
        "excluded_sources": excluded_rows,
        "duplicate_sources": duplicate_rows,
        "source_count": len(required_rows),
        "excluded_count": len(excluded_rows),
        "duplicate_count": len(duplicate_rows),
        "snapshot_hash": _json_hash({"required_sources": required_rows, "excluded_sources": excluded_rows, "duplicate_sources": duplicate_rows}),
    }
    return manifest


def _claim_evidence(raw_root: Path, contract: Mapping[str, Any], manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_uri = {str(row["source_uri"]): row for row in manifest["required_sources"]}
    evidence: list[dict[str, Any]] = []
    for claim_value in contract["claims"]:
        claim = dict(_require_mapping(claim_value, "claim"))
        source_uri = str(claim["source_uri"])
        row = by_uri[source_uri]
        path = _source_file(Path(raw_root), source_uri)
        lines = path.read_text(encoding="utf-8").splitlines()
        start = int(claim["line_start"])
        end = int(claim["line_end"])
        if end > len(lines):
            raise LocationPilotError(f"claim anchor is outside source: {claim['claim_id']}", code="claim_anchor")
        anchor_text = "\n".join(lines[start - 1 : end]).strip()
        if not anchor_text:
            raise LocationPilotError(f"claim anchor is empty: {claim['claim_id']}", code="claim_anchor")
        evidence_row = {
                "claim_id": claim["claim_id"],
                "text": claim["text"],
                "direction": _claim_direction(claim),
                "target_section": claim["section_id"],
                "source_uri": source_uri,
                "source_id": row["source_id"],
                "fragment_locator": f"lines:{start}-{end}",
                "line_start": start,
                "line_end": end,
                "anchor_text": anchor_text,
                "content_hash": hashlib.sha256(anchor_text.encode("utf-8")).hexdigest(),
                "source_content_hash": row["content_hash"],
                "validation_status": "verified",
            }
        evidence_row["claim_fingerprint"] = _json_hash(
            {
                "claim_id": evidence_row["claim_id"],
                "source_uri": evidence_row["source_uri"],
                "fragment_locator": evidence_row["fragment_locator"],
                "content_hash": evidence_row["content_hash"],
            }
        )
        evidence.append(evidence_row)
    return evidence


def _default_provider_sections(contract: Mapping[str, Any], evidence: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_claim = {str(row["claim_id"]): row for row in evidence}
    result: list[dict[str, Any]] = []
    for section_value in contract["sections"]:
        section = dict(_require_mapping(section_value, "section"))
        claim_ids = [str(value) for value in section["claim_ids"]]
        result.append(
            {
                "section_id": section["section_id"],
                "layer": section["layer"],
                "heading": section.get("heading") or section["section_id"],
                "claim_ids": claim_ids,
                "bullets": [str(by_claim[claim_id]["text"]) for claim_id in claim_ids],
            }
        )
    return result


def _provider_sections(
    contract: Mapping[str, Any],
    evidence: list[Mapping[str, Any]],
    provider: Callable[[Mapping[str, Any]], Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if provider is None:
        return _default_provider_sections(contract, evidence), {"mode": "deterministic-contract", "calls": 0}
    request = {
        "schema_version": PROVIDER_SCHEMA_VERSION,
        "topic_id": contract["canonical_topic"]["topic_id"],
        "claims": [dict(row) for row in evidence],
        "sections": [dict(row) for row in contract["sections"]],
        "instruction": "表达已验证事实；不要新增 claim、来源、能力或测试结论。",
    }
    try:
        response = provider(request)
    except Exception as exc:
        raise LocationPilotError(f"provider failed: {exc}", code="provider_failed") from exc
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError as exc:
            raise LocationPilotError(f"provider returned invalid JSON: {exc}", code="provider_schema") from exc
    response = _require_mapping(response, "provider response")
    allowed = {"schema_version", "sections", "fidelity_only"}
    unknown = sorted(set(response) - allowed)
    if unknown:
        raise LocationPilotError(f"provider response has unknown fields: {unknown}", code="provider_schema")
    if response.get("schema_version") != PROVIDER_SCHEMA_VERSION:
        raise LocationPilotError("provider schema_version is invalid", code="provider_schema")
    if response.get("fidelity_only") is True:
        raise LocationPilotError("provider returned fidelity_only", code="fidelity_only")
    sections = response.get("sections")
    if not isinstance(sections, list):
        raise LocationPilotError("provider sections must be a list", code="provider_schema")
    expected_sections = {str(row["section_id"]): dict(row) for row in contract["sections"]}
    expected_claims = {str(row["claim_id"]) for row in evidence}
    actual_sections: list[dict[str, Any]] = []
    assigned: list[str] = []
    for section_value in sections:
        section = _require_mapping(section_value, "provider section")
        unknown_section = sorted(set(section) - {"section_id", "layer", "heading", "claim_ids", "bullets"})
        if unknown_section:
            raise LocationPilotError(f"provider section has unknown fields: {unknown_section}", code="provider_schema")
        section_id = str(section.get("section_id", ""))
        if section_id not in expected_sections:
            raise LocationPilotError(f"provider returned unknown section: {section_id}", code="provider_schema")
        if section.get("layer") != expected_sections[section_id]["layer"]:
            raise LocationPilotError(f"provider section layer mismatch: {section_id}", code="provider_schema")
        claim_ids = section.get("claim_ids")
        bullets = section.get("bullets")
        if not isinstance(claim_ids, list) or not claim_ids or not isinstance(bullets, list) or len(bullets) != len(claim_ids):
            raise LocationPilotError(f"provider section is empty or unaligned: {section_id}", code="provider_schema")
        if any(not isinstance(item, str) or not item.strip() for item in bullets):
            raise LocationPilotError(f"provider section has empty bullet: {section_id}", code="provider_schema")
        for claim_id in claim_ids:
            if claim_id not in expected_claims:
                raise LocationPilotError(f"provider returned unknown claim: {claim_id}", code="unknown_claim")
        assigned.extend(str(claim_id) for claim_id in claim_ids)
        actual_sections.append(
            {
                "section_id": section_id,
                "layer": section["layer"],
                "heading": str(section.get("heading") or expected_sections[section_id].get("heading") or section_id),
                "claim_ids": [str(item) for item in claim_ids],
                "bullets": [str(item) for item in bullets],
            }
        )
    if {row["section_id"] for row in actual_sections} != set(expected_sections) or sorted(assigned) != sorted(expected_claims) or len(assigned) != len(set(assigned)):
        raise LocationPilotError("provider did not preserve the complete claim/section mapping", code="provider_schema")
    return actual_sections, {"mode": "provider", "calls": 1, "schema_version": PROVIDER_SCHEMA_VERSION}


def _validate_direction(evidence: list[Mapping[str, Any]], page_body: str) -> None:
    for row in evidence:
        if row["direction"] == "unsupported" and not any(token in page_body for token in _UNSUPPORTED_WORDS):
            raise LocationPilotError(f"unsupported claim lost its boundary: {row['claim_id']}", code="claim_direction")
        if not str(row["text"]).strip():
            raise LocationPilotError(f"empty claim reached Reader: {row['claim_id']}", code="claim_anchor")


def _frontmatter(fields: Mapping[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, bool):
            encoded = "true" if value else "false"
        else:
            encoded = json.dumps(str(value), ensure_ascii=False)
        lines.append(f"{key}: {encoded}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def _reader_snapshot_hash(root: Path) -> str:
    rows: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(("audit/", "reports/", "sources/")):
            continue
        rows.append({"path": relative, "sha256": _file_hash(path)})
    return _json_hash(rows)


def _write_reader_package(
    output_root: Path,
    contract: Mapping[str, Any],
    manifest: Mapping[str, Any],
    evidence: list[Mapping[str, Any]],
    sections: list[Mapping[str, Any]],
) -> dict[str, Any]:
    from .page_layout import render_task4_two_layer_page

    topic = contract["canonical_topic"]
    related = [dict(row) for row in topic["related_topics"]]
    related_links = [{"title": str(row["title"]), "href": f"../{Path(str(row['page_path'])).name}"} for row in related]
    source_projection = [
        {
            "title": str(row["title"]),
            "href": f"../../../sources/{row['source_uri']}",
            "source_uri": str(row["source_uri"]),
        }
        for row in manifest["required_sources"]
    ]
    layout = render_task4_two_layer_page(
        topic_id=str(topic["topic_id"]),
        title=str(topic["title"]),
        canonical_path=str(topic["page_path"]),
        usage_sections=[dict(row) for row in sections if row["layer"] == "usage"],
        rules_sections=[dict(row) for row in sections if row["layer"] == "rules"],
        claims=[dict(row) for row in evidence],
        related_links=related_links,
        source_projection=source_projection,
    )
    _validate_direction(evidence, str(layout["body"]))

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "Home.md").write_text("# KnowledgeDigest candidate\n\n- [GoInsight](products/GoInsight/index.md)\n", encoding="utf-8")
    product_index = output_root / "products/GoInsight/index.md"
    product_index.parent.mkdir(parents=True, exist_ok=True)
    product_index.write_text("# GoInsight\n\n- [字段与筛选](字段与筛选/index.md)\n", encoding="utf-8")
    field_index = output_root / str(topic["index_path"])
    field_index.parent.mkdir(parents=True, exist_ok=True)
    field_index.write_text(
        "# 字段与筛选\n\n- [位置字段筛选](位置字段筛选.md)\n- [数据分析](../数据分析.md)\n- [设备位置历史数据集](../设备位置历史数据集.md)\n",
        encoding="utf-8",
    )

    page_path = output_root / str(topic["page_path"])
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(
        _frontmatter(
            {
                "managed_by": "KnowledgeDigest",
                "digest_topic_id": topic["topic_id"],
                "digest_published_path": topic["page_path"],
                "digest_page_status": READER_PAGE_STATUS,
                "reader_eligible": True,
                "semantic_mode": "structured",
            }
        )
        + str(layout["body"]),
        encoding="utf-8",
    )
    related_summaries = {
        "GoInsight/数据分析.md": "数据分析页提供字段拖拽、数据筛选、工作表和报告上下文。",
        "GoInsight/设备位置历史数据集.md": "设备位置历史数据集提供位置历史问题和字段上下文。",
    }
    for row in related:
        related_path = output_root / str(row["page_path"])
        related_path.parent.mkdir(parents=True, exist_ok=True)
        related_path.write_text(
            _frontmatter(
                {
                    "managed_by": "KnowledgeDigest",
                    "digest_topic_id": row["topic_id"],
                    "digest_published_path": row["page_path"],
                    "digest_page_status": READER_PAGE_STATUS,
                    "reader_eligible": True,
                    "semantic_mode": "projection",
                }
            )
            + f"# {row['title']}\n\n{related_summaries.get(str(row['page_path']), '相关上下文页。')}\n\n- [回到位置字段筛选](字段与筛选/位置字段筛选.md)\n",
            encoding="utf-8",
        )
    for row in manifest["required_sources"]:
        projection = output_root / "sources" / str(row["source_uri"])
        projection.parent.mkdir(parents=True, exist_ok=True)
        projection.write_text(
            f"# {row['title']}\n\n- 来源文件：`{row['source_uri']}`\n- 状态：已核验\n",
            encoding="utf-8",
        )
    return {
        "canonical_page": str(topic["page_path"]),
        "canonical_page_hash": _file_hash(page_path),
        "reader_snapshot_hash": _reader_snapshot_hash(output_root),
        "reader_eligible": True,
        "layout_line_count": int(layout["line_count"]),
    }


def _write_failure_package(
    output_root: Path,
    *,
    contract: Mapping[str, Any] | None,
    manifest: Mapping[str, Any] | None,
    status: str,
    reason: str,
    code: str,
    details: Any = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "README.md").write_text(
        "# KnowledgeDigest candidate\n\n本次编译未进入 Reader。请查看 `audit/compilation-run.json`。\n",
        encoding="utf-8",
    )
    if manifest is not None:
        _write_json(output_root / "audit/source-manifest.json", manifest)
    record = {
        "schema_version": "task4-location-compilation-run.v1",
        "status": status,
        "run_status": status,
        "page_status": "degraded" if status == "degraded" else None,
        "delivery_status": DELIVERY_STATUS,
        "candidate_status": "not_released",
        "reader_eligible": False,
        "reader_inclusion": False,
        "semantic_status": "degraded" if status == "degraded" else "failed",
        "fallback_used": False,
        "fallback_mode": "audit-only",
        "fallback_reason": reason,
        "provider_status": "failed" if code.startswith("provider") or code == "fidelity_only" else "not_called",
        "failure_reasons": [reason],
        "failure_code": code,
        "details": details,
        "manifest_id": contract.get("manifest_id") if contract else None,
        "contract_hash": _json_hash(contract) if contract else None,
    }
    _write_json(output_root / "audit/compilation-run.json", record)
    _write_json(output_root / "reports/release-summary.json", record)
    return {
        "status": status,
        "delivery_status": DELIVERY_STATUS,
        "candidate_status": "not_released",
        "reader_eligible": False,
        "failure_reasons": [reason],
        "failure_code": code,
        "output_root": str(output_root),
        "canonical_page": None,
    }


def _is_running_wrapper_marker(output: Path) -> bool:
    """Allow the recovery wrapper's own running record to precede compilation."""

    if output.is_symlink() or not output.is_dir():
        return False
    marker = output / "audit/compilation-run.json"
    if not marker.is_file() or marker.is_symlink():
        return False
    for path in output.rglob("*"):
        if path.is_symlink():
            return False
        if path.is_file() and path != marker:
            return False
        if path.is_dir() and path != marker.parent:
            return False
    try:
        record = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(record, Mapping) and record.get("status") == "running" and record.get("run_status") == "running"


def compile_location_candidate(
    raw_root: Path,
    output_root: Path,
    *,
    config_path: Path,
    provider: Callable[[Mapping[str, Any]], Any] | None = None,
    evidence_root: Path | None = None,
) -> Mapping[str, Any]:
    """Compile a new isolated candidate directory.

    A successful result is still only a candidate: ``delivery_status`` remains
    ``not_released``. Contract, source, provider, claim and layout failures
    create an Audit-only output and never create a Reader page.
    """

    output = Path(output_root)
    if output.exists() and any(output.iterdir()) and not _is_running_wrapper_marker(output):
        return {
            "status": "failed",
            "delivery_status": DELIVERY_STATUS,
            "candidate_status": "not_released",
            "reader_eligible": False,
            "failure_reasons": ["output root already contains files"],
            "failure_code": "output_exists",
            "output_root": str(output),
            "canonical_page": None,
        }
    contract: Mapping[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    try:
        contract = load_location_contract(Path(config_path))
        manifest = freeze_location_sources(Path(raw_root), contract)
        evidence = _claim_evidence(Path(raw_root), contract, manifest)
        sections, provider_meta = _provider_sections(contract, evidence, provider)
        observed_manifest = freeze_location_sources(Path(raw_root), contract)
        if observed_manifest["snapshot_hash"] != manifest["snapshot_hash"]:
            raise LocationPilotError(
                "source manifest changed after freeze",
                code="manifest_drift",
                details={
                    "expected_snapshot_hash": manifest["snapshot_hash"],
                    "observed_snapshot_hash": observed_manifest["snapshot_hash"],
                },
            )
        reader_meta = _write_reader_package(output, contract, manifest, evidence, sections)
        _write_json(output / "audit/source-manifest.json", manifest)
        _write_json(
            output / "audit/claim-evidence.json",
            {
                "schema_version": "task4-location-claim-evidence.v1",
                "manifest_id": contract["manifest_id"],
                "claims": evidence,
                "claim_count": len(evidence),
                "evidence_hash": _json_hash(evidence),
            },
        )
        run_record = {
            "schema_version": "task4-location-compilation-run.v1",
            "status": "completed",
            "delivery_status": DELIVERY_STATUS,
            "candidate_status": "candidate",
            "reader_eligible": True,
            "manifest_id": contract["manifest_id"],
            "contract_hash": _json_hash(contract),
            "source_manifest_hash": manifest["snapshot_hash"],
            "claim_count": len(evidence),
            "provider": provider_meta,
            **reader_meta,
            "failure_reasons": [],
        }
        _write_json(output / "audit/compilation-run.json", run_record)
        _write_json(output / "reports/release-summary.json", run_record)
        result: dict[str, Any] = {
            "status": "completed",
            "delivery_status": DELIVERY_STATUS,
            "candidate_status": "candidate",
            "reader_eligible": True,
            "failure_reasons": [],
            "output_root": str(output),
            "canonical_page": reader_meta["canonical_page"],
            "source_manifest_hash": manifest["snapshot_hash"],
            "claim_count": len(evidence),
            "reader_snapshot_hash": reader_meta["reader_snapshot_hash"],
            "canonical_page_hash": reader_meta["canonical_page_hash"],
        }
    except LocationPilotError as exc:
        result = _write_failure_package(
            output,
            contract=contract,
            manifest=manifest,
            status="degraded" if exc.code in {"provider_failed", "provider_schema", "fidelity_only", "claim_anchor", "claim_direction", "unknown_claim"} else "failed",
            reason=str(exc),
            code=exc.code,
            details=exc.details,
        )
    except (OSError, UnicodeError) as exc:
        result = _write_failure_package(
            output,
            contract=contract,
            manifest=manifest,
            status="failed",
            reason=str(exc),
            code="io_error",
        )
    if evidence_root is not None:
        _write_json(Path(evidence_root) / "location-compiler-result.json", result)
    return result
