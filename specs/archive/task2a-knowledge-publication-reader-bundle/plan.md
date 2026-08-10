# 实现计划：OKF-compatible Reader Bundle 基础与正向机器信号

> 基于当前 `spec.md` 与 D-004 scope revision。本计划安排 Task 2-A 结构合同和可由已有 source/Claim 证据证明的页面级正向机器信号，不提前做正文语义、人工读者质量门或全量发布。

- **Input**：`specs/task2a-knowledge-publication-reader-bundle/spec.md`（`task2a-spec-v1-draft`，SHA-256 `62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e`）
- **Status**：Draft/in_progress；本次 scope revision 吸收 D-004，新增 Phase 4/T009–T010；T009/T010 已完成实现和测试；正式 build-plan review、routing、spec-analyze、wh-review/current receipts 仍因 WorkflowHub bundle mismatch unavailable，历史 review 不冒充当前事实；技术 verify 已完成，formal verify 仍未闭合
- **Lifecycle note**：spec.md 的 `v1-draft`/等待接受描述的是输入 artifact identity；本 plan/tasks 仍是 Draft/in_progress，不代表 spec 已在本阶段重新接受或已完成正式 handoff。
- **Template version**：`plan-task.v3`

## 1. 速读卡

- **Goal**：在隔离 fixture 目录生成一个可被固定版本外部 OKF parser 零网络读取的 Reader Bundle；Bundle 具备固定布局、三类 concept、嵌套 frontmatter round-trip、来源归因回查、确定性投影报告、页面级正向机器信号和 `not_released` 状态。
- **Non-goals**：不编译 89 篇正文、不调用 LLM 或 embedding、不做 `critical_token_recheck`/`sampled_entailment`/人工 reader gate、不猜 freshness TTL、不改写旧 Reader/Audit 产物、不把包标为 `released`、不引入 OKF runtime/Knowledge Catalog/数据库/图服务、不接入正式 `digest` CLI 或 S1–S6 写回链路（来源：当前 `spec.md` §12，R-009/D1/D-004）。
- **Before**：现有 `navigation.py`/`page_layout.py` 产出旧 Reader Package（`Home.md`、`indexes/`、`pages/`）；`kb_structure.py` 只有简单 YAML-like frontmatter 解析；`pyproject.toml`/`uv.lock` 未锁定 PyYAML；当前 worktree 没有 Task 2-A implementation、fixture、vendor 或 acceptance test。
- **After**：新增显式 `artifact_root` 的隔离 Bundle contract API；同一 artifact root 内分别生成 `bundle/`、`audit/`、`reports/`，输出 `README.md`、`Home.md`、根 `index.md`、根 `log.md`、`products/{product}/...`、`references/sources.md`；concept 页按证据生成 `generated`、`digest_machine_pass`、`source_hash_match`/`locator_resolved` 和可选 `stale_after`；结构失败或信号证据不闭合时 fail-closed，固定 parser smoke 失败只允许记录 `OKF-inspired profile` 降级，不能把未完成的 AC-08/AC-04 冒充 GREEN。
- **Main risk**：外部 parser 固定 commit 和三类真实样本片段尚未关闭；若没有可审计的固定 parser 或本机原始语料，不能伪装 OKF-compatible 或虚构 fixture。
- **Next step**：补齐当前快照的 WorkflowHub formal review/receipt（宿主修复 bundle 后），并保留技术 verify 的真实测试结果；parser commit、原始语料、fixture 选样和真实入口回读仍不得猜测；缺失时按 STOP。

## WorkflowHub Stage Progress

| Stage | Status | Work / artifacts | Review / handoff | Next / deferred risk |
| --- | --- | --- | --- | --- |
| make-decision | completed/revised | `artifact_refs=decision-log.md`；D-001–D-004；R-001–R-009；`decision-log-v1` 当前 SHA-256 `fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734`；`plain_language_summary=在保留结构/离线边界下补充确定性正向机器信号` | `quality_status=source-artifact-recorded`；D-004 来自当前用户直接指令，不伪造 host comment；`user_handoff=current instruction authorizes ordinary continuation` | `risks_deferred=critical_token_recheck/sampled_entailment/human reader gate/Task3 release`；已交 build-plan |
| build-spec | revised | `artifact_refs=spec.md`；27 FR、8 AC、7 SCN、9 PFACT；`task2a-spec-v1-draft` 当前 SHA-256 `62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e`；`plain_language_summary=在原有 AC-04 合同内明确本轮正向机器信号范围` | `quality_status=source-artifact-recorded`；未新增页面类型/provider/人工 reader gate；本次 plan/tasks 必须消费当前 hash | `risks_deferred=OPEN-01/02 由 build-code 关闭，OPEN-03 到 Task 3 前人工确认`；已交 build-plan |
| build-plan | in_progress | `artifact_refs=plan.md`；4 Phase、10 Task；本次加入 D-004 和正向机器信号 Phase 4；constitution binding 按当前快照回读；`plain_language_summary=把 generated、machine pass、source/locator verified、freshness omission 和失效校验写入可执行计划` | `quality_status=unknown/incomplete`；本地结构检查和 routing fallback 已记录，官方 review/receipt 因 `bundle sha256 mismatch: scripts/review-materials.mjs` unavailable；不把历史 review 当当前事实 | `risks_deferred=parser/raw corpus/Task1 receipt debt；semantic/human signals；formal host review receipt 待宿主修复后补齐` |
| build-code | completed | `T009→T010`；Phase 4 只改 `reader_bundle.py` 与对应 acceptance；`trust-signal-red.txt`、`trust-signal-green.txt`；focused `7 passed`、Bundle `34 passed` | `quality_status=technical-pass / formal-review-unavailable`；机器事件、audit 对账、source binding、freshness、mutation rejection 已验证；没有 provider/human/semantic signal | `user_handoff=进入 verify-code；保留 `fullstack/fullstack-slice-testing` 路由和 formal review unavailable` |
| verify-code | in_progress | `final-aggregate.txt`；定向六文件 aggregate `123 passed, 1 skipped`；skip 为未设置 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` | `quality_status=technical-pass / incomplete`；独立复核已发现并修正 audit 对账、source binding、freshness 日期和 mutation 边界；WorkflowHub formal verify/current confirmation 尚缺 | `next=用户确认或宿主补齐 formal receipt 后再闭合 Stage；Task 2-C semantic/human gate 仍 deferred` |

每行包含 `quality_status`、`artifact_refs`、`plain_language_summary`、`risks_deferred` 和 `user_handoff`；`pass` 只表示已有审查事实，不替代阶段语义验收；当前 build-plan 不把缺失 review 写成 pass。

## 2. Technical Context and Constraints

- **Language / runtime**：Python `>=3.11`；当前冻结运行验证使用 CPython 3.12.13、`uv run --frozen`。
- **Primary dependencies**：现有 `src/knowledge_digest`、标准库 `pathlib/hashlib/json/re`、`errors.ValidationError`、`identity.source_id/resolve_topic_identity`、`jsonl` 读写；新增唯一运行依赖 `PyYAML==6.0.2`，只使用 `yaml.safe_load`/`yaml.safe_dump`。输入通过显式 `input_root`/resolver 绑定，不读取隐式 cwd。
- **Storage / state**：调用方显式传入单一、空且独占的 `artifact_root`；API 先在该 root 下的 run-scoped staging 目录写 `bundle/`、`audit/`、`reports/projection-report.json` 和 `reports/exit-manifest.json`，校验完成后原子提交，失败清理 staging 并保持目标 root 不变。validator 同时读取这三个输出面并对账 degraded records。输入使用 Task 1 `topic-index.json`、source inventory/backfill manifest、fixture claim records；输出保持 `not_released`。不写正式 KB，不更新 `_digest`、`_archive` 或旧 Reader 文件。
- **Canonical input aliases**：accepted spec 的 `topic_key_v2` 是输入版本别名；adapter 先归一为 canonical `digest_topic_key`，再按 `digest_topic_id → topic_id → topic_key` 读取稳定身份，输出只写 `digest_topic_key`/`digest_topic_id`。decision-log 的 `OPEN-001`（fixture）和 `OPEN-002`（parser）是跨材料 canonical IDs；spec 中的 `OPEN-02`/`OPEN-01` 分别是它们的别名，不能交换 owner 或关闭条件。
- **Testing**：pytest acceptance；每个行为先 RED 后 GREEN；AC-07 必须通过现有 `digest` CLI 的真实 `--no-llm` 路径，测试 fixture 在调用边界执行 deny-only 本地 socket/provider 拦截并读取既有 runtime audit，再验证 Bundle API；parser compatibility 的 GREEN 只有固定 vendor bytes/commit/license/read smoke 全闭合时成立。阶段预判按 changed-file 多根目录保守路由为 `fullstack`，本阶段不执行具体测试 skill，只把策略写入任务卡。
- **Target environment**：本地人工触发、离线 fixture、无网络；外部 parser 只能读取已 vendor 的固定代码；三类 fixture 首次选样允许读取 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS`，仓库不提交原始语料。
- **Project type**：Python `src-layout` 本地 CLI/文件发布工具；本 Task 只增加可测试的 bundle projection API，不改变现有 `digest` CLI 入口。
- **Performance goals**：N/A — Task 2-A 只处理 3 个 fixture；不设全量 89 条性能目标，避免把本阶段误扩成发布任务。
- **Scale / scope**：3 个手工 concept fixture、Task 1 受控 TopicIndex 样本、source/claim 映射、1 个固定 parser smoke；20 个样本只作为选样来源，不在本任务编译全量。Task 2-A 接受 spec 的 AC-08 降级口径：固定 parser 通过是 `compatibility_passed`，可审计的失败/不可用并正确降级是 `honest_downgrade_passed`；两者都不等于 released。
- **Relevant ADR / context**：`CONTEXT.md` Reader Bundle 定义；`docs/adr/0004-reader-publication-separate-from-audit.md`；`docs/research/20260806-okf-structure-research.md`；accepted `decision-log.md`/`spec.md`。
- **Unresolved facts**：PFACT-007/OPEN-01（spec alias；decision canonical `OPEN-002`，最终 parser commit）、PFACT-008/OPEN-02（spec alias；decision canonical `OPEN-001`，真实片段）、PFACT-009/OPEN-03（Task1 历史 receipt 冲突）不阻断计划编写，但不可在计划或代码中伪装已关闭。当前 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置，worktree 没有 Task 2-A fixture/vendor/tests；T005/T006 因此只能保持 STOP。真实入口 backfill 可读于 `quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`，Task1 控制面可读于 `quality/evidence/task2-entry/task1-real-corpus-20260806/`，但必须在测试中校验 manifest 路径、hash、schema/version 和 coverage，不能用临时最小 manifest 代替 AC-02。当前 task `index.json` 的 reviews 为空、`facts.jsonl` 为空、`quality/verify.json` 为 `unknown`；没有可引用的当前 build-plan review receipt 或用户确认。任务投影必须在本计划每次修订后重新绑定当前 plan SHA-256。

### Global Constraints

- 只做 R-001–R-009/D1–D3 与 D-004 已确定的结构合同和页面级确定性机器信号；正文语义归 Task 2-B，人工读者门归 Task 2-C。
- 根 `index.md` 只有 parser smoke 成功且 profile 为 OKF-compatible 时才写 `okf_version: "0.2"`；降级时必须省略。
- `README.md`、`Home.md`、`references/sources.md` 是固定豁免文件；`index.md`/`log.md` 不能被当作 concept；嵌套目录不生成 `log.md`。
- concept 的 `type` 只能来自三类固定映射；`digest_release_status` 只在 manifest，永不写入 concept 页。
- `digest_content_hash` 排除自身、时间、verified 追加、machine pass、page status、release manifest 和 audit/runtime 字段；YAML 输出参数固定。
- `sources[].id → digest_claims[].claim_id + fragment_locator → source URI/content fingerprint` 必须唯一闭合；只有 source/Claim fingerprint 与 locator evidence 闭合时才生成 D-004 的 `verified` 事件；没有人工证据不能生成 `human:` actor。
- `generated` 记录本次有意义的 Bundle 编译过程；`digest_machine_pass` 只表示结构/归因机器门通过；`verified` 事件必须含白名单 event、固定 process actor、detector version、输入 fingerprint、当前 content hash 和 audit evidence；受管内容/归因/page type 变化必须使旧事件失效。
- `stale_after` 只从 source row 的显式有效期/复核日期读取；无证据省略，非法值不猜测；本 Phase 不实现 `critical_token_recheck`、`sampled_entailment` 或人工 reader gate。
- 失败、冲突、无归属、未通过门禁的页只进入隔离 Audit/Archive fixture 的 `_digest/degraded/` 和 degraded 记录，不进 Reader 导航；不删除旧产物，不写正式 KB。
- `--no-llm` 路径不触碰 provider；凭据、provider 原始响应、完整快照和 `_digest` 不进入 Bundle。
- AC-07 的证据必须来自现有 `cli.main`/`digest` `--no-llm` 真实路径；Bundle API 自身的 provider guard 只补充隔离投影证据，不能替代 CLI 运行审计。
- `ReaderBundleStructureInputs`、`ReaderBundleInputs`、`BundleArtifactPaths`、`BundleReport`、`BundleValidationReport` 和 `ParserSmokeResult` 必须有版本、字段、必填项、拒绝规则和唯一 consumer；TopicIndex adapter 先做公共 envelope/身份/证据/path 检查，再按 product-only 与 standard 分区：仅 standard row 调用 module-required `validate_topic_index`，product-only 调用 module-optional validator；不得按猜测消费旧 alias。
- 固定 parser 通过时只能标记 `ac08_result=compatibility_passed`、写 `okf_version` 和宣称 `OKF-compatible`；固定 parser 失败/不可用但原因、读取边界和降级命名均闭合时标记 `ac08_result=honest_downgrade_passed`，省略 `okf_version`，不宣称兼容；证据不完整仍为 `blocked`。这三种结果都保持包级 `not_released`。
- 所有路径拒绝绝对路径、`..`、软链接和 output root 外写入；所有失败明确返回非零/结构化错误。

## 3. Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"workflowhub/CONSTITUTION.md","hash":"d17c85373e30c4733a77b19dc260373268fca6dd29b8ac3574c8a35b4da6ebd5","id":"workflowhub-constitution","version":"1.5.0","clause_count":21,"checklist_ref":"workflowhub/constitution-checklist.md","checklist_hash":"368817c2910a36e63d3ab4642c30270abdecef15dee7caf8050e778f095919ca"}`

### Framework Principles

- [x] F1 — addressed：使用官方 `CONSTITUTION.md` binding，保留不可伪造、fail-closed 和边界优先原则。
- [x] F2 — addressed：按已接受 spec/plan/tasks 作为当前 Stage 的唯一执行投影，不扩展需求。
- [x] F3 — addressed by `freeze-constitution-check.md`：accepted decision/spec、入口 backfill 和 FR/AC 可回源。
- [x] F4 — addressed：前置 lens/review 只提供质量事实，不授权业务范围。
- [x] F5 — addressed：不增加后台、调度、数据库或第二套门禁。
- [x] F6 — addressed：正式审查仍由 Runner/provider 产生；本计划不把本地检查冒充 verdict。
- [x] F7 — addressed：保留 task、artifact、snapshot 和 handoff 的可追溯关系，路径不由 provider 自选。
- [x] F8 — addressed：复用 identity/jsonl/error 和 vendor parser，只新增 PyYAML 与最小 Bundle 模块。
- [x] F9 — addressed：parser、raw corpus、fixture selection 等未知事实明确 STOP，不用猜测填充。
- [x] F10 — addressed：OPEN-01/02/03、PFACT-007/008/009 明确保留，不把未知写成完成。

### Quality Principles

- [x] Q1 — addressed：每个 AC 有可判定 gate、RED/GREEN、evidence 和 fail-closed 条件。
- [x] Q2 — addressed：计划安排来源闭合、幂等、状态分离和不丢字段，并保留归因失败审计。
- [x] Q3 — addressed：正式 wh-review 与 provider unavailable 语义分离，风险处置不伪装成功。

### Skill Principles

- [x] S1 — addressed：遵循 `spec-plan` 的精确文件边界与三阶段拆分。
- [x] S2 — addressed：遵循 `spec-tasks` 的单卡、DAG、RED/GREEN 合同。
- [x] S3 — addressed：遵循 `simplicity-guard` 的 P0–P3，新增依赖和模块保持最小。
- [x] S4 — addressed：保留接口、失败、回滚、旧 pipeline 保护和停止条件。
- [x] S5 — addressed：遵循 `test-routing-advisor` 的保守分级，build-code 再按实际 diff 重路由。
- [x] S6 — addressed：保留 27 FR ↔ Task ↔ AC 双向追踪。
- [x] S7 — addressed：正式 `wh-review` 由 Runner 运行，unavailable 不改写为 pass。
- [x] S8 — addressed：交接保持用户可读，build-code 不猜 parser、raw corpus 或新 CLI。

**Result**：21/21 条款已有 binding 与计划证据；constitution binding 已验证，正式 `wh-review` 仍是本计划的唯一待决质量事实；不把本地计划检查写成 provider verdict。

## 4. Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| Project rules | `AGENTS.md`, `CONTEXT.md` | no change | N/A | 当前任务不改变项目命令、三深职责或既有 Reader/Audit 规则；实现若改 CLI 需另开规格。 |
| Workflow contracts | `specs/task2a-knowledge-publication-reader-bundle/plan.md`, `tasks.md` | change | T001–T010 | 计划和任务卡是本 Stage 的正式执行投影。 |
| Review contracts | `specs/task2a-knowledge-publication-reader-bundle/freeze-constitution-check.md` | no change | N/A | 只读取既有局部检查；正式 wh-review 由宿主运行，不能手改结果。 |
| Schemas and events | `src/knowledge_digest/reader_frontmatter.py`, `src/knowledge_digest/reader_bundle.py`, `src/knowledge_digest/okf_smoke.py` | change | T001–T010 | 新增 Bundle/frontmatter/manifest/trust-event 的文件合同；不改现有 S1–S6 schema。 |
| Runtime configuration | `pyproject.toml`, `uv.lock` | change | T002 | 固定 PyYAML 运行依赖，避免解析器版本漂移。 |
| Knowledge and docs | `tests/fixtures/task2a_reader_bundle/fixture-selection.json` | change | T006 | 记录三类真实片段选样理由、URI、fingerprint 和 claim 映射；不提交原始语料。 |
| Automation gates | `tests/acceptance/test_task2a_reader_frontmatter.py`, `test_task2a_reader_bundle.py`, `test_task2a_okf_smoke.py` | change | T001–T010 | 为 8 条 AC 提供可执行 RED/GREEN、信号失效断言与离线 smoke。 |

## 5. Technical Decisions

### DEC-001 — 隔离 projection API，不接入正式 CLI

- **Problem**：Task 2-A 必须生成样本包，但不能把 `audit_run` 的正式写回链路、旧 Reader 路径或 CLI 行为提前改成 Task 3。
- **Options**：A. 在 `pipeline.audit_run` 内切换默认输出；B. 新增 `digest` 子命令；C. 新增隔离 `reader_bundle` Python API，由 acceptance fixture 调用。
- **Selected**：extend — 复用现有 identity/error/jsonl 和审计输入，在独立模块提供隔离 projection；接口以显式 `ReaderBundleInputs` + `artifact_root` 接收边界，禁止隐式写固定仓库路径。
- **Reason**：C 满足“只在隔离 fixture 生成”，不改变既有 CLI、S1–S6、旧 Reader/Audit 产物；A/B 会扩大 Task 2-A 影响面。
- **Consequence / risk**：Task 3 仍需设计正式入口；本阶段的 CLI `--no-llm` smoke 只证明既有离线运行边界，不能伪装成 Bundle 生成 CLI；Bundle API 必须把 bundle、audit、report 三个输出面纳入同一 artifact root。
- **Fallback**：接口验证失败时只保留临时 fixture 和 evidence，不写正式 KB；后续 Task 3 另定 CLI。
- **F10 disposition**：keep — 这是 D1/R-009 的边界保护，不是额外门禁。

### DEC-002 — 用一个 frontmatter 模块封装固定 YAML/hash 规则

- **Problem**：现有页面只解析简单 YAML-like header，不能保留嵌套未知字段。
- **Options**：A. 继续扩展行解析；B. 直接在每个 writer 中调用 PyYAML；C. 新增 `reader_frontmatter.py` 作为唯一 parse/dump/hash 边界。
- **Selected**：new — P0/P1/P2 无法满足嵌套 round-trip；C 是最小可审计新增。
- **Reason**：把 `safe_load/safe_dump` 参数和受管 hash 集中，避免多处 serializer 漂移；不修改旧 frontmatter 逻辑。
- **Consequence / risk**：新增一个内部模块和 PyYAML 锁定；后续 2-B/2-C 必须复用同一合同。
- **Fallback**：PyYAML 无法固定或 safe API 不可用时停止，不降级为手写 parser。
- **F10 real threat**：嵌套 sources/generated/verified 丢字段会破坏互操作和归因。
- **F10 existing cover**：现有 `kb_structure._frontmatter_lines` 只处理简单行，不能覆盖本需求。
- **F10 bypassable**：writer 若绕过模块直接拼接 YAML 即可绕过，需 validator/测试抓出并禁止。
- **F10 maintenance cost**：维护固定 serializer 参数、受管字段白名单和 PyYAML pin。
- **F10 disposition**：keep。

### DEC-003 — 复用稳定身份，新增 bundle path/status 规则

- **Problem**：TopicIndex 的 `digest_topic_id`、product/module 归属和 degraded 状态必须在 Bundle 中保持稳定。
- **Options**：A. 用文件顺序或 hash 重新命名；B. 复用 `identity.py` 的 source/topic identity 并在 Bundle 层映射；C. 引入新的 identity service。
- **Selected**：extend — 复用 `source_id`、`resolve_topic_identity`、`read_jsonl` 和 `ValidationError`，只扩展 Bundle 的 profile path/allowlist validator。
- **Reason**：保持 Task 1 当前 `topic_key`/`topic_id`、稳定 ID 和旧页面不变；不新建第二套身份系统。对当前 v2 行，Bundle adapter 把非空 `digest_topic_id` 原样保留，否则把非空 `topic_id`（再否则 `topic_key`）作为同一稳定身份别名；只有 legacy `topic-*` 行才调用 `resolve_topic_identity`，不强迫 v2 行伪造旧 `category_id/topic_dir`。
- **Consequence / risk**：Bundle path 必须明确区分已发布 product/module 和 degraded；无 product/冲突不能生成读者路径。
- **Fallback**：身份、归属或 path 不可验证时输出 degraded audit 记录并保持 `not_released`。
- **F10 disposition**：keep。

### DEC-004 — vendor 外部 parser 最小读取面，失败自动降级

- **Problem**：OKF-compatible 不能只靠自测；需要固定版本外部消费者零网络读取。
- **Options**：A. 重写一个本地 parser；B. vendor 官方 `document.py/index.py/paths.py` 最小读取面；C. 不做 smoke，直接命名 OKF-compatible。
- **Selected**：extend/reuse — B；只 vendor 已核实的官方读取面，禁止引入 runtime；兼容 GREEN 必须绑定实际 vendor bytes、commit、license/notice 和 smoke 结果。
- **Reason**：D2 已接受；外部 parser 是互操作证据。候选研究 commit 为 `930b65fc3f5619d5d0591f88c72ebae8b848d60d`，build-code 必须验证实际固定 commit 后写入 exit manifest。
- **Consequence / risk**：需要 Apache-2.0 license/notice 和升级审计；固定失败必须转 `OKF-inspired profile`。
- **Fallback**：不能固定 commit、license 或离线读取时，先区分“有完整失败/不可用事实”与“事实缺失”：前者结构化记录 `profile=OKF-inspired profile`、省略 `okf_version`、`ac08_result=honest_downgrade_passed`；后者才是 `blocked`。任何降级都不得宣称 `OKF-compatible` 或 released。
- **F10 disposition**：keep。

### DEC-005 — 三类 fixture 用真实样本一次人工选定

- **Problem**：attribution 合同必须接触真实 source URI、fingerprint 和 claim locator，但原始语料不提交仓库。
- **Options**：A. 从 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 的 20 个已预检样本人工选片段；B. 虚构 fixture；C. 从 TopicIndex 自动编译正文。
- **Selected**：extend — A；只把手工整理后的最小 fixture 和选择说明提交；没有当前 raw corpus 时不创建虚构 fixture，不把 synthetic input 计入 AC-03。
- **Reason**：D3 已接受；A 能验证真实回查链，又不提前做正文语义编译。
- **Consequence / risk**：本机必须有原始语料；选样理由、URI、fingerprint、claim mapping 需要可审计。
- **Fallback**：原始语料缺失、片段无法回查或 claim 不唯一时 STOP；不改用虚构样本冒充 AC-03。synthetic fixture 只能覆盖 adapter/validator 负例，不能关闭 T005/T006。
- **F10 disposition**：keep。

## 6. Solution Design

### Overview

`reader_frontmatter.py` 负责唯一 YAML 入口：从 Markdown 分离 frontmatter/body，使用固定 PyYAML safe API 读写嵌套映射，保留未知扩展字段，并按受管字段白名单和正文计算 `digest_content_hash`。旧 `page_layout.py` 的简单 frontmatter 逻辑保持不动。

`reader_bundle.py` 先把 TopicIndex、source inventory/backfill manifest 和 entry refs 适配为结构阶段的 `ReaderBundleStructureInputs`；T005/T006 再把 claim records 和 fixture selection 加入完整的 `ReaderBundleInputs`。在调用方提供的单一 `artifact_root` 内生成 `bundle/`、`audit/` 和 `reports/`，先写 run-scoped staging，再校验后原子提交。TopicIndex 适配器先执行公共 envelope、身份、证据和路径检查；随后把已批准的 product-only row（`status=published`、`knowledge_type=products`、非空 product/object_intent、`module is None`）分区，运行专用 product-only 校验并直接发布到 `bundle/products/{product}/...`，不能虚构 module；其余 standard row 原样交给现有 `validate_topic_index`。这不是静默绕过：公共检查对两条分支都生效，malformed/unsupported/uncertain row 进入 degraded audit。没有满足已批准形状的输入必须 fail-closed 并保留结构化原因；冲突、无归属、未通过检查的内容不进入 Reader index。相同运行写入 `reports/projection-report.json` 的 `degraded_records[]`，并在 `audit/_digest/degraded/{stable_id}.md` 物化对应页面；每条记录固定包含 `reason`、`input_fingerprint`、`recovery_path` 和 `audit_target`，validator 同时校验报告、页面和 Reader 导航三者闭合。Reader Bundle 自身不含 `_digest`，正式 pipeline/KB 不被写入。

`okf_smoke.py` 只读取 vendor 的固定 parser 代码和样本 Bundle，返回可审计的 pass/fail/unavailable、source commit、vendor/license/notice hash、bundle hash、读取边界和原因。`reader_bundle.py` 根据该事实决定 profile/name/根 `okf_version`，生成 `reports/exit-manifest.json`；完整的 smoke 失败/不可用事实可生成 honest downgrade，缺少失败原因或 provenance 才保持 blocked。`--no-llm` 的 `calls.llm=0`、`calls.embedding=0` 由现有 CLI runtime audit 产生；未触网由 acceptance 边界的 deny-only socket guard 证明；两者都不进入生产 smoke 或 Bundle 报告。

### Module responsibilities

#### `reader_frontmatter.py`

- **Responsibility**：固定 frontmatter parse/dump、受管 hash、字段/状态基础校验。
- **Consumes**：Markdown text、`Mapping[str, Any]`、concept contract constants。
- **Produces**：frontmatter mapping、body text、稳定 serialized YAML、`digest_content_hash`、结构错误。
- **Must not decide**：product/module 归属、正文语义质量、reader release、OKF parser profile。

#### `reader_bundle.py`

- **Responsibility**：版本化输入 adapter、隔离 projection、Bundle tree、index/source projection、allowlist/link/path validator、entry backfill 对账和 `not_released` manifest。
- **信号投影**：在同一 projection 中生成 `generated`；结构/归因门通过时生成 `digest_machine_pass` 和 D-004 白名单内的 `source_hash_match`、`locator_resolved`；事件引用输入 fingerprint、detector version、当前受管 content hash 和 `audit/trust-signals/*.json`。没有 raw source bytes、语义 detector 或人工记录时不生成更高等级信号。
- **Consumes**：结构阶段的 `ReaderBundleStructureInputs`（TopicIndex、source inventory、entry artifact refs、offline mode），或归因阶段完整的 `ReaderBundleInputs`（再加 claim records、fixture selection），以及 `BundleArtifactPaths`；只调用 `reader_frontmatter`、当前 `validate_topic_index`、现有 identity/error/jsonl。
- **Produces**：`artifact_root/bundle/**`、`artifact_root/audit/_digest/degraded/**`、`artifact_root/audit/trust-signals/*.json`、`artifact_root/reports/projection-report.json`、`artifact_root/reports/exit-manifest.json`、`BundleReport`/`BundleValidationReport`。
- **Must not decide**：LLM 正文、读者质量、全量发布、旧 Reader 路径迁移。

#### `okf_smoke.py`

- **Responsibility**：固定 vendor parser 的零网络最小读取验证，并区分 passed、failed、unavailable。
- **Consumes**：`bundle_dir`、vendor package、固定 source/commit/license/notice metadata；不新增生产级网络 guard 或 production counter context。
- **Produces**：带 schema/version、vendor hash、bundle hash、读取边界和 reason 的 `ParserSmokeResult`；不自行改变 profile 或 AC-08。完整成功才允许 compatibility pass；`failed/unavailable` 只有在 source/attempt/reason/bundle provenance 完整时才允许 honest downgrade，事实缺失或结果含糊必须 blocked。
- **Must not decide**：自动升级 parser、网络下载、正式 released 状态。

### Conditional contracts

- **UI**：N/A — 本任务只有 Markdown 文件和本地 CLI/模块调用，无交互界面、响应式、焦点或浏览器路由。
- **Externally maintained code**：适用但受限于 `tests/vendor/okf_reference_agent/bundle/document.py`、`index.py`、`paths.py` 和明确的 `LICENSE`、`NOTICE.md`、`README.md`；只保留官方最小读取面、来源 commit、Apache-2.0 license/notice 和复制说明，不修改 vendor 代码，不引入完整 Knowledge Catalog。无固定 bytes/commit/license 时 STOP。

## 7. Data Model and Lifecycle

- **Input binding**：结构阶段使用 `ReaderBundleStructureInputs`（`schema_version=reader-bundle-structure-inputs.v1`、`topic_index_ref`、`source_inventory_ref`、`entry_manifest_refs`、`offline_mode`）；完整归因阶段使用 `ReaderBundleInputs`（`schema_version=reader-bundle-inputs.v1`，在结构字段上增加 `claim_records_ref`、`fixture_selection_ref`）。两者都带显式 `input_root` 和 `resolve_ref(ref)` resolver；resolver 只返回 input root 内、非 symlink 的真实相对文件。每个 `ArtifactRef` 都包含完整的 `artifact_kind`、`ref`、`id`、SHA-256 `hash`、`schema_version`、`version`；缺失、过期、版本不支持或 hash 不符即拒绝。TopicIndex adapter 先做公共 envelope、身份、证据和路径检查，再按批准的 product-only 条件分区：standard row 调用现有 `validate_topic_index`，product-only row 调用专用 module-optional validator；两条分支都保留公共检查并拒绝 malformed/unsupported/uncertain row。随后消费 `topic_key`、`knowledge_type`、`product`、`module`、`object_intent`、`source_members`、`published_path`、`status`、`reason`、`evidence_refs`。稳定身份按 DEC-003 归一：`digest_topic_id` 非空优先，否则 `topic_id`，再否则 `topic_key`；回放必须保持该值和 path 不变。
- **Artifact binding**：`BundleArtifactPaths` 由显式 `artifact_root` 派生且只允许 `bundle_dir=artifact_root/bundle`、`audit_dir=artifact_root/audit`、`projection_report_path=artifact_root/reports/projection-report.json`、`exit_manifest_path=artifact_root/reports/exit-manifest.json`；调用方必须提供新建的空目录且非 symlink，并保证单写者/串行调用。实现只向 `artifact_root/.staging/{run_id}` 写入，完整验证后以目录/文件原子提交；失败清理 staging、保持正式 root 不变。并发协调不属于本 API 合同；若调用方违反单写者边界，结果按 partial-write/validation failure 处理，不增加 owner lock 或 contention 协议。所有最终路径必须 root-contained，禁止绝对逃逸、`..`、软链接和隐式仓库路径。
- **Concept**：`type` 必填，正式字面值固定为 `KnowledgeDigest Product Overview`、`KnowledgeDigest Module or Capability`、`KnowledgeDigest Procedure or Rule`；`title`、`description`、`tags`、`sources`、`generated`、`verified`、`status`、`stale_after` 按合同使用；未知扩展字段原样保留。
- **Fixed type mapping**：映射只消费 TopicIndex 当前行的 `knowledge_type`、`topic_id`、`object_intent`、`product`、`module`、`status` 和 `evidence_refs`，不读标题或正文关键词。对三条人工 fixture，`fixture-selection.json` 必须为每条记录提供 exact `(topic_id, object_intent)` pair、`mapping_role` 和 `digest_page_type`；匹配先做固定 Unicode/空白归一，再要求 pair 唯一且与 TopicIndex 实测值、source fingerprint 完全相等。`mapping_role=product_overview` → `digest_page_type=product_overview` → `KnowledgeDigest Product Overview`（产品定位/边界 fixture）；`mapping_role=module_or_capability` → `module_or_capability` → `KnowledgeDigest Module or Capability`（模块/能力/入口 fixture）；`mapping_role=procedure_or_rule` → `procedure_or_rule` → `KnowledgeDigest Procedure or Rule`（步骤/规则/异常 fixture）。缺 mapping、重复 pair、role/type 不一致、TopicIndex 值不一致或 evidence 不闭合即 degraded；非 `products`、未注册类型、无证据或冲突也不生成正式页，只进入隔离 Audit/Archive `_digest/degraded/`。禁止按标题临时猜 type，未映射即 degraded。
- **Source entry**：`id` 是稳定 source-fragment key；`resource`/URI、title、content fingerprint 和 `digest_claims[]` 必须存在；每个 claim entry 只有一个 `claim_id + fragment_locator`。
- **Identity**：优先沿用 TopicIndex 当前 `digest_topic_id`/`topic_id`/`topic_key` 归一后的稳定别名；Bundle path 仅由明确 product/module 归属与可读 slug 决定，禁止 hash/输入顺序命名。
- **Status**：concept `status` 只取 `stable|draft|deprecated`；页级 `digest_page_status` 只取 `published|degraded`；包级 `digest_release_status` 只取 `not_released`。`verified` 只在 source content fingerprint、claim locator/target path、page type 和 audit evidence 仍与当前输入一致时有效；若 fingerprint、locator、target/path、page type 或 evidence 缺失/变化，validator 必须 fail-closed，保留已有 audit 供诊断，不自动改写当前 Bundle 或伪造 degraded 页面。projection 的输入失败才写隔离 degraded record；T009/T010 覆盖这些 mutation rejection boundaries。
- **Trust event**：当前实现只生成两类机器事件：`source_hash_match` 证明 source inventory、fixture selection 和 Claim 的 fingerprint 一致；`locator_resolved` 证明正文 footnote、source entry、Claim locator 和 target path 唯一闭合。actor 为 `process:knowledge-digest-<event>-v1`，`verified` 是 list；`critical_token_recheck`、`sampled_entailment`、`human:` 和 `agent_assisted` 不生成。
- **Hash**：受管 frontmatter business fields + body 参与 hash；hash 自身、时间、verified、machine pass、page status、release manifest 和 audit/runtime fields 排除。
- **Lifecycle**：entry validation → structure-only projection → structural validation → fixture selection/完整归因 projection → parser smoke → profile/manifest finalization；普通输入/结构失败只保留可审计 failure/degraded evidence，不覆盖旧文件；parser `failed/unavailable` 在 provenance 完整时明确产出 AC-08 `honest_downgrade_passed`，缺失才 `blocked`。结构阶段不得宣称 claim attribution 通过。
- **Commit lifecycle gate**：initial projection 和 profile finalize 都必须走 `staging → validate_reader_bundle(status=passed) → atomic commit`；validator 是两个 commit producer 的硬前置，不是事后 display check。initial commit 产出 `CommittedBundleRun` 三项 base hash；finalize 只接受该句柄，先验证 base hash 未变，再在 staging 注入 smoke 结果。`parser_finalize_recovery` 负例必须在坏 provenance、validator failure 和 base-hash mismatch 三种情况下证明旧 Bundle、projection report、exit manifest 的 SHA-256 不变，且 staging 不出现在正式 root；成功路径才更新三者。
- **Degraded record**：Task 2-A projection report 的 `degraded_records[]` 必须与同一次隔离运行生成的一张 Audit/Archive fixture page 一一对应；记录必须有 `reason`、输入 `input_fingerprint`、`recovery_path` 和唯一 `audit_target`，目标实际位于 `artifact_root/audit/_digest/degraded/{stable_id}.md`，Reader Bundle 内不写 `_digest`，Reader 导航也不出现 degraded 页。测试证据再把该 artifact root 的相对结果复制/记录到 `quality/evidence/task2a-reader-bundle/`，API 不直接写固定证据目录。
- **Invalid transitions**：缺入口 manifest、hash 不一致、path escape、symlink、未知正式 type、空 title/description、断链、重复 attribution、degraded 进入 index、degraded 缺少对应 Audit/Archive fixture page、nested directory 出现 `log.md`、smoke 失败仍写 `okf_version` 都必须非零失败或明确降级。
- **Ownership**：输入 facts 来自 Task 0/1 audit/backfill；Bundle 只读投影，不生成第二套 source/claim truth；exit manifest 只记录本次 fixture 输出事实。

## 8. API Contract

无 HTTP/API 网络接口。新增 Python 模块接口冻结如下：

- `reader_frontmatter.parse_concept_document(text: str) -> tuple[dict[str, Any], str]`：无合法 frontmatter、非 mapping 或 YAML unsafe/解析错误时抛 `ValidationError`。
- `reader_frontmatter.serialize_concept_document(frontmatter: Mapping[str, Any], body: str) -> str`：固定 `safe_dump` 参数；不接受不可序列化对象。
- `reader_frontmatter.managed_content_hash(frontmatter: Mapping[str, Any], body: str) -> str`：只按受管字段和固定 body normalization 计算 SHA-256。
- `reader_bundle.adapt_topic_index_row(row: Mapping[str, Any], *, source_ref: ArtifactRef, row_number: int) -> TopicIndexAdapterResult`：先执行公共 envelope/identity/evidence/path 检查；`knowledge_type=products`、`status=published`、非空 `product/object_intent` 且 `module is None` 只走 module-optional product-only validator，其余 standard row 才调用现有 `validate_topic_index`。结果固定为 `branch=standard|product_only|degraded`、归一后的 `digest_topic_id`/`digest_topic_key`/product/module/object_intent/path、`error_codes`；拒绝码至少包括 `TOPIC_ROW_SCHEMA_UNSUPPORTED`、`TOPIC_ROW_MISSING_IDENTITY`、`TOPIC_ROW_MISSING_EVIDENCE`、`PRODUCT_ONLY_MISSING_PRODUCT`、`PRODUCT_ONLY_MISSING_OBJECT_INTENT`、`PRODUCT_ONLY_MODULE_FORBIDDEN`、`PRODUCT_ONLY_INVALID_STATUS`、`TOPIC_ROW_CONFLICT`、`TOPIC_ROW_UNCERTAIN`。product-only 分支不能静默绕过公共检查，也不能虚构 module。
- `reader_bundle.ReaderBundleStructureInputs`：`schema_version: Literal["reader-bundle-structure-inputs.v1"]`、`input_root: Path`、`topic_index_ref: ArtifactRef`、`source_inventory_ref: ArtifactRef`、`entry_manifest_refs: tuple[ArtifactRef, ...]`、`offline_mode: Literal["no-llm"]`；拒绝未知/缺失顶层字段、root 外 refs、schema/version/hash 不一致和非离线模式。
- `reader_bundle.ReaderBundleInputs`：`schema_version: Literal["reader-bundle-inputs.v1"]`、上述结构字段加 `claim_records_ref: ArtifactRef`、`fixture_selection_ref: ArtifactRef`；只有该完整输入才允许 AC-03 的正向 attribution。
- `reader_bundle.ArtifactRef`：`artifact_kind: str`、`ref: str`、`id: str`、`hash: str`、`schema_version: str`、`version: str`；`hash` 必须为 SHA-256，`id` 在本次输入集合中唯一，`ref` 必须经 `input_root`/resolver 指向允许读取的相对文件；缺失、重复、越界、版本漂移或内容 hash 不符时抛 `ValidationError`。
- `reader_bundle.BundleArtifactPaths.from_root(artifact_root: Path) -> BundleArtifactPaths`：要求调用方提供新建/空的非 symlink root；调用方保证单写者/串行使用。只派生 `bundle_dir`、`audit_dir`、`projection_report_path`、`exit_manifest_path` 四个 root-contained 路径，投影内部另有 run-scoped staging 和原子提交；不创建 owner lock，也不承诺并发协调。
- `reader_bundle.project_reader_bundle(inputs: ReaderBundleStructureInputs | ReaderBundleInputs, artifacts: BundleArtifactPaths) -> BundleReport`：先经 resolver 验证 entry refs 和 TopicIndex v2，再只写 staging；报告包含 `schema_version`、`run_id`、profile（初始为 `pending-parser`）、`ac08_result=blocked`、`release_status=not_released`、bundle/audit/report refs、degraded records 和 input readback。CLI runtime audit 单独提供 `calls.llm=0`、`calls.embedding=0`；网络零请求只由 acceptance 边界 deny-only socket guard 提供，二者都不进入 BundleReport。
- `reader_bundle.validate_reader_bundle(artifacts: BundleArtifactPaths, expected: ReaderBundleStructureInputs | ReaderBundleInputs) -> BundleValidationReport`：同时检查 bundle allowlist/frontmatter/links/index、Home 唯一指向、status、结构阶段的 entry readback，完整输入再检查 source/claim 回查、projection report 与 degraded audit page 一一对应、resolver containment；报告包含 `schema_version`、`status`、checked paths、error codes、entry/source/claim counts、degraded match count 和 artifact root ref；错误 fail-closed，empty index entry 或 Home 指向其他目标必须拒绝。
- `reader_bundle` trust-signal projection：`generated={by,at}` 使用本次有意义的 Bundle 编译时间；`digest_machine_pass` 为结构/归因 gate 的布尔投影；`verified` 为事件 list，每项至少有 `event`、`actor`、`detector_version`、`input_fingerprints`、`content_hash`、`evidence_ref`。只允许 `source_hash_match` 和 `locator_resolved` 进入本轮 GREEN；`stale_after` 只有 source input 的显式有效期/复核日期可解析时写入。validator 必须回读 evidence_ref、actor、事件白名单和当前 content hash，并在 mutation 后报错。
- `reader_bundle.CommittedBundleRun`：由初次 `project_reader_bundle` 在 `validate_reader_bundle(...).status == "passed"` 后生成，包含 `artifact_root`、`run_id`、`base_bundle_hash`、`base_projection_report_hash`、`base_exit_manifest_hash`；它是 finalize 的唯一输入句柄，禁止只传裸 root 猜测当前版本。
- `reader_bundle.finalize_bundle_profile(run: CommittedBundleRun, smoke: ParserSmokeResult) -> BundleReport`：只在 run-scoped staging 内消费 smoke 事实并更新 profile/manifest；先核对 run handle 的三项 base hash，再让 validator 强制消费 staging 输出且 `status == "passed"`，之后才 atomic replace。任一 hash、validator 或 provenance 失败都清理 staging、保持原 Bundle/report/manifest 字节不变并返回结构化 failure。只有 `smoke.status=passed` 且 source/attempt/commit/vendor hash/license/notice/bundle hash/read-boundary 字段齐全时才写 `profile=OKF-compatible`、`ac08_result=compatibility_passed` 与根 `okf_version: "0.2"`；`failed/unavailable` 且失败原因和读取边界完整时写 `profile=OKF-inspired profile`、`ac08_result=honest_downgrade_passed` 并省略字段；事实不完整才为 `blocked`。AC-07 的 `calls.llm=0`、`calls.embedding=0` 另由现有 CLI runtime audit 提供，网络零请求由 acceptance deny-only socket guard 提供。
- `okf_smoke.ParserVendorRef`：`source_ref`、`source_commit`、`vendor_root`、`vendor_hash`、`license_ref`、`license_hash`、`notice_ref`、`notice_hash`、固定 `read_boundary`；这些值必须来自已读回的本地 vendor manifest，不能由 smoke 函数猜测。
- `okf_smoke.ParserSmokeAttempt`：`attempt_ref`、`bundle_hash`、`command`、`read_boundary` 和 attempt evidence ref；由 `okf_smoke.create_smoke_attempt(vendor: ParserVendorRef, bundle_dir: Path, *, attempt_ref: str) -> ParserSmokeAttempt` 生成并在执行前固定。`okf_smoke.run_parser_smoke(bundle_dir: Path, vendor: ParserVendorRef, attempt: ParserSmokeAttempt) -> ParserSmokeResult` 禁止网络；vendor/commit/hash/license/notice 不匹配或 parser 失败返回带完整 provenance 的 `failed/unavailable` 事实，不抛成成功；结果至少带 `source_ref`、`attempt_ref`、`source_commit`、vendor/license/notice/bundle hash、`read_boundary`、`read_summary` 和 `reason`；缺 source、attempt、reason、bundle 或读取边界时返回 `blocked`。`--no-llm` 的 `calls.llm=0`、`calls.embedding=0` 由现有 CLI runtime audit 负责；AC-08 的 acceptance 测试可以在测试边界安装 deny-only socket guard，但不把 guard/counter context 传入生产函数。只由 `finalize_bundle_profile` 消费其结果。

### Versioned input schema

| Object | Required fields | Rejection rule | Consumer |
| --- | --- | --- | --- |
| `ArtifactRef` | `artifact_kind`, `ref`, `id`, `hash`, `schema_version`, `version` | non-SHA-256, missing/duplicate id, missing path, root escape/symlink, stale hash, unsupported schema/version | explicit `input_root` resolver used by both input loaders |
| `ReaderBundleStructureInputs` | `schema_version`, `input_root`, `topic_index_ref`, `source_inventory_ref`, `entry_manifest_refs`, `offline_mode` | missing structural ref, root escape, stale hash, non-offline mode | T003/T004 structure projection |
| `ReaderBundleInputs` | structure fields plus `claim_records_ref`, `fixture_selection_ref` | missing attribution ref or claim/fixture fields used before T005/T006 | T005/T006 attribution projection |
| TopicIndex v2 row | current validator required fields plus current `topic_key`/`topic_id`/optional `digest_topic_id` identity fields | schema not `2.0.0`, invalid row, duplicate member/path, missing evidence, published axis invalid; public envelope checks run first, approved product-only rows are partitioned to a dedicated adapter before the existing module-required validator, while standard rows use `validate_topic_index`; malformed/unsupported/uncertain stays degraded | `reader_bundle` adapter |
| Source inventory row | `source_id`, `source_uri`, `content_fingerprint`, `content_path`, `knowledge_type`, `validation_status`, `evidence_refs` | missing source identity/fingerprint, non-passed source, evidence mismatch | attribution resolver |
| Claim record | `claim_id`, `source_uri`, `content_fingerprint`, `fragment_locator`, `verification_status`, `target_path` | no unique source/fingerprint/locator, target outside artifact projection | attribution resolver |
| `BundleReport` | `schema_version`, `run_id`, `profile`, `ac08_result`, `release_status`, four artifact refs, `degraded_records`, `input_readback` | missing output ref, invalid result enum, inconsistent degraded/audit counts, non-`not_released` status | `project_reader_bundle` and `finalize_bundle_profile` |
| `BundleValidationReport` | `schema_version`, `status`, `checked_paths`, `error_codes`, entry/source/claim counts, degraded match count, artifact root ref | unchecked output surface, unresolved error, report/page mismatch, root escape | `validate_reader_bundle` |
| `ParserSmokeResult` | `schema_version`, `status`, `source_ref`, `attempt_ref`, `source_commit`, `vendor_hash`, `license_hash`, `notice_hash`, `bundle_hash`, `read_boundary`, `read_summary`, `reason` | missing source/attempt/reason/bundle/read-boundary provenance or ambiguous result cannot become honest downgrade; only complete pass can become compatibility pass | `finalize_bundle_profile` |

### Current entry input binding (逐项版本/哈希/消费者)

所有真实入口都先由同一 `input_root` resolver 读取，再做声明 hash 与实测 SHA-256 对账。文件自身没有 `schema_version` 的（`source-inventory.jsonl`、`topic-plan.json`、`run-report.json`、`kb.structure.md`）不猜版本：必须绑定父级 `task1-real-corpus-verification.v1` 的 `outputs.<name>` receipt；缺父级 receipt 或 receipt 中没有该 output 就拒绝。下面的 hash 是当前 backfill/verification receipt 声明值，build-code 必须重新实测并把结果写入 entry readback evidence。

| ArtifactRef id | Relative ref / schema-version | Declared SHA-256 | Producer / consumer |
| --- | --- | --- | --- |
| `task2a-entry-backfill-20260806` | `knowledge-publication-task2-entry-backfill.v1.json` / `knowledge-publication-task2-entry-backfill.v1` | `567c27dd4f791a9eccfdef85b67a58e56f9b58c19b4483f5f86e5b536cb054bf` | entry-backfill producer / T003-T004 |
| `task2a-sample-coverage-20260806` | `task2-entry-sample-coverage.v1.json` / `task2-entry-sample-coverage.v1` | `fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f` | Task 2 entry precheck / T003-T004 |
| `task2a-task1-source-inventory-20260806` | `task1-real-corpus-20260806/source-inventory.jsonl` / parent `task1-real-corpus-verification.v1`, `outputs.source_inventory` | `1e770ca33d865f5f3ceb0f5e8236e9daa49dda7a8f62faa97d9be7b0f1f17f52` | Task 1 verification receipt / T003-T004 |
| `task2a-task1-topic-index-20260806` | `task1-real-corpus-20260806/topic-index.json` / `2.0.0` plus parent receipt | `78ab433084e782d8753d1399f5d85714a572ddaa0c1c3b7f29f535a7105b1c7c` | Task 1 TopicIndex producer / T003-T004 |
| `task2a-task1-topic-plan-20260806` | `task1-real-corpus-20260806/topic-plan.json` / parent `task1-real-corpus-verification.v1`, `outputs.topic_plan` | `8b3b3ce5716751f044cf09835bd4be85956a4a77d1d8beed51491467c3db96a8` | Task 1 verification receipt / T003-T004 |
| `task2a-task1-run-report-20260806` | `task1-real-corpus-20260806/run-report.json` / parent `task1-real-corpus-verification.v1`, `outputs.run_report` | `532e6ce4794beb9245b63f8d6a15617a8a8169e667814b52bc4f76ddbb063412` | Task 1 run producer / T003-T004 |
| `task2a-task1-verification-20260806` | `task1-real-corpus-20260806/verification-receipt.json` / `task1-real-corpus-verification.v1` | `3a32d5a07f1a87f80e4c1bfc44432626f3391d192281e278cc45e47c340bf87a` | Task 1 verification producer / T003-T004 |
| `task2a-task1-kb-structure-20260806` | `task1-real-corpus-20260806/kb.structure.md` / parent `task1-real-corpus-verification.v1`, `outputs.kb_structure` | `7ddaa6d58eda9cb7e1713c982938400ede4e333b017d9b5afb4a026282fe83b3` | Task 1 verification receipt / T003-T004 |

`task1-receipt-reconciliation.v1.json`（当前文件 hash `ae12d83591bcbcd6c058805d1c8e29958a7f725f2034c1f451a4a88420802609`）只作为历史 receipt 冲突的 audit input，不作为当前 exit；它的 consumer 是 projection report/STOP evidence，不得被 `ArtifactRef` 当作已发布事实消费。

### Entry backfill producer contract

`reader_bundle.check_entry_bindings(inputs: ReaderBundleStructureInputs) -> EntryBindingCheck` 必须返回每个 ArtifactRef 的 `declared_schema_version`、`declared_version`、`declared_hash`、`observed_hash`、`consumer`、`status` 和 `error_codes`。当入口缺失、过期或 hash 不一致时，`reader_bundle.write_entry_backfill_manifest(check: EntryBindingCheck, artifacts: BundleArtifactPaths, *, run_id: str) -> EntryBackfillResult` 在 staging 中生成 `audit/entry-backfill/{run_id}.json`，固定 `schema_version=reader-bundle-entry-backfill.v1`、`status=backfill_required|blocked`、`digest_release_status=not_released`、缺失/过期 refs、原始输入快照、`recheck_command` 和 evidence ref；不得填充虚构 source/claim。只有 backfill manifest 写入、校验并在 projection report 中对账后，结构运行才可返回“有 backfill 的 not_released”；缺 raw corpus 或缺 producer 事实时只能 `blocked`。入口完整时不生成空 backfill。

Backfill 行为的唯一 acceptance gate 是 `pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'entry_backfill or entry_readback'`；证据为 `quality/evidence/task2a-reader-bundle/entry-backfill-{red,green}.txt` 与隔离 root 的 canonical manifest 哈希。该 gate 只证明入口状态和 backfill 可回放，不关闭 AC-03 或 Task 2-B/2-C。

## 9. File Boundary

### NEW

- `src/knowledge_digest/reader_frontmatter.py`
- `src/knowledge_digest/reader_bundle.py`（Phase 2 NEW；Phase 3 仅 MODIFY profile/smoke integration region）
- `src/knowledge_digest/okf_smoke.py`
- `tests/acceptance/test_task2a_reader_frontmatter.py`
- `tests/acceptance/test_task2a_reader_bundle.py`
- `tests/acceptance/test_task2a_okf_smoke.py`
- `tests/fixtures/task2a_reader_bundle/topic-index.json`
- `tests/fixtures/task2a_reader_bundle/source-inventory.jsonl`
- `tests/fixtures/task2a_reader_bundle/claim-history.jsonl`
- `tests/fixtures/task2a_reader_bundle/fixture-selection.json`
- `tests/fixtures/task2a_reader_bundle/product-overview.md`
- `tests/fixtures/task2a_reader_bundle/module-capability.md`
- `tests/fixtures/task2a_reader_bundle/procedure-rule.md`
- `tests/vendor/okf_reference_agent/__init__.py`
- `tests/vendor/okf_reference_agent/bundle/__init__.py`
- `tests/vendor/okf_reference_agent/bundle/document.py`
- `tests/vendor/okf_reference_agent/bundle/index.py`
- `tests/vendor/okf_reference_agent/bundle/paths.py`
- `tests/vendor/okf_reference_agent/LICENSE`
- `tests/vendor/okf_reference_agent/NOTICE.md`
- `tests/vendor/okf_reference_agent/README.md`

### GENERATED EVIDENCE (execution outputs)

`quality/evidence/task2a-reader-bundle/frontmatter-red.txt`、`frontmatter-green.txt`、`bundle-red.txt`、`bundle-green.txt`、`attribution-red.txt`、`attribution-green.txt`、`smoke-red.txt`、`smoke-green.txt`、`final-aggregate.txt` 以及隔离 artifact root 里的 `audit/_digest/degraded/{stable_id}.md` 页面是 build-code/verify-code 运行时生成的 evidence receipts；它们不作为 source `NEW/MODIFY` 文件重复列入边界。`artifact_root/reports/projection-report.json` 和 `artifact_root/reports/exit-manifest.json` 是 API 的唯一事实源；runner/build-code 只在对应 task-relative evidence path 复制、记录 SHA-256、读回并失败即 STOP，不能反向把 evidence copy 当产品输出或第二事实源。Audit/Archive fixture 不是正式 KB，也不允许被 Reader root 引用为导航内容。

### MODIFY

- `pyproject.toml`
- `uv.lock`
- `src/knowledge_digest/reader_bundle.py`
- `tests/acceptance/test_task2a_reader_bundle.py`

### DO NOT TOUCH

- `src/knowledge_digest/navigation.py`
- `src/knowledge_digest/page_layout.py`
- `src/knowledge_digest/provenance.py`
- `src/knowledge_digest/pipeline.py`
- `src/knowledge_digest/cli.py`
- `src/knowledge_digest/identity.py`
- `src/knowledge_digest/kb_structure.py`
- `src/knowledge_digest/publication.py`（仅作 `PublicationContract` 类型引用，不修改）
- `tests/acceptance/test_task0_reader_package.py`
- `tests/acceptance/test_publication_contract.py`
- `tests/acceptance/test_task1_topic_axis.py`
- `quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`
- `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`
- `quality/evidence/task2-entry/task1-receipt-reconciliation.v1.json`
- `quality/evidence/task2-entry/task1-real-corpus-20260806/source-inventory.jsonl`
- `quality/evidence/task2-entry/task1-real-corpus-20260806/topic-index.json`
- `quality/evidence/task2-entry/task1-real-corpus-20260806/topic-plan.json`
- `quality/evidence/task2-entry/task1-real-corpus-20260806/run-report.json`
- `quality/evidence/task2-entry/task1-real-corpus-20260806/verification-receipt.json`
- `quality/evidence/task2-entry/task1-real-corpus-20260806/kb.structure.md`

Task0/Task1 backfill 与 exit-manifest 输入必须由 acceptance 测试以当前仓库中的真实相对 refs 读取并校验；允许另建 synthetic negative fixture 测试拒绝分支，但 synthetic input 不能关闭 AC-02。`artifact_root` 只在 `tmp_path` 内创建，真实 evidence 目录只读。

## 10. Data Flow and Integration

```text
Task 1 TopicIndex v2 + real entry refs + fixture claims
  → validate_topic_index + versioned adapter + artifact_root containment
  → fixed source/claim mapping
  → reader_frontmatter safe YAML/hash
  → reader_bundle isolated bundle/audit/report projection + allowlist/link validation
  → okf_smoke fixed vendor parser
  → profile decision + not_released projection/exit manifests
```

- **Existing modules / packages / services**：复用 `kb_structure.validate_topic_index`/`TOPIC_INDEX_SCHEMA_VERSION` 做 v2 输入闸，`identity.source_id`/`resolve_topic_identity` 作为稳定身份锚点，`jsonl.read_jsonl` 作为既有 JSONL 读写，`errors.ValidationError` 作为 fail-closed 错误；读取 Task 1 backfill/index，不调用 LLM/embedding/provider。
- **Integration points**：只在 acceptance tests 和显式 artifact root API 中调用；AC-07 另由现有 `cli.main` + `--no-llm` 真实路径验证；不改 `pipeline.audit_run`、`navigation.build_publication_navigation`、`page_layout.build_topic_layouts` 或 `cli.build_parser`。
- **Compatibility boundaries**：旧 `Home.md`/`indexes/sources.md`/`pages/` 保持不动；新 Bundle 固定 `references/sources.md`；Task 1 当前 `topic_key`/`topic_id` 和稳定身份别名不漂移。
- **Fail-loud behavior**：输入 manifest/hash/claim 不闭合、TopicIndex schema/字段漂移、artifact root 越界、symlink、空入口、断链、状态混层、未知正式 type、verified 证据失效、固定 parser 不可读取都返回明确错误或结构化降级；普通 projection degraded 不等于 AC-08 结果，但 parser `failed/unavailable` 在 provenance 完整时明确返回 `honest_downgrade_passed`，只有 provenance 缺失才 `blocked`，永不返回假成功。

## 11. Code Anchors and Reuse

### Versioned identity and context projection

- **Spec binding**：`{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"}`
- **Decision binding**：`{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"}`
- **Research binding**：`{"artifact_kind":"research","ref":"docs/research/20260806-okf-structure-research.md","hash":"38f7de7935becb674be20a09b075750cba2795d2185e3aef33548e78ac37a56d","id":"okf-structure-research-20260806"}`
- **Entry bindings**：
  - `{"artifact_kind":"entry-backfill","ref":"quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json","hash":"567c27dd4f791a9eccfdef85b67a58e56f9b58c19b4483f5f86e5b536cb054bf","id":"task2a-entry-backfill-20260806"}`
  - `{"artifact_kind":"sample-coverage","ref":"quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json","hash":"fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f","id":"task2a-sample-coverage-20260806"}`
  - `{"artifact_kind":"task1-source-inventory","ref":"quality/evidence/task2-entry/task1-real-corpus-20260806/source-inventory.jsonl","hash":"1e770ca33d865f5f3ceb0f5e8236e9daa49dda7a8f62faa97d9be7b0f1f17f52","id":"task2a-task1-source-inventory-20260806"}`
  - `{"artifact_kind":"task1-topic-index","ref":"quality/evidence/task2-entry/task1-real-corpus-20260806/topic-index.json","hash":"78ab433084e782d8753d1399f5d85714a572ddaa0c1c3b7f29f535a7105b1c7c","id":"task2a-task1-topic-index-20260806"}`
  - `{"artifact_kind":"task1-topic-plan","ref":"quality/evidence/task2-entry/task1-real-corpus-20260806/topic-plan.json","hash":"8b3b3ce5716751f044cf09835bd4be85956a4a77d1d8beed51491467c3db96a8","id":"task2a-task1-topic-plan-20260806"}`
  - `{"artifact_kind":"task1-run-report","ref":"quality/evidence/task2-entry/task1-real-corpus-20260806/run-report.json","hash":"532e6ce4794beb9245b63f8d6a15617a8a8169e667814b52bc4f76ddbb063412","id":"task2a-task1-run-report-20260806"}`
  - `{"artifact_kind":"task1-verification-receipt","ref":"quality/evidence/task2-entry/task1-real-corpus-20260806/verification-receipt.json","hash":"3a32d5a07f1a87f80e4c1bfc44432626f3391d192281e278cc45e47c340bf87a","id":"task2a-task1-verification-receipt-20260806"}`
  These refs and hashes must be read back before T004; the Task 1 receipt reconciliation remains an audit input, not a completed closure.
- **read_now**：`kb_structure.validate_topic_index`（`kb_structure.py:685`）、`topic_axis.topic_index_from_plan`（`topic_axis.py:1053`）、`navigation.build_publication_navigation`（`navigation.py:256`）、`page_layout.build_topic_layouts`（`page_layout.py:572`）、`provenance.validate_prewrite_provenance`（`provenance.py:65`）、`pipeline.audit_run`（`pipeline.py:1688`）、`identity.source_id/resolve_topic_identity`、`jsonl.read_jsonl`（`jsonl.py:106`）、真实 Task 1 evidence refs。
- **must_read_before_task**：T002 前读 `pyproject.toml`/`uv.lock`；T004/T006 前读 `kb_structure.validate_topic_index`、Task 1 v2 field sample、`identity.py`、`jsonl.py`、entry backfill 和 claim schema；T008 前读外部 parser license/source commit 和 smoke input；AC-07 前读 `cli.main`/`--no-llm` current signature。
- **Context mode**：Full — 新 Bundle 是跨模块文件合同，必须同时核对旧 Reader、identity、provenance、Task 1 artifacts 和 test boundary；不需要读取全量 raw corpus。

### Verified anchors

| Anchor | Path and symbol | Current responsibility | Intended use | Forbidden change |
| --- | --- | --- | --- | --- |
| A-001 | `src/knowledge_digest/navigation.py:256 build_publication_navigation` | 生成旧 Reader navigation records，不直接写文件 | reference only，复用 staged-record 思路 | 不切换旧输出为 Bundle |
| A-002 | `src/knowledge_digest/page_layout.py:572 build_topic_layouts` | 合并稳定 topic、锁定可读路径、按 300 行分页 | reuse identity/path invariants as input facts | 不改旧页面布局或分页 |
| A-003 | `src/knowledge_digest/provenance.py:65 validate_prewrite_provenance` | 写前校验 source/snapshot/ledger/claim/target | reference for fail-closed source closure | 不扩大旧 `_is_reader_target` 到 Bundle |
| A-004 | `src/knowledge_digest/pipeline.py:1688 audit_run` | S1–S6 单写者正式写回 | integration boundary only | 不接入 Task 2-A projection |
| A-005 | `src/knowledge_digest/identity.py:39 source_id; :116 resolve_topic_identity` | 稳定 source/topic identity 和可读路径 | reuse | 不创建第二套 identity |
| A-006 | `src/knowledge_digest/kb_structure.py:685 validate_topic_index` | 校验并归一 TopicIndex v2/legacy input | reuse as input gate | 不改 schema 或把 legacy migration 当新 Bundle contract |
| A-007 | `src/knowledge_digest/jsonl.py:106 read_jsonl` | 读取既有 JSONL records，容忍唯一 torn tail | reuse for fixture/audit input | 不把 JSONL 读取结果当 Bundle source truth |
| A-008 | `src/knowledge_digest/kb_structure.py:831 serialize_source_index` | 旧 `indexes/sources.md` markdown projection | reference only | 不把旧 source-index 当新 `references/sources.md` 合同 |
| A-009 | `src/knowledge_digest/cli.py:26 build_parser; :78 main` | 现有 `digest` CLI 参数解析和离线 `--no-llm` 运行入口 | read-only AC-07 oracle | 不新增 flag、不接入 Bundle projection、不改 CLI |

### Reuse → Extend → New

| Capability | Decision | Existing candidates | Reason |
| --- | --- | --- | --- |
| Stable source/topic identity | reuse | A-005 | 已有稳定 hash/路径不应重写。 |
| TopicIndex v2 input validation | reuse | A-006 | 当前 schema 和 alias 已有唯一 validator；adapter 只做字段投影。 |
| JSONL/source evidence loading | reuse | `jsonl.py`, pipeline S1–S6 artifacts | 不增加 repository/service 层。 |
| Fail-closed errors | reuse | `errors.ValidationError` | 保持现有错误类别和 CLI 测试习惯。 |
| Nested YAML round-trip/hash | new | 现有 `kb_structure` 行解析不足 | P0/P1/P2 不足，PyYAML 是 spec 硬约束。 |
| Bundle tree/allowlist validator | new | 旧 navigation 只懂旧目录 | 新 `products/references/index/log` 身份合同不应污染旧 Reader。 |
| External parser smoke | extend/reuse | 官方 vendor 最小读取面 | 不重写 parser，不引入 runtime。 |

### Existing interface signatures

| Signature ID | Object | Verified current signature/schema | Source anchor |
| --- | --- | --- | --- |
| SIG-001 | navigation renderer | `build_publication_navigation(layouts: list[dict[str, Any]], paths: DigestPaths, publication: PublicationContract, *, topic_universe: set[str] | None = None, source_index: dict[str, Any] | None = None) -> list[dict[str, Any]]` | A-001 |
| SIG-002 | topic layout | `build_topic_layouts(drafts: list[dict[str, Any]], paths: DigestPaths, roots: tuple[str, ...], *, max_lines: int, publication: PublicationContract | None = None) -> list[dict[str, Any]]` | A-002 |
| SIG-003 | provenance gate | `validate_prewrite_provenance(source_manifest: dict[str, Any], snapshots: list[dict[str, Any]], source_audit_ledger: list[dict[str, Any]], claims: list[dict[str, Any]], planned_writes: list[dict[str, Any]]) -> None` | A-003 |
| SIG-004 | formal pipeline | `audit_run(paths: DigestPaths, settings: DigestSettings, roots: tuple[str, ...] = DEFAULT_ROOTS, *, dry_run: bool, generator: Any = None, allowed_content_paths: set[str] | None = None, cluster_plan: list[dict[str, Any]] | None = None, global_duplicates: dict[str, dict[str, str]] | None = None) -> tuple[Path, str]` | A-004 |
| SIG-005 | stable identity | `source_id(source_uri: str) -> str`; `resolve_topic_identity(topic_index: dict[str, object], *, stable_topic_id: str, source_ids: Iterable[str], category_id: str, title: str, topic_dir: str) -> dict[str, object]` | A-005 |
| SIG-006 | TopicIndex validator | `validate_topic_index(value: Any) -> dict[str, Any]` | A-006 |
| SIG-007 | JSONL reader | `read_jsonl(path: Path) -> list[dict[str, Any]]` | A-007 |
| SIG-008 | CLI offline entry | `build_parser() -> argparse.ArgumentParser`; `main(argv: list[str] | None = None) -> int`; existing `--no-llm` sets `llm_enabled=False` | A-009 |

## 12. Rollback and Recovery

- **Global recovery rule**：只删除/恢复当前隔离 fixture 的新输出；保留 accepted `spec.md`、entry backfill、旧 Reader/Audit 和 review records；不执行 `git reset`、宽泛删除或正式 KB 写回。
- **Irreversible boundaries**：vendor 外部代码进入仓库、PyYAML 依赖锁定、根 `okf_version` 宣称和后续正式 CLI 接入；本任务只允许前两项在 build-code 通过审查后落地，后两项仍受 smoke/后续 Task 门禁约束。
- **Recovery owner**：build-code 恢复 fixture/output 和锁文件；verify-code 复核当前 snapshot；产品维护者在 Task 3 前处理 OPEN-03。无固定 parser 或 raw corpus 时由 build-code STOP，不自行降级需求。

### Engineering Risk Handoff

- **PLAN-RISK-001**：parser commit 未固定
  - **Affected IDs**：OPEN-01、PFACT-007、FR-SMOKE-001/002、AC-08
  - **Trigger**：无法在无网络环境验证 vendor 文件与一个明确 commit 一致。
  - **Consequence**：不能证明外部互操作；继续写 `okf_version` 会造成虚假兼容声明。
  - **Mitigation or STOP**：优先核验研究候选 `930b65fc...`；失败则 STOP/降级 OKF-inspired，exit manifest 写原因。
  - **Handling Stage**：`build-code`
  - **Verification**：`ORACLE-OKF-SMOKE`、exit manifest parser source/commit/bundle hash 三者闭合。
- **PLAN-RISK-002**：真实 fixture 原文不可访问
  - **Affected IDs**：OPEN-02、PFACT-008、FR-FIX-001/002、AC-03
  - **Trigger**：`KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置、样本片段无法按 URI/fingerprint 回查或 claim 不唯一。
  - **Consequence**：attribution fixture 失真，不能用虚构正文补齐 AC-03。
  - **Mitigation or STOP**：停止 T006；要求本机提供原始目录并只提交最小人工 fixture、selection manifest 和 claim 映射。
  - **Handling Stage**：`build-code`
  - **Verification**：`ORACLE-ATTRIBUTION` 逐个 footnote 回查 source/claim/locator/fingerprint。
- **PLAN-RISK-003**：Bundle 输出误接入旧 pipeline
  - **Affected IDs**：R-009、FR-BUNDLE-001/002/003、FR-PROJ-001/002、AC-01/05/07
  - **Trigger**：改动 `pipeline.py`/`cli.py` 或把 isolated output root 指向正式 KB。
  - **Consequence**：旧 Reader/Audit 产物漂移、Task 2-A 越界到 Task 3。
  - **Mitigation or STOP**：文件边界保护；新增 API 只接受显式 output root，测试使用 `tmp_path`。
  - **Handling Stage**：`build-plan` → `build-code`
  - **Verification**：目标文件 diff 与 `DO NOT TOUCH` 对账；旧 Reader 回归测试保持通过。
- **PLAN-RISK-004**：当前 build-plan review 与确认事实缺失
  - **Affected IDs**：F3/F4/F6/F7/F9、Q1/Q2/Q3、stage handoff
  - **Trigger**：当前 task `index.json` 的 reviews 为空，`facts.jsonl` 为空，`quality/verify.json` 的 status 为 `unknown`。
  - **Consequence**：计划可以继续作为工程投影，但不能声称当前 build-plan 已通过正式审查、用户已确认或已获得自动放行。
  - **Mitigation or STOP**：保留 `unknown/incomplete`；下游只消费四份可读材料，缺失 review/confirmation 不伪造；若需要正式完成声明，补充真实 Runner/provider/用户事实。
  - **Handling Stage**：`build-plan`
  - **Verification**：回读 task `index.json`、`facts.jsonl`、`quality/verify.json` 和本计划 Stage Progress；不得引用当前 worktree 不存在的 review result/report。

- **PLAN-RISK-005**：Bundle、Audit、projection report 的写入合同不闭合
  - **Affected IDs**：FR-PROJ-001/002、FR-VALID-001/002、AC-01/02/05/07、T003/T004/T008
  - **Trigger**：API 只收到 bundle output，却把 report/audit 写到隐式路径，或 validator 不读取同次运行的 audit/report。
  - **Consequence**：degraded 对账、回滚边界和写入 containment 不可证明；可能越过 artifact root 或漏校验失败页。
  - **Mitigation or STOP**：只接受 `BundleArtifactPaths`；同一 root 固定含 `bundle/`、`audit/`、`reports/`；validator 对三者做一一对账；缺任一 consumer/路径拒绝规则即 STOP。
  - **Handling Stage**：`build-plan` → `build-code`
  - **Verification**：`ORACLE-ARTIFACT-CONTAINMENT`；越界、symlink、缺 report、缺 degraded target 的负例均非零失败。
- **PLAN-RISK-006**：TopicIndex/entry/claim schema 只写名称不写字段合同
  - **Affected IDs**：FR-FRONT-003、FR-ATTR-001/002、FR-PROJ-001/002、FR-SMOKE-001、AC-02/03/06/08、T003–T008
  - **Trigger**：adapter 直接消费未验证 dict，或用 synthetic minimal manifest 代替当前 v2/entry/claim records。
  - **Consequence**：测试可能只证明文件存在，身份、证据、claim locator 和 parser input 漂移被隐藏。
  - **Mitigation or STOP**：固定 `reader-bundle-inputs.v1`、TopicIndex `2.0.0` field table、ArtifactRef hash/version 和 claim required fields；先调用 `validate_topic_index`；unknown/missing field 明确拒绝。
  - **Handling Stage**：`build-plan` → `build-code`
  - **Verification**：`ORACLE-INPUT-ADAPTER`；真实 Task 1 backfill readback 与 fixture oracle 同时通过，schema mutation 非零失败。
- **PLAN-RISK-007**：AC-07 被 API guard 冒充真实 `--no-llm` 运行证据
  - **Affected IDs**：FR-LLM-001、AC-07、T003/T004/T008
  - **Trigger**：测试不调用现有 `cli.main`/`digest --no-llm`，只 monkeypatch Bundle API provider。
  - **Consequence**：不能证明用户实际离线路径未触网；AC-07 可能被过弱证据满足。
  - **Mitigation or STOP**：在 Bundle gate 中运行现有 CLI `--no-llm`，由 acceptance fixture 在调用边界做本地 socket/provider 拦截并读取真实 runtime audit；API 不新增生产级 guard，不能替代 CLI oracle。
  - **Handling Stage**：`build-code`
  - **Verification**：`ORACLE-CLI-OFFLINE`；CLI report 的 `calls.llm=0`、`calls.embedding=0`，并由测试边界 deny-only socket guard 证明未触网；Bundle manifest 为 `not_released`。
- **PLAN-RISK-008**：入口 backfill 被 synthetic fixture 掩盖
  - **Affected IDs**：FR-ENTRY-001、AC-02、T003/T004
  - **Trigger**：测试只在 `tmp_path` 构造最小 backfill，未回读当前 backfill 的 refs/hash/version/coverage。
  - **Consequence**：当前 Task 0/1 控制面是否可消费没有证据；AC-02 假绿。
  - **Mitigation or STOP**：只读验证 `quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`、Task1 `source-inventory/topic-index/run-report/verification-receipt` 的声明 hash 与实测 hash；缺失或不符 STOP。
  - **Handling Stage**：`build-code` / `verify-code`
  - **Verification**：`ORACLE-ENTRY-READBACK`；真实 refs、hash、schema/version、source/topic coverage 闭合后才计入 AC-02。
- **PLAN-RISK-009**：parser 降级事实被误报为 AC-08 GREEN
  - **Affected IDs**：OPEN-01、PFACT-007、FR-SMOKE-001/002、AC-08、T007/T008
  - **Trigger**：vendor commit/license/read smoke 未闭合，但测试用 downgrade output 作为 parser compatibility GREEN。
  - **Consequence**：对外命名和完成状态不一致，可能错误写 `okf_version` 或宣称 OKF-compatible。
  - **Mitigation or STOP**：完整 failed/unavailable 事实走 `honest_downgrade_passed`，验证省略字段和原因；只有固定 bytes、commit、license/notice、bundle hash 和 parser read-boundary 全闭合才标 `compatibility_passed`；AC-07 另需现有 CLI runtime audit 的 `calls.llm=0`、`calls.embedding=0`，并由测试边界 deny-only socket guard 证明未触网；任一事实缺失仍 STOP/blocked。
  - **Handling Stage**：`build-code` / `verify-code`
  - **Verification**：`ORACLE-OKF-SMOKE`；固定 parser GREEN exit `0`；缺固定 parser 只能保留 blocked evidence。
- **PLAN-RISK-010**：真实 raw corpus 不可访问导致 fixture/attribution 伪造
  - **Affected IDs**：OPEN-02、PFACT-008、FR-FIX-001/002、FR-ATTR-001/002、AC-03、T005/T006
  - **Trigger**：`KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置、片段无法回查或 claim 不唯一。
  - **Consequence**：三类 fixture 不具备真实 URI/fingerprint/locator 闭合，不能证明 attribution。
  - **Mitigation or STOP**：保留 T005/T006 STOP；提供受控 raw corpus 后再人工选样并记录 selection hash；不得用虚构正文关闭 AC-03。
  - **Handling Stage**：`build-code`
  - **Verification**：`ORACLE-ATTRIBUTION`；三类 fixture 每个 footnote 唯一回查 source/claim/locator/fingerprint 和 audit record。
- **PLAN-RISK-011**：结构 projection 把 attribution required inputs 提前硬编码
  - **Affected IDs**：FR-ATTR-001/002、FR-FIX-001/002、AC-02/03/05/06、T003–T006
  - **Trigger**：T003/T004 用 synthetic claim/fixture 填满完整 schema，或结构 GREEN 被当成真实 attribution GREEN。
  - **Consequence**：结构证据与真实 claim chain 混淆，AC-03 可能假绿。
  - **Mitigation or STOP**：T003/T004 只消费 `ReaderBundleStructureInputs`；T005/T006 才消费完整 `ReaderBundleInputs`；synthetic 只测拒绝分支，真实 corpus 缺失时 STOP。
  - **Handling Stage**：`build-plan` → `build-code`
  - **Verification**：`ORACLE-INPUT-ADAPTER`、`ORACLE-ATTRIBUTION`；结构报告不能含 attribution passed 计数。
- **PLAN-RISK-012**：TopicIndex 当前身份字段与旧 identity validator 不同
  - **Affected IDs**：FR-BUNDLE-005、FR-FRONT-004、FR-PROJ-002、AC-02/05/06、T003/T004
  - **Trigger**：把当前 `topic_id=v2/...` 当作旧 `topic-*`，或把 product-only row 强行补 module/category。
  - **Consequence**：修改旧 schema、身份漂移或虚构目录层级。
  - **Mitigation or STOP**：先校验公共 v2 字段并进入显式 product-only adapter；v2 以 `digest_topic_id → topic_id → topic_key` 归一，legacy 才复用 `resolve_topic_identity`；adapter 只适配 legacy module-only 约束，不跳过其他 validator 规则；合法 product-only 不丢失 source/identity、不造 module，malformed/unsupported/uncertain 才 degraded。
  - **Handling Stage**：`build-code`
  - **Verification**：`ORACLE-INPUT-ADAPTER`、`ORACLE-REPLAY`；重复输入身份和 path 必须稳定。
- **PLAN-RISK-013**：输入 resolver 或 result schema 不完整导致隐式路径/不完整报告
  - **Affected IDs**：FR-PROJ-001/002、FR-VALID-001/002、FR-ENTRY-001、FR-SMOKE-001/002、AC-02/05/06/07/08、T003/T004/T008
  - **Trigger**：ref 依赖 cwd，或 report/smoke result 缺 schema、license/notice provenance、consumer 字段。
  - **Consequence**：无法证明读取边界、兼容来源或 degraded 对账闭合。
  - **Mitigation or STOP**：显式 `input_root`/resolver；固定 `ArtifactRef`、`BundleReport`、`BundleValidationReport`、`ParserSmokeResult` field table 和拒绝规则；缺字段立即 STOP。
  - **Handling Stage**：`build-code` / `verify-code`
  - **Verification**：`ORACLE-INPUT-ADAPTER`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-OKF-SMOKE`。
- **PLAN-RISK-014**：重复投影或中途失败留下半套 artifact 或第二事实源
  - **Affected IDs**：FR-PROJ-001/002、FR-VALID-001/002、AC-05/06/07/08、T004/T008
  - **Trigger**：复用非空 root、直接写正式路径，或把 evidence copy 当 API source of truth。
  - **Consequence**：Bundle/Audit/Report 不一致，失败恢复和 replay 不可判定。
  - **Mitigation or STOP**：fresh empty non-symlink root、调用方单写者/串行边界、run-scoped staging、验证后 atomic commit；artifact_root reports 是唯一事实源，evidence copy 必须 hash/readback；非空 root/复用/失败 partial write 负例必须失败，不引入 owner marker 或并发协议。
  - **Handling Stage**：`build-code` / `verify-code`
  - **Verification**：`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-REPLAY`；测试证明 fresh root、root reuse、staging/partial-write recovery 和失败后正式 root 不变。

### Task0/Task1 handoff

T003/T004 必须先只读回读当前 Task 2-A entry backfill 与 Task 1 control-plane artifacts，再在 `tmp_path` 生成 synthetic negative cases。真实 refs/hash/version/coverage 不闭合时，T003/T004 的 structural fixture 仍可用于错误分支，但 AC-02 和 build-code handoff 保持 STOP；verify-code/operator 不能用临时 receipt 冒充真实入口事实。

## 13. Current build-plan review dispositions

本轮 `plan-eng-review` 的结果是 advisory，已逐项采纳其可修正项：

- `PLAN-ENG-R3-001`：接受；本次 plan 改完后由正式 `spec-tasks` producer 重算 tasks header 与 T001–T008 的 current plan SHA-256，未重绑前不得 handoff。
- `PLAN-ENG-R3-002/003`：接受；新增逐项 entry binding 表、父 receipt 版本规则、`check_entry_bindings` 和 `write_entry_backfill_manifest`，缺事实时只产出 `not_released` backfill/blocked evidence。
- `PLAN-ENG-R3-004/005`：接受；新增 `ParserVendorRef`/`ParserSmokeAttempt` producer 合同和命名的 `adapt_topic_index_row` product-only/standard adapter、rejection codes。
- `PLAN-ENG-R3-006`：接受；冻结现有 `uv run --frozen digest ... --no-llm` 的 argv、临时 input/output、runtime audit 和测试边界 deny-only guard；Bundle API 仍不扩展正式 CLI。
- `PLAN-ENG-R3-007/008`：接受；增加 `CommittedBundleRun`、validator-before-commit、base hash/recovery gate，并把 AC-08 固定为 compatibility/downgrade 的排他 OR aggregate，blocked 不计通过。
- `PLAN-ENG-R3-009`：接受；T002 增加 `uv lock --check` 与运行时 `PyYAML==6.0.2` 的独立 dependency gate/evidence。
- `INPUT-ACCEPTANCE-R3-001`：保留为开放输入门；spec 的 `v1-draft`、当前 review/facts 缺失和用户尚未确认 build-code handoff 不改写成通过。`INPUT-STOP-R3-001` 同样保留：raw corpus、vendor、实现和测试缺失时 T005/T006/T008 继续 `blocked-by-design`。

下一步必须重新运行 `spec-tasks`、`spec-analyze` 和正式 `wh-review`，并以修订后的 plan/tasks 当前快照生成组件 receipts；旧 review 结果只能作为审计，不能替代新快照。

## 13. Test Strategy

> 行为改动均先 RED 后 GREEN；每一对使用相同 `gate_cmd` 和 oracle identity。Phase 1/2/3 与 final 暂按跨 `src`、`tests`、`pyproject/uv.lock` 或 vendor 根的 `fullstack` 复杂度设计；具体 routing 由 build-code 按真实 changed files 重新核对，本阶段不把预判写成已执行结果。

Spec 中 `--no-llm` 的 acceptance 语义必须经过现有 `cli.main`/`digest` `--no-llm` 真实路径；测试 fixture 在该调用周围启用本地 socket/provider 拦截并读取既有 runtime audit。Bundle API 不新增生产级 guard；该 fixture 只能补充隔离 projection 证据，不能替代 CLI oracle；本 Task 不新增 CLI flag。

### AC-07 concrete command and producer boundary

Bundle projection 与既有 CLI offline audit 是同一 acceptance fixture 的两个明确步骤，不把 CLI 偷换成新的 Bundle CLI，也不把 Bundle API guard 当作 CLI 事实源。测试先在 `tmp_path` 写固定的 `offline.json`（`similarity.backend=jaccard`、`llm_enabled=false`、`llm_summary_enabled=false`），再执行：

```text
uv run --frozen digest <tmp>/new <tmp>/cli-kb --config <tmp>/offline.json --no-llm
```

其中 `<tmp>/new/items/note.md` 与 `<tmp>/new/sources.jsonl` 是测试创建的最小本地输入；expected exit 为 `0`；唯一 CLI output 是 `<tmp>/cli-kb/_digest/runs/<run_id>/report.json`，其 `runtime_audit.calls` 必须严格为 `{"llm": 0, "embedding": 0}`、`status.delivery_status=not_released`、`provider_transport=not_requested`。同一测试随后以 `offline_mode="no-llm"` 调用 `project_reader_bundle(...)`，验证 `<tmp>/artifact-root/bundle`、`audit` 和 `reports/projection-report.json`；Bundle API 的 output 不从 CLI report 猜路径或复制 source truth。

acceptance 边界的 deny-only socket guard 由 `tests/acceptance/test_task2a_reader_bundle.py` 自己安装，只允许记录 `attempt_ref`、argv hash、guard mode 和 `connect_attempts=0` 到 `quality/evidence/task2a-reader-bundle/cli-offline-guard.txt`；它在第一次连接尝试时立即抛错，不做生产计数器，不向 `reader_bundle`/`okf_smoke` 传入 `SmokeContext`。缺 CLI report、audit、guard receipt 或任一 calls 非零时，AC-07 为 STOP。

- **Target**：FR-FRONT-001/002/005、FR-PROJ-002、AC-02（frontmatter parse/field legality portion）、AC-06。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`。
- **dependency_gate_cmd**：`uv run --frozen python -c "import pathlib, tomllib, yaml; p=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); assert p['project']['dependencies'].count('PyYAML==6.0.2') == 1; assert yaml.__version__ == '6.0.2'"`；同时用 `uv lock --check` 验证 `uv.lock` 与 `pyproject.toml` 一致。
- **expected_exit**：RED `1`；GREEN `0`。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/frontmatter-{red,green}.txt`、`quality/evidence/task2a-reader-bundle/pyyaml-lock.txt`。
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_reader_frontmatter.py -q -vv`。
- **Oracle ID and result**：`ORACLE-FM-ROUNDTRIP`；未知 nested field、sources/generated/verified 和受管 hash 规则在 parse→dump→parse 后保持，易变字段改动不改变受管 hash；AC-02 的 frontmatter parse/field legality portion 在此门通过，concept mapping 由 Phase 2 门继续验证。

- **Target**：FR-BUNDLE-001/002/003/005/006、FR-FRONT-003/004/006、FR-STATUS-001/002/003、FR-VALID-001/002、FR-ENTRY-001、FR-PROJ-001/002、FR-LLM-001、AC-01/02/04/05/06/07。
- **AC-01 层级解释**：产品/模块/主题中的“主题”层由 `products/{product}` 下的 concept pages 实现；本 Task 不生成独立的 `topics/` 目录。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q`。
- **expected_exit**：RED `1`；GREEN `0`。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/bundle-{red,green}.txt`、`projection-report.json`。
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q -vv`。
- **Oracle ID and result**：`ORACLE-BUNDLE-TREE`、`ORACLE-STATUS`、`ORACLE-LINKS`、`ORACLE-REPLAY`、`ORACLE-OFFLINE-RELEASE`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-INPUT-ADAPTER`、`ORACLE-ENTRY-READBACK`、`ORACLE-ENTRY-BACKFILL`、`ORACLE-CLI-OFFLINE`；显式核验根 `log.md` 的 status/change summary，且只有根目录有 `log.md`、nested directory 出现 `log.md` 即失败；先读取真实 backfill 与 Task1 control-plane refs，逐项校验声明 hash 与实测 hash、schema/version、producer receipt、consumer、source/topic coverage，再执行 projection；缺入口项必须由 `write_entry_backfill_manifest` 在 staging 生成 `reader-bundle-entry-backfill.v1`，不允许用 synthetic row 填充正式输入。synthetic minimal manifests 只能覆盖拒绝分支。TopicIndex 派生 concept 必须按固定 mapping 验证：`products` + 产品定位/边界 → `product_overview` → `KnowledgeDigest Product Overview`，`products` + 模块/能力/入口 → `module_or_capability` → `KnowledgeDigest Module or Capability`，`products` + 步骤/规则/异常 → `procedure_or_rule` → `KnowledgeDigest Procedure or Rule`，非 `products`/未注册/无证据/冲突 → degraded。index 必须无空入口，`Home.md` 只能指向根 `index.md`，错误目标和空入口均为负例；每个 `index.md` 只能列可读 title 与恰好一行 description，不得写正文 body；嵌套保留名 `index.md` 或 `log.md` 若带 concept frontmatter 或被当作 concept page，必须明确拒绝。title/description（来源 metadata、frontmatter、H1、文件名顺序必须有单测）；`digest_topic_key`/`digest_topic_id`/path 一致性、同一 TopicIndex 重放时 `digest_topic_id` 不变、无 module 不造 module。product-only 统一调用 `adapt_topic_index_row`，正例与 rejection codes 负例必须同 gate；版本冲突、无 title/description、无证据的 verified、无 freshness 证据的 stale_after、agent_assisted→human: 和 artifact root 越界均拒绝；degraded record 必须同时有 projection report 字段和 `artifact_root/audit/_digest/degraded/{stable_id}.md`，且不进 Reader index。测试还必须调用现有 CLI `--no-llm`，核对 runtime audit 的 `calls.llm=0`、`calls.embedding=0`，并由测试边界 deny-only socket guard 证明未触网；API guard 不能单独满足 AC-07。
- **Aggregate completeness/STOP**：该定向命令是唯一正式 aggregate；只有真实 changed-file routing 完成、当前 plan/tasks receipt 与材料 hash 匹配、当前 review/confirmation 缺失被如实保留、AC-03/AC-08 的 blocked 输入未被伪造关闭、所有专项 gate exit 为 0、现有 CLI runtime audit 的 `calls.llm=0`、`calls.embedding=0` 且测试边界 deny-only socket guard 证明未触网、diff 未越过 Phase Files/DO NOT TOUCH 时才可写 aggregate GREEN。网络 guard 只能作为独立 evidence，不能变成生产 API counter contract。evidence 必须记录 command、exit、oracle、current snapshot、coverage limits、STOP 判定和 SHA-256；full-tree pytest 只作诊断。

- **Target**：FR-ATTR-001/002、FR-FIX-001/002、FR-FRONT-003、FR-VALID-001、FR-PROJ-002、AC-02/03/05/06。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q`。
- **expected_exit**：RED `1`；GREEN `0`。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/attribution-{red,green}.txt`。
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q -vv`。
- **Oracle ID and result**：`ORACLE-ATTRIBUTION`、`ORACLE-AUDIT-CLAIM-EVIDENCE`、`ORACLE-REPLAY`；三张 fixture 必须恰好覆盖固定三类完整字面值和 mapping，每张均有合法 `digest_*`/path identity；所有 footnote 唯一回查 `sources[].id`、`claim_id`、`fragment_locator`、URI 和 fingerprint，并继续回查 audit claim/evidence 完整记录；`references/sources.md` 只能投影同一组 source IDs，不能新增第二 source ID、第二 footnote target 或完整 audit snapshot；重复 projection、unknown extension 和受管 hash replay 断言必须在同一 gate 中执行。

- **Target**：FR-BUNDLE-004、FR-SMOKE-001/002、AC-08。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_compatible`。
- **downgrade_gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_downgrade`；这是独立的合法降级门，不与 compatibility GREEN 混用。
- **expected_exit**：RED `1`；GREEN `0`。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/smoke-red.txt`、`quality/evidence/task2a-reader-bundle/smoke-downgrade-red.txt`、`quality/evidence/task2a-reader-bundle/smoke-green.txt`、`quality/evidence/task2a-reader-bundle/smoke-downgrade-green.txt`、`quality/evidence/task2a-reader-bundle/exit-manifest.json`。
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_okf_smoke.py -q -vv`。
- **Oracle ID and result**：`ORACLE-OKF-SMOKE`；`-k parser_compatible` 的 RED 与 GREEN 使用同一 `gate_cmd`/oracle：vendor 缺失、bytes/hash/commit/license/notice 不闭合或 parser 无法读取时 RED 非零；闭合后 compatibility GREEN 为 0，并且 `exit-manifest.json` 记录 source/commit/vendor/license/notice hash/bundle hash/read-boundary 结果。生产 smoke API 不接收 `SmokeContext` 或 counter 参数；`--no-llm` 的 `calls.llm=0`、`calls.embedding=0` 由现有 CLI runtime audit 负责，未触网由 acceptance 边界 deny-only socket guard 证明。另有 `ORACLE-OKF-DOWNGRADE` 场景验证 smoke failed/unavailable 且 source/attempt/reason/bundle provenance 完整时 profile 为 `OKF-inspired profile`、根 `index.md` 省略 `okf_version`、`ac08_result=honest_downgrade_passed` 并记录原因；缺事实或结果含糊才 blocked。嵌套 `index.md` 始终省略 `okf_version`，index 标题不得为 hash。
- **AC-08 aggregate rule**：compatibility gate 与 downgrade gate 都单独执行并各自写 evidence；最终 AC-08 只有 `compatibility_passed OR honest_downgrade_passed` 为真才通过，且两者都排除 `blocked`。若 compatibility 失败但 downgrade 通过，aggregate 选择 `smoke-downgrade-green.txt` 与对应 exit manifest；若 compatibility 通过，优先选择 compatibility evidence；若两者均失败、任一合法路径缺 provenance、或只有 blocked 结果，aggregate 非零并保留 STOP。该 OR 只用于 AC-08，不改变包级 `not_released`。

- **Target**：全部 AC-01–AC-08、既有 Reader 不回归。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_frontmatter.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2a_okf_smoke.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task1_topic_axis.py -q`。
- **expected_exit**：0。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/final-aggregate.txt`。
- **display_cmd**：`uv run --frozen pytest tests/ -q`。
- **Oracle ID and result**：`ORACLE-TASK2A-AGGREGATE`；新 Bundle 8 AC 闭合，旧 Reader/Task 1 核心行为未漂移；full tree 仅作 final build-code/verify-code 回归，不替代专项 gate。

## 14. Implementation Order

1. T001/T002：固定 PyYAML、frontmatter parse/dump/hash；所有后续模块只能调用这一边界。
2. T003/T004：先只读回读真实 entry backfill/Task1 refs，再固定 versioned input adapter、Bundle tree、concept mapping、状态/路径/allowlist、artifact root 和 projection report；先有 producer contract 再验证 consumer。
3. T005/T006：从原始样本选择三类 fixture，闭合 footnote→source→claim，验证幂等和 source projection。
4. T007/T008：先写 parser compatibility RED，再固定 vendor parser，跑零网络 smoke，并把 passed/failed/unavailable 事实接到 profile/name/exit manifest；完整 failed/unavailable 事实按 accepted 口径形成 honest downgrade，事实缺失保持 blocked。
5. Final aggregate：重跑专项 acceptance、旧 Reader/Task 1 回归和 full tree；不新增产品范围，不在本阶段做 release。

## Phase 1：Frontmatter 与受管 hash

### Goal

在不影响旧 Reader 的前提下，提供固定 PyYAML nested frontmatter round-trip 和受管 `digest_content_hash`。

### Files

- **NEW**：`src/knowledge_digest/reader_frontmatter.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`
- **MODIFY**：`pyproject.toml`; `uv.lock`
- **DO NOT TOUCH**：`src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `tests/acceptance/test_task0_reader_package.py`; `tests/acceptance/test_publication_contract.py`; `tests/acceptance/test_task1_topic_axis.py`

### Tasks

- T001：添加可执行 RED 和最小 importable contract stub，证明 nested round-trip/hash 断言当前失败。
- T002：锁定 `PyYAML==6.0.2`，实现 safe parse/dump/hash，GREEN 通过并保持未知字段。

### Verify

`ORACLE-FM-ROUNDTRIP`；`pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`；evidence `frontmatter-{red,green}.txt`。
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；build-code 按真实 changed files 重判。
- **fixtures_services**：`tmp_path`，无服务、无网络、无 provider。
- **coverage limits**：只覆盖 nested frontmatter round-trip/hash；不覆盖 Bundle path/status、fixture attribution、parser smoke。
- **STOP**：命令/setup/import 错误不能替代目标断言；不得修改旧 frontmatter/parser。

### Knowledge

现有 `kb_structure._frontmatter_lines/_frontmatter_values` 是简单行解析；accepted spec 明确要求 nested PyYAML safe API 和固定 serializer 参数。

### STOP

PyYAML 不能锁定、测试失败来自环境/命令而非目标断言、serializer 丢 nested/unknown fields、或修改旧 frontmatter/parser 文件。

### Done

`reader_frontmatter.py` API 固定；PyYAML 和 `uv.lock` 一致；round-trip/hash/status tests GREEN；旧测试未被修改。

### Risks and rollback

- **Risk**：serializer 参数漂移或 hash 包含易变字段。
- **Prevention**：常量化参数与受管字段白名单，固定 oracle。
- **Rollback / recovery**：撤回当前新增模块和 dependency lock 变更；不碰旧 Reader 文件。

## Phase 2：隔离 Bundle projection、validator 与 attribution fixture

### Goal

在 `tmp_path` output root 生成固定 Reader Bundle tree、三类真实样本 fixture、source projection、结构 validator 和 `not_released` projection report。

### Files

- **NEW**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; `tests/fixtures/task2a_reader_bundle/topic-index.json`; `tests/fixtures/task2a_reader_bundle/source-inventory.jsonl`; `tests/fixtures/task2a_reader_bundle/claim-history.jsonl`; `tests/fixtures/task2a_reader_bundle/fixture-selection.json`; `tests/fixtures/task2a_reader_bundle/product-overview.md`; `tests/fixtures/task2a_reader_bundle/module-capability.md`; `tests/fixtures/task2a_reader_bundle/procedure-rule.md`
- **MODIFY**：N/A — reader bundle is created in this Phase and only integrated with parser result in Phase 3；report/manifest 的 product output 只存在于运行时 artifact root，不直接写固定 evidence 目录
- **DO NOT TOUCH**：`src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `src/knowledge_digest/kb_structure.py`; `src/knowledge_digest/identity.py`; `tests/acceptance/test_task0_reader_package.py`; `tests/acceptance/test_publication_contract.py`; `tests/acceptance/test_task1_topic_axis.py`; `quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`; `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`; `quality/evidence/task2-entry/task1-receipt-reconciliation.v1.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/source-inventory.jsonl`; `quality/evidence/task2-entry/task1-real-corpus-20260806/topic-index.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/topic-plan.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/run-report.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/verification-receipt.json`

### Tasks

- T003：添加 Bundle tree/type/status/path/allowlist/entry-readback/CLI-offline RED，覆盖 AC-01/02/04/05/06/07；显式锁定 replay identity、artifact containment 和真实 `--no-llm` 负例。
- T004：实现 versioned input adapter、显式命名的 `adapt_topic_index_row` product-only/standard 分支、`check_entry_bindings`/`write_entry_backfill_manifest`、explicit artifact-root `project_reader_bundle`/`validate_reader_bundle` 和 projection report；validator `status=passed` 是 initial commit 的硬前置，成功后返回带三项 base hash 的 `CommittedBundleRun`；synthetic entry 只用于拒绝分支。
- T005：添加 attribution/fixture/idempotence RED，证明三类固定 type/mapping、footnote/source/claim 回查和重复运行当前失败，覆盖 AC-02/03/05/06。
- T006：从 20 个真实预检样本人工选三类 fixture，闭合三类 type/mapping、attribution、source projection 和 replay，GREEN 通过，覆盖 AC-02/03/05/06。

### Verify

`ORACLE-BUNDLE-TREE`、`ORACLE-STATUS`、`ORACLE-LINKS`、`ORACLE-REPLAY`、`ORACLE-ATTRIBUTION`、`ORACLE-OFFLINE-RELEASE`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-INPUT-ADAPTER`、`ORACLE-ENTRY-READBACK`、`ORACLE-ENTRY-BACKFILL`、`ORACLE-CLI-OFFLINE`、`ORACLE-FINALIZE-RECOVERY`；`pytest tests/acceptance/test_task2a_reader_bundle.py -q`；evidence `bundle-red.txt`、`bundle-green.txt`、`entry-backfill-{red,green}.txt`、`attribution-red.txt`、`attribution-green.txt`，以及 artifact root 内的 `reports/projection-report.json`、`audit/entry-backfill/{run_id}.json` 与 `audit/_digest/degraded/{stable_id}.md` 的复制/哈希/回读 receipt；GREEN 必须证明真实 entry refs/hash/version/coverage 回读、三类固定 type/mapping（raw corpus 可用后）、nested `log.md` 禁止、artifact containment 和 degraded page/report 一一对应，并在现有 CLI `--no-llm` 加 socket/provider guard 下证明 runtime audit 的 `calls.llm=0`、`calls.embedding=0` 且未触网，否则失败。`project_reader_bundle` 只有在 validator passed 后提交并返回 `CommittedBundleRun`；坏 smoke provenance、validator failure 和 base-hash mismatch 的 finalize recovery 必须证明旧 Bundle/report/manifest SHA-256 不变。raw corpus 缺失时 T005/T006 保持 STOP，不能生成虚构 fixture 或关闭 AC-03。
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；build-code 按真实 changed files 重判。
- **fixtures_services**：local structural fixture + `tmp_path`；真实 entry refs 只读；无服务、无网络、无 provider。
- **coverage limits**：覆盖 Bundle tree/status/link/adapter/entry readback/CLI offline；不覆盖 external parser 或完整真实 attribution。
- **STOP**：raw corpus 缺失、product-only 正向路径未通过、真实入口回读缺失、或正式 CLI 路径未执行时，不写 GREEN。

### Knowledge

Task 1 backfill 的 `topic-index.json` 是 v2 控制面；现有 `identity.py` 提供稳定 source/topic identity；`CONTEXT.md` 已锁定 Reader Bundle 豁免清单与 `references/sources.md`。

### STOP

raw corpus 未由 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 提供、fixture 片段无法回查、任何 degraded 页进入 Reader index、path/symlink/allowlist/link 检查不明确、或需要修改正式 pipeline/CLI。

### Done

三类 fixture 和 selection manifest 可追溯；Bundle tree、frontmatter、status、source projection、links、entry backfill、幂等和 zero-provider 事实均通过专项测试；包级状态保持 `not_released`。

### Risks and rollback

- **Risk**：fixture 选择把结构验证误写成语义质量，或 product/module 归属漂移。
- **Prevention**：fixture 只写人工片段和 attribution；使用 TopicIndex v2/固定 mapping；selection reason 可回放。
- **Rollback / recovery**：删除本 Phase 隔离 fixture/output evidence，保留 raw/Task 0/1 facts；不删除旧 Reader/Audit。

## Phase 3：外部 OKF parser smoke 与 profile 降级

### Goal

vendor 固定 commit 的官方最小 parser 读取 Bundle；smoke pass 才声明 `OKF-compatible`/`okf_version: "0.2"`，否则结构化降级到 `OKF-inspired profile`。

### Files

- **NEW**：`src/knowledge_digest/okf_smoke.py`; `tests/acceptance/test_task2a_okf_smoke.py`; `tests/vendor/okf_reference_agent/__init__.py`; `tests/vendor/okf_reference_agent/bundle/__init__.py`; `tests/vendor/okf_reference_agent/bundle/document.py`; `tests/vendor/okf_reference_agent/bundle/index.py`; `tests/vendor/okf_reference_agent/bundle/paths.py`; `tests/vendor/okf_reference_agent/LICENSE`; `tests/vendor/okf_reference_agent/NOTICE.md`; `tests/vendor/okf_reference_agent/README.md`
- **MODIFY**：`src/knowledge_digest/reader_bundle.py`（仅 profile/smoke integration region）
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/identity.py`; `src/knowledge_digest/kb_structure.py`; `tests/acceptance/test_task0_reader_package.py`; `tests/acceptance/test_publication_contract.py`; `tests/acceptance/test_task1_topic_axis.py`; `quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`; `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`; `quality/evidence/task2-entry/task1-receipt-reconciliation.v1.json`

### Tasks

- T007：添加 parser pass/downgrade RED，要求 smoke result 驱动 `okf_version` 与 exit manifest。
- T008：核验并 vendor 固定 parser commit，冻结 `ParserVendorRef`/`ParserSmokeAttempt`，实作零网络 smoke、profile integration 和 exit manifest；compatibility evidence 全闭合时标 `compatibility_passed`，完整 failed/unavailable provenance 时标 `honest_downgrade_passed`；无法建立任一事实链才 blocked，始终 STOP OKF-compatible 宣称直到 compatibility pass。T008 消费 T004 的 `CommittedBundleRun`，并在坏 provenance、validator failure、base-hash mismatch 下执行 `parser_finalize_recovery`，证明正式 Bundle/report/manifest 不变。

### Verify

`ORACLE-OKF-SMOKE`、`ORACLE-OKF-DOWNGRADE`、`ORACLE-FINALIZE-RECOVERY`；compatibility 使用 `pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_compatible`（RED 非零、GREEN 0），降级使用独立的 `pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_downgrade`（完整 failed/unavailable provenance 时 exit 0、`honest_downgrade_passed`），恢复使用 `pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_finalize_recovery`。evidence `smoke-red.txt`、`smoke-green.txt`、`smoke-downgrade-green.txt`、`parser-finalize-recovery-{red,green}.txt`、`exit-manifest.json`。AC-08 aggregate 唯一判定为 `compatibility_passed OR honest_downgrade_passed`，两者都排除 `blocked`；compatibility 通过优先绑定 compatibility evidence，否则绑定 downgrade evidence；两个 gate 都失败或 provenance 不完整时 aggregate 非零。缺事实才 blocked。
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；build-code 按真实 changed files 重判。
- **fixtures_services**：vendored parser files + `tmp_path`；socket/provider guard；无网络、无外部服务。
- **coverage limits**：只覆盖 vendor provenance、parser read smoke、profile/manifest、CLI `calls.llm`/`calls.embedding` audit 和 deny-only socket guard 引用；不覆盖 semantic body、Task 2-B/2-C 或 release。
- **STOP**：vendor provenance、parser read-boundary、CLI `calls.llm`/`calls.embedding` audit 或 deny-only socket guard evidence 不完整、parser 触网、或失败仍写 `okf_version` 时停止；完整 failure 只能走 honest downgrade。

### Knowledge

官方研究已核实 `document.py/index.py/paths.py` 最小读取面和 Apache-2.0；最终 commit 仍是 OPEN-01，不能把研究 commit 当作已 vendor 事实。

### STOP

vendor 文件与 commit 不一致、license/notice 缺失、smoke 触网、parser fail 仍写 `okf_version`、或需要引入完整 Knowledge Catalog/runtime。

### Done

exit manifest 包含 parser source/commit、vendor/license/notice hash、fixture bundle hash、未知扩展/type 行为、读取边界、profile 和 `ac08_result`；固定 parser pass 时 profile/`okf_version`/命名互斥且可重放，完整 smoke failed/unavailable 时留下 `OKF-inspired profile` 的 honest-downgrade evidence，事实缺失才 blocked；CLI runtime audit 的 `calls.llm=0`、`calls.embedding=0` 与测试边界 deny-only socket guard 作为独立验收证据，不写成生产 manifest 计数；所有 Bundle 仍 `not_released`。

### Risks and rollback

- **Risk**：外部代码升级导致 smoke 结果漂移。
- **Prevention**：固定 commit、vendor license/notice、零网络测试和 manifest hash。
- **Rollback / recovery**：保留原始 unavailable/fail evidence，移除当前 vendor/output 变更并回到 OKF-inspired 文档口径；不宣称兼容。

## Phase 4：正向机器信任信号投影与失效校验

### Goal

在不引入 Task 2-C 人工读者门的前提下，让已有三类完整 fixture concept 页真实产生并可回查的 `generated`、`digest_machine_pass`、`source_hash_match`/`locator_resolved` 信号；无 freshness 证据时不生成 `stale_after`，所有 Bundle 继续 `not_released`。

### Files

- **NEW**：N/A — 复用现有 Bundle/frontmatter/acceptance 边界。
- **MODIFY**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`
- **DO NOT TOUCH**：`src/knowledge_digest/reader_frontmatter.py`; `src/knowledge_digest/okf_smoke.py`; `src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/identity.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`; `tests/acceptance/test_task2a_okf_smoke.py`; `quality/evidence/task2-entry/`

### Tasks

- T009：为正向信号、audit evidence、actor/事件白名单、freshness 缺失和 verified mutation 添加目标 RED。
- T010：在现有 projection/validator 中实现正向信号投影和 fail-closed 失效校验，使用同一 gate/oracle 让 T009 GREEN。

### Verify

`ORACLE-TRUST-SIGNAL-POSITIVE`、`ORACLE-TRUST-SIGNAL-NEGATIVE`、`ORACLE-TRUST-SIGNAL-INVALIDATION`；`pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers'`。成功 fixture 必须看到 `generated.by/at`、`digest_machine_pass=true`、两个白名单机器事件和对应 `audit/trust-signals/*.json`；结构-only fixture 不得伪造 verified；无 freshness input 时省略 `stale_after`；篡改正文、source fingerprint、locator、target path 或 page type 后 validator 必须报告信号失效/哈希错误；不得出现 human/agent_assisted/critical_token_recheck/sampled_entailment。RED/GREEN evidence 为 `trust-signal-red.txt`/`trust-signal-green.txt`，artifact root 的 trust audit 记录是唯一信号证据源。
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；真实 changed files 同时跨 `src/` 与 `tests/`，虽无服务/网络仍按路由脚本归为 fullstack；build-code 仍需按最终 diff 重路由。
- **fixtures_services**：现有 `_full_inputs` 三类 fixture、现有结构-only inputs、`tmp_path` artifact root；不启动服务，不访问 provider。
- **coverage limits**：证明结构/来源回查型机器信号和失效边界；不证明 `critical_token_recheck`、`sampled_entailment`、人工 reader gate、正文语义质量、全量 release 或外部 raw bytes 重新读取。
- **STOP**：若实现需要新字段事实源、外部 raw source、LLM/provider、人工记录、修改 `reader_frontmatter` hash 排除规则或改变 `not_released`/parser 边界，停止并回到 scope review。

### Knowledge

当前 `managed_content_hash` 已排除 `generated.at`、`verified`、`digest_machine_pass` 和 `digest_page_status`；source inventory、fixture selection 和 claim history 已提供可对账的 fingerprint/locator/target path；没有 source freshness 字段，故默认不写 `stale_after`。

### STOP

- source/Claim/selection fingerprint 无法一致、locator/target path 不能唯一闭合、audit evidence 无法回读或 actor 不符合白名单时，不能生成 verified。
- 任何 mutation 后仍保留当前 verified，或把结构 lint/provider/provider 成功写成 verified，必须修复后才能 GREEN。
- 不得借本 Phase 实现人工 reader gate、semantic entailment、trust score、TTL 推断、正式 CLI 或发布状态变化。

### Done

T009 的正向/负向/失效断言先出现目标性 RED；T010 以相同 gate/oracle GREEN；三类完整 fixture 产生可回查机器信号，结构-only fixture 保持 unverified，freshness 缺失保持省略，mutation fail-closed，包级仍 `not_released`。

### Risks and rollback

- **Risk**：fingerprint 一致性被误读成外部原文语义验证，或 audit event 被误当成第二事实源。
- **Prevention**：事件明确命名为 source/locator checks；只从同一 source/Claim/selection 输入投影；正文语义和人工门保持 deferred；content hash 绑定事件失效。
- **Rollback / recovery**：删除当前 Phase 的 trust fields/audit projection 逻辑和测试，保留结构 Bundle、旧 evidence 和历史 audit；不删除旧 Reader/Audit，不改 release 状态。

## 15. Dependencies and Parallelism

```text
T001 (frontmatter RED) → T002 (frontmatter GREEN)
T002 → T003 (Bundle RED) → T004 (Bundle GREEN)
T004 → T005 (attribution RED) → T006 (fixture/attribution GREEN)
T006 → T007 (smoke RED) → T008 (smoke/profile GREEN)
T008 → T009 (trust-signal RED) → T010 (trust-signal GREEN)
```

- Phase 1 必须先于 Phase 2：Bundle 不能自行实现第二套 YAML/hash。
- Phase 2 必须先于 Phase 3：parser smoke 的输入是已验证的 Bundle；不能对半成品做兼容结论。
- T001/T002、T003/T004、T005/T006、T007/T008 各自串行；RED/GREEN 同一行为、同一 command、同一 oracle。
- 不安排并行任务：实现模块和 acceptance fixture 共享 schema/output boundary；并行会产生双重 contract authority。
- Phase 4 必须在 Phase 3 后执行：信号事件要绑定已提交 Bundle 的当前 content hash，不能对未完成 profile/manifest 的半成品作结论。

### Source handoff coverage

| Source | Plan binding | Task/AC handoff |
| --- | --- | --- |
| R-008 | AC-01–AC-08 + `not_released` in plan decisions/trace | T001–T010；AC-01–AC-08 |
| F-001 | PFACT-002/parser research and license provenance | T007/T008；FR-SMOKE-001/002；AC-08 |
| F-003 | frozen contract aliases/lifecycle mapping | T001–T010（每张 task card 必须直接列 source ref）；FR-FRONT-004/005、FR-STATUS-001/002/003、FR-SMOKE-002；AC-02/04/06/08 |

## 16. Requirement and Verification Traceability

每行 `source_refs` 保留 decision-log R/D 与 spec FR/AC 关系；计划不复制 PFACT 原文。

| FR | source_refs | Task IDs | AC IDs | Phase | Gate / evidence |
| --- | --- | --- | --- | --- | --- |
| FR-BUNDLE-001 | R-001→D1 | T003,T004 | AC-01 | Phase 2 | bundle gate / `bundle-green.txt` |
| FR-BUNDLE-002 | R-001→D1 | T003,T004 | AC-01,AC-06 | Phase 2 | allowlist identity + round-trip validator / `bundle-green.txt` |
| FR-BUNDLE-003 | R-001→D1 | T003,T004 | AC-01,AC-05 | Phase 2 | canonical index/source projection / `projection-report.json` |
| FR-BUNDLE-004 | R-007→D2 | T007,T008 | AC-08 | Phase 3 | smoke gate / `exit-manifest.json` |
| FR-BUNDLE-005 | R-001→D1 | T003,T004 | AC-02,AC-05 | Phase 2 | product/module/degraded oracle |
| FR-BUNDLE-006 | R-001→D1 | T003,T004 | AC-01,AC-05 | Phase 2 | index/link oracle |
| FR-FRONT-001 | R-002→D1 | T001,T002 | AC-06 | Phase 1 | round-trip oracle |
| FR-FRONT-002 | R-003→D1 | T001,T002 | AC-02,AC-06 | Phase 1 | PyYAML lock + round-trip |
| FR-FRONT-003 | R-002→D1 | T003,T004,T005,T006 | AC-02 | Phase 2 | topic-index mapping + three-fixture type mapping oracle |
| FR-FRONT-004 | R-002→D1 | T003,T004 | AC-02,AC-04 | Phase 2 | status placement oracle |
| FR-FRONT-005 | R-002→D1 | T001,T002 | AC-06 | Phase 1 | managed hash oracle |
| FR-FRONT-006 | R-002→D1 | T003,T004 | AC-02 | Phase 2 | title/description fallback oracle |
| FR-STATUS-001 | R-005→D1/D-004 | T003,T004,T009,T010 | AC-04 | Phase 2/4 | three-layer status + machine-pass oracle |
| FR-STATUS-002 | R-005→D1/D-004 | T009,T010 | AC-04 | Phase 4 | verified actor/evidence/invalidation oracle |
| FR-STATUS-003 | R-005→D1/D-004 | T009,T010 | AC-04 | Phase 4 | explicit freshness projection/omission oracle |
| FR-ATTR-001 | R-004→D3 | T005,T006 | AC-03 | Phase 2 | attribution gate |
| FR-ATTR-002 | R-004→D3 | T005,T006 | AC-03,AC-05 | Phase 2 | source projection gate |
| FR-VALID-001 | R-006→D1/D3 | T003,T004,T005,T006,T009,T010 | AC-02,AC-04,AC-06 | Phase 2/4 | validator acceptance；AC-03 attribution 由 FR-ATTR-001/002 单独覆盖 |
| FR-VALID-002 | R-006→D1 | T003,T004 | AC-05 | Phase 2 | allowlist/link/degraded gate |
| FR-SMOKE-001 | R-007→D2 | T007,T008 | AC-08 | Phase 3 | parser smoke gate |
| FR-SMOKE-002 | R-007→D2 | T007,T008 | AC-08 | Phase 3 | profile downgrade gate |
| FR-FIX-001 | R-004→D3 | T005,T006 | AC-03 | Phase 2 | selection manifest + fixture gate |
| FR-FIX-002 | R-004→D3 | T005,T006 | AC-03 | Phase 2 | footnote/claim locator gate |
| FR-PROJ-001 | R-001→D1 | T003,T004 | AC-02,AC-07 | Phase 2 | projection report |
| FR-PROJ-002 | R-001→D1 | T001,T002,T003,T004,T005,T006 | AC-06,AC-07 | Phase 1/2 | round-trip + replay gate; AC-07 zero-provider projection evidence |
| FR-ENTRY-001 | F-002→D1 | T003,T004 | AC-02 | Phase 2 | backfill/not_released gate + Task0/Task1 machine-gate handoff |
| FR-LLM-001 | R-001/R-009→D1 | T003,T004 | AC-07 | Phase 2 | zero-provider/not_released evidence |
发布前确认：27/27 FR 有 Task 和 AC；8/8 AC 有 gate/evidence；每个 Task 反向引用 FR/AC；DAG 无环；constitution binding 已按实际文件 hash 核对；T009/T010 已完成实现和专项证据；当前 WorkflowHub review/receipt 因 bundle mismatch 仍 unavailable，不能写成 runner review 已通过；完整 aggregate 已通过，verify-code 仍需完成当前快照复核。

## 17. Review and Finding Disposition

| finding_id | original_fact | consequence | status | next_action | evidence_ref | owner | consumer | retain_or_delete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PLAN-ADV-001 | simplicity-guard 已完成静态范围检查：结构合同有必要性，既有 identity/jsonl/error 与外部 parser 可复用，PyYAML 是需求硬约束。 | 当前无可核实的范围收缩阻断。 | fixed | 保留 DEC-001–005；不新增 CLI、数据库或 runtime。 | specs/task2a-knowledge-publication-reader-bundle/simplicity-guard-facts.md | Plan Builder | build-code | retain |
| PLAN-ADV-002 | engineering checklist 已记录旧 pipeline/CLI 保护、依赖锁、RED/GREEN、STOP 和 evidence 边界。 | 这是静态计划检查，不是 provider review。 | fixed | 下游按计划边界执行；不把 checklist 写成正式 verdict。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md | Plan Builder | build-code/verify-code | retain |
| PLAN-ADV-003 | UI 设计审查标记为不适用；本任务只有 Markdown 文件和本地模块接口。 | 不产生 UI review 事实。 | fixed | 不新增 UI phase；未来 viewer 另开规格。 | specs/task2a-knowledge-publication-reader-bundle/plan-design-review-facts.md | Plan Builder | build-code | retain |
| PLAN-ADV-004 | CEO advisory 文件认为方向、范围和失败路径成立。 | 这是只读 advisory，不是当前 task 的正式确认。 | accepted_risk | 仅作为设计背景保留；不替代当前 task review 或用户确认。 | specs/task2a-knowledge-publication-reader-bundle/plan-ceo-review-facts.md | Plan Builder | build-code | retain |
| ENG-001 | `tasks.md` 曾绑定旧 plan hash，且把不存在的 runner-authenticated review receipt 写成事实。 | 下游可能消费过期 plan 或假 review。 | fixed | `spec-tasks` 已按当前 plan snapshot 重算 tasks header/T001–T008 plan hash，并确认旧 hash 清除；当前 review receipt 仍按 unknown 处理。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#findings; quality/evidence/host-invocations/a3aafe066f60a2ffd51ec95aa8955d4691612ab601b97fd8b880750b77ecaae5.json | Plan Builder / build-plan | build-code | retain |
| ENG-002 | 旧方案把 Bundle、Audit、projection report 写入边界混在一起，validator 缺 audit/report 参数。 | containment、回滚和 degraded 对账不闭合。 | fixed | `BundleArtifactPaths` 固定同一 root；validator 同时校验三面；staging/atomic commit 和 report/page 对账写入计划。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#findings | Plan Builder | build-code | retain |
| ENG-003 | 旧方案只有 API 名称，没有 versioned input/schema，也没钉死 TopicIndex v2 adapter。 | 结构测试可能掩盖字段漂移和 claim 断链。 | fixed | 增加结构/完整两种 versioned input、四个 result schema、当前 `validate_topic_index` gate 和拒绝规则。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#findings | Plan Builder | build-code | retain |
| ENG-004 | 旧方案把 Bundle API guard 当作 AC-07 `--no-llm` 等价证据，未跑现有 CLI 路径。 | 不能证明真实 CLI 离线零网络。 | fixed | Bundle acceptance 必须调用现有 `cli.main`/`digest --no-llm` + socket/provider guard；API guard 只作补充。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#findings | Plan Builder | build-code | retain |
| ENG-005 | 旧方案用 tmp_path 最小 entry manifest 代替当前 Task0/Task1 backfill readback。 | AC-02 可能假绿。 | fixed | 显式 `input_root`/resolver 只读校验真实 refs/hash/version/coverage；synthetic 仅测拒绝分支，真实回读缺失则 STOP。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#findings | Plan Builder | build-code/verify-code | retain |
| ENG-006 | 旧方案同时把 parser blocked 和 downgrade 当成 AC-08 GREEN。 | 可能错误宣称兼容或完成。 | fixed | 区分 `compatibility_passed`、`honest_downgrade_passed` 和 `blocked`；只有前者写 `okf_version`/宣称兼容，事实缺失才 blocked。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#findings | Plan Builder | build-code/verify-code | retain |
| ENG-007 | 当前 raw corpus 未设置且没有 Task 2-A fixture/vendor/tests。 | 不能生成真实 fixture 或 attribution 证据。 | needs_human | T005/T006/T008 保持 STOP；未提供受控 corpus/vendor provenance 前不写虚构 fixture，不关闭 AC-03/AC-08。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#findings | Plan Builder | build-code | retain |
| CURRENT-QUALITY-UNKNOWN-001 | 当前 task store 的 index.json reviews 为空，facts.jsonl 为空，quality/verify.json status 为 unknown。 | 当前没有可引用的 build-plan review receipt、provider verdict 或用户确认。 | needs_human | 保持 Stage Progress 的 unknown/incomplete；正式完成声明必须由真实 Runner/provider/用户事实产生，不能从历史文件补写。 | task.json; index.json; facts.jsonl; quality/verify.json | WorkflowHub host owner | build-code barrier | retain |
| CURRENT-TASKS-PLAN-HASH-001 | 既有 tasks.md 的 header 与 T001–T008 versioned_refs 曾绑定旧 plan SHA-256。 | 下游任务投影不能证明消费当前 plan；直接 build-code 会留下 stale binding。 | fixed | `spec-tasks` 已重写并回读 tasks header/T001–T008 的当前 plan hash；当前 review/confirmation 缺失仍由其他 finding 约束。 | tasks.md header/T001–T008 versioned_refs; quality/evidence/host-invocations/a3aafe066f60a2ffd51ec95aa8955d4691612ab601b97fd8b880750b77ecaae5.json | Plan Builder | build-code barrier | retain |
| ENG-CURRENT-001 | 旧 review 快照曾发现 tasks header/T001–T008 绑定旧 plan hash。 | 旧 review packet 不能证明消费当时的计划。 | fixed | 当前 `spec-tasks` 已按最新 plan snapshot 重算并回读所有 plan refs；保留旧 finding 作为历史审计，不再阻止 build-code。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings; quality/evidence/host-invocations/605533eac2121d0e3f621cb7f447609675ffd7c7cb5e39519b3c011d5963ba4a.json | Plan Builder / build-plan | build-code | retain |
| ENG-CURRENT-002 | 完整 `ReaderBundleInputs` 的 claim/fixture refs 在 T005 才可用，不能成为 T003/T004 结构正例输入。 | 结构 GREEN 可能掩盖 attribution 断链。 | fixed | 拆出 `ReaderBundleStructureInputs`；T003/T004 只测结构/拒绝，T005/T006 才测完整 attribution。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code | retain |
| ENG-CURRENT-003 | 当前 v2 row 使用 `topic_key`/`topic_id`，published validator 要求 axis 非空，旧 resolver 还要求 `topic-*`/category/path。 | adapter 可能伪造 module/ID 或修改旧 schema。 | fixed | 先用当前 validator；v2 按 `digest_topic_id → topic_id → topic_key` 归一，legacy 才调用 resolver；product-only 不可发布时保留 degraded 和 source/identity，不造 module。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code | retain |
| ENG-CURRENT-004 | 原计划没有显式 input root/resolver，binding 示例缺 schema/version。 | 读取范围和版本绑定不闭合。 | fixed | `ReaderBundleStructureInputs`/`ReaderBundleInputs` 固定 input root/resolver；ArtifactRef 必须携带并校验 schema/version/hash。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code | retain |
| ENG-CURRENT-005 | 三个结果对象字段、producer/consumer、license provenance 不完整。 | 报告或 parser pass 可能缺关键事实。 | fixed | 增加 BundleReport、BundleValidationReport、ParserSmokeResult field table、license/notice/source fields 和拒绝规则。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code/verify-code | retain |
| ENG-CURRENT-006 | artifact root report 与 task-relative evidence 曾有双事实源，缺 copy/hash/readback owner。 | 回滚和验收无法判断事实源。 | fixed | artifact_root reports 是唯一事实源；runner/build-code 复制、哈希、回读 evidence，失败即 STOP。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code/verify-code | retain |
| ENG-CURRENT-007 | 没有重复 root、staging、atomic publish 合同。 | 中途失败可能留下半套结果。 | fixed | fresh empty non-symlink root + caller single-writer boundary + run-scoped staging + validate-before-atomic-commit；补复用/partial-write 负例，不增加 owner lock/concurrency protocol。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code | retain |
| ENG-CURRENT-008 | accepted AC-08 允许 honest downgrade，但旧 plan 统一写 blocked。 | 计划错误收紧已接受语义。 | fixed | 采用 `compatibility_passed`、`honest_downgrade_passed`、`blocked` 三态；只有兼容 pass 写版本和命名，完整 downgrade 可通过 AC-08 但不宣称兼容。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code/verify-code | retain |
| ENG-CURRENT-009 | tasks 把 full-tree pytest 写成 final aggregate，plan 却只把定向命令作为 gate。 | final gate、expected exit、oracle 不唯一。 | fixed | 定向六文件命令是正式 aggregate；full-tree 仅 display/diagnostic，不另立验收 gate。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code/verify-code | retain |
| INPUT-STOP-001 | 当前无 raw corpus、Bundle 实现/tests/vendor，无法真实跑 attribution/parser RED/GREEN。 | 不能生成真实 AC-03/AC-08 证据。 | needs_human | 保持 T005/T006/T008 blocked；提供受控 corpus、vendor commit/license/notice/bytes 后再执行；不得用 synthetic/history 关闭。 | specs/task2a-knowledge-publication-reader-bundle/plan-eng-review-facts.md#current-findings | Plan Builder | build-code barrier | retain |
| WH-REVIEW-CURRENT-001 | 当前只读 wh-review 发现的 plan hash 过期提示，实际已由后续 spec-tasks projection 修复。 | 旧提示可能让 build-code 无谓 STOP。 | fixed | 已将 plan 下一步和 finding 改为历史审计事实；当前 tasks header/T001–T008 均绑定最新 plan hash。 | quality/evidence/host-invocations/60d7e2c01ce6a0a497ece409d14aa4d488664e933eb50058f5344f4b00de45f7.json; quality/evidence/host-invocations/605533eac2121d0e3f621cb7f447609675ffd7c7cb5e39519b3c011d5963ba4a.json | Plan Builder | build-code | retain |
| WH-REVIEW-CURRENT-002 | 当前只读 wh-review 发现 AC-08 合法 downgrade 已写入，但没有独立可执行的 downgrade gate。 | parser downgrade 分支可能漏测，无法证明 accepted AC-08 口径。 | fixed | 增加独立 `parser_downgrade` gate、RED/GREEN evidence 和 `ORACLE-OKF-DOWNGRADE`；compatibility gate 仍单独使用 `parser_compatible`。 | quality/evidence/host-invocations/60d7e2c01ce6a0a497ece409d14aa4d488664e933eb50058f5344f4b00de45f7.json | Plan Builder | build-code/verify-code | retain |
| SPEC-ANALYZE-MATERIAL-001 | 当前 Runner 的 spec-analyze 两次均缺少 `review-packet.v1`/`planning_artifacts` 投影，无法计算覆盖率或语义一致性。 | 没有 spec-analyze 通过事实；不能把 material incomplete 当 pass。 | needs_human | 保留 Runner 的 material-incomplete 结果；若宿主补齐冻结 packet，再按当前快照重跑，否则保持本阶段 unknown/incomplete。 | quality/evidence/host-invocations/9292e5b4013d9cabc6e31481d0365b208fe0193afb188b09ec79edb81da28db7.json; workflowhub/skills/spec-analyze/review-bundle.json | WorkflowHub host owner | wh-review/build-code barrier | retain |
| SPEC-ANALYZE-CURRENT-001 | 当前 spec-analyze 仍缺 `review-packet.v1`/`planning_artifacts`，task path 也未被宿主投影；即使按当前 `plan/tasks` 哈希重建官方 `buildReviewMaterials` bundle，host invocation 仍未消费该附件。 | 无法产生 coverage/semantic pass。 | needs_human | 宿主补齐并显式绑定当前 packet、planning artifacts 和真实 task-path 投影后再重跑；本阶段保留 incomplete，不伪造通过。 | quality/evidence/host-invocations/77378ffb8194b676d478785984d278a27e47b091418f8ae54b36c908f96f8ae7.json; /Users/Hugh/.workflowhub/wh-review-packets/.wh-review-packets/bundle-build-plan-default-LrSWaW/review-packet.v1.json | WorkflowHub host owner | build-plan barrier | retain |
| SPEC-ANALYZE-CURRENT-002 | R-008、F-001、F-003 的 plan final trace 不完整。 | 下游无法从来源追到 task/AC。 | fixed | 新增 Source handoff coverage 表并补任务/AC 绑定；保留原 finding 供回查。 | quality/evidence/host-invocations/b249cd42242cf915c43fccc2b4d0ba73c5eee1cdd6f00a35647cdca0b1d18d3b.json; plan.md#source-handoff-coverage | Plan Builder | build-code/verify-code | retain |
| SPEC-ANALYZE-CURRENT-003 | decision-log 的 canonical `OPEN-001`/`OPEN-002` 与 spec 的 `OPEN-02`/`OPEN-01` 别名顺序不一致。 | owner/关闭条件可能被交换。 | fixed | 在 plan 中冻结 alias→canonical 映射；未关闭事实仍按 PFACT/STOP 保留。 | quality/evidence/host-invocations/b249cd42242cf915c43fccc2b4d0ba73c5eee1cdd6f00a35647cdca0b1d18d3b.json; plan.md#canonical-input-aliases | Plan Builder | build-code | retain |
| SPEC-ANALYZE-CURRENT-004 | spec v1-draft 与 plan/tasks Draft/in_progress 的生命周期口径未显式区分。 | 下游可能把草稿当正式 handoff。 | fixed | 增加 Lifecycle note，明确 spec artifact identity 与当前阶段状态不同。 | quality/evidence/host-invocations/b249cd42242cf915c43fccc2b4d0ba73c5eee1cdd6f00a35647cdca0b1d18d3b.json; plan.md#lifecycle-note | Plan Builder | build-code barrier | retain |
| SPEC-ANALYZE-CURRENT-005 | spec 使用 `topic_key_v2`，plan 同时出现 `topic_key`/`topic_id`/`digest_topic_id`。 | adapter 可能发生身份漂移。 | fixed | 冻结 `topic_key_v2 → digest_topic_key` 和 `digest_topic_id → topic_id → topic_key` 的 canonical mapping。 | quality/evidence/host-invocations/b249cd42242cf915c43fccc2b4d0ba73c5eee1cdd6f00a35647cdca0b1d18d3b.json; plan.md#canonical-input-aliases | Plan Builder | build-code | retain |
| SPEC-ANALYZE-CURRENT-006 | product-only valid row 与旧 validator 接受条件冲突，原计划允许静默 degraded。 | 合法产品-only 输入可能被错误丢入 degraded。 | fixed | 规定 valid product-only 直接写 `products/{product}/...`；仅 malformed/unsupported/uncertain 才 degraded，validator 不接受时先停并调整 adapter。 | quality/evidence/host-invocations/b249cd42242cf915c43fccc2b4d0ba73c5eee1cdd6f00a35647cdca0b1d18d3b.json; plan.md#solution-design | Plan Builder | build-code | retain |
| SPEC-ANALYZE-CURRENT-007 | Phase Verify 缺少自包含 test tier/method、fixtures/services、coverage limits 和 STOP。 | 下游无法按同一方法执行或判停。 | fixed | 为三 Phase Verify 补齐四项字段，覆盖本地夹具、零网络边界和缺事实 STOP。 | quality/evidence/host-invocations/b249cd42242cf915c43fccc2b4d0ba73c5eee1cdd6f00a35647cdca0b1d18d3b.json; plan.md#test-strategy | Plan Builder | build-code/verify-code | retain |
| RUN-CONTRACT-CURRENT-001 | 官方 run 把 `uv run --frozen pytest` 识别为不可执行 gate_cmd。 | 结构检查无法开始。 | fixed | 所有正式 gate_cmd 统一为宿主可识别的 `pytest ...`；uv 命令只保留 display/环境说明。 | quality/facts/ce936ccc2b3f49b97aeb00035011ceaef1b799ef5b57bdc2cdbae43ddcfcaf58.json; plan.md#test-strategy; tasks.md | Plan Builder | build-plan runtime | retain |
| RUN-CONTRACT-CURRENT-002 | Phase 2 Files 中反引号 `artifact_root` 被解析为未归属的待改文件。 | Phase/file ownership 检查失败。 | fixed | 改写为 runtime artifact root prose，不把运行时目录当 source file。 | quality/facts/0c1b9605772523deb7fb7ef370126a26035f56eedce7d9ac6770dd74216cb47a.json; plan.md#phase-2；tasks.md | Plan Builder | build-plan runtime | retain |
| ENG-CURRENT-010 | 当前 plan-eng-review 发现 plan/tasks component receipt 仍绑定旧 plan hash，且 ParserSmokeResult producer/consumer、product-only adapter、artifact-root recovery 都不够可执行。 | 下游可能消费 stale receipt，或实现出无法证明合法 product-only/降级边界/失败恢复的合同。 | fixed | 重新明确当前 plan/tasks receipt 由官方 producer 生成；冻结不带生产计数器的 smoke API、CLI runtime audit owner、product-only 专用 adapter 顺序和 staging/atomic recovery，随后必须重新生成 current receipts。 | quality/evidence/host-invocations/04c431e33c92915ecc71a1cedc739622518d9f6a6c6b1c042640278c18de7e1a.json | Plan Builder | build-code/verify-code | retain |
| SPEC-ANALYZE-CURRENT-008 | 当前 spec-analyze 指出 T001–T008 的 task cards 没有逐卡直接列出 F-003 等 source refs，且 handoff 排除项不够明确。 | 仅靠 plan 反向索引无法证明每张卡消费同一冻结依据。 | fixed | 在 tasks 顶部增加 source handoff coverage，并让每张卡直接列 F-003；T007/T008 另直接列 F-001，补齐 FR/AC 和 STOP 关系。 | quality/evidence/host-invocations/bab1f4564960dea02d0962a23565ab356b08231fc7ecf8be48182dc65d8a1f4c.json; tasks.md#source-handoff-coverage | Plan Builder | build-code/verify-code | retain |
| SPEC-ANALYZE-CURRENT-009 | product-only 合同与现有 validator 的 module 非空约束冲突；原始方案未冻结正例、负例和适配层边界。 | 合法 product-only row 可能被错误降级，或实现为偷偷跳过所有校验。 | fixed | 规定公共字段先校验，专用 adapter 只适配 module-only 约束；合法 row 直写 products 路径，malformed/unsupported/uncertain 进入 degraded；T003/T004 必须同时有正负 oracle。 | quality/evidence/host-invocations/bab1f4564960dea02d0962a23565ab356b08231fc7ecf8be48182dc65d8a1f4c.json; plan.md#solution-design; tasks.md#T004 | Plan Builder | build-code/verify-code | retain |
| SPEC-ANALYZE-CURRENT-010 | ParserSmokeResult 声明 network/provider count，但 `run_parser_smoke` 原签名没有必要的 producer/consumer contract。 | 生产接口可能膨胀，或缺失零调用事实被误判。 | fixed | 从生产 ParserSmokeResult/API 删除计数器与 `SmokeContext`；由现有 CLI runtime audit 负责 `--no-llm` 零调用事实，AC-08 测试边界仅保留 deny-only guard，缺 audit/guard evidence 即 STOP。 | quality/evidence/host-invocations/bab1f4564960dea02d0962a23565ab356b08231fc7ecf8be48182dc65d8a1f4c.json; plan.md#api-contract; tasks.md#T007 | Plan Builder | build-code/verify-code | retain |
| SPEC-ANALYZE-CURRENT-011 | artifact_root 只检查空目录/staging/atomic，未证明并发 owner 的原子排他。 | 两次投影可能同时进入 staging 或留下不一致事实。 | fixed | 收缩为 fresh empty non-symlink root、调用方 single-writer/serial boundary、run-scoped staging 和 validate-before-atomic-commit；补复用/partial-write recovery，不增加 owner lock 或 contention 协议。 | quality/evidence/host-invocations/bab1f4564960dea02d0962a23565ab356b08231fc7ecf8be48182dc65d8a1f4c.json; plan.md#data-model-and-lifecycle; tasks.md#T003 | Plan Builder | build-code/verify-code | retain |
| TEST-ROUTING-CURRENT-001 | 当前 test-routing-advisor 看到 task.json 的 changed_files、phase_count、test_command 等输入为空，因而只能给出 `fullstack` 失败/无测试结果。 | 当前不能把路由结果写成已执行的测试事实。 | needs_human | 保留 `fullstack` 为计划预判；build-code 必须按真实 changed files 重路由并提供真实 task facts 后再执行，当前不补写测试 receipt。 | quality/evidence/host-invocations/00bce6e9c14dc3e8f6ebdce950c3ff967491919e180ec39134f22fcbc0145e30.json | WorkflowHub host owner / build-code | build-code barrier | retain |
| WH-REVIEW-CURRENT-003 | 当前 wh-review 已生成审查包，但只读 TaskHandle 无法写入 canonical review record（`EPERM canonical TaskHandle write`），没有正式 verdict/result ref。 | 当前没有独立 wh-review 通过事实，阶段不能闭合。 | needs_human | 保留真实 canonical writer failure/无 verdict；待宿主提供可写的正式 review 运行或人工 continuation 后再补独立 review，当前保持 `in_review`/incomplete。 | quality/evidence/host-invocations/5f8808e83e353ec3a0690ad40bc5e3d7b9d455b07c1caac8b9cf22e8f2b1af22.json | WorkflowHub host owner | build-plan barrier | retain |
| SIMPLICITY-20260808-001 | simplicity-guard 要求 artifact root owner lock、`O_CREAT|O_EXCL` 和并发 contention 协议，但 accepted scope 只冻结本地单写者/串行调用。 | 实现边界被无依据扩大，测试会把未接受的并发语义当作门禁。 | fixed | 删除 owner lock、exclusive-create 和 contention oracle；保留 fresh non-symlink root、staging、atomic commit、root reuse/partial-write recovery。 | quality/evidence/host-invocations/de76500f239c6bf1efe9d25866b975bb2bb7c2e8f791934cf3d49398c3d71d08.json | Plan Builder | build-code | retain |
| SIMPLICITY-20260808-002 | simplicity-guard 指出 production `SmokeContext`、provider/network counters 与 counter read boundary 不必要；AC-07 已由 CLI runtime audit 负责。 | 生产 API 与验收责任边界膨胀，可能把测试计数误写成产品事实。 | fixed | 删除生产 SmokeContext/counter 字段；AC-07 只引用现有 CLI audit，AC-08 测试边界可使用 deny-only guard，缺 audit/guard evidence 仍 STOP。 | quality/evidence/host-invocations/de76500f239c6bf1efe9d25866b975bb2bb7c2e8f791934cf3d49398c3d71d08.json | Plan Builder | build-code/verify-code | retain |
| SG-P1-003 | 当前计划的 `BundleReport`/`ParserSmokeResult` 仍残留生产级离线计数字段或将计数暗示为 manifest 责任。 | 生产接口和 Bundle 报告可能重复实现 CLI runtime audit，并把测试计数误写成产品事实。 | fixed | 删除 `offline_counters` 和生产 smoke 计数要求；保持现有 CLI runtime audit 为 AC-07 唯一事实源，测试边界 deny-only guard 只作补充；审计缺失或非零仍 STOP。 | quality/evidence/host-invocations/dd2890922809d7489481bcc197720d7e12fb76a7ba91f0c7fcdfedb979679e3a.json; plan.md#api-contract; tasks.md#T008 | Plan Builder | build-code/verify-code | retain |
| SG-P1-004 | 当前计划把网络计数写入 CLI runtime audit，但现有 `_task0_runtime_audit` 只生产 `calls.llm`/`calls.embedding`。 | 下游可能依赖不存在的 audit 字段，或为补字段新增生产计数器。 | fixed | CLI audit 只核对 `calls.llm=0`、`calls.embedding=0`；网络零请求改由 acceptance 测试边界的 deny-only socket guard 独立证明，生产 API/manifest 不增加网络计数。 | quality/evidence/host-invocations/7b1f56e67177d3880197037582b12ad50b99949910235c9b6a8e9de21118b50a.json; plan.md#test-strategy; tasks.md#T003/T008 | Plan Builder | build-code/verify-code | retain |
| ENG-RETRY-005 | 当前 plan-eng-review 重复发现旧 tasks plan hash、AC-08 降级完成口径、mapping 执行规则和 verified 失效转换未完全落到当前材料。 | 下游可能消费 stale task projection、误把 honest downgrade 当 blocked/compatibility，或静默继承失效 verified。 | fixed | 保留 stale hash 作为 spec-tasks 的重绑输入；明确完整 failed/unavailable provenance 是 AC-08 `honest_downgrade_passed`，缺事实才 blocked；用 selection manifest 的 exact `(topic_id, object_intent)` pair 冻结三类 mapping，并要求 fingerprint/locator/path/page type mutation 使 validator 拒绝当前 verified、保留旧 audit，不自动改写现有页面。 | quality/evidence/host-invocations/73080a098528b28660670c437c84826550e59fe5171d88cd5815aecc3864d12d.json; plan.md#data-model-and-lifecycle; tasks.md#T003/T005/T006/T008 | Plan Builder | spec-tasks/build-code/verify-code | retain |
| ENG-RETRY-001 | 当前 tasks.md 与修订后的 plan.md SHA-256 不一致。 | 下游可能消费旧任务投影和错误的组件 receipt。 | fixed | 保留 plan；下一步由 spec-tasks 重算 tasks header、versioned refs 和所有当前 plan 绑定，再回读 hash。 | quality/evidence/host-invocations/d9a869bde7102d9d242281a4cf14da173dde40165cd8a06f580bd23557d097b6.json; tasks.md#header | Plan Builder | spec-tasks/build-code | retain |
| ENG-RETRY-002 | product-only adapter 的计划文字先调用 module-required `validate_topic_index`，与后续专用 adapter 顺序冲突。 | 合法 product-only row 可能被错误降级，或实现成静默 bypass。 | fixed | 冻结公共 envelope → 分区 → standard 使用现有 validator / product-only 使用 module-optional validator；两条分支都保留公共检查。 | quality/evidence/host-invocations/d9a869bde7102d9d242281a4cf14da173dde40165cd8a06f580bd23557d097b6.json; plan.md#data-model-and-lifecycle | Plan Builder | build-code | retain |
| ENG-RETRY-003 | `finalize_bundle_profile` 缺少写入 staging、验证后原子替换和失败保留旧 root 的直接 API 边界。 | smoke profile 更新可能留下半套 Bundle/manifest，回滚无法证明。 | fixed | 把 finalize 限定在 run-scoped staging、validate-before-atomic-commit；失败保留旧正式 root并返回结构化 failure。 | quality/evidence/host-invocations/d9a869bde7102d9d242281a4cf14da173dde40165cd8a06f580bd23557d097b6.json; plan.md#api-contract | Plan Builder | build-code/verify-code | retain |
| ENG-RETRY-004 | `ParserSmokeResult` 使用 source/reason 文字但缺少 attempt/source provenance 和 read boundary 字段的明确合同。 | failed/unavailable 可能无法证明 honest downgrade 的来源、尝试和读取范围。 | fixed | 增加 `attempt_ref` 与 `read_boundary`，并要求 source/attempt/reason/bundle/read-boundary 完整后才允许 downgrade 或 compatibility。 | quality/evidence/host-invocations/d9a869bde7102d9d242281a4cf14da173dde40165cd8a06f580bd23557d097b6.json; plan.md#api-contract | Plan Builder | build-code | retain |
| PLAN-ENG-20260808-001 | plan-eng-review 发现 AC-08 的 compatibility、honest downgrade、blocked 三态与测试/STOP 口径未完全闭合。 | 下游可能把 blocked 当作合法 downgrade GREEN，或反过来错误收紧 accepted AC。 | fixed | 冻结三态和两个独立 gate；完整 failed/unavailable provenance 才能 honest downgrade，缺失/含糊保持 blocked。 | quality/evidence/host-invocations/4c0a57c08aa4cbaaaa74b12da28e07c050f782b7de6bce745b83145b3f1546c6.json | Plan Builder | build-code/verify-code | retain |
| PLAN-ENG-20260808-002 | plan-eng-review 发现 product-only adapter 与现有 `validate_topic_index` 的调用顺序未冻结。 | 合法 product-only row 可能被旧 module-required validator 错误拒绝，或实现成静默 bypass。 | fixed | 先做公共 envelope 检查并分区 product-only；standard rows 调用现有 validator，product-only 调用专用 validator，二者都保留公共检查。 | quality/evidence/host-invocations/4c0a57c08aa4cbaaaa74b12da28e07c050f782b7de6bce745b83145b3f1546c6.json | Plan Builder | build-code | retain |
| PLAN-ENG-20260808-003 | 当前冻结 TopicIndex 没有 product-only positive fixture，任务又禁止 synthetic positive 关闭真实入口验收。 | 无法同时验证 adapter 结构契约和真实 Task 1 entry backfill 边界。 | fixed | 允许结构 fixture 只验证 adapter positive；真实 Task 1 entry refs/hash/coverage 仍是 AC-02 handoff 的独立 STOP 条件。 | quality/evidence/host-invocations/4c0a57c08aa4cbaaaa74b12da28e07c050f782b7de6bce745b83145b3f1546c6.json | Plan Builder | build-code/verify-code | retain |
| PLAN-ENG-20260808-004 | AC-07 要求 network=0，但当前权威运行时 audit 的字段生产者未写进计划。 | 可能凭 Bundle API 或自造计数器宣称离线通过。 | fixed | 明确现有 CLI runtime audit 是唯一 producer；Bundle/ParserSmokeResult 不新增生产 count，audit 缺失或非零即 STOP。 | quality/evidence/host-invocations/4c0a57c08aa4cbaaaa74b12da28e07c050f782b7de6bce745b83145b3f1546c6.json | Plan Builder | build-code/verify-code | retain |
| PLAN-ENG-20260808-005 | RED scenario command 与正式 `gate_cmd` 不一致，部分仍使用 `uv run --frozen pytest`。 | host gate 可能无法执行或把 display command 当验收命令。 | fixed | 所有正式 scenario/gate_cmd 统一为 `pytest ...`；uv 只保留 display/诊断。 | quality/evidence/host-invocations/4c0a57c08aa4cbaaaa74b12da28e07c050f782b7de6bce745b83145b3f1546c6.json | Plan Builder | build-plan/build-code | retain |
| WH-RUNTIME-CURRENT-004 | 本次最终快照的官方 `build-plan` review dispatch 在 `simplicity-guard` 重跑时返回 `bundle sha256 mismatch: scripts/review-materials.mjs`。 | 没有当前 WorkflowHub lens invocation receipt；不能把本地 fallback 当正式 review。 | needs_human | 保留 unavailable 和原始错误；本地只做静态计划检查与测试路由观察，继续实现但不写 provider pass；待宿主修复 bundle 后再重跑正式 review/receipt。 | `quality/evidence/host-invocations/build-plan-signal-revision-runtime.json` | WorkflowHub host owner | verify-code/build-plan barrier | retain |
| TEST-ROUTING-DIRECT-20260810 | 对 Phase 1–4 和 final changed-file 集合直接调用 `test-routing-advisor/scripts/route.mjs`，五次均返回 `fullstack`/`pass`；Phase 4 跨 `src/` 与 `tests/`，不是 feature tier。 | 官方 routing receipt 仍受同一 bundle mismatch 限制。 | accepted_risk | 已把 Phase 4 任务卡修正为 `fullstack`/`fullstack-slice-testing`；build-code/verify-code 仍按最终 diff 重路由。 | `quality/evidence/task2a-reader-bundle/build-plan-routing-20260810.json` | Plan Builder | build-code/verify-code | retain |
| LOCAL-REVIEW-CURRENT-20260810 | 独立只读复核发现 locator/target 约束、TopicIndex source binding、canonical fingerprint 对账、audit/frontmatter 一致性、真实 freshness 日期和 mutation policy 仍需收紧。 | 若不修正，正向信号可能只检查字段存在，或把失效信号静默保留。 | fixed | 已补 source/evidence binding、locator syntax/target containment、canonical fingerprint/audit/topic 对账、`date.fromisoformat`、显式 freshness 测试；mutation 统一为 fail-closed rejection，不自动改写页面。 | `quality/evidence/task2a-reader-bundle/local-independent-review-20260810.md` | Plan Builder | verify-code | retain |

历史 worktree 中曾出现的 quality/reviews/results/*、quality/reviews/reports/*、provider pass/finding 和 runner receipt 均不在当前 worktree，且当前 task records 未引用它们；本 plan 不把这些缺失文件写成当前证据。wh-review-disposition.md 只作为上游 build-spec 处置材料保留，不代表本次 build-plan review 已完成。

本节的 fixed 仅表示已处理的本地计划检查或明确的边界决定；unverified 表示当前证据不足。它们不代表产品代码完成、正式发布、用户确认或 build-code 自动放行。Parser commit、raw corpus、Task 1 receipt 冲突和下游 STOP 仍有效。
