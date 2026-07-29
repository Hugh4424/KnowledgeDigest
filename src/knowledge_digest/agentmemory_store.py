"""Small official-REST adapter for isolated agentmemory acceptance runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROVENANCE_PREFIX = "KD_PROVENANCE_V1\n"
DEFAULT_TIMEOUT_SECONDS = 10.0


class AgentMemoryError(RuntimeError):
    """Raised when the official agentmemory REST contract fails."""


@dataclass(frozen=True)
class MemoryWrite:
    claim_fingerprint: str
    memory_id: str | None
    status: str
    memory: dict[str, Any] | None


def provenance_content(claim: dict[str, Any]) -> str:
    """Encode exact claim text and lineage as JSON for lossless read-back."""
    payload = {
        "claim": str(claim.get("text", "")),
        "claim_fingerprint": str(claim.get("claim_fingerprint", "")),
        "source_uri": str(claim.get("source_uri", "")),
        "fragment_locator": str(claim.get("fragment_locator", "")),
        "content_fingerprint": str(claim.get("content_fingerprint", "")),
        "source_snapshot_ref": claim.get("source_snapshot_ref"),
        "raw_id": claim.get("raw_id"),
    }
    return PROVENANCE_PREFIX + json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def parse_provenance(memory: dict[str, Any]) -> dict[str, Any] | None:
    content = memory.get("content")
    if not isinstance(content, str) or not content.startswith(PROVENANCE_PREFIX):
        return None
    try:
        value = json.loads(content[len(PROVENANCE_PREFIX) :])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def provenance_matches(memory: dict[str, Any], claim: dict[str, Any]) -> bool:
    actual = parse_provenance(memory)
    if actual is None:
        return False
    expected = json.loads(provenance_content(claim)[len(PROVENANCE_PREFIX) :])
    stable_keys = (
        "claim",
        "claim_fingerprint",
        "source_uri",
        "fragment_locator",
        "content_fingerprint",
        "source_snapshot_ref",
    )
    return all(actual.get(key) == expected.get(key) for key in stable_keys)


class AgentMemoryStore:
    """Use only documented agentmemory REST endpoints.

    The adapter never opens the engine state file and never falls back to a
    local or in-memory store. A failed endpoint is an acceptance failure.
    """

    def __init__(
        self,
        base_url: str,
        *,
        project: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        base = base_url.rstrip("/")
        if not base.startswith(("http://", "https://")):
            raise ValueError("agentmemory base_url must use http:// or https://")
        if not project.strip():
            raise ValueError("agentmemory project must not be empty")
        self.base_url = base
        self.project = project
        self.timeout = timeout
        self._opener = opener

    def _request(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        suffix = f"?{urlencode(query)}" if query else ""
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.base_url}{path}{suffix}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, OSError, TimeoutError) as error:
            detail = getattr(error, "reason", error)
            raise AgentMemoryError(f"agentmemory REST request failed: {path}: {detail}") from error
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as error:
            raise AgentMemoryError(f"agentmemory REST returned invalid JSON: {path}") from error
        if not isinstance(decoded, dict):
            raise AgentMemoryError(f"agentmemory REST returned a non-object: {path}")
        if decoded.get("success") is False or "error" in decoded and decoded.get("error"):
            raise AgentMemoryError(f"agentmemory REST rejected {path}: {decoded.get('error')}")
        return decoded

    def livez(self) -> dict[str, Any]:
        return self._request("/agentmemory/livez")

    def remember_claims(self, claims: list[dict[str, Any]]) -> list[MemoryWrite]:
        existing = self.list_memories()
        existing_by_fingerprint = {
            (
                str(parsed.get("claim_fingerprint")),
                str(parsed.get("source_uri")),
                str(parsed.get("fragment_locator")),
            ): memory
            for memory in existing
            if (parsed := parse_provenance(memory))
            and parsed.get("claim_fingerprint")
        }
        writes: list[MemoryWrite] = []
        for claim in claims:
            fingerprint = str(claim.get("claim_fingerprint", ""))
            if not fingerprint:
                raise AgentMemoryError("every agentmemory claim requires claim_fingerprint")
            identity = (
                fingerprint,
                str(claim.get("source_uri", "")),
                str(claim.get("fragment_locator", "")),
            )
            prior = existing_by_fingerprint.get(identity)
            if prior is not None:
                if not provenance_matches(prior, claim):
                    raise AgentMemoryError(
                        f"agentmemory duplicate claim has conflicting provenance: {identity}"
                    )
                writes.append(MemoryWrite(fingerprint, str(prior["id"]), "duplicate", prior))
                continue
            response = self._request(
                "/agentmemory/remember",
                method="POST",
                payload={
                    "content": provenance_content(claim),
                    "type": "fact",
                    "concepts": ["KnowledgeDigest", "Phase3", fingerprint],
                    "files": [str(claim.get("source_uri", ""))],
                    "project": self.project,
                },
            )
            memory = response.get("memory")
            if not isinstance(memory, dict) or not memory.get("id"):
                raise AgentMemoryError("agentmemory remember response has no memory id")
            if not provenance_matches(memory, claim):
                raise AgentMemoryError("agentmemory remember response lost provenance")
            writes.append(MemoryWrite(fingerprint, str(memory["id"]), "created", memory))
            existing_by_fingerprint[identity] = memory
        return writes

    def list_memories(self) -> list[dict[str, Any]]:
        response = self._request(
            "/agentmemory/memories",
            query={"latest": "true", "limit": "5000"},
        )
        memories = response.get("memories")
        if not isinstance(memories, list):
            raise AgentMemoryError("agentmemory memories response has no memories list")
        return [
            memory
            for memory in memories
            if isinstance(memory, dict) and memory.get("project") == self.project
        ]

    def smart_search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        response = self._request(
            "/agentmemory/smart-search",
            method="POST",
            payload={"query": query, "limit": limit, "project": self.project},
        )
        results = response.get("results")
        if not isinstance(results, list):
            raise AgentMemoryError("agentmemory smart-search response has no results list")
        materialized: list[dict[str, Any]] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            memory_id = result.get("obsId") or result.get("memoryId") or result.get("id")
            if not isinstance(memory_id, str):
                continue
            memory = self._request(f"/agentmemory/memories/{memory_id}").get("memory")
            if isinstance(memory, dict) and memory.get("project") == self.project:
                materialized.append({"result": result, "memory": memory})
        return materialized

    def get_memory(self, memory_id: str) -> dict[str, Any]:
        response = self._request(f"/agentmemory/memories/{memory_id}")
        memory = response.get("memory")
        if not isinstance(memory, dict):
            raise AgentMemoryError(f"agentmemory memory not found: {memory_id}")
        return memory

    def forget(self, memory_id: str) -> dict[str, Any]:
        return self._request(
            "/agentmemory/forget",
            method="POST",
            payload={"memoryId": memory_id},
        )
