# KnowledgeDigest Task2：知识发布架构规格

状态：build-spec 已形成可实施版本；正式 WorkflowHub publication 受 vNext task 与旧 stage-runtime 不兼容阻塞，见第 9 节。
上游方向：`decision-log.md`

## 1. 目标与边界

Task1 已能保留 Claim、Evidence、Provenance 并安全写回，但结果仍像按批次堆叠的 Markdown：标题泛化、分类单一、主题页过大、读者入口不清楚。本任务只补上“知识发布层”，让同一份消化结果先可浏览、再可理解、最后可回溯。

成功标准不是 Claim 数量增加，而是读者可以从 `Home.md` 按领域进入一个语义化主题页，在页内理解用途、摘要、背景和版本信息，并用来源索引回到原始材料；所有原有内容和质量门不能丢失。

本任务不重写 Task1 的 S1–S6 Claim/Evidence/Provenance 算法，不把产品变成在线服务、数据库或 AgentMemory 系统。

### 已锁定决定

- 采用轻量分层，不大搬现有 `src/knowledge_digest`。
- 主题页使用语义标题、受控分类和来源索引；不复制原文作为附录。
- 同一主题先完整聚合，再分页；当前页硬上限 300 行。
- 批次逐步写入，失败批可拆分并用同一状态文件恢复。
- 保留 fail-closed、写前归档、原子发布、Provenance、macOS spawn 和无损约束。
- 构建阶段允许 qwen3.6 与 jina-embeddings；DeepSeek 不进入正式 pipeline。
- 发布后的知识库必须完全离线可读。

### 当前未解决项

无产品范围未决项。实现阶段只能在本规格的字段、分类、预算和验收边界内做细节选择；若需要改变这些边界，先更新规格和验收测试。

## 2. 发布数据模型

### SCOPE-001 主题发布记录

每个最终主题有稳定 `topic_id`、`title`、`slug`、主分类、可选的确定性 `product_slug`、`summary`、`why`、`version`、`claim_refs`、`field_refs`、`related_topics` 和分页记录。`product_slug` 只从来源 metadata title/H1 或确定性规则提取，不能由模型自由发明；缺失时不做产品分组。首次发布后，`_digest/topic-index.json` 持久化 `topic_id`、来源成员、首个 category 和首个 published path；后续新增来源、输入顺序变化或标题变化都复用该 identity。标题改变只改 H1，不改路径；分类改变不自动移动，转为 `needs-review`。

主题页必须包含：

1. 语义标题，禁止 `cluster-N`、`draft-N`、输入顺序或裸文件名；
2. 一句话用途；
3. `Summary`，只概括页内已验证 Claim；
4. `Why`，无法证明时写“来源未说明”；
5. `Version`，没有版本信息时写“未提供版本信息”；
6. `Evidence` 与定位；
7. `Provenance` 与验证状态；
8. 经验证的 `Related topics`。

### SCOPE-002 受控分类

分类的唯一运行时事实来源是知识库自己的 `kb.structure.md` `publication_categories`。不新建并行 `config/publication-taxonomy.json`，避免两份分类表漂移。该段扩展以下字段：`taxonomy_version`、`taxonomy_owner`、`taxonomy_change_policy` 和每个叶分类的 `id`、`title`、`topic_dir`、`parent_id`、`aliases`；父分类只由受控 `parent_id` 集合派生，不是可写目录。序列化格式仍是当前 YAML-like frontmatter：列表字段使用重复的 `- value` 行，禁止引入未声明的嵌套 YAML。

初始 taxonomy 版本为 `1.0.0`，owner 为 `KnowledgeDigest maintainers`，普通 digest 运行不得改变它。父分类是逻辑节点，不占用 topic directory；叶分类才声明唯一 `topic_dir`，Home 只链接父分类索引，父索引再聚合叶分类主题。两级分类固定如下；`Other/unclassified` 是明确兜底，不是默认垃圾桶：

- `products` 产品：`product-overview`、`product-capability`、`product-operations`、`product-boundary`
- `engineering` 研发：`architecture`、`implementation`、`operations-troubleshooting`、`development-practice`
- `customers` 客户：`customer-overview`、`customer-case`、`market-feedback`
- `operations` 运营：`project`、`management`、`people`、`competitor`、`event`
- `principles` 原则：`business-principle`、`content-standard`、`delivery-standard`
- `other` 其他：`unclassified`
- `pending` 待归类：运行控制分类，不计入 `Other` 占比；用于缺少可靠分类证据的主题。

分类新增、合并、删除或别名变化必须由维护者修改 `kb.structure.md` 并升级 SemVer；补丁版本修正文案，次版本新增兼容分类，主版本重命名/删除分类。模型只能从声明的分类中选择，不能创建新分类。新 KB 初始化时一次声明完整分类和 `pending`；已有 KB 缺少 `taxonomy_version` 时，Task2 语义发布必须 fail-closed 并提示人工迁移，不自动把旧 pending 页面移动到新目录。已有 managed topic 的 category/path 一旦登记，分类冲突只进入 `needs-review`。

89 篇 Task2 对比使用新的空 KB，Task1 输出只作为只读基线，不作为待原地改造的输入。因此本任务不实现旧 pending 页面到新 taxonomy 的物理迁移；已有 KB 的迁移另开任务或由维护者先显式完成结构升级。

### SCOPE-003 读者导航

正式入口固定为：

`Home.md → indexes/<parent>.md → <declared-topic-dir>/<topic-slug>[.part-N].md → <publication_source_index>`

结果根目录额外生成受管 `README.md`，用大白话说明 `Home.md` 是入口、`indexes/` 是分类导航、主题目录是正文、`_digest/` 是审计和来源索引、归档目录不可直接阅读且不要手改。`Home.md` 展示分类说明、主题数、最近更新和待复核入口。父分类页展示叶分类说明和主题入口，叶分类页展示主题标题、用途摘要、更新时间和来源数。Products 叶分类页按确定性的 `product_slug` 再分组，避免不同产品重新堆成一个大目录。主题页的 `Why` 映射 CompanyBrain 的使用场景/调用建议；来源提供使用边界时单独显示，不臆造。来源索引每个有效来源只出现一次，包含显示名、相对 URI、内容指纹、状态和到当前主题页的相对链接；不复制 Claim、Evidence 或正文。重复来源继承 canonical 来源链接。`publication_source_index` 是 `kb.structure.md` 声明的托管路径，默认 `_digest/source-index.md`。它的 canonical 序列化形式是固定列顺序的 Markdown 表格（`source_uri`、`content_fingerprint`、`status`、`target_paths`），表头包含 `schema_version`；程序内部仍按 `{schema_version, entries:[...]}` 结构校验，不能再写第二份并行 JSON。它必须与 Home、分类、主题、Provenance 一起归档后原子发布。

## 3. LLM、embedding 与确定性回退

### FR-LLM-001 建议接口

LLM 只接收冻结的主题证据、主题元数据和允许的 taxonomy，输出一条严格 JSON 建议。建议作为现有 `draft` generator 响应中的可选 `publication` 对象返回，不新增第二次模型调用；程序决定最终标题、slug、分类、路径、分页、链接和权限；模型不能发明事实、来源、分类或写文件。

允许的模型身份：

- LLM：`qwen3.6`，OpenAI-compatible endpoint；
- Embedding：`jina-embeddings`，OpenAI-compatible endpoint。

凭据只从环境变量读取，不能进入配置、task receipt、日志、报告或 KB。qwen3.6 继续使用现有 `KD_LLM_*` 环境变量；jina 继续使用现有 `similarity.embedding` 配置、`api_key_env` 和 adopted calibration artifact。运行时 resolver 必须校验允许的 model/base URL，拒绝 DeepSeek 和其他 provider；缺失或失败时只走 Jaccard/deterministic fallback，不切换 provider。

### FR-LLM-002 JSON 合同

建议对象必须满足以下等价 JSON Schema；未知字段拒绝：

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["title", "slug", "category_id", "summary", "why", "version", "related_topics", "claim_refs", "field_refs"],
  "properties": {
    "title": {"type": "string", "minLength": 4, "maxLength": 80},
    "slug": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{2,63}$"},
    "category_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{1,63}$"},
    "summary": {"type": "string", "maxLength": 420},
    "why": {"type": "string", "maxLength": 280},
    "version": {"type": "string", "maxLength": 120},
    "related_topics": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
    "claim_refs": {"type": "array", "maxItems": 80, "items": {"type": "string"}},
    "field_refs": {
      "type": "object",
      "additionalProperties": false,
      "required": ["title", "category_id", "summary", "why", "version"],
      "properties": {
        "title": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
        "category_id": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
        "summary": {"type": "array", "maxItems": 16, "items": {"type": "string"}},
        "why": {"type": "array", "maxItems": 16, "items": {"type": "string"}},
        "version": {"type": "array", "maxItems": 16, "items": {"type": "string"}}
      }
    }
  }
}
```

提示词固定包含四段：`ROLE`（只做语义建议）、`EVIDENCE`（带 Claim ID 和定位的冻结证据）、`ALLOWED TAXONOMY`（当前分类及别名）、`OUTPUT SCHEMA`（上面的 JSON 合同）。提示词明确禁止新事实、整段复述、越权路径和思考内容；客户端只读取现有响应的最终 `content`，不能写入 `reasoning_content`。

### FR-LLM-003 校验与保真门

写入前必须依次通过：JSON 解析和 schema；`category_id` 在 taxonomy；`claim_refs` 是当前主题 Claim 的子集；`field_refs.<field>` 是 `claim_refs` 的子集；每个非回退字段至少引用一个 Claim；生成字段中的数字、版本号和专有标识符必须能在被引用 Evidence 中找到；related topic 在完整 topic universe 建立后由 navigation pass 校验，未知 ID 丢弃并标记 needs-review；slug 和路径必须通过现有写入安全门。确定性 slug 必须是 ASCII：优先标题转 ASCII，无法转写时使用 `topic-<stable-id-suffix>`，同分类同 slug 冲突追加稳定 ID 后缀。失败时该字段使用确定性 fallback，并报告 provider、批次、字段和原因；不能把半合法输出写入正式页。

### FR-LLM-004 embedding 的明确用途

embedding 只用于候选主题检索、重复/相关主题排序和聚类辅助，不生成正文、不决定权限、不改变 taxonomy。一个运行只允许选用一个相似度后端；选中的 adopted artifact、endpoint identity、model、dimension、probe fingerprint 和文本 hash 必须参与 cache key。embedding 不可用时整次回退 Jaccard，禁止混用分数。`--no-llm` 既不调用 LLM，也不探测 embedding。

### FR-LLM-005 局部回退与离线消费

LLM 或 embedding 失败只影响当前来源/批次：确定性标题、分类、Claim、Evidence、Provenance 和导航继续发布，失败来源标为 `needs-review`。已成功批次立即落盘；修复后从同一状态文件恢复，不重复成功批次。无 LLM 时标题依次取既有托管标题、metadata title/H1、文件名；分类使用明确的 metadata/规则映射，无法判断进入 `pending`，不把所有主题塞入 `Other`。发布后的 KB 在无网络、无模型和无凭据环境中仍能阅读、导航、回溯和结构校验。

## 4. 批次、性能和安全接口

状态文件 schema 升级为 v3，锁定来源相对路径、URI、内容指纹、taxonomy 版本、模型身份、相似度 backend identity、首次主题计划、topic-index fingerprint 和请求预算。`topic-index.json` schema 为 `{schema_version, topics:[{topic_id, source_ids, category_id, published_path, product_slug}]}`。来源、taxonomy、模型身份或 topic plan 变化必须拒绝续跑并要求新状态文件；失败批可记录 `split_from` 并按来源拆分，成功批不重复调用。

对 89 篇固定语料冻结以下运行预算：publication 建议必须复用现有 generator 请求，不得新增第二次语义调用；dry-run 先按现有 `llm_batch_max_claims`/`llm_batch_max_source_chars` 计算 planned generator calls；planned calls 超过 180 时在发出 provider 请求前停止。单次请求硬超时 180 秒，目标墙钟时间 30 分钟，60 分钟为安全硬上限；失败来源最多一次拆单重放。预算超限是性能失败，不得伪装成内容成功；报告记录 generator/publication 调用数、失败数、重放数、耗时、token（若 provider 提供）和 fallback 比例。

Home、分类页、主题页、`publication_source_index` 和 provenance 在同一写入批次中先归档后发布；source-index 写失败时旧 index 必须保持可恢复。只允许 `kb.structure.md` 声明的目录；手写文件、路径逃逸、软链接、页头路径不符、失效链接、清单变化和模型越权必须明确 fail-closed。

## 5. 验收标准

### AC-001 导航和分类

89 篇固定语料运行后，按 taxonomy 分层抽取 `min(20, 当前主题数)` 个主题；若少于 20，报告缺口，不伪造样本。每个主题从 Home 最多三次点击可达正文，并可回到来源索引。当前主题不得全部落在单一 `pages/digest`。`Other` 占比不得超过 20%；`pending` 单独报告，不计入 `Other`。Products 分类索引按 `product_slug` 聚合主题，避免不同产品重新堆成一个大目录。

### AC-002 语义可读

抽样主题中至少 80% 的标题在不打开正文时能说明主题用途；标题不得是文件名、编号、`cluster-*`、`draft-*` 或“知识总结”。分类、标题、路径在同一初始 KB 上重复运行必须稳定。

### AC-003 读者字段完整

100% 当前主题页含 Summary、Evidence、Provenance。Summary、Why、Version 要么有 Claim/Evidence 引用，要么使用明确缺失标记；字段不能重复整段正文。每页不超过 300 行，每个有效 Claim 只出现于一个当前 part。

### AC-004 内容无损与回溯

Task1 基线的所有有效 Claim、来源 URI、内容指纹、定位、验证状态逐项匹配；每个 Claim 只有一个当前 target path。任一主题页能经 source-index 找到原始 URI 和指纹；坏来源、空壳来源、无效链接不能进入有效列表。

### AC-005 批次恢复

注入一个 provider 失败和一个 malformed JSON：成功批次保持可读，失败来源标为待复核；修复后用同一状态文件恢复，不重复成功批次、不产生重复主题或孤儿索引。来源变更时续跑必须拒绝。

### AC-006 离线边界

清空模型凭据并断网后，Home、分类页、主题页、来源索引和结构校验仍可用；`--no-llm` 运行不得发出任何 LLM/embedding 请求。

### AC-007 CompanyBrain 阅读对比

对 Task1、Task2 和 `/Users/Hugh/Hugh/Knowledge/CompanyBrain` 使用同一份分层抽样表：Products、Engineering、Customers、Operations、Principles 各最多 4 个，总数为 `min(20, 当前主题数)`；不足时记录缺口，不从无关页面补齐。样本 manifest 先固定 Task2 `topic_id`，再按 shared source URI/product_slug 匹配 Task1 页面和 CompanyBrain 最近语义页面；无法匹配时标记 `no_match`，不人工换样。每行记录：`title_understood`、`category_correct`、`home_to_topic_clicks`、`source_backlink`、`summary_faithful`、`why_or_missing_explicit`、`version_or_missing_explicit`、`usage_boundary_visible`、`orphan_link`、`reader_time_seconds` 和人工备注。报告把机器证据与人工判断分开，不把 Claim 数、页数或 token 数称为质量。

### AC-008 成本与安全

报告包含 89 篇运行的 provider 调用数、失败/重放数、耗时、token、fallback 比例，并检查未写凭据、未越界文件、未改 taxonomy、未触碰手写页。越界或预算硬上限必须 fail-closed。

## 6. 最小实现边界

保留现有 `src/knowledge_digest` src-layout，不建立通用 framework/repository/provider 层。只新增两个内部职责：

- `publication.py`：语义建议、JSON/schema 校验、字段 fallback、taxonomy 选择和保真门；
- `navigation.py`：Home、分类索引、主题页、来源索引的读者渲染与链接汇总。

复用并深化现有 `kb_structure.py`（taxonomy 的唯一声明与校验）、`identity.py`（stable topic ID）、`page_layout.py`（最终聚合分页）、`batch_run.py`（v3 清单与恢复）、`writeback.py`（先归档后原子发布 source-index）、`provenance.py` 和 `llm.py`（既有 qwen 请求、180 秒 hard deadline、publication object）。`pipeline.py` 只编排，不承载 prompt、分类规则或 Markdown 拼接。不得新增 `taxonomy.py` 或并行 taxonomy 配置文件。

## 7. 风险、非目标与交付物

CompanyBrain 只作为“入口清楚、按领域组织、带使用边界和来源可追溯”的读者参考，不复制 Obsidian 插件或运行时。个人/企业权限隔离留作后续任务；本任务只发布静态、离线可读知识。

非目标：数据库、向量库、CAS、journal、调度器、在线聊天、AgentMemory、权限系统、重写 S1–S6、模型自由分类、删除历史 part。

交付物：代码与 acceptance 测试、更新后的 `AGENTS.md`/项目文档、每个发布 KB 根 `README.md`、89 篇 Task1/Task2/CompanyBrain 对比报告、批次与成本报告。正式知识库输出必须能解释每个文件的用途和入口关系。

## 8. 审查修订记录

本版根据 build-spec 独立审查补齐了：现有 `kb.structure.md` 单一分类事实来源、初始两级 taxonomy/version/owner/变更规则、完整 JSON schema 与提示词段落、embedding 的唯一功能边界、请求和墙钟预算、CompanyBrain 20 主题抽样表、稳定路径锁定规则，以及“无未决产品歧义”的明确声明。运行时只允许用户已指定的 qwen3.6（`https://dashscope.in.whatspos.cn/v1`）和 jina-embeddings（`https://llm.paxszapp.com/v1`），拒绝 DeepSeek 及其他 provider。审查过程中的 provider permission failure 和首次缺少 context map 的 unavailable 结果保留在 TaskHandle 证据目录，不被改写成成功。

## 9. WorkflowHub 状态披露

上一版规格曾通过一次真实 `build-spec` wh-review，质量 verdict 为 pass；其中两路 provider 有效，`cursor/grok` 因尝试访问审查包外工具而 permission denied。随后按审查意见修订了当前规格（单一 taxonomy 来源、完整 schema、embedding 用途、预算、抽样表和最小组件边界）。同一 review flow 的重跑复用了既有结果，没有产生针对本版文本的新 provider verdict，因此本版不把旧 pass 包装成新审查证据。

正式 publication 尚未写入：当前 TaskHandle 使用 `vnext-single-write`，公开 `stage-runtime` 仍调用旧 attempt writer，执行时报 `legacy attempt writer is unavailable for vNext tasks`。这属于 WorkflowHub 运行器兼容性问题，不是规格或产品验收结论；不得伪造 receipt，也不阻断后续在同一 TaskHandle 上进行 build-plan 的人工推进。
