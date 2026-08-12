# 任务清单：Task 2-C 信任信号与小语料 Agent 读者质量门

- **Input**：`specs/task2c-knowledge-publication-trust-reader-quality/decision-log.md`、`specs/task2c-knowledge-publication-trust-reader-quality/spec.md`、`specs/task2c-knowledge-publication-trust-reader-quality/plan.md`
- **Template version**：`plan-task.v3`

## Phase P1 — Reader 信号、Agent 读者门与隔离出口

### Goal

让已有 Reader Bundle 在入口显示同一事实源的信任/生命周期信号，并完成 Reader-only Agent 小语料质量门和 `not_released` 出口；失败不覆盖旧包。

### Files

- **NEW**：`src/knowledge_digest/reader_quality.py`、`tests/acceptance/test_task2c_reader_quality.py`
- **MODIFY**：`src/knowledge_digest/reader_bundle.py`
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/cli.py`、`src/knowledge_digest/publication.py`：本任务是隔离的 Reader Bundle quality slice，不扩大到正式 S1-S6/CLI。
- **DO NOT TOUCH**：`src/knowledge_digest/identity.py`、`src/knowledge_digest/topic_axis.py`：不改变 TopicIndex 身份和 Task1 事实。
- **DO NOT TOUCH**：`src/knowledge_digest/reader_frontmatter.py`、`src/knowledge_digest/llm.py`、`src/knowledge_digest/lock.py`：已有窄接口足够，避免无必要 schema/provider/锁改动。
- **DO NOT TOUCH**：`config/task0-question-set.v1.json`：冻结输入只读，不临时改题。
- **DO NOT TOUCH**：`tests/acceptance/test_task2a_reader_bundle.py` 及 `tests/fixtures/task2a_reader_bundle/`：保留 Task2A 回归基线。
- **DO NOT TOUCH**：`apply/evidence/`、Task2B commit/evidence：只读交接事实，不重新生成或篡改。

### Tasks

- T001 RED → T002 GREEN：Reader signal/lifecycle projection 与导航过滤。
- T003 RED → T004 GREEN：冻结小题集、Reader-only Agent scorecard、答案和来源链门。
- T005 RED → T006 GREEN：失败隔离、重跑/并发边界和完整 exit manifest。
- T007 FINAL：Task2C + Task2A 当前快照聚合验证。

#### T001 — RED：锁定 Reader signal/lifecycle 的失败行为

- **ID**：T001
- **Phase**：Phase P1 — Reader 信号、Agent 读者门与隔离出口
- **goal**：增加会因入口信号缺失、信号伪造或 stale/deprecated 误降级而失败的 acceptance 断言。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2c-knowledge-publication-trust-reader-quality/spec.md","hash":"ebaac0fa4a80973206941464e81f90483926411d6d69c1bac753dbd0a10ead4b","id":"SPEC-T2C"},{"artifact_kind":"plan","ref":"specs/task2c-knowledge-publication-trust-reader-quality/plan.md","hash":"4c9f2891ad74ef57ed6ec590ad6e0af74ee4f60dc52a23e5c0c4926f02711621","id":"PLAN-T2C"}]`
- **source_refs / decision_refs**：R-001、R-002、R-004 / D-004、D-006 → FR-SIGNAL-001、FR-SIGNAL-002、FR-LIFE-001、FR-STATUS-001；AC-01、AC-02、AC-03
- **输入**：现有 `project_reader_bundle`、`validate_reader_bundle`、frontmatter trust/stale 字段和 Task2A fixtures。
- **依赖**：none
- **并行**：否 — first RED for this behavior
- **FR**：FR-SIGNAL-001、FR-SIGNAL-002、FR-LIFE-001、FR-STATUS-001、FR-READER-001
- **AC**：AC-01、AC-02、AC-03、AC-07
- **动作**：在新 acceptance 文件中覆盖根/产品/模块入口信号、mapping/list/缺失验证、既有事件与 Agent 不造 trust tier、未到期/到期/deprecated/unverified 状态，以及失败页退出默认导航、旧包不被覆盖；只增加测试，不改生产实现。
- **精确文件**：`tests/acceptance/test_task2c_reader_quality.py`
- **boundary**：files: `tests/acceptance/test_task2c_reader_quality.py`; symbols/regions: Task2C test helpers and signal/lifecycle cases only
- **输出**：RED 测试明确指出当前入口信号或状态映射缺口；负例必须在实现后仍保留。
- **Knowledge**：入口信号必须从现有 Bundle/Audit 事实重算；Agent 评审不得产生 `verified`、`machine-confirmed`、`human-reviewed`。
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'`
- **expected_exit**：-1
- **oracle**：`ORACLE-SIGNAL-LIFECYCLE` — 缺少必需入口信号、第二事实源、伪造 trust tier 或错误 degraded 判定必须被测试识别。
- **evidence_path**：`quality/evidence/T001-signal-lifecycle-red.txt`
- **STOP**：如果页面结构、frontmatter schema 或已有 trust 事实与规格不符，停止并回到 spec/plan；不临时增加字段契约。
- **recovery**：保留原始 RED 输出；由当前执行者只修正测试设计或回报 owning material 缺口。
- **task risk**：RED 只测静态字段、未测重算和负例，会把第二事实源带入实现。
- **test tier / test method**：fullstack / fullstack-slice-testing；路由顾问因 `src/`+`tests/` 跨顶层输出 fullstack，但本测试只用本地 Python fixtures。
- **scenarios / commands / expected exit / oracle**：入口信号完整、mapping/list/缺失验证、stale/deprecated 不误降级、坏 Audit/来源链失败、失败页退出默认导航且旧包保持不变；命令同 `gate_cmd`；RED 非零、GREEN 0；oracle `ORACLE-SIGNAL-LIFECYCLE`。
- **fixtures_services**：复用 `tests/fixtures/task2a_reader_bundle` 和 tmp_path；不启动服务、不读密钥，pytest 负责临时目录清理。
- **coverage limits**：覆盖本地投影和可见信号；不证明真实模型读者质量、不覆盖 89 条全量、不改正式 pipeline/CLI。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 Task2C signal/lifecycle acceptance；保留坏导航负例；无生产文件改动在 T001 阶段
- **executed_commands**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` → exit 2（collection ImportError）
- **evidence_refs**：`quality/evidence/T007-final-current-snapshot-v10.json`（结构化当前快照证据；历史 RED 原始记录仍由 executed_commands 说明）
- **covered_ac**：AC-01、AC-02、AC-03、AC-07（RED anchors）
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result
- **completed_at**：2026-08-12
- **执行事实**：RED 实际在 collection 阶段因待实现符号缺失而退出（exit 2）；该次没有执行行为断言，只证明实现尚不存在。对应负例在 T002 当前 GREEN 测试中保留并执行，未用 RED 结果冒充行为证据。

#### T002 — GREEN：实现单一事实源的 Reader signal/lifecycle 投影

- **ID**：T002
- **Phase**：Phase P1 — Reader 信号、Agent 读者门与隔离出口
- **goal**：让 T001 通过，并保留所有失败/负例边界。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2c-knowledge-publication-trust-reader-quality/spec.md","hash":"ebaac0fa4a80973206941464e81f90483926411d6d69c1bac753dbd0a10ead4b","id":"SPEC-T2C"},{"artifact_kind":"plan","ref":"specs/task2c-knowledge-publication-trust-reader-quality/plan.md","hash":"4c9f2891ad74ef57ed6ec590ad6e0af74ee4f60dc52a23e5c0c4926f02711621","id":"PLAN-T2C"}]`
- **source_refs / decision_refs**：同 T001：R-001、R-002、R-004 / D-004、D-006 → FR-SIGNAL-001、FR-SIGNAL-002、FR-LIFE-001、FR-STATUS-001；AC-01、AC-02、AC-03
- **输入**：T001 的真实失败断言；`reader_bundle.py:project_reader_bundle`、`_trust_events`、`validate_reader_bundle`、`_atomic_commit`。
- **依赖**：T001
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-SIGNAL-001、FR-SIGNAL-002、FR-LIFE-001、FR-STATUS-001、FR-READER-001
- **AC**：AC-01、AC-02、AC-03、AC-07
- **动作**：扩展已有 Bundle 投影与索引/页头渲染，复用现有 generated/verified/source/stale/page status 事实；增加确定性 trust/lifecycle 映射和明确 degraded 导航过滤，不新增第二事实源或 Agent/human trust event。
- **精确文件**：`src/knowledge_digest/reader_bundle.py`、`tests/acceptance/test_task2c_reader_quality.py`
- **boundary**：files: `src/knowledge_digest/reader_bundle.py`, `tests/acceptance/test_task2c_reader_quality.py`; symbols/regions: 现有 `project_reader_bundle` 的 signal/index writer、validation helper 和 Task2C tests；不得改 frontmatter schema/provider。
- **输出**：入口展示必需信号；stale/deprecated/unverified 不单独降级；必需事实或回查失败时明确 degraded 并退出默认导航，旧包不被覆盖。
- **Knowledge**：T001 RED 输出是唯一实现输入；不得弱化断言或删除负例来得到 GREEN。
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'`
- **expected_exit**：0
- **oracle**：`ORACLE-SIGNAL-LIFECYCLE` — 同 T001；成功信号为所有入口信号可从同一事实源重算，负例仍失败闭环。
- **evidence_path**：`quality/evidence/T002-signal-lifecycle-green.txt`
- **STOP**：若实现需要新增 `verified`/trust tier 权威、修改 Task2A schema、修改 CLI/pipeline 或放宽 deprecated/stale 语义，回到 spec/plan。
- **recovery**：只回滚 T002 当前实现修改，保留 T001 RED/GREEN 原始输出；不要重写 Task2A 基线。
- **task risk**：把可读投影写成新的事实源，或因便利把 stale/unverified 误写为 degraded。
- **test tier / test method**：与 T001 相同：fullstack / fullstack-slice-testing。
- **scenarios / commands / expected exit / oracle**：与 T001 相同，包含失败页退出默认导航和旧包保护；GREEN 0，oracle `ORACLE-SIGNAL-LIFECYCLE`。
- **fixtures_services**：与 T001 相同；无外部服务，tmp_path 清理。
- **coverage limits**：与 T001 相同；真实 provider 质量和 Task3 全量仍未覆盖。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：扩展 `reader_bundle.py` 的纯信号派生、页头信号和产品/模块导航展示；验证信号可从现有事实重算
- **executed_commands**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` → exit 0（8 passed）；聚合命令 → exit 0（42 passed）
- **evidence_refs**：`quality/evidence/T007-final-current-snapshot-v10.json`、`quality/evidence/test-routing-advisor-p1.json`（结构化当前快照证据；历史 GREEN 原始记录仍由 executed_commands 说明）
- **covered_ac**：AC-01、AC-02、AC-03、AC-07
- **review_fact**：N/A — build-code Phase review not executed
- **completed_at**：2026-08-12
- **执行事实**：信号字段从同一 frontmatter/Audit 事实派生；stale/deprecated 不自动写成 degraded；Task2A 回归聚合通过。

#### T003 — RED：锁定小题集覆盖、Reader-only 和 Agent-only 字段缺口

- **ID**：T003
- **Phase**：Phase P1 — Reader 信号、Agent 读者门与隔离出口
- **goal**：增加会因题集选择非确定、覆盖不足、Agent 读隐藏 Audit、字段缺失、答案与来源链脱节而失败的 acceptance 断言。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2c-knowledge-publication-trust-reader-quality/spec.md","hash":"ebaac0fa4a80973206941464e81f90483926411d6d69c1bac753dbd0a10ead4b","id":"SPEC-T2C"},{"artifact_kind":"plan","ref":"specs/task2c-knowledge-publication-trust-reader-quality/plan.md","hash":"4c9f2891ad74ef57ed6ec590ad6e0af74ee4f60dc52a23e5c0c4926f02711621","id":"PLAN-T2C"}]`
- **source_refs / decision_refs**：R-001、R-003、R-005 / D-001、D-002、D-005 → FR-GATE-001、FR-GATE-002、FR-GATE-003、FR-READER-002；AC-04、AC-05、AC-06
- **输入**：`config/task0-question-set.v1.json`、Task2B 已回查的正文出口、T002 的 Reader Bundle、`llm.py:call_llm` 注入 seam。
- **依赖**：T002
- **并行**：否 — consumes T002 signal projection
- **FR**：FR-GATE-001、FR-GATE-002、FR-GATE-003、FR-READER-002
- **AC**：AC-04、AC-05、AC-06
- **动作**：为 Task0 正负题派生、Task1 类别覆盖、Reader-only allowlist、三项 Agent-only 标记、逐题答案/边界/版本/来源回查和缺失字段失败增加 RED 测试，不改生产实现。
- **精确文件**：`tests/acceptance/test_task2c_reader_quality.py`
- **boundary**：files: 该测试文件；symbols/regions: question derivation, fake Agent response, scorecard and provenance cases only
- **输出**：RED 明确说明当前没有 Task2C quality gate 或字段/来源链不完整。
- **Knowledge**：Task2C 只做小样本：正向至少 8、负向 3，至少 2 product/module、2 page type；Task1 inventory 中实际存在的 long、table/image、bilingual、multi-source、failed/degraded 五类必须逐项有正向样本，或有 machine fixture 和明确排除理由；不能以“样本中碰巧没有”跳过；Agent 不得写 `human_reviewed`。
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'`
- **expected_exit**：-1
- **oracle**：`ORACLE-AGENT-READER-GATE` — 覆盖、Reader-only、逐题字段、答案+来源链和正负门槛缺口必须被识别。
- **evidence_path**：`quality/evidence/T003-agent-reader-gate-red.txt`
- **STOP**：如果要改 Task0 冻结题集、改变 8/3 门槛、允许 Audit 补答案或让 Agent 结果产生 trust tier，回到 decision-log/spec。
- **recovery**：保留 RED 失败样本和输入 hash；只修正测试边界或上游规格，不写临时生产兜底。
- **task risk**：测试使用了 Audit/Archive 隐藏答案，导致隔离假通过。
- **test tier / test method**：fullstack / fullstack-slice-testing；fake provider 和 tmp_path，不联网。
- **scenarios / commands / expected exit / oracle**：正向全命中、负向零误命中、少于 8、产品/页面类别缺失、Task1 inventory 实际存在的 long/table-image/bilingual/multi-source/failed-degraded 任一类别既无正向样本也无 machine fixture+明确排除理由、Reader-only 越界、三字段/来源链/答案字段缺失；同 `gate_cmd`；RED 非零、GREEN 0；oracle `ORACLE-AGENT-READER-GATE`，覆盖矩阵逐项可回查。
- **fixtures_services**：Task0 frozen JSON、Task2A fixture bundle、Task2B evidence refs 只读；fake `call_llm`；pytest 清理临时 output。
- **coverage limits**：证明程序的隔离与门槛，不证明真实 qwen 模型稳定性，不做 89 条全量。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 Task2C question/Reader-only/scorecard acceptance；未读 Audit 答案
- **executed_commands**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` → exit 2（缺 `reader_quality.py`）
- **evidence_refs**：`quality/evidence/T007-final-current-snapshot-v10.json`（结构化当前快照证据；历史 RED 原始记录仍由 executed_commands 说明）
- **covered_ac**：AC-04、AC-05、AC-06
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result
- **completed_at**：2026-08-12
- **执行事实**：RED 实际在 collection 阶段因 `reader_quality.py` 缺失而退出（exit 2）；该次没有执行行为断言，只证明质量门尚不存在。对应负例在 T004 当前 GREEN 测试中保留并执行，未用 RED 结果冒充行为证据。

#### T004 — GREEN：实现 Reader-only Agent 小语料质量门

- **ID**：T004
- **Phase**：Phase P1 — Reader 信号、Agent 读者门与隔离出口
- **goal**：让 T003 通过，保存逐题可回放证据，并拒绝所有隐藏资料/缺字段/来源断裂负例。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2c-knowledge-publication-trust-reader-quality/spec.md","hash":"ebaac0fa4a80973206941464e81f90483926411d6d69c1bac753dbd0a10ead4b","id":"SPEC-T2C"},{"artifact_kind":"plan","ref":"specs/task2c-knowledge-publication-trust-reader-quality/plan.md","hash":"4c9f2891ad74ef57ed6ec590ad6e0af74ee4f60dc52a23e5c0c4926f02711621","id":"PLAN-T2C"}]`
- **source_refs / decision_refs**：同 T003：R-001、R-003、R-005 / D-001、D-002、D-005 → FR-GATE-001、FR-GATE-002、FR-GATE-003、FR-READER-002；AC-04、AC-05、AC-06
- **输入**：T003 RED 断言；Task0 frozen labels/rules；T002 Reader Package；环境 provider contract；测试注入 fake `call_llm`。
- **依赖**：T003
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-GATE-001、FR-GATE-002、FR-GATE-003、FR-READER-002
- **AC**：AC-04、AC-05、AC-06
- **动作**：新增 `reader_quality.py` 的窄接口，确定性派生题集和覆盖矩阵；只把 Reader allowlist 内容送入 Agent；结构化记录全部逐题字段、输入/提示/模型/seed/hash、答案、边界/版本、来源回查和失败原因；计算正负门槛，不创建 trust tier/human event。
- **精确文件**：`src/knowledge_digest/reader_quality.py`、`tests/acceptance/test_task2c_reader_quality.py`
- **boundary**：files: `src/knowledge_digest/reader_quality.py`, `tests/acceptance/test_task2c_reader_quality.py`; symbols/regions: new question/scorecard/quality result types and Task2C tests；不得改 provider seam、Task0 JSON、Claim/Evidence authority。
- **输出**：小语料覆盖可重放；正向至少 8 全命中、负向 3 零误命中；答案+边界/版本+来源链缺一失败；Agent-only 三字段显式存在，`human_reviewed` 不出现。
- **Knowledge**：T003 的 RED 失败事实；真实 provider 不作为 acceptance fake 的替代；Task1 五类 inventory 覆盖矩阵是硬门；Task2B live baseline refs 固定但仍需 preflight。
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'`
- **expected_exit**：0
- **oracle**：`ORACLE-AGENT-READER-GATE` — 同 T003；成功是所有正向、负向、覆盖、隔离、字段和来源链断言闭环。
- **evidence_path**：`quality/evidence/T004-agent-reader-gate-green.txt`
- **STOP**：需要临时降低门槛、让 Audit/Archive 进入 prompt、把 Agent 记成 human/verified、改变 Task2B source chain 或新增未决产品行为时，回到 owning material。
- **recovery**：只回滚 `reader_quality.py`/对应测试修改；保留 T003/T004 原始 evidence 和既有 Reader Bundle。
- **task risk**：模型 JSON 解析“宽松兜底”掩盖缺字段，或 scorecard 保存了答案却没有稳定 source locator。
- **test tier / test method**：与 T003 相同：fullstack / fullstack-slice-testing，fake provider、离线、tmp_path。
- **scenarios / commands / expected exit / oracle**：与 T003 相同，特别包含五类 inventory 逐项样本或 machine fixture+明确排除理由；GREEN 0，oracle `ORACLE-AGENT-READER-GATE`。
- **fixtures_services**：与 T003 相同；无外部服务，凭据不进测试或 evidence。
- **coverage limits**：覆盖程序规则与数据边界；不把 fake 结果升级为真实模型质量、不覆盖 Task3 全量。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 `reader_quality.py` 的冻结题集派生、Reader 快照、Agent-only scorecard、答案/来源链回查和失败闭环
- **executed_commands**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q'` → exit 0（56 passed；Task2C 22、Task2A 34）
- **evidence_refs**：`quality/evidence/T007-final-current-snapshot-v10.json`
- **covered_ac**：AC-04、AC-05、AC-06
- **review_fact**：修复后 P1 当前审查 `quality/reviews/results/build-code-default-ed175006cbfe85a071807b24698e274c1aba738b-20b5afc5-cf59-40d0-86aa-ab01d8e1691d.json`；无 actionable major/blocking，5 个 minor 建议保留为后续改进，不阻断本 Phase。主要修复已验证：机器 inventory 覆盖、dead-lock owner 重跑、真实 provider 参数映射、来源链失败和 Reader-only 隔离。
- **completed_at**：2026-08-12
- **执行事实**：正向 8/8、负向 3/3；Reader-only prompt 去除内部 Audit 指针；真实 `knowledge_digest.llm.call_llm` 参数映射分支已由不联网 stub 覆盖；来源链断裂（含 Evidence 文件缺失）失败；生产投影按绝对日期显示 stale；缺字段、缺 inventory、矛盾答案失败；交付仍 not_released。

#### T005 — RED：锁定失败隔离、重跑/并发和 exit manifest 缺口

- **ID**：T005
- **Phase**：Phase P1 — Reader 信号、Agent 读者门与隔离出口
- **goal**：增加会因失败覆盖旧包、取消/并发产生第二事实源、预算/凭据/commit/Agent 字段缺失或误标 `released` 而失败的 acceptance 断言。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2c-knowledge-publication-trust-reader-quality/spec.md","hash":"ebaac0fa4a80973206941464e81f90483926411d6d69c1bac753dbd0a10ead4b","id":"SPEC-T2C"},{"artifact_kind":"plan","ref":"specs/task2c-knowledge-publication-trust-reader-quality/plan.md","hash":"4c9f2891ad74ef57ed6ec590ad6e0af74ee4f60dc52a23e5c0c4926f02711621","id":"PLAN-T2C"}]`
- **source_refs / decision_refs**：R-002、R-004、R-005 / D-003、D-004、D-006 → FR-RUN-001、FR-EXIT-001、FR-STATUS-001；AC-07、AC-08、AC-09
- **输入**：T004 quality result、现有 `_atomic_commit`/staging、`kb_lock` 约束和已有 exit manifest。
- **依赖**：T004
- **并行**：否 — consumes quality result and signal contract
- **FR**：FR-RUN-001、FR-EXIT-001、FR-STATUS-001
- **AC**：AC-07、AC-08、AC-09
- **动作**：增加失败 provider、来源回查、取消/重跑/并发、预算缺失、入口污染和 `released` 误标的 acceptance 断言；只增加测试，不改生产实现。
- **精确文件**：`tests/acceptance/test_task2c_reader_quality.py`
- **boundary**：files: 该测试文件；symbols/regions: failure isolation, replay/concurrency seam, exit manifest cases only
- **输出**：RED 明确当前缺少 Task2C 完整出口或隔离行为。
- **Knowledge**：Task2C 即使 Agent gate 通过也必须 `not_released`；旧正式包不能被失败运行覆盖。
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'`
- **expected_exit**：-1
- **oracle**：`ORACLE-ISOLATION-EXIT` — 失败/取消/并发/重跑和 exit 字段缺口必须被识别。
- **evidence_path**：`quality/evidence/T005-isolation-exit-red.txt`
- **STOP**：如果要改为覆盖式写入、引入后台队列/数据库、把 release 交给 Task2C，回到 decision-log/spec。
- **recovery**：保留旧包 hash 和 RED 输出；只修测试或回报边界缺失。
- **task risk**：只测最终 JSON，不测旧包 hash/atomic boundary，导致半成品覆盖无法发现。
- **test tier / test method**：fullstack / fullstack-slice-testing；使用 tmp_path、fake provider 和可控 lock seam，不启动服务。
- **scenarios / commands / expected exit / oracle**：provider/来源/质量失败、取消、同输入 replay、并发单写者、完整 exit manifest、`not_released`；同 `gate_cmd`；RED 非零、GREEN 0；oracle `ORACLE-ISOLATION-EXIT`。
- **fixtures_services**：T2A fixture bundle、fake provider、tmp_path；不联网、不用密钥，pytest 清理。
- **coverage limits**：覆盖本地失败隔离和出口字段；不授权 Git delivery、正式 release 或 Task3 全量。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 provider 失败、取消、重跑、并发、旧包 hash、scorecard hash 和出口字段失败断言
- **executed_commands**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` → RED exit 1（scorecard hash 不一致）
- **evidence_refs**：`quality/evidence/T007-final-current-snapshot-v10.json`（结构化当前快照证据；历史 RED 原始记录仍由 executed_commands 说明）
- **covered_ac**：AC-07、AC-08、AC-09
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result
- **completed_at**：2026-08-12
- **执行事实**：红灯锁定可回放 scorecard/hash 一致性缺口；未把测试误报为功能通过，进入 T006。

#### T006 — GREEN：完成失败隔离与 Task2C not_released 出口

- **ID**：T006
- **Phase**：Phase P1 — Reader 信号、Agent 读者门与隔离出口
- **goal**：让 T005 通过，并把质量门与 Reader Bundle 的写入边界连成一次可回放、不可误发布的出口。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2c-knowledge-publication-trust-reader-quality/spec.md","hash":"ebaac0fa4a80973206941464e81f90483926411d6d69c1bac753dbd0a10ead4b","id":"SPEC-T2C"},{"artifact_kind":"plan","ref":"specs/task2c-knowledge-publication-trust-reader-quality/plan.md","hash":"4c9f2891ad74ef57ed6ec590ad6e0af74ee4f60dc52a23e5c0c4926f02711621","id":"PLAN-T2C"}]`
- **source_refs / decision_refs**：同 T005：R-002、R-004、R-005 / D-003、D-004、D-006 → FR-RUN-001、FR-EXIT-001、FR-STATUS-001；AC-07、AC-08、AC-09
- **输入**：T005 RED 断言；T004 `QualityGateResult`；现有 staging/atomic commit/lock 事实。
- **依赖**：T005
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-RUN-001、FR-EXIT-001、FR-STATUS-001
- **AC**：AC-07、AC-08、AC-09
- **动作**：实现单写者/临时输出边界、失败回滚和稳定 replay；生成包含 Concept Contract、page types、signal fields、template、question derivation、scorecard、Agent-only 字段、seed/threshold、provider/config、call/wall-clock budget、credential source、commit 和状态的 exit manifest；状态固定为 `not_released`。
- **精确文件**：`src/knowledge_digest/reader_quality.py`、`src/knowledge_digest/reader_bundle.py`、`tests/acceptance/test_task2c_reader_quality.py`
- **boundary**：files: `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/reader_bundle.py`, `tests/acceptance/test_task2c_reader_quality.py`; symbols/regions: quality output/manifest integration and existing atomic writer seam；不得修改正式 pipeline/CLI 或 release authority。
- **输出**：失败不覆盖旧包；同输入稳定投影；出口字段齐全、可回放、明确 `not_released`。
- **Knowledge**：T005 RED 的旧包 hash、失败注入和缺字段事实；不存在第二状态权威。
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'`
- **expected_exit**：0
- **oracle**：`ORACLE-ISOLATION-EXIT` — 同 T005；成功包括负例、旧包保护、replay 和 not_released exit。
- **evidence_path**：`quality/evidence/T006-isolation-exit-green.txt`
- **STOP**：需要发布 `released`、改变现有 lock/atomic contract、写真实密钥、或无法把失败保留在 Audit/Reports 时，回到 spec/plan。
- **recovery**：只回滚 Task2C 当前实现；保留旧 Reader Bundle、失败 evidence 和 Task2B baseline。
- **task risk**：为了让并发测试通过而增加隐藏队列/数据库，或把质量通过误写成交付发布。
- **test tier / test method**：与 T005 相同：fullstack / fullstack-slice-testing。
- **scenarios / commands / expected exit / oracle**：与 T005 相同；GREEN 0，oracle `ORACLE-ISOLATION-EXIT`。
- **fixtures_services**：与 T005 相同；fake provider、tmp_path、现有 lock/staging；不联网。
- **coverage limits**：覆盖 Task2C 本地运行边界；不证明 Git 交付、formal release、Task3 全量或真实模型长期稳定性。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：补齐质量输出单写者 lock、取消清理、稳定 scorecard/hash、完整 Task2C exit manifest；固定 not_released
- **executed_commands**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` → exit 0（20 passed）
- **evidence_refs**：`quality/evidence/T007-final-current-snapshot-v10.json`
- **covered_ac**：AC-07、AC-08、AC-09
- **review_fact**：修复后当前集成审查曾发现并修复 `kb_lock` 异常上下文丢失；当前树 `a0fb479452c6f9f8328bd398aceee1fc804f2118` 的集成审查为 `quality/reviews/results/build-code-default-a0fb479452c6f9f8328bd398aceee1fc804f2118-fedd0b33-460a-450e-8ffd-3d1932d8959b.json`，有效 reviewer 没有 actionable major/blocking，仅 3 个 minor 建议；另一个 provider 的历史 `OUTPUT_INVALID`/不可用事实不当作通过。P1 phase review 当前树为 `quality/reviews/results/build-code-default-a0fb479452c6f9f8328bd398aceee1fc804f2118-a437531e-9609-4525-b2ad-ee806f3cd0c1.json`；严重条目均为 `invalid_evidence`，无可采纳的严重 finding，minor 建议保留为风险/延期。
- **completed_at**：2026-08-12
- **执行事实**：失败不改 Reader Bundle；取消不残留 staging；同输入 scorecard 稳定；并发只有一个 writer；实际 provider seam 参数完整；出口含题集、阈值、provider、预算、凭据、review_date、Evidence root 和 commit。

#### T007 — FINAL：当前快照聚合验证

- **ID**：T007
- **Phase**：Phase P1 — Reader 信号、Agent 读者门与隔离出口
- **goal**：按计划固定的最终路线一次性验证全部适用 AC、跨任务 seam 和 Task2A 回归，不创建第二状态权威。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2c-knowledge-publication-trust-reader-quality/spec.md","hash":"ebaac0fa4a80973206941464e81f90483926411d6d69c1bac753dbd0a10ead4b","id":"SPEC-T2C"},{"artifact_kind":"plan","ref":"specs/task2c-knowledge-publication-trust-reader-quality/plan.md","hash":"4c9f2891ad74ef57ed6ec590ad6e0af74ee4f60dc52a23e5c0c4926f02711621","id":"PLAN-T2C"}]`
- **source_refs / decision_refs**：R-001～R-005 / D-001～D-006 → 全部 FR、AC-01～AC-09
- **输入**：T002、T004、T006 完成事实和最终当前 worktree。
- **依赖**：T006
- **并行**：否 — aggregate reads all preceding task facts
- **FR**：FR-SIGNAL-001/002、FR-LIFE-001、FR-STATUS-001、FR-GATE-001/002/003、FR-READER-001/002、FR-EXIT-001、FR-RUN-001
- **AC**：AC-01～AC-09
- **动作**：只执行最终聚合检查并记录真实命令、退出码、oracle、覆盖范围、Task2B baseline refs 和剩余风险；不补实现、不改阈值、不创建新状态权威。
- **精确文件**：`src/knowledge_digest/reader_quality.py`、`src/knowledge_digest/reader_bundle.py`、`tests/acceptance/test_task2c_reader_quality.py`
- **boundary**：files: `src/knowledge_digest/reader_quality.py`, `src/knowledge_digest/reader_bundle.py`, `tests/acceptance/test_task2c_reader_quality.py`; symbols/regions: aggregate verification only；Task2A tests 作为只读回归输入。
- **输出**：Task2C targeted acceptance 与 Task2A Reader Bundle tests 的当前快照事实，以及明确未覆盖项。
- **Knowledge**：所有 paired GREEN 的真实输出；review/analysis 是事实，不是通过许可证。
- **verification_role**：N/A — non-behavior aggregate verification
- **paired_task**：N/A — aggregate has no RED/GREEN pair
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q'`
- **expected_exit**：0
- **oracle**：`ORACLE-FINAL` — 所有适用 AC、三组跨任务 seam、Task2A 回归通过，且输出不声称 formal release。
- **evidence_path**：`quality/evidence/T007-final-current-snapshot.json`
- **STOP**：命令不可执行、任一 AC 无证据、Task2A 回归失败、Task2B baseline 漂移、出现越界修改或需要新决策时停止并回到 owning material。
- **recovery**：保留完整原始输出，回到受影响 paired task；不得用全量测试掩盖局部失败。
- **task risk**：把 targeted green、review 或 latest provider 状态误报成 Task2C released/全量成功。
- **test tier / test method**：fullstack / fullstack-slice-testing；路由事实为 fullstack，命令是本地 pytest slice + Task2A compatibility。
- **scenarios / commands / expected exit / oracle**：成功、失败、状态、来源链、旧包保护、replay、Task2A seam；命令同 `gate_cmd`；预期 0；oracle `ORACLE-FINAL`。
- **fixtures_services**：Task2A fixture、Task0 frozen JSON、fake provider；无 HTTP/DB/真实 key，临时目录由 pytest 清理。
- **coverage limits**：覆盖 Task2C 实现与 Task2A Reader Bundle 回归；不覆盖 89 条全量、真实 provider 长期质量、Task3 release、Git delivery。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：只读聚合当前 Task2C 与 Task2A acceptance 结果
- **executed_commands**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q'` → exit 0（56 passed；Task2C 22、Task2A 34）
- **evidence_refs**：`quality/evidence/T007-final-current-snapshot-v10.json`
- **covered_ac**：AC-01～AC-09
- **review_fact**：P1 phase review 在当前材料包上按标准 CLI 记录为 unavailable/incomplete（packet 超过 330 KiB，provider 未启动）；最后一次为 `quality/reviews/attempts/8565a046-200f-4f52-938d-3131916b1227/attempt.json`。修复后的最终集成审查 `quality/reviews/results/build-code-default-40c5c4e70a2a90f0b1b45428b7ca82d964186e4f-fcc460e0-79dc-480c-9590-26bf3dfee827.json` 有 1 个有效异源 reviewer，无可采纳 major/blocking；另一 provider 输出无效，host provider 为 same-source，均不改写成通过。此前 `F-dff414932051` 的 trust-tier 矛盾已 fixed。
- **completed_at**：2026-08-12
- **执行事实**：当前工作树的完整 `uv run --frozen pytest -q` 当前收据为 `quality/tests/build-code-task2c-current-20260813-v10.json`，exit 0（549 passed、3 skipped），快照树 `de96911ae68ab024a84f1b2a566a59a777455723`；当前实现收据为 `quality/evidence/implementation/93a074afa1270e03d889ee461d5329ece59d44aa921f68da0ba3b0bb920b17b2.json`。`git diff --check` 通过；Task0 题集和 Task2B handoff hash 已纳入当前测试夹具；未声称 89 条全量、Task3 release 或 Git delivery。真实 provider 在同一兼容性修复上先有一次 8/8 正向、3/3 负向通过，随后当前树再次运行变为 8/8 正向但 2 个负向误命中，程序 fail-closed；因此真实 provider 稳定性保持 unknown。
- **追加验证事实（2026-08-13）**：`rightapi/deepseek-v4-flash` 当前实现连续三次 11 题 Reader-only 运行均保持 `delivery_status=not_released`，但真实 provider 质量未稳定通过：第一次 `4/8` 正向命中、`3/3` 负向有效 `no_match`，其余正向 provider 失败；第二次 `7/8` 正向命中、`3/3` 负向有效 `no_match`，一个正向请求超时；第三次 `8/8` 正向命中，但 `negative-02` 返回空内容，只有 `2/3` 负向有效 `no_match`，程序按 fail-closed 拒绝。三次都证明异常响应不会伪装成成功；当前真实读者门仍是 `unknown/failed`，不能宣称 Task2C 真实门通过，也未扩展为 89 条全量、Task3 release 或 Git delivery。

- **Verify-code 验收事实（2026-08-13）**：架构师反向检查已覆盖原始 PRD、scope revision、四份材料、完整用户流程、页面/数据状态、成功/失败/恢复边界、非目标、延期项和 AC-01～AC-09。异源 verify review `quality/reviews/results/verify-code-default-76645ecd4d906d8a16c663604300a55c24ff5822-483faddd-0c43-48fa-9544-5fb47569ce60.json` 曾根据 provider 汇总数字提出 AC-06 风险；回读原始 scorecard 证实当次运行的 3 个负向题实际都有完整有效 `no_match`，该 finding 处置为 `rejected_invalid`（汇总推断与逐题证据矛盾），不是代码问题。此前 verify receipt `quality/tests/verify-code-task2c-current-20260813-v4.json` 曾为 exit 0（547 passed、3 skipped）；其余未决项保持 unknown/deferred；delivery_status 仍为 `not_released`。verify review 绑定的是修复前的代码快照，后续只改任务事实记录，未重新开启审查轮。

- **追加真实运行事实（2026-08-13）**：在同一实现上对 `rightapi/deepseek-v4-flash` 又做了两次 11 题 Reader-only 运行。第一次为 `failed/not_released`：7/8 正向命中、1 个正向请求 90 秒超时，3/3 负向题完整 `no_match` 且无误命中；第二次为 `failed/not_released`：8/8 正向命中，但 `negative-02` 返回空内容而不是 JSON，程序按 fail-closed 拒绝，只有 2/3 负向题有效 `no_match`，不能算真实门通过。两次运行都证明异常响应不会被伪装成成功；真实 provider 稳定性和当前整包读者门仍是 `unknown`，不扩展为 89 条全量或 release。

- **追加参数诊断事实（2026-08-13）**：保持同一当前实现、同一题集和 `rightapi/deepseek-v4-flash`，把单次 `max_tokens` 从 4096 降到 1024 后运行仍为 `failed/not_released`：多次 503、截断/空 JSON，只有 2 个正向命中、1 个有效负向 `no_match`，2 个负向响应被拒绝。降低输出预算没有消除问题，因此不能把真实门失败归因于本地输出上限；provider/接口稳定性仍为 `unknown`。临时诊断脚本未纳入项目。

- **追加兼容性修复与真实运行事实（2026-08-13）**：旧实现虽然已有 `json_mode=true` 配置，却没有把它传入项目 LLM 调用；对非 qwen 的 OpenAI-compatible provider 也没有按该配置请求 JSON 响应。修复仅补齐既有配置的传递和 `response_format=json_object` 请求，不改变 provider 身份、题集、阈值、Reader-only 路由或交付状态。修复后聚焦测试 `106 passed`，全量 `uv run --frozen pytest -q` 为 `548 passed, 3 skipped`。随后用同一冻结 11 题、同一 Reader-only 路由和 `rightapi/deepseek-v4-flash` 做当前真实运行：`status=passed`、`delivery_status=not_released`、8/8 正向命中、3/3 负向完整 `no_match`、0 failures、0 false positives。密钥只通过临时环境变量传入，未写入项目或证据。该结果证明当前兼容性修复下本次真实门通过，但不证明 provider 长期稳定、89 条全量、Task3 release 或 Git delivery。

- **追加 P1 phase review 事实（2026-08-13）**：按标准 `wh-review-cli.mjs run` 重跑当前 P1 phase review；旧输入和修复后输入均由 WorkflowHub 在 provider 调用前以 `MATERIAL_INCOMPLETE` 结束，原因是 phase packet 超过 330 KiB 硬上限，provider 未启动、没有 semantic finding。最后一次 attempt 为 `quality/reviews/attempts/8565a046-200f-4f52-938d-3131916b1227/attempt.json`，报告为 `quality/reviews/reports/8565a046-200f-4f52-938d-3131916b1227.md`，当前快照为 `79632cf92310c738ea9228a710315cf9c8295316`。该事实是 review unavailable/incomplete，不当作通过；未再用同一快照盲目重试。

- **追加集成审查与修复事实（2026-08-13）**：最终集成审查第一次发现 `derive_reader_signals` 会投影 `human-reviewed`，但同文件 validator 又拒绝 `human:` actor；该 finding `F-dff414932051` 为真实 major，已修复为 Task 2-C 只投影既有机器事件或 `unverified`，并新增人工事件不产生读者 trust tier 的回归测试。修复后全量为 `549 passed, 3 skipped`；当前实现收据为 `quality/evidence/implementation/c2fabb5c31d594a0af5aaa06438682ade3bc888577ba5269576b6880faf4ea37.json`，当前集成审查为 `quality/reviews/results/build-code-default-40c5c4e70a2a90f0b1b45428b7ca82d964186e4f-fcc460e0-79dc-480c-9590-26bf3dfee827.json`，有效 reviewer 无可采纳 finding；另一个 provider 输出无效、host provider 为 same-source，均如实保留。

- **追加当前树真实 provider 事实（2026-08-13）**：在上述修复后的当前实现、冻结 11 题和 Reader-only 路由上再次调用 `rightapi/deepseek-v4-flash`：8/8 正向命中，但 3 个负向题只有 1 个完整 `no_match`，2 个误命中，程序按 fail-closed 记为 `status=failed`、`delivery_status=not_released`、8 failures。此前同一兼容性修复下曾有一次 8/8 正向、3/3 负向通过；两次结果矛盾，说明当前 provider 读者质量不稳定，保持 `unknown`，不能宣称真实门稳定通过。密钥仍只经环境变量传入，临时脚本不纳入项目。

- **Verify-code 最终事实（2026-08-13）**：架构师反向核对了原始 PRD、当前 decision-log/spec/plan/tasks、完整用户流程、页面范围、数据状态、成功/失败/恢复边界、非目标、延期项和 AC-01～AC-09。最终当前全量收据为 `quality/tests/build-code-task2c-current-20260813-v11.json`：`549 passed, 3 skipped`，快照树 `e141fd11615352e5c945750621053b9f9ec10d2c`；这只证明本地实现，不替代真实模型语义门。异源 verify review 为 `quality/reviews/results/verify-code-default-e4f07d8e032b484859e9e148500c946d93210488-61561ed8-90c1-4b17-9fdd-e23cb752930d.json`，有效 reviewer 提出 major `F-322f10cbf402`：真实 provider 最近一次有 2 个负向误命中，不能把 pytest 全绿当作 AC-06 通过；该 finding 已按建议处置为“保持 failed/not_released、做一次最终真实复查”，不是伪装成 pass。最终真实复查仍失败：5/8 正向命中、3/3 负向误命中、`status=failed`、`delivery_status=not_released`。因此 AC-01/02/03/07/08/09 为本地实现 pass，AC-04 为实现门 pass 但 89 条生产全量 deferred，AC-05 为 Reader-only 合同 pass、外部模型行为 unknown，AC-06 为 unknown；总体 verify-code 结论为 `incomplete`，不得 close/release。verify review 的 minor 供应商稳定性建议保留为延期风险，未获用户风险接受。最终实现收据为 `quality/evidence/implementation/1e8fa9e1926beba857f8434867310e967dc35d5349a0a70e50cf1a194eefb312.json`；最后仅追加了本条事实，所以该 verify review 的审查快照仍按代码/需求语义有效，但当前最终收据应以 v11 为准。

- **追加 scorecard 口径修复事实（2026-08-13）**：发现 provider 缺失/非法响应会被旧汇总逻辑计入 `negative_false_positives`，混淆“模型明确误命中”和“provider/响应合同失败”。现已限定语义误命中只统计 `answer_found=true` 或 `answer_result=hit`；缺字段仍逐题失败并保持总状态 `failed/not_released`。新增回归后，聚焦测试 `108 passed`，全量为 `550 passed, 3 skipped`；当时生成 v12 测试/实现收据。未重跑真实 provider，既有真实门失败/unknown 事实保留。

- **追加 build-code 修复事实（2026-08-13）**：针对集成审查发现的真实 provider 负向题误命中风险，补强 Reader-only prompt：负向题必须检查题目点名对象的直接证据，不能用相似词、不同产品、历史文字或“缺少证据”的推断代替 `no_match`；同时把内部链接按目标脱敏，保留正文中提到 `_digest/` 等字样。另将旧调用路径默认强制 `json_mode=true`，确保 Reader JSON 合同不依赖调用方是否带配置。新增回归后聚焦为 `110 passed`，全量 `552 passed, 3 skipped`；当前测试收据为 `quality/tests/build-code-task2c-current-20260813-v14.json`，receipt hash `d9c5aabc93223ad9c29b00f4b04d32e9554fb749d5ad370a5bf45ad6313b490b`，快照树 `af4c430406548cc120d21fc59e34fe2ad79b1cd1`；当前实现收据为 `quality/evidence/implementation/114e8b0b607e222f3c2124c10d4939fb6b342f73b22b9b50195b53882c0ba3e0.json`。最新 build-code 集成审查为 `quality/reviews/results/build-code-default-7147833da8a723119f80d648dcf7ae2fd8056941-bee9f312-3aad-4ff7-bf3d-52c1fd31ae47.json`，有效 reviewer 只报告了两个 `major/invalid_evidence`，无有效 major/blocking finding；同源 host provider 和另一个 provider 无效均如实保留。未重跑 verify review；原 verify 的真实门结论仍有效：`unknown/failed`、`not_released`。

- **追加 verify 当前快照真实运行事实（2026-08-13）**：重新读取原始 PRD、当前 decision-log/spec/plan/tasks，并按完整流程核对入口（Home → index → 产品/模块索引 → concept 页）、成功门（答案+来源链）、失败门（provider/响应合同失败仍 fail-closed）、恢复门（取消/重跑/并发不覆盖旧包）、非目标（89 条全量、Task 3 release、Git delivery）和延期项。当前工作树 `HEAD=7cf8c40e6703c8284527d74b2cec8bf2d60119d8` 的本地完整测试收据仍为 v14，快照树 `af4c430406548cc120d21fc59e34fe2ad79b1cd1`，exit 0；最新 build-code review 的有效 reviewer 没有可采纳 major/blocking，另有 provider invalid/same-source 事实保持原样。

- **追加 verify 真实 provider 事实（2026-08-13）**：使用当前代码快照、冻结 11 题、Reader-only 路由和临时环境凭据，对 `rightapi/deepseek-v4-flash` 连续执行两次完整运行；两次均为 `status=passed`、`delivery_status=not_released`、8/8 正向命中、3/3 负向 `no_match`、0 failures、0 negative false positives。第一次 scorecard hash 为 `0f84a400b77724821c9856df33c8de10545a801b8f828a2ee7145611c8dd21ae`，第二次为 `d6d9cc2b001e5da9b5e8896d83afe4e7caa76474ce9769ceb6c65d935ec01dab`；运行根目录只在临时目录，凭据来源为 environment，未写入项目或证据。该事实足以把当前小语料 AC-04/AC-05/AC-06 的真实 provider 结果更新为 `pass`，但不证明长期稳定性、89 条全量或 Task 3 release；交付仍为 `not_released`。

- **追加真实 provider 持久证据事实（2026-08-13）**：已将上述两次完整运行的 `scorecard.json`、`exit-manifest.json` 和 `run-report.json` 固化为任务库内容寻址证据：`quality/evidence/real-reader-gate-run-40425a7d31c887a21a24c45a75b6ecae3d9263bde6833e2a8f6d621f936fe2c7.json`（run `f876578606714645`）和 `quality/evidence/real-reader-gate-run-db5b8af7a4f96e91551c11ccfa640343c0d78115056a6ce4b7b5ec6e35daa369.json`（run `2eb98700bb86cee8`）。两条证据均为 8/8 正向、3/3 负向、0 failure；凭据未写入证据。该持久化只增强可回放性，不改变“历史运行矛盾、长期稳定性 unknown、交付 not_released”的结论。

- **追加当前完整测试收据事实（2026-08-13）**：持久化真实运行证据后，未改生产代码；重新执行 `uv run --frozen pytest -q`，退出码 0，`552 passed, 3 skipped`。最新收据为 `quality/tests/build-code-task2c-current-20260813-v16.json`，快照树 `49e19e9c3f06825b631d52d6d285c1daf261d96c`；实现收据为 `quality/evidence/implementation/238d8919c8617ad0ba6e9d9d1038219f7edea079d43db175c21d6dafada15fb0.json`。这是文档/证据变更后的当前事实，不改变真实 provider 长期稳定性 unknown 或 not_released 边界。

- **追加最终真实复测事实（2026-08-13）**：在当前 worktree、同一冻结 11 题、`rightapi/deepseek-v4-flash`、`json_mode=true` 和 900 秒总预算下连续执行 3 次；3 次均为 `status=passed`、8/8 正向、3/3 负向、0 failures、`not_released`。持久证据分别为 `quality/evidence/real-reader-gate-run-3a91b9d5a7b0c32c24d572016087c7019cc5750610cb738247a6bb3abc26f733.json`、`quality/evidence/real-reader-gate-run-7974b92c91ac7c5847c010ec1ee9c1f064a7ce8d19ac61d5c5ddf5e060890b9b.json`、`quality/evidence/real-reader-gate-run-d8fc1c8aebd613a55e3b7944169379bffcdee0c4ba9048363fb38f61c678803d.json`。同批相邻记录 `quality/evidence/real-reader-gate-run-43b8a4cb9fa86ac2cd774e55e13d816526f0b9d048e35442197ba8832c241f00.json` 为 provider 子进程无返回、`status=failed`、44 failures；该失败不隐藏。综合结论仍是当前小语料功能可运行，但 provider/网络稳定性 `unknown`，不能 close/release。

- **追加最终完整测试事实（2026-08-13）**：上述真实复测后未改生产代码；重新执行完整命令 `uv run --frozen pytest -q`，退出码 0，`552 passed, 3 skipped`。最终当前收据为 `quality/tests/build-code-task2c-current-20260813-v18.json`，快照树 `40af24ac500181bdba6aba3e51f82d63b6c44513`；实现收据为 `quality/evidence/implementation/a71f427259bcdc20ec059aee4915c435937d49fe6302474db51b7587632639eb.json`。`git diff --check` 通过；未执行 Git 交付或清理。

### 追加本轮 build-code 修复事实（2026-08-13）

- 针对阶段审查暴露的两个真实边界补最小修复：`reader_quality._manifest_pages` 在 mapping manifest 路径同样排除 `degraded`/`deprecated` 页面；`_inventory_observed_features` 将 inventory 中的数值计数按“有记录”处理，不再把 `0`/`1` 误当布尔值。
- 新增两条回归：mapping manifest 不抽样 degraded 页面；numeric inventory feature 能触发缺失覆盖失败。跨 Task2A seam 与 Task2C gate 聚焦命令退出 0，`73 passed`；`git diff --check` 通过。
- 当前代码仍未宣称阶段完成；待生成当前全量测试/实现收据、补当前 P1 审查和真实 provider 复测，再进入 verify-code。

### 当前审查证据索引（2026-08-13）

这段只是把当前实现和验证入口列成可回查索引，不新增需求，不改变 Phase 边界，也不替代 canonical receipt。审查时以当前工作树、WorkflowHub 生成的 change-map、当前测试 receipt 和本段列出的代码/测试锚点为准。

- **AC-01 / Reader 信号可见性**：生产入口在 `src/knowledge_digest/reader_bundle.py`，负责把页面既有字段投影到根索引、产品索引、模块索引和页面头；Task2C 回归覆盖字段存在、导航可见、页面状态和 stale/deprecated 展示。审查重点是索引与页头是否来自同一投影，而不是由测试夹具另造一份信号。
- **AC-02 / trust tier 来源边界**：`reader_bundle.py` 的 `derive_reader_signals` 只接受既有机器事实源；缺失或无法确认时保留 `unverified`。Task2C 测试同时覆盖 mapping/list、缺失验证、机器事件和人工事件，人工事件不能被转成新的机器或人工 trust tier。审查重点是输入事实和读者展示之间没有隐式升级。
- **AC-03 / lifecycle 与降级边界**：`reader_bundle.py` 保留 current/stale/deprecated 的可读状态；`src/knowledge_digest/reader_quality.py` 在质量门抽样前排除明确 `degraded`/`deprecated` 页面。测试覆盖 stale 提示、deprecated 默认隐藏、普通 unverified 不误降级，以及 mapping manifest 的 degraded/deprecated 排除。
- **AC-04 / 冻结题集与覆盖**：`reader_quality.py` 从 Task0 冻结题集和 Reader Bundle inventory 派生小语料问题，覆盖产品、模块、页面类型和实际 inventory feature；覆盖不足、Task2B handoff 不匹配或正向题不足都 fail-closed。测试固定 8 个正向题、3 个负向题和 coverage fixture；真实 provider 只作为补充事实，不替代本地门。
- **AC-05 / Agent-only 逐题记录**：`reader_quality.py` 的 scorecard/exit manifest 固定 `agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`、题目、入口、跳转、命中页、输入 hash、prompt/model/seed hash、失败原因和 scorecard hash。`tests/acceptance/test_task2c_reader_quality.py` 检查字段完整性、Reader-only 输入边界和不把 Agent 结果升级成 trust tier。
- **AC-06 / 答案与来源链双门**：正向题只有在目标页命中、答案完整、边界/版本准确、来源归因和 source recheck 同时满足时才算通过；负向题只接受点名对象的直接证据，不用相似词、不同产品、历史文字或“缺少证据”推断命中。失败结果保留逐题记录，不能由 Audit/Archive 补答案。
- **AC-07 / 失败隔离与不覆盖**：质量门先写 staging，再通过 lock 和原子替换写 scorecard/exit manifest；provider、响应 JSON、覆盖、来源链和页面状态失败均保留失败证据并返回 `not_released`。测试覆盖失败页不进默认导航、失败运行不覆盖旧包、provider 失败和 malformed result 的 fail-closed 行为。
- **AC-08 / 取消、重跑、并发**：`reader_quality.py` 以 run root、staging root、lock owner 和内容 hash 隔离运行；重复输入不把运行审计误当第二业务事实源，并发 owner 失败可回查。测试覆盖 lock owner、取消/失败清理、相同输入重跑、并发写入和旧 Reader Package 保留。
- **AC-09 / exit manifest 与延期**：出口明确记录 Concept Contract、页面类型、信号字段、题集派生、scorecard、Agent 字段、seed、阈值、provider/config、call budget、wall-clock budget、credential source、commit 和 `not_released`。本任务不把 89 条全量、Task3 release、长期 provider 稳定性或 Git delivery 写成已通过；这些仍在 Deferred/Open Handoff。

当前代码/测试边界：`src/knowledge_digest/llm.py` 只负责 JSON mode 与旧调用默认值；`src/knowledge_digest/reader_bundle.py` 只负责既有 Reader 信号投影；`src/knowledge_digest/reader_quality.py` 负责 Task2C 小语料门、隔离、scorecard 和出口；`tests/acceptance/test_phase25_llm.py`、`tests/acceptance/test_task2c_reader_quality.py` 负责调用契约和行为回归；Task2A seam 用 `tests/acceptance/test_task2a_reader_bundle.py` 回查下游兼容性。fixtures 只提供冻结的 Task0、Task2B、inventory、coverage 和 Reader 页面样本，不是新的生产数据源。

当前真实运行事实：本轮使用临时环境凭据和 `rightapi/deepseek-v4-flash`，11 道冻结题得到 `status=passed`、8/8 正向、3/3 负向、0 failure、`delivery_status=not_released`；运行根目录在系统临时目录，凭据未写入项目。该运行只证明当前小语料本次结果，不能覆盖此前 provider 无返回/失败记录，因此长期稳定性仍为 `unknown`。之前 P1 标准审查因材料包超过 330 KiB 未启动 provider；这不是空 finding，也不是通过事实。

当前验证命令索引：Task2C/Task2A seam 为 `uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q`，本轮 `73 passed`；完整回归为 `uv run --frozen pytest -q`，WorkflowHub 已生成当前快照 receipt，退出码 0。`git diff --check` 通过。所有 receipt、review attempt/result 和真实运行证据都以任务库 canonical ref 为准，本文不复制原始日志或凭据。

当前 P1 变更范围索引（供大 diff 的标准分流使用）：

- `CONTEXT.md`：同步 Reader Bundle、Reader Package、Task2C Agent-only、页级状态和交付级 `not_released` 的项目术语；它不改变运行逻辑。
- `docs/adr/0007-task2c-agent-reader-gate.md`：记录 Agent 读者门为什么只作为 Task2C 小语料质量证据，为什么不等同人工审核、机器信任事件或正式 release。
- `specs/.../decision-log.md`：保存原始需求、关键事实、方案选择、风险和延期交接；不作为运行时输入。
- `specs/.../spec.md`：定义用户可见入口、页面信号、题集、逐题记录、失败隔离、并发恢复、exit manifest、非目标和 AC-01～AC-09；不定义代码实现。
- `specs/.../plan.md`：把已接受规格分解为 P1/T001～T007 的 producer-before-consumer 顺序、职责边界、回归 oracle、回滚方式和延期项；不引入新的产品行为。
- `specs/.../tasks.md`：保留唯一执行事实、RED/GREEN 配对、当前快照索引、review/test/evidence refs 和未解决边界；本段本身不产生业务状态。
- `src/knowledge_digest/llm.py`：保留既有 OpenAI-compatible 请求路径，补充 JSON mode 请求参数和 qwen 兼容的 thinking 控制；Task2C 只使用它来稳定结构化 Reader 结果解析，不改变 provider 选择或凭据来源。
- `src/knowledge_digest/reader_bundle.py`：从既有页面 frontmatter、generated、verified、source 和 status 事实派生 Reader signals，并将同一投影写入页面/索引可读区域；不读取 Audit/Archive 来补正文答案。
- `src/knowledge_digest/reader_quality.py`：冻结 Task0 题集和 coverage 规则；构造 Reader-only 输入；执行正向/负向 Agent 题；校验 JSON、答案、边界/版本、来源链；在 staging、lock 和隔离 run root 中保存 scorecard、失败原因和 exit manifest；失败保持 `not_released`。
- `tests/acceptance/test_phase25_llm.py`：锁定旧调用路径默认启用 JSON mode 后的请求合同，防止现有调用方无意破坏结构化响应。
- `tests/acceptance/test_task2c_reader_quality.py`：覆盖 Reader signals、trust/lifecycle、题集覆盖、Agent-only 字段、Reader-only 边界、答案/来源双门、失败页排除、provider 失败、staging/lock、重跑/并发、exit manifest、numeric inventory 和 mapping manifest 的 degraded/deprecated 过滤。
- `tests/fixtures/task2c_reader_quality/claim-history.jsonl`：提供稳定 claim/source locator 事实，验证读者答案能回到来源链。
- `tests/fixtures/task2c_reader_quality/coverage-fixtures/failed-degraded.json`：提供被机器门标记为 degraded 的页面，验证它不能成为正向 Reader 抽样对象。
- `tests/fixtures/task2c_reader_quality/coverage-fixtures/multi-source.json`：声明多来源 coverage 的状态和延期理由，验证未完成全量时不能静默伪造覆盖。
- `tests/fixtures/task2c_reader_quality/fixture-selection.json`：固定 fixture 选择与输入指纹，防止运行时依赖目录顺序或隐式发现。
- `tests/fixtures/task2c_reader_quality/module-capability.md`：提供模块能力正文、版本边界和来源引用，支持产品→模块→正文的读者路径。
- `tests/fixtures/task2c_reader_quality/procedure-rule.md`：提供 procedure/rule 页面和边界文字，支持页面类型覆盖与负向题隔离。
- `tests/fixtures/task2c_reader_quality/product-overview.md`：提供产品总览正文、版本和来源引用，支持产品页正向题。
- `tests/fixtures/task2c_reader_quality/source-inventory.jsonl`：固定页面类型、table/image、bilingual 等 inventory feature；数字计数由实现按“有记录”解释，不能因 truthiness 丢掉覆盖门。
- `tests/fixtures/task2c_reader_quality/task0-question-set.v1.json`：冻结 8 个正向与 3 个负向题及其目标页、路径和边界规则；它不是运行时自动扩展题库的入口。
- `tests/fixtures/task2c_reader_quality/task2b-handoff-recheck.json`：固定 Task2B handoff 的 snapshot、contract、page type 和来源链回查字段；不满足回查时质量门 fail-closed。
- `tests/fixtures/task2c_reader_quality/topic-index.json`：提供根、产品和模块索引所需的稳定导航节点，验证不打开正文即可看到 Reader signals。

范围结论：当前实现没有把 Task2C 接入正式 `pipeline.py`/`digest` CLI，没有新增 scheduler、database、vector store、AgentMemory 或 Task3 release 路径；没有改写 Task2A 的 Reader Bundle 身份、正文分页、Evidence/Provenance 结构或旧 Reader Package。当前 provider URL/model 只存在于本轮临时环境配置和任务库真实运行事实，不写入源代码、fixture、测试 receipt 或实现收据；真实运行结果不作为长期稳定性证明。

### 追加 P1 审查修复事实（2026-08-13）

- 当前 P1 标准审查已由 \`wh-review-cli.mjs run\` 进入两个异源 reviewer。有效 reviewer 发现一个真实 major：未来 \`stale_after\` 的页面在首次投影为 \`current\` 时没有冻结 \`lifecycle_as_of\`，以后按当天日期重算会改变同一 Reader Bundle 的生命周期；该 finding 为 \`F-862dcb346b29\`，不是 provider 无效输出。
- 已修复：\`derive_reader_signals\` 对所有带 \`stale_after\` 的页面保存投影日期，校验始终按已保存日期重算；同时删除审查指出的未使用 \`actors\` 局部变量。新增跨日期回放测试，模拟日期越过 \`stale_after\` 后验证同一 bundle 仍通过。
- 修复后 Task2C + Task2A seam 命令退出 0，\`74 passed\`；\`git diff --check\` 通过。审查指出的配置预检时机为 nonblocking minor，未扩大本任务范围，保留为后续改进风险。
- 本次 P1 review 结果不能沿用到修复后快照；待当前快照 receipt 生成后按“真实修复 → 一次 focused review”重跑。当前仍未进入 close，也未执行 Git 交付或清理。

### 追加第二次 P1 审查修复事实（2026-08-13）

- focused review 在修复快照上又发现一个真实 major：\`_invoke_agent\` 原先靠 \`__name__\`/\`__module__\` 识别项目 LLM，且把 prompt 作为位置参数传入，真实 \`call_llm\` seam 没有独立验证，可能让每题都因参数冲突 fail-closed；该 finding 为 \`F-dc51dbe53565\`，由两个异源 reviewer 共同指出。
- 已修复：按稳定的参数签名识别项目 LLM seam，并以 \`prompt=...\` 关键字调用；新增改名 provider 的签名契约回归，验证不依赖函数身份且仍强制 \`json_mode=true\`。其余 broad exception、inventory 文件名和 dead import 为 nonblocking minor，保留为后续风险。
- 修复后 Task2C + Task2A seam 命令退出 0，\`75 passed\`；待当前快照 receipt 生成后再做一次 focused review。当前不进入 close。

### Verify

- **Target**：全部 FR/AC 和 P1 三组跨任务 seam。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q'`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/T007-final-current-snapshot.json`
- **Oracle**：`ORACLE-FINAL`；Task2C 门、失败隔离、Task2A 回归都能从当前快照和原始输出复核，且交付级状态仍是 `not_released`。

### Deferred and Open Handoff

- `DEFER-001`：字段序列化、模板和 validator 合同；owner build-spec/build-plan；trigger 实现合同设计；handoff 只展开已接受 FR/AC；close condition 精确接口和 oracle 已进入本计划与任务。
- `DEFER-002`：小语料真实运行、机器回查和失败样本；owner build-code；trigger 实现完成；handoff 使用冻结题集和 manifest；close condition verify-code 记录真实结果或 unavailable。
- `DEFER-003`：Task3 评审主体是否继承 Agent-only；owner Task3 make-decision；trigger Task3 启动；handoff 重新决定；close condition Task3 明确确认。
- `DEFER-004`：89 条全量、17+3 完整题集和 Reader Package 发布；owner Task3；trigger Task3 启动；handoff 复用 Task2C 冻结门；close condition 全量机器门、读者门和交付门完成。
- `DEFER-005`：README/AGENTS/CONTEXT 同步、清理和归档；owner Task3-Closeout；trigger 最终输出稳定；handoff 正式 close 流程；close condition 交付记录和清理证据齐全。

### Knowledge

交给 build-code 的事实：实现只触及三文件；Task2B live baseline 已在 build-spec handoff 核对；fake provider 只证明程序边界；Task3 Agent-only 继承仍未决；任何方向变化必须返回上游。

### STOP

- 命令、schema、签名或文件边界不成立时，停止并回到当前 owning material。
- review finding 可以在本任务修复或记录风险，但不能变成新的产品需求或进入许可证。

### Done

- T001～T006 每组有同命令、同 oracle 的 RED/GREEN 事实；T007 有一次最终聚合事实。
- AC-01～AC-09 可双向追溯到 FR、任务、文件、命令和 evidence path。
- build-plan review 与最终 `spec-analyze` 的真实结果已记录；未知/不可用保持原样。

### Risks and rollback

- **Risk**：Agent 自评、小样本代表性、Task2B 基线漂移。
- **Prevention**：Reader-only allowlist、覆盖矩阵、三项 Agent-only 字段、答案+来源链双门、baseline hash preflight。
- **Rollback / recovery**：只回滚当前三文件实现，保留四材料/质量事实，旧 Reader Bundle 继续不变。

## 4. Final current-snapshot aggregate strategy

- **tier / method**：fullstack / fullstack-slice-testing；原因是路由顾问检测到 `src/`+`tests/` 跨顶层，实际不启 HTTP/DB。
- **scenarios**：AC-01～AC-09；入口信号、trust/lifecycle、题集覆盖、Reader-only、答案+来源链、失败页/交付、取消/重跑/并发、exit manifest。
- **command**：`uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q`
- **expected exit**：0
- **oracle**：`ORACLE-FINAL`；当前快照所有适用断言通过，失败保留原始输出，Task2C 不写 `released`。
- **fixtures_services**：Task2A fixtures、Task0 frozen JSON、fake provider、tmp_path；无外部服务，pytest 清理临时状态。
- **evidence_path**：`quality/evidence/T007-final-current-snapshot.json`
- **coverage limits**：不覆盖 89 条全量、真实 provider 长期质量、Task3、Git 交付和正式 release。
- **STOP**：命令损坏、AC 缺失、Task2A seam 失败、baseline 漂移、边界越界或新决策。
- **execution_contract**：当前快照运行一次；失败保留原始输出，回受影响 task，不用全量重跑掩盖局部失败。

## Dependency Graph

- **order**：T001 (RED) → T002 (GREEN) → T003 (RED) → T004 (GREEN) → T005 (RED) → T006 (GREEN) → T007 (FINAL)

```text
T001 (RED) → T002 (GREEN) → T003 (RED) → T004 (GREEN) → T005 (RED) → T006 (GREEN) → T007 (FINAL)
```

## Final Boundary Check

- [x] 每个 Phase 的 Goal、Files、Tasks、Verify、Knowledge、STOP、Done、Risks and rollback 完整。
- [x] 每个任务只有一张卡和一个完成区；文件是所属 Phase NEW/MODIFY 的子集。
- [x] 每个行为变化都有同命令、同 oracle 的 RED → GREEN；FINAL 只做一次聚合。
- [x] 依赖无环，FR/AC 双向追溯闭合，未知事实没有被写成假设或通过。
- [ ] review、test、evidence 只作为事实记录，不是开始、继续或交付许可证；待 build-plan 执行 review/analysis 后补实际 refs。
