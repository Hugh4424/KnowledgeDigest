# CompanyBrain 与 Task2 阅读路径审查

日期：2026-08-04  
范围：只读比较 `/Users/Hugh/Hugh/Knowledge/CompanyBrain` 与 `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb`。本报告记录事实；修复建议是基于事实的推测。

## 结论

CompanyBrain 是“人工设计的知识产品”：先给读者说明知识库用途和查询入口，再按产品、模块、场景组织内容，正文页也告诉读者什么时候应该查它、如何排查和如何继续阅读。Task2 是“分类索引 + 原文证据页”：能从 Home 找到分类和每个页面，但页面之间没有语义连接，且大量页面的标题、摘要、Why、Version 不足以帮助读者判断内容是否值得读。

因此 Task2 机器上的“页面全部有索引、来源可追溯、行数不超过 300”不等于读者可用。

## Task2 的实际阅读路径

事实：Task2 有 `Home.md`、27 个 `indexes/*.md`、120 个 `pages/**/*.md`。Home 只链接 6 个一级入口：客户、研发、运营、其他、原则、产品（证据：`company-kb/Home.md`）。

典型路径：

```text
Home.md
  -> indexes/products.md
  -> indexes/product-capability.md
  -> pages/products/product-capability/ae-emm.md
```

也就是至少 3 次点击才到正文。一级分类下再进入空分类时会遇到死路，例如 `indexes/principles.md -> indexes/business-principle.md`，该页只有“主题”标题、没有主题链接；`indexes/products/product-overview.md` 和 `indexes/product-boundary.md` 也为空。

统计事实：

- 120 个正文文件均被分类索引链接一次（索引链接行 120、唯一目标 120）。这证明“有入口”，不证明“入口有意义”。
- 27 个索引中，只有 8 个分类索引有正文链接，13 个分类索引为空；其余是一级/父级索引。
- 120 个正文页都写 `暂无已验证的相关主题`，正文页没有指向其他知识页的内部链接。
- `_digest/source-index.md` 只提供来源 URI、指纹、状态和目标路径，是审计回查入口，不是语义阅读入口。
- 120 页中 34 个是 `.part-002` 等分页文件；分页可以防止超长，但读者没有“上一页/下一页/同一主题总览”的正文导航。

读者落到页面后，常见模板为：`Summary -> Why -> Version -> Related topics -> Evidence -> Provenance`。其中 60/120 页的 Summary 是“来源未提供摘要；请阅读 Evidence”，58/120 页的 Why 是“来源未说明”，19/120 页 Version 是 `missing`。证据正文通常仍是 Confluence 原始层级和图片/外部链接，读者需要自己从长证据中重建主题。

文件名也暴露实现细节而不是知识语义：至少 27 个正文文件使用 `topic-<hash>.md`（如 `topic-d6d55101.md`），还有 `ae.md`、`ios.md`、`global.md` 等高度重复的短名。部分 H1 虽有中文标题，路径和索引仍使主题身份难以判断。

## CompanyBrain 的实际阅读路径

事实：CompanyBrain 根目录有 `Home.md`、Products、Engineering、Customers、Operations、Principles 等长期入口；Home 明确写出“企业正式知识库”、查询建议和使用边界（证据：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Home.md`）。

典型产品路径：

```text
Home.md
  -> Products/产品索引.md
  -> Products/MAXSTORE/文档总览.md
  -> Products/MAXSTORE/模块手册/模块总览.md
  -> Products/MAXSTORE/模块手册/终端与设备/终端与设备总览.md
  -> Products/MAXSTORE/模块手册/终端与设备/终端监控与详情页.md
```

典型场景路径：

```text
Home.md
  -> Products/产品索引.md
  -> Products/GoInsight/文档总览.md
  -> Products/GoInsight/使用场景索引.md
  -> 按“新员工答疑 / 新功能调研 / 研发实现 / AI 自动答疑”选择模块入口
```

CompanyBrain 的路径比 Task2 深，但每一级都有用途说明和下一步选择，深度换来了导航确定性。产品总览页区分“产品定位、模块手册、技术实现、经验与坑、规范与资产”；模块总览按真实模块列出页数；场景索引把同一知识映射到不同工作任务，不复制正文。

正文页也有读者语义。例如 `Products/MAXSTORE/模块手册/终端与设备/终端监控与详情页.md` 开头直接说明“终端监控用于查看什么”，随后给出监控入口、监控内容和排查路径，并保留来源说明。它不是把原文包在 `Evidence` 下，而是先编译成可执行的知识，再给出处。

CompanyBrain 还保留治理反馈：`Products/MAXSTORE/_config/structure_review.md` 记录模块规则、低置信度先进入“资料汇总”；`quality_report.md` 记录自动审计结果。GoInsight 的质量报告明确列出 60 个 uncertain_module，而不是把不确定分类伪装成完成。

## 差异与修复启示

### 1. 入口设计

Task2 解决“页面能被索引”，没有解决“读者该从哪个问题开始”。需要增加产品/领域总览和场景入口；分类页应解释适用问题、边界、推荐下一跳，而不是只有主题清单。

### 2. 分类粒度

Task2 的 `product-capability / product-operations / customer-overview` 是通用标签，无法表达产品、模块、知识类型的组合关系；因此很多内容进入正确的大类，却仍然不知属于哪个产品、哪个模块、哪个任务。CompanyBrain 以“产品 -> 知识本体 -> 模块 -> 单页”为主轴，以场景索引做第二条入口。

### 3. 正文编译

Task2 的 `Summary/Why/Version` 对缺失字段采用模板占位，导致形式上完整、语义上空洞。应区分“原文没有该事实”和“模型没有生成”：缺失时进入待处理/原文模式，不能把占位文本当作知识摘要；正文需要按问题、适用范围、步骤/规则、限制、排查、版本和来源编译。

### 4. 页面命名和分页

Task2 的 hash 文件名和 `part-002` 能稳定写入，但对人不可读。稳定 ID 应隐藏在 frontmatter；路径/H1 应使用经过校验的语义标题，并保存旧路径映射。分页页应显示主题总览、当前部分、上一页/下一页及回到主题入口，避免读者在分页中迷路。

### 5. 质量门禁

Task2 当前强门禁是无损、溯源、路径和行数；这些是必要底线，不是知识质量。应新增 reader-facing 验收：入口可达、分类非空且有解释、标题可理解、摘要非占位、正文能回答明确问题、相关主题有依据、分页可连续阅读、低置信度可见且不伪装完成。CompanyBrain 的质量报告和低置信度隔离可作为治理模式参考。

## 证据路径索引

- Task2 入口：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/Home.md`
- Task2 目录说明：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/README.md`
- Task2 分类页示例：`.../company-kb/indexes/products.md`、`.../indexes/product-capability.md`、`.../indexes/pending.md`
- Task2 正文示例：`.../company-kb/pages/products/product-capability/ae-emm.md`、`.../pages/engineering/implementation/uptrillion.md`
- Task2 来源索引：`.../company-kb/_digest/source-index.md`
- CompanyBrain 根入口：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Home.md`
- CompanyBrain 产品入口：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/产品索引.md`
- CompanyBrain 产品总览：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/MAXSTORE/文档总览.md`
- CompanyBrain 模块总览：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/MAXSTORE/模块手册/模块总览.md`
- CompanyBrain 场景索引：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/MAXSTORE/使用场景索引.md`
- CompanyBrain 编译页：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/MAXSTORE/模块手册/终端与设备/终端监控与详情页.md`
- CompanyBrain 结构/质量治理：`/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/MAXSTORE/_config/structure_review.md`、`quality_report.md`

