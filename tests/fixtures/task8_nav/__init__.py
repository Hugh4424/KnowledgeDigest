"""Small, deterministic Task8 batch fixtures built from the Task7 contract."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any


PAGE_FRONTMATTER_FIELDS = (
    "title",
    "type",
    "page_model",
    "scope",
    "product",
    "section",
    "module",
    "tier",
    "trust",
    "source_status",
    "quality_status",
    "created",
    "updated",
    "generated_by",
    "tags",
    "source",
)


def _yaml_value(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_value(item) for item in value) + "]"
    return str(value).lower() if isinstance(value, bool) else str(value)


def _page_text(
    *,
    title: str,
    product: str,
    section: str,
    source_path: str,
    created: str,
    updated: str,
    body: str,
) -> str:
    values: dict[str, Any] = {
        "title": title,
        "type": "reference",
        "page_model": "derived",
        "scope": "company",
        "product": product,
        "section": section,
        "module": section,
        "tier": 2,
        "trust": "medium",
        "source_status": "compiled",
        "quality_status": "formal",
        "created": created,
        "updated": updated,
        "generated_by": "knowledge_digest_semantic_compiler.py",
        "tags": ["company", product, section],
        "source": f"fixture/{source_path}",
    }
    frontmatter = "\n".join(
        ["---", *(f"{field}: {_yaml_value(values[field])}" for field in PAGE_FRONTMATTER_FIELDS), "---"]
    )
    return f"{frontmatter}\n\n# {title}\n\n{body}\n"


def _source_hash(source_path: str) -> str:
    return sha256(source_path.encode("utf-8")).hexdigest()


def make_batch(root: Path) -> Path:
    """Write a three-page Task7-shaped batch and return its directory."""

    batch = root / "batch"
    page_specs = (
        {
            "topic_key": "GoInsight:login",
            "page_path": "products/GoInsight/authentication/login.md",
            "title": "登录认证",
            "product": "GoInsight",
            "section": "authentication",
            "source_path": "goinsight/login.md",
            "created": "2026-01-01",
            "updated": "2026-01-02",
            "body": "登录页说明认证入口和会话要求。",
        },
        {
            "topic_key": "GoInsight:invoice",
            "page_path": "products/GoInsight/billing/invoice.md",
            "title": "发票配置",
            "product": "GoInsight",
            "section": "billing",
            "source_path": "goinsight/invoice.md",
            "created": "2026-01-03",
            "updated": "2026-01-04",
            "body": "发票页说明账单配置入口和字段。",
        },
        {
            "topic_key": "emm-android:device-login",
            "page_path": "products/emm-android/authentication/device-login.md",
            "title": "设备登录",
            "product": "emm-android",
            "section": "authentication",
            "source_path": "emm-android/device-login.md",
            "created": "2026-01-05",
            "updated": "2026-01-06",
            "body": "设备登录页说明终端认证步骤。",
        },
    )

    for spec in page_specs:
        page = batch / spec["page_path"]
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(_page_text(**{key: spec[key] for key in ("title", "product", "section", "source_path", "created", "updated", "body")}), encoding="utf-8")

    pages: list[dict[str, Any]] = []
    source_to_pages: dict[str, list[str]] = {}
    source_ledger: list[dict[str, Any]] = []
    for index, spec in enumerate(page_specs, start=1):
        source_path = str(spec["source_path"])
        page_path = str(spec["page_path"])
        pages.append(
            {
                "topic_key": spec["topic_key"],
                "page_path": page_path,
                "page_paths": [page_path],
                "source_paths": [source_path],
                "block_count": 1,
                "claim_count": 1,
                "block_ids": [f"block-{index}"],
                "claim_ids": [f"claim-{index}"],
            }
        )
        source_to_pages[source_path] = [page_path]
        source_ledger.append(
            {
                "source_path": source_path,
                "content_hash": _source_hash(source_path),
                "source_status": "ready",
                "pages": [page_path],
            }
        )

    audit = batch / "_audit"
    audit.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "task7-page-manifest.v1",
        "publish_status": "not_released",
        "run_status": "complete",
        "attempt_id": "fixture-attempt",
        "source_snapshot": {
            "input_manifest_id": "task8-fixture-manifest",
            "expected_count": len(page_specs),
            "entries": [
                {
                    "source_path": spec["source_path"],
                    "source_uri": spec["source_path"],
                    "source_id": f"fixture-source-{index}",
                    "content_hash": _source_hash(str(spec["source_path"])),
                    "byte_count": 1,
                }
                for index, spec in enumerate(page_specs, start=1)
            ],
        },
        "blockers": [],
        "pages": pages,
        "source_to_pages": source_to_pages,
        "source_ledger": source_ledger,
    }
    (audit / "page-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (audit / "reference-blocks.jsonl").write_text("", encoding="utf-8")
    (audit / "sources.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in source_ledger), encoding="utf-8"
    )
    (audit / "run-metrics.json").write_text("{}\n", encoding="utf-8")
    (audit / "suspected-synonyms.md").write_text("# Suspected synonyms\n", encoding="utf-8")
    (batch / "README.md").write_text("# Task8 fixture batch\n", encoding="utf-8")
    return batch


__all__ = ["PAGE_FRONTMATTER_FIELDS", "make_batch"]
