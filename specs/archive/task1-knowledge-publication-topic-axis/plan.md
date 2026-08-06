# 历史 product-only 计划（只读审计记录，非当前授权）

状态：scope revision 后暂停旧 build-code 计划；必须重新完成 `build-spec`/`build-plan` 的受影响材料修订。旧 Phase 证据只作历史事实。

## 1. 计划依据和交付边界

本计划原本只执行 product-only Task1；现在必须改为：先生成 `knowledge_type`，再在 `Products` 类型内使用 ProductGazetteer，之后生成 TopicPlan、TopicIndex、affected set 和冲突审计。

Task1 交付状态仍为 `not_released`。本计划不承诺 Home、分类导航、主题正文、Summary/Evidence/Provenance、完整 89 条语义发布、Task2/Task3 provider 内容或人工语义复核。

## 2. 设计原则

- 先复用现有 `identity.py`、`kb_structure.py`、`batch_run.py`、`page_layout.py`、`pipeline.py` 和 `writeback.py` 的职责；不新增数据库、服务层或并行权威文件。
- `kb.structure.md` 是知识类型 registry 和 Products 类型 ProductGazetteer 的唯一正式存储；四个 `_digest` JSON/JSONL 文件是可重建审计投影，不是 reader 入口。
- 顶层路径和身份先带 `knowledge_type`；产品不再是全库根轴。CompanyBrain 只作为信息架构参考，不作为运行时词表上游。
- TopicPlan 在 provider 之前冻结。provider 只消费计划，不能改身份、成员、词表或路径。
- 所有集合、数组、证据和输出按稳定 key/URI/行定位排序；冲突和不确定性 fail-closed 或明确 `degraded`。
- 先写能失败的行为测试，再写最小实现；固定结构 fixture 继续作为仓库回归样例，真实语料验收使用用户提供的原始目录生成隔离输入，不把 fixture 冒充生产语义验收，也不依赖 CompanyBrain。

## 3. 实施阶段和依赖

| 阶段 | 主要产出 | 依赖 | 完成检查 |
| --- | --- | --- | --- |
| P0 合同与 fixture | schema、89 条结构样例、失败样例 | 无 | schema/排序校验失败可见 |
| P1 inventory 与词表 | inventory、匹配事实、Gazetteer | P0 | 89 条和 canonical 门禁成立 |
| P2 计划与身份 | TopicPlan、key/path、TopicIndex | P1 | 合并/降级/路径不变性成立 |
| P3 增量与保护 | affected set、哈希冲突、持久化 | P2 | 范围外字节不变、冲突不覆盖 |
| P4 集成与交付证据 | pipeline 接线、样例、离线验收 | P3 | `--no-llm` 全套验收及回归 |

依赖是单向的 `P0 → P1 → P2 → P3 → P4`。P4 只补验证和文档，不反向改变产品范围；发现规格级变化必须回到 WorkflowHub 的受影响阶段。

## 4. 模块边界和数据/API 变化

### 4.1 现有模块的职责改造

- `ingest.py`：沿用来源快照、URI、指纹和清单校验；输出 inventory 所需的原始证据。
- `identity.py`：加入知识类型优先的纯函数式 slug、版本化 key、degraded key、声明路径和旧身份兼容映射；保留现有 `digest_topic_id`，不让旧 hash 路径成为新正式路径。
- `kb_structure.py`：解析和校验 `kb.structure.md` 的 KnowledgeTypeRegistry 与 Products 类型 ProductGazetteer 受控区段、声明 topic root、保留词和 `_digest` 审计根；改造 `validate_topic_index`/`TOPIC_INDEX_SCHEMA_VERSION` 以支持新 schema、degraded 的 JSON `null` 和旧 product-only 记录迁移；拒绝非法结构和路径碰撞。
- `batch_run.py`：固定来源清单、稳定排序、batch/order/repeat 比较和 TopicPlan 版本；不扩展成调度器。
- `page_layout.py`：复用已发布路径锁定和旧路径映射的边界；不实现正文分页或 Home。
- `pipeline.py`：把 inventory → Gazetteer match → TopicPlan → TopicIndex 放在 provider/正文生成之前，并输出 affected set 和运行指纹。
- `writeback.py`：沿用先归档、原子写入和 managed hash 检查；Task1 只写审计投影，不写 Home 或正文。

实施时新增了单一职责的 `topic_axis.py`：现有 `identity.py`、`kb_structure.py`、`pipeline.py` 分别承担旧身份、旧 TopicIndex 校验和完整读者发布；把 inventory、知识类型/词表匹配、计划和四产物写入直接塞进其中任一模块会混用旧/新权威并破坏增量兼容。该模块只做纯规则和审计投影，不提供远程 API、不保存第二份词表、不进入读者页面；本次必须先扩展知识类型边界，再恢复实现。

### 4.2 最小数据合同

实现 `SourceInventory`、ProductGazetteer entry、TopicPlan topic、TopicIndex topic、AffectedSet 和 ConflictRecord 的最小字段，严格遵守 spec §6.5–§6.10：

- ProductGazetteer 存在 `kind/canonical/aliases/object_intents/owner/source_refs/status/reason`，模型只能产生 `candidate`。
- TopicPlan/TopicIndex 的 `published` 轴字段来自 canonical entry；`degraded` 的正式轴字段和路径写 JSON `null`，不能省略或写空串。
- 正式路径只按声明 root + 三段 slug 构造；`PUBLISHED_PATH_COLLISION` 和 `DEGRADED_KEY_COLLISION` 在写前失败。
- 当前投影落在 `_digest/source-inventory.jsonl`、`_digest/topic-plan.json`、`_digest/topic-index.json` 和 `_digest/runs/<run_id>.json`，并互相记录内容指纹。

不新增远程 API，也不新增对外 CLI。内部可用 `topic_axis_plan(..., rebuild=True)` 表达显式重建；它只是实现层入口，不改变产品页面或用户流程。其他函数接口以已存在的 Python 数据和 JSON/JSONL 投影为边界；provider 接口只接收冻结 TopicPlan。

## 5. 任务执行顺序

具体任务见 `tasks.md`。关键顺序是：先锁字段和 fixture，再做匹配和身份，再做增量/写入，最后接入 pipeline 与全量验收。任何任务不得先依赖 provider 输出或读者页面。

## 6. 验证策略

- 单元/行为测试：使用 `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "schema or identity or gazetteer or plan or index or path or migration" -q`；实现前预期 RED（退出码 1），实现后预期 GREEN（退出码 0），证据分别写入 `artifacts/task1/t01-schema-migration.txt`、`t03-gazetteer.json`、`t04-identity.json`、`t05-topic-plan.json`、`t06-topic-index.json`。
- 确定性矩阵：使用 `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "batch_invariance" -q`；比较 `artifacts/task1/determinism/{batch-1,batch-20,reordered,repeated}.json` 的 TopicPlan、TopicIndex、成员、key、路径和旧映射字节。
- 增量矩阵：使用 `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "affected_set or rebuild" -q`；比较 `artifacts/task1/affected-set.json` 和集合外文件字节清单。
- 保护矩阵：使用 `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "managed_conflict or override" -q`；证据写入 `artifacts/task1/conflicts.json`。
- 离线回归：使用 `uv run --frozen digest tests/fixtures/task1_topic_axis/new_dir tests/fixtures/task1_topic_axis/kb_dir --config tests/fixtures/task1_topic_axis/offline.json --no-llm`，预期退出码 0；断言 `_digest/source-inventory.jsonl`、`_digest/topic-plan.json`、`_digest/topic-index.json`、`_digest/runs/<run_id>.json` 存在、互有指纹且不进 reader package。网络零调用由测试 monkeypatch `socket.socket.connect` 与 `socket.create_connection` 计数并断言为 0。证据写入 `artifacts/task1/offline-run.json`。
- 证据回溯：12–20 个稳定排序样例覆盖合并、未知和冲突，并能回到 URI、指纹和行定位；不把 fixture 说成真实 89 条完整语义发布。

## 7. 风险和处理

- 真实 89 条生产语料不在仓库：把结构字段和证据格式做成可替换 fixture，报告明确数据边界；不伪造全量语义结果。
- 旧 `topic-<hash>` 与新语义轴并存：保留 `digest_topic_id` 和旧页面/映射，所有新正式路径只由 TopicPlan 产生。
- `kb.structure.md` 受控区段增加合并冲突：schema/version/owner/source_refs 必须显式，非法或重复项直接失败。
- degraded 增多会降低正式导航覆盖：保留完整证据和原因，把后续人工补词表留作延期，不用模型自动晋升。
- 现有 `indexes/sources.md` 代码合同与旧文档表述不一致：本计划只消费当前代码合同，不在 Task1 擅自改写无关文档。

## 8. 独立审查和处置规则

build-plan 只做一次异源 `wh-review`，审查完整 `spec.md`、`plan.md`、`tasks.md` 和明确上下文。审查结果按实际 provider 可用性记录；建议作为质量输入处理，不把 `pass` 当作阶段门，也不重复审查未变化材料。

每条 finding 必须在本文件“审查处置”或对应任务中留下：事实、证据、处理方式（`fixed`、`rejected_invalid` 或 `accepted_risk`）和下一步。若建议改变产品范围、身份合同、接口、状态或阶段顺序，不在 build-plan 偷改，回到 WorkflowHub 的受影响阶段。

## 9. FR/AC 覆盖摘要

| 需求 | 主要任务 | 判断证据 |
| --- | --- | --- |
| FR-01/02 | T01–T03、T12 | inventory、词表 schema、匹配失败样例 |
| FR-03/04/05/06 | T03–T06、T10、T12 | key、provider 前计划、合并降级、path/index |
| FR-07/08 | T02、T05、T07–T08、T10、T12 | rebuild/不变性、affected set、范围外字节 |
| FR-09/10/11 | T03、T05、T07、T09–T12 | 冲突审计、五项布尔门、离线零请求 |
| FR-12 | T01–T02、T11–T12 | 12–20 样例、回归和交付报告 |

AC-01–AC-02 由 T01–T03 覆盖；AC-03–AC-06 由 T04–T06、T10 覆盖；AC-07–AC-09 由 T07–T10 覆盖；AC-10–AC-13 由 T01、T03、T05、T10–T12 覆盖。`tasks.md` 逐项列出反向映射和可执行检查。

FR↔AC 对照固定为：FR-01→AC-01/08/13；FR-02→AC-02；FR-03→AC-03/11；FR-04→AC-04；FR-05→AC-05/06/13；FR-06→AC-06/07；FR-07→AC-07；FR-08→AC-08/12/13；FR-09→AC-09；FR-10→AC-04/10；FR-11→AC-03/11；FR-12→AC-04/10/12。这样 AC-13 归属于产物落盘相关 FR，不再错误归到样例 FR-12。

## 10. 交付边界

本阶段只交付当前候选工作区中的 `plan.md`、`tasks.md` 及其 WorkflowHub 计划记录。未获用户确认前不进入 `build-code`，不改生产代码，不提交、不合并、不推送。用户确认计划后，下一阶段才按任务顺序实现并验证。

## 10.1 Scope revision handoff

- CompanyBrain 对照确认顶层目录是知识类型：`Products`、`Customers`、`Engineering`、`Operations`、`Principles`、`ProductBoundaries`。
- 旧 T01–T12 仍按 product-only 轴编排，不能直接继续执行；build-plan 必须把 `knowledge_type` registry、Products 嵌套 ProductGazetteer、非产品安全降级、v2 key/path 和旧映射拆成新的可验证任务。
- 当前 89 条原始语料是产品资料，真实运行的 `knowledge_type` 应固定为 `products`；这不证明其他知识类型已有完整语义词表。
- 旧代码和旧测试不得在新计划完成前宣称已覆盖修正版 AC；不做替代任务、不删除历史证据。

## 11. 审查处置

本次 build-plan 异源审查事实：

- attempt：`quality/reviews/attempts/e89fd646-8578-4ac1-a91f-fcc7fb0cf67f/attempt.json`
- result：`quality/reviews/results/build-plan-default-9fb66ff9e06748e7bf4e3699993c63de0a23bcc7-e89fd646-8578-4ac1-a91f-fcc7fb0cf67f.json`
- report：`quality/reviews/reports/e89fd646-8578-4ac1-a91f-fcc7fb0cf67f.md`
- 实际覆盖：3 个有效异源 provider；1 个同源 provider 被排除；verdict 为 `revise_required`。

建议已评估并修订：

- F-fdc18e754745、F-e71d30303883、F-2251ff252731、F-25cde3a978fc：已修正任务依赖，先做 key/path 再做 TopicPlan；每个任务补了明确 pytest 命令、RED/GREEN 退出码和证据路径；补了明确 `--no-llm` CLI 与四个产物断言。
- F-5ce8f1356334、F-160725add881、F-534587feee00：已把 `validate_topic_index`/版本升级、旧 `_digest/topic-index.json` 迁移、旧 `digest_topic_id` 保留和 degraded `null` 兼容明确放入 T01/T06/T10。
- F-6bb42142811b、F-9425cf2d5601：已把首次导入/显式 rebuild 全量 affected set 和 socket 零网络调用观测放入 T08/T10。
- F-266d76e34c95、F-d1146c1f65a0：已移除 T01 对 AC-03 的错误归属，并删除无触发条件的开放式新增模块出口。
- F-d7319f3c536a、F-e20b25e5705f：已按 `tasks.md` 反向索引统一 plan §9 的 FR/AC 归属，并补入 T07 的批次不变性归属。
- 修订后只读覆盖检查：FR/AC 出现、任务依赖、迁移、rebuild、零网络和证据路径均已复核；额外把 FR↔AC 对照、T12 只做最终 GREEN、T08 的 rebuild 入口和指纹变化 fail-closed 写入当前材料。

这些是同一 build-plan 任务内的普通修订；按用户规则不再为追求 `pass` 重跑相同审查。

---

# 当前实施计划：知识类型优先的 Task1 主题轴

- **Input**：`specs/task1-knowledge-publication-topic-axis/decision-log.md`、`specs/task1-knowledge-publication-topic-axis/spec.md`
- **Status**：Draft — scope revision 已收敛，等待用户确认后进入 build-code
- **Template version**：`plan-task.v3`

## 1. 速读卡

- **Goal**：先按 `knowledge_type` 建立顶层轴；当前 89 条产品语料进入 `products`，再生成 Products 专用 ProductGazetteer、TopicPlan、TopicIndex 和 affected set。
- **Non-goals**：不复制 CompanyBrain、不硬编码非产品词表、不写 Home/正文、不做完整 89 条语义发布；来源：`spec.md` §2、§10.2。
- **Before**：旧实现只有 product-only 轴，不能证明企业知识类型优先。
- **After**：类型先于产品；Products 才能使用产品词表；其他类型在本 Task1 安全降级。
- **Main risk**：把 CompanyBrain 目录事实误做运行时词表，或把旧 v1 key 原地改写。
- **Next step**：用户确认本计划后，从 T21 RED 开始；未确认前不改生产代码。

## 2. Technical Context and Constraints

- **Language / runtime**：Python `src-layout`、`uv run --frozen pytest`、离线 `digest` CLI。
- **Primary modules**：`ingest.py`、`kb_structure.py`、`topic_axis.py`、`identity.py`、`pipeline.py`、`writeback.py`。
- **Storage / state**：`kb.structure.md` 是 registry 和 Products ProductGazetteer 的唯一权威；四个 `_digest` 文件是审计投影。
- **Testing**：每个行为变化先 RED 再 GREEN；绿色检查必须是同一 oracle；正式验收不调用 provider。
- **Target data**：`/Users/Hugh/Downloads/confluence 原始数据`；本次 89 条来源只证明 `products`。
- **External reference**：CompanyBrain 只用于确认顶层信息架构，不是运行时上游。

### Global Constraints

- `knowledge_type` 是第一层；Products、Customers、Engineering、Operations、Principles、ProductBoundaries 是平级概念，不能把非产品知识塞进产品 facet。
- 本次只有有来源证据的类型才能进入 registry；实际 89 条语料初始只登记 `products`。
- `topic_key_v1` 旧规则和旧路径只保留映射；带知识类型的新规则命名为 `topic_key_v2`。
- provider 只能消费冻结 TopicPlan，不能改身份、成员、词表、路径或状态。
- 发现未知、冲突、非 canonical 或缺证据时必须 `degraded` 或明确失败；不猜、不自动晋升。
- 不删除历史页面、旧 ID、旧路径、用户手工内容或历史 WorkflowHub 记录。

## 3. Code Anchors

- `src/knowledge_digest/topic_axis.py`：当前来源 inventory、词表编译、TopicPlan、TopicIndex、affected set 的集中边界；本次先补知识类型，再保留 Products 规则。
- `src/knowledge_digest/kb_structure.py`：`kb.structure.md` 受控区段和 TopicIndex schema 校验。
- `src/knowledge_digest/identity.py`：稳定 topic identity、slug、旧 identity 兼容。
- `src/knowledge_digest/pipeline.py`：provider 前冻结计划和运行审计边界。
- `tests/acceptance/test_task1_topic_axis.py`：Task1 行为 oracle；真实目录只用于隔离验收，不写入 fixture。

## 4. Solution Design

输入先经过来源快照和结构 inventory。inventory 明确记录 `knowledge_type`；只有 `products` 才进入 ProductGazetteer 匹配。随后在 provider 前生成 TopicPlan，按 `topic_key_v2` 生成 TopicIndex 和 affected set。写回仍沿用现有 fail-closed 与 managed hash 保护，只落审计投影，不写 Home 或主题正文。

模块边界：`ingest.py` 负责来源事实；`kb_structure.py` 负责受控 registry/schema；`topic_axis.py` 负责纯规则、计划和投影；`identity.py` 负责 key/path；`pipeline.py` 负责顺序和冻结；`writeback.py` 负责原子审计写入和冲突保护。CompanyBrain 不进入任何运行时调用路径。

## 5. File Boundary

### NEW

- 无；本轮不增加新的权威文件或外部接口。

### MODIFY

- `src/knowledge_digest/ingest.py`
- `src/knowledge_digest/kb_structure.py`
- `src/knowledge_digest/topic_axis.py`
- `src/knowledge_digest/identity.py`
- `src/knowledge_digest/page_layout.py`
- `src/knowledge_digest/batch_run.py`
- `src/knowledge_digest/pipeline.py`
- `src/knowledge_digest/writeback.py`
- `tests/acceptance/test_task1_topic_axis.py`
- `tests/fixtures/task1_topic_axis_89/`
- `AGENTS.md`

### DO NOT TOUCH

- `specs/task1-knowledge-publication-topic-axis/decision-log.md`
- `specs/task1-knowledge-publication-topic-axis/spec.md`
- `docs/plans/knowledge-digest-knowledge-publication-prd.md`
- 真实原始语料目录、CompanyBrain、`.git/` 和既有 reader 页面。

## 6. Technical Decisions

### DEC-01：类型 registry 的初始内容

- **Problem**：CompanyBrain 有多个知识类型，但本次真实输入只有产品资料。
- **Options**：硬编码全套类型 / 只登记有证据的类型 / 把所有未知类型塞进 Products。
- **Selected**：只登记当前输入或受控结构声明有证据的类型；本次初始为 `products`。
- **Reason**：保持结构正确又不伪造词表；未来真实来源加入时可扩展。
- **Consequence / risk**：非产品输入本次只能安全降级，不能生成 published 类型内路径。
- **Fallback**：新类型来源到位后重新进入 scope revision，补对应类型内轴。

### DEC-02：新 key 版本

- **Problem**：旧 product-only key 没有知识类型前缀。
- **Options**：原地改 v1 / 另起 v2 / 保留 product-only 不变。
- **Selected**：旧 `topic_key_v1` 只读兼容，新知识类型合同使用 `topic_key_v2`。
- **Reason**：避免旧页面身份和路径被静默改写。
- **Consequence / risk**：需要维护 old key/path mapping。
- **Fallback**：映射缺证据时记录 `unmappable`，不猜路径。

### DEC-03：人工编辑冲突

- **Problem**：托管页被人工修改时不能静默覆盖。
- **Options**：直接覆盖 / 永久人工队列 / 默认 fail-closed，允许逐页显式恢复。
- **Selected**：默认 fail-closed；逐页 override 仅作为带原/现 hash、原因和操作者说明的显式恢复动作。
- **Reason**：保留数据安全边界，不新增人工审批队列或批量放行。
- **Consequence / risk**：操作者需要明确提供恢复事实。
- **Fallback**：没有 manifest 就停止覆盖并保留人工内容。

## 7. Data Model and Lifecycle

- `KnowledgeTypeRegistry`：canonical、aliases、owner、source_refs、status、reason；无证据类型不生成正式入口。
- `ProductGazetteer`：只服务 `products`，包含 kind、canonical、aliases、object_intents、owner、source_refs、status、reason；模型只能产生 candidate。
- `TopicPlan`：provider 前冻结，包含 knowledge_type、适用 Products 轴、成员、merge_mode、版本和证据。
- `TopicIndex`：一主题一记录，包含 `topic_key_v2`、旧映射、状态和原因；degraded 轴字段/path 使用 JSON `null`。
- `AffectedSet`：由来源、结构 link、registry/Gazetteer、计划、索引和旧映射触发；首次/rebuild 全量，普通无变化为空。

## 8. API Contract

不新增外部 HTTP API、数据库或服务。内部仍使用现有 Python 数据结构和 JSON/JSONL 审计投影；provider 接口只接收冻结 TopicPlan。CompanyBrain 不作为输入参数或运行时依赖。

## 9. Test Strategy

- T21/T22：schema、89 条 inventory、knowledge_type registry、Products-only 初始边界；RED 退出 1，GREEN 退出 0。
- T23/T24：ProductGazetteer canonical 门禁、`topic_key_v2`、路径、TopicPlan、TopicIndex、旧 schema/version migration 和旧映射；同时模拟 provider 失败/改名/重组。
- T25/T26：batch/order/repeat、首次/rebuild/增量 affected set、managed hash conflict、override，以及 `--no-llm` + Jaccard、无 embedding 探测和零网络。
- T27/T28：真实目录隔离运行、12–20 个样例、五项单来源门槛、四个 `_digest` 产物、`not_released` 和全量 acceptance 回归。
- 所有命令都使用 `uv run --frozen pytest`；真实目录只复制到临时 KB，禁止直接改基线产物。

## 10. Rollback and Recovery

- 任何 schema、路径、映射、托管哈希或写入范围不一致都停止；保留旧文件和人工文件，不做删除或 reset。
- 代码回滚只撤回当前 phase 的受限变更；不触碰历史 receipt、真实原始语料或 CompanyBrain。
### Engineering Risk Handoff

- **Affected IDs**：FR-01–FR-12、AC-01–AC-13。
- **Trigger**：非产品类型被硬编码、v1 被原地改写、provider 改变计划、或集合外字节变化。
- **Consequence**：错误目录层级、旧链接断裂、知识误归类或人工内容丢失。
- **Mitigation or STOP**：fail-closed；保留 evidence_refs；回到对应 phase 修复。
- **Handling Stage**：build-code 对应 phase；若改变 scope，回到 make-decision/build-spec。
- **Verification**：phase RED/GREEN、完整 acceptance、真实目录边界和独立 review。

## 11. Implementation Order

1. Phase 1：冻结 registry/schema/inventory，先验证“类型第一层、当前只 Products”。
2. Phase 2：实现 Products-only matcher、`topic_key_v2`、TopicPlan、TopicIndex。
3. Phase 3：实现确定性矩阵、affected set 和托管冲突保护。
4. Phase 4：真实目录隔离验收、审计产物和交付文档。

## 12. Dependencies and Parallelism

依赖为 Phase 1 → Phase 2 → Phase 3 → Phase 4；每个 phase 内 RED → GREEN 串行。不同 phase 不并行，因为会共同修改 `topic_axis.py`、`kb_structure.py` 和同一 acceptance 文件。

## 13. Requirement and Verification Traceability

| 需求 | 任务 | 验证重点 |
| --- | --- | --- |
| FR-01/02 | T21–T24 | inventory、registry、Products-only Gazetteer |
| FR-03/04/05/06 | T23–T24 | provider 前计划、v2 key/path、Index |
| FR-07/08/09 | T25–T26 | 不变性、affected set、冲突保护 |
| FR-10/11/12 | T21–T28 | 降级、离线隔离、样例和证据 |
| AC-01–AC-13 | T22、T24、T26、T28 | 四阶段 GREEN 和真实目录边界 |

## 14. Governance Synchronization Matrix

| Surface | Files | Change | Owner |
| --- | --- | --- | --- |
| Product implementation | `src/knowledge_digest/` | modify | build-code |
| Acceptance | `tests/acceptance/`、`tests/fixtures/` | modify | build-code |
| Project instructions | `AGENTS.md` | sync if contracts change | build-code |
| WorkflowHub evidence | task materials and runtime records | publish | WorkflowHub |

## 15. Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"CONSTITUTION.md","hash":"d17c85373e30c4733a77b19dc260373268fca6dd29b8ac3574c8a35b4da6ebd5","id":"CONSTITUTION","version":"1.5.0","clause_count":21}`
- **Framework**：F1、F2、F3、F4、F5、F6、F7、F8、F9、F10：全部遵守；不扩建平台、不新增 gate、不把 review 当完成许可。
- **Quality**：Q1、Q2、Q3：全部遵守；测试、review、delivery 和 close 分开记录。
- **Skill**：S1、S2、S3、S4、S5、S6、S7、S8：全部遵守；沿用当前 WorkflowHub v3 材料和阶段顺序。

## 16. Complexity Trade-offs

- 选择一个 `kb.structure.md` 中的 registry 区段和一个 Products Gazetteer 区段，避免第二权威文件；代价是结构文件冲突更集中。
- 只为真实有证据的类型生成 published，避免伪造全公司 ontology；代价是未来非产品输入先 degraded。
- 继续保留 override 恢复边界，避免人工内容永远无法恢复；代价是 manifest 校验必须严格逐页。

## Phase 1：类型 registry、结构 inventory 和 schema

### Goal

把知识类型放在第一层，并证明当前输入只生成有证据的 `products`；同时冻结四个审计投影的字段合同。

### Files

- **MODIFY**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`

### Tasks

- T21 RED：registry、inventory、schema、Products-only 初始边界失败测试。
- T22 GREEN：最小实现和固定 89 条结构验收。

### Verify

`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "knowledge_type or inventory or schema or topic_index" -q`

### Knowledge

`kb.structure.md` 是唯一 registry/Gazetteer 权威；CompanyBrain 只提供信息架构参考事实。

### STOP

若实现需要硬编码 Customers/Engineering 等非产品词表、复制 CompanyBrain，或测试只能靠 provider 才能通过，停止。

### Done

T21/T22 的 RED/GREEN 结果、89 条 inventory 数量、registry 来源证据和 schema 证据均写入 `quality/evidence/task1/phase-1/`。

### Risks and rollback

风险是把“存在于 CompanyBrain”误当成“当前语料已证明”；回滚只撤回 Phase 1 当前文件，保留历史审计。

## Phase 2：Products 词表、v2 身份和 TopicPlan/Index

### Goal

让 ProductGazetteer 只处理 Products，并让 knowledge_type 进入新 key/path/TopicPlan/TopicIndex。

### Files

- **MODIFY**：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/topic_axis.py`、`src/knowledge_digest/identity.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task1_topic_axis.py`

### Tasks

- T23 RED：Products-only 匹配、canonical 门禁、v2 key/path、旧 schema migration、provider failure invariance 和 TopicPlan/Index 失败测试。
- T24 GREEN：实现匹配、稳定身份、迁移、provider 前计划、索引和旧映射。

### Verify

`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "gazetteer or canonical_gate or identity or topic_plan or topic_index or path or old_schema or migration or old_path_mapping or provider_boundary or provider_failure" -q`

### Knowledge

只有 canonical ProductGazetteer entry 能进入 Products published 轴；非 Products 不读取该词表。

### STOP

若新实现沿用 product-only 根路径、把非产品 subject 填成产品，或用 hash/输入序号补洞，停止。

### Done

T23/T24 证明 `topic_key_v2`、canonical-only、旧 schema/version migration、degraded null 和 old_path_mapping。

### Risks and rollback

风险是旧 v1 身份被原地改写；回滚只撤回 Phase 2 实现并保留旧映射。

## Phase 3：确定性、affected set 和托管冲突

### Goal

证明批次/顺序/重复不改变身份，并让增量范围和人工编辑保护可审计。

### Files

- **MODIFY**：`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`

### Tasks

- T25 RED：确定性、rebuild、affected set、managed hash、Jaccard/no-embedding 和离线隔离失败测试。
- T26 GREEN：实现矩阵、范围计算、冲突保护和 provider/离线隔离。

### Verify

`uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "batch_invariance or affected_set or rebuild or managed_conflict or override or offline" -q`

### Knowledge

首次/rebuild 是全量 affected set；无变化增量为空；集合外页面字节不变；provider 不能回写计划。

### STOP

若测试直接改旧 reader 页面、`--no-llm` 触碰网络或失败时覆盖人工文件，停止。

### Done

T25/T26 证据包含 batch-1/batch-20/reordered/repeated、rebuild、冲突前后 hash、Jaccard/no-embedding 和零网络观测。

### Risks and rollback

风险是把批处理差异误当主题差异；回滚时保留旧审计文件和人工内容。

## Phase 4：真实目录隔离验收和交付准备

### Goal

在用户提供的原始目录上做隔离运行，确认四个审计产物、not_released 和读者写入边界；不宣称非产品完整语义发布。

### Files

- **MODIFY**：`tests/acceptance/test_task1_topic_axis.py`、`tests/fixtures/task1_topic_axis_89/`、`AGENTS.md`

### Tasks

- T27 RED：真实目录、12–20 样例、五项单来源矩阵、全量回归和 reader 字节边界失败测试。
- T28 GREEN：真实目录隔离验收、全量回归、文档同步和交付证据。

### Verify

`export KNOWLEDGEDIGEST_TASK1_RAW_CORPUS='/Users/Hugh/Downloads/confluence 原始数据' && uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k "examples or failure_matrix or single_source_predicates or real_corpus" -q && uv run --frozen pytest tests/acceptance -q`

### Knowledge

真实目录是 `/Users/Hugh/Downloads/confluence 原始数据`；产品 candidate 不等于 canonical；Task1 结果是 `not_released`。

### STOP

若要把真实页面写回基线、把 candidate 改成 canonical、或把测试结果写成 released，停止；真实目录不可用时报告 `unavailable`，不能拿 fixture 冒充真实语料验收。

### Done

真实运行保存 89 条来源、四个 `_digest` 产物、失败/降级原因和读者文件字节 manifest；无 CompanyBrain 运行时依赖。

### Risks and rollback

风险是误把真实结构证据说成完整语义交付；回滚删除临时复制目录，不删除用户原始目录。

## Current amendment: source-canonical ProductGazetteer — 2026-08-06

### Goal

用用户提供的 89 条原始语料确认可直接证明的 canonical ProductGazetteer：4 个产品根、89 个稳定 source page/capability module seed；模型候选仍不能晋升；object/intent 没有证据时保持空数组。

### Scope

- **MODIFY**：`src/knowledge_digest/topic_axis.py`、`tests/acceptance/test_task1_topic_axis.py`、本任务四份材料。
- **DO NOT MODIFY**：CompanyBrain、用户原始目录、Home、Reader Package、主题正文、`released` 状态。

### Checks

- `uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -q`
- `export KNOWLEDGEDIGEST_TASK1_RAW_CORPUS='/Users/Hugh/Downloads/confluence 原始数据' && uv run --frozen pytest tests/acceptance/test_task1_topic_axis.py -k 'source_canonical or generated_gazetteer or real_corpus' -q`
- `export KNOWLEDGEDIGEST_TASK1_RAW_CORPUS='/Users/Hugh/Downloads/confluence 原始数据' && uv run --frozen pytest tests/acceptance -q`
- `python -m py_compile src/knowledge_digest/topic_axis.py`、`git diff --check`

### Oracle

真实运行生成 89/89 source inventory、4 个 canonical product、89 个 canonical module，所有 entry 有 owner/source_refs/稳定排序；模型候选仍为 candidate；没有 CompanyBrain 读取；reader 文件字节不变；summary 仍为 `not_released`。

### Review and handoff

这是同任务 scope revision 的新增实现闭环。build-code 必须对本 amendment 作为新 phase 审查到 `pass`；随后 verify-code 重新判断 AC-02，并反向回放所有原始需求、流程、FR/AC、任务和证据。任何没有证据的语义扩展保持 `unknown`，不准用全量绿测试替代。

## 17. Independent Review and Handoff

build-plan 只进行一次完整异源 review。审查是建议输入，不要求 verdict 为 pass；每个 finding 必须在本材料或对应任务写明 fixed、rejected_invalid 或 accepted_risk。用户确认当前计划后才 handoff 到 build-code；未确认前不改生产代码、不提交、不合并、不推送、不 close。

### 本轮 review 事实和处置

- 当前结果：`quality/reviews/results/build-plan-default-78a6833f5b7c11de6ea3cd85cf55a3ea7dd14d4f-ced6f933-200f-4853-afdc-39a8d09c92a2.json`；实际有效 provider 为 `pi/k3`、`opencode/v4flash`；verdict=`revise_required`。按用户规则不追求 pass。
- `F-eddd14eb8145`、`F-69703cc805c0`：fixed。旧 product-only 计划/任务现在明确标为历史审计，当前 v3 计划从分隔线后的“当前实施计划/当前任务清单”开始；当前 coverage 只认 T21–T28。
- `F-42be5e1adb1b`、`F-f5f923dac557`：fixed。T27/T28 加入 12–20 样例、五项单来源矩阵、完整 `uv run --frozen pytest tests/acceptance -q`；真实目录不可用时报告 `unavailable`，不能用 fixture 冒充。
- `F-bfef43eab8c1`：fixed。T23/T24 加入旧 schema/version round-trip、缺字段 fail-loud、`old_schema/migration/old_path_mapping` 检查。
- `F-e86a25c0c262`：fixed。T25/T26 明确 `--no-llm` 使用 Jaccard，且不探测 LLM/embedding，保留零网络证据。
- 审查只给建议，不改变用户已确认的 scope；下一步是用户确认计划，之后才进入 build-code。

---
