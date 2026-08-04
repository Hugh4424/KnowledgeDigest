# Task2 最终产物内容质量审计（2026-08-04）

## 范围与结论

只读抽查 `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/pages`，并对照同机的 `/Users/Hugh/Hugh/Knowledge/CompanyBrain` 入口页。未调用外部模型，也没有修改产物。

结论：Task2 已有可用的 Home → 分类索引 → 主题页路径，Evidence/Provenance 保留得较完整；但内容字段仍明显是“机器发布结果”，不是可直接交付给读者的知识库。主要阻塞项是摘要和 Why 的失败占位、Related topics 全部为空、Version 大量缺失，以及 34 个分片页重复展示同一套元字段。

## 机器统计

- `pages/` 共 120 个 Markdown 页，`_digest/topic-index.json` 记录 86 个稳定主题；其中 34 个为 `.part-002/003/...` 分片。
- 页行数 33–300，平均约 189 行；120/120 页均不超过 300 行。33 页达到 298–300 行，末尾仍是完整 Provenance 条目，没有发现 `...[truncated]`、`内容截断` 等字面截断标记。硬上限会把长来源切成多个 part，读者需要连续打开多个文件。
- 顶层页目录：`products` 54、`customers` 26、`engineering` 20、`operations` 19、`principles` 1。实际二级分类主要集中在 `products/product-capability`（51）和 `customers/customer-overview`（26），分类存在但仍是来源主题平铺，不是 CompanyBrain 式产品/模块知识本体。
- 119/120 页有非空 Provenance；唯一空 Provenance 页为 `pages/engineering/implementation/ae.md`，文件末尾只有 `## Provenance`，没有条目。

## 标题与路径

标题层面有改善：120 页 H1 均非空，去掉 Markdown 加粗后共有 86 个唯一标题，分片页重复同一来源标题。例如：

- `pages/customers/customer-overview/1.md`：`1.背景介绍`（过于泛化，无法单独定位 Dashboard 主题）。
- `pages/customers/customer-overview/ae-73c408bf.md`：`AE - 应用详情`。
- `pages/customers/customer-overview/ae.md`：`[AE] 弹窗输入标识符注册设备`。
- `pages/products/product-capability/topic-20d64964.md`：`累计计算`。
- `pages/products/product-capability/q-a.md`：`・Q&A`（符号噪声）。
- `pages/customers/customer-overview/email-activity-audit-log-global-system.md`：`Email ActivityAudit Log日志管理Global System`（中英文粘连，读起来不自然）。

索引显示的是这些语义标题，因此从索引进入时比旧的 `topic-<hash>` 有改善；但 63/120 个文件名仍含 8 位 hash 后缀（如 `ae-73c408bf.md`、`topic-20d64964.md`），直接在文件夹中浏览仍不易理解。CompanyBrain 则用 `Products/<产品>/文档总览.md`、`模块手册`、`技术实现` 等稳定本体入口，读者先按产品/模块定位，再读主题，层级更清楚。

## Summary / Why / Version / Related topics

| 字段 | 统计 | 读者影响 | 样本 |
| --- | ---: | --- | --- |
| Summary | 58/120 是明确 fallback 占位（约一半） | 只能被迫打开 Evidence | `customers/customer-overview/ae.md` |
| Why | 58/120 为 `- 来源未说明` | 没有说明用途/决策价值 | `operations/management/topic-419044ac.md` |
| Version | 54/120 是缺失类值 | 无法判断时效 | `products/product-capability/ios.md` |
| Related topics | 120/120 为 `- 暂无已验证的相关主题。` | 没有主题间导航 | 任意主题页 |

### Summary

明确 fallback 的分片分布为：第 1 部分 37 页、第 2 部分 16 页、第 3 部分 5 页（合计 58 页）。典型页面 `pages/customers/customer-overview/ae.md` 的 Summary 只有：

```text
- 来源未提供摘要；请阅读 Evidence。
- 已验证来源证据；第 1 部分。
```

这不是摘要，只是失败说明和分片说明。成功生成的页（例如 `pages/customers/customer-overview/1.md`）能给出 Merchant Portal Dashboard 的用途和核心指标，说明成功路径有效，但失败回退的读者价值明显不足。

### Why

58 页完全是 `- 来源未说明`。有内容的 Why 通常是有用的一句用途说明，例如 `pages/engineering/implementation/ae.md` 的“Provides administrators and resellers with the correct workflow and UI navigation...”，但这类成功值没有覆盖失败来源。

### Version

缺失类值合计 54 页，包含 `missing` 19、`未提供版本信息` 15、`Missing` 14、`未提供` 4、`missing marker` 1、`N/A` 1。其余版本值也混合 `v1/v2`、日期、产品名和自然语言（如 `待补充`、`No version history provided`），缺少统一可读格式。

### Related topics

120 页全部写入同一占位：`- 暂无已验证的相关主题。`。这不是“关系很少”的证据，而是当前发布结果没有提供任何主题间关系；读者无法从 `EMM设备数据收集范围` 跳到 `EMM设备数据收集`、从 `创建设备报告` 跳到 `指标详情页` 等明显相关主题。

## LLM 失败与 fallback

- 结果 README 声明 30 次 provider 调用失败；`_queues/needs_review.md` 实际有 31 条 `provider-source-*` 记录，其中 9 条为 deadline exceeded、22 条为 provider 输出不是 JSON。README 与队列条数存在 30/31 不一致，应在后续审计中解释。
- 失败来源仍保留原始 Evidence，且多数页面保留 Provenance，说明 fallback 没有丢证据；但字段层 fallback 直接暴露为 Summary/Why 占位，导致知识页不可读。
- 失败样本路径包括：
  - `pages/customers/customer-overview/emm.md`（EMM 客户端页面，deadline exceeded）。
  - `pages/products/product-capability/ios.md`（iOS 资产列表，deadline exceeded）。
  - `pages/operations/management/topic-419044ac.md`（日志管理，invalid JSON）。
  - `pages/products/product-capability/ae-goinsight.md`（AE-GoInsight 数据收集，invalid JSON）。

## Evidence 可读性与重复

Evidence 仍然是最有价值的部分：保留中英文原文、表格、图片链接、Confluence 行定位，样本 `pages/customers/customer-overview/1.md` 的 Dashboard 需求和 `pages/products/product-capability/topic-20d64964.md` 的累计计算说明均可追溯。问题在于每个 part 都重复完整的 Summary/Why/Version/Related topics/Provenance 元字段，长页接近 300 行时读者需要跳过大量 hash 引用；而分片页自身没有“上一页/下一页”导航。

## 与 CompanyBrain 的结构差距

CompanyBrain 的产品入口（如 `Products/EMM/文档总览.md`）先给出“产品定位 → 模块手册 → 技术实现 → 经验与坑 → 规范与资产”的知识本体和调用建议；`gbrain-product-index.md` 通过产品 slug 连接到产品总览、定位、FAQ、边界和模块指南。Task2 当前只有“领域 → 子分类 → 来源主题列表”，没有产品级总览、模块级聚合页、FAQ/边界入口，也没有 Related topics 反向链接。因此“有分类”成立，但“语义化、结构化、可按问题阅读”仍未达到 CompanyBrain 水平。

## 最小修复方向

1. 失败 fallback 至少从来源 H1/metadata 生成一句中文或英文摘要；不要把“请阅读 Evidence”当 Summary。
2. Why 缺失时从来源背景/目的段落抽取一句用途说明，并显式标注“来源未说明”仅作为证据状态。
3. Related topics 不能全部写同一占位；先按同产品/同模块/来源主题共现建立可审计的双向链接。
4. 为每个产品或主模块增加总览页，索引只列语义主题和 part 导航；文件路径的 hash 仅保留在稳定 ID，不要成为主要阅读路径。
5. 清理分片元字段重复和空 Provenance（至少修复 `engineering/implementation/ae.md`）。

