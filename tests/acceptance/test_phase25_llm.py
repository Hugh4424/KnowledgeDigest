"""Phase 2.5 acceptance coverage for the LLM refinement generator.

Most tests replace ``urllib.request.urlopen`` so no external network request is
made. One transport-boundary test uses a local HTTP server to exercise real
concurrent provider calls and the hard-deadline process boundary.
"""

from __future__ import annotations

import io
import json
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from knowledge_digest import llm
from knowledge_digest.config import DigestSettings, resolve_settings
from knowledge_digest.draft import _repair_summary, _validate_summary, draft, resolve_generator
from knowledge_digest.errors import ValidationError
from knowledge_digest.kb_structure import parse_roots
from knowledge_digest.paths import validate_paths
from knowledge_digest.pipeline import audit_run


PROVIDER = {
    "base_url": "https://provider.example",
    "api_key": "secret-key",
    "model": "test-model",
}


class _StubResponse(io.BytesIO):
    def __init__(self, payload: Any, status: int = 200) -> None:
        super().__init__(json.dumps(payload).encode("utf-8") if not isinstance(payload, str) else payload.encode("utf-8"))
        self.status = status

    def __enter__(self) -> "_StubResponse":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def getcode(self) -> int:
        return self.status


class _LocalOpenAIHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"final_body": "local ok"}),
                    }
                }
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        pass


class _SlowOpenAIHandler(_LocalOpenAIHandler):
    def do_POST(self) -> None:
        time.sleep(2)
        super().do_POST()


def _capture(monkeypatch: pytest.MonkeyPatch, payload: Any, status: int = 200) -> list[urllib.request.Request]:
    """Record outgoing requests and answer them from a stub payload."""
    seen: list[urllib.request.Request] = []

    def fake_urlopen(request: urllib.request.Request, timeout: int | None = None) -> _StubResponse:
        seen.append(request)
        return _StubResponse(payload, status)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return seen


def _openai_payload(text: str) -> dict[str, Any]:
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


def _anthropic_payload(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


# --------------------------------------------------------------------------
# Provider protocol
# --------------------------------------------------------------------------


def test_openai_format_sends_expected_request_and_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture(monkeypatch, _openai_payload("refined body"))

    text = llm.call_llm("prompt text", api_format="openai", **PROVIDER)

    assert text == "refined body"
    request = seen[0]
    assert request.full_url == "https://provider.example/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer secret-key"
    assert request.get_header("X-api-key") is None
    body = json.loads(request.data.decode("utf-8"))
    assert body["model"] == "test-model"
    assert body["messages"] == [{"role": "user", "content": "prompt text"}]
    assert body["temperature"] == 0
    assert body["max_tokens"] == llm.DEFAULT_MAX_TOKENS


def test_anthropic_format_sends_expected_request_and_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture(monkeypatch, _anthropic_payload("refined body"))

    text = llm.call_llm("prompt text", api_format="anthropic", **PROVIDER)

    assert text == "refined body"
    request = seen[0]
    assert request.full_url == "https://provider.example/v1/messages"
    assert request.get_header("X-api-key") == "secret-key"
    assert request.get_header("Anthropic-version") == "2023-06-01"
    assert request.get_header("Authorization") is None
    body = json.loads(request.data.decode("utf-8"))
    assert body["max_tokens"] == llm.DEFAULT_MAX_TOKENS
    assert body["messages"] == [{"role": "user", "content": "prompt text"}]


def test_qwen_openai_payload_requests_json_and_no_thinking() -> None:
    body = llm._request_payload(
        "openai",
        llm.PUBLICATION_LLM_MODEL,
        "prompt text",
        max_tokens=llm.PUBLICATION_MAX_TOKENS,
    )

    assert body["response_format"] == {"type": "json_object"}
    assert body["enable_thinking"] is False
    assert body["max_tokens"] == llm.PUBLICATION_MAX_TOKENS


def test_four_concurrent_real_requests_cross_the_transport_boundary() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LocalOpenAIHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    def invoke() -> str:
        return llm.call_llm(
            "local transport boundary",
            api_format="openai",
            base_url=base_url,
            api_key="local-test-key",
            model="local-test-model",
            timeout=5,
        )

    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda _index: invoke(), range(4)))
    finally:
        server.shutdown()
        server_thread.join(timeout=5)

    assert [json.loads(result) for result in results] == [{"final_body": "local ok"}] * 4


def test_spawned_request_preserves_the_hard_wall_clock_deadline() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SlowOpenAIHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    started = time.monotonic()

    try:
        with pytest.raises(ValidationError, match="deadline exceeded after 1s"):
            llm.call_llm(
                "local timeout boundary",
                api_format="openai",
                base_url=base_url,
                api_key="local-test-key",
                model="local-test-model",
                timeout=1,
            )
    finally:
        server.shutdown()
        server_thread.join(timeout=5)

    assert time.monotonic() - started < 2


# --------------------------------------------------------------------------
# Fail-closed error paths: no retry, no silent downgrade
# --------------------------------------------------------------------------


def test_missing_api_key_raises_without_calling_the_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture(monkeypatch, _openai_payload("unused"))

    with pytest.raises(ValidationError, match="KD_LLM_API_KEY"):
        llm.call_llm("prompt", api_format="openai", base_url=PROVIDER["base_url"], api_key="", model="m")

    assert seen == []


def test_generator_from_env_without_key_raises_instead_of_downgrading(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture(monkeypatch, _openai_payload("unused"))
    generator = llm.generator_from_env(
        env={"KD_LLM_FORMAT": "openai", "KD_LLM_BASE_URL": "https://x.example", "KD_LLM_MODEL": "m"}
    )

    with pytest.raises(ValidationError, match="KD_LLM_API_KEY"):
        generator({"initial_body": "body", "claims": []})

    assert seen == []


def test_generator_from_env_accepts_a_configurable_timeout() -> None:
    generator = llm.generator_from_env(
        env={
            "KD_LLM_FORMAT": "openai",
            "KD_LLM_BASE_URL": "https://x.example",
            "KD_LLM_API_KEY": "key",
            "KD_LLM_MODEL": "m",
            "KD_LLM_TIMEOUT_SECONDS": "180",
        }
    )

    assert generator.__closure__ is not None


@pytest.mark.parametrize("value", ["0", "-1", "not-an-int"])
def test_generator_from_env_rejects_invalid_timeout(value: str) -> None:
    with pytest.raises(ValidationError, match="KD_LLM_TIMEOUT_SECONDS"):
        llm.generator_from_env(
            env={
                "KD_LLM_FORMAT": "openai",
                "KD_LLM_BASE_URL": "https://x.example",
                "KD_LLM_API_KEY": "key",
                "KD_LLM_MODEL": "m",
                "KD_LLM_TIMEOUT_SECONDS": value,
            }
        )


def test_http_500_raises_and_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_urlopen(request: urllib.request.Request, timeout: int | None = None) -> _StubResponse:
        calls.append(1)
        raise urllib.error.HTTPError(request.full_url, 500, "Server Error", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValidationError, match="non-success status"):
        llm.call_llm("prompt", api_format="openai", **PROVIDER)

    assert len(calls) == 1


def test_timeout_raises_and_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_urlopen(request: urllib.request.Request, timeout: int | None = None) -> _StubResponse:
        calls.append(1)
        raise urllib.error.URLError(socket.timeout("timed out"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValidationError, match="request failed"):
        llm.call_llm("prompt", api_format="openai", **PROVIDER)

    assert len(calls) == 1


def test_generator_retries_transport_failure_only_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fake_call_llm(*_args: Any, **_kwargs: Any) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValidationError("llm", "provider", "provider request failed (timed out)")
        return json.dumps({"final_body": "Claim one."})

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)
    generator = llm.build_generator(api_format="openai", retry_attempts=1, **PROVIDER)

    result = generator(
        {
            "target_page": "pages/one.md",
            "initial_body": "Claim one.",
            "claims": [],
        }
    )

    assert result["final_body"] == "Claim one."
    assert result["provider_attempt_count"] == 2
    assert calls == 2


def test_generator_does_not_retry_invalid_provider_output(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fake_call_llm(*_args: Any, **_kwargs: Any) -> str:
        nonlocal calls
        calls += 1
        return "not json"

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)
    generator = llm.build_generator(api_format="openai", retry_attempts=1, **PROVIDER)

    with pytest.raises(ValidationError, match="not JSON"):
        generator({"target_page": "pages/one.md", "initial_body": "body", "claims": []})

    assert calls == 1


def test_qwen_generator_disables_hidden_thinking_without_persisting_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def fake_call_llm(prompt: str, **_kwargs: Any) -> str:
        seen.append(prompt)
        return json.dumps({"final_body": "body"})

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)
    generator = llm.build_generator(
        api_format="openai",
        base_url=llm.PUBLICATION_LLM_BASE_URL,
        api_key="secret-key",
        model=llm.PUBLICATION_LLM_MODEL,
    )

    result = generator({"target_page": "pages/one.md", "initial_body": "body", "claims": []})

    assert result["final_body"] == "body"
    assert seen and seen[0].startswith("/no_think\n")


def test_publication_only_generator_uses_bounded_output_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[int] = []

    def fake_call_llm(_prompt: str, **kwargs: Any) -> str:
        seen.append(int(kwargs["max_tokens"]))
        return json.dumps({"publication": {}})

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)
    generator = llm.build_generator(
        api_format="openai",
        base_url=llm.PUBLICATION_LLM_BASE_URL,
        api_key="secret-key",
        model=llm.PUBLICATION_LLM_MODEL,
    )

    generator(
        {
            "target_page": "pages/one.md",
            "initial_body": "body",
            "claims": [],
            "publication_only": True,
        }
    )

    assert seen == [llm.PUBLICATION_MAX_TOKENS]


def test_hard_deadline_interrupts_a_blocking_read() -> None:
    started = time.monotonic()
    with pytest.raises(TimeoutError, match="deadline exceeded after 1s"):
        with llm._hard_deadline(1):
            time.sleep(5)
    assert time.monotonic() - started < 3


def test_non_json_provider_output_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture(monkeypatch, "this is not json")

    with pytest.raises(ValidationError, match="invalid JSON"):
        llm.call_llm("prompt", api_format="openai", **PROVIDER)

    assert len(seen) == 1


def test_unexpected_response_shape_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture(monkeypatch, {"unexpected": "shape"})

    with pytest.raises(ValidationError, match="unexpected response shape"):
        llm.call_llm("prompt", api_format="openai", **PROVIDER)

    assert len(seen) == 1


# --------------------------------------------------------------------------
# Prompt content: the loss-prevention constraints must be stated up front
# --------------------------------------------------------------------------


def test_prompt_states_the_verbatim_and_structure_constraints() -> None:
    prompt = llm.build_prompt(
        {
            "initial_body": "Claim one.",
            "source_text": "Claim one.",
            "old_target_body": "",
            "claims": [
                {
                    "claim_fingerprint": "fp-1",
                    "text": "Claim one.",
                    "source_uri": "https://source.example/one",
                    "fragment_locator": "lines:1-1",
                    "raw_id": "raw-1",
                }
            ],
        },
        target_page="pages/one.md",
    )

    assert "VERBATIM" in prompt
    assert "Never drop a claim" in prompt
    assert "Never truncate" in prompt
    assert "tables, code blocks" in prompt
    assert "version history" in prompt
    assert "fp-1" in prompt
    assert "pages/one.md" in prompt
    assert '"raw_id": "raw-1"' in prompt
    assert "fragment_locator and raw_id copied verbatim" in prompt


def test_summary_prompt_declares_nested_contract_and_evidence_mode() -> None:
    prompt = llm.build_prompt(
        {
            "initial_body": "Claim one.",
            "source_text": "Claim one.",
            "claims": [{"claim_fingerprint": "fp-1", "text": "Claim one."}],
            "summary_enabled": True,
        },
        target_page="pages/one.md",
    )

    assert "SUMMARY MODE" in prompt
    assert '"summary_id":"summary-1"' in prompt
    assert "deterministic Evidence section" in prompt
    assert '"summary_enabled": true' in prompt
    assert "Preserve every number" in prompt
    assert "approximately" in prompt


# --------------------------------------------------------------------------
# Hard-gate interaction with LLM output
# --------------------------------------------------------------------------


def _items() -> list[dict[str, Any]]:
    return [
        {
            "raw_id": "raw-1",
            "text": "Claim one.\nClaim two.\n",
            "source_uri": "https://source.example/one",
            "content_fingerprint": "content-1",
            "source_snapshot_ref": "s1/source-snapshots.jsonl#snapshot-1",
            "input_path": "/fixture/one.md",
            "validation_status": "passed",
        }
    ]


def _cluster() -> list[dict[str, object]]:
    return [
        {
            "cluster_id": "cluster-1",
            "tier": "auto",
            "cluster_tier": "auto",
            "members": ["raw-1"],
            "decision_reason": "llm fixture",
        }
    ]


def _decision() -> list[dict[str, object]]:
    return [
        {
            "cluster_id": "cluster-1",
            "action": "revise",
            "target_paths": ["pages/one.md"],
            "source_count": 1,
            "target_page_count": 1,
        }
    ]


def _llm_draft(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, response: dict[str, Any]) -> dict[str, Any]:
    """Run draft() with a stubbed provider returning ``response`` as JSON."""
    _capture(monkeypatch, _openai_payload(json.dumps(response)))
    generator = llm.build_generator(api_format="openai", **PROVIDER)
    return draft(_decision(), _cluster(), _items(), tmp_path, DigestSettings(), generator=generator)[0]


def _claim_rows(target: str = "pages/one.md") -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from knowledge_digest.faithfulness import verify_claims

    claims, _ = verify_claims(_items())
    coverage = [
        {
            "raw_id": claim["raw_id"],
            "source_uri": claim["source_uri"],
            "input_fragment": claim["fragment_locator"],
            "output_page": target,
            "fragment_locator": claim["fragment_locator"],
            "claim_fingerprint": claim["claim_fingerprint"],
        }
        for claim in claims
    ]
    return [dict(claim) for claim in claims], coverage


def test_faithful_llm_output_is_accepted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A well-formed refinement must be selected, not silently fall back."""
    claims, coverage = _claim_rows()
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "## Summary\n\nClaim one.\nClaim two.",
            "claims": claims,
            "coverage_mapping": coverage,
        },
    )

    assert result["rethink_status"] == "completed"
    assert result["selected_round"] == 1
    assert result["fallback_reason"] is None
    assert result["final_body"].startswith("## Summary")


def test_missing_provider_raw_ids_are_restored_from_exact_source_lineage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Omitted transport IDs do not force a faithful provider result to fallback."""
    claims, coverage = _claim_rows()
    provider_claims = [
        {name: value for name, value in claim.items() if name != "raw_id"}
        for claim in claims
    ]
    provider_coverage = [
        {name: value for name, value in row.items() if name != "raw_id"}
        for row in coverage
    ]

    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "## Summary\n\nClaim one.\nClaim two.",
            "claims": provider_claims,
            "coverage_mapping": provider_coverage,
        },
    )

    assert result["selected_round"] == 1
    assert result["rethink_status"] == "completed"
    assert result["fallback_reason"] is None
    assert {claim["raw_id"] for claim in result["claims"]} == {"raw-1"}
    assert {row["raw_id"] for row in result["coverage_mapping"]} == {"raw-1"}
    for claim in result["claims"]:
        assert claim["content_fingerprint"] == "content-1"
        assert claim["source_snapshot_ref"] == "s1/source-snapshots.jsonl#snapshot-1"
        assert claim["input_path"] == "/fixture/one.md"
        assert claim["validation_status"] == "passed"
        assert claim["verification_status"] == "verified"


def test_missing_provider_raw_id_is_not_guessed_when_source_is_ambiguous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two exact source candidates must stay unresolved instead of being guessed."""
    source_claim = {
        "claim_fingerprint": "shared-fingerprint",
        "text": "Shared claim.",
        "source_uri": "https://source.example/shared",
        "fragment_locator": "lines:1-1",
    }
    response = {
        "final_body": "Shared claim.",
        "claims": [source_claim],
        "coverage_mapping": [
            {
                "claim_fingerprint": "shared-fingerprint",
                "source_uri": "https://source.example/shared",
                "input_fragment": "lines:1-1",
                "fragment_locator": "lines:1-1",
                "output_page": "pages/one.md",
            }
        ],
    }
    _capture(monkeypatch, _openai_payload(json.dumps(response)))
    generator = llm.build_generator(api_format="openai", **PROVIDER)

    candidate = generator(
        {
            "target_page": "pages/one.md",
            "initial_body": "Shared claim.",
            "claims": [
                dict(source_claim, raw_id="raw-1", content_fingerprint="content-a"),
                dict(source_claim, raw_id="raw-1", content_fingerprint="content-b"),
            ],
        }
    )

    assert "raw_id" not in candidate["claims"][0]
    assert "raw_id" not in candidate["coverage_mapping"][0]


def test_provider_cannot_invent_internal_provenance_missing_from_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider-supplied internal metadata is removed when the source lacks it."""
    source_claim = {
        "claim_fingerprint": "source-fingerprint",
        "text": "Source claim.",
        "source_uri": "https://source.example/clean",
        "fragment_locator": "lines:1-1",
        "raw_id": "raw-clean",
    }
    forged = dict(
        source_claim,
        content_fingerprint="forged-content",
        source_snapshot_ref="forged-snapshot",
        input_path="/forged/path",
        validation_status="forged",
        verification_status="forged",
    )
    _capture(
        monkeypatch,
        _openai_payload(
            json.dumps(
                {
                    "final_body": "Source claim.",
                    "claims": [forged],
                    "coverage_mapping": [],
                }
            )
        ),
    )
    candidate = llm.build_generator(api_format="openai", **PROVIDER)(
        {
            "target_page": "pages/one.md",
            "initial_body": "Source claim.",
            "claims": [source_claim],
        }
    )

    for name in (
        "content_fingerprint",
        "source_snapshot_ref",
        "input_path",
        "validation_status",
        "verification_status",
    ):
        assert name not in candidate["claims"][0]


def test_llm_reorganization_that_keeps_claim_text_verbatim_passes_the_hard_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Headings, reordering and added prose are allowed around verbatim claims.

    This is the "light rewrite that should still pass" boundary: the LLM adds
    structure and commentary but leaves every claim string untouched.
    """
    claims, coverage = _claim_rows()
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": (
                "# Page\n\n## Second\n\nClaim two.\n\n## First\n\nClaim one.\n\n"
                "> Context added by the model, which is fine."
            ),
            "claims": claims,
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] == 1
    assert result["rethink_status"] == "completed"
    assert "Context added by the model" in result["final_body"]


def test_llm_dropping_a_claim_is_rejected_by_the_retention_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A silently dropped claim is caught by the retention gate.

    The provider returns fewer claims plus a matching (also shortened)
    coverage_mapping, so every per-claim gate would pass. The retention gate
    asserts ``source_claims`` fingerprints are a subset of the candidate's and
    rejects the whole candidate, so the run falls back instead of losing a line.
    """
    claims, coverage = _claim_rows()
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "Claim one.",
            "claims": claims[:1],
            "coverage_mapping": coverage[:1],
        },
    )

    assert result["selected_round"] is None
    assert result["rethink_status"] == "fallback"
    assert result["rounds"][0]["stop_reason"] == "candidate dropped a source claim"
    assert result["fallback_reason"] == "no valid round; used claim fallback"
    assert "Claim one." in result["final_body"]
    assert "Claim two." in result["final_body"]


def test_llm_dropping_a_claim_while_keeping_coverage_rows_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A dropped claim IS caught when final_body no longer carries its text.

    This is the realistic drop shape: the provider omits a claim from
    ``final_body`` but still reports the full claim list, so the verbatim gate
    fires and the run falls back without losing content.
    """
    claims, coverage = _claim_rows()
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "Claim one.",
            "claims": claims,
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] is None
    assert result["rethink_status"] == "fallback"
    assert result["fallback_reason"] == "no valid round; used claim fallback"
    assert "Claim one." in result["final_body"]
    assert "Claim two." in result["final_body"]


def test_llm_paraphrasing_a_claim_is_rejected_by_the_hard_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Heavy rewriting (drift) must be rejected: claim text is no longer verbatim."""
    claims, coverage = _claim_rows()
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "The first assertion holds, and a second one follows as well.",
            "claims": claims,
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate failed faithfulness hard gate"
    assert result["rethink_status"] == "fallback"


def test_minimal_punctuation_drift_is_rejected_by_the_hard_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Document the gate's strictness: even one changed character is rejected.

    This is the sensitivity boundary. ``Claim two.`` becoming ``Claim two!``
    is semantically identical yet fails, because the gate is a substring test.
    """
    claims, coverage = _claim_rows()
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "Claim one.\nClaim two!",
            "claims": claims,
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate failed faithfulness hard gate"


# --------------------------------------------------------------------------
# Normalized hard gate: harmless surface drift passes, word swaps do not
# --------------------------------------------------------------------------


def test_extra_whitespace_and_case_drift_passes_the_normalized_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Whitespace runs and letter case are surface noise, not content loss.

    Real providers routinely re-wrap lines and re-space text. Normalizing both
    sides before the substring test lets this through without weakening the
    gate against actual rewording.
    """
    claims, coverage = _claim_rows()
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "## Notes\n\nclaim  one.\nCLAIM   two.",
            "claims": claims,
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] == 1
    assert result["rethink_status"] == "completed"
    assert result["fallback_reason"] is None


def test_fullwidth_punctuation_drift_passes_the_normalized_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A fullwidth period is the same mark at a different width, so it passes."""
    items = [
        {
            "raw_id": "raw-1",
            "text": "决策依据是延迟, 不是成本.\n",
            "source_uri": "https://source.example/one",
            "validation_status": "passed",
        }
    ]
    from knowledge_digest.faithfulness import verify_claims

    claims, _ = verify_claims(items)
    claims = [dict(claim) for claim in claims]
    coverage = [
        {
            "raw_id": claim["raw_id"],
            "source_uri": claim["source_uri"],
            "input_fragment": claim["fragment_locator"],
            "output_page": "pages/one.md",
            "fragment_locator": claim["fragment_locator"],
            "claim_fingerprint": claim["claim_fingerprint"],
        }
        for claim in claims
    ]
    _capture(
        monkeypatch,
        _openai_payload(
            json.dumps(
                {
                    # ASCII "," and "." rendered fullwidth by the provider.
                    "final_body": "## 摘要\n\n决策依据是延迟，不是成本。",
                    "claims": claims,
                    "coverage_mapping": coverage,
                }
            )
        ),
    )
    generator = llm.build_generator(api_format="openai", **PROVIDER)
    result = draft(_decision(), _cluster(), items, tmp_path, DigestSettings(), generator=generator)[0]

    assert result["selected_round"] == 1
    assert result["rethink_status"] == "completed"


def test_word_substitution_is_still_rejected_by_the_normalized_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Normalization must stay surface-only: ``3 times`` -> ``three times`` fails.

    This is the boundary that keeps the relaxed gate from becoming a semantic
    judge. Only whitespace/punctuation-width/case are folded, so a swapped word
    still differs after normalization.
    """
    items = [
        {
            "raw_id": "raw-1",
            "text": "The retry ran 3 times before the circuit opened.\n",
            "source_uri": "https://source.example/one",
            "validation_status": "passed",
        }
    ]
    from knowledge_digest.faithfulness import verify_claims

    claims, _ = verify_claims(items)
    claims = [dict(claim) for claim in claims]
    coverage = [
        {
            "raw_id": claim["raw_id"],
            "source_uri": claim["source_uri"],
            "input_fragment": claim["fragment_locator"],
            "output_page": "pages/one.md",
            "fragment_locator": claim["fragment_locator"],
            "claim_fingerprint": claim["claim_fingerprint"],
        }
        for claim in claims
    ]
    _capture(
        monkeypatch,
        _openai_payload(
            json.dumps(
                {
                    "final_body": "The retry ran three times before the circuit opened.",
                    "claims": claims,
                    "coverage_mapping": coverage,
                }
            )
        ),
    )
    generator = llm.build_generator(api_format="openai", **PROVIDER)
    result = draft(_decision(), _cluster(), items, tmp_path, DigestSettings(), generator=generator)[0]

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate failed faithfulness hard gate"
    assert result["rethink_status"] == "fallback"


def test_normalize_for_gate_folds_surface_only() -> None:
    """Unit-level boundary: widths/case/whitespace fold, words do not."""
    from knowledge_digest.faithfulness import normalize_for_gate

    assert normalize_for_gate("A  b\n c") == normalize_for_gate("a b c")
    assert normalize_for_gate("done。") == normalize_for_gate("done.")
    assert normalize_for_gate("a（b）") == normalize_for_gate("a(b)")
    assert normalize_for_gate("a, b") == normalize_for_gate("a，b")
    assert normalize_for_gate("Ran 3 times") != normalize_for_gate("Ran three times")
    assert normalize_for_gate("Claim two.") != normalize_for_gate("Claim two!")
    # Word spacing stays significant: only punctuation-adjacent space is folded.
    assert normalize_for_gate("the cat sat") != normalize_for_gate("thecatsat")


def test_llm_claim_not_present_in_source_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from knowledge_digest.faithfulness import claim_fingerprint

    claims, coverage = _claim_rows()
    # Well-formed but invented: its fingerprint is honestly derived from its own
    # text, so only the source-membership gate can reject it.
    invented_text = "Invented claim."
    invented = dict(
        claims[0],
        text=invented_text,
        claim_fingerprint=claim_fingerprint(claims[0]["source_uri"], invented_text),
    )
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "Claim one.\nClaim two.\nInvented claim.",
            "claims": claims + [invented],
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate contains a claim not present in the source"


def test_llm_copying_a_source_fingerprint_onto_replacement_text_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The retention gate must bind each fingerprint to its own claim text.

    Without that binding a provider can paste a real source fingerprint onto
    substituted -- even inverted -- text and satisfy source membership,
    retention, lineage, coverage, and the normalized hard gate at once.
    """
    claims, coverage = _claim_rows()
    forged = [
        dict(claims[0], text="Claim one is false."),
        dict(claims[1], text="Claim two is false."),
    ]
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "Claim one is false.\nClaim two is false.",
            "claims": forged,
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate claim fingerprint does not match its own text"
    assert result["rethink_status"] == "fallback"
    # The fallback body carries the real source claims, not the substitution.
    assert "Claim one is false." not in result["final_body"]
    assert "Claim one." in result["final_body"]


def test_llm_shrinking_claims_to_filler_under_kept_fingerprints_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The 'keep fps, replace every text with ok' trivial-satisfaction attack."""
    claims, coverage = _claim_rows()
    gutted = [dict(claim, text="ok") for claim in claims]
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {"final_body": "ok", "claims": gutted, "coverage_mapping": coverage},
    )

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate claim fingerprint does not match its own text"


def test_provider_output_without_final_body_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture(monkeypatch, _openai_payload(json.dumps({"claims": []})))
    generator = llm.build_generator(api_format="openai", **PROVIDER)

    with pytest.raises(ValidationError, match="final_body"):
        generator({"initial_body": "body", "claims": [], "target_page": "pages/one.md"})


def test_fenced_json_response_is_parsed() -> None:
    parsed = llm.parse_response('```json\n{"final_body": "body"}\n```')
    assert parsed["final_body"] == "body"


# --------------------------------------------------------------------------
# Configuration and injection chain
# --------------------------------------------------------------------------


def test_llm_is_disabled_by_default_and_uses_the_identity_generator() -> None:
    settings = resolve_settings(None, top_k=None, high=None, medium=None, max_lines=None, env={})
    assert settings.llm_enabled is False
    assert resolve_generator(settings)({"initial_body": "body"}) == {"final_body": "body"}


def test_env_format_enables_the_provider_path() -> None:
    settings = resolve_settings(
        None,
        top_k=None,
        high=None,
        medium=None,
        max_lines=None,
        env={"KD_LLM_FORMAT": "anthropic"},
    )
    assert settings.llm_enabled is True
    assert settings.llm_format == "anthropic"


def test_no_llm_flag_overrides_the_environment() -> None:
    settings = resolve_settings(
        None,
        top_k=None,
        high=None,
        medium=None,
        max_lines=None,
        llm_enabled=False,
        env={"KD_LLM_FORMAT": "anthropic"},
    )
    assert settings.llm_enabled is False
    assert resolve_generator(settings)({"initial_body": "body"}) == {"final_body": "body"}


def test_unknown_llm_format_is_rejected() -> None:
    with pytest.raises(ValidationError, match="llm_format"):
        resolve_settings(
            None, top_k=None, high=None, medium=None, max_lines=None, env={"KD_LLM_FORMAT": "bedrock"}
        )


def test_llm_batch_limits_are_configurable_and_validated(tmp_path: Path) -> None:
    config_path = tmp_path / "digest.json"
    config_path.write_text(
        json.dumps(
            {
                "llm_batch_max_claims": 7,
                "llm_batch_max_source_chars": 2048,
                "llm_batch_concurrency": 2,
            }
        ),
        encoding="utf-8",
    )

    settings = resolve_settings(
        config_path,
        top_k=None,
        high=None,
        medium=None,
        max_lines=None,
        env={},
    )

    assert settings.llm_batch_max_claims == 7
    assert settings.llm_batch_max_source_chars == 2048
    assert settings.llm_batch_concurrency == 2

    config_path.write_text(
        json.dumps({"llm_batch_max_claims": 0}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="llm_batch_max_claims"):
        resolve_settings(
            config_path,
            top_k=None,
            high=None,
            medium=None,
            max_lines=None,
            env={},
        )

    config_path.write_text(
        json.dumps({"llm_batch_concurrency": 0}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="llm_batch_concurrency"):
        resolve_settings(
            config_path,
            top_k=None,
            high=None,
            medium=None,
            max_lines=None,
            env={},
        )


def test_llm_summary_mode_is_configurable(tmp_path: Path) -> None:
    config_path = tmp_path / "digest.json"
    config_path.write_text(json.dumps({"llm_summary_enabled": True}), encoding="utf-8")

    settings = resolve_settings(
        config_path,
        top_k=None,
        high=None,
        medium=None,
        max_lines=None,
        env={},
    )

    assert settings.llm_summary_enabled is True


def test_summary_mode_renders_model_summary_above_complete_deterministic_evidence(
    tmp_path: Path,
) -> None:
    claims, _ = _claim_rows()
    result = draft(
        _decision(),
        _cluster(),
        _items(),
        tmp_path,
        DigestSettings(llm_enabled=True, llm_summary_enabled=True),
        generator=lambda context: {
            "final_body": "A concise model summary.",
            "summary": {
                "status": "validated",
                "segments": [
                    {
                        "summary_id": "provider-id",
                        "text": "Both supplied claims matter.",
                        "supports": [
                            {"claim_fingerprint": claims[0]["claim_fingerprint"]},
                            {"claim_fingerprint": claims[1]["claim_fingerprint"]},
                        ],
                    }
                ],
            },
        },
    )[0]

    assert result["selected_round"] == 1
    assert result["summary"]["status"] == "validated"
    assert result["summary"]["segments"][0]["summary_id"] == "summary-1"
    assert "Both supplied claims matter." in result["final_body"]
    assert "## Evidence" in result["final_body"]
    assert result["final_body"].count("Claim one.") == 1
    assert result["final_body"].count("Claim two.") == 1
    assert "A concise model summary." not in result["final_body"]


def test_summary_rejects_omitted_protected_numbers_and_identifiers() -> None:
    claims = [
        {
            "claim_fingerprint": "fp-1",
            "text": "`select_detail_lines()` keeps at most 12 lines and cites at most 3 sources.",
        }
    ]
    valid, reason = _validate_summary(
        {
            "status": "validated",
            "segments": [
                {
                    "summary_id": "summary-1",
                    "text": "The process keeps 12 lines and cites a few sources.",
                    "supports": [{"claim_fingerprint": "fp-1"}],
                }
            ],
        },
        source_claims=claims,
        target="pages/one.md",
    )

    assert valid is False
    assert reason == "summary omitted protected number(s): 3"


def test_summary_repair_copies_exact_source_detail_instead_of_accepting_vague_wording() -> None:
    claims = [
        {
            "claim_fingerprint": "fp-1",
            "text": "`select_detail_lines()` keeps at most 12 lines and cites at most 3 sources.",
        }
    ]
    repaired = _repair_summary(
        {
            "status": "validated",
            "segments": [
                {
                    "summary_id": "summary-1",
                    "text": "The process keeps 12 lines and cites a few sources.",
                    "supports": [{"claim_fingerprint": "fp-1"}],
                }
            ],
        },
        source_claims=claims,
        target="pages/one.md",
    )

    repair_text = repaired["segments"][-1]["text"]
    assert "select_detail_lines()" in repair_text
    assert "at most 3" in repair_text
    valid, reason = _validate_summary(
        repaired,
        source_claims=claims,
        target="pages/one.md",
    )
    assert valid is True
    assert reason is None


def test_summary_support_fingerprint_shorthand_is_normalized_safely(tmp_path: Path) -> None:
    claims, _ = _claim_rows()
    result = draft(
        _decision(),
        _cluster(),
        _items(),
        tmp_path,
        DigestSettings(llm_enabled=True, llm_summary_enabled=True),
        generator=lambda context: {
            "final_body": "Ignored by summary mode.",
            "summary": {
                "status": "validated",
                "segments": [
                    {
                        "summary_id": "provider-id",
                        "text": "Both claims.",
                        "supports": [
                            claims[0]["claim_fingerprint"],
                            claims[1]["claim_fingerprint"],
                        ],
                    }
                ],
            },
        },
    )[0]

    assert result["selected_round"] == 1
    assert result["summary"]["segments"][0]["supports"][0]["claim_fingerprint"] == claims[0]["claim_fingerprint"]


def test_invalid_summary_reference_falls_back_without_losing_evidence(tmp_path: Path) -> None:
    result = draft(
        _decision(),
        _cluster(),
        _items(),
        tmp_path,
        DigestSettings(llm_enabled=True, llm_summary_enabled=True),
        generator=lambda context: {
            "final_body": "Unsafe summary.",
            "summary": {
                "status": "validated",
                "segments": [
                    {
                        "summary_id": "provider-id",
                        "text": "Unsupported statement.",
                        "supports": [{"claim_fingerprint": "unknown"}],
                    }
                ],
            },
        },
    )[0]

    assert result["selected_round"] is None
    assert result["summary"]["status"] == "rejected"
    assert result["fallback_reason"] == "no valid round; used claim fallback"
    assert "Unsafe summary." not in result["final_body"]
    assert "Claim one." in result["final_body"]
    assert "Claim two." in result["final_body"]


def test_llm_large_draft_is_generated_in_bounded_claim_batches(tmp_path: Path) -> None:
    items = [
        {
            "raw_id": "raw-batched",
            "text": "\n".join(f"Claim {index}." for index in range(1, 6)),
            "source_uri": "https://source.example/batched",
            "validation_status": "passed",
        }
    ]
    contexts: list[dict[str, Any]] = []

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        contexts.append(context)
        return {"final_body": context["initial_body"]}

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-batched"]}],
        items,
        tmp_path,
        DigestSettings(
            llm_enabled=True,
            llm_batch_max_claims=2,
            llm_batch_max_source_chars=10_000,
        ),
        generator=generator,
    )[0]

    assert sorted(len(context["claims"]) for context in contexts) == [1, 2, 2]
    assert all(f"Claim {index}." in result["final_body"] for index in range(1, 6))
    assert result["selected_round"] == 1
    assert result["rounds"][0]["provider_call_count"] == 3
    assert len(result["rounds"][0]["batches"]) == 3
    assert result["quality"]["coverage_ratio"] == 1.0

    planned = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-batched"]}],
        items,
        tmp_path / "dry",
        DigestSettings(
            llm_enabled=True,
            llm_batch_max_claims=2,
            llm_batch_max_source_chars=10_000,
        ),
        dry_run=True,
    )[0]
    assert planned["planned_generator_calls"] == 3


def test_invalid_llm_batch_falls_back_for_the_whole_draft(tmp_path: Path) -> None:
    items = [
        {
            "raw_id": "raw-batched",
            "text": "\n".join(f"Claim {index}." for index in range(1, 6)),
            "source_uri": "https://source.example/batched",
            "validation_status": "passed",
        }
    ]
    call_count = 0

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        if context["initial_body"].startswith("Claim 3."):
            return {"final_body": "Dropped the source claims."}
        return {"final_body": context["initial_body"]}

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-batched"]}],
        items,
        tmp_path,
        DigestSettings(
            llm_enabled=True,
            llm_batch_max_claims=2,
            llm_batch_max_source_chars=10_000,
        ),
        generator=generator,
    )[0]

    # Batches are independent and submitted together; a later invalid result
    # must still make the whole draft fall back, even though other calls may
    # already be in flight.
    assert call_count == 3
    assert result["selected_round"] is None
    assert result["rethink_status"] == "fallback"
    assert result["rounds"][0]["provider_call_count"] == 3
    assert result["rounds"][0]["stop_reason"].startswith("batch 2:")
    assert all(f"Claim {index}." in result["final_body"] for index in range(1, 6))


def test_provider_validation_error_keeps_deterministic_source_and_marks_review(
    tmp_path: Path,
) -> None:
    """A provider failure must not discard this source or pretend it passed."""
    def generator(_context: dict[str, Any]) -> dict[str, Any]:
        raise ValidationError("llm", "provider", "malformed JSON")

    result = draft(
        _decision(),
        _cluster(),
        _items(),
        tmp_path,
        DigestSettings(llm_enabled=True, llm_batch_max_claims=1),
        generator=generator,
    )[0]

    assert result["rethink_status"] == "fallback"
    assert result["provider_failure"] is True
    assert result["provider_failures"][0]["kind"] == "provider_error"
    assert result["fallback_reason"] == "no valid round; used claim fallback"
    assert "Claim one." in result["final_body"]
    assert "Claim two." in result["final_body"]


def test_llm_batch_concurrency_is_bounded_and_merge_order_is_stable(tmp_path: Path) -> None:
    items = [
        {
            "raw_id": "raw-concurrent",
            "text": "\n".join(f"Claim {index}." for index in range(1, 5)),
            "source_uri": "https://source.example/concurrent",
            "validation_status": "passed",
        }
    ]
    lock = threading.Lock()
    active = 0
    max_active = 0

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.03)
        with lock:
            active -= 1
        return {"final_body": context["initial_body"]}

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-concurrent"]}],
        items,
        tmp_path,
        DigestSettings(
            llm_enabled=True,
            llm_batch_max_claims=1,
            llm_batch_max_source_chars=10_000,
            llm_batch_concurrency=2,
        ),
        generator=generator,
    )[0]

    assert 2 <= max_active <= 2
    assert [batch["batch_index"] for batch in result["rounds"][0]["batches"]] == [1, 2, 3, 4]
    assert result["rounds"][0]["provider_call_count"] == 4
    assert result["selected_round"] == 1
    assert all(f"Claim {index}." in result["final_body"] for index in range(1, 5))


def test_llm_batching_never_splits_an_atomic_code_component(tmp_path: Path) -> None:
    body = "Example:\n```python\nvalue = 1\nprint(value)\n```"
    items = [
        {
            "raw_id": "raw-code",
            "text": body,
            "source_uri": "https://source.example/code",
            "validation_status": "passed",
        }
    ]
    contexts: list[dict[str, Any]] = []

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        contexts.append(context)
        return {"final_body": context["initial_body"]}

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-code"]}],
        items,
        tmp_path,
        DigestSettings(
            llm_enabled=True,
            llm_batch_max_claims=2,
            llm_batch_max_source_chars=20,
        ),
        generator=generator,
    )[0]

    assert len(contexts) == 1
    assert contexts[0]["initial_body"] == body
    assert result["rounds"][0]["batches"][0]["oversized_atomic"] is True
    assert result["final_body"] == body


def test_summary_batching_splits_oversized_atomic_claims_without_losing_evidence(
    tmp_path: Path,
) -> None:
    body = "Example:\n```python\nvalue = 1\nprint(value)\nvalue = 2\n```"
    items = [
        {
            "raw_id": "raw-summary-code",
            "text": body,
            "source_uri": "https://source.example/summary-code",
            "validation_status": "passed",
        }
    ]
    contexts: list[dict[str, Any]] = []

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        contexts.append(context)
        summary_numbers = " ".join(
            token
            for claim in context["claims"]
            for token in re.findall(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?", claim["text"])
        )
        return {
            "final_body": context["initial_body"],
            "claims": context["claims"],
            "coverage_mapping": [
                {
                    "raw_id": claim["raw_id"],
                    "source_uri": claim["source_uri"],
                    "input_fragment": claim["fragment_locator"],
                    "output_page": context["target_page"],
                    "fragment_locator": claim["fragment_locator"],
                    "claim_fingerprint": claim["claim_fingerprint"],
                }
                for claim in context["claims"]
            ],
            "summary": {
                "status": "validated",
                "segments": [
                    {
                        "summary_id": "summary-1",
                            "text": f"The code example is retained: {summary_numbers}.",
                        "supports": [
                            {"claim_fingerprint": claim["claim_fingerprint"]}
                            for claim in context["claims"]
                        ],
                    }
                ],
            },
        }

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-summary-code"]}],
        items,
        tmp_path,
        DigestSettings(
            llm_enabled=True,
            llm_summary_enabled=True,
            llm_batch_max_claims=1,
            llm_batch_max_source_chars=20,
        ),
        generator=generator,
    )[0]

    assert len(contexts) == 6
    assert all(len(context["claims"]) <= 1 for context in contexts)
    assert all(context["batch_oversized_atomic"] is False for context in contexts)
    assert result["selected_round"] == 1
    assert result["summary"]["status"] == "validated"
    assert "## Evidence" in result["final_body"]
    assert body in result["final_body"]


def test_llm_dropping_a_source_heading_rejects_the_whole_draft(tmp_path: Path) -> None:
    items = [
        {
            "raw_id": "raw-heading",
            "text": "# Required title\nSupported fact.",
            "source_uri": "https://source.example/heading",
            "validation_status": "passed",
        }
    ]

    contexts: list[dict[str, Any]] = []

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        contexts.append(context)
        return {
            "final_body": "Supported fact.",
            "claims": context["claims"],
        }

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-heading"]}],
        items,
        tmp_path,
        DigestSettings(llm_enabled=True),
        generator=generator,
    )[0]

    assert contexts[0]["initial_body"] == "# Required title\nSupported fact."
    assert result["selected_round"] is None
    assert result["rethink_status"] == "fallback"
    assert result["rounds"][0]["stop_reason"] == "candidate dropped source structure"
    assert result["final_body"] == "# Required title\nSupported fact."


def test_oversized_prose_section_keeps_its_heading_in_a_batch(tmp_path: Path) -> None:
    items = [
        {
            "raw_id": "raw-heading",
            "text": "# Required title\nSupported fact.",
            "source_uri": "https://source.example/heading",
            "validation_status": "passed",
        }
    ]
    contexts: list[dict[str, Any]] = []

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        contexts.append(context)
        return {"final_body": context["initial_body"]}

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-heading"]}],
        items,
        tmp_path,
        DigestSettings(
            llm_enabled=True,
            llm_batch_max_claims=1,
            llm_batch_max_source_chars=1,
        ),
        generator=generator,
    )[0]

    assert contexts[0]["initial_body"] == "# Required title"
    assert result["selected_round"] == 1
    assert "# Required title" in result["final_body"]


def test_llm_cannot_merge_two_code_blocks_by_dropping_repeated_fences(tmp_path: Path) -> None:
    source = "```python\nvalue = 1\n```\n```python\nvalue = 2\n```"
    items = [
        {
            "raw_id": "raw-fences",
            "text": source,
            "source_uri": "https://source.example/fences",
            "validation_status": "passed",
        }
    ]

    result = draft(
        _decision(),
        [{"cluster_id": "cluster-1", "tier": "auto", "members": ["raw-fences"]}],
        items,
        tmp_path,
        DigestSettings(),
        generator=lambda context: {
            "final_body": "```python\nvalue = 1\nvalue = 2\n```",
            "claims": context["claims"],
        },
    )[0]

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate dropped source structure"
    assert result["final_body"] == source


def _kb_case(tmp_path: Path) -> tuple[Path, Path]:
    new_dir = tmp_path / "new"
    (new_dir / "items").mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "kb.structure.md").write_text(
        "---\ncontract_version: phase2\nroots: [pages, _archive, _queues]\n"
        "why_field: why\nversion_field: version\npublication_home: Home.md\n"
        "publication_index_root: indexes\npublication_categories:\n"
        "  - id: pending\n    title: 待归类\n    topic_dir: pages/待归类\n---\n",
        encoding="utf-8",
    )
    (new_dir / "items" / "source.md").write_text("Claim one.\nClaim two.\n", encoding="utf-8")
    (new_dir / "sources.jsonl").write_text(
        json.dumps({"content_path": "source.md", "source_uri": "https://source.example/llm"}) + "\n",
        encoding="utf-8",
    )
    return new_dir, kb_dir


def test_end_to_end_fallback_page_keeps_every_source_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When the LLM drops a claim, the committed page must still carry it."""
    seen = _capture(monkeypatch, _openai_payload(json.dumps({"final_body": "Claim one."})))
    new_dir, kb_dir = _kb_case(tmp_path)
    paths = validate_paths(new_dir, kb_dir)
    roots = parse_roots(paths.structure_path)
    generator = llm.build_generator(api_format="openai", **PROVIDER)

    audit_run(paths, DigestSettings(), roots, dry_run=False, generator=generator)

    assert seen, "LLM urlopen stub was never called"
    pages = list((kb_dir / "pages").rglob("*.md"))
    assert pages, "expected a committed page"
    written = "\n".join(page.read_text(encoding="utf-8") for page in pages)
    for line in ("Claim one.", "Claim two."):
        assert line in written


def test_end_to_end_provider_error_publishes_source_and_pending_review(
    tmp_path: Path,
) -> None:
    """A transport/JSON failure keeps deterministic output and a replay queue."""
    new_dir, kb_dir = _kb_case(tmp_path)
    paths = validate_paths(new_dir, kb_dir)
    roots = parse_roots(paths.structure_path)

    def generator(_context: dict[str, Any]) -> dict[str, Any]:
        raise ValidationError("llm", "provider", "malformed JSON")

    audit_run(
        paths,
        DigestSettings(llm_enabled=True),
        roots,
        dry_run=False,
        generator=generator,
    )

    pages = list((kb_dir / "pages").rglob("*.md"))
    assert pages
    written = "\n".join(page.read_text(encoding="utf-8") for page in pages)
    assert "Claim one." in written and "Claim two." in written
    pending = (kb_dir / "_digest" / "pending-review.jsonl").read_text(encoding="utf-8")
    assert "malformed JSON" in pending
    from knowledge_digest.kb_structure import parse_source_index_markdown

    source_index = parse_source_index_markdown((kb_dir / "_digest" / "source-index.md").read_text(encoding="utf-8"))
    assert source_index["entries"][0]["status"] == "needs-review"
    assert "https://source.example/llm" in (kb_dir / "_queues" / "needs_review.md").read_text(encoding="utf-8")
    report = json.loads(next((kb_dir / "_digest").glob("runs/*/report.json")).read_text(encoding="utf-8"))
    assert report["pending_review"]


def test_end_to_end_retention_gate_keeps_a_dropped_claim_on_the_committed_page(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The retention gate must protect the page on disk, not just the round record.

    The provider returns a self-consistent candidate that simply omits one
    claim (claims list AND coverage_mapping both shortened). Every per-claim
    gate would pass it; only the retention gate rejects it, so the run falls
    back and the committed markdown still carries both source lines.
    """
    new_dir, kb_dir = _kb_case(tmp_path)
    paths = validate_paths(new_dir, kb_dir)
    roots = parse_roots(paths.structure_path)

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        kept = [dict(claim) for claim in context["claims"]][:1]
        return {
            "final_body": "## Refined by the model\n\n" + "\n".join(c["text"] for c in kept),
            "claims": kept,
            "coverage_mapping": [
                {
                    "raw_id": claim["raw_id"],
                    "source_uri": claim["source_uri"],
                    "input_fragment": claim["fragment_locator"],
                    "output_page": context["target_page"],
                    "fragment_locator": claim["fragment_locator"],
                    "claim_fingerprint": claim["claim_fingerprint"],
                }
                for claim in kept
            ],
        }

    audit_run(paths, DigestSettings(), roots, dry_run=False, generator=generator)

    pages = list((kb_dir / "pages").rglob("*.md"))
    assert pages, "expected a committed page"
    written = "\n".join(page.read_text(encoding="utf-8") for page in pages)
    for line in ("Claim one.", "Claim two."):
        assert line in written
    assert "## Refined by the model" not in written


def test_end_to_end_accepted_llm_body_reaches_the_committed_page(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A faithful refinement must be observably different from the identity path."""
    new_dir, kb_dir = _kb_case(tmp_path)
    paths = validate_paths(new_dir, kb_dir)
    roots = parse_roots(paths.structure_path)

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        claims = [dict(claim) for claim in context["claims"]]
        return {
            "final_body": "## Refined by the model\n\n" + "\n".join(claim["text"] for claim in claims),
            "claims": claims,
            "coverage_mapping": [
                {
                    "raw_id": claim["raw_id"],
                    "source_uri": claim["source_uri"],
                    "input_fragment": claim["fragment_locator"],
                    "output_page": context["target_page"],
                    "fragment_locator": claim["fragment_locator"],
                    "claim_fingerprint": claim["claim_fingerprint"],
                }
                for claim in claims
            ],
        }

    audit_run(paths, DigestSettings(), roots, dry_run=False, generator=generator)

    written = "\n".join(
        page.read_text(encoding="utf-8") for page in (kb_dir / "pages").rglob("*.md")
    )
    assert "## Refined by the model" in written
    for line in ("Claim one.", "Claim two."):
        assert line in written


def test_llm_forging_claim_lineage_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A real claim must not be re-attributed to another line.

    Text, source_uri and fingerprint are all genuine here, so the recompute and
    source-membership gates both pass. Only binding fingerprint -> source
    (raw_id, fragment_locator) catches the forged locator, which would otherwise
    point the provenance trail at the wrong input line.
    """
    claims, coverage = _claim_rows()
    forged = dict(claims[0], fragment_locator="lines:99-99")
    forged_coverage = dict(coverage[0], input_fragment="lines:99-99", fragment_locator="lines:99-99")
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "Claim one.\nClaim two.",
            "claims": [forged] + claims[1:],
            "coverage_mapping": [forged_coverage] + coverage[1:],
        },
    )

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate claim lineage does not match the source record"
    assert result["rethink_status"] == "fallback"


def test_llm_forging_claim_raw_id_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The same binding must also reject a swapped raw_id, not only the locator."""
    claims, coverage = _claim_rows()
    forged = dict(claims[0], raw_id="raw-999")
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {
            "final_body": "Claim one.\nClaim two.",
            "claims": [forged] + claims[1:],
            "coverage_mapping": coverage,
        },
    )

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate claim lineage does not match the source record"


def test_llm_collapsing_a_duplicated_source_line_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Two identical source lines share one fingerprint and must both be retained.

    With a set-based retention gate a single candidate claim satisfies the subset
    check and one of the two source claims is silently dropped. Only a multiset
    (Counter) comparison sees the missing copy.
    """
    from knowledge_digest.faithfulness import verify_claims

    items = [
        {
            "raw_id": "raw-1",
            "text": "Claim one.\nClaim one.\n",
            "source_uri": "https://source.example/one",
            "validation_status": "passed",
        }
    ]
    source_claims, _ = verify_claims(items)
    assert len({claim["claim_fingerprint"] for claim in source_claims}) == 1
    assert len(source_claims) == 2

    kept = dict(source_claims[0])
    _capture(monkeypatch, _openai_payload(json.dumps({
        "final_body": "Claim one.",
        "claims": [kept],
        "coverage_mapping": [
            {
                "raw_id": kept["raw_id"],
                "source_uri": kept["source_uri"],
                "input_fragment": kept["fragment_locator"],
                "output_page": "pages/one.md",
                "fragment_locator": kept["fragment_locator"],
                "claim_fingerprint": kept["claim_fingerprint"],
            }
        ],
    })))
    generator = llm.build_generator(api_format="openai", **PROVIDER)
    result = draft(_decision(), _cluster(), items, tmp_path, DigestSettings(), generator=generator)[0]

    assert result["selected_round"] is None
    assert result["rounds"][0]["stop_reason"] == "candidate dropped a source claim"
    assert result["rounds"][0]["unsupported_claim_count"] == 1
    # The fallback keeps both copies rather than losing the duplicate line.
    assert result["final_body"].count("Claim one.") == 2


@pytest.mark.parametrize(
    "malformed_claims",
    [None, "not a list", 42, ["not a mapping"], [{"text": "Claim one."}, "not a mapping"]],
)
def test_malformed_provider_claims_fall_back_instead_of_crashing_the_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, malformed_claims: Any
) -> None:
    """Provider output is adversarial: a bad ``claims`` field must not kill the run.

    Deserializing these shapes used to raise TypeError/ValueError straight out of
    draft(), losing every cluster in the run. They must instead be judged invalid
    and routed through the existing fallback so no content is dropped.
    """
    result = _llm_draft(
        monkeypatch,
        tmp_path,
        {"final_body": "Claim one.\nClaim two.", "claims": malformed_claims},
    )

    assert result["selected_round"] is None
    assert result["rethink_status"] == "fallback"
    assert result["rounds"][0]["stop_reason"] == "generator returned a malformed claims field"
    for line in ("Claim one.", "Claim two."):
        assert line in result["final_body"]
