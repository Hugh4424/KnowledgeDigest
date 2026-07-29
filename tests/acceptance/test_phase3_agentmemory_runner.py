from __future__ import annotations

import json
import importlib.util
from pathlib import Path

_SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "phase3_agentmemory_acceptance.py"
_SPEC = importlib.util.spec_from_file_location("phase3_agentmemory_acceptance", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

SELECTED_RELATIVE = _MODULE.SELECTED_RELATIVE
copy_corpus = _MODULE.copy_corpus
isolated_agentmemory_env = _MODULE.isolated_agentmemory_env
memory_write_counts = _MODULE.memory_write_counts
provenance_validation_exit = _MODULE.provenance_validation_exit
write_agentmemory_config = _MODULE.write_agentmemory_config


def provenance_fixture(claim: dict[str, str]) -> str:
    payload = {
        "claim": claim["text"],
        "claim_fingerprint": claim["claim_fingerprint"],
        "source_uri": claim["source_uri"],
        "fragment_locator": claim["fragment_locator"],
        "content_fingerprint": claim["content_fingerprint"],
        "source_snapshot_ref": claim["source_snapshot_ref"],
        "raw_id": claim["raw_id"],
    }
    return "KD_PROVENANCE_V1\n" + json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def test_copy_corpus_selects_three_inputs_and_keeps_other_markdown_in_company_kb(tmp_path: Path) -> None:
    source = tmp_path / "source"
    for relative in (*SELECTED_RELATIVE, Path("old/page.md")):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {relative}\n事实\n", encoding="utf-8")

    layout = copy_corpus(source, tmp_path / "run")

    assert layout["selected_count"] == 3
    assert sorted(layout["selected_relative_paths"]) == sorted(map(str, SELECTED_RELATIVE))
    for relative in SELECTED_RELATIVE:
        assert (tmp_path / "run" / "new-input" / "items" / relative).is_file()
    assert (tmp_path / "run" / "company-kb" / "pages" / "old/page.md").is_file()
    rows = [json.loads(line) for line in (tmp_path / "run" / "sources.jsonl").read_text().splitlines()]
    assert sum(row["selected_new_input"] for row in rows) == 3


def test_agentmemory_environment_and_paths_are_inside_temp_root(tmp_path: Path) -> None:
    instance = tmp_path / "agentmemory-instance"
    ports = {"rest": 3211, "stream": 3212, "viewer": 3213, "engine": 49234}
    paths = write_agentmemory_config(instance, ports)
    env = isolated_agentmemory_env(instance, paths, ports)

    for key in ("HOME", "AGENTMEMORY_III_CONFIG"):
        assert Path(env[key]).resolve().is_relative_to(tmp_path.resolve())
    assert Path(paths["state_path"]).is_relative_to(tmp_path)
    assert Path(paths["stream_path"]).is_relative_to(tmp_path)
    assert ports["rest"] != 3111
    assert ports["stream"] != 3112
    assert ports["engine"] != 49134


def test_replay_created_count_is_zero() -> None:
    class Write:
        def __init__(self, status: str) -> None:
            self.status = status

    assert memory_write_counts([Write("duplicate"), Write("duplicate")]) == {"created": 0, "duplicate": 2}


def test_provenance_reverse_validation_is_nonzero_then_zero() -> None:
    claim = {
        "text": "事实",
        "claim_fingerprint": "claim-1",
        "source_uri": "confluence://company/page.md",
        "fragment_locator": "lines:1-1",
        "content_fingerprint": "content-1",
        "source_snapshot_ref": "snapshot-1",
        "raw_id": "raw-1",
    }
    memory = {"id": "memory-1", "project": "phase3", "content": provenance_fixture(claim)}
    assert provenance_validation_exit([memory], [claim]) == (0, 0)
    assert provenance_validation_exit([], [claim]) == (1, 1)
    assert provenance_validation_exit([memory], [claim]) == (0, 0)
