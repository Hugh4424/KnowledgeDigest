"""Small real-provider probe for the Task10 Reader contract.

This is intentionally separate from the full 89-page run so a provider
transport or response-contract failure is diagnosed without spending the full
Reader budget.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from knowledge_digest.reader_projection import (
    READER_MODEL_ID,
    READER_PROMPT_VERSION,
    READER_TOPIC_MAP_VERSION,
    _call_provider,
    _load_batch,
    _normalise_draft,
    _normalise_provider_result,
    _prompt,
    compile_reader_candidate,
)
from knowledge_digest.semantic_cache import ModelCache
from knowledge_digest.semantic_compiler import configured_provider_from_env


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--compile":
        batch = Path(sys.argv[2])
        cache = Path(sys.argv[3])
        input_root = Path(sys.argv[4])
        provider = configured_provider_from_env()
        result = compile_reader_candidate(
            batch,
            provider=provider,
            cache_root=cache,
            input_root=input_root,
            force=True,
        )
        print(json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True))
        return 0 if result.status == "candidate" else 2
    if len(sys.argv) > 1 and sys.argv[1] == "--repair-cache":
        batch = Path(sys.argv[2])
        cache_root = Path(sys.argv[3])
        input_root = Path(sys.argv[4])
        provider = configured_provider_from_env()
        _manifest, pages, _snapshot = _load_batch(batch, input_root=input_root)
        cache = ModelCache(cache_root)
        repaired = 0
        hits = 0
        for page in pages:
            topic = f"reader:{page.original_path}"
            members = [item.cache_member(topic, index) for index, item in enumerate(page.evidence)]
            try:
                cached = cache.get_or_call(
                    model_id=READER_MODEL_ID,
                    prompt_version=READER_PROMPT_VERSION,
                    topic_map_version=READER_TOPIC_MAP_VERSION,
                    topic_key=topic,
                    members=members,
                    provider=lambda: (_ for _ in ()).throw(RuntimeError("repair preflight must not call provider")),
                    allow_provider=False,
                )
                _normalise_draft(cached.result, page, page.evidence)
                hits += 1
                continue
            except Exception:
                pass
            repair_topic = f"{topic}:repair-v2"
            repair_members = [item.cache_member(repair_topic, index) for index, item in enumerate(page.evidence)]
            cache.get_or_call(
                model_id=READER_MODEL_ID,
                prompt_version=f"{READER_PROMPT_VERSION}-repair-v2",
                topic_map_version=READER_TOPIC_MAP_VERSION,
                topic_key=repair_topic,
                members=repair_members,
                provider=lambda page=page: _normalise_provider_result(_call_provider(provider, _prompt(page, page.evidence, "\n请确保至少引用一个有效 evidence_id。")), page, page.evidence),
                allow_provider=True,
            )
            repaired += 1
        print(json.dumps({"status": "ok", "base_cache_hits": hits, "repaired": repaired}, ensure_ascii=False))
        return 0
    provider = configured_provider_from_env()
    if provider is None:
        print(json.dumps({"status": "blocked", "reason": "provider_missing"}, ensure_ascii=False))
        return 2
    prompt = (
        "只返回 JSON 对象，不要 Markdown 代码围栏。"
        "JSON 必须包含 title、question、page_type、module、object、scenario、boundary、summary、sections、evidence。"
        "page_type 使用 operation；sections 使用前置条件、操作步骤、预期结果、验证方式、失败与限制。"
        "evidence 的每个数组只返回 [\"e1\"]。证据 e1：进入设备列表并点击激活。"
    )
    if len(sys.argv) > 1 and sys.argv[1] in {"--full", "--page"}:
        batch = Path(sys.argv[2])
        _manifest, pages, _snapshot = _load_batch(batch)
        page = pages[0]
        if sys.argv[1] == "--page":
            target = sys.argv[3]
            page = next(item for item in pages if item.original_path == target)
        prompt = _prompt(page, page.evidence)
    try:
        result = provider.complete_reader(prompt)
    except Exception as error:  # probe output must remain secret-free
        print(json.dumps({"status": "failed", "error_type": type(error).__name__, "error": str(error)[:240]}, ensure_ascii=False))
        return 1
    output = {"status": "ok", "keys": sorted(result), "provider_tokens": result.get("provider_tokens")}
    if len(sys.argv) > 1 and sys.argv[1] in {"--full", "--page"}:
        raw_evidence = result.get("evidence") if isinstance(result, dict) else None
        if isinstance(raw_evidence, dict):
            output["evidence_refs"] = {str(key): [str(item) for item in value] for key, value in raw_evidence.items() if isinstance(value, list)}
        try:
            _normalise_draft(result, page, page.evidence)
            output["contract"] = "passed"
        except Exception as error:
            output["contract"] = "failed"
            output["contract_error"] = f"{type(error).__name__}: {error}"
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
