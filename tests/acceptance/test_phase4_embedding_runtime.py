from __future__ import annotations

import hashlib
import json
import math
import ssl
from pathlib import Path
from urllib.request import HTTPSHandler, ProxyHandler

import pytest

from knowledge_digest.calibration import build_calibration_result
from knowledge_digest.calibration_artifact import (
    load_calibration_artifact,
    validate_calibration_artifact,
)
from knowledge_digest.cli import DEFAULT_CONFIG_PATH, build_parser
from knowledge_digest.config import resolve_settings
from knowledge_digest.embedding import (
    BackendResolution,
    EmbeddingBatchError,
    EmbeddingError,
    OpenAIEmbeddingClient,
    normalize_endpoint_identity,
    resolve_similarity_backend,
    validate_vector_cache_entry,
    vector_cache_entry,
)
from knowledge_digest.paths import DigestPaths
from knowledge_digest.pipeline import _run_similarity_stages, _write_similarity_audit
from knowledge_digest.text_similarity import EmbeddingScorer


def test_digest_cli_defaults_to_project_embedding_config() -> None:
    args = build_parser().parse_args(["new", "kb"])
    assert args.config == DEFAULT_CONFIG_PATH
    assert json.loads(args.config.read_text(encoding="utf-8"))["similarity"]["backend"] == "embedding"


def _settings(path: Path, payload: dict[str, object]):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return resolve_settings(
        path,
        top_k=None,
        high=None,
        medium=None,
        max_lines=None,
        page_match_threshold=None,
    )


def _valid_artifact(endpoint: str, *, adopted: bool = True) -> dict[str, object]:
    cases: list[dict[str, object]] = []
    for split in ("calibration", "holdout"):
        strata = [
            (
                "S2",
                "positive" if relation == "mergeable" else "negative",
                {"relation": relation, "similarity_band": band},
            )
            for relation in ("mergeable", "not_mergeable")
            for band in ("high", "medium", "low")
        ] + [
            (
                "S3",
                "positive" if target else "negative",
                {"action": action, "target_in_top_k": target},
            )
            for action in ("new", "revise", "merge_multiple")
            for target in (False, True)
        ]
        for index, (stage, label, stratum) in enumerate(strata):
            case_id = f"{split}-{stage}-{index}"
            positive = label == "positive"
            jaccard_correct = not adopted or positive
            cases.append(
                {
                    "case_id": case_id,
                    "lineage_id": f"lineage-{case_id}",
                    "content_identity": hashlib.sha256(case_id.encode()).hexdigest(),
                    "label_version": "v1",
                    "stage": stage,
                    "label": label,
                    "stratum": stratum,
                    "confirmed": True,
                    "gold_action": stratum.get("action"),
                    "split": split,
                    "query_id": case_id,
                    "gold_case_hash": hashlib.sha256(
                        f"{case_id}:gold".encode()
                    ).hexdigest(),
                    "vector_manifest_hash": "e" * 64,
                    "vector_hashes": {
                        "left": hashlib.sha256(f"{case_id}:left".encode()).hexdigest(),
                        "right": hashlib.sha256(f"{case_id}:right".encode()).hexdigest(),
                    },
                    "scores": {
                        "jaccard": 0.7 if positive else 0.3,
                        "embedding": 0.9 if positive else 0.1,
                    },
                    "outcomes": {
                        "jaccard": {
                            "correct": jaccard_correct,
                            "error": not jaccard_correct,
                        },
                        "embedding": {"correct": True, "error": False},
                    },
                }
            )
    result = build_calibration_result(cases)
    ordered = sorted(cases, key=lambda item: str(item["case_id"]))
    canonical = lambda item: json.dumps(
        item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    value: dict[str, object] = {
        "schema_version": "calibration-artifact.v1",
        "adoption_status": result["adoption_status"],
        "endpoint_identity": endpoint,
        "model": "embed-model",
        "dimension": 3,
        "probe_fingerprint": "a" * 64,
        "corpus_hash": "b" * 64,
        "gold_hash": hashlib.sha256(
            canonical([case["gold_case_hash"] for case in ordered])
        ).hexdigest(),
        "split_hash": hashlib.sha256(
            canonical(
                [
                    {
                        "case_id": case["case_id"],
                        "lineage_id": case["lineage_id"],
                        "split": case["split"],
                    }
                    for case in ordered
                ]
            )
        ).hexdigest(),
        "vectors_hash": "e" * 64,
        "metrics": result["metrics"],
        "cases": result["cases"],
        "tool_version": "0.1.0",
    }
    if result["adoption_status"] == "adopted":
        value["thresholds"] = result["thresholds"]
    validate_calibration_artifact(value)
    return value


def test_default_is_jaccard_and_does_not_construct_client(tmp_path: Path) -> None:
    settings = _settings(tmp_path / "config.json", {})
    called = False

    def factory(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("client must not be constructed")

    resolved = resolve_similarity_backend(settings, client_factory=factory)
    assert resolved.effective_backend == "jaccard"
    assert resolved.reason_code == "explicit_jaccard"
    assert called is False


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        ("http://127.0.0.1:7777/v1", "http://127.0.0.1:7777/v1"),
        ("https://[::1]:8443/v1/", "https://[::1]:8443/v1"),
        ("https://llm.paxszapp.com/v1", "https://llm.paxszapp.com:443/v1"),
    ],
)
def test_endpoint_allowlist(base_url: str, expected: str) -> None:
    assert normalize_endpoint_identity(base_url) == expected


@pytest.mark.parametrize(
    "base_url",
    [
        "http://llm.paxszapp.com/v1",
        "https://llm.paxszapp.com:444/v1",
        "https://example.com/v1",
        "http://192.168.1.20:7777/v1",
        "https://llm.paxszapp.com/v2",
        "https://llm.paxszapp.com/v1?query=1",
        "https://llm.paxszapp.com/v1#fragment",
        "https://user:secret@llm.paxszapp.com/v1",
    ],
)
def test_endpoint_allowlist_rejects_unapproved_addresses(base_url: str) -> None:
    with pytest.raises(ValueError):
        normalize_endpoint_identity(base_url)


def test_client_disables_proxies_redirects_and_tls_downgrade(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path / "config.json",
        {
            "similarity": {
                "backend": "jaccard",
                "embedding": {
                    "base_url": "https://llm.paxszapp.com/v1",
                    "model": "embed-model",
                    "expected_dimension": 3,
                    "calibration_artifact": str(tmp_path / "artifact.json"),
                    "api_key_env": "KD_EMBEDDING_KEY",
                },
            }
        },
    )
    assert settings.similarity.embedding is not None
    client = OpenAIEmbeddingClient(settings.similarity.embedding)
    https = next(
        handler for handler in client._opener.handlers if isinstance(handler, HTTPSHandler)
    )
    redirect = next(
        handler
        for handler in client._opener.handlers
        if type(handler).__name__ == "_RejectRedirects"
    )
    assert not any(
        isinstance(handler, ProxyHandler) for handler in client._opener.handlers
    )
    assert https._context.verify_mode == ssl.CERT_REQUIRED
    assert https._context.check_hostname is True
    with pytest.raises(EmbeddingError, match="redirect rejected"):
        redirect.redirect_request(None, None, 302, "redirect", {}, "https://example.com")


def test_tls_failure_and_cache_evidence_never_expose_api_key(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path / "config.json",
        {
            "similarity": {
                "backend": "jaccard",
                "embedding": {
                    "base_url": "https://llm.paxszapp.com/v1",
                    "model": "embed-model",
                    "expected_dimension": 3,
                    "calibration_artifact": str(tmp_path / "artifact.json"),
                    "api_key_env": "KD_EMBEDDING_KEY",
                },
            }
        },
    )
    assert settings.similarity.embedding is not None
    secret = "super-secret"
    client = OpenAIEmbeddingClient(settings.similarity.embedding, api_key=secret)

    class InvalidCertificate:
        def open(self, *_args, **_kwargs):
            raise ssl.SSLCertVerificationError("certificate verify failed")

    client._opener = InvalidCertificate()
    with pytest.raises(EmbeddingError) as caught:
        client.embed(["company text"])
    assert "SSLCertVerificationError" in str(caught.value)
    assert secret not in str(caught.value)
    cache = vector_cache_entry(
        "company text",
        [1.0, 0.0, 0.0],
        endpoint_identity=client.endpoint_identity,
        model=client.model,
        dimension=client.dimension,
        probe_fingerprint="a" * 64,
    )
    assert secret not in json.dumps(cache)


def test_embedding_requires_matching_adopted_artifact(
    tmp_path: Path,
) -> None:
    endpoint = "https://llm.paxszapp.com:443/v1"
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(json.dumps(_valid_artifact(endpoint)), encoding="utf-8")
    settings = _settings(
        tmp_path / "config.json",
        {
            "similarity": {
                "backend": "embedding",
                "embedding": {
                    "base_url": "https://llm.paxszapp.com/v1",
                    "model": "embed-model",
                    "expected_dimension": 3,
                    "calibration_artifact": str(artifact_path),
                    "api_key_env": "KD_EMBEDDING_KEY",
                },
            }
        },
    )
    resolved = resolve_similarity_backend(
        settings,
        env={"KD_EMBEDDING_KEY": "super-secret"},
        probe_fingerprint="a" * 64,
        client_factory=lambda *_args, **_kwargs: object(),
    )
    assert resolved.effective_backend == "embedding"
    assert resolved.reason_code == "adopted_artifact_match"
    assert "super-secret" not in repr(resolved)


def test_not_adopted_artifact_falls_back_without_client(tmp_path: Path) -> None:
    endpoint = "http://127.0.0.1:7777/v1"
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(
        json.dumps(_valid_artifact(endpoint, adopted=False)), encoding="utf-8"
    )
    settings = _settings(
        tmp_path / "config.json",
        {
            "similarity": {
                "backend": "embedding",
                "embedding": {
                    "base_url": endpoint,
                    "model": "embed-model",
                    "expected_dimension": 3,
                    "calibration_artifact": str(artifact_path),
                    "api_key_env": "KD_EMBEDDING_KEY",
                },
            }
        },
    )
    resolved = resolve_similarity_backend(
        settings,
        probe_fingerprint="a" * 64,
        client_factory=lambda *_args, **_kwargs: pytest.fail("must not construct client"),
    )
    assert resolved.effective_backend == "jaccard"
    assert resolved.reason_code == "artifact_not_adopted"


def test_missing_artifact_falls_back_without_client(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path / "config.json",
        {
            "similarity": {
                "backend": "embedding",
                "embedding": {
                    "base_url": "http://127.0.0.1:7777/v1",
                    "model": "embed-model",
                    "expected_dimension": 3,
                    "calibration_artifact": str(tmp_path / "missing.json"),
                    "api_key_env": "KD_EMBEDDING_KEY",
                },
            }
        },
    )
    resolved = resolve_similarity_backend(
        settings,
        client_factory=lambda *_args, **_kwargs: pytest.fail("must not construct client"),
    )
    assert resolved.effective_backend == "jaccard"
    assert resolved.reason_code == "artifact_missing_or_invalid"


def test_artifact_schema_is_exact(tmp_path: Path) -> None:
    payload = _valid_artifact("http://127.0.0.1:7777/v1")
    payload["unknown"] = True
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_calibration_artifact(path)


@pytest.mark.parametrize(
    ("changed", "reason"),
    [
        ({"base_url": "http://127.0.0.1:8888/v1"}, "artifact_identity_mismatch"),
        ({"model": "other-model"}, "artifact_identity_mismatch"),
        ({"expected_dimension": 4}, "artifact_identity_mismatch"),
    ],
)
def test_artifact_and_probe_identity_mismatches_are_explicit(
    tmp_path: Path, changed: dict[str, object], reason: str
) -> None:
    endpoint = "http://127.0.0.1:7777/v1"
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(json.dumps(_valid_artifact(endpoint)), encoding="utf-8")
    embedding = {
        "base_url": endpoint,
        "model": "embed-model",
        "expected_dimension": 3,
        "calibration_artifact": str(artifact_path),
        "api_key_env": "KD_EMBEDDING_KEY",
        **changed,
    }
    settings = _settings(
        tmp_path / "config.json",
        {"similarity": {"backend": "embedding", "embedding": embedding}},
    )
    resolved = resolve_similarity_backend(
        settings,
        probe_fingerprint="a" * 64,
        client_factory=lambda *_args, **_kwargs: object(),
    )
    assert resolved.reason_code == reason
    assert resolved.effective_backend == "jaccard"


def test_probe_fingerprint_mismatch_is_explicit(tmp_path: Path) -> None:
    endpoint = "http://127.0.0.1:7777/v1"
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(json.dumps(_valid_artifact(endpoint)), encoding="utf-8")
    settings = _settings(
        tmp_path / "config.json",
        {
            "similarity": {
                "backend": "embedding",
                "embedding": {
                    "base_url": endpoint,
                    "model": "embed-model",
                    "expected_dimension": 3,
                    "calibration_artifact": str(artifact_path),
                    "api_key_env": "KD_EMBEDDING_KEY",
                },
            }
        },
    )
    resolved = resolve_similarity_backend(
        settings,
        probe_fingerprint="f" * 64,
        client_factory=lambda *_args, **_kwargs: object(),
    )
    assert resolved.reason_code == "probe_identity_mismatch"


def test_batch_response_must_be_complete_unique_finite_and_nonzero() -> None:
    valid = {
        "data": [
            {"index": 1, "embedding": [0.0, 1.0, 0.0]},
            {"index": 0, "embedding": [1.0, 0.0, 0.0]},
        ]
    }
    assert OpenAIEmbeddingClient.validate_response(valid, count=2, dimension=3) == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]
    invalid = [
        {"data": [{"index": 0, "embedding": [1.0, 0.0, 0.0]}]},
        {"data": [{"index": 0, "embedding": [1.0, 0.0, 0.0]}, {"index": 0, "embedding": [0.0, 1.0, 0.0]}]},
        {"data": [{"index": 0, "embedding": [math.nan, 0.0, 0.0]}, {"index": 1, "embedding": [0.0, 1.0, 0.0]}]},
        {"data": [{"index": 0, "embedding": [1.0, 0.0]}, {"index": 1, "embedding": [0.0, 1.0, 0.0]}]},
        {"data": [{"index": 0, "embedding": [True, 0.0, 0.0]}, {"index": 1, "embedding": [0.0, 1.0, 0.0]}]},
        {"data": [{"index": 0, "embedding": [0.0, 0.0, 0.0]}, {"index": 1, "embedding": [0.0, 1.0, 0.0]}]},
    ]
    for response in invalid:
        with pytest.raises(EmbeddingBatchError):
            OpenAIEmbeddingClient.validate_response(response, count=2, dimension=3)


def test_embedding_requests_use_bounded_batches_and_fail_before_overlong_input() -> None:
    class Client(OpenAIEmbeddingClient):
        def __init__(self) -> None:
            self.calls: list[list[str]] = []

        def _embed_batch(self, texts: list[str]) -> list[list[float]]:
            self.calls.append(texts)
            if len(self.calls) == 2 and texts == ["FAIL"]:
                raise EmbeddingError("second batch failed")
            return [[1.0] for _ in texts]

    client = Client()
    assert len(client.embed(["x"] * 9)) == 9
    assert [len(batch) for batch in client.calls] == [8, 1]

    client.calls.clear()
    assert len(client.embed(["x" * 40_000, "y" * 30_001])) == 2
    assert [len(batch) for batch in client.calls] == [1, 1]

    client.calls.clear()
    assert client.embed(["x" * 70_000]) == [[1.0]]
    with pytest.raises(EmbeddingBatchError, match="character limit"):
        client.embed(["valid", "x" * 70_001])
    assert client.calls == [["x" * 70_000]]

    client.calls.clear()
    with pytest.raises(EmbeddingError, match="second batch"):
        client.embed(["x"] * 8 + ["FAIL"])
    assert [len(batch) for batch in client.calls] == [8, 1]


def test_s3_embedding_failure_discards_decisions_and_restarts_from_s2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kb_dir = tmp_path / "kb"
    (kb_dir / "pages").mkdir(parents=True)
    (kb_dir / "pages" / "a.md").write_text("shared topic page one", encoding="utf-8")
    (kb_dir / "pages" / "b.md").write_text("target page two", encoding="utf-8")
    run_dir = tmp_path / "run"
    paths = DigestPaths(tmp_path, tmp_path, kb_dir, kb_dir / "kb.structure.md")
    raw_items = [
        {"raw_id": "r1", "text": "shared topic one", "source_uri": "s1"},
        {"raw_id": "r2", "text": "shared topic two", "source_uri": "s2"},
    ]

    class Client:
        def __init__(self):
            self.calls = 0
            self.endpoint_identity = "http://127.0.0.1:7777/v1"
            self.model = "embed-model"
            self.dimension = 3

        def embed(self, texts: list[str]) -> list[list[float]]:
            self.calls += 1
            return [[1.0, float(index + 1), 0.5] for index, _ in enumerate(texts)]

    class FailsInsideRetrieve(EmbeddingScorer):
        def score(self, left: str, right: str) -> float:
            if right == "target page two":
                raise EmbeddingBatchError("forced failure inside S3 retrieve")
            return super().score(left, right)

    client = Client()
    mode = {"backend": "embedding"}
    monkeypatch.setattr(
        "knowledge_digest.pipeline.resolve_similarity_backend",
        lambda _settings: (
            BackendResolution(
                "embedding",
                "embedding",
                "adopted_artifact_match",
                client=client,
                probe_fingerprint="a" * 64,
            )
            if mode["backend"] == "embedding"
            else BackendResolution("jaccard", "jaccard", "explicit_jaccard")
        ),
    )
    monkeypatch.setattr("knowledge_digest.pipeline.EmbeddingScorer", FailsInsideRetrieve)
    settings = _settings(tmp_path / "config.json", {})
    clusters, decisions, audit = _run_similarity_stages(
        raw_items, run_dir, paths, ("pages", "_archive", "_queues"), settings
    )
    assert audit["effective_backend"] == "jaccard"
    assert audit["fallback_restarted_from"] == "S2"
    assert audit["cache"]["entries"] >= 2
    assert clusters
    assert decisions
    assert (run_dir / "embedding-cache.jsonl").is_file()
    assert not (kb_dir / "_queues").exists()
    persisted = [
        json.loads(line)
        for line in (run_dir / "s3" / "evolution-decisions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert persisted == decisions
    mode["backend"] = "jaccard"
    expected_clusters, expected_decisions, _ = _run_similarity_stages(
        raw_items,
        tmp_path / "expected",
        paths,
        ("pages", "_archive", "_queues"),
        settings,
    )
    assert clusters == expected_clusters
    assert decisions == expected_decisions


def test_s2_embedding_score_failure_restarts_with_only_jaccard_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kb_dir = tmp_path / "kb"
    (kb_dir / "pages").mkdir(parents=True)
    (kb_dir / "pages" / "target.md").write_text("alpha target page", encoding="utf-8")
    paths = DigestPaths(tmp_path, tmp_path, kb_dir, kb_dir / "kb.structure.md")
    raw_items = [
        {"raw_id": "r1", "text": "alpha shared one", "source_uri": "s1"},
        {"raw_id": "r2", "text": "alpha shared two", "source_uri": "s2"},
    ]

    class Client:
        endpoint_identity = "http://127.0.0.1:7777/v1"
        model = "embed-model"
        dimension = 3

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, float(index + 1), 0.5] for index, _ in enumerate(texts)]

    class FailsInsideS2(EmbeddingScorer):
        def score(self, left: str, right: str) -> float:
            raise EmbeddingBatchError("forced failure inside S2 clustering")

    mode = {"backend": "embedding"}
    monkeypatch.setattr(
        "knowledge_digest.pipeline.resolve_similarity_backend",
        lambda _settings: (
            BackendResolution(
                "embedding",
                "embedding",
                "adopted_artifact_match",
                client=Client(),
                probe_fingerprint="a" * 64,
            )
            if mode["backend"] == "embedding"
            else BackendResolution("jaccard", "jaccard", "explicit_jaccard")
        ),
    )
    monkeypatch.setattr("knowledge_digest.pipeline.EmbeddingScorer", FailsInsideS2)
    settings = _settings(tmp_path / "config.json", {})
    run_dir = tmp_path / "run"
    clusters, decisions, audit = _run_similarity_stages(
        raw_items, run_dir, paths, ("pages", "_archive", "_queues"), settings
    )
    assert audit["effective_backend"] == "jaccard"
    assert audit["fallback_restarted_from"] == "S2"
    assert (run_dir / "embedding-cache.jsonl").is_file()
    mode["backend"] = "jaccard"
    expected_clusters, expected_decisions, _ = _run_similarity_stages(
        raw_items,
        tmp_path / "expected",
        paths,
        ("pages", "_archive", "_queues"),
        settings,
    )
    assert clusters == expected_clusters
    assert decisions == expected_decisions
    persisted_clusters = [
        json.loads(line)
        for line in (run_dir / "s2" / "clusters.jsonl").read_text().splitlines()
    ]
    assert persisted_clusters == clusters
    assert not (kb_dir / "_queues").exists()


def test_similarity_audit_is_written_on_early_report_exit(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps({"similarity": {"reason_code": "not_resolved"}}),
        encoding="utf-8",
    )
    audit = {
        "requested_backend": "embedding",
        "effective_backend": "jaccard",
        "reason_code": "embedding_run_failed",
        "fallback_restarted_from": "S2",
    }
    _write_similarity_audit(report, audit)
    assert json.loads(report.read_text(encoding="utf-8"))["similarity"] == audit


def test_similarity_audit_updates_report_to_effective_thresholds(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "settings": {
                    "high": 0.9,
                    "medium": 0.8,
                    "page_match_threshold": 0.15,
                }
            }
        ),
        encoding="utf-8",
    )
    thresholds = {
        "high": 0.79,
        "medium": 0.79,
        "page_match_threshold": 0.35,
    }
    _write_similarity_audit(
        report,
        {
            "requested_backend": "embedding",
            "effective_backend": "embedding",
            "reason_code": "adopted_artifact_match",
            "effective_thresholds": thresholds,
        },
    )
    persisted = json.loads(report.read_text(encoding="utf-8"))
    assert {key: persisted["settings"][key] for key in thresholds} == thresholds
    assert persisted["similarity"]["effective_thresholds"] == thresholds


def test_probe_failure_falls_back_before_s2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kb_dir = tmp_path / "kb"
    (kb_dir / "pages").mkdir(parents=True)
    paths = DigestPaths(tmp_path, tmp_path, kb_dir, kb_dir / "kb.structure.md")
    monkeypatch.setattr(
        "knowledge_digest.pipeline.resolve_similarity_backend",
        lambda _settings: (_ for _ in ()).throw(EmbeddingBatchError("probe down")),
    )
    settings = _settings(tmp_path / "config.json", {})
    clusters, decisions, audit = _run_similarity_stages(
        [{"raw_id": "r1", "text": "some useful text", "source_uri": "s1"}],
        tmp_path / "run",
        paths,
        ("pages", "_archive", "_queues"),
        settings,
    )
    assert clusters
    assert decisions
    assert audit["effective_backend"] == "jaccard"
    assert audit["reason_code"] == "embedding_probe_failed"
    assert audit["fallback_restarted_from"] == "S2"


def test_identity_bound_vector_cache_is_reused(tmp_path: Path) -> None:
    class Client:
        endpoint_identity = "http://127.0.0.1:7777/v1"
        model = "embed-model"
        dimension = 3

        def __init__(self):
            self.calls = 0

        def embed(self, texts):
            self.calls += 1
            return [[1.0, float(index + 1), 0.0] for index, _ in enumerate(texts)]

    cache = tmp_path / "vectors.jsonl"
    first = Client()
    EmbeddingScorer(first, "a" * 64, cache).prefetch(["one", "two"])
    assert first.calls == 1
    second = Client()
    scorer = EmbeddingScorer(second, "a" * 64, cache)
    scorer.prefetch(["one", "two"])
    assert second.calls == 0
    assert scorer.cache_stats["hits"] == 2


def test_vector_cache_rejects_every_identity_mismatch() -> None:
    entry = vector_cache_entry(
        "cache text",
        [1.0, 0.0, 0.0],
        endpoint_identity="http://127.0.0.1:7777/v1",
        model="embed-model",
        dimension=3,
        probe_fingerprint="a" * 64,
    )
    bindings = {
        "endpoint_identity": "http://127.0.0.1:8888/v1",
        "model": "other-model",
        "dimension": 4,
        "probe_fingerprint": "c" * 64,
        "input_hash": "d" * 64,
    }
    expected = {
        "endpoint_identity": "http://127.0.0.1:7777/v1",
        "model": "embed-model",
        "dimension": 3,
        "probe_fingerprint": "a" * 64,
        "input_hash": hashlib.sha256(b"cache text").hexdigest(),
    }
    assert validate_vector_cache_entry(entry, **expected) == [1.0, 0.0, 0.0]
    for field, changed in bindings.items():
        assert (
            validate_vector_cache_entry(entry, **{**expected, field: changed}) is None
        )
