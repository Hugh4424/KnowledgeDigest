# Task2 重排与 OKF 结构化方案审查

日期：2026-08-06  
范围：只读检查当前 `main`（Task0、Task1 已合并）、现有 PRD、Task2 历史产物和 Google Open Knowledge Format（OKF）v0.2。没有修改代码、PRD 或下载结果。

## 结论

现在不适合直接进入原 PRD 的 Task2。Task0、Task1 主要解决了“运行是否诚实、来源是否可追溯、主题身份是否稳定”，但还没有解决“一个 Markdown 文件到底是什么知识对象、读者为什么要读、如何从入口逐层找到答案”。如果直接继续原 Task2，最可能得到的是一个带稳定 TopicIndex 的 Evidence 发布器，而不是 CompanyBrain 级知识库。

建议把下一阶段改成三个连续的小任务，再做全量发布：

```text
Task 2A  OKF-compatible Concept Contract + Reader Bundle 骨架
    ↓
Task 2B  知识对象规划与正文编译（小语料）
    ↓
Task 2C  读者质量、信任信号与发布门（小语料）
    ↓
Task 3   89 条全量发布、对比和人工验收
```

这不是引入 OKF 运行时，也不是重写 Task0/Task1；是把当前缺失的“知识发布层”拆开，先固定文件合同和目录，再做内容编译，最后才跑全量。

## 一、当前 Task0/Task1 已经解决什么

### Task0

Task0 已把账本、快照、写回前门、页级 `published/degraded`、交付级 `released/not_released`、Reader/Audit 分离和失败不伪装成功固定下来。这些是必须保留的保存层底线。

### Task1

`src/knowledge_digest/topic_axis.py` 已提供：

- `SourceInventory`：来源 URI、指纹、标题/H1、父路径、结构特征和来源边。
- `ProductGazetteer`：产品、模块、别名、owner、来源证据和候选/冲突状态。
- `TopicPlan`/`TopicIndex`：版本化 `topic_key`、source members、正式路径和旧路径映射。
- `affected_set`：增量变更、来源边和旧路径关系的影响范围。
- `find_managed_conflicts`：检测人工修改，避免静默覆盖。

Task1 的 `run_topic_axis()` 明确只写 `_digest/source-inventory.jsonl`、`topic-plan.json`、`topic-index.json` 和运行报告，状态为 `not_released`，不生成正文。这是正确边界，但也说明它不能被误认为已经完成知识结构化。

## 二、当前结果为什么仍然“不像知识库”

### 1. TopicIndex 不是知识本体

当前稳定 key 的核心形态是：

```text
v2/<knowledge_type>/<product>/<module>/<object_intent>
```

它解决“主题身份稳定”，不回答：

- 这是产品总览、模块说明、操作流程、规则、技术参考还是排障记录？
- 读者要完成什么任务？
- 这条事实的适用范围、前置条件、限制和异常是什么？
- 哪些页面是父级概念，哪些页面是可执行步骤？

Task1 的 `knowledge_type` 是来源声明的类型注册，不是 OKF 的概念 `type`，也不是 CompanyBrain 的页面职责。两者不能混用。

### 2. 旧 Task2 把 Evidence 当成正文

历史产物仍有典型结构：`Summary → Why → Version → Related topics → Evidence → Provenance`。Evidence 保存很完整，但 `publication.py` 的失败回退会写入“请阅读 Evidence”“来源未说明”“未提供版本信息”等占位；`page_layout.py` 主要负责外壳和 300 行分页，而不是把原文编译成读者任务页。

现有审计已统计：120 页中 58 页 Summary 是 fallback，58 页 Why 是占位，54 页 Version 缺失类值，Related topics 全部为空。这里的根因不是模型换得不够好，而是没有“概念对象 → 页面职责 → 正文结构”的编译层。

### 3. 目录有链接，但没有渐进式知识入口

旧产物的 `Home.md → indexes → pages` 可以到达页面，但存在大量空分类，产品总览、模块总览、场景入口和跨页关系不足。CompanyBrain 的优势是先给“产品定位、模块手册、技术实现、经验与坑、规范与资产”，再进入具体页面；不是简单把来源文件按标签放到目录里。

### 4. 质量信号只在隐藏审计区

当前 `page_status`、`delivery_status`、Claim 和 source index 能够审计，但读者打开一个页面时看不到：由什么产生、基于哪些来源、何时生成、是否验证、是否过期、是否已废弃。信任信息没有进入概念页的 frontmatter，也没有形成可过滤的 Reader Bundle。

## 三、OKF v0.2 可以借什么

参考：

- [Google Cloud：OKF v0.2 adds trust signals](https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals)
- [OKF v0.2 SPEC.md](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/main/okf/SPEC.md)
- [GoogleCloudPlatform/knowledge-catalog/okf](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)

OKF 的关键不是某个固定分类，而是一个“可被人、Agent、脚本共同读取的 Markdown bundle”合同：

1. 每个 Markdown 文件是一个独立 **Concept**，文件路径是稳定 Concept ID。
2. YAML frontmatter 放少量可查询字段；正文保留结构化 Markdown、示例和解释。
3. 任何目录都可以有 `index.md`，用于 progressive disclosure；目录结构和普通 Markdown 链接共同形成树 + 图。
4. `sources` 记录来源；正文通过稳定 source id 做逐条归因，而不是页面底部一团无法定位的来源清单。
5. `generated` 和 `verified` 分开：谁生成不等于谁确认。
6. `status`（`draft/stable/deprecated`）和 `stale_after` 表达生命周期和新鲜度。
7. OKF 记录客观信号，不保存不可迁移的“可信度分数”。消费者自行决定过滤策略。
8. `type` 是唯一必填概念字段；OKF 不强制一个中央本体，未知类型必须可容忍。

## 四、哪些 OKF 内容适合 KnowledgeDigest

### 应采纳：作为输出合同的兼容子集

Task2A 应新增 `KnowledgeDigest Concept Contract v1`，兼容 OKF v0.2 的通用字段，同时保留本项目自己的审计字段：

```yaml
---
type: Capability                 # 或 Product Overview / Procedure / Rule / Technical Reference
title: 可读的人类标题
description: 一句话说明这个概念解决什么问题
tags: [产品, 模块, 场景]
generated:
  by: knowledgedigest/<version-or-commit>
  at: 2026-08-06T00:00:00Z
verified:
  - by: process:knowledgedigest-machine-gates
    at: 2026-08-06T00:00:00Z
status: stable                   # draft / stable / deprecated
stale_after: 2026-12-31          # 只有来源或规则真的提供复核日期时才写
sources:
  - id: src-001
    resource: confluence://...
    title: 原始来源标题
    last_modified: 2026-07-01
    content_fingerprint: sha256:...
digest_topic_id: ...
topic_key: v2/...
product: ...
module: ...
page_status: published
delivery_status: not_released
---
```

约束：

- 不生成虚假的 `author`、`usage_count`、`last_modified` 或 `stale_after`；缺失就省略。
- 不生成 `trust_score`；信任层级由 `verified` 和消费者推导。
- `verified` 的机器事件不能冒充人工验收；人工事件只在 Task2C/Task3 真实完成后添加。
- `digest_topic_id`、`topic_key`、Claim/locator 和旧路径映射继续保留，不能被 OKF 字段替代。

### 应采纳：概念路径和 index

建议最终 Reader Bundle 采用一棵唯一的可读树，避免同时维护 `Home.md`、泛化 `indexes/` 和大量空目录：

```text
index.md                         # OKF 根目录渐进式索引
Home.md                          # 面向人的说明页，可链接到 index.md
products/
  index.md
  <product>/
    index.md                     # 产品定位、边界、模块入口
    modules/
      index.md
      <module>/
        index.md                 # 模块目的、能力、场景入口
        <concept>.md             # 可读 Concept 文件
references/                      # 只存必要来源入口，不复制全部原文
log.md                           # 可选的读者可见变更摘要
_digest/                         # Audit Package，不在阅读入口
_archive/                        # 历史快照，不在阅读入口
```

`Home.md` 和 `index.md` 的职责必须写死：不能让用户面对两套互相不一致的目录。Task2A 先确定一个 canonical reader tree；Task3 才清理旧 `indexes/` 兼容层。

### 应采纳：逐条归因和跨页图

- `sources[].id` 应该是稳定 source key。
- 正文关键结论用 Markdown footnote 或等价的 `[src-001]` 语法指向来源。
- `claim_id` 继续承担审计身份；不能只把一串 claim hash 放到 HTML 注释里。
- 只有有证据的关系才生成链接，例如“属于产品”“同模块”“前置条件”“相关排障”；不能为了填满 Related topics 伪造关系。
- `source-index` 仍可作为机器审计投影，但 Reader Bundle 内的来源链接必须能点击到 Concept 或 `references/` 入口。

### 不应直接引入

- 不引入 OKF reference agent、可视化服务、Knowledge Catalog 或数据库。
- 不把 OKF 的 `Attested Computation` 当成所有页面必需字段；只有真实存在的计算/SQL/API 规则才单独建该类型。
- 不建立中央全公司 taxonomy；保留受管 `ProductGazetteer`，概念 `type` 允许扩展，未知类型进入候选/降级。
- 不把 OKF 的兼容性当作“通过 frontmatter 就算知识质量通过”。正文可读性、CompanyBrain 对比和真实问题验收仍由本项目负责。

## 五、建议重排的后续任务

### Task 2A：Concept Contract 与 Reader Bundle 骨架

目标：先让输出文件“是什么、能不能被读取、如何导航”变得确定；不调用 LLM。

工作：

1. 冻结 `Concept Contract v1`：`type/title/description/tags/generated/verified/status/stale_after/sources` 与本项目扩展字段。
2. 冻结页面类型映射。建议最小集合：`Product Overview`、`Module Overview`、`Capability`、`Procedure`、`Rule`、`Technical Reference`、`Troubleshooting`。允许 `Reference` 作为保留原文/资料页，但不把它伪装成已编译知识。
3. 把 Task1 `TopicIndex` 映射为 Concept Plan；TopicIndex 是稳定身份，Concept `type` 是读者职责，两者分开。
4. 生成根 `index.md`、`Home.md`、产品 `index.md`、模块 `index.md`；不生成空目录或空索引。
5. 生成可点击的来源入口、旧路径 redirect/alias，并保留 `_digest`/`_archive` 隔离。
6. 定义 `generated/verified/status/stale_after` 与 `page_status/delivery_status` 的关系，禁止状态互相覆盖。

验收：

- `--no-llm + Jaccard` 零网络、零模型调用。
- 所有 Concept frontmatter 可解析；未知扩展字段可保留。
- 读者从根 `index.md` 或 `Home.md` 能逐级进入产品、模块和当前 Concept；无空入口、断链、哈希主文件名。
- `sources[].id`、`topic_key` 和 `claim_id` 可追溯且跨重跑稳定。
- 只有 Task2A 生成的 bundle skeleton，不能把未编译的 Evidence 标为 `stable`。

### Task 2B：知识对象规划与正文编译（小语料）

目标：解决“页面不是原文切片”的根因。输入必须是 Task1 的固定 TopicPlan，不允许重新按批次探索主题。

工作：

1. 为每个来源/主题识别知识对象：产品、模块、能力、流程、规则、技术参考、排障或资料归档。
2. 为每个对象选择页面类型和正文模板；正文至少回答：是什么、适用范围、入口/前置、步骤/规则、限制/异常、版本/时效、下一步和来源。
3. 先生成完整证据图和 Concept Plan，再调用模型写正文；模型不得创建新产品、模块或 topic key。
4. 正文与 Evidence 分离；Evidence/Archive 保留原文、表格、图片 URL、历史和 Claim，Reader Concept 只放解释后的结构化内容。
5. 长主题按“一个读者问题/一个业务对象/一个流程”拆页；禁止按 300 行机械切断章节。拆分页必须有主题总览、上一页/下一页和同主题关系。
6. 关键正文事实用 source id/claim id 做逐条归因；数字、标识符、版本和条件必须可回查。
7. 缺少必需证据时生成 `draft/degraded` 或 `Reference`，不得写“请阅读 Evidence”类占位并称为 `stable`。

验收：

- 小语料覆盖多来源合并、单来源手册、长表格、双语、图片、版本历史、流程/规则/技术参考和 provider 失败。
- 每个 Concept 独立阅读能回答至少一个预注册问题；不需要先打开原始 Evidence 才能理解主旨。
- 正文无通用占位、无连续原文 Evidence dump、无空 Related topics；关系链接必须有证据。
- 页面类型、标题、路径、正文和 sources 经过 deterministic schema/links/claim gates。

### Task 2C：信任信号与读者质量门（小语料）

目标：确认“写得像知识”不只是机器字段通过。

工作：

1. 运行 Task0 冻结的 17 个正向问题和 3 个负向问题的可答子集。
2. 记录人工 reviewer、日期、问题 seed、答案入口、跳转次数、答案完整性、标题可理解度、来源归因和版本/边界准确性。
3. 以 OKF `generated`/`verified`/`status`/`stale_after` 做可见信任信号；不把 provider 成功等于 verified。
4. 机器验证、Agent 辅助和人工阅读分开记录；Task2C 失败只产生 `not_released`/`degraded`，不覆盖旧 Reader Bundle。
5. 与 Task2 历史产物和 CompanyBrain 做同语料/同问题对照，报告保存完整性、正文可读性、入口、关系、失败率和成本。

验收：

- 可答正向题全部达到 Task2C 的样本阈值；负向题 0 误命中。完整 15/17 + 0/3 留给 Task3。
- 关键概念页能在页头看到生成、验证、状态和来源信号。
- 所有失败、未知、冲突和过期候选可见但不进入 `stable` Reader Package。
- 人工 reviewer 的读者评分和失败样本必须落盘，不能由静态 lint 代替。

### Task 3：89 条全量发布、对比和人工验收

Task3 保持原 PRD 的职责，但新增约束：

- 只消费 Task2A/2B 冻结的 Concept Contract、Concept Plan、词典和模板；不在全量运行中重新发明分类。
- 输出是 Concept Bundle，不是 89 个来源文件的包装。
- 全量产品/模块 `index.md` 只列真实存在的 Concept；没有证据的模块不生成空壳页。
- 生成 `generated` 和机器 `verified`；人工完成后才添加 `human:<id>`。
- `status: deprecated` 的旧概念保留历史和旧链接，但不再出现在新入口。
- 对比报告必须区分保存完整性、知识正文质量、导航/图关系、信任/新鲜度、失败和调用成本。

## 六、PRD 需要增加的硬合同

建议把以下条目写进 PRD，而不是留在实现说明里：

1. **Concept 不等于 Topic**：TopicIndex 负责稳定身份，Concept Contract 负责读者语义。
2. **OKF 兼容是子集**：采用 Markdown + frontmatter + index + sources/trust/lifecycle；不引入 OKF runtime 或中央 taxonomy。
3. **Reader/Audit 只有一套 canonical reader tree**：`index.md/Home.md → product → module → concept`；隐藏账本和归档不进入主阅读树。
4. **正文质量不是 Evidence 质量**：Evidence 可完整而正文仍 degraded；两者必须分别验收。
5. **来源缺失不写通用占位**：可选字段省略；必需字段缺失则 `draft/degraded/Reference`，不能进入 stable。
6. **信任信号必须前置**：`generated`、`verified`、`status`、`stale_after` 和 `sources` 可在不打开正文的情况下查询。
7. **逐条归因**：正文关键陈述通过稳定 source id/claim id 指向来源；不要只在文末列一串 hash。
8. **生命周期**：新生成、人工审核、过期、替代和废弃各有明确状态；`deprecated` 不等于删除。
9. **关系图有证据才生成**：不为了填 Related topics 伪造链接；所有关系链接可回查来源或 TopicIndex。
10. **先小语料再全量**：Task2A/2B/2C 任一读者质量门未通过，Task3 不得启动。

## 七、不建议的方向

- 不把“增加更多 Summary/Why 字段”当作修复。
- 不把所有来源强行归并为一个产品/模块。
- 不让 LLM 在 Task2/Task3 自由扩展 ProductGazetteer 或 topic key。
- 不用全局可信度分数替代可解释的来源、生成和验证事件。
- 不用 `_digest`、`_archive` 或大批次运行报告作为 Reader Bundle 的主目录。
- 不把 300 行限制当成正文结构规则；先按知识对象和读者问题分页，再检查硬上限。
- 不直接照搬 OKF `Attested Computation`、图数据库或 Knowledge Catalog。

## 证据索引

- 原始设计：`docs/plans/universal-knowledge-digest-design.md`
- 当前 PRD：`docs/plans/knowledge-digest-knowledge-publication-prd.md`
- Task0/Task1 代码：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/topic_axis.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/publication.py`
- Task2 输出审计：`docs/research/20260804-output-audit.md`、`20260804-output-content-quality.md`、`20260804-output-navigation.md`
- CompanyBrain 对照：`docs/research/20260804-companybrain-ia.md`、`20260804-companybrain-reader-journey.md`
- OKF：Google Cloud blog、OKF v0.2 SPEC.md 和官方 `okf/` repository（本报告“第三节”列出链接）。
