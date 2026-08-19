# 实现计划：KnowledgeDigest 全量 Reader 质量编译器

- **Input**：`specs/task4-reader-quality-compiler/decision-log.md`（D-020–D-025、DEFER-003–006）；`specs/task4-reader-quality-compiler/spec.md`（`efb6acc8b1abf56d1a2c8423193f322e146970471575a7983bc0bc4b6455cc0c`）
- **Template version**：`plan-task.v3`

## Quick Read

- **Goal**：把 89 条样本从“按标题和目录堆 Markdown”变成可读、可追溯、可解释的 Reader：文件名、产品/模块/对象/场景、正文、关系、导航和来源投影全部由同一语义节点驱动；再用机器评估与 CompanyBrain 做全量对照，只有严格不差且至少一个轴更好才允许报告 `better_than_companybrain`。
- **Non-goals**：不把 89 条写死成生产规则；不复制 CompanyBrain 固定目录；不增加人工逐页审查、`human_reviewed`、后台调度、数据库、向量库、agentmemory、未来数万条的吞吐/成本方案（D-024、DEFER-003）。来源：D-024、DEFER-003。
- **Before**：`task4_reader_quality.py` 默认硬编码 `expected_source_count=89`；分类主要靠标题关键词，未命中落入待分类；页面标题/正文/来源链接没有统一语义节点；评估依赖 17+3 旧题集和人工表。
- **After**：编译器使用通用 domain config 和输入 manifest；新节点须证据充分，否则只进 Audit；Reader 只写干净投影；评估使用冻结的 89 来源→M 个 canonical case 映射、固定 evaluator 和可复现的 path/answer/boundary 三轴 oracle，不读人工表。
- **Main risk**：如果语义抽取仍把“分类、文件名、正文”分别猜，输出会继续出现 `ae-`、通用目录、孤立页和正文失真。必须先形成一个 `semantic_node`，再从它生成整条输出链。
- **Next step**：先执行 T001/T003/T005 的 RED 测试；RED 必须先真实失败，才进入对应 GREEN 实现。

## Technical Context

### Global Constraints

- **Verified facts**：入口是 `scripts/task4_reader_quality.py` 的 `compile`/`assess`；实现集中在 `src/knowledge_digest/task4_reader_quality.py`；CompanyBrain 只读；89 条输入 manifest 为 `confluence-raw-89-20260818-v1`，SHA-256 `e1842f683ee3b92fbe532d781a3cd374563ac94e4db3240272238481e33765bf`；当前 CompanyBrain 为 `companybrain-full-20260819-current-v2`，1,406 个非系统文件、716 个正式 Reader Markdown 页，完整 tree hash `dbfd60230790c7774e4a680397074859809dd9a0e5bc93af4c0923f51c27ea22`。
- **Language / runtime**：Python `>=3.11`；使用项目 `uv run --frozen` 和 `pytest`。
- **Primary dependencies**：复用标准库、现有 `PyYAML` 和正式模块；不新增运行时依赖。
- **Storage / state**：输出仍为候选目录 `bundle/`、`audit/`、`reports/`、`status.json`；staging 完成且硬门通过后原子切换 Reader；失败不得留下可读候选。
- **Testing**：临时目录和固定 fixture；离线、不调用网络/LLM；不改原始 89 条和 CompanyBrain；每个行为 RED→GREEN，最后一次聚合回归。
- **Target environment**：本地 macOS；CLI 和 Python API 不绑定当前绝对路径。
- **Scale / scope**：本次只把 89 条做成回归样本；实现必须配置驱动，未来数万条只保留接口兼容，不在本 task 承诺吞吐/成本。
- **Unresolved facts**：真实 M、逐 case 命中和 CompanyBrain 结果需 build-code 实跑生成；未知不能写成通过。词表 schema/version、旧路径迁移、批量并发/成本/恢复留在 DEFER-003–006。

## Code Anchors

- **Task4 anchors**：`src/knowledge_digest/task4_reader_quality.py:_load_config`、`_taxonomy_classification`、`_source_row`、`_extract_content`、`_render_topic_page`、`compile_full_reader`、`_machine_quality`、`assess_reader_quality`；`scripts/task4_reader_quality.py:main`；测试 `tests/acceptance/test_task4_full_compiler.py`、`tests/acceptance/test_task4_full_quality.py`。
- **Formal reusable anchors**：`identity.py:source_id/topic_id/resolve_topic_identity`；`ingest.py:ingest`；`batch_run.py:build_input_manifest`；`topic_axis.py:build_source_inventory/build_topic_plan/topic_index_from_plan`；`draft.py:build_page_draft`；`page_layout.py:build_semantic_parts/validate_semantic_parts/protect_old_page_on_failure`；`reader_bundle.py:project_reader_bundle/validate_reader_bundle`；`navigation.py:build_publication_navigation`；`provenance.py:validate_prewrite_provenance/audit_provenance`；`reader_quality.py:build_reader_snapshot/_reader_route/_source_chain`。
- **Existing interfaces**：`compile_full_reader(raw_root, output, config, cancel_check=None) -> dict`；`assess_reader_quality(...) -> dict`。可调整参数，但 CLI 必须明确迁移/错误，不静默读旧人工表。
- **Read now**：上述锚点、Task2/Task3 acceptance、CompanyBrain 入口和既有比较脚本，均只读。
- **Must read before task**：执行每个 task 前重新读当前四份材料、task 所列符号和测试；符号变化则回 `plan.md`，不猜。
- **Context mode**：`Full` — 同一输出契约跨来源、语义、页面和评估。

### Reuse → Extend → New

| Capability | Decision | Existing anchor | Reason / removal condition |
| --- | --- | --- | --- |
| 来源快照/身份/重复 | reuse + extend | `ingest.py:ingest`, `identity.py` | 复用正式指纹和稳定 ID，Task4 只加候选状态 |
| Product/Module/Object 计划 | reuse + extend | `topic_axis.py` | 不重写分类框架，Task4 增加新节点 admission 和关系 ledger |
| Claim/正文/分页 | reuse + extend | `draft.py`, `page_layout.py` | 复用保真、唯一 Claim ownership、300 行边界 |
| Reader 导航/来源投影/溯源 | reuse + extend | `reader_bundle.py`, `navigation.py`, `provenance.py` | 不平行造一套写回和 route 规则 |
| Task4 语义节点和质量矩阵 | new within adapter | `task4_reader_quality.py` | 只保留 Task4 特有的 node state、relation、case/evaluator；不新建框架 |

## Solution Design

### Overview

先用正式 `ingest`/`identity`/`batch_run` 建立输入 manifest；再为每个来源生成 `semantic_node` 候选：产品/领域、模块、对象或场景、任务、显示名、稳定 key、证据事实、边界和关系。节点状态为 `existing/new_candidate/pending/conflict/failed`；只有名称明确、至少两个互相支持的事实/关系、且不与既有节点冲突的节点进入 Reader。未知不再落入“通用”。

之后调用已有 `topic_axis`、`draft`、`page_layout`、`reader_bundle`、`navigation`、`provenance` 完成路径、标题、正文、关系、来源投影和 staging。Reader 白名单只保留人能读的标题、摘要、答案、规则/边界、关系、来源名称和合法链接；`source_uri`、fingerprint、claim id、provider、Audit 不能泄漏。任一 89 条来源硬失败、manifest 漂移、关键节点冲突或页面越界，包为 `not_released`。

质量评估读取固定 case matrix/evaluator：89 个来源只做覆盖统计，重复来源合并为 M 个 canonical case；两侧分别算首命中路径、答案覆盖、边界/来源清晰度。`N/A`、`unknown`、多路径、oracle 缺失都不能算优势。只有全量覆盖、无关键未知、全轴不差且至少一个轴严格更好才报告 `better_than_companybrain`。

### Module responsibilities

#### Task4 adapter

- **Responsibility**：编排正式模块，补充 Task4 semantic node、scenario/relation ledger、Reader projection 和质量报告。
- **Consumes**：通用 domain config、source manifest、`semantic-baseline-v1`、`page-type-registry-v1`、既有候选节点。
- **Produces**：source/topic/claim/index、Reader bundle、Audit、root-cause、quality reports。
- **Must not decide**：不以 CompanyBrain 路径当分类真相；不以人工状态当发布条件；不把未知写成通过。

#### Machine evaluator

- **Responsibility**：按冻结 protocol 对 KD/CompanyBrain 做同一批量计算。
- **Consumes**：Reader projection、CompanyBrain、case matrix、evaluator config、baseline manifest。
- **Produces**：machine quality、comparison、receipt、root cause、release summary。
- **Must not decide**：不改 Reader、不补写内容、不读人工表。

### Interfaces, data, and lifecycle

- **Schemas**：新增 `task4-source-coverage.v1`、`task4-reader-case-matrix.v1`、`task4-semantic-baseline.v1`、`task4-page-type-registry.v1`、`task4-reader-evaluator.v1`；质量配置只引用它们。
- **Case matrix**：必须含 89 行 `source_to_case_map`、M 个 canonical case、page type、criticality、required evidence/answer/boundary/relation；source denominator=89，Reader denominator=M。
- **State**：`source_snapshot → valid|duplicate|degraded|failed → identified → existing|new_candidate|pending|conflict|failed → claim_candidate → reader_candidate → published|degraded → not_released|released`。
- **CLI**：`compile --raw-input --output --config`；`assess --candidate --companybrain --quality-config --output`。不再提供或消费 `--human-review-table`。
- **Fail-loud**：manifest 漂移、全量来源不完整、证据不足、冲突、坏链接、Reader 泄漏、页超限、case/evaluator/hash 不一致均返回明确 reason code。

## File Boundary

### NEW

- `config/task4-source-coverage-89-input.v1.json` — 当前 89 条真实来源的只读覆盖 fixture、manifest id/hash；不作为生产路径规则。
- `config/task4-reader-case-matrix-89-input.v1.json` — 89→M 的 canonical case 和 source map。
- `config/task4-semantic-baseline.v1.json` — 当前既有 Product/Module/Object/Relation 基线的版本化摘要；未来新域以配置版本替换。
- `config/task4-page-type-registry.v1.json` — page type 与必需 section/body oracle。
- `config/task4-reader-evaluator.v1.json` — reader evaluator、reader compare、三轴公式、N/A/unknown/criticality。

### MODIFY

- `config/task4-reader-quality.v1.json` — 通用 source/domain/semantic 配置，并引用上述 fixture；删除生产默认 expected_source_count=89。
- `src/knowledge_digest/task4_reader_quality.py` — Task4 薄适配层、semantic node 状态、Reader/Audit 分离、机器评估。
- `scripts/task4_reader_quality.py` — 新配置/评估参数，移除人工表入口。
- `tests/acceptance/test_task4_full_compiler.py` — 全量来源、命名、分类、节点状态、正文、关系、导航、溯源、失败边界。
- `tests/acceptance/test_task4_full_quality.py` — canonical case、三轴 oracle、N/A/unknown、无人工输入和严格聚合。

### DO NOT TOUCH

- `specs/task4-reader-quality-compiler/decision-log.md`、`spec.md` — 当前方向已确认，本阶段只写计划。
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain`、`/Users/Hugh/Downloads/confluence 原始数据`、既有真实产物 — 只读。
- `config/task4-question-oracle.v1.json` — 17+3 历史 pilot fixture，保留但新评估不消费。
- `pipeline.py`、`reader_bundle.py`、`reader_quality.py`、`topic_axis.py`、`publication.py`、`writeback.py` — 作为既有能力复用，不改正式边界。

## Technical Decisions

### DEC-001 — 一个 semantic node 驱动整条输出链

- **Problem**：当前分类、文件名、页面标题、正文和关系各自猜，造成 `ae-`、通用目录、孤立链接和正文失真。
- **Options**：A 分别修五处；B 复制 CompanyBrain 目录；C 先建节点再生成整条链。
- **Selected**：C，extend Task4 adapter，复用正式模块。
- **Reason**：一次决定同时约束 path/title/body/relations/provenance，最少隐含条件；CompanyBrain 的优势是编辑后的语义结构，不是固定目录。
- **Consequence / risk**：要定义节点状态和证据门；不足则降级而不强行输出。
- **Fallback**：pending/conflict/failed 只写 Audit，包不发布。
- **F10 disposition**：`keep` — 直接解决真实失败，不另建 gate 平台。

### DEC-002 — 新模块/对象不默认归入通用

- **Problem**：未命中的来源被伪装为已分类。
- **Options**：A 默认通用；B 全部人工分类；C 证据充分才进 Reader，否则 Audit。
- **Selected**：C，配置驱动、机器判定。
- **Reason**：支持未来新知识，又不污染读者入口，不需逐页人工。
- **Consequence / risk**：证据不足会使包 `not_released`，但能定位到来源和第一失败阶段。
- **Fallback**：保留来源、证据、候选名和 reason code。
- **F10 disposition**：`keep`。

### DEC-003 — M 个 canonical case，不使用人工表

- **Problem**：17+3 和人工表不能覆盖 89 条，也不能稳定证明更好。
- **Options**：A 继续人工逐题；B 只做结构分；C 固定 89→M 映射和机器 oracle。
- **Selected**：C。
- **Reason**：一批命令覆盖全样本，重复来源不重复计分，路径/答案/边界可追溯。
- **Consequence / risk**：oracle 质量影响结论；缺失/冲突必须 unknown。
- **Fallback**：报告 `undecidable` 和具体 case，不报告“更好”。
- **F10 disposition**：`keep`。

### DEC-004 — 样本 fixture 与生产规则分离

- **Problem**：当前配置把 89 和当前路径写进默认逻辑。
- **Options**：A 继续写死；B 删除样本验收；C 只把 89 的 manifest/case/baseline 放 fixture。
- **Selected**：C。
- **Reason**：保留可重复回归，并用配置变体证明没有源路径硬编码。
- **Consequence / risk**：样本变更须换 manifest id/hash，不覆盖历史。
- **Fallback**：manifest 不匹配就 fail-closed。
- **F10 disposition**：`keep`。

## Test Strategy

设计 RED/GREEN，不在 build-plan 执行命令；RED/GREEN 使用同一 `gate_cmd` 和 oracle identity。

| Target | Task | Role | gate_cmd / expected_exit | Oracle / evidence_path |
| --- | --- | --- | --- | --- |
| FR-SOURCE-001/002、FR-SEMANTIC-001/002；AC-SOURCE-001/002、AC-COMPILER-001/002 | T001/T002 | RED/GREEN | `env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py` / 非零→0 | `ORACLE-COMPILER-FULL`；89 manifest、身份、全量失败边界，`quality/evidence/build-plan/T001-T002-compiler.json` |
| FR-SEMANTIC-003/004/005、FR-READER-001/002、FR-AUDIT-001/002；AC-COMPILER-003/004/005、AC-READER-001/002、AC-AUDIT-001/002 | T003/T004 | RED/GREEN | 同上 / 非零→0 | `ORACLE-SEMANTIC-READER`；命名、分类、正文、关系、Reader/Audit、变体配置，`quality/evidence/build-plan/T003-T004-semantic.json` |
| FR-READER-003/004、FR-QUALITY-001/002/003；AC-READER-003/004、AC-QUALITY-001–005、AC-STATE-001/002 | T005/T006 | RED/GREEN | `env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_quality.py` / 非零→0 | `ORACLE-READER-COMPARE`；M cases、三轴、N/A/unknown、无人工表，`quality/evidence/build-plan/T005-T006-quality.json` |
| 全部适用 FR/AC 与 seam | T007 | FINAL | `env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_task4_full_compiler.py tests/acceptance/test_task4_full_quality.py tests/acceptance/test_task4_location_compiler.py tests/acceptance/test_task4_location_gate.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2b_body_compiler.py tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task3_projection.py tests/acceptance/test_task3_quality_release.py tests/acceptance/test_task3_closeout.py` / 0 | `ORACLE-FINAL-TASK4`；结构回归和边界事实，`quality/evidence/build-plan/T007-final.json` |

## Rollback and Recovery

- **Global recovery rule**：只回滚 Task4 实现和新 fixture，保留四份材料、旧历史 fixture、既有 Audit、原始输入和 CompanyBrain；不直接改基线。
- **Irreversible boundaries**：build-plan 只写方案；commit/push/merge/archive/cleanup 分别授权；候选只有明确 `released` 才能成为正式入口。
- **Recovery owner**：build-code 执行者按 task boundary 恢复；先回到受影响 RED/GREEN，再运行同一命令，不用全量结果掩盖局部失败。

### Engineering Risk Handoff

- **Affected IDs**：FR-SEMANTIC-002/003、FR-READER-001/002、FR-QUALITY-001/002/003、FR-SOURCE-002、AC-COMPILER-002/003、AC-READER-001/002、AC-QUALITY-001–005、AC-STATE-001/002。
- **Trigger**：单证据进 Reader、Reader 泄漏 Audit、case/oracle 失配、取消/权限/manifest 变化或 staging 失败。
- **Consequence**：出现“看似分类、实际不懂”、错误宣称更好、或旧 Reader 被错误替换。
- **Mitigation or STOP**：semantic node 准入要求明确名称+两条互相支持证据+无冲突；Reader projection 白名单；hash、唯一 key→entry path、N/A/unknown/criticality 分支；staging+原子切换。任一证据或全量硬门缺失立即停止发布并保留 Audit。
- **Handling Stage**：build-code；质量结论由 verify-code 复核。
- **Verification**：正例、单证据负例、冲突负例、Reader 泄漏扫描、case/oracle 负例、取消/权限/manifest drift 和旧 Reader 保护测试。

- **PLAN-RISK-001**：节点 admission 过宽。**Affected**：FR-SEMANTIC-002/003、AC-COMPILER-002/003。**Trigger**：单一标题/事实也进 Reader。**Consequence**：重现“看似分类、实际不懂”。**Mitigation/STOP**：名称+两条互相支持证据+无冲突；不足只 Audit。**Stage**：build-code。**Verification**：正例、单证据负例、冲突负例。
- **PLAN-RISK-002**：Reader 泄漏 Audit。**Affected**：FR-READER-001/002、AC-READER-001/002。**Trigger**：页面出现 uri/fingerprint/provider/claim id 或链接 audit。**Consequence**：读者看到内部实现。**Mitigation/STOP**：Reader projection 白名单和全量扫描。**Stage**：build-code。
- **PLAN-RISK-003**：case/oracle 失配。**Affected**：FR-QUALITY-001–003、AC-QUALITY-001–005。**Trigger**：重复计分、多路径、N/A 算优势、缺 oracle 当 0。**Consequence**：错误宣称更好。**Mitigation/STOP**：hash、唯一 key→entry path、N/A/unknown/criticality 分支；否则 undecidable。**Stage**：build-code。
- **PLAN-RISK-004**：失败留下旧 Reader。**Affected**：FR-SOURCE-002、AC-STATE-001/002。**Trigger**：取消、权限、manifest 变化。**Consequence**：用户误读旧候选。**Mitigation/STOP**：staging+原子切换，硬失败清除当前候选入口。**Stage**：build-code。

### Required Engineering Risk Fields

- **Affected IDs**：FR-SEMANTIC-002/003、FR-READER-001/002、FR-QUALITY-001/002/003、FR-SOURCE-002、AC-COMPILER-002/003、AC-READER-001/002、AC-QUALITY-001–005、AC-STATE-001/002。
- **Trigger**：单证据进 Reader、Reader 泄漏 Audit、case/oracle 失配、取消/权限/manifest 变化或 staging 失败。
- **Consequence**：出现“看似分类、实际不懂”、错误宣称更好、或旧 Reader 被错误替换。
- **Mitigation or STOP**：semantic node 准入要求明确名称+两条互相支持证据+无冲突；Reader projection 白名单；hash、唯一 key→entry path、N/A/unknown/criticality 分支；staging+原子切换。任一证据或全量硬门缺失立即停止发布并保留 Audit。
- **Handling Stage**：build-code；质量结论由 verify-code 复核。
- **Verification**：正例、单证据负例、冲突负例、Reader 泄漏扫描、case/oracle 负例、取消/权限/manifest drift 和旧 Reader 保护测试。

## Implementation Order

T001/T002 先固定来源和基础节点；T003/T004 再生成 Reader；T005/T006 最后消费稳定页面做批量对照；T007 只做聚合。顺序是 producer→consumer，避免评估器反过来决定页面路径。

## Dependencies and Parallelism

- **Dependencies**：T001→T002；T003→T004；T005→T006；T002/T004→T005；T006→T007。
- **Parallel work**：无并行写入；Task4 module 和两组测试共享接口，强行并行会冲突。
- **External dependencies**：无网络、无 provider、无新依赖；CompanyBrain 和原始语料只读。

## Requirement and Verification Traceability

| Source / decision | FR | AC | Phase / Task | Depends on | Exact files | Command / oracle |
| --- | --- | --- | --- | --- | --- | --- |
| R1/R2、D-020/D-024 | FR-SOURCE-001/002 | AC-SOURCE-001/002 | P1/T001–T002 | none | source config; Task4 module; compiler test | compiler / ORACLE-COMPILER-FULL |
| R1/R2、D-020/D-021/D-022 | FR-SEMANTIC-001–005 | AC-COMPILER-001–005 | P1/T003–T004 | T002 | baseline/page registry; Task4 module; compiler test | compiler / ORACLE-SEMANTIC-READER |
| R1/R2、D-022 | FR-READER-001–004、FR-AUDIT-001–003 | AC-READER-001–004、AC-AUDIT-001/002 | P1/T003–T004 | T002 | Task4 module/script; compiler test | compiler / ORACLE-SEMANTIC-READER |
| R3/R4、D-023/D-024 | FR-QUALITY-001–003 | AC-QUALITY-001–005 | P1/T005–T006 | T004 | case matrix/evaluator/config/module/script/quality test | quality / ORACLE-READER-COMPARE |
| R1–R4、PFACT-006/007 | all applicable | AC-STATE-001/002 | P1/T007 | T006 | all Task4 files + regression tests | final / ORACLE-FINAL-TASK4 |

## Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| 四份材料 | `spec.md`, `decision-log.md` | no change | all | 方向已冻结 |
| 计划/任务 | `plan.md`, `tasks.md` | change | build-plan | 本阶段唯一写入范围 |
| 配置/fixture | `config/task4-*.json` | change | T001–T006 | 样本与生产分离 |
| 实现/CLI | Task4 module/script | change | T002/T004/T006 | 编译与评估 |
| 验收测试 | 两个 Task4 acceptance | change | T001–T007 | RED/GREEN 与聚合 |
| WorkflowHub 宪法/技能 | `/Users/Hugh/Hugh/Project/workflowhub/CONSTITUTION.md` | no change | all | 只读绑定 |

## Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"/Users/Hugh/Hugh/Project/workflowhub/CONSTITUTION.md","hash":"d17c85373e30c4733a77b19dc260373268fca6dd29b8ac3574c8a35b4da6ebd5","id":"CONSTITUTION","version":"1.5.0","clause_count":21}`
- **Constitution checklist hash**：`368817c2910a36e63d3ab4642c30270abdecef15dee7caf8050e778f095919ca`
- **F1**：Task4 adapter 编译业务，WorkflowHub 只编排；不改核心。
- **F2**：CLI、config、manifest、bundle/report 是窄文件契约；内部状态不进入 Reader。
- **F3**：四份材料决定继续；candidate/released 和质量结论分离，失败 fail-loud。
- **F4**：保留独立 review 事实；finding 记录处置，不把 review 伪装成测试通过。
- **F5**：只保留 manifest、泄漏、oracle、原子发布检查这些真实问题对应的关卡。
- **F6**：运行事实写外置 `quality/*`；方案不绑定临时 runner。
- **F7**：build-plan 是本次业务确认边界；不可逆操作另行授权。
- **F8**：复用正式模块、标准库和 acceptance，不新建框架。
- **F9**：缺 source/case/oracle 显示 failed/unknown/undecidable，禁止假绿。
- **F10**：新增 fixture 直接解决复现和错误对比，不建设 gate 平台；未来不需要时可删除样本 fixture。
- **Q1**：质量事实用于报告和完成判断，不是开工许可证。
- **Q2**：推进、发布结构、阶段完成分开；candidate 不等于 released。
- **Q3**：保留一次异源 plan review；本地测试只证明实现事实。
- **S1**：复用现有 Reader/provenance/route 能力和测试技能。
- **S2**：配置和 adapter 可就地改造，不引入不合宪框架。
- **S3**：不新增外部技能依赖。
- **S4**：扩展 source/case/path/answer/boundary 指标进入既有报告。
- **S5**：任务按模块和测试边界拆分；子代理只做只读调研。
- **S6**：依据 CompanyBrain 实际语义结构和现有 Task2/3 实现，不凭空造目录。
- **S7**：本次是单一 Task4 workflow，不拆无实际阶段的新技能目录。
- **S8**：CLI 使用相对输入/config/output 参数，可脱离当前绝对路径运行。

## Phase P1 — 语义 Reader 编译与机器质量对照

### Goal

一次编译覆盖全部输入，生成可读语义路径/正文/关系和干净 Reader；一次评估覆盖全部 canonical case，严格、可追溯地回答是否比 CompanyBrain 好。

### Files

- **NEW**：`config/task4-source-coverage-89-input.v1.json`；`config/task4-reader-case-matrix-89-input.v1.json`；`config/task4-semantic-baseline.v1.json`；`config/task4-page-type-registry.v1.json`；`config/task4-reader-evaluator.v1.json`
- **MODIFY**：`config/task4-reader-quality.v1.json`；`src/knowledge_digest/task4_reader_quality.py`；`scripts/task4_reader_quality.py`；`tests/acceptance/test_task4_full_compiler.py`；`tests/acceptance/test_task4_full_quality.py`
- **DO NOT TOUCH**：`decision-log.md`、`spec.md`、原始 89 条、CompanyBrain、`config/task4-question-oracle.v1.json`、正式 Task1–Task3 模块。

### Tasks

- `T001/T002`：来源、语义节点和全量失败边界。
- `T003/T004`：命名、分类、正文、关系、导航、溯源和 Reader/Audit 分离。
- `T005/T006`：case matrix、evaluator、三轴、N/A/unknown、无人工表和 CLI。
- `T007`：最终聚合、当前快照事实和 verify-code 交接；不新建发布状态。

### Verify

按 T001–T007 的同命令同 oracle 执行；最终命令覆盖 Task4 全量和 Task2/Task3 相关回归。任何 `not_released`、`undecidable`、unknown 或剩余严重 finding 都如实交接。

### Knowledge

交给 verify-code 的事实必须包括：真实 M、每个 case 的 unique baseline path、所有 source/semantic state、所有 Reader 页的标题/路径/正文/关系/来源投影、失败根因链和当前是否仅 candidate。

### STOP

若要新增目录模型、重新定义“更好”、补人工评审或改变 89/未来数万条边界，回到 `spec.md`/`decision-log.md`；若只是实现错误，回到对应 RED/GREEN task。

### Done

实现、聚焦测试、最终聚合、一次独立 review、逐 AC 事实和大白话交接齐全，才能进入 verify-code；测试通过不等于 CompanyBrain 质量已被证明。

### Risks and rollback

优先回滚 Task4 实现和新 fixture 到最后一组通过的 RED/GREEN；保留原始和审计材料；质量结论回退到 `undecidable/not_released`，不保留误导性 candidate。
