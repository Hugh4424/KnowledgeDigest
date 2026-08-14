# 实现计划：Task 3 全量知识发布

- **Input**：`specs/task3-knowledge-publication-full-release/decision-log.md`、`specs/task3-knowledge-publication-full-release/spec.md`
- **Template version**：`plan-task.v3`

## Quick Read

- **Goal**：把冻结的 89 条输入生成同源 Reader/Audit 候选包，完成 17+3、两项 90% 自动门和固定对比；人只确认一页汇总后，整包才原子切换为 `released`。
- **Non-goals**：不逐页人工验收；不改主题身份、正文 compiler、Task 2-C 历史结果或 `digest` CLI；不引入数据库、调度器、向量库和第二套发布状态。来源：decision-log 的非目标与延期交接、spec 第 10 节。
- **Before**：已有正文主链、Reader Bundle、8+3 质量门、old-path/affected 算法和 Task 2 对比统计，但没有 Task 3 统一发布事务。
- **After**：候选生成、自动验收、汇总确认、包级发布和失败保护由一个窄协调器串起，旧正式包在任何失败下保持不变。
- **Main risk**：现有 Bundle 的三目录替换不是单一原子切换，质量读取也未锁定同一快照；若直接拼接会出现 Reader/Audit/报告混版。
- **Next step**：build-code 先执行 T001 的 RED；任何测试只能通过弱化既定阈值时立即 STOP。

## Technical Context

### Global Constraints

- **Verified facts**：`project_reader_bundle()` 当前只生成 Task 2-A `not_released` 包；`run_reader_quality_gate()` 固定 8+3；题集实际为 17+3；合成 89 条 fixture 存在；真实语料需 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS`。
- **Language / runtime**：Python `>=3.11`；当前 Python 3.13.12、uv 0.10.11、锁定 pytest 9.1.1。
- **Primary dependencies**：复用 PyYAML、pytest、现有 `kb_lock`、`reader_frontmatter`、`topic_axis.affected_set`、`batch_run.run_batched`；不新增依赖。
- **Storage / state**：每次运行冻结 manifest/hash；候选、质量、对比和汇总均写入 run-scoped 目录；正式入口只在锁内通过单一目录/指针切换。
- **Testing**：pytest acceptance；provider、时钟、锁故障只在系统边界注入；真实 89 条、真实 provider、人工汇总确认属于 verify-code 证据，不能由 fixture 冒充。
- **Target environment**：本地 macOS 文件系统；离线/Jaccard 可产基线但不能发布为 semantic `released`。
- **Scale / scope**：89 个来源、17 个正向题、3 个负向题、Reader/Audit/报告/确认四类交付面。
- **Unresolved facts**：真实 Task 1/Task 2 基线当前缺失且环境变量未设置；不阻塞编码，阻塞 verify-code 的真实 AC-01/05/06/12 结论。

## Code Anchors

- **Verified anchors**：`src/knowledge_digest/reader_bundle.py:project_reader_bundle,validate_reader_bundle`；`reader_quality.py:derive_task2c_questions,run_reader_quality_gate`；`topic_axis.py:affected_set`；`batch_run.py:run_batched`；`scripts/task2_publication_comparison.py:build_comparison_report`；`lock.py:kb_lock`。
- **Existing interfaces**：`project_reader_bundle(inputs, artifacts) -> CommittedBundleRun`；`run_reader_quality_gate(bundle_dir, question_set_path, output_dir, *, config, llm_call=None) -> QualityGateResult`；`affected_set(...) -> dict`。
- **Read now**：上述符号及 Task 2-A/2-C/TopicAxis/batch recovery acceptance。
- **Must read before task**：T007 前读 `lock.kb_lock` 和 Bundle rollback；T011 前读 comparison schema/rendering；真实运行前读本机基线路径和 provider 配置。
- **Context mode**：Full — 跨候选包、质量、发布事务和恢复边界，但不扩到正文 compiler 内部。

### Reuse → Extend → New

| Capability | Decision | Existing anchor | Reason / removal condition |
| --- | --- | --- | --- |
| 正文编译/affected | reuse | `pipeline.py:audit_run`; `topic_axis.py:affected_set` | 唯一既有算法，不复制 |
| Reader 投影/兼容 | extend | `reader_bundle.py:project_reader_bundle` | 增加 semantic 输入和 old-path/Related 投影 |
| 自动读者门 | extend | `reader_quality.py:run_reader_quality_gate` | 抽 policy，旧 8+3 wrapper 不变 |
| 包级发布事务 | new | `src/knowledge_digest/full_release.py` | 当前无 consumer；由 Task3 薄入口消费并由 acceptance 覆盖；若不能保持单一职责则删除重做 |
| 固定对比 | extend | `task2_publication_comparison.py` | 复用统计，不复制脚本 |
| 执行入口 | new | `scripts/task3_full_release.py` | 薄编排入口；若现有 CLI 获得同等不破坏接口则删除 |

## Solution Design

### Overview

先由既有主链和 batch/affected 逻辑得到冻结的全量语义证据。`reader_bundle.py` 新增并列 semantic 输入，只把同一 snapshot 投影成候选 Reader/Audit；候选默认仍是 `not_released`，并补齐 canonical 导航、基于明确依据的双向 Related links、old-path alias/deprecated 结果。

`reader_quality.py` 把硬编码阈值抽成 `ReaderQualityPolicy`。旧 Task 2-C wrapper 继续保持 8/8、0/3 和原 schema；Task 3 策略执行全部 17+3、15/17、0/3 及两个 90% 门，并记录 actor/model/rule/seed/hash。`full_release.py` 同时重读 `validate_reader_bundle()` 结果和候选文件，逐项硬验来源链、Claim 唯一目标、结构/导航、失败隔离、可重放材料、正文 120 行和整页 300 行；任一缺失或矛盾归为 hard failure/undecidable。

唯一新增深模块 `full_release.py` 重读证据和 hash，分类 hard failures、warnings、undecidable，生成一页汇总。确认只绑定 `run_id + summary_sha256 + actor + time`；锁内再次 readback 后，用单一正式根切换发布。formal root 必须显式提供；已有根先做完整包形状、无软链接和整包 hash 预检，首次发布只允许明确的空目标。它不接受调用者传入的“已通过”布尔值，不写 `human_reviewed`。

失败时保留旧正式包和候选证据，重放只复用 `affected_set` 与 `run_batched`；不新增第二套恢复状态机。固定对比在原脚本内扩展为 Task2/CompanyBrain/Task3 三方报告。

### Module responsibilities

#### `reader_bundle.py`

- **Responsibility**：把 semantic manifest 投影成候选 Reader/Audit，并验证导航、关系和旧路径。
- **Consumes**：`SemanticReaderBundleInputs` 和既有 `ArtifactRef`。
- **Produces**：`CommittedBundleRun`，初始包级状态固定 `not_released`。
- **Must not decide**：最终 `released`、人工确认和质量 verdict。

#### `reader_quality.py`

- **Responsibility**：按显式 policy 运行完整题集、标题理解和归属准确率门；来源/Claim/结构/长度等交付硬门由 `full_release.py` 在同一质量结果中汇总。
- **Consumes**：冻结 Reader snapshot、question set、policy、provider config。
- **Produces**：不可变 `QualityGateResult` 及逐题/评分证据。
- **Must not decide**：包级发布和人工内容信任。

#### `full_release.py`

- **Responsibility**：冻结并重读发布证据；调用 `validate_reader_bundle()` 并检查来源链、Claim 唯一性、120/300 行、失败隔离和可重放材料；生成汇总、验证确认、锁内 readback 和正式切换。
- **Consumes**：`FullReleaseEvidence`、`SummaryConfirmation`、当前正式根。
- **Produces**：`PreparedFullRelease`、release receipt、`FullReleaseResult`。
- **Must not decide**：正文内容、主题身份、题集阈值或警告分类规则之外的新产品需求。

#### comparison/entry script

- **Responsibility**：复用统计生成三方固定对比；薄入口按既定顺序调用公共 seam。
- **Consumes**：baseline/candidate/CompanyBrain 路径和冻结配置。
- **Produces**：comparison report 与一次 run 的可定位输出。
- **Must not decide**：发布状态；只把证据交给 `full_release.py`。

### Interfaces, data, and lifecycle

- **Interfaces / schemas**：新增 `SemanticReaderBundleInputs`、`ReaderQualityPolicy`、`FullReleaseEvidence`、`SummaryConfirmation`；旧 Task2 schema/signature 保持兼容。
- **Data flow / state**：frozen manifest → candidate Reader/Audit → quality/comparison → summary → current-run confirmation → locked readback → released root；任何缺失/矛盾/未知停在 `not_released`。
- **API contract**：N/A — 本地 Python API 与脚本，无 HTTP API。
- **UI / external code**：一页 Markdown/JSON 汇总是唯一人工界面；README 是 Reader 起点，Audit 不进入日常导航。
- **Fail-loud behavior**：hash 变化、题数不符、不可判定、过期确认、并发冲突、offline/fallback、部分目录切换都明确失败且不改旧正式包。

## File Boundary

### NEW

- `src/knowledge_digest/full_release.py`
- `scripts/task3_full_release.py`
- `tests/acceptance/test_task3_projection.py`
- `tests/acceptance/test_task3_quality_release.py`
- `tests/acceptance/test_task3_closeout.py`
- `tests/fixtures/task3_full_release/projection-cases.json`
- `tests/fixtures/task3_full_release/release-cases.json`
- `tests/fixtures/task3_full_release/closeout-cases.json`

### MODIFY

- `src/knowledge_digest/reader_bundle.py`
- `src/knowledge_digest/reader_quality.py`
- `scripts/task2_publication_comparison.py`

### DO NOT TOUCH

- `src/knowledge_digest/pipeline.py`, `draft.py`, `publication.py`, `identity.py`, `topic_axis.py`, `page_layout.py`, `navigation.py`, `writeback.py`, `provenance.py`, `reader_frontmatter.py`, `llm.py`, `lock.py` — 只复用，不重写既有权威。
- `src/knowledge_digest/cli.py`, `pyproject.toml` — 不把 Task3 强塞进正式 `digest` CLI。
- `config/task0-question-set.v1.json`、Task0～Task2C 归档 spec/evidence — 冻结历史输入。
- `AGENTS.md`, `README.md`, `CONTEXT.md` — 根文档同步延期到 Task 3-Closeout；本阶段已有的 CONTEXT 工作流记录除外。

## Technical Decisions

### DEC-001 — 一个包级发布协调器

- **Problem**：现有三条数据流互不锁定，直接拼接会混版。
- **Options**：让各模块各自切状态；重写 pipeline；新增一个窄协调器。
- **Selected**：new `full_release.py`，只做证据绑定和发布事务。
- **Reason**：最小化跨模块状态权威，保留既有 compiler 和 validator。
- **Consequence / risk**：新增一个深模块；必须拒绝布尔“pass”输入并做锁内 readback。
- **Fallback**：准备失败只留下 `not_released` 候选；修复后重新 prepare，不 resume 发布事务。
- **F10 real threat**：Reader/Audit/quality 可能来自不同版本并错误发布。
- **F10 existing cover**：各模块只有局部锁/局部 hash，没有包级事务。
- **F10 bypassable**：否；最终 released 必须唯一经过该 seam。
- **F10 maintenance cost**：两个公共函数、四个窄 dataclass、一个 acceptance 边界。
- **F10 disposition**：`keep`

### DEC-002 — 质量策略参数化，旧 wrapper 不变

- **Problem**：Task2C 的 8+3 不能满足 Task3 17+3。
- **Options**：改旧常量；复制模块；抽 policy。
- **Selected**：extend，抽 `ReaderQualityPolicy` 和通用 assessment，旧 wrapper 固定旧策略。
- **Reason**：避免改写历史结果，也避免复制来源链/快照逻辑。
- **Consequence / risk**：需回归旧 schema、计数和 exit evidence。
- **Fallback**：若旧测试变化，恢复 wrapper 兼容层并只让新入口使用 policy。

### DEC-003 — 正式包用单一根切换

- **Problem**：当前 bundle/audit/reports 三目录逐个替换可被读者观察到混版。
- **Options**：继续三目录替换；数据库事务；run-scoped 根 + 单一 current 根切换。
- **Selected**：run-scoped 候选，锁内 staging/readback 后单一根替换。
- **Reason**：纯文件系统、无新依赖，且旧正式包可整体保留。
- **Consequence / risk**：跨文件系统复制不能原子；入口必须保证 staging 与 release root 同一文件系统。
- **Fallback**：检测设备不一致或 replace 失败即 STOP，清理本次 staging，旧根不动。

## Test Strategy

RED/GREEN 使用同一命令和 oracle；build-plan 不执行测试。

| Target | Task | Role | gate_cmd / expected_exit | Oracle / evidence_path |
| --- | --- | --- | --- | --- |
| AC-02/03/04/11 | T001/T002 | RED/GREEN | `uv run --frozen pytest tests/acceptance/test_task3_projection.py -q` / nonzero→0 | ORACLE-PROJECTION / `apply/evidence/T001...`, `T002...` |
| AC-01/05/06 | T003/T004 | RED/GREEN | `uv run --frozen pytest tests/acceptance/test_task3_quality_release.py -q -k 'snapshot or quality'` / nonzero→0 | ORACLE-QUALITY / T003,T004 evidence |
| AC-07/08/09 | T005/T006 | RED/GREEN | same file `-k 'summary or release'` / nonzero→0 | ORACLE-RELEASE / T005,T006 evidence |
| AC-10 | T007/T008 | RED/GREEN | same file `-k recovery` / nonzero→0 | ORACLE-RECOVERY / T007,T008 evidence |
| AC-12 | T009/T010 | RED/GREEN | `uv run --frozen pytest tests/acceptance/test_task3_closeout.py -q -k comparison` / nonzero→0 | ORACLE-COMPARE / T009,T010 evidence |
| AC-13 | T011/T012 | RED/GREEN | same file `-k entrypoint` / nonzero→0 | ORACLE-HANDOFF / T011,T012 evidence |
| AC-01..13 | T013 | FINAL | related integration + full pytest / 0 | ORACLE-TASK3-AGGREGATE / T013 evidence |

最终相关集成：`uv run --frozen pytest -q tests/acceptance/test_task3_projection.py tests/acceptance/test_task3_quality_release.py tests/acceptance/test_task3_closeout.py tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task1_topic_axis.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py`。最终仓库门：`uv run --frozen pytest -q`。真实 89 条和人工汇总确认另在 verify-code 运行并保存 receipt。

## Rollback and Recovery

- **Global recovery rule**：只撤销当前实现或丢弃当前 candidate；保留 decision/spec/plan/tasks、失败证据和旧 released 根。
- **Deletion proof**：本实现不涉及删除现有正式页、历史证据或旧 released 包；只替换本次 run-scoped staging，清理由 Task 3-Closeout 另行授权。
- **Irreversible boundaries**：commit/push/merge/archive/cleanup 均需独立授权；发布到本地正式根只在明确 summary confirmation 后执行。
- **Recovery owner**：build-code 处理代码/fixture；verify-code 处理真实 provider、89 条运行和人工回执；Task 3-Closeout 处理归档清理。

### Engineering Risk Handoff

- **PLAN-RISK-001**：包级切换混版
  - **Affected IDs**：AC-01、AC-08、AC-10、T007/T008
  - **Trigger**：候选 hash 在确认后变化、跨设备 replace 或并发发布。
  - **Consequence**：Reader/Audit/报告不一致或覆盖旧包。
  - **Mitigation or STOP**：同设备 staging、`kb_lock`、锁内全量 readback、CAS/hash 不符即 STOP。
  - **Handling Stage**：build-code
  - **Verification**：故障注入、并发提交和旧根 byte/hash 不变断言。
- **PLAN-RISK-002**：自动质量结果看似完整但不可回放
  - **Affected IDs**：AC-05、AC-06、T003/T004
  - **Trigger**：缺 actor/model/rule/seed/hash，或只跑 8+3。
  - **Consequence**：不该发布的包被标绿。
  - **Mitigation or STOP**：20 题精确计数和字段完整性都是硬门；未知一律阻断。
  - **Handling Stage**：build-code/verify-code
  - **Verification**：缺字段、14/17、1/3、89% 负例与真实运行 readback。
- **PLAN-RISK-003**：测试 fixture 冒充真实全量结果
  - **Affected IDs**：AC-01、AC-05、AC-06、AC-07、AC-12、AC-13
  - **Trigger**：仅 pytest 通过即宣称发布完成。
  - **Consequence**：形式绿、业务未验收。
  - **Mitigation or STOP**：tasks 明确 real-run/manual evidence；缺原始语料或基线只能报告 blocked/unavailable。
  - **Handling Stage**：verify-code
  - **Verification**：真实 run manifest、quality、comparison、summary confirmation、release readback。

## Implementation Order

P1 先补候选投影和导航；P2 才能在冻结候选上执行完整质量与包级发布；P3 最后生成三方对比和薄入口。每个行为先 RED 后 GREEN，P1 → P2 → P3 串行。

## Dependencies and Parallelism

- **Dependencies**：T001→T002→T003→T004→T005→T006→T007→T008→T009→T010→T011→T012→T013；发布必须消费已验证候选，入口必须消费所有公共 seam；T013 只读聚合，不新增业务行为。
- **Parallel work**：同一 Phase 内的 RED 设计可评审并行，但 build-code 实际写文件按上述顺序，避免共享测试 fixture 和 schema 竞争。
- **External dependencies**：真实语料环境变量、qwen3.6/jina provider 与 CompanyBrain；缺失时 acceptance 仍可完成，但真实发布结论保持 `not_released`/unavailable。

## Requirement and Verification Traceability

| Source / decision | FR | AC | Phase / Task | Depends on | Exact files | Command / oracle |
| --- | --- | --- | --- | --- | --- | --- |
| R-005/D-Reader-Audit | PUBLISH-002,NAV-001..003 | 02,03,04,11 | P1/T001-T002 | none | `reader_bundle.py`, projection test | projection / ORACLE-PROJECTION |
| B/PFACT-001,004 | PUBLISH-001,QUALITY-001..003 | 01,05,06 | P2/T003-T004 | T002 | `reader_quality.py`, `full_release.py` | quality / ORACLE-QUALITY |
| B/PFACT-003,006 | SUMMARY-001,RELEASE-001..003 | 07,08,09 | P2/T005-T006 | T004 | `full_release.py` | summary/release / ORACLE-RELEASE |
| R-005/failure A | RECOVER-001 | 10 | P2/T007-T008 | T006 | `full_release.py` | recovery / ORACLE-RECOVERY |
| R-005 | COMPARE-001 | 12 | P3/T009-T010 | T008 | comparison script | comparison / ORACLE-COMPARE |
| DEFER-001 | CLOSE-001 | 13 | P3/T011-T012 | T010 | Task3 script/test | entrypoint / ORACLE-HANDOFF |
| DEFER-002 | CLOSE-001 | 13 | P3/T011-T012 | T010 | Task3 script/test | entrypoint / ORACLE-HANDOFF |
| DEFER-003 | SUMMARY-001,RELEASE-001..003 | 07,08,09 | P2/T005-T006 | T004 | `full_release.py`, release test | summary/release / ORACLE-RELEASE |
| DEFER-004 | PUBLISH-001,QUALITY-002..003,COMPARE-001 | 01,06,12 | P2/P3/T003-T010 | upstream contracts | implementation/verify-code materials | technical detail only; no new product choice |
| DEFER-005 | all full-run AC | 01,05,06,07,08,09,10,12 | verify-code after P3 | T013 | real run materials | real acceptance / verify-code readback |

完整覆盖索引：R-001、R-002、R-003、R-004、R-005；FR-PUBLISH-001、FR-PUBLISH-002、FR-NAV-001、FR-NAV-002、FR-NAV-003、FR-QUALITY-001、FR-QUALITY-002、FR-QUALITY-003、FR-SUMMARY-001、FR-RELEASE-001、FR-RELEASE-002、FR-RELEASE-003、FR-COMPARE-001、FR-RECOVER-001、FR-CLOSE-001；AC-01、AC-02、AC-03、AC-04、AC-05、AC-06、AC-07、AC-08、AC-09、AC-10、AC-11、AC-12、AC-13。详细 task/oracle 以本表和 tasks 卡为准。

延期交接保持：

- DEFER-001 — status: deferred；owner: Task 3-Closeout；trigger: Task 3 最终状态已由 verify-code readback；handoff: 根文档同步；close condition: 文档与实际代码、命令、状态和目录一致。
- DEFER-002 — status: deferred；owner: Task 3-Closeout；trigger: Task 3 最终 artifact/hash 齐全；handoff: inventory、引用扫描、归档、清理和恢复演练；close condition: 可恢复证据齐全且不确定项保留。
- DEFER-003 — status: resolved in make-decision；owner: make-decision（已关闭）；trigger: 用户确认只看一页汇总；handoff: 固定 17+3 自动题集和 summary confirmation；close condition: 不写 `human_reviewed`，保持 `agent_only`/自动评审事实。
- DEFER-004 — status: deferred to downstream materials；owner: build-plan/build-code/verify-code；trigger: 实现冻结 provider/model/config、题集评分、归属抽样或对比字段时；handoff: 只记录已确认技术细节；close condition: 不改变产品方向，方向变化退回 owning decision。
- DEFER-005 — status: deferred to build-code/verify-code；owner: build-code/verify-code；trigger: Task 3 实现完成并开始真实验收；handoff: 全量运行、全量评分、summary confirmation 和 release readback；close condition: 真实证据给出 `released` 或 `not_released`，保留失败原因。

## Independent Review Disposition

- `F-54e2b62afd0f`、`F-d9c7b44ba66e`：fixed — T003/T004 已补来源、Claim、结构、120/300 行、导航、失败隔离和可重放交付硬门及负例。
- `F-dbe92d8df02c`：fixed — T005/T006 已补离线/语义模式和旧包保护必显字段。
- `F-11130bab7114`、`F-77623954ac4d`：fixed — 卡数改为 13，并补 T013 Test Strategy 行。
- `F-43d46ee906bd`：fixed — 依赖链补到 T013，明确其只读聚合。

## Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| 宪法 | WorkflowHub checklist | no change | all | 逐条绑定，不改治理 |
| 产品规格 | decision/spec | no change | all | build-code 不补需求 |
| 项目根文档 | AGENTS/README/CONTEXT | no change | none | 延期 Closeout |
| acceptance | 三个 Task3 test | change | T001-T012 | 真实 RED/GREEN 合同 |
| 历史 Task2 | Task2 tests/evidence | no change | regression | 仅回归，不改历史 |

## Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"/Users/Hugh/Hugh/Project/workflowhub/constitution-checklist.md","hash":"368817c2910a36e63d3ab4642c30270abdecef15dee7caf8050e778f095919ca","id":"CONSTITUTION","version":"2026-08-03","clause_count":21}`
- **F1**：`full_release.py` 是薄协调器，重活复用现有模块。
- **F2**：四个 dataclass、三个公共函数族构成窄接口。
- **F3**：候选与正式根分离，写前 hash/readback fail-loud。
- **F4**：独立 review 形成 finding，不替代修复和测试。
- **F5**：只保留已确认的硬门、读者门、汇总确认，无新增人工逐项 gate。
- **F6**：run-scoped 证据和 receipt 外置，旧 run 不作新 run 身份。
- **F7**：build-plan 需用户确认；本地正式发布、commit/push 等另行授权。
- **F8**：复用现有 compiler/quality/bundle/comparison，不复制 runner。
- **F9**：pytest、真实运行、人工确认和 release readback 分开报告。
- **F10**：唯一新增深模块针对真实混版威胁，consumer/test/删除条件已记录。
- **Q1**：缺真实 89 条、17+3、review 或交接不得报完成。
- **Q2**：四材料、candidate publication、最终 released 完成分别证明。
- **Q3**：独立 review 与用户计划确认保留，本地测试不冒充质量 verdict。
- **S1**：能力全部优先复用现有项目模块。
- **S2**：N/A — 不引入外部 skill 实现业务。
- **S3**：N/A — 不迭代 WorkflowHub skill。
- **S4**：N/A — 不新增自定义 skill。
- **S5**：N/A — 不新增自定义 skill。
- **S6**：N/A — 不新增自定义 skill。
- **S7**：本计划不改变阶段/skill 目录关系。
- **S8**：N/A — 不新增自定义 skill。

## Phase P1 — 候选 Reader 投影与兼容

### Goal

同一 semantic snapshot 生成 `not_released` 候选 Reader/Audit；正式页面全可达，Related 有依据且双向，旧路径都有 alias/deprecated 结果。

### Files

- **NEW**：`tests/acceptance/test_task3_projection.py`、`tests/fixtures/task3_full_release/projection-cases.json`
- **MODIFY**：`src/knowledge_digest/reader_bundle.py`
- **DO NOT TOUCH**：正文 compiler、TopicAxis、navigation.py 和正式根。

### Tasks

- `T001` RED 投影/导航/关系/旧路径合同；`T002` GREEN semantic 输入与候选投影。

### Verify

ORACLE-PROJECTION — `uv run --frozen pytest tests/acceptance/test_task3_projection.py -q`；RED 非零，GREEN 0；证据 `apply/evidence/T001...`、`T002...`。

### Knowledge

Task3 candidate 仍必须 `not_released`；最终状态只归 `full_release.py`。

### STOP

若需改变 TopicIndex/主题身份/正文结构或靠词面相似生成 Related，返回 build-spec。

### Done

只可报告合成合同通过；不可报告真实 89 条完成或 released。

### Risks and rollback

旧 Task2A schema 回归；失败时回退本 Phase 修改，历史 fixture/evidence 不动。

## Phase P2 — 全量自动质量与包级发布

### Goal

完整执行 17+3 和两项 90% 门，生成一页汇总；只有当前 run 的有效确认能在锁内把同源候选整体发布。

### Files

- **NEW**：`src/knowledge_digest/full_release.py`、`tests/acceptance/test_task3_quality_release.py`、`tests/fixtures/task3_full_release/release-cases.json`
- **MODIFY**：`src/knowledge_digest/reader_quality.py`
- **DO NOT TOUCH**：Task2C 历史 schema/evidence、`lock.py`、`provenance.py`、正式 pipeline。

### Tasks

- `T003/T004` 质量 RED/GREEN；`T005/T006` 汇总发布 RED/GREEN；`T007/T008` 恢复/并发 RED/GREEN。

### Verify

ORACLE-QUALITY — 三组 `-k` 命令及完整 `test_task3_quality_release.py`；旧 `test_task2c_reader_quality.py` 回归必须通过；ORACLE-RELEASE 与 ORACLE-RECOVERY 由对应卡保留。

### Knowledge

确认不是内容审核；warning 可放行，hard/unknown/undecidable/缺确认必须阻断。

### STOP

若需把 unknown 降为 warning、把人工确认写成 `human_reviewed`、或绕过锁内 readback，返回 decision/spec owner。

### Done

可报告包级合同、故障注入和旧根保护通过；真实 provider/89 条/人工确认仍待 verify-code。

### Risks and rollback

并发与文件系统切换风险最高；任何失败只清理本次 staging，不覆盖旧根。

## Phase P3 — 固定对比与薄执行入口

### Goal

生成不伪造可比性的 Task2/CompanyBrain/Task3 固定报告，并用一个薄脚本串起既有 seam，输出 Closeout 可消费的真实状态交接。

### Files

- **NEW**：`scripts/task3_full_release.py`、`tests/acceptance/test_task3_closeout.py`、`tests/fixtures/task3_full_release/closeout-cases.json`
- **MODIFY**：`scripts/task2_publication_comparison.py`
- **DO NOT TOUCH**：`src/knowledge_digest/cli.py`、根文档和归档材料。

### Tasks

- `T009/T010` 对比 RED/GREEN；`T011/T012` 入口与 Closeout 交接 RED/GREEN；`T013` 最终聚合与真实证据缺口清单。

### Verify

ORACLE-COMPARE — `uv run --frozen pytest tests/acceptance/test_task3_closeout.py -q`；再跑 ORACLE-HANDOFF、ORACLE-TASK3-AGGREGATE、相关集成和全仓测试。

### Knowledge

脚本只编排，不重新判状态；真实缺失基线必须写 `N/A`/unavailable。

### STOP

若薄入口需要复制业务逻辑、修改 `digest` CLI 或用主观总分补不可比数据，停止并修正边界。

### Done

合同、回归、独立 review 和交接形状齐全；最终 released 仍必须由真实运行、汇总确认和 readback 证明。

### Risks and rollback

真实基线缺失会阻塞 AC-12 证据；保留 fixture 测试结果但诚实标记未完成，不伪造报告。
