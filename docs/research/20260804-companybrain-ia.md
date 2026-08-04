# CompanyBrain 与 Task2 信息架构对照

> 调查日期：2026-08-04。只读检查本机文件；没有调用外部模型。本文区分“事实”和“判断”。

## 1. 事实统计

### CompanyBrain

- 根入口是 [`Home.md`](/Users/Hugh/Hugh/Knowledge/CompanyBrain/Home.md)。它把知识分成 Products、Engineering、Customers、Operations、Principles 五个业务入口，并写明不同问题应该从哪个入口开始（Home.md:22-44）。
- 可见知识（排除 `_gbrain/` 生成镜像和隐藏目录）共 838 个 Markdown：Products 750、Operations 67、Principles 8、Customers 4、ProductBoundaries 4、Engineering 2。
- Products 下有 24 个产品目录；产品总入口 [`Products/产品索引.md`](/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/产品索引.md) 同时提供“优先入口、按能力查、产品清单、使用边界”（Products/产品索引.md:24-98），不是只列文件名。
- 大产品有自己的知识本体。以 MAXSTORE 为例，共 169 个 Markdown；目录按 `产品定位`、`模块手册`、`技术实现`、`经验与坑`、`规范与资产` 等语义层组织。入口 [`Products/MAXSTORE/文档总览.md`](/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/MAXSTORE/文档总览.md:4-25) 明确每类内容适合回答什么问题。
- MAXSTORE 还有 [`使用场景索引.md`](/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/MAXSTORE/使用场景索引.md:4-16)，按新员工答疑、新功能调研、写 spec、研发测试、销售答疑、AI 答疑等真实任务指向入口，而不是按来源文件顺序排列。
- MAXSTORE 的 `模块手册`继续按业务模块拆分（例如“终端与设备”“应用与市场”“账号组织与权限”等），每个模块有“总览”和具体规则/流程页；`产品定位/产品定位与价值.md`还明确产品边界、核心对象、组合产品关系和高频问法。

### Task2 输出

- 当前 KB 根目录为 [`company-kb`](/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb)，根 [`Home.md`](/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/Home.md) 只有六个粗粒度入口（客户、研发、运营、其他、原则、产品）和待归类。
- `pages/` 有 120 个 Markdown：86 个主题页 + 34 个分页 part。主题分布为：产品能力 51、客户概览 26、运营管理 19、研发实现 18、产品运营 3、研发实践 1、研发架构 1、内容规范 1。
- `indexes/` 有 27 个 Markdown，但父索引只链接叶分类，叶分类再把每个主题（以及每一个 part）按标题平铺。例如 [`indexes/product-capability.md`](/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/indexes/product-capability.md) 有大量“标题 + 第 2/3 部分”条目，没有产品级入口、模块总览或使用场景入口。
- `topic-index.json` 有 86 个主题，`product_slug` 非空数量为 0。也就是说，虽然 taxonomy 声明了产品相关分类，实际产物没有建立产品实体层。
- 120 个主题页均包含 `Summary`、`Why`、`Version`、`Related topics`、`Evidence`、`Provenance`，但这是统一发布壳，不等于完成知识重组。典型页 [`ae-f8a2c6d4.md`](/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/pages/products/product-capability/ae-f8a2c6d4.md) 的 `Evidence` 仍是原始 Confluence 的图片链接、双语表格和操作碎片；`Summary` 是一段英文概括，`Why` 仅为“来源未说明”，`Related topics` 为“暂无已验证的相关主题”。
- 页面文件名中仍有 `topic-xxxxxxxx`、`ae.md`、`ios.md`、`1.md` 等不可读或容易冲突的命名；同一主题分页在索引中变成多个独立条目（如“AE-通信和网络配置（第 2 部分）”）。
- 结果目录约 279 MB、Markdown 2978 个；其中绝大多数是 `_archive/` 的运行快照。当前读者若直接浏览文件夹，会把审计历史、运行锁、队列和正文混在一起。

## 2. 差异与根因判断

### 事实差异

1. CompanyBrain 的最小发布单元是“可回答一个问题的语义页面”，Task2 的最小发布单元仍基本是“一个来源文件的原文 + 元数据壳”。
2. CompanyBrain 先建立产品/模块/内容类型的知识本体，再把来源资料归档；Task2 先把来源放进固定叶分类，再用 LLM 生成标题、摘要和分类字段，未产生产品、模块、流程、版本等实体关系。
3. CompanyBrain 的索引写“如何查、何时查、边界是什么”；Task2 的叶索引只写文件链接。Task2 的 `Home → parent → leaf → page` 形式存在，但缺少读者决策信息，因此形式上可导航，实际上难检索。
4. Task2 的分类是来源级粗分类，不是语义结构化。`product_slug=0` 是直接证据；产品能力页把 EMM、AE、iOS、GoInsight 等不同产品/子系统混在一个 51 页叶目录中。

### 判断（需后续主审计验证的技术根因）

- Task2 规格的“知识发布架构”主要完成了路径、分类合法性、分页、来源索引和 fail-closed；它没有把“把原文变成可复用知识”定义成独立生成阶段，也没有要求输出产品总览、模块总览、场景入口、边界页或跨来源整合页。因此质量门通过时，仍可能得到一套难读的原文重排。
- `Summary/Why/Version` 是字段级补充，不会自动重写 `Evidence`。当 `Evidence` 仍保留 Confluence 导出碎片、图片 URL、重复中英文和 UI 操作表格时，页面整体阅读质量不会因摘要存在而提高。
- 300 行上限解决了超长文件，却不能解决“页面主题错误、页面类型错误、缺少层级”的问题；把同一来源拆成多个 part 还会增加索引噪声。
- 文件名可读性只改善了部分路径；当源标题本身是 `AE`、`iOS`、`1.背景介绍` 或产品内部页面标题时，直接 slug 化必然产生重复和歧义。需要产品/模块上下文和内容类型共同构造标题，而不是只依赖单页 H1。

## 3. 对后续修复的直接要求

1. 发布流水线要分成“来源保真层”和“读者知识层”：原文证据独立保存；正文必须经过结构化重写，不能把 Evidence 当成最终正文。
2. 先识别知识实体：产品、模块、功能、流程、角色、问题、版本、客户、规则、规范、经验；再做页面聚合。产品页面至少应有“定位/边界/核心能力/模块入口/场景/来源”。
3. 输出必须有实体级入口：顶层 Home、产品索引、每产品文档总览、模块总览、场景索引、内容类型索引；叶页只承载一个清晰问题或一个可复用知识单元。
4. 设计“页面类型”合同（产品总览、模块总览、流程/操作、技术实现、经验与坑、规范/资产、客户案例等），每种类型定义必需字段和写作模板；不能用一个统一 `Summary/Evidence/Provenance` 模板覆盖所有知识。
5. 质量验收必须加入读者指标：从 Home 到答案入口的跳转、标题理解度、页面是否能回答真实问题、跨页重复率、无上下文可读性、产品/模块归属准确率。Claim 保留和链接完整只能作为底线，不能作为“知识质量通过”。

## 4. 结论

CompanyBrain “好用”的核心不是 Markdown 文件多，而是它有稳定的业务本体、面向任务的入口、产品级总览、模块级目录和边界说明。Task2 产物目前实现的是“受控分类 + 语义标题/摘要 + 可追溯原文发布”，不是完整的知识发布/知识重构系统；因此用户看到“有分类、能点开、字段齐全”，但读起来仍像按分类重新包装的 Confluence 导出。这是架构目标缺失导致的系统性问题，不是简单改几个文件名能解决的。
