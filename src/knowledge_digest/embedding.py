"""Approved-endpoint embedding client and fail-closed runtime resolver."""

from __future__ import annotations

import hashlib
import json
import math
import os
import ssl
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)

from .calibration_artifact import load_calibration_artifact
from .config import DigestSettings, EmbeddingSettings


class EmbeddingError(RuntimeError):
    pass


class EmbeddingBatchError(EmbeddingError):
    pass


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise EmbeddingError("embedding redirect rejected")


def normalize_endpoint_identity(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("embedding endpoint contains forbidden URL components")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("embedding endpoint must be HTTP(S)")
    host = parsed.hostname.lower()
    try:
        loopback = ip_address(host).is_loopback
    except ValueError:
        loopback = False
    path = parsed.path.rstrip("/")
    if path != "/v1":
        raise ValueError("embedding base path must be /v1")
    if loopback:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    else:
        if parsed.scheme != "https" or host != "llm.paxszapp.com" or (parsed.port or 443) != 443:
            raise ValueError("embedding endpoint is not approved")
        port = 443
    netloc_host = f"[{host}]" if ":" in host else host
    return urlunsplit((parsed.scheme, f"{netloc_host}:{port}", path, "", ""))


class OpenAIEmbeddingClient:
    def __init__(self, settings: EmbeddingSettings, *, api_key: str | None = None, timeout: float | None = None):
        self.endpoint_identity = normalize_endpoint_identity(settings.base_url)
        self.model = settings.model
        self.dimension = settings.expected_dimension
        self._api_key = api_key
        if timeout is None:
            timeout_text = os.environ.get("KD_EMBEDDING_TIMEOUT_SECONDS")
            try:
                timeout = float(timeout_text) if timeout_text is not None else 180.0
            except ValueError as error:
                raise EmbeddingError("KD_EMBEDDING_TIMEOUT_SECONDS must be numeric") from error
        if timeout <= 0:
            raise EmbeddingError("KD_EMBEDDING_TIMEOUT_SECONDS must be greater than zero")
        self._timeout = timeout
        context = ssl.create_default_context()
        self._opener = build_opener(ProxyHandler({}), _RejectRedirects(), HTTPSHandler(context=context))

    @staticmethod
    def validate_response(value: Any, *, count: int, dimension: int) -> list[list[float]]:
        if not isinstance(value, dict) or not isinstance(value.get("data"), list):
            raise EmbeddingBatchError("embedding response has invalid shape")
        data = value["data"]
        if len(data) != count:
            raise EmbeddingBatchError("embedding response count mismatch")
        ordered: dict[int, list[float]] = {}
        for row in data:
            if not isinstance(row, dict) or isinstance(row.get("index"), bool) or not isinstance(row.get("index"), int):
                raise EmbeddingBatchError("embedding response index invalid")
            index = row["index"]
            vector = row.get("embedding")
            if index in ordered or not isinstance(vector, list) or len(vector) != dimension:
                raise EmbeddingBatchError("embedding response is partial, duplicate, or wrong dimension")
            if any(isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(float(item)) for item in vector):
                raise EmbeddingBatchError("embedding response contains non-finite values")
            normalized = [float(item) for item in vector]
            if not any(item != 0.0 for item in normalized):
                raise EmbeddingBatchError("embedding response contains a zero vector")
            ordered[index] = normalized
        if set(ordered) != set(range(count)):
            raise EmbeddingBatchError("embedding response indexes are incomplete")
        return [ordered[index] for index in range(count)]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        request = Request(f"{self.endpoint_identity}/embeddings", data=body, headers=headers, method="POST")
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                if response.geturl() != request.full_url:
                    raise EmbeddingError("embedding redirect rejected")
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise EmbeddingError(f"embedding request failed ({type(error).__name__})") from error
        return self.validate_response(payload, count=len(texts), dimension=self.dimension)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed every input in bounded batches; publish nothing on partial failure."""
        if not texts:
            return []
        if any(len(text) > 70_000 for text in texts):
            raise EmbeddingBatchError("embedding input exceeds batch character limit")
        batches: list[list[str]] = []
        current: list[str] = []
        current_chars = 0
        for text in texts:
            if current and (len(current) >= 8 or current_chars + len(text) > 70_000):
                batches.append(current)
                current = []
                current_chars = 0
            current.append(text)
            current_chars += len(text)
        if current:
            batches.append(current)
        vectors: list[list[float]] = []
        for batch in batches:
            vectors.extend(self._embed_batch(batch))
        return vectors

    def probe_fingerprint(self) -> str:
        vector = self.embed(["KnowledgeDigest embedding identity probe"])[0]
        canonical = json.dumps(vector, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_CACHE_FIELDS = {
    "schema_version",
    "endpoint_identity",
    "model",
    "dimension",
    "probe_fingerprint",
    "input_hash",
    "vector",
}


def validate_vector_cache_entry(
    value: Any,
    *,
    endpoint_identity: str,
    model: str,
    dimension: int,
    probe_fingerprint: str,
    input_hash: str | None = None,
) -> list[float] | None:
    """Return a valid bound vector, otherwise treat the entry as a cache miss."""
    if not isinstance(value, dict) or set(value) != _CACHE_FIELDS:
        return None
    if (
        value.get("schema_version") != "vector-cache-entry.v1"
        or value.get("endpoint_identity") != endpoint_identity
        or value.get("model") != model
        or value.get("dimension") != dimension
        or value.get("probe_fingerprint") != probe_fingerprint
        or (input_hash is not None and value.get("input_hash") != input_hash)
    ):
        return None
    input_hash = value.get("input_hash")
    vector = value.get("vector")
    if (
        not isinstance(input_hash, str)
        or len(input_hash) != 64
        or not isinstance(vector, list)
        or len(vector) != dimension
        or any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(float(item))
            for item in vector
        )
        or not any(float(item) != 0.0 for item in vector)
    ):
        return None
    return [float(item) for item in vector]


def vector_cache_entry(
    text: str,
    vector: list[float],
    *,
    endpoint_identity: str,
    model: str,
    dimension: int,
    probe_fingerprint: str,
) -> dict[str, Any]:
    value = {
        "schema_version": "vector-cache-entry.v1",
        "endpoint_identity": endpoint_identity,
        "model": model,
        "dimension": dimension,
        "probe_fingerprint": probe_fingerprint,
        "input_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "vector": vector,
    }
    if validate_vector_cache_entry(
        value,
        endpoint_identity=endpoint_identity,
        model=model,
        dimension=dimension,
        probe_fingerprint=probe_fingerprint,
        input_hash=value["input_hash"],
    ) is None:
        raise ValueError("invalid vector cache entry")
    return value


@dataclass(frozen=True)
class BackendResolution:
    requested_backend: str
    effective_backend: str
    reason_code: str
    artifact_path: str | None = None
    client: Any | None = None
    thresholds: dict[str, float] | None = None
    probe_fingerprint: str | None = None


def resolve_similarity_backend(
    settings: DigestSettings,
    *,
    env: dict[str, str] | None = None,
    probe_fingerprint: str | None = None,
    client_factory: Callable[..., Any] = OpenAIEmbeddingClient,
) -> BackendResolution:
    similarity = settings.similarity
    if similarity.backend == "jaccard":
        return BackendResolution("jaccard", "jaccard", "explicit_jaccard")
    embedding = similarity.embedding
    if embedding is None:
        return BackendResolution("embedding", "jaccard", "embedding_config_missing")
    try:
        endpoint = normalize_endpoint_identity(embedding.base_url)
    except ValueError:
        return BackendResolution("embedding", "jaccard", "endpoint_not_approved")
    try:
        artifact = load_calibration_artifact(embedding.calibration_artifact)
    except ValueError:
        return BackendResolution("embedding", "jaccard", "artifact_missing_or_invalid")
    if artifact.adoption_status != "adopted":
        return BackendResolution("embedding", "jaccard", "artifact_not_adopted")
    if (
        artifact["endpoint_identity"] != endpoint
        or artifact["model"] != embedding.model
        or artifact["dimension"] != embedding.expected_dimension
    ):
        return BackendResolution("embedding", "jaccard", "artifact_identity_mismatch")
    source = os.environ if env is None else env
    api_key = source.get(embedding.api_key_env)
    client = client_factory(embedding, api_key=api_key)
    actual_probe = probe_fingerprint if probe_fingerprint is not None else client.probe_fingerprint()
    if actual_probe != artifact["probe_fingerprint"]:
        return BackendResolution("embedding", "jaccard", "probe_identity_mismatch")
    return BackendResolution(
        "embedding",
        "embedding",
        "adopted_artifact_match",
        str(embedding.calibration_artifact),
        client,
        {key: float(value) for key, value in artifact["thresholds"].items()},
        actual_probe,
    )
