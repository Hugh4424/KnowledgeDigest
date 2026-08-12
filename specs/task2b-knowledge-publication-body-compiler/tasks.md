# Task 2-B 知识发布正文编译任务清单

- **Input**：当前 root `decision-log.md`、`specs/task2b-knowledge-publication-body-compiler/spec.md`、`specs/task2b-knowledge-publication-body-compiler/plan.md`；同目录 `decision-log.md` 是只读旧 receipt，不是执行依据。
- **Template version**：`plan-task.v3`

## 1. 执行摘要

按 T001→T014 串行执行。T001/T003/T005/T007/T009/T011 先写目标失败测试，随后对应 GREEN 实现；T013 只记录真实语义运行，T014 做最终回归。缺少上游事实时保留 `pending/incomplete/not_released`，不改低门槛。

## 2. Global Constraints

- 只改 Phase 1 的 NEW/MODIFY 文件；不改当前 `decision-log.md`、`spec.md`、PRD、Task 2-A Reader Bundle/Frontmatter、CLI、配置或写回单写者边界。
- provider 只能填固定 page type 的受控 section；所有正文事实必须有唯一 Claim、来源 URI、内容指纹和 fragment locator。
- 影响不确定时整页重编；失败不覆盖旧正式页；`degraded` 不进 Reader 导航；整包不声称 `released`。
- RED/GREEN 命令必须真实可执行；RED setup 失败或需要新产品决策时 STOP，不弱化断言。
- `SR-20260811-task2b-procedure-source-gap` 是同一 Task 的 scope revision；只更新受影响 section 和其消费方，不重开 T001–T014，不把实现推导成新需求。
- `procedure_or_rule.exceptions` 仍是固定 section；确定性来源审计才能使用 `source_not_documented`。它不是异常 Claim、不是“暂无异常”，异常题为 `not_answerable`；来源含糊、审计不全或 provider 映射/归因失败仍 `degraded/not_released`。
- 本 SR 不改变三类 page type、页级 `published/degraded`、交付 `not_released`、`>=6`、inventory coverage、provenance/faithfulness/version/duplicate gates；唯一 contract revision 额度已为 `1/1`。

## Phase 1：受控正文编译与机器出口

### Goal

完成固定 page type、受控 section、正文/证据分离、影响闭包、分页导航、机器语义出口和 Task 2-A 兼容回归。

### Phase Card — Phase 1

- **goal**：在现有 S1–S6 seam 上完成三类固定 page type、受控 section、结构片段回查和后续正文编译门；先从 T001 的 typed-section RED 开始。
- **allowed files**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/llm.py`、`src/knowledge_digest/publication.py`、`src/knowledge_digest/faithfulness.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/navigation.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`；运行时证据只写 `apply/evidence/`。
- **covered ACs**：AC-01–AC-13；既有 T001–T014 事实不重置，SR 新增 T015/T016 覆盖 AC-13 及受影响的 AC-02/AC-07/AC-09/AC-11。
- **non-goals**：不改 CLI、配置、Task 2-A Reader Bundle/Frontmatter、TopicIndex、写回单写者、PRD；不做人工读者门、全量 89 篇正式发布、数据库、第二套导航或 UI。四份当前材料只按本 SR 做一次受影响范围更新。
- **compatibility boundary**：继续复用 `draft`、`llm`、`faithfulness`、`page_layout`、`navigation`、`pipeline` 现有入口；不破坏旧字段和 Task 2-A 稳定主题/导航/回查合同。
- **test tier**：预判 `feature`；实际 changed files 经 test-routing-advisor 判为 `fullstack`（跨 `src/` 与 `tests/` 边界），因此本 Phase 选 `fullstack-slice-testing`，保留本地 CLI/管线 slice 和无服务/N/A 限制；无浏览器、常驻服务或外部网络。
- **STOP**：需要新增 page type/必需 section/页级或交付状态、改 CLI 或 Reader Bundle、RED 是 setup error、影响边界超出允许文件，或 provider/旧页保护无法 fail-closed。已批准的 `exceptions=source_not_documented` section 规则不再回到 make-decision；超出该规则才停止。
- **expected handoff**：每张卡更新自身状态和执行事实；本 Phase 结束留下 focused tests、最终兼容回归、逐 AC 结果、一次当前代码 review 事实和未解决限制。

### Files

- **NEW**：`tests/acceptance/test_task2b_body_compiler.py`
- **NEW**：`tests/fixtures/task2b_publication_body/cases.json`
- **MODIFY**：`src/knowledge_digest/draft.py`
- **MODIFY**：`src/knowledge_digest/llm.py`
- **MODIFY**：`src/knowledge_digest/publication.py`
- **MODIFY**：`src/knowledge_digest/faithfulness.py`
- **MODIFY**：`src/knowledge_digest/page_layout.py`
- **MODIFY**：`src/knowledge_digest/navigation.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`

### Tasks

以下卡片的 `状态` 由执行者更新；本计划生成时全部为 `pending`。

#### T001 — RED：固定 page type 与受控 section 的失败测试

- **ID**：T001
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：先证明当前实现不能稳定输出三类固定 page type 和必需 section，也不能拒绝 provider 扩张合同。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：`R-004`、`D-001`、`PFACT-001`、三类 page type section matrix
- **依赖**：N/A — first task
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-FLOW-001、FR-FLOW-002、FR-DRAFT-001
- **AC**：AC-01、AC-02
- **动作**：只在 `test_task2b_body_compiler.py` 和 `cases.json` 增加三类正例、TopicIndex 到唯一 page type 的映射正例、标题与 TopicIndex 不一致时以 TopicIndex 为准的正例、未知 section、未知 page type、未知来源字段、缺必需 section、provider 截断 JSON/不可解析输出、无依据事实和空结果的行为断言；TopicIndex 缺映射或映射冲突必须进 Audit/Archive，不进 Reader；这些 provider 越界或失败输入必须被拒绝并转为 `degraded`，不进 Reader；fixture 还必须覆盖 H1/title、父子关系、FAQ、表格、图片、双语、版本和噪声结构，并断言每个可用片段带 `source_locator`/`content_type`，无法回查的片段被排除或转为 `degraded`；不改生产代码。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: typed section fixtures only。
- **输出**：目标断言失败的测试和固定 fixture。
- **Knowledge**：当前生产入口是 `draft.draft`、`llm.build_prompt/parse_response`；测试通过受信 generator seam 注入。
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k typed_sections'`
- **expected_exit**：1
- **oracle**：ORACLE-T2B-TYPED-SECTIONS — 目标断言报告固定三类 page type、必需 section、结构片段可回查字段和 provider 越界失败。
- **evidence_path**：`apply/evidence/T001.typed-sections.red.txt`
- **STOP**：如果 RED 因依赖安装、import、fixture 路径或命令错误失败，停止并修复测试设置；不得把 setup error 当目标失败。
- **recovery**：删除本卡新增测试/fixture bytes，保留当前生产代码。
- **task risk**：测试只检查 section 名称而没有证明 provider 越界被拒绝。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 T001 typed-section RED acceptance test 与 `cases.json` fixture；未修改生产代码。
- **Trace**：AC-01、AC-02
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T001 typed-section RED 已真实执行，3 个目标断言失败且不是 setup error。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k typed_sections`；exit `1`，3 个目标断言失败，失败点是当前缺少 `normalize_structure` seam，不是 setup error。
- **evidence_refs**：`apply/evidence/T001.typed-sections.red.txt`
- **covered_ac**：AC-01、AC-02（RED 目标断言已建立；GREEN 待 T002）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T002 — GREEN：实现固定 page type 与受控 section contract

- **ID**：T002
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：让 T001 的固定 page type/section 断言通过，并保留未知结构和缺证据负例。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T001；`R-004`、`D-001`、`PFACT-001`
- **依赖**：T001
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-FLOW-001、FR-FLOW-002、FR-DRAFT-001
- **AC**：AC-01、AC-02
- **动作**：在 `draft.py` 形成确定性的 Structure Normalizer adapter 和受信 PageDraft/section contract，保留 H1/title、父子、FAQ、表格、图片、双语、版本、噪声的结构关系及 `source_locator`/`content_type`；显式只消费既有 TopicIndex 的唯一 page type 映射，标题只能作为显示线索，不能临时猜 page type；在 `llm.py` 限制 provider 输入输出，在 `publication.py` 注册三类 section matrix；不改 `topic_axis.py`、CLI 或 Reader Bundle。
- **精确文件**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/llm.py`、`src/knowledge_digest/publication.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `src/knowledge_digest/draft.py`, `src/knowledge_digest/llm.py`, `src/knowledge_digest/publication.py`, `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: PageDraft context, prompt/parser contract, publication section matrix。
- **输出**：带结构片段回查信息的 typed PageDraft 和 provider section contract；未知或不可回查结构 fail-closed。
- **Knowledge**：继续使用 `validate_publication_provider_identity`；provider/model/base URL 是 build-code 启动时从当前代码/配置和环境回读的外部事实，本卡不提前选择。
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k typed_sections'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-TYPED-SECTIONS — 同一断言全部通过，TopicIndex 映射优先于标题猜测且缺映射/冲突进入 Audit，结构关系和 source locator/content type 可回查，未知 page type/section/来源字段、必需证据缺失、截断/不可解析 provider 输出、无依据事实和空结果负例仍失败并保持 fail-closed。
- **evidence_path**：`apply/evidence/T002.typed-sections.green.txt`
- **STOP**：先回读并确认 `draft.py`、`llm.py`、`publication.py` 的计划 seam 和调用关系；若符号/签名不一致，或实现需要新增 page type、改变必需 section、预先选择未冻结 provider 或放宽 provider 来源边界，停止并回到当前材料，不自行补接口。
- **recovery**：只回滚本卡在 `draft.py`、`llm.py`、`publication.py` 和对应测试/fixture 的改动。
- **task risk**：把结构整理误写成 provider 自由补事实。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `draft.py` 增加 Structure Normalizer、TopicIndex 驱动的 PageDraft contract；在 `publication.py` 固定三类 section matrix；在 `llm.py` 增加 provider typed-section fail-closed validator；T001 测试/fixture 保持可回归。
- **Trace**：AC-01、AC-02
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T002 typed-section GREEN 已真实执行，3 个 focused tests 通过。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k typed_sections`；exit `0`，3 passed，10 deselected。
- **evidence_refs**：`apply/evidence/T002.typed-sections.green.txt`
- **covered_ac**：AC-01、AC-02（结构关系、TopicIndex 映射、固定 section 和 provider contract）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T003 — RED：正文与 Evidence 分离及关键事实门的失败测试

- **ID**：T003
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：先证明正文不能把 Evidence dump 当答案，且数字、标识符、版本、命令、配置、表格、图片和重复负例会被机器门识别。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T002；`R-004`、`D-001`、`PFACT-001`
- **依赖**：T002
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-DRAFT-002、FR-PUBLISH-001、FR-PUBLISH-002
- **AC**：AC-03、AC-04、AC-12
- **动作**：增加正文/证据分离、Claim footnote 回查、关键 token 篡改、无归因、provider 截断 JSON/不可解析输出/空结果、连续逐字块、同页/跨页近重复和 golden-negative 的失败测试；这些 provider 失败必须断言页级 `degraded`、完整 Claim/Evidence 留在 Audit/Archive 且不进 Reader；fixture 还要覆盖数字、标识符、版本、命令、端口、配置、表格、图片的版本来源优先级（托管 metadata → 来源 frontmatter/显式 metadata → 版本标题/字段）、只接受 semver/日期版本/release label、多版本冲突或无法解析转 `degraded`、`stale_after` 只能来自来源明确有效期/复核日期；连续逐字块和同页/跨页近重复每项都断言正确的 `denominator`、`detector_version`、`seed` 和失败样本；不改生产代码。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: provenance_gate fixtures only。
- **输出**：目标事实门失败的 focused test。
- **Knowledge**：关键 token 和 Claim 归因必须走 `faithfulness.verify_claims`/`normalize_for_gate`，fixture 明确公共模板、代码、表格和双语例外。
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k provenance_gate'`
- **expected_exit**：1
- **oracle**：ORACLE-T2B-PROVENANCE-GATE — 目标断言报告无来源事实、关键 token 变化、重复或 Evidence 冒充正文被阻断；截断/不可解析 provider 输出和空结果进入 `degraded`，完整 Claim/Evidence 仍留在 Audit/Archive，并能回查每项重复检测的 `denominator`、`detector_version`、`seed`。
- **evidence_path**：`apply/evidence/T003.provenance-gate.red.txt`
- **STOP**：如果测试只能检查字符串存在、不能定位具体 Claim/失败样本，停止并补 oracle；不得以 provider 返回 200 代替门。
- **recovery**：删除本卡新增测试/fixture bytes。
- **task risk**：把带 attribution 的短引、公共模板、代码、表格或双语合法例外误判为失败。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增正文/Evidence 分离、Claim footnote、关键 token 篡改、无归因、近重复和 provider 空/截断输出的 RED fixture/test；未修改生产代码。
- **Trace**：AC-03、AC-04、AC-12
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T003 provenance-gate RED 已真实执行，4 个目标断言失败且不是 setup error。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k provenance_gate`；exit `1`，4 个目标断言失败，15 个测试被筛除。
- **evidence_refs**：`apply/evidence/T003.provenance-gate.red.txt`
- **covered_ac**：AC-03、AC-04、AC-12（RED 目标断言已建立；GREEN 待 T004）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T004 — GREEN：实现正文/证据分离与 Publication Gate

- **ID**：T004
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：让 T003 的正例通过、golden-negative 保持稳定失败，并把完整 Claim/Evidence 留在 Audit/Archive。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T003；`R-004`、`D-001`、`D-004`
- **依赖**：T003
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-DRAFT-002、FR-PUBLISH-001、FR-PUBLISH-002
- **AC**：AC-03、AC-04、AC-12
- **动作**：在 `faithfulness.py` 提供正文事实 token/Claim mapping 和重复 gate，在 `publication.py` 汇总版本/归因/失败原因和当前 `contract_revision`；在 `llm.py`/`draft.py` 让 provider section 输出经过 gate；显式执行版本来源优先级、可接受版本格式、多版本冲突/无法解析降级和 `stale_after` 来源限制；行为修复不静默消耗修订预算，只有 section/page type/field 合同变化才增加 revision 且不得超过 `1`；重复 gate 输出并保留每项检测的 `denominator`、`detector_version`、`seed` 和失败样本；保留 Evidence/archive 的完整证据，不把失败页送进 Reader。
- **精确文件**：`src/knowledge_digest/faithfulness.py`、`src/knowledge_digest/publication.py`、`src/knowledge_digest/llm.py`、`src/knowledge_digest/draft.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `src/knowledge_digest/faithfulness.py`, `src/knowledge_digest/publication.py`, `src/knowledge_digest/llm.py`, `src/knowledge_digest/draft.py`, `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: gate result, section candidate validation, provenance mapping。
- **输出**：可读正文与 Evidence/archive 分层、可解释的 page gate result、失败样本和输入指纹，并记录重复检测的 `denominator`/`detector_version`/`seed` 以及 `contract_revision`/revision ledger。
- **Knowledge**：连续逐字块、5-gram Jaccard、版本选择规则和例外均来自当前 spec，不新增全局复制率门。
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k provenance_gate'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-PROVENANCE-GATE — 同一正例通过、golden-negative 稳定失败；数字、标识符、版本、命令、端口、配置、表格、图片的事实门可回查；截断/不可解析 provider 输出和空结果进入 `degraded`，失败页状态、完整证据和恢复依据可回查。
- **evidence_path**：`apply/evidence/T004.provenance-gate.green.txt`
- **STOP**：如果实现需要引入人工评分、全局复制率或修改 Reader Bundle schema，停止并回到当前材料。
- **recovery**：只回滚本卡在 `faithfulness.py`、`publication.py`、`llm.py`、`draft.py` 和对应测试/fixture 的改动。
- **task risk**：正文 gate 通过但完整 Evidence/archive 链断裂。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `publication.py` 增加正文/Evidence、Claim 回查、token/版本指纹和 5-gram/重复失败记录的 Publication Gate；失败统一为 `degraded`/Audit，成功才允许 `published`。
- **Trace**：AC-03、AC-04、AC-12
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T004 provenance-gate GREEN 已真实执行，4 个 focused tests 通过。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k provenance_gate`；exit `0`，4 passed，15 deselected。
- **evidence_refs**：`apply/evidence/T004.provenance-gate.green.txt`
- **covered_ac**：AC-03、AC-04、AC-12（当前 gate 的正文/Evidence 分离、归因/token/重复 oracle；版本完整矩阵待后续卡）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T005 — RED：影响闭包与旧 section 失效的失败测试

- **ID**：T005
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：先证明来源/Claim/版本/结构变化不能安全复用受影响 section，且影响不确定时不能只保留旧 section。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T004；`R-004`、`D-002`、`D-003`、`PFACT-006`
- **依赖**：T004
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-DRAFT-003、FR-PUBLISH-003、FR-PUBLISH-004、FR-COMPAT-001
- **AC**：AC-05、AC-06、AC-07
- **动作**：按 plan 冻结的 `section-dependency-record.v1` 构造明确影响、依赖未变安全复用、缺 record/字段缺失、版本冲突不确定、旧 signal 失效、整页失败保护和禁止新旧拼接的测试；不改生产代码。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: impact_closure fixtures only。
- **输出**：目标影响闭包断言失败的 focused test。
- **Knowledge**：当前 `old_target_body` 是否进入 draft context 需 build-code 首卡回读；本卡要证明它不能代替受影响 section 的重编。
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k impact_closure'`
- **expected_exit**：1
- **oracle**：ORACLE-T2B-IMPACT-CLOSURE — 目标断言报告受影响 section 仍复用旧内容或不确定影响未扩大整页。
- **evidence_path**：`apply/evidence/T005.impact-closure.red.txt`
- **STOP**：如果测试无法比较 section dependency/attribution/version 或旧页 bytes，停止并补 fixture/oracle。
- **recovery**：删除本卡新增测试/fixture bytes。
- **task risk**：只测“调用了 provider”，没有证明旧说法真的失效。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增影响闭包、依赖未变复用、不确定整页和旧页失败保护的 RED acceptance test/fixture；未修改生产代码。
- **Trace**：AC-05、AC-06、AC-07
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T005 impact-closure RED 已真实执行，3 个目标断言失败且不是 setup error。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k impact_closure`；exit `1`，3 个目标断言失败，19 个测试被筛除。
- **evidence_refs**：`apply/evidence/T005.impact-closure.red.txt`
- **covered_ac**：AC-05、AC-06、AC-07（RED 目标断言已建立；GREEN 待 T006）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T006 — GREEN：实现影响闭包、安全复用和整页失败保护

- **ID**：T006
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：让 T005 的明确影响、安全复用、不确定整页和旧正式页保护断言通过。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T005；`D-002`、`D-003`、`PFACT-006`
- **依赖**：T005
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-DRAFT-003、FR-PUBLISH-003、FR-PUBLISH-004、FR-COMPAT-001
- **AC**：AC-05、AC-06、AC-07
- **动作**：在 `draft.py`/`page_layout.py` 按 plan 冻结的 `section-dependency-record.v1` 记录 `source_deps`、`claim_deps`、`version_deps`、`structure_deps`、`attribution_deps`、canonical `dependency_hash` 和序列化版本；只有三组指纹及记录版本一致才复用；在 `pipeline.py` 把 uncertain 扩大为整页，整页失败保留旧正式页并把当前结果放 Audit/Archive，禁止新旧正文拼接。
- **精确文件**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `src/knowledge_digest/draft.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/pipeline.py`, `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: impact record, layout history selection, status/writeback filtering。
- **输出**：可审计 impact record；安全复用、affected recompile、uncertain whole-page 和旧页保护。
- **Knowledge**：既有 writeback 单写者和 archive 机制保持不变，只改变进入写回的 layout/status 数据。
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k impact_closure'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-IMPACT-CLOSURE — unaffected page bytes/hash 不变，affected section 不残留旧 signal，uncertain failure 不覆盖旧 Reader。
- **evidence_path**：`apply/evidence/T006.impact-closure.green.txt`
- **STOP**：如果需要删除旧页、创建第二写回链或把 uncertain 降级为局部复用，停止并回到当前材料。
- **recovery**：只回滚本卡在 `draft.py`、`page_layout.py`、`pipeline.py` 和对应测试/fixture 的改动。
- **task risk**：影响集合漏掉跨 section/跨 page 的版本或父子关系依赖。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `page_layout.py` 增加 canonical `section-dependency-record.v1`、安全复用/影响评估、不确定整页判定和旧正式页失败保护；当前 focused seam 尚未改写既有 writeback 单写者。
- **Trace**：AC-05、AC-06、AC-07
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T006 impact-closure GREEN 已真实执行，3 个 focused tests 通过。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k impact_closure`；exit `0`，3 passed，24 deselected。
- **evidence_refs**：`apply/evidence/T006.impact-closure.green.txt`
- **covered_ac**：AC-05、AC-06、AC-07（明确变更只重编受影响 section；不确定影响扩大为整页；候选失败不覆盖旧页）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T007 — RED：语义拆分、分页和唯一 Claim part 的失败测试

- **ID**：T007
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：先证明长正文不能任意按字符切碎，也不能保证总览、related key、prev/next、120/300 行和唯一 Claim part。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T006；`R-004`、`D-001`、`PFACT-001`、`PFACT-003`
- **依赖**：T006
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-PUBLISH-005、FR-COMPAT-001
- **AC**：AC-04、AC-08
- **动作**：增加长主题、多 part、overview/related/prev-next、正文 120 行、整页 300 行、Claim exactly-once 和每个 part 都有入口的正例；增加 part 无入口和只把 part-1 当入口的负例；不改生产代码。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: semantic_split fixtures only。
- **输出**：目标分页/导航断言失败的 focused test。
- **Knowledge**：布局入口是 `page_layout._partition/_render_page/build_topic_layouts`，导航入口是 `navigation.build_publication_navigation`。
- **verification_role**：RED
- **paired_task**：T008
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_split'`
- **expected_exit**：1
- **oracle**：ORACLE-T2B-SEMANTIC-SPLIT — 目标断言报告任意切碎、超限、缺 overview/prev-next、任一 part 无入口或 Claim 重复/丢失。
- **evidence_path**：`apply/evidence/T007.semantic-split.red.txt`
- **STOP**：如果只能通过提高行数上限、丢 Claim 或把 part-1 当第二入口来过测试，停止。
- **recovery**：删除本卡新增测试/fixture bytes。
- **task risk**：只验证行数，不验证语义边界和导航入口。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增长主题、overview/part、prev/next、入口、行数和 Claim exactly-once 的 RED acceptance test/fixture；未修改生产代码。
- **Trace**：AC-04、AC-08
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T007 semantic-split RED 已真实执行，目标分页断言失败且另一个边界断言通过。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_split`；exit `1`，1 个目标断言失败、1 个断言通过，22 个测试被筛除。
- **evidence_refs**：`apply/evidence/T007.semantic-split.red.txt`
- **covered_ac**：AC-04、AC-08（RED 目标断言已建立；GREEN 待 T008）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T008 — GREEN：实现语义拆分、分页和统一导航投影

- **ID**：T008
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：让 T007 的语义拆分、容量、Claim 唯一归属和统一导航断言通过。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T007；`D-001`、`PFACT-001`、`PFACT-003`
- **依赖**：T007
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-PUBLISH-005、FR-COMPAT-001
- **AC**：AC-04、AC-08
- **动作**：在 `page_layout.py` 先按产品/模块/能力/步骤/问题边界组织 section，再按 120/300 行分页；在 `navigation.py` 复用现有入口生成 overview/related/prev-next，并确保每个 Claim 只落一个 part。
- **精确文件**：`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/navigation.py`、`src/knowledge_digest/faithfulness.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/navigation.py`, `src/knowledge_digest/faithfulness.py`, `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: semantic partition, layout rendering, navigation rows, claim coverage。
- **输出**：不超限的 overview/part pages、稳定 related key 和 `prev/next`，同一主题无重复/丢失 Claim。
- **Knowledge**：不另建 navigation writer；现有 Home→分类→主题链保持唯一读者入口。
- **verification_role**：GREEN
- **paired_task**：T007
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_split'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-SEMANTIC-SPLIT — 正例满足语义边界/120/300 行/导航/Claim exactly-once，超限和重复负例仍失败。
- **evidence_path**：`apply/evidence/T008.semantic-split.green.txt`
- **STOP**：如果改动需要第二套 Home/index/navigation 或删除历史 part，停止并回到当前材料。
- **recovery**：只回滚本卡在 `page_layout.py`、`navigation.py`、`faithfulness.py` 和对应测试/fixture 的改动。
- **task risk**：语义拆分后 provenance locator 或现有 source-index 链接失配。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `page_layout.py` 增加按 section 的语义 parts 构建和验证，在 `navigation.py` 增加 overview/entry/prev-next/related 的统一 part 投影；未建立第二套 Home/index/navigation 写入链。
- **Trace**：AC-04、AC-08
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T008 semantic-split GREEN 已真实执行，2 个 focused tests 通过。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_split`；exit `0`，2 passed，25 deselected。
- **evidence_refs**：`apply/evidence/T008.semantic-split.green.txt`
- **covered_ac**：AC-04、AC-08（120/300 行边界、稳定 part 路径、每个 part 可达、Claim 只归属一个 part）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T009 — RED：样本覆盖和语义机器出口的失败测试

- **ID**：T009
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：先证明缺样本 manifest、provider/detector/budget/threshold、真实语义运行或三类/六概念底线时不能声称机器出口通过。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T008；`R-004`、`D-004`、`PFACT-004`、`PFACT-005`
- **依赖**：T008
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-SEM-001、FR-SEM-002、FR-SEM-003、FR-PUBLISH-003
- **AC**：AC-09、AC-10、AC-11、AC-12、AC-13
- **动作**：增加固定 manifest 字段、实际 inventory 类别覆盖、fallback/Jaccard-only/provider 失败、`>=6` concept/三类 page type 和 `not_released` 聚合断言；负例还必须缺少或篡改 `answerability_source`、确定性 answerability subset id/hash、逐题 answerability/`first_hit`、`evidence_backtrace.claim_id`/`fragment_locator`、逐 section `section_completeness` 或 `failure_reason`，并覆盖 revision ledger 从 `0` 到当前 `1/1` 的修订预算规则；在 `tests/fixtures/task2b_publication_body/cases.json` 固定的 `semantic_evidence_file` 键下增加正负 fixture，明确缺必填字段或 AC-01/03/05/07/09/10/11/12/13 任一绑定时机器断言失败；不改生产代码。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: semantic_exit fixtures only。
- **输出**：目标语义出口断言失败的 focused test。
- **Knowledge**：本卡不挑选真实样本；真实清单由 T013 回读上游事实，fixture 只覆盖机器规则和不存在类别的明确排除。
- **verification_role**：RED
- **paired_task**：T010
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_exit'`
- **expected_exit**：1
- **oracle**：ORACLE-T2B-SEMANTIC-EXIT-GATE — 目标断言报告缺 manifest/运行字段、缺 answerability/first-hit/证据回查/section completeness/修订记录、缺 AC 绑定、覆盖不足或 fallback 被误报通过；离线 `semantic_evidence_file` 必填字段断言必须失败。
- **evidence_path**：`apply/evidence/T009.semantic-exit.red.txt`
- **STOP**：如果测试要求临时改题、降低 `>=6` 或把离线/Jaccard-only 当语义通过，停止。
- **recovery**：删除本卡新增测试/fixture bytes。
- **task risk**：fixture 通过但没有绑定真实 sample manifest 的 hash/范围。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 semantic evidence 正负 fixture 和机器出口 RED acceptance test；未修改生产代码。
- **Trace**：AC-09、AC-10、AC-11、AC-12
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T009 semantic-exit RED 已真实执行，3 个目标断言失败且不是 setup error。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_exit`；exit `1`，3 个目标断言失败，24 个测试被筛除。
- **evidence_refs**：`apply/evidence/T009.semantic-exit.red.txt`
- **covered_ac**：AC-09、AC-10、AC-11、AC-12（RED 目标断言已建立；GREEN 待 T010）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T010 — GREEN：实现样本/语义运行 manifest 和 not_released 出口

- **ID**：T010
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：让 T009 的机器出口正例通过，并在证据不足时稳定返回 `not_released` 而不是假通过。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T009；`D-004`、`PFACT-004`、`PFACT-005`
- **依赖**：T009
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-SEM-001、FR-SEM-002、FR-SEM-003、FR-PUBLISH-003
- **AC**：AC-09、AC-10、AC-11、AC-12、AC-13
- **动作**：在 `publication.py`/`pipeline.py` 汇总冻结 manifest、真实运行身份、样本覆盖、detector/budget/threshold、归因和失败项；读取运行前传入的 `KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE`，由同一次 digest 运行写入新的 semantic evidence 文件，并在文件中绑定 `run_id`、sample/KB/input 指纹和 `output_path`；强制绑定 `answerability_source`、确定性 answerability subset id/hash、逐题 answerability/`first_hit`、`evidence_backtrace` 中的 `claim_id`/`fragment_locator`、逐 section `section_completeness`、`ac_bindings`（AC-01、AC-03、AC-05、AC-07、AC-09、AC-10、AC-11、AC-12、AC-13，其中 AC-12/AC-13 由 revision ledger 和来源缺口 section 状态绑定）和 failure reason；实现 `>=6`/三类/实际 inventory 覆盖门，把 provider 失败、fallback、Jaccard-only、缺证据留为 `not_released`，并执行 revision ledger 当前为 `1/1`，后续只能修行为 bug；提供 `semantic_evidence_file` validator，供 T013 的 gate command 对本次运行实际产出的证据文件做路径、运行身份、字段和全部 AC 绑定机器断言。
- **精确文件**：`src/knowledge_digest/publication.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`
- **boundary**：files: `src/knowledge_digest/publication.py`, `src/knowledge_digest/pipeline.py`, `tests/acceptance/test_task2b_body_compiler.py`, `tests/fixtures/task2b_publication_body/cases.json`; symbols/regions: semantic run summary, delivery status, coverage aggregation。
- **输出**：可审计 semantic run record（含 answerability、first hit、evidence backtrace、section completeness、failure reason、AC 绑定和 revision ledger）和页级/交付级分离状态；提供可被 `semantic_evidence_file` 直接检查的证据格式。
- **Knowledge**：真实 provider 具体运行值仍由 T013 绑定；本卡不把当前未知值写成已完成事实。
- **verification_role**：GREEN
- **paired_task**：T009
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_exit'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-SEMANTIC-EXIT-GATE — 正例满足离线机器底线且所有语义字段和 AC 绑定可回查，缺任一 fixture 证据或违反 revision budget 的负例为 `not_released` 并保留原因；不代表 T013 的真实 provider 运行完成。
- **evidence_path**：`apply/evidence/T010.semantic-exit.green.txt`
- **STOP**：如果实现把 `not_released` 降成 `published`、把 provider 失败吞掉或发明完整题集门，停止并回到当前材料。
- **recovery**：只回滚本卡在 `publication.py`、`pipeline.py` 和对应测试/fixture 的改动。
- **task risk**：机器聚合统计正确但运行身份没有绑定具体 sample/provider evidence。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `publication.py` 增加 semantic evidence validator 和 run-bound file validator；在 `pipeline.py` 增加按环境变量写入真实运行身份、样本/输入/KB 指纹、覆盖、失败项、AC bindings、revision ledger 和 `not_released` 的 evidence writer；同任务修复补充非 fixture provider、SHA-256 运行指纹和 manifest/answerability hash 校验，避免把重标记 fixture 当真实语义出口。正式调用接线与真实运行仍由 T012/T013 继续验证。
- **Trace**：AC-09、AC-10、AC-11、AC-12
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T010 semantic-exit GREEN 已真实执行，3 个 focused tests 通过；真实语义运行仍由 T013 诚实记录为 incomplete。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_exit`；exit `0`，3 passed，24 deselected。
- **evidence_refs**：`apply/evidence/T010.semantic-exit.green.txt`
- **covered_ac**：AC-09、AC-10、AC-11、AC-12、AC-13（validator 与 file identity seam；真实 provider/sample 事实待 T013）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T011 — RED：正式 pipeline、导航和 Task 2-A 兼容的失败测试

- **ID**：T011
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：先证明正文 compiler 的结果没有真正接入现有 S1–S6 状态/导航/写回链，或会破坏 Task 2-A Reader Bundle 兼容。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T010；`R-005`、`D-001`、`D-003`、`PFACT-003`
- **依赖**：T010
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-FLOW-001、FR-PUBLISH-001、FR-PUBLISH-003、FR-COMPAT-001
- **AC**：AC-01、AC-03、AC-07、AC-08
- **动作**：增加正式 `audit_run`/layout/navigation 的端到端 seam 断言：用截断/不可解析 provider 输出或空结果制造一次失败，确认页面为 `degraded`、不进导航、完整 Claim/Evidence 留在 Audit/Archive 且旧正式页失败保护成立；另用未映射 TopicIndex、冲突 TopicIndex identity、缺失冻结输入和 fingerprint mismatch 制造入口失败，确认它们同样只进 Audit/Archive、不进 Reader 导航；正常、失败和重复运行后，Reader 入口、稳定主题身份、source/Claim 回查和旧正式页 bytes 仍可对账；Task 2-A Reader Bundle/Frontmatter 既有字段和入口仍可消费；不改生产代码。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`; symbols/regions: pipeline_compat integration fixtures only。
- **输出**：目标接线/兼容断言失败的 focused test。
- **Knowledge**：正式入口是 `pipeline.audit_run` 和既有 `build_publication_navigation`；Task 2-A 投影不是第二个生产 pipeline。
- **verification_role**：RED
- **paired_task**：T012
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k pipeline_compat'`
- **expected_exit**：1
- **oracle**：ORACLE-T2B-PIPELINE-COMPAT — 截断/不可解析 provider 输出或空结果导致的 `degraded` 不出现在导航；未映射/冲突 identity、缺失冻结输入或 fingerprint mismatch 也只进 Audit/Archive；旧页不被覆盖，完整失败证据可回查，Task 2-A contract 不断裂。
- **evidence_path**：`apply/evidence/T011.pipeline-compat.red.txt`
- **STOP**：先回读并确认 `pipeline.py`、`navigation.py`、`page_layout.py` 的计划 seam；若符号/调用关系不一致，或兼容测试要求修改 Task 2-A schema、重建第二套导航、改变旧页删除规则或预先选择未冻结 provider，停止。
- **recovery**：删除本卡新增测试 bytes。
- **task risk**：只测函数返回，不测正式写回前后的 Reader/Audit 分流。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 pipeline compatibility RED acceptance test，覆盖 typed draft handoff、provider failure、TopicIndex unmapped/conflict、缺失/不一致冻结输入、旧 Reader 保护、导航空投影和稳定身份；未修改生产代码。
- **Trace**：AC-01、AC-03、AC-07、AC-08
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T011 pipeline-compat RED 已真实执行，5 个目标断言失败且不是 setup error。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k pipeline_compat`；exit `1`，5 个目标断言失败，27 个测试被筛除。
- **evidence_refs**：`apply/evidence/T011.pipeline-compat.red.txt`
- **covered_ac**：AC-01、AC-03、AC-07、AC-08（RED 目标断言已建立；GREEN 待 T012）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T012 — GREEN：接通正式 pipeline 并保持 Task 2-A 兼容

- **ID**：T012
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：让 T011 的正式链路和兼容断言通过，同时保留原有原子写回、导航和 Reader Bundle 合同。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T011；`R-005`、`D-001`、`D-003`、`PFACT-003`
- **依赖**：T011
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-FLOW-001、FR-PUBLISH-001、FR-PUBLISH-003、FR-COMPAT-001
- **AC**：AC-01、AC-03、AC-07、AC-08
- **动作**：在 `pipeline.py` 接通 typed PageDraft、Publication Gate、impact/layout status 和 semantic evidence；在 `navigation.py`/`page_layout.py` 保持同一入口和旧页保护，重复运行也不得新增重复主题或改变稳定身份；确保 Task 2-A Reader Bundle/Frontmatter 回归不变。
- **精确文件**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/navigation.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/draft.py`、`tests/acceptance/test_task2b_body_compiler.py`
- **boundary**：files: `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/navigation.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/draft.py`, `tests/acceptance/test_task2b_body_compiler.py`; symbols/regions: audit_run seam, reader/audit filter, navigation records, old page protection。
- **输出**：正式 S1–S6 运行结果与 Task 2-A 兼容的 Reader/Audit 分流。
- **Knowledge**：不改 `writeback.py` 单写者；只改变其消费的已验证 layout/navigation records。
- **verification_role**：GREEN
- **paired_task**：T011
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k pipeline_compat'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-PIPELINE-COMPAT — 通过页进入唯一导航，截断/不可解析 provider 输出或空结果产生的 degraded、未映射/冲突 identity、缺失冻结输入或 fingerprint mismatch 留在 Audit，旧正式页不被失败覆盖，Task 2-A contract 继续通过。
- **evidence_path**：`apply/evidence/T012.pipeline-compat.green.txt`
- **STOP**：如果接线需要改变 CLI/config、删除旧 history 或把 Task 2-B 机器出口写成正式 released，停止。
- **recovery**：只回滚本卡在 `pipeline.py`、`navigation.py`、`page_layout.py`、`draft.py` 和对应测试的改动。
- **task risk**：离线回归通过但真实 provider failure 的 page status 没有保留。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `draft.py` 接入可选 TopicIndex→typed PageDraft→provider section contract，在 `llm.py` 增加 typed prompt/解析边界，在 `pipeline.py` 接入 compiler、Publication Gate、Audit/Reader 分流、语义 evidence writer；保留既有 writeback 单写者和 Task 2-A 页面/导航字段。
- **Trace**：AC-01、AC-03、AC-07、AC-08
- **证据**：ref=`quality/evidence/task2b-build-code-handoff.json`
- **执行事实**：T012 pipeline-compat GREEN 已真实执行，6 个 focused tests 通过；真实语义出口仍受 T013 前置事实限制。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k pipeline_compat`；exit `0`，6 passed，28 deselected。兼容回归另有 task2_publication 18 passed、phase25_llm 72 passed、Task 2-A 48 passed、batch recovery 13 passed。
- **evidence_refs**：`apply/evidence/T012.pipeline-compat.green.txt`
- **covered_ac**：AC-01、AC-03、AC-07、AC-08（typed handoff、失败不进 Reader、旧页保护、稳定入口；真实语义出口待 T013）
- **review_fact**：N/A — Phase 1 review pending
- **completed_at**：2026-08-10

#### T013 — N/A：冻结并执行一次真实语义运行

- **ID**：T013
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：在不临时挑样本、不降低门槛的前提下，记录真实 provider/model/budget/seed/sample/detector/threshold/归因/失败项和交付状态。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T012；权威样本清单 `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`、上游 Task 0 question set、受信 provider config
- **依赖**：T012
- **并行**：否 — depends on all behavior GREEN
- **FR**：FR-SEM-001、FR-SEM-002、FR-SEM-003
- **AC**：AC-01、AC-03、AC-05、AC-07、AC-09、AC-10、AC-11、AC-12、AC-13
- **动作**：T013 开始先回读当前 `cli.py`/config 的命令面（`digest --help`、`--config`、`--llm-format` 及其响应格式含义）和 runner 环境变量映射，把回读结果写入 preflight evidence；若实际命令面或变量映射与本卡冻结 gate_cmd 不一致，停止并记 `incomplete`，先修订当前 `plan.md`/`tasks.md`、重新发布并重新审查，不能在执行时就地改写 gate_cmd。随后绑定已有 sample manifest、`sample_count`、`sampling_seed`、Task 0 17+3 题集、当前 provider/model/base URL、credential、detector、budget、threshold 和 `section-dependency-record.v1`；在隔离 sample input/KB 上使用正常 `digest` CLI，不由本卡选择 provider。把真实结果写入 task evidence，至少记录 `answerability_source`、确定性 answerability subset id/hash、逐题 answerability/`first_hit`、`evidence_backtrace.claim_id`/`fragment_locator`、逐 section `section_completeness`、来源缺口 section audit/status、failure reason、实际 provider/model/detector/budget/threshold、`contract_revision`、`sample_count`、`sampling_seed` 和 `ac_bindings`：AC-01 绑定 page type/section/structure，AC-03 绑定正文/Evidence/Claim 回查，AC-05 绑定 impact closure，AC-07 绑定页级状态/导航投影/旧页保护，AC-09 绑定 sample manifest/coverage，AC-10 绑定运行身份/可复核字段，AC-11 绑定机器底线判定，AC-12/AC-13 绑定 revision ledger 和来源缺口 section。对 evidence 文件做必填字段和全部 AC 绑定机器断言；若任一前置事实缺失，记录 `incomplete/not_released`，不伪造通过。
- **evidence_binding**：`apply/evidence/T013.semantic-run.json` 在运行前解析为绝对路径且必须不存在；先导出 `KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE` 再启动同一次 `digest`，由 `digest`/`pipeline` 写入该新文件。文件必须含本次 `run_id`、sample/KB/input 指纹和 `output_path`；pytest validator 只读取这个路径并核对身份，路径不存在、是旧文件或身份不匹配就失败。
- **manifest_binding**：preflight 只接受 `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`；必须记录路径、存在性和 content hash，并把同一 hash 写入 T013 manifest/evidence。路径或 hash 无法回读时记 `incomplete/not_released`，不得用新 fixture 或自行挑选的样本替代。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`; symbols/regions: semantic_exit assertion and evidence capture guidance only；运行输入/KB 为隔离外部目录，不写进源码边界。
- **输出**：包含 answerability、first hit、evidence backtrace、section completeness、failure reason 和 revision ledger 的真实 semantic run evidence，或诚实的 missing/incomplete record。
- **Knowledge**：命令使用普通 `digest`，不建立第二 runner；provider/model/base URL/threshold/budget 的具体值必须来自 T013 开始前的事实回读，不由本卡猜测。
- **verification_role**：N/A — non-behavior real semantic evidence capture
- **paired_task**：N/A — non-behavior real semantic evidence capture
- **gate_cmd**：`bash -lc 'expected_evidence="$(pwd -P)/apply/evidence/T013.semantic-run.json"; export KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE="${KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE:?KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE is required}"; test "$KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE" = "$expected_evidence"; test ! -e "$expected_evidence"; uv run --frozen digest --help >/dev/null; uv run --frozen digest "${KNOWLEDGEDIGEST_TASK2B_SAMPLE_INPUT:?KNOWLEDGEDIGEST_TASK2B_SAMPLE_INPUT is required}" "${KNOWLEDGEDIGEST_TASK2B_SAMPLE_KB:?KNOWLEDGEDIGEST_TASK2B_SAMPLE_KB is required}" --config "${KNOWLEDGEDIGEST_TASK2B_SEMANTIC_CONFIG:?KNOWLEDGEDIGEST_TASK2B_SEMANTIC_CONFIG is required}" --llm-format="${KNOWLEDGEDIGEST_TASK2B_LLM_FORMAT:?KNOWLEDGEDIGEST_TASK2B_LLM_FORMAT is required}"; test -s "$expected_evidence"; uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_evidence_file'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-SEMANTIC-RUN — 证据含冻结运行身份、`sample_count`/`sampling_seed`、17+3 派生 answerability、逐题 first hit、Claim/fragment 回查、section completeness、来源缺口 section audit/status、修订记录、AC-01/03/05/07/09/10/11/12/13 全部绑定和覆盖/失败项，并证明 `run_id`、sample/KB/input 指纹及 `output_path` 来自本次 digest；环境变量、命令面、证据路径、运行身份或任一字段/绑定缺失都使 gate 非零；达到底线才记录 machine-passing，未达到底线但证据完整时 gate 仍以 exit 0 记录 `not_released`，不把它改写成通过。
- **evidence_path**：`apply/evidence/T013.semantic-run.json`
- **STOP**：命令面回读不支持冻结 gate_cmd、环境变量（包括 `KNOWLEDGEDIGEST_TASK2B_LLM_FORMAT`、`KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE`）、当前工作目录不是任务 worktree 根、`apply/evidence` 路径约定、权威样本清单 `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json` 或其 content hash、隔离目录、manifest、`sample_count`/`sampling_seed`、provider/model/detector/budget/threshold、Task 0 派生 answerability 或 section dependency v1 任一缺失，或 CLI/semantic evidence machine assertion 非目标失败时停止；只记 incomplete，不换 provider、不降阈值。诚实的完整 `not_released` 是 gate exit 0 的目标结果，不是失败。
- **recovery**：删除隔离 sample KB 和本次临时运行输出，保留不可用 provider/manifest 的事实证据，不动正式 KB。
- **task risk**：真实运行结束但样本覆盖或 provider identity 没有绑定到 evidence。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`incomplete`
- **actual_changes**：完成真实 T013 运行接线；使用冻结 sample manifest 指定的隔离输入/KB、embedding 配置和用户提供的 qwen3.6 provider 运行普通 `digest`。为避免主线程 HTTPS 无限等待，真实 provider 请求统一走可终止子进程；同时修正 TopicIndex 的 v2 路径 ID 不覆盖 digest 稳定 `topic-*` 身份，并保证离线模式不误套 typed provider contract。运行完成并写出绑定证据，但 provider 返回截断/不可解析 JSON，机器语义门明确失败，保持 `not_released`。同任务修复补齐了 mapped page 的 typed-body prompt、publication-only 与 typed body 的边界，以及语义证据 writer 对声明 sample input/KB 的绑定。
- **executed_commands**：`uv run --frozen digest --help`；单源真实 provider/embedding smoke；冻结 20-example / 30-source 隔离运行（run_id=`run-dc0d99596e70414099a31d54cf6b26fb`，28 rounds，30 source notes）；`uv run --frozen python -c '...validate_semantic_evidence_file...'` 返回 `valid=false`、`machine_exit_passed=false`；`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_evidence_file` 为 1 passed、38 deselected。
- **evidence_refs**：`apply/evidence/T013.preflight.txt`、`apply/evidence/T013.semantic-run.json`
- **covered_ac**：AC-09、AC-10、AC-12 的运行身份、样本/失败项、provider identity 和 revision ledger 已写入证据；AC-01/03/05/07 的实现绑定由前置卡覆盖，但真实运行因 provider 输出无效未达到 machine-passing。
- **review_fact**：本次 build-code integration review 已执行；当前审查发现的语义出口缺口和任务锚点证据限制已在 T014 处置，未把 incomplete 说成通过。
- **completed_at**：2026-08-11

#### T014 — N/A：最终 Task 2-B 与 Task 2-A 兼容回归

- **ID**：T014
- **Phase**：Phase 1：受控正文编译与机器出口
- **goal**：一次性确认本计划相关行为、现有 Task 2 publication/batch/corpus 回归和 Task 2-A Reader Bundle/Frontmatter/OKF smoke 都可运行，并记录真实限制。
- **design_state**：ready
- **versioned_refs**：`decision-log.md`、`spec.md`、`plan.md` 当前版本
- **输入**：T013 的真实状态记录或 incomplete evidence
- **依赖**：T013
- **并行**：否 — final aggregate
- **FR**：FR-FLOW-001、FR-FLOW-002、FR-DRAFT-001、FR-DRAFT-002、FR-DRAFT-003、FR-PUBLISH-001、FR-PUBLISH-002、FR-PUBLISH-003、FR-PUBLISH-004、FR-PUBLISH-005、FR-SEM-001、FR-SEM-002、FR-SEM-003、FR-COMPAT-001
- **AC**：AC-01、AC-02、AC-03、AC-04、AC-05、AC-06、AC-07、AC-08、AC-09、AC-10、AC-11、AC-12、AC-13
- **动作**：运行最终聚合命令，逐项记录 Task 2-B focused oracle、现有 Task 2 publication/batch/corpus 和 Task 2-A 兼容结果，并核对 `contract_revision=1/1`/revision ledger、section dependency v1、来源缺口 section audit、AC-01/03/05/07/09/10/11/12/13 evidence bindings 与所有语义出口字段；provider/样本未完成只记录限制，不把整体写成 released。
- **精确文件**：`tests/acceptance/test_task2b_body_compiler.py`
- **boundary**：files: `tests/acceptance/test_task2b_body_compiler.py`; symbols/regions: final aggregate verification only；不修改既有回归测试。
- **输出**：最终测试 evidence、覆盖矩阵、跳过原因和未解决限制。
- **Knowledge**：正式验收仍需当前 WorkflowHub review/human confirmation；绿色测试不替代 review、真实 provider 完成或人工读者门。
- **verification_role**：N/A — non-behavior final aggregate verification
- **paired_task**：N/A — non-behavior final aggregate verification
- **gate_cmd**：`bash -lc 'export KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE="$(pwd -P)/apply/evidence/T013.semantic-run.json"; test -s "$KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE"; uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_evidence_file; uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2_publication.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2a_reader_frontmatter.py tests/acceptance/test_task2a_okf_smoke.py -q'`
- **expected_exit**：0
- **oracle**：ORACLE-T2B-FINAL-REGRESSION — 先对 T013 同一路径、同一运行身份执行 `semantic_evidence_file` machine assertion，再执行 focused tests 和既有兼容回归；两者都退出 0，且 revision ledger、section dependency v1、来源缺口 section audit、AC-01/03/05/07/09/10/11/12/13 evidence bindings 和语义出口字段完整；结果单独标注 provider、sample、人工门和 formal release 限制。
- **evidence_path**：`apply/evidence/T014.final-regression.txt`
- **STOP**：如果聚合命令失败且无法归因到本计划变更、发现越界文件、或有人要求用旧 receipt/历史绿测替代当前证据，停止并保留真实失败。
- **recovery**：不做自动修复；回到对应失败 Task，必要时按 plan 的最小回滚命令验证。
- **task risk**：把完整测试绿灯误读为 Task 2-B 语义出口或 WorkflowHub stage 完成。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`incomplete`
- **actual_changes**：执行独立聚合回归并回读 T013 同一次 digest 的绑定证据；补齐版本冲突/非法版本/无版本产品概览/显式 release label 的正文门测试与 fail-closed 实现；兼容回归与全仓回归均通过，但 T013 evidence validator 明确返回 invalid，未把绿测冒充语义通过。
- **executed_commands**：T013 evidence-file focused test exit `0`，1 passed、40 deselected；Task 2-B/Task 2/Task 2-A aggregate exit `0`，123 passed、2 skipped；full repository `uv run --frozen pytest -q` exit `0`，484 passed、3 skipped；版本门 focused test 5 passed；T013 direct validator diagnostic 返回 `valid=false`、`machine_exit_passed=false`；qwen3.6 typed-body live smoke 返回三组必需 section，未把它当成正式样本语义出口；当前快照异源 integration review 返回 1 个 major incomplete 语义建议和 1 个 minor packet 锚点建议，未把 AC-09/10/11 的缺失证据说成通过；随后修复 qwen bridge 所需的 `chat_template_kwargs.enable_thinking=false`，新增 payload 回归断言，v5 全仓回归仍为 484 passed、3 skipped；使用 20 个冻结 example/30 个真实来源重跑时，provider transport 仍未在诊断窗口内完成，未将该诊断写成语义通过；正式 verify-code 已执行，当前 stage=`in_progress`、quality=`incomplete`，已绑定 v5 当前逐 AC evidence、测试和一次异源 review 事实，未取得 human confirmation，也未把语义出口延期说成完成。
- **evidence_refs**：`apply/evidence/T013.semantic-run.json`、`apply/evidence/T013.typed-body-live-smoke.txt`、`apply/evidence/T014.final-regression.txt`、`apply/evidence/T014.test-routing.json`、`quality/evidence/implementation/current-final-v3.json`、`quality/tests/build-code-full-regression-final-v3.json`、`quality/evidence/T014-build-code-review-current-v3.json`
- **covered_ac**：AC-01–AC-08、Task 2-A 兼容回归已通过；AC-09/AC-10/AC-11/AC-12 的字段和失败事实已记录，但 machine-passing、answerability 和完整 backtrace 仍 incomplete。
- **review_fact**：当前快照 integration review 已执行，result=`quality/reviews/results/build-code-default-165fa246b52ca465b084cdb0df34e2274e4cc2b7-b5bf0380-baf0-491d-8408-b200c6d29f42.json`；fixture 重标记问题、版本门测试缺口已修复；AC-09/10/11 的真实样本/语义出口缺口保持 `unknown/incomplete`、delivery=`not_released`，任务完成锚点的 packet 内摘录限制按审查事实保留。
- **completed_at**：2026-08-11

#### T014 追加执行事实

- 修复了语义模式对 `TopicIndex mapping_status != mapped` 页仍调用 provider 的问题：这类页现在直接保留 `degraded/Audit`，`planned_generator_calls=0`，不再浪费请求，也不可能靠 publication metadata 误进 Reader。
- 新增回归覆盖：`tests/acceptance/test_task2b_body_compiler.py` 与 `tests/acceptance/test_task2_publication.py`；完整 `uv run --frozen pytest -q` 为 `485 passed, 3 skipped`，`git diff --check` 通过。
- 已更新 WorkflowHub 实现/测试 receipts：`quality/evidence/implementation/current-final-v6.json`、`quality/tests/build-code-full-regression-final-v6.json`；正式 build-code stage 仍为 `in_progress/quality=incomplete`，原因是 AC-09/10/11 真实语义出口和当前 review snapshot 未闭合，未伪造通过。

### Verify

先执行 T001/T003/T005/T007/T009/T011 的 RED，再执行对应 GREEN；之后执行 T013 和 T014。每个 GREEN 必须保留对应 golden-negative/失败状态，T013 的 provider 或样本缺失只能记录 `incomplete/not_released`。

### Knowledge

实现只消费当前 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 与代码锚点；旧 receipt、历史评论、旧 plan/tasks 或 provider 空结果不构成完成事实。

### STOP

命令不可执行、RED 是 setup error、GREEN 需要弱化断言、依赖缺失、文件越界、需要新增产品决策，或真实运行无法冻结样本/provider/detector/budget/threshold 时 STOP。

### Done

每个行为 pair 有同一 gate_cmd/oracle 且 RED 在 GREEN 前；T013 有真实运行事实或明确 incomplete；T014 留下最终回归和限制；所有 Task 仍需由实际执行事实与 WorkflowHub 当前 stage evidence 认证后才能标记完成。

### Risks and rollback

风险是 provider 越界、影响闭包漏记、旧页覆盖和语义证据不足；只回滚本 Phase 的 MODIFY/NEW bytes，不删除正式历史页，不修改 Task 2-A 合同。

## 3. Dependency Graph

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014。

## 4. Requirement and Verification Traceability

| FR | Task IDs | AC IDs | Phase | Gate / evidence |
|---|---|---|---|---|
| FR-FLOW-001、FR-FLOW-002、FR-DRAFT-001 | T001、T002 | AC-01、AC-02 | Phase 1 | `ORACLE-T2B-TYPED-SECTIONS` |
| FR-FLOW-001、FR-PUBLISH-001、FR-PUBLISH-003、FR-COMPAT-001 | T011、T012 | AC-01、AC-03、AC-07、AC-08 | Phase 1 | `ORACLE-T2B-PIPELINE-COMPAT` |
| FR-FLOW-002、FR-DRAFT-002、FR-PUBLISH-001、FR-PUBLISH-002 | T003、T004 | AC-03、AC-04、AC-12 | Phase 1 | `ORACLE-T2B-PROVENANCE-GATE` |
| FR-DRAFT-003、FR-PUBLISH-003、FR-PUBLISH-004、FR-COMPAT-001 | T005、T006 | AC-05、AC-06、AC-07 | Phase 1 | `ORACLE-T2B-IMPACT-CLOSURE` |
| FR-PUBLISH-005 | T007、T008 | AC-04、AC-08 | Phase 1 | `ORACLE-T2B-SEMANTIC-SPLIT` |
| FR-SEM-001、FR-SEM-002、FR-SEM-003 | T009、T010 | AC-09、AC-10、AC-11、AC-12 | Phase 1 | `ORACLE-T2B-SEMANTIC-EXIT-GATE` |
| FR-SEM-001、FR-SEM-002、FR-SEM-003 | T013 | AC-09、AC-10、AC-11、AC-12 | Phase 1 | `ORACLE-T2B-SEMANTIC-RUN` |
| FR-SEM-001、FR-SEM-002、FR-SEM-003 | T014 | AC-09、AC-10、AC-11、AC-12 | Phase 1 | `ORACLE-T2B-FINAL-REGRESSION` |

## 5. Final Boundary Check

Phase 1 NEW/MODIFY 与全局 File Boundary 一致；所有生产文件至少由一张卡负责；所有 FR/AC 都有 task 与 gate/oracle；依赖图无环；T001/T003/T005/T007/T009/T011 的 RED 均先于 reciprocal GREEN；T013/T014 明确为非行为 N/A，不替代行为配对。

## 6. T013/T014 当前快照追加执行事实（2026-08-11）

- 修复正文编译的多批次 typed section 合并：同一页被按来源拆批时，先合并各批 section/body/claim mapping，再进入正文门；补充多批次测试。另修复 typed claim 回查允许可信的 provider 改写正文、但仍强制 claim 映射、来源 URI/fragment、指纹和脚注归因；degraded typed response 不再进入 compiler；离线页状态不再误标为 degraded。
- 相关测试：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2_publication.py -q`，exit `0`，`72 passed`；`uv run --frozen pytest -q`，exit `0`，`490 passed, 3 skipped`；`git diff --check`，exit `0`。
- 当前全仓测试权威 receipt：`quality/tests/build-code-full-regression-20260811-v14.json`，receipt hash=`2e63248ff940e63271b6c9253437d7b1788643237d28e0b38e7b8f77b9174f96`，snapshot_tree=`0588152d28802a14cda18cdb953edd943f16d729`，output=`quality/tests/output/build-code-full-regression-20260811-v14.output`，output hash=`0c0be457e7dcc881bc28eb9ab6442a7518f768c31076909f8652b2f986ea530e`。
- T013 正确绑定 `_digest/topic-index.json` 后的真实语义运行：隔离根目录 `/tmp/kd-task2b-semantic-run-v11.XIRfAk`，run_id=`run-0eda73df62c4477aa7d1a1edca8f0454`，`run_status=completed`，provider calls=`113`；13 个 TopicIndex degraded 页未调用 provider，6 个 `module_or_capability` 页进入 typed/compiler；最终 `concepts=0`、`answerable=0`，validator=`valid=false`、`machine_exit_passed=false`、`delivery_status=not_released`。失败事实包括 provider 未完整提供可信 claim mapping、required section 缺失、unsupported claim facts/empty relationship、版本不合法和部分映射不完整；没有把该运行记为语义通过，也没有写入凭据。
- 因冻结 sample 的 page-type 覆盖只有 6 个可进入 typed/compiler 的 `module_or_capability` 页，缺少 `product_overview` 与 `procedure_or_rule`，AC-09/AC-10/AC-11 仍为 `unknown/incomplete`；AC-01–AC-08 的实现与回归证据完整，AC-12 的字段/修订记录已记录，但不能替代真实语义出口和人工读者门。当前交付状态继续为 `not_released`，build-code phase review 仍待当前快照审查。

### Phase 1 review 处置（当前快照）

- 当前 phase review ref=`quality/reviews/results/build-code-default-a33dcb26e1f4b4385a23a1f119268c75627b2a9e-0af7ba31-890a-43c7-864c-f6335f484ec4.json`，snapshot_tree=`a33dcb26e1f4b4385a23a1f119268c75627b2a9e`。异源 provider 返回了 2 个有效的 minor 建议；另 2 个 major 建议在 adjudication 中因 provider 只引用 diff-shard 行号而标为 `invalid_evidence`，仍逐项检查了根因。
- 已修复/加固：正式 pipeline 给 body gate 传入同页/跨页近重复上下文；映射页禁止非空 section 缺失 trusted claim_ids；sample manifest 只从当前项目工作目录读取，不向任意父目录爬取；结构 normalizer 将 fenced code 消费到闭合 fence。新增对应回归测试；当前 focused 回归为 `75 passed`，下一步需生成新快照 receipt 并重新审查。

### Phase 1 review 追加处置（当前快照）

- 当前复审 ref=`quality/reviews/results/build-code-default-378bc0446e375cf79e1c74f7e86e7f9a6c2f13f9-499100ca-c1df-4171-836e-afc2de2fe8e4.json`，snapshot_tree=`378bc0446e375cf79e1c74f7e86e7f9a6c2f13f9`。异源结果为 1 个 major（adjudication=`invalid_evidence`，因 diff-shard 行号无效）和 2 个 nonblocking minor；major 根因仍做了代码核对。
- 已补齐 PageDraft section dependency 的 `claim_deps`/`attribution_deps`，Claim/来源归因变化会改变 `dependency_hash` 并进入影响闭包；当 module/procedure 来源没有版本事实时，`version` 不再强制 provider 猜测，页面安全省略该 section。新增对应回归，focused 回归为 `76 passed`。
- 语义证据输出路径继续保持“一次运行一个预声明的新文件、已存在即失败”的绑定合同；这是 T013 防止旧证据覆盖和伪造重跑身份的明确门，不按 minor 建议改成覆盖或静默轮转。

### Phase 1 当前最终回归快照（待当前 review 绑定）

- 全仓回归：`uv run --frozen pytest -q`，exit `0`，`494 passed, 3 skipped`；`git diff --check`，exit `0`。
- 当前实现 receipt：`quality/evidence/implementation/current-final-v10.json`，hash=`8faaa790e65c751d5848b308faceba9e799f5ba37e97a6b32efad7da9884cceb`，diff=`quality/evidence/implementation/f0a8df973b4c91d495d9cb742dc8c470b690643cabefa428946995c4b96250bc.diff`，diff hash=`f0a8df973b4c91d495d9cb742dc8c470b690643cabefa428946995c4b96250bc`。
- 当前测试 receipt：`quality/tests/build-code-full-regression-20260811-v17.json`，hash=`ef18b25a7c61bb81497780539455ed00d956137d63c04200a4aa7563d68eb1ce`，snapshot_tree=`af57a50c752b42013442e5fbe1b5b20873fc7ea6`，output=`quality/tests/output/build-code-full-regression-20260811-v17.output`，output hash=`407682258d70b1a684d5cdc36e0f95aeefc3f31dd03194f4612ff10aacbd2856`。

### Verify-code 追加修复与真实重跑（2026-08-11）

- 发现并修复一个正文编译缺陷：typed PageDraft 原先沿用 legacy body-refinement 的 source/claim 小批次拆分，但每个批次仍要求完整 page-wide required sections，导致批次缺少 section 证据时 provider 必然返回不完整映射，整页被降级。现在 typed body 一页只发一个包含完整可信 Claim 集合的 provider context；请求过大或失败仍走原有 fail-closed/degraded 路径，不改变 section/page type 合同。新增 `test_typed_generation_keeps_complete_page_claims_in_one_provider_context`，并更新多批次回归为完整 typed page contract 回归。
- 修复后 focused 回归：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2_publication.py -q`，exit `0`，`80 passed`；全仓回归：`uv run --frozen pytest -q`，exit `0`，`498 passed, 3 skipped`；`git diff --check`，exit `0`。
- 使用同一冻结 sample manifest、同一隔离输入/KB 和用户提供的 allowlisted provider identity 重跑 T013：run_id=`run-538bed276afb43e9b509bda2a835ea55`，provider calls=`14`/planned `14`，Task0 budget=`within_budget`，run_status=`completed`，delivery=`not_released`；证据=`apply/evidence/T013.semantic-run-v13.json`，sha256=`8f282b9a8759c0f5193d84bd82d6d93e641410060cb53275abf268a040014647`。
- 真实重跑仍为 `concepts=0`、`evidence_backtrace=0`、`answerable=0`，validator/machine exit 未通过。13 页 TopicIndex degraded 被正确跳过；剩余 6 页全部是 `module_or_capability`，没有 `product_overview` 或 `procedure_or_rule` 覆盖；provider 对部分大页返回截断/不可解析 JSON，对其他页返回缺少可信 section claim mapping 或 token/faithfulness/重复门失败。T013 因此仍为 `incomplete/not_released`，AC-09/AC-10/AC-11 继续 `unknown`，不能声称语义机器出口通过。
- 这次真实运行确认代码缺陷已修复且预算问题已消除，但冻结样本的页面类型覆盖、上游 TopicIndex 映射和语义内容质量仍不足以满足原始 `>=6` 且三类各至少 1 个的出口；不通过修改 Task1 冻结产物、临时换样本、猜 page type 或放宽门槛解决。

### Verify-code 当前快照收尾事实（2026-08-11）

- 通过 WorkflowHub canonical `verify-code` test capture 重新执行当前工作区完整回归：`uv run --frozen pytest -q`，exit `0`，`498 passed, 3 skipped`；receipt=`quality/tests/verify-code-final-full-20260811-v23.json`，receipt_hash=`d90325809f1da9af5760dbd0a606c495376a29a087d8581c7420b503a655c415`，snapshot_tree=`6d35d9fd55490de18478708bda4afb0b157697ae`，output=`quality/tests/output/verify-code-final-full-20260811-v23.output`。
- 已用 WorkflowHub 官方 `verify-code` runner 绑定当前测试 receipt、既有实现审查事实、一次 verify-code 异源审查尝试、AC evidence 和 verification receipt；当前结果为 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。本次没有重复异源审查，也没有调用 `close`。
- 当前官方质量事实 refs：测试=`quality/facts/56d4859bd0a0a17de3404bb8e13ef82eb484054079642064140a538c91a53003.json`；finding dispositions=`quality/facts/3ed73b8d20580235d60b1ef31d36051f26aabf04dfdc710f0e52953329caa518.json`。缺失/unknown 仍明确保留：`independent_review`（provider 输出非法 JSON）、`AC-09/AC-10/AC-11`（语义证据失败）、`exceptions` 和 `human_confirmation`。
- Verify 反向检查再次确认：原始 PRD Task 2-B、当前 decision/spec/plan/tasks、完整用户流程、三类页面范围、published/degraded/not_released 边界、旧 Reader 保护、非目标和延期项均已覆盖；没有把“498 个测试通过”或 provider transport 成功解释成语义出口通过。
- 收尾结论：当前代码修复和确定性回归完成；真实语义出口仍 `unknown/incomplete`，交付继续 `not_released`。按要求停在 close 前，等待用户对 verify-code 结论的确认；不得推断确认或继续进入 close。

### Verify-code 后续缺陷修复（2026-08-11）

- 发现并修复正文门的边界错误：原实现把一个主题的全部来源 Claim 都强制放进 provider 的正文 Claim 映射，导致大主题必须返回数百个映射；provider 截断或无法逐项映射时，即使读者正文只使用了少量事实也会整页降级。规格要求是“进入 Reader 的事实 100% 可回查”，完整 Claim/Evidence 仍保留在 Audit/Archive；未进入正文的来源 Claim 不应被强迫伪装成正文事实。
- 修复内容：`pipeline._typed_body_gate_payload` 将完整来源 Claim ledger 与 Reader body claims 分开；正文门只校验 typed sections 实际引用的 Claim，完整 Claim 仍从 draft/audit evidence 保留。provider prompt 同步说明只为实际陈述的事实返回 `claim_ids`，不改变 page type、section、来源字段或失败边界。
- 新增回归：`test_typed_body_gate_separates_reader_claims_from_complete_evidence_ledger`；focused 回归 `uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2_publication.py -q`，exit `0`，`81 passed`。
- 当前全仓回归：`uv run --frozen pytest -q`，exit `0`，`499 passed, 3 skipped`；`git diff --check`，exit `0`。这次改动尚未重新生成 WorkflowHub verify-code receipt，也尚未重新执行真实 T013；既有 T013 v13 证据仍只能说明此前语义出口 `incomplete/not_released`，不能替代修复后的新运行。

### Verify-code 最新证据登记（2026-08-11）

- 已通过 WorkflowHub canonical `verify-code` test capture 重新执行当前工作区：`uv run --frozen pytest -q && git diff --check`，exit `0`，`499 passed, 3 skipped`；receipt=`quality/tests/verify-code-final-full-20260811-v25.json`，receipt_hash=`a78e17644849daef8090df2c0197aa64f7df10e70a480999da97608380713165`，snapshot_tree=`e6e9fdd67e6897f93e5f3b24c70f38c316844574`，output=`quality/tests/output/verify-code-final-full-20260811-v25.output`。
- 已用同一份当前四材料、既有 build-code 一次通过审查事实、既有 verify-code 异源审查尝试、AC evidence 和 finding dispositions 执行一次 WorkflowHub `verify-code`；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。没有重复异源审查，没有调用 `close`。
- 最新 verify 事实：`full_tests_fresh=satisfied`；`finding_dispositions=satisfied`；`independent_review` 仍因 provider 输出非法 reviewer JSON 而 `missing`；`AC-09/AC-10/AC-11` 的真实语义证据仍 `unknown/incomplete`；`exceptions` 与 `human_confirmation` 仍 `missing`。失败证据继续保留：`quality/evidence/verify-ac-09-v6.json`、`quality/evidence/verify-ac-10-v6.json`、`quality/evidence/verify-ac-11-v6.json`。
- 本轮继续核查了本机原始样本和 Task 0/Task 2-A 证据：当前只有冻结 sample coverage、TopicIndex、Task 2-A 归因探针和 Task 2-B 行为 fixture；没有可合法重放 T013 的原始样本目录。Task 2-A 手写 fixture 明确不是语义发布，不能冒充真实语义运行；Task 0 也明确只证明运行/防丢失，不证明 Reader answerability 或 semantic quality。因此没有临时换样本、猜 page type、重标记 fixture 或伪造 T013 通过。
- 收尾判断：代码、确定性测试和 verify 反向检查已完成；真实语义机器出口继续 `not_released`。保持在 `verify-code`、`close` 前，等待后续补齐真实样本/有效异源审查或用户确认，不能把当前结果报告为 Task 2-B 完成。

### T013/T014 最新更正（2026-08-11）

- 更正上一条“没有可合法重放的原始样本目录”的过时判断：已从本机只读的 Downloads 原始审计材料恢复冻结 `20` 个 example 对应的 `30` 个真实来源；逐文件 SHA-256 与 Task 0 `source-manifest.json` 一致。输入不是 Task 2-A 手写 fixture，Task 2-A fixture 仅用于显式 page-type 映射，不作为语义正文证据。
- 冻结样本 manifest 已回读：`quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`，content hash=`fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f`；sample=`20`，source=`89`，sampling seed=`4026961625`。原始来源和隔离 KB 只用于本次 T013，不写入正式知识库。
- 修复正文编译的实际缺陷：同一条事实可被多个 Reader section 引用，但语义 part ledger 必须只有一个 owner；现在按 section 顺序确定唯一 part owner，Reader 正文支持关系不丢，完整 Claim/Evidence ledger 仍保留。新增 `test_shared_section_claim_gets_one_semantic_part_owner`。
- focused 回归：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2_publication.py -q`，exit `0`，`82 passed`；全仓回归：`uv run --frozen pytest -q`，exit `0`，`500 passed, 3 skipped`；`git diff --check`，exit `0`。
- 修复后真实 T013：普通 `digest` 在隔离输入/KB 上完成，run_id=`run-87cdb14fc528422d9544587c80b2721b`，run_status=`completed`，execution=`real_semantic`，provider calls=`15/15`，delivery=`not_released`；证据=`apply/evidence/T013.semantic-run-v16.json`，sha256=`78e310527db6e3608a1c1dccfb23b44d62d32a710a8e24336c64182f0066e883`。provider 凭据只通过环境变量使用，未写入材料或证据。
- v16 真实证据出现 `6` 个 machine-passing concepts：`5` 个 `module_or_capability`、`1` 个 `product_overview`；evidence backtrace=`617`，section completeness=`6`，answerability=`13/20`。因此重复 claim 的代码问题已解决，`>=6` 和 product 覆盖已获得真实证据；但 `procedure_or_rule` 仍没有 machine-passing page。
- `procedure_or_rule` 的真实探针来源是“17 智能搭建”设计比较文档；provider 返回 `section exceptions claim mapping is missing`，所以页面保持 degraded/Audit，不补空话、不猜异常规则、不改 page type/必需 section。其他真实失败（截断 JSON、缺 section claim mapping、版本/归因门）也保留在 `failure_reasons`，不能把部分通过写成整体通过。
- 当前结论仍是 `T013=incomplete`、`AC-09/AC-10/AC-11=unknown/incomplete`、delivery=`not_released`。这是修复后最新真实证据，替代此前 v13/v15 的运行结论；不得使用旧 WorkflowHub receipt 代替本次结果。
- WorkflowHub 约束不变：不重复异源审查、不调用 `close`；修改材料后必须重新 capture 当前测试并重新执行一次 verify-code 反向检查。独立审查、exceptions、human confirmation 仍按 `missing/unknown` 记录，不伪造通过。

### Verify-code 最新官方结果（2026-08-11）

- 材料更新后的 canonical test capture：`uv run --frozen pytest -q && git diff --check`，exit `0`，`500 passed, 3 skipped`；receipt=`quality/tests/verify-code-final-full-20260811-v27.json`，receipt_hash=`f0a71ed6f6143b9e7683d2f7b97f67e5f155219205d6f3aeb96b28f41984fd43`，snapshot_tree=`6225e716cd2457c1c63e4ecbff09176832568f1e`，output_hash=`34d22c152ae5ad9da3795bebde223a14be12b9cc58821f2961ede0ea34cd1b04`。
- 使用当前四份材料、v27 测试 receipt、既有 build-code 一次审查事实、既有 verify-code 一次异源审查 attempt、finding dispositions 和 verification receipt 执行官方 verify-code；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。
- 官方 freshness 事实：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；仍为 `independent_review=missing`（provider reviewer JSON 无效）、`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。官方旧 acceptance refs 仍把 AC-09/10/11 标成 failed/unknown；不能用这次 6 concepts 的局部改善冒充三类完整语义出口。
- verify 反向检查仍覆盖原始 PRD、当前 decision/spec/plan/tasks、完整用户流程、三类页面范围、`published/degraded/not_released` 边界、旧 Reader 保护、非目标和延期项；没有调用 `close`，也没有重复异源审查。

### 当前材料绑定修正（2026-08-11）

- 上一条 v27 receipt 写入后材料又增加了官方结果记录，故 v27 只作历史记录；当前材料快照对应的最新 canonical test capture 是 `quality/tests/verify-code-final-full-20260811-v28.json`，receipt_hash=`34b1aef6926865e95c43f9b1e51d8b4b4576264e61e41b980c69ccd7531fdf87`，snapshot_tree=`773f0929b5ad4ff4593c78712ca8dfb67c067a3c`，output_hash=`223db25af36662061afbe646e31dbbe27db0a947fb50a5405f4263a65a33a78d`，exit `0`，`500 passed, 3 skipped`。
- 绑定 v28 的官方 verify-code 结果仍为 `in_progress / ready / quality=incomplete`；fresh tests 和 finding dispositions 满足，`independent_review`、`acceptance_criteria`、`exceptions`、`human_confirmation` 继续 `missing`，没有重复审查或调用 `close`。

### 最终当前快照绑定（2026-08-11）

- v28 记录后未改变产品/实现结论，但当前材料已完成最终落盘；最新 canonical test capture 为 `quality/tests/verify-code-final-full-20260811-v29.json`，receipt_hash=`aaec3412b97389c1b2feb7971875d06d951efe8f12b2f3659865f430ca8ed7a6`，snapshot_tree=`e4056ed11d433f276131f4f51180e9457f1c0f05`，output_hash=`b05921dcdecec32500f1203f342d09e775fb256c9b5acc3bbbac01ebf20851d3`，exit `0`，`500 passed, 3 skipped`。
- v29 对应的官方 verify-code 仍为 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`；fresh tests 和 finding dispositions 满足，独立审查不可用、AC-09/10/11 仍不闭合、exceptions 和 human confirmation 缺失。到这里停在 close 前，不重复审查、不调用 close。

### Verify-code 后续测试证据修正（2026-08-11）

- 修正了旧的 `unsupported-fact` 负例：原测试在缺少必需 section 的 validator 层就失败，不能证明正文事实门真正拦截无来源事实；现已移除该错层 fixture，并在 `validate_body_gate` 层加入带完整 Claim/footnote 的无来源正文负例。
- 受影响测试：`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`；没有改变生产代码、page type、section contract 或失败边界。
- focused 回归：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q`，exit `0`，`62 passed`；全仓回归：`uv run --frozen pytest -q`，exit `0`，`500 passed, 3 skipped`；JSON 校验和 `git diff --check` 均通过。
- 该修正只补强测试证据，不改变既有一次 build-code phase review 事实；不重复异源审查。当前仍在 verify-code，真实 `procedure_or_rule` 语义出口、独立审查、exceptions 和 human confirmation 继续按 `unknown/incomplete/missing` 记录。

### Verify-code 当前官方绑定（2026-08-11）

- 最新 canonical 测试 receipt：`quality/tests/verify-code-final-full-20260811-v31.json`，receipt_hash=`9fc4520203fa5284ab75427e4b038ebd70424d84a3b28c4b6a5e2106a10c24b3`，snapshot_tree=`9f06822686bc6f28b58e785a21b797625f95fac5`，output_hash=`3519faafe83ef9c27f4a37a1a89ab74775c51dcf5fda904d8dea8d2a3ef89aa4`；命令 `uv run --frozen pytest -q && git diff --check`，exit `0`，`500 passed, 3 skipped`。
- 已用 WorkflowHub 官方 `verify-code` runner 绑定 v31 测试、既有 review/finding dispositions、语义 evidence 和 verification receipt；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。本轮没有重复异源审查，也没有调用 `close`。
- 官方质量事实：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`（provider reviewer JSON 非法）、`acceptance_criteria=missing`（AC-09/10/11 真实样本/语义出口不闭合）、`exceptions=missing`、`human_confirmation=missing`。失败证据仍保留：`quality/evidence/verify-ac-09-v6.json`、`quality/evidence/verify-ac-10-v6.json`、`quality/evidence/verify-ac-11-v6.json`。
- 反向检查仍覆盖原始 PRD、Design、完整用户流程、三类 page type、`published/degraded/not_released` 边界、旧 Reader 保护、非目标和延期项；因此不能把代码测试绿灯或部分语义概念通过说成 Task 2-B 已交付。

### Verify-code 后续保真门修复（2026-08-11）

- 完成一次完成性审计后发现：typed body 流程把 `typed_claim_ids` 当成充分证明，可能让带合法 Claim ID 的无来源正文绕过 token/faithfulness 门。现已在 `publication.py` 增加保守的改写校验：typed mapping 仍可允许正文改写，但必须保留足够 Claim 词项，并保留数字和大写标识符；无 typed mapping 继续要求归一化后的事实原文命中。
- 新增回归：无来源正文即使带 `typed_claim_ids` 也降级；数字从 `99%` 改成 `100%` 也降级；保留数字的合理改写继续通过。相关测试在 `tests/acceptance/test_task2b_body_compiler.py`。
- 受影响代码/测试没有改变 page type、section 集合、字段合同或失败状态；全仓回归：`uv run --frozen pytest -q`，exit `0`，`502 passed, 3 skipped`；Task 2-B focused 回归为 `84 passed`；`git diff --check` 通过。
- 修复后冻结 20-example 真实语义重跑使用 300 秒边界，exit `124`，没有生成新的 semantic evidence；事实记录在 `apply/evidence/T013.semantic-run-v17.timeout.txt`，按 `unknown/incomplete` 处理，T013 v16 仍是最近一次完成的真实运行，不把超时当通过。
- 该同任务修复未重复 build-code/verify-code 异源审查；当前 verify-code 仍保持 close 前，真实语义出口、独立审查、exceptions 和 human confirmation 不伪造通过。

### Verify-code 后续重复 Claim 投影修复与 T013 重跑（2026-08-11）

- 完成真实运行后的代码审计发现：同一来源中重复出现的相同句子会保留多个不同 `fragment_locator` 的完整 Claim 记录，但正文门按 `claim_fingerprint` 作为脚注身份，错误地把这些合法重复来源判定为 `claim attribution is not unique`。现已修复 `pipeline._typed_body_gate_payload`：完整 `evidence_claims` 不去重；Reader body gate 只对每个被引用 fingerprint 取首个确定性代表，避免丢失来源位置，也不放宽正文事实门。
- 新增回归 `test_typed_body_gate_projects_repeated_source_claim_once_but_keeps_evidence_occurrences`；focused `uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q`，exit `0`，`65 passed`；全仓 `uv run --frozen pytest -q`，exit `0`，`503 passed, 3 skipped`；`git diff --check`，exit `0`。
- 使用同一冻结 manifest（sample=`20`、source=`89`、hash=`fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f`）和隔离输入/KB，以真实 qwen3.6 provider 重新执行普通 `digest`；embedding 探针使用受控短超时后明确回退 Jaccard，未把回退伪装成 embedding 通过。run_id=`run-377d583f065b4e8b90742d48d6be62e6`，`run_status=completed`，provider calls=`15/15`，证据=`apply/evidence/T013.semantic-run-v19.json`，sha256=`bfca47726c6a1721117e44440538e5f1fb36acd7d422977dcb20bea08f44e736`，delivery=`not_released`。
- v19 真实证据得到 `2` 个 machine-passing concepts，均为 `module_or_capability`；`evidence_backtrace=291`、完整 section=`2`、answerable=`11/20`。相较 v18 的 `1` 个 machine-passing concept，重复 Claim 误判已实际减少；但仍缺 `product_overview` 与 `procedure_or_rule`，validator=`valid=false`、`machine_exit_passed=false`。其余失败保留为真实 provider 截断 JSON、section claim mapping 缺失、保真不匹配、near duplicate、degraded TopicIndex 和非法版本等，不以放宽门槛解决。
- `procedure_or_rule` 仍来自“17 智能搭建”设计比较来源；原始材料没有可回查的 `exceptions` 规则，不能把“缺点”改写成异常处理，也不能填“暂无异常”占位。因此该页继续 `degraded/Audit`，不改变 page type 或必需 section 合同。
- v19 semantic evidence validator 结果：`valid=false`、`machine_exit_passed=false`、`delivery_status=not_released`，原因是 machine-passing concept 少于 `6`，且缺 `product_overview`、`procedure_or_rule` 两类。该事实替代 v18 的最新真实运行结果；v17 超时记录仍保留为历史诊断，不把任何一次超时或部分通过写成语义通过。
- 本轮没有重复 build-code/verify-code 异源审查；由于本次修改更新了当前材料和实现，下一步只需按既定一次性规则重新 capture 当前测试并执行一次官方 verify-code。独立审查、exceptions、human confirmation 继续按 `missing/unknown` 记录，不调用 `close`。

### Verify-code v35 当前材料绑定（2026-08-11）

- 当前材料更新后的 canonical 测试 capture：`uv run --frozen pytest -q && git diff --check`，exit `0`，`503 passed, 3 skipped`；receipt=`quality/tests/verify-code-final-full-20260811-v35.json`，receipt_hash=`296ee03c35a9858e8807d3d90b63c48ac43b0ee68f6eee62292b7ec9e5489a3d`，snapshot_tree=`bb231a49b7e10e45a248636e99aed28d9c7af1b6`，output_hash=`a03559323aae7a2ef013df59bd70f537622f482614da7f4396f231e7dcc8d387`。
- 已用当前四份材料、v35 测试收据、既有一次 build-code review、既有一次 verify-code 异源审查 attempt、finding dispositions 和 T013 v19 事实执行官方 `verify-code`；结果：`stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。
- 官方质量事实：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`（provider reviewer JSON 非法）、`acceptance_criteria=missing`（AC-09/10/11 仍无完整语义出口）、`exceptions=missing`、`human_confirmation=missing`。官方 warnings 明确保留三类 page type、answerability、完整 backtrace、`>=6` machine-passing concept 和用户确认缺口；delivery 继续 `not_released`。
- 这次没有重复异源审查，没有调用 `close`。由于本条事实追加会改变当前材料快照，后续如继续执行 verify，必须先重新 capture 当前测试；当前停在 close 前。

### Verify-code prompt 上下文收敛与 T013 v20（2026-08-11）

- 完成一次实现审计后确认：typed body provider 请求原来同时携带重复的 `initial_body`/`source_text`，并可能携带旧 `existing_target_body`；这会增加请求体和旧说法残留风险。现已让 typed prompt 只携带当前 `source_text`、完整 Claim 和固定 typed page contract，并明确要求只为同一 section 实际陈述的事实返回 `claim_ids`；legacy prompt 不变。
- 新增回归 `test_typed_prompt_does_not_repeat_source_or_send_stale_reader_body`；focused 回归为 `158 passed`，全仓回归为 `504 passed, 3 skipped`，`git diff --check` 通过。
- 使用同一冻结 manifest、同一隔离真实来源、同一 qwen3.6 provider、同一 8192 token budget 和原门槛执行 T013 v20：run_id=`run-1be80b3959ff4a15bc22ea5c3d8c7c5a`，run_status=`completed`，provider calls=`15/15`，execution=`real_semantic`，evidence=`apply/evidence/T013.semantic-run-v20.json`，sha256=`32b5a11c8414c500f01195f5251768f7d6e51e67b86a980946e94e11f6bab331`，delivery=`not_released`。
- v20 只有 `1` 个 machine-passing concept，类型仍只有 `module_or_capability`；`evidence_backtrace=212`、完整 section=`1`、answerable=`11/20`。仍缺 `product_overview`、`procedure_or_rule` 和 `>=6` machine-passing concepts；provider 的 section claim mapping、保真门和输入映射失败继续真实保留，不能改成通过。
- prompt 修复没有把真实语义出口变成通过；独立只读审查也未发现新的明确代码缺陷。当前结论仍是 T013=`incomplete`、AC-09/AC-10/AC-11=`unknown/incomplete`、delivery=`not_released`。本条追加后必须重新 capture 当前测试并执行一次官方 verify-code；不重复异源审查，不调用 `close`。

### Verify-code v39 官方结果（2026-08-11）

- 当前 canonical 测试 capture：`uv run --frozen pytest -q && git diff --check`，exit `0`；receipt=`quality/tests/verify-code-final-full-20260811-v39.json`，receipt_hash=`4f82255b2a37f5ffff448ed6f13ce332ef7e7ca9349be36125af7fcec9d670d8`，snapshot_tree=`c68a76d77b8e5161f76cb43c86bbef2975958ed0`，output_hash=`1565364e83c3a5416d4c7a2cb681cbb1aade7815ff08c2920c84d6e990a1b030`。
- 已用当前四份材料、v39 测试 receipt、既有一次 build-code review、既有一次 verify-code 异源审查 attempt、finding dispositions 和 T013 v20 事实执行官方 `verify-code`；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`，且 `full_tests_fresh=satisfied`、`finding_dispositions=satisfied`。
- 官方仍把 `independent_review`、`acceptance_criteria`、`exceptions`、`human_confirmation` 标为 `missing`；AC-09/10/11 真实语义证据、三类 page type、answerability、完整 backtrace、`>=6` machine-passing concepts 仍不闭合，delivery=`not_released`。这次没有重复异源审查，没有调用 `close`；保持在 close 前。

### Verify-code 后提示词与格式 Claim 修复、T013 v21-v23（2026-08-11）

- 继续按一次性异源审查规则推进，没有重复 make-decision/build-spec/build-plan/verify-code 审查，也没有调用 `close`。本轮只修复已接受 typed body 合同的实现行为，不改变 page type、section 集合、字段合同、失败状态或语义门槛。
- 修复 `llm.py` typed prompt：补充三类 section 的原始合同语义；要求 claim_id 只绑定同一 section 实际陈述的事实；URL、路径、命令、标识符、数字、版本、表格值和链接没有原样保留时不得挂该 claim；sources 不得把修订表当正文证据；没有证据不得填占位内容。新增 prompt 回归覆盖 section 说明和保守 claim 绑定。
- 修复 `validate_section_response` 对 Markdown 表格分隔线的误伤：格式分隔线保留在完整 Claim/Evidence ledger，但不再要求进入 Reader 正文语义 claim；新增回归证明它不会被当成读者事实，同时缺少其他真实 claim 仍然 `degraded`。
- focused 回归：`uv run --frozen pytest -q tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_phase25_llm.py tests/acceptance/test_task2_publication.py`，exit `0`，`160 passed`；`git diff --check`，exit `0`。随后全仓 `uv run --frozen pytest -q`，exit `0`，`505 passed, 3 skipped`。
- T013 v21 使用同一冻结 manifest、同一隔离真实来源、同一 qwen3.6、8192 token、15 planned calls；run_id=`run-6a23c822cacc487b92c2face77741fb8`，evidence=`apply/evidence/T013.semantic-run-v21.json`，sha256=`4cd79e08b7c4efbfb7fc75236997bf641f6b85463e5b4f86c30ff5325a9fea2f`，`run_status=completed`，`delivery=not_released`。提示词使 `procedure_or_rule` 生成了完整 section，但仍被事实保真门拒绝；不能记为 machine-passing。
- T013 v22 在提示词补强后完成：run_id=`run-a2acfc2d6e034515b2aa8b9d1abfee4f`，evidence=`apply/evidence/T013.semantic-run-v22.json`，sha256=`5b4f01b2b926eedbcbdd316500c409d5902b6559392460d6732154ed782e7392`，`run_status=completed`，`delivery=not_released`；得到 `2` 个 machine-passing concept，均为 `module_or_capability`，`evidence_backtrace=393`、完整 section=`2`，仍缺 `product_overview`、`procedure_or_rule` 和 `>=6`。
- T013 v23 在表格格式 Claim 修复后完成：run_id=`run-1e2741e45fc24947ae654fd17da09feb`，evidence=`apply/evidence/T013.semantic-run-v23.json`，sha256=`e7f05c40b3b16253fc1733cee4fe76784ba6d34f17a2b50ed0f1df543a66882a`，`run_status=completed`，`delivery=not_released`；结果仍为 `2` 个 `module_or_capability` machine-passing concept，未达到语义出口。procedure 仍因来源没有可回查 `exceptions` 规则而不能通过；不把“缺点”改写成异常，也不填占位句。
- 当前真实结论：T013=`incomplete`；AC-09/AC-10/AC-11=`unknown/incomplete`；独立审查、exceptions、human confirmation 继续按 `missing` 记录；旧 Reader 保护和 fail-closed 边界保持有效。由于本条更新了当前材料，下一步必须重新 capture 当前全仓测试并执行一次官方 verify-code；不重复异源审查，不调用 `close`。

### Verify-code embedding fallback 与 v42 官方绑定（2026-08-11）

- 官方全量测试第一次捕获曾因默认配置探测已采用 embedding 服务而长时间等待网络；排查确认没有 API key 时仍会发未认证探测。按“embedding 不可用整次回退 Jaccard”的既有质量合同，`embedding.py` 现在在缺少配置声明的 embedding key 时直接返回 `embedding_api_key_missing`/Jaccard，不发网络请求；新增回归证明 adopted artifact 且缺 key 时不会构造 client。没有改变有 key 时的真实 provider 路径或 Task 2-B 语义合同。
- 修复后的 focused 回归：`193 passed`；随后当前树全量：`uv run --frozen pytest -q && git diff --check`，exit `0`，`507 passed, 3 skipped`。
- 按 WorkflowHub 快照绑定规则，先把 `verify-code-test-capture-v42.json` 和 `verify-code-run-v42.json` 放入当前工作区，再执行 canonical test capture。receipt=`quality/tests/verify-code-final-full-20260811-v42.json`，receipt_hash=`e5901f140c3f0f57cf19214acf689eb3a0ed46c72d0cc226b77307c08bb7f36a`，snapshot_tree=`b9951e43fe35d70664df3d153d34202a3ef9ffe2`，output_hash=`df7a618980774e6acf0f4614d89acb7c6a883a6c0cfe6665a6ec0df8ec0cacb3`，exit `0`。
- 官方 verify-code 已用 v42 receipt、既有一次 build-code review、既有一次 verify-code 异源审查 attempt、finding dispositions、语义 evidence 和 verification receipt 执行一次；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。最新 quality facts：tests=`quality/facts/8c11371aff04e060596d31e7db7d5f8aa16872485b12317b674b2c8bdef340e0.json`；finding dispositions=`quality/facts/6657dada7fd81171a1460d0de0ef19254719daf6a6e850319125d8bef27cfdd2.json`。
- 官方仍明确保留：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review` 因 provider reviewer JSON 非法而 `missing`；`AC-09/AC-10/AC-11` 真实语义证据不闭合而 `acceptance_criteria=missing`；`exceptions=missing`；`human_confirmation=missing`。T013 v23 仍是最近一次完整真实语义结果，`2` 个 module machine-passing concepts、delivery=`not_released`；不把 `507` 个测试通过写成语义出口通过，也没有调用 `close`。

### Phase Card — Phase 2：typed provider prompt compaction（2026-08-12）

- **goal**：在不改 page type、section、Claim/Evidence、预算、阈值或失败状态合同的前提下，解决长 typed 请求因重复发送原文而把 provider JSON 截断的问题。
- **allowed files/symbols**：`src/knowledge_digest/llm.py` 的 `_typed_source_outline`、`_TYPED_BODY_RULES`、`build_prompt`；`tests/acceptance/test_task2b_body_compiler.py` 的 typed prompt 回归；本阶段 evidence。
- **covered AC**：AC-02、AC-03、AC-04、AC-07、AC-09、AC-10、AC-11；影响闭包仍由 deterministic Claim、section gate 和 Evidence 保证。
- **non-goals**：不换 provider/model，不增加 `max_tokens`，不降低语义门，不拆 typed page 请求，不改变旧 section 复用/失效规则，不把 provider 返回变成发布通过。
- **route**：实际边界为 Python publication pipeline 的单功能域行为变化，选 `feature` + `backend-testing`；浏览器 QA 不适用。
- **stop conditions**：Claim 文本或来源 lineage 丢失、结构提示混入事实证据、provider JSON 仍截断、或 semantic evidence 仍缺字段时，保持 `unknown/incomplete/not_released`，不补占位结论。
- **expected handoff**：focused/consumer/full tests、真实 T013 结果和一次当前 Phase review；review unavailable 仍如实记录，不循环追求 pass。

### T014 最终聚合回归追加事实（2026-08-11）

- 按 T014 原始聚合命令，在当前 worktree、当前 T013 证据路径和无 provider 网络依赖环境下重新执行：`semantic_evidence_file` focused test=`1 passed, 67 deselected`；Task 2-B、Task 2 publication、batch recovery、corpus regression、Task 2-A Reader Bundle/frontmatter/OKF smoke aggregate=`150 passed, 2 skipped`，exit `0`。
- 直接验证最新完成的 `apply/evidence/T013.semantic-run-v23.json`：`valid=false`、`machine_exit_passed=false`、`reader_eligible=false`、`delivery_status=not_released`；原因是 machine-passing concept 少于 6，缺 `product_overview` 和 `procedure_or_rule`。因此 T014 的回归证据完成，但 T013 语义出口仍保持 `incomplete`，不把聚合绿灯解释成 Task 2-B 通过。

### T013 procedure 来源审计追加事实（2026-08-11）

- 回读冻结 Task 1 证据：`example-004` 的 `17 智能搭建` 主题是 `merge_mode=single`，唯一 source member=`source-520b6110d7a4abd4dd8b`，唯一来源 URI=`raw://confluence/GoInsight/17  智能搭建.md`；source content fingerprint=`f13a606b8e3905db2b0cf5ae94d8e61f0ae79b0f26cfba02074b61986ec6e96f`，与本机原始文件 SHA-256 一致。
- 对冻结原始目录按主题名和异常/错误处理关键词检索后，未找到同一主题的第二份来源。该 41 行来源只有三种方案、优缺点、影响范围和“信息不足/错误可交互补充”的比较描述，没有具体的异常触发条件、处理步骤、分支规则或恢复动作；其他命中“异常/失败”的 GoInsight 文档属于不同主题，不能跨主题拼接成该页 Claim。
- 因此当前 `procedure_or_rule.exceptions` 缺口是冻结源材料缺失，不是 provider mapping 或正文 gate 可以安全修复的代码 bug。继续保持 fail-closed：不把“缺点”映射成 `exceptions`，不写“暂无异常”占位，不改 page type/required section；T013 仍为 `unknown/incomplete`、delivery=`not_released`。若要改变该结论，必须先回到 `make-decision` 确认契约或补入新的已声明来源。

## Scope revision addendum：SR-20260811-task2b-procedure-source-gap

### SR 状态与边界

- **状态**：`in_progress`；这是同一 Task 2-B 的 bounded scope revision，不创建 successor task，不重置 T001–T014，也不重新走完整 `make-decision → build-spec → build-plan`。
- **触发阶段 / 返回阶段**：`verify-code` → `build-code`。
- **原始需求**：冻结的 `procedure_or_rule` 来源没有明确异常触发、处理、分支或恢复规则；不能为了补齐正文编造异常内容，也不能让受影响 section 残留过期说法。
- **已选规则**：保留固定 `exceptions` section；确定性来源审计证明没有异常规则时使用 section-level `source_not_documented`；不生成异常 Claim、不写“暂无异常”等占位句、不跨主题拼接；异常专属问题为 `not_answerable`。其他 section 和既有机器门通过时，页面可 `published` 并计入 `procedure_or_rule` 覆盖。
- **失败边界**：来源含糊、审计不完整、source binding 缺失、provider 映射失败、归因/保真/版本/重复等既有机器门失败，仍为 `degraded` 或交付 `not_released`，不得降级为 `source_not_documented`。
- **不变项**：三类 page type、固定 section 清单、页级状态、交付状态、`>=6`、三类覆盖、inventory coverage、旧 Reader 保护、Task 2-C/Task 3 非目标不变；contract revision 已为 `1/1`。
- **WorkflowHub 事实**：当前主分支没有可执行的独立 `scope_revision` review 路由；缺失专用审查记录为 `missing/incomplete`。已有 C1 detail review 不冒充 SR review，不重复阶段审查；这不阻塞本次同任务材料修订和 build-code 交接。

### 受影响闭包

- **需求/规格**：`PFACT-007`、`FR-DRAFT-004`、`FR-PUBLISH-006`、`FR-SEM-003`、`AC-13`，以及消费该 section 的 `FR-DRAFT-001`、`FR-PUBLISH-002`、`AC-02`、`AC-07`、`AC-09`、`AC-11`。
- **计划/任务**：`DEC-005`、`T009`、`T010`、`T015`、`T016`、`ORACLE-T2B-SOURCE-GAP-SECTION`、`ORACLE-T2B-SEMANTIC-RUN`。
- **实现/测试**：仅评估并按实际 seam 修改 `src/knowledge_digest/draft.py`、`src/knowledge_digest/publication.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/llm.py` 及 `tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`。若发现 page layout/navigation 也消费该状态，必须补兼容断言；不能凭猜测扩大改动。
- **交付/证据**：更新 `apply/evidence/` 中本 SR 的 focused 行为证据和后续真实语义/聚合证据；旧 Reader 正式页不覆盖，缺失 provider 或样本证据记 `incomplete/not_released`。

### T015 — RED/GREEN：来源缺口 section 状态与旧说法失效

- **ID**：T015
- **Phase**：SR-20260811 bounded build-code repair
- **goal**：在不新增 page type 或页级状态的前提下，让确定性来源审计可产生 `exceptions=source_not_documented`，并证明其不生成异常 Claim、不写占位句、不跨主题推导；同时证明来源变化或审计不确定时受影响 section 不复用旧正文，必要时整页 `degraded`。
- **status**：`pending`
- **RED/GREEN**：先写可区分目标行为的正例和负例；RED 不能只是 fixture/setup 失败。GREEN 只实现本 SR 规则，不降低既有正文、保真、版本、归因、重复和发布门。
- **required cases**：冻结 `17 智能搭建` 单来源缺口正例；有明确异常规则的 `documented` 正例；来源含糊/审计不完整/缺 fingerprint/跨主题命中/旧 dependency 不一致负例；异常题 `not_answerable`；其他 section 可用且机器门通过时页级 eligible/published 的组合断言。
- **evidence**：focused test exit、oracle、输入 fingerprint、audit version、source URI/locator、section status、claim mapping、旧 section bytes/失效理由，写入 task-relative `apply/evidence/`。
- **STOP**：若实现必须改固定 section、page type、页级/交付状态、机器阈值、CLI、Reader Bundle 或需要新增产品决策，停止并回报，不在 T015 内补需求。

### T016 — 证据重跑与回归交接

- **ID**：T016
- **Phase**：SR-20260811 bounded verify handoff
- **goal**：用 T015 的当前代码和当前四份材料重新捕获受影响 focused 回归；然后按既有 T013/T014 规则重跑或验证真实语义证据，明确 `source_not_documented` 是否只改善受影响 section，不把部分通过写成 Task 2-B 完成。
- **status**：`pending`
- **preconditions**：T015 GREEN；当前测试 capture；冻结样本 manifest、provider/model/detector/budget/threshold、answerability 和 section dependency v1 事实可回读。缺任一项时记录 `incomplete/not_released`，不换 provider、不降阈值、不编造证据。
- **required assertions**：`procedure_or_rule` 的异常题仍 `not_answerable`；同页其他 section 不被误伤；旧受影响 section 无过期正文残留；既有 `>=6`、三类 page type、inventory、provenance/faithfulness/version/duplicate 和交付边界不变；真实语义结果按真实值记录。
- **evidence**：`apply/evidence/SR-20260811...` 下 focused test、semantic evidence/validator、aggregate regression、provider identity 和失败原因；如需官方 verify-code，只执行一次当前材料绑定的普通阶段验证，不重复异源审查，不调用 `close`。
- **handoff**：T016 完成后回到 `verify-code`；独立 SR review 仍 `missing/incomplete`，人工确认仍单独记录，不以测试绿灯或 section 通过替代。

### SR 执行顺序

不重跑已完成的 T001–T014：先 `T015 RED → T015 GREEN`，再 `T016` focused/semantic/aggregate evidence；若超出本 addendum，停止并回到当前材料，而不是继续隐式扩 scope。

### T015 执行事实（2026-08-11）

- **status**：`completed`。
- **实现**：`publication.py` 增加 `procedure-exceptions-audit.v1` 的确定性来源审计；`draft.py` 把可信审计绑定到 `exceptions` section dependency；`llm.py` 只允许可信 `source_not_documented` section 为空且无 Claim；`pipeline.py` 把 section 状态送入 body gate、机器概念和 answerability；语义 evidence 的 contract revision/AC binding 已更新为 `1/1`、`AC-13`。
- **focused evidence**：`apply/evidence/SR-20260811-source-gap-section-focused.txt`；Task 2-B focused=`72 passed`，consumer regression=`164 passed`，full regression=`511 passed, 3 skipped`，`git diff --check`=`0`。
- **正例**：冻结来源只有错误/信息不足描述，没有明确异常触发、处理、分支或恢复规则时，`exceptions` 保留但状态为 `source_not_documented`，绑定 source URI/content hash/locator/audit version，异常题为 `not_answerable`，其他 section 可继续进入页级机器门。
- **负例**：有明确异常处理规则、来源绑定不完整、provider 在特殊 section 写正文或 Claim 时均不使用特殊状态并保持 fail-closed。
- **旧说法保护**：特殊 section 不携带 Reader body/Claim；来源审计依赖进入 section dependency，来源变化或无法证明时不能安全复用旧 section。

### T016 当前交接（2026-08-11）

- **status**：`pending`。
- **next**：回到 `verify-code` 前，先基于当前四份材料重新 capture T013/T014 相关证据；真实 provider、样本、detector、budget、threshold 缺失时记录 `incomplete/not_released`，不以 focused/full tests 冒充语义出口。
- **review boundary**：不重复既有异源审查；当前主分支没有独立 `scope_revision` review 路由，该缺失保持 `missing/incomplete`；不调用 `close`。
- **preflight fact**：当前进程缺少冻结 T013 所需的 provider、sample input/KB、semantic config、LLM format 和新 evidence path 环境变量；没有生成新的语义 evidence。旧 v23 evidence 重新校验为 `valid=false`、`machine_exit_passed=false`、`delivery_status=not_released`，且缺 `AC-13` binding。
- **evidence**：`apply/evidence/SR-20260811-T016-preflight.txt`；T016 保持 `incomplete/not_released`，等待冻结输入，不替换样本/provider/阈值。

### T016 执行事实追加（2026-08-11）

- 按当前四份材料重新执行 WorkflowHub 普通 `verify-code` 路由；没有调用不存在的独立 `scope_revision` 路由，也没有重复异源审查或调用 `close`。
- 当前树的 canonical test capture：`uv run --frozen pytest -q && git diff --check`，exit `0`；receipt=`quality/tests/verify-code-final-full-20260811-sr4.json`，receipt_hash=`29534111158dfdfba10f4f18f5e791b2ba8cdeae231f44859a07f065ad02befd`，snapshot_tree=`f0290c8087ef193c5cc2006206d20d0c6fab28c6`，output_hash=`faf049e55ccef7b7da40c83bf84cd7580c5037bcc43bc01823d4b1ec1626ee0a`。
- 官方 verify-code 结果：`stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`（既有 provider 输出为 `OUTPUT_INVALID`，不改写成 pass）；`acceptance_criteria=missing`（旧 AC evidence 缺 `AC-13`，且 AC-09/10/11 仍为失败/不完整）；`exceptions=missing`；`human_confirmation=missing`。最新普通阶段绑定的 WorkflowHub quality facts：tests=`quality/facts/a919e1bcc549da320c662a72abe93217833aaf9e840c05f1e3e49930871c9f54.json`，finding dispositions=`quality/facts/b8db2d1074bc2bcc0f17b5546f2403e0a79ef8f7e0c6e69059433225beede684.json`。
- T013 仍没有合法冻结的 sample input/KB、semantic config、provider identity、detector、budget、threshold 和新 evidence path；没有生成新的真实语义 evidence。旧 v23 继续为 `valid=false`、`machine_exit_passed=false`、`delivery_status=not_released`，不能替代本次运行。
- 因上述事实，T016 不标记完成，Task 2-B 不宣称完成或 released；回交 `verify-code` 前保持 `incomplete/not_released`，等待补齐冻结运行输入、有效异源审查事实和独立的人类确认。

### Phase 1 build-code 标准执行事实（2026-08-11）

- `test-routing-advisor` 基于实际改动重新判定为 `feature`，选择一次 `backend-testing`；此前材料中的 `fullstack` 是过宽的历史记录，不能覆盖当前 Python 本地 publication pipeline 的真实边界。
- 已按该路由执行 Phase 1 功能回归：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2_publication.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2a_reader_frontmatter.py tests/acceptance/test_task2a_okf_smoke.py tests/acceptance/test_phase25_llm.py tests/acceptance/test_phase4_embedding_runtime.py -q`，exit `0`，`259 passed, 2 skipped`；receipt=`quality/tests/build-code-phase1-feature-20260811.json`，receipt_hash=`bca6966ee98e2ead1293a7dbcc8b4ad2bad4a83fdfaab8f4f16a3c844bdcb4b9`，snapshot=`f33d0fe8911978bc7840b91f9d3922d3a3579258`；`git diff --check` exit `0`。
- 浏览器 QA 不适用；本 Phase 没有 UI、外部服务或浏览器流程。真实 T013 语义运行仍是 `unknown/incomplete`，不能用本次结构/功能回归替代。
- 已对当前 `phase-1` 执行一次正式异源 `build-code` 审查，attempt=`quality/reviews/attempts/ba26ee80-1ce8-4bc9-8973-881c34a5960b/attempt.json`，report=`quality/reviews/reports/ba26ee80-1ce8-4bc9-8973-881c34a5960b.md`，material=`0d6fff9f18580f51bc52357543e4049146bb50af52a8547a3f5bbaf879add39b`；审查材料已经通过 330 KiB 传输限制并绑定当前 snapshot，但最终 `unavailable`：`opencode/v4flash` 超时、`kimi/coding` 进程无进度后终止、`codex/luna` 同源排除。
- 因审查没有有效 reviewer JSON，finding 状态必须记为 `unknown`；不把“没有 adjudicated findings”说成“没有严重 findings”。按 WorkflowHub 规则，审查不可用不阻塞同一任务继续修复，但 Phase 质量仍是 `incomplete`，不能宣称已通过或 released。完整事实见 `apply/evidence/build-code-phase1-routing-and-review-20260811.json`。
- Phase 1 的实现和测试动作已完成；T013/T014/T016 的语义证据、独立审查和人类确认仍未闭合。下一步进入一次 `verify-code`，反向检查原始需求、Design、完整用户流程、成功/失败/恢复边界、非目标和延期项；所有缺证据继续标 `unknown`，close 前停下，不调用 `close`。

### Verify-code 当前验收事实（2026-08-11）

- 已完成一次架构师反向检查：原始需求 → 当前 decision-log → `spec.md` → `plan.md`/`tasks.md` → 入口、成功、失败、恢复和 `source_not_documented` 特殊分支 → AC → 当前测试/证据。没有新增产品需求或代码修复；架构结论写入 `apply/evidence/verify-code-architect-assessment-20260811.json`。
- 当前适用 AC 结论：AC-02、AC-06、AC-08 为自动化行为测试范围内的 `pass`；AC-01、AC-03、AC-04、AC-05、AC-07、AC-09、AC-10、AC-11、AC-12、AC-13 均因 evidence、测量记录或真实语义运行缺失保持 `unknown/incomplete`；AC-04 明确没有把缺少分母/检测器版本/seed/失败样本的摘要当成通过。
- 当前最终测试曾执行 `uv run --frozen pytest -q -rs`，exit `0`，`511 passed, 3 skipped`。三个 skip 已记录具体测试和原因：Task 1 外部 89-source corpus 未设置；两个可选 Task1/Task2/CompanyBrain corpus fixture 不在 checkout。`git diff --check` exit `0`。详细摘要见 `apply/evidence/verify-code-final-test-summary-20260811.json`。
- 已执行 verify-code 唯一一次异源架构复核：attempt=`quality/reviews/attempts/bbfbfaa4-d85c-445e-b514-0eacfaf53778/attempt.json`，result=`quality/reviews/results/verify-code-default-77c051128229589f50cae0da72191ad920c6f806-bbfbfaa4-d85c-445e-b514-0eacfaf53778.json`，report=`quality/reviews/reports/bbfbfaa4-d85c-445e-b514-0eacfaf53778.md`；`opencode/v4flash` 返回 1 个 major、2 个 minor，`antigravity/opus` authentication failure，`codex/luna` same-source 排除。
- finding 处置：major `F-a3484cf00ad5` 已修复为 AC-04 `unknown`，不伪造规格要求的门控测量；minor `F-887d33bac044` 已将 evidence 型 AC 从 pass 收紧为 unknown；minor `F-9cb127a17ac0` 已补写三个 skip 的身份和原因。没有代码变化，因此不重跑 provider review；按 verify-code 规则只做最终测试和收尾。
- 当前 verify-code 质量结论必须是 `incomplete`：测试绿灯，但独立 build-code review unavailable、AC-04 等证据不闭合、T013/T014/T016 真实语义出口和 human confirmation 缺失，交付保持 `not_released`。close 前停止，不调用 `close`、不提交、不合并。

### SR-20260811 T013/T014/T016 当前执行事实追加（2026-08-11）

- 发现 `apply/evidence/T013.semantic-run.json` 原有一份未绑定本次 scope revision 的旧结果：`contract_revision=0`、缺 `AC-13`；已保留原始内容并移动为 `apply/evidence/T013.semantic-run-pre-scope-revision-20260811.json`，没有覆盖历史证据。
- 按冻结 sample manifest 重建隔离输入：20 个 frozen examples 对应 30 条 source notes；来源正文来自本机外部 Task 0 source-snapshot bundle，未写入正式知识库。普通 `digest` 运行使用 qwen3.6、环境变量凭据、同一 sample manifest 和当前 scope revision；embedding 探针使用 3 秒边界，失败后明确回退 Jaccard，不把回退算作语义通过。
- 新 T013 运行：run_id=`run-37095bf59935497985137ca79722f7e6`，`run_status=completed`、`execution_mode=real_semantic`、`delivery_status=not_released`；证据=`apply/evidence/T013.semantic-run.json`，sha256=`b05d2aa0d7e965b7046a751e00ceec4e94df0dd83392e5653aae28b358edd36c`。
- 新证据已绑定 `contract_revision=1/1`、scope revision ledger、`AC-01/03/05/07/09/10/11/12/13`，并记录 20 个问题的逐题 answerability/first-hit。provider 每次请求 5 秒硬超时；真实结果为 `machine-passing concepts=0`、`evidence_backtrace=0`、`section_completeness=0`，全部问题没有 first hit，失败原因保留为 provider timeout、semantic backtrace unavailable、TopicIndex mapping degraded 和非法版本；不把它解释成语义通过。
- T013 evidence-file gate：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_evidence_file`，exit `0`，`1 passed, 71 deselected`。这证明证据身份/字段合同成立，不证明语义出口通过。
- T014 当前聚合：Task 2-B、Task 2 publication、batch recovery、corpus regression、Task 2-A Reader Bundle/frontmatter/OKF smoke 共 `154 passed, 2 skipped`，exit `0`；完整事实见 `apply/evidence/SR-20260811-T016-final-regression-v2.txt`。
- 当前全仓回归：`uv run --frozen pytest -q`，exit `0`，`511 passed, 3 skipped`；`git diff --check` exit `0`。测试通过只说明代码和兼容回归通过，不能替代真实语义出口、独立审查或人工确认。
- **T016 执行状态**：`completed`（当前 scope revision 的 focused/semantic/aggregate evidence 已完成并回交 verify-code）；Task 2-B 仍为 `incomplete/not_released`。后续只执行一次当前材料绑定的普通 `verify-code` 收敛，不重复异源审查、不调用 `close`。

### Verify-code SR 当前官方收敛结果（2026-08-11）

- 已用当前四份材料、当前 T013 真实语义 evidence、T014 聚合回归和 fresh test receipt `quality/tests/verify-code-final-full-20260811-sr5.json` 执行一次普通 WorkflowHub `verify-code`；没有重复异源审查，没有调用 `close`。
- 官方结果：`stage=in_progress`、`work_status=ready`、`quality_status=incomplete`；`full_tests_fresh=satisfied`、`independent_review=satisfied`、`finding_dispositions=satisfied`；`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。
- 本次 fresh test receipt：receipt_hash=`e5dbb0e3873208b1687b4eb2b8b2c684a96661ebc2c4090f74f72051ec8d69c3`，snapshot_tree=`6922901e6b6a99a049e98f42ad18bef483693978`，output_hash=`ebaadc1fecc584ce855d89e0cd8656256c34ac772fdcbfa47a72f59d63b9c0e4`；命令 `uv run --frozen pytest -q -rs && git diff --check`，`511 passed, 3 skipped`，三个 skip 的身份和原因已由命令输出记录。
- 官方 warnings 保留：当前 verify acceptance evidence criterion set 与现行 AC 不一致；AC-09/10/11 的真实样本、provider 语义和机器出口仍 `unknown/incomplete`；三类 page type、answerability、完整 backtrace 和 `>=6` machine-passing concepts 仍缺失；delivery=`not_released`；build-code integration review 不可用；尚未取得 human confirmation。
- 最新 WorkflowHub quality facts：tests=`quality/facts/67005292e8f6c8f5adad2a8f0689c61e294db48dbcbba12479014da28f297de8.json`；independent review=`quality/facts/05af1d830147044549512469a96a48a3c796613f139ca610b3219d66cf18e368.json`；finding dispositions=`quality/facts/19fed23b4fb0ea260835b997e05f25832e2c7c1eec4bfd7f223dabcfdb3105df.json`。
- 当前动作完成：已反向检查原始需求、Design、完整用户流程和所有成功/失败/恢复边界；缺证据均保持 `unknown/incomplete`。按用户要求在 `close` 前停下，不提交、不合并、不调用 `close`。

### T013 provider 连通性诊断追加事实（2026-08-11）

- 对用户指定的 qwen3.6 endpoint 做了最小 OpenAI-compatible JSON 请求诊断；请求字段与 `src/knowledge_digest/llm.py` 当前合同一致，未更换 provider、模型或门槛。
- 默认网络路径和显式直连均在 20 秒内连接超时：`curl exit=28`、HTTP status=`000`、response body=`0 bytes`。证据见 `apply/evidence/T013.provider-connectivity-20260811.txt`。
- 结论：T013 当前首先被外部 provider 连通性阻塞；这不是可通过放宽正文/语义门修复的代码问题。继续保持 `unknown/incomplete`、`not_released`，不把超时伪装成 provider 失败后的语义通过，也不调用 `close`。

### Verify-code provider 诊断后的最终收敛（2026-08-11）

- provider 连通性诊断证据已纳入当前材料；重新捕获 fresh test receipt：`quality/tests/verify-code-final-full-20260811-sr6.json`，receipt_hash=`d04c617e0d012f30e5962a5c60e75d542ce1bb5ab23124ab447163eee94e940c`，snapshot_tree=`c1031515113790d01ef75254139d19c0ce030bcf`，output_hash=`f3ea217269c0c5bd2817f43cc73f089442ce2567fe6a5b8735e9839d11d273df`；`511 passed, 3 skipped`，`git diff --check` 通过。
- 已用 sr6 receipt、当前 T013 evidence、既有 review/finding dispositions 执行一次当前材料绑定的普通 WorkflowHub `verify-code`；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。
- 官方 predicates：`full_tests_fresh=satisfied`、`independent_review=satisfied`、`finding_dispositions=satisfied`；`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。
- 最新 quality facts：tests=`quality/facts/660a306f5a11c4b5fd2a8fd186d88d4b5ad1ff0618ec7e0549dc7874fa40cef9.json`；independent review=`quality/facts/4ca9e9a16257f35f292c3747bb36d9844965189424b2c73787610d10212e9bc0.json`；finding dispositions=`quality/facts/db42edc17c65271cf44111256f5374b9427a783e8f0bdf4e0f987569db25edfe.json`。
- 官方仍保留：AC-09/10/11 语义证据不闭合、三类 page type/answerability/backtrace/`>=6` machine-passing concepts 缺失、build-code integration review unavailable、human confirmation 缺失；交付保持 `not_released`。本轮没有重复异源审查，没有调用 `close`。

### Phase 2 后当前 verify-code 收敛事实（2026-08-12）

- 当前完整测试命令：`uv run --frozen pytest -q && git diff --check`，exit=`0`，`512 passed, 3 skipped`。最新 receipt=`quality/tests/verify-code-final-full-20260812-phase2-v4.json`，receipt_hash=`ac3dca16b82d988d2ffd6b22c3101efcd2850446326cdb5380a5ad88ed62fc5e`，snapshot_tree=`8ea4e60f694e32cfd49dd8cf441a369e3a4da1ec`，output_hash=`a0006db1a2e6afe09ca78f57dec9a64db4cd991897fa8f80d000a972dab78aa3`。
- 已按当前四份材料和最新测试 receipt 执行一次官方 `verify-code`；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。质量事实：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`、`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。fact refs：tests=`quality/facts/038a2f8fa7266f79f86be5777d785ed0228f81607187ca1c8869b1ccdcedd3e2.json`；finding dispositions=`quality/facts/75c504fde97afccec279e9fe76458d7a49cadb9e8a2ad9e02219742b809f98c6.json`。
- verify-code 的具体未满足项已保留：当前 AC evidence criterion set 与 spec 不一致；`verify-ac-09-v6.json`、`verify-ac-10-v6.json`、`verify-ac-11-v6.json` 仍是失败/不完整证据；provider 输出有非法 JSON、未受信 Claim ID 和保真失败；独立审查同时保留 Phase 2 的 `MATERIAL_INCOMPLETE` 与既有 verify review 的 `OUTPUT_INVALID`，不把 unavailable 或“无 findings”改写成通过。
- 本轮没有重复异源审查，没有再次改 provider/model/预算/阈值，没有调用 `close`。Task 2-B 当前仍为 `incomplete/not_released`；下一步只能在补齐真实语义出口、有效审查证据和用户确认后再谈交付，不能用 `512 passed` 替代这些条件。

### Phase 2 build-code 执行事实：typed prompt compaction（2026-08-12）

- 实现范围严格限于 Phase Card：`llm.py` 将重复的完整 `source_text` 收敛为结构性 `source_outline`，保留完整 trusted Claim/lineage；没有修改 provider、model、`max_tokens=8192`、阈值、page type、section 合同或失败状态。
- RED/GREEN：新增的长提示词回归先因仍存在 `source_text` 而失败，修复后 focused typed prompt=`2 passed, 71 deselected`；Task 2-B 全套=`73 passed`；相邻 publication/batch/corpus/Task 2-A/LLM/embedding 回归=`187 passed, 2 skipped`。`git diff --check` 待本条材料落盘后重新执行。
- 官方测试 capture：receipt=`quality/tests/build-code-phase2-feature-20260812.json`，receipt_hash=`61becab4b56df3d36798badfec0404c14369ee6920c11d83a96c88591aac3c7f`，output_hash=`5327c77c9b1025559f2c56c40a6ab881c5202fb0090813f9fc6a8a753ed4d328`，snapshot_tree=`b4994052ecade0823fe4f1f421d782a257b16e5a`，exit=`0`。直接 provider smoke 使用同一 qwen3.6 请求合同返回 HTTP 200、合法 JSON、`finish_reason=stop`，说明提示词长度/截断问题有实测改善，但不等于完整语义出口通过。
- T013 正确冻结重跑：同一 manifest（sample=`20`、source=`89`、hash=`fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f`）、qwen3.6、15/15 provider calls、`max_tokens=8192`；run_id=`run-768346c90c5f4717beeb1bab7877a031`，evidence=`apply/evidence/T013.semantic-run-20260812-compact.json`，sha256=`7e6d2a2947bd3a3460811b8318389c1e12ea5fbdf516d8d6af297c8baad89d65`，`run_status=completed`、`delivery_status=not_released`。结果为 `0` machine-passing concepts、`0` evidence backtrace、所有问题 `answerable=false`；失败事实保留：2 个 provider claim id 不在 trusted input、2 个输出为非法/截断 JSON、空 `entry_prerequisites`、多项 token/faithfulness mismatch、TopicIndex degraded、版本不符合规则。
- embedding 端点单独直连可返回 HTTP 200 和 1024 维向量；但本次 T013 使用明确的 `KD_EMBEDDING_TIMEOUT_SECONDS=3`，探针失败后整次按既有合同回退 Jaccard，记录为 degraded，不把它伪装成 embedding 通过。第一次未设短超时的尝试因客户端默认 180 秒等待而停止，未作为成功证据。
- 本 Phase 只执行一次官方异源审查：attempt=`quality/reviews/attempts/9887ef3f-ee23-48eb-889c-8da9b230445a/attempt.json`，report=`quality/reviews/reports/9887ef3f-ee23-48eb-889c-8da9b230445a.md`；结果 `unavailable`，原因是 review packet 超过 330 KiB（`MATERIAL_INCOMPLETE`），provider 没有被调度，不能写成“无严重发现”。按既定规则不循环重审；Phase 2 质量保持 `incomplete`，但不阻塞同任务继续。
- 当前交接：prompt compaction 的代码和回归动作完成；T013 仍 `incomplete/not_released`。下一步只基于本条更新后的当前材料重新 capture 测试并进入一次 `verify-code` 反向检查；不降低门槛、不换 provider、不调用 `close`。

### Phase 2 build-code 异源审查事实：bounded packet（2026-08-12）

- 按用户约定，Phase 2 只执行一次异源审查；本次先把审查范围收窄到本 Phase 的两个实际改动文件 `src/knowledge_digest/llm.py` 和 `tests/acceptance/test_task2b_body_compiler.py`，其余变更通过 `phase_map`、`impact_map`、`reuse_map` 和 `acceptance_map` 标记为 out-of-phase；审查包大小 `235890` bytes，material=`66ae64dc84d6ffb9d77491cb03a4f8b5a79f425e9fb155e5d26517d51138f2a5`，snapshot=`95b3344e0d4653a9476dd796d65b8209968a9951`。
- 正式审查 attempt=`quality/reviews/attempts/46a34cd0-c5e6-4e65-ae06-575310644579/attempt.json`，report=`quality/reviews/reports/46a34cd0-c5e6-4e65-ae06-575310644579.md`；terminal=`unavailable`，有效 reviewer=`0/1`。`opencode/v4flash` 返回 `OUTPUT_INVALID`（不是协议要求的 reviewer JSON）；`pi/coding` 返回 `PROCESS_EXIT_NONZERO`；`codex/luna` 因同源被排除。报告中没有可采信、可处置的异源 finding。
- 以上是审查不可用，不是“没有严重问题”或审查通过。provider 的原始非协议输出不纳入 finding，不据此改代码；本阶段不重复审查。Phase 2 的独立审查质量事实保持 `unknown/incomplete`，交接给一次 `verify-code` 反向检查。
- 本 Phase 当前完整测试仍以 `quality/tests/build-code-phase2-current-20260812.json` 为准：`uv run --frozen pytest -q && git diff --check`，exit=`0`，`512 passed, 3 skipped`；审查材料追加后需重新 capture 当前树，不能复用旧 snapshot 宣称最终通过。

### Verify-code 当前官方收敛事实：Phase 2 bounded review 后（2026-08-12）

- 已重新 capture 当前树并执行最终命令：`uv run --frozen pytest -q && git diff --check`，exit=`0`，`512 passed, 3 skipped`。receipt=`quality/tests/verify-code-final-full-20260812-phase2-v7.json`，receipt_hash=`a7e8fe0616529f4847344a4b58e972af0d01945525c6a3eee7906c5bdf83d1cf`，snapshot_tree=`b33e6a0995453dd75286d58c0aaae4638b3ec43a`，output_hash=`b117f0d3c5b12d2389ae53ee07f40638134f33ea25727c91d1c584d7b251a400`。
- 已执行一次官方 `verify-code`，输入=`apply/evidence/verify-code-run-input-20260812-phase2-v5.json`；结果为 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。官方 predicates：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`、`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。
- 当前 quality facts：tests=`quality/facts/65bc724a42ae08a2068e734890ffa551f225b584315378f87d68c02e89283066.json`；finding dispositions=`quality/facts/826c21e62480f732ca1c829ef5f9d931c45aff03d44f87cc6b480ed2120a6c01.json`；官方结果还记录 build-code/verify-code 两次 review 的 `OUTPUT_INVALID`、AC-09/10/11 failed、当前 spec 与 acceptance evidence criterion set 不一致、T013 语义出口未闭合。
- 当前 verification receipt=`quality/evidence/verification-v9.json`，已按最终 capture 的 `snapshot_tree` 绑定；它明确把独立审查、AC、核心缺口和人类交接保留为 `unknown/incomplete`，没有把 512 条测试通过改写成产品通过。
- 本轮没有 provider 重试、没有改 provider/model/预算/阈值、没有新增代码修复，也没有调用 `close`。Task 2-B 仍保持 `incomplete/not_released`；下一步等待补齐真实语义出口、有效异源审查证据和用户确认。

### T016 provider claim reference 修复追加事实（2026-08-12）

- 真实失败根因已做最小修复：typed provider 之前必须回写 64 字符的 `claim_fingerprint`，当前真实 T013 compact 结果已记录 2 个不在 trusted input 的 claim id；现在 prompt 给 provider 稳定短引用 `c001`、`c002`，validator 在进入依赖、保真和发布门前确定性映射回 trusted `claim_id`/`claim_fingerprint`。不改变固定 page type、section、来源/Evidence、机器阈值、失败状态或 legacy prompt。
- 按实际 changed files 重新判定测试路由为 `feature` + 一次 `backend-testing`；浏览器 QA 不适用。RED 命令先真实失败 1 个目标断言（缺 `provider_claim_ref`，不是 setup error），GREEN focused/consumer=`166 passed`；全量 `uv run --frozen pytest -q && git diff --check`=`513 passed, 3 skipped`，exit=`0`。
- 当前 canonical receipt=`quality/tests/build-code-phase2-claim-ref-20260812.json`，receipt_hash=`0180a3d984e8b8ed4e41e448de6fda7f5d599df2c9de5da68ad860b670220fda`，snapshot_tree=`c56f6885302541d39dfb83676b69e98eb62d5061`，output_hash=`ddb11d6dc3356fd063e67729c4da9e97716691e9e60f39dc243e72168d1b8e98`；详细事实=`apply/evidence/T016.provider-claim-ref-repair-20260812.txt`。
- Phase 2 异源审查已经按用户约定只执行一次；既有 attempt=`quality/reviews/attempts/46a34cd0-c5e6-4e65-ae06-575310644579/attempt.json` 在本修复前因 `opencode/v4flash=OUTPUT_INVALID`、`pi/coding=PROCESS_EXIT_NONZERO`、`codex/luna=SAME_SOURCE` 不可用。本修复不重复审查；因此独立审查质量继续为 `incomplete/unknown`，不能说“没有严重 findings”。
- 这次只完成 provider 引用映射的确定性修复和回归；当前进程没有 provider 凭据环境，未声称 fresh T013 语义运行。最新可用真实语义 evidence 仍是修复前的 `T013.semantic-run-20260812-compact.json`，`0` machine-passing concepts、`0` backtrace、`not_released`，不能替代修复后的语义结果。T016 继续 `incomplete/not_released`，下一步是基于当前材料重新捕获并执行一次普通 `verify-code`，close 前停下。

### T016 当前材料 receipt 重绑定追加事实（2026-08-12）

- 上一份 claim-ref receipt 在 append-only task fact 写入前捕获，不能覆盖当前材料快照；已重新捕获当前树。权威 receipt=`quality/tests/build-code-phase2-claim-ref-20260812-v2.json`，receipt_hash=`cdf56b3ab6d137335e4aa9b61510c7a53f2f85c20a8e862b1760acf9f1ed85d7`，snapshot_tree=`d2caf22a65d8711614519eeba7c845fa1d239f7e`，output_hash=`f484acde012f3a947c06f5eb576012ac36203f081eb709523a28b1e82ace1db8`，exit=`0`。
- v2 仍只证明当前代码/测试回归通过，不能替代修复后的真实语义运行、独立审查或用户确认；T016 和 Task 2-B 继续 `incomplete/not_released`。

### T016 receipt 最终重绑定追加事实（2026-08-12）

- 上一条 receipt correction 也属于 append-only 材料变化；因此 v2 不能作为当前快照证据。随后重新捕获的 v3 receipt=`quality/tests/build-code-phase2-claim-ref-20260812-v3.json`，receipt_hash=`54d3b242aba4e16b2bed9873b43620d7efb0e866307dbf3b06decedb78663e45`，snapshot_tree=`a7204da9229224baeac1316dd7390ac979b2093a`，output_hash=`b4c846727990281a20109fa8f5589078eaa8b2e25d1f213b3e813b40e993210c`，exit=`0`。
- 这条记录仍不把测试绿灯、qwen transport 成功或 opencode 诊断改写成语义/审查通过。T016 继续 incomplete，待 fresh provider semantic evidence 和当前材料绑定的 verify-code。

### T016 fresh semantic rerun after claim reference repair（2026-08-12）

- 使用未改变的冻结 manifest/sample（sample=`20`、source=`89`、manifest hash=`fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f`、input fingerprint=`28f547447f97500977b17fb849e612826b8c1bbce461a6c6eb46c4386ff2ac5c`）、qwen3.6、环境变量凭据、`max_tokens=8192` 和 `15/15` provider calls 完成真实语义重跑。证据=`apply/evidence/T013.semantic-run-20260812-claim-ref-v3.json`，run_id=`run-98428571e91c47228e1cc9d9fb841327`，`run_status=completed`、`delivery_status=not_released`。
- Claim reference 修复在真实运行中生效：本次 failure list 不再出现 provider claim id 不在 trusted input，也不再出现非法/截断 provider JSON；至少一个 mapped typed round 达到 `coverage=1.0`、`faithfulness_status=passed`。这证明修复了原来的 provider 引用协议问题，但不等于整次语义发布通过。
- 真实出口仍未通过：`concepts=0`、`evidence_backtrace=0`、`section_completeness=0`；失败保留为 TopicIndex degraded 映射、必需 section 为空、backtrace 缺失、部分 faithfulness mismatch 和非法版本。冻结 TopicIndex 中 23 个样本行本来就是 degraded，代码按合同跳过，不猜 page type、不改 Task 1 产物、不放宽门槛；embedding 在固定短超时下回退 Jaccard，交付保持 `not_released`。
- 本条只补充真实证据，不重复 Phase 2 异源审查，不把 provider transport 成功或测试通过写成语义通过；下一步重新 capture 当前材料并执行一次普通 `verify-code`，close 前停下。
- 当前材料追加后已重新执行官方 build-code test capture：`uv run --frozen pytest -q && git diff --check`，exit=`0`；receipt=`quality/tests/build-code-phase2-claim-ref-20260812-v6.json`，receipt_hash=`67a01c8c49e49647dc6d75a23342106bbc6fa2c18393924c6271ff4db57b00d8`，snapshot_tree=`ab71edb6e2a0e91099ebcb4c7484c740e19c6a1d`，output_hash=`fdced490d25d6adf6c181b46585be98e7621c35ccc4e39996ff1f79b5cf74a8a`。该 receipt 只证明当前本地回归，不替代语义出口、独立审查或用户确认。

### T016 最新 verify-code 反向检查（2026-08-12）

- 已使用当前四份材料、最新 T013 真实语义证据、当前 build-code 测试 receipt、既有 finding dispositions 和一次性 Phase review 事实执行官方 `verify-code`；结果为 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`，没有重复 Phase 审查，也没有调用 `close`。
- 官方 predicates：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`、`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。缺失事实保持 `unknown`，不把 provider transport 或测试绿灯写成通过。
- 官方 warnings 保留：AC-09/AC-10/AC-11 真实语义出口仍未闭合；短 provider claim reference 已修复，但 TopicIndex degraded、必需 section、evidence backtrace、保真/版本门仍失败；当前 acceptance evidence criterion set 与 spec AC set 不一致；Phase review 中 `OUTPUT_INVALID` 仍是不可用审查事实；尚未取得用户确认。
- T016 与 Task 2-B 继续 `incomplete/not_released`，当前停在 `verify-code` 的 close 前边界。后续若材料继续追加，必须重新 capture 当前测试并重新绑定 verify；不重复审查、不降低门槛、不换 provider。

### T016 verify-code 最新官方结果（2026-08-12）

- 在上一条材料事实之后，重新执行当前树测试 capture：`uv run --frozen pytest -q && git diff --check`，exit=`0`，`513 passed, 3 skipped`；receipt=`quality/tests/build-code-phase2-claim-ref-20260812-v8.json`，receipt_hash=`48bc8a0b275b1f1a447e0adbdb31790f1d83ec3158679af7fcfbb5339d6b9726`，snapshot_tree=`aa3ed56690132f56074f1e2500c31b93d6f4ea08`，output_hash=`13d7b309fa22d87ce7e5cfebcff7cd1a8c013cccae8bf3ed610dc6142b2e4755`。
- 随后使用当前四份材料、v8 receipt、T013 真实语义证据、既有 finding dispositions 和一次性 Phase review 事实执行官方 `verify-code`；结果仍为 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。官方 predicates：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`、`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。
- 最新 quality facts：tests=`quality/facts/0fc8bf4c595a499214d99300406e508caf75c18e867075fd39dbb5c86e9dab40.json`；finding dispositions=`quality/facts/f418726c16f18b5d88cb62fd5b2e65de9e2c6495c1c20ee960192b69aa60fb9e.json`。警告继续保留 AC-09/10/11 语义出口、TopicIndex/section/backtrace/保真/版本缺口、acceptance criterion set 不一致、审查 `OUTPUT_INVALID` 和 human confirmation 缺失。
- 这次仍没有重复 Phase 审查，没有改 provider/model/预算/阈值，没有调用 `close`。当前任务按要求停在 verify-code close 前，Task 2-B 仍 `incomplete/not_released`；本条材料更新后若要再次执行 verify，必须重新 capture 当前快照。

### T016 source_kind 提示修复与真实语义复测（2026-08-12）

- 针对上次真实运行暴露的结构化证据误引用，增加最小实现：typed prompt 从同一 `PageDraft.source_fragments` 给 claim 附加 `source_kind`（如 `table`、`bilingual`、`image`、`code`、`version`），并明确这是处理提示而不是证据；固定 page type、section 合同、trusted claim、门槛、provider/model、预算和失败状态均未改变。
- RED：`uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k 'structured_claim_kind or typed_prompt_compacts_source_context or provider_claim_refs_are_short'`，1 个目标断言失败（缺 `source_kind`，不是 setup error），2 个既有断言通过。GREEN：同命令 `3 passed`；focused/consumer=`167 passed`；全量 `uv run --frozen pytest -q && git diff --check`=`514 passed, 3 skipped`，exit=`0`。
- 使用同一冻结 manifest/sample/config/provider 做真实语义重跑；sample=`20`、source=`89`、manifest hash=`fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f`、input fingerprint=`28f547447f97500977b17fb849e612826b8c1bbce461a6c6eb46c4386ff2ac5c`、qwen3.6、环境变量凭据、`max_tokens=8192`、`14/14` planned/observed provider calls。证据=`apply/evidence/T013.semantic-run-20260812-source-kind-v1.json`，run_id=`run-84c8857251da4746a392308d4f4b8d61`，`run_status=completed`、`delivery_status=not_released`。
- 这次提示有效但没有达到语义出口：`concepts=2`、`evidence_backtrace=234`、`section_completeness=2`，比上次 claim-ref 运行的 `0/0/0` 有改善；但仍有 1 次 provider 非法/截断 JSON、必需 section 为空、保真 mismatch、TopicIndex degraded，且 embedding 运行失败后按合同回退 Jaccard。故不能写成 provider 已通过或产品已发布。
- 大白话结论：qwen3.6 不是完全跑不通，14 次请求中大部分能返回并产生有效 typed 结果；现在主要问题是模型偶尔截断 JSON，并且仍会把“相关证据”当成“正文已明确说出的证据”，所以严格门禁拒绝发布。opencode 也不是主语义运行 provider；本阶段唯一一次异源审查中 `opencode/v4flash=OUTPUT_INVALID`，因此审查不可用，不能解释成“没有严重问题”，也不重复审查。
- 当前 T016 保持 `incomplete/not_released`；本条材料追加后必须重新 capture 当前测试并再执行一次当前材料绑定的普通 `verify-code`。不换 provider、不降阈值、不调用 `close`。

### T016 source_kind 修复后的 verify-code 收尾（2026-08-12）

- 已重新 capture 当前材料快照：`uv run --frozen pytest -q && git diff --check`，exit=`0`，`514 passed, 3 skipped`；receipt=`quality/tests/build-code-phase2-source-kind-20260812-v3.json`，receipt_hash=`f18ee6553170b36ce1bd49c0a1105f4432fcd1556bdf33ba7a17930fadfab7b1`，snapshot_tree=`7173d033694c0b25315fc8c055fd529cd7796d06`，output_hash=`259b4f9b96b1bac8c08004d506cd322d0f72006f1298a491b71cb457ac971f23`。
- 使用当前四份材料、最新测试 receipt、T013 source_kind 真实语义 evidence、既有一次性 Phase 2 review 和 finding dispositions 执行一次官方 `verify-code`；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。官方 predicates：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`、`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。
- 最新 verification=`quality/evidence/verification-v16.json`；语义 evidence 通过 canonical wrapper=`quality/evidence/verify-evidence-v7.json` 绑定，原始运行证据仍保留在 `apply/evidence/T013.semantic-run-20260812-source-kind-v1.json`。官方 warnings 如实保留：acceptance criterion set 与当前 spec 不一致、AC-09/10/11 失败证据、一次 review `OUTPUT_INVALID`、真实语义内容和人类确认缺失。
- 本次没有重复异源审查，没有改 provider/model/预算/阈值，没有调用 `close`。T016 和 Task 2-B 继续 `incomplete/not_released`，停在 verify-code 的 close 前边界。

### T016 结构化 Claim 逐条提示修复（2026-08-12）

- 真实失败样本显示，qwen 会把表格、链接、图片、双语、代码或版本 Claim 改写后仍挂上 Claim ID，主要影响 `sources` 和 `relationships`；这不是允许放宽 Publication Gate 的理由。
- 最小修复：`llm.py` 对这些 `source_kind` 增加逐 Claim 的 `structured_claim_rule=copy_verbatim_or_omit` 提示，并补充明确规则：只能原样复制完整 Claim 后引用，或同时省略事实和 Claim ID。该字段是模型处理提示，不是证据；page type、section、trusted Claim、门槛、provider/model、预算和失败状态均未改变。
- RED：新增断言先失败 1 个目标断言（缺 `structured_claim_rule`，不是 setup error）。GREEN：typed focused=`3 passed, 72 deselected`；Task 2-B=`75 passed`；相邻 consumer=`187 passed, 2 skipped`；全量=`514 passed, 3 skipped`，`git diff --check` 通过。
- 本次当前 shell 没有 provider 凭据环境，未伪造新的 T013 语义运行；现有 source_kind 语义证据仍保持 `2 concepts / 234 backtrace / 2 complete sections / not_released`。不重复 Phase 2 异源审查，后续需在重新注入环境变量后做一次真实语义复测，再重新绑定当前材料的测试 receipt 和 verify-code。

### T016 当前结构化 Claim 修复后的最终 verify-code 事实（2026-08-12）

- 为覆盖本条事实追加和最终 verify 输入，重新执行官方 build-code 测试 capture：`uv run --frozen pytest -q && git diff --check`，exit=`0`，`514 passed, 3 skipped`；receipt=`quality/tests/build-code-phase2-structured-claim-rule-20260812-v2.json`，receipt_hash=`84792c3a601a0b25b98b052577f811861d384901bc51d02a6b6d8e6cc1243310`，snapshot_tree=`f6c4f0df4863d2a2b589e5ff90e38b8046dc34b9`，output_hash=`5b7fc62685e51a12ffd318b1c987daed6d829aee7fba7fe2d6b484a1bd2cbe5b`。
- 使用当前四份材料、v2 测试 receipt、`verify-evidence-v6` 合法 acceptance wrapper、既有一次性 Phase 2 review 和 finding dispositions 执行一次官方 `verify-code`；verification=`quality/evidence/verification-v20.json`，sha256=`7796dfa0cdd57561561de67076e7ea56b4c85bb99eaec69980670d2e15bb7f0a`；结果 `stage=in_progress`、`work_status=ready`、`quality_status=incomplete`。
- 官方 predicates：`full_tests_fresh=satisfied`、`finding_dispositions=satisfied`；`independent_review=missing`、`acceptance_criteria=missing`、`exceptions=missing`、`human_confirmation=missing`。正式 warnings 如实保留：AC-09/10/11 acceptance evidence 为失败/不完整、当前 evidence criterion set 与 spec AC set 不一致、一次审查 `OUTPUT_INVALID`、真实语义的截断 JSON/必需 section/保真/TopicIndex/embedding fallback 缺口、人类确认缺失。
- `verify-evidence-v7` 因包含当前校验器不接受的 `ac_bindings` 字段而未被强行兼容；没有放宽校验器，改用已有合法 `verify-evidence-v6`，并保留其中 AC-09/10/11 的失败事实。两次输入/快照不匹配也保留为执行诊断，不改写成通过。
- 本轮没有重复任何 Phase 异源审查，没有改 provider/model/预算/阈值，没有调用 `close`、提交或合并。T016 和 Task 2-B 仍为 `incomplete/not_released`，当前按要求停在 `verify-code` 的 close 前边界。

### 2026-08-12 当前用户授权后的同任务执行事实

- T013 当前尝试先完成了命令面和输入绑定回读：`uv run --frozen digest --help` exit `0`；冻结 sample manifest hash=`fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f`；冻结题集 hash=`8f5cb5e82c66d26f9b92c122ab5ab2c70f1ac9`；隔离输入为 20-example/30-source 的现有本机样本目录。
- T013 当前尝试在真实 provider 启动前停止：`KD_LLM_API_KEY`、`KD_LLM_MODEL`、`KD_LLM_BASE_URL` 当前均为空/缺失；同时冻结要求的新输出路径 `apply/evidence/T013.semantic-run.json` 已是历史受控文件。历史文件被保留，没有覆盖、重标记或拼接为本次运行证据。
- 当前 preflight 证据：`apply/evidence/T013.preflight-current-20260812.txt`；当前 T013 结论仍为 `incomplete/not_released`。
- T014 当前非 provider 回归：Task 2-B focused（排除 semantic evidence file）`74 passed, 1 deselected`；Task 2/Task 2-A 兼容集合 `82 passed, 2 skipped`；全仓 `514 passed, 3 skipped`；均 exit `0`。详细证据：`apply/evidence/T014.final-regression-current-20260812.txt`。
- WorkflowHub 当前测试收据：`quality/tests/build-code-task2b-20260812-v1.json`，由 canonical build-code test capture 生成；当前树绑定为 `7cf8c40e6703c8284527d74b2cec8bf2d60119d8`。
- 本次没有生产代码变更；确定性测试绿灯不替代 T013 真实语义出口，Task 2-B 仍不能标记完成，Task 2-C 不得继续。

### 2026-08-12 当前用户授权后的真实语义重跑事实

- 按用户提供的 provider 配置，仅在本次进程环境使用凭据，未写入代码、证据或日志；使用冻结 manifest（sample=`20`、source=`89`、hash=`fb9fad748137827a4814f40b28c945df6e1bf15d4b964185219629894be6370f`）、隔离输入/KB、qwen3.6、`max_tokens=8192`、`14/14` provider calls 和原门槛执行绑定重跑。
- 运行完成：run_id=`run-9076fc7b8e8440bb96c03f801bf636d8`、`run_status=completed`、`execution_mode=real_semantic`、provider=`https://dashscope.in.whatspos.cn/v1` / `qwen3.6`、credential=`environment-only`；证据=`apply/evidence/T013.semantic-run-current-20260812.json`，sha256=`a47f51cc653f82f1a023683993e480f8cd11d083ca1adf787c3e9f16fc0ea05b`。
- 真实结果仍未达到语义出口：`concepts=1` 个 machine-passing concept，page type 只有 `module_or_capability`；缺 `product_overview`、`procedure_or_rule`，`evidence_backtrace=168`，`section_completeness=1`，交付=`not_released`。provider 运行成功不等于页面可发布。
- 当前 validator：`valid=false`、`machine_exit_passed=false`、`reader_eligible=false`；唯一门禁原因是 machine-passing concept `<6` 及两类 page type 缺失。其余 AC 绑定字段与 revision ledger 均存在；不把完整字段伪装成语义出口通过。
- 本次未改生产代码、未换 provider、未降阈值、未覆盖旧证据；Task 2-B 仍为 `incomplete/not_released`，Task 2-C 继续停在 `make-decision` 前的延期交接。下一步仍需修复真实语义出口并重新执行完整 T013/T014/verify-code 闭环。
- 记录本条事实后重新执行当前 worktree 回归：`uv run --frozen pytest -q && git diff --check`，exit=`0`，`514 passed, 3 skipped`，`git diff --check` 通过；这只是确定性回归，不改变 T013 语义门禁结论。

### 2026-08-12 快捷路径执行卡

- 用户授权：同一 TaskHandle 内做最小范围调整，不重复完整 WorkflowHub 阶段链；当前官方公开 `scope_revision` 路由已移除，因此不伪造该状态。
- Task 1 前置：修复显式 page-type 从真实 source declaration 到 TopicIndex 的投影，生成新哈希快照并完成 89 来源/主题身份/证据引用对账；旧快照只作审计基线。
- Task 2-B：仅在新快照通过入口对账后重跑 T013/T014；继续使用冻结 sample manifest、qwen3.6、原阈值和真实语义命令。
- STOP：没有真实 URI/hash/locator 绑定、入口对账失败、`>=6`/三类覆盖/实际 inventory 覆盖不满足、provider 失败或证据不完整时，均保持 `incomplete/not_released`，不进入 Task 2-C。
- non-goals：不改 fixed section/page type/body contract，不降低门槛，不用 fixture/overlay/标题或正文猜测，不提前人工读者门、全量 89 篇或 released。

### T013/T014 快捷路径实际结果（2026-08-12）

- Task 1 current snapshot completed from the real 89-source corpus: 54 topics, 31 `published`, 23 `degraded`; explicit `page_type` values are source-declared and bound to URI, content fingerprint, locator and topic identity. Old snapshot remains the audit baseline.
- T013 rerun consumed the current snapshot: run_id=`run-6827d359b90d467c87d3d955d4a6673d`; evidence=`apply/evidence/T013.semantic-run-task1-repair-20260812.json`; sha256=`dd3e746c44edab76500259a61abbca3f97f8a2dcec83ebbbf5356e01d5afd1ce`; `completed` / `real_semantic`; qwen3.6 approved endpoint; environment-only credential; `15/15` provider calls.
- T013 result: `1` machine-passing concept, page type only `module_or_capability`, `evidence_backtrace=168`, complete sections=`1`; validator `valid=false`, `machine_exit_passed=false`, `reader_eligible=false`; missing `product_overview` and `procedure_or_rule`; delivery=`not_released`.
- T014 result: Task 1 focused `49 passed`; consumer regression `262 passed, 2 skipped`; full regression `516 passed, 3 skipped`; `git diff --check` passed. Evidence: `apply/evidence/T014.final-regression-task1-repair-20260812.txt` and `apply/evidence/T014.test-routing-task1-repair-20260812.json`.
- Closure: upstream projection repair is retained, but the semantic exit is still incomplete. No commit/merge/push/cleanup as a completed Task 2-B delivery; Task 2-C remains deferred. Do not retry by lowering gates, guessing page types, or using fixtures/overlays.

### T013/T014 continuation root-cause audit (2026-08-12)

- After the user-authorized continuation, a read-only audit rechecked the frozen Task1 TopicIndex, Task0/Task2 entry evidence, current T013 result, and the Task2-B mapping adapter. The frozen TopicIndex has 54 rows (`31 published`, `23 degraded`), no `page_type`/`digest_page_type` field, and the Task0 entry manifest has no registered machine fixture for the missing page types.
- The current T013 result is therefore not a transient provider-stop: it has `1` machine-passing `module_or_capability`, no legal `product_overview` or `procedure_or_rule` coverage, `machine_exit_passed=false`, and `reader_eligible=false`.
- The adapter's explicit-page-type requirement for `procedure_or_rule` and its no-title/no-prose-guessing behavior are required by the current Task2-B materials. Existing Task2A/Task2B behavior fixtures cannot be promoted to Task0 machine fixtures. Changing the adapter to guess would be a contract violation, not a defect fix.
- A separate read-only typed-provider audit found the remaining body failures are conservative faithfulness rejections for unsupported claim/body pairings; no safe Task2-B-local relaxation or content rewrite can turn them into verified facts. The failure boundary remains fail-closed.
- Formal disposition: the current worktree has no safe in-scope implementation change that can close T013. The minimum valid handoff is upstream evidence registration: bind a real source/topic/page-type candidate with URI, content hash and locator, or have Task0 formally register a machine fixture; for a procedure candidate also bind the deterministic exceptions audit. Only then rerun T013/T014. Until that handoff, Task2-B stays `incomplete/not_released`, no commit/merge/push/cleanup is authorized by completion state, and Task2-C remains deferred per the user's earlier choice A.

### T016 当前真实语义与回归结果（2026-08-12）

- 状态：`completed`（Task 2-B 机器出口与 T014 当前回归已完成）；不等于人工读者质量或正式 released。
- T013 evidence=`apply/evidence/T013.semantic-run-task2b-provider-repair-v9-20260812.json`; run_id=`run-519d5c93591e45faab8e3ef56601a3f1`; evidence sha256=`c38aad3185bd534ee988766d55fc26ee68d5f8b2688f8e00ddb72d23dbbd17e4`; validator=`machine_exit_passed=true`。
- 机器结果：12 个通过 concept，三类 page type 均覆盖；delivery=`not_released`。
- T014 evidence=`apply/evidence/T014.final-regression-task2b-provider-repair-v9-20260812.txt`; Task 1=`49 passed`；消费者=`264 passed, 2 skipped`；全量=`518 passed, 3 skipped`；`git diff --check` 通过。
- 代码边界：未降低 `>=6`、三类覆盖、连续来源块、归因/保真、版本和 `not_released` 门；只增加 bounded provider repair、列表编号格式归一和确认型 Evidence-dump 安全前缀修复。
- 延期交接：Task 2-C 必须从 `make-decision` 开始，负责人工读者可用性、正/负题和人类确认；不得把 T013 机器通过当成人工通过。Task 2-B 的 Git 提交、合并、推送、清理另行完成，当前记录不声称已完成。
