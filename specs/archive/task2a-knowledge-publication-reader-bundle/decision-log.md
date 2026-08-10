# Decision Log — Task 2-A：OKF-compatible Reader Bundle 基础（Concept Contract v1-draft）

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 关联 D/处理状态 |
| --- | --- | --- | --- |
| R-001 | 把 Reader Package 从私有页面目录升级为可被人、Agent 和普通 Markdown 工具直接消费的 OKF v0.2-compatible bundle；本任务只做结构合同，不做正文语义 | 根 Issue ZHI-938 描述："本任务只做结构合同，不做正文语义（正文归 Task 2-B）" | D1/D2/D3 |
| R-002 | 三类 concept type 与 frontmatter contract；未知扩展字段 round-trip 保留 | PRD §6.8："每个 concept 的 frontmatter 至少有 `type`"；"未知扩展字段必须保留，不能因不认识而丢弃" | D1 |
| R-003 | 固定版本 PyYAML safe_load/safe_dump，禁止手写行解析伪装嵌套 frontmatter | PRD §6.8 实施要点 3："Task 2-A 必须采用固定版本的安全 YAML 解析/序列化依赖 `PyYAML`，只使用 `safe_load/safe_dump`" | D1 |
| R-004 | claim_id 是 audit identity，sources[].id 是正文 attribution key；fixture 用标准 Markdown footnote 引用 | PRD §6.8："每个关键事实用标准 Markdown footnote（如 `[^src-abc]`）指向同一页面 frontmatter 的 `sources[].id`" | D3 |
| R-005 | 状态映射三层分开：status / digest_page_status / digest_release_status；verified 只记录真实核验 | PRD §6.8 信号映射 2/3："`verified` 只记录真实的来源/内容回查或独立人工核验"；"`agent_assisted` 不能写成 `human:` actor" | D1 |
| R-006 | 无 LLM 结构验证器；只使用人工编写的三类 fixture 正文验证 attribution，不声称语义质量 | PRD Task 2-A 实施要点 6/8 | D1/D3 |
| R-007 | 固定版本零网络外部 OKF parser smoke；无法固定则降级 OKF-inspired | PRD §6.9.7/8："Task 2-A 必须跑零网络的最小外部 OKF parser smoke；若无法提供固定版本的消费者验证，对外名称改为 `OKF-inspired profile`" | D2 |
| R-008 | 8 条验收标准全部满足；包保持 not_released | PRD Task 2-A 验收标准 1–8 | D1 |
| R-009 | 不做全量 89 篇、不调用 LLM、不重写正文、不引入 OKF runtime/数据库/图服务、不删除旧产物、只在隔离 fixture 中生成 | PRD Task 2-A "不做"："不做全量 89 篇、不调用 LLM、不重写正文、不引入 OKF runtime、Knowledge Catalog、数据库或图服务；不删除旧 Reader/Audit 产物；只在隔离 fixture 中生成 OKF-compatible bundle" | D1 |

## 目标

- 确认 Task 2-A 的边界、取舍和入口验收标准，产出可被下游（build-spec、Task 2-B/2-C）消费的 decision-log。
- 入口验收结论：backfill 门禁 `task2a_entry_allowed=true`、包保持 `not_released`；方向已被 PRD §6.8/§6.9 冻结。

## 成功/失败边界

- 成功边界：8 条验收标准全部覆盖；三处用户决策有真实回答；盲审与细节审查有正式记录；decision-log 经用户确认 accepted 并写入 WorkflowHub task。
- 失败边界：入口门禁不过、或外部 parser 无法固定版本仍宣称 OKF-compatible、或正文语义门提前到本轮、或包状态被改成 released。

## 范围

- 当前范围：结构合同（布局、frontmatter 合同、validator、三个手工 fixture、外部 parser smoke、确定性投影报告）以及本次 scope revision 明确补齐的确定性正向机器信任信号。
- 本次只补页面级 `generated`、`digest_machine_pass`、可由现有来源/Claim 证据证明的 `verified` 事件和显式 freshness 的 `stale_after`；不提前做正文语义、人工读者门、全量发布或 trust score。
- 用户流程/结果只记索引和验收影响，细节进入 spec：正文语义（2-B）、人工读者门（2-C）、全量发布（3）。

## 非目标

- 不编译 89 篇正文；不调用 LLM；不重写正文；不引入 OKF runtime/Knowledge Catalog/数据库/图服务；不删除旧 Reader/Audit 产物；不在正式知识库写包，只在隔离 fixture 生成；不新增通用 repository/service 层；不引入 Attested Computation。

## 决定

```text
### D-001
- question/final_option: Task 2-A 这轮的目标是否定为「只做结构合同」？/ 选 A（只做结构合同）
- recommendation/plain_language: 推荐 A。正好覆盖 8 条验收标准，全部产物 not_released，正文语义归 Task 2-B。
- decision: Task 2-A 只交付 bundle 骨架与文件合同（布局、frontmatter 合同、validator、三个手工 fixture、外部 parser smoke、投影报告）；正文语义编译由 Task 2-B 负责。
- source_type/reference/exact_excerpt: talk-with-zhipeng 第 1 轮用户回答；ZHI-956 comment 1f845377-8159-4a52-bcaa-8f46886484d2；原文："A"
- approval_binding: accepted（用户决策卡回答 "A"，comment 5afa257d-3f26-4222-a802-9757b169987c）
- facts_and_constraints: 入口 backfill 门禁 task2a_entry_allowed=true、task2b_body_compilation_allowed=false；PRD 三任务拆分 2-A/2-B/2-C；Task 2-A 只解决 bundle/frontmatter/index 结构，不能自动解决正文语义（PRD §Task 2-A 风险段）。
- Logic: 入口只允许 2-A 进入且正文门未开 -> 本轮只能做结构合同 -> 验收标准 1–8 全部是结构/投影性质 -> 选 A 恰好覆盖。
- choice_reason/impact: 范围最小且验收全覆盖；影响 Task 2-A 全部交付物形态与 8 条验收标准。
- consequences_and_risks: 外部 OKF parser 若无法固定版本，对外名称按 PRD §6.9.7 降级 OKF-inspired（已留退路）；正文语义风险推迟到 2-B。
- rejected_alternatives: B（结构合同+顺手做 2-B 正文编译）：范围变大、语义门提前、正文门不过整轮无法交付；C（只做骨架，validator/smoke 延后）：验收标准 2/6/8 不满足，本阶段无法收口。
- unresolved_items/owner: 无。
- Supersedes: none
```

```text
### D-002
- question/final_option: 对外命名承诺「OKF-compatible」还是直接「OKF-inspired」？/ 选 A（承诺 OKF-compatible）
- recommendation/plain_language: 推荐 A。官方 reference agent 的 bundle parser 是纯 Python、可离线、可按 commit 固定并 vendor 做零网络 smoke，承诺可行；失败自动降级。
- decision: 对外命名承诺 OKF-compatible：固定 knowledge-catalog 一个 commit，把最小 bundle parser 以固定版本 vendor 进测试，跑零网络 smoke；exit manifest 记录 parser 来源/commit/bundle hash；vendoring 失败则自动降级 OKF-inspired 并省略 okf_version 字段。
- source_type/reference/exact_excerpt: talk-with-zhipeng 第 2 轮问题 1 用户回答；ZHI-956 comment a99ce2fd-c30b-40d1-863e-5b58a65f708d；原文："A"
- approval_binding: accepted（用户决策卡回答 "A"，comment 5afa257d-3f26-4222-a802-9757b169987c）
- facts_and_constraints: PRD §6.9.8 要求实现前定名，不能在 Task 3 才临时决定；官方仓库 GoogleCloudPlatform/knowledge-catalog 的 okf/src/reference_agent/bundle/（document.py/index.py/paths.py）为纯 Python、Apache-2.0、可离线运行；根 index.md 只有 smoke 通过且宣称 OKF-compatible 时才声明 okf_version: "0.2"（PRD §6.8）。
- Logic: 有固定版本可离线消费者 -> 满足 §6.9.7 承诺条件 -> 定名 OKF-compatible 并承担固定 commit 义务 -> 失败路径已在 PRD 冻结为自动降级。
- choice_reason/impact: 满足验收标准 8、对外声明最强、Task 2-B/2-C 沿用同一命名；影响测试依赖（vendored parser）与 exit manifest 内容。
- consequences_and_risks: 引入 Apache-2.0 外部代码与固定 commit 义务，延续到后续任务；vendoring 失败时按 PRD 自动降级，降级原因必须写入 exit manifest。
- rejected_alternatives: B（直接 OKF-inspired，不引入外部 parser，省略 okf_version 字段）：实现最简但验收标准 8 不满足、对外可信度弱一档、后续任务全部按 inspired 口径。
- unresolved_items/owner: 具体固定的 commit 由 build-code 实现时选择并在 exit manifest 记录。
- Supersedes: none
```

```text
### D-003
- question/final_option: 三个手工 fixture 正文的语料基础怎么定？/ 选 A（从 20 个真实样本挑片段人工整理）
- recommendation/plain_language: 推荐 A。入口验收已提供 20 个真实样本（7 个 published、13 个 degraded，覆盖 2 个产品、7 个模块），fixture 基于真实来源片段可验证 attribution 反查，也给 2-B/2-C 铺路。
- decision: 从 20 个真实样本里挑片段，人工整理三类 fixture（产品总览、模块能力、流程规则各一），保留真实 source URI、内容指纹和 claim 映射。
- source_type/reference/exact_excerpt: talk-with-zhipeng 第 2 轮问题 2 用户回答；ZHI-956 comment 2cabf9bb-ecf1-4b2b-b369-ed1cabbc3a45；原文："A"
- approval_binding: accepted（用户决策卡回答 "A"，comment 5afa257d-3f26-4222-a802-9757b169987c）
- facts_and_constraints: PRD 要求「人工编写的三类 fixture 正文」验证 attribution，未要求虚构；入口验收提供 task2-entry-sample-coverage.v1.json（20 个结构样本，verified_source_precheck）；attribution 反查链路：footnote → sources[].id → claim_id + fragment_locator。
- Logic: 有真实来源样本 -> fixture 用真实片段 -> 验收标准 3 的 footnote→sources[].id→claim_id+locator 用真实来源验证 -> 2-B/2-C 用真语料时合同无需重新验证。
- choice_reason/impact: attribution 验证最真实且向后兼容；影响 fixture 文件内容、选样说明和测试设计。
- consequences_and_risks: fixture 与真实语料耦合，选样需说明理由；虚构方案（B）隔离最干净但 2-B/2-C 用真语料时合同要重新验证；自动投影（C）违背 PRD「人工编写」约定。
- rejected_alternatives: B（完全虚构）：attribution 不接触真实来源形态，合同要在 2-B/2-C 重新验证；C（由真实 TopicIndex 自动投影生成）：违背 PRD「人工编写」约定，等于把语义编译提前到本轮。
- unresolved_items/owner: 具体选哪些样本片段由 build-spec/build-code 决定，基于 20 个已验证样本并说明选样理由。
- Supersedes: none
```

```text
### D-004
- question/final_option: 是否回到计划/实现阶段补齐 Task 2-A 已声明但尚未落地的正向信任信号？/ 继续补齐，但只做可由现有证据证明的确定性机器信号
- recommendation/plain_language: 先把“生成过、机器门通过、来源/Claim 回查通过”写成读者能看到且审计能回查的事实；没有证据的人工核验、语义蕴含和新鲜度不补假数据。
- decision: 在本任务新增一个信号投影阶段。每个正式 concept 生成 `generated`；结构与归因机器门通过后写 `digest_machine_pass: true`；对完整 fixture 只从已有 source/claim fingerprint 和 locator 证据生成 `source_hash_match`、`locator_resolved` 两类 `verified` 事件；只在输入明确提供有效 freshness 元数据时投影 `stale_after`。四类白名单中 `critical_token_recheck`、`sampled_entailment`，以及 `human:`/`agent_assisted` 事件继续不生成。
- source_type/reference/exact_excerpt: 当前用户直接指令（2026-08-10）：“回到计划/实现阶段补齐正向信任信号后再验证”；依据既有 spec FR-STATUS-002/003、AC-04 和 PRD §6.8/§6.9.5/§6.9.11/§6.9.12。
- approval_binding: current-user-direct-instruction；不扩展为 Task 2-C 人工读者门或 Task 3 release。
- facts_and_constraints: `verified` actor 必须符合 `process:knowledge-digest-<event>-<detector_version>`；事件引用输入 fingerprint、detector version 和 audit evidence；`digest_content_hash` 排除 generated/verified/machine pass；任何受管内容、归因、分页或 page type 变化使旧 verified 失效；无 freshness 证据省略 stale_after；包仍为 `not_released`、`--no-llm` 零网络。
- Logic: AC-04 已要求这些字段语义可验证，当前实现只保留了负向“没有信号”结果；补上两个可由现有 fixture 证据证明的机器事件即可形成正向证据，同时保留没有人工/语义核验时的 honest boundary。
- choice_reason/impact: 最小闭环能修复当前 verify 的 AC-04 unknown，不引入 provider、数据库、人工队列或第二套事实源；影响 spec、plan、tasks、reader_bundle、frontmatter/Bundle acceptance tests 和当前 audit evidence。
- consequences_and_risks: `source_hash_match` 只证明已审计输入 fingerprint 在 source/Claim/selection 间一致，不等于重新读取外部原始库；`locator_resolved` 只证明 Claim/footnote/target locator 闭合，不等于语义蕴含；这两个限制必须写进 evidence 和最终报告。
- rejected_alternatives: A（继续把正向信号留给 Task 2-C）：AC-04 继续 unknown，当前实现缺少已声明字段的正向生产语义；B（用结构 lint/provider 成功伪造 verified）：违反白名单和 PRD；C（顺便实现人工读者门/8 题）：超出本次用户指令和 Task 2-A 最小范围。
- unresolved_items/owner: `critical_token_recheck`、`sampled_entailment` 和 human reader gate 由 Task 2-C；正式 release 由 Task 3；真实外部原始内容重新读取仍不由本阶段虚构。
- Supersedes: only the Task 2-A deferral wording in D-001's scope projection; D-001's no-LLM/not_released and no-body boundaries remain.
```

## 三轮 talk

| talk_id | 问题/选项 | 后果/风险 | 用户选择/原文 | 队列变化 | source/evidence |
| --- | --- | --- | --- | --- | --- |
| T-001 | 范围：A 只做结构合同（推荐）/ B 结构+正文 / C 只骨架 | 见 D1 | "A" | 队列 1→0，无遗留方向性问题 | comment 6041d6b2.../1f845377... |
| T-002-Q1 | 命名：A OKF-compatible+固定 parser（推荐）/ B OKF-inspired | 见 D2 | "A" | 队列 2→1（问题 1 处理） | comment 3b05207f.../a99ce2fd... |
| T-002-Q2 | fixture：A 真实样本人工整理（推荐）/ B 虚构 / C 自动投影 | 见 D3 | "A" | 队列 1→0 | comment c87fbd59.../2cabf9bb... |
| T-003 | 盲审发现/矛盾/剩余假设：0 个待答问题，按事实关闭 | 无新问题 | 无需回答 | 0→0 | comment d7825982...；方向盲审 pass |

## 调研

| research_id/source | 调研重点 | 关键事实 | 处理状态 | 关联 D |
| --- | --- | --- | --- | --- |
| F-001 / docs/research/20260806-okf-structure-research.md | OKF v0.2 官方结构、信号、参考实现 | 官方仓库 commit `930b65fc3f5619d5d0591f88c72ebae8b848d60d`；bundle parser（document.py/index.py/paths.py）纯 Python、离线可跑、Apache-2.0；type 是唯一必填字段；index.md/log.md 保留名；根 index.md 可声明 okf_version；sources[].id 供正文 footnote 归因；verified/generated 分离；trust tier 是 advisory 不是发布许可 | 已消化，支撑 D2 | D2 |
| F-002 / quality/evidence/task2-entry/ | Task 0/1 重算与入口门禁 | backfill manifest `status=not_released`、`task2a_entry_allowed=true`、`task2b_body_compilation_allowed=false`；Task0 重跑 89 源/125 输出/llm 0/embedding 0；Task1 保存 inventory/topic-plan/topic-index/kb.structure.md；题集 17+3；样本 20 个（7 published、13 degraded，2 产品、7 模块） | 已通过，支撑 D1/D3 | D1/D3 |
| F-003 / PRD §6.9 | 实施前冻结合同 | 8 条冻结决定（Concept Contract v1-draft→v1 生命周期、topic key v2、parser smoke 与命名、单次 contract revision、Task 2-C defect 回修边界等） | 方向冻结，不得临时解释 | D1/D2 |

## grill

| grill_id | CONTEXT/冲突 | 结论 | ADR/四项退出 | source/evidence |
| --- | --- | --- | --- | --- |
| G-001 | Reader Package vs Reader Bundle 关系；references/sources.md 与旧 indexes/sources.md | Reader Bundle 是 Reader Package 的 OKF-compatible 形态，不是两套产品；来源投影在 references/sources.md，旧 indexes/sources.md 不迁移不重写；CONTEXT.md 已补 Reader Bundle 唯一定义 | ADR not-needed（PRD §6.9.7/8 已冻结且可逆）；四项退出全部 pass | comment 8d8774c4...；CONTEXT.md 第 35-36 行 |

## 审查处置

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| FND-001 | 方向盲审（make-decision/direction）pass，无 findings | 无 | fixed | 无需处置；evidence_ref=quality/reviews/results/make-decision-direction-134b4f5a64147f4c54ef79e5ba7f587a4b40f38e-a20c156c-a288-4508-bf8c-582f9bb41767.json | Decision Maker / 下游 Stage / retain |
| FND-002 | 细节审查（make-decision/detail）通过（semantic pass），覆盖三轮职责、决策字段、grill 退出事实与验收可判断性 | 无 | fixed | evidence_ref=quality/reviews/results/make-decision-detail-b54779bef7f4f6a7451263fbcafd208edfeb6fc5-c5700650-ca55-4249-9a90-679712b213fc.json | Decision Maker / 下游 Stage / retain |
| FND-003 | 审查方提出 T-001 首轮直接谈范围、未按「问题/成功标准」对齐首轮职责 | 非可行动 finding（invalid_anchor，单方无佐证） | rejected_invalid | 证据锚点无效；T-001 实际先陈述入口验收/PRD 冻结/调研事实再问单一范围问题，问题/成功标准已由 PRD 冻结且卡内陈述；evidence_ref=quality/reviews/reports/c5700650-ca55-4249-9a90-679712b213fc.md | Decision Maker / 下游 Stage / retain |
| FND-004 | 审查方提出 T-002 同次并行处理命名与 fixture 两个决策轴 | 非可行动 finding（invalid_anchor，单方无佐证）；事实不符：Q1/Q2 是先后两次卡、每次真实回答后重排再问下一题 | rejected_invalid | 证据锚点无效且与事实不符（Q1 答于 05:18:46，Q2 卡于 05:19:23 重排后发出，答于 05:24:17）；evidence_ref=quality/reviews/reports/c5700650-ca55-4249-9a90-679712b213fc.md | Decision Maker / 下游 Stage / retain |

## 最终确认

- 状态：accepted
- 用户原文与 host-visible 绑定：T1/T2 三个回答均为 "A"（comments 1f845377…/a99ce2fd…/2cabf9bb…）；最终决策卡回答 "A"（comment 5afa257d-3f26-4222-a802-9757b169987c，2026-08-07T07:02:44Z，author 志鹏 36d8091a-ab8e-4189-bc2f-67d1dfec84f4）。
- 未确认内容：无。

## 拒绝方案

| 选项 | 拒绝理由 | 关联 D |
| --- | --- | --- |
| 范围 B：结构+正文一起做 | 范围变大，语义质量门提前到本轮，违背 PRD 三任务拆分；正文门不过整轮无法交付 | D1 |
| 范围 C：只做骨架 | 验收标准 2/6/8 直接不满足，本阶段无法收口 | D1 |
| 命名 B：直接 OKF-inspired | 验收标准 8 无法满足（exit manifest 必须记录降级原因），对外可信度弱一档 | D2 |
| fixture B：完全虚构 | attribution 不接触真实来源形态，2-B/2-C 用真语料时合同要重新验证 | D3 |
| fixture C：TopicIndex 自动投影 | 违背 PRD「人工编写」约定，等于把语义编译提前到本轮 | D3 |

## 风险与延期交接

| risk/deferred_id | 风险或延期内容 | 触发/后果 | 处理阶段/owner |
| --- | --- | --- | --- |
| RISK-001 | vendored OKF parser 固定 commit 义务延续到 2-B/2-C | 外部代码升级或维护 | build-code 固定并在 exit manifest 记录；Task 2-B/2-C 沿用 |
| RISK-002 | fixture 与真实语料耦合 | 选样需说明理由 | build-spec/build-code 说明选样理由 |
| RISK-003 | Concept Contract 单次修订预算（v1-draft→v1） | 改变 section/模板/字段/映射消耗唯一一次额度 | Task 2-B；超预算需 PRD scope revision |
| RISK-004 | Task1 历史 receipt 与当前结果冲突未关闭 | 不影响 2-A 控制面投影（fresh backfill 权威），审计债保留 | 已记录 task1-receipt-reconciliation.v1.json；由 Task 3 前人工确认 |
| RISK-005 | 入口 backfill 是重算而非历史 exit receipt | 审计债 | 已披露（backfill manifest missing_or_historical）；不影响 2-A 进入 |

## 质量边界

- 质量事实：方向盲审 pass（1 个有效独立审查方，无 findings）；细节审查 pass（1 个有效独立审查方；2 条 major 意见因证据锚点无效被裁为非可行动，已记录 rejected_invalid 处置）。
- 推进资格：入口门禁已通过（task2a_entry_allowed=true）；本阶段推进资格来自 PRD 冻结方向 + 用户三轮回答 + 两轮正式审查记录 + 用户最终 accepted（comment 5afa257d-3f26-4222-a802-9757b169987c）。
- 完成判据：detail 审查有正式记录 ✓、用户确认 accepted ✓、decision-log 写入 WorkflowHub task ✓、工头确认交接（待下游 stage barrier 唤醒，非本阶段动作）。
- 不可逆授权边界：只有 parser smoke 通过且 bundle 宣称 OKF-compatible 时才允许根 index.md 声明 okf_version: "0.2"；命名承诺延续到 2-B/2-C，降级必须在实现前完成，不能在 Task 3 临时决定。

## 未决项

| item_id | 未决内容 | 原因 | 谁在何时解决 |
| --- | --- | --- | --- |
| OPEN-001 | 三个 fixture 具体选哪些真实样本片段 | 实现细节，依赖 20 个样本的具体内容 | build-spec/build-code，说明选样理由 |
| OPEN-002 | 具体固定的 OKF parser commit | 实现时挑选并记录进 exit manifest | build-code |
| OPEN-003 | Task1 历史 receipt 冲突的最终关闭 | 需要产品维护者最终 canonical 确认，不冒充 | Task 3 前人工确认 |
| OPEN-004 | decision-log 整体接受/拒绝 | 等待用户决策卡真实回答 | 已解决：用户回答 "A"（accepted），绑定 comment 5afa257d-3f26-4222-a802-9757b169987c |

## Supersedes

- none（本任务无先前决策记录；PRD §6.8/§6.9 是上游冻结合同，本 log 引用不替代）。

## 文档结果

- CONTEXT.md：changed；原因：新增 Reader Bundle 唯一定义（与 Reader Package 的关系、references/sources.md 投影路径、豁免清单）；文件引用：CONTEXT.md「Reader Bundle」条目。
- ADR：not-needed；原因：OKF-compatible 命名规则与降级路径已由 PRD §6.9.7/8 在实现前冻结，且自带可逆降级出口；decision-log 引用 PRD 即可，不重复造记录。
- ADR criteria：hard to reverse=false（自带降级出口）；surprising without context=false（PRD 已明文冻结）；genuine trade-off=true（OKF-compatible vs OKF-inspired 是真实取舍，记录在 D2 拒绝方案）。
- 术语/ADR 冲突及处理：Reader Package vs Reader Bundle 关系已澄清（G-001）；references/sources.md 与旧 indexes/sources.md 路径差异已钉死；无其他冲突。
- 不复制 spec 的边界：正文编译细节、validator 实现、PyYAML 具体版本号、fixture 具体正文由 spec/计划承接，不在本 log。

## Exit checks

- 上下文一致：三轮 talk、grill、盲审结论与 PRD §6.8/§6.9、入口 backfill、OKF 官方调研一致。
- owner/接口一致：OKF parser 按官方 commit `930b65fc…` 核实；PyYAML 固定版本 safe_load/safe_dump 由 PRD 固定；豁免清单/布局/命名唯一权威为 PRD §6.8 + CONTEXT.md。
- 失败语义明确：parser smoke 失败→降级 OKF-inspired+省略 okf_version+exit manifest 记录原因；入口缺失→backfill+not_released；degraded 只进 Audit；validator fail-closed。
- 范围与延期明确：范围/非目标已冻结；OPEN-001/002/003 已记录负责人与解决时机。
