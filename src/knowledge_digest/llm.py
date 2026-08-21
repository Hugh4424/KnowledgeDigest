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
import re
import signal
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Mapping

from .errors import ValidationError
from .faithfulness import normalize_claim, normalize_for_gate
from .publication import (
    PAGE_TYPE_OPTIONAL_SECTIONS,
    PAGE_TYPE_SECTION_MATRIX,
    _claim_is_supported_by_body,
    _continuous_source_block_check,
)
from .provider_config import effective_llm_environment


OPENAI_FORMAT = "openai"
ANTHROPIC_FORMAT = "anthropic"
SUPPORTED_FORMATS = (OPENAI_FORMAT, ANTHROPIC_FORMAT)
DEFAULT_TIMEOUT_SECONDS = 60
# The provider spends part of its budget on hidden reasoning even though the
# client only persists final content. Keep enough headroom for a publication
# object that references a large claim batch; the parser still rejects any
# non-JSON or truncated final content.
DEFAULT_MAX_TOKENS = 8192
# qwen3.6 may spend part of the completion budget on hidden reasoning even
# when the publication prompt asks for compact JSON.  Keep enough room for the
# contract instead of treating a truncated empty content field as a semantic
# result.
PUBLICATION_MAX_TOKENS = 8192
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


def _request_payload(
    api_format: str,
    model: str,
    prompt: str,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    json_mode: bool = False,
) -> dict[str, Any]:
    messages = [{"role": "user", "content": prompt}]
    if api_format == OPENAI_FORMAT:
        # Bound provider output for OpenAI-compatible endpoints. Without an
        # explicit cap, qwen3.6 may spend the entire transport deadline on
        # unbounded reasoning/output before it can return the JSON contract.
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        if json_mode or model == PUBLICATION_LLM_MODEL:
            payload["response_format"] = {"type": "json_object"}
        if model == PUBLICATION_LLM_MODEL:
            # The approved qwen OpenAI bridge understands JSON mode.  It does
            # not expose reasoning_content to the client.  The bridge only
            # honors the no-thinking switch through chat_template_kwargs;
            # sending enable_thinking alone still burns the completion budget
            # on hidden reasoning and can truncate the JSON body.
            payload["enable_thinking"] = False
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        return payload
    return {"model": model, "max_tokens": max_tokens, "messages": messages}


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

_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_STRUCTURED_SOURCE_KINDS = frozenset({"table", "bilingual", "image", "code", "version"})


def _typed_source_outline(
    source_text: str, claims: list[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Keep only non-claim structure in the typed provider context.

    Typed claims already carry the complete trusted source text and lineage.
    Sending the raw source again can duplicate a long page inside the prompt
    and make the provider truncate its JSON response. Headings, code fences,
    table separators, and unclaimed table headers preserve enough layout to
    map claims without sending a second copy of the evidence.
    """
    claim_texts = {
        str(claim.get("text", "")).strip()
        for claim in claims
        if str(claim.get("text", "")).strip()
    }
    outline: list[dict[str, Any]] = []
    for line_number, line in enumerate(str(source_text or "").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            kind = "heading"
        elif stripped.startswith(("```", "~~~")):
            kind = "code_fence"
        elif _TABLE_SEPARATOR_RE.fullmatch(stripped):
            kind = "table_separator"
        elif _TABLE_ROW_RE.fullmatch(stripped) and stripped not in claim_texts:
            kind = "table_row"
        else:
            continue
        outline.append({"line": line_number, "kind": kind, "text": stripped})
    return outline


def _is_format_only_claim(claim: Mapping[str, Any]) -> bool:
    """Identify Markdown table delimiter claims with no reader fact."""
    return bool(_TABLE_SEPARATOR_RE.fullmatch(str(claim.get("text", ""))))


def _source_not_documented_audit(
    page_draft: Mapping[str, Any],
    section_id: str,
) -> Mapping[str, Any] | None:
    audits = page_draft.get("section_audits")
    if not isinstance(audits, Mapping):
        return None
    audit = audits.get(section_id)
    if not isinstance(audit, Mapping) or audit.get("status") != "source_not_documented":
        return None
    return audit

_TYPED_BODY_RULES = """You compile one typed knowledge-base page. Return ONLY one JSON object.

Typed body schema:
{"page_type":"<supplied page type>",
 "sections":{"<required section>":{"body":"<reader-facing text>","claim_ids":["<supplied provider claim ref>"]}},
 "publication": {<optional semantic publication metadata>},
 "summary": {<optional validated summary object>}}

Typed body rules:
1. Copy page_type exactly from the supplied typed page contract.
2. Return every required section exactly once; optional sections are allowed only when the source supports them.
3. Do not add sections, page types, source fields, claims, paths, permissions, or unsupported facts.
4. Every section body must be supported by the supplied trusted claims. The source_outline is only a structural hint; it is not evidence. claim_ids may only reference supplied provider claim refs. The pipeline maps those short refs back to trusted claim identities.
   Use a claim_id only when that claim supports a fact actually stated in that
   section; not every source claim must be repeated in the reader body because
   the complete Claim/Evidence ledger is preserved separately.
5. Keep commands, numbers, versions, identifiers, tables, code, images, bilingual text, limits, and conditions faithful to the source.
6. Do not return final_body, claims, or coverage_mapping. Those are deterministic pipeline fields.
7. Choose claim_ids conservatively. A claim_id must support a fact actually
   stated in that same section body; never attach the whole Claim/Evidence
   ledger to a section as a completeness checklist. If a claim is not stated,
   leave its claim_id out.
8. Before adding a claim_id, check the body against that exact claim. If the
   claim contains a URL, path, command, identifier, number, version, table
   value, or other exact token, copy that material into the body or leave the
   claim_id out. Do not cite a claim merely because it is related to the
   section. For ordinary prose, the safest valid form is to copy the complete
   claim sentence into the section body and cite it; a short paraphrase is
   valid only when it preserves the claim's facts, qualifiers, and protected
   tokens. Cite only claims whose facts are actually present; never cite a
   claim just because it is nearby or because it completes a section.
9. Do not invent a required section, fill it with a placeholder, or claim that
   the source says something it does not say. If the supplied source cannot
   support a required section, the safe result is for the page to be rejected
   by the deterministic gate; never manufacture an answer to make the JSON
   complete.
   If the trusted typed page contract marks `procedure_or_rule.exceptions` as
   `source_not_documented`, return that required section with an empty body and
   an empty claim_ids list. The deterministic pipeline records the auditable
   section state; do not write a sentence such as "no exceptions".
10. The `sources` section is for traceable source-identifying content, not a
    summary of every revision-history row. Do not cite neighboring table rows,
    Markdown separator lines, URLs, or links unless the exact material is
    present in that section body. A compact paraphrase must cite only the
    specific claims it actually preserves; never use claim_ids as a source
    checklist. Prefer a plain source title or heading claim. If no such claim
    exists, do not invent a source description.
11. `source_kind` is a deterministic handling hint, not evidence. For `table`,
    `bilingual`, `image`, `code`, and `version` claims, preserve the exact
    protected values, paired text, link, path, command, or version when citing
    them; otherwise leave the claim_id out. A shortened version/date sentence
    must not cite neighboring revision-table rows.
12. Keep section bodies concise and reader-facing. Do not copy the complete
    source, Claim ledger, or long evidence blocks into every section; the
    deterministic Evidence output preserves the full source content.
13. A supplied claim marked `structured_claim_rule=copy_verbatim_or_omit` has
    only two valid uses: copy that claim's complete text into the same section
    body and cite it, or omit both the claim_id and the fact. Never paraphrase
    a marked claim and then cite it. This rule is especially important for
    tables, URLs, paths, images, code, bilingual pairs, and revision rows. When
    in doubt, omit the structured claim and the related fact; omission is safer
    than a paraphrase with a misleading citation. In particular, do not cite
    revision-table, image, URL, or Markdown-format claims merely because they
    appear in the `sources` or `relationships` input.
14. For each required section, choose only the smallest set of claims needed to
   state the section. The robust output pattern is one or two concise sentences
   copied from supported ordinary-prose claims, followed by only those claim
   refs. Never attach every supplied claim to a section.
15. Keep ordinary-prose sections concise: do not copy more than 3 consecutive
   source sentences or 240 characters into one reader section. Select the
   shortest sufficient claims and leave the rest in Evidence. This limit does
   not apply to a single table, code block, bilingual pair, public template, or
   other explicitly structured source fragment when it is copied verbatim.
"""


_TYPED_SECTION_GUIDANCE: dict[str, dict[str, str]] = {
    "product_overview": {
        "positioning": "what the product is and the reader-level conclusion",
        "use_cases": "who uses it or which supported scenarios it serves",
        "capability_boundaries": "supported capabilities and explicit limits or exclusions",
        "entry": "how to enter, access, subscribe to, or start using it",
        "version": "an explicitly stated version, release label, or date version",
        "sources": "source-identifying facts that help the reader trace this page",
    },
    "module_or_capability": {
        "purpose": "what this module or capability is for",
        "capabilities": "what it can do, including supported behavior",
        "entry_prerequisites": "required access, setup, permissions, or prerequisites",
        "relationships": "explicit relationships to products, modules, APIs, or other components",
        "limitations": "explicit limits, exclusions, or trade-offs",
        "version": "an explicitly stated version, release label, or date version",
        "sources": "source-identifying facts that help the reader trace this page",
    },
    "procedure_or_rule": {
        "prerequisites": "what must be true or ready before the procedure",
        "steps_rules": "the documented steps, order, commands, or operating rules",
        "exceptions": "explicit failure handling, alternate branches, or edge cases",
        "limitations": "explicit limits, exclusions, or trade-offs of the procedure",
        "version": "an explicitly stated version, release label, or date version",
        "sources": "source-identifying facts that help the reader trace this page",
    },
}


def _typed_section_guidance(contract: Mapping[str, Any]) -> str:
    """Render source-derived section meanings without changing the contract."""
    page_type = str(contract.get("page_type") or "")
    guidance = _TYPED_SECTION_GUIDANCE.get(page_type, {})
    section_ids = [
        *[str(value) for value in contract.get("required_sections", [])],
        *[str(value) for value in contract.get("optional_sections", [])],
    ]
    rows = [
        f"- {section_id}: {guidance[section_id]}"
        for section_id in section_ids
        if section_id in guidance
    ]
    if not rows:
        return ""
    return "SECTION MEANINGS (use only as labels; source evidence remains authoritative):\n" + "\n".join(rows)


def _typed_source_section_rule(contract: Mapping[str, Any]) -> str:
    """Give the required source section an explicit, source-only recipe."""
    sections = {
        str(value)
        for value in [
            *contract.get("required_sections", []),
            *contract.get("optional_sections", []),
        ]
    }
    if "sources" not in sections:
        return ""
    return (
        "SOURCE SECTION RULE:\n"
        "The required `sources` section must not be empty and must cite at least one supplied claim. "
        "Use one source-identifying claim only: copy that claim's complete text into `sources` and cite its provider claim ref. "
        "A heading/source-title claim, a linked title, or a revision/version claim may be used only when its complete supplied text is copied verbatim. "
        "Do not summarize a revision table, cite an image/URL/Markdown delimiter without copying it, or invent a source description."
    )


def validate_publication_provider_identity(*, model: str, base_url: str) -> None:
    """Reject providers outside the user-approved Task2 publication seam."""
    if model != PUBLICATION_LLM_MODEL or base_url.rstrip("/") != PUBLICATION_LLM_BASE_URL:
        raise ValidationError("llm", model or base_url, "Task2 publication allows only qwen3.6 at the approved endpoint")


def publication_prompt_sections(context: dict[str, Any]) -> str:
    """Return the four fixed prompt sections for semantic publication."""
    # Publication metadata is a bounded semantic hint, not a second copy of
    # the complete evidence ledger.  The deterministic pipeline still keeps
    # every claim and attaches full trusted references after validation.  A
    # small excerpt prevents qwen's reasoning budget from being consumed by a
    # huge repeated claim list on long source pages.
    source_claims = context.get("publication_claims") or context.get("claims", [])
    evidence = [
        {
            "claim_fingerprint": claim.get("claim_fingerprint"),
            "text": str(claim.get("text", ""))[:280],
            "source_uri": claim.get("source_uri"),
            "fragment_locator": claim.get("fragment_locator"),
        }
        for claim in list(source_claims)[:8]
    ]
    taxonomy = context.get("allowed_taxonomy", [])
    return "\n\n".join(
        (
            "ROLE:\nYou provide semantic publication suggestions only. Do not create facts, paths, permissions, or taxonomy entries.",
            "EVIDENCE:\n" + json.dumps(evidence, ensure_ascii=False, separators=(",", ":")),
            "ALLOWED TAXONOMY:\n" + json.dumps(taxonomy, ensure_ascii=False, separators=(",", ":")),
            "OUTPUT SCHEMA:\n" + _PUBLICATION_OUTPUT_SCHEMA + "\nReturn only final JSON content; never include reasoning_content or <think> text.",
        )
    )



def typed_publication_prompt_sections(context: dict[str, Any]) -> str:
    """Describe optional publication metadata without changing the body role."""
    return "\n\n".join(
        (
            "OPTIONAL NESTED PUBLICATION METADATA:\n"
            "Keep the typed body response as the top-level contract. If you return "
            "publication metadata, put it under the top-level `publication` key; "
            "never return publication metadata as the only result. Use this shape:\n"
            + _PUBLICATION_OUTPUT_SCHEMA,
            "ALLOWED TAXONOMY:\n"
            + json.dumps(context.get("allowed_taxonomy", []), ensure_ascii=False, separators=(",", ":")),
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
    max_tokens: int = DEFAULT_MAX_TOKENS,
    json_mode: bool = False,
) -> str:
    """POST one completion request and return the raw assistant text."""
    if api_format not in SUPPORTED_FORMATS:
        raise ValidationError("llm", api_format, f"format must be one of {', '.join(SUPPORTED_FORMATS)}")
    for env_name, value in (("KD_LLM_API_KEY", api_key), ("KD_LLM_BASE_URL", base_url), ("KD_LLM_MODEL", model)):
        if not value:
            raise ValidationError("llm", env_name, f"{env_name} is required")

    if max_tokens <= 0:
        raise ValidationError("llm", "max_tokens", "must be greater than zero")
    body = _request_payload(
        api_format,
        model,
        prompt,
        max_tokens=max_tokens,
        json_mode=json_mode,
    )
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
    if (
        urllib.request.urlopen is _ORIGINAL_URLOPEN
        and hasattr(os, "fork")
    ):
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
    typed_contract = context.get("typed_section_contract")
    if isinstance(typed_contract, Mapping):
        # Typed compilation must use one current source context.  The legacy
        # initial_body/source_text pair is usually identical, and
        # existing_target_body can contain stale Reader wording; neither is
        # part of the trusted typed PageDraft input. Claims carry the complete
        # source evidence; only structural source hints are sent separately so
        # a long page is not duplicated in the provider prompt.
        source_text = context.get("source_text") or context.get("initial_body", "")
        source_kinds: dict[tuple[str, str], str] = {}
        page_draft = context.get("page_draft")
        if isinstance(page_draft, Mapping):
            source_fragments = page_draft.get("source_fragments", [])
            if isinstance(source_fragments, list):
                for fragment in source_fragments:
                    if not isinstance(fragment, Mapping):
                        continue
                    content_type = str(fragment.get("content_type", "")).strip()
                    raw_id = str(fragment.get("raw_id", "")).strip()
                    locator = str(fragment.get("fragment_locator", "")).strip()
                    if content_type and raw_id and locator:
                        source_kinds[(raw_id, locator)] = content_type
        typed_claims = []
        for index, claim in enumerate(claims, start=1):
            # Long fingerprints are trusted identities, not a good model-facing
            # handle.  Give the provider a short deterministic reference while
            # retaining only the fingerprint needed by optional publication
            # metadata. URI/locator/raw_id are deterministic local lineage and
            # do not help the model write the body; repeating them consumes
            # context and increases the chance of truncated or malformed JSON.
            typed_claim = {
                "provider_claim_ref": f"c{index:03d}",
                "claim_fingerprint": claim.get("claim_fingerprint"),
                "text": claim.get("text"),
            }
            source_kind = source_kinds.get(
                (
                    str(claim.get("raw_id", "")).strip(),
                    str(claim.get("fragment_locator", "")).strip(),
                )
            )
            if source_kind:
                # This is an instruction hint only. The source claim text and
                # deterministic gate remain the authority for evidence.
                typed_claim["source_kind"] = source_kind
                if source_kind in _STRUCTURED_SOURCE_KINDS:
                    # Make the existing copy-verbatim-or-omit contract
                    # machine-visible per claim without adding evidence.
                    typed_claim["structured_claim_rule"] = "copy_verbatim_or_omit"
            typed_claims.append(typed_claim)
        payload = {
            "target_page": target_page,
            "source_outline": _typed_source_outline(str(source_text), claims),
            "claims": typed_claims,
        }
    else:
        payload = {
            "target_page": target_page,
            "initial_body": context.get("initial_body", ""),
            "source_text": context.get("source_text", ""),
            "existing_target_body": context.get("old_target_body", ""),
            "claims": claims,
        }
    if isinstance(typed_contract, Mapping):
        payload["typed_page_contract"] = {
            "page_type": typed_contract.get("page_type"),
            "required_sections": list(typed_contract.get("required_sections", [])),
            "optional_sections": list(typed_contract.get("optional_sections", [])),
            "section_audits": {
                str(section_id): {
                    "status": str(audit.get("status")),
                    "audit_version": str(audit.get("audit_version")),
                }
                for section_id, audit in (typed_contract.get("section_audits") or {}).items()
                if isinstance(audit, Mapping)
            },
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
                {"target_page": target_page},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            )
    if isinstance(typed_contract, Mapping) and not context.get("publication_only"):
        publication = typed_publication_prompt_sections(context) if context.get("publication_enabled") else ""
        section_guidance = _typed_section_guidance(typed_contract)
        source_section_rule = _typed_source_section_rule(typed_contract)
        repair_feedback = str(context.get("typed_repair_feedback") or "").strip()
        repair_instruction = (
            "\n\nDETERMINISTIC REPAIR FEEDBACK:\n"
            + repair_feedback
            + "\nReturn the complete typed JSON again. For every listed claim/body failure, either copy the complete supplied claim text into the same section or remove both its claim_id and the related fact. Do not preserve an unsupported paraphrase."
            if repair_feedback
            else ""
        )
        summary_requirement = (
            "\n\nIf summary is returned, use the validated shape "
            "{\"status\":\"validated\",\"segments\":[{\"summary_id\":\"summary-1\",\"text\":\"...\",\"supports\":[{\"claim_fingerprint\":\"...\"}]}]} "
            "and reference every supplied claim fingerprint."
            if context.get("summary_enabled")
            else ""
        )
        publication_requirement = (
            "\n\nThe top-level publication object is optional for the body gate. "
            "If returned, it must use only the supplied claim fingerprints and allowed taxonomy."
            if publication
            else ""
        )
        return (
            f"{_TYPED_BODY_RULES}\n"
            f"{section_guidance}\n"
            f"{source_section_rule}\n"
            f"{publication}\n"
            f"{publication_requirement}{summary_requirement}{repair_instruction}\n\n"
            "INPUT:\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )
    summary_enabled = bool(context.get("summary_enabled", False))
    payload["summary_enabled"] = summary_enabled
    rules = _SUMMARY_PROMPT_RULES if summary_enabled else _PROMPT_RULES
    if isinstance(typed_contract, Mapping):
        rules += (
            "\n\nTASK 2-B TYPED BODY CONTRACT:\n"
            "Return the supplied page_type unchanged and add a top-level `sections` object. "
            "The section keys must be exactly the supplied required_sections plus any optional "
            "section supported by source evidence; each value must "
            "be {\"body\":\"...\",\"claim_ids\":[\"claim_fingerprint\"]}. "
            "Do not add sections, page types, source fields, or claims. Every claim_id must "
            "refer to a supplied claim fingerprint, and every section fact must be supported "
            "by the supplied source text."
        )
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


def _typed_section_failure(page_draft: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "status": "degraded",
        "reader_eligible": False,
        "page_type": page_draft.get("page_type"),
        "sections": {},
        "reason": reason,
        "audit_record": {"destination": "Audit", "reason": reason},
    }


def _decode_typed_section_payload(payload: Any) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(payload, Mapping):
        return dict(payload), None
    if not isinstance(payload, str) or not payload.strip():
        return None, "provider result is empty"
    stripped = payload.strip()
    fence = chr(96) * 3
    if stripped.startswith(fence):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.rstrip().endswith(fence):
            stripped = stripped.rstrip()[:-len(fence)]
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as error:
        return None, f"provider output parse failed ({error})"
    if not isinstance(parsed, dict):
        return None, "provider output must be an object"
    return parsed, None


def validate_section_response(
    page_draft: Mapping[str, Any],
    payload: Any,
) -> dict[str, Any]:
    """Validate provider output against the trusted page/section contract."""
    parsed, parse_reason = _decode_typed_section_payload(payload)
    if parse_reason:
        return _typed_section_failure(page_draft, parse_reason)
    assert parsed is not None
    unknown_top_level = sorted(set(parsed) - {"page_type", "sections", "publication", "summary"})
    if unknown_top_level:
        return _typed_section_failure(
            page_draft,
            "provider top-level fields are not allowed: " + ", ".join(unknown_top_level),
        )
    page_type = parsed.get("page_type")
    expected_page_type = page_draft.get("page_type")
    if page_type != expected_page_type or page_type not in PAGE_TYPE_SECTION_MATRIX:
        return _typed_section_failure(page_draft, f"provider page type is invalid: {page_type}")
    sections = parsed.get("sections")
    if not isinstance(sections, Mapping):
        return _typed_section_failure(page_draft, "provider sections object is missing")
    required = tuple(page_draft.get("required_sections") or PAGE_TYPE_SECTION_MATRIX[page_type])
    optional = tuple(page_draft.get("optional_sections") or PAGE_TYPE_OPTIONAL_SECTIONS.get(page_type, ()))
    allowed_sections = set(required) | set(optional)
    unknown_sections = sorted(set(sections) - allowed_sections)
    if unknown_sections:
        return _typed_section_failure(page_draft, f"unknown section: {', '.join(unknown_sections)}")
    trusted_claim_ids = {
        str(claim.get("claim_id") or claim.get("claim_fingerprint"))
        for claim in page_draft.get("claims", [])
        if isinstance(claim, Mapping) and (claim.get("claim_id") or claim.get("claim_fingerprint"))
    }
    if not trusted_claim_ids:
        trusted_claim_ids = {str(value) for value in page_draft.get("claim_ids", []) if str(value).strip()}
    trusted_claims_by_id = {
        str(claim.get("claim_id") or claim.get("claim_fingerprint")): claim
        for claim in page_draft.get("claims", [])
        if isinstance(claim, Mapping)
        and (claim.get("claim_id") or claim.get("claim_fingerprint"))
    }
    provider_claim_ref_to_id = {
        str(claim.get("provider_claim_ref") or f"c{index:03d}"): claim_id
        for index, claim in enumerate(page_draft.get("claims", []), start=1)
        if isinstance(claim, Mapping)
        for claim_id in [str(claim.get("claim_id") or claim.get("claim_fingerprint") or "").strip()]
        if claim_id
    }
    missing_sections = sorted(set(required) - set(sections))
    if missing_sections:
        for section_id, raw in sections.items():
            if isinstance(raw, Mapping):
                unknown_fields = sorted(set(raw) - {"body", "claim_ids"})
                if unknown_fields:
                    return _typed_section_failure(
                        page_draft,
                        "provider source/claim fields are not allowed: " + ", ".join(unknown_fields),
                    )
        return _typed_section_failure(page_draft, f"required section missing: {', '.join(missing_sections)}")
    normalized: dict[str, dict[str, Any]] = {}
    section_ids = [*required, *[section_id for section_id in optional if section_id in sections]]
    for section_id in section_ids:
        raw = sections[section_id]
        source_audit = _source_not_documented_audit(page_draft, str(section_id))
        claim_ids: list[str] = []
        if isinstance(raw, str):
            body = raw.strip()
        elif isinstance(raw, Mapping):
            unknown_fields = sorted(set(raw) - {"body", "claim_ids"})
            if unknown_fields:
                return _typed_section_failure(
                    page_draft,
                    "provider source/claim fields are not allowed: " + ", ".join(unknown_fields),
                )
            body = str(raw.get("body", "")).strip()
            raw_claim_ids = raw.get("claim_ids", [])
            if not isinstance(raw_claim_ids, list) or not all(isinstance(value, str) and value.strip() for value in raw_claim_ids):
                return _typed_section_failure(page_draft, f"section {section_id} claim mapping is invalid")
            claim_ids = [
                provider_claim_ref_to_id.get(value.strip(), value.strip())
                for value in raw_claim_ids
            ]
            if trusted_claim_ids:
                unknown_claims = sorted(set(claim_ids) - trusted_claim_ids)
                if unknown_claims:
                    return _typed_section_failure(
                        page_draft,
                        "provider claim ids are not supplied by the trusted input: " + ", ".join(unknown_claims),
                    )
            # A Markdown delimiter is structure, not a reader-facing fact.
            # Keep it in the complete source/evidence ledger, but do not make
            # the provider reproduce a formatting-only line as a semantic
            # claim just because it was extracted as a Claim.
            claim_ids = [
                claim_id
                for claim_id in claim_ids
                if not _is_format_only_claim(trusted_claims_by_id.get(claim_id, {}))
            ]
        else:
            return _typed_section_failure(page_draft, f"section {section_id} is not an object or string")
        if source_audit is not None:
            if body or claim_ids:
                return _typed_section_failure(
                    page_draft,
                    f"section {section_id} must stay empty when source is not documented",
                )
            normalized[section_id] = {
                "section_id": section_id,
                "body": "",
                "claim_ids": [],
                "status": "source_not_documented",
                "source_audit": dict(source_audit),
            }
            trusted_section = page_draft.get("sections", {}).get(section_id) if isinstance(page_draft.get("sections"), Mapping) else None
            if isinstance(trusted_section, Mapping) and isinstance(trusted_section.get("dependency_record"), Mapping):
                normalized[section_id]["dependency_record"] = dict(trusted_section["dependency_record"])
            continue
        if not body:
            return _typed_section_failure(page_draft, f"section {section_id} is empty")
        if not claim_ids:
            return _typed_section_failure(
                page_draft,
                f"section {section_id} claim mapping is missing",
            )
        normalized[section_id] = {
            "section_id": section_id,
            "body": body,
            "claim_ids": claim_ids,
            "status": "candidate",
        }
        trusted_section = page_draft.get("sections", {}).get(section_id) if isinstance(page_draft.get("sections"), Mapping) else None
        if isinstance(trusted_section, Mapping) and isinstance(trusted_section.get("dependency_record"), Mapping):
            normalized[section_id]["dependency_record"] = dict(trusted_section["dependency_record"])
    normalized_response = {
        "status": "draft",
        "reader_eligible": False,
        "page_type": page_type,
        "sections": normalized,
        "reason": None,
        "audit_record": None,
        "_validated_typed_response": True,
    }
    if isinstance(page_draft.get("section_audits"), Mapping):
        normalized_response["section_audits"] = {
            str(section_id): dict(audit)
            for section_id, audit in page_draft["section_audits"].items()
            if isinstance(audit, Mapping)
        }
    if "publication" in parsed:
        if not isinstance(parsed["publication"], Mapping):
            return _typed_section_failure(page_draft, "provider publication metadata is not an object")
        normalized_response["publication"] = dict(parsed["publication"])
    if "summary" in parsed:
        if not isinstance(parsed["summary"], Mapping):
            return _typed_section_failure(page_draft, "provider summary is not an object")
        normalized_response["summary"] = dict(parsed["summary"])
    return normalized_response


def typed_claim_support_failures(
    page_draft: Mapping[str, Any],
    typed_response: Mapping[str, Any],
) -> list[str]:
    """Return cited typed claims whose facts are absent from the body.

    This is a provider-repair diagnostic only.  The Publication Gate remains
    the release authority; the helper lets a live provider receive a bounded
    correction request before its response is finally marked degraded.
    """
    if typed_response.get("status") != "draft":
        return [str(typed_response.get("reason") or "typed response is not a draft")]
    claims_by_id = {
        str(claim.get("claim_id") or claim.get("claim_fingerprint")): claim
        for claim in page_draft.get("claims", [])
        if isinstance(claim, Mapping)
        and (claim.get("claim_id") or claim.get("claim_fingerprint"))
    }
    sections = typed_response.get("sections")
    if not isinstance(sections, Mapping):
        return ["provider sections object is missing"]
    full_body = "\n".join(
        str(section.get("body", ""))
        for section in sections.values()
        if isinstance(section, Mapping)
    )
    failures: list[str] = []
    for section_id, section in sections.items():
        if not isinstance(section, Mapping):
            continue
        for raw_claim_id in section.get("claim_ids", []):
            claim_id = str(raw_claim_id).strip()
            claim = claims_by_id.get(claim_id)
            if claim is None or _is_format_only_claim(claim):
                continue
            if not _claim_is_supported_by_body(str(claim.get("text", "")), full_body):
                failures.append(f"{section_id}:{claim_id}")
    return failures


def typed_source_block_failures(
    page_draft: Mapping[str, Any],
    typed_response: Mapping[str, Any],
) -> list[str]:
    """Return typed sections that copy too many ordinary source sentences.

    The final Publication Gate checks the rendered page.  This helper applies
    the same deterministic rule to each typed section so a live provider can
    repair a section before the candidate is rejected.  Checking sections
    independently is important: separate reader sections must not become one
    artificial source run merely because their evidence is stored together.
    """
    if typed_response.get("status") != "draft":
        return []
    claims_by_id = {
        str(claim.get("claim_id") or claim.get("claim_fingerprint")): claim
        for claim in page_draft.get("claims", [])
        if isinstance(claim, Mapping)
        and (claim.get("claim_id") or claim.get("claim_fingerprint"))
    }
    fragments = [
        fragment
        for fragment in page_draft.get("source_fragments", [])
        if isinstance(fragment, Mapping)
    ]
    failures: list[str] = []
    sections = typed_response.get("sections")
    if not isinstance(sections, Mapping):
        return failures
    for section_id, raw_section in sections.items():
        if not isinstance(raw_section, Mapping):
            continue
        claim_ids = [str(value).strip() for value in raw_section.get("claim_ids", [])]
        section_claims = [claims_by_id[claim_id] for claim_id in claim_ids if claim_id in claims_by_id]
        evidence_body = "\n".join(
            str(claim.get("text", ""))
            for claim in section_claims
            if str(claim.get("text", "")).strip()
        )
        if not evidence_body:
            continue
        section_fragments = [
            fragment
            for claim in section_claims
            for fragment in fragments
            if fragment.get("raw_id") == claim.get("raw_id")
            and str(fragment.get("fragment_locator") or "")
            == str(claim.get("fragment_locator") or "")
        ]
        check = _continuous_source_block_check(
            str(raw_section.get("body", "")),
            evidence_body,
            {"source_fragments": section_fragments},
        )
        if check.get("failed_samples"):
            failures.append(str(section_id))
    return failures


def repair_typed_source_blocks(
    page_draft: Mapping[str, Any],
    typed_response: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Safely shorten verbatim typed sections without touching the evidence ledger.

    This is a last deterministic compiler repair, not a relaxed gate: it only
    runs when a section body contains complete supplied claim text. It keeps
    the longest safe prefix of those claims, removes the omitted claim refs
    from the Reader section, and leaves every omitted claim in the trusted
    source/evidence records. Paraphrased or ambiguous output remains degraded.
    """
    if typed_response.get("status") != "draft":
        return None
    claims_by_id = {
        str(claim.get("claim_id") or claim.get("claim_fingerprint")): claim
        for claim in page_draft.get("claims", [])
        if isinstance(claim, Mapping)
        and (claim.get("claim_id") or claim.get("claim_fingerprint"))
    }
    fragments = [
        fragment
        for fragment in page_draft.get("source_fragments", [])
        if isinstance(fragment, Mapping)
    ]
    sections = typed_response.get("sections")
    if not isinstance(sections, Mapping):
        return None
    repaired_sections = {str(section_id): dict(section) for section_id, section in sections.items() if isinstance(section, Mapping)}
    repaired_ids: list[str] = []
    changed = False
    for section_id, section in repaired_sections.items():
        claim_ids = [str(value).strip() for value in section.get("claim_ids", []) if str(value).strip()]
        section_claims = [claims_by_id[claim_id] for claim_id in claim_ids if claim_id in claims_by_id]
        if not section_claims:
            continue
        current_body = normalize_for_gate(str(section.get("body", "")))
        if not current_body:
            continue
        # Do not replace a genuine paraphrase with source text. This fallback
        # is only for the unambiguous Evidence-dump shape.
        if any(
            normalize_for_gate(str(claim.get("text", ""))) not in current_body
            for claim in section_claims
            if str(claim.get("text", "")).strip()
        ):
            continue
        safe_prefix: list[Mapping[str, Any]] = []
        for claim in section_claims:
            candidate = [*safe_prefix, claim]
            candidate_body = "\n".join(str(item.get("text", "")) for item in candidate)
            candidate_fragments = [
                fragment
                for item in candidate
                for fragment in fragments
                if fragment.get("raw_id") == item.get("raw_id")
                and str(fragment.get("fragment_locator") or "")
                == str(item.get("fragment_locator") or "")
            ]
            check = _continuous_source_block_check(
                candidate_body,
                candidate_body,
                {"source_fragments": candidate_fragments},
            )
            if check.get("failed_samples"):
                break
            safe_prefix = candidate
        if len(safe_prefix) == len(section_claims):
            continue
        if not safe_prefix:
            continue
        section["body"] = "\n".join(str(item.get("text", "")) for item in safe_prefix)
        section["claim_ids"] = [
            str(item.get("claim_id") or item.get("claim_fingerprint"))
            for item in safe_prefix
        ]
        repaired_ids.append(section_id)
        changed = True
    if not changed:
        return None
    repaired = dict(typed_response)
    repaired["sections"] = repaired_sections
    repaired["_deterministic_source_block_repair"] = repaired_ids
    return repaired


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
        # The approved qwen endpoint enables thinking by default.  Its
        # OpenAI-compatible bridge accepts the documented soft switch in the
        # user prompt; without it, reasoning consumes the response budget and
        # frequently truncates the required JSON contract.  The client still
        # reads only message.content, never reasoning_content.
        if model == PUBLICATION_LLM_MODEL and api_format == OPENAI_FORMAT:
            prompt = "/no_think\n" + prompt
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
                            max_tokens=(
                                PUBLICATION_MAX_TOKENS
                                if context.get("publication_only")
                                else DEFAULT_MAX_TOKENS
                            ),
                        ),
                        require_final_body=not bool(
                            context.get("publication_only") or context.get("typed_section_contract")
                        ),
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
    *,
    api_format: str | None = None,
    env: dict[str, str] | None = None,
    provider_config_path: Any | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a provider generator from user config, then env fallback."""
    source = effective_llm_environment(provider_config_path=provider_config_path, env=env)
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
