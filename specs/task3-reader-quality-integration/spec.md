# mini-task spec：结构化 Reader 编译

## 结果

给定真实来源目录和可选 Task3 语义候选，KnowledgeDigest 生成按产品、模块、知识页组织的 Reader Bundle；Reader 干净可读，哈希和审计字段只出现在 Audit。

## 流程与范围

维护者指定输入和候选输出目录；系统冻结普通 Markdown/文本/JSON，记录路径、产品、指纹和行数；按“产品→模块→知识页”编译；生成产品 overview、模块索引、来源入口、Audit 和一页汇总；机器检查覆盖、导航、泄漏和 300 行限制。

```text
bundle/README.md  Home.md  index.md  products/index.md
bundle/products/<product>/{index.md,overview.md,modules/index.md}
bundle/products/<product>/modules/<module>/{index.md,knowledge/<knowledge>.md}
bundle/references/sources.md
audit/source-manifest.json  ...运行、指纹、质量、失败证据...
reports/projection-report.json  quality.json  release-summary.json
```

`bundle` 是日常入口，`audit` 是追溯/恢复/排错入口。Reader 不放完整 source id、topic id、content hash、fingerprint、生成器、验证事件、provider 配置或逐页机器信号。

每个产品另外生成 `knowledge-types/<type>/index.md` 作为类型入口，类型只做可追溯来源投影：产品定位与边界、模块手册、技术实现、经验与坑、规范与资产。它们链接既有唯一知识页，不复制正文，不增加第二份事实。

## 状态

`snapshot` 输入冻结；`candidate` 已生成未过门；页级 `published/degraded/failed` 描述单页；包级 `released/not_released` 描述整套交付。失败或未知不得升级，失败运行不覆盖旧正式包。

## 成功边界

- 89 条真实有效资料全部有且只有一个 Reader 逻辑知识入口；超长入口拆成连续 `part-01/part-02` 页面，不丢内容。
- 每个产品有 overview/index，每个模块有 index，Home 可达每个知识页。
- 每个产品至少有一个真实类型入口；类型入口可回到唯一知识页，不把经验、规范和产品资料继续混在一个平面。
- Reader 去除内部元数据、哈希脚注和审计块，保留事实、结构、代码、表格、链接和来源入口。
- 结构、覆盖、泄漏、链接、行数检查通过；语义覆盖与保真整理覆盖分开记录。

## 失败边界

- 读取/编码/空内容失败：只写 Audit，整包 `not_released`。
- 无法确定产品：进入 Reader 的 `products/unclassified/modules/general/knowledge/`，页面标 `degraded`，Audit 记录原因；不伪造产品，但不让来源消失。
- 软链接、导航逃逸、非新候选目录或旧包保护失败：停止且旧包不变。
- provider 不可用：允许保真整理 candidate，但不能宣称语义质量或 released。
- 重复落点、事实损失：机器失败，不静默发布。
- 超过 300 行：按 300 行硬上限拆成连续页面，页间有上一页/下一页链接；拆分失败才进入 Audit 失败。

## 非目标

不重走 make-decision，不用 build-spec 补需求；不改 TopicIndex、Task2-C 17+3 和状态语义；不新增本体、向量库、数据库、调度器或 AgentMemory；不修改 CompanyBrain；不增加逐页人工验收。

## 验收条件

- AC-01 产品→模块→知识页层级存在。
- AC-02 产品 overview/index 可读。
- AC-03 有效来源唯一落点且完整对账。
- AC-04 Reader 无哈希、指纹和内部字段。
- AC-05 正文清理但不丢事实。
- AC-06 Home→产品→模块→知识页全链路可达且每页≤300行。
- AC-07 语义不可用时诚实降级。
- AC-08 失败不覆盖旧正式包。
- AC-09 一页汇总保留人工确认边界。

## 80 分代理口径

这是机器可复算的结构质量代理，不是对 CompanyBrain 的主观等价承诺：结构层级 20 分、有效来源覆盖 20 分、产品入口 15 分、Reader 清洁度 15 分、内容保真 20 分、溯源入口 10 分，共 100 分；每项按实际通过比例计分，`score >= 80` 才能标记 `reader_quality_proxy_passed`。语义 provider 不可用时仍可生成 candidate，但必须单独标注 semantic unavailable。

## 最小依赖接口

- source manifest：`source_id`、`source_uri`、`relative_path`、`title`、`content_fingerprint`、`line_count`、`validation_status`。
- semantic candidate：`source_uri`、`content_fingerprint`、`title`、`summary`、`body`、`module`、`semantic_status`。
- Audit 映射：`source_id`、`reader_paths`、`product`、`module`、`mapping_reason`、`content_fingerprint`、`semantic_status`。
- 可选 TopicIndex 只读取 `source_members/source_ids/product/module/object_intent/published_path`；TopicIndex 不被本 mini-task 改写。
