from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


def _write_config(path):
    path.write_text(
        json.dumps(
            {
                "llm": {
                    "base_url": "https://dashscope.in.whatspos.cn/v1",
                    "model": "qwen3.8",
                    "api_key": "llm-test-key",
                    "timeout_seconds": 30,
                },
                "embedding": {
                    "base_url": "https://llm.paxszapp.com/v1",
                    "model": "jina-embeddings",
                    "api_key": "embedding-test-key",
                    "expected_dimension": 1024,
                    "timeout_seconds": 30,
                },
                "budget": {"max_provider_calls": 2},
            }
        ),
        encoding="utf-8",
    )


def test_build_providers_shares_one_hard_budget(tmp_path):
    from knowledge_digest.providers import build_providers

    config = tmp_path / "config.json"
    _write_config(config)
    model, embedder = build_providers(config)

    assert model.budget is embedder.budget
    assert model.budget.limit == 2
    model.budget.reserve("test")
    embedder.budget.reserve("test")
    with pytest.raises(RuntimeError, match="provider call budget exceeded"):
        model.budget.reserve("test")


def test_provider_timeout_is_one_bounded_attempt(monkeypatch):
    from knowledge_digest.providers import CallBudget, ProviderError, QwenAdapter

    attempts = 0

    def timeout(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        raise subprocess.TimeoutExpired(kwargs.get("args", args[0] if args else "curl"), 1)

    monkeypatch.setattr("knowledge_digest.providers.subprocess.run", timeout)
    budget = CallBudget(3)
    model = QwenAdapter(
        {
            "base_url": "https://dashscope.in.whatspos.cn/v1",
            "model": "qwen3.8",
            "api_key": "test-key",
            "timeout_seconds": 1,
        },
        budget,
    )

    with pytest.raises(ProviderError, match="timed out"):
        model.generate("return an object")

    assert attempts == 1
    assert budget.used == 1
    assert model.calls == 1


def test_provider_timeout_caps_an_unbounded_user_value():
    from knowledge_digest.providers import CallBudget, QwenAdapter

    model = QwenAdapter(
        {
            "base_url": "https://dashscope.in.whatspos.cn/v1",
            "model": "qwen3.8",
            "api_key": "test-key",
            "timeout_seconds": 300,
        },
        CallBudget(1),
    )

    assert model._timeout == 300.0


def test_provider_config_rejects_retry_attempts(tmp_path):
    from knowledge_digest.providers import load_provider_config, ProviderError

    config = tmp_path / "retry-config.json"
    config.write_text(
        json.dumps({
            "llm": {
                "base_url": "https://dashscope.in.whatspos.cn/v1",
                "model": "qwen3.8",
                "api_key": "llm-test-key",
                "retry_attempts": 1,
            },
            "embedding": {
                "base_url": "https://llm.paxszapp.com/v1",
                "model": "jina-embeddings",
                "api_key": "embedding-test-key",
                "expected_dimension": 1024,
            },
        }),
        encoding="utf-8",
    )
    with pytest.raises(ProviderError, match="retry_attempts must be 0"):
        load_provider_config(config)


def test_provider_config_rejects_unapproved_task5_identity(tmp_path):
    from knowledge_digest.providers import load_provider_config, ProviderConfigError

    config = tmp_path / "identity-config.json"
    _write_config(config)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["llm"]["model"] = "some-other-model"
    config.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ProviderConfigError, match="approved Qwen endpoint/model"):
        load_provider_config(config)


def test_provider_config_rejects_qwen36_for_task5_contract(tmp_path):
    from knowledge_digest.providers import load_provider_config, ProviderConfigError

    config = tmp_path / "legacy-qwen-config.json"
    _write_config(config)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["llm"]["model"] = "qwen3.6"
    config.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ProviderConfigError, match="approved Qwen endpoint/model"):
        load_provider_config(config)


def test_provider_credentials_prefer_direct_config_key_over_environment(tmp_path, monkeypatch):
    from knowledge_digest.providers import build_providers

    config = tmp_path / "direct-key.json"
    _write_config(config)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["llm"].pop("api_key")
    value["llm"]["api_key_env"] = "KD_TEST_LLM_KEY"
    value["embedding"]["api_key_env"] = "KD_TEST_EMBEDDING_KEY"
    config.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setenv("KD_TEST_LLM_KEY", "env-llm-key")
    monkeypatch.setenv("KD_TEST_EMBEDDING_KEY", "env-embedding-key")

    model, embedder = build_providers(config)
    assert model._api_key == "env-llm-key"
    assert embedder._api_key == "embedding-test-key"
    assert "api_key" not in model.identity
    assert "api_key" not in embedder.identity


def test_provider_credentials_fail_closed_when_direct_and_environment_are_missing(tmp_path, monkeypatch):
    from knowledge_digest.providers import ProviderError, build_providers

    config = tmp_path / "missing-key.json"
    _write_config(config)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["llm"].pop("api_key")
    value["llm"]["api_key_env"] = "KD_MISSING_LLM_KEY"
    config.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.delenv("KD_MISSING_LLM_KEY", raising=False)

    with pytest.raises(ProviderError, match="LLM provider credential is missing"):
        build_providers(config)


def test_provider_configuration_failure_is_distinct_from_remote_unavailability(tmp_path, monkeypatch):
    from knowledge_digest.providers import ProviderConfigError, build_providers

    config = tmp_path / "missing-key-status.json"
    _write_config(config)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["llm"].pop("api_key")
    value["llm"].pop("api_key_env", None)
    config.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.delenv("KD_MISSING_LLM_KEY", raising=False)

    with pytest.raises(ProviderConfigError, match="LLM provider credential is missing"):
        build_providers(config)


def test_call_budget_keeps_attempt_counts_by_provider_kind():
    from knowledge_digest.providers import CallBudget

    budget = CallBudget(3)
    budget.reserve("LLM")
    budget.reserve("LLM")
    budget.reserve("embedding")

    assert budget.used == 3
    assert budget.used_by_kind == {"LLM": 2, "embedding": 1}
