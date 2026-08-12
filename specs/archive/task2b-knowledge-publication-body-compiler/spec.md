# 功能规格：Task 2-B — 类型化知识正文编译闭环

> `content_profile: "spec-content.v3"`
>
> 基于当前已接受的 `decision-log.md`。本文件只写用户能看到的行为、状态、边界和验收，不写实现顺序、工程命令或代码方案。

- **功能名**：Task 2-B 类型化知识正文编译闭环
- **来源**：当前任务 root `decision-log.md` 的 R-001–R-005、D-001–D-005；本次 `SR-20260811-task2b-procedure-source-gap`；PRD v1.7 Task 2-B
- **状态**：草稿

## 速读卡（30 秒）

- **一句话需求**：把小语料里的知识主题从 Evidence 堆叠变成读者能直接理解、每条事实都能回查、出错时明确降级的三类主题页。
- **核心改动点**：
  - 固定三类主题页的结构，正文生成只能填受控内容。
  - 来源变化先判断影响范围；能证明安全才复用 section，不确定就整页重编。
  - 通过机器门的页面才能进 Reader；失败页面留在 Audit/Archive，整包不发布。
- **最大影响面**：Task 2-A 已冻结的 Reader Bundle、主题导航、来源/Claim 回查和旧正式页面更新行为。
- **验收信号**：至少 6 个机器通过主题，三类各至少 1 个；失败和不确定状态可见；没有过期 section 混入当前 Reader。

## 来源与决策映射

| Source ID | Decision ID | FR / AC IDs | Status / affected scope | Unresolved / handoff |
| --- | --- | --- | --- | --- |
| R-001 | D-001–D-004 | FR-FLOW-001、FR-DRAFT-001、AC-01、AC-12 | current / WorkflowHub 阶段边界 | 不由 build-spec 或实现阶段补产品决策 |
| R-002 | D-001–D-004 | FR-DRAFT-001、FR-PUBLISH-003、AC-02、AC-07 | current / Talk 取舍与记录边界 | 用户确认已完成；实现证据延期到 Task 2-B |
| R-003 | D-001–D-004 | SCN-001–SCN-008、AC-01–AC-12 | current / 流程、页面、状态和边界 | 具体任务拆解交给 build-plan |
| R-004 | D-001–D-004 | FR-FLOW-001–FR-PUBLISH-005、FR-SEM-003、AC-01–AC-12 | current / 正文编译与机器出口 | 真实运行值进入 Task 2-B 证据 |
| R-005 | D-001–D-004 | FR-COMPAT-001、FR-PUBLISH-001、AC-03、AC-07 | current / 继承 Task 2-A Reader Bundle | 用户已确认完成；机器回读仍是 Task 2-B 前置事实 |
| D-001 | D-001 | FR-DRAFT-001、FR-DRAFT-002、FR-PUBLISH-001、AC-02、AC-03 | current / 固定骨架和受控正文 | 各 page type 的 section 内容矩阵由 Task 2-B 规格细化，不改骨架原则 |
| D-002 | D-002 | FR-DRAFT-003、FR-PUBLISH-002、AC-05 | current / 影响闭包和安全复用 | 依赖字段的具体序列化由 build-plan 冻结 |
| D-003 | D-003 | FR-DRAFT-003、FR-PUBLISH-003、AC-06、AC-07 | current / 不确定时整页重编和失败保护 | 不接受只降级不确定 section |
| D-004 | D-004 | FR-SEM-001–FR-SEM-003、AC-09–AC-12 | current / 样本、语义运行和机器出口 | OPEN-001–OPEN-003 由 Task 2-B 执行阶段关闭 |
| D-005 / SR-20260811-task2b-procedure-source-gap | D-005 | FR-DRAFT-001、FR-DRAFT-004、FR-PUBLISH-002/003/006、FR-SEM-003、AC-02、AC-07、AC-09、AC-11、AC-13 | current / `exceptions` 来源缺口特殊状态；只影响 procedure page 的 section、题目可答性和机器覆盖解释 | OPEN-004 由 build-spec/build-plan 冻结审计输入与落盘字段；返回 build-code |

### 决策分类（build-spec 不重新开产品决策）

| 分类 | 当前 ID | 本规格如何处理 |
| --- | --- | --- |
| `locked` | D-001、D-002、D-003、D-004、D-005 | 已接受的方向和本次 scope revision 原样落到 FR/AC；下游只能实现和验证，不能改选项、顺序或机器底线。 |
| `unresolved` | OPEN-001、OPEN-002、OPEN-003 | 是执行阶段的输入、配置和依赖表达交接，不是新的产品方向；由 build-plan/build-code 关闭，不能在本阶段猜测。 |
| `newly discovered ambiguity` | 当前无 | 本阶段没有发现需要重新选择产品方向的新歧义；若下游发现会改变范围、页面合同或发布边界的歧义，必须回到 make-decision。 |

每条 FR 和 AC 都在本表或后续对应 ID 处绑定了当前决策；本次新增只来自 `SR-20260811-task2b-procedure-source-gap`，不重开未受影响的产品方向。

## 1. 问题与紧迫性

Task 2-A 已把 Reader Bundle 的入口、主题身份、页面结构和回查骨架固定下来，但骨架本身不会替读者回答问题。如果正文继续直接堆 Evidence，读者需要自己从来源片段、表格和版本差异中拼答案；一旦来源更新，旧 section 还可能留在页面里，读者无法判断哪些说法已经过期。

Task 2-B 要在已有 Reader Bundle 上补齐“小语料、类型化、可回查、可失败”的正文行为。现在处理可以让 Task 2-C 的人工读者门和 Task 3 的全量发布建立在稳定的机器出口上；本期不把机器通过说成人工质量，也不把失败结果伪装成发布成功。

## 2. 背景、目标与范围

### 背景

- 输入来自已冻结的来源快照、Task 1 TopicIndex、样本覆盖记录和 Task 2-A Reader Bundle 合同。
- 页面需要同时服务两类人：直接读主题页的读者，以及需要按来源和 Claim 回查的维护者/Agent。
- 同一个主题页可能由多个来源、多个版本、表格、图片或双语片段共同组成；页面不能只依赖一个来源摘要。
- 正式 Reader 入口和 Audit/Archive 不是同一层：Reader 给当前可读答案，Audit/Archive 保存失败原因、完整 Claim/Evidence、旧正文和恢复依据。

### 目标

- 让三类主题页能用清楚的正文回答主题问题，而不是复制 Evidence。
- 让每条进入 Reader 的事实都能回查到唯一 Claim、来源 URI、内容指纹和片段位置。
- 让来源更新、影响不确定、provider 失败和证据不足都产生可解释状态，不留下悄悄过期的旧 section。
- 在小语料机器出口上证明方向成立，为 Task 2-C 人工读者门和 Task 3 全量发布提供稳定输入。

### 范围内

- `product_overview`、`module_or_capability`、`procedure_or_rule` 三类主题页。
- Structure Normalizer 对标题、层级、FAQ、表格、图片、双语、版本和噪声的可追溯整理。
- TopicIndex 到 page type、主题身份和 Reader 目标的确定性映射。
- 固定页面骨架、受控 section 正文、正文与 Evidence/archive 的分离。
- section 影响闭包、安全复用、整页重编和旧正式页保护。
- OKF Concept Compiler 对正文、来源、Claim footnote、frontmatter 和导航的产品级投影。
- Publication Gate 的归因、保真、重复和失败状态。
- 超长主题按语义边界拆分、正文/整页行数上限、主题总览和 `prev/next` 关系。
- 冻结的 12–20 篇代表样本、真实语义运行和 Task 2-B 机器出口。

## 3. 用户场景与状态覆盖

### SCN-001：操作者生成小语料主题页

- **角色**：知识库操作者
- **Given**：输入快照、TopicIndex、样本覆盖记录和 Task 2-A Reader Bundle 合同可回读。
- **When**：运行一次 Task 2-B 正文编译。
- **Then**：每个主题先经过结构整理和类型映射，再生成受控正文、回查信息和页面状态；通过机器门的页面才出现在 Reader 导航。

### SCN-002：读者打开单来源完整主题

- **角色**：知识读者
- **Given**：主题属于三类 page type 之一，来源内容完整且机器门通过。
- **When**：从 Reader 导航进入主题页。
- **Then**：先看到可读正文，再能按页面内来源标记回查原始片段；不需要阅读完整 Evidence 才能理解主题结论。

### SCN-003：多源同产品主题合并

- **角色**：知识读者、维护者
- **Given**：多个来源描述同一产品或模块，内容可能有版本差异。
- **When**：编译主题页。
- **Then**：正文只写能被来源和 Claim 支持的共同或分版本事实；每条事实保留来源归属，冲突或无法闭合的部分进入 Audit，不被默默合并。

### SCN-004：长文、表格、图片和双语来源

- **角色**：知识读者
- **Given**：来源包含长段落、表格、图片链接/alt、双语内容或版本信息。
- **When**：结构整理并生成正文。
- **Then**：正文保留这些内容对读者有用的语义；命令、端口、配置、数字、标识符、版本、表格和图片归属都能回查；无法确认时页面降级。

### SCN-005：来源更新且影响范围明确

- **角色**：知识库操作者
- **Given**：某些来源、Claim、版本或结构关系变化。
- **When**：更新已有主题页。
- **Then**：系统计算受影响 section 的依赖闭包；仅复用依赖、归因和版本都未变的 section，受影响 section 重新生成，页面不会混入已知过期说法。

### SCN-006：影响范围无法证明

- **角色**：知识库操作者
- **Given**：依赖登记不完整、版本/结构关系不明或归因无法证明。
- **When**：更新主题页。
- **Then**：扩大到整页重编；整页重编失败时页面为 `degraded`，旧 Reader 正式页不被失败结果覆盖。

### SCN-007：正文或 provider 失败

- **角色**：知识库操作者、知识读者
- **Given**：必需证据缺失、provider 失败、返回截断/不可解析内容、fallback 或机器门失败。
- **When**：编译或发布检查结束。
- **Then**：页面为 `degraded`，失败原因、输入指纹和恢复依据保留在 Audit/Archive；页面不进入正式导航，交付级保持 `not_released`。

### SCN-008：重复运行和机器出口

- **角色**：知识库操作者、质量维护者
- **Given**：冻结样本覆盖和运行配置可用。
- **When**：对小语料执行真实语义运行并检查出口。
- **Then**：结果记录 provider/model/预算、样本覆盖、失败项和归因；至少 6 个 concept 通过机器门，三类各至少 1 个；不满足时不声称发布或人工质量。

### SCN-009：来源没有记录异常规则

- **角色**：知识库操作者、知识读者
- **Given**：主题是 `procedure_or_rule`，确定性来源审计证明冻结来源没有明确异常触发、处理、分支或恢复规则。
- **When**：正文编译和机器门完成。
- **Then**：固定 `exceptions` section 保留 `source_not_documented` 状态，不生成异常 Claim，不写“暂无异常”等占位句；异常专属题目为 `not_answerable`。其他必需 section 和既有机器门通过时，页面仍可为 `published` 并计入 `procedure_or_rule` 覆盖；审计不确定、来源含糊、provider 映射失败或归因失败时仍为 `degraded`。

### 状态覆盖清单

- [x] **默认态**：SCN-001、SCN-002；页通过机器门后为 `published`，交付仍为 `not_released`。
- [x] **空态**：SCN-004、SCN-007；无正文、无必需证据或无法形成有效主题时为 `degraded`，不生成占位正文。
- [x] **错误态**：SCN-006、SCN-007；影响不确定、provider 失败、截断、归因断链或保真失败均显式降级。
- [ ] **加载态**：N/A — 本期是人工触发的本地批处理，没有面向读者的在线加载界面。
- [x] **取消态**：SCN-007；执行中止或语义运行未完成时不写成成功，保留已有正式页和失败审计。
- [x] **边界态**：SCN-003、SCN-004、SCN-008；多源、长文/表格/图片/双语、三类覆盖、`>=6` 和缺类 fixture/排除理由均有出口。
- [ ] **权限态**：N/A — 本期没有用户权限模型；权限系统不属于 KnowledgeDigest 产品边界。
- [x] **竞态态**：SCN-005、SCN-006；同一页更新时依赖或来源快照不稳定则扩大重编或失败，不拼接两次结果。
- [x] **来源缺口态**：SCN-009；`source_not_documented` 只属于 `procedure_or_rule.exceptions`，不改变页级 `published/degraded` 枚举，也不等于“没有异常”。

## 4. 产品事实与假设（PFACT）

- **PFACT-001**：固定骨架、受控 section、影响闭包和整页兜底已经是当前接受的产品方向。
  - **status**：`verified`
  - **证据或来源**：当前 `decision-log.md` D-001–D-003；用户最终确认已绑定当前决策快照。
  - **关联**：FR-DRAFT-001、FR-DRAFT-003、AC-02、AC-05、AC-06。

- **PFACT-002**：Task 2-B 只负责小语料三类 page type 的机器正文编译和机器出口；人工读者门与正式全量发布属于后续阶段。
  - **status**：`verified`
  - **证据或来源**：当前 `decision-log.md` R-004、D-004；PRD v1.7 Task 2-B/2-C/3 边界。
  - **关联**：FR-SEM-001–FR-SEM-003、FR-PUBLISH-003、AC-09–AC-12。

- **PFACT-003**：Task 2-A Reader Bundle、主题身份和入口合同是本期的上游输入，不在本期重设计。
  - **status**：`inferred`
  - **证据或来源**：当前 `decision-log.md` R-005 和 Task 2-A archive；限制是本期仍需在执行前回读机器证据和当前 artifact。
  - **关联**：FR-COMPAT-001、FR-PUBLISH-001、AC-03、AC-07。

- **PFACT-004**：Task 1 inventory 中各类别的实际分布、冻结 12–20 篇逐项清单和不存在类别的 fixture/排除记录尚未在本阶段逐项回读。
  - **status**：`unknown`
  - **owner、影响**：owner=Task 2-B build-plan/build-code；影响 AC-09、AC-10、AC-11；关联 OPEN-001、RISK-003。

- **PFACT-005**：语义运行使用的 provider/model、检测器、阈值和预算尚未在本阶段冻结。
  - **status**：`unknown`
  - **owner、影响**：owner=Task 2-B build-plan/build-code；影响 AC-10、AC-11；关联 OPEN-002、RISK-002。

- **PFACT-006**：具体 section 依赖字段和影响闭包的可审计表达尚未冻结。
  - **status**：`unknown`
  - **owner、影响**：owner=Task 2-B build-plan/build-code；影响 FR-DRAFT-003、AC-05、AC-06；关联 OPEN-003、RISK-001。

- **PFACT-007**：真实 T013 v23 来源审计确认 `17 智能搭建` 的唯一冻结来源没有明确异常触发、处理、分支或恢复规则；该事实支持来源缺口状态，不支持任何异常领域 Claim。
  - **status**：`verified`
  - **证据或来源**：`apply/evidence/T013.semantic-run-v23.json` 及 `tasks.md` 的 T013 来源审计追加事实；来源 URI、content hash 和主题唯一来源关系已核对。
  - **关联**：FR-DRAFT-004、FR-PUBLISH-006、FR-SEM-003、AC-13、RISK-005。

## 5. 功能需求

### 用户流程与输入整理（FLOW）

Task 2-B 的用户可见流程是“读取冻结输入 → 整理结构 → 确定主题和类型 → 生成受控正文 → 回查和机器门 → Reader 或 Audit/Archive”。每个中间结果都必须能解释为什么进入下一步或为什么停在失败状态。

- **FR-FLOW-001**：编译流程必须先使用冻结输入和 Reader Bundle 合同，再产生主题正文；输入缺失、指纹不一致或主题身份无法闭合时不得进入正式 Reader。
  - **范围边界**：本期只定义用户结果和状态，不规定具体读取命令、类名或任务顺序。
  - **依据**：R-003、R-004、D-004、PFACT-001–003。
  - **场景**：SCN-001、SCN-007。
  - **验收**：AC-01、AC-07。

- **FR-FLOW-002**：每个来源片段必须保留可回查的结构关系和来源位置；无法保留关系的片段进入 Audit 或被明确排除，不能变成没有出处的正文事实。
  - **范围边界**：结构整理只描述来源中已有信息，不自行补充主题事实。
  - **依据**：R-004、D-001、PFACT-002。
  - **场景**：SCN-003、SCN-004。
  - **验收**：AC-01、AC-03、AC-04。

### 主题类型与正文（DRAFT）

- **FR-DRAFT-001**：主题页必须属于且只能属于 `product_overview`、`module_or_capability`、`procedure_or_rule` 三类之一；每类页面按下方固定矩阵生成必需/可选 section，来源字段和状态字段沿用 Task 2-A 页面合同。
  - **范围边界**：不新增 page type；未映射或冲突的主题不进入正式 Reader。
  - **依据**：R-004、D-001、PFACT-001–002。
  - **场景**：SCN-001、SCN-003。
  - **验收**：AC-02、AC-07。

#### 三类 page type 的 section 矩阵（v1-draft）

以下是 PRD 已列明的页面必需内容，不新增页面类型或第二套模板。“可选”只表示来源有证据时可以补充；没有证据就省略，不能写占位句。未列出的 section 不属于本期正文合同。三类页面共同保留稳定主题身份、page type、页级状态、来源/Claim 回查和导航投影等非 provider 自由扩展的页面元数据。

| page type | 必需 section | 可选 section |
| --- | --- | --- |
| `product_overview` | 定位、适用场景、能力边界、入口、来源 | 版本（仅来源有可回查版本时） |
| `module_or_capability` | 目的、能力、入口/前置、关系、限制、版本、来源 | 无额外固定正文 section；可选来源字段按 Task 2-A 合同省略 |
| `procedure_or_rule` | 前置、步骤/规则、异常、限制、版本、来源 | `exceptions` 在确定性来源审计确认来源没有异常规则时可有 `source_not_documented` section 状态；不是可选 section |

`module_or_capability` 和 `procedure_or_rule` 的“版本”在来源声明版本相关行为时必须有可回查证据；没有来源版本事实时不得猜测版本或 `stale_after`，按版本 oracle 和页面状态规则处理。

- **FR-DRAFT-002**：正文必须用读者能理解的方式表达主题结论；Evidence、完整 Claim、原文和表格/图片证据继续保留在 Evidence/archive，不把证据堆直接当成正文。
  - **范围边界**：provider 只能填写受控正文，不得自行增加 section、page type、来源字段或没有来源支持的新事实。
  - **依据**：R-004、D-001、PFACT-001。
  - **场景**：SCN-002、SCN-003、SCN-004。
  - **验收**：AC-02、AC-03、AC-04。

- **FR-DRAFT-003**：来源、Claim、版本或结构关系变化时，系统必须计算影响闭包；只有依赖集合、归因和版本均可证明未变的 section 才能复用，受影响 section 必须重编，不能把新旧正文直接拼接。
  - **范围边界**：影响关系无法证明时按整页处理，不允许只留下不确定的旧 section。
  - **依据**：R-004、D-002、D-003、PFACT-001、PFACT-006。
  - **场景**：SCN-005、SCN-006。
  - **验收**：AC-05、AC-06。

- **FR-DRAFT-004**：`procedure_or_rule.exceptions` 必须始终存在；只有确定性来源审计证明冻结来源没有明确异常触发、处理、分支或恢复规则时，才能使用 section-level `source_not_documented`。该状态不生成领域 Claim、不写正文占位句、不跨主题推导异常规则，并绑定 source URI、content hash、可回查 locator（如适用）和审计版本；异常专属题目保持 `not_answerable`。
  - **范围边界**：来源含糊、审计不完整、provider 映射失败、归因失败或其他必需证据缺失不属于该状态，仍按 `degraded/not_released` 处理。
  - **依据**：D-005、SR-20260811-task2b-procedure-source-gap、PFACT-007。
  - **场景**：SCN-009。
  - **验收**：AC-13。

### 回查与发布状态（PUBLISH）

- **FR-PUBLISH-001**：进入 Reader 的主题页必须同时保留可读正文、页面类型、稳定主题身份、来源标记、Claim 标记和到 Evidence/archive 的回查关系；导航只指向当前通过机器门的页面。
  - **范围边界**：Task 2-A 已冻结的 Reader Bundle 结构和主题身份不被本期重命名或另建一套入口。
  - **依据**：R-005、D-001、PFACT-003。
  - **场景**：SCN-001、SCN-002、SCN-003。
  - **验收**：AC-03、AC-07。

- **FR-PUBLISH-002**：机器门必须检查事实归因、数字/标识符/版本、命令/端口/配置、表格/图片、重复和负向样本；版本按“既有托管 metadata → 来源 frontmatter/显式 metadata → 明确的版本标题/字段”选择，只接受 semver、日期版本或来源明确的 release label。多个版本不一致或无法解析时页级 `degraded`；`product_overview` 可在来源确实没有版本信息时省略，其他两类在来源声明版本相关行为时必须有可回查版本证据；`stale_after` 只能来自来源明确的有效期/复核日期。质量 oracle 固定为：连续逐字来源块最多 3 个句子或 240 个字符（代码块、表格、双语配对、公共模板段落和带 attribution 的短引除外）；同页或跨页 section 的 5-gram Jaccard ≥0.92 且正文长度超过 80 字符时视为近重复并阻断，公共模板、代码、表格和双语配对按 fixture 规则排除；golden-negative fixture 必须稳定失败并保持 `degraded/not_released`，每项记录分母、检测器版本、seed 和失败样本。任何关键检查失败时页面不能成为正式 Reader 答案。
  - **范围边界**：本期不设全局正文复制率硬门，不以 provider 成功或写回成功替代事实检查。
  - **依据**：R-004、D-001、D-004。
  - **场景**：SCN-003、SCN-004、SCN-007。
  - **验收**：AC-03、AC-04、AC-12。

- **FR-PUBLISH-003**：页级 `published` 和 `degraded`、交付级 `not_released` 必须分开表达；`degraded` 页面保留失败原因、输入指纹、完整证据和恢复依据，但不出现在正式导航。
  - **范围边界**：本期不把任何机器出口写成 `released` 或人工读者质量通过。
  - **依据**：R-004、D-003、D-004、PFACT-002。
  - **场景**：SCN-006、SCN-007、SCN-008。
  - **验收**：AC-06、AC-07、AC-11。

- **FR-PUBLISH-006**：`source_not_documented` 是 section-level 事实状态，不新增页级状态或交付状态。若该状态经过确定性审计并且其他必需 section/机器门通过，页面可以 `published`、进入 Reader 候选并计入 `procedure_or_rule` page-type 覆盖；这不表示异常问题已回答。审计不确定或状态无法回查时，页面必须 `degraded`。
  - **范围边界**：不降低 `>=6` concept、三类 page type、来源归因、关键事实保真、重复、版本和 `not_released` 交付底线。
  - **依据**：D-005、FR-DRAFT-004、PFACT-007。
  - **场景**：SCN-009。
  - **验收**：AC-07、AC-11、AC-13。

- **FR-PUBLISH-004**：来源或页面内容变化后，受影响内容的旧信号和旧归因不得继续被当作当前事实；未变化且可证明安全的 section 才能保留其有效状态。
  - **范围边界**：本期不设计新的信号体系；沿用 Task 2-A 已冻结的状态和失效规则。
  - **依据**：R-005、D-002、PFACT-003。
  - **场景**：SCN-005、SCN-006。
  - **验收**：AC-05、AC-06。

- **FR-PUBLISH-005**：主题正文超过单页容量时，必须先按产品、模块、能力、步骤或问题边界做语义拆分，再按行数分页；正文最多 120 行，整页（含来源和引用）最多 300 行。同一主题族必须保留总览页、稳定相关 key 和 `prev/next` 导航；每个有效 Claim 必须且只能进入一个 part，`part-1` 不能代替主题主入口。
  - **范围边界**：本期不允许为了通过行数门把主题按任意字符切碎，也不允许丢失、重复 Claim 或生成无入口 part。
  - **依据**：R-004、D-001、PFACT-001–003；PRD v1.7 Task 2-B 超长拆分和页面尺寸合同。
  - **场景**：SCN-001、SCN-004、SCN-008。
  - **验收**：AC-04、AC-08。

### 样本与语义出口（SEM）

- **FR-SEM-001**：机器验证必须使用上游冻结的 12–20 篇代表样本和覆盖记录，不允许编译器临时挑选样本；样本必须按实际 inventory 覆盖多源、长文、表格/图片、双语等类别。Task 2-B 的题集诊断必须使用 Task 0 冻结的 17+3 题集派生出的确定性 answerability 可答子集，记录首次命中、证据回查、section 完整性和失败原因；不得为了实现方便临时删题或换题。
  - **范围边界**：样本或 answerability 标签缺失、覆盖不完整或不存在类别没有 fixture/排除理由时，不降低门槛继续宣称通过；完整 17+3 题集和人工读者门仍属于后续阶段。
  - **依据**：R-004、D-004、PFACT-004。
  - **场景**：SCN-004、SCN-008。
  - **验收**：AC-09、AC-10。

- **FR-SEM-002**：至少一次真实语义运行必须留下冻结 provider/model/预算、抽样 seed、样本数、判定阈值、检测器/模型版本、样本范围、归因、失败项和运行状态；provider 失败、截断、fallback、Jaccard-only 或证据不足都必须保持 `not_released`。
  - **范围边界**：本期不把离线结构基线或 Jaccard 结果当成语义出口，不建立长期候选队列或人工复核系统。
  - **依据**：R-004、D-004、PFACT-002、PFACT-005。
  - **场景**：SCN-007、SCN-008。
  - **验收**：AC-10、AC-11。

- **FR-SEM-003**：Task 2-B 的机器成功底线是至少 6 个 `machine-passing concept`，三类 page type 各至少 1 个；`procedure_or_rule` 允许在 `exceptions=source_not_documented` 且其他必需 section/机器门通过时计入 page-type 覆盖，但异常题仍 `not_answerable`；实际 inventory 中存在的类别必须覆盖，不存在的类别必须有 machine fixture 或明确排除理由。
  - **范围边界**：这只是机器出口，不等同于 Task 2-C 人工读者质量，也不等同于 Task 3 正式 released。
  - **依据**：D-004、当前 decision-log「机器验收底线」、PFACT-004–005。
  - **场景**：SCN-008。
- **验收**：AC-09、AC-11、AC-13。

### 兼容和更新（COMPAT）

- **FR-COMPAT-001**：正文编译必须兼容 Task 2-A 已冻结的 Reader Bundle、主题身份、导航入口、来源/Claim 回查和旧正式页面保护；本期只新增正文行为，不建立第二套 Reader 入口。
  - **范围边界**：旧正式页面保留历史价值；当前导航是否展示由本期页面状态和影响结果决定，不直接删除旧页面。
  - **依据**：R-005、D-001–D-003、PFACT-003。
  - **场景**：SCN-001、SCN-005、SCN-006。
  - **验收**：AC-03、AC-05、AC-06、AC-07。

## 6. 模块划分

### Structure Normalizer

- **负责什么**：把来源中的层级、标题、FAQ、表格、图片、双语、版本和噪声整理成可追溯结构。
- **对外提供什么**：带来源位置和父子关系的结构片段；无法解释的片段带失败或排除原因。
- **依赖谁**：冻结来源快照和内容身份。
- **测试边界**：SCN-004 中的结构覆盖与 AC-01、AC-04。

### TopicIndex 与 page type 映射

- **负责什么**：确定主题身份、产品/模块关系和三类 page type。
- **对外提供什么**：稳定主题入口和唯一 page type；冲突或未映射结果进入 Audit。
- **依赖谁**：Task 1 TopicIndex、Task 2-A Reader Bundle 合同。
- **测试边界**：SCN-001、SCN-003 与 AC-02、AC-07。

### PageDraft

- **负责什么**：按固定 page type 骨架组织读者正文，并标出每个 section 的来源、Claim、版本和结构依赖。
- **对外提供什么**：可读、受控、可回查的 section 草稿；影响不确定时要求整页重编。
- **依赖谁**：结构片段、TopicIndex 和允许使用的 Claim/Evidence。
- **测试边界**：SCN-002、SCN-005、SCN-006 与 AC-02、AC-05、AC-06。

### OKF Concept Compiler

- **负责什么**：把通过编译和校验的正文投影为 Task 2-A Reader Bundle 可消费的主题页、来源/Claim 回查和导航关系。
- **对外提供什么**：Reader 页面或 Audit/Archive 结果，不产生第二套导航事实。
- **依赖谁**：PageDraft、Reader Bundle 合同和 Publication Gate 结果。
- **测试边界**：SCN-001、SCN-002、SCN-007 与 AC-03、AC-07。

### Publication Gate

- **负责什么**：检查归因、保真、版本、重复、负向样本和页面状态，决定是否进入 Reader。
- **对外提供什么**：可解释的 `published`/`degraded` 页级结果和 `not_released` 交付状态。
- **依赖谁**：编译结果、样本运行证据和失败原因。
- **测试边界**：SCN-003、SCN-007、SCN-008 与 AC-04、AC-07、AC-09–AC-12。

### UI 设计审查

N/A — 本期交付是本地 Markdown/Reader Bundle 的产品行为和机器门，不新增 Web/App 页面、交互组件、视觉布局或响应式界面；Reader 的可读性通过内容和导航验收，不引入 UI 设计合同。

## 7. 关键实体

- **结构片段**：来源中的可追溯内容单元；包含来源身份、位置、父子关系、内容类型和版本线索。
- **主题页草稿**：一个稳定主题和 page type 的受控正文集合；每个 section 关联其依赖集合和归因集合。
- **Section 影响记录**：描述来源、Claim、版本、结构关系变化如何影响 section；依赖或归因无法证明时标记为需整页重编。
- **来源缺口状态记录**：只描述 `procedure_or_rule.exceptions` 的确定性来源审计结果；包含来源 URI、content hash、可回查 locator（如适用）、审计版本、`source_not_documented` 状态和异常题 `not_answerable` 结果，不是领域 Claim。
- **正文事实回查记录**：正文中的一个可核验事实，关联唯一 `claim_id`、source URI、内容指纹和 `fragment_locator`。
- **页面发布结果**：页级 `published` 或 `degraded`，带验证原因、输入身份和 Reader/Audit 去向。
- **语义运行结果**：一次冻结 provider/model/预算下的样本运行，包含覆盖、通过概念数、失败项、归因和交付级状态。

## 8. 数据和生命周期

- **数据粒度**：来源以结构片段为输入，主题以 page type 为编译单位，正文以 section 为更新单位，机器出口以 concept 和一次语义运行记录为验收单位。
- **数据时效**：来源、Claim、版本或结构关系变化会使受影响 section 和相关旧信号失效；只有依赖闭包证明未变的 section 才保持当前状态。
- **缺失或迟到**：缺正文、缺必需证据、缺样本覆盖、语义运行未完成或 provider 失败时，页面为 `degraded` 或交付为 `not_released`；不得补占位内容。只有 SCN-009 的确定性来源缺口可记录 `source_not_documented`，且不生成异常 Claim。
- **预览与正式**：机器通过的页面可以进入当前 Reader 导航；Task 2-B 整包仍是 `not_released`，人工读者质量必须等 Task 2-C。
- **当前与历史**：新结果不能覆盖旧正式页的历史依据；失败结果不覆盖旧正式 Reader；当前导航只展示当前有效且通过的页面。
- **归属与清理**：Reader 负责当前可读页，Audit/Archive 负责完整失败和溯源证据；本期不删除历史页，不建立数据库、图谱或永久候选队列。

## 9. 兼容性预留

- **既有消费方**：继续使用 Task 2-A Reader Bundle、稳定主题身份、canonical navigation 和来源/Claim 回查；正文只是向已有容器填入受控内容。
- **命名预留**：只使用已有三类 page type；未来新类型必须另行确认，不通过本期临时扩展。
- **容器预留**：保留 Reader、Audit、Archive 的分层，让 Task 2-C 的人工信号和 Task 3 的完整发布可以追加而不改变本期失败语义。
- **状态预留**：保持页级 `published`/`degraded` 和交付级 `not_released` 分离；`source_not_documented` 只作为 `exceptions` 的 section-level 状态，不塞进页级或交付级字段。
- **扩展边界**：本期只允许一次受控 body/section contract revision；本次 `SR-20260811-task2b-procedure-source-gap` 已占用该额度；不承诺向量库、数据库、图谱、调度器、长期人工候选系统或 UI 产品化。

- **当前修订预算**：沿用 decision-log 的 `contract revision = 1/1`；本次 `SR-20260811-task2b-procedure-source-gap` 已消耗唯一额度。后续只允许修复实现行为 bug，不得再改变 section、字段、状态语义或 page type 映射。

## 10. 明确不做与默认必须成立

### 明确不做

- 不做全量 89 篇正文编译和正式 `released`（D-004；Task 3）。
- 不做 Task 2-C 人工读者门、人工评分、`human:*` 信号和最终信任判断（D-004；Task 2-C）。
- 不做完整 17+3 题集和全量交付门（D-004；Task 3）。
- 不在 Task 2-B 临时删改题集；只运行 Task 0 冻结题集派生出的样本可答子集，不把它说成完整题集或人工读者门（D-004；Task 2-C/Task 3）。
- 不新增 page type、数据库、图谱、永久 candidate 队列或无人维护的人工复核系统（D-001–D-004）。
- 不用全局正文复制率作硬门，不把 provider 成功、写回成功、结构 lint、Jaccard 或离线结果说成语义/读者质量通过（D-001、D-004）。
- 不重做 Task 2-A Reader Bundle、主题身份、导航入口或已有 Audit/Archive 分层（R-005、D-001–D-003）。

### 默认必须成立

- 每条进入 Reader 的事实都能回查到唯一 Claim、来源 URI、内容指纹和片段位置（FR-PUBLISH-001、AC-03）。
- 不确定影响必须扩大为整页重编，整页失败不得覆盖旧正式 Reader（FR-DRAFT-003、AC-06）。
- 缺证据、provider 失败、截断、fallback、重复或保真失败必须显式降级（FR-PUBLISH-002/003、AC-04、AC-07）。
- Task 2-B 的机器出口不足或证据不完整时保持 `not_released`，不声称人工质量（FR-SEM-002/003、AC-11）。
- `source_not_documented` 不能代替异常 Claim，不能由 provider mapping failure 触发，且必须绑定来源指纹和审计版本（FR-DRAFT-004、FR-PUBLISH-006、AC-13）。
- 任何 contract revision 都必须可追溯；本次 scope revision 已消耗唯一额度，行为 bug 修复不能偷偷改变 section、字段或 page type 合同（D-004、D-005、AC-12）。

## 11. 验收标准

- [ ] **AC-01**：结构整理保留完整来源关系。
  - **需求**：FR-FLOW-001、FR-FLOW-002。
  验证：用代表性来源检查标题/H1、父子页、FAQ、表格、图片、双语、版本和噪声片段的结构与来源位置。
  - **通过条件**：每个进入正文或 Audit 的片段都有可追溯结构关系；无法追溯的片段被明确排除或降级。
  - **失败条件**：片段丢失父子关系、位置或内容类型，或被写成没有来源的正文事实。
  - **证据类型**：`evidence`

- [ ] **AC-02**：三类 page type 使用固定骨架，provider 不能扩张页面合同。
  - **需求**：FR-DRAFT-001、FR-DRAFT-002。
  验证：逐类检查 page type、必需/可选 section、来源字段和 provider 输出边界。
  - **通过条件**：三类各有稳定、可判定的页面结构；provider 只能填受控 section，不能增加 page type、section、来源字段或无来源事实。
  - **失败条件**：页面类型被标题临时猜测、必需 section 缺失，或 provider 改写结构合同。
  - **证据类型**：`test`

- [ ] **AC-03**：Reader 正文事实 100% 可回查。
  - **需求**：FR-FLOW-002、FR-DRAFT-002、FR-PUBLISH-001、FR-COMPAT-001。
  验证：抽查并逐项反查正文事实到 `claim_id`、source URI、内容指纹和 `fragment_locator`，同时检查 Reader 与 Evidence/archive 的连接。
  - **通过条件**：所有进入 Reader 的事实都有唯一、可解析、未断链的回查关系；完整 Claim/Evidence/原文仍可在 Audit/Archive 找到。
  - **失败条件**：任何事实无来源、多个来源无法判定归属、回查链断裂或正文直接替代完整证据。
  - **证据类型**：`evidence`

- [ ] **AC-04**：关键事实、结构保真和页面边界门可拒绝错误正文。
  - **需求**：FR-PUBLISH-002、FR-PUBLISH-005。
  验证：使用包含数字、标识符、版本、命令、端口、配置、表格、图片、golden-negative、同页/跨页近重复和超长主题的样本，观察机器门结果；按 PRD §6.9.10 固定规则检查连续逐字来源块和近重复。
  - **通过条件**：事实保真、归因、表格/图片、重复、正文最多 120 行、整页最多 300 行和语义拆分检查均能判定；连续逐字来源块最多 3 个句子或 240 个字符，代码块、表格、双语配对、公共模板段落和带 attribution 的短引按例外处理；同页或跨页 section 的 5-gram Jaccard ≥0.92 且正文长度超过 80 字符时阻断近重复，公共模板、代码、表格和双语配对按 fixture 规则排除；每项记录分母、检测器版本、seed 和失败样本；超长主题保留总览、相关 key、`prev/next`，每个 Claim 只进入一个 part，且每个 part 有入口；不满足条件的页进入 `degraded`，不进入 Reader 导航。
  - **失败条件**：错误数字/版本/命令被放行，连续逐字来源块超出固定边界，golden-negative 未稳定失败，符合固定规则的同页或跨页近重复未阻断，或未记录分母/检测器版本/seed/失败样本；正文或整页超限，Claim 丢失/重复、part-1 代替主题入口、part 无入口，或 provider 成功直接变成通过。
  - **证据类型**：`test`

- [ ] **AC-05**：受影响 section 更新，不留下已知过期说法。
  - **需求**：FR-DRAFT-003、FR-PUBLISH-004。
  验证：改变一个来源、Claim、版本或结构关系，比较影响闭包内外 section 的依赖、归因和内容状态。
  - **通过条件**：受影响 section 被重编；影响闭包外仅复用依赖、归因和版本均未变且可证明安全的 section；影响集外页面的正文和路径字节保持不变并通过 content hash 对账；旧信号不再代表当前受影响内容。
  - **失败条件**：受影响 section 未更新、旧 section 与新 section 混拼、旧验证仍被当作当前，或影响范围无法解释。
  - **证据类型**：`evidence`

- [ ] **AC-06**：影响不确定时整页重编并保护旧正式页。
  - **需求**：FR-DRAFT-003、FR-PUBLISH-003、FR-COMPAT-001。
  验证：制造依赖登记缺失、版本/结构关系不明或归因无法证明的更新，再观察页面和旧 Reader。
  - **通过条件**：系统扩大为整页重编；整页成功则整页一致更新，整页失败则为 `degraded`，旧 Reader 正式页保持不被失败结果覆盖。
  - **失败条件**：只降级不确定 section、继续复用无法证明安全的旧内容，或失败结果覆盖旧正式页。
  - **证据类型**：`test`

- [ ] **AC-07**：页级和交付级状态诚实分离。
  - **需求**：FR-PUBLISH-001、FR-PUBLISH-003、FR-COMPAT-001。
  验证：检查通过页、失败页、冲突页、未映射页和整包状态在 Reader、Audit/Archive 和导航中的投影。
  - **通过条件**：通过页可为 `published` 并进入 Reader；失败页为 `degraded` 且只进 Audit/Archive；Task 2-B 交付保持 `not_released`。
  - **失败条件**：degraded 页进入正式导航、失败被写成空白成功页，或 Task 2-B 声称 `released`/人工质量通过。
  - **证据类型**：`evidence`

- [ ] **AC-08**：Task 2-A Reader Bundle 和稳定入口不被正文编译破坏。
  - **需求**：FR-PUBLISH-001、FR-COMPAT-001。
  验证：对正常、失败和重复运行后的 Reader 入口、主题身份、来源/Claim 回查和旧正式页做兼容回归。
  - **通过条件**：既有入口和身份规则仍有效；正文、来源回查、Audit/Archive 和导航结果能相互对账。
  - **失败条件**：新建第二套导航、重命名既有稳定主题、丢失旧正式页依据或破坏来源/Claim 回查。
  - **证据类型**：`test`

- [ ] **AC-09**：冻结样本覆盖达到 Task 2-B 范围。
  - **需求**：FR-SEM-001、FR-SEM-003。
  验证：回读冻结的 12–20 篇样本覆盖记录和实际 inventory，对 source/topic/page type/类别逐项核对。
  - **通过条件**：不临时挑样本；三类 page type 各至少 1 个；实际存在的长文、表格/图片、双语、多源类别均覆盖；不存在的类别有 machine fixture 或明确排除理由。
  - **失败条件**：样本数量或来源未绑定、类别漏项、缺类无 fixture/排除理由，或实现者为凑门槛临时换样本。
  - **证据类型**：`evidence`

- [ ] **AC-10**：真实语义运行结果可复核。
  - **需求**：FR-SEM-001、FR-SEM-002。
  验证：检查至少一次真实语义运行的冻结 provider/model/预算、抽样 seed、样本数、判定阈值、检测器/模型版本、样本范围、Task 0 answerability 派生可答子集、首次命中、section 完整性、通过/失败项、归因和运行状态。
  - **通过条件**：运行身份、抽样参数、冻结题集派生关系和输入覆盖完整；失败项真实保留；运行结果能重放或解释，不把 fallback 当成成功语义运行；没有临时删题或换题。
  - **失败条件**：只提供结构基线、Jaccard-only、provider 失败被隐藏、运行配置或抽样参数漂移、缺少可答子集/首次命中/section 完整性/归因/失败项，或为实现方便改动题集。
  - **证据类型**：`evidence`

- [ ] **AC-11**：机器语义出口达到不可下调的成功线。
  - **需求**：FR-SEM-002、FR-SEM-003、FR-PUBLISH-003。
  验证：从语义运行证据统计机器通过 concept 数、三类 page type 覆盖、inventory 覆盖和交付状态。
  - **通过条件**：至少 6 个 `machine-passing concept`；三类各至少 1 个；`procedure_or_rule` 可以由已审计的 `exceptions=source_not_documented` 计入 page-type 覆盖，但异常题仍标记 `not_answerable`；实际类别覆盖完整；至少一次真实语义运行完成；全部条件成立才可报告 Task 2-B 机器出口成立。
  - **失败条件**：少于 6 个、缺 page type、缺类别证据、没有完成真实语义运行，或 fallback/Jaccard-only/证据不足仍报告通过；此时保持 `not_released`。
  - **证据类型**：`evidence`

- [ ] **AC-12**：范围和契约修订保持可追溯。
  - **需求**：R-001、FR-COMPAT-001、D-004。
  验证：检查本期变更是否只落在已接受的三类正文、影响闭包、机器门和样本出口；检查 body/section contract revision 记录。
  - **通过条件**：不新增 page type、长期系统或全局复制率门；改变 section 集合、模板、字段或 page type 映射时明确消耗唯一 revision；行为 bug 修复不静默改变合同。
  - **失败条件**：build-spec/实现阶段补充新产品方向、临时降低机器底线、重复建设第二套状态/证据系统，或无法说明修订是否消耗预算。
  - **证据类型**：`evidence`

- [ ] **AC-13**：来源未记录异常规则时，特殊状态既不编造事实，也不误伤同页可用内容。
  - **需求**：FR-DRAFT-004、FR-PUBLISH-006、FR-SEM-003。
  - **验证**：使用一个真实 `procedure_or_rule` 来源，分别覆盖“确定性审计证明没有异常规则”“来源含糊/审计不完整”“provider 映射失败”“归因失败”四种输入；核对 section 状态、正文、Claim、题目可答性、页级状态和 page-type 统计。
  - **通过条件**：四种输入都保留固定 `exceptions` section；只有第一种使用 `source_not_documented`，绑定 source URI、content hash、可回查 locator（如适用）和审计版本，不生成 Claim、不写“暂无异常”等占位句、不跨主题推导；异常题为 `not_answerable`；其他 section/机器门通过时页可 `published` 并计入 `procedure_or_rule` 覆盖。
  - **失败条件**：把“没有记录”写成“没有异常”、从“缺点”或其他主题生成异常 Claim、把映射/归因失败伪装成来源缺口、缺少状态回查绑定，或在特殊状态下错误地声称异常问题已回答。
  - **证据类型**：`test` + `evidence`

## 12. 风险、未决与交接

- **RISK-001**：section 依赖或反向依赖登记不完整。
  - **受影响 ID**：PFACT-006、FR-DRAFT-003、FR-PUBLISH-004、AC-05、AC-06。
  - **触发条件**：来源、Claim、版本或结构变化无法映射到完整影响闭包。
  - **后果**：旧说法可能残留，或无关 section 被错误重编。
  - **缓解或 STOP**：无法证明安全就整页重编；整页失败保持 `degraded`，不得覆盖旧 Reader。
  - **处理 Stage**：`build-plan` / `build-code`。
  - **验证**：有可回读的依赖/影响证据，且不确定分支有失败测试。

- **RISK-002**：provider 生成无来源事实、截断或返回不可用结果。
  - **受影响 ID**：PFACT-005、FR-DRAFT-002、FR-PUBLISH-002/003、FR-SEM-002、AC-03、AC-04、AC-10、AC-11。
  - **触发条件**：provider 失败、输出不可解析、fallback 或 claim/source gate 不通过。
  - **后果**：读者看到错误、残缺或过期答案。
  - **缓解或 STOP**：拒绝进入 Reader；页面 `degraded`，整包 `not_released`，保留真实错误。
  - **处理 Stage**：`build-plan` / `build-code`。
  - **验证**：真实 provider 运行和负向样本证据完整。

- **RISK-003**：冻结样本或 inventory 覆盖无法回读。
  - **受影响 ID**：PFACT-004、FR-SEM-001/003、AC-09、AC-11。
  - **触发条件**：上游 manifest 缺失、内容指纹不匹配、类别分布未知或缺类没有 fixture/排除理由。
  - **后果**：样本看似通过但不能代表批准范围。
  - **缓解或 STOP**：不临时换样本；语义出口保持 `not_released`，等待真实 manifest 或明确排除理由。
  - **处理 Stage**：`build-plan` / `build-code`。
  - **验证**：逐项 source/topic/page type/类别覆盖回读通过。

- **RISK-004**：在实现阶段静默改变 body/section contract。
  - **受影响 ID**：FR-DRAFT-001、FR-COMPAT-001、AC-02、AC-08、AC-12。
  - **触发条件**：为解决实现困难而新增 section、字段、page type 或降低验收门槛。
  - **后果**：Task 2-C 和 Task 3 消费不同版本的页面合同，历史结果不可比较。
  - **缓解或 STOP**：只允许一次受控 revision；行为 bug 修复不改变合同；任何真正改变都回到产品决策边界。
  - **处理 Stage**：`build-plan`。
  - **验证**：revision 记录、前后合同差异和用户影响可追溯。

- **RISK-005**：来源缺口特殊状态被过宽使用。
  - **受影响 ID**：PFACT-007、FR-DRAFT-004、FR-PUBLISH-006、FR-SEM-003、AC-13。
  - **触发条件**：审计把 provider 映射失败、来源含糊或没有完整回查绑定误判为 `source_not_documented`。
  - **后果**：Reader 可能把“来源没有写”误读成“产品没有异常”，或绕过事实归因门。
  - **缓解或 STOP**：审计条件必须逐项证明“没有异常触发/处理/分支/恢复规则”；任一条件不确定即 `degraded`；状态绑定来源指纹和审计版本；不写正文占位、不跨主题推导。
  - **处理 Stage**：`build-spec` / `build-plan` / `build-code`。
  - **验证**：AC-13 的正负例和真实 T013 evidence。

- **OPEN-001**：冻结 sample coverage manifest 的逐项清单和类别分布是什么？
  - **受影响 ID**：PFACT-004、FR-SEM-001/003、AC-09、AC-11。
  - **owner**：Task 2-B 执行负责人。
  - **影响**：若不关闭，无法判定样本覆盖和不存在类别的 fixture/排除理由。
  - **处理 Stage**：`build-plan` / `build-code`。
  - **关闭条件或 STOP**：回读上游冻结 manifest，逐项列出 source/topic/page type/类别；无法回读则 STOP，保持 `not_released`。

- **OPEN-002**：真实语义运行的 provider/model、检测器、阈值和预算是什么？
  - **受影响 ID**：PFACT-005、FR-SEM-002/003、AC-10、AC-11。
  - **owner**：Task 2-B 执行负责人。
  - **影响**：若不关闭，运行结果不可复核，不能声称语义出口成立。
  - **处理 Stage**：`build-plan` / `build-code`。
  - **关闭条件或 STOP**：运行前冻结并在运行证据中记录全部字段；provider 失败或配置不可复核则只记录失败并保持 `not_released`。

- **OPEN-003**：各 page type 的 section 依赖字段和影响闭包如何表达？
  - **受影响 ID**：PFACT-006、FR-DRAFT-003、AC-05、AC-06。
  - **owner**：Task 2-B 计划与实现负责人。
  - **影响**：若不关闭，无法证明 section 安全复用，必须整页重编。
  - **处理 Stage**：`build-plan` / `build-code`。
  - **关闭条件或 STOP**：计划中冻结可审计的依赖记录和不确定分支；不能形成证明时直接采用整页重编兜底。

- **OPEN-004**：`source_not_documented` 的确定性审计输入、状态落盘字段、Reader 文案和语义 evidence 结构如何实现？
  - **受影响 ID**：PFACT-007、FR-DRAFT-004、FR-PUBLISH-006、AC-13、T009、T010、T013。
  - **owner**：Task 2-B build-spec/build-plan/build-code。
  - **影响**：若不关闭，不能区分真实来源缺口与 provider/归因失败，也不能回放 page-type 覆盖解释。
  - **处理 Stage**：`build-spec` → `build-plan` → 返回 `build-code`。
  - **关闭条件或 STOP**：冻结审计输入和 evidence schema；实现和负例证明只有真实来源缺口能进入特殊状态；无法证明时保持 `degraded/not_released`。

## 13. 业务影响与回归范围

### 主题正文与 Reader 入口

- **既有行为**：Task 2-A 已有 Reader Bundle、稳定主题身份、导航和来源/Claim 回查骨架，但正文语义尚未完成。
- **本需求影响**：通过机器门的主题有可读正文；失败主题明确降级，不污染 Reader。
- **回归路径**：正常单源、多源同产品、长文/表格/图片/双语、无正文、provider 失败、影响不确定更新、重复运行。
- **验收**：AC-01–AC-08。

### 机器语义出口

- **既有行为**：Task 2-B 尚未形成可声称的正文语义出口。
- **本需求影响**：新增冻结小语料和真实语义运行证据，建立 `>=6` concept、三类覆盖和 `not_released` 失败边界。
- **回归路径**：样本完整、缺类别、真实运行通过、provider 失败、fallback/Jaccard-only、语义证据不足。
- **验收**：AC-09–AC-12。

- **可能受冲击的业务规则**：主题身份稳定性、Reader/Audit 分离、来源/Claim 回查、页面状态、旧正式页保护、交付状态。
- **明确无影响**：Task 0/Task 1 的输入身份和主题轴、Task 2-A 的 Reader Bundle 结构、Task 2-C 人工门、Task 3 全量发布、数据库/图谱/调度器/权限体系和 UI 产品化。
