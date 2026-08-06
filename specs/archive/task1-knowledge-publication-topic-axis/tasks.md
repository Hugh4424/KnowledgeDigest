# 历史 product-only 任务记录（只读审计记录，非当前授权）

状态：旧 product-only build-plan 任务已因 `knowledge_type` scope revision 暂停；需要在同一任务中重排受影响任务后才能继续 build-code。

每个实现任务只做一个可验证闭环。旧 T01–T12 记录的是 product-only 方向，不再作为修正版的执行授权；新的任务必须先覆盖 `knowledge_type` registry、Products 嵌套 ProductGazetteer、非产品安全降级和 v2 key/path，再恢复实现。历史完成记录保留作审计，不删除、不改写成修正版通过。

## T01：冻结结构、schema 和旧索引迁移合同

- 变更范围：`kb_structure.py`、`validate_topic_index`、`TOPIC_INDEX_SCHEMA_VERSION`、schema/序列化测试、Task1 fixture。
- 依赖：无。
- 做什么：定义 SourceInventory、ProductGazetteer、TopicPlan、TopicIndex、AffectedSet、ConflictRecord 的最小字段和稳定排序；支持 JSON `null`、状态枚举、证据引用和四个 `_digest` 输出路径；明确新 TopicIndex schema 与旧 1.0.0 的双读/迁移规则，保留旧 `digest_topic_id` 和旧路径，不静默删除。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "schema or topic_index_migration" -q`；RED→GREEN；证据 `artifacts/task1/t01-schema-migration.txt`。缺字段、空串冒充未知、重复 topic/source、旧 schema 丢字段或错误输出根目录必须明确失败；合法新旧样例可 round-trip。
- 覆盖：FR-01、FR-02、FR-05、FR-12；AC-01、AC-02、AC-05、AC-13。

## T02：建立 89 条结构 inventory

- 变更范围：`ingest.py`、结构提取纯函数、固定 89 条 fixture/JSONL。
- 依赖：T01。
- 做什么：为每个来源保存 URI、指纹、标题/H1、父子路径、表格/FAQ/图片/双语/版本/噪声特征和稳定排序的内部 link edges；每条 link edge 带目标和来源行定位。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "inventory or link_edges" -q`；RED→GREEN；证据 `artifacts/task1/t02-inventory.jsonl`。fixture 必须得到 89 条；删除来源、改 URI/指纹、缺定位、未声明目标时必须 fail-closed；只有输入顺序变化允许得到稳定相同结果。
- 覆盖：FR-01、FR-08、FR-12；AC-01、AC-08、AC-12。

## T03：实现 ProductGazetteer 匹配和 canonical 门禁

- 变更范围：`kb_structure.py` 受控区段、匹配规则函数、词表与匹配 acceptance。
- 依赖：T01、T02。
- 做什么：实现 canonical → alias → parent_path → h1_title → candidate 的固定顺序；同级多命中冲突；entry 保存 kind/owner/object_intents/source_refs/status/reason；candidate 不得晋升正式项；只有 `status=canonical` 才能填 published 轴字段。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "gazetteer or canonical_gate or single_source_predicates" -q`；RED→GREEN；证据 `artifacts/task1/t03-gazetteer.json`。canonical/alias/父子路径/H1/候选各有样例；同级冲突、无 product、非 canonical 命中和模型直写正式词表均失败或 degraded。
- 覆盖：FR-02、FR-04、FR-10；AC-02、AC-04、AC-10。

## T04：实现 v1 key、slug、degraded key 和路径冲突

- 变更范围：`identity.py`、`kb_structure.py` 声明 root/保留词校验、identity tests。
- 依赖：T03。
- 做什么：实现 `v1/<product>/<module>/<object-intent>`、NFKC/ASCII/保留词 `x-` 规则、规则升级用 v2、无 hash/序号/输入顺序；实现可读 degraded key；`PUBLISHED_PATH_COLLISION` 和 `DEGRADED_KEY_COLLISION` 写前 fail-closed。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "identity or slug or path_collision or degraded_collision" -q`；RED→GREEN；证据 `artifacts/task1/t04-identity.json`。同输入不同 batch/order/repeat 得到同 key/path；冲突不加后缀、不自动降级。
- 覆盖：FR-05、FR-06；AC-05、AC-06。

## T05：实现确定性 object/intent seed 与 TopicPlan

- 变更范围：计划生成函数、`pipeline.py` provider 前边界、plan fixture。
- 依赖：T03、T04。
- 做什么：按既有托管 object/intent → metadata → H1 → 标题 → 父子路径末级取 seed；同产品/模块下合并，来源只能进入一个主题；provider 调用前冻结计划版本和证据；无法唯一取 seed 时 degraded 的正式轴字段为 JSON `null`。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "topic_plan or object_intent or provider_boundary" -q`；RED→GREEN；证据 `artifacts/task1/t05-topic-plan.json`。provider 不可用或返回改名/改归属时，计划身份、成员、key、状态不变。
- 覆盖：FR-03、FR-04、FR-07、FR-10、FR-11；AC-03、AC-04、AC-07、AC-10、AC-11。

## T06：生成新 TopicIndex、旧 schema 迁移和旧路径映射

- 变更范围：`page_layout.py`、`kb_structure.py` TopicIndex 投影/迁移、旧 `digest_topic_id` 兼容测试。
- 依赖：T04、T05。
- 做什么：按一个当前主题一条记录生成新 TopicIndex；扩展校验器允许新 schema 和 degraded `null`；读取旧 `_digest/topic-index.json` 时按 schema/version 迁移，保存旧路径、旧 `digest_topic_id` 和 `old_path_mapping[]` 的 rename/merge/split/unmappable 关系。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "topic_index or old_schema or old_path_mapping" -q`；RED→GREEN；证据 `artifacts/task1/t06-topic-index.json`。同产品同对象合并、不同产品同名分开；旧文件不会被静默丢弃；degraded 正式轴字段/path 为 JSON `null`。
- 覆盖：FR-04、FR-05、FR-06；AC-04、AC-05、AC-06。

## T07：实现 batch/order/repeat 不变性

- 变更范围：`batch_run.py`、确定性比较器、稳定性 acceptance。
- 依赖：T04、T05、T06。
- 做什么：固定输入清单和稳定排序；在纯 TopicPlan/TopicIndex 计算边界比较 batch-1、batch-20、重排和重复输入。Task1 opt-in 的正式写入命令明确拒绝旧的逐批正文流水线，避免每个 batch 覆盖完整四产物；batch size 只能影响后续传输层，不能改变计划结果。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "batch_invariance" -q`；RED→GREEN；证据 `artifacts/task1/determinism/{batch-1,batch-20,reordered,repeated}.json`。四种运行得到相同 canonical JSON/JSONL；一个 source 不得出现在多个主题。
- 覆盖：FR-07、FR-11；AC-07、AC-11。

## T08：实现 affected set、首次导入和显式 rebuild

- 变更范围：`batch_run.py`/`pipeline.py` 的增量计算、首次/rebuild/增量触发矩阵测试。
- 依赖：T02、T05、T06、T07。
- 做什么：按来源/指纹/结构 link、TopicPlan、Gazetteer、旧映射变化加入直接相关主题和产品/模块投影；首次导入和内部 `topic_axis_plan(..., rebuild=True)` 显式 rebuild 产生完整 affected set；普通无变化返回空集合；不写 Home，不新增对外 CLI。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "affected_set or rebuild" -q`；RED→GREEN；证据 `artifacts/task1/affected-set.json`。测试明确调用 `topic_axis_plan(..., rebuild=True)`；首次/rebuild 覆盖全部主题，增量只覆盖完整受影响集合，无变化为空；集合外既有正文和路径字节完全不变。
- 覆盖：FR-08；AC-08、AC-12。

## T09：实现托管哈希冲突和显式 override

- 变更范围：`writeback.py`、`_digest/runs/<run_id>.json` 冲突记录、冲突 acceptance。
- 依赖：T06、T08。
- 做什么：比较 managed/actual hash；默认保留人工文件、停止受影响写回并记录 `MANAGED_CONTENT_CONFLICT`；只接受逐页、带原现 hash/说明/原因/ref 的 override manifest，追加 `MANAGED_CONTENT_OVERRIDE`。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "managed_conflict or override" -q`；RED→GREEN；证据 `artifacts/task1/conflicts.json`。无 manifest 不覆盖；override 不能批量放开或静默更新 hash；运行结果和审计文件含相同恢复事实。
- 覆盖：FR-09；AC-09。

## T10：接通四个审计投影与离线边界

- 变更范围：`pipeline.py`、`writeback.py`、CLI 离线配置、运行审计测试、旧 topic-index 迁移输出。
- 依赖：T07、T08、T09。
- 做什么：按原子写入顺序输出 source-inventory、topic-plan、topic-index 和 run record；旧 topic-index 迁移结果和四个产物互有指纹；`--no-llm + Jaccard` 不探测 embedding、不发网络请求；provider 只读冻结计划。
- 检查：先跑 `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "offline or zero_network or audit_outputs" -q`，再跑 `uv run --frozen digest tests/fixtures/task1_topic_axis/new_dir tests/fixtures/task1_topic_axis/kb_dir --config tests/fixtures/task1_topic_axis/offline.json --no-llm`；两者 RED→GREEN，CLI GREEN 预期退出码 0；证据 `artifacts/task1/offline-run.json`。测试 monkeypatch `socket.socket.connect` 与 `socket.create_connection` 并断言计数为 0；四个 `_digest` 路径存在、稳定排序、不进入 reader package。
- 覆盖：FR-03、FR-08、FR-09、FR-11；AC-03、AC-08、AC-09、AC-11、AC-13。

## T11：补齐 12–20 个可回溯样例和失败矩阵

- 变更范围：`tests/fixtures`、`tests/acceptance`、样例报告生成。
- 依赖：T03、T05、T06、T09、T10。
- 做什么：固定排序生成 12–20 个 TopicPlan 样例，覆盖合并、unknown、candidate/conflict、五项单来源 true/false、路径冲突和人工冲突；每个样例保留来源证据。
- 检查：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "examples or failure_matrix" -q`；RED→GREEN；证据 `artifacts/task1/topic-plan-examples.json`。每个样例能回到 URI/指纹/行定位；至少一个五项全 true 和每项 false 样例；报告明确不是 89 条完整语义发布。
- 覆盖：FR-10、FR-12；AC-04、AC-10、AC-12。

## T12：跑全量回归并同步 Task1 文档

- 变更范围：Task1 acceptance、现有全量测试、必要的 `AGENTS.md`/对应开发文档同步。
- 依赖：T01–T11。
- 做什么：运行 Task1 专用和现有全量 acceptance；只同步实际改变的 CLI、文件结构、质量门禁或开发命令；记录失败边界、证据路径和 `not_released` 交付状态。
- 检查：实现前不执行全量回归；实现后 `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -q` 和 `uv run --frozen pytest tests/acceptance -q` 均 GREEN（退出码 0）；T12 记录前置 T01–T11 的 RED→GREEN 事实，不伪造 T12 自身的 RED；离线命令沿 T10 执行；证据 `artifacts/task1/final-regression.txt`。文档没有把 Home、正文或 released 写成已完成；任何失败均保留明确错误。
- 覆盖：FR-01–FR-12；AC-01–AC-13。

## 反向覆盖索引

- FR-01：T01、T02、T12；AC-01。
- FR-02：T01、T03、T12；AC-02。
- FR-03：T05、T10、T12；AC-03。
- FR-04：T03、T05、T06、T11；AC-04。
- FR-05：T01、T04、T06、T12；AC-05。
- FR-06：T04、T06、T12；AC-06。
- FR-07：T05、T07、T12；AC-07。
- FR-08：T02、T08、T10、T12；AC-08。
- FR-09：T09、T10、T12；AC-09。
- FR-10：T03、T05、T11、T12；AC-10。
- FR-11：T05、T07、T10、T12；AC-11。
- FR-12：T01、T02、T11、T12；AC-12、AC-13。

## build-plan 交付前检查

- [ ] 每项任务有范围、依赖、可执行检查、RED/GREEN 预期、证据路径和 FR/AC 映射。
- [ ] 依赖图无环，阶段顺序为 P0→P4。
- [ ] 所有 FR-01–FR-12 和 AC-01–AC-13 均有双向覆盖。
- [ ] 独立审查的实际 provider、verdict、finding 处置和下一步已写入 `plan.md` §11。
- [ ] 用户明确确认计划后，才允许 handoff 到 `build-code`。

## Task completion records

### Phase 1：T01–T03 — completed 2026-08-05

- Delivered: frozen TopicIndex 2.0.0 validation and legacy 1.0.0 migration; deterministic 89-source structural inventory with stable URI/fingerprint/line evidence and fail-closed internal links; controlled ProductGazetteer read/write and canonical-only product/module matching; single-source five-field gate; candidate/conflict/unknown remain degraded.
- Focused checks: `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -q` → 17 passed; `uv run --frozen pytest tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_publication.py tests/acceptance/test_publication_contract.py -q` → 54 passed; `python -m py_compile src/knowledge_digest/topic_axis.py src/knowledge_digest/kb_structure.py src/knowledge_digest/pipeline.py src/knowledge_digest/batch_run.py src/knowledge_digest/identity.py` → passed; `git diff --check` → passed.
- Evidence: repository fixture `tests/fixtures/task1_topic_axis_89/` contains 89 sources and all seven required structural feature classes; acceptance covers image/link normalization, undeclared-link failure, schema migration, Gazetteer round-trip, canonical/candidate/conflict gates, and evidence completeness.
- Covered: FR-01, FR-02, FR-04, FR-10, FR-12; AC-01, AC-02, AC-04, AC-05, AC-10, AC-12, AC-13.
- Independent phase review: PASS after repair loop. Findings disposed: legacy degraded path and semantic-field preservation `fixed`; undeclared internal target `fixed`; merge/unknown/conflict examples `fixed`; 89-source/structure evidence `fixed`; ProductGazetteer integration `fixed`; image-vs-link and safe `../` normalization `fixed`; single-source completeness/evidence checks `fixed`; ProductGazetteer same-tier conflict in `fact_conflict_free` `fixed`.
- Unresolved risk: the fixture is structural evidence, not the real 89-source production corpus; full semantic publication remains explicitly outside Task1 and stays `not_released`.
- Next: Phase 2 (T04–T06).

### Phase 2：T04–T06 — completed 2026-08-05

- Delivered: deterministic v1 semantic key and readable degraded key with NFKC/ASCII/reserved-word handling; duplicate key/path fail-closed; provider-before-plan boundary; same-axis merge and different-product split; TopicIndex 2.0.0 projection with legacy digest identity and rename/merge/split/unmappable mappings.
- Focused checks: `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "identity or slug or path_collision or degraded_collision or topic_plan or object_intent or provider_boundary or topic_index or old_schema or old_path_mapping" -q` → 6 passed; old regression suite → 54 passed; `py_compile` and `git diff --check` → passed.
- Covered: FR-03, FR-04, FR-05, FR-06, FR-07, FR-10, FR-11; AC-03, AC-04, AC-05, AC-06, AC-07, AC-10, AC-11.
- Independent phase review: PASS. No valid findings remained.
- Unresolved risk: semantic identity migration preserves old paths and IDs but does not release reader pages; Task1 remains `not_released`.
- Next: Phase 3 (T07–T09).

### Phase 3：T07–T09 — completed 2026-08-05

- Delivered: Task1 fixed-manifest determinism across batch-1/batch-20/reorder/repeat; Task1 opt-in rejects legacy batch write; affected set includes current/previous source edges, reverse link impact, match/plan changes, and old mapping changes; managed hash conflict is fail-closed, missing hash is visible, and explicit per-page override records the full manifest hash.
- Focused checks: Phase 3 focused → 6 passed; `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -q` → 24 passed; old regression suite → 54 passed; `py_compile` and `git diff --check` → passed.
- Covered: FR-07, FR-08, FR-09, FR-11; AC-07, AC-08, AC-09, AC-11.
- Independent phase review: PASS after repair loop. Findings disposed: reverse impact for old-link deletion `fixed`; full override manifest hash and unique refs `fixed`; missing managed hash conflict `fixed`; real batch/repeat/old-mapping evidence `fixed`; old/current snapshot preservation and mapping-change detection `fixed`.
- Unresolved risk: Task1 does not write reader pages, so affected-set evidence is an input for later publication tasks rather than a released navigation update.
- Next: Phase 4 (T10–T12).

### Phase 4：T10–T12 — completed 2026-08-05

- Delivered: four Task1 audit projections and run record with stable ordering and real byte hashes; opt-in CLI path before provider with `--no-llm` zero-network evidence; fixed 89-source structural fixture; 20-example failure matrix covering merge, unknown, conflict and each single-source check; AGENTS architecture and boundary documentation synchronized.
- Focused checks: Phase 4 focused → 5 passed; `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -q` → 26 passed; old regression suite → 54 passed; CLI fixture exited 0 with `inventoried 89 source(s)` and `not_released`; `py_compile` and `git diff --check` → passed.
- Covered: FR-01–FR-12; AC-01–AC-13.
- Independent phase review: PASS after repair loop. Finding disposed: required-evidence failure examples now retain URI, fingerprint and line fields while using invalid values to demonstrate the failed gate; test checks field completeness.
- Unresolved risk: the fixed fixture is structural evidence only; real production corpus, final reader pages, semantic quality and released delivery remain outside Task1.
- Next: verify-code reverse check; stop before close.

### verify-code：completed 2026-08-05；停在 close 前

- Reverse scope checked: decision-log 原始需求、PRD Task1、`universal-knowledge-digest-design.md`、reader/audit 分离 ADR、完整操作者流程和延期的读者流程；实现与当前四份材料逐项对照。
- Full regression (historical pre-`/wiki`-link repair snapshot): `uv run --frozen pytest tests/acceptance -q` → 368 passed, 2 skipped; `py_compile` → passed; `git diff --check` → passed。该数字不代表当前最新回归收据。
- AC result: AC-03–AC-07、AC-09–AC-13 = pass；AC-01 = unknown（固定 89 条结构 fixture 通过，但真实生产 89 条语料未提供）；AC-02 = unknown（受控词表链路通过，但真实语料完整 seed 覆盖无证据）；AC-08 = unknown（affected set 算法通过，但 Task1 不写真实旧读者页面，集合外页面字节不变缺少现场证据）。
- Boundary result: CLI opt-in 实际输出 89 sources、`not_released`、无 Home/reader 写入；未知/冲突/candidate 均 degraded；没有把样例、测试绿灯或阶段完成写成 released。
- Review fact (historical record): Phase 1–4 独立复审均达到 PASS；当时官方 verify `wh-review` 在材料预检阶段不可用，未伪造替代 receipt 或 PASS。代码和测试证据已保留，unknown 按要求保留；后续证据补齐后已重新走官方入口。
- Close boundary: 未提交、未合并、未推送、未关闭；下一步只等待用户决定是否进入 close 或处理 unknown 证据。

### Evidence follow-up：completed 2026-08-05；准 close 前复核

- Real corpus fact: 在 `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb/_digest/source-snapshots.jsonl` 找到真实运行快照；178 行是两次完整快照，去重后 89 个 `source_uri`、88 个内容指纹。直接调用 `build_source_inventory(..., expected_count=89)` 成功：89/89 都有 URI、内容指纹和来源定位；其中 `confluence://company/merchant system/Dashboard_MerchantPortal.md` 与 `confluence://company/merchant system/Dashboard_ResellerPortal.md` 共享指纹 `61f416abeb33660ff339446ca3e54a549636c94b32a593e8890b765d02c1d54e`，inventory 保留两条来源记录，不因内容重复误删来源。另有 89/89 父子路径、89/89 至少有路径或标题/H1 seed，结构特征覆盖为 table 79、FAQ 7、image 61、bilingual 88、version 77、noise 9。
- Real-corpus repair: 真实 Confluence 内容包含 105 个 host-relative `/wiki/...` 链接；它们是外部网页链接，不是本地 source-tree 路径。`topic_axis.py` 现在忽略这类边，仍对本地相对链接执行声明目标和路径逃逸校验；新增 acceptance 覆盖。当前 canonical 最新回归收据 → 369 passed, 2 skipped；Task1 focused → 27 passed；`py_compile` 和 `git diff --check` 通过。该 369 是修复后的新 snapshot，不与上面的历史 368 混用；具体 snapshot_tree 和 receipt ref 以本次官方 review packet 的 immutable roots 为准。
- C-01 / AC-01: 已补齐真实 89 条结构 inventory 证据；不把 fixture 当生产语料，也没有把原始语料复制进仓库。
- AC-02: 已补齐真实 seed 覆盖审计：4 个父路径根、89/89 来源定位字段、80/89 有 H1/title；但真实旧 KB 没有正式 canonical `ProductGazetteer`，所以“正式产品/模块/别名词表已完整确认”仍是 `unknown`。延期交接：由产品维护者确认 canonical product/module、alias、object/intent 和 source_refs 后，再重跑真实 TopicPlan；临时 boundary harness 的词表不作为正式语义证据，模型不得自动晋升。
- AC-08: 使用真实旧 KB `/Users/Hugh/Downloads/KnowledgeDigest-task2-qwen-final9-20260804/company-kb` 的隔离副本运行 boundary harness；89 条 inventory、4 个临时 boundary topics、`not_released`；排除 `kb.structure.md` 后 151 个真实读者 Markdown 文件运行前后 manifest SHA-256 均为 `d91469ccefd53dd7d2ae12783969b6bbae1571c73d20768dcd7f52876b2b04e2`，字节不变。只写 `_digest` 审计输出；这证明 Task1 的读者写入边界，不替代 AC-02 的正式词表确认。
- Review fact: 本轮真实语料修复曾有几次正式材料预检失败，原因是 `context_map` 锚点/verify-code 证据包不完整，不是 provider 或 task handle 不可用；补齐 TaskKernel 任务证据后，官方 `wh-review` 已成功进入 provider，并返回正式 `revise_required`。此前 Phase 1–4 review PASS 仍作为历史审查事实，新增 host-relative 链接改动已由 focused/full tests 覆盖。
- Final verify-code disposition: AC-01 = pass（真实 89 条结构 inventory）；AC-02 = unknown（正式 canonical 词表仍需产品维护者确认）；AC-08 = pass（真实旧读者文件的写入边界和既有 affected-set 测试共同覆盖）；其余 AC 保持此前 pass。整体不能宣称“所有 AC 已通过”，只能准 close 并保留 AC-02 延期交接。
- Close boundary: 当前可进入准 close；但不能把 AC-02 的 unknown 改写成 pass，也不能声称真实语料已完成正式语义发布。未提交、未合并、未推送、未正式 close。
- Latest official verify-code review: 当前最新 immutable receipt、逐 AC evidence aggregate、context/evidence maps 和官方 review packet 已绑定同一个候选 snapshot；provider 已正常返回，未发生 unavailable，公开 verdict 为 `pass`。provider 的唯一实质意见是 AC-02 的产品层 ProductGazetteer 仍未由产品维护者确认；该意见保持为延期交接，不是代码缺陷，也不能把保守的机器 `fail` 改写成 pass。此前各轮 snapshot ID 只作历史审查记录，不作为当前 binding。AC-01 的 89/88 指纹表述已修正，任务保持准 close，等待产品维护者确认后再重跑真实 TopicPlan/AC-02。

### build-code integration review disposition：completed 2026-08-05

- `F-255628897265`：fixed。`ProductGazetteer.object_intents[]` 是证据字段，不是发布白名单；移除额外 membership gate，并新增未列入 `object_intents[]` 但 seed 唯一时仍可发布的 acceptance。
- `F-774ceaa43bc8`：rejected_invalid。审查上下文只截取了 `build_topic_plan`，未包含实际负责旧路径映射的 `topic_index_from_plan`；该函数已读取 `old_topic_index`，并覆盖 rename/merge/split/unmappable，AC-05/AC-06 锚点已改到真实实现。
- `F-92d18d0aebf6`：rejected_invalid。AC-07 原锚点落在旧的 batch 规划代码；已改到 `build_topic_plan` 的稳定排序/分组实现，批次、顺序和重复运行的测试证据已存在。
- `F-a173e35765f0`：rejected_invalid。`canonical-evidence.json` 由 WorkflowHub provider packet 固定写为空数组，canonical receipts 通过 TaskKernel 绑定，不复制进 provider bundle；正式 verify-code 已审查同一根证据并返回 pass。
- `F-13abe4f24e7b`：accepted_risk。当前 `tasks.md` 没有标准 `#### Txx` 完成行，历史 Phase 链无法重放；不补造 Phase receipt，保留为审计缺口，不阻止当前实现审查，但正式 close 前仍需按当前 WorkflowHub 事实链如实处理。
- `F-db3f7f26c44f`：accepted_risk。`paths_by_content` 是无效的轻微死代码，不影响 Task1 行为或交付边界；后续清理不进入本次 close 范围。
- 修复后 focused：`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -q` → 27 passed；新的实现/测试证据必须绑定修复后的候选 snapshot。

### 真实语料 ProductGazetteer 补证：completed 2026-08-05

- Delivered: missing ProductGazetteer 时从当前 source inventory 的产品根路径、标题和 H1 自动生成稳定、可追溯的 candidate seed；写回 `kb.structure.md` 受控区段；降级 key 能保留中文证据并避免真实语料同首级标题碰撞。
- Real input: `/Users/Hugh/Downloads/confluence 原始数据`，89/89 Markdown；与历史真实快照逐文件 SHA-256 一致。
- Real run: 4 个 product candidate、89 个 module candidate，共 93 项；每项有 source URI、内容指纹和行定位；未读取 CompanyBrain，未自动晋升 canonical。
- Checks: Task1 focused `29 passed`；旧回归 `54 passed`；全量 acceptance `371 passed, 2 skipped`；`py_compile` 和 `git diff --check` 通过。
- Covered: AC-01 的真实来源边界、AC-02 的真实 seed 覆盖和 source-derived 生成链；AC-02 的 canonical owner/alias/object-intent 确认仍保留为延期交接，不能改写成已完成。

### build-code Phase 5 finding disposition：completed 2026-08-05

- `F-6b69ee15b4fd`：fixed。`_single_source_checks` 对未命中 product/module 改用空字典安全取值，并新增 unknown source acceptance；focused 结果 30 passed。
- `F-8128de567d54`：fixed。样例循环显式按剩余容量取值并返回，保持总数 12–20；已有失败矩阵和 focused acceptance 继续覆盖。
- `F-7e8d9f85f441`、`F-98e5c9e2ce9b`：fixed。不是业务逻辑缺失，而是 integration packet 的默认代码锚点过窄；本次 Phase completion row 提供每条 AC 的当前实现锚点和测试绑定，后续 packet 使用这些声明锚点。
- `F-8141172e9849`：fixed for current work。补齐本次真实语料 Phase 的标准 completion row、passing phase review、implementation diff 和 GREEN receipt；不补造之前未结构化的历史 Phase receipt。
- `F-cf5b36808d34`：accepted_risk。跨 Phase seam 继续按 WorkflowHub 合同标记 `unknown/TRACE_HAS_PATHS_NOT_SEMANTIC_SEAMS`，没有把路径存在误报成语义 seam 完成。

#### Historical T13：真实语料 ProductGazetteer 编译与降级边界

- [x] **任务完成**
- **status**：`completed`
- **covered_ac**：AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-12, AC-13
- **evidence_refs**：`[{"ref":"quality/evidence/implementation/452a3a7fea702ce58aaff7bacda9c55591970177.json","sha256":"69399c7aa69cf02e112321ac180b9e785063a3ece092ce4d3b3863fa0e90bd74"},{"ref":"quality/tests/build-code-task1-real-corpus-452a3a7fea702ce58aaff7bacda9c55591970177.json","sha256":"18d538fdc71bb6233531cdf7f4b48c736d8dda2d0292a0cbabcc215996b84f9a"},{"ref":"quality/reviews/results/build-code-default-452a3a7fea702ce58aaff7bacda9c55591970177-8d882f8e-8255-4ed0-9f21-d32f54618dd2.json","sha256":"1faf7732fe6ac7cad321e64beaa0fe8dd919490af91a09333d3da8e467844c00"}]`
- **actual_changes**：真实语料缺少 ProductGazetteer 时由 KnowledgeDigest 从产品根路径、标题/H1 生成 93 个可追溯 candidate；unknown match 不崩溃；TopicPlan 降级 key 保留中文来源证据；样例上限显式为 12–20。
- **phase_id**：`phase-5-real-corpus-gazetteer`
- **review_fact**：`{"ref":"quality/reviews/results/build-code-default-452a3a7fea702ce58aaff7bacda9c55591970177-8d882f8e-8255-4ed0-9f21-d32f54618dd2.json","sha256":"1faf7732fe6ac7cad321e64beaa0fe8dd919490af91a09333d3da8e467844c00"}`
- **phase_map_trace**：`{"ref":"evidence/implementation-f0b4c69073ab533cf9606f6fe4165071bf0eb764d0973d7feb05e1081397ed7d.diff","sha256":"f0b4c69073ab533cf9606f6fe4165071bf0eb764d0973d7feb05e1081397ed7d"}`
- **green_test_receipt**：`{"ref":"quality/tests/build-code-task1-real-corpus-452a3a7fea702ce58aaff7bacda9c55591970177.json","sha256":"18d538fdc71bb6233531cdf7f4b48c736d8dda2d0292a0cbabcc215996b84f9a"}`
- **implementation_anchors**：`{"AC-01":[{"id":"implementation:AC-01","path":"src/knowledge_digest/topic_axis.py","start_line":274,"end_line":375,"role":"implementation","reason":"source inventory and structural evidence"}],"AC-02":[{"id":"implementation:AC-02","path":"src/knowledge_digest/topic_axis.py","start_line":178,"end_line":270,"role":"implementation","reason":"source-derived ProductGazetteer candidate compiler"}],"AC-03":[{"id":"implementation:AC-03","path":"src/knowledge_digest/topic_axis.py","start_line":633,"end_line":740,"role":"implementation","reason":"provider-before-plan and TopicPlan construction"}],"AC-04":[{"id":"implementation:AC-04","path":"src/knowledge_digest/topic_axis.py","start_line":506,"end_line":718,"role":"implementation","reason":"canonical match and degraded outcomes"}],"AC-05":[{"id":"implementation:AC-05","path":"src/knowledge_digest/topic_axis.py","start_line":786,"end_line":900,"role":"implementation","reason":"TopicIndex projection and old mapping"}],"AC-06":[{"id":"implementation:AC-06","path":"src/knowledge_digest/topic_axis.py","start_line":633,"end_line":733,"role":"implementation","reason":"stable keys and published path collision checks"}],"AC-07":[{"id":"implementation:AC-07","path":"src/knowledge_digest/topic_axis.py","start_line":633,"end_line":740,"role":"implementation","reason":"stable sorting and grouping"}],"AC-08":[{"id":"implementation:AC-08","path":"src/knowledge_digest/topic_axis.py","start_line":918,"end_line":1000,"role":"implementation","reason":"affected set calculation"}],"AC-09":[{"id":"implementation:AC-09","path":"src/knowledge_digest/topic_axis.py","start_line":1025,"end_line":1068,"role":"implementation","reason":"managed hash conflict and override"}],"AC-10":[{"id":"implementation:AC-10","path":"src/knowledge_digest/topic_axis.py","start_line":587,"end_line":623,"role":"implementation","reason":"single-source completeness predicates"}],"AC-11":[{"id":"implementation:AC-11","path":"src/knowledge_digest/topic_axis.py","start_line":1136,"end_line":1208,"role":"implementation","reason":"offline topic-axis run and provider boundary"}],"AC-12":[{"id":"implementation:AC-12","path":"src/knowledge_digest/topic_axis.py","start_line":1085,"end_line":1133,"role":"implementation","reason":"audit-only not-released output"}],"AC-13":[{"id":"implementation:AC-13","path":"src/knowledge_digest/topic_axis.py","start_line":1085,"end_line":1133,"role":"implementation","reason":"stable audit artifact hashes"}]} `

### build-code Phase 8：严格重复运行、托管冲突与保留词边界 — completed 2026-08-05

- 当前候选 snapshot：`cd68bd30cc029a7ed9518bc3c680b94538119a6e`；focused `38 passed`；full `380 passed, 2 skipped`；`py_compile`、`git diff --check` 通过。
- 当前异源 review：`quality/reviews/results/build-code-default-cd68bd30cc029a7ed9518bc3c680b94538119a6e-db1f9983-5d33-4ac1-9cdc-c56162dd1dad.json`，SHA-256 `64ad6c75d87361bb9ca644c069437413830b218c287d529f100efc1815f10a6e`，`phase_id=phase-8-final-repairs`，正式 verdict `pass`；`pi/coding` 与 `cursor/grok` 均 completed，未发生 unavailable。
- 已评估并处置此前有效建议：重复运行补读上一轮 inventory/plan，使无变化时 `affected_set.empty`；托管页哈希改为排除自引用字段，匹配哈希不再误报冲突；真实入口接通声明式 override manifest；保留词二次转义碰撞改为 degraded，不合并来源。
- 本轮三个 minor 建议：`canonical-evidence.json=[]` 属于 WorkflowHub packet 固定的执行阶段空索引，代码审查所需的测试收据已由 `test_evidence` 绑定，记为 `rejected_invalid`；1297 行 `topic_axis.py` 是本任务集中实现审计边界，当前不拆分以避免扩大变更面，记为 `accepted_risk`；AC 锚点已在任务完成记录中落到 `topic_axis.py` 和 Task1 acceptance，不再采用统一 `identity.py:1` 桩，记为 `fixed`。
- Covered：AC-01–AC-13。当前阶段不写 reader 页面，不把真实 candidate 自动晋升 canonical；AC-02 的正式词表确认仍是独立延期项。

### Phase 9：source-canonical ProductGazetteer confirmation — completed 2026-08-06

- **goal**：按用户新确认的 source-canonical 规则，从当前 89 条原始语料自身确认产品根和稳定 page/capability module seed，重跑 AC-02；模型候选、外部词表和 reader 发布边界不变。
- **files**：`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`、`specs/task1-knowledge-publication-topic-axis/{decision-log,spec,plan,tasks}.md`。
- **oracle**：4 个 canonical product、89 个 canonical module；每项 owner/source_refs/稳定排序完整；`object_intents=[]` 仅表示原始语料没有结构化 object/intent，不伪造业务词；CompanyBrain 读取为 0；Task1 仍 `not_released`。
- **focused_cmd**：`export KNOWLEDGEDIGEST_TASK1_RAW_CORPUS='/Users/Hugh/Downloads/confluence 原始数据' && uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k 'source_canonical or generated_gazetteer or real_corpus' -q`
- **full_cmd**：`export KNOWLEDGEDIGEST_TASK1_RAW_CORPUS='/Users/Hugh/Downloads/confluence 原始数据' && uv run --frozen pytest tests/acceptance -q`
- **stop**：不把模型提案或 CompanyBrain 内容写成 canonical；不写 Home/正文；测试或审查失败时停在当前任务修复，不 close。

#### T29：source-canonical promotion and AC-02 revalidation

- **status**：completed
- **FR**：FR-02、FR-03、FR-04、FR-10、FR-12
- **AC**：AC-02、AC-04、AC-05、AC-10、AC-13
- **files**：`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`
- **oracle**：当前 raw corpus 生成 4 个 canonical product、89 个 canonical module；模型候选仍 candidate；每项 owner/source_refs 完整；source inventory、TopicPlan、TopicIndex 和 not_released 边界保持有效。
- **stop**：若只能靠 CompanyBrain、模型语义或未提供的业务词表才能确认，保留 unknown；不写 reader 页面、不 close。

##### T29 completion — 2026-08-06

- **actual_changes**：ProductGazetteer 改为从当前原始语料的显式 `products/<product-root>` 和稳定 source page/capability seed 生成 source-canonical entry；模型提案仍隔离为 candidate；缺少结构化 object/intent 时保持空数组；缺少显式 `knowledge_type` 时 fail-closed；H1 只取真正的一级标题。
- **real_corpus_oracle**：`/Users/Hugh/Downloads/confluence 原始数据` 共 89 条 Markdown；生成 4 个 canonical product、89 个 canonical module，全部有 `owner`、`source_refs` 和稳定排序；CompanyBrain 未作为运行时上游；Task1 仍 `not_released`。
- **test_receipts**：focused `quality/tests/verify-code-task1-ac02-current-90fdac.json`（SHA-256 `185bce56d18c084068d7da6b26847c23f6dcfd90759362c51c05dffae1db911d`）；full `quality/tests/verify-code-full-task1-current-90fdac.json`（SHA-256 `c54e08e24cbd6e924839fe9737619950d7419c6d39c5bdaa665a3b295167cc71`），结果 `47 passed`、`389 passed, 2 skipped`。
- **implementation_receipt**：`quality/evidence/implementation/97b8545b3adccadc52e91949f8abc102cbf06f5937b05f5c3c6bef57630fe046.json`，SHA-256 同名 hash。
- **review_fact**：Phase 9 build-code review `quality/reviews/results/build-code-default-90fdac6f82900eb066a58f16f022a5987d499e16-8a58a10b-1a0f-4912-8238-1b2048fdfe89.json`，SHA-256 `669f1f7b5fb426716f717a3f97368743e97d2adceae1c5ac85a1bf876ae97b05`，verdict=`pass`；scope revision review `quality/reviews/results/build-code-default-3b3ea112b5fbc1fa35029fbfdf676d748fb1dcce-39b4a0bf-dd73-45c9-854e-df7f0bf9590a.json`，verdict=`pass`。Phase 9 review 中的实现建议已修复；其余 provider 无效锚点建议不改变代码结论，已记录为 `rejected_invalid`。
- **verify_handoff**：AC-02 当前结果为 `pass`；verify-code 需绑定当前快照的逐 AC 证据和反向需求回放。研究 receipt SHA 不匹配、R*/F*/D*/INC-001..015 无稳定来源 ID 的部分保持 `unknown/incomplete`，不能借绿测试伪造完成。
- **boundary**：不写 Home、Reader Package、主题正文、CompanyBrain、released；不提交、不推送、不 close。

#### Historical T14：严格重复运行、托管冲突与保留词降级边界

- [x] **任务完成**
- **status**：`completed`
- **covered_ac**：AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-12, AC-13
- **evidence_refs**：`[{"ref":"quality/evidence/implementation/b080c8d15a87df6afeeee026964e76fed2a8f403.json","sha256":"e761b9e81d33b0435fd50145b1cfd6afddc5047fb459ed9e2c893587f78568c9"},{"ref":"quality/tests/build-code-task1-full-phase8-post-t14-r5.json","sha256":"37738a322cbcd4a5f99025bebe955b1e0b002c8799b7e19720b0aea75da90daa"}]`；focused `38 passed`，full `380 passed, 2 skipped`。
- **actual_changes**：补齐真实入口 override manifest；重复运行复用上一轮 inventory/plan；托管内容哈希排除自引用 frontmatter；保留词转义碰撞 fail-closed 为 degraded；清理死路径和无效参数。
- **phase_id**：`phase-8-final-repairs`
- **review_fact**：Phase 8 review `pass`；minor packet 建议按上方 disposition 记录，不阻塞阶段完成。
- **risk_and_handoff**：真实语料生成的 4 个 product candidate、89 个 module candidate 仍不是 canonical ProductGazetteer；正式产品/模块/alias/object-intent/source_refs 需要产品维护者确认后，才能完成 AC-02 的最终语义证据。未知语义和无法形成唯一 ASCII degraded key 时继续保守失败，不自动猜测或合并。
- **最终复审建议处置**：`F-7d3573d71844` 已修复：旧路径与当前路径相同时不再写自指 `rename`，并更新 batch/repeat 回归断言；`F-5558a1ce536c` 已修复：examples 只收录真实 inventory 中自然出现的 unknown，不再制造伪来源，缺失的 unknown 只在测试中验证降级；`F-2507fa1ac429` 记为 `accepted_risk`：WorkflowHub 禁止把具体锚点落在 changed hunk 内，当前 Phase packet 只能以完整 diff 为实现权威，具体 AC 行区间仍保留在本任务完成记录中。

### build-code final integration review：completed 2026-08-05

- 当前整条 build-code integration review：`quality/reviews/results/build-code-default-d5e9f98d64347406f79719b7c404b2df4a9f75cd-6f7de0e6-cd18-42eb-91e4-66e40f37b91d.json`，SHA-256 `ee3d77d20828f209a6c84baf4e2367e65328d9ffd6e9b01cd51358557e6c76ae`，正式 verdict `pass`，findings 为空。
- integration 使用当前实现收据、当前 full GREEN 收据、当前四份 WorkflowHub 材料和 AC trace；历史 Phase 链仍按 current-snapshot-only 如实标记，未伪造历史 receipt。
- 交付结论：KnowledgeDigest 已从真实原始语料自身生成 candidate ProductGazetteer，不依赖 CompanyBrain；仍不宣称真实 canonical 词表确认、语义发布或 `released`。

### Scope revision handoff：knowledge_type 优先

- 用户已纠正：顶层目录必须是知识类型，`Products` 只是其中一类；CompanyBrain 的 `Customers`、`Engineering`、`Operations`、`Principles`、`ProductBoundaries` 与 `Products` 平级。
- 当前旧实现的 `product → module → object/intent` 轴缺少 `knowledge_type`，所以旧 Phase/verify 证据不再覆盖修正版合同。
- 下一轮 build-plan 必须重拆：知识类型 registry、Products 类型 ProductGazetteer、非产品类型的 subject/module 安全降级、v2 key/path、旧映射和 affected set。
- 当前 89 条原始语料属于产品资料，运行时应记录 `knowledge_type=products`；不读取 CompanyBrain 作为运行上游，也不凭空生成其他类型的完整词典。

---

# 当前任务清单：知识类型优先的 Task1 主题轴

> 本清单只执行当前 `spec.md` 和 `plan.md`；上方内容是 product-only 历史审计记录，不是当前授权。

- **Input**：`specs/task1-knowledge-publication-topic-axis/spec.md`、`specs/task1-knowledge-publication-topic-axis/plan.md`
- **Status**：已确认，T21–T29 已完成；当前进入 verify-code 结果交接，未授权 close
- **Template version**：`plan-task.v3`

## 1. 执行摘要

- **Goal**：实现 knowledge_type-first 的 registry、Products-only ProductGazetteer、`topic_key_v2`、TopicPlan、TopicIndex、affected set 和真实目录隔离验收。
- **Boundary**：不复制 CompanyBrain，不伪造非产品词表，不写 Home/正文，不提交或 close。
- **First executable task**：T21；先 RED，再 GREEN。

## 2. Global Constraints

- 每个行为任务必须有同一 `gate_cmd` 的 RED/GREEN 配对；RED 退出码非 0，GREEN 退出码 0。
- 当前 89 条真实语料只登记 `knowledge_type=products`；非 Products 在本 Task1 一律 degraded。
- 旧 `topic_key_v1`、旧 `digest_topic_id`、旧路径和人工内容不能被静默删除或覆盖。
- 只允许修改当前 phase 的精确文件；不执行 Git reset、清理或真实语料原地写回。
- `tasks.md` 是执行状态唯一权威；历史 receipt/review 不自动完成当前任务。

## Phase 1：类型 registry、结构 inventory 和 schema

### Goal

把知识类型放在第一层，并证明当前输入只生成有证据的 `products`；同时冻结四个审计投影的字段合同。

### Files

- **MODIFY**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`

### Tasks

- T21 RED：registry、inventory、schema、Products-only 初始边界的失败测试。
- T22 GREEN：最小实现和固定 89 条结构验收。

### Verify

`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "knowledge_type or inventory or schema or topic_index" -q`

### Knowledge

`kb.structure.md` 是唯一 registry/Gazetteer 权威；CompanyBrain 只提供信息架构参考事实。

### STOP

若实现需要硬编码 Customers/Engineering 等非产品词表、复制 CompanyBrain，或测试只能靠 provider 才能通过，停止并回到规格边界。

### Done

T21/T22 的 RED/GREEN 结果、89 条 inventory 数量、registry 来源证据和 schema 证据均写入 `quality/evidence/task1/phase-1/`。

### Risks and rollback

风险是把“存在于 CompanyBrain”误当成“当前语料已证明”；回滚只撤回 Phase 1 当前文件，保留历史审计。

#### T21 RED — 类型 registry 和 inventory 合同

- **ID**：T21
- **Phase**：Phase 1：类型 registry、结构 inventory 和 schema
- **goal**：复现非产品类型被硬编码、89 条结构证据缺失和 schema 允许未知字段伪装成功。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：当前 `spec.md` FR-01/FR-02/FR-12、真实来源目录和现有 Task1 acceptance。
- **依赖**：无 — first task
- **并行**：否 — T22 依赖本 RED。
- **FR**：FR-01、FR-02、FR-10、FR-12
- **AC**：AC-01、AC-02、AC-10、AC-12、AC-13
- **动作**：只新增或调整测试 fixture，断言类型第一层、Products-only 初始 registry、89 条结构 inventory、字段/排序/证据缺失必须失败。
- **精确文件**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`
- **boundary**：files: `src/knowledge_digest/ingest.py`, `src/knowledge_digest/kb_structure.py`, `src/knowledge_digest/topic_axis.py`, `tests/acceptance/test_task1_topic_axis.py`, `tests/fixtures/task1_topic_axis_89/`; RED 只改测试和 fixture。
- **输出**：真实 RED，命中 OR-TYPE-FIRST。
- **Knowledge**：CompanyBrain 的平级目录不是当前 registry 的证据；真实语料只证明 products。
- **verification_role**：RED
- **paired_task**：T22
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "knowledge_type or inventory or schema or topic_index" -q'`
- **expected_exit**：1
- **oracle**：OR-TYPE-FIRST — 非产品硬编码、缺 knowledge_type、89 条不完整、缺 source_refs/排序/行定位却通过即失败。
- **evidence_path**：`quality/evidence/task1/phase-1/t21-red.json`
- **STOP**：若 RED 只能通过修改真实 KB、调用 provider 或删除旧测试构造，停止。
- **recovery**：撤回测试 fixture 变更，保留最小失败用例。
- **task risk**：旧 product-only 测试可能误报 green。

#### T22 GREEN — 类型 registry、inventory 和 schema

- **ID**：T22
- **Phase**：Phase 1：类型 registry、结构 inventory 和 schema
- **goal**：实现可追溯的 knowledge_type-first registry/inventory 和四个投影的最小 schema。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：T21 RED。
- **依赖**：T21
- **并行**：否 — 共享 registry/inventory 文件。
- **FR**：FR-01、FR-02、FR-10、FR-12
- **AC**：AC-01、AC-02、AC-10、AC-12、AC-13
- **动作**：实现只从当前输入或受控声明登记类型；89 条产品来源显式写 `knowledge_type=products`；schema、证据、排序、JSON null 和审计路径按 spec 固定。
- **精确文件**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`
- **boundary**：files: `src/knowledge_digest/ingest.py`, `src/knowledge_digest/kb_structure.py`, `src/knowledge_digest/topic_axis.py`, `tests/acceptance/test_task1_topic_axis.py`, `tests/fixtures/task1_topic_axis_89/`; 不改 ProductGazetteer 匹配和路径算法。
- **输出**：GREEN，89/89 inventory，Products-only registry，schema round-trip。
- **Knowledge**：不把 CompanyBrain 内容写入运行时词表；未知类型保留证据并安全降级。
- **verification_role**：GREEN
- **paired_task**：T21
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "knowledge_type or inventory or schema or topic_index" -q'`
- **expected_exit**：0
- **oracle**：OR-TYPE-FIRST — 89 条均有类型、URI、指纹和结构证据；无证据的非产品类型不生成 canonical。
- **evidence_path**：`quality/evidence/task1/phase-1/t22-green.json`
- **STOP**：若需要预置完整非产品 ontology、第二权威词表或删除旧 schema，停止。
- **recovery**：撤回 registry/inventory 接线，保留 T21 RED。
- **task risk**：schema 迁移漏掉旧 `digest_topic_id`。

##### T21/T22 completion — 2026-08-05

- **status**：completed; T21 RED reproduced the type-first failures, then T22 GREEN repaired them.
- **actual_changes**：`topic_axis.py` now requires explicit `knowledge_type` in source declarations, builds a source-derived `KnowledgeTypeRegistry`, persists its controlled section in `kb.structure.md`, skips ProductGazetteer validation/matching for non-Products input, and projects the type into TopicPlan. `kb_structure.py` now requires `knowledge_type` in current TopicIndex rows and migrates legacy rows as `unknown`. The 89-source fixture declarations now explicitly carry `knowledge_type=products`.
- **evidence_refs**：`quality/evidence/task1/phase-1/t21-red.json`; `quality/evidence/task1/phase-1/t22-green.json`
- **focused_tests**：T21 RED `exit_code=1` with `3 failed, 10 passed, 29 deselected`; T22 GREEN focused `14 passed, 29 deselected`; Task1 regression `43 passed`; `py_compile` and `git diff --check` passed.
- **covered_ac**：AC-01, AC-02, AC-10, AC-12, AC-13
- **review_fact**：official `wh-review` result `quality/reviews/results/build-code-default-3f2e68cb1f82cd3dfc0dd84c84b000308996094f-e841a4c2-038f-4a1a-99ad-a89907fcaae2.json`, SHA-256 `cb7463b3c2e45c05feab8d51f8ebd68c4aff583766e9abf5daa00114669b1f5f`; snapshot `3f2e68cb1f82cd3dfc0dd84c84b000308996094f`; official verdict `pass` with one valid provider. `cursor/grok` independently exited nonzero; it is retained as provider evidence and not counted as a pass.
- **finding_dispositions**：`F-41ca30ff0ae4` → `rejected_invalid`: the provider evidence anchor was adjudicated `invalid_anchor`, and the requested `topic_key_v2`/path work is explicitly T23/T24 Phase 2 scope; T22 boundary says not to change ProductGazetteer matching or path algorithms. `F-a8a0ab3cbd39` → `accepted_risk`: the example-set unknown-category guarantee is a real deferred concern, handed to T24/T28; it is outside T21/T22 and does not change this Phase 1 implementation.
- **unresolved_risk**：the current source declaration is strict, but old hand-built in-memory Products test callers retain a compatibility default; the next Products/v2 phase must remove or explicitly constrain that compatibility boundary.

## Phase 2：Products 词表、v2 身份和 TopicPlan/Index

### Goal

让 ProductGazetteer 只处理 Products，并让 knowledge_type 进入新 key/path/TopicPlan/TopicIndex。

### Files

- **MODIFY**：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`src/knowledge_digest/identity.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task1_topic_axis.py`

### Tasks

- T23 RED：Products-only 匹配、canonical 门禁、v2 key/path、TopicPlan/Index 的失败测试。
- T24 GREEN：实现匹配、稳定身份、计划、索引和旧映射。

### Verify

`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "gazetteer or canonical_gate or identity or topic_plan or topic_index or path" -q`

### Knowledge

只有 canonical ProductGazetteer entry 能进入 Products published 轴；非 Products 不读取该词表。

### STOP

若新实现沿用 product-only 根路径、把非产品 subject 填成产品，或用 hash/输入序号补洞，停止。

### Done

T23/T24 证明 `topic_key_v2`、canonical-only、degraded null 和 old_path_mapping。

### Risks and rollback

风险是旧 v1 身份被原地改写；回滚只撤回 Phase 2 实现并保留旧映射。

#### T23 RED — Products 词表与 v2 主题身份

- **ID**：T23
- **Phase**：Phase 2：Products 词表、v2 身份和 TopicPlan/Index
- **goal**：复现非 Products 读取 ProductGazetteer、candidate 自动发布、v1/v2 混用和路径碰撞被吞掉。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：T22 GREEN、spec §6.5–§6.6、旧 TopicIndex fixture。
- **依赖**：T22
- **并行**：否 — 共享 identity/topic_axis。
- **FR**：FR-02、FR-03、FR-04、FR-05、FR-06
- **AC**：AC-02、AC-03、AC-04、AC-05、AC-06
- **动作**：新增失败断言：候选不能发布、非 Products 不绑定产品、`topic_key_v2` 必须带类型、旧 v1 只能映射；旧 schema/version migration、round-trip、缺字段 fail-loud、provider 失败/改名/重组后计划身份不变，以及路径碰撞必须 fail-closed。
- **精确文件**：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`src/knowledge_digest/identity.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task1_topic_axis.py`
- **boundary**：files: `src/knowledge_digest/kb_structure.py`, `src/knowledge_digest/topic_axis.py`, `src/knowledge_digest/identity.py`, `src/knowledge_digest/page_layout.py`, `tests/acceptance/test_task1_topic_axis.py`; RED 只增加行为断言。
- **输出**：真实 RED，命中 OR-PRODUCTS-NESTED。
- **Knowledge**：ProductGazetteer 是 Products 子轴，不是全库根轴。
- **verification_role**：RED
- **paired_task**：T24
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "gazetteer or canonical_gate or identity or topic_plan or topic_index or path or old_schema or migration or old_path_mapping or provider_boundary or provider_failure" -q'`
- **expected_exit**：1
- **oracle**：OR-PRODUCTS-NESTED — 非产品伪造 product、candidate published、旧 schema 丢字段、provider 改变计划、v1 原地变化或碰撞静默成功即失败。
- **evidence_path**：`quality/evidence/task1/phase-2/t23-red.json`
- **STOP**：若必须依赖 CompanyBrain 词表或 provider 才能判断身份，停止。
- **recovery**：保留旧 identity 和失败测试，不写回真实 KB。
- **task risk**：旧实现的 product-only 测试会掩盖缺少 knowledge_type。

#### T24 GREEN — Products 词表、v2 key/path、TopicPlan/Index

- **ID**：T24
- **Phase**：Phase 2：Products 词表、v2 身份和 TopicPlan/Index
- **goal**：完成 Products-only matcher、`topic_key_v2`、TopicPlan、TopicIndex 和旧路径映射。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：T23 RED。
- **依赖**：T23
- **并行**：否 — 共享同一计划和索引实现。
- **FR**：FR-02、FR-03、FR-04、FR-05、FR-06
- **AC**：AC-02、AC-03、AC-04、AC-05、AC-06
- **动作**：实现 canonical→alias→parent_path→h1_title→candidate 顺序；Products 嵌套 product/module；生成 v2 key/path；按 schema/version 双读迁移旧 `_digest/topic-index.json`，保留 digest_topic_id、旧 path 和 rename/merge/split/unmappable evidence；模拟 provider failure/rename/regroup 仍保持冻结计划身份；degraded 轴字段/path 为 JSON null。
- **精确文件**：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`src/knowledge_digest/identity.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task1_topic_axis.py`
- **boundary**：files: `src/knowledge_digest/kb_structure.py`, `src/knowledge_digest/topic_axis.py`, `src/knowledge_digest/identity.py`, `src/knowledge_digest/page_layout.py`, `tests/acceptance/test_task1_topic_axis.py`; 不写 Home、正文或 CompanyBrain。
- **输出**：GREEN，TopicPlan 在 provider 前冻结，TopicIndex 与旧映射可重建。
- **Knowledge**：类型未知/非 canonical/冲突时降级而非造词。
- **verification_role**：GREEN
- **paired_task**：T23
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "gazetteer or canonical_gate or identity or topic_plan or topic_index or path or old_schema or migration or old_path_mapping or provider_boundary or provider_failure" -q'`
- **expected_exit**：0
- **oracle**：OR-PRODUCTS-NESTED — Products 可进入 v2 published；非 Products 不读 ProductGazetteer；旧 schema round-trip、缺字段 fail-loud、provider 不能改变冻结计划，旧映射保留。
- **evidence_path**：`quality/evidence/task1/phase-2/t24-green.json`
- **STOP**：若路径碰撞用 hash 后缀掩盖或旧页面被删除，停止。
- **recovery**：撤回 v2 接线，保留旧 mapping 和 T23 RED。
- **task risk**：迁移映射可能一对多，必须带 evidence_refs。

##### T23/T24 completion — 2026-08-05

- **delivered**：Products-only ProductGazetteer matching；非 Products 不读取该词表并使用 JSON `null` 降级；新增 `topic_key_v2` 和 `pages/topics/<knowledge-type>/<product>/<module>/<object-intent>.md` 路径；保留 `topic_key_v1`/旧路径映射；路径碰撞以 `PUBLISHED_PATH_COLLISION` fail-closed；样例稳定包含 merge/unknown/conflict；89 条 fixture 覆盖 Atlas/Checkout/billing 与 Beacon/Reports/export；删除 `identity.py` 中无调用方的重复 wrapper。
- **RED**：`quality/evidence/task1/phase-2/t23-red.json`，`topic_key_v2` 未实现时 ImportError，退出码 1。
- **GREEN**：`quality/evidence/task1/phase-2/t24-green.json`；17 条 Phase 2 聚焦测试、44 条 Task1 专用测试通过；`py_compile` 和 `git diff --check` 通过。当前 canonical receipt：`quality/tests/build-code-task1-phase2-green-v2.json`，sha256 `f7f26d88228aad108f0920fbbe2771fbad10038bc09f1f024d542c5ea28b89a5`，snapshot tree `393c5caa31c2df9e2fc4c0054ff01700d0a64807`。
- **covered**：FR-02–FR-06；AC-02–AC-06。
- **review_fact**：正式 Phase review result `quality/reviews/results/build-code-default-393c5caa31c2df9e2fc4c0054ff01700d0a64807-f5075d0f-7a28-45da-bb1b-a80f94d79ca0.json`，sha256 `7a7a19188a2a8a8fa79cfea9182bea30c2e58f67931a3f766d1c9c9a66604911`，official aggregate verdict `pass`；`pi/coding` 已返回，`cursor/grok` 进程非零退出，不能计作第二个通过 provider。此前一次材料预检 unavailable 已因补齐 `change_ids` 修正，不作为代码失败。
- **finding_dispositions**：`F-5fffa1a8534b` fixed（补 unknown example）；`F-d1d26a67cef2` fixed（89-source fixture 增加第二产品轴）；`F-ea8703304f88` fixed（删除未使用 identity wrapper）；最终 `F-3f5e72eb375d` rejected_invalid（provider 建议使用 `bundle/diff-shards` 不是合法 snapshot anchor；改动文件的 diff hunk 也不能按当前材料合同重复作为 context，完整 diff 才是实现权威）；`F-8151cecae645` accepted_risk（impact map 诚实保留 unknown，后续 integration review 再补消费者关系）；`F-a00446ffc019` accepted_risk（实现已复用 `ValidationError`、`source_id`、`DigestPaths` 和既有 JSON/JSONL 约定，reuse map 的细分说明延期到 integration packet）。
- **unresolved_risk**：本阶段正式 review 的 aggregate pass 依赖 1 个有效 provider；当前 review material 的 implementation anchor 仍受完整 diff/changed-file anchor 规则限制，已保留为质量事实，不影响代码功能判断。Phase 3 继续处理确定性、affected set 和托管冲突；Phase 4 再处理真实 corpus 输出与交付证据。

## Phase 3：确定性、affected set 和托管冲突

### Goal

证明批次/顺序/重复不改变身份，并让增量范围和人工编辑保护可审计。

### Files

- **MODIFY**：`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`

### Tasks

- T25 RED：确定性、rebuild、affected set、managed hash 和离线隔离失败测试。
- T26 GREEN：实现矩阵、范围计算、冲突保护和 provider 隔离。

### Verify

`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "batch_invariance or affected_set or rebuild or managed_conflict or override or offline" -q`

### Knowledge

首次/rebuild 是全量 affected set；无变化增量为空；集合外页面字节不变；provider 不能回写计划。

### STOP

若测试直接改旧 reader 页面、`--no-llm` 触碰网络或失败时覆盖人工文件，停止。

### Done

T25/T26 证据包含 batch-1/batch-20/reordered/repeated、rebuild、冲突前后 hash 和零网络观测。

### Risks and rollback

风险是把批处理差异误当主题差异；回滚时保留旧审计文件和人工内容。

#### T25 RED — 确定性、范围和保护

- **ID**：T25
- **Phase**：Phase 3：确定性、affected set 和托管冲突
- **goal**：复现 batch/order/repeat 漂移、rebuild 不全、集合外字节变化和人工覆盖。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：T24 GREEN、Task1 离线 fixture 和隔离旧 KB。
- **依赖**：T24
- **并行**：否 — 共享 pipeline/writeback。
- **FR**：FR-07、FR-08、FR-09、FR-11
- **AC**：AC-07、AC-08、AC-09、AC-11
- **动作**：新增确定性矩阵、首次/rebuild/无变化 affected set、managed hash conflict/override，以及 `--no-llm` + Jaccard、无 LLM/embedding probe、socket 零调用断言。
- **精确文件**：`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`
- **boundary**：files: `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/writeback.py`, `src/knowledge_digest/topic_axis.py`, `tests/acceptance/test_task1_topic_axis.py`; 旧 KB 只使用隔离副本。
- **输出**：真实 RED，命中 OR-BOUNDARY-PROTECTION。
- **Knowledge**：Task1 只写 `_digest` 审计投影，不写 Home/正文。
- **verification_role**：RED
- **paired_task**：T26
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "batch_invariance or affected_set or rebuild or managed_conflict or override or offline" -q'`
- **expected_exit**：1
- **oracle**：OR-BOUNDARY-PROTECTION — 计划随 batch/order 变化、rebuild 漏来源、范围外字节变化、人工内容被覆盖、`--no-llm` 未使用 Jaccard/触碰 embedding 或出现网络请求即失败。
- **evidence_path**：`quality/evidence/task1/phase-3/t25-red.json`
- **STOP**：若只能靠删除旧页面或禁用冲突测试构造 RED，停止。
- **recovery**：删除临时隔离 KB，不碰真实基线。
- **task risk**：环境 provider 配置可能让离线测试误触网络。

#### T26 GREEN — 确定性、affected set 和保护

- **ID**：T26
- **Phase**：Phase 3：确定性、affected set 和托管冲突
- **goal**：实现稳定矩阵、affected set、fail-closed 冲突和 provider/离线隔离。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：T25 RED。
- **依赖**：T25
- **并行**：否 — 共享 pipeline/writeback 和测试。
- **FR**：FR-07、FR-08、FR-09、FR-11
- **AC**：AC-07、AC-08、AC-09、AC-11
- **动作**：固定排序和 grouping；首次/rebuild 全量、无变化为空；冲突保留人工文件；override 逐页审计；`--no-llm` 强制 Jaccard，不探测 LLM/embedding，并保留零网络证据。
- **精确文件**：`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`
- **boundary**：files: `src/knowledge_digest/batch_run.py`, `src/knowledge_digest/pipeline.py`, `src/knowledge_digest/writeback.py`, `src/knowledge_digest/topic_axis.py`, `tests/acceptance/test_task1_topic_axis.py`; 不写 reader 页面。
- **输出**：GREEN，四种输入矩阵相同，affected set 和冲突审计可重建。
- **Knowledge**：provider unavailable 不能改变身份；人工 override 不是默认覆盖或批量审批。
- **verification_role**：GREEN
- **paired_task**：T25
- **gate_cmd**：`bash -lc 'uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "batch_invariance or affected_set or rebuild or managed_conflict or override or offline" -q'`
- **expected_exit**：0
- **oracle**：OR-BOUNDARY-PROTECTION — 集合外文件字节不变、人工文件保留、离线使用 Jaccard 且无 LLM/embedding probe、无网络、计划身份不变。
- **evidence_path**：`quality/evidence/task1/phase-3/t26-green.json`
- **STOP**：若需要新增调度器、数据库、向量库或人工队列，停止并回到 scope。
- **recovery**：撤回增量/writeback 接线，保留冲突证据。
- **task risk**：related-link 级联可能扩大集合，必须保留触发事实。

##### T25/T26 completion — 2026-08-05

- **status**：completed; T25 captured a real RED for an override manifest bound to the wrong manifest hash, then T26 GREEN repaired the binding and completed the recorded boundary checks.
- **actual_changes**：`topic_axis.py` now includes manifest-bound managed-content overrides, declared reader roots in the reserved-slug set, conflict-only `fact_conflict_free`, and production examples that do not include synthetic failure rows. The acceptance fixture keeps the synthetic failure matrix test-only. Existing batch, pipeline, and legacy identity boundaries remain protected.
- **evidence_refs**：`[{"ref":"quality/tests/build-code-task1-phase3-focused-v3.json","sha256":"cb79ec430a1e7286fd0d35faec4ffecd339ead658a9450df1eba5e615435bafd"},{"ref":"quality/reviews/results/build-code-default-c5e4c5fc0b8f94c55ea633cc5396cd2ca56f71c2-f8fe2137-68d7-460f-90ff-3994e69d2633.json","sha256":"a1c2455ee35d14a5e827e3d1eaeaa6c5ddfb40b885f1faacf11153660999f0d1"}]`
- **focused_tests**：Phase 3 exact command `11 passed, 34 deselected`; Task1 acceptance `45 passed`; `py_compile` and `git diff --check` passed. Current GREEN receipt binds snapshot tree `c5e4c5fc0b8f94c55ea633cc5396cd2ca56f71c2`.
- **covered_ac**：AC-07, AC-08, AC-09, AC-11.
- **review_fact**：official Phase review result above is `pass`; `pi/coding` completed with no blocking or major findings. `cursor/grok` exited nonzero and is retained as provider evidence, not counted as a valid pass.
- **finding_dispositions**：`F-2f23c761f3f3` → `fixed`：reserved slugs now include declared reader roots and a collision regression was added. `F-6080acbe4b2b` → `fixed`：missing object/intent is no longer misclassified as a fact conflict and is covered by a regression. `F-d69fe22dbf04` → `fixed`：production calls the example builder with `include_failure_matrix=False`; synthetic failure rows are test-only. `F-660ac7a62ffa` → `rejected_invalid`：the four current WorkflowHub materials predate build-code and remain required task authority; they are not implementation changes introduced by T25/T26. `F-3eddaa1f4a61` → `accepted_risk`：production explicitly disables the matrix; keeping the test-fixture default avoids duplicating the five failure constructors outside the acceptance test boundary. `F-b467cbfe66fd` → `accepted_risk`：the provider-visible complete diff is the implementation authority for the added module; changed-hunk anchors are forbidden by the current review material contract, so AC-09 retains an outside-diff legacy-boundary anchor.
- **unresolved_risk**：the review had one valid provider (`pi/coding`); `cursor/grok` remains unavailable by process exit. Formal acceptance still needs Phase 4 real-corpus output evidence and the final build-code/verify-code checks.

## Phase 4：真实目录隔离验收和交付准备

### Goal

在用户提供的原始目录上做隔离运行，确认四个审计产物、not_released 和读者写入边界；不宣称非产品完整语义发布。

### Files

- **MODIFY**：`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`、`AGENTS.md`

### Tasks

- T27 RED：真实目录、离线产物和 reader 字节边界的失败测试。
- T28 GREEN：真实目录隔离验收、文档同步和交付证据。

### Verify

`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -q`

### Knowledge

真实目录是 `/Users/Hugh/Downloads/confluence 原始数据`；产品 candidate 不等于 canonical；Task1 结果是 `not_released`。

### STOP

若要把真实页面写回基线、把 candidate 改成 canonical、或把测试结果写成 released，停止。

### Done

真实运行保存 89 条来源、四个 `_digest` 产物、失败/降级原因和读者文件字节 manifest；无 CompanyBrain 运行时依赖。

### Risks and rollback

风险是误把真实结构证据说成完整语义交付；回滚删除临时复制目录，不删除用户原始目录。

#### T27 RED — 真实目录和交付边界

- **ID**：T27
- **Phase**：Phase 4：真实目录隔离验收和交付准备
- **goal**：复现真实输入未隔离、产物缺失、reader 字节被改和 not_released 被误报。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：T26 GREEN、`/Users/Hugh/Downloads/confluence 原始数据`、临时 KB。
- **依赖**：T26
- **并行**：否 — 最终集成 oracle。
- **FR**：FR-01、FR-02、FR-03、FR-04、FR-05、FR-06、FR-07、FR-08、FR-09、FR-10、FR-11、FR-12
- **AC**：AC-01、AC-02、AC-03、AC-04、AC-05、AC-06、AC-07、AC-08、AC-09、AC-10、AC-11、AC-12、AC-13
- **动作**：新增真实目录隔离运行、89 条来源、四产物、12–20 个稳定排序 TopicPlan 样例、五项单来源布尔门（含全真样例和逐项失败样例）、not_released、无 CompanyBrain 读取和 reader manifest 断言；同时执行完整 acceptance 回归。
- **精确文件**：`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`、`AGENTS.md`、`src/knowledge_digest/topic_axis.py`
- **boundary**：files: `tests/acceptance/test_task1_topic_axis.py`, `tests/fixtures/task1_topic_axis_89/`, `AGENTS.md`; 真实原始目录只读，输出使用临时目录。
- **输出**：真实 RED，命中 OR-REAL-BOUNDARY。
- **Knowledge**：89 条结构证据不等于其他知识类型完整词表，也不等于 released。
- **verification_role**：RED
- **paired_task**：T28
- **gate_cmd**：`bash -lc 'export KNOWLEDGEDIGEST_TASK1_RAW_CORPUS="/Users/Hugh/Downloads/confluence 原始数据" && uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "examples or failure_matrix or single_source_predicates or real_corpus" -q && uv run --frozen pytest tests/acceptance -q'`
- **expected_exit**：1
- **oracle**：OR-REAL-BOUNDARY — 任一真实来源漏计、产物不完整、样例不在 12–20、缺全真/逐项失败单来源样例、CompanyBrain 被读取、reader 字节变化、全量回归失败或状态误报即失败。
- **evidence_path**：`quality/evidence/task1/phase-4/t27-red.json`
- **STOP**：若真实目录不可用，报告 `unavailable` 并停止，不能用 fixture 冒充；若测试要求写回真实原始目录或基线 KB，也停止。
- **recovery**：删除临时目录，保留失败 receipt 和原始数据。
- **task risk**：真实目录权限/格式可能暴露此前 fixture 未覆盖的结构。

#### T28 GREEN — 真实目录隔离验收和交付证据

- **ID**：T28
- **Phase**：Phase 4：真实目录隔离验收和交付准备
- **goal**：完成真实 89 条结构运行、四产物、not_released 和 reader 边界证据。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/task1-knowledge-publication-topic-axis/spec.md","hash":"2c8af7ebb40ece0d2503a47badaa01796511ba60b4def9294e28ac1a85263812","id":"CURRENT-SPEC"},{"artifact_kind":"plan","ref":"specs/task1-knowledge-publication-topic-axis/plan.md","hash":"69972462b4484424abe479449fddfe0437ec7df9c97cafe9b96277fa12b088ea","id":"CURRENT-PLAN"}]`
- **输入**：T27 RED。
- **依赖**：T27
- **并行**：否 — 交付前最后一个 GREEN。
- **FR**：FR-01、FR-02、FR-03、FR-04、FR-05、FR-06、FR-07、FR-08、FR-09、FR-10、FR-11、FR-12
- **AC**：AC-01、AC-02、AC-03、AC-04、AC-05、AC-06、AC-07、AC-08、AC-09、AC-10、AC-11、AC-12、AC-13
- **动作**：在隔离副本运行真实原始目录；保存 89 条 inventory、Products candidate/canonical 状态、12–20 个稳定排序样例、五项单来源全真/逐项失败矩阵、TopicPlan/Index/affected set、四产物 hash 和 `not_released`；执行完整 acceptance 回归；同步 AGENTS 仅在实际合同变化时修改。
- **精确文件**：`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`、`AGENTS.md`、`src/knowledge_digest/topic_axis.py`
- **boundary**：files: `tests/acceptance/test_task1_topic_axis.py`, `tests/fixtures/task1_topic_axis_89/`, `AGENTS.md`, `src/knowledge_digest/topic_axis.py`; 不提交、不推送、不写 Home/正文。
- **输出**：GREEN，真实运行可复现且交付状态诚实。
- **Knowledge**：本阶段不把 candidate 自动晋升 canonical；非 Products 未来扩展另起 scope revision。
- **verification_role**：GREEN
- **paired_task**：T27
- **gate_cmd**：`bash -lc 'export KNOWLEDGEDIGEST_TASK1_RAW_CORPUS="/Users/Hugh/Downloads/confluence 原始数据" && uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "examples or failure_matrix or single_source_predicates or real_corpus" -q && uv run --frozen pytest tests/acceptance -q'`
- **expected_exit**：0
- **oracle**：OR-REAL-BOUNDARY — 89/89 可回溯、12–20 个样例和五项单来源矩阵完整、四产物存在、完整 acceptance 为 0、读者文件字节不变、状态为 not_released。
- **evidence_path**：`quality/evidence/task1/phase-4/t28-green.json`
- **STOP**：若真实目录不可用报告 `unavailable`；若结果需要 CompanyBrain、真实 canonical 确认或正文发布才能成立，保留 unknown 并停止 close。
- **recovery**：保留真实 evidence，删除临时输出，不修改原始语料。
- **task risk**：AC-02 的 canonical 语义确认可能仍需产品维护者延期确认。

##### T27/T28 completion — 2026-08-05

- **status**：completed; T27 captured the expected RED before the temporary input was staged, and T28 completed the isolated real-corpus run after fixing the existing degraded-key collision exposed by the 89-file corpus.
- **actual_changes**：the acceptance test stages `/Users/Hugh/Downloads/confluence 原始数据` into a temporary `new_dir/items/products` tree with explicit `knowledge_type=products` declarations, runs against a temporary KB, asserts 89 sources and four `_digest` artifacts, checks candidate-only generated ProductGazetteer entries, `not_released`, no CompanyBrain runtime dependency, and byte-identical reader files. `topic_axis.py` now derives degraded keys from the declared child path with auditable `uXXXX` encoding for non-ASCII evidence, so distinct files under one parent do not collapse; exact duplicate evidence still fails with `DEGRADED_KEY_COLLISION`.
- **evidence_refs**：`[{"ref":"quality/tests/build-code-task1-phase4-focused-v12.json","sha256":"0c51c91fd204b2e379f49f17f846dc00976fff6c7a2686db609b746e6e2f316f"}]`
- **focused_tests**：Phase 4 exact command `3 passed, 43 deselected`; complete acceptance `388 passed, 2 skipped`; `python -m py_compile src/knowledge_digest/topic_axis.py` and `git diff --check` passed. T28's real-corpus test asserted 89 sources, 12–20 examples, the five-predicate matrix, four `_digest` files, `not_released`, no CompanyBrain read, and unchanged Home/existing reader bytes. The raw corpus is now supplied through `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS`, so the build-code packet is hermetic unless the external corpus is explicitly opted in.
- **covered_ac**：AC-01 through AC-13.
- **review_fact**：official Phase 4 `wh-review` returned `pass` on snapshot `7230105bd4c837bdba47a5d73eca39841f44e80f`; result `quality/reviews/results/build-code-default-7230105bd4c837bdba47a5d73eca39841f44e80f-2e340d1a-ce52-4815-9b3c-9b0bc6a63b29.json`, SHA-256 `cfcea0f9f8754ada8ade44d6db1b6556ff646ff50ade6e181e3273a94f5e8957`. `pi/coding` was valid with no findings; `cursor/grok` exited nonzero and is retained as provider evidence, not counted as a second pass.
- **finding_dispositions**：the real-corpus `DEGRADED_KEY_COLLISION` was a valid implementation defect within existing AC-04/AC-06 scope and was fixed with a focused regression; the API default for `include_failure_matrix` was changed to `False` after review and tests opt in explicitly. `F-96994c51f2b4` → `fixed`：production no longer defaults to test-only failure rows. `F-a05e5bf05753` → `rejected_invalid`：the request to force a normal-merge example from a candidate-only real corpus would fabricate canonical semantics and contradict the explicit Task1/non-goal boundary; the fixture covers normal/unknown/conflict scenarios, while production raw output remains truthful. `F-df0ff240a837` → `accepted_risk`：the provider requested changed-file implementation anchors, but the current build-code contract forbids context anchors overlapping changed hunks and declares the complete diff authoritative; the map names the concrete `topic_axis.py` functions and uses pre-existing consumer boundaries for allowed context. `F-13aa5c994268` → `fixed`：the five-check field now follows the spec name `topic_axis_explicit`. `F-25285df9746e` → `addressed`：the supported single-line frontmatter format and unsupported YAML forms are documented in `AGENTS.md`. `F-3503d3fbfd` → `accepted_risk`：implementation functions are named in the acceptance map, while changed-file anchors remain excluded by the build-code contract. `F-9c0781154a39` → `accepted_risk`：the host-only raw corpus is intentionally supplied by `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS` and is not committed; the fixture remains the hermetic regression path. No new user-visible scope, state, or acceptance criterion was added.
- **unresolved_risk**：the generated ProductGazetteer is candidate-only from the user-supplied product corpus; AC-02 canonical confirmation and any released semantic publication remain deferred. The 89 files do not establish vocabulary for non-Products knowledge types.

---

##### Verify-code completion — 2026-08-05

- **status**：verified with an explicit open exception; no close authorization implied.
- **snapshot**：`36cba892df422e9f07339a7e42ed80caff3d0f8c`.
- **complete_suite**：`quality/tests/verify-code-task1-full-v1.json`, SHA-256 `60d08f39a0bd26a1864b0e18a184cfc516039cc7d8ae5f6a6a64c54a69bc0fd9`; `388 passed, 2 skipped` with `KNOWLEDGEDIGEST_TASK1_RAW_CORPUS=/Users/Hugh/Downloads/confluence 原始数据`.
- **acceptance_evidence**：`evidence/task1-verify/aggregate-36cba892df422e9f07339a7e42ed80caff3d0f8c-v9.json`, SHA-256 `2900769131c1f12167043e2df9ea28b89f3f76906a72fceeff92b7ac9b177118`; AC-01、AC-03–AC-13 的当前结构/行为证据为 pass，AC-02 的真实 canonical ProductGazetteer 确认保持 `unknown`。
- **verification_receipt**：`quality/evidence/verification/cbefcdaa4a430ed7e01727276fd767e554bcc4595bab76c4be920c2fae037357.json`，SHA-256 `9a5d1f153cd95ba727e51ed754270ba8d600f92ec65bc29ccd60b05477060e01`；正式 receipt 明确记录 `acceptance_criteria=unknown`、`core_gaps=unknown`、`browser_qa=not_applicable` 和用户交接，不把绿测试当成无条件完成。
- **wh-review**：verify-code review result `quality/reviews/results/verify-code-default-36cba892df422e9f07339a7e42ed80caff3d0f8c-20382a59-5cd0-4d31-a253-5476ecb5aa2b.json`，SHA-256 `f148de6ae2a9fae0937e2afda054bf5533ca0e60babdb0cee9f9c66a21444d9e`，整体 `pass`。provider 提出的三条建议均为验证材料问题，已修正：`F-2050675bdbc3` → `fixed`（AC 行锚点）；`F-45b109cd3513` → `fixed`（操作者流程锚点）；`F-69174839f219` → `fixed`（AC-02 明确保持 unknown）。
- **research_boundary**：`quality/tests/research.json` 的当前 SHA-256 与任务记录要求不一致（actual `19cfa5ebf98c5351b824714422313659d1d8f0ca9603d7cc3e6f29ea457fac6c`，expected `422f4044bfc68952c8ca917057e6930e51f7825943b49a0727e1b2936457ffe0`），因此原始 PRD 中无法直接映射的 `R*/F*/D*/INC-001..015` 研究断言保持 `unknown/incomplete`，不伪造通过。
- **boundary**：browser QA 为 `not_applicable`（本 Task1 是确定性 CLI/runtime，未改用户页面）；Task1 仍为 `not_released`，不写 Home、正文或 CompanyBrain 上游依赖。
- **next_close_gate**：先由产品维护者确认真实 canonical `ProductGazetteer`（产品、模块、alias、object/intent、source_refs）；确认后重跑真实 TopicPlan 和 AC-02 verify 证据。完成该门槛前不正式 close。
