# CONTEXT — Knowledge Digest

## 核心术语

**Claim（论断）**：正式知识页中的一条独立陈述。每条论断必须能关联有效来源、校验状态和变更历史；无法支持的论断不得进入正式页。

**片段定位（`fragment_locator`）**：论断在来源快照中的位置描述，必须与来源地址和来源内容指纹一同写入溯源记录。完整原文清理后，该定位和关联信息仍长期保留；`CONTEXT.md` 是此术语和字段名的唯一权威来源。

**来源快照**：本次手动提供的来源副本及其来源地址、抓取时间和内容指纹。系统保留完整快照与溯源记录；当前没有自动物理清理。

**手动 Digest**：操作人以一组新增材料和一个目标知识库启动一次本地处理。输入中的来源状态可明确标记抓取失败或空壳；系统只处理已提供的文件，不自行访问外部网址。

**二次校验**：只核对本地来源快照的完整性、一致性、来源地址、抓取时间和内容变化。它不访问外部网址，也不代表外部页面当前仍可用。

**待复核**：二次校验失败时的状态。原论断保留、记录失败原因，并在后续手动运行时再次校验；不因临时失败删除论断。本期不设自动终止次数，也不提供人工复核流程。

**替换归档**：论断或托管页面被更新时，先把完整原文、原因及关联来源快照追加到归档；当前只增不删，不做自动物理清理。日常增量不删除旧主题页或旧分页。

**完整重组**：超长文档拆分为业务或逻辑组件时，不能删减任何可处理内容。拆分只改变知识页组织；每个来源片段或论断必须能映射到至少一个输出页。原始来源快照不被拆分步骤覆盖。

**主题页**：围绕一个稳定主题身份组织正式 Claim、可选 Summary、Evidence 和 Provenance 的知识页。主题身份不随输入顺序、批次边界或重复运行改变。

**主题分页**：一个主题的完整内容超过 300 行时生成的确定性多卷页面。每卷都不得超过 300 行；分页只能重组内容，不能截断、遗漏或重复 Claim。

**托管知识页**：页头同时声明 `managed_by: KnowledgeDigest`、`digest_kind: topic`、稳定 `digest_topic_id` 与等于实际路径的 `digest_published_path` 的正式主题页；只有它可被日常 Digest 新增或更新，未托管页面绝不改写，日常运行不删除任何旧页面。

**读者入口**：知识库根目录中面向人阅读的 `Home.md` 和分类索引；它只链接托管知识页，不要求读者进入 `_digest` 或 `_queues`。Home、分类和主题页在同一归档后发布事务中更新。

**发布结构**：由 `kb.structure.md` 声明的托管目录、读者入口和分类规则；新知识库直接发布默认入口和主题页，旧知识库只在这些目录内新增或更新带托管标记的文件，绝不删除旧主题页或旧分页；它重组正式主题页的展示，不复制或替代 Claim、Evidence、Provenance 和审计数据。

**来源索引**：从每个有效来源指向承载其 Claim 的主题页或主题分页的导航清单。它不复制原文、Claim 或 Evidence，也不替代正式 Provenance。

**Reader Package**：用户默认阅读的交付包，只包含 `README.md`、`Home.md`、现有结构/分类导航索引、正式主题页和 `indexes/sources.md`。新运行不生成 `_digest/source-index.md`；历史结果不迁移、不重写。

**Reader Bundle**：把 Reader Package 升级为 OKF v0.2-compatible profile 后的可读交付形态（Task 2-A 起），布局见 PRD §6.8：`README.md → Home.md → 根 index.md → 根 log.md → products/<product>/...`；`Home.md`、Reader `README.md`、`references/sources.md` 是豁免文件，不是 concept，不放 concept frontmatter；来源投影路径是 `references/sources.md`，旧 `indexes/sources.md` 属旧 Reader Package 布局，不迁移、不重写；包级 `digest_release_status` 只在 manifest，不写入 concept 页。

**Raw Reader candidate**：Task 3 真实裸目录演练的候选编译模式。它把输入顶层目录映射为产品，把来源保留在 `products/<product>/modules/<module>/knowledge/`，并把指纹、映射原因和完整来源清单放进同级 `audit/`；没有可靠产品归属的来源进入 `unclassified/general`，不静默丢失。该模式只生成 `candidate/not_released`，不能替代既有机器门、汇总确认或正式发布回读；语义候选与保真整理的数量必须分开报告。

Raw Reader 编译对空内容只写 Audit 失败，不生成“暂无正文”占位页；语义候选还要通过可执行代码的确定性保真检查，失败时回退保真正文并把事实损失写入 Audit，质量代理按实际通过比例扣分。表格、链接、版本历史和普通叙述允许被语义候选重新组织。

**受控语义候选编译**：`scripts/task3_semantic_compile.py` 按固定小批量调用批准的 `qwen3.6`，每批只请求一次，失败不自动重放，逐批输出进度并把失败来源写入 `audit/semantic-manifest.json`。它只生成可供 Raw Reader candidate 消费的语义候选，不直接发布；凭据只能通过 `KD_LLM_API_KEY`、`KD_LLM_BASE_URL`、`KD_LLM_MODEL` 环境变量传入。

**Audit/Archive Package**：用于审计、恢复和排查的交付包，包含 input manifest、source snapshot、Claim、Evidence、原文归档、失败原因、运行报告和配置/provider hash。它不作为日常阅读入口。

**页级发布状态**：页级只允许 `published` 或 `degraded`。`published` 表示通过机器门，可以进入候选 Reader Package；`degraded` 表示失败、冲突、缺证据或人工修改冲突，不进入正式导航。

**来源未说明（`source_not_documented`）**：仅用于 `procedure_or_rule` 页的 `exceptions` section，表示确定性来源审计确认当前冻结来源没有明确的异常触发、处理、分支或恢复规则。它不是“没有异常”的判断，不生成领域 Claim；异常专属问题仍为 `not_answerable`。该 section 仍存在并绑定来源指纹与审计记录；其他缺证据、含糊或映射失败不得使用此状态。

**交付级发布状态**：交付级只允许 `released` 或 `not_released`。Task 0–2 只能是 `not_released`；Task 3 只有在机器硬门、自动固定读者题集、交付完整性和“汇总确认”都通过后才能是 `released`。非阻断警告不阻止发布，但必须留在汇总和审计记录中；未知或无法分类的信号按硬失败处理。

**汇总确认**：人工只确认自动验收汇总完整、可判定且没有明确阻断失败；不打开知识页、不逐题检查、不检查来源链。它不等于人工阅读正文，不产生 `human_reviewed` 内容核验。

**Task 2-C Agent 读者门**：本任务允许 Agent 作为小语料读者质量门的评审主体，但这只是 Task 2-C 的范围修订，不代表人工评审、`verified` 事件或正式发布。逐题证据保留 `agent_assisted=true`，并明确 `review_mode=agent_only`、`gate_actor=agent`；不得写 `human_reviewed`、`human:` actor 或把 Agent 结果派生为 `machine-confirmed`/`human-reviewed` trust tier。即使 Agent 读者门通过，Task 2-C 交付级状态仍为 `not_released`。

**Task 2-C 页级状态映射**：`unverified`、stale 警告和 `status=deprecated` 本身不把页面改成 `degraded`；前者是信任信号，stale 只提示复核，deprecated 保留旧路径但默认隐藏。只有必需信号投影/事实源不一致、来源回查断裂、机器门失败、正文/人工修改冲突或其他明确失败，页面才是 `degraded`，并从正式 Reader 导航排除。页面通过机器门且信号投影可重算时可为 `published`，但 Task 2-C 整包仍保持 `not_released`。

**业务结果幂等**：同一输入快照和配置重跑时，Reader/Audit 中的来源、Claim、页面、duplicate 和 archive 内容不能重复增长；运行记录可以追加，用于保留审计历史。

**待复核清单**：待复核论断在每次运行报告和待处理清单中可见，供后续手动运行再次校验。本期不设告警、数量上限或人工复核产品流程。

**Why（决策背景）**：解释某项设计或规则为何存在的来源内容，不能只保留结果描述。

**版本历史**：来源中关于版本号、修订时间和变更原因的记录，需作为可追溯结构保存。

**结构约定**：每个输入知识库都必须声明 Why 与版本历史的承载字段；系统不假设目标库已具备这些字段。缺少任一声明时，系统不得写入正式知识页，必须明确指出需要补齐的结构。

**标定产物**：把模型身份、向量维度、语料与标签版本、校准集和留出集结果、三个阈值及采用状态绑定在一起的可重放证据；裸阈值不构成标定产物。

**采用状态**：标定产物对 embedding 的结论，只能是 `adopted` 或 `not_adopted`；未通过安全门时保持 Jaccard，不得为了启用而降低门槛。

## 关系

- **标定产物**属于一个明确的本地 embedding 模型和一份隔离语料
- **采用状态**由独立留出集决定，不能由校准集或实现完成度决定
- 公司 Confluence 正文只能发送给本机 embedding 服务，不得发送到外部 API
- 每个有效来源至少由一条**来源索引**记录指向承载其 Claim 的**主题页**或**主题分页**
- **主题分页**合计保留该主题的全部 Claim，并继续满足 Evidence 与 Provenance 门禁
- 每个**托管知识页**属于一个**发布结构**；**读者入口**只链接其可读路径，审计数据继续留在 Audit/Archive Package 的 `_digest` 与 `_queues`，不进入 Reader Package
- 只有存在真实、非空、可导航的待处理项时才生成 `pending`；离线标题依次取既有托管标题、来源 metadata title/H1、文件名，稳定主题身份仍只由来源决定
