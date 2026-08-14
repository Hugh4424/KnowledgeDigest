# Task 3 P1 Phase Card

- Goal: extend the isolated Reader Bundle projection with a semantic snapshot seam while keeping the candidate package `not_released`.
- In scope: `src/knowledge_digest/reader_bundle.py`, `tests/acceptance/test_task3_projection.py`, `tests/fixtures/task3_full_release/projection-cases.json`.
- Required behavior: canonical Home → root → product/module/concept navigation; degraded topics remain in Audit; evidence-backed bidirectional Related links only; every supplied old path has a canonical alias or an explicit deprecated reason; Task 2-A inputs remain compatible.
- Covered AC: AC-02, AC-03, AC-04, AC-11.
- Non-goals: final `released`, human review, real 89-source acceptance, provider calls, changes to compiler/TopicAxis/navigation/formal pipeline.
- Predicted route: `feature` / `backend-testing`.
- Gate: `uv run --frozen pytest tests/acceptance/test_task3_projection.py -q`; RED must fail on the target contract, GREEN must pass with negative cases retained.
- Stop conditions: setup failure, weakened acceptance boundary, new product decision, or any change outside the declared files.
- Handoff: expose a stable semantic input/projection seam for P2 quality and release work.
