"""Provider-backed five-dimension comparison for a Task5 candidate.

The compiler owns the candidate bytes; this module owns the only semantic
comparison that may turn those bytes into a release.  It deliberately keeps
the comparison small: one fixed question page, one CompanyBrain baseline
packet, five dimensions, and two label-swapped rounds.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .providers import ProviderError, SemanticModel
from .quality import QualityProjection


DIMENSIONS = (
    "route",
    "taxonomy",
    "business-answer",
    "page-type",
    "Reader-Audit",
)
DIMENSION_IDS = {
    "route": "DIM-01.route",
    "taxonomy": "DIM-02.taxonomy",
    "business-answer": "DIM-03.business-answer",
    "page-type": "DIM-04.page-type",
    "Reader-Audit": "DIM-05.reader-audit",
}
_VERDICTS = {"A_WIN", "B_WIN", "KD_WIN", "CB_WIN", "TIE", "UNKNOWN"}
_PAGE_DUTIES = {
    "positioning": "回答是什么、服务谁、怎么选、边界",
    "concept": "解释对象、组成、关系、生效规则、边界",
    "operation": "给前置条件、步骤、结果、验证、失败限制",
    "diagnosis": "给现象、检查顺序、可能原因、处理动作、升级边界",
    "experience": "整理背景、阶段变化、取舍、教训、适用边界",
}


def _sha(raw: bytes | str) -> str:
    return hashlib.sha256(raw.encode("utf-8") if isinstance(raw, str) else raw).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _bounded(value: str, limit: int = 16_000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n[比较输入已截断；原始证据仍以 Audit 为准]"


def _normalise(value: Mapping[str, Any], projection_id: str, swapped: bool) -> dict[str, Any]:
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, Mapping) or set(dimensions) != set(DIMENSIONS):
        raise ValueError("comparison response must contain exactly five dimensions")
    output: dict[str, Any] = {}
    for dimension in DIMENSIONS:
        item = dimensions.get(dimension)
        if not isinstance(item, Mapping):
            raise ValueError(f"comparison response has malformed dimension: {dimension}")
        verdict = str(item.get("verdict", "")).strip()
        if verdict not in _VERDICTS:
            raise ValueError(f"comparison response has invalid verdict: {dimension}")
        if verdict in {"KD_WIN", "CB_WIN"}:
            kd_verdict = verdict
        elif verdict == "A_WIN":
            kd_verdict = "CB_WIN" if swapped else "KD_WIN"
        elif verdict == "B_WIN":
            kd_verdict = "KD_WIN" if swapped else "CB_WIN"
        else:
            kd_verdict = verdict
        reason = str(item.get("reason", "")).strip()
        if not reason:
            raise ValueError(f"comparison response has no reason: {dimension}")
        output[dimension] = {"verdict": kd_verdict, "reason": reason[:120]}
    risks = value.get("blocking_risks", [])
    if not isinstance(risks, list) or any(not isinstance(item, str) for item in risks):
        raise ValueError("comparison response blocking_risks is invalid")
    return {
        "projection_id": projection_id,
        "dimensions": output,
        "blocking_risks": [item.strip() for item in risks if item.strip()],
    }


def _prompt(
    projection: QualityProjection,
    candidate_text: str,
    companybrain_text: str,
    home_text: str,
    audit_text: str,
    raw_evidence: Sequence[Mapping[str, Any]],
    swapped: bool,
) -> str:
    candidate_label, baseline_label = ("B", "A") if swapped else ("A", "B")
    contract = {
        "projection_id": projection.projection_id,
        "dimensions": {
            dimension: {"verdict": "A_WIN|B_WIN|TIE|UNKNOWN", "reason": "具体理由"}
            for dimension in DIMENSIONS
        },
        "blocking_risks": [],
    }
    return f"""你是独立的企业知识库质量评审者。只评审一个固定问题，不使用外部知识、CompanyBrain 以外的资料或常识。

固定问题：{projection.question}
固定页面类型：{projection.page_type}；这个类型的职责：{_PAGE_DUTIES.get(projection.page_type, '')}
固定五轴：{_json(dict(projection.axes))}
KnowledgeDigest 候选是 {candidate_label}，CompanyBrain 基线是 {baseline_label}。

五项必须分别判断：
- route：读者能否从问题/场景入口找到这张专门答案页，而不是混合概览；
- taxonomy：产品、模块、对象、场景、边界是否清楚且有用；
- business-answer：是否直接回答问题，能执行，并保留条件、冲突、数字和未明确边界；
- page-type：是否履行固定页面类型职责，不能只看页面自称；
- Reader-Audit：正文是否能回到具体原始路径、证据和行范围。

只有实际使用价值严格更高且没有事实退化才判 WIN；相近判 TIE；证据不足判 UNKNOWN。若专门问题页对比宽泛混合页，专门页在 route/page-type 可以胜出，但仍要检查正文是否有证据。理由必须用大白话，点出具体内容或具体缺口，不能只写“更好”“更完整”。
只返回 JSON，结构必须是：{_json(contract)}。不要输出 Markdown、问题复述、内部 ID 列表或新的建议。

{candidate_label}（KnowledgeDigest）：
{_bounded(candidate_text)}

{baseline_label}（CompanyBrain）：
{_bounded(companybrain_text)}

候选入口 Home：
{_bounded(home_text, 8_000)}

候选 Audit 回查摘要：
{_bounded(audit_text, 10_000)}

冻结的原始证据（判断是否漏知识的唯一依据）：
{_json(list(raw_evidence))}
"""


def _load_baseline(root: Path, baseline_path: Path, projection: QualityProjection) -> tuple[list[str], str]:
    try:
        value = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("CompanyBrain baseline manifest is invalid") from error
    entries = value.get("entries") if isinstance(value, Mapping) else None
    if not isinstance(entries, list):
        raise ValueError("CompanyBrain baseline manifest has no entries")
    paths: list[str] = []
    texts: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping) or projection.projection_id not in entry.get("projection_keys", []):
            continue
        relative = str(entry.get("relative_path", ""))
        target = root / relative
        if not relative or not target.is_file() or target.is_symlink():
            continue
        actual_hash = _sha(target.read_bytes())
        if actual_hash != str(entry.get("content_hash", "")) or entry.get("applicability") != "present":
            continue
        paths.append(relative)
        texts.append(f"FILE: {relative}\n{target.read_text(encoding='utf-8', errors='replace')}")
    return paths, "\n\n".join(texts)


def compare_quality(
    *,
    projections: Sequence[QualityProjection],
    page_payloads: Mapping[str, Mapping[str, Any]],
    companybrain_root: Path,
    baseline_path: Path,
    raw_evidence: Mapping[str, Sequence[Mapping[str, Any]]],
    model: SemanticModel,
) -> dict[str, Any]:
    """Run two label-swapped semantic rounds and return a release decision."""

    jobs: list[tuple[QualityProjection, bool]] = []
    packets: dict[tuple[str, bool], dict[str, Any]] = {}
    blockers: list[str] = []
    for projection in projections:
        page = page_payloads.get(projection.projection_id)
        if not isinstance(page, Mapping):
            blockers.append(f"{projection.projection_id} has no candidate Reader page")
            continue
        baseline_paths, baseline_text = _load_baseline(companybrain_root, baseline_path, projection)
        if not baseline_paths:
            blockers.append(f"{projection.projection_id} has no verified CompanyBrain baseline")
            continue
        packet = {
            "candidate_text": str(page.get("text", "")),
            "companybrain_text": baseline_text,
            "home_text": str(page.get("home_text", "")),
            "audit_text": str(page.get("audit_text", "")),
            "raw_evidence": list(raw_evidence.get(projection.projection_id, ())),
            "baseline_paths": baseline_paths,
        }
        packets[(projection.projection_id, False)] = packet
        packets[(projection.projection_id, True)] = packet
        jobs.extend(((projection, False), (projection, True)))

    def judge(job: tuple[QualityProjection, bool]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        projection, swapped = job
        packet = packets[(projection.projection_id, swapped)]
        prompt = _prompt(
            projection,
            candidate_text=packet["candidate_text"],
            companybrain_text=packet["companybrain_text"],
            home_text=packet["home_text"],
            audit_text=packet["audit_text"],
            raw_evidence=packet["raw_evidence"],
            swapped=swapped,
        )
        prompt_hash = _sha(prompt)
        try:
            response = model.generate(prompt)
            response_hash = _sha(response)
            value = json.loads(response)
            if not isinstance(value, Mapping):
                raise ValueError("comparison response is not an object")
            normalised = _normalise(value, projection.projection_id, swapped)
            return normalised, {
                "projection_id": projection.projection_id,
                "round": "swapped" if swapped else "normal",
                "status": "passed",
                "prompt_sha256": prompt_hash,
                "response_sha256": response_hash,
                "baseline_paths": packet["baseline_paths"],
            }
        except (ProviderError, ValueError, TypeError, json.JSONDecodeError) as error:
            return None, {
                "projection_id": projection.projection_id,
                "round": "swapped" if swapped else "normal",
                "status": "failed",
                "prompt_sha256": prompt_hash,
                "response_sha256": "",
                "error": f"{type(error).__name__}: {error}",
            }

    rounds: dict[str, dict[str, dict[str, Any]]] = {}
    trace: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="digest-quality-judge") as executor:
        results = list(executor.map(judge, jobs))
    for judgement, receipt in results:
        trace.append(receipt)
        if judgement is None:
            blockers.append(f"{receipt['projection_id']} {receipt['round']} quality comparison failed")
            continue
        rounds.setdefault(receipt["projection_id"], {})[receipt["round"]] = judgement
        blockers.extend(
            f"{receipt['projection_id']} {risk}"
            for risk in judgement.get("blocking_risks", [])
        )

    dimension_verdicts: dict[str, dict[str, list[str]]] = {}
    for projection in projections:
        values = rounds.get(projection.projection_id, {})
        normal = values.get("normal", {}).get("dimensions", {})
        swapped = values.get("swapped", {}).get("dimensions", {})
        dimension_verdicts[projection.projection_id] = {
            DIMENSION_IDS[dimension]: [
                str(normal.get(dimension, {}).get("verdict", "UNKNOWN")),
                str(swapped.get(dimension, {}).get("verdict", "UNKNOWN")),
            ]
            for dimension in DIMENSIONS
        }
    strict = bool(
        not blockers
        and len(dimension_verdicts) == len(projections)
        and all(
            values == ["KD_WIN", "KD_WIN"]
            for projection_values in dimension_verdicts.values()
            for values in projection_values.values()
        )
    )
    return {
        "schema_version": "task5-quality-comparison.v1",
        "rounds": rounds,
        "dimension_verdicts": dimension_verdicts,
        "provider_trace": trace,
        "hard_blockers": list(dict.fromkeys(blockers)),
        "verdict": "released" if strict else "not_released",
        "publication_status": "released" if strict else "not_released",
        "quality_result_status": "released" if strict else "candidate",
    }


__all__ = ["DIMENSIONS", "DIMENSION_IDS", "compare_quality"]
