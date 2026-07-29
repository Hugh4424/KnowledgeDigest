from __future__ import annotations

import io
import json
from typing import Any

from knowledge_digest.agentmemory_store import (
    AgentMemoryStore,
    MemoryWrite,
    parse_provenance,
    provenance_content,
    provenance_matches,
)


def claim() -> dict[str, Any]:
    return {
        "text": "原文事实 A",
        "claim_fingerprint": "claim-a",
        "source_uri": "confluence://company/topic/page.md",
        "fragment_locator": "lines:2-3",
        "content_fingerprint": "content-a",
        "source_snapshot_ref": "snapshot-a",
        "raw_id": "raw-a",
    }


def memory_for(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "memory-a",
        "project": "phase3-test",
        "content": provenance_content(value),
        "isLatest": True,
    }


def test_provenance_round_trip_is_exact_and_rejects_changed_locator() -> None:
    value = claim()
    memory = memory_for(value)

    parsed = parse_provenance(memory)
    assert parsed is not None
    assert parsed["claim"] == value["text"]
    assert all(parsed[key] == value[key] for key in value if key != "text")
    assert provenance_matches(memory, value)
    changed = dict(value, fragment_locator="lines:99-99")
    assert not provenance_matches(memory, changed)


class FakeResponse(io.BytesIO):
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def test_store_uses_official_endpoints_and_deduplicates_by_claim_fingerprint() -> None:
    value = claim()
    stored = memory_for(value)
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def opener(request: Any, timeout: float) -> FakeResponse:
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        calls.append((request.full_url, request.method, body))
        if request.full_url.endswith("/agentmemory/memories?latest=true&limit=5000"):
            payload = {"memories": [stored], "total": 1}
        elif request.full_url.endswith("/agentmemory/livez"):
            payload = {"status": "ok"}
        else:
            raise AssertionError(request.full_url)
        return FakeResponse(json.dumps(payload).encode("utf-8"))

    store = AgentMemoryStore("http://127.0.0.1:3211", project="phase3-test", opener=opener)
    assert store.livez()["status"] == "ok"
    writes = store.remember_claims([value])

    assert writes == [MemoryWrite("claim-a", "memory-a", "duplicate", stored)]
    assert [method for _url, method, _body in calls] == ["GET", "GET"]
