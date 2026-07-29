from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from knowledge_digest.corpus_isolation import (
    cleanup_disposable_corpus,
    prepare_disposable_corpus,
    tree_manifest,
)
from knowledge_digest.errors import ValidationError
from knowledge_digest.gold import freeze_confirmed_gold


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_prepare_corpus_copies_markdown_only_and_binds_read_only_inputs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    kb = tmp_path / "kb"
    disposable = tmp_path / "owned" / "corpus"
    source.mkdir()
    kb.mkdir()
    (source / "a.md").write_text("private alpha", encoding="utf-8")
    (source / "nested").mkdir()
    (source / "nested" / "b.MD").write_text("private beta", encoding="utf-8")
    (source / "skip.txt").write_text("private excluded", encoding="utf-8")
    (kb / "page.md").write_text("formal knowledge", encoding="utf-8")
    source_before = tree_manifest(source)
    kb_before = tree_manifest(kb)

    result = prepare_disposable_corpus(source, kb, disposable)

    assert result["markdown_count"] == 2
    assert result["excluded_non_markdown_count"] == 1
    assert [row["path"] for row in result["copy_manifest"]["files"]] == [
        "a.md",
        "nested/b.MD",
    ]
    assert result["source_markdown_manifest"] == result["copy_manifest"]
    assert result["corpus_hash"] == result["copy_manifest"]["manifest_hash"]
    assert tree_manifest(source) == source_before
    assert tree_manifest(kb) == kb_before
    serialized = json.dumps(result, sort_keys=True)
    assert "private alpha" not in serialized
    assert "formal knowledge" not in serialized

    cleanup = cleanup_disposable_corpus(disposable, result)
    assert cleanup["cleanup_complete"] is True
    assert not disposable.exists()
    assert tree_manifest(source) == source_before
    assert tree_manifest(kb) == kb_before


def test_prepare_corpus_rejects_relative_or_overlapping_roots(tmp_path: Path) -> None:
    source = tmp_path / "source"
    kb = tmp_path / "kb"
    source.mkdir()
    kb.mkdir()
    with pytest.raises(ValidationError):
        prepare_disposable_corpus(Path("relative"), kb, tmp_path / "copy")
    with pytest.raises(ValidationError):
        prepare_disposable_corpus(source, kb, source / "copy")


def test_gold_requires_per_item_decisions_and_complete_identity(tmp_path: Path) -> None:
    draft = tmp_path / "draft.jsonl"
    decisions = tmp_path / "decisions.jsonl"
    output = tmp_path / "confirmed.json"
    audit = tmp_path / "gold-confirmation-audit.json"
    common = {
        "lineage_id": "lineage-a",
        "content_identity": hashlib.sha256(b"source-a").hexdigest(),
        "stage": "S2",
        "stratum": {"relation": "mergeable", "similarity_band": "high"},
        "ai_label": "positive",
        "label_version": "v1",
        "left_ref": "a.md",
        "right_ref": "b.md",
        "right_root": "corpus",
        "query_id": "query-a",
        "gold_action": None,
    }
    _write_jsonl(
        draft,
        [
            {"case_id": "case-a", **common},
            {"case_id": "case-b", **{**common, "lineage_id": "lineage-b"}},
        ],
    )
    _write_jsonl(decisions, [{"case_id": "case-a", "decision": "confirm"}])
    with pytest.raises(ValidationError, match="decision"):
        freeze_confirmed_gold(draft, decisions, output, audit)
    assert not output.exists()
    assert not audit.exists()

    _write_jsonl(
        decisions,
        [
            {"case_id": "case-a", "decision": "confirm"},
            {"case_id": "case-b", "decision": "reject"},
        ],
    )
    result = freeze_confirmed_gold(draft, decisions, output, audit)
    assert result["unconfirmed_count"] == 0
    assert [case["case_id"] for case in result["cases"]] == ["case-a"]
    audit_data = json.loads(audit.read_text(encoding="utf-8"))
    assert audit_data["unconfirmed_count"] == 0
    assert audit_data["decisions"] == [
        {
            "case_id": "case-a",
            "content_identity": common["content_identity"],
            "decision": "confirm",
            "lineage_id": "lineage-a",
        },
        {
            "case_id": "case-b",
            "content_identity": common["content_identity"],
            "decision": "reject",
            "lineage_id": "lineage-b",
        },
    ]
    assert "ai_label" not in json.dumps(audit_data)


def test_gold_rejects_batch_defaults_duplicate_decisions_and_bad_identity(tmp_path: Path) -> None:
    draft = tmp_path / "draft.jsonl"
    decisions = tmp_path / "decisions.jsonl"
    row = {
        "case_id": "case-a",
        "lineage_id": "lineage-a",
        "content_identity": "not-a-sha",
        "stage": "S3",
        "stratum": {"action": "new", "target_in_top_k": False},
        "ai_label": "negative",
        "label_version": "v1",
        "left_ref": "a.md",
        "right_ref": "page.md",
        "right_root": "kb",
        "query_id": "query-a",
        "gold_action": "new",
    }
    _write_jsonl(draft, [row])
    _write_jsonl(decisions, [{"case_id": "*", "decision": "confirm"}])
    with pytest.raises(ValidationError):
        freeze_confirmed_gold(
            draft,
            decisions,
            tmp_path / "confirmed.json",
            tmp_path / "audit.json",
        )


@pytest.mark.parametrize(("stage", "right_root"), [("S2", "kb"), ("S3", "corpus")])
def test_gold_binds_stage_to_the_only_valid_right_root(
    tmp_path: Path, stage: str, right_root: str
) -> None:
    draft = tmp_path / "draft.jsonl"
    decisions = tmp_path / "decisions.jsonl"
    _write_jsonl(
        draft,
        [{
            "case_id": "case-a",
            "lineage_id": "lineage-a",
            "content_identity": hashlib.sha256(b"identity").hexdigest(),
            "stage": stage,
            "stratum": (
                {"relation": "mergeable", "similarity_band": "high"}
                if stage == "S2"
                else {"action": "new", "target_in_top_k": False}
            ),
            "ai_label": "positive" if stage == "S2" else "negative",
            "label_version": "v1",
            "left_ref": "a.md",
            "right_ref": "same-name.md",
            "right_root": right_root,
            "query_id": "query-a",
            "gold_action": None if stage == "S2" else "new",
        }],
    )
    _write_jsonl(decisions, [{"case_id": "case-a", "decision": "confirm"}])
    with pytest.raises(ValidationError, match=f"{stage} requires"):
        freeze_confirmed_gold(
            draft,
            decisions,
            tmp_path / "confirmed.json",
            tmp_path / "audit.json",
        )
