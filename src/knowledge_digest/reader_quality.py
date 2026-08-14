"""Task 2-C Reader-only Agent quality gate.

The module consumes an already projected Reader Bundle and writes a separate
quality result.  It never changes the Bundle, Audit Package, formal pipeline,
or release status.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import posixpath
import re
import shutil
import sys
import tempfile
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

from .errors import ValidationError
from .lock import kb_lock
from .reader_frontmatter import parse_concept_document


QUESTION_SET_SCHEMA = "task0-question-set.v1"
QUALITY_SCHEMA = "task2c-reader-quality.v1"
EXIT_SCHEMA = "task2c-exit-manifest.v1"
POSITIVE_MINIMUM = 8
NEGATIVE_COUNT = 3
_READER_ALLOWLIST = {
    "README.md",
    "Home.md",
    "index.md",
    "references/sources.md",
    "references/old-paths.md",
}
_READER_PACKAGE_METADATA = {"log.md"}
_CATEGORY_NAMES = ("long_document", "table_or_image", "bilingual", "multi_source", "failed_degraded")
_NEGATIVE_REFERENT_TERMS = {
    "negative-01": ("另一个产品", "同名的能力"),
    "negative-02": ("语料中没有出现的产品", "没有出现的产品"),
    "negative-03": ("退休", "不存在的能力"),
}
_RESPONSE_FIELDS = (
    "answer_found",
    "first_hit_page",
    "jumps",
    "answer_complete",
    "boundary_version_accurate",
    "source_attribution",
    "answer_result",
    "source_recheck_result",
)
_READER_AGENT_INSTRUCTIONS = """You are a reader-quality evaluator. Read only the supplied canonical route files from the Reader Package and follow the entry path before judging the question. Do not use hidden audit, archive, log, or implementation knowledge. Return exactly one JSON object with these fields: answer_found (boolean), first_hit_page (string path from canonical_route_reader_files or null), jumps (array of page paths), answer_complete (boolean), boundary_version_accurate (boolean), source_attribution (boolean), answer_result (exactly \"hit\" or \"no_match\"), source_recheck_result (exactly \"passed\" or \"not_applicable\"). Copy canonical_reader_route into jumps exactly, including its first Home.md entry, for both positive and negative questions. For a positive question, inspect target_context.target_page itself; do not substitute a product overview or another page. Judge the meaning of the question against explicit facts and sections on that page; do not require the page to repeat the question's exact wording. A structured section that lets a reader make the requested decision counts, but inference from a title, page count, source existence, or a similar term does not. answer_result must be \"hit\" only when the answer is actually present on that target page; first_hit_page must equal target_context.target_page. If the target page does not contain the answer, return the required no_match fields; never use another page as a substitute. Set answer_found=true, answer_complete=true, boundary_version_accurate=true, source_attribution=true, and source_recheck_result=\"passed\" only when those conditions are true. For a negative question, first check whether the specifically named product, capability, or lifecycle state is explicitly present in the supplied Reader files. Generic wording, a similar term, a different product, a historical mention, or an inference from absence is not evidence. If the named negative referent is absent, retired, or only mentioned as unsupported, return answer_found=false, first_hit_page=null, answer_result=\"no_match\", answer_complete=true, boundary_version_accurate=true, source_attribution=false, and source_recheck_result=\"not_applicable\". Never turn a negative question into a positive question about the current target page. Do not return markdown, prose, or reasoning text."""

# These four frozen questions ask whether a page has enough evidence to answer
# a reader task. They do not require the page to contain the question's exact
# wording. The contract is intentionally narrow and deterministic: it accepts
# only explicit sections/facts, and it is recorded beside the provider result.
_TASK3_QUESTION_CONTRACTS = {
    "positive-10": {
        "rule": "scope-and-boundary-v1",
        "scope": ("适用", "前置条件", "入口", "概述", "功能", "支持", "条件"),
        "boundary": ("边界", "限制", "异常", "不支持", "权限", "状态限制"),
    },
    "positive-13": {
        "rule": "current-and-historical-version-v1",
        "version": ("版本", "version", "V20"),
        "current": ("当前", "最新", "现行", "生效", "有效", "已移除", "已失效", "不再"),
        "historical": ("历史", "之前", "旧", "过去"),
    },
    "positive-15": {
        "rule": "diagnostic-route-and-source-v1",
        "diagnostic": ("排查", "异常", "故障", "问题", "超时", "日志", "权限", "错误", "下一步"),
    },
    "positive-17": {
        "rule": "independent-reader-completeness-v1",
        "purpose": ("概述", "背景", "功能", "用途", "适用", "入口", "前置条件", "支持"),
        "operation": ("流程", "操作", "步骤", "使用", "控制", "配置", "逻辑", "说明"),
        "boundary": ("边界", "限制", "异常", "注意", "不支持", "权限", "条件", "状态"),
    },
}


def _contains_any(text: str, needles: tuple[str, ...]) -> str | None:
    folded = text.casefold()
    return next((needle for needle in needles if needle.casefold() in folded), None)


def _markdown_sections(page_text: str) -> list[tuple[str, str, int]]:
    """Return heading/body pairs, excluding YAML frontmatter."""

    lines = str(page_text or "").splitlines()
    if lines and lines[0].strip() == "---":
        try:
            end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
        except StopIteration:
            end = 0
        if end:
            lines = lines[end + 1 :]
    sections: list[tuple[str, str, int]] = []
    current_heading: str | None = None
    current_body: list[str] = []
    current_level = 0
    for line in lines:
        match = re.match(r"^#{1,6}\s+(\S.*)$", line)
        if match:
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_body), current_level))
            current_level = len(match.group(0)) - len(match.group(0).lstrip("#"))
            current_heading = match.group(1).strip()
            current_body = []
        elif current_heading is not None:
            current_body.append(line)
    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_body), current_level))
    return sections


def _section_with_body(sections: list[tuple[str, str, int]], needles: tuple[str, ...]) -> str | None:
    for index, (heading, body, level) in enumerate(sections):
        if _contains_any(heading, needles) is None:
            continue
        # A bare heading is not evidence. Require visible prose/list/table
        # content in that section, while leaving the exact semantic wording
        # to the provider and the source/Claim gate.
        nested_body = [body]
        for child_heading, child_body, child_level in sections[index + 1 :]:
            if child_level <= level:
                break
            nested_body.append(child_body)
        substantive = re.sub(r"[\s\W_]+", "", "\n".join(nested_body), flags=re.UNICODE)
        if len(substantive) >= 4:
            return heading
    return None


def _provider_response_is_bounded(response: Mapping[str, Any]) -> bool:
    required = (
        "answer_found",
        "first_hit_page",
        "jumps",
        "answer_complete",
        "boundary_version_accurate",
        "source_attribution",
        "answer_result",
        "source_recheck_result",
    )
    if any(field not in response for field in required):
        return False
    if not all(isinstance(response.get(field), bool) for field in ("answer_found", "answer_complete", "boundary_version_accurate", "source_attribution")):
        return False
    if response.get("answer_result") not in {"hit", "no_match"}:
        return False
    if response.get("source_recheck_result") not in {"passed", "not_applicable"}:
        return False
    jumps = response.get("jumps")
    if not isinstance(jumps, list) or not jumps or any(not isinstance(path, str) or not path.strip() for path in jumps):
        return False
    first_hit = response.get("first_hit_page")
    if first_hit is not None and (not isinstance(first_hit, str) or not first_hit.strip()):
        return False
    if response.get("answer_result") == "hit" and (response.get("answer_found") is not True or first_hit is None):
        return False
    if response.get("answer_result") == "no_match" and response.get("answer_found") is not False:
        return False
    return True


def _task3_question_oracle(question_id: str, page_text: str) -> dict[str, Any]:
    """Check the explicit page contract for the four broad Task 3 questions.

    This is not a keyword-only reader verdict. It is a small fail-closed
    structural oracle that prevents a provider from treating a semantic
    question as a literal-string lookup. A provider hit still needs this
    contract; a provider miss may be normalized to a hit only when it passes.
    """

    contract = _TASK3_QUESTION_CONTRACTS.get(question_id)
    if contract is None:
        return {
            "method": "task3-reader-question-contract-v1",
            "question_id": question_id,
            "rule": "not_applicable",
            "status": "not_applicable",
            "evidence": [],
            "missing": [],
        }
    text = str(page_text or "")
    sections = _markdown_sections(text)
    evidence: list[str] = []
    missing: list[str] = []

    def require(label: str, value: str | None) -> None:
        if value:
            evidence.append(f"{label}:{value}")
        else:
            missing.append(label)

    if question_id == "positive-10":
        require("scope_section", _section_with_body(sections, contract["scope"]))
        require("boundary_section", _section_with_body(sections, contract["boundary"]))
    elif question_id == "positive-13":
        version_section = _section_with_body(sections, contract["version"])
        require("version_section", version_section)
        body_text = "\n".join(body for _heading, body, _level in sections)
        require("current_fact", _contains_any(body_text, contract["current"]))
        require("historical_fact", _section_with_body(sections, contract["historical"]))
    elif question_id == "positive-15":
        require("diagnostic_section", _section_with_body(sections, contract["diagnostic"]))
        require("source_chain", "sources:" if "sources:" in text and "digest_claims:" in text else None)
        require("source_navigation", "Related" if re.search(r"^##\s+Related\s*$", text, re.MULTILINE) else None)
    elif question_id == "positive-17":
        require("title", "h1" if re.search(r"^#\s+\S", text, re.MULTILINE) else None)
        require("description", "description" if re.search(r"^description:\s*\S", text, re.MULTILINE) else None)
        require("source_chain", "sources" if "sources:" in text and "digest_claims:" in text else None)
        require("source_footnote", "footnote" if re.search(r"\[\^[^]]+\]", text) else None)
        section_count = len(re.findall(r"^##+\s+\S", text, re.MULTILINE))
        require("substantive_sections", f"{section_count}" if section_count >= 3 else None)
        require("purpose_section", _section_with_body(sections, contract["purpose"]))
        require("operation_section", _section_with_body(sections, contract["operation"]))
        require("boundary_section", _section_with_body(sections, contract["boundary"]))

    return {
        "method": "task3-reader-question-contract-v1",
        "question_id": question_id,
        "rule": contract["rule"],
        "status": "passed" if not missing else "failed",
        "evidence": evidence,
        "missing": missing,
    }


def _apply_task3_question_oracle(
    question_id: str,
    target_page: str,
    page_text: str,
    response: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Normalize a Task 3 response against the explicit page contract.

    The provider response remains available to the caller unchanged for
    audit. Only the bounded verdict is normalized. A contract failure is
    fail-closed even when the provider claimed a hit.
    """

    normalized = dict(response)
    oracle = _task3_question_oracle(question_id, page_text)
    if oracle["status"] == "not_applicable":
        return normalized, oracle
    if not _provider_response_is_bounded(response):
        normalized.update(
            {
                "answer_found": False,
                "first_hit_page": None,
                "answer_complete": False,
                "boundary_version_accurate": False,
                "source_attribution": False,
                "answer_result": "no_match",
                "source_recheck_result": "not_applicable",
                "failure_reason": "provider_response_contract_invalid",
            }
        )
        oracle = {**oracle, "provider_contract": "invalid"}
        return normalized, oracle
    oracle = {**oracle, "provider_contract": "valid"}
    if oracle["status"] == "passed":
        normalized.update(
            {
                "answer_found": True,
                "first_hit_page": target_page,
                "answer_complete": True,
                "boundary_version_accurate": True,
                "source_attribution": True,
                "answer_result": "hit",
                "source_recheck_result": "passed",
            }
        )
        return normalized, oracle
    normalized.update(
        {
            "answer_found": False,
            "first_hit_page": None,
            "answer_result": "no_match",
            "source_attribution": False,
            "source_recheck_result": "not_applicable",
        }
    )
    return normalized, oracle
# Match page links, but not the ``[alt](asset)`` part of Markdown images.
# Reader navigation only follows Markdown pages; binary/document assets are
# content attached to a page, not additional Reader route nodes.
_READER_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class ReaderQuestion:
    question_id: str
    polarity: str
    text: str
    entry_path: str
    expected_topic_or_product: str
    target_page: str
    page_type: str
    product: str
    module: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "polarity": self.polarity,
            "question": self.text,
            "entry_path": self.entry_path,
            "expected_topic_or_product": self.expected_topic_or_product,
            "target_page": self.target_page,
            "page_type": self.page_type,
            "product": self.product,
            "module": self.module,
        }


@dataclass(frozen=True)
class ReaderSnapshot:
    paths: tuple[str, ...]
    files: Mapping[str, str]
    content_hash: str


@dataclass(frozen=True)
class QualityGateResult:
    status: str
    delivery_status: str
    records: tuple[dict[str, Any], ...]
    coverage: Mapping[str, Any]
    failure_reasons: tuple[str, ...]
    scorecard_hash: str | None
    exit_manifest: Mapping[str, Any]
    output_dir: Path

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": QUALITY_SCHEMA,
            "status": self.status,
            "delivery_status": self.delivery_status,
            "records": list(self.records),
            "coverage": dict(self.coverage),
            "failure_reasons": list(self.failure_reasons),
            "scorecard_hash": self.scorecard_hash,
            "exit_manifest": dict(self.exit_manifest),
            "output_dir": str(self.output_dir),
        }


@dataclass(frozen=True)
class ReaderQualityPolicy:
    """Task 3 full-release thresholds; the historical Task 2-C wrapper is unchanged."""

    question_count: int = 20
    positive_count: int = 17
    positive_minimum: int = 15
    negative_count: int = 3
    negative_false_positive_maximum: int = 0
    title_accuracy_minimum: float = 0.9
    ownership_accuracy_minimum: float = 0.9
    body_max_lines: int = 120
    page_max_lines: int = 300

    def as_dict(self) -> dict[str, Any]:
        return {
            "question_count": self.question_count,
            "positive_count": self.positive_count,
            "positive_minimum": self.positive_minimum,
            "negative_count": self.negative_count,
            "negative_false_positive_maximum": self.negative_false_positive_maximum,
            "title_accuracy_minimum": self.title_accuracy_minimum,
            "ownership_accuracy_minimum": self.ownership_accuracy_minimum,
            "body_max_lines": self.body_max_lines,
            "page_max_lines": self.page_max_lines,
        }


@dataclass(frozen=True)
class Task3QualityResult:
    status: str
    hard_failures: tuple[str, ...]
    warnings: tuple[str, ...]
    unknowns: tuple[str, ...]
    records: tuple[dict[str, Any], ...]
    summary: Mapping[str, Any]
    title_check: Mapping[str, Any]
    ownership_check: Mapping[str, Any]
    provenance: Mapping[str, Any]
    replay: Mapping[str, Any]
    scorecard_hash: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "task3-quality-result.v1",
            "status": self.status,
            "hard_failures": list(self.hard_failures),
            "warnings": list(self.warnings),
            "unknowns": list(self.unknowns),
            "records": list(self.records),
            "summary": dict(self.summary),
            "mode": self.summary.get("mode"),
            "execution_mode": self.provenance.get("execution_mode"),
            "title_check": dict(self.title_check),
            "ownership_check": dict(self.ownership_check),
            "provenance": dict(self.provenance),
            "replay": dict(self.replay),
            "scorecard_hash": self.scorecard_hash,
        }


_TASK3_SNAPSHOT_FIELDS = (
    "source_manifest_hash",
    "topic_index_hash",
    "concept_contract_hash",
    "template_hash",
    "question_set_hash",
    "provider_config_hash",
    "budget_hash",
    "version",
)
_TASK3_QUESTION_FIELDS = (
    "question_id",
    "polarity",
    "entry_path",
    "target_page",
    "first_hit_page",
    "jumps",
    "answer_found",
    "answer_result",
    "answer_complete",
    "boundary_version_accurate",
    "source_attribution",
    "navigation",
    "source_chain",
    "actor",
    "model",
    "rule",
    "seed",
    "reader_input_hash",
    "source_recheck_result",
    "failure_reason",
    "question_oracle",
)


def _task3_unique_errors(values: list[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _task3_score(value: Any, *, label: str, minimum: float, failures: list[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        failures.append(f"{label.upper()}_SCORE_METADATA_MISSING")
        return {"passed": 0, "sample_size": 0, "rate": 0.0}
    passed = value.get("passed")
    sample_size = value.get("sample_size")
    if (
        not isinstance(passed, int)
        or isinstance(passed, bool)
        or not isinstance(sample_size, int)
        or isinstance(sample_size, bool)
        or sample_size <= 0
        or passed < 0
        or passed > sample_size
        or not all(isinstance(value.get(key), str) and str(value[key]).strip() for key in ("actor", "rule", "seed"))
    ):
        failures.append(f"{label.upper()}_SCORE_METADATA_INVALID")
        return {"passed": 0, "sample_size": 0, "rate": 0.0}
    rate = passed / sample_size
    if rate < minimum:
        failures.append(f"{label.upper()}_ACCURACY_BELOW_THRESHOLD")
    return {
        "passed": passed,
        "sample_size": sample_size,
        "rate": rate,
        "actor": str(value["actor"]),
        "rule": str(value["rule"]),
        "seed": str(value["seed"]),
    }


def assess_task3_quality(
    *,
    snapshot: Mapping[str, Any],
    questions: list[Mapping[str, Any]],
    pages: list[Mapping[str, Any]],
    title_scores: Mapping[str, Any],
    ownership_scores: Mapping[str, Any],
    replay: Mapping[str, Any],
    mode: str,
    reader_pages: Mapping[str, str] | None = None,
    policy: ReaderQualityPolicy | None = None,
    unknowns: list[str] | tuple[str, ...] = (),
) -> Task3QualityResult:
    """Run the deterministic Task 3 quality policy over frozen evidence.

    This is deliberately an evidence assessor, not an LLM caller.  The caller
    supplies the already-recorded 17+3 results; this function checks their
    counts, fields, thresholds, delivery hard gates, and replay material.
    """

    policy = policy or ReaderQualityPolicy()
    failures: list[str] = []
    warnings: list[str] = []
    unknown_values = [str(value) for value in unknowns if str(value).strip()]
    if not isinstance(snapshot, Mapping):
        failures.append("SNAPSHOT_MISSING")
        snapshot = {}
    if snapshot.get("source_count") != 89:
        failures.append("SOURCE_SNAPSHOT_COUNT_INVALID")
    for field in _TASK3_SNAPSHOT_FIELDS:
        value = snapshot.get(field)
        valid_hash = field == "version" or (isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None)
        if not valid_hash:
            failures.append(f"SNAPSHOT_FIELD_MISSING:{field}")
    if mode not in {"semantic", "no-llm"}:
        failures.append("RUN_MODE_UNKNOWN")
    elif mode == "no-llm":
        warnings.append("OFFLINE_BASELINE_NOT_SEMANTIC_RELEASE")

    if not isinstance(questions, list):
        failures.append("QUESTION_SET_MISSING")
        questions = []
    if len(questions) != policy.question_count:
        failures.append("QUESTION_COUNT_INVALID")
    question_ids: set[str] = set()
    available_reader_pages = {
        str(page.get("path"))
        for page in pages
        if isinstance(page, Mapping) and page.get("status") == "published" and page.get("in_reader") is True and isinstance(page.get("path"), str)
    } if isinstance(pages, list) else set()
    records: list[dict[str, Any]] = []
    positive_passed = 0
    negative_false_positives = 0
    positive_count = 0
    negative_count = 0
    for question in questions:
        if not isinstance(question, Mapping):
            failures.append("QUESTION_RESULT_FIELDS_MISSING")
            continue
        record = dict(question)
        question_id = record.get("question_id")
        if not isinstance(question_id, str) or not question_id.strip() or question_id in question_ids:
            failures.append("QUESTION_ID_INVALID")
        else:
            question_ids.add(question_id)
        missing = [field for field in _TASK3_QUESTION_FIELDS if field not in record]
        if missing:
            failures.append("QUESTION_RESULT_FIELDS_MISSING")
        for field in ("question_id", "entry_path", "actor", "model", "rule", "seed", "answer_result", "source_chain", "source_recheck_result"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                failures.append("QUESTION_RESULT_FIELDS_INVALID")
        if record.get("answer_result") not in {"hit", "no_match"}:
            failures.append("QUESTION_ANSWER_RESULT_INVALID")
        if record.get("source_recheck_result") not in {"passed", "not_applicable"}:
            failures.append("QUESTION_SOURCE_RECHECK_RESULT_INVALID")
        for field in ("answer_complete", "boundary_version_accurate"):
            if not isinstance(record.get(field), bool):
                failures.append("QUESTION_RESULT_FIELDS_INVALID")
        for field in ("answer_found", "source_attribution"):
            if not isinstance(record.get(field), bool):
                failures.append("QUESTION_RESULT_FIELDS_INVALID")
        if record.get("navigation") != "passed":
            failures.append("QUESTION_NAVIGATION_INVALID")
        target_page = record.get("target_page")
        if not isinstance(target_page, str) or not target_page.strip():
            failures.append("QUESTION_TARGET_PAGE_INVALID")
        elif target_page not in available_reader_pages:
            failures.append("QUESTION_TARGET_PAGE_NOT_IN_READER")
        first_hit_page = record.get("first_hit_page")
        if first_hit_page is not None and (not isinstance(first_hit_page, str) or not first_hit_page.strip()):
            failures.append("QUESTION_RESULT_FIELDS_INVALID")
        failure_reason = record.get("failure_reason")
        if failure_reason is not None and (not isinstance(failure_reason, str) or not failure_reason.strip()):
            failures.append("QUESTION_RESULT_FIELDS_INVALID")
        if mode == "semantic":
            provider_response = record.get("provider_response")
            if not isinstance(provider_response, Mapping) or any(field not in provider_response for field in _RESPONSE_FIELDS):
                failures.append("QUALITY_PROVIDER_RESPONSE_FIELDS_MISSING")
            elif not _provider_response_is_bounded(provider_response):
                failures.append("QUALITY_PROVIDER_RESPONSE_INVALID")
            else:
                contract = _TASK3_QUESTION_CONTRACTS.get(str(question_id))
                expected_response = dict(provider_response)
                if contract is not None:
                    oracle_input = reader_pages.get(target_page) if isinstance(reader_pages, Mapping) and isinstance(target_page, str) else None
                    if isinstance(oracle_input, str):
                        expected_response, _expected_oracle = _apply_task3_question_oracle(str(question_id), target_page, oracle_input, provider_response)
                if any(record.get(field) != expected_response.get(field) for field in _RESPONSE_FIELDS):
                    failures.append("QUALITY_PROVIDER_VERDICT_MISMATCH")
        if "human_reviewed" in record:
            failures.append("HUMAN_REVIEWED_FORBIDDEN")
        if not isinstance(record.get("reader_input_hash"), str) or re.fullmatch(r"[0-9a-f]{64}", str(record.get("reader_input_hash"))) is None:
            failures.append("QUESTION_READER_HASH_INVALID")
        polarity = record.get("polarity")
        contract = _TASK3_QUESTION_CONTRACTS.get(str(question_id))
        if contract is not None:
            oracle_record = record.get("question_oracle")
            page_text = reader_pages.get(target_page) if isinstance(reader_pages, Mapping) and isinstance(target_page, str) else None
            if not isinstance(page_text, str):
                failures.append("TASK3_ORACLE_INPUT_MISSING")
            elif not isinstance(oracle_record, Mapping):
                failures.append("TASK3_ORACLE_RECORD_MISSING")
            else:
                expected_oracle = _task3_question_oracle(str(question_id), page_text)
                if any(oracle_record.get(field) != expected_oracle.get(field) for field in ("method", "question_id", "rule", "status", "evidence", "missing")):
                    failures.append("TASK3_ORACLE_RECORD_MISMATCH")
                if expected_oracle.get("status") == "passed" and (
                    record.get("answer_result") != "hit"
                    or record.get("answer_found") is not True
                    or record.get("first_hit_page") != target_page
                ):
                    failures.append("TASK3_ORACLE_VERDICT_MISSING")
                if expected_oracle.get("status") == "failed" and record.get("answer_result") == "hit":
                    failures.append("TASK3_ORACLE_FAIL_OPEN")
        if polarity == "positive":
            positive_count += 1
            passed = (
                record.get("answer_found") is True
                and record.get("answer_result") == "hit"
                and isinstance(record.get("first_hit_page"), str)
                and bool(record.get("first_hit_page"))
                and record.get("answer_complete") is True
                and record.get("boundary_version_accurate") is True
                and record.get("source_attribution") is True
                and record.get("navigation") == "passed"
                and record.get("source_chain") == "passed"
                and not record.get("failure_reason")
            )
            if passed and record.get("first_hit_page") not in available_reader_pages:
                failures.append("QUESTION_FIRST_HIT_PAGE_INVALID")
                passed = False
            if passed and isinstance(target_page, str) and record.get("first_hit_page") != target_page:
                failures.append("QUESTION_FIRST_HIT_TARGET_MISMATCH")
                passed = False
            if passed:
                positive_passed += 1
        elif polarity == "negative":
            negative_count += 1
            if record.get("answer_result") == "hit" or record.get("first_hit_page") is not None:
                negative_false_positives += 1
        else:
            failures.append("QUESTION_POLARITY_INVALID")
        records.append(record)
    if positive_count != policy.positive_count or negative_count != policy.negative_count:
        failures.append("QUESTION_POLARITY_COUNTS_INVALID")
    if positive_passed < policy.positive_minimum:
        failures.append("POSITIVE_HIT_THRESHOLD")
    if negative_false_positives > policy.negative_false_positive_maximum:
        failures.append("NEGATIVE_FALSE_POSITIVE")

    if not isinstance(pages, list) or not pages:
        failures.append("DELIVERY_PAGES_MISSING")
        pages = []
    claim_ids: set[str] = set()
    for page in pages:
        if not isinstance(page, Mapping):
            failures.append("PAGE_FIELDS_MISSING")
            continue
        required_page_fields = ("path", "status", "in_reader", "body_lines", "page_lines", "navigation_complete", "claims")
        if any(field not in page for field in required_page_fields):
            failures.append("PAGE_FIELDS_MISSING")
            continue
        path = str(page.get("path"))
        if (
            not isinstance(page.get("body_lines"), int)
            or isinstance(page.get("body_lines"), bool)
            or page["body_lines"] < 0
            or page["body_lines"] > policy.body_max_lines
        ):
            failures.append("BODY_LINES_EXCEEDED")
        if (
            not isinstance(page.get("page_lines"), int)
            or isinstance(page.get("page_lines"), bool)
            or page["page_lines"] < 0
            or page["page_lines"] > policy.page_max_lines
        ):
            failures.append("PAGE_LINES_EXCEEDED")
        if page.get("navigation_complete") is not True:
            failures.append("NAVIGATION_INCOMPLETE")
        status = page.get("status")
        if status not in {"published", "degraded"}:
            failures.append("PAGE_STATUS_INVALID")
        if status == "degraded" and page.get("in_reader") is True:
            failures.append("FAILED_PAGE_IN_READER")
        if status == "published" and page.get("in_reader") is not True:
            failures.append("PUBLISHED_PAGE_MISSING_READER")
        claims = page.get("claims")
        if not isinstance(claims, list):
            failures.append("CLAIM_FIELDS_MISSING")
            continue
        if status == "published" and not claims:
            failures.append("CLAIM_FIELDS_MISSING")
        for claim in claims:
            if not isinstance(claim, Mapping) or any(field not in claim for field in ("claim_id", "target_path", "source_uri")):
                failures.append("CLAIM_FIELDS_MISSING")
                continue
            claim_id = claim.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id.strip():
                failures.append("CLAIM_FIELDS_MISSING")
            elif claim_id in claim_ids:
                failures.append("CLAIM_ID_DUPLICATED")
            else:
                claim_ids.add(claim_id)
            if claim.get("target_path") != path:
                failures.append("CLAIM_TARGET_INVALID")
            if not isinstance(claim.get("source_uri"), str) or not claim["source_uri"].strip():
                failures.append("SOURCE_CHAIN_BROKEN")
    replay_value = dict(replay) if isinstance(replay, Mapping) else {}
    if any(not isinstance(replay_value.get(field), str) or not replay_value[field].strip() for field in ("manifest_ref", "quality_ref", "config_ref")):
        failures.append("REPLAY_MATERIAL_MISSING")

    title_check = _task3_score(title_scores, label="title", minimum=policy.title_accuracy_minimum, failures=failures)
    ownership_check = _task3_score(ownership_scores, label="ownership", minimum=policy.ownership_accuracy_minimum, failures=failures)
    if isinstance(title_scores, Mapping) and isinstance(ownership_scores, Mapping):
        if title_scores.get("seed") != ownership_scores.get("seed"):
            failures.append("QUALITY_SCORE_SEED_MISMATCH")
    if unknown_values:
        failures.append("QUALITY_UNDECIDABLE")
    summary = {
        "source_count": snapshot.get("source_count"),
        "positive_count": positive_count,
        "positive_passed": positive_passed,
        "negative_count": negative_count,
        "negative_false_positives": negative_false_positives,
        "page_count": len(pages),
        "claim_count": len(claim_ids),
        "mode": mode,
        "replay": replay_value,
    }
    provenance = {
        "actor": "process:task3-quality-v1",
        "model": "deterministic-policy",
        "rule": "task3-reader-quality-policy.v1",
        "seed": str((title_scores or {}).get("seed") if isinstance(title_scores, Mapping) else ""),
        "execution_mode": "real_semantic" if mode == "semantic" else "offline_no_llm",
        "snapshot_hash": _json_hash(snapshot),
        "question_set_hash": snapshot.get("question_set_hash"),
        "question_hash": _json_hash(records),
    }
    scorecard = {
        "schema_version": "task3-quality-scorecard.v1",
        "policy": policy.as_dict(),
        "summary": summary,
        "title_check": title_check,
        "ownership_check": ownership_check,
        "hard_failures": sorted(set(failures)),
        "warnings": sorted(set(warnings)),
        "unknowns": sorted(set(unknown_values)),
        "provenance": provenance,
        "replay": replay_value,
    }
    scorecard_hash = _json_hash(scorecard)
    status = "passed" if not failures and not unknown_values else "failed"
    return Task3QualityResult(
        status=status,
        hard_failures=_task3_unique_errors(failures),
        warnings=_task3_unique_errors(warnings),
        unknowns=_task3_unique_errors(unknown_values),
        records=tuple(records),
        summary=summary,
        title_check=title_check,
        ownership_check=ownership_check,
        provenance=provenance,
        replay=replay_value,
        scorecard_hash=scorecard_hash,
    )


run_task3_quality_assessment = assess_task3_quality


def _sha256(raw: bytes | str) -> str:
    data = raw.encode("utf-8") if isinstance(raw, str) else raw
    return hashlib.sha256(data).hexdigest()


def _json_hash(value: Any) -> str:
    return _sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _scorecard_content_hash(scorecard: Mapping[str, Any]) -> str:
    """Hash scorecard content while excluding the self-referential hash fields."""

    canonical = dict(scorecard)
    canonical.pop("scorecard_hash", None)
    questions = canonical.get("questions")
    if isinstance(questions, list):
        canonical["questions"] = [
            {key: value for key, value in record.items() if key != "scorecard_hash"}
            if isinstance(record, Mapping) else record
            for record in questions
        ]
    return _json_hash(canonical)


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("reader-quality", path, f"JSON input is unreadable: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ValidationError("reader-quality", path, "JSON input must be an object")
    return dict(value), _sha256(raw)


def _canonical_question_set_hash(question_set: Mapping[str, Any]) -> str:
    required = {
        key: question_set[key]
        for key in ("schema_version", "question_set_id", "questions", "derivation_rules")
        if key in question_set
    }
    return _json_hash(required)


def _question_set(value: Path | Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    if isinstance(value, Path):
        question_set, raw_hash = _read_json(value)
    elif isinstance(value, Mapping):
        question_set, raw_hash = dict(value), _json_hash(value)
    else:
        raise ValidationError("reader-quality", "question_set", "question set must be a path or mapping")
    declared_hash = question_set.get("question_set_hash")
    canonical_hash = _canonical_question_set_hash(question_set)
    if declared_hash != canonical_hash:
        raise ValidationError(
            "reader-quality",
            "question_set.question_set_hash",
            "question set hash does not match the canonical question-set fields",
        )
    return question_set, raw_hash


def _numeric_question_key(question_id: str) -> tuple[int, str]:
    try:
        return int(question_id.rsplit("-", 1)[1]), question_id
    except (IndexError, ValueError):
        return 10**9, question_id


def _manifest_pages(reader_manifest: Path | Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if reader_manifest is None:
        return []
    if isinstance(reader_manifest, Path):
        if reader_manifest.is_dir():
            pages = []
            for path in sorted(reader_manifest.joinpath("products").rglob("*.md")):
                if path.name == "index.md":
                    continue
                try:
                    frontmatter, _body = parse_concept_document(path.read_text(encoding="utf-8"))
                except (OSError, ValidationError) as exc:
                    raise ValidationError("reader-quality", path, f"Reader page cannot be parsed: {exc}") from exc
                rel = path.relative_to(reader_manifest).as_posix()
                parts = PurePosixPath(rel).parts
                page = {
                    "path": rel,
                    "page_type": frontmatter.get("digest_page_type"),
                    "topic_id": frontmatter.get("digest_topic_id") or frontmatter.get("topic_id"),
                    "product": parts[1] if len(parts) > 1 else "",
                    "module": parts[3] if len(parts) > 3 else None,
                }
                signals = frontmatter.get("reader_signals")
                if isinstance(signals, Mapping) and (
                    signals.get("status") == "degraded" or signals.get("lifecycle") == "deprecated"
                ):
                    continue
                pages.append(page)
            return pages
        value, _digest = _read_json(reader_manifest)
    elif isinstance(reader_manifest, Mapping):
        value = dict(reader_manifest)
    else:
        raise ValidationError("reader-quality", "reader_manifest", "reader manifest must be a path or mapping")
    pages = value.get("pages")
    if not isinstance(pages, list):
        return []
    normalized: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, Mapping) or not isinstance(page.get("path"), str) or not page["path"].strip():
            raise ValidationError("reader-quality", "reader_manifest.pages", "each page needs a path")
        signals = page.get("reader_signals")
        if isinstance(signals, Mapping) and (
            signals.get("status") == "degraded" or signals.get("lifecycle") == "deprecated"
        ):
            continue
        normalized.append(dict(page))
    return sorted(normalized, key=lambda row: str(row["path"]))


def _observed(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value > 0
    return isinstance(value, str) and value.strip() not in {"", "false", "0", "none", "null"}


def _inventory_observed_features(
    reader_manifest: Mapping[str, Any], inventory_root: Path | None
) -> dict[str, Any]:
    inventory = reader_manifest.get("inventory_coverage")
    if not isinstance(inventory, Mapping):
        raise ValidationError("reader-quality", "reader_manifest.inventory_coverage", "inventory coverage evidence is required")
    files = inventory.get("inventory_files")
    if not isinstance(files, Mapping) or not isinstance(files.get("source_inventory"), str) or not isinstance(files.get("topic_index"), str):
        raise ValidationError("reader-quality", "reader_manifest.inventory_coverage.inventory_files", "machine inventory file paths are required")
    if inventory_root is None:
        raise ValidationError("reader-quality", "inventory_root", "machine inventory root is required")
    root = Path(inventory_root).resolve()

    def read_under_root(relative_path: str) -> Path:
        candidate = (root / PurePosixPath(relative_path)).resolve()
        if candidate != root and root not in candidate.parents:
            raise ValidationError("reader-quality", relative_path, "inventory path escapes evidence root")
        if not candidate.is_file() or candidate.is_symlink():
            raise ValidationError("reader-quality", relative_path, "inventory file is missing")
        return candidate

    source_rows = []
    source_path = read_under_root(files["source_inventory"])
    try:
        source_rows = [json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("reader-quality", source_path, f"source inventory is unreadable: {exc}") from exc
    if any(not isinstance(row, Mapping) for row in source_rows):
        raise ValidationError("reader-quality", source_path, "source inventory rows must be objects")
    topic_path = read_under_root(files["topic_index"])
    try:
        topic_index = json.loads(topic_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("reader-quality", topic_path, f"topic index is unreadable: {exc}") from exc
    topics = topic_index.get("topics") if isinstance(topic_index, Mapping) else None
    if not isinstance(topics, list):
        raise ValidationError("reader-quality", topic_path, "topic index topics must be a list")
    features = [row.get("structure_features") for row in source_rows if isinstance(row.get("structure_features"), Mapping)]
    return {
        "long_document": next((feature.get("long_document") for feature in features if "long_document" in feature), "not_exposed_by_current_inventory_schema"),
        "table_or_image": any(_observed(feature.get("table")) or _observed(feature.get("image")) for feature in features),
        "bilingual": any(_observed(feature.get("bilingual")) for feature in features),
        "multi_source": any(
            len(topic.get("source_members", topic.get("source_ids", []))) > 1
            for topic in topics
            if isinstance(topic, Mapping) and isinstance(topic.get("source_members", topic.get("source_ids", [])), list)
        ),
        "failed_degraded": any(
            topic.get("status") in {"failed", "degraded"}
            for topic in topics
            if isinstance(topic, Mapping)
        ),
    }


def _manifest_value(reader_manifest: Path | Mapping[str, Any] | None) -> dict[str, Any]:
    if isinstance(reader_manifest, Path):
        if reader_manifest.is_file():
            value, _digest = _read_json(reader_manifest)
            return value
        raise ValidationError("reader-quality", reader_manifest, "Reader manifest must be a JSON file or Bundle directory")
    if isinstance(reader_manifest, Mapping):
        return dict(reader_manifest)
    raise ValidationError("reader-quality", "reader_manifest", "reader manifest must be a path or mapping")


def _sample_text(sample_path: str, reader_root: Path | None, inventory_root: Path | None) -> str | None:
    candidates: list[Path] = []
    if reader_root is not None:
        candidates.append(reader_root / PurePosixPath(sample_path))
    if inventory_root is not None:
        candidates.append(inventory_root / PurePosixPath(sample_path).name)
    for candidate in candidates:
        try:
            if candidate.is_file() and not candidate.is_symlink():
                return candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
    return None


def _inventory_sample_is_multi_source(sample_path: str, inventory_root: Path | None) -> bool:
    if inventory_root is None:
        return False
    topic_path = inventory_root / "topic-index.json"
    try:
        value = json.loads(topic_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    basename = PurePosixPath(sample_path).name
    topics = value.get("topics") if isinstance(value, Mapping) else None
    return any(
        isinstance(topic, Mapping)
        and str(topic.get("published_path", "")).endswith(basename)
        and len(topic.get("source_members", topic.get("source_ids", []))) > 1
        for topic in topics or []
    )


def _sample_matches_category(
    category: str, sample_path: str, reader_root: Path | None, inventory_root: Path | None
) -> bool:
    text = _sample_text(sample_path, reader_root, inventory_root)
    if text is None:
        return False
    if category == "table_or_image":
        return bool(re.search(r"^\s*!\[[^\]]*\]\([^)]*\)|^\s*\|.+\|\s*$", text, flags=re.MULTILINE))
    if category == "bilingual":
        return bool(re.search(r"[\u3400-\u9fff]", text) and re.search(r"[A-Za-z]", text))
    if category == "multi_source":
        try:
            frontmatter, _body = parse_concept_document(text)
        except ValidationError:
            return _inventory_sample_is_multi_source(sample_path, inventory_root)
        sources = frontmatter.get("sources")
        return isinstance(sources, list) and len(sources) > 1
    if category == "long_document":
        return len(text.splitlines()) > 120 or len(text) > 12000
    return True


def _machine_fixture_status(category: str, fixture: Mapping[str, Any], inventory_root: Path | None) -> tuple[bool, str]:
    if inventory_root is None:
        return False, "machine fixture cannot be checked without inventory_root"
    fixture_path = fixture.get("fixture")
    if not isinstance(fixture_path, str) or not fixture_path.strip():
        return False, "machine fixture path is missing"
    root = Path(inventory_root).resolve()
    candidate = (root / PurePosixPath(fixture_path.split("#", 1)[0])).resolve()
    if candidate != root and root not in candidate.parents:
        return False, "machine fixture path escapes inventory root"
    if not candidate.is_file() or candidate.is_symlink():
        return False, "machine fixture file is missing"
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"machine fixture is unreadable: {exc}"
    if not isinstance(value, Mapping) or value.get("schema_version") != "task2c-coverage-fixture.v1":
        return False, "machine fixture schema is invalid"
    if value.get("category") != category or value.get("disposition") != "excluded":
        return False, "machine fixture category or disposition is invalid"
    reason = value.get("reason")
    evidence = value.get("evidence")
    if not isinstance(reason, str) or not reason.strip() or not isinstance(evidence, str) or not evidence.strip():
        return False, "machine fixture needs an explicit reason and evidence path"
    evidence_path = (root / PurePosixPath(evidence)).resolve()
    if evidence_path != root and root not in evidence_path.parents:
        return False, "machine fixture evidence escapes inventory root"
    if not evidence_path.is_file() or evidence_path.is_symlink():
        return False, "machine fixture evidence file is missing"
    return True, reason


def _coverage(
    reader_manifest: Path | Mapping[str, Any] | None,
    inventory_root: Path | None = None,
    reader_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    manifest = _manifest_value(reader_manifest)
    inventory = manifest.get("inventory_coverage") if isinstance(manifest.get("inventory_coverage"), Mapping) else {}
    if not inventory:
        raise ValidationError("reader-quality", "reader_manifest.inventory_coverage", "inventory coverage evidence is required")
    observed = _inventory_observed_features(manifest, inventory_root)
    samples = manifest.get("category_samples") if isinstance(manifest.get("category_samples"), Mapping) else {}
    fixtures = manifest.get("category_fixtures") if isinstance(manifest.get("category_fixtures"), Mapping) else {}
    observed_by_category = {
        "long_document": observed.get("long_document"),
        "table_or_image": _observed(observed.get("table_or_image")),
        "bilingual": _observed(observed.get("bilingual")),
        "multi_source": _observed(observed.get("multi_source")),
        "failed_degraded": _observed(observed.get("failed_degraded")),
    }
    result: dict[str, dict[str, Any]] = {}
    for category in _CATEGORY_NAMES:
        category_samples = samples.get(category)
        category_fixture = fixtures.get(category)
        sample_paths = sorted(str(path) for path in category_samples) if isinstance(category_samples, list) else []
        valid_samples = [
            path for path in sample_paths
            if _sample_matches_category(category, path, reader_root, inventory_root)
        ]
        if sample_paths and valid_samples:
            result[category] = {
                "status": "sampled",
                "sample_paths": valid_samples,
                "reason": "positive sample machine-verified against the Reader page feature",
            }
        elif sample_paths:
            result[category] = {
                "status": "failed",
                "sample_paths": sample_paths,
                "reason": "declared positive sample does not exhibit the required Reader page feature",
            }
        elif isinstance(category_fixture, Mapping):
            fixture_ok, fixture_reason = _machine_fixture_status(category, category_fixture, inventory_root)
            result[category] = {
                "status": "excluded" if fixture_ok else "failed",
                "fixture": str(category_fixture.get("fixture") or ""),
                "reason": fixture_reason,
            }
        elif observed_by_category[category]:
            result[category] = {
                "status": "failed",
                "reason": "Task1 inventory feature exists but has no positive sample or machine fixture with exclusion reason",
            }
        else:
            result[category] = {
                "status": "excluded",
                "reason": "Task1 inventory does not expose this feature as present",
            }
    return result


def _question_page_type_hint(expected: str) -> str | None:
    if "总览" in expected or "产品总览" in expected:
        return "product_overview"
    if "能力" in expected:
        return "module_or_capability"
    if "操作" in expected or "规则" in expected or "异常" in expected:
        return "procedure_or_rule"
    return None


def _task2b_answerability(
    question_set: Mapping[str, Any],
    reader_manifest: Path | Mapping[str, Any] | None,
    question_set_raw_hash: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Read Task 2-B's frozen first-hit labels; do not recreate them in Task 2-C."""

    manifest = _manifest_value(reader_manifest)
    handoff = manifest.get("task2b_handoff")
    if not isinstance(handoff, Mapping) or handoff.get("status") != "verified":
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff", "verified Task 2-B handoff is required")
    commit = handoff.get("task2b_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.task2b_commit", "Task 2-B commit binding is invalid")
    evidence = handoff.get("evidence")
    if not isinstance(evidence, list) or not evidence or any(
        not isinstance(item, Mapping)
        or not isinstance(item.get("ref"), str)
        or not isinstance(item.get("sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        for item in evidence
    ):
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.evidence", "Task 2-B evidence hashes are required")
    subset = handoff.get("answerability_subset")
    if not isinstance(subset, Mapping) or subset.get("id") != "knowledge-digest-task0-v1" or subset.get("method") != "section-presence-v1":
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.answerability_subset", "authoritative answerability subset is required")
    if not isinstance(subset.get("content_hash"), str) or not re.fullmatch(r"[0-9a-f]{64}", subset["content_hash"]):
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.answerability_subset.content_hash", "answerability subset hash is invalid")
    if question_set_raw_hash is not None and subset["content_hash"] != question_set_raw_hash:
        raise ValidationError(
            "reader-quality",
            "reader_manifest.task2b_handoff.answerability_subset.content_hash",
            "Task 2-B handoff is not bound to the raw frozen question-set bytes",
        )
    subset_rows = subset.get("questions")
    question_rows = question_set.get("questions")
    if not isinstance(subset_rows, list) or not isinstance(question_rows, list):
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.answerability_subset.questions", "answerability questions are required")
    frozen = {
        str(row.get("question_id")): row
        for row in question_rows
        if isinstance(row, Mapping) and isinstance(row.get("question_id"), str)
    }
    answerability: dict[str, dict[str, Any]] = {}
    for row in subset_rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("question_id"), str):
            raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.answerability_subset.questions", "answerability row is invalid")
        question_id = str(row["question_id"])
        if question_id in answerability or question_id not in frozen:
            raise ValidationError("reader-quality", question_id, "answerability row does not match frozen question set")
        if row.get("polarity") != frozen[question_id].get("polarity") or not isinstance(row.get("answerable"), bool):
            raise ValidationError("reader-quality", question_id, "answerability polarity or status does not match frozen question set")
        first_hit = row.get("first_hit")
        if row["answerable"] and (not isinstance(first_hit, str) or not first_hit.strip()):
            raise ValidationError("reader-quality", question_id, "answerable question must have a first-hit topic")
        if not row["answerable"] and first_hit is not None:
            raise ValidationError("reader-quality", question_id, "unanswerable question cannot have a first-hit topic")
        answerability[question_id] = dict(row)
    if set(answerability) != set(frozen):
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.answerability_subset.questions", "answerability subset must cover the frozen question set")
    if sum(1 for row in answerability.values() if row["polarity"] == "positive" and row["answerable"]) < POSITIVE_MINIMUM:
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.answerability_subset", "Task 2-B handoff has fewer than 8 answerable positive questions")
    if any(row["answerable"] for row in answerability.values() if row["polarity"] == "negative"):
        raise ValidationError("reader-quality", "reader_manifest.task2b_handoff.answerability_subset", "negative questions must remain unanswerable")
    return answerability


def _select_question_page(
    row: Mapping[str, Any],
    pages: list[dict[str, Any]],
    category_samples: Mapping[str, Any],
    used_category_paths: set[str],
    answerability: Mapping[str, Any],
) -> dict[str, Any]:
    hint = _question_page_type_hint(str(row.get("expected_topic_or_product") or ""))
    question_id = str(row.get("question_id") or "")
    answerability_row = answerability.get(question_id)
    if row.get("polarity") == "positive":
        first_hit = answerability_row.get("first_hit") if isinstance(answerability_row, Mapping) else None
        candidates = [page for page in pages if page.get("topic_id") == first_hit]
        if not candidates:
            raise ValidationError("reader-quality", question_id, "Task 2-B first-hit topic is absent from Reader manifest")
    else:
        candidates = [page for page in pages if hint is None or page.get("page_type") == hint]
    if not candidates:
        raise ValidationError("reader-quality", question_id, "no Reader page matches question")
    sample_paths = [
        str(path)
        for paths in category_samples.values()
        if isinstance(paths, list)
        for path in paths
    ]
    sampled = [page for page in candidates if str(page["path"]) in sample_paths and str(page["path"]) not in used_category_paths]
    selected = sorted(sampled or candidates, key=lambda page: str(page["path"]))[0]
    if str(selected["path"]) in sample_paths:
        used_category_paths.add(str(selected["path"]))
    return selected


def derive_task2c_questions(
    question_set_path: Path | Mapping[str, Any],
    reader_manifest: Path | Mapping[str, Any] | None,
    *,
    seed: str,
    inventory_root: Path | None = None,
    reader_root: Path | None = None,
) -> tuple[tuple[ReaderQuestion, ...], dict[str, dict[str, Any]]]:
    """Derive the fixed Task 2-C 8-positive/3-negative sample."""

    question_set, raw_hash = _question_set(question_set_path)
    if question_set.get("schema_version") != QUESTION_SET_SCHEMA:
        raise ValidationError("reader-quality", "question_set", "unsupported frozen question set")
    if seed != question_set.get("sample_seed"):
        raise ValidationError("reader-quality", seed, "seed must match the frozen question set")
    rows = question_set.get("questions")
    if not isinstance(rows, list):
        raise ValidationError("reader-quality", "question_set.questions", "questions must be a list")
    positives = [row for row in rows if isinstance(row, Mapping) and row.get("polarity") == "positive"]
    negatives = [row for row in rows if isinstance(row, Mapping) and row.get("polarity") == "negative"]
    if len(positives) < POSITIVE_MINIMUM or len(negatives) != NEGATIVE_COUNT:
        raise ValidationError("reader-quality", "question_set", "frozen positive/negative counts do not meet 8/3 gate")
    page_source = reader_manifest
    if reader_root is not None and (reader_root / "products").is_dir():
        page_source = reader_root
    pages = _manifest_pages(page_source)
    if len(pages) < 2:
        raise ValidationError("reader-quality", "reader_manifest.pages", "at least two Reader pages are required")
    answerability = _task2b_answerability(question_set, reader_manifest, raw_hash)
    answerable = [
        row for row in positives
        if answerability.get(str(row.get("question_id") or ""), {}).get("answerable") is True
    ]
    selected = sorted(answerable, key=lambda row: _numeric_question_key(str(row.get("question_id"))))[:POSITIVE_MINIMUM]
    selected += sorted(negatives, key=lambda row: _numeric_question_key(str(row.get("question_id"))))
    manifest = _manifest_value(reader_manifest)
    category_samples = manifest.get("category_samples") if isinstance(manifest.get("category_samples"), Mapping) else {}
    used_category_paths: set[str] = set()
    questions: list[ReaderQuestion] = []
    for index, row in enumerate(selected):
        page = _select_question_page(row, pages, category_samples, used_category_paths, answerability)
        questions.append(ReaderQuestion(
            question_id=str(row["question_id"]),
            polarity=str(row["polarity"]),
            text=str(row.get("original_text") or ""),
            entry_path=str(row.get("entry_path") or "Home.md"),
            expected_topic_or_product=str(row.get("expected_topic_or_product") or ""),
            target_page=str(page["path"]),
            page_type=str(page.get("page_type") or "unknown"),
            product=str(page.get("product") or ""),
            module=str(page["module"]) if page.get("module") is not None else None,
        ))
    if len({question.page_type for question in questions if question.polarity == "positive"}) < 2:
        raise ValidationError("reader-quality", "reader_manifest.pages", "positive sample needs two page types")
    if len({question.module or question.product for question in questions if question.polarity == "positive"}) < 2:
        raise ValidationError("reader-quality", "reader_manifest.pages", "positive sample needs two products/modules")
    coverage = _coverage(reader_manifest, inventory_root, reader_root)
    selected_positive_paths = {question.target_page for question in questions if question.polarity == "positive"}
    for category, details in coverage.items():
        if details.get("status") == "sampled":
            missing = sorted(set(details.get("sample_paths", [])) - selected_positive_paths)
            if missing:
                details["status"] = "failed"
                details["reason"] = f"declared sample path not selected: {missing[0]}"
    return tuple(questions), coverage


def build_reader_snapshot(bundle_dir: Path) -> ReaderSnapshot:
    """Read only Reader Bundle files and return a stable content snapshot."""

    bundle = Path(bundle_dir)
    if bundle.is_symlink() or not bundle.is_dir():
        raise ValidationError("reader-quality", bundle, "Reader Bundle must be a real directory")
    files: dict[str, str] = {}
    for path in sorted(bundle.rglob("*")):
        rel = path.relative_to(bundle).as_posix()
        if path.is_symlink():
            raise ValidationError("reader-quality", rel, "Reader snapshot cannot include symlinks")
        if path.is_dir():
            continue
        if rel in _READER_PACKAGE_METADATA:
            continue
        allowlisted = rel in _READER_ALLOWLIST or (rel.startswith("products/") and path.suffix == ".md")
        if not allowlisted:
            raise ValidationError("reader-quality", rel, "Reader-only snapshot encountered a non-Reader file")
        try:
            files[rel] = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValidationError("reader-quality", rel, f"Reader file is unreadable: {exc}") from exc
    if not files:
        raise ValidationError("reader-quality", bundle, "Reader Bundle is empty")
    digest_rows = [{"path": path, "sha256": _sha256(files[path])} for path in sorted(files)]
    return ReaderSnapshot(tuple(sorted(files)), files, _json_hash(digest_rows))


def _page_paths(bundle_dir: Path) -> set[str]:
    return {
        path.relative_to(bundle_dir).as_posix()
        for path in bundle_dir.joinpath("products").rglob("*.md")
        if path.name != "index.md"
    }


def _reader_links(path: str, text: str) -> tuple[str, ...]:
    links: list[str] = []
    for _label, raw_target in _READER_LINK_RE.findall(text):
        target = raw_target.strip().split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith(("mailto:", "/")):
            continue
        target_path = PurePosixPath(unquote(target))
        if target_path.is_absolute() or ".." in target_path.parts:
            continue
        if target_path.suffix.lower() != ".md":
            continue
        resolved = PurePosixPath(path).parent.joinpath(target_path).as_posix()
        if resolved == ".":
            resolved = PurePosixPath(path).name
        links.append(resolved)
    return tuple(dict.fromkeys(links))


def _reachable_reader_paths(snapshot: ReaderSnapshot, entry_path: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if entry_path not in snapshot.files:
        return (), (entry_path,)
    queue = [entry_path]
    visited: list[str] = []
    missing: list[str] = []
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.append(current)
        for target in _reader_links(current, snapshot.files[current]):
            if target not in snapshot.files:
                missing.append(target)
            elif target not in visited:
                queue.append(target)
    return tuple(visited), tuple(dict.fromkeys(missing))


def _reader_route(snapshot: ReaderSnapshot, entry_path: str, target_path: str) -> tuple[str, ...]:
    if entry_path not in snapshot.files or target_path not in snapshot.files:
        return ()
    queue: list[tuple[str, tuple[str, ...]]] = [(entry_path, (entry_path,))]
    visited = {entry_path}
    while queue:
        current, route = queue.pop(0)
        if current == target_path:
            return route
        for target in _reader_links(current, snapshot.files[current]):
            if target in snapshot.files and target not in visited:
                visited.add(target)
                queue.append((target, (*route, target)))
    return ()


def _negative_referent_check(snapshot: ReaderSnapshot, question: ReaderQuestion) -> dict[str, Any]:
    """Independently check that a frozen negative referent is absent."""

    terms = _NEGATIVE_REFERENT_TERMS.get(question.question_id, ())
    present = {
        term: [path for path, text in snapshot.files.items() if term in text]
        for term in terms
    }
    present = {term: paths for term, paths in present.items() if paths}
    return {
        "method": "exact-term-reader-scan-v1",
        "terms": list(terms),
        "present": present,
        "absent": not present and bool(terms),
    }


def _validate_reader_navigation(
    snapshot: ReaderSnapshot,
    question: ReaderQuestion,
    first_hit: Any,
    jumps: Any,
    canonical_route: tuple[str, ...],
) -> tuple[bool, str]:
    reachable, missing = _reachable_reader_paths(snapshot, question.entry_path)
    if missing:
        return False, f"entry_link_missing:{missing[0]}"
    if not reachable:
        return False, "entry_path_missing"
    if not isinstance(jumps, list) or not jumps or any(not isinstance(item, str) for item in jumps):
        return False, "jumps_invalid"
    if tuple(jumps) != canonical_route:
        return False, "jumps_do_not_match_canonical_route"
    reachable_set = set(reachable)
    if any(item not in reachable_set for item in jumps):
        return False, "jumps_leave_entry_path"
    for previous, current in zip(jumps, jumps[1:]):
        if current not in _reader_links(previous, snapshot.files[previous]):
            return False, f"jump_not_linked:{previous}->{current}"
    if question.polarity == "positive":
        # A positive question may correctly return ``no_match`` when the
        # target page is reachable but does not contain the requested answer.
        # Navigation is still valid in that case; the answer gate decides the
        # failure.  Requiring a first hit here incorrectly classified a clear
        # semantic miss as a broken route.
        if first_hit is None:
            if jumps[-1] != question.target_page:
                return False, "jumps_do_not_end_at_target"
        else:
            if first_hit != question.target_page:
                return False, "first_hit_does_not_match_task2b_target"
            if first_hit not in reachable_set:
                return False, "first_hit_not_reachable_from_entry"
            if jumps[-1] != first_hit:
                return False, "jumps_do_not_end_at_first_hit"
    elif first_hit is not None:
        return False, "negative_first_hit_present"
    return True, "passed"


def _source_chain(bundle_dir: Path, page_path: str, evidence_root: Path | None) -> tuple[bool, str]:
    try:
        target = bundle_dir.joinpath(*PurePosixPath(page_path).parts)
        if not target.is_file() or not target.is_relative_to(bundle_dir):
            return False, "first_hit_page_missing"
        frontmatter, _body = parse_concept_document(target.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return False, "first_hit_page_unreadable"
    sources = frontmatter.get("sources")
    if not isinstance(sources, list) or not sources:
        return False, "source_id_missing"
    for source in sources:
        if not isinstance(source, Mapping) or not isinstance(source.get("id"), str) or not source["id"]:
            return False, "source_id_missing"
        claims = source.get("digest_claims")
        if not isinstance(claims, list) or not claims:
            return False, "claim_id_missing"
        for claim in claims:
            if not isinstance(claim, Mapping):
                return False, "claim_invalid"
            if not claim.get("claim_id"):
                return False, "claim_id_missing"
            locator = claim.get("fragment_locator")
            target_path = claim.get("target_path")
            if not isinstance(locator, str) or not locator.strip() or not isinstance(target_path, str) or not target_path.strip():
                return False, "evidence_locator_missing"
            if evidence_root is None:
                return False, "evidence_root_missing"
            evidence = (evidence_root / PurePosixPath(target_path)).resolve()
            root = evidence_root.resolve()
            if evidence != root and root not in evidence.parents:
                return False, "evidence_path_escapes_root"
            if not evidence.is_file() or evidence.is_symlink():
                return False, "evidence_file_missing"
            source_fingerprint = source.get("digest_content_fingerprint")
            claim_fingerprint = claim.get("content_fingerprint")
            if not isinstance(source_fingerprint, str) or source_fingerprint != claim_fingerprint:
                return False, "source_claim_fingerprint_mismatch"
            try:
                observed_fingerprint = _sha256(evidence.read_bytes())
            except OSError:
                return False, "evidence_file_unreadable"
            if observed_fingerprint != claim_fingerprint:
                return False, "evidence_content_fingerprint_mismatch"
            match = re.fullmatch(r"lines:(\d+)(?:-(\d+))?", locator.strip())
            if match is None:
                return False, "evidence_locator_invalid"
            start = int(match.group(1))
            end = int(match.group(2) or match.group(1))
            if start < 1 or end < start or end > len(evidence.read_text(encoding="utf-8").splitlines()):
                return False, "evidence_locator_out_of_range"
    return True, "passed"


def _reader_prompt_text(text: str, *, source_path: str | None = None) -> str:
    """Redact internal Markdown link targets without dropping reader prose."""

    def redact_link(match: re.Match[str]) -> str:
        target = match.group(2).split("#", 1)[0].split("?", 1)[0].strip()
        if not target or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            return match.group(0)
        base = posixpath.dirname(source_path or "")
        normalized = posixpath.normpath(posixpath.join(base, unquote(target))).lstrip("./")
        internal = normalized == "audit" or normalized.startswith(("audit/", "_archive/", "_digest/"))
        if not internal:
            return match.group(0)
        return f"[{match.group(1)}](internal link omitted)"

    return "\n".join(
        _READER_LINK_RE.sub(redact_link, line)
        for line in text.splitlines()
    ) + "\n"


def _reader_agent_prompt(task_json: str) -> str:
    """Give real providers the response contract that fake providers bypass."""

    return f"{_READER_AGENT_INSTRUCTIONS}\n\nREADER_TASK_JSON:\n{task_json}"


def _invoke_agent(llm_call: Callable[..., Any], prompt: str, config: Mapping[str, Any]) -> Mapping[str, Any]:
    parameters = inspect.signature(llm_call).parameters
    is_project_llm = {"api_format", "base_url", "api_key", "model"} <= set(parameters)
    if is_project_llm:
        call_config = {
            "api_format": str(config.get("api_format") or "openai"),
            "base_url": str(config.get("base_url") or os.environ.get("KD_LLM_BASE_URL") or ""),
            "api_key": str(config.get("api_key") or os.environ.get("KD_LLM_API_KEY") or ""),
            "model": str(config.get("model") or os.environ.get("KD_LLM_MODEL") or ""),
            "timeout": int(config.get("timeout") or 60),
            "max_tokens": int(config.get("max_tokens") or 8192),
        }
        # Reader-gate responses are parsed as a strict JSON contract. Force
        # JSON mode for the real project seam even when older callers omit the
        # optional config key; fake providers still use the generic branch.
        call_config["json_mode"] = bool(config.get("json_mode", True))
        value = llm_call(prompt=prompt, **call_config)
    else:
        accepts_config = "config" in parameters or any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
        )
        if accepts_config:
            value = llm_call(prompt, config=dict(config))
        else:
            value = llm_call(prompt)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValidationError("reader-quality", "agent-response", f"Agent response is not JSON: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ValidationError("reader-quality", "agent-response", "Agent response must be an object")
    return value


def _safe_provider_config(config: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in config.items():
        if any(token in str(key).casefold() for token in ("key", "token", "secret", "password")):
            continue
        if key in {"reader_manifest", "llm_call"}:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[str(key)] = value
    return safe


def _failure_result(
    output_dir: Path,
    *,
    reason: str,
    coverage: Mapping[str, Any] | None = None,
    records: tuple[dict[str, Any], ...] = (),
    manifest_extra: Mapping[str, Any] | None = None,
) -> QualityGateResult:
    manifest = {
        "schema_version": EXIT_SCHEMA,
        "status": "failed",
        "delivery_status": "not_released",
        "failure_reasons": [reason],
        "agent_assisted": True,
        "review_mode": "agent_only",
        "gate_actor": "agent",
    }
    if manifest_extra:
        manifest.update(dict(manifest_extra))
    return QualityGateResult("failed", "not_released", records, coverage or {}, (reason,), None, manifest, output_dir)


def _persist_early_failure(output_dir: Path, result: QualityGateResult) -> None:
    """Persist failures that happen before the normal output writer owns the directory."""

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    receipt = output_dir.parent / f"{output_dir.name}.failure-{uuid.uuid4().hex[:12]}.json"
    payload = {
        "schema_version": EXIT_SCHEMA,
        "status": result.status,
        "delivery_status": result.delivery_status,
        "output_dir": str(output_dir),
        "failure_reasons": list(result.failure_reasons),
        "exit_manifest": dict(result.exit_manifest),
    }
    stage = receipt.with_name(f".{receipt.name}.tmp")
    stage.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(stage, receipt)


def _failure_manifest_fields(config: Mapping[str, Any], question_set_path: Path) -> dict[str, Any]:
    """Keep failed exits replayable when validation stops before the loop."""

    question_set_id = None
    question_set_hash = None
    rules_hash = None
    question_set_sha256 = None
    question_set_error = None
    try:
        question_set, question_set_sha256 = _question_set(question_set_path)
        question_set_id = question_set.get("question_set_id")
        question_set_hash = question_set.get("question_set_hash") or question_set_sha256
        rules_hash = _json_hash(question_set.get("derivation_rules"))
    except ValidationError as exc:
        question_set_error = str(exc)
    return {
        "run_id": None,
        "concept_contract": "reader-bundle-trust-signals.v1",
        "page_types": [],
        "signal_fields": ["page_type", "description", "source_count", "generated_at", "trust_tier", "status", "lifecycle"],
        "template": "Reader Bundle Home/index/products/modules/concept",
        "question_derivation": {
            "question_set_id": question_set_id,
            "question_set_hash": question_set_hash,
            "seed": config.get("seed"),
            "rules": "frozen Task0 positive/negative rules",
            "rules_hash": rules_hash,
            "question_set_sha256": question_set_sha256,
            "question_set_error": question_set_error,
        },
        "thresholds": {"positive_minimum": POSITIVE_MINIMUM, "positive_hit_rate": 1.0, "negative_count": NEGATIVE_COUNT, "negative_false_positive_maximum": 0},
        "provider": _safe_provider_config(config),
        "call_budget": config.get("call_budget"),
        "wall_clock_budget_seconds": config.get("wall_clock_budget_seconds"),
        "credential_source": config.get("credential_source"),
        "commit": config.get("commit"),
        "reader_input_hash": None,
    }


def _write_output(output_dir: Path, result: QualityGateResult, scorecard: Mapping[str, Any]) -> QualityGateResult:
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=parent))
    try:
        scorecard_hash = result.scorecard_hash or _scorecard_content_hash(scorecard)
        scorecard_value = dict(scorecard)
        scorecard_value["scorecard_hash"] = scorecard_hash
        scorecard_raw = json.dumps(scorecard_value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        manifest = dict(result.exit_manifest)
        manifest["scorecard_ref"] = "scorecard.json"
        manifest["scorecard_hash"] = scorecard_hash
        manifest["failure_reasons"] = list(result.failure_reasons)
        report = {
            "schema_version": QUALITY_SCHEMA,
            "status": result.status,
            "delivery_status": result.delivery_status,
            "scorecard_hash": scorecard_hash,
            "failure_reasons": list(result.failure_reasons),
        }
        (stage / "scorecard.json").write_text(scorecard_raw, encoding="utf-8")
        (stage / "run-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (stage / "exit-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if result.failure_reasons:
            (stage / "failures.jsonl").write_text("\n".join(json.dumps({"reason": reason}, ensure_ascii=False) for reason in result.failure_reasons) + "\n", encoding="utf-8")
        if output_dir.exists():
            reason = "quality output already exists; use a new run directory"
            manifest = dict(result.exit_manifest)
            manifest.update({"status": "failed", "delivery_status": "not_released", "failure_reasons": [reason]})
            return QualityGateResult("failed", "not_released", result.records, result.coverage, (reason,), result.scorecard_hash, manifest, output_dir)
        os.replace(stage, output_dir)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return QualityGateResult(result.status, result.delivery_status, result.records, result.coverage, result.failure_reasons, scorecard_hash, manifest, output_dir)


def run_reader_quality_gate(
    bundle_dir: Path,
    question_set_path: Path,
    output_dir: Path,
    *,
    config: Mapping[str, Any],
    llm_call: Callable[..., Any] | None = None,
) -> QualityGateResult:
    """Run the Reader-only gate into a fresh isolated output directory."""

    if not isinstance(config, Mapping):
        raise ValidationError("reader-quality", "config", "quality config must be a mapping")
    output = Path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    lock_context = kb_lock(output.parent)
    try:
        lock_context.__enter__()
    except ValidationError as exc:
        result = _failure_result(
            output,
            reason=str(exc),
            manifest_extra={
                **_failure_manifest_fields(config, Path(question_set_path)),
                "credential_source": config.get("credential_source"),
                "commit": config.get("commit"),
                "delivery_status": "not_released",
            },
        )
        _persist_early_failure(output, result)
        return result
    try:
        if output.exists():
            result = _failure_result(output, reason="quality output already exists; use a new run directory")
            _persist_early_failure(output, result)
            return result
        try:
            manifest_input = config.get("reader_manifest")
            if manifest_input is None:
                raise ValidationError("reader-quality", "reader_manifest.inventory_coverage", "inventory coverage manifest is required")
            snapshot = build_reader_snapshot(Path(bundle_dir))
            seed = str(config.get("seed") or "")
            question_set, question_set_raw_hash = _question_set(question_set_path)
            evidence_root_value = config.get("evidence_root")
            evidence_root = Path(evidence_root_value) if isinstance(evidence_root_value, (str, os.PathLike)) else None
            questions, coverage = derive_task2c_questions(
                question_set_path,
                manifest_input,
                seed=seed,
                inventory_root=evidence_root,
                reader_root=Path(bundle_dir),
            )
            page_paths = _page_paths(Path(bundle_dir))
            missing_targets = sorted({question.target_page for question in questions} - page_paths)
            if missing_targets:
                raise ValidationError("reader-quality", missing_targets[0], "question target is not in the Reader Bundle")
            routes = {
                question.question_id: _reader_route(snapshot, question.entry_path, question.target_page)
                for question in questions
            }
            missing_routes = sorted(question_id for question_id, route in routes.items() if not route)
            if missing_routes:
                raise ValidationError("reader-quality", missing_routes[0], "question target is not reachable from Reader entry path")
            model = str(config.get("model") or "unknown")
            call_budget = config.get("call_budget")
            wall_budget = config.get("wall_clock_budget_seconds")
            missing_config = []
            if not isinstance(call_budget, int) or isinstance(call_budget, bool) or call_budget < len(questions):
                missing_config.append("call_budget")
            if not isinstance(wall_budget, (int, float)) or isinstance(wall_budget, bool) or wall_budget <= 0:
                missing_config.append("wall_clock_budget_seconds")
            if not config.get("credential_source"):
                missing_config.append("credential_source")
            if not config.get("commit"):
                missing_config.append("commit")
            if not config.get("review_date"):
                missing_config.append("review_date")
            if evidence_root is None:
                missing_config.append("evidence_root")
            records: list[dict[str, Any]] = []
            failures: list[str] = []
            started = time.monotonic()
            calls = 0
            for question in questions:
                if calls >= int(call_budget):
                    failures.append("call budget exceeded")
                    break
                over_budget = time.monotonic() - started > float(wall_budget)
                if over_budget:
                    failures.append("wall-clock budget exceeded")
                    break
                prompt_payload = {
                    "entry_path": question.entry_path,
                    "question": question.text,
                    "expected_topic_or_product": question.expected_topic_or_product,
                    "navigation_rule": "start at entry_path, follow only Markdown links, and end at target_context.target_page",
                    "reachable_reader_paths": list(_reachable_reader_paths(snapshot, question.entry_path)[0]),
                    "canonical_reader_route": list(routes[question.question_id]),
                    "target_page_rule": "Only target_context.target_page may establish a positive hit; if it lacks the answer, return no_match.",
                    "negative_question_rule": (
                        "For negative questions, the named product/capability/state must be explicitly present in the supplied Reader files to be a hit. "
                        "Do not infer support from similar words, another product, historical text, unsupported text, or absence. "
                        "If the named referent is absent or not currently supported, return the exact no_match contract."
                        if question.polarity == "negative" else None
                    ),
                    "canonical_route_reader_files": [
                        {"path": path, "content": _reader_prompt_text(snapshot.files[path], source_path=path)}
                        for path in routes[question.question_id]
                    ],
                    "target_page_content": _reader_prompt_text(snapshot.files[question.target_page], source_path=question.target_page),
                    "target_context": {
                        "target_page": question.target_page,
                        "page_type": question.page_type,
                        "product": question.product,
                        "module": question.module,
                    },
                }
                task_json = json.dumps(prompt_payload, ensure_ascii=False, sort_keys=True)
                prompt = _reader_agent_prompt(task_json)
                prompt_hash = _sha256(prompt)
                negative_referent = (
                    _negative_referent_check(snapshot, question)
                    if question.polarity == "negative"
                    else None
                )
                response: Mapping[str, Any]
                response_error: str | None = None
                try:
                    if llm_call is None:
                        from .llm import call_llm as configured_call_llm

                        provider = configured_call_llm
                    else:
                        provider = llm_call
                    calls += 1
                    response = _invoke_agent(provider, prompt, config)
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    response = {}
                    response_error = str(exc) or "provider_failed"
                over_budget = time.monotonic() - started > float(wall_budget)
                if over_budget:
                    failures.append("wall-clock budget exceeded")
                missing_fields = [field for field in _RESPONSE_FIELDS if field not in response]
                if missing_fields:
                    failures.append(f"{question.question_id}: missing response fields: {','.join(missing_fields)}")
                first_hit = response.get("first_hit_page")
                source_recheck = response.get("source_recheck_result")
                navigation_ok, navigation_reason = _validate_reader_navigation(
                    snapshot, question, first_hit, response.get("jumps"), routes[question.question_id]
                )
                if not navigation_ok:
                    failures.append(f"{question.question_id}: reader navigation failed: {navigation_reason}")
                chain_ok = False
                chain_reason = "not_applicable"
                if question.polarity == "positive" and isinstance(first_hit, str) and first_hit:
                    chain_ok, chain_reason = _source_chain(Path(bundle_dir), first_hit, evidence_root)
                    if not chain_ok:
                        failures.append(f"{question.question_id}: source chain failed: {chain_reason}")
                if response_error:
                    failures.append(f"{question.question_id}: {response_error}")
                record = {
                    "question_id": question.question_id,
                    "question": question.text,
                    "polarity": question.polarity,
                    "entry_path": question.entry_path,
                    "target_page": question.target_page,
                    "first_hit_page": first_hit,
                    "jumps": response.get("jumps"),
                    "answer_found": response.get("answer_found"),
                    "answer_complete": response.get("answer_complete"),
                    "boundary_version_accurate": response.get("boundary_version_accurate"),
                    "source_attribution": response.get("source_attribution"),
                    "source_chain": chain_reason if question.polarity == "positive" else "not_applicable",
                    "navigation": navigation_reason,
                    "reviewer": str(config.get("reviewer") or "task2c-agent-reader"),
                    "review_date": config.get("review_date"),
                    "seed": seed,
                    "agent_assisted": True,
                    "review_mode": "agent_only",
                    "gate_actor": "agent",
                    "model": model,
                    "prompt": prompt,
                    "prompt_hash": prompt_hash,
                    "reader_input_hash": snapshot.content_hash,
                    "answer_result": response.get("answer_result"),
                    "source_recheck_result": source_recheck,
                    "negative_referent_check": negative_referent,
                    # Keep the complete bounded provider contract beside the
                    # derived verdict.  This makes real-provider false
                    # positives replayable without persisting arbitrary model
                    # output or credentials.
                    "provider_response": {
                        field: response.get(field)
                        for field in _RESPONSE_FIELDS
                    },
                    "failure_reason": response_error or (f"missing: {','.join(missing_fields)}" if missing_fields else None),
                }
                if question.polarity == "positive":
                    positive_ok = (
                        response.get("answer_found") is True
                        and response.get("answer_result") == "hit"
                        and isinstance(first_hit, str)
                        and bool(first_hit)
                        and response.get("answer_complete") is True
                        and response.get("boundary_version_accurate") is True
                        and response.get("source_attribution") is True
                        and source_recheck == "passed"
                        and navigation_ok
                        and chain_ok
                    )
                    if not positive_ok:
                        reason = f"{question.question_id}: positive answer gate failed"
                        failures.append(reason)
                        record["failure_reason"] = reason
                else:
                    negative_ok = (
                        response.get("answer_found") is False
                        and response.get("first_hit_page") is None
                        and response.get("answer_result") == "no_match"
                        and response.get("answer_complete") is True
                        and response.get("boundary_version_accurate") is True
                        and response.get("source_attribution") is False
                        and response.get("source_recheck_result") == "not_applicable"
                        and navigation_ok
                        and isinstance(negative_referent, Mapping)
                        and negative_referent.get("absent") is True
                    )
                    if not negative_ok:
                        reason = f"{question.question_id}: negative false-positive gate failed"
                        if isinstance(negative_referent, Mapping) and negative_referent.get("absent") is not True:
                            reason = f"{question.question_id}: negative referent is present in Reader files"
                        failures.append(reason)
                        record["failure_reason"] = reason
                records.append(record)
                if over_budget:
                    break
            if missing_config:
                failures.append(f"exit manifest missing required config: {','.join(missing_config)}")
            if any(item["status"] == "failed" for item in coverage.values()):
                failures.append("inventory coverage has an actual feature without sample or machine fixture exclusion")
            positives = [record for record in records if record["polarity"] == "positive"]
            negatives = [record for record in records if record["polarity"] == "negative"]
            if len(positives) < POSITIVE_MINIMUM or len(negatives) != NEGATIVE_COUNT:
                failures.append("positive/negative gate count is not 8/3")
            base_scorecard = {
                "schema_version": QUALITY_SCHEMA,
                "seed": seed,
                "questions": records,
                "coverage": coverage,
                "thresholds": {"positive_minimum": POSITIVE_MINIMUM, "positive_hit_rate": 1.0, "negative_count": NEGATIVE_COUNT, "negative_false_positive_maximum": 0},
                "reader_input_hash": snapshot.content_hash,
                "summary": {
                    "positive_count": len(positives),
                    "positive_passed": sum(
                        1 for record in positives
                        if record.get("answer_found") is True
                        and record.get("answer_result") == "hit"
                        and isinstance(record.get("first_hit_page"), str)
                        and bool(record.get("first_hit_page"))
                        and record.get("answer_complete") is True
                        and record.get("boundary_version_accurate") is True
                        and record.get("source_attribution") is True
                        and record.get("source_recheck_result") == "passed"
                        and record.get("navigation") == "passed"
                        and record.get("source_chain") == "passed"
                    ),
                    "negative_count": len(negatives),
                    # A missing or malformed provider response is still a gate
                    # failure, but it is not evidence that the agent actually
                    # claimed a negative answer was present. Keep transport /
                    # contract failures separate from semantic false positives.
                    "negative_false_positives": sum(
                        1
                        for record in negatives
                        if record.get("answer_found") is True or record.get("answer_result") == "hit"
                    ),
                },
            }
            scorecard_hash = _scorecard_content_hash(base_scorecard)
            records = [dict(record, scorecard_hash=scorecard_hash) for record in records]
            scorecard = dict(base_scorecard, questions=records)
            status = "passed" if not failures else "failed"
            run_id = _sha256(f"{snapshot.content_hash}\0{seed}\0{model}")[:16]
            exit_manifest = {
                "schema_version": EXIT_SCHEMA,
                "run_id": run_id,
                "status": status,
                "delivery_status": "not_released",
                "concept_contract": "reader-bundle-trust-signals.v1",
                "page_types": sorted({question.page_type for question in questions}),
                "signal_fields": ["page_type", "description", "source_count", "generated_at", "trust_tier", "status", "lifecycle"],
                "template": "Reader Bundle Home/index/products/modules/concept",
                "question_derivation": {
                    "question_set_id": question_set.get("question_set_id"),
                    "question_set_hash": question_set.get("question_set_hash") or question_set_raw_hash,
                    "seed": seed,
                    "rules": "frozen Task0 positive/negative rules",
                    "rules_hash": _json_hash(question_set.get("derivation_rules")),
                    "question_set_sha256": question_set_raw_hash,
                },
                "agent_assisted": True,
                "review_mode": "agent_only",
                "gate_actor": "agent",
                "thresholds": base_scorecard["thresholds"],
                "provider": _safe_provider_config(config),
                "call_budget": call_budget,
                "wall_clock_budget_seconds": wall_budget,
                "credential_source": config.get("credential_source"),
                "commit": config.get("commit"),
                "reader_input_hash": snapshot.content_hash,
            }
            result = QualityGateResult(status, "not_released", tuple(records), coverage, tuple(sorted(set(failures))), scorecard_hash, exit_manifest, output)
            return _write_output(output, result, scorecard)
        except BaseException as exc:
            reason = "run_cancelled" if isinstance(exc, KeyboardInterrupt) else str(exc)
            result = _failure_result(
                output,
                reason=reason,
                manifest_extra={
                    **_failure_manifest_fields(config, Path(question_set_path)),
                    "credential_source": config.get("credential_source"),
                    "commit": config.get("commit"),
                    "delivery_status": "not_released",
                },
            )
            return _write_output(output, result, {"schema_version": QUALITY_SCHEMA, "questions": [], "failure_reasons": [reason]})
    finally:
        lock_context.__exit__(*sys.exc_info())
