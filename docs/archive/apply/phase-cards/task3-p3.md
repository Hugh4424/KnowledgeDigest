# Task3 Phase P3

- Goal: produce a fixed Task2/CompanyBrain/Task3 comparison and a thin handoff entrypoint.
- Allowed files: `scripts/task2_publication_comparison.py`, `scripts/task3_full_release.py`, `tests/acceptance/test_task3_closeout.py`, `tests/fixtures/task3_full_release/closeout-cases.json`, plus this evidence/status area.
- Covered AC: AC-12, AC-13.
- Non-goals: no changes to `digest` CLI, page compiler, root docs, release semantics, or Closeout business scope.
- Compatibility boundary: comparison is evidence-only with per-dimension `comparable/N/A`; entrypoint reads status from readback and never upgrades it.
- Test route: `feature / backend-testing`; focused comparison and entrypoint RED/GREEN, then aggregate regression.
- Stop conditions: subjective total score, inferred comparability, status rewrite, new pages/topics/quality gates, or fixture treated as live baseline.
- Stage-end summary: eight comparison dimensions and the fixed seven-step handoff are implemented; real evidence remains for verify-code.
