from __future__ import annotations

from pathlib import Path

from knowledge_digest.task5_runtime import _raw_coordinate_map, _snd_artifacts, _snd_classify, _verify_snd_certificate


def test_coordinate_map_preserves_non_overlapping_raw_offsets(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.md").write_bytes("第一行\n\n第二行\n".encode("utf-8"))
    rows = [{"source_id": "s1", "relative_path": "a.md", "raw_hash": "raw", "evidence_ids": ["e1", "e2"]}]
    evidence = [
        {"evidence_id": "e1", "start_line": 1, "end_line": 1},
        {"evidence_id": "e2", "start_line": 3, "end_line": 3},
    ]
    result = _raw_coordinate_map(raw, rows, evidence, "snapshot")
    blocks = result["sources"][0]["blocks"]
    assert blocks[0]["raw_byte_start"] == 0
    assert blocks[0]["raw_byte_end"] < blocks[1]["raw_byte_start"]
    assert result["coverage"]["complete"]


def test_coordinate_map_accepts_frozen_known_empty_whitespace_source(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "empty.md").write_bytes(b"  \n  ")
    rows = [{"source_id": "s-empty", "relative_path": "empty.md", "status": "known_empty"}]

    result = _raw_coordinate_map(raw, rows, [], "snapshot")

    assert result["sources"][0]["blocks"] == []
    assert result["coverage"]["complete"] is True


def test_snd_descriptive_error_mention_is_not_an_operational_rule():
    classification, triggers, actions = _snd_classify(
        "逻辑明确,可控,不会出现不可预知的错误；交互较好。"
    )
    assert classification == "no_rule"
    assert "错误" in triggers
    assert actions == []


def test_snd_trigger_without_descriptive_context_stays_ambiguous():
    classification, triggers, actions = _snd_classify("系统发生错误")
    assert classification == "ambiguous"
    assert "错误" in triggers
    assert actions == []


def test_snd_trigger_with_action_remains_an_operational_rule():
    classification, triggers, actions = _snd_classify("发生错误后检查日志并重试")
    assert classification == "rule"
    assert "错误" in triggers
    assert "检查" in actions


def test_snd_verifier_rejects_tampered_block_result(tmp_path):
    raw = tmp_path / "raw"
    source_path = raw / "GoInsight" / "17  智能搭建.md"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("发生错误后检查日志并重试\n", encoding="utf-8")
    rows = [{"source_id": "src-snd-test", "relative_path": "GoInsight/17  智能搭建.md", "evidence_ids": ["src-snd-test-e0001"]}]
    evidence = [{"evidence_id": "src-snd-test-e0001", "source_id": "src-snd-test", "start_line": 1, "end_line": 1}]
    certificate = _snd_artifacts(raw, rows, evidence, "snapshot")
    certificate["per_block_results"][0]["classification"] = "no_rule"
    receipt = _verify_snd_certificate(
        certificate=certificate,
        certificate_sha256="a" * 64,
        raw=raw,
        rows=rows,
        evidence_rows=evidence,
        source_manifest_id="snapshot",
        material_id="material",
    )
    assert receipt["status"] == "unknown"
    assert receipt["failure_code"] == "block_result_mismatch"
