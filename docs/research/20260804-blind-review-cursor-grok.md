# 3rd-review 盲审：cursor/grok

- provider: `cursor/grok`
- status: `completed`
- runtime: `a00dbdbd-f0c2-4bd1-96bb-f9c25aec74ad`
- 材料：修正版 hash-verified file-only bundle

---

先按你的约束，只用 third-review-bundle 的只读工具读取指定冻结材料。按你指定的逻辑路径逐个读取，不列目录。请求被拒，改用 `list_bundle` 确认可用路径，并尝试不同路径写法。路径是相对 bundle 根目录的；开始批量读取全部材料。继续读取剩余设计、对比与样本材料。继续读取剩余样本页。材料已齐，下面给出独立盲审结论。

---

## 结论（不超过 8 条）

1. Task2 完成的是**来源保真与审计发布**，不是知识编译；难读/难查/难复用的根因是“一来源一主题 + Evidence 当正文 + 无产品/模块页面合同”，不是标题丑或 300 行太短。
2. 原始方案 S1–S6 在保存/溯源上大体兑现，但方案本身就把“Claim 可回指、不截断、页不超长”当成质量代理，**从未把知识发布质量写成可验收合同**。
3. research 的两层拆分（Preservation + Compiler）、raw/candidate/formal、读者硬门、拒绝假修复——方向正确，应批准其问题诊断，**不批准其作为最小可行方案的全部范围**。
4. 第一版本体过重（多实体 + 八类页面 + 全量 TopicPlan + 三项大任务）有“先建宇宙再证明能编译”的风险；应先用**产品/模块 + 3–4 种页面类型**在小语料打穿。
5. **“按主题把来源编译成产品/模块/场景/规则等页面”必须是核心**；否则永远超过不了 CompanyBrain。
6. 必须把批次、单源自动成主题、哈希读者路径、Evidence dump、LLM 失败占位进 formal 写成**硬不变量**，否则会复发。
7. 交付分包、formal 导航隔离失败页，是低成本高收益项，不应拖到全量任务末尾。
8. 能明显超过 CompanyBrain 的标准不是文件更多，而是：**同一问题更快找到、正文可独立作答、边界/版本清晰、失败不伪装正式、机器与人工门禁分开**。

---

## 根因证据

**根因（架构）**

- 主题粒度错：86 主题中 85 为单来源，`batch_size: 1`；聚类 ID/来源哈希被当成读者主题，批次成了知识边界。
- 编译缺失：`publication-only` 禁 `final_body`，正文仍是 Evidence/Claim 拼接；统一六段壳（Summary/Why/Version/Related/Evidence/Provenance）不按问题重组。
- 无本体：`product_slug=0`；EMM/AE/iOS/GoInsight 混在同一叶目录；分类是标签不是产品→模块→任务。
- 质量合同错位：Claim/页长/断链/写回成功通过，读者任务与人工审查未成为发布门；`quality.status` 空、`benefit_status=unmeasured` 仍记 batch succeeded。

**表面症状（由根因导出）**

- 58/120 Summary 为“请阅读 Evidence”；58/120 Why 占位；120/120 Related 空；哈希/短名路径；13/21 空分类；31 失败源仍有正式页；279MB 中审计远大于正文。

**对照样本**

- Task2 `Home` 仅六领域入口 + 空 pending；`ae.md` Summary 失败占位，Evidence 为 Confluence 原文堆叠，Provenance 空。
- CompanyBrain `Home`/产品索引/GoInsight 模块总览：用途说明、产品入口、模块分层、资料汇总与正式页分离。

---

## 原方案实现缺口

| 层次 | 状态 |
| --- | --- |
| S1 指纹/空壳/快照，S5 原子写/归档，S6 Claim 回指 | 基本实现（保存层） |
| S2 complete-linkage 形态与队列；S3 top-k 与 new/revise/merge 规则路径 | 工程实现，但非语义主题/页面规划 |
| Task2 taxonomy、Home/indexes、稳定 topic、300 行分页、source-index | 发布**形式**实现，非发布**质量** |
| F1–F7、S3 LLM 路径判定、S4 可读提炼、`old_target_body` 真重写、`remove_with_reason` 真协议 | 未兑现或仅壳 |
| 产品/模块/场景/页面类型、场景导航、raw→formal 晋级、固定读者任务硬门 | 原方案未定义；调研有样例未译成合同 |

判断：原方案实现了“不丢、可审计的 digest”，**没有实现、也几乎没有设计**“CompanyBrain 级知识产品”。缺口首先在方案合同，其次才在 Task2 实现。

---

## 对当前修复方向的批评

**应保留**

- 保存层与编译层分离；禁止继续堆 `publication.py` 字段。
- 跨来源 TopicPlan、类型化正文、Claim 回指、raw/candidate/formal、读者硬门、三项任务连续推进、假修复黑名单。

**遗漏**

- 未把“禁止 batch/单源自动等于 formal 主题”写成管线第一不变量与测试。
- 未规定**增量编译**：新来源挂既有产品/模块 TopicPlan，而非每轮全量重规划才可用。
- 交付分包、失败不出 formal 导航——应作为 Task A/B 早期硬门，不应主要压在 Task C。
- 账本闭合（source-index vs snapshot vs batch、duplicates 幂等、S6 写前回审）未纳入修复主路径。
- 页面类型缺少“何时**不**合并/不拆”的冲突规则（同名 AE、跨产品词面相似）。

**过度设计**

- 首版 `KnowledgeEntity` 覆盖领域/产品/模块/对象/角色/场景/版本/边界/别名/置信度过重；八类页面一次上齐成本过高。
- Task A“抽全本体 + 全模型 + 20 题”再写编译器，易空转；应**小语料编译闭环**与合同共进。
- “全量 TopicPlan → 再编译”若无产品种子词典，可能再造一层错误抽象。

**错误优先级**

- 把“定义宇宙”放在“证明一页可读可查”之前。
- 低估早期即可做的：formal 隔离占位页、审计包拆分、语义路径（hash 仅内部 ID）。
- 三项任务边界合理，但 A 应瘦身为**最小页面合同 + 产品/模块词典 + 验收题**，B 才是主战场。

---

## 建议的最小可行修复架构

```text
S1–S6 保存层（只增不删）
  → 来源结构归一（标题/产品路径/章节意图；噪声标记）
  → 最小实体：Product + Module（+ 别名表）
  → TopicPlan（跨批次、可多源；单源默认 candidate）
  → 页面类型编译（先 4 类）→ Claim/Evidence 回指
  → 状态：raw | candidate | formal
  → 读者包 ∪ 独立审计包
```

**核心原则**

1. **主题编译是核心**：来源按主题编译成产品总览 / 模块总览 / 操作或规则页 / 经验或边界页；Evidence 永不当 formal 正文。
2. 首版页面类型只保留四类：产品总览、模块总览、操作/规则、经验/边界；技术/版本/案例等有稳定模板后再加。
3. TopicPlan 身份 = 产品/模块/问题意图，**不是** batch_id、cluster_id、source_uri、文件哈希。
4. LLM 只填结构化 Draft 段落且每段绑 Claim；失败 → raw/candidate + 原文档案，**禁止**占位 Summary 进 formal 导航。
5. 路径/H1 语义化；稳定 ID 仅 frontmatter；分页必须有主题总览与上下页。

**防复发不变量**

| 风险 | 硬约束 |
| --- | --- |
| 批次边界 | 传输批次 ≠ TopicPlan；跨批必须能归入同一 plan |
| 单源聚类 | 单源可建 plan，默认 candidate；多源或词典命中才可冲 formal |
| 哈希文件名 | formal 路径禁止 `topic-<hex>` 作主路径 |
| Evidence dump | formal 无“请阅读 Evidence”式摘要；Evidence 仅证据区 |
| LLM 失败 | provider/JSON/超时不得 `published/formal`；与 batch succeeded 解耦 |

---

## 任务拆分与顺序

1. **P0（几天，可与合同并行）**：读者包与审计包分离；needs-review/占位页移出 formal 导航；Home pending 指向真队列；source-index 可点击且与 snapshot/batch 集合对齐。
2. **A′ 最小发布合同**：Product/Module 词典（本批语料）、4 类页面必填字段、TopicPlan 状态机、20 道读者题与评分表；不追求完整 ontology 引擎。
3. **B 编译器小闭环（12–20 篇，建议含 GoInsight/EMM/AE）**：结构归一 → TopicPlan → 类型化正文 → Claim 回指；证明多源可合、独立流程不合、无 Evidence 正文。
4. **B2 防复发门**：单测/验收锁死上表五条不变量。
5. **C 全量发布**：冻结词典/TopicPlan/模型/manifest；全量跑；同一 20 题对比 Task2/CompanyBrain；仅 human_reviewed + machine 全绿可称最终发布。

顺序要点：**先可读可查的一条产品竖切，再横向扩本体与语料**；不要先建八类页面宇宙。

---

## 硬质量门禁

**机器底线（保留）**：Claim 可回放、有效来源索引、路径安全、无断链、原子/归档写、离线可读；source-index≡snapshots≡batch；duplicates 幂等。

**发布状态门**

- formal 导航零占位 Summary/Why；零 provider_failure Claim。
- `written` ≠ 质量通过；须分 provider / claim_verified / formal / human_reviewed。

**读者硬门（未过不得 formal 全量）**

- 20 题均有入口；Home→答案 ≤4 跳。
- 脱离路径仍能理解标题；产品/模块归属人工准确率 ≥90%。
- formal 正文含页面类型要求的用途/步骤或规则/边界/版本或显式“来源未载版本”/来源；Evidence 不替代正文。
- 相关主题非统一空占位；无关联须显式声明。
- 多源应合并主题有合并证据；不应合并者有分离证据。
- 对比报告区分 `machine_pass` / `agent_assisted` / `human_reviewed`，后两者不可冒充。

**超过 CompanyBrain 的附加条**

- 低置信进资料汇总/candidate，有晋级记录；编译失败可定位到页与来源；增量更新不毁掉已 formal 页的稳定路径。

---

## 最危险的三条误区

1. **用更强模型/更好 Summary prompt/更长行数/更漂亮 slug 冒充架构修复**——不改变“单源 Evidence 页”本质。
2. **先造完整 ontology/八类页面/全量 TopicPlan，再证明一页可读**——重蹈“合同很完整、产物仍不能用”。
3. **为可读性削弱 Claim/归档/fail-closed，或把失败降级页继续留在 formal 主导航**——前者重复 CompanyBrain 丢信息；后者重复 Task2“机器绿、人不可用”。