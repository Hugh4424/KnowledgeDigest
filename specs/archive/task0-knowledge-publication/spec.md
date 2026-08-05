# KnowledgeDigest Task0 规格：诚实化与交付包

## 当前材料修订说明

- 初版：把已接受的 Task0 决定整理成功能规格。
- 本次：按更新后的 WorkflowHub `spec-content.v3` 结构重排，补齐场景、产品事实、稳定需求 ID、状态合同和失败边界；不增加 PRD 之外的产品目标。
- 本次修订：明确 Reader Package 中“现有结构/分类导航索引”只复用既有产物，产品/模块语义索引延期到 Task1；不改变 allowlist、验收或当前范围。
- 本次修订：明确 pending 只在存在真实、非空、可导航待处理项时生成；不保留空 pending 默认入口，也不改变其他导航边界。
- 影响材料：当前 `decision-log.md`、`CONTEXT.md` 和 PRD Task0；实现文件范围留给后续 `build-plan`。

## 速读卡（30 秒）

- 一句话需求：让 KnowledgeDigest 把“处理成功、写入成功、可读发布和整包交付”分开记录，失败内容不混进正式读者入口。
- 核心交付：唯一来源账本、写回前门禁、Reader/Audit 双包、诚实状态、可解释的重跑幂等。
- 阅读入口：`README.md → Home.md → 现有结构/分类导航索引 → published 主题页 → indexes/sources.md`。
- 最大风险：旧正式页面被失败运行覆盖，或审计现场混入日常阅读目录。
- Task0 结果：页级可以有 `published` 或 `degraded`；交付级固定为 `not_released`。

## 1. 问题与紧迫性

当前运行把 provider 成功、Claim 验证、写回成功和知识质量混成一个“成功”。失败来源可能进入导航，pending 可能是空壳，来源索引、快照和批次账本可能不一致，审计现场也可能混在默认阅读目录。继续做语义编译会把错误放大。

Task0 必须先补齐诚实化和交付包边界：所有来源都有可核对的处理事实，写回前完成安全门禁，读者只看到通过机器门的内容，失败仍可恢复和审计。

## 2. 背景、目标与范围

### 背景

现有流水线已经有来源读取、聚类、检索、Claim 草稿、发布、导航、写回和溯源职责。原始设计要求失败即报错、写入前归档、不删除旧内容；Task0 把这些原则落实到来源闭环、状态和交付包。

### 目标

- 建立 `input manifest → source snapshots → audit ledger` 的唯一来源对账链。
- 在正式写回前检查 provenance、Claim、路径、状态和包边界。
- 隔离 provider、JSON、正文、归属和冲突失败，不让它们进入 Reader 导航。
- 让 Reader Package 简单、干净，Audit/Archive Package 保留恢复和排查事实。
- 让同一输入快照和配置的重跑不重复增长业务结果。

### 范围

- 只处理 Task0 之后的新运行。
- 覆盖用户运行流程、Reader/Audit 页面范围、数据状态、成功失败边界、导航完整性、离线基线、provider fallback、题集 manifest 和异常增长审计。
- 保留现有 S1–S6 和单写者事务边界；不改造正文语义编译能力。

## 3. 用户场景与状态覆盖

### SCN-001：新运行成功但整包未发布

- **角色**：知识库维护者与读者。
- **Given**：维护者手动运行一次既有 digest 流程，输入清单可闭合，来源和 Claim 通过机器门。
- **When**：系统完成写回并生成两类交付事实。
- **Then**：通过机器门的页标为 `published`，进入候选 Reader Package；本 Task0 的交付级仍为 `not_released`。

### SCN-002：来源级失败被隔离

- **角色**：知识库维护者。
- **Given**：部分来源发生 provider 失败、JSON 破损、无正文、无产品归属、事实冲突或人工修改冲突。
- **When**：系统处理同一批次的其他来源。
- **Then**：失败来源记录为 `degraded` 审计内容，不进入 Reader 导航；无关的已发布页继续保留。

### SCN-003：来源闭环或写前门禁失败

- **角色**：知识库维护者。
- **Given**：manifest、snapshot、ledger、Claim、provenance、路径、状态或包 allowlist 任一不一致。
- **When**：系统准备写回正式页面。
- **Then**：在写回前明确失败，不产生新的 formal 页面，也不覆盖旧 formal 页面。

### SCN-004：读者从干净入口查看来源关系

- **角色**：知识库读者。
- **Given**：Reader Package 已生成，存在 Home、分类、主题页和来源投影。
- **When**：读者依次打开入口和链接。
- **Then**：所有链接指向真实的 `published` 页面或可定位的来源记录；不需要进入 `_digest`、`_archive` 或 provider 现场。

### SCN-005：同一快照重跑

- **角色**：知识库维护者。
- **Given**：同一输入快照、配置和批次再次运行。
- **When**：系统完成重跑并记录新的运行事实。
- **Then**：来源、Claim、页面、duplicate 和 archive 等业务结果不重复增长；运行记录可以追加且能区分运行。

### SCN-006：离线基线与语义 fallback

- **角色**：离线运行维护者。
- **Given**：运行使用 `--no-llm + Jaccard`，或语义模式的 embedding 探测失败。
- **When**：系统完成本次处理。
- **Then**：离线基线产生零 LLM、零 embedding 网络调用；语义 fallback 写入 manifest/status，若本次要求语义发布则交付级为 `not_released`。

### SCN-007：题集 manifest 可重放

- **角色**：Task2/Task3 评审者。
- **Given**：系统生成 v1 题集 manifest。
- **When**：评审者读取题集、抽样规则和 hash。
- **Then**：可核对 17 个正向问题、3 个负向问题及原文、入口、期望主题/产品、覆盖角色、负向设计原则、seed、评审人和 hash。

### SCN-008：状态覆盖

| 对象 | 状态 | 说明 | Task0 终态 |
| --- | --- | --- | --- |
| 主题页 | `published` | 通过机器门 | 可进入候选 Reader |
| 主题页 | `degraded` | 失败或缺证据 | 只进 Audit |
| 交付包 | `released` | 机器、读者、交付门全过 | Task3 才允许 |
| 交付包 | `not_released` | 任一门未过 | Task0 固定 |
| 写入事实 | `written` | 只表示写入完成 | 不等于发布 |

## 4. 产品事实与假设（PFACT）

- **PFACT-CLOSURE**：manifest、source snapshot 和 audit ledger 必须覆盖同一来源集合；Reader 来源索引只是投影，不是第二事实源。
  - **status**：`verified`
  - **依据**：PRD Task0 原始方案 1、已接受决定和现有溯源合同。
  - **关联**：FR-KD-001、FR-KD-002、AC-001、AC-003。

- **PFACT-PREWRITE**：S6 provenance、Claim、路径、状态和交付包门禁必须发生在正式写回之前。
  - **status**：`verified`
  - **依据**：PRD Task0 原始方案 2、现有“写入前检查并归档”原则。
  - **关联**：FR-KD-003、FR-KD-010、AC-003、AC-007。

- **PFACT-FAILURE**：来源级失败不应拖垮无关内容，也不能伪装成发布成功。
  - **status**：`verified`
  - **依据**：PRD Task0 原始方案 3、4 和用户已确认的失败隔离选择。
  - **关联**：FR-KD-004、FR-KD-005、FR-KD-006、AC-004、AC-007。

- **PFACT-PACKAGE**：Reader Package 和 Audit/Archive Package 是两类不同交付包；Reader 必须保持干净，Audit 必须可恢复和排查。
  - **status**：`verified`
  - **依据**：PRD Task0 原始方案 5 和用户已确认的 `indexes/sources.md` 投影选择。
  - **关联**：FR-KD-007、FR-KD-008、AC-005、AC-006。

- **PFACT-IDEMPOTENCY**：同一快照和配置的重跑不重复增长业务结果，运行记录可以追加。
  - **status**：`verified`
  - **依据**：PRD Task0 原始方案 6 和用户已确认的业务幂等选择。
  - **关联**：FR-KD-009、FR-KD-013、AC-002、AC-009。

- **PFACT-OFFLINE**：`--no-llm + Jaccard` 是合法离线基线；允许既有 embedding fallback，但不能把 fallback 伪装成语义发布成功。
  - **status**：`verified`
  - **依据**：PRD Task0 原始方案 4 和项目既有离线合同。
  - **关联**：FR-KD-011、AC-008、AC-010。

- **PFACT-QUESTIONSET**：题集是后续读者门的固定输入，不由 Task0 代替 Task2/Task3 做正文质量判断。
  - **status**：`verified`
  - **依据**：PRD Task0 原始方案 7 和已接受的范围边界。
  - **关联**：FR-KD-012、AC-008。

- **PFACT-HISTORY**：本任务只处理后续新运行；旧 Task2 结果、旧 formal 页面和旧审计证据不迁移、不重写、不删除。
  - **status**：`verified`
  - **依据**：用户已确认的历史保护选择和当前项目质量合同。
  - **关联**：FR-KD-010、AC-007。

## 5. 功能需求

- **FR-KD-001**：系统必须为每次新运行建立唯一 input manifest，并让 manifest、source snapshot、audit ledger 的来源集合、稳定来源 ID 和内容指纹完全一致。
  - **范围边界**：缺失、额外、重复或清单变化都要显式失败，不能静默省略。
  - **场景**：SCN-001、SCN-003。
  - **验收**：AC-001。

- **FR-KD-002**：每个来源必须保留来源地址、相对路径、运行时间、内容指纹、处理状态和失败原因，并能定位到 Claim、Evidence、页面关系或失败原因。
  - **范围边界**：Audit 的唯一来源事实源是 `_digest/source-manifest.json`；`indexes/sources.md` 只做 Reader 投影，不能维护第二份来源事实。
  - **场景**：SCN-001、SCN-004。
  - **验收**：AC-001、AC-005。

- **FR-KD-003**：正式写回前必须完成 provenance、Claim 验证、target path、页级状态、交付级状态和 Reader/Audit allowlist 检查。
  - **范围边界**：任一门禁失败时，不产生新的 formal 页面，也不覆盖旧 formal 页面。
  - **场景**：SCN-003。
  - **验收**：AC-003、AC-007。

- **FR-KD-004**：系统必须分别记录 `provider_transport`、`claim_verification`、`writeback`、`machine_pass`、`agent_assisted`、`human_reviewed` 和最终发布状态。
  - **范围边界**：`written` 不得推导为 `published` 或 `released`。
  - **场景**：SCN-001、SCN-002。
  - **验收**：AC-004。

- **FR-KD-005**：provider 失败、JSON 破损、无正文、没有可验证的产品/模块归属证据、事实冲突或人工修改冲突的来源只能生成 `degraded` 审计内容，不得进入正式 Reader 导航。
  - **范围边界**：Task0 只消费已有的归属事实并记录缺失，不建立 ProductGazetteer/TopicIndex，也不猜测归属；单个来源失败不回滚无关的已发布页。
  - **场景**：SCN-002。
  - **验收**：AC-004、AC-006。

- **FR-KD-006**：页级状态只允许 `published` 或 `degraded`；交付级状态只允许 `released` 或 `not_released`。
  - **范围边界**：Task0–Task2 固定为 `not_released`；只有 Task3 同时通过机器门、题集读者门和交付门后才允许 `released`。
  - **场景**：SCN-001、SCN-002、SCN-006。
  - **验收**：AC-004、AC-010。

- **FR-KD-007**：Reader Package 和 Audit/Archive Package 必须按 allowlist 生成，不能靠偶然目录排除得到 Reader Package。
  - **范围边界**：Reader 不包含 `_digest`、`_archive`、provider 日志、模型原始响应或运行比较报告；Audit/Archive 保留来源、Claim、Evidence、原文归档、失败原因、运行报告和配置/provider hash。
  - **场景**：SCN-001、SCN-004。
  - **验收**：AC-005。

- **FR-KD-008**：Home、现有结构/分类导航索引、主题页链接和 `indexes/sources.md` 必须无空页、断链和不可点击链接。
  - **范围边界**：Task0 的产品/模块索引只复用现有结构/导航产物；产品/模块语义索引内容属于 Task1。pending 只有在存在真实、非空、可导航的待处理内容时生成；无真实待处理项不生成 pending。新运行不生成新的 `_digest/source-index.md`，历史结果不迁移、不重写。
  - **场景**：SCN-004。
  - **验收**：AC-005、AC-006、AC-007。

- **FR-KD-009**：同一输入 snapshot、配置和批次重复运行时，来源关系、Claim、duplicate、页面和 archive 内容不得重复增长。
  - **范围边界**：运行记录可以追加，但必须区分运行，不能用追加历史掩盖业务重复。
  - **场景**：SCN-005。
  - **验收**：AC-002、AC-009。

- **FR-KD-010**：失败运行不得静默覆盖旧 formal 页面；写回前先归档，归档必须可恢复。
  - **范围边界**：Task0 只回滚本任务代码，不删除基线输出和审计证据；路径变化必须保留旧路径到新路径映射。
  - **场景**：SCN-003、SCN-005。
  - **验收**：AC-003、AC-007。

- **FR-KD-011**：离线和语义 fallback 必须诚实记录。
  - **范围边界**：`--no-llm + Jaccard` 必须产生零 LLM、零 embedding 网络调用；语义 provider 只允许项目约定的 qwen3.6 和 jina-embeddings；语义运行必须在 manifest/status/audit 中记录 provider、model、endpoint、embedding 维度、probe/calibration hash、timeout、replay 次数、call 数和 wall-clock 预算；凭据只能从环境变量读取，绝不写入日志、报告或知识库。embedding 探测失败时整次回退 Jaccard，并在 manifest/status 记录 fallback；语义要求下 fallback 的交付级必须为 `not_released`；timeout、replay、call 和 wall-clock 超限不能改写为成功。
  - **场景**：SCN-006。
  - **验收**：AC-008、AC-010。

- **FR-KD-012**：系统必须冻结并落盘 v1 题集 manifest，包含 17 个正向问题和 3 个负向问题的原文、入口、期望主题/产品、覆盖角色、负向设计原则、抽样 seed、评审人和题集 hash。
  - **范围边界**：Task2 只使用样本可回答的派生子集，Task3 使用完整题集；Task0 不承担正文语义质量和读者门判定。
  - **场景**：SCN-007。
  - **验收**：AC-008。

- **FR-KD-013**：运行报告必须能按 snapshot、Claim、duplicate 识别重复运行和 archive 增长，并定位异常增长。
  - **范围边界**：不得用一个全局文件体积阈值替代内容级审计。
  - **场景**：SCN-005。
  - **验收**：AC-009。

## 6. 模块划分

### 来源闭环

负责冻结输入、source snapshot、稳定来源身份、Claim/duplicate/provenance 关系和 Audit manifest；对外提供一份可核对的全来源事实。

### 写回前门禁

负责检查 Claim、provenance、路径、状态、归档前置条件与可写性和两类包的 allowlist；门禁失败时阻止 formal 写回。真实归档可恢复性由 AC-007 验收。

### Reader 导航与交付包

负责 README、Home、现有结构/分类导航索引、主题页和 `indexes/sources.md` 的读者投影；负责把审计现场隔离到 Audit/Archive Package。

### 重跑与审计

负责同一快照和配置的业务幂等、运行记录区分、异常增长定位、离线/fallback 和题集 manifest 事实。

以上模块沿用现有 S1–S6 和单写者边界，不复制第二套事实源。

## 7. 关键实体

- **Input Manifest**：本次来源 ID、路径/URI、内容指纹和配置 hash 的冻结清单；Audit 唯一事实源落在 `_digest/source-manifest.json`。
- **Source Snapshot**：来源地址、相对路径、运行时间、原文副本和内容指纹。
- **Audit Ledger**：来源、Claim、Evidence、duplicate、provenance、状态、失败原因和目标页关系。
- **Page Result**：页面路径、Claim、provenance 和页级 `published/degraded` 状态。
- **Reader Package**：README、Home、现有结构/分类导航索引（产品/模块语义索引属于 Task1）、published 主题页和 `indexes/sources.md`。
- **Audit/Archive Package**：`_digest/source-manifest.json`、snapshot、Claim、Evidence、原文归档、失败原因、运行报告和配置/provider hash。
- **Delivery Result**：allowlist、运行报告和交付级状态。
- **Question-set Manifest**：17+3 题、派生样本规则、seed、评审人和 hash。

## 8. 数据和生命周期

### 流程顺序

`ingest → manifest/snapshot → Claim/duplicate/provenance → path/status/package checks → prewrite gate → archive → atomic writeback`

S6 和交付包事实必须位于 writeback 之前；Home、分类索引、来源入口和主题页在同一归档后发布事务内更新。

### 状态关系

- 来源先进入 manifest 和 snapshot，再进入处理、Claim、duplicate、provenance 和页面关系；缺失或变化必须显式记录。
- 页面通过机器门为 `published`，失败、冲突、缺证据或人工修改冲突为 `degraded`。
- 写入事实 `written` 只代表写回动作，不代表页级或交付级成功。
- 交付包只有 `released` 或 `not_released`；Task0 固定 `not_released`。
- 失败内容只保留在 Audit/Archive，不进入正式 Reader 导航；既有合法结果保留。

### 事务与恢复

写入前先归档；写回失败时保留旧 formal 页面和审计证据。旧结果只读保留；新候选包不能覆盖上一份 released 包。单来源失败隔离，重跑失败不删除历史。

## 9. 兼容性预留

- 继续使用现有 S1–S6、单写者和本地命令运行方式。
- Reader 来源入口使用 `indexes/sources.md` 投影；新运行不再新增 `_digest/source-index.md`，历史文件不迁移、不重写。
- 允许既有 qwen3.6、jina-embeddings 和 Jaccard fallback 合同继续存在，但 Task0 只记录事实，不把 fallback 变成语义发布成功。
- 题集 manifest 为后续 Task2/Task3 提供固定输入；Task0 不提前实现题集读者门。
- 不改变既有主题正文编译能力和已发布历史的阅读路径。

## 10. 明确不做与默认必须成立

### 明确不做

- 不迁移、不重写历史 Task2 结果、旧正式页面或旧审计证据。
- 不做 ProductGazetteer、TopicIndex、稳定主题主轴或全量 TopicPlan。
- 不做三类正文编译、正文语义质量、完整读者门或人工读者验收。
- 不做全量 89 篇重发布。
- 不引入数据库、图数据库、向量数据库、CAS、调度器、后台守护或 AgentMemory 正式接入。
- 不建立永久人工审核队列。
- 不清理仓库；文档归档、inventory、引用扫描和清理属于 Task3-Closeout。

### 默认必须成立

- 失败即明确失败，不能用 provider、写回或运行记录掩盖缺失的质量事实。
- Reader 与 Audit/Archive 的边界由 allowlist 验证，不由目录现状猜测。
- 所有状态和来源关系都有稳定可核对的事实；具体字段、hash 算法、预算数值和题集文件路径在实现 manifest 中冻结。
- 后续若需要改变范围、状态、页面或验收标准，必须回到 make-decision，不在实现阶段补需求。

## 11. 验收标准

- [ ] **AC-001**：给定包含成功、失败、重复和缺失来源的输入清单，input manifest、snapshot 和 audit ledger 的来源集合完全一致；缺失来源明确失败，写回前无新的 formal 页面。
- [ ] **AC-002**：同一 snapshot、配置和批次运行两次，source、Claim、duplicate、history 的业务关系、页面关系和 archive 内容不重复增长；运行记录可追加且统计可解释。
- [ ] **AC-003**：模拟 provenance、Claim、路径、状态或包 allowlist 任一失败，系统在 writeback 前失败，旧 formal 页面内容和路径不变。
- [ ] **AC-004**：可分别断言页级 `published/degraded`、交付级 `released/not_released`、`written`、provider transport、Claim verification 及机器/agent/人工证据；Task0 任何成功路径都不能输出 `released`。
- [ ] **AC-005**：Reader Package 只包含 README、Home、现有结构/分类导航索引（产品/模块语义索引属于 Task1）、正式页面和 `indexes/sources.md`；Audit/Archive 能定位全部来源和失败原因；Reader 不含审计现场。
- [ ] **AC-006**：Home、分类、来源入口和 pending 经过链接检查无空页、断链和不可点击链接；没有真实待处理项时不生成 pending。
- [ ] **AC-007**：失败运行不能覆盖旧 formal 页面；归档能够恢复旧内容；新运行不迁移或重写历史 Task2 结果。
- [ ] **AC-008**：题集 manifest 可重放，包含 17+3 题、派生样本规则、seed、评审人和 hash；`--no-llm` 运行的 LLM 和 embedding 网络调用数均为 0。
- [ ] **AC-009**：同一 snapshot 的重复运行不会产生异常 archive/duplicate 增长；若发生异常，audit report 能定位到 snapshot、Claim、duplicate、运行和归档记录。
- [ ] **AC-010**：provider 只来自 allowlist；语义运行可审计记录 provider、model、endpoint、embedding 维度、probe/calibration hash、timeout、replay、call 和 wall-clock 预算；凭据只从环境变量读取且不进入日志、报告或知识库；embedding fallback 写入 manifest/status；语义要求下 fallback 的交付级为 `not_released`；超时、重放、调用数或 wall-clock 超限不能生成成功事实。

## 12. 风险、未决与交接

### 风险

- 当前历史产物不迁移，短期内会存在旧阅读结构和新 Reader Package 并存。
- provider 失败与 fallback 的事实如果记录不全，会让 `degraded`、`not_released` 和“仅写入”再次混淆。
- 业务幂等和运行审计追加若边界不清，可能出现 duplicate、claim-history 或 archive 异常增长。

### 未决

不再有会改变本规格范围的未决产品问题。具体字段、hash 算法、预算数值、题集文件路径和现有职责内的最小实现位置属于 build-plan/实现参数；若它们改变 FR、AC、页面或状态，必须回到 make-decision。

### 决策分层

- **Locked**：decision-log 已确认的来源闭环、写前门禁、失败隔离、状态分层、Reader/Audit allowlist、`indexes/sources.md` 投影、幂等、真实 pending、17+3 题集、provider/fallback 和预算超限失败规则；本规格不得重新解释这些方向。
- **Unresolved**：只剩实现前要落盘的字段、hash 算法、预算数值、题集文件路径和既有职责内的最小实现位置；它们不能改变 FR、AC、页面或状态。
- **Newly discovered ambiguity**：当前没有；若实现或审查发现会改变产品范围、状态、页面或验收标准的歧义，必须回到 `make-decision`，不能由 `build-spec` 或实现阶段补需求。

### 交接

- build-plan 只读取本规格、当前 decision-log 和 PRD 已冻结的 Task0 事实。
- build-plan 必须在实现前冻结题集 manifest 的字段、hash 算法、题集文件路径、状态字段，以及 provider/model/endpoint、embedding 维度、probe/calibration hash、timeout、replay、call 和 wall-clock 预算，并把冻结结果映射到 AC-008/AC-010 的验证步骤。
- build-plan 必须把 FR/AC 映射到实现步骤、测试和恢复证据，不得重新讨论 Reader/Audit 是否属于 Task0。
- 任何实现阶段的范围扩大、历史迁移、正文编译或全量发布，都延期回 make-decision。

## 13. 业务影响与回归范围

本任务新增的是诚实化的来源闭环、写回前门禁、Reader/Audit 包和运行审计；既有来源处理、主题正文编译和合法历史阅读路径必须保持可用。

回归重点是：来源集合对账、写前失败、来源失败隔离、包 allowlist、导航无空入口、同一快照重跑、旧页面保护、离线零调用、provider fallback、题集 manifest 和异常增长定位。
