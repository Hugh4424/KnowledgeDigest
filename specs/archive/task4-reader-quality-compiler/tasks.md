# 任务清单：KnowledgeDigest 全量 Reader 质量编译器

- **Input**：`specs/task4-reader-quality-compiler/decision-log.md`（hash `5de5c648019eb219d36855524bb71fb9f5af4801ebeaa32fecb3e5aba6a7dd6b`）、`specs/task4-reader-quality-compiler/spec.md`（hash `a930a5d8393e26edd06cba8f069bc7249d0d9c507841e6fb0d7ab711edda2adf`）、`specs/task4-reader-quality-compiler/plan.md`（hash `2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6`）
- **Template version**：`plan-task.v3`

## Phase P1 — 语义 Reader 编译与机器质量对照

### Goal

让 Task4 先形成可信的来源/语义节点，再形成 Reader，最后用无人工输入的 canonical case evaluator 做严格对照。89 条是覆盖分母，M 个 canonical case 是 Reader 质量分母。

### Files

- **NEW**：`config/task4-source-coverage-89-input.v1.json`；`config/task4-reader-case-matrix-89-input.v1.json`；`config/task4-semantic-baseline.v1.json`；`config/task4-page-type-registry.v1.json`；`config/task4-reader-evaluator.v1.json`
- **MODIFY**：`config/task4-reader-quality.v1.json`；`src/knowledge_digest/task4_reader_quality.py`；`scripts/task4_reader_quality.py`；`tests/acceptance/test_task4_full_compiler.py`；`tests/acceptance/test_task4_full_quality.py`
- **DO NOT TOUCH**：`decision-log.md`、`spec.md`、原始 89 条、CompanyBrain、`config/task4-question-oracle.v1.json`、正式 Task1–Task3 模块。

### Tasks

#### T001 — RED：冻结来源覆盖和全量失败边界

- **ID**：T001
- **Phase**：Phase P1 — 语义 Reader 编译与机器质量对照
- **goal**：增加会真实暴露当前缺口的测试和最小冻结 fixture：生产配置不再默认依赖 89；89 条来源逐行可追溯；任一来源读取/manifest/取消失败都不生成可见 Reader。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task4-reader-quality-compiler/spec.md","hash":"a930a5d8393e26edd06cba8f069bc7249d0c507841e6fb0d7ab711edda2adf","id":"task4-reader-quality-compiler-spec-v1"},{"artifact_kind":"plan","ref":"specs/task4-reader-quality-compiler/plan.md","hash":"2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6","id":"task4-reader-quality-compiler-plan-v1"}]`
- **source_refs / decision_refs**：R-001/R-002、PFACT-001、PFACT-007、D-024 → FR-SOURCE-001/002 → AC-SOURCE-001/002、AC-STATE-001/002
- **输入**：当前 spec 的 source contract；真实 89 manifest fixture；现有 `_collect_sources`、`ingest`、`identity` 和 `batch_run` 锚点。
- **依赖**：none
- **并行**：否 — first RED for source contract
- **FR**：FR-SOURCE-001、FR-SOURCE-002、FR-STATE-002
- **AC**：AC-001、AC-SOURCE-001、AC-SOURCE-002、AC-STATE-001、AC-STATE-002
- **动作**：只增加失败断言和冻结 fixture，不修改生产实现。测试必须同时覆盖真实 89 manifest 绑定、一个配置变体、损坏/缺失来源、取消和 manifest drift。
- **精确文件**：`config/task4-source-coverage-89-input.v1.json`；`config/task4-reader-quality.v1.json`；`tests/acceptance/test_task4_full_compiler.py`
- **boundary**：files: 上述三项; symbols/regions: `_config`/fixture helpers、source manifest assertions、failure/cancel tests；不得改正式 Task1–Task3 模块。
- **输出**：RED 回执目标，至少包含 expected 89、observed count、source id/content hash、失败 reason code 和 `bundle/Home.md` 不存在。
- **Knowledge**：当前 `compile_full_reader` 以默认 89 和 `core_source_patterns` 判断候选；正式 `ingest`/`batch_run` 可提供稳定 manifest 和 replay 事实。
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py`
- **expected_exit**：1
- **oracle**：`ORACLE-COMPILER-FULL` — 失败应指向缺少通用 source contract、全量硬门、稳定身份或旧候选保护，而不是测试本身损坏。
- **evidence_path**：`quality/evidence/build-plan/T001-compiler-red.json`
- **STOP**：命令无法收集、fixture 不能绑定真实 manifest、需要修改 spec/decision-log、或失败原因不是目标行为时停止并回到 owning material。
- **recovery**：build-code 执行者只修测试 fixture/测试断言；不为让 RED 通过而放宽 oracle。
- **task risk**：把合成 89 条误当真实 89 条，或用固定数字掩盖漏源。
- **test tier / test method**：feature — 直接运行 CLI adapter 的完整 source→output seam，不用单元 mock 掩盖失败。
- **scenarios / commands / expected exit / oracle**：正常真实 manifest→非零 RED；变体配置→非零 RED；损坏/缺失/取消/drift→非零 RED 且无 Reader；均用上述命令和 `ORACLE-COMPILER-FULL`。
- **fixtures_services**：新 source coverage fixture、临时 raw/output 目录；无服务；测试结束清理 tmp_path。
- **coverage limits**：只覆盖 source manifest、全量失败、旧候选保护；不证明语义命名、正文质量或 CompanyBrain 对照。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：重写 Task4 compiler acceptance fixture，覆盖配置化来源分母、89 全量清单、坏源、取消、冲突、语义命名/分类和 Reader/Audit 隔离。
- **executed_commands**：`env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py`；RED exit `1`（7 个目标断言因旧实现仍校验 `expected_source_count`）；GREEN exit `0`，`7 passed`。
- **evidence_refs**：`tests/acceptance/test_task4_full_compiler.py`；`quality/tests/task4-p1/compiler-red.json`；`quality/tests/task4-p1/compiler-green.json`。
- **covered_ac**：AC-001、AC-SOURCE-001、AC-SOURCE-002、AC-STATE-001、AC-STATE-002。
- **review_fact**：P1 review 已执行一次，结果 `unavailable`，`MATERIAL_INCOMPLETE`；没有把 unavailable 写成 pass，也没有待处置 provider finding。
- **completed_at**：`2026-08-19T01:10:00Z`
- **执行事实**：RED 来自配置契约和目标行为，不是 import/setup；GREEN 复核真实 pytest，当前仍保留 review unavailable 风险。

#### T002 — GREEN：实现通用来源快照和全量候选硬门

- **ID**：T002
- **Phase**：Phase P1 — 语义 Reader 编译与机器质量对照
- **goal**：让 T001 通过：生产配置不写死 89；输入来源有稳定 id、snapshot/hash、manifest generation 和失败状态；任一 89 条硬失败、取消或 drift 不发布 Reader。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task4-reader-quality-compiler/spec.md","hash":"a930a5d8393e26edd06cba8f069bc7249d0d9c507841e6fb0d7ab711edda2adf","id":"task4-reader-quality-compiler-spec-v1"},{"artifact_kind":"plan","ref":"specs/task4-reader-quality-compiler/plan.md","hash":"2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6","id":"task4-reader-quality-compiler-plan-v1"}]`
- **source_refs / decision_refs**：与 T001 相同：R-001/R-002、PFACT-001/007、D-024 → FR-SOURCE-001/002 → AC-SOURCE-001/002、AC-STATE-001/002
- **输入**：T001 真实失败事实；`ingest.py:ingest`、`identity.py`、`batch_run.py:build_input_manifest`。
- **依赖**：T001
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-SOURCE-001、FR-SOURCE-002、FR-STATE-002
- **AC**：AC-001、AC-SOURCE-001、AC-SOURCE-002、AC-STATE-001、AC-STATE-002
- **动作**：最小修改 Task4 adapter/config，复用正式快照、身份和 batch manifest；把样本 89 放入 fixture 校验，不放入默认编译逻辑；staging 只有全量硬门通过才切换。
- **精确文件**：`config/task4-source-coverage-89-input.v1.json`；`config/task4-reader-quality.v1.json`；`src/knowledge_digest/task4_reader_quality.py`；`tests/acceptance/test_task4_full_compiler.py`
- **boundary**：files: 上述四项; symbols/regions: `_load_config`、`_collect_sources`/source adapter、`compile_full_reader` preflight/status/publish；不得修改正式模块。
- **输出**：GREEN 回执、89 条 source manifest、稳定 id/hash、失败/取消/drift Audit、候选包状态和旧 Reader 保护事实。
- **Knowledge**：T001 的失败 oracle 和 fixture 绑定方式；source denominator 只来自 manifest/config fixture，不来自默认常量。
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py`
- **expected_exit**：0
- **oracle**：`ORACLE-COMPILER-FULL` — 正例全量覆盖且状态清楚；负例仍非候选且无可见 Home；配置变体不依赖样本路径。
- **evidence_path**：`quality/evidence/build-code/T002-compiler-green.json`
- **STOP**：需要更改正式 pipeline/writer 边界、需要把任何失败转为 candidate、或不能保留失败根因时停止。
- **recovery**：保留 staging/Audit，回滚 Task4 adapter 本 task 改动，再重跑 T001/T002 同命令。
- **task risk**：把失败“处理成成功”、复用旧 candidate、或只在测试 helper 中满足覆盖。
- **test tier / test method**：feature — 同 T001，验证真实文件边界和原子发布行为。
- **scenarios / commands / expected exit / oracle**：正常→0；变体→0；损坏/缺失/取消/drift→测试断言 fail-closed；同命令、同 oracle。
- **fixtures_services**：同 T001；无外部服务。
- **coverage limits**：不覆盖 semantic node admission、页面正文和质量比较。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：实现通用 source snapshot/manifest generation、全量硬失败、semantic node pending/conflict 审计、staging 发布和失败时清理旧 bundle；生产路径不再默认写死 89。
- **executed_commands**：同 T001；GREEN exit `0`，`7 passed`；覆盖 89 与 2 条变体来源。
- **evidence_refs**：`src/knowledge_digest/task4_reader_quality.py`；`scripts/task4_reader_quality.py`；`tests/acceptance/test_task4_full_compiler.py`。
- **covered_ac**：AC-001、AC-SOURCE-001、AC-SOURCE-002、AC-STATE-001、AC-STATE-002；真实 89 运行与 CompanyBrain 优势尚未由本 task claim。
- **review_fact**：同 P1 review：`unavailable / MATERIAL_INCOMPLETE`；状态完整但质量声明保持 incomplete。
- **completed_at**：`2026-08-19T01:10:00Z`
- **执行事实**：任一来源失败、manifest 数量不符、pending/conflict 或取消都不发布 bundle；失败保留 Audit/Reports。

#### T003 — RED：语义命名、分类、正文、关系和 Reader/Audit 边界

- **ID**：T003
- **Phase**：Phase P1 — 语义 Reader 编译与机器质量对照
- **goal**：增加会暴露当前质量问题的测试：文件名由可读对象/任务名生成，不带 `ae-` 和输入噪声；产品/模块/对象/场景可解释；新节点需两条互相支持证据；正文有 page-type section、边界、关系、来源投影；pending/conflict 只在 Audit；Reader 不泄漏内部字段。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task4-reader-quality-compiler/spec.md","hash":"a930a5d8393e26edd06cba8f069bc7249d0d9c507841e6fb0d7ab711edda2adf","id":"task4-reader-quality-compiler-spec-v1"},{"artifact_kind":"plan","ref":"specs/task4-reader-quality-compiler/plan.md","hash":"2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6","id":"task4-reader-quality-compiler-plan-v1"}]`
- **source_refs / decision_refs**：R-001/R-002、PFACT-002/003、D-020/D-021/D-022 → FR-SEMANTIC-001–005、FR-READER-001/002、FR-AUDIT-001/002 → AC-COMPILER-001–005、AC-READER-001/002、AC-AUDIT-001/002
- **输入**：T002 的稳定 source manifest；`topic_axis.py`、`draft.py`、`page_layout.py`、`reader_bundle.py`、`navigation.py`、`provenance.py` 的现有接口；新增 semantic baseline/page registry fixture。
- **依赖**：T002
- **并行**：否 — 依赖 source contract
- **FR**：FR-SEMANTIC-001、FR-SEMANTIC-002、FR-SEMANTIC-003、FR-SEMANTIC-004、FR-SEMANTIC-005、FR-READER-001、FR-READER-002、FR-READER-003、FR-READER-004、FR-AUDIT-001、FR-AUDIT-002、FR-AUDIT-003、FR-STATE-002
- **AC**：AC-COMPILER-001、AC-COMPILER-002、AC-COMPILER-003、AC-COMPILER-004、AC-COMPILER-005、AC-READER-001、AC-READER-002、AC-READER-003、AC-READER-004、AC-STATE-002、AC-AUDIT-001、AC-AUDIT-002
- **动作**：只增加正例/负例断言和 fixture，不改生产实现。覆盖：真实来源可读标题/路径；至少两个 evidence fragment 的新节点；单证据 pending；冲突；关系 target；页面类型必需 section；Reader link 只到 Reader projection；`source_uri/provider/claim_id/fingerprint` 不出现。
- **精确文件**：`config/task4-semantic-baseline.v1.json`；`config/task4-page-type-registry.v1.json`；`config/task4-reader-quality.v1.json`；`tests/acceptance/test_task4_full_compiler.py`
- **boundary**：files: 上述四项; symbols/regions: taxonomy/semantic/page/body/navigation/provenance assertions；不改 formal module。
- **输出**：RED 证据必须能指出至少一个 `ae`/通用/错分类/单证据放行/正文缺失/内部泄漏/关系坏链断言失败。
- **Knowledge**：CompanyBrain 的优势是编辑后的语义产品→模块→对象/场景→任务结构；不能把其固定路径直接复制为 KD 分类。
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py`
- **expected_exit**：1
- **oracle**：`ORACLE-SEMANTIC-READER` — 失败信号来自命名、语义状态、正文 section、关系/来源 projection、Reader/Audit 隔离，不来自测试收集错误。
- **evidence_path**：`quality/evidence/build-plan/T003-semantic-red.json`
- **STOP**：若需要修改产品目录原则、补人工分类或正式模块无法支持而需扩需求，回 `spec.md`/`decision-log.md`。
- **recovery**：只修 fixture/测试断言到真实 spec；不把当前坏产物写成 oracle。
- **task risk**：测试只检查一个位置字段页，不能覆盖后续文件名/分类/正文问题。
- **test tier / test method**：feature — 同时检查全量页面和至少四类正负例，不做单页 smoke。
- **scenarios / commands / expected exit / oracle**：正常/新节点/单证据/冲突/关系/坏链/内部泄漏，统一上述命令、非零 RED、同一 oracle。
- **fixtures_services**：semantic baseline、page registry、临时真实样本/合成边界 fixture；无服务；tmp_path 清理。
- **coverage limits**：不判断 CompanyBrain 三轴优劣，不执行真实大 corpus。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：补齐 semantic node、可读标题/分类、关系 ledger、page-type section、Reader source projection 和 pending/conflict Audit 断言。
- **executed_commands**：compiler focus command RED exit `1`（目标断言失败）；同命令 GREEN exit `0`，`8 passed`。
- **evidence_refs**：`tests/acceptance/test_task4_full_compiler.py`；`quality/tests/task4-p1/semantic-red.json`；`quality/tests/task4-p1/semantic-green.json`。
- **covered_ac**：AC-COMPILER-001/002/003/004/005、AC-READER-001/002/003/004、AC-AUDIT-001/002、AC-STATE-002。
- **review_fact**：复用本 P1 review：`unavailable / MATERIAL_INCOMPLETE`；无可信 findings 可伪装处置。
- **completed_at**：`2026-08-19T01:18:00Z`
- **执行事实**：单证据节点进入 pending；显式冲突进入 Audit；Reader 不出现 `ae-`、`通用`、内部审计字段；关系 link 与 relation ledger 同时生成。

#### T004 — GREEN：从 semantic node 生成可读 Reader

- **ID**：T004
- **Phase**：Phase P1 — 语义 Reader 编译与机器质量对照
- **goal**：让 T003 通过：同一 semantic node 决定产品/模块/对象/场景、显示名、文件名、页面正文、相关主题、来源投影和稳定链接；证据不足/冲突只进 Audit；页面类型和 300 行/Claim ownership 复用正式校验。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task4-reader-quality-compiler/spec.md","hash":"a930a5d8393e26edd06cba8f069bc7249d0d9c507841e6fb0d7ab711edda2adf","id":"task4-reader-quality-compiler-spec-v1"},{"artifact_kind":"plan","ref":"specs/task4-reader-quality-compiler/plan.md","hash":"2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6","id":"task4-reader-quality-compiler-plan-v1"}]`
- **source_refs / decision_refs**：与 T003 相同：R-001/R-002、PFACT-002/003、D-020/D-021/D-022 → FR-SEMANTIC-001–005、FR-READER-001/002、FR-AUDIT-001/002 → AC-COMPILER-001–005、AC-READER-001/002、AC-AUDIT-001/002
- **输入**：T003 的失败断言；T002 source manifest；正式 identity/topic_axis/draft/page_layout/reader_bundle/navigation/provenance 接口。
- **依赖**：T003
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-SEMANTIC-001、FR-SEMANTIC-002、FR-SEMANTIC-003、FR-SEMANTIC-004、FR-SEMANTIC-005、FR-READER-001、FR-READER-002、FR-READER-003、FR-READER-004、FR-AUDIT-001、FR-AUDIT-002、FR-AUDIT-003、FR-STATE-002
- **AC**：AC-COMPILER-001、AC-COMPILER-002、AC-COMPILER-003、AC-COMPILER-004、AC-COMPILER-005、AC-READER-001、AC-READER-002、AC-READER-003、AC-READER-004、AC-STATE-002、AC-AUDIT-001、AC-AUDIT-002
- **动作**：把当前平行 keyword compiler 改为薄适配层；移除默认 89、`ae-`/旧文件名规则和 `通用` 伪分类；实现 semantic node admission、relation ledger、page-type body；用正式模块做身份、Claim、分页、Reader projection、导航、溯源和 staging；更新 root-cause 链。
- **精确文件**：`config/task4-reader-quality.v1.json`；`config/task4-semantic-baseline.v1.json`；`config/task4-page-type-registry.v1.json`；`src/knowledge_digest/task4_reader_quality.py`；`tests/acceptance/test_task4_full_compiler.py`
- **boundary**：files: 上述五项; symbols/regions: `_load_config`、taxonomy/semantic helpers、`_extract_content`、`_render_topic_page`、`compile_full_reader` 和对应 tests；不得改 formal module API/正式发布链。
- **输出**：GREEN Reader bundle、Home→产品→模块→主题可达；每页有 page-type sections、可读文件名、关系、来源简表；Audit 记录 pending/conflict/degraded；claim/source lineage 可回查。
- **Knowledge**：T003 真实失败事实；新节点 admission 不是目录猜测；Reader projection 与 Audit projection 分离。
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py`
- **expected_exit**：0
- **oracle**：`ORACLE-SEMANTIC-READER` — 全量页面不再有 `ae-`/伪通用；节点状态、正文、关系、来源和失败边界符合 fixture；Reader 无内部字段/坏链。
- **evidence_path**：`quality/evidence/build-code/T004-semantic-green.json`
- **STOP**：需要人工逐页确认、需要复制 CompanyBrain 固定目录、需要改变 formal Task1–Task3 API、或为通过测试删除来源事实时停止。
- **recovery**：保留 Audit，回滚 Task4 adapter 到 T002；不保留质量未知的 Reader candidate。
- **task risk**：为了文件名好看而删掉原文、为了分类稳定而把未知归入通用、或关系全部按同模块猜。
- **test tier / test method**：feature — 全量 Reader 结构/正文/关系/溯源和失败 seam。
- **scenarios / commands / expected exit / oracle**：同 T003 的所有场景；正常 GREEN 0，负例仍验证 Audit/not_released；同命令、同 oracle。
- **fixtures_services**：同 T003；无服务。
- **coverage limits**：不证明比 CompanyBrain 更好；只证明 KD Reader 合同和语义编译边界。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：把分类、命名、正文、关系、来源投影和 staging 发布收敛到同一 topic/semantic node；CLI 保持 Task4 独立，不碰 formal pipeline。
- **executed_commands**：`env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py`；exit `0`，`8 passed`。
- **evidence_refs**：`src/knowledge_digest/task4_reader_quality.py`；`scripts/task4_reader_quality.py`；`config/task4-semantic-baseline.v1.json`；`config/task4-page-type-registry.v1.json`。
- **covered_ac**：同 T003；真实 89 运行和最终三轴结果仍交 verify-code。
- **review_fact**：P1 review unavailable，质量声明 incomplete。
- **completed_at**：`2026-08-19T01:18:00Z`
- **执行事实**：所有 topic 页先在 staging 生成，只有全量硬门通过才发布 bundle；失败运行只保留 Audit/Reports。

#### T005 — RED：冻结 canonical case 和严格三轴 evaluator

- **ID**：T005
- **Phase**：Phase P1 — 语义 Reader 编译与机器质量对照
- **goal**：增加会暴露当前人工流程和弱 oracle 的测试：读取 89→M case matrix；重复来源只计一次；每个 case 有唯一 comparison key、page type、criticality、答案/边界/关系锚点；CompanyBrain 多路径、N/A、unknown、缺 oracle、负例不能被算成优势；不传人工表也能运行。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task4-reader-quality-compiler/spec.md","hash":"a930a5d8393e26edd06cba8f069bc7249d0d9c507841e6fb0d7ab711edda2adf","id":"task4-reader-quality-compiler-spec-v1"},{"artifact_kind":"plan","ref":"specs/task4-reader-quality-compiler/plan.md","hash":"2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6","id":"task4-reader-quality-compiler-plan-v1"}]`
- **source_refs / decision_refs**：R-003/R-004、PFACT-006/007、D-023/D-024 → FR-READER-003/004、FR-QUALITY-001–003 → AC-READER-003/004、AC-QUALITY-001–005
- **输入**：T004 的 Reader；CompanyBrain 只读 baseline；新增 source coverage/case matrix/evaluator；旧 17+3 和人工表必须不再作为输入。
- **依赖**：T004
- **并行**：否 — evaluator 消费稳定 Reader
- **FR**：FR-READER-003、FR-READER-004、FR-AUDIT-001、FR-AUDIT-002、FR-AUDIT-003、FR-QUALITY-001、FR-QUALITY-002、FR-QUALITY-003
- **AC**：AC-READER-003、AC-READER-004、AC-STATE-001、AC-STATE-002、AC-AUDIT-001、AC-AUDIT-002、AC-QUALITY-001、AC-QUALITY-002、AC-QUALITY-003、AC-QUALITY-004、AC-QUALITY-005
- **动作**：只补 case/evaluator fixture、对比结果和负例断言，不改生产评估器。覆盖路径首命中/跳数、答案 completeness、boundary/source clarity、N/A/unknown/critical、负向 false hit、baseline hash/session isolation。
- **精确文件**：`config/task4-source-coverage-89-input.v1.json`；`config/task4-reader-case-matrix-89-input.v1.json`；`config/task4-reader-evaluator.v1.json`；`tests/acceptance/test_task4_full_quality.py`
- **boundary**：files: 上述四项; symbols/regions: case/evaluator loaders、comparison assertions、receipt assertions；不改旧历史 oracle。
- **输出**：RED 证据应指出当前 17+3、human table、固定 89、关键词/首页面扫描等缺口至少一项。
- **Knowledge**：quality denominator=M；`N/A` 表示 CompanyBrain 真无主题，delta=0；unknown/critical evidence missing=undecidable。
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_quality.py`
- **expected_exit**：1
- **oracle**：`ORACLE-READER-COMPARE` — 失败必须来自 case denominator、strict delta、N/A/unknown、人工输入依赖或 receipt 漂移。
- **evidence_path**：`quality/evidence/build-plan/T005-quality-red.json`
- **STOP**：case matrix 只能从生成产物反推、CompanyBrain baseline 漂移、需要人工逐页确认或需要重新定义“更好”时停止。
- **recovery**：只补冻结材料/测试；不把任何旧报告当当前质量事实。
- **task risk**：只改 17+3 数字，不真正覆盖 89→M 和 CompanyBrain 全树。
- **test tier / test method**：feature — 同一批量 evaluator 输入，覆盖正/负/缺失/多路径/N/A/unknown。
- **scenarios / commands / expected exit / oracle**：完整 case、重复 map、多路径、N/A、缺 oracle、negative false hit、无人工参数，统一上述命令、非零 RED、同一 oracle。
- **fixtures_services**：四份冻结 JSON、临时 KD/CompanyBrain 树；无服务；tmp_path 清理。
- **coverage limits**：不证明真实 89 运行已完成；只设计 evaluator 合同。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增机器 case/evaluator fixture 和质量 acceptance；移除旧 17+3/human table 测试入口。
- **executed_commands**：quality focus command初次 exit `1`，严格三轴目标断言失败；修正 source-anchor oracle 后同命令 exit `0`，`4 passed`。
- **evidence_refs**：`tests/acceptance/test_task4_full_quality.py`；`quality/tests/task4-p1/quality-red.json`；`quality/tests/task4-p1/quality-green.json`。
- **covered_ac**：AC-QUALITY-001/002/003/004/005、AC-READER-003/004、AC-AUDIT-001/002、AC-STATE-001/002。
- **review_fact**：P1 review unavailable / MATERIAL_INCOMPLETE；无人工评审事实。
- **completed_at**：`2026-08-19T01:20:00Z`
- **执行事实**：测试不传人工表；N/A neutral；多路径和缺 oracle 进入 undecidable；比较使用固定 case denominator。

#### T006 — GREEN：实现无人工的全量 Reader 质量评估

- **ID**：T006
- **Phase**：Phase P1 — 语义 Reader 编译与机器质量对照
- **goal**：让 T005 通过：评估器只消费 case matrix/evaluator/CompanyBrain manifest；输出机器覆盖、comparison、receipt、root cause、release summary；全量覆盖且严格不差并至少一轴更好才报告 `better_than_companybrain`，否则 `undecidable/not_released`。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task4-reader-quality-compiler/spec.md","hash":"a930a5d8393e26edd06cba8f069bc7249d0d9c507841e6fb0d7ab711edda2adf","id":"task4-reader-quality-compiler-spec-v1"},{"artifact_kind":"plan","ref":"specs/task4-reader-quality-compiler/plan.md","hash":"2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6","id":"task4-reader-quality-compiler-plan-v1"}]`
- **source_refs / decision_refs**：与 T005 相同：R-003/R-004、PFACT-006/007、D-023/D-024 → FR-READER-003/004、FR-QUALITY-001–003 → AC-READER-003/004、AC-QUALITY-001–005
- **输入**：T005 的失败断言；T004 Reader；case matrix/evaluator；CompanyBrain manifest/hash。
- **依赖**：T005
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-READER-003、FR-READER-004、FR-AUDIT-001、FR-AUDIT-002、FR-AUDIT-003、FR-QUALITY-001、FR-QUALITY-002、FR-QUALITY-003
- **AC**：AC-READER-003、AC-READER-004、AC-STATE-001、AC-STATE-002、AC-AUDIT-001、AC-AUDIT-002、AC-QUALITY-001、AC-QUALITY-002、AC-QUALITY-003、AC-QUALITY-004、AC-QUALITY-005
- **动作**：重写 `_machine_quality`/`assess_reader_quality` 的入口和聚合：从 fixture 读取 source denominator/case denominator；使用唯一 comparison key 和真实 Home route；实现 N/A/unknown/critical 分支、axis delta、严格聚合、根因链；移除 `_load_human_table` consumer 和旧 17+3 硬编码；CLI 改为 `--quality-config`。
- **精确文件**：`config/task4-reader-case-matrix-89-input.v1.json`；`config/task4-reader-evaluator.v1.json`；`config/task4-reader-quality.v1.json`；`src/knowledge_digest/task4_reader_quality.py`；`scripts/task4_reader_quality.py`；`tests/acceptance/test_task4_full_quality.py`
- **boundary**：files: 上述六项; symbols/regions: evaluator loaders、`_machine_quality`、`assess_reader_quality`、CLI assess parser、quality tests；不改变 formal Reader release chain。
- **输出**：质量 JSON/Markdown、evaluator receipt、root cause、release summary；明确 source_count=89、case_count=M、unknown/N/A/critical 计数和严格结论。
- **Knowledge**：T005 目标失败事实；没有人工表也能运行；CompanyBrain 只读、baseline-first、session isolated、network disabled。
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_quality.py`
- **expected_exit**：0
- **oracle**：`ORACLE-READER-COMPARE` — 正常 fixture 可重算；缺失/漂移/N/A/unknown/critical/negative false hit 均拒绝“更好”；不读人工表。
- **evidence_path**：`quality/evidence/build-code/T006-quality-green.json`
- **STOP**：需要人工 review table、把 N/A 算优势、把未知当 0、弱化 strict no-worse、或用合成 baseline 代替真实 baseline 时停止。
- **recovery**：保留 assessment 报告原始状态，回滚评估器到 T005 前，不删除 root-cause evidence。
- **task risk**：评估器本身通过但 Reader 内容仍差；质量报告必须保留逐 case evidence，不能只给一个总分。
- **test tier / test method**：feature — 机器批量对照和故障状态 seam；不调用网络/LLM。
- **scenarios / commands / expected exit / oracle**：完整 M cases→0；缺 oracle/hash drift/multiple baseline/N/A/unknown→0（测试断言报告 undecidable）；negative false hit→0（报告阻断）；同命令、同 oracle。
- **fixtures_services**：冻结 JSON、临时 KD/CompanyBrain 树；无服务；tmp_path 清理。
- **coverage limits**：不等同真实 CompanyBrain 全量语义优于；真实 89 compile+assess 由 verify-code 绑定独立运行证据。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：重写 `_machine_quality`/`assess_reader_quality` 为 quality-config/case-matrix 入口；输出逐 case 三轴、receipt、根因和 release summary；CLI 改为 `--quality-config`。
- **executed_commands**：`env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_quality.py`；exit `0`，`4 passed`。
- **evidence_refs**：`src/knowledge_digest/task4_reader_quality.py`；`scripts/task4_reader_quality.py`；`config/task4-reader-case-matrix-89-input.v1.json`；`config/task4-reader-evaluator.v1.json`。
- **covered_ac**：同 T005；业务结论仅在机器证据完整时报告，仍不代表 formal released。
- **review_fact**：P1 review unavailable，未声称 provider clean。
- **completed_at**：`2026-08-19T01:20:00Z`
- **执行事实**：评估器没有 `human_reviewed` 字段/参数；CompanyBrain 只读，baseline-first、network-disabled 记录在 receipt。

#### T007 — FINAL：聚合回归和 build-plan 交接

- **ID**：T007
- **Phase**：Phase P1 — 语义 Reader 编译与机器质量对照
- **goal**：按计划一次验证全部适用 AC、跨 task seam 和当前完整回归，形成交给 verify-code 的真实交接事实；不新建状态权威，不把测试绿改写成质量优于。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task4-reader-quality-compiler/spec.md","hash":"a930a5d8393e26edd06cba8f069bc7249d0d9c507841e6fb0d7ab711edda2adf","id":"task4-reader-quality-compiler-spec-v1"},{"artifact_kind":"plan","ref":"specs/task4-reader-quality-compiler/plan.md","hash":"2d0782423487d5c807e4fcb7abc1e54eff44263bee7ecc0ef141b0f183ec95a6","id":"task4-reader-quality-compiler-plan-v1"}]`
- **source_refs / decision_refs**：R-001–R-004、PFACT-001–007、D-020–D-024 → 全部适用 FR/AC
- **输入**：T002、T004、T006 的完成事实、当前快照、既有 Task2/Task3 回归测试。
- **依赖**：T006
- **并行**：否 — aggregate reads all preceding task facts
- **FR**：FR-SOURCE-001、FR-SOURCE-002、FR-SEMANTIC-001、FR-SEMANTIC-002、FR-SEMANTIC-003、FR-SEMANTIC-004、FR-SEMANTIC-005、FR-READER-001、FR-READER-002、FR-READER-003、FR-READER-004、FR-AUDIT-001、FR-AUDIT-002、FR-AUDIT-003、FR-QUALITY-001、FR-QUALITY-002、FR-QUALITY-003、FR-STATE-002
- **AC**：AC-001、AC-SOURCE-001、AC-SOURCE-002、AC-COMPILER-001、AC-COMPILER-002、AC-COMPILER-003、AC-COMPILER-004、AC-COMPILER-005、AC-READER-001、AC-READER-002、AC-READER-003、AC-READER-004、AC-STATE-001、AC-STATE-002、AC-AUDIT-001、AC-AUDIT-002、AC-QUALITY-001、AC-QUALITY-002、AC-QUALITY-003、AC-QUALITY-004、AC-QUALITY-005
- **动作**：只执行一次最终命令，记录退出码、测试收集、失败、覆盖限制、逐 AC 状态、review finding 和 verify-code 真实运行入口；不修改四份材料。
- **精确文件**：`tests/acceptance/test_task4_full_compiler.py`
- **boundary**：files: Phase P1 NEW/MODIFY 及既有回归测试; symbols/regions: 只读验证和证据写入，不在 T007 修生产逻辑。
- **输出**：`quality/evidence/build-plan/T007-final.json` 目标；包括完整测试输出、current snapshot、covered/uncovered AC、剩余风险、下一阶段命令。
- **Knowledge**：所有前置 task 的真实测试/失败/修复事实；真实 M 和 89 运行结果如尚未执行，明确记为 unknown/deferred。
- **verification_role**：N/A — non-behavior aggregate verification
- **paired_task**：N/A — aggregate has no RED/GREEN pair
- **gate_cmd**：`pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py tests/acceptance/test_task4_full_quality.py tests/acceptance/test_task4_location_compiler.py tests/acceptance/test_task4_location_gate.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task3_projection.py tests/acceptance/test_task3_quality_release.py tests/acceptance/test_task3_closeout.py`
- **expected_exit**：0
- **oracle**：`ORACLE-FINAL-TASK4` — 所有适用测试通过、无 skipped 代替关键证据、逐 AC 有事实；质量结论仍受真实 89/CompanyBrain 运行证据约束。
- **evidence_path**：`quality/evidence/build-plan/T007-final.json`
- **STOP**：命令损坏、前置 task 未完成、出现越界改动、缺逐 AC 事实或需要新方向时停止，回 owning material。
- **recovery**：回到具体失败 task；不把最终聚合改成“重跑直到绿”。
- **task risk**：把旧历史测试或旧产物误认当前快照；把 `better_than_companybrain` 当作已发布。
- **test tier / test method**：fullstack — 当前 Task4 与 Task2/Task3 Reader/quality/release seam 的一次真实聚合。
- **scenarios / commands / expected exit / oracle**：正常完整回归→0；任何失败保留原始输出并回受影响 task；取消/permission/drift/unknown 的语义由前置测试 oracle 判定。
- **fixtures_services**：既有 acceptance fixture；无服务；测试自身临时目录清理。
- **coverage limits**：不替代真实 89 资料 compile、CompanyBrain 全量比较、verify-code 独立审查或正式 release。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：无生产逻辑新增；对当前 Task4 快照执行最终跨模块聚合回归，并保留真实 89 条编译与评估的未发布事实。
- **executed_commands**：`env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py tests/acceptance/test_task4_full_quality.py tests/acceptance/test_task4_location_compiler.py tests/acceptance/test_task4_location_gate.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task3_projection.py tests/acceptance/test_task3_quality_release.py tests/acceptance/test_task3_closeout.py`；exit `0`，`276 passed in 5.99s`。
- **evidence_refs**：上述 10 个 acceptance 文件；`/Users/Hugh/Downloads/KnowledgeDigest-task4-real-candidate-20260819-v4/status.json`；`/Users/Hugh/Downloads/KnowledgeDigest-task4-real-assessment-20260819-v5/reports/release-summary.json`。
- **covered_ac**：全部 Task4 适用 AC 的测试回归事实；真实 89 结果为 `package_status=not_released`、`source_count=89`、`reader_source_count=88`、`failure_count=1`，质量评估为 `undecidable/candidate_not_released`，因此未覆盖“整体优于 CompanyBrain”的业务结论。
- **review_fact**：现有 P1 `wh-review` 结果仍为 `unavailable / MATERIAL_INCOMPLETE`；没有把 unavailable 或测试绿写成 review pass。
- **completed_at**：`2026-08-19T01:25:00Z`
- **执行事实**：聚合回归通过；真实 89 仍有一条空文件 `emm for android /AE - AirViewer厂商管理.md`，按全量硬门不发布 Reader。下一阶段必须由 verify-code 反向检查原始需求、Design、完整用户流程和该未发布边界。

#### T007 current repair rerun — 2026-08-19

- **最新回归**：聚焦 `test_task4_full_compiler.py`、`test_task4_full_quality.py`、`test_task4_companybrain_mapping.py` 为 `34 passed`；仓库全量为 `731 passed, 3 skipped in 28.73s`。
- **最新真实产物**：v38 89 条为 `source_count=89 / reader_source_count=88 / failure_count=1 / package_status=not_released`，失败源仍是 `emm for android /AE - AirViewer厂商管理.md` 的 `empty_body`。
- **最新映射**：`config/task4-companybrain-mapping-20260819-v13-89.json` 使用完整 1,406 文件 manifest、716 页 Reader scope 和 typed `ck1` key；89 行为 `5 unique / 83 not_applicable / 1 undecidable`，不可证明身份不再被 fuzzy 猜测。
- **最新对照**：v37 88 条可读诊断状态为 `better_than_companybrain`；路径和边界/来源清晰度更好，答案完整度不差；正式 89 仍不计为通过。
- **当前 verify-code 结论**：没有新的严重代码 finding；正式 89 条被原始空文件阻断，`quality/verify.json` 保持 `incomplete`、`close_authorized=false`。
- **交接结论**：自动化实现回归通过；空源、CompanyBrain 基线身份漂移和未证明映射仍未闭环，verify-code 只能如实反向报告，当前不得 close。

### Verify

- **Target**：全部适用 FR/AC、跨 task producer→consumer seam、Reader/Audit/quality 分离。
- **gate_cmd**：T007 的最终命令；RED/GREEN 使用各自配对命令。
- **expected_exit**：T001/T003/T005 为非零；T002/T004/T006/T007 为 0。
- **evidence_path**：各 task card 明确路径；最终为 `quality/evidence/build-plan/T007-final.json`。
- **Oracle**：`ORACLE-COMPILER-FULL`、`ORACLE-SEMANTIC-READER`、`ORACLE-READER-COMPARE`、`ORACLE-FINAL-TASK4`。

### Knowledge

交给 verify-code：真实 89 source manifest/hash、M、case→path/answer/boundary/relations 结果、CompanyBrain manifest/hash、每个 failure 的 `symptom → evidence_ref → first_failing_stage → change_ref → rerun_result`，以及当前 candidate/not_released/released 状态。缺失的事实保持 unknown。

### STOP

- 命令收集失败、测试失败原因不是目标行为、fixture/hash 漂移、实现改了 DO NOT TOUCH 文件、需要人工审查或改变“更好”定义时停止。
- 任何任务不得用旧 `task4-question-oracle.v1.json`、旧 17+3、旧真实产物或历史通过数替代当前快照。

### Done

只有 RED/GREEN 成对执行、T007 聚合完成、一次独立 wh-review 已记录、逐 AC 和交接事实齐全，才能诚实结束 build-plan 并请求用户确认；这里不声称代码已实现。

### Risks and rollback

- **Risk**：编译器继续按关键词分别猜分类/文件名/正文；**Prevention**：T003/T004 强制 semantic node 单一来源；**Rollback**：回 T002。
- **Risk**：评估器给出假“更好”；**Prevention**：T005/T006 固定 M、三轴、N/A/unknown/strict aggregate；**Rollback**：回 T005，报告 undecidable。
- **Risk**：失败留下旧 Reader；**Prevention**：T001/T002 原子 staging 和硬门；**Rollback**：移除候选入口，保留 Audit。

## Final current-snapshot aggregate strategy

- **tier / method**：fullstack；真实 pytest 聚合，使用 `testing-system-blueprint` 的命令/输出绑定。
- **scenarios**：89 source coverage、semantic node/path/title/body/relation/provenance、Reader/Audit separation、case matrix/evaluator、N/A/unknown、negative false hit、cancel/permission/drift、Task2/Task3 seam。
- **command**：T007 的完整 `pytest` 命令。
- **expected exit**：0
- **oracle**：`ORACLE-FINAL-TASK4`；逐 AC 有事实，且不把测试通过当 CompanyBrain 质量通过。
- **fixtures_services**：本地 JSON fixture 和 tmp_path；无服务。
- **evidence_path**：`quality/evidence/build-plan/T007-final.json`
- **coverage limits**：不覆盖未来数万条的性能/成本，不代替真实资料和独立审查。
- **STOP**：命令损坏、AC 缺失、越界或新设计需要时回 owning material。
- **execution_contract**：当前快照只运行一次；失败保留原始输出，回受影响 task，不用全量重跑掩盖局部失败。

## Dependency Graph

- **order**：T001 → T002 → T003 → T004 → T005 → T006 → T007

```text
T001 (source RED) → T002 (source GREEN)
                         ↓
T003 (semantic RED) → T004 (Reader GREEN)
                         ↓
T005 (quality RED) → T006 (quality GREEN) → T007 (FINAL)
```

## Final Boundary Check

- [ ] Phase Goal、Files、Tasks、Verify、Knowledge、STOP、Done、Risks and rollback 完整。
- [ ] 每个 task 只有一张卡和一个完成区；文件属于 Phase NEW/MODIFY。
- [ ] 每个行为变化都有同命令、同 oracle 的 RED→GREEN；T007 只聚合。
- [ ] FR/AC 与 source/decision 双向追溯；未知没有被写成通过。
- [ ] review、test、evidence 是事实记录，不是开工许可证；build-plan 仍等待用户确认。
- **删除证明**：本任务没有删除动作；旧 `task4-question-oracle.v1.json`、正式 Task1–Task3 模块、原始输入和 CompanyBrain 均为 `DO NOT TOUCH`；无删除命令、无删除任务。
