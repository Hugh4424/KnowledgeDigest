# Task 0 决策记录：诚实化与交付包

## 目标

让 KnowledgeDigest 把“已写入”“机器通过”“页面可读”和“正式发布”分开记录；任何来源缺失、失败或证据不闭合都不能被包装成成功交付。

## 任务边界

- 任务：KnowledgeDigest Task 0
- 来源：`docs/plans/knowledge-digest-knowledge-publication-prd.md` v1.2
- 阶段：`make-decision`
- 代码基线：任务启动时的干净 `main` 工作树
- 本记录只决定 Task 0 方向，不进入 `build-spec`、`build-plan` 或实现阶段。

## 范围

覆盖 PRD Task 0 的 manifest/snapshot/ledger 对账、写回前 S6 与交付门禁、来源级失败隔离、页级和交付级状态、Reader/Audit allowlist、导航入口、重跑幂等、题集 manifest 和离线/fallback 合同；实现仍由后续阶段执行。

## 原始需求

KnowledgeDigest 当前把 provider 成功、Claim 验证、写回成功和知识质量发布混成一个“成功”。Task 0 需要让系统诚实：建立 `input manifest → source snapshots → audit ledger` 对账链；把 provenance、Claim、路径、状态和交付包事实移到写回前；失败来源不进入正式导航；Reader Package 与 Audit/Archive Package 分离；同一运行重跑不重复增长业务结果；Task 0–2 不能把整包标为 `released`。

Task 0 不做产品词典、TopicIndex、类型化正文编译、全量重新发布、数据库/图谱/向量库/调度器/AgentMemory 正式接入，也不迁移或重写历史 Task2 结果。

## 关键事实

### 代码事实

- `src/knowledge_digest/pipeline.py:863-915` 当前先写回，再执行 provenance、claim-history 和 source-index；Task 0 必须把写前阻断事实补齐。
- `src/knowledge_digest/provenance.py:49-70` 当前只为成功写入页面上的有效 Claim 生成审计记录。
- `src/knowledge_digest/navigation.py:146-161` 当前无条件生成 pending 入口；新运行必须只在真实有待处理项时生成。
- `src/knowledge_digest/kb_structure.py:16-26` 当前默认使用 `_digest/source-index.md`；本任务的新 Reader Package 不再生成这个兼容投影，统一使用 `indexes/sources.md`。
- `src/knowledge_digest/draft.py:1047-1064,1124-1132,1483-1484` 当前记录 provider failure，但失败结果仍可能走 Claim fallback 进入写回；Task 0 必须阻断其进入正式导航。
- 现有 acceptance 测试覆盖旧 S1–S6、写回、归档和部分重跑，但没有覆盖 manifest 闭环、Reader/Audit allowlist、页级/交付级状态和写前 S6 阻断；相关测试入口见 `tests/acceptance/test_phase0_digest.py`、`test_publication_contract.py`、`test_task2_batch_recovery.py` 和 `test_phase2_5_append_only_durability.py`。

### 文档事实

- `docs/adr/0004-reader-publication-separate-from-audit.md` 已记录读者入口与审计数据分离；本任务只补充路径和状态合同，不新增重复 ADR。
- `AGENTS.md` 已规定 `Home.md → indexes/<category>.md → pages/...` 为阅读入口，并要求失败不伪装成功。
- `CONTEXT.md` 原先没有 Reader/Audit Package、`published/degraded`、`released/not_released` 和业务幂等的唯一解释；本阶段已补充这些领域术语。

## Talk 记录

### Round 1：问题和成功标准

- 用户选择：只处理后续新运行，不迁移、不重写历史 Task2 结果。
- 用户选择：部分来源失败时按来源隔离为 `degraded`，无关内容继续处理；整包仍为 `not_released`。
- 理由：缩小破坏面，保留历史证据；单个坏来源不能拖垮无关内容，也不能伪装成正式发布。

### Round 2：方向和范围

- 用户选择：Task 0 生成候选 Reader Package，只放 `published` 页面；整包仍为 `not_released`，不覆盖旧正式包。
- 用户选择：新运行不生成 `_digest/source-index.md`，统一使用 `indexes/sources.md`；历史结果不迁移、不重写。
- 理由：最终产物结构要简单、干净，减少无用兼容文件和维护成本；Reader/Audit 只能有一个事实源。

### Round 3：盲审发现和剩余风险

- 用户选择：保留 PRD 中 Task 0 的完整范围；“诚实化”是核心，账本、分包、状态、导航是配套验收，不拆成新的 WorkflowHub 任务。
- 用户选择：重跑要求业务结果幂等，审计运行记录允许追加；来源、Claim、页面、duplicate 和 archive 内容不得重复增长。
- 理由：既不牺牲审计历史，也不接受业务产物和归档内容无边界膨胀。

## 决定

Task 0 做一个以“发布诚实”为核心的完整交付边界：

1. 写回前闭合 manifest、snapshot、Claim、provenance、路径、状态和交付包事实。
2. Provider 失败、JSON 损坏、无正文、无归属和事实冲突只生成 `degraded` 审计内容，不进入正式导航。
3. Reader Package 与 Audit/Archive Package 按 allowlist 分离；Reader Package 不含 `_digest`、`_archive`、provider 日志、模型原始响应或运行现场。
4. 新 Reader Package 的来源入口固定为 `indexes/sources.md`；不再生成 `_digest/source-index.md`。历史结果只读保留，不迁移、不重写。
5. 同一输入快照和配置重跑时，业务结果和归档内容幂等；运行记录可追加。
6. 页级状态只用 `published/degraded`；交付级状态只用 `released/not_released`；Task 0 只能产生 `not_released`。
7. 无真实待处理项时不生成 pending 入口；空分类、断链和不可点击来源入口直接失败。
8. 失败运行不能覆盖旧正式页面；无关已发布页面不因单个来源失败而整库回滚。
9. 冻结并落盘 17 个正向问题和 3 个负向问题的 manifest，保存原文、入口、期望主题/产品、覆盖角色、负向设计原则、抽样 seed、评审人和 hash；Task 2 只取样本可回答的派生子集，Task 3 执行完整题集。
10. 对同一 snapshot、claim、duplicate 的重复运行和归档增长做审计报告；异常增长必须可定位，但不设置全局文件体积阈值。
11. 语义 provider 只允许 PRD 约定的 `qwen3.6` 和 `jina-embeddings`；`--no-llm` 使用 Jaccard 且零 LLM/embedding 网络调用；语义 embedding 探测失败只能按既有合同整次回退 Jaccard，并在 manifest/status 标明，要求语义发布时交付级仍为 `not_released`。
12. 实现前需要冻结 timeout、replay、call、wall-clock 预算；超限不能改写为成功。

## 三轮 talk

三轮 Talk 的原始选择和理由见上面的 `## Talk 记录`；其中所有用户选择均已写成下面的决定、范围、风险和延期交接，不依赖后续阶段补需求。

## 用户流程和页面范围

### 操作人流程

1. 用户准备来源并手动触发 `digest`。
2. 系统冻结输入 manifest 和 source snapshot。
3. 系统核对 Claim、重复来源、历史记录、路径和 provenance。
4. 写回前完成账本和交付包门禁。
5. 合格页面进入候选 Reader Package；失败内容进入 Audit/Archive Package。
6. Task 0 输出明确的页级状态和 `not_released` 交付状态。
7. 重跑同一快照时复用已有业务结果，不重复追加业务归档内容；运行记录保留审计历史。

### 阅读者流程

`Reader Package/README.md → Home.md → 产品/模块索引 → 正式主题页 → indexes/sources.md → Audit/Archive（需要审计时）`

Reader Package 只承担阅读；Audit/Archive Package 承担恢复、审计和失败排查。Task 0 不负责产品/模块语义页和正文编译。

## 状态合同

| 层级 | 状态 | 含义 |
|---|---|---|
| 页级 | `published` | 通过机器门，可进入候选 Reader Package |
| 页级 | `degraded` | 失败、冲突、缺证据或人工修改冲突，不进正式导航 |
| 交付级 | `released` | 仅 Task 3 完成机器门、读者门和交付门后允许 |
| 交付级 | `not_released` | Task 0–2 固定状态，或任一交付门未通过 |

`provider transport`、Claim verification、writeback、`machine_pass`、`agent_assisted`、`human_reviewed` 是独立证据；`written` 不等于 `published` 或 `released`。

## 成功边界

- manifest、snapshot、audit ledger 来源集合闭合；缺失来源显式失败。
- 写回前完成 provenance、Claim、路径、状态和交付包检查。
- 失败、冲突、无正文和无归属来源不进入正式导航。
- Reader/Audit 包符合 allowlist；Reader 不含审计现场。
- Home、分类、`indexes/sources.md` 无空页、断链和不可点击链接。
- 同一快照重跑不重复增长来源、Claim、页面、duplicate 和 archive 内容。
- `--no-llm + Jaccard` 零 LLM、零 embedding 网络调用。
- Task 0 输出交付级 `not_released`。
- 17+3 题集 manifest 可重放，字段完整且 hash 可校验；重复运行和异常 archive/duplicate 增长能在 audit report 中定位。

## 失败边界

- manifest、snapshot、ledger 不一致：写前失败，不产生新的正式页面。
- provider 失败、JSON 损坏、无正文、无归属或冲突：页级 `degraded`，只进入 Audit/Archive。
- 空 pending、空分类、断链、不可点击链接：直接失败。
- 语义运行 embedding fallback：必须写入 manifest/status；若本次要求语义发布，交付级仍为 `not_released`。
- 人工修改的正式托管页：不得静默覆盖，保留旧页并标记冲突。
- 单个来源失败：隔离受影响内容，不整库回滚无关已发布页。

## 非目标

- 不做 ProductGazetteer、TopicIndex、稳定主题主轴和三类正文编译。
- 不做全量 89 篇重发布。
- 不改写历史 Task2 结果、旧正式页或旧审计证据。
- 不引入数据库、图数据库、向量数据库、CAS、调度器、后台守护或 AgentMemory 正式接入。
- 不建立永久人工审核队列。
- 不在本任务清理仓库；文档同步、归档和清理属于 Task 3-Closeout。
- 不把正文语义质量、完整题集读者验收或 `released` 判定提前伪造成 Task 0 完成；Task 0 只冻结其输入合同和独立状态字段。

## 延期交接

- Task 1：ProductGazetteer、TopicIndex、稳定主题 key、路径和 affected set。
- Task 2：结构归一化、三类正文编译、claim-id、12–20 篇样本和读者题集子集。
- Task 3：89 篇全量 Reader/Audit Package、完整题集、人工读者门和 `released` 判定。
- Task 3-Closeout：根 README、AGENTS/CONTEXT 最终同步、inventory、引用扫描、归档和清理。

## 调研

- PRD §2.2 的硬证据：source-index 88 对 snapshot/batch 89；31 个失败或 needs-review 来源未严格隔离；90 个 written 报告 quality 为空；duplicates、claim-history 重复；S6 在 writeback 后；读者包混入审计现场。
- 当前代码核实：`pipeline.py` 先写回再做 provenance/claim-history/source-index；`navigation.py` 无条件生成 pending；`draft.py` 的 provider failure 仍可能走 Claim fallback；现有 acceptance 未覆盖 manifest 闭环、包 allowlist、状态分层和写前 S6。
- 这些事实只用于说明 Task 0 的必要性；不把历史 Task2 产物当作本任务的改动对象。

## 审查处置

- 方向审查使用冻结材料，实际来源为 `kimi/k3`、`cursor/grok`、`antigravity/flash`，3/3 完成。
- 正式 verdict：`revise_required`。
- 已消费的有效问题：Task 0 需要明确核心诚实边界；幂等必须区分业务结果与可追加运行历史。
- 处理方式：用户确认保留 PRD Task 0 完整范围；本记录把“发布诚实”设为核心，把账本、分包、状态和导航写成配套验收；用户确认业务结果幂等、运行记录可追加但不得重复增长业务归档。
- 未采纳的审查意见：要求把 Reader/Audit 分包整体延期。理由是这会违反当前 PRD Task 0 退出物和用户要求的最终产物结构简单、干净；改为在同一 Task 0 内明确边界和 allowlist。
- 审查包中关于 objective facts 缺少代码锚点的问题由本阶段事实核实修复；审查结果本身不改写。
- 细节审查已按完整材料再次调用；此前两次是材料锚点校验错误，已分别修正 `context_map` 的 disposition 和 ADR 行号。修正后实际调用 4 个提供方全部超时，结果为 `unavailable`，没有有效审查结论；这被记录为质量事实，不能当成通过。对应报告为 `quality/reviews/reports/89ecbb99-754f-4e32-9b2a-014ef44e0fe9.md`，attempt 为 `quality/reviews/attempts/89ecbb99-754f-4e32-9b2a-014ef44e0fe9/attempt.json`。

## grill

- CONTEXT：`changed`。补充 Reader Package、Audit/Archive Package、页级/交付级状态、业务结果幂等和 `indexes/sources.md` 唯一来源入口定义；实际文件为 `CONTEXT.md`。
- ADR：`not needed`。已有 `docs/adr/0004-reader-publication-separate-from-audit.md` 已记录读者发布与审计数据分离；本任务是把现有方向具体化，不新增重复 ADR。
- ADR 三项判断：难以反转=true；无背景会意外=true；存在真实取舍=true。已有 ADR 已覆盖该架构取舍，因此不新增文件。
- 术语冲突：旧 `CONTEXT.md` 使用 `_digest/source-index.md` 作为来源索引和阅读外部审计数据描述；处理为新运行固定 `indexes/sources.md`，`_digest` 只属于 Audit/Archive，历史结果不迁移。
- 外部接口真实定义：已核实 `digest` CLI、`kb.structure.md`、现有 pipeline/writeback/navigation/provenance 模块和 acceptance 测试入口。
- 字段和路径唯一来源：本记录与更新后的 `CONTEXT.md`；实现不得再维护第二份来源索引事实。
- 失败语义：已明确 manifest 不闭合写前失败；来源级失败为 `degraded`；交付级为 `not_released`；旧正式页不覆盖。
- 范围边界：已写死 Task 0 完整范围、非目标和延期交接，不把历史迁移、正文编译、全量发布或仓库清理混入本任务。

## 风险

- 细节审查当前是 `unavailable`，原因是正式评审提供方超时；这不是通过结论，已保留报告和 attempt 引用，后续不得把它改写成 pass。
- 新运行取消 `_digest/source-index.md` 可能触及旧测试和调用方；处理方式是实现阶段逐项迁移，新运行只生成 `indexes/sources.md`，历史结果不迁移。
- 题集文件、hash 算法、状态字段和预算数值还未实现冻结；业务要求已冻结，具体参数进入实现 manifest，不能借此扩大范围。

## 未决项

- `indexes/sources.md` 的具体 Markdown 字段和 Reader/Audit allowlist 需要在后续实现材料中落成，但不能改变本记录的单一事实源和分包方向。
- 运行预算、题集 manifest 文件和 hash、状态 manifest 的具体字段需要在实现前冻结；这里是实现参数落盘，不是待补充的产品需求；预算超限不得改写为成功。
- provider/model/endpoint、fallback、timeout/replay/call/wall-clock 的具体数值需要进入任务 manifest；当前业务约束已经冻结为 PRD allowlist、零调用离线基线和透明 fallback。
- 当前旧代码中的 `_digest/source-index.md` 测试和调用方需要在实现阶段逐项迁移；不得直接删除历史产物或无引用扫描删除代码。

## 拒绝方案

- 不把 Reader/Audit 分包延期到另一个 WorkflowHub 任务；这会漏掉 PRD Task 0 的退出物，也不符合用户要求的干净产物结构。
- 不继续生成第二份独立 `_digest/source-index.md`；兼容投影只有在同一 manifest 原子生成时才可另行确认，本任务的新输出固定 `indexes/sources.md`。
- 不把部分来源失败升级为整库回滚，也不把失败内容写进 formal 导航。
- 不以 `written`、页数、Claim 数、测试绿灯或 provider transport 成功代替发布状态。

## 最终确认

- 用户已明确接受本决策：保留 PRD Task 0 完整范围；新运行 only；Reader/Audit 分包；`indexes/sources.md`；来源级 `degraded`；交付级 `not_released`；业务结果幂等、运行记录可追加。
- 本确认只收口 `make-decision`，不授权跳到 `build-spec`、实现、提交、合并、推送或清理。

## Supersedes

- 本记录不替换 PRD、原始设计或既有 ADR；它只把 PRD Task 0 的方向和用户选择冻结为本 WorkflowHub 任务的决策输入。
- 未发现需要 supersede 的既有 Task 0 决策记录；已有 ADR 0004 继续有效。

## 文档结果

- 已更新候选工作树中的 `CONTEXT.md`，补充 Reader/Audit Package、状态、业务幂等和 `indexes/sources.md` 规则。
- 已创建候选工作树中的 `decision-log.md`；未新增重复 ADR、spec、plan 或清理文件。
- 正式实现阶段必须同步 acceptance 测试和受影响模块；根 README、AGENTS/CONTEXT 最终一致性和仓库清理交给 Task 3-Closeout。

## Exit checks

- PRD Task 0 覆盖审计已逐条核对方案、交付物、验收标准、非目标和实现前技术选择；结论为无产品需求漏项。
- 方向审查意见已处置；细节审查 unavailable 已显式记录，未冒充通过。
- 真实代码路径、失败边界、唯一事实源、状态合同、包 allowlist、幂等和延期交接均有材料落点。
- 当前仍停留在 `make-decision`；不创建 `spec.md`、`plan.md` 或 `tasks.md`。

## 推翻条件

- 发现 `indexes/sources.md` 无法承载现有读者入口且没有更小的单一事实源方案。
- 发现业务结果去重会破坏合法的来源版本历史，且无法用运行记录和版本字段分开表达。
- 发现 Task 0 全范围无法在单写者、文件型、无数据库约束下完成；此时必须回到用户重新确认，不得自行缩小范围。

## PRD Task 0 覆盖审计

本次逐条核对 PRD §5.3、§6.1–§6.2、§6.6、§7 Task 0 的 8 条方案、交付物、非目标和 9 条验收标准，以及 §11 的实现前技术选择。结论如下：

- 来源闭环：已覆盖 `input_manifest → source snapshots → audit ledger`、来源集合闭合、缺失显式失败；唯一事实源按 PRD 使用 Audit manifest（实现路径冻结为 `_digest/source-manifest.json`），`indexes/sources.md` 只是 Reader 投影。
- 写前门禁：已覆盖 S6 provenance、Claim、路径、页级状态、交付包事实全部在写回前检查；写前失败不得产生新的 formal 页面。
- 状态诚实：已覆盖 provider transport、Claim verification、writeback、`machine_pass`、`agent_assisted`、`human_reviewed` 独立记录；`written` 不等于 `published`/`released`；Task 0 固定 `not_released`。
- 失败隔离：已覆盖 provider 失败、JSON 损坏、无正文、无产品归属、冲突和人工修改冲突进入 `degraded`/Audit，不进入正式导航；无关页面不整库回滚；旧 formal 不被失败运行覆盖。
- 包和导航：已覆盖 Reader/Audit allowlist、Reader 排除 `_digest`/`_archive`/provider 日志/运行比较报告、真实 pending、空分类、断链和不可点击来源入口失败；新运行只用 `indexes/sources.md`，历史 `_digest/source-index.md` 不迁移。
- 幂等和审计：已覆盖 source/claim/duplicate/history 业务关系幂等、归档内容不重复增长、运行记录可追加，以及异常增长在 audit report 定位。
- 读者题集与离线：已覆盖 17+3 manifest 的字段、派生样本规则、seed、评审人和 hash；`--no-llm + Jaccard` 零 LLM/embedding 网络调用；完整读者门延期到 Task 3。
- Provider 和预算：已覆盖 `qwen3.6`/`jina-embeddings` allowlist、透明 Jaccard fallback、语义要求下 `not_released`、timeout/replay/call/wall-clock 预算超限失败语义。
- 范围和交接：已覆盖 Task 0 不做 ProductGazetteer、TopicIndex、正文编译、全量重发布、数据库/图谱/向量库/调度器/AgentMemory、永久人工队列和仓库清理；Task 1、Task 2、Task 3、Task 3-Closeout 的交接已列明。

覆盖结论：没有发现需要新增产品决策的 PRD 漏项。尚未落地的是实现阶段才冻结的具体字段、hash 计算和预算数值；它们属于已冻结方向的实现参数，不得被 `build-spec` 用来补产品需求。
