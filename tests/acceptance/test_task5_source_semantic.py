from __future__ import annotations

import json

import pytest

from knowledge_digest.compiler import (
    PAGE_TYPES,
    SourceDoc,
    _normalise_page,
    _normalise_task5_semantic_output,
    _render_evidence,
)
from knowledge_digest.task5_semantic_model import SemanticContractError, parse_typed_response, validate_evidence_closure


def _page():
    return {
        "schema_version": "task5-semantic-output.v2",
        "title": "测试页面",
        "page_type": "concept",
        "page_type_claim_ids": ["e1"],
        "axis": {"product": "产品", "module": "模块", "object": "对象", "scene": "场景", "boundary": "边界"},
        "axis_claim_ids": {name: ["e1"] for name in ("product", "module", "object", "scene", "boundary")},
        "summary": {"body": "结论", "claim_ids": ["e1"], "evidence_ids": ["e1"]},
        "sections": {heading: {"body": "原始资料未明确", "claim_ids": [], "evidence_ids": []} for heading in PAGE_TYPES["concept"]},
    }


def test_typed_response_requires_exact_shape_and_known_evidence():
    value = parse_typed_response(json.dumps(_page(), ensure_ascii=False))
    validate_evidence_closure(value, ["e1"])


def test_typed_response_rejects_unknown_fields_and_out_of_closure_refs():
    value = _page()
    value["extra"] = True
    with pytest.raises(SemanticContractError):
        parse_typed_response(json.dumps(value))
    value = _page()
    value["summary"]["evidence_ids"] = ["not-supplied"]
    value["summary"]["claim_ids"] = ["not-supplied"]
    parsed = parse_typed_response(json.dumps(value))
    with pytest.raises(SemanticContractError, match="outside"):
        validate_evidence_closure(parsed, ["e1"])


def test_compiler_preserves_provider_claim_ids_for_reader_lineage():
    value = _page()
    first_heading = PAGE_TYPES["concept"][0]
    value["sections"][first_heading] = {
        "body": "事实正文",
        "claim_ids": ["e1"],
        "evidence_ids": ["e1"],
    }

    normalised = _normalise_task5_semantic_output(
        value,
        allowed_claim_ids={"e1"},
        expected_question="固定问题",
    )

    assert normalised["summary"]["claim_ids"] == ["e1"]
    assert normalised["sections"][first_heading]["claim_ids"] == ["e1"]

    source = SourceDoc(
        source_id="source-test",
        relative_path="product/source.md",
        raw_bytes=b"fact\n",
        text="fact\n",
        lines=("fact",),
        product="product",
        product_label="产品",
        evidence=({
            "evidence_id": "e1",
            "source_id": "source-test",
            "start_line": 1,
            "end_line": 1,
            "text": "fact",
        },),
    )
    page = _normalise_page((source,), value, require_task5_semantic=True)
    rows = [json.loads(line) for line in _render_evidence((source,), (page,)).decode().splitlines()]
    by_surface = {row["surface"] + ":" + row["slot"]: row for row in rows}

    assert by_surface["Reader.summary:summary"]["claim_ids"] == ["e1"]
    assert by_surface[f"Reader.section:{first_heading}"]["claim_ids"] == ["e1"]


def test_compiler_rejects_claim_refs_outside_evidence_closure():
    value = _page()
    value["summary"]["claim_ids"] = ["not-supplied"]

    with pytest.raises(ValueError, match="outside closure"):
        _normalise_task5_semantic_output(value, allowed_claim_ids={"e1"})


def test_compiler_repairs_unique_one_character_qev_copy_slip():
    exact = "qev-09eec2f2a7645f41f65f5674"
    slipped = "qev-09eec2f2f2a7645f41f65f5674"
    value = _page()
    for section in (value["summary"], *value["sections"].values()):
        section["body"] = "事实正文"
        section["claim_ids"] = [slipped]
        section["evidence_ids"] = [slipped]
    value["page_type_claim_ids"] = [slipped]
    value["axis_claim_ids"] = {name: [slipped] for name in ("product", "module", "object", "scene", "boundary")}

    normalised = _normalise_task5_semantic_output(
        value,
        allowed_claim_ids={exact},
        expected_question="固定问题",
    )

    assert normalised["summary"]["claim_ids"] == [exact]
    assert normalised["summary"]["evidence_ids"] == [exact]


def test_compiler_repairs_unique_source_evidence_suffix_after_source_id_copy_slip():
    exact = "source-canonical-e0061"
    slipped = "source-canon-e0061"
    value = _page()
    for section in (value["summary"], *value["sections"].values()):
        section["body"] = "事实正文"
        section["claim_ids"] = [slipped]
        section["evidence_ids"] = [slipped]
    value["page_type_claim_ids"] = [slipped]
    value["axis_claim_ids"] = {name: [slipped] for name in ("product", "module", "object", "scene", "boundary")}

    normalised = _normalise_task5_semantic_output(
        value,
        allowed_claim_ids={exact},
        expected_question="固定问题",
    )

    assert normalised["summary"]["claim_ids"] == [exact]
    assert normalised["summary"]["evidence_ids"] == [exact]


def test_source_semantic_allows_unknown_axis_without_fake_evidence():
    value = _page()
    value["axis"]["module"] = "原始资料未明确"
    value["axis_claim_ids"]["module"] = []

    normalised = _normalise_task5_semantic_output(
        value,
        allowed_claim_ids={"e1"},
        expected_question="固定问题",
    )

    assert normalised["axes"]["module"] == "原始资料未明确"
    assert normalised["axis_evidence_ids"]["module"] == ()


def test_source_semantic_keeps_valid_claim_refs_when_evidence_list_omits_them():
    value = _page()
    value["summary"] = {"body": "结论", "claim_ids": ["e1", "e2"], "evidence_ids": ["e1"]}
    value["axis_claim_ids"] = {name: ["e1"] for name in ("product", "module", "object", "scene", "boundary")}

    normalised = _normalise_task5_semantic_output(
        value,
        allowed_claim_ids={"e1", "e2"},
        expected_question="固定问题",
    )

    assert normalised["summary"]["claim_ids"] == ["e1", "e2"]
    assert normalised["summary"]["evidence_ids"] == ["e1", "e2"]


def test_source_semantic_normalises_short_no_evidence_section_without_inventing_fact():
    value = _page()
    value["sections"]["边界与容易混淆"] = {
        "body": "资料未提及",
        "claim_ids": [],
        "evidence_ids": [],
    }

    normalised = _normalise_task5_semantic_output(
        value,
        allowed_claim_ids={"e1"},
        expected_question="固定问题",
    )

    assert normalised["sections"]["边界与容易混淆"] == {
        "body": "原始资料未明确",
        "claim_ids": [],
        "evidence_ids": [],
    }


def test_source_semantic_rejects_unknown_summary_when_source_has_evidence():
    value = _page()
    value["summary"] = {
        "body": "原始资料未明确",
        "claim_ids": [],
        "evidence_ids": [],
    }

    with pytest.raises(ValueError, match="summary cannot be UNKNOWN while evidence closure is non-empty"):
        _normalise_task5_semantic_output(value, allowed_claim_ids={"e1"})


def test_source_semantic_normalises_long_no_evidence_section_without_inventing_fact():
    value = _page()
    value["sections"]["边界与容易混淆"] = {
        "body": "原始资料未明确该章节的网络边界或兼容性限制信息",
        "claim_ids": [],
        "evidence_ids": [],
    }

    normalised = _normalise_task5_semantic_output(
        value,
        allowed_claim_ids={"e1"},
        expected_question="固定问题",
    )

    assert normalised["sections"]["边界与容易混淆"]["body"] == "原始资料未明确"


def test_source_semantic_does_not_hide_fact_when_evidence_is_missing():
    value = _page()
    value["sections"]["边界与容易混淆"] = {
        "body": "管理员必须先完成配置",
        "claim_ids": [],
        "evidence_ids": [],
    }

    with pytest.raises(ValueError, match="evidence_ids is empty"):
        _normalise_task5_semantic_output(value, allowed_claim_ids={"e1"})


def test_unknown_axis_is_metadata_only_and_never_emits_empty_audit_unit():
    value = _page()
    value["axis"]["module"] = "原始资料未明确"
    value["axis_claim_ids"]["module"] = []
    source = SourceDoc(
        source_id="source-test",
        relative_path="product/source.md",
        raw_bytes=b"fact\n",
        text="fact\n",
        lines=("fact",),
        product="product",
        product_label="产品",
        evidence=({
            "evidence_id": "e1",
            "source_id": "source-test",
            "start_line": 1,
            "end_line": 1,
            "text": "fact",
        },),
    )
    from knowledge_digest.compiler import _render_evidence

    page = _normalise_page((source,), value, require_task5_semantic=True)
    rows = [json.loads(line) for line in _render_evidence((source,), (page,)).decode().splitlines()]

    assert not any(row["surface"] == "Reader.axis" and row["slot"] == "module" for row in rows)
