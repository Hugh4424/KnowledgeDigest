#!/usr/bin/env python3
"""Promote one authenticated WorkflowHub implementation review into Task5 M401-R."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowledge_digest.m401_r_adapter import promote_m401_r


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--m401-attempt", type=Path, required=True)
    parser.add_argument("--review-result", type=Path, required=True)
    parser.add_argument("--review-attempt", type=Path, required=True)
    parser.add_argument("--review-report", type=Path, required=True)
    parser.add_argument("--finding-dispositions", type=Path, required=True)
    parser.add_argument("--task-id", default="task5-reader-quality-compiler-redesign")
    parser.add_argument("--project-name", default="KnowledgeDigest")
    parser.add_argument("--worktree", type=Path)
    parser.add_argument(
        "--resume-existing-attempt",
        action="store_true",
        help="revalidate an already-written M401-R attempt after an interrupted promotion",
    )
    parser.add_argument(
        "--replace-existing-promotion",
        action="store_true",
        help="replace stale fixed promotion views; requires --resume-existing-attempt",
    )
    args = parser.parse_args(argv)
    try:
        result = promote_m401_r(
            task_root=args.task_root,
            m401_attempt=args.m401_attempt,
            review_result=args.review_result,
            review_attempt=args.review_attempt,
            review_report=args.review_report,
            finding_dispositions=args.finding_dispositions,
            task_id=args.task_id,
            project_name=args.project_name,
            worktree=args.worktree,
            resume_existing_attempt=args.resume_existing_attempt,
            replace_existing_promotion=args.replace_existing_promotion,
        )
    except Exception as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "passed", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
