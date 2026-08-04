# KnowledgeDigest 知识发布架构盲审综合结论

日期：2026-08-04

本报告合并 `pi/k3`、`cursor/grok`、`claude-code/opus` 的修正版盲审，并与本地调研报告对照。三路 provider 均在修正版 hash-verified、file-only 材料包中完成 `status=completed`；没有把第一轮附件打包失败的空结果纳入意见。

盲审原文：

- `20260804-blind-review-pi-k3.md`
- `20260804-blind-review-cursor-grok.md`
- `20260804-blind-review-claude-code-opus.md`

## 一、三方一致结论

1. Task2 完成的是“来源保真与审计发布”，不是知识编译器。
2. 难读的根因不是模型名称、文件名或 300 行上限，而是：批次/来源被当成主题边界；Evidence 被当成正文；没有产品/模块/问题类型的页面合同。
3. 原始设计对 S1–S6 的保存、溯源、归档和 fail-closed 设计基本成立；S2/S3 语义决策和 S4 “提炼合并”没有真正实现。
4. “来源按主题编译成产品、模块、场景、规则、技术、经验页面”必须是核心交付。只改 slug、Summary、目录或分页，不能超过 CompanyBrain。
5. 当前“两层架构：S1–S6 保真层 + Knowledge Compiler 编译层”方向正确，但原方案把 v1 本体、实体、8 类页面、候选生命周期做得过重。
6. 失败降级、审计账本和交付包拆分应提前；不能等到全量发布任务才处理。
7. 原方案最重要的遗漏是“读者能否回答真实问题”的硬合同；研究报告已经补上，但需要把它变成代码级发布阻断，而不是报告里的描述。
8. 原方案还没有解决长期增量：`digest(new_dir, kb_dir)` 与“全量 TopicPlan”如何共存、已发布页面如何稳定更新、人工修订如何不被覆盖。

## 二、盲审对当前方案的关键修正

### 1. 无损和可读必须是两个产物

当前方案曾写“每个正文段绑定 Claim/Evidence”。这句话如果继续沿用现有的“Claim 原文必须逐字出现在正文”校验，会再次得到 Evidence dump。

修正为：

- `reader page`：类型化、可读、按问题组织；正文段只保存 `claim_id` 引用和必要的来源链接，不要求把 Claim 原文逐字复制进去。
- `source archive`：保留完整原文、表格、图片 URL、行定位和 Claim 证据，负责不丢失。
- 忠实性：检查 `claim_id` 可解析、数字/标识符/版本不变、抽样蕴含和人工核验；不再用字符串包含证明“可读”。

### 2. v1 不做完整本体

保留受管的 `ProductGazetteer`，不要一次建立十维 `KnowledgeEntity`。

v1 只需要：

- 产品/系统 slug；
- 产品内模块 slug；
- 别名；
- 对象/功能名；
- 置信度和冲突原因。

词典由项目维护并版本化，模型只能提出候选；不能让 LLM 自动扩展正式产品目录。

主轴明确为：

```text
产品/系统 → 模块/能力 → 页面
```

客户、研发、运营等领域只作为查询 facet，不作为正文主目录。这样才不会再次把 EMM、AE、iOS、GoInsight 混在同一叶分类里。

### 3. v1 压缩为三类正式页面

不要一次实现八类页面。首版只做：

1. `product_overview`：产品定位、适用场景、能力边界、入口。
2. `module_or_capability`：模块/功能是什么、入口、前置条件、相关能力。
3. `procedure_or_rule`：操作步骤、规则、部署、异常、限制、版本和经验。

原文档案页不算正式知识页，用于承接失败、低置信和未编译来源。案例、版本历史、技术实现等，等语料证明有稳定需求后再增加类型。

### 4. 对外只保留两个终态

原方案的 `raw → candidate → formal` 作为内部规划状态容易变成永久堆积，尤其原始方案明确没有人工复核工作流。

建议对外只暴露：

- `published`：进入读者包和正式导航；
- `degraded`：保留原文档案和失败原因，不进入正式导航。

内部可以暂时使用 `draft`，但不把长期 `candidate` 当成完成态。若未来要做人审晋级，再单独设计人工复核任务，不在本次任务偷渡。

### 5. 先做增量语义，再谈全量规划

“全量 TopicPlan”只适用于首次导入或显式重建，不能成为每次 `digest(new_dir, kb_dir)` 的默认行为。

正常增量规则：

```text
新来源 → 归一化 → 匹配已有 Product/Module/TopicIndex
       → 只重编译受影响主题
       → 新主题需要显式稳定键和旧路径映射
```

Topic identity 必须与批次、输入顺序、来源 hash 集合解耦，例如由“产品 + 模块 + 对象/问题意图”组成。初次导入仍要先拿全量清单做一次规划；之后只做局部重规划。既有正式页路径不能因日常更新改名，必要时保存旧路径重定向。

## 三、修订后的架构

```text
S1–S6 Preservation Layer
  ├─ source snapshot / claim / provenance / archive
  ├─ ledger reconciliation / pre-write audit
  └─ raw source archive
          ↓
Structure Normalizer
  └─ 标题层级、父子页、表格、FAQ、图片引用、双语和噪声标记
          ↓
ProductGazetteer + TopicIndex
  └─ 产品/模块主轴；跨批次规划；单源默认 degraded
          ↓
Typed Page Compiler
  └─ 3 类正式页面；正文与原文证据分离；claim_id 回指
          ↓
Publication Gate
  ├─ published reader package
  └─ degraded archive/audit package
```

保留原项目的文件型 KB、人工触发、单写者、原子写、写前归档、Jaccard fallback 和 no-LLM 离线验证；不引入数据库、向量数据库、调度器、CAS、journal 或 AgentMemory。

## 四、修订后的任务顺序

### 任务 0：诚实化和交付包（先做）

不改变语义编译，先修可见错误和质量造假风险：

- S6 provenance 审计移到 writeback 前；失败不写 formal。
- `batch sources = snapshots = source-index`，缺失来源显式失败；`duplicates` 幂等。
- provider 成功、Claim 验证、写回、质量状态分开，`written` 不覆盖空的 `quality`。
- provider 失败、embedding 降级、无产品归属的来源只能进入档案包，不进 formal 导航。
- reader package 与 audit package 分离；默认打开的目录不能包含 `_digest`、`_archive`、provider 日志和比较报告。
- Home 的待复核入口必须指向真实队列；删除空分类页；source-index 目标必须是可点击链接。

完成后，即使不改正文，读者也不再被 58 个占位页和 279MB 运行现场误导。

### 任务 1：主题和产品主轴

- 建立受管 `ProductGazetteer`：只从本批真实语料提取，CompanyBrain 只作参照。
- 建立 `TopicIndex`：稳定 topic key、产品、模块、对象/问题意图、来源成员、路径和状态。
- 单源默认 `degraded`；只有完整独立手册、产品模块明确、无冲突时才允许发布。
- 同产品同对象的来源必须进入同一计划；不同产品同名对象必须显式分开。
- 批次不产生 topic；增加 batch-size 1/20 不得改变 topic 集合和正式路径。

### 任务 2：小语料正文编译闭环

用 12–20 篇代表性语料打穿，不先全量：多源同产品、单源手册、超长、表格密集、中英混排、provider 失败、无 body 各至少覆盖一例。

- Structure Normalizer → TopicIndex → typed draft → Publication Gate。
- 解除 `final_body` 被禁止和“Claim 原文逐字包含”这两个互相冲突的旧合同。
- 真正填充 `old_target_body`，支持语义 revise，而不是拼接历史 Claim。
- formal 正文只能由三个页面类型渲染；Evidence 和完整原文进入 archive。
- 每段保存 claim_id、来源链接和必要 locator；失败只产 `degraded` 档案。
- 20 个读者问题每次都跑，不能等到全量任务才第一次验收。

### 任务 3：导航和全量发布

- 生成产品索引、产品总览、模块总览和页面导航；目录按真实实例出现，空模块不生成。
- 冻结 input manifest、产品词典版本、页面合同、provider/model 和运行参数。
- 对 89 篇全量运行；同一套问题对比 Task2、CompanyBrain 和新产物。
- 只有机器门、真实人工读者门和 `human_reviewed` 全部完成，才称正式发布。

## 五、硬质量门禁

### 机器门

- 三方来源清单一致；Claim/duplicate/history 统计幂等；S6 在写回前通过。
- batch-size 1 与 20 的 TopicIndex 和正式路径一致。
- 正式路径必须包含产品语义 slug；禁止 `topic-<hex>`、裸 `1.md`、`ae.md`、`ios.md` 等主入口名。
- `product_slug`、module 归属和页面类型在正式页不为空；冲突只能 degraded。
- 正式页不出现“请阅读 Evidence”“来源未说明”“Missing”“暂无已验证的相关主题”等占位串。
- 正文必须有页面类型必需 section；不能以 Evidence 区代替正文；禁止连续大段原文和图片 URL 堆。
- provider 失败、JSON 破损、embedding 语义降级、无 body、事实冲突均不得进入 formal 导航。
- 相关主题只能由同产品/同模块/共享来源/原文显式互引等结构证据产生；无关系则省略，不写统一空句。
- 空分类、断链、不可点击 source-index、旧 part 误入当前导航均失败。
- reader package 不含 `_digest`/`_archive`/provider 日志；完整原文仍在独立 archive。

### 读者门

- 预注册至少 20 个真实问题，包含 2–3 个“应该查不到”的负样本。
- 首次命中正确率 ≥85%；不设机械的“最多 4 跳”，而要求每一跳都说明适用问题、边界和下一跳。
- 标题脱离路径仍可理解率 ≥90%；产品/模块归属人工准确率 ≥90%。
- 正式页能独立回答“是什么、怎么用、限制/异常、适用版本、来源”，不需要打开原文档案才能理解主答案。
- 报告必须分开记录 `machine_pass`、`agent_assisted`、`human_reviewed`；未完成人工审查不能称发布完成。
- 任一读者门失败，运行状态只能是 `degraded`，旧 formal 知识不被覆盖。

## 六、最终调整结论

盲审没有推翻“两层架构 + Knowledge Compiler”主方案，但把它从“先建完整知识宇宙”收缩为“先修诚实性，再用三类页面完成一条产品竖切，再扩量”。

本次必须新增的设计约束：

1. 无损证据与可读正文分离，不能继续用逐字 Claim 包含验证可读性。
2. 主轴固定为产品/系统，领域只做 facet。
3. 正常运行支持局部增量重编译；全量规划只用于首次导入或显式重建。
4. v1 只有三类正式页面；产品词典受管，模型不能自动扩展正式目录。
5. 先做任务 0 诚实化和交付包，再做主题和正文编译；不要先写完整本体规格。
6. 机器门必须阻断失败 formal 写入，人工门只负责确认读者效果，不能替代代码阻断。

这比原三任务方案更小、更稳，也更直接对应“超过 CompanyBrain、让人读得懂并能复用”的真实目标。
