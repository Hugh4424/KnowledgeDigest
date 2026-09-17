from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

import pytest

from knowledge_digest.config import DigestSettings, EmbeddingSettings
from knowledge_digest.gold import canonical_json_bytes


_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "phase4_embedding_acceptance.py"
)
_SPEC = importlib.util.spec_from_file_location("phase4_embedding_acceptance", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


@pytest.mark.parametrize(
    "changed, message",
    [
        (
            {
                "left_ref": "same.md",
                "left_hash": "a" * 64,
                "lineage_id": "other",
                "query_id": "q2",
                "gold_action": None,
            },
            "source identity",
        ),
        (
            {
                "left_ref": "other.md",
                "left_hash": "b" * 64,
                "lineage_id": "other",
                "query_id": "q1",
                "gold_action": "revise",
            },
            "query_id",
        ),
    ],
)
def test_formal_identity_bindings_are_globally_unique(
    changed: dict[str, object], message: str
) -> None:
    first = {
        "left_ref": "same.md",
        "left_hash": "a" * 64,
        "lineage_id": "lineage",
        "query_id": "q1",
        "gold_action": None,
    }
    with pytest.raises(ValueError, match=message):
        _MODULE._validate_identity_bindings([first, changed])


def test_formal_cases_are_scored_by_one_real_batch_not_trusted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = tmp_path / "copy"
    kb = tmp_path / "kb"
    corpus.mkdir()
    kb.mkdir()
    rows = []
    strata = [
        ("S2", {"relation": relation, "similarity_band": band}, relation == "mergeable")
        for relation in ("mergeable", "not_mergeable")
        for band in ("high", "medium", "low")
    ] + [
        ("S3", {"action": action, "target_in_top_k": target}, target)
        for action in ("new", "revise", "merge_multiple")
        for target in (False, True)
    ]
    for cell, (stage, stratum, positive) in enumerate(strata):
        for lineage_index in range(2):
            left = f"left-{cell}-{lineage_index}.md"
            right = f"right-{cell}-{lineage_index}.md"
            left_text = f"shared-{cell} POS"
            right_text = f"shared-{cell} POS" if positive else f"different-{cell} NEG"
            (corpus / left).write_text(left_text, encoding="utf-8")
            root = kb if stage == "S3" else corpus
            (root / right).write_text(right_text, encoding="utf-8")
            rows.append(
                {
                    "case_id": f"case-{cell}-{lineage_index}",
                    "lineage_id": f"lineage-{cell}-{lineage_index}",
                    "content_identity": hashlib.sha256(
                        (left_text + "\0" + right_text).encode()
                    ).hexdigest(),
                    "label_version": "v1",
                    "stage": stage,
                    "label": "positive" if positive else "negative",
                    "stratum": stratum,
                    "confirmed": True,
                    "gold_action": stratum.get("action"),
                    "left_ref": left,
                    "right_ref": right,
                    "right_root": "kb" if stage == "S3" else "corpus",
                    "query_id": f"query-{cell}-{lineage_index}",
                }
            )
    gold_binding = [
        hashlib.sha256(canonical_json_bytes(row)).hexdigest()
        for row in sorted(rows, key=lambda item: item["case_id"])
    ]
    raw = {
        "schema_version": "confirmed-gold.v1",
        "unconfirmed_count": 0,
        "gold_hash": hashlib.sha256(
            canonical_json_bytes(gold_binding)
        ).hexdigest(),
        "cases": rows,
    }

    class BatchClient:
        calls = 0

        def __init__(self, *_args, **_kwargs):
            pass

        def embed(self, texts):
            type(self).calls += 1
            return [
                [1.0, 0.0, 0.0] if "POS" in text else [0.0, 1.0, 0.0]
                for text in texts
            ]

    monkeypatch.setattr(_MODULE, "OpenAIEmbeddingClient", BatchClient)
    scored, gold_hash, vectors_hash, vector_manifest = _MODULE._score_real_cases(
        raw,
        disposable_corpus=corpus,
        kb_root=kb,
        settings=EmbeddingSettings(
            "http://127.0.0.1:9/v1",
            "model",
            3,
            tmp_path / "artifact.json",
            "KEY",
        ),
        env={},
        digest_settings=DigestSettings(),
    )
    assert BatchClient.calls == 1
    assert gold_hash == raw["gold_hash"]
    assert len(vectors_hash) == 64
    assert vector_manifest
    assert all(set(item) == {"root", "path_hash", "input_hash", "vector_hash"} for item in vector_manifest)
    assert hashlib.sha256(canonical_json_bytes(vector_manifest)).hexdigest() == vectors_hash
    assert all(
        row["outcomes"][backend]["predicted_tier"]
        in {"auto", "needs_review", "insufficient_signal"}
        for row in scored
        if row["stage"] == "S2"
        for backend in ("jaccard", "embedding")
    )
    assert all(
        row["outcomes"][backend]["observed_clusters"]
        for row in scored
        if row["stage"] == "S2"
        for backend in ("jaccard", "embedding")
    )
    assert all(set(row["scores"]) == {"jaccard", "embedding"} for row in scored)
    forged = json.loads(json.dumps(raw))
    forged["cases"][0]["scores"] = {"jaccard": 1.0, "embedding": 1.0}
    with pytest.raises(ValueError, match="unscored"):
        _MODULE._score_real_cases(
            forged,
            disposable_corpus=corpus,
            kb_root=kb,
            settings=EmbeddingSettings(
                "http://127.0.0.1:9/v1", "model", 3, tmp_path / "artifact.json", "KEY"
            ),
            env={},
            digest_settings=DigestSettings(),
        )


def _corpus(root: Path) -> None:
    for index in range(89):
        path = root / f"group-{index % 4}" / f"page-{index:02d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Page {index}\ncompany fact {index}\n", encoding="utf-8")
    (root / "ignored.txt").write_text("not markdown", encoding="utf-8")
    (root / "ignored.json").write_text("{}", encoding="utf-8")


def _config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "similarity": {
                    "backend": "jaccard",
                    "embedding": {
                        "base_url": "http://127.0.0.1:9/v1",
                        "model": "approved-local-model",
                        "expected_dimension": 3,
                        "calibration_artifact": str(path.parent / "not-present.json"),
                        "api_key_env": "KD_TEST_EMBEDDING_TOKEN",
                    },
                }
            }
        ),
        encoding="utf-8",
    )


def test_runner_requires_distinct_absolute_paths(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    kb = tmp_path / "kb"
    temp = tmp_path / "temp"
    evidence = tmp_path / "evidence"
    config = tmp_path / "config.json"
    for path in (corpus, kb, temp, evidence):
        path.mkdir()
    _config(config)

    with pytest.raises(ValueError, match="absolute"):
        _MODULE.validate_paths(
            Path("relative"),
            kb,
            temp,
            evidence,
            config,
        )
    with pytest.raises(ValueError, match="distinct"):
        _MODULE.validate_paths(corpus, kb, temp, temp, config)


def test_runner_rejects_nonempty_evidence_without_overwriting(tmp_path: Path) -> None:
    corpus, kb, temp, evidence = (
        tmp_path / "corpus", tmp_path / "kb", tmp_path / "temp", tmp_path / "evidence"
    )
    for path in (corpus, kb, temp, evidence):
        path.mkdir()
    _corpus(corpus)
    config = tmp_path / "config.json"
    _config(config)
    existing = evidence / "calibration-artifact.json"
    existing.write_text("preserve-me", encoding="utf-8")
    with pytest.raises(ValueError, match="evidence directory must be empty"):
        _MODULE.run_acceptance(
            corpus=corpus, kb=kb, temp_root=temp, evidence_dir=evidence, config=config
        )
    assert existing.read_text(encoding="utf-8") == "preserve-me"


def test_replay_mismatch_is_blocked_and_removes_current_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = tmp_path / "evidence"
    disposable = tmp_path / "temp" / "corpus-copy"
    kb = tmp_path / "kb"
    for path in (evidence, disposable, kb):
        path.mkdir(parents=True)
    cases = tmp_path / "gold.json"
    cases.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(_MODULE, "load_confirmed_gold", lambda _path: {"cases": []})
    monkeypatch.setattr(
        _MODULE,
        "_score_real_cases",
        lambda *_args, **_kwargs: (
            [],
            "a" * 64,
            hashlib.sha256(canonical_json_bytes([])).hexdigest(),
            [],
        ),
    )
    calls = 0
    def fake_calibration(argv):
        nonlocal calls
        calls += 1
        output = Path(argv[argv.index("--output") + 1])
        split = Path(argv[argv.index("--split-audit") + 1])
        output.write_text(
            json.dumps(
                    {
                        "adoption_status": "not_adopted",
                        "vectors_hash": hashlib.sha256(canonical_json_bytes([])).hexdigest(),
                    }
            ) + ("" if calls == 1 else " "),
            encoding="utf-8",
        )
        split.write_text("{}" + ("" if calls == 1 else " "), encoding="utf-8")
        return 0
    monkeypatch.setattr(_MODULE, "calibration_main", fake_calibration)
    result = _MODULE._default_calibrate(
        cases=cases,
        evidence_dir=evidence,
        service_identity={
            "endpoint_identity": "http://127.0.0.1:9/v1",
            "model": "model",
            "dimension": 3,
            "probe_fingerprint": "c" * 64,
        },
        corpus_hash="d" * 64,
        config=tmp_path / "config.json",
        disposable_corpus=disposable,
        formal_kb=kb,
        embedding_settings=EmbeddingSettings(
            "http://127.0.0.1:9/v1", "model", 3, tmp_path / "artifact.json", "KEY"
        ),
        digest_settings=DigestSettings(),
        env={},
    )
    assert result == {
        "result": "BLOCKED",
        "reason_code": "replay_mismatch",
        "replay_match": False,
    }
    assert not (evidence / "calibration-artifact.json").exists()
    assert not (tmp_path / "temp" / "scored-cases.json").exists()
    assert not list(evidence.glob(".replay-*"))


def test_calibration_exception_removes_every_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = tmp_path / "evidence"
    disposable = tmp_path / "temp" / "corpus-copy"
    kb = tmp_path / "kb"
    for path in (evidence, disposable, kb):
        path.mkdir(parents=True)
    cases = tmp_path / "gold.json"
    cases.write_text("{}", encoding="utf-8")
    vectors_hash = hashlib.sha256(canonical_json_bytes([])).hexdigest()
    monkeypatch.setattr(_MODULE, "load_confirmed_gold", lambda _path: {"cases": []})
    monkeypatch.setattr(
        _MODULE, "_score_real_cases", lambda *_args, **_kwargs: ([], "a" * 64, vectors_hash, [])
    )
    def fail_after_partial(argv):
        Path(argv[argv.index("--output") + 1]).write_text("partial", encoding="utf-8")
        Path(argv[argv.index("--split-audit") + 1]).write_text("partial", encoding="utf-8")
        raise RuntimeError("simulated calibration failure")
    monkeypatch.setattr(_MODULE, "calibration_main", fail_after_partial)
    with pytest.raises(RuntimeError, match="simulated"):
        _MODULE._default_calibrate(
            cases=cases, evidence_dir=evidence,
            service_identity={
                "endpoint_identity": "http://127.0.0.1:9/v1", "model": "model",
                "dimension": 3, "probe_fingerprint": "c" * 64,
            },
            corpus_hash="d" * 64, config=tmp_path / "config.json",
            disposable_corpus=disposable, formal_kb=kb,
            embedding_settings=EmbeddingSettings(
                "http://127.0.0.1:9/v1", "model", 3, tmp_path / "artifact.json", "KEY"
            ),
            digest_settings=DigestSettings(), env={},
        )
    assert not (tmp_path / "temp" / "scored-cases.json").exists()
    assert not list(evidence.iterdir())


def test_blocked_run_proves_isolation_cleanup_and_writes_no_artifact(
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "corpus"
    kb = tmp_path / "formal-kb"
    temp = tmp_path / "owned-temp"
    evidence = tmp_path / "evidence"
    config = tmp_path / "config.json"
    corpus.mkdir()
    kb.mkdir()
    temp.mkdir()
    evidence.mkdir()
    _corpus(corpus)
    (kb / "existing.md").write_text("# Formal KB\n", encoding="utf-8")
    _config(config)

    result = _MODULE.run_acceptance(
        corpus=corpus,
        kb=kb,
        temp_root=temp,
        evidence_dir=evidence,
        config=config,
        probe=lambda _settings, _env: (_ for _ in ()).throw(
            _MODULE.EmbeddingError("service unavailable")
        ),
    )

    assert result["result"] == "BLOCKED"
    assert result["reason_code"] == "embedding_service_unavailable"
    assert result["corpus"]["markdown_count"] == 89
    assert result["corpus"]["excluded_non_markdown_count"] == 2
    assert result["source_unchanged"] is True
    assert result["formal_kb_unchanged"] is True
    assert result["config_unchanged"] is True
    assert result["cleanup"]["complete"] is True
    assert result["process_ownership"]["spawned_pids"] == []
    assert result["process_ownership"]["remaining_owned_pids"] == []
    assert result["service"]["probe_kind"] == "real_endpoint_request"
    assert result["service"]["endpoint_identity"] == "http://127.0.0.1:9/v1"
    assert not any(temp.iterdir())
    assert not list(evidence.glob("*artifact*.json"))

    persisted = json.loads(
        (evidence / "real-service-acceptance.json").read_text(encoding="utf-8")
    )
    assert persisted == result
    serialized = json.dumps(persisted, ensure_ascii=False)
    assert "company fact" not in serialized
    assert "KD_TEST_EMBEDDING_TOKEN" not in serialized


def test_success_keeps_explicit_jaccard_config_and_binds_probe_identity(
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "corpus"
    kb = tmp_path / "formal-kb"
    temp = tmp_path / "owned-temp"
    evidence = tmp_path / "evidence"
    config = tmp_path / "config.json"
    for path in (corpus, kb, temp, evidence):
        path.mkdir()
    _corpus(corpus)
    _config(config)
    before = config.read_bytes()

    result = _MODULE.run_acceptance(
        corpus=corpus,
        kb=kb,
        temp_root=temp,
        evidence_dir=evidence,
        config=config,
        probe=lambda settings, _env: {
            "endpoint_identity": _MODULE.normalize_endpoint_identity(settings.base_url),
            "model": settings.model,
            "dimension": settings.expected_dimension,
            "probe_fingerprint": "a" * 64,
        },
        calibrate=lambda **kwargs: {
            "result": "not_adopted",
            "artifact": {
                "adoption_status": "not_adopted",
                "endpoint_identity": kwargs["service_identity"]["endpoint_identity"],
                "model": kwargs["service_identity"]["model"],
                "dimension": kwargs["service_identity"]["dimension"],
                "probe_fingerprint": kwargs["service_identity"]["probe_fingerprint"],
            },
            "replay_match": True,
        },
    )

    assert result["result"] == "not_adopted"
    assert result["service"]["probe_fingerprint"] == "a" * 64
    assert result["replay_match"] is True
    assert config.read_bytes() == before
    assert json.loads(config.read_text())["similarity"]["backend"] == "jaccard"
    assert result["cleanup"]["complete"] is True
