"""Task7 model-result cache with deterministic composite invalidation.

The cache is intentionally small and local.  It stores only JSON-serializable
provider results and the material needed to prove which input produced them;
provider credentials never enter the cache path or an entry.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any


_CACHE_FIELDS = frozenset(
    {
        "cache_key",
        "model_id",
        "prompt_version",
        "topic_map_version",
        "result",
        "created_from_fingerprint",
    }
)
_SENSITIVE_FIELD_RE = re.compile(
    r"^(?:token|secret|password|authorization|credential|"
    r"api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"auth[_-]?(?:token|key|header)|bearer[_-]?token|"
    r"private[_-]?key|client[_-]?(?:secret|key))$",
    re.IGNORECASE,
)
_MISSING = object()


class CacheIntegrityError(RuntimeError):
    """A cache read or write violated the frozen cache contract."""

    def __init__(
        self,
        message: str,
        *,
        provider_called: bool = False,
        provider_result: object | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_called = provider_called
        self.provider_result = provider_result


@dataclass(frozen=True)
class CacheResult:
    """A cache lookup result and whether a provider call was needed."""

    result: Mapping[str, Any]
    cache_key: str
    created_from_fingerprint: str
    hit: bool
    called: bool


def _read_field(value: object, name: str, default: object = _MISSING) -> object:
    if isinstance(value, Mapping):
        result = value.get(name, default)
    else:
        result = getattr(value, name, default)
    if result is _MISSING:
        raise ValueError(f"cache member is missing {name!r}")
    return result


def _optional_field(value: object, name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(name, _MISSING)
    return getattr(value, name, _MISSING)


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _member_record(member: object) -> dict[str, Any]:
    """Normalize the exact provider material consumed by the page fingerprint."""

    record: dict[str, Any] = {
        "topic_key": _required_string(_read_field(member, "topic_key"), "topic_key"),
        "source_path": _required_string(
            _read_field(member, "source_path"), "source_path"
        ),
        "content_hash": _required_string(
            _read_field(member, "content_hash"), "content_hash"
        ),
    }
    optional_strings = ("block_id", "kind", "text")
    for name in optional_strings:
        value = _optional_field(member, name)
        if value is not _MISSING:
            if name == "text":
                if not isinstance(value, str):
                    raise TypeError("text must be a string")
                record[name] = value
            else:
                record[name] = _required_string(value, name)
    member_order = _optional_field(member, "member_order")
    if member_order is not _MISSING:
        if not isinstance(member_order, int) or isinstance(member_order, bool) or member_order < 0:
            raise ValueError("member_order must be a non-negative integer")
        record["member_order"] = member_order
    for name in ("line_start", "line_end"):
        value = _optional_field(member, name)
        if value is not _MISSING:
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
            record[name] = value
    if "line_start" in record and "line_end" in record and record["line_end"] < record["line_start"]:
        raise ValueError("member line range is invalid")
    return record


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("cache material must be JSON-serializable") from exc


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "surrogateescape")).hexdigest()


def _sorted_member_records(members: Iterable[object]) -> tuple[dict[str, Any], ...]:
    records = [_member_record(member) for member in members]
    if records and all("member_order" in item for item in records):
        records.sort(
            key=lambda item: (
                item["topic_key"],
                item["member_order"],
                item["source_path"],
                item["content_hash"],
            )
        )
    else:
        records.sort(
            key=lambda item: (
                item["topic_key"],
                item["source_path"],
                item["content_hash"],
            )
        )
    return tuple(records)


def page_input_fingerprint(members: Iterable[object]) -> str:
    """Hash every member identity in a stable order.

    The record includes the exact provider material (source block, span,
    kind, text, and group order) so a prompt-changing edit cannot reuse a
    stale model response.  Legacy callers without the richer fields retain a
    deterministic identity-only sort.
    """

    records = _sorted_member_records(members)
    return _sha256(_canonical_json({"members": records}))


def composite_cache_key(
    *,
    model_id: str,
    prompt_version: str,
    topic_map_version: str,
    topic_key: str,
    members: Iterable[object],
) -> str:
    """Build the FR-CMP-003 key from all version and page inputs."""

    material = {
        "model_id": _required_string(model_id, "model_id"),
        "prompt_version": _required_string(prompt_version, "prompt_version"),
        "topic_map_version": _required_string(
            topic_map_version, "topic_map_version"
        ),
        "topic_key": _required_string(topic_key, "topic_key"),
        "page_input_fingerprint": page_input_fingerprint(members),
    }
    return _sha256(_canonical_json(material))


def _contains_sensitive_field(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError("cache result object keys must be strings")
            if _SENSITIVE_FIELD_RE.search(key):
                return True
            if _contains_sensitive_field(nested):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_sensitive_field(item) for item in value)
    return False


def _validated_result(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("provider result must be a JSON object")
    if _contains_sensitive_field(value):
        raise ValueError("provider result contains a credential field")
    result_json = _canonical_json(dict(value))
    try:
        result = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise ValueError("provider result is not valid JSON") from exc
    if not isinstance(result, dict):
        raise ValueError("provider result must be a JSON object")
    return result


def _validated_entry(entry: object, line_number: int) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ValueError(f"cache line {line_number} must contain a JSON object")
    if set(entry) != _CACHE_FIELDS:
        missing = sorted(_CACHE_FIELDS - set(entry))
        extra = sorted(set(entry) - _CACHE_FIELDS)
        raise ValueError(
            f"cache line {line_number} has invalid fields; missing={missing}, extra={extra}"
        )
    for field in (
        "cache_key",
        "model_id",
        "prompt_version",
        "topic_map_version",
        "created_from_fingerprint",
    ):
        _required_string(entry[field], field)
    entry["result"] = _validated_result(entry["result"])
    return entry


def _invoke_provider(provider: object) -> object:
    if callable(provider):
        return provider()
    complete = getattr(provider, "complete", None)
    if callable(complete):
        return complete()
    raise TypeError("provider must be callable or expose a callable complete()")


@dataclass(frozen=True)
class ModelCache:
    """Append-only JSONL cache for one task-level model-result directory."""

    root: Path

    def __init__(self, root: str | Path):
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=True)
        if not root_path.is_dir():
            raise ValueError(f"cache root is not a directory: {root_path}")
        object.__setattr__(self, "root", root_path)

    @property
    def path(self) -> Path:
        return self.root / "entries.jsonl"

    def _entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        if not self.path.is_file():
            raise ValueError(f"cache entries path is not a file: {self.path}")
        entries: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8", newline="") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    raw_entry = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"cache line {line_number} is not valid JSON") from exc
                entries.append(_validated_entry(raw_entry, line_number))
        return entries

    def get_or_call(
        self,
        *,
        model_id: str,
        prompt_version: str,
        topic_map_version: str,
        topic_key: str,
        members: Iterable[object],
        provider: Callable[[], Mapping[str, Any]] | object,
    ) -> CacheResult:
        """Return a frozen result, calling and recording the provider on miss."""

        material_members = _sorted_member_records(members)
        fingerprint = page_input_fingerprint(material_members)
        key = composite_cache_key(
            model_id=model_id,
            prompt_version=prompt_version,
            topic_map_version=topic_map_version,
            topic_key=topic_key,
            members=material_members,
        )
        normalized_model = _required_string(model_id, "model_id")
        normalized_prompt = _required_string(prompt_version, "prompt_version")
        normalized_topic_map = _required_string(
            topic_map_version, "topic_map_version"
        )

        try:
            entries = self._entries()
        except CacheIntegrityError:
            raise
        except Exception as error:
            raise CacheIntegrityError(
                f"cache read or validation failed: {error}",
                provider_called=False,
            ) from error

        matching: dict[str, Any] | None = None
        try:
            for entry in entries:
                if entry["cache_key"] != key:
                    continue
                if entry["created_from_fingerprint"] != fingerprint:
                    raise ValueError("cache key and page fingerprint do not agree")
                if (
                    entry["model_id"] != normalized_model
                    or entry["prompt_version"] != normalized_prompt
                    or entry["topic_map_version"] != normalized_topic_map
                ):
                    raise ValueError("cache key metadata does not match requested material")
                if matching is not None and _canonical_json(matching["result"]) != _canonical_json(
                    entry["result"]
                ):
                    raise ValueError("duplicate cache key has conflicting frozen results")
                matching = entry
        except CacheIntegrityError:
            raise
        except Exception as error:
            raise CacheIntegrityError(
                f"cache identity validation failed: {error}",
                provider_called=False,
            ) from error

        if matching is not None:
            return CacheResult(
                result=deepcopy(matching["result"]),
                cache_key=key,
                created_from_fingerprint=fingerprint,
                hit=True,
                called=False,
            )

        # Provider exceptions are deliberately allowed through unchanged. A
        # provider outage is not a cache-integrity failure.
        raw_result = _invoke_provider(provider)
        try:
            result = _validated_result(raw_result)
        except Exception as error:
            raise CacheIntegrityError(
                f"provider result could not be frozen in cache: {error}",
                provider_called=True,
                provider_result=None,
            ) from error
        entry = {
            "cache_key": key,
            "model_id": normalized_model,
            "prompt_version": normalized_prompt,
            "topic_map_version": normalized_topic_map,
            "result": result,
            "created_from_fingerprint": fingerprint,
        }
        try:
            encoded = _canonical_json(entry)
            with self.path.open("a", encoding="utf-8", newline="") as stream:
                stream.write(encoded)
                stream.write("\n")
        except Exception as error:
            raise CacheIntegrityError(
                f"cache result could not be persisted: {error}",
                provider_called=True,
                provider_result=result,
            ) from error
        return CacheResult(
            result=deepcopy(result),
            cache_key=key,
            created_from_fingerprint=fingerprint,
            hit=False,
            called=True,
        )
