"""The two external seams used by the small KnowledgeDigest compiler.

The compiler knows nothing about HTTP, headers, credentials, or provider JSON.
This module has exactly two production adapters: Qwen for semantic writing and
Jina for routing embeddings.  Tests can replace either adapter with a fixed
in-memory implementation.
"""

from __future__ import annotations

import json
import math
import os
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


class ProviderError(RuntimeError):
    """A provider could not produce a trustworthy result."""


class ProviderConfigError(ProviderError):
    """Provider configuration cannot be used for this run."""


class SemanticModel(Protocol):
    identity: Mapping[str, str]
    calls: int

    def generate(self, prompt: str) -> str:
        """Return one JSON document or raise ProviderError."""


class Embedder(Protocol):
    identity: Mapping[str, str]
    calls: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one non-zero vector per input or raise ProviderError."""


@dataclass(frozen=True)
class ProviderConfig:
    llm: Mapping[str, Any]
    embedding: Mapping[str, Any]
    budget: Mapping[str, Any]


_APPROVED_LLM_ENDPOINT = "https://dashscope.in.whatspos.cn/v1"
_APPROVED_LLM_MODELS = frozenset({"qwen3.8"})
_APPROVED_EMBEDDING_ENDPOINT = "https://llm.paxszapp.com/v1"
_APPROVED_EMBEDDING_MODEL = "jina-embeddings"


# Qwen may need close to a minute to produce a complete evidence-bound JSON
# page.  Keep the configured 300-second ceiling instead of turning a valid
# long response into a false provider failure.  Connection setup is bounded
# separately below, so an unreachable endpoint still fails quickly.
_MAX_PROVIDER_TIMEOUT_SECONDS = 300.0


class CallBudget:
    """One shared hard limit for all LLM and embedding requests in a run."""

    def __init__(self, limit: int):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ProviderError("budget.max_provider_calls must be greater than zero")
        self.limit = limit
        self._used = 0
        self._used_by_kind: dict[str, int] = {}
        self._lock = threading.Lock()

    @property
    def used(self) -> int:
        with self._lock:
            return self._used

    @property
    def used_by_kind(self) -> dict[str, int]:
        """Return every reserved attempt, including failed and retried calls."""

        with self._lock:
            return dict(self._used_by_kind)

    def reserve(self, kind: str) -> None:
        with self._lock:
            if self._used >= self.limit:
                raise ProviderError(f"provider call budget exceeded before {kind} request: {self.limit}")
            self._used += 1
            self._used_by_kind[kind] = self._used_by_kind.get(kind, 0) + 1


def load_provider_config(path: Path) -> ProviderConfig:
    """Load the user-owned config file without ever exposing credentials."""

    path = Path(path).expanduser()
    if path.is_symlink() or not path.is_file():
        raise ProviderConfigError(f"provider config is missing or not a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProviderConfigError(f"provider config is invalid: {path} ({error})") from error
    if not isinstance(value, dict):
        raise ProviderConfigError("provider config must be a JSON object")
    llm = value.get("llm")
    embedding = value.get("embedding")
    if not isinstance(llm, dict) or not isinstance(embedding, dict):
        raise ProviderConfigError("provider config needs llm and embedding objects")
    llm_endpoint = str(llm.get("base_url", "")).rstrip("/")
    embedding_endpoint = str(embedding.get("base_url", "")).rstrip("/")
    if llm_endpoint != _APPROVED_LLM_ENDPOINT or str(llm.get("model", "")) not in _APPROVED_LLM_MODELS:
        raise ProviderConfigError("provider config does not use an approved Qwen endpoint/model")
    if embedding_endpoint != _APPROVED_EMBEDDING_ENDPOINT or str(embedding.get("model", "")) != _APPROVED_EMBEDDING_MODEL:
        raise ProviderConfigError("provider config does not use an approved Jina endpoint/model")
    if str(llm.get("api_format", "openai")) != "openai":
        raise ProviderConfigError("LLM api_format must be openai")
    for kind, section in (("LLM", llm), ("embedding", embedding)):
        retry_attempts = section.get("retry_attempts", 0)
        if isinstance(retry_attempts, bool) or not isinstance(retry_attempts, int) or retry_attempts != 0:
            raise ProviderConfigError(f"{kind} retry_attempts must be 0")
    # A few users kept the key at the root while migrating the file.  A root
    # key is only a compatibility input; it is never copied to any output.
    root_key = value.get("api_key")
    if isinstance(root_key, str) and root_key.strip():
        llm = dict(llm)
        embedding = dict(embedding)
        llm.setdefault("api_key", root_key.strip())
        embedding.setdefault("api_key", root_key.strip())
    budget = value.get("budget", {})
    if not isinstance(budget, dict):
        raise ProviderConfigError("provider config budget must be an object")
    raw_limit = budget.get("max_provider_calls", 180)
    if isinstance(raw_limit, bool) or not isinstance(raw_limit, int) or raw_limit <= 0:
        raise ProviderConfigError("budget.max_provider_calls must be greater than zero")
    return ProviderConfig(llm=llm, embedding=embedding, budget=budget)


def _required_text(section: Mapping[str, Any], name: str) -> str:
    value = section.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ProviderError(f"provider config field is missing: {name}")
    return value.strip()


def _api_key(section: Mapping[str, Any], *, kind: str) -> str:
    """Resolve a provider credential without changing the public identity.

    The user-owned config file is the primary source.  ``api_key_env`` is
    only a compatibility fallback for older installations; an environment
    value never overrides a direct key in the config file.
    """

    direct = section.get("api_key")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    env_name = section.get("api_key_env")
    if isinstance(env_name, str) and env_name.strip():
        value = os.environ.get(env_name.strip())
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ProviderError(f"{kind} provider credential is missing")


def _timeout(section: Mapping[str, Any], default: float) -> float:
    value = section.get("timeout_seconds", default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ProviderError("provider timeout_seconds must be greater than zero")
    return min(float(value), _MAX_PROVIDER_TIMEOUT_SECONDS)


def _retry_attempts(section: Mapping[str, Any]) -> int:
    value = section.get("retry_attempts", 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProviderError("provider retry_attempts must be a non-negative integer")
    return value


def _endpoint(base_url: str, suffix: str) -> str:
    root = base_url.rstrip("/")
    if not root.endswith("/v1"):
        root += "/v1"
    return f"{root}/{suffix.lstrip('/')}"


def _curl_response(request: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    """Run one bounded HTTP request through curl's real wall-clock timeout."""

    command = [
        "curl",
        "--silent",
        "--show-error",
        "--http1.1",
        "--max-time",
        f"{timeout:.3f}",
        "--connect-timeout",
        f"{min(10.0, timeout):.3f}",
        "--write-out",
        "\n__KNOWLEDGEDIGEST_HTTP_STATUS__%{http_code}",
        "--request",
        request.get_method(),
        request.full_url,
    ]
    # Keep credentials out of argv/process listings.  Curl reads headers from
    # its stdin config while the request body is held in a short-lived 0600
    # file, so neither secrets nor source text appear in the command line.
    def quote_config(value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

    config_lines = [f"header = {quote_config(f'{name}: {value}')}" for name, value in request.header_items()]
    body_path: str | None = None
    if request.data is not None:
        descriptor, body_path = tempfile.mkstemp(prefix="knowledge-digest-", suffix=".body")
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as body:
                body.write(request.data)
        except BaseException:
            os.close(descriptor)
            raise
        command.extend(("--data-binary", f"@{body_path}"))
    command.extend(("--config", "-"))
    try:
        try:
            completed = subprocess.run(
                command,
                input=("\n".join(config_lines) + "\n").encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 5,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("curl wall-clock timeout") from error
    finally:
        if body_path is not None:
            try:
                os.unlink(body_path)
            except FileNotFoundError:
                pass
    if completed.returncode == 28:
        raise TimeoutError("curl wall-clock timeout")
    if completed.returncode != 0:
        raise OSError(f"curl exited {completed.returncode}")
    marker = b"\n__KNOWLEDGEDIGEST_HTTP_STATUS__"
    if marker not in completed.stdout:
        raise OSError("curl response is missing HTTP status")
    body, raw_status = completed.stdout.rsplit(marker, 1)
    try:
        status = int(raw_status.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as error:
        raise OSError("curl response has an invalid HTTP status") from error
    return status, body


def _response_json(
    request: urllib.request.Request,
    timeout: float,
    budget: CallBudget | None = None,
    kind: str = "provider",
    retry_attempts: int = 0,
) -> Any:
    """Read one provider response with a hard per-attempt wall-clock limit."""

    last_error: Exception | None = None
    for attempt in range(retry_attempts + 1):
        if budget is not None:
            budget.reserve(kind)
        try:
            status, body = _curl_response(request, timeout)
            if not 200 <= int(status) < 300:
                if status not in {408, 429, 500, 502, 503, 504} or attempt == retry_attempts:
                    raise ProviderError(f"provider returned HTTP {status}")
                last_error = ProviderError(f"provider returned HTTP {status}")
                time.sleep(0.5 * (attempt + 1))
                continue
            return json.loads(body.decode("utf-8"))
        except (TimeoutError, socket.timeout) as error:
            # A read timeout is already a complete attempt. Retrying it three
            # times would make a single stalled page block the whole run for
            # many minutes and hide the real provider failure.
            raise ProviderError("provider request timed out") from error
        except OSError as error:
            if isinstance(getattr(error, "reason", None), (TimeoutError, socket.timeout)):
                raise ProviderError("provider request timed out") from error
            if attempt == retry_attempts:
                raise ProviderError(f"provider request failed: {type(error).__name__}") from error
            last_error = error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProviderError(f"provider response is invalid: {type(error).__name__}") from error
        time.sleep(0.5 * (attempt + 1))
    raise ProviderError(f"provider request failed: {type(last_error).__name__ if last_error else 'unknown'}")


def _content(payload: Any) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError("LLM response has no choices[0].message.content") from error
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        joined = "".join(str(part) for part in parts).strip()
        if joined:
            return joined
    raise ProviderError("LLM response content is empty")


class QwenAdapter:
    """OpenAI-compatible Qwen adapter, configured from the user JSON file."""

    def __init__(self, section: Mapping[str, Any], budget: CallBudget | None = None):
        self._base_url = _required_text(section, "base_url")
        self._model = _required_text(section, "model")
        self._api_key = _api_key(section, kind="LLM")
        self._timeout = _timeout(section, 300)
        self._retry_attempts = _retry_attempts(section)
        raw_max_tokens = section.get("max_tokens", 12_288)
        if isinstance(raw_max_tokens, bool) or not isinstance(raw_max_tokens, int) or raw_max_tokens <= 0:
            raise ProviderError("LLM max_tokens must be greater than zero")
        # The compiler emits five typed sections plus evidence bindings.  A
        # 4096-token implicit cap truncated long source pages into invalid
        # JSON; keep the user's max_tokens as the ceiling while allowing a
        # complete response unless they explicitly set output_token_cap.
        raw_output_cap = section.get("output_token_cap", 8_192)
        if isinstance(raw_output_cap, bool) or not isinstance(raw_output_cap, int) or raw_output_cap <= 0:
            raise ProviderError("LLM output_token_cap must be greater than zero")
        raw_input_limit = section.get("max_input_chars", 120_000)
        if isinstance(raw_input_limit, bool) or not isinstance(raw_input_limit, int) or raw_input_limit <= 0:
            raise ProviderError("LLM max_input_chars must be greater than zero")
        # A large configured ceiling is useful for other callers, but Reader
        # pages are deliberately short.  The cap is a product readability
        # policy and can be raised explicitly in the user config when needed.
        self._max_tokens = min(raw_max_tokens, raw_output_cap)
        self._max_input_chars = raw_input_limit
        self._budget = budget
        self._calls = 0
        self._lock = threading.Lock()
        self.identity = {"base_url": self._base_url, "model": self._model, "api_format": str(section.get("api_format", "openai"))}

    @property
    def calls(self) -> int:
        # A failed/timeout request is still an observed provider attempt. The
        # shared budget is the source of truth when it is present, including
        # retry attempts that never reach the successful-response increment.
        budget_calls = self._budget.used_by_kind.get("LLM", 0) if self._budget is not None else 0
        return max(self._calls, budget_calls)

    @property
    def budget(self) -> CallBudget | None:
        return self._budget

    @property
    def retry_attempts(self) -> int:
        return self._retry_attempts

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ProviderError("LLM prompt is empty")
        if len(prompt) > self._max_input_chars:
            raise ProviderError("LLM prompt exceeds max_input_chars")
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": self._max_tokens,
            "response_format": {"type": "json_object"},
        }
        # These fields are accepted by the configured Qwen OpenAI bridge and
        # prevent hidden reasoning from consuming the JSON response budget.
        if self._model.lower().startswith("qwen"):
            payload["enable_thinking"] = False
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        request = urllib.request.Request(
            _endpoint(self._base_url, "chat/completions"),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"},
            method="POST",
        )
        result = _content(_response_json(request, self._timeout, self._budget, "LLM", self._retry_attempts))
        with self._lock:
            self._calls += 1
        return result


class JinaAdapter:
    """OpenAI-compatible Jina embedding adapter."""

    def __init__(self, section: Mapping[str, Any], budget: CallBudget | None = None):
        self._base_url = _required_text(section, "base_url")
        self._model = _required_text(section, "model")
        self._api_key = _api_key(section, kind="embedding")
        raw_dimension = section.get("expected_dimension", section.get("dimension", 1024))
        if isinstance(raw_dimension, bool) or not isinstance(raw_dimension, int) or raw_dimension <= 0:
            raise ProviderError("embedding expected_dimension must be greater than zero")
        self._dimension = raw_dimension
        self._timeout = _timeout(section, 180)
        self._retry_attempts = _retry_attempts(section)
        self._calls = 0
        self._budget = budget
        self._lock = threading.Lock()
        self.identity = {"base_url": self._base_url, "model": self._model, "dimension": str(self._dimension)}

    @property
    def calls(self) -> int:
        budget_calls = self._budget.used_by_kind.get("embedding", 0) if self._budget is not None else 0
        return max(self._calls, budget_calls)

    @property
    def budget(self) -> CallBudget | None:
        return self._budget

    @property
    def retry_attempts(self) -> int:
        return self._retry_attempts

    def _batch(self, texts: Sequence[str]) -> list[list[float]]:
        payload = {"model": self._model, "input": list(texts)}
        request = urllib.request.Request(
            _endpoint(self._base_url, "embeddings"),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"},
            method="POST",
        )
        value = _response_json(request, self._timeout, self._budget, "embedding", self._retry_attempts)
        if not isinstance(value, dict) or not isinstance(value.get("data"), list):
            raise ProviderError("embedding response has invalid shape")
        ordered: dict[int, list[float]] = {}
        for row in value["data"]:
            if not isinstance(row, dict) or not isinstance(row.get("index"), int) or isinstance(row.get("index"), bool):
                raise ProviderError("embedding response index is invalid")
            vector = row.get("embedding")
            index = row["index"]
            if index in ordered or not isinstance(vector, list) or len(vector) != self._dimension:
                raise ProviderError("embedding response is partial or has the wrong dimension")
            if any(isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(float(item)) for item in vector):
                raise ProviderError("embedding response contains a non-finite value")
            numbers = [float(item) for item in vector]
            if not any(numbers):
                raise ProviderError("embedding response contains a zero vector")
            ordered[index] = numbers
        if set(ordered) != set(range(len(texts))):
            raise ProviderError("embedding response indexes are incomplete")
        with self._lock:
            self._calls += 1
        return [ordered[index] for index in range(len(texts))]

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ProviderError("embedding input contains an empty text")
        result: list[list[float]] = []
        for start in range(0, len(texts), 8):
            result.extend(self._batch(texts[start : start + 8]))
        return result


def build_providers(path: Path) -> tuple[QwenAdapter, JinaAdapter]:
    try:
        config = load_provider_config(path)
    except ProviderConfigError:
        raise
    except ProviderError as error:
        # File/schema/allowlist validation is preflight, not transport.
        raise ProviderConfigError(f"provider config is invalid: {error}") from error
    raw_limit = config.budget.get("max_provider_calls", 180)
    budget = CallBudget(raw_limit)
    try:
        return QwenAdapter(config.llm, budget), JinaAdapter(config.embedding, budget)
    except ProviderConfigError:
        raise
    except ProviderError as error:
        # Adapter construction is still preflight: missing credentials,
        # malformed timeout/token limits, and other section-level problems
        # must not be reported as a remote transport outage.
        raise ProviderConfigError(f"provider config is invalid: {error}") from error


__all__ = [
    "Embedder",
    "CallBudget",
    "JinaAdapter",
    "ProviderError",
    "ProviderConfigError",
    "QwenAdapter",
    "SemanticModel",
    "build_providers",
    "load_provider_config",
]
