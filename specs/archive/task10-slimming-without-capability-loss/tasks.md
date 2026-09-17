# 任务清单：K4 瘦身且不丢能力

- **Input**：`decision-log.md`、`specs/task10-slimming-without-capability-loss/spec.md`、`specs/task10-slimming-without-capability-loss/plan.md`
- **Template version**：`plan-task.v4`

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `decision-log.md#删除与保留清单（file-level，build-plan 直接消费）` | 批次与处置权威 | M 先读；B 每批回查；P 汇总 |
| `spec.md#11. 验收标准` | AC 与失败条件 | M/S 主读；B 执行；P 汇总 |
| `plan.md#Phase P1–P6` | 工程边界、依赖、oracle、回退 | B 主读；P 交接 |
| `tasks.md#Phase P1–P6` | 执行卡与真实事实区 | B 执行；P 只写事实 |


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

#### T001 — RED: freeze baseline metrics and reachability/config inventory

- **ID**：T001
- **Phase**：Phase P1 — Baseline and pre-delete behavior
- **goal**：freeze baseline metrics and reachability/config inventory
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：none
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-BASELINE-001, FR-BASELINE-002
- **AC**：AC-K4-001, AC-K4-002
- **动作**：write a reproducible baseline assertion that initially fails because the K4 metrics script does not yet exist
- **精确文件**：`scripts/task10_metrics.py`
- **boundary**：files: `scripts/task10_metrics.py`; symbols/regions: only the named files and their existing test regions
- **输出**：ORACLE-METRICS design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree`
- **expected_exit**：1
- **oracle**：`ORACLE-METRICS {"pass":"baseline script reports frozen physical/code lines, root closure and config counts","reject":{"input":"missing scripts/task10_metrics.py or wrong baseline ref","expected_rejection":"non-zero or explicit metric mismatch","observation":"no baseline evidence is accepted"}}`
- **evidence_path**：`quality/evidence/k4/t001.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：a missing or wrong root set could make the baseline non-reproducible
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：记录缺失脚本的真实 RED；未伪造产品失败。
- **executed_commands**：`python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree` → exit 2（脚本不存在）。
- **evidence_refs**：[`quality/evidence/k4/t001.json`]
- **covered_ac**：AC-K4-001, AC-K4-002（RED 前置事实）
- **review_fact**：P1 phase review 已通过 WorkflowHub `review --action=record` 记录；`terminal_status=unavailable`，`error.code=PUBLIC_RESULT_INVALID`，canonical attempt=`quality/reviews/attempts/f7daaccc-c5cc-5a8e-a42a-c75d5420998b/attempt.json`，result_ref=null；未把 unavailable 写成通过。
- **completed_at**：2026-09-16T15:40:00Z
- **执行事实**：T001 已完成真实缺失脚本 RED；实际命令级 exit 为 2，不是计划文本中的 expected_exit 1，原因已保留。
#### T002 — GREEN: produce the frozen baseline and final-comparison metric tool design

- **ID**：T002
- **Phase**：Phase P1 — Baseline and pre-delete behavior
- **goal**：produce the frozen baseline and final-comparison metric tool design
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T001
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-BASELINE-001, FR-BASELINE-002
- **AC**：AC-K4-001, AC-K4-002
- **动作**：implement the one script that reports physical/code lines, five-root AST closure, config zero-reference count/bytes and anti-gaming counts
- **精确文件**：`scripts/task10_metrics.py`
- **boundary**：files: `scripts/task10_metrics.py`; symbols/regions: only the named files and their existing test regions
- **输出**：ORACLE-METRICS design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree`
- **expected_exit**：0
- **oracle**：`ORACLE-METRICS {"pass":"same baseline command exits 0 and emits reproducible metric JSON"}`
- **evidence_path**：`quality/evidence/k4/t002.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：static closure is not runtime safety; retain test coupling checks
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：新增 `scripts/task10_metrics.py`；实现 baseline/tree 同脚本复算、五根 AST 闭包、配置零引用和反刷分计数。
- **executed_commands**：`python -m py_compile scripts/task10_metrics.py` → exit 0；metrics gate → exit 0。
- **evidence_refs**：[`quality/evidence/k4/t002.json`]
- **covered_ac**：AC-K4-001, AC-K4-002
- **review_fact**：复用 P1 canonical phase review attempt `quality/reviews/attempts/f7daaccc-c5cc-5a8e-a42a-c75d5420998b/attempt.json`；`terminal_status=unavailable`，当前 metrics 仍是删除前快照。
- **completed_at**：2026-09-16T15:40:00Z
- **执行事实**：baseline 67 modules / 56,382 physical lines / 50,145 code lines / 5 roots / 39 unreachable / config 76 files / 18,427,623 B / approved A-list 21 files / 3,341,698 B；当前 tree 尚未删除，source and closure deltas remain 0。
#### T003 — N/A: capture live pagination, claims, failure and provenance baseline before deletion

- **ID**：T003
- **Phase**：Phase P1 — Baseline and pre-delete behavior
- **goal**：pin live pagination, claims, failure and provenance regression before deletion
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T002
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-CAPABILITY-001, FR-RETIREMENT-002
- **AC**：AC-K4-003, AC-K4-007
- **动作**：record the existing pre-delete live capability suite and baseline facts; do not invent a failing assertion or claim a production change in P1
- **精确文件**：`tests/acceptance/test_task7_pages.py`, `tests/acceptance/test_task7_claims.py`, `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_split.py`
- **boundary**：files: `tests/acceptance/test_task7_pages.py`, `tests/acceptance/test_task7_claims.py`, `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_split.py`; symbols/regions: existing live behavior and baseline guard tests only
- **输出**：ORACLE-S6-LIVE design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：N/A — non-behavior: baseline capture only
- **paired_task**：N/A — reason: P1 records an existing baseline, not an artificial RED
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_pages.py tests/acceptance/test_task7_claims.py tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py tests/acceptance/test_task7_split.py`
- **expected_exit**：0
- **oracle**：`ORACLE-S6-LIVE {"pass":"existing live capability baseline is captured; known DEF-K4-8 remains explicitly distinguished","reject":{"input":"new unexpected live regression","expected_rejection":"pytest non-zero outside pinned baseline exception","observation":"deletion is stopped"}}`
- **evidence_path**：`quality/evidence/k4/t003.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="Task7 live regression asset is intentionally shared with P2"; impact="one canonical before/after fixture prevents divergent evidence"; owner="build-code"; recheck="before P2"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：无生产代码变更；固定当前 S6/K1–K3 live regression baseline。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task7_pages.py tests/acceptance/test_task7_claims.py tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py tests/acceptance/test_task7_split.py` → exit 0，73 passed / 1 skipped / 74 collected。
- **evidence_refs**：[`quality/evidence/k4/t003.json`]
- **covered_ac**：AC-K4-003, AC-K4-007
- **review_fact**：复用 P1 canonical phase review attempt `quality/reviews/attempts/f7daaccc-c5cc-5a8e-a42a-c75d5420998b/attempt.json`；review unavailable；未执行 provider/release。
- **completed_at**：2026-09-16T15:40:00Z
- **执行事实**：裸 `python` 环境缺 pytest，保留为 unavailable；`uv run --frozen pytest` 完成基线捕获。
#### T004 — N/A: verify current live S6 and K1-K3 contracts before any deletion

- **ID**：T004
- **Phase**：Phase P1 — Baseline and pre-delete behavior
- **goal**：verify current live S6 and K1-K3 contracts before any deletion
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T003
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-CAPABILITY-001, FR-RETIREMENT-002
- **AC**：AC-K4-003, AC-K4-007
- **动作**：run the same focused route and record only current green/known-baseline facts
- **精确文件**：`tests/acceptance/test_task7_pages.py`, `tests/acceptance/test_task7_claims.py`, `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_split.py`
- **boundary**：files: `tests/acceptance/test_task7_pages.py`, `tests/acceptance/test_task7_claims.py`, `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_split.py`; symbols/regions: existing live behavior and baseline guard tests only
- **输出**：ORACLE-S6-LIVE design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：N/A — non-behavior: baseline verification only
- **paired_task**：N/A — reason: P1 records an existing baseline, not an implementation GREEN
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_pages.py tests/acceptance/test_task7_claims.py tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py tests/acceptance/test_task7_split.py`
- **expected_exit**：0
- **oracle**：`ORACLE-S6-LIVE {"pass":"focused live regression command exits 0 except explicitly pinned DEF-K4-8 baseline"}`
- **evidence_path**：`quality/evidence/k4/t004.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="Task7 live regression asset is intentionally shared with P2"; impact="one canonical before/after fixture prevents divergent evidence"; owner="build-code"; recheck="after P2 GREEN"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **real_digest_proof**：build-code must execute `uv run --frozen digest NEW_DIR --manifest config/task4-source-coverage-89-input.v1.json`, capture exit/stdout/stderr and output `_audit/run-result.json`; provider unavailable is blocked/unavailable, never pass.
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：无生产代码变更；复用 T003 focused route 验证当前 live contracts。
- **executed_commands**：同 T003 focused `uv run --frozen pytest` → exit 0，73 passed / 1 skipped / 74 collected。
- **evidence_refs**：[`quality/evidence/k4/t004.json`]
- **covered_ac**：AC-K4-003, AC-K4-007
- **review_fact**：复用 P1 canonical phase review attempt `quality/reviews/attempts/f7daaccc-c5cc-5a8e-a42a-c75d5420998b/attempt.json`；review unavailable；真实 digest/provider 仍待后续证据。
- **completed_at**：2026-09-16T15:40:00Z
- **执行事实**：P1 live baseline verified；没有删除动作，没有新回归。
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

#### T005 — RED: pin same-frozen-batch checkpoint and active semantic duplicate-source behavior
- **cross_phase_file_reason**：`tests/acceptance/test_task7_e2e.py`/`test_task7_audit.py` are intentionally shared with P1 because the active regression is added to existing Task7 assets before deletion.

- **ID**：T005
- **Phase**：Phase P2 — Minimal checkpoint and dedup guard
- **goal**：pin same-frozen-batch checkpoint and active semantic duplicate-source behavior
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T004
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-CAPABILITY-001, FR-CAPABILITY-002
- **AC**：AC-K4-003, AC-K4-004
- **动作**：add RED cases for identical frozen manifest rerun provider_calls=0 and duplicate sources sharing products/audit canonical alias
- **精确文件**：`tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`
- **boundary**：files: `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`; symbols/regions: only the named files and their existing test regions
- **输出**：ORACLE-CHECKPOINT design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py -k "checkpoint_resume or active_dedup"`
- **expected_exit**：1
- **oracle**：`ORACLE-CHECKPOINT {"pass":"checkpoint and active dedup cases expose missing K4 behavior","reject":{"input":"same frozen batch rerun or duplicate-source ledger","expected_rejection":"provider_calls repeats or canonical alias/products are absent","observation":"named RED test failure is recorded"}}`
- **evidence_path**：`quality/evidence/k4/t005.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="checkpoint/dedup tests reuse the existing Task7 asset"; impact="splitting fixtures would weaken same-batch comparison"; owner="build-code"; recheck="before and after P2"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：新增 `checkpoint_resume` 与 `active_dedup` 聚焦断言；未改生产代码。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py -k 'checkpoint_resume or active_dedup'` → exit 1，2 selected，1 failed / 1 passed；失败为 checkpoint 文件缺失，active dedup 断言通过。
- **evidence_refs**：[`quality/evidence/k4/t005.json`]
- **covered_ac**：AC-K4-003（active dedup baseline），AC-K4-004（checkpoint RED）
- **review_fact**：P2 phase review 已通过 WorkflowHub `review --action=record` 记录；`terminal_status=unavailable`，`error.code=RATE_LIMITED`（kimi/coding）与 `EVIDENCE_ANCHOR_INVALID`（codex/luna），canonical attempt=`quality/reviews/attempts/88255e16-b7a2-5647-aa18-e08ceaa2a141/attempt.json`，result_ref=null；未把 unavailable 写成通过。
- **completed_at**：2026-09-17T00:02:00+08:00
- **执行事实**：T005 真实 RED 已捕获；checkpoint 尚未实现，active duplicate alias 现有行为已被钉住。
#### T006 — GREEN: implement the minimum checkpoint/resume extension over existing cache identity
- **cross_phase_file_reason**：`tests/acceptance/test_task7_e2e.py`/`test_task7_audit.py` are intentionally shared with P1 because the active regression is added to existing Task7 assets before deletion.

- **ID**：T006
- **Phase**：Phase P2 — Minimal checkpoint and dedup guard
- **goal**：implement the minimum checkpoint/resume extension over existing cache identity
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T005
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-CAPABILITY-001, FR-CAPABILITY-002
- **AC**：AC-K4-003, AC-K4-004
- **动作**：extend compile/cache with only frozen manifest/source/topic/model/prompt identity; no batch scheduler or new CLI
- **精确文件**：`src/knowledge_digest/semantic_compiler.py`, `src/knowledge_digest/semantic_cache.py`, `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`
- **boundary**：files: `src/knowledge_digest/semantic_compiler.py`, `src/knowledge_digest/semantic_cache.py`, `tests/acceptance/test_task7_e2e.py`, `tests/acceptance/test_task7_audit.py`; symbols/regions: only the named files and their existing test regions
- **输出**：ORACLE-CHECKPOINT design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py -k "checkpoint_resume or active_dedup"`
- **expected_exit**：0
- **oracle**：`ORACLE-CHECKPOINT {"pass":"same frozen batch rerun records provider_calls=0 and dedup products/audit alias are stable"}`
- **evidence_path**：`quality/evidence/k4/t006.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="checkpoint/dedup tests reuse the existing Task7 asset"; impact="splitting fixtures would weaken same-batch comparison"; owner="build-code"; recheck="after P2 GREEN"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：`semantic_compiler.py` 增加原子 `checkpoint.v1.json` 身份/状态/完成 topic ledger 与内部 `resume_batch` seam，并拒绝位于调用方 `output_parent` 之外的 resume 目录；`semantic_cache.py` 增加 completed-topic 禁止 provider fallback；Task7 E2E/audit 增加 checkpoint、mismatch、corruption、resume 边界和 active dedup 行为覆盖。
- **executed_commands**：`python -m py_compile src/knowledge_digest/semantic_compiler.py src/knowledge_digest/semantic_cache.py` 与 `git diff --check` → exit 0；`uv run --frozen pytest tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py -k 'checkpoint_resume or active_dedup'` → exit 0，5 passed / 49 deselected / 54 collected；当前正式捕获 receipt=`quality/tests/build-code-p2-boundary-r3.json`。
- **evidence_refs**：[`quality/evidence/k4/t005.json`, `quality/evidence/k4/t006.json`, `quality/tests/build-code-p2-boundary-r3.json`]
- **covered_ac**：AC-K4-003、AC-K4-004
- **review_fact**：复用 P2 canonical phase review attempt `quality/reviews/attempts/88255e16-b7a2-5647-aa18-e08ceaa2a141/attempt.json`；`terminal_status=unavailable`，result_ref=null；未把 unavailable 写成通过。
- **completed_at**：2026-09-17T02:17:00+08:00
- **执行事实**：同一冻结批次复用已完成 topic/cache 时 provider_calls=0；checkpoint identity mismatch、损坏 JSON、以及位于 requested `output_parent` 外的 resume 目录均在 provider 前 fail-closed；现有 duplicate_alias canonical projection 保持稳定。
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

#### T007 — RED: guard B1 deletion against formal-entry and coupled-test imports
- **slice_markers**：`SIG-FILES` is intentional: B1 is an atomic deletion batch with 25 modules plus its coupled recovery test; every path is re-read immediately before deletion.
- **slice_reason**：splitting B1 would leave mixed imports and make rollback/closure evidence non-representative.

- **ID**：T007
- **Phase**：Phase P3 — Delete B1 live-disconnected historical modules
- **goal**：guard B1 deletion against formal-entry and coupled-test imports
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T006
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-RETIREMENT-001, FR-HANDOFF-001
- **AC**：AC-K4-005, AC-K4-006
- **动作**：record the expected failure of the pre-delete B1 closure/coupled-test disposition guard
- **精确文件**：`src/knowledge_digest/agentmemory_store.py`, `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/cli.py`, `src/knowledge_digest/cluster.py`, `src/knowledge_digest/draft.py`, `src/knowledge_digest/embedding.py`, `src/knowledge_digest/ingest.py`, `src/knowledge_digest/jsonl.py`, `src/knowledge_digest/navigation.py`, `src/knowledge_digest/okf_smoke.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/paths.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/provenance.py`, `src/knowledge_digest/providers.py`, `src/knowledge_digest/publisher.py`, `src/knowledge_digest/queues.py`, `src/knowledge_digest/reader_bundle.py`, `src/knowledge_digest/reader_frontmatter.py`, `src/knowledge_digest/retrieve.py`, `src/knowledge_digest/runtime_status.py`, `src/knowledge_digest/task4_location_pilot.py`, `src/knowledge_digest/topic_axis.py`, `src/knowledge_digest/text_similarity.py`, `src/knowledge_digest/writeback.py`, `tests/acceptance/test_task2_batch_recovery.py`, `tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_audit.py`
- **boundary**：files: `src/knowledge_digest/agentmemory_store.py`, `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/cli.py`, `src/knowledge_digest/cluster.py`, `src/knowledge_digest/draft.py`, `src/knowledge_digest/embedding.py`, `src/knowledge_digest/ingest.py`, `src/knowledge_digest/jsonl.py`, `src/knowledge_digest/navigation.py`, `src/knowledge_digest/okf_smoke.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/paths.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/provenance.py`, `src/knowledge_digest/providers.py`, `src/knowledge_digest/publisher.py`, `src/knowledge_digest/queues.py`, `src/knowledge_digest/reader_bundle.py`, `src/knowledge_digest/reader_frontmatter.py`, `src/knowledge_digest/retrieve.py`, `src/knowledge_digest/runtime_status.py`, `src/knowledge_digest/task4_location_pilot.py`, `src/knowledge_digest/topic_axis.py`, `src/knowledge_digest/text_similarity.py`, `src/knowledge_digest/writeback.py`, `tests/acceptance/test_task2_batch_recovery.py`; symbols/regions: only the named files and their existing test regions; guard region: `b1_retirement_guard`; guard region: `b1_retirement_guard`
- **输出**：ORACLE-B1-CLOSURE design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：RED
- **paired_task**：T008
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_audit.py -k b1_retirement_guard`
- **expected_exit**：1
- **oracle**：`ORACLE-B1-CLOSURE {"pass":"B1 guard exposes coupled historical imports before deletion","reject":{"input":"B1 candidates remain imported by unhandled test/script","expected_rejection":"guard exits non-zero and identifies owner","observation":"no deletion proceeds"}}`
- **evidence_path**：`quality/evidence/k4/t007.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="B1 is an atomic deletion batch with coupled recovery tests"; impact="splitting files would hide import and rollback coupling"; owner="build-code"; recheck="before B1 delete"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：在 `test_task7_audit.py` 增加 `b1_retirement_guard`，核对 25 个 B1 模块和旧分批恢复测试路径。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task7_audit.py -k b1_retirement_guard` → exit 1，1 selected / 1 failed；guard 列出 26 个待处置路径。
- **evidence_refs**：[`quality/evidence/k4/t007.json`]
- **covered_ac**：AC-K4-005、AC-K4-006
- **review_fact**：P3 phase review 已通过 WorkflowHub `review --action=record` 记录；`terminal_status=unavailable`，`error.code=REVIEW_WAIT_EXCEEDED`，provider_attempts=[]，canonical attempt=`quality/reviews/attempts/fe0239bf-d166-5f16-a255-936ab4326c9a/attempt.json`，result_ref=null；未把非终态写成通过。
- **completed_at**：2026-09-17T00:15:00+08:00
- **执行事实**：T007 真实 RED 已捕获；未在 guard 前删除任何 B1 文件。
#### T008 — GREEN: delete B1 historical modules after migrating or synchronizing coupled tests
- **slice_markers**：`SIG-FILES` is intentional: GREEN verifies the same atomic B1 batch after coupled test disposition.
- **slice_reason**：RED/GREEN must share the exact B1 boundary to prevent partial deletion.

- **ID**：T008
- **Phase**：Phase P3 — Delete B1 live-disconnected historical modules
- **goal**：delete B1 historical modules after migrating or synchronizing coupled tests
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T007
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-RETIREMENT-001, FR-HANDOFF-001
- **AC**：AC-K4-005, AC-K4-006
- **动作**：remove only B1 files and update/remove every coupled historical test asset while retaining active K1-K3 assertions
- **精确文件**：`src/knowledge_digest/agentmemory_store.py`, `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/cli.py`, `src/knowledge_digest/cluster.py`, `src/knowledge_digest/draft.py`, `src/knowledge_digest/embedding.py`, `src/knowledge_digest/ingest.py`, `src/knowledge_digest/jsonl.py`, `src/knowledge_digest/navigation.py`, `src/knowledge_digest/okf_smoke.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/paths.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/provenance.py`, `src/knowledge_digest/providers.py`, `src/knowledge_digest/publisher.py`, `src/knowledge_digest/queues.py`, `src/knowledge_digest/reader_bundle.py`, `src/knowledge_digest/reader_frontmatter.py`, `src/knowledge_digest/retrieve.py`, `src/knowledge_digest/runtime_status.py`, `src/knowledge_digest/task4_location_pilot.py`, `src/knowledge_digest/topic_axis.py`, `src/knowledge_digest/text_similarity.py`, `src/knowledge_digest/writeback.py`, `tests/acceptance/test_task2_batch_recovery.py`, `tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_audit.py`
- **boundary**：files: `src/knowledge_digest/agentmemory_store.py`, `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/cli.py`, `src/knowledge_digest/cluster.py`, `src/knowledge_digest/draft.py`, `src/knowledge_digest/embedding.py`, `src/knowledge_digest/ingest.py`, `src/knowledge_digest/jsonl.py`, `src/knowledge_digest/navigation.py`, `src/knowledge_digest/okf_smoke.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/paths.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/provenance.py`, `src/knowledge_digest/providers.py`, `src/knowledge_digest/publisher.py`, `src/knowledge_digest/queues.py`, `src/knowledge_digest/reader_bundle.py`, `src/knowledge_digest/reader_frontmatter.py`, `src/knowledge_digest/retrieve.py`, `src/knowledge_digest/runtime_status.py`, `src/knowledge_digest/task4_location_pilot.py`, `src/knowledge_digest/topic_axis.py`, `src/knowledge_digest/text_similarity.py`, `src/knowledge_digest/writeback.py`, `tests/acceptance/test_task2_batch_recovery.py`; symbols/regions: only the named files and their existing test regions; guard region: `b1_retirement_guard`; guard region: `b1_retirement_guard`
- **输出**：ORACLE-B1-CLOSURE design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：GREEN
- **paired_task**：T007
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_audit.py -k b1_retirement_guard`
- **expected_exit**：0
- **oracle**：`ORACLE-B1-CLOSURE {"pass":"B1 deletion and coupled test disposition pass import/K1-K3 checks"}`
- **evidence_path**：`quality/evidence/k4/t008.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="B1 GREEN verifies the same atomic deletion boundary"; impact="partial deletion would invalidate closure evidence"; owner="build-code"; recheck="after B1 GREEN"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：删除冻结 B1 的 25 个历史模块及 23 个 B1-only 旧测试资产；保留 Task7 活测试；将 legacy help 断言同步为非零并把 B2 混合测试延后到 P4。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task7_audit.py -k b1_retirement_guard` → exit 0，1 passed / 14 deselected；保留能力回归 `uv run --frozen pytest tests/acceptance/test_task7_pages.py tests/acceptance/test_task7_claims.py tests/acceptance/test_task7_e2e.py tests/acceptance/test_task7_audit.py tests/acceptance/test_task7_split.py` → exit 0，79 passed / 1 skipped。
- **evidence_refs**：[`quality/evidence/k4/t007.json`, `quality/evidence/k4/t008.json`]
- **covered_ac**：AC-K4-005、AC-K4-006
- **review_fact**：复用 P3 canonical phase review attempt `quality/reviews/attempts/fe0239bf-d166-5f16-a255-936ab4326c9a/attempt.json`；`terminal_status=unavailable`，result_ref=null；未把 unavailable 写成通过。
- **completed_at**：2026-09-17T00:20:00+08:00
- **执行事实**：B1 guard GREEN；正式五根入口无 B1 import；非正式脚本消费者留在 P5 处置，B2 混合测试留在 P4 处置。
### Verify

Run the B1 retirement guard in `tests/acceptance/test_task7_audit.py` and import closure; every one of the 42 current test files importing B1/B2 candidates is either migrated to a retained semantic/K3 assertion or synchronously deleted. Then run focused K1/K2/K3 tests; any new failure reverts B1.

### Knowledge

B1 must be applied only after P1/P2 GREEN. `reader_compiler` and `reader_quality` belong to B2, not B1.

### STOP

If any formal command imports a B1 module or any retained behavior changes, return to D-002/plan before deleting.

### Done

Pending; build-code owns actual deletion and evidence.

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

#### T009 — RED: guard B2 self-proof deletion and old-only test/script disposition
- **slice_markers**：`SIG-FILES` is intentional: B2 includes 14 self-proof modules and all explicitly coupled old-only/active assertion test assets.
- **slice_reason**：the test assets are the required migration/deletion safety boundary, not an unrelated aggregate.

- **ID**：T009
- **Phase**：Phase P4 — Delete B2 self-proof cluster
- **goal**：guard B2 self-proof deletion and old-only test/script disposition
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T008
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-RETIREMENT-001, FR-RETIREMENT-002
- **AC**：AC-K4-005, AC-K4-007
- **动作**：pin expected old self-proof/route-ledger failures before B2 removal
- **精确文件**：`src/knowledge_digest/compiler.py`, `src/knowledge_digest/companybrain_mapping.py`, `src/knowledge_digest/companybrain_snapshot.py`, `src/knowledge_digest/full_release.py`, `src/knowledge_digest/m401_r_adapter.py`, `src/knowledge_digest/quality.py`, `src/knowledge_digest/quality_compare.py`, `src/knowledge_digest/reader_compiler.py`, `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/task4_reader_quality.py`, `src/knowledge_digest/task5_provider.py`, `src/knowledge_digest/task5_quality_gate.py`, `src/knowledge_digest/task5_runtime.py`, `src/knowledge_digest/task5_semantic_model.py`, `tests/acceptance/test_task5_publication_contract.py`, `tests/acceptance/test_task5_compiler_formal_tree.py`, `tests/acceptance/test_task5_contract.py`, `tests/acceptance/test_task5_projection.py`, `tests/acceptance/test_task5_provider.py`, `tests/acceptance/test_task5_m401_r_adapter.py`, `tests/acceptance/test_task3_quality_release.py`, `tests/test_simple_digest.py`, `tests/acceptance/test_task8_entry_navigation.py`, `tests/acceptance/test_task9_accept.py`, `tests/acceptance/test_task9_publish.py`, `tests/acceptance/test_task5_full_run.py`, `tests/acceptance/test_task5_quality_compare.py`, `tests/acceptance/test_task5_quality_gate.py`, `tests/acceptance/test_task5_source_semantic.py`
- **boundary**：files: `src/knowledge_digest/compiler.py`, `src/knowledge_digest/companybrain_mapping.py`, `src/knowledge_digest/companybrain_snapshot.py`, `src/knowledge_digest/full_release.py`, `src/knowledge_digest/m401_r_adapter.py`, `src/knowledge_digest/quality.py`, `src/knowledge_digest/quality_compare.py`, `src/knowledge_digest/reader_compiler.py`, `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/task4_reader_quality.py`, `src/knowledge_digest/task5_provider.py`, `src/knowledge_digest/task5_quality_gate.py`, `src/knowledge_digest/task5_runtime.py`, `src/knowledge_digest/task5_semantic_model.py`, `tests/acceptance/test_task5_publication_contract.py`, `tests/acceptance/test_task5_compiler_formal_tree.py`, `tests/acceptance/test_task5_contract.py`, `tests/acceptance/test_task5_projection.py`, `tests/acceptance/test_task5_provider.py`, `tests/acceptance/test_task5_m401_r_adapter.py`, `tests/acceptance/test_task3_quality_release.py`, `tests/test_simple_digest.py`, `tests/acceptance/test_task8_entry_navigation.py`, `tests/acceptance/test_task9_accept.py`, `tests/acceptance/test_task9_publish.py`, `tests/acceptance/test_task5_full_run.py`, `tests/acceptance/test_task5_quality_compare.py`, `tests/acceptance/test_task5_quality_gate.py`, `tests/acceptance/test_task5_source_semantic.py`; symbols/regions: only the named files and their existing test regions
- **输出**：ORACLE-B2-LEGACY-OFF design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：RED
- **paired_task**：T010
- **gate_cmd**：`python -m pytest tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_compiler_formal_tree.py -k legacy_retirement`
- **expected_exit**：1
- **oracle**：`ORACLE-B2-LEGACY-OFF {"pass":"B2 guard exposes old self-proof/route-ledger dependencies","reject":{"input":"old-only test or live K3 seam is not dispositioned","expected_rejection":"guard exits non-zero","observation":"B2 deletion stops"}}`
- **evidence_path**：`quality/evidence/k4/t009.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="B2 includes self-proof modules and coupled historical tests"; impact="separating assets would hide deletion coupling"; owner="build-code"; recheck="before B2 delete"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：在 `test_task5_publication_contract.py` 增加 `legacy_retirement` guard；原计划命令因已删除的 B1 `publisher.py` 造成旧 compiler 测试收集失败，按实际边界改用 publication contract guard 做 RED。
- **executed_commands**：计划命令 exit 2（collection `ModuleNotFoundError: knowledge_digest.publisher`）；修正后的 `uv run --frozen pytest tests/acceptance/test_task5_publication_contract.py -k legacy_retirement` → exit 1，1 failed / 5 deselected。
- **evidence_refs**：[`quality/evidence/k4/t009.json`]
- **covered_ac**：AC-K4-005、AC-K4-007
- **review_fact**：P4 phase review 请求在 provider dispatch 前失败，`terminal_status=unavailable`，`error.code=MATERIAL_TOO_LARGE`，无 attempt/result；task-local fact=`quality/evidence/k4/p4-review-unavailable.json`，未把不可用写成通过。
- **completed_at**：2026-09-17T00:40:00+08:00
- **执行事实**：T009 真实 RED 已捕获；14 个 B2 模块与 19 个旧测试仍待同步删除，B1 导致的旧 compiler 收集失败已显式保留。
#### T010 — GREEN: delete B2 self-proof cluster and preserve K1-K3 acceptance paths
- **slice_markers**：`SIG-FILES` is intentional: GREEN verifies the same atomic B2 boundary and K1-K3 retained tests.
- **slice_reason**：separating retained assertions from the deleted cluster would hide import coupling.

- **ID**：T010
- **Phase**：Phase P4 — Delete B2 self-proof cluster
- **goal**：delete B2 self-proof cluster and preserve K1-K3 acceptance paths
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T009
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-RETIREMENT-001, FR-RETIREMENT-002
- **AC**：AC-K4-005, AC-K4-007
- **动作**：delete compiler/self-proof modules and only old-only tests; migrate/retain active assertions; old commands must be non-zero
- **精确文件**：`src/knowledge_digest/compiler.py`, `src/knowledge_digest/companybrain_mapping.py`, `src/knowledge_digest/companybrain_snapshot.py`, `src/knowledge_digest/full_release.py`, `src/knowledge_digest/m401_r_adapter.py`, `src/knowledge_digest/quality.py`, `src/knowledge_digest/quality_compare.py`, `src/knowledge_digest/reader_compiler.py`, `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/task4_reader_quality.py`, `src/knowledge_digest/task5_provider.py`, `src/knowledge_digest/task5_quality_gate.py`, `src/knowledge_digest/task5_runtime.py`, `src/knowledge_digest/task5_semantic_model.py`, `tests/acceptance/test_task5_publication_contract.py`, `tests/acceptance/test_task5_compiler_formal_tree.py`, `tests/acceptance/test_task5_contract.py`, `tests/acceptance/test_task5_projection.py`, `tests/acceptance/test_task5_provider.py`, `tests/acceptance/test_task5_m401_r_adapter.py`, `tests/acceptance/test_task3_quality_release.py`, `tests/test_simple_digest.py`, `tests/acceptance/test_task8_entry_navigation.py`, `tests/acceptance/test_task9_accept.py`, `tests/acceptance/test_task9_publish.py`, `tests/acceptance/test_task5_full_run.py`, `tests/acceptance/test_task5_quality_compare.py`, `tests/acceptance/test_task5_quality_gate.py`, `tests/acceptance/test_task5_source_semantic.py`
- **boundary**：files: `src/knowledge_digest/compiler.py`, `src/knowledge_digest/companybrain_mapping.py`, `src/knowledge_digest/companybrain_snapshot.py`, `src/knowledge_digest/full_release.py`, `src/knowledge_digest/m401_r_adapter.py`, `src/knowledge_digest/quality.py`, `src/knowledge_digest/quality_compare.py`, `src/knowledge_digest/reader_compiler.py`, `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/task4_reader_quality.py`, `src/knowledge_digest/task5_provider.py`, `src/knowledge_digest/task5_quality_gate.py`, `src/knowledge_digest/task5_runtime.py`, `src/knowledge_digest/task5_semantic_model.py`, `tests/acceptance/test_task5_publication_contract.py`, `tests/acceptance/test_task5_compiler_formal_tree.py`, `tests/acceptance/test_task5_contract.py`, `tests/acceptance/test_task5_projection.py`, `tests/acceptance/test_task5_provider.py`, `tests/acceptance/test_task5_m401_r_adapter.py`, `tests/acceptance/test_task3_quality_release.py`, `tests/test_simple_digest.py`, `tests/acceptance/test_task8_entry_navigation.py`, `tests/acceptance/test_task9_accept.py`, `tests/acceptance/test_task9_publish.py`, `tests/acceptance/test_task5_full_run.py`, `tests/acceptance/test_task5_quality_compare.py`, `tests/acceptance/test_task5_quality_gate.py`, `tests/acceptance/test_task5_source_semantic.py`; symbols/regions: only the named files and their existing test regions
- **输出**：ORACLE-B2-LEGACY-OFF design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：GREEN
- **paired_task**：T009
- **gate_cmd**：`python -m pytest tests/acceptance/test_task5_publication_contract.py tests/acceptance/test_task5_compiler_formal_tree.py -k legacy_retirement`
- **expected_exit**：0
- **oracle**：`ORACLE-B2-LEGACY-OFF {"pass":"B2 deletion leaves K1-K3 acceptance paths green and old commands non-zero"}`
- **evidence_path**：`quality/evidence/k4/t010.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="B2 GREEN verifies the same atomic deletion boundary"; impact="retained K1-K3 assertions must be checked with deletion"; owner="build-code"; recheck="after B2 GREEN"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：删除 14 个 B2 self-proof/quality 模块和 19 个 B2-only 测试；保留并同步 `test_task5_publication_contract.py` 的 current reader/simple_cli 合同；Task8/Task9 测试保留。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task5_publication_contract.py -k legacy_retirement` → exit 0，1 passed / 3 deselected；publication contract → 4 passed；K1/K2/K3 aggregate → exit 0，156 passed / 1 skipped。
- **evidence_refs**：[`quality/evidence/k4/t009.json`, `quality/evidence/k4/t010.json`]
- **covered_ac**：AC-K4-005、AC-K4-007
- **review_fact**：P4 phase review `MATERIAL_TOO_LARGE`，provider 未 dispatch，attempt/result 均 unavailable；task-local fact=`quality/evidence/k4/p4-review-unavailable.json`，未把不可用写成通过。
- **completed_at**：2026-09-17T00:48:00+08:00
- **执行事实**：B2 guard GREEN；src/tests 无 B2 import；K1/K2/K3 active acceptance 保留并通过。
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

#### T011 — RED: guard B3 legacy entry retirement and coupled scripts

- **ID**：T011
- **Phase**：Phase P5 — Retire legacy entry and delete approved configs
- **goal**：guard B3 legacy entry retirement and coupled scripts
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T010
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-RETIREMENT-001
- **AC**：AC-K4-005
- **动作**：pin the old entry retirement non-zero behavior and script dependency disposition
- **精确文件**：`tests/acceptance/test_task7_audit.py`, `tests/acceptance/test_task7_audit.py`, `scripts/legacy_digest_reference.py`, `scripts/evaluate_reader_candidate.py`, `scripts/task5_m401_r_adapter.py`, `scripts/task4_reader_quality.py`
- **boundary**：files: `tests/acceptance/test_task7_audit.py`, `scripts/legacy_digest_reference.py`, `scripts/evaluate_reader_candidate.py`, `scripts/task5_m401_r_adapter.py`, `scripts/task4_reader_quality.py`; symbols/regions: only the named files and their existing test regions; guard region: `b3_legacy_entry_retirement`
- **输出**：ORACLE-LEGACY-OFF design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：RED
- **paired_task**：T012
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_audit.py -k b3_legacy_entry_retirement`
- **expected_exit**：1
- **oracle**：`ORACLE-LEGACY-OFF {"pass":"legacy entry/script guard records planned retirement behavior","reject":{"input":"legacy script or coupled old path remains executable","expected_rejection":"retirement guard exits non-zero","observation":"B3 stops"}}`
- **evidence_path**：`quality/evidence/k4/t011.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="shared audit guard is intentionally reused across phases"; impact="one canonical retirement proof prevents divergent evidence"; owner="build-code"; recheck="before and after B3/B4"
- **risk note**：simple_cli legacy-flag messaging must be updated consistently
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：在 `test_task7_audit.py` 增加 `b3_legacy_entry_retirement` guard，确认四个 B3 脚本仍在；同步 current CLI/AGENTS 旧参数拒绝文案。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task7_audit.py -k b3_legacy_entry_retirement` → exit 1，1 failed / 15 deselected。
- **evidence_refs**：[`quality/evidence/k4/t011.json`]
- **covered_ac**：AC-K4-005
- **review_fact**：P5 phase review 请求在 provider dispatch 前失败，`terminal_status=unavailable`，`error.code=MATERIAL_TOO_LARGE`，无 attempt/result；task-local fact=`quality/evidence/k4/p5-review-unavailable.json`，未把不可用写成通过。
- **completed_at**：2026-09-17T01:05:00+08:00
- **执行事实**：四个 B3 script 路径均被 guard 识别，尚未删除。
#### T012 — GREEN: retire legacy entry and coupled old self-proof scripts

- **ID**：T012
- **Phase**：Phase P5 — Retire legacy entry and delete approved configs
- **goal**：retire legacy entry and coupled old self-proof scripts
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T011
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-RETIREMENT-001
- **AC**：AC-K4-005
- **动作**：delete B3 scripts and update/remove only historical references; retain five pyproject roots
- **精确文件**：`tests/acceptance/test_task7_audit.py`, `scripts/legacy_digest_reference.py`, `scripts/evaluate_reader_candidate.py`, `scripts/task5_m401_r_adapter.py`, `scripts/task4_reader_quality.py`
- **boundary**：files: `scripts/legacy_digest_reference.py`, `scripts/evaluate_reader_candidate.py`, `scripts/task5_m401_r_adapter.py`, `scripts/task4_reader_quality.py`; symbols/regions: only the named files and their existing test regions; guard region: `b3_legacy_entry_retirement`
- **输出**：ORACLE-LEGACY-OFF design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：GREEN
- **paired_task**：T011
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_audit.py -k b3_legacy_entry_retirement`
- **expected_exit**：0
- **oracle**：`ORACLE-LEGACY-OFF {"pass":"legacy entry and coupled historical scripts are retired without dangling active roots"}`
- **evidence_path**：`quality/evidence/k4/t012.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="shared audit guard is intentionally reused across phases"; impact="one canonical retirement proof prevents divergent evidence"; owner="build-code"; recheck="before and after B3/B4"
- **risk note**：do not leave a dangling help path or claim old self-proof still runs
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：删除四个 B3 script；更新 `simple_cli`、`semantic_cli`、`AGENTS.md` 和 legacy refusal 测试，不再指向旧脚本。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task7_audit.py -k b3_legacy_entry_retirement` → exit 0，1 passed / 15 deselected。
- **evidence_refs**：[`quality/evidence/k4/t011.json`, `quality/evidence/k4/t012.json`]
- **covered_ac**：AC-K4-005
- **review_fact**：P5 phase review `MATERIAL_TOO_LARGE`，provider 未 dispatch，attempt/result 均 unavailable；task-local fact=`quality/evidence/k4/p5-review-unavailable.json`，T012 绿灯不等于 phase review 通过。
- **completed_at**：2026-09-17T01:20:00+08:00
- **执行事实**：B3 脚本路径已退役，当前 CLI 文案不再留下悬空入口。
#### T013 — RED: guard exact 21-config deletion against live/provenance references
- **slice_markers**：`SIG-FILES` is intentional: the A-list guard reads all 21 exact config files plus its guard test.
- **slice_reason**：per-file hash/reference proof must be one atomic deletion decision.

- **ID**：T013
- **Phase**：Phase P5 — Retire legacy entry and delete approved configs
- **goal**：guard exact 21-config deletion against live/provenance references
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T012
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-BASELINE-002, FR-HANDOFF-001
- **AC**：AC-K4-002, AC-K4-006
- **动作**：verify each A-list file and byte total before deletion; uncertainty produces RED/defer
- **精确文件**：`tests/acceptance/test_task7_audit.py`, `config/task4-companybrain-mapping-20260819-v1.json`, `config/task4-companybrain-mapping-20260819-v2.json`, `config/task4-companybrain-mapping-20260819-v4.json`, `config/task4-companybrain-mapping-20260819-v5.json`, `config/task4-companybrain-mapping-20260819-v7.json`, `config/task4-companybrain-mapping-20260819-v9.json`, `config/task4-companybrain-mapping-20260819-v10.json`, `config/task4-reader-case-matrix-89-semantic-v4.json`, `config/task4-reader-case-matrix-89-semantic-v5.json`, `config/task4-reader-case-matrix-89-semantic-v6.json`, `config/task4-reader-case-matrix-89-semantic-v7.json`, `config/task5-companybrain-baseline-v1.json`, `config/task4-reader-quality-88-diagnostic.v1.json`, `config/task5-provider-contract-handshake-v1.json`, `config/task5-provider-contract-handshake-v2.json`, `config/task5-provider-semantic-output-v1.json`, `config/task5-root-cause-evidence-v1.json`, `config/task5-source-not-documented-contract-v1.json`, `config/task5-source-digest-contract-v1.json`, `config/task5-publication-layout-v1.json`, `config/task5-reader-quality-v1.json`
- **boundary**：files: `tests/acceptance/test_task7_audit.py`, `config/task4-companybrain-mapping-20260819-v1.json`, `config/task4-companybrain-mapping-20260819-v2.json`, `config/task4-companybrain-mapping-20260819-v4.json`, `config/task4-companybrain-mapping-20260819-v5.json`, `config/task4-companybrain-mapping-20260819-v7.json`, `config/task4-companybrain-mapping-20260819-v9.json`, `config/task4-companybrain-mapping-20260819-v10.json`, `config/task4-reader-case-matrix-89-semantic-v4.json`, `config/task4-reader-case-matrix-89-semantic-v5.json`, `config/task4-reader-case-matrix-89-semantic-v6.json`, `config/task4-reader-case-matrix-89-semantic-v7.json`, `config/task5-companybrain-baseline-v1.json`, `config/task4-reader-quality-88-diagnostic.v1.json`, `config/task5-provider-contract-handshake-v1.json`, `config/task5-provider-contract-handshake-v2.json`, `config/task5-provider-semantic-output-v1.json`, `config/task5-root-cause-evidence-v1.json`, `config/task5-source-not-documented-contract-v1.json`, `config/task5-source-digest-contract-v1.json`, `config/task5-publication-layout-v1.json`, `config/task5-reader-quality-v1.json`; symbols/regions: `b4_config_guard` and exact A-list hash/reference assertions
- **输出**：ORACLE-CONFIG-PROOF design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：RED
- **paired_task**：T014
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_audit.py -k b4_config_guard`
- **expected_exit**：1
- **oracle**：`ORACLE-CONFIG-PROOF {"pass":"config guard identifies exact 21-file A-list and live/provenance references","reject":{"input":"A-list count/hash/reference mismatch","expected_rejection":"non-zero guard and deletion deferred","observation":"no config is removed"}}`
- **evidence_path**：`quality/evidence/k4/t013.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="exact A-list hash/reference proof is atomic"; impact="partial config deletion is prohibited"; owner="build-code"; recheck="before B4 delete"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：在 `test_task7_audit.py` 增加 `b4_config_guard`，按 21 路径逐文件记录 bytes/SHA-256，并检查 active/deferred config 保留。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task7_audit.py -k 'b3_legacy_entry_retirement or b4_config_guard'` → exit 1，B3 1 passed、B4 1 failed；B4 预删 21 文件 / 3,341,698 B。
- **evidence_refs**：[`quality/evidence/k4/t013.json`]
- **covered_ac**：AC-K4-002、AC-K4-006
- **review_fact**：复用 P5 task-local unavailable fact=`quality/evidence/k4/p5-review-unavailable.json`；无 attempt/result，未把不可用写成通过。
- **completed_at**：2026-09-17T01:12:00+08:00
- **执行事实**：T013 真实 RED 已捕获，逐文件 hash 在 guard failure 输出中保留。
#### T014 — GREEN: delete exactly the approved config A-list and verify retained assets
- **slice_markers**：`SIG-FILES` is intentional: GREEN verifies the same exact A-list boundary.
- **slice_reason**：no partial config deletion is permitted.

- **ID**：T014
- **Phase**：Phase P5 — Retire legacy entry and delete approved configs
- **goal**：delete exactly the approved config A-list and verify retained assets
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T013
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-BASELINE-002, FR-HANDOFF-001
- **AC**：AC-K4-002, AC-K4-006
- **动作**：remove exactly 21 A-list files after per-file reread and confirm deferred/active files remain
- **精确文件**：`tests/acceptance/test_task7_audit.py`, `config/task4-companybrain-mapping-20260819-v1.json`, `config/task4-companybrain-mapping-20260819-v2.json`, `config/task4-companybrain-mapping-20260819-v4.json`, `config/task4-companybrain-mapping-20260819-v5.json`, `config/task4-companybrain-mapping-20260819-v7.json`, `config/task4-companybrain-mapping-20260819-v9.json`, `config/task4-companybrain-mapping-20260819-v10.json`, `config/task4-reader-case-matrix-89-semantic-v4.json`, `config/task4-reader-case-matrix-89-semantic-v5.json`, `config/task4-reader-case-matrix-89-semantic-v6.json`, `config/task4-reader-case-matrix-89-semantic-v7.json`, `config/task5-companybrain-baseline-v1.json`, `config/task4-reader-quality-88-diagnostic.v1.json`, `config/task5-provider-contract-handshake-v1.json`, `config/task5-provider-contract-handshake-v2.json`, `config/task5-provider-semantic-output-v1.json`, `config/task5-root-cause-evidence-v1.json`, `config/task5-source-not-documented-contract-v1.json`, `config/task5-source-digest-contract-v1.json`, `config/task5-publication-layout-v1.json`, `config/task5-reader-quality-v1.json`
- **boundary**：files: `tests/acceptance/test_task7_audit.py`, `config/task4-companybrain-mapping-20260819-v1.json`, `config/task4-companybrain-mapping-20260819-v2.json`, `config/task4-companybrain-mapping-20260819-v4.json`, `config/task4-companybrain-mapping-20260819-v5.json`, `config/task4-companybrain-mapping-20260819-v7.json`, `config/task4-companybrain-mapping-20260819-v9.json`, `config/task4-companybrain-mapping-20260819-v10.json`, `config/task4-reader-case-matrix-89-semantic-v4.json`, `config/task4-reader-case-matrix-89-semantic-v5.json`, `config/task4-reader-case-matrix-89-semantic-v6.json`, `config/task4-reader-case-matrix-89-semantic-v7.json`, `config/task5-companybrain-baseline-v1.json`, `config/task4-reader-quality-88-diagnostic.v1.json`, `config/task5-provider-contract-handshake-v1.json`, `config/task5-provider-contract-handshake-v2.json`, `config/task5-provider-semantic-output-v1.json`, `config/task5-root-cause-evidence-v1.json`, `config/task5-source-not-documented-contract-v1.json`, `config/task5-source-digest-contract-v1.json`, `config/task5-publication-layout-v1.json`, `config/task5-reader-quality-v1.json`; symbols/regions: `b4_config_guard` and exact A-list hash/reference assertions
- **输出**：ORACLE-CONFIG-PROOF design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：GREEN
- **paired_task**：T013
- **gate_cmd**：`python -m pytest tests/acceptance/test_task7_audit.py -k b4_config_guard`
- **expected_exit**：0
- **oracle**：`ORACLE-CONFIG-PROOF {"pass":"exactly the approved 21 config files are removed and deferred/active files remain"}`
- **evidence_path**：`quality/evidence/k4/t014.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：slice-advisory: reason="B4 GREEN verifies the exact A-list boundary"; impact="no partial config deletion is permitted"; owner="build-code"; recheck="after B4 GREEN"
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **semantic_review_status**：unavailable
- **semantic_review_ref**：quality/reviews/current-build-plan-review.json
- **semantic_review_reason**：independent review dispatch/current result is unavailable; this is not pass evidence
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：删除恰好 21 个 B4 A-list 配置；保留 active/deferred 配置；复算指标与 K1/K2/K3 回归均通过。
- **executed_commands**：B3/B4 guards → exit 0，2 passed / 15 deselected；K1/K2/K3 aggregate → exit 0，162 passed / 1 skipped；metrics → exit 0，`final_predicates_satisfied=true`。
- **evidence_refs**：[`quality/evidence/k4/t013.json`, `quality/evidence/k4/t014.json`]
- **covered_ac**：AC-K4-002、AC-K4-006
- **review_fact**：P5 phase review `MATERIAL_TOO_LARGE`，provider 未 dispatch，attempt/result 均 unavailable；task-local fact=`quality/evidence/k4/p5-review-unavailable.json`，未把不可用写成通过。
- **completed_at**：2026-09-17T01:20:00+08:00
- **执行事实**：B4 exact list 已完成；21 files / 3,341,698 B removed；current config 55 files / 15,085,925 B。
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

#### T015 — N/A: run final aggregate and produce honest handoff evidence

- **ID**：T015
- **Phase**：Phase P6 — Final aggregate and handoff
- **goal**：run final aggregate and produce honest handoff evidence
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task10-slimming-without-capability-loss/spec.md","hash":"44a559da636f66889f94c8c5ebbd2afc78f28a552d7690bf835d5cdf566117b4","id":"K4-SPEC"},{"artifact_kind":"plan","ref":"specs/task10-slimming-without-capability-loss/plan.md","hash":"4714de00ca1e03ed87db8a696d68803e93ddaf80b3017217751fd8097d5fa350","id":"K4-PLAN"}]`
- **source_refs / decision_refs**：R-017/R-018/R-019/R-020/R-021/R-025 → D-001/D-002/D-003/D-005
- **输入**：accepted decision/spec and the owning phase boundary
- **依赖**：T014
- **并行**：否 — serial producer-before-consumer chain
- **FR**：FR-BASELINE-001, FR-BASELINE-002, FR-CAPABILITY-001, FR-CAPABILITY-002, FR-RETIREMENT-001, FR-RETIREMENT-002, FR-HANDOFF-001, FR-HANDOFF-002, FR-K4-001, FR-K4-002, FR-K4-003, FR-K4-004
- **AC**：AC-K4-001, AC-K4-002, AC-K4-003, AC-K4-004, AC-K4-005, AC-K4-006, AC-K4-007, AC-K4-008
- **动作**：consume current snapshot metrics, K1-K3 aggregate, old-entry checks, real digest fact and all deferred/known-red facts; do not publish merge/release
- **精确文件**：`quality/evidence/k4/final-aggregate.json`
- **boundary**：files: `quality/evidence/k4/final-aggregate.json`; symbols/regions: only the named files and their existing test regions
- **输出**：ORACLE-FINAL-K4 design evidence and current execution receipt
- **Knowledge**：build-code must re-read each named file and preserve unavailable/baseline-red distinctions
- **verification_role**：N/A — non-behavior: aggregate evidence only
- **paired_task**：N/A — reason: final aggregate
- **gate_cmd**：`python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree`
- **expected_exit**：0
- **oracle**：`ORACLE-FINAL-K4 {"pass":"final aggregate evidence records current metrics, K1-K3, legacy, deferred and unavailable facts"}`
- **evidence_path**：`quality/evidence/k4/t015.json`
- **STOP**：command/setup failure, boundary drift, new product decision, or any retained K1-K3 regression
- **recovery**：revert only this card/phase changes, preserve materials and facts, return to owning plan row
- **task risk**：missing current evidence leaves K4 incomplete
- **test tier / test method**：feature — command/acceptance focused; no build-plan execution
- **scenarios / commands / expected exit / oracle**：default success, mismatch/failure stop, and retained K1-K3 seam use the gate command above with the same oracle identity
- **fixtures_services**：temporary pytest tmp_path/fake provider where existing tests require; no external service is started by build-plan
- **required_receipts**：final aggregate must include baseline metrics, real digest receipt or authenticated unavailable, retained K1/K2/K3 regression, 42-row coupled-test disposition, B1–B4 guard receipts, negative-path STOP/rollback matrix, and final handoff owner/next step.
- **coverage limits**：does not prove real provider/release/merge; verify-code must supply those facts
- **acceptance_role**：acceptance
- **ui_scope**：non_ui
- **acceptance_data**：`[{"source":"current K4 worktree","sample":"baseline eee5549 plus final tree","scenario":"aggregate metrics and K1-K3/old-entry evidence","tier":"command","execution":{"command":"python","args":["scripts/task10_metrics.py","--baseline","eee55492517bc86e3aad4838fe215bb23d84e8a4","--tree","worktree","--workflowhub-acceptance"],"timeout_ms":120000}}]`
- **e2e_scope**：not_required

##### 执行状态填写区（唯一完成权威）

- **status**：completed
- **actual_changes**：新增并刷新 `quality/evidence/k4/final-aggregate.json`、`real-digest.json`、`coupled-test-dispositions.json`；补充 P2 resume 边界修复后的当前聚合证据；无产品配置变更。
- **executed_commands**：metrics exit 0，final predicates satisfied；当前 retained K1/K2/K3 aggregate exit 0，163 passed / 1 skipped；real digest exit 1 with `run_status=complete` and `publish_status=not_released`；当前正式 final aggregate receipt=`quality/tests/build-code-final-aggregate-r5.json` exit 0；当前 acceptance receipt=`quality/tests/build-code-acceptance-producer-r4.json` exit 0；official build-code run published current quality facts but returned `quality_status=incomplete`.
- **evidence_refs**：[`quality/evidence/k4/t015.json`, `quality/evidence/k4/final-aggregate.json`, `quality/evidence/k4/real-digest.json`, `quality/evidence/k4/coupled-test-dispositions.json`, `quality/tests/build-code-final-aggregate-r5.json`, `quality/tests/build-code-acceptance-producer-r4.json`, `quality/reviews/results/build-code-simple-3b0ab302-7ef3-5759-a9fc-c061ad3a89e7.json`]
- **covered_ac**：AC-K4-001…AC-K4-008
- **review_fact**：final integration review 已真实记录为 `result`，其中 `F-38bdbd3f570f` 为 blocking/actionable；补充 implementation context 后的唯一重审被 `REVIEW_RETRY_BUDGET_EXHAUSTED` 在 dispatch 前拒绝，未产生新 result；当前官方 handler 有 AC leaves，但 canonical status projection 保留 acceptance/integration/finding 的 incomplete/unavailable，stage outcome/spec-analyze/reflection unavailable，不能把 aggregate 或 review result 当作通过。
- **completed_at**：2026-09-17T02:20:18+08:00
- **执行事实**：K4 implementation/retirement/retained tests/real digest facts are current after the resume-boundary repair; release and WorkflowHub final review/verify-code remain separate.
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


## 4. Final current-snapshot aggregate strategy

- **tier / method**：feature — current snapshot command aggregate; build-plan designs only.
- **scenarios**：all AC-K4-001…008, K1/K2/K3 seam checks, old-entry non-executability, known DEF-K4-8 baseline red, provider/review/unavailable states.
- **command**: `python scripts/task10_metrics.py --baseline eee55492517bc86e3aad4838fe215bb23d84e8a4 --tree worktree`
- **expected exit**：0 only when current evidence is complete; unavailable/incomplete remains non-pass.
- **oracle**：ORACLE-FINAL-K4 — metrics, retained behavior, retirement, rollback/STOP and handoff facts are all current and traceable.
- **fixtures_services**：N/A — reason: build-plan does not execute; build-code supplies authenticated fixtures/provider facts.
- **evidence_path**：`quality/evidence/k4/final-aggregate.json`
- **coverage limits**：does not authorize implementation, commit, merge, release, or substitute for verify-code/provider evidence.
- **STOP**：missing current evidence, unknown deletion proof, unavailable provider/review/reflection/handoff, or any new regression.
- **execution_contract**：current snapshot is run once by build-code/verify-code; raw output and actual status are preserved.

## Dependency Graph

- **order**：T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015
```

## Final Boundary Check

- [ ] Every phase has Goal/Files/Tasks/Verify/Knowledge/STOP/Done/Risks and rollback.
- [ ] Every task is pending; build-plan has executed no command.
- [ ] Every behavior has RED/GREEN same command/oracle.
- [ ] Review/research/reflection/unavailable facts remain visible and are not completion claims.
