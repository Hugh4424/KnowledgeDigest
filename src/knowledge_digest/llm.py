"""LLM refinement generator over OpenAI- and Anthropic-compatible HTTP APIs.

Standard library only: no runtime third-party dependency is introduced. A
request has a hard wall-clock deadline. Only transport failures may be retried
when explicitly configured; invalid provider output never retries or silently
downgrades to the identity generator.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import signal
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from typing import Any, Callable, Iterator

from .errors import ValidationError
from .faithfulness import normalize_claim


OPENAI_FORMAT = "openai"
ANTHROPIC_FORMAT = "anthropic"
SUPPORTED_FORMATS = (OPENAI_FORMAT, ANTHROPIC_FORMAT)
DEFAULT_TIMEOUT_SECONDS = 60
# The provider spends part of its budget on hidden reasoning even though the
# client only persists final content. Keep enough headroom for a publication
# object that references a large claim batch; the parser still rejects any
# non-JSON or truncated final content.
DEFAULT_MAX_TOKENS = 8192
TIMEOUT_ENV = "KD_LLM_TIMEOUT_SECONDS"
RETRY_ENV = "KD_LLM_RETRY_ATTEMPTS"
DEFAULT_RETRY_ATTEMPTS = 0
PUBLICATION_LLM_MODEL = "qwen3.6"
PUBLICATION_LLM_BASE_URL = "https://dashscope.in.whatspos.cn/v1"
_ORIGINAL_URLOPEN = urllib.request.urlopen


@contextmanager
def _hard_deadline(seconds: int) -> Iterator[None]:
    """Bound a blocking urllib read, not only each individual socket read."""
    if threading.current_thread() is not threading.main_thread() or not hasattr(signal, "SIGALRM"):
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)

    def handle_timeout(_signum: int, _frame: Any) -> None:
        raise TimeoutError(f"deadline exceeded after {seconds}s")

    signal.signal(signal.SIGALRM, handle_timeout)
    timer = threading.Timer(
        float(seconds), os.kill, args=(os.getpid(), signal.SIGALRM)
    )
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()
        signal.signal(signal.SIGALRM, previous_handler)

_PROMPT_RULES = """You refine knowledge-base notes. Return ONLY one JSON object.

Schema:
{"final_body": "<the refined markdown page>",
 "claims": [{"claim_fingerprint": "...", "text": "...", "source_uri": "...", "fragment_locator": "...", "raw_id": "..."}],
 "coverage_mapping": [{"raw_id": "...", "source_uri": "...", "input_fragment": "...", "output_page": "...", "fragment_locator": "...", "claim_fingerprint": "..."}]}

Loss-prevention rules (violating any one makes the output rejected):
1. Never drop a claim. Every claim given below must appear in "claims" with its
   claim_fingerprint, source_uri, fragment_locator and raw_id copied verbatim.
2. Never truncate. Never delete a line because of a surface rule such as
   "ends with a question mark", "looks alphanumeric", or "is bilingual".
3. Every claim "text" must appear VERBATIM, character for character, as a
   substring of "final_body". Do not reword, translate, re-punctuate, merge or
   summarize claim text. This is a hard gate: any paraphrase is rejected and
   the whole refinement is discarded.
4. Keep tables, code blocks and fenced content in their original structure.
   Never rewrite structured content into prose.
5. Keep statements of decision motivation (why) and version history.
6. "coverage_mapping" must contain one row per claim; copy raw_id,
   source_uri, claim_fingerprint and set input_fragment and fragment_locator to
   the claim's fragment_locator, and output_page to the given target page.

You may reorder, add headings, and remove exact duplicate lines, as long as
every claim text still appears verbatim in final_body."""

_SUMMARY_PROMPT_RULES = _PROMPT_RULES.replace(
    '''3. Every claim "text" must appear VERBATIM, character for character, as a
   substring of "final_body". Do not reword, translate, re-punctuate, merge or
   summarize claim text. This is a hard gate: any paraphrase is rejected and
   the whole refinement is discarded.''',
    '3. In summary mode, every claim must remain in "claims" with its exact text. The concise model text in "final_body" may summarize, but it must not replace or alter the claims; the system will append a deterministic Evidence section containing the complete source body.',
)
_SUMMARY_PROMPT_RULES += """

SUMMARY MODE:
Return an additional nested object:
{"summary":{"status":"validated","segments":[{"summary_id":"summary-1","text":"...","supports":[{"claim_fingerprint":"..."}]}]}}
Each summary segment must be concise, factual, and supported only by the supplied
claim fingerprints. Reference every supplied claim at least once across
supports. Do not invent a claim or a source. The system will render the full
source body as Evidence, so summary text is never the sole copy of a fact."""
_SUMMARY_PROMPT_RULES += """

Summary fidelity requirements:
- Preserve every number, date, percentage, count, range, version, path,
  command, identifier, and named tool that is material to the supported claims.
- Preserve qualifiers and conditions such as approximately, at least, default,
  may, must, still, only, no, and not; never turn a possibility into a fact.
- Never replace an exact limit or identifier with vague wording such as "a few",
  "some", or "many". Copy the exact number and identifier from the claim.
- Do not merge separate limits or causes into one broader statement. If a
  detail cannot be stated safely, leave it in Evidence rather than guessing."""


def _endpoint(base_url: str, api_format: str) -> str:
    root = base_url.rstrip("/")
    if api_format == OPENAI_FORMAT:
        return f"{root}/chat/completions"
    return f"{root}/v1/messages"


def _request_payload(api_format: str, model: str, prompt: str) -> dict[str, Any]:
    messages = [{"role": "user", "content": prompt}]
    if api_format == OPENAI_FORMAT:
        # Bound provider output for OpenAI-compatible endpoints. Without an
        # explicit cap, qwen3.6 may spend the entire transport deadline on
        # unbounded reasoning/output before it can return the JSON contract.
        return {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": DEFAULT_MAX_TOKENS,
        }
    return {"model": model, "max_tokens": DEFAULT_MAX_TOKENS, "messages": messages}


def _extract_text(api_format: str, payload: Any) -> str:
    try:
        if api_format == OPENAI_FORMAT:
            return str(payload["choices"][0]["message"]["content"])
        return str(payload["content"][0]["text"])
    except (KeyError, IndexError, TypeError) as error:
        raise ValidationError("llm", api_format, f"unexpected response shape ({error})") from error


def _request_result(request: urllib.request.Request, *, timeout: int) -> dict[str, Any]:
    """Perform the raw HTTP request and return a pipe-safe result object."""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", None) or response.getcode()
            if not 200 <= int(status) < 300:
                raise ValidationError("llm", status, "provider returned a non-success status")
            return {"ok": True, "raw": response.read().decode("utf-8")}
    except ValidationError as error:
        return {
            "ok": False,
            "stage": error.stage,
            "failed_input": error.failed_input,
            "reason": error.reason,
        }
    except urllib.error.HTTPError as error:
        return {
            "ok": False,
            "stage": "llm",
            "failed_input": str(error.code),
            "reason": "provider returned a non-success status",
        }
    except (urllib.error.URLError, OSError, TimeoutError) as error:
        return {
            "ok": False,
            "stage": "llm",
            "failed_input": request.full_url,
            "reason": f"provider request failed ({error})",
        }


def _request_in_spawned_process(
    url: str,
    data: bytes | None,
    headers: dict[str, str],
    method: str,
    timeout: int,
    result_connection: multiprocessing.connection.Connection,
) -> None:
    """Make one request in a fresh interpreter and return a pipe-safe result."""
    try:
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        result = _request_result(request, timeout=timeout)
        payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
        result_connection.send_bytes(payload)
    except BaseException as error:
        fallback = json.dumps(
            {
                "ok": False,
                "stage": "llm",
                "failed_input": url,
                "reason": f"provider request failed ({error})",
            }
        ).encode("utf-8")
        try:
            result_connection.send_bytes(fallback)
        except (BrokenPipeError, OSError):
            pass
    finally:
        result_connection.close()


def _stop_process(process: multiprocessing.Process) -> None:
    if process.is_alive():
        process.terminate()
    process.join()


def _request_in_child(request: urllib.request.Request, *, timeout: int) -> str:
    """Run a real network call behind a killable wall-clock boundary.

    ``spawn`` is required here: forking a Python process from the batch worker
    threads is unsafe on macOS and can abort inside the Objective-C runtime.
"""

    context = multiprocessing.get_context("spawn")
    parent_connection, child_connection = context.Pipe(duplex=False)
    process = context.Process(
        target=_request_in_spawned_process,
        args=(
            request.full_url,
            request.data,
            dict(request.header_items()),
            request.get_method(),
            timeout,
            child_connection,
        ),
    )
    try:
        process.start()
    except BaseException as error:
        parent_connection.close()
        child_connection.close()
        raise ValidationError(
            "llm", request.full_url, f"provider request failed ({error})"
        ) from error
    child_connection.close()

    deadline = time.monotonic() + timeout
    payload: bytes | None = None
    try:
        while True:
            remaining = max(0.0, deadline - time.monotonic())
            if parent_connection.poll(min(0.2, remaining)):
                try:
                    payload = parent_connection.recv_bytes()
                except (EOFError, OSError):
                    payload = None
                break
            if not process.is_alive():
                break
            if time.monotonic() >= deadline:
                _stop_process(process)
                raise ValidationError(
                    "llm",
                    request.full_url,
                    f"provider request failed (deadline exceeded after {timeout}s)",
                )
    finally:
        parent_connection.close()
        if process.is_alive():
            _stop_process(process)
        else:
            process.join()

    if not payload:
        raise ValidationError("llm", request.full_url, "provider request failed (child returned no result)")
    try:
        result = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("llm", request.full_url, f"provider request failed (invalid child result: {error})") from error
    if not result.get("ok"):
        raise ValidationError(
            str(result.get("stage", "llm")),
            result.get("failed_input", request.full_url),
            str(result.get("reason", "provider request failed")),
        )
    return str(result["raw"])

_PUBLICATION_OUTPUT_SCHEMA = """{
  "publication": {
    "title": "4-80 character reader title",
    "slug": "lowercase ascii suggestion",
    "category_id": "one allowed leaf category id",
    "summary": "verified one-paragraph summary",
    "why": "reader use or explicit missing marker",
    "version": "version/history or explicit missing marker",
    "related_topics": ["known topic ids only"],
    "claim_refs": ["claim fingerprints"],
    "field_refs": {"title": ["claim fingerprints"], "category_id": ["claim fingerprints"], "summary": ["claim fingerprints"], "why": ["claim fingerprints"], "version": ["claim fingerprints"]}
  }
}"""


def validate_publication_provider_identity(*, model: str, base_url: str) -> None:
    """Reject providers outside the user-approved Task2 publication seam."""
    if model != PUBLICATION_LLM_MODEL or base_url.rstrip("/") != PUBLICATION_LLM_BASE_URL:
        raise ValidationError("llm", model or base_url, "Task2 publication allows only qwen3.6 at the approved endpoint")


def publication_prompt_sections(context: dict[str, Any]) -> str:
    """Return the four fixed prompt sections for semantic publication."""
    evidence = [
        {
            "claim_fingerprint": claim.get("claim_fingerprint"),
            "text": claim.get("text"),
            "source_uri": claim.get("source_uri"),
            "fragment_locator": claim.get("fragment_locator"),
        }
        for claim in context.get("claims", [])
    ]
    taxonomy = context.get("allowed_taxonomy", [])
    return "\n\n".join(
        (
            "ROLE:\nYou provide semantic publication suggestions only. Do not create facts, paths, permissions, or taxonomy entries.",
            "EVIDENCE:\n" + json.dumps(evidence, ensure_ascii=False, indent=2),
            "ALLOWED TAXONOMY:\n" + json.dumps(taxonomy, ensure_ascii=False, indent=2),
            "OUTPUT SCHEMA:\n" + _PUBLICATION_OUTPUT_SCHEMA + "\nReturn only final JSON content; never include reasoning_content or <think> text.",
        )
    )



def call_llm(
    prompt: str,
    *,
    api_format: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """POST one completion request and return the raw assistant text."""
    if api_format not in SUPPORTED_FORMATS:
        raise ValidationError("llm", api_format, f"format must be one of {', '.join(SUPPORTED_FORMATS)}")
    for env_name, value in (("KD_LLM_API_KEY", api_key), ("KD_LLM_BASE_URL", base_url), ("KD_LLM_MODEL", model)):
        if not value:
            raise ValidationError("llm", env_name, f"{env_name} is required")

    body = _request_payload(api_format, model, prompt)
    headers = {"content-type": "application/json"}
    if api_format == OPENAI_FORMAT:
        headers["authorization"] = f"Bearer {api_key}"
    else:
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"

    request = urllib.request.Request(
        _endpoint(base_url, api_format),
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    if urllib.request.urlopen is _ORIGINAL_URLOPEN and hasattr(os, "fork"):
        raw = _request_in_child(request, timeout=timeout)
    else:
        try:
            with _hard_deadline(timeout):
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    status = getattr(response, "status", None) or response.getcode()
                    if not 200 <= int(status) < 300:
                        raise ValidationError("llm", status, "provider returned a non-success status")
                    raw = response.read().decode("utf-8")
        except ValidationError:
            raise
        except urllib.error.HTTPError as error:
            raise ValidationError("llm", error.code, "provider returned a non-success status") from error
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            raise ValidationError("llm", base_url, f"provider request failed ({error})") from error
    try:
        return _extract_text(api_format, json.loads(raw))
    except json.JSONDecodeError as error:
        raise ValidationError("llm", base_url, f"provider returned invalid JSON ({error})") from error


def build_prompt(context: dict[str, Any], *, target_page: str) -> str:
    """Render the structured refinement prompt from a draft generator context."""
    claims = [
        {
            "claim_fingerprint": claim.get("claim_fingerprint"),
            "text": claim.get("text"),
            "source_uri": claim.get("source_uri"),
            "fragment_locator": claim.get("fragment_locator"),
            "raw_id": claim.get("raw_id"),
        }
        for claim in context.get("claims", [])
    ]
    payload = {
        "target_page": target_page,
        "initial_body": context.get("initial_body", ""),
        "source_text": context.get("source_text", ""),
        "existing_target_body": context.get("old_target_body", ""),
        "claims": claims,
    }
    if context.get("publication_enabled") and context.get("publication_only"):
        publication = publication_prompt_sections(context)
        summary_contract = (
            " Return an additional `summary` object exactly shaped as "
            "{\"status\":\"validated\",\"segments\":[{\"summary_id\":\"summary-1\","
            "\"text\":\"...\",\"supports\":[{\"claim_fingerprint\":\"...\"}]}]}; "
            "every supplied claim fingerprint must be referenced at least once."
            if context.get("summary_enabled")
            else ""
        )
        return (
            "ROLE: You provide compact semantic publication metadata only. "
            "This is publication-only mode; Do not return final_body, rewritten "
            "claims, paths, permissions, or new taxonomy entries.\n\n"
            f"{publication}\n\n"
            "OUTPUT CONTRACT: Return one JSON object containing the required "
            "top-level `publication` object. It must use only the supplied claim "
            "fingerprints and allowed taxonomy."
            f"{summary_contract}\n\n"
            "INPUT:\n"
            + json.dumps(
                {"target_page": target_page, "claims": claims},
                ensure_ascii=False,
                indent=2,
            )
        )
    summary_enabled = bool(context.get("summary_enabled", False))
    payload["summary_enabled"] = summary_enabled
    rules = _SUMMARY_PROMPT_RULES if summary_enabled else _PROMPT_RULES
    publication = publication_prompt_sections(context) if context.get("publication_enabled") else ""
    publication_requirement = (
        "\n\nMANDATORY OUTPUT CONTRACT: The top-level JSON object MUST include the "
        "top-level publication object shown above. Do not omit it, move its "
        "fields to the root, or return the legacy schema alone. Keep final_body, "
        "claims, coverage_mapping, and summary as required by the loss-prevention contract."
        if publication
        else ""
    )
    prefix = f"{rules}\n\n{publication}{publication_requirement}\n\n" if publication else f"{rules}\n\n"
    final_reminder = (
        "\n\nFINAL REMINDER: Return one JSON object now. It MUST contain a non-empty "
        "top-level `publication` object with title, slug, category_id, summary, "
        "why, version, related_topics, claim_refs, and field_refs."
        if publication
        else ""
    )
    return f"{prefix}INPUT:\n{json.dumps(payload, ensure_ascii=False, indent=2)}{final_reminder}"


def parse_response(text: str, *, require_final_body: bool = True) -> dict[str, Any]:
    """Parse the provider text into the candidate mapping draft.py expects."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as error:
        raise ValidationError("llm", "response", f"provider output is not JSON ({error})") from error
    if not isinstance(parsed, dict) or (require_final_body and "final_body" not in parsed):
        raise ValidationError("llm", "response", "provider output must be an object with final_body")
    return parsed


def _restore_source_lineage(
    candidate: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Restore trusted internal lineage only when a claim match is unambiguous.

    Providers are asked to echo ``raw_id``, but it is transport metadata rather
    than generated content.  A missing value can therefore be recovered from
    the trusted prompt context after the provider has echoed the claim's exact
    fingerprint, text, source URI, and fragment locator.  Explicit conflicting
    IDs are left untouched so draft.py's lineage gate still rejects them.
    Provenance fields that providers are not asked to generate are always
    copied from that same trusted source record.
    """
    source_claims = [
        dict(claim)
        for claim in context.get("claims", [])
        if isinstance(claim, dict)
    ]

    def source_for(row: dict[str, Any], *, coverage: bool) -> dict[str, Any] | None:
        locator = row.get("input_fragment") if coverage else row.get("fragment_locator")
        matches = [
            claim
            for claim in source_claims
            if claim.get("claim_fingerprint") == row.get("claim_fingerprint")
            and claim.get("source_uri") == row.get("source_uri")
            and claim.get("fragment_locator") == locator
            and (coverage or normalize_claim(str(claim.get("text", ""))) == normalize_claim(str(row.get("text", ""))))
        ]
        if len(matches) != 1 or not matches[0].get("raw_id"):
            return None
        return matches[0]

    restored = dict(candidate)
    for field, coverage in (("claims", False), ("coverage_mapping", True)):
        rows = restored.get(field)
        if not isinstance(rows, list):
            continue
        normalized: list[Any] = []
        for value in rows:
            if not isinstance(value, dict):
                normalized.append(value)
                continue
            row = dict(value)
            if not row.get("raw_id"):
                source = source_for(row, coverage=coverage)
                if source is not None:
                    row["raw_id"] = source["raw_id"]
            elif coverage:
                source = None
            else:
                source = source_for(row, coverage=False)
            if source is not None and not coverage:
                for name in (
                    "content_fingerprint",
                    "source_snapshot_ref",
                    "input_path",
                    "validation_status",
                    "verification_status",
                ):
                    if source.get(name) is not None:
                        row[name] = source[name]
                    else:
                        row.pop(name, None)
            normalized.append(row)
        restored[field] = normalized
    return restored


def build_generator(
    *,
    api_format: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a ``generator(context)`` callable backed by a live provider."""

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        if context.get("publication_provider_enforced"):
            validate_publication_provider_identity(model=model, base_url=base_url)
        prompt = build_prompt(context, target_page=str(context.get("target_page", "")))
        for attempt in range(1, retry_attempts + 2):
            try:
                result = _restore_source_lineage(
                    parse_response(
                        call_llm(
                            prompt,
                            api_format=api_format,
                            base_url=base_url,
                            api_key=api_key,
                            model=model,
                            timeout=timeout,
                        ),
                        require_final_body=not bool(context.get("publication_only")),
                    ),
                    context,
                )
                result["provider_attempt_count"] = attempt
                return result
            except ValidationError as error:
                if attempt > retry_attempts or not error.reason.startswith("provider request failed"):
                    raise
        raise AssertionError("unreachable retry loop")

    return generator


def generator_from_env(
    *, api_format: str | None = None, env: dict[str, str] | None = None
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a provider generator from ``KD_LLM_*`` environment variables."""
    source = dict(os.environ if env is None else env)
    timeout_text = source.get(TIMEOUT_ENV)
    if timeout_text is None:
        timeout = DEFAULT_TIMEOUT_SECONDS
    else:
        try:
            timeout = int(timeout_text)
        except ValueError as error:
            raise ValidationError("llm", TIMEOUT_ENV, f"{TIMEOUT_ENV} must be an integer") from error
        if timeout <= 0:
            raise ValidationError("llm", TIMEOUT_ENV, f"{TIMEOUT_ENV} must be greater than zero")
    retry_text = source.get(RETRY_ENV)
    if retry_text is None:
        retry_attempts = DEFAULT_RETRY_ATTEMPTS
    else:
        try:
            retry_attempts = int(retry_text)
        except ValueError as error:
            raise ValidationError("llm", RETRY_ENV, f"{RETRY_ENV} must be an integer") from error
        if retry_attempts < 0:
            raise ValidationError("llm", RETRY_ENV, f"{RETRY_ENV} must not be negative")
    return build_generator(
        api_format=api_format or source.get("KD_LLM_FORMAT") or OPENAI_FORMAT,
        base_url=source.get("KD_LLM_BASE_URL", ""),
        api_key=source.get("KD_LLM_API_KEY", ""),
        model=source.get("KD_LLM_MODEL", ""),
        timeout=timeout,
        retry_attempts=retry_attempts,
    )
