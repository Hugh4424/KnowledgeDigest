# 任务清单：本地 embedding 价值标定与安全采用

> 基于 accepted spec 和当前 plan；每个行为先 RED 后 GREEN。

- **Input**：`specs/kd-phase4-embedding-calibration/spec.md`、`specs/kd-phase4-embedding-calibration/plan.md`
- **Status**：Draft
- **Template version**：`plan-task.v3`

## 1. 执行摘要

- **Goal**：交付默认关闭、证据达标后可启用、失败整轮回退的本地 embedding 与可重放标定工具。
- **Main boundary**：只连接 loopback 或精确批准的公司内网 HTTPS 端点；公司正文不进仓库/日志/artifact；S4-S6 不改。
- **Main risk**：错误 artifact 或部分 embedding 决策被当成有效结果。
- **First executable task**：T001。

## 2. Global Constraints

- 显式 Jaccard 永远优先；embedding 需要 adopted artifact 完整匹配。
- 行为改动必须先有真实 RED，再做 GREEN。
- `display_cmd` 不能充当 pass/fail 判据。
- 文件只用精确路径，不用通配符。
- holdout 不调参；BLOCKED 不生成 calibration artifact。

## Phase 1：本地服务与绑定合同

### Goal

默认不调用服务；只有合法 loopback/批准的公司内网 HTTPS 配置和完整 adopted artifact 才能构造严格批量 embedding scorer。

### Files

- **NEW**：`src/knowledge_digest/embedding.py`、`src/knowledge_digest/calibration_artifact.py`、`tests/acceptance/test_phase4_embedding_runtime.py`
- **MODIFY**：`src/knowledge_digest/config.py`、`src/knowledge_digest/text_similarity.py`、`tests/acceptance/test_phase0_digest.py`
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Tasks

#### T001 — RED：本地配置、artifact 与批量响应必须 fail-closed

- **ID**：T001
- **Phase**：Phase 1：本地服务与绑定合同
- **goal**：证明默认/错配零请求，非法 endpoint/artifact/批量响应被整体拒绝。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：FR-CONFIG-001、FR-EMBED-001、FR-ARTIFACT-001；A-001/A-002。
- **依赖**：N/A — first task。
- **并行**：否 — 建立所有 consumer 的安全合同。
- **FR**：FR-CONFIG-001、FR-EMBED-001、FR-ARTIFACT-001
- **AC**：AC-01、AC-02、AC-06
- **动作**：新增 acceptance 断言覆盖精确嵌套 schema、loopback/批准的公司内网 HTTPS 端点、默认端口规范化正负例、密钥环境变量、artifact/cache 和批量响应。
- **精确文件**：`tests/acceptance/test_phase4_embedding_runtime.py`、`tests/acceptance/test_phase0_digest.py`
- **boundary**：files: `tests/acceptance/test_phase4_embedding_runtime.py`, `tests/acceptance/test_phase0_digest.py`; symbols/regions: Phase 4 contract tests only
- **输出**：因目标能力缺失而失败的 RED 证据。
- **Knowledge**：现有 config 顶层严格 allowlist；Jaccard `_similarity` 是基线。
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`
- **expected_exit**：1
- **oracle**：KD-P4-CONTRACT 证明默认/错配零请求；`https://llm.paxszapp.com/v1` 与显式 `:443` 均规范化为精确身份 `https://llm.paxszapp.com:443/v1`，其他 scheme/host/port/path 拒绝；无 artifact、not_adopted、endpoint/model/dimension/probe identity mismatch 分别写稳定 machine-readable `similarity.reason_code`；artifact/cache 都绑定 `endpoint_identity`；`api_key_env` 只保存变量名，密钥值不进入 config/log/error/artifact/cache；代理、redirect、TLS 降级和无效证书被拒绝；非法批次整体拒绝。
- **evidence_path**：`evidence/phase4/t001-red.txt`
- **STOP**：命令损坏、RED 来自环境，或测试要求正文/凭证落盘。
- **recovery**：build-code owner 修正 fixture/断言后重跑，不弱化 accepted contract。
- **task risk**：错误测试可能把外部地址或 partial response 当合法。

#### T002 — GREEN：实现严格 resolver、client、artifact 与 cache

- **ID**：T002
- **Phase**：Phase 1：本地服务与绑定合同
- **goal**：让 KD-P4-CONTRACT 通过并保持现有 Jaccard 数值/配置兼容。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T001 RED；SIG-003/SIG-004；artifact/cache 精确字段。
- **依赖**：T001
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-CONFIG-001、FR-EMBED-001、FR-ARTIFACT-001
- **AC**：AC-01、AC-02、AC-06
- **动作**：实现嵌套配置、runtime resolver 的 `similarity.reason_code`、loopback/公司内网 HTTPS allowlist client、严格 artifact/cache，并在现有 text_similarity 扩展 scorer protocol。
- **精确文件**：`src/knowledge_digest/config.py`、`src/knowledge_digest/text_similarity.py`、`src/knowledge_digest/embedding.py`、`src/knowledge_digest/calibration_artifact.py`
- **boundary**：files: `src/knowledge_digest/config.py`, `src/knowledge_digest/text_similarity.py`, `src/knowledge_digest/embedding.py`, `src/knowledge_digest/calibration_artifact.py`; symbols/regions: config resolution and similarity contracts
- **输出**：安全 resolver/client/scorer 与严格 schema validator。
- **Knowledge**：批量 response 要求 index 完整唯一、维度/finite/非零；错误不得回显请求体。
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`
- **expected_exit**：0
- **oracle**：KD-P4-CONTRACT 全绿；降级 reason code 稳定、错配请求计数为 0、endpoint identity 与密钥保密断言成立、代理/redirect/TLS 负例全绿、Jaccard 旧断言不变。
- **evidence_path**：`evidence/phase4/t002-green.txt`
- **STOP**：需要外部 HTTP 依赖、允许代理/redirect，或破坏旧配置兼容。
- **recovery**：恢复 Jaccard-only resolver，保留 RED 证据，返回 build-plan 处理新依赖。
- **task risk**：URL 规范化、DNS/IPv6 或 redirect 处理不严导致请求越过已批准端点。

### Verify

- **Target**：FR-CONFIG-001、FR-EMBED-001、FR-ARTIFACT-001
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`
- **expected_exit**：0
- **evidence_path**：`evidence/phase4/runtime-contract.txt`
- **display_cmd**：N/A — pytest 输出已足够。
- **Oracle**：KD-P4-CONTRACT 默认零请求、非法批次整体拒绝、schema 错配拒绝。

### Knowledge

- Python 标准库可用自定义 opener 禁代理和 redirect；凭证只从环境读取。

### STOP

- RED 无法因目标断言失败而复现；需要 Phase.Files 外文件或新架构；安全错误会泄露正文。

### Done

- T001/T002 成对证据存在，Jaccard 兼容测试和 Phase 4 合同测试通过。

### Risks and rollback

- **Risk**：网络边界可绕过。
- **Prevention**：请求前地址解析、无代理 opener、redirect 负例。
- **Rollback / recovery**：显式 Jaccard；不构造 embedding client。

## Phase 2：共享 scorer 与整轮回退

### Goal

S2/S3 共用一个 scorer；任一 embedding 失败作废本轮决策并从 S2 以 Jaccard 重跑。

### Files

- **NEW**：N/A — 本 Phase 只扩展已声明文件。
- **MODIFY**：`tests/acceptance/test_phase4_embedding_runtime.py`、`tests/acceptance/test_phase0_digest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`、`src/knowledge_digest/pipeline.py`
- **DO NOT TOUCH**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/provenance.py`、`src/knowledge_digest/writeback.py`

### Tasks

#### T003 — RED：失败后不得保留混合 embedding 决策

- **ID**：T003
- **Phase**：Phase 2：共享 scorer 与整轮回退
- **goal**：证明 S2/S3 共享身份，S2 或 S3 failure 都必须从 S2 统一重跑 Jaccard。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T002 scorer；A-003/A-004/A-005。
- **依赖**：T002
- **并行**：否 — consumer 依赖 Phase 1 producer。
- **FR**：FR-SCORE-001、FR-FALLBACK-001、FR-COMPAT-001
- **AC**：AC-04、AC-09、AC-12
- **动作**：增加 S2/S3 success、S2 failure、S3 failure 的请求/决策/report 审计断言。
- **精确文件**：`tests/acceptance/test_phase4_embedding_runtime.py`、`tests/acceptance/test_phase0_digest.py`
- **boundary**：files: `tests/acceptance/test_phase4_embedding_runtime.py`, `tests/acceptance/test_phase0_digest.py`; symbols/regions: scorer identity, fallback, and existing digest compatibility tests
- **输出**：旧 pipeline 因无法共享/回退而失败的 RED。
- **Knowledge**：fallback 必须在 S4 前完成；有效 cache 可留但旧决策不可留。
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`
- **expected_exit**：1
- **oracle**：KD-P4-FALLBACK 显示最终决策仅一个 backend，failure 后 S2 调用重新发生。
- **evidence_path**：`evidence/phase4/t003-red.txt`
- **STOP**：只能通过混合分数或跳过 S3 故障才能满足断言。
- **recovery**：保留测试，返回设计 owner；不得降为剩余工作 Jaccard。
- **task risk**：只检查 report 标签而未检查实际决策重算。

#### T004 — GREEN：注入 run-scoped scorer 并协调从 S2 重跑

- **ID**：T004
- **Phase**：Phase 2：共享 scorer 与整轮回退
- **goal**：实现批量预取、同 scorer S2/S3 和 typed failure 整轮 Jaccard 重跑。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T003 RED；SIG-001/SIG-002；T002 scorer。
- **依赖**：T003
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-SCORE-001、FR-FALLBACK-001、FR-COMPAT-001
- **AC**：AC-04、AC-09、AC-12
- **动作**：扩展 cluster/retrieve scorer 参数，并在 pipeline 统一管理预取、discard、restart 和 audit。
- **精确文件**：`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`、`src/knowledge_digest/pipeline.py`
- **boundary**：files: `src/knowledge_digest/cluster.py`, `src/knowledge_digest/retrieve.py`, `src/knowledge_digest/pipeline.py`; symbols/regions: S2/S3 invocation and report scorer audit
- **输出**：最终单后端 S2/S3 决策与失败/缓存审计。
- **Knowledge**：complete-linkage/top-k/action 不变；`write_jsonl` 可确定性替换本轮文件。
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`
- **expected_exit**：0
- **oracle**：KD-P4-FALLBACK 全绿且 S2/S3 决策身份一致，无混合分数。
- **evidence_path**：`evidence/phase4/t004-green.txt`
- **STOP**：需改变 S4-S6、complete-linkage 或 action 语义。
- **recovery**：恢复显式 scorer 注入为 Jaccard，保留测试并返回计划处理接口扩大。
- **task risk**：S3 failure 后未清掉首次 S2 产物/queue 副作用。

### Verify

- **Target**：FR-SCORE-001、FR-FALLBACK-001、FR-COMPAT-001
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runtime.py tests/acceptance/test_phase0_digest.py`
- **expected_exit**：0
- **evidence_path**：`evidence/phase4/fallback.txt`
- **display_cmd**：N/A — pytest 输出已足够。
- **Oracle**：KD-P4-FALLBACK 从实际调用/文件证明 S2 重跑、最终单后端和现有 digest 兼容回归。

### Knowledge

- pipeline 是 S2/S3 唯一共同上游；queue 副作用需首次 embedding 尝试禁持久化或延后提交。

### STOP

- 无法让首次尝试无副作用，或需要改动 DO NOT TOUCH 文件。

### Done

- success/failure 路径均有行为证据，既有 S2/S3 输出合同继续通过。

### Risks and rollback

- **Risk**：首次尝试 queue 副作用泄漏。
- **Prevention**：候选运行内存/临时产物，只有最终 scorer 结果持久化。
- **Rollback / recovery**：Jaccard 全轮重跑并重建 run-local S2/S3/queue 结果。

## Phase 3：标定、gold 与采用门

### Goal

先生成并验证 disposable corpus manifest，证明源语料与正式 KB 只读且 cleanup 可证；再冻结 confirmed gold 和 lineage split，只用 calibration 的 feature-separation 诊断生成并选择阈值，在 holdout 可重算完整指标并生成 adopted/not_adopted。

### Files

- **NEW**：`src/knowledge_digest/corpus_isolation.py`、`src/knowledge_digest/gold.py`、`tests/acceptance/test_phase4_gold.py`、`src/knowledge_digest/calibration.py`、`src/knowledge_digest/calibration_cli.py`、`tests/acceptance/test_phase4_calibration.py`
- **MODIFY**：`pyproject.toml`
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/agentmemory_store.py`

### Tasks

#### T005 — RED：disposable corpus copy 必须先于 gold 且保持源只读

- **ID**：T005
- **Phase**：Phase 3：标定、gold 与采用门
- **goal**：证明只复制 Markdown、生成 source/copy manifest 与 corpus_hash，源或正式 KB 变化即失败。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：FR-CORPUS-001、AC-03；显式 source/kb/temp roots。
- **依赖**：T004
- **并行**：否 — 是 gold 和 calibration 的输入 producer。
- **FR**：FR-CORPUS-001
- **AC**：AC-03
- **动作**：新增 disposable copy、Markdown-only manifest、before/after 源与正式 KB 只读断言。
- **精确文件**：`tests/acceptance/test_phase4_gold.py`
- **boundary**：files: `tests/acceptance/test_phase4_gold.py`; symbols/regions: isolated corpus preparation tests
- **输出**：目标 isolation producer 缺失导致的 RED。
- **Knowledge**：合成 fixture 测机制；真实首次验收另要求恰好 89 Markdown、排除 2 非 Markdown。
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_gold.py`
- **expected_exit**：1
- **oracle**：KD-P4-CORPUS-PREP 证明 copy manifest/hash 完整，源与正式 KB before/after 不变，非 Markdown 不复制。
- **evidence_path**：`evidence/phase4/t005-red.txt`
- **STOP**：需要写源/正式 KB、使用相对未解析路径或正文进入 repo fixture。
- **recovery**：删除 disposable copy，保留失败 manifest，修复 isolation producer 后重跑。
- **task risk**：copy 完成前源漂移造成 manifest 与内容错配。

#### T006 — GREEN：实现 corpus isolation producer

- **ID**：T006
- **Phase**：Phase 3：标定、gold 与采用门
- **goal**：在 gold 前产出只读、可验证、可清理的 disposable corpus 与 manifest。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T005 RED；显式 source/kb/temp roots。
- **依赖**：T005
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-CORPUS-001
- **AC**：AC-03
- **动作**：实现 `knowledge-digest-calibrate prepare-corpus`，生成 disposable copy、双 manifest、corpus_hash 和 cleanup metadata。
- **精确文件**：`src/knowledge_digest/corpus_isolation.py`、`src/knowledge_digest/calibration_cli.py`
- **boundary**：files: `src/knowledge_digest/corpus_isolation.py`, `src/knowledge_digest/calibration_cli.py`; symbols/regions: prepare-corpus subcommand and manifest/copy lifecycle
- **输出**：供 T007/T009 消费的 corpus manifest 与 disposable root。
- **Knowledge**：正式 89/2 数量只在 real-service gate 判定，库代码不写死业务绝对路径。
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_gold.py`
- **expected_exit**：0
- **oracle**：KD-P4-CORPUS-PREP 全绿；cleanup 后 disposable 正文不存在，源/正式 KB hash 不变。
- **evidence_path**：`evidence/phase4/t006-green.txt`
- **STOP**：manifest 无法绑定 source/copy 或 cleanup 不能证明完成。
- **recovery**：终止当前准备，清理 owned temp root，不触碰源与正式 KB。
- **task risk**：异常退出残留 disposable 正文。

#### T007 — RED：AI gold 草稿必须逐项确认并绑定 identity

- **ID**：T007
- **Phase**：Phase 3：标定、gold 与采用门
- **goal**：证明未确认项、缺 lineage/content identity、批量确认和外部网络草稿都不能进入正式 gold。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：FR-GOLD-001、AC-07；隔离 corpus manifest 和 AI draft exchange contract。
- **依赖**：T006
- **并行**：否 — gold 是后续 split/metrics 的 authority producer。
- **FR**：FR-GOLD-001
- **AC**：AC-07
- **动作**：新增 AI draft import、逐项 confirm/reject、identity 和 manual audit 的 RED 断言。
- **精确文件**：`tests/acceptance/test_phase4_gold.py`
- **boundary**：files: `tests/acceptance/test_phase4_gold.py`; symbols/regions: gold draft/confirmation contract tests
- **输出**：目标 gold workflow 缺失导致的 RED。
- **Knowledge**：AI 只通过本机隔离文件交换草稿；工具不调用外部 LLM；每项用户决定独立记录。
- **verification_role**：RED
- **paired_task**：T008
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_gold.py`
- **expected_exit**：1
- **oracle**：KD-P4-GOLD 证明 confirmed gold 的 unconfirmed_count=0、identity 完整、逐项 decision 可追溯，未确认项不可被 calibration 读取。
- **evidence_path**：`evidence/phase4/t007-red.txt`
- **STOP**：需要自动确认、批量默认接受或外部网络传输公司正文。
- **recovery**：保留 draft exchange，要求用户逐项补决定；不生成正式 gold。
- **task risk**：把 AI 草稿状态误当用户确认状态。

#### T008 — GREEN：实现本机 gold draft/confirm 子命令 与人工审计

- **ID**：T008
- **Phase**：Phase 3：标定、gold 与采用门
- **goal**：产出绑定 lineage/content identity 的 confirmed gold 和可人工核对的 AC-07 audit。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T007 RED；corpus manifest；AI draft JSONL；逐项用户 reply records。
- **依赖**：T007
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-GOLD-001
- **AC**：AC-07
- **动作**：实现离线 draft exchange/import 和逐项 confirm/reject，生成 confirmed gold 与 confirmation-only `gold-confirmation-audit.json`。
- **精确文件**：`src/knowledge_digest/gold.py`、`src/knowledge_digest/calibration_cli.py`
- **boundary**：files: `src/knowledge_digest/gold.py`, `src/knowledge_digest/calibration_cli.py`; symbols/regions: gold subcommands, identity validation, per-item decision ledger
- **输出**：confirmed gold、逐项决定 ledger 和 confirmation audit。
- **Knowledge**：audit 只含 confirmation-owned 事实：unconfirmed_count、逐项 identity 与 user decision 完整性。
- **verification_role**：GREEN
- **paired_task**：T007
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_gold.py`
- **expected_exit**：0
- **oracle**：KD-P4-GOLD 全绿；人工审计可逐项反查来源 identity 和 user decision。
- **evidence_path**：`evidence/phase4/t008-green.txt`
- **STOP**：缺任一用户逐项决定、identity 错配或 audit 无法反查原 gold case。
- **recovery**：保留未确认草稿，补齐逐项确认后重新冻结 gold_hash。
- **task risk**：修改确认记录后未使 gold_hash/split_hash 失效。

#### T009 — RED：采用门必须由 confirmed gold 和独立 holdout 可重算

- **ID**：T009
- **Phase**：Phase 3：标定、gold 与采用门
- **goal**：证明缺 cell/分母、未确认 gold、lineage 泄漏、缺失或不可重算 feature-separation、阈值无 calibration 来源、指标退化和新增错误都不能 adopted。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：FR-GOLD/CAL/ADOPT/REPORT；T002 artifact/client。
- **依赖**：T008
- **并行**：否 — 标定复用已验证 scorer/artifact。
- **FR**：FR-CONFIG-001、FR-SCORE-001、FR-GOLD-001、FR-CAL-001、FR-ARTIFACT-001、FR-ADOPT-001、FR-REPORT-001
- **AC**：AC-05、AC-06、AC-07、AC-08、AC-10
- **动作**：新增 backend=jaccard 下 calibration-only client/probe、推荐配置写入与显式 Jaccard 不覆盖，以及 strict coverage/split/feature-separation/threshold provenance/metrics/replay RED。
- **精确文件**：`tests/acceptance/test_phase4_calibration.py`
- **boundary**：files: `tests/acceptance/test_phase4_calibration.py`; symbols/regions: calibration domain tests
- **输出**：目标标定域缺失导致的 RED。
- **Knowledge**：S2/S3 完整指标与新增错误集合定义固定；holdout 不调参。
- **verification_role**：RED
- **paired_task**：T010
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_calibration.py`
- **expected_exit**：1
- **oracle**：KD-P4-CAL 证明 feature-separation 与阈值候选来源可从 cases 重算；阈值严格使用 `high=S2 embedding positive.p50`、`medium=min(high,(S2 positive.min+S2 negative.max)/2)`、`page_match_threshold=(S3 positive.min+S3 negative.max)/2`，按 case_id 排序、quantile 线性插值、无十进制 rounding，且 holdout 改动不改变冻结阈值；覆盖不足时 `split-coverage-audit.json` 精确枚举 undecidable strict cells 并得出 not_adopted；backend=jaccard 可用连接字段做真实探针；adopted fresh config 写 backend=embedding；已有显式 Jaccard 文件字节不变；其余安全门可重算。
- **evidence_path**：`evidence/phase4/t009-red.txt`
- **STOP**：fixture 无法让每个严格 cell 在 calibration/holdout 都可判定。
- **recovery**：扩充 synthetic contract fixtures，但不得降低真实 corpus 覆盖门。
- **task risk**：指标实现与测试共用同一错误计算而产生假绿。

#### T010 — GREEN：实现独立 calibration CLI 与 deterministic artifact

- **ID**：T010
- **Phase**：Phase 3：标定、gold 与采用门
- **goal**：实现 confirmed-only、strict split、machine-readable feature-separation、calibration-only 阈值选择、holdout 门和 artifact/BLOCKED 分离。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T009 RED；T002 client/artifact；T004 scorer 行为。
- **依赖**：T009
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-CONFIG-001、FR-SCORE-001、FR-GOLD-001、FR-CAL-001、FR-ARTIFACT-001、FR-ADOPT-001、FR-REPORT-001
- **AC**：AC-05、AC-06、AC-07、AC-08、AC-10
- **动作**：在 Calibration domain 内实现 calibration-only client factory（只复用 `embedding.py` 导出的 client 与 endpoint 规范化函数，不复制校验），实现 feature-separation、`deterministic-positive-median-and-class-midpoint.v1` 阈值冻结、完整 metrics/cases、安全门、artifact/BLOCKED、`split-coverage-audit.json`、holdout tier 分布诊断和安全推荐配置。
- **精确文件**：`src/knowledge_digest/calibration.py`、`src/knowledge_digest/calibration_cli.py`、`pyproject.toml`
- **boundary**：files: `src/knowledge_digest/calibration.py`, `src/knowledge_digest/calibration_cli.py`, `pyproject.toml`; symbols/regions: calibration console entry and domain
- **输出**：含 machine-readable feature-separation、阈值候选来源与 holdout tier 分布诊断的可重放 artifact 或 BLOCKED evidence，以及 calibration-owned split/coverage audit；覆盖不足时 audit 必须精确枚举 undecidable strict cells，作为按证据扩充清单。
- **Knowledge**：gold confirmation audit 是输入；本任务拥有 `split-coverage-audit.json`，记录 lineage intersection、两集合 strict-cell decidability 与 undecidable strict-cell 扩充清单。阈值公式、case_id 排序、quantile 线性插值、无 rounding 和 holdout 只读规则均为冻结合同。
- **verification_role**：GREEN
- **paired_task**：T009
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_calibration.py`
- **expected_exit**：0
- **oracle**：KD-P4-CAL 全绿；cases 可独立重算 feature-separation 且按冻结公式得到同一阈值；覆盖不足的扩充清单精确且结论为 not_adopted；runtime 与 calibration client 构造边界分离，推荐配置两条规则通过，cases 独立重算与 replay 一致。
- **evidence_path**：`evidence/phase4/t010-green.txt`
- **STOP**：实现需要 holdout 调参、自动确认 gold 或生成 BLOCKED artifact。
- **recovery**：固定保持 Jaccard，保存诊断，返回 spec owner 处理任何产品决策变化。
- **task risk**：阈值 tie-break 不确定导致 replay 漂移。

### Verify

- **Target**：FR-GOLD-001；`gate_cmd`：`pytest -q tests/acceptance/test_phase4_gold.py`；`expected_exit`：0；`evidence_path`：`evidence/phase4/gold.txt`；Oracle KD-P4-GOLD。
- **Target**：FR-CORPUS-001；`gate_cmd`：`pytest -q tests/acceptance/test_phase4_gold.py`；`expected_exit`：0；`evidence_path`：`evidence/phase4/corpus-prep.txt`；Oracle KD-P4-CORPUS-PREP。
- **Target**：AC-07 manual；核对 `gold-confirmation-audit.json` 与 calibration-owned `split-coverage-audit.json` 并保存 `evidence/phase4/gold-manual-audit.json`。
- **Target**：FR-CONFIG-001、FR-SCORE-001、FR-CAL-001、FR-ARTIFACT-001、FR-ADOPT-001、FR-REPORT-001
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_calibration.py`
- **expected_exit**：0
- **evidence_path**：`evidence/phase4/calibration.txt`
- **display_cmd**：N/A — pytest 输出已足够。
- **Oracle**：KD-P4-CAL confirmed-only、lineage 隔离、可重算门和 replay 全绿。

### Knowledge

- artifact 公共字段/thresholds 精确 schema 已在 Phase 1 建立；本 Phase 只生产，不重新定义。

### STOP

- 任何 coverage cell 缺失仍想 adopted，或需要未批准的外部 API/mock 作为正式证据。

### Done

- calibration CLI 在冻结输入上可确定重放，安全门所有负例和正例通过。

### Risks and rollback

- **Risk**：浮点/tie-break 引入非确定性。
- **Prevention**：排序键、canonical JSON、阈值候选和 rounding 明确定义并测试。
- **Rollback / recovery**：产出 not_adopted，保留 cases 诊断，不启用 embedding。

## Phase 4：隔离真实服务验收与回归

### Goal

用真实受控服务和 disposable 公司语料副本证明 89 Markdown 边界、无越界外发/无源变更、可重放结论；服务不可用时只 BLOCKED。

### Files

- **NEW**：`scripts/phase4_embedding_acceptance.py`、`tests/acceptance/test_phase4_embedding_runner.py`
- **MODIFY**：N/A — runner 是独立脚本，不需要新增 console entry。
- **DO NOT TOUCH**：公司 Confluence 源目录、正式 KB 正文、`scripts/phase3_agentmemory_acceptance.py`

### Tasks

#### T011 — RED：真实 runner 必须证明 corpus、服务和 cleanup 隔离

- **ID**：T011
- **Phase**：Phase 4：隔离真实服务验收与回归
- **goal**：证明 89 Markdown、排除 2 非 Markdown、before/after manifest、真实服务和 BLOCKED/no-artifact 合同。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T010 CLI；A-006 隔离模式；真实验收边界。
- **依赖**：T010
- **并行**：否 — runner 消费完整工具链。
- **FR**：FR-EMBED-001、FR-CORPUS-001、FR-GOLD-001、FR-ADOPT-001、FR-REPORT-001、FR-COMPAT-001
- **AC**：AC-03、AC-07、AC-08、AC-11、AC-12
- **动作**：新增 runner 合同测试，覆盖临时 HOME/state、进程 ownership、manifest、敏感扫描、replay 和 cleanup。
- **精确文件**：`tests/acceptance/test_phase4_embedding_runner.py`
- **boundary**：files: `tests/acceptance/test_phase4_embedding_runner.py`; symbols/regions: Phase 4 isolated runner contract tests
- **输出**：runner 不存在导致的 RED。
- **Knowledge**：mock 只验证 runner 机制；正式价值结论必须记录真实服务身份。
- **verification_role**：RED
- **paired_task**：T012
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runner.py && pytest -q`
- **expected_exit**：1
- **oracle**：KD-P4-RUNNER 证明源/正式 KB 不变、89/2 边界、服务不可用无 artifact、cleanup 完整。
- **evidence_path**：`evidence/phase4/t011-red.txt`
- **STOP**：测试需读取真实公司正文进入 repo fixture，或无法隔离进程/路径。
- **recovery**：只用合成 fixture 测 runner 机制；真实验收留给显式 corpus 参数。
- **task risk**：只验证端口未验证进程 ownership。

#### T012 — GREEN：实现隔离 runner 并执行 scoped regression

- **ID**：T012
- **Phase**：Phase 4：隔离真实服务验收与回归
- **goal**：实现一键隔离 runner，产出真实 adopted/not_adopted 或 BLOCKED evidence，并保持全回归。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/kd-phase4-embedding-calibration/spec.md","hash":"57a63cb5a5212d359ebd7eb3260f6cdfb3e9aed768d57e3c5be3cf920028dc62","id":"kd-phase4-embedding-calibration"},{"artifact_kind":"plan","ref":"specs/kd-phase4-embedding-calibration/plan.md","hash":"205c7ef996ce6d8bdcf5873d19d0722d7bae885ddfdaec6dbbfbad08581c4aee","id":"kd-phase4-embedding-calibration-plan"}]`
- **输入**：T011 RED；T010 calibration CLI；用户确认的 gold 和显式批准的受控服务/corpus 参数。
- **依赖**：T011
- **并行**：否 — RED/GREEN 和真实资源使用必须串行。
- **FR**：FR-EMBED-001、FR-CORPUS-001、FR-GOLD-001、FR-ADOPT-001、FR-REPORT-001、FR-COMPAT-001
- **AC**：AC-03、AC-07、AC-08、AC-11、AC-12
- **动作**：实现隔离复制、manifest、真实服务身份、敏感扫描、replay、finally cleanup 和 regression orchestration。
- **精确文件**：`scripts/phase4_embedding_acceptance.py`
- **boundary**：files: `scripts/phase4_embedding_acceptance.py`; symbols/regions: Phase 4 acceptance entry only
- **输出**：隔离验收 evidence、可选 artifact、cleanup 证明和 regression 结果。
- **Knowledge**：公司源/正式 KB 只读；所有临时路径绝对化；父子进程和动态端口均需证明。
- **verification_role**：GREEN
- **paired_task**：T011
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runner.py && pytest -q`
- **expected_exit**：0
- **oracle**：KD-P4-RUNNER 全绿；此门只证明 runner 机制和回归。
- **formal_gate_cmd**：`uv run python scripts/phase4_embedding_acceptance.py --corpus "$KD_CONFLUENCE_CORPUS" --kb "$KD_FORMAL_KB" --temp-root "$KD_PHASE4_TEMP_ROOT" --config "$KD_CONFIG" --evidence-dir "$KD_PHASE4_EVIDENCE_DIR" --cases "$KD_PHASE4_CASES"`
- **formal_expected_exit**：0
- **formal_oracle**：KD-P4-REAL-SERVICE 证明真实受控服务的端点/模型/维度/探针身份、89/2 边界、源与正式 KB before/after 不变、replay 与敏感扫描。
- **formal_evidence_path**：`evidence/phase4/real-service-acceptance.json`
- **evidence_path**：`evidence/phase4/t012-green.txt`
- **STOP**：真实语料路径/服务身份不可证明，或 before/after manifest 变化。
- **recovery**：终止 owned child、清理 disposable 副本、保留 BLOCKED/failure evidence，不生成 artifact。
- **task risk**：异常退出残留子进程或临时正文。

### Verify

- **Target**：FR-CORPUS-001、FR-REPORT-001、FR-COMPAT-001
- **gate_cmd**：`pytest -q tests/acceptance/test_phase4_embedding_runner.py && pytest -q`
- **expected_exit**：0
- **evidence_path**：`evidence/phase4/runner-and-regression.txt`
- **display_cmd**：N/A — pytest 输出已足够。
- **Oracle**：KD-P4-RUNNER 同时覆盖 runner 合同与全量 pytest 回归；真实 corpus 结论另有正式 evidence。
- **Target**：AC-03、AC-11 正式真实服务；**gate_cmd**：`uv run python scripts/phase4_embedding_acceptance.py --corpus "$KD_CONFLUENCE_CORPUS" --kb "$KD_FORMAL_KB" --temp-root "$KD_PHASE4_TEMP_ROOT" --config "$KD_CONFIG" --evidence-dir "$KD_PHASE4_EVIDENCE_DIR" --cases "$KD_PHASE4_CASES"`；**expected_exit**：0；**evidence_path**：`$KD_PHASE4_EVIDENCE_DIR/real-service-acceptance.json`；**Oracle**：KD-P4-REAL-SERVICE 证明真实受控服务的端点/模型/维度/探针身份、89/2 边界、源与正式 KB before/after 不变、真实批量评分、replay 与敏感扫描；服务不可用只写 BLOCKED，不能满足 AC-03/AC-11。

### Knowledge

- Phase 3 runner 证明模式可参考但不得耦合 agentmemory；Phase 4 服务只允许 loopback 或精确批准的公司内网 HTTPS embedding。

### STOP

- 无法证明 isolation/cleanup，或 full regression 失败且原因未修复。

### Done

- runner 合同和全回归通过，且 KD-P4-REAL-SERVICE 正式门通过；服务不可用时诚实 BLOCKED，但不算 T012 Done，也不满足 AC-03/AC-11。

### Risks and rollback

- **Risk**：残留临时正文或 owned process。
- **Prevention**：mkdtemp、绝对路径、finally 终止/等待、退出后路径和 PID 审计。
- **Rollback / recovery**：清理 disposable 资源；源/正式 KB 不做恢复性写入。

## 3. Dependency Graph

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012
```

- 全链无环；每个 consumer 只依赖更早 producer。
- 没有 `[P]`：阶段共享配置/scorer/artifact 或同一测试文件，文件所有权不独立。

## 4. Requirement and Verification Traceability

| FR | Task IDs | AC IDs | Phase | Gate / evidence |
| --- | --- | --- | --- | --- |
| FR-CONFIG-001 | T001,T002,T009,T010 | AC-01,AC-02 | Phase 1,3 | KD-P4-CONTRACT/CAL |
| FR-EMBED-001 | T001,T002,T011,T012 | AC-02,AC-03 | Phase 1,4 | contract/runner |
| FR-CORPUS-001 | T005,T006,T011,T012 | AC-03 | Phase 3,4 | CORPUS-PREP/REAL-SERVICE |
| FR-GOLD-001 | T007,T008,T009,T010,T011,T012 | AC-05,AC-07 | Phase 3,4 | CAL/RUNNER |
| FR-SCORE-001 | T003,T004,T009,T010 | AC-04,AC-09 | Phase 2,3 | KD-P4-FALLBACK/CAL |
| FR-CAL-001 | T009,T010 | AC-05,AC-10 | Phase 3 | KD-P4-CAL |
| FR-ARTIFACT-001 | T001,T002,T009,T010 | AC-06,AC-10 | Phase 1,3 | CONTRACT/CAL |
| FR-ADOPT-001 | T009,T010,T011,T012 | AC-05,AC-08 | Phase 3,4 | CAL/RUNNER |
| FR-FALLBACK-001 | T003,T004 | AC-09 | Phase 2 | KD-P4-FALLBACK |
| FR-REPORT-001 | T009,T010,T011,T012 | AC-08,AC-11 | Phase 3,4 | CAL/RUNNER |
| FR-COMPAT-001 | T003,T004,T011,T012 | AC-04,AC-12 | Phase 2,4 | FALLBACK/regression |

## 5. Final Boundary Check

- [x] 每个 Phase 八段完整，Files 与 plan 逐字一致。
- [x] 每个 Task 只有一张权威卡，精确文件属于本 Phase NEW/MODIFY。
- [x] 每个行为变化都有真实 RED → GREEN，命令、oracle 和证据明确。
- [x] DAG 与 FR/Task/AC/gate 双向闭合；每对 RED/GREEN 的 gate_cmd 与 oracle ID 相同，Phase aggregate gate/oracle/evidence 在 plan 和 tasks 一致。
- [x] Plan File Boundary 等于所有 Phase NEW/MODIFY 的并集。
- [x] 每个 Phase NEW/MODIFY 文件至少有一个 owning Task。
- [x] 每个 Task 的精确文件和 boundary 都是所属 Phase NEW/MODIFY 的子集。
- [x] 没有 host identity、固定 artifact root、无关项目规则或未声明文件。
