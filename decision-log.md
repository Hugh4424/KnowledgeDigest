# Decision Log

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 关联 D/处理状态 |
| --- | --- | --- | --- |
| R-001 | Task 2-B 必须按标准 WorkflowHub 从 `make-decision` 开始，不跳阶段，不让 `build-spec` 补产品决策。 | 用户原话："请按标准 WorkflowHub 从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。" | D-001–D-003；已覆盖 |
| R-002 | Talk 说清选项、后果、风险；decision-log 保留原始需求、事实、选择、理由和延期交接。 | 用户原话："Talk 请用大白话说明选项、后果和风险；decision-log 记录原始需求、关键事实、选择、理由和延期交接。" | T-001–T-003、G-001；已覆盖 |
| R-003 | 先冻结完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。 | 用户原话；PRD §Task 2-B，lines 627–699 | 本文「流程与边界」；已覆盖 |
| R-004 | 交付小语料类型化正文编译闭环：Normalizer → TopicIndex → PageDraft → OKF Concept Compiler → Publication Gate；三类 page type；正文与 Evidence/archive 分离；失败 fail-closed。 | PRD lines 651–668、686–699 | D-001–D-004；已覆盖 |
| R-005 | Task 2-A 已正式完成，其缺口已在其他会话处理并合并到 `main`。 | 当前用户原话："我已经把task 2-A正式完成了，差的这几项都在其他会话搞定了，也合并到main了" | Task 2-A handoff；按当前用户事实接收，不在本任务重开 |

## 目标

- 让小语料页面真正回答读者问题，而不是把 Evidence 原文堆进正文。
- 保留 Task 2-A 已冻结的 Reader Bundle、frontmatter、index/log、source/claim footnote 合同。
- 在机器门内证明正文可编译、可归因、可回查、可失败；不把机器结果说成人工读者质量。

## 流程与边界

### 用户流程

1. 运行读取 Task 0/Task 1 的冻结输入、TopicIndex、样本覆盖记录和 Task 2-A Reader Bundle 合同。
2. Structure Normalizer 将父子页、标题/H1、FAQ、表格、图片、双语、版本和噪声块变成可追溯结构。
3. TopicIndex 确定主题身份、产品/模块关系和 page type；未映射、冲突或证据不闭合的项进入 Audit。
4. PageDraft 生成受控 section 草稿；provider 只填写受控正文内容，不能自行增加 page type、section 或来源字段。
5. OKF Concept Compiler 将正文、页内 source id、claim id footnote、frontmatter 和索引投影写入样本包。
6. Publication Gate 检查必需 section、100% 事实归因、数字/标识符/版本、命令/端口/配置、表格/图片、近重复、golden-negative 和页面边界。
7. 通过的页进入 Reader 导航；失败页保留 Audit/Archive 原因、输入指纹和恢复路径，整包保持 `not_released`。

### 页面范围

- Reader concept page：`product_overview`、`module_or_capability`、`procedure_or_rule`。
- Reader navigation：根、产品、模块和主题索引；`index.md` 是唯一 canonical navigation。
- Audit/Archive：失败、冲突、缺证据、旧正文和完整 Claim/Evidence/原文；不是读者入口。

### 数据状态

- 页级：`published` 或 `degraded`；`degraded` 不进入正式导航。
- 交付级：Task 2-B 只能是 `not_released`，不能声称 `released`。
- 内容信号：`generated`、`digest_machine_pass`、`verified`、`stale_after` 按 Task 2-A/PRD 合同分开；内容变化使旧验证事件失效。section 另记录 `documented` 或 `source_not_documented`；后者只允许用于 `procedure_or_rule.exceptions`，不是页级状态，也不等于“没有异常”。
- 增量更新：section 只有在依赖集合、版本、结构关系和归因都可证明未变时才能复用；影响关系不确定时扩大到整页重编。

### 成功边界

- 至少 6 个 machine-passing concept。
- 三类 page type 各至少 1 个；`procedure_or_rule` 在 `exceptions` 经过确定性来源审计并标为 `source_not_documented` 时，仍可计入 page-type 覆盖，但不能声称异常处理规则已被回答。覆盖 Task 1 inventory 中实际存在的长文、表格/图片、双语、多源类别；不存在的类别必须有 machine fixture 或排除理由。
- 使用 Task 0/Task 1 已冻结的 12–20 篇代表样本，不由编译器临时挑选；样本来源和覆盖以 `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json` 为准。
- 至少一次冻结 provider/model/预算的真实语义运行完成并留存结果。

### 机器验收底线（下游不能降低）

- 语义出口必须同时满足：`machine-passing concept >= 6`；三类 page type 各至少 1 个；实际 inventory 中存在的长文、表格/图片、双语、多源类别均被覆盖；inventory 中不存在的类别必须有 machine fixture 或明确排除理由。
- 必须至少完成一次冻结 provider/model/预算的真实语义运行并留存运行结果、失败项和归因信息；未完成、fallback、Jaccard-only 或语义证据不足时，交付级保持 `not_released`。
- 这三条是 Task 2-B 的机器成功底线，不由 `build-spec`、临时样本或单次结构测试下调。
- `procedure_or_rule.exceptions` 是唯一例外：若确定性来源审计证明冻结来源没有明确异常触发、处理、分支或恢复规则，section 必须存在并写入 `source_not_documented` 状态；它不生成领域 Claim，异常专属问题记为 `not_answerable`，但不因此阻断该页 Reader/机器通过。其他必需 section 仍须完整、可归因并通过既有门禁；来源含糊、provider 映射失败或审计不确定时仍按失败处理。

### 失败边界

- 必需证据缺失、归因不闭合、版本冲突、事实保真失败、provider 失败、截断 JSON、fallback、golden-negative 未失败或近重复命中：页为 `degraded`，不进正式导航；唯一例外是通过确定性来源审计确认的 `procedure_or_rule.exceptions=source_not_documented`，其状态进入页内审计且不被写成领域事实。
- provider 只能生成受控 section；任何无法解析为唯一 `claim_id + source URI + content hash + fragment_locator` 的事实不得进入正式正文。
- 影响关系无法证明时整页重编；整页重编失败时整页 `degraded`，旧 Reader 页不被失败结果覆盖。
- Jaccard/离线结果只能作结构基线，不能满足语义 exit；Task 2-B 不形成人工读者质量通过。

## 范围

- 当前范围：小语料、三类 page contract、Normalizer、受控 PageDraft、OKF concept 编译、claim/source 回指、保真与降级门、样本索引和语义运行证据。
- 当前 contract revision 预算：`1/1`（本轮 C1 变更已占用唯一额度，待用户确认）。改变 section 集合、模板、必需/可选字段或 page type 映射消耗唯一一次修订；只修复既有合同的行为 bug 不消耗；后续不得再用实现缺陷修复偷改本规则。
- 影响闭包定义：section 的直接 source/claim/版本/结构依赖，以及由其变化传递影响的关联 section；无法证明不受影响即纳入整页重编。

## 非目标

- 全量 89 篇正文编译和正式 `released`。
- Task 2-C 的人工读者门、人工评分、`human:*` 信号和最终信任判断。
- Task 3 的完整 17+3 题集、全量交付门和发布。
- 新增 page type、数据库、图谱、永久 candidate 队列、无人维护的人工复核系统。
- 用全局正文复制率作为硬门；不把 provider 成功、写回成功或结构 lint 当成读者质量通过。

## 决定

### D-001

- question/final_option: 正文由谁控制结构？最终选择 A：固定页面骨架，provider 只填写受控 section。
- recommendation/plain_language: 推荐；代码先定页面该回答什么，模型只补具体说法。
- decision: 必需/可选 section、page type、来源字段和校验边界由确定性代码控制；provider 输出不得改变这些合同。
- source_type/reference/exact_excerpt: user_talk / Talk Round 2 / T-001 / "A"；PRD lines 653–655、686–690。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: Evidence 不适合作为读者正文；正文必须可读且每条事实可回查；provider 失败只能 degraded/not_released。
- Logic: Evidence dump 是已知问题 -> 需要可读正文但不能放松归因 -> 由固定骨架限制模型输出 -> 必需 section、来源和失败边界稳定可验。
- choice_reason/impact: 可预测、容易回查、不会让模型扩张页面合同；影响 `PageDraft`、compiler、validator、provider prompt 和 semantic sample runner。
- consequences_and_risks: 文风可能更模板化；受控 section 的内容矩阵必须足够清楚，否则会得到空泛答案。
- rejected_alternatives: B（provider 生成完整 PageDraft）风险是漏 section、无证据断言和截断；C（纯规则拼接）不能满足语义正文 exit。
- unresolved_items/owner: 各 page type 的最终 section 内容和样本级提示词在后续规格/实现材料中落地，但不得改变本决定的骨架边界；owner=Task 2-B。
- Supersedes: none。

### D-002

- question/final_option: 来源更新时是否整页重编？最终选择 B：只重编受影响 section，但先计算影响范围。
- recommendation/plain_language: 用户选择 B；它减少无关内容抖动，同时保留旧正文稳定性。
- decision: 每个 section 必须记录 source/claim/版本/结构依赖；只有依赖集合和归因全部未变才能复用旧 section；新旧内容不能直接拼接。
- source_type/reference/exact_excerpt: user_talk / Talk Round 2 / "我想选B，但是需要注意，虽然只改受影响的section，但是需要评估哪些section受影响，尽量不要出现“旧 section 可能残留过期说法”的问题"。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: PRD line 656 要求 `old_target_body` 真正进入 revise 上下文；PRD lines 442–443 规定内容变化使旧验证失效；PRD lines 895–896 要求 affected set 外正文和路径字节不变。
- Logic: 更新只影响部分证据 -> 需要减少无关 section 变化 -> 用依赖闭包判断受影响范围 -> 只复用可证明安全的 section，避免旧说法残留。
- choice_reason/impact: 页面稳定性和更新安全之间取平衡；影响 revise context、section dependency manifest、content hash、verified invalidation、writeback 和回归测试。
- consequences_and_risks: 需要维护反向依赖和影响诊断；漏记依赖会产生旧内容风险，因此 D-003 规定保守兜底。
- rejected_alternatives: A（每次整页重编）成本和页面抖动较大；C（新旧正文并存）会污染 Reader，且不能证明当前答案。
- unresolved_items/owner: 依赖字段的具体序列化格式属于实现合同，必须在本任务内冻结；owner=Task 2-B。
- Supersedes: none。

### D-003

- question/final_option: 影响范围算不清时怎么办？最终选择 A：扩大到整页重编。
- recommendation/plain_language: 推荐；不确定就多做一点，不能拿旧内容冒险。
- decision: 影响关系不完整、版本/结构关系不确定或归因无法证明时，整页重编；整页重编失败则整页 `degraded`，旧 Reader 正式页不覆盖。
- source_type/reference/exact_excerpt: user_talk / Talk Round 3 / "A"；Grill G-001。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: 项目已有页级 `published/degraded` 与交付级 `not_released`；PRD lines 657–668 要求失败显式降级、旧正式结果不被失败样本覆盖。
- Logic: 影响不确定 -> 不能证明旧 section 安全 -> 整页重编取得一致上下文 -> 重编失败保持 degraded/not_released，避免静默残留或覆盖。
- choice_reason/impact: 把“增量更新”限制在可证明安全的情况；影响 Publication Gate、atomic writeback、失败 manifest 和旧页保护。
- consequences_and_risks: provider 调用和页面变化可能增加；但风险是可见、可回放，不会伪装成成功。
- rejected_alternatives: B（只降级不确定 section）可能留下新旧不一致；C（旧 Reader 永久保留、新结果只进 Audit）会让更新不生效。
- unresolved_items/owner: 影响闭包的具体依赖图和诊断错误码在实现阶段定义；owner=Task 2-B。
- Supersedes: none。

### D-004

- question/final_option: 小语料、抽样蕴含和契约修订怎么受约束？最终选择沿用已冻结合同，不新增临时门。
- recommendation/plain_language: 直接复用 Task 0/Task 1/PRD 已有事实，避免下一阶段重新拍脑袋。
- decision: 使用冻结的 12–20 篇样本和其 source/type/answerability 覆盖记录；抽样蕴含记录固定 seed、样本数、判定阈值、检测器/模型和失败项；Task 2-B 只做机器诊断；在 D-005 修订前 body/section contract revision 为 `0/1`，现已被 D-005 占用，当前为 `1/1`（待用户确认）。只有改变 section 集合、模板、字段或 page type 映射才消耗；D-005 的这次受控修订已耗尽额度。
- source_type/reference/exact_excerpt: PRD lines 432、437、440–442、479、653、657、665、697；Task 0/Task 1 frozen evidence refs in PRD line 574。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: 样本不能由编译器临时挑选；`sampled_entailment` 是机器 verified 白名单事件；Task 2-C 才是人工读者门；fallback/Jaccard 不能满足 semantic exit。
- Logic: 样本和质量门已有上游冻结事实 -> 不允许 build-spec/实现者重新解释 -> 当前记录边界和来源 -> 后续只实现和回放，不扩大合同。
- choice_reason/impact: 解决 direction review 的四项 minor 缺口，保持任务边界可追溯；影响 sample manifest、semantic run、quality oracle 和 contract revision 记录。
- consequences_and_risks: 当前日志不替代真实样本 manifest、阈值和运行证据；如果上游 manifest 缺失或无法回读，必须 `not_released`，不能用新 fixture 冒充。
- rejected_alternatives: 临时按 page type 自由挑样本、临时降低阈值、把人工读者门前置，都会改变已冻结阶段边界。
- unresolved_items/owner: 实际样本逐项清单、检测器版本和运行预算仍需从冻结 manifest/config 回读并写入 Task 2-B 运行证据；不存在的 inventory 类别必须有 machine fixture 或明确排除理由；owner=Task 2-B，不能由 `build-spec` 补产品决策。
- Supersedes: none。

### D-005

- question/final_option: 冻结来源没有异常处理规则时，`procedure_or_rule.exceptions` 是否必须让整页失败？用户先选 C：保留 section，但明确标记“来源没有说明”，不编造领域事实；随后选 C1：其他 section 通过时，允许该页进入 Reader 和机器通过，但异常专属问题仍记为 `not_answerable`。
- recommendation/plain_language: 推荐 C1；它把“来源没写”与“系统判断没有异常”分开，读者仍能看到有用的步骤/规则内容，同时不让编译器拿别的段落凑异常处理。代价是页面可能通过机器门，但异常问题本身仍没有答案，必须在状态和审计里说清楚。
- decision: `procedure_or_rule.exceptions` 仍是固定 section，不能省略。仅当确定性来源审计证明当前冻结来源没有明确异常触发条件、处理步骤、分支规则或恢复动作时，才写 `source_not_documented`；该状态不是领域 Claim，不填“暂无异常”等正文占位，不从“缺点”“信息不足”或其他主题来源推导异常规则。所有其他必需 section 和现有机器门必须通过后，该页可以标为页级 `published`、进入 Reader 候选并计入 `procedure_or_rule` 覆盖；异常专属问题保持 `not_answerable`，不得宣称异常处理已覆盖。来源存在但表述含糊、审计无法确定、provider 映射失败或归因失败时，不得使用该特殊状态，仍按既有 `degraded`/`not_released` 处理。
- source_type/reference/exact_excerpt: user_talk / make-decision bounded revision / “C”；“C1”。
- approval_binding: pending；本条必须由用户对最终决策卡再次明确接受后，才能替换当前 decision hash 并生成 interaction aggregate。
- facts_and_constraints: 当前真实 T013 来源审计确认 `17 智能搭建` 唯一来源只比较三种方案、优缺点和影响范围，没有异常触发/处理/分支/恢复规则；PRD 原规则要求必需 section 缺证据即 `degraded`，因此本条是唯一一次正文/section contract revision，而不是把现有实现缺陷说成 bug。页级状态仍只有 `published/degraded`，交付级仍保持 `not_released` 规则。
- Logic: 事实确实缺失 -> 继续强行写异常会编造 -> 继续整页失败会丢掉同页已有可用答案 -> 用可审计的 section 状态表达缺口 -> 只对这个可证明的来源缺口放行，其他不确定情况继续 fail-closed。
- choice_reason/impact: 保留真实可读内容，避免“来源没写”被误读为“没有异常”，同时不降低其他 section 的归因、保真、版本、近重复和语义门；影响 `procedure_or_rule` 的 section schema、正文渲染、异常题目的 answerability、Publication Gate、semantic evidence 和审计记录。
- consequences_and_risks: 机器通过不等于异常问题已回答；若来源审计规则过宽，会把 provider 映射失败伪装成来源缺失；若状态没有稳定绑定 source URI、content hash、locator/审计版本，会失去回放能力；若 Reader 文案不清楚，读者可能误以为系统保证没有异常。
- rejected_alternatives: A（保持严格缺证据即 degraded）会让同页其他已证实内容无法进入 Reader；C2（只展示/仍 degraded）不满足用户希望保留可用正文的方向；C3（Reader 可进但不计 page-type 机器覆盖）会让页面状态与语义覆盖统计分裂；把“缺点”或其他主题的异常段落拼进来会制造跨主题 Claim，违反来源边界。
- unresolved_items/owner: `source_not_documented` 的确定性审计算法、状态落盘字段、Reader 显示文案、validator 与 semantic evidence 的序列化由 Task 2-B 的 build-spec/build-plan 冻结；不得改变本条的放行边界；owner=Task 2-B。
- downstream_invariants: 后续规格必须原样保留四条硬约束：不生成“暂无异常”等正文占位；不从“缺点”“信息不足”或其他主题来源推导异常规则；`source_not_documented` 必须绑定 source URI、content hash、可回查 locator（如适用）和审计版本；无法证明来源缺失而只是映射失败、含糊或审计不完整时，仍为 `degraded`/`not_released`。这些是 D-005 的产品边界，不是实现阶段可自由删减的字段建议。
- Supersedes: D-004 仅关于“必需 section 缺证据一律 degraded”的窄规则；D-004 的样本、抽样蕴含、Task 2-C/Task 3 边界和不得临时降门槛的其余部分继续有效。

## Talk 协议和初始队列

本次对话保留用户真实回答，不改写原始话术。第一张 Talk 卡之前已经先向用户展示了问题、用户流程、页面、状态、成功/失败边界、非目标和延期范围；外部调研是否会改变方向也已按 PRD 和 Task 2-A 事实关闭。为满足 WorkflowHub 的可追溯要求，初始候选队列补录如下：

- Q-001（问题/成功标准/调研）：正文不能继续是 Evidence dump；小语料、三类页面、机器门和人工门分工均由 PRD 已回答，无需另造问题。
- Q-002（方向）：正文结构由固定骨架还是 provider 自由生成控制；由 T-001 回答。
- Q-003（范围/取舍）：来源更新采用整页还是 section 增量；由 T-002 回答。
- Q-004（失败风险）：影响关系算不清时的保守边界；由 T-003 回答。
- Q-005（延期事实）：样本、抽样蕴含和 contract revision 复用上游冻结合同；保留为 D-004/OPEN-001/OPEN-002，不临时发明数值。

Round 1 关闭 Q-001 的事实/调研轴；Round 2 收敛方向、范围和取舍；Round 3 收敛影响不确定、盲审风险和剩余延期项。原对话中的“第 1/2/3 轮”是面向用户的卡片编号，下面按 WorkflowHub 职责补齐映射；不把没有发生的用户回答写成发生过。

## 三轮 talk

| talk_id | 问题/选项 | 后果/风险 | 用户选择/原文 | 队列变化 | source/evidence |
| --- | --- | --- | --- | --- | --- |
| T-001 | Round 2 方向轴：正文采用固定骨架+受控 section、完整 PageDraft、还是纯规则拼接？ | A 稳定可验但更模板化；B 更自然但漏字段/截断风险；C 安全但不能语义 exit。 | A；用户原文："A" | Q-002 关闭；Q-003 重新成为最高未决轴。 | Talk Round 2；PRD 653–655 |
| T-002 | Round 2 范围/取舍轴：来源更新时整页重编、受影响 section 增量重编、还是新旧并存？ | A 干净但抖动；B 稳定但必须识别影响；C Reader 会混乱且更新不生效。 | B；用户原文："我想选B，但是需要注意，虽然只改受影响的section，但是需要评估哪些section受影响，尽量不要出现“旧 section 可能残留过期说法”的问题" | Q-003 关闭；Q-004 成为最高未决轴。 | Talk Round 2 |
| T-003 | Round 3 风险轴：影响范围算不清时整页重编、只降级 section、还是旧页留在 Reader？ | A 最安全但成本高；B 可能新旧不一致；C 更新不生效。 | A；用户原文："A" | Q-004 关闭；Grill/review 后无新的 high/medium 用户问题，剩余项显式进入 OPEN/RISK。 | Talk Round 3；Grill G-001 |

### 本轮规则修订 Talk（仍属于 make-decision）

本轮不是跳到下一阶段，而是针对真实来源缺口回到当前 make-decision，修订一次正文 contract。用户回答只记录原文，不把解释性文字伪装成用户回答。

| talk_id | 问题/选项 | 后果/风险 | 用户选择/原文 | 队列变化 | source/evidence |
| --- | --- | --- | --- | --- | --- |
| T-004 | `procedure_or_rule.exceptions` 没有来源证据时：A 继续整页失败；B 让它变成可选；C 保留 section 并标记来源未说明，不编造事实。 | A 丢掉同页已有可用内容；B 会掩盖结构缺口；C 需要稳定状态和审计，否则可能被误解成“没有异常”。 | C；用户原文："C" | 进入状态/机器门的第二个问题。 | make-decision Talk revision |
| T-005 | 选择 C 后，该页能否进入 Reader/机器通过：C1 其他 section 通过即可，但异常题仍 `not_answerable`；C2 只展示并保持 degraded；C3 Reader 可进但不计 page-type 机器覆盖。 | C1 保留可用内容但机器通过不代表异常已回答；C2 最保守但会丢掉同页答案；C3 会让覆盖统计和页面状态分裂。 | C1；用户原文："C1" | 方向改变问题关闭；待最终决策卡确认。 | make-decision Talk revision |

当前修订后的 clarify：`open_direction_changing_questions=0`；仍需用户对完整最终决策卡明确接受，才能完成本阶段确认绑定。

## 调研

| research_id/source | 调研重点 | 关键事实 | 处理状态 | 关联 D |
| --- | --- | --- | --- | --- |
| F-001 / PRD + Task 2-A archive | 是否需要外部调研改变方向？ | PRD 已冻结三类 page type、12–20 样本、失败状态、一次 contract revision、Task 2-C/3 延期边界；Task 2-A 已冻结 Reader Bundle contract。 | 跳过外部调研：没有发现会改变本轮方向的未知外部事实；实现阶段仍需核实真实 provider/model 和样本 manifest。 | D-001–D-004 |
| F-002 / `CONTEXT.md` + current main | 术语和现有边界是否冲突？ | Claim、fragment_locator、Reader/Audit、`published/degraded/not_released` 和信号失效已有唯一解释；本决定新增的“影响闭包”是 Task 2-B 实现术语。 | 已核对；无术语冲突。 | D-002–D-003 |
| F-003 / 冻结 Task 1 source audit + T013 v23 | `17 智能搭建` 只有一个来源，内容是三种方案的优缺点/影响范围，没有异常触发、处理、分支或恢复规则；不能跨主题拼接其他 GoInsight 文档。 | 继续按旧规则会让 procedure 页整体 degraded；放宽成“可选”又会隐藏固定 section 缺口。 | 已核对；事实支持只增加 `source_not_documented` 特殊 section 状态，不增加领域 Claim。外部调研跳过：外部事实不会改变这条本地来源边界。 | D-005 |

## grill

| grill_id | CONTEXT/冲突 | 结论 | ADR/四项退出 | source/evidence |
| --- | --- | --- | --- | --- |
| G-001 | B 的增量复用若没有 section 依赖闭包，会把旧正文、旧版本或旧归因残留到当前页面；provider 若新增无来源事实，也会绕过 claim 回查。 | 每个 section 维护依赖集合；只复用可证明未受影响的 section；影响不确定就整页重编；整页失败则 `degraded` 且旧正式页不覆盖；provider 只能在受控 section 内生成并接受 claim/source gate。 | `CONTEXT.md`: no-change；ADR: created，见 `docs/adr/0005-task2b-controlled-section-recompile.md`；hard to reverse=是，surprising without context=是，genuine trade-off=是；四项退出：上下文一致=通过，owner/接口一致=通过，失败语义明确=通过，范围/延期明确=通过。 | Grill-with-docs；`CONTEXT.md`；ADR-0005；PRD 432、443、668 |
| G-002 | C1 可能把“来源没有记录”误当成“异常不存在”，也可能让 provider 映射失败借特殊状态绕过门禁；同时现有 PRD 禁止通用“来源未说明”占位句。 | 只有确定性 source audit 命中完整的“无异常规则证据”条件时才允许 `source_not_documented`；状态绑定来源指纹和审计版本；异常题保持 `not_answerable`；所有其他缺口仍 `degraded`。这是一项 section contract revision，需消耗 `1/1`，不降低其它语义底线。 | `CONTEXT.md`: update，补充“来源未说明”与“没有异常”的区别；ADR: created，见 `docs/adr/0006-procedure-source-not-documented.md`；hard to reverse=是，surprising without context=是，genuine trade-off=是；四项退出：上下文一致=通过，owner/接口一致=通过，失败语义明确=通过，范围/延期明确=通过。 | Grill-with-docs；`CONTEXT.md`；ADR-0006；PRD 655、663、665、688；T013 v23 来源审计 |

## 审查处置

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| F-1443ba03dc96 | detail review：Grill 三项 ADR 条件均为“是”，但记录成 `not-needed`。 | 决策日志内部矛盾，后续无法知道是否应保留该取舍。 | fixed | 已创建 `docs/adr/0005-task2b-controlled-section-recompile.md`，并将 G-001 改为 `ADR: created`。 | owner=make-decision；consumer=Task 2-B；retain=保留 |
| F-1bee0c33c4b0 | detail review：三轮 Talk 的职责和初始队列未按合同呈现。 | 审查者无法确认问题/方向/风险分别收敛。 | fixed | 补录初始候选队列和 Round 1/2/3 职责映射；保留原始用户回答，不伪造回答。 | owner=make-decision；consumer=interaction aggregate；retain=保留 |
| F-5f436ba75403 | direction review：原始材料没有完整页面清单、状态枚举和 Task 2-A 交接项。 | 后续可能漏边界或重复验收。 | fixed | 已在本文「流程与边界」「延期交接」和 R-005 补齐；保留 review ref。 | owner=make-decision；consumer=build-spec/Task 2-B；retain=保留 |
| F-7a9cd9f799fd | direction review：小语料构成未在 review packet 展开。 | 可能由后续阶段临时挑样本。 | fixed | D-004 固定 12–20 篇和上游 sample coverage manifest；实际逐项清单仍须回读，不能新选。 | owner=Task 2-B；consumer=sample runner；retain=保留 |
| F-df4dceaac28b | direction review：抽样蕴含的抽样、判定和通过边界未在 packet 展开。 | 可能被重新解释为人工门或任意阈值。 | fixed | D-004 固定 seed、样本数、阈值、检测器/模型和失败项；当前只作机器诊断，详细运行值进入语义 evidence。 | owner=Task 2-B；consumer=Publication Gate/Task 2-C；retain=保留 |
| F-e9f77d51ff71 | direction review：一次 contract revision 的触发条件未写清。 | 可能静默消耗唯一修订额度。 | fixed | D-004 记录当前 `0/1` 和四类触发条件；行为 bug 不消耗。 | owner=Task 2-B；consumer=Task 2-C；retain=保留 |
| F-90de7ffefcfa | detail review：验收草案漏写“inventory 不存在的类别要有 machine fixture 或排除理由”。 | 覆盖门不够可判定。 | fixed | 已在成功边界、D-004 和本文「机器验收底线」中补上；后续验收草案必须逐字承载。 | owner=Task 2-B；consumer=semantic exit；retain=保留 |
| F-b41db5c6e091 | 当前快照 detail review：临时验收草案漏掉 `>=6`、缺类 fixture/排除理由和至少一次真实语义运行，低于已批准成功线。 | 下游可能在不足 6 个 concept、没有真实语义运行或未处理缺类时放行。 | fixed | 已将三条不可下调机器底线写入本文；后续 draft/spec 只能展开验证方法，不能降低门槛；保留当前 review ref。 | owner=make-decision；consumer=build-spec/Task 2-B semantic exit；retain=保留 |
| F-bbc7ad467844 | detail review：当前没有实现运行 evidence。 | 不能把决策阶段材料说成语义运行通过。 | accepted_risk | 这是阶段边界；实际 sample/semantic evidence 延期到 Task 2-B 运行，缺失时保持 `not_released`。 | owner=Task 2-B；consumer=semantic exit；retain=保留 |
| F-db15fea821ac | detail review：审查时最终确认仍是 pending。 | 用户若修改决定，当前材料必须重算。 | accepted_risk | 用户已接受；当前决策 hash 由 WorkflowHub confirmation 与 interaction aggregate 重新绑定。 | owner=make-decision；consumer=downstream stages；retain=保留 |
| F-e0e6107b0b27 | detail review：provider packet 无法独立验证跨仓 PRD 行号。 | review 不能把外部引用当作 packet 内证据。 | accepted_risk | 保留精确来源作为 provenance；不把 provider 未核验说成 provider 已核验，后续仍以当前仓库 PRD 为准。 | owner=downstream stage；consumer=build-spec；retain=保留 |
| REVIEW-DETAIL-RECHECK | 当前 decision-log 修订后的 detail review：`pass`；1 个异源 provider 返回有效结果，另 1 个 provider 返回 `OUTPUT_INVALID`，未把它冒充为通过。 | 当前材料已有一份真实独立 review 事实；用户确认后只需绑定当前 decision hash，不重复调用未变材料。 | fixed | 保留 attempt/result/report refs；由当前 confirmation 与 interaction aggregate 绑定当前决策。 | owner=make-decision；consumer=interaction aggregate；retain=保留 |
| F-43b46fcb7dbe | 本轮 detail review：验收草案没有逐字承载“不生成正文占位、不跨主题推导异常、状态绑定来源指纹和审计版本”三条防滥用边界。 | 下游可能把 provider 映射失败或占位文本伪装成 `source_not_documented`。 | fixed | 已在 D-005 增加 `downstream_invariants`，明确这些是产品边界；后续 spec/plan 必须原样继承；保留本轮 review report/ref，不重复审查。 | owner=make-decision；consumer=build-spec/build-plan；retain=保留 |
| F-7b63034233e7 | 本轮 detail review：D-004 的 contract revision 字段仍写 `0/1`，与当前 `1/1` 冲突。 | 下游可能误以为还剩一次修订额度。 | fixed | 已回写 D-004 为“D-005 前为 `0/1`，现已占用，当前 `1/1`（待用户确认）”；保留本轮 review report/ref，不重复审查。 | owner=make-decision；consumer=build-spec/build-plan；retain=保留 |
| REVIEW-DETAIL-C1-20260811 | 当前 C1 修订的唯一异源审查：`status=available`、`terminal_status=semantic`；有效异源 reviewer 为 `opencode/v4flash`，发现 2 个 minor，均已 fixed。`antigravity/flash` 为 `AUTHENTICATION_FAILED`，`codex/luna` 为 `SAME_SOURCE`，均按真实传输事实保留。 | 这是一份当前材料的独立质量建议，不是“所有 provider 通过”，也不要求重复审查。 | fixed | attempt=`quality/reviews/attempts/8c6c7df8-7f3d-48d2-8d40-69c489761bd9/attempt.json`；result=`quality/reviews/results/make-decision-detail-95828981cdf945f76518b0fa65fb9ccb50f093a9-8c6c7df8-7f3d-48d2-8d40-69c489761bd9.json`；report=`quality/reviews/reports/8c6c7df8-7f3d-48d2-8d40-69c489761bd9.md`；本轮后不重复。 | owner=make-decision；consumer=当前确认/interaction aggregate；retain=保留 |

## 历史确认（D-001–D-004）

- 状态：accepted
- 用户原文与 host-visible 绑定：用户最终决策卡原文“接受”；WorkflowHub confirmation 与 interaction aggregate 绑定当前 decision-log 的快照、引用和 hash。
- 未确认内容：无。OPEN-001–OPEN-003 仍是已明确延期的实现项，不是本次方向确认的缺口。

## 当前最终确认（D-005）

- 状态：pending；用户已选择 C、C1，但尚未对包含 Grill、审查事实和交接边界的完整当前决策卡再次回复“接受”。
- 当前确认范围：仅确认 `source_not_documented` 的产品方向；不提前确认具体字段名以外的实现算法、测试步骤或语义运行结果。
- interaction aggregate：待当前决策确认后，按当前四份材料和 decision hash 只生成一次；在此之前不得声称 make-decision 完成或进入 build-spec。

## 拒绝方案

| 选项 | 拒绝理由 | 关联 D |
| --- | --- | --- |
| provider 自由生成完整 PageDraft | 容易漏必需 section、增加无来源断言和截断风险 | D-001 |
| 每次来源变化都整页重编 | 页面抖动和 provider 成本较高，未充分利用未受影响 section | D-002 |
| 新旧正文并存或只把结果放 Audit | Reader 会混入过期答案，更新不真正生效 | D-002–D-003 |
| 影响不确定时只降级单个 section | 可能留下新旧 section 不一致 | D-003 |
| 临时挑样本、临时降低阈值、用 Jaccard 代替语义 exit | 违反上游冻结事实和 Task 2-B 语义边界 | D-004 |
| 把 `exceptions` 变成可选或把“缺点”改写成异常 | 隐藏固定问题或制造无来源 Claim | D-005 |
| 只展示并保持整页 degraded | 最安全，但会丢掉同页其他已经证实的可用答案 | D-005 |
| Reader 可进但不计 `procedure_or_rule` 覆盖 | 页面状态与机器覆盖统计不一致，无法形成完整样本闭环 | D-005 |

## 风险与延期交接

| risk/deferred_id | 风险或延期内容 | 触发/后果 | 处理阶段/owner |
| --- | --- | --- | --- |
| RISK-001 | section 依赖登记不完整 | 可能误复用旧正文；触发时扩大整页重编，失败则 degraded | Task 2-B / compiler + gate |
| RISK-002 | provider 生成无来源事实或截断 | 机器门拒绝，页不进 Reader；保留 Audit/Archive | Task 2-B / publication gate |
| RISK-003 | 上游 sample coverage 或实际运行 manifest 无法回读 | 不得用新 fixture 冒充，语义 exit 保持 `not_released` | Task 2-B / run evidence |
| RISK-004 | `source_not_documented` 审计过宽或 Reader 文案含糊 | 可能把“来源没写”误读成“没有异常”，或让 provider 映射失败绕过门禁 | Task 2-B / spec + compiler + gate |
| DEFER-001 | 人工读者质量门、3 个负向题、人工信号 | 本阶段不声称 reader quality | Task 2-C |
| DEFER-002 | 完整 17+3 题集、全量 89 篇、正式 released | 本阶段只做样本和机器诊断 | Task 3 |
| DEFER-003 | 文档同步、清理和归档 | 不重新打开前面任务的业务决策 | Task 3-Closeout |

## 质量边界

- 质量事实：当前有 PRD/Task 2-A 合同、三轮 Talk、规则修订 Talk、Grill、旧 direction/detail review 事实，以及 C1 修订后的唯一异源 detail review；C1 review 有 1 个有效异源 reviewer、2 个 minor finding，均已修正，并保留 `AUTHENTICATION_FAILED` 与 `SAME_SOURCE` 传输事实。任何这些事实都不等于代码已实现或语义 exit 已通过。
- 推进资格：本阶段只在用户接受当前 decision card 后生成 interaction aggregate；之后下游只能把决定转成规格/计划，不能重新发明方向。
- 完成判据：Talk/Clarify resolved、必要调研有跳过理由、Grill 完成、decision-log 当前、review findings 有处置、用户明确接受、content-addressed aggregate 写入并绑定当前 decision hash。
- 不可逆授权边界：当前不写实现、不提交代码、不合并、不发布；Task 2-B semantic exit 仍必须在实现后单独验证。

## 未决项

| item_id | 未决内容 | 原因 | 谁在何时解决 |
| --- | --- | --- | --- |
| OPEN-001 | 冻结 sample coverage manifest 的逐项 source/topic/page-type 清单和实际篇数分布 | 本文只固定上游来源和 12–20 范围，不重新选择样本 | Task 2-B 进入 build-plan/build-code 前回读，不由 build-spec 发明 |
| OPEN-002 | 具体 sampled-entailment detector/version/threshold/run budget | PRD 固定必须记录这些字段，但当前阶段不伪造运行值 | Task 2-B semantic run 前冻结并写 manifest |
| OPEN-003 | 各 page type 的具体 section 依赖字段序列化 | 这是实现合同，不改变当前方向 | Task 2-B specification/implementation |
| OPEN-004 | `source_not_documented` 的确定性审计输入、证据结构、状态投影和 Reader 文案 | 当前只冻结放行边界，不在 make-decision 发明实现字段；必须防止把映射失败伪装成来源缺失 | Task 2-B build-spec/build-plan；不能降低 D-005 |

## Supersedes

- D-004 的“必需 section 缺证据一律 degraded”仅在 `procedure_or_rule.exceptions` 的 D-005 特殊状态范围内被窄化；D-004 的样本、抽样蕴含、Task 2-C/Task 3 边界和不得临时降门槛的其余部分继续有效。Task 2-A 的 Reader Bundle contract 继续有效；本任务已使用 PRD 允许的一次正文/section contract revision，当前为 `1/1`，待用户确认。

## 文档结果

- CONTEXT.md：updated；新增 `source_not_documented` 的唯一解释，明确它不是“没有异常”、不生成 Claim，且只适用于 `procedure_or_rule.exceptions`。
- ADR：created；`docs/adr/0005-task2b-controlled-section-recompile.md` 记录 section 增量更新和整页保守兜底；`docs/adr/0006-procedure-source-not-documented.md` 记录本轮唯一的来源缺口放行规则；两份状态均为 proposed，最终接受绑定仍由本阶段决定。
- ADR criteria：hard to reverse=是；surprising without context=是；genuine trade-off=是；三项均成立，因此已创建 ADR。
- 术语/ADR 冲突及处理：旧 PRD/决策曾禁止“来源未说明”正文占位，本轮没有把它写成正文占位，而是新增 section 状态并明确不生成 Claim；Task 2-A 的结构合同与本任务的正文更新策略正交，旧 Reader/Audit 分离 ADR 继续适用。
- 不复制 spec 的边界：本文只保留需求索引、决策理由、边界、风险和交接；页面字段、测试步骤和实现任务留给后续正式规格/计划。

## Exit checks

- 上下文一致：通过；与 `CONTEXT.md`、PRD v1.7 和 Task 2-A Reader Bundle contract 一致。
- owner/接口一致：通过；Task 2-B 负责正文编译和机器门，Task 2-C 负责人工读者门，Task 3 负责全量和 released。
- 失败语义明确：通过；不确定影响整页重编，失败 degraded，旧 formal 不覆盖，整包 not_released。
- 范围与延期明确：通过；全量、人工门、正式 release、数据库/图谱和永久人工系统均明确延期或不做。
- 当前修订确认：待用户确认 D-005；确认前不生成 interaction aggregate，不进入 build-spec。

## Scope revision：SR-20260811-task2b-procedure-source-gap

- **状态**：`in_progress`；沿用当前 task，不创建 successor task、不重跑完整五阶段、不改写历史 receipt。
- **触发阶段 / 返回阶段**：`verify-code` → 受影响的 `build-code`。原因是这次新增的是已实现正文合同的产品行为，既影响 spec/plan/tasks，也影响 compiler、validator、测试和语义出口；不从头回到 Task 2-A 或重新规划无关内容。
- **原始需求**：Task 2-B 要让三类主题页正文可读、可回查、失败明确降级，并避免来源更新后旧 section 残留过期说法。
- **为什么现在修订**：T013 v23 的真实来源审计证明 `procedure_or_rule.exceptions` 的缺口来自冻结材料本身，不是 provider mapping bug；继续强行填异常会编造事实，继续整页失败又会丢掉同页已有可用内容。
- **本次新增方向**：沿用 D-005/C1：固定保留 `exceptions` section；仅在确定性来源审计证明来源没有异常触发、处理、分支或恢复规则时使用 `source_not_documented`；不生成 Claim、不写占位句、不跨主题推导；异常题保持 `not_answerable`；其他 section 和现有机器底线通过时，页面可进入 Reader/机器覆盖统计；含糊、审计不完整、provider 映射或归因失败仍 `degraded/not_released`。
- **受影响 ID**：`PFACT-007`、`R-004`、`D-004`、`D-005`、`FR-DRAFT-001`、`FR-DRAFT-004`、`FR-PUBLISH-002`、`FR-PUBLISH-003`、`FR-PUBLISH-006`、`FR-SEM-003`、`AC-02`、`AC-07`、`AC-09`、`AC-11`、`AC-12`、`AC-13`、`T009`、`T010`、`T013`、`T014`、`T015`、`T016`。
- **影响评估**：用户流程增加“来源审计 → exceptions 特殊状态/失败”的分支；数据状态增加 section-level `source_not_documented` 与题目 `not_answerable` 的组合；成功边界只放宽这一来源缺口，不降低 `>=6`、三类 page type、归因、保真、版本、重复和交付 `not_released` 门；失败边界继续 fail-closed；实现/测试/审查/交付都必须绑定来源 URI、content hash、locator（如适用）和审计版本。
- **四份材料变更**：`decision-log.md` 追加本记录并保留 Talk/Grill/审查原始事实；`spec.md` 只补受影响的场景、状态、FR、AC、风险和 revision note；`plan.md` 只补受影响设计、测试、返回阶段和 traceability；`tasks.md` 只追加受影响的 T015/T016 执行、测试和证据卡，不重开 T001–T014。
- **非目标与延期**：不新增 page type、Reader Bundle、CLI、provider、数据库、人工读者门、Task 3 released 或新的永久状态机；完整样本覆盖、真实语义出口和人工确认继续按原有边界记录，不因本修订伪造通过。
- **沟通事实**：Talk/Clarify/Grill 由主代理完成；用户原始选择为 `C`、`C1`，本次用户指令为“请用scope_revision流程增加需求，不要从头开始！”。不把 review verdict 或实现结果当作用户确认。
- **宪法检查**：同一 task、四份材料一致、只改受影响范围、旧事实只读保留、失败不伪造成功、不新增控制面、不泄露凭据；均保持。
- **审查状态**：当前 main 的 `wh-review` 明确不再接受 `materials.scope_revision`，旧专用 route 已被移除；不能伪造专用 review。现有 C1 detail review 只作为相邻质量事实，不冒充 scope_revision review；专用审查缺失继续记录为 `incomplete/unavailable`，不阻止同 task 材料修订，但不能声称 scope revision 已正式闭合。
- **返回交接**：材料修订完成后回到 `build-code`，只执行 T015 的受影响 `procedure_or_rule.exceptions` 状态、gate、测试，再由 T016 更新 T013/T014 证据；不重跑已完成的无关卡片，不调用 `close`。
