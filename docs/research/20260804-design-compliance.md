# 原始方案实现度与知识质量合同审查

日期：2026-08-04  
范围：原始设计、Task2 规格、当前 S1-S6 代码与验收记录。只读审查，不调用外部模型。

## 结论

KnowledgeDigest 的“保存层”大体已经实现：来源快照、Claim、Evidence、Provenance、归档、原子写、失败回退和分页都有代码与测试。原始方案对工程安全和“不丢资料”考虑得较完整。

但“知识产品层”没有完整实现。原始方案把 Claim 可追溯、Evidence 存在、faithfulness 和页长当作质量主要代理指标，却没有把知识本体、页面职责、场景入口、正文编译和读者任务做成正式阶段。因此当前结果可以机器验证为“无损、可回溯、结构合法”，仍然可能是“主题混杂、标题像文件名、正文像原文堆叠、读者无法使用”。这不是单一模型故障，而是方案缺少发布质量合同。

## 一、原始 S1-S6 实现度

| 阶段 | 判断 | 证据与影响 |
|---|---|---|
| S1 Ingest | 基本实现，语义元数据部分缺失 | `ingest.py:131-284` 有扩展名读取、URI、指纹、空壳门禁、重复/冲突检测、快照和 URL 引用；非文本引用只是正则 URL（`:83-85`），没有附件/截图/父子页/来源类型一等字段。质量门能防坏来源，不能为后续页面规划提供足够上下文。 |
| S2 Cluster | 工程实现，知识聚类部分实现 | `cluster.py:20-79` 是 complete-linkage 和 auto/needs-review/insufficient 分层；`pipeline.py:61-183` 支持 embedding 失败后整次回退 Jaccard。它解决相似度分组，不识别产品、模块、业务对象、任务或知识类型；最终语料还记录 jina 探测失败，实际不是语义 embedding。 |
| S3 Retrieve | 部分实现 | `retrieve.py:48-124` 做 top-k 相似度和阈值决定 `new/revise/merge_multiple`，但原始设计 `universal-knowledge-digest-design.md:95-100` 要求 LLM 结合候选页面作路径判断。当前函数没有独立的对象/页面规划，也没有把“同一来源应拆成哪些业务页面”作为决策。聚类结果容易直接变成主题页。 |
| S4 Synthesize | 安全门实现，知识编译未实现 | `draft.py:528-549` 的离线 generator 是原文身份回写；`draft.py:1296-1314` 失败时回退 claim 拼接；`draft.py:1418-1447` 只校验 title/category/summary/why/version 的字段建议。代码有 claim/faithfulness/coverage 和拆分，但没有“来源类型→知识对象→页面类型→正文模板→读者场景”的编译阶段。 |
| S5 Commit | 基本实现 | `writeback.py:110-133` 实现临时文件、fsync、原子替换和目录 fsync；归档与导航同批写回由 `pipeline.py:903-964` 串联。原始设计明确删掉 CAS/journal（`:121-130`），所以这不是遗漏；强制杀进程的多文件一致性仍是已知边界。 |
| S6 Provenance | 基本实现 | `provenance.py:49-124` 对每个 Claim 校验有效来源快照、成功目标页、定位、指纹和验证状态；归档记录保留原文（`:127-174`）。这能证明“从哪来”，不能证明“读者能否理解或完成任务”。 |

## 二、原始方案的九条防丢失设计

原始方案 `universal-knowledge-digest-design.md:172-184` 明确列出九类 CompanyBrain 教训。当前代码大致完成了空壳隔离、来源指纹、FAQ/代码块组件保护、失败来源拒绝索引、归档不删除和 Claim 回溯；但有三项不能等同于知识质量：

1. `max_doc_lines` 被实现为拆分/300 行发布门（`page_layout.py:397-455`、`:756-806`），它防止巨页，却没有规定每个页面回答什么问题、如何按业务对象切分。
2. 非文本引用在 S1 只收集 URL（`ingest.py:83-85`、`:271-274`），没有图像、附件、截图说明或“视觉证据仍可见”的页面合同。
3. 表格在 Evidence 中通常原样保留，但方案没有要求表格字段语义化、状态机/枚举/条件与正文模板分别编译；“不丢表格”不等于“读者能用表格”。

Why/Version 虽有结构字段校验（`kb_structure.py:543-565`），发布回退却统一写占位语义（`publication.py:152-188`），所以形式上满足字段存在，实际没有回答“为什么使用/何时适用/当前版本是什么”。

## 三、原始方案与调研覆盖度

### 已覆盖

- 原始设计 `:8-24` 引用了 ovmc 聚类、sleep-curator、CompanyBrain 丢失分析和开源项目比较；`docs/research/ovmc-analysis.md`、`sleep-curator-report.md`、`goinsight-loss-report.md`、`sc-cb-analysis.md` 对算法、安全和信息丢失有足够工程证据。
- 原始设计 `:50-62` 明确了增量、文件 KB、离线、手动触发和非目标；`:81-119` 定义了 S1-S6；`:172-184` 定义了防丢失底线。

### 缺失或不完整

1. **知识本体**：没有产品、模块、业务对象、任务、规则、版本、边界、别名和关系模型；聚类被默认当作页面。
2. **页面规划**：没有总览页、模块页、场景页、规则页、排障页的类型和切分规则。
3. **正文编译**：没有把“是什么/何时使用/步骤或规则/限制/异常/版本/来源”编译成稳定模板，Evidence 被迫兼任正文。
4. **读者质量**：原始 Phase 0/1 主要验收 fixture、溯源、空壳和超长文档（`:190-202`），没有固定真实问题集、答案完整性、阅读时间和人工停止门。
5. **治理生命周期**：原始方案把 needs-review 限定为队列文件（`:56-62`、`:87-93`），没有 pending→candidate→formal 的编译/晋级规则。
6. **研究可复现性**：方案用 OpenViking 的绝对路径引用研究（`:8-24`），没有为外部材料绑定版本/hash、采样清单和生成命令；脱离外部 repo 后不具备自证性。
7. **Confluence 特征研究**：没有把父子页、表格、截图、FAQ、双语、版本页、跨产品引用和导出重复率量化为实现输入。

因此，现有调研足够支撑“如何安全处理文件”，不足以支撑“如何把 89 篇原始资料编译成 CompanyBrain 级知识”。详细证据见 `20260804-design-research-coverage.md`。

## 四、Task2 解决了什么，没解决什么

Task2 规格确实补了语义标题、受控两级分类、Home/分类/来源索引、字段引用、离线阅读和 CompanyBrain 抽样（`spec.md:8-43`、`:45-69`、`:73-130`、`:166-172`）。这是正确方向，但仍把发布层建模为“主题页固定字段 + Evidence”，没有把本体、页面类型、场景和正文编译变成一等对象。

最关键的是，Task2 自己的完成账本没有宣称读者质量已经通过：

- `tasks.md:1081-1097` 明确 AC-002/AC-007 只有部分证据，人工阅读不能由 Codex audit 替代。
- `tasks.md:1113-1125` 的 final9 记录 89/89 批次、86 个主题、120 页、jina 探测失败后回退 Jaccard、30 次 provider 失败、fallback ratio `0.471591`；AC-007 人工确认仍开放。

当前代码也直接暴露这一风险：

- `publication.py:58-105` 的离线分类是少量关键词计分；它是保守 fallback，不是产品/模块知识分类器。
- `publication.py:152-188` 在缺少合法建议时固定生成“来源未提供摘要；请阅读 Evidence”“来源未说明”“未提供版本信息”，并把所有 Claim 作为引用；这通过字段合同，却不生成有用知识。
- `page_layout.py:295-369` 只负责 Summary/Why/Version/Evidence/Provenance 外壳；`page_layout.py:566-854` 先按稳定 topic 聚合再分页，但没有页面职责或场景编译。
- `navigation.py:127-220` 生成 README/Home/分类链接；导航可达不代表分类语义正确，Home 也没有按用户问题组织入口。

## 五、导致低质量结果的因果链

```text
原始来源
  → Claim/相似度簇
  → 稳定 topic_id
  → 语义字段建议（标题/分类/摘要）
  → Evidence 原文分页
```

缺少：

```text
来源类型/实体识别
  → 知识本体与对象字典
  → 页面规划（总览/模块/场景/规则/排障）
  → 正文编译与状态治理
  → 读者任务验收
```

所以“结构合法”的页面仍会出现：文件名像 hash、多个产品/模块混在一个主题、标题只是来源标题拼接、Summary/Why 是占位或泛化句、Evidence 变成难读的原文堆叠、来源失败只被标记而没有正式治理路径。

## 六、修复方向（供主任务汇总）

保留现有 S1-S6 作为保存层，不继续往 `publication.py` 堆字段。新增发布层合同：

1. **Ontology**：产品、模块、对象、任务、知识类型、版本、边界、别名、关系和置信度。
2. **Page planner**：cluster 只能提供候选证据；程序/模型共同决定总览、模块、场景、规则、排障和来源页，禁止“一簇一页”。
3. **Compiler**：按页面类型生成“是什么、何时使用、步骤/规则、限制、异常、版本、来源”；Evidence 只做证据区，不替代正文。
4. **Governance**：`raw → candidate → formal → needs_review`；来源缺失、模型失败、事实冲突、待人工编译必须区分，不能共用一个占位字符串。
5. **Reader gate**：固定真实问题集和 CompanyBrain 对照；验收标题理解、入口跳数、答案完整性、适用边界、版本、跨页导航、来源回溯和阅读时间。任一关键维度失败，结果只能叫 candidate，不能叫最终发布。

## 证据索引

- 原始设计：`docs/plans/universal-knowledge-digest-design.md:8-24,48-62,81-119,172-202,215-239`
- Task2 规格：`specs/archive/knowledge-digest-llm-naming-classification/spec.md:8-43,45-69,73-130,166-189`
- Task2 账本：`specs/archive/knowledge-digest-llm-naming-classification/tasks.md:1081-1125`
- 代码：`src/knowledge_digest/ingest.py:83-85,131-284`; `cluster.py:20-79`; `retrieve.py:48-124`; `publication.py:58-105,152-188`; `draft.py:528-549,1296-1314,1418-1447`; `page_layout.py:295-369,397-455,566-854`; `navigation.py:127-220`; `provenance.py:49-174`; `writeback.py:110-133`
- 调研覆盖：`docs/research/20260804-design-research-coverage.md`
- S4-S6 细审：`docs/research/20260804-design-s4-s6.md`（S5/S6 机器安全基本落地；S4 主题级语义重组、`old_target_body` 和真实 `remove_with_reason` 缺失；S6 在写回后审计、source-index 事务边界有缺口）
