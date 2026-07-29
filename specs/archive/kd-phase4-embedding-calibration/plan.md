# 实现计划：本地 embedding 价值标定与安全采用

> 基于已接受的 Phase 4 spec；只规划实现与验证，不重新选择产品方向。

- **Input**：`specs/kd-phase4-embedding-calibration/spec.md`
- **Status**：Draft
- **Template version**：`plan-task.v3`

## 1. 速读卡

- **Goal**：交付本地 embedding scorer、标定工具和绑定产物；只有独立 holdout 证明安全价值时运行时才可启用。
- **Non-goals**：任意公网或未批准的外部 embedding API、agentmemory/OpenViking 配置复用、向量数据库、调度器、S4-S6 语义变更；来源：accepted spec 第 10 节。
- **Before**：S2/S3 直接调用 token Jaccard；配置为扁平 JSON；没有 embedding、gold、split 或标定产物。
- **After**：S2/S3 共用 run-scoped scorer；有效 adopted 产物才允许 embedding；失败从 S2 统一以 Jaccard 重跑；独立工具生成 adopted/not_adopted 或 BLOCKED 证据。
- **Main risk**：公司正文经未批准端点、代理、重定向或日志离开受控边界，或部分 embedding 决策混入最终结果。
- **Next step**：先写配置、响应、产物和默认不调用服务的 RED 测试。

## 2. Technical Context and Constraints

- **Language / runtime**：Python >=3.11；setuptools；pytest >=8。
- **Primary dependencies**：仅 Python 标准库和 pytest；已批准的 OpenAI-compatible `/v1/embeddings` 服务是运行时外部能力。
- **Storage / state**：KnowledgeDigest JSON 是配置权威；缓存和标定证据为本地版本化 JSON；公司正文只存在受控源和 disposable 副本。
- **Testing**：pytest acceptance；真实服务正式验收另用隔离 runner，mock 只测协议故障，不能证明价值。
- **Target environment**：macOS 本机；embedding 服务可为 loopback，或显式批准的公司内网 HTTPS 端点；输入可省略默认端口，但规范化身份必须精确等于 `https://llm.paxszapp.com:443/v1`。
- **Project type**：Python CLI 与本地文件流水线。
- **Performance goals**：每轮唯一文本批量向量化，禁止逐 pair HTTP；未规定硬延迟上限。
- **Scale / scope**：首次真实语料恰好 89 个 Markdown，排除 2 个非 Markdown；S2 complete-linkage 和 S3 top-k。
- **Relevant ADR / context**：`docs/adr/0003-local-evidence-gated-embedding.md`、`CONTEXT.md`、accepted spec。
- **Unresolved facts**：真实 corpus 绝对路径、受控服务可用性和凭证环境变量只在隔离验收时注入；缺失则正式运行输出 BLOCKED，不能猜测或改用未批准服务。

### Global Constraints

- 默认 Jaccard；显式 `backend=jaccard` 永不被推荐配置覆盖。
- `backend=embedding` 必须绑定完整匹配的 adopted 产物；任何错配都不请求服务。
- 服务地址只允许 loopback 或精确批准的公司内网 HTTPS 端点；禁代理和重定向；日志、错误、缓存、产物不得含正文或凭证。
- 单轮 S2/S3 只有一个最终 scorer；任一 embedding 失败作废本轮相似度决策并从 S2 重跑 Jaccard。
- holdout 不调参；严格分层缺类、分母为零、lineage 泄漏或输入漂移不得 adopted。
- S4-S6、provenance、archive、queue、writeback 合同不变。

## 3. Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"CONSTITUTION.md","hash":"0dd8f6f659175bb09ecffd4fb713c291e1f9eccb81ff367c89dbc749be585606","id":"workflowhub-constitution","version":"1.4.0","clause_count":21}`

### Framework Principles

- [x] F1：编排留在 pipeline，HTTP、artifact、calibration 各自窄模块。
- [x] F2：scorer、artifact、gold/split 使用明确数据对象和严格 schema。
- [x] F3：hash/schema/lineage 是硬校验；质量结论保留原始证据。
- [x] F4：正式计划交给异源 review，最终由人确认。
- [x] F5：只增加 accepted spec 要求的门，不预造通用 gate 平台。
- [x] F6：运行审计写入既有 report/独立 evidence，不隐式藏状态。
- [x] F7：build-plan 保留人工确认；提交、推送、真实语料操作另行授权。
- [x] F8：复用 Jaccard、pipeline 和 JSONL；新增模块按单一职责拆分。
- [x] F9：RED 必须因目标断言失败，BLOCKED 不伪装 not_adopted。
- [x] F10：新增校验直接对应泄漏、混合决策和伪 adopted 三类真实威胁。

### Quality Principles

- [x] Q1：正式 actionable major/blocking 才暂停；其余 finding 记录并处置。
- [x] Q2：结构 validator、review 事实、人工确认三类边界分离。
- [x] Q3：使用 WorkflowHub 正式异源 review，不自审改写 verdict。

### Skill Principles

- [x] S1：HTTP/JSON/hash 使用标准库，不引入新框架。
- [x] S2：N/A — 不引入外部技能代码。
- [x] S3：N/A — 不升级外部技能。
- [x] S4：标定工具输出完整指标、cases、hash 和采用结论。
- [x] S5：计划研究已由只读子代理执行，主上下文只吸收结论。
- [x] S6：采用 OpenAI-compatible 批量协议和标准 holdout 方法，不自造网络协议。
- [x] S7：N/A — 不新增 WorkflowHub 阶段或技能。
- [x] S8：标定 CLI 只依赖显式文件和已批准 endpoint，可独立运行。

**Result**：21/21 addressed；无宪法 blocker。

## 4. Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| Project rules | `CONTEXT.md` | no change | N/A | 已记录边界 |
| Workflow contracts | N/A | no change | N/A | 不改 WorkflowHub |
| Review contracts | N/A | no change | N/A | 沿用正式 review |
| Schemas and events | artifact/cache JSON | change | T001-T002 | 严格绑定 |
| Runtime configuration | `config.py` | change | T001-T002 | 嵌套显式后端 |
| Knowledge and docs | `docs/adr/0003-local-evidence-gated-embedding.md` | no change | N/A | 已接受决策 |
| Automation gates | Phase 4 acceptance | change | T011-T012 | 真实隔离证明 |

## 5. Technical Decisions

### DEC-001 — Run-scoped scorer

- **Problem**：S2/S3 直接调用私有 Jaccard，无法证明单轮后端一致。
- **Options**：各阶段独立 client；共享 scorer；全局单例。
- **Selected**：extend — 共享显式传入的 run-scoped scorer。
- **Reason**：依赖可见、测试简单、无全局状态；Jaccard 数值可原样保留。
- **Consequence / risk**：需要修改 cluster/retrieve 签名和 pipeline 调用点。
- **Fallback**：构造 Jaccard scorer，保持旧算法与排序。

### DEC-002 — 批量向量化后本地 cosine

- **Problem**：complete-linkage 和 top-k 会重复比较文本，逐 pair HTTP 慢且易部分失败。
- **Options**：逐 pair 请求；预取本轮唯一文本；向量数据库。
- **Selected**：new — 预取唯一文本、严格验证整批响应、缓存有效向量，本地 cosine。
- **Reason**：请求数最少，失败边界清晰，不引入向量库。
- **Consequence / risk**：需规范化 input hash、批次 index 校验和内存向量表。
- **Fallback**：任何失败抛 typed error，由 pipeline 从 S2 以 Jaccard 重跑。
- **F10 real threat**：部分批次或错维度向量造成混合决策。
- **F10 existing cover**：当前没有 embedding client 或响应校验。
- **F10 bypassable**：所有 embedding scorer 构造统一经过批量验证，不能由 S2/S3 绕过。
- **F10 maintenance cost**：一个小型标准库 client、一个严格缓存 schema。
- **F10 disposition**：keep。

### DEC-003 — 标定域与运行时分离

- **Problem**：阈值选择、gold/split 和真实语料隔离不属于 digest 在线路径。
- **Options**：塞入 digest；独立 CLI 复用 scorer/artifact；独立项目。
- **Selected**：new — 同包独立 `knowledge-digest-calibrate` CLI，复用 client/scorer/artifact。
- **Reason**：KnowledgeDigest 独立配置且不扩大运行时职责。
- **Consequence / risk**：新增若干小模块和一个 acceptance runner。
- **Fallback**：服务不可用只写 BLOCKED evidence，不生成 artifact。
- **F10 real threat**：holdout 调参、未确认 gold、公司语料外泄导致伪价值。
- **F10 existing cover**：Phase 3 隔离 runner 可复用隔离证明模式，但无 Phase 4 指标逻辑。
- **F10 bypassable**：adoption evaluator 只接受 confirmed gold、冻结 split 和可重算 cases。
- **F10 maintenance cost**：限定为本期固定 schema/指标，不建通用实验平台。
- **F10 disposition**：keep。

## 6. Solution Design

### Overview

`config.py` 严格解析嵌套 similarity 配置；`calibration_artifact.py` 校验 adopted/not_adopted 精确 schema 和全部 identity。运行开始时 resolver 决定 requested/effective backend：digest runtime resolver 在显式 Jaccard 时只返回 Jaccard；仅 backend=embedding 且 adopted artifact 完整匹配时创建 runtime client。独立 calibration client factory 则可在 backend=jaccard 时读取 similarity.embedding 连接字段、执行真实受控服务探针并写入 endpoint_identity/probe_fingerprint，不要求既有 adopted artifact。

pipeline 先收集 S2 原文和 S3 候选页需要的唯一文本，批量获取并验证向量，再把同一 scorer 传给 cluster/retrieve。若 S2 或 S3 出现 embedding typed failure，丢弃本轮 S2/S3 决策文件，保留身份有效缓存，并用 Jaccard scorer 从 S2 重跑；最终 report 只呈现一个 effective backend。

标定 CLI 在隔离副本上生成/读取逐项确认 gold，按 lineage 严格切分 calibration/holdout，只用 calibration 选三个阈值，再在 holdout 同时运行 Jaccard/embedding，输出 cases、可重算 feature-separation、阈值候选来源、完整指标和错误差集。安全门决定 adopted/not_adopted；adopted 另生成 fresh 推荐配置 backend=embedding，但已有显式 backend=jaccard 保持原文件不变。服务不可用另写 BLOCKED evidence，绝不写 artifact。

### Module responsibilities

#### 配置与 artifact

- **Responsibility**：解析嵌套配置，验证 loopback/批准的公司内网 HTTPS 端点、artifact schema/hash/endpoint/model/dimension/probe/split 身份。
- **Consumes**：KnowledgeDigest JSON、环境凭证、calibration artifact。
- **Produces**：不可变 similarity settings、digest runtime resolution、可由标定域复用的 client 与 endpoint 规范化函数。
- **Must not decide**：不得选择阈值或覆盖显式 Jaccard。

#### Embedding client 与 scorer

- **Responsibility**：无代理/无重定向批量请求、严格响应验证、cosine、cache identity。
- **Consumes**：唯一规范化文本及本地服务配置。
- **Produces**：run-scoped scorer、缓存统计和不含正文的失败码。
- **Must not decide**：不得决定 adopted 或写业务页面。

#### Pipeline fallback coordinator

- **Responsibility**：同一 scorer 驱动 S2/S3；失败时作废决策并从 S2 重跑。
- **Consumes**：resolved scorer、raw items、page records。
- **Produces**：单后端 S2/S3 文件和 report 审计。
- **Must not decide**：不得混用缓存向量与 Jaccard 分数。

#### Gold workflow

- **Responsibility**：在本机隔离副本上生成 AI draft exchange，校验 lineage/content identity，并记录用户逐项 confirm/reject。
- **Consumes**：隔离 corpus manifest、AI 候选标签和逐项用户决定。
- **Produces**：confirmed gold 与 confirmation-only `gold-confirmation-audit.json`；unconfirmed_count、identity 和逐项 user decision 可核对。
- **Must not decide**：不得自动确认、不得调用外部服务或让未确认项进入指标。

#### Calibration domain

- **Responsibility**：corpus manifest、confirmed gold、strict split、threshold selection、metrics、安全门、artifact/BLOCKED。
- **Consumes**：隔离副本、gold、显式配置和真实受控服务。
- **Produces**：含 machine-readable feature-separation 与阈值候选来源的可重放 artifact，或 BLOCKED evidence。
- **Must not decide**：不得自动确认 gold、不得用 holdout 调参。

### Conditional contracts

- **UI**：N/A — 仅 CLI 和文件产物，无交互界面。
- **Externally maintained code**：N/A — 不复制第三方代码；仅调用本地 OpenAI-compatible HTTP 协议。

## 7. Data Model and Lifecycle

- `SimilaritySettings`：`backend` 与可选 `EmbeddingSettings(base_url,model,expected_dimension,calibration_artifact,api_key_env)`；unknown 字段拒绝，密钥值只从 `api_key_env` 指定的环境变量读取。
- `CalibrationArtifact`：公共 13 字段，含不带凭证的规范化 `endpoint_identity`；`metrics.feature_separation` 按 S2/S3 × Jaccard/embedding 保存 count、min、max、quantiles、overlap_count、overlap_rate、margin 并可从 cases 重算；adopted 仅增加 thresholds，not_adopted 禁 thresholds；canonical JSON 用于 hash/replay。
- `BackendResolution`：记录 requested_backend、effective_backend、reason_code、artifact identity；无 artifact、not_adopted、identity mismatch 使用稳定机器码。
- `VectorCacheEntry`：仅 `schema_version|endpoint_identity|model|dimension|probe_fingerprint|input_hash|vector`；identity 错配视为 miss。
- `GoldCase`：lineage/content identity、S2/S3 label、AI draft、confirmed 状态和 label version；未确认不得进入指标。
- 状态流：`draft gold → per-item confirmed → strict split → calibration threshold freeze → holdout evaluation → adopted|not_adopted`；服务不可用分支为 `BLOCKED evidence`，不进入 artifact 状态。
- adopted artifact 任一 identity 变化立即失效；历史 artifact 追加保存，不覆盖。

## 8. API Contract

- `POST {base_url}/embeddings`（`base_url` 已含 `/v1`）；request 为 `model`、`input`；凭证只从环境注入。
- response 必须含与输入数量一致的 data；index 唯一且完整；每个 vector 维度一致、全有限、非零。
- client 禁系统代理和 HTTP redirect；地址只接受 IPv4/IPv6 loopback，或规范化后精确等于 `https://llm.paxszapp.com:443/v1` 的公司内网端点；输入 `https://llm.paxszapp.com/v1` 与显式 `:443` 归一为同一身份，artifact/runtime 复用同一规范化函数比较；后者强制 HTTPS 且不得因重定向改变 scheme/host/port/path。
- 错误只返回稳定 code、批次计数和安全上下文，不回显 input/header/body。
- 兼容性：Jaccard scorer 继续返回当前浮点结果；S2/S3 既有字段保留，仅增加 scorer audit 字段。

## 9. File Boundary

### NEW

- `src/knowledge_digest/embedding.py`
- `src/knowledge_digest/calibration_artifact.py`
- `src/knowledge_digest/corpus_isolation.py`
- `src/knowledge_digest/gold.py`
- `src/knowledge_digest/calibration.py`
- `src/knowledge_digest/calibration_cli.py`
- `scripts/phase4_embedding_acceptance.py`
- `tests/acceptance/test_phase4_embedding_runtime.py`
- `tests/acceptance/test_phase4_gold.py`
- `tests/acceptance/test_phase4_calibration.py`
- `tests/acceptance/test_phase4_embedding_runner.py`

### MODIFY

- `pyproject.toml`
- `src/knowledge_digest/config.py`
- `src/knowledge_digest/text_similarity.py`
- `src/knowledge_digest/cluster.py`
- `src/knowledge_digest/retrieve.py`
- `src/knowledge_digest/pipeline.py`
- `tests/acceptance/test_phase0_digest.py`

### DO NOT TOUCH

- `src/knowledge_digest/draft.py`
- `src/knowledge_digest/provenance.py`
- `src/knowledge_digest/writeback.py`
- `src/knowledge_digest/agentmemory_store.py`
- 公司 Confluence 源目录与正式 KB 正文文件

## 10. Data Flow and Integration

```text
JSON config + adopted artifact → backend resolver → batch embed/cache → one scorer → S2 → S3 → report
isolated corpus + confirmed gold → strict split → calibration thresholds → holdout comparison → artifact or BLOCKED
embedding failure → invalidate S2/S3 decisions → Jaccard scorer → rerun S2 → rerun S3 → single-backend report
```

- **Existing modules / packages / services**：复用 `config.py` 严格 JSON、`text_similarity.py` Jaccard、`cluster.py` complete-linkage、`retrieve.py` top-k、`pipeline.py` 编排、Phase 3 隔离 runner 模式。
- **Integration points**：只改 scorer 参数、配置解析、pipeline S2/S3 边界与两个 console script。
- **Compatibility boundaries**：Jaccard 阈值/排序、S4-S6 输入输出、归档/写回/provenance 不变。
- **Fail-loud behavior**：配置/schema/响应不合法抛 ValidationError 或 typed embedding failure；正式标定证据不足输出明确 not_adopted，服务不可用输出 BLOCKED 且无 artifact。

## 11. Code Anchors and Reuse

### Versioned identity and context projection

- **Spec binding**：`{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"}`
- **read_now**：`config.py:DigestSettings/resolve_settings`、`text_similarity.py:_similarity`、`cluster.py:cluster`、`retrieve.py:retrieve`、`pipeline.py:audit_run`、`cli.py:main`、`pyproject.toml`。
- **must_read_before_task**：Phase 3 runner 和对应 runner tests；`jsonl.py:write_jsonl`；report 初始化/更新路径。
- **Context mode**：Full — 跨配置、S2/S3 编排、独立验收和证据 schema，需完整边界。

### Verified anchors

| Anchor | Path and symbol | Current responsibility | Intended use | Forbidden change |
| --- | --- | --- | --- | --- |
| A-001 | `config.py:DigestSettings` | 扁平阈值配置 | extend | 不破坏旧键 |
| A-002 | `text_similarity.py:_similarity` | Jaccard | reuse | 数值不变 |
| A-003 | `cluster.py:cluster` | complete-linkage S2 | extend | 算法语义不变 |
| A-004 | `retrieve.py:retrieve` | top-k/action S3 | extend | action 规则不变 |
| A-005 | `pipeline.py:audit_run` | S1-S6 编排 | extend | S4-S6 合同不变 |
| A-006 | `scripts/phase3_agentmemory_acceptance.py` | 隔离验收模式 | reference | 不耦合 agentmemory |

### Reuse → Extend → New

| Capability | Decision | Existing candidates | Reason |
| --- | --- | --- | --- |
| Jaccard 与 scorer protocol | extend | A-002 | 在现有 `text_similarity.py` 手术式扩展，避免第二个 similarity 模块 |
| S2/S3 hook | extend | A-003/A-004/A-005 | 最小集成 |
| embedding client | new | 标准库 urllib | 当前不存在 |
| artifact/calibration | new | 严格 JSON/hash 模式 | 当前不存在 |
| isolation runner | extend | A-006 | 复用证明方法 |

### Existing interface signatures

| Signature ID | Object | Verified current signature/schema | Source anchor |
| --- | --- | --- | --- |
| SIG-001 | `cluster` | `(raw_items, run_dir, paths, roots, settings, *, persist_queues=True)` | A-003 |
| SIG-002 | `retrieve` | `(clusters, raw_items, run_dir, paths, roots, settings)` | A-004 |
| SIG-003 | `resolve_settings` | `(config_path, *, top_k, high, medium, max_lines, page_match_threshold, llm_*)` | A-001 |
| SIG-004 | config JSON | strict top-level allowlist with aliases | A-001 |
| SIG-005 | embedding HTTP | OpenAI-compatible `POST /v1/embeddings` | accepted spec |

## 12. Rollback and Recovery

- **Global recovery rule**：保留 accepted spec/plan 和标定历史；撤销当前实现后显式 `backend=jaccard` 即恢复旧运行行为。
- **Irreversible boundaries**：真实公司语料复制/清理、提交、推送、启用 embedding 都需各自明确授权；本计划不执行。
- **Recovery owner**：build-code 修复实现；verify-code 重跑隔离验收；无法证明本地服务或 corpus isolation 时记录 BLOCKED。

### Engineering Risk Handoff

- **PLAN-RISK-001**：公司正文经网络或证据泄漏
  - **Affected IDs**：RISK-03、FR-CONFIG-001、FR-EMBED-001、FR-CORPUS-001、AC-02、AC-03
  - **Trigger**：非 loopback 且不是精确批准的公司内网 HTTPS 端点、代理/重定向生效，或日志/artifact 出现正文/凭证。
  - **Consequence**：公司数据离开受控边界。
  - **Mitigation or STOP**：禁代理/重定向；规范化端点精确校验；敏感扫描不通过立即 STOP，不生成 artifact。
  - **Handling Stage**：build-code
  - **Verification**：故障注入与真实隔离 runner 的 before/after manifest、网络和敏感扫描。

## 13. Test Strategy

- **Target**：FR-CONFIG/EMBED/ARTIFACT；`gate_cmd`：`uv run pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`; RED=2（新模块尚不存在时 pytest collection error），GREEN=0；Phase evidence `evidence/phase4/runtime-contract.txt`；Oracle `KD-P4-CONTRACT` 验证默认零请求、严格响应和 artifact 错配。
- **Target**：FR-SCORE/FALLBACK/COMPAT；`gate_cmd`：`uv run pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`; RED=2（pipeline 尚无 scorer coordinator 时 pytest collection error），GREEN=0；Phase evidence `evidence/phase4/fallback.txt`；Oracle `KD-P4-FALLBACK` 验证 S2/S3 单后端、整轮重跑和现有 digest 兼容回归。
- **Target**：FR-CORPUS-001；`gate_cmd`：`uv run pytest -q tests/acceptance/test_phase4_gold.py`; RED=2（corpus producer 尚不存在时 pytest collection error），GREEN=0；Phase evidence `evidence/phase4/corpus-prep.txt`；Oracle `KD-P4-CORPUS-PREP` 验证 Markdown-only 副本、manifest、只读边界和 cleanup。
- **Target**：FR-GOLD；`gate_cmd`：`uv run pytest -q tests/acceptance/test_phase4_gold.py`; RED=2（gold producer 尚不存在时 pytest collection error），GREEN=0；Phase evidence `evidence/phase4/gold.txt`；Oracle `KD-P4-GOLD` 验证 AI draft exchange、逐项确认和 identity。
- **Target**：FR-CONFIG/SCORE/CAL/ADOPT/REPORT；feature-separation 与阈值候选来源必须从 cases 独立重算；`gate_cmd`：`uv run pytest -q tests/acceptance/test_phase4_calibration.py`; RED=2（calibration domain 尚不存在时 pytest collection error），GREEN=0；`evidence_path`：`evidence/phase4/calibration.txt`；Oracle `KD-P4-CAL` 验证严格 split、feature-separation、阈值候选来源、指标重算、安全门和 replay。
- **Target**：runner 合同与全回归；`gate_cmd`：`uv run pytest -q tests/acceptance/test_phase4_embedding_runner.py && uv run pytest -q`; RED=2（runner 尚不存在时 pytest collection error），GREEN=0；Phase evidence `evidence/phase4/runner-and-regression.txt`；Oracle `KD-P4-RUNNER` 同时证明 runner 合同与全量 pytest 回归。
- **Target**：AC-03/AC-11 正式真实服务；`gate_cmd`：`uv run python scripts/phase4_embedding_acceptance.py --corpus "$KD_CONFLUENCE_CORPUS" --kb "$KD_FORMAL_KB" --temp-root "$KD_PHASE4_TEMP_ROOT" --config "$KD_CONFIG" --evidence-dir "$KD_PHASE4_EVIDENCE_DIR" --cases "$KD_PHASE4_CASES"`; expected_exit=0；evidence `$KD_PHASE4_EVIDENCE_DIR/real-service-acceptance.json`；Oracle `KD-P4-REAL-SERVICE` 证明真实受控服务的端点/模型/维度/探针身份、89 Markdown/排除 2 非 Markdown、源与正式 KB before/after 不变、真实批量评分、replay 和敏感扫描；服务不可用只能 BLOCKED 且不得满足 AC-03/AC-11。
- **Target**：AC-07 manual；检查 `gold-confirmation-audit.json` 的 unconfirmed_count=0 与逐项 identity/decision，再检查 calibration-owned `split-coverage-audit.json` 的 lineage intersection 为空、两集合 strict-cell decidability 完整；证据 `evidence/phase4/gold-manual-audit.json`。

## 14. Implementation Order

先建立配置/client/artifact 的 fail-closed 边界，再接入共享 scorer 与 pipeline fallback；之后实现 calibration domain；最后写真实 corpus runner 和全回归。consumer 不得先于 producer。

## Phase 1：本地服务与绑定合同

### Goal

默认不调用服务；只有合法 loopback/批准的公司内网 HTTPS 配置和完整 adopted artifact 才能构造严格批量 embedding scorer。

### Files

- **NEW**：`src/knowledge_digest/embedding.py`、`src/knowledge_digest/calibration_artifact.py`、`tests/acceptance/test_phase4_embedding_runtime.py`
- **MODIFY**：`src/knowledge_digest/config.py`、`src/knowledge_digest/text_similarity.py`、`tests/acceptance/test_phase0_digest.py`
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Tasks

- T001：写配置、artifact、批量响应、缓存和零请求 RED。
- T002：实现严格 resolver/client/scorer 并保持 Jaccard 兼容。

### Verify

- `uv run pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`；证据 `evidence/phase4/runtime-contract.txt`。

### Knowledge

- 标准库 client 必须显式禁代理/redirect；artifact/cache 精确字段来自 accepted spec。

### STOP

- 无法在请求前证明目标为 loopback 或精确批准的公司内网 HTTPS 端点，或实现需要正文/凭证进入日志。

### Done

- 默认、not_adopted、错配均零请求；合法批次完整消费；非法批次整体拒绝。

### Risks and rollback

- **Risk**：hostname 重绑定或错误泄漏正文。
- **Prevention**：解析后只接受 loopback 或精确批准的公司内网 HTTPS 端点，并覆盖 scheme/host/port/path、代理和重定向负例。
- **Rollback / recovery**：移除 embedding 配置并显式 Jaccard；不动旧算法。

## Phase 2：共享 scorer 与整轮回退

### Goal

S2/S3 共用一个 scorer；任一 embedding 失败作废本轮决策并从 S2 以 Jaccard 重跑。

### Files

- **NEW**：N/A — 本 Phase 只扩展已声明文件。
- **MODIFY**：`tests/acceptance/test_phase4_embedding_runtime.py`、`tests/acceptance/test_phase0_digest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`、`src/knowledge_digest/pipeline.py`
- **DO NOT TOUCH**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/provenance.py`、`src/knowledge_digest/writeback.py`

### Tasks

- T003：写单 scorer、S2/S3 故障和无混合决策 RED。
- T004：注入 scorer，批量预取，并实现 pipeline 从 S2 重跑和 report 审计。

### Verify

- `uv run pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`；证据 `evidence/phase4/fallback.txt`。

### Knowledge

- cluster/retrieve 当前只在 `_similarity` 调用点耦合；pipeline 是整轮重启的唯一正确所有者。

### STOP

- 需要改变 complete-linkage、top-k/action 或 S4-S6 合同，或无法证明最终单后端。

### Done

- Jaccard 回归一致；embedding 成功共用身份；S2/S3 任一失败均从 S2 重跑且缓存可保留。

### Risks and rollback

- **Risk**：首次 embedding 输出已写盘后被下游消费。
- **Prevention**：fallback 在进入 S4 前完成并覆盖 S2/S3 决策，report 记录 discarded attempt。
- **Rollback / recovery**：显式 Jaccard 重跑；保留安全缓存但不消费旧决策。

## Phase 3：标定、gold 与采用门

### Goal

先产出并验证 disposable corpus manifest，证明源语料与正式 KB 只读且 cleanup 可证；再冻结 confirmed gold 和 lineage split，只用 calibration 的 feature-separation 诊断生成并选择阈值，在 holdout 可重算完整指标并生成 adopted/not_adopted。

### Files

- **NEW**：`src/knowledge_digest/corpus_isolation.py`、`src/knowledge_digest/gold.py`、`tests/acceptance/test_phase4_gold.py`、`src/knowledge_digest/calibration.py`、`src/knowledge_digest/calibration_cli.py`、`tests/acceptance/test_phase4_calibration.py`
- **MODIFY**：`pyproject.toml`
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/agentmemory_store.py`

### Tasks

- T005：写 disposable corpus copy/manifest 与只读边界 RED。
- T006：实现 corpus isolation producer。
- T007：写 AI draft exchange、lineage identity 和逐项确认 RED。
- T008：实现 gold draft/confirm CLI 与人工审计产物。
- T009：写 confirmed-only、严格分层、错误差集、安全门和 replay RED。
- T010：实现独立 calibration CLI、阈值冻结、完整 metrics/cases 和 artifact/BLOCKED 分离。

### Verify

- `uv run pytest -q tests/acceptance/test_phase4_gold.py`；证据 `evidence/phase4/gold.txt`，Oracle `KD-P4-GOLD`。
- `uv run pytest -q tests/acceptance/test_phase4_gold.py`；同时覆盖 FR-CORPUS-001，证据 `evidence/phase4/corpus-prep.txt`，Oracle `KD-P4-CORPUS-PREP`。
- `uv run pytest -q tests/acceptance/test_phase4_calibration.py`；证据 `evidence/phase4/calibration.txt`，Oracle `KD-P4-CAL`。
- 人工核对 `gold-confirmation-audit.json` 与 `split-coverage-audit.json` 并保存 `evidence/phase4/gold-manual-audit.json`。

### Knowledge

- feature-separation 固定输出 S2/S3 × Jaccard/embedding 的 count、min、max、quantiles、overlap_count、overlap_rate、margin，并从 cases 重算。
- 阈值冻结算法固定为 `deterministic-positive-median-and-class-midpoint.v1`：`high=S2 embedding positive.p50`；`medium=min(high,(S2 positive.min+S2 negative.max)/2)`；`page_match_threshold=(S3 positive.min+S3 negative.max)/2`。输入 cases 先按 `case_id` 确定性排序；quantile 使用线性插值；不搜索候选、不做十进制 rounding，canonical JSON 直接编码有限 IEEE-754 值；holdout 只评估，冻结后不得改阈值。
- 完整指标固定为 S2 pair P/R/F1、S3 page P/R/F1、S3 action exact accuracy；holdout 不参与选阈值。
- artifact 诊断另记录 Jaccard 与 embedding 在 holdout 的 `auto/needs_review/insufficient_signal` tier 分布，仅用于人工确认 `high` 的影响，不进入 adopted 门。

### STOP

- 任一严格 cell 无可判定样本、任一分母为零、lineage 交集非空或需要自动确认 gold。

### Done

- cases 可重算指标和新增错误差集；重复运行除时间外一致；门槛不足安全地产生 not_adopted。

### Risks and rollback

- **Risk**：阈值搜索偷看 holdout 或少数 cell 缺失。
- **Prevention**：split hash 冻结、两阶段 API 分离、coverage 先验硬校验。
- **Rollback / recovery**：删除未采用推荐配置，保留 not_adopted 诊断和 Jaccard 默认。

## Phase 4：隔离真实服务验收与回归

### Goal

用真实受控服务和 disposable 公司语料副本证明 89 Markdown 边界、无越界外发/无源变更、可重放结论；服务不可用时只 BLOCKED。

### Files

- **NEW**：`scripts/phase4_embedding_acceptance.py`、`tests/acceptance/test_phase4_embedding_runner.py`
- **MODIFY**：N/A — runner 是独立脚本，不需要新增 console entry。
- **DO NOT TOUCH**：公司 Confluence 源目录、正式 KB 正文、`scripts/phase3_agentmemory_acceptance.py`

### Tasks

- T011：写真实 runner 边界、cleanup、BLOCKED/no-artifact 和 replay RED。
- T012：实现 runner，执行真实服务验收、敏感扫描与全回归证据。

### Verify

- `uv run pytest -q tests/acceptance/test_phase4_embedding_runner.py && uv run pytest -q`；证据 `evidence/phase4/runner-and-regression.txt`。

### Knowledge

- 首次正式 corpus 是 89 个 Markdown，排除 2 个非 Markdown；真实服务身份必须可证明，mock 只用于 runner 单测。

### STOP

- 无法证明副本隔离、进程/网络所有权、源/正式 KB before-after manifest 或真实服务身份。

### Done

- runner 可一键重放并清理；真实服务可用则产出 adopted/not_adopted，服务不可用则只有 BLOCKED evidence；全回归通过。

### Risks and rollback

- **Risk**：runner 误写源语料或残留进程/副本。
- **Prevention**：绝对路径、只读源 manifest、临时 HOME/state、子进程 ownership、finally cleanup。
- **Rollback / recovery**：立即停止、不生成 artifact、保留失败证据并清理 disposable 资源。

## 15. Dependencies and Parallelism

- `Phase 1 → Phase 2 → Phase 3 → Phase 4`。
- Phase 1 是 scorer 与 artifact producer；Phase 2 是运行时 consumer；Phase 3 复用 Phase 1 能力；Phase 4 消费全部实现，因此整体串行。
- Phase 内 RED 必须先于 GREEN；不得以并行名义共享同一文件所有权。

## 16. Requirement and Verification Traceability

| FR | Task IDs | AC IDs | Phase | Gate / evidence |
| --- | --- | --- | --- | --- |
| FR-CONFIG-001 | T001,T002,T009,T010 | AC-01,AC-02 | Phase 1,3 | runtime-contract.txt/calibration.txt |
| FR-EMBED-001 | T001,T002,T011,T012 | AC-02,AC-03 | Phase 1,4 | runtime/runner |
| FR-CORPUS-001 | T005,T006,T011,T012 | AC-03 | Phase 3,4 | corpus-prep.txt/real-service |
| FR-GOLD-001 | T007,T008,T009,T010,T011,T012 | AC-05,AC-07 | Phase 3,4 | calibration/runner |
| FR-SCORE-001 | T003,T004,T009,T010 | AC-04,AC-09 | Phase 2,3 | fallback.txt/calibration.txt |
| FR-CAL-001 | T009,T010 | AC-05,AC-10 | Phase 3 | calibration.txt |
| FR-ARTIFACT-001 | T001,T002,T009,T010 | AC-06,AC-10 | Phase 1,3 | runtime/calibration |
| FR-ADOPT-001 | T009,T010,T011,T012 | AC-05,AC-08 | Phase 3,4 | calibration/runner |
| FR-FALLBACK-001 | T003,T004 | AC-09 | Phase 2 | fallback.txt |
| FR-REPORT-001 | T009,T010,T011,T012 | AC-08,AC-11 | Phase 3,4 | calibration/runner |
| FR-COMPAT-001 | T003,T004,T011,T012 | AC-04,AC-12 | Phase 2,4 | fallback/regression |
