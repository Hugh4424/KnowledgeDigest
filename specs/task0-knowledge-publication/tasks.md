# KnowledgeDigest Task0 任务清单
- **Template version**：`plan-task.v3`

## 1. 执行摘要
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008；先 RED 后 GREEN，所有任务串行。

## 2. Global Constraints
只修改所属 Phase 的精确文件；不迁移历史结果，不引入第二套来源事实，不把 review 或运行记录当作质量成功事实。新运行不生成 `_digest/source-index.md` 或 `_digest/source-index.jsonl`，历史文件只读保留。所有 GREEN 必须使用对应 RED 的同一 gate command 和 oracle identity；oracle 同时写明 RED 的预期失败与 GREEN 的同一断言以 exit 0 通过。任务卡的 `gate_cmd` 是 WorkflowHub 字段校验要求的内层命令，不可脱离环境单独作为完成证据；权威执行命令是 `uv run --frozen` 包住该命令，任务执行状态必须记录实际包装命令和 stdout 证据。

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

#### T001 — 来源闭环 RED
- **ID**：T001
- **Phase**：Phase 1：来源闭环与幂等
- **goal**：先建立来源集合、指纹和重复运行不增长的失败断言。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：FR-KD-001、FR-KD-002、FR-KD-009；AC-001、AC-002。
- **依赖**：N/A — first task
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-KD-001、FR-KD-002、FR-KD-009
- **AC**：AC-001（写回前无 formal 页面子项由 T003/T004 关闭）、AC-002（来源关系幂等子项；archive 子项由 T003/T004 关闭）
- **动作**：在 `tests/acceptance/test_task0_manifest_contract.py` 写入成功、缺失、额外、重复、清单变化、每个 snapshot 的 `validated_at` 和同快照重跑不增长的失败测试。
- **精确文件**：`tests/acceptance/test_task0_manifest_contract.py`
- **boundary**：files: `tests/acceptance/test_task0_manifest_contract.py`; symbols/regions: Task0 manifest, ledger and idempotency acceptance cases only.
- **输出**：可复现的 RED 测试输出和失败原因。
- **Knowledge**：来源集合必须由 manifest、snapshot、ledger 三方闭合；每个来源的运行时间使用 snapshot 的 `validated_at`，必须是可解析的 UTC 时间并进入对账断言。
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：1
- **oracle**：ORACLE-TASK0-MANIFEST — same contract oracle: RED must show the expected missing closure behavior with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T001.stdout`
- **STOP**：测试因环境或无关 import 失败，而不是目标合同失败时停止。
- **recovery**：删除当前测试 bytes，保留历史 acceptance 和审计证据。
- **task risk**：RED 可能误报环境错误为产品失败。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 manifest/snapshot/ledger 闭环、缺失/额外声明失败和同 snapshot 关系幂等 RED 测试；RED 首次按预期暴露 3 个产品失败。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`（RED：exit 1，3 个新增断言失败；后续同命令 GREEN：exit 0）。
- **evidence_refs**：`[{"ref":"quality/tests/phase-1-manifest-final.json","sha256":"a887e5040348784ce998bb81b5fa29858eb6d0d14c1dc77e48d55425367f01d7","kind":"test"}]`
- **covered_ac**：`AC-001`（来源闭环测试输入）、`AC-002`（来源关系幂等测试输入；archive 子项仍由 T003/T004 关闭）。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-196c071da2623da7b218e9b89f67e1fae5b8b0cc-4007b2f6-2ed1-4280-9415-6051b6feedc4.json","sha256":"f42bbcead751733bd55ab6ad1bf49e22af8a5366363b520e3e5d5f496e804157"}`
- **completed_at**：`2026-08-04T12:47:00+08:00`

#### T002 — 来源闭环 GREEN
- **ID**：T002
- **Phase**：Phase 1：来源闭环与幂等
- **goal**：实现 manifest/snapshot/ledger 对账、稳定来源事实和同快照业务幂等。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：T001 RED 输出；FR-KD-001、FR-KD-002、FR-KD-009；AC-001、AC-002。
- **依赖**：T001
- **并行**：否 — same contract as T001
- **FR**：FR-KD-001、FR-KD-002、FR-KD-009
- **AC**：AC-001（写回前无 formal 页面子项由 T003/T004 关闭）、AC-002（来源关系幂等子项；archive 子项由 T003/T004 关闭）
- **动作**：在 `src/knowledge_digest/ingest.py`、`batch_run.py`、`provenance.py`、`pipeline.py` 实现来源闭环、`validated_at`、source/duplicate 关系幂等和重跑事实；archive 内容幂等由 Phase 2 关闭，异常增长定位留给 Phase 4。
- **精确文件**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/provenance.py`、`src/knowledge_digest/pipeline.py`
- **boundary**：files: `src/knowledge_digest/ingest.py`, `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/provenance.py`, `src/knowledge_digest/pipeline.py`; symbols/regions: existing S1, batch state, S6 provenance and `_commit_outputs` source/duplicate append paths only.
- **输出**：GREEN 测试、可定位 source-manifest 和运行审计事实。
- **Knowledge**：`_digest/source-manifest.json` 是唯一 Audit 来源事实源，snapshot 的 `validated_at` 与 manifest/ledger 逐项关联，`indexes/sources.md` 不在本 Phase 生成。
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：0
- **oracle**：ORACLE-TASK0-MANIFEST — same contract oracle: RED must show the expected missing closure behavior with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T002.stdout`
- **STOP**：发现业务结果或 archive 随同快照重跑重复增长时停止交付。
- **recovery**：撤销当前四个源文件的修改，不删除历史运行记录。
- **task risk**：幂等修复可能误删运行审计追加，必须保持两者分离。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `batch_run.py`、`pipeline.py`、`provenance.py` 中实现唯一 manifest、持久化 source-audit-ledger、snapshot/duplicate/ledger 幂等合并、统一 Claim 提取、来源声明闭合检查和空写回时的 audit-only 持久化；补齐 ledger 集合/ID/指纹断言。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`，exit 0，`44 passed`。
- **evidence_refs**：`[{"ref":"quality/tests/phase-1-manifest-final.json","sha256":"a887e5040348784ce998bb81b5fa29858eb6d0d14c1dc77e48d55425367f01d7","kind":"test"}]`
- **covered_ac**：`AC-001`（manifest/snapshot/ledger 集合、稳定 ID、指纹闭合；写回前无 formal 页面由 T003/T004 关闭）、`AC-002`（source/duplicate/ledger 同 snapshot 不增长；archive 子项由 T003/T004 关闭）。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-196c071da2623da7b218e9b89f67e1fae5b8b0cc-4007b2f6-2ed1-4280-9415-6051b6feedc4.json","sha256":"f42bbcead751733bd55ab6ad1bf49e22af8a5366363b520e3e5d5f496e804157"}`
- **completed_at**：`2026-08-04T12:47:00+08:00`

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
现有 writeback 已有归档和单写者边界；本 Phase 只调整门禁顺序和事实分层。
### STOP
任一失败在 writeback 后才暴露，或无关页面被回滚时停止。
### Done
AC-001 的写回前无 formal 页面子项、AC-002 的 archive 不增长断言、AC-003、AC-004、AC-007 的故障注入和旧页恢复断言通过。
### Risks and rollback
归档先行；写回失败时恢复旧 formal 页面，不删除 audit。

#### T003 — 写回门禁 RED
- **ID**：T003
- **Phase**：Phase 2：写前门禁与原子写回
- **goal**：先写出 writeback 前失败、状态独立、来源降级和旧页保护的失败断言。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：T002 GREEN；FR-KD-001、FR-KD-003、FR-KD-004、FR-KD-005、FR-KD-006、FR-KD-007、FR-KD-009、FR-KD-010；AC-001、AC-002、AC-003、AC-004、AC-007。
- **依赖**：T002
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-KD-001、FR-KD-003、FR-KD-004、FR-KD-005、FR-KD-006、FR-KD-007、FR-KD-009、FR-KD-010
- **AC**：AC-001、AC-002、AC-003、AC-004、AC-007
- **动作**：在 `tests/acceptance/test_task0_writeback_gate.py` 写入缺失来源时写回前无 formal 页面、非法 `page_status=released` 或 `delivery_status=released` 时的状态门禁、同快照下 Claim/claim-history、页面关系、ledger 和 archive 不增长、provenance/Claim、路径、allowlist fail-closed、来源失败、`_queues` 不变和旧页面保护的 RED 测试；运行记录可追加但不得作为业务增长。
- **精确文件**：`tests/acceptance/test_task0_writeback_gate.py`
- **boundary**：files: `tests/acceptance/test_task0_writeback_gate.py`; symbols/regions: prewrite gate, status independence and archive recovery cases only.
- **输出**：可复现的 writeback 前失败证据。
- **Knowledge**：`written`、`published` 和 `released` 必须由独立事实断言。
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：1
- **oracle**：ORACLE-TASK0-WRITEBACK — same contract oracle: RED must show the expected late or incomplete gate behavior with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T003.stdout`
- **STOP**：失败不是 writeback 合同，而是测试夹具或环境时停止。
- **recovery**：删除当前测试 bytes，保留旧页面和 audit 记录。
- **task risk**：故障注入可能误把 unrelated provider 失败当作门禁失败。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增写回幂等、状态/allowlist、来源级 degraded 和旧页/队列保护 RED 测试；RED 在修正测试夹具后只保留同 snapshot archive/history 增长这一目标失败。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`（RED：exit 1，目标幂等断言失败；后续 GREEN：exit 0）。
- **evidence_refs**：`[{"ref":"quality/tests/phase-2-writeback-final.json","sha256":"aabdec18da62a30aa7ab951ddae9648d667fd420ab5ed0d266ca2ca3aa777116","kind":"test"}]`
- **covered_ac**：`AC-001`（写前失败不改变已有 formal/queue）、`AC-002`（archive/claim-history 幂等）、`AC-003`、`AC-004`、`AC-007` 的 Phase 2 故障与状态子项。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-e242c318c63cc71c0bc1606a721fbabfe283930d-eff338ff-e628-4f1d-bbfc-30a9ffea52b2.json","sha256":"f034f693747fb65fddb718f07dfb201e99c6213db0e3e0d38446a4169d52f975"}`
- **completed_at**：`2026-08-04T13:03:00+08:00`

#### T004 — 写回门禁 GREEN
- **ID**：T004
- **Phase**：Phase 2：写前门禁与原子写回
- **goal**：把 provenance、Claim、路径、状态和 Reader/Audit 包 allowlist 检查放到 archive-before-writeback 的同一发布边界内；导航链接完整性留给 Phase 3。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：T003 RED 输出；FR-KD-001、FR-KD-003、FR-KD-004、FR-KD-005、FR-KD-006、FR-KD-007、FR-KD-009、FR-KD-010；AC-001、AC-002、AC-003、AC-004、AC-007。
- **依赖**：T003
- **并行**：否 — same contract as T003
- **FR**：FR-KD-001、FR-KD-003、FR-KD-004、FR-KD-005、FR-KD-006、FR-KD-007、FR-KD-009、FR-KD-010
- **AC**：AC-001、AC-002、AC-003、AC-004、AC-007
- **动作**：在 `src/knowledge_digest/provenance.py` 定义 `validate_prewrite_provenance(source_manifest, snapshots, source_audit_ledger, claims, planned_writes)`；由 `pipeline.py` 的 `_commit_outputs` 在组装 source manifest/snapshot/`source_audit_ledger`/Claim/planned writes 后、任何 source snapshot/duplicate/ledger 持久化、调用 `write_queues`、归档和 `writeback(...)` 之前调用。它必须独立检查 source-audit ledger 与 manifest/snapshot 闭合、`page_status`/`delivery_status` 合法、planned topic/navigation writes 满足 allowlist；任一失败不得改变 `_queues`、source snapshot/duplicate/ledger append、归档或新 formal 页面。`audit_provenance` 仍在成功写回后记录 claim lineage；相同稳定页路径、写前内容 SHA、snapshot/config 身份已存在时，writeback 不追加重复 archive 内容或 archive 记录，运行记录可追加；保留来源级 degraded 和旧 formal 页面保护。具体 `indexes/sources.md` 内容和导航链接完整性不在本任务实现。
- **精确文件**：`src/knowledge_digest/writeback.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/provenance.py`、`src/knowledge_digest/publication.py`
- **boundary**：files: `src/knowledge_digest/writeback.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/provenance.py`, `src/knowledge_digest/publication.py`; symbols/regions: `validate_prewrite_provenance` and `source_audit_ledger` in provenance.py, `_commit_outputs` call before source snapshot/duplicate/ledger append and before `write_queues`/archive/writeback, status/allowlist helpers in publication.py, existing writeback contract, and post-write `audit_provenance` emission.
- **输出**：GREEN 测试、旧页保护和失败不写回证据。
- **Knowledge**：单来源失败不整库回滚；语义 fallback 不等于 released。
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：0
- **oracle**：ORACLE-TASK0-WRITEBACK — same contract oracle: RED must show the expected late or incomplete gate behavior with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T004.stdout`
- **STOP**：任一门禁失败后仍出现新 formal 页面或旧页面变化时停止。
- **recovery**：撤销当前四个源文件的修改，恢复旧页和 audit。
- **task risk**：门禁顺序变更可能影响现有 pipeline 的原子写入边界。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `writeback.py`、`pipeline.py`、`provenance.py` 实现 archive-before-writeback 的 changed-only/archive-key 幂等、claim-history 同快照/config 去重、正向 Reader allowlist、合法页面名不误伤、独立 page/delivery 状态、来源级 degraded 和写前失败保护；补充 `source_uri` 三方一致性门禁，防止 manifest、snapshot、ledger 被错误 URI 串联；补齐 Claim provenance 缺字段和 fingerprint 不一致的写前失败断言。
- **executed_commands**：定向门禁与来源闭环测试 exit 0，`45 passed`；全量 `uv run --frozen pytest -q` exit 0，`341 passed, 2 skipped`。
- **evidence_refs**：`[{"ref":"quality/tests/phase-2-writeback-final.json","sha256":"aabdec18da62a30aa7ab951ddae9648d667fd420ab5ed0d266ca2ca3aa777116","kind":"test"}]`
- **repair_evidence_refs**：`quality/tests/build-code-full-final-v5.json`、`quality/tests/verify-code-full-final-v6.json`（同一当前快照的全量回归收据）。
- **covered_ac**：`AC-001`、`AC-002`、`AC-003`、`AC-004`、`AC-007`。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-e242c318c63cc71c0bc1606a721fbabfe283930d-eff338ff-e628-4f1d-bbfc-30a9ffea52b2.json","sha256":"f034f693747fb65fddb718f07dfb201e99c6213db0e3e0d38446a4169d52f975"}`
- **completed_at**：`2026-08-04T13:03:00+08:00`

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
AC-005、AC-006、AC-007 的 allowlist、真实 pending、空页、断链、来源定位、旧路径映射和历史保护断言通过。
### Risks and rollback
只撤销导航投影改动；保留旧 formal 页面和旧入口历史。

#### T005 — Reader/Audit 导航 RED
- **ID**：T005
- **Phase**：Phase 3：Reader/Audit 导航与来源投影
- **goal**：先写出 Reader allowlist、真实 pending、空入口、断链和来源定位的失败断言。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：T004 GREEN；FR-KD-002、FR-KD-005、FR-KD-007、FR-KD-008、FR-KD-010；AC-005、AC-006、AC-007。
- **依赖**：T004
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-KD-002、FR-KD-005、FR-KD-007、FR-KD-008、FR-KD-010
- **AC**：AC-005、AC-006、AC-007
- **动作**：在 `tests/acceptance/test_task0_reader_package.py` 写入 Reader 正向 allowlist、Audit 来源可定位、真实 pending、链接完整性以及不再生成 `_digest/source-index.md`/`_digest/source-index.jsonl` 的 RED 测试；为 `kb_structure.py` 的新运行入口、既有调用方迁移、旧 source-index 历史只读路径和旧路径到 `indexes/sources.md` 的真实映射书写预期断言；`kb_structure.py` 及调用方的实现迁移只在 T006 发生。
- **精确文件**：`tests/acceptance/test_task0_reader_package.py`、`tests/acceptance/test_publication_contract.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：files: `tests/acceptance/test_task0_reader_package.py`, `tests/acceptance/test_publication_contract.py`, `tests/acceptance/test_task2_publication.py`; symbols/regions: Reader/Audit package, navigation assertions, current generated-path expectations and historical source-index compatibility only.
- **输出**：可复现的 Reader 污染、空入口或断链失败证据。
- **Knowledge**：Reader 只含 README/Home/现有结构导航/主题页/`indexes/sources.md`。
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：1
- **oracle**：ORACLE-TASK0-READER — same contract oracle: RED must show the expected Reader/Audit or navigation boundary failure with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T005.stdout`
- **STOP**：断链由测试 fixture 产生而不是导航规则时停止。
- **recovery**：删除当前测试 bytes，保留旧导航历史。
- **task risk**：allowlist 测试可能漏掉 `_queues` 或 provider 原始响应，需保持正向清单。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 `tests/acceptance/test_task0_reader_package.py` 的 Reader/Audit、真实 pending、空入口、断链和旧 source-index 停止写入 RED 断言；同步迁移 `test_publication_contract.py` 与 `test_task2_publication.py` 的来源入口断言。
- **executed_commands**：RED：`uv run --frozen pytest -q tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`（exit 1，预期 Reader/Audit 边界失败）；GREEN：同命令（exit 0，44 passed）。
- **evidence_refs**：`[{"ref":"quality/tests/phase-3-reader-final-fixed.json","sha256":"0c7110630d79599205fc3ea4142dc29a3cca0d0c00c73abfe6f9030e15950257","kind":"test"}]`
- **covered_ac**：AC-005、AC-006、AC-007
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-5a54d4a8dab712c489643c45624b08230ba2fab2-8cc5cec3-dd5e-47b5-aa11-8af73a90fa98.json","sha256":"05a054b3180bacd5e3095d9331c8cf76ffc72635678bdaf835ecd307da9f1a6a"}`
- **completed_at**：`2026-08-04T13:17:17+08:00`

#### T006 — Reader/Audit 导航 GREEN
- **ID**：T006
- **Phase**：Phase 3：Reader/Audit 导航与来源投影
- **goal**：实现正向 Reader allowlist、Audit 来源投影、真实 pending 和同一发布事务的导航检查。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：T005 RED 输出；FR-KD-002、FR-KD-005、FR-KD-007、FR-KD-008、FR-KD-010；AC-005、AC-006、AC-007。
- **依赖**：T005
- **并行**：否 — same contract as T005
- **FR**：FR-KD-002、FR-KD-005、FR-KD-007、FR-KD-008、FR-KD-010
- **AC**：AC-005、AC-006、AC-007
- **动作**：在 `src/knowledge_digest/navigation.py`、`page_layout.py`、`kb_structure.py` 实现 Reader/Audit allowlist、`indexes/sources.md` 投影、真实 pending 和链接阻断；在 `pipeline.py` 的 `_write_source_index` 调用边界停止新运行生成 `_digest/source-index.md` 与 `_digest/source-index.jsonl`，只读保留历史文件并记录旧路径→`indexes/sources.md` 映射；逐项迁移现有调用方和测试。
- **精确文件**：`src/knowledge_digest/navigation.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_publication_contract.py`、`tests/acceptance/test_task2_publication.py`
- **boundary**：files: `src/knowledge_digest/navigation.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/kb_structure.py`, `src/knowledge_digest/pipeline.py`, `tests/acceptance/test_publication_contract.py`, `tests/acceptance/test_task2_publication.py`; symbols/regions: existing navigation, page layout, `_write_source_index` and its `.md`/`.jsonl` call sites, publication defaults and current generated-path expectations only.
- **输出**：GREEN 测试、无空入口/断链的 Reader Package 和可定位 Audit 事实。
- **Knowledge**：新运行不生成新的 `_digest/source-index.md` 或 `_digest/source-index.jsonl`；`_digest/source-manifest.json` 是唯一 Audit 事实源，历史 source-index 文件不迁移、不重写。
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：0
- **oracle**：ORACLE-TASK0-READER — same contract oracle: RED must show the expected Reader/Audit or navigation boundary failure with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T006.stdout`
- **STOP**：任何审计现场进入 Reader 或导航失败晚于 writeback 时停止。
- **recovery**：撤销当前导航源文件修改，保留旧入口和历史结果。
- **task risk**：把 Reader 投影误当第二事实源会引起增量分叉。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新运行将来源投影写入 `indexes/sources.md`，来源目标使用可点击的 Reader 相对链接；主题页提供返回来源索引的入口；来源索引发现历史目标页缺失时 fail-closed，不再发布断链投影；不再创建 `_digest/source-index.md`/`.jsonl`；默认初始化不生成空 pending；导航按实际内容生成父/子/叶分类，空运行保持干净 Home；旧结构中的 legacy source-index 路径规范化为新的 Reader 入口但不改写历史文件；保留来源 manifest 为 Audit 事实源并完成 Reader 链接与 allowlist 校验；补充失败来源只留在 Audit、不进入 Reader 导航的端到端断言。
- **executed_commands**：Reader/来源闭环/写前门禁/运行审计定向测试 exit 0，`46 passed`；全量 `uv run --frozen pytest -q` exit 0，`342 passed, 2 skipped`；`git diff --check`（exit 0）。
- **evidence_refs**：`[{"ref":"quality/tests/phase-3-reader-final-fixed.json","sha256":"0c7110630d79599205fc3ea4142dc29a3cca0d0c00c73abfe6f9030e15950257","kind":"test"}]`
- **repair_evidence_refs**：`quality/tests/build-code-full-final-v5.json`、`quality/tests/verify-code-full-final-v6.json`（同一当前快照的全量回归收据）。
- **covered_ac**：AC-005、AC-006、AC-007
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-5a54d4a8dab712c489643c45624b08230ba2fab2-8cc5cec3-dd5e-47b5-aa11-8af73a90fa98.json","sha256":"05a054b3180bacd5e3095d9331c8cf76ffc72635678bdaf835ecd307da9f1a6a"}`
- **completed_at**：`2026-08-04T13:17:17+08:00`

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
### STOP
出现凭据落盘、离线触网、预算超限仍成功、题集缺项或 Task0 试图做读者门时停止。
### Done
AC-004、AC-008、AC-009、AC-010 的运行字段、题集 hash、fallback 和调用计数断言通过。
### Risks and rollback
撤销本 Phase 的审计字段和测试变更；不删除已存在的历史 run 记录。

#### T007 — 运行审计 RED
- **ID**：T007
- **Phase**：Phase 4：离线、语义 fallback、题集与运行审计
- **goal**：先写出 provider/fallback/预算、凭据安全、题集 17+3 和离线零调用的失败断言。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：T006 GREEN；FR-KD-004、FR-KD-006、FR-KD-011、FR-KD-012、FR-KD-013；AC-004、AC-008、AC-009、AC-010。
- **依赖**：T006
- **并行**：否 — ordered RED/GREEN
- **FR**：FR-KD-004、FR-KD-006、FR-KD-011、FR-KD-012、FR-KD-013
- **AC**：AC-004、AC-008、AC-009、AC-010
- **动作**：先只读核对 `config/knowledge-digest.json`、`evidence/phase4/real-service-acceptance.json` 和 `evidence/phase4/calibration-artifact.json` 的 provider identity、dimension、probe fingerprint 和 calibration hash；再在 `tests/acceptance/test_task0_runtime_audit.py` 写入离线网络计数、fallback、预算超限、凭据排除、题集字段和增长报告 RED 测试。核对失败必须 RED 失败，不能用实现阶段新值替代。
- **精确文件**：`tests/acceptance/test_task0_runtime_audit.py`
- **boundary**：files: `tests/acceptance/test_task0_runtime_audit.py`; symbols/regions: runtime audit, question-set and provider safety assertions only.
- **输出**：可复现的离线、fallback、预算或题集合同失败证据。
- **Knowledge**：fallback 成功不等于语义 released；题集是后续读者门的固定输入；题目从 PRD Task 2/Task 3 读者验收要求和 decision-log 决定 9 派生，原文整理必须服从 `derivation_rules`。
- **verification_role**：RED
- **paired_task**：T008
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_task0_runtime_audit.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：1
- **oracle**：ORACLE-TASK0-RUNTIME — same contract oracle: RED must show the expected runtime audit, offline, fallback or question-set boundary failure with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T007.stdout`
- **STOP**：测试触发网络、凭据或 provider 进程而非受控 fixture 时停止。
- **recovery**：删除当前测试 bytes，保留历史 provider 和运行记录。
- **task risk**：真实 provider 误调用会破坏离线合同，必须使用受控计数 fixture。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增 `test_task0_runtime_audit.py` 的离线零调用、语义 fallback、预算、凭据排除、17+3 题集和异常增长 RED 断言。
- **executed_commands**：RED：同 Phase 4 gate 命令（exit 1，预期运行审计合同失败）；GREEN：`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_task0_runtime_audit.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_architecture_optimization.py tests/acceptance/test_phase1_loss_prevention.py tests/acceptance/test_phase25_llm.py tests/acceptance/test_phase2_5_append_only_durability.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py tests/acceptance/test_task2_publication.py`（exit 0，193 passed，2 skipped）。
- **evidence_refs**：`[{"ref":"quality/tests/build-code-full-final-v3.json","sha256":"bd39b8a7b65f0f57128c4de91fd72cb82ac984fdf3887548aeec744714242971","kind":"test"}]`
- **covered_ac**：AC-004、AC-008、AC-009、AC-010
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-7e943c5245520d8c0cb9d7355b8b6e7bb89ba3cb-3739ddd8-876a-4980-a69c-ea1566d33b93.json","sha256":"03c295e59ba3489847374bdc2cc3e2eb93cd2af90911a758eddeea0b6019e99a"}`
- **completed_at**：`2026-08-05T07:00:00+08:00`

#### T008 — 运行审计 GREEN
- **ID**：T008
- **Phase**：Phase 4：离线、语义 fallback、题集与运行审计
- **goal**：实现运行 manifest/status/audit 字段、题集 17+3、离线零调用和透明 fallback/预算边界。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task0-knowledge-publication/spec.md","hash":"9c9a87ca8209c79bc27810118f3db8f2cc7437febdb1118d79c337047fe9e3eb","id":"SPEC-TASK0"},{"artifact_kind":"plan","ref":"specs/task0-knowledge-publication/plan.md","hash":"011461df63885fedb6ce38e3ca375c221a414aba6fad50b42a4dffd00a1d4400","id":"PLAN-TASK0"}]`
- **输入**：T007 RED 输出；FR-KD-004、FR-KD-006、FR-KD-011、FR-KD-012、FR-KD-013；AC-004、AC-008、AC-009、AC-010。
- **依赖**：T007
- **并行**：否 — same contract as T007
- **FR**：FR-KD-004、FR-KD-006、FR-KD-011、FR-KD-012、FR-KD-013
- **AC**：AC-004、AC-008、AC-009、AC-010
- **动作**：在 `src/knowledge_digest/draft.py`、`publication.py`、`batch_run.py`、`pipeline.py` 实现运行审计、题集 manifest、离线零调用和 fallback/预算状态；由 `batch_run.py` 的 run report/failure report 输出 AC-009/FR-KD-013 的内容级增长定位，至少记录 snapshot、Claim、duplicate、run 和 archive 记录及其增长差异，不使用全局文件体积阈值；manifest/status/audit 的 provider identity、dimension、probe fingerprint 和 calibration hash 必须来自 T007 已核对的只读事实，不得自行改写。
- **精确文件**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/publication.py`、`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`config/task0-question-set.v1.json`
- **boundary**：files: `src/knowledge_digest/draft.py`, `src/knowledge_digest/publication.py`, `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/pipeline.py`, `config/task0-question-set.v1.json`; symbols/regions: existing draft, publication, batch and pipeline contracts plus the frozen Task0 question-set manifest only.
- **输出**：GREEN 测试、可重放题集 manifest、运行安全字段、AC-009 内容级异常增长定位报告和 fallback/not_released 事实。
- **Knowledge**：provider 凭据只来自环境变量，不能写入日志、报告或知识库；题集 manifest 只保存 DEC-004 冻结的 17+3 题集字段和 hash，`sample_seed` 固定为 `knowledge-digest-task0-v1`，`reviewer` 固定为 `task3-independent-human-reviewer` 预注册角色，实际姓名/日期延期到 Task 3；运行审计的状态/provider/budget 参数按计划冻结并进入既有 manifest/status/audit 断言；embedding 配置原始 endpoint `https://llm.paxszapp.com/v1` 与历史 evidence 的 `https://llm.paxszapp.com:443/v1` 比较前按 scheme/host 小写、去 HTTPS 默认端口、保留 `/v1` 归一化，T007 断言归一化相等，T008 的 `embedding_endpoint` 只写 canonical `https://llm.paxszapp.com/v1`；`written` 必须与 `writeback`、`published`、`released` 独立；1024 维、probe `cc7ae744e79a19a32ca64d3274e11b3e2ea0611cf4c0f58cebc49e950fc6ed2c`、calibration `c31b1f8c78a889dff4cdbbab0fb695871c513844b5c8392d52dbbd8ad33e4c06`、180 秒 timeout、1 次 replay、4×来源数 call、180 次 planned generator、1800/3600 秒 wall-clock 都必须断言；provider identity 和 hash 先与只读 config/phase4 evidence 对齐，题目原文按 PRD/decision-log 派生并记录 derivation_rules。
- **verification_role**：GREEN
- **paired_task**：T007
- **gate_cmd**：`python -m pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_task0_runtime_audit.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_publication.py`
- **expected_exit**：0
- **oracle**：ORACLE-TASK0-RUNTIME — same contract oracle: RED must show the expected runtime audit, offline, fallback or question-set boundary failure with exit 1; GREEN must show the same targeted assertions passing with exit 0; unrelated setup failure is invalid.
- **evidence_path**：`apply/evidence/T008.stdout`
- **STOP**：任何语义 fallback 被写成 released、预算超限被写成成功或离线产生网络调用时停止。
- **recovery**：撤销当前四个源文件的修改；若本任务已创建 `config/task0-question-set.v1.json`，一并删除该 NEW 文件；不删除历史 run 记录或只读证据。
- **task risk**：运行审计字段过多会增加维护成本，只保留规格要求的可重放事实。

##### 执行状态填写区（唯一完成权威）
- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `batch_run.py`、`pipeline.py`、`config/task0-question-set.v1.json` 和 `test_task0_runtime_audit.py` 实现运行 manifest/status/audit、provider/fallback/预算边界、离线零调用和内容级增长审计；按职责复核了 T008 声明的 `draft.py`、`publication.py`，两者无需改动，相关运行审计落在现有 `pipeline.py`/`batch_run.py` 边界内。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_task0_manifest_contract.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_task0_runtime_audit.py tests/acceptance/test_task0_writeback_gate.py tests/acceptance/test_architecture_optimization.py tests/acceptance/test_phase1_loss_prevention.py tests/acceptance/test_phase25_llm.py tests/acceptance/test_phase2_5_append_only_durability.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py tests/acceptance/test_task2_publication.py`（exit 0，193 passed，2 skipped）；`git diff --check`（exit 0）。
- **evidence_refs**：`[{"ref":"quality/tests/build-code-full-final-v3.json","sha256":"bd39b8a7b65f0f57128c4de91fd72cb82ac984fdf3887548aeec744714242971","kind":"test"}]`
- **covered_ac**：AC-004、AC-008、AC-009、AC-010
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-7e943c5245520d8c0cb9d7355b8b6e7bb89ba3cb-3739ddd8-876a-4980-a69c-ea1566d33b93.json","sha256":"03c295e59ba3489847374bdc2cc3e2eb93cd2af90911a758eddeea0b6019e99a"}`
- **completed_at**：`2026-08-05T07:00:00+08:00`

## 3. Dependency Graph
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008。

## 4. Requirement and Verification Traceability
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

## 5. Final Boundary Check
当前任务只定义实现顺序、文件边界、测试门和交接证据；不声明任何任务已完成，不创建额外进度状态机。
