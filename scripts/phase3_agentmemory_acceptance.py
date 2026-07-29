#!/usr/bin/env python3
"""Run the isolated Phase 3 company-kb + agentmemory acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SELECTED_RELATIVE = (
    Path("merchant system/apple接口调用方式.md"),
    Path("emm for android /EMM售前确认.md"),
    Path("GoInsight/数据分析.md"),
)
RUN_PREFIX = "kd-phase3-agentmemory-run."
PROJECT = "knowledge-digest-phase3-company-kb"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_manifest(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    if not root.is_dir():
        raise RuntimeError(f"expected directory: {root}")
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def copy_corpus(source_dir: Path, run_root: Path) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise RuntimeError(f"source directory is missing: {source_dir}")

    new_dir = run_root / "new-input" / "items"
    company_kb = run_root / "company-kb"
    new_dir.mkdir(parents=True)
    (company_kb / "pages").mkdir(parents=True)
    (company_kb / "_archive").mkdir()
    (company_kb / "_queues").mkdir()
    (company_kb / "_digest").mkdir()
    (company_kb / "kb.structure.md").write_text(
        "---\n"
        "roots: [pages, _archive, _queues]\n"
        "why_field: why\n"
        "version_field: version\n"
        "---\n\n"
        "# Isolated company-kb\n\n"
        "This disposable copy is the Phase 3 acceptance target.\n",
        encoding="utf-8",
    )

    all_files = sorted(
        path.relative_to(source_dir)
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".md"
    )
    missing = [relative for relative in SELECTED_RELATIVE if relative not in all_files]
    if missing:
        raise RuntimeError("fixed source selection is missing: " + ", ".join(map(str, missing)))

    selected_set = set(SELECTED_RELATIVE)
    sources: list[dict[str, Any]] = []
    selected_hashes: dict[str, str] = {}
    for relative in all_files:
        source = source_dir / relative
        selected = relative in selected_set
        destination = new_dir / relative if selected else company_kb / "pages" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        digest = sha256_file(source)
        record = {
            "relative_path": str(relative),
            "content_path": f"items/{relative.as_posix()}" if selected else relative.as_posix(),
            "source_uri": f"confluence://company/{relative.as_posix()}",
            "sha256": digest,
            "selected_new_input": selected,
        }
        sources.append(record)
        if selected:
            selected_hashes[str(relative)] = digest

    sources_jsonl = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in sources)
    (run_root / "sources.jsonl").write_text(sources_jsonl, encoding="utf-8")
    (run_root / "new-input" / "sources.jsonl").write_text(sources_jsonl, encoding="utf-8")
    (run_root / "selected-files.sha256").write_text(
        "".join(f"{digest}  {relative}\n" for relative, digest in sorted(selected_hashes.items())),
        encoding="utf-8",
    )
    (run_root / "kb.structure.md").write_text(
        (company_kb / "kb.structure.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return {
        "source_dir": str(source_dir),
        "source_markdown_count": len(all_files),
        "selected_relative_paths": [str(path) for path in SELECTED_RELATIVE],
        "selected_count": len(SELECTED_RELATIVE),
        "selected_hashes": selected_hashes,
        "new_dir": str(run_root / "new-input"),
        "company_kb": str(company_kb),
        "sources_jsonl": str(run_root / "sources.jsonl"),
        "structure_path": str(company_kb / "kb.structure.md"),
    }


def free_port_block() -> dict[str, int]:
    for _ in range(20):
        sockets: list[socket.socket] = []
        try:
            # agentmemory derives engine as REST + 46023, so the base must
            # stay below 19513 while remaining outside the documented defaults.
            base = 10000 + secrets.randbelow(9000)
            ports = {
                "rest": base,
                "stream": base + 1,
                "viewer": base + 2,
                "engine": base + 46023,
            }
            for port in ports.values():
                sock = socket.socket()
                sock.bind(("127.0.0.1", port))
                sockets.append(sock)
            return ports
        except OSError:
            pass
        finally:
            for sock in sockets:
                sock.close()
    raise RuntimeError("could not reserve an isolated agentmemory port block")


def write_agentmemory_config(instance_root: Path, ports: dict[str, int]) -> dict[str, str]:
    data_root = instance_root / "data"
    home = instance_root / "home"
    state_path = data_root / "state_store.db"
    stream_path = data_root / "stream_store"
    config_path = instance_root / "iii-config.yaml"
    for path in (data_root, home, stream_path):
        path.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "workers:\n"
        "  - name: iii-worker-manager\n"
        "    config:\n"
        "      host: 127.0.0.1\n"
        f"      port: {ports['engine']}\n"
        "  - name: iii-http\n"
        "    config:\n"
        f"      port: {ports['rest']}\n"
        "      host: 127.0.0.1\n"
        "      default_timeout: 180000\n"
        "  - name: iii-state\n"
        "    config:\n"
        "      adapter:\n"
        "        name: kv\n"
        "        config:\n"
        "          store_method: file_based\n"
        f"          file_path: {state_path}\n"
        "  - name: iii-queue\n"
        "    config:\n"
        "      adapter:\n"
        "        name: builtin\n"
        "  - name: iii-pubsub\n"
        "    config:\n"
        "      adapter:\n"
        "        name: local\n"
        "  - name: iii-cron\n"
        "    config:\n"
        "      adapter:\n"
        "        name: kv\n"
        "  - name: iii-stream\n"
        "    config:\n"
        f"      port: {ports['stream']}\n"
        "      host: 127.0.0.1\n"
        "      adapter:\n"
        "        name: kv\n"
        "        config:\n"
        "          store_method: file_based\n"
        f"          file_path: {stream_path}\n",
        encoding="utf-8",
    )
    result = {
        "home": str(home),
        "data_root": str(data_root),
        "state_path": str(state_path),
        "stream_path": str(stream_path),
        "config_path": str(config_path),
    }
    (instance_root / "ports.json").write_text(
        json.dumps({**ports, **result}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def isolated_agentmemory_env(instance_root: Path, config: dict[str, str], ports: dict[str, int]) -> dict[str, str]:
    env = dict(os.environ)
    iii_path = shutil.which("iii")
    if not iii_path:
        existing_iii = Path.home() / ".agentmemory" / "bin" / "iii"
        if existing_iii.is_file() and os.access(existing_iii, os.X_OK):
            iii_path = str(existing_iii)
    if iii_path:
        env["PATH"] = str(Path(iii_path).parent) + os.pathsep + env.get("PATH", "")
    env.update(
        {
            "HOME": config["home"],
            "AGENTMEMORY_III_CONFIG": config["config_path"],
            "III_REST_PORT": str(ports["rest"]),
            "III_STREAM_PORT": str(ports["stream"]),
            "III_ENGINE_PORT": str(ports["engine"]),
            "AGENTMEMORY_AUTO_COMPRESS": "false",
            "AGENTMEMORY_ALLOW_AGENT_SDK": "false",
            "AGENTMEMORY_REFLECT": "false",
            "CONSOLIDATION_ENABLED": "false",
            "GRAPH_EXTRACTION_ENABLED": "false",
            "AGENTMEMORY_URL": f"http://127.0.0.1:{ports['rest']}",
        }
    )
    for key in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENROUTER_API_KEY",
        "MINIMAX_API_KEY",
        "VOYAGE_API_KEY",
        "COHERE_API_KEY",
        "EMBEDDING_PROVIDER",
    ):
        env[key] = ""
    return env


def run_and_save(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return {
        "command": command,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "exit_code": completed.returncode,
    }


def wait_for_livez(base_url: str, timeout_seconds: float = 30.0) -> None:
    from urllib.request import urlopen

    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{base_url}/agentmemory/livez", timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, dict) and payload.get("status") in {"ok", "healthy"}:
                return
            last_error = RuntimeError(f"unexpected livez response: {payload!r}")
        except Exception as error:  # startup connection refusal is expected
            last_error = error
        time.sleep(0.25)
    raise RuntimeError(f"disposable agentmemory did not become ready: {last_error}")


def stop_disposable_engine(instance_paths: dict[str, str]) -> dict[str, Any]:
    pid_path = Path(instance_paths["home"]) / ".agentmemory" / "iii.pid"
    if not pid_path.is_file():
        return {"pid": None, "stopped": True, "reason": "no engine pid file"}
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except ValueError as error:
        raise RuntimeError(f"invalid disposable engine pid file: {pid_path}") from error
    command = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    config_path = instance_paths["config_path"]
    if command and config_path not in command:
        return {"pid": pid, "stopped": False, "reason": "pid command is not the disposable config"}
    if command:
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if not subprocess.run(
                ["ps", "-p", str(pid), "-o", "pid="],
                check=False,
                capture_output=True,
                text=True,
            ).stdout.strip():
                return {"pid": pid, "stopped": True, "reason": "SIGTERM"}
            time.sleep(0.1)
        os.kill(pid, signal.SIGKILL)
    return {"pid": pid, "stopped": True, "reason": "SIGKILL" if command else "already stopped"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def source_claims(run_dir: Path) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for row in read_jsonl(run_dir / "s6" / "provenance-audit.jsonl"):
        claims.append(
            {
                "text": row["claim_body"],
                "claim_fingerprint": row["claim_fingerprint"],
                "source_uri": row["source_uri"],
                "fragment_locator": row["fragment_locator"],
                "content_fingerprint": row["content_fingerprint"],
                "source_snapshot_ref": row["source_snapshot_ref"],
                "raw_id": row.get("claim_id"),
            }
        )
    return claims


def provenance_validation_exit(memories: Iterable[dict[str, Any]], claims: list[dict[str, Any]]) -> tuple[int, int]:
    from knowledge_digest.agentmemory_store import provenance_matches

    by_identity = {}
    for memory in memories:
        from knowledge_digest.agentmemory_store import parse_provenance

        parsed = parse_provenance(memory)
        if parsed:
            identity = (
                str(parsed.get("claim_fingerprint")),
                str(parsed.get("source_uri")),
                str(parsed.get("fragment_locator")),
            )
            by_identity[identity] = memory
    missing = 0
    for claim in claims:
        identity = (
            str(claim["claim_fingerprint"]),
            str(claim["source_uri"]),
            str(claim["fragment_locator"]),
        )
        memory = by_identity.get(identity)
        if memory is None or not provenance_matches(memory, claim):
            missing += 1
    return (0 if missing == 0 else 1), missing


def memory_write_counts(writes: Iterable[Any]) -> dict[str, int]:
    counts = {"created": 0, "duplicate": 0}
    for write in writes:
        status = getattr(write, "status", "")
        if status in counts:
            counts[status] += 1
    return counts


def parse_cli_report(stdout_path: Path) -> Path:
    text = stdout_path.read_text(encoding="utf-8")
    for line in reversed(text.splitlines()):
        if "report=" in line:
            return Path(line.rsplit("report=", 1)[1].strip())
    raise RuntimeError(f"CLI output has no report path: {stdout_path}")


def assert_under(path: Path, root: Path, label: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise RuntimeError(f"{label} is outside disposable root: {path}") from error


def build_receipt(
    run_root: Path,
    source_dir: Path,
    *,
    layout: dict[str, Any],
    ports: dict[str, int],
    instance_paths: dict[str, str],
    real_manifest_before: dict[str, str],
) -> dict[str, Any]:
    from knowledge_digest.agentmemory_store import AgentMemoryStore, parse_provenance

    base_url = f"http://127.0.0.1:{ports['rest']}"
    env = isolated_agentmemory_env(run_root / "agentmemory-instance", instance_paths, ports)
    cli_base = ["uv", "run", "--frozen", "python", "-m", "knowledge_digest.cli"]
    dry_stdout = run_root / "company-kb-dry-run.stdout.txt"
    dry_stderr = run_root / "company-kb-dry-run.stderr.txt"
    formal_stdout = run_root / "company-kb-formal.stdout.txt"
    formal_stderr = run_root / "company-kb-formal.stderr.txt"
    dry = run_and_save(
        [*cli_base, layout["new_dir"], layout["company_kb"], "--no-llm", "--dry-run"],
        cwd=REPO_ROOT,
        env=env,
        stdout_path=dry_stdout,
        stderr_path=dry_stderr,
    )
    if dry["exit_code"] != 0:
        raise RuntimeError(f"isolated company-kb dry-run failed: {dry}")
    formal = run_and_save(
        [*cli_base, layout["new_dir"], layout["company_kb"], "--no-llm"],
        cwd=REPO_ROOT,
        env=env,
        stdout_path=formal_stdout,
        stderr_path=formal_stderr,
    )
    if formal["exit_code"] != 0:
        raise RuntimeError(f"isolated company-kb formal run failed: {formal}")
    dry["report"] = str(parse_cli_report(dry_stdout))
    formal["report"] = str(parse_cli_report(formal_stdout))

    formal_report = json.loads(Path(formal["report"]).read_text(encoding="utf-8"))
    writes = formal_report.get("formal_kb_changes", [])
    if not writes or any(row.get("status") != "success" for row in writes):
        raise RuntimeError("company-kb formal output is not all success")
    company_kb_page_hashes = {
        path.relative_to(Path(layout["company_kb"])).as_posix(): sha256_file(path)
        for path in Path(layout["company_kb"]).rglob("*.md")
        if path.is_file()
    }
    (run_root / "company-kb-pages.sha256").write_text(
        "".join(f"{digest}  {relative}\n" for relative, digest in sorted(company_kb_page_hashes.items())),
        encoding="utf-8",
    )
    layout["company_kb_page_hashes"] = company_kb_page_hashes
    claims = source_claims(Path(formal["report"]).parent)
    if not claims:
        raise RuntimeError("company-kb produced no provenance claims")

    store = AgentMemoryStore(base_url, project=PROJECT)
    livez = store.livez()
    first_writes = store.remember_claims(claims)
    first_counts = memory_write_counts(first_writes)
    memories_after_first = store.list_memories()
    first_memory_count = len(memories_after_first)
    if first_counts["created"] == 0 or first_memory_count != first_counts["created"]:
        raise RuntimeError("agentmemory did not create the expected isolated memories")

    search_readback: list[dict[str, Any]] = []
    selected_uris = [
        f"confluence://company/{relative.as_posix()}" for relative in SELECTED_RELATIVE
    ]
    for source_uri in selected_uris:
        results = store.smart_search(source_uri, limit=5)
        matched = [
            item["memory"]
            for item in results
            if parse_provenance(item["memory"]) and parse_provenance(item["memory"]).get("source_uri") == source_uri
        ]
        if not matched:
            raise RuntimeError(f"agentmemory smart-search could not read back {source_uri}")
        search_readback.append({"source_uri": source_uri, "matched_memory_ids": [m["id"] for m in matched]})

    replay_writes = store.remember_claims(claims)
    replay_counts = memory_write_counts(replay_writes)
    replay_memory_count = len(store.list_memories())
    if replay_counts["created"] != 0 or replay_memory_count != first_memory_count:
        raise RuntimeError("agentmemory replay created a duplicate memory")

    target = first_writes[0].memory_id
    if not target:
        raise RuntimeError("first agentmemory write has no memory id")
    before_code, before_missing = provenance_validation_exit(store.list_memories(), claims)
    store.forget(target)
    red_code, red_missing = provenance_validation_exit(store.list_memories(), claims)
    if red_code == 0 or red_missing == 0:
        raise RuntimeError("provenance reverse validation did not turn red after forget")
    restored = store.remember_claims([claims[0]])
    green_code, green_missing = provenance_validation_exit(store.list_memories(), claims)
    if green_code != 0 or green_missing != 0:
        raise RuntimeError("provenance reverse validation did not recover after REST remember")
    after_memories = store.list_memories()
    real_manifest_after = file_manifest(Path.home() / ".agentmemory")
    if real_manifest_after != real_manifest_before:
        raise RuntimeError("real agentmemory state changed during isolated acceptance")
    original_after = file_manifest(source_dir)
    original_before = layout["original_manifest"]
    if original_after != original_before:
        raise RuntimeError("original Confluence sha256 changed during acceptance")

    receipt = {
        "schema": "kd.phase3.agentmemory.acceptance.v1",
        "status": "passed",
        "run_root": str(run_root),
        "layout": layout,
        "commands": {"dry_run": dry, "formal_run": formal},
        "agentmemory": {
            "project": PROJECT,
            "base_url": base_url,
            "ports": ports,
            "paths": instance_paths,
            "livez": livez,
            "llm": "disabled",
            "embedding": "disabled",
            "first_write": {**first_counts, "memory_count": first_memory_count},
            "search_readback": search_readback,
            "replay": {**replay_counts, "memory_count_before": first_memory_count, "memory_count_after": replay_memory_count},
            "memory_count_after_restore": len(after_memories),
            "restored": memory_write_counts(restored),
        },
        "provenance_reverse": {
            "before": {"exit_code": before_code, "missing": before_missing},
            "after_forget": {"exit_code": red_code, "missing": red_missing},
            "after_restore": {"exit_code": green_code, "missing": green_missing},
            "evidence": str(run_root / "provenance-reverse.json"),
        },
        "original_confluence": {
            "sha256_unchanged": original_after == original_before,
            "before_file_count": len(original_before),
            "after_file_count": len(original_after),
        },
        "real_agentmemory": {
            "state_unchanged": real_manifest_after == real_manifest_before,
            "before_file_count": len(real_manifest_before),
            "after_file_count": len(real_manifest_after),
        },
    }
    (run_root / "provenance-reverse.json").write_text(
        json.dumps(receipt["provenance_reverse"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    run_root = Path("/tmp") / f"{RUN_PREFIX}{os.getpid()}"
    run_root.mkdir(parents=True)
    receipt_path = run_root / "receipt.json"
    process: subprocess.Popen[str] | None = None
    instance_paths: dict[str, str] | None = None
    real_manifest_before: dict[str, str] = {}
    receipt: dict[str, Any] = {
        "schema": "kd.phase3.agentmemory.acceptance.v1",
        "status": "failed",
        "run_root": str(run_root),
    }
    try:
        source_dir = args.source_dir.resolve()
        real_manifest_before = file_manifest(Path.home() / ".agentmemory")
        layout = copy_corpus(source_dir, run_root)
        layout["original_manifest"] = file_manifest(source_dir)
        ports = free_port_block()
        instance_root = run_root / "agentmemory-instance"
        instance_paths = write_agentmemory_config(instance_root, ports)
        for path in instance_paths.values():
            assert_under(Path(path), run_root, "agentmemory isolation path")
        if ports["rest"] == 3111 or ports["stream"] == 3112 or ports["engine"] == 49134:
            raise RuntimeError("disposable agentmemory reused a default port")
        env = isolated_agentmemory_env(instance_root, instance_paths, ports)
        log_path = run_root / "agentmemory.stdout-stderr.log"
        log_handle = log_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            ["agentmemory", "--port", str(ports["rest"]), "--verbose"],
            cwd=instance_root,
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        wait_for_livez(f"http://127.0.0.1:{ports['rest']}")
        receipt = build_receipt(
            run_root,
            source_dir,
            layout=layout,
            ports=ports,
            instance_paths=instance_paths,
            real_manifest_before=real_manifest_before,
        )
        receipt["agentmemory"]["process_exit_code_before_stop"] = process.poll()
        log_handle.close()
        process.terminate()
        process.wait(timeout=20)
        receipt["agentmemory"]["process_exit_code_after_stop"] = process.returncode
    except Exception as error:
        receipt["error"] = str(error)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=20)
        if "agentmemory" not in receipt:
            receipt["agentmemory"] = {"stopped": process is None or process.poll() is not None}
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=20)
        engine_stop = stop_disposable_engine(instance_paths) if instance_paths is not None else {"stopped": True}
        receipt["agentmemory"] = {
            **receipt.get("agentmemory", {}),
            "stopped": (process is None or process.poll() is not None) and engine_stop["stopped"],
            "engine_stop": engine_stop,
        }
        if not engine_stop["stopped"]:
            receipt["status"] = "failed"
            receipt["error"] = f"disposable engine cleanup refused: {engine_stop.get('reason')}"
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not engine_stop["stopped"]:
            raise RuntimeError(receipt["error"])
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print(f"receipt={receipt_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"phase3 acceptance failed: {error}", file=sys.stderr)
        raise SystemExit(1)
