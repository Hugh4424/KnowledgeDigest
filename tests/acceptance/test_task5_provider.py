from __future__ import annotations

import json

import pytest

from knowledge_digest.task5_provider import config_identity, redact_identity
from knowledge_digest.providers import ProviderError


def _config(path, *, llm_model="qwen3.8"):
    path.write_text(json.dumps({
        "llm": {"base_url": "https://dashscope.in.whatspos.cn/v1", "model": llm_model, "api_key": "test"},
        "embedding": {"base_url": "https://llm.paxszapp.com/v1", "model": "jina-embeddings", "expected_dimension": 1024, "api_key": "test"},
    }), encoding="utf-8")


def test_task5_provider_identity_is_secret_free(tmp_path):
    path = tmp_path / "config.json"
    _config(path)
    identity = config_identity(path)
    assert identity["llm_model"] == "qwen3.8"
    assert "api_key" not in identity
    assert identity["llm_endpoint"] == "https://dashscope.in.whatspos.cn/v1"
    assert identity["embedding_endpoint"] == "https://llm.paxszapp.com/v1"
    assert identity["config_sha256"]
    assert identity["embedding_dimension"] == "1024"


def test_public_provider_identity_drops_paths_and_secrets():
    public = redact_identity({
        "config_path": "/Users/Hugh/.config/knowledge-digest/config.json",
        "api_key": "do-not-publish",
        "llm_model": "qwen3.8",
        "embedding_model": "jina-embeddings",
        "config_sha256": "a" * 64,
    })
    assert public == {
        "llm_model": "qwen3.8",
        "embedding_model": "jina-embeddings",
        "config_sha256": "a" * 64,
    }


def test_task5_provider_rejects_wrong_endpoint_or_model(tmp_path):
    path = tmp_path / "config.json"
    _config(path, llm_model="not-approved")
    with pytest.raises(ProviderError, match="approved Qwen"):
        config_identity(path)
