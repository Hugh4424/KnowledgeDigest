# Task1：知识发布主题轴——决策日志

## 0. 当前状态

- 阶段：WorkflowHub `make-decision` scope revision；原实现需按新分类轴回到 `build-spec`。
- 任务：`task1-knowledge-publication-topic-axis`。
- 决策：原方向已接受；本轮新增“知识类型优先、产品只是其中一类”的修正。
- 本轮结论：保留原 Task1 目标，但把顶层主轴改为 `knowledge_type`；产品词典只服务于 `Products` 类型。当前代码和旧计划不能直接作为新方向的完成证据。
- 正式交付状态：`not_released`。本决策日志不是代码交付，也不是正式验收。

## 1. 原始需求

用户要求：查看
`/Users/Hugh/Hugh/Project/KnowledgeDigest/docs/plans/knowledge-digest-knowledge-publication-prd.md`，准备做其中的 Task1；按标准 WorkflowHub 从 `make-decision` 开始，不跳阶段，不依赖 `build-spec` 补需求；Talk 用大白话说明选项、后果和风险；decision-log 记录原始需求、关键事实、选择、理由和延期交接；先基于原始需求梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。

这条原始需求的硬约束是：

1. 先做方向决定，再进入规格、计划和实现。
2. 不能把遗漏的产品需求推给 `build-spec` 临时决定。
3. Task1 的范围必须从 PRD 原文和现有代码事实推导，不从“实现起来方便”倒推需求。
4. 读者最终要能沿稳定的语义入口找到知识；但本轮只冻结 Task1 的主题轴基础，不能把后续页面交付假装成已完成。

## 2. 关键事实

### 2.1 PRD 对 Task1 已经冻结的事实

来源：`docs/plans/knowledge-digest-knowledge-publication-prd.md`，Task1“主题轴与 TopicIndex 基础”部分（约 §7 Task1，原文行 371–425）。

- 当前 Task2 的 `batch_size=1` 产生 86 个主题，其中 85 个只有单一来源；`product_slug=0`，没有稳定的产品语义。
- Task1 的主轴是受控的 `ProductGazetteer`、稳定的 `TopicIndex` 和 provider 之前的 `TopicPlan`。
- `ProductGazetteer` 从 89 个来源的标题、H1、父子路径中建立受控产品和模块词表；模型可以提出候选，但不能直接改正式词表。
- `TopicIndex` 至少要表达稳定的 `topic_key`、产品、模块、对象/意图、来源集合、发布路径、旧路径映射和状态。
- `TopicPlan` 必须在 provider 调用之前确定；`batch_size` 只是传输参数，不得改变主题归属。
- 同一产品和对象可以合并；不同产品的同名对象不能合并；未知或冲突项必须降级。
- 单来源不能自动算错，也不能自动算正式高置信主题；只有资料完整、产品/模块明确、结构有意义、必需证据存在且无事实冲突时才可发布。单来源比例只作报告监控，不作全局硬门。
- 首次运行或词表重建才生成完整计划；增量只处理受影响集合。
- 人工编辑过的已发布内容如果哈希发生变化，不能静默覆盖，必须进入冲突/降级边界。
- Task1 交付物包括：扩展 identity、`kb_structure`、`page_layout`；受控词表和 `TopicIndex`；89 来源结构清单；稳定路径和旧路径映射；批次不变性测试；12–20 个样例 `TopicPlan`。
- 89 条来源的结构清单不只记录标题/H1/父子路径，还要覆盖父子页、表格、FAQ、图片、双语、版本和噪声，作为归一化范围依据。
- Task1 不做数据库、图、向量、通用服务、10D ontology；也不允许模型直接修改正式词表。

### 2.2 现有仓库事实

来源：当前候选工作区基于 KnowledgeDigest `main` 的 `d3ebc236...`，以及对应代码、测试和 `CONTEXT.md`。

- 当前 `identity.py` 主要以来源 URI 哈希生成 `topic-<hash>`；已有可读路径和稳定托管字段，但还没有 Task1 要求的 `product/module/object-intent/topic_key` 轴。
- 当前 `kb_structure.py` 和验收测试把读者来源索引固定为 `indexes/sources.md`；`_digest/source-index.md` 只应作为兼容投影。仓库 `AGENTS.md` 中仍有旧表述，属于需要延期同步的文档冲突，不作为本轮新增需求。
- 当前 `TopicIndex` 结构较小，尚不包含 Task1 的模块、对象/意图、状态、旧路径映射和批次不变性证明。
- 当前 `batch_run.py` 固定来源和已有聚类/重复来源计划，但不是 Task1 的 ProductGazetteer/TopicPlan 实现。
- 现有 `docs/adr/0004-reader-publication-separate-from-audit.md` 已覆盖读者发布包与审计包分离、稳定主题身份、Home/分类/托管页面等边界。本轮不新增重复 ADR。
- 真实 89 条生产语料不在当前仓库验收 fixture 中；现有缺失 fixture 的回归不能冒充 Task1 的语义验收证据。

## 3. 经过 Talk 的真实选择

Talk 共三轮；以下只记录用户真实回复，不补写未发生的回答。

本次 Talk 的过程记录也作为决策依据保留：每轮先列出候选队列，只处理一个会改变方向的问题；用户回答后重新排序，已经被 PRD 事实覆盖或不改变方向的项目退出队列。三轮均以“没有仍未处理的方向改变问题”结束。

### Round 1：Task1 做到哪里

选项：

- **A：只做主题轴基础**：先把产品、模块、对象/意图、稳定 key、TopicIndex、TopicPlan 和不变性基础定下来。
- B：连 Home 和分类入口一起做：会扩大页面和验收范围。
- C：直接做完整读者发布：会把 Task2/Task3 的正文和读者验收一起卷入。

用户选择：`A`。

后果：本轮不承诺完整 Home、分类页、主题正文和最终读者体验；只为这些后续页面提供稳定主题身份、结构索引和计划输入。

### Round 2：输入范围和验证粒度

选项：

- **1：89 条来源做完整确定性结构清单，再做 12–20 个 TopicPlan 样例**。
- 2：只做样例：成本低，但无法证明全量结构入口完整。
- 3：89 条全部生成完整 TopicPlan：验证更重，也会提前绑定 provider 和正文处理。

用户选择：`1`。

后果：Task1 要覆盖全量 89 条来源的结构事实；语义计划先以 12–20 个样例验证，不能把样例说成全量语义发布。

### Round 3：未知产品或模块

选项：

- **1：未知或冲突项降级，不进入正式导航**。
- 2：遇到未知项自动创建正式新词：速度快，但会污染受控词表。
- 3：全部进入永久人工队列：边界清楚，但会把 Task1 变成人工运营系统。

用户选择：`1`。

后果：未知/冲突项仍保留来源和失败原因，可进入后续处理；本轮不生成正式产品/模块入口，不伪装成成功发布。

### 3.1 每轮开始队列、处理和重排

以下队列与 WorkflowHub 保存的三轮 interaction evidence 顺序一致，保留了真实 Talk 的处理顺序和收敛原因；这些 canonical JSON 已在 TaskHandle 中留存，本日志只引用其事实，不把内部记录路径当成产品需求。

- Round 1 职责：问题/成功标准与调研边界。开始队列：`scope-boundary`（中影响）、`input-range`（中影响）、`failure-boundary`（中影响）。先处理 `scope-boundary`，用户选择 `A`；回答后，`input-range` 和 `failure-boundary` 在本轮被标为“已有 PRD 事实覆盖”，但作为尚未由用户确认的方向轴转交后续轮次，不写成全局关闭。结束结论：Task1 只做主题轴基础。
- Round 2 职责：方向、范围、取舍与风险。开始队列：`input-range`（中影响）、`gazetteer-storage`（低影响）、`topic-key-rules`（低影响）、`normalizer-depth`（低影响）。先处理仍待用户确认的 `input-range`，用户选择 `1`；回答后将存储、key 规则和归一化深度降为后续 manifest 技术合同，并把未知归属作为下一轮剩余风险轴。结束结论：89 条做结构清单，12–20 个做 TopicPlan 样例。
- Round 3 职责：盲审 finding、假设与剩余风险。开始队列：`unknown-ownership`（中影响）、`source-index-compat`（低影响）、`manual-edit-conflict`（低影响）。先处理 `unknown-ownership`，用户选择 `1`；回答后将 source index 冲突标为延期文档同步，将人工编辑哈希规则标为已有 PRD 事实覆盖。结束结论：未知/冲突降级，不进入正式导航；没有仍需用户决定的方向问题。

因此，本日志没有把“用户流程和页面范围”误当作 Task1 的产品目标：它们只用于说明完整边界和后续交接；真正改变方向的三个轴是范围、输入验证粒度和未知归属处理。

## 4. 最终决定

### 4.1 方向

Task1 采用“主题轴基础”方向：

1. 以 89 条来源的标题、H1、父子路径建立可追溯的结构清单。
2. 在 provider 之前建立受控 `ProductGazetteer` 和确定性的 `TopicPlan`。
3. 用 `TopicIndex` 保存稳定主题 key、产品、模块、对象/意图、来源成员、当前发布路径、旧路径映射和状态。
4. 用批次大小、输入顺序、重复运行不变性证明主题归属、key 和路径稳定。
5. 对未知和冲突项采用降级、不入正式导航；对人工编辑冲突采用不覆盖、明确失败。
6. 输出 12–20 个 `TopicPlan` 样例作为 Task1 的语义计划证据；不把这批样例扩张成完整正文发布。
7. 89 条结构 inventory 固定记录父子页、表格、FAQ、图片、双语、版本和噪声特征；这些特征用于界定归一化范围，不提前变成 Task2 正文合同。
8. 单来源只有在资料完整、产品/模块明确、结构有意义、必需证据存在且无事实冲突时才可进入 `published`；单来源比例只报告，不作为全局硬门。
9. provider 不可用、provider 改名或批次变化不能改变正式 `TopicIndex`、`topic_key`、成员归属和路径；Task1 的结构与计划证据必须能用 `--no-llm` 离线完成。

### 4.2 为什么选它

- 它直接解决 PRD 指出的根问题：当前主题按来源碎裂，缺少稳定的产品语义。
- 先冻结主题身份，再让 provider 生成内容，能避免模型输出反过来决定产品分类和页面路径。
- 全量结构清单能检查“有没有漏掉来源”；样例 TopicPlan 能检查“主题轴是否真的能工作”，两者成本和风险平衡合理。
- 降级比自动造词更安全：不影响来源保留和失败可追溯，也不把错误分类传播到后续 Home 和分类页。
- 只做基础不会把 Task1 和后续正文、读者页面、最终发布门槛绑死，能保持任务边界清楚。

### 4.3 不选择的方案和代价

- 不选“只做样例”：无法说明 89 条来源的结构事实是否完整，后续仍可能发生漏源或漏分类。
- 不选“89 条全部生成完整 TopicPlan”：会提前引入 provider 成本、全量语义错误和正文范围，超出用户选择的主轴基础。
- 不选“未知项自动成为正式词”：会让受控词表被输入污染，后续再改名会破坏稳定 key、路径和读者链接。
- 不选“永久人工队列”：Task1 不是后台运营系统；只记录降级事实和原因，后续另行决定处理方式。
- 不选“现在连 Home/完整发布一起做”：这会跳过 Task2/Task3 的职责边界，使 Task1 无法单独判断主题轴是否正确。

## 12. 真实语料补证与上游边界（2026-08-05）

- 用户提供原始语料目录：`/Users/Hugh/Downloads/confluence 原始数据`。
- 目录实际包含 89 个 Markdown 文件，分属 4 个根目录：GoInsight 22、emm for android 27、emm for ios 20、merchant system 20；无软链接、均可按 UTF-8 读取。
- 逐文件 SHA-256 与历史 89 条真实快照一致；其中两份 Dashboard 来源内容相同，但仍保留为两条来源记录，不做错误去重。
- 选择：ProductGazetteer 必须由 KnowledgeDigest 根据当前 inventory 自己生成，不以 CompanyBrain、旧 KB 索引或其他外部产品表作为上游。CompanyBrain最多作为后续对照材料。
- 当前真实运行生成 93 个 source-derived candidate：4 个产品根 seed、89 个标题/H1 模块 seed；每项带来源 URI、内容指纹和行定位。由于原始导出没有显式模块层级、别名 owner 或 object/intent 维护字段，系统不自动晋升 canonical，89 个 TopicPlan 项按 fail-closed 规则保持 degraded。
- 延期交接：若要把模块/别名/object/intent 标成 canonical，必须由产品维护者提供明确确认或受控确认清单；这不是 CompanyBrain 依赖，而是防止把页面标题误当成产品语义的控制边界。

### 4.4 替代关系

- `supersedes`: 当前 Task2 `batch_size=1` 下“一个来源基本形成一个主题”的隐含分组方式；Task1 以后以 provider 前的 `TopicPlan` 和稳定 `topic_key` 作为主题归属权威。
- `supersedes`: 以 `cluster-N`、输入顺序或裸 hash 作为读者可见主题语义的做法；这些值仍可保留为运行审计或兼容字段，但不再是正式主题命名依据。
- `does_not_supersede`: `docs/adr/0004-reader-publication-separate-from-audit.md` 的 reader/audit 分离、旧主题页保留和稳定托管原则。
- `does_not_supersede`: 现有 `digest_topic_id` 的托管更新身份；Task1 新增语义主题轴和旧路径映射，迁移关系交给 §11 的技术合同确定。

## 5. 完整用户流程

这里的“用户”是维护本地知识库的操作者；最终读者流程只描述 Task1 必须支撑的目标路径，不把后续页面误算为本轮交付。

### 5.1 操作者流程

1. 操作者准备一份固定的 89 条来源输入和新的 KB 输出目录，冻结本轮输入指纹与代码基线。
2. 系统读取来源的 URI、标题、H1、父子路径和内容指纹，先做结构清单；缺来源、路径逃逸、清单变动或指纹不一致，立即失败。
3. 系统根据受控词表匹配产品和模块，并记录命中、别名、候选、冲突和未知原因。词表有版本和来源；模型只提交候选建议，不能直接写正式词表。
4. 系统根据产品、模块、对象/意图和来源证据生成 `TopicPlan`，在任何 provider 调用前冻结计划。
5. 系统按稳定 `topic_key` 合并同一产品/对象的来源；不同产品的同名对象分开；未知或冲突项标记为 `degraded`，不进入正式导航。
6. 系统生成或更新 `TopicIndex`，记录主题成员、稳定 key、当前路径、旧路径映射、状态和失败原因。
7. 系统使用 12–20 个样例检查 TopicPlan；检查批次大小、顺序、重复运行不改变成员、key、路径和旧路径映射。
8. 若是增量运行，系统只重算受影响来源、主题和它们的索引投影；未受影响页面和字节保持不变。
9. 若发现已发布页面被人工编辑，系统比较托管哈希；哈希不一致就标为冲突并停止覆盖，操作者看到明确失败原因。
10. Task1 输出结构、索引和计划证据，状态仍为 `not_released`；后续 Task2/Task3 再使用这些事实生成正文、读者入口并完成发布门禁。

### 5.2 读者目标流程（Task1 只提供稳定中间层）

未来读者应能沿：

`README.md → Home.md → 产品入口 → 模块/能力入口 → 稳定主题页 → 来源证据`

Task1 只负责让“产品、模块、稳定主题 key、来源成员、路径映射”这条中间层存在且稳定；Home、分类页、主题正文、来源展示细节和最终读者验收延期到后续任务。

## 6. 页面范围

### 6.1 本轮包含

- 主题身份和路径基础：`topic_key`、产品、模块、对象/意图、稳定路径、旧路径映射。
- `ProductGazetteer` 的受控数据结构、版本/来源/别名/冲突/候选记录能力。
- `TopicIndex` 的结构索引和状态投影。
- 89 条来源的结构清单。
- 12–20 个样例 `TopicPlan`，以及批次大小、输入顺序、重复运行不变性测试所需的证据。
- 增量受影响集合的计算边界和人工编辑冲突的保护边界。

### 6.2 本轮不包含

- Home、产品页、模块页、完整分类导航的最终读者页面设计。
- 主题正文的 Summary/Evidence/Provenance 生成、分页和语义质量验收。
- 全量 89 条来源的完整正文 TopicPlan 或 provider 生成。
- Task2 的命名、分类、摘要生成，以及 Task3 的完整读者发布和人工语义复核。

## 7. 数据和状态

### 7.1 主要数据

- `ProductGazetteer`：受控产品/模块词表；包括 canonical 名称、别名、来源证据、版本、匹配优先级、冲突和候选，但不允许模型直接改正式项。
- `TopicIndex`：稳定主题目录；包括 `topic_key`、product、module、object/intent、source members、published path、old path mapping、状态和原因。
- `TopicPlan`：provider 前冻结的主题计划；包括主题身份、成员来源、合并/拆分结果、计划版本和证据。
- 结构清单：89 条来源的 URI、标题/H1、父子路径、内容指纹和匹配结果。
- 托管哈希：用于识别人工编辑；发生不一致时保护人工内容，不静默覆盖。

### 7.2 状态

- 词表项：`canonical`、`candidate`、`conflict`、`unknown`。
- 主题页/主题索引项：`published` 或 `degraded`。
- 发布状态：Task1 统一保持 `not_released`；只有后续全部发布门禁满足时才可能进入 `released`。
- 来源处理：成功、重复来源、受影响、未受影响、失败；失败必须有可读原因和来源定位。
- 人工编辑：托管哈希一致可继续；哈希不一致进入冲突，不覆盖。
- WorkflowHub 阶段：本决策在用户确认前是进行中；用户确认只代表接受方向，不代表实现完成或正式发布。

## 8. 成功边界

只有同时满足以下条件，Task1 主轴基础才算业务上成功：

1. 89 条来源都出现在结构清单中，且来源 URI、指纹、父子路径可追溯。
2. `ProductGazetteer` 和 `TopicIndex` 都有明确版本、字段和来源。`published` 项的 product/module/object-intent/topic_key 不能为空；`degraded` 项仍必须有稳定的 degraded `topic_key`、来源成员、失败原因和可追溯输入，但可以没有正式产品/模块导航投影，不能因此生成空入口。
3. `TopicPlan` 在 provider 前确定；同一产品/对象能合并，不同产品同名对象不合并。
4. 12–20 个样例能展示成功、未知和冲突至少一类边界，并能回到原始来源证据。
5. `batch_size=1` 与 `batch_size=20`、输入顺序变化、重复运行不会改变主题成员、稳定 key、当前路径和旧路径映射。
6. 增量只重算受影响集合；未受影响数据的字节保持不变。
7. 旧路径仍可通过映射访问或被明确记录为不可迁移原因；旧主题页不被删除。
8. 人工编辑内容的哈希不一致会明确失败/降级，不被覆盖。
9. 不生成空的产品或模块导航；未知/冲突项保留证据但不进入正式导航。降级行的索引字段和正式导航字段差异必须由 schema 明确表达，不能用空字符串掩盖未知。
10. 单来源只有满足完整资料、明确归属、有意义结构、必需证据和无冲突五项前提才可为 `published`；单来源比例作为监控项，不作为全局硬门。
11. provider 失败或更换不会改变 Task1 的身份和计划；`--no-llm` 离线运行能完成结构 inventory、TopicIndex/TopicPlan 计划证据和失败边界检查。

### 8.1 验收草案摘要

验收实现必须保留以下可判断条件，不能只检查“文件生成了”：

- 12–20 个 TopicPlan 样例至少各覆盖一类正常合并、未知归属和冲突降级，并能回到来源证据。
- schema 必须明确 `published` 与 `degraded` 的字段差异：`published` 的正式产品/模块/对象/意图字段非空；`degraded` 必须有稳定 key、来源成员、失败原因和输入证据，但不投影正式导航；禁止以空字符串伪装未知。
- 89 条结构 inventory 必须覆盖父子页、表格、FAQ、图片、双语、版本和噪声；这些字段存在性和稳定性可检查，但不把正文归一化质量提前算作 Task1 的页面验收。
- 单来源发布必须同时满足资料完整、产品/模块明确、结构有意义、必需证据存在、无事实冲突；单来源比例只写监控报告，不作全局硬门。
- 还必须执行清单完整性、URI/指纹一致性、路径安全、批次/顺序/重复运行不变性、单来源单主题、同 key 单主题、旧路径保留/映射、受影响集合字节边界、人工编辑哈希保护，以及 provider 不可用时身份/计划不变和 `--no-llm` 可离线完成。
- 模型只能输出 ProductGazetteer 候选；模型写入或自动晋升正式词典项，直接判 Task1 失败。
- `topic_key`、正式路径或旧路径映射若使用 `topic-<hash>`、裸数字/裸文件名、hash/bare 不可读片段或输入顺序命名，直接判 Task1 失败。

## 9. 失败边界

以下情况必须明确失败或降级，不能返回“成功”：

- 输入清单变化、来源 URI/指纹变化、来源缺失、路径逃逸、软链接或结构声明不合法：整次运行失败。
- 产品或模块无法匹配、存在多个同优先级匹配、对象/意图冲突：对应 TopicIndex 项 `degraded`，不生成正式产品/模块入口。
- 模型建议与受控词表冲突：保留候选和原因，不自动写入词表。
- 主题 key、路径或旧映射为空、含 hash/bare unreadable 片段、因输入顺序变化而变化：验收失败。
- 人工编辑过的页面哈希变化：停止覆盖，进入冲突；不能用“重新生成”掩盖问题。
- 同一来源被错误地放进多个主题，或同一 `topic_key` 在一次计划中产生多个主题：验收失败。
- 受影响集合计算错误导致范围外字节改变：验收失败。
- provider 不可用只能影响后续正文生成，不得反过来改变 Task1 的正式主题身份；Task1 的计划和结构证据仍需遵守离线边界。

## 10. 非目标

以下内容明确不属于 Task1：

- 数据库、图数据库、向量库、CAS、调度器、后台守护、AgentMemory 或通用知识服务。
- 10D ontology 或一次性设计全公司所有知识类型的分类学。
- 让模型直接修改正式 `ProductGazetteer`。
- 把未知项变成永久人工运营队列。
- 立即追求 CompanyBrain 全量迁移或规模化兼容。
- 删除旧主题页、旧分页或旧路径。
- 以 `cluster-N`、`draft-N` 或输入顺序作为正式主题名称。
- 用测试通过、review 通过或 WorkflowHub 记录替代真实读者语义质量。

## 11. 延期项和交接

这些项目不是把需求丢给 `build-spec`，而是本次决定明确留下的技术合同待定项；进入下一阶段前必须逐项写入正式规格/manifest，并回链本日志：

1. `ProductGazetteer` 的正式存储位置：`kb.structure.md` 的声明段，还是独立受控文件；必须保持可重建、可审计。
2. `topic_key_v1` 的规范化版本：大小写、空白、标点、别名、保留词和兼容升级规则。
3. 匹配优先级：canonical、别名、父子路径、H1/标题、候选的优先顺序；同优先级冲突如何标记。
4. `TopicIndex` 的精确 schema、状态枚举、版本字段和 `old_path_mapping` 的一对一/一对多迁移表达。
5. 受影响集合的精确定义：来源、主题、产品/模块索引、旧路径投影分别何时算受影响。
6. 手工编辑冲突的落盘位置、错误码、恢复动作和“允许人工确认后继续”的边界；本轮不自动引入人工审批流程。
7. 89 条结构清单和 12–20 个 TopicPlan 样例的固定 fixture、稳定排序和证据格式。
8. `indexes/sources.md` 与 `AGENTS.md` 中旧 `_digest/source-index.md` 表述的文档同步；本轮只记录冲突，不修改历史事实。
9. Task1 与现有 source-hash `topic_id` 的迁移关系：旧主题页保留、旧路径如何映射到新 `topic_key`，以及何时允许停止兼容投影。
10. 离线验证只使用 `--no-llm` + Jaccard；需要语义 provider 的范围、凭据和真实调用证据由后续规格另行确认，不能在本轮补写。
11. 归一化深度和结构 inventory 字段合同：至少记录父子页、表格、FAQ、图片、双语、版本和噪声；Task1 只冻结字段和范围，不把正文归一化或页面类型验收提前带入。若实现删减字段，必须记录理由和验收影响。

交接给 `build-spec` 的最小输入：本日志、PRD Task1 原文、现有 `CONTEXT.md`/ADR 0004、结构清单字段、以上 11 项技术合同和三轮 Talk 证据。`build-spec` 只能把这些已决定事项形式化并暴露无法实现的冲突，不能新增产品目标、页面范围或发布承诺。

## 12. 风险

- 任务名称可能和历史 Task1 记录混淆：本任务使用 `task1-knowledge-publication-topic-axis`，并以本日志和当前 PRD 为准。
- 从来源 hash 主题迁移到语义 `topic_key` 可能造成旧路径一对多映射；必须先保留旧页面和映射，不能覆盖迁移风险。
- 词表过窄会产生大量降级；词表过宽会污染正式导航。选择“受控词表 + 候选不自动落地”是用可控缺口换长期稳定。
- 真实 89 条语料当前未成为仓库 fixture；本轮只能冻结输入和证据格式，不能声称已经完成全量语义验收。
- 现有文档对 source index 有新旧两种说法；若不在后续同步，使用者可能写错入口。已记录为延期文档冲突。
- provider 不可用、输出质量不佳或模型改名不能改变 TopicIndex；否则会把内容生成错误传导到身份层。

## 13. 文档拷问和复核结果

### Grill with docs

- 外部接口：Task1 是本地文件和本地 CLI 合同，没有新增远程接口；provider 不是主题身份的权威来源。
- 命名权威：现有 reader/audit/stable identity 术语以 `CONTEXT.md` 和 ADR 0004 为准；Task1 的 ProductGazetteer/TopicIndex/topic_key 以 PRD 为产品需求权威，精确 schema 延期到规格合同。
- 失败语义：未知/冲突降级、不进正式导航；人工编辑不覆盖；空入口、无 key、hash/bare 路径和批次不变性破坏均为失败。
- 范围：三轮 Talk 已固定为“主轴基础 + 89 结构清单 + 12–20 样例 + 未知降级”。
- `CONTEXT.md`：本轮不修改。当前文件已覆盖已有 reader/audit/status/stable topic 术语；Task1 新术语尚未实现，提前写入会把计划伪装成事实，按 PRD 留给 Task3-Closeout 同步。
- ADR：不新增。`docs/adr/0004-reader-publication-separate-from-audit.md` 已覆盖本轮涉及的 reader/audit 分界；本日志提供 Task1 新取舍的上下文。
- Spec/Contract：本轮不写 `spec.md`，但已把会影响实现方向的技术合同列入 §11；后续 `build-spec` 只能把它们形式化，不能新增产品需求。
- 已知冲突：`AGENTS.md` 的旧 `_digest/source-index.md` 表述和当前 `indexes/sources.md` 测试/PRD 约束不一致，已列入延期项，不在本轮扩大范围。

Grill 四项退出检查：

1. 外部接口是否有真实定义：通过。Task1 只新增本地 KB 文件、manifest 和 CLI 输入/输出合同；provider 不决定主题身份，不需要新增远程接口。
2. 字段/路径是否有唯一权威来源：通过。现有读者来源索引以 `indexes/sources.md` 的代码和测试为准；Task1 新增字段的精确 schema、词表存储位置和 key 规则已明确列为 §11 技术合同，不能由实现临时发明。
3. 失败语义是否明确：通过。未知/冲突降级且不入导航，输入完整性、路径、批次不变性和人工哈希冲突失败，均已写入 §9。
4. 范围边界是否固定：通过。Talk 已固定“主轴基础 + 89 条结构清单 + 12–20 样例 + 未知降级”；Home、正文、全量语义发布、Task2/Task3 和 released 明确延期。

本轮 `CONTEXT.md` 为 no-change，ADR 为 not-needed，冲突已转成文档延期项，四项退出检查均通过；没有需要继续拷问的方向性问题。

### wh-review

- 方向审查：已使用冻结的原始需求和目标事实进行盲向审查，结果 `pass`。
- 详细审查：第一次材料锚点错误，已按 fail-closed 规则停止；修正后的 detail review 必须重新检查 Talk 过程证据、Grill 退出检查、supersedes、降级字段、验收边界和映射锚点。
- WorkflowHub 预检：官方 `stage-runtime review` 在进入 host bridge 前因 `skills/wh-review/skill-bundle.json` 与当前工作树的 `scripts/review-runner.mjs` 哈希不一致而停止。WorkflowHub 仓库存在用户已有 dirty changes；本任务不擅自修复或重写其基础设施。已成功执行的方向审查仍保留 canonical result，不把预检失败伪装成完整阶段通过。

## 14. 批准绑定

- 用户当前已经通过 Talk 选择方向：`A`、`1`、`1`。
- 这三次选择证明范围已经收敛；用户随后已明确回复“接受”，接受完整决策日志和其中的范围、边界、风险与延期交接。
- 当前 approval binding：`accepted`。用户确认由 WorkflowHub 的 canonical human-confirmation record 单独绑定，不靠文档自称。
- `approved_direction` 现在可以作为已接受方向交给 `build-spec`；它仍不代表代码实现完成、正式发布或 `released`。
- 用户确认解除的是方向确认阻断，不会扩大页面、实现或发布范围；后续仍必须按阶段继续。

## 17. Source-canonical ProductGazetteer confirmation — 2026-08-06

### 用户新增要求

用户要求：确认 canonical `ProductGazetteer`，重跑 AC-02，再检查全部原始需求和任务完成情况。

### 关键事实

- `/Users/Hugh/Downloads/confluence 原始数据` 有 89 条 Markdown，分布在 4 个直接产品根目录：`GoInsight`、`emm for android`、`emm for ios`、`merchant system`。
- 原始目录没有 CompanyBrain 词表、外部产品清单或模型结果；每条来源都有可回溯路径、URI、指纹和行定位。
- 旧实现把产品根和页面能力 seed 全部写成 `candidate`，导致即使证据来自用户提供的当前语料，AC-02 仍只能是 `unknown`。

### 本轮选择

1. 把当前原始语料明确声明的 `products/<product-root>` 目录名确认成 source-canonical product。
2. 把来源声明的 `module`，或没有声明时的稳定文件标题/文件名 capability seed，确认成 source-canonical module；每项保留来源证据和非空 owner。当前语料没有结构化 object/intent 字段时，保留 `object_intents=[]`，不猜测业务语义。
3. 只有确定性来源证据能生成 canonical；模型/provider 输出继续只能进入 `candidate`，不能晋升或覆盖 canonical。
4. `CompanyBrain` 仍只作信息架构参考，不能成为运行时词表上游。

### 理由、后果和风险

- 这让 KnowledgeDigest 根据用户给的原始材料自己生成并确认词表，不依赖另一套知识库。
- 这确认的是“当前语料中的 source-canonical 事实”，不是声称所有未来业务别名和 object/intent 都已完成产品语义治理。
- 当前 89 条语料应得到 4 个 canonical product、89 个 canonical module；没有证据的别名、object/intent 或模型提案仍保持空值/candidate/unknown。
- 这是一项同任务 scope revision：影响 ProductGazetteer 编译、AC-02、真实语料验收和 verify 证据；不扩大到 Home、正文、Reader Package 或 `released`。

### 延期交接

- 后续若要增加产品维护者定义的业务别名、模块合并或 object/intent 词表，必须以新的受控词表材料再次修订，不从模型结果隐式推导。
- 本轮完成实现和测试后，必须重新走当前任务的 phase review 到 `pass`，再重跑 verify-code；未完成前不 close。

## 15. 依据清单

- 原始需求：用户本线程消息。
- 产品依据：`docs/plans/knowledge-digest-knowledge-publication-prd.md`，Task1 §7、全局状态和 §13 技术决策。
- 项目约束：`AGENTS.md`、`CONTEXT.md`。
- 现有设计决策：`docs/adr/0004-reader-publication-separate-from-audit.md`。
- 代码事实：`src/knowledge_digest/identity.py`、`kb_structure.py`、`batch_run.py`、`pipeline.py`、`page_layout.py`、`navigation.py`、`writeback.py`。
- 测试事实：`tests/acceptance/test_task0_reader_package.py`、`test_task2_publication.py`、`test_task2_batch_recovery.py`。
- 当前候选基线：KnowledgeDigest `d3ebc236...`；候选工作区 `/Users/Hugh/Hugh/Project/KnowledgeDigest-task1-knowledge-publication-topic-axis`。

## 16. Scope revision：知识类型优先，产品只是其中一类

### 原始修正

用户明确指出：原先把顶层目录理解成产品是错误的。应参考 CompanyBrain：企业知识库的顶层目录是知识类型，产品知识只是其中一个类型；企业知识还包括客户、研发、运营、原则、产品边界等内容。除顶层分类轴外，前面已经确认的 Task1 方向不变。

### 关键事实

- CompanyBrain 的真实顶层入口包括 `Products`、`Customers`、`Engineering`、`Operations`、`Principles`、`ProductBoundaries`。
- `Products/产品索引.md` 下面才进入具体产品，再进入模块、能力和页面；产品不是整个知识库的根。
- 用户提供的 `/Users/Hugh/Downloads/confluence 原始数据` 是产品资料语料，本次 89 条来源可归入 `knowledge_type=products`，但不能据此把所有企业知识都假设成产品知识。
- ProductGazetteer 仍然有价值，但它是 `Products` 类型下的产品/模块词表，不是全库顶层分类表。
- 当前已实现的 `product → module → object/intent` 轴缺少顶层 `knowledge_type`；旧实现证据因此只能证明旧方向，不能证明修正后的完整任务。

### 已接受选择

1. 第一层固定为 `knowledge_type`，而不是 product。
2. `Products` 是其中一个 `knowledge_type`；只有该类型继续使用 ProductGazetteer 的 product/module/object-intent 轴。
3. 本次产品语料运行显式记录 `knowledge_type=products`，不读取 CompanyBrain 的词表、索引或页面作为运行上游；CompanyBrain 只作为信息架构参考事实。
4. 其他知识类型不能被强行塞入 ProductGazetteer；它们需要自己的 subject/area 证据或先进入 candidate/degraded，不能伪装成产品主题。
5. 旧的稳定 key、路径、批次、增量、冲突、离线和不发布边界继续保留，但必须在 key/path/index/affected set 中带上 `knowledge_type`。

### 后果和风险

- `SourceInventory`、`TopicPlan`、`TopicIndex` 和路径都要增加顶层知识类型；原有 product-only schema、测试和计划需要回到 `build-spec`/`build-plan` 修订。
- 同名产品、模块或主题在不同知识类型下不能合并；类型变化会进入 affected set。
- 这会扩大 Task1 的结构范围，但不等于本轮建立全公司所有知识类型的完整本体，也不等于马上生成 Home 或读者页面。
- 若没有可靠证据判断某来源属于哪个知识类型，必须记录 candidate/degraded；不能因为文件名看起来像产品就自动晋升。

### 非目标和延期交接

- 不复制 CompanyBrain 的目录、页面或词表；不把 CompanyBrain 变成 KnowledgeDigest 的依赖。
- 不在本轮凭空为 Customers、Engineering、Operations、Principles、ProductBoundaries 发明完整业务词典。
- `build-spec` 需要形式化 `knowledge_type` 的字段、候选/降级规则、Products 类型的嵌套 product/module 规则和非产品类型的最小安全边界；`build-plan` 再拆对应实现、迁移和验收任务。
- 在新规格和计划完成前，不再把旧代码的 AC-01–AC-13 GREEN 证据当作修正方向的 close 证据。
