"""Task9 K3 publish-channel acceptance slices."""

from __future__ import annotations

import importlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = PROJECT_ROOT / "tests"
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from fixtures.task9_publish import make_batch_with_nav, make_kb


def _require_tree_hash():
    module = importlib.import_module("knowledge_digest.kb_publish")
    tree_hash = getattr(module, "kb_tree_hash", None)
    assert callable(tree_hash), "knowledge_digest.kb_publish.kb_tree_hash is not implemented"
    return tree_hash


def test_cli_entries_exist() -> None:
    """The three K3 commands are independently wired without changing digest."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]

    assert scripts["knowledge-digest-publish"] == "knowledge_digest.kb_publish:main"
    assert scripts["knowledge-digest-rollback"] == "knowledge_digest.kb_publish:main"
    assert scripts["knowledge-digest-accept"] == "knowledge_digest.kb_accept:main"
    assert scripts["digest"] == "knowledge_digest.simple_cli:main"

    for module_name in ("knowledge_digest.kb_publish", "knowledge_digest.kb_accept"):
        module = importlib.import_module(module_name)
        assert callable(module.main)

        help_result = subprocess.run(
            [sys.executable, "-m", module_name, "--help"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert help_result.returncode == 0, help_result.stderr
        assert "usage" in help_result.stdout.lower()


def test_tree_hash_frozen_algorithm(tmp_path: Path) -> None:
    tree_hash = _require_tree_hash()
    root = tmp_path / "version"
    (root / "nested").mkdir(parents=True)
    (root / "nested" / "a.txt").write_bytes(b"A")
    (root / "z.txt").write_bytes(b"Z\n")

    assert tree_hash(root) == "67fd45da021894df27ec0a093274cd1246c3143b981a3d8a62375953c6d2d3af"

    link = root / "link.txt"
    link.symlink_to(root / "nested" / "a.txt")
    with pytest.raises(ValueError):
        tree_hash(root)

    with pytest.raises(ValueError):
        tree_hash(tmp_path / "missing")


def _write_manifest(batch_dir: Path, payload: dict[str, object]) -> None:
    audit_dir = batch_dir / "_audit"
    audit_dir.mkdir(parents=True)
    (audit_dir / "page-manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def test_manifest_whitelist(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    load_batch_manifest = getattr(module, "load_batch_manifest", None)
    assert callable(load_batch_manifest), "knowledge_digest.kb_publish.load_batch_manifest is not implemented"

    base = {
        "schema_version": "task7-page-manifest.v1",
        "attempt_id": "attempt-1",
        "run_status": "complete",
        "publish_status": "not_released",
        "navigation": {"navigation_status": "generated_ok"},
        "blockers": [],
        "pages": [{"page_paths": ["products/acme/page.md"]}],
    }
    ready_dir = tmp_path / "ready"
    _write_manifest(ready_dir, base)
    ready = load_batch_manifest(ready_dir)
    assert ready["status"] == "ready"
    assert ready["manifest"] == base

    invalid_cases = (
        ({"run_status": "blocked"}, "run_status"),
        ({"publish_status": None}, "publish_status"),
        ({"navigation": None}, "navigation.navigation_status"),
        ({"navigation": {"navigation_status": "blocked"}}, "navigation.navigation_status"),
        ({"blockers": [{"reason": "failed"}]}, "blockers"),
        ({"publish_status": "released"}, "publish_status"),
    )
    for index, (changes, reason_field) in enumerate(invalid_cases):
        payload = dict(base)
        payload["navigation"] = dict(base["navigation"])
        payload.update(changes)
        if changes.get("publish_status") is None:
            payload.pop("publish_status")
        batch_dir = tmp_path / f"invalid-{index}"
        _write_manifest(batch_dir, payload)

        blocked = load_batch_manifest(batch_dir)
        assert blocked["status"] == "blocked"
        assert reason_field in blocked["reasons"]

    control_char_batch = tmp_path / "control-char-batch"
    control_char_payload = dict(base)
    control_char_payload["pages"] = [{"page_paths": ["products/acme/page.md\n  - private.md"]}]
    _write_manifest(control_char_batch, control_char_payload)
    (control_char_batch / "products/acme").mkdir(parents=True)
    (control_char_batch / "products/acme/page.md\n  - private.md").write_text("page\n", encoding="utf-8")
    with pytest.raises(ValueError, match="control characters"):
        module.construct_staging(
            tmp_path / "control-char-kb",
            control_char_batch,
            control_char_payload,
            module.sidecar_path(tmp_path / "control-char-kb"),
            run_id="control-char",
        )


def test_sidecar_layout_and_lock(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    sidecar_path = getattr(module, "sidecar_path", None)
    ensure_sidecar = getattr(module, "ensure_sidecar", None)
    kb_write_lock = getattr(module, "kb_write_lock", None)
    new_version_id = getattr(module, "new_version_id", None)
    assert callable(sidecar_path), "knowledge_digest.kb_publish.sidecar_path is not implemented"
    assert callable(ensure_sidecar), "knowledge_digest.kb_publish.ensure_sidecar is not implemented"
    assert callable(kb_write_lock), "knowledge_digest.kb_publish.kb_write_lock is not implemented"
    assert callable(new_version_id), "knowledge_digest.kb_publish.new_version_id is not implemented"

    kb_dir = tmp_path / "knowledge-base"
    sidecar = sidecar_path(kb_dir)
    assert sidecar == tmp_path / ".knowledge-base.kd"
    ensure_sidecar(sidecar)
    assert {
        path.name
        for path in sidecar.iterdir()
    } >= {"versions", "staging", "lkg", "releases", "receipts", "freeze"}

    (sidecar / "versions" / "20260915-120000-001").mkdir()
    (sidecar / "versions" / "20260915-120001-004").mkdir()
    assert new_version_id(sidecar, now=datetime(2026, 9, 15, 12, 1, 2, tzinfo=timezone.utc)) == "20260915-120102-005"

    with kb_write_lock(kb_dir):
        assert (tmp_path / ".digest.lock").is_file()
        with pytest.raises(ValueError):
            with kb_write_lock(kb_dir):
                pass


def test_sidecar_path_canonicalizes_symlinked_parent(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    sidecar_path = getattr(module, "sidecar_path", None)
    assert callable(sidecar_path)

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(real_parent, target_is_directory=True)

    assert sidecar_path(alias_parent / "knowledge-base") == real_parent / ".knowledge-base.kd"


def test_merge_construct(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    construct_staging = getattr(module, "construct_staging", None)
    ensure_target_kb = getattr(module, "ensure_target_kb", None)
    sidecar_path = getattr(module, "sidecar_path", None)
    ensure_sidecar = getattr(module, "ensure_sidecar", None)
    load_batch_manifest = getattr(module, "load_batch_manifest", None)
    assert callable(construct_staging), "knowledge_digest.kb_publish.construct_staging is not implemented"
    assert callable(ensure_target_kb), "knowledge_digest.kb_publish.ensure_target_kb is not implemented"
    assert callable(sidecar_path)
    assert callable(ensure_sidecar)
    assert callable(load_batch_manifest)

    batch = make_batch_with_nav(
        tmp_path / "batch-root",
        pages={
            "products/Acme/overview.md": "# New overview\n",
            "Home.md": "# New home\n",
        },
    )
    manifest = load_batch_manifest(batch)["manifest"]

    empty_kb = tmp_path / "empty-kb"
    sidecar = ensure_sidecar(sidecar_path(empty_kb))
    ensure_target_kb(empty_kb, sidecar)
    empty_result = construct_staging(empty_kb, batch, manifest, sidecar, run_id="merge-empty")
    empty_staging = empty_result["staging_dir"]
    assert (empty_staging / "kb.structure.md").is_file()
    assert (empty_staging / "products/Acme/overview.md").read_text(encoding="utf-8") == "# New overview\n"
    assert (empty_staging / "Home.md").read_text(encoding="utf-8") == "# New home\n"
    assert (empty_staging / "_audit/page-manifest.json").read_bytes() == (batch / "_audit/page-manifest.json").read_bytes()
    assert empty_result["tree_hash"]

    existing_kb = make_kb(
        tmp_path / "existing-root",
        files={
            "products/Acme/overview.md": "# Old overview\n",
            "private/keep.md": "keep this unmanaged file\n",
        },
    )
    existing_sidecar = ensure_sidecar(sidecar_path(existing_kb))
    existing_result = construct_staging(existing_kb, batch, manifest, existing_sidecar, run_id="merge-existing")
    existing_staging = existing_result["staging_dir"]
    assert (existing_staging / "products/Acme/overview.md").read_text(encoding="utf-8") == "# New overview\n"
    assert (existing_staging / "private/keep.md").read_text(encoding="utf-8") == "keep this unmanaged file\n"

    collision_batch = make_batch_with_nav(
        tmp_path / "collision-root",
        pages={"products/Acme/overview.md": "# Collision\n"},
        extra_files={"private/keep.md": "attempted overwrite\n"},
    )
    collision_manifest = load_batch_manifest(collision_batch)["manifest"]
    collision_kb = make_kb(
        tmp_path / "collision-kb-root",
        files={"private/keep.md": "original\n"},
    )
    collision_sidecar = ensure_sidecar(sidecar_path(collision_kb))
    with pytest.raises(ValueError, match="path_collision_unmanaged"):
        construct_staging(collision_kb, collision_batch, collision_manifest, collision_sidecar, run_id="merge-collision")
    assert (collision_kb / "private/keep.md").read_text(encoding="utf-8") == "original\n"

    missing_batch = make_batch_with_nav(
        tmp_path / "missing-page-root",
        pages={"products/Acme/missing.md": "# Missing\n"},
    )
    (missing_batch / "products/Acme/missing.md").unlink()
    missing_manifest = load_batch_manifest(missing_batch)["manifest"]
    with pytest.raises(ValueError, match="manifest page is missing"):
        construct_staging(
            existing_kb,
            missing_batch,
            missing_manifest,
            existing_sidecar,
            run_id="merge-missing-page",
        )

    with pytest.raises(ValueError, match="run_id must be one safe path component"):
        construct_staging(
            existing_kb,
            batch,
            manifest,
            existing_sidecar,
            run_id="../escape",
        )
    assert not (existing_sidecar / "escape").exists()


def test_first_publish_skeleton(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    ensure_target_kb = getattr(module, "ensure_target_kb", None)
    sidecar_path = getattr(module, "sidecar_path", None)
    assert callable(ensure_target_kb), "knowledge_digest.kb_publish.ensure_target_kb is not implemented"
    assert callable(sidecar_path)

    empty_kb = tmp_path / "new-kb"
    initialized = ensure_target_kb(empty_kb, sidecar_path(empty_kb))
    structure = empty_kb / "kb.structure.md"
    assert initialized["status"] == "initialized"
    assert initialized["structure_path"] == structure
    assert initialized["structure_sha256"] == hashlib.sha256(structure.read_bytes()).hexdigest()
    assert "managed_paths:" in structure.read_text(encoding="utf-8")

    invalid_kb = tmp_path / "invalid-kb"
    invalid_kb.mkdir()
    (invalid_kb / "existing.md").write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="kb.structure.md"):
        ensure_target_kb(invalid_kb, sidecar_path(invalid_kb))

    conflict_kb = make_kb(tmp_path / "conflict-root")
    (conflict_kb / "current").write_text("not a symlink\n", encoding="utf-8")
    with pytest.raises(ValueError, match="current_name_conflict"):
        ensure_target_kb(conflict_kb, sidecar_path(conflict_kb))


def test_publish_happy_path(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = getattr(module, "publish", None)
    kb_tree_hash = getattr(module, "kb_tree_hash", None)
    sidecar_path = getattr(module, "sidecar_path", None)
    assert callable(publish), "knowledge_digest.kb_publish.publish is not implemented"
    assert callable(kb_tree_hash)
    assert callable(sidecar_path)

    batch = make_batch_with_nav(
        tmp_path / "batch-root",
        pages={
            "products/Acme/overview.md": "# Published overview\n",
            "Home.md": "# Published home\n",
        },
    )
    kb = make_kb(
        tmp_path / "kb-root",
        files={
            "products/Acme/overview.md": "# Previous overview\n",
            "private/keep.md": "keep this content\n",
        },
    )
    old_hash = kb_tree_hash(kb)
    result = publish(
        batch,
        kb,
        run_id="release-1",
        now=datetime(2026, 9, 15, 12, 30, 0, tzinfo=timezone.utc),
    )

    assert result["status"] == "released"
    assert result["exit_code"] == 0
    assert result["no_op"] is False
    assert result["old_tree_hash"] == old_hash
    assert result["new_tree_hash"] == kb_tree_hash((kb / "current").resolve())
    assert result["verified"] is True
    current = kb / "current"
    assert current.is_symlink()
    assert os.readlink(current) == f"../.{kb.name}.kd/versions/{result['version_id']}"
    assert (current / "products/Acme/overview.md").read_text(encoding="utf-8") == "# Published overview\n"
    assert (current / "private/keep.md").read_text(encoding="utf-8") == "keep this content\n"
    assert list(path.name for path in kb.iterdir()) == ["current"]

    sidecar = sidecar_path(kb)
    assert (sidecar / "versions" / result["version_id"]).is_dir()
    pointer = json.loads((sidecar / "lkg" / "pointer.json").read_text(encoding="utf-8"))
    assert pointer["tree_hash"] == old_hash
    assert kb_tree_hash(sidecar / "lkg" / pointer["version_id"]) == old_hash
    release = json.loads((sidecar / "releases" / f"{result['version_id']}.json").read_text(encoding="utf-8"))
    assert release["new_tree_hash"] == result["new_tree_hash"]
    assert release["batch_attempt_id"] == "fixture-attempt"
    assert not (sidecar / "staging" / "release-1").exists()


def test_publish_noop(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = getattr(module, "publish", None)
    sidecar_path = getattr(module, "sidecar_path", None)
    assert callable(publish), "knowledge_digest.kb_publish.publish is not implemented"
    assert callable(sidecar_path)

    batch = make_batch_with_nav(tmp_path / "batch-root")
    kb = make_kb(tmp_path / "kb-root")
    first = publish(batch, kb, run_id="release-first", now=datetime(2026, 9, 15, 12, 30, tzinfo=timezone.utc))
    sidecar = sidecar_path(kb)
    versions_before = sorted(path.name for path in (sidecar / "versions").iterdir())
    pointer_before = (sidecar / "lkg" / "pointer.json").read_bytes()

    second = publish(batch, kb, run_id="release-noop", now=datetime(2026, 9, 15, 12, 31, tzinfo=timezone.utc))

    assert first["status"] == "released"
    assert second["status"] == "released"
    assert second["exit_code"] == 0
    assert second["no_op"] is True
    assert second["version_id"] == first["version_id"]
    assert sorted(path.name for path in (sidecar / "versions").iterdir()) == versions_before
    assert (sidecar / "lkg" / "pointer.json").read_bytes() == pointer_before
    assert not (sidecar / "staging" / "release-noop").exists()


def test_failure_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = getattr(module, "publish", None)
    kb_tree_hash = getattr(module, "kb_tree_hash", None)
    sidecar_path = getattr(module, "sidecar_path", None)
    assert callable(publish), "knowledge_digest.kb_publish.publish is not implemented"
    assert callable(kb_tree_hash)
    assert callable(sidecar_path)

    first_batch = make_batch_with_nav(tmp_path / "first-batch")
    second_batch = make_batch_with_nav(
        tmp_path / "second-batch",
        pages={"products/Acme/overview.md": "# Changed\n"},
    )
    kb = make_kb(tmp_path / "kb-root")
    publish(first_batch, kb, run_id="release-first")
    before_hash = kb_tree_hash((kb / "current").resolve())
    sidecar = sidecar_path(kb)

    copies = 0

    def fail_during_copy(source: Path, destination: Path) -> None:
        nonlocal copies
        copies += 1
        if copies == 2:
            raise OSError("injected copy failure")
        shutil.copy2(source, destination)

    failed = publish(
        second_batch,
        kb,
        run_id="release-failed",
        copy_file=fail_during_copy,
    )
    assert failed["status"] == "failed"
    assert failed["exit_code"] != 0
    assert failed["reason_code"] == "publish_failed"
    assert failed["receipt_path"] == str(sidecar / "receipts/release-failed.json")
    assert kb_tree_hash((kb / "current").resolve()) == before_hash
    assert not (sidecar / "staging" / "release-failed").exists()

    receipt = json.loads(Path(failed["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["receipt"] is True
    assert receipt["batch_attempt_id"] == "fixture-attempt"
    assert receipt["elapsed_ms"] is not None
    assert receipt["provider_calls"] == 2
    assert receipt["provider_tokens"] == 13
    assert receipt["compile"]["inherited_from_compile"] is True

    real_write = module._atomic_write_json

    def fail_receipt_sink(path: Path, value: object) -> None:
        if path.name == "release-sink-failed.json":
            raise OSError("receipt sink unavailable")
        real_write(path, value)

    monkeypatch.setattr(module, "_atomic_write_json", fail_receipt_sink)
    copies = 0
    sink_failed = publish(
        second_batch,
        kb,
        run_id="release-sink-failed",
        copy_file=fail_during_copy,
    )
    assert sink_failed["status"] == "failed"
    assert sink_failed["reason_code"] == "receipt_sink_unavailable"
    assert sink_failed["original_reason_code"] == "publish_failed"
    assert "receipt_path" not in sink_failed


def test_failed_current_restore_keeps_a_complete_current(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = module.publish
    kb_tree_hash = module.kb_tree_hash
    sidecar_path = module.sidecar_path
    first_batch = make_batch_with_nav(tmp_path / "first-batch", pages={"products/Acme/page.md": "# first\n"})
    second_batch = make_batch_with_nav(tmp_path / "second-batch", pages={"products/Acme/page.md": "# second\n"})
    kb = make_kb(tmp_path / "kb-root")
    first = publish(first_batch, kb, run_id="restore-first")
    assert first["status"] == "released"

    real_replace = module.os.replace

    def fail_only_old_current_restore(source: Path, destination: Path) -> None:
        if destination.name == "current" and source.name.startswith(".current.restore-"):
            raise OSError("injected current restore failure")
        real_replace(source, destination)

    monkeypatch.setattr(module.os, "replace", fail_only_old_current_restore)

    def fail_after_switch(point: str) -> None:
        if point == "before_release_record":
            raise OSError("injected failure after switch")

    failed = publish(
        second_batch,
        kb,
        run_id="restore-current",
        fault=fail_after_switch,
        replace_file=real_replace,
    )

    assert failed["status"] == "failed"
    assert failed["reason_code"] == "publish_failed"
    assert "current restore failed" in failed["recovery_warning"]
    current = kb / "current"
    assert current.is_symlink()
    assert current.exists()
    assert current.resolve().parent == sidecar_path(kb) / "versions"
    assert kb_tree_hash(current.resolve()) == failed["new_tree_hash"]
    assert (sidecar_path(kb) / "versions" / failed["version_id"]).is_dir()
    pointer = json.loads((sidecar_path(kb) / "lkg" / "pointer.json").read_text(encoding="utf-8"))
    assert pointer["version_id"] == first["version_id"]
    assert (sidecar_path(kb) / "lkg" / first["version_id"]).is_dir()


def test_rollback(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = getattr(module, "publish", None)
    rollback = getattr(module, "rollback", None)
    kb_tree_hash = getattr(module, "kb_tree_hash", None)
    sidecar_path = getattr(module, "sidecar_path", None)
    assert callable(publish), "knowledge_digest.kb_publish.publish is not implemented"
    assert callable(rollback), "knowledge_digest.kb_publish.rollback is not implemented"
    assert callable(kb_tree_hash)
    assert callable(sidecar_path)

    first_batch = make_batch_with_nav(
        tmp_path / "first-batch",
        pages={"products/Acme/overview.md": "# Version one\n"},
        attempt_id="attempt-one",
    )
    second_batch = make_batch_with_nav(
        tmp_path / "second-batch",
        pages={"products/Acme/overview.md": "# Version two\n"},
        attempt_id="attempt-two",
    )
    kb = make_kb(tmp_path / "kb-root")
    first = publish(first_batch, kb, run_id="release-one")
    second = publish(second_batch, kb, run_id="release-two")
    assert first["status"] == "released"
    assert second["status"] == "released"
    first_hash = first["new_tree_hash"]
    second_hash = second["new_tree_hash"]
    sidecar = sidecar_path(kb)

    rolled_back = rollback(
        kb,
        run_id="rollback-one",
        now=datetime(2026, 9, 15, 13, 0, tzinfo=timezone.utc),
    )
    assert rolled_back["status"] == "rolled_back"
    assert rolled_back["exit_code"] == 0
    assert rolled_back["new_tree_hash"] == first_hash
    assert rolled_back["old_tree_hash"] == second_hash
    assert rolled_back["verified"] is True
    assert kb_tree_hash((kb / "current").resolve()) == first_hash
    pointer = json.loads((sidecar / "lkg" / "pointer.json").read_text(encoding="utf-8"))
    assert pointer["tree_hash"] == second_hash
    assert pointer["batch_attempt_id"] == "attempt-two"
    assert kb_tree_hash(sidecar / "lkg" / pointer["version_id"]) == second_hash
    assert not (sidecar / "staging" / "rollback-one").exists()

    pointer_path = sidecar / "lkg" / "pointer.json"
    pointer_path.write_text("not-json\n", encoding="utf-8")
    before_corrupt_hash = kb_tree_hash((kb / "current").resolve())
    rejected = rollback(kb, run_id="rollback-corrupt")
    assert rejected["status"] in {"blocked", "failed"}
    assert rejected["exit_code"] != 0
    assert rejected["reason_code"] in {"rollback_pointer_invalid", "rollback_failed"}
    assert kb_tree_hash((kb / "current").resolve()) == before_corrupt_hash


def test_failed_rollback_current_restore_keeps_a_complete_current(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = module.publish
    rollback = module.rollback
    kb_tree_hash = module.kb_tree_hash
    sidecar_path = module.sidecar_path
    first_batch = make_batch_with_nav(tmp_path / "first-batch", pages={"products/Acme/page.md": "# first\n"})
    second_batch = make_batch_with_nav(tmp_path / "second-batch", pages={"products/Acme/page.md": "# second\n"})
    kb = make_kb(tmp_path / "kb-root")
    first = publish(first_batch, kb, run_id="rollback-restore-first")
    second = publish(second_batch, kb, run_id="rollback-restore-second")
    assert first["status"] == "released"
    assert second["status"] == "released"

    real_replace = module.os.replace

    def fail_only_old_current_restore(source: Path, destination: Path) -> None:
        if destination.name == "current" and source.name.startswith(".current.restore-"):
            raise OSError("injected rollback current restore failure")
        real_replace(source, destination)

    monkeypatch.setattr(module.os, "replace", fail_only_old_current_restore)

    def fail_after_pointer(sidecar: Path, keep: str | None) -> None:
        raise OSError("injected rollback failure after pointer")

    monkeypatch.setattr(module, "_prune_lkg", fail_after_pointer)

    failed = rollback(
        kb,
        run_id="rollback-restore-current",
        replace_file=real_replace,
    )

    assert failed["status"] == "failed"
    assert failed["reason_code"] == "rollback_failed"
    assert "current restore failed" in failed["recovery_warning"]
    current = kb / "current"
    assert current.is_symlink()
    assert current.exists()
    assert current.resolve().parent == sidecar_path(kb) / "versions"
    assert kb_tree_hash(current.resolve()) == failed["new_tree_hash"]
    assert (sidecar_path(kb) / "versions" / failed["version_id"]).is_dir()
    pointer = json.loads((sidecar_path(kb) / "lkg" / "pointer.json").read_text(encoding="utf-8"))
    assert pointer["version_id"] == second["version_id"]
    assert (sidecar_path(kb) / "lkg" / second["version_id"]).is_dir()


def test_run_record_costs(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = getattr(module, "publish", None)
    assert callable(publish), "knowledge_digest.kb_publish.publish is not implemented"

    batch = make_batch_with_nav(
        tmp_path / "batch-root",
        run_metrics={
            "elapsed_ms": 101,
            "provider_calls": 7,
            "provider_tokens": 42,
            "reasons": {},
        },
    )
    kb = make_kb(tmp_path / "kb-root")

    def fail_copy(source: Path, destination: Path) -> None:
        raise OSError("injected failure after compile")

    failed = publish(kb_dir=kb, batch_dir=batch, run_id="cost-failed", copy_file=fail_copy)
    assert failed["exit_code"] != 0
    assert failed["provider_calls"] == 7
    assert failed["provider_tokens"] == 42
    assert failed["elapsed_ms"] is not None
    assert failed["compile"] == {
        "elapsed_ms": 101,
        "provider_calls": 7,
        "provider_tokens": 42,
        "inherited_from_compile": True,
    }
    assert failed["publish"]["provider_calls"] == 0
    assert failed["publish"]["provider_tokens"] == 0
    assert failed["publish"]["reasons"]["provider_calls"] == "no_provider_call_yet"

    no_metrics_batch = make_batch_with_nav(tmp_path / "no-metrics-batch")
    (no_metrics_batch / "_audit" / "run-metrics.json").unlink()
    no_metrics_kb = make_kb(tmp_path / "no-metrics-kb")
    no_metrics = publish(no_metrics_batch, no_metrics_kb, run_id="cost-zero")
    assert no_metrics["status"] == "released"
    assert no_metrics["provider_calls"] == 0
    assert no_metrics["provider_tokens"] == 0
    assert no_metrics["reasons"]["provider_calls"] == "no_provider_call_yet"
    assert no_metrics["reasons"]["provider_tokens"] == "no_provider_call_yet"

    invalid_batch = make_batch_with_nav(
        tmp_path / "invalid-cost-batch",
        run_metrics={"elapsed_ms": 0, "provider_calls": 0, "provider_tokens": 0, "reasons": {}},
    )
    invalid_kb = make_kb(tmp_path / "invalid-cost-kb")
    invalid = publish(invalid_batch, invalid_kb, run_id="cost-invalid")
    assert invalid["status"] == "blocked"
    assert invalid["exit_code"] != 0
    assert "requires a reason" in str(invalid["error"])

    contradictory_batch = make_batch_with_nav(
        tmp_path / "contradictory-cost-batch",
        run_metrics={
            "elapsed_ms": 1,
            "provider_calls": 1,
            "provider_tokens": 1,
            "reasons": {"provider_calls": "no_provider_call_yet"},
        },
    )
    contradictory = publish(contradictory_batch, make_kb(tmp_path / "contradictory-cost-kb"), run_id="cost-contradictory")
    assert contradictory["status"] == "blocked"
    assert "zero-value reason" in str(contradictory["error"])


def test_run_record_inherits_k2_costs(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = getattr(module, "publish", None)
    assert callable(publish)

    batch = make_batch_with_nav(
        tmp_path / "batch-root",
        run_metrics={
            "elapsed_ms": 101,
            "provider_calls": 7,
            "provider_tokens": 42,
            "reasons": {},
            "task8_navigation": {
                "elapsed_ms": 13,
                "provider_calls": 3,
                "actual_provider_calls": 3,
                "provider_tokens": 19,
                "actual_provider_tokens": 19,
                "provider_token_observations": 3,
                "reasons": {},
            },
        },
    )
    kb = make_kb(tmp_path / "kb-root")

    def fail_copy(source: Path, destination: Path) -> None:
        raise OSError("injected failure after compile")

    failed = publish(kb_dir=kb, batch_dir=batch, run_id="cost-k1-k2", copy_file=fail_copy)
    assert failed["exit_code"] != 0
    assert failed["provider_calls"] == 10
    assert failed["provider_tokens"] == 61
    assert failed["compile"] == {
        "elapsed_ms": 114,
        "provider_calls": 10,
        "provider_tokens": 61,
        "inherited_from_compile": True,
    }


def test_positive_partial_token_observation_is_publishable(tmp_path: Path) -> None:
    """Positive token totals use observation counts, not a zero-value reason."""
    from knowledge_digest.kb_publish import publish
    from knowledge_digest.semantic_navigation import _write_navigation_metrics

    batch = make_batch_with_nav(
        tmp_path / "partial-token-batch",
        run_metrics={
            "elapsed_ms": 5,
            "provider_calls": 0,
            "provider_tokens": 0,
            "reasons": {
                "provider_calls": "no_provider_call_yet",
                "provider_tokens": "no_provider_call_yet",
            },
        },
    )
    _write_navigation_metrics(
        batch,
        page_count=2,
        provider_calls=2,
        cache_hits=0,
        provider_tokens=19,
        provider_token_observations=1,
        elapsed_ms=13,
    )
    navigation = json.loads((batch / "_audit" / "run-metrics.json").read_text(encoding="utf-8"))["task8_navigation"]
    assert navigation["provider_tokens"] == 19
    assert navigation["provider_token_observations"] == 1
    assert "provider_tokens" not in navigation["reasons"]

    published = publish(batch, make_kb(tmp_path / "partial-token-kb"), run_id="partial-token")
    assert published["status"] == "released"
    assert published["provider_tokens"] == 19


def test_negative_injections(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_publish")
    publish = module.publish
    kb_tree_hash = module.kb_tree_hash
    sidecar_path = module.sidecar_path
    first_batch = make_batch_with_nav(tmp_path / "first", pages={"products/acme/page.md": "# old\n"})
    second_batch = make_batch_with_nav(tmp_path / "second", pages={"products/acme/page.md": "# new\n"})
    injection_batch = make_batch_with_nav(tmp_path / "injection", pages={"products/acme/page.md": "# newer\n"})
    kb = make_kb(tmp_path / "kb")
    first = publish(first_batch, kb, run_id="negative-first")
    old_hash = first["new_tree_hash"]
    second = publish(second_batch, kb, run_id="negative-second")
    new_hash = second["new_tree_hash"]
    sidecar = sidecar_path(kb)

    copies = 0

    def fail_copy(source: Path, destination: Path) -> None:
        nonlocal copies
        copies += 1
        if copies == 2:
            raise OSError("copy interrupted")
        shutil.copy2(source, destination)

    interrupted = publish(injection_batch, kb, run_id="negative-copy", copy_file=fail_copy)
    assert interrupted["exit_code"] != 0
    assert kb_tree_hash((kb / "current").resolve()) in {old_hash, new_hash}
    assert not (sidecar / "staging" / "negative-copy").exists()

    cancelled = publish(injection_batch, kb, run_id="negative-cancel", cancel=lambda: True)
    assert cancelled["exit_code"] != 0
    assert kb_tree_hash((kb / "current").resolve()) in {old_hash, new_hash}
    assert not (sidecar / "staging" / "negative-cancel").exists()

    def corrupt_staging(point: str) -> None:
        if point == "before_version_move":
            (sidecar / "staging" / "negative-hash" / "products/acme/page.md").write_text("corrupt\n", encoding="utf-8")

    corrupted = publish(injection_batch, kb, run_id="negative-hash", fault=corrupt_staging)
    assert corrupted["exit_code"] != 0
    assert kb_tree_hash((kb / "current").resolve()) in {old_hash, new_hash}
    assert not (sidecar / "staging" / "negative-hash").exists()

    out_of_bounds = make_batch_with_nav(
        tmp_path / "out-of-bounds",
        pages={"products/acme/page.md": "# newer\n"},
        extra_files={"private/unmanaged.md": "must not overwrite\n"},
    )
    before_bytes = (kb / "current" / "products/acme/page.md").read_bytes()
    blocked = publish(out_of_bounds, kb, run_id="negative-boundary")
    assert blocked["exit_code"] != 0
    assert blocked["reason_code"] == "path_outside_allowed"
    assert (kb / "current" / "products/acme/page.md").read_bytes() == before_bytes
    assert not (sidecar / "staging" / "negative-boundary").exists()

    def fail_after_lkg(point: str) -> None:
        if point == "before_release_record":
            raise OSError("release record interrupted")

    after_lkg = publish(injection_batch, kb, run_id="negative-after-lkg", fault=fail_after_lkg)
    assert after_lkg["exit_code"] != 0
    assert not (sidecar / "staging" / "negative-after-lkg").exists()
    assert not (sidecar / "lkg" / second["version_id"]).exists()
    retry = publish(injection_batch, kb, run_id="negative-after-lkg-retry")
    assert retry["status"] == "released"

    escaped = publish(injection_batch, kb, run_id="../outside")
    assert escaped["exit_code"] != 0
    assert "run_id must be one safe path component" in escaped["error"]
    assert not (tmp_path / "outside").exists()


def test_defect_ledger(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    append_ledger = getattr(module, "append_ledger", None)
    read_ledger = getattr(module, "read_ledger", None)
    void_record = getattr(module, "void_record", None)
    assert callable(append_ledger)
    assert callable(read_ledger)
    assert callable(void_record)
    kb = make_kb(tmp_path / "ledger-kb")
    row = append_ledger(
        kb,
        {
            "id": "K1-001",
            "severity": "blocking",
            "evidence": "audit/failure.json",
            "fixed_by_this_card": True,
            "repair_batch_hash": "a" * 64,
        },
    )
    assert row["id"] == "K1-001"
    void_record(kb, "accept-old", "repaired in a new batch")
    rows = read_ledger(kb)
    assert [item["type"] for item in rows] == ["defect", "void"]
    assert rows[0]["repair_batch_hash"] == "a" * 64
    assert rows[1]["record_id"] == "accept-old"
