from __future__ import annotations

import json
from pathlib import Path

from knowledge_digest.quality import QualityProjection
from knowledge_digest.quality_compare import compare_quality


class _FakeModel:
    identity = {"model": "qwen3.8"}
    calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        # The comparison module swaps labels in the prompt; the fake names
        # the KnowledgeDigest side as the winner in both rounds.
        winner = "B_WIN" if "KnowledgeDigest 候选是 B" in prompt else "A_WIN"
        dimensions = {
            key: {"verdict": winner, "reason": "专门答案页更清楚且有原始证据"}
            for key in ("route", "taxonomy", "business-answer", "page-type", "Reader-Audit")
        }
        return json.dumps({"projection_id": "Q-TEST", "dimensions": dimensions, "blocking_risks": []}, ensure_ascii=False)


def _projection() -> QualityProjection:
    return QualityProjection(
        projection_id="Q-TEST",
        case_id="case",
        page_type="operation",
        projection_key="case.operation",
        title="操作答案",
        question="如何完成操作？",
        axes={"product": "产品", "module": "模块", "object": "对象", "scene": "场景", "boundary": "边界"},
        source_paths=("产品/操作.md",),
        source_block_refs=("产品/操作.md#L1-L2::步骤",),
        required_claims=(),
        required_boundaries=(),
        guidance="",
        repair_guidance="",
        forbidden_literals=(),
        reader_markers=(),
    )


def test_comparison_requires_two_swapped_rounds_and_can_release(tmp_path: Path):
    companybrain = tmp_path / "companybrain"
    companybrain.mkdir()
    baseline_file = companybrain / "answer.md"
    baseline_file.write_text("# CompanyBrain\n旧答案", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps({
            "entries": [{
                "baseline_id": "cb-1",
                "relative_path": "answer.md",
                "content_hash": __import__("hashlib").sha256(baseline_file.read_bytes()).hexdigest(),
                "projection_keys": ["Q-TEST"],
                "applicability": "present",
            }]
        }),
        encoding="utf-8",
    )

    model = _FakeModel()
    result = compare_quality(
        projections=(_projection(),),
        page_payloads={"Q-TEST": {
            "text": "---\npage_type: operation\n---\n# 操作答案\n可执行步骤",
            "home_text": "[操作答案](products/p/operation/answer.md)",
            "audit_text": "Audit.md#evidence-qev",
        }},
        companybrain_root=companybrain,
        baseline_path=baseline,
        raw_evidence={"Q-TEST": [{"block_ref": "产品/操作.md#L1-L2::步骤", "text": "第一步\n第二步"}]},
        model=model,
    )

    assert result["verdict"] == "released"
    assert result["publication_status"] == "released"
    assert result["dimension_verdicts"]["Q-TEST"]["DIM-01.route"] == ["KD_WIN", "KD_WIN"]
    assert len(result["provider_trace"]) == 2
    assert model.calls == 2
