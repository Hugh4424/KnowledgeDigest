"""User-scoped provider configuration for local/private model endpoints.

The project keeps provider credentials outside the repository.  This module
loads the user-owned JSON file without ever returning secrets to evidence or
runtime reports.  Environment variables remain a compatibility fallback for
older callers and tests.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from .errors import ValidationError


PROVIDER_CONFIG_ENV = "KD_PROVIDER_CONFIG"


def default_provider_config_path(env: Mapping[str, str] | None = None) -> Path:
    source = os.environ if env is None else env
    config_root = source.get("XDG_CONFIG_HOME")
    root = Path(config_root).expanduser() if config_root else Path.home() / ".config"
    return root / "knowledge-digest" / "config.json"


def configured_provider_config_path(env: Mapping[str, str] | None = None) -> Path:
    source = os.environ if env is None else env
    raw = source.get(PROVIDER_CONFIG_ENV)
    return Path(raw).expanduser() if raw else default_provider_config_path(source)


def load_provider_config(path: Path | None) -> dict[str, Any]:
    """Load a provider file, returning an empty mapping when it is absent.

    A configured but malformed file fails loudly.  Missing files still allow
    the legacy environment fallback, which keeps offline tests and old users
    deterministic.
    """

    if path is None:
        return {}
    path = Path(path).expanduser()
    if not path.exists():
        return {}
    if path.is_symlink() or not path.is_file():
        raise ValidationError("provider-config", str(path), "provider config must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("provider-config", str(path), f"invalid JSON ({error})") from error
    if not isinstance(value, dict):
        raise ValidationError("provider-config", str(path), "provider config must contain an object")
    for section in ("llm", "embedding"):
        section_value = value.get(section)
        if section_value is not None and not isinstance(section_value, dict):
            raise ValidationError("provider-config", section, "must be an object")
    return value


def provider_section(path: Path | None, section: str) -> Mapping[str, Any]:
    value = load_provider_config(path).get(section, {})
    return value if isinstance(value, Mapping) else {}


def _configured_string(section: Mapping[str, Any], key: str) -> str:
    value = section.get(key)
    return value.strip() if isinstance(value, str) else ""


def effective_llm_environment(
    *,
    provider_config_path: Path | None,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return LLM settings with the user file taking precedence over env."""

    source = dict(os.environ if env is None else env)
    section = provider_section(provider_config_path, "llm")
    mapping = {
        "KD_LLM_FORMAT": "api_format",
        "KD_LLM_BASE_URL": "base_url",
        "KD_LLM_API_KEY": "api_key",
        "KD_LLM_MODEL": "model",
        "KD_LLM_TIMEOUT_SECONDS": "timeout_seconds",
    }
    for env_name, config_name in mapping.items():
        value = section.get(config_name)
        if value is not None and str(value).strip():
            source[env_name] = str(value).strip()
    return source


def effective_embedding_provider(
    *,
    provider_config_path: Path | None,
    base_url: str,
    model: str,
    expected_dimension: int,
    api_key_env: str,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Merge embedding identity and credential with config-first precedence."""

    source = os.environ if env is None else env
    section = provider_section(provider_config_path, "embedding")
    configured_base_url = section.get("base_url")
    configured_model = section.get("model")
    configured_dimension = section.get("expected_dimension")
    configured_key = section.get("api_key")
    return {
        "base_url": configured_base_url.strip() if isinstance(configured_base_url, str) and configured_base_url.strip() else base_url,
        "model": configured_model.strip() if isinstance(configured_model, str) and configured_model.strip() else model,
        "expected_dimension": configured_dimension if isinstance(configured_dimension, int) and not isinstance(configured_dimension, bool) else expected_dimension,
        "api_key": configured_key.strip() if isinstance(configured_key, str) and configured_key.strip() else source.get(api_key_env),
    }


def credential_source(provider_config_path: Path | None, *, env: Mapping[str, str] | None = None) -> str | None:
    """Return a report-safe credential source label; never include a key."""

    if provider_config_path is not None:
        section = provider_section(provider_config_path, "llm")
        embedding = provider_section(provider_config_path, "embedding")
        if _configured_string(section, "api_key") or _configured_string(embedding, "api_key"):
            return "config-file"
    source = os.environ if env is None else env
    if source.get("KD_LLM_API_KEY") or source.get("KD_PHASE4_EMBEDDING_KEY"):
        return "environment"
    return None


def redacted_provider_identity(path: Path | None) -> dict[str, Any]:
    """Return provider identity fields safe to bind into run metadata."""

    config = load_provider_config(path)
    identity: dict[str, Any] = {}
    for section_name, fields in (
        ("llm", ("api_format", "base_url", "model")),
        ("embedding", ("base_url", "model", "expected_dimension")),
    ):
        section = config.get(section_name)
        if not isinstance(section, Mapping):
            continue
        identity[section_name] = {
            field: section[field]
            for field in fields
            if field in section and field != "api_key"
        }
    return identity
