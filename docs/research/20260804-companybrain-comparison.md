# CompanyBrain 与 KnowledgeDigest Task2 对照汇总

调查日期：2026-08-04。范围是只读对照：

- Task2 规格：`/Users/Hugh/Hugh/Project/KnowledgeDigest/specs/archive/knowledge-digest-llm-naming-classification`
- Task2 产物：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804`
- 参考知识库：`/Users/Hugh/Hugh/Knowledge/CompanyBrain`
- 原始方案：`/Users/Hugh/Hugh/Project/KnowledgeDigest/docs/plans/universal-knowledge-digest-design.md`

没有调用外部模型，没有修改代码。数字是本机文件统计；“判断”单独标出。

## 一句话结论

Task2 做成的是“有分类、有溯源、有写入保护的来源发布器”，不是 CompanyBrain 那种“先建立知识本体，再编译成可阅读知识页”的知识系统。它把原始 Confluence 内容换了目录、标题和固定字段，但没有完成产品/模块/场景/页面类型级的知识重组，所以机器检查通过，读者仍然要自己从 Evidence 里重新整理答案。

## 硬事实对照

| 维度 | Task2 | CompanyBrain |
| --- | --- | --- |
| 正式正文 | 120 页，约 86 主题 | 838 个正式 Markdown |
| 入口 | Home → 领域 → 叶分类 → 页 | Home → 产品 → 模块/场景 → 页 |
| 产品实体 | `product_slug` 非空为 0 | 产品目录、产品总览、产品边界 |
| 页面类型 | 统一六段模板 | 定位、操作、规则、技术、经验、规范等 |
| 质量方法 | 无损/溯源/路径/行数 | 本体、边界、场景、来源、质量审计 |

Task2 还有 34 个 `.part-*` 文件、27 个 `topic-<hash>` 文件名、29 个高度重复短文件名（如 `ae.md`、`ios.md`、`global.md`）。120/120 页的 `Related topics` 都是“暂无已验证的相关主题”；60 页 Summary 是“来源未提供摘要；请阅读 Evidence”，58 页 Why 是“来源未说明”。

Task2 的 `_queues/needs_review.md` 记录了 30 个 provider 失败（超时或 JSON 损坏）。失败页仍可被发布，但多数只剩原文 Evidence 和占位字段。`comparison/COMPARISON.md` 明确写着“人工标题理解度：未审查”，固定样本只有 17 条，且状态是 `agent_assisted_review`，不能证明读者质量。

CompanyBrain 的 Home 写明“企业正式知识库”、查询建议和使用边界；`Products/产品索引.md` 提供优先入口、能力分组和产品边界；产品内再有 `文档总览.md`、`模块总览.md`、`使用场景索引.md`。以 GoInsight 为例，资料按产品定位、模块手册、技术实现、经验与坑、规范与资产分层，模块手册再按真实业务对象组织。

## 为什么 CompanyBrain 更好

### 1. 先建本体，再放来源

CompanyBrain 先定义产品、模块、知识类型和任务入口，再决定每份资料进入哪里。MAXSTORE 有受控的 `module_rules.json`；结构优化脚本会按产品和真实业务词生成模块。Task2 的 `topic-index.json` 中 `product_slug` 全为空，产品能力目录把 EMM、AE、iOS、GoInsight 等不同产品和子系统混在同一个叶目录。

### 2. 页面回答问题，不只是承载原文

CompanyBrain 的页面通常有“当前结论、适用场景/使用方式、使用边界、排查路径、来源”等面向读者的结构。产品定位页回答“是什么、解决什么问题、和什么有边界”；操作页回答“入口、前置条件、步骤、异常”。

Task2 的 `Summary/Why/Version/Related topics/Evidence/Provenance` 是所有主题共用的外壳。它不能把原始 Evidence 中的截图、双语表格、权限条件和 UI 碎片自动重组为产品知识。300 行上限只能防止巨页，不能决定页面主题、页面类型或阅读顺序。

### 3. 导航本身就是功能

CompanyBrain 的索引页写“什么时候查这页、下一步查什么、哪些内容不能混用”。Task2 的叶索引基本只有标题列表；27 个索引中仅 8 个有正文链接，13 个为空；正文之间没有语义内链，分页页也没有明确的主题总览、上一页/下一页或回到主题入口。

### 4. 有持续治理，而不是一次性绿灯

CompanyBrain 有 `structure_review.md`、`quality_report.md` 和低置信度“资料汇总”路径；不确定内容会被记录或待审，不会伪装成正式知识。Task2 的失败/低置信度页仍进入正式目录，机器门禁只证明“没有丢写入数据”，没有证明“内容值得读”。

### 5. 生成内容有领域模板和人工校准

CompanyBrain 的 `synthesize_remaining_product_guides.py` 直接定义了产品定位、操作规则、生命周期、边界、排查和高频问法等页面正文模板，并把来源线索放在末尾。它不是把一套通用提示词套到所有文件上。

## 根因判断

以下是基于硬事实的技术判断：

1. 原始方案的总纲把场景收窄为简单 `digest(new_dir, kb_dir)`，重点是聚类、提炼合并、增量写回和防丢失；没有把“知识本体建模”和“读者发布质量”设成独立阶段。
2. S4 关注 claim-level verify、faithfulness 和 Evidence 保留，但没有规定产品总览、模块总览、场景索引、边界页、页面类型或可读正文的验收合同。因此 `Evidence` 仍是原文，机器仍可判定通过。
3. Task2 的 LLM 主要承担标题、摘要、Why、Version 和分类字段；失败时可回退到模板。它没有先识别产品、模块、业务对象、角色、流程、版本和跨页关系，再按实体聚合。
4. 分类在来源级完成，而不是在知识实体级完成。批次写入和稳定 ID 解决了可恢复性，却没有形成跨来源的产品/模块总览；这也是“页数增加但读起来更乱”的直接原因。
5. 对比验收把 Claim 数、指纹数、页面数、行数和链接作为主要证据，人工读者字段没有真正审查。于是“机器质量通过”被误当成“知识质量通过”。

## 不能只做的修补

- 只把 `topic-<hash>` 改成 LLM 标题：没有产品/模块上下文，标题仍会冲突。
- 只提高 Summary 提示词：Evidence 仍是原文，页面职责仍不清楚。
- 只把 300 行改成 500 行：只能改变分页，不会增加结构。
- 只增加索引链接：没有场景、边界和下一步说明，仍然是标题清单。
- 只降低 provider 失败率：失败率下降不等于生成了可复用知识。

## 后续修复必须达到的结果

1. 保留现有来源保真层、Claim、Provenance、归档和 fail-closed；但把它们与读者知识层分开。
2. 增加一个知识编译阶段：来源清洗 → 产品/业务对象/模块识别 → 页面类型选择 → 页面规划 → 正文编译 → 来源映射 → 读者验收。
3. 支持最小可配置知识本体：领域、产品、模块、知识类型、场景、角色、版本和边界；产品/模块字典应能像 CompanyBrain `module_rules.json` 一样锁定、审计和逐步扩展。
4. 为页面类型定义必需字段：产品总览、模块总览、操作流程、规则/配置、技术实现、故障经验、版本演进、规范/资产、客户案例等不能共用一套空壳模板。
5. 正式页必须是可独立回答问题的正文；原始 Evidence 和定位放到末尾或独立来源页，不让读者先读 Confluence 导出碎片。
6. Home、产品索引、产品总览、模块总览、场景索引和边界页成为正式发布物；叶页只承载一个稳定问题/对象/任务链路。
7. 低置信度、provider 失败、缺失版本/Why 必须显式进入待审，不得带占位字段进入“正式知识”导航。
8. 增加真实 reader-facing 验收：从 Home 找到给定产品/模块/任务，标题可理解，正文能回答“是什么/怎么用/限制/异常/适用版本/来源”，分页可连续阅读，相关主题有真实依据。Claim/行数/溯源仍保留为底线，不再作为质量替代品。

CompanyBrain 自身也不是完美答案：它仍有不确定模块和少量目录审计告警。应借鉴它的“本体先行、页面分型、场景导航、边界明确、持续审计”方法，不应照搬 1,347 个文件或把所有内容改成纯人工维护。

## 子调查报告

- [信息架构对照](20260804-companybrain-ia.md)
- [页面内容与写作质量](20260804-companybrain-content.md)
- [阅读路径与功能差异](20260804-companybrain-reader-journey.md)
