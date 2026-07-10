# Tasks: Phase 0 Knowledge Digest

## Depends On

| Task | Depends On | Parallel | Reason |
|---|---|---|---|
| T001 | none | no | CLI contract and the initial acceptance test skeleton are prerequisites for all later gate_cmd checks. |
| T002 | T001 | no | Directory/KB validation and minimal fixture skeletons hang off parsed CLI args. |
| T003 | T001, T002 | no | Run directory and dry-run semantics need validated paths. |
| T004 | T002, T003 | no | S1 writes into the run directory and consumes validated new_dir. |
| T005 | T004 | no | S2 consumes RawItem output. |
| T006 | T005 | no | S3 consumes clusters. |
| T007 | T006 | no | S4 consumes evolution decisions. |
| T008 | T007 | no | S5 consumes safe drafts. |
| T009 | T008 | no | S6 audits final writeback/provenance. |
| T010 | T001-T009 | no | Full acceptance completion extends the test skeleton and fixture skeletons already created earlier. |
| T011 | T010 | no | Docs update references final verified behavior. |

## Stage 1: Contract and filesystem foundation

- T001 [FR-CONTRACT-001, AC-001, AC-002] Create `pyproject.toml`, `src/knowledge_digest/__init__.py`, `src/knowledge_digest/cli.py`, `src/knowledge_digest/config.py`, `src/knowledge_digest/errors.py`, and the initial `tests/acceptance/test_phase0_digest.py` gate skeleton for the manual `digest(new_dir, kb_dir)` entry, required args, optional args, defaults, exit codes, and stderr contract. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "cli_contract"`.
- T002 [FR-CONTRACT-002, FR-CONTRACT-003, AC-002] Create `src/knowledge_digest/paths.py`, `src/knowledge_digest/kb_structure.py`, and minimal fixture skeletons under `tests/fixtures/phase0_digest/` for `new_dir`/`kb_dir` validation and `kb.structure.md` parsing/defaults. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "missing_inputs or kb_structure"`.
- T003 [FR-CONTRACT-001, FR-CONTRACT-002, AC-001, AC-002, AC-011] Create `src/knowledge_digest/pipeline.py` run skeleton and dry-run guard so dry-run changes only appear in the run report. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "dry_run_contract"`.

## Stage 2: S1-S4 processing pipeline

- T004 [FR-STRUCTURE-001, FR-BEHAV-001, AC-003, AC-009] Create `src/knowledge_digest/jsonl.py` and `src/knowledge_digest/ingest.py`; extend fixture files under `tests/fixtures/phase0_digest/new_dir/`; implement RawItem output, exact dedupe, empty-shell filtering, and ingest failure records. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s1"`.
- T005 [FR-STRUCTURE-002, AC-004] Create `src/knowledge_digest/cluster.py` and `src/knowledge_digest/queues.py`; implement complete-linkage clustering, tier assignment, queue output, and model-failure semantics. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s2"`.
- T006 [FR-STRUCTURE-003, AC-005] Create `src/knowledge_digest/retrieve.py`; implement top-k association and `new`/`revise`/`merge_multiple` decisions with candidate preservation and reasons. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s3"`.
- T007 [FR-STRUCTURE-004, FR-BEHAV-001, AC-006, AC-010] Create `src/knowledge_digest/draft.py` and `src/knowledge_digest/faithfulness.py`; implement drafts, claim support checks, unsupported claims, removed claims, faithfulness fallback, and split suggestions. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s4 or split_suggestion"`.

## Stage 3: Writeback, provenance, and acceptance

- T008 [FR-STRUCTURE-005, FR-CONTRACT-001, FR-BEHAV-001, AC-007, AC-011] Create `src/knowledge_digest/writeback.py`; implement temp-file/fsync/atomic-rename writeback, archive behavior, write-report, write failure handling, and dry-run planned changes. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s5 or dry_run_contract"`.
- T009 [FR-STRUCTURE-006, FR-BEHAV-001, AC-008, AC-009] Create `src/knowledge_digest/provenance.py`; implement provenance audit and final claim source enforcement, including zero final references to empty-shell sources. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q -k "s6 or provenance"`.
- T010 [FR-BEHAV-002, AC-001, AC-002, AC-003, AC-005, AC-008, AC-009, AC-010, AC-011] Complete `tests/acceptance/test_phase0_digest.py` and fixture files under `tests/fixtures/phase0_digest/`; cover new, revise, merge_multiple, empty-shell filtering, long-doc split suggestion, source checks, forbidden-scope absence, and 3 negative AC-002 cases: missing `new_dir`, missing `kb_dir`, missing `kb.structure.md`. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q`.
- T011 [FR-CONTRACT-001, FR-CONTRACT-002, FR-STRUCTURE-001, FR-STRUCTURE-006, FR-BEHAV-002, AC-001-AC-011] Modify `docs/plans/phase0-implementation-spec.md` with final implementation-plan reference after build-plan human approval. Verify: `python -m pytest tests/acceptance/test_phase0_digest.py -q` and `rg -n "落地计划|implementation plan|digest\(new_dir, kb_dir\)" docs/plans/phase0-implementation-spec.md`.
