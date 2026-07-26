"""LLM refinement generator over OpenAI- and Anthropic-compatible HTTP APIs.

Standard library only: no runtime third-party dependency is introduced. Every
failure raises ``ValidationError`` immediately -- no retry, no silent downgrade
to the identity generator, because a silent downgrade makes "did refinement
actually happen" unobservable.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable

from .errors import ValidationError


OPENAI_FORMAT = "openai"
ANTHROPIC_FORMAT = "anthropic"
SUPPORTED_FORMATS = (OPENAI_FORMAT, ANTHROPIC_FORMAT)
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MAX_TOKENS = 8192

_PROMPT_RULES = """You refine knowledge-base notes. Return ONLY one JSON object.

Schema:
{"final_body": "<the refined markdown page>",
 "claims": [{"claim_fingerprint": "...", "text": "...", "source_uri": "...", "fragment_locator": "..."}],
 "coverage_mapping": [{"raw_id": "...", "source_uri": "...", "input_fragment": "...", "output_page": "...", "fragment_locator": "...", "claim_fingerprint": "..."}]}

Loss-prevention rules (violating any one makes the output rejected):
1. Never drop a claim. Every claim given below must appear in "claims" with its
   claim_fingerprint, source_uri and fragment_locator copied verbatim.
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


def _endpoint(base_url: str, api_format: str) -> str:
    root = base_url.rstrip("/")
    if api_format == OPENAI_FORMAT:
        return f"{root}/chat/completions"
    return f"{root}/v1/messages"


def _request_payload(api_format: str, model: str, prompt: str) -> dict[str, Any]:
    messages = [{"role": "user", "content": prompt}]
    if api_format == OPENAI_FORMAT:
        return {"model": model, "messages": messages}
    return {"model": model, "max_tokens": DEFAULT_MAX_TOKENS, "messages": messages}


def _extract_text(api_format: str, payload: Any) -> str:
    try:
        if api_format == OPENAI_FORMAT:
            return str(payload["choices"][0]["message"]["content"])
        return str(payload["content"][0]["text"])
    except (KeyError, IndexError, TypeError) as error:
        raise ValidationError("llm", api_format, f"unexpected response shape ({error})") from error


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
    try:
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
    return f"{_PROMPT_RULES}\n\nINPUT:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


def parse_response(text: str) -> dict[str, Any]:
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
    if not isinstance(parsed, dict) or "final_body" not in parsed:
        raise ValidationError("llm", "response", "provider output must be an object with final_body")
    return parsed


def build_generator(
    *,
    api_format: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a ``generator(context)`` callable backed by a live provider."""

    def generator(context: dict[str, Any]) -> dict[str, Any]:
        prompt = build_prompt(context, target_page=str(context.get("target_page", "")))
        return parse_response(
            call_llm(
                prompt,
                api_format=api_format,
                base_url=base_url,
                api_key=api_key,
                model=model,
                timeout=timeout,
            )
        )

    return generator


def generator_from_env(
    *, api_format: str | None = None, env: dict[str, str] | None = None
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a provider generator from ``KD_LLM_*`` environment variables."""
    source = dict(os.environ if env is None else env)
    return build_generator(
        api_format=api_format or source.get("KD_LLM_FORMAT") or OPENAI_FORMAT,
        base_url=source.get("KD_LLM_BASE_URL", ""),
        api_key=source.get("KD_LLM_API_KEY", ""),
        model=source.get("KD_LLM_MODEL", ""),
    )
