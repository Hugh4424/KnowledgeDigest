# 实现计划：K4 瘦身且不丢能力

- **Input**：`decision-log.md`、`specs/task10-slimming-without-capability-loss/spec.md`
- **Template version**：`plan-task.v4`

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `decision-log.md#删除与保留清单（file-level，build-plan 直接消费）` | 67 模块、21 配置、B0–B4 批次边界 | M 先读；B 每批前回查；P 复算回查 |
| `decision-log.md#验收指标冻结（FR-K4-1 口径唯一解释）` | 行数、入口闭包、配置引用唯一口径 | M 先读；B/P 绑定同一报告 |
| `spec.md#5. 功能需求` | FR-BASELINE/CAPABILITY/RETIREMENT/HANDOFF | M/S 主读；B 按 phase 回查 |
| `spec.md#11. 验收标准` | AC-K4-001…008 与失败条件 | M/S 主读；B 执行；P 汇总 |
| `plan.md#Phase P1–P6` | 工程批次、恢复、验证和回退 | B 按 phase 读；P 交接 |
| `tasks.md#Phase P1–P6` | RED/GREEN/FINAL 任务卡 | B 执行；P 只读执行事实 |

## Quick Read

- **Goal**：以固定基线和可复算报告保护 K1–K3，先恢复最小同批次幂等，再分批删除旧模块/脚本/21 个配置，最终复算得到物理行与代码行净下降、五条正式入口闭包无未处置模块、配置总量下降。
- **Non-goals**：不改 K1 语义编译、K2 导航、K3 发布通道和真实查询集；不清理 docs/specs/archive/apply；不修停摆流水线，不接管 synthesize；来源：D-001、D-002、D-003、D-004、D-005、NG-001…NG-013、DEF-K4-1…9。
- **Before**：67 个 src 模块、56,382 物理行；39 个模块不在五条正式命令闭包；config 76 文件/18,427,623 B；旧自证约 24,021 行；语义 compiler 有活 cache，但没有 K4 要求的同批次 checkpoint 绑定。
- **After**：B0 先把最小 checkpoint/resume 绑定到冻结 manifest 指纹并以第二次 provider 调用为 0；B1–B4 按清单删除并逐批验证/回退；当前 42 个候选耦合测试文件先逐项迁移或同步删除；K1–K3 活路径继续由 semantic_*、kb_accept、kb_publish 提供。
- **Main risk**：把静态不可达误判为运行时无用，或把删除批次与已有测试资产的活断言混在一起。
- **Next step**：执行 T001 基线/回归 RED 设计；任何删除前证据缺失都 STOP 回当前 task，不先删。

## Technical Context

### Global Constraints

- **Verified facts**：正式入口来自 `pyproject.toml` 五个 project.scripts；digest 闭包 19 模块/11,618 行；全入口不可达 39 模块/39,161 行；config 76 文件；21 个配置删除候选/3,341,698 B；9 个 archive-only 配置延期；旧自证不在 K3 活路径。
- **Language / runtime**：Python `>=3.11`；审计环境 Python 3.13.12、uv 0.10.11；测试使用 pytest>=8；build-plan 不执行测试。
- **Primary dependencies**：复用 Python 标准库、现有 `semantic_cache.ModelCache`、`semantic_compiler.compile_batch`、`semantic_audit.write_audit`、`semantic_page.render_pages`、K3 `kb_accept`/`kb_publish`；不新增依赖。
- **Storage / state**：正式语义批次写 output-parent 下的批次目录和 `_audit`；模型 cache 在 `cache/model-cache/entries.jsonl`；B0 新 checkpoint 必须绑定 `input_manifest_id`/manifest hash/source snapshot 与 topic plan，不保存凭据。
- **Testing**：pytest 聚焦 acceptance；真实 provider 运行只作为 build-code 证据，build-plan 不执行；既有 `test_task2a_reader_bundle` 外部 fixture 红灯是 DEF-K4-8 基线豁免。
- **Target environment**：本地 Python CLI、无前端；正常路径可离线使用 fake provider/cache fixture，真实 provider 缺失必须 blocked/not_released。
- **Scale / scope**：67 src 模块、39 删除候选；config 76 个平面 JSON 文件、21 删除候选；K4 新增只允许最小 checkpoint/resume 与 dedup regression test。
- **Unresolved facts**：静态 config/AST 审计未被运行时逐文件重放验证，交 build-code 按 DEF-K4-6 重读；五根闭包的模块计数存在包模块呈现口径差异，39 个候选仅证明“不在静态正式根闭包”，不能代替 pytest 安全性；当前 42 个测试文件仍 import B1/B2 候选，不能把“39 模块删除”误写成“测试无需处置”：build-code 必须逐文件迁移或同步删除并保留新回归；Stage Agent/review/reflection 当前质量事实可 unavailable，不能当 pass。

## Code Anchors

- **Verified anchors**：`src/knowledge_digest/semantic_compiler.py:compile_batch`, `_model_results`, `_attempt_id`; `semantic_cache.py:ModelCache.get_or_call`; `semantic_audit.py:write_audit`; `semantic_page.py:MAX_NARRATIVE_LINES/render_pages`; `semantic_cli.py:main`; `kb_accept.py` acceptance entry; `kb_publish.py:publish/rollback`.
- **Existing interfaces**：`compile_batch(new_dir, manifest_path, output_parent, topic_map_path, cache_root, provider, model_id, prompt_version, today, write_failure_after)` returns `BatchResult`; cache key uses model/prompt/topic/member fingerprint; audit records `source_snapshot`, run status, publish status, provider calls and blockers.
- **Read now**：decision deletion/config tables; semantic compiler/cache/audit/page; K3 acceptance/publish tests; current task7/task8/task9 acceptance tests.
- **Must read before task**：each deletion module and its owning test immediately before its batch; current config JSON and all inbound refs before B4; current test collection before final aggregate.
- **Context mode**：Full for B0/B1/B2 because cross-module deletion and K3 seam; Lite for B4 per-file config review.

### Reuse → Extend → New

| Capability | Decision | Existing anchor | Reason / removal condition |
| --- | --- | --- | --- |
| source identity/dedup | reuse | `semantic_audit._source_statuses` | already marks duplicate_alias and canonical source; add only direct regression test |
| 300-line pagination | reuse | `semantic_page.render_pages` / `MAX_NARRATIVE_LINES` | live behavior exists; no new paginator |
| failure/provenance audit | reuse | `semantic_audit.write_audit`, `kb_publish` gates | preserve fail-closed statuses and source_snapshot |
| provider result cache | extend | `semantic_cache.ModelCache.get_or_call` | add a narrow batch checkpoint ledger around existing cache; remove if no live consumer after B0 evidence |
| module/config slimming | reuse/delete | formal five-command closure and file-level manifest | deletion is the smallest route; no reconnection code |

## Solution Design

### Overview

P1 freezes an immutable baseline report and runs the pre-delete live behavior checks without changing production code. P2 adds a narrow checkpoint record for the semantic compile run: the checkpoint stores only the frozen manifest/source snapshot, topic-plan fingerprint, completed topic keys and cache/checkpoint status. On resume, changed manifest/source/topic inputs fail closed; completed keys reuse existing cache entries and do not call the provider again.

P3 deletes B1 old S1–S6 modules and then B2 old self-proof modules/tests, with a focused test and import/entry closure check after each batch. P4 deletes the B3 legacy script and B4’s 21 configs only after all code batches pass, then runs the same baseline metric script, K1–K3 aggregate, old-entry nonzero checks and a real `digest` run. No plan phase creates a second scheduler, provider or release gate.

### Module responsibilities

#### Baseline and deletion ledger

- **Responsibility**：produce the one before/after metric report and enforce the 67/67 disposition.
- **Consumes**：decision-log deletion/config manifests and current repository tree.
- **Produces**：task-local metric evidence and batch diff facts.
- **Must not decide**：must not expand reachability roots or delete deferred/provenance assets.

#### Live semantic compile checkpoint

- **Responsibility**：persist and validate minimal same-batch resume identity before provider work.
- **Consumes**：frozen manifest/source snapshot, topic-map version, existing cache keys and provider result state.
- **Produces**：checkpoint status and zero-provider-call resume evidence.
- **Must not decide**：must not implement batch sizing, budget scheduling, failure splitting or release.

#### Formal K1–K3 closure

- **Responsibility**：retain semantic pages/provenance, navigation, publish/rollback and query acceptance.
- **Consumes**：existing semantic batch/audit and K3 freeze/query inputs.
- **Produces**：same user-visible output and fail-closed publish/accept outcomes.
- **Must not decide**：must not retain legacy self-proof merely for historical replay.

### Interfaces, data, and lifecycle

- **Interfaces / schemas**：checkpoint is a versioned JSON object bound to `input_manifest_id`, manifest hash/source snapshot hash, topic-map hash, model/prompt version, completed topic keys, and cache fingerprint; invalid/mismatched state returns blocked/incomplete without provider calls.
- **Data flow / state**：baseline → pre-delete regression → checkpoint `pending`/`running`/`complete` or `blocked` → per-batch delete/verify → final metrics/aggregate. A failed deletion batch rolls back only that batch; material/decision files remain.
- **API contract**：no new public CLI. Reuse existing `digest`/`semantic_cli` invocation and existing `--manifest`, `--cache-root`, output-parent controls; checkpoint is internal task-local state.
- **UI / external code**：N/A — reason: task is non_ui and has no browser/page surface.
- **Fail-loud behavior**：manifest/source/topic/checkpoint mismatch, cache integrity failure, provider unavailable, new test failure, or K3 gate failure remains blocked/not_released and stops the next batch.

## UI Delivery Contract (仅 UI phase/task 使用)

- **UI applicability**：`non_ui`；N/A — reason: decision-log source fact is non_ui and no frontend files are in any phase.
- **Component action**：N/A — reason: non_ui.
- **Real consumer**：N/A — reason: no UI consumer.
- **State owner**：N/A — reason: no UI state.
- **Typed ViewModel**：N/A — reason: no UI view model.
- **CSS/token owner**：N/A — reason: no CSS/tokens.
- **Fixture / viewport**：N/A — reason: no browser surface.
- **Browser / a11y / performance**：N/A — reason: command/service tests only.
- **Screenshot handoff**：N/A — reason: no UI artifact.
- **Coverage limits**：does not cover browser rendering or frontend interaction.
- **N/A / unknown reason**：non_ui is explicitly recorded in decision-log.

### Design-gap handoff (不改变 Design.md 权威)

- **design_status**：`not_applicable` — reason: 当前任务明确 non_ui，未发起 UI 设计审批。
- **missing_items / reason**：[]；UI design is not applicable, not missing.
- **fallback_visual_basis**：N/A — reason: no UI.
- **constraints / assumptions**：CLI and file artifacts only; no visual rule is introduced.
- **rework_risk / human_confirmation**：N/A — reason: no UI design confirmation path.
- **current_material_ref / design_revision**：`specs/task10-slimming-without-capability-loss/spec.md`; `N/A — reason: no Design.md applies`.
- **visible_labels**：N/A — reason: no page or interaction labels.
- **preview_refs / fixture_refs / viewport_refs / screenshot_refs**：N/A — reason: no UI.
- **responsive / a11y**：N/A — reason: no UI.

## File Boundary

### NEW

- `scripts/task10_metrics.py`
- `quality/evidence/k4/final-aggregate.json`

### MODIFY

- `src/knowledge_digest/semantic_compiler.py`
- `src/knowledge_digest/semantic_cache.py`
- `tests/acceptance/test_task7_e2e.py`
- `tests/acceptance/test_task7_claims.py`
- `tests/acceptance/test_task7_pages.py`
- `tests/acceptance/test_task7_audit.py`
- `tests/acceptance/test_task8_entry_navigation.py`
- `tests/acceptance/test_task9_accept.py`
- `tests/acceptance/test_task9_publish.py`
- `tests/acceptance/test_task2_batch_recovery.py`
- `tests/acceptance/test_task5_publication_contract.py`
- `tests/acceptance/test_task5_projection.py`
- `tests/acceptance/test_task5_provider.py`
- `tests/acceptance/test_task5_m401_r_adapter.py`
- `tests/acceptance/test_task3_quality_release.py`
- `tests/acceptance/test_task5_compiler_formal_tree.py`
- `tests/acceptance/test_task5_contract.py`
- `tests/test_simple_digest.py`
- `scripts/legacy_digest_reference.py`
- `config/task4-companybrain-mapping-20260819-v1.json`
- `config/task4-companybrain-mapping-20260819-v2.json`
- `config/task4-companybrain-mapping-20260819-v4.json`
- `config/task4-companybrain-mapping-20260819-v5.json`
- `config/task4-companybrain-mapping-20260819-v7.json`
- `config/task4-companybrain-mapping-20260819-v9.json`
- `config/task4-companybrain-mapping-20260819-v10.json`
- `config/task4-reader-case-matrix-89-semantic-v4.json`
- `config/task4-reader-case-matrix-89-semantic-v5.json`
- `config/task4-reader-case-matrix-89-semantic-v6.json`
- `config/task4-reader-case-matrix-89-semantic-v7.json`
- `config/task5-companybrain-baseline-v1.json`
- `config/task4-reader-quality-88-diagnostic.v1.json`
- `config/task5-provider-contract-handshake-v1.json`
- `config/task5-provider-contract-handshake-v2.json`
- `config/task5-provider-semantic-output-v1.json`
- `config/task5-root-cause-evidence-v1.json`
- `config/task5-source-not-documented-contract-v1.json`
- `config/task5-source-digest-contract-v1.json`
- `config/task5-publication-layout-v1.json`
- `config/task5-reader-quality-v1.json`
- `src/knowledge_digest/agentmemory_store.py`
- `src/knowledge_digest/batch_run.py`
- `src/knowledge_digest/cli.py`
- `src/knowledge_digest/cluster.py`
- `src/knowledge_digest/draft.py`
- `src/knowledge_digest/embedding.py`
- `src/knowledge_digest/ingest.py`
- `src/knowledge_digest/jsonl.py`
- `src/knowledge_digest/navigation.py`
- `src/knowledge_digest/okf_smoke.py`
- `src/knowledge_digest/page_layout.py`
- `src/knowledge_digest/paths.py`
- `src/knowledge_digest/pipeline.py`
- `src/knowledge_digest/provenance.py`
- `src/knowledge_digest/providers.py`
- `src/knowledge_digest/publisher.py`
- `src/knowledge_digest/queues.py`
- `src/knowledge_digest/reader_bundle.py`
- `src/knowledge_digest/reader_frontmatter.py`
- `src/knowledge_digest/retrieve.py`
- `src/knowledge_digest/runtime_status.py`
- `src/knowledge_digest/task4_location_pilot.py`
- `src/knowledge_digest/topic_axis.py`
- `src/knowledge_digest/text_similarity.py`
- `src/knowledge_digest/writeback.py`
- `src/knowledge_digest/compiler.py`
- `src/knowledge_digest/companybrain_mapping.py`
- `src/knowledge_digest/companybrain_snapshot.py`
- `src/knowledge_digest/full_release.py`
- `src/knowledge_digest/m401_r_adapter.py`
- `src/knowledge_digest/quality.py`
- `src/knowledge_digest/quality_compare.py`
- `src/knowledge_digest/reader_compiler.py`
- `src/knowledge_digest/reader_quality.py`
- `src/knowledge_digest/task4_reader_quality.py`
- `src/knowledge_digest/task5_provider.py`
- `src/knowledge_digest/task5_quality_gate.py`
- `src/knowledge_digest/task5_runtime.py`
- `src/knowledge_digest/task5_semantic_model.py`
- `scripts/evaluate_reader_candidate.py`
- `scripts/task5_m401_r_adapter.py`
- `scripts/task4_reader_quality.py`

- `tests/acceptance/test_task5_full_run.py`
- `tests/acceptance/test_task5_quality_compare.py`
- `tests/acceptance/test_task5_quality_gate.py`
- `tests/acceptance/test_task5_source_semantic.py`



### READ-ONLY CONTEXT

- `tests/acceptance/test_task7_split.py` — read-only baseline context; no P1 write ownership.

### DO NOT TOUCH

- `src/knowledge_digest/semantic_page.py` — live 300-line pagination.
- `src/knowledge_digest/semantic_audit.py` — source/claim/page provenance and fail-closed audit.
- `src/knowledge_digest/semantic_cli.py` — formal digest CLI boundary.
- `src/knowledge_digest/kb_accept.py` — K3 query acceptance.
- `src/knowledge_digest/kb_publish.py` — K2 navigation gate and K3 publish/rollback.
- all `semantic_*` modules except the explicitly scoped checkpoint extension; `docs/**`, `specs/**`, `apply/**`, deferred configs and mapping provenance.

## Technical Decisions

### DEC-001 — Extend existing cache seam, do not build a scheduler

- **Problem**：same frozen batch rerun must not repeat provider calls.
- **Options**：reuse cache only; extend cache/compile with checkpoint identity; build a general batch scheduler.
- **Selected**：extend existing `ModelCache`/`compile_batch` seam with one bounded checkpoint identity and no new scheduler.
- **Reason**：cache already proves composite input identity; only run-level completed-key persistence is missing. Full scheduler is DEF-K4-7 and violates simplicity.
- **Consequence / risk**：checkpoint schema must reject stale/mixed state; it adds a small persistence surface.
- **Fallback**：on invalid checkpoint, stop with blocked/incomplete and require a new state path; do not call provider.
- **F10 real threat**：同一冻结批次重跑若绕过既有 cache identity，会重复 provider 调用/计费；这是 AC-K4-004 的直接风险。
- **F10 existing cover**：`ModelCache.get_or_call` 已覆盖 topic/member/model/prompt fingerprint，但没有 run-level checkpoint completion marker。
- **F10 bypassable**：任何调用方仍可用新 output-parent 或删除 checkpoint 绕过复用；规范要求同一状态路径并在 mismatch 时 fail-closed。
- **F10 maintenance cost**：一个受版本/manifest/topic/model/prompt 绑定的 JSON checkpoint 与两条回归断言；不引入 scheduler、worker 或新 CLI。
- **F10 disposition**：keep only the narrow extension; remove if build-code proves existing cache already satisfies the exact same-batch oracle.

### DEC-002 — Delete by formal command closure, not by historical imports

- **Problem**：AST graph contains dead subtrees whose tests/importers are historical.
- **Options**：retain all historical paths; reconnect them; delete exact B1–B4 manifest.
- **Selected**：delete exact manifest, preserve five pyproject roots and K1–K3 seam.
- **Reason**：D-005 and NG-011 prioritize net reduction; reconnecting dead code would game reachability.
- **Consequence / risk**：historical M401/M402 replay disappears; accepted as RISK-K4-003.
- **Fallback**：if a formal command/import closure or retained regression fails, revert only the active batch.
- **F10 disposition**：simplify/delete; no compatibility wrapper.

### DEC-003 — Treat existing red fixture as baseline exemption, not a new waiver

- **Problem**：Task2-A external fixture is already red and unavailable.
- **Options**：repair unrelated fixture; ignore all reds; pin exact baseline node and reject new failures.
- **Selected**：pin exact DEF-K4-8 node and compare final collection by node name.
- **Reason**：G3 permits only the known external gap; fixing it expands scope.
- **Consequence / risk**：full aggregate remains partially red; the difference is visible.
- **Fallback**：new failure outside the pinned set stops the batch and returns to the owning task.
- **F10 disposition**：reuse existing baseline-report mechanism.

## Test Strategy

Design only; build-plan does not execute commands. Every RED/GREEN pair uses the same executable command and oracle identity; command names below are the task-card authority.

| Target | Task | Role | gate_cmd / expected_exit | Oracle / evidence_path |
| --- | --- | --- | --- | --- |
| FR-BASELINE-001/002; AC-K4-001/002 | T001/T002 | RED/GREEN | `python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree` / 1 then 0 | ORACLE-METRICS / `quality/evidence/k4/t001.json`, `t002.json` |
| FR-CAPABILITY-001; AC-K4-003 | T003/T004 | RED/GREEN | `python -m pytest tests/acceptance/test_task7_pages.py tests/acceptance/test_task7_claims.py tests/acceptance/test_task7_e2e.py` / 1 then 0 | ORACLE-S6-LIVE; pre-existing live regression only / `quality/evidence/k4/t003.json`, `t004.json` |
| FR-CAPABILITY-002; AC-K4-004 | T005/T006 | RED/GREEN | `python -m pytest tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py -k checkpoint_resume` / 1 then 0 | ORACLE-CHECKPOINT / `quality/evidence/k4/t005.json`, `t006.json` |
| FR-RETIREMENT-001; AC-K4-005 | T007/T008 | RED/GREEN | `python -m pytest tests/acceptance/test_task7_audit.py -k b1_retirement_guard` / 1 then 0 | ORACLE-B1-CLOSURE / `quality/evidence/k4/t007.json`, `t008.json` |
| FR-RETIREMENT-002; AC-K4-007 | T009/T010 | RED/GREEN | `python -m pytest tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_compiler_formal_tree.py -k b2_legacy_retirement` / 1 then 0 | ORACLE-B2-LEGACY-OFF / `quality/evidence/k4/t009.json`, `t010.json` |
| FR-RETIREMENT-001; AC-K4-005 | T011/T012 | RED/GREEN | `python -m pytest tests/acceptance/test_task7_audit.py -k b3_legacy_entry_retirement` / 1 then 0 | ORACLE-LEGACY-OFF / `quality/evidence/k4/t011.json`, `t012.json` |
| FR-BASELINE-002; AC-K4-002 | T013/T014 | RED/GREEN | `python -m pytest tests/acceptance/test_task7_audit.py -k b4_config_guard` / 1 then 0 | ORACLE-CONFIG-PROOF / `quality/evidence/k4/t013.json`, `t014.json` |
| FR-HANDOFF-001/002; AC-K4-006/008 | T015 | N/A | `python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree` / 0 | ORACLE-FINAL-K4; current aggregate only / `quality/evidence/k4/final-aggregate.json` |

P1 is a read-only baseline/known-green capture; T003/T004 must not invent a production RED. If the pre-existing live suite is green, T003 records the baseline GREEN fact and T004 reuses it; the only new RED/GREEN behavior pair begins in P2.

## Source / FR / AC coverage index

| Source / decision | FR | AC | Phase / Task | Depends on | Exact files | Command / oracle |
| --- | --- | --- | --- | --- | --- | --- |
| R-018/D-001 | FR-BASELINE-001 | AC-K4-001 | P1/T001,T002 | none | `scripts/task10_metrics.py` | `python scripts/task10_metrics.py` / ORACLE-METRICS |
| R-020/D-003 | FR-BASELINE-002 | AC-K4-002 | P1/T001,T002 | T001 | `scripts/task10_metrics.py` | config audit / ORACLE-METRICS |
| R-017/D-002 | FR-CAPABILITY-001 | AC-K4-003 | P1/T003,T004 | T001 | `tests/acceptance/test_task7_pages.py` | pytest / ORACLE-S6-LIVE |
| R-021/D-002 | FR-CAPABILITY-002 | AC-K4-004 | P2/T005,T006 | T003 | `src/knowledge_digest/semantic_compiler.py` | pytest / ORACLE-CHECKPOINT |
| R-016/D-005 | FR-RETIREMENT-001 | AC-K4-005 | P3/P4/P5/T007–T012 | T006 | B1/B2/B3 files | exit checks / ORACLE-LEGACY-OFF |
| R-025/D-003 | FR-RETIREMENT-002 | AC-K4-007 | P4/T009,T010 | T008 | `tests/acceptance/test_task9_publish.py` | pytest / ORACLE-K123 |
| R-012/D-001 | FR-HANDOFF-001 | AC-K4-006/008 | P5/P6/T011–T015 | T010 | task-local evidence | aggregate / ORACLE-FAIL-LOUD |
| R-013/D-004 | FR-HANDOFF-002 | AC-K4-008 | P6/T015 | T014 | handoff evidence | aggregate / ORACLE-HANDOFF |

## Review Finding Disposition (build-plan repair pass)

| Finding theme | Disposition | Current repair / owner |
| --- | --- | --- |
| Baseline contradiction | actionable, repaired in material design | `decision-log.md` baseline `eee55492517bc86e3aad4838fe215bb23d84e8a4` is authoritative; every metric gate uses the full SHA; context packets must not override it. T001/T002. |
| Stale strategy/order table | actionable, repaired | this table now mirrors T001–T015 and six phases P1–P6; tasks.md gate commands are the executable authority. |
| T003/T004 artificial RED | actionable, constrained | P1 is read-only pre-delete capture; no invented failing assertion. New RED/GREEN behavior begins in P2/T005/T006. T003/T004 remain baseline capture cards and may record exit 0 as a baseline fact. |
| Dedup ownership | actionable, repaired | active duplicate-source regression belongs only to P2/T005/T006; P1/T003/T004 cover existing pagination/claims/e2e only. |
| Checkpoint contract | actionable, required before build-code | B0 must define task-local checkpoint path under the semantic output batch directory, atomic temp+rename, discovery by frozen batch identity, and identity tuple: batch directory, input manifest id/hash/source snapshot, topic-map hash, model id, prompt version. Resume must reuse completed cache entries, mismatch must fail closed without provider call. T005/T006. |
| Real digest proof | actionable, required before deletion | T004/P1 must add a concrete real `digest` invocation receipt design; provider unavailable is a recorded unavailable/block, never pass. T015 final acceptance consumes that receipt. |
| Coupled tests | actionable, required before B1/B2 | P3/P4 must consume an authoritative 42-file inventory with imported symbol and migrate/delete/retain owner for every row. Static closure is not enough. |
| Config proof | actionable, required before B4 | T013/T014 `b4_config_guard` must compare all 21 path-level SHA-256 values and reference disposition, not only count/bytes. |
| Negative/rollback coverage | actionable, required | P3–P5 guards must cover stop/revert on failed deletion, provider unavailable, workspace drift, cancellation, and handoff fields; T015 aggregate requires the receipt schema. |
| Retained K1/K2/K3 tests | actionable, repaired | `test_task8_entry_navigation.py`, `test_task9_accept.py`, `test_task9_publish.py` are retained read-only regression consumers, not B2 deletion files. |
| Minimality budget | actionable, required | T006/T015 must enforce a numeric checkpoint-extension line budget and fail if the implementation exceeds it; exact budget remains a build-code measurement from the approved G1 guard, not an invented source requirement. |

### Concrete checkpoint lifecycle contract

- **Path**：`<output_parent>/<batch_dir>/_audit/checkpoint.v1.json`; write a temporary sibling then atomic rename; never persist credentials or provider raw output.
- **Discovery**：resume searches only the requested output parent for the exact frozen batch directory and validates the checkpoint identity tuple before reading completed keys.
- **First run**：write `pending` before model work, update completed topic keys after each successful cache/audit unit, finish `complete` only after audit manifest is durable.
- **Resume**：same identity resumes completed keys and requires `provider_calls == 0` for already completed keys; a distinct batch directory or any input/topic/model/prompt mismatch is a new run or fail-closed, never mixed reuse.
- **Failure**：interrupted/corrupt/mismatched checkpoint yields `blocked`/`incomplete` and no provider call; no full `batch_run` scheduler is introduced.

### Required pre-delete evidence chain

`baseline metrics/hash manifest → P2 checkpoint/dedup GREEN → real digest receipt (or authenticated unavailable) → retained K1/K2/K3 GREEN → coupled-test inventory disposition → B1/B2/B3/B4 guard receipts → final metrics/negative-path aggregate`.
Each deletion card must consume the previous receipt's snapshot/material identity and stop on mismatch; P5 B3 and B4 keep separate rollback scopes even though they share a Phase.

## Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| Formal CLI roots | `pyproject.toml` | no change | T007,T008 | five roots are frozen by D-005 |
| K1/K2/K3 contracts | `src/knowledge_digest/semantic_*.py`,`src/knowledge_digest/kb_accept.py`,`src/knowledge_digest/kb_publish.py` | no change except narrow checkpoint seam | T005,T006 | preserve live behavior |
| Deferred docs/archive | `docs/**`,`specs/archive/**`,`apply/**` | no change | none | NG-012/DEF-K4-1/4 |
| Config provenance | 18 config provenance files | no change | T011,T012 | DEF-K4-4 |

## Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"constitution-checklist.md","hash":"91c72a0db7a77da84369d0aada56105612c21def13761f6aa7db387b8922f434","id":"CONSTITUTION","version":"current","clause_count":22}`
- **F1**：reuse semantic/K3 boundaries; no new coordinator; `DEC-001`.
- **F2**：checkpoint is a narrow JSON contract; no public interface expansion; `DEC-001`.
- **F3**：four current materials remain authoritative; no code task edits them; D-001.
- **F4**：review is advisory and unavailable remains visible; current build-spec/build-plan facts.
- **F5**：no new gate; existing per-batch tests only; DEC-002.
- **F6**：all execution facts go through WorkflowHub task evidence; no local status ledger.
- **F7**：no new daily confirmation; irreversible operations still require WorkflowHub authorization.
- **F8**：reuse ModelCache and formal CLI; do not build a scheduler.
- **F9**：blocked/not_released and baseline red are distinct; AC-K4-008/DEF-K4-8.
- **F10**：checkpoint extension has one exact user-visible failure it prevents and a removal condition; DEC-001.
- **F11**：no extra control plane; unavailable provider/review remains diagnostic.
- **Q1**：quality facts never authorize deletion; GREEN tests and evidence do.
- **Q2**：plan/task structure is separate from code completion and irreversible authorization.
- **Q3**：independent review is attempted; unavailable is not pass.
- **S1**：reuse Python/pytest/current semantic cache.
- **S2**：extend only existing cache seam.
- **S3**：read current anchors immediately before each deletion.
- **S4**：no new standalone skill.
- **S5**：subagents supply audit conclusions only; no second authority.
- **S6**：reuse mature WorkflowHub/pytest patterns.
- **S7**：one plan phase per real deletion/verification boundary.
- **S8**：plan remains portable: exact files, commands, oracle, no host assumptions.

## Rollback and Recovery

- **Global recovery rule**：只回滚当前实现/删除批次，保留四份材料、review facts、unavailable facts 和失败 receipt；不执行 commit/merge/release。
- **Irreversible boundaries**：删除文件、配置、commit、push、merge、archive、cleanup 均需要后续 WorkflowHub 授权；build-plan 不执行。
- **Recovery owner**：build-code executor；失败时恢复当前 batch 的 worktree、记录 snapshot/material hashes、回到 owning task，不能继续下一批。

### Engineering Risk Handoff

- **PLAN-RISK-001**：静态不可达或测试迁移清单遗漏动态消费者。
  - **Affected IDs**：R-009/R-017/R-019/R-025; FR-BASELINE-001/002, FR-CAPABILITY-001, FR-RETIREMENT-001/002; T007–T015。
  - **Trigger**：formal command/import closure、coupled-test inventory、retained K1/K2/K3 regression 或 config reference audit 发现新消费者。
  - **Consequence**：digest/accept/publish 行为回退、回归证据不完整或误删活配置。
  - **Mitigation or STOP**：停止当前 batch，恢复 batch，保留失败 receipt；不得扩展 roots 或改方向。
  - **Handling Stage**：build-code / verify-code。
  - **Verification**：ORACLE-B1-CLOSURE、ORACLE-B2-LEGACY-OFF、ORACLE-K123、ORACLE-CONFIG-PROOF、ORACLE-FINAL-K4。

## Implementation Order

P1 baseline inventory → P2 minimal checkpoint/dedup → P3 B1 coupled-test disposition and deletion → P4 B2 self-proof deletion → P5 B3 legacy retirement plus B4 exact config deletion → P6 final aggregate/handoff. The order is serial because each deletion consumes the prior snapshot, receipt chain and rollback boundary.

## Dependencies and Parallelism

- **Dependencies**：T001→T002→T003→T004→T005→T006→T007→T008→T009→T010→T011→T012→T013→T014→T015。
- **Parallel work**：仅允许 read-only inventory/research in parallel with design; no implementation/deletion card overlaps files in the same phase.
- **External dependencies**：Python/pytest/uv and local worktree; provider/review/Stage Agent absence remains unavailable, not pass.

## Requirement and Verification Traceability

| Source / decision | FR | AC | Phase / Task | Depends on | Exact files | Command / oracle |
| --- | --- | --- | --- | --- | --- | --- |
| R-018/D-001 | FR-BASELINE-001 | AC-K4-001 | P1/T001,T002 | none | `scripts/task10_metrics.py` | metrics/full baseline / ORACLE-METRICS |
| R-020/D-003 | FR-BASELINE-002 | AC-K4-002 | P1/T001,T002; P5/T013,T014 | T001 | metrics + `tests/acceptance/test_task7_audit.py` | per-file config proof / ORACLE-CONFIG-PROOF |
| R-017/D-002 | FR-CAPABILITY-001 | AC-K4-003 | P1/T003,T004; P2/T005,T006 | T002 | retained Task7 tests + semantic compiler/cache seam | live digest receipt / ORACLE-S6-LIVE |
| R-021/D-002 | FR-CAPABILITY-002 | AC-K4-004 | P2/T005,T006 | T004 | semantic compiler/cache + Task7 checkpoint/dedup tests | two identical runs / ORACLE-CHECKPOINT |
| R-016/D-005 | FR-RETIREMENT-001 | AC-K4-005 | P3/P4/P5/T007–T012 | T006 | B1/B2/B3 files and coupled inventory | exit/import guards / ORACLE-LEGACY-OFF |
| R-025/D-003 | FR-RETIREMENT-002 | AC-K4-007 | P4/T009,T010; P6/T015 | T008 | retained Task7/Task8/Task9 acceptance tests | K1/K2/K3 aggregate / ORACLE-K123 |
| R-012/D-001 | FR-HANDOFF-001 | AC-K4-006 | P3–P6/T007–T015 | prior receipt chain | batch receipts | stop/revert/handoff / ORACLE-FAIL-LOUD |
| R-013/D-004 | FR-HANDOFF-002 | AC-K4-008 | P6/T015 | T014 | final aggregate evidence | negative-path matrix / ORACLE-FINAL-K4 |

## Phase P1 — Baseline and pre-delete behavior

### Goal

Freeze the before-state metric report and prove current live capability tests are the deletion precondition.

### Files

- **NEW**：`scripts/task10_metrics.py`
- **MODIFY**：`tests/acceptance/test_task7_pages.py`, `tests/acceptance/test_task7_claims.py`, `tests/acceptance/test_task7_e2e.py`
- **READ-ONLY CONSUMER**：`tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_split.py`
- **DO NOT TOUCH**：`src/knowledge_digest/semantic_page.py`, `semantic_audit.py`, `semantic_cli.py`, `kb_accept.py`, `kb_publish.py`

### Tasks

- `T001` owns `scripts/task10_metrics.py`; `T002` owns the same metric oracle GREEN; `T003` owns `tests/acceptance/test_task7_pages.py`, `tests/acceptance/test_task7_claims.py`, `tests/acceptance/test_task7_e2e.py` RED; `T004` owns those test files GREEN.

### Verify

`python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree` and focused pytest; RED is required before implementation, GREEN is required before P2.

### Knowledge

The audit numbers are read-only facts; code/build-code must recalculate them and distinguish existing DEF-K4-8 failures.

### STOP

If baseline cannot be regenerated, a live test is missing, or a new failure appears, return to plan/task owner before deletion.

### Done

Only build-code can fill execution facts; at planning time all tasks remain pending and no command has been executed.

### Risks and rollback

Static audit may miss runtime consumers; retain all DO NOT TOUCH anchors and revert only P1 changes.

## Phase P2 — Minimal checkpoint and dedup guard

### Goal

Make same frozen batch rerun reuse completed work without a provider call and pin live duplicate-source behavior.

### Files

- **NEW**：N/A — reason: checkpoint regression is added to the existing Task7 semantic E2E asset.
- **MODIFY**：`src/knowledge_digest/semantic_compiler.py`, `src/knowledge_digest/semantic_cache.py`, `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`
- **DO NOT TOUCH**：`src/knowledge_digest/semantic_page.py`, `src/knowledge_digest/semantic_audit.py`

### Tasks

- `T005` owns the new checkpoint RED cases in `tests/acceptance/test_task7_e2e.py` and the active dedup RED case in `tests/acceptance/test_task7_audit.py`; `T006` owns the same test files plus the minimal `semantic_compiler.py`/`semantic_cache.py` GREEN implementation.

### Verify

`python -m pytest tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py -k checkpoint_resume`; second identical run must report zero provider calls and same frozen manifest/topic fingerprints.

### Knowledge

This phase is intentionally not full batching; DEF-K4-7 remains open.

### STOP

If implementation needs batch sizing, budget scheduling, split recovery, new CLI flags, or semantic output changes, stop and return to make-decision.

### Done

No execution claim in build-plan; GREEN will be populated by build-code.

### Risks and rollback

A stale checkpoint could reuse wrong results; mismatched manifest/source/topic/model/prompt identities must fail closed.

## Phase P3 — Delete B1 live-disconnected historical modules

### Goal

Delete only B1 modules proven outside all five formal command closures, while enumerating and migrating/synchronizing every coupled test file before the batch is considered safe; preserve semantic/K3 modules.

### Files

- **NEW**：`tests/acceptance/test_task7_audit.py` — guard cases are authored before B1 deletion
- **MODIFY**：`src/knowledge_digest/agentmemory_store.py`, `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/cli.py`, `src/knowledge_digest/cluster.py`, `src/knowledge_digest/draft.py`, `src/knowledge_digest/embedding.py`, `src/knowledge_digest/ingest.py`, `src/knowledge_digest/jsonl.py`, `src/knowledge_digest/navigation.py`, `src/knowledge_digest/okf_smoke.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/paths.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/provenance.py`, `src/knowledge_digest/providers.py`, `src/knowledge_digest/publisher.py`, `src/knowledge_digest/queues.py`, `src/knowledge_digest/reader_bundle.py`, `src/knowledge_digest/reader_frontmatter.py`, `src/knowledge_digest/retrieve.py`, `src/knowledge_digest/runtime_status.py`, `src/knowledge_digest/task4_location_pilot.py`, `src/knowledge_digest/topic_axis.py`, `src/knowledge_digest/text_similarity.py`, `src/knowledge_digest/writeback.py`, `tests/acceptance/test_task2_batch_recovery.py`
- **DO NOT TOUCH**：`src/knowledge_digest/semantic_*.py`, `src/knowledge_digest/simple_cli.py`, `src/knowledge_digest/kb_accept.py`, `src/knowledge_digest/kb_publish.py`

### Tasks

- `T007` owns B1 deletion files and focused import/closure RED; `T008` owns B1 deletion files and GREEN verification.

### Verify

Run the B1 retirement guard in `tests/acceptance/test_task7_audit.py` and import closure; every one of the 42 current test files importing B1/B2 candidates is either migrated to a retained semantic/K3 assertion or synchronously deleted. Then run focused K1/K2/K3 tests; any new failure reverts B1.

### Knowledge

B1 must be applied only after P1/P2 GREEN. `reader_compiler` and `reader_quality` belong to B2, not B1.

### STOP

If any formal command imports a B1 module or any retained behavior changes, return to D-002/plan before deleting.

### Done

Pending; build-code owns actual deletion and evidence.

### Deletion proofs

- **B1/B2 module proof**：current decision-log reachability audit is the input proof; build-code must re-run formal five-root closure and coupled-test inventory immediately before each deletion batch. Static closure alone is not a pass.
- **B3 script proof**：the legacy entry and each coupled old self-proof script is enumerated in P5; build-code must prove non-executability and no dangling formal root.
- **B4 config proof**：the exact 21 A-list paths and byte/hash total are frozen in decision-log; build-code must re-read each path and references before removal.
- **Deletion status**：not executed in build-plan; no deletion is authorized by this plan material alone.

### Risks and rollback

B1 deletes historical importers that may be reached dynamically; import tracing and tests are mandatory.

## Phase P4 — Delete B2 self-proof cluster

### Goal

Remove compiler/self-proof/task5/task4 quality modules and tests after B1 no longer imports them, with explicit disposition for every coupled historical test/script.

### Files

- **NEW**：N/A — reason: deletion only
- **MODIFY**：`src/knowledge_digest/compiler.py`, `src/knowledge_digest/companybrain_mapping.py`, `src/knowledge_digest/companybrain_snapshot.py`, `src/knowledge_digest/full_release.py`, `src/knowledge_digest/m401_r_adapter.py`, `src/knowledge_digest/quality.py`, `src/knowledge_digest/quality_compare.py`, `src/knowledge_digest/reader_compiler.py`, `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/task4_reader_quality.py`, `src/knowledge_digest/task5_provider.py`, `src/knowledge_digest/task5_quality_gate.py`, `src/knowledge_digest/task5_runtime.py`, `src/knowledge_digest/task5_semantic_model.py`, `tests/acceptance/test_task5_publication_contract.py`, `tests/acceptance/test_task5_compiler_formal_tree.py`, `tests/acceptance/test_task5_contract.py`, `tests/acceptance/test_task5_projection.py`, `tests/acceptance/test_task5_provider.py`, `tests/acceptance/test_task5_m401_r_adapter.py`, `tests/acceptance/test_task3_quality_release.py`, `tests/test_simple_digest.py`, `tests/acceptance/test_task8_entry_navigation.py`, `tests/acceptance/test_task9_accept.py`, `tests/acceptance/test_task9_publish.py`, `tests/acceptance/test_task5_full_run.py`, `tests/acceptance/test_task5_quality_compare.py`, `tests/acceptance/test_task5_quality_gate.py`, `tests/acceptance/test_task5_source_semantic.py`
- **DO NOT TOUCH**：`src/knowledge_digest/semantic_*.py`, `src/knowledge_digest/kb_accept.py`, `src/knowledge_digest/kb_publish.py`; K3 tests except explicitly dead projections.

### Tasks

- `T009` owns B2 deletion files plus sync deletion of old-only test assets (`test_task5_projection.py`, `test_task5_provider.py`, `test_task5_m401_r_adapter.py`, `test_task3_quality_release.py`) and route-ledger cases; `T010` owns active assertion migration/retention and K1–K3 GREEN verification.

### Verify

Run the B2 retirement guard in `tests/acceptance/test_task5_publication_contract.py`; old self-proof commands fail non-zero; `kb_accept`/`kb_publish` and task7/task8/task9 tests remain valid.

### Knowledge

`compiler.py` is deleted as a whole; `_route_ledger_projection` is not migrated because K3 does not read route-ledger output.

### STOP

If K3 imports compiler or a retained test requires a deleted symbol, stop and return to B2 disposition; do not add a compatibility wrapper.

### Done

Pending; no build-plan execution claim.

### Risks and rollback

Historical M401/M402 replay is intentionally lost under accepted RISK-K4-003.

## Phase P5 — Retire legacy entry and delete approved configs

### Goal

Delete `scripts/legacy_digest_reference.py` and exactly the 21 A-list configs only after B1/B2 regression evidence.

### Files

- **NEW**：N/A — reason: deletion only
- **MODIFY**：`tests/acceptance/test_task7_audit.py`, `scripts/legacy_digest_reference.py`, `scripts/evaluate_reader_candidate.py`, `scripts/task5_m401_r_adapter.py`, `scripts/task4_reader_quality.py`, `config/task4-companybrain-mapping-20260819-v1.json`, `config/task4-companybrain-mapping-20260819-v2.json`, `config/task4-companybrain-mapping-20260819-v4.json`, `config/task4-companybrain-mapping-20260819-v5.json`, `config/task4-companybrain-mapping-20260819-v7.json`, `config/task4-companybrain-mapping-20260819-v9.json`, `config/task4-companybrain-mapping-20260819-v10.json`, `config/task4-reader-case-matrix-89-semantic-v4.json`, `config/task4-reader-case-matrix-89-semantic-v5.json`, `config/task4-reader-case-matrix-89-semantic-v6.json`, `config/task4-reader-case-matrix-89-semantic-v7.json`, `config/task5-companybrain-baseline-v1.json`, `config/task4-reader-quality-88-diagnostic.v1.json`, `config/task5-provider-contract-handshake-v1.json`, `config/task5-provider-contract-handshake-v2.json`, `config/task5-provider-semantic-output-v1.json`, `config/task5-root-cause-evidence-v1.json`, `config/task5-source-not-documented-contract-v1.json`, `config/task5-source-digest-contract-v1.json`, `config/task5-publication-layout-v1.json`, `config/task5-reader-quality-v1.json`
- **DO NOT TOUCH**：config provenance/active inputs, `config/task9-comparison-mapping.v1.json`, `docs/**`, `specs/archive/**`, `apply/**`

### Config ownership

- **config ownership: T013/T014**：each card owns the complete 21-path A-list guard/deletion proof; no path is deleted outside these paired cards.

### Tasks

- `T011` owns legacy entry retirement RED and coupled old-script/test disposition; `T012` owns legacy entry retirement GREEN; `T013` owns exact 21-config deletion RED/guard; `T014` owns config deletion GREEN and final pre-aggregate verification.

### Verify

Run the exact config retirement guard in `tests/acceptance/test_task7_audit.py`, file-level config ref audit, old entry non-zero check, then final metric/K1–K3 aggregate. Any uncertainty defers rather than deletes.

### Knowledge

Config list and byte total are from read-only audit and must be rechecked before deletion; 9 archive-only files remain deferred.

### STOP

If any A-list config is a live input/provenance dependency or any new aggregate failure appears, revert P5 and preserve it as deferred.

### Done

Pending; build-code fills actual files, exit codes, evidence and review facts.

### Risks and rollback

Deletion is reversible only while uncommitted; no commit/merge/cleanup occurs in this task stage.

## Phase P6 — Final aggregate and handoff

### Goal

Produce one final current-snapshot metric/K1–K3/old-entry/real-digest aggregate and an honest handoff.

### Files

- **NEW**：`quality/evidence/k4/final-aggregate.json` — task-local evidence output only
- **MODIFY**：N/A — reason: no source modification
- **DO NOT TOUCH**：all product source/config; aggregate writes task-local quality evidence only

### Tasks

- `T015`

### Verify

Final aggregate command is planned only; build-code/verify-code produce current evidence and distinguish DEF-K4-8 baseline red from new failures.

### Knowledge

Do not claim release/merge; K3 query set remains merge gate.

### STOP

Any missing current evidence, unknown deletion proof or unavailable provider keeps task incomplete.

### Done

Pending until build-code/verify-code; build-plan does not execute.

### Risks and rollback

No source rollback; return to the phase that produced the missing evidence.

## Final current-snapshot aggregate strategy

- **tier / method**：feature — current snapshot command aggregate; build-plan designs only.
- **scenarios**：AC-K4-001…008, K1/K2/K3 seam checks, old-entry non-executability, known DEF-K4-8 baseline red, provider/review/unavailable states.
- **command**：`python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree`
- **expected exit**：0 only when current evidence is complete; unavailable/incomplete remains non-pass.
- **oracle**：ORACLE-FINAL-K4 — current metrics, retained behavior, retirement, rollback/STOP and handoff facts.
- **evidence_path**：`quality/evidence/k4/final-aggregate.json`
- **coverage limits**：does not authorize implementation, commit, merge, release, or substitute for verify-code/provider evidence.
- **STOP**：missing current evidence, unknown deletion proof, unavailable provider/review/reflection/handoff, or new regression.

## Coupled Test Inventory

The following 42 current test files were found importing B1/B2 candidates during the read-only audit. This is an execution input, not proof that each file is live production reachability. Before B1/B2, build-code must assign each row exactly one disposition: `migrate-to-retained`, `sync-delete-old-only`, or `retain-unchanged`, with imported symbols and a receipt.

| # | Current file | Required disposition owner |
| ---: | --- | --- |
| 1 | `tests/acceptance/test_architecture_optimization.py` | T007/T008 inventory |
| 2 | `tests/acceptance/test_mini_task_runtime_observability.py` | T007/T008 inventory |
| 3 | `tests/acceptance/test_phase0_digest.py` | T007/T008 inventory |
| 4 | `tests/acceptance/test_phase1_loss_prevention.py` | T007/T008 inventory |
| 5 | `tests/acceptance/test_phase25_llm.py` | T007/T008 inventory |
| 6 | `tests/acceptance/test_phase2_5_append_only_durability.py` | T007/T008 inventory |
| 7 | `tests/acceptance/test_phase2_5_concurrency_lock.py` | T007/T008 inventory |
| 8 | `tests/acceptance/test_phase2_rethink.py` | T007/T008 inventory |
| 9 | `tests/acceptance/test_phase3_agentmemory.py` | T007/T008 inventory |
| 10 | `tests/acceptance/test_phase4_embedding_runtime.py` | T007/T008 inventory |
| 11 | `tests/acceptance/test_reader_compiler.py` | T009/T010 inventory |
| 12 | `tests/acceptance/test_task0_runtime_audit.py` | T007/T008 inventory |
| 13 | `tests/acceptance/test_task0_writeback_gate.py` | T007/T008 inventory |
| 14 | `tests/acceptance/test_task1_topic_axis.py` | T007/T008 inventory |
| 15 | `tests/acceptance/test_task2_batch_recovery.py` | T007/T008 inventory |
| 16 | `tests/acceptance/test_task2_corpus_regression.py` | T007/T008 inventory |
| 17 | `tests/acceptance/test_task2_publication.py` | T007/T008 inventory |
| 18 | `tests/acceptance/test_task2a_okf_smoke.py` | T007/T008 inventory |
| 19 | `tests/acceptance/test_task2a_reader_bundle.py` | T007/T008 inventory |
| 20 | `tests/acceptance/test_task2a_reader_frontmatter.py` | T007/T008 inventory |
| 21 | `tests/acceptance/test_task2b_body_compiler.py` | T009/T010 inventory |
| 22 | `tests/acceptance/test_task2c_reader_quality.py` | T009/T010 inventory |
| 23 | `tests/acceptance/test_task3_closeout.py` | T007/T008 inventory |
| 24 | `tests/acceptance/test_task3_projection.py` | T009/T010 inventory |
| 25 | `tests/acceptance/test_task3_quality_release.py` | T009/T010 inventory |
| 26 | `tests/acceptance/test_task3_semantic_compile.py` | T007/T008 inventory |
| 27 | `tests/acceptance/test_task4_companybrain_mapping.py` | T009/T010 inventory |
| 28 | `tests/acceptance/test_task4_full_compiler.py` | T009/T010 inventory |
| 29 | `tests/acceptance/test_task4_full_quality.py` | T009/T010 inventory |
| 30 | `tests/acceptance/test_task4_location_compiler.py` | T007/T008 inventory |
| 31 | `tests/acceptance/test_task5_compiler_formal_tree.py` | T009/T010 inventory |
| 32 | `tests/acceptance/test_task5_contract.py` | T009/T010 inventory |
| 33 | `tests/acceptance/test_task5_full_run.py` | T009/T010 inventory |
| 34 | `tests/acceptance/test_task5_m401_r_adapter.py` | T009/T010 inventory |
| 35 | `tests/acceptance/test_task5_projection.py` | T009/T010 inventory |
| 36 | `tests/acceptance/test_task5_provider.py` | T009/T010 inventory |
| 37 | `tests/acceptance/test_task5_publication_contract.py` | T009/T010 inventory |
| 38 | `tests/acceptance/test_task5_quality_compare.py` | T009/T010 inventory |
| 39 | `tests/acceptance/test_task5_quality_gate.py` | T009/T010 inventory |
| 40 | `tests/acceptance/test_task5_source_semantic.py` | T009/T010 inventory |
| 41 | `tests/test_simple_digest.py` | T009/T010 inventory |
| 42 | `tests/test_simple_providers.py` | T007/T008 inventory |

No row is treated as already migrated/deleted by this plan; the table is a pre-delete executable obligation.
