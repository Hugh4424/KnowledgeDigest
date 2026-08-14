from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from knowledge_digest.full_release import (
    FullReleaseEvidence,
    SummaryConfirmation,
    atomic_release,
    build_release_summary,
    inspect_formal_root,
    prepare_full_release,
    release_decision,
    summary_sha256,
    validate_summary_confirmation,
)
from knowledge_digest.batch_run import build_affected_replay_plan
import knowledge_digest.full_release as full_release_module
from knowledge_digest.full_release import _quality_scorecard_hash, _source_manifest_hash
from knowledge_digest.errors import ValidationError
from knowledge_digest.reader_bundle import _TRUST_DETECTOR_VERSION, _sha256_tree as bundle_tree_hash, _trust_audit_ref, derive_reader_signals
from knowledge_digest.reader_frontmatter import managed_content_hash, serialize_concept_document
from knowledge_digest.reader_quality import (
    ReaderQuestion,
    ReaderSnapshot,
    _apply_task3_question_oracle,
    _task3_question_oracle,
    _validate_reader_navigation,
    assess_task3_quality,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "task3_full_release" / "release-cases.json"
_FIXTURE_PAGE = """---
description: A complete fixture page.
sources:
- digest_claims:
  - claim_id: claim-overview
    source_uri: raw://fixture/product-overview.md
---
# Fixture overview

## 功能概述
This page explains the purpose and supported use.

## 前置条件
The service must be enabled before operation.

## 异常与边界
Unsupported states and limits are documented here.

## 版本记录
当前版本 V2025.4 is effective.

## 历史版本
历史版本 V2025.3 used the previous route.

## 异常与排查
Check logs and permissions when the operation fails.

## 操作流程
Follow the documented steps.

## Related

[^source]
"""


def _case() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _questions() -> list[dict[str, object]]:
    questions: list[dict[str, object]] = []
    question_set = json.loads((Path(__file__).parents[2] / "config" / "task0-question-set.v1.json").read_text(encoding="utf-8"))
    for frozen in question_set["questions"]:
        positive = frozen["polarity"] == "positive"
        questions.append(
            {
                "question_id": frozen["question_id"],
                "polarity": frozen["polarity"],
                "question": frozen["original_text"],
                "expected_topic_or_product": frozen["expected_topic_or_product"],
                "entry_path": frozen["entry_path"],
                "target_page": "products/fixture-product/product-overview.md",
                "first_hit_page": "products/fixture-product/product-overview.md" if positive else None,
                "jumps": ["Home.md", "products/fixture-product/product-overview.md"],
                "answer_found": positive,
                "source_attribution": positive,
                "navigation": "passed",
                "answer_result": "hit" if positive else "no_match",
                "answer_complete": True,
                "boundary_version_accurate": True,
                "source_chain": "passed" if positive else "not_applicable",
                "source_recheck_result": "passed" if positive else "not_applicable",
                "actor": "process:task3-reader-v1",
                "model": "fixture-reader",
                "rule": "reader-question-v1",
                "seed": "task3-fixture-seed",
                "reader_input_hash": "1" * 64,
                "failure_reason": None,
                "question_oracle": _task3_question_oracle(frozen["question_id"], _FIXTURE_PAGE),
                "provider_response": {
                    "answer_found": positive,
                    "first_hit_page": "products/fixture-product/product-overview.md" if positive else None,
                    "jumps": ["Home.md", "products/fixture-product/product-overview.md"],
                    "answer_complete": True,
                    "boundary_version_accurate": True,
                    "source_attribution": positive,
                    "answer_result": "hit" if positive else "no_match",
                    "source_recheck_result": "passed" if positive else "not_applicable",
                },
            }
        )
    return questions


def _assess(**overrides: object):
    case = _case()
    values: dict[str, object] = {
        "snapshot": case["snapshot"],
        "questions": _questions(),
        "pages": case["pages"],
        "reader_pages": {"products/fixture-product/product-overview.md": _FIXTURE_PAGE},
        "title_scores": case["title_scores"],
        "ownership_scores": case["ownership_scores"],
        "replay": case["replay"],
        "mode": "semantic",
    }
    values.update(overrides)
    return assess_task3_quality(**values)


def test_positive_no_match_keeps_navigation_result_separate_from_answer_result() -> None:
    target = "products/fixture-product/product-overview.md"
    snapshot = ReaderSnapshot(
        paths=("Home.md", target),
        files={"Home.md": f"[Product]({target})\n", target: "# Product\n"},
        content_hash="0" * 64,
    )
    question = ReaderQuestion(
        question_id="positive-01",
        polarity="positive",
        text="这个主题或产品解决什么问题？",
        entry_path="Home.md",
        expected_topic_or_product="当前主题或产品总览",
        target_page=target,
        page_type="product_overview",
        product="fixture-product",
        module=None,
    )
    assert _validate_reader_navigation(snapshot, question, None, ["Home.md", target], ("Home.md", target)) == (True, "passed")


@pytest.mark.parametrize(
    ("question_id", "page_text"),
    [
        (
            "positive-10",
            "# SDK\n\n## 前置条件\n需要开通服务。\n\n## 异常与边界处理\n不满足条件时不上传。\n",
        ),
        (
            "positive-13",
            "# Privacy\n\n## 当前版本\nV2025.4 已移除入口。\n\n## 历史版本\nV2025.3 仍使用旧入口。\n",
        ),
        (
            "positive-15",
            "---\nsources:\n- digest_claims: [claim]\n---\n# Remote control\n\n## 异常与超时处理\n检查权限和超时日志。\n\n## 日志记录\n查看连接日志。\n\n## Related\n\n[^source]\n",
        ),
        (
            "positive-17",
            "---\ndescription: A complete page.\nsources:\n- digest_claims: [claim]\n---\n# Complete\n\n## 功能概述\n说明用途。\n\n## 操作流程\n说明怎么做。\n\n## 边界与异常\n说明限制。\n\n## 版本记录\nV1 当前有效。\n\n[^source]\n",
        ),
    ],
)
def test_task3_question_oracle_accepts_explicit_page_contracts(question_id: str, page_text: str) -> None:
    normalized, oracle = _apply_task3_question_oracle(
        question_id,
        "products/example/topic.md",
        page_text,
        {
            "answer_found": False,
            "first_hit_page": None,
            "jumps": ["Home.md", "products/example/topic.md"],
            "answer_complete": True,
            "boundary_version_accurate": True,
            "source_attribution": False,
            "answer_result": "no_match",
            "source_recheck_result": "not_applicable",
        },
    )

    assert oracle["status"] == "passed"
    assert normalized["answer_found"] is True
    assert normalized["first_hit_page"] == "products/example/topic.md"
    assert normalized["answer_result"] == "hit"
    assert normalized["source_recheck_result"] == "passed"


def test_task3_question_oracle_rejects_sparse_independent_reading_claim() -> None:
    normalized, oracle = _apply_task3_question_oracle(
        "positive-17",
        "products/example/topic.md",
        "# Thin page\n\nOnly a title and one sentence.\n",
        {
            "answer_found": True,
            "first_hit_page": "products/example/topic.md",
            "jumps": ["Home.md", "products/example/topic.md"],
            "answer_complete": True,
            "boundary_version_accurate": True,
            "source_attribution": True,
            "answer_result": "hit",
            "source_recheck_result": "passed",
        },
    )

    assert oracle["status"] == "failed"
    assert normalized["answer_found"] is False
    assert normalized["first_hit_page"] is None
    assert normalized["answer_result"] == "no_match"


def test_task3_question_oracle_rejects_invalid_provider_contract() -> None:
    normalized, oracle = _apply_task3_question_oracle(
        "positive-10",
        "products/example/topic.md",
        _FIXTURE_PAGE,
        {},
    )

    assert oracle["status"] == "passed"
    assert oracle["provider_contract"] == "invalid"
    assert normalized["answer_result"] == "no_match"
    assert normalized["answer_complete"] is False
    assert normalized["failure_reason"] == "provider_response_contract_invalid"


def test_task3_question_oracle_requires_substantive_sections() -> None:
    page = "# Thin\n\n## 前置条件\n\n## 异常与边界\n\n"
    _normalized, oracle = _apply_task3_question_oracle(
        "positive-10",
        "products/example/topic.md",
        page,
        {
            "answer_found": True,
            "first_hit_page": "products/example/topic.md",
            "jumps": ["Home.md", "products/example/topic.md"],
            "answer_complete": True,
            "boundary_version_accurate": True,
            "source_attribution": True,
            "answer_result": "hit",
            "source_recheck_result": "passed",
        },
    )

    assert oracle["status"] == "failed"
    assert oracle["missing"] == ["scope_section", "boundary_section"]


def test_task3_quality_passes_exact_17_plus_3_and_two_90_percent_gates() -> None:
    result = _assess()
    assert result.status == "passed"
    assert result.summary["positive_count"] == 17
    assert result.summary["positive_passed"] == 17
    assert result.summary["negative_count"] == 3
    assert result.summary["negative_false_positives"] == 0
    assert result.title_check == {"passed": 9, "sample_size": 10, "rate": 0.9, "actor": "process:task3-title-v1", "rule": "title-detached-path-v1", "seed": "task3-fixture-seed"}
    assert result.ownership_check == {"passed": 9, "sample_size": 10, "rate": 0.9, "actor": "process:task3-ownership-v1", "rule": "product-module-ownership-v1", "seed": "task3-fixture-seed"}
    assert result.provenance["actor"] == "process:task3-quality-v1"
    assert result.provenance["seed"] == "task3-fixture-seed"
    assert result.scorecard_hash and len(result.scorecard_hash) == 64
    assert all("human_reviewed" not in record for record in result.records)
    assert result.summary["replay"]["quality_ref"] == "reports/quality.json"


@pytest.mark.parametrize(
    ("mutation", "error_code"),
    [
        (lambda questions: questions.pop(), "QUESTION_COUNT_INVALID"),
        (lambda questions: [item.update(answer_result="no_match") for item in questions[:3]], "POSITIVE_HIT_THRESHOLD"),
        (lambda questions: questions[-1].update(first_hit_page="products/fixture-product/product-overview.md", answer_result="hit"), "NEGATIVE_FALSE_POSITIVE"),
    ],
)
def test_task3_quality_question_policy_fails_closed(mutation, error_code: str) -> None:
    questions = _questions()
    mutation(questions)
    result = _assess(questions=questions)
    assert result.status == "failed"
    assert error_code in result.hard_failures


def test_task3_quality_rejects_first_hit_page_outside_published_reader() -> None:
    questions = _questions()
    questions[0].update(
        target_page="products/fixture-product/missing.md",
        first_hit_page="products/fixture-product/missing.md",
    )
    result = _assess(questions=questions)

    assert result.status == "failed"
    assert "QUESTION_TARGET_PAGE_NOT_IN_READER" in result.hard_failures
    assert "QUESTION_FIRST_HIT_PAGE_INVALID" in result.hard_failures


def test_task3_question_oracle_rejects_empty_jumps() -> None:
    normalized, oracle = _apply_task3_question_oracle(
        "positive-10",
        "products/example/topic.md",
        _FIXTURE_PAGE,
        {
            "answer_found": False,
            "first_hit_page": None,
            "jumps": [],
            "answer_complete": True,
            "boundary_version_accurate": True,
            "source_attribution": False,
            "answer_result": "no_match",
            "source_recheck_result": "not_applicable",
        },
    )

    assert oracle["provider_contract"] == "invalid"
    assert normalized["failure_reason"] == "provider_response_contract_invalid"


def test_task3_quality_rejects_raw_provider_verdict_mismatch() -> None:
    questions = _questions()
    questions[0]["provider_response"]["answer_found"] = False
    questions[0]["provider_response"]["first_hit_page"] = None
    questions[0]["provider_response"]["answer_result"] = "no_match"
    result = _assess(questions=questions)

    assert result.status == "failed"
    assert "QUALITY_PROVIDER_VERDICT_MISMATCH" in result.hard_failures


def test_task3_quality_requires_provider_replay_fields() -> None:
    questions = _questions()
    questions[0].pop("provider_response")
    result = _assess(questions=questions)

    assert result.status == "failed"
    assert "QUALITY_PROVIDER_RESPONSE_FIELDS_MISSING" in result.hard_failures


def test_task3_quality_rejects_unknown_answer_result() -> None:
    questions = _questions()
    questions[-1]["answer_result"] = "unknown"
    result = _assess(questions=questions)
    assert result.status == "failed"
    assert "QUESTION_ANSWER_RESULT_INVALID" in result.hard_failures


@pytest.mark.parametrize(
    ("field", "error_code"),
    [("title_scores", "TITLE_ACCURACY_BELOW_THRESHOLD"), ("ownership_scores", "OWNERSHIP_ACCURACY_BELOW_THRESHOLD")],
)
def test_task3_quality_accuracy_gates_require_machine_score_metadata(field: str, error_code: str) -> None:
    scores = {"passed": 8, "sample_size": 10, "actor": "process:test", "rule": "test-rule", "seed": "task3-fixture-seed"}
    result = _assess(**{field: scores})
    assert result.status == "failed"
    assert error_code in result.hard_failures


@pytest.mark.parametrize(
    ("mutation", "error_code"),
    [
        (lambda case: case["pages"][0].update(body_lines=121), "BODY_LINES_EXCEEDED"),
        (lambda case: case["pages"][0].update(page_lines=301), "PAGE_LINES_EXCEEDED"),
        (lambda case: case["pages"][1]["claims"].append(dict(case["pages"][0]["claims"][0])), "CLAIM_ID_DUPLICATED"),
        (lambda case: case["pages"][1].update(status="degraded", in_reader=True), "FAILED_PAGE_IN_READER"),
        (lambda case: case["replay"].pop("quality_ref"), "REPLAY_MATERIAL_MISSING"),
    ],
)
def test_task3_quality_delivery_hard_gates_fail_closed(mutation, error_code: str) -> None:
    case = _case()
    mutation(case)
    result = _assess(pages=case["pages"], replay=case["replay"])
    assert result.status == "failed"
    assert error_code in result.hard_failures


def test_task3_quality_rejects_missing_required_question_field_and_human_reviewed() -> None:
    questions = _questions()
    questions[0].pop("reader_input_hash")
    questions[1]["human_reviewed"] = True
    result = _assess(questions=questions)
    assert result.status == "failed"
    assert "QUESTION_RESULT_FIELDS_MISSING" in result.hard_failures
    assert "HUMAN_REVIEWED_FORBIDDEN" in result.hard_failures


def test_task3_quality_rejects_empty_replay_fields_and_published_pages_without_claims() -> None:
    questions = _questions()
    questions[0]["actor"] = ""
    questions[1]["answer_complete"] = None
    case = _case()
    case["pages"][0]["claims"] = []
    result = _assess(questions=questions, pages=case["pages"])
    assert result.status == "failed"
    assert "QUESTION_RESULT_FIELDS_INVALID" in result.hard_failures
    assert "CLAIM_FIELDS_MISSING" in result.hard_failures


def _summary(**overrides: object) -> dict[str, object]:
    quality = _assess()
    delivery = {
        "status": "passed",
        "hard_failures": [],
        "warnings": [],
        "unknowns": [],
        "reader_hash": "2" * 64,
        "audit_hash": "3" * 64,
        "replay_material": True,
    }
    value = build_release_summary(
        run_id="run-task3-fixture",
        quality=quality,
        delivery=delivery,
        mode="semantic",
        old_package_protected=True,
    )
    value.update(overrides)
    value["summary_sha256"] = summary_sha256(value)
    return value


def test_summary_contains_every_machine_decision_field_without_manual_content_trust() -> None:
    summary = _summary()
    assert summary["run_id"] == "run-task3-fixture"
    assert summary["completion"] == "complete"
    assert summary["hard_failures"] == []
    assert summary["warnings"] == []
    assert summary["unknowns"] == []
    assert summary["reader_quality"]["positive_passed"] == 17
    assert summary["reader_quality"]["negative_false_positives"] == 0
    assert summary["accuracy"]["title"]["rate"] == 0.9
    assert summary["mode"] == "semantic"
    assert summary["old_package_protected"] is True
    assert "human_reviewed" not in json.dumps(summary)
    assert "verified" not in summary


def test_summary_confirmation_is_bound_to_run_and_hash_and_warnings_are_allowed() -> None:
    summary = _summary(warnings=["KNOWN_WARNING"])
    summary_hash = summary["summary_sha256"]
    confirmation = SummaryConfirmation("run-task3-fixture", summary_hash, "human:test", "2026-08-13T00:00:00Z")
    assert validate_summary_confirmation(confirmation, summary=summary) is True
    assert release_decision(summary, confirmation) == "released"
    assert release_decision(summary, SummaryConfirmation("other-run", summary_hash, "human:test", "2026-08-13T00:00:00Z")) == "not_released"
    assert release_decision(summary, SummaryConfirmation("run-task3-fixture", "0" * 64, "human:test", "2026-08-13T00:00:00Z")) == "not_released"
    assert release_decision(summary, SummaryConfirmation("run-task3-fixture", summary_hash, "agent:auto", "2026-08-13T00:00:00Z")) == "not_released"


def test_summary_confirmation_rejects_missing_timezone_old_and_future_timestamps() -> None:
    summary = _summary()
    summary_hash = summary["summary_sha256"]
    now = datetime.now(timezone.utc)
    for timestamp in (
        now.replace(tzinfo=None).isoformat(),
        (now - timedelta(days=2)).isoformat().replace("+00:00", "Z"),
        (now + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
    ):
        confirmation = SummaryConfirmation("run-task3-fixture", summary_hash, "human:test", timestamp)
        assert release_decision(summary, confirmation) == "not_released"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda summary: summary.update(hard_failures=["PAGE_LINES_EXCEEDED"]),
        lambda summary: summary.update(unknowns=["QUALITY_UNDECIDABLE"]),
        lambda summary: summary.update(completion="incomplete"),
        lambda summary: summary.update(old_package_protected=False),
        lambda summary: summary.update(mode="no-llm"),
    ],
)
def test_hard_failure_unknown_incomplete_offline_or_unprotected_old_package_cannot_release(mutation) -> None:
    summary = _summary()
    mutation(summary)
    confirmation = SummaryConfirmation("run-task3-fixture", summary["summary_sha256"], "human:test", "2026-08-13T00:00:00Z")
    assert release_decision(summary, confirmation) == "not_released"


def test_prepare_rejects_quality_status_or_failures_tampering(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    formal = tmp_path / "current"
    _write_valid_candidate(candidate)
    _write_valid_candidate(formal)
    questions = _questions()
    for question in questions[:3]:
        question["answer_result"] = "no_match"
    failed = _assess(questions=questions)
    tampered = replace(failed, status="passed", hard_failures=(), scorecard_hash=failed.scorecard_hash)
    prepared = prepare_full_release(
        FullReleaseEvidence(
            "run-task3-fixture",
            _case()["snapshot"],
            tampered,
            {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True},
            "semantic",
            candidate,
            formal,
            True,
            {"release_decision": "not_a_release_decision"},
        )
    )
    assert "QUALITY_SCORECARD_HASH_MISMATCH" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rejects_self_consistent_incomplete_17_plus_3_records(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    formal = tmp_path / "current"
    _write_valid_candidate(candidate)
    _write_valid_candidate(formal)
    quality = _assess()
    records = tuple(quality.records[:1])
    provenance = dict(quality.provenance)
    provenance["question_hash"] = hashlib.sha256(json.dumps(list(records), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    summary = dict(quality.summary)
    summary.update({"positive_count": 1, "positive_passed": 1, "negative_count": 0, "negative_false_positives": 0})
    quality = replace(quality, records=records, summary=summary, provenance=provenance, scorecard_hash="0" * 64)
    quality = replace(quality, scorecard_hash=_quality_scorecard_hash(quality))
    prepared = prepare_full_release(
        FullReleaseEvidence(
            "run-task3-fixture",
            _case()["snapshot"],
            quality,
            {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True},
            "semantic",
            candidate,
            formal,
            True,
            {"release_decision": "not_a_release_decision"},
        )
    )
    assert "QUALITY_QUESTION_COUNT_INVALID" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rejects_candidate_symlink(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    formal = tmp_path / "current"
    _write_valid_candidate(candidate)
    _write_valid_candidate(formal)
    outside = tmp_path / "outside-projection.json"
    outside.write_text((candidate / "reports" / "projection-report.json").read_text(encoding="utf-8"), encoding="utf-8")
    (candidate / "reports" / "projection-report.json").unlink()
    (candidate / "reports" / "projection-report.json").symlink_to(outside)
    prepared = prepare_full_release(
        FullReleaseEvidence(
            "run-task3-fixture",
            _case()["snapshot"],
            _assess(),
            {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True},
            "semantic",
            candidate,
            formal,
            True,
            {"release_decision": "not_a_release_decision"},
        )
    )
    assert "CANDIDATE_SYMLINK_PRESENT" in prepared.hard_failures or "REPLAY_MATERIAL_SYMLINK" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rechecks_each_question_field_and_score_metadata(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    formal = tmp_path / "current"
    _write_valid_candidate(candidate)
    _write_valid_candidate(formal)
    quality = _assess()
    records = [dict(record) for record in quality.records]
    records[0].pop("actor")
    provenance = dict(quality.provenance)
    provenance["question_hash"] = hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    invalid = replace(quality, records=tuple(records), provenance=provenance, scorecard_hash="0" * 64)
    invalid = replace(invalid, scorecard_hash=_quality_scorecard_hash(invalid))
    prepared = prepare_full_release(FullReleaseEvidence("run-task3-fixture", _case()["snapshot"], invalid, {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True}, "semantic", candidate, formal, True, {"release_decision": "not_a_release_decision"}))
    assert "QUALITY_QUESTION_FIELDS_MISSING" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rechecks_score_metadata_and_replay_file_binding(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    formal = tmp_path / "current"
    _write_valid_candidate(candidate)
    _write_valid_candidate(formal)
    quality = _assess()
    title_check = dict(quality.title_check)
    title_check.pop("actor")
    replay = dict(quality.replay)
    replay["quality_ref"] = "../../outside-quality.json"
    summary = dict(quality.summary)
    summary["replay"] = dict(replay)
    invalid = replace(quality, title_check=title_check, replay=replay, summary=summary, scorecard_hash="0" * 64)
    invalid = replace(invalid, scorecard_hash=_quality_scorecard_hash(invalid))
    prepared = prepare_full_release(FullReleaseEvidence("run-task3-fixture", _case()["snapshot"], invalid, {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True}, "semantic", candidate, formal, True, {"release_decision": "not_a_release_decision"}))
    assert "QUALITY_TITLE_SCORE_INVALID" in prepared.hard_failures
    assert "QUALITY_REPLAY_REFERENCE_INVALID" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rejects_swapped_fixed_question_polarity_and_duplicate_replay_refs(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    formal = tmp_path / "current"
    _write_valid_candidate(candidate)
    _write_valid_candidate(formal)
    quality = _assess()
    records = [dict(record) for record in quality.records]
    records[0]["polarity"], records[-1]["polarity"] = records[-1]["polarity"], records[0]["polarity"]
    provenance = dict(quality.provenance)
    provenance["question_hash"] = hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    replay = dict(quality.replay)
    replay["quality_ref"] = replay["manifest_ref"]
    summary = dict(quality.summary)
    summary["replay"] = dict(replay)
    invalid = replace(quality, records=tuple(records), provenance=provenance, replay=replay, summary=summary, scorecard_hash="0" * 64)
    invalid = replace(invalid, scorecard_hash=_quality_scorecard_hash(invalid))
    prepared = prepare_full_release(FullReleaseEvidence("run-task3-fixture", _case()["snapshot"], invalid, {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True}, "semantic", candidate, formal, True, {"release_decision": "not_a_release_decision"}))
    assert "QUALITY_QUESTION_POLARITY_BINDING_INVALID" in prepared.hard_failures
    assert "QUALITY_REPLAY_REFERENCE_DUPLICATED" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rejects_fixed_question_text_drift(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    formal = tmp_path / "current"
    _write_valid_candidate(candidate)
    _write_valid_candidate(formal)
    quality = _assess()
    records = [dict(record) for record in quality.records]
    records[0]["question"] = "被替换的问题"
    provenance = dict(quality.provenance)
    provenance["question_hash"] = hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    invalid = replace(quality, records=tuple(records), provenance=provenance, scorecard_hash="0" * 64)
    invalid = replace(invalid, scorecard_hash=_quality_scorecard_hash(invalid))
    prepared = prepare_full_release(FullReleaseEvidence("run-task3-fixture", _case()["snapshot"], invalid, {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True}, "semantic", candidate, formal, True, {"release_decision": "not_a_release_decision"}))
    assert "QUALITY_FIXED_QUESTION_BINDING_INVALID" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rejects_semantic_replay_without_provider_call_records(tmp_path: Path) -> None:
    prepared, _confirmation, candidate, formal = _prepared_release(tmp_path)
    receipt_path = candidate / "audit" / "provider-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["calls"] = []
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    invalid = prepare_full_release(FullReleaseEvidence("run-task3-fixture", _case()["snapshot"], _assess(snapshot=_case()["snapshot"]), {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True}, "semantic", candidate, formal, True, {"release_decision": "not_a_release_decision", "binding": {"run_id": "run-task3-fixture", "bundle_hash": bundle_tree_hash(candidate / "bundle")}}))
    assert "QUALITY_PROVIDER_RECEIPT_INVALID" in invalid.hard_failures
    assert prepared.status == "not_released"


def _prepared_release(tmp_path: Path, *, old_package_protected: bool = True, formal_exists: bool = True):
    candidate = tmp_path / "candidate"
    _write_valid_candidate(candidate)
    formal = tmp_path / "current"
    if formal_exists:
        _write_valid_candidate(formal)
    manifest = json.loads((candidate / "audit" / "source-manifest.json").read_text(encoding="utf-8"))
    snapshot = dict(_case()["snapshot"])
    snapshot["source_manifest_hash"] = _source_manifest_hash(manifest)
    quality = _assess(snapshot=snapshot)
    reader_hash = bundle_tree_hash(candidate / "bundle")
    records = tuple({**record, "reader_input_hash": reader_hash, "model": "fixture-model"} for record in quality.records)
    provenance = dict(quality.provenance)
    provenance["question_hash"] = hashlib.sha256(json.dumps(list(records), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    quality = replace(quality, records=records, provenance=provenance, scorecard_hash="0" * 64)
    quality = replace(quality, scorecard_hash=_quality_scorecard_hash(quality))
    (candidate / "audit" / "run-manifest.json").write_text(json.dumps({"run_id": "run-task3-fixture", "source_manifest_hash": snapshot["source_manifest_hash"], "execution_mode": "real_semantic"}) + "\n", encoding="utf-8")
    (candidate / "audit" / "config.json").write_text(json.dumps({"run_id": "run-task3-fixture", "snapshot_hash": hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "execution_mode": "real_semantic", "llm_enabled": True, "model": "fixture-model", "provider": "fixture-provider", "config_hash": snapshot["provider_config_hash"], "endpoint": "https://fixture.invalid/v1", "budget": {"max_calls": 20}}) + "\n", encoding="utf-8")
    quality_payload = quality.as_dict()
    quality_payload.update({"run_id": "run-task3-fixture", "mode": "semantic", "execution_mode": "real_semantic", "provider_calls": 20, "provider": "fixture-provider", "model": "fixture-model", "provider_receipt_ref": "audit/provider-receipt.json"})
    (candidate / "reports" / "quality.json").write_text(json.dumps(quality_payload, ensure_ascii=False) + "\n", encoding="utf-8")
    def canonical_hash(value: object) -> str:
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    calls = []
    for record in records:
        request = {"question_id": record["question_id"], "question": record["question"], "entry_path": record["entry_path"], "expected_topic_or_product": record["expected_topic_or_product"], "provider": "fixture-provider", "model": "fixture-model", "config_hash": snapshot["provider_config_hash"]}
        response = record["provider_response"]
        calls.append({"question_id": record["question_id"], "record_hash": canonical_hash(record), "provider": "fixture-provider", "model": "fixture-model", "status": "completed", "request_hash": canonical_hash(request), "response": response, "response_hash": canonical_hash(response)})
    (candidate / "audit" / "provider-receipt.json").write_text(json.dumps({"run_id": "run-task3-fixture", "execution_mode": "real_semantic", "provider_calls": 20, "provider": "fixture-provider", "model": "fixture-model", "config_hash": snapshot["provider_config_hash"], "calls": calls}) + "\n", encoding="utf-8")
    delivery = {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True}
    comparison = {
        "schema_version": "kd-task3-comparison.v1",
        "sources": {"task2": {"saved_integrity": {"status": "N/A", "basis": "fixture"}}, "companybrain": {"saved_integrity": {"status": "N/A", "basis": "fixture"}}, "task3": {"binding": {"run_id": "run-task3-fixture", "bundle_hash": bundle_tree_hash(candidate / "bundle")}, "claim_count": 3, **{dimension: {"status": "comparable", "basis": "fixture"} for dimension in ("saved_integrity", "machine_quality", "reader_readability", "trust_freshness", "failures")}}},
        "dimensions": {
            dimension: {
                name: {"comparability": "N/A", "basis": "fixture"}
                for name in ("task2", "companybrain", "task3")
            }
            for dimension in ("saved_integrity", "machine_quality", "reader_readability", "trust_freshness", "failures", "performance", "cost", "limitations")
        },
        "release_decision": "not_a_release_decision",
        "binding": {"run_id": "run-task3-fixture", "bundle_hash": bundle_tree_hash(candidate / "bundle")},
    }
    prepared = prepare_full_release(FullReleaseEvidence("run-task3-fixture", snapshot, quality, delivery, "semantic", candidate, formal, old_package_protected, comparison, manifest))
    confirmation = SummaryConfirmation(prepared.summary["run_id"], prepared.summary_sha256, "human:test", "2026-08-13T00:00:00Z", summary_file_sha256=prepared.summary_file_sha256)
    return prepared, confirmation, candidate, formal


def _write_valid_candidate(root: Path) -> None:
    bundle = root / "bundle"
    audit = root / "audit"
    reports = root / "reports"
    pages = [
        "products/fixture-product/product-overview.md",
        "products/fixture-product/modules/fixture-module/module-capability.md",
        "products/other-product/modules/other-module/module-capability.md",
    ]
    for relative in pages:
        page = bundle / relative
        page.parent.mkdir(parents=True, exist_ok=True)
        topic = relative.rsplit("/", 1)[-1].removesuffix(".md")
        ident = relative.removesuffix(".md").replace("/", "-")
        source_uri = f"raw://fixture/{topic}.md"
        fingerprint = hashlib.sha256(topic.encode()).hexdigest()
        frontmatter = {
            "type": "KnowledgeDigest Module or Capability",
            "title": topic.replace("-", " ").title(),
            "description": "A fixture page with a complete source and claim chain.",
            "sources": [{"id": f"source-{ident}", "resource": source_uri, "digest_content_fingerprint": fingerprint, "digest_claims": [{"claim_id": f"claim-{ident}", "target_path": relative, "source_uri": source_uri, "fragment_locator": "lines:1-1", "content_fingerprint": fingerprint}]}],
            "status": "draft",
            "digest_topic_id": f"topic-{ident}",
            "digest_page_type": "module_or_capability",
            "digest_page_status": "published",
            "digest_machine_pass": True,
            "generated": {"by": "test", "at": "2026-08-13T00:00:00Z"},
            "verified": [],
        }
        body = f"# {frontmatter['title']}\n\nA complete fixture body for {topic}.\n"
        events = [
            {
                "event": event,
                "actor": f"process:knowledge-digest-{event}-{_TRUST_DETECTOR_VERSION}",
                "detector_version": _TRUST_DETECTOR_VERSION,
                "input_fingerprints": {"source_inventory": fingerprint, "fixture_selection": fingerprint, "claim_records": {f"claim-{ident}": fingerprint}, "fixture_bytes": fingerprint},
                "content_hash": "",
                "evidence_ref": _trust_audit_ref(relative),
            }
            for event in ("source_hash_match", "locator_resolved")
        ]
        frontmatter["verified"] = events
        frontmatter["reader_signals"] = derive_reader_signals(frontmatter, as_of="2026-08-13")
        frontmatter["digest_content_hash"] = managed_content_hash(frontmatter, body)
        for event in events:
            event["content_hash"] = frontmatter["digest_content_hash"]
        page.write_text(serialize_concept_document(frontmatter, body), encoding="utf-8")
        trust_path = audit / Path(_trust_audit_ref(relative)).relative_to("audit")
        trust_path.parent.mkdir(parents=True, exist_ok=True)
        trust_path.write_text(json.dumps({"schema_version": "reader-bundle-trust-signals.v1", "page_path": relative, "topic_id": frontmatter["digest_topic_id"], "generated": frontmatter["generated"], "machine_pass": True, "content_hash": frontmatter["digest_content_hash"], "events": events}) + "\n", encoding="utf-8")
    (bundle / "references").mkdir(parents=True, exist_ok=True)
    (bundle / "Home.md").write_text("# Home\n\n[Reader index](index.md)\n", encoding="utf-8")
    (bundle / "README.md").write_text("# Reader Bundle\n\nThis semantic snapshot candidate is not released.\n\n- digest_release_status: `not_released`\n", encoding="utf-8")
    (bundle / "log.md").write_text("# Projection log\n\n- digest_release_status: `not_released`\n", encoding="utf-8")
    (bundle / "references" / "sources.md").write_text("# Sources\n", encoding="utf-8")
    (bundle / "index.md").write_text("# Reader index\n\n[Products](products/index.md)\n", encoding="utf-8")
    (bundle / "products").mkdir(exist_ok=True)
    (bundle / "products" / "index.md").write_text("# Products\n\n[Fixture](fixture-product/index.md)\n\n[Other](other-product/index.md)\n", encoding="utf-8")
    (bundle / "products" / "fixture-product" / "index.md").write_text("# Fixture\n\n[Overview](product-overview.md)\n\n[Module](modules/fixture-module/module-capability.md)\n", encoding="utf-8")
    (bundle / "products" / "other-product").mkdir(parents=True, exist_ok=True)
    (bundle / "products" / "other-product" / "index.md").write_text("# Other\n\n[Module](modules/other-module/module-capability.md)\n", encoding="utf-8")
    audit.mkdir(parents=True, exist_ok=True)
    page_entries = []
    for relative in pages:
        topic = relative.rsplit("/", 1)[-1].removesuffix(".md")
        ident = relative.removesuffix(".md").replace("/", "-")
        page_entries.append({"source_id": f"source-{ident}", "source_uri": f"raw://fixture/{topic}.md", "content_fingerprint": hashlib.sha256(topic.encode()).hexdigest()})
    entries = page_entries + [{"source_id": f"source-filler-{i}", "source_uri": f"raw://fixture/filler-{i}.md", "content_fingerprint": f"{i + 100:064x}"} for i in range(86)]
    (audit / "source-manifest.json").write_text(json.dumps({"schema_version": "reader-bundle-source-manifest.v1", "run_id": "run-task3-fixture", "source_count": 89, "entries": entries}) + "\n", encoding="utf-8")
    reports.mkdir(parents=True, exist_ok=True)
    bundle_hash = bundle_tree_hash(bundle)
    (reports / "projection-report.json").write_text(json.dumps({"digest_release_status": "not_released", "run_id": "run-task3-fixture", "entry_binding": {"status": "passed"}, "degraded_records": []}) + "\n", encoding="utf-8")
    (reports / "exit-manifest.json").write_text(json.dumps({"digest_release_status": "not_released", "run_id": "run-task3-fixture", "bundle_hash": bundle_hash}) + "\n", encoding="utf-8")
    (audit / "run-manifest.json").write_text("{}\n", encoding="utf-8")
    (audit / "config.json").write_text("{}\n", encoding="utf-8")
    (reports / "quality.json").write_text("{}\n", encoding="utf-8")


def test_recovery_keeps_old_formal_root_when_candidate_is_stale(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    old_hash = bundle_tree_hash(formal)
    (candidate / "bundle.txt").write_text("mutated after prepare\n", encoding="utf-8")
    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal) == "not_released"
    assert bundle_tree_hash(formal) == old_hash


def test_release_rechecks_nested_candidate_symlink_inside_lock(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    outside = tmp_path / "outside-readme.md"
    outside.write_text((candidate / "bundle" / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
    (candidate / "bundle" / "README.md").unlink()
    (candidate / "bundle" / "README.md").symlink_to(outside)
    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal) == "not_released"


def test_recovery_keeps_old_formal_root_when_atomic_replace_fails(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    old_hash = bundle_tree_hash(formal)
    calls = 0

    def fail_second_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected replace failure")
        import os
        os.replace(source, destination)

    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal, replace_fn=fail_second_replace) == "not_released"
    assert bundle_tree_hash(formal) == old_hash


def test_recovery_keeps_old_formal_root_when_formal_readback_detects_corruption(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    old_hash = bundle_tree_hash(formal)
    calls = 0

    def corrupt_staged_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            Path(source, "bundle.txt").write_text("corrupted during swap\n", encoding="utf-8")
        import os
        os.replace(source, destination)

    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal, replace_fn=corrupt_staged_replace) == "not_released"
    assert bundle_tree_hash(formal) == old_hash


def test_successful_release_swaps_one_root_and_writes_machine_receipt(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal) == "released"
    assert (formal / "bundle" / "products" / "fixture-product" / "product-overview.md").is_file()
    receipt = json.loads((formal / "reports" / "release-receipt.json").read_text(encoding="utf-8"))
    assert receipt["digest_release_status"] == "released"
    assert receipt["confirmed_summary_sha256"] == prepared.summary_sha256
    assert receipt["summary_sha256"] == json.loads((formal / "reports" / "release-summary.json").read_text(encoding="utf-8"))["summary_sha256"]
    assert json.loads((formal / "reports" / "projection-report.json").read_text(encoding="utf-8"))["digest_release_status"] == "released"
    assert json.loads((formal / "reports" / "exit-manifest.json").read_text(encoding="utf-8"))["digest_release_status"] == "released"
    assert "human_reviewed" not in receipt


def test_recovery_stops_on_lock_competition_without_touching_old_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    old_hash = bundle_tree_hash(formal)

    @contextmanager
    def busy_lock(_root):
        raise ValidationError("kb_lock", "test", "another digest run is processing this knowledge base; retry later")
        yield

    monkeypatch.setattr(full_release_module, "kb_lock", busy_lock)
    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal) == "not_released"
    assert bundle_tree_hash(formal) == old_hash


def test_recovery_preserves_rollback_when_old_root_restore_also_fails(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    calls = 0

    def fail_install_and_restore(source, destination):
        nonlocal calls
        calls += 1
        if calls in {2, 3}:
            raise OSError("injected install and restore failure")
        import os
        os.replace(source, destination)

    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal, replace_fn=fail_install_and_restore) == "not_released"
    assert not formal.exists()
    assert list(formal.parent.glob(".task3-rollback-*")), "the old package backup must remain recoverable"


def test_prepare_re_reads_candidate_and_cannot_be_bypassed_by_passed_mapping(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "bundle.txt").write_text("not a Reader Bundle\n", encoding="utf-8")
    formal = tmp_path / "current"
    _write_valid_candidate(formal)
    prepared = prepare_full_release(
        FullReleaseEvidence(
            "run-task3-fixture",
            _case()["snapshot"],
            _assess(),
            {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True},
            "semantic",
            candidate,
            formal,
            True,
            {"release_decision": "not_a_release_decision"},
        )
    )
    assert "READER_BUNDLE_MISSING" in prepared.hard_failures
    assert prepared.status == "not_released"


def test_prepare_rejects_questions_from_a_different_reader_hash(tmp_path: Path) -> None:
    prepared, _confirmation, candidate, formal = _prepared_release(tmp_path)
    quality = _assess()
    quality = replace(quality, records=tuple({**record, "reader_input_hash": "0" * 64} for record in quality.records))
    invalid = prepare_full_release(
        FullReleaseEvidence(
            "run-task3-fixture",
            _case()["snapshot"],
            quality,
            {"status": "passed", "hard_failures": [], "warnings": [], "unknowns": [], "replay_material": True},
            "semantic",
            candidate,
            formal,
            True,
            {"release_decision": "not_a_release_decision"},
        )
    )
    assert "QUALITY_READER_HASH_MISMATCH" in invalid.hard_failures
    assert prepared.status == "not_released"


def test_summary_file_tampering_invalidates_confirmation(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path)
    old_hash = bundle_tree_hash(formal)
    assert prepared.summary_path is not None
    prepared.summary_path.write_text("tampered\n", encoding="utf-8")
    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal) == "not_released"
    assert bundle_tree_hash(formal) == old_hash


def test_formal_root_preflight_rejects_missing_or_incomplete_old_package(tmp_path: Path) -> None:
    assert inspect_formal_root(None)["status"] == "missing"
    missing = inspect_formal_root(tmp_path / "new-formal")
    assert missing["status"] == "absent"
    assert missing["protected"] is True
    incomplete = tmp_path / "incomplete-formal"
    incomplete.mkdir()
    assert inspect_formal_root(incomplete)["status"] == "invalid"


def test_prepare_derives_old_package_protection_from_root_not_caller_flag(tmp_path: Path) -> None:
    prepared, _confirmation, _candidate, _formal = _prepared_release(tmp_path, old_package_protected=False)
    assert "OLD_PACKAGE_NOT_PROTECTED" not in prepared.hard_failures
    assert prepared.summary["old_package_protected"] is True


def test_first_release_can_target_an_explicit_empty_formal_root(tmp_path: Path) -> None:
    prepared, confirmation, candidate, formal = _prepared_release(tmp_path, formal_exists=False)
    assert "FORMAL_ROOT_REQUIRED" not in prepared.hard_failures
    assert prepared.summary["delivery"]["formal_root_state"] == "absent"
    assert atomic_release(prepared, confirmation, candidate_root=candidate, formal_root=formal) == "released"
    assert (formal / "reports" / "release-receipt.json").is_file()
    assert json.loads((formal / "reports" / "exit-manifest.json").read_text(encoding="utf-8"))["digest_release_status"] == "released"


def test_affected_replay_only_returns_unfinished_affected_items_and_stops_on_contract_change() -> None:
    state = {
        "manifest_sha256": "a" * 64,
        "sources": [
            {"source_id": "source-done", "content_path": "done.md"},
            {"source_id": "source-failed", "content_path": "failed.md"},
            {"source_id": "source-unaffected", "content_path": "unaffected.md"},
        ],
        "batches": [
            {"batch_id": "batch-1", "source_paths": ["done.md"], "status": "succeeded"},
            {"batch_id": "batch-2", "source_paths": ["failed.md"], "status": "failed"},
            {"batch_id": "batch-3", "source_paths": ["unaffected.md"], "status": "succeeded"},
        ],
    }
    affected = {"affected_source_ids": ["source-done", "source-failed"], "affected_topic_keys": ["topic-done", "topic-failed"]}
    plan = build_affected_replay_plan(
        affected=affected,
        batch_state=state,
        topic_sources={"topic-done": ["source-done"], "topic-failed": ["source-failed"]},
        old_formal_tree_hash="b" * 64,
    )
    assert plan["status"] == "ready"
    assert plan["replay_source_ids"] == ["source-failed"]
    assert plan["replay_source_paths"] == ["failed.md"]
    assert plan["replay_topic_keys"] == ["topic-failed"]
    assert plan["preserved_source_ids"] == ["source-done", "source-unaffected"]
    assert plan["old_formal_preserved"] is True
    stopped = build_affected_replay_plan(
        affected=affected,
        batch_state=state,
        topic_sources={"topic-done": ["source-done"], "topic-failed": ["source-failed"]},
        contract_changed=True,
        contract_change_reason="reader contract changed",
        old_formal_tree_hash="b" * 64,
    )
    assert stopped["status"] == "stopped"
    assert stopped["replay_source_ids"] == []
    assert stopped["contract_change_reason"] == "reader contract changed"


def test_affected_replay_treats_successful_split_child_as_completed_and_stops_on_bad_old_hash() -> None:
    state = {
        "manifest_sha256": "a" * 64,
        "sources": [{"source_id": "source-split", "content_path": "split.md"}],
        "batches": [
            {"batch_id": "parent", "source_paths": ["split.md"], "status": "failed"},
            {"batch_id": "child", "source_paths": ["split.md"], "status": "succeeded", "split_from": "parent"},
        ],
    }
    affected = {"affected_source_ids": ["source-split"], "affected_topic_keys": []}
    completed = build_affected_replay_plan(affected=affected, batch_state=state, old_formal_tree_hash="b" * 64)
    assert completed["status"] == "nothing_to_replay"
    assert completed["replay_source_ids"] == []
    stopped = build_affected_replay_plan(affected=affected, batch_state=state, old_formal_tree_hash="not-a-tree-hash")
    assert stopped["status"] == "stopped"
    assert stopped["old_formal_hash_valid"] is False
    assert stopped["stop_reason"] == "old formal tree hash is invalid"
    assert stopped["replay_source_ids"] == []
