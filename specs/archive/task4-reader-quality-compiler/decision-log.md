# Decision Log

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 关联 D/处理状态 |
| --- | --- | --- | --- |
| R-001 | 比较 KnowledgeDigest v19 与 CompanyBrain 的知识成果，找出质量差距和根因，并基于原始方案决定如何继续，使 KnowledgeDigest 的知识结果超过原方案。 | `user-request-2026-08-17-a`："请仔细调查根本原因，派出多个子代理调研，也可以进行外部anysearch调研！" | 已完成事实梳理；待本任务方向决策 |
| R-002 | 按标准 WorkflowHub 新建任务，从 make-decision 开始，不跳阶段，不依赖 build-spec 补需求。 | `user-request-2026-08-17-b`："请按标准 WorkflowHub 新建一个任务，做这个优化吧，从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。" | D-000 已确认 |
| R-003 | Talk 用大白话说明选项、后果和风险；decision-log 记录原始需求、关键事实、选择、理由和延期交接。 | `user-request-2026-08-17-b`："Talk 请用大白话说明选项、后果和风险；decision-log 记录原始需求、关键事实、选择、理由和延期交接。" | D-000 已确认；后续 Talk/Grill/确认待完成 |
| R-004 | 在方向确认前先梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。 | `user-request-2026-08-17-b`："先基于原始需求，梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。" | 当前日志先记录索引；具体方向待 Talk |

## 目标

- 目标：把 KnowledgeDigest 从“来源保真归档器”提升为“面向读者的知识编译器”，并在真实 89 条 Confluence 语料上用可复现的读者任务验证，而不是用页面写入成功或单一机器分数代替知识质量。
- 目标边界：本轮只决定产品方向、用户结果、页面与状态合同、质量边界和延期交接；实现、测试实现和正式发布留给后续阶段。

## 成功/失败边界

- 成功边界：当前任务最终要产出一份用户确认的 `decision-log.md`，明确用户流程、页面范围、数据状态、成功/失败语义、非目标、风险和延期项；下游不需要猜测“什么算读者可用”。
- 成功边界：后续候选结果能从 Reader 入口完成真实知识任务；产品/模块/场景有稳定主轴；正文不是 Evidence 原文堆放；失败或降级内容不会伪装成正常发布；机器门、读者门和交付门分开记录。
- 失败边界：`fidelity_only`、固定模板、占位摘要、可达目录、无断链或 `quality_score` 高，不能单独代表知识消化完成。
- 失败边界：provider 失败、截断、无法归类、无正文或人工读者门未完成时，必须保持 `degraded` 或 `not_released`，不能覆盖上一次正式结果，也不能用 fallback 改写成功；第一闭环任一角色任务失败或负向边界误答时，不能扩大到全量。
- 失败边界：本阶段没有真实用户选择、没有最终决策日志或把未决内容移交给 build-spec 猜测，都不能声称 make-decision 完成。

## 范围

- 当前范围：重新定义并验证 KnowledgeDigest 的 Reader 质量编译链：原始来源快照 → 结构/产品/模块识别 → 主题与页面类型规划 → 可读正文编译 → Reader 导航与 Audit 分离 → 页级状态 → 包级发布门 → 读者任务验证；第一验证场景为 GoInsight 位置字段筛选。
- 历史方向（已由“当前生效修订”覆盖）：先做一个代表性产品/模块的端到端闭环，再推广到全量；不再作为当前范围或当前门槛。
- 页面范围索引：Reader 入口（README/Home/根索引）、产品总览、模块/能力索引、按稳定业务对象或用户任务组织的知识页、相关主题导航、简短来源入口；Audit 侧保留原文、Claim/Evidence/Provenance、运行和失败证据。正式页面细节不在本日志展开。
- 用户流程索引：用户打开 Home → 进入产品 → 进入模块或场景 → 打开一个能解决问题的知识页 → 通过 Summary/边界/步骤/配置/异常/相关主题完成任务 → 查看简短来源；若页面 degraded 或包 not_released，用户和发布方都能看见状态与原因。
- 数据状态索引：来源层 `valid/duplicate/failed/degraded`；页面层 `published/degraded`；候选/交付层 `candidate` 与 `released/not_released`；质量证据层 `machine_pass/agent_assisted/human_reviewed` 分开。具体状态转移待 Talk 收敛。
- 现有方案必须保留的底线：来源可追溯、Claim 只能有一个正式归属、稳定主题身份、页数上限、增量安全写回、失败不伪装成功。

## 当前生效修订（2026-08-18，覆盖旧草案）

旧的 pilot-only、8+3 早期门、逐来源人工状态和多层审查流程保留为历史记录，不再作为当前执行方向。当前生效方向以本节和 D-017～D-019 为准。

- 当前范围：89 条真实来源全量编译、全量机器检查、CompanyBrain 批量对照和一次正式 `17+3` 人工确认；89 条不是要求生成 89 个 Reader 页面，Reader 按产品/模块/任务合并，Audit 必须能回放 89 条来源。
- 人工方式：生成一张批量对照表，集中展示 KnowledgeDigest/CompanyBrain 的答案、路径、边界、来源锚点和异常提示。人工只判断固定 `17+3` 个问题，不逐页打开 89 条；删除 `8+3` 早期人工门。
- 成功条件：在同一批真实问题上，KnowledgeDigest 的路径、答案完整度、边界/来源清晰度整体优于 CompanyBrain；机器报告覆盖 89 条来源；人工确认结果支持该结论。
- 失败条件：关键任务答错、边界说反、来源无法回查、Reader/Audit 混杂、批量评审表缺字段或全量运行失败时，保留完整失败证据，结果标为 `degraded/not_released`，不伪装成功。
- 简化原则：只保留影响“最终产物是否更好”的事实和比较；删除不影响结论的中间门禁、复杂状态矩阵、逐来源人工标签和重复审查流程。

## 非目标

- 本任务不复制 CompanyBrain 的全部文件数量、人工脚本或不确定模块体系，只借鉴其读者主轴、业务对象和场景组织方式。
- 本任务不先做 UI 重绘、文件名美容、加链接、压页数或继续堆字段；这些不能替代正文消化和读者验收。
- 本任务不把 `agentmemory`、调度器、数据库、向量数据库或后台守护加入正式 KnowledgeDigest pipeline。
- 本阶段不实现代码、不跑正式全量发布、不覆盖 CompanyBrain、不把当前 v19 标为 released，也不通过 build-spec 补齐本阶段遗漏的方向需求。

## 决定

### D-000
- question/final_option: 这次优化从哪里开始？选择标准 WorkflowHub `make-decision`，不跳阶段。
- recommendation/plain_language: 推荐且已按用户要求执行；先把“要做成什么、什么不做、失败怎么算”说清楚，再进入规格和实现。
- decision: 当前任务 `task4-reader-quality-compiler` 只从 `make-decision` 开始；`build-spec` 不负责补本阶段遗漏的需求。
- source_type/reference/exact_excerpt: user_reply / `user-request-2026-08-17-b` / "从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。"
- approval_binding: 用户原始要求已绑定；最终方向尚未确认。
- facts_and_constraints: WorkflowHub 当前任务已建立；当前 make-decision 质量事实仍缺 scope、non-goals、risks、Talk、finding dispositions 和 human confirmation。
- Logic: 原始要求 -> 需要先收敛方向 -> 选择 make-decision -> 下游只消费已确认决策。
- choice_reason/impact: 先消除方向歧义，避免实现后再返工；影响当前只写 decision-log，不创建 spec/plan/tasks。
- consequences_and_risks: 需要用户分轮选择，短期不会立刻产出代码；如果用户不回复，阶段保持 in_progress，不能伪装完成。
- rejected_alternatives: 直接进入 build-spec；先改代码再补需求；复用旧 Task3 作为本任务决定。它们都违反当前用户边界或会把未决方向带入实现。
- unresolved_items/owner: Reader 质量优化的第一条方向轴尚未由用户选择；owner 为用户，在 Talk Round 1 处理。
- Supersedes: none

### D-001
- question/final_option: 第一阶段是 89 条全量重做、只修质量门，还是先做一个代表性产品/模块闭环？选择 B：先做一个代表性产品/模块闭环。
- recommendation/plain_language: 推荐且已被用户选择；先把一条完整路径跑通，能更快看出哪里真的不好读，再扩展全量。
- decision: 第一阶段只做一个代表性产品/模块的完整 Reader 质量闭环，覆盖来源整理、产品/模块/主题规划、类型化页面、导航、状态和读者任务验证；全量 89 条重编译延期到闭环通过后。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-17-talk-round-1` / "B"
- approval_binding: Talk Round 1 用户选择已记录；最终 make-decision 仍待后续 Talk、Grill 和最终确认。
- facts_and_constraints: v19 有 40 条 `fidelity_only` 和 41 条失败；原始 PRD 要求小语料先测，且明确建议不要让全量任务同时承担主题探索和正文设计；CompanyBrain GoInsight 方案建议先处理一个模块，并先输出 compile review。
- Logic: 全量同时承担探索与编译 -> 失败难定位且成本高 -> 先做代表性闭环 -> 用真实读者结果决定是否推广。
- choice_reason/impact: B 能保留真实问题和端到端链路，又把返工范围限制在一条可观察路径；影响是全量结果暂不承诺，第一闭环必须包含正向和失败样本，不能只挑好看的页面。
- consequences_and_risks: 短期只能得到局部候选包；代表性选错会漏掉长文、表格/图片、双语、多源或失败来源等问题；后续必须按冻结覆盖规则扩展，不能把一个模块的成功外推成全库成功。
- rejected_alternatives: A 全量重做：成本高、根因难定位，容易重演“写完但不好读”；C 只修质量门：能阻止假通过，但不能消除原文堆积。
- unresolved_items/owner: 代表性产品/模块具体选哪个、覆盖哪些来源和读者任务，下一轮 Talk 决定；owner 为用户，make-decision 负责提供证据和选项。
- Supersedes: none

### D-002
- question/final_option: 代表性闭环选哪个切片？选择 A：GoInsight“字段与筛选”。
- recommendation/plain_language: 推荐且已被用户选择；这个切片的业务对象、规则边界和操作链路最清楚，能直接检验 KnowledgeDigest 是否真的把原文编成可用知识。
- decision: 第一阶段以 GoInsight“字段与筛选”为代表性产品/模块切片；候选来源包括数据分析、位置字段筛选、添加关联数据、添加指标、指标详情和累计计算等，最终来源清单与读者题集仍需冻结。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-17-talk-round-2` / "A"
- approval_binding: Talk Round 2 用户选择已记录；最终 make-decision 仍待独立方向建议、Talk Round 3、Grill 和最终确认。
- facts_and_constraints: CompanyBrain GoInsight 编译方案明确建议从“字段与筛选”开始；原始 GoInsight 语料包含字段、筛选、指标、数据分析和关联数据相关材料；原 PRD 要求小语料覆盖真实结构类别，并先生成规划再编译候选页。
- Logic: 需要一个能验证业务对象/规则/操作链路的切片 -> “字段与筛选”有明确关系和真实来源群 -> 选择 A -> 用一条模块闭环检验导航、正文、归因和读者任务。
- choice_reason/impact: A 最能直接暴露当前固定模板、关键词归类和原文堆放的问题；影响第一阶段不覆盖全库，只冻结这个模块的来源清单、结构方案、候选页和读者验证。
- consequences_and_risks: 资料可能分散在多个产品流程中，若边界不严会把指标、图表或数据集混进字段模块；切片成功也不能外推全库，必须保留扩展前的 coverage gap。
- rejected_alternatives: B 数据分析主流程：覆盖更宽但对象关系更多，容易重演范围膨胀；C 指标流程：链路清楚但页面类型和资料类型较窄，不能充分检验通用编译链。
- unresolved_items/owner: 具体 source manifest、对象边界、页面类型、正负读者题和排除项，需在 Talk Round 3/Grill 前冻结；owner 为 make-decision 与用户共同确认。
- Supersedes: none

### D-003
- question/final_option: 第一闭环服务哪类读者？选择 C：GoInsight 使用者/实施支持人员和产品/研发/技术人员同时覆盖。
- recommendation/plain_language: 用户已选择；两类人都要能从同一知识结果完成自己的任务，但不能因此写成一篇没有重点的“大杂烩”。
- decision: 字段与筛选闭环同时验证业务使用/支持任务和技术理解/边界任务；后续必须明确两类任务、页面分层或分流方式，以及各自的成功/失败判定。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-17-talk-round-3` / "C"
- approval_binding: Talk Round 3 用户选择已记录；最终方向仍待页面结构、Grill 和最终确认。
- facts_and_constraints: 字段与筛选同时涉及业务选择/查询和字段模型/规则边界；审查指出目标读者、核心任务、页面纳入和状态行为未定义；不能用一套泛化摘要声称两类读者都被覆盖。
- Logic: 两类真实使用者都需要知识 -> 单一角色验收会漏掉另一类问题 -> 同时覆盖两类 -> 用分开的读者任务集和清楚的页面结构验证，避免正文混合失焦。
- choice_reason/impact: C 保留业务可用性与技术可信度，能更严格检验“超过原方案”；影响样本、页面结构、读者门和成本都扩大，必须明确共享内容与角色专属内容。
- consequences_and_risks: 第一闭环更复杂；若页面同时堆两套内容，会重演原文堆积；若拆成两套页面，又会产生重复、漂移和维护成本。
- rejected_alternatives: A 只覆盖使用/支持人员：技术边界可能漏测；B 只覆盖产品/研发/技术人员：普通使用者的可读性可能漏测。
- unresolved_items/owner: 两类读者是同页双层、同主题双入口还是其他结构，下一问处理；owner 为用户，make-decision 记录。
- Supersedes: none

### D-004
- question/final_option: 两类读者如何进入正文？选择 A：同一主题、同页双层结构。
- recommendation/plain_language: 推荐且已被用户选择；先给业务/支持人员可执行的答案，再给产品/研发/技术人员所需的模型、规则和边界，事实底座保持一套。
- decision: 字段与筛选主题使用一个 canonical Reader 主题页，正文按“使用/操作层 → 规则/边界层”组织；两类读者从各自索引或入口进入同一主题，不复制两套 canonical 正文。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-17-talk-round-3-page-structure` / "A"
- approval_binding: Talk Round 3 页面结构选择已记录；最终方向仍待任务验收、Grill 和最终确认。
- facts_and_constraints: 用户要求同时覆盖两类读者；原方案要求单一 canonical Reader tree、按 page type 组织正文、超长按语义边界拆分；审查要求明确角色任务和失败后的行为。
- Logic: 两类读者共享同一主题事实 -> 双入口会增加重复和漂移 -> 同页按层组织 -> 一套 Claim/Evidence，两个阅读层次。
- choice_reason/impact: A 维护面最小、事实不分叉，也能验证业务可用性和技术可信度；影响页面必须控制长度，不能把两层内容简单拼接。
- consequences_and_risks: 同页可能过长或两层边界不清；必须有明确标题、角色入口提示、语义分页和层级验收，否则会重新变成大杂烩。
- rejected_alternatives: B 双入口：角色清楚但会增加导航和内容漂移风险；C 延期一类读者：与 D-003 冲突，留下方向审查盲区。
- unresolved_items/owner: 两层分别对应哪些真实任务、每层的必需答案和通过条件，下一问处理；owner 为用户与 make-decision。
- Supersedes: none

### D-005
- question/final_option: 双层页面如何验收？选择 A：同一个真实场景，按两种角色分别验收。
- recommendation/plain_language: 推荐且已被用户选择；不做两套互不相关的演示，而是让两类读者围绕同一个字段/筛选问题各自完成任务。
- decision: 第一闭环使用一个共同真实场景；使用/支持层验证能否完成选择、查询、判断和排查，规则/技术层验证能否解释字段模型、筛选关系和边界。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-17-talk-round-3-task-shape` / "A"
- approval_binding: Talk Round 3 任务形态已记录；具体真实场景、阈值和停止条件仍待确认。
- facts_and_constraints: 原始语料同时存在数据分析、位置字段筛选、字段关系、设备位置历史数据集和性能限制；审查要求目标任务、对照、停止和回滚可判定；小闭环不能扩成完整题集。
- Logic: 同一主题需要验证两类读者 -> 同一场景能保持事实和路径一致 -> 选择 A -> 以两类角色的不同完成条件共同判断页面是否可用。
- choice_reason/impact: A 最能检验同一内容是否既可操作又可信，且能控制第一阶段范围；影响后续必须定义两个角色的可观察结果，不能用“读过页面”当通过。
- consequences_and_risks: 场景选得太简单会漏掉关系和边界；选得太复杂会重新扩大范围；两层答案必须共享同一事实，不能出现角色间结论冲突。
- rejected_alternatives: B 两条独立任务：覆盖更宽但会增加样本和归因成本；C 完整多任务题集：不符合先做小闭环的决定。
- unresolved_items/owner: 具体采用位置字段、普通字段/时间、还是关联数据场景，下一问处理；owner 为用户与 make-decision。
- Supersedes: none

### D-006
- question/final_option: 双角色共同验收的具体场景和细节怎么定？选择 A：由 make-decision 基于现有证据直接冻结，不再逐项询问。
- recommendation/plain_language: 推荐且已被用户授权；核心不是继续讨论验收表，而是让 KnowledgeDigest 在一个真实问题上产出比 CompanyBrain 更能用的答案。
- decision: 第一闭环固定为“市场管理员或支持人员按区域筛选设备”。使用/支持层要能从入口找到位置字段筛选、完成区域内/区域外筛选并知道限制；规则/技术层要能解释该筛选属于数据分析、位置字段的语义、绘制规则、点数限制、性能事实和不适用边界。两层共用一套 canonical 主题事实，具体验收细节由本任务依据证据冻结，最终仍交用户确认。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-17-detail-delegation` / "A，这些验收细节没必要问的这么详细，你自己可以决定，当前的核心还是如何修改KnowledgeDigest能让最终产物质量比原来的companybrain高！"
- approval_binding: 用户已明确授权 make-decision 自行决定细节；最终 make-decision 方向仍需用户确认。
- facts_and_constraints: 原始 `位置字段筛选.md` 有区域内/区域外、地图绘制、至少 3 个点、最多 100 个点、不允许相交/穿越和百万终端性能事实；v19 已保留不少事实但仍是摘要/详细内容/来源的固定包装；CompanyBrain 同主题页额外提供何时查、操作边界、排查和相关主题入口。
- Logic: 需要证明 Reader 结果真的解决问题 -> 位置筛选同时有操作、规则和反例边界 -> 用一个真实场景让两类读者分别完成任务 -> 把细节交给证据和质量门冻结，避免继续消耗在微小选项上。
- choice_reason/impact: A 直接把讨论收束到可观察的读者结果，并保持第一阶段可逆；影响是 make-decision 必须自己补齐样本、对照、通过和停止条件，不能把“用户没逐项选”当成下游猜测的理由。
- consequences_and_risks: 场景覆盖有限，不能代表所有 GoInsight 页面；若来源边界或负面边界漏掉，页面可能看似完整却给出错误操作建议；失败必须停在 `degraded/not_released`，不得扩大或覆盖正式结果。
- rejected_alternatives: 继续逐项询问每个验收字段：会拖慢主线，且用户已明确授权；直接用一条 v19 页面作通过：无法证明比 CompanyBrain 更好；一次性覆盖全量 89 条：违反先做代表性闭环的选择。
- unresolved_items/owner: 代码实现、精确字段 schema、自动化题集和最终全量推广规则留给后续阶段；方向层 owner 为 make-decision，最终确认 owner 为用户。
- Supersedes: none

### D-007
- question/final_option: 什么才算“比 CompanyBrain 更好”？选择：先在本闭环的同一真实场景上设定硬底线加严格优势，不拿文件数或单一机器分数代替读者质量。
- recommendation/plain_language: 推荐；先保证不能答错、不能找不到、不能说不清来源，再要求关键任务比 CompanyBrain 更快找到答案、边界更清楚、排查路径更完整。
- decision: 第一闭环只有同时满足以下条件才可称为优于 CompanyBrain：1）两类角色任务都能从 Reader 入口完成；2）位置筛选的关键事实、限制和不适用边界不丢失、不矛盾；3）每个关键结论有可回查来源和定位；4）没有占位摘要、原文堆放或 `fidelity_only` canonical 页；5）导航能到达主题并能继续看相关主题；6）用同一题目、同一记录格式对比 CompanyBrain 参考页，KnowledgeDigest 在“首个相关页/跳转路径、答案完整度、边界与排查清晰度”三个比较轴上至少有一个严格更好，另外两个不能更差；任一硬底线失败、没有严格优势或出现任一轴变差，都判定 pilot 停止，不扩大、不发布。该标准只对第一切片生效，不外推全库。
- source_type/reference/exact_excerpt: make-decision synthesis / `F-001`–`F-011`、`D-003`–`D-006` / 基于 v19、原始来源和 CompanyBrain 同主题页的页级对照。
- approval_binding: 当前为待用户最终确认的方向草案；下游须消费该比较标准，不得自行降级为“生成成功”。
- facts_and_constraints: v19 的 99.78 代理分数与 40 条 `fidelity_only`、41 条失败、`not_released` 并存；CompanyBrain 的同主题页有何时查、操作/边界、排查、相关页和来源入口；因此“机器分数高”不是充分条件。
- Logic: 质量目标是读者完成任务 -> 先设硬正确性/可信度底线 -> 再与现有 CompanyBrain 做同场景对照 -> 只有可观察优势才算超过。
- choice_reason/impact: 该标准直接对准用户核心目标，并能防止漂亮但无用的页面通过；影响是第一闭环可能因 CompanyBrain 已较强而判定未超过，届时必须修正编译链或保持不发布。
- consequences_and_risks: “更好”仍需要后续把任务结果记录成可复现证据；不同角色耗时或表述判断存在主观性，必须保留页级事实、题目、答案和人工读者记录，不能只报结论。
- rejected_alternatives: 只看页面数量/覆盖率：会奖励堆页；只看质量代理分数：已被 v19 证明会假绿；要求第一轮全面胜过 CompanyBrain 全库：范围过大，无法定位改进是否有效。
- unresolved_items/owner: 题目文本、预期答案和记录格式已在 D-010 冻结；后续只补自动化执行、正式报告字段和既有 Task 2-C/Task 3 的评审主体绑定，不得改变比较轴或“不达标不推广”。
- Supersedes: none

### D-008
- question/final_option: 第一闭环的来源和失败后怎么处理？选择：冻结最小真实清单，独立生成候选，硬失败即停止，不覆盖、不扩张。
- recommendation/plain_language: 推荐；先用三份能串起“怎么用、怎么筛、拿什么数据验证”的真实来源，失败时保住现有知识，不把半成品当新版本。
- decision: 第一轮 primary source manifest 固定为 `goinsight-location-pilot-20260817-v1`，来源路径和快照指纹为：`GoInsight/数据分析.md`（54 行，sha256 `52abb4c14c9beb1f0752bb6c50a8da9bef225237fc46e76f5f9c471e87c42668`）、`GoInsight/位置字段筛选.md`（72 行，sha256 `32b3c01b03a44727c6a692e9b10e3ee71106abec1f90c45272cbd75c9bce32b1`）、`GoInsight/设备位置历史数据集.md`（44 行，sha256 `39b5bf52e177319239ebe6afb1df037163b6e567ef2ae2752bc46b3bab739cb6`）。初始排除 `GoInsight/添加指标页.md`、`GoInsight/指标详情页.md`、`GoInsight/图表类型.md`、`GoInsight/添加关联数据.md`，各自排除原因是它们不是位置字段筛选第一闭环的必需来源。候选包写入隔离目录，不覆盖 CompanyBrain 或当前正式结果。只有当 D-010 的两类正向任务、负向边界、关键事实和来源定位、无占位/`fidelity_only` canonical 页、Reader 导航和 D-007 的严格对照门全部通过时，才允许交给下一阶段；任一硬条件失败则标记 `degraded/not_released`，记录原因并停止扩张。发现依赖缺口时必须生成新 manifest/version、绑定新快照指纹并重新记录原因，不得静默加源。
- source_type/reference/exact_excerpt: make-decision synthesis / `F-007`、`F-009`–`F-011`、`D-001`、`D-006` / 第一切片来源边界与回滚方案。
- approval_binding: 用户已授权由 make-decision 冻结细节；最终确认后才能交给下游消费。
- facts_and_constraints: 原始来源中 `位置字段筛选.md` 给出核心操作与限制，`数据分析.md` 给出入口和筛选上下文，`设备位置历史数据集.md` 给出真实验证问题和字段关系；CompanyBrain 同主题页可作为对照，不是写入目标。
- Logic: 小范围实验必须可复现、可回滚 -> 冻结来源和排除项 -> 独立生成候选 -> 用正向与负向任务验收 -> 硬失败停在未发布。
- choice_reason/impact: 该边界能把根因定位到结构、编译或质量门，避免再次把全量语料混成一个不可解释的结果；影响是第一轮不会解决所有字段/指标/关联数据问题。
- consequences_and_risks: 三份来源仍可能遗漏跨页关系；排除项过严时只能显式生成新 manifest/version 并重跑受影响审查，不能把新来源偷偷塞进同一 pilot。当前 manifest 指纹只代表本机原始快照，后续交接必须保留相同的相对路径和内容哈希。
- rejected_alternatives: 直接沿用 v19 全量输入：不可定位、不可回滚；把所有候选文件都纳入：范围膨胀；失败后用 fallback 继续发布：会重复当前 `fidelity_only` 假通过。
- unresolved_items/owner: 页级字段、自动化检查命令和下一版本 manifest 的存储实现留给后续规格/计划；本阶段已冻结第一版本的来源身份、覆盖关系、排除项和扩源规则。
- Supersedes: none

### D-009
- question/final_option: 第一切片的两角色小闭环会不会放宽原 KnowledgeDigest 的正式读者门？选择：不会；它只是方向验证和候选包门，正式 Task 2-C/Task 3 门保持不变。
- recommendation/plain_language: 必须保留；位置字段筛选先证明编译链值得推广，但不能把两道题的通过包装成 89 条全量发布通过。
- decision: D-006–D-008 的两角色任务、负向边界和 CompanyBrain 对照只决定“第一切片是否值得继续”。它不修改原 PRD 的正式合同：Task 2-C 仍需使用冻结题集的 answerable 子集、至少 8 个正向题、覆盖规则和 3 个负向题零误命中；Task 3 仍需完整 17+3 题集及既有发布门。若后续要改变 page type、section、题集、阈值或 provider allowlist，必须走新的 scope revision，不能用本轮 pilot 偷改。
- source_type/reference/exact_excerpt: grill/codebase fact / `docs/plans/knowledge-digest-knowledge-publication-prd.md` §6.2、§6.9、Task 2-C exit、Task 3 exit / "Task 2-B/2-C 只能使用样本可答子集；Task 3 使用完整题集"。
- approval_binding: 这是基于现有项目合同的边界解释，待最终用户确认后作为下游约束。
- facts_and_constraints: 原 PRD 已把“样本方向验证”和“正式读者/交付门”分开；CONTEXT.md 与 ADR 0004/0008 也要求 Reader/Audit 分离、失败不伪装发布、Task 3 的 `released/not_released` 不被候选结果替代。
- Logic: 第一阶段要小而可逆 -> 不能用小样本替代正式全量门 -> 保留 pilot 作为继续/停止信号 -> 正式 release 继续消费既有 PRD 门。
- choice_reason/impact: 避免为了让 pilot 看起来通过而降低项目已有质量合同；影响是本任务结束时只确认优化方向，不声称完成全量知识结果。
- consequences_and_risks: 如果 pilot 通过，后续仍需补齐多产品/模块、页面类型和全量题集；如果 pilot 失败，保持候选未发布，不得用旧 v19 分数或 CompanyBrain 文件数量掩盖失败。
- rejected_alternatives: 把两角色两任务当正式 reader gate：违反原 PRD；为满足 pilot 临时降低 8/17+3 门槛：制造不可追溯的合同漂移。
- unresolved_items/owner: 后续任务如何把位置筛选 pilot 映射到冻结题集和三类 page type，由 build-spec/plan 在不改方向的前提下展开；若需改合同，由新 scope revision 负责。
- Supersedes: none

### D-010
- question/final_option: 第一切片怎么把“读者能用”和“比 CompanyBrain 好”变成可打破的最小门？选择：冻结两条正向任务、两条负向边界和同题对照记录。
- recommendation/plain_language: 推荐；不再写“内容覆盖了就算好”，而是让支持人员和技术人员分别给出可检查的答案，答错一条就停。
- decision: 固定以下 reader gate。使用/支持任务 S-01：从 Reader `Home` 出发回答“我想在数据分析里筛出区域内的设备，应该从哪里开始？Inside/Outside 怎么选？画区域提交前需要满足什么条件？”预期输出必须包含：进入数据分析页；把位置字段拖入筛选栏；选择 Inside/Outside 且说明 Inside 为默认；地图至少 3 点、最多 100 点；多边形不能交叉；Submit/Cancel、双击删点和 Clear 的基本处理；结果会保留点位/筛选条件，当前不展示小地图。规则/技术任务 T-01：从同一入口回答“为什么位置字段只能在数据分析页筛选？设备位置历史数据集怎么验证这个场景？报告里的地理位置计算指标能不能当普通位置筛选使用？”预期输出必须区分：位置字段在数据分析页配置，数据集详情页和全局筛选卡片不支持；位置历史数据集的真实评测关系包括 Location、Reseller、Merchant、Terminal SN、Event Time 以及 30 天/SN/位置变化问题；报告里的地理位置计算指标不是普通位置筛选规则，不能把两者混答。负向边界 N-01：询问“能否在数据集详情页或全局筛选卡片添加位置筛选”，必须明确回答不支持；N-02：询问“报告计算指标是否自动具备普通位置筛选能力”，必须明确回答不是同一规则/当前不支持，不能编造支持路径。每条任务记录：入口、首次命中页、跳转数、答案要点、来源定位、错误或遗漏；同一题目和同一记录格式同时跑 CompanyBrain 参考页。硬门为 S-01/T-01 全部完成、N-01/N-02 零误导、关键事实和来源定位 100%、无占位/原文堆放/`fidelity_only` canonical 页、Reader 导航可达。通过硬门后，三个比较轴“首个相关页/跳转路径、答案完整度、边界与排查清晰度”必须至少一轴严格优于 CompanyBrain、其余不差；否则 pilot 停止。
- source_type/reference/exact_excerpt: detail-review repair / `F-009`–`F-011`、原始 `GoInsight/位置字段筛选.md` L3–L61、`GoInsight/数据分析.md` L5–L43、`GoInsight/设备位置历史数据集.md` L3–L31、CompanyBrain `Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md` L24–L166。
- approval_binding: 用户已授权 make-decision 自行冻结细节；最终确认前仍是当前方向草案，不能直接声称 reader gate 已执行通过。
- facts_and_constraints: 原始来源明确写出区域背景、Inside/Outside、3–100 点、交叉校验、数据集详情/全局筛选限制和报告计算指标边界；CompanyBrain 参考页已有何时查、排查、相关页等可比较结构；v19 页虽然保留事实，但没有以上任务级门。
- Logic: 需要证明“知识结果更好” -> 固定同一问题和答案要求 -> 同时对照 CompanyBrain -> 硬错停、严格优势才继续。
- choice_reason/impact: S-01 检验操作可执行性，T-01 检验跨来源技术解释，N-01/N-02 防止页面把能力边界说反；影响是第一轮只证明这一条切片，不把题目数量伪装成全库质量。
- consequences_and_risks: 任务答案需要后续执行器记录真实首次命中和来源回查；如果 CompanyBrain 同样通过，KnowledgeDigest 必须在路径、完整度或边界排查中产生严格增益，否则保持不发布。
- rejected_alternatives: 只检查标题、摘要、Claim 数或页面存在：不能证明任务完成；把精确题目留给 build-spec：违反用户不依赖 build-spec 补方向需求；只测正向题：会漏掉错误能力边界。
- unresolved_items/owner: 自动化执行命令、结果文件 schema 和既有 Task 2-C/Task 3 评审主体由下游展开，但不得修改 S-01/T-01/N-01/N-02 或比较门。
- Supersedes: none

### D-011
- question/final_option: 三份来源部分失败、页面失败、候选失败和恢复时怎么行动？选择：用不可变 manifest + 明确状态转移，任何必需来源/必需证据失败都不交付。
- recommendation/plain_language: 推荐；失败时让人一眼看到“哪里坏了、当前不能用、旧结果还在”，而不是留下半页看起来像成功的知识。
- decision: 状态合同固定为：`valid` 来源可进入 Claim/Evidence；`duplicate` 只保留 canonical 来源关系，Reader 继续指向 canonical；`failed`/`degraded` 来源只进 Audit，不能进入 Reader 导航。页只有在必需 section 有真实内容、关键 Claim 可回查、无 semantic fallback/`fidelity_only` 且导航校验通过时才是 `published`；否则是 `degraded`，从 Reader 导航排除。候选编译完成但未完成读者门仍是隔离的 `candidate`，不等于发布；任一三份 primary source 失败、必需页 degraded、S-01/T-01 未完成、N-01/N-02 误答、来源定位不全或对照无严格优势时，pilot outcome 为 stop，交付状态保持 `not_released`，旧 formal 不变。即使部分无关页已生成，也只能留在隔离候选/Audit，不能成为当前知识入口；只有保留的正式 Task 3 机器门、完整 17+3 读者门和交付门全部通过，才允许 `released`。
- recovery: 同一冻结快照上的编译缺陷只能产生新的运行记录并重跑受影响门；来源内容变化、来源新增或排除项变化必须新建 manifest/version、重新计算 hash、说明依赖原因并重新审查，不能续跑旧清单或隐式扩源。失败时不覆盖 CompanyBrain、旧 formal 或已 released 包；修复前后都保留失败现场和恢复路径。
- source_type/reference/exact_excerpt: detail-review repair / `F-984df3be9a30`、`D-008`、原始 PRD §6.2/§6.9/Task 2-C/Task 3、`CONTEXT.md`、ADR 0004/0008。
- approval_binding: 这是对既有 `published/degraded`、`released/not_released` 合同的本任务应用，不新增状态类型；最终确认后由下游实现和验证。
- facts_and_constraints: 项目已有 Reader/Audit 分离和页级/交付级状态；原 PRD 明确失败不能用 fallback 伪装、Task 2-C/Task 3 门不能被 pilot 降低；三份来源的相对路径和内容 hash 已在 D-008 冻结。
- Logic: 状态名称本身不够 -> 为每个状态定义进入条件、可见性和恢复行为 -> 必需来源失败阻断 pilot -> 旧 formal 安全保留。
- choice_reason/impact: 能直接回答审查指出的“部分失败后用户看到什么、何时重试”；影响是有些生成出来的页面即使内容局部可读，也不能因为写出来了就进入正式 Reader。
- consequences_and_risks: 候选包会更容易保持 `not_released`，但这是诚实成本；若未来要允许局部发布，必须另开 scope revision，不能在本 pilot 中临时放宽。
- rejected_alternatives: 只把失败写进 Audit 但继续导航：会让读者误信；把部分成功自动合并回旧 formal：违反单写者和回滚边界；用同一 batch-state 强行续跑变更后的来源：破坏输入身份。
- unresolved_items/owner: 具体文件布局、状态字段和命令由 build-spec/build-plan 展开；状态转移、可见性、阻断和回滚语义已由本阶段决定。
- Supersedes: none

### D-012
- question/final_option: 对照 CompanyBrain 和“关键事实 100%”怎样做到别人照着也能复跑？选择：冻结起点、跳转计数、Claim checklist、评分公式、并列处理和记录格式。
- recommendation/plain_language: 推荐；不让验收者凭感觉说“差不多”，每个事实一条一条对，三个比较轴按同一公式算，证据缺一项就停。
- decision: 两个包都从各自 `Home.md` 开始，不允许直接打开目标页；按 S-01、T-01、N-01、N-02 的固定顺序执行。一次 hop 只计一次 Reader 内部 Markdown link 点击/跳转，打开 Home 记 0，首次打开包含题目所需至少一条 Claim 的页即为 first hit；无 first hit 记为失败。每条 Claim checklist 通过=1，缺失、含糊、方向错误或没有可回查锚点=0；正向题必须 100% 通过，负向题必须 1/1 明确拒绝且不能同时给出相反建议。固定 checklist：`CL-S01-01` 数据分析页把位置字段拖入筛选栏（位置字段筛选 L22–L24）；`CL-S01-02` Inside/Outside 且 Inside 默认（L25–L30）；`CL-S01-03` 点位交互、至少 3 点、最多 100 点（L31–L49）；`CL-S01-04` 区域交叉不能提交（L46–L51）；`CL-S01-05` 提交/取消、删点/清空、结果点位和当前不展示小地图（L36–L61）；`CL-T01-01` 位置字段只在数据分析页，不在数据集详情页/全局筛选卡片（L58–L60）；`CL-T01-02` 位置历史数据集验证上下文包含 Location、Reseller、Merchant、Terminal SN、Event Time 及近 30 天/SN/位置变化问题（设备位置历史数据集 L3–L18、L23–L31）；`CL-T01-03` 报告地理位置计算指标不是普通位置筛选规则且当前不支持该做法（位置字段筛选 L60–L61）；`CL-T01-04` 百万终端是位置筛选的性能背景，不能被写成单机实测结果（位置字段筛选 L3–L6）；`CL-N01-01` 数据集详情页/全局筛选卡片明确不支持位置筛选（位置字段筛选 L58–L60）；`CL-N02-01` 报告计算指标不得被回答为普通位置筛选能力（位置字段筛选 L60–L61，CompanyBrain 参考页 L123–L125）。每条 checklist 还必须带 `manifest_id + source_relative_path + line_start + line_end + content_hash`，不能只写“有来源”。
- comparison_contract: 记录字段固定为 `case_id, package_id, entry_path, first_hit_path, first_hit_kind, hop_count, claim_results, source_anchors, boundary_score, protocol_id, prompt_set_id, evaluator_id, evaluator_config_hash, session_id, package_order, isolation_mode, run_at, failure_reason`。答案完整度轴 = 通过 checklist 条目数 / 应答条目数；边界与排查轴固定 4 项：能识别只支持数据分析、能拒绝数据集详情/全局筛选、能区分报告计算指标、能给出点数/交叉/Inside-Outside 排查路径，得分为通过项 / 4；路径轴使用确定性三元组 `route_rank = (reachable, first_hit_kind, -hop_count)`：`reachable` 可达=1/不可达=0，`first_hit_kind` 命中 canonical 主题页=2、只命中产品/模块索引=1、无命中=0，按字典序比较；`route_delta` 是两包三元组比较的 sign，不能把不同含义的路径字符串直接相减。三轴分别计算 `KD - CompanyBrain`：数值轴差值 > 0 为严格更好，= 0 为不差，< 0 为变差；路径轴按 `route_delta` 得到 +1/0/-1。必须至少一个轴 > 0、没有轴 < 0，且所有记录都有证据，否则 pilot stop。并列不算更好；无法判定也不算通过。共同协议、题集、evaluator config、运行条件和隔离字段来自 D-016。
- source_type/reference/exact_excerpt: detail-review repair / `F-7e68c59ad1fb`、`F-b0cc37e256bb`、`D-010`、`D-011`、原始三份来源和 CompanyBrain 参考页。
- approval_binding: 用户已授权 make-decision 自行定下这套最小测量合同；最终用户确认前保持 pending。
- facts_and_constraints: 同一来源快照的路径/行号/hash 已在 D-008 冻结；CompanyBrain 参考页有同场景可对照内容；原 PRD 要求固定题集、可回查证据和失败闭环，不能用开放式“读者觉得好”替代。
- Logic: 需要可复现比较 -> 固定入口/计数/题目/Claim/公式 -> 记录逐条证据 -> 缺证据或没有严格优势就停止。
- choice_reason/impact: 这套门能直接阻止“页面多、摘要长、分数高”冒充质量，也让后续报告能解释到底赢在哪里；影响是验收成本会上升，但只针对第一条 pilot。
- consequences_and_risks: CompanyBrain 如果在三轴上同样强，KnowledgeDigest 可能无法通过；这是有效结果，不允许靠改题、改起点或放宽并列规则制造优势。
- rejected_alternatives: 只记录首次命中页不记录 hop/答案：无法比较；只看总分不看逐条 Claim：会掩盖关键边界丢失；并列算通过：无法证明“超过”。
- unresolved_items/owner: 记录文件的具体落盘路径和执行器实现留给后续规格/计划；字段、题目、公式、并列和缺证据处理已由本阶段决定。
- Supersedes: none

### D-013
- question/final_option: CompanyBrain 对照怎样保证不是会漂移的“随手参考页”？选择：冻结一个只读对照 manifest，所有比较记录都绑定它。
- recommendation/plain_language: 必须冻结；否则 CompanyBrain 一变，今天的“超过”明天就无法复现。
- decision: 对照 manifest 固定为 `companybrain-goinsight-field-filter-20260817-v1`，只读、不写回。入口链路固定为 `Home.md` → `Products/产品索引.md` → `Products/GoInsight/文档总览.md` → `Products/GoInsight/模块手册/模块总览.md` → `Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md`。五个文件的快照身份分别为：`Home.md` 44 行 / sha256 `cac402ccaef6bc55bef765ea93405a6af4c315d35cb68ecca7448249e729be2f`；`Products/产品索引.md` 98 行 / `75e3b641ea4506c67cc4f209b1322a5a0c5381b295243fc0826299e32ae449d7`；`Products/GoInsight/文档总览.md` 25 行 / `0a22821c27352cb31f6c39e7b44e229d54fba82f2f5de0e4e99cd3b2ebe399f9`；`Products/GoInsight/模块手册/模块总览.md` 24 行 / `daea01ef80111682ce15ae79b9accc4251e3889d5dbf154c128e6c31f7448cae`；目标页 `Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md` 166 行 / `9ac850ad9816a422997f99a4564b55ea84dc2834171e7a853bdecbc03c0f4edf`。每条比较记录必须同时绑定 `companybrain_manifest_id`、入口链路版本、目标页相对路径和目标页 hash；对照包内容变化即为新版本，旧结果不与新包混算。
- source_type/reference/exact_excerpt: detail-review repair / `F-bfabd22a311c`、`F-010`、CompanyBrain `Home.md` L22–L43、`Products/产品索引.md` L30、GoInsight 文档/模块入口和目标页。
- approval_binding: 当前只读对照已由 make-decision 冻结，最终确认后下游按 manifest 消费，不复制、不修改 CompanyBrain。
- facts_and_constraints: CompanyBrain 参考页有正式内容和现成入口链路；用户目标是超过原方案，不是重写原方案；对照快照必须和 KnowledgeDigest pilot 一样可复现。
- Logic: 要比较 -> 先固定参照身份 -> 所有题目和轴绑定同一参照 -> 参照变化就新版本/新证据。
- choice_reason/impact: 解决对照漂移，比较结果可审计；影响是以后 CompanyBrain 更新不会自动更新本次结论，必须重新跑对照。
- consequences_and_risks: hash 只能证明快照一致，不能证明 CompanyBrain 本身永远正确；它是基线，不是领域真理。
- rejected_alternatives: 只写目标页路径：内容会漂移；直接引用当前目录：无法复跑；把 CompanyBrain 文件拷贝进候选包：制造第二事实源。
- unresolved_items/owner: 对照 manifest 的实际落盘和执行器读取留给后续规格/计划；manifest 身份与绑定规则已冻结。
- Supersedes: none

### D-014
- question/final_option: 如何保证单一 canonical 页面、完整入口和失败转移真的被验收？选择：增加结构门和状态转移矩阵，不把“从 Home 能点到某页”当全部证明。
- recommendation/plain_language: 推荐；页面必须走规定的产品→模块→主题路径，两个角色看同一页；哪里坏了、能不能重跑、旧结果是否保留，都要有固定答案。
- decision: Reader 结构门固定为：`Home.md` → Reader 根/产品索引 → GoInsight 产品入口 → “字段与筛选”模块入口 → 位置字段筛选 canonical 主题页。允许有既定根索引中间层，但不能跳过产品和模块，也不能从题目外的直接链接起步。主题只允许一个 canonical page identity；其 identity/path 在 TopicIndex/Audit 绑定稳定 `digest_topic_id`/canonical path，Reader 页面可用人类可读标题，不另建角色副本。该页必须同时有且只有一套共享 Claim/Evidence，并包含字面固定的两层标题 `使用/操作层`、`规则/边界层`；两类角色都从该页完成任务。结构门还检查：入口链路每一跳有有效 Reader link；canonical page identity 只有一个；双层都非空；两层引用同一 Claim/Evidence 集合；任何角色专属副本或绕过链路的“直达通过”均失败。
- state_transition_matrix: `manifest_frozen → source_valid/duplicate → claim_evidence_ready → page_published → candidate_not_released` 是唯一正常路径；`source_failed`：不生成该来源 Reader 页、写 Audit failure、候选交付保持 `not_released`、旧 formal 保留，修复后同一内容 hash可用新运行记录重试；若内容/来源变化则先新建 manifest/version/hash。`source_degraded` 或 `claim_evidence_missing`：页为 `degraded`、不进 Reader 导航、写 Audit 原因，候选保持 `not_released`，只能按缺陷修复重跑。`page_published` 但任一必需页/来源失败：允许隔离候选留存已生成页，但不允许交 Reader 当前入口，包仍 `not_released`。`candidate_not_released + reader_gate_failed/undecidable`：停止 pilot、保留题目/答案/失败证据、旧 formal 不变；只有改变实现缺陷后才能重跑受影响门，改变合同/来源必须新版本并重审。`candidate_not_released + reader_gate_passed + strict_comparison_passed`：只记录 pilot continue 并交下一阶段，仍不改成 `released`。`released` 只能由既有 Task 3 正式门产生。任一状态缺少触发证据、可见性证据或恢复身份，均按失败处理。
- source_type/reference/exact_excerpt: detail-review repair / `F-34f3d7f45ed9`、`F-ec9f5ca0c07f`、`D-004`、`D-011`、原始 PRD §6.2/§6.8/§6.9/Task 3、`CONTEXT.md`、ADR 0004。
- approval_binding: 这是对既有 canonical Reader tree、Reader/Audit 分离和状态合同的第一切片验收化，不新增正式状态；最终确认后下游只能展开实现。
- facts_and_constraints: 原始方案已经要求单一 canonical Reader tree、TopicIndex 稳定身份、失败页不进导航和 `released/not_released` 分离；当前 v19 的问题是内容编译和质量门，不是再造一套入口。
- Logic: 读者路径和状态必须能被打破 -> 固定结构、唯一身份、共享证据和转移矩阵 -> 任何绕过/缺证据/不可恢复都失败。
- choice_reason/impact: 直接堵住“页面拆成两份”“跳过模块入口”“半失败仍显示”和“旧 formal 被覆盖”四类风险；影响是下游实现必须保存更多审计字段，但不扩展领域模型。
- consequences_and_risks: 既有 v19 页面可能无法满足 canonical/双层门，需要重新编译候选；这会降低短期通过率，但正是本轮要暴露的根因。
- rejected_alternatives: 只验证 link 不断：无法证明结构；失败页继续挂导航：误导读者；每个角色一页：事实漂移和维护重复。
- unresolved_items/owner: 具体 TopicIndex 字段映射、页面模板和自动检查命令留给后续规格/计划；结构门和状态转移语义已冻结。
- Supersedes: none

### D-015
- question/final_option: 主路径走通后，相关主题、来源入口和失败状态怎么证明读者真的看得见？选择：把这些出口和状态可见性纳入硬门，不能只检查 canonical 页存在。
- recommendation/plain_language: 推荐；读者要能继续查，发布方要能知道哪里坏了、为什么没发布；“没挂链接”或“状态藏在日志里”都算没做好。
- decision: 结构门补充四项：1）位置字段筛选页至少能通过 Reader link 到 `数据分析` 和 `设备位置历史数据集` 两个相关主题，相关主题再回到所属模块入口；缺链、错链或跳到 Audit/raw 快照即失败；2）页面必须有一个短来源入口，指向 Reader 的来源投影，不把 `_digest`、Audit 原文、provider 响应或内部指纹暴露到 Reader；3）候选 `README`/状态索引必须显式显示 `delivery_status=not_released`、阻断原因和对应 run/source/page 标识，Audit manifest 必须同时记录状态、reason、输入 manifest 和恢复路径；4）任一页 `degraded` 时，Reader 导航不出现该页，但候选状态索引必须列出该页和原因；旧 formal 的入口、hash 和路径保持不变，并在验证记录中给出对账结果。状态、原因、可见面和旧 formal 保留证据缺一项，pilot stop。
- source_type/reference/exact_excerpt: detail-review repair / `F-1290384e7dcd`、`F-cb3fbea8c518`、D-006 用户流程、D-014 结构/状态门、原始 PRD Reader/Audit 与失败隔离合同。
- approval_binding: 当前为 make-decision 草案，最终确认后下游按此验收；不新增 Reader/Audit 体系，只把已有用户流程落成硬门。
- facts_and_constraints: 原始方向已要求相关主题、简短来源和失败状态可见；当前 v19 报告只证明链接/泄漏门，不证明读者能继续查或发布方看见失败原因；已有 Reader/Audit 分离不能被破坏。
- Logic: 主入口走通不等于用户完成流程 -> 检查相关主题/来源出口 -> 检查失败状态和原因可见 -> 检查旧 formal 没被动 -> 缺一项就停止。
- choice_reason/impact: 直接覆盖用户流程的后半段和发布方排障，不让“页面存在”冒充“知识可用”；影响是候选包需要有清晰的状态索引，但不把 Audit 变成 Reader 内容。
- consequences_and_risks: 失败候选会更明显地暴露问题，短期看起来更“不完整”；这是预期的 fail-closed 行为，不允许隐藏失败来提高通过率。
- rejected_alternatives: 只检查主链路：用户找到了主题却无法继续查；只把原因写进 Audit：发布方和读者入口看不到状态；把 Audit 直接链接给读者：破坏 Reader/Audit 边界。
- unresolved_items/owner: 状态索引文件的具体名字和自动检查命令留给下游；四项可见性和失败门已冻结。
- Supersedes: none

### D-016
- question/final_option: KnowledgeDigest 与 CompanyBrain 的比较如何避免评测者、顺序和上下文造成假优势？选择：冻结共同评测协议，并让两个包在相同、隔离的执行条件下各跑一次。
- recommendation/plain_language: 推荐；两边必须用同一把尺子、同一组题、同一套规则，而且评测一个包时不能偷偷记住另一个包的答案。
- decision: 固定 `protocol_id=reader-compare-v1`、`prompt_set_id=goinsight-location-reader-gate-v1`、`evaluator_id=reader-evaluator-v1`。S-01/T-01/N-01/N-02 的题目、顺序、Claim checklist、边界 rubric、hop 规则和并列规则对两个包完全相同；同一个 evaluator config/hash 执行两次，每个包单独新建无网络、Reader-only、无 Audit/raw/外部搜索的 session，执行顺序固定为 KnowledgeDigest → CompanyBrain，session 之间不共享上下文；每条记录增加 `protocol_id, prompt_set_id, evaluator_id, evaluator_config_hash, session_id, package_order, isolation_mode`。两边的 manifest、评测协议、题集 hash、运行配置或隔离条件任何一项不一致，比较结果为 `undecidable`，pilot stop；不能换 evaluator、换题或把先看到的答案带入第二包。比较只读取各自 Reader 入口，来源定位由该包允许的 Reader/Audit 证据单独记录，不访问外部网络补事实。
- source_type/reference/exact_excerpt: detail-review repair / `F-842c9ca7ecfb`、D-012、D-013、D-015、原 PRD 的固定题集/Reader-only 读者门原则。
- approval_binding: 这是第一切片对照实验的执行合同，最终确认后由下游固化配置 hash；不改变原 PRD 的正式 Task 2-C/Task 3 评审主体和门槛。
- facts_and_constraints: 用户目标是“比 CompanyBrain 好”，而不是只做自测；同题、同入口、同快照和隔离执行是结果可解释的最低条件；现有正式读者门仍由原任务合同决定。
- Logic: 主观比较容易被上下文污染 -> 固定协议/evaluator/题集 -> 每包独立 session -> 条件不一致直接停止。
- choice_reason/impact: 让三轴差值反映知识结果，而不是评测过程差异；影响是两包至少需要两次隔离运行，不能为了省成本合并上下文。
- consequences_and_risks: 同一 evaluator 仍可能有系统性偏差，因此保留逐条 Claim、来源和原始记录，不能把 evaluator 分数当领域真理；若正式 Task 2-C 要求其他评审主体，继续叠加其既有门，不用本 pilot 替代。
- rejected_alternatives: 两包连续在同一会话评测：会串答案；不同 evaluator 各测一边：比较不公平；运行时允许搜索 Audit/网络：把来源差异和编译质量混在一起。
- unresolved_items/owner: evaluator 实现、prompt/config hash 的实际文件和执行命令留给后续规格/计划；共同协议、隔离、顺序和不一致处理已冻结。
- Supersedes: none

### D-017
- question/final_option: 89 条全量和正式人工评审是延期项，还是当前任务范围？选择：提升为当前范围，但不把“当前范围”误写成“立即发布许可”。
- recommendation/plain_language: 推荐；用户的真实目标就是看 89 条最终产物是否超过 CompanyBrain，继续只做 3 条 pilot 会把核心问题继续往后拖。
- plain_language_meaning: 现在就做完整 89 条产物和正式对照；中途发现失败就如实停在未发布，不再另造一套 pilot-only 流程。
- decision: 当前任务必须覆盖 89 条来源全量编译、全量机器检查、Reader/Audit 分离、CompanyBrain 对照和一次 `17+3` 正式人工确认。89 条来源可合并成少于 89 个 Reader 页面，但每条来源必须在 manifest、snapshot 和 Audit 中可回查。失败来源只进 Audit，核心任务失败时结果保持 `degraded/not_released`。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-simplify` / "好的，继续，之前回答的那些过重的流程改善就删掉吧，太麻烦了"
- approval_binding: 用户已在当前会话确认简化方向；官方 host confirmation ref/hash 待 make-decision publish 重新绑定当前材料。
- facts_and_constraints: 已有 89 条离线/语义候选事实但没有正式 released 包；当前 pilot 只能证明方向值得继续；用户明确要求不要把流程做得过重；原始目标仍是最终结果超过 CompanyBrain。
- Logic: 目标是比较最终 89 条结果 -> 只做 pilot 无法回答 -> 把全量编译和对照放回当前范围 -> 用失败状态和人工结论控制发布，不用额外 pilot 层阻塞结论。
- choice_reason/impact: 直接回答用户最关心的最终产物质量；影响是全量成本和失败暴露提前，但不再维护两套重复验收流程。
- consequences_and_risks: 全量失败可能浪费一次运行成本；批量人工评审不能证明每个页面都被人打开；因此机器必须覆盖全量，人工结论只能代表固定题集和异常复核范围。
- rejected_alternatives: 继续 pilot-only：无法回答 89 条最终结果；89 条逐页人工：成本过高且不是用户要的；多层 pilot/8+3/多重审查：流程过重，不能提高最终比较结论的清晰度。
- unresolved_items/owner: 全量编译命令、批量对照表字段和实际输出目录由 build-spec/build-plan 展开；不得重新改变全量范围、人工方式或比较目标。
- Supersedes: D-001、D-009、DEFER-001、DEFER-002（仅就当前范围与流程，不改写历史证据）。

### D-018
- question/final_option: 正式人工评审如何做到简单？选择：一张批量对照表 + 固定 `17+3` 题，不做 `8+3` 早期门，不逐页检查 89 条。
- recommendation/plain_language: 推荐；人只看一张已经整理好的表，判断最终结果是否更好，不承担翻目录、找来源和逐页抄答案的体力活。
- plain_language_meaning: 机器先把 89 条和两套知识结果整理好；人工集中看 20 行题目对照，必要时只打开异常行的完整页面。
- decision: 批量表至少展示题目、两边答案摘要、首次命中页、路径/跳转、边界要点、来源锚点、机器异常和人工结论。人工结论只允许 `通过/有问题/不确定`；`不确定` 不得自动算通过，需保留为失败或待复核。未被人工查看的来源不得标记 `human_reviewed`。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-simplify` / "你别搞得太麻烦了，我只想确认KnowledgeDigest最终的知识产物质量比CompanyBrain高"
- approval_binding: 用户已确认采用简化人工方式；正式 confirmation fact 待 publish 绑定。
- facts_and_constraints: 原 PRD 的最终题集是 17+3；用户不希望逐条检查；机器、agent_assisted、human_reviewed 不能混写；人工评审表本身尚待实现验证。
- Logic: 人工目标是判断两边谁更好 -> 预先整理对照材料 -> 人工只做最终判断 -> 缺字段或不确定就不能冒充通过。
- choice_reason/impact: 最大限度减少用户操作，同时保留真正人工判断；影响是人工结论是题集级而不是 89 条逐页级。
- consequences_and_risks: 批量表生成错误会影响结论；下游必须先验证表格字段完整，失败时停止正式结论，不用机器结果补写人工结论。
- rejected_alternatives: `8+3` 再 `17+3`：重复；逐页人工：过重；只看总分或模型总结：不是真实人工确认。
- unresolved_items/owner: 表格生成器和实际评分文件由 build-spec/build-plan 实现，评审表字段不能再扩展成复杂工作流。
- Supersedes: D-010、D-012（仅就当前人工评审方式与记录复杂度）。

### D-019
- question/final_option: “超过 CompanyBrain”如何简单判定？选择：只保留三项读者结果对照。
- recommendation/plain_language: 推荐；不再堆几十个门，只看用户最终能不能更快找到、更完整理解、更少被边界误导。
- plain_language_meaning: 比较路径、答案完整度、边界/来源清晰度三件事；至少一项更好，其他不更差，才说超过。
- decision: 固定 `17+3` 题集和同一批量表。三个比较项为：首次找到正确页面的路径、答案完整度、边界与来源清晰度。KnowledgeDigest 至少一项严格优于 CompanyBrain，其他项不变差；关键题错误、负向题误导、无法回查来源或两边条件不一致时，结论为 `not_released`，不以平均分掩盖问题。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-simplify` / "我只想确认KnowledgeDigest最终的知识产物质量比CompanyBrain高"
- approval_binding: 用户已确认目标是最终质量对比，不要求额外流程门；正式 confirmation fact 待 publish 绑定。
- facts_and_constraints: v19 的高代理分数与低读者质量并存；CompanyBrain 有稳定读者路径和边界说明；原始目标是超过 CompanyBrain，不是单独证明结构合法。
- Logic: 需要回答“谁更好” -> 只比较三项读者结果 -> 设一项严格优势且无退化 -> 输出清晰结论和失败原因。
- choice_reason/impact: 结论足够直接，能解释好在哪里；影响是不会把机器完整性、页数、Claim 数等无关指标混进最终质量判断。
- consequences_and_risks: 三项仍不能代表所有领域质量；报告必须写清只对固定题集和 89 条当前产物负责，不宣称永远优于 CompanyBrain。
- rejected_alternatives: 复杂多级 gate：用户不需要且增加执行成本；只看机器分数：已被 v19 事实否定；主观印象：无法复现。
- unresolved_items/owner: 17+3 题集内容复用原 PRD，批量表的落盘和报告格式由下游实现；下游不能增加新的方向门。
- Supersedes: D-007、D-012、D-016（仅就最终质量判定的复杂度；保留同题、同条件和来源可回查底线）。

## 三轮 talk

| talk_id | 问题/选项 | 后果/风险 | 用户选择/原文 | 队列变化 | source/evidence |
| --- | --- | --- | --- | --- | --- |
| T-001 | 第一阶段先全量、只修质量门，还是先做代表性闭环？A/B/C | 用户选择 B：先做一个代表性产品/模块闭环；代价是全量延期，风险是代表性不足 | "B" | OPEN-001 关闭；新增“选择具体代表性切片”问题，进入 research-inputs/Talk Round 2 | `user-reply-2026-08-17-talk-round-1` |
| T-002 | 代表性闭环选 GoInsight 哪个切片？A/B/C | 用户选择 A：字段与筛选；优点是业务对象/规则/操作链路清晰，风险是来源边界容易膨胀 | "A" | 进入 direction advice review；待审查后处理盲点 | `user-reply-2026-08-17-talk-round-2` |
| T-003 | 第一闭环服务哪类读者？A/B/C | 用户选择 C：使用/实施支持人员 + 产品/研发/技术人员；覆盖更全，但页面和验收不能混成泛化正文 | "C" | 进入双角色页面结构问题；FND-004 部分收敛，仍需定义任务和状态行为 | `user-reply-2026-08-17-talk-round-3` |
| T-004 | 两类读者如何进入正文？A/B/C | 用户选择 A：同一主题、同页双层；维护简单，但页面长度和层次风险上升 | "A" | 新增“角色任务与通过条件”问题 | `user-reply-2026-08-17-talk-round-3-page-structure` |
| T-005 | 双层页面如何验收？A/B/C | 用户选择 A：同一个真实场景按两种角色验收；范围可控，但具体场景必须真实且有边界 | "A" | 新增“锁定具体真实场景”问题 | `user-reply-2026-08-17-talk-round-3-task-shape` |
| T-006 | 具体场景和验收细节是否继续逐项询问？ | 用户授权 make-decision 自行决定；继续拆问的收益低，且会偏离“让结果超过 CompanyBrain”的核心 | "A；这些验收细节没必要问的这么详细，你自己可以决定，当前的核心还是如何修改KnowledgeDigest能让最终产物质量比原来的companybrain高！" | 由 D-006–D-008 冻结位置字段筛选场景、CompanyBrain 对照标准、来源 manifest、停止/回滚边界；Talk Round 3 收束 | `user-reply-2026-08-17-detail-delegation` |

## 调研

| research_id/source | 调研重点 | 关键事实 | 处理状态 | 关联 D |
| --- | --- | --- | --- | --- |
| F-001 / v19 projection + quality + release summary | 真实产物是否达到读者质量 | 89 条来源、88 条有效逻辑条目、104 个 Reader 页、40 条 `fidelity_only`、41 条失败；代理分数 99.78 通过，但交付仍 `not_released`，未完成人工读者门。 | 已核实，作为 Talk 输入，不当作最终方向 | R-001 |
| F-002 / `comparison/ROOT-CAUSE.md` | 当前结果根因 | 结构、链接和保真度门能通过，但没有把“来源完整”与“知识可用”区分；产品/模块主轴、正文消化和失败隔离不足。 | 已核实，待 Talk 选择修复顺序 | R-001 |
| F-003 / `docs/plans/knowledge-digest-knowledge-publication-prd.md` | 原始方案对下一步的约束 | 原方案明确要求 Structure Normalizer、ProductGazetteer/TopicIndex、Typed Page Compiler、按语义边界拆分、Reader/Audit 分离、页级 `published/degraded`、包级 `released/not_released` 和真实读者门。 | 已核实，不能被当前 v19 的代理分数覆盖 | R-001 |
| F-004 / CompanyBrain GoInsight compilation plan | 参照方案为什么更可读 | 先建业务对象和任务主轴，再决定页面；页面围绕一个稳定对象/任务，区分产品、模块、操作/规范、架构/经验等正文结构，并保留 compile review。 | 已核实，只借鉴方法，不复制规模 | R-001 |
| F-005 / `docs/research/knowledge-publication-quality-external-20260817.md` | 外部知识发布与读者质量方法 | 已整理 Confluence 层级/版本、受管词表、原子事实与证据、事实一致性评估、引用可验证性和读者任务评估方法；支持先小范围冻结结构、再用读者任务验证后扩展。 | 已作为 B 的研究输入；具体切片仍待 Talk Round 2 | D-001 |
| F-006 / CompanyBrain GoInsight compilation plan §下一步执行 | 代表性切片选择 | 方案明确建议先处理一个模块，从“字段与筛选”开始；理由是业务对象、规则边界和操作链路较清楚，并要求先生成结构方案、再评估页面划分、最后生成 3–5 个候选页。 | 已核实，作为下一轮选项依据，不替用户决定 | D-001 |
| F-007 / 原始 GoInsight 语料清单 | 代表性切片是否有真实覆盖 | 原始目录含 `数据分析.md`、`位置字段筛选.md`、`指标详情页.md`、`添加指标页.md`、`添加关联数据.md`、`累计计算.md` 等可形成字段/筛选/指标关系的来源；不是单一孤立文档。 | 已核实，候选切片可做；范围和题集待定 | D-001 |
| F-008 / Talk Round 2 用户选择 | 代表性切片最终选择 | 用户选择 A：GoInsight“字段与筛选”；该选择进入独立方向建议，不等于最终 make-decision 确认。 | 已记录，待 direction advice review | D-002 |
| F-009 / v19 位置字段筛选页 | 页级现状 | `/Users/Hugh/Downloads/KnowledgeDigest-real-reader-quality-20260814-v19/bundle/products/goinsight/modules/data-and-analytics/knowledge/位置字段筛选.md` 已保留区域内/区域外、3–100 点、不相交/不穿越、拖入筛选栏和百万终端性能等事实，但正文仍是固定“摘要/详细内容/来源”包装，缺少“什么时候查、排查、相关页”阅读路径。 | 已核实，作为对照基线，不当作通过 | D-006、D-007 |
| F-010 / CompanyBrain 位置字段参考页 | 页级优势 | `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/模块手册/字段与筛选/文本、数值与位置筛选.md` 组织了何时查、文本/数值/位置筛选、规则边界、排查、相关页和来源索引；它是同场景对照对象，不是写入目标。 | 已核实，作为严格对照 | D-006、D-007 |
| F-011 / 原始位置筛选与位置历史数据集 | 真实任务与边界 | `位置字段筛选.md` 提供区域筛选操作和限制；`数据分析.md` 提供入口/筛选上下文；`设备位置历史数据集.md` 提供设备轨迹、位置变化、默认字段和复杂筛选问题，可组成“操作 + 规则/技术”闭环。 | 已核实，冻结第一轮来源依据 | D-006、D-008 |
| F-012 / `goinsight-location-pilot-20260817-v1` | 来源可复现身份 | 三份 primary source 已绑定相对路径、行数和内容 hash：`数据分析.md` 54 行 / `52abb4c14c9beb1f0752bb6c50a8da9bef225237fc46e76f5f9c471e87c42668`；`位置字段筛选.md` 72 行 / `32b3c01b03a44727c6a692e9b10e3ee71106abec1f90c45272cbd75c9bce32b1`；`设备位置历史数据集.md` 44 行 / `39b5bf52e177319239ebe6afb1df037163b6e567ef2ae2752bc46b3bab739cb6`。 | 已冻结；内容变化或扩源必须新建 manifest/version | D-008、D-011 |
| F-013 / detail review `b88117d7-e826-49af-bac2-454de60e9069` | 方向草案的交付缺口 | 有效 provider `codex/luna` 返回 3 个 major finding：题目/预期输出/对照记录不够具体；状态只有词汇没有转移行为；manifest 只有文件名没有不可变身份。`opencode/v4flash` 为 `SESSION_IDLE_WITHOUT_TERMINAL`，`antigravity/flash` 为 `ATTACHMENT_DELIVERY_UNSUPPORTED`，因此 coverage 为 partial。 | finding 已按 D-010/D-011 修复；transport partial 作为 accepted risk 保留，不重复调用 unchanged review | D-010、D-011 |
| F-014 / detail re-review `ce48377e-2c51-47bf-b990-733b10b2476b` | 修复后剩余交付缺口 | 有效 provider `codex/luna` 又指出两点：CompanyBrain 三轴对照缺少可复现评分/起点/并列规则；“关键事实 100%”没有绑定有限 checklist 和逐条锚点。`opencode/v4flash`、`antigravity/flash` 的 transport 仍分别失败。 | finding 已按 D-012 修复；重复 transport 作为 accepted risk 保留 | D-012 |
| F-015 / detail re-review `bd8da977-5be2-4111-8f76-6879ab62c726` | 修复后剩余交付缺口 | 有效 provider `codex/luna` 又指出四点：CompanyBrain 对照包没有 manifest 身份；路径轴缺确定性排序；结构门没有约束唯一 canonical/双层/入口；状态叙述还不是可执行矩阵。两路异源 transport 继续失败。 | finding 已按 D-013/D-014 修复；transport partial 保留 | D-013、D-014 |
| F-016 / detail re-review `429d797c-575c-4800-9fa7-ef4306163a87` | 最后收口检查 | 有效 provider `codex/luna` 指出：确认仍 pending；验收缺相关主题/来源出口与 Reader/Audit 边界；失败原因和状态可见性未纳入硬门；两包评测未冻结共同 evaluator/protocol/隔离。两路异源 transport 继续失败。 | 前三项已按 D-015/D-016 修复；确认项保留为 needs_human，等待用户最终确认 | D-015、D-016、最终确认 |

## grill

| grill_id | CONTEXT/冲突 | 结论 | ADR/四项退出 | source/evidence |
| --- | --- | --- | --- | --- |
| G-001 | 已检查 `CONTEXT.md`、ADR 0004/0007/0008、原始 PRD 与 `reader_compiler.py`。现有术语和失败语义与 D-003–D-009 一致；代码事实也印证当前问题集中在关键词归类、固定摘要/正文包装、`fidelity_only` 仍可形成 Reader 页和偏宽的质量代理，而不是需要另造一套知识域模型。唯一需要钉死的边界是 pilot 不能放宽原 PRD 的正式 8+3/17+3 读者门。 | completed；方向改变点已解决：同一 canonical 主题页双层、位置字段筛选共同场景、CompanyBrain 严格对照、三份最小来源、失败即停止且不发布；D-009 保留既有正式门 | CONTEXT：no-change，沿用 Claim/Reader/Audit/TopicIndex/`published`/`degraded`/`released`/`not_released`；ADR：not-needed，本轮是隔离、可回滚的 pilot，不锁定新的跨项目架构；退出：上下文一致、owner/接口可交接、失败语义明确、范围/延期明确均 passed | `CONTEXT.md`、`docs/adr/0004-reader-publication-separate-from-audit.md`、`docs/adr/0007-task2c-agent-reader-gate.md`、`docs/adr/0008-task3-summary-confirmation-release-gate.md`、`docs/plans/knowledge-digest-knowledge-publication-prd.md`、`src/knowledge_digest/reader_compiler.py` |

## 决策草案（Grill 后，历史版本；已被 D-017～D-019 supersede）

用大白话说：KnowledgeDigest 这次不再把“原文都保住、页面都写出来”当成成功，而是先证明它能帮人解决一个具体问题。第一条闭环就是 GoInsight 的“位置字段筛选”：一个市场管理员/支持人员要按区域找设备；同一页先告诉他怎么操作，再告诉产品/研发人员这条筛选到底适用于哪里、有哪些硬限制、哪里不能用。

- 用户流程：打开 Reader `Home` → 进入 GoInsight → 进入“字段与筛选”模块 → 打开“位置字段筛选”主题页 → 在“使用/操作层”完成区域内/区域外筛选 → 在“规则/边界层”核对数据分析入口、点数/绘制/性能限制和不适用场景 → 需要时从相关主题和简短来源入口继续查；失败页或候选包必须明确显示 `degraded/not_released`，不能把半成品当正常知识。
- Reader 页面范围：`Home`、产品入口、模块入口、一个稳定 canonical 主题页、相关主题入口和简短来源入口。Audit 范围：三份冻结来源、Claim/Evidence/Provenance、来源指纹、运行清单和失败原因。Audit 不能反过来成为读者入口。
- 数据状态：来源保持 `valid/duplicate/failed/degraded`；页只用 `published/degraded`；候选包和交付分别保持 `candidate` 与 `released/not_released`；机器、Agent 辅助和人工/汇总确认分开记录。
- 通过条件：两类角色都能从 Reader 入口完成各自任务；关键事实、限制、反例和来源定位完整；没有占位摘要、原文堆放或 `fidelity_only` canonical 页；导航可达；与 CompanyBrain 同场景参考页相比，至少在任务路径、答案完整度或边界/排查清晰度上有可观察优势，并且不牺牲正确性、溯源和失败诚实性。
- 失败条件：任一角色任务答不出来、负向边界误导、关键事实丢失/矛盾、来源无法回查、页面仍是 fallback 堆放、导航不可达或 provider/编译失败时，候选保持 `degraded/not_released`，隔离保存，不覆盖旧 formal，不扩大来源清单。
- 最小读者题：支持人员回答“在数据分析里按区域筛设备怎么做、Inside/Outside 怎么选、画区提交前有什么限制”；技术人员回答“为什么只在数据分析页支持、设备位置历史数据集如何作为验证上下文、报告计算指标为何不是普通位置筛选”；两道负向题必须明确拒绝数据集详情/全局筛选位置条件，以及拒绝把报告计算指标当普通位置筛选。每题保存首次命中页、跳转、答案要点、来源定位和失败原因，并用同题同格式对照 CompanyBrain。
- 最小读者题：支持人员回答“在数据分析里按区域筛设备怎么做、Inside/Outside 怎么选、画区提交前有什么限制”；技术人员回答“为什么只在数据分析页支持、设备位置历史数据集如何作为验证上下文、报告计算指标为何不是普通位置筛选”；两道负向题必须明确拒绝数据集详情/全局筛选位置条件，以及拒绝把报告计算指标当普通位置筛选。每题保存首次命中页、跳转、答案要点、来源定位和失败原因，并用同题同格式对照 CompanyBrain。
- Claim 与对照公式：固定 `CL-S01-*`、`CL-T01-*`、`CL-N01-*`、`CL-N02-*` checklist；正向题逐条通过率必须 100%，负向题必须 1/1 且无相反建议。两个包都从各自 Home 开始，一次 Reader link 算一次 hop；路径轴比较 first-hit/hop，答案轴比较 checklist 通过率，边界轴按四项固定检查计分。三个轴计算 `KnowledgeDigest - CompanyBrain`，至少一个严格为正、没有一个为负，缺证据/并列/无法判定都停止。
- 严格对照：硬门全部通过后，首个相关页/跳转路径、答案完整度、边界与排查清晰度三个轴至少一个严格优于 CompanyBrain，另外两个不差；没有严格优势或有任一退化就停止 pilot。
- 对照身份：CompanyBrain 不是动态目录，而是冻结的 `companybrain-goinsight-field-filter-20260817-v1`，固定 Home→产品索引→GoInsight 文档总览→模块总览→目标页的入口链路和五个文件 hash；比较记录必须绑定该 manifest。
- 结构门：KnowledgeDigest 必须从 Home 经产品入口和“字段与筛选”模块入口到唯一 canonical“位置字段筛选”主题页；同一页同时包含“使用/操作层”和“规则/边界层”，两层共享同一 Claim/Evidence，不允许角色副本或绕过入口直达通过。
- 出口与状态可见：位置页必须能链接到 `数据分析` 和 `设备位置历史数据集` 相关主题，并有短来源入口；Reader 不得链接 Audit/raw/provider 内容。候选状态索引/README 必须显示 `not_released`、阻断原因、run/source/page 标识，degraded 页不进 Reader 导航但必须在候选状态索引和 Audit 中可见；旧 formal 路径/hash 必须对账不变。
- 评测隔离：固定 `reader-compare-v1`、`goinsight-location-reader-gate-v1`、`reader-evaluator-v1`；两个包用同一 evaluator config、同题同序、独立无网络 Reader-only session，先 KD 后 CompanyBrain，禁止跨包记忆；协议、题集、evaluator、manifest 或隔离条件不一致，比较无效并停止。
- 状态转移：来源 `valid/duplicate` 才能进入 Claim/Evidence；`failed/degraded` 只进 Audit；页只有必需证据、可回查、无 fallback 且导航通过才是 `published`，否则 `degraded` 且不进导航；候选编译完成仍是 `candidate/not_released`，任何必需来源或读者门失败都不覆盖旧 formal；正式 `released` 仍只由既有 Task 3 门产生。来源变化必须新建 manifest/version 和 hash，不能隐式扩源或续跑旧清单。
- 非目标：本轮不重编译 89 条全量、不覆盖 CompanyBrain、不先做 UI 重绘、不复制 CompanyBrain 的人工文件规模、不加入数据库/向量库/调度器、不降低原 PRD 的正式读者门、不让 build-spec 补方向需求。
- 延期交接：下游只补实现所需的字段、接口、题目、命令和证据路径，不得重新决定读者、场景、来源边界、状态语义或比较标准；第一切片通过后，另行决定如何扩展到多产品/多 page type 和全量题集。

## Talk/Grill 修订结论

| source_id | 用户选择/结论 | 影响 |
| --- | --- | --- |
| T-007 | 全量完成定义选 A：89 条来源全部进入 Reader/Audit 包，Reader 按主题合并，不强制 89 页 | 当前范围从 pilot 扩到全量，但不制造碎片页 |
| T-008 | 人工评审选 A：一页式批量评审表，机器全量检查，人工看固定题和异常 | 删除逐页检查和重复人工门 |
| T-009 | 分层覆盖选 A：机器覆盖 89 条，人工覆盖固定题和机器异常 | 未人工查看的来源不标 `human_reviewed` |
| T-010 | Grill 选 A：局部失败允许保留可用内容；影响核心任务时整包 `not_released` | 失败透明，不用一条无关坏数据拖住全部内容，也不把核心错误放行 |
| T-011 | Grill 选 A：人工“不确定”不能自动通过；CompanyBrain 无对应内容标 `N/A` | 不制造假通过、假优势或假劣势 |
| T-012 | Grill 选 A：只保留路径、答案完整度、边界/来源清晰度三项比较 | 删除与最终读者质量无关的复杂指标 |
| T-013 | 用户修订确认：删除过重流程，目标只保留“最终 89 条产物质量高于 CompanyBrain” | supersede 旧 pilot-only、多层门禁和逐来源人工方案 |

## 当前生效决策草案（简化版）

这次只解决一个问题：89 条最终知识产物，是否比 CompanyBrain 更好。

- 用户流程：打开 KnowledgeDigest 的 Reader 入口，按产品/模块找到知识页，完成固定 `17+3` 个真实问题；批量对照表同时展示 CompanyBrain 的对应结果。
- 页面范围：89 条来源全部纳入编译和 Audit；Reader 页面按产品、模块、任务合并，不要求一条来源一页；Reader 不展示原文堆放、机器字段或 Audit 细节。
- 机器检查：全量检查来源是否进入 manifest/Audit、页面是否可达、正文是否为空或占位、来源是否可回查、Reader/Audit 是否混杂、失败原因是否可见。
- 最小失败规则：编译失败、无法归类、没有可回查来源、正文为空/占位、导航不可达，或关键质量检查失败，就不进 Reader，只保留 Audit；Audit 至少保留来源唯一 ID、原始快照、运行记录和失败原因，能够重放“这条来源发生了什么”。
- 人工检查：只看一张批量表中的 `17+3` 题；表格自动提供两边答案、首次命中、跳转、边界和来源锚点。只有异常行需要打开完整页面；不逐页检查 89 条。
- 人工不确定：只处理该异常行；补看表中已给出的页面/来源后仍不确定，就按“有问题”处理，不得自动通过。
- 成功：KnowledgeDigest 在路径、答案完整度、边界/来源清晰度三项中至少一项严格优于 CompanyBrain，另外两项不变差；关键任务没有错误，来源能回查。
- 三项计算：路径看首次命中正确页面和跳转数；答案看固定答案要点通过率；边界/来源看固定限制是否说对且能回查来源。至少一项严格更好、其他不差；任一关键错误或缺证据直接失败。
- 根因记录：对每个主要差距记录“现象、来源/页面证据、根因、修正动作、复核结果”；根因没有证据时只记为未确认，不当作结论。
- 失败：批量表缺字段、人工出现不确定、关键任务答错、负向题误导、来源无法回查、Reader/Audit 混杂或全量运行失败时，结果保持 `degraded/not_released`。
- 非目标：不做 UI 美化，不复制 CompanyBrain 的文件数量和人工脚本，不引入数据库/向量库/调度器，不增加 8+3 早期门，不建立永久人工队列，不让 build-spec 重新决定方向。
- 延期交接：下游只补编译器、批量表、报告的实现字段和命令；不得把 89 条重新缩回 pilot，不得把人工评审改成逐页检查，不得用机器结果冒充人工结果。

## 本轮方向审查处置（2026-08-18）

方向审查结果为 `available`，当前结果：`quality/reviews/results/make-decision-direction-0f14ceb5c31a3569d63cf10ec1f1c2635af6f88f-6fae98ee-b2bf-4182-af5f-fe9d0ea45420.json`。审查提出的“全量范围与未发布 pilot 混淆、比较标准不足、批量表未验证、Reader/Audit 与评审状态边界不清”等意见已按 D-017～D-019 修正：

| finding_id | 处置 | 后续动作 |
| --- | --- | --- |
| F-4da6e1dfd5bd、F-d20f520d0c3d、F-ee581f9a9ed3 | fixed | 当前范围与发布结果分开；89 条进入本任务，不以当前未发布候选冒充正式发布 |
| F-d6c280e027a5、F-2da30c54740d、F-c67938a4c159 | fixed | 用固定 17+3 和三项读者结果判定“超过” |
| F-7e69010e7cbe、F-afd364adeac4 | fixed | 删除 8+3 早期门；人工只做一次 17+3 批量评审 |
| F-51a5ad94a6a0、F-63bb7bba0612、F-a03fd46743cd | fixed | 明确 Reader/Audit 分离；未人工查看的来源不标 human_reviewed |
| F-99a83067a064、F-d5a6b1eb78e5、F-df9a4da5240d | fixed | 已把批量表和全量机器检查列为下游必须验证的实现项；缺字段或失败时不形成正式质量结论 |

以上记录保留审查原始事实，不把审查意见改写成通过结论。

## 本轮细节审查处置（2026-08-18）

细节审查结果为 `available`，当前结果：`quality/reviews/results/make-decision-detail-1734235cf8c63ebf6d6d912c688c860453563685-e848d2be-410a-4513-bdf2-1145392e4c3d.json`。审查提出的状态、回放、三项比较和根因记录缺口，已用最小规则补齐；没有恢复旧的复杂门禁。

| finding_id | 处置 | 后续动作 |
| --- | --- | --- |
| F-0dc9d40ee16d、F-85e746aa6f70、F-e18bb8a7a8e6、F-191b41ee243、F-60c91c15dd45 | fixed | 用最小失败规则、来源唯一 ID、原始快照、运行记录和失败原因定义 Reader/Audit 资格与 Audit 回放 |
| F-ad948d712246 | fixed | 人工不确定只复核异常行，复核后仍不确定按有问题处理 |
| F-b8cc1a22db1f、F-f4a972b3eda6 | fixed | 路径、答案完整度、边界/来源清晰度各有固定字段；一项严格更好且其他不差才算超过 |
| F-bb7884854779 | fixed | 每个主要差距记录现象、证据、根因、修正动作和复核结果；无证据只记未确认 |
| F-ee14b028c04d | fixed | 明确当前阶段只定方向；下游只补实现字段、命令和证据路径 |

以上处置是轻量补充，不新增独立状态机、人工队列或额外发布门。

## 审查处置

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| FND-001 | direction review 启动前没有本任务审查结果；该事实已被当前审查记录取代 | 不能把旧的“无结果”当成当前审查结论 | fixed | 当前结果：`quality/reviews/results/make-decision-direction-8304c49e5852fe6b0752ba5c502e4228c2076186-7bac9723-4869-4198-b62c-43a96f0df082.json`；保留历史事实 | make-decision / 保留历史，不作当前结论 |
| FND-002 | 独立 direction review `F-3705d384e7c6`：缺少“超过 CompanyBrain”的可判定标准 | 无法判断何时真的比原方案好，容易再次用机器分数代替读者质量 | fixed | D-007 已定义硬正确性/溯源/导航底线和相对 CompanyBrain 的任务路径、答案完整度、边界/排查优势；精确题目与记录格式留给后续规格/验证；保留 finding | make-decision / detail review、verify-code / 保留 |
| FND-003 | 独立 direction review `F-61345fe1623d`：根因只有聚合计数和概括，缺少页面/来源/任务级证据 | 可能把推断当根因，修错地方 | fixed | F-009–F-011 已绑定 v19 页面、CompanyBrain 参考页和原始来源/任务；D-006–D-007 明确事实、读者任务和对照关系；后续仍需把证据落到候选页和验证记录 | make-decision / detail review、后续 spec/verify / 保留 |
| FND-004 | 独立 direction review `F-dd6cc004b03b`：目标读者、核心任务、页面纳入规则和状态转移后的行为未定义 | 用户流程、页面范围和失败边界仍不能验收 | fixed | D-003–D-006 已定义双角色、同页双层、共同场景；D-008 已定义初始 manifest、排除项、Reader/Audit 边界和 `degraded/not_released` 行为 | make-decision / detail review、下游消费 / 保留 |
| FND-005 | 独立 direction review `F-ac5c71b0a9db`：小语料没有可逆边界 | 试验失败后无法判断停止、回滚或扩大范围 | fixed | D-008 已冻结三份 primary source、隔离候选包、硬失败停止、不覆盖和不扩张门槛；精确指纹与自动化步骤留给后续规格/计划 | make-decision / build-plan、verify-code / 保留 |
| FND-006 | direction review 传输事实：3 个请求配置中仅 `codex/luna` 返回有效 finding；`opencode/v4flash` 为 `SESSION_IDLE_WITHOUT_TERMINAL`，`antigravity/flash` 为 `ATTACHMENT_DELIVERY_UNSUPPORTED` | 这是 partial review，不是 pass，也不是空 findings | accepted_risk | 不重复调用 unchanged review；保留真实 transport/result/report，继续同任务处理 finding | make-decision / 审查事实消费者 / 保留 |
| FND-007 | detail review `F-3ce2a6fea450`：验收草案没有技术/研发任务、正负题、预期答案、来源锚点、对照执行、记录格式和停止阈值 | 不能判断双角色任务完成，也不能证明超过 CompanyBrain | fixed | D-010 已冻结 S-01/T-01/N-01/N-02、预期输出、来源范围、同题同格式记录和“硬门 + 至少一轴严格更优且无退化”的停止规则 | make-decision / spec-analyze、下游实现验证 / 保留 |
| FND-008 | detail review `F-91b4abb75315`：primary source 只有文件名，没有稳定路径、版本/快照/hash 或受控扩源规则 | 同一 pilot 的输入可能漂移，结果无法复现 | fixed | D-008、D-011、F-012 已冻结 manifest id、相对路径、行数、sha256、排除项和“扩源必须新版本并重审”规则 | make-decision / build-spec、build-plan / 保留 |
| FND-009 | detail review `F-984df3be9a30`：数据状态只有词汇，没有部分失败、可见性、恢复和旧 formal 保留行为 | 失败时不知道哪些页能看、何时重试，容易把半成品当成功 | fixed | D-011 和决策草案已给出来源→Claim/Evidence→页→候选/交付的进入条件、Reader/Audit 可见性、必需来源失败阻断、重跑和回滚规则 | make-decision / spec-analyze、下游实现验证 / 保留 |
| FND-010 | detail review transport：仅 `codex/luna` 有语义结果；`opencode/v4flash` 为 `SESSION_IDLE_WITHOUT_TERMINAL`，`antigravity/flash` 为 `ATTACHMENT_DELIVERY_UNSUPPORTED` | detail review coverage partial，不能写成多 provider 一致通过 | accepted_risk | 两次 detail attempt `b88117d7-e826-49af-bac2-454de60e9069`、`ce48377e-2c51-47bf-b990-733b10b2476b` 均保留 attempt/result/report、provider 身份和真实诊断；不再重复 unchanged transport；最终结论只依赖有效 finding 已修复和 spec-analyze，不声称全 provider clean | make-decision / 审查事实消费者 / 保留 |
| FND-011 | detail re-review `F-7e68c59ad1fb`：CompanyBrain 三轴对照不可复现，缺评分公式、起点、跳转计数和并列处理 | “超过 CompanyBrain”仍可能靠主观判断 | fixed | D-012 冻结各自 Home 起点、hop 定义、三轴计算、严格/并列/不可判定规则和记录字段 | make-decision / spec-analyze、verify-code / 保留 |
| FND-012 | detail re-review `F-b0cc37e256bb`：关键事实 100% 未绑定有限 checklist 和逐条来源锚点 | 验收者可随意扩大或缩小事实范围，无法复现 | fixed | D-012 冻结 CL-S01/CL-T01/CL-N01/CL-N02 checklist、允许方向、manifest/path/line/hash 锚点和 100%/1-of-1 规则 | make-decision / spec-analyze、verify-code / 保留 |
| FND-013 | detail re-review `F-bfabd22a311c`：CompanyBrain 对照包没有冻结不可变身份 | 对照变化后不能稳定复跑，比较结果失去基线 | fixed | D-013 冻结 `companybrain-goinsight-field-filter-20260817-v1`、Home/产品/模块/目标页链路、五个文件 hash 和记录绑定字段 | make-decision / spec-analyze、verify-code / 保留 |
| FND-014 | detail re-review `F-b8547fac07ef`：路径比较轴没有确定性排序、差值、并列和无命中处理 | 无法判定“严格更好” | fixed | D-012 已定义 `route_rank=(reachable, first_hit_kind, -hop_count)` 字典序、route_delta sign、无命中/缺证据 stop | make-decision / spec-analyze、verify-code / 保留 |
| FND-015 | detail re-review `F-34f3d7f45ed9`：验收没有约束唯一 canonical 主题页、双层正文和完整入口链路 | 分页/复制页/绕过入口可能伪通过 | fixed | D-014 冻结 Home→产品→模块→canonical 路径、唯一 identity、共享 Claim/Evidence、双层标题和禁止角色副本 | make-decision / spec-analyze、verify-code / 保留 |
| FND-016 | detail re-review `F-ec9f5ca0c07f`：状态合同没有可执行的部分失败转移矩阵 | 失败可见性、阻断、重跑和旧 formal 保留仍可能被实现者猜测 | fixed | D-014 给出 manifest/source/page/candidate/released 的正常与失败转移、可见性、阻断、重跑和新版本条件 | make-decision / spec-analyze、verify-code / 保留 |
| FND-017 | detail re-review `F-1290384e7dcd`：验收没有覆盖相关主题、简短来源入口和 Reader/Audit 分离 | 主页面可过，但读者无法继续查或回溯来源 | fixed | D-015 已把两个相关主题、短来源投影、禁止 Audit/raw/provider 链接和双向入口纳入硬门 | make-decision / spec-analyze、verify-code / 保留 |
| FND-018 | detail re-review `F-cb3fbea8c518`：失败状态和原因没有要求对用户/发布方可见 | 候选可能静默消失，验收仍误判通过 | fixed | D-015 已要求候选 README/状态索引显示 not_released、reason、run/source/page 标识，Audit 记录恢复路径，旧 formal 对账 | make-decision / spec-analyze、verify-code / 保留 |
| FND-019 | detail re-review `F-842c9ca7ecfb`：两包比较没有冻结共同 evaluator、协议、顺序和上下文隔离 | 答案完整度/边界清晰度可能被评测条件制造 | fixed | D-016 已冻结 protocol/prompt/evaluator identity、同 config、固定顺序、fresh Reader-only session、无跨包记忆和条件不一致 stop | make-decision / spec-analyze、verify-code / 保留 |
| FND-020 | detail re-review `F-a344a43553c1`：最终用户确认仍 pending | make-decision 不能完成，也不能安全交给下游 | fixed | 用户已回复“好的，继续吧”，接受当前方向；已写入最终确认并准备发布 interaction aggregate | 用户 / make-decision publish / 保留 |

## Stage-end spec-analyze 结果（历史版本；当前修订后需重跑）

- 官方 stage-end `spec-analyze` 已执行两次；第一次只发现 analyzer packet 对 R-002 的实际语义描述夹带额外否定词，属于分析包表达问题，不是产品方向问题。
- 第二次复跑已修正该表达，并绑定当前 `decision-log.md`、当前 snapshot、当前 evidence 和当前审查处置：`quality/evidence/stage-outcomes/make-decision/6fbe4863d5fead11b20f908749f5f1f44a877871ec62fc3f3329fe3b6811390a.json`。
- 结果：`consistent`；4/4 条原始需求有语义和证据绑定；0 条 semantic mismatch；0 条 stale evidence；0 条未解释的一致性问题。
- 上述结果绑定的是旧 pilot 方向，不能直接证明当前简化版决策一致；当前修订后必须重新绑定当前材料、interaction aggregate 和 confirmation。

## 最终确认

- 状态：accepted
- 用户原文与 host-visible 绑定：`好的，继续吧`；该回复承接上一轮方案说明，表示接受当前开发方向并继续标准 WorkflowHub 流程。
- 已确认内容：先做 GoInsight“字段与筛选”的位置筛选语义编译闭环；同一 canonical 页面分使用/操作层和规则/边界层；用冻结版 CompanyBrain 做同题对照；失败保持 degraded/not_released；不跳阶段、不让 build-spec 补方向需求。
- 风险接受：接受先做代表性 pilot、provider transport partial 保留为真实风险、全量 89 条和正式推广延期；不把 pilot 结果直接称为全库 release。

### 修订确认（2026-08-18）

- 状态：accepted_pending_runtime_binding
- 用户原文："好的，继续，之前回答的那些过重的流程改善就删掉吧，太麻烦了"
- 当前确认内容：89 条全量和正式人工评审回到当前范围；只做一次 `17+3` 批量人工对照；机器覆盖全量；最终只比较路径、答案完整度、边界/来源清晰度；删除 `8+3` 早期门、逐页人工、复杂多层审查和无关状态门。
- supersedes：D-017～D-019 覆盖旧的 pilot-only、8+3 早期门、逐来源人工状态和多层比较流程；历史记录保留，不改写旧证据。
- 风险接受：接受全量运行可能失败、人工不逐页确认 89 条、部分来源可能 degraded；失败必须保留证据并保持 `not_released`。
- 延期交接：build-spec 只能把已确认方向写成可实现规格，补接口、字段、命令和测试步骤，不能重新决定读者、场景、来源边界、状态语义或比较标准。

## 拒绝方案

| 选项 | 拒绝理由 | 关联 D |
| --- | --- | --- |
| 直接进入 build-spec | 违反用户“不依赖 build-spec 补需求” | D-000 |
| 直接改代码再看效果 | 会把方向歧义和错误质量门带进实现 | D-000 |
| 继续用 99.78 代理分数代表读者质量 | 与 40 条 fidelity-only、41 条失败和未发布状态冲突 | R-001/F-001 |

## 风险与延期交接

> 下表保留旧 pilot 方向的历史记录。当前全量范围下，89 条全量编译和正式 `17+3` 人工对照已从延期项提升为当前范围；当前交接只保留实现字段、命令、测试和证据路径。

| risk/deferred_id | 风险或延期内容 | 触发/后果 | 处理阶段/owner |
| --- | --- | --- | --- |
| RISK-001 | 优化范围过大，重新承担主题探索、正文编译和全量发布 | 成本高、失败难定位、容易再次得到“跑完但不好读” | 已通过 D-001 先收窄；后续仍需防止代表性切片膨胀 |
| RISK-002 | 产品/模块/业务对象无法确认 | 自动猜测会制造假目录和错误归属 | 方向确认后冻结词典/冲突策略；make-decision → build-spec |
| RISK-003 | provider 截断或语义 fallback | 页面可能退回原文堆放，读者质量不成立 | 后续实现和验证；保持 degraded/not_released |
| DEFER-001 | 真实 89 条全量重编译、预算和重放策略 | 代表性闭环未通过前不能承诺全量 release | build-plan/build-code/verify-code |
| DEFER-002 | 正式全量读者题集、评审主体独立性和最终对比报告 | 第一切片只冻结最小 2 正向 + 2 负向题；正式 8+3/17+3 题集仍受原 PRD 约束 | 后续 Task 2-C/Task 3 / build-spec、verify-code |

## 质量边界

- 质量事实：当前 v19 的来源数、失败数、`fidelity_only`、页面数、代理分数、`not_released` 和 CompanyBrain 对照是事实；不把它们自动升级为完成资格。
- 推进资格：Talk、调研、Grill、方向审查、detail 审查、stage-end spec-analyze 和用户最终确认已产生可消费事实；make-decision 可由官方 runtime 重新绑定后发布，下一阶段只能消费本日志。
- 完成判据：Talk/必要调研/方向审查/Grill/决策日志/细节审查/用户确认/不可变交互聚合全部完成后，才可结束 make-decision；当前先补齐 interaction aggregate 并执行官方发布。
- 不可逆授权边界：当前没有 commit、merge、push、archive、cleanup 授权，也没有正式发布授权。

## 未决项

| item_id | 未决内容 | 原因 | 谁在何时解决 |
| --- | --- | --- | --- |
| OPEN-001 | 第一阶段先做全量质量合同，还是先做一个代表性产品/模块闭环 | 已由用户选择 B 解决：先做代表性闭环 | 已解决，关联 D-001 |
| OPEN-002 | Reader 页面最小必需正文结构及各类 page type | 需要把“好读”转成可验收的用户结果 | D-004/D-006 已定方向；精确字段和 page type 留给后续规格 |
| OPEN-003 | 哪些来源/页面允许进入导航，哪些只进 Audit | 需要明确 degraded 与 not_released 的阅读边界 | 已由 D-011 解决第一轮：failed/degraded source、degraded page 只进 Audit；跨切片规则延期 |
| OPEN-004 | 何时认为结果“比 CompanyBrain 更好” | CompanyBrain 不是完全无缺，需要冻结可比维度和任务集 | 已由 D-007 解决第一切片；全库比较延期 |
| OPEN-005 | 代表性闭环具体 source manifest、对象边界和读者任务 | 已选 GoInsight“字段与筛选”，不能把候选文件名直接当作全量清单 | D-006/D-008/D-010 已冻结第一轮 manifest 身份、场景、题目和答案要点；执行器/存储格式留给后续 |
| OPEN-006 | 两类读者共用同页双层、同主题双入口，还是其他分层方式 | C 已确定两类读者，但页面结构会改变重复、导航和维护风险 | 已由 D-004 解决：同一 canonical 主题页双层 |
| OPEN-007 | 使用/支持层和规则/技术层各自必须完成什么真实任务 | 需要把双层结构转成可判定的 reader outcome | 已由 D-005/D-006/D-010 解决最小任务、预期输出、负向题和记录字段；自动化执行延期 |
| OPEN-008 | 双角色共同验收的具体真实场景 | 示例尚未冻结；场景会决定来源清单、页面边界和停止条件 | 已由 D-006 解决：按区域筛选设备；后续只展开执行细节 |
| OPEN-009 | 全部产品和 89 条来源都超过 CompanyBrain 的推广判定 | 第一闭环不能代表全库，且 CompanyBrain 质量随模块变化 | 第一切片通过后再由后续任务决定；本阶段延期 |

## Supersedes

无。本日志只新增本任务当前决策，不改写 Task 0–3 的历史记录。

## 文档结果

- CONTEXT.md：no-change；现有 Claim、Reader/Audit、TopicIndex、页级/交付级状态和失败语义已经覆盖本轮方向，新增的“位置字段筛选 pilot/读者任务/CompanyBrain 对照”是任务范围，不改项目通用术语。
- ADR：not-needed；Grill 判断本轮是隔离、可回滚的 pilot，未锁定新的跨项目架构；同页双层与 Reader/Audit 分离也与现有 ADR 0004 一致。
- ADR criteria：hard to reverse：否（pilot 可丢弃且不覆盖 formal）；surprising without context：否（D-009 已把 pilot 与正式门分开）；genuine trade-off：是（同页双层 vs 重复双页、严格对照 vs 快速通过），但不足以单独新建 ADR。
- 术语/ADR 冲突及处理：沿用原方案中的 ProductGazetteer、TopicIndex、Reader/Audit、`published/degraded`、`released/not_released`；代码的关键词映射和固定正文是待修实现问题，不改写术语定义。
- 不复制 spec 的边界：这里只保留需求、事实、决策索引和验收影响；页面字段、接口和测试步骤留给后续阶段。

## Exit checks

- 上下文一致：passed；已读取当前 WorkflowHub 任务、原始 PRD、v19 真实报告、根因报告和 CompanyBrain 参考方案。
- owner/接口一致：passed for direction handoff；用户保留最终确认权，make-decision 已定义下游消费的方向边界，detail review/spec-analyze 已完成且不再有隐藏方向问题。
- 失败语义明确：passed；失败/降级/not_released 不得伪装成正常发布。
- 范围与延期明确：passed；第一阶段由 D-001 收窄，D-006–D-009 冻结位置字段筛选 pilot、来源边界、正式门不变和全量延期。

## 当前方向重开记录（2026-08-18，Talk 修订）

本节是用户重新进入 `make-decision` 后的当前方向，不改写前面的历史选择和审查事实。前面的 pilot-only 决策保留为历史，但不再约束当前架构。

### D-020

- question/final_option: 是复制 CompanyBrain 的固定目录，还是借鉴它的整理方法并做成可扩展的通用编译器？选择 B：借鉴方法，做配置驱动的通用语义编译器。
- recommendation/plain_language: CompanyBrain 做得好，不是因为目录名字固定，而是因为先整理业务对象、用户问题、模块边界和页面用途，再写正文。KnowledgeDigest 要学这个方法，但不能把 GoInsight 的固定目录硬套给几万条未知资料。
- decision: 编译器先生成可演进的领域词表、对象、关系、场景和页面类型，再生成目录、文件名、正文、导航和来源关系；配置按知识域沉淀，不写成 89 条来源的专用映射表。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-companybrain-direction-batch` / 四项均选 "B"；第一项为“借鉴 CompanyBrain 方法，但做配置驱动的通用语义编译器，不照抄固定目录”。
- approval_binding: 当前 Talk 修订的用户选择；待方向审查、Grill、stage-end spec-analyze 和最终确认。
- facts_and_constraints: CompanyBrain 的真实流程是受控输入、来源归档、业务对象/模块/场景建模、类型化页面编译、产品审计和语义审计；GoInsight 的 `module_rules.json`、`feature_dictionary.json`、`object_relations.json`、`scenario_chains.json` 是显式领域配置；KnowledgeDigest 当前真实浅层输入会回退到“通用”，没有做语义模块识别。
- Logic: 复制固定目录不能承载未知产品和持续增长资料；只复制目录会把当前问题扩大到未来几万条；借鉴“先建模再编译”并把领域知识配置化，才能让编译结果可扩展、可追溯、可迭代。
- choice_reason/impact: B 同时保留 CompanyBrain 的质量来源和 KnowledgeDigest 面向多领域资料的扩展能力；影响是要补领域模型和候选配置，但这是提升知识质量的核心工作。
- consequences_and_risks: 自动推断可能生成错误对象或关系；证据不足时必须生成候选/待确认状态，不能静默写入正式目录。领域配置必须版本化并保留来源证据。
- rejected_alternatives: A 直接复制 CompanyBrain 固定目录：对已知产品有效，对未知知识会强行归类；C 继续只做通用目录和关键词聚类：会重演“通用”堆积和文件名失真。
- unresolved_items/owner: 领域模型字段、配置版本和候选确认方式交给后续规格；下游不得把它缩成 89 条静态映射。
- Supersedes: D-001、D-008、D-009 中“先做 pilot 再决定是否推广”的架构限制；不删除历史证据，只将 pilot 改为验证集用途。

### D-021

- question/final_option: 新知识超出 CompanyBrain 现有分类时怎么处理？选择 B：有证据才新建模块/对象；证据不足就待确认/降级，不默认扔进“通用”。
- recommendation/plain_language: 分类错了比暂时没有分类更糟。系统宁可告诉人“发现了一个新领域，证据还不够”，也不能用“通用”掩盖没识别出来。
- decision: 分类器必须区分“命中已有模块/对象”“证据支持的新模块/对象候选”“无法确认的待整理资料”。只有满足最小证据条件的候选才进入正式结构；其他内容保留来源、建议分类、证据和原因，进入批量处理。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-companybrain-direction-batch` / “新知识超出既有分类时，有证据才新建模块/对象，否则不默认进入通用”。
- approval_binding: 当前 Talk 修订的用户选择；待后续审查和最终确认。
- facts_and_constraints: CompanyBrain 的低置信内容会进入 `资料汇总`，不做无依据语义重写；GoInsight 配置有对象关系、场景链和禁止对象；KnowledgeDigest 当前的“通用”只是浅层路径缺失后的默认值，不是证据确认的分类。
- Logic: 未知内容无法安全套旧分类；默认“通用”会隐藏分类失败；证据驱动的新节点或待确认状态能保留信息并暴露不确定性。
- choice_reason/impact: B 解决新知识不在 CompanyBrain 范围内的问题，也不牺牲可读性和诚实状态；影响是要保存分类证据和候选提案，但不要求用户逐页检查。
- consequences_and_risks: 新模块过多会造成碎片化；需要按对象/场景相似性、证据量和跨来源一致性合并候选，而不是只看文件名。待确认内容不能进入正常 Reader 导航。
- rejected_alternatives: A 全部塞入“通用”：短期省事，长期不可检索；C 直接照抄 CompanyBrain：新产品、新业务和跨产品主题会被错误映射。
- unresolved_items/owner: 最小证据阈值、候选合并规则和批量确认表字段交给后续规格；当前只冻结“不静默归入通用”。
- Supersedes: 当前日志中把“通用”当作可接受默认归类的旧实现假设；不改写历史运行结果。

### D-022

- question/final_option: 优化只做摘要/正文，还是把目录、文件名、页面类型、正文、关系和来源一起重编译？选择 B：全链路一起重编译。
- recommendation/plain_language: 文件名已经错了，目录也已经错了，只改正文等于给错误导航贴更长的内容；必须从识别主题开始，连同路径和正文一起生成。
- decision: 每次正式发布以语义主题为单位，同时决定可读文件名、模块路径、页面类型、正文结构、相关主题、来源锚点和稳定身份。原始文件名和路径只留在来源记录，不直接当 Reader 标题。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-companybrain-direction-batch` / “目录、文件名、页面类型、正文、关系、溯源一起重编译”。
- approval_binding: 当前 Talk 修订的用户选择；待方向审查、Grill、stage-end spec-analyze 和最终确认。
- facts_and_constraints: CompanyBrain 正式页使用语义中文标题和业务对象/场景路径；例如 `Android安全通信网络配置项字典.md` 是按读者对象命名，而 KnowledgeDigest 的 `ae-通信和网络配置.md` 仍接近 raw slug；Task4 `_clean` 主要做 slug 化，真实浅层输入还会回退到“通用”。
- Logic: 路径和文件名决定能否找到主题；正文决定找到后能否解决问题；关系和来源决定能否继续查证；四者必须由同一语义编译结果产生。
- choice_reason/impact: B 直接解决文件名、分类和内容一起失真的根因；影响是不能把 Task4 限定为“质量评估器”，必须调整编译链核心职责。
- consequences_and_risks: 语义标题和路径可能因新证据变化；已发布主题需要稳定 ID 和路径变更记录，不能每次运行随意改名。证据不足时可以降级，但不能用自动 slug 冒充语义标题。
- rejected_alternatives: A 只优化正文：用户仍找不到；C 只做文件名美容：内容和分类仍不可信。
- unresolved_items/owner: 页面类型、命名冲突、旧路径迁移、跨对象关系和页内模板交给后续规格；不得在 build-spec 重新决定是否全链路编译。
- Supersedes: 非目标中“本任务不先做文件名美容”的字面排除；保留其反对孤立美容的原意，当前改为全链路语义重编译。

### D-023

- question/final_option: 人工质量确认逐页做，还是批量做？选择 B：机器先全量检查，人工集中看一张对照表和异常。
- recommendation/plain_language: 几万条资料不可能逐页检查；机器负责全量，人只看固定问题和异常，不把时间耗在重复翻页上。
- decision: 固定为“全量机器编译与检查 + 一张批量对照表 + 固定读者问题 + 异常展开”。人工不逐页标记每个来源；人工结果只对实际检查的题目/异常负责，未检查内容不得标成已人工确认。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-companybrain-direction-batch` / “批量人工评审，不逐个页面检查”。
- approval_binding: 当前 Talk 修订的用户选择；待审查和最终确认。
- facts_and_constraints: 用户已明确不想一个一个检查；现有 `17+3` 只能作为 89 条样本的回归基线，不能成为几万条生产资料的最终人工清单。
- Logic: 逐页人工成本随资料数爆炸；只看机器分数又会重演 v19 假绿；机器全量覆盖，再用固定问题和异常抽样检查读者结果，成本和质量才平衡。
- choice_reason/impact: B 保留人工判断价值，又面向未来几万条；批量表必须按领域、页面类型、置信度和异常类型组织，不能只展示位置字段筛选一条对照。
- consequences_and_risks: 抽样会漏掉少数坏页；机器报告必须列出全量失败、低置信、新模块候选、标题冲突、来源缺失和关系冲突，人工优先看异常。批量通过不等于所有页面人工阅读。
- rejected_alternatives: A 逐页人工：规模不可承受；C 只依赖自动分数：无法证明可读性和语义整理成立。
- unresolved_items/owner: 抽样策略、固定问题模板、异常排序和表格字段交给后续规格；当前只冻结批量而非逐页。
- Supersedes: D-018 中“17+3 是当前唯一人工范围”的表述；17+3 保留为 89 条样本回归基线。

### D-024

- question/final_option: 89 条原始文件是最终知识原材料，还是只是样本？结论：只是验证样本；生产架构面向后续几万条资料。
- recommendation/plain_language: 89 条用来验证系统有没有变好，不能写进模型。真正的分类、命名和编译规则必须换一批资料也能工作。
- decision: 89 条继续作为当前可复现的验证集、回归集和 CompanyBrain 对照样本；不把 89 条文件名、路径或人工结论硬编码成正式分类器。生产目标是支持数万条资料的分批摄取、增量更新、跨来源聚合、候选分类演进和可追溯失败处理。样本通过只说明样本上的编译器有效，不说明全库完成或超过 CompanyBrain。
- source_type/reference/exact_excerpt: user_reply / `user-reply-2026-08-18-sample-boundary` / “这89个原始文件只是一个简单的样本，我后续还有好几万的原始资料需要消化，不要把这89个当做最终知识原材料”。
- approval_binding: 用户最新澄清，直接绑定当前方向；后续审查和最终确认必须以此为前提。
- facts_and_constraints: v19 的 89 条只是一次运行输入；CompanyBrain 的配置是按产品/领域持续维护的业务模型，不是 89 条文件的逐条答案；几万条资料要求分批、可恢复、去重、增量和领域模型演进。
- Logic: 89 条只是样本；为样本定制映射无法泛化；样本应做回归而非定义模型；架构优先解决语义识别、候选分类、增量编译和批量质量反馈。
- choice_reason/impact: 该边界把当前验证范围和长期产品目标分开，避免再次做出样本专用的 0 分实现；当前不承诺几万条马上全部发布，但设计不能被 89 条绑死。
- consequences_and_risks: 数万条资料会出现跨语言、跨产品、重复、冲突和长尾新领域；没有候选/冲突和增量机制，系统会退回“通用”或复制错误结构。规模性能、成本和恢复需后续验证。
- rejected_alternatives: 把 89 条做成固定映射表：新增资料必然失效；把 89 条全量人工看完再推广：无法解决规模问题；先做通用空壳再补语义：会继续产生无意义目录。
- unresolved_items/owner: 批次、并发、成本、索引和恢复细节交给 build-spec/build-plan；方向层已冻结可泛化、可增量、样本不硬编码。
- Supersedes: D-001、DEFER-001、DEFER-002 中把 89 条全量编译和 17+3 正式评审写成最终交付边界的表述；历史保留，当前改为“89 条验证样本，生产规模为几万条”。

### D-025

- **question/final_option**: CompanyBrain 的旧冻结身份与当前只读目录不一致时，比较基线怎么处理？选择：重新绑定当前真实目录，保留旧身份为历史证据。
- **decision**: 当前正式比较基线为 `companybrain-full-20260819-current-v2`；范围是全部 1,406 个非系统常规文件，`tree_hash=dbfd60230790c7774e4a680397074859809dd9a0e5bc93af4c0923f51c27ea22`。其中 716 个正式 Markdown Reader 页作为页面对照范围；`_gbrain`、`_config` 仍计入完整性清单，但不作为 Reader 正文页。页面身份用 typed `ck1:<sha256>` comparison key，页面标题或明确小节标题才可提供匹配证据。
- **source_type/reference/exact_excerpt**: local_read_only_fact / `/Users/Hugh/Hugh/Knowledge/CompanyBrain` 当前实际目录；完整 manifest 由 `src/knowledge_digest/companybrain_mapping.py` 生成。
- **facts_and_constraints**: 旧 `companybrain-full-20260818-v1` 的 hash 不能与当前目录复核；继续沿用会把不同目录当成同一基线。当前 89 条原始输入仍保留 `confluence-raw-89-20260818-v1` 作为验证样本身份。
- **choice_reason/impact**: 先绑定实际只读目录，才能让逐文件 hash、页面 hash、comparison key 和评估回执闭合；旧报告不删除，只标历史，不再作为当前通过依据。
- **consequences_and_risks**: 正式 89 条仍受原始 5 字节空文件阻断；88 条可读诊断只能说明当前可读子集结果，不能替代 89 条正式结论。基线页没有明确 key 时只能 `not_applicable`（完整 Reader 范围已冻结为 exhaustive），身份缺失、冲突或重复只能 `undecidable`。
- **deferred_handoff**: 修复或明确排除空源后，重跑 89 条正式编译、对照和 verify-code；不得在本次任务内擅自删除该来源。
- **Supersedes**: 仅覆盖旧报告/配置中把 `companybrain-full-20260818-v1` 当作当前可复核基线的表述；不改写旧报告事实。

## 当前修订后的方向摘要

- 借鉴 CompanyBrain 的受控输入、来源归档、业务对象/场景建模、类型化语义页面、导航和审计；不复制固定目录和每个产品的硬编码脚本。
- 核心交付从“把 89 条文件写成页面”改为“把任意规模原始资料编译成读者能用、可回查、可演进的知识结构”。
- 结构识别、文件名、目录、页面类型、正文、对象关系和溯源一起生成；未知知识有证据才建新节点，证据不足就明确待整理，不进默认“通用”。
- 89 条是验证集；后续几万条是产品边界。验证方案可以用 89 条，实现方案不得出现 89 条专用映射、专用目录或专用人工结论。
- 人工只做批量对照和异常复核；机器覆盖全量来源和结构问题。具体题目、抽样、批次和成本字段下游补齐，但不能退回逐页检查。

## 当前修订的延期交接

| deferred_id | 暂不在 make-decision 细化 | 交接要求 |
| --- | --- | --- |
| DEFER-003 | 数万条资料的批次、并发、成本和恢复细节 | 只能补可执行参数，不能限定为 89 条单次运行 |
| DEFER-004 | 领域词表、对象/关系/场景配置 schema 和版本迁移 | 必须支持已有领域、新领域候选和待确认状态 |
| DEFER-005 | 语义命名、路径冲突、旧路径迁移和分页规则 | 同时保证可读名称和稳定 ID，不得恢复 raw slug 正式标题 |
| DEFER-006 | 批量对照表的抽样、异常排序和固定问题模板 | 必须覆盖不同领域、页面类型和置信度，不能只做一条位置筛选对照 |

## 本轮审查前状态

- Talk 修订：已完成；用户明确选择四项 B，并明确 89 条只是样本、生产面向几万条。
- 方向审查：待执行；审查对象是“通用语义编译器 + 新知识候选 + 全链路重编译 + 批量人工 + 样本/生产分离”。
- Grill、细节审查、stage-end spec-analyze、最终确认：待方向审查后按标准顺序执行。
- 当前不能进入 `build-spec`，也不能把本节当成最终确认。

## 当前方向审查结果（2026-08-18，Talk 修订后）

方向审查已完成，结果为 `available`。真实审查记录：

- attempt：`quality/reviews/attempts/de2e2ab3-88d7-4495-9adf-73e6bc226a33/attempt.json`
- result：`quality/reviews/results/make-decision-direction-8e8055b7d91b5f64b81898089e60c2a19fca4cfb-de2e2ab3-88d7-4495-9adf-73e6bc226a33.json`
- report：`quality/reviews/reports/de2e2ab3-88d7-4495-9adf-73e6bc226a33.md`
- 覆盖：`kimi/coding`、`codex/luna` 两个异源 provider，8 条有效 finding；不能把 transport 或 provider 返回当作方向通过。

### Finding 处置

| finding_id | 严重度 | 审查事实 | 当前处置 | Talk Round 3 后动作 |
| --- | --- | --- | --- | --- |
| F-68bcd91793af | blocking | 89 条与几万条之间没有可逆晋级边界 | needs_human | 冻结样本试点、晋级条件和停止/回滚规则 |
| F-8cb7a1072d69 | blocking | 通用编译器的生产承诺过大，没有中间验证路径 | needs_human | 决定“架构面向几万条”与“当前只验证小批”如何同时成立 |
| F-4b30909fd5ec | major | “更好”还没有可观察的质量标准和评估方法 | needs_human | 冻结 CompanyBrain 对照维度、样本审计协议和最低信号 |
| F-c39a8eff5e72 | major | 当前材料没有说明缺陷首发在哪个处理环节 | needs_human | 选择首个缺陷机制/页面类型，建立输入到输出的证据链 |
| F-02be0827376c | major | 一次重编目录、命名、页面、正文、关系和溯源，失败时难归因和回滚 | needs_human | 决定是否先做一条端到端闭环，再扩大编译范围 |
| F-be003e7e4a6a | major | 新模块/对象的证据、关系和待确认生命周期没冻结 | needs_human | 冻结最小知识模型与证据契约，不能留给 build-spec 猜 |
| F-dc679eacfe81 | major | “有证据”没有证据类型、阈值和冲突裁决 | needs_human | 冻结证据等级、阈值和冲突处理的方向原则 |
| F-e86eb8bb528f | major | 批量异常复核可能漏掉系统性坏页，没有真值集/抽样协议 | needs_human | 决定 89 条如何形成代表性真值/回归集，避免只看机器分数 |

以上 8 条先标 `needs_human`，不是因为必须把实现细节问完，而是因为它们会改变当前方向的范围、成功边界或可逆性。旧的 pilot-only 不自动恢复；需要在 Talk Round 3 把“架构长期目标”和“当前验证路径”同时说清楚。

## Talk Round 3（待用户回答的一组问题）

下面只问会改变方向的四件事，具体字段、命令和测试不在这里展开：

1. **几万条目标怎么落地？**
   - **A（推荐）**：架构按几万条设计，但当前只做一个可丢弃的小批验证；验证“归档→建模→命名/分类→正文→溯源→批量质量表”闭环，达到晋级条件后再扩展。
   - B：直接拿 89 条跑完整通用编译器，再按结果决定是否扩展；快，但失败范围大、难归因。

2. **第一条先证明什么？**
   - **A（推荐）**：先证明“CompanyBrain 的方法确实能修掉当前已证实的三类问题：`通用`误归类、raw slug 文件名、正文未按用户任务整理”；只选能覆盖这三类的代表性资料，其他能力先不宣称。
   - B：一开始同时覆盖所有页面类型、关系和所有质量问题；范围大，容易再次得到跑完但不好读的结果。

3. **新模块/对象的证据底线怎么定？**
   - **A（推荐）**：至少有“来源中明确出现的领域/对象名称 + 两条以上相互支持的事实或关系 + 没有与已有模块冲突”；不足就进入待确认，不进入正式 Reader。
   - B：只要模型判断相似就自动建；速度快，但很容易制造错误目录。

4. **人工批量评审如何防漏？**
   - **A（推荐）**：89 条建立分层回归集（已有模块、新模块候选、低置信、标题冲突、关系冲突、正文长短不同），批量表只看固定读者题和异常；机器负责其余全量覆盖。
   - B：只看固定 17+3 题，不做分层异常；最省事，但不能证明几万条可扩展。

用户回答后，make-decision 才继续 Grill；在此之前不进入 `build-spec`，也不把上述 finding 改写成已修复。

## Talk Round 3 用户回答与处置（2026-08-18）

用户一次回答四项：`A（只拿当前89条测试，能通过即可）`、`B`、`A`、`A（不要再让人工评审了，CompanyBrain也没这个步骤啊）`。

### 当前生效解释

- 当前验收范围只拿现有 89 条做测试；89 条仍然只是验证样本，不是未来几万条资料的最终知识原材料，也不能被写成 89 条专用映射。
- 本次 89 条测试不再先缩成一个页面类型或三个缺陷，而是一次覆盖现有样本中能出现的页面类型、对象关系、命名、分类、正文、导航和溯源问题；通过标准仍使用已记录的硬正确性、来源可回查、Reader 可用和三项 CompanyBrain 自动对照结果。
- 新模块/对象采用 A 的证据底线：来源明确出现名称 + 至少两条相互支持的事实或关系 + 不与已有模块冲突；不足时进入待确认/降级，不进入正常 Reader，也不默认进入“通用”。
- 删除本任务新增的人工评审。批量表改成机器自动生成的对照报告和异常报告，不要求用户逐页检查、逐题确认或人工判定通过。CompanyBrain 的可复用部分是领域建模和自动审计脚本，不是人工评审步骤。
- 几万条规模的性能、成本、分批恢复和生产晋级不作为本次 89 条验收条件；它们是后续扩展项。但实现仍必须保持通用、可增量、可配置，不能靠 89 条文件名和路径硬编码。

### 方向审查 finding 处置

| finding_id | 处置 | 处置理由和后续约束 |
| --- | --- | --- |
| F-68bcd91793af | accepted_risk | 用户明确本次只验收 89 条；数万条晋级边界延期，不伪装成已验证。架构仍不得写死 89 条。 |
| F-8cb7a1072d69 | fixed | 89 条本身就是当前可回滚验证路径；本次不承诺数万条已可生产运行。 |
| F-4b30909fd5ec | fixed | 沿用 D-019 的路径、答案完整度、边界/来源清晰度三轴，加硬正确性、来源可回查、无占位/无错误归类；本次全部机器计算。 |
| F-c39a8eff5e72 | fixed | 89 条测试同时保留来源快照、领域识别、对象关系、页面编译和最终页面的中间证据，失败时能定位首个失败环节。 |
| F-02be0827376c | fixed | 允许本次全链路一起编译，但每个环节必须有独立诊断和来源绑定，失败不覆盖旧结果，便于定位和回滚。 |
| F-be003e7e4a6a | fixed | D-021 与本轮 A 冻结最小实体/关系证据底线；待确认生命周期作为 Audit 状态，不进入 Reader。 |
| F-dc679eacfe81 | fixed | 证据类型、两条支持事实/关系和冲突排除已成为新节点最低条件；冲突进入待确认，不自动选边。 |
| F-e86eb8bb528f | accepted_risk | 用户明确删除人工评审；机器必须生成分层覆盖、固定三轴对照、全量异常和失败清单，但不声称人工确认，也不以人工步骤作为通过条件。 |

以上处置是当前 Talk 结论，不代表 make-decision 已完成；仍需完成 Grill、决策草案、细节审查、stage-end spec-analyze 和最终确认。

## Grill with docs（2026-08-18）

本轮按现有项目术语、PRD、代码和 CompanyBrain 资料做质询；用户已经明确的四项选择作为当前输入，不再把实现细节反问给用户。

### 术语和现有模型对齐

- `Claim`、来源快照、`fragment_locator`、主题页、稳定 `digest_topic_id`、Reader/Audit 分离、页级 `published/degraded` 和包级 `released/not_released` 继续沿用，不另造一套状态模型。
- “通用”不再被当作正式知识模块。它只能作为当前实现暴露出来的问题名；正式输出使用已有的未分类/待确认/降级语义，待确认内容只留在 Audit，不进正常 Reader。
- “89 条”固定叫验证样本/回归集；“几万条”是生产规模目标。本任务不把后者写成已验证事实，也不把前者硬编码成领域词典。
- “不人工评审”指不要求人打开页面、逐题判断或人工确认知识质量；机器报告必须可重放。现有 ADR 0008 中“汇总确认不是正文评审”的区分保留，正式发布是否需要工作流确认不在本次代码质量对照中重新发明。

### 文档和代码质询结论

- `CONTEXT.md` 已覆盖 Claim、来源溯源、Reader/Audit、失败不伪装和本期不设人工复核流程；本轮是把它们用于通用语义编译器，**CONTEXT：no-change**。
- ADR 0004 已明确 Reader 与 Audit 分离；ADR 0008 已明确拒绝逐页人工阅读并保留自动读者题集。本轮的机器对照、异常报告和不产生 `human_reviewed` 与现有语言一致，**ADR：not-needed**。
- CompanyBrain 的可复用事实是“先有领域/对象/场景模型，再由脚本生成语义页并审计”；它不是把所有内容扔进固定 `通用`，也不是靠逐页人工评审。KnowledgeDigest 下游必须复用这个因果顺序，而不是复制 GoInsight 的固定目录。
- 当前实现的浅层输入回退和 raw slug 命名，正好对应用户指出的三类可见缺陷；因此本次全链路编译有真实问题依据，不是单纯追求更复杂架构。

### 具体边界场景

1. 来源明确出现一个新领域名，并有两条相互支持的事实/关系：生成新模块/对象候选，保留证据和稳定 ID，进入 Reader。
2. 只有文件名相似、没有足够事实，或与既有模块冲突：进入待确认/降级和 Audit，不进入 Reader，不默认进“通用”。
3. 某个来源或某个页面编译失败：保留原始快照、失败原因和已成功的其他页面；受影响页面不进入导航，候选包按既有规则保持 `not_released`，不覆盖旧正式结果。
4. 自动对照报告无法判断、缺来源或出现矛盾：报告标记失败/不可判定，不生成“人工通过”，也不把空结果当质量通过。

### Grill 退出检查

- 上下文一致：passed；沿用现有 Claim/Reader/Audit/状态术语，没有与 CONTEXT 或 ADR 产生新冲突。
- ADR 判断：not-needed；本轮是既有 Reader/Audit 和自动读者门原则的范围修订，不新增不可逆存储或跨项目架构。
- owner/接口可交接：passed；下游只实现已确定的语义编译、证据底线、机器对照和失败可见性，不得把 89 条做成静态映射，也不得重新引入人工评审。
- 失败语义：passed；低置信、新节点冲突、来源失败、页面失败、报告不可判定均有可见状态和 Audit 证据，不伪装成功。

Grill 结论：当前方向可以继续写决策草案；仍需在细节审查前把用户流程、页面范围、机器数据状态、自动成功/失败边界、非目标和延期交接收束成一份最终方向摘要。

## 当前正式决策草案（Grill 后，2026-08-18）

### 一句话决定

KnowledgeDigest 要借鉴 CompanyBrain 的“先建领域/对象/场景，再编译读者知识页”的方法，做成配置驱动、可增量演进的通用语义编译器；当前只用 89 条样本验证，必须同时修复目录、文件名、分类、页面类型、正文、关系和溯源；所有质量判断用机器自动完成，不新增人工评审。

### 用户流程

1. 操作人提供一批原始资料，系统建立来源快照、唯一 ID、内容指纹和审计清单。
2. 系统识别产品/领域、模块、业务对象、关系和用户场景；已有配置直接复用，证据足够的新节点进入候选，证据不足的内容进入待确认/降级。
3. 系统把同一主题的来源合并，再一起生成语义路径、中文文件名、页面类型、正文、相关主题和来源锚点；原始文件名只留在 Audit。
4. 用户从 `Home → 产品/领域 → 模块/对象/场景 → 主题页` 阅读；Reader 只展示可读且通过机器门的主题页，Audit 保存原文、Claim、Evidence、Provenance、候选和失败原因。
5. 系统自动生成 89 条覆盖报告、CompanyBrain 对照报告、异常报告和失败清单；不要求用户逐页打开、不要求人工逐题确认。

### 页面范围

- 89 条来源全部进入来源清单和 Audit；重复来源保留 canonical 关系，失败来源保留失败证据。
- Reader 按稳定主题、对象、场景或任务合并页面，不按输入文件机械生成 89 页。
- 89 条样本中出现的页面类型、对象关系、跨页关系、命名和边界问题都属于当前验证范围；不能只验证“位置字段筛选”一条页面。
- 正式 Reader 页面必须有语义标题、清楚的用途/适用范围/正文结构、相关主题入口和可回查来源；不能继续使用 `ae-通信和网络配置.md` 这类 raw slug 作为正式语义命名。
- 未确认新节点、低置信分类、冲突关系和失败页面只进入 Audit/候选状态，不进入正常 Reader 导航。

### 机器数据状态

- 来源：`valid`、`duplicate`、`failed`、`degraded`。
- 主题页：`published` 或 `degraded`；只有通过机器门的页面才能进入候选 Reader 导航。
- 交付包：`released` 或 `not_released`；当前 89 条是验证候选，不把验证通过自动说成几万条生产已完成。
- 语义分类：`existing`、`new_candidate`、`pending`、`conflict`；`pending/conflict` 只能进 Audit。
- 每个 Claim 必须绑定来源 URI、内容指纹、片段定位、验证状态和唯一正式归属；机器报告必须能回放来源到页面的映射。
- 自动对照：记录 KnowledgeDigest 和 CompanyBrain 各自的入口、首个命中、跳转、答案要点、边界/来源锚点和 `N/A` 原因；不生成 `human_reviewed`。

### 自动成功边界

当前 89 条测试只有同时满足以下条件才算通过：

1. 89 条来源都有唯一身份、快照/指纹和最终状态，没有静默丢失。
2. 不把无法确认的内容静默塞入“通用”；新模块/对象满足“明确名称 + 两条相互支持事实/关系 + 无既有冲突”的最低证据。
3. 目录、文件名、页面类型、正文、关系和溯源互相一致；正文不是原文堆放、固定摘要或占位内容。
4. Reader 导航可达，正式页面能完成机器定义的读者问题，相关主题和来源入口可继续查。
5. 机器对照按既有三轴计算：路径、答案完整度、边界/来源清晰度。KnowledgeDigest 至少一轴严格优于 CompanyBrain，其他轴不变差；无对应内容记 `N/A`，不假造优势。
6. 所有失败、冲突、低置信和无法判定信号都有原因、来源/页面标识和 Audit 证据；旧正式结果不被半成品覆盖。

### 自动失败边界

- 任一来源静默丢失、无法回查、错误归类、错误命名、关键事实丢失或边界说反。
- 新节点证据不足却进入 Reader，或冲突关系被自动选边。
- 页面仍是 raw slug、`通用`默认堆积、占位摘要或原文拼接，机器不能证明正文已按任务整理。
- Reader 不可达、Audit 内容混入 Reader、对照报告缺字段、质量结果不可判定或任何关键轴退化。
- 失败时只保留候选/Audit 并返回 `not_released`，不通过 fallback 把失败改成成功，不要求人工补判。

### 非目标

- 本次不证明几万条资料的性能、成本、并发、恢复和生产晋级；只验证当前 89 条样本。
- 本次不把 89 条做成静态分类表、文件名映射表、专用目录或专用人工结论。
- 本次不新增人工评审、逐页检查、逐题确认或 `human_reviewed` 状态。
- 本次不复制 CompanyBrain 的固定目录和产品硬编码脚本；只复用领域建模、语义编译和自动审计方法。
- 本次不加入数据库、向量库、调度器、后台守护，不先做 UI 重绘，也不降低失败和溯源底线。

### 延期交接

- 下游只补通用编译器的 schema、配置文件、接口、命令和自动测试；不得重新决定当前范围、机器-only 验收、证据底线或 89 样本边界。
- 几万条资料的规模化运行另行验证；但下游实现不得依赖 89 条硬编码，必须保留批次、增量、配置版本和候选演进接口。
- CompanyBrain 的更多领域配置和跨产品关系先作为可加载配置，不在本次把所有领域一次性建完。
- 具体自动读者题、对照表字段和异常排序可以在后续规格细化，但必须落在当前三轴和机器-only原则内。

## 当前细节审查结果与最小补充（2026-08-18）

detail review 已完成，真实记录：

- attempt：`quality/reviews/attempts/a6bfed60-11c0-4529-bd2f-bad0b137c991/attempt.json`
- result：`quality/reviews/results/make-decision-detail-ef5fa9bb9a8fc8e8c8bfc73953d93ea919fc9a88-a6bfed60-11c0-4529-bd2f-bad0b137c991.json`
- report：`quality/reviews/reports/a6bfed60-11c0-4529-bd2f-bad0b137c991.md`
- 覆盖：`kimi/coding`、`codex/luna` 有语义结果；`opencode/v4flash` 为 `SESSION_IDLE_WITHOUT_TERMINAL`，保留为 partial transport 事实。

### Findings 处置

| finding_id | 处置 | 结果 |
| --- | --- | --- |
| F-32d38902d50a | fixed | 增加最小 Claim/页面/关系 lineage 合同，见下文。 |
| F-474b69a9e841 | fixed | 增加节点、事实、关系稳定身份和证据准入合同，见下文。 |
| F-80956360b9f6 | fixed | 增加 CompanyBrain 固定基线、三轴公式、N/A、unknown 和严格优于规则，见下文。 |
| F-afa9694e94c8 | fixed | 增加“症状→证据→首个失败环节→改动→复跑结果”的根因映射，未完成则 not_released。 |
| F-bb8ef08eb991 | fixed | 增加最小状态转换、部分失败、幂等和原子发布不变量，见下文。 |
| F-ad74ba8a3c93 | accepted_risk | 本任务不增加第 90 条原始资料或规模试验；用配置入口、禁止 89 条字面硬编码和确定性配置变体测试防止专用映射，数万条反过拟合留给后续规模任务。 |
| F-3d7e5e6848b2 | fixed | 当前 decision-log 已有明确延期交接；原 review 输入是压缩摘要，下一阶段以完整本日志为唯一方向材料。 |
| F-a8a92e32dc04 | fixed | 当前本日志已包含 Talk、Grill、CONTEXT/ADR 判断、取舍、风险、拒绝方案和退出检查；不再用压缩摘要替代完整决策材料。 |
| F-d1750da04198 | fixed | 当前决策草案已补充中间状态和转换，不把状态名留给 build-spec 猜测。 |
| F-4c5029eeee99 | fixed | 已补充固定 CompanyBrain 基线、同题同评估器、路径/答案/边界来源三轴公式、N/A/unknown 规则和“至少一轴严格优于且其他不变差”的机器判定。 |

### 最小溯源合同

每个正式 Claim、页面和关系必须保留以下绑定：

- `source_snapshot_id`、来源 URI、内容指纹、`fragment_locator`；
- `claim_id`、Claim 文本、验证状态、唯一 `target_path`；
- `page_id`/稳定 `digest_topic_id`、页面类型、实际发布路径；
- 关系的 `relation_id`、两端稳定 ID、关系类型和支持来源；
- `lineage_step`，记录它经过“识别、归类、合并、编译、发布”哪一步；
- 机器检查结果：来源覆盖率、Claim 断链数、页面断链数、关系断链数。

缺任一必需绑定，不能进入正常 Reader；保留原始来源和失败原因在 Audit。

### 新节点最小语义合同

新模块/对象候选要同时满足：

1. 来源正文或标题中明确出现该领域/对象名称，形成稳定候选身份；
2. 至少两条来自同一来源或相互独立来源、且指向同一候选的事实/关系支持；
3. 与已有模块/对象没有名称、职责或关系冲突；有冲突就进入 `conflict`，不自动选边；
4. 候选、支持事实、冲突事实和最终决定都保留来源定位。

不满足条件时状态为 `pending` 或 `conflict`，只进 Audit，不进 Reader，不默认写入“通用”。

### 三轴自动对照合同

CompanyBrain 对照固定使用 `companybrain-goinsight-field-filter-20260817-v1`；两边从各自 Home 开始，使用同一题目、同一自动 evaluator 和同一记录格式。

- 路径轴：`path_score = (first_hit_correct, -hop_count)`，按字典序比较；首个命中错误优先于跳转少；无命中为失败。
- 答案轴：固定答案要点通过数 / 要点总数；关键要点缺失或说反直接失败。
- 边界/来源轴：固定边界检查通过数 + 可回查来源检查通过数，除以该题总检查数；来源锚点断裂直接失败。
- 每条题记录两边的 Home、首个命中页、跳转数、答案要点、边界结果、来源锚点和 `N/A` 原因。
- CompanyBrain 没有对应主题时记 `N/A`，不制造劣势或优势；如果所有关键题都为 `N/A`，不能形成“严格优于”结论。
- 计算 `KnowledgeDigest - CompanyBrain`：至少一轴严格为正，另外两轴不为负；任一关键题 unknown、缺证据或轴退化，自动失败。
- 该比较完全由机器执行，不生成 `human_reviewed`，不要求用户打开页面确认。

### 根因闭环合同

每个主要缺陷必须生成机器可读记录：

`symptom → evidence_ref → first_failing_stage → change_ref → rerun_result`。

当前至少覆盖：错误落入“通用”、raw slug 文件名、正文固定包装、对象/关系缺失、来源断链和 Reader 不可达。没有证据的根因只能标 `unconfirmed`，不能当作已修复。

### 最小状态转换与发布不变量

`source_snapshot → identified → claim_candidate → reader_candidate | pending | conflict | failed → published | degraded → candidate/not_released`。

- `source_snapshot` 必须有内容指纹；重复来源转 `duplicate` 并继承 canonical 关系。
- `identified` 记录领域、模块、对象、场景和置信理由；无法确认转 `pending`。
- `claim_candidate` 只有完成溯源和唯一归属才能转 `reader_candidate`。
- `pending/conflict/failed` 只进 Audit；不因其他页面成功而静默进入 Reader。
- `reader_candidate` 通过机器门才转 `published`，否则为 `degraded`。
- 任一核心页面、关键来源、对照报告或完整性检查失败，包级保持 `not_released`；不覆盖旧正式结果。
- 同一来源指纹和配置版本重跑必须幂等；不能重复创建主题、Claim、关系或归档内容。

### Deferred handoff

交给下游的不是“请自行决定怎么做”，而是以下固定方向材料：

- 通用编译器：领域/对象/关系/场景配置入口，不能出现 89 条来源专用映射；
- Reader：语义目录、文件名、页面类型、正文、相关主题和来源入口一起发布；
- Audit：保留快照、Claim、Evidence、Provenance、lineage、候选/冲突/失败和根因映射；
- 自动质量：89 条覆盖、三轴 CompanyBrain 对照、异常报告、unknown/失败报告和 not_released 结果；
- 待实现但不改方向的细节：配置文件 schema、具体命令、页面模板、自动题目、批次/恢复参数、测试脚本和证据文件路径；
- 明确延期：几万条资料的成本、性能、并发、恢复和生产晋级，不作为当前 89 条验收条件。

### 复审 transport 事实

- `opencode/v4flash` 的 `SESSION_IDLE_WITHOUT_TERMINAL` 是真实不可用事实，不改写为空 finding，也不阻塞同任务继续。
- `kimi/coding` 和 `codex/luna` 的有效 finding 已逐条处置；当前不重复请求同一份未变化的 detail review。

## 当前输入边界更新（2026-08-19，D-026）

### 原始事实

- `emm for android /AE - AirViewer厂商管理.md` 的原始内容只有 5 bytes：`b"  \\n+  "`，没有标题正文、Claim、操作步骤或边界事实。
- 在 Downloads、旧 KnowledgeDigest 产物和本地 CompanyBrain 中没有找到同名的可恢复正文；相关的 AirViewer 插件包设置和新厂商适配资料是其他来源，不能冒充这一个空白来源的原文。
- 如果继续按普通来源失败处理，89 条正式候选永远无法完成；如果补写推测正文，则会破坏溯源和“失败不伪装成功”的原始要求。

### 选择

把这个**已确认的标题-only 空白页**作为 `not_applicable` 输入处理：

- 仍进入 89 行 source manifest、Audit 原始快照和失败/处理原因记录；不静默丢弃。
- 不生成 Reader 页面、不生成 Claim、不把文件名当正文。
- 只对当前 `source_uri + content_hash` 精确 allowlist；其他任何空白来源仍按 `empty_body` 硬失败。
- CompanyBrain 对照把该项作为中性 `N/A`，不贡献 KnowledgeDigest 优势，也不形成 `undecidable`。

### 理由与风险

这是对“没有知识内容的导出占位页”的数据边界处理，不是放宽普通空源质量门。这样保留事实、避免编造，并让其余 88 条真实知识进入正式机器对照。风险是原始 Confluence 页面未来可能被补回正文；届时内容指纹变化，allowlist 不再匹配，系统会重新阻断并要求新 run。

### 用户确认与延期交接

- 用户在 2026-08-19 回复“好的，你去处理吧，处理吧完成尽快close”，确认按上述方式处理并继续收尾。
- 下游必须保留精确 allowlist、空源 Audit 和指纹漂移失败；不得把 `audit_only` 扩展成所有空源默认放行。
- 其他真实资料、规模化吞吐和未来空白页处理规则不在本次继续扩展。
