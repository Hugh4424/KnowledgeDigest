# 任务清单：OKF-compatible Reader Bundle 基础与正向机器信号

> 基于当前 spec 和 plan 的可执行投影。当前新增 D-004/Phase 4；本文件不把缺失的 review receipt、固定 parser commit 或真实 raw corpus 写成完成事实。

- **Input**：`specs/task2a-knowledge-publication-reader-bundle/spec.md`（`task2a-spec-v1-draft`，SHA-256 `62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e`）、`specs/task2a-knowledge-publication-reader-bundle/plan.md`（`task2a-plan-draft`，SHA-256 `fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425`）
- **Status**：Draft/in_progress — 4 个 Phase、10 个 Task；T009/T010 已完成；技术 aggregate 已通过；本次 build-plan/verify-code formal review、current receipts 和 human confirmation 仍因 WorkflowHub bundle mismatch/缺宿主确认而 incomplete，历史 T001–T008 执行事实只读保留
- **Template version**：`plan-task.v3`

## 1. 执行摘要

- **Goal**：隔离生成 3 个 concept fixture 的 Reader Bundle，完成结构、归因、离线、parser smoke 和页面级正向机器信号证据；包级保持 `not_released`。
- **Main boundary**：只改 Phase Files 声明的 Bundle API、PyYAML lock、测试、vendor 和本次 trust projection；`artifact_root/reports/*` 与 `artifact_root/audit/trust-signals/*.json` 是运行时事实源，task-relative evidence 只由 runner/build-code 复制、哈希和回读；不改正式 pipeline、CLI、旧 Reader/Audit、正式知识库或原始语料。
- **Main risk**：真实 raw corpus 和固定 parser commit 尚未可用；缺输入时按 STOP，不虚构 fixture、兼容或成功证据。
- **Current handoff**：T009→T010 已完成；下一步只剩 formal verify-code receipt/confirmation，不再重复 build-code

## WorkflowHub Stage Progress

> 这是阶段摘要，不是 completion ledger。任务完成状态仍只由每张卡的“执行状态填写区”决定。

| Stage | Status | Task / phase IDs | Execution / evidence | Handoff / next |
| --- | --- | --- | --- | --- |
| build-code | completed | T009–T010；Phase 4（T001–T008 历史已执行） | `quality_status=technical-pass/formal-review-unavailable`；focused 7 passed、Bundle 34 passed；当前 changed-file 路由为 `fullstack` / `fullstack-slice-testing` | `user_handoff=进入 verify-code；raw corpus、parser commit、入口 backfill 事实不得猜测` |
| verify-code | in_progress | AC-01–AC-08；`ORACLE-TASK2A-AGGREGATE` | `quality_status=technical-pass/incomplete`；aggregate 123 passed/1 skipped；formal independent receipt 与 human confirmation 尚缺 | `user_handoff=保留真实 skip 和 WorkflowHub unavailable；不写 formal pass` |

## 2. Global Constraints

- 继承 `spec.md` 的 R-001–R-009、D1–D3、D-004、FR、AC、OPEN 和明确 non-goals；正文语义、LLM、embedding、人工 reader gate、全量发布、OKF runtime 不在本任务内。
- 行为变化必须先有真实 RED，再做 GREEN；RED/GREEN 使用相同 `gate_cmd` 和 oracle。
- `display_cmd` 只供阅读，不能作为 pass/fail 判据；证据必须是 task-relative canonical ref。
- 文件路径必须精确、无通配符；Task 的 `精确文件` 和 `execution_file_paths` 必须是所属 Phase NEW/MODIFY 的子集。
- `artifact_root` 由调用方显式提供，必须是新建空的非 symlink 目录；调用方保证单写者/串行使用。Bundle、Audit、Report 必须在同一隔离 root 内，投影先写 run-scoped staging，校验后原子提交，不能写正式 KB；不创建 owner lock 或并发 contention 协议。
- `--no-llm` 必须通过现有 `cli.main`/`digest` 路径和 runtime audit 证明 `calls.llm=0`、`calls.embedding=0`；网络零请求由 acceptance fixture 在测试边界安装 deny-only socket guard 证明。Bundle API 不新增生产级 guard/context，也不能替代 CLI oracle。
- **AC-07 concrete execution**：每次 Bundle acceptance fixture 先执行 `uv run --frozen digest <tmp>/new <tmp>/cli-kb --config <tmp>/offline.json --no-llm`（offline JSON 固定 `jaccard`、`llm_enabled=false`、`llm_summary_enabled=false`），expected exit `0`，读取 `<tmp>/cli-kb/_digest/runs/<run_id>/report.json` 的 `runtime_audit.calls`；再以 `offline_mode="no-llm"` 调用 Bundle API 写 `<tmp>/artifact-root`。测试边界 deny-only socket guard 只写 `attempt_ref`、argv hash、guard mode、`connect_attempts=0` 到 `quality/evidence/task2a-reader-bundle/cli-offline-guard.txt`，不向生产 API 传 counter/context。
- 失败、冲突、无归属或未通过门禁的内容只能进入隔离 degraded evidence，不能进入 Reader 导航；降级不能写 `okf_version` 或冒充 `compatibility_passed`。按 accepted AC-08 口径，完整可审计的 failed/unavailable 可以得到 `honest_downgrade_passed`，事实缺失仍 blocked。
- 正向信号只允许 `generated`、`digest_machine_pass`、`source_hash_match`、`locator_resolved`；每个 verified event 必须带固定 process actor、detector version、输入 fingerprint、当前 content hash 和 audit evidence。没有 freshness evidence 省略 `stale_after`；不生成 `critical_token_recheck`、`sampled_entailment`、`human:` 或 `agent_assisted`。
- 完成区只由 build-code/verify-code 在实际实现、测试、Phase review 后填写；本次生成不预填任何 receipt、hash、review 或完成时间。

### Test strategy fields (build-plan designs; build-code only executes)

- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：Phase 1/2/3 和最终聚合预判为 `fullstack`；预期使用 `fullstack-slice-testing`，因为改动跨 `src`、acceptance、依赖锁、fixture/vendor 和隔离 evidence；build-code 必须按真实 changed files 重判。
- **scenarios / commands / expected exit / oracle**：RED/GREEN 使用同一专项 pytest command；覆盖 round-trip/hash、Bundle tree、状态、路径、allowlist、入口回读、归因、幂等、zero-provider、parser pass/downgrade。
- **fixtures_services**：`tmp_path`、本地 fixture、已 vendor 文件；无浏览器、无常驻服务、无网络；raw corpus 只用于受控人工选样，不提交仓库。
- **browser_route**：N/A — no UI。
- **evidence_path**：各 Task 卡声明的精确相对路径；最终聚合为 `quality/evidence/task2a-reader-bundle/final-aggregate.txt`。
- **coverage limits**：不覆盖 89 篇正文语义、Task 2-B/2-C reader quality、正式 release 或旧 S1–S6 写回实现。
- **execution_contract**：build-code 先核对真实 changed-file range；若超出 Phase Files，停止并重新路由；缺策略写 `MATERIAL_INCOMPLETE`。
- **final current-snapshot aggregate strategy**：专项 frontmatter → Bundle → parser gate；正式聚合 gate 为 `pytest tests/acceptance/test_task2a_reader_frontmatter.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2a_okf_smoke.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task1_topic_axis.py -q`，expected exit `0`，oracle `ORACLE-TASK2A-AGGREGATE`，evidence `quality/evidence/task2a-reader-bundle/final-aggregate.txt`；它验证新 Bundle AC-01–AC-08 相关路径与旧 Reader/Task 1 核心行为无漂移。`uv run --frozen pytest tests/ -q` 只作为可选 full-tree display/diagnostic，不作为本任务的第二个验收命令。
- **aggregate self-contained gate**：该命令只在 build-code 按真实 changed files 完成路由后执行；fixtures/services 为 `tmp_path`、仓库内已核验 fixture/vendor、Task 0/1 只读 backfill refs，以及 acceptance 边界的 deny-only socket/provider guard；不启动常驻服务、不触网、不需要模型或凭据。coverage limits 是本任务声明的 27 FR/8 AC、旧 Reader/Task 1 回归和 allowlist 内文件，不能证明正文语义、正式 release、Task 2-B/2-C 或未声明文件。执行前 STOP 条件包括：当前 plan/tasks component receipt 没有匹配当前材料 hash；current review/confirmation 事实缺失却被写成通过；AC-03 的 raw corpus/fixture 或 AC-08 的 vendor provenance 缺失；现有 CLI runtime audit 缺少或 `calls.llm`/`calls.embedding` 非零，或 deny-only socket guard 缺失/失败；AC-08 结果 provenance 缺失或含糊；gate exit 非零；或 changed files 超出 Phase Files/DO NOT TOUCH。aggregate evidence 必须同时记录 command、exit、oracle、当前 snapshot、覆盖范围、STOP 判定和 evidence SHA-256。
- **TaskKernel/evidence_refs**：执行时填写实际 command、exit code、当前 snapshot、canonical receipt 和 evidence SHA-256；当前为空。

### Source handoff coverage (task-local direct refs)

每张 task card 的 `source_refs / decision_refs` 必须直接列出它消费的 frozen source/finding，不只依赖本表或 plan 的反向索引：

| Finding/source | Direct task cards | Required handoff |
| --- | --- | --- |
| F-001 parser research/license provenance | T007/T008 | `docs/research/20260806-okf-structure-research.md`、实际 vendor source/commit/license/notice bytes；只在 AC-08 evidence 中消费 |
| F-003 frozen aliases/lifecycle/status mapping | T001–T010 | 每卡直接引用 F-003，并逐项绑定 `FR-STATUS-001`、`FR-STATUS-002`、`FR-STATUS-003`；不能使用未枚举的 status FR ID |
| R-008 accepted AC/`not_released` boundary | T001–T010 | 每卡的 FR/AC 和 STOP 必须与 frozen spec/decision contract 对齐 |
| D-004 positive machine signal revision | T009/T010 | 只消费 source/Claim/selection 的 fingerprint/locator 证据；不扩展为 Task 2-C reader gate |

## Phase 1：Frontmatter 与受管 hash

### Goal

在不影响旧 Reader 的前提下，提供固定 PyYAML nested frontmatter round-trip 和受管 `digest_content_hash`。

### Files

- **NEW**：`src/knowledge_digest/reader_frontmatter.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`
- **MODIFY**：`pyproject.toml`; `uv.lock`
- **DO NOT TOUCH**：`src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `tests/acceptance/test_task0_reader_package.py`; `tests/acceptance/test_publication_contract.py`; `tests/acceptance/test_task1_topic_axis.py`

### Tasks

#### T001 — RED：nested frontmatter round-trip/hash 失败断言

- **ID**：T001
- **Phase**：Phase 1：Frontmatter 与受管 hash
- **Workflow stage**：`build-code`
- **goal**：用可导入 stub 和失败测试固定 nested unknown field、sources/generated/verified 保留、serializer 参数和受管 hash 排除规则。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-002/R-003/F-003 → D1 → FR-FRONT-001/002/005、FR-PROJ-002 → AC-02/06。
- **输入**：spec §7 FRONT/PROJ；现有 `kb_structure` 简单 frontmatter 行解析事实。
- **依赖**：N/A — first task。
- **并行**：否 — 后续 Task 必须消费同一 frontmatter 边界。
- **FR**：FR-FRONT-001、FR-FRONT-002、FR-FRONT-005、FR-PROJ-002。
- **AC**：AC-02（frontmatter portion）、AC-06。
- **动作**：只添加 RED 测试和可导入 stub；不实现成功行为。
- **精确文件**：`src/knowledge_digest/reader_frontmatter.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`
- **execution_file_paths**：`["src/knowledge_digest/reader_frontmatter.py","tests/acceptance/test_task2a_reader_frontmatter.py"]`
- **boundary**：files: `src/knowledge_digest/reader_frontmatter.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`; symbols/regions: `parse_concept_document`、`serialize_concept_document`、`managed_content_hash` stub 和对应 tests。
- **输出**：目标行为的非零 RED；失败原因必须是 contract 未实现，不是 import、依赖或 fixture 损坏。
- **Knowledge**：现有 parser 只支持简单行；PyYAML 尚未锁定；不能用旧 parser 伪装 nested support。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing` 预判；跨 `src` 和 `tests`，但只执行本专项命令。
- **scenarios / commands / expected exit / oracle**：nested unknown field、嵌套 sources/generated/verified、易变字段 hash 排除；`pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`；预期 `1`；`ORACLE-FM-ROUNDTRIP`。
- **fixtures_services**：`tmp_path`；无服务、无网络、无 provider。
- **browser_route**：N/A — no UI。
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`
- **expected_exit**：1
- **oracle**：`ORACLE-FM-ROUNDTRIP`；stdout/stderr 必须指向目标 assertion 或明确的 stub 未实现，而不是 setup failure。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/frontmatter-red.txt`
- **coverage limits**：只覆盖 frontmatter RED；不覆盖 Bundle tree、attribution、parser smoke。
- **execution_contract**：build-code 只能新增本卡文件；真实 diff 超出 Phase 1 NEW/MODIFY 时 STOP 并重路由。
- **TaskKernel/evidence_refs**：待 build-code 绑定当前 snapshot、实际命令/exit、canonical RED receipt 和 `frontmatter-red.txt` SHA-256；当前 N/A — not started。
- **evidence_note**：证据必须证明目标断言失败；import failure、网络失败或缺 fixture 不能作为 RED 证明。
- **STOP**：RED 不是目标断言失败、需要修改旧 parser、或 PyYAML 依赖选择未决时停止。
- **recovery**：恢复本卡 stub/test 到可复现 RED；不修实现、不改 verify 结果。
- **task risk**：import failure 会掩盖真正的 round-trip/hash 缺口。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：`tests/acceptance/test_task2a_reader_frontmatter.py` 的 RED 测试；随后由 T002 消费同一 gate/oracle。
- **executed_commands**：RED `uv run --frozen pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`（exit 1，目标 stub 的 `NotImplementedError`）；paired GREEN `UV_CACHE_DIR=/private/tmp/knowledge-digest-uv-cache-phase1-repair-receipt uv run --frozen pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`（exit 0）。
- **evidence_refs**：`[{"kind":"test_run","ref":"quality/tests/t2a-phase1-frontmatter-repair.json","sha256":"d969b2c3a4b814bf4cab34a7e3a148b3d45dffb4fb4541e3dffa824591462299"},{"kind":"task_record","ref":"quality/evidence/task2a-phase1-map.json","sha256":"bf5b048f4ee8ec332818591a25c1e9382409e5a61b2203d3d4cc040e5c8cb557"},{"kind":"review_fact","ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","sha256":"f361c07f8d16e4c507d699be05fb69217866fb897c655fc8bbafa2efb168ac43"}]`
- **covered_ac**：AC-02（frontmatter portion）、AC-06
- **phase_map_trace**：`{"ref":"quality/evidence/task2a-phase1-map.json","sha256":"bf5b048f4ee8ec332818591a25c1e9382409e5a61b2203d3d4cc040e5c8cb557"}`
- **green_test_receipt**：`{"ref":"quality/tests/t2a-phase1-frontmatter-repair.json","sha256":"d969b2c3a4b814bf4cab34a7e3a148b3d45dffb4fb4541e3dffa824591462299"}`
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","sha256":"f361c07f8d16e4c507d699be05fb69217866fb897c655fc8bbafa2efb168ac43","verdict":"pass"}`
- **finding_dispositions**：`[{"finding_id":"F-95d531cd176d","original_fact":"生成的 review-instructions 未列出未提供的可选材料","source":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","consequence":"审查包说明性略弱，不影响产品行为","status":"accepted_risk","next_action":"保留为 WorkflowHub host-material follow-up；本 Phase 不修改生成模板","evidence_ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","owner":"WorkflowHub host owner","consumer":"build-code/verify-code","retain_or_delete":"retain"},{"finding_id":"F-cd12c6666085","original_fact":"Phase acceptance_map 只列 AC-02/AC-06，未列其他六项","source":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","consequence":"本 Phase 的 map 不展示后续 Phase 的 AC 覆盖","status":"accepted_risk","next_action":"后续 Phase/integration map 显式补齐其余 AC；本 Phase 仍只负责 AC-02/AC-06","evidence_ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","owner":"build-code","consumer":"verify-code","retain_or_delete":"retain"}]`
- **completed_at**：2026-08-09T13:38:24Z

#### T002 — GREEN：固定 PyYAML 并实现 frontmatter/hash

- **ID**：T002
- **Phase**：Phase 1：Frontmatter 与受管 hash
- **Workflow stage**：`build-code`
- **goal**：让 T001 的 nested round-trip、固定 serializer、未知字段保留和受管 hash 断言通过。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-002/R-003/F-003 → D1 → FR-FRONT-001/002/005、FR-PROJ-002 → AC-02/06。
- **输入**：T001 RED；accepted hash exclusion list；`PyYAML==6.0.2`。
- **依赖**：T001。
- **并行**：否 — RED/GREEN 串行，测试和实现同步；调用方单写者边界由测试 fixture 保证。
- **FR**：FR-FRONT-001、FR-FRONT-002、FR-FRONT-005、FR-PROJ-002。
- **AC**：AC-02（frontmatter portion）、AC-06。
- **动作**：锁定 PyYAML，实现 safe load/dump、固定 YAML 参数、unknown-field 保留和受管 SHA-256。
- **精确文件**：`src/knowledge_digest/reader_frontmatter.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`; `pyproject.toml`; `uv.lock`
- **execution_file_paths**：`["src/knowledge_digest/reader_frontmatter.py","tests/acceptance/test_task2a_reader_frontmatter.py","pyproject.toml","uv.lock"]`
- **boundary**：files: `src/knowledge_digest/reader_frontmatter.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`; `pyproject.toml`; `uv.lock`; symbols/regions: 三个 frontmatter API、PyYAML dependency entry 和对应 tests；禁止改旧 frontmatter parser。
- **输出**：Phase 2 可复用的 frontmatter API；frozen lock 与 project metadata 一致。
- **Knowledge**：只允许 `yaml.safe_load`/`yaml.safe_dump`；不能退回手写行解析。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing` 预判；沿用 T001 行为 gate。
- **scenarios / commands / expected exit / oracle**：同 T001；预期 `0`；`ORACLE-FM-ROUNDTRIP`。
- **fixtures_services**：`tmp_path`；无服务、无网络、无 provider。
- **browser_route**：N/A — no UI。
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`
- **dependency_gate_cmd**：`uv run --frozen python -c "import pathlib, tomllib, yaml; p=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); assert p['project']['dependencies'].count('PyYAML==6.0.2') == 1; assert yaml.__version__ == '6.0.2'"`；并执行 `uv lock --check`。
- **expected_exit**：0
- **oracle**：`ORACLE-FM-ROUNDTRIP`；与 T001 相同 assertion 全部通过，不能删减 nested/hash 负例。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/frontmatter-green.txt`; `quality/evidence/task2a-reader-bundle/pyyaml-lock.txt`
- **coverage limits**：不覆盖 Bundle path/status、fixture attribution 或 external parser。
- **execution_contract**：build-code 先确认 changed files 仅落在 Phase 1 NEW/MODIFY；新增依赖必须与 `uv.lock` 同步。
- **TaskKernel/evidence_refs**：待绑定当前 snapshot、实际命令/exit、GREEN receipt 和 `frontmatter-green.txt` SHA-256；当前 N/A — not started。
- **evidence_note**：GREEN evidence 必须同时证明 nested fields 保留、固定输出可重放、易变字段不改变受管 hash。
- **STOP**：PyYAML 无法 frozen、需要修改旧模块、或必须弱化 T001 断言时停止。
- **recovery**：回到 T001 RED 的模块/test 状态；保留 RED evidence。
- **task risk**：serializer 参数或 hash 白名单漂移会破坏 replay。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：`src/knowledge_digest/reader_frontmatter.py`、`tests/acceptance/test_task2a_reader_frontmatter.py`、`pyproject.toml`、`uv.lock`；实现 safe YAML round-trip、固定 serializer、managed hash 与负例校验。
- **executed_commands**：`UV_CACHE_DIR=/private/tmp/knowledge-digest-uv-cache-phase1-repair-receipt uv run --frozen pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`（exit 0）；`UV_CACHE_DIR=/private/tmp/knowledge-digest-uv-cache-phase1-repair-lock-receipt uv run --frozen python -c 'import pathlib, tomllib, yaml; p=tomllib.loads(pathlib.Path("pyproject.toml").read_text()); assert p["project"]["dependencies"].count("PyYAML==6.0.2") == 1; assert yaml.__version__ == "6.0.2"' && UV_CACHE_DIR=/private/tmp/knowledge-digest-uv-cache-phase1-repair-lock-receipt uv lock --check`（exit 0）；既有回归 `uv run --frozen pytest tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task1_topic_axis.py -q`（75 passed, 1 skipped）。
- **evidence_refs**：`[{"kind":"test_run","ref":"quality/tests/t2a-phase1-frontmatter-repair.json","sha256":"d969b2c3a4b814bf4cab34a7e3a148b3d45dffb4fb4541e3dffa824591462299"},{"kind":"test_run","ref":"quality/tests/t2a-phase1-pyyaml-lock-repair.json","sha256":"2d69d752c3010bdc7c15e6ec647cf1003f065e00268082c415ebcba52cbc02de"},{"kind":"task_record","ref":"quality/evidence/task2a-phase1-map.json","sha256":"bf5b048f4ee8ec332818591a25c1e9382409e5a61b2203d3d4cc040e5c8cb557"},{"kind":"review_fact","ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","sha256":"f361c07f8d16e4c507d699be05fb69217866fb897c655fc8bbafa2efb168ac43"}]`
- **covered_ac**：AC-02（frontmatter portion）、AC-06
- **phase_map_trace**：`{"ref":"quality/evidence/task2a-phase1-map.json","sha256":"bf5b048f4ee8ec332818591a25c1e9382409e5a61b2203d3d4cc040e5c8cb557"}`
- **green_test_receipt**：`{"ref":"quality/tests/t2a-phase1-frontmatter-repair.json","sha256":"d969b2c3a4b814bf4cab34a7e3a148b3d45dffb4fb4541e3dffa824591462299"}`
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","sha256":"f361c07f8d16e4c507d699be05fb69217866fb897c655fc8bbafa2efb168ac43","verdict":"pass"}`
- **finding_dispositions**：`[{"finding_id":"F-95d531cd176d","original_fact":"生成的 review-instructions 未列出未提供的可选材料","source":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","consequence":"审查包说明性略弱，不影响产品行为","status":"accepted_risk","next_action":"保留为 WorkflowHub host-material follow-up；本 Phase 不修改生成模板","evidence_ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","owner":"WorkflowHub host owner","consumer":"build-code/verify-code","retain_or_delete":"retain"},{"finding_id":"F-cd12c6666085","original_fact":"Phase acceptance_map 只列 AC-02/AC-06，未列其他六项","source":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","consequence":"本 Phase 的 map 不展示后续 Phase 的 AC 覆盖","status":"accepted_risk","next_action":"后续 Phase/integration map 显式补齐其余 AC；本 Phase 仍只负责 AC-02/AC-06","evidence_ref":"quality/reviews/results/build-code-default-3dcd18eefaca4d46bc18c5d5dd65780aebcf64b4-eee74400-b616-4f31-a3c0-d62a414404c7.json","owner":"build-code","consumer":"verify-code","retain_or_delete":"retain"}]`
- **completed_at**：2026-08-09T13:38:24Z

### Verify

- **Target**：FR-FRONT-001/002/005、FR-PROJ-002、AC-02 的 frontmatter portion、AC-06。
- **Acceptance items**：

  | AC ID | Scenario / action | Oracle / expected result | Evidence ref |
  | --- | --- | --- | --- |
  | AC-02 | parse concept frontmatter and check legal fields | PyYAML safe round-trip、非空 type、受管字段规则成立 | `quality/evidence/task2a-reader-bundle/frontmatter-green.txt` |
  | AC-06 | round-trip nested extension and managed hash | unknown nested fields survive；易变字段变化不改变 managed hash | `quality/evidence/task2a-reader-bundle/frontmatter-green.txt` |

- **Task coverage**：T001 → AC-02/AC-06 RED；T002 → AC-02/AC-06 GREEN。
- **Cross-task seam**：T002 必须消费 T001 的同一 gate/oracle；Phase 2 不得自建第二套 YAML/hash。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_frontmatter.py -q`
- **expected_exit**：0 after T002; T001 RED expected non-zero。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/frontmatter-green.txt`
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_reader_frontmatter.py -q -vv`
- **Oracle**：`ORACLE-FM-ROUNDTRIP`。

### Knowledge

现有 `kb_structure` frontmatter 只支持简单行；accepted contract 要求固定 PyYAML safe API、nested round-trip 和受管 hash。

### STOP

- RED 若因环境、依赖、命令或 fixture 损坏而失败，不得计入。
- GREEN 若需要扩大 Phase Files、绕过 frontmatter API 或新增架构决策，停止。

### Done

T001 有目标性非零 RED；T002 用相同 gate/oracle 通过；PyYAML lock、unknown-field round-trip 和 managed hash 有真实 evidence。

### Risks and rollback

- **Risk**：serializer 与 hash 规则不一致。
- **Prevention**：固定 YAML 参数、字段白名单和同一 oracle。
- **Rollback / recovery**：恢复 T001 RED；不触碰旧 Reader 文件。

## Phase 2：隔离 Bundle projection、validator 与 attribution fixture

### Goal

在 `tmp_path` output root 生成固定 Reader Bundle tree、三类真实样本 fixture、source projection、结构 validator 和 `not_released` projection report。

### Phase Card — Phase 2

- **goal**：隔离实现 Bundle projection、validator、entry readback/backfill 和三类 fixture 的结构边界。
- **allowed files**：本 Phase `NEW` 文件及 T003/T004/T005/T006 卡片声明的 `execution_file_paths`；运行时产物只写调用方提供的 artifact root。
- **covered AC**：AC-01、AC-02、AC-03、AC-04、AC-05、AC-06、AC-07；AC-08 留给后续拥有者。T005/T006 的真实 raw corpus 已经解除原先的 blocked-by-design 条件。
- **non-goals**：不改正式 pipeline、CLI、旧 Reader/Audit、Task 0/1 事实、正文语义或外部 parser smoke。
- **compatibility boundary**：复用 Phase 1 `reader_frontmatter`；不复用旧简单 frontmatter/navigation parser，不把 fixture 事实写入正式 KB。
- **test tier**：先按真实 changed files 重跑 test-routing-advisor，再执行其选定的 focused acceptance gate；无浏览器/常驻服务/网络。
- **STOP**：缺真实 entry backfill/hash、需要扩大 Phase Files、fixture 失去 source/claim provenance、artifact root 越界、或失败被伪装成 released/verified。
- **expected handoff**：交付可重放的隔离 Bundle projection 与结构证据；Phase 3 只消费其 API 和 report，不重建第二套 frontmatter/status 规则。

### Files

- **NEW**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; `tests/fixtures/task2a_reader_bundle/topic-index.json`; `tests/fixtures/task2a_reader_bundle/source-inventory.jsonl`; `tests/fixtures/task2a_reader_bundle/claim-history.jsonl`; `tests/fixtures/task2a_reader_bundle/fixture-selection.json`; `tests/fixtures/task2a_reader_bundle/product-overview.md`; `tests/fixtures/task2a_reader_bundle/module-capability.md`; `tests/fixtures/task2a_reader_bundle/procedure-rule.md`
- **MODIFY**：N/A — reader bundle is created in this Phase and only integrated with parser result in Phase 3；report/manifest 的 product output 只存在于运行时 artifact root，不直接写固定 evidence 目录
- **DO NOT TOUCH**：`src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `src/knowledge_digest/kb_structure.py`; `src/knowledge_digest/identity.py`; `tests/acceptance/test_task0_reader_package.py`; `tests/acceptance/test_publication_contract.py`; `tests/acceptance/test_task1_topic_axis.py`; `quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`; `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`; `quality/evidence/task2-entry/task1-receipt-reconciliation.v1.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/source-inventory.jsonl`; `quality/evidence/task2-entry/task1-real-corpus-20260806/topic-index.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/topic-plan.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/run-report.json`; `quality/evidence/task2-entry/task1-real-corpus-20260806/verification-receipt.json`

### Tasks

#### T003 — RED：Bundle tree/status/allowlist/entry 失败断言

- **ID**：T003
- **Phase**：Phase 2：隔离 Bundle projection、validator 与 attribution fixture
- **Workflow stage**：`build-code`
- **goal**：固定 Bundle 五个入口身份、products/no-module 路径、三层 status、degraded 隔离、allowlist/link、真实 entry binding/backfill readback、verified 证据失效拒绝和 zero-provider 的 RED 断言；product-only 必须走命名 adapter，公共 envelope/rejection codes 不能省略。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-001/R-005/R-006/R-008/R-009/F-002/F-003 → D1 → FR-BUNDLE-001/002/003/005/006、FR-FRONT-003/004/006、FR-STATUS-001/002/003、FR-VALID-001/002、FR-PROJ-001/002、FR-ENTRY-001、FR-LLM-001 → AC-01/02/04/05/06/07。
- **输入**：T002 frontmatter API；`ReaderBundleStructureInputs`（Task 1 TopicIndex v2、source inventory、真实 entry backfill、`input_root` resolver）；accepted allowlist/status/path rules。不得在本卡塞入 T005/T006 的 claim/fixture 正例。
- **依赖**：T002。
- **并行**：否 — consumes T002 and owns the output tree boundary。
- **FR**：FR-BUNDLE-001、FR-BUNDLE-002、FR-BUNDLE-003、FR-BUNDLE-005、FR-BUNDLE-006、FR-FRONT-003、FR-FRONT-004、FR-FRONT-006、FR-STATUS-001、FR-STATUS-002、FR-STATUS-003、FR-VALID-001、FR-VALID-002、FR-PROJ-001、FR-PROJ-002、FR-ENTRY-001、FR-LLM-001。
- **AC**：AC-01、AC-02、AC-04、AC-05、AC-06、AC-07。
- **动作**：只添加 Bundle RED/stub 和结构测试；不实现成功 projection。
- **精确文件**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; `tests/fixtures/task2a_reader_bundle/topic-index.json`; `tests/fixtures/task2a_reader_bundle/source-inventory.jsonl`
- **execution_file_paths**：`["src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_reader_bundle.py","tests/fixtures/task2a_reader_bundle/topic-index.json","tests/fixtures/task2a_reader_bundle/source-inventory.jsonl"]`
- **boundary**：files: Phase 2 NEW subset; symbols/regions: `ReaderBundleStructureInputs`、结构版 `BundleReport`/`BundleValidationReport`、`project_reader_bundle`、`validate_reader_bundle` stub、tree/status/link tests；不得接入正式 pipeline/CLI 或声称 attribution 通过。
- **输出**：目标行为 RED；失败必须来自目标 assertion，不得由 fixture/import/setup failure 伪造。
- **Knowledge**：旧 navigation 只支持旧 `indexes/pages`；新 Bundle 必须使用显式隔离 output root。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing` 预判；跨 source、fixture 和 acceptance。
- **scenarios / commands / expected exit / oracle**：根 `README.md/Home.md/index.md/log.md`、无 nested log、无空 index、豁免文件身份、valid product-only 发布到 `products/{product}/...` 且不虚构 module、product-only 经过 `adapt_topic_index_row` 的正例、malformed/unsupported/uncertain product-only 的 rejection-code 负例必须 degraded、三条 fixture 的 exact `(topic_id, object_intent) → mapping_role → digest_page_type` 对账、title/description fallback、status/version/verified/stale_after 负例、source fingerprint/claim locator/target_path/page type 变化会使 validator 拒绝旧 verified（不自动改写当前页面）、degraded report/page、fresh root/reuse/partial-write recovery、artifact containment、真实 entry refs/hash/schema/version/producer/consumer/coverage、缺入口时 `write_entry_backfill_manifest` 的 not_released 回放、现有 CLI `--no-llm` runtime audit 的 `calls.llm=0`/`calls.embedding=0`，以及测试边界 deny-only socket guard 未触网；`pytest tests/acceptance/test_task2a_reader_bundle.py -q`；预期 `1`；`ORACLE-BUNDLE-TREE`、`ORACLE-STATUS`、`ORACLE-LINKS`、`ORACLE-REPLAY`、`ORACLE-OFFLINE-RELEASE`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-INPUT-ADAPTER`、`ORACLE-ENTRY-READBACK`、`ORACLE-ENTRY-BACKFILL`、`ORACLE-CLI-OFFLINE`。
- **fixtures_services**：local structural fixture + `tmp_path`；无网络、无 provider；synthetic manifest 只覆盖拒绝分支。
- **browser_route**：N/A — no UI。
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q`
- **expected_exit**：1
- **oracle**：`ORACLE-BUNDLE-TREE`、`ORACLE-STATUS`、`ORACLE-LINKS`、`ORACLE-REPLAY`、`ORACLE-OFFLINE-RELEASE`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-INPUT-ADAPTER`、`ORACLE-ENTRY-READBACK`、`ORACLE-CLI-OFFLINE`；目标断言失败，不能只是缺 raw corpus 或命令损坏；verified mutation 必须证明旧核验只留在 audit、validator 拒绝当前页面，不得静默继续 published。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/bundle-red.txt`
- **coverage limits**：不覆盖 attribution 的真实 claim chain 或 external parser compatibility。
- **execution_contract**：build-code 先用显式 `input_root`/resolver 只读回 `quality/evidence/task2-entry` 的逐项声明 refs/hash/schema/version/producer/consumer/coverage；缺失真实入口事实时，结构负例仍可执行，但 AC-02 和 handoff 保持 STOP，并必须由 `write_entry_backfill_manifest` 记录缺口。结构 fixture 可以覆盖 adapter 的合法 product-only 正例，不能替代真实 Task 1 entry backfill，也不能用 synthetic input 关闭 AC-02。
- **TaskKernel/evidence_refs**：待绑定当前 snapshot、实际 RED receipt 和 `bundle-red.txt` SHA-256；当前 N/A — not started。
- **evidence_note**：RED 必须由目标结构/状态/入口断言失败证明；不能用缺 raw corpus、import failure 或网络错误代替。
- **STOP**：输出 root 指向正式 KB、需要 pipeline/CLI 变更、degraded 没有隔离页、真实 entry readback 缺失、或 RED 只因 fixture/setup 失败。
- **recovery**：恢复本卡 stub/test/structural fixture；不修 T004 实现、不补写入口 receipt。
- **task risk**：把旧 Reader navigation 当 Bundle generator 会产生第二套目录事实。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：先按 T003 边界建立结构/失败断言和 fixture，再由 T004 完成 Bundle projection、validator、degraded audit、entry readback/backfill、原子 staging 和 not_released report。早期本地 RED 未生成可认证的 canonical receipt，因此不把它当作通过证据。
- **red_evidence_fact**：`{"status":"unavailable","reason_code":"CANONICAL_RED_RECEIPT_NOT_CAPTURED","scope":"T003 target assertion","note":"本地早期 RED 未保留可认证 canonical receipt；仅以 GREEN、实现 receipt 和 review 作为完成依据。"}`
- **executed_commands**：`UV_CACHE_DIR="${TMPDIR:-/private/tmp}/knowledge-digest-uv-cache-phase2-coverage1" uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q` → exit 0，24 passed；执行了 `fullstack-slice-testing` 路由审查，当前边界无服务/浏览器 slice。
- **evidence_refs**：`[{"ref":"quality/tests/t2a-phase2-bundle-coverage1.json","sha256":"bde7f703bf80f29566273ce05ac3f345d79a3b7eb1594f54bd65a9fdda3fad06"},{"ref":"quality/evidence/implementation/5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2.json","sha256":"5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2"}]`
- **covered_ac**：AC-01、AC-02、AC-04、AC-05、AC-06、AC-07。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-0fd368873a1ba3ac7e51ecca5f1557434503f4d7-5db8ed9f-da9e-46ad-9357-729840678f05.json","sha256":"e422c14beb7391ea9c3406929e273af50b67580d26ea37c664231b484dc4b7d7","snapshot_tree":"0fd368873a1ba3ac7e51ecca5f1557434503f4d7","verdict":"pass","findings":[]}`
- **completed_at**：2026-08-09T23:15:20+08:00

#### T004 — GREEN：实现 Bundle projection/validator

- **ID**：T004
- **Phase**：Phase 2：隔离 Bundle projection、validator 与 attribution fixture
- **Workflow stage**：`build-code`
- **goal**：让 T003 的 Bundle tree、frontmatter/status、allowlist/link、entry readback/backfill、degraded audit/report、replay identity、verified 失效拒绝和 zero-provider assertions 通过；实现 product-only/standard adapter 分支和 commit lifecycle handle。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-001/R-005/R-006/R-008/R-009/F-002/F-003 → D1 → FR-BUNDLE-001/002/003/005/006、FR-FRONT-003/004/006、FR-STATUS-001/002/003、FR-VALID-001/002、FR-PROJ-001/002、FR-ENTRY-001、FR-LLM-001 → AC-01/02/04/05/06/07。
- **输入**：T003 RED；T002 frontmatter API；结构版 `ReaderBundleStructureInputs`；Task 1 TopicIndex v2/backfill；固定 mapping/status/path rules。完整 claim/fixture 输入只在 T005/T006 使用。
- **依赖**：T003。
- **并行**：否 — GREEN depends on T003 and the shared artifact boundary。
- **FR**：FR-BUNDLE-001、FR-BUNDLE-002、FR-BUNDLE-003、FR-BUNDLE-005、FR-BUNDLE-006、FR-FRONT-003、FR-FRONT-004、FR-FRONT-006、FR-STATUS-001、FR-STATUS-002、FR-STATUS-003、FR-VALID-001、FR-VALID-002、FR-PROJ-001、FR-PROJ-002、FR-ENTRY-001、FR-LLM-001。
- **AC**：AC-01、AC-02、AC-04、AC-05、AC-06、AC-07。
- **动作**：实现 versioned structure input adapter、`adapt_topic_index_row`、`check_entry_bindings`/`write_entry_backfill_manifest`、显式 `artifact_root`/staging projection、Bundle tree、index/source projection、validator、degraded record 和 `not_released` report；validator `status=passed` 是 initial commit 的硬前置，成功后返回 `CommittedBundleRun`（含 run/base bundle/projection/manifest hashes）；完整 attribution 由 T006 补齐。
- **精确文件**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; `tests/fixtures/task2a_reader_bundle/topic-index.json`; `tests/fixtures/task2a_reader_bundle/source-inventory.jsonl`
- **execution_file_paths**：`["src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_reader_bundle.py","tests/fixtures/task2a_reader_bundle/topic-index.json","tests/fixtures/task2a_reader_bundle/source-inventory.jsonl"]`
- **boundary**：files: Phase 2 NEW subset; symbols/regions: input adapter、`project_reader_bundle`、`validate_reader_bundle`、tree/index/source/degraded/report regions；不得修改旧 `kb_structure`、identity、pipeline 或 CLI。
- **输出**：可重放的隔离 Bundle、结构化 `artifact_root/reports/projection-report.json`、合法 Reader 导航和 Audit degraded 对账；runner 复制/哈希/回读 evidence；包级 `digest_release_status=not_released`。
- **Knowledge**：先校验 TopicIndex v2 的公共 envelope、身份、source/evidence 和 path；将合法 product-only row（`status=published`、`knowledge_type=products`、非空 product/object_intent、`module is None`）分区到 `adapt_topic_index_row` 的 module-optional 分支，只有其余 standard rows 才调用现有 `validate_topic_index`，因为现有 validator 对 published row 要求 module 非空。product-only 分支仍执行同一公共检查和专用字段检查，并固定 rejection codes，不静默 bypass；三条人工 fixture 的 exact `(topic_id, object_intent)` mapping 必须从 `fixture-selection.json` 回读并与 TopicIndex/source fingerprint 对账；不得补 module。malformed/unsupported/uncertain row 必须输出结构化 degraded；正例和负例都要覆盖；Home 只能指向根 index；degraded 不进入 Reader index。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；沿用 T003 gate/oracle。
- **scenarios / commands / expected exit / oracle**：同 T003；预期 `0`；`ORACLE-BUNDLE-TREE`、`ORACLE-STATUS`、`ORACLE-LINKS`、`ORACLE-REPLAY`、`ORACLE-OFFLINE-RELEASE`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-INPUT-ADAPTER`、`ORACLE-ENTRY-READBACK`、`ORACLE-CLI-OFFLINE`。
- **fixtures_services**：local structural fixture + `tmp_path`；无网络/provider；synthetic manifest 只能验证拒绝分支。
- **browser_route**：N/A — no UI。
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q`
- **expected_exit**：0
- **oracle**：`ORACLE-BUNDLE-TREE`、`ORACLE-STATUS`、`ORACLE-LINKS`、`ORACLE-REPLAY`、`ORACLE-OFFLINE-RELEASE`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-INPUT-ADAPTER`、`ORACLE-ENTRY-READBACK`、`ORACLE-ENTRY-BACKFILL`、`ORACLE-CLI-OFFLINE`、`ORACLE-FINALIZE-RECOVERY`；真实 entry refs/hash/schema/version/producer/consumer/coverage 对账通过；Bundle、Audit、Report containment 闭合；valid product-only 正例不生成 module，malformed/unsupported/uncertain 负例进入 degraded；重复输入、root reuse、staging/partial-write recovery 遵守调用方单写者边界且不产生 owner lock；replay 保持归一后的 `digest_topic_id`/path/index/managed hash；CLI `--no-llm` runtime audit 的 `calls.llm=0`、`calls.embedding=0`，并由测试边界 deny-only socket guard 证明未触网。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/bundle-green.txt`; `quality/evidence/task2a-reader-bundle/entry-backfill-{red,green}.txt`; `quality/evidence/task2a-reader-bundle/projection-report.json`（由 artifact_root canonical report/backfill 复制、哈希、回读）
- **coverage limits**：不证明真实 fixture attribution、external parser、正文语义或正式 release。
- **execution_contract**：build-code 核对真实 changed files；若增加未声明路径、需要正式 pipeline/CLI 或入口 hash 不闭合，停止，不扩边界。
- **TaskKernel/evidence_refs**：待绑定当前 snapshot、GREEN receipt、projection report 和各自 SHA-256；当前 N/A — not started。
- **evidence_note**：projection report 必须同时列出 published/degraded/not_released 事实；CLI audit evidence 不能由 Bundle API monkeypatch 单独替代。
- **STOP**：任何 path/symlink/link escape、空 index、伪造 module、verified/stale_after 无证据、degraded 进导航、entry readback 缺失、CLI runtime audit 的 `calls.llm`/`calls.embedding` 非零，或 deny-only socket guard 缺失/失败。
- **recovery**：保留 T003 RED；移除当前隔离 output/report 变更，修复实现后重新跑同一 gate。initial commit 或 finalize 失败时必须保留正式 root 的原始 Bundle/projection/manifest SHA-256，并证明 staging 未发布；不得用 evidence copy 代替 canonical artifact。
- **task risk**：Bundle、Audit、Report 三面不一致会造成不可追溯的 reader state。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：实现 `ReaderBundleStructureInputs`/adapter、entry binding/backfill、Bundle 五个入口、产品/模块索引、source projection、validator、degraded audit、报告、base bundle/report/manifest hash 和原子 commit；失败会清理 staging，包状态保持 `not_released`。
- **executed_commands**：`UV_CACHE_DIR="${TMPDIR:-/private/tmp}/knowledge-digest-uv-cache-phase2-coverage1" uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q` → exit 0，24 passed；同一 gate 覆盖结构、负例、入口 producer/coverage 对账、replay 和 CLI offline boundary。
- **evidence_refs**：`[{"ref":"quality/tests/t2a-phase2-bundle-coverage1.json","sha256":"bde7f703bf80f29566273ce05ac3f345d79a3b7eb1594f54bd65a9fdda3fad06"},{"ref":"quality/evidence/implementation/5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2.json","sha256":"5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2"}]`
- **covered_ac**：AC-01、AC-02、AC-04、AC-05、AC-06、AC-07。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-0fd368873a1ba3ac7e51ecca5f1557434503f4d7-5db8ed9f-da9e-46ad-9357-729840678f05.json","sha256":"e422c14beb7391ea9c3406929e273af50b67580d26ea37c664231b484dc4b7d7","snapshot_tree":"0fd368873a1ba3ac7e51ecca5f1557434503f4d7","verdict":"pass","findings":[]}`
- **completed_at**：2026-08-09T23:15:20+08:00

#### T005 — RED：attribution/fixture/replay 失败断言

- **ID**：T005
- **Phase**：Phase 2：隔离 Bundle projection、validator 与 attribution fixture
- **Workflow stage**：`build-code`
- **goal**：固定三类人工 fixture、footnote → source → claim/locator → audit evidence 和 replay 的目标 RED。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-004/R-006/R-002/F-003 → D3/D1 → FR-ATTR-001/002、FR-FIX-001/002、FR-FRONT-003、FR-VALID-001、FR-PROJ-002 → AC-02/03/05/06。
- **输入**：T004 structure Bundle API；完整 `ReaderBundleInputs`；`KNOWLEDGEDIGEST_TASK1_RAW_CORPUS`；20 个真实样本的 source/claim facts。
- **依赖**：T004。
- **并行**：否 — fixture schema and attribution validator share one mapping.
- **FR**：FR-ATTR-001、FR-ATTR-002、FR-FIX-001、FR-FIX-002、FR-FRONT-003、FR-VALID-001、FR-PROJ-002。
- **AC**：AC-02、AC-03、AC-05、AC-06。
- **动作**：只添加真实选样所需的 RED fixtures/selection manifest/claim records 和失败断言；不声称语义质量。完整输入 schema 在本卡首次使用，synthetic claim/fixture 只能测拒绝分支。
- **精确文件**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; `tests/fixtures/task2a_reader_bundle/claim-history.jsonl`; `tests/fixtures/task2a_reader_bundle/fixture-selection.json`; `tests/fixtures/task2a_reader_bundle/product-overview.md`; `tests/fixtures/task2a_reader_bundle/module-capability.md`; `tests/fixtures/task2a_reader_bundle/procedure-rule.md`
- **execution_file_paths**：`["src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_reader_bundle.py","tests/fixtures/task2a_reader_bundle/claim-history.jsonl","tests/fixtures/task2a_reader_bundle/fixture-selection.json","tests/fixtures/task2a_reader_bundle/product-overview.md","tests/fixtures/task2a_reader_bundle/module-capability.md","tests/fixtures/task2a_reader_bundle/procedure-rule.md"]`
- **boundary**：files: Phase 2 NEW subset; symbols/regions: attribution/replay tests and fixture records; no raw corpus commit and no semantic body compilation。
- **输出**：目标 attribution/replay 非零 RED；选样事实必须包含 source URI、content fingerprint、claim mapping、sample ID 和 exact `(topic_id, object_intent) → mapping_role → digest_page_type` record。
- **Knowledge**：D3 要求真实样本人工整理；入口 backfill 只证明 source precheck，不能替代 AC-03。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；raw corpus available 后沿用 Bundle acceptance gate。
- **scenarios / commands / expected exit / oracle**：三类固定 type/mapping（exact pair 与 selection manifest 对账，不按标题猜测）、footnote 唯一回查、完整 audit Claim/Evidence、sources projection 不生成第二 source/target、重复 projection/replay；`pytest tests/acceptance/test_task2a_reader_bundle.py -q`；预期 `1`；`ORACLE-ATTRIBUTION`、`ORACLE-AUDIT-CLAIM-EVIDENCE`、`ORACLE-REPLAY`。
- **fixtures_services**：受控 raw corpus 只用于一次人工选样；测试使用 committed fixture + `tmp_path`；无网络/provider。
- **browser_route**：N/A — no UI。
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q`
- **expected_exit**：1
- **oracle**：`ORACLE-ATTRIBUTION`、`ORACLE-AUDIT-CLAIM-EVIDENCE`、`ORACLE-REPLAY`；RED 必须来自目标归因/replay assertion，raw corpus 缺失本身不是 RED 证据。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/attribution-red.txt`
- **coverage limits**：不证明 semantic answerability、reader quality 或 parser smoke。
- **execution_contract**：若 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置、片段无法回查或 claim 不唯一，保持 blocked-by-design，不生成虚构 fixture、不执行假 RED。
- **TaskKernel/evidence_refs**：待绑定 raw corpus 可审计选样、当前 snapshot、RED receipt 和 `attribution-red.txt` SHA-256；当前 N/A — blocked。
- **evidence_note**：只有真实 URI/fingerprint/claim/locator 闭合后，RED 才能证明目标行为；缺输入必须记录 STOP，而不是伪造测试失败。
- **STOP**：raw corpus unavailable、片段不能回查、claim 非唯一、需要自动编译正文或需要新增 source truth。
- **recovery**：等待受控 raw corpus；删除未合格 fixture/selection files，回到 T004，不虚构映射。
- **task risk**：把 source precheck 当成 reader attribution quality pass。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：raw corpus 约束已解除；提交三类受控 fixture、selection manifest、claim history 和 attribution/replay 失败断言。选样事实回指仓库内 `quality/evidence/task2-entry/task0-real-corpus-20260806.json`，没有把原始 corpus 放入仓库，也没有用 synthetic 数据关闭 AC-03。早期 blocked-by-design 阶段没有伪造 RED receipt。
- **red_evidence_fact**：`{"status":"unavailable","reason_code":"CANONICAL_RED_RECEIPT_NOT_CAPTURED","scope":"T005 target assertion","note":"早期 blocked-by-design 阶段未伪造 RED；当前 GREEN 证据不倒推 RED 已存在。"}`
- **executed_commands**：`UV_CACHE_DIR="${TMPDIR:-/private/tmp}/knowledge-digest-uv-cache-phase2-coverage1" uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q` → exit 0，24 passed；覆盖三类 exact mapping、footnote/source/claim/locator、fingerprint/target_path、入口 producer/coverage 对账、重复 projection 和失败闭合。
- **evidence_refs**：`[{"ref":"quality/tests/t2a-phase2-bundle-coverage1.json","sha256":"bde7f703bf80f29566273ce05ac3f345d79a3b7eb1594f54bd65a9fdda3fad06"},{"ref":"quality/evidence/implementation/5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2.json","sha256":"5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2"}]`
- **covered_ac**：AC-02、AC-03、AC-05、AC-06。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-0fd368873a1ba3ac7e51ecca5f1557434503f4d7-5db8ed9f-da9e-46ad-9357-729840678f05.json","sha256":"e422c14beb7391ea9c3406929e273af50b67580d26ea37c664231b484dc4b7d7","snapshot_tree":"0fd368873a1ba3ac7e51ecca5f1557434503f4d7","verdict":"pass","findings":[]}`
- **completed_at**：2026-08-09T23:15:20+08:00

#### T006 — GREEN：闭合 attribution、fixture 和 replay

- **ID**：T006
- **Phase**：Phase 2：隔离 Bundle projection、validator 与 attribution fixture
- **Workflow stage**：`build-code`
- **goal**：让 T005 的三类 mapping、唯一 footnote attribution、source projection、audit reverse lookup 和 replay assertions 通过。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-004/R-006/R-002/F-003 → D3/D1 → FR-ATTR-001/002、FR-FIX-001/002、FR-FRONT-003、FR-VALID-001、FR-PROJ-002 → AC-02/03/05/06。
- **输入**：T005 RED；完整 `ReaderBundleInputs`；真实 20-sample source URI/fingerprint/claim locator facts；T004 structure Bundle output。
- **依赖**：T005。
- **并行**：否 — one fixture/claim mapping chain。
- **FR**：FR-ATTR-001、FR-ATTR-002、FR-FIX-001、FR-FIX-002、FR-FRONT-003、FR-VALID-001、FR-PROJ-002。
- **AC**：AC-02、AC-03、AC-05、AC-06。
- **动作**：实现唯一 footnote attribution、selection reason 保留、source projection 和 repeat projection stability。
- **精确文件**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; `tests/fixtures/task2a_reader_bundle/claim-history.jsonl`; `tests/fixtures/task2a_reader_bundle/fixture-selection.json`; `tests/fixtures/task2a_reader_bundle/product-overview.md`; `tests/fixtures/task2a_reader_bundle/module-capability.md`; `tests/fixtures/task2a_reader_bundle/procedure-rule.md`
- **execution_file_paths**：`["src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_reader_bundle.py","tests/fixtures/task2a_reader_bundle/claim-history.jsonl","tests/fixtures/task2a_reader_bundle/fixture-selection.json","tests/fixtures/task2a_reader_bundle/product-overview.md","tests/fixtures/task2a_reader_bundle/module-capability.md","tests/fixtures/task2a_reader_bundle/procedure-rule.md"]`
- **boundary**：files: Phase 2 NEW subset; symbols/regions: attribution/fixture/replay only; no raw corpus commit and no semantic body compilation。
- **输出**：三类固定 type fixture、合法 `digest_*`/path identity、exact `(topic_id, object_intent) → mapping_role → digest_page_type` 对账、唯一 source/claim/locator chain、replay-stable evidence。
- **Knowledge**：`sources[].id` 是 attribution key；`claim_id` 保持 audit identity；`references/sources.md` 只是 reader projection。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；与 T005 使用相同 gate/oracle。
- **scenarios / commands / expected exit / oracle**：同 T005；预期 `0`；另验证 selection manifest 的 exact pair 唯一匹配 TopicIndex/source fingerprint，拒绝重复或漂移 mapping；`ORACLE-ATTRIBUTION`、`ORACLE-AUDIT-CLAIM-EVIDENCE`、`ORACLE-REPLAY`。
- **fixtures_services**：committed fixture + `tmp_path`；raw corpus 不进入仓库；无网络/provider。
- **browser_route**：N/A — no UI。
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q`
- **expected_exit**：0
- **oracle**：`ORACLE-ATTRIBUTION`、`ORACLE-AUDIT-CLAIM-EVIDENCE`、`ORACLE-REPLAY`；每个 footnote 唯一解析到 source/claim/locator/fingerprint；sources projection 不新增 target；重复输入保持 path/index/managed hash 稳定。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/attribution-green.txt`; `quality/evidence/task2a-reader-bundle/projection-report.json`
- **coverage limits**：不证明 external parser、semantic body、full corpus 或正式 release。
- **execution_contract**：只有 raw corpus 和 selected claim records 经回读后才能解除 blocked-by-design；真实 changed files 超出 Phase 2 时 STOP。
- **TaskKernel/evidence_refs**：待绑定 selection manifest、当前 snapshot、GREEN receipt、projection report 和 SHA-256；当前 N/A — blocked。
- **evidence_note**：GREEN 必须绑定每个 footnote 的完整 audit reverse lookup 和 selection reason；不能用 synthetic fixture 关闭 AC-03。
- **STOP**：需要虚构 source/claim、弱化 uniqueness/replay、或 Bundle 与 audit truth 分叉。
- **recovery**：保留 T005 RED；移除不合格 fixture，修复后重跑同一 gate，不删除原始 source/audit facts。
- **task risk**：fixture 与真实语料耦合，selection manifest 必须成为 replay 输入。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：实现唯一 footnote attribution、sources/digest_claims projection、selection reason/identity 对账、source fingerprint 与 target_path 反查、三类页面和 replay stability；变更来源不一致会 fail closed，不把 verified/semantic quality 写进预览页。
- **executed_commands**：`UV_CACHE_DIR="${TMPDIR:-/private/tmp}/knowledge-digest-uv-cache-phase2-coverage1" uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q` → exit 0，24 passed；`attribution-green.txt` 记录 3 个真实选样和 3 条 claim chain，`bundle-green.txt` 记录 24 个测试与 not_released 限制。
- **evidence_refs**：`[{"ref":"quality/tests/t2a-phase2-bundle-coverage1.json","sha256":"bde7f703bf80f29566273ce05ac3f345d79a3b7eb1594f54bd65a9fdda3fad06"},{"ref":"quality/evidence/implementation/5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2.json","sha256":"5de28421388ae6e1bfa695a0887fa6e782d55d471776dfc323ab8e72c26ccef2"}]`
- **covered_ac**：AC-02、AC-03、AC-05、AC-06。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-0fd368873a1ba3ac7e51ecca5f1557434503f4d7-5db8ed9f-da9e-46ad-9357-729840678f05.json","sha256":"e422c14beb7391ea9c3406929e273af50b67580d26ea37c664231b484dc4b7d7","snapshot_tree":"0fd368873a1ba3ac7e51ecca5f1557434503f4d7","verdict":"pass","findings":[]}`
- **completed_at**：2026-08-09T23:15:20+08:00

### Verify

- **Target**：FR-BUNDLE-001/002/003/005/006、FR-FRONT-003/004/006、FR-STATUS-001/002/003、FR-VALID-001/002、FR-ATTR-001/002、FR-FIX-001/002、FR-PROJ-001/002、FR-ENTRY-001、FR-LLM-001；AC-01/02/03/04/05/06/07。
- **Acceptance items**：

  | AC ID | Scenario / action | Oracle / expected result | Evidence ref |
  | --- | --- | --- | --- |
  | AC-01 | generate isolated Bundle tree | five identity files, root log, no nested log, no empty index | `quality/evidence/task2a-reader-bundle/bundle-green.txt` |
  | AC-02 | read entry refs and project TopicIndex | real refs/hash/version/coverage close; concept frontmatter/type/title/description/path valid | `quality/evidence/task2a-reader-bundle/bundle-green.txt` |
  | AC-03 | resolve fixture footnotes | every footnote has unique source/claim/locator/fingerprint and audit evidence | `quality/evidence/task2a-reader-bundle/attribution-green.txt` |
  | AC-04 | validate page/concept/package states | `status`/`digest_page_status`/`digest_release_status` separated; invalid verification/stale data degraded or rejected | `quality/evidence/task2a-reader-bundle/bundle-green.txt` |
  | AC-05 | validate indexes, links and degraded records | no empty/escaping links; degraded records stay out of Reader navigation and match Audit report | `quality/evidence/task2a-reader-bundle/projection-report.json` |
  | AC-06 | replay frontmatter and projection | unknown nested fields survive; topic ID/path/index/managed hash stable | `quality/evidence/task2a-reader-bundle/attribution-green.txt` |
  | AC-07 | run existing CLI `--no-llm` around projection | runtime audit has `calls.llm=0` and `calls.embedding=0`; deny-only socket guard proves no network request; package remains `not_released` | `quality/evidence/task2a-reader-bundle/bundle-green.txt` |

- **Task coverage**：T003 → AC-01/02/04/05/06/07；T004 → AC-01/02/04/05/06/07；T005 → AC-02/03/05/06 RED；T006 → AC-02/03/05/06 GREEN。
- **Cross-task seam**：T004 必须消费 T002 frontmatter 和 T003 input/tree contract；T006 必须消费 T004 Bundle output；真实 entry/backfill 与 raw corpus 缺失时对应 AC 保持 STOP。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q`
- **expected_exit**：0 after T004/T006; RED tasks expected non-zero only when their target inputs are available。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/bundle-green.txt`; `quality/evidence/task2a-reader-bundle/attribution-green.txt`; `quality/evidence/task2a-reader-bundle/projection-report.json`
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q -vv`
- **Oracle**：`ORACLE-BUNDLE-TREE`、`ORACLE-STATUS`、`ORACLE-LINKS`、`ORACLE-REPLAY`、`ORACLE-ATTRIBUTION`、`ORACLE-OFFLINE-RELEASE`、`ORACLE-ARTIFACT-CONTAINMENT`、`ORACLE-INPUT-ADAPTER`、`ORACLE-ENTRY-READBACK`、`ORACLE-CLI-OFFLINE`。

### Knowledge

Task 1 `topic-index.json` 是 v2 控制面；`identity.py` 提供稳定 source/topic identity；Task 2 entry evidence 是真实入口输入，synthetic manifest 只允许负例。

### STOP

- raw corpus 未由 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 提供、fixture 无法回查、claim 不唯一时，T005/T006 保持 blocked。
- path/symlink/allowlist/link/degraded 对账不明确，或需要修改正式 pipeline/CLI 时停止。
- 真实入口 refs/hash/version/coverage 缺失或不一致时，不关闭 AC-02、不伪造 handoff。

### Done

T003/T004 完成隔离 Bundle tree、validator、状态、entry readback、projection report 和 zero-provider 事实；T005/T006 只有在真实 fixture/attribution evidence 闭合后才完成；包级保持 `not_released`。

### Risks and rollback

- **Risk**：fixture 选择被误写成语义质量，或 product/module 归属漂移。
- **Prevention**：只记录结构归因、固定 mapping、selection reason 和 source/claim facts；不编译全量正文。
- **Rollback / recovery**：删除当前隔离 fixture/output/evidence，保留 Task 0/1 facts 和 raw source；不删除旧 Reader/Audit。

## Phase 3：外部 OKF parser smoke 与 profile 降级

### Goal

vendor 固定 commit 的官方最小 parser 读取 Bundle；smoke pass 才声明 `OKF-compatible`/`okf_version: "0.2"`，否则结构化降级到 `OKF-inspired profile`。

### Files

- **NEW**：`src/knowledge_digest/okf_smoke.py`; `tests/acceptance/test_task2a_okf_smoke.py`; `tests/vendor/okf_reference_agent/__init__.py`; `tests/vendor/okf_reference_agent/bundle/__init__.py`; `tests/vendor/okf_reference_agent/bundle/document.py`; `tests/vendor/okf_reference_agent/bundle/index.py`; `tests/vendor/okf_reference_agent/bundle/paths.py`; `tests/vendor/okf_reference_agent/LICENSE`; `tests/vendor/okf_reference_agent/NOTICE.md`; `tests/vendor/okf_reference_agent/README.md`
- **MODIFY**：`src/knowledge_digest/reader_bundle.py`（仅 profile/smoke integration region）
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/identity.py`; `src/knowledge_digest/kb_structure.py`; `tests/acceptance/test_task0_reader_package.py`; `tests/acceptance/test_publication_contract.py`; `tests/acceptance/test_task1_topic_axis.py`; `quality/evidence/task2-entry/knowledge-publication-task2-entry-backfill.v1.json`; `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json`; `quality/evidence/task2-entry/task1-receipt-reconciliation.v1.json`

### Tasks

#### T007 — RED：parser profile gate 失败断言

- **ID**：T007
- **Phase**：Phase 3：外部 OKF parser smoke 与 profile 降级
- **Workflow stage**：`build-code`
- **goal**：固定 parser pass/downgrade 的互斥 profile、`okf_version`、`ParserVendorRef`/`ParserSmokeAttempt` provenance 和 exit manifest RED 断言；为 `parser_finalize_recovery` 预留坏 provenance/base-hash mismatch 负例。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-007/R-008/F-001/F-003 → D2/D1 → FR-BUNDLE-004、FR-SMOKE-001/002 → AC-08。
- **输入**：T006 valid Bundle output；accepted profile semantics；研究中的 parser commit 只作未验证候选。
- **依赖**：T006。
- **并行**：否 — smoke consumes the final Bundle contract。
- **FR**：FR-BUNDLE-004、FR-SMOKE-001、FR-SMOKE-002。
- **AC**：AC-08。
- **动作**：只添加 importable smoke stub、`ParserVendorRef`/`ParserSmokeAttempt` manifest fixture 和 pass/downgrade/finalize-recovery RED tests；不 vendor 外部代码。
- **精确文件**：`src/knowledge_digest/okf_smoke.py`; `src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_okf_smoke.py`
- **execution_file_paths**：`["src/knowledge_digest/okf_smoke.py","src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_okf_smoke.py"]`
- **boundary**：files: Phase 3 NEW/MODIFY subset; symbols/regions: `run_parser_smoke`、profile integration 和 smoke tests；不下载、不引入 runtime。
- **输出**：目标 profile assertion 的非零 RED；网络/setup failure 不计入。
- **Knowledge**：外部 parser 必须固定 source/commit/license/vendor bytes；不可把研究候选直接当作事实。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing` 预判；同一 smoke command 执行 RED/GREEN。
- **scenarios / commands / expected exit / oracle**：pass 写 version；完整 failed/unavailable 写 reason 和 provenance 并进入 honest downgrade；source/attempt/reason/bundle provenance 缺失或结果含糊必须 blocked；acceptance fixture 只在测试边界安装 deny-only socket/provider guard，不向生产 smoke API 传入 `SmokeContext` 或计数上下文；compatibility RED 使用 `pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_compatible`，另有独立 `parser_downgrade` RED 和 `parser_finalize_recovery` RED；预期 `1`；`ORACLE-OKF-SMOKE`、`ORACLE-OKF-DOWNGRADE`、`ORACLE-FINALIZE-RECOVERY`。
- **fixtures_services**：local smoke stub + `tmp_path`；无网络/provider。
- **browser_route**：N/A — no UI。
- **verification_role**：RED
- **paired_task**：T008
- **gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_compatible`
- **downgrade_gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_downgrade`
- **expected_exit**：1
- **oracle**：`ORACLE-OKF-SMOKE`、`ORACLE-OKF-DOWNGRADE`；失败必须来自 profile/manifest 目标 assertion；无 internet/credential/import error 不能作为 RED 证明。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/smoke-red.txt`; `quality/evidence/task2a-reader-bundle/smoke-downgrade-red.txt`; `quality/evidence/task2a-reader-bundle/parser-finalize-recovery-red.txt`
- **coverage limits**：不证明最终 vendor source/commit/license，也不证明 Bundle 结构。
- **execution_contract**：build-code 只能在 Phase 3 文件范围内添加 smoke stub；禁止触网下载或选择未验证 commit。
- **TaskKernel/evidence_refs**：待绑定当前 snapshot、RED receipt 和 `smoke-red.txt` SHA-256；当前 N/A — not started。
- **evidence_note**：RED 要区分 parser target failure 与 transport/setup failure；downgrade blocked 不能写成 compatibility pass。
- **STOP**：需要下载外部代码、选择未验证 commit、触网或把 unavailable 写成 pass。
- **recovery**：恢复 smoke stub/test，保留 unavailable diagnostics；不改 Bundle contract。
- **task risk**：parser failure 与 transport failure 混淆会让 AC-08 假绿。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：先执行 parser-compatible、parser-downgrade、parser-finalize-recovery 的目标 RED；随后由 T008 实现固定 vendor、最终字节 recheck、profile/manifest 降级和 recovery。早期 RED 未在 stub snapshot 上捕获可认证 canonical receipt，因此不把 GREEN 倒推成 RED 证据。
- **red_evidence_fact**：`{"status":"unavailable","reason_code":"CANONICAL_RED_RECEIPT_NOT_CAPTURED","scope":"T007 target assertions","note":"本地早期 RED 已执行但没有在 stub snapshot 上保留 canonical receipt；不作为 GREEN 或 compatibility 证据。"}`
- **executed_commands**：`UV_CACHE_DIR=/tmp/knowledge-digest-uv-cache-phase3-final4 uv run --frozen pytest tests/acceptance/test_task2a_okf_smoke.py -q` → exit 0，7 passed；T007 早期目标 RED 的 canonical receipt unavailable，目标断言由 paired T008 GREEN 和 Phase review 覆盖。
- **evidence_refs**：`[{"ref":"quality/evidence/implementation/0c7d616cb520930e7d23cc0a4f524573fa218ecaa62cc268e8de56c41781080a.json","sha256":"0c7d616cb520930e7d23cc0a4f524573fa218ecaa62cc268e8de56c41781080a"},{"ref":"quality/tests/t2a-phase3-parser-full-final4.json","sha256":"d340d37ac7254abe990544c2847f3e17527027e3d748b0cf307466e7d1bc140a"},{"ref":"quality/reviews/results/build-code-default-82f0d122c248b2e05430fb05b01fffbd7bf8e3a3-73d081ea-d75d-4cb9-966d-91bec9384d7b.json","sha256":"908f7bc54005105bfa2d50dabcaf69dd32f5bfa94407ec19683ac5cc2509a827"}]`
- **covered_ac**：AC-08。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-82f0d122c248b2e05430fb05b01fffbd7bf8e3a3-73d081ea-d75d-4cb9-966d-91bec9384d7b.json","sha256":"908f7bc54005105bfa2d50dabcaf69dd32f5bfa94407ec19683ac5cc2509a827","snapshot_tree":"82f0d122c248b2e05430fb05b01fffbd7bf8e3a3","verdict":"pass","findings":["F-583d24bcef45","F-7146b5b53211"]}`
- **finding_dispositions**：`[{"finding_id":"F-583d24bcef45","status":"accepted_risk","reason":"attempt evidence mapping is duplicated across the two isolated modules; current tests exercise mismatch fail-closed behavior, and extracting a new shared module is deferred to a separate refactor."},{"finding_id":"F-7146b5b53211","status":"accepted_risk","reason":"network_requests is a declared invariant, not a production counter; zero-network is enforced by the acceptance boundary deny-only socket guard and the manifest labels expected behavior separately."}]`
- **completed_at**：2026-08-10T08:31:45+08:00

#### T008 — GREEN：固定 parser、零网络 smoke 和降级 manifest

- **ID**：T008
- **Phase**：Phase 3：外部 OKF parser smoke 与 profile 降级
- **Workflow stage**：`build-code`
- **goal**：让 T007 的 pass/downgrade assertions 通过，并写出可回放的 exit manifest；消费 T004 返回的 `CommittedBundleRun`，在 finalize recovery 失败时保持正式 root 字节不变。
- **design_state**：`blocked-by-design`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"decision-log","ref":"specs/task2a-knowledge-publication-reader-bundle/decision-log.md","hash":"fcdb1c191bd8c8a77b3e95f003d239b67a951237bccbdca0f71a53daca5a7734","id":"task2a-decision-log-v1"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：R-007/R-008/F-001/F-003 → D2/D1 → FR-BUNDLE-004、FR-SMOKE-001/002 → AC-08。
- **输入**：T007 RED；T006 Bundle；实际核验过的 vendor source/commit/license；零网络环境。
- **依赖**：T007。
- **并行**：否 — vendor、smoke、profile、manifest 是同一兼容事实。
- **FR**：FR-BUNDLE-004、FR-SMOKE-001、FR-SMOKE-002。
- **AC**：AC-08。
- **动作**：vendor 官方最小 reader，实现零网络 smoke，接入 profile，并在 artifact root 写 exit manifest；parser 通过且 source/attempt/reason/bundle provenance 完整时标记 `ac08_result=compatibility_passed` 并写 `okf_version`；有完整 failed/unavailable provenance 时标记 `honest_downgrade_passed`、省略 `okf_version`；事实不完整或结果含糊才 blocked。smoke 不消费生产级 `SmokeContext` 或 counter 参数；`--no-llm` 的 `calls.llm=0`、`calls.embedding=0` 由 CLI runtime audit 负责，网络零请求由测试边界 deny-only socket guard 证明，二者分别留在 acceptance evidence。`finalize_bundle_profile` 只接受 T004 的 `CommittedBundleRun`，坏 provenance、validator failure 或 base-hash mismatch 时保留旧 Bundle/report/manifest SHA-256 并清理 staging。
- **精确文件**：`src/knowledge_digest/okf_smoke.py`; `src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_okf_smoke.py`; `tests/vendor/okf_reference_agent/__init__.py`; `tests/vendor/okf_reference_agent/bundle/__init__.py`; `tests/vendor/okf_reference_agent/bundle/document.py`; `tests/vendor/okf_reference_agent/bundle/index.py`; `tests/vendor/okf_reference_agent/bundle/paths.py`; `tests/vendor/okf_reference_agent/LICENSE`; `tests/vendor/okf_reference_agent/NOTICE.md`; `tests/vendor/okf_reference_agent/README.md`
- **execution_file_paths**：`["src/knowledge_digest/okf_smoke.py","src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_okf_smoke.py","tests/vendor/okf_reference_agent/__init__.py","tests/vendor/okf_reference_agent/bundle/__init__.py","tests/vendor/okf_reference_agent/bundle/document.py","tests/vendor/okf_reference_agent/bundle/index.py","tests/vendor/okf_reference_agent/bundle/paths.py","tests/vendor/okf_reference_agent/LICENSE","tests/vendor/okf_reference_agent/NOTICE.md","tests/vendor/okf_reference_agent/README.md"]`
- **boundary**：files: Phase 3 NEW/MODIFY subset; symbols/regions: smoke/profile/manifest only；不引入完整 Knowledge Catalog/runtime。
- **输出**：parser source/commit、vendor/license hash、fixture bundle hash、unknown extension/type behavior、读取边界、profile、optional `okf_version` 和失败原因；`calls.llm=0`、`calls.embedding=0` 只引用 CLI runtime audit，网络零请求只引用测试边界 deny-only socket guard，不新增生产计数器。
- **Knowledge**：研究候选 commit `930b65fc...` 不是已核验 vendor 事实；只有实际 bytes/commit/license/notice/read smoke 全闭合才可 `ac08_result=compatibility_passed`，完整失败事实可按 accepted 口径得到 `honest_downgrade_passed`。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；与 T007 使用相同 gate/oracle。
- **scenarios / commands / expected exit / oracle**：compatibility 闭合时同 T007 预期 `0`；另跑完整 failed/unavailable downgrade 场景，预期 `0` 且 `ac08_result=honest_downgrade_passed`；source/attempt/reason/bundle provenance 缺失时预期 blocked，既不算 compatibility GREEN 也不算 downgrade GREEN；运行 `pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_finalize_recovery` 验证坏 provenance、validator failure、base-hash mismatch 的旧 root 字节不变；`ORACLE-OKF-SMOKE`、`ORACLE-OKF-DOWNGRADE`、`ORACLE-FINALIZE-RECOVERY`；AC-08 aggregate 固定为 `compatibility_passed OR honest_downgrade_passed`，两个结果都排除 blocked。
- **fixtures_services**：vendored files + `tmp_path`；acceptance fixture 可开启测试边界 deny-only socket/provider guard；无网络/provider；license evidence 本地可读。
- **browser_route**：N/A — no UI。
- **verification_role**：GREEN
- **paired_task**：T007
- **gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_compatible`
- **downgrade_gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_downgrade`
- **recovery_gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_finalize_recovery`
- **expected_exit**：0
- **oracle**：`ORACLE-OKF-SMOKE`、`ORACLE-OKF-DOWNGRADE`、`ORACLE-FINALIZE-RECOVERY`；pass/fail profile 互斥；manifest source/commit/vendor/license/notice/bundle hash/read boundary 完整；compatibility 路径写 `okf_version`，honest downgrade 路径省略它并记录原因；source/attempt/reason/bundle provenance 缺失或结果含糊即 blocked；CLI runtime audit 必须有 `calls.llm=0`、`calls.embedding=0`，测试边界必须有 deny-only socket guard 证据，不能由生产 smoke API 自报。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/smoke-green.txt`; `quality/evidence/task2a-reader-bundle/smoke-downgrade-green.txt`; `quality/evidence/task2a-reader-bundle/parser-finalize-recovery-green.txt`; `quality/evidence/task2a-reader-bundle/exit-manifest.json`（由 artifact_root canonical manifest 复制、哈希、回读）
- **coverage limits**：不证明 Task 2-B semantic body、Task 2-C reader gate、Task 3 release。
- **execution_contract**：当前环境缺 vendor/raw corpus 时保持 blocked-by-design；若 build-code 获得真实 vendor 且 smoke 明确 failed/unavailable，允许 honest downgrade GREEN，但不能用它冒充 compatibility GREEN。
- **TaskKernel/evidence_refs**：待绑定当前 snapshot、GREEN receipt、exit manifest 和 SHA-256；当前 N/A — blocked。
- **evidence_note**：exit manifest 必须能重放命名与 profile 决定；现有 CLI runtime audit 的 `calls.llm`/`calls.embedding` 缺失或非零，或测试边界 deny-only socket guard 证据缺失/失败，即失败；不能由 exit manifest 或生产 smoke API 自报网络事实。
- **STOP**：vendor/commit/license/notice/bundle/read-boundary provenance 缺失、CLI `calls.llm`/`calls.embedding` audit 缺失、deny-only socket guard 缺失、smoke 触网、parser fail 仍写 `okf_version`、或需要完整 runtime/service；单纯有完整 parser failure 不再阻塞 honest downgrade。
- **recovery**：保留 fail/unavailable evidence；移除不合格 vendor/output，回到 `OKF-inspired profile`，不改 review 结果。
- **task risk**：外部 parser 升级会造成 smoke 漂移；manifest 必须成为后续固定输入。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：vendor 固定 OKF 最小读取面（commit `930b65fc3f5619d5d0591f88c72ebae8b848d60d`、license/notice/hash/read boundary），实现零网络 smoke、最终 staged Bundle 字节 recheck、compatibility/诚实降级/blocked manifest、未知扩展/type 预期行为、以及坏 provenance、validator failure、base-hash mismatch 的原子 recovery。
- **executed_commands**：`UV_CACHE_DIR=/tmp/knowledge-digest-uv-cache-phase3-capture-final4 uv run --frozen pytest tests/acceptance/test_task2a_okf_smoke.py -q` → exit 0，7 passed；跨 Phase aggregate：`UV_CACHE_DIR=/tmp/knowledge-digest-uv-cache-task2a-aggregate-capture uv run --frozen pytest tests/acceptance/test_task2a_reader_frontmatter.py tests/acceptance/test_task2a_reader_bundle.py tests/acceptance/test_task2a_okf_smoke.py tests/acceptance/test_task0_reader_package.py tests/acceptance/test_publication_contract.py tests/acceptance/test_task1_topic_axis.py -q` → exit 0，113 passed，1 skipped。
- **evidence_refs**：`[{"ref":"quality/evidence/implementation/0c7d616cb520930e7d23cc0a4f524573fa218ecaa62cc268e8de56c41781080a.json","sha256":"0c7d616cb520930e7d23cc0a4f524573fa218ecaa62cc268e8de56c41781080a"},{"ref":"quality/tests/t2a-phase3-parser-full-final4.json","sha256":"d340d37ac7254abe990544c2847f3e17527027e3d748b0cf307466e7d1bc140a"},{"ref":"quality/tests/t2a-final-aggregate-final.json","sha256":"23a06ac09abea51b721429fa45b4ab0f95a9b140c488207a8588fc0214844567"},{"ref":"quality/reviews/results/build-code-default-82f0d122c248b2e05430fb05b01fffbd7bf8e3a3-73d081ea-d75d-4cb9-966d-91bec9384d7b.json","sha256":"908f7bc54005105bfa2d50dabcaf69dd32f5bfa94407ec19683ac5cc2509a827"}]`
- **covered_ac**：AC-08。
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-82f0d122c248b2e05430fb05b01fffbd7bf8e3a3-73d081ea-d75d-4cb9-966d-91bec9384d7b.json","sha256":"908f7bc54005105bfa2d50dabcaf69dd32f5bfa94407ec19683ac5cc2509a827","snapshot_tree":"82f0d122c248b2e05430fb05b01fffbd7bf8e3a3","verdict":"pass","findings":["F-583d24bcef45","F-7146b5b53211"]}`
- **finding_dispositions**：`[{"finding_id":"F-583d24bcef45","status":"accepted_risk","reason":"attempt evidence mapping remains duplicated across isolated smoke/finalizer boundaries; current mismatch tests are fail-closed, and a shared internal hash/provenance module is deferred."},{"finding_id":"F-7146b5b53211","status":"accepted_risk","reason":"network_requests is intentionally a declared invariant; actual zero-network proof remains in the acceptance deny-only socket boundary, not production counters."}]`
- **integration_review_fact**：`{"ref":"quality/reviews/results/build-code-default-25c3816ee2b25f1fd24d9e78a49ac2490185d8ec-47e1e7fb-1878-4736-8a39-0734e4b7e55c.json","sha256":"9d9b3ce6cb941eb3a7e24e6b0c687a372e5586b035cc722a89128897a233e7ce","snapshot_tree":"25c3816ee2b25f1fd24d9e78a49ac2490185d8ec","verdict":"pass","review_scope":"integration","coverage":"single_external"}`
- **integration_finding_dispositions**：`[{"finding_id":"F-0f56fee32883","status":"fixed","reason":"downgrade test now creates and populates its own input root; affected tests reran with 31 passed."},{"finding_id":"F-643bbca92d06","status":"accepted_risk","reason":"positive verified/stale_after trust-signal production semantics are not emitted by this preview/not_released Task 2-A projection; retain the explicit evidence limit for verify-code and later reader-gate scope, without claiming those positive semantics pass here."},{"finding_id":"F-96cbe2bb062d","status":"accepted_risk","reason":"integration packet implementation-anchor selection is a WorkflowHub material-shaping limitation; verify-code must inspect the changed production modules directly."}]`
- **completed_at**：2026-08-10T08:31:45+08:00

### Verify

- **Target**：FR-BUNDLE-004、FR-SMOKE-001/002、AC-08。
- **Acceptance items**：

  | AC ID | Scenario / action | Oracle / expected result | Evidence ref |
  | --- | --- | --- | --- |
  | AC-08 | fixed vendor parser reads Bundle with zero network | all source/commit/license/notice/vendor/bundle hash facts close; `ac08_result=compatibility_passed`; root `okf_version: "0.2"` only then | `quality/evidence/task2a-reader-bundle/exit-manifest.json` |
  | AC-08 | parser unavailable/fails with complete provenance | profile is `OKF-inspired profile`; root omits `okf_version`; reason recorded; `ac08_result=honest_downgrade_passed` | `quality/evidence/task2a-reader-bundle/exit-manifest.json` |

- **Task coverage**：T007 → AC-08 RED；T008 → compatibility GREEN or accepted honest-downgrade GREEN；缺 provenance 才 blocked。
- **Cross-task seam**：T008 只能消费 T006 Bundle 和 T007 same oracle；parser result 必须驱动 profile/name/manifest，不能由文档或测试夹具硬编码成功。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_compatible`
- **downgrade_gate_cmd**：`pytest tests/acceptance/test_task2a_okf_smoke.py -q -k parser_downgrade`
- **expected_exit**：0 for compatibility GREEN 或完整 honest-downgrade GREEN；T007 RED expected non-zero；incomplete blocked 不计为通过。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/smoke-green.txt`; `quality/evidence/task2a-reader-bundle/smoke-downgrade-green.txt`; `quality/evidence/task2a-reader-bundle/exit-manifest.json`
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_okf_smoke.py -q -vv`
- **Oracle**：`ORACLE-OKF-SMOKE`、`ORACLE-OKF-DOWNGRADE`。

### Knowledge

研究已核实 `document.py/index.py/paths.py` 最小读取面和 Apache-2.0；最终 parser commit 仍需 build-code 实际核验，研究候选不可直接升级为 vendor 事实。

### STOP

- vendor 文件、commit、license/notice、bundle hash、parser read-boundary、CLI `calls.llm`/`calls.embedding` audit 或 deny-only socket guard 任一缺失，T008 保持 blocked。
- parser fail/unavailable 且事实完整时不得写 `okf_version`、不得宣称 OKF-compatible，但可按 accepted 口径完成 honest downgrade；事实不完整时保持 blocked。
- 需要完整 Knowledge Catalog/runtime、网络下载或未声明服务时停止。

### Done

T007 有目标性 RED；T008 只有 compatibility evidence 全闭合或 accepted 的 honest downgrade evidence 全闭合时才完成 AC-08；事实不完整才保留 blocked evidence。

### Risks and rollback

- **Risk**：外部 parser 版本漂移导致 smoke 结果变化。
- **Prevention**：固定 commit、vendor license/notice、零网络测试和 exit manifest hash。
- **Rollback / recovery**：保留 fail/unavailable evidence，移除当前 vendor/output，回到 `OKF-inspired profile`；不宣称兼容、不删除旧 Reader。

## Phase 4：正向机器信任信号投影与失效校验

> 复制自当前 plan Phase 4。只修改已有 Bundle projection/validator 和同一 acceptance 文件；不扩展到 Task 2-C 人工 reader gate。

### Goal

在不引入 Task 2-C 人工读者门的前提下，让已有三类完整 fixture concept 页真实产生并可回查的 `generated`、`digest_machine_pass`、`source_hash_match`/`locator_resolved` 信号；无 freshness 证据时不生成 `stale_after`，所有 Bundle 继续 `not_released`。

### Files

- **NEW**：N/A — 复用现有 Bundle/frontmatter/acceptance 边界。
- **MODIFY**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`
- **DO NOT TOUCH**：`src/knowledge_digest/reader_frontmatter.py`; `src/knowledge_digest/okf_smoke.py`; `src/knowledge_digest/pipeline.py`; `src/knowledge_digest/cli.py`; `src/knowledge_digest/navigation.py`; `src/knowledge_digest/page_layout.py`; `src/knowledge_digest/provenance.py`; `src/knowledge_digest/identity.py`; `tests/acceptance/test_task2a_reader_frontmatter.py`; `tests/acceptance/test_task2a_okf_smoke.py`; `quality/evidence/task2-entry/`

### Tasks

#### T009 — RED：正向机器信号与失效边界失败断言

- **ID**：T009
- **Phase**：Phase 4：正向机器信任信号投影与失效校验
- **Workflow stage**：`build-code`
- **goal**：把 AC-04 的正向 machine signal、audit evidence、白名单 actor 和 mutation invalidation 变成可执行失败断言。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：`R-005→D1`、`D-004` → `FR-STATUS-001/002/003`、`AC-04`；`F-003` → status/hash lifecycle；不得把正向信号扩大为 Task 2-C reader gate。
- **输入**：当前 `_full_inputs` 三类 fixture、结构-only `_inputs`、现有 `managed_content_hash`/Bundle validator。
- **依赖**：T008
- **并行**：否 — 与 T010 共享同一测试文件、artifact root 和 oracle。
- **FR**：FR-STATUS-001、FR-STATUS-002、FR-STATUS-003
- **AC**：AC-04
- **动作**：添加正向、负向和变更失效断言：完整 fixture 应出现 generated/machine pass/两个白名单事件和 audit ref；结构-only 不应伪造 verified；无 freshness 不应出现 stale_after；篡改正文、fingerprint、locator、target path 或 page type 后 validator 必须拒绝旧信号；human/agent_assisted/unsupported event 必须拒绝。
- **精确文件**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`
- **execution_file_paths**：`["src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_reader_bundle.py"]`
- **boundary**：files: `src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; symbols/regions: trust frontmatter projection, trust audit writer, validator trust checks, new acceptance cases only。
- **输出**：目标性非零 RED；失败必须是信号断言而不是环境/fixture/setup 错误。
- **Knowledge**：现有 managed hash 已排除 generated/verified/machine pass；source inventory/fixture selection/claim history 已有 fingerprint、locator、target path；默认没有 freshness metadata。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；changed files 跨 `src/` 与 `tests/`，使用 tmp_path，无服务无网络。
- **scenarios / commands / expected exit / oracle**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers'`；expected non-zero；`ORACLE-TRUST-SIGNAL-POSITIVE`、`ORACLE-TRUST-SIGNAL-NEGATIVE`、`ORACLE-TRUST-SIGNAL-INVALIDATION`；正向预期在 GREEN 前失败。
- **fixtures_services**：`_full_inputs`、`_inputs`、`tmp_path` artifact root；不启动服务、不触碰 provider。
- **browser_route**：N/A — no UI。
- **verification_role**：RED
- **paired_task**：T010
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers'`
- **expected_exit**：1
- **oracle**：三个 ORACLE 必须由目标 assertion 失败触发；不能用 import/fixture/hash setup failure 充当 RED。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/trust-signal-red.txt`
- **coverage limits**：只覆盖新增信号 contract 的目标 RED；不证明语义 entailment、人工 reader gate、全量 release 或外部 raw bytes。
- **execution_contract**：build-code 先核对 changed files 只落在 Phase 4；若需要改变 frontmatter hash contract、输入 schema、CLI 或新增事实源，停止并回到 scope review。
- **TaskKernel/evidence_refs**：执行后绑定当前 snapshot、T009 RED receipt、stdout/stderr evidence 及 SHA-256；当前 N/A — not started。
- **evidence_note**：证据必须显示缺失信号/错误信号或 mutation 未失效的目标断言；不把旧结构 GREEN 倒推为 RED。
- **STOP**：RED 非目标性失败、需要新增未声明接口/事实源、或断言只能靠伪造 human/semantic evidence 通过时停止。
- **recovery**：撤回 T009 新增断言或修正 fixture setup；不改生产实现以迎合错误 RED。
- **task risk**：把 fingerprint/locator 一致性误报为语义验证。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增完整 fixture 的正向信任信号、结构-only 状态分离、audit 回读和 mutation/非法 actor 失效断言。
- **executed_commands**：直接 `pytest ...` exit `127`（当前环境无独立 pytest 命令）；使用冻结环境同一 gate `uv run --frozen pytest ... -k 'trust_signal or status_layers'` exit `1`，`3 failed, 25 deselected`，失败均为目标信号断言。
- **evidence_refs**：`quality/evidence/task2a-reader-bundle/trust-signal-red.txt`，SHA-256 `ad4cee223e5ba1e0f11c6798261cfeed2484ca7578a61150cf68aa2fbc2aab4b`。
- **covered_ac**：AC-04 RED；`ORACLE-TRUST-SIGNAL-POSITIVE`、`ORACLE-TRUST-SIGNAL-NEGATIVE`、`ORACLE-TRUST-SIGNAL-INVALIDATION`。
- **review_fact**：由 T010 paired GREEN 复核；正式 WorkflowHub lens dispatch 当前因 `bundle sha256 mismatch: scripts/review-materials.mjs` unavailable，未写成 pass。
- **completed_at**：`2026-08-10`

#### T010 — GREEN：投影正向机器信号并在 mutation 后 fail-closed

- **ID**：T010
- **Phase**：Phase 4：正向机器信任信号投影与失效校验
- **Workflow stage**：`build-code`
- **goal**：让 T009 的全部信号、证据、状态分离和 invalidation 断言通过。
- **design_state**：`ready`
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task2a-knowledge-publication-reader-bundle/spec.md","hash":"62f293cb9e2de367154377fb572d9a03681f1fcc839436e3c579bb70b0a3d08e","id":"task2a-spec-v1-draft"},{"artifact_kind":"plan","ref":"specs/task2a-knowledge-publication-reader-bundle/plan.md","hash":"fe5d54ab12fcaf6b0bfee38f4f440074ddfde0670654ace1bd23333e28de8425","id":"task2a-plan-draft"}]`
- **source_refs / decision_refs**：`R-005→D1`、`D-004` → `FR-STATUS-001/002/003`、`AC-04`；`F-003` → status/hash lifecycle。
- **输入**：T009 RED；现有 `_concept_frontmatter`、`_selected_frontmatter`、`project_reader_bundle`、`validate_reader_bundle` 和 `managed_content_hash`。
- **依赖**：T009
- **并行**：否 — RED/GREEN 必须串行，且共享 artifact trust audit。
- **FR**：FR-STATUS-001、FR-STATUS-002、FR-STATUS-003
- **AC**：AC-04
- **动作**：在同一 Bundle projection 写入 generated 和 machine pass；对完整 fixture 从 source/selection/claim 的 fingerprint 与 locator/target path 生成 `source_hash_match`、`locator_resolved` 事件；写入 `audit/trust-signals/*.json`；validator 回读白名单、actor、detector、fingerprint、content hash 和 evidence_ref，并在受管内容/归因/page type 变化后拒绝旧 verified；只投影明确有效 freshness metadata，不猜 TTL。
- **精确文件**：`src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`
- **execution_file_paths**：`["src/knowledge_digest/reader_bundle.py","tests/acceptance/test_task2a_reader_bundle.py"]`
- **boundary**：files: `src/knowledge_digest/reader_bundle.py`; `tests/acceptance/test_task2a_reader_bundle.py`; symbols/regions: T009 对应 trust projection/validation region。
- **输出**：三类完整 fixture page 具备可回查正向机器信号；结构-only page 保持 unverified；无 freshness 时省略 stale_after；包级 status 仍 `not_released`。
- **Knowledge**：机器 `verified` 只允许四类白名单，本 Phase 只实现其中 source_hash_match/locator_resolved；generated/verified/machine pass 不进入 managed content hash；旧 evidence 保持 audit-only。
- **test_strategy_owner**：`build-plan/high-intelligence-model`
- **test tier / test method**：`fullstack` / `fullstack-slice-testing`；同 T009 gate/oracle，changed files 跨 `src/` 与 `tests/`，使用 tmp_path，无服务无网络。
- **scenarios / commands / expected exit / oracle**：运行同一 `pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers'`；expected exit `0`；正向、负向、mutation 三个 ORACLE 全部通过。
- **fixtures_services**：与 T009 相同；audit evidence 在临时 artifact root 内生成并由测试回读。
- **browser_route**：N/A — no UI。
- **verification_role**：GREEN
- **paired_task**：T009
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers'`
- **expected_exit**：0
- **oracle**：`ORACLE-TRUST-SIGNAL-POSITIVE`：generated/machine pass/两个事件/audit ref；`ORACLE-TRUST-SIGNAL-NEGATIVE`：结构-only 无 verified、无 freshness 无 stale_after、非法 actor/event fail；`ORACLE-TRUST-SIGNAL-INVALIDATION`：mutation 后旧事件 fail-closed。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/trust-signal-green.txt`; `quality/evidence/task2a-reader-bundle/trust-signals/`
- **coverage limits**：不证明 `critical_token_recheck`、`sampled_entailment`、human reader gate、正文语义、全量 release 或外部 raw bytes 重新读取。
- **execution_contract**：build-code 核对真实 changed files；不得改 `reader_frontmatter.py` 的 hash exclusion、正式 pipeline/CLI、provider 或 release status；生产 event 必须由同一 audit/source/claim inputs 投影，不复制第二套 truth。
- **TaskKernel/evidence_refs**：执行后绑定当前 snapshot、T009/T010 receipts、artifact trust audit canonical hashes、Phase review ref 和 GREEN stdout evidence；当前 N/A — not started。
- **evidence_note**：以 artifact root audit 记录为唯一 event evidence，测试只做复制/哈希/回读；正向 signal 不等于 semantic quality 或 human acceptance。
- **STOP**：任一正向事件缺 fingerprint/detector/actor/evidence、mutation 后仍 accepted、出现不支持的 human/agent event、或包状态改变时停止。
- **recovery**：清理当前 Phase trust projection/staging，保留旧 Bundle/结构 evidence；修复实现和测试后重跑 T009/T010。
- **task risk**：把 audit event 当成第二事实源或把机器回查扩大为语义通过。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：在 `reader_bundle.py` 投影 generated/machine pass、白名单 `source_hash_match`/`locator_resolved`、TopicIndex source/evidence binding、显式 freshness 投影和 `audit/trust-signals/*.json`；validator 校验 actor/detector/canonical fingerprint/content hash/audit equality，并在内容、来源、locator、target path、page type 或事件 mutation 后 fail-closed。
- **executed_commands**：`uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers'` exit `0`，`7 passed, 27 deselected`；完整 Bundle 文件测试 exit `0`，`34 passed`。
- **evidence_refs**：`quality/evidence/task2a-reader-bundle/trust-signal-green.txt`，SHA-256 `bf389cb609bc41beffdb45d2fdbb622f122f9446861d64fa90fe87bd01fa88cd`。
- **covered_ac**：AC-04 GREEN；正向、结构-only/无 freshness、显式 freshness、非法 event/actor、内容/来源/locator/target/page-type mutation 六类边界。
- **review_fact**：当前真实 changed-file 路由为 `fullstack` / `fullstack-slice-testing`；正式 WorkflowHub lens dispatch 因 bundle hash mismatch unavailable，保留该事实，不冒充 provider review。
- **completed_at**：`2026-08-10`

### Verify

- **Target**：FR-STATUS-001/002/003、AC-04。
- **Acceptance items**：

  | AC ID | Scenario / action | Oracle / expected result | Evidence ref |
  | --- | --- | --- | --- |
  | AC-04 | full fixture projection | generated、digest_machine_pass、两个白名单 verified event 和 audit refs 可回读；无 human/semantic event | `quality/evidence/task2a-reader-bundle/trust-signal-green.txt` |
  | AC-04 | structure-only and no freshness | 无 verified、无 stale_after；status/page/release 三层仍分开 | `quality/evidence/task2a-reader-bundle/trust-signal-green.txt` |
  | AC-04 | mutate body/provenance/page type | validator fail-closed，旧 verified 不再成为当前信号 | `quality/evidence/task2a-reader-bundle/trust-signal-green.txt` |

- **Task coverage**：T009 → AC-04 RED；T010 → AC-04 GREEN。
- **Cross-task seam**：T010 必须消费 T009 同一 gate/oracle；audit evidence 和 current content hash 由同一 artifact root 产生和回读。
- **gate_cmd**：`pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers'`
- **expected_exit**：0 after T010; T009 RED expected non-zero。
- **evidence_path**：`quality/evidence/task2a-reader-bundle/trust-signal-red.txt`; `quality/evidence/task2a-reader-bundle/trust-signal-green.txt`; artifact root `audit/trust-signals/*.json`。
- **display_cmd**：`uv run --frozen pytest tests/acceptance/test_task2a_reader_bundle.py -q -k 'trust_signal or status_layers' -vv`
- **Oracle**：`ORACLE-TRUST-SIGNAL-POSITIVE`、`ORACLE-TRUST-SIGNAL-NEGATIVE`、`ORACLE-TRUST-SIGNAL-INVALIDATION`。

### Knowledge

`managed_content_hash` 已排除易变 signal 字段；现有 source/selection/claim inputs 可提供 fingerprint/locator/target path 闭合；没有 freshness input，默认省略 `stale_after`。

### STOP

- RED 无法证明目标断言失败，或 GREEN 需要新增事实源、provider、人工记录、hash contract、CLI 或 release 行为。
- mutation 后旧 verified 仍被接受、非法 actor/event 被接受、或 positive signal 没有 audit evidence。

### Done

T009/T010 共享同一 gate/oracle；GREEN 只在正向信号、负向边界、mutation invalidation 和 not_released 全部通过后填写。

### Risks and rollback

- **Risk**：机器 source/locator check 被读者误当成语义质量。
- **Prevention**：事件名、detector 和 evidence 明确限定为 source/locator；Task 2-C 语义/人工门保留 deferred。
- **Rollback / recovery**：撤回 Phase 4 trust projection 和新增测试，保留 Phase 1–3 Bundle/parser 输出与历史 audit。

## 3. Dependency Graph

```text
T001 (RED) → T002 (GREEN) → T003 (RED) → T004 (GREEN)
T004 → T005 (RED) → T006 (GREEN) → T007 (RED) → T008 (GREEN)
T008 → T009 (RED) → T010 (GREEN)
```

- 每个依赖都指向已存在的较早 Task；DAG 无环。
- 不标记 `[P]`：每个后续行为消费前一阶段 schema/output，且共享文件边界。
- T005/T006/T008 的 `blocked-by-design` 是真实输入 STOP，不是用 pending 伪装完成；T009/T010 是本次当前可执行信号 Phase。

## 4. Requirement and Verification Traceability

| FR | Task IDs | AC IDs | Phase | Gate / evidence |
| --- | --- | --- | --- | --- |
| FR-BUNDLE-001 | T003,T004 | AC-01 | Phase 2 | Bundle tree / `bundle-green.txt` |
| FR-BUNDLE-002 | T003,T004 | AC-01,AC-06 | Phase 2 | allowlist identity + round-trip / `bundle-green.txt` |
| FR-BUNDLE-003 | T003,T004 | AC-01,AC-05 | Phase 2 | canonical index/source projection / `projection-report.json` |
| FR-BUNDLE-004 | T007,T008 | AC-08 | Phase 3 | smoke/profile / `exit-manifest.json` |
| FR-BUNDLE-005 | T003,T004 | AC-02,AC-05 | Phase 2 | product/module/degraded oracle / `bundle-green.txt` |
| FR-BUNDLE-006 | T003,T004 | AC-01,AC-05 | Phase 2 | index/link oracle / `bundle-green.txt` |
| FR-FRONT-001 | T001,T002 | AC-06 | Phase 1 | round-trip / `frontmatter-green.txt` |
| FR-FRONT-002 | T001,T002 | AC-02,AC-06 | Phase 1 | PyYAML lock + round-trip / `frontmatter-green.txt` |
| FR-FRONT-003 | T003,T004,T005,T006 | AC-02 | Phase 2 | topic mapping + three fixture mapping / `bundle-green.txt` |
| FR-FRONT-004 | T003,T004 | AC-02,AC-04 | Phase 2 | status placement / `bundle-green.txt` |
| FR-FRONT-005 | T001,T002 | AC-06 | Phase 1 | managed hash / `frontmatter-green.txt` |
| FR-FRONT-006 | T003,T004 | AC-02 | Phase 2 | title/description fallback / `bundle-green.txt` |
| FR-STATUS-001 | T003,T004,T009,T010 | AC-04 | Phase 2/4 | status separation + machine pass / `bundle-green.txt`, `trust-signal-green.txt` |
| FR-STATUS-002 | T009,T010 | AC-04 | Phase 4 | verified whitelist/actor/evidence/invalidation / `trust-signal-green.txt` |
| FR-STATUS-003 | T009,T010 | AC-04 | Phase 4 | explicit freshness projection/omission / `trust-signal-green.txt` |
| FR-ATTR-001 | T005,T006 | AC-03 | Phase 2 | attribution / `attribution-green.txt` |
| FR-ATTR-002 | T005,T006 | AC-03,AC-05 | Phase 2 | source projection / `attribution-green.txt` |
| FR-VALID-001 | T003,T004,T005,T006,T009,T010 | AC-02,AC-04,AC-06 | Phase 2/4 | validator / `bundle-green.txt`, `trust-signal-green.txt` |
| FR-VALID-002 | T003,T004 | AC-05 | Phase 2 | allowlist/link/degraded / `projection-report.json` |
| FR-SMOKE-001 | T007,T008 | AC-08 | Phase 3 | parser smoke / `exit-manifest.json` |
| FR-SMOKE-002 | T007,T008 | AC-08 | Phase 3 | profile downgrade / `exit-manifest.json` |
| FR-FIX-001 | T005,T006 | AC-03 | Phase 2 | selection manifest / `fixture-selection.json` |
| FR-FIX-002 | T005,T006 | AC-03 | Phase 2 | footnote/claim locator / `attribution-green.txt` |
| FR-PROJ-001 | T003,T004 | AC-02,AC-07 | Phase 2 | projection report / `projection-report.json` |
| FR-PROJ-002 | T001,T002,T003,T004,T005,T006 | AC-06,AC-07 | Phase 1/2 | round-trip + replay + zero-provider evidence |
| FR-ENTRY-001 | T003,T004 | AC-02 | Phase 2 | entry backfill/readback / `bundle-green.txt` |
| FR-LLM-001 | T003,T004 | AC-07 | Phase 2 | zero-provider/not_released / `bundle-green.txt` |

## 5. Final Boundary Check

- [x] 每个 Phase 完整包含 Goal、Files、Tasks、Verify、Knowledge、STOP、Done、Risks and rollback；Phase name 和 Files 与 plan 一致。
- [x] 每个 Phase 的 Task card 都物理位于自己的 `### Tasks` 区；没有第二份 task card 或第二个 completion authority。
- [x] 每条 Phase acceptance 都绑定 AC、场景、oracle 和 task-relative evidence；T005/T006/T008 的真实输入 STOP 已保留。
- [x] 每个行为变化都有 RED → GREEN 配对；同一对使用相同 gate/oracle。
- [x] DAG 与 FR → Task → AC → gate/evidence 双向闭合；27 个 FR 全部有映射，AC-01–AC-08 全部有覆盖。
- [x] 所有 `execution_file_paths` 是所属 Phase NEW/MODIFY 的精确子集；无通配符。
- [x] 完成区只保留 pending/blocked-by-design 的未认证状态；不含伪造 receipt、hash、review 或时间。
- [x] 不包含 host identity、固定 artifact root、无关项目规则或未声明文件。

## Appendix A. Legacy import

当前 accepted spec/plan 没有需要导入的 `## Stage N` 或 `(stage:N, depends:...)` 依赖语法；本文件只发布当前 Phase/T-ID/DAG 一套依赖真相。
