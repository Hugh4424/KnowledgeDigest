#!/usr/bin/env python3
"""Reproducible Task10 baseline/final metrics.

The command intentionally measures two trees with the same implementation:
the frozen Git baseline and either the current worktree or another Git tree.
It reports facts even when the final slimming predicates are not satisfied;
measurement is not a deletion or release gate by itself.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import subprocess
import tarfile
import sys
import tokenize
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping


BASELINE_COMMIT = "eee55492517bc86e3aad4838fe215bb23d84e8a4"
SCHEMA_VERSION = "task10-metrics.v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
RETAINED_ACCEPTANCE_TESTS = (
    "tests/acceptance/test_task5_publication_contract.py",
    "tests/acceptance/test_task7_pages.py",
    "tests/acceptance/test_task7_claims.py",
    "tests/acceptance/test_task7_e2e.py",
    "tests/acceptance/test_task7_audit.py",
    "tests/acceptance/test_task7_split.py",
    "tests/acceptance/test_task8_entry_navigation.py",
    "tests/acceptance/test_task9_accept.py",
    "tests/acceptance/test_task9_publish.py",
)
ACCEPTANCE_IDS = tuple(f"AC-K4-{index:03d}" for index in range(1, 9))


def fail(message: str) -> "NoReturn":
    print(json.dumps({"schema_version": SCHEMA_VERSION, "status": "failed", "error": message}, ensure_ascii=False))
    raise SystemExit(2)


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git exited {completed.returncode}"
        raise RuntimeError(detail)
    return completed.stdout


def physical_lines(text: str) -> int:
    return len(text.splitlines())


def code_lines(text: str) -> int:
    """Count physical lines containing at least one non-comment token."""

    lines: set[int] = set()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        ignored = {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT}
        for token in tokens:
            if token.type not in ignored:
                lines.add(token.start[0])
    except (IndentationError, tokenize.TokenError):
        # The file is still a physical source fact. Parse errors are reported
        # separately and must not silently turn code lines into zero.
        return sum(1 for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#"))
    return len(lines)


@dataclass(frozen=True)
class TreeReader:
    label: str
    paths: tuple[str, ...]
    root: Path | None = None
    ref: str | None = None
    contents: Mapping[str, bytes] | None = field(default=None, repr=False)

    @classmethod
    def for_worktree(cls) -> "TreeReader":
        paths: list[str] = []
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(REPO_ROOT)
            if any(part in {".git", ".venv", "__pycache__"} for part in relative.parts):
                continue
            paths.append(relative.as_posix())
        return cls("worktree", tuple(sorted(paths)), REPO_ROOT, None)

    @classmethod
    def for_git(cls, ref: str) -> "TreeReader":
        resolved = git("rev-parse", "--verify", f"{ref}^{{commit}}").strip()
        archive = subprocess.run(
            ["git", "archive", "--format=tar", resolved],
            cwd=REPO_ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if archive.returncode != 0:
            raise RuntimeError(archive.stderr.decode(errors="replace").strip() or "git archive failed")
        contents: dict[str, bytes] = {}
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
            for member in bundle:
                if not member.isfile():
                    continue
                handle = bundle.extractfile(member)
                if handle is not None:
                    contents[member.name] = handle.read()
        return cls(resolved, tuple(sorted(contents)), None, resolved, contents)

    def has(self, path: str) -> bool:
        return path in self.paths

    def read_bytes(self, path: str) -> bytes:
        if self.contents is not None:
            return self.contents[path]
        if self.root is not None:
            return (self.root / Path(path)).read_bytes()
        assert self.ref is not None
        completed = subprocess.run(
            ["git", "show", f"{self.ref}:{path}"],
            cwd=REPO_ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"cannot read {path} from {self.ref}: {completed.stderr.decode(errors='replace').strip()}")
        return completed.stdout

    def read_text(self, path: str) -> str:
        return self.read_bytes(path).decode("utf-8", errors="replace")


def source_modules(tree: TreeReader) -> dict[str, str]:
    modules: dict[str, str] = {}
    for path in tree.paths:
        if not path.startswith("src/") or not path.endswith(".py"):
            continue
        relative = PurePosixPath(path).relative_to("src")
        parts = list(relative.parts)
        if parts[-1] == "__init__.py":
            parts.pop()
        else:
            parts[-1] = parts[-1][:-3]
        if parts:
            modules[".".join(parts)] = path
    return modules


def resolve_module(candidate: str, modules: Mapping[str, str]) -> str | None:
    parts = candidate.split(".")
    for length in range(len(parts), 0, -1):
        value = ".".join(parts[:length])
        if value in modules:
            return value
    return None


def imported_modules(module: str, text: str, modules: Mapping[str, str]) -> tuple[set[str], tuple[str, ...]]:
    found: set[str] = set()
    unresolved: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return set(), (f"{module}:syntax:{error.msg}",)

    current_parts = module.split(".")
    package_parts = current_parts if modules.get(module, "").endswith("/__init__.py") else current_parts[:-1]

    def add(candidate: str) -> None:
        resolved = resolve_module(candidate, modules)
        if resolved is None:
            unresolved.append(candidate)
        else:
            found.add(resolved)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package_parts[: max(0, len(package_parts) - node.level + 1)]
                prefix = ".".join(base)
                if node.module:
                    candidate = f"{prefix}.{node.module}" if prefix else node.module
                    add(candidate)
                else:
                    for alias in node.names:
                        candidate = f"{prefix}.{alias.name}" if prefix else alias.name
                        add(candidate)
            elif node.module:
                add(node.module)
                # ``from knowledge_digest import semantic_compiler`` is a
                # package-level import whose real consumer is the child module.
                for alias in node.names:
                    add(f"{node.module}.{alias.name}")
    return found, tuple(sorted(set(unresolved)))


def project_script_roots(tree: TreeReader) -> tuple[str, ...]:
    data = tomllib.loads(tree.read_text("pyproject.toml"))
    scripts = data.get("project", {}).get("scripts", {})
    roots: list[str] = []
    for value in scripts.values():
        if not isinstance(value, str) or ":" not in value:
            continue
        roots.append(value.split(":", 1)[0])
    return tuple(roots)


def reachability(tree: TreeReader, modules: Mapping[str, str]) -> dict[str, object]:
    roots = project_script_roots(tree)
    reachable: set[str] = set()
    unresolved: set[str] = set()
    queue = list(roots)
    missing_roots: list[str] = []
    while queue:
        module = queue.pop()
        if module in reachable:
            continue
        if module not in modules:
            missing_roots.append(module)
            continue
        reachable.add(module)
        # The package initializer is part of the import closure whenever one
        # of its child modules is a formal root or reachable dependency.
        parts = module.split(".")
        for length in range(1, len(parts)):
            parent = ".".join(parts[:length])
            if parent in modules:
                reachable.add(parent)
        dependencies, missing = imported_modules(module, tree.read_text(modules[module]), modules)
        unresolved.update(missing)
        queue.extend(sorted(dependencies - reachable))
    unreachable = sorted(set(modules) - reachable)
    return {
        "roots": list(roots),
        "root_count": len(roots),
        "module_count": len(modules),
        "reachable_count": len(reachable),
        "unreachable_count": len(unreachable),
        "reachable_modules": sorted(reachable),
        "unreachable_modules": unreachable,
        "missing_roots": sorted(set(missing_roots)),
        "unresolved_imports": sorted(unresolved),
    }


def source_metrics(tree: TreeReader, modules: Mapping[str, str]) -> dict[str, object]:
    physical = 0
    sloc = 0
    functions = 0
    parse_errors: list[str] = []
    for module, path in sorted(modules.items()):
        text = tree.read_text(path)
        physical += physical_lines(text)
        sloc += code_lines(text)
        try:
            parsed = ast.parse(text)
        except SyntaxError as error:
            parse_errors.append(f"{path}:{error.msg}")
            continue
        functions += sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(parsed))
    return {
        "module_count": len(modules),
        "physical_lines": physical,
        "code_lines": sloc,
        "function_count": functions,
        "parse_errors": parse_errors,
    }


def test_metrics(tree: TreeReader) -> dict[str, int]:
    files = [path for path in tree.paths if path.startswith("tests/") and path.endswith(".py")]
    test_functions = 0
    test_classes = 0
    parse_errors = 0
    for path in files:
        try:
            parsed = ast.parse(tree.read_text(path))
        except SyntaxError:
            parse_errors += 1
            continue
        for node in ast.walk(parsed):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                test_functions += 1
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                test_classes += 1
    return {"test_files": len(files), "test_functions": test_functions, "test_classes": test_classes, "parse_errors": parse_errors}


def reference_paths(tree: TreeReader) -> tuple[str, ...]:
    allowed: list[str] = []
    for path in tree.paths:
        if path.startswith(("src/", "scripts/", "tests/", "docs/", "config/")):
            allowed.append(path)
        elif path.startswith("apply/"):
            allowed.append(path)
        elif path.startswith("specs/"):
            allowed.append(path)
        elif "/" not in path and path == "pyproject.toml":
            allowed.append(path)
        elif "/" not in path and path.endswith(".md"):
            allowed.append(path)
    return tuple(sorted(allowed))


def config_metrics(tree: TreeReader) -> dict[str, object]:
    config_files = sorted(path for path in tree.paths if path.startswith("config/") and path.endswith(".json"))
    all_bytes = sum(len(tree.read_bytes(path)) for path in config_files)
    scope = reference_paths(tree)
    rows: list[dict[str, object]] = []
    for config in config_files:
        basename = PurePosixPath(config).name
        needles = (basename, config)
        refs: list[str] = []
        for candidate in scope:
            if candidate == config:
                continue
            text = tree.read_text(candidate)
            if any(needle in text for needle in needles):
                refs.append(candidate)
        size = len(tree.read_bytes(config))
        rows.append({"path": config, "bytes": size, "references": sorted(set(refs))})
    zero = [row for row in rows if not row["references"]]
    return {
        "file_count": len(config_files),
        "bytes": all_bytes,
        "reference_scope": ["src/", "scripts/", "tests/", "docs/", "pyproject.toml", "top-level *.md", "config/"],
        "zero_reference_count": len(zero),
        "zero_reference_bytes": sum(int(row["bytes"]) for row in zero),
        "zero_reference_files": [row["path"] for row in zero],
        "files": rows,
    }


def measure(tree: TreeReader) -> dict[str, object]:
    modules = source_modules(tree)
    return {
        "tree": tree.label,
        "source": source_metrics(tree, modules),
        "reachability": reachability(tree, modules),
        "config": config_metrics(tree),
        "tests": test_metrics(tree),
    }


def comparison(baseline: Mapping[str, object], target: Mapping[str, object]) -> dict[str, object]:
    base_source = baseline["source"]
    target_source = target["source"]
    base_reach = baseline["reachability"]
    target_reach = target["reachability"]
    base_config = baseline["config"]
    target_config = target["config"]
    physical_delta = int(target_source["physical_lines"]) - int(base_source["physical_lines"])
    code_delta = int(target_source["code_lines"]) - int(base_source["code_lines"])
    unreachable_delta = int(target_reach["unreachable_count"]) - int(base_reach["unreachable_count"])
    zero_bytes_delta = int(target_config["zero_reference_bytes"]) - int(base_config["zero_reference_bytes"])
    return {
        "physical_lines_delta": physical_delta,
        "code_lines_delta": code_delta,
        "unreachable_modules_delta": unreachable_delta,
        "zero_reference_config_bytes_delta": zero_bytes_delta,
        "physical_lines_decreased": physical_delta < 0,
        "code_lines_decreased": code_delta < 0,
        "unreachable_modules_zero": int(target_reach["unreachable_count"]) == 0,
        "zero_reference_config_bytes_decreased": zero_bytes_delta < 0,
        "final_predicates_satisfied": physical_delta < 0 and code_delta < 0 and int(target_reach["unreachable_count"]) == 0 and zero_bytes_delta < 0,
    }


def _run_acceptance_command(args: list[str]) -> dict[str, object]:
    """Run one bounded acceptance command without leaking child output."""

    try:
        completed = subprocess.run(
            args,
            cwd=REPO_ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=110,
        )
    except subprocess.TimeoutExpired:
        return {"exit_code": 124, "timed_out": True}
    except OSError:
        return {"exit_code": 127, "timed_out": False}
    return {
        "exit_code": completed.returncode,
        "timed_out": False,
        "stdout_has_test_result": "passed" in completed.stdout,
    }


def _read_task_evidence(name: str) -> dict[str, object] | None:
    path = REPO_ROOT / "quality" / "evidence" / "k4" / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _acceptance_entries(
    baseline: Mapping[str, object],
    target: Mapping[str, object],
    result: Mapping[str, object],
) -> list[dict[str, object]]:
    """Produce criterion-level facts only from executed checks and receipts."""

    base_config = baseline["config"]
    target_config = target["config"]
    metrics_comparison = result["comparison"]
    full_regression = _run_acceptance_command([
        "uv", "run", "--frozen", "pytest", *RETAINED_ACCEPTANCE_TESTS,
    ])
    checkpoint = _run_acceptance_command([
        "uv", "run", "--frozen", "pytest",
        "tests/acceptance/test_task7_e2e.py",
        "tests/acceptance/test_task7_audit.py",
        "-k", "checkpoint_resume",
    ])
    guard_commands = (
        ["uv", "run", "--frozen", "pytest", "tests/acceptance/test_task7_audit.py", "-k", "b1_retirement_guard"],
        ["uv", "run", "--frozen", "pytest", "tests/acceptance/test_task5_publication_contract.py", "-k", "legacy_retirement"],
        ["uv", "run", "--frozen", "pytest", "tests/acceptance/test_task7_audit.py", "-k", "b3_legacy_entry_retirement"],
        ["uv", "run", "--frozen", "pytest", "tests/acceptance/test_task7_audit.py", "-k", "b4_config_guard"],
    )
    guards = [_run_acceptance_command(command) for command in guard_commands]

    real_digest = _read_task_evidence("real-digest.json")
    final_aggregate = _read_task_evidence("final-aggregate.json")
    final_run = _read_task_evidence("build-code-final-run.json")
    coupled = _read_task_evidence("coupled-test-dispositions.json")

    metric_ok = bool(metrics_comparison["final_predicates_satisfied"])
    config_ok = (
        int(base_config["zero_reference_count"]) == 21
        and int(base_config["zero_reference_bytes"]) == 3_341_698
        and int(target_config["file_count"]) == 55
        and int(metrics_comparison["zero_reference_config_bytes_delta"]) == -3_341_698
    )
    regression_ok = full_regression["exit_code"] == 0 and full_regression["stdout_has_test_result"]
    digest_ok = (
        isinstance(real_digest, dict)
        and real_digest.get("result", {}).get("run_status") == "complete"
        and real_digest.get("result", {}).get("publish_status") == "not_released"
    )
    checkpoint_ok = checkpoint["exit_code"] == 0 and checkpoint["stdout_has_test_result"]
    guards_ok = all(item["exit_code"] == 0 and item["stdout_has_test_result"] for item in guards)
    handoff_ok = (
        isinstance(final_aggregate, dict)
        and isinstance(final_run, dict)
        and isinstance(coupled, dict)
        and final_aggregate.get("status") == "incomplete"
        and final_run.get("official_run", {}).get("stage_end") == "published"
        and final_run.get("delivery", {}).get("release") == "not_released"
        and coupled.get("row_count") == 42
    )
    fail_loud_ok = (
        isinstance(final_run, dict)
        and final_run.get("status") == "incomplete"
        and final_run.get("official_run", {}).get("quality_status") == "incomplete"
        and bool(final_run.get("quality_gaps"))
        and final_run.get("delivery", {}).get("release") == "not_released"
    )
    values = {
        "AC-K4-001": metric_ok,
        "AC-K4-002": config_ok,
        "AC-K4-003": regression_ok and digest_ok,
        "AC-K4-004": checkpoint_ok,
        "AC-K4-005": guards_ok,
        "AC-K4-006": handoff_ok,
        "AC-K4-007": regression_ok,
        "AC-K4-008": fail_loud_ok,
    }
    return [
        {
            "acceptance_criterion_id": criterion_id,
            "assertions": [
                {
                    "id": "current_acceptance_checks",
                    "expected": True,
                    "actual": values[criterion_id],
                },
            ],
        }
        for criterion_id in ACCEPTANCE_IDS
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="Git commit/ref used as the frozen baseline")
    parser.add_argument("--tree", default="worktree", help="worktree or a Git commit/ref to measure")
    parser.add_argument(
        "--workflowhub-acceptance",
        action="store_true",
        help="also run the bounded per-AC acceptance producer contract",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        baseline_ref = git("rev-parse", "--verify", f"{args.baseline}^{{commit}}").strip()
        baseline = measure(TreeReader.for_git(baseline_ref))
        target_tree = TreeReader.for_worktree() if args.tree == "worktree" else TreeReader.for_git(args.tree)
        target = measure(target_tree)
        output = {
            "schema_version": SCHEMA_VERSION,
            "status": "completed",
            "repository": str(REPO_ROOT),
            "baseline": {"requested": args.baseline, "resolved": baseline_ref, "metrics": baseline},
            "tree": {"requested": args.tree, "metrics": target},
            "comparison": comparison(baseline, target),
        }
        if args.workflowhub_acceptance:
            output["entries"] = _acceptance_entries(baseline, target, output)
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, SyntaxError, TypeError, ValueError, tomllib.TOMLDecodeError) as error:
        fail(str(error))
    return 2


if __name__ == "__main__":
    main()
