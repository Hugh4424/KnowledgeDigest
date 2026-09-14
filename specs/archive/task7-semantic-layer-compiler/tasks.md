# 任务清单：task7 语义层页面编译器（K1）

- **Input**：`specs/task7-semantic-layer-compiler/decision-log.md`、`specs/task7-semantic-layer-compiler/spec.md`、`specs/task7-semantic-layer-compiler/plan.md`
- **Template version**：`plan-task.v4`

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `plan.md#Phase P1…P7` | 工程方案、文件边界、依赖与回滚 | M：执行前逐 Phase 读 |
| `spec.md#5 功能需求` | FR 行为契约 | M：任务卡 FR/AC 绑定核对 |
| `tasks.md#Phase P1…P7` | 15 张任务卡与完成区 | B：build-code 逐卡执行与回填 |

## Phase P1 — 保真拆块与双方法块清单

### Goal

89 份语料（及 fixture）被拆成整块单元块流，表格行聚合为整块、坏行原样、分类优先级确定；独立第二方法产出可比清单。

### Files

- **NEW**：`src/knowledge_digest/semantic_split.py`; `tests/acceptance/test_task7_split.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：`src/knowledge_digest/compiler.py`（只 import `_paragraph_evidence`）；语料根目录（只读输入）

### Tasks

#### T001 — RED：拆块边界、整块聚合与双方法比对测试先行失败

- **ID**：T001
- **Phase**：Phase P1 — 保真拆块与双方法块清单
- **goal**：让拆块契约的目标断言以失败形态存在（整块聚合/分类优先级/坏行归属/第二方法比对）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-028/R-029 → D-010 → FR-BLK-001/FR-BLK-002 → AC-01
- **输入**：spec FR-BLK-001 边界与优先级契约；plan DEC-001 复用锚点（`_paragraph_evidence` @ compiler.py:2945）
- **依赖**：none
- **并行**：否 — first RED for this behavior
- **FR**：FR-BLK-001 / FR-BLK-002 / FR-AUD-001
- **AC**：AC-01
- **动作**：增加因目标断言失败的测试，不改生产实现
- **精确文件**：`tests/acceptance/test_task7_split.py`
- **boundary**：files: `tests/acceptance/test_task7_split.py`; symbols/regions: 仅新增测试函数
- **输出**：RED 证据目标（pytest 非零 + 失败断言清单）
- **Knowledge**：`_paragraph_evidence(lines, source_id)` 返回 evidence 字典列表（evidence_id/start_line/end_line/text）；FR-BLK-001 优先级 table>list>code>attachment_refs>error_text；整块聚合 = 连续 `|` 行并一块（含坏行）
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"`
- **expected_exit**：1
- **oracle**：`ORACLE-SPLIT-001 {"pass":"五类 fixture 拆块断言全过且坏行/粘 bullet 负例保留","reject":{"input":"带坏行整表、粘 bullet 表、代码块、报错段 fixture","expected_rejection":"表格被按行拆散、坏行被修正或分类优先级错乱（pytest 非零）","observation":"pytest 失败输出中整块聚合断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T001/`
- **STOP**：环境失败、命令损坏、或断言无法以失败形态表达时停止
- **recovery**：build-code 执行者修复测试构造；无法修复回 plan 修设计
- **task risk**：错误 RED（断言写错方向）导致 GREEN 误过
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=整表/坏行/粘 bullet/代码块/报错段五类 fixture 拆块正确 exit 0；失败=表格被按行拆散 exit 1（ORACLE-SPLIT-001 信号）；负例=坏行归属表块、表格粘 bullet 边界不含前导 bullet（同命令同 oracle）
- **fixtures_services**：内联 fixture（测试内构造五类块样本）；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：覆盖 FR-BLK-001 分类与边界；不覆盖跨文件归组（P2）与页面渲染（P4）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `tests/acceptance/test_task7_split.py`，仅增加三组目标行为断言；未修改生产代码。
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"` → exit `1`；3 collected / 3 failed，均为目标断言失败。
- **evidence_refs**：`quality/evidence/build-code/task7/T001/red-result.json`
- **covered_ac**：AC-01 — RED 已证明旧拆块行为不满足整块聚合、边界和第二方法对账；GREEN 结果待 T002。
- **review_fact**：P1 Phase review 已记录于 `quality/evidence/build-code/task7/P1-phase-review.json`；审查发现 3 个 major，均已在 T002 修复，当前 review 状态仍保留为 `incomplete`，因为 immutable attempt 产生于修复前且 Phase review 预算未允许第二次同快照调用。
- **completed_at**：2026-09-14 — T001 RED 与 paired T002 完成
- **执行事实**：2026-09-14：T001 RED 已执行。失败原因为旧 `_paragraph_evidence` 按行拆表、围栏边界不完整，且与独立状态机范围不一致；无 collection/import error。T002 后补足 CRLF/空行/末尾 CR、嵌入错误段、附件语法和长围栏回归，当前 focused gate 8 passed。

#### T002 — GREEN：semantic_split 最小实现使拆块测试通过

- **ID**：T002
- **Phase**：Phase P1 — 保真拆块与双方法块清单
- **goal**：让 T001 的目标断言通过并保留负例（坏行/粘 bullet 不回归）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-028/R-029 → D-010 → FR-BLK-001/FR-BLK-002 → AC-01
- **输入**：T001 的失败断言与已核实实现锚点
- **依赖**：T001
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-BLK-001 / FR-BLK-002 / FR-AUD-001
- **AC**：AC-01
- **动作**：新增 semantic_split：import `_paragraph_evidence` 得行级块 → 聚合连续表格行为整块 → 按优先级分类 → 第二方法状态机扫描器独立产出清单 → 比对
- **精确文件**：`src/knowledge_digest/semantic_split.py`; `tests/acceptance/test_task7_split.py`
- **boundary**：files: `src/knowledge_digest/semantic_split.py`; `tests/acceptance/test_task7_split.py`; symbols/regions: semantic_split 全部新符号
- **输出**：GREEN 可观察结果（pytest exit 0）
- **Knowledge**：T001 产出的真实失败事实；块记录字段（source_path/block_id/content_hash/kind/line_start/line_end/text）
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-SPLIT-001 {"pass":"五类 fixture 拆块断言全过且坏行/粘 bullet 负例保留","reject":{"input":"带坏行整表、粘 bullet 表、代码块、报错段 fixture","expected_rejection":"表格被按行拆散、坏行被修正或分类优先级错乱（pytest 非零）","observation":"pytest 失败输出中整块聚合断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T002/`
- **STOP**：需要弱化测试、扩大边界或新增设计时停止
- **recovery**：回滚实现改动，保 RED 证据，回 plan 修设计
- **task risk**：实现偏离 FR-BLK-001 优先级（如坏行被「修正」）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=五类 fixture 全过 exit 0；失败=任一断言红 exit 1；负例=坏表原样字节保留、粘 bullet 表边界正确（同命令同 oracle）
- **fixtures_services**：同 T001；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：块级行为全覆盖；不覆盖 claim 切分（P3）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `src/knowledge_digest/semantic_split.py`，并扩展 `tests/acceptance/test_task7_split.py`；主扫描器复用 `_paragraph_evidence` 作段落锚点，第二扫描器使用独立 token 规则，保留原始分隔符/空行/CR，输出 mismatch/blocker。
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"` → exit `0`；`9 passed in 0.04s`；canonical receipt `quality/tests/task7/T002-current.json`，hash `555ec8e879e29246e1bba257734244c5d6927ee99c051c5f186b048402c4cf4e`，snapshot `824fb77c386f2ea6abbb0efe1d8591eeb6fad29d`。
- **evidence_refs**：`quality/evidence/build-code/task7/T002/routing.json`; `quality/evidence/build-code/task7/T002/test-strategy.json`; `quality/evidence/build-code/task7/T002/green-result.json`; `quality/evidence/build-code/task7/P1-phase-review.json`; `quality/evidence/build-code/task7/P2-phase-review.json`; canonical `quality/tests/task7/T002-current.json`。
- **covered_ac**：AC-01（6 个 fixture 的主/独立清单相等、坏行/粘 bullet/未闭合代码 blocker 可见）；AC-02 的块级字节保持由 CRLF、空行、末尾 CR 保护测试覆盖。89 份真实语料与端到端覆盖留给 P7。
- **review_fact**：`quality/evidence/build-code/task7/P1-phase-review.json`；canonical result `quality/reviews/results/build-code-simple-a19dfc78-9576-540f-a03f-edff4a23f9a8.json`，3 个 major 已按记录修复；不把修复前 attempt 改写成 clean/pass。
- **completed_at**：2026-09-14
- **执行事实**：2026-09-14：T002 先通过原有 4 个断言，P1 review 发现 3 个 major；随后修复原始分隔符保留、独立分类谓词、嵌入结构后的段落归并。P2 review 又发现长围栏、附件语法和空标题漂移，已修复并增加回归；当前 canonical focused gate 为 9 passed。

### Verify

- **Target**：FR-BLK-001/002、AC-01
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py -q"`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/build-code/task7/T002/`
- **Oracle**：ORACLE-SPLIT-001 全过且负例保留

### Knowledge

块字段形态（含 heading_path）与 FR-BLK-001 优先级表交给 P2/P3。

### STOP

命令损坏、oracle 不符、边界越界或需要新设计时返回 owning material。

### Done

测试、AC 覆盖、review findings、证据和大白话交接事实待 build-code 回填。

### Risks and rollback

- **Risk**：上游锚点漂移
- **Prevention**：单锚点 import + 聚合纯函数化
- **Rollback / recovery**：删除两新文件，无既有面影响

## Phase P2 — 主题归组与显式映射

### Goal

标题名归一化 + product 作用域分组确定性成立；显式主题映射机械生效；模型建议不改变页面成员。

### Files

- **NEW**：`src/knowledge_digest/semantic_group.py`; `config/task7-topic-map.json`; `tests/acceptance/test_task7_group.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：`config/` 其余冻结清单（只读输入）

### Tasks

#### T003 — RED：归组确定性、作用域与显式映射测试先行失败

- **ID**：T003
- **Phase**：Phase P2 — 主题归组与显式映射
- **goal**：让归组契约的目标断言以失败形态存在（归一化/product 作用域/显式映射/建议不改成员）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-021/R-015 → D-003/D-007 → FR-GRP-001/FR-GRP-002 → AC-06
- **输入**：spec FR-GRP-001 归一化规则与 product 作用域；T002 的块字段形态
- **依赖**：T002
- **并行**：否 — first RED for this behavior
- **FR**：FR-GRP-001 / FR-GRP-002
- **AC**：AC-06
- **动作**：增加因目标断言失败的测试，不改生产实现
- **精确文件**：`tests/acceptance/test_task7_group.py`
- **boundary**：files: `tests/acceptance/test_task7_group.py`; symbols/regions: 仅新增测试函数
- **输出**：RED 证据目标（pytest 非零 + 失败断言清单）
- **Knowledge**：归一化 = NFC + 去首尾空白 + 内部空白压缩 + ASCII 小写；product = 顶层目录 slug；显式映射 = `config/task7-topic-map.json` 的 `topic_aliases`（别名→规范主题）与 `audit_only_sources`（audit_only 声明输入，初始空）
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"`
- **expected_exit**：1
- **oracle**：`ORACLE-GROUP-001 {"pass":"同输入两次划分一致、显式映射生效、模型建议不改变成员","reject":{"input":"跨 product 同标题与模型建议改变成员 fixture","expected_rejection":"跨 product 被合并或建议改变页面成员（pytest 非零）","observation":"pytest 失败输出中划分确定性断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T003/`
- **STOP**：环境失败、命令损坏、或断言无法以失败形态表达时停止
- **recovery**：build-code 执行者修复测试构造；无法修复回 plan 修设计
- **task risk**：错误 RED（如把建议改变成员写成合法断言）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=同输入两次划分一致 exit 0；失败=跨 product 同标题被合并 exit 1（ORACLE-GROUP-001 信号）；负例=显式映射机械生效且模型建议输出不改变成员（同命令同 oracle）
- **fixtures_services**：内联 fixture（合成标题栈与块流）；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：覆盖归组规则；不覆盖 slug 生成（P4）与缓存键（P5）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `tests/acceptance/test_task7_group.py`，仅增加归一化、product 作用域、显式映射和模型建议只读断言；未修改生产代码。
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"` → exit `1`；4 collected / 4 failed，均为目标断言失败，无 collection/import error。
- **evidence_refs**：`quality/evidence/build-code/task7/T003/phase-card.md`; `quality/evidence/build-code/task7/T003/red-result.json`; `quality/evidence/build-code/task7/T004/green-result.json`
- **covered_ac**：AC-06 — paired T004 已使归一化、product 作用域、显式映射和建议只读断言通过。
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result; P2 Phase review 已记录在 `quality/evidence/build-code/task7/P2-phase-review.json`
- **completed_at**：2026-09-14
- **执行事实**：2026-09-14：T003 RED 先执行，旧代码下 4 个行为断言失败；T004 后同一 gate 通过。无 collection/import error。

#### T004 — GREEN：semantic_group 实现使归组测试通过

- **ID**：T004
- **Phase**：Phase P2 — 主题归组与显式映射
- **goal**：让 T003 的目标断言通过：确定性划分、product 作用域、显式映射、建议只读报告
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-021/R-015 → D-003/D-007 → FR-GRP-001/FR-GRP-002 → AC-06
- **输入**：T003 的失败断言与 TopicGroup 目标字段
- **依赖**：T003
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-GRP-001 / FR-GRP-002
- **AC**：AC-06
- **动作**：新增 semantic_group（归一化/分组/映射应用/建议输出/audit_only_sources 读取）+ 初始空映射 `config/task7-topic-map.json`（内容为 `{"topic_aliases":{},"audit_only_sources":[]}`，人编辑机器读）
- **精确文件**：`src/knowledge_digest/semantic_group.py`; `config/task7-topic-map.json`; `tests/acceptance/test_task7_group.py`
- **boundary**：files: `src/knowledge_digest/semantic_group.py`; `config/task7-topic-map.json`; `tests/acceptance/test_task7_group.py`; symbols/regions: semantic_group 全部新符号
- **输出**：GREEN 可观察结果（pytest exit 0）
- **Knowledge**：T003 失败事实；`emm for android ` 尾随空格在目录名中的形态由 fixture 固定
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-GROUP-001 {"pass":"同输入两次划分一致、显式映射生效、模型建议不改变成员","reject":{"input":"跨 product 同标题与模型建议改变成员 fixture","expected_rejection":"跨 product 被合并或建议改变页面成员（pytest 非零）","observation":"pytest 失败输出中划分确定性断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T004/`
- **STOP**：需要弱化测试、扩大边界或新增设计时停止
- **recovery**：回滚实现改动，保 RED 证据，回 plan 修设计
- **task risk**：归一化过度合并不同主题
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=划分确定性 + 映射生效 exit 0；失败=建议改变成员 exit 1；负例=缺失映射文件时纯标题名归组（同命令同 oracle）
- **fixtures_services**：同 T003；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：归组行为全覆盖；不覆盖页面拼装
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `src/knowledge_digest/semantic_group.py` 与空的 `config/task7-topic-map.json`；实现标题归一化、product 作用域归组、公共 H2 模块 slug、显式别名、`audit_only_sources` 读取及 report-only 模型建议；T003 测试保留。
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"` → exit `0`；原始 6 passed，P5 repair 后 7 passed；canonical repair receipt `quality/tests/task7/T004-module-repair.json`，hash `3be9f19856ee2271adcc155edca4cc3766b45cf5be1ae8e5003f989f8ecd1312`，snapshot `239472d5952f1bc6348468a3972b6fc78880e703`。
- **evidence_refs**：`quality/evidence/build-code/task7/T003/phase-card.md`; `quality/evidence/build-code/task7/T003/red-result.json`; `quality/evidence/build-code/task7/T004/routing.json`; `quality/evidence/build-code/task7/T004/test-strategy.json`; `quality/evidence/build-code/task7/T004/green-result.json`; `quality/evidence/build-code/task7/P2-phase-review.json`; canonical `quality/tests/task7/T004-current.json`; P5 repair `quality/evidence/build-code/task7/T010/test-capture-current-input.json`; `quality/tests/task7/T004-module-repair.json`
- **covered_ac**：AC-06 — 同输入逆序仍得到相同分组；相同标题仅在 product 内合并；显式映射合并；模型建议输出不改变成员；配置初始为空；slug 碰撞不跨 product 合并。
- **review_fact**：`quality/evidence/build-code/task7/P2-phase-review.json`；canonical review 记录 3 个 major + 1 个 minor，均已修复或移除；current GREEN is the implementation/test fact, not a clean review claim。
- **completed_at**：2026-09-14
- **执行事实**：2026-09-14：T004 实现并修正边界校验后先通过 4 个 P2 acceptance 场景；P2 review 后补齐 product slug 碰撞、公共 H2 一致性、长围栏、附件语法回归，并移除未使用别名；P5 review 后再补齐同产品 module slug 碰撞，当前 repair gate 为 7 passed。真实 89 条语料、claim/page/cache/audit/CLI 仍未覆盖。

### Verify

- **Target**：FR-GRP-001/002、AC-06
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/build-code/task7/T004/`
- **Oracle**：ORACLE-GROUP-001 全过

### Knowledge

TopicGroup 字段与 topic-map 配置形态交给 P4/P5。

### STOP

归一化规则与 spec FR-GRP-001 冲突、或需要语义相似度归组时返回 spec。

### Done

测试、AC 覆盖、review findings、证据待 build-code 回填。

### Risks and rollback

- **Risk**：归一化过度/不足
- **Prevention**：fixture 覆盖空白/大小写/尾随空格
- **Rollback / recovery**：删除三新文件

## Phase P3 — claim 管道与双轨溯源

### Goal

句子级 claim 切分、稳定 claim_id、span 级正文↔旁路映射、被拒导读句锚点登记全部成立。

### Files

- **NEW**：`src/knowledge_digest/semantic_claims.py`; `tests/acceptance/test_task7_claims.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：spec FR-AUD-002 字段清单（只读契约）

### Tasks

#### T005 — RED：claim_id 稳定性、span 映射与被拒导读锚点测试先行失败

- **ID**：T005
- **Phase**：Phase P3 — claim 管道与双轨溯源
- **goal**：让 claim 契约的目标断言以失败形态存在（切分/claim_id/span 映射/被拒导读句登记）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-015/R-019 → D-004/D-005 → FR-AUD-002/FR-CMP-002/FR-CMP-004 → AC-04/AC-11
- **输入**：spec FR-AUD-002 schema（claim_id 含 char 区间 + occurrence_index；span 级映射）
- **依赖**：T002
- **并行**：否 — first RED for this behavior
- **FR**：FR-AUD-002 / FR-CMP-002 / FR-CMP-004
- **AC**：AC-04 / AC-11
- **动作**：增加因目标断言失败的测试，不改生产实现
- **精确文件**：`tests/acceptance/test_task7_claims.py`
- **boundary**：files: `tests/acceptance/test_task7_claims.py`; symbols/regions: 仅新增测试函数
- **输出**：RED 证据目标（pytest 非零 + 失败断言清单）
- **Knowledge**：claim_id = `cl_` + sha256(source_path + 行区间 + char 区间 + occurrence_index + 规范化文本) 前 12 位；occurrence_index 从 1 起；被拒导读句 `page_anchor=intro` 且 retrieval_evidence 必填
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"`
- **expected_exit**：1
- **oracle**：`ORACLE-CLAIM-001 {"pass":"零无锚点 span、重复句不碰撞、被拒导读句 intro 锚点且 evidence 必填","reject":{"input":"同来源同行重复文本与多 claim 句 fixture","expected_rejection":"claim_id 碰撞或正文 span 无旁路记录（pytest 非零）","observation":"pytest 失败输出中 claim_id 稳定性断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T005/`
- **STOP**：环境失败、命令损坏、或断言无法以失败形态表达时停止
- **recovery**：build-code 执行者修复测试构造；无法修复回 plan 修设计
- **task risk**：错误 RED（重复句碰撞断言写反）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=重复句不碰撞 + 多 claim 句逐条映射 exit 0；失败=同来源同行重复文本碰撞 exit 1（ORACLE-CLAIM-001 信号）；负例=被拒导读句有 intro 锚点且 evidence 必填（同命令同 oracle）
- **fixtures_services**：内联 fixture（含重复句/多 claim 句/无依据导读句）；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：claim 级行为；不覆盖旁路落盘（P6）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `tests/acceptance/test_task7_claims.py`，仅增加句子切分、重复 claim、span 与被拒导读断言；未修改生产代码。
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"` → exit `1`；3 collected / 3 failed，均为目标断言失败，无 collection/import error。
- **evidence_refs**：`quality/evidence/build-code/task7/T005/phase-card.md`; `quality/evidence/build-code/task7/T005/red-result.json`; `quality/evidence/build-code/task7/T006/green-result.json`
- **covered_ac**：AC-04 / AC-11 — paired T006 已使 claim span、稳定 ID 和 rejected intro 断言通过。
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result; P3 Phase review 待执行
- **completed_at**：2026-09-14
- **执行事实**：2026-09-14：T005 RED 先执行，旧代码下 3 个行为断言失败；T006 后同一 gate 通过。无 collection/import error。

#### T006 — GREEN：semantic_claims 实现使 claim 测试通过

- **ID**：T006
- **Phase**：Phase P3 — claim 管道与双轨溯源
- **goal**：让 T005 的目标断言通过：切分、稳定 ID、span 映射、被拒导读句登记
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-015/R-019 → D-004/D-005 → FR-AUD-002/FR-CMP-002/FR-CMP-004 → AC-04/AC-11
- **输入**：T005 的失败断言
- **依赖**：T005
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-AUD-002 / FR-CMP-002 / FR-CMP-004
- **AC**：AC-04 / AC-11
- **动作**：新增 semantic_claims：句子级切分（句号/问号/叹号/分号/换行）+ claim_id 生成 + span 映射 + 导读逐句回溯（无依据句登记 status=原文未明确、page_anchor=intro、retrieval_evidence 必填）
- **精确文件**：`src/knowledge_digest/semantic_claims.py`; `tests/acceptance/test_task7_claims.py`
- **boundary**：files: `src/knowledge_digest/semantic_claims.py`; `tests/acceptance/test_task7_claims.py`; symbols/regions: semantic_claims 全部新符号
- **输出**：GREEN 可观察结果（pytest exit 0）
- **Knowledge**：T005 失败事实；切分不切散原文行
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-CLAIM-001 {"pass":"零无锚点 span、重复句不碰撞、被拒导读句 intro 锚点且 evidence 必填","reject":{"input":"同来源同行重复文本与多 claim 句 fixture","expected_rejection":"claim_id 碰撞或正文 span 无旁路记录（pytest 非零）","observation":"pytest 失败输出中 claim_id 稳定性断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T006/`
- **STOP**：需要弱化测试、扩大边界或新增设计时停止
- **recovery**：回滚实现改动，保 RED 证据，回 plan 修设计
- **task risk**：切分吞掉中日文标点边界
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=零无锚点 span + 重复句不碰撞 exit 0；失败=任一断言红 exit 1；负例=被拒导读句不进事实分母（同命令同 oracle）
- **fixtures_services**：同 T005；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：claim 行为全覆盖；不覆盖 sources.jsonl 落盘（P6）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `src/knowledge_digest/semantic_claims.py`；实现句子/换行切分、原文 char/line span、occurrence-aware `claim_id`、narrative provenance、intro grounding 与 `原文未明确` rejected claim。
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"` → exit `0`；`6 passed in 0.04s`；canonical receipt `quality/tests/task7/T006-current-v2.json`，hash `d6492345d240d0d27a927483e2bdf626f609c9cc0a92f934daea3abaf50d4736`，snapshot `418d015f0d777a7dfa182834772d5ab48ff005af`。
- **evidence_refs**：`quality/evidence/build-code/task7/T005/phase-card.md`; `quality/evidence/build-code/task7/T005/red-result.json`; `quality/evidence/build-code/task7/T006/routing.json`; `quality/evidence/build-code/task7/T006/test-strategy.json`; `quality/evidence/build-code/task7/T006/green-result.json`; `quality/evidence/build-code/task7/P3-phase-review.json`; canonical `quality/tests/task7/T006-current-v2.json`; P4 review finding repair recorded in `quality/evidence/build-code/task7/P4-review-request.json`
- **covered_ac**：AC-04 / AC-11 — 句子逐条映射到来源行/char、重复文本 ID 不碰撞、被拒导读带 intro 锚点与 retrieval evidence 且不进 fact denominator。
- **review_fact**：`quality/evidence/build-code/task7/P3-phase-review.json`；canonical review 记录 2 个 major + 2 个 minor，均已修复；current GREEN is the implementation/test fact, not a clean review claim。
- **completed_at**：2026-09-14
- **执行事实**：2026-09-14：T006 先通过 3 个 P3 acceptance 场景；P3 review 后增加 period-token 与 surrogateescape 回归，P4 review 又补充重复边界标点回归；当前 canonical P3 gate 为 6 passed。sources.jsonl 落盘、页面锚点、缓存、审计、CLI、真实 89 条语料仍未覆盖。

### Verify

- **Target**：FR-AUD-002/CMP-002/004、AC-04/11
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_claims.py -q"`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/build-code/task7/T006/`
- **Oracle**：ORACLE-CLAIM-001 全过

### Knowledge

Claim 记录形态交给 P4/P6。

### STOP

切分规则需改写原文、或 claim_id 稳定性无法保证时返回 spec。

### Done

测试、AC 覆盖、review findings、证据待 build-code 回填。

### Risks and rollback

- **Risk**：句子切分边界
- **Prevention**：fixture 覆盖中英文标点
- **Rollback / recovery**：删除两新文件

## Phase P4 — 模型缓存

### Goal

复合键缓存冻结、命中不重调、缺缓存调用写回、改一字节必失效。

### Files

- **NEW**：`src/knowledge_digest/semantic_cache.py`; `tests/acceptance/test_task7_cache.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：`~/.config/knowledge-digest/config.json`（用户凭据，只读）；凭据禁止写入代码/产物/缓存

### Tasks

#### T007 — RED：缓存键构成、命中与失效负例测试先行失败

- **ID**：T007
- **Phase**：Phase P4 — 模型缓存
- **goal**：让缓存契约的目标断言以失败形态存在（复合键/命中不重调/缺缓存写回/负例失效）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-022/R-023 → D-007 → FR-CMP-003 → AC-06/AC-12
- **输入**：spec FR-CMP-003 键构成与页面复合输入指纹定义
- **依赖**：T004
- **并行**：否 — first RED for this behavior
- **FR**：FR-CMP-003
- **AC**：AC-06 / AC-12
- **动作**：增加因目标断言失败的测试，不改生产实现
- **精确文件**：`tests/acceptance/test_task7_cache.py`
- **boundary**：files: `tests/acceptance/test_task7_cache.py`; symbols/regions: 仅新增测试函数
- **输出**：RED 证据目标（pytest 非零 + 失败断言清单）
- **Knowledge**：缓存键 = 模型标识 + 提示模板版本 + 主题映射版本 + 页面复合输入指纹（成员 content_hash 按主题键升序拼接 + 主题键）；命中不重调；缺缓存调用并写回
- **verification_role**：RED
- **paired_task**：T008
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"`
- **expected_exit**：1
- **oracle**：`ORACLE-CACHE-001 {"pass":"复合键命中不重调、缺缓存调用写回、成员变化负例必失效","reject":{"input":"改合并页非主来源与 fake provider 计数 fixture","expected_rejection":"成员变化后仍命中旧缓存或调用数异常（pytest 非零）","observation":"pytest 失败输出中缓存失效断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T007/`
- **STOP**：环境失败、命令损坏、或断言无法以失败形态表达时停止
- **recovery**：build-code 执行者修复测试构造；无法修复回 plan 修设计
- **task risk**：错误 RED（fake provider 计数断言错误）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=改合并页非主来源必失效 exit 0；失败=成员变化后仍命中旧缓存 exit 1（ORACLE-CACHE-001 信号）；负例=同输入两次读取字节一致（同命令同 oracle）
- **fixtures_services**：内联 fake provider（计数调用）；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：缓存行为；不覆盖 provider 真实调用（端到端另验）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `tests/acceptance/test_task7_cache.py` 三个行为断言；未修改生产实现
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"` → exit 1，3 collected / 3 failed，失败均为目标 API 尚未实现的断言
- **evidence_refs**：`quality/evidence/build-code/task7/T007/red-result.json`
- **covered_ac**：AC-06 / AC-12（RED 目标断言）
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result
- **completed_at**：2026-09-14
- **执行事实**：T007 RED 已真实执行；未发生 collection/import error；失败清单见 `red-result.json`。实现未变更。

#### T008 — GREEN：semantic_cache 实现使缓存测试通过

- **ID**：T008
- **Phase**：Phase P4 — 模型缓存
- **goal**：让 T009 的目标断言通过：键变必失效（含改合并页非主来源负例）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-022/R-023 → D-007 → FR-CMP-003 → AC-06/AC-12
- **输入**：T009 的失败断言
- **依赖**：T007
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-CMP-003
- **AC**：AC-06 / AC-12
- **动作**：新增 semantic_cache：JSONL 条目（cache_key/model_id/prompt_version/topic_map_version/result/created_from_fingerprint）、目录 `cache/model-cache/`、miss→call→write-back、不含凭据
- **精确文件**：`src/knowledge_digest/semantic_cache.py`; `tests/acceptance/test_task7_cache.py`
- **boundary**：files: `src/knowledge_digest/semantic_cache.py`; `tests/acceptance/test_task7_cache.py`; symbols/regions: semantic_cache 全部新符号
- **输出**：GREEN 可观察结果（pytest exit 0）
- **Knowledge**：T009 失败事实；目录约定交 P7 入 .gitignore
- **verification_role**：GREEN
- **paired_task**：T007
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-CACHE-001 {"pass":"复合键命中不重调、缺缓存调用写回、成员变化负例必失效","reject":{"input":"改合并页非主来源与 fake provider 计数 fixture","expected_rejection":"成员变化后仍命中旧缓存或调用数异常（pytest 非零）","observation":"pytest 失败输出中缓存失效断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T008/`
- **STOP**：需要弱化测试、扩大边界或新增设计时停止
- **recovery**：回滚实现改动，保 RED 证据，回 plan 修设计
- **task risk**：缓存条目意外包含凭据或路径绝对化
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=负例失效 + 命中不重调 exit 0；失败=任一红 exit 1；负例=缓存缺失时重新调用并写回（同命令同 oracle）
- **fixtures_services**：同 T009；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：缓存行为全层；不覆盖 provider 不可用产品语义（P7 SCN-007）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `src/knowledge_digest/semantic_cache.py`；保留并执行 T007 的三条缓存行为测试；未读取或修改用户配置凭据
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"` → exit 0；`4 passed in 0.03s`；canonical receipt `quality/tests/task7/T008-current-v2.json`，hash `022cc67ebac73996ff1751972d9ce130173bd219815134198fc4d178bdea27c8`，snapshot `418d015f0d777a7dfa182834772d5ab48ff005af`
- **evidence_refs**：`quality/evidence/build-code/task7/T007/phase-card.md`; `quality/evidence/build-code/task7/T007/red-result.json`; `quality/evidence/build-code/task7/T008/routing.json`; `quality/evidence/build-code/task7/T008/test-strategy.json`; `quality/evidence/build-code/task7/T008/green-result.json`; `quality/evidence/build-code/task7/P4-review-request.json`; canonical `quality/tests/task7/T008-current-v2.json`
- **covered_ac**：AC-06 / AC-12 — 复合键四项材料、全部成员指纹、miss 写回、hit 不重调和非主来源变化失效均通过；凭据字段在持久化前拒绝
- **review_fact**：P4 build-code Phase review 已执行，canonical result `quality/reviews/results/build-code-simple-163cdf86-ec71-59d2-a550-e51c8a0e4f4b.json`；3 个 minor 已按 review 建议修复；未把修复前结果改写为 clean
- **completed_at**：2026-09-14
- **执行事实**：2026-09-14：T008 新增任务级 JSONL 缓存；当前 canonical focused gate 为 4 passed。缓存条目只包含六个约定字段，结果含凭据字段时 fail-closed；P4 review 的 3 个 minor 已修复，当前 focused receipt 已重采。

### Verify

- **Target**：FR-CMP-003、AC-06/12
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_cache.py -q"`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/build-code/task7/T008/`
- **Oracle**：ORACLE-CACHE-001 全过

### Knowledge

缓存条目 schema 与目录约定交给 P7。

### STOP

需把凭据写入缓存、或键无法覆盖成员来源变化时返回 spec FR-CMP-003。

### Done

测试、AC 覆盖、review findings、证据待 build-code 回填。

### Risks and rollback

- **Risk**：缓存目录误入 git
- **Prevention**：P7 .gitignore 行 + T010 断言路径相对化
- **Rollback / recovery**：删除两新文件并清理 .gitignore 行

## Phase P5 — 页面渲染、命名与分页

### Goal

16 字段 frontmatter、英文 slug（不动点+批内唯一+回退链）、`[[wikilink]]` 相关页面、300 行分页与 oversized 附录 part、读者侧出处行、附件标注全部落地。

### Files

- **NEW**：`src/knowledge_digest/semantic_page.py`; `tests/acceptance/test_task7_pages.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：真实 CompanyBrain 页面（同构基准只读抽样，不写入）

### Tasks

#### T009 — RED：页面结构、slug 契约、双链与分页测试先行失败

- **ID**：T009
- **Phase**：Phase P5 — 页面渲染、命名与分页
- **goal**：让页面契约的目标断言以失败形态存在（16 字段/slug 不动点且唯一/双链/分页/逐字节块/出处行）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-013/R-035/R-036/R-028/R-016 → D-005/D-006/D-015/D-010/D-013 → FR-PUB-001/FR-PUB-003/FR-CMP-001 → AC-02/AC-03/AC-07
- **输入**：spec FR-PUB-001/003 与 FR-CMP-001；T004 的 TopicGroup、T006 的 Claim 字段
- **依赖**：T006 / T008
- **并行**：否 — first RED for this behavior
- **FR**：FR-PUB-001 / FR-PUB-003 / FR-CMP-001
- **AC**：AC-02 / AC-03 / AC-07
- **动作**：增加因目标断言失败的测试，不改生产实现
- **精确文件**：`tests/acceptance/test_task7_pages.py`
- **boundary**：files: `tests/acceptance/test_task7_pages.py`; symbols/regions: 仅新增测试函数
- **输出**：RED 证据目标（pytest 非零 + 失败断言清单）
- **Knowledge**：16 字段值域（真实 CompanyBrain 抽样锚定）；slug = gbrain 不动点；碰撞后缀按主题键字典序；出处行 = 「原始文件名 + 文件内标题」无行号；附件标注固定模板句
- **verification_role**：RED
- **paired_task**：T010
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"`
- **expected_exit**：1
- **oracle**：`ORACLE-PAGE-001 {"pass":"16 字段断言全过、slug 不动点且批内唯一、双链可解析、300 行分页与 oversized 附录正确","reject":{"input":"缺字段 frontmatter、slug 碰撞、双链悬空 fixture","expected_rejection":"字段缺失或 slug 碰撞或附录 part 缺失标注（pytest 非零）","observation":"pytest 失败输出中结构断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T009/`
- **STOP**：环境失败、命令损坏、或断言无法以失败形态表达时停止
- **recovery**：build-code 执行者修复测试构造；无法修复回 plan 修设计
- **task risk**：错误 RED（字段值断言与 spec 值域不符）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=抽样页 16 字段断言全过 exit 0；失败=slug 碰撞或缺字段 exit 1（ORACLE-PAGE-001 信号）；负例=超 300 行参考块入附录 part、双链指向存在页（同命令同 oracle）
- **fixtures_services**：内联 fixture（合成 TopicGroup+Claim+块）；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：页面结构与字节；不覆盖审计落盘（P6）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `tests/acceptance/test_task7_pages.py`，仅增加目标断言；未修改生产代码
- **executed_commands**：`node skills/test-routing-advisor/scripts/route.mjs /dev/stdin`（selected_tier=fullstack）；`bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"`（exit 1，4 collected/4 failed）
- **evidence_refs**：`quality/evidence/build-code/task7/T009/phase-card.md`; `quality/evidence/build-code/task7/T009/routing.json`; `quality/evidence/build-code/task7/T009/test-strategy.json`; `quality/evidence/build-code/task7/T009/red-result.json`
- **covered_ac**：AC-02 / AC-03 / AC-07（RED target assertions）
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result
- **completed_at**：2026-09-14
- **执行事实**：测试成功收集且全部在 API 缺失断言处失败；无 collection error；生产实现未改动

#### T010 — GREEN：semantic_page 实现使页面测试通过

- **ID**：T010
- **Phase**：Phase P5 — 页面渲染、命名与分页
- **goal**：让 T007 的目标断言通过并保留负例
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-013/R-035/R-036/R-028/R-016 → D-005/D-006/D-015/D-010/D-013 → FR-PUB-001/FR-PUB-003/FR-CMP-001 → AC-02/AC-03/AC-07
- **输入**：T007 的失败断言；缓存接口约定（P5 的 semantic_cache 接口先行约定）
- **依赖**：T009
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-PUB-001 / FR-PUB-003 / FR-CMP-001
- **AC**：AC-02 / AC-03 / AC-07
- **动作**：新增 semantic_page：frontmatter 渲染、slug 主路径（模型译文）+ ASCII 段回退、批内唯一后缀、相关页面 wikilink、300 行分页与 oversized 附录 part、出处行与附件标注
- **精确文件**：`src/knowledge_digest/semantic_page.py`; `tests/acceptance/test_task7_pages.py`
- **boundary**：files: `src/knowledge_digest/semantic_page.py`; `tests/acceptance/test_task7_pages.py`; symbols/regions: semantic_page 全部新符号
- **输出**：GREEN 可观察结果（pytest exit 0）
- **Knowledge**：T007 失败事实；slug 回退链（DEC-002）
- **verification_role**：GREEN
- **paired_task**：T009
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-PAGE-001 {"pass":"16 字段断言全过、slug 不动点且批内唯一、双链可解析、300 行分页与 oversized 附录正确","reject":{"input":"缺字段 frontmatter、slug 碰撞、双链悬空 fixture","expected_rejection":"字段缺失或 slug 碰撞或附录 part 缺失标注（pytest 非零）","observation":"pytest 失败输出中结构断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T010/`
- **STOP**：需要弱化测试、扩大边界或新增设计时停止
- **recovery**：回滚实现改动，保 RED 证据，回 plan 修设计
- **task risk**：回退 slug 误用于主路径（缓存可用时）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=全部断言过 exit 0；失败=任一红 exit 1；负例=中文主题键无缓存时走 ASCII 段回退（同命令同 oracle）
- **fixtures_services**：同 T007；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：页面渲染全层；不覆盖端到端（P7）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `src/knowledge_digest/semantic_page.py`；补齐页面断言 fixture；修复 P5 审查发现的 slug 全局保留、claim 精确块绑定、首个 part 300 行边界；同时修复 `semantic_group.py` 的同产品 module slug 碰撞并补回归测试
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"`（初次 exit 0，4 passed；修复后 exit 0，7 passed）；`bash -c "uv run --frozen pytest tests/acceptance/test_task7_group.py -q"`（修复后 exit 0，7 passed）；WorkflowHub `verify --action=execute`（当前 receipt 已写入）
- **evidence_refs**：`quality/evidence/build-code/task7/T009/phase-card.md`; `quality/evidence/build-code/task7/T009/routing.json`; `quality/evidence/build-code/task7/T009/test-strategy.json`; `quality/evidence/build-code/task7/T009/red-result.json`; `quality/evidence/build-code/task7/T010/test-capture-input.json`; `quality/evidence/build-code/task7/T010/test-capture-current-input.json`; `quality/evidence/build-code/task7/T010/green-result.json`; `quality/evidence/build-code/task7/P5-review-request.json`; `quality/evidence/build-code/task7/P5-phase-review.json`; `quality/tests/task7/T010-current-v2.json`; `quality/tests/task7/T004-module-repair.json`
- **covered_ac**：AC-02 / AC-03 / AC-07
- **review_fact**：`quality/evidence/build-code/task7/P5-phase-review.json`；canonical review 记录 4 个 major + 1 个 minor，全部已修复；review fact 仍为 `recorded_with_findings`，不是 clean review
- **completed_at**：2026-09-14
- **执行事实**：页面测试当前 7/7 通过；receipt `quality/tests/task7/T010-current-v2.json`，receipt_hash=`482e485b64ecf9e9425d5db2859def3a7fdbb332291c0e791234a21d71d7390b`，snapshot_tree=`239472d5952f1bc6348468a3972b6fc78880e703`；归组 module repair 测试当前 7/7 通过，receipt=`quality/tests/task7/T004-module-repair.json`

### Verify

- **Target**：FR-PUB-001/003/CMP-001、AC-02/03/07
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_pages.py -q"`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/build-code/task7/T010/`
- **Oracle**：ORACLE-PAGE-001 全过且负例保留

### Knowledge

页面字节契约交给 P6 审计与 P7 端到端。

### STOP

slug 回退链穷尽、或 16 字段值与真实 CompanyBrain 抽样不符时返回 spec FR-PUB-001。

### Done

测试、AC 覆盖、review findings、证据待 build-code 回填。

### Risks and rollback

- **Risk**：slug 碰撞编号误配
- **Prevention**：按主题键字典序编号 fixture
- **Rollback / recovery**：删除两新文件

## Phase P6 — 审计与机读批次状态

### Goal

五件 `_audit/` 产物、五类状态推导（audit_only 声明式输入）、覆盖不变量（含 duplicate_alias 别名分支）、批次状态、成本记账全部机读可验。

### Files

- **NEW**：`src/knowledge_digest/semantic_audit.py`; `tests/acceptance/test_task7_audit.py`
- **MODIFY**：N/A — 本 Phase 无既有文件修改
- **DO NOT TOUCH**：冻结清单（对账基准只读）

### Tasks

#### T011 — RED：五件审计 schema、五类状态与覆盖不变量测试先行失败

- **ID**：T011
- **Phase**：Phase P6 — 审计与机读批次状态
- **goal**：让审计契约的目标断言以失败形态存在（五件 schema/状态推导/覆盖/成本记账）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-014/R-024/R-025/R-034 → D-008/D-009/D-011 → FR-AUD-001/FR-AUD-003/FR-AUD-004/FR-AUD-005 → AC-05/AC-08/AC-12/AC-13
- **输入**：spec FR-AUD-001/003/004/005 与 AC-13 覆盖不变量；expected_status 分布（present=88/empty=1）作 fixture 依据
- **依赖**：T008 / T010
- **并行**：否 — first RED for this behavior
- **FR**：FR-AUD-001 / FR-AUD-003 / FR-AUD-004 / FR-AUD-005
- **AC**：AC-05 / AC-08 / AC-12 / AC-13
- **动作**：增加因目标断言失败的测试，不改生产实现
- **精确文件**：`tests/acceptance/test_task7_audit.py`
- **boundary**：files: `tests/acceptance/test_task7_audit.py`; symbols/regions: 仅新增测试函数
- **输出**：RED 证据目标（pytest 非零 + 失败断言清单）
- **Knowledge**：audit_only 需声明式输入（task5 expected_status 或运行配置）+ 程序核验；duplicate_alias 别名承载分支（alias_of + canonical_block_id）；真实 0 计数附 reason
- **verification_role**：RED
- **paired_task**：T012
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"`
- **expected_exit**：1
- **oracle**：`ORACLE-AUDIT-001 {"pass":"五件 schema 合规、五类状态逐类正确、覆盖双向一致、成本真实记账","reject":{"input":"五类状态与重复来源 fixture","expected_rejection":"第三态块存在、重复来源发两页或真实 0 无 reason（pytest 非零）","observation":"pytest 失败输出中覆盖/状态断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T011/`
- **STOP**：环境失败、命令损坏、或断言无法以失败形态表达时停止
- **recovery**：build-code 执行者修复测试构造；无法修复回 plan 修设计
- **task risk**：错误 RED（fixture 五类状态构造错）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=五类 fixture 逐类核对 exit 0；失败=重复来源发两页或第三态块存在 exit 1（ORACLE-AUDIT-001 信号）；负例=真实 0 调用附 reason 合法（同命令同 oracle）
- **fixtures_services**：内联 fixture（五类状态样本 + 合成管道事实）；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：审计 schema 与状态；不覆盖端到端出批（P7）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `tests/acceptance/test_task7_audit.py`，仅增加五件审计产物、来源/claim 状态、覆盖与成本目标断言；未修改生产代码
- **executed_commands**：`node skills/test-routing-advisor/scripts/route.mjs /dev/stdin`（selected_tier=fullstack）；`bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"`（exit 1，6 collected/6 failed）
- **evidence_refs**：`quality/evidence/build-code/task7/T011/phase-card.md`; `quality/evidence/build-code/task7/T011/routing.json`; `quality/evidence/build-code/task7/T011/test-strategy.json`; `quality/evidence/build-code/task7/T011/red-result.json`
- **covered_ac**：AC-05 / AC-08 / AC-12 / AC-13（RED target assertions）
- **review_fact**：N/A — RED task is reviewed with its paired GREEN Phase result
- **completed_at**：2026-09-14
- **执行事实**：测试正常收集，6 个测试全部在 `semantic_audit.build_audit is not implemented` 目标断言失败；无 collection error；生产实现未改动

#### T012 — GREEN：semantic_audit 实现使审计测试通过

- **ID**：T012
- **Phase**：Phase P6 — 审计与机读批次状态
- **goal**：让 T011 的目标断言通过：五件产物、状态推导、覆盖校验、成本记账
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-014/R-024/R-025/R-034 → D-008/D-009/D-011 → FR-AUD-001/FR-AUD-003/FR-AUD-004/FR-AUD-005 → AC-05/AC-08/AC-12/AC-13
- **输入**：T011 的失败断言
- **依赖**：T011
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-AUD-001 / FR-AUD-003 / FR-AUD-004 / FR-AUD-005
- **AC**：AC-05 / AC-08 / AC-12 / AC-13
- **动作**：新增 semantic_audit：五件产物写入、五类状态推导、覆盖不变量校验（含别名分支）、批次状态、成本记账（真实 0 附 reason）
- **精确文件**：`src/knowledge_digest/semantic_audit.py`; `tests/acceptance/test_task7_audit.py`
- **boundary**：files: `src/knowledge_digest/semantic_audit.py`; `tests/acceptance/test_task7_audit.py`; symbols/regions: semantic_audit 全部新符号
- **输出**：GREEN 可观察结果（pytest exit 0）
- **Knowledge**：T011 失败事实；manifest 最后落盘约定
- **verification_role**：GREEN
- **paired_task**：T011
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-AUDIT-001 {"pass":"五件 schema 合规、五类状态逐类正确、覆盖双向一致、成本真实记账","reject":{"input":"五类状态与重复来源 fixture","expected_rejection":"第三态块存在、重复来源发两页或真实 0 无 reason（pytest 非零）","observation":"pytest 失败输出中覆盖/状态断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T012/`
- **STOP**：需要弱化测试、扩大边界或新增设计时停止
- **recovery**：回滚实现改动，保 RED 证据，回 plan 修设计
- **task risk**：覆盖校验放过第三态块
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测
- **scenarios / commands / expected exit / oracle**：成功=双向覆盖一致 exit 0；失败=任一断言红 exit 1；负例=audit_only 未声明而块零入 products 时状态冲突进阻塞（同命令同 oracle）
- **fixtures_services**：同 T011；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：审计全层；不覆盖 CLI 面（P7）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `src/knowledge_digest/semantic_audit.py`，实现五件审计产物、来源/claim 状态推导、canonical/duplicate_alias 覆盖校验、批次状态、阻塞清单、真实成本与零值原因、manifest-last 写入；保留 T011 测试作为行为契约
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"`（exit 0，6 passed）；canonical capture `stage-runtime verify --action=execute`（exit 0）
- **evidence_refs**：`quality/evidence/build-code/task7/T011/phase-card.md`; `quality/evidence/build-code/task7/T011/routing.json`; `quality/evidence/build-code/task7/T011/test-strategy.json`; `quality/evidence/build-code/task7/T011/red-result.json`; `quality/evidence/build-code/task7/T012/test-capture-input.json`; `quality/evidence/build-code/task7/T012/test-capture-repair-input.json`; `quality/evidence/build-code/task7/T012/green-result.json`; `quality/evidence/build-code/task7/P6-review-request.json`; `quality/evidence/build-code/task7/P6-phase-review.json`; canonical `quality/tests/task7/T012-current-v2.json`
- **covered_ac**：AC-05 / AC-08 / AC-12 / AC-13
- **review_fact**：`quality/evidence/build-code/task7/P6-phase-review.json`；canonical review `62dfd6bc-910d-5c5a-a43a-ee0481be2b55` 记录 4 个 major，均已按记录修复；immutable review 仍为 `recorded_with_findings`，未改写为 clean
- **completed_at**：2026-09-14
- **执行事实**：T011 正常收集并以 6 个目标断言失败；首版实现 focused gate 为 6 passed；P6 review 后新增 4 个回归，当前 focused gate 为 10 passed。canonical receipt `quality/tests/task7/T012-current-v2.json`（sha256 `3f3516e3d865b4dc8661f7f88b8bfe9a45c8ffd6c34c428c3161aedc89b1361a`，snapshot_tree `bd98ed0c2e47cd9407c0f890d44b1b73e73bdea1`，output_hash `e01d5a0d2e778d7b370c61303769113b4572a385a766aecc1ce0b056fc7d16aa`）；P6 review 发现的 4 个 major 已修复，但 immutable review 保留 `recorded_with_findings`，故本任务完成不等于 clean review

### Verify

- **Target**：FR-AUD-001/003/004/005、AC-05/08/12/13
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_audit.py -q"`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/build-code/task7/T012/`
- **Oracle**：ORACLE-AUDIT-001 全过

### Knowledge

manifest 最后落盘约定与状态词表交给 P7 骨架批次。

### STOP

五类 fixture 无法构造、或覆盖校验需要第三态时返回 spec FR-AUD-003/AC-13。

### Done

测试、AC 覆盖、review findings、证据待 build-code 回填。

### Risks and rollback

- **Risk**：状态推导与正文漂移
- **Prevention**：声明式输入 + 程序核验
- **Rollback / recovery**：删除两新文件

## Phase P7 — 命令切换与端到端

### Goal

`digest` 默认分支执行新语义编译；旧行为迁至 scripts/ 可独立运行；对账骨架批次、计划打印、端到端小语料出批、AC-10 基线 16 节点冻结。

### Files

- **NEW**：`src/knowledge_digest/semantic_compiler.py`; `src/knowledge_digest/semantic_cli.py`; `scripts/legacy_digest_reference.py`; `tests/acceptance/test_task7_e2e.py`; `tests/fixtures/task7_e2e/`
- **MODIFY**：`src/knowledge_digest/simple_cli.py`; `.gitignore`; `AGENTS.md`
- **DO NOT TOUCH**：`src/knowledge_digest/compiler.py` 等旧模块（legacy 脚本只调不改）；`docs/adr/`

### Tasks

#### T013 — RED：对账、骨架批次、digest 新行为与基线节点测试先行失败

- **ID**：T013
- **Phase**：Phase P7 — 命令切换与端到端
- **goal**：让端到端契约的目标断言以失败形态存在（对账/骨架批次/计划打印/digest 新行为/基线 16 节点）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-011/R-026/R-041/R-037 → D-002/D-011/D-016/D-018 → FR-CLI-001/FR-SRC-001/FR-SRC-002/FR-PUB-002/FR-REG-001 → AC-08/AC-09/AC-10/AC-01
- **输入**：spec FR-SRC-001/002、FR-CLI-001；基线 16 节点 ID 清单（plan Technical Context 实测）
- **依赖**：T012
- **并行**：否 — first RED for this behavior
- **FR**：FR-CLI-001 / FR-SRC-001 / FR-SRC-002 / FR-PUB-002 / FR-REG-001
- **AC**：AC-08 / AC-09 / AC-10 / AC-01
- **动作**：增加因目标断言失败的测试，不改生产实现
- **精确文件**：`tests/acceptance/test_task7_e2e.py`; `tests/fixtures/task7_e2e/`
- **boundary**：files: `tests/acceptance/test_task7_e2e.py`; `tests/fixtures/task7_e2e/`; symbols/regions: 仅新增测试函数与 fixture 语料
- **输出**：RED 证据目标（pytest 非零 + 失败断言清单）
- **Knowledge**：冻结清单对账基准（task4 coverage v1，semantic_cli 支持 `--manifest` 传配套小清单）；骨架批次 = README + run-metrics(0+reason) + manifest(blocked)；基线 16 节点精确清单（含 1×test_task0_runtime_audit + 15×test_task2a_reader_bundle 及各自根因）冻结于 plan.md Technical Context；SCN-007 三态矩阵的逐项断言点
- **verification_role**：RED
- **paired_task**：T014
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_e2e.py -q"`
- **expected_exit**：1
- **oracle**：`ORACLE-E2E-001 {"pass":"小语料端到端出批且 manifest 机读、digest 走新路径、骨架批次与基线节点集合不变","reject":{"input":"对账差异、provider 三态、写中断注入 fixture","expected_rejection":"digest 仍走旧路径或骨架/中断语义错误（pytest 非零）","observation":"pytest 失败输出中命令面断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T013/`
- **STOP**：环境失败、命令损坏、或断言无法以失败形态表达时停止
- **recovery**：build-code 执行者修复测试构造；无法修复回 plan 修设计
- **task risk**：错误 RED（端到端 fixture 构造不当）
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；目标单测 + 邻接集成
- **scenarios / commands / expected exit / oracle**：成功=小语料端到端出批且 manifest 机读 exit 0；失败=digest 仍走旧路径 exit 1（ORACLE-E2E-001 信号）；负例=① 对账差异时骨架批次 + blocked 且基线节点集合不变；② SCN-007 三态：缓存命中正常/缺缓存可调用写回/缺缓存不可用时回退标题+空导读+同义缺席+阻塞项+run_status=complete；③ 同批两次运行 products 与 _audit 比对范围字节一致（AC-06）；④ 写文件中途注入失败 → manifest interrupted/blocked 且半成品保留（AC-08）；⑤ 计划调用数 ≤ 主题数×2+20 且实际 ≤ 计划×1.5、调用数不随 claim/块数线性增长、成功与失败运行 token 真实（AC-12）（同命令同 oracle）
- **fixtures_services**：`tests/fixtures/task7_e2e/`（T013 构造：小语料 + 配套 manifest.json + fake provider）；进程内直调 + 一次 subprocess CLI 冒烟；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：命令面与端到端；不覆盖真实 provider 调用（fake provider 注入）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `tests/acceptance/test_task7_e2e.py` 与 `tests/fixtures/task7_e2e/`；覆盖清单对账、骨架批次、SCN-007 三态、复跑稳定性、写入中断、CLI 分发、legacy 脚本和 AC-10 基线节点。
- **executed_commands**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_e2e.py -q"` → exit `1`；10 collected，9 failed，1 skipped；无 collection/import error。
- **evidence_refs**：`quality/evidence/build-code/task7/T013/phase-card.md`; `quality/evidence/build-code/task7/T013/routing.json`; `quality/evidence/build-code/task7/T013/test-strategy.json`; `quality/evidence/build-code/task7/T013/red-result.json`。
- **covered_ac**：AC-01 / AC-08 / AC-09 / AC-10 / AC-12；RED 失败事实已由 T014 GREEN 配对闭合。
- **review_fact**：RED 作为 P7 配对任务随 T014 结果记录；P7 唯一 phase review 另见 `P7-phase-review.json`，其状态为 `recorded_unavailable`，不作 clean review 声明。
- **completed_at**：2026-09-14
- **执行事实**：目标断言先以 9 个失败、1 个显式跳过的 RED 形态存在；失败均指向尚未实现的 semantic compiler/CLI/legacy 载体，无命令损坏或 collection error。

#### T014 — GREEN：semantic_compiler/semantic_cli/legacy 脚本与入口改派

- **ID**：T014
- **Phase**：Phase P7 — 命令切换与端到端
- **goal**：让 T013 的目标断言通过：digest 新行为、旧行为脚本化、骨架批次、基线冻结
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：R-011/R-026/R-041/R-037 → D-002/D-011/D-016/D-018 → FR-CLI-001/FR-SRC-001/FR-SRC-002/FR-PUB-002/FR-REG-001 → AC-08/AC-09/AC-10/AC-01
- **输入**：T013 的失败断言；P1-P6 全部模块
- **依赖**：T013
- **并行**：否 — RED/GREEN 必须串行
- **FR**：FR-CLI-001 / FR-SRC-001 / FR-SRC-002 / FR-PUB-002 / FR-REG-001
- **AC**：AC-08 / AC-09 / AC-10 / AC-01
- **动作**：新增 semantic_compiler（编排+SCN-007 矩阵+预检计划打印）与 semantic_cli（参数面）；simple_cli.py 默认分支改派新链路（历史 flag 明确报错指向 legacy 脚本，含 --no-llm）；新增 scripts/legacy_digest_reference.py 承载旧行为；.gitignore 加 `cache/` 行；AGENTS.md 使用说明同步
- **精确文件**：`src/knowledge_digest/semantic_compiler.py`; `src/knowledge_digest/semantic_cli.py`; `scripts/legacy_digest_reference.py`; `tests/acceptance/test_task7_e2e.py`; `tests/fixtures/task7_e2e/`; `src/knowledge_digest/simple_cli.py`; `.gitignore`; `AGENTS.md`
- **boundary**：files: `src/knowledge_digest/semantic_compiler.py`; `src/knowledge_digest/semantic_cli.py`; `scripts/legacy_digest_reference.py`; `tests/acceptance/test_task7_e2e.py`; `tests/fixtures/task7_e2e/`; `src/knowledge_digest/simple_cli.py`; `.gitignore`; `AGENTS.md`; symbols/regions: 新模块全部符号；simple_cli 仅默认分发分支；.gitignore 仅追加 cache/ 行；AGENTS.md 仅 digest 使用说明一节
- **输出**：GREEN 可观察结果（pytest exit 0）
- **Knowledge**：T013 失败事实；旧路径入口形态（compiler.digest 默认分支调用方式）
- **verification_role**：GREEN
- **paired_task**：T013
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_e2e.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-E2E-001 {"pass":"对账/骨架批次/计划打印/digest 新行为成功信号与基线节点不变","reject":{"input":"对账差异、provider 三态、写中断注入 fixture","expected_rejection":"端到端出批失败或 legacy 脚本不可运行或基线节点集合变化（pytest 非零）","observation":"pytest 失败输出中命令面断言的失败位置"}}`
- **semantic_review_status**：incomplete
- **semantic_review_ref**：`specs/task7-semantic-layer-compiler/plan.md#Test Strategy`
- **semantic_review_reason**：build-plan 设计期事实——RED/GREEN 尚未执行，oracle 语义审查随 build-code 完成后复核
- **evidence_path**：`quality/evidence/build-code/task7/T014/`
- **STOP**：需要弱化测试、扩大边界或新增设计时停止
- **recovery**：回滚实现改动，保 RED 证据，回 plan 修设计
- **task risk**：simple_cli 改派误伤 --no-llm/M401/M402 历史分支
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；邻接集成
- **scenarios / commands / expected exit / oracle**：成功=端到端出批 + legacy 脚本可运行 + 基线 16 节点集合不变 exit 0；失败=任一红 exit 1；负例=对账失败骨架不写 products（同命令同 oracle）
- **fixtures_services**：同 T013；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：命令面与端到端；不覆盖真实 provider（fake 注入）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `semantic_compiler.py`、`semantic_cli.py`、`scripts/legacy_digest_reference.py`；改派 `simple_cli.py`；同步 `.gitignore` 与 `AGENTS.md`。实现 89 条清单对账、87 个主题批次、缓存/provider 三态、模型配置读取、确定性回退、五件审计、legacy 独立入口和中断语义；未修改旧 compiler/pipeline/reader 模块。
- **executed_commands**：RED exit `1`（T013）；初始 GREEN `9 passed, 1 skipped`；新增集成边界回归 `6 passed, 9 deselected`；修复后 Task7 聚合 `57 passed, 1 skipped`；真实 acceptance `1 passed, 14 deselected`；canonical 当前聚合见 T016。
- **evidence_refs**：`quality/evidence/build-code/task7/T014/routing.json`; `quality/evidence/build-code/task7/T014/test-strategy.json`; `quality/evidence/build-code/task7/T014/green-result.json`; `quality/evidence/build-code/task7/T013/red-result.json`; `quality/evidence/build-code/task7/T016/real-corpus-result.json`; `quality/evidence/build-code/task7/P7-phase-review.json`; canonical `quality/tests/task7/T014-current.json`; canonical 当前聚合 `quality/tests/task7/T016-current.json`。
- **covered_ac**：AC-01 / AC-08 / AC-09 / AC-10 / AC-12；真实 89 条 acceptance 另覆盖 89 来源、87 页、首跑 provider 成本和缓存复跑一致性。
- **review_fact**：P7 唯一 phase review 已执行并记录为 `unavailable`（`REVIEW_WAIT_EXCEEDED`，无 result_ref）；初始 integration review 已返回 actionable findings，修复后需按一次 focused 规则复核，不能改写 phase review 为 clean。
- **completed_at**：2026-09-14
- **执行事实**：小语料 GREEN 初次通过后，真实语料暴露一份纯空白来源被判为 ready 的缺陷；修正为 `known_empty`，随后补齐计划先行、渲染失败、真实写失败、大批次中断审计和直接 CLI 兼容回归。当前真实 acceptance 与聚合均通过。provider 凭据仅从用户配置进程内读取，未进入代码、审计或缓存。

#### T015 — FINAL：aggregate verification（聚合验收）

- **ID**：T015
- **Phase**：Phase P7 — 命令切换与端到端
- **goal**：按 plan 预先设计的最终路线验证全部适用 AC、跨任务 seam 和当前完整测试事实
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task7-semantic-layer-compiler/spec.md","hash":"d495816e280bd9f4b6e5baa668b931f9a6d780bcf89a0e8f6d901bbf5e3bdc21","id":"spec-task7"},{"artifact_kind":"plan","ref":"specs/task7-semantic-layer-compiler/plan.md","hash":"6f1552280b646a3e34fb00eed3314e317ec0ce323c8b3957a5317d6d8365d81a","id":"plan-task7"}]`
- **source_refs / decision_refs**：全部 R*/D* → FR-SRC/BLK/GRP/CMP/PUB/AUD/CLI/REG-001… → AC-01…AC-13
- **输入**：T002-T014 的完成事实与最终路线
- **依赖**：T014
- **并行**：否 — aggregate reads all preceding task facts
- **FR**：FR-SRC-001 / FR-SRC-002 / FR-BLK-001 / FR-BLK-002 / FR-GRP-001 / FR-GRP-002 / FR-CMP-001 / FR-CMP-002 / FR-CMP-003 / FR-CMP-004 / FR-PUB-001 / FR-PUB-002 / FR-PUB-003 / FR-AUD-001 / FR-AUD-002 / FR-AUD-003 / FR-AUD-004 / FR-AUD-005 / FR-CLI-001 / FR-REG-001
- **AC**：AC-01 / AC-02 / AC-03 / AC-04 / AC-05 / AC-06 / AC-07 / AC-08 / AC-09 / AC-10 / AC-11 / AC-12 / AC-13
- **动作**：只执行一次最终聚合检查并记录真实退出码、oracle、覆盖范围和剩余风险；不创建新的状态权威
- **current review repair scope**：integration re-review 必须把 CLI 分发及 stdout/stderr 机器通道、编排、audit_only 不抢 canonical、页面/审计写入与可物化 anchor、sourced intro 的读者来源归属、空 intro fallback 的 audit claim/retrieval evidence、缺失或不可读 manifest source 的 blocked ledger 与 blocker、provider 成功但无 token usage 时的显式 blocked/zero-reason、重复 source block 跨 multipart 的 concrete claim→part 绑定、缓存/provider 失败（包括 cache-integrity fallback 必须落对应 `原文未明确` audit claim/retrieval evidence、provider adapter 已调用但异常时仍须记入实际调用数）、reference block/attachment 的读者来源归属、初始化 fail-closed、重复原文的导读歧义必须 fail-closed、跨 topic 的 intro occurrence/claim ID 必须共享分配且按 claim kind 隔离、provider prompt 的行号/类型/正文/成员顺序变化必须使缓存失效、interrupted recovery、导读混合结论及实际 fallback span、导读分页限额、叙述空白保真和 claim 句号边界的可执行代码片段纳入 provider-visible implementation context；句号 fixture 需覆盖数字版本号、文件名、版本路径和 URL；created/updated 继续遵守 FR-PUB-001 的来源 mtime 契约与 RISK-015。
- **精确文件**：`tests/acceptance/test_task7_e2e.py`
- **boundary**：files: `tests/acceptance/test_task7_e2e.py`; symbols/regions: 仅最终验证允许的新增测试函数
- **输出**：最终测试与交接事实
- **Knowledge**：所有前序任务的真实结果
- **verification_role**：N/A — non-behavior aggregate verification
- **paired_task**：N/A — aggregate has no RED/GREEN pair
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py tests/acceptance/test_task7_group.py tests/acceptance/test_task7_claims.py tests/acceptance/test_task7_pages.py tests/acceptance/test_task7_cache.py tests/acceptance/test_task7_audit.py tests/acceptance/test_task7_e2e.py -q"`
- **expected_exit**：0
- **oracle**：`ORACLE-FINAL {"pass":"七文件全绿 + 端到端 seam + 基线 16 节点集合不变 + 前序任务事实齐备"}`
- **evidence_path**：`quality/evidence/build-code/task7/T015/`
- **STOP**：最终命令不可执行、AC 缺失、越界或需要新决策时停止
- **recovery**：回受影响 task，不用全量重跑掩盖局部失败
- **task risk**：聚合覆盖遗漏或把质量事实误写成通过
- **test tier / test method**：feature — test-routing-advisor 判类（2026-09-13T05:15:04Z，routing_tier=feature，result=pass）；聚合检查
- **scenarios / commands / expected exit / oracle**：成功=七文件全绿 + 端到端 seam exit 0；失败=任一前序事实缺失 exit 1；状态=基线 16 节点集合比对（同命令同 oracle）
- **fixtures_services**：汇总前序 fixture；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **coverage limits**：最终命令覆盖范围 = 全部新测试文件 + 真实 89 语料运行（第二条 acceptance_data 需真实语料与 provider；provider 不可用时该条记 unavailable 并保留原因，owner=build-code，重试触发=provider 恢复）；AC-01 人工抽 20 块复核清单为人工证据，不随命令自动通过
- **acceptance_role**：acceptance
- **ui_scope**：non_ui
- **acceptance_data**：`[{"source":"tests/fixtures/task7_e2e","sample":"task7 专用合成小语料","scenario":"七文件聚合 + 端到端出批 + 逐 AC 断言输出 JSON","tier":"command","execution":{"command":"bash","args":["-c","uv run --frozen python tests/acceptance/test_task7_e2e.py --workflowhub-json"],"timeout_ms":180000}},{"source":"/Users/Hugh/Downloads/confluence 原始数据 + config/task4-source-coverage-89-input.v1.json","sample":"真实 89 份冻结语料","scenario":"真实出批 + 两次运行字节比对 + AC-01 人工抽 20 块逐字复核清单","tier":"command","execution":{"command":"bash","args":["-c","KNOWLEDGEDIGEST_TASK7_RAW_CORPUS=1 uv run --frozen python tests/acceptance/test_task7_e2e.py --workflowhub-json --real-corpus"],"timeout_ms":600000}}]`
- **e2e_scope**：not_required

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：N/A — aggregate verification only
- **executed_commands**：当前 material 修正后，将重新执行同一 aggregate 命令和真实语料命令；上一次 canonical 结果为 `79 passed, 1 skipped` 与 `1 passed, 25 deselected`，仅在新 snapshot/material revision 下重新捕获，不把旧 receipt 直接冒充 current。
- **evidence_refs**：当前回捕后填写新的 implementation receipt、aggregate/real-corpus receipts、Stage Agent outcome、official run facts 和当前 integration review result；历史 refs 保留在前序事实中，不作为 current completion evidence。
- **covered_ac**：AC-01…AC-13 的官方 acceptance chain；AC-01 真实语料人工抽 20 块逐字复核仍不由自动命令替代，保持为明确 coverage limit。
- **review_fact**：P7 phase review 的历史 `recorded_unavailable` 保持原样；当前 integration review 必须绑定新 material revision，要求无 actionable `major|blocking`，minor advice 逐项记录 disposition。不得改写历史 immutable review。
- **completed_at**：2026-09-14
- **执行事实**：T015 的前次 current refs 已因完成区事实修正而 stale；修正后重新捕获并由官方 build-code handler 重新确认 stage、quality、AC、finding dispositions 和 stage-end spec-analyze，reflection 若无 executor 仍记录 `unavailable`，不伪造 completed。阶段通过不等于 release 或 Git delivery。

### Verify

- **Target**：P7 全部 FR/AC 与跨任务 seam
- **gate_cmd**：`bash -c "uv run --frozen pytest tests/acceptance/test_task7_e2e.py -q"`
- **expected_exit**：0
- **evidence_path**：`quality/evidence/build-code/task7/T015/`
- **Oracle**：ORACLE-E2E-001 + ORACLE-FINAL

### Knowledge

交付 build-code：digest 门牌号已切换；legacy 脚本为旧行为唯一入口；AGENTS.md 使用说明需同步。P7 集成审查后的生命周期、计划先行、异常收口和直接 CLI 兼容修复事实已记录在 T015 执行区；最终 focused review 仍以当前 worktree 为准。

### STOP

旧行为无法完整迁移、或基线 16 节点无法冻结时返回 plan 修计划。

### Done

端到端出批且 manifest 机读；legacy 脚本可运行；基线节点 ID 清单落 plan；T015 聚合通过。

### Risks and rollback

- **Risk**：旧测试大面积变红的误读（实为 AC-10 分类对象）
- **Prevention**：分类清单逐文件标注绑定面
- **Rollback / recovery**：还原 simple_cli.py 与 .gitignore，删四新文件

## 4. Final current-snapshot aggregate strategy

- **tier / method**：feature — test-routing-advisor 判类（routing_tier=feature，result=pass，2026-09-13T05:15:04Z）；backend-testing 技能在 build-code 执行
- **scenarios**：全部适用 AC-01…AC-13、成功/失败/状态、跨任务 seam（拆块→归组→claim→页面→缓存→审计→命令）
- **command**: `bash -c "uv run --frozen pytest tests/acceptance/test_task7_split.py tests/acceptance/test_task7_group.py tests/acceptance/test_task7_claims.py tests/acceptance/test_task7_pages.py tests/acceptance/test_task7_cache.py tests/acceptance/test_task7_audit.py tests/acceptance/test_task7_e2e.py -q"`
- **expected exit**：0
- **oracle**：ORACLE-FINAL — 七个测试文件全绿 + 端到端 seam + 基线 16 节点集合不变
- **fixtures_services**：各卡内联 fixture 汇总；清理=pytest tmp 自动回收 / N/A — 无外部服务
- **evidence_path**：`quality/evidence/build-code/task7/FINAL/`
- **coverage limits**：覆盖全部新行为与端到端 seam；未覆盖真实 provider 调用、真实 89 语料全量运行（属 verify-code 真实运行验收决策）
- **STOP**：命令损坏、AC 缺失、边界越界或需要新决策
- **execution_contract**：当前快照运行一次；失败保留原始输出，回受影响 task，不用全量重跑掩盖局部失败。

## Dependency Graph

- **order**：T001 (RED) → T002 (GREEN) → T003 (RED) → T004 (GREEN) → T005 (RED) → T006 (GREEN) → T007 (RED) → T008 (GREEN) → T009 (RED) → T010 (GREEN) → T011 (RED) → T012 (GREEN) → T013 (RED) → T014 (GREEN) → T015 (FINAL)

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015
```

完成区的 `executed_commands`、`evidence_refs`、`review_fact` 和 `执行事实` 只填真实调用及消费者结果；规划文本不冒充执行、验收或发布。

## Final Boundary Check

- [x] 每个 Phase 的 Goal、Files、Tasks、Verify、Knowledge、STOP、Done、Risks and rollback 完整。
- [x] 每个任务只有一张卡和一个完成区；文件是所属 Phase NEW/MODIFY 的子集。
- [x] 每个行为变化都有同命令、同 oracle 的 RED → GREEN；FINAL 只做一次聚合。
- [x] 依赖无环，FR/AC 双向追溯闭合，未知事实没有被写成假设或通过。
- [x] review、test、evidence 只作为事实记录，不是开始、继续或交付许可证。
