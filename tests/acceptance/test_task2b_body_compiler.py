"""Task 2-B deterministic contracts for typed body compilation.

These tests cover the accepted Task 2-B seam and never call a provider.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

import pytest

from knowledge_digest import draft as draft_module
from knowledge_digest import kb_structure
from knowledge_digest import llm
from knowledge_digest import navigation
from knowledge_digest import page_layout
from knowledge_digest import pipeline as pipeline_module
from knowledge_digest import publication as publication_module
from knowledge_digest.config import DigestSettings
from knowledge_digest.paths import DigestPaths


FIXTURE = Path(__file__).parents[1] / "fixtures" / "task2b_publication_body" / "cases.json"


def _cases() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _source_item(case: dict[str, Any]) -> dict[str, Any]:
    source = case["source"]
    return {
        **source,
        "content_fingerprint": "f" * 64,
        "validation_status": "passed",
        "source_meta": {"title": case["topic_index"]["title"]},
    }


def test_pipeline_binds_existing_topic_index_page_type_without_guessing_procedure(tmp_path: Path) -> None:
    attach = getattr(pipeline_module, "_attach_task2b_topic_mapping", None)
    assert callable(attach)
    kb_dir = tmp_path / "kb"
    (kb_dir / "_digest").mkdir(parents=True)
    (kb_dir / "_digest" / "topic-index.json").write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "topics": [
                    {
                        "topic_key": "v2/products/goinsight/procedure",
                        "knowledge_type": "products",
                        "product": "GoInsight",
                        "module": "Builder",
                        "object_intent": "Builder",
                        "source_members": ["source-a"],
                        "published_path": "pages/topics/procedure.md",
                        "old_path_mapping": [],
                        "status": "published",
                        "topic_plan_version": "1.0.0",
                        "reason": "",
                        "evidence_refs": [{"source_uri": "raw://a", "content_fingerprint": "a" * 64, "line_number": 1}],
                        "page_type": "procedure_or_rule",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    decisions = [{"cluster_id": "cluster-a", "topic_id": "topic-a"}]
    clusters = [{"cluster_id": "cluster-a", "members": ["raw-a"]}]
    raw_items = [{"raw_id": "raw-a", "source_id": "source-a", "source_uri": "raw://a"}]
    attach(
        decisions=decisions,
        clusters=clusters,
        raw_items=raw_items,
        paths=DigestPaths(tmp_path / "input", tmp_path / "input" / "items", kb_dir, kb_dir / "kb.structure.md"),
    )
    assert decisions[0]["topic_id"] == "topic-a"
    assert decisions[0]["topic_index"]["topic_index_id"] == "v2/products/goinsight/procedure"
    assert decisions[0]["topic_index"]["page_type"] == "procedure_or_rule"
    assert decisions[0]["topic_index"]["mapping_status"] == "mapped"


def test_semantic_evidence_writer_is_bound_to_declared_sample_paths(monkeypatch, tmp_path: Path) -> None:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    paths = __import__("knowledge_digest.paths", fromlist=["validate_paths"]).validate_paths(
        new_dir,
        kb_dir,
        allow_new_kb=True,
    )
    output = tmp_path / "semantic-run.json"
    monkeypatch.setenv("KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE", str(output))
    monkeypatch.delenv("KNOWLEDGEDIGEST_TASK2B_SAMPLE_INPUT", raising=False)
    monkeypatch.delenv("KNOWLEDGEDIGEST_TASK2B_SAMPLE_KB", raising=False)

    assert pipeline_module.write_semantic_evidence_file(
        paths=paths,
        settings=DigestSettings(llm_enabled=False),
        result=None,
    ) is None
    assert not output.exists()


def test_structure_normalizer_preserves_typed_source_fragments() -> None:
    case = _cases()["page_types"][0]
    normalizer = getattr(draft_module, "normalize_structure", None)
    assert callable(normalizer), "Task 2-B must expose the deterministic Structure Normalizer seam"

    fragments = normalizer([_source_item(case)])

    assert fragments
    assert {fragment["content_type"] for fragment in fragments} >= {
        "heading",
        "faq",
        "table",
        "image",
        "bilingual",
        "version",
        "noise",
    }
    assert all(fragment.get("source_locator") for fragment in fragments)
    assert all(fragment.get("source_uri") == case["source"]["source_uri"] for fragment in fragments)
    assert any(fragment.get("parent_locator") for fragment in fragments if fragment["content_type"] != "heading")


def test_typed_generation_keeps_complete_page_claims_in_one_provider_context() -> None:
    contexts = draft_module._generation_contexts(
        [
            {"raw_id": "raw-a", "text": "# Module\nPurpose A"},
            {"raw_id": "raw-b", "text": "Capabilities B"},
        ],
        [
            {"raw_id": "raw-a", "claim_fingerprint": "a" * 64, "text": "Purpose A"},
            {"raw_id": "raw-b", "claim_fingerprint": "b" * 64, "text": "Capabilities B"},
        ],
        base_context={
            "typed_section_contract": {
                "page_type": "module_or_capability",
                "required_sections": ["purpose", "capabilities"],
                "optional_sections": [],
            },
            "initial_body": "# Module\nPurpose A\nCapabilities B",
            "source_text": "# Module\nPurpose A\nCapabilities B",
        },
        max_claims=1,
        max_chars=1,
    )

    assert len(contexts) == 1
    assert contexts[0]["batch_count"] == 1
    assert {claim["claim_fingerprint"] for claim in contexts[0]["claims"]} == {"a" * 64, "b" * 64}
    assert contexts[0]["source_text"] == "# Module\nPurpose A\nCapabilities B"


def test_typed_prompt_does_not_repeat_source_or_send_stale_reader_body() -> None:
    prompt = llm.build_prompt(
        {
            "typed_section_contract": {
                "page_type": "module_or_capability",
                "required_sections": ["purpose", "capabilities"],
                "optional_sections": [],
            },
            "initial_body": "CURRENT SOURCE",
            "source_text": "CURRENT SOURCE",
            "old_target_body": "STALE READER BODY",
            "claims": [],
        },
        target_page="pages/module.md",
    )

    assert prompt.count("CURRENT SOURCE") == 0
    assert "STALE READER BODY" not in prompt
    assert '"initial_body"' not in prompt
    assert '"source_text"' not in prompt
    assert "never attach the whole Claim/Evidence" in prompt


def test_typed_prompt_compacts_source_context_without_dropping_claim_evidence() -> None:
    source_text = "# Module\n\n" + "\n".join(
        [
            "The module supports the documented workflow.",
            "```bash",
            "digest --offline",
            "```",
            "| Field | Value |",
            "| --- | --- |",
            "| mode | offline |",
        ]
    )
    claims = [
        {
            "claim_fingerprint": "fp-compact",
            "text": "The module supports the documented workflow.",
            "source_uri": "raw://module.md",
            "fragment_locator": "lines:3-3",
            "raw_id": "raw-compact",
        },
        {
            "claim_fingerprint": "fp-command",
            "text": "digest --offline",
            "source_uri": "raw://module.md",
            "fragment_locator": "lines:5-5",
            "raw_id": "raw-compact",
        },
        {
            "claim_fingerprint": "fp-table",
            "text": "| mode | offline |",
            "source_uri": "raw://module.md",
            "fragment_locator": "lines:8-8",
            "raw_id": "raw-compact",
        },
    ]
    prompt = llm.build_prompt(
        {
            "typed_section_contract": {
                "page_type": "module_or_capability",
                "required_sections": ["purpose", "capabilities"],
                "optional_sections": [],
            },
            "source_text": source_text,
            "claims": claims,
        },
        target_page="pages/module.md",
    )

    payload = json.loads(prompt.split("INPUT:\n", 1)[1])
    assert "source_text" not in payload
    assert payload["source_outline"] == [
        {"line": 1, "kind": "heading", "text": "# Module"},
        {"line": 4, "kind": "code_fence", "text": "```bash"},
        {"line": 6, "kind": "code_fence", "text": "```"},
        {"line": 7, "kind": "table_row", "text": "| Field | Value |"},
        {"line": 8, "kind": "table_separator", "text": "| --- | --- |"},
    ]
    assert payload["claims"] == [
        {
            **{key: claim[key] for key in ("claim_fingerprint", "text", "source_uri", "fragment_locator", "raw_id")},
            "provider_claim_ref": f"c{index:03d}",
        }
        for index, claim in enumerate(claims, start=1)
    ]


def test_typed_prompt_marks_structured_claim_kind_without_treating_it_as_evidence() -> None:
    claim = {
        "claim_fingerprint": "fp-table",
        "text": "| mode | offline |",
        "source_uri": "raw://module.md",
        "fragment_locator": "lines:8-8",
        "raw_id": "raw-compact",
    }
    prompt = llm.build_prompt(
        {
            "typed_section_contract": {
                "page_type": "module_or_capability",
                "required_sections": ["purpose"],
                "optional_sections": [],
            },
            "source_text": "| mode | offline |",
            "claims": [claim],
            "page_draft": {
                "source_fragments": [
                    {
                        "raw_id": "raw-compact",
                        "fragment_locator": "lines:8-8",
                        "content_type": "table",
                        "text": "| mode | offline |",
                    }
                ]
            },
        },
        target_page="pages/module.md",
    )

    payload = json.loads(prompt.split("INPUT:\n", 1)[1])
    assert payload["claims"][0]["source_kind"] == "table"
    assert payload["claims"][0]["structured_claim_rule"] == "copy_verbatim_or_omit"
    assert "source_kind" in prompt


def test_typed_provider_claim_refs_are_short_but_bind_to_trusted_ids() -> None:
    page = {
        "page_type": "module_or_capability",
        "required_sections": ["purpose"],
        "optional_sections": [],
        "claims": [
            {
                "claim_id": "trusted-claim-1",
                "claim_fingerprint": "f" * 64,
                "text": "The module serves the documented workflow.",
                "source_uri": "raw://module",
                "fragment_locator": "lines:1-1",
            }
        ],
        "sections": {"purpose": {}},
    }
    prompt = llm.build_prompt(
        {
            "typed_section_contract": {
                "page_type": "module_or_capability",
                "required_sections": ["purpose"],
                "optional_sections": [],
            },
            "source_text": "# Module",
            "claims": page["claims"],
        },
        target_page="pages/module.md",
    )

    payload = json.loads(prompt.split("INPUT:\n", 1)[1])
    assert payload["claims"][0]["provider_claim_ref"] == "c001"
    assert len(payload["claims"][0]["provider_claim_ref"]) < len(page["claims"][0]["claim_fingerprint"])

    validated = llm.validate_section_response(
        page,
        {
            "page_type": "module_or_capability",
            "sections": {
                "purpose": {
                    "body": page["claims"][0]["text"],
                    "claim_ids": ["c001"],
                }
            },
        },
    )
    assert validated["status"] == "draft"
    assert validated["sections"]["purpose"]["claim_ids"] == ["trusted-claim-1"]


def test_typed_prompt_explains_section_roles_and_conservative_exact_claim_binding() -> None:
    prompt = llm.build_prompt(
        {
            "typed_section_contract": {
                "page_type": "procedure_or_rule",
                "required_sections": [
                    "prerequisites",
                    "steps_rules",
                    "exceptions",
                    "limitations",
                    "sources",
                ],
                "optional_sections": [],
            },
            "source_text": "Run the documented command.",
            "claims": [],
        },
        target_page="pages/procedure.md",
    )

    assert "exceptions: explicit failure handling, alternate branches, or edge cases" in prompt
    assert "copy that material into the body" in prompt
    assert "claim_id out" in prompt
    assert "never manufacture an answer" in prompt
    assert "make the JSON" in prompt
    assert "complete" in prompt
    assert "Markdown separator lines" in prompt
    assert "never use claim_ids" in prompt
    assert "source" in prompt
    assert "checklist" in prompt


def _source_gap_procedure_page() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    topic_index = {
        "topic_id": "topic-source-gap-procedure",
        "title": "Source Gap Procedure",
        "page_type": "procedure_or_rule",
        "mapping_status": "mapped",
    }
    item = {
        "raw_id": "raw-source-gap",
        "source_uri": "raw://source-gap/procedure",
        "content_fingerprint": "f" * 64,
        "text": (
            "# Source Gap Procedure\n"
            "方案 A：适合当前场景。\n"
            "方案 B：需要更多信息。\n"
            "信息不足/错误可交互补充。"
        ),
    }
    fragments = draft_module.normalize_structure([item])
    page = draft_module.build_page_draft(topic_index=topic_index, fragments=fragments)
    claims: list[dict[str, Any]] = []
    for index, section_id in enumerate(page["required_sections"], start=1):
        if section_id == "exceptions":
            continue
        claims.append(
            {
                "claim_id": f"claim-source-gap-{section_id}",
                "text": f"Documented {section_id} fact.",
                "source_uri": item["source_uri"],
                "fragment_locator": f"lines:{min(index, 4)}-{min(index, 4)}",
                "content_fingerprint": item["content_fingerprint"],
                "raw_id": item["raw_id"],
            }
        )
    page["claims"] = claims
    return page, claims


def test_source_gap_audit_is_deterministic_and_does_not_confuse_error_mentions_with_rules() -> None:
    page, _claims = _source_gap_procedure_page()
    audit = page["section_audits"]["exceptions"]

    assert audit["audit_version"] == "procedure-exceptions-audit.v1"
    assert audit["status"] == "source_not_documented"
    assert audit["question_status"] == "not_answerable"
    assert audit["source_deps"]
    assert audit["explicit_rule_fragment_locators"] == []


def test_source_gap_section_can_publish_without_exception_claim_or_placeholder() -> None:
    page, claims = _source_gap_procedure_page()
    payload = {
        "page_type": "procedure_or_rule",
        "sections": {
            **{
                claim["fragment_locator"] and section_id: {
                    "body": claim["text"],
                    "claim_ids": [claim["claim_id"]],
                }
                for section_id, claim in zip(
                    [section for section in page["required_sections"] if section != "exceptions"],
                    claims,
                )
            },
            "exceptions": {"body": "", "claim_ids": []},
        },
    }
    validated = llm.validate_section_response(page, payload)
    assert validated["status"] == "draft"
    assert validated["sections"]["exceptions"]["status"] == "source_not_documented"
    assert validated["sections"]["exceptions"]["claim_ids"] == []
    assert validated["sections"]["exceptions"]["source_audit"]["source_deps"]

    bound = draft_module._bind_typed_section_dependencies(page, validated, claims)
    gate_payload = pipeline_module._typed_body_gate_payload(
        {"typed_page_draft": page, "claims": claims},
        bound,
    )
    gate = publication_module.validate_body_gate(gate_payload)
    assert gate["reader_eligible"] is True
    assert not any("暂无异常" in reason for reason in gate["reasons"])

    compiled = pipeline_module.compile_publication_candidate(
        page_draft=page,
        provider_payload=bound,
        body_gate_payload=gate_payload,
    )
    assert compiled["status"] == "published"
    assert compiled["candidate"]["sections"]["exceptions"]["status"] == "source_not_documented"
    assert compiled["candidate"]["sections"]["exceptions"]["body"] == ""

    answerability = pipeline_module._task2b_answerability_subset(
        question_set={
            "question_set_id": "fixture",
            "questions": [{"question_id": "positive-06", "polarity": "positive"}],
        },
        concepts=[
            {
                "concept_id": "topic-source-gap-procedure",
                "page_type": "procedure_or_rule",
                "status": "machine-passing",
                "section_ids": list(compiled["candidate"]["sections"]),
                "section_statuses": {"exceptions": "source_not_documented"},
            }
        ],
    )
    assert answerability["questions"] == [
        {
            "question_id": "positive-06",
            "polarity": "positive",
            "answerable": False,
            "first_hit": None,
        }
    ]


def test_source_gap_audit_rejects_incomplete_binding_and_explicit_exception_rule() -> None:
    explicit = {
        "raw_id": "raw-explicit",
        "source_uri": "raw://explicit",
        "content_fingerprint": "f" * 64,
        "text": "如果失败，则保留上一版并记录错误。",
    }
    explicit_audit = publication_module.audit_procedure_exceptions_source(
        draft_module.normalize_structure([explicit])
    )
    assert explicit_audit["status"] == "documented"

    incomplete = {
        "raw_id": "raw-incomplete",
        "source_uri": "raw://incomplete",
        "text": "没有记录异常处理规则。",
    }
    incomplete_audit = publication_module.audit_procedure_exceptions_source(
        draft_module.normalize_structure([incomplete])
    )
    assert incomplete_audit["status"] == "audit_incomplete"


def test_source_not_documented_rejects_provider_written_exception_text() -> None:
    page, claims = _source_gap_procedure_page()
    sections = {
        section_id: {"body": claim["text"], "claim_ids": [claim["claim_id"]]}
        for section_id, claim in zip(
            [section for section in page["required_sections"] if section != "exceptions"],
            claims,
        )
    }
    sections["exceptions"] = {
        "body": "No exceptions are expected.",
        "claim_ids": [],
    }
    result = llm.validate_section_response(
        page,
        {"page_type": "procedure_or_rule", "sections": sections},
    )
    assert result["status"] == "degraded"
    assert "must stay empty" in result["reason"]


def test_structure_fidelity_keeps_version_literals_commands_ports_config_tables_and_images() -> None:
    normalizer = getattr(draft_module, "normalize_structure", None)
    builder = getattr(draft_module, "build_page_draft", None)
    assert callable(normalizer)
    assert callable(builder)

    overview = _cases()["page_types"][0]
    overview_fragments = normalizer([_source_item(overview)])
    overview_text = "\n".join(str(fragment["text"]) for fragment in overview_fragments)
    assert "| version | v2.1 |" in overview_text
    assert "![architecture](images/alpha.png)" in overview_text
    assert any(fragment["content_type"] == "version" and "v2.1" in fragment["text"] for fragment in overview_fragments)
    assert any(fragment["content_type"] == "table" for fragment in overview_fragments)
    assert any(fragment["content_type"] == "image" for fragment in overview_fragments)

    procedure = _cases()["page_types"][2]
    procedure_fragments = normalizer([_source_item(procedure)])
    procedure_text = "\n".join(str(fragment["text"]) for fragment in procedure_fragments)
    assert "digest --no-llm" in procedure_text
    assert "port 5174" in procedure_text
    assert "PROFILE=prod" in procedure_text
    procedure_page = builder(
        topic_index=procedure["topic_index"],
        fragments=procedure_fragments,
    )
    version_dependency = procedure_page["sections"]["version"]["dependency_record"]
    assert any(dep["normalized_value"] == "2026-08-10" for dep in version_dependency["version_deps"])
    assert "stale_after" not in version_dependency


@pytest.mark.parametrize("case", _cases()["version_cases"], ids=lambda case: case["id"])
def test_version_contract_rejects_conflicts_invalid_literals_and_omits_missing_product_version(
    case: dict[str, Any],
) -> None:
    normalizer = getattr(draft_module, "normalize_structure", None)
    builder = getattr(draft_module, "build_page_draft", None)
    assert callable(normalizer)
    assert callable(builder)

    fragments = normalizer(
        [
            {
                **source,
                "content_fingerprint": hashlib.sha256(source["text"].encode()).hexdigest(),
                "validation_status": "passed",
            }
            for source in case["sources"]
        ]
    )
    page = builder(topic_index=case["topic_index"], fragments=fragments)

    assert page["status"] == case["expected_status"]
    if case["expected_status"] == "degraded":
        assert case["reason_contains"] in page["audit_record"]["reason"]
        assert page["reader_eligible"] is False
    else:
        assert page["optional_sections"] == case["expected_optional_sections"]
        if case["id"] in {"missing-module-version", "missing-procedure-version"}:
            assert "version" not in page["required_sections"]
            assert "version" not in page["sections"]
        if case["topic_index"]["page_type"] in {"module_or_capability", "procedure_or_rule"}:
            if "version" in page["sections"]:
                version_record = page["sections"]["version"]["dependency_record"]
                assert version_record["version_deps"] == []
                assert "stale_after" not in version_record


@pytest.mark.parametrize("case_id", ["overview", "module", "procedure"])
def test_typed_sections_use_topic_index_mapping_and_fixed_matrix(case_id: str) -> None:
    case = next(item for item in _cases()["page_types"] if item["id"] == case_id)
    normalizer = getattr(draft_module, "normalize_structure", None)
    builder = getattr(draft_module, "build_page_draft", None)
    assert callable(normalizer)
    assert callable(builder)

    page = builder(
        topic_index=case["topic_index"],
        fragments=normalizer([_source_item(case)]),
    )

    assert page["page_type"] == case["topic_index"]["page_type"]
    assert page["topic_id"] == case["topic_index"]["topic_id"]
    assert set(page["required_sections"]) == set(case["expected_required_sections"])
    assert set(page["optional_sections"]) == set(case["expected_optional_sections"])
    assert set(page["sections"]) == set(case["expected_sections"])
    assert page["status"] == "draft"
    assert page["reader_eligible"] is False
    assert all(
        page["sections"][section_id]["dependency_record"]["schema_version"]
        == "section-dependency-record.v1"
        for section_id in page["sections"]
    )


@pytest.mark.parametrize("failure", _cases()["negative_provider_outputs"])
def test_provider_cannot_expand_typed_contract_or_enter_reader(failure: dict[str, Any]) -> None:
    case = _cases()["page_types"][0]
    normalizer = getattr(draft_module, "normalize_structure", None)
    builder = getattr(draft_module, "build_page_draft", None)
    validator = getattr(llm, "validate_section_response", None)
    assert callable(normalizer)
    assert callable(builder)
    assert callable(validator)

    page = builder(
        topic_index=case["topic_index"],
        fragments=normalizer([_source_item(case)]),
    )
    result = validator(page, failure["payload"])

    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False
    assert failure["reason_contains"] in result["reason"].casefold()
    assert result["audit_record"]["destination"] in {"Audit", "Archive"}


def test_publication_gate_rejects_unsupported_reader_fact() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)

    payload = _provenance_payload(
        "Alpha serves 999 unrelated customers. [^claim-alpha-1]\n\n"
        "[^claim-alpha-1]: https://docs.example.test/alpha/overview#lines:3-3"
    )
    result = gate(payload)

    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False
    assert any("token or faithfulness mismatch" in reason for reason in result["reasons"])
    assert result["audit_record"]["destination"] in {"Audit", "Archive"}


def test_publication_gate_does_not_trust_typed_mapping_for_unsupported_fact() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)

    payload = _provenance_payload(
        "Alpha serves 999 unrelated customers. [^claim-alpha-1]\n\n"
        "[^claim-alpha-1]: https://docs.example.test/alpha/overview#lines:3-3"
    )
    payload["typed_claim_ids"] = ["claim-alpha-1"]
    result = gate(payload)

    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False
    assert any("token or faithfulness mismatch" in reason for reason in result["reasons"])


@pytest.mark.parametrize("mapping_status", ["unmapped", "conflict"])
def test_unmapped_or_conflicting_topic_index_is_audit_only(mapping_status: str) -> None:
    base = next(item for item in _cases()["page_types"] if item["id"] == "overview")
    topic_index = next(item for item in _cases()["topic_index_failures"] if item["mapping_status"] == mapping_status)
    normalizer = getattr(draft_module, "normalize_structure", None)
    builder = getattr(draft_module, "build_page_draft", None)
    assert callable(normalizer)
    assert callable(builder)

    page = builder(topic_index=topic_index, fragments=normalizer([_source_item(base)]))

    assert page["status"] == "degraded"
    assert page["reader_eligible"] is False
    assert page["audit_record"]["destination"] in {"Audit", "Archive"}
    assert mapping_status in page["audit_record"]["reason"]


def test_degraded_topic_mapping_skips_provider_calls_and_keeps_audit_state(tmp_path: Path) -> None:
    base = next(item for item in _cases()["page_types"] if item["id"] == "overview")
    topic_index = next(
        item
        for item in _cases()["topic_index_failures"]
        if item["mapping_status"] == "unmapped"
    )
    calls: list[dict[str, Any]] = []

    def provider(context: dict[str, Any]) -> dict[str, Any]:
        calls.append(context)
        raise AssertionError("an unmapped page must not call the provider")

    result = draft_module.draft(
        [
            {
                "cluster_id": "cluster-unmapped",
                "action": "new",
                "target_paths": [],
                "topic_id": topic_index["topic_id"],
                "topic_index": topic_index,
            }
        ],
        [{"cluster_id": "cluster-unmapped", "members": [base["source"]["raw_id"]]}],
        [_source_item(base)],
        tmp_path,
        DigestSettings(llm_enabled=True),
        generator=provider,
    )[0]

    assert calls == []
    assert result["planned_generator_calls"] == 0
    assert result["typed_page_draft"]["status"] == "degraded"
    assert result["typed_response"]["status"] == "degraded"
    assert result["provider_failure"] is True
    assert result["provider_failures"][0]["provider_call_skipped"] is True


def _provenance_payload(body: str, *, provider_status: str = "ok") -> dict[str, Any]:
    fixture = _cases()["provenance_cases"]
    claims = [dict(claim) for claim in fixture["claims"]]
    return {
        "page_type": "product_overview",
        "body": body,
        "sections": [
            {
                "section_id": "positioning",
                "body": body,
                "claim_ids": ["claim-alpha-1"],
            }
        ],
        "claims": claims,
        "evidence_body": fixture["evidence_body"],
        "provider_status": provider_status,
        "duplicate_context": fixture["duplicate_context"],
    }


def test_provenance_gate_keeps_reader_body_separate_from_evidence_and_backtraceable() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate), "Task 2-B must expose a deterministic Publication Gate seam"

    result = gate(_provenance_payload(_cases()["provenance_cases"]["supported_body"]))

    assert result["status"] == "published"
    assert result["reader_eligible"] is True
    assert result["body"] != result["evidence_body"]
    assert result["evidence"]["claim_backtrace"][0]["claim_id"] == "claim-alpha-1"
    assert result["evidence"]["claim_backtrace"][0]["source_uri"] == "https://docs.example.test/alpha/overview"
    assert result["evidence"]["claim_backtrace"][0]["fragment_locator"] == "lines:3-3"


def test_provenance_gate_accepts_typed_claim_backtrace_for_a_faithful_paraphrase() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)
    payload = _provenance_payload(
        "Alpha serves 99% of internal cases in practice. [^claim-alpha-1]"
    )
    payload["typed_claim_ids"] = ["claim-alpha-1"]

    result = gate(payload)

    assert result["status"] == "published"
    assert result["evidence"]["claim_backtrace"][0]["claim_id"] == "claim-alpha-1"

    incomplete = {**payload, "typed_claim_ids": []}
    incomplete_result = gate(incomplete)
    assert incomplete_result["status"] == "degraded"
    assert any("typed claim mapping is incomplete" in reason for reason in incomplete_result["reasons"])


def test_publication_gate_rejects_typed_mapping_when_numeric_fact_changes() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)

    payload = _provenance_payload(
        "Alpha supports 100% of internal cases. [^claim-alpha-1]\n\n"
        "[^claim-alpha-1]: https://docs.example.test/alpha/overview#lines:3-3"
    )
    payload["typed_claim_ids"] = ["claim-alpha-1"]
    result = gate(payload)

    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False
    assert any("token or faithfulness mismatch" in reason for reason in result["reasons"])


def test_provenance_gate_requires_unique_backtrace_for_each_claim() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)
    payload = _provenance_payload(_cases()["provenance_cases"]["supported_body"])
    second = {
        **payload["claims"][0],
        "claim_id": "claim-alpha-2",
        "fragment_locator": "lines:4-4",
        "content_fingerprint": "b" * 64,
        "text": "Alpha also supports scheduled exports.",
    }
    payload["claims"].append(second)
    payload["body"] = (
        "Alpha supports 99% of internal cases. [^claim-alpha-1]\n"
        "Alpha also supports scheduled exports. [^claim-alpha-2]"
    )
    result = gate(payload)
    assert result["status"] == "published"
    assert {row["claim_id"] for row in result["evidence"]["claim_backtrace"]} == {
        "claim-alpha-1",
        "claim-alpha-2",
    }

    duplicate = {**payload, "claims": [payload["claims"][0], {**payload["claims"][1], "claim_id": "claim-alpha-1"}]}
    duplicate_result = gate(duplicate)
    assert duplicate_result["status"] == "degraded"
    assert any("not unique" in reason for reason in duplicate_result["reasons"])


@pytest.mark.parametrize(
    ("body_key", "reason_part"),
    [
        ("token_tampered_body", "token"),
        ("missing_attribution_body", "attribution"),
    ],
)
def test_provenance_gate_rejects_tampering_and_unattributed_facts(
    body_key: str,
    reason_part: str,
) -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)

    result = gate(_provenance_payload(_cases()["provenance_cases"][body_key]))

    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False
    assert any(reason_part in reason.casefold() for reason in result["reasons"])
    assert result["audit_record"]["destination"] in {"Audit", "Archive"}


def test_provenance_gate_records_duplicate_detector_facts_and_blocks_near_duplicate() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)

    fixture = _cases()["provenance_cases"]
    result = gate(_provenance_payload(fixture["near_duplicate_body"]))

    duplicate = result["checks"]["duplicate"]
    assert duplicate["denominator"] == fixture["duplicate_context"]["denominator"]
    assert duplicate["detector_version"] == "jaccard-5gram.v1"
    assert duplicate["seed"] == 17
    assert duplicate["failed_samples"]
    assert all(sample["jaccard"] >= 0.92 for sample in duplicate["failed_samples"] if "jaccard" in sample)
    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False

    unrelated = _provenance_payload(_cases()["provenance_cases"]["supported_body"])
    unrelated["duplicate_context"] = {
        "same_page": ["A wholly unrelated sentence with different evidence."],
        "cross_page": ["Another unrelated page with no shared claim."],
        "denominator": 2,
        "detector_version": "jaccard-5gram.v1",
        "seed": 17,
    }
    unrelated_result = gate(unrelated)
    assert unrelated_result["status"] == "published"
    assert unrelated_result["checks"]["duplicate"]["failed_samples"] == []

    short = {
        **unrelated,
        "body": "A [^claim-short]",
        "evidence_body": "A",
        "claims": [{
            "claim_id": "claim-short",
            "source_uri": "u",
            "fragment_locator": "l",
            "text": "A",
            "content_fingerprint": "c" * 64,
        }],
    }
    short_result = gate(short)
    assert short_result["status"] == "published"


def test_provenance_gate_requires_content_fingerprint_and_source_block_limit() -> None:
    gate = getattr(publication_module, "validate_body_gate", None)
    assert callable(gate)
    fixture = _cases()["provenance_cases"]

    missing_fingerprint = _provenance_payload(fixture["supported_body"])
    missing_fingerprint["claims"][0].pop("content_fingerprint")
    missing_result = gate(missing_fingerprint)
    assert missing_result["status"] == "degraded"
    assert "attribution is incomplete" in " ".join(missing_result["reasons"])

    copied = "Alpha supports 99% of internal cases. " + " ".join(
        f"Copied source sentence {index} remains unchanged." for index in range(1, 8)
    )
    copied_payload = _provenance_payload(copied + " [^claim-alpha-1]")
    copied_payload["evidence_body"] = copied
    copied_result = gate(copied_payload)
    assert copied_result["status"] == "degraded"
    assert copied_result["checks"]["continuous_source_block"]["failed_samples"]
    assert any("continuous source block" in reason for reason in copied_result["reasons"])


@pytest.mark.parametrize(
    "provider_payload",
    [
        "",
        "{\"page_type\":\"product_overview\",\"sections\":{",
    ],
)
def test_provider_empty_or_truncated_output_stays_degraded(provider_payload: str) -> None:
    case = _cases()["page_types"][0]
    normalizer = getattr(draft_module, "normalize_structure", None)
    builder = getattr(draft_module, "build_page_draft", None)
    validator = getattr(llm, "validate_section_response", None)
    assert callable(normalizer)
    assert callable(builder)
    assert callable(validator)

    page = builder(
        topic_index=case["topic_index"],
        fragments=normalizer([_source_item(case)]),
    )
    result = validator(page, provider_payload)

    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False


def test_mapped_typed_section_without_claim_mapping_stays_degraded() -> None:
    case = _cases()["page_types"][0]
    builder = getattr(draft_module, "build_page_draft", None)
    validator = getattr(llm, "validate_section_response", None)
    assert callable(builder)
    assert callable(validator)
    page = builder(
        topic_index=case["topic_index"],
        fragments=draft_module.normalize_structure([_source_item(case)]),
    )
    page["claims"] = [{"claim_fingerprint": "f" * 64}]
    payload = {
        "page_type": case["page_type"],
        "sections": {
            section_id: {"body": "Alpha platform uses Alpha Console v2.1.", "claim_ids": []}
            for section_id in case["expected_sections"]
        },
    }
    result = validator(page, payload)
    assert result["status"] == "degraded"
    assert "claim mapping is missing" in result["reason"]


def test_typed_validator_does_not_turn_markdown_table_delimiters_into_reader_claims() -> None:
    case = _cases()["page_types"][0]
    builder = getattr(draft_module, "build_page_draft", None)
    validator = getattr(llm, "validate_section_response", None)
    assert callable(builder)
    assert callable(validator)
    page = builder(
        topic_index=case["topic_index"],
        fragments=draft_module.normalize_structure([_source_item(case)]),
    )
    delimiter_id = "d" * 64
    page["claims"] = [{"claim_fingerprint": delimiter_id, "text": "| --- | --- |"}]
    payload = {
        "page_type": case["page_type"],
        "sections": {
            section_id: {"body": "Alpha platform.", "claim_ids": []}
            for section_id in case["expected_sections"]
        },
    }
    payload["sections"]["positioning"]["claim_ids"] = [delimiter_id]

    result = validator(page, payload)

    assert result["status"] == "degraded"
    assert "claim mapping is missing" in result["reason"]


def test_structure_normalizer_consumes_fenced_code_as_one_fragment() -> None:
    fragments = draft_module.normalize_structure([{
        "raw_id": "raw-code",
        "source_uri": "raw://code",
        "text": "# Heading\n```python\n# not a heading\nprint('x')\n```\n## Next",
        "validation_status": "passed",
    }])
    code = [fragment for fragment in fragments if fragment["content_type"] == "code"]
    assert len(code) == 1
    assert "# not a heading" in code[0]["text"]
    assert any(fragment["text"] == "## Next" for fragment in fragments)


def test_page_draft_dependency_hash_includes_claim_and_attribution_lineage() -> None:
    case = _cases()["page_types"][0]
    builder = getattr(draft_module, "build_page_draft", None)
    assert callable(builder)
    fragments = draft_module.normalize_structure([_source_item(case)])
    first = builder(
        topic_index=case["topic_index"],
        fragments=fragments,
        claims=[{
            "claim_fingerprint": "a" * 64,
            "source_uri": case["source"]["source_uri"],
            "fragment_locator": "lines:3-3",
            "content_fingerprint": "b" * 64,
        }],
    )
    second = builder(
        topic_index=case["topic_index"],
        fragments=fragments,
        claims=[{
            "claim_fingerprint": "c" * 64,
            "source_uri": case["source"]["source_uri"],
            "fragment_locator": "lines:3-3",
            "content_fingerprint": "d" * 64,
        }],
    )
    first_record = first["sections"]["positioning"]["dependency_record"]
    second_record = second["sections"]["positioning"]["dependency_record"]
    assert first_record["claim_deps"][0]["claim_fingerprint"] == "a" * 64
    assert first_record["attribution_deps"][0]["content_fingerprint"] == "b" * 64
    assert first_record["dependency_hash"] != second_record["dependency_hash"]


def test_typed_claim_mapping_binds_dependencies_to_each_section() -> None:
    case = _cases()["page_types"][0]
    page = draft_module.build_page_draft(
        topic_index=case["topic_index"],
        fragments=draft_module.normalize_structure([_source_item(case)]),
    )
    fragments = [
        fragment
        for fragment in page["source_fragments"]
        if fragment.get("content_type") != "heading"
    ]
    assert len(fragments) >= 2
    claims = [
        {
            "claim_fingerprint": "a" * 64,
            "source_uri": fragments[0]["source_uri"],
            "raw_id": fragments[0]["raw_id"],
            "fragment_locator": fragments[0]["fragment_locator"],
            "content_fingerprint": "b" * 64,
        },
        {
            "claim_fingerprint": "c" * 64,
            "source_uri": fragments[1]["source_uri"],
            "raw_id": fragments[1]["raw_id"],
            "fragment_locator": fragments[1]["fragment_locator"],
            "content_fingerprint": "d" * 64,
        },
    ]
    page["claims"] = claims
    binder = getattr(draft_module, "_bind_typed_section_dependencies", None)
    assert callable(binder)
    result = binder(
        page,
        {
            "status": "draft",
            "page_type": case["page_type"],
            "sections": {
                "positioning": {"body": "Alpha", "claim_ids": ["a" * 64]},
                "use_cases": {"body": "Beta", "claim_ids": ["c" * 64]},
            },
        },
        claims,
    )

    first = result["sections"]["positioning"]["dependency_record"]
    second = result["sections"]["use_cases"]["dependency_record"]
    assert first["dependency_scope"] == "resolved"
    assert second["dependency_scope"] == "resolved"
    assert [row["claim_id"] for row in first["claim_deps"]] == ["a" * 64]
    assert [row["claim_id"] for row in second["claim_deps"]] == ["c" * 64]
    assert first["dependency_hash"] != second["dependency_hash"]


def test_typed_body_gate_payload_carries_duplicate_context() -> None:
    builder = getattr(pipeline_module, "_typed_body_gate_payload", None)
    assert callable(builder)
    payload = builder(
        {
            "claims": [],
            "typed_page_draft": {"source_fragments": []},
        },
        {"sections": {"positioning": {"body": "Alpha", "claim_ids": []}}},
        duplicate_context={
            "same_page": ["same"],
            "cross_page": ["cross"],
            "denominator": 2,
            "detector_version": "jaccard-5gram.v1",
            "seed": 0,
        },
    )
    assert payload["duplicate_context"]["denominator"] == 2
    assert payload["duplicate_context"]["same_page"] == ["same"]
    assert payload["duplicate_context"]["cross_page"] == ["cross"]


def test_typed_body_gate_separates_reader_claims_from_complete_evidence_ledger() -> None:
    builder = getattr(pipeline_module, "_typed_body_gate_payload", None)
    assert callable(builder)
    claims = [
        {
            "claim_id": "claim-used",
            "claim_fingerprint": "a" * 64,
            "text": "The reader body states this fact.",
            "source_uri": "raw://used",
            "fragment_locator": "lines:1-1",
        },
        {
            "claim_id": "claim-evidence-only",
            "claim_fingerprint": "b" * 64,
            "text": "This complete source fact remains in evidence.",
            "source_uri": "raw://evidence-only",
            "fragment_locator": "lines:2-2",
        },
    ]
    payload = builder(
        {
            "claims": claims,
            "typed_page_draft": {
                "source_fragments": [
                    {"text": claim["text"], "content_type": "text"}
                    for claim in claims
                ]
            },
        },
        {
            "sections": {
                "positioning": {
                    "body": "The reader body states this fact.",
                    "claim_ids": ["claim-used"],
                }
            }
        },
    )

    assert [claim["claim_id"] for claim in payload["claims"]] == ["claim-used"]
    assert [claim["claim_id"] for claim in payload["evidence_claims"]] == [
        "claim-used",
        "claim-evidence-only",
    ]
    assert "[^claim-evidence-only]" not in payload["body"]
    assert "claim-evidence-only" not in payload["typed_claim_ids"]


def test_typed_body_gate_projects_repeated_source_claim_once_but_keeps_evidence_occurrences() -> None:
    builder = getattr(pipeline_module, "_typed_body_gate_payload", None)
    assert callable(builder)
    claim_fingerprint = "c" * 64
    repeated_claims = [
        {
            "claim_fingerprint": claim_fingerprint,
            "text": "The same source fact appears twice.",
            "source_uri": "raw://repeated",
            "fragment_locator": "lines:1-1",
            "content_fingerprint": "d" * 64,
        },
        {
            "claim_fingerprint": claim_fingerprint,
            "text": "The same source fact appears twice.",
            "source_uri": "raw://repeated",
            "fragment_locator": "lines:4-4",
            "content_fingerprint": "d" * 64,
        },
    ]
    payload = builder(
        {
            "claims": repeated_claims,
            "typed_page_draft": {
                "source_fragments": [{"text": repeated_claims[0]["text"], "content_type": "text"}]
            },
        },
        {
            "sections": {
                "positioning": {
                    "body": repeated_claims[0]["text"],
                    "claim_ids": [claim_fingerprint],
                }
            }
        },
    )

    assert [claim["fragment_locator"] for claim in payload["evidence_claims"]] == [
        "lines:1-1",
        "lines:4-4",
    ]
    assert [claim["fragment_locator"] for claim in payload["claims"]] == ["lines:1-1"]
    assert payload["typed_claim_ids"] == [claim_fingerprint]


def test_shared_section_claim_gets_one_semantic_part_owner() -> None:
    owners = getattr(pipeline_module, "_semantic_section_claim_owners", None)
    assert callable(owners)
    sections = owners(
        [
            {"section_id": "positioning", "body": "Shared fact", "claim_ids": ["shared", "first"]},
            {"section_id": "use_cases", "body": "Same shared fact", "claim_ids": ["shared", "second"]},
        ]
    )

    semantic = page_layout.build_semantic_parts(
        topic_id="topic-shared-claim",
        title="Shared claim",
        page_type="product_overview",
        sections=sections,
        claims=[
            {"claim_id": "shared", "text": "Shared fact"},
            {"claim_id": "first", "text": "First fact"},
            {"claim_id": "second", "text": "Second fact"},
        ],
    )

    assert sections[0]["claim_ids"] == ["shared", "first"]
    assert sections[1]["claim_ids"] == ["second"]
    assert semantic["valid"] is True
    assert [claim_id for part in semantic["parts"] for claim_id in part["claim_ids"]] == [
        "shared",
        "first",
        "second",
    ]


def _dependency_record(section_id: str, *, content_hash: str, claim_id: str) -> dict[str, Any]:
    builder = getattr(page_layout, "build_section_dependency_record", None)
    assert callable(builder)
    return builder(
        topic_id="topic-alpha",
        page_type="product_overview",
        section_id=section_id,
        source_deps=[
            {
                "source_uri": "https://docs.example.test/alpha/overview",
                "content_hash": content_hash,
                "fragment_locator": "lines:3-3",
            }
        ],
        claim_deps=[{"claim_id": claim_id, "claim_fingerprint": "c" * 64}],
        version_deps=[{"field": "version", "normalized_value": "v2.1", "claim_id": claim_id}],
        structure_deps=[
            {
                "fragment_locator": "lines:1-1",
                "relation_type": "child_of",
                "structure_hash": "s" * 64,
            }
        ],
        attribution_deps=[
            {
                "claim_id": claim_id,
                "source_uri": "https://docs.example.test/alpha/overview",
                "content_hash": content_hash,
                "fragment_locator": "lines:3-3",
            }
        ],
    )


def test_impact_closure_recompiles_changed_section_and_reuses_only_unchanged_sections() -> None:
    evaluator = getattr(page_layout, "evaluate_section_impact", None)
    assert callable(evaluator), "Task 2-B must expose a section dependency impact seam"
    fixture = _cases()["impact_cases"]
    old_sections = [
        {
            "section_id": "positioning",
            "body": fixture["old"]["positioning_body"],
            "target_path": "pages/topic-alpha/index.md",
            "dependency_record": _dependency_record("positioning", content_hash="a" * 64, claim_id="claim-positioning"),
            "signal_status": "verified",
        },
        {
            "section_id": "limitations",
            "body": fixture["old"]["limitations_body"],
            "target_path": "pages/topic-alpha/index.md",
            "dependency_record": _dependency_record("limitations", content_hash="b" * 64, claim_id="claim-limitations"),
            "signal_status": "verified",
        },
    ]
    new_sections = [
        {
            "section_id": "positioning",
            "body": fixture["changed"]["positioning_body"],
            "target_path": "pages/topic-alpha/index.md",
            "dependency_record": _dependency_record("positioning", content_hash="d" * 64, claim_id="claim-positioning-new"),
            "signal_status": "verified",
        },
        {
            "section_id": "limitations",
            "body": fixture["changed"]["limitations_body"],
            "target_path": "pages/topic-alpha/index.md",
            "dependency_record": _dependency_record("limitations", content_hash="b" * 64, claim_id="claim-limitations"),
            "signal_status": "verified",
        },
    ]

    result = evaluator(old_sections, new_sections)

    assert result["recompile_scope"] == "sections"
    assert result["affected_sections"] == ["positioning"]
    assert result["reused_sections"] == ["limitations"]
    assert result["old_signal_invalidated"] == ["positioning"]
    assert result["safe_reuse_proof"]["limitations"] is True
    assert result["content_hash_proof"]["limitations"]["equal"] is True
    assert result["path_byte_proof"]["limitations"]["equal"] is True


def test_impact_closure_unknown_dependency_expands_to_whole_page() -> None:
    evaluator = getattr(page_layout, "evaluate_section_impact", None)
    assert callable(evaluator)
    fixture = _cases()["impact_cases"]
    result = evaluator(
        [
            {
                "section_id": "positioning",
                "body": fixture["old"]["positioning_body"],
                "target_path": "pages/topic-alpha/index.md",
                "dependency_record": None,
                "signal_status": "verified",
            }
        ],
        [
            {
                "section_id": "positioning",
                "body": fixture["changed"]["positioning_body"],
                "target_path": "pages/topic-alpha/index.md",
                "dependency_record": _dependency_record("positioning", content_hash="d" * 64, claim_id="claim-positioning-new"),
                "signal_status": "verified",
            }
        ],
    )

    assert result["recompile_scope"] == "page"
    assert result["uncertain"] is True
    assert result["reused_sections"] == []
    assert "dependency" in result["reason"].casefold()


def test_impact_closure_failed_recompile_preserves_old_reader_page_without_splicing_new_body() -> None:
    protector = getattr(page_layout, "protect_old_page_on_failure", None)
    assert callable(protector)
    fixture = _cases()["impact_cases"]

    result = protector(fixture["old_reader_page"], fixture["failed_candidate_page"])

    assert result["status"] == "degraded"
    assert result["reader_eligible"] is False
    assert result["candidate"]["reader_eligible"] is False
    assert result["reader_projection"]["reader_eligible"] is True
    assert result["reader_projection"]["body"] == fixture["old_reader_page"]["body"]
    assert result["reader_projection"]["body"] != fixture["old_reader_page"]["body"] + "\n" + fixture["failed_candidate_page"]["body"]
    assert result["audit_record"]["destination"] in {"Audit", "Archive"}


def _semantic_split_input() -> dict[str, Any]:
    fixture = _cases()["semantic_split"]
    sections = []
    for section in fixture["sections"]:
        body = [
            f"{section['section_id']} semantic line {index + 1}"
            for index in range(section["body_line_count"])
        ]
        sections.append(
            {
                "section_id": section["section_id"],
                "heading": section["heading"],
                "body": body,
                "claim_ids": section["claim_ids"],
            }
        )
    return {
        "topic_id": fixture["topic_id"],
        "title": fixture["title"],
        "page_type": fixture["page_type"],
        "sections": sections,
        "claims": fixture["claims"],
    }


def test_semantic_split_keeps_overview_navigation_limits_and_claim_exactly_once() -> None:
    builder = getattr(page_layout, "build_semantic_parts", None)
    validator = getattr(page_layout, "validate_semantic_parts", None)
    nav_builder = getattr(navigation, "build_topic_part_navigation", None)
    assert callable(builder), "Task 2-B must expose a semantic partition seam"
    assert callable(validator)
    assert callable(nav_builder)

    result = builder(**_semantic_split_input())
    navigation_rows = nav_builder(
        result["parts"],
        overview_path=result["overview"]["target_path"],
        related_key=result["related_key"],
    )
    checked = validator(result)

    assert checked["valid"] is True
    assert result["overview"]["target_path"]
    assert result["related_key"] == "topic-long-alpha"
    assert len(result["parts"]) >= 2
    assert all(len(part["body"].splitlines()) <= 120 for part in result["parts"])
    assert all(len(part["rendered_body"].splitlines()) <= 300 for part in result["parts"])
    assert all(part["entry_path"] for part in result["parts"])
    assert result["parts"][0]["prev"] is None
    assert result["parts"][-1]["next"] is None
    assert all(part["overview_path"] == result["overview"]["target_path"] for part in result["parts"])
    assert navigation_rows[0]["prev"] is None
    assert navigation_rows[-1]["next"] is None
    assert all(row["related_key"] == "topic-long-alpha" for row in navigation_rows)
    claim_counts = {
        claim_id: sum(claim_id in part["claim_ids"] for part in result["parts"])
        for claim_id in {claim["claim_id"] for claim in _semantic_split_input()["claims"]}
    }
    assert set(claim_counts.values()) == {1}
    section_part_counts = {
        section["section_id"]: sum(
            section["section_id"] in part["section_ids"] for part in result["parts"]
        )
        for section in _cases()["semantic_split"]["sections"]
    }
    assert set(section_part_counts.values()) == {1}


def test_semantic_split_rejects_part_without_entry_and_part1_only_navigation() -> None:
    builder = getattr(page_layout, "build_semantic_parts", None)
    validator = getattr(page_layout, "validate_semantic_parts", None)
    assert callable(builder)
    assert callable(validator)
    result = builder(**_semantic_split_input())

    missing_entry = {
        **result,
        "parts": [{**result["parts"][0], "entry_path": ""}, *result["parts"][1:]],
    }
    part1_only = {
        **result,
        "overview": {**result["overview"], "target_path": result["parts"][0]["target_path"]},
    }

    assert validator(missing_entry)["valid"] is False
    assert validator(part1_only)["valid"] is False


def test_semantic_exit_validates_all_machine_fields_but_keeps_delivery_not_released() -> None:
    validator = getattr(publication_module, "validate_semantic_evidence", None)
    assert callable(validator), "Task 2-B must expose a semantic exit validator"
    fixture = {
        **_cases()["semantic_evidence_file"]["valid_machine_fixture"],
        "execution_mode": "real_semantic",
        "run_identity": {
            "run_id": "run-real-semantic-fixture-1",
            "sample_fingerprint": "a" * 64,
            "kb_fingerprint": "b" * 64,
            "input_fingerprint": "c" * 64,
        },
        "provider": {
            "provider": "qwen3.6",
            "model": "qwen3.6",
            "base_url": "https://dashscope.in.whatspos.cn/v1",
        },
    }
    fixture["run_id"] = "run-real-semantic-fixture-1"
    fixture["sample_manifest"] = {**fixture["sample_manifest"], "content_hash": "d" * 64}
    fixture["answerability_subset"] = {**fixture["answerability_subset"], "content_hash": "e" * 64}
    result = validator(fixture)

    assert result["valid"] is True
    assert result["machine_exit_passed"] is True
    assert result["delivery_status"] == "not_released"
    assert result["sample_count"] == 12
    assert result["page_type_counts"] == {
        "module_or_capability": 2,
        "procedure_or_rule": 2,
        "product_overview": 2,
    }
    assert set(result["ac_bindings"]) == {
        "AC-01",
        "AC-03",
        "AC-05",
        "AC-07",
        "AC-09",
        "AC-10",
        "AC-11",
        "AC-12",
        "AC-13",
    }


def test_semantic_exit_rejects_offline_fixture_as_machine_pass() -> None:
    validator = getattr(publication_module, "validate_semantic_evidence", None)
    assert callable(validator)
    result = validator(_cases()["semantic_evidence_file"]["valid_machine_fixture"])

    assert result["valid"] is False
    assert result["machine_exit_passed"] is False
    assert any("offline fixtures" in reason for reason in result["reasons"])


def test_semantic_exit_rejects_fixture_relabelled_as_real_semantic() -> None:
    validator = getattr(publication_module, "validate_semantic_evidence", None)
    assert callable(validator)
    fixture = {
        **_cases()["semantic_evidence_file"]["valid_machine_fixture"],
        "execution_mode": "real_semantic",
    }

    result = validator(fixture)

    assert result["valid"] is False
    assert result["machine_exit_passed"] is False
    assert any("non-fixture provider" in reason for reason in result["reasons"])


def test_semantic_evidence_derives_task0_first_hits_without_claiming_human_review() -> None:
    derive = getattr(pipeline_module, "_task2b_answerability_subset", None)
    assert callable(derive)
    question_set = json.loads(
        (Path(__file__).parents[2] / "config" / "task0-question-set.v1.json").read_text(
            encoding="utf-8"
        )
    )
    question_set["question_set_hash"] = "a" * 64
    subset = derive(
        question_set=question_set,
        concepts=[
            {
                "concept_id": "overview-1",
                "page_type": "product_overview",
                "status": "machine-passing",
                "section_ids": ["positioning", "use_cases", "sources", "version"],
            },
            {
                "concept_id": "procedure-1",
                "page_type": "procedure_or_rule",
                "status": "machine-passing",
                "section_ids": ["prerequisites", "steps_rules", "exceptions", "version", "sources"],
            },
        ],
    )

    assert len(subset["questions"]) == 20
    assert next(row for row in subset["questions"] if row["question_id"] == "positive-04")["first_hit"] == "procedure-1"
    assert next(row for row in subset["questions"] if row["question_id"] == "negative-01")["answerable"] is False
    assert "not human reader review" in subset["reason"]


@pytest.mark.parametrize(
    "fixture_name",
    ["invalid_fallback", "missing_fields"],
)
def test_semantic_exit_rejects_fallback_or_missing_fields_without_passing(
    fixture_name: str,
) -> None:
    validator = getattr(publication_module, "validate_semantic_evidence", None)
    assert callable(validator)
    semantic_fixtures = _cases()["semantic_evidence_file"]
    fixture = semantic_fixtures[fixture_name] if fixture_name != "missing_fields" else {
        **semantic_fixtures["valid_machine_fixture"],
        "evidence_backtrace": [],
        "ac_bindings": {"AC-01": "only-one-binding"},
    }
    result = validator(fixture)

    assert result["valid"] is False
    assert result["machine_exit_passed"] is False
    assert result["delivery_status"] == "not_released"
    assert result["reasons"]
    assert result["reader_eligible"] is False


def test_semantic_evidence_file_binds_one_path_and_run_identity(tmp_path: Path) -> None:
    validator = getattr(publication_module, "validate_semantic_evidence_file", None)
    assert callable(validator), "Task 2-B must expose a run-bound semantic evidence file validator"
    fixture = {
        **_cases()["semantic_evidence_file"]["valid_machine_fixture"],
        "execution_mode": "real_semantic",
    }
    fixture["run_identity"] = {
        **fixture["run_identity"],
        "run_id": "run-file-1",
        "sample_fingerprint": "a" * 64,
        "kb_fingerprint": "b" * 64,
        "input_fingerprint": "c" * 64,
    }
    fixture["run_id"] = "run-file-1"
    fixture["provider"] = {
        "provider": "qwen3.6",
        "model": "qwen3.6",
        "base_url": "https://dashscope.in.whatspos.cn/v1",
    }
    fixture["sample_manifest"] = {**fixture["sample_manifest"], "content_hash": "d" * 64}
    fixture["answerability_subset"] = {**fixture["answerability_subset"], "content_hash": "e" * 64}
    output_path = tmp_path / "semantic-run.json"
    fixture["output_path"] = str(output_path.resolve())
    output_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")

    result = validator(
        output_path,
        expected_run_id="run-file-1",
        expected_output_path=output_path,
    )

    assert result["valid"] is True
    assert result["machine_exit_passed"] is True
    assert validator(output_path, expected_run_id="run-other") ["valid"] is False


def test_pipeline_compat_failure_stays_in_audit_and_preserves_old_reader_page() -> None:
    compiler = getattr(pipeline_module, "compile_publication_candidate", None)
    assert callable(compiler), "Task 2-B must expose the formal pipeline compiler seam"
    case = _cases()["page_types"][0]
    page = draft_module.build_page_draft(
        topic_index=case["topic_index"],
        fragments=draft_module.normalize_structure([_source_item(case)]),
    )
    old_page = _cases()["impact_cases"]["old_reader_page"]

    result = compiler(page_draft=page, provider_payload="", old_page=old_page)

    assert result["status"] == "degraded"
    assert result["candidate"]["reader_eligible"] is False
    assert result["navigation_records"] == []
    assert result["reader_projection"]["body"] == old_page["body"]
    assert result["reader_projection"]["target_path"] == old_page["target_path"]
    assert result["audit_record"]["destination"] in {"Audit", "Archive"}
    assert result["reader_projection"]["body"] != old_page["body"] + "\n" + result["candidate"].get("body", "")


def test_pipeline_loads_only_the_bound_existing_reader_page_for_failure_protection(tmp_path: Path) -> None:
    kb_dir = tmp_path / "kb"
    target = kb_dir / "pages" / "topic-alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("---\nmanaged_by: KnowledgeDigest\n---\n\nold reader body\n", encoding="utf-8")
    paths = DigestPaths(tmp_path / "input", tmp_path / "input" / "items", kb_dir, kb_dir / "kb.structure.md")

    loader = getattr(pipeline_module, "_existing_reader_page", None)
    assert callable(loader)
    result = loader(paths, {"published_path": "pages/topic-alpha.md", "target_paths": []})

    assert result == {
        "status": "published",
        "reader_eligible": True,
        "body": "---\nmanaged_by: KnowledgeDigest\n---\n\nold reader body\n",
        "target_path": "pages/topic-alpha.md",
    }
    assert loader(paths, {"published_path": "../outside.md", "target_paths": []}) is None


def test_writeback_reader_gate_consumes_compiler_projection() -> None:
    gate = getattr(pipeline_module, "_reader_record_is_eligible", None)
    assert callable(gate)
    assert gate({"page_status": "published", "reader_projection": {"reader_eligible": True}}) is True
    assert gate({"page_status": "published", "reader_projection": {"reader_eligible": False}}) is False
    assert gate({"page_status": "degraded", "reader_projection": {"reader_eligible": True}}) is False


@pytest.mark.parametrize("mapping_status", ["unmapped", "conflict"])
def test_pipeline_compat_topic_identity_and_frozen_input_failures_never_enter_reader(
    mapping_status: str,
) -> None:
    compiler = getattr(pipeline_module, "compile_publication_candidate", None)
    assert callable(compiler)
    base = next(item for item in _cases()["page_types"] if item["id"] == "overview")
    topic_index = next(
        item
        for item in _cases()["topic_index_failures"]
        if item["mapping_status"] == mapping_status
    )
    page = draft_module.build_page_draft(
        topic_index=topic_index,
        fragments=draft_module.normalize_structure([_source_item(base)]),
    )
    result = compiler(
        page_draft=page,
        provider_payload={"page_type": "product_overview", "sections": {}},
        frozen_input={"required": True, "available": False},
    )

    assert result["status"] == "degraded"
    assert result["candidate"]["reader_eligible"] is False
    assert result["navigation_records"] == []
    assert result["audit_record"]["destination"] in {"Audit", "Archive"}
    assert mapping_status in result["audit_record"]["reason"] or "frozen" in result["audit_record"]["reason"]


def test_pipeline_compat_fingerprint_mismatch_is_audit_only() -> None:
    compiler = getattr(pipeline_module, "compile_publication_candidate", None)
    assert callable(compiler)
    case = _cases()["page_types"][0]
    page = draft_module.build_page_draft(
        topic_index=case["topic_index"],
        fragments=draft_module.normalize_structure([_source_item(case)]),
    )

    result = compiler(
        page_draft=page,
        provider_payload="",
        frozen_input={
            "required": True,
            "available": True,
            "expected_fingerprint": "a" * 64,
            "actual_fingerprint": "b" * 64,
        },
    )

    assert result["status"] == "degraded"
    assert result["candidate"]["reader_eligible"] is False
    assert result["navigation_records"] == []
    assert "fingerprint" in result["audit_record"]["reason"]


def test_pipeline_compat_success_projects_one_stable_reader_navigation() -> None:
    compiler = getattr(pipeline_module, "compile_publication_candidate", None)
    assert callable(compiler)
    case = _cases()["page_types"][0]
    page = draft_module.build_page_draft(
        topic_index=case["topic_index"],
        fragments=draft_module.normalize_structure([_source_item(case)]),
    )
    section_claims = []
    typed_sections = {}
    body_parts = []
    for index, section_id in enumerate(case["expected_sections"], start=1):
        claim_id = f"claim-alpha-{index}"
        claim_text = f"Alpha {section_id} is documented in the source."
        section_claims.append({
            "claim_id": claim_id,
            "source_uri": "raw://alpha",
            "fragment_locator": f"lines:{index}-{index}",
            "text": claim_text,
            "content_fingerprint": "a" * 64,
        })
        typed_sections[section_id] = {
            "body": claim_text,
            "claim_ids": [claim_id],
        }
        body_parts.append(f"{claim_text} [^{claim_id}]")
    body_gate_payload = {
        "body": "\n\n".join(body_parts)
        + "\n\n"
        + "\n".join(
            f"[^{{claim_id}}]: raw://alpha#{{fragment_locator}}".format(**claim)
            for claim in section_claims
        ),
        "evidence_body": "",
        "claims": section_claims,
        "duplicate_context": {
            "same_page": [],
            "cross_page": [],
            "denominator": 0,
            "detector_version": "jaccard-5gram.v1",
            "seed": 0,
        },
    }
    payload = {"page_type": case["page_type"], "sections": typed_sections}

    first = compiler(
        page_draft=page,
        provider_payload=payload,
        body_gate_payload=body_gate_payload,
    )
    second = compiler(
        page_draft=page,
        provider_payload=payload,
        body_gate_payload=body_gate_payload,
    )

    assert first["status"] == "published"
    assert first["candidate"]["reader_eligible"] is True
    assert first["navigation_records"]
    assert first["stable_topic_id"] == case["topic_index"]["topic_id"]
    assert [row["target_path"] for row in first["navigation_records"]] == [
        row["target_path"] for row in second["navigation_records"]
    ]
    assert first["audit_record"] is None

    validated = llm.validate_section_response(page, payload)
    assert validated["status"] == "draft"
    internal_result = compiler(
        page_draft=page,
        provider_payload=validated,
        body_gate_payload=body_gate_payload,
    )
    assert internal_result["status"] == "published"
    assert internal_result["candidate"]["reader_eligible"] is True


def test_pipeline_compat_draft_emits_typed_page_contract_for_formal_pipeline(tmp_path: Path) -> None:
    case = _cases()["page_types"][0]
    decision = {
        "cluster_id": "cluster-typed",
        "action": "new",
        "target_paths": [],
        "topic_id": case["topic_index"]["topic_id"],
        "topic_index": case["topic_index"],
    }
    cluster = {"cluster_id": "cluster-typed", "members": [case["source"]["raw_id"]]}
    item = _source_item(case)
    def generator(context: dict[str, Any]) -> dict[str, Any]:
        claim_id = str(context["claims"][0]["claim_fingerprint"])
        return {
            "page_type": case["page_type"],
            "sections": {
                section_id: {
                    "body": "Alpha platform uses Alpha Console v2.1.",
                    "claim_ids": [claim_id],
                }
                for section_id in case["expected_sections"]
            },
        }

    result = draft_module.draft(
        [decision],
        [cluster],
        [item],
        tmp_path,
        DigestSettings(llm_enabled=True),
        generator=generator,
    )[0]

    assert result["typed_page_draft"]["page_type"] == case["page_type"]
    assert result["typed_response"]["status"] == "draft"
    assert set(result["typed_response"]["sections"]) == set(case["expected_sections"])


def test_draft_keeps_typed_page_sections_in_one_complete_provider_batch(tmp_path: Path) -> None:
    case = _cases()["page_types"][0]
    seen_batches: list[int] = []

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        seen_batches.append(int(context["batch_index"]))
        body = "Alpha platform uses Alpha Console v2.1."
        return {
            "page_type": case["page_type"],
            "sections": {
                section_id: {
                    "body": body,
                    "claim_ids": [str(context["claims"][0]["claim_fingerprint"])],
                }
                for section_id in case["expected_sections"]
            },
        }

    result = draft_module.draft(
        [{
            "cluster_id": "cluster-multi-batch",
            "action": "new",
            "topic_id": case["topic_index"]["topic_id"],
            "topic_index": case["topic_index"],
            "target_paths": [],
        }],
        [{"cluster_id": "cluster-multi-batch", "members": [case["source"]["raw_id"]]}],
        [_source_item(case)],
        tmp_path,
        DigestSettings(
            llm_enabled=True,
            llm_batch_max_claims=1,
            llm_batch_max_source_chars=80,
        ),
        generator=generator,
    )[0]

    assert seen_batches == [1]
    assert result["provider_failures"] == []
    assert result["typed_response"]["status"] == "draft"
    assert set(result["typed_response"]["sections"]) == set(case["expected_sections"])
    assert "Alpha platform uses Alpha Console v2.1." in result["typed_response"]["sections"]["positioning"]["body"]


def test_mapped_live_page_uses_typed_body_mode_and_keeps_publication_metadata(tmp_path: Path) -> None:
    case = _cases()["page_types"][0]
    claim_text = "Alpha platform uses Alpha Console v2.1."
    seen: list[bool] = []

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        seen.append(bool(context.get("publication_only")))
        return {
            "page_type": case["page_type"],
            "sections": {
                section_id: {
                    "body": claim_text,
                    "claim_ids": [str(context["claims"][0]["claim_fingerprint"])],
                }
                for section_id in case["expected_sections"]
            },
            "publication": {
                "title": "Alpha platform",
                "category_id": "product-overview",
                "summary": claim_text,
                "why": "Useful for readers.",
                "version": "v2.1",
                "related_topics": [],
                "claim_refs": [],
                "field_refs": {},
            },
        }

    result = draft_module.draft(
        [{
            "cluster_id": "cluster-live",
            "action": "new",
            "topic_id": case["topic_index"]["topic_id"],
            "topic_index": case["topic_index"],
            "target_paths": [],
            "source_count": 1,
            "target_page_count": 0,
        }],
        [{"cluster_id": "cluster-live", "members": ["raw-alpha"]}],
        [{
            "raw_id": "raw-alpha",
            "text": claim_text,
            "source_uri": "raw://alpha",
            "validation_status": "passed",
        }],
        tmp_path,
        DigestSettings(llm_enabled=True),
        generator=generator,
        publication=kb_structure._publication_contract(
            kb_structure.default_publication_structure(),
            require_taxonomy=True,
        )[0],
    )

    assert seen == [False]
    assert result[0]["typed_response"]["status"] == "draft"
    assert result[0]["publication"]["title"] == "Alpha platform"
