# KnowledgeDigest 知识发布总诊断与修复方向

日期：2026-08-04

本报告合并 12 条独立调查线的结果，调查对象为：

- 原始方案：`docs/plans/universal-knowledge-digest-design.md`
- Task2 规格：`specs/archive/knowledge-digest-llm-naming-classification/`
- Task2 产物：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804`
- 参考库：`/Users/Hugh/Hugh/Knowledge/CompanyBrain`
- 当前代码：`src/knowledge_digest/`

只读调查，没有调用外部模型，也没有修改业务代码和原始语料。

## 一、最终判断

KnowledgeDigest 不是“完全失败”，而是完成了保存层，却没有完成知识产品层。

- 保存层：来源、Claim、Evidence、Provenance、归档、路径安全、批次恢复、分页和本地链接大体可验证。
- 知识层：没有建立产品/模块/场景/页面类型本体，没有把多篇来源编译成可独立阅读的知识页，也没有真正通过人工读者验收。

因此 Task2 实际产物是：

> 带审计、索引和溯源的原文切片器，而不是 CompanyBrain 式知识编译器。

这解释了“机器检查通过，但人读起来很差”的矛盾。问题不是只换一个模型或改几个文件名可以解决的，而是发布目标和质量合同定义得不够完整。

## 二、Task2 产物的硬证据

| 维度 | 实际结果 | 说明 |
| --- | ---: | --- |
| 稳定主题 | 86 | 其中 85 个是单来源主题，1 个双来源；没有形成足够的跨来源主题 |
| 当前页面 | 120 | 34 个 `.part-*` 分页文件 |
| 非空叶分类 | 8/21 | 13 个分类页为空，像未完成的菜单 |
| `product_slug` | 0 | 没有建立产品实体层 |
| Summary 占位 | 58/120 | `来源未提供摘要；请阅读 Evidence。` |
| Why 占位 | 58/120 | `来源未说明` |
| Version 缺失类 | 54/120 | 无法判断时效和适用版本 |
| Related topics 占位 | 120/120 | 没有可用的知识关系网 |
| Provider 失败 | 31 条 needs-review | 超时或 JSON 损坏的来源仍有正文页，但没有正式读者治理 |
| Source index | 88 行 | 批次/快照涉及 89 个来源，存在账本不一致 |
| 当前包体积 | 约 279 MB | 正文约 4.9 MB；`_digest` 约 237 MB、`_archive` 约 36 MB |
| 运行/归档现场 | 92 个 run、88 个 archive run | 审计历史和读者正文混在一个交付目录 |
| 本地链接 | 149 条，0 断链 | 结构可达，但 `source-index` 的目标路径是纯文本，不是链接 |
| 读者验收 | 未完成 | 对比报告只有 17 个 `agent_assisted_review` 样本，不能算人工质量通过 |

这些数字来自 `20260804-output-audit.md`、`20260804-output-navigation.md`、`20260804-output-content-quality.md` 和 `20260804-output-provenance-integrity.md`。Claim/fingerprint 的无损证据仍然有价值，但不能替代上述读者质量证据。

## 三、为什么页面难读

当前管线的实际因果链近似如下：

```text
原始 Confluence
  → Claim/相似度簇
  → 稳定 topic_id
  → 标题/分类/Summary/Why 建议
  → 原始 Evidence 按 300 行切片
```

缺少的关键链路是：

```text
来源结构归一
  → 产品/模块/对象/场景识别
  → 跨来源主题规划
  → 页面类型选择
  → 可读正文编译
  → 来源映射与读者验收
```

具体表现：

1. **S2 粒度错**：85/86 个主题是单来源。聚类 ID 被当成读者主题 ID，批次是传输边界，却变成了知识边界。
2. **S3 路由弱**：实际主路径是全文词面相似度和固定阈值，不是对产品、能力、流程和版本关系的语义判断。
3. **S4 责任过窄**：`publication-only` 只让模型建议元数据；`final_body` 仍是原始 Evidence 或 Claim 拼接。300 行限制解决的是文件长度，不是主题边界。
4. **回退语义错误**：回退占位是安全保护，但仍被放进正式主导航；读者得到的是“请自己读 Evidence”，而不是可复用知识。
5. **分类不是本体**：`products/engineering/...` 只是来源级叶目录，`product_slug=0` 直接证明没有产品、模块、场景层。
6. **导航只有链接**：叶索引平铺标题，没有“什么时候查、适用范围、下一步、边界和常见任务”。
7. **交付包错误**：`pages`、运行审计、归档快照、失败队列和比较报告放在一个最终目录，用户首先面对的是工程现场，不是知识入口。
8. **质量门被代理指标替代**：Claim 数、页数、行数、链接和指纹通过，不代表标题可理解、主题不混杂、正文能回答问题。

## 四、CompanyBrain 为什么明显更好

CompanyBrain 的优势不是文件多，而是先建立了可维护的知识本体：

- `Home.md` 先按 Products、Engineering、Customers、Operations、Principles 给出查询入口和使用边界。
- 产品索引再进入具体产品；产品内部有产品总览、模块、技术实现、经验与坑、规范与资产、使用场景等语义层。
- 页面按类型回答问题：产品定位回答“是什么/解决什么/边界”；操作页回答“入口/前置条件/步骤/异常”；经验页回答“问题/原因/处理/复盘”。
- frontmatter 区分 `page_model`、`tier`、`trust`、`source_status`、`quality_status`；原始资料、候选页和正式页不是一个状态。
- 有场景索引、边界页、来源索引和质量审计脚本，导航本身承担知识路由功能。

CompanyBrain 也不是完美答案：资料汇总层存在截取式摘录和编译完成度不一致。应借鉴“本体先行、页面分型、场景导航、边界治理、质量审计”，不能照搬其 1,347 个文件或所有人工脚本。

## 五、原始方案完成度

### 已基本实现

- S1 文件读取、指纹、快照、空壳门禁。
- S2 complete-linkage 形态、相似度分层和队列输出。
- S3 top-k 候选和 `new/revise/merge_multiple` 规则路径。
- S5 临时文件、fsync、原子写、写前归档、路径安全。
- S6 Claim 到 source URI、定位、指纹和验证状态的机器回溯。
- Task2 的 taxonomy、Home/indexes/pages、稳定 topic ID、300 行分页和 source-index。

### 只有部分实现

- 非文本引用只被正则收集为 URL，没有附件/截图/父子页的一等模型。
- 表格、FAQ、双语和代码大多被保留为原文结构，没有转成读者可用的语义字段。
- `keep/revise/remove_with_reason` 没有成为真实数据协议，移除主要来自固定 unsupported 处理。
- source-index 与导航虽有同批记录，但 pipeline 后面仍存在单独覆盖 source-index 的路径。
- 失败来源有 `needs-review` 记录，却仍然有正式正文页，且 Home 的 pending 页面为空。

### 没有实现原始需求的部分

- 原方案要求的 F1–F7 多特征决策没有落地；实际 S2 主要只有一个相似度分数。
- 设计写明 S3 由 LLM 判定路径，但当前正式路径是规则阈值，未形成对象/页面规划。
- S4 的“提炼合并”没有形成可读正文编译；已有目标正文没有真正进入重写上下文，更多是历史 Claim 拼接。
- 没有产品、模块、业务对象、任务、知识类型、版本、边界和关系模型。
- 没有产品总览、模块总览、场景索引、边界页、排障页等页面职责合同。
- 没有“从真实问题找到答案并完成任务”的硬验收。

结论：工程安全与防丢失约束完成度较高；“知识消化”这个面向读者的核心目标完成度不足。不能用 254/316 测试通过、89 批成功或 Claim 数量给出“质量完成”的结论。

## 六、原始调研是否完整

原始方案引用的 ovmc、sleep-curator、CompanyBrain 丢失分析和开源项目调研文件都存在，且内容足以支撑：

- 聚类、增量和资源瓶颈判断；
- Claim/faithfulness/归档/溯源防丢失；
- CompanyBrain 已有目录、字段和信息丢失教训；
- 是否引入图数据库、向量库、调度器的取舍。

但调研没有被完整翻译成可执行的知识质量合同。缺口是：

1. 没有把 CompanyBrain 的产品/模块/场景/页面类型建成数据模型。
2. 没有研究 Confluence 父子页、表格、截图、FAQ、双语、版本记录和产品命名的归一规则。
3. 没有页面规划、正文编译和跨来源主题合并的中间模型。
4. 没有固定读者任务集、人工评分表和“不通过就不进入正式知识”的门禁。
5. 研究使用 OpenViking 的绝对路径，没有绑定外部材料版本/hash/采样清单，脱离外部目录后不可自证。

所以“调研文件完整”只能回答工程风险，不能回答“怎样生成 CompanyBrain 级可读知识”。

## 七、推荐修复架构

不要继续给 `publication.py` 增加更多字段。保留 S1–S6 作为来源保真层，在其上增加独立的知识发布编译层。

### 1. 保留层：Source Preservation

保留现有：快照、Claim、Evidence、Provenance、归档、source-index、fail-closed、批次恢复和路径安全。它的目标是“不丢、不假、不越界”，不是直接供人阅读。

### 2. 新增层：Knowledge Compiler

建议至少有以下内部记录：

- `KnowledgeEntity`：领域、产品、模块、业务对象、角色、场景、版本、边界、别名和置信度。
- `TopicPlan`：一个读者主题的稳定 ID、成员来源、实体关系、页面类型、标题、目标读者、状态和拆分计划。
- `KnowledgePageDraft`：页面类型、用途、正文 sections、证据引用、来源列表、版本/边界、相关主题和质量状态。
- `ReviewState`：`raw → candidate → formal`，以及 `needs_review` 的原因（provider failure、事实冲突、命名冲突、缺来源、人工未审）。

### 3. 页面类型，不再统一套一个壳

第一版建议支持：

- 产品总览：定位、解决的问题、核心对象、能力地图、边界、模块入口、适用场景、来源。
- 模块总览：模块职责、子能力、常见任务、相关产品、入口。
- 功能/操作页：用途、前置条件、入口、步骤、结果、异常、权限、适用版本。
- 规则/配置页：配置项、取值、约束、默认值、冲突和示例。
- 技术实现页：架构、数据流、接口、依赖、部署/排障。
- 经验与决策页：问题、背景、判断、方案、取舍、结果、后续风险。
- 版本/演进页：版本、变更、兼容性、迁移和时间线。
- 客户案例/内容资产页：场景、对象、结果、可复用素材和边界。

Evidence 和 Provenance 保留在页尾或独立来源区，不能继续承担正文职责。

### 4. 统一事实源但允许领域扩展

继续以 `kb.structure.md` 作为发布合同单一事实源；增加一个由它声明的 ontology/page-type 区域，或声明一个受管的本体文件，禁止无绑定的第二份 taxonomy。初始本体从 CompanyBrain 五个顶层域和现有 24 个产品目录中提取，先覆盖本批真实语料，不追求一次覆盖所有公司知识。

### 5. 运行顺序

```text
全量来源快照
  → 结构归一/噪声标记
  → 产品/模块/对象实体识别
  → 全量 TopicPlan（批次只是传输，不是主题边界）
  → 按页面类型编译正文
  → Claim/Evidence/Provenance 回指
  → 读者导航与质量门
  → 生成当前知识包 + 独立审计包
```

## 八、建议拆成三个任务

不建议把所有问题塞进一个“重构大任务”；也不建议继续只做一个小字段任务。推荐三个有明确产物的连续任务。

### 任务 A：知识本体与发布合同

目标：先定义“什么是一个可发布知识页”。

- 从 CompanyBrain 和 89 篇语料提取产品、模块、场景、对象、页面类型、别名和边界。
- 定义 `KnowledgeEntity`、`TopicPlan`、`KnowledgePageDraft`、`ReviewState`。
- 定义页面模板、证据回指和 raw/candidate/formal 状态。
- 固定 20 个真实读者问题和人工评分表。
- 不重写全量 S1–S6，不调用真实 provider 做大规模运行。

完成标准：规格能判断一个样本页“为什么属于某产品/模块、解决什么问题、缺什么字段、何时可正式发布”。

### 任务 B：知识编译器与小语料验证

目标：实现从 TopicPlan 到类型化可读页面。

- 先在 12–20 篇代表性来源上实现结构归一、主题规划和页面编译。
- 允许 LLM 输出结构化 `KnowledgePageDraft`，但每段必须绑定 Claim/Evidence；失败只发布 raw/candidate，不把占位页当 formal。
- 保留现有 Claim、Provenance、归档和路径安全门。
- 先证明产品/模块聚合、标题、用途、边界、步骤、版本、FAQ 和相关主题可读，再扩大语料。

完成标准：固定样本中人工能从 Home 找到答案；页面不再把 Evidence 当正文；多来源主题能合并，独立流程页不会被错误合并。

### 任务 C：全量发布、质量门和交付包

目标：在 89 篇语料上完成可交付结果。

- 全量运行前冻结 TopicPlan/ontology/模型/预算和输入 manifest。
- 运行失败来源单独进入 review/raw 区，不进入 formal 导航。
- 当前知识包只保留 `README/Home/indexes/pages/source-index`；`_digest`、`_archive`、provider 日志和比较报告作为独立审计包。
- 用同一套 20 个读者任务比较 Task1、Task2、CompanyBrain 和新结果。
- 只有人工审查完成且 machine gates 全绿，才叫最终发布。

完成标准：输出能解释每个文件的用途，读者无需打开 Evidence 原文才能理解主题；所有质量下降都能定位到具体页面和来源。

## 九、不能接受的“假修复”

- 只把 `topic-<hash>` 改成更漂亮的 slug。
- 只提高 Summary prompt 或把 Summary 翻译成中文。
- 只把 300 行改成 500 行。
- 只增加更多索引链接而没有产品/模块/场景语义。
- 只降低 provider 失败率，仍把失败页放入正式知识。
- 删除 Claim、Evidence、Provenance、归档、fail-closed 或离线能力换可读性。
- 直接复制 CompanyBrain 的 1,347 个文件或把所有来源强行归入固定产品。

## 十、最终质量合同建议

机器底线继续保留：Claim 无损、来源可回溯、路径安全、无断链、原子/归档写回、离线可读。

新增读者硬门：

- 20 个固定真实问题全部有对应入口；每题从 Home 到答案不超过 4 跳。
- 正式页标题在脱离路径时仍能说明对象和用途；人工理解度至少 90%。
- 产品/模块/页面类型归属人工准确率至少 90%；不确定项进入 review。
- 正式页不出现“请阅读 Evidence”式摘要占位；缺失字段应省略或明确标为 candidate。
- 正文必须包含与页面类型匹配的用途/主体/规则或步骤/边界/版本/来源；Evidence 只做证据，不替代正文。
- 有证据的主题必须有真实相关主题或明确说明无关联；不能所有页面统一显示空关系。
- provider 失败、事实冲突、来源缺失和命名冲突不能进入 formal 主导航。
- 对比报告必须区分 `machine_pass`、`agent_assisted` 和 `human_reviewed`；后两者不能互相冒充。
- 审计历史与读者当前知识分包，最终知识目录不被数 GB 运行现场淹没。

## 关联调查报告

- `20260804-companybrain-comparison.md`
- `20260804-companybrain-ia.md`
- `20260804-companybrain-content.md`
- `20260804-companybrain-reader-journey.md`
- `20260804-design-compliance.md`
- `20260804-design-research-coverage.md`
- `20260804-design-s1-s3.md`
- `20260804-design-s4-s6.md`
- `20260804-output-audit.md`
- `20260804-output-navigation.md`
- `20260804-output-content-quality.md`
- `20260804-output-provenance-integrity.md`
