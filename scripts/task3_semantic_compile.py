"""Compile bounded semantic candidates for the Task 3 raw Reader route.

One provider request handles a small fixed batch. There are no automatic
replays: a failed batch is recorded and the Reader compiler can keep the
corresponding sources as explicit fidelity-only pages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from knowledge_digest.llm import OPENAI_FORMAT, call_llm
from knowledge_digest.provider_config import configured_provider_config_path, effective_llm_environment
from knowledge_digest.reader_compiler import SUPPORTED_SUFFIXES, _normalize_label, _product_label, _slug


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_sources(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith(".") or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        records.append({
            "relative_path": relative,
            "source_uri": f"raw://confluence/{relative}",
            "content_fingerprint": _sha256(text),
            "title": _normalize_label(next((line[2:].strip() for line in text.splitlines() if line.startswith("# ") and line[2:].strip()), Path(relative).stem.replace("_", " "))),
            "text": text,
        })
    return records


def _prompt(batch: list[dict[str, Any]], max_chars: int) -> str:
    payload = [
        {
            "source_uri": item["source_uri"],
            "title": item["title"],
            "text": item["text"][:max_chars],
            "truncated_input": len(item["text"]) > max_chars,
        }
        for item in batch
    ]
    return """/no_think
You are the semantic editor for an internal product knowledge base. Return ONLY one JSON object.

Schema:
{"items":[{"source_uri":"...","title":"...","summary":"...","module":"...","knowledge_type":"...","body":"..."}]}

Rules:
- Return exactly one item for every supplied source_uri, in the same order.
- Use only facts present in that source. Never invent product boundaries, permissions, dates, limits, causes, or procedures.
- The summary is 1-3 plain-language sentences. The body is a compact Markdown knowledge page with headings such as Summary, Key facts, How to use, Boundaries, or Troubleshooting when supported.
- Keep commands, URLs, identifiers, names, numbers, dates, versions, conditions, tables, and code materially intact. Do not turn a conditional into a certainty.
- Do not copy internal hashes, source IDs, provider fields, or audit metadata into the body.
- Choose one short reusable module name. Do not use the source filename as the module name. Use one of: device-management, app-management, identity-and-access, messaging-and-email, merchant-and-payment, logs-and-audit, policy-and-configuration, data-and-analytics, or a concise product module name when the source clearly requires it.
- Choose one knowledge_type from: product-positioning, module-manual, technical-implementation, experience-and-pitfalls, standards-and-assets.
- If the input is truncated, summarize only supported visible content and say in the body that the source excerpt was truncated.

SOURCES:
""" + json.dumps(payload, ensure_ascii=False)


def _parse(text: str) -> list[dict[str, Any]]:
    value = json.loads(text)
    items = value.get("items") if isinstance(value, Mapping) else None
    if not isinstance(items, list) or any(not isinstance(item, Mapping) for item in items):
        raise ValueError("provider JSON must contain items[]")
    return [dict(item) for item in items]


def _write_candidate(root: Path, source: Mapping[str, Any], item: Mapping[str, Any]) -> str:
    relative = str(source["relative_path"])
    parts = Path(relative).parts
    product, _label = _product_label(parts[0]) if len(parts) > 1 else ("unclassified", "Unclassified")
    module_value = _normalize_label(str(item.get("module") or "general"))
    module = _slug(module_value, "general")
    title = _normalize_label(str(item.get("title") or source["title"]))
    slug = _slug(title, "knowledge")
    target = root / "bundle" / "products" / product / "modules" / module / f"{slug}.md"
    suffix = 2
    while target.exists():
        target = root / "bundle" / "products" / product / "modules" / module / f"{slug}-{suffix}.md"
        suffix += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    summary = str(item.get("summary") or "").strip()
    body = str(item.get("body") or "").strip()
    if not body:
        raise ValueError("provider item body is empty")
    yaml_lines = [
        "---",
        f"description: {json.dumps(summary[:280], ensure_ascii=False)}",
        "sources:",
        f"- resource: {source['source_uri']}",
        f"  digest_content_fingerprint: {source['content_fingerprint']}",
        "status: draft",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        "type: KnowledgeDigest Knowledge",
        "---",
        "",
        f"# {title}",
        "",
        body,
        "",
    ]
    target.write_text("\n".join(yaml_lines), encoding="utf-8")
    return target.relative_to(root / "bundle").as_posix()


def compile_semantic_candidates(
    input_root: Path,
    output_root: Path,
    *,
    api_key: str,
    base_url: str,
    model: str,
    batch_size: int = 4,
    max_chars_per_source: int = 9000,
    timeout: int = 60,
) -> dict[str, Any]:
    if not api_key:
        raise ValueError("KD_LLM_API_KEY is required")
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError("semantic output must be new and empty")
    output_root.mkdir(parents=True, exist_ok=True)
    records = _read_sources(input_root.resolve())
    (output_root / "bundle").mkdir()
    successes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    truncated: list[dict[str, Any]] = []
    for source in records:
        input_chars = len(source["text"])
        if input_chars > max_chars_per_source:
            truncated.append({
                "source_uri": source["source_uri"],
                "relative_path": source["relative_path"],
                "status": "semantic_truncated_fallback",
                "reason": "input_exceeds_max_chars_per_source",
                "input_chars": input_chars,
                "max_chars_per_source": max_chars_per_source,
            })
        else:
            eligible.append(source)
    failures.extend(truncated)
    if truncated:
        print(
            f"semantic preflight: {len(truncated)} sources exceed {max_chars_per_source} chars; "
            "kept as full-source fallback, no provider call",
            file=sys.stderr,
            flush=True,
        )
    batches = [eligible[i:i + batch_size] for i in range(0, len(eligible), batch_size)]
    for index, batch in enumerate(batches, start=1):
        try:
            response = call_llm(
                _prompt(batch, max_chars_per_source),
                api_format=OPENAI_FORMAT,
                base_url=base_url,
                api_key=api_key,
                model=model,
                timeout=timeout,
                max_tokens=6000,
                json_mode=True,
            )
            items = _parse(response)
            by_uri = {str(item.get("source_uri")): item for item in items}
            if set(by_uri) != {str(source["source_uri"]) for source in batch}:
                raise ValueError("provider did not return exactly the requested source URIs")
            for source in batch:
                item = by_uri[source["source_uri"]]
                path = _write_candidate(output_root, source, item)
                successes.append({"source_uri": source["source_uri"], "relative_path": source["relative_path"], "reader_candidate_path": path, "status": "semantic_candidate"})
            print(f"semantic batch {index}/{len(batches)} completed: {len(batch)} sources", flush=True)
        except Exception as error:
            reason = f"{type(error).__name__}: {error}"
            for source in batch:
                failures.append({"source_uri": source["source_uri"], "relative_path": source["relative_path"], "status": "semantic_failed", "reason": reason})
            print(f"semantic batch {index}/{len(batches)} failed: {reason}", file=sys.stderr, flush=True)
    audit = output_root / "audit"
    reports = output_root / "reports"
    audit.mkdir()
    reports.mkdir()
    manifest = {
        "schema_version": "task3-semantic-candidate.v1",
        "source_count": len(records),
        "semantic_candidate_count": len(successes),
        "failure_count": len(failures),
        "max_chars_per_source": max_chars_per_source,
        "truncated_count": len(truncated),
        "entries": successes,
        "failures": failures,
    }
    (audit / "semantic-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "schema_version": "task3-semantic-compile.v1",
        "status": "passed" if not failures else "degraded",
        "source_count": len(records),
        "semantic_candidate_count": len(successes),
        "failure_count": len(failures),
        "max_chars_per_source": max_chars_per_source,
        "truncated_count": len(truncated),
        "batch_size": batch_size,
        "batch_count": len(batches),
        "replays": 0,
        "model": model,
        "base_url": base_url,
        "failures": failures,
    }
    (reports / "semantic-compile.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-chars-per-source", type=int, default=9000)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--provider-config", type=Path, default=None)
    args = parser.parse_args()
    provider_env = effective_llm_environment(
        provider_config_path=args.provider_config or configured_provider_config_path()
    )
    report = compile_semantic_candidates(
        args.input,
        args.output,
        api_key=provider_env.get("KD_LLM_API_KEY", ""),
        base_url=provider_env.get("KD_LLM_BASE_URL", "https://dashscope.in.whatspos.cn/v1"),
        model=provider_env.get("KD_LLM_MODEL", "qwen3.6"),
        batch_size=args.batch_size,
        max_chars_per_source=args.max_chars_per_source,
        timeout=args.timeout,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["semantic_candidate_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
