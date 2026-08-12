# Task 2-B 知识发布正文编译实施计划

- **Input**：当前 root `decision-log.md`、`specs/task2b-knowledge-publication-body-compiler/spec.md`；同目录 `decision-log.md` 是只读旧 receipt，不是执行依据。
- **Template version**：`plan-task.v3`

## 1. 速读卡

- **Goal**：让小语料的三类主题页按固定 section 生成可读正文；每条正文事实可回查；受影响 section 不留旧说法；机器失败进入 `degraded`，整包保持 `not_released`。
- **Non-goals**：不做 Task 2-C 人工读者门、全量 89 篇正式发布、完整 17+3 题集出口、数据库、向量库、第二套导航或 UI。来源：`R-004`、`R-005`、`D-001`–`D-005`；本次 `SR-20260811-task2b-procedure-source-gap` 只修订受影响的 `procedure_or_rule.exceptions` section。
- **Before（需 build-code 首卡回读核验）**：当前实现被观察为仍围绕完整 `final_body` 和 Evidence 保真合同，正式布局主要按 Claim/Evidence 分页；`old_target_body`、section 依赖和安全复用没有形成可判定闭环。本段是待核验的实现假设，不是冻结接口。
- **After**：现有 S1–S6 管线先确定 page type 和受控 section，再让 provider 只填 section 正文；Publication Gate 检查归因、关键事实、版本、重复、边界和状态；布局与原有导航/写回共用一条链。
- **Main risk**：section 影响闭包或版本无法证明时，如果仍复用旧正文，会把过期说法带回 Reader。
- **Next step**：不重开 T001→T014；按本计划末尾的 `SR-20260811-task2b-procedure-source-gap` 交接回 `build-code`，只补受影响 section 的实现/测试，再重新取得相关运行证据；缺样本或 provider 证据只记 `incomplete/not_released`。

### Scope revision addendum：SR-20260811-task2b-procedure-source-gap

- **状态**：`in_progress`；同一 Task 2-B，不创建 successor task，不重置既有 T001–T014。
- **触发阶段 / 返回阶段**：`verify-code` → `build-code`。
- **原始需求**：真实 `procedure_or_rule` 来源只比较三种方案，没有明确异常触发、处理、分支或恢复规则；不能为了补齐正文而编造异常内容，也不能让旧 section 残留过期说法。
- **本次选择**：固定 `exceptions` section 保留；确定性来源审计确认没有异常规则时写入 section-level `source_not_documented`，异常专属问题为 `not_answerable`；其他 section 和既有机器门通过时，页面仍可 `published` 并计入 `procedure_or_rule` 覆盖。
- **不变边界**：不新增 page type、页级状态、交付状态、必需 section、机器阈值或 Task 2-C/Task 3 交付；含糊来源、审计不完整、provider 映射/归因失败仍 `degraded/not_released`。
- **范围**：受影响 ID 为 `PFACT-007`、`FR-DRAFT-004`、`FR-PUBLISH-006`、`FR-SEM-003`、`AC-13`、`T009`、`T010`、新增 `T015`–`T016`；未受影响卡片不返工。
- **WorkflowHub 事实**：当前主分支没有可执行的独立 `scope_revision` review 路由；不得把已有 C1 detail review 冒充该审查。缺失的专用审查记录为 `missing/incomplete`，但不阻塞本次同任务材料修订和后续 `build-code`。

## 2. Technical Context and Constraints

候选实现事实包括 `draft.py` 的生成上下文、`llm.py` 的 provider seam、`faithfulness.py` 的 Claim 回查、`page_layout.py` 的主题布局、`navigation.py` 的统一导航和 `pipeline.py` 的原子写回/降级路径；这些都须在 build-code 启动时回读核验。Task 2-B 用核验后的现有 seam 扩展数据，不建立平行编译器。

### Global Constraints

- 四份当前材料是唯一产品与执行依据；旧 receipt 只读，不作为本计划的实现门槛。
- `spec.md` 顶部的“草稿”是 build-spec 遗留的阶段标签，不表示本计划可以补产品需求；产品方向、FR 和 AC 以当前 `decision-log.md`/`spec.md` 为准，build-plan 的正式接受仍由本阶段人确认单独完成。
- 生产 provider identity 是 build-code 启动时必须从当前代码/配置和运行环境回读核验的 `EXTERNAL-STATE`，本计划不预先冻结 model 或 base URL。凭据只来自环境变量，不写入 prompt、结果、测试 fixture 或证据；T013 仍必须读取并记录实际 model、base URL、detector、budget、threshold，缺失或不一致就记 `incomplete/not_released`。
- `product_overview`、`module_or_capability`、`procedure_or_rule` 是唯一 page type；provider 不能增加 page type、section、来源字段或没有 Claim 支持的新事实。
- **Deletion proofs**：本期不涉及删除；不删除旧正式页、旧分页、历史归档、Task 2-A 文件或现有导航记录，只新增/更新本计划声明的正文编译与机器状态结果。
- 影响闭包不可证明时必须整页重编；整页失败不覆盖旧 Reader 正式页，当前结果进入 Audit/Archive 并标记 `degraded`。
- 不拼接新旧正文；可复用 section 必须同时证明依赖集合、归因和版本未变，并保留可验证的 section 记录。
- 正文最多 120 行，整页最多 300 行；先按语义边界拆分，再按容量分页；总览页、稳定 related key、`prev/next` 和唯一 Claim part 约束不能被行数门掩盖。
- Task 2-A 的 Reader Bundle、Frontmatter、稳定主题身份和现有写回边界是上游合同；本计划不改它们，也不建立第二套 Reader 入口。
- Task 2-B 的页级 `published/degraded` 与交付级 `not_released` 分开；机器通过不等于人工读者通过或正式 `released`。
- `procedure_or_rule.exceptions` 永远保留；只有绑定冻结来源 URI、content hash、locator（如适用）和 audit version 的确定性来源审计，才能产生 section-level `source_not_documented`。它不是异常 Claim、不是“暂无异常”，也不能跨主题找材料补写。
- `source_not_documented` 不改变页级 `published/degraded`、交付级 `not_released`、`>=6`、三类 page type、inventory coverage、provenance/faithfulness/version/duplicate 等既有机器门；异常专属题目保持 `not_answerable`。
- 本次 `SR-20260811-task2b-procedure-source-gap` 是唯一一次 contract revision（`1/1`）；后续只允许修实现 bug，不得再次改变 section、字段、状态语义或 page type 映射。
- `PFACT-004`、`PFACT-005`、`PFACT-006` 尚未形成当前运行值；T001–T012 的离线行为任务不依赖真实样本 manifest 或 provider 运行值，可以先行；T013 开始前必须回读样本清单并冻结 provider/detector/budget/threshold/section dependency，不能在计划里猜值。

## 3. Code Anchors

以下 Code Anchors 都是 build-code 启动时必须回读的候选 seam，不是本阶段已经批准的签名；任一符号、调用关系或状态出口不一致，按 T002/T012 STOP，不由实现者自行补接口：

- `src/knowledge_digest/draft.py`：`draft`、`_generation_contexts`、`_candidate_from_result` 和 `old_target_body` 上下文是候选 PageDraft/Provider 输入出口；同一 seam 承担确定性的 Structure Normalizer adapter，把标题/H1、父子关系、FAQ、表格、图片、双语、版本和噪声片段整理为带 source locator/content type 的结构记录。
- `src/knowledge_digest/llm.py`：`build_prompt`、`parse_response`、`build_generator` 和 `validate_publication_provider_identity` 是候选 provider 边界；调整输出为受控 section，不放宽 provider 身份。
- `src/knowledge_digest/publication.py`：现有 `validate_publication_suggestion` 及 publication metadata 校验是候选 page type、section contract 和 Publication Gate 复用点。
- `src/knowledge_digest/faithfulness.py`：`verify_claims`、`normalize_for_gate`、`claim_entity_key` 是候选 Claim、关键 token 和重复检测输入。
- `src/knowledge_digest/page_layout.py`：`_render_page`、`_partition`、`build_topic_layouts` 是候选固定页面骨架、语义拆分、Claim 唯一归属和旧页历史保护入口。
- `src/knowledge_digest/navigation.py`：`_topic_rows`、`_expanded_navigation`、`build_publication_navigation` 是候选 Home/分类/主题导航入口，prev/next 只能接在这里。
- `src/knowledge_digest/pipeline.py`：`audit_run`、`draft`/`build_topic_layouts` 调用、Reader/Audit 过滤、`_commit_outputs` 和运行报告是候选状态、原子写回和交付出口；T011/T012 将先回读 `audit_run` 是否为正式端到端入口。

## 4. Solution Design

### 数据流

1. 复用 ingest、Task 1 TopicIndex、稳定 topic identity 和现有 Claim 记录，由 `draft.py` 的 Structure Normalizer adapter 先形成带父子关系、标题/H1、FAQ、表格、图片、双语、版本线索、source locator、content type 和失败原因的结构片段；无法回查来源的片段必须排除或把页面标为 `degraded`。
2. 在 `draft.py` 形成唯一的 typed PageDraft：page type、固定 section 清单、每个 section 的 source/claim/version 依赖集合、归因集合和输入指纹都由受信代码产生。
3. `llm.py` 只把允许的 section、受信 Claim 标识和 `old_target_body` 修订上下文给 provider；provider 返回 section 内容和 Claim 引用，解析器拒绝未知 section、未知 page type、未知来源字段、截断和无依据事实。
4. `faithfulness.py` 与 `publication.py` 对 section/page 运行归因、数字/标识符/版本、命令/端口/配置、表格/图片、连续逐字块、同页/跨页近重复和 golden-negative 检查，保留失败样本、分母、detector version、seed 和输入指纹。
5. `page_layout.py` 只消费通过编译的 section 记录：先按产品/模块/能力/步骤/问题语义拆分，再按 120/300 行硬边界分 part；每个 Claim 只有一个 part，part-1 保持主题主入口。
6. `navigation.py` 继续渲染现有 Home、分类和主题索引，并从当前通过的 layout 生成总览、related key、`prev/next`；`pipeline.py` 只把机器门通过的页送入 Reader，失败页留在 Audit/Archive，写回继续使用既有原子边界。

### 固定 section 与 provider 边界

- `product_overview`：定位、适用场景、能力边界、入口、来源；版本只有在来源有可回查版本时出现。
- `module_or_capability`：目的、能力、入口/前置、关系、限制、版本、来源。
- `procedure_or_rule`：前置、步骤/规则、异常、限制、版本、来源。
- section 缺少必需证据时不写占位句；provider 不负责选择结构合同、来源字段或 page type。

### 影响闭包与更新

- 比较当前来源/Claim/版本/结构关系指纹与既有 section dependency record；依赖集合、归因、版本完全一致才允许字节级复用。
- 任何来源变化先求反向影响闭包；受影响 section 必须整段重编并使旧 signal/归因失效，不能把新 section 与旧 section 直接拼接。
- 既有页缺少可审计 dependency record、版本冲突、归因不唯一或结构关系不明时，影响状态为 uncertain，扩大为整页重编。
- 整页失败时只记录失败结果和恢复依据；旧正式页保持原 bytes、原导航状态和历史价值，不被失败结果覆盖。

### section dependency record v1

每个 section 必须携带一个确定性、可序列化的 `section-dependency-record.v1`，作为复用和影响闭包的唯一比较对象：

```json
{
  "schema_version": "section-dependency-record.v1",
  "topic_id": "stable topic identity",
  "page_type": "product_overview|module_or_capability|procedure_or_rule",
  "section_id": "controlled section id",
  "source_deps": [{"source_uri": "...", "content_hash": "...", "fragment_locator": "..."}],
  "claim_deps": [{"claim_id": "...", "claim_fingerprint": "..."}],
  "version_deps": [{"field": "...", "normalized_value": "...", "claim_id": "..."}],
  "structure_deps": [{"fragment_locator": "...", "relation_type": "...", "structure_hash": "..."}],
  "attribution_deps": [{"claim_id": "...", "source_uri": "...", "content_hash": "...", "fragment_locator": "..."}],
  "dependency_hash": "sha256(canonical-json-of-sorted-dependency-fields)"
}
```

- 所有数组按稳定 key 排序，canonical JSON 不含运行时间、输入顺序或 provider 文案；`dependency_hash` 只对上述依赖字段计算。
- 记录先作为 `PageDraft.sections[*].dependency_record` 和 layout record 的内部 typed data 传递，再随 Audit/Archive/run evidence 序列化；不新增数据库、队列或第二套持久化入口。
- 依赖、归因、版本三组指纹完全一致且记录版本可识别时才允许 section 字节复用；旧页没有 v1 记录或字段缺失直接是 uncertain，走整页重编。

### 机器语义出口

- T013 只使用权威文件 `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json` 指定的 12–20 篇上游冻结样本和 Task 0 17+3 题集派生的确定性 answerability 可答子集；preflight 必须记录该文件存在性和 content hash，不在实现阶段临时换题、删题或重抽样。
- T013 开始前写入 manifest，包含样本逐项 source/topic/page-type、`sample_count`、`sampling_seed`、inventory 类别、provider/model、budget、seed、threshold、detector version、归因和失败项；运行 record 还必须绑定 `answerability_source`、由 Task 0 17+3 题集确定性派生的 answerability subset id/hash、逐题 answerability 与 `first_hit`、`evidence_backtrace`（至少含 `claim_id` 和 `fragment_locator`）、逐 section `section_completeness`、失败原因、`ac_bindings`（至少显式覆盖 AC-01、AC-03、AC-05、AC-07、AC-09、AC-10、AC-11、AC-12、AC-13，其中 AC-12/AC-13 由 revision ledger 和来源缺口 section 状态绑定）以及 `contract_revision`/revision ledger；其中未冻结的 PFACT-004/005 值必须先补事实，缺失时 T013 直接记 `incomplete/not_released`。
- T013 的 semantic evidence 必须由同一次 `digest` 运行产生：运行前把 `apply/evidence/T013.semantic-run.json` 解析为绝对路径，通过 `KNOWLEDGEDIGEST_TASK2B_SEMANTIC_EVIDENCE` 传给该进程；路径在运行前不得已存在，digest/pipeline 必须写入包含 `run_id`、sample/KB/input 指纹和 `output_path` 的新文件，随后 validator 只读取同一路径并核对本次运行身份。路径不存在、不是本次运行产物或仍是旧文件时，gate 非零并记录 incomplete。
- 只有至少 6 个 `machine-passing concept` 且三类 page type 各至少 1 个、实际 inventory 类别均有覆盖、真实语义运行完整时，机器出口才可记为满足；否则仍为 `not_released`。

## 5. File Boundary

### NEW

- `tests/acceptance/test_task2b_body_compiler.py`
- `tests/fixtures/task2b_publication_body/cases.json`

semantic_evidence_file 的正负 fixture 只放在上述 cases.json 的固定键下；不新增第三个 fixture 文件。

### MODIFY

- `src/knowledge_digest/draft.py`
- `src/knowledge_digest/llm.py`
- `src/knowledge_digest/publication.py`
- `src/knowledge_digest/faithfulness.py`
- `src/knowledge_digest/page_layout.py`
- `src/knowledge_digest/navigation.py`
- `src/knowledge_digest/pipeline.py`

### DO NOT TOUCH

- `specs/task2b-knowledge-publication-body-compiler/decision-log.md`
- `specs/task2b-knowledge-publication-body-compiler/spec.md`
- `docs/plans/knowledge-digest-knowledge-publication-prd.md`
- `src/knowledge_digest/reader_bundle.py`
- `src/knowledge_digest/reader_frontmatter.py`
- `src/knowledge_digest/topic_axis.py`
- `src/knowledge_digest/writeback.py`
- `src/knowledge_digest/cli.py`
- `config/knowledge-digest.json`
- `AGENTS.md`

- **接口边界**：扩展 `draft` context/result、provider JSON 的受控 section 表达、layout record 的 section/dependency/impact 元数据和 pipeline 状态/语义 evidence 汇总；保持现有 `draft`、`build_topic_layouts`、`build_publication_navigation`、`audit_run` 调用的兼容入口，不改 CLI 参数和 Reader Bundle schema。
- **兼容边界**：Task 2-A 既有测试和 formal S1–S6 离线路径继续可运行；旧正式页不删除、不被失败覆盖；现有 source/Claim/provenance、Home→分类→主题入口和原子 writeback 继续唯一生效。

## 6. Technical Decisions

### DEC-001：沿用现有 S1–S6 seam

- **Selected**：extend existing `draft.py`、`publication.py`、`page_layout.py`、`pipeline.py` seam，并让 `llm.py`/`faithfulness.py` 提供受控 section 校验。
- **Reason**：这些模块已经拥有 Claim、provider、布局、导航和原子写回的真实调用链；增加第二套 compiler 或第二套导航会制造状态分叉。
- **Consequence**：PageDraft、Publication Gate 和 OKF projection 以内部 typed records 组合，不新增永久数据库或后台运行时。

### DEC-002：section reuse 采用保守可证明规则

- **Selected**：只有 dependency、attribution、version 三组指纹均一致时复用；任何缺记录或不确定状态都走整页重编。
- **Reason**：用户明确要求评估受影响 section，避免旧 section 残留过期说法；保守兜底的成本低于错误 Reader 事实。
- **Consequence**：可能多调用 provider，但不会用不确定的局部复用掩盖页面级一致性风险。

### DEC-003：真实运行复用普通 CLI

- **Selected**：reuse the existing `digest` CLI on an isolated frozen sample input and an isolated KB, with runtime evidence written outside product source files。
- **Reason**：普通 CLI 已经绑定正常 ingest、draft、layout、navigation、writeback 和审计链；不为一次语义运行维护第二个执行器。
- **Consequence**：T001–T012 先完成离线行为 RED/GREEN；T013 开始前由实现者回读并绑定样本目录、KB 目录、provider credential、model/base URL、manifest、detector、budget、threshold 和 answerability 证据。缺任何一项都记 `incomplete/not_released`。provider identity 只作为待核验的代码/环境事实，不由本计划预先选择。

### DEC-004：依赖记录采用 v1 canonical JSON

- **Selected**：section 依赖使用上面的 `section-dependency-record.v1`；内部由 PageDraft/layout record 携带，Audit/Archive/run evidence 保存序列化副本。
- **Reason**：D-002 要求只复用可证明未受影响的 section，OPEN-003 又要求本任务冻结可审计格式；固定字段和排序规则才能让 T005/T006 真的比较依赖、归因、版本和结构，而不是靠实现者口头解释。
- **Consequence**：记录字段成为 Task 2-B 内部 contract；旧页没有 v1 record 时一律 uncertain/整页重编，不补猜历史依赖。它是 OPEN-003 授权的内部 typed/audit expression，不改变 Reader section 集合、模板、必需/可选字段或 page type 映射；本 DEC 本身不消耗已由 SR-20260811 唯一占用的 `contract_revision=1/1` 预算。

### DEC-005：冻结来源缺少异常规则时的 section 状态

- **Selected**：沿用 `procedure_or_rule.exceptions` 固定 section；确定性来源审计确认来源没有明确异常触发、处理、分支或恢复规则时，使用 `source_not_documented`。不生成异常 Claim，不写占位句，异常题标记 `not_answerable`；其余 section 和机器门通过时允许页面进入 Reader 候选并计入该 page type 覆盖。
- **Reason**：真实冻结来源没有这类事实；硬填会编造，直接整页降级又会误伤同页有证据的前置/步骤/限制内容。该规则同时保护保真和可读性。
- **Consequence**：这是 section-level 状态，不是页级成功或异常已解决；来源含糊、审计不完整、provider 映射失败或归因失败仍必须 `degraded/not_released`。本决定消耗唯一 `contract revision = 1/1`。

## 7. Test Strategy

本计划只设计 RED/GREEN，不运行测试。测试路线为 `feature`：核心是本地 Python 内容编译和 S1–S6 seam，最终补一组兼容回归；无浏览器、无 UI、无用户权限态，因此这些维度记为 N/A，不用空测试代替。

### 风险维度与 oracle

- 行为与数据流：固定 section、provider 越界、Claim 回查、影响闭包、语义分页和状态流转。
- 错误/取消/恢复：provider 失败、截断、未知依赖、版本冲突、golden-negative、未完成语义运行都必须 fail-closed。
- 原子性与并发：失败整页不覆盖旧正式页；复用只允许同一输入指纹；同一主题不拼两次结果。
- 跨模块 seam：`draft → publication/faithfulness → page_layout → navigation → pipeline`，并回归 Task 2-A Reader Bundle 输入/入口合同。
- 可观测性：输出 section dependency、impact、claim mapping、输入指纹、失败原因和语义 manifest；不泄露凭据。
- 不适用：UI 加载/可访问性、权限模型、网络服务并发；本期交付是人工触发的本地 Markdown 管线。

### 证据约定

每个 RED/GREEN 使用同一命令和同一 `ORACLE-*` 身份；RED 必须因目标断言失败而非环境损坏退出非零，GREEN 退出 0 且保留负例；证据路径都是 task-relative `apply/evidence/...`。T013/T014 是非行为验证，使用 `N/A — ...`，不绕过行为配对。

## 8. Rollback and Recovery

- 代码回滚只恢复本计划 MODIFY 文件中的当前 Task 变更；删除本计划 NEW 的测试/fixture 文件即可，不动旧正式 KB、Task 2-A 文件和历史归档。
- 回滚后运行 `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2_publication.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2a_reader_frontmatter.py tests/acceptance/test_task2a_okf_smoke.py -q'`，以既有 publication、批恢复、corpus 和 Reader Bundle 断言为 oracle。
- 语义运行失败只回收本次隔离 sample KB 和运行证据，不回写正式知识库；保留 provider 失败、manifest 缺失或 detector 不完整的原始事实，交接给 Task 2-C/Task 3。

### Engineering Risk Handoff

- **Affected IDs**：`PFACT-007`、`FR-DRAFT-004`、`FR-PUBLISH-006`、`FR-SEM-003`、`AC-13`、`T009`、`T010`、`T015`、`T016`；原有 `FR-DRAFT-003`/`FR-PUBLISH-002`/`FR-PUBLISH-003` 的受影响 section 行为只做兼容核验，不重写未受影响合同。
- **Trigger**：依赖/归因/版本无法证明，样本 manifest 或 provider/detector/budget 未冻结，或 RED/GREEN 命令无法区分目标断言与环境失败。
- **Consequence**：可能残留旧 section、错误进入 Reader，或把离线/Jaccard/provider 成功误报成语义出口。
- **Mitigation or STOP**：影响不确定扩大整页；缺 manifest/运行值记 `incomplete/not_released`；RED setup 失败、边界漂移或需要改变 section/page type 时停止并回到对应当前材料。
- **Handling Stage**：build-code；本 SR 已经批准 `exceptions=source_not_documented` 的 section 规则。如果再改 page type、必需 section、机器阈值、页级状态或交付状态，才停止并回到对应当前材料，不在实现中补需求。
- **Verification**：`ORACLE-T2B-IMPACT-CLOSURE`、`ORACLE-T2B-SEMANTIC-EXIT-GATE`、`ORACLE-T2B-SEMANTIC-RUN`、`ORACLE-T2B-FINAL-REGRESSION` 及对应 evidence refs。

## 9. Implementation Order

串行顺序为：T001 RED → T002 GREEN → T003 RED → T004 GREEN → T005 RED → T006 GREEN → T007 RED → T008 GREEN → T009 RED → T010 GREEN → T011 RED → T012 GREEN → T013 真实语义运行记录 → T014 最终回归。每个 GREEN 只修复前一张 RED 的目标行为，不弱化断言。

## 10. Dependencies and Parallelism

- T001/T002 先冻结 section contract 和 fixture；T003/T004 依赖它才能定义正文与 Evidence 的边界。
- T005/T006 依赖 section dependency record；T007/T008 依赖通过编译的 section；T009/T010 依赖稳定的 page/layout/gate 结果；T011/T012 依赖完整 pipeline seam；T013 依赖所有行为 GREEN 和上游 manifest/provider facts；T014 依赖 T013 的真实状态记录。
- 不并行：所有行为任务共享同一 compiler contract 和同一测试 fixture；并行会让 RED/GREEN 或 page status 互相污染。
- 外部依赖：上游 Task 2-A current aggregate、权威样本清单 `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`、Task 0 question set、运行前回读的 provider identity 和环境凭据。当前值未完全回读；T001–T012 不依赖这些运行值，T013 只记录实际事实或 `incomplete`；清单路径不存在或 hash 无法回读时不得用新 fixture 代替。

## 11. Requirement and Verification Traceability

| Source / decision | FR | AC | Task | Depends on | Exact files | Gate / oracle |
|---|---|---|---|---|---|---|
| `R-003`、`R-004`、`D-001` | `FR-FLOW-001`、`FR-FLOW-002`、`FR-DRAFT-001` | `AC-01`、`AC-02` | `T001`、`T002` | none → T001 | `tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json`、`src/knowledge_digest/draft.py`、`src/knowledge_digest/llm.py` | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k typed_sections'` / `ORACLE-T2B-TYPED-SECTIONS` |
| `R-004`、`D-001` | `FR-FLOW-002`、`FR-DRAFT-002`、`FR-PUBLISH-001`、`FR-PUBLISH-002` | `AC-03`、`AC-04`、`AC-12` | `T003`、`T004` | T002 → T003 | `src/knowledge_digest/faithfulness.py`、`src/knowledge_digest/publication.py`、`src/knowledge_digest/llm.py`、`src/knowledge_digest/draft.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json` | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k provenance_gate'` / `ORACLE-T2B-PROVENANCE-GATE` |
| `R-004`、`D-002`、`D-003` | `FR-DRAFT-003`、`FR-PUBLISH-003`、`FR-PUBLISH-004`、`FR-COMPAT-001` | `AC-05`、`AC-06`、`AC-07` | `T005`、`T006` | T004 → T005 | `src/knowledge_digest/draft.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_task2b_body_compiler.py` | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k impact_closure'` / `ORACLE-T2B-IMPACT-CLOSURE` |
| `R-004`、`D-001` | `FR-PUBLISH-005`、`FR-COMPAT-001` | `AC-04`、`AC-08` | `T007`、`T008` | T006 → T007 | `src/knowledge_digest/page_layout.py`、`src/knowledge_digest/navigation.py`、`src/knowledge_digest/faithfulness.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json` | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_split'` / `ORACLE-T2B-SEMANTIC-SPLIT` |
| `R-004`、`D-004`、`D-005` | `FR-SEM-001`、`FR-SEM-002`、`FR-SEM-003`、`FR-PUBLISH-003`、`FR-PUBLISH-006` | `AC-09`、`AC-10`、`AC-11`、`AC-12`、`AC-13` | `T009`、`T010` | T008 → T009 | `src/knowledge_digest/publication.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json` | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k semantic_exit'` / `ORACLE-T2B-SEMANTIC-EXIT-GATE` |
| `D-005`、`SR-20260811-task2b-procedure-source-gap` | `FR-DRAFT-004`、`FR-PUBLISH-006`、`FR-SEM-003`、受影响的 `FR-DRAFT-001`/`FR-PUBLISH-002` | `AC-02`、`AC-07`、`AC-09`、`AC-11`、`AC-13` | `T009`、`T010`、`T015`、`T016` | T014 的既有事实 → T015 | `src/knowledge_digest/draft.py`、`src/knowledge_digest/publication.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/llm.py`、`tests/acceptance/test_task2b_body_compiler.py`、`tests/fixtures/task2b_publication_body/cases.json` | `source_not_documented` section audit + `ORACLE-T2B-SOURCE-GAP-SECTION` / `ORACLE-T2B-SEMANTIC-RUN` |
| `R-005`、`D-001`、`D-003` | `FR-FLOW-001`、`FR-PUBLISH-001`、`FR-PUBLISH-003`、`FR-COMPAT-001` | `AC-01`、`AC-03`、`AC-07`、`AC-08` | `T011`、`T012` | T010 → T011 | `src/knowledge_digest/pipeline.py`、`src/knowledge_digest/navigation.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/draft.py`、`tests/acceptance/test_task2b_body_compiler.py` | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2b_body_compiler.py -q -k pipeline_compat'` / `ORACLE-T2B-PIPELINE-COMPAT` |
| `R-004`、`D-004`、`D-005` | `FR-SEM-001`、`FR-SEM-002`、`FR-SEM-003`、`FR-PUBLISH-003`、`FR-PUBLISH-006` | `AC-01`、`AC-03`、`AC-05`、`AC-07`、`AC-09`、`AC-10`、`AC-11`、`AC-12`、`AC-13` | `T013` | T012（所有行为 GREEN + manifest/provider preflight） | `tests/acceptance/test_task2b_body_compiler.py` | `digest` CLI + `semantic_evidence_file` machine assertion / `ORACLE-T2B-SEMANTIC-RUN` |
| `R-003`–`R-005`、`D-001`–`D-005` | `FR-FLOW-001`–`FR-SEM-003`、`FR-COMPAT-001` | `AC-01`–`AC-13` | `T014` | T013 | `tests/acceptance/test_task2b_body_compiler.py` | `semantic_evidence_file` validator on T013 evidence + existing Task 2/2-A regression / `ORACLE-T2B-FINAL-REGRESSION` |

## 12. Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
|---|---|---|---|---|
| Current product materials | root `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` | SR update | SR-20260811... | 本次只更新受影响 section 和交接；同目录旧 decision-log 只读，不是执行依据 |
| Task 2-A Reader contract | `reader_bundle.py`、`reader_frontmatter.py` | no change | T011、T012、T014 | 只做兼容回归，不建第二套入口 |
| Formal pipeline | `draft.py`、`llm.py`、`publication.py`、`faithfulness.py`、`page_layout.py`、`navigation.py`、`pipeline.py` | change | T001–T012、T015–T016 | 一条正文编译、来源缺口 section 状态、机器门、导航和状态数据流 |
| Acceptance fixtures | `test_task2b_body_compiler.py`、`cases.json` | change | T001–T014 | 固定正例、负例、缺类排除和证据出口 |

## 13. Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"constitution-checklist.md","hash":"368817c2910a36e63d3ab4642c30270abdecef15dee7caf8050e778f095919ca","id":"CONSTITUTION","version":"current","clause_count":21}`
- F1：需求、实现、测试和证据保持同一条可追溯链。
- F2：失败、缺失和 provider 不可用都显式暴露，不伪造成功。
- F3：当前状态与历史归档分离，失败不覆盖旧正式页。
- F4：来源、Claim、版本和结构关系保持可回查。
- F5：写回、导航和页面状态使用既有单写者边界。
- F6：测试 oracle 必须观察行为结果，不以文件存在代替通过。
- F7：外部 provider、凭据和运行值必须有边界和事实记录。
- F8：优先复用现有模块，不引入第二执行器、数据库或长期队列。
- F9：每个关键门都有可重复的 RED/GREEN 或明确的 N/A 理由。
- F10：任何扩展都必须有真实防御对象、现有覆盖差距、不可绕过性和可接受维护成本。
- Q1：小范围、可逆、可审计地修改现有生产链。
- Q2：先验证边界和失败路径，再扩大运行范围。
- Q3：交付事实、review 事实和用户确认分开记录。
- S1：不改变用户已确认的产品方向。
- S2：不让实现阶段补 page type、section 或阈值需求。
- S3：不删除旧正式页和历史证据。
- S4：不泄露凭据或把 provider 输出当成可信事实。
- S5：不绕过正常 CLI、导航和 writeback 链。
- S6：不以离线/Jaccard/结构通过代替真实语义出口。
- S7：机器 `published/degraded` 与交付 `not_released` 分离。
- S8：未决事实进入 STOP 和延期交接，不静默猜测。

## Phase 1：受控正文编译与机器出口

### Goal

完成三类 page type 的受控 section 正文、Claim 回查、影响闭包、语义分页、状态出口和 Task 2-A 兼容回归。

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

T001/T002、T003/T004、T005/T006、T007/T008、T009/T010、T011/T012、T013、T014，按 Implementation Order 串行执行。

### Verify

先逐对运行 focused RED/GREEN，再执行 T013 的真实语义命令和 T014 的 Task 2-B/Task 2-A/Task 2 相关回归；每张卡把实际 exit、oracle、失败样本和 evidence ref 写回自己的 task-relative 路径。

### Knowledge

实现者必须回读并核验当前 `draft`、`build_topic_layouts`、`build_publication_navigation`、`audit_run` 和 provider identity seam；不得从旧 receipt、历史计划或 provider 空结果推导通过。

### STOP

T001–T012 允许在没有真实样本逐项清单和 provider 运行值时完成离线行为验证；T013 开始前必须拿到样本 manifest、provider/model/detector/budget/threshold、Task 0 answerability 派生集和 section dependency v1 证据。T013 任一事实缺失时停止真实语义运行并记录 `incomplete/not_released`。本 SR 允许在已确认的 `source_not_documented` section 合同内补 T015/T016；若再要求改变固定 section/page type/页级状态/交付状态或机器阈值，才停止并回到对应当前材料。

### Done

所有行为卡的 GREEN 使用同一 oracle 保住正例和 golden-negative；T013 留下真实语义运行事实或诚实的 `incomplete/not_released`；T014 回归不破坏 Task 2-A 和旧正式页保护。

### Risks and rollback

主要风险是影响闭包漏记、provider 越界和旧页覆盖；回滚只恢复本 Phase 当前代码/fixture bytes，隔离 KB 不写入正式库，按 Rollback and Recovery 的命令复核。

## 14. Current execution status (2026-08-11)

- T001–T012 的行为实现与回归已完成；最近一次完整回归为 `500 passed, 3 skipped`，`git diff --check` 通过。
- T013 已使用冻结 sample manifest 恢复的真实本地原始来源完成一次普通 `digest` 运行；证据为 `apply/evidence/T013.semantic-run-v16.json`，状态为 `completed` 但交付仍为 `not_released`。
- 该运行得到 `6` 个 machine-passing concepts，其中 `5` 个 `module_or_capability`、`1` 个 `product_overview`；`procedure_or_rule` 因真实来源缺少可回查的 `exceptions` section claim mapping 而保持 degraded。不得通过猜测 page type、填空正文或降低机器门解决。
- 当前只继续到 verify-code；verify-code 之后必须停在 close 前。未取得的独立审查、人工确认和 procedure 语义出口证据均记录为 `missing/unknown/incomplete`，不把测试绿灯当作 Task 2-B 完成。

### Scope revision handoff（2026-08-11）

- `SR-20260811-task2b-procedure-source-gap` 已写入当前 root `decision-log.md`、本 `spec.md`、本 `plan.md` 和 `tasks.md`；不重开既有 T001–T014。
- 当前唯一新增产品规则是：`procedure_or_rule.exceptions` 在确定性来源审计证明无异常规则时使用 `source_not_documented`；异常题 `not_answerable`；不写领域 Claim 或占位句；其余 section/机器门通过时可进入 Reader 候选并计入 page-type 覆盖。
- 下一阶段回到 `build-code`，只实现/验证 `T015`、`T016`；必须覆盖正例、来源含糊/审计不完整/provider 映射失败负例，以及旧 section 不残留的影响闭包断言。既有语义门和交付 `not_released` 边界不降低。
- 当前 WorkflowHub 主分支没有可执行的独立 `scope_revision` review 路由；本事实已记录为 `missing/incomplete`，不把已有一次 C1 detail review 冒充 SR review，也不重复既有阶段审查。

### 快捷范围调整执行边界（2026-08-12）

- 受影响材料只追加当前 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 的范围绑定；不重跑完整 WorkflowHub 阶段链，也不调用已移除的公开 `scope_revision` review kind。
- 先修 Task 1：从真实 source declaration 的显式 page-type 元数据生成带 source URI、content fingerprint、locator 和 topic identity 的新 TopicIndex/entry snapshot，并对账通过后才允许 T013。
- Task 2-B 只重跑现有 T013/T014 和当前普通阶段检查；不改 body/section contract、阈值、provider、样本选择或失败语义。
- 旧快照不可覆盖；入口修复失败、快照对账失败或语义门失败均保留 `incomplete/not_released`，Task 2-C 不启动。

### 快捷路径执行结果（2026-08-12）

- Task 1 current snapshot and reconciliation completed from the real 89-source corpus. The current TopicIndex carries only explicit source-declared page types; no title/body classifier or Task 2-B overlay was used.
- T013 consumed the current snapshot and completed a real qwen3.6 run (`15/15` calls), but failed the unchanged machine exit with one passing concept and only `module_or_capability`; `product_overview` and `procedure_or_rule` coverage are absent. Evidence remains `not_released`.
- T014 current regression is complete: Task 1 focused `49 passed`; consumer set `262 passed, 2 skipped`; full repository `516 passed, 3 skipped`; `git diff --check` passed.
- Handoff: remain at the current Task 2-B boundary. Do not commit/merge/push/clean as a completed delivery, and do not begin Task 2-C. A future run needs genuine semantic exit evidence and current ordinary-stage evidence; deterministic tests alone are insufficient.

### SR build-code result（2026-08-11）

- `T015` 已完成：确定性 `procedure-exceptions-audit.v1`、可信 section 状态、正文/Claim 禁写、answerability `not_answerable` 和依赖闭包已落到实现与 acceptance tests。
- 当前证据：`apply/evidence/SR-20260811-source-gap-section-focused.txt`；focused=`72 passed`，consumer=`164 passed`，full=`511 passed, 3 skipped`，`git diff --check`=`0`。
- `T016` 仍 pending：需要用当前材料重跑/验证 T013/T014 真实语义证据；不把 focused/full tests 当语义出口，不替换 provider/阈值，不重复异源审查，不调用 `close`。

## 2026-08-12 当前机器出口收敛

- T013 current evidence=`apply/evidence/T013.semantic-run-task2b-provider-repair-v9-20260812.json`; run_id=`run-519d5c93591e45faab8e3ef56601a3f1`; sha256=`c38aad3185bd534ee988766d55fc26ee68d5f8b2688f8e00ddb72d23dbbd17e4`; canonical validator=`valid=true`、`machine_exit_passed=true`。
- Machine result: 12 passing concepts; page-type counts `module_or_capability=10`、`product_overview=1`、`procedure_or_rule=1`。真实运行仍以 `delivery_status=not_released` 结束。
- T014 current evidence=`apply/evidence/T014.final-regression-task2b-provider-repair-v9-20260812.txt`；Task 1=`49 passed`、consumer=`264 passed, 2 skipped`、full=`518 passed, 3 skipped`、`git diff --check` pass。
- Implementation note: provider repair remains bounded; the Publication Gate thresholds are unchanged. Confirmed raw source stacks may be shortened to a safe Reader prefix while complete source Claims remain in Evidence; uncertain/paraphrased failures remain degraded。
- Handoff: Task 2-C is not started. Its next owner must run `make-decision` for the human reader-quality direction and must not treat this machine result as human acceptance or formal release. Git delivery/closeout remains a separate authorized operation。
