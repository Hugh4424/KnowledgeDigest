# 功能规格：Reader 知识质量编译器优化

> 本规格把已确认的方向翻译成可验收的产品合同。当前只验收 89 条样本；样本不是未来知识原材料上限。实现细节、代码文件、命令和任务拆分留给后续阶段。

## 速读卡（30 秒）

- 目标：把原始资料编译成比 CompanyBrain 更好用的 Reader 知识，而不是把原文换个文件名或照抄目录。
- 当前范围：89 条来源全量编译；覆盖页面、主题、关系、文件名、分类、正文、导航和来源追溯。
- Reader 规则：先识别产品、模块、对象、任务和关系，再决定标题与路径；无法证明归属的内容进入 Audit，不默认塞进“通用”。
- 新模块/对象规则：必须有明确名称、至少两条互相支持的事实或关系、且不与现有知识冲突；否则只能是 `pending`、`conflict` 或 `degraded`。
- 质量结论：机器完成全量覆盖和同题对照；不要求逐页或逐题人工审核。只有证据完整、关键任务不出错、三项质量比较达到严格规则时，才可称为优于 CompanyBrain。
- 当前不做：把 89 条当成生产规模门槛、永久人工审核、后台调度、数据库/向量库、UI 改版和与本目标无关的流程门禁。

## 1. 问题与紧迫性

### 1.1 当前问题

KnowledgeDigest 目前可能出现“来源已进入、页面能打开、机器字段齐全”，但读者仍然找不到正确主题，文件名像输入简称，很多内容落在没有信息量的“通用”，正文像原文拼接，关系和边界没有整理出来。这样的结果不能满足原始目标。

CompanyBrain 的有效做法不是目录本身，而是先做知识编辑：把来源事实整理成产品、模块、对象、任务、规则和关系，再使用读者能理解的名称、分类和入口。KnowledgeDigest 必须吸收这套编辑原则，同时保留自动化、可追溯和可重复运行的优势。

### 1.2 紧迫性

当前 89 条结果已经显示出结构和命名质量问题。若继续沿用当前编译逻辑，未来扩大到数万条资料只会把错误分类、低质量标题和不可读正文放大，不能靠多跑几次解决。

## 2. 背景、目标与范围

### 2.1 用户和用户结果

- **知识使用者**：从入口按产品、模块和任务找到主题，读完即可知道怎么做、适用边界是什么、依据来自哪里。
- **知识维护者**：看到每条来源的去向、未进入 Reader 的原因、关系冲突和质量异常，不用逐页人工检查才能发现大问题。
- **评测者**：用同一组问题、同一套口径和两个独立 Reader 结果比较，能看到路径、答案、边界和来源证据。

### 2.2 原始需求映射

| 原始需求 | 本规格落实 | 交接阶段 |
| --- | --- | --- |
| 89 条全量先跑通 | 全量快照、去向、失败可见 | build-plan |
| 不照抄 CompanyBrain 结构 | 语义识别后独立分类 | build-code |
| 文件名必须像知识标题 | 标题由对象、动作、范围生成 | build-code |
| 新知识不能进默认通用 | 新模块/对象证据阈值与待定态 | build-code |
| 内容质量要优于 CompanyBrain | 同题三轴机器比较 | verify-code |

### 2.3 当前范围

本任务必须覆盖 89 条来源及其全部可见结果：

- 来源快照、去重、唯一身份、Claim、Evidence、Provenance 和运行状态。
- 产品、模块、对象、任务、能力、规则、限制、关系和主题的识别。
- 主题合并、主题拆分、跨来源关系、冲突和重复来源处理。
- 可读标题、主题路径、分类导航、Home、相关主题和来源入口。
- Summary、答案、规则/边界、相关主题和可回查来源组成的正文。
- Reader 与 Audit 分离、失败不伪装、旧结果不被错误覆盖。
- 89 条全量机器报告，以及与 CompanyBrain 的同题批量对照报告。

89 条是当前验收样本，不是未来生产数据规模承诺；本任务不以数万条的吞吐、成本、并发或长期恢复能力作为通过条件。

### 2.4 成功结果

成功不是“生成更多页面”，而是同时满足：

1. 读者能从入口找到正确主题，标题和分类能表达主题含义。
2. 主题正文是整理后的知识，能说明答案、适用条件、限制和相关关系，而不是原文堆放。
3. 每条结论都能回到来源证据；不确定、冲突或证据不足的内容不会伪装成正式 Reader 知识。
4. 在固定比较条件下，KnowledgeDigest 至少一项严格优于 CompanyBrain，其余比较项不变差，且没有关键任务错误或负向误导。

## 3. 用户场景与状态覆盖

### SCN-001：89 条来源全量编译

发布者启动一次固定输入的全量编译。系统为每条来源给出明确去向：进入一个正式主题、作为重复来源关联到 canonical 主题，或进入 Audit 并记录原因。任何来源都不能无声丢失。

验证：检查全量清单、去向记录和运行汇总。通过条件：89 条全部可追踪；失败条件：缺来源、输入漂移无提示、来源只有临时编号或无去向。

### SCN-002：读者从入口找到答案

读者从 Home 进入产品、模块、对象或任务主题，先看到清楚标题和 Summary，再看到答案、规则/边界、相关主题和来源入口。页面不要求读者先理解内部聚类编号或机器字段。

验证：机器走查导航并读取主题页面。通过条件：入口可达、标题可读、正文有答案和边界、来源可回查；失败条件：孤立页、断链、临时标题、原文堆放或占位正文。

### SCN-003：新模块或对象的归类

来源表达了一个 CompanyBrain 中没有的新模块或对象。系统只有在名称明确、至少两条事实/关系互相支持、且与现有知识不冲突时，才把它作为正式 Reader 节点和分类依据；证据不足、互相矛盾或名称不确定时进入 Audit，并标记 `pending`、`conflict` 或 `degraded`。

验证：使用新增模块、证据不足、互相冲突和已有模块四类样本检查节点状态。通过条件：正式节点满足三项条件；失败条件：仅凭一个词或一个来源创建正式节点，或把未确认内容默认放入“通用”。

### SCN-004：批量机器质量对照

评测者查看一次批量报告，不逐页、不逐题手工确认。报告把 KnowledgeDigest 和 CompanyBrain 放在相同问题、相同入口和相同口径下，分别给出路径、答案要点、边界/来源和机器异常。证据不齐时结论为 `undecidable`，不猜测优劣。

验证：检查报告覆盖、字段和比较条件。通过条件：89 条机器检查全覆盖，比较报告可按题回查；失败条件：只抽一页、只比较文件名、缺证据仍给出“更好”，或把机器结果写成 `human_reviewed`。

### SCN-005：局部失败、核心失败和重跑

某条来源读取失败、无法分类、正文为空、关系冲突或来源锚点缺失时，问题内容留在 Audit 并写明原因。当前 89 条全量包不区分核心/非核心：任一来源或任一全量硬门失败，候选包都保持 `not_released`；未受影响的候选页可以隔离保存，但不能成为当前 Reader 入口。修复后重跑必须产生新的运行记录，不能覆盖旧结果或沿用变化后的来源身份。

验证：注入局部失败、全量硬门失败和输入变化后重跑。通过条件：失败边界明确、旧结果不被覆盖、原因可回放，且没有核心/非核心豁免；失败条件：静默丢失、假发布、错误复用旧身份或失败后仍标为正式可用。

### SCN-006：取消、权限失败和并发竞态

运行被取消、没有读取权限、目标已被其他运行更新或输入在运行中变化时，系统停止本次正式发布，留下可解释状态和运行证据。用户能区分“正在运行”“已失败”“候选未发布”和“正式可读”。

验证：模拟取消、权限失败、目标冲突和输入变化。通过条件：状态准确、失败原因可见、旧正式结果保持不变；失败条件：把非终态当成功，或将半成品暴露为 Reader 入口。

### 3.1 状态覆盖

| 维度 | 必须覆盖的状态 | 读者或维护者结果 |
| --- | --- | --- |
| 运行 | loading、completed、failed、cancelled | 运行状态不等于发布成功 |
| 来源 | valid、duplicate、failed、degraded | 每条来源有去向和原因 |
| 语义节点 | existing、new_candidate、pending、conflict、failed | 只有 existing 或满足准入的 new_candidate 可进入正式导航 |
| 页面 | published、degraded | 只有 published 页进入 Reader |
| 包 | candidate、not_released、released | 失败不覆盖旧结果 |
| 环境 | empty、permission、race | 边界明确且可重跑 |

## 4. 产品事实与假设（PFACT）

- **PFACT-001**：`verified`；当前验收输入是 89 条真实来源；它是样本，不是未来生产规模上限。来源：原始需求、decision-log D-017；影响：FR-SOURCE-001、AC-SOURCE-001。
- **PFACT-002**：`verified`；CompanyBrain 的主要优势来自知识编辑和整理：可读标题、语义分类、主题合并、关系和边界，不是简单复制目录。来源：CompanyBrain 与 Knowledge 规则调查、decision-log D-017～D-019；影响：FR-SEMANTIC-001～004。
- **PFACT-003**：`verified`；当前低质量问题覆盖结构、命名、正文、关系、导航和溯源，不能只修一个示例页或一种字段。来源：89 条审计与原始需求；影响：FR-SEMANTIC-001、FR-READER-001～004。
- **PFACT-004**：`verified`；Reader 面向知识使用者，Audit 面向追溯和失败调查；两者必须分开。来源：原始方案与 decision-log；影响：FR-READER-004、FR-AUDIT-001。
- **PFACT-005**：`verified`；新模块/对象必须有明确名称、至少两条相互支持的事实或关系、且不与现有知识冲突。来源：用户确认的 make-decision 方向；影响：FR-SEMANTIC-003、FR-STATE-002。
- **PFACT-006**：`verified`；正式质量比较使用路径、答案完整度、边界/来源清晰度三项；至少一项严格更好、其余不差，且无关键错误，才允许声称优于 CompanyBrain。来源：decision-log D-019；影响：FR-QUALITY-002、AC-QUALITY-004。
- **PFACT-007**：`unknown`；89 条全量产物是否最终整体优于 CompanyBrain，必须由正式机器运行和同题证据确认。owner：verify-code；影响：FR-QUALITY-002；未确认前状态只能是 `candidate` 或 `not_released`。

## 5. 功能需求

- **FR-SOURCE-001**：来源全量和稳定身份；每条来源必须有稳定身份、内容指纹、来源位置和本次运行去向。

### FR-SOURCE-001：来源全量和稳定身份

每条来源必须有稳定身份、内容指纹、来源位置和本次运行去向。来源集合、内容或身份发生变化时，运行必须显式失败或创建新的输入版本，不能悄悄沿用旧计划。

来源：PFACT-001。场景：SCN-001、SCN-005、SCN-006。验收：AC-SOURCE-001、AC-FAIL-002。

### FR-SOURCE-002：Claim、Evidence 和唯一归属

每个正式 Claim 必须有来源锚点和验证状态，并且只能绑定一个 canonical 主题。重复来源可以继承 canonical 主题；冲突或多重归属只能进入 Audit，不能同时作为多个正式答案。

来源：PFACT-004。场景：SCN-001、SCN-005。验收：AC-SOURCE-002、AC-AUDIT-001。

### FR-SEMANTIC-001：语义对象识别

系统必须从来源识别产品/领域、模块、对象、场景、任务、能力、规则、限制和关系，并把识别结果与支持它的事实关联。场景状态必须是 `supported`、`not_applicable` 或 `pending`：只有来源确实表达场景时才要求稳定 `scenario_id`、用户意图、前置条件、成功边界、负向边界和来源证据；不适用必须有原因，证据不足必须 `pending`，禁止编造场景字段。输入顺序、文件名前缀或临时聚类编号不能直接决定正式标题和分类。

来源：PFACT-002、PFACT-003。场景：SCN-001、SCN-002、SCN-003。验收：AC-COMPILER-001、AC-COMPILER-002。

### FR-SEMANTIC-002：标题和分类编译

正式标题必须表达主题对象、动作或用途和必要范围，不能只是来源简称、随机缩写或内部编号。分类优先使用已识别的产品、模块和任务；无法安全归类时保留明确的待定状态，不得把“通用”当作默认垃圾桶。

来源：PFACT-002、PFACT-003。场景：SCN-002、SCN-003。验收：AC-COMPILER-002、AC-READER-001。

### FR-SEMANTIC-003：新模块/对象准入

只有同时满足“名称明确、至少两条互相支持的事实或关系、与现有知识不冲突”时，模块或对象才可进入正式 Reader 分类。两条支持事实必须来自不同 `fragment_locator`，去重键为 `source_snapshot_id + fragment_locator + normalized_claim_text + relation_id`；两条事实的规范化主体必须指向同一候选，且不能包含相反断言或冲突关系。它们可以来自同一来源的不同片段，也可以来自不同来源；重复片段不算第二条支持。既有节点基线绑定 `semantic-baseline-v1` 和配置版本，名称、职责或关系端点/类型冲突都算冲突，不自动选边。候选、支持事实、冲突事实和最终决定都必须保留来源 URI、内容指纹和 `fragment_locator`。任一条件不满足，节点只能进入 `pending` 或 `conflict`，对应页面如已生成则为 `degraded`；不能把 `degraded` 当作语义节点状态，也不能默认归到“通用”。

来源：PFACT-005。场景：SCN-003。验收：AC-COMPILER-003、AC-STATE-002。

### FR-SEMANTIC-004：主题合并、关系和冲突

同一主题的多条来源必须合并完整证据；不同主题之间的依赖、包含、替代、前置、限制和关联关系应可被 Reader 使用。相互矛盾的事实不能被静默拼接为一个答案，必须保留冲突状态和来源范围。

来源：PFACT-002、PFACT-003。场景：SCN-001、SCN-005。验收：AC-COMPILER-004、AC-AUDIT-002。

### FR-SEMANTIC-005：配置驱动而非 89 条专用映射

语义编译必须读取版本化领域配置和输入事实，不能用 89 条来源路径、文件名或固定输出路径做专用映射。机器必须用一组不增加真实原始资料的配置变体夹具替换领域名称、节点名称和输入路径，仍能产生稳定身份、正式/待定/冲突状态、Reader/Audit lineage 和失败报告；本任务不以第 90 条真实资料或规模性能作为门槛。

来源：PFACT-001、PFACT-002。场景：SCN-001、SCN-003。验收：AC-COMPILER-005。

### FR-READER-001：可读标题和稳定路径

Reader 必须提供从候选 `Home(package_id, run_id)` 到产品、模块、对象/任务和主题的稳定入口；当前正式 `Home` 只有后续 `released` 转换才能更新。正式页面不得使用输入顺序、`cluster-N`、`draft-N` 或无法理解的来源缩写作为读者标题；既有稳定主题身份不能因普通更新随意改名。

来源：PFACT-002、PFACT-003。场景：SCN-002。验收：AC-READER-001、AC-READER-002。

### FR-READER-002：知识正文

主题页必须按版本化 `page-type-registry-v1` 选择页面类型；类型专属的必需 section、关系和正文 oracle 由案例矩阵固定，不能用一个“通用”模板覆盖所有页面。适用的主题页先给 Summary 和可执行答案，再给适用条件、规则/边界、关系和简短来源入口；索引、参考、场景、排障等页面类型按自己的必需 section 验收。正文必须是整理后的知识；不能以原文整段、原文片段简单拼接、机器字段、空摘要或仅有链接代替答案。分页时不得重复或互相矛盾地表达同一 Claim。

来源：PFACT-002、PFACT-003。场景：SCN-002、SCN-005。验收：AC-READER-003。

### FR-READER-003：相关主题和来源入口

读者能从当前主题进入相关主题，并能通过简短来源入口回查依据。来源入口只能指向脱敏的 Reader source projection；相关主题必须有实际语义关系。Audit、原始快照、provider 响应、内部指纹和失败记录只能由维护者在 Audit 查看，不能出现在 Reader 正文、来源入口或默认导航；不能用无关链接填充导航。

来源：PFACT-004。场景：SCN-002。验收：AC-READER-004。

### FR-READER-004：Reader 与 Audit 分离

Reader 只展示可读、可追溯的正式知识；Audit 保存原始快照、Claim/Evidence、语义判断、冲突、失败、运行和质量异常。待定、冲突和失败内容不能出现在默认 Reader 导航中，但维护者必须能在 Audit 找到它。

来源：PFACT-004、PFACT-005。场景：SCN-003、SCN-005。验收：AC-READER-004、AC-AUDIT-001。

### FR-AUDIT-001：全量覆盖报告

机器报告必须覆盖 89 条来源的清单归属、语义去向、页面可达性、标题可读性、正文非空/非占位、关系、来源回查、Reader/Audit 分离和失败原因。报告必须能按来源、主题和运行回查证据。

来源：PFACT-001、PFACT-004。场景：SCN-001、SCN-004。验收：AC-AUDIT-001、AC-QUALITY-001。

### FR-AUDIT-002：异常和根因记录

每个主要质量差距必须固定记录 `symptom → evidence_ref → first_failing_stage → change_ref → rerun_result`，并让每个引用绑定 source/page/run/config identity。没有证据的判断标为 `unconfirmed`；缺少首个失败阶段、修正引用或复跑结果时不能标为已修复，失败原因不能只写“处理失败”这类无法行动的描述。

来源：PFACT-003。场景：SCN-004、SCN-005。验收：AC-AUDIT-002、AC-STATE-001。

### FR-AUDIT-003：可重复和安全发布

每次运行保留输入快照、版本、状态、输出关系和失败记录。运行必须带 `run_id`、`input_manifest_generation`、`config_generation` 和 `base_reader_generation`。相同来源 manifest、来源内容指纹和配置版本的重跑必须使用同一幂等身份，不得重复创建正式主题、Claim、关系或归档副本。候选包先在独立 run/package 命名空间中完整构建，再以一次原子切换更新候选命名空间；只有运行拥有目标、输入与配置代际仍匹配、Reader 基线代际未变化、运行已完成且全量硬门通过时才允许切换。当前正式 Reader 入口只有后续 `released` 转换才能更新；本任务的 `published` 页面只表示候选命名空间内可读。取消、竞态、权限失败或任一全量硬门失败时，切换必须被拒绝，旧 Reader 入口和 hash 不变。

来源：PFACT-004、PFACT-007。场景：SCN-005、SCN-006。验收：AC-FAIL-001、AC-FAIL-002。

### FR-QUALITY-001：机器结果真实标记

89 条全量检查全部由机器完成，并明确标记为机器证据。系统不得生成 `human_reviewed`，不得把机器通过当成人工确认，也不得要求用户逐页或逐题检查才能完成本任务。

来源：PFACT-001、用户已确认方向。场景：SCN-004。验收：AC-QUALITY-001、AC-QUALITY-003。

### FR-QUALITY-002：同题三轴比较

系统必须使用固定的 Reader 案例集 `reader-case-matrix-89-input-v1`、协议 `reader-compare-v1`、评估器 `reader-evaluator-v1` 和当前只读 CompanyBrain 基线 `companybrain-full-20260819-current-v2`，在相同问题、各自 Home 起点和相同比较口径下，对 KnowledgeDigest 与 CompanyBrain 计算三项结果。该基线完整性范围包含 1,406 个非系统常规文件；Reader 页面对照范围是其中 716 个正式 Markdown 页，`_gbrain` 与 `_config` 只进入完整性清单。案例集覆盖 89 条输入映射出的去重 canonical 主题/任务，不把重复来源重复计入读者质量；每个案例由来源事实、主题任务和固定 Claim/边界检查组成，不需要人工生成或确认。旧的 GoInsight pilot baseline 和旧的 `companybrain-full-20260818-v1` 只作为历史证据，不得混入当前聚合。

1. **路径**：从各自 Home 开始；打开 Home 记 0 hop；每次 Reader 内部 Markdown link 点击记 1 hop；首次打开包含案例所需 Claim 的页为 first hit。`first_hit_correct` 只有命中案例目标 canonical 主题页时为 1，否则为 0；路径按已冻结的 `path_score = (first_hit_correct, -hop_count)` 字典序比较。`first_hit_kind` 仍作为证据记录，不另造评分口径。
2. **答案完整度**：固定 Claim 要点的通过数 / 要点总数；要点缺失、含糊、说反或无证据均为 0，关键要点错误直接失败。
3. **边界/来源清晰度**：固定边界检查和来源可回查检查的通过数 / 检查总数；来源 URI、内容指纹或片段定位缺失直接失败。

CompanyBrain 匹配必须使用冻结的 `comparison_key = normalize(product_or_domain + module + object_or_scenario + task + page_type)`，只接受基线 manifest 中唯一的 key→entry_path 映射；无匹配是 `not_applicable`，多匹配或 key/入口/hash 不一致是 `undecidable`，不能由执行者挑一个“看起来最像”的页面。入口链路和目标页均来自冻结 manifest，不能从当前目录临时搜索。

每条案例记录 `case_id`、两边 Home、首次命中页、命中类型、跳转数、Claim 结果、边界结果、来源锚点、`N/A` 原因、协议/题集/评估器身份、配置 hash、session、包顺序、隔离模式、运行时间和失败原因。Reader 质量分母固定为去重案例数 `M`，不能通过删除案例改变；来源覆盖仍单独使用 89 行分母。`not_applicable` 只表示 CompanyBrain 确实没有该主题：该案例三轴差值记 0 但仍计入 `M`，不制造优势；双方都 `not_applicable` 也记 0。KnowledgeDigest 没有对应主题而 CompanyBrain 有内容记为 `issue`，不能排除。`unknown`、`evidence_missing`、条件不一致或关键案例缺失证据才触发 `undecidable/not_released`；关键案例的 `not_applicable` 也触发 `undecidable/not_released`，非关键案例的 `not_applicable` 只能保持中性，不能贡献优势。对完整 `M` 行聚合：路径每例按 tuple 得出 +1/0/-1，路径轴为 `M` 行结果之和；答案和边界轴按固定 `M` 分母的平均差值计算，`not_applicable` 行贡献 0。严格正值表示更好，0 表示不差，负值表示退化；至少一轴严格为正、其余不为负、没有关键错误和负向误导时，才可标为“优于 CompanyBrain”，否则为 `candidate` 或 `not_released`。

聚合前必须先通过逐案例零错误门：全部 `M` 个 canonical 案例的必需 Claim、边界、关系和来源都为 `covered`，没有 `missing`、`contradictory`、无依据改写或负向误导；任一案例失败都直接 `issue/not_released`，不能用其他案例的平均优势抵消。

来源：PFACT-006、PFACT-007。场景：SCN-004。验收：AC-QUALITY-002、AC-QUALITY-003、AC-QUALITY-004。

### FR-QUALITY-003：差距闭环

质量报告必须把“结构/命名/分类/正文/关系/导航/溯源”的差距分别呈现，并能关联到具体来源、主题、页面或状态。报告不能只用单页样例或一个字段代表 89 条整体质量。

来源：PFACT-003。场景：SCN-004、SCN-005。验收：AC-QUALITY-005。

## 6. 模块划分

| 模块 | 用户可见职责 | 失败时结果 |
| --- | --- | --- |
| 来源与证据 | 快照、身份、Claim、Evidence、Provenance | Audit 记录原因 |
| 语义编译 | 识别对象、关系、标题、分类、主题 | pending/conflict |
| Reader 发布 | 正文、路径、导航、相关主题 | 不进默认入口 |
| Audit 与质量 | 全量报告、对照、根因、运行状态 | 不给虚假结论 |

模块是产品职责边界，不规定下游的代码组织方式。

## 7. 关键实体

- **SourceSnapshot**：一条来源在一次运行中的稳定身份、来源 URI、内容指纹、`fragment_locator`、位置和快照状态。
- **SemanticNode**：产品、模块、对象、任务或能力等可识别知识节点，带稳定 ID、名称、证据数、关系和状态。
- **Scenario**：用户意图、角色、前置条件、成功步骤、负向边界和结果的稳定场景节点，带 `scenario_id`、证据和相关主题关系。
- **Claim**：可被读者使用的事实或规则，带稳定 `claim_id`、Claim 文本、Evidence、验证状态和唯一 `target_path`。
- **Relation**：主题、对象、模块、任务之间的语义关系，带稳定 `relation_id`、两端稳定 ID、关系类型、支持来源和冲突状态。
- **ReaderPage**：面向读者的主题页，带稳定 `page_id`/`digest_topic_id`、标题、路径、页面类型、正文、相关主题和来源入口。
- **AuditRecord**：维护者查看的来源、判断、失败、冲突、运行和质量记录。
- **QualityComparison**：同题比较中的问题、两边结果、三项指标、证据、异常和最终状态。
- **PageTypeRegistry**：版本化页面类型、类型专属 section、必需关系和正文 oracle 的集合；缺少类型映射不能回退到“通用”。

所有正式实体还必须带 `lineage_step`，记录识别、归类、合并、编译或发布阶段；机器报告保存来源覆盖率、Claim 断链数、页面断链数和关系断链数。

## 8. 数据和生命周期

### 8.1 来源与语义生命周期

`source_snapshot → valid | duplicate | degraded | failed`

`valid | duplicate → identified → existing | new_candidate | pending | conflict | failed`

`existing | new_candidate → claim_candidate → reader_candidate`

只有完成唯一归属、完整溯源和冲突检查的 `claim_candidate` 才能进入 `reader_candidate`；`pending`、`conflict`、`failed` 不得转入 Claim、Reader 或 published，只能进入 Audit 终态。页面单独从 `reader_candidate → published | degraded` 转换，`degraded` 不进默认导航。

重复来源在 `identified` 后指向 canonical 来源，不复制正式 Claim。来源 `degraded` 表示快照可读但完整性、格式或溯源不满足要求；它只能进入 Audit，不进入 Claim。节点 `pending`、`conflict` 和 `failed` 只能进入 Audit；页面 `degraded` 不进入任何默认 Reader 导航，只在候选状态索引和 Audit 中可见。

### 8.2 页面与发布生命周期

页面生命周期为 `reader_candidate → published | degraded`；交付包生命周期为 `candidate → not_released | released`。

`published` 只表示页面已经通过本任务的内容、导航和追溯要求；`released` 需要后续正式发布任务确认。页面即使 published，只要包仍未完成全量和质量比较，包仍是 `candidate` 或 `not_released`。本任务任何核心质量失败、证据缺失、输入竞态或运行非终态都必须保持 `not_released`，旧正式结果不变。

### 8.2.1 失败转移和可见性矩阵

| 触发条件 | 最终状态 | Reader 可见面 | Audit 必须保留 | 重试规则 |
| --- | --- | --- | --- | --- |
| 全量编译完成但质量门未完成 | 包 `candidate` | 只在独立候选命名空间可见 | 候选页、运行和矩阵 | 继续当前候选或新运行 |
| 输入为空或 89 条清单为空 | 运行 `completed` 但包 `not_released` | 不生成候选 Reader | empty reason、输入代际和运行记录 | 补充新 manifest 后重跑 |
| 来源读取/权限失败 | 来源 `failed`，包 `not_released` | 受影响页不进导航 | 快照、原因、run/source 标识 | 同指纹可新运行重试 |
| 证据不足或关系冲突 | 节点 `pending/conflict`，页 `degraded` | 不进默认导航 | 候选、支持/冲突事实和定位 | 修复证据后重跑 |
| 取消、输入竞态或目标冲突 | 运行 `cancelled/failed`，包 `not_released` | 不生成新入口 | 触发原因、旧入口和恢复身份 | 输入变化须新 manifest |
| 核心质量失败或不可判定 | 包 `not_released` | 旧正式入口不变 | 逐案例结果和失败原因 | 修复缺陷后新运行 |
| 同 manifest、指纹、配置重跑 | 保持同一幂等身份 | 只允许一次原子切换 | 重跑记录和复用关系 | 不重复创建主题/Claim/关系 |

任何 `published` 页面只有在候选包自己的原子切换成功后才可更新候选 Reader；当前正式 Reader 入口只有后续 `released` 转换才能更新。任何失败或非终态都只能留在候选/Audit，旧正式结果保持不变。

### 8.3 质量比较生命周期

`machine_pending → machine_complete → comparable | undecidable | issue`

机器比较不产生人工结论。`undecidable` 表示证据或条件不足，不是通过；`issue` 表示已发现不满足目标的问题。当前不建立 `human_reviewed` 流程。

## 9. 兼容性预留

- 保留现有来源可追溯、稳定主题身份、分页上限、增量安全写回和失败不伪装的底线。
- 已有正式主题的稳定入口默认保持；确需重命名时必须留下旧路径映射和原因，不能让链接静默失效。
- 分类由配置和语义证据共同决定，不能把 89 条的具体目录写死成未来所有数据的规则。
- 未来数万条资料需要另行验证吞吐、成本、批次、恢复和冲突处理；本规格只要求当前 89 条结果可正确验收。
- CompanyBrain 只作为同题基线，不作为 KnowledgeDigest 的固定目录模板或内容来源。

## 10. 明确不做与默认必须成立

### 明确不做

- 不复制 CompanyBrain 的目录、文件数量或文件名；只吸收其知识编辑原则。
- 不把 89 条硬编码成永久生产输入，不以未来数万条的性能作为本任务门槛。
- 不逐页人工审核、不逐题人工审核、不建立永久人工审核队列，不生成 `human_reviewed`。
- 不把无法确认的模块、对象或关系默认放进“通用”。
- 不做只改文件名、只改目录、只加链接、只加机器字段或只压页数的表面优化。
- 不引入数据库、向量数据库、调度器、后台守护、AgentMemory 或无关的 UI 改版。
- 不用原文 fallback 掩盖语义编译失败；失败必须进入 Audit 并说明原因。

### 10.2 默认必须成立

- 输入来源、CompanyBrain 基线和比较问题在一次比较中固定；条件不一致即 `undecidable`。
- 读者必须先看到可读标题和答案；机器字段、异常和原文快照属于 Audit。
- 正式 Claim 只有一个 canonical 归属；冲突不能静默合并。
- 证据不足、运行非终态或核心质量失败不能标为正式可用。
- “优于 CompanyBrain”必须由证据推导，不能由页面数量、文件名变化或机器分数单独推导。

## 11. 验收标准

### 当前 89 条机器判定矩阵

本节所有验收都消费两个绑定当前来源 manifest 的机器材料，不用“抽几页看起来不错”代替全量判定。`source-coverage-89-v1` 是严格 89 行的一对一来源覆盖索引，每行只对应一条来源，负责清单、快照、去向和失败状态。`reader-case-matrix-89-input-v1` 是去重后的 canonical Reader 主题/任务案例矩阵，固定记录案例数量 `M`、案例 hash 和 `source_to_case_map`；多来源合并主题只生成一个案例，重复来源不增加读者质量权重，但必须在 89 行来源覆盖索引中可回查。Reader 质量聚合固定使用这 `M` 行，来源质量聚合固定使用 89 行，两个分母不能混用。

每个 Reader 案例行固定记录：来源身份和输入指纹、`canonical_case_id`、`criticality`（`critical` 或 `standard`）、预期产品/领域、模块、对象、场景、任务、页面类型、类型专属必需 section、标题所需对象/动作/范围、必需 Claim、必需关系端点、必需边界、来源定位和预期状态。`critical` 的确定规则是：主产品/模块/场景入口、包含限制/不支持边界的案例、负向边界案例或影响安全/正确操作的案例；其余才是 `standard`。每行必须显式填写，不能使用“关键案例”自由解释。矩阵的预期值只能来自原始来源事实、已有稳定领域配置或明确的跨来源支持关系，不能来自生成后的标题、路径或正文。

矩阵同时包含三类可重复夹具：已有模块/对象的正常归类、新模块/对象的三项准入、证据不足或冲突的待定/冲突归类。每个夹具都规定输入事实、期望状态和失败原因；所有夹具由机器运行，不需要人工确认。下游只能把矩阵物化为可执行数据，不能改变本节的期望状态、证据阈值或失败语义。

当前输入材料身份已经冻结为：`input_manifest_id=confluence-raw-89-20260818-v1`、89 条 Markdown 来源、manifest SHA-256 `e1842f683ee3b92fbe532d781a3cd374563ac94e4db3240272238481e33765bf`；CompanyBrain 当前只读基线冻结为：`companybrain-full-20260819-current-v2`、1,406 个非系统文件、完整树 hash `dbfd60230790c7774e4a680397074859809dd9a0e5bc93af4c0923f51c27ea22`，其中 716 个 Markdown 页作为 Reader 对照范围。每个 manifest 的逐文件路径、字节数和内容 SHA-256 属于验收材料；任一 hash、数量或来源集合变化，当前结果必须是 `undecidable/not_released`，不能继续沿用旧矩阵。

`source-coverage-89-v1` 必须恰好 89 行；`reader-case-matrix-89-input-v1` 必须有固定的 `M` 行、`source_to_case_map`、逐案例预期值和 hash。每个 Reader 行绑定一个或多个 source snapshot、一个 `canonical_case_id`、期望语义节点/页面类型、必需 Claim/边界清单和来源锚点。`reader-evaluator-v1` 的配置必须把本规格的路径、Claim、边界、来源、N/A、unknown 和聚合公式固化，并输出 `evaluator_config_hash`。缺少逐行矩阵、CompanyBrain manifest、evaluator 配置 hash、source_to_case_map 或任一逐案例预期值时，比较只允许返回 `undecidable`，不得生成“优于”结论。

每个案例的不可变 oracle 结构为：`case_id`、source snapshot ID、`canonical_case_id`、`criticality`、期望产品/模块/对象/场景/任务、页面类型、类型专属 section、标题信号、Claim 列表（`claim_id + normalized_claim_text + fragment_locator + content_hash`）、边界列表（包括负向边界）、关系端点、CompanyBrain 匹配状态/入口/目标页、`not_applicable` 原因和失败阈值。Claim/边界列表必须在读取原始来源和 CompanyBrain 基线后、编译 KnowledgeDigest 前冻结；不能从 KnowledgeDigest 生成结果反推。每条 expected Claim 必须映射到最终页面的 section 和 `section_lineage`，机器结果只能是 `covered`、`missing` 或 `contradictory`；每条 required boundary 和 relation 也必须有同样映射。Reader evaluator 的定性门也固定：每种页面类型必须满足其 registry section、Claim/关系和来源 oracle；适用的主题页必须有非空 Summary、答案、规则/边界、相关主题和来源入口；Summary/答案不能等于单个原文片段，也不能只是多个原文片段的无编辑拼接，正文不能只有 Evidence 或链接；标题必须同时有对象、动作/用途、必要范围信号；缺任何必需项、出现 `missing/contradictory` 或 fallback 即失败。这样“可读标题”“不是原文堆放”“页面类型正确”和“答案没有改错”都有机器判定，不依赖人工印象。

- [ ] **AC-001**：89 条来源无声丢失（`AC-SOURCE-001` 的 WorkflowHub 兼容索引）

运行完成后可以看到 89 条来源各自对应正式主题、重复关联或带原因的 Audit 记录。

验证：对照 89 条固定输入与来源去向、重复关系和 Audit 记录。

通过条件：每条来源都有唯一身份、快照指纹和明确去向；失败条件：缺来源、重复计数、无去向或输入漂移未被发现。

证据类型：`test`、来源清单和 Audit 报告。

### AC-SOURCE-002：Claim 唯一归属和证据完整

打开 Claim 记录可以看到唯一 canonical 主题、来源锚点和验证状态。

验证：检查正式 Claim、来源锚点、验证状态和 canonical 主题关系。

通过条件：每个正式 Claim 只有一个 canonical 归属，并完整带有 `source_snapshot_id`、来源 URI、内容指纹、`fragment_locator`、`claim_id`、唯一 `target_path`、`page_id`/`digest_topic_id`、关系端点/`relation_id`（适用时）和 `lineage_step`，且可回到证据；失败条件：任一字段缺失、多重正式归属、无证据、无验证状态或冲突被静默合并。

证据类型：`test`、Claim/Evidence 报告。

### AC-COMPILER-001：语义识别覆盖

全量报告中可以按来源看到产品/领域、模块、对象、场景、任务、能力、规则、限制和关系的识别结果。

验证：对 89 条结果逐行检查产品/领域、模块、对象、场景、任务、能力、规则、限制和关系的证据绑定；每行必须有场景状态 `supported/not_applicable/pending`，`supported` 才要求 `scenario_id`、用户意图、前置条件、成功/负向边界和来源定位，`not_applicable` 必须有原因。

通过条件：89 条均有机器可判定的语义覆盖行，适用场景字段和边界有证据，不适用项有原因，证据不足项为 `pending`，识别结果可回查，不能由输入顺序或临时编号单独决定；失败条件：缺覆盖行、适用场景缺失/矛盾、不适用无原因、编造场景、只有来源简称/编号，或关系没有证据。

证据类型：`test`、机器覆盖报告。

### AC-COMPILER-002：标题和分类可读

Reader 索引中可以看到可解释的标题和分类，无法归类项显示明确状态。

验证：用 89 条覆盖矩阵检查标题字段、标题来源事实、路径分类节点和“通用”归因字段。

通过条件：每个正式标题都满足“对象/动作或用途/必要范围”三段式字段检查，分类有证据，无法归类项有明确状态；失败条件：标题仍是输入简称、临时编号或不加判断地归入“通用”。

证据类型：`test`、Reader 结构报告。

### AC-COMPILER-003：新模块/对象准入

新模块/对象样本会分别显示正式节点或待定、冲突、降级状态。

验证：用新增模块/对象、证据不足和冲突三类固定机器夹具，按 `source_snapshot_id + fragment_locator + normalized_claim_text + relation_id` 去重，检查两条不同片段、同一候选主体、支持关系、既有节点基线、冲突结果及每条候选/支持/冲突/决定的来源定位。

通过条件：三项准入条件和来源定位同时满足才进正式 Reader；失败条件：单一证据即建正式节点、冲突仍发布、来源定位缺失或证据不足默认进“通用”。

证据类型：`test`、语义节点 Audit。

### AC-COMPILER-004：主题、关系和冲突整理

多来源主题会显示合并后的证据，冲突主题会显示冲突状态和来源范围。

验证：检查多来源主题是否合并、跨主题关系是否可用、冲突是否留痕。

通过条件：相关来源共同支撑一个一致主题，关系可回查，冲突有状态和范围；失败条件：重复页面、关系缺失或矛盾正文被拼成一个答案。

证据类型：`test`、主题/关系报告。

### AC-COMPILER-005：配置变体不依赖 89 条专用映射

替换领域配置、节点名称和输入路径后，编译链仍能生成稳定身份、正确状态、Reader/Audit lineage 和失败报告。

验证：运行配置变体夹具，并检查输出中没有按 89 条来源路径或文件名直接映射结果的专用规则。

通过条件：变体能完成同一语义生命周期和失败语义，且稳定 ID、证据和状态字段完整；失败条件：只有当前 89 条名称可用、配置替换后静默丢失或必须修改代码/固定路径才能运行。

证据类型：`test`、配置变体报告。

### AC-READER-001：入口和路径可达

从候选 `Home(package_id, run_id)` 出发可以走到每个候选主题及其相关主题，同时当前正式 Home 保持旧版本。

验证：从候选 `Home(package_id, run_id)` 机器遍历产品、模块、对象/任务、主题和相关主题链接，并确认当前正式 Home 未被候选包改写。

通过条件：正式主题可达且无孤立页；失败条件：断链、死链、仅能从内部索引找到或路径无语义。

证据类型：`test`、Reader 导航报告。

### AC-READER-002：标题不是输入污染

页面标题和路径能表达知识主题，并且不暴露来源简称或临时编号。

验证：检查候选页面标题、路径和稳定身份与来源文件名、临时编号的差异，并对照 `base_reader_generation` 的旧 `page_id`、旧路径和链接映射。

通过条件：标题是知识标题，稳定身份可持续更新；旧路径保留，或有可回查的替代映射和原因；失败条件：来源简称、随机编号或批次顺序暴露给读者，或旧入口既无保留也无映射。

证据类型：`test`、页面索引报告。

### AC-READER-003：正文是可用知识

打开候选页面可以看到案例矩阵指定的页面类型和类型专属 section；适用的主题页先读到 Summary 和答案，再读到边界、相关主题和来源入口。

验证：按 `page-type-registry-v1` 检查每个 canonical case 的类型映射、类型专属 section、Claim/关系 lineage，并检查适用主题页的 Summary、答案、规则/边界、相关主题和来源入口；同时检测空摘要、占位语、单片段正文和无编辑拼接。

通过条件：每个页面类型满足自己的 section/Claim/关系 oracle，适用主题页有可读答案和边界，分页不重复冲突；失败条件：类型缺失、回退“通用”模板、只剩 Evidence、只剩链接、正文为空、原文拼接或机器字段替代正文。

证据类型：`test`、Reader 内容报告。

### AC-READER-004：Reader 与 Audit 分离

读者页面不显示内部审计字段，但维护者能从来源入口找到 Audit 证据。

验证：对照 Reader 页面、默认导航和 Audit 记录的字段与链接。

通过条件：Reader 不暴露内部审计字段但可回查来源；失败条件：失败原文进入默认导航、Audit 字段直接当正文或来源无法回查。

证据类型：`test`、Reader/Audit 对照报告。

### AC-STATE-001：失败和非终态不伪装

失败或取消运行后，默认 Reader 入口保持不可发布，候选页只在自己的 run/package 命名空间可见，旧正式结果仍然存在。

验证：模拟空输入/空 89 条清单、读取失败、权限失败、取消、输入竞态、目标并发更新和任一 89 条全量硬门失败；同时检查 `run_id`、输入/配置代际、旧 Reader 代际和原子提交证据。

通过条件：空输入直接留下 `empty` 原因并保持包 `not_released`；任一代际不匹配、运行取消或全量硬门未通过都拒绝切换，候选不进入当前正式 Reader，旧 Reader 入口和 hash 不变；相同来源指纹和配置版本重跑不重复创建正式主题/Claim/关系，满足条件的运行最多一次原子提交；失败条件：半成品进入 Reader、候选覆盖正式入口、旧结果被覆盖、重复写入、竞态提交或非终态被标成功。

证据类型：`test`、运行状态和失败记录。

### AC-STATE-002：待定和冲突不进默认分类

证据不足或冲突的新节点能在 Audit 中找到，但不会出现在默认“通用”入口。

验证：模拟证据不足、名称不明和语义冲突的新模块/对象。

通过条件：节点进入 `pending`、`conflict` 或 `degraded` 并保留证据；失败条件：直接发布或默认塞入“通用”。

证据类型：`test`、语义 Audit。

### AC-AUDIT-001：89 条机器覆盖报告

全量报告可以按来源查看去向、标题、分类、正文、关系、导航、回查和状态。

验证：检查报告是否逐条覆盖来源去向、标题、分类、正文、关系、导航、回查和状态。

通过条件：全量可按来源和主题回查；失败条件：只抽一页、只看文件结构或漏掉失败项。

证据类型：`evidence`、全量质量报告。

### AC-AUDIT-002：主要差距有根因证据

每类主要差距的报告行都能链接到现象、证据、根因、修正和复核状态。

验证：检查结构、命名、分类、正文、关系、导航和溯源差距的记录。

通过条件：每个主要差距都有 `symptom`、`evidence_ref`、`first_failing_stage`、`change_ref`、`rerun_result`，并绑定 source/page/run/config identity；缺任一项只能标 `unconfirmed/not_released`；失败条件：只给分数、只给单页例子或无证据猜根因。

证据类型：`evidence`、根因报告。

### AC-QUALITY-001：没有人工审核伪装

运行报告能区分机器结果与不存在的人工判断，不会出现无事实依据的人工状态。

验证：检查全量报告、状态和交付说明中的评审身份。

通过条件：机器结果明确标记为机器结果，不出现无事实依据的 `human_reviewed`；失败条件：把机器通过写成人工通过或要求逐页人工才能闭环。

证据类型：`test`、运行报告。

### AC-QUALITY-002：三项比较条件一致

`reader-case-matrix-89-input-v1` 的每个 canonical 机器案例在两边 Reader 中都从各自 Home 开始，并产生相同字段的三项指标和证据。

验证：检查案例集、`reader-compare-v1`、`reader-evaluator-v1`、CompanyBrain manifest、Home 起点、hop 计数、隔离模式和逐案例字段是否一致。

通过条件：题目/案例、顺序、入口、评价口径、配置 hash、运行隔离和来源基线一致；失败条件：一边使用额外上下文、案例变更、条件不一致或证据缺失仍计算优势。

证据类型：`test`、比较报告。

### AC-QUALITY-003：机器比较可回查

比较报告的每一行都可以回到两边页面、首次命中路径、答案 Claim、边界检查、来源锚点和 `N/A` 原因。

验证：从报告逐案例检查 `case_id`、Home、first hit、hop、Claim 结果、边界结果、来源 URI/指纹/片段定位、协议/评估器身份、session 和失败原因。

通过条件：异常行能定位到具体页面/来源，`not_applicable` 不被算作优势，`unknown`、`evidence_missing` 和 `undecidable` 不能被忽略，所有关键案例均有证据，Reader 页面没有 Audit/raw/provider 链接；失败条件：只有主观分数、字段缺失、来源入口越界或无法复现的结论。

证据类型：`evidence`、比较明细。

### AC-QUALITY-004：最终结果优于 CompanyBrain

最终报告会明确给出三项比较、聚合公式、关键错误检查和“优于/不可判定/不通过”状态。

验证：汇总 89 条来源覆盖和 `reader-case-matrix-89-input-v1` 的 `M` 个 canonical 案例三轴结果；路径按 route rank 的赢/并列/输聚合，答案和边界按固定 `M` 分母的平均通过率聚合。

通过条件：全部 `M` 个 canonical 案例先通过逐案例零错误门，再满足至少一项严格优于 CompanyBrain、其余不差、所有 `criticality=critical` 案例均有可比较证据且无关键任务错误/负向误导、来源证据可回查；critical 案例为 `not_applicable`、任一案例为 `unknown/evidence_missing` 或全量案例无法形成可比较证据时标记 `undecidable`；失败条件：任一条件不满足、任一轴退化、证据不完整或结果为 `undecidable`，则不得声称优于。

证据类型：`evidence`、最终质量报告。

### AC-QUALITY-005：不是单页假优化

最终报告同时覆盖 89 条来源和结构、命名、分类、正文、关系、导航、溯源七类差距。

验证：检查报告是否覆盖所有主要差距类别和 89 条来源，而不是只展示一个对照页。

通过条件：结构、命名、分类、正文、关系、导航、溯源均有机器结果或明确不适用原因；失败条件：只验证“位置字段筛选”或只改一个文件名就给出整体结论。

证据类型：`evidence`、全量差距报告。

## 12. 风险、未决与交接

### 12.1 风险

- **RISK-001 样本代表性**：89 条不能证明未来数万条的性能和成本。责任：后续规模任务。关闭条件：另建规模验证，不把它混入本任务结论。
- **RISK-002 语义不确定**：来源可能无法可靠识别模块、对象或关系。责任：build-code。关闭条件：不确定项进入 Audit，且不被默认归入“通用”。
- **RISK-003 正文失真**：合并或摘要可能漏掉条件、限制和冲突。责任：build-code/verify-code。关闭条件：正文、Claim、Evidence 和边界机器检查通过。
- **RISK-004 溯源断裂**：标题或主题重排后可能找不到原始证据。责任：build-code。关闭条件：每个正式 Claim 都能回查稳定来源锚点。
- **RISK-005 仍未优于 CompanyBrain**：结构修正不等于结果一定更好。责任：verify-code。关闭条件：三轴比较满足 AC-QUALITY-004；否则保持 `not_released`，返回继续优化。

### 12.2 未决项

当前没有需要用户重新选择的产品方向。下游可以补充字段格式、模板细节和验证实现，但不能改变：89 条当前范围、全量机器覆盖、无人工审核、新模块/对象三项准入条件、三项比较轴和“不得默认进通用”的边界。

### 12.3 下游硬前置材料

这些材料不是人工审核，也不是未来工作；它们是 build-code/verify-code 能否客观验收当前 89 条的机器输入。缺失或 hash 不一致时只能 `undecidable/not_released`，不能先实现后补口径。

| 材料 | 必须绑定 | owner | 缺失结果 |
| --- | --- | --- | --- |
| 89 条输入 manifest | `input_manifest_id`、逐文件 hash、89 条总 hash | build-plan | 不得编译 |
| 89 条来源覆盖索引 | 严格 89 行、逐文件 hash、去向和失败状态 | build-plan | 不得编译 |
| canonical Reader 案例矩阵 | 固定 `M` 行、逐案例 Claim/边界/来源锚点、`source_to_case_map`、版本/hash | build-plan | 不得比较 |
| CompanyBrain 基线 | `companybrain-full-20260819-current-v2`、1,406 条总 hash、716 页对照范围、逐文件映射 | build-plan | 不可判定 |
| Reader evaluator | 公式、N/A/unknown、聚合、配置版本/hash | build-code | 不可判定 |
| 既有节点基线 | `semantic-baseline-v1`、节点/关系版本/hash | build-code | 新节点不可判定 |

当前已知的输入和 CompanyBrain 总 hash 已在第 11 节冻结；来源覆盖索引、canonical Reader 案例矩阵、evaluator 配置和既有节点基线必须在进入正式实现验收前落下真实 hash。矩阵内容必须逐行冻结预期 Claim、负向边界、来源锚点、匹配规则和失败阈值，build-code/verify-code 只能消费这些材料，不能另造一套口径，也不得由人工逐页补判。

### 12.4 明确延期项

- 数万条生产资料的吞吐、成本、并发、批次恢复和长期运行。
- 正式 `released` 发布、跨批次迁移和旧知识库的大规模升级策略。
- 更复杂的跨版本知识冲突治理和自动修复闭环。
- Reader UI 的视觉改版、搜索体验和非本任务的交互增强。

延期项不影响当前 89 条验收；但下游不得用延期项替代当前质量目标。

## 13. 业务影响与回归范围

### 13.1 预期业务影响

- 读者从“找文件”变成“找答案”，尤其改善产品、模块、对象和任务入口。
- 新知识不会因为暂时无法分类而污染正式“通用”分类；维护者仍能在 Audit 找到它。
- 机器报告能一次发现全量结构和内容异常，降低逐页检查负担。
- 只有证据完整的比较结果才能支持“比 CompanyBrain 好”的结论，避免发布虚假优越性。

### 13.2 回归范围

回归必须覆盖：来源完整性、稳定身份、主题合并、标题分类、关系冲突、正文可读性、Reader/Audit 分离、导航可达、来源回查、失败状态、输入竞态、旧结果保护、全量机器报告和同题三轴比较。

### 13.3 下一阶段交接

下一阶段是 `build-plan`。它只把本规格拆成可执行计划和验收映射，不重新讨论产品方向，不加入人工审核，不把 89 条硬编码成生产规则，不把 CompanyBrain 目录当作模板。若实现中发现本规格无法同时满足原始目标和当前边界，必须返回 `make-decision`，不能在下游偷偷改范围。
