# Task2 final9 最终产物审计

日期：2026-08-04  
对象：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804`  
范围：只读检查输出目录、页面正文、导航、Task2 实现与对比报告；没有调用外部模型，没有修改代码或原始材料。

## 先给结论

Task2 没有“消化失败”，而是把“保留原文、生成可追溯字段、组织成 Markdown”误当成了“形成可读知识”。

当前结果的机器质量门大多通过：来源、Claim、Evidence、Provenance、页面上限和本地链接都存在；但读者质量没有通过：主题没有真正合并，标题仍大量沿用文件名，Summary/Why/Version 大量是占位语，页面正文基本是原文 Evidence，分类只是粗粒度目录，不是知识结构。

换句话说，当前产物是一个“带索引和审计账本的原文切片器”，不是 CompanyBrain 式的知识发布系统。

## 产物规模与阅读噪声

当前 `company-kb` 共有约 4,973 个文件、1,179 个目录、约 279 MB：

| 区域 | 规模 | 阅读意义 |
| --- | ---: | --- |
| `pages/` | 120 页，约 4.9 MB | 当前正文 |
| `indexes/` | 27 页 | 导航骨架 |
| `_digest/` | 92 个 run，约 237 MB | 运行账本，不应成为阅读入口 |
| `_archive/` | 88 个 run，约 36 MB | 历史快照，不应成为阅读入口 |

根目录还有 `README.md`、`company-kb/` 和 `comparison/` 三套入口。README 指向 `company-kb/Home.md`，但没有把 `comparison/COMPARISON.md` 做成可点击入口。把 92 次运行和 88 次归档都放在最终交付目录，导致用户看到的文件量远大于真正的知识内容。

## 读者路径：结构存在，但信息架构不完整

当前路径是：

```text
README.md → company-kb/Home.md → 6 个父分类 → 21 个叶分类 → 120 个主题分页
```

本地检查结果：120 页都能从 Home 三跳到达，149 个本地相对链接无断链；这是结构性优点。但仍有三个读者问题：

1. 21 个叶分类中只有 8 个有主题，13 个空页仍被生成，像未完成的产品菜单。
2. Home 的“待复核”链接到空的 `indexes/pending.md`；实际 31 条 provider 失败记录在 `_queues/needs_review.md`，读者无法从 Home 看到。
3. `_digest/source-index.md` 的 `target_paths` 是纯文本，不是 Markdown 链接；读者需要手工复制路径才能回到主题页。

导航报告：`docs/research/20260804-output-navigation.md`。

## 页面质量：问题集中且可复现

当前有 86 个稳定主题、120 个主题页，其中 34 个分页页；85/86 个主题实际上是单来源主题。`_digest/batch-state.json` 还明确记录 `batch_size: 1`、89 个批次。结果不是把相近来源合并成知识主题，而是把每个来源单独包装。

### 1. 标题仍接近原文件名或编号

代表样本：

- `pages/engineering/implementation/16.md` → `# 16 问数自动识别数据集`
- `pages/engineering/implementation/17.md` → `# 17  智能搭建`
- `pages/customers/customer-overview/1.md` → `# **1.背景介绍**`
- `pages/products/product-capability/12-goinsight-dc.md` → `# 12. GoInsight DC部署方案`

120 个页面中有 27 个 `topic-<hex>` 文件名，另有 24 个带 8 位 hash 后缀；即使 H1 可读，脱离索引打开文件时路径仍不可理解。

### 2. Summary/Why/Version 不是可靠的知识摘要

统计：

- 58 页的 Summary 是明确 fallback 占位；
- 58 页出现“来源未说明”；
- 54 页出现缺失类 Version 值（含 `missing`、`未提供版本信息`、`Missing`、`未提供` 等）；
- 120 页的 Related topics 都是“暂无已验证的相关主题”。

失败来源页的典型内容是：

```text
## Summary
- 来源未提供摘要；请阅读 Evidence。
## Why
- 来源未说明
## Version
- v2
```

成功模型页也常只是“这篇文档讲了什么”的一段英文摘要，随后把几百行原文完整放入 Evidence。例如 `pages/products/product-capability/12-goinsight-dc.md` 的 Summary 是英文，Evidence 仍是原始部署文档；`pages/products/product-capability/ae-c69e5c54.md` 的 Summary/Why 尚未形成面向读者的操作结构。

### 3. 页面不是“知识页”，而是“元数据壳 + 原文切片”

页面外壳都有 `Summary`、`Evidence`、`Provenance` 标题，但 `pages/engineering/implementation/ae.md` 的 Provenance 为空；其余页面才有来源条目。Evidence 基本保留输入正文。`llm.py` 的 `publication_only` 提示明确禁止模型返回 `final_body`（`src/knowledge_digest/llm.py:435-452`），而 Task2 运行报告显示 `llm_summary_enabled: false`。因此模型主要只负责 title/category/summary/why/version 元数据，正文没有经过知识重组。

`page_layout.py` 的 `_render_page` 固定生成元数据壳（`src/knowledge_digest/page_layout.py:295-368`），`_partition` 只按 300 行硬上限拆分（`src/knowledge_digest/page_layout.py:397-454`）。这保证了不丢行，却不能保证章节完整、主题边界清楚或阅读顺序自然。

### 4. 失败回退是正确性保护，不是质量结果

`publication.py` 的字段回退是明确的占位语：

- `summary = "来源未提供摘要；请阅读 Evidence。"`（`publication.py:166`）
- `why = "来源未说明"`（`publication.py:181`）
- `version = "未提供版本信息"`（`publication.py:168`）

这符合“不能臆造事实”的安全原则，但当前产品把这些回退页也作为正式知识页发布，读者得到的是“请自己读原文”，不是可参考的知识。失败来源应该进入清晰的待复核入口，或生成明确的原文档案页，而不应伪装成完成的语义页。

## Provenance 与质量门的真实边界

`source-index.md` 有 88 个来源行：56 `published`、31 `needs-review`、1 `duplicate`；123 个 target path 均存在。`claim-history.jsonl`、`pending-review.jsonl` 和 89 个批次状态都保留了审计信息，说明内容丢失防护基本有效。

但“可追溯”不等于“可读”：

- 31 个 provider 失败来源仍然有正文页，状态只在 source-index/queue 中体现；
- `_queues/needs_review.md` 与 Home 的 pending 页面脱节；
- source-index 的目标路径不是可点击链接；
- 279 MB 的审计/归档文件混在最终结果包内，用户很难区分当前知识和历史现场。

Task2 对比报告还暴露了验收边界问题：`comparison/COMPARISON.md` 明确说人工字段必须由固定样本人工填写，`COMPARISON.json` 却记录 17/17 `title_understood` 的 `agent_assisted_pass`。Task2 `tasks.md` T038 又明确写着 CompanyBrain 人工确认仍开放，不能把这个结果当作独立读者质量通过。

## 对照原始方案/Task2 规格的判断

已经实现或基本实现：

- S1–S6 的文件读取、Claim、Evidence、Provenance、归档和原子写；
- 稳定 topic ID、受控 taxonomy、Home/indexes/pages 导航；
- 300 行硬上限和分页；
- provider 失败、fallback、批次恢复和运行账本。

没有实现“原始需求意义上的知识消化”：

- S2 仍以逐来源批次和单一相似度为主，没有形成真正的跨文档语义主题；
- S4 没有把完整主题重写成可读知识，只生成了元数据建议并保留原文 Evidence；
- `Why` 没有映射到用户的使用场景/调用建议；
- `Related topics` 全部为空，主题之间没有知识网络；
- 版本、适用边界、对象模型、流程、决策、FAQ 等 CompanyBrain 式结构没有成为发布合同；
- AC-002/AC-007/AC-008 的人工阅读质量和真实语义质量并未形成独立通过证据。

因此，Task2 的“316 tests passed / 89 批成功 / Claim 数和页数”只能证明系统安全地写出了结果，不能证明结果质量合格。

## 根因排序

1. **产品目标错位**：把“无损和可审计”当成“知识可读”；读者质量没有硬门禁。
2. **主题模型过弱**：一来源一主题，分类是目录标签，不是跨文档知识主题。
3. **生成职责过窄**：publication-only 禁止 `final_body`，且关闭 `llm_summary`，模型不负责知识重组。
4. **分页时机错误**：对原文 Evidence 做 300 行切片，而不是对完成的知识结构分页。
5. **失败语义错误**：fallback 占位页仍进入主导航，待复核队列却不在 Home 可见。
6. **交付包设计错误**：审计、归档、运行现场与读者知识混为一个文件夹。
7. **验收被代理指标替代**：用 Claim/page/link 统计和 agent-assisted review 代替真实人工阅读。

## 修复方向（只给调查结论，不改代码）

修复不应继续堆导航和字段。下一任务应先重做“知识发布合同”：

1. 把每个主题定义成可回答的知识单元：对象/用途、概念、流程、配置、边界、版本、FAQ、来源；
2. 先做跨来源主题规划，再生成主题正文；单来源只是来源，不应自动成为主题；
3. 模型输出允许生成结构化 `KnowledgeDraft`，但每个段落必须有 Claim/Evidence 回指；失败时发布原文档案，不发布假摘要；
4. 主题页正文和来源证据分离：正文可读、来源索引可回溯，必要时另放 `sources/` 或 `_digest`；
5. 主题标题、产品、领域、用途和关系必须在发布前通过抽样人工验收；低于阈值直接失败；
6. 最终交付包只保留 `README/Home/indexes/pages/_digest/source-index`，历史 run/archive 另存审计包；
7. 质量报告必须明确区分 machine-pass、agent-assisted、human-reviewed，不能把前两者写成读者质量通过。

## 关联调查

- `docs/research/20260804-output-navigation.md`
- `docs/research/20260804-output-content-quality.md`（并行调查）
- `docs/research/20260804-output-provenance-integrity.md`（并行调查）
