# 任务清单：KnowledgeDigest Task2 知识发布架构

> 基于已审计的 spec 与 plan；行为必须先 RED 后 GREEN。此文件是 build-code 的唯一完成权威。

- **Input spec**：`specs/knowledge-digest-llm-naming-classification/spec.md`
- **Spec SHA-256**：`f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42`
- **Input plan**：`specs/knowledge-digest-llm-naming-classification/plan.md`
- **Plan SHA-256**：`0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae`
- **Status**：Phase 1–5 implementation complete；corrective closure r9 complete；integration review and verify-code pending
- **Template version**：`plan-task.v3`

## 1. 执行规则

- 89 篇 Task2 运行只写新的隔离 KB；`/Users/Hugh/Downloads/KnowledgeDigest-offline-architecture-verified-5Ng5LpvP` 只读。
- qwen3.6/jina-embeddings 使用现有环境配置；禁止 DeepSeek 和其他 provider。
- 行为任务必须由目标缺口触发 RED，再由最小实现变为 GREEN；环境错误不算 RED。
- 每个任务的 `exact_files`、Phase Files、gate、oracle、evidence_path 和完成区不可省略。
- `display_cmd` 不作为判定；真实语料失败必须保留现场，不用 fallback 掩盖失败。

## 2. Phase 1：Taxonomy 与数据合同

### Goal

固定 parent/leaf/pending taxonomy、topic-index/source-index schema 和旧 KB fail-closed 边界；PublicationMetadata/field_refs 归 Phase 2 单一实现。

### Files

- **NEW**：`tests/acceptance/test_task2_publication.py`
- **MODIFY**：`src/knowledge_digest/kb_structure.py`、`tests/acceptance/test_publication_contract.py`
- **DO NOT TOUCH**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Verify

`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py tests/acceptance/test_publication_contract.py`；oracle：`KD-T2-TAXONOMY`。

### Knowledge

`PublicationContract`/`inspect_structure` 是现有解析入口；父分类无目录，叶分类独占目录，pending 不计入 Other。

### STOP

需要并行 taxonomy、自动迁移旧 KB、目录 overlap 或触碰 S1–S3。

### Done

合法 taxonomy、topic-index、source-index 可被后续模块读取；source-index 使用固定 Markdown 表格序列化，不产生并行 JSON；旧 publication tests 仍通过。

### Risks and rollback

风险是旧 parser 回归；保留旧 fixtures，若失败只撤回 schema 扩展，不迁移旧 KB。

### T001 — RED：taxonomy 与旧结构失败合同

- **ID / phase**：T001 / Phase 1
- **design_state**：ready
- **inputs**：spec SCOPE-002/AC-001/006、现有 PublicationContract
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T002
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：缺 taxonomy_version、parent/topic_dir overlap、重复叶分类、非法 pending、旧结构迁移均明确失败。
- **dependencies / paired_task**：无 / T002
- **FR / AC**：SCOPE-002 / AC-001、AC-006
- **action**：写 negative fixtures 和行为断言。
- **exact_files**：`tests/acceptance/test_task2_publication.py`
- **boundary**：只新增 taxonomy/structure tests，不修改 parser 或 S1–S3。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k taxonomy` / `1`
- **oracle**：失败原因必须是 `KD-T2-TAXONOMY` 缺失 gate，不能是 collection/import error。
- **evidence_path**：`evidence/build-code/task2/T001-red.txt`
- **STOP**：RED 不是目标行为失败，或需要触碰 DO NOT TOUCH 文件/自动迁移旧 KB。
- **recovery**：保留测试，回到 Phase 1 重新确认合同。
- **risk**：把 pending 错算进 Other，造成假通过。
- **completion**：`status=pending`；actual_changes/evidence_refs/completed_at 由执行者填写。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 taxonomy/旧结构负向断言，并补充 legacy source-index fail-closed 断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py -k 'taxonomy or schema or source_index or structure'`（RED exit 1；GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase1-r2-red.json`；`receipts/tests/phase1-r2-green.json`；`evidence/phases/phase-1-r3/379f5f487b73a229f06925bc619447c81af2342f/phase-map-trace-4856d5a8606fbe2a37a87f5ca422ff22f6a16cba2de2ced720f397bb27fb2e27.json`。
- **covered_ac**：AC-001、AC-003、AC-006。
- **review_fact**：Phase `phase-1-r3` 使用配置路由 `kimi/coding + cursor/grok`，semantic `pass`；前一轮发现的问题已修复。
- **completed_at**：2026-08-03T17:31:00+08:00

### T002 — GREEN：实现 taxonomy/旧结构校验

- **ID / phase**：T002 / Phase 1
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T001
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：让 T001 通过；新空 KB 初始化完整叶 taxonomy、parent_id、pending；旧缺 version fail-closed。
- **dependencies / paired_task**：T001 / T001
- **FR / AC**：SCOPE-002 / AC-001、AC-006
- **action**：扩展 `kb_structure.py` parser/validator/initializer，并保留旧结构安全门。
- **exact_files**：`src/knowledge_digest/kb_structure.py`、`tests/acceptance/test_publication_contract.py`
- **boundary**：只改 PublicationContract parser/init 和对应兼容测试。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k taxonomy` / `0`
- **oracle**：`KD-T2-TAXONOMY` 合法结构通过，缺 version/overlap/重复项失败。
- **evidence_path**：`evidence/build-code/task2/T002-green.txt`
- **STOP**：需要第二份 taxonomy 配置或弱化路径安全。
- **recovery**：撤回 parser 扩展，不迁移旧 KB。
- **risk**：frontmatter 列表解析造成旧 fixture 回归。
- **completion**：`status=pending`；填写实际修改、命令、证据和时间。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：扩展 `kb_structure.py` taxonomy parent/leaf/pending 合同、版本字段和结构安全校验；修复缩进回归。
- **executed_commands**：同 T001 RED/GREEN focused command；旧 publication contract 全量通过。
- **evidence_refs**：`receipts/tests/phase1-r2-red.json`；`receipts/tests/phase1-r2-green.json`；`reviews/results/build-code-default-379f5f487b73a229f06925bc619447c81af2342f-d5667f40-be9b-4026-85bf-c65e5d68b710.json`。
- **covered_ac**：AC-001、AC-006。
- **review_fact**：Phase `phase-1-r3` semantic `pass`；configured reviewer set `kimi/coding + cursor/grok`，2/2 valid。
- **completed_at**：2026-08-03T17:31:00+08:00

### T003 — RED：topic-index/source-index schema

- **ID / phase**：T003 / Phase 1
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T004
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：缺失/非法 topic-index、source-index schema 明确失败；PublicationMetadata/field_refs 留给 Phase 2。
- **dependencies / paired_task**：T002 / T004
- **FR / AC**：SCOPE-002、SCOPE-003 / AC-003、AC-004
- **action**：新增 topic-index/source-index negative fixtures，断言 source-index Markdown 固定列与内部 entries schema 一致。
- **exact_files**：`tests/acceptance/test_task2_publication.py`
- **boundary**：只写 schema/invariant tests。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k schema` / `1`
- **oracle**：`KD-T2-TAXONOMY`；失败来自 schema，不是环境。
- **evidence_path**：`evidence/build-code/task2/T003-red.txt`
- **STOP**：无法形成单一 schema 或需要数据库。
- **recovery**：保持测试，回到 spec/plan，不猜字段。
- **risk**：schema 过宽让非法索引进入写回。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 topic-index/source-index 结构化 schema 断言、固定 Markdown 表头和重复来源拒绝断言。
- **executed_commands**：同 T001 RED/GREEN focused command（schema/source-index 子集 RED exit 1；GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase1-r2-red.json`；`receipts/tests/phase1-r2-green.json`；`evidence/phases/phase-1-r3/379f5f487b73a229f06925bc619447c81af2342f/phase-evidence-05a093f9c22e08ea00125225f4eabba0a82645ae3348898b13f421cff5a58676.json`。
- **covered_ac**：AC-003、AC-004。
- **review_fact**：Phase `phase-1-r3` semantic `pass`；审查要求的 canonical receipt 已绑定。
- **completed_at**：2026-08-03T17:31:00+08:00

### T004 — GREEN：实现 metadata/topic/source index schema

- **ID / phase**：T004 / Phase 1
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T003
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：让 T003 通过，并提供后续模块可消费的 topic-index/source-index typed validation helpers；不实现 PublicationMetadata/field_refs。
- **dependencies / paired_task**：T003 / T003
- **FR / AC**：SCOPE-002、SCOPE-003 / AC-003、AC-004
- **action**：实现 topic-index/source-index validators 和结构化记录；不负责落盘，不复制 publication schema。
- **exact_files**：`src/knowledge_digest/kb_structure.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：只改 schema helpers。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k schema` / `0`
- **oracle**：`KD-T2-TAXONOMY`；合法记录通过，非法字段拒绝。
- **evidence_path**：`evidence/build-code/task2/T004-green.txt`
- **STOP**：validator 取代 writeback 安全门。
- **recovery**：撤回 helper，保留结构 parser。
- **risk**：helper 与正式记录格式漂移。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：实现 topic-index/source-index validator、固定 Markdown serializer/parser、内容 fingerprint/status/path fail-closed 校验；legacy link list 明确拒绝。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py -k 'taxonomy or schema or source_index or structure'`（4 个目标测试通过）。
- **evidence_refs**：`receipts/tests/phase1-r2-green.json`；`reviews/reports/d5667f40-be9b-4026-85bf-c65e5d68b710.md`；`evidence/phases/phase-1-r3/379f5f487b73a229f06925bc619447c81af2342f/phase-map-trace-4856d5a8606fbe2a37a87f5ca422ff22f6a16cba2de2ced720f397bb27fb2e27.json`。
- **covered_ac**：AC-003、AC-004。
- **review_fact**：Phase `phase-1-r3` semantic `pass`；没有 DeepSeek 或产品运行时 LLM 调用。
- **completed_at**：2026-08-03T17:31:00+08:00

## 3. Phase 2：语义建议与回退

### Goal

复用既有 generator response 携带可选 publication object；qwen allowlist、180 秒 deadline、输出上限和字段级 Claim/Evidence 校验必须 fail-closed，失败只影响当前来源/批次。

### Files

- **NEW**：`src/knowledge_digest/publication.py`
- **MODIFY**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/llm.py`、`tests/acceptance/test_task2_publication.py`
- **DO NOT TOUCH**：`src/knowledge_digest/faithfulness.py`

### Verify

`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k "pub_object or provider_contract"`；oracle：`KD-T2-SEMANTIC`。

### Knowledge

`llm.py` 已有 bounded request、spawn/hard deadline 和 final content parser；本 Phase 只做向后兼容扩展。

### STOP

需要第二次 semantic call、DeepSeek fallback、改变 faithfulness 或把失败伪装成成功。

### Done

validated metadata 可供 layout 消费；失败来源明确 needs-review，成功来源不受影响。

### Risks and rollback

风险是截断 JSON 或字段重复正文；用 output cap、field_refs 和 malformed fixtures 防护，必要时关闭 publication object。

### T005 — RED：publication object/field_refs 合同

- **ID / phase**：T005 / Phase 2
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T006
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：缺 publication object、非法 title/category/summary/why/version、field_refs 越界时失败。
- **dependencies / paired_task**：T004 / T006
- **FR / AC**：FR-LLM-001/002/003 / AC-002、AC-003
- **action**：fake generator response fixtures 和字段级断言。
- **exact_files**：`tests/acceptance/test_task2_publication.py`
- **boundary**：只写 publication schema/Claim ref tests。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k pub_object` / `1`
- **oracle**：`KD-T2-SEMANTIC`；RED 必须暴露现有 generator 无 publication contract。
- **evidence_path**：`evidence/build-code/task2/T005-red.txt`
- **STOP**：需要第二次 semantic provider call。
- **recovery**：保留 fixture，退回 T004 schema。
- **risk**：把生成字段当事实而没有 Evidence 回指。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 publication object、field_refs、Claim 绑定和缺失/非法输入的 fail-closed RED 合同；补充修复回归断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k 'pub_object or provider_contract or allowed_taxonomy'`（初次 RED exit 1；修复后 GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase2-red.json`；`receipts/tests/phase2-r1-red.json`；`receipts/tests/phase2-r1-green.json`；`evidence/phases/phase-2-r1/15491fbc629260edeacdd5465422ac65b72c53b3/phase-map-trace-e07aa6e69bc840e620d7115a9251733ac2e439cfa6ccd5f8647c6fb71b29f9e0.json`。
- **covered_ac**：AC-002、AC-003、AC-006。
- **review_fact**：Phase `phase-2-r1` 使用配置路由 `kimi/coding + cursor/grok`，2/2 valid，semantic `pass`；首轮 revise_required 已按测试修复。
- **completed_at**：2026-08-03T18:15:30+08:00

### T006 — GREEN：实现 publication metadata 校验

- **ID / phase**：T006 / Phase 2
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T005
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：合法 publication 建议通过；缺失/非法字段确定性 fallback 并标 needs-review；Claim/正文不丢。
- **dependencies / paired_task**：T005 / T005
- **FR / AC**：FR-LLM-001/002/003 / AC-002、AC-003
- **action**：新增 `publication.py`，扩展 `draft.py` 消费可选 object。
- **exact_files**：`src/knowledge_digest/publication.py`、`src/knowledge_digest/draft.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：不生成事实、不写文件、不改 faithfulness。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k pub_object` / `0`
- **oracle**：`KD-T2-SEMANTIC`；字段 fallback 有原因，合法字段保留 refs。
- **evidence_path**：`evidence/build-code/task2/T006-green.txt`
- **STOP**：Publication module 决定最终路径、权限或 Claim 主体。
- **recovery**：禁用 publication object，恢复既有 deterministic fields。
- **risk**：fallback 文案重复正文或丢数字/标识符。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `publication.py`，扩展 `draft.py` 消费可选 publication object，并保留 Claim/正文；回退字段统一显式 missing markers，不生成臆造 Why/Summary，不暴露未使用 product_slug。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k 'pub_object or provider_contract or allowed_taxonomy'`（5 passed）。
- **evidence_refs**：`receipts/tests/phase2-green.json`；`receipts/tests/phase2-r1-green.json`；`reviews/results/build-code-default-15491fbc629260edeacdd5465422ac65b72c53b3-e9d74fa4-c66e-452d-9d6d-946a35b072f4.json`；`evidence/phases/phase-2-r1/15491fbc629260edeacdd5465422ac65b72c53b3/phase-evidence-8ca19915b2427c93ab174261f55cc5e3492bf0a9fa8cf6543c70f66f6ab256c0.json`。
- **covered_ac**：AC-002、AC-003、AC-006。
- **review_fact**：配置路由 `kimi/coding + cursor/grok`，2/2 valid，semantic `pass`。
- **completed_at**：2026-08-03T18:15:30+08:00

### T007 — RED：provider allowlist、malformed JSON、预算和 no-LLM

- **ID / phase**：T007 / Phase 2
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T008
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：DeepSeek/其他 provider、截断 JSON、超过 180 planned calls、请求超时、`--no-llm`、混用 embedding/Jaccard 和 cache identity 缺口被测试并暴露。
- **dependencies / paired_task**：T006 / T008
- **FR / AC**：FR-LLM-003/004/005 / AC-005、AC-006、AC-008
- **action**：fake transport、malformed response、budget/no-call、backend-mixing 和 cache-key fixtures；请求 payload 断言四段提示词。
- **exact_files**：`tests/acceptance/test_task2_publication.py`
- **boundary**：不访问真实网络，不修改 provider 配置。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k provider` / `1`
- **oracle**：`KD-T2-SEMANTIC`；失败必须来自 allowlist/deadline/budget/no-call/prompt/backend 缺口。
- **evidence_path**：`evidence/build-code/task2/T007-red.txt`
- **STOP**：需要 DeepSeek fallback、无限 retry 或放宽 fail-closed。
- **recovery**：保留 fake fixtures，回到 T006。
- **risk**：provider transport 成功被误当作合法语义输出。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 qwen-only provider identity、semantic prompt 四段约束和 focused provider/no-LLM RED 合同；没有真实网络调用或 DeepSeek fallback。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k 'pub_object or provider_contract or allowed_taxonomy'`（初次 RED exit 1；修复后 GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase2-red.json`；`receipts/tests/phase2-r1-red.json`；`receipts/tests/phase2-r1-green.json`；`evidence/phases/phase-2-r1/15491fbc629260edeacdd5465422ac65b72c53b3/phase-map-trace-e07aa6e69bc840e620d7115a9251733ac2e439cfa6ccd5f8647c6fb71b29f9e0.json`。
- **covered_ac**：AC-005、AC-006、AC-008。
- **review_fact**：Phase `phase-2-r1` 配置路由 `kimi/coding + cursor/grok`，2/2 valid，semantic `pass`。
- **completed_at**：2026-08-03T18:15:30+08:00

### T008 — GREEN：实现 provider 边界与确定性回退

- **ID / phase**：T008 / Phase 2
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T007
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：只允许 qwen3.6；180 秒 hard deadline/max output；budget 超限先停；失败来源确定性发布并 needs-review；no-LLM 请求数为 0；请求含 `ROLE/EVIDENCE/ALLOWED TAXONOMY/OUTPUT SCHEMA` 四段；embedding 不可用整次回退 Jaccard，cache key 绑定 endpoint/model/dimension/probe/text hash。
- **dependencies / paired_task**：T007 / T007
- **FR / AC**：FR-LLM-003/004/005 / AC-005、AC-006、AC-008
- **action**：最小扩展 `llm.py`/`draft.py`，复用现有请求和最终 content 解析；补 prompt 四段、backend 一致性和 cache-key 断言。
- **exact_files**：`src/knowledge_digest/llm.py`、`src/knowledge_digest/draft.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：不切换 provider，不读取 reasoning_content，不修改 faithfulness。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k provider` / `0`
- **oracle**：`KD-T2-SEMANTIC`；禁止 provider 明确失败，失败来源不污染成功来源；混用 backend、缺任一 cache 身份字段或缺 prompt 段均失败。
- **evidence_path**：`evidence/build-code/task2/T008-green.txt`
- **STOP**：需要第二次语义请求或把失败伪装成成功。
- **recovery**：关闭 publication extension，保留旧 generator 合同。
- **risk**：超时处理破坏 macOS spawn/硬 deadline。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：复用现有 hard deadline/final content parser；禁止 DeepSeek/其他 provider，移除无用 embedding 常量，fallback 保留 needs-review 和 Claim refs。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k 'pub_object or provider_contract or allowed_taxonomy'`（5 passed）。
- **evidence_refs**：`receipts/tests/phase2-green.json`；`receipts/tests/phase2-r1-green.json`；`reviews/reports/e9d74fa4-c66e-452d-9d6d-946a35b072f4.md`；`evidence/phases/phase-2-r1/15491fbc629260edeacdd5465422ac65b72c53b3/phase-evidence-8ca19915b2427c93ab174261f55cc5e3492bf0a9fa8cf6543c70f66f6ab256c0.json`。
- **covered_ac**：AC-005、AC-006、AC-008。
- **review_fact**：配置路由 `kimi/coding + cursor/grok`，2/2 valid，semantic `pass`。
- **completed_at**：2026-08-03T18:15:30+08:00

## 4. Phase 3：Identity、布局和导航

### Goal

用 topic-index 锁稳定 topic/category/path，先完整聚合再分页；生成 README、Home、父/叶索引、Products product_slug 分组、related links 和 source-index records。

### Files

- **NEW**：`src/knowledge_digest/navigation.py`
- **MODIFY**：`src/knowledge_digest/identity.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task2_publication.py`
- **DO NOT TOUCH**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Verify

`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k "identity or layout or navigation"`；oracle：`KD-T2-NAV`。

### Knowledge

`build_topic_layouts` 已有 aggregate/split，`identity.py` 已有 source-derived ID，导航只消费已验证 records。

### STOP

需要 cluster-N/draft-N 作为正式路径、删除旧 part、复制全文到 source-index 或改变 taxonomy。

### Done

主题页、README、Home、父/叶分类、source-index 和 related links 可被同批 writeback 接受。

### Risks and rollback

风险是标题变化导致路径漂移和孤儿链接；topic-index lock、ASCII fallback、collision tests 失败即回滚布局/导航变更。

### T009 — RED：topic-index、ASCII slug、collision、首路径锁

- **ID / phase**：T009 / Phase 3
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T010
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：输入顺序/标题变化、新来源、非 ASCII 标题、同 slug 碰撞时暴露路径漂移或覆盖缺口。
- **dependencies / paired_task**：T008 / T010
- **FR / AC**：SCOPE-001 / AC-002、AC-004
- **action**：identity fixtures，固定 topic-index schema 和重复运行断言。
- **exact_files**：`tests/acceptance/test_task2_publication.py`
- **boundary**：只写 identity/path tests。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k identity` / `1`
- **oracle**：`KD-T2-NAV`；失败来自路径未锁/ASCII/collision 缺口。
- **evidence_path**：`evidence/build-code/task2/T009-red.txt`
- **STOP**：需要以 cluster-N/draft-N 作为正式路径，或自动移动旧 path。
- **recovery**：保留 fixtures，回到 Phase 2 输出合同。
- **risk**：同 slug 覆盖不同主题。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增稳定 topic identity 的 RED fixtures，覆盖 ASCII slug、collision、输入顺序/标题变化与首路径锁定缺口。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k identity`（RED exit 1；GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase3-red.json`（sha256 `2abf62ca11207ac805a328372f262784ee9f7f1519f2a70413077aee0c9ad692`）；`receipts/tests/phase3-green.json`（sha256 `874785e30ebed9c9b0db7f1d2c774890ba6a8bda53d262920e65a497db59f7ad`）；`evidence/phases/phase-3-r1/52cadf50ebcf7c3398ce1c66a557c55bfd445aec/phase-map-trace-eea887d0899ff1cdb35bdf489a7d963182f62d98f31bf60d9126283d9c1f23da.json`。
- **covered_ac**：AC-002、AC-004。
- **review_fact**：Phase `phase-3-r1` 独立复审使用配置路由 `kimi/coding + cursor/grok`，semantic `pass`；本任务的 identity 行为同时由 focused GREEN 覆盖，最终集成复审再核对整条发布链。
- **completed_at**：2026-08-03T18:43:40+08:00

### T010 — GREEN：实现稳定 topic identity/path

- **ID / phase**：T010 / Phase 3
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T009
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：topic-index 锁 source_ids/category/path；slug ASCII；冲突追加稳定 ID；标题/输入顺序改变不漂移。
- **dependencies / paired_task**：T009 / T009
- **FR / AC**：SCOPE-001 / AC-002、AC-004
- **action**：扩展 `identity.py`，不依赖运行 cluster/draft 编号。
- **exact_files**：`src/knowledge_digest/identity.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：不改变 S1–S3 或删除旧 part。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k identity` / `0`
- **oracle**：`KD-T2-NAV`；首次 path/category 锁定，冲突 needs-review。
- **evidence_path**：`evidence/build-code/task2/T010-green.txt`
- **STOP**：identity helper 重新用输入顺序生成正式路径。
- **recovery**：恢复旧 path resolver，保留 topic-index fixture。
- **risk**：现有 `publication_topic_part_path` 兼容性回归。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：`identity.py` 实现稳定 topic/category/path 解析、ASCII-only slug、collision 稳定后缀与已发布首路径锁；不依赖 cluster-N/draft-N。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k identity`（5 个 identity 断言通过）。
- **evidence_refs**：`receipts/tests/phase3-green.json`（sha256 `874785e30ebed9c9b0db7f1d2c774890ba6a8bda53d262920e65a497db59f7ad`）；`receipts/tests/phase3-r1-green.json`（sha256 `a824cd4a9a5131e05767e5f875e5ff6031767bd980df5ec5724c2d2332231fca`）；`evidence/phases/phase-3-r1/52cadf50ebcf7c3398ce1c66a557c55bfd445aec/phase-evidence-41c534a91ba63fc8acc920bf91b1382f02b641e7b0982ddf4f1c5e5828cc0c82.json`。
- **covered_ac**：AC-002、AC-004。
- **review_fact**：Phase `phase-3-r1` 配置路由 `kimi/coding + cursor/grok`，semantic `pass`；identity 通过 focused GREEN，未将其错误归因到本次导航 diff。
- **completed_at**：2026-08-03T18:43:40+08:00

### T011 — RED：最终聚合、分页和 header consistency

- **ID / phase**：T011 / Phase 3
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T012
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：跨批聚合、300 行上限、Claim 单 part、header/category/path 一致性缺口先失败。
- **dependencies / paired_task**：T010 / T012
- **FR / AC**：SCOPE-003 / AC-003、AC-004
- **action**：构造跨批重复/更新/巨页 fixtures。
- **exact_files**：`tests/acceptance/test_task2_publication.py`
- **boundary**：只写 layout assertions。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k layout` / `1`
- **oracle**：`KD-T2-NAV`；RED 必须对应多页/唯一 Claim/头部一致性缺口。
- **evidence_path**：`evidence/build-code/task2/T011-red.txt`
- **STOP**：通过删除旧 part 或丢弃重复 Claim 让测试通过。
- **recovery**：保留失败 fixture，回到 identity/layout 设计。
- **risk**：跨批更新留下幽灵正文。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增跨批聚合、300 行分页、Claim 单 part 与 header/category/path consistency 的 RED fixtures。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k layout`（RED exit 1；GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase3-layout-red.json`（sha256 `10e4ce0acaf9f75c17c175b10d30b2aeb358b72df2c04ba20233d9e261569392`）；`receipts/tests/phase3-layout-green.json`（sha256 `6e7f61f6103d0c4bdfdd2d8efc3ae4ca5763bda0e974d388dcc4f36f48177bfb`）；`receipts/tests/phase3-r1-green.json`（sha256 `a824cd4a9a5131e05767e5f875e5ff6031767bd980df5ec5724c2d2332231fca`）。
- **covered_ac**：AC-003、AC-004。
- **review_fact**：Phase `phase-3-r1` 独立复审 semantic `pass`，并保留 layout focused RED/GREEN 证据；最终集成复审再验证写回链。
- **completed_at**：2026-08-03T18:43:40+08:00

### T012 — GREEN：实现最终聚合分页

- **ID / phase**：T012 / Phase 3
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T011
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：先合并完整主题证据再分页；每页 ≤300 行；每个有效 Claim 一个当前 part；header/category/path 与 topic-index 一致。
- **dependencies / paired_task**：T011 / T011
- **FR / AC**：SCOPE-003 / AC-003、AC-004
- **action**：扩展 `page_layout.py`，保留旧 part 归档、不删除。
- **exact_files**：`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：不负责导航写入或 provider 调用。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k layout` / `0`
- **oracle**：`KD-T2-NAV`；无巨页、无孤儿 Claim、无头部错配。
- **evidence_path**：`evidence/build-code/task2/T012-green.txt`
- **STOP**：需要重写 S1–S3 或删除历史 part。
- **recovery**：回退布局函数，旧归档保持可读。
- **risk**：行数计算遗漏 fenced code/Provenance。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：`page_layout.py` 先完成主题聚合再分页，保留稳定 topic metadata/header 与旧 part 归档语义；导航入口改为薄委托。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k layout`（布局 focused GREEN 通过）。
- **evidence_refs**：`receipts/tests/phase3-layout-green.json`（sha256 `6e7f61f6103d0c4bdfdd2d8efc3ae4ca5763bda0e974d388dcc4f36f48177bfb`）；`receipts/tests/phase3-r1-green.json`（sha256 `a824cd4a9a5131e05767e5f875e5ff6031767bd980df5ec5724c2d2332231fca`）；`evidence/phases/phase-3-r1/52cadf50ebcf7c3398ce1c66a557c55bfd445aec/phase-evidence-41c534a91ba63fc8acc920bf91b1382f02b641e7b0982ddf4f1c5e5828cc0c82.json`。
- **covered_ac**：AC-003、AC-004。
- **review_fact**：Phase `phase-3-r1` 使用 `kimi/coding + cursor/grok`，semantic `pass`；本次 review 明确只把导航 diff 作为修复审查对象，未虚报 layout 变更覆盖。
- **completed_at**：2026-08-03T18:43:40+08:00

### T013 — RED：README/Home/分类/source-index/related links

- **ID / phase**：T013 / Phase 3
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T014
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：读者入口缺根 README、父/叶层级、Products 分组、最多三跳、source-index backlink 时失败。
- **dependencies / paired_task**：T012 / T014
- **FR / AC**：SCOPE-003 / AC-001、AC-003、AC-004
- **action**：navigation negative fixtures，包含 unknown related topic、source-index orphan、固定 Markdown 表格列和重复导航生成来源。
- **exact_files**：`tests/acceptance/test_task2_publication.py`
- **boundary**：只写导航记录/链接测试。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k navigation` / `1`
- **oracle**：`KD-T2-NAV`；失败来自入口/链接/分层/source-index 序列化/重复生成来源缺口。
- **evidence_path**：`evidence/build-code/task2/T013-red.txt`
- **STOP**：把所有页面继续放入 `pages/digest` 或复制全文到 source-index。
- **recovery**：保留 fixtures，回到 navigation contract。
- **risk**：Home 只列本批新主题，旧合法托管主题变孤儿。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 navigation RED fixtures，覆盖 README/Home、父/叶分类、Products 分组、source-index、related links、unknown ID 和重复导航来源。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k navigation`（RED exit 1；修复后 GREEN 通过）。
- **evidence_refs**：`receipts/tests/phase3-nav-red.json`（sha256 `7d765d44ce36cac89ef1b1f0f8f34764fbffd6f9299b1e7374e8e6cd6b2e1e85`）；`receipts/tests/phase3-r1-green.json`（sha256 `a824cd4a9a5131e05767e5f875e5ff6031767bd980df5ec5724c2d2332231fca`）；`reviews/results/build-code-default-52cadf50ebcf7c3398ce1c66a557c55bfd445aec-409582f8-370c-4106-889a-971f9217b529.json`（sha256 `affeafb07c90a6baaf0cb285aff6b86b15c2750087488c0303fb662886e72bcf`）。
- **covered_ac**：AC-001、AC-004。
- **review_fact**：Phase `phase-3-r1` 配置路由 `kimi/coding + cursor/grok`，2/2 valid，semantic `pass`；修复了前一轮发现的重复 renderer、flat fallback 丢索引和相对路径锚点问题。
- **completed_at**：2026-08-03T18:43:40+08:00

### T014 — GREEN：实现语义导航记录

- **ID / phase**：T014 / Phase 3
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T013
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：生成根 README、Home、父/叶索引、Products product_slug 分组、source-index 和合法 related links；把既有 `page_layout.build_publication_navigation` 收敛为到 `navigation.py` 的薄委托。
- **dependencies / paired_task**：T013 / T013
- **FR / AC**：SCOPE-003 / AC-001、AC-003、AC-004
- **action**：新增 `navigation.py`，只渲染已验证 records。
- **exact_files**：`src/knowledge_digest/navigation.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：只允许 `page_layout.py` 保留薄委托并切换唯一调用方；不决定事实、Claim、taxonomy 或 identity；未知 related ID 丢弃并 needs-review。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k navigation` / `0`
- **oracle**：`KD-T2-NAV`；Home→parent→leaf→topic ≤3 跳，source-index 可回溯。
- **evidence_path**：`evidence/build-code/task2/T014-green.txt`
- **STOP**：导航复制整篇原文或引入第二 taxonomy。
- **recovery**：回退导航 records，保留主题页和 topic-index。
- **risk**：parent index 汇总时路径链接错误。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 `navigation.py` 单一只读 renderer；`page_layout.py` 仅保留薄委托；生成 README/Home/父叶分类/Products 分组/source-index/related records，过滤未知 related ID，保持 source-index 紧凑不复制 Evidence。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py -k 'identity or layout or navigation'`（5 passed）。
- **evidence_refs**：`receipts/tests/phase3-r1-green.json`（sha256 `a824cd4a9a5131e05767e5f875e5ff6031767bd980df5ec5724c2d2332231fca`）；`evidence/phases/phase-3-r1/52cadf50ebcf7c3398ce1c66a557c55bfd445aec/phase-evidence-41c534a91ba63fc8acc920bf91b1382f02b641e7b0982ddf4f1c5e5828cc0c82.json`；`evidence/phases/phase-3-r1/52cadf50ebcf7c3398ce1c66a557c55bfd445aec/phase-map-trace-eea887d0899ff1cdb35bdf489a7d963182f62d98f31bf60d9126283d9c1f23da.json`；`reviews/results/build-code-default-52cadf50ebcf7c3398ce1c66a557c55bfd445aec-409582f8-370c-4106-889a-971f9217b529.json`（sha256 `affeafb07c90a6baaf0cb285aff6b86b15c2750087488c0303fb662886e72bcf`）。
- **covered_ac**：AC-001、AC-003、AC-004。
- **review_fact**：Phase `phase-3-r1` 独立 semantic review `pass`，配置路由 `kimi/coding + cursor/grok`，2/2 valid；前一轮 `revise_required` 已完成修复并保留其审计记录。
- **completed_at**：2026-08-03T18:43:40+08:00

## 5. Phase 4：Pipeline、写回与批次恢复

### Goal

把 metadata/layout/navigation/source-index/provenance 放入同一 archive-before-write；state v3 支持成功 checkpoint、split_from、budget 和恢复。

### Files

- **NEW**：`tests/acceptance/test_task2_batch_recovery.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/provenance.py`
- **DO NOT TOUCH**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Verify

`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py`；oracle：`KD-T2-RECOVERY`。

### Knowledge

`writeback.py` 已有 archive/safe-relative boundary；`batch_run.py` 当前 state 需要升级为 v3，不引入 scheduler。

### STOP

需要数据库/CAS/journal、删除旧 part、绕过 writeback 或修改 S1–S3。

### Done

source-index 与导航同批安全发布；成功批可恢复，失败批可拆分，变更清单拒绝续跑。

### Risks and rollback

风险是多文件部分写入留下孤儿导航；failure injection 和旧快照恢复失败即回到旧 writeback/state 路径。

### T015 — RED：single-writer/source-index 事务

- **ID / phase**：T015 / Phase 4
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T016
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：source-index 写失败、Home/主题多文件失败和 archive-before-write 不一致先失败。
- **dependencies / paired_task**：T014 / T016
- **FR / AC**：SCOPE-003 / AC-004、AC-005、AC-008
- **action**：failure injection 和旧 index/旧页面保留断言。
- **exact_files**：`tests/acceptance/test_task2_batch_recovery.py`
- **boundary**：只测试 writeback transaction，不修改生产写回。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k transaction` / `1`
- **oracle**：`KD-T2-RECOVERY`；失败来自 source-index/staged publish 缺口。
- **evidence_path**：`evidence/build-code/task2/T015-red.txt`
- **STOP**：用直接写文件或删除旧 index 掩盖失败。
- **recovery**：保留注入测试，回到 writeback 边界。
- **risk**：部分发布留下孤儿导航。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增事务失败注入测试，证明 source-index、Home/主题发布失败时旧快照保持可恢复。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k transaction`（RED，exit 1）；随后同命令 GREEN（exit 0）。
- **evidence_refs**：`receipts/tests/phase4-r1-red.json`；`evidence/phases/phase-4-r1/8c15df1f426f324342671f5218df077102cbf381/phase-evidence-5d7644c1f2359727ab999f949773d5203699c93ef7885209e7282d47f65c7d41.json`。
- **covered_ac**：AC-004、AC-005、AC-008
- **review_fact**：Phase 4 r1 使用 WorkflowHub 配置的 `kimi/coding + cursor/grok` 完成 2/2 semantic review；其后 Phase 4 r2 修复 review 同样为 2/2 semantic pass。review 结果保留于 `reviews/results/build-code-default-8c15df1f426f324342671f5218df077102cbf381-cd5bc289-b847-4465-93b7-902e7dcbbe43.json` 与 `reviews/results/build-code-default-3d8e9b7cc13a34096de6d2d62ece3a8aaa0c70fa-8c196a16-4a8e-4554-9254-a21bee55da47.json`。
- **completed_at**：2026-08-03T19:12:00+08:00

### T016 — GREEN：同批归档后安全发布

- **ID / phase**：T016 / Phase 4
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T015
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：Home、分类、主题、source-index、Provenance 同批 archive-before-write；失败可恢复旧快照；pipeline 只消费 `navigation.py` records。
- **dependencies / paired_task**：T015 / T015
- **FR / AC**：SCOPE-003 / AC-004、AC-005、AC-008
- **action**：扩展 `pipeline.py`/`writeback.py`/`provenance.py`，通过现有单写者边界，删除第二套导航记录生成路径。
- **exact_files**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/provenance.py`、`tests/acceptance/test_task2_batch_recovery.py`
- **boundary**：不引入数据库/CAS/journal，不删除旧 part。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k transaction` / `0`
- **oracle**：`KD-T2-RECOVERY`；失败时旧 index/page 仍可恢复，成功时无孤儿导航。
- **evidence_path**：`evidence/build-code/task2/T016-green.txt`
- **STOP**：绕过 writeback 或把原子性降级为“尽力而为”。
- **recovery**：恢复旧 writeback 路径，保留 archive evidence。
- **risk**：多文件切换时出现短暂混合版本。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：将 Home、分类、主题、source-index 与 provenance 纳入同一 publication/writeback 记录流，删除 pipeline 的第二套 source-index 直接写入路径。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k transaction`（GREEN，exit 0）。
- **evidence_refs**：`receipts/tests/phase4-r1-green.json`；`evidence/phases/phase-4-r1/8c15df1f426f324342671f5218df077102cbf381/phase-evidence-5d7644c1f2359727ab999f949773d5203699c93ef7885209e7282d47f65c7d41.json`；`evidence/phases/phase-4-r2/3d8e9b7cc13a34096de6d2d62ece3a8aaa0c70fa/phase-evidence-6d76fef8e07637ebd6fb36afdd36c8a0c6e1afafb5e8a51af9009024f7990c52.json`。
- **covered_ac**：AC-004、AC-005、AC-008
- **review_fact**：Phase 4 r1 `kimi/coding + cursor/grok` 2/2 semantic review 后，r2 对 source-index 写回边界完成修复并通过同配置 2/2 semantic review；结果为 `reviews/results/build-code-default-3d8e9b7cc13a34096de6d2d62ece3a8aaa0c70fa-8c196a16-4a8e-4554-9254-a21bee55da47.json`。
- **completed_at**：2026-08-03T19:12:00+08:00

### T017 — RED：state v3、budget、split/resume

- **ID / phase**：T017 / Phase 4
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T018
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：状态缺 taxonomy/model/backend/topic-plan/budget、manifest 变化、成功批重复执行、失败批 split 语义、cache identity 和 60 分钟墙钟门先失败。
- **dependencies / paired_task**：T016 / T018
- **FR / AC**：FR-LLM-004/005 / AC-005、AC-006、AC-008
- **action**：state v2 mismatch、source failure、split_from、planned-call、fake clock 和 cache-key fixtures。
- **exact_files**：`tests/acceptance/test_task2_batch_recovery.py`
- **boundary**：只写 batch state/recovery tests。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k resume` / `1`
- **oracle**：`KD-T2-RECOVERY`；旧/变更状态拒绝，成功来源不能重跑；planned-call 或 fake clock 超过 60 分钟 fail-closed。
- **evidence_path**：`evidence/build-code/task2/T017-red.txt`
- **STOP**：需要调度器、跨模型复用 cache 或无限重试。
- **recovery**：保留 state fixtures，返回 writeback checkpoint 设计。
- **risk**：resume 误判成功批，产生重复主题。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增 state v3、固定运行身份、planned-call 预算、持久化 wall-clock 起点、失败尝试计费、单次 split/resume 语义测试。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k resume`（RED，exit 1）；随后同命令 GREEN（exit 0）。
- **evidence_refs**：`receipts/tests/phase4-r2-red.json`；`receipts/tests/phase4-r2-green.json`。
- **covered_ac**：AC-005、AC-006、AC-008
- **review_fact**：Phase 4 r2 独立 review 使用配置文件指定的 `kimi/coding + cursor/grok`，2/2 provider completed，semantic verdict pass；结果为 `reviews/results/build-code-default-3d8e9b7cc13a34096de6d2d62ece3a8aaa0c70fa-8c196a16-4a8e-4554-9254-a21bee55da47.json`。
- **completed_at**：2026-08-03T19:12:00+08:00

### T018 — GREEN：state v3 分批恢复与预算

- **ID / phase**：T018 / Phase 4
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T017
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：状态 v3 锁清单/身份/预算/首个主题计划；cache key 绑定 endpoint/model/dimension/probe/text hash；成功批立即落盘；失败来源最多一次拆单恢复；planned-call 或 60 分钟墙钟超限 fail-closed；变更拒绝续跑。
- **dependencies / paired_task**：T017 / T017
- **FR / AC**：FR-LLM-004/005 / AC-005、AC-006、AC-008
- **action**：扩展 `batch_run.py`，pipeline 只编排恢复结果并记录报告；不改变既有 similarity seam，只锁定并验证 backend/cache identity。
- **exact_files**：`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_task2_batch_recovery.py`
- **boundary**：不演化为 scheduler/database；不重新调用成功来源。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k resume` / `0`
- **oracle**：`KD-T2-RECOVERY`；成功批可读、失败批可拆、状态变更 fail-closed。
- **evidence_path**：`evidence/build-code/task2/T018-green.txt`
- **STOP**：预算超限仍发 provider 请求，或失败被计为成功。
- **recovery**：恢复 state v2 只读兼容路径，要求新状态文件。
- **risk**：状态文件与 topic-index fingerprint 不一致。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：实现 state v3 的清单/身份/预算锁定，成功批 checkpoint，失败批最多一次拆单，预算超限前 fail-closed；保留既有 similarity seam。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py -k resume`（GREEN，exit 0）。
- **evidence_refs**：`receipts/tests/phase4-r2-green.json`；`receipts/revisions/implementation/3a95857bfd840d0547aa4d7c7edd7b3c55265337e1de77f122c8f589d4b82011.json`；`evidence/phases/phase-4-r2/3d8e9b7cc13a34096de6d2d62ece3a8aaa0c70fa/phase-evidence-6d76fef8e07637ebd6fb36afdd36c8a0c6e1afafb5e8a51af9009024f7990c52.json`；`evidence/phases/phase-4-r2/3d8e9b7cc13a34096de6d2d62ece3a8aaa0c70fa/phase-map-trace-9cda99bffa1f583c6a8a2b1cc6dc15946a2fefabe21f4165b104c4fe6c2c47be.json`。
- **covered_ac**：AC-005、AC-006、AC-008
- **review_fact**：`kimi/coding + cursor/grok` 2/2 independent semantic review completed with verdict pass；修复前 review 报告保留为审计证据，修复后的 Phase 4 r2 review 结果为 `reviews/results/build-code-default-3d8e9b7cc13a34096de6d2d62ece3a8aaa0c70fa-8c196a16-4a8e-4554-9254-a21bee55da47.json`。
- **completed_at**：2026-08-03T19:12:00+08:00

### Phase 4 corrective closure (r3/r4)

- **r3 source-index repair**：`receipts/tests/phase4-r3-red.json`（RED exit 1）→ `receipts/tests/phase4-r3-green.json`（GREEN exit 0）；candidate `8aa550fa01e0d4df5452b704294d58707f0b432d`；review `reviews/results/build-code-default-8aa550fa01e0d4df5452b704294d58707f0b432d-31b46bfe-721d-4317-91a9-83237b14a29f.json`，2/2 configured providers pass。
- **r4 fail-closed repair**：`receipts/tests/phase4-r4-red.json`（missing immutable snapshot manifest，RED exit 1）→ `receipts/tests/phase4-r4-green.json`（GREEN exit 0）；implementation `receipts/revisions/implementation/994e0ddc7d5c88886d7860ea7afee783bcb89e4bc1f02c0635602443982f09e1.json`；candidate `adcf29a548ffa83fea3b79d18d1608a19f61ab0e`；review `reviews/results/build-code-default-adcf29a548ffa83fea3b79d18d1608a19f61ab0e-1e8d403f-1b41-4eba-a315-fdb038be6967.json`，2/2 configured providers pass。
- **closure**：source-index 不再回退到易变 raw items；缺 immutable source snapshot manifest 明确失败；Phase 4 r4 phase evidence 状态 `done`。

## 6. Phase 5：文档、语料和对比报告

### Goal

让最终结果文件夹可解释；用固定 manifest 对比 Task1、Task2 和 CompanyBrain 的机器证据、人工阅读质量与成本。

### Files

- **NEW**：`tests/acceptance/test_task2_corpus_regression.py`、`scripts/task2_publication_comparison.py`、`docs/reports/knowledge-digest-task2-publication-comparison.md`
- **MODIFY**：`AGENTS.md`
- **DO NOT TOUCH**：`/Users/Hugh/Downloads/confluence`、`/Users/Hugh/Downloads/KnowledgeDigest-offline-architecture-verified-5Ng5LpvP`、`docs/plans/universal-knowledge-digest-design.md`

### Verify

`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py`；oracle：`KD-T2-CORPUS`。

### Knowledge

Task1 baseline 和原始 Confluence 只读；CompanyBrain 只作 reader-visible reference；真实语料必须写新隔离 KB。

### STOP

需要覆盖 baseline、调用 DeepSeek、把 Claim/page/token 数当质量，或不能保留 raw source hash。

### Done

README/AGENTS 解释结果目录；固定 manifest、结构/无损/导航证据和读者报告可复现。

### Risks and rollback

风险是机器门通过但阅读退化；固定样本人工检查失败时保留两套结果，先修 publication 再重跑。

### T019 — RED：89 篇离线回归缺口

- **ID / phase**：T019 / Phase 5
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T020
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：固定 89 篇、新空 KB、no-LLM/Jaccard 的无损、导航、页限、来源回溯、重复运行、Other≤20%、pending 单列和非单一 `pages/digest` 分布合同先失败；逐项读取 Task1 基线做 Claim/URI/fingerprint/定位/验证状态比对。
- **dependencies / paired_task**：T018 / T020
- **FR / AC**：SCOPE-003、FR-LLM-005 / AC-001、AC-003、AC-004、AC-006
- **action**：新增 corpus regression fixtures/manifest 验证。
- **exact_files**：`tests/acceptance/test_task2_corpus_regression.py`
- **boundary**：原始目录只读；Task1 baseline 只读其 Claim/source manifest 做逐项比对；任何输入均不得写回。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k corpus` / `1`
- **oracle**：`KD-T2-CORPUS`；失败必须是目标能力缺口，非缺数据/网络；Other>20%、pending 被计入 Other、主题全落单一 `pages/digest` 或 Task1 集合不相等均非零退出。
- **evidence_path**：`evidence/build-code/task2/T019-red.txt`
- **STOP**：用旧产物冒充新运行，或把 Claim 数当质量。
- **recovery**：保留 manifest，返回 Phase 3/4 修复。
- **risk**：样本或输入清单漂移。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增固定 89 篇 no-LLM/Jaccard 语料回归合同，锁定 raw hash、Claim/source/定位/验证状态、导航分布、Other≤20%、pending 单列和 300 行上限。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k corpus`（RED exit 1；GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase5-r5-red.json`；`receipts/tests/phase5-r5-green.json`；`evidence/phases/phase-5-r5/fabcfc152ed741693d5e91f421f9a275c7ba9db9/phase-evidence-e57e080977d4f388db1c594ed9ce8152946d5c3d7c69828c0b1140889ee87b76.json`。
- **covered_ac**：AC-001、AC-003、AC-004、AC-006
- **review_fact**：Phase `phase-5-r5` 使用配置路由 `kimi/coding + cursor/grok`，2/2 provider completed，semantic verdict `pass`；无 DeepSeek 或产品运行时 LLM 调用。
- **completed_at**：2026-08-03T21:40:00+08:00

### T020 — GREEN：离线语料结构/无损回归

- **ID / phase**：T020 / Phase 5
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T019
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：89 篇固定输入在新空 KB 可重复离线发布；所有有效 Claim/URI/fingerprint/定位/验证状态与 Task1 baseline 逐项匹配；Home/分类/主题/source-index 可读且 ≤300 行；Other≤20%、pending 单列、主题不全落单一 `pages/digest`。
- **dependencies / paired_task**：T019 / T019
- **FR / AC**：SCOPE-003、FR-LLM-005 / AC-001、AC-003、AC-004、AC-006
- **action**：实现测试和脚本入口，不把真实正文提交 Git。
- **exact_files**：`tests/acceptance/test_task2_corpus_regression.py`
- **boundary**：测试只复制原始语料到新临时/Downloads 隔离目录，并只读 Task1 baseline 的 Claim/source manifest；绝不覆盖 baseline/raw source。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k corpus` / `0`
- **oracle**：`KD-T2-CORPUS`；报告样本/分类缺口，不伪造 20 个样本；逐项集合和分类分布断言必须通过。
- **evidence_path**：`evidence/build-code/task2/T020-green.txt`
- **STOP**：发生 LLM/embedding 请求，或修改 baseline/raw source。
- **recovery**：删除临时输出并保留 evidence，不触碰基线。
- **risk**：离线配置误触发 provider。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：完成 89 篇隔离 KB 的离线结构/无损回归实现与断言；不读取或修改原始 Confluence、Task1 baseline 和旧 Task2 产物。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k corpus`（GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase5-r5-green.json`；`evidence/phases/phase-5-r5/fabcfc152ed741693d5e91f421f9a275c7ba9db9/phase-evidence-e57e080977d4f388db1c594ed9ce8152946d5c3d7c69828c0b1140889ee87b76.json`。
- **covered_ac**：AC-001、AC-003、AC-004、AC-006
- **review_fact**：Phase `phase-5-r5` configured reviewer set `kimi/coding + cursor/grok`，2/2 valid，semantic `pass`。
- **completed_at**：2026-08-03T21:40:00+08:00

### T021 — N/A：AGENTS 与输出说明同步

- **ID / phase**：T021 / Phase 5
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：N/A — non-behavior change
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：更新根 `AGENTS.md`，解释命令、README/Home/index/topic/source-index/_digest/archive 用途和质量边界。
- **dependencies**：T020；无 paired RED/GREEN（纯文档任务）。
- **FR / AC**：SCOPE-003 / AC-001、AC-006
- **exact_files**：`AGENTS.md`
- **boundary**：不改变运行行为、路径或质量门。
- **gate_cmd / expected_exit**：`test -s AGENTS.md && rg -n "Home.md|source-index|--no-llm|300 行|qwen3.6" AGENTS.md` / `0`
- **oracle**：文档包含真实入口和禁止事项，不含凭据。
- **evidence_path**：`evidence/build-code/task2/T021-doc.txt`
- **STOP**：文档开始定义与 spec 不同的 taxonomy/输出合同。
- **recovery**：回退文档变更，保留代码/测试。
- **risk**：文档漂移导致下次维护误用输出目录。
- **completion**：`status=pending`；填写 actual_changes、命令、证据和时间。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：N/A — non-behavior change: documentation only
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：更新 `AGENTS.md`，说明结果目录、Home/category/topic/source-index/_digest/archive 的用途、qwen3.6/jina 配置和离线命令；未写入凭据。
- **executed_commands**：`test -s AGENTS.md && rg -n "Home.md|source-index|--no-llm|300 行|qwen3.6" AGENTS.md`（exit 0）。
- **evidence_refs**：`receipts/tests/phase5-r5-green.json`；`evidence/phases/phase-5-r5/fabcfc152ed741693d5e91f421f9a275c7ba9db9/phase-evidence-e57e080977d4f388db1c594ed9ce8152946d5c3d7c69828c0b1140889ee87b76.json`。
- **covered_ac**：AC-001、AC-006
- **review_fact**：Phase `phase-5-r5` included documentation in its declared allowed files；configured `kimi/coding + cursor/grok` 2/2 semantic `pass`。
- **completed_at**：2026-08-03T21:40:00+08:00

### T022 — RED：CompanyBrain 对比报告合同

- **ID / phase**：T022 / Phase 5
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T023
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：缺固定 sample manifest、shared source URI/product_slug matching、no_match、机器/人工分栏和成本字段时先失败。
- **dependencies / paired_task**：T021 / T023
- **FR / AC**：SCOPE-003 / AC-002、AC-007、AC-008
- **action**：新增报告 fixture，固定最多 20 个分层样本，禁止人工换样。
- **exact_files**：`tests/acceptance/test_task2_corpus_regression.py`、`scripts/task2_publication_comparison.py`
- **boundary**：只读 Task1/CompanyBrain；不生成替代样本。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k comparison` / `1`
- **oracle**：`KD-T2-CORPUS`；无匹配必须显式 no_match，不能默默忽略。
- **evidence_path**：`evidence/build-code/task2/T022-red.txt`
- **STOP**：把 Claim/page/token 数宣称为阅读质量，或写入密钥/原文。
- **recovery**：保留 fixture，回到报告字段合同。
- **risk**：样本替换造成有利偏差。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：RED
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：新增固定样本 manifest、CompanyBrain deterministic title/product matching、no_match、sample gaps、人工阅读字段、成本可用性和安全证据；脚本只读。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k comparison`（RED exit 1；GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase5-r5-red.json`；`receipts/tests/phase5-r5-green.json`；`evidence/phases/phase-5-r5/fabcfc152ed741693d5e91f421f9a275c7ba9db9/phase-evidence-e57e080977d4f388db1c594ed9ce8152946d5c3d7c69828c0b1140889ee87b76.json`。
- **covered_ac**：AC-002、AC-007、AC-008
- **review_fact**：Phase `phase-5-r5` configured `kimi/coding + cursor/grok` 2/2 completed，semantic `pass`；r4 revise_required 已通过 r5 RED/GREEN 修复并重新审查。
- **completed_at**：2026-08-03T21:40:00+08:00

### T023 — GREEN：生成对比、成本和阅读报告

- **ID / phase**：T023 / Phase 5
- **design_state**：ready
- **inputs**：绑定 spec/plan、对应 FR/AC 和前置任务输出
- **parallel**：否 — 当前任务共享本 Phase 文件并依赖前序合同。
- **paired_task**：T022
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-llm-naming-classification/plan.md","hash":"0e0deb6f9c6c0348d0c27d8a4602fad2f6ed23e27369515e33204471773014ae","id":"kd-task2-publication-plan"}]`
- **goal**：生成样本 manifest、Task1/Task2/CompanyBrain 读者表、provider 调用/失败/重放/耗时/token/fallback 报告，并区分机器事实与人工判断；输出 `title_understood` 分子、分母、百分比及“≥80% 通过 / <80% 未达标”结论。
- **dependencies / paired_task**：T022 / T022
- **FR / AC**：SCOPE-003 / AC-002、AC-007、AC-008
- **action**：实现 comparison script 和报告模板，报告输出到隔离结果目录，文档模板写入 repo。
- **exact_files**：`scripts/task2_publication_comparison.py`、`docs/reports/knowledge-digest-task2-publication-comparison.md`、`tests/acceptance/test_task2_corpus_regression.py`
- **boundary**：只消费既有结果，不调用 DeepSeek，不修改任何 baseline/raw source。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k comparison` / `0`
- **oracle**：`KD-T2-CORPUS`；样本不足报告缺口，报告无密钥和原文正文；人工标题理解度按固定分母给出明确阈值结论，不能用 Claim/page/token 替代。
- **evidence_path**：`evidence/build-code/task2/T023-green.txt`
- **STOP**：报告把人工结论伪造成 provider/机器事实，或无法复现 manifest。
- **recovery**：保留 Task1/Task2 输出，删除临时报告后重跑，不覆盖结果。
- **risk**：人工阅读质量被结构指标替代。
- **completion**：`status=pending`；执行后填完成区。
- **output**：目标行为断言/实现证据，详见 gate 与 oracle。
- **Knowledge**：执行前读取本卡 exact_files 现有 seam 和 plan 对应 anchor；不得扩大文件边界。
- **verification_role**：GREEN
##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：completed
- **actual_changes**：生成对比脚本和仓库报告模板；报告区分机器事实、人工阅读待审、成本证据状态与安全检查，不把 Claim/page/token 当阅读质量。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k comparison`（GREEN exit 0）。
- **evidence_refs**：`receipts/tests/phase5-r5-green.json`；`evidence/phases/phase-5-r5/fabcfc152ed741693d5e91f421f9a275c7ba9db9/phase-evidence-e57e080977d4f388db1c594ed9ce8152946d5c3d7c69828c0b1140889ee87b76.json`；`reviews/results/build-code-default-fabcfc152ed741693d5e91f421f9a275c7ba9db9-29a3c954-e2ac-4ab1-ae6f-c0ecfc89c39e.json`。
- **covered_ac**：AC-002、AC-007、AC-008
- **review_fact**：r5 review SHA-256 `41b03c6a98f587d4e59cbe8ca4b0fc534002a14409d47bff23633676fde2df42`；`kimi/coding + cursor/grok` 2/2 valid，no findings，semantic `pass`。
- **completed_at**：2026-08-03T21:40:00+08:00

### Phase 5 corrective closure (r6)

- **RED**：`receipts/tests/phase5-r6-red.json`，聚焦测试 2 项失败：分批 source-index 被最后一批覆盖；README 缺托管标记导致后续运行 fail-closed。
- **GREEN**：`receipts/tests/phase5-r6-green.json`，同一聚焦命令 2 项通过；测试覆盖新增累计 source-index 与 README reader identity。
- **implementation**：`receipts/revisions/implementation/0d6f1d6df2d6ec00fc5a666dc26cf43386d7395923b6a947c4c58a33441feeca.json`。
- **review**：`reviews/results/build-code-default-9100523c7b8ab040368aa4eb447720319b0311ef-2f4dedd3-de68-49de-8dcd-ff5654a0ecf5.json`，SHA-256 `f753babcaee82e45c3348631556f4731455ea520c6d05471e0d21339393509e4`；配置路由 `kimi/coding + cursor/grok`，2/2 semantic `pass`，无 findings。
- **phase evidence**：`evidence/phases/phase-5-r6/9100523c7b8ab040368aa4eb447720319b0311ef/phase-evidence-5ba7e9173bddfe45accd22da1a83b967b4ca3d26d07bd095ff4f149be1d1ca3a.json`，状态 `done`。
- **scope note**：旧 acceptance 中引用废弃 JSONL source-index 的断言已改为固定 Markdown source-index 合同；未恢复并行 JSON 产物。

### Phase 5 corrective closure (r7)

本轮修复由上一轮独立验证暴露的真实问题触发；不扩大 Task2 产品范围，不重跑已失败的 89 篇实时 provider 全量。

- **T024 — publication-only prompt 与输出上限**：`src/knowledge_digest/llm.py`、`tests/acceptance/test_phase25_llm.py`、`tests/acceptance/test_task2_publication.py`。新增紧凑 publication-only 提示词和 OpenAI `max_tokens` 上限；聚焦测试通过。
- **T025 — live provider context 稳定性**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/llm.py`。provider 已解析后所有 live topic 仍使用 publication-only 合同；解析器允许 publication-only 响应；聚焦测试通过。
- **T026 — 批次聚合保留 publication**：`src/knowledge_digest/draft.py`、`tests/acceptance/test_task2_publication.py`。多个 Claim 批次合并时保留 publication、claim_refs、field_refs 和 related_topics；聚焦测试通过。
- **T027 — 最终页面去重**：`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task2_publication.py`。生成器 Summary/Evidence 外壳不再嵌入 Evidence；最终 layout record 保留 publication；聚焦测试通过。
- **T028 — 成本证据纠正**：`scripts/task2_publication_comparison.py`、`tests/acceptance/test_task2_corpus_regression.py`。deterministic generator rounds 与真实 provider calls 分开记录，离线运行 provider calls 固定为 0；聚焦测试通过。
- **T029 — qwen/jina 真实分步证据**：真实 3-input 小批次完成，其中 2 条有效来源成功、1 条 5 字节空来源被正确拒绝；结果为 `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-live3-JiyW7X`。89-source 全量失败/中止现场保留于 corrective closure report，未伪造成功。
- **T030 — 89-source 离线回归与边界披露**：结果为 `/Users/Hugh/Downloads/KnowledgeDigest-task2-offline-after-kJjick`；9,288 Claim 保留、120 physical pages、每页 ≤300 行；CompanyBrain 17 样本人工字段仍为 `manual_review_required`。

**r7 focused gate**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py tests/acceptance/test_phase25_llm.py tests/acceptance/test_task2_corpus_regression.py` → `87 passed`；完整 `uv run --frozen pytest -q` → `307 passed`。
**r7 review fact**：已按 `/Users/Hugh/.config/workflowhub/config.json` 检查 `wh-review` doctor；配置路由是 `kimi/coding + cursor/grok`。当前快照的官方 `stage-runtime review:invoke` 产生了 authenticated request，但因宿主 bridge 返回 `host bridge requires exactly one response after request`，未形成 semantic result；该 unavailable 事实不能算 pass。此前 phase review 不能替代当前 dirty snapshot 的新审查。实时 89-source 语义发布与 CompanyBrain 人工阅读验收仍是开放质量事实。

### Phase 5 corrective closure (r8)

#### T031 — GREEN：批次失败/成本账本

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T018 的失败恢复合同
- **goal**：provider、写入和预算失败均留下可审计失败状态；planned calls 不冒充 observed calls；失败来源进入 `needs-review`，重放仍为 pending。
- **FR / AC**：FR-LLM-004/005 / AC-005、AC-008
- **exact_files**：`src/knowledge_digest/batch_run.py`、`tests/acceptance/test_task2_batch_recovery.py`
- **boundary**：不调用 provider，不改变成功来源，不引入 scheduler/database；失败账本是历史事实，不覆盖最终成功状态。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py` / `0`
- **oracle**：失败侧车为 `batch-failure-report.v1` 且 `status_semantics=historical_failure`；`final_status` 单独表达最终批次状态；run report 为 `failed_provider` 或 `failed`；`provider_calls_observed`/tokens 未知时必须是 `null`；来源数预算只写 `provider_calls_reserved`，不能冒充 generator planned calls。
- **evidence_path**：`evidence/build-code/task2/T031-green.txt`
- **actual_changes**：新增 `cost_summary`、失败侧车、失败 run report 更新、elapsed/failure/replay/fallback 账本；将来源数预算命名为 `provider_calls_reserved`。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py -k 'comparison or failed_provider_attempt or batch'` → `14 passed, 1 deselected`。
- **evidence_refs**：`evidence/build-code/task2/T031-green.txt`；`tests/acceptance/test_task2_batch_recovery.py::test_failed_provider_attempt_writes_durable_failure_cost_report`。
- **covered_ac**：AC-005、AC-008。
- **review_fact**：本 r8 快照的官方 review 因 host bridge 未返回唯一响应而 unavailable；未将其记为 pass。
- **completed_at**：2026-08-03T23:10:00+08:00

#### T032 — GREEN：对比脚本读取失败账本

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T031
- **goal**：按 report freshness 选择最新运行；批次账本存在时读取明确成本状态；预留调用数和实际调用数分开。
- **FR / AC**：FR-LLM-005 / AC-008
- **exact_files**：`scripts/task2_publication_comparison.py`、`tests/acceptance/test_task2_corpus_regression.py`
- **boundary**：只读知识库、batch-state、run reports 和 CompanyBrain；不写回输入，不调用 provider。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k comparison` / `0`
- **oracle**：UUID 命名变化不影响 latest 选择；失败账本的 reserved/planned/observed/failed/elapsed 字段原样可见；拆批后仍保留失败与重放计数。
- **evidence_path**：`evidence/build-code/task2/T032-green.txt`
- **actual_changes**：修正 latest run 选择，读取 `batch-state.json.cost_summary`，补失败账本回归测试。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k comparison` → `2 passed`。
- **evidence_refs**：`evidence/build-code/task2/T032-green.txt`；`tests/acceptance/test_task2_corpus_regression.py::test_comparison_uses_freshest_report_and_batch_failure_ledger`。
- **covered_ac**：AC-008。
- **review_fact**：本 r8 快照的官方 review unavailable；不以历史 phase review 代替当前审查。
- **completed_at**：2026-08-03T23:10:00+08:00

**r8 focused gate**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_publication.py tests/acceptance/test_phase25_llm.py tests/acceptance/test_task2_corpus_regression.py` → `100 passed`；完整 `uv run --frozen pytest -q` → `310 passed`。
**r8 boundary**：该修复补齐失败现场的可审计账本，但没有把 89-source qwen 全量失败改写成成功；`provider_calls_observed` 和 `provider_tokens` 在 provider 截断/异常时仍为 `null`。批次按来源数记录的预算叫 `provider_calls_reserved`，不是按 claim/字符拆分得到的 planned generator calls；89-source 的 180-call dry-run hard-stop 仍未完成。Task2 的 AC-002、AC-007、AC-008 仍不能宣称全部通过。

### Phase 5 corrective closure (r9)

#### T033 — GREEN：planned-call hard-stop 与离线成本语义

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T031
- **goal**：首个 provider 请求前完成 full-manifest dry-run；planned generator calls 超过 180 时暂停且不发请求；离线 report 不把 deterministic rounds 写成 provider calls。
- **FR / AC**：FR-LLM-004 / AC-006、AC-008
- **exact_files**：`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_task2_batch_recovery.py`、`tests/acceptance/test_task2_corpus_regression.py`
- **boundary**：dry-run 不调用 provider；不改变输入、KB 页面或 fallback 规则。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py::test_planned_generator_call_hard_stop_happens_before_provider tests/acceptance/test_task2_corpus_regression.py::test_corpus_contract_is_fixed_and_structured` / `0`
- **oracle**：`planned_generator_calls > 180` 时 `run_status=paused`；offline `provider_calls_planned/observed=0`，`deterministic_rounds` 单独存在。
- **evidence_path**：`evidence/build-code/task2/T033-green.txt`
- **actual_changes**：新增 full-manifest provider-free preflight、180 hard-stop、planned report identity；修正 pipeline cost report 的 LLM/离线语义。
- **evidence_refs**：`evidence/build-code/task2/T033-green.txt`；对应两个 acceptance test。
- **covered_ac**：AC-006、AC-008。
- **review_fact**：本 r9 快照官方 review unavailable；未将 unavailable 记为 pass。
- **completed_at**：2026-08-03T23:30:00+08:00

#### T034 — GREEN：批次聚合事实不丢失

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T032
- **goal**：最后一个 batch report 成功时，比较报告仍合并 batch-state 的 failed/replay/elapsed；aggregate observed calls 未知时保持 `null`。
- **FR / AC**：FR-LLM-005 / AC-008
- **exact_files**：`scripts/task2_publication_comparison.py`、`tests/acceptance/test_task2_corpus_regression.py`
- **boundary**：只读 report、batch-state 和 KB；不把最后一批结果冒充全量 provider 成本。
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_corpus_regression.py -k comparison` / `0`
- **oracle**：批次失败/重放字段不被 latest successful report 覆盖；planned/reserved/observed 字段含义不混淆。
- **evidence_path**：`evidence/build-code/task2/T032-green.txt`
- **actual_changes**：批次账本始终合并，provider aggregate unknown 保持 `null`，新增 reserved/planned 区分。
- **evidence_refs**：`evidence/build-code/task2/T032-green.txt`；`test_comparison_uses_freshest_report_and_batch_failure_ledger`。
- **covered_ac**：AC-008。
- **review_fact**：本 r9 快照官方 review unavailable；不以历史 review 替代当前审查。
- **completed_at**：2026-08-03T23:30:00+08:00

**r9 focused gate**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_publication.py tests/acceptance/test_phase25_llm.py tests/acceptance/test_task2_corpus_regression.py` → `100 passed`；完整 `uv run --frozen pytest -q` → `310 passed`。
**r9 boundary**：180-call 预算门和离线报告语义已补齐；89-source qwen3.6 全量语义发布仍没有成功证据，CompanyBrain 17 个样本仍需人工阅读，所以 AC-002、AC-007、AC-008 仍未全部通过。

### T035 — GREEN：provider 失败的来源索引与可读队列

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T031/T032
- **goal**：provider 输出失败时，成功页继续可达；失败来源同时出现在机器 pending-review、来源索引 `needs-review` 和读者可见 `_queues/needs_review.md`。
- **FR / AC**：FR-LLM-005 / AC-004、AC-005
- **exact_files**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/queues.py`、`tests/acceptance/test_phase25_llm.py`
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_phase25_llm.py::test_end_to_end_provider_error_publishes_source_and_pending_review` / `0`
- **actual_changes**：provider pending source 不再被 source-index 静默过滤；队列使用稳定 source key；增加端到端断言。
- **evidence_path**：`evidence/build-code/task2/T035-green.txt`
- **covered_ac**：AC-004、AC-005。
- **review_fact**：本快照官方 review unavailable；未用 unavailable 冒充 pass。
- **completed_at**：2026-08-04T00:20:00+08:00
- **completion**：`status=completed`；本任务已按声明范围完成。官方 review unavailable 是未解决质量事实，不是通过结论。

### T036 — GREEN：全量 qwen 分批回归与真实成本账本

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T033/T034
- **goal**：在用户指定 qwen3.6 + jina-embeddings 下，89 篇按批次完成，结果可读、无 Claim 丢失、失败可见，成本事实不把 reserved/planned/observed 混淆。
- **FR / AC**：FR-LLM-004/005 / AC-001、AC-002、AC-003、AC-004、AC-005、AC-008
- **exact_files**：`scripts/task2_publication_comparison.py`、`docs/reports/knowledge-digest-task2-corrective-closure.md`、最终 Downloads 产物
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q` / `0`
- **oracle**：89 snapshots、9,288 Claim entity、7,796 fingerprint、88 source-index URI、74 stable topics、all topic pages <=300 lines；provider qwen only。
- **evidence_path**：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-batched-final-kxlAw1/comparison-final-r3/COMPARISON.json`
- **actual_changes**：对比脚本聚合全量 claim-history；批次 cost summary 汇总 172 provider calls、80 failed/fallback、2 replay；增加显式 agent-assisted reader audit，保留 independent human boundary。
- **covered_ac**：机器证据覆盖 AC-001/003/004/005；AC-002/007 为部分证据；AC-008 的 3,600 秒安全线超出 88.666 秒，标记 partial。
- **review_fact**：第三版更大批次性能尝试首批未完成即停止，现场保留；未把它计入最终成功产物。官方 review unavailable。
- **completed_at**：2026-08-04T00:45:00+08:00
- **completion**：`status=completed`；全量 qwen 结果与成本账本已写入独立产物，人工语义审查和官方 review 的边界保持公开。

**r10 full gate**：`uv run --frozen pytest -q` → `312 passed in 17.39s`；`git diff --check` → `0`。
**r10 boundary**：该历史尝试中的更大批次超过 3,600 秒安全线，已由后续 T038 的 final9 分批结果取代；固定语料只有 17 个可抽样主题；Codex agent-assisted reader audit 不能替代独立人工阅读。以上事实均保留，未伪造全部 AC 通过。

### T037 — GREEN：跨批次稳定主题身份

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T017/T018
- **goal**：固定全量主题计划拥有稳定 `topic_id`；相似度候选只能提供检索提示，不能把新来源并入旧主题页面。
- **FR / AC**：SCOPE-001 / AC-004、AC-005
- **exact_files**：`src/knowledge_digest/retrieve.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task2_batch_recovery.py`
- **gate_cmd / expected_exit**：`uv run --frozen pytest -q tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_publication.py` / `0`
- **oracle**：固定计划主题 ID 不被旧页面相似候选覆盖；相关测试 `31 passed`。
- **actual_changes**：批次路径调用 `retrieve(..., preserve_cluster_identity=True)`；布局读取候选页头并拒绝跨主题目标；补充回归测试。
- **evidence_path**：`evidence/build-code/task2/T037-green.txt`
- **review_fact**：未调用新的 provider review；历史官方 review unavailable 仍保持原样。
- **completed_at**：2026-08-04T01:00:00+08:00
- **completion**：`status=completed`；稳定主题身份回归已完成，未新增 provider 调用。

### T038 — GREEN：最终 qwen 全量分批发布

- **design_state**：ready；**verification_role**：GREEN；**paired_task**：T033/T034/T036/T037
- **goal**：使用用户指定的 qwen3.6 与 jina-embeddings 配置，对 89 个来源逐批完成发布；失败来源可见，成功批次不重复执行。
- **FR / AC**：FR-LLM-001/004/005 / AC-001～AC-008
- **exact_files**：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804`
- **gate_cmd / expected_exit**：批次命令退出 `0`；随后 `uv run --frozen pytest -q` → `316 passed in 16.82s`。
- **oracle**：89/89 批成功落盘；9,288 Claim entity、7,796 fingerprint、88 source-index URI、86 stable topics、120 topic pages、页长≤300；176 planned/observed calls、30 failed provider calls、1 replay、fallback ratio 0.471591、2,690.861 秒。
- **boundary**：jina 探测失败，整次运行回退 Jaccard；不混用分数。固定语料只有 17/20 个可抽样主题；Codex agent-assisted reader review 不能替代独立人工确认。
- **evidence_path**：`/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/comparison/COMPARISON.json`
- **review_fact**：官方 WorkflowHub `wh-review` 仍因 `host bridge requires exactly one response after request` unavailable；未伪造 close receipt。
- **completed_at**：2026-08-04T01:50:00+08:00
- **completion**：`status=completed`；89/89 批次和最终产物已完成，jina 探测失败按合同整次回退 Jaccard；AC-007 的人工确认与官方 review 仍显式保留为开放事实。

## 7. Dependencies and Traceability

```text
T001→T002→T003→T004→T005→T006→T007→T008→T009→T010→T011→T012→T013→T014→T015→T016→T017→T018→T019→T020→T021→T022→T023
```

| Requirement | Tasks | Acceptance | Gate |
| --- | --- | --- | --- |
| SCOPE-001 | T005-T012 | AC-002/003/004 | `KD-T2-SEMANTIC`, `KD-T2-NAV` |
| SCOPE-002 | T001-T004 | AC-001/006 | `KD-T2-TAXONOMY` |
| SCOPE-003 | T013-T014,T019-T023 | AC-001/003/006/007/008 | `KD-T2-NAV`, `KD-T2-RECOVERY`, `KD-T2-CORPUS` |
| FR-LLM-001 | T005-T006 | AC-002/003 | semantic schema evidence |
| FR-LLM-002 | T005-T008 | AC-002/003 | prompt/schema/field_refs evidence |
| FR-LLM-003 | T005-T008 | AC-003/004/008 | semantic evidence |
| FR-LLM-004 | T007-T008,T017-T018 | AC-006/008 | backend consistency/cache/wall-clock evidence |
| FR-LLM-005 | T007-T008,T017-T020 | AC-005/006 | offline/recovery evidence |

发布前检查：spec/plan/tasks hash 一致；Phase Files 与 plan 逐字一致；所有行为 task 有 RED/GREEN 对；每个 AC 有 task/gate；无 task 触碰 DO NOT TOUCH；不伪造 provider review 或 WorkflowHub receipt。

## 8. Completion Ledger

所有任务初始为 `pending`。build-code 每完成一个任务，必须只在对应卡片的 completion 区填写实际文件、命令、evidence path、covered AC、review fact 和 UTC 时间；未执行不得写 `passed`。
