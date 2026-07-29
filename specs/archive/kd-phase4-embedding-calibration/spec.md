# 功能规格：本地 embedding 价值标定与安全采用

> 基于已接受的 Phase 4 决策。本文件只定义产品行为、边界和验收。

- **功能名**：本地 embedding 价值标定与安全采用
- **来源**：accepted make-decision / KnowledgeDigest Phase 4
- **状态**：待审查

## 速读卡（30 秒）

- **一句话需求**：KnowledgeDigest 用隔离的公司语料证明本地 embedding 比 Jaccard 更安全有效，达标才启用。
- **核心改动点**：
  - 交付本地 embedding scorer、标定工具和可重放标定产物。
  - 强制安全门、统一 scorer、整轮回退和公司语料受控网络隔离。
- **最大影响面**：S2 聚类、S3 页面关联及其运行审计；S4-S6 行为保持不变。
- **验收信号**：独立留出集通过安全门并生成绑定完整的 `adopted` 产物，或安全地交付 `not_adopted` 结论且 Jaccard 仍为默认。

## 1. 问题与紧迫性

当前 S2/S3 只使用 token Jaccard，无法证明本地 embedding 对公司语料更有价值。直接启用会带来错误聚类、错误页面关联、公司正文外发、模型漂移和混合评分风险。本期先建立真实、隔离、可重放的比较证据，再决定是否启用。

## 2. 背景、目标与范围

### 背景

现有流程已具备 Jaccard 基线、complete-linkage 聚类、top-k 页面关联和隔离语料复制模式，但没有 embedding 运行能力或本语料阈值证据。

### 目标

- 用同一份冻结 gold 和 lineage 隔离切分比较 Jaccard 与本地 embedding。
- 标定 `high`、`medium`、`page_match_threshold`，输出可验证的采用结论。
- 未通过安全门时仍交付工具与诊断，但不启用 embedding。

### 范围内

- KnowledgeDigest 独立配置的本地 OpenAI-compatible embedding。
- S2/S3 共享 scorer、响应校验、缓存身份、整轮回退。
- 隔离 Confluence 语料、AI 起草且用户确认的 gold、分层自适应抽样。
- calibration/holdout、阈值建议、价值比较、版本化标定产物和真实受控服务验收。

## 3. 用户场景与状态覆盖

### SCN-001：默认继续使用 Jaccard
- **角色**：KnowledgeDigest 操作人
- **Given**：没有有效的 adopted 标定产物
- **When**：运行 digest
- **Then**：S2/S3 都使用 Jaccard，不请求 embedding 服务。

### SCN-002：真实受控服务完成标定
- **角色**：标定操作人
- **Given**：隔离语料、已确认 gold 和已批准受控服务可用
- **When**：运行 calibration 与独立 holdout
- **Then**：得到三个阈值、基线/候选指标和 adopted 或 not_adopted 产物。

### SCN-003：证据不足
- **角色**：标定操作人
- **Given**：严格分层类别缺样本或指标分母为零
- **When**：计算采用结论
- **Then**：列出需扩充类别，保持 not_adopted，不降低门槛。

### SCN-004：产物错配
- **角色**：KnowledgeDigest 操作人
- **Given**：产物缺失、被篡改或模型/维度/语料/gold/split 不匹配
- **When**：尝试使用 embedding
- **Then**：拒绝启用并统一使用 Jaccard，记录机器可读原因。

### SCN-005：运行中 embedding 失败
- **角色**：KnowledgeDigest 操作人
- **Given**：有效 adopted 产物已启用 embedding
- **When**：S2 或 S3 请求/响应失败
- **Then**：保留已验证缓存但作废本轮 embedding 决策，从 S2 起统一重跑 Jaccard。

### SCN-006：非法批量响应
- **角色**：KnowledgeDigest 操作人
- **Given**：已批准受控服务返回缺失/重复 index、错数量、错维度、非有限值或零向量
- **When**：校验响应
- **Then**：不消费部分结果，触发 SCN-005。

### SCN-007：语料或切分隔离失败
- **角色**：标定操作人
- **Given**：源语料发生变化或同 lineage 跨 calibration/holdout
- **When**：执行隔离检查
- **Then**：停止 adopted 结论，保留失败证据。

### SCN-008：确定性重放
- **角色**：验证人
- **Given**：冻结语料、gold、向量和 split
- **When**：重复标定
- **Then**：除时间元数据外，阈值、指标与采用状态一致。

### 状态覆盖清单
- [x] **默认态**：SCN-001
- [x] **空态**：SCN-003
- [x] **错误态**：SCN-004、SCN-005、SCN-006、SCN-007
- [x] **加载态**：N/A — 本期不提供交互式加载界面。
- [x] **取消态**：N/A — 本期是一次性本地命令；中止不得产生 adopted 产物。
- [x] **边界态**：SCN-003、SCN-006
- [x] **权限态**：SCN-007；公司正文只能进入本机或显式批准的公司内网 HTTPS 服务。
- [x] **竞态**：SCN-008；冻结身份防止标定期间输入漂移。

## 4. 产品事实与假设（PFACT）

- **PFACT-01**：默认采用 Jaccard，embedding 必须先证明价值。
  - **status**：`verified`
  - **证据或来源**：accepted decision D1、D4、D7
  - **关联**：FR-ADOPT-001、FR-REPORT-001；AC-01、AC-08
- **PFACT-02**：采用门是零新增错误、至少一项严格改善、其他冻结指标不退化；阈值建议前必须用 confirmed gold 检验 S2/S3 正负样本的 score 分离度，分离度只作诊断和阈值候选证据，不能替代 holdout 安全门。
  - **status**：`verified`
  - **证据或来源**：accepted decision D2
  - **关联**：FR-CAL-001；AC-05
- **PFACT-03**：公司 Confluence 正文只允许进入本机服务，或 KnowledgeDigest 配置中显式批准的公司内网 HTTPS embedding 服务。
  - **status**：`verified`
  - **证据或来源**：accepted decision D3、D9
  - **关联**：FR-CORPUS-001、FR-EMBED-001；AC-02、AC-03
- **PFACT-04**：同一运行的 S2/S3 必须使用同一 scorer，失败整轮回退。
  - **status**：`verified`
  - **证据或来源**：accepted decision D5 及 verified detail resolution
  - **关联**：FR-SCORE-001、FR-FALLBACK-001；AC-04、AC-09
- **PFACT-05**：embedding 必须绑定标定产物，未达标只交付工具。
  - **status**：`verified`
  - **证据或来源**：accepted decision D6、D7
  - **关联**：FR-ARTIFACT-001、FR-REPORT-001；AC-06、AC-08
- **PFACT-06**：gold 由 AI 起草，用户逐项确认后生效。
  - **status**：`verified`
  - **证据或来源**：accepted decision D8
  - **关联**：FR-GOLD-001；AC-07
- **PFACT-07**：抽样按证据扩充，不设固定总数。
  - **status**：`verified`
  - **证据或来源**：accepted decision D10
  - **关联**：FR-GOLD-001、FR-CAL-001；AC-05、AC-07
- **PFACT-08**：本地 embedding 由 KnowledgeDigest 独立配置。
  - **status**：`verified`
  - **证据或来源**：accepted decision D11
  - **关联**：FR-CONFIG-001；AC-01、AC-02

## 5. 功能需求

### 本地配置与服务（LOCAL）

- **FR-CONFIG-001**：KnowledgeDigest JSON 是唯一配置权威。`similarity.backend` 必须是 `jaccard|embedding`；`similarity.embedding` 必须且只能包含 `base_url`、`model`、`expected_dimension`、`calibration_artifact`、`api_key_env`；标定工具可在 backend=jaccard 时使用这些连接字段并把端点身份与探针指纹写入目标产物，digest 运行时 backend=embedding 才要求该路径存在可读的 adopted 产物并校验产物内端点身份与探针指纹。凭证值仅从 `api_key_env` 指定的环境变量读取，不得写入配置、日志或产物，也不复用其他产品配置。
  - **范围边界**：`base_url` 允许 IPv4/IPv6 loopback HTTP(S)，以及显式批准的公司内网 HTTPS 端点；公司内网规范化 base identity 必须精确等于 `https://llm.paxszapp.com:443/v1`（默认端口归一化），请求路径只允许其下的 `/embeddings`，禁止代理、重定向、TLS 降级或跳过系统 CA/hostname 校验。任一必填字段缺失、未知、越界或错配都拒绝 embedding。
  - **依据**：PFACT-03、PFACT-08
  - **场景**：SCN-001、SCN-004
  - **验收**：AC-01、AC-02
- **FR-EMBED-001**：已批准受控服务支持批量 embedding；每批校验数量、index 唯一完整、维度、有限值和非零向量，正文与凭证不得进入日志或产物。
  - **范围边界**：不支持任意公网或未批准的外部 API，也不静默接受部分响应。
  - **依据**：PFACT-03
  - **场景**：SCN-002、SCN-006
  - **验收**：AC-02、AC-03

### 隔离语料与 gold（EVIDENCE）

- **FR-CORPUS-001**：首次真实 calibration/holdout 只读取公司 Confluence 的 89 个 Markdown 文件隔离副本，排除 2 个非 Markdown 文件；绑定文件数量、源/副本 SHA-256 manifest 与 corpus_hash，并证明原语料和正式 KB 未改变。
  - **范围边界**：正文不进入仓库、日志或标定产物。
  - **依据**：PFACT-03
  - **场景**：SCN-002、SCN-007
  - **验收**：AC-03
- **FR-GOLD-001**：AI 起草候选 gold；每项绑定来源 lineage 与内容身份，只有用户逐项确认后才能参与指标；按相似度带和 S2/S3 类别分层并按证据扩充。
  - **范围边界**：严格覆盖 S2 正/负关系 × 高/中/低相似度，以及 S3 new/revise/merge_multiple 与目标页在/不在 top-k；两集合每类至少有可判定样本且所有指标分母非零，缺类继续扩充。
  - **依据**：PFACT-06、PFACT-07
  - **场景**：SCN-002、SCN-003、SCN-007
  - **验收**：AC-05、AC-07

### 评分、标定与采用（SCORE）

- **FR-SCORE-001**：S2 complete-linkage 与 S3 top-k 在同一运行中共享一个最终 scorer。`backend=jaccard` 始终使用 Jaccard；`backend=embedding` 只有 adopted 产物完整匹配时才使用 embedding，否则使用 Jaccard。标定通过后工具生成的推荐配置默认写 `backend=embedding`，但不得覆盖已有显式 `backend=jaccard`。
  - **范围边界**：非相似度质量门保持原语义。
  - **依据**：PFACT-04
  - **场景**：SCN-001、SCN-004、SCN-005
  - **验收**：AC-04、AC-09
- **FR-CAL-001**：calibration 先按 S2/S3 标签统计 Jaccard/embedding 正负 score 分布，输出 count、min、max、quantiles、overlap_count、overlap_rate 与 margin，并从可重算的 feature-separation 诊断生成三个阈值候选；只用 calibration 选择三个阈值，冻结后才运行 lineage 隔离的 holdout；Jaccard 与 embedding 使用同一输入、gold 和 split。S2 错误集合是 gold 标记不可合并但结果进入同簇的 pair；S3 错误集合是 gold 标记不相关但结果选为目标页的 query-page pair。每类新增错误集合等于 embedding 错误集合减去同一 holdout 的 Jaccard 错误集合。
  - **范围边界**：冻结指标为 S2 pair precision/recall/F1、S3 页面关联 precision/recall/F1、S3 action exact accuracy；feature-separation 必须能从 cases 独立重算，任类不可判定或分母为零继续扩充；holdout 禁止调参。
  - **依据**：PFACT-02、PFACT-07
  - **场景**：SCN-002、SCN-003、SCN-007、SCN-008
  - **验收**：AC-05、AC-10
- **FR-ARTIFACT-001**：标定产物公共必填字段为 `schema_version`、`adoption_status`、`endpoint_identity`、`model`、`dimension`、`probe_fingerprint`、`corpus_hash`、`gold_hash`、`split_hash`、`vectors_hash`、`metrics`、`cases`、`tool_version`；`endpoint_identity` 是不含凭证的规范化 scheme/host/port/path；`metrics` 必须包含按 S2/S3 × Jaccard/embedding 分组且可从 cases 重算的 `feature_separation`；`adoption_status` 只允许 `adopted|not_adopted`。adopted 产物还必须且只能增加 `thresholds`，其子字段必须且只能是 `high|medium|page_match_threshold`；not_adopted 产物禁止包含 `thresholds`。任一必填字段缺失、出现未知字段、篡改或错配时拒绝 embedding。
  - **范围边界**：正文不进入产物。
  - **依据**：PFACT-05
  - **场景**：SCN-002、SCN-004、SCN-008
  - **验收**：AC-06、AC-10
- **FR-ADOPT-001**：只有 S2 与 S3 新增错误集合大小分别为 0，并且完整指标集至少一项严格改善、其余全部不退化时，独立 holdout 才满足安全门并产生 adopted；否则 Jaccard 保持默认。
  - **范围边界**：不得通过减少指标或样本类别降低门槛。
  - **依据**：PFACT-01、PFACT-02
  - **场景**：SCN-001、SCN-002、SCN-003
  - **验收**：AC-05、AC-08
- **FR-FALLBACK-001**：embedding 任一请求或响应失败时，可保留身份有效的已算向量，但必须作废本轮 embedding 决策并从 S2 起统一以 Jaccard 重跑；记录失败原因、缓存统计和重启证明。
  - **范围边界**：缓存绑定模型名、维度、固定探针向量指纹、规范化输入 hash 与协议版本；禁止混合后端。
  - **依据**：PFACT-04
  - **场景**：SCN-005、SCN-006
  - **验收**：AC-09
- **FR-REPORT-001**：未达门槛仍交付标定工具、adoption_status=not_adopted 的产物和诊断；真实的已批准本机/公司内网服务不可用时只输出 BLOCKED 运行结论且不生成标定产物，不能以 mock 或未批准的外部 API 替代。
  - **范围边界**：BLOCKED 不等于 not_adopted。
  - **依据**：PFACT-01、PFACT-05
  - **场景**：SCN-002、SCN-003
  - **验收**：AC-08、AC-11
- **FR-COMPAT-001**：S4-S6、溯源、归档、队列与写回的产品行为保持不变，现有回归套件继续通过。
  - **范围边界**：不改变正式知识页业务语义。
  - **依据**：PFACT-01、PFACT-04
  - **场景**：SCN-001、SCN-005
  - **验收**：AC-04、AC-12

## 6. 模块划分

### 标定工具
- **负责什么**：隔离输入、gold 工作流、分层切分、阈值选择、holdout 比较和产物生成。
- **对外提供什么**：服务可用时提供 adoption_status 为 adopted 或 not_adopted 的标定产物；服务不可用时只提供 BLOCKED 运行证据且不生成标定产物。
- **依赖谁**：本地 embedding 服务与用户确认的 gold。
- **测试边界**：冻结输入可确定性重放。

### 运行时 scorer
- **负责什么**：为 S2/S3 提供统一相似度和整轮回退。
- **对外提供什么**：单一 backend 的 S2/S3 决策与审计身份。
- **依赖谁**：KnowledgeDigest 配置和有效标定产物。
- **测试边界**：默认、adopted、错配和失败回退路径。

## 7. 关键实体

- **标定产物**：版本、模型名、维度、固定探针向量指纹、语料/gold/split/向量 hash、阈值、指标、逐例结果、采用状态和工具版本；不得包含正文。
- **Gold 项**：来源 lineage、内容身份、S2/S3 标签、AI 草稿、用户确认状态与标签版本。
- **Scorer 身份**：backend、模型身份、维度、产物身份和运行身份；同一运行 S2/S3 必须一致。
- **向量缓存项**：必须且只能包含 `schema_version|endpoint_identity|model|dimension|probe_fingerprint|input_hash|vector`。任一字段缺失、未知或错配时该项无效，不得作为有效向量消费。

## 8. 数据和生命周期

- **数据粒度**：gold 按判断项，向量按规范化输入，标定产物按一次冻结实验。
- **数据时效**：任一绑定身份变化后原 adopted 产物失效。
- **缺失或迟到**：缺样本列入扩充清单；已批准受控服务不可用为 BLOCKED。
- **预览与正式**：AI gold 是草稿；用户确认后才正式。calibration 是调参证据；holdout 是采用证据。
- **当前与历史**：产物版本化追加；不得用新结果覆盖旧证据。
- **归属与清理**：KnowledgeDigest 持有配置和标定证据；公司正文只存在于受控源与 disposable 副本，临时副本按验收流程清理。

## 9. 兼容性预留

- **既有消费方**：无有效 adopted 产物时完全保持 Jaccard 行为。
- **命名预留**：scorer/backend 与 artifact schema 版本化。
- **容器预留**：产物允许后续增加指标，但 adopted 门所用冻结指标不可运行时删减。
- **状态预留**：标定产物 adoption_status 只允许 adopted 或 not_adopted；运行结论另行区分 BLOCKED 与 fallback，BLOCKED 不写入 adoption_status。
- **扩展边界**：只预留 scorer 身份；不承诺外部 provider、向量库或跨产品路由。

## 10. 明确不做与默认必须成立

### 明确不做
- 任意公网或未批准的外部 embedding API；显式批准的公司内网 HTTPS 端点不属于本项。
- agentmemory/OpenViking 配置复用或接入。
- 向量数据库、生产索引替换、调度器。
- 修改 S4-S6 业务语义。
- 用 mock 替代真实受控服务的正式价值证明。

### 默认必须成立
- 未采用或绑定不匹配时不发 embedding 请求。
- 公司正文与凭证不进入日志、仓库或标定产物。
- S2/S3 单轮只有一个 scorer 身份。
- 任一证据不足、泄漏或输入漂移都不能产生 adopted。

## 11. 验收标准

- [ ] **AC-01**：默认、not_adopted 或任一绑定错配时，S2/S3 均使用 Jaccard且不请求 embedding。
  - **需求**：FR-CONFIG-001、FR-ADOPT-001
  - **验证方法**：状态组合验收与请求审计
  - **通过条件**：`backend=jaccard` 始终统一 Jaccard；`backend=embedding` 仅在 adopted 完整匹配时统一 embedding，否则统一 Jaccard并记录原因
  - **失败条件**：发生 embedding 请求、混合后端或无原因降级
  - **证据类型**：test
- [ ] **AC-02**：有效 adopted 运行配置只连接本机或显式批准的公司内网 HTTPS 服务，批量响应全部通过严格校验。
  - **需求**：FR-CONFIG-001、FR-EMBED-001
  - **验证方法**：真实受控服务与非法响应验收
  - **通过条件**：合法批次被消费，非法批次整体拒绝
  - **失败条件**：未批准地址可用、公司内网地址未使用 HTTPS、发生代理/重定向、部分消费或正文/凭证泄漏
  - **证据类型**：test
- [ ] **AC-03**：隔离运行前后源语料和正式 KB manifest 不变，副本 hash 与产物绑定。
  - **需求**：FR-CORPUS-001、FR-EMBED-001
  - **验证方法**：before/after manifest 与敏感内容扫描
  - **通过条件**：首次真实评测恰好复制 89 个 Markdown、排除 2 个非 Markdown，文件数与源/副本 manifest/corpus_hash 一致，源未变且日志/产物无正文与凭证
  - **失败条件**：文件数或 Markdown-only 边界变化、源变化、绑定缺失或敏感内容出现
  - **证据类型**：evidence
- [ ] **AC-04**：S2/S3 审计显示同一 scorer 身份，既有 S2/S3/S4-S6 合同不变。
  - **需求**：FR-SCORE-001、FR-COMPAT-001
  - **验证方法**：端到端回归与决策产物检查
  - **通过条件**：单一身份且下游合同不变
  - **失败条件**：分阶段后端、混合分数或下游合同变化
  - **证据类型**：test
- [ ] **AC-05**：固定 holdout 只有满足零新增错误、完整指标集中至少一项严格改善、其余不退化且覆盖充分时才 adopted。
  - **需求**：FR-GOLD-001、FR-CAL-001、FR-ADOPT-001
  - **验证方法**：从逐例结果重算指标与错误集合
  - **通过条件**：可从逐例结果重算 feature-separation、阈值候选来源和两类差集且大小均为 0；完整指标集至少一项严格改善、其余不退化；严格覆盖充分
  - **失败条件**：缺少或无法重算 feature-separation、阈值建议无法追溯到 calibration 诊断、任一差集非空、任一指标退化、无严格改善、覆盖不足却 adopted，或通过删指标/缺类别规避
  - **证据类型**：evidence
- [ ] **AC-06**：adopted 产物绑定完整，任一字段缺失、篡改或错配都拒绝 embedding。
  - **需求**：FR-ARTIFACT-001
  - **验证方法**：逐字段篡改与重放
  - **通过条件**：adopted 包含且只包含可应用 thresholds；not_adopted 禁止 thresholds；精确 schema、枚举和全部绑定完整匹配才启用
  - **失败条件**：not_adopted 含 thresholds、adopted 缺 thresholds、必填字段缺失、出现未知字段、枚举非法、裸阈值、错配或篡改仍可启用
  - **证据类型**：test
- [ ] **AC-07**：只有用户确认的 gold 参与指标，lineage 不跨 calibration/holdout，缺类别会列出扩充清单。
  - **需求**：FR-GOLD-001、FR-CAL-001
  - **验证方法**：gold/split 审计
  - **通过条件**：未确认数为零、lineage 交集为空、严格类别在两集合均可判定且全部指标分母非零
  - **失败条件**：未确认项参与、发生泄漏或缺类仍继续 adopted
  - **证据类型**：manual
- [ ] **AC-08**：未达门槛生成 not_adopted 并保持 Jaccard；真实服务不可用生成 BLOCKED，二者都不伪装 adopted。
  - **需求**：FR-ADOPT-001、FR-REPORT-001
  - **验证方法**：失败门槛与服务不可用验收
  - **通过条件**：未达门槛生成 adoption_status=not_adopted；服务不可用只生成 BLOCKED 运行证据且无标定产物；两者都保持 Jaccard
  - **失败条件**：BLOCKED 被写入 adoption_status、BLOCKED 仍生成标定产物、工具交付自动启用 embedding，或 mock 代替真实服务
  - **证据类型**：evidence
- [ ] **AC-09**：S2 或 S3 embedding 失败时保留有效缓存但从 S2 统一重跑 Jaccard，最终无混合决策。
  - **需求**：FR-SCORE-001、FR-FALLBACK-001
  - **验证方法**：S2/S3 故障注入与运行审计
  - **通过条件**：embedding 决策作废、Jaccard 从 S2 重启、缓存身份可验证
  - **失败条件**：保留部分 embedding 决策、只回退剩余工作或混合后端
  - **证据类型**：test
- [ ] **AC-10**：冻结输入重复标定得到相同阈值、指标与采用状态，holdout 不参与选阈值。
  - **需求**：FR-CAL-001、FR-ARTIFACT-001
  - **验证方法**：确定性 replay 与输入追踪
  - **通过条件**：除时间字段外 feature-separation、阈值、指标与采用状态一致，且阈值只依赖 calibration
  - **失败条件**：结果漂移或 holdout 影响阈值
  - **证据类型**：evidence
- [ ] **AC-11**：正式价值证明必须使用真实的已批准本机或公司内网服务。
  - **需求**：FR-REPORT-001
  - **验证方法**：真实服务身份与运行证据核对
  - **通过条件**：真实调用的规范化端点身份、模型、维度和探针指纹可证明
  - **失败条件**：mock、未批准的外部 API 或无法证明服务身份
  - **证据类型**：evidence
- [ ] **AC-12**：现有回归套件全部通过，S4-S6、溯源、归档、队列与写回产品行为不变。
  - **需求**：FR-COMPAT-001
  - **验证方法**：回归测试与正式产物对比
  - **通过条件**：套件全绿且合同无变化
  - **失败条件**：任一回归失败或业务合同变化
  - **证据类型**：test

## 12. 风险、未决与交接

- **RISK-01**：样本稀疏或 lineage 泄漏制造虚假改善
  - **受影响 ID**：FR-GOLD-001、FR-CAL-001、AC-05、AC-07
  - **触发条件**：强制类别缺失、分母为零或 lineage 交集非空
  - **后果**：不可靠 adopted
  - **缓解或 STOP**：继续扩充或停止 adopted
  - **处理 Stage**：build-spec
  - **验证**：严格分层与 split 审计通过
- **RISK-02**：本地模型同名换权重导致旧产物误用
  - **受影响 ID**：FR-CONFIG-001、FR-ARTIFACT-001、AC-06、AC-11
  - **触发条件**：模型身份无法稳定证明
  - **后果**：阈值与向量证据失效
  - **缓解或 STOP**：绑定模型名、维度和固定探针向量指纹；无法生成稳定指纹则不 adopted
  - **处理 Stage**：build-spec
  - **验证**：探针漂移错配验收通过
- **RISK-03**：公司正文外发或进入产物
  - **受影响 ID**：FR-CONFIG-001、FR-EMBED-001、FR-CORPUS-001、AC-02、AC-03
  - **触发条件**：非 loopback 且不是显式批准的公司内网 HTTPS 地址、重定向/代理生效或敏感数据落盘
  - **后果**：公司数据泄露
  - **缓解或 STOP**：只允许 loopback 或精确批准的公司内网 HTTPS 端点，发现越界外发或落盘立即停止
  - **处理 Stage**：build-plan
  - **验证**：网络边界与敏感内容扫描


## 13. 业务影响与回归范围

### S2/S3 相似度决策
- **既有行为**：始终使用 Jaccard。
- **本需求影响**：仅有效 adopted 产物匹配时默认 embedding；失败整轮回退。
- **回归路径**：默认、adopted、错配、S2 失败、S3 失败、非法响应。
- **验收**：AC-01、AC-04、AC-09、AC-12

### 标定与证据
- **既有行为**：没有本语料 embedding 标定产物。
- **本需求影响**：新增隔离、可重放、用户确认 gold 的价值证明。
- **回归路径**：not_adopted、BLOCKED、adopted、replay、lineage 泄漏。
- **验收**：AC-03、AC-05 至 AC-08、AC-10、AC-11

- **可能受冲击的业务规则**：complete-linkage、top-k、页面 action、溯源与写回不变量。
- **明确无影响**：任意公网/未批准外部 API、agentmemory、向量数据库、生产索引替换和调度不在本期。
