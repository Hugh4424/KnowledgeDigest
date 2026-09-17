"""Task7 P4: deterministic model cache and invalidation contract."""

from __future__ import annotations

import json
from pathlib import Path
import stat

import pytest


try:
    from knowledge_digest.semantic_cache import (
        CacheIntegrityError,
        ModelCache,
        composite_cache_key,
        page_input_fingerprint,
    )
except (ImportError, ModuleNotFoundError):
    # Keep the RED assertions collectable before T008 adds the module.
    ModelCache = None
    CacheIntegrityError = None
    composite_cache_key = None
    page_input_fingerprint = None


def _members(secondary_hash: str = "hash-secondary") -> tuple[dict[str, str], ...]:
    return (
        {
            "topic_key": "payments:login",
            "source_path": "payments/login.md",
            "content_hash": "hash-primary",
        },
        {
            "topic_key": "payments:login",
            "source_path": "payments/session.md",
            "content_hash": secondary_hash,
        },
    )


def _require_api():
    assert ModelCache is not None, "semantic_cache.ModelCache is not implemented"
    assert composite_cache_key is not None, "semantic_cache.composite_cache_key is not implemented"
    assert page_input_fingerprint is not None, "semantic_cache.page_input_fingerprint is not implemented"
    return ModelCache, composite_cache_key, page_input_fingerprint


def test_task7_cache_composite_key_is_order_independent_and_covers_all_key_parts() -> None:
    _, composite_key_api, fingerprint_api = _require_api()
    members = _members()

    fingerprint = fingerprint_api(members)
    assert fingerprint == fingerprint_api(tuple(reversed(members)))
    assert fingerprint != fingerprint_api(_members("hash-secondary-changed"))

    base = composite_key_api(
        model_id="qwen3.8",
        prompt_version="semantic-v1",
        topic_map_version="map-v1",
        topic_key="payments:login",
        members=members,
    )
    assert base != composite_key_api(
        model_id="qwen3.9",
        prompt_version="semantic-v1",
        topic_map_version="map-v1",
        topic_key="payments:login",
        members=members,
    )
    assert base != composite_key_api(
        model_id="qwen3.8",
        prompt_version="semantic-v2",
        topic_map_version="map-v1",
        topic_key="payments:login",
        members=members,
    )
    assert base != composite_key_api(
        model_id="qwen3.8",
        prompt_version="semantic-v1",
        topic_map_version="map-v2",
        topic_key="payments:login",
        members=members,
    )
    assert base != composite_key_api(
        model_id="qwen3.8",
        prompt_version="semantic-v1",
        topic_map_version="map-v1",
        topic_key="payments:other",
        members=members,
    )


def test_task7_cache_fingerprint_covers_exact_provider_material_and_order(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    members = (
        {
            "topic_key": "payments:login",
            "source_path": "payments/login.md",
            "content_hash": "hash-primary",
            "block_id": "login-1",
            "member_order": 0,
            "line_start": 10,
            "line_end": 10,
            "kind": "narrative",
            "text": "第一句。",
        },
        {
            "topic_key": "payments:login",
            "source_path": "payments/login.md",
            "content_hash": "hash-secondary",
            "block_id": "login-2",
            "member_order": 1,
            "line_start": 12,
            "line_end": 12,
            "kind": "table",
            "text": "",
        },
    )
    calls: list[str] = []
    cache = cache_type(tmp_path / "model-cache")
    common = {
        "model_id": "qwen3.8",
        "prompt_version": "semantic-v1",
        "topic_map_version": "map-v1",
        "topic_key": "payments:login",
    }

    cache.get_or_call(
        members=members,
        provider=lambda: calls.append("original") or {"title": "Login"},
        **common,
    )
    changed_span = (dict(members[0], line_start=11, line_end=11, text="第一句。"), members[1])
    cache.get_or_call(
        members=changed_span,
        provider=lambda: calls.append("span") or {"title": "Login"},
        **common,
    )
    reordered = (
        dict(members[1], member_order=0),
        dict(members[0], member_order=1),
    )
    cache.get_or_call(
        members=reordered,
        provider=lambda: calls.append("order") or {"title": "Login"},
        **common,
    )

    assert calls == ["original", "span", "order"]


def test_task7_cache_miss_calls_once_writes_jsonl_and_hit_skips_provider(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    calls: list[str] = []

    def provider() -> dict[str, str]:
        calls.append("called")
        return {"title": "Login", "intro": "原文明确"}

    cache = cache_type(tmp_path / "cache" / "model-cache")
    kwargs = {
        "model_id": "qwen3.8",
        "prompt_version": "semantic-v1",
        "topic_map_version": "map-v1",
        "topic_key": "payments:login",
        "members": _members(),
    }
    first = cache.get_or_call(provider=provider, **kwargs)
    cache_bytes_after_miss = cache.path.read_bytes()
    second = cache.get_or_call(provider=provider, **kwargs)

    assert calls == ["called"]
    assert first.result == second.result == {"title": "Login", "intro": "原文明确"}
    assert first.hit is False
    assert first.called is True
    assert second.hit is True
    assert second.called is False
    assert cache.path.read_bytes() == cache_bytes_after_miss

    entries = [json.loads(line) for line in cache.path.read_text(encoding="utf-8").splitlines()]
    assert len(entries) == 1
    assert set(entries[0]) == {
        "cache_key",
        "model_id",
        "prompt_version",
        "topic_map_version",
        "result",
        "created_from_fingerprint",
    }
    assert "secret" not in cache.path.read_text(encoding="utf-8").lower()
    assert "token" not in cache.path.read_text(encoding="utf-8").lower()


def test_task7_cache_recovers_an_incomplete_tail_before_reading(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    calls: list[str] = []
    cache = cache_type(tmp_path / "cache" / "model-cache")
    kwargs = {
        "model_id": "qwen3.8",
        "prompt_version": "semantic-v1",
        "topic_map_version": "map-v1",
        "topic_key": "payments:login",
        "members": _members(),
    }

    cache.get_or_call(provider=lambda: calls.append("first") or {"title": "Login"}, **kwargs)
    with cache.path.open("a", encoding="utf-8") as stream:
        stream.write('{"partial":')

    hit = cache.get_or_call(provider=lambda: calls.append("unexpected") or {"title": "wrong"}, **kwargs)

    assert hit.hit is True
    assert calls == ["first"]
    assert len(cache.path.read_text(encoding="utf-8").splitlines()) == 1


def test_task7_cache_preserves_a_complete_tail_without_newline(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    calls: list[str] = []
    cache = cache_type(tmp_path / "cache" / "model-cache")
    kwargs = {
        "model_id": "qwen3.8",
        "prompt_version": "semantic-v1",
        "topic_map_version": "map-v1",
        "topic_key": "payments:login",
        "members": _members(),
    }

    cache.get_or_call(provider=lambda: calls.append("first") or {"title": "Login"}, **kwargs)
    cache.path.write_bytes(cache.path.read_bytes().removesuffix(b"\n"))

    hit = cache.get_or_call(provider=lambda: calls.append("unexpected") or {"title": "wrong"}, **kwargs)

    assert hit.hit is True
    assert calls == ["first"]
    assert cache.path.read_bytes().endswith(b"\n")
    assert len(cache.path.read_text(encoding="utf-8").splitlines()) == 1


def test_task7_cache_member_change_including_non_primary_source_forces_new_call(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    calls: list[str] = []

    def provider() -> dict[str, int]:
        calls.append("called")
        return {"sequence": len(calls)}

    cache = cache_type(tmp_path / "model-cache")
    common = {
        "model_id": "qwen3.8",
        "prompt_version": "semantic-v1",
        "topic_map_version": "map-v1",
        "topic_key": "payments:login",
    }
    original = cache.get_or_call(provider=provider, members=_members(), **common)
    changed = cache.get_or_call(
        provider=provider,
        members=_members("hash-secondary-changed"),
        **common,
    )

    assert original.hit is False
    assert changed.hit is False
    assert calls == ["called", "called"]
    assert changed.result == {"sequence": 2}


def test_task7_cache_normalizes_json_values_and_allows_usage_token_counters(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    cache = cache_type(tmp_path / "model-cache")
    calls: list[str] = []

    def provider() -> dict[str, object]:
        calls.append("called")
        return {"usage": {"total_tokens": 3, "token_count": 3}, "items": ("x",)}

    kwargs = {
        "model_id": "qwen3.8",
        "prompt_version": "semantic-v1",
        "topic_map_version": "map-v1",
        "topic_key": "payments:login",
        "members": _members(),
    }
    first = cache.get_or_call(provider=provider, **kwargs)
    second = cache.get_or_call(provider=provider, **kwargs)

    assert calls == ["called"]
    assert first.result == second.result == {
        "usage": {"total_tokens": 3, "token_count": 3},
        "items": ["x"],
    }


def test_task7_cache_corruption_is_a_structured_integrity_failure(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    assert CacheIntegrityError is not None
    cache = cache_type(tmp_path / "model-cache")
    cache.path.write_text("not-json\n", encoding="utf-8")
    calls: list[str] = []

    with pytest.raises(CacheIntegrityError) as raised:
        cache.get_or_call(
            model_id="qwen3.8",
            prompt_version="semantic-v1",
            topic_map_version="map-v1",
            topic_key="payments:login",
            members=_members(),
            provider=lambda: calls.append("called") or {"title": "Login"},
        )

    assert raised.value.provider_called is False
    assert calls == []


def test_task7_cache_retired_task8_entry_is_not_silently_ignored(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    assert CacheIntegrityError is not None
    cache = cache_type(tmp_path / "model-cache")
    cache.path.write_text(
        json.dumps({"cache_key": "task8-retired-key"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CacheIntegrityError, match="cache read or validation failed"):
        cache.get_or_call(
            model_id="qwen3.8",
            prompt_version="semantic-v1",
            topic_map_version="map-v1",
            topic_key="payments:login",
            members=_members(),
            provider=lambda: {"title": "Login"},
        )


def test_task7_cache_skips_valid_task8_sibling_records_in_shared_jsonl(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    cache = cache_type(tmp_path / "model-cache")
    cache.path.write_text(
        json.dumps(
            {
                "cache_key": "task8-desc:valid-sibling",
                "model_id": "qwen3.8",
                "prompt_version": "task8-navigation-v3",
                "topic_map_version": "task8-topic-map-v1",
                "result": "这页帮助你完成登录配置。",
                "created_from_fingerprint": "a" * 64,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    calls: list[str] = []

    result = cache.get_or_call(
        model_id="qwen3.8",
        prompt_version="semantic-v1",
        topic_map_version="map-v1",
        topic_key="payments:login",
        members=_members(),
        provider=lambda: calls.append("called") or {"title": "Login"},
    )

    assert result.called is True
    assert calls == ["called"]


def test_task7_cache_lock_path_cannot_follow_symlink(tmp_path) -> None:
    cache_type, _, _ = _require_api()
    cache = cache_type(tmp_path / "model-cache")
    outside = tmp_path / "outside.lock"
    outside.write_bytes(b"unchanged")
    cache_lock = cache.root / "entries.jsonl.lock"
    cache_lock.symlink_to(outside)

    with pytest.raises(ValueError, match="lock"):
        cache.get_or_call(
            model_id="qwen3.8",
            prompt_version="semantic-v1",
            topic_map_version="map-v1",
            topic_key="payments:login",
            members=_members(),
            provider=lambda: {"title": "Login"},
        )

    assert outside.read_bytes() == b"unchanged"


def test_task7_cache_append_fsyncs_cache_directory(tmp_path, monkeypatch) -> None:
    cache_type, _, _ = _require_api()
    import knowledge_digest.semantic_cache as semantic_cache

    original_fsync = semantic_cache.os.fsync
    fsync_kinds: list[bool] = []

    def record_fsync(descriptor: int) -> None:
        fsync_kinds.append(stat.S_ISDIR(semantic_cache.os.fstat(descriptor).st_mode))
        original_fsync(descriptor)

    monkeypatch.setattr(semantic_cache.os, "fsync", record_fsync)
    cache = cache_type(tmp_path / "model-cache")
    cache.get_or_call(
        model_id="qwen3.8",
        prompt_version="semantic-v1",
        topic_map_version="map-v1",
        topic_key="payments:login",
        members=_members(),
        provider=lambda: {"title": "Login"},
    )

    assert True in fsync_kinds


def test_task7_cache_write_failure_records_that_provider_was_called(tmp_path, monkeypatch) -> None:
    cache_type, _, _ = _require_api()
    assert CacheIntegrityError is not None
    cache = cache_type(tmp_path / "model-cache")
    original_open = Path.open

    def fail_cache_append(path: Path, *args: object, **kwargs: object):
        mode = kwargs.get("mode", args[0] if args else "r")
        if path == cache.path and mode == "a":
            raise OSError("simulated cache disk full")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_cache_append)
    with pytest.raises(CacheIntegrityError) as raised:
        cache.get_or_call(
            model_id="qwen3.8",
            prompt_version="semantic-v1",
            topic_map_version="map-v1",
            topic_key="payments:login",
            members=_members(),
            provider=lambda: {"title": "Login", "provider_tokens": 4},
        )

    assert raised.value.provider_called is True
    assert raised.value.provider_result == {"title": "Login", "provider_tokens": 4}
