# 任务清单：task8 入口与导航（K2）

- **Input**：`specs/task8-entry-navigation/decision-log.md`（approved）、`specs/task8-entry-navigation/spec.md`（frozen）、`specs/task8-entry-navigation/plan.md`（本文件姊妹篇）
- **Template version**：`plan-task.v4`
- **build-code 开工 gate（spec §12 F-4）**：~~T001 开工前 DEF-K2-2 必须关闭~~ **已于 2026-09-13 满足**——十条题目经用户确认冻结（`tests/fixtures/task8_nav/query_fixture_sample.json`）；DEF-K2-4 由 plan DEC-K2-004 关闭。build-code 可开工。
- **RED/GREEN 纪律**：每对同一 gate_cmd 与 oracle identity；RED expected_exit 非零先行提交，GREEN 修到 exit 0。
- **权威执行命令**：`uv run --frozen pytest -q` 包住 gate_cmd；执行事实（status/changed files/commands/evidence）逐卡回填下方执行状态填写区——该区是唯一完成权威。

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `decision-log.md#已选方向` | 已确认方向/范围/非目标 | S：判类与 review 时读 |
| `spec.md#5. 功能需求` | FR 精确契约 | M：写卡与实现时读 |
| `spec.md#11. 验收标准` | AC oracle 定义 | M：写 oracle 时读；B：回归时读 |
| `plan.md#Solution Design` | 职责块与接口 | M：实现对应块时读 |
| `plan.md#File Boundary` | NEW/MODIFY/DO NOT TOUCH | S：build-code 首卡前读 |
| `tasks.md#Phase P1…P4` | 42 卡执行设计与执行事实区 | M：逐卡执行时读写 |
| `CONTEXT.md#本轮新增术语（task8）` | 四术语 _Avoid_ 红线 | S：review 时读 |

## test-routing 判类（test-routing-advisor 输出合同）

```json
{
  "routing_tier": "feature",
  "routing_rationale": "Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/基础设施/并发/数据库变更。changed_files=semantic_navigation.py 单模块 + 测试 + fixtures；phase_count=4 同功能域不升级。",
  "result": "pass",
  "ts": "2026-09-13T00:00:00Z"
}
```

## Phase P1 — 输入对账与 fixture

### Goal

manifest 输入校验 fail-closed + 双向路径对账可用；fixture 把 K1 冻结 schema 固化为代码。

### Files

- **NEW**：`src/knowledge_digest/semantic_navigation.py`（对账职责块） + `tests/fixtures/task8_nav/`（fixture 构造器与样例）
- **MODIFY**：N/A — 本卡零 MODIFY（spec/plan/tasks 材料冻结）
- **DO NOT TOUCH**：K1 规划文件（semantic_*.py 尚不存在）；旧 `navigation.py`；既有 49 测试文件；CONTEXT.md/docs//CompanyBrain/gbrain/真实语料目录

### Tasks

#### T001R — RED：对账 happy 路径

- **ID**：T001R
- **Phase**：Phase P1
- **goal**：使 `test_reconcile_happy` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：R-008/R-014·D-004·OI-04·PFACT-K2-002
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：P1 对账层
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002
- **AC**：AC-K2-1
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：页面集精确等于 manifest 条目集（双向路径对账通过）
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T001G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "对账"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T001R — 页面集精确等于 manifest 条目集（双向路径对账通过）`
- **evidence_path**：`quality/evidence/build-code/T001R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：页面集精确等于 manifest 条目集（双向路径对账通过）（同 gate_cmd/oracle）
- **fixtures_services**：make_batch() 迷你批次（K1 schema manifest + 16 字段页面）
- **coverage limits**：不测 K1 真实写出；K1 schema 漂移由负例与 P4 wiring 卡兜住
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增 T001R；`tests/fixtures/task8_nav/__init__.py` 新增 Task7 schema 迷你批次。
- **executed_commands**：RED command exit 2（fixture 导入路径，已修测试）；同 command 目标 RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T001R/result.json`
- **covered_ac**：AC-K2-1
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:27:59Z
- **执行事实**：T001R 目标断言因 API 未实现失败；未改生产代码。
#### T001G — GREEN：对账 happy 路径

- **ID**：T001G
- **Phase**：Phase P1
- **goal**：实现使 T001R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：R-008/R-014·D-004·OI-04·PFACT-K2-002
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：P1 对账层
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002
- **AC**：AC-K2-1
- **动作**：实现 load_and_validate + reconcile_pages；fixture 3 页面/2 product/2 section
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T001R 同 gate_cmd exit 0
- **Knowledge**：实现 load_and_validate + reconcile_pages；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T001R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "对账"`
- **expected_exit**：0
- **oracle**：`ORACLE-T001R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T001G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T001R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：make_batch() 迷你批次（K1 schema manifest + 16 字段页面）
- **coverage limits**：不测 K1 真实写出；K1 schema 漂移由负例与 P4 wiring 卡兜住
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现 P1 对账职责块。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "对账"` exit 0；1 passed。
- **evidence_refs**：`quality/evidence/build-code/T001G/result.json`
- **covered_ac**：AC-K2-1
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:27:59Z
- **执行事实**：返回按 `page_path` 排序的 `ReconciledPage`；核对 manifest pages 与 products 文件双向集合，读取 title/product/section。
#### T002R — RED：manifest 缺字段 fail-closed

- **ID**：T002R
- **Phase**：Phase P1
- **goal**：使 `test_reconcile_manifest_missing_field` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：R-016·OI-05·SCN-K2-003
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：P1 对账层
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002/FR §9
- **AC**：AC-K2-5
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：缺 run_status/阻塞项/来源台账任一 → blocked，reason 含精确字段名
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T002G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "manifest"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T002R — 缺 run_status/阻塞项/来源台账任一 → blocked，reason 含精确字段名`
- **evidence_path**：`quality/evidence/build-code/T002R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：缺 run_status/阻塞项/来源台账任一 → blocked，reason 含精确字段名（同 gate_cmd/oracle）
- **fixtures_services**：字段删除版 manifest fixture ×3
- **coverage limits**：只测三个已冻结字段；K1 未来新增字段不在本卡
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增 3 个 manifest 缺字段负例。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "manifest"` RED exit 1，3 failed。
- **evidence_refs**：`quality/evidence/build-code/T002R/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:27:59Z
- **执行事实**：缺 `run_status`、`blockers`、`source_ledger` 均先验证未抛错，形成有效 RED。
#### T002G — GREEN：manifest 缺字段 fail-closed

- **ID**：T002G
- **Phase**：Phase P1
- **goal**：实现使 T002R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：R-016·OI-05·SCN-K2-003
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：P1 对账层
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002/FR §9
- **AC**：AC-K2-5
- **动作**：实现启动字段校验（K1 冻结字段缺失 → blocked 不写产物）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T002R 同 gate_cmd exit 0
- **Knowledge**：实现启动字段校验（K1 冻结字段缺失 → blocked 不写产物）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T002R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "manifest"`
- **expected_exit**：0
- **oracle**：`ORACLE-T002R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T002G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T002R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：字段删除版 manifest fixture ×3
- **coverage limits**：只测三个已冻结字段；K1 未来新增字段不在本卡
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 加入 K1 manifest 必需顶层字段 fail-closed 校验。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "manifest"` exit 0；3 passed, 1 deselected。
- **evidence_refs**：`quality/evidence/build-code/T002G/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:27:59Z
- **执行事实**：缺字段错误为 `missing-manifest-field:<field>`，reason 保留精确字段名。
#### T003R — RED：双向对账三态

- **ID**：T003R
- **Phase**：Phase P1
- **goal**：使 `test_reconcile_bidirectional` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-004·PFACT-K2-002·review F-2
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：P1 对账层
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002
- **AC**：AC-K2-1/AC-K2-5
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：条目有文件无/文件有条目无/slug=Index 冲突三态各自 blocked + reason 精确
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T003G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "双向对账三态"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T003R — 条目有文件无/文件有条目无/slug=Index 冲突三态各自 blocked + reason 精确`
- **evidence_path**：`quality/evidence/build-code/T003R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：条目有文件无/文件有条目无/slug=Index 冲突三态各自 blocked + reason 精确（同 gate_cmd/oracle）
- **fixtures_services**：撕裂目录 fixture ×3（手工增删文件/条目）
- **coverage limits**：Index 冲突依赖 K1 slug 排除对齐（DEF-K2-5），本卡只验 K2 检出
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增文件无条目、条目无文件、`Index.md` 冲突三态。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "双向对账三态"` RED exit 1；3 failed。
- **evidence_refs**：`quality/evidence/build-code/T003R/result.json`
- **covered_ac**：AC-K2-1/AC-K2-5
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:27:59Z
- **执行事实**：三态先统一返回泛化 reason，测试证明精确分类尚未实现。
#### T003G — GREEN：双向对账三态

- **ID**：T003G
- **Phase**：Phase P1
- **goal**：实现使 T003R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-004·PFACT-K2-002·review F-2
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：P1 对账层
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002
- **AC**：AC-K2-1/AC-K2-5
- **动作**：实现对账双向遍历 + Index 保留名规则
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T003R 同 gate_cmd exit 0
- **Knowledge**：实现对账双向遍历 + Index 保留名规则；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T003R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "双向对账三态"`
- **expected_exit**：0
- **oracle**：`ORACLE-T003R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T003G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T003R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：撕裂目录 fixture ×3（手工增删文件/条目）
- **coverage limits**：Index 冲突依赖 K1 slug 排除对齐（DEF-K2-5），本卡只验 K2 检出
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 区分三态 reason，并在集合对账前拦截保留名 `Index.md`。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "双向对账三态"` exit 0；3 passed, 4 deselected。
- **evidence_refs**：`quality/evidence/build-code/T003G/result.json`
- **covered_ac**：AC-K2-1/AC-K2-5
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:27:59Z
- **执行事实**：三态分别为 `manifest-page-file-missing`、`products-page-undeclared`、`nav-index-name-conflict`。
## Phase P2 — 机械生成（无模型）

### Goal

三件套机械层确定性生成（Index/模块 Index/Home 机械段 + frontmatter + 模块名推断），零模型调用。

### Files

- **NEW**：`src/knowledge_digest/semantic_navigation.py`（生成职责块） + `tests/fixtures/task8_nav/`（fixture 构造器与样例）
- **MODIFY**：N/A — 本卡零 MODIFY（spec/plan/tasks 材料冻结）
- **DO NOT TOUCH**：K1 规划文件（semantic_*.py 尚不存在）；旧 `navigation.py`；既有 49 测试文件；CONTEXT.md/docs//CompanyBrain/gbrain/真实语料目录

### Tasks

#### T004R — RED：挂载树生成

- **ID**：T004R
- **Phase**：Phase P2
- **goal**：使 `test_build_mount_tree` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-003/D-004·OI-02
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002/004
- **AC**：AC-K2-4
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：Index 按 product 分节、节内 section 升序；模块 Index 条目含 wikilink+描述槽
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T004G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "挂载树生成"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T004R — Index 按 product 分节、节内 section 升序；模块 Index 条目含 wikilink+描述槽`
- **evidence_path**：`quality/evidence/build-code/T004R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：Index 按 product 分节、节内 section 升序；模块 Index 条目含 wikilink+描述槽（同 gate_cmd/oracle）
- **fixtures_services**：T001 happy fixture 复用
- **coverage limits**：不验模型产物（P3）；排序只 section slug 升序
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增挂载树、全局 Index、模块 Index 的 RED oracle。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "挂载树生成"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T004R/result.json`
- **covered_ac**：AC-K2-4
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：目标 build_index/build_module_indexes 未实现，RED 来自 API 缺失。
#### T004G — GREEN：挂载树生成

- **ID**：T004G
- **Phase**：Phase P2
- **goal**：实现使 T004R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-003/D-004·OI-02
- **输入**：spec §5（FR-NAV-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-002/004
- **AC**：AC-K2-4
- **动作**：实现 build_index + build_module_indexes（确定性模板）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T004R 同 gate_cmd exit 0
- **Knowledge**：实现 build_index + build_module_indexes（确定性模板）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T004R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "挂载树生成"`
- **expected_exit**：0
- **oracle**：`ORACLE-T004R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T004G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T004R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：T001 happy fixture 复用
- **coverage limits**：不验模型产物（P3）；排序只 section slug 升序
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现 NavigationDocument、全局 Index、模块 Index 和描述 pending 槽。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "挂载树生成"` exit 0；1 passed, 10 deselected。
- **evidence_refs**：`quality/evidence/build-code/T004G/result.json`
- **covered_ac**：AC-K2-4
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：Index 按 product 分节；模块 Index 以 `products/<product>/<section>/Index.md` 输出 wikilink 和描述槽。
#### T005R — RED：frontmatter 16 字段契约

- **ID**：T005R
- **Phase**：Phase P2
- **goal**：使 `test_build_frontmatter_contract` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-005"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：S1·D-010·review F-3
- **输入**：spec §5（FR-NAV-005）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-005
- **AC**：AC-K2-4
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：16 字段逐项（tier 分层/title/source=batch/created/updated/tags/generated_by）
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T005G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "frontmatter"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T005R — 16 字段逐项（tier 分层/title/source=batch/created/updated/tags/generated_by）`
- **evidence_path**：`quality/evidence/build-code/T005R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：16 字段逐项（tier 分层/title/source=batch/created/updated/tags/generated_by）（同 gate_cmd/oracle）
- **fixtures_services**：字段断言辅助函数
- **coverage limits**：generated_by 值由 DEC-K2-004 冻结，本卡验常量存在性
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增三类导航页 16 字段和值的 RED oracle。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "frontmatter"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T005R/result.json`
- **covered_ac**：AC-K2-4
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：frontmatter 构造器未实现，RED 断言未被实现细节满足。
#### T005G — GREEN：frontmatter 16 字段契约

- **ID**：T005G
- **Phase**：Phase P2
- **goal**：实现使 T005R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-005"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：S1·D-010·review F-3
- **输入**：spec §5（FR-NAV-005）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-005
- **AC**：AC-K2-4
- **动作**：实现三件套 frontmatter 构造（零新增字段）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T005R 同 gate_cmd exit 0
- **Knowledge**：实现三件套 frontmatter 构造（零新增字段）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T005R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "frontmatter"`
- **expected_exit**：0
- **oracle**：`ORACLE-T005R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T005G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T005R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：字段断言辅助函数
- **coverage limits**：generated_by 值由 DEC-K2-004 冻结，本卡验常量存在性
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现 Task7 16 字段有序 frontmatter 构造和导航固定值。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "frontmatter"` exit 0；1 passed, 8 deselected。
- **evidence_refs**：`quality/evidence/build-code/T005G/result.json`
- **covered_ac**：AC-K2-4
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：Home/Index tier=1，模块 tier=2；`source=batch`、稳定日期和 `generated_by` 均按合同生成。
#### T006R — RED：模块中文名推断

- **ID**：T006R
- **Phase**：Phase P2
- **goal**：使 `test_module_title_inference` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-004"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：R2-Q7·D-006·DEC-K2-004
- **输入**：spec §5（FR-GEN-004）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-004
- **AC**：AC-K2-4
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：词频最高/并列字典序最小/单页三态；同输入两次推断一致
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T006G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "模块中文名推断"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T006R — 词频最高/并列字典序最小/单页三态；同输入两次推断一致`
- **evidence_path**：`quality/evidence/build-code/T006R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：词频最高/并列字典序最小/单页三态；同输入两次推断一致（同 gate_cmd/oracle）
- **fixtures_services**：三态 title 集合 fixture
- **coverage limits**：推断质量（像不像人话）不入 oracle——机器只验确定性
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增最高频、tie-break、单页、空集合推断 RED oracle。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "模块中文名推断"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T006R/result.json`
- **covered_ac**：AC-K2-4
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：模块名推断器未实现，RED 来自 API 缺失。
#### T006G — GREEN：模块中文名推断

- **ID**：T006G
- **Phase**：Phase P2
- **goal**：实现使 T006R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-004"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：R2-Q7·D-006·DEC-K2-004
- **输入**：spec §5（FR-GEN-004）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-004
- **AC**：AC-K2-4
- **动作**：实现确定性推断（切分→词频→字典序 tie-break）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T006R 同 gate_cmd exit 0
- **Knowledge**：实现确定性推断（切分→词频→字典序 tie-break）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T006R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "模块中文名推断"`
- **expected_exit**：0
- **oracle**：`ORACLE-T006R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T006G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T006R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：三态 title 集合 fixture
- **coverage limits**：推断质量（像不像人话）不入 oracle——机器只验确定性
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现 Unicode token 计数、最高频选择、字典序 tie-break 和空集合回退。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "模块中文名推断"` exit 0；1 passed, 9 deselected。
- **evidence_refs**：`quality/evidence/build-code/T006G/result.json`
- **covered_ac**：AC-K2-4
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：三类 title 集合和空集合结果均稳定；无模型调用。
#### T007R — RED：Home 机械段

- **ID**：T007R
- **Phase**：Phase P2
- **goal**：使 `test_home_mechanical_sections` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-007·OI-06
- **输入**：spec §5（FR-NAV-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-003
- **AC**：AC-K2-4/AC-K2-5
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：状态行 nav: success_pages=N blocked_sources=M + 快速入口 + 使用边界段；无时间戳/批次名；建议槽空标记
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T007G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "home"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T007R — 状态行 nav: success_pages=N blocked_sources=M + 快速入口 + 使用边界段；无时间戳/批次名；建议槽空标记`
- **evidence_path**：`quality/evidence/build-code/T007R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：状态行 nav: success_pages=N blocked_sources=M + 快速入口 + 使用边界段；无时间戳/批次名；建议槽空标记（同 gate_cmd/oracle）
- **fixtures_services**：T001 fixture + blocked=[2] 变体
- **coverage limits**：建议文本 P3 注入，本卡只验槽位
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增 Home 状态行、入口、建议槽和边界段 RED oracle。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "home"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T007R/result.json`
- **covered_ac**：AC-K2-4/AC-K2-5
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：Home 机械构造器未实现，RED 来自 API 缺失。
#### T007G — GREEN：Home 机械段

- **ID**：T007G
- **Phase**：Phase P2
- **goal**：实现使 T007R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-007·OI-06
- **输入**：spec §5（FR-NAV-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-003
- **AC**：AC-K2-4/AC-K2-5
- **动作**：实现 build_home 机械段（确定性模板）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T007R 同 gate_cmd exit 0
- **Knowledge**：实现 build_home 机械段（确定性模板）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T007R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "home"`
- **expected_exit**：0
- **oracle**：`ORACLE-T007R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T007G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T007R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：T001 fixture + blocked=[2] 变体
- **coverage limits**：建议文本 P3 注入，本卡只验槽位
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现 Home 稳定状态行、Index/product 入口、建议 pending 槽和 K3 边界段。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "挂载树生成 or frontmatter or 模块中文名推断 or home"` exit 0；4 passed, 7 deselected。
- **evidence_refs**：`quality/evidence/build-code/T007G/result.json`
- **covered_ac**：AC-K2-4/AC-K2-5
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:49:56Z
- **执行事实**：Home 正文不包含运行日期/批次名；日期只来自稳定 frontmatter，查询建议留给 P3 模型职责。
## Phase P3 — 模型产物（缓存/描述/建议）

### Goal

缓存协议对接、描述/建议生成、拒绝词表与非空校验、预算记账；离线全链可验。

### Files

- **NEW**：`src/knowledge_digest/semantic_navigation.py`（model 职责块） + `tests/fixtures/task8_nav/`（fixture 构造器与样例）
- **MODIFY**：N/A — 本卡零 MODIFY（spec/plan/tasks 材料冻结）
- **DO NOT TOUCH**：K1 规划文件（semantic_*.py 尚不存在）；旧 `navigation.py`；既有 49 测试文件；CONTEXT.md/docs//CompanyBrain/gbrain/真实语料目录

### Tasks

#### T008R — RED：缓存键契约

- **ID**：T008R
- **Phase**：Phase P3
- **goal**：使 `test_cache_key_contract` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-009·PFACT-K2-005·review F-6
- **输入**：spec §5（FR-GEN-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-003
- **AC**：AC-K2-6
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：五要素（任务标识/输入内容指纹/模型标识/提示模板版本/主题映射版本）逐项；改页面一字节→键变
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T008G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存键契约"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T008R — 五要素（任务标识/输入内容指纹/模型标识/提示模板版本/主题映射版本）逐项；改页面一字节→键变`
- **evidence_path**：`quality/evidence/build-code/T008R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：五要素（任务标识/输入内容指纹/模型标识/提示模板版本/主题映射版本）逐项；改页面一字节→键变（同 gate_cmd/oracle）
- **fixtures_services**：字节级 fixture + 键导出钩子
- **coverage limits**：负例只验描述键；建议键同构推理不重复测
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增五要素缓存键 RED oracle。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存键契约"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T008R/result.json`
- **covered_ac**：AC-K2-6
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：缓存键 API 未实现，RED 来自目标断言。
#### T008G — GREEN：缓存键契约

- **ID**：T008G
- **Phase**：Phase P3
- **goal**：实现使 T008R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-009·PFACT-K2-005·review F-6
- **输入**：spec §5（FR-GEN-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-003
- **AC**：AC-K2-6
- **动作**：实现键构造（与 K1 同构）+ 键导出可测钩子
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T008R 同 gate_cmd exit 0
- **Knowledge**：实现键构造（与 K1 同构）+ 键导出可测钩子；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T008R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存键契约"`
- **expected_exit**：0
- **oracle**：`ORACLE-T008R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T008G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T008R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：字节级 fixture + 键导出钩子
- **coverage limits**：负例只验描述键；建议键同构推理不重复测
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现 description/suggestion 独立前缀和五要素内容指纹键。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存键契约"` exit 0；1 passed, 11 deselected。
- **evidence_refs**：`quality/evidence/build-code/T008G/result.json`
- **covered_ac**：AC-K2-6
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：键值不含批次名/时间；页面字节或模型/提示/主题版本变化均导致 key 变化。
#### T009R — RED：缓存命中零调用

- **ID**：T009R
- **Phase**：Phase P3
- **goal**：使 `test_cache_hit_no_call` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-009·OI-08
- **输入**：spec §5（FR-GEN-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-003
- **AC**：AC-K2-6
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：预置命中 → gateway 零调用且输出=缓存值；miss → 调用一次并写回
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T009G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存命中零调用"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T009R — 预置命中 → gateway 零调用且输出=缓存值；miss → 调用一次并写回`
- **evidence_path**：`quality/evidence/build-code/T009R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：预置命中 → gateway 零调用且输出=缓存值；miss → 调用一次并写回（同 gate_cmd/oracle）
- **fixtures_services**：DictCache + FakeGateway 调用计数
- **coverage limits**：真实 K1 缓存适配归 DEC-K2-002 后续，本卡验协议
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增 DictCache/FakeGateway hit/miss RED oracle。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存命中零调用"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T009R/result.json`
- **covered_ac**：AC-K2-6
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：缓存边界 API 未实现，RED 来自目标断言。
#### T009G — GREEN：缓存命中零调用

- **ID**：T009G
- **Phase**：Phase P3
- **goal**：实现使 T009R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-009·OI-08
- **输入**：spec §5（FR-GEN-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-003
- **AC**：AC-K2-6
- **动作**：实现缓存读写路径（CacheProtocol 对接）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T009R 同 gate_cmd exit 0
- **Knowledge**：实现缓存读写路径（CacheProtocol 对接）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T009R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存命中零调用"`
- **expected_exit**：0
- **oracle**：`ORACLE-T009R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T009G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T009R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：DictCache + FakeGateway 调用计数
- **coverage limits**：真实 K1 缓存适配归 DEC-K2-002 后续，本卡验协议
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现 hit 先返回、miss 单次 gateway complete 后 set。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "缓存命中零调用"` exit 0；1 passed, 12 deselected。
- **evidence_refs**：`quality/evidence/build-code/T009G/result.json`
- **covered_ac**：AC-K2-6
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：命中 gateway 调用数为 0，miss 调用数为 1 且缓存收到结果。
#### T010R — RED：模型输出校验（空/拒绝词）

- **ID**：T010R
- **Phase**：Phase P3
- **goal**：使 `test_model_output_validation` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-001"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-005·review R2-B3/F-5
- **输入**：spec §5（FR-GEN-001）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-001/002
- **AC**：AC-K2-2/AC-K2-5
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：空串/拒绝词（最佳）→ blocked 且 reason 精确；无重试（一次即决）
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T010G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "模型输出校验（空/拒绝词）"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T010R — 空串/拒绝词（最佳）→ blocked 且 reason 精确；无重试（一次即决）`
- **evidence_path**：`quality/evidence/build-code/T010R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：空串/拒绝词（最佳）→ blocked 且 reason 精确；无重试（一次即决）（同 gate_cmd/oracle）
- **fixtures_services**：FakeGateway 三态脚本
- **coverage limits**：真实模型不调用；重试被 spec review F-11 显式删除
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增空输出/拒绝词/合法输出 RED oracle。
- **executed_commands**：原冻结 gate exit 4（pytest selector 非法）；等价 `-k "模型输出校验"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T010R/result.json`
- **covered_ac**：AC-K2-2/AC-K2-5
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：冻结 gate 含非法全角括号/斜杠表达式，保留失败事实并用最小等价 selector 继续；未改 tasks.md。
#### T010G — GREEN：模型输出校验（空/拒绝词）

- **ID**：T010G
- **Phase**：Phase P3
- **goal**：实现使 T010R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-001"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-005·review R2-B3/F-5
- **输入**：spec §5（FR-GEN-001）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-001/002
- **AC**：AC-K2-2/AC-K2-5
- **动作**：实现非空校验 + REJECTION_WORDS 过滤（DEC-K2-004 常量）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T010R 同 gate_cmd exit 0
- **Knowledge**：实现非空校验 + REJECTION_WORDS 过滤（DEC-K2-004 常量）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T010R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "模型输出校验（空/拒绝词）"`
- **expected_exit**：0
- **oracle**：`ORACLE-T010R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T010G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T010R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：FakeGateway 三态脚本
- **coverage limits**：真实模型不调用；重试被 spec review F-11 显式删除
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现空值、非字符串和 `REJECTION_WORDS` fail-closed 校验。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "模型输出校验"` exit 0；1 passed, 13 deselected。
- **evidence_refs**：`quality/evidence/build-code/T010G/result.json`
- **covered_ac**：AC-K2-2/AC-K2-5
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：空/拒绝词分别报告 `model-output-missing`/`model-output-rejected`；无重试逻辑。
#### T011R — RED：建议数与预算记账

- **ID**：T011R
- **Phase**：Phase P3
- **goal**：使 `test_suggestion_count_and_metrics` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-007·K1 FR-AUD-005
- **输入**：spec §5（FR-GEN-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-002/FR-AUD-002
- **AC**：AC-K2-4/AC-K2-6
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：建议 ≥3 非空（无上限）；run-metrics K2 调用数记账（计划=页面数+1）
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T011G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "建议数与预算记账"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T011R — 建议 ≥3 非空（无上限）；run-metrics K2 调用数记账（计划=页面数+1）`
- **evidence_path**：`quality/evidence/build-code/T011R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：建议 ≥3 非空（无上限）；run-metrics K2 调用数记账（计划=页面数+1）（同 gate_cmd/oracle）
- **fixtures_services**：FakeGateway + metrics 读取断言
- **coverage limits**：预算上界 1.5× 为 K1 继承约束，本卡验记账真实性
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 新增建议数量和 page_count+1 预算 RED oracle。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "建议数与预算记账"` exit 1；1 failed。
- **evidence_refs**：`quality/evidence/build-code/T011R/result.json`
- **covered_ac**：AC-K2-4/AC-K2-6
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：建议校验和 metrics API 未实现，RED 来自目标断言。
#### T011G — GREEN：建议数与预算记账

- **ID**：T011G
- **Phase**：Phase P3
- **goal**：实现使 T011R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-007·K1 FR-AUD-005
- **输入**：spec §5（FR-GEN-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-002/FR-AUD-002
- **AC**：AC-K2-4/AC-K2-6
- **动作**：实现建议批量生成 + metrics 补记
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T011R 同 gate_cmd exit 0
- **Knowledge**：实现建议批量生成 + metrics 补记；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T011R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "建议数与预算记账"`
- **expected_exit**：0
- **oracle**：`ORACLE-T011R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T011G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T011R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：FakeGateway + metrics 读取断言
- **coverage limits**：预算上界 1.5× 为 K1 继承约束，本卡验记账真实性
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`src/knowledge_digest/semantic_navigation.py` 实现建议 ≥3 校验和 K2 metrics projection。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "建议数与预算记账"` exit 0；1 passed, 14 deselected。
- **evidence_refs**：`quality/evidence/build-code/T011G/result.json`
- **covered_ac**：AC-K2-4/AC-K2-6
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T16:57:43Z
- **执行事实**：建议无上限；`planned_provider_calls = page_count + 1`，实际调用和命中数独立记账。
## Phase P4 — 自检、状态增写、端到端

### Goal

覆盖判定三件套 + 四判据 + 路径抽查 + blocked 矩阵 + commit fail-closed + 生产接线；七 AC 闭环。

### Files

- **NEW**：`src/knowledge_digest/semantic_navigation.py`（自检+commit 职责块） + `tests/fixtures/task8_nav/`（fixture 构造器与样例）
- **MODIFY**：N/A — 本卡零 MODIFY（spec/plan/tasks 材料冻结）
- **DO NOT TOUCH**：K1 规划文件（semantic_*.py 尚不存在）；旧 `navigation.py`；既有 49 测试文件；CONTEXT.md/docs//CompanyBrain/gbrain/真实语料目录

### Tasks

#### T012R — RED：覆盖判定三件套

- **ID**：T012R
- **Phase**：Phase P4
- **goal**：使 `test_check_coverage_three` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-001"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-008·OI-07·review R2-B1
- **输入**：spec §5（FR-CHK-001）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-001
- **AC**：AC-K2-1
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：漏挂（孤儿）/死链/指向 manifest 外页面三态检出，reason 精确；不用数量等式
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T012G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "覆盖判定三件套"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T012R — 漏挂（孤儿）/死链/指向 manifest 外页面三态检出，reason 精确；不用数量等式`
- **evidence_path**：`quality/evidence/build-code/T012R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：漏挂（孤儿）/死链/指向 manifest 外页面三态检出，reason 精确；不用数量等式（同 gate_cmd/oracle）
- **fixtures_services**：破坏版暂存 fixture ×3（写暂存区模拟）
- **coverage limits**：遍历只认 wikilink；裸 URL/相对链接按 CB 同构约定不出现于导航
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的覆盖三件套 RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "覆盖判定三件套"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T012R/result.json`
- **covered_ac**：AC-K2-1
- **review_fact**：N/A — RED 与其 paired GREEN 合并审
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 覆盖孤儿、死链和 manifest 外页面三态。
#### T012G — GREEN：覆盖判定三件套

- **ID**：T012G
- **Phase**：Phase P4
- **goal**：实现使 T012R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-001"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-008·OI-07·review R2-B1
- **输入**：spec §5（FR-CHK-001）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-001
- **AC**：AC-K2-1
- **动作**：实现 wikilink 解析 + BFS 遍历 + 覆盖判定（⊆/存在/⊆）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T012R 同 gate_cmd exit 0
- **Knowledge**：实现 wikilink 解析 + BFS 遍历 + 覆盖判定（⊆/存在/⊆）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T012R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "覆盖判定三件套"`
- **expected_exit**：0
- **oracle**：`ORACLE-T012R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T012G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T012R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：破坏版暂存 fixture ×3（写暂存区模拟）
- **coverage limits**：遍历只认 wikilink；裸 URL/相对链接按 CB 同构约定不出现于导航
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_nav_check.py` 实现 Home BFS 覆盖、链接存在和 manifest 边界检查。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "覆盖判定三件套"` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T012G/result.json`
- **covered_ac**：AC-K2-1
- **review_fact**：N/A — 与 paired RED 合并审
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：BFS 覆盖、链接存在和 manifest 边界检查通过；未使用数量等式。
#### T013R — RED：描述四判据

- **ID**：T013R
- **Phase**：Phase P4
- **goal**：使 `test_check_description_criteria` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：Talk R3 冻结·review R2-B2/B3
- **输入**：spec §5（FR-CHK-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-002
- **AC**：AC-K2-2
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：重复=0/骨架≥3/问句模板≥3/空描述 四判据逐条检出
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T013G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "描述四判据"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T013R — 重复=0/骨架≥3/问句模板≥3/空描述 四判据逐条检出`
- **evidence_path**：`quality/evidence/build-code/T013R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：重复=0/骨架≥3/问句模板≥3/空描述 四判据逐条检出（同 gate_cmd/oracle）
- **fixtures_services**：违例描述集 fixture ×4
- **coverage limits**：判据算法（切分/归一化）按 spec AC-K2-2 冻结口径实现
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的描述四判据 RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "描述四判据"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T013R/result.json`
- **covered_ac**：AC-K2-2
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 覆盖精确重复、骨架重复、问句模板和空描述四种违规。
#### T013G — GREEN：描述四判据

- **ID**：T013G
- **Phase**：Phase P4
- **goal**：实现使 T013R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：Talk R3 冻结·review R2-B2/B3
- **输入**：spec §5（FR-CHK-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-002
- **AC**：AC-K2-2
- **动作**：实现规范化/骨架/问句模板/空判据四函数
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T013R 同 gate_cmd exit 0
- **Knowledge**：实现规范化/骨架/问句模板/空判据四函数；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T013R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "描述四判据"`
- **expected_exit**：0
- **oracle**：`ORACLE-T013R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T013G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T013R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：违例描述集 fixture ×4
- **coverage limits**：判据算法（切分/归一化）按 spec AC-K2-2 冻结口径实现
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_nav_check.py` 实现描述规范化、骨架和问句模板检查，并拒绝空值。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "描述四判据"` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T013G/result.json`
- **covered_ac**：AC-K2-2
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：四判据逐条返回 reason；编译入口遇红时不落导航并写 blocked 状态。
#### T014R — RED：N=10 路径抽查

- **ID**：T014R
- **Phase**：Phase P4
- **goal**：使 `test_path_sample_and_gate` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：Q7·Talk R3 N=10·DEF-K2-2
- **输入**：spec §5（FR-CHK-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-003
- **AC**：AC-K2-3
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：10 题 BFS 边数≤3；一题 3+跳构造 → blocked；fixture=None → incomplete 不失败
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T014G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "n=10"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T014R — 10 题 BFS 边数≤3；一题 3+跳构造 → blocked；fixture=None → incomplete 不失败`
- **evidence_path**：`quality/evidence/build-code/T014R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：10 题 BFS 边数≤3；一题 3+跳构造 → blocked；fixture=None → incomplete 不失败（同 gate_cmd/oracle）
- **fixtures_services**：query_fixture_sample.json（10 题样例）
- **coverage limits**：真实清单用户确认前 AC-K2-3 记 incomplete（gate）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的 N=10 路径抽查 RED 断言。
- **executed_commands**：原冻结 `-k "n=10"` selector exit 4（非法表达式）；等价 `-k "路径抽查"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T014R/result.json`
- **covered_ac**：AC-K2-3
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：保留冻结 selector 的 exit 4；RED 目标覆盖短路径、长路径和 fixture=None incomplete。
#### T014G — GREEN：N=10 路径抽查

- **ID**：T014G
- **Phase**：Phase P4
- **goal**：实现使 T014R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：Q7·Talk R3 N=10·DEF-K2-2
- **输入**：spec §5（FR-CHK-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-003
- **AC**：AC-K2-3
- **动作**：实现题目清单加载 + BFS 测跳 + gate 语义
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T014R 同 gate_cmd exit 0
- **Knowledge**：实现题目清单加载 + BFS 测跳 + gate 语义；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T014R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "n=10"`
- **expected_exit**：0
- **oracle**：`ORACLE-T014R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T014G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T014R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：query_fixture_sample.json（10 题样例）
- **coverage limits**：真实清单用户确认前 AC-K2-3 记 incomplete（gate）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_nav_check.py` 实现冻结 query fixture 读取、N=10 校验和 BFS 跳数门。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "路径抽查"` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T014G/result.json`
- **covered_ac**：AC-K2-3
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：合法等价 selector 通过；N=10 每题 ≤3 跳为 passed，超跳为 blocked，未填 slug 保持 incomplete。
#### T015R — RED：e2e manifest+cleanup+commit 顺序

- **ID**：T015R
- **Phase**：Phase P4
- **goal**：使 `test_e2e_manifest_and_cleanup` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-004"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-008·OI-12·review B-13
- **输入**：spec §5（FR-CHK-004）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-004/FR-AUD-001
- **AC**：AC-K2-5
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：happy → ①三文件落盘②metrics③manifest navigation 最后写出；blocked → 零落盘+reasons+暂存清空+未触及字段
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T015G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "e2e"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T015R — happy → ①三文件落盘②metrics③manifest navigation 最后写出；blocked → 零落盘+reasons+暂存清空+未触及字段语义相等`
- **evidence_path**：`quality/evidence/build-code/T015R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：happy → ①三文件落盘②metrics③manifest navigation 最后写出；blocked → 零落盘+reasons+暂存清空+未触及字段（同 gate_cmd/oracle）
- **fixtures_services**：全 fixture 套件 + manifest 解析断言
- **coverage limits**：manifest 字节稳定归 K1 真实集成检查点（review B-6）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的端到端 manifest/cleanup/commit RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "e2e"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T015R/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 验证成功落盘、blocked 零导航和 staging 清理目标尚未实现。
#### T015G — GREEN：e2e manifest+cleanup+commit 顺序

- **ID**：T015G
- **Phase**：Phase P4
- **goal**：实现使 T015R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-004"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-008·OI-12·review B-13
- **输入**：spec §5（FR-CHK-004）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-004/FR-AUD-001
- **AC**：AC-K2-5
- **动作**：实现 commit_or_block（顺序 fail-closed + 暂存清理 + manifest 二次落盘）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T015R 同 gate_cmd exit 0
- **Knowledge**：实现 commit_or_block（顺序 fail-closed + 暂存清理 + manifest 二次落盘）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T015R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "e2e"`
- **expected_exit**：0
- **oracle**：`ORACLE-T015R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T015G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T015R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：全 fixture 套件 + manifest 解析断言
- **coverage limits**：manifest 字节稳定归 K1 真实集成检查点（review B-6）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_navigation.py` 实现 staging、导航/metrics/manifest 提交和 blocked 清理。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "e2e"` exit 0；13 passed, 21 deselected。
- **evidence_refs**：`quality/evidence/build-code/T015G/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：成功路径写三层导航并增写 navigation/metrics；blocked 和 commit 写失败路径不伪造成功。
#### T016R — RED：同输入双跑字节一致

- **ID**：T016R
- **Phase**：Phase P4
- **goal**：使 `test_e2e_rerun_bytes` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-009·review R2
- **输入**：spec §5（FR-GEN-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-003/FR §8
- **AC**：AC-K2-6
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：同 fixture 连跑两次 → 三导航文件字节完全一致；第二次零模型调用
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T016G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "同输入双跑字节一致"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T016R — 同 fixture 连跑两次 → 三导航文件字节完全一致；第二次零模型调用`
- **evidence_path**：`quality/evidence/build-code/T016R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：同 fixture 连跑两次 → 三导航文件字节完全一致；第二次零模型调用（同 gate_cmd/oracle）
- **fixtures_services**：双跑 harness（tmp 批次 ×2）
- **coverage limits**：manifest 运行级字段不参与比对（spec SCN-K2-007）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的同输入双跑字节一致 RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "同输入双跑字节一致"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T016R/result.json`
- **covered_ac**：AC-K2-6
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 验证第二次运行应零模型调用且三导航文件字节稳定。
#### T016G — GREEN：同输入双跑字节一致

- **ID**：T016G
- **Phase**：Phase P4
- **goal**：实现使 T016R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-GEN-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-009·review R2
- **输入**：spec §5（FR-GEN-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-GEN-003/FR §8
- **AC**：AC-K2-6
- **动作**：端到端复跑（缓存全命中路径）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T016R 同 gate_cmd exit 0
- **Knowledge**：端到端复跑（缓存全命中路径）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T016R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "同输入双跑字节一致"`
- **expected_exit**：0
- **oracle**：`ORACLE-T016R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T016G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T016R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：双跑 harness（tmp 批次 ×2）
- **coverage limits**：manifest 运行级字段不参与比对（spec SCN-K2-007）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_navigation.py` 以稳定输入/模板/版本生成缓存键并复用模型结果。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "同输入双跑字节一致"` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T016G/result.json`
- **covered_ac**：AC-K2-6
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：第二次 gateway 调用为 0，Home/Index/3 个模块 Index 与首跑字节完全一致。
#### T017R — RED：写路径审计

- **ID**：T017R
- **Phase**：Phase P4
- **goal**：使 `test_e2e_write_audit` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "PFACT-K2-001"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-012·review B（白名单六项）
- **输入**：spec §5（PFACT-K2-001）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：PFACT-K2-001
- **AC**：AC-K2-7
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：批次目录外零写入；批次内仅白名单六项；暂存区终态清空
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T017G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "写路径审计"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T017R — 批次目录外零写入；批次内仅白名单六项；暂存区终态清空`
- **evidence_path**：`quality/evidence/build-code/T017R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：批次目录外零写入；批次内仅白名单六项；暂存区终态清空（同 gate_cmd/oracle）
- **fixtures_services**：写审计桩 fixture
- **coverage limits**：审计桩只在测试注入，生产路径零开销
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的写路径审计 RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "写路径审计"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T017R/result.json`
- **covered_ac**：AC-K2-7
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 验证批次外不得写入、批次内只允许导航和审计白名单路径。
#### T017G — GREEN：写路径审计

- **ID**：T017G
- **Phase**：Phase P4
- **goal**：实现使 T017R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "PFACT-K2-001"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：D-012·review B（白名单六项）
- **输入**：spec §5（PFACT-K2-001）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：PFACT-K2-001
- **AC**：AC-K2-7
- **动作**：实现写操作记录桩（测试注入审计器）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T017R 同 gate_cmd exit 0
- **Knowledge**：实现写操作记录桩（测试注入审计器）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T017R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "写路径审计"`
- **expected_exit**：0
- **oracle**：`ORACLE-T017R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T017G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T017R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：写审计桩 fixture
- **coverage limits**：审计桩只在测试注入，生产路径零开销
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_navigation.py` 将所有写入限制在 staging、三层导航、manifest navigation 和 run-metrics。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "写路径审计"` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T017G/result.json`
- **covered_ac**：AC-K2-7
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：outside sentinel 字节不变；批次新增路径仅白名单，staging 终态不存在。
#### T018R — RED：部分成功对账

- **ID**：T018R
- **Phase**：Phase P4
- **goal**：使 `test_e2e_partial_success` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：Q6·SCN-K2-002·review B-5
- **输入**：spec §5（FR-NAV-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-003/FR-AUD-001
- **AC**：AC-K2-5
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：blocked=[2] → Home 行 blocked_sources=2；navigation 三数对账全等
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T018G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "部分成功对账"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T018R — blocked=[2] → Home 行 blocked_sources=2；navigation 三数对账全等`
- **evidence_path**：`quality/evidence/build-code/T018R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：blocked=[2] → Home 行 blocked_sources=2；navigation 三数对账全等（同 gate_cmd/oracle）
- **fixtures_services**：T007 fixture 变体（blocked 非空）
- **coverage limits**：K1 阻塞清单形态以 manifest blocked 数组为准
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的部分成功三数对账 RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "部分成功对账"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T018R/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 验证 K1 blockers 与 success_pages 应同步到 Home/manifest。
#### T018G — GREEN：部分成功对账

- **ID**：T018G
- **Phase**：Phase P4
- **goal**：实现使 T018R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-003"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：Q6·SCN-K2-002·review B-5
- **输入**：spec §5（FR-NAV-003）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-NAV-003/FR-AUD-001
- **AC**：AC-K2-5
- **动作**：blocked 参数贯通 Home 状态行与 manifest 计数
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T018R 同 gate_cmd exit 0
- **Knowledge**：blocked 参数贯通 Home 状态行与 manifest 计数；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T018R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "部分成功对账"`
- **expected_exit**：0
- **oracle**：`ORACLE-T018R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T018G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T018R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：T007 fixture 变体（blocked 非空）
- **coverage limits**：K1 阻塞清单形态以 manifest blocked 数组为准
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_navigation.py` 将 products 页面数、K1 blockers 长度和 Home 状态行统一记账。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "部分成功对账"` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T018G/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：fixture 中 3 个成功页面、2 个 blockers 在导航结果、Home 和 manifest 对账一致。
#### T019R — RED：blocked 矩阵七情形

- **ID**：T019R
- **Phase**：Phase P4
- **goal**：使 `test_e2e_blocked_matrix` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-004"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：SCN-K2-003…006·review B-12
- **输入**：spec §5（FR-CHK-004）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-004
- **AC**：AC-K2-5
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：模型不可用/空输出/拒绝词/K1 blocked/对账违例/frontmatter 缺字段/零页面七情形 → status+reasons+零落盘+暂存清空+语
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T019G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "blocked"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T019R — 模型不可用/空输出/拒绝词/K1 blocked/对账违例/frontmatter 缺字段/零页面七情形 → status+reasons+零落盘+暂存清空+语义相等`
- **evidence_path**：`quality/evidence/build-code/T019R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：模型不可用/空输出/拒绝词/K1 blocked/对账违例/frontmatter 缺字段/零页面七情形 → status+reasons+零落盘+暂存清空+语（同 gate_cmd/oracle）
- **fixtures_services**：七情形 fixture 矩阵
- **coverage limits**：interrupted（manifest 损坏）另行断言：不写 manifest 显式报告（spec SCN-K2-003）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的七类 blocked 矩阵 RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "blocked"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T019R/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 覆盖模型不可用、空/拒绝、K1 blocked、对账、frontmatter、零页面失败场景。
#### T019G — GREEN：blocked 矩阵七情形

- **ID**：T019G
- **Phase**：Phase P4
- **goal**：实现使 T019R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-CHK-004"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：SCN-K2-003…006·review B-12
- **输入**：spec §5（FR-CHK-004）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：FR-CHK-004
- **AC**：AC-K2-5
- **动作**：参数化端到端（七情形驱动同一断言组）
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T019R 同 gate_cmd exit 0
- **Knowledge**：参数化端到端（七情形驱动同一断言组）；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T019R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "blocked"`
- **expected_exit**：0
- **oracle**：`ORACLE-T019R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T019G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T019R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：七情形 fixture 矩阵
- **coverage limits**：interrupted（manifest 损坏）另行断言：不写 manifest 显式报告（spec SCN-K2-003）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_navigation.py` 统一 blocked reason、清场、K1 字段保留和 manifest blocked 增写。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "blocked"` exit 0；7 passed, 27 deselected。
- **evidence_refs**：`quality/evidence/build-code/T019G/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：七类情形均不落导航、清空 staging、返回 blocked；损坏 manifest 保持原字节不写回。
#### T020R — RED：生产接线

- **ID**：T020R
- **Phase**：Phase P4
- **goal**：使 `test_production_wiring` 因目标断言失败（当前无实现）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "DEC-K2-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：review B-2·B-1
- **输入**：spec §5（DEC-K2-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：DEC-K2-002/003
- **AC**：AC-K2-4(gate)
- **动作**：只写失败测试与必要 fixture 辅助，不改生产代码
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：真实 config 构造 ModelGateway（零网络）+ CacheProtocol 适配点 + K1 挂接签名（三依赖显式注入无默认）
- **Knowledge**：fixture 结构参考 plan Code Anchors；K1 schema 常量在 tests/fixtures/task8_nav/
- **verification_role**：RED
- **paired_task**：T020G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "生产接线"`
- **expected_exit**：非零（断言失败）
- **oracle**：`ORACLE-T020R — 真实 config 构造 ModelGateway（零网络）+ CacheProtocol 适配点 + K1 挂接签名（三依赖显式注入无默认）`
- **evidence_path**：`quality/evidence/build-code/T020R/`
- **STOP**：环境失败、命令损坏、断言写错（改测试而非实现）或需要新设计时停止
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试/环境后重跑 gate
- **task risk**：错误 RED（断言本身写错）导致 GREEN 误实现
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：RED 证据：真实 config 构造 ModelGateway（零网络）+ CacheProtocol 适配点 + K1 挂接签名（三依赖显式注入无默认）（同 gate_cmd/oracle）
- **fixtures_services**：假 config 文件 fixture
- **coverage limits**：DEF-K2-2 未关闭前本卡为 build-code 最后一张卡（gate）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的 config/gateway/cache/入口签名 RED 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "生产接线"` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T020R/result.json`
- **covered_ac**：AC-K2-4(gate)
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 验证三依赖必须显式注入，不能依赖隐式 NullCache/默认参数。
#### T020G — GREEN：生产接线

- **ID**：T020G
- **Phase**：Phase P4
- **goal**：实现使 T020R 的断言通过并保留其负例语义
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "DEC-K2-002"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001..004"}]`
- **source_refs / decision_refs**：review B-2·B-1
- **输入**：spec §5（DEC-K2-002）+ plan Solution Design 对应职责块 + 上游 Phase 产物
- **依赖**：同 Phase 前序卡；详见 Phase 块
- **并行**：否 — 单模块顺序 RED→GREEN
- **FR**：DEC-K2-002/003
- **AC**：AC-K2-4(gate)
- **动作**：实现 config 只读解析 + 入口签名冻结
- **精确文件**：`src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`
- **boundary**：files: `src/knowledge_digest/semantic_navigation.py（本 Phase 职责块）`; symbols/regions: 仅本 Phase 声明的 symbol/region；不得触碰其他职责块
- **输出**：GREEN：T020R 同 gate_cmd exit 0
- **Knowledge**：实现 config 只读解析 + 入口签名冻结；接口签名以 plan Solution Design 为准
- **verification_role**：GREEN
- **paired_task**：T020R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "生产接线"`
- **expected_exit**：0
- **oracle**：`ORACLE-T020R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T020G/`
- **STOP**：实现需要越出 File Boundary / 需要改 spec/plan/tasks 设计时停止（回 stage）
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退本卡实现
- **task risk**：实现引入非确定性（时间戳/随机序/运行级字段入产物）
- **test tier / test method**：feature — Python 模块级单功能域行为变化（批次导航编译器），需目标单测+邻接集成测试（fixture 批次端到端）；无跨端/…
- **scenarios / commands / expected exit / oracle**：GREEN：T020R 同 gate_cmd exit 0（同 gate_cmd/oracle）
- **fixtures_services**：假 config 文件 fixture
- **coverage limits**：DEF-K2-2 未关闭前本卡为 build-code 最后一张卡（gate）
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_nav_check.py` 实现用户配置读取、Jsonl cache/gateway 适配和显式 compile 签名。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "生产接线"` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T020G/result.json`
- **covered_ac**：AC-K2-4(gate)
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：假 config 不发网络即构造 qwen3.8 gateway；cache_root、gateway、query_fixture 均由调用方显式提供。
#### T022R — RED：digest 挂接集成

- **ID**：T022R
- **Phase**：Phase P4
- **goal**：使 test_cli_invokes_navigation_after_compile 失败（当前 semantic_cli.main compile 后无 navigation 调用）
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-001/OI-12"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001"}]`
- **source_refs / decision_refs**：R-011·D-002·OI-12·PFACT-K2-001；plan DEC-K2-001（挂接点 semantic_cli.main）
- **输入**：spec §5 FR-NAV-001 + plan DEC-K2-001 + T020G 完成的库入口
- **依赖**：T020G（库入口冻结后）
- **并行**：否
- **FR**：FR-NAV-001
- **AC**：AC-K2-5（真实链路端到端）
- **动作**：只写失败测试：monkeypatch semantic_navigation.compile_batch_navigation 为探针，跑 semantic_cli.main（fixture 迷你语料 + mock provider）→ 断言探针被调用一次且参数 = BatchResult.output_dir
- **精确文件**：`tests/acceptance/test_task8_entry_navigation.py`
- **boundary**：files: `tests/acceptance/test_task8_entry_navigation.py`; symbols/regions: 仅测试文件
- **输出**：RED 证据：探针调用次数 == 0（AssertionError）
- **Knowledge**：真实链路：simple_cli.main → semantic_cli.main（@55）→ compile_batch（@1459）→ BatchResult.output_dir；当前 compile 后无钩子（已核实）
- **verification_role**：RED
- **paired_task**：T022G
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k cli_hook`
- **expected_exit**：非零（AssertionError）
- **oracle**：`ORACLE-T022R — 探针被调用一次且收到 output_dir`
- **evidence_path**：`quality/evidence/build-code/T022R/`
- **STOP**：semantic_cli 接口变化导致测试无法构造输入时停止（回 plan 修订 DEC-K2-001）
- **recovery**：负责人=build-code 执行者；最小恢复=修正测试构造
- **task risk**：探针断言写错（应断言恰好一次、参数为 output_dir）
- **test tier / test method**：feature — 单功能域行为挂接，邻接集成测试（mock provider）
- **scenarios / commands / expected exit / oracle**：RED 证据：探针调用次数 == 0（AssertionError）（同 gate_cmd/oracle）
- **fixtures_services**：迷你语料 fixture + mock provider + monkeypatch 探针
- **coverage limits**：不验导航内容正确性（库卡已验）；只验调用发生与参数
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`tests/acceptance/test_task8_entry_navigation.py` 的 semantic_cli 挂接 RED 探针。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k cli_hook` RED exit 1。
- **evidence_refs**：`quality/evidence/build-code/T022R/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：RED 证明 compile_batch 后原链路未调用导航入口。

#### T022G — GREEN：digest 挂接集成

- **ID**：T022G
- **Phase**：Phase P4
- **goal**：实现挂接使 T022R 通过：compile_batch 成功后调用 compile_batch_navigation
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind": "spec", "ref": "specs/task8-entry-navigation/spec.md", "hash": "1eee4f77c28bd3193f2ec79a7c02005dc983720ba12ef37e6ea651a6749eb3ec", "id": "FR-NAV-001/OI-12"}, {"artifact_kind": "plan", "ref": "specs/task8-entry-navigation/plan.md", "hash": "f302839b28ddf41d257a9fa6be4a3820ce2aba6fd93a5c4604b68c3efcfd5577", "id": "DEC-K2-001"}]`
- **source_refs / decision_refs**：R-011·D-002·OI-12·PFACT-K2-001；plan DEC-K2-001（挂接点 semantic_cli.main）
- **输入**：spec §5 FR-NAV-001 + plan DEC-K2-001 + T020G 完成的库入口
- **依赖**：T020G（库入口冻结后）
- **并行**：否
- **FR**：FR-NAV-001
- **AC**：AC-K2-5（真实链路端到端）
- **动作**：MODIFY semantic_cli.py：compile_batch 返回后、打印 output 前调用 compile_batch_navigation(batch.output_dir, cache=..., gateway=..., query_fixture=...)（生产依赖按 DEC-K2-002/003 构造），NavigationResult 并入输出 JSON；K1 其余行零改动
- **精确文件**：`src/knowledge_digest/semantic_cli.py`
- **boundary**：files: `src/knowledge_digest/semantic_cli.py`; symbols/regions: 仅 compile_batch 调用点之后 ~10 行挂接区
- **输出**：GREEN：T022R 同 gate_cmd exit 0 + 输出 JSON 含 navigation 节
- **Knowledge**：挂接一行 + 输出合并；gateway 构造失败（无 config）→ 记录 navigation blocked 不使 digest 崩溃（fail-soft 于入口层，批次状态仍由 K2 内部 fail-closed 管辖）
- **verification_role**：GREEN
- **paired_task**：T022R
- **gate_cmd**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k cli_hook`
- **expected_exit**：0
- **oracle**：`ORACLE-T022R 全绿（同 oracle identity）`
- **evidence_path**：`quality/evidence/build-code/T022G/`
- **STOP**：挂接需要改 compile_batch 内部或 K1 其余文件时停止
- **recovery**：负责人=build-code 执行者；最小恢复=git 回退挂接区
- **task risk**：挂接引入循环 import（semantic_cli → semantic_navigation 单向，禁止反向）
- **test tier / test method**：feature — 单功能域行为挂接，邻接集成测试（mock provider）
- **scenarios / commands / expected exit / oracle**：GREEN：T022R 同 gate_cmd exit 0 + 输出 JSON 含 navigation 节（同 gate_cmd/oracle）
- **fixtures_services**：T022R 同款 fixture + DictCache + FakeGateway
- **coverage limits**：不跑真实 provider；真实 89 语料冒烟归 P4 Knowledge 人工项
- **acceptance_role**：implementation
- **ui_scope**：non_ui

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：completed
- **actual_changes**：`semantic_cli.py` 在 compile_batch 后构造三依赖、调用导航并合并输出 JSON。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k cli_hook` exit 0；1 passed, 33 deselected。
- **evidence_refs**：`quality/evidence/build-code/T022G/result.json`
- **covered_ac**：AC-K2-5
- **review_fact**：unavailable — P4 final review route unavailable；见 `quality/evidence/build-code/P4/review.json`
- **completed_at**：2026-09-14T17:40:00Z
- **执行事实**：探针恰好收到 BatchResult.output_dir、cache/gateway/query_fixture 三个显式参数，输出含 navigation 节。

## 跨 Phase 事实

- 基线守卫（实跑 2026-09-14，merge main @361114e 后）：`uv run --frozen pytest --cache-clear -q` = 20 failed, 1010 passed, 4 skipped（1034 收集）；20 失败节点集合与 `tests/fixtures/task8_nav/baseline_failures_20.txt` 完全一致，均为既有 K1/Task2a 基线，不是本卡新增失败。
- 最终验收卡 = T022G；真实 89 语料与已回填 target_slug 的 N=10 路径抽查仍是 P4 Knowledge 未完成项。
- 执行事实回填纪律：每卡完成后在"执行状态填写区"逐字段更新；review_fact 引用 wh-review build-code 面。

## verify-code 代码审查处置（当前实现快照）

- 架构审查发现并已修复：frontmatter/页面路径穿越与符号链接写入边界、Task8/K1 provider 输出契约不匹配、K1 blocked 批次仍创建导航缓存、无效模型结果污染缓存、multipart 页面覆盖统计、CLI 导航失败退出码与结构化状态、manifest 审计字段 fail-open，以及 query fixture 结构校验。
- 受影响回归：`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py` → `40 passed`。
- 独立 `wh-review` 路由：`ROUTE_UNAVAILABLE`（当前 host 不支持 `wh_review.non_stage`），如实保留，不改写为通过。
- 真实 89 条语料 smoke：K1 成功生成 89 来源/87 主题/125 物理页；K2 已进入真实入口，但首次运行因未绑定 query targets/模型输出与暂存 metrics 写入边界阻塞，输入与证据需在 verify-code 收尾继续处理。
