from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from knowledge_digest.calibration_artifact import load_calibration_artifact
from knowledge_digest.config import resolve_settings
from knowledge_digest.embedding import (
    BackendResolution,
    EmbeddingBatchError,
    OpenAIEmbeddingClient,
    normalize_endpoint_identity,
    resolve_similarity_backend,
)
from knowledge_digest.paths import DigestPaths
from knowledge_digest.pipeline import _run_similarity_stages
from knowledge_digest.text_similarity import EmbeddingScorer


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


def _artifact(endpoint: str, *, status: str = "adopted") -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "calibration-artifact.v1",
        "adoption_status": status,
        "endpoint_identity": endpoint,
        "model": "embed-model",
        "dimension": 3,
        "probe_fingerprint": "a" * 64,
        "corpus_hash": "b" * 64,
        "gold_hash": "c" * 64,
        "split_hash": "d" * 64,
        "vectors_hash": "e" * 64,
        "metrics": {"feature_separation": {}},
        "cases": [],
        "tool_version": "0.1.0",
    }
    if status == "adopted":
        value["thresholds"] = {
            "high": 0.9,
            "medium": 0.8,
            "page_match_threshold": 0.2,
        }
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
        "https://example.com/v1",
        "https://llm.paxszapp.com/v2",
        "https://user:secret@llm.paxszapp.com/v1",
    ],
)
def test_endpoint_allowlist_rejects_unapproved_addresses(base_url: str) -> None:
    with pytest.raises(ValueError):
        normalize_endpoint_identity(base_url)


def test_embedding_requires_matching_adopted_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    endpoint = "https://llm.paxszapp.com:443/v1"
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(json.dumps(_artifact(endpoint)), encoding="utf-8")
    class BoundArtifact:
        adoption_status = "adopted"

        def __getitem__(self, key: str):
            return _artifact(endpoint)[key]

    monkeypatch.setattr(
        "knowledge_digest.embedding.load_calibration_artifact",
        lambda _path: BoundArtifact(),
    )
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
    artifact_path.write_text(json.dumps(_artifact(endpoint, status="not_adopted")), encoding="utf-8")
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
    assert resolved.reason_code == "artifact_missing_or_invalid"


def test_artifact_schema_is_exact(tmp_path: Path) -> None:
    payload = _artifact("http://127.0.0.1:7777/v1")
    payload["unknown"] = True
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_calibration_artifact(path)


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
        {"data": [{"index": 0, "embedding": [0.0, 0.0, 0.0]}, {"index": 1, "embedding": [0.0, 1.0, 0.0]}]},
    ]
    for response in invalid:
        with pytest.raises(EmbeddingBatchError):
            OpenAIEmbeddingClient.validate_response(response, count=2, dimension=3)


def test_s3_embedding_failure_discards_decisions_and_restarts_from_s2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kb_dir = tmp_path / "kb"
    (kb_dir / "pages").mkdir(parents=True)
    (kb_dir / "pages" / "target.md").write_text("shared topic target", encoding="utf-8")
    run_dir = tmp_path / "run"
    paths = DigestPaths(tmp_path, tmp_path, kb_dir, kb_dir / "kb.structure.md")
    raw_items = [
        {"raw_id": "r1", "text": "shared topic one", "source_uri": "s1"},
        {"raw_id": "r2", "text": "shared topic two", "source_uri": "s2"},
    ]

    class FailsOnRetrieve:
        def __init__(self):
            self.calls = 0
            self.endpoint_identity = "http://127.0.0.1:7777/v1"
            self.model = "embed-model"
            self.dimension = 3

        def embed(self, texts: list[str]) -> list[list[float]]:
            self.calls += 1
            if self.calls >= 2:
                raise EmbeddingBatchError("forced S3 failure")
            return [[1.0, float(index + 1), 0.5] for index, _ in enumerate(texts)]

    client = FailsOnRetrieve()
    monkeypatch.setattr(
        "knowledge_digest.pipeline.resolve_similarity_backend",
        lambda _settings: BackendResolution(
            "embedding",
            "embedding",
            "adopted_artifact_match",
            client=client,
            probe_fingerprint="a" * 64,
        ),
    )
    settings = _settings(tmp_path / "config.json", {})
    clusters, decisions, audit = _run_similarity_stages(
        raw_items, run_dir, paths, ("pages", "_archive", "_queues"), settings
    )
    assert audit["effective_backend"] == "jaccard"
    assert audit["fallback_restarted_from"] == "S2"
    assert clusters
    assert decisions
    persisted = [
        json.loads(line)
        for line in (run_dir / "s3" / "evolution-decisions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert persisted == decisions


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
