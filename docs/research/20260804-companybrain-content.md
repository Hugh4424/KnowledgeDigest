# CompanyBrain 与 Task2 内容质量对照

调查范围：只读检查 `/Users/Hugh/Hugh/Knowledge/CompanyBrain` 与 `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb`；未调用外部模型、未改代码。

## 结论

CompanyBrain 的优势不是“摘要更短”，而是先建立稳定的知识本体、页面职责和读者入口，再把来源内容编译进对应页面。Task2 主要完成了来源拆分、固定模板、分类索引和溯源写入，仍接近“带摘要的来源归档”，没有达到 CompanyBrain 的知识发布层。

## 可复核统计

### Task2

- `pages/` 有 120 个 Markdown 页面；其中 34 个是 `.part-*`，基础主题约 86 个。
- `indexes/` 有 27 个分类/子分类索引，根入口是 `Home.md`。
- `pages/` 的 120/120 页面都包含固定的 `Summary`、`Why`、`Version`、`Related topics`、`Evidence`、`Provenance` 六段。
- 120/120 页面都写 `暂无已验证的相关主题`；实际业务关系没有形成页面级链接。
- 33 个页面接近 300 行，34 个页面是分页文件。
- 73/120 文件名属于短名、碰撞名或明显不具备业务语义的名字；27 个文件名直接是 `topic-<hash>`。例：`pages/customers/customer-overview/topic-d87aa93b.md`、`pages/products/product-capability/ae.md`、`pages/engineering/implementation/16.md`。
- 86 个唯一标题中有 24 个标题重复；例如 `Uptrillion日志管理` 5 份、`AE - 应用详情` 3 份、`AE-参数推送` 3 份。文件名无法帮助读者区分重复主题。
- 15 页明确写 `未提供版本信息`，另有页面写 `Missing`/`版本信息缺失`；这类占位信息未转化成可靠的时间/适用范围判断。
- 页面 front matter 主要只有 `managed_by`、`digest_kind`、`digest_topic_id`、`digest_published_path`、`digest_part`，缺少 CompanyBrain 使用的产品、知识类型、可信级别、更新时间、质量状态、可见范围等读者和 agent 需要的元数据。

证据示例：

- `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/pages/products/product-capability/12-goinsight-dc.md` 的标题虽然可读，但正文把部署、迁移、平台注册、MAXSTORE 配置、数据库检查混在一个主题中，`Related topics` 仍为空。
- `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/pages/products/product-capability/ae-c69e5c54.md` 有可读摘要，但正文仍以来源原文顺序展开，包含大量截图/链接和不同条件的流程，未拆成入口、前置条件、权限判断、控制流程、异常边界等独立知识页。

### CompanyBrain

- CompanyBrain 总计 1,347 个 Markdown；排除 `_gbrain` 与隐藏目录后的正式知识层为 838 个 Markdown，分布在明确的 `Products`、`Engineering`、`Customers`、`Operations`、`Principles`、`ProductBoundaries` 下。
- 正式知识层没有发现以纯 hash 或 `ae`、`ios`、`global` 等短值作为文件名的页面（统计为 0）。
- 412 页含 `page_model` 与 `quality_status` 等质量元数据；436 页含 `updated`；603 页显式记录来源；260 页包含“使用边界”；74 页包含使用方式/场景/查询建议。
- GoInsight 单产品目录有 281 个 Markdown，按 `产品定位`、`模块手册`、`技术实现`、`经验与坑`、`规范与资产`、`使用场景索引` 分层；模块手册又按真实业务对象分成数据集、字段与筛选、工作表、图表、大屏、报告、设备与应用、组织权限等。
- CompanyBrain 根入口 `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Home.md` 明确按 Products、Engineering、Customers、Operations、Principles 分流，并给出查询建议和使用边界；GoInsight 的 `文档总览.md`、`模块总览.md`、`使用场景索引.md` 继续提供产品内入口和按问题类型的调用路径。

代表性页面：

- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/产品索引.md` 先给产品定位入口、能力分组、产品清单和使用边界，不把正文塞进索引。
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/模块手册/设备与应用/设备状态、库存与运维.md` 围绕一个业务对象组织状态、运维数据、使用边界和可追溯来源，而不是简单复制来源标题。
- `/Users/Hugh/Hugh/Knowledge/CompanyBrain/Products/GoInsight/产品定位/产品关系与边界.md` 明确 GoInsight 与 MAXSTORE、AirViewer、MobileAPP、SupportHub 的责任边界，解决跨产品误用。

## 为什么 CompanyBrain 更可读

1. **先有知识模型，再有页面**：GoInsight 的配置和审计文件明确要求先做来源分层、业务对象字典、对象关系和场景链路，再规划页面；来源标题不直接等于正式页面。
2. **页面按问题和对象切粒度**：产品定位、模块手册、技术实现、经验与坑、规范资产分开；一个页面回答一个稳定问题/对象/任务链路，目录页只做入口。
3. **正文由业务顺序重组**：例如设备状态页按状态→运维数据→边界→关键细节→来源索引组织；不是把 Confluence 行号顺序直接拼起来。
4. **导航是产品功能**：根入口、产品总览、模块总览、场景索引和边界页形成多级可读路径；Task2 只有通用领域/子分类，缺少“产品→模块→任务/规则”的语义导航。
5. **显式表达边界和使用方式**：CompanyBrain 页面普遍写适用场景、使用边界、时间和来源；Task2 的固定 `Why`/`Version`/`Related topics` 占位段不能替代真实边界判断。
6. **允许人工/规则驱动的渐进治理**：CompanyBrain 的 `quality_report.md` 会记录不确定模块而不乱改，`model_audit` 会记录对象错位；这说明其质量控制接受“不确定并待审”，而非把低置信分类直接发布成正式知识。

## 对 KnowledgeDigest 的修复启示

- 不能只改文件名或把 `topic-hash` 换成 LLM 标题；必须增加“知识编译”阶段：来源清单 → 来源类型 → 业务对象/产品 → 页面规划 → 正文编译 → 人工/规则验收。
- `Summary/Why/Version/Related` 不应是所有页面强制模板。页面结构应按功能说明、操作配置、规则边界、故障经验、版本演进、决策等知识类型选择。
- 分类器需要稳定的产品/对象字典和关系图谱，低置信内容进入待审区，不能直接进入正式导航。
- 主题页应支持一个主题多个细节页，并在产品/模块/场景入口处链接；300 行上限只能是分页安全门，不能是页面设计目标。
- 文件路径必须由稳定业务对象和页面标题生成，哈希只能作为内部 ID；同标题/同 slug 冲突必须显式处理。
- 发布前至少要有读者验收：从 Home 能否找到某个产品/模块/任务，打开页面后能否回答“是什么、怎么用、限制、异常、版本、来源”；不能用 Claim 数量、页数、行数、溯源存在代替语义质量。
- 应保留原始来源/归档，但正式页只保留经过业务重组的可复用知识；来源链接和定位放在末尾或独立来源索引，不能让 Evidence 原文成为正文主体。

## CompanyBrain 自身边界（避免照搬）

CompanyBrain 也不是零缺陷：其 GoInsight `quality_report.md` 仍记录 60 个 `uncertain_module`，`model_audit` 仍有 13 个对象目录错位警告，说明人工/规则治理仍在演进。应借鉴其“先建模、分层、审计、不确定即待审”的方法，而不是复制 1,347 个文件或全部人工维护。

