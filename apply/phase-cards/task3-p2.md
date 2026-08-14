# Task3 Phase P2

- Goal: freeze the 89-source/17+3 automatic quality contract, produce summary confirmation, and protect the old formal root during release/recovery.
- Allowed files: `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/full_release.py`, `tests/acceptance/test_task3_quality_release.py`, `tests/fixtures/task3_full_release/release-cases.json`, plus this evidence/status area.
- Covered AC: AC-01, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10.
- Non-goals: no Task2C schema rewrite, no `lock.py`/`provenance.py` rewrite, no formal real publish, no `human_reviewed`, no new product state.
- Compatibility boundary: Task2C wrapper/schema remains unchanged; candidate remains `not_released` until current-run confirmation and locked readback.
- Test route: `feature / backend-testing`; focused `test_task3_quality_release.py` RED/GREEN and related Task2C regression.
- Stop conditions: threshold weakening, unknown treated as warning, stale confirmation accepted, partial root switch, or fixture presented as real 89-source evidence.
- Stage-end summary: automatic gates and recovery code are test-backed; real 89-source/provider evidence and independent review remain separate facts.
