#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowledge_digest.companybrain_mapping import build_mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic read-only CompanyBrain case mapping")
    parser.add_argument("--companybrain", type=Path, required=True)
    parser.add_argument("--case-matrix", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--raw", type=Path, help="Optional raw source root used only for content-based matching")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    matrix = json.loads(args.case_matrix.read_text(encoding="utf-8"))
    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8")) if args.source_manifest else None
    source_texts = {}
    if args.raw and source_manifest:
        for entry in source_manifest.get("entries", []):
            if not isinstance(entry, dict) or entry.get("status") != "valid" or not entry.get("source_id") or not entry.get("source_uri"):
                continue
            source_path = args.raw / str(entry["source_uri"])
            if source_path.is_file():
                source_texts[str(entry["source_id"])] = source_path.read_text(encoding="utf-8", errors="replace")
    result = build_mapping(args.companybrain, list(matrix.get("cases", [])), source_manifest, source_texts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": result["case_count"], "counts": result["counts"], "companybrain_tree_hash": result["companybrain_manifest"]["tree_hash"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
