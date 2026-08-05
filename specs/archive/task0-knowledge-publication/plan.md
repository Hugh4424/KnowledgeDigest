# KnowledgeDigest Task0 实施计划
- **Template version**：`plan-task.v3`

## 1. 速读卡
- **Goal**：在现有 S1–S6 和单写者边界内，实现来源闭环、写前门禁、Reader/Audit 分包、诚实状态、幂等和可审计运行事实。
- **Non-goals**：不迁移历史 Task2，不做 ProductGazetteer/TopicIndex/正文编译/完整读者门，不引入数据库或第二套事实源。来源：`docs/plans/knowledge-digest-knowledge-publication-prd.md` Task0、`specs/task0-knowledge-publication/decision-log.md`。
- **Before**：当前代码存在来源索引与 audit ledger 可能分叉、写回后才检查质量事实、pending 可能为空、状态混用和重跑增长风险。
- **After**：每次新运行先冻结 manifest/snapshot/ledger，写回前完成门禁；Reader 只呈现 allowlist 内容；失败来源隔离为 `degraded`，交付级诚实保持 `not_released`。
- **Main risk**：把历史迁移、产品语义索引或 provider fallback 当成 Task0 成功，会扩大范围或伪造质量事实。
- **Next step**：先执行 Phase 1 的 RED，再按依赖执行 GREEN；完成后跑四阶段 acceptance 和完整测试。

## 2. Technical Context and Constraints
KnowledgeDigest 是本地、人工触发、可恢复的知识消化工具。实现沿用 `src/knowledge_digest` 的 S1–S6 职责和 `pipeline.py` 单写者边界；不把 WorkflowHub、数据库、AgentMemory 或调度器接入正式 pipeline。
### Global Constraints
- 新运行只写当前 Task0 合同；历史 Task2、旧 formal 页面和旧审计证据只读保留。
- `_digest/source-manifest.json` 是 Audit 来源事实源；`indexes/sources.md` 只是 Reader 投影，不得维护第二份来源事实。新运行不再生成 `_digest/source-index.md` 或 `_digest/source-index.jsonl`；历史文件只读保留。
- 页面状态只允许 `published/degraded`，交付状态只允许 `released/not_released`；Task0 输出固定 `not_released`。
- `--no-llm + Jaccard` 必须零 LLM/embedding 网络调用；语义 provider 只允许 PRD 约定的 `qwen3.6` 和 `jina-embeddings`；fallback、预算和凭据安全必须可审计。
- 先补能复现问题的 RED，再做最小 GREEN；所有失败必须 fail-closed，不能用运行记录或 fallback 掩盖。
- 阶段 Verify 使用项目真实命令 `uv run --frozen pytest -q ...`；任务卡的 `gate_cmd` 记录其可执行内层 `python -m pytest -q ...`，以符合 WorkflowHub 的命令字段校验，实际执行必须置于同一 `uv run --frozen` 环境。

## 3. Code Anchors and Reuse
- `src/knowledge_digest/ingest.py`：复用本地快照、来源指纹和输入校验边界。
- `src/knowledge_digest/batch_run.py`：复用批次状态和运行报告边界，不扩展为调度器。
- `src/knowledge_digest/provenance.py`：复用 Claim/Evidence/source locator 关系，补齐 manifest/ledger 对账。
- `src/knowledge_digest/writeback.py`、`pipeline.py`：复用归档后原子写回和单写者入口，把门禁前移。
- `src/knowledge_digest/navigation.py`、`page_layout.py`：复用 Home、分类、主题页和来源入口渲染，不生成第二份来源事实；`pipeline.py` 负责停止新运行的旧 source-index 投影。
- `src/knowledge_digest/kb_structure.py`：迁移新运行的默认来源入口和现有结构调用方；旧 `_digest/source-index.md`、`_digest/source-index.jsonl` 只按历史只读路径解析。
- `src/knowledge_digest/draft.py`、`publication.py`：复用现有草稿、fallback 和发布元数据校验入口，补审计字段，不新增发布服务。
- `src/knowledge_digest/draft.py`、`publication.py`：复用 provider/fallback 和语义事实校验，不改变 qwen3.6/jina-embeddings allowlist。
- `config/knowledge-digest.json`：只读核对既有 embedding endpoint、model、dimension、calibration artifact 路径和凭据环境变量。
- `evidence/phase4/real-service-acceptance.json`、`evidence/phase4/calibration-artifact.json`：只读核对 DEC-004 的 provider identity、probe fingerprint 和 calibration hash；Task0 不修改这些历史证据。

## 4. Solution Design
1. 先由 ingest 冻结唯一来源集合、稳定 ID、URI、相对路径、内容指纹和 `validated_at`；batch_run 绑定运行 snapshot/config，provenance 在内存中组装 `source_audit_ledger` 并与 manifest 逐项对账。
2. pipeline 在任何持久化 `_digest` append（包括 source snapshot、duplicate、ledger）、`write_queues`、归档和 `writeback(...)` 之前串起 Claim、`source_audit_ledger`、路径、状态和 allowlist 的 fail-closed 门禁；任一失败不产生新 formal 页面或改变 `_queues`。具体 Reader 投影和导航链接检查留给 Phase 3。
3. navigation/page_layout 只从 `published` 页面生成 Reader Package；真实、非空、可导航待处理项才生成 pending；失败来源留在 Audit/Archive。
4. draft/publication/pipeline 把 provider transport、fallback、预算、endpoint、embedding 维度、probe/calibration hash 和凭据来源写入审计事实；题集 manifest 固定 17+3 题，离线基线零网络调用。

## 5. File Boundary
### MODIFY
- **MODIFY**：`src/knowledge_digest/ingest.py`
- **MODIFY**：`src/knowledge_digest/batch_run.py`
- **MODIFY**：`src/knowledge_digest/provenance.py`
- **MODIFY**：`src/knowledge_digest/writeback.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`
- **MODIFY**：`src/knowledge_digest/publication.py`
- **MODIFY**：`src/knowledge_digest/navigation.py`
- **MODIFY**：`src/knowledge_digest/page_layout.py`
- **MODIFY**：`src/knowledge_digest/kb_structure.py`
- **MODIFY**：`src/knowledge_digest/draft.py`
- **MODIFY**：`tests/acceptance/test_publication_contract.py`
- **MODIFY**：`tests/acceptance/test_task2_publication.py`
### NEW
- **NEW**：`tests/acceptance/test_task0_manifest_contract.py`
- **NEW**：`tests/acceptance/test_task0_writeback_gate.py`
- **NEW**：`tests/acceptance/test_task0_reader_package.py`
- **NEW**：`tests/acceptance/test_task0_runtime_audit.py`
- **NEW**：`config/task0-question-set.v1.json`
### DO NOT TOUCH
- **DO NOT TOUCH**：`specs/archive/`
- **DO NOT TOUCH**：历史 Task2 输出、旧 `_digest/source-index.md`、旧 `_digest/source-index.jsonl` 和旧审计报告
- **DO NOT TOUCH**：provider 凭据、WorkflowHub 全局配置和项目外运行时
- **READ ONLY**：`config/knowledge-digest.json`、`evidence/phase4/real-service-acceptance.json`、`evidence/phase4/calibration-artifact.json`；它们只作为 DEC-004 的既有事实来源。

## 6. Technical Decisions
### DEC-001：唯一来源事实源
- **Selected**：复用现有 S1–S6 和单写者结构，只把 `_digest/source-manifest.json` 设为来源事实源，`indexes/sources.md` 只做投影。
- **F10 real threat**：第二份来源索引或运行顺序导致事实分叉。
- **F10 existing cover**：现有 ingest、provenance、navigation 分层和 acceptance 测试。
- **F10 bypassable**：写回前 manifest/snapshot/ledger 对账与路径 allowlist 会阻止分叉结果发布。
- **F10 maintenance cost**：只增加现有模块的对账和投影断言，不新增服务或存储层。

### DEC-002：状态与失败边界
- **Selected**：保留独立 provider、Claim、writeback、page、delivery 和人工证据；来源级失败进入 `degraded`，整包在 Task0 为 `not_released`。
- **F10 real threat**：provider 或写回成功被误写成知识质量发布成功。
- **F10 existing cover**：现有 draft/publication/writeback 状态字段与 fail-closed 测试边界。
- **F10 bypassable**：AC-004、AC-007 和 AC-010 分别检查状态独立、旧页保护和 fallback/预算失败。
- **F10 maintenance cost**：沿用当前状态对象，不增加新的全局状态机。

### DEC-003：Reader/Audit 交付边界
- **Selected**：用正向 Reader allowlist 加 Audit/Archive 事实包；不靠目录排除，不生成新的 `_digest/source-index.md` 或 `_digest/source-index.jsonl`。
- **F10 real threat**：审计现场、provider 原始响应或 `_queues` 混入 Reader。
- **F10 existing cover**：现有 navigation/page_layout 的导航渲染和写回原子事务。
- **F10 bypassable**：AC-005/AC-006 的 allowlist、空入口、断链和来源可定位检查。
- **F10 maintenance cost**：复用现有导航文件，不新增索引服务或复制事实。

### DEC-004：Task0 实现参数冻结
- **Selected**：将 17+3 题集固定在一份 `config/task0-question-set.v1.json` manifest；运行审计的 provider/status/budget 参数在本计划冻结，由 T007/T008 逐项断言并写入既有 manifest/status/audit，不新增第二份运行配置。改变题集语义、provider 或预算必须回到 `make-decision`。
- **Question-set fields**：`schema_version`、`question_set_id`、`questions[].question_id`、`polarity`、`original_text`、`entry_path`、`expected_topic_or_product`、`covered_roles`、`negative_design`、`sample_seed`、`reviewer`、`question_set_hash`、`derivation_rules`。
- **Question-set source**：题目从 PRD 的 Task 2/Task 3 读者验收要求和 `specs/task0-knowledge-publication/decision-log.md` 决定 9 派生；实现者可以整理原文，但必须按 `derivation_rules` 记录这两个权威来源，不能现场无依据发明题集语义。
- **Replay values**：`sample_seed` 固定为 `knowledge-digest-task0-v1`；`reviewer` 固定为 `task3-independent-human-reviewer` 这一预注册角色，Task 3 再记录实际姓名/日期；不得用本次实现者作为唯一评审人。
- **Hash**：对 `schema_version`、`question_set_id`、`questions` 和 `derivation_rules` 组成的 canonical UTF-8 JSON 计算 lowercase SHA-256；对象键按字典序排序、去空白、不包含末尾换行，明确排除 `question_set_hash` 字段本身。
- **Status fields**：`provider_transport`、`claim_verification`、`written`、`writeback`、`machine_pass`、`agent_assisted`、`human_reviewed`、`page_status`、`delivery_status`、`fallback`、`reason`、`budget_status`。
- **Provider/fallback**：`qwen3.6` at `https://dashscope.in.whatspos.cn/v1`；`jina-embeddings` 的 canonical audit endpoint 为 `https://llm.paxszapp.com/v1`；离线 fallback backend `jaccard`。qwen3.6 由 `src/knowledge_digest/llm.py:43-44` 核对；embedding endpoint/model/dimension/env/path 由 `config/knowledge-digest.json:5-9` 核对。
- **Embedding endpoint normalization**：读取配置和历史证据时保留原始值；比较前将 scheme/host 转小写、去掉 HTTPS 默认端口 `:443`、保留 `/v1`，得到 canonical `https://llm.paxszapp.com/v1`。T007 必须同时断言原始值和归一化相等；T008 的 `embedding_endpoint` 只写 canonical 值，`endpoint_identity_raw` 如需保留必须是独立审计字段。
- **Embedding identity**：`evidence/phase4/real-service-acceptance.json:1` 是 dimension `1024`、model `jina-embeddings`、endpoint identity `https://llm.paxszapp.com:443/v1` 和 probe fingerprint `cc7ae744e79a19a32ca64d3274e11b3e2ea0611cf4c0f58cebc49e950fc6ed2c` 的 service identity 事实源；`evidence/phase4/calibration-artifact.json:1` 只提供 calibration 文件的 canonical SHA-256 `c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06`。两者都只读。
- **Budgets**：单请求 timeout `180s`；拆分 replay 上限 `1`；provider call budget 为 `4 × manifest.source_count`，planned generator call hard cap `180`；wall-clock target `1800s`，hard cap `3600s`。任一超限写入失败事实，不得生成成功事实。
- **F10 real threat**：实现阶段自行改题集、provider 或预算，导致验收不可重放。
- **F10 existing cover**：Task0 manifest、config、运行报告和 acceptance gate。
- **F10 bypassable**：T007/T008 对字段、hash、allowlist、身份指纹和预算逐项断言，并绑定 AC-008/AC-010。
- **F10 maintenance cost**：只增加一份小型题集 manifest 和既有审计字段，不新增第二份运行配置、配置服务或数据库。

## 7. Test Strategy
- RED 先验证失败原因是目标合同而不是测试装置；GREEN 使用同一 gate command 和同一 oracle identity。oracle 同时写明 RED 的预期失败和 GREEN 的同一断言以 exit 0 通过，避免把失败文字误当成 GREEN 成功标准。
- 每个阶段必须列出本阶段的精确文件；同一模块允许按依赖在后续阶段被串行复触，但必须在对应任务卡重新声明边界并重跑受影响门禁，禁止并行碰同一文件。
- 重点测试来源集合变化、写前失败、单来源降级、Reader allowlist、真实 pending、重跑幂等、旧页恢复、离线零调用、fallback/预算和 17+3 manifest；T007/T008 必须断言 DEC-004 的具体值。
- 完成阶段后运行 `uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_task0_runtime_audit.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`，再运行 `uv run --frozen pytest -q`。

## 8. Rollback and Recovery
失败时只撤销当前 Task0 代码和测试变更；不删除历史输出、旧审计记录或 WorkflowHub 证据。若归档或原子写回失败，保留旧 formal 页面并让本次 run 明确失败；若发现历史迁移、语义产品索引或 provider 凭据写入范围，立即 STOP，回到 make-decision。
### Engineering Risk Handoff
- **PLAN-RISK-001**：来源闭环不一致。
- **Affected IDs**：FR-KD-001, FR-KD-002, FR-KD-009, AC-001, AC-002。
- **Trigger**：manifest、snapshot、ledger 的集合、指纹或重复运行计数不一致；异常增长定位属于 Phase 4 的独立审计事实。
  - **Consequence**：无法证明来源闭环，可能重复发布或漏来源。
  - **Mitigation or STOP**：停止写回，保留 audit 事实；只修复现有 ingest/provenance/batch_run 边界。
  - **Handling Stage**：build-code。
  - **Verification**：Phase 1 acceptance 与同 snapshot 两次运行报告。

- **PLAN-RISK-002**：Reader 污染或旧页覆盖。
  - **Affected IDs**：FR-KD-003, FR-KD-005, FR-KD-006, FR-KD-007, FR-KD-008, FR-KD-010, AC-003, AC-004, AC-005, AC-006, AC-007。
  - **Trigger**：门禁晚于 writeback、allowlist 漏 `_queues`、或失败路径覆盖旧 formal 页面。
  - **Consequence**：读者看到审计现场或历史结果丢失。
  - **Mitigation or STOP**：STOP；归档先行，阻断本次 formal 写回；恢复旧页面并保留映射事实。
  - **Handling Stage**：build-code。
  - **Verification**：Phase 2/3 acceptance、归档恢复测试和 Reader allowlist 检查。

- **PLAN-RISK-003**：语义调用不诚实。
  - **Affected IDs**：FR-KD-004, FR-KD-011, FR-KD-012, AC-004, AC-008, AC-010。
  - **Trigger**：fallback/预算/endpoint/凭据边界缺失或 `--no-llm` 仍触网。
  - **Consequence**：把非语义结果误判为语义发布成功，或泄露凭据。
  - **Mitigation or STOP**：停止语义发布；保留明确 fallback/not_released 事实，凭据只从环境变量读取。
  - **Handling Stage**：build-code。
  - **Verification**：Phase 4 acceptance、离线调用计数和 provider 审计字段检查。

## 9. Implementation Order
Phase 1 → Phase 2 → Phase 3 → Phase 4；每个 Phase 内 RED → GREEN。Phase 1 先冻结事实源，Phase 2 才允许写回，Phase 3 才生成 Reader 投影，Phase 4 最后接入语义/离线/题集审计。

## Phase 1：来源闭环与幂等
### Goal
建立 manifest、snapshot、ledger 的单一来源闭环，并让同一 snapshot/config 重跑不重复增长业务结果。
### Files
- **MODIFY**：`src/knowledge_digest/ingest.py`
- **MODIFY**：`src/knowledge_digest/batch_run.py`
- **MODIFY**：`src/knowledge_digest/provenance.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`
- **NEW**：`tests/acceptance/test_task0_manifest_contract.py`
### Tasks
T001 RED → T002 GREEN。
### Verify
`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
### Knowledge
现有 S1 ingest、S6 provenance 和 batch_run 已提供快照、指纹和运行报告边界。
### STOP
来源集合、稳定 ID 或历史保护要求出现变化时停止，不在实现中猜测。
### Done
AC-001 的固定输入断言通过；T001/T002 只建立 AC-002 的来源关系幂等前提，archive 不增长由 Phase 2 关闭，异常增长定位由 Phase 4 的 AC-009 完成。
### Risks and rollback
只撤销本 Phase 修改；旧来源记录和历史审计证据保留。

## Phase 2：写前门禁与原子写回
### Goal
在 writeback 前完成 Claim、provenance、路径、状态和 allowlist 的 fail-closed 门禁，保护旧 formal 页面；具体 Reader/Audit 内容和导航链接完整性留给 Phase 3。
### Files
- **MODIFY**：`src/knowledge_digest/writeback.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`
- **MODIFY**：`src/knowledge_digest/provenance.py`
- **MODIFY**：`src/knowledge_digest/publication.py`
- **NEW**：`tests/acceptance/test_task0_writeback_gate.py`
### Tasks
T003 RED → T004 GREEN。
### Verify
`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
### Knowledge
现有 writeback 已有归档和单写者边界；本 Phase 在 `provenance.py` 新增 `source_audit_ledger` 对账与 `validate_prewrite_provenance`，由 pipeline 在任何 source snapshot/duplicate/ledger 持久化、`write_queues`、归档和 `writeback(...)` 之前调用；`audit_provenance` 仍在成功写回后记录 claim lineage。相同稳定页路径、写前内容 SHA、snapshot/config 身份已存在时，writeback 不追加重复 archive 内容或 archive 记录；运行审计记录仍可追加。本 Phase 只调整门禁顺序和事实分层。
### STOP
任一失败在 writeback 后才暴露，或无关页面被回滚时停止。
### Done
AC-001 的写回前无 formal 页面子项、AC-002 的 archive 不增长断言、AC-003、AC-004、AC-007 的故障注入和旧页恢复断言通过。
### Risks and rollback
归档先行；写回失败时恢复旧 formal 页面，不删除 audit。

## Phase 3：Reader/Audit 导航与来源投影
### Goal
生成干净 Reader Package 和可定位 Audit/Archive Package，确保 Home、分类、主题页、来源入口无空入口和断链。
### Files
- **MODIFY**：`src/knowledge_digest/navigation.py`
- **MODIFY**：`src/knowledge_digest/page_layout.py`
- **MODIFY**：`src/knowledge_digest/kb_structure.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`
- **MODIFY**：`tests/acceptance/test_publication_contract.py`
- **MODIFY**：`tests/acceptance/test_task2_publication.py`
- **NEW**：`tests/acceptance/test_task0_reader_package.py`
### Tasks
T005 RED → T006 GREEN。
### Verify
`uv run --frozen pytest -q tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
### Knowledge
现有导航入口是 Home、分类页和主题页；新运行只增加 `indexes/sources.md` 投影。`pipeline._write_source_index` 不再生成新的 `_digest/source-index.md` 或 `_digest/source-index.jsonl`；两者历史文件不迁移、不重写，只保留只读兼容路径；`source-manifest.json` 是唯一 Audit 事实源。
### STOP
产品/模块语义索引、历史迁移或审计现场进入 Reader 时停止并回到 make-decision。
### Done
AC-005、AC-006、AC-007 的 allowlist、真实 pending、空页、断链、来源定位、旧路径映射、历史保护以及停止两个旧 source-index 新写入的断言通过。
### Risks and rollback
只撤销导航投影改动；保留旧 formal 页面和旧入口历史。

## Phase 4：离线、语义 fallback、题集与运行审计
### Goal
冻结 17+3 题集和运行 manifest，记录 provider/fallback/预算安全事实，保证离线零网络调用。
### Files
- **MODIFY**：`src/knowledge_digest/draft.py`
- **MODIFY**：`src/knowledge_digest/publication.py`
- **MODIFY**：`src/knowledge_digest/batch_run.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`
- **NEW**：`config/task0-question-set.v1.json`
- **NEW**：`tests/acceptance/test_task0_runtime_audit.py`
### Tasks
T007 RED → T008 GREEN。
### Verify
`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_task0_runtime_audit.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
### Knowledge
现有 provider allowlist、Jaccard 和 qwen3.6/jina-embeddings 约定可复用；本 Phase 不引入 provider。
DEC-004 已冻结题集 manifest 路径、字段、canonical SHA-256、状态字段、provider/model/endpoint、1024 维 embedding、probe/calibration hash、180 秒 timeout、1 次 replay、4×来源数调用预算、180 次 planned generator hard cap、1800/3600 秒 wall-clock；T007 RED 先从只读 config/phase4 evidence 核对既有参数和 hash，T008 再把核对后的值写入 manifest/status/audit 并逐项映射 AC-008/AC-010。
### STOP
出现凭据落盘、离线触网、预算超限仍成功、题集缺项或 Task0 试图做读者门时停止。
### Done
AC-004、AC-008、AC-009、AC-010 的运行字段、题集 hash、fallback 和调用计数断言通过。
### Risks and rollback
撤销本 Phase 的审计字段和测试变更；不删除已存在的历史 run 记录。

## 10. Dependencies and Parallelism
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008。所有任务串行；同一 Phase 的 RED/GREEN 共享 gate command 和 oracle，不能并行。

## 11. Requirement and Verification Traceability
| FR | Task IDs | AC IDs | Phase | Gate / evidence |
|---|---|---|---|---|
| FR-KD-001 | T001,T002,T003,T004 | AC-001 | Phase 1/2 | manifest/snapshot/ledger 对账与写回前无 formal 页面 |
| FR-KD-002 | T001,T002,T005,T006 | AC-001,AC-005 | Phase 1/3 | source-manifest 与 sources 投影 |
| FR-KD-003 | T003,T004 | AC-003,AC-007 | Phase 2 | writeback 前门禁 |
| FR-KD-004 | T003,T004,T007,T008 | AC-004,AC-010 | Phase 2/4 | 独立状态与运行事实 |
| FR-KD-005 | T003,T004,T005,T006 | AC-004 (Phase 2), AC-006 (Phase 3) | Phase 2/3 | 来源级 degraded 隔离 |
| FR-KD-006 | T003,T004,T007,T008 | AC-004,AC-010 | Phase 2/4 | page/delivery 状态 |
| FR-KD-007 | T003,T004,T005,T006 | AC-005 | Phase 2/3 | allowlist 包检查 |
| FR-KD-008 | T005,T006 | AC-005,AC-006,AC-007 | Phase 3 | 导航和历史保护 |
| FR-KD-009 | T001,T002,T003,T004 | AC-002 | Phase 1/2 | source/Claim/duplicate/history/page/archive 关系重跑幂等，运行记录可追加 |
| FR-KD-010 | T003,T004,T005,T006 | AC-003,AC-007 | Phase 2/3 | archive-before-writeback 与旧路径映射 |
| FR-KD-011 | T007,T008 | AC-008,AC-010 | Phase 4 | 离线/fallback/预算 |
| FR-KD-012 | T007,T008 | AC-008 | Phase 4 | 17+3 manifest |
| FR-KD-013 | T007,T008 | AC-009 | Phase 4 | 异常增长定位 |

## 12. Governance Synchronization Matrix
| Governance surface | Actual files | Change / no change | Task IDs | Reason |
|---|---|---|---|---|
| Current product code | `src/knowledge_digest` | change | T002,T004,T006,T008 | 只改四个已声明职责边界 |
| Acceptance regression | `tests/acceptance` | change | T001,T003,T005,T007 | RED/GREEN 和逐 AC 证据 |
| Reader/Audit contract | `CONTEXT.md` | no change | none | 已在 make-decision/build-spec 冻结 |
| WorkflowHub evidence | task records | no change | none | 由正式 runtime 生成，不进产品目录 |
| Historical outputs | `_digest`, `_archive` | no change | none | 用户选择历史只读保护 |

## 13. Constitution Check
- **Constitution binding**：`{"artifact_kind":"constitution","ref":"constitution-checklist.md","hash":"368817c2910a36e63d3ab4642c30270abdecef15dee7caf8050e778f095919ca","id":"CONSTITUTION","version":"1.5.0","clause_count":21}`
- F1 薄核心：沿用 S1–S6 和单写者，不增加服务层。
- F2 事实可追溯：manifest、snapshot、ledger、Claim、Evidence 和页面关系可定位。
- F3 入口边界：Reader/Audit allowlist 分开，失败不进 Reader。
- F4 失败显式：门禁失败不产生新 formal 页面，不伪造 released。
- F5 安全边界：凭据只从环境变量读取，不写日志、报告或知识库。
- F6 变更最小：只改已声明模块和 acceptance 测试。
- F7 可恢复：archive-before-writeback，旧页可恢复。
- F8 验收诚实：逐 AC、RED/GREEN、独立审查和用户确认分别记录。
- F9 外部操作隔离：不提交、推送、合并、归档或清理。
- F10 自动化收益：只增加能证明来源、状态和安全边界的测试。
- Q1 质量事实不作准入证：审查记录不替代测试、逐 AC 和交接事实。
- Q2 完成事实可复核：命令、oracle、evidence path 和 run 记录可核对。
- Q3 真实执行：测试命令使用项目真实 `uv run --frozen pytest`。
- S1 复用现有模块：不新造第二套 pipeline 或索引服务。
- S2 小改动：按阶段和文件边界拆分，禁止跨阶段大改。
- S3 单一事实源：source-manifest 是 Audit 唯一来源事实，sources.md 仅投影。
- S4 可回滚：每阶段只撤销当前 bytes，历史产物保留。
- S5 可观察：失败原因、状态、预算和增长报告都落审计事实。
- S6 依赖明确：任务依赖和阶段门禁形成无环顺序。
- S7 人工确认：build-plan 正式确认由用户回答，不能由文件或 review 代替。
- S8 交付边界：本阶段只交 plan/tasks，不做 commit/push/merge。
