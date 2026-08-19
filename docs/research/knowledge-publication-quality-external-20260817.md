# 知识库出版质量：外部方法研究

研究日期：2026-08-17  
研究范围：公开、非敏感的第一方文档、论文和标准。  
比较对象：A=`/Users/Hugh/Downloads/KnowledgeDigest-real-reader-quality-20260814-v19`；B=`/Users/Hugh/Hugh/Knowledge/CompanyBrain`。  

## 先说结论

外部方法给出的稳妥路线不是用一个“质量分”判断 A/B，而是分四层测量：

1. **抽取完整性与可追溯性**：来源版本、层级、结构节点、附件/链接、定位信息是否保留。
2. **主题与导航**：主题概念、父子层级、相关关系、入口路径是否清楚且稳定。
3. **摘要与证据边界**：摘要中的原子事实是否能回到来源片段；事实性、覆盖度、引用质量分开测。
4. **读者可用性**：给真实读者真实问题，测任务成功率、耗时、错误、满意度。

**事实**：下面的标准、文档和论文分别支持这些测量维度。  
**推断**：把它们组合成 A/B 审计路线，是针对本项目目标的可执行推断。  
**未知**：本文件没有读取 A、B 或原始数据，因此不声称 A 当前存在任何具体缺陷，也不把外部方法当成项目事实证明。

## 1. Confluence 内容抽取：先保结构，再转读者文本

### 方法 1：把页面身份、父子关系、版本和正文表示作为同一份快照

**外部事实**：Atlassian Confluence Cloud REST API 的页面接口同时暴露页面 `id`、`title`、`parentId`、`version`、`status` 和正文 `body`；接口支持选择 `body-format`，并使用响应中的下一页链接继续分页。[Confluence REST API v2：Page Operations](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/)

**可执行推断**：抽取器应至少保存以下字段，而不是只保存清洗后的 Markdown：

- `source_id`、原始 URI、页面标题；
- `parent_id` 或完整 ancestor path；
- 页面版本号和抽取时间；
- 原始正文表示（如 ADF/storage）及其哈希；
- 转换后的文本、结构化节点和每个节点的来源定位。

**不能直接证明本项目事实**：这不能证明 A、B 或 `/Users/Hugh/Downloads/confluence 原始数据` 已保存这些字段；必须对实际文件统计字段存在率、版本覆盖率和定位可回放率。

### 方法 2：优先解析 ADF/结构化正文，不把 HTML 纯文本当作唯一真相

**外部事实**：Atlassian Document Format（ADF）是有 JSON Schema 的层级文档模型，区分 block/inline 节点，支持 heading、paragraph、list、table、link、media 等结构；文档按顺序遍历节点可以得到正文顺序。[Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)

**可执行推断**：转换时应保留“结构节点 → 读者文本”的映射。至少把标题、列表、表格、代码、链接、图片/附件和引用拆成可核查单元；表格不能简单拼成一段话，链接不能只保留显示文字，媒体节点不能静默丢弃。

**不能直接证明本项目事实**：外部 ADF 规范不能证明原始数据是 Cloud ADF，也不能证明 A/B 的转换器在表格、嵌套列表、链接或附件上发生了丢失。

### 方法 3：用 ancestors 重建导航路径，用版本接口检查时间边界

**外部事实**：Confluence 的 ancestors 接口返回从最高层祖先到直接祖先的顺序；版本接口提供页面版本历史查询。[Ancestors Operations](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-ancestors/)、[Version Operations](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-version/)

**可执行推断**：对每个输入页面生成一条稳定路径，例如 `space / domain / category / page`，并记录当前版本与抽取版本。比较 A/B 时应区分“内容缺失”和“路径/导航没有呈现”两类问题。

**未知**：原始数据是否包含完整祖先链、页面版本和删除/移动历史，需要本地检查，不能靠最终页面标题反推。

## 2. 主题分层：概念关系和显示路径分开

### 方法 4：用概念方案、broader/narrower/related 三类关系建主题轴

**外部事实**：W3C SKOS 为知识组织系统定义通用数据模型，包括 `ConceptScheme`、top concepts、`broader`/`narrower` 和 `related`；它明确区分直接声明的 broader 关系与可推导的 broaderTransitive 关系。[SKOS Reference](https://www.w3.org/TR/skos-reference/)、[SKOS Primer](https://www.w3.org/TR/skos-primer/)

**可执行推断**：主题模型至少应分开保存：

- 稳定的 `concept_id`；
- 首选名称、别名和定义；
- `broader`/`narrower` 父子关系；
- `related` 交叉关系；
- 当前读者入口使用的显示路径。

不要把一次聚类结果、输入顺序或页面 slug 当成概念身份；也不要把所有语义相关主题硬塞进父子树。显示路径可以变化，但稳定主题身份和证据关系应可回放。

**不能直接证明本项目事实**：SKOS 不规定 KnowledgeDigest 必须采用某种目录；它只提供可复用的语义边界。A/B 是否主题过粗、过细、错层或入口断裂，仍需实际目录和任务测试证明。

### 方法 5：把“主题正确”拆成分类正确、层级正确、入口可达

**外部事实**：SKOS 的概念关系与展示策略是分开的；一个概念方案可以有顶层概念，具体展示由应用决定。[SKOS Reference](https://www.w3.org/TR/skos-reference/)

**可执行推断**：A/B 比较不应只数主题数或目录深度，至少要检查三件事：

1. 用户问题能否从 Home/入口沿稳定链接到目标主题；
2. 主题是否挂在符合其定义的父类下；
3. 需要横向跳转时是否有 related/cross-link，而不是重复复制正文。

**未知**：目录深度的“最佳值”没有由上述外部资料给出，必须结合本项目读者任务测量，不能凭经验设阈值。

## 3. 摘要与证据边界：原子化、回链、分维度评分

### 方法 6：以原子事实为单位检查支持关系

**外部事实**：FActScore 将长文本拆成 atomic facts，逐条检查是否有知识来源支持；论文指出长文本常混合支持和不支持内容，因此一个二元的整篇好/坏判断不够。[FActScore](https://aclanthology.org/2023.emnlp-main.741/)

**可执行推断**：对主题页摘要和正文中的关键陈述，建立最小记录：

`claim_id → atomic_claim → source_id → source_locator → support_status`

其中 `support_status` 至少区分 `supported`、`contradicted`、`not_found/unknown`、`opinion/inference`。把“有来源链接”与“来源真的支持这句话”分开统计；同时报告支持精度与覆盖度，不能只报告一个聚合百分比。

**不能直接证明本项目事实**：FActScore 的自动模型和数据集不是本项目的验收标准；它提供的是原子化思路。A/B 的事实边界必须由项目来源片段和人工抽样复核确认。

### 方法 7：对长摘要采用 clause-level 人工复核，并用来源对齐减轻负担

**外部事实**：LongEval 研究长文摘要的人工事实性评估，报告更细粒度（例如 clause-level）可以降低标注者间差异；部分细粒度判断与完整标注结果高度相关，并建议利用摘要—来源片段对齐。[LongEval](https://aclanthology.org/2023.eacl-main.121/)

**可执行推断**：先固定一批真实读者高频主题，按句子/分句抽样，而不是让评审凭整页印象打分。每条判断都展示摘要句和对应原文片段；抽样可先覆盖 50%，再检查是否与全量结论一致。若评审意见分歧大，优先修正 claim 切分和证据定位，不先调摘要文风。

**未知**：LongEval 的数据集、语言和长文场景不等于本项目；“50% 抽样”只能作为候选起点，不能直接当作 A/B 的统计保证。

### 方法 8：把“事实一致性”与“词面相似度”分开

**外部事实**：QAGS 通过对摘要提出问题、从摘要和源文档分别回答，再用答案差异定位事实不一致；它的优点之一是能给出相对可解释的错误位置。[QAGS](https://aclanthology.org/2020.acl-main.450/)。TRUE 对多任务、多数据集的事实一致性指标做 example-level 元评估，指出 NLI 与 QA 类方法具有互补性。[TRUE](https://aclanthology.org/2022.naacl-main.287/)

**可执行推断**：自动回归至少拆成：

- 词面/语义相似度：只回答“像不像”；
- entailment/support：回答“来源能否推出这句话”；
- contradiction：回答“是否与来源冲突”；
- locator validity：回答“读者能否打开并定位到证据”。

QAGS、NLI 或 LLM judge 可以做候选筛查，但高风险陈述仍需人工复核，且报告应保留错误样例。

**不能直接证明本项目事实**：这些论文评估的是摘要模型或评估指标，不证明任何项目的自动分数与读者质量天然等价。

### 方法 9：把引用质量拆成正确性、覆盖/召回和可读性

**外部事实**：ALCE 设计了带引用的生成式信息检索评测，并将评价拆为 fluency、correctness、citation quality 三个维度，报告自动指标与人工判断的相关性。[ALCE](https://aclanthology.org/2023.emnlp-main.398/)

**可执行推断**：对每个摘要/主题页分别统计：

- 关键陈述是否被来源支持（citation correctness）；
- 关键陈述是否都给了足够来源（citation coverage/recall）；
- 读者能否沿链接看到原文、版本和定位（citation usability）。

不要把“引用数量多”当作引用质量高，也不要用一个总分掩盖“内容正确但证据不可打开”或“链接可打开但并不支持陈述”。

**未知**：ALCE 的检索语料和问答任务与内部 Confluence 不同；指标是否适合 A/B，需要在一小批真实主题上与人工标签做校准。

### 方法 10：使用目标内容单元（ACU）做稳定的人评，不让评审凭整体印象判断

**外部事实**：RoSE 研究提出基于细粒度语义单元的 Atomic Content Units，并用更稳健的人工评估比较摘要；论文还提醒，LLM 评审可能迎合无关的表面偏好，不能直接替代有针对性的人工协议。[Revisiting the Gold Standard: Grounding Summarization Evaluation with Robust Human Evaluation](https://aclanthology.org/2023.acl-long.228/)

**可执行推断**：把评审表固定成单元级问题：

- 该单元是否是来源的重要内容？
- 该单元是否被 A/B 正确表达？
- 是否有不可支持、夸大、拼接或遗漏？
- 证据链接是否能直接验证？

评审者先盲评 A/B，再看聚合统计；保留原始标签和分歧样例。LLM 可辅助预标注，但不能把它的 `pass` 当成正式读者质量证明。

## 4. 读者可用性：必须测真实任务，不只看结构指标

### 方法 11：用 effectiveness、efficiency、satisfaction 定义读者质量

**外部事实**：ISO 9241-11:2018 将 usability 放在特定用户、目标和使用情境中理解，并明确它是使用结果；该标准本身不规定唯一评估流程。[ISO 9241-11:2018](https://www.iso.org/standard/63500.html)

NIST 的公开说明将方法落成可测指标：代表性用户执行代表性任务，收集任务耗时、错误、完成率和主观满意度；其中 effectiveness 关注准确与完整，efficiency 关注资源/时间，satisfaction 关注易用、满意和有用。[NIST Usability Testing](https://www.nist.gov/programs-projects/usability-testing)

**可执行推断**：A/B 应使用同一批问题、同一批读者或匹配读者，至少记录：

- 任务成功/失败及答案正确性；
- 首次找到答案的时间、总耗时；
- 错误路径、回退次数、求助次数；
- 证据核查是否完成；
- 任务后满意度和“我是否敢据此做决定”。

**不能直接证明本项目事实**：目录层数、文件数、摘要字数、链接总数和测试通过数都不能单独证明读者可用性。

### 方法 12：先写使用情境和成功标准，再做比较

**外部事实**：ISO 9241-11 要求把用户、目标和使用情境放进 usability 讨论；ISO/TR 25060:2023 说明可用性相关信息应以一致术语和结构化信息记录。[ISO/TR 25060:2023](https://www.iso.org/standard/83763.html)

**可执行推断**：在 A/B 实测前冻结一张任务表：`读者角色 / 问题 / 期望答案 / 最短证据 / 成功标准 / 允许的时间`。没有先冻结标准，事后很容易把“看起来更漂亮”误当成质量提升。

**未知**：本项目的读者角色、问题分布、可接受耗时和“足够证据”标准尚未由本次外部研究确定，应从原始数据和真实使用场景中补齐。

## 5. 面向 A/B 的可复核审计路线

以下是基于外部方法的项目内执行建议，不是本次已经完成的 A/B 事实统计。

### 阶段 0：冻结比较边界

**事实状态：未知，待本地执行。** 对 A、B 和原始数据分别保存只读清单、文件数、字节数、相对路径、SHA-256；明确是否同一批来源、同一版本和同一语言范围。不要用“目录看起来差不多”代替输入对齐。

可复核命令示例（只读）：

```bash
find "/Users/Hugh/Downloads/KnowledgeDigest-real-reader-quality-20260814-v19" -type f -print | sort
find "/Users/Hugh/Hugh/Knowledge/CompanyBrain" -type f -print | sort
find "/Users/Hugh/Downloads/confluence 原始数据" -type f -print | sort

find "/Users/Hugh/Downloads/KnowledgeDigest-real-reader-quality-20260814-v19" -type f -print0 | xargs -0 shasum -a 256
find "/Users/Hugh/Hugh/Knowledge/CompanyBrain" -type f -print0 | xargs -0 shasum -a 256
```

### 阶段 1：结构与导航统计

对 A/B 生成同一字段表：页面/主题数、目录深度、空页、孤儿页、断链、重复主题、标题缺失、表格/列表/链接/附件保留率、来源定位覆盖率。统计必须保留分母，并按页面类型分层；不要只报一个总百分比。

建议先用纯文本工具做候选检查，再人工复核：

```bash
rg -n "^#|^##|^###|Summary|Evidence|Provenance|source_uri|digest_topic_id" \
  "/Users/Hugh/Downloads/KnowledgeDigest-real-reader-quality-20260814-v19" \
  "/Users/Hugh/Hugh/Knowledge/CompanyBrain"

rg -n "\]\([^)]*\)|https?://|source|provenance|evidence" \
  "/Users/Hugh/Downloads/KnowledgeDigest-real-reader-quality-20260814-v19" \
  "/Users/Hugh/Hugh/Knowledge/CompanyBrain"
```

**注意**：这些命令只能发现候选文本，不能证明链接有效、证据支持陈述或读者能完成任务。

### 阶段 2：证据边界抽样

从同一批主题中分层抽样，建议覆盖：高访问/高重要主题、长页、分页主题、表格密集主题、重复来源主题和疑似摘要主题。对每条摘要或关键正文陈述记录：

`claim_id, atomic_claim, A/B, source_id, source_locator, support_status, reviewer, disagreement`

输出至少包括：支持率、冲突率、unknown 率、无定位率、引用正确率、引用覆盖率；同时保存 10–20 个最典型错误样例。**unknown 不是空 findings，也不是 pass。**

### 阶段 3：盲测读者任务

用原始数据中真实会问的问题，构造 A/B 相同任务集。建议每个任务要求读者：

1. 找到答案；
2. 说出答案来自哪一页/哪一段；

3. 判断是否存在冲突、缺失或不确定；

4. 给出满意度和信心。

比较成功率、正确率、首达时间、总耗时、错误路径、证据回链率和满意度。若 A 在速度上更好但证据正确率更差，不能用单一总分抹平这个风险。

### 阶段 4：按根因优先级改进

基于以上外部方法，建议优先级为：

1. **先修抽取和 lineage**：来源身份、版本、结构节点、定位、附件/链接不能丢。
2. **再修页面类型和证据边界**：把摘要、正文、证据、推断、未知分开。
3. **再修主题轴和入口**：稳定概念身份，清楚区分父子和相关关系，保证 Home → 分类 → 主题可达。
4. **最后修摘要文风和视觉细节**：只有前面三层稳定后，简洁、标题和版式优化才有可验证收益。

## 6. 本研究的事实、推断、未知边界

### 外部事实

- Atlassian 文档支持结构化正文表示、页面层级和版本信息的读取；ADF 是带节点层级的 JSON 文档模型。
- W3C SKOS 提供概念方案、顶层概念以及 broader/narrower/related 关系。
- W3C PROV-O 提供 Entity、Activity、Agent 以及 used/generated/derived 等溯源关系；可作为 lineage 的通用建模参考。[PROV-O](https://www.w3.org/TR/prov-o/)
- 摘要研究支持原子事实、分句级人工复核、QA/NLI 互补和引用质量分维度评估。
- ISO 9241-11/NIST 支持在具体用户、目标和情境下用有效性、效率和满意度评估可用性。

### 针对本项目的推断

- A/B 比较应把“内容保留”“证据支持”“导航可达”“读者任务成功”拆开；不要用文件数量、主题数量、词面相似度或 provider/LLM 单项通过替代读者证据。
- 最有价值的改进顺序大概率是先保证可追溯和边界，再优化主题与摘要；这是方法论推断，不是对 A/B 的现状判断。
- 人工抽样和自动检查应互相校准；自动分数只作筛查或趋势，不作唯一正式结论。

### 当前未知

- A、B 是否使用同一来源集合、同一版本、同一转换边界。
- 两者在结构节点、附件、表格、链接、来源定位、主题入口和分页上的实际差异。
- 摘要中 unsupported/contradicted/unknown 陈述的真实比例。
- 真实读者在 A、B 上的成功率、耗时、错误路径和满意度。
- 哪个根因对本项目读者损失最大；需要阶段 1–3 的本地证据排序。

## 7. 研究复核记录

本次只向 AnySearch 提交了公开主题查询和公开 URL，没有提交 A/B 路径、原始数据路径、文件内容、项目代码、凭据、token、cookie 或日志。使用的公开来源类型：Atlassian Developer、W3C、ISO、NIST、ACL Anthology。

可复核的公开检索主题：

- `Confluence REST API v2 page body-format parentId version ancestors`
- `Atlassian Document Format JSON schema block inline nodes`
- `W3C SKOS broader narrower related concept scheme`
- `W3C PROV-O Entity Activity Agent provenance`
- `ISO 9241-11 usability effectiveness efficiency satisfaction`
- `QAGS TRUE FActScore ALCE LongEval summarization factuality citation evaluation`

本文件是外部方法研究，不是 A/B 审计报告；下一步若要回答“差距和根因”，必须在本地执行阶段 0–3 并把结果按“事实 / 推断 / 未知”回填。
