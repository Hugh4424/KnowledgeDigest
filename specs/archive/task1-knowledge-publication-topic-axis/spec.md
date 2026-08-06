# Task1：知识类型、产品模块和稳定主题主轴规格

状态：发生 scope revision；已把 CompanyBrain 证明的知识类型优先级写入当前规格，已评估有效异源审查建议，当前可进入 build-plan。

## 0. 当前材料修订说明

- 本版是 `build-spec` 首版起草。
- 依据：已接受的 `decision-log.md`、PRD Task1、现有 `CONTEXT.md`、ADR 0004、当前代码和验收测试。
- 本版做的事：把已接受方向整理成稳定的功能需求、数据边界和验收条件，并显式列出仍会影响接口或验收的技术歧义。
- 本版没有新增产品目标、页面范围、发布承诺或 provider 依赖。
- 影响材料：`decision-log.md` 的 §4、§5、§6、§7、§8、§9、§10、§11；后续 `plan.md` 和 `tasks.md` 尚未建立。
- v0.2：build-spec 依据用户已接受的 Task1 范围、PRD、ADR 0004 和现有文件结构，直接收敛 ProductGazetteer 存放在 `kb.structure.md` 受控区段；已解除 `AMB-01`，并更新 FR-02、§6、AC-02。原因：本项目已有 `kb.structure.md` 作为文件型 KB 的结构权威，单文件更容易随 KB 一起复制、审计和重建；代价是词表变更会与结构文件产生更大的合并冲突。
- v0.3：build-spec 依据同一材料直接收敛 `topic_key_v1` 使用产品/模块/对象-意图的 canonical 语义 ASCII slug tuple；别名先归一到 canonical，再参与 key 生成。空白和标点归一为稳定 slug；规范化后仍冲突时不得静默合并，必须进入冲突/降级。已解除 `AMB-02` 的方向部分，并更新 FR-05、FR-06、AC-03、AC-06。原因：key 需要可读、可跨平台和可审计；代价是词表变更必须维护兼容映射。
- v0.4：build-spec 依据 PRD 和现有词表边界直接收敛匹配优先级为 canonical → alias → 父子路径 → H1/标题 → 模型候选；同一优先级多个命中直接标为冲突/降级，不靠输入顺序猜测。已解除 `AMB-03`，并更新 FR-02、FR-04、AC-02、AC-04。原因：正式词表优先于文档表面线索，能降低误归类和模型污染；代价是资料不完整时降级会更多。
- v0.5：build-spec 依据“最简单可追溯”原则直接收敛 TopicIndex 以“一个当前主题一条记录”为主，`old_path_mapping` 使用列表表达旧路径到当前主题的合并/拆分关系；不另建平行权威映射表。更新 FR-05、AC-05、AC-06。原因：保持文件型 KB 的单一投影，足够表达迁移关系；历史审计仍依靠映射条目中的关系和证据。
- v0.6：其余技术合同按 PRD、ADR 0004、现有文件结构和当前代码直接收敛：Task1 只计算 affected set，不写最终 Home；人工编辑冲突 fail-closed；fixture 使用稳定排序的 JSON/JSONL 证据；保留旧 `digest_topic_id` 并新增语义 `topic_key`；正式验收走 `--no-llm`，provider 不属于 Task1 必需运行链路。没有新增产品范围。
- v0.7：首轮 `wh-review` 的 3 个 provider 中 2 个通过、1 个要求修订；主 agent 接受其有效内容并修正：补齐 ProductGazetteer `owner`、TopicIndex/旧路径映射最小 schema、related-link topics 的 affected set、reserved word/版本升级规则、空目录/facet 延期边界、人工哈希冲突的 fail-closed 验收和顶部状态。无效锚点不作为事实依据，但对应问题已用 PRD/现有代码复核后修正。
- v0.8：第三轮 `wh-review` 发现并修正最后合同：inventory 正式包含内部 link edges；补齐可判断的 published path 算法、产品/模块 kind、object/intent 的确定性 seed、TopicPlan degraded null 规则、Jaccard 离线边界，并恢复非默认、逐页、可审计的显式 override。无效锚点不作为事实依据；override finding 有 direct evidence，已按上游允许的恢复边界修订。
- v0.9：最新 review 建议已评估并修订：统一 degraded 缺省字段为 JSON `null`、补充 ProductGazetteer 的对象字段和 canonical-only 发布门、固定路径碰撞为 fail-closed、补齐单来源五项的离线判定、固定三个当前产物的审计路径。按用户规则保留 review 建议，不继续循环追 pass。
- v1.0：真实语料补证后明确：当 `kb.structure.md` 没有 ProductGazetteer 时，KnowledgeDigest 从当前 inventory 的产品根路径、标题和 H1 自动生成可追溯 `candidate` seed 并写入受控区段；不读取 CompanyBrain 或其他外部词表。候选不能自动晋升 canonical；没有明确层级证据的模块、别名和 object/intent 保持 candidate/空数组并降级。
- v1.1：用户纠正顶层目录规则：企业知识库先按 `knowledge_type` 分流，`Products` 只是其中一种类型；`Customers`、`Engineering`、`Operations`、`Principles`、`ProductBoundaries` 等不能被当成产品或 facet。ProductGazetteer 只在 `knowledge_type=products` 下负责 product/module/object-intent；本次 89 条原始语料按其产品资料边界进入 `products`，不读取 CompanyBrain 作为运行上游。旧 product-only 的字段、key、path、affected set 和验收条款均需按本修订重审。
- v1.3：用户要求确认 canonical ProductGazetteer。当前原始语料明确声明的 `products/<product-root>` 和稳定 source page/capability seed 现在定义为 source-canonical；不再把确定性来源事实一律停在 candidate。模型/provider 提案仍只能是 candidate；缺失的 object/intent 仍为空并明确记录，不猜测业务语义。
- v1.2：评估本轮有效异源建议并修订：初始 registry 只从当前有证据的类型生成，不预置 CompanyBrain 的非产品类型；当前知识类型优先的 key 正式命名为 `topic_key_v2`；非 Products 在本 Task1 只有顶层类型和安全降级边界，不能误认为有已实现的 published 类型内路径。逐页显式 override 保留为非默认、逐页、可审计的恢复边界，不引入人工审批队列或批量放行。

## 1. 目标和结果

### 1.1 目标

解决当前 `batch_size=1` 把来源错误地当成主题边界的问题，在 provider 之前先建立稳定、可追溯的 `knowledge_type` 顶层轴；进入 `products` 类型后，再使用产品→模块→对象/意图主题轴。

Task1 完成后，系统应能对 89 条产品资料来源生成带 `knowledge_type=products` 的结构 inventory、受控 `ProductGazetteer`、provider 前冻结的 `TopicPlan` 和稳定 `TopicIndex`；同一数据合同也必须能保留其他知识类型而不强行套产品词典。读者页面正文和完整导航仍由后续任务负责。

### 1.2 完成结果

操作者可以看到：

1. 每个声明来源的结构事实、指纹、匹配结果和失败原因。
2. 顶层知识类型及其来源证据；`products` 类型下的受控产品/模块词表及其版本、别名、来源证据和冲突记录。
3. 主题如何合并、拆分、降级的冻结计划。
4. 每个主题的稳定 key、知识类型、可选产品、模块、对象/意图、来源成员、当前路径、旧路径映射和状态。
5. 12–20 个能回到原始来源的 TopicPlan 样例。

## 2. 范围

### 2.1 包含

- 扩展现有 `identity.py`、`kb_structure.py`、`page_layout.py` 或等价职责模块。
- 在文件型 KB 约定内保存受控 `ProductGazetteer` 和 `TopicIndex`。
- 建立 89 条来源的结构 inventory，至少覆盖父子页、表格、FAQ、图片、双语、版本和噪声。
- 在 provider 调用前生成 `TopicPlan`。
- 先以 `knowledge_type` 决定顶层归属；`products` 类型再以产品、模块、对象/意图和稳定规范化 key 决定主题归属。
- 验证同产品同对象可合并、不同产品同名对象不合并、未知/冲突项降级。
- 验证 batch size、输入顺序和重复运行不改变主题成员、key、正式路径和旧路径映射。
- 定义增量 affected set，并保护集合外页面和路径字节不变。
- 检测已发布页面人工编辑造成的托管哈希冲突，不静默覆盖。
- 以 `--no-llm` 完成结构、索引、计划和失败边界验证。

### 2.2 不包含

- `Home.md`、产品页、模块页、完整分类导航的最终读者页面设计。
- Summary/Evidence/Provenance 正文生成、分页和语义质量验收。
- 89 条来源的完整正文编译或全量语义 TopicPlan。
- Task2 的命名、分类、摘要和 provider 内容生成。
- Task3 的完整读者发布、人工语义复核和 `released` 判定。
- Task1 不生成空知识类型、空产品、空模块或没有真实实例的目录；产品只是 `Products` 类型下的主轴，客户、研发、运营、原则和产品边界是平级知识类型，不再作为产品 facet 偷塞进产品轴。
- 数据库、图数据库、向量库、CAS、调度器、后台守护、AgentMemory、通用服务层或 10D ontology。
- 让模型直接写入或晋升正式产品词典。
- 删除旧主题页、旧分页或旧路径。

## 3. 操作者流程

1. 操作者提供固定来源清单、来源快照和 KB 输出目录。
2. 系统先读取 URI、标题、H1、父子路径、内容指纹，生成结构 inventory。
3. 系统校验来源缺失、清单变化、指纹变化、路径逃逸、软链接和结构声明；违反时整次运行明确失败。
4. 系统先记录 `knowledge_type` 的 canonical/alias/candidate/unknown 命中；只有进入 `products` 类型后，才按 canonical → alias → 父子路径 → H1/标题 → 模型候选匹配产品和模块，并保存命中、别名、候选、未知和冲突事实。
5. 系统根据知识类型、类型内主题轴和来源证据生成 `TopicPlan`；调用任何 provider 前冻结它。
6. 系统按稳定 key 合并主题：同一知识类型内同产品同对象可合并；不同知识类型或不同产品的同名对象分开。
7. 系统把未知或冲突项标为 `degraded`，保留来源和原因，但不生成正式知识类型、产品或模块导航入口。
8. 系统写入或更新 `TopicIndex`，记录当前路径和旧路径映射；已有托管页路径不能因日常更新改名。
9. 系统对 12–20 个样例和不同 batch/order/repeat 运行做确定性比较。
10. 增量运行只重算 affected set；集合外已发布正文和路径字节不变。
11. 发现人工编辑导致托管哈希不一致时停止覆盖，进入冲突并给出恢复所需事实。
12. Task1 输出结构、词表、计划、索引和测试证据；交付状态仍是 `not_released`。

## 4. 功能需求

### FR-01：结构 inventory 与知识类型

系统必须为参考输入中的 89 条来源各保存可追溯的 URI、内容指纹、`knowledge_type`、标题/H1、父子路径、结构特征和归一化的内部 link edges。结构特征至少包括父子页、表格、FAQ、图片、双语、版本和噪声；每条 link edge 必须有目标来源/托管路径、稳定排序和来源行定位。字段缺失或来源未进入清单必须能明确发现。当前原始语料是产品资料，运行时必须显式记录 `knowledge_type=products`，不能把这个输入假设成全库只有产品知识。

### FR-02：知识类型与受控 ProductGazetteer

系统必须先保存受控 `knowledge_type` 记录，至少有 canonical 名称、别名、owner、来源证据、版本、状态和冲突事实。registry 只能登记当前输入或受控结构声明有证据的类型；CompanyBrain 的目录事实不能自动变成运行时初始词表。`Products` 类型下再保存 ProductGazetteer 的正式产品/模块项，字段为 `kind`（`product` 或 `module`）、canonical 名称、别名、owner、来源证据、版本、匹配优先级和冲突事实。只有 `knowledge_type=products` 的来源才绑定 product/module；其他类型不允许被强行绑定产品。匹配优先级固定为 canonical → alias → 父子路径 → H1/标题 → 模型候选；同一优先级多个命中必须进入冲突/降级。模型只能提交候选，不能直接写入或晋升正式词表项。未知项和冲突项必须保留原因。

### FR-03：provider 前 TopicPlan

系统必须在任何 provider 调用前生成并冻结 TopicPlan。TopicPlan 至少表达主题身份、`knowledge_type`、来源成员、可选产品、模块、对象/意图、合并/拆分结果、计划版本和证据引用。`products` 类型的产品和模块来自受控 ProductGazetteer，且只能使用 `status=canonical` 的 entry；其他类型不读取 ProductGazetteer。object/intent 有类型内词表或来源证据时才使用，同时按“既有托管 object/intent → 来源 metadata object/intent → H1 → 标题 → 父子路径末级”的顺序取确定性 seed，再用同一 ASCII slug 规则归一化；无法得到唯一 seed 时降级。

### FR-04：主题归属规则

同一知识类型内的同一主题可以合并；`products` 类型内同一产品的同一对象/意图可以进入同一主题，不同产品的同名对象/意图不得合并。知识类型未知、`products` 类型的产品或模块未知、命中 entry 不是 `status=canonical`、多个同优先级命中、object/intent seed 不唯一或对象/意图冲突时，对应项必须降级，不进入正式导航。

### FR-05：稳定 TopicIndex

系统必须生成可重建的 TopicIndex，按“一个当前主题一条记录”表达 `topic_key`、`knowledge_type`、可选产品、模块、对象/意图、来源集合、当前发布路径、`old_path_mapping` 列表、状态、版本和失败原因。映射列表必须能表达多个旧主题合并到一个当前主题、一个旧主题拆到多个当前主题，以及对应证据和关系；它不能改变当前 `topic_key` 的唯一身份。`published` 项的适用轴字段不可为空；`degraded` 项仍需有稳定 key、来源成员、输入证据和可读原因，但不投影正式导航。

### FR-06：稳定身份和路径

正式主题 key、路径和旧路径映射不得依赖 batch size、输入顺序、来源 hash、`cluster-N`、`draft-N`、裸数字或不可读 hash/bare 片段。正式路径必须先包含 `<knowledge-type-slug>`；`products` 类型再按 `<product-slug>/<module-slug>/<object-intent-slug>.md` 构造，不能伪造 product segment。所有 segment 都来自冻结 TopicPlan，声明 root 必须来自 `kb.structure.md`。路径候选与其他 topic key 冲突时固定以 `PUBLISHED_PATH_COLLISION` 失败，禁止降级、输入序号或 hash 后缀。不得使用 `topic-<hash>`、`1.md`、`ae.md`、`ios.md` 作为正式主题主路径。旧 product-only 规则命名为 `topic_key_v1` 并保持不变；本次加入知识类型后正式使用新命名的 `topic_key_v2`，保留旧 key/旧路径映射，不能原地改写旧 v1。首次发布路径锁定，改名必须通过映射保留旧链接。本 Task1 实现只对有产品证据的 `products` 生成 published 路径；其他知识类型保留顶层类型字段但一律 `degraded`，未来建立类型内词表时再扩展其 published 轴。

### FR-07：批次、顺序和重复运行不变性

相同输入使用 `batch_size=1`、`batch_size=20`、不同输入顺序和重复运行时，TopicPlan、TopicIndex 的主题成员、稳定 key、正式路径和旧路径映射必须一致。batch size 只能改变传输边界，不能改变主题归属。

### FR-08：增量 affected set

首次导入或显式 rebuild 生成完整计划；普通增量只处理受影响来源、知识类型、主题、与受影响主题有直接关系的 related-link topics、类型/产品/模块索引投影和旧路径映射。Task1 只计算并输出 affected set，不写最终 Home；集合外已发布正文和路径字节必须保持不变。后续页面任务如改变 Home/索引统计，必须能引用 Task1 的 affected set。

### FR-09：人工编辑保护

正式托管页保存托管哈希。发现当前内容与托管哈希不一致时，系统必须停止覆盖、保留人工内容并记录冲突原因和受影响路径；不得用重新生成掩盖冲突。

### FR-10：单来源和降级边界

单来源只有同时满足资料完整、适用的知识类型/主题轴明确、结构有意义、必需证据存在、无事实冲突五项前提时，才可标为 `published`。`products` 类型必须额外满足产品/模块明确；其他类型不得用产品词典替代自己的主题轴。五项前提必须由 §5.4 的布尔字段和证据引用判断；单来源比例只进入报告监控，不作为全局硬门。未知/冲突项保留证据和失败原因，但不进入正式导航。

### FR-11：provider 隔离和离线验证

provider 失败、provider 改名或 provider batch 变化不得改变 TopicPlan、TopicIndex、稳定 key、成员归属或路径。正式离线验证只使用 `--no-llm` + Jaccard，不探测 embedding，不发出任何 LLM/网络请求；离线运行必须能完成结构 inventory、TopicIndex/TopicPlan 计划证据和失败边界检查。

### FR-12：样例和证据

系统必须提供 12–20 个稳定排序的 TopicPlan 样例，至少覆盖正常合并、未知归属和冲突降级，并能回到原始来源证据。样例不能被表述为 89 条来源的完整语义发布。

## 5. 数据状态

### 5.1 词表项

- `canonical`：正式受控项，可参与正式匹配。
- `source-canonical`：本 Task1 中由当前输入的明确目录、声明字段或稳定文件标题/文件名直接确认的 canonical 事实；它不读取外部词表，也不等同于未来产品维护者的业务语义扩展。
- `candidate`：候选建议，不能参与正式词表写入，除非后续明确批准。
- `conflict`：存在冲突，必须记录来源和原因。
- `unknown`：没有足够依据建立正式归属。

ProductGazetteer 的正式项必须有非空 `owner`；候选、冲突和未知项可以暂时没有正式 owner，但必须记录状态和原因。

### 5.2 TopicIndex 项

- `published`：满足 Task1 的知识类型和适用主题轴条件，可作为后续正文/导航的正式输入。
- `degraded`：保留稳定 key、来源和失败事实，但不进入正式知识类型、产品或模块导航。

### 5.3 运行和发布

- 来源处理：成功、重复来源、受影响、未受影响、失败。
- 人工编辑：托管哈希一致可继续；不一致进入冲突。
- Task1 交付状态：`not_released`。`written`、质量通过和 WorkflowHub 阶段通过都不等于 `released`。

### 5.4 单来源五项布尔判定

单来源是否可标为 `published` 由 inventory/plan 中固定的布尔字段判断，不靠 reviewer 主观印象：

- `资料完整=true`：URI、指纹、标题/H1、父子路径、必需结构字段和来源快照均存在，且没有输入校验失败。
- `topic_axis_explicit=true`：`knowledge_type` 已命中 canonical 类型；`products` 类型还要求 product 和 module 都命中 `status=canonical` 的对应词表 entry，且没有同级冲突；其他类型使用其已声明的类型内主题轴。
- `meaningful_structure=true`：至少有非空 H1/标题、一个父子路径定位或一个非噪声结构特征；仅有噪声不能通过。
- `required_evidence=true`：至少有一个来源行定位的 evidence ref，且能回到固定快照和内容指纹。
- `fact_conflict_free=true`：无重复来源冲突、知识类型/产品/模块冲突、object/intent 冲突和人工托管哈希冲突。

五项必须全部为 `true` 才允许单来源 `published`；任一为 `false` 就保留证据并进入 `degraded`。12–20 个样例 fixture 至少包含一个五项全 true 的单来源和一个各缺一项的失败样例；单来源比例仍只作报告监控。

## 6. 接口和数据边界

### 6.1 输入

- 固定来源清单、来源快照、来源 URI、标题/H1、父子路径和内容指纹。
- 当前 KB 的 `kb.structure.md`、已声明托管目录和已有 TopicIndex/旧路径映射。
- `kb.structure.md` 受控区段中的明确版本 `knowledge_type` registry；`Products` 类型还需要 ProductGazetteer。

### 6.2 输出

- 89 条来源结构 inventory。
- `kb.structure.md` 内版本化 ProductGazetteer 受控区段。
- provider 前冻结的 TopicPlan。
- TopicIndex、稳定路径和旧路径映射。
- 12–20 个样例及其来源证据。
- 批次不变性、增量范围和人工哈希冲突证据。

### 6.3 边界

- TopicPlan 是主题身份的权威；provider 不是主题身份的权威。
- `kb.structure.md` 是知识类型 registry 和 ProductGazetteer 正式存储、版本声明的唯一权威；运行时不得另写一份同等权威的词表。
- `topic_key_v2` 由 canonical 的知识类型和适用的类型内主题轴组成；当前 `products` 类型使用产品、模块、对象/意图语义 slug tuple，别名不能直接产生另一套 key。key 规范化不依赖 batch、输入顺序、来源 hash 或 provider。
- `topic_key_v2` 使用固定的 ASCII slug 规范化；`kb.structure.md` 声明的 reader 根、保留目录和保留词构成保留集合，冲突时按固定 `x-` 规则转义。任何规范化规则升级都产生新 key 版本，并用旧 key/路径映射兼容，不原地改写旧 key。
- 原始来源快照和旧 formal 页面不删除；TopicIndex 是可重建投影。
- Task1 不新增远程接口，不把 `_digest` 审计文件变成读者入口。
- `indexes/sources.md` 的当前代码/测试合同继续有效；旧 `_digest/source-index.md` 文档冲突不在本阶段擅自改写。

### 6.4 已收敛的技术合同

- TopicIndex 是当前主题的单一可重建投影；`old_path_mapping` 是记录内列表，不另设同等权威的迁移表。
- affected set 包括来源、知识类型、主题、related-link topics、类型/产品/模块索引投影和旧路径映射；Task1 不写 Home、正文或最终读者导航。Home 统计属于后续页面任务的下游影响，不属于 Task1 写入物。
- 托管页使用 `managed_content_hash` 做冲突检测；冲突写入运行审计/结果并停止覆盖，不提供默认 override 或人工审批队列。
- inventory 和样例使用现有 JSON/JSONL 习惯，按 canonical source URI、topic key 和来源定位稳定排序；证据必须能回到来源相对路径和行定位。
- 迁移保留旧 `digest_topic_id`、旧页面和旧路径；新增语义 `topic_key`，Task1 不删除旧兼容投影。
- 正式验收使用 `--no-llm` + Jaccard，不探测 embedding；provider 可以消费冻结计划，但不是 Task1 必需运行链路，也不能改变身份、成员、路径或状态。
- inventory 只冻结 PRD 要求的结构字段和知识类型边界，不把正文归一化、页面类型识别或人工语义质量提前纳入 Task1。

### 6.5 最小持久化 schema

以下是 Task1 的最小字段合同；实现可以增加审计字段，但不能删掉必需字段或改变状态含义。

`KnowledgeTypeRegistry` 受控区段：

- `schema_version`：固定版本字符串。
- `entries[]`：按 canonical slug 稳定排序；每项有 `canonical`、`aliases[]`、`owner`、`source_refs[]`、`status` 和 `reason`。
- 初始类型只覆盖当前输入或 `kb.structure.md` 受控声明有直接来源证据的类型；本次 89 条原始语料因此只生成 `products`。CompanyBrain 的 `customers`、`engineering`、`operations`、`principles`、`product-boundaries` 只作为信息架构参考，不得被硬编码成初始 canonical 或伪装成当前已有语料；未来有真实来源时再登记对应类型。缺乏来源证据的类型不能生成正式入口。

`ProductGazetteer` 受控区段（仅适用于 `knowledge_type=products`）：

- `schema_version`：固定版本字符串。
- `entries[]`：按 canonical slug 稳定排序。
- 受控区段必须有固定的全局 `match_order`：`canonical`、`alias`、`parent_path`、`h1_title`、`candidate`；每个 entry 必须有 `kind`、`canonical`、`aliases[]`、`object_intents[]`、`owner`、`source_refs[]`、`status` 和 `reason`。`kind` 只能是 `product` 或 `module`。匹配结果可以记录 `matched_by_tier`，但它只是事实字段，不能覆盖全局顺序。正式 `canonical` entry 的 `owner`、`source_refs[]` 非空；`object_intents[]` 字段必须存在，未知时为空数组并由 `status/reason` 说明。
- `status` 只能是 `canonical`、`candidate`、`conflict`、`unknown`；模型输出只能写入 `candidate`。

`TopicIndex`：

- `schema_version`：固定版本字符串。
- `topics[]`：一个当前主题一条记录，按 `topic_key` 稳定排序。
- 每条记录必须有 `topic_key`、`knowledge_type`、`product`、`module`、`object_intent`、`source_members[]`、`published_path`、`old_path_mapping[]`、`status`、`topic_plan_version` 和 `reason`；非产品类型的 `product` 为 JSON `null`；同时保留可用的 `digest_topic_id` 作为旧托管更新身份。
- `status` 只能是 `published` 或 `degraded`。`published` 的知识类型、适用主题轴和路径非空；`degraded` 的正式轴字段和路径统一使用 JSON `null`，禁止字段缺省和空字符串；它必须有稳定 key、来源、原因和证据。
- `old_path_mapping[]` 的每项必须有 `old_path`、`relation` 和 `evidence_refs[]`。`relation` 只能是 `rename`、`merge`、`split` 或 `unmappable`；同一旧路径可在多个当前主题记录中以 `split` 出现，多个旧路径可在一个当前主题记录中以 `merge` 出现。
- `source_members[]`、`old_path_mapping[]`、`evidence_refs[]` 都必须稳定排序；映射证据必须能回到来源、快照或迁移记录。

`TopicPlan`：

- `schema_version`：固定版本字符串。
- `topics[]`：按 `topic_key` 稳定排序；每条必须有 `topic_key`、`knowledge_type`、`source_members[]`、`product`、`module`、`object_intent`、`merge_mode`、`topic_plan_version` 和 `evidence_refs[]`。非产品类型的 `product` 为 JSON `null`；`product`、`module`、`object_intent` 在 `merge_mode=degraded` 时统一使用 JSON `null`，禁止字段缺省和空字符串；其余模式按适用类型轴填写。
- `merge_mode` 只能是 `single`、`merge`、`split` 或 `degraded`；`source_members[]` 必须稳定排序，且每个来源只能出现在一个当前计划主题中。
- TopicPlan 是 provider 输入前的冻结事实；provider 输出不得回写其中的身份、成员或归属字段。

### 6.6 topic_key_v2 规范化和 degraded key

旧 product-only key 仍按 `topic_key_v1` 解释并只通过旧映射兼容；当前 `published` key 使用 `topic_key_v2` 的 `v2/<knowledge-type-slug>/<subject-slug>/<module-slug>/<object-intent-slug>` 形式。`products` 类型的 subject 是 ProductGazetteer canonical product；其他类型的 subject 必须来自已确认的类型内词表或来源证据，不能借用 ProductGazetteer。object-intent slug 来自 FR-03 的确定性 seed，不进入 ProductGazetteer。每个 slug 按以下顺序处理：

1. 对 knowledge type/subject/module 取对应类型 registry 或 ProductGazetteer 的 canonical ASCII slug；别名先映射到 canonical，不能直接产生另一套 key。对 object/intent 取确定性 seed 的 ASCII slug。
2. 做 Unicode NFKC、ASCII 小写化、首尾空白裁剪；连续空白和标点统一成一个 `-`，连续 `-` 合并，首尾 `-` 去除。
3. 只允许 `a-z`、`0-9` 和 `-`。知识类型、subject、module canonical 或 object/intent seed 没有可审计 ASCII slug 时不能猜测，转为 `degraded`。
4. 保留集合来源固定为 `kb.structure.md` 声明的 reader 根/目录，加上 `Home`、`indexes`、`_digest`、`_archive`、`_queues`、`pending`；冲突的 slug 在同一位置前加 `x-`，转义后仍冲突则 `degraded`。
5. `topic_key_v1` 规则冻结后不得原地改变；本次知识类型前缀是 `topic_key_v2` 的新合同。后续规则变更继续生成更高版本，旧 key、旧路径和映射继续保留。

例子：`Go Insight` → `go-insight`；别名 `AE` 指向 canonical `Adobe Experience` 时只产生 canonical 的 key；`index` → `x-index`。

未知或冲突主题使用 `degraded/<evidence-slug>` key。`evidence-slug` 按父子路径、H1/标题、来源 URI path 的固定顺序取第一个可生成 ASCII slug 的证据，并附上所有参与来源的稳定排序证据引用；不能使用 hash、输入序号或随机值。若多个 degraded 主题仍产生相同 key，直接记录 `DEGRADED_KEY_COLLISION` 并失败，不添加数字后缀猜测。

### 6.7 affected set 算法

affected set 的输入只有固定来源清单、内容指纹、结构 inventory 的内部 link edges、当前 TopicPlan/TopicIndex、ProductGazetteer 版本和旧路径映射。related-link topics 只来自 inventory 中已归一化的内部 link edge 或已有 TopicIndex 的显式关系，不由模型语义猜测。

- 来源新增、删除、URI/指纹/结构字段变化：加入该来源、其当前主题和直接 related-link topics。
- TopicPlan 成员、知识类型、产品、模块、对象/意图或 key 变化：加入旧主题、新主题、两侧直接 related-link topics、相关类型/产品/模块投影和旧路径映射。
- 知识类型 registry 或 ProductGazetteer 的 canonical/alias/owner/status 变化：加入命中该 entry 的主题、其 related-link topics 和对应类型/产品/模块投影；未命中的主题不进入集合。
- 旧路径映射变化：加入映射两侧当前主题和映射投影；不重编译无关系的主题正文。
- 没有上述变化：affected set 为空，不能因为输入枚举顺序变化而扩大集合。

Task1 只输出这个集合及触发事实，不写 Home；后续页面任务可据此更新 Home/索引统计。

### 6.8 人工编辑冲突合同

冲突写入现有 `_digest/runs/<run_id>.json` 的 `conflicts[]` 审计角色，并在运行结果返回同一记录。每项至少包含：`code`（固定为 `MANAGED_CONTENT_CONFLICT`）、`run_id`、`topic_key`、可用的 `digest_topic_id`、`path`、`managed_content_hash`、`actual_content_hash`、`action`（固定为 `preserve_and_stop`）和 `recovery`（默认 `reconcile_then_rerun`）。

发现冲突后默认保留人工文件，停止该主题及其受影响写回。允许操作者显式提交逐页 override manifest 后继续，但不是默认行为，也不是人工审批队列：manifest 必须包含 `topic_key`、`path`、原/现 hash、操作者说明、override 原因和唯一 `override_ref`；运行结果必须追加 `MANAGED_CONTENT_OVERRIDE` 记录并绑定 manifest hash，`action` 为 `replace_after_explicit_override`。没有 manifest 时不得覆盖；override 不能批量放开整次运行，也不能静默更新 managed hash。

### 6.9 published_path 构造

对 `published` TopicPlan，先从 `kb.structure.md` 读取唯一声明的 topic root，再按 `knowledge-type-slug/subject-slug/module-slug/object-intent-slug.md` 依次拼接；非产品类型不填 product segment。每个 segment 来自同一冻结计划和 §6.6 规范化；不使用标题随机选项、输入序号、source hash 或 provider 输出。候选路径已被其他不同 `topic_key` 占用时固定记录 `PUBLISHED_PATH_COLLISION` 并使本次 Task1 写前校验失败，不加不可读后缀。首次锁定后的路径只允许通过 `old_path_mapping` 迁移。

### 6.10 当前产物的持久化位置

以下路径是当前 KB 下的唯一可重建审计投影，不是读者入口；`kb.structure.md` 必须允许现有 `_digest` 审计根，否则写前失败：

- `_digest/source-inventory.jsonl`：89 条来源的当前结构 inventory，按 source URI 稳定排序。
- `_digest/topic-plan.json`：当前冻结 TopicPlan，按 topic key 稳定排序；每次运行的 run record 保存其内容指纹。
- `_digest/topic-index.json`：当前 TopicIndex 投影，按 topic key 稳定排序。
- `_digest/runs/<run_id>.json`：运行结果、affected set、冲突记录、上述三个产物的内容指纹和恢复事实。

这些文件不进入 Home、分类或来源读者导航；旧 `_digest/topic-index.json` 若存在，按 schema/version 和旧 `digest_topic_id` 规则迁移，不能静默删除。

## 7. 验收标准

### AC-01：全量结构清单

给定参考 89 条来源，结构 inventory 包含 89 条且每条都能通过 URI、指纹和来源定位回溯；父子页、表格、FAQ、图片、双语、版本、噪声和归一化内部 link edges 字段存在且排序稳定。每条 link edge 有目标和来源行定位。

### AC-02：词表受控

知识类型 registry 和 `Products` 下的 ProductGazetteer 都有版本、owner、来源证据和稳定排序；当前原始语料明确给出的产品根与稳定页面 capability seed 以 source-canonical 状态落盘，模型输出只能落在 candidate 区。任何模型直接写入或自动晋升正式词表项，验收失败。

### AC-03：TopicPlan 先于 provider

执行记录能证明 TopicPlan 在 provider 调用前已冻结；provider 不可用时仍能生成同一身份/成员计划或明确失败，不得改用 provider 输出决定归属。

### AC-04：合并与降级

样例至少覆盖正常合并、未知归属和冲突降级。同一知识类型内按适用规则合并；`Products` 内同产品同对象合并，不同产品同名对象分开。只有 canonical 的类型 entry，以及 `Products` 下 canonical 的 ProductGazetteer entry，才能填充对应 `published` 轴字段；candidate/conflict/unknown 或 candidate tier 命中都必须 `degraded` 且不进正式导航。未知/冲突项使用 `degraded/<evidence-slug>` 稳定 key，有来源、原因和证据；无法生成唯一可读 degraded key 时明确失败。

### AC-05：TopicIndex schema 边界

每个 `published` 项的知识类型、适用 subject/module/object-intent、topic key 和路径非空；`Products` 项的产品/模块必须来自 `status=canonical` entry，非产品项不能伪造 product；每个 `degraded` 项有稳定 key、来源成员、输入证据和原因，正式轴字段和路径统一使用 JSON `null`，不能用空字符串或缺省字段伪装未知；TopicPlan 与 TopicIndex 使用同一规则。TopicIndex 必须符合 §6.5，旧路径映射必须携带关系和证据。

### AC-06：路径和旧映射

正式路径按 §6.9 从声明 root、知识类型和冻结 TopicPlan 的类型内 slug 构造，可读、稳定，不使用 `topic-<hash>`、裸数字、裸文件名、输入顺序或不可读 hash/bare 片段。保留词按固定 `x-` 规则转义；规范化规则升级使用新 key 版本；路径碰撞固定以 `PUBLISHED_PATH_COLLISION` 失败，不降级。已有路径被保留，并能通过旧路径映射到当前主题或明确记录不可迁移原因。

### AC-07：批次/顺序/重复不变

`batch_size=1`、`batch_size=20`、输入顺序变化和重复运行得到相同主题成员、topic key、正式路径和旧路径映射；同一 topic key 在一次计划中只对应一个主题。

### AC-08：增量范围

按 §6.7 的触发矩阵计算 affected set：来源/指纹/结构变化会带入当前主题和直接 related-link topics，词表变化会带入命中主题和相关投影，映射变化会带入映射两侧主题。集合外已发布正文和路径字节不变。Task1 不写 Home；后续 Home/索引统计或链接变化必须能回到 Task1 输出的 affected set 解释。无输入变化时集合为空。

### AC-09：人工编辑冲突

托管哈希不一致时运行必须 fail-closed：保留人工内容、记录冲突路径和恢复事实、停止覆盖；没有逐页、可审计 override manifest 时不得覆盖。显式 override 必须绑定原/现 hash、原因、操作者说明和 manifest hash，不能批量放开或静默更新 managed hash；不得用主题 `degraded` 替代覆盖保护。

### AC-10：单来源门槛

单来源仅在 §5.4 五项布尔前提同时满足时标为 `published`；fixture 能逐项判断五项 true/false；单来源比例只出现在监控报告，不触发全局失败。

### AC-11：离线和 provider 隔离

`--no-llm` + Jaccard 运行网络调用数为 0，仍能产出结构、索引、计划和失败边界证据；不得探测 embedding。provider 失败、更换或 batch 变化不改变正式身份和计划。

### AC-12：Task1 交付边界

验收只证明结构、词表、TopicPlan、TopicIndex、固定审计产物、稳定性和失败保护；不把 Home、正文、最终导航、人工语义质量或 `released` 作为 Task1 已完成事实。

### AC-13：当前产物落盘

`_digest/source-inventory.jsonl`、`_digest/topic-plan.json`、`_digest/topic-index.json` 和 `_digest/runs/<run_id>.json` 按 §6.10 生成，稳定排序、可重建、互相有内容指纹引用，且不进入 reader package。

## 8. 失败边界

以下情况必须明确失败或降级，不能返回成功：

- 来源缺失、清单变化、URI/指纹变化、路径逃逸、软链接或结构声明不合法：整次运行失败。
- 知识类型无匹配、`Products` 下产品/模块无匹配、命中非 canonical entry、同优先级冲突或对象/意图冲突：对应项 `degraded`，不生成正式入口。
- topic key、路径或旧映射为空、不可读或随输入顺序变化：验收失败。
- 发生 `PUBLISHED_PATH_COLLISION` 或 `DEGRADED_KEY_COLLISION`：写前整次 Task1 运行失败，不降级、不添加数字/hash 后缀。
- 一个来源进入多个主题、一个 topic key 对应多个主题、不同知识类型同名对象被合并或不同产品同名对象被合并：验收失败。
- 受影响集合计算错误导致范围外字节变化：验收失败。
- 人工编辑哈希冲突被静默覆盖：验收失败。
- provider 输出反向改变主题身份、模型写入正式词表或 `--no-llm` 发出请求：验收失败。

## 9. 风险和假设

- 当前仓库没有真实 89 条生产语料 fixture；本规格要求固定 fixture/证据格式，但不能宣称当前已有全量语义验收。
- 从来源 hash 主题 ID 迁移到语义 topic key 可能产生一对多旧路径映射；必须先保留旧页和映射。
- 知识类型过窄会把客户/研发/运营资料误塞进产品轴，类型过宽会污染正式导航；候选不自动落地是可接受的稳定性取舍。
- `indexes/sources.md` 与 `AGENTS.md` 的 `_digest/source-index.md` 表述冲突；本规格记录兼容边界，不在 Task1 隐式修改历史文档合同。
- 已有代码的 `digest_topic_id` 是托管更新身份；Task1 语义 topic key 与旧身份的迁移字段必须明确，不能静默替换。

## 9.1 首轮 review finding 处置

- `F-572138af612b`：接受问题本身，已修复 reserved word、`topic_key_v1` 不可变和 v2 兼容升级规则；原 provider 锚点无效，不作为证据来源。
- `F-5c2abc3ee372`：接受问题本身，已把 related-link topics 纳入 affected set，并明确 Home 只作为后续任务下游影响；原 provider 锚点无效，不作为证据来源。
- `F-81b7eec41ef2`：接受问题本身，已补齐 TopicIndex 和 `old_path_mapping` 的字段、类型和关系合同；原 provider 锚点无效，不作为证据来源。
- `F-94d58fe6ce1b`：接受问题本身，已将 `owner` 纳入 ProductGazetteer 和 AC-02；原 provider 锚点无效，不作为证据来源。
- `F-b0d2ab058e6a`：接受并修复 AC-09，人工编辑冲突现在只允许 fail-closed，不允许用 degraded 替代。
- `F-9f5d372fc7fa`：接受并补充空目录和 facet 轴的延期边界。
- `F-f14d6cb27254`：接受并修正规格顶部状态。

## 9.2 第三轮 review finding 处置

- `F-225414adda39`：接受问题本身，已把内部 link edges 加入 FR-01、AC-01 和 inventory 输入合同。
- `F-3ce773029ceb`：接受问题本身，已补充 §6.9 的 published_path 构造、声明 root 和碰撞失败规则。
- `F-7ee7e0dee69e`：接受 direct finding，恢复非默认、逐页、可审计 override；默认仍 fail-closed，未引入人工审批队列。
- `F-b7fbcd282605`：接受问题本身，已给 ProductGazetteer entry 增加 `kind=product|module`，并规定分开绑定。
- `F-cee2959ceedf`：接受问题本身，TopicPlan 的 degraded 轴字段与 TopicIndex 统一使用 JSON `null`，禁止字段缺省。
- `F-cf7752e3f9d5`：接受问题本身，已把 object/intent 的确定性 seed 规则从 ProductGazetteer 中分离并写入 FR-03、§6.6。

## 9.3 最新 review 建议处置

- `F-41fb4f4b64a9`：接受并修订 §5.4/AC-10，五项单来源前提现在有固定布尔字段、证据引用和失败样例要求。
- `F-610b50ae7c26`：接受并统一 TopicPlan/TopicIndex 的 degraded 缺省表示为 JSON `null`，禁止字段缺省和空字符串。
- `F-7cbd67e9ee11`：接受并统一 `PUBLISHED_PATH_COLLISION` 为写前整次运行失败。
- `F-80b06aa7f082`：接受并恢复 ProductGazetteer entry 的 `object_intents[]` 最小字段；它保留对象证据，不改变 object/intent seed 的确定性提取顺序。
- `F-83cfdb4827fc`：接受并增加 canonical-only 发布门；candidate/conflict/unknown 不得填充 published 轴字段。
- `F-93c335cecc50`、`F-a3b9aad4ab0a`：接受并更新顶部状态，当前可进入 build-plan，不再追 review pass。
- `F-d16417266879`：接受并固定三个当前产物及 run record 的持久化路径于 §6.10。

## 9.4 Scope revision review 建议处置

- `pi/k3` 和 `antigravity/flash` 的有效建议：初始 registry 不应硬编码 CompanyBrain 的非产品类型。已接受；改为只从当前输入或受控结构声明登记有证据的类型，本次真实 89 条语料只登记 `products`。
- 有效建议：`topic_key_v1` 与 `v2/...` 前缀命名混用。已接受；旧 product-only 合同保留为 `topic_key_v1`，带 `knowledge_type` 的当前合同明确命名为 `topic_key_v2`。
- 有效建议：非 Products 的类型内轴尚未建立，却保留了通用 published 语气。已接受；明确本 Task1 非 Products 一律走 `degraded`，不生成伪造的 published 类型内路径。
- `antigravity/flash` 建议删除逐页 override。评估后不采纳：现有决定允许“人工确认后继续”的边界延期，当前条款不是默认覆盖、不是批量审批队列，而是逐页、带原/现 hash 和原因的显式恢复动作；默认仍 `fail-closed`。如后续决定完全不允许人工恢复，再作为新的 scope revision 删除该能力。

## 10. 当前材料歧义门

以下不是新增需求，而是 `decision-log.md` §11 明确延期、且会影响数据接口或验收的技术合同。它们已在本规格中锁定或明确延期；review 建议作为质量输入保留，不作为继续推进的 pass 门。

| 编号 | 来源 | 影响 | 当前状态 |
|---|---|---|---|
| AMB-01 | decision-log §11.1 | ProductGazetteer 的正式存储接口、重建和审计 | 已锁定：嵌入 `kb.structure.md` 受控区段 |
| AMB-02 | §11.2 | `topic_key_v1` 规范化和兼容升级 | 已直接规格化：§6.6 的固定步骤、保留词、转义、degraded key 和 v2 映射 |
| AMB-03 | §11.3 | 匹配优先级和同级冲突 | 已锁定：canonical → alias → 父子路径 → H1/标题 → 候选；同级多命中降级 |
| AMB-04 | §11.4 | TopicIndex 精确 schema、状态和映射 | 已直接规格化：一条当前主题记录 + §6.5 schema + `old_path_mapping` 列表；状态为 `published/degraded` |
| AMB-05 | §11.5 | affected set 的精确边界 | 已直接规格化：§6.7 触发矩阵、related-link 来源、级联规则；Task1 不写 Home |
| AMB-06 | §11.6 | 人工编辑冲突落盘和恢复动作 | 已直接规格化：§6.8 冲突记录 schema、错误码、恢复动作和 fail-closed 边界 |
| AMB-07 | §11.7 | fixture、排序和证据格式 | 已直接规格化：JSON/JSONL、canonical URI/topic key 稳定排序、来源路径+行定位 |
| AMB-08 | §11.8 | source index 文档同步 | 已延期，不改变本 Task1 产品范围 |
| AMB-09 | §11.9 | source-hash topic_id 到语义 key 的迁移 | 已直接规格化：保留旧 `digest_topic_id`、旧页和旧映射，新增语义 key，不删除兼容投影 |
| AMB-10 | §11.10 | 离线/provider 证据范围 | 已锁定：Task1 正式验收走 `--no-llm` + Jaccard，不探测 embedding；provider 不改变计划和身份 |
| AMB-11 | §11.11 | 归一化深度和 inventory 字段合同 | 已直接规格化：只冻结 PRD 最低结构字段，不扩正文/页面类型验收 |

### 10.1 处理结果

- 产品方向已由 `make-decision` 和用户确认锁定；技术合同已依据 PRD、ADR、现有代码和“最简单可追溯”原则直接收敛。
- 当前没有需要用户继续选择的材料歧义；如果后续发现会改变产品范围、页面范围或发布承诺的冲突，才重新向用户提问。
- 异源 review 已提供真实建议，全部已评估并在本规格中修订或记录；按用户规则不再循环追 `pass`，现在可以进入 `build-plan`。

### 10.2 Scope revision 处理结果

- 已接受用户对 CompanyBrain 信息架构的纠正：顶层是 `knowledge_type`，`Products` 只是其中一类。
- 已把 `knowledge_type` 加入 inventory、TopicPlan、TopicIndex、key/path、affected set 和 AC；ProductGazetteer 明确收缩为 `Products` 类型内的词表。
- 本次 89 条原始语料按产品资料边界记录为 `knowledge_type=products`；CompanyBrain 只提供已核验的目录事实，不作为运行时词表或页面上游。
- 当前旧实现、旧计划和旧 AC 证据不能直接证明这个修正版规格；必须回到 `build-plan` 重拆影响任务，再回到 `build-code` 实现和复验。

### 10.3 新增材料歧义门

- `knowledge_type` 的正式存储段与 ProductGazetteer 共用 `kb.structure.md`：两个明确受控区段，版本和来源分别记录；不另建平行权威词表。
- 非 `Products` 类型的类型内 subject/module 词表：影响非产品资料何时能进入 `published`；当前本 Task1 只冻结顶层类型和安全降级边界，不凭空建立全公司本体。
- 旧 product-only `topic_key_v1` 到带知识类型的新 `topic_key_v2`：影响迁移和路径；当前已选择新版本 key，并保留旧 key/旧路径映射。

## 11. 后续交接

- 本修正版规格连同 decision-log 和 scope revision 事实交给 `build-plan`，不是直接交给实现；build-plan 必须先拆出知识类型字段、迁移和非产品降级边界。
- review 通过或有效 finding 处置后，连同 `decision-log.md`、规格审查结果和当前风险交给 `build-plan`。
- 现有 `plan.md`、`tasks.md` 是旧 product-only 计划，不能直接作为新规格的实施授权；build-plan 必须修订同一份材料，不创建替代任务。
- 代码、提交、合并、推送和正式发布不属于本次 scope revision 动作。
