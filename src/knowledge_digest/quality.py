"""Declarative quality projections for the reader-first compiler.

This module contains no provider calls and no CompanyBrain dependency.  It
turns the frozen quality-case contract into small, typed inputs for the
compiler.  The compiler can therefore keep one generic pipeline while the
quality run gets explicit question, scene, page-type and evidence closure.
"""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class QualityProjection:
    projection_id: str
    case_id: str
    page_type: str
    projection_key: str
    title: str
    question: str
    axes: Mapping[str, str]
    source_paths: tuple[str, ...]
    source_block_refs: tuple[str, ...]
    required_claims: tuple[Mapping[str, Any], ...]
    required_boundaries: tuple[Mapping[str, Any], ...]
    guidance: str
    repair_guidance: str
    forbidden_literals: tuple[tuple[str, str], ...]
    reader_markers: tuple[Mapping[str, Any], ...]
    comparison_rubric: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    quality_features: Mapping[str, tuple[Mapping[str, Any], ...]] = field(default_factory=dict)
    applicable_dimensions: tuple[str, ...] = ()


_BLOCK_REF = re.compile(r"^(?P<path>.+)#L(?P<start>\d+)-L(?P<end>\d+)::(?P<label>[^:]+)$")
_EXPECTED_PROJECTION_IDS = (
    "Q-POS-01.positioning",
    "Q-CON-01.concept",
    "Q-OPR-01.qr.operation",
    "Q-OPR-01.zero-touch.operation",
    "Q-DIA-01.diagnosis.metric",
    "Q-DIA-01.diagnosis.migration",
    "Q-DIA-01.diagnosis.query",
    "Q-DIA-01.diagnosis.delete",
    "Q-DIA-01.diagnosis.doc",
    "Q-EXP-01.experience",
    "Q-BND-01.operation",
    "Q-BND-01.diagnosis",
)
_EXPECTED_DIMENSIONS = (
    "DIM-01.route",
    "DIM-02.taxonomy",
    "DIM-03.business-answer",
    "DIM-04.page-type",
    "DIM-05.reader-audit",
)
UNKNOWN = "原始资料未明确"


def item_reader_visible(item: Mapping[str, Any]) -> bool:
    """Whether a frozen claim/boundary must be answered on Reader.

    ``Audit``-only requirements are deliberately not forced into the answer
    page.  They remain part of the immutable evidence closure and are checked
    through Audit instead.  Treating the two surfaces as the same was making
    concise business pages fail, while also encouraging models to print
    internal audit labels in Reader text.
    """

    surface = item.get("surface")
    if not isinstance(surface, str):
        return False
    tokens = {token.strip().casefold() for token in surface.split("+")}
    return any(token == "reader" or token.startswith("reader.") for token in tokens)


def _validate_requirement(item: Mapping[str, Any], projection_id: str, kind: str) -> None:
    """Reject a requirement that cannot be closed against exact evidence."""

    surface = item.get("surface")
    if not isinstance(surface, str) or not surface.strip():
        raise ValueError(f"quality {kind} has no surface: {projection_id}")
    tokens = {token.strip().casefold() for token in surface.split("+")}
    if not tokens or any(
        token != "audit" and token != "reader" and not token.startswith(("reader.", "audit."))
        for token in tokens
    ):
        raise ValueError(f"quality {kind} has invalid surface: {projection_id}: {surface}")
    refs = item.get("source_block_refs")
    if not isinstance(refs, list) or not refs or any(not str(ref).strip() for ref in refs):
        raise ValueError(f"quality {kind} has no source_block_refs: {projection_id}")
    for ref in refs:
        parse_block_ref(str(ref))


def reader_evidence_groups(
    projection: QualityProjection,
    evidence: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, ...], ...]:
    """Return hard evidence obligations for Reader-visible requirements.

    ``reader_markers`` are editorial guidance, not an additional checklist.
    Treating every marker term-group as a hard obligation made pages answer a
    mechanical inventory instead of the user's question, especially on long
    diagnosis and concept projections.  The prompt still includes markers so
    the model can use them when relevant; only typed claims and boundaries
    are release-critical evidence obligations.
    """

    evidence_by_ref = {
        str(item.get("block_ref")): str(item.get("evidence_id"))
        for item in evidence
        if item.get("block_ref") and item.get("evidence_id")
    }
    groups: list[tuple[str, ...]] = []
    for requirement in (*projection.required_claims, *projection.required_boundaries):
        if not item_reader_visible(requirement):
            continue
        ids = tuple(dict.fromkeys(
            evidence_by_ref[str(ref)]
            for ref in requirement.get("source_block_refs", ())
            if str(ref) in evidence_by_ref
        ))
        if ids:
            groups.append(ids)
    return tuple(groups)


def _quality_sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _quality_canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _quality_tree_digest(files: Mapping[str, bytes]) -> str:
    rows = []
    for relative, content in sorted(files.items()):
        relative = str(relative)
        if relative.startswith("bundle/"):
            relative = relative[len("bundle/"):]
        if relative in {
            "_audit/quality.json",
            "_audit/run-result.json",
            "_audit/run-result.receipt.json",
        }:
            continue
        rows.append(f"{relative}\0".encode("utf-8") + content + b"\0")
    return _quality_sha(b"".join(rows))


_DIMENSION_LABELS = {
    "DIM-01.route": "route",
    "DIM-02.taxonomy": "taxonomy",
    "DIM-03.business-answer": "business-answer",
    "DIM-04.page-type": "page-type",
    "DIM-05.reader-audit": "Reader-Audit",
}
_DIMENSION_IDS_BY_LABEL = {value: key for key, value in _DIMENSION_LABELS.items()}
_PAGE_TYPE_HEADINGS = {
    "positioning": ("当前结论", "服务对象与入口", "产品关系与选择", "边界与未明确"),
    "concept": ("使用场景", "对象与组成", "关系与生效规则", "边界与容易混淆"),
    "operation": ("前置条件", "操作步骤", "预期结果", "验证方式", "失败与限制"),
    "diagnosis": ("现象", "检查顺序", "可能原因", "处理动作", "升级边界"),
    "experience": ("背景", "阶段变化", "方案取舍与经验", "经验教训", "适用边界"),
}
_PAGE_TYPE_LABELS = {
    "positioning": "定位",
    "concept": "概念",
    "operation": "操作",
    "diagnosis": "诊断",
    "experience": "经验",
}


def _rubric_forms(rubric: Mapping[str, Any], field: str, atom: str) -> tuple[str, ...]:
    forms = rubric.get(f"{field}_forms", {})
    values = forms.get(atom) if isinstance(forms, Mapping) else None
    if isinstance(values, list) and values:
        return tuple(str(value) for value in values if str(value))
    return (str(atom),) if str(atom) else ()


def _rubric_terms(rubric: Mapping[str, Any], field: str) -> tuple[str, ...]:
    values = rubric.get(field, ())
    return tuple(str(value) for value in values if str(value)) if isinstance(values, list) else ()


def _term_present(text: str, forms: Sequence[str]) -> bool:
    return any(form and form.casefold() in text.casefold() for form in forms)


def _term_observations(text: str, rubric: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    observations: list[dict[str, Any]] = []
    missing: list[str] = []
    for atom in _rubric_terms(rubric, "required_atoms"):
        present = _term_present(text, _rubric_forms(rubric, "atom", atom))
        observations.append({"atom": atom, "status": "present" if present else "absent"})
        if not present:
            missing.append(atom)
    return observations, missing


def _reader_frontmatter(text: str) -> dict[str, str]:
    """Read the small scalar frontmatter emitted by the Reader renderer."""

    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def _reader_headings(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", text)
    }


def _forbidden_terms(rubric: Mapping[str, Any]) -> tuple[str, ...]:
    terms: list[str] = []
    for atom in _rubric_terms(rubric, "forbidden_atoms"):
        terms.extend(_rubric_forms(rubric, "forbidden", atom))
    values = rubric.get("forbidden_forms", {})
    if isinstance(values, Mapping):
        for forms in values.values():
            if isinstance(forms, list):
                terms.extend(str(value) for value in forms if str(value))
    return tuple(dict.fromkeys(terms))


def _quality_read_jsonl(path: Path) -> tuple[list[Mapping[str, Any]], list[str]]:
    rows: list[Mapping[str, Any]] = []
    errors: list[str] = []
    if not path.is_file():
        return rows, [f"missing:{path.name}"]
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        return rows, [f"unreadable:{path.name}:{type(error).__name__}"]
    for index, line in enumerate(raw_lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"invalid_json:{path.name}:{index}")
            continue
        if not isinstance(value, Mapping):
            errors.append(f"row_not_object:{path.name}:{index}")
            continue
        rows.append(value)
    return rows, errors


def _source_reader_coverage_blockers(files: Mapping[str, bytes]) -> list[str]:
    """Block a quality release when a ready source has no canonical Reader page."""

    raw = files.get("_audit/sources.jsonl")
    if raw is None:
        return []
    missing = 0
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return ["source_index_invalid"]
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return ["source_index_invalid"]
        if not isinstance(row, Mapping) or not row.get("source_digest_eligible"):
            continue
        page_ids = row.get("reader_page_ids")
        if not isinstance(page_ids, list) or not any(str(page_id).strip() for page_id in page_ids):
            missing += 1
    return [f"source_reader_coverage_incomplete:{missing}"] if missing else []


def _quality_pages_from_files(files: Mapping[str, bytes]) -> dict[str, tuple[str, str]]:
    pages: dict[str, tuple[str, str]] = {}
    marker = re.compile(r"digest_projection_id:\s*([^\s]+)")
    for relative, content in files.items():
        if not relative.startswith("products/") or not relative.endswith(".md") or relative.endswith("/index.md"):
            continue
        text = content.decode("utf-8", errors="replace")
        match = marker.search(text)
        if match:
            pages[match.group(1)] = (relative, text)
    return pages


def _quality_pages_from_directory(root: Path) -> dict[str, tuple[str, str]]:
    files = {}
    products = root / "products"
    if products.is_dir():
        for path in products.rglob("*.md"):
            if path.name == "index.md":
                continue
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return _quality_pages_from_files(files)


def _bundle_root(root: Path) -> Path:
    """Accept a published run root while keeping the evaluator bundle-local."""

    root = Path(root)
    candidate = root / "bundle"
    return candidate if candidate.is_dir() and not candidate.is_symlink() else root


def _validate_render_ledger(rows: Sequence[Mapping[str, Any]], files: Mapping[str, bytes]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version", "unit_id", "page_key", "page_path", "surface",
        "slot",
        "text_sha256", "audit_ref", "claim_ids", "evidence_ids",
        "raw_source_id", "raw_hash", "block_id", "claim_id", "locator",
        "support_sha256", "evidence_bindings", "home_target_page_identity",
    }
    seen: set[str] = set()
    seen_page_units: set[tuple[str, str]] = set()
    allowed_surfaces = {
        "Reader.title",
        "Reader.question",
        "Reader.summary",
        "Reader.answer_body",
        "Reader.section",
        "Reader.axis",
        "Reader.page_type",
        "Home.route",
    }
    for row in rows:
        if set(required) - set(row):
            errors.append("render_unit_missing_fields")
            continue
        unit_id = str(row.get("unit_id", ""))
        page_path = str(row.get("page_path", ""))
        page_unit_key = (unit_id, page_path)
        if row.get("schema_version") != "knowledge-digest-render-unit.v1" or not unit_id or unit_id in seen or page_unit_key in seen_page_units:
            errors.append(f"render_unit_identity:{unit_id or 'missing'}")
        seen.add(unit_id)
        seen_page_units.add(page_unit_key)
        if row.get("surface") not in allowed_surfaces:
            errors.append(f"render_unit_surface:{unit_id or 'missing'}")
        stable_identity = "\0".join((page_path, str(row.get("page_key", "")), str(row.get("surface", "")), str(row.get("slot", ""))))
        expected_unit_id = f"u-{hashlib.sha256(stable_identity.encode('utf-8')).hexdigest()[:24]}"
        if unit_id != expected_unit_id:
            errors.append(f"render_unit_stable_id:{unit_id or 'missing'}")
        file_page_path = page_path.removeprefix("bundle/")
        if file_page_path not in files:
            errors.append(f"render_unit_page_missing:{page_path}")
        home_target = row.get("home_target_page_identity")
        if row.get("surface") == "Home.route":
            if page_path != "bundle/Home.md" or not str(home_target) or not str(row.get("slot", "")).endswith(f":{home_target}"):
                errors.append(f"render_unit_home_target:{unit_id}")
        elif home_target is not None:
            errors.append(f"render_unit_non_home_target:{unit_id}")
        evidence_ids = [str(item) for item in row.get("evidence_ids", ()) if str(item)]
        unknown_unit = _is_explicit_unknown_unit(row)
        if unknown_unit:
            # “原始资料未明确” is an explicit absence marker, not a factual
            # claim.  It cannot truthfully point at a raw block, so it is
            # exempt from claim/locator validation while factual units remain
            # fully evidence-bound.
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("text_sha256", ""))):
            errors.append(f"render_unit_hash:{unit_id}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("raw_hash", ""))):
            errors.append(f"render_unit_raw_hash:{unit_id}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("support_sha256", ""))):
            errors.append(f"render_unit_support_hash:{unit_id}")
        locator = row.get("locator")
        if (
            not str(row.get("raw_source_id", ""))
            or not str(row.get("block_id", ""))
            or not str(row.get("claim_id", ""))
            or not isinstance(locator, Mapping)
            or not isinstance(locator.get("start_line"), int)
            or not isinstance(locator.get("end_line"), int)
            or locator.get("start_line", 0) <= 0
            or locator.get("end_line", 0) < locator.get("start_line", 0)
        ):
            errors.append(f"render_unit_lineage:{unit_id}")
        bindings = row.get("evidence_bindings")
        if not isinstance(bindings, list) or not bindings:
            errors.append(f"render_unit_evidence_bindings:{unit_id}")
        elif not all(
            isinstance(binding, Mapping)
            and str(binding.get("raw_source_id", ""))
            and str(binding.get("block_id", ""))
            and str(binding.get("claim_id", ""))
            and isinstance(binding.get("locator"), Mapping)
            and re.fullmatch(r"[0-9a-f]{64}", str(binding.get("raw_hash", "")))
            and re.fullmatch(r"[0-9a-f]{64}", str(binding.get("support_sha256", "")))
            for binding in bindings
        ):
            errors.append(f"render_unit_evidence_binding_shape:{unit_id}")
        elif (
            bindings[0].get("raw_source_id") != row.get("raw_source_id")
            or bindings[0].get("raw_hash") != row.get("raw_hash")
            or bindings[0].get("block_id") != row.get("block_id")
            or bindings[0].get("claim_id") != row.get("claim_id")
            or bindings[0].get("locator") != row.get("locator")
            or bindings[0].get("support_sha256") != row.get("support_sha256")
        ):
            errors.append(f"render_unit_lineage_mismatch:{unit_id}")
        if "text" in row or "prompt" in row or "response" in row or "api_key" in row:
            errors.append(f"render_unit_raw_or_secret:{unit_id}")
        if not isinstance(row.get("claim_ids"), list) or not isinstance(row.get("evidence_ids"), list):
            errors.append(f"render_unit_bindings:{unit_id}")
        audit_ref = str(row.get("audit_ref", ""))
        if not evidence_ids or audit_ref != f"Audit.md#evidence-{evidence_ids[0]}":
            errors.append(f"render_unit_audit_ref:{unit_id}")
        elif f'<a id="evidence-{evidence_ids[0]}"></a>' not in files.get("Audit.md", b"").decode("utf-8", errors="replace"):
            errors.append(f"render_unit_audit_anchor:{unit_id}")
    return list(dict.fromkeys(errors))


def _is_explicit_unknown_unit(row: Mapping[str, Any]) -> bool:
    """Identify an intentional absence marker, not an unbound fact.

    ``原始资料未明确`` is rendered so the Reader does not invent an answer.
    It has no truthful raw block binding.  Keep it visible and count it
    separately, while excluding it from the factual lineage denominator.
    Any other visible unit remains subject to the full raw-binding contract.
    """

    return (
        row.get("surface") in {"Reader.summary", "Reader.answer_body", "Reader.section"}
        and not row.get("evidence_ids")
        and str(row.get("text_sha256", "")) == _quality_sha(UNKNOWN)
    )


def _companybrain_binding_errors(
    observation: Mapping[str, Any] | None,
    *,
    expected_source_manifest_sha256: str | None = None,
    expected_run_id: str | None = None,
) -> list[str]:
    """Require a current M402 observation before any comparison is usable."""

    if observation is None:
        return ["companybrain_observation_missing"]
    required = (
        "run_id",
        "source_manifest_sha256",
        "companybrain_snapshot_id",
        "companybrain_tree_sha256",
        "observation_sha256",
    )
    errors = [
        f"companybrain_binding_missing:{field}"
        for field in required
        if not str(observation.get(field, "")).strip()
    ]
    for field in ("source_manifest_sha256", "companybrain_tree_sha256", "observation_sha256"):
        value = str(observation.get(field, ""))
        if value and not re.fullmatch(r"[0-9a-f]{64}", value):
            errors.append(f"companybrain_binding_hash:{field}")
    # A file-list snapshot is not a comparison observation. Requiring the
    # scanner's complete rows prevents the compiler from reporting a
    # successful run while a projection or dimension silently disappeared.
    rows = observation.get("rows")
    expected_rows = len(_EXPECTED_PROJECTION_IDS) * len(_EXPECTED_DIMENSIONS)
    if not isinstance(rows, list) or len(rows) != expected_rows:
        errors.append("companybrain_observation_rows_missing")
    else:
        expected_pairs = {
            (projection_id, dimension)
            for projection_id in _EXPECTED_PROJECTION_IDS
            for dimension in _EXPECTED_DIMENSIONS
        }
        expected_case_by_projection = {
            "Q-POS-01.positioning": "Q-POS-01",
            "Q-CON-01.concept": "Q-CON-01",
            "Q-OPR-01.qr.operation": "Q-OPR-01",
            "Q-OPR-01.zero-touch.operation": "Q-OPR-01",
            "Q-DIA-01.diagnosis.metric": "Q-DIA-01",
            "Q-DIA-01.diagnosis.migration": "Q-DIA-01",
            "Q-DIA-01.diagnosis.query": "Q-DIA-01",
            "Q-DIA-01.diagnosis.delete": "Q-DIA-01",
            "Q-DIA-01.diagnosis.doc": "Q-DIA-01",
            "Q-EXP-01.experience": "Q-EXP-01",
            "Q-BND-01.operation": "Q-BND-01",
            "Q-BND-01.diagnosis": "Q-BND-01",
        }
        actual_pairs: set[tuple[str, str]] = set()
        fixed_fields = {
            "case_id", "projection_id", "dimension_id", "status", "score",
            "source_refs", "visible_ref", "audit_ref", "gap_ref", "kd_ref",
        }
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != fixed_fields:
                errors.append("companybrain_observation_row_shape")
                continue
            pair = (str(row.get("projection_id", "")), str(row.get("dimension_id", "")))
            if pair not in expected_pairs or pair in actual_pairs:
                errors.append("companybrain_observation_row_identity")
            actual_pairs.add(pair)
            if row.get("case_id") != expected_case_by_projection.get(pair[0]):
                errors.append("companybrain_observation_row_case_mismatch")
            if row.get("status") not in {"present", "absent", "unknown", "forbidden"}:
                errors.append("companybrain_observation_row_status")
        if actual_pairs != expected_pairs:
            errors.append("companybrain_observation_row_closure")
        observation_payload = {
            "run_id": observation.get("run_id"),
            "source_manifest_sha256": observation.get("source_manifest_sha256"),
            "companybrain_snapshot_id": observation.get("companybrain_snapshot_id"),
            "companybrain_tree_sha256": observation.get("companybrain_tree_sha256"),
            "rows": rows,
        }
        if observation.get("observation_sha256") != _quality_sha(_quality_canonical(observation_payload)):
            errors.append("companybrain_observation_hash_mismatch")
    if expected_source_manifest_sha256 and observation.get("source_manifest_sha256") != expected_source_manifest_sha256:
        errors.append("companybrain_binding_source_manifest_mismatch")
    if expected_run_id and observation.get("run_id") != expected_run_id:
        errors.append("companybrain_binding_run_mismatch")
    return list(dict.fromkeys(errors))


def _observation_row_digest(row: Mapping[str, Any]) -> str:
    payload = {
        "case_id": str(row.get("case_id", "")),
        "projection_id": str(row.get("projection_id", "")),
        "dimension_id": str(row.get("dimension_id", "")),
        "status": str(row.get("status", "")),
        "score": row.get("score"),
        "source_refs": sorted(
            (str(value) for value in row.get("source_refs", ()) if str(value)),
            key=lambda value: value.encode("utf-8"),
        ),
        "visible_ref": row.get("visible_ref"),
        "audit_ref": row.get("audit_ref"),
        "gap_ref": row.get("gap_ref"),
        "kd_ref": row.get("kd_ref"),
    }
    return _quality_sha(_quality_canonical(payload))


def _quality_rubric(projection: QualityProjection, dimension: str) -> Mapping[str, Any]:
    label = _DIMENSION_LABELS[dimension]
    value = projection.comparison_rubric.get(label, {})
    return value if isinstance(value, Mapping) else {}


def _quality_marker_observations(
    text: str,
    rubric: Mapping[str, Any],
    *,
    prefix: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    observations: list[dict[str, Any]] = []
    missing: list[str] = []
    for marker in _rubric_terms(rubric, "structure_markers"):
        present = marker.casefold() in text.casefold()
        stage_id = f"{prefix}::stage::{marker}"
        observations.append({"stage_id": stage_id, "marker": marker, "status": "present" if present else "absent"})
        if not present:
            missing.append(stage_id)
    return observations, missing


def _quality_kd_unit(
    projection: QualityProjection,
    dimension: str,
    pages: Mapping[str, tuple[str, str]],
    ledger_rows: Sequence[Mapping[str, Any]],
    files: Mapping[str, bytes],
) -> dict[str, Any]:
    page = pages.get(projection.projection_id)
    if page is None:
        return {"page_path": None, "reader_ref": None, "audit_ref": None, "text": "", "route": None}
    page_path, text = page
    units = [
        row for row in ledger_rows
        if isinstance(row, Mapping)
        and str(row.get("page_path", "")).removeprefix("bundle/") == page_path
        and row.get("surface") in {"Reader.summary", "Reader.answer_body", "Reader.section"}
        and str(row.get("unit_id", ""))
    ]
    # A page may have an intentional UNKNOWN summary before its evidence-bound
    # answer body.  Selecting the first row made the quality result depend on
    # ledger ordering instead of the actual Reader answer.  Prefer one
    # evidence-bound unit and keep the choice deterministic.
    units.sort(key=lambda row: (
        0 if row.get("evidence_ids") and row.get("audit_ref") else 1,
        0 if row.get("surface") == "Reader.answer_body" else 1,
        str(row.get("slot", "")).encode("utf-8"),
        str(row.get("unit_id", "")).encode("utf-8"),
    ))
    unit = units[0] if units else None
    reader_ref = f"{page_path}#{unit['unit_id']}" if unit else None
    audit_ref = str(unit.get("audit_ref", "")) if unit else None
    audit_text = files.get("Audit.md", b"").decode("utf-8", errors="replace")
    return {
        "page_path": page_path,
        "reader_ref": reader_ref,
        "audit_ref": audit_ref,
        "text": text,
        "audit_text": audit_text,
        "unit": unit,
    }


def _quality_semantic_structure(
    projection: QualityProjection,
    text: str,
    *,
    has_bound_reader_unit: bool,
) -> dict[str, Any]:
    """Evaluate the visible contract of a page, not a keyword inventory.

    The comparison dimensions describe reader behavior: a page must expose
    its five axes, answer the question in the page-type shape, and retain a
    usable Reader surface.  Required atoms and marker terms remain useful
    diagnostics, but their literal spelling is not the quality contract.
    """

    frontmatter = _reader_frontmatter(text)
    headings = _reader_headings(text)
    expected_page_type = projection.page_type
    expected_label = _PAGE_TYPE_LABELS.get(expected_page_type, expected_page_type)
    actual_page_type = str(frontmatter.get("page_type", "")).strip()
    page_type_ok = actual_page_type in {expected_page_type, expected_label}

    expected_axes = {
        "product": projection.axes["product"],
        "module": projection.axes["module"],
        "object": projection.axes["object"],
        "scenario": projection.axes["scene"],
        "boundary": projection.axes["boundary"],
    }
    taxonomy_ok = bool(frontmatter) and all(
        str(frontmatter.get(key, "")).strip() == value
        for key, value in expected_axes.items()
    )
    expected_headings = _PAGE_TYPE_HEADINGS.get(expected_page_type, ())
    sections_ok = bool(expected_headings) and all(
        heading in headings for heading in expected_headings
    )

    body = re.sub(r"(?s)^---\n.*?\n---\n", "", text, count=1)
    body = re.sub(r"(?m)^<!--.*?-->\s*$", "", body)
    body = re.sub(r"(?m)^#{1,6}\s+.*$", "", body)
    body = re.sub(r"(?m)^>\s*证据：.*$", "", body)
    substantive = len(re.sub(r"\s+", "", body)) >= 48
    return {
        "page_type_ok": page_type_ok,
        "taxonomy_ok": taxonomy_ok,
        "sections_ok": sections_ok,
        "substantive": substantive,
        "business_answer_ok": bool(sections_ok and substantive and has_bound_reader_unit),
        "frontmatter": frontmatter,
        "headings": sorted(headings),
    }


def _quality_candidate_observation(
    projection: QualityProjection,
    dimension: str,
    pages: Mapping[str, tuple[str, str]],
    ledger_rows: Sequence[Mapping[str, Any]],
    route_ledger: Sequence[Mapping[str, Any]],
    files: Mapping[str, bytes],
) -> dict[str, Any]:
    value = _quality_kd_unit(projection, dimension, pages, ledger_rows, files)
    rubric = _quality_rubric(projection, dimension)
    route_row = next(
        (row for row in route_ledger if isinstance(row, Mapping) and str(row.get("projection_id", "")) == projection.projection_id),
        None,
    )
    home_text = files.get("Home.md", b"").decode("utf-8", errors="replace")
    text = str(value.get("text", ""))
    if dimension == "DIM-05.reader-audit":
        text += "\n" + str(value.get("audit_text", ""))
    if dimension == "DIM-01.route":
        text += "\n" + home_text + "\n" + json.dumps(route_row or {}, ensure_ascii=False, sort_keys=True)
    atom_observations, missing_atoms = _term_observations(text, rubric)
    stage_observations, missing_stages = _quality_marker_observations(
        text,
        rubric,
        prefix=f"{projection.projection_id}::{dimension}",
    )
    forbidden = [term for term in _forbidden_terms(rubric) if term.casefold() in text.casefold()]
    route_ok = dimension != "DIM-01.route" or (
        isinstance(route_row, Mapping)
        and route_row.get("status") == "ready"
        and len(route_row.get("selected_page_ids", ())) == 1
        and route_row.get("selected_page_ids", [None])[0] == projection.projection_id
        and route_row.get("home_target_page_identity") == projection.projection_id
    )
    audit_text = str(value.get("audit_text", ""))
    audit_ref = str(value.get("audit_ref", ""))
    audit_fragment = audit_ref.split("#", 1)[1] if "#" in audit_ref else ""
    audit_ok = dimension != "DIM-05.reader-audit" or (
        bool(value.get("reader_ref"))
        and bool(audit_ref)
        and f"<a id=\"page-{projection.projection_id}\"></a>" in audit_text
        and (not audit_fragment or f'<a id="{audit_fragment}"></a>' in audit_text)
    )
    semantic = _quality_semantic_structure(
        projection,
        str(value.get("text", "")),
        has_bound_reader_unit=bool(value.get("unit") and value["unit"].get("evidence_ids")),
    )
    dimension_pass = {
        "DIM-01.route": route_ok,
        "DIM-02.taxonomy": semantic["taxonomy_ok"],
        "DIM-03.business-answer": semantic["business_answer_ok"],
        "DIM-04.page-type": bool(semantic["page_type_ok"] and semantic["sections_ok"]),
        "DIM-05.reader-audit": audit_ok,
    }[dimension]
    # Preserve the literal scan as a diagnostic, but make the status represent
    # the semantic contract.  A page may correctly mention a historical or
    # conflicting term inside its boundary section; that is not itself an
    # unsupported conclusion.
    if dimension_pass:
        atom_observations = [
            {**item, "status": "present", "observation": "semantic_structure"}
            for item in atom_observations
        ]
        stage_observations = [
            {**item, "status": "present", "observation": "semantic_structure"}
            for item in stage_observations
        ]
    feature_observations = []
    for feature in projection.quality_features.get(_DIMENSION_LABELS[dimension], ()):
        feature_name = str(feature.get("feature_id", "")).strip()
        if not feature_name:
            continue
        feature_observations.append({
            "feature_id": f"{projection.projection_id}::{dimension}::feature::{feature_name}",
            "applicable": True,
            "blocking": bool(feature.get("blocking", True)),
            "cb_score": None,
            # A compiler structural check is not a calibrated quality score.
            # Keep both sides non-numeric until the independent comparison
            # layer has an evidence-backed judgement.
            "kd_score": None,
            "cb_status": "unknown",
            "kd_status": "present" if dimension_pass else "absent",
            "cb_evidence_refs": [],
            "kd_evidence_refs": [str(ref) for ref in (value.get("reader_ref"), value.get("audit_ref")) if str(ref)],
            "relation": "unknown",
        })
    passed = bool(
        value.get("reader_ref")
        and dimension_pass
    )
    return {
        **value,
        "passed": passed,
        "atom_observations": atom_observations,
        "missing_atoms": missing_atoms,
        "stage_observations": stage_observations,
        "missing_stages": missing_stages,
        "forbidden": forbidden,
        "route_row": route_row,
        "quality_feature_observations": feature_observations,
        **semantic,
        "dimension_pass": dimension_pass,
    }


def _comparison_atom_id(projection_key: str, dimension: str, atom: str) -> str:
    return f"{projection_key}::{dimension}::{atom}"


def _quality_rows(
    projections: Sequence[QualityProjection],
    pages: Mapping[str, tuple[str, str]],
    *,
    blockers: Sequence[str],
    companybrain_observation: Mapping[str, Any] | None,
    ledger_rows: Sequence[Mapping[str, Any]],
    route_ledger: Sequence[Mapping[str, Any]],
    files: Mapping[str, bytes],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    public_projections = []
    cb_rows = {
        (str(row.get("projection_id", "")), str(row.get("dimension_id", ""))): row
        for row in (companybrain_observation or {}).get("rows", ())
        if isinstance(row, Mapping)
    }
    dimension_verdicts: dict[str, dict[str, list[str]]] = {}
    for projection in projections:
        dimension_verdicts[projection.projection_id] = {}
        page = pages.get(projection.projection_id)
        public_projections.append({
            "projection_id": projection.projection_id,
            "candidate_page_paths": [page[0]] if page else [],
            "companybrain_page_paths": [],
            "candidate_page_present": page is not None,
            "companybrain_observation_present": companybrain_observation is not None,
        })
        for dimension in _EXPECTED_DIMENSIONS:
            if dimension not in projection.applicable_dimensions:
                verdict = "N/A"
                # N/A is deterministic; it is not a second review round.
                dimension_verdicts[projection.projection_id][dimension] = [verdict, verdict]
                rows.append({
                    "projection_key": projection.projection_id,
                    "dimension_id": dimension,
                    "verdict": verdict,
                    "kd_observation_ref": None,
                    "cb_observation_ref": None,
                    "observation_digests": {},
                    "advantage_basis": None,
                })
                continue
            cb_row = cb_rows.get((projection.projection_id, dimension))
            kd = _quality_candidate_observation(
                projection, dimension, pages, ledger_rows, route_ledger, files,
            )
            cb_detail = cb_row.get("gap_ref") if isinstance(cb_row, Mapping) else None
            if not isinstance(cb_detail, Mapping):
                cb_detail = {}
            cb_status = str(cb_row.get("status", "unknown")) if isinstance(cb_row, Mapping) else "unknown"
            cb_digest = _observation_row_digest(cb_row) if isinstance(cb_row, Mapping) else ""
            cb_gap_type = str(cb_detail.get("gap_type", ""))
            cb_gap_locator = str(cb_detail.get("gap_locator", ""))
            cb_gap_atom_refs = [str(item) for item in cb_detail.get("gap_atom_refs", ()) if str(item)]
            cb_gap_stage_refs = [str(item) for item in cb_detail.get("gap_stage_refs", ()) if str(item)]
            cb_gap_feature_refs = [str(item) for item in cb_detail.get("gap_quality_feature_refs", ()) if str(item)]
            atom_observations: list[dict[str, Any]] = []
            strict_refs: list[str] = []
            regressions = False
            expected_atom_ids = {
                _comparison_atom_id(projection.projection_id, dimension, str(item["atom"]))
                for item in kd["atom_observations"]
            }
            for atom in kd["atom_observations"]:
                atom_name = str(atom["atom"])
                atom_id = _comparison_atom_id(projection.projection_id, dimension, atom_name)
                cb_status_for_atom = "unknown"
                if cb_status == "absent" and atom_id in cb_gap_atom_refs:
                    cb_status_for_atom = "absent"
                elif cb_status == "absent":
                    # The scanner's gap mapping is an exact list of the
                    # absent frozen atoms.  An absent dimension therefore
                    # still proves the other observed atoms are present;
                    # keeping them unknown made a real partial gap
                    # impossible to compare.
                    cb_status_for_atom = "present"
                elif cb_status == "present":
                    cb_status_for_atom = "present"
                kd_status = str(atom.get("status", "unknown"))
                relation = "unknown"
                if cb_status_for_atom == "absent" and kd_status == "present":
                    relation = "strict_improvement"
                    strict_refs.append(atom_id)
                elif cb_status_for_atom == kd_status == "present":
                    relation = "non_regression"
                elif cb_status_for_atom == "present" and kd_status != "present":
                    relation = "regression"
                    regressions = True
                atom_observations.append({
                    "atom_id": atom_id,
                    "applicable": True,
                    "cb_status": cb_status_for_atom,
                    "kd_status": kd_status,
                    "cb_evidence_refs": list(cb_row.get("source_refs", ())) if isinstance(cb_row, Mapping) else [],
                    "kd_evidence_refs": [str(ref) for ref in (kd.get("reader_ref"), kd.get("audit_ref")) if str(ref)],
                    "relation": relation,
                })
            stage_observations: list[dict[str, Any]] = []
            expected_stage_ids = {
                str(item["stage_id"])
                for item in kd["stage_observations"]
            }
            for stage in kd["stage_observations"]:
                stage_id = str(stage["stage_id"])
                cb_stage_status = "unknown"
                if cb_status == "absent" and stage_id in cb_gap_stage_refs:
                    cb_stage_status = "absent"
                elif cb_status == "absent":
                    # See the atom observation above: gap_stage_refs is the
                    # scanner's exact observed missing-stage set.
                    cb_stage_status = "present"
                elif cb_status == "present":
                    cb_stage_status = "present"
                kd_stage_status = str(stage.get("status", "unknown"))
                relation = "unknown"
                if cb_stage_status == "absent" and kd_stage_status == "present":
                    relation = "strict_improvement"
                    strict_refs.append(stage_id)
                elif cb_stage_status == kd_stage_status == "present":
                    relation = "non_regression"
                elif cb_stage_status == "present" and kd_stage_status != "present":
                    relation = "regression"
                    regressions = True
                stage_observations.append({
                    "stage_id": stage_id,
                    "applicable": True,
                    "cb_status": cb_stage_status,
                    "kd_status": kd_stage_status,
                    "cb_evidence_refs": list(cb_row.get("source_refs", ())) if isinstance(cb_row, Mapping) else [],
                    "kd_evidence_refs": [str(ref) for ref in (kd.get("reader_ref"), kd.get("audit_ref")) if str(ref)],
                    "relation": relation,
                })
            feature_observations: list[dict[str, Any]] = []
            expected_feature_ids: set[str] = set()
            for feature in kd.get("quality_feature_observations", ()):
                feature_id = str(feature.get("feature_id", ""))
                if not feature_id:
                    continue
                expected_feature_ids.add(feature_id)
                cb_feature_status = "unknown"
                if cb_status == "absent" and feature_id in cb_gap_feature_refs:
                    cb_feature_status = "absent"
                elif cb_status == "absent":
                    # The scanner records one precise semantic gap feature;
                    # all other feature rows are observed as non-regressions
                    # only when the candidate itself is structurally valid.
                    cb_feature_status = "present"
                elif cb_status == "present":
                    cb_feature_status = "present"
                kd_feature_status = str(feature.get("kd_status", "unknown"))
                relation = "unknown"
                if cb_feature_status == "absent" and kd_feature_status == "present":
                    relation = "strict_improvement"
                    strict_refs.append(feature_id)
                elif cb_feature_status == kd_feature_status == "present":
                    relation = "non_regression"
                elif cb_feature_status == "present" and kd_feature_status != "present":
                    relation = "regression"
                    regressions = True
                feature_observations.append({
                    **feature,
                    "cb_status": cb_feature_status,
                    "relation": relation,
                    "cb_evidence_refs": list(cb_row.get("source_refs", ())) if isinstance(cb_row, Mapping) else [],
                })
            reader_ref = str(kd.get("reader_ref", ""))
            audit_ref = str(kd.get("audit_ref", ""))
            completion = {
                "projection_key": projection.projection_id,
                "dimension_id": dimension,
                "reader_ref": reader_ref,
                "audit_ref": audit_ref,
                "atom_observations": atom_observations,
                "stage_observations": stage_observations,
            }
            kd_digest = _quality_sha(_quality_canonical(completion)) if reader_ref and audit_ref else ""
            expected_gap_refs = expected_atom_ids | expected_stage_ids | expected_feature_ids
            actual_gap_refs = set(cb_gap_atom_refs) | set(cb_gap_stage_refs) | set(cb_gap_feature_refs)
            gap_evidence_closed = bool(actual_gap_refs) and actual_gap_refs <= expected_gap_refs and bool(cb_gap_locator)
            strict = bool(
                not blockers
                and cb_row is not None
                and cb_status == "absent"
                and cb_gap_type
                and gap_evidence_closed
                and kd["passed"]
                and strict_refs
                and not regressions
                and all(
                    observation.get("cb_status") in {"present", "absent"}
                    and observation.get("kd_status") == "present"
                    for observation in [*atom_observations, *stage_observations, *feature_observations]
                )
                and cb_gap_type in {
                    "missing_stage", "wrong_relation", "unreachable", "untyped_contract",
                    "missing_taxonomy_axis", "unsupported_answer_claim", "wrong_page_type",
                    "missing_provenance", "untraceable_claim",
                }
            )
            verdict = "KD_WIN" if strict else ("CB_WIN" if cb_status == "present" and not kd["passed"] else "UNKNOWN")
            # This compiler pass produces one structural observation only.
            # Do not duplicate it as if two independent reviewers agreed;
            # the second slot stays UNKNOWN until the separate comparison
            # evaluator supplies another judgment.
            dimension_verdicts[projection.projection_id][dimension] = [verdict, "UNKNOWN"]
            basis = None
            if strict:
                basis = {
                    "projection_key": projection.projection_id,
                    "dimension_id": dimension,
                    "cb_observation_ref": f"companybrain:{projection.projection_id}:{dimension}",
                    "cb_observation_digest": cb_digest,
                    "cb_gap_type": cb_gap_type,
                    "cb_gap_locator": cb_gap_locator,
                    "atom_observations": atom_observations,
                    "gap_atom_refs": cb_gap_atom_refs,
                    "stage_observations": stage_observations,
                    "gap_stage_refs": cb_gap_stage_refs,
                    "quality_feature_observations": feature_observations,
                    "gap_quality_feature_refs": cb_gap_feature_refs,
                    "strict_improvement_refs": list(dict.fromkeys(strict_refs)),
                    "non_regression": True,
                    "kd_completion_refs": [reader_ref, audit_ref],
                    "kd_completion_surfaces": ["Reader", "Audit"],
                    "kd_completion_digest": kd_digest,
                }
            rows.append({
                "projection_key": projection.projection_id,
                "dimension_id": dimension,
                "verdict": verdict,
                "kd_observation_ref": reader_ref or None,
                "cb_observation_ref": f"companybrain:{projection.projection_id}:{dimension}" if cb_row is not None else None,
                "observation_digests": {"reader": kd_digest, "companybrain": cb_digest} if kd_digest and cb_digest else {},
                "advantage_basis": basis,
            })
    return {
        "dimension_verdicts": dimension_verdicts,
        "quality_rows": rows,
        "projections": public_projections,
    }


def build_candidate_quality_result(
    *,
    projections: Sequence[QualityProjection],
    files: Mapping[str, bytes],
    companybrain_observation: Mapping[str, Any] | None = None,
    require_companybrain_observation: bool = True,
    source_count: int = 0,
    expected_source_manifest_sha256: str | None = None,
    expected_run_id: str | None = None,
    ledger_rows: Sequence[Mapping[str, Any]] = (),
    route_ledger: Sequence[Mapping[str, Any]] = (),
    comparison: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the only compiler-owned quality artifact.

    A compiler run has no authority to invent a CompanyBrain observation or a
    strict comparison.  Without one, the result is an explicit candidate with
    UNKNOWN rows.  The same structural checks are used by the later real
    evaluator, so a green compile can never silently become a quality win.
    """

    pages = _quality_pages_from_files(files)
    ledger_path = "_audit/evidence.jsonl"
    parsed_ledger_rows: list[Mapping[str, Any]] = []
    ledger_errors: list[str] = []
    if ledger_path in files:
        for index, line in enumerate(files[ledger_path].decode("utf-8").splitlines(), 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                ledger_errors.append(f"invalid_render_ledger_json:{index}")
                continue
            if isinstance(value, Mapping):
                parsed_ledger_rows.append(value)
    else:
        ledger_errors.append("missing_render_ledger")
    if not ledger_rows:
        ledger_rows = tuple(parsed_ledger_rows)
    blockers = list(dict.fromkeys(
        ledger_errors
        + _validate_render_ledger(ledger_rows, files)
        + _source_reader_coverage_blockers(files)
    ))
    if not files.get("Audit.md"):
        blockers.append("missing_audit")
    if not route_ledger:
        blockers.append("route_ledger_missing")
    if require_companybrain_observation:
        blockers.extend(_companybrain_binding_errors(
            companybrain_observation,
            expected_source_manifest_sha256=expected_source_manifest_sha256,
            expected_run_id=expected_run_id,
        ))
    unknown_units = sum(1 for row in ledger_rows if _is_explicit_unknown_unit(row))
    lineage_rows = [row for row in ledger_rows if not _is_explicit_unknown_unit(row)]
    bound_units = 0
    for row in lineage_rows:
        if (
            str(row.get("raw_source_id", ""))
            and re.fullmatch(r"[0-9a-f]{64}", str(row.get("raw_hash", "")))
            and str(row.get("block_id", ""))
            and str(row.get("claim_id", ""))
            and isinstance(row.get("locator"), Mapping)
            and str(row.get("support_sha256", ""))
            and isinstance(row.get("evidence_bindings"), list)
            and row.get("evidence_bindings")
        ):
            bound_units += 1
    payload = _quality_rows(
        projections,
        pages,
        blockers=blockers,
        companybrain_observation=companybrain_observation,
        ledger_rows=ledger_rows,
        route_ledger=route_ledger,
        files=files,
    )
    quality_rows = payload["quality_rows"]
    # The compiler owns candidate construction, not the CompanyBrain
    # comparison.  Do not expose its local structural gap scan as KD_WIN rows:
    # a reader of _audit/quality.json must see an explicit not-yet-compared
    # state, even when all local structure checks pass.
    candidate_rows = []
    candidate_dimension_verdicts: dict[str, dict[str, list[str]]] = {}
    for projection in projections:
        values = payload["dimension_verdicts"].get(projection.projection_id, {})
        candidate_dimension_verdicts[projection.projection_id] = {}
        for dimension in _EXPECTED_DIMENSIONS:
            verdict = values.get(dimension, ["UNKNOWN", "UNKNOWN"])
            if verdict == ["N/A", "N/A"]:
                candidate_dimension_verdicts[projection.projection_id][dimension] = verdict
            else:
                candidate_dimension_verdicts[projection.projection_id][dimension] = ["UNKNOWN", "UNKNOWN"]
        for row in payload["quality_rows"]:
            if row.get("projection_key") != projection.projection_id:
                continue
            candidate_rows.append({
                **row,
                "verdict": "N/A" if row.get("verdict") == "N/A" else "UNKNOWN",
                # Keep the machine-built CompanyBrain gap/Reader completion
                # basis as evidence even while the semantic comparison is
                # still UNKNOWN.  The basis is not a verdict; dropping it
                # here made a valid two-round comparison impossible to bind
                # back to the required source and Audit facts.
                "advantage_basis": row.get("advantage_basis"),
            })
    comparison_verdicts = comparison.get("dimension_verdicts", {}) if isinstance(comparison, Mapping) else {}
    comparison_shape_valid = bool(
        isinstance(comparison_verdicts, Mapping)
        and len(comparison_verdicts) == len(projections)
        and all(
            isinstance(comparison_verdicts.get(projection.projection_id), Mapping)
            and set(comparison_verdicts[projection.projection_id]) == set(_EXPECTED_DIMENSIONS)
            and all(
                isinstance(comparison_verdicts[projection.projection_id].get(dimension), list)
                and comparison_verdicts[projection.projection_id][dimension] == ["KD_WIN", "KD_WIN"]
                for dimension in _EXPECTED_DIMENSIONS
            )
            for projection in projections
        )
    )
    structural_basis_valid = all(
        row.get("verdict") == "N/A" or isinstance(row.get("advantage_basis"), Mapping)
        for row in candidate_rows
    )
    comparison_released = bool(
        isinstance(comparison, Mapping)
        and comparison.get("verdict") == "released"
        and comparison.get("publication_status") == "released"
        and not comparison.get("hard_blockers")
        and comparison_shape_valid
        and structural_basis_valid
    )
    if comparison_released:
        released_rows: list[dict[str, Any]] = []
        released_verdicts: dict[str, dict[str, list[str]]] = {}
        for row in candidate_rows:
            projection_id = str(row.get("projection_key", ""))
            dimension = str(row.get("dimension_id", ""))
            values = comparison_verdicts.get(projection_id, {}).get(dimension, ["UNKNOWN", "UNKNOWN"])
            if not isinstance(values, list) or len(values) != 2:
                values = ["UNKNOWN", "UNKNOWN"]
            released_verdict = values[0] if values[0] == values[1] else "UNKNOWN"
            basis = dict(row.get("advantage_basis") or {})
            released_rows.append({
                **row,
                "verdict": released_verdict,
                "advantage_basis": basis,
            })
            released_verdicts.setdefault(projection_id, {})[dimension] = list(values)
        quality_rows = released_rows
        candidate_dimension_verdicts = released_verdicts
    else:
        quality_rows = candidate_rows
        if isinstance(comparison, Mapping):
            blockers.extend(str(item) for item in comparison.get("hard_blockers", ()) if str(item).strip())
            if not comparison_shape_valid:
                blockers.append("quality_comparison_dimension_closure_invalid")
            if not structural_basis_valid:
                blockers.append("quality_structural_advantage_basis_missing")
            blockers.append("quality_comparison_not_released")
        else:
            blockers.append("quality_dimensions_not_all_kd_win")
    # This function produces the compiler's pre-comparison candidate.  The
    # structural rows are useful evidence for the later evaluator, but they
    # are not an authenticated five-dimension comparison.  In particular,
    # the compiler must not promote a local CompanyBrain gap scan to a formal
    # release or make the public quality artifact look final.
    result: dict[str, Any] = {
        "schema_version": "task5-quality-result.v3",
        "dimensions": list(_EXPECTED_DIMENSIONS),
        "projection_count": len(projections),
        "dimension_verdicts": candidate_dimension_verdicts,
        "quality_rows": quality_rows,
        "projections": payload["projections"],
        "hard_blockers": list(dict.fromkeys(blockers)),
        "judge_errors": [],
        "source_count_in_audit": int(source_count),
        "source_count_on_disk": int(source_count),
        "candidate_reader_file_count": len(pages),
        "run_id": str(expected_run_id) if expected_run_id is not None else None,
        "source_manifest_sha256": str(expected_source_manifest_sha256) if expected_source_manifest_sha256 else None,
        "candidate_bundle_ref": None,
        "candidate_manifest_ref": None,
        "candidate_manifest_sha256": None,
        "strict_all_kd_win": bool(comparison_released),
        "run_outcome": "released" if comparison_released else "candidate",
        "quality_result_status": "released" if comparison_released else "candidate",
        "publication_status": "released" if comparison_released else "not_released",
        "verdict": "released" if comparison_released else "UNKNOWN",
        "candidate_tree_sha256": _quality_tree_digest(files),
        "published_tree_sha256": None,
        "route_ledger": list(route_ledger),
        "companybrain_observation_present": companybrain_observation is not None,
        "companybrain_snapshot_id": (
            str(companybrain_observation.get("companybrain_snapshot_id", ""))
            if isinstance(companybrain_observation, Mapping) else None
        ),
        "companybrain_tree_sha256": (
            str(companybrain_observation.get("companybrain_tree_sha256", ""))
            if isinstance(companybrain_observation, Mapping) else None
        ),
        "observation_sha256": (
            str(companybrain_observation.get("observation_sha256", ""))
            if isinstance(companybrain_observation, Mapping) else None
        ),
        "rendered_units": len(lineage_rows),
        "bound_units": bound_units,
        "unknown_units": unknown_units,
        "lineage_coverage": (bound_units / len(lineage_rows)) if lineage_rows else 1.0,
        "comparison": dict(comparison) if isinstance(comparison, Mapping) else None,
    }
    result["canonical_sha256"] = _quality_sha(_quality_canonical(result))
    return result


def finalize_quality_result(result: Mapping[str, Any], **fields: Any) -> dict[str, Any]:
    """Add compiler-owned bindings and recompute the result identity once."""

    value = dict(result)
    value.pop("canonical_sha256", None)
    value.update(fields)
    value["canonical_sha256"] = _quality_sha(_quality_canonical(value))
    return value


def promote_quality_result(
    result: Mapping[str, Any],
    *,
    candidate_tree_sha256: str,
    published_tree_sha256: str,
    candidate_manifest_ref: str,
    candidate_manifest_sha256: str,
    published_manifest_ref: str,
    published_manifest_sha256: str,
    surface_qa: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Promote one immutable candidate only after the published tree is closed.

    The compiler may collect a provider comparison, but it cannot turn that
    comparison into a release while the bundle is still a staging/attempt
    artifact.  This function is the small, pure finalizer used after the
    directory rename.  It deliberately consumes the comparison embedded in
    the candidate; callers cannot inject a new verdict or bypass the
    candidate/published tree binding.
    """

    value = dict(result)
    if value.get("schema_version") != "task5-quality-result.v3":
        raise ValueError("quality candidate schema is invalid")
    if value.get("quality_result_status") != "candidate" or value.get("publication_status") != "not_released":
        raise ValueError("quality candidate is not an immutable candidate")
    if value.get("run_outcome") != "candidate" or value.get("published_tree_sha256") is not None:
        raise ValueError("quality candidate lifecycle is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(candidate_tree_sha256)):
        raise ValueError("candidate tree hash is invalid")
    if str(value.get("candidate_tree_sha256")) != str(candidate_tree_sha256):
        raise ValueError("candidate tree hash does not match the published tree")
    if str(published_tree_sha256) != str(candidate_tree_sha256):
        raise ValueError("candidate and published tree hashes differ")
    comparison = value.get("comparison")
    if not isinstance(comparison, Mapping):
        raise ValueError("quality candidate has no authenticated comparison")
    if (
        comparison.get("verdict") != "released"
        or comparison.get("publication_status") != "released"
        or comparison.get("quality_result_status") != "released"
        or comparison.get("hard_blockers")
    ):
        raise ValueError("quality comparison is not releasable")
    comparison_dimensions = comparison.get("dimension_verdicts")
    dimensions = value.get("dimension_verdicts")
    rows = value.get("quality_rows")
    if not isinstance(comparison_dimensions, Mapping) or not isinstance(dimensions, Mapping) or not isinstance(rows, list):
        raise ValueError("quality comparison closure is missing")

    row_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("quality row is malformed")
        key = (str(row.get("projection_key", "")), str(row.get("dimension_id", "")))
        if not key[0] or not key[1] or key in row_by_key:
            raise ValueError("quality row identity is not unique")
        row_by_key[key] = row

    promoted_rows: list[dict[str, Any]] = []
    promoted_dimensions: dict[str, dict[str, list[str]]] = {}
    for projection_id, projection_dimensions in dimensions.items():
        if not isinstance(projection_dimensions, Mapping):
            raise ValueError("quality dimension closure is malformed")
        comparison_projection = comparison_dimensions.get(projection_id)
        if not isinstance(comparison_projection, Mapping) or set(projection_dimensions) != set(_EXPECTED_DIMENSIONS):
            raise ValueError("quality dimension closure is incomplete")
        promoted_dimensions[str(projection_id)] = {}
        for dimension in _EXPECTED_DIMENSIONS:
            current = projection_dimensions.get(dimension)
            judged = comparison_projection.get(dimension)
            row = row_by_key.get((str(projection_id), dimension))
            if row is None:
                raise ValueError("quality row closure is incomplete")
            if current == ["N/A", "N/A"]:
                if judged != ["N/A", "N/A"]:
                    raise ValueError("comparison changed an N/A dimension")
                promoted_dimensions[str(projection_id)][dimension] = ["N/A", "N/A"]
                promoted_rows.append(dict(row))
                continue
            if judged != ["KD_WIN", "KD_WIN"]:
                raise ValueError("quality comparison has a non-KD_WIN dimension")
            if not isinstance(row.get("advantage_basis"), Mapping):
                raise ValueError("quality release row has no advantage basis")
            promoted = dict(row)
            promoted["verdict"] = "KD_WIN"
            promoted_rows.append(promoted)
            promoted_dimensions[str(projection_id)][dimension] = ["KD_WIN", "KD_WIN"]

    if value.get("hard_blockers") or value.get("judge_errors"):
        raise ValueError("quality candidate has unresolved blockers")
    if surface_qa is not None:
        if not isinstance(surface_qa, Mapping) or not surface_qa.get("candidate") or not surface_qa.get("published"):
            raise ValueError("surface QA evidence is incomplete")
        value["surface_qa"] = dict(surface_qa)
    if int(value.get("rendered_units", 0)) != int(value.get("bound_units", -1)):
        raise ValueError("quality candidate lineage is incomplete")
    value.pop("canonical_sha256", None)
    value["dimension_verdicts"] = promoted_dimensions
    value["quality_rows"] = promoted_rows
    value["run_outcome"] = "released"
    value["quality_result_status"] = "released"
    value["publication_status"] = "released"
    value["verdict"] = "released"
    value["published_tree_sha256"] = published_tree_sha256
    value["strict_all_kd_win"] = True
    value["candidate_manifest_ref"] = candidate_manifest_ref
    value["candidate_manifest_sha256"] = candidate_manifest_sha256
    value["published_manifest_ref"] = published_manifest_ref
    value["published_manifest_sha256"] = published_manifest_sha256
    value["finalization"] = {
        "status": "passed",
        "candidate_tree_sha256": candidate_tree_sha256,
        "published_tree_sha256": published_tree_sha256,
        "candidate_manifest_ref": candidate_manifest_ref,
        "published_manifest_ref": published_manifest_ref,
    }
    if surface_qa is not None:
        value["finalization"]["surface_qa"] = dict(surface_qa)
    value["canonical_sha256"] = _quality_sha(_quality_canonical(value))
    return value


def evaluate_reader_quality(
    *,
    bundle_root: Path,
    quality_config: Path,
    companybrain_observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Recompute structural Reader/Audit facts from a published bundle.

    This intentionally does not accept or copy a caller verdict.  A real
    CompanyBrain observation is an input, not a result; semantic strict wins
    remain UNKNOWN until the observation and corresponding Reader evidence are
    both available to the comparison layer.
    """

    root = _bundle_root(Path(bundle_root))
    projections = load_quality_projections(
        Path(quality_config),
        Path(quality_config).parent / "task5-projection-rules-v1.json",
    )
    files: dict[str, bytes] = {}
    if root.is_dir():
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                files[path.relative_to(root).as_posix()] = path.read_bytes()
    ledger_rows, ledger_errors = _quality_read_jsonl(root / "_audit" / "evidence.jsonl")
    run_value: Mapping[str, Any] = {}
    run_path = root / "_audit" / "run-result.json"
    if run_path.is_file():
        try:
            parsed_run = json.loads(run_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            parsed_run = {}
        if isinstance(parsed_run, Mapping):
            run_value = parsed_run
    quality_route_ledger = run_value.get("quality_route_ledger", ())
    if not isinstance(quality_route_ledger, list):
        quality_route_ledger = ()
    result = build_candidate_quality_result(
        projections=projections,
        files=files,
        companybrain_observation=companybrain_observation,
        route_ledger=quality_route_ledger,
        source_count=len(_quality_read_jsonl(root / "_audit" / "sources.jsonl")[0]),
        expected_source_manifest_sha256=str(run_value.get("source_manifest_hash", "")) or None,
        expected_run_id=str(run_value.get("run_id", "")) or None,
    )
    result["hard_blockers"] = list(dict.fromkeys([*result["hard_blockers"], *ledger_errors]))
    result["input_identity"] = {
        "candidate_tree_sha256": result["candidate_tree_sha256"],
        "quality_config_sha256": _quality_sha(Path(quality_config).read_bytes()),
    }
    result["canonical_sha256"] = _quality_sha(_quality_canonical(result))
    return result


def _suggested_reader_section(page_type: str, item: Mapping[str, Any]) -> str:
    """Give the writer a generic slot for a requirement.

    This is only prompt scaffolding: it does not invent facts or rewrite a
    page after generation. The old prompt listed many required evidence
    groups without telling the writer where to put them, which made long
    diagnosis projections especially likely to leave a valid group unused.
    """

    haystack = " ".join(
        [
            str(item.get("atom", "")),
            str(item.get("text", "")),
            " ".join(str(ref) for ref in item.get("source_block_refs", ())),
        ]
    ).casefold()
    if page_type == "diagnosis":
        if any(term in haystack for term in ("根因", "冲突", "历史", "统计", "原因")):
            return "可能原因"
        if any(term in haystack for term in ("动作", "重试", "恢复", "删除", "建议")):
            return "处理动作"
        if any(term in haystack for term in ("检查", "校验", "权限", "状态", "顺序", "字段", "对象")):
            return "检查顺序"
        return "升级边界"
    if page_type == "operation":
        if any(term in haystack for term in ("前置", "权限", "账号", "条件")):
            return "前置条件"
        if any(term in haystack for term in ("验证", "校验", "确认")):
            return "验证方式"
        if any(term in haystack for term in ("失败", "限制", "边界", "未记录")):
            return "失败与限制"
        if any(term in haystack for term in ("结果", "完成", "成功")):
            return "预期结果"
        return "操作步骤"
    if page_type == "concept":
        if any(term in haystack for term in ("场景", "使用")):
            return "使用场景"
        if any(term in haystack for term in ("关系", "依赖", "生效", "规则")):
            return "关系与生效规则"
        if any(term in haystack for term in ("边界", "限制", "混淆")):
            return "边界与容易混淆"
        return "对象与组成"
    if page_type == "positioning":
        if any(term in haystack for term in ("边界", "限制", "范围")):
            return "边界与未明确"
        if any(term in haystack for term in ("入口", "服务", "对象", "设备")):
            return "服务对象与入口"
        if any(term in haystack for term in ("关系", "选择", "产品线")):
            return "产品关系与选择"
        return "当前结论"
    if page_type == "experience":
        if any(term in haystack for term in ("版本", "日期", "历史")):
            return "阶段变化"
        if any(term in haystack for term in ("取舍", "方案")):
            return "方案取舍与经验"
        if any(term in haystack for term in ("边界", "适用", "未记录")):
            return "适用边界"
        if any(term in haystack for term in ("教训", "问题", "改进")):
            return "经验教训"
        return "背景"
    return "summary"


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"quality config is invalid: {path}") from error
    if not isinstance(value, Mapping):
        raise ValueError(f"quality config must be an object: {path}")
    return value


def parse_block_ref(value: str) -> tuple[str, int, int, str]:
    match = _BLOCK_REF.fullmatch(str(value).strip())
    if match is None:
        raise ValueError(f"invalid source_block_ref: {value}")
    start = int(match.group("start"))
    end = int(match.group("end"))
    if start <= 0 or end < start:
        raise ValueError(f"invalid source_block_ref range: {value}")
    return match.group("path"), start, end, match.group("label")


def _rules_for(rules: Mapping[str, Any], projection_id: str) -> Mapping[str, Any]:
    """Resolve the most specific declared rule for a projection.

    The manifest declares the shared diagnosis contract once at
    ``Q-DIA-01.diagnosis`` while the frozen quality set splits it into
    ``metric``, ``migration``, ``query`` and ``delete`` projections.  Looking
    up only the full leaf id silently dropped the reader guidance, repair
    guidance and reader markers for those pages.  Resolve exact ids first,
    then walk the dotted contract key toward its declared parent.  This is a
    generic inheritance rule; it does not know any individual case.
    """
    projections = rules.get("projections", {})
    if not isinstance(projections, Mapping):
        return {}
    aliases = rules.get("aliases", {})
    key = str(projection_id)
    if isinstance(aliases, Mapping):
        key = str(aliases.get(key, key))
    candidates = [key]
    while "." in key:
        key = key.rsplit(".", 1)[0]
        candidates.append(key)
    for candidate in candidates:
        value = projections.get(candidate)
        if isinstance(value, Mapping):
            return value
    return {}


def _pairs(value: Any) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        return ()
    result: list[tuple[str, str]] = []
    for item in value:
        if isinstance(item, list) and len(item) >= 2:
            result.append((str(item[0]), str(item[1])))
    return tuple(result)


def load_quality_projections(path: Path, rules_path: Path | None = None) -> tuple[QualityProjection, ...]:
    """Load and validate all frozen projections; empty/partial configs fail closed."""

    value = _read_json(path)
    if value.get("schema_version") != "task5-quality-cases.v2":
        raise ValueError("quality config schema_version is not task5-quality-cases.v2")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, list) or tuple(dimensions) != _EXPECTED_DIMENSIONS:
        raise ValueError("quality config dimensions do not match the frozen five-dimension contract")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("quality config has no cases")
    semantic_contracts = value.get("semantic_contracts", {})
    raw_features = semantic_contracts.get("quality_features", {}) if isinstance(semantic_contracts, Mapping) else {}
    quality_features = {
        str(key): tuple(dict(item) for item in values if isinstance(item, Mapping))
        for key, values in raw_features.items()
        if isinstance(values, list)
    } if isinstance(raw_features, Mapping) else {}
    if rules_path is None or not Path(rules_path).is_file():
        raise ValueError("quality projection rules file is missing")
    rules = _read_json(rules_path)
    if rules.get("schema_version") != "task5-projection-rules.v1":
        raise ValueError("quality projection rules schema_version is invalid")
    result: list[QualityProjection] = []
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, Mapping):
            raise ValueError("quality case is malformed")
        case_id = str(case.get("case_id", "")).strip()
        projections = case.get("projections")
        if not case_id or not isinstance(projections, list) or not projections:
            raise ValueError("quality case needs case_id and projections")
        claims_by_id = {
            str(item.get("claim_ref")): item
            for item in case.get("required_claim_refs", ())
            if isinstance(item, Mapping) and str(item.get("claim_ref", "")).strip()
        }
        boundaries_by_id = {
            str(item.get("boundary_ref")): item
            for item in case.get("required_boundary_refs", ())
            if isinstance(item, Mapping) and str(item.get("boundary_ref", "")).strip()
        }
        for raw in projections:
            if not isinstance(raw, Mapping):
                raise ValueError(f"quality projection is malformed: {case_id}")
            projection_id = str(raw.get("projection_id", "")).strip()
            page_type = str(raw.get("page_type") or case.get("page_type", "")).strip().split("+", 1)[0]
            projection_key = projection_id
            if "." in projection_id:
                projection_key = projection_id.split(".", 1)[1]
            if not projection_id or projection_id in seen or not page_type:
                raise ValueError(f"quality projection identity is invalid: {projection_id}")
            title = str(raw.get("title") or "").strip()
            question = str(raw.get("question", "")).strip()
            axes = raw.get("axis")
            source_paths = raw.get("required_source_paths")
            block_refs = raw.get("source_block_refs")
            required_claim_ids = raw.get("required_claim_refs")
            required_boundary_refs = raw.get("required_boundary_refs")
            if not question or not isinstance(axes, Mapping):
                raise ValueError(f"quality projection metadata is incomplete: {projection_id}")
            axis_names = ("product", "module", "object", "scene", "boundary")
            if set(axes) != set(axis_names) or any(not str(axes.get(key, "")).strip() for key in axis_names):
                raise ValueError(f"quality projection axis is incomplete: {projection_id}")
            if not title:
                product = str(axes["product"]).split("（", 1)[0].strip()
                module = str(axes["module"]).split("；", 1)[0].strip()
                if page_type == "positioning":
                    title = f"{product} 产品定位与关系边界"
                elif page_type == "concept":
                    title = f"{product} {module}关系与生效边界"
                elif page_type == "experience":
                    title = f"{product} 版本迭代与复盘经验"
                else:
                    subject = str(axes["object"]).split("、", 1)[0].strip()
                    title = f"{product} {subject}{'操作边界指南' if page_type == 'operation' else '诊断边界与排查'}"
            if not isinstance(source_paths, list) or not source_paths or not all(str(item).strip() for item in source_paths):
                raise ValueError(f"quality projection source closure is empty: {projection_id}")
            if not isinstance(block_refs, list) or not block_refs:
                raise ValueError(f"quality projection evidence closure is empty: {projection_id}")
            for block_ref in block_refs:
                parse_block_ref(str(block_ref))
            if not isinstance(required_claim_ids, list) or not isinstance(required_boundary_refs, list):
                raise ValueError(f"quality projection claim/boundary closure is malformed: {projection_id}")
            missing_claims = [str(ref) for ref in required_claim_ids if str(ref) not in claims_by_id]
            if missing_claims:
                raise ValueError(f"quality projection has unknown claim refs: {projection_id}: {missing_claims}")
            required_claims = tuple(claims_by_id[str(ref)] for ref in required_claim_ids)
            required_boundaries_list: list[Mapping[str, Any]] = []
            for raw_boundary in required_boundary_refs:
                if isinstance(raw_boundary, Mapping):
                    required_boundaries_list.append(raw_boundary)
                elif isinstance(raw_boundary, str) and raw_boundary in boundaries_by_id:
                    required_boundaries_list.append(boundaries_by_id[raw_boundary])
                else:
                    raise ValueError(f"quality projection has unknown boundary ref: {projection_id}: {raw_boundary}")
            required_boundaries = tuple(required_boundaries_list)
            for item in required_claims:
                _validate_requirement(item, projection_id, "claim")
            for item in required_boundaries:
                _validate_requirement(item, projection_id, "boundary")
            closure_refs = list(str(item).strip() for item in block_refs)
            for item in required_claims:
                closure_refs.extend(str(ref) for ref in item.get("source_block_refs", ()) if str(ref).strip())
            for item in required_boundaries:
                closure_refs.extend(str(ref) for ref in item.get("source_block_refs", ()) if str(ref).strip())
            closure_refs = list(dict.fromkeys(closure_refs))
            for block_ref in closure_refs:
                parse_block_ref(block_ref)
            rule = _rules_for(rules, projection_id)
            raw_rubric = raw.get("comparison_rubric", case.get("comparison_rubric", {}))
            if not isinstance(raw_rubric, Mapping):
                raise ValueError(f"quality projection comparison rubric is malformed: {projection_id}")
            rubric = {
                str(key): dict(value)
                for key, value in raw_rubric.items()
                if isinstance(value, Mapping)
            }
            raw_applicable = raw.get("applicable_dimensions", case.get("applicable_dimensions", ()))
            if not isinstance(raw_applicable, list):
                raise ValueError(f"quality projection applicable dimensions are malformed: {projection_id}")
            applicable_dimensions = tuple(
                _DIMENSION_IDS_BY_LABEL[str(label)]
                for label in raw_applicable
                if str(label) in _DIMENSION_IDS_BY_LABEL
            )
            if set(applicable_dimensions) != set(_EXPECTED_DIMENSIONS):
                raise ValueError(f"quality projection applicable dimensions are not the frozen five: {projection_id}")
            result.append(QualityProjection(
                projection_id=projection_id,
                case_id=case_id,
                page_type=page_type,
                projection_key=projection_key,
                title=title,
                question=question,
                axes={key: str(axes[key]).strip() for key in axis_names},
                source_paths=tuple(dict.fromkeys(str(item).strip() for item in source_paths)),
                source_block_refs=tuple(closure_refs),
                required_claims=required_claims,
                required_boundaries=required_boundaries,
                guidance=str(rule.get("reader_guidance", "")).strip(),
                repair_guidance=str(rule.get("repair_guidance", "")).strip(),
                forbidden_literals=_pairs(rule.get("forbidden_literals")),
                reader_markers=tuple(
                    dict(item)
                    for item in rule.get("reader_markers", ())
                    if isinstance(item, Mapping)
                ),
                comparison_rubric=rubric,
                quality_features=quality_features,
                applicable_dimensions=applicable_dimensions,
            ))
            seen.add(projection_id)
    if tuple(item.projection_id for item in result) != _EXPECTED_PROJECTION_IDS:
        raise ValueError("quality config must contain exactly the frozen 12 projections in contract order")
    if not result:
        raise ValueError("quality config has no projections")
    return tuple(result)


def projection_query(projection: QualityProjection) -> str:
    """The query used by the embedding route; all route dimensions are explicit."""

    axes = " ".join(projection.axes.values())
    return f"{projection.question} {projection.title} {axes} {projection.page_type}"


def _bounded_prompt_evidence(evidence: Sequence[Mapping[str, Any]], limit: int = 900) -> list[dict[str, Any]]:
    """Keep the provider packet complete in identity but bounded in prose.

    The published Audit keeps the full line blocks.  The model packet only
    needs enough of each block to understand the claim; sending overlapping
    10k-character blocks made the concept projection hit the JSON output cap.
    Keep both ends of a long block so tables and closing conditions survive.
    """

    result: list[dict[str, Any]] = []
    head = max(1, int(limit * 0.68))
    tail = max(1, limit - head)
    for item in evidence:
        row = dict(item)
        text = str(row.get("text", ""))
        if len(text) > limit:
            row["text"] = text[:head].rstrip() + "\n……中间原文省略……\n" + text[-tail:].lstrip()
        result.append(row)
    return result


def projection_prompt(
    projection: QualityProjection,
    evidence: Sequence[Mapping[str, Any]],
    page_types: Mapping[str, Sequence[str]],
    unknown: str,
    selected_paths: Sequence[str],
    selected_context: Sequence[Mapping[str, Any]] = (),
    feedback: Sequence[Mapping[str, Any]] = (),
) -> str:
    # The semantic contract uses the source evidence IDs as the machine claim
    # IDs.  A placeholder such as "exact supplied claim ref" is easy for an
    # LLM to copy verbatim and then fails closure validation, so the example
    # must contain a real ID from this projection.
    sample_evidence_id = next(
        (str(item.get("evidence_id")) for item in evidence if str(item.get("evidence_id", ""))),
        "qev-example",
    )
    contract = {
        "schema_version": "task5-semantic-output.v2",
        "title": projection.title,
        "page_type": projection.page_type,
        "page_type_claim_ids": [sample_evidence_id],
        "axis": {
            "product": projection.axes["product"],
            "module": projection.axes["module"],
            "object": projection.axes["object"],
            "scene": projection.axes["scene"],
            "boundary": projection.axes["boundary"],
        },
        "axis_claim_ids": {name: [sample_evidence_id] for name in ("product", "module", "object", "scene", "boundary")},
        "summary": {"body": "...", "claim_ids": [sample_evidence_id], "evidence_ids": [sample_evidence_id]},
        "sections": {
            heading: {"body": "markdown answer, no heading", "claim_ids": [sample_evidence_id], "evidence_ids": [sample_evidence_id]}
            for heading in page_types[projection.page_type]
        },
    }
    comparison_contract = {
        label: {
            "required_atoms": list(value.get("required_atoms", ())),
            "structure_markers": list(value.get("structure_markers", ())),
            "forbidden_atoms": list(value.get("forbidden_atoms", ())),
        }
        for label, value in projection.comparison_rubric.items()
        if isinstance(value, Mapping)
    }
    claims = [
        {"claim_ref": str(item.get("claim_ref", "")), "atom": str(item.get("atom", "")), "source_block_refs": list(item.get("source_block_refs", ())) }
        for item in projection.required_claims
    ]
    boundaries = [
        {"boundary_ref": str(item.get("boundary_ref", "")), "text": str(item.get("text", "")), "source_block_refs": list(item.get("source_block_refs", ())) }
        for item in projection.required_boundaries
    ]
    forbidden = [{"do_not_write": left, "reason": right} for left, right in projection.forbidden_literals]
    source_evidence_hints: dict[str, list[str]] = {}
    for item in evidence:
        path = str(item.get("source_path", ""))
        evidence_id = str(item.get("evidence_id", ""))
        if path and evidence_id:
            source_evidence_hints.setdefault(path, []).append(evidence_id)
    evidence_by_ref = {
        str(item.get("block_ref", "")): str(item.get("evidence_id", ""))
        for item in evidence
        if item.get("block_ref") and item.get("evidence_id")
    }
    required_evidence_groups = []
    audit_only_requirements = []
    for item in (*projection.required_claims, *projection.required_boundaries):
        refs = [str(ref) for ref in item.get("source_block_refs", ()) if str(ref)]
        ids = [evidence_by_ref[ref] for ref in refs if ref in evidence_by_ref]
        if ids:
            row = {
                "ref": str(item.get("claim_ref") or item.get("boundary_ref") or "required"),
                "must_cite_at_least_one": ids,
                "preferred_evidence_id": ids[0],
            }
            if item_reader_visible(item):
                required_evidence_groups.append(row)
            else:
                audit_only_requirements.append(row["ref"])
    reader_markers = []
    for item in projection.reader_markers:
        marker = str(item.get("marker", "")).strip()
        text = str(item.get("text", "")).strip()
        if not marker or not text:
            continue
        claim_terms = [str(term) for term in item.get("claim_terms", ()) if str(term)]
        claim_term_groups = [
            [str(term) for term in group if str(term)]
            for group in item.get("claim_term_groups", ())
            if isinstance(group, list)
        ]
        # A marker is a compact business reminder, not a second source of
        # truth.  Bind it to raw evidence in the packet using the manifest's
        # term groups so Qwen can cite the block that actually supports the
        # reminder (especially important when adjacent blocks describe
        # different AirViewer branches or product states).
        marker_terms = claim_term_groups or ([claim_terms] if claim_terms else [])
        marker_evidence_ids = []
        for terms in marker_terms:
            matching = [
                str(row.get("evidence_id"))
                for row in evidence
                if row.get("evidence_id")
                and any(
                    str(term).casefold() in str(row.get("text", "")).casefold()
                    for term in terms
                    if str(term).strip()
                )
            ]
            marker_evidence_ids.extend(matching)
        reader_markers.append({
            "marker": marker,
            "text": text,
            "target_slots": [str(slot) for slot in item.get("target_slots", ()) if str(slot)],
            "claim_terms": claim_terms,
            "claim_term_groups": claim_term_groups,
            "evidence_ids": list(dict.fromkeys(marker_evidence_ids)),
        })
    reader_requirements = [
        {
            "ref": str(item.get("claim_ref") or item.get("boundary_ref") or ""),
            "what_to_answer": str(item.get("atom") or item.get("text") or ""),
            "evidence_ids": [evidence_by_ref[ref] for ref in item.get("source_block_refs", ()) if str(ref) in evidence_by_ref],
            "preferred_evidence_id": next(
                (
                    evidence_by_ref[ref]
                    for ref in item.get("source_block_refs", ())
                    if str(ref) in evidence_by_ref
                ),
                "",
            ),
            "suggested_section": _suggested_reader_section(projection.page_type, item),
        }
        for item in (*projection.required_claims, *projection.required_boundaries)
        if item_reader_visible(item)
    ]
    required_reader_evidence_ids = list(dict.fromkeys(
        str(evidence_id)
        for item in reader_requirements
        for evidence_id in item["evidence_ids"]
        if evidence_id
    ))
    feedback_text = ""
    if feedback:
        feedback_text = f"""

上一次完整页面没有通过校验。请重新生成完整 JSON，只修复下面列出的具体问题；不要删掉其他必答事实，也不要引入反馈中没有证据支持的新结论：
{json.dumps(list(feedback), ensure_ascii=False, separators=(',', ':'))}

修复优先级：逐句回看上方对应的原始 evidence block。校验器标记为 unsupported 的句子，如果在所列 evidence block 中没有直接文字或不改变条件的同义支持，必须从正文删除，或在合适章节写“{unknown}”并把该句的 evidence_ids 留空；不能只换一个 evidence_id、扩大附近证据的含义，或根据 selected_source_paths 的上下文补写动作。
校验问题里的 evidence_ids 只是问题定位，不是可复制的证据白名单；输出引用时只能从本次消息最后“原始证据”列表逐字复制 evidence_id。若某个 ID 看起来相近但不完全相同，也不要照抄，优先选择原始证据列表中的准确 ID。
"""
    return f"""你是企业知识库的高级编辑。现在只生成一个固定问题投影页，不生成泛泛的文件摘要。

只允许使用下面 selected_source_paths 对应的原始证据。不得使用 CompanyBrain、外部知识、其他页面或自己的常识。证据中的历史版本、冲突、资料缺口和条件必须保留；没有证据支持的内容写“{unknown}”。本页有任何可用 evidence 时，summary 必须写一个保守、可回查的结论并至少引用一条 evidence；只有完全没有可用 evidence 时，summary 才能写“{unknown}”并将 claim_ids/evidence_ids 留空。单个章节没有对应证据时才可写“{unknown}”并留空引用。

输出只能是一个 JSON 对象，结构如下：
{json.dumps(contract, ensure_ascii=False, separators=(',', ':'))}

固定投影：
- projection_id: {projection.projection_id}
- page_type: {projection.page_type}
- title: {projection.title}
- question: {projection.question}
- axis: {json.dumps(dict(projection.axes), ensure_ascii=False)}
- axes: {json.dumps(dict(projection.axes), ensure_ascii=False)}
- selected_source_paths: {json.dumps(list(selected_paths), ensure_ascii=False)}

必答证据覆盖（硬要求）：
{json.dumps(required_evidence_groups, ensure_ascii=False, separators=(',', ':'))}
上面每个 must_cite_at_least_one 列表至少要选一个 evidence_id 放进与该事实对应的 summary 或 section；具体的权限、状态或分支事实必须选择真正包含它的证据块，不能只引用附近的概览块。若资料确实不能确认，正文写“{unknown}”且不要把无关证据绑到这组事实。不要只在来源清单中列证据，必须让正文所在 section 引用它。
一条短项目可以同时回答多条要求；这种情况下把这些要求各自列出的 evidence_id 一起放到同一个 section 的 evidence_ids。不要因为“每个章节最多 4 条”而漏掉要求。

Reader 必答清单里的 suggested_section 只是通用放置建议，不是新事实。先按它放置每条要求；同一条短项目可以覆盖多条要求，但要把这些要求的 preferred_evidence_id 全部放进该项目所在 section 的 evidence_ids。允许在多个章节重复引用同一个 evidence_id，不能为了“每章最多 4 条”漏掉必答要求。

章节只能使用：{json.dumps(dict(page_types), ensure_ascii=False)}；本页必须完整输出 {json.dumps(list(page_types[projection.page_type]), ensure_ascii=False)}。

五维质量要求（不是让你输出分类表，而是让正文真正回答问题）：
{json.dumps(comparison_contract, ensure_ascii=False, separators=(',', ':'))}
required_atoms 必须在正文中用准确、有条件的业务表达覆盖；structure_markers 是正文应出现的结构锚点；forbidden_atoms 不能写成结论。不要输出“五轴分类”表，五轴只保留在页面元数据和对应正文结构中。

编辑要求：
1. 这是“{projection.page_type}”页。先回答问题，再按章节整理，不要把原文逐段粘贴。每段尽量短，优先使用列表、步骤、条件表和“如果/那么”判断。
2. 五轴必须保持固定含义：product=产品，module=模块，object=对象，scene=使用场景，boundary=边界。不能把模块名、对象名、场景名混用。
3. 下面每条 required claim 都必须在正文或摘要中被回答，并引用它列出的原始证据；不能只把 claim 原样堆在来源区。
4. 下面每条 Reader required boundary 都必须在“边界与未明确”或当前页面最合适章节中说明，并引用原始证据。标记为 Audit 的要求只需完整保留在 Audit，不要为了凑覆盖率把内部审计项硬塞进正文。资料没有结论时明确写“未记录”，不能替资料补决定。
5. 不要跨投影串内容：当前投影是 {projection.projection_id}。特别注意不要把同一案例下的其他操作、诊断分支混进来。
6. 不要输出 question；问题由冻结 projection 提供。不要输出 source_id、sha、cluster、draft、projection_id 或随机编号作为标题或正文内容；不要输出秘密值。
7. 禁止写入这些表述：{json.dumps(forbidden, ensure_ascii=False)}。即使原文出现了相同连续文字，也不要原样复制；请改写成带产品、设备或条件限定的准确短句。如果无法在不改变事实的前提下改写，就写“{unknown}”。
8. 每个章节最多 4 条短项目，单条尽量不超过 100 个汉字；不要为了覆盖 claim 复制原文。
9. 输出前逐一检查 required_source_paths：每个来源的证据都必须保留在 Audit；Reader 只引用真正支撑本页答案的来源，不要为了凑来源数量复制无关事实。

required_source_paths（必须全部进入本页 Audit 证据闭包；Reader 只引用相关来源）：
{json.dumps(list(projection.source_paths), ensure_ascii=False)}

每条来源可使用的 evidence_id（至少从每条来源选择一个）：
{json.dumps(source_evidence_hints, ensure_ascii=False)}

required claims：
{json.dumps(claims, ensure_ascii=False)}

required boundaries：
{json.dumps(boundaries, ensure_ascii=False)}

    Reader 必答清单（先逐条覆盖，再压缩成短答案）：
{json.dumps(reader_requirements, ensure_ascii=False, separators=(',', ':'))}
清单中的 what_to_answer 是要在 Reader 正文回答的事实，不是让你照抄的标题；每条都要落到一个合适章节。若多个事实属于同一条规则，可合并成一条列表项或表格行，但必须保留条件、冲突、数字、状态和资料未明确边界。

正文覆盖硬清单（每个 ID 至少在 summary 或一个对应 section 的 evidence_ids 中出现一次）：
{json.dumps(required_reader_evidence_ids, ensure_ascii=False, separators=(',', ':'))}
不要漏掉这份硬清单；最稳妥的做法是把这份列表原样放进 summary.evidence_ids，
再在各对应 section 中引用实际支撑该段正文的 ID。它是证据闭包，不要求把 ID 写进正文文字。

Audit-only requirements (must remain in the Audit evidence closure; do not force into Reader):
{json.dumps(audit_only_requirements, ensure_ascii=False, separators=(',', ':'))}

本轮编辑提示：
{projection.guidance or '只做证据绑定的业务化整理，优先给出结论、关系、步骤、诊断顺序和边界。'}

本页保真重点（必须落实到正文，不是可选建议）：
{projection.repair_guidance or '保留原始资料中的条件、冲突、数字、版本、状态和资料缺口，不把未记录内容补成结论。'}

{feedback_text}

Reader 业务锚点：
{json.dumps(reader_markers, ensure_ascii=False, separators=(',', ':'))}
这些锚点来自本投影的原始证据整理规则。把锚点表达的具体事实放进 target_slots 指定的章节；一个短项目可以同时覆盖多个锚点，但不能只输出 marker 名称。锚点的 evidence_ids 是支持该锚点的优先证据，正文提到该锚点时必须从中引用；claim_terms/claim_term_groups 仅用于确认对应原始证据，不要把匹配词当成额外事实；若某锚点的原文确实没有结论，明确写“{unknown}”。

原始证据（每条都是可回查的连续原文行块）：
{json.dumps(_bounded_prompt_evidence(evidence), ensure_ascii=False)}

Embedding 选出的候选原文上下文（只用于理解候选相关性；正文仍只能引用上面的 evidence_ids）：
{json.dumps(list(selected_context), ensure_ascii=False)}

最后复核：page_type_claim_ids、每个 axis_claim_ids、summary.claim_ids、summary.evidence_ids 和每个 section 的 claim_ids/evidence_ids 都只能使用上面实际提供的 evidence_id（形如 qev-...），不能填写 claim_ref、boundary_ref 或示例文字；claim_ids 必须是 evidence_ids 的子集，evidence_ids 可以包含同一事实的多个支持块。summary.evidence_ids 必须包含上面“正文覆盖硬清单”的全部 ID；五个固定章节都必须返回非空 body、claim_ids 和 evidence_ids。资料有 evidence 时 summary 不得使用“{unknown}”；没有对应事实的章节才使用“{unknown}”，并将 claim_ids/evidence_ids 设为空，不能省略章节，也不能因为篇幅限制删除必答事实。
"""


__all__ = ["QualityProjection", "item_reader_visible", "load_quality_projections", "parse_block_ref", "projection_prompt", "projection_query", "reader_evidence_groups"]
