## Plan engineering review fact

- **scope**：Task 2-A build-plan；只检查接口边界、失败/回滚、依赖锁、证据路径和旧 pipeline 保护。
- **method**：按 `plan-eng-review` checklist 做静态对账；结果写入 `plan.md` §9、§12、§13、§17 和 `tasks.md` 的 per-task gate。
- **status**：`static_check_recorded`；本文件不是 provider verdict，也不替代正式 `wh-review`。
- **finding disposition**：旧 Reader/CLI 不触碰、PyYAML pin、RED/GREEN、STOP、evidence 和 fullstack route 已在计划中；正式质量事实只认 Runner 生成的 canonical result。
- **receipt limitation**：当前包不复制 broker/provider 原始日志；缺少独立 dispatcher receipt 时不把它伪装成 pass。

## Invocation step-5 — current-snapshot engineering review

- **reviewed material**：accepted `spec.md`、完整 `plan.md`、`tasks.md`、当前 source anchors、task-store `index.json`/`facts.jsonl`/`quality/verify.json`。
- **snapshot facts**：当前 worktree 没有 Task 2-A implementation/tests/vendor；`KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置；task-store `reviews=[]`、`facts=[]`、verify `status=unknown`。本节只记录工程镜头，不是 provider verdict、stage result、用户确认或 build-code 放行。
- **status**：`findings_recorded`。

### Findings

| finding_id | anchored fact | affected IDs | engineering consequence | smallest corrective action to wh-review |
| --- | --- | --- | --- | --- |
| ENG-001 | `tasks.md` 仍把 plan 绑定为旧 hash `18f37903...`，而当前 `plan.md` hash 是 `5be8de09...`；`tasks.md` 还写“runner-authenticated review receipt is recorded”，但 `plan.md` 与 task-store 都记录当前 review 缺失/unknown。 | T001–T008；progression | 下游可能消费过期 plan，且材料把不存在的 review 暗示为已存在。 | plan 定稿后重算并回读 `tasks.md` header 与 T001–T008 的 plan hash；删除/改正 receipt 断言；匹配前 STOP build-code。 |
| ENG-002 | `project_reader_bundle(..., output_dir)` 声明只写 output root，但设计又要求同次运行写 `quality/evidence/.../projection-report.json` 和外置 Audit/Archive degraded pages；`validate_reader_bundle` 没有 audit/report root 参数，§9 同时把 report 归为 NEW 与 generated evidence。 | FR-PROJ-001/002、FR-VALID-001/002；AC-01/02/05/07；T003/T004/T008 | 写入范围、回滚范围和 validator 的事实源不闭合；实现可能越过 output root 或只校验 Reader 而漏掉 degraded 对账。 | 冻结单一 `artifact_root`（含 `bundle/`、`audit/`、reports）或显式 `audit_dir/report_path` 合同，并补路径 containment、partial-write recovery 和 consumer tests。 |
| ENG-003 | API 只写出 `ReaderBundleInputs`、`BundleReport`、`BundleValidationReport`、`ParserSmokeResult` 名称，没有字段/版本/必填项 schema，也没有把当前 TopicIndex v2 字段映射到新输入的精确 adapter；现有 `validate_topic_index` 与 `resolve_topic_identity` 的输入合同分别要求 v2 axis 字段和 `category_id/topic_dir`。 | FR-FRONT-003、FR-ATTR-001/002、FR-PROJ-001/002、FR-SMOKE-001；AC-02/03/06/08；T003–T008 | 结构测试可能只验证文件存在，不能证明实现消费了当前身份、claim、entry 和 parser 合同；类型/字段漂移会被隐藏。 | 增加 versioned dataclass/JSON schema、字段表和 TopicIndex→Bundle adapter；为每个新接口指定唯一 consumer、拒绝未知/缺失字段规则和 fixture oracle。 |
| ENG-004 | spec AC-07 要求真实 `--no-llm`/Jaccard 运行审计报告证明零网络；plan 却把它改成 Bundle API socket/provider guard 的“等价门禁”，并明确不调用 `cli.build_parser`。现有 CLI 已有 `--no-llm`。 | FR-LLM-001；AC-07；T003/T004 | API guard 只能证明测试调用路径未外呼，不能证明用户实际 `digest --no-llm` 路径零调用；AC-07 可能被过弱证据满足。 | 在不改 CLI 的前提下增加现有 `digest ... --no-llm` 的隔离命令/`cli.main` smoke 和 network guard；若坚持 API-only，先做 accepted spec/AC revision。 |
| ENG-005 | AC-02 要求当前 Task 0/Task 1 exit manifest 的路径/hash/version/coverage 闭合；T004 的 fixture contract 只在 `tmp_path` 构造最小 backfill/manifest，且任务没有独立的真实入口重跑命令与 evidence path。 | FR-ENTRY-001；AC-02；T003/T004 | synthetic input 通过不能证明当前入口控制面真实可用；真实入口债可能被结构测试掩盖。 | 分离 synthetic parser test 与 real entry verification；补一个只读的当前 backfill readback/校验命令、exit/evidence ref，缺失则明确 STOP，不计入 AC-02。 |
| ENG-006 | T008 标成 `blocked-by-design`，要求 fixed parser commit/license；同时仍固定 GREEN exit `0` 并把 AC-08 列为完成目标，且“downgrade path may be accepted”与“OKF-compatible remains STOP”并存。 | FR-SMOKE-001/002；AC-08；T007/T008 | parser 不可固定时，降级事实可能被误报为 T008/AC-08 GREEN，或反过来阻塞合法的降级记录；profile、completion 和 release 语义不一致。 | 把 downgrade-only 记录定义为未完成 AC-08 的 blocked evidence；只有 vendor bytes/commit/license/read smoke 全闭合才允许 T008 GREEN；否则 STOP。 |
| ENG-007 | 当前环境 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置，且 worktree 尚无 Task 2-A fixture/tests/vendor。任务自身把 T005/T006 标为缺 raw corpus 时 STOP。 | FR-FIX-001/002、FR-ATTR-001/002；AC-03；T005/T006 | 真实 fixture、claim locator、URI/fingerprint 回查当前不可执行；不能生成 RED 或 GREEN 伪证据。 | 提供受控本地 raw corpus 路径并记录选样/指纹，或把 T005/T006 保持 blocked；禁止虚构 fixture 与 claim 证据。 |

### Review disposition

- 本次没有修改 `spec.md`、`plan.md`、`tasks.md`、代码、provider、Git 或 task status。
- 上述 finding 仅供 `wh-review` 消费；本事实文件也不授予 build-code、verify-code、发布或完成资格。

## Invocation retry-0cffa318f69d298b63b2e91473893fd960251d81046f3ce46523d777 — current snapshot engineering review

- **reviewed material**：accepted `decision-log.md`、`spec.md`、当前完整 `plan.md`/`tasks.md`、当前 source anchors、Task 0/1 entry artifacts 和 task-store quality facts。
- **snapshot facts**：`plan.md` 当前 SHA-256 为 `99e122a525d9e4e3d654b00265706c9c81c3d4bbb6d02a4047e0cc3600a7d0f0`；`tasks.md` 与 T001–T008 仍绑定 `3644f67fa5dc3a08e65119ab3e8de1950fc14bd13ab80121d5f8bbc634399061`。当前 task store `reviews=[]`、`facts=[]`、`quality/verify.json.status=unknown`；`KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置；Task 2-A 实现、测试和 vendor 文件不存在。
- **status**：`findings_recorded`；本节是 advisory engineering lens，不是 provider verdict、stage result、用户确认或 build-code 放行。

### Current findings

| finding_id | anchored fact | affected IDs | engineering consequence | smallest corrective action to wh-review |
| --- | --- | --- | --- | --- |
| ENG-CURRENT-001 | `tasks.md:5-6` 及 T001–T008 的 `versioned_refs` 仍绑定旧 plan hash；当前 `plan.md` hash 已为 `99e122...`。 | T001–T008；handoff | 下游可能按过期计划实现，review packet 也无法证明消费当前计划。 | 重算并回读 tasks header、每张卡和最终 evidence 的 plan binding；旧 hash finding 改为 fixed 后再审。 |
| ENG-CURRENT-002 | `ReaderBundleInputs` 在 `plan.md:220-226` 强制要求 `claim_records_ref`、`fixture_selection_ref`，但 T003/T004 的输入和文件边界只提供 TopicIndex/source inventory；这两份输入到 T005 才出现。 | FR-ATTR-001/002、FR-FIX-001/002、AC-02/03/05/06；T003–T006 | T004 GREEN 无法构造完整 required schema；若塞入最小 synthetic records，会把结构 GREEN 与真实 attribution 混在一起。 | 拆出结构 projection 输入 schema，或把 claim/fixture 输入提前纳入 T003/T004；synthetic 只测拒绝分支，正例仍需真实证据。 |
| ENG-CURRENT-003 | 当前 Task 1 published row 的字段是 `topic_key`、`topic_id=v2/...`、`digest_topic_id=null`；`validate_topic_index` 还要求 published `module` 非空；`resolve_topic_identity` 要求 `topic-` ID 和旧 `category_id/topic_dir`。计划却要求 `topic_key_v2`、优先 `digest_topic_id`，并承诺 product-only/no-module 路径。 | FR-BUNDLE-005、FR-FRONT-004、FR-PROJ-002；AC-02/05/06；T003/T004 | adapter 既可能无法消费真实 v2 身份，也无法让“有 product、无 module”的正例通过当前 validator；实现会被迫改旧 schema、伪造 ID 或生成第二套身份。 | 冻结 `topic_id → digest_topic_id` 的明确归一规则和 Bundle 专用 path adapter；为 product-only 定义可被当前 validator 接受的输入形状，或明确该场景 STOP/降级。 |
| ENG-CURRENT-004 | `ArtifactRef` 要求 `ref` 为调用方允许的相对路径，但 `ReaderBundleInputs`/`project_reader_bundle` 没有显式 input root 或 resolver；计划中的 binding 示例也缺 `schema_version`/`version`。 | FR-PROJ-001/002、FR-ENTRY-001；AC-02/06/07；T003/T004 | 不能证明读取范围、版本和 hash 绑定；实现可能隐式依赖 cwd/仓库路径，违反边界合同。 | 增加显式 input root/resolver，并让所有 entry/spec refs 完整携带并校验 `schema_version`、`version`、SHA-256。 |
| ENG-CURRENT-005 | `BundleReport`、`BundleValidationReport` 的字段级 schema 未定义；`ParserSmokeResult` 的 required fields 没有 license/source ref，而 `run_parser_smoke` 也没有对应参数，无法独立证明 license/commit/vendor bytes 闭合。 | FR-VALID-001/002、FR-SMOKE-001/002；AC-05/08；T004/T008 | 文件存在或 parser 返回 pass 不能证明报告/兼容事实完整；profile finalize 可能遗漏关键 provenance。 | 补齐三个 result schema、生产者/消费者、license/source 字段及拒绝规则；为每个字段增加明确 oracle。 |
| ENG-CURRENT-006 | API 只写 `artifact_root/reports/*`，计划又把 `quality/evidence/task2a-reader-bundle/projection-report.json`、`exit-manifest.json` 列为 owning outputs；没有明确复制、hash、回读和失败恢复 producer。 | FR-PROJ-001/002；AC-02/05/07/08；T004/T008 | artifact root、validator 与 canonical evidence 可能分叉；回滚和验收无法判断哪个是事实源。 | 选择单一事实根，或写明唯一复制/哈希/回读步骤、owner、失败行为和 evidence oracle。 |
| ENG-CURRENT-007 | `artifact_root` 支持重复运行，但没有 exclusive-root、staging、锁或 atomic publish 合同；生命周期只写“失败不覆盖旧文件”。 | FR-PROJ-002、FR-VALID-001；AC-05/06；T004/T008 | 并发或中途异常可能留下 Bundle/Audit/Report 半套结果，破坏幂等和 degraded 一一对账。 | 要求 fresh exclusive root，或增加 staging 后原子提交；补 partial-write/concurrent invocation 负例和恢复证据。 |
| ENG-CURRENT-008 | accepted `spec.md:475-480` 把 smoke 失败后的 `OKF-inspired` 降级列为 AC-08 通过条件；`plan.md:147`、`tasks.md:578-584` 却把 downgrade 固定为 `ac08_status=blocked`，不算 GREEN。 | FR-BUNDLE-004、FR-SMOKE-001/002；AC-08；T007/T008 | 计划比 accepted spec 收紧交付语义，可能把合法降级误判为未完成，或导致实现按两个完成标准分叉。 | 由主计划明确采用哪一条已接受口径；若保留 blocked，先修订 spec/AC；若按 spec，通过条件必须区分 compatibility pass 与 honest downgrade pass。 |
| ENG-CURRENT-009 | `tasks.md:46` 把 `uv run --frozen pytest tests/ -q` 写入 final aggregate strategy，但 `plan.md:495-500` 的正式 gate 是六个定向文件，full tree 仅作 `display_cmd`。 | 全部 AC；final aggregate | 最终全量回归到底是验收命令还是展示命令不清，无法绑定 expected exit、evidence path 和 oracle。 | 删除冲突的 full-tree claim，或新增明确的 final aggregate gate/evidence/oracle；不要把默认全套命令当占位验收。 |
| INPUT-STOP-001 | 当前环境未设置 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS`，且 `reader_frontmatter.py`、`reader_bundle.py`、`okf_smoke.py`、Task 2-A tests/vendor 均不存在。 | FR-FIX-001/002、FR-SMOKE-001/002；AC-03/08；T005–T008 | 真实 attribution 与 parser compatibility 不能生成 RED/GREEN；不能用历史或 synthetic 结果关闭这些门。 | 保持 T005/T006/T008 blocked；提供受控 raw corpus、实际 vendor commit/license/bytes 后再执行目标 gate。 |

### Review disposition

- 本次只更新本事实文件；未修改 `spec.md`、`plan.md`、`tasks.md`、产品代码、provider、Git 或 task status。
- 上述 finding 交给 `wh-review` 消费；不生成 pass/revise 决策，不替代正式 provider 结果。

## Invocation retry-43bda6208bac502e9081dd6bc63f585795b69b6ce09829d312c1bbfd — current snapshot engineering review

- **reviewed material**：accepted `decision-log.md`、`spec.md`、当前完整 `plan.md`/`tasks.md`、当前 source anchors、Task 0/1 entry artifacts 和 task-store `index.json`/`facts.jsonl`/`quality/verify.json`。
- **snapshot facts**：本轮冻结 snapshot tree 为 `f0486d26bd7b2366fed78927df6f2b7b086ad1ee`；当前 `decision-log.md` SHA-256 为 `86f53ac3e0ca6960995a7e9e9f8f17010168f47126338581b39428e523a181b9`，`spec.md` 为 `69528c8e2f6eb3067f6375765978abe1fecf7575fbd87ec8a5919791de6abf68`，`plan.md` 为 `a8045ce52813ab9fd50d47b62f91f4b46504c2ab5803e2f27977856b80b14622`，`tasks.md` 为 `d3b6dfc0b1d27f10370d6729cec6fba59d5b415820066e43f913490be544c434`。`tasks.md` 仍引用旧 plan hash `34665f8e44cceac8f87e97129ec17d13e42e048efdcc9e9625fdabd11196231d`；`KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置；Task 2-A implementation/tests/vendor 不存在；task-store `reviews=[]`、`facts=[]`、`quality/verify.json.status=unknown`。本节是 advisory engineering lens，不是 provider verdict、stage result、用户确认或 build-code 放行。
- **source anchors checked**：`kb_structure.validate_topic_index`（`kb_structure.py:685`）、`identity.source_id`（`identity.py:39`）、`identity.resolve_topic_identity`（`identity.py:116`）、`jsonl.read_jsonl`（`jsonl.py:106`）、`cli.build_parser`/`cli.main`（`cli.py:26/78`）、`navigation.build_publication_navigation`（`navigation.py:256`）、`page_layout.build_topic_layouts`（`page_layout.py:572`）、`provenance.validate_prewrite_provenance`（`provenance.py:65`）、`pipeline.audit_run`（`pipeline.py:1688`）。
- **status**：`findings_recorded`；没有执行产品代码、测试、provider、Git、task status 或正式 stage-runtime review。

### Current findings

| finding_id | anchored fact | affected IDs | engineering consequence | smallest corrective action to wh-review |
| --- | --- | --- | --- | --- |
| ENG-RETRY-20260809-001 | `plan.md` 当前 SHA-256 为 `a8045ce52813ab9fd50d47b62f91f4b46504c2ab5803e2f27977856b80b14622`，但 `tasks.md:5` 和 T001–T008 的 `versioned_refs` 仍绑定旧 hash `34665f8e44cceac8f87e97129ec17d13e42e048efdcc9e9625fdabd11196231d`；`plan.md:17` 反而声明 tasks 已按当前 hash 重绑定。 | T001–T008；handoff | 下游可能按过期计划实施；当前 plan/tasks component receipt 不能证明同一冻结材料。 | 由官方 producer 重算并回读 `tasks.md` header、T001–T008 和最终 evidence 的 plan binding；修正 `plan.md:17`/相关 fixed 处置文字，匹配前 STOP build-code。 |
| ENG-RETRY-20260809-002 | `tasks.md:433-434` 的 Phase 2 Verify AC 表头重复出现两次。 | Phase 2；AC-01–AC-07；T003–T006 | AC 矩阵不是单一合法 Markdown 表结构，确定性材料检查或下游解析可能把重复表头当数据行。 | 删除一行重复表头，重新运行 plan/tasks 结构检查并回读 Phase 2 的 AC、oracle、evidence 映射。 |
| INPUT-STOP-001 (reconfirmed) | 当前 `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` 未设置，且 `reader_frontmatter.py`、`reader_bundle.py`、`okf_smoke.py`、Task 2-A acceptance tests/vendor 均不存在。 | FR-FIX-001/002、FR-ATTR-001/002、FR-SMOKE-001/002；AC-03/08；T005–T008 | 当前不能生成真实 fixture attribution 或 parser compatibility RED/GREEN；历史/synthetic 证据不能关闭这些门。 | 保持 T005/T006/T008 的真实输入 STOP；提供受控 raw corpus、实际 parser commit/license/notice/vendor bytes 后再执行目标 gate。 |

### Review disposition

- 本轮只追加本 advisory fact；未修改 `spec.md`、`plan.md`、`tasks.md`、产品代码、provider、Git 或 task status。
- 以上 finding 交给 `wh-review` 消费；不生成 pass/revise 决策，不替代正式 provider 结果。
