# K4 findings

- Current task worktree: `/Users/Hugh/Hugh/Project/KnowledgeDigest-task10-slimming-without-capability-loss`.
- K4 authoritative decision log freezes B0 minimal semantic same-batch rerun plus active dedup regression, B1/B2/B3/B4 retirement boundaries, and exact 21-config A-list.
- Five formal `pyproject.toml [project.scripts]` roots are the reachability roots, but static closure is not pytest safety.
- A read-only cross-check found 42 test files importing B1/B2 candidates; plan must explicitly migrate or synchronously delete these historical assets and retain active K1/K2/K3 assertions.
- Active semantic anchors to preserve: `semantic_page.MAX_NARRATIVE_LINES`/`render_pages`, `semantic_cache.ModelCache.get_or_call`, `semantic_compiler.compile_batch`/`_model_results`/`_attempt_id`, `semantic_audit.build_audit`/`write_audit`, `semantic_navigation.compile_batch_navigation`, `kb_publish.publish`/`rollback`, and `kb_accept.main`.
- No dedicated K4 metrics script existed before this plan; `scripts/task10_metrics.py` is a planned deliverable, not evidence.
- `tests/acceptance/test_task5_*` and `tests/test_simple_digest.py` are real existing assets; fictional `test_task10_*` paths were removed from the plan.

## 2026-09-17 — output-quality diagnosis started

- Reproduced the user-visible symptom against `/Users/Hugh/Downloads/KD测试/task10-real-digest-2026-09-17/2026-09-17-1`: 133 Markdown files, 4,320 inline `来源：` labels across 125 files, and no `Summary`/`Evidence`/`Provenance` sections.
- The generated `Home.md` explicitly says the batch is a temporary comparison artifact and that the formal entry is K3. The recorded real-digest result is `run_status=complete` but `publish_status=not_released`.
- Initial ranked hypotheses: K4 real-digest evidence ran K1/K2 only and was presented as final; K1 mixes audit provenance into reader body; K2 supplies navigation but not reader synthesis; K3 publish/acceptance was not used as the delivery gate; K4 scope cannot improve content quality because it is a slimming/checkpoint/dedup task.

### Confirmed root-cause chain

1. **Wrong layer delivered**: `src/knowledge_digest/semantic_cli.py:112-146` calls `compile_batch()` and then `compile_batch_navigation()` only. It never calls `kb_publish.publish()` or `kb_accept.main`; `semantic_compiler` hard-codes `publish_status="not_released"`. The result is K1+K2, not a K3 Reader release.
2. **K1 is intentionally raw/reference-oriented**: `semantic_page.py:495-505` builds `来源：...` attribution, and `_reference_unit`/`_narrative_units` append it to every rendered block/claim. The real output has 4,320 such lines. This is acceptable as a temporary K1 trace surface only if Audit/K3 reader projection follows; it is not a usable final Reader surface.
3. **K2 only builds navigation**: `CONTEXT.md` defines K2 as `Home → Index → module Index`, explicitly temporary and not knowledge-use evidence. Current `Home.md` says the same: “临时对照产物；正式入口归 K3”.
4. **K3 is a copier/release gate, not a semantic repair stage**: `kb_publish.construct_staging()` validates and copies batch files; it does not turn raw K1 pages into Task 2-B/2-C Reader pages. If the batch is wrong, publishing it cannot make it reader-quality.
5. **K4 scope explicitly forbids the missing work**: K4 `spec.md`/`plan.md` say not to change K1/K2/K3 semantics and only add checkpoint/dedup plus deletion/metrics. The K4 real-digest receipt therefore proves execution, not PRD reader quality.

### Differential evidence

- Current K4 batch: 133 Markdown files, 4,320 inline source labels, no `Summary/Evidence/Provenance` sections.
- Task9 `task9-real-final` batch: 133 Markdown files, 4,319 inline source labels, same raw K1/K2 shape; 109 of 119 shared-path files are byte-identical to current K4, so K4 did not create the quality regression.
- Earlier `release4/bundle`: 107 Markdown files, 3 source labels, rich Home question/scenario navigation, typed `concept/operation/diagnosis/experience` Reader pages, and Audit back-links. This is the materially better layer the user remembers.
- PRD explicitly says Task 0–2 are `not_released`, Task 3 is the only release path, and “正文可读而非 Evidence dump”; the current K4 output fails this surface check by construction.
- Read-only `git log --all` encountered a missing historical object while traversing old history; direct baseline `git show eee5549:...` reads succeeded, so the root-cause comparison does not depend on that failed traversal.

## 2026-09-17 — authorized Reader recovery result

- Added `src/knowledge_digest/reader_projection.py` as the K3 boundary. It supports fresh semantic projection, exact frozen-source citation rebinding, provider/cache fail-closed behavior, clean Reader rendering, and verified same-corpus seed promotion.
- Added `--reader-seed` to `semantic_cli.py`; seed promotion compares every source hash from the seed with the current K1 `source_snapshot` before writing any Reader page. A mismatch is rejected.
- K1/K2 facts are copied unchanged to the candidate's `_audit/k1/`; K3 writes a separate `_audit/sources.jsonl`, `seed-binding.json`, `reader-manifest.json`, and `page-manifest.json`. K3 never treats old seed receipts as current release facts.
- The clean published result is `/Users/Hugh/Downloads/KD测试/task10-reader-final-kb-2026-09-17-final/current`: 99 Reader pages, 89 source snapshot entries, no `来源：` page labels, no leaked internal Claim IDs, max 113 lines, 0 broken internal Markdown links, and 0 symlinks in the published version.
- K3 release receipt: version `20260917-060125-001`, tree hash `3be60654d2bc62ea6bfa8ad80387bbd2037633349d3d317d4a1e39745590d695`, status `released`, verified `true`.
- Frozen mapped acceptance: `/Users/Hugh/Downloads/KD测试/task10-reader-final-acceptance-clean-2026-09-17.json`, status `pass`, 24/24 effective questions correct, 0 hard failures. This is a mapped machine acceptance sample, not a claim of human reader-quality closure for every page.
- Regression verification: `124 passed, 1 deselected` across Reader projection, K1/K2 navigation, publication, and Task9 acceptance/publish tests; `git diff --check` passed.

## 2026-09-17 — Provenance repair and CompanyBrain comparison

- Root cause of the reported Provenance defect: seed promotion injected the same machine-path paragraph into every page and left the old `## 来源` section beside it. That made page Provenance generic and visually unrelated to the current module.
- Repair: each page now has a page-local Provenance table built only from that page's Evidence citations (`source_path` plus exact line ranges). The old duplicate `## 来源` section is replaced; product `index.md` files are not transformed into topic pages.
- Provenance recheck: 99/99 Reader pages; missing source files `0`; invalid line ranges `0`; Provenance sources absent from that page's Evidence `0`; duplicated rows `0`.
- CompanyBrain remains the reference bar, not a correctness oracle. Current KD is stronger for this frozen 89-source slice on uniform frontmatter, page-type coverage, exact line-bound provenance, and clean K1/K2/K3 separation. It is not globally better: CompanyBrain has 838 Markdown pages, richer cross-product breadth, gbrain `[[wikilink]]` integration, and more mature hand-curated navigation/source-index conventions.
- Remaining quality gap: 40 of 99 KD Reader pages explicitly contain `原始资料未明确`; these are honest source gaps, not backfilled facts. The next improvement should be source coverage/semantic enrichment for those pages, not hiding the marker or importing unrelated CompanyBrain content.
- Latest clean release: version `20260917-061306-002`, tree hash `02a7e1d7e02c3e962a3693857179dddfd2b2854bf8a75c0cf210c128ba70e5e9`, status `released`. Latest mapped acceptance: `/Users/Hugh/Downloads/KD测试/task10-reader-final-acceptance-provenance-fixed-2026-09-17.json`, `pass`, 24/24.
