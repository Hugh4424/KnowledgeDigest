# Task 2-C Decision Log — 信任信号与读者质量门（小语料）

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 处理状态 |
| --- | --- | --- | --- |
| R-001 | 按标准 WorkflowHub 从 `make-decision` 开始，不跳阶段，不让 `build-spec` 补产品决策。 | 用户原话："请按标准 WorkflowHub 从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。" | current |
| R-002 | Talk 用大白话说明选项、后果和风险；decision-log 记录原始需求、关键事实、选择、理由和延期交接。 | 用户原话："Talk 请用大白话说明选项、后果和风险；decision-log 记录原始需求、关键事实、选择、理由和延期交接。" | current |
| R-003 | 先冻结完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。 | 用户原话；PRD §Task 2-C | current |
| R-004 | Task 2-C 在小语料上接入信任/新鲜度/生命周期信号，并建立读者质量门；不能把静态字段、lint 或 provider 成功当成读者质量通过。 | PRD §6.9、§Task 2-C | current |
| R-005 | 依赖 Task 0 题集/状态合同、Task 1 TopicIndex、Task 2-A Reader Bundle 和 Task 2-B 可读页面；不做 89 条全量。 | PRD §Task 2-C「依赖和不做什么」；Task 2-B T013/T014 与提交 `2369a85` | current — Task 2-B 已闭合，Task 2-C 只消费其出口 |

> **历史记录边界**：从下方“关键事实”到“Exit checks”的旧内容，是 Task 2-B 尚未闭合时的真实阻塞草稿，现已由“当前 make-decision 续谈记录”明确 supersede。保留它是为了追溯当时为什么暂停；当前工作不得再把其中的 `unknown/incomplete`、独立人工门或“Grill 待执行”当成现状。

## 关键事实

- PRD 的 Task 2-C 目标是小语料门，不是全量发布；整包仍只能是 `not_released`，Task 3 才能做全量 `released` 判定。
- OKF 信号只告诉读者“这份内容从哪里来、何时生成、有没有验证、可能是否过期”；它不等于正文真的能回答问题。
- Reader Package 与 Audit/Archive Package 分开；信号必须从同一 audit records/frontmatter 确定性投影，不能再造一份 trust 事实源。
- 页级状态只有 `published`/`degraded`；交付级状态只有 `released`/`not_released`。`machine_pass`、`agent_assisted`、`human_reviewed` 分开记录。
- `verified` 没有真实人工事件时不能显示 `human-reviewed`；结构 lint 不能单独产生 `machine-confirmed`。
- `stale_after` 只能按明确证据生成；过期只提示复核，不自动删页、不自动改成 `deprecated`，也不改变 `released` 判定。
- Task 2-C 的正向样本至少 8 题，覆盖至少 2 个产品/模块和 2 类页面；3 个负向题必须 0 次误命中；不足 8 题或评审人不独立时保持 `not_released`。
- 当前仓库的 Task 2-B 归档材料记录：代码/确定性测试已完成，但真实语义出口、独立审查、`exceptions` 和用户确认仍为 `unknown/incomplete/missing`；这与 PRD“任一任务未达到退出物，不得进入下一任务”存在直接冲突，不能静默当成已完成。

## 流程与边界

### 用户流程

1. 维护者启动 Task 2-C 小语料运行，读取 Task 0 冻结题集、Task 1 TopicIndex、Task 2-A Reader Bundle 和 Task 2-B 正文样本/运行证据。
2. 系统从同一 audit records/frontmatter 投影页面和索引信号：concept type、description、来源数、`generated.at`、derived trust tier、`status`、`stale_after`/stale 提示。
3. 系统用统一规则归一 `verified` 的 mapping/list；缺失验证显示 `unverified`；结构检查和真实内容机器回查分开。
4. 系统按绝对日期判断 stale；stale 只显示复核提示，`deprecated` 保留旧链接但默认入口隐藏。
5. 系统从 Task 0 题集按冻结规则派生至少 8 个正向可答样本，并覆盖规定的产品/模块、页面类型和特殊语料类别；不足则直接 `not_released`。
6. 机器门记录首次命中、跳转、答案完整性、边界/版本准确性、来源归因和失败原因；agent 辅助单独记录。
7. 独立人工评审逐题记录 reviewer、角色、独立性、日期、评分表 hash、答案结果和失败原因；不把 agent 辅助冒充人工。
8. 通过条件是正向题全部命中且 3 个负向题零误命中；任一失败、来源回查断裂、评审人不独立、样本不足或上游依赖未闭合，都保留失败/降级证据，不覆盖旧 formal Reader Package。
9. Task 2-C 退出时冻结 Concept Contract v1、信号投影、题集派生规则、评分表、seed、阈值和发布门；Task 3 只能复用，不能临时改门。

### 页面与入口范围

- Reader 根入口：`Home.md` 只指向唯一 canonical `index.md`；不能维护第二套目录事实。
- Reader 页面/索引：产品与模块索引、三类已由 Task 2-B 冻结的 concept page；Task 2-C 只补信号投影和质量证据，不新增 page type。
- Reader 页头/索引信号：type、description、来源数、`generated.at`、derived trust tier、`status`、stale/deprecated 提示。
- Audit/Archive：逐题评分、机器/agent/human 状态、失败样本、来源回查、manifest、失败原因和恢复路径；失败页不进入 Reader 导航。
- 不把 `topic-index.json`、provider 原始响应、审计现场或包级 release 状态当成读者页面。

### 数据状态

- 页级：`published` / `degraded`。
- 交付级：Task 2-C 只能是 `not_released`；`released` 延期到 Task 3。
- 信任层级：`unverified`、机器内容验证产生的 machine-confirmed、真实人工事件产生的 human-reviewed；不生成 `trust_score`。
- 生命周期：`status=deprecated` 保留旧路径，默认新入口隐藏；stale 是复核提示，不是自动降级。
- 证据层：`machine_pass`、`agent_assisted`、`human_reviewed` 独立记录。
- 题目层：正向题命中/未命中、负向题误命中/未命中、答案完整性、边界/版本准确性、来源归因、失败原因。
- 评审人层：reviewer identifier、角色、与实现者关系、独立性标记、日期、评分表 hash、冲突说明。

### 成功边界

- 不打开正文即可从根/产品/模块索引读到全部要求的信号，且信号可从单一事实源重算。
- `verified` mapping/list、缺失验证、机器验证和人工验证的 derived tier 结果稳定一致。
- stale/deprecated 规则按绝对日期重放；不删页、不伪造稳定或发布状态。
- 正向可答样本不少于 8 题，覆盖规则满足；正向题 100% 命中，3 个负向题 0 误命中。
- 每题有完整人工记录，且评审独立；评审人 `non_independent` 或样本不足时不算成功。
- 关键正文事实仍能从 `sources[].id` 回查到 `digest_claims[].claim_id`、`fragment_locator` 和 Evidence。
- Task 2-C exit manifest 冻结并记录 Concept Contract v1、信号字段、题集派生、评分表、seed、阈值、provider/config、预算和 commit；交付仍为 `not_released`。

### 失败边界

- 必需信号缺失、来源投影出现第二事实源、`verified` 归一不一致、stale 日期无证据或 deprecated 误入默认入口：该页/样本失败，保留 Audit 证据。
- 正向题不足 8 个、覆盖不足、任一正向题未命中、任一负向题误命中：Task 2-C 不通过，交付 `not_released`。
- 没有真实人工事件不能写 `human-reviewed`；只有 agent 或机器证据不能替代人工门。
- 评审人不独立、评分表/seed/阈值不可回放、来源回查失败、Task 2-B 依赖未闭合：不宣称读者质量通过，不覆盖旧 formal。
- provider 失败、fallback、结构 lint 通过或测试绿灯都不能改写为读者质量通过。

## 范围

- 当前范围：小语料信号投影、trust/freshness/lifecycle validator、题集派生、机器/agent/human 三类状态、逐题人工 scorecard、失败样本和 Task 2-C exit manifest。
- 当前阶段只做 make-decision；在用户确认前不写 `spec.md`、`plan.md`、`tasks.md`，不实现代码。

## 非目标

- 不做 89 条全量正文编译、全量导航、正式 `released` 或 Task 3 对比报告。
- 不新增 page type，不改变 TopicIndex 身份、页面类型、Evidence/Provenance 权威或 Task 2-A Reader Bundle 合同。
- 不引入 OKF reference agent/viewer、Attested Computation、trust score、数据库、图谱、向量库、调度器或永久人工队列。
- 不把人工门变成长驻人工工作流；本阶段只是一次性小语料读者验收证据。
- 不用静态 frontmatter、Claim 数、页数、lint、provider 成功、写入成功或 agent 输出替代读者质量。

## 延期交接

| deferred_id | 内容 | 交接阶段 | 完成条件 |
| --- | --- | --- | --- |
| DEFER-001 | 具体字段序列化、模板和 validator 实现合同 | build-spec/build-plan | 只展开当前决定，不改变范围和门 |
| DEFER-002 | 小语料真实运行、机器回查和失败样本 | build-code | 使用冻结题集/样本和可回放 manifest |
| DEFER-003 | 独立人工逐题评分和 `human-reviewed` 事件 | build-code/verify-code | 评审人与实现者关系、日期、hash、冲突齐全 |
| DEFER-004 | 89 条全量、17+3 完整题集、Reader Package 发布 | Task 3 | 复用 Task 2-C 冻结门，不临时改门 |
| DEFER-005 | README/AGENTS/CONTEXT 同步、清理、归档 | Task 3-Closeout | 实现和最终输出稳定后执行 |

## Talk

### Round 1：Task 2-B 与 Task 2-C 的先后关系

决策卡只问一个问题：Task 2-B 的正式出口尚未闭合时，Task 2-C 是否继续推进？

### Round 1 当前决策卡

现状：PRD 明确 Task 2-C 是 Task 2-B 后的下一项，但仓库最新 Task 2-B 证据只证明代码/确定性测试完成，真实语义出口仍 `incomplete/not_released`，因此正式依赖还没闭合。

问题：现在怎么处理这个依赖？

- **A（推荐）先闭合 Task 2-B，再开始 Task 2-C**：最符合 PRD 任务依赖；代价是 Task 2-C 暂不推进，风险是要继续补 Task 2-B 的真实语义/质量证据。
- B 先做 Task 2-C 的 `make-decision`，但明确标记“依赖未闭合”：可以先把产品方向谈清楚；代价是不能进入 `build-spec`/实现，若 Task 2-B 合同变化可能重谈，风险是形成悬空决策。
- C 把“代码已完成”当作 Task 2-B 已完成，直接进入 Task 2-C：最快；风险是违反 PRD §9，把未闭合依赖伪装成正式交接。

用户原文回复：`A`

用户选择 A 后，本轮方向结论为：先闭合 Task 2-B，再重新开始 Task 2-C。Task 2-C 本轮不进入 Talk Round 2/3，不进入 `build-spec`，不进入实现；这不是 Task 2-C 的最终产品方向确认，而是当前任务的延期交接决定。

### Round 1 结果与延期交接

- 选择：A。
- 理由：Task 2-C 依赖 Task 2-B 的正式出口；当前证据显示 Task 2-B 仍为 `incomplete` / `not_released`，最新代码修复后没有新的真实语义运行，正式 verify 也未闭合。
- 交接给 Task 2-B：补做真实语义运行；证明至少 6 个机器通过概念、覆盖 3 种页面类型，并完成独立核验与正式出口记录。具体以 Task 2-B 原始任务记录为准，不在 Task 2-C 里补需求。
- Task 2-C 保留：完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项已经记录；待 Task 2-B 正式闭合后，从 `make-decision` 重新进入 Task 2-C 的 Talk。
- 本阶段状态：`deferred_pending_user_confirmation`。已记录用户的真实选择，但没有伪造 Task 2-C 的最终确认，也没有生成 `build-spec`。

## 调研

当前已核对：PRD、Task 2-B 归档材料、Task 0/Task 1/Task 2-A 证据入口、当前 Git 基线和 WorkflowHub 工作树。外部调研暂跳过：本轮问题是本地任务依赖和已冻结合同，不需要外部事实改变方向；若用户选择先修 Task 2-B，后续再核实真实 provider/样本输入。

## Grill

待 Talk Round 3 后执行；不能提前写成完成。

## 审查处置

待方向审查、Talk Round 3、Grill 和 detail 审查后填写；不可把审查不可用写成通过。

## 最终确认

延期中；A 是“先闭合 Task 2-B”的真实选择，不是 Task 2-C 最终产品方向确认。因此不生成 content-addressed interaction aggregate，不结束 Task 2-C 的 `make-decision`，也不进入后续阶段。

## 未决项

| item_id | 内容 | 原因 | 解决阶段 |
| --- | --- | --- | --- |
| OPEN-001 | Task 2-B 是否满足进入 Task 2-C 的正式退出条件 | 用户已选择先闭合 Task 2-B；当前仍有语义出口和质量事实缺口 | Task 2-B，闭合后重新进入 Task 2-C |
| OPEN-002 | 若可进入，Task 2-C 的最小小语料边界是否严格按 PRD 冻结 | 不得由 build-spec 补产品需求 | Task 2-B 闭合后重新进入 Talk |
| OPEN-003 | 具体字段、manifest 和 scorecard 序列化 | 属于后续规格/实现合同 | build-spec/build-plan |

## 风险与延期交接

| risk/deferred_id | 风险/延期 | 后果 | 处理阶段 |
| --- | --- | --- | --- |
| RISK-001 | 把 Task 2-B 的代码完成误当正式退出完成 | Task 2-C 在缺正文/语义依赖上建门，结果不可解释 | 已由 A 决定先交接回 Task 2-B |
| RISK-002 | 用静态信号或 agent 输出冒充读者质量 | 读者仍可能找不到答案，正式发布判断失真 | Task 2-C machine/human gate |
| RISK-003 | 题集不足或评审不独立 | 即使样本看似通过，也不能形成正式读者证据 | Task 2-C 保持 `not_released` |
| DEFER-004 | 全量发布和完整题集 | 未完成前不进入 Task 3 | Task 3 |

## Supersedes

none；本日志不改写归档的 Task 2-B 决策，只记录本 Task 2-C 的当前判断和用户确认。

## 文档结果

- 当前 Task 2-C 尚未改变根 `CONTEXT.md`；术语沿用 `published/degraded/not_released`、Reader/Audit、TopicIndex 和信号边界。
- ADR 尚未创建；是否需要新 ADR 留到 Grill，只有满足难以反转、无背景会意外、存在真实取舍三项才创建。

## Exit checks

- 外部接口真实定义：当前 make-decision 讨论不依赖新的外部接口；Task 2-C 实现阶段仍需核实 provider/config 的真实调用。
- 字段/路径唯一权威：PRD、Task 2-A/Task 2-B 合同和现有 `CONTEXT.md` 是当前来源；具体新字段尚未在本阶段发明。
- 失败语义：已按 `published/degraded`、`released/not_released`、机器/agent/人工分离列出；依赖未闭合仍是开放项。
- 范围边界：小语料、一次性读者门、非全量、非永久人工系统已写死；Task 2-B 依赖由用户选择先闭合，Task 2-C 边界留待重新进入 Talk 时确认。

## 当前 make-decision 续谈记录（2026-08-12）

本节是当前 Task 2-C 的 of-record，覆盖上方早先“Task 2-B 尚未闭合、延期等待”的历史草稿。Task 2-B 已于提交 `2369a85` 完成机器出口、回归证据、提交、合并、推送和 worktree 清理；因此 Task 2-C 已重新进入 `make-decision`，不再沿用早先的延期结论。

### D-001
- question/final_option: Task 2-C 的核心读者验收范围怎么定？选择 A：小语料人工读者门，至少 8 个可回答正向题全部命中，3 个负向题 0 误命中，同时验证信任信号。
- recommendation/plain_language: 推荐。先证明一小批真实问题能答对，再决定是否值得扩大；不把 89 条全量质量提前带进来。
- decision: 当前 Task 2-C 只验收冻结小语料和信任信号，不提前做完整 17+3 题或 89 条全量。
- source_type/reference/exact_excerpt: user_reply / 本轮 Talk Round 1 / `A`
- approval_binding: 已获当前回合用户选择；最终整包确认待 Talk Round 3、Grill、审查和最终决策卡之后绑定。
- facts_and_constraints: PRD 要求正向样本至少 8 题、正向 100% 命中、3 个负向题 0 误命中；Task 2-C 通过后才进入 Task 3 全量发布。
- Logic: PRD 小语料门 -> 控制验收成本并保留读者证据 -> 选择 A -> Task 3 复用冻结门做全量验收。
- choice_reason/impact: 选择可解释、可回放的最小质量门；影响题集、样本、信任投影和 exit manifest，不改变 TopicIndex、页面类型或 Evidence/Provenance 权威。
- consequences_and_risks: 范围可控但不能代表全量质量；如果样本覆盖不足，结果必须保持 `not_released`，不能把小样本通过解释成全量通过。
- rejected_alternatives: B 只验信任字段，不能证明读者找得到答案；C 直接做完整 17+3，会提前扩大 Task 3 范围和成本。
- unresolved_items/owner: 具体题目、样本、scorecard 字段和回放格式交给后续 `build-spec`/`build-code`，不得改变本决定。
- Supersedes: 早先仅等待 Task 2-B 闭合的延期草稿；不改写其历史事实。

### D-002
- question/final_option: 没有独立人工评审时，Agent 评分能否替代人工门？选择 C，并确认修改原始门槛：Agent 评分可以替代独立人工评审并允许通过。
- recommendation/plain_language: 原 PRD 不推荐此选项；用户明确确认修改原始门槛，因此当前 Task 2-C 采用该范围修订。大白话：模型自己按固定题目和评分表检查，满足门槛就算读者质量证据，但这会增加“模型自证”的风险。
- decision: Task 2-C 允许 Agent 评分作为读者质量评审主体；不再把“必须独立人工评审”作为本 Task 2-C 的通过前置条件。Agent 证据仍必须独立记录，不得伪造 `human_reviewed`。
- source_type/reference/exact_excerpt: user_reply / 本轮 Talk Round 1 / `C`；随后用户确认：`确认修改原始门槛`
- approval_binding: 已获当前回合用户明确确认；最终整包确认待最终决策卡绑定。
- facts_and_constraints: PRD 原文要求独立人工评审，且 Agent/机器/人工分别记录；本决定只修改评审主体门槛，保留题集阈值、来源回查、信号事实源、失败隔离和 Task 3 全量边界。
- Logic: 原 PRD 独立人工门与用户当前取舍冲突 -> 用户明确承担“模型自证”风险并确认改门 -> 仅在 Task 2-C 小语料内允许 Agent 评审 -> 用独立 Agent 记录和可回放证据限制影响面。
- choice_reason/impact: 用户选择更快、更可执行的小语料质量验证；影响评审身份、结果字段和失败语义，不扩大到 Task 3 或永久人工队列。
- consequences_and_risks: 少了人工独立性，可能漏掉模型不擅长发现的错误；若 Agent 题目、提示、模型或证据不可回放，结果不得宣称通过；后续 Task 3 是否采用该门必须重新确认或明确继承。
- rejected_alternatives: A 保留独立人工门，与用户确认的范围修订不符；未选择将 Agent 只作为辅助，因为用户确认其可替代人工。
- unresolved_items/owner: Agent 评审身份、模型/提示/seed/hash、输出结构、冲突和失败样本由 `build-spec`/`build-code` 固化；Task 3 是否继承由 Task 3 决策确认。
- 追加约束：逐题记录和 exit manifest 必须显式包含 `agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`；任一缺失或与实际评审主体不一致，该题失败，且不能形成 Task 2-C 读者门通过证据。
- Supersedes: 当前日志中“评审人不独立则 Task 2-C 不通过”的原始门槛，仅限 Task 2-C；原始要求保留作历史事实。

### D-003
- question/final_option: Task 2-C 的 Agent 质量门通过后，是否可以直接把整包标为 `released`？选择：仍保持 `not_released`，由 Task 3 才做全量发布判定。
- recommendation/plain_language: 推荐。Task 2-C 只证明小语料质量，不能冒充全量发布。
- decision: 即使 Agent 评分达到阈值，Task 2-C 只生成小语料质量门通过证据；交付级状态仍为 `not_released`，不得覆盖正式 Reader Package。
- source_type/reference/exact_excerpt: user_reply / 本轮 Talk Round 2 / `确认`
- approval_binding: 已获当前回合用户确认；最终整包确认待最终决策卡绑定。
- facts_and_constraints: PRD 将 Task 2-C 定义为进入 Task 3 的小语料门；`released` 属于全量发布结果，页级状态和交付级状态分开。
- Logic: 小语料证据不等于全量证据 -> 保持交付级 `not_released` -> Task 3 复用冻结门并完成全量验收 -> 才能判断正式发布。
- choice_reason/impact: 防止局部通过污染正式发布状态；影响 exit manifest 和下游交接，不改变当前页级 `published/degraded` 合同。
- consequences_and_risks: Task 2-C 通过后仍不能直接对外宣称正式发布；Task 3 必须重新产生全量证据，代价是多一个阶段，但状态真实。
- rejected_alternatives: Agent 通过即 `released` 会把小样本结果误当全量结果；只改页级状态会混淆页级和交付级责任。
- unresolved_items/owner: Task 3 的全量题集和发布判定留到 Task 3；本阶段不提前实现。
- Supersedes: none。

### 当前 Talk 状态

- Round 1：方向已收敛为小语料读者门；原始人工独立性门已由用户明确改为 Agent 可替代，仅限 Task 2-C。
- Round 2：范围修订限定在 Task 2-C；即使通过，交付级仍为 `not_released`。
- Round 3：用户确认按方向审查意见补全原始需求、客观事实、非目标和 Task 2-B 证据锚点，保持当前方向不变。
- 调研：外部调研跳过。当前方向由 PRD 冻结事实、Task 2-B 真实交付证据和用户明确取舍决定；外部资料不会改变本轮边界。该跳过不是研究通过。
- 方向审查：已完成；`opencode/v4flash` 有效返回意见，`codex/luna` 因同源限制未形成独立意见；结果为可用建议，不是通过判定。
- Grill：已完成；`CONTEXT.md` 已更新，ADR `0007-task2c-agent-reader-gate.md` 已创建为 proposed。
- detail 审查：已完成一次初审和一次针对性复核；针对性复核可用，但仍保留一个“Task 2-B 证据在当前审查包外”的 accepted risk，详见审查处置。

### D-004
- question/final_option: Agent 做读者测试时看哪些内容？选择 A：只看 Reader Package，Audit/Archive 只做事后溯源核对。
- recommendation/plain_language: 推荐。让 Agent 像真实读者一样从 Home、索引和正文找答案，不能用隐藏资料补答案。
- decision: Task 2-C Agent 评分输入只包含 Reader Package；Audit/Archive 不参与答案命中评分，只用于验证来源链和保存失败证据。
- source_type/reference/exact_excerpt: user_reply / Grill / `A`
- approval_binding: 已获当前回合用户选择；最终整包确认待最终决策卡绑定。
- facts_and_constraints: Reader Package 是默认阅读入口；Audit/Archive 不是读者入口；读者门要验证“读者能否从页面完成问题”，不能验证“审计包里是否存在答案”。
- Logic: 真实阅读路径 -> 禁止隐藏资料补答案 -> 选择 A -> 读者命中结果更能代表实际使用。
- choice_reason/impact: 保持读者验收真实性；影响 Agent 输入边界和证据分层，不改变 Audit 的溯源职责。
- consequences_and_risks: 页面缺答案会真实失败，失败样本会增加；但不会把读者看不到的审计资料误算成通过。
- rejected_alternatives: B 会让隐藏资料替页面补答案；C 完全不能验证读者使用页面。
- unresolved_items/owner: Reader Package 的具体文件白名单由 `build-spec` 固化；Audit/Archive 的回查格式由 `build-code` 固化。
- Supersedes: none。

### D-005
- question/final_option: Agent 能答对但找不到来源时是否通过？选择 A：不通过，答案和来源都必须完整。
- recommendation/plain_language: 推荐。看似答对但无法核查的内容不能作为质量门通过。
- decision: 每道正向题必须同时满足答案命中、边界/版本准确、来源链可回查；来源断裂即失败，交付保持 `not_released`。
- source_type/reference/exact_excerpt: user_reply / Grill / `A`
- approval_binding: 已获当前回合用户选择；最终整包确认待最终决策卡绑定。
- facts_and_constraints: PRD 要求正文事实继续经过 source id -> claim id/locator -> Evidence；Reader/Audit 分包不能切断这条链。
- Logic: 无来源的答案不可核查 -> 不允许质量门通过 -> 选择 A -> 保留失败证据且不污染正式包。
- choice_reason/impact: 牺牲部分样本通过率换取可审计性；影响逐题 scorecard、失败样本和出口状态。
- consequences_and_risks: 需要更多失败处理和回查工作；否则会发布“可能正确但无法证明”的答案。
- rejected_alternatives: B 会把来源问题拖到以后；C 会把失败内容带入正式入口。
- unresolved_items/owner: 逐题回查字段和失败分类由 `build-spec`/`build-code` 固化。
- Supersedes: none。

## Grill 结果（当前回合）

- CONTEXT.md：changed。新增 Task 2-C Agent 读者门术语，明确 `agent_assisted`、`review_mode=agent_only`、`gate_actor=agent`，并明确不产生 `human_reviewed`、`verified`、trust tier 或 `released`。
- ADR：created，`docs/adr/0007-task2c-agent-reader-gate.md`，状态为 proposed，等待最终 make-decision 确认。
- ADR criteria：hard to reverse = yes（会影响读者门和结果字段）；surprising without context = yes（现有 PRD 原本要求独立人工）；genuine trade-off = yes（速度/可执行性换取模型自证风险）。
- 代码事实：`reader_bundle.py` 不允许 Agent actor 冒充 `human:` 或生成 `verified`；`pipeline.py` 已把 `machine_pass`、`agent_assisted`、`human_reviewed` 分开记录；因此 Agent 读者门必须是单独的评分/状态，不得改写 trust tier。
- 失败语义：Reader Package 找不到答案、来源链断裂、样本不足、正向题失败或负向题误命中，均不能形成 Task 2-C 通过证据；交付级仍为 `not_released`。
- 范围边界：只限 Task 2-C 小语料；不外推 Task 3、89 条全量、永久队列或正式发布。

## 审查处置（当前回合补记）

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| F-c877a7facb19 | direction review 指出 raw requirement 过短，未展开信号、读者门、小语料和出口 | 审查无法判断方向是否完整 | fixed | 已在本日志 D-001～D-005、流程/边界和本回合材料中补齐；保留原 review result `quality/reviews/results/make-decision-direction-d6a0b65ddeae1b78e937957b7ec66c80e17573f4-3e343bbe-c0b4-4cc3-9860-8bbb90e5a5f8.json` | main agent / 后续 detail review / retain |
| F-7b3263a57df1 | direction review 指出“Task 2-C not full corpus”边界表达含糊 | 全量非目标和小语料范围可能被误读 | fixed | 已由 D-001、D-003 和 Grill 结果明确；保留原 review result | main agent / build-spec / retain |
| F-e4d7cd606423 | direction review 指出 Task 2-B closed 缺少可查证锚点 | Task 2-C 依赖无法验证 | fixed | 已绑定 Task 2-B commit `2369a85`、T013/T014 evidence 和交接事实；保留原 review result | main agent / build-spec / retain |
| F-39507afeb522 | direction review 指出 facts、hard constraints、non-goals 未分栏 | 审查材料边界不清 | fixed | 已在当前 decision-log 分开记录；保留原 review result | main agent / detail review / retain |

### D-006
- question/final_option: 哪些情况才把页面标为 `degraded`？采用 PRD/现有状态合同的严格映射。
- recommendation/plain_language: 推荐。普通的“还没验证”“可能过期”“已废弃”只是信号，不要误报成页面坏了；只有事实源、来源回查或机器门真的失败才降级。
- decision: `unverified`、stale、`status=deprecated` 本身不触发 `degraded`；必需信号投影不一致、来源回查断裂、机器门失败、正文/人工修改冲突等明确失败才是 `degraded`，并排除出正式 Reader 导航。页面可为 `published`，但 Task 2-C 交付仍为 `not_released`。
- source_type/reference/exact_excerpt: code_and_PRD / `CONTEXT.md` 页级发布状态、PRD §6.9 与 Task 2-C 验收 / `stale 只显示复核提示，不自动删页、不自动降级；deprecated 保留旧路径但默认入口隐藏`
- approval_binding: 由现有代码/PRD事实固定；最终整包确认待最终决策卡绑定。
- facts_and_constraints: 现有 `CONTEXT.md` 定义页级 `published/degraded`；PRD 明确 stale 不自动降级、deprecated 不删除、信号必须从同一事实源投影。
- Logic: 信号提示不等于页面坏 -> 仅明确失败触发 degraded -> 保留 published/degraded 与 released/not_released 分层 -> Reader 不展示失败页。
- choice_reason/impact: 避免把“未验证/过期提示”误报成内容损坏；影响 validator、导航过滤和失败样本。
- consequences_and_risks: 需要实现者准确区分信号异常与质量/溯源失败；若把真实失败留成 published，会污染读者入口。
- rejected_alternatives: 所有 stale/unverified/deprecated 一律 degraded 会误伤可读页面；所有页面都 published 会掩盖真实失败。
- unresolved_items/owner: 具体字段组合和 validator 错误码由 `build-spec` 固化，但不得改变上述映射。
- Supersedes: none。

## detail 审查处置（补修后复核输入）

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| F-5cb7b2002207 | detail review 指出审查材料只带 5 行 D 摘要，没带完整 decision-log/Grill 判断 | 无法复核 Talk/Grill 和决定可追溯性 | fixed | 本次针对性复核输入改为携带完整当前 decision-log 的决策字段、Grill 结果和 ADR/CONTEXT 处置；原结果 `quality/reviews/results/make-decision-detail-73d050ac95455eb84605fbc280c15f90ea4f07c1-8cb2dfa3-e077-4646-8242-63ec11967ab7.json` 保留 | main agent / make-decision completion / retain |
| F-23f1a1e49b7d | detail review 指出 Agent 三个防伪造字段未显式进入逐题合同 | 结果无法逐项验收 | fixed | D-002 已补充三字段及缺失即失败；针对性复核输入显式列出字段 | main agent / build-spec / retain |
| F-6b7d16e1f8ce | detail review 指出 `degraded` 触发条件缺失 | 页级状态边界不清 | fixed | D-006 与 `CONTEXT.md` 已明确映射；针对性复核输入显式列出 | main agent / build-spec / retain |
| F-07ada34d101d | 针对性 detail review 指出“字段缺失即该题失败”没有在方向层明确 | 规格可能偷偷加门 | fixed | D-002 已明确三字段任一缺失即该题失败；复核结果 `quality/reviews/results/make-decision-detail-b21d4013c8a6b212ad44255f14cba783f7225fc6-05565cf2-0345-45d8-ad29-01f31e9b0e32.json` 保留 | main agent / build-spec / retain |
| F-8214d8f2494c | 针对性 detail review 无法从当前 packet 独立验证 Task 2-B `2369a85`、T013/T014 | Task 2-C 依赖证据在本审查包外 | accepted_risk | 用户已确认 Task 2-B 继续交接；保留提交、T013/T014 路径和 hash 作为外部事实，不把它写成本次 detail review 的独立通过；build-spec 消费前继续核对 | 用户确认 / build-spec / retain |
| F-89289a9582ad | detail review 误读日志中的旧“未完成/待执行/未确认”段落 | 阶段状态可能被误判 | fixed | 已增加历史边界说明、Round 3 记录和当前阶段状态；保留复核结果 | main agent / make-decision completion / retain |
| F-a6d59cb6abae | detail review 发现旧流程仍写“人工独立评审” | 与 D-002 Agent-only 决定冲突 | fixed | 旧流程属于历史阻塞草稿；当前 D-002、CONTEXT 和 draft acceptance 以 Agent-only 为准 | main agent / build-spec / retain |
| F-fbc625dc6685 | detail review 发现旧“Grill 待执行”与当前 Grill 结果并存 | 日志自相矛盾 | fixed | 已用历史边界和当前 Grill 状态 supersede 旧文字 | main agent / make-decision completion / retain |

## Talk Round 3 / detail 修正的 correction appendix（decision-correction-appendix.v1）

- original_decision_ref: `specs/task2c-knowledge-publication-trust-reader-quality/decision-log.md` 当前 D-001～D-006；does_not_rewrite_upstream=true。
- D-001 correction: 当前范围是小语料读者门，不是全量；旧延期草稿只保留历史。
- D-002 correction: Task 2-C 允许 Agent-only；`agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent` 缺失即该题失败；不得写 `human_reviewed`。
- D-003 correction: Task 2-C 通过也保持 `not_released`。
- D-004 correction: Agent 只读 Reader Package，Audit/Archive 不能补答案。
- D-005 correction: 答案和来源链都必须通过。
- D-006 correction: `unverified`、stale、deprecated 本身不触发 `degraded`；明确事实/机器/溯源失败才触发。

## 当前最终决策卡

- 目标：在小语料上验证读者从 Reader Package 能否找到答案，同时展示可解释的信任、更新时间和生命周期信号。
- 评审方式：Agent 只读 Reader Package；逐题记录 `agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`；不写 `human_reviewed`，不生成 `verified` 或 trust tier。
- 通过条件：至少 8 个正向题，覆盖至少 2 个产品/模块和 2 类页面；正向题全部命中；3 个负向题 0 误命中；答案、边界/版本和来源链都能回查。
- 页面状态：只有明确信号/事实源/机器门/溯源失败才是 `degraded`；`unverified`、stale、deprecated 本身只是信号，不自动降级。失败页不进 Reader 导航。
- 交付状态：Task 2-C 即使通过也保持 `not_released`；Task 3 才做 89 条全量和 `released` 判定。
- 非目标：89 条全量、完整 17+3、永久人工队列、trust score、OKF runtime、数据库/图谱/向量库、TopicIndex/Evidence/Provenance 改造。
- 主要风险：Agent 自己评估自己，可能漏掉模型不擅长发现的问题；因此必须保存输入、模型、提示、seed、hash、逐题结果和失败样本。
- 审查限制：Task 2-B 已有提交和 T013/T014 证据，但本次 detail 审查包不能跨任务读取它们；这条风险交给 build-spec 前再次核对。
- 状态：accepted。
- 用户原文与 host-visible 绑定：`A`，确认以上决定、接受 Agent 自评风险和 Task 2-B 证据需在下游复核的限制。
- 完成事实：Talk 三轮、方向审查、Grill、detail 审查及审查处置均已记录；interaction aggregate 在当前 TaskHandle 的 `quality/evidence/interactions/` 下单独绑定。

## 下游交接核对（build-spec handoff）

- 原延期交接已完成：Task 2-B commit `2369a853adb4bc70709036c563233cae361222be` 与 origin/main 一致。
- 已核对真实语义出口：T013 run `run-519d5c93591e45faab8e3ef56601a3f1`，12 个 concept machine-passing，delivery `not_released`；T014 为 49 passed、264 passed/2 skipped、518 passed/3 skipped，diff check passed。
- 已核对证据 hash：T013 `c38aad3185bd534ee988766d55fc26ee68d5f8b2688f8e00ddb72d23dbbd17e4`；T014 `c202e04f2a2e208fd2e3b7cb3ad6372e57b38459ab69c9c423180e2cd59a852c`。
- 结论：F-8214d8f2494c 在“detail review 包外不可独立读取”的范围内仍保留为历史 accepted risk；其要求的下游复核已完成，Task 2-C 可以继续 build-plan。若后续基线或证据改变，立即停止实现并重新核对。
