"""Task5 provider boundary.

This module is intentionally small: transport and credential loading remain in
``providers.py``.  Task5 adds the frozen identity checks needed before a real
run can consume raw or CompanyBrain bytes; it never returns a credential.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .providers import Embedder, ProviderError, SemanticModel, build_providers, load_provider_config


LLM_ENDPOINT = "https://dashscope.in.whatspos.cn/v1"
APPROVED_LLM_MODELS = frozenset({"qwen3.8"})
EMBEDDING_ENDPOINT = "https://llm.paxszapp.com/v1"
EMBEDDING_MODEL = "jina-embeddings"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def config_identity(path: Path) -> dict[str, str]:
    """Return only stable, non-secret config identity."""

    path = Path(path).expanduser()
    config = load_provider_config(path)
    llm = config.llm
    embedding = config.embedding
    llm_endpoint = str(llm.get("base_url", "")).rstrip("/")
    embedding_endpoint = str(embedding.get("base_url", "")).rstrip("/")
    model = str(llm.get("model", ""))
    embedding_model = str(embedding.get("model", ""))
    if llm_endpoint != LLM_ENDPOINT or model not in APPROVED_LLM_MODELS:
        raise ProviderError("Task5 provider identity does not match approved Qwen endpoint/model")
    if embedding_endpoint != EMBEDDING_ENDPOINT or embedding_model != EMBEDDING_MODEL:
        raise ProviderError("Task5 provider identity does not match approved Jina endpoint/model")
    return {
        "config_path": str(path),
        "config_sha256": sha256_bytes(path.read_bytes()),
        "llm_endpoint": llm_endpoint,
        "llm_model": model,
        "embedding_endpoint": embedding_endpoint,
        "embedding_model": embedding_model,
        "embedding_dimension": str(embedding.get("expected_dimension", embedding.get("dimension", "1024"))),
        "retry_attempts": str(max(int(llm.get("retry_attempts", 0)), int(embedding.get("retry_attempts", 0)))),
    }


def build_task5_providers(path: Path) -> tuple[SemanticModel, Embedder, dict[str, str]]:
    """Build the real adapters only after identity validation."""

    identity = config_identity(path)
    model, embedder = build_providers(path)
    return model, embedder, identity


def redact_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    """Copy a provider identity while dropping accidental secret-like keys."""

    forbidden = {"api_key", "authorization", "token", "secret", "password", "config_path"}
    return {
        str(key): value
        for key, value in identity.items()
        if str(key).casefold() not in forbidden
        and "key" not in str(key).casefold()
        and "path" not in str(key).casefold()
        and not (isinstance(value, str) and value.startswith("/"))
    }


__all__ = [
    "APPROVED_LLM_MODELS",
    "EMBEDDING_ENDPOINT",
    "EMBEDDING_MODEL",
    "LLM_ENDPOINT",
    "build_task5_providers",
    "config_identity",
    "redact_identity",
    "sha256_bytes",
]
