# 实现计划：KnowledgeDigest Task2 知识发布架构

> 基于当前 `spec.md` 与 `decision-log.md`；不重新选择产品方向。

- **Input**：`specs/knowledge-digest-llm-naming-classification/spec.md`（SHA-256 `f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42`）、`decision-log.md`
- **Status**：Draft
- **Template version**：`plan-task.v3`

## 1. 速读卡

- **Goal**：在不重写 S1–S6 的前提下，把生成结果发布成有语义标题、受控父/叶分类、Home/分类/主题/来源索引和可离线阅读的知识库。
- **Non-goals**：数据库、向量库、CAS、journal、调度器、在线聊天、AgentMemory、权限系统、S1–S6 重写、旧 Task1 KB 的原地 taxonomy 迁移；来源：spec §7 与 SCOPE-002。
- **Before**：现有 `page_layout.py` 有 300 行分页和 stable topic ID，但页面仍可能落在 `pages/digest`/pending，`draft.py` 的 generator 合同没有 publication metadata，`kb_structure.py` 只有扁平 category，source-index 不在同一写回事务。
- **After**：新空 KB 初始化完整 taxonomy；语义建议复用既有 generator response，经过字段级 Claim/Evidence 校验后发布；父分类索引聚合叶分类，Products 叶分类按 `product_slug` 分组；首次路径写入 topic-index 后锁定；source-index 与 Home/主题同批归档后原子发布；失败只影响当前来源/批次。
- **Main risk**：现有 PublicationContract、topic identity、generator 请求、批次 state 和 source-index 写回边界不一致，可能再次形成 pending 巨页、重复 Claim、路径漂移或孤儿导航。
- **Next step**：先执行 T001 RED，固定 taxonomy、semantic metadata、topic-index 和 source-index 的失败合同；若 RED 不能由目标缺口触发，立即 STOP。

## 2. Technical Context and Constraints

- **Language / runtime**：Python `>=3.11`；CLI 入口 `digest = knowledge_digest.cli:main`。
- **Primary dependencies**：标准库、现有 pytest；不新增运行时框架。LLM/embedding 只复用现有 OpenAI-compatible HTTP seam。
- **Storage / state**：Markdown KB、`kb.structure.md`、`README.md`、`Home.md`、`indexes/`、叶分类主题目录、`_digest/` JSON/JSONL；写回由现有单写者锁和 archive-before-write 负责。
- **Testing**：pytest acceptance；schema/identity/link 用临时目录和 fake generator；89 篇语料只写新的隔离 KB；真实 qwen3.6 只在显式构建验收使用，verify-code 使用离线记录或 deterministic fixture。
- **Target environment**：本机 macOS、单用户、离线可消费；不存在后台服务要求。
- **Project type**：Python `src-layout` 本地 CLI 与文件型知识库。
- **Performance goals**：请求硬超时 180 秒；dry-run planned generator calls 超过 180 时不发请求；89 篇目标 30 分钟、60 分钟安全上限；失败来源最多一次拆单重放。
- **Scale / scope**：89 篇 Confluence 来源、20 个以内的分层对比样本、最多 300 行/页。
- **Relevant ADR / context**：`docs/plans/universal-knowledge-digest-design.md`、现有 `kb_structure.py`、`identity.py`、`page_layout.py`、`batch_run.py`、`writeback.py`、`provenance.py`、`llm.py` 与 acceptance tests。
- **Unresolved facts**：qwen3.6/jina 端点可用性和人工标题判断只能在隔离验收时确认；缺凭据或网络时走 deterministic fallback。产品范围无未决项。

### Global Constraints

- LLM 只提出 title/slug/category/Summary/Why/Version/related topics；程序决定路径、分类合法性、分页、链接、权限和写入。
- taxonomy 唯一事实源是 `kb.structure.md` 的叶分类和受控 parent_id；不新增并行 taxonomy 配置或 taxonomy.py。
- Task2 89 篇验收使用新空 KB；Task1 输出只读，用于比较，不执行旧 pending 页的物理迁移。
- stable topic-index、首个 category/path、Claim 唯一 target path、Provenance、写前归档、单写者锁必须保留。
- qwen3.6 精确使用现有 `KD_LLM_*` 环境；jina 使用现有 `similarity.embedding`/`api_key_env`/adopted artifact；拒绝 DeepSeek 和其他 provider。
- 一个运行不能混用 embedding/Jaccard；`--no-llm` 不发送模型或 embedding 请求。
- 行为先 RED 后 GREEN；不提交凭据、真实语料正文或绝对主机路径。

## 3. Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"CONSTITUTION.md","hash":"a4c63f0c3865fdc2ea83b1f2aea0a824608f65512a27a21e05a58e2d80e16001","id":"WORKFLOWHUB-CONSTITUTION","version":"1.5.0","clause_count":21}`

### Framework Principles

- [x] F1：`pipeline.py` 只编排；publication/navigation/已有写回各自窄职责。
- [x] F2：跨模块只传稳定主题、发布建议、布局记录和既有 Claim/Provenance 合同。
- [x] F3：schema、taxonomy、Claim 引用、topic-index、路径和 hash 校验均 fail-closed。
- [x] F4：计划阶段使用一次真实异源 `wh-review`；不可用事实不改写成通过。
- [x] F5：只增加本规格要求的发布合同，不建通用框架或 gate 平台。
- [x] F6：调用、回退、成本和 CompanyBrain 比较写 evidence/report，不藏状态。
- [x] F7：保留 build-plan 人工确认；不因确认自动提交、推送或清理。
- [x] F8：优先扩展 `kb_structure.py`、`identity.py`、`page_layout.py`、`batch_run.py`、`writeback.py`。
- [x] F9：RED 必须因目标行为缺失失败；环境错误不算 RED。
- [x] F10：新增 `publication.py`/`navigation.py` 与最小 `llm.py` 改动只对应真实缺口。

### Quality Principles

- [x] Q1：review findings 修复或明确记录，不循环制造 verdict。
- [x] Q2：机器结构门、provider review、人工阅读判断分别报告。
- [x] Q3：异源 review 由 wh-review 负责，主代理不改写原始结果。

### Skill Principles

- [x] S1：HTTP/JSON/Markdown 使用现有标准库，不新增框架。
- [x] S2：N/A — 不引入外部 skill 代码。
- [x] S3：N/A — 不升级第三方依赖。
- [x] S4：成本、回退、样本 manifest 和结果 hash 写入可审计证据。
- [x] S5：计划已由独立子代理复核；结论回写当前材料。
- [x] S6：复用现有 generator、Jaccard/embedding、archive/writeback seam。
- [x] S7：不新增 WorkflowHub 阶段或任务实例。
- [x] S8：publication 输出可在离线环境阅读和校验。

**Result**：21/21 addressed；无产品范围 blocker。

## 4. Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| Project rules | `AGENTS.md` | change | T021 | 同步最终输出入口、命令、目录用途和不变量 |
| Workflow contracts | N/A | no change | N/A | 不修改 WorkflowHub |
| Review contracts | N/A | no change | N/A | 沿用现有 wh-review |
| Schemas and events | `src/knowledge_digest/kb_structure.py`, `publication.py`, `batch_run.py` | change | T001-T008,T017-T018 | taxonomy/index、publication field_refs、state v3 |
| Runtime configuration | `src/knowledge_digest/llm.py` | change | T005-T008 | qwen allowlist、180s deadline、publication response |
| Knowledge and docs | `scripts/task2_publication_comparison.py`、`docs/reports/knowledge-digest-task2-publication-comparison.md` | change | T019,T022-T023 | 固定样本和读者对比报告 |
| Automation gates | `tests/acceptance/test_task2_publication.py`、`test_task2_batch_recovery.py`、`test_task2_corpus_regression.py` | change | T001-T023 | 新增最小行为、恢复和语料门 |

## 5. Technical Decisions

### DEC-001 — taxonomy 单一事实源与父/叶模型

- **Problem**：独立 JSON taxonomy 会与现有 `kb.structure.md` PublicationContract 漂移，平铺 Home 也无法形成 CompanyBrain 式入口。
- **Options**：并行 JSON；叶分类存 `parent_id`、父分类仅逻辑节点；运行时自由生成。
- **Selected**：extend `kb_structure.py`，只存叶分类行和受控 parent_id；Home 链父索引，父索引聚合叶分类。
- **Reason**：不引入第二份配置或复杂树；叶 topic_dir 唯一，避免目录 overlap。
- **Consequence / risk**：parser 和导航需支持父索引；旧 KB 缺 taxonomy_version 明确 fail-closed。
- **Fallback**：新空 KB 初始化全 taxonomy；旧 KB 仅保留 Task1 读者结果并提示人工迁移，不静默移动。

### DEC-002 — publication 建议复用既有 generator

- **Problem**：新增语义请求会把 89 篇运行成本翻倍，且破损 JSON 风险扩大。
- **Options**：第二次 metadata 请求；纯 deterministic；在既有 generator response 增加可选 `publication` 对象。
- **Selected**：extend `llm.py`/`draft.py` 既有请求，publication call 增量为零。
- **Reason**：复用 hard deadline、spawn 和现有 claim 保真门；报告区分 generator 与 publication 字段验证。
- **Consequence / risk**：旧 provider JSON 合同需要向后兼容；缺 publication 对象时 deterministic fallback。
- **Fallback**：保持现有 final_body/claims/coverage 输出，字段状态为 fallback/needs-review。

### DEC-003 — identity/path 与 topic-index

- **Problem**：当前 topic_id 以最小 source_id 为 anchor，新增来源或合并可能改变 identity。
- **Options**：每次重算；禁止新增来源；持久化 topic-index。
- **Selected**：extend `identity.py`，用 `_digest/topic-index.json` 锁 topic membership/category/path。
- **Reason**：允许增量来源而不漂移路径；跨分类冲突不自动移动。
- **Consequence / risk**：需要 topic universe 和 collision tests。
- **Fallback**：未知/冲突 topic 进入 needs-review，旧 path 不覆盖。

### DEC-004 — source-index 纳入同一写回

- **Problem**：当前 source-index 在 writeback 后单独写，失败会留下导航与索引不一致。
- **Options**：继续单独写；新增声明路径并加入 staged outputs；数据库事务。
- **Selected**：extend PublicationContract/writeback，声明 `publication_source_index`，与 Home/主题/Provenance 同批 archive-before-write。
- **Reason**：复用现有写回原语，不引入数据库。
- **Consequence / risk**：需要 source-index failure injection 和旧 index recovery test。
- **Fallback**：任何 source-index 写失败都保持旧 index/旧页面快照，明确失败。

## 6. Solution Design

### Overview

S1–S3 继续产生来源、Claim 和候选主题。S4 的现有 generator 响应增加可选 `publication`，由 `publication.py` 做 schema、field_refs、数字/标识符证据回指和 model allowlist 校验；缺失/非法字段回退到 metadata/H1/文件名和 pending。完整 topic universe 建立后，`navigation.py` 再解析 related topics 和父/叶分类索引。

`page_layout.py` 读取 topic-index 的 locked identity，先合并完整主题证据，再按语义 slug 和 300 行上限切分。`navigation.py` 生成 KB README、Home、父索引、叶索引和 publication_source_index 记录；`writeback.py` 将这些记录与主题页、Provenance 一起先归档后原子发布。`batch_run.py` 的 v3 state 保存模型/taxonomy/topic plan 和预算；成功来源先落盘，失败来源可拆分恢复。

### Module responsibilities

#### `publication.py`

- **Responsibility**：publication JSON schema、field_refs、model identity、字段 fallback、product_slug deterministic extraction。
- **Consumes**：稳定 topic、Claim/Evidence、PublicationContract、现有 generator response。
- **Produces**：`PublicationMetadata`（字段状态、needs-review、claim refs）；不直接写文件。
- **Must not decide**：最终路径、权限、taxonomy 内容、Claim 主体。

#### `navigation.py`

- **Responsibility**：README、Home、父/叶分类页、source-index、related link 的纯记录渲染。
- **Consumes**：validated metadata、完整 topic universe、final layouts、PublicationContract。
- **Produces**：带 managed marker 的导航 records；未知 related id 只丢弃并记录 needs-review。
- **Must not decide**：事实、Claim、Evidence、模型调用或 topic identity。

#### Existing modules

- `kb_structure.py`：解析叶分类、parent_id、taxonomy 元数据和 publication_source_index。
- `identity.py`：稳定 topic-index、ASCII slug、首次路径锁和 collision。
- `page_layout.py`：最终聚合、分页、header/category/path 一致性。
- `llm.py`/`draft.py`：既有请求、qwen allowlist、publication object、180s deadline。
- `batch_run.py`：state v3、成功 checkpoint、split_from、resume。
- `writeback.py`/`provenance.py`：同批归档、原子发布、溯源。

### Conditional contracts

- **UI**：N/A — Task2 只发布静态 Markdown，不新增浏览器界面。
- **Externally maintained code**：N/A — 不修改 WorkflowHub 或第三方 provider。

## 7. Data Model and Lifecycle

- `PublicationMetadata`：`title`, `slug`, `category_id`, optional `product_slug`, `summary`, `why`, `version`, `related_topics`, `claim_refs`, `field_refs`, per-field status 和 `needs_review`。
- `PublicationCategory`：叶 `id/title/topic_dir/parent_id/aliases`；父集合由 parent_id 派生；`pending` 是 operational leaf，不计 Other。
- `TopicIndex`：`schema_version`, `topics[{topic_id, source_ids, category_id, published_path, product_slug}]`；首次写入后锁 category/path。
- `SourceIndex`：`schema_version`, `entries[{source_uri, content_fingerprint, status, target_paths}]`；进入同一 writeback staged output。
- 状态：来源 `pending → processing → published`，provider/schema 失败 `needs-review`；布局 `drafted → layout_finalized → archived-before-write → published`。

## 8. API Contract

无新增 HTTP API。内部接口：

- `validate_publication_suggestion(raw: object, *, claims: list[dict], publication: PublicationContract, topic_universe: set[str]) -> PublicationMetadata`：字段级 invalid 返回 fallback metadata；taxonomy/topic-index/source-index 结构错误抛 `ValidationError`。
- `build_publication_navigation(layouts, paths, publication, topic_universe, source_index) -> list[dict]`：只返回导航/README/source-index records，不写磁盘。
- `audit_run(...) -> tuple[Path, str]`、`draft(...) -> list[dict]`、`writeback(...) -> list[dict]` 保持现有公共签名。

## 9. File Boundary

### NEW

- `src/knowledge_digest/publication.py`
- `src/knowledge_digest/navigation.py`
- `tests/acceptance/test_task2_publication.py`
- `tests/acceptance/test_task2_batch_recovery.py`
- `tests/acceptance/test_task2_corpus_regression.py`
- `scripts/task2_publication_comparison.py`
- `docs/reports/knowledge-digest-task2-publication-comparison.md`

### MODIFY

- `src/knowledge_digest/kb_structure.py`
- `src/knowledge_digest/identity.py`
- `src/knowledge_digest/page_layout.py`
- `src/knowledge_digest/draft.py`
- `src/knowledge_digest/llm.py`
- `src/knowledge_digest/pipeline.py`
- `src/knowledge_digest/writeback.py`
- `src/knowledge_digest/batch_run.py`
- `src/knowledge_digest/provenance.py`
- `tests/acceptance/test_publication_contract.py`
- `AGENTS.md`

### DO NOT TOUCH

- `src/knowledge_digest/ingest.py`
- `src/knowledge_digest/cluster.py`
- `src/knowledge_digest/retrieve.py`
- `src/knowledge_digest/faithfulness.py`
- `config/knowledge-digest.json`
- `tests/fixtures/`
- `docs/plans/universal-knowledge-digest-design.md`
- `/Users/Hugh/Downloads/confluence` 原始目录和 `/Users/Hugh/Downloads/KnowledgeDigest-offline-architecture-verified-5Ng5LpvP`

## 10. Data Flow and Integration

```text
S1-S3 source/claims → existing draft generator + publication object
→ field/schema/identity validation → complete topic universe
→ final aggregate/paging → README/Home/parent/leaf/source-index records
→ single archive-before-write transaction → provenance/report
```

- **Integration points**：S4 产出 validated metadata；layout 消费 locked topic/path；navigation 消费完整 universe；writeback 同批发布所有 records；batch state 保存 identity/budget。
- **Compatibility boundaries**：公共 `audit_run`/`draft`/`writeback` 签名保持；旧正文/Claim/Evidence/Provenance 合同保持；旧 Task1 KB 不原地迁移。
- **Fail-loud behavior**：taxonomy/manifest/model/path/Claim ref/JSON/source-index/link/写入失败抛 `ValidationError`，旧快照可恢复。

## 11. Code Anchors and Reuse

### Versioned identity and context projection

- **Spec binding**：`{"artifact_kind":"spec","ref":"specs/knowledge-digest-llm-naming-classification/spec.md","hash":"f73a61a90558e7a663f71ee28ec573c581ec033eee6b5dca53650626f894fd42","id":"kd-task2-publication-spec"}`。
- **read_now**：`identity.py`, `kb_structure.py`, `page_layout.py`, `llm.py`, `batch_run.py`, `writeback.py`, `provenance.py`, current acceptance tests。
- **must_read_before_task**：T001 前读 `kb_structure.py` parser；T005 前读 `llm.py` `_request_payload`/generator parser；T009 前读 `identity.py`/`page_layout.py`；T015 前读 `writeback.py`；T017 前读 `batch_run.py`。
- **Context mode**：Full for existing boundaries; no S1–S3 redesign。

### Verified anchors

| Anchor | Path and symbol | Current responsibility | Intended use | Forbidden change |
| --- | --- | --- | --- | --- |
| A-001 | `identity.py:topic_id`, `publication_topic_part_path` | source-derived identity and paths | extend topic-index/ASCII fallback/path lock | no cluster/draft leakage |
| A-002 | `kb_structure.py:PublicationContract`, `inspect_structure` | roots/categories/safety | leaf taxonomy/parent/source-index fields | no parallel config |
| A-003 | `page_layout.py:build_topic_layouts` | aggregate/split final pages | locked path/header/category and 300-line rule | no per-batch final publish |
| A-004 | `page_layout.py:build_publication_navigation` | Home/category records | delegate to navigation.py | no claim generation |
| A-005 | `llm.py:_request_payload`, `draft.py:draft` | bounded provider response and drafts | publication object, allowlist, 180s | no DeepSeek/fallback |
| A-006 | `batch_run.py:_manifest`, `_load_or_create_state` | fixed source state/resume | state v3/budget/split_from | no scheduler |
| A-007 | `writeback.py:writeback`, `provenance.py` | archive/materialize/lineage | source-index same transaction | no unsafe direct write |

### Reuse → Extend → New

| Capability | Decision | Existing candidates | Reason |
| --- | --- | --- | --- |
| taxonomy | extend | A-002 | one source of truth |
| semantic metadata | extend + new | A-005 + `publication.py` | no second provider call |
| identity/path | extend | A-001 | durable locked paths |
| layout/navigation | extend + new | A-003/A-004 + `navigation.py` | isolate reader rendering |
| batch recovery | extend | A-006 | preserve state semantics |
| atomic source-index | extend | A-007 | no new storage primitive |

### Existing interface signatures

| Signature ID | Object | Verified current signature/schema | Source anchor |
| --- | --- | --- | --- |
| SIG-001 | `pipeline.audit_run` | `audit_run(paths, settings, roots=DEFAULT_ROOTS, *, dry_run, generator=None, allowed_content_paths=None, cluster_plan=None, global_duplicates=None) -> tuple[Path, str]` | A-007 |
| SIG-002 | `draft.draft` | `draft(decisions, clusters, raw_items, run_dir, settings, *, generator=None, dry_run=False) -> list[dict[str, Any]]` | A-005 |
| SIG-003 | `page_layout.build_topic_layouts` | `build_topic_layouts(drafts, paths, roots, *, max_lines, publication=None) -> list[dict[str, Any]]` | A-003 |
| SIG-004 | `writeback.writeback` | `writeback(drafts, run_dir, paths, roots, *, publication=None) -> list[dict[str, Any]]` | A-007 |

## 12. Rollback and Recovery

- **Global recovery rule**：所有测试和真实语料写入新隔离 KB；实现失败恢复到旧 managed pages/archives，不改 Task1 baseline。
- **Irreversible boundaries**：不删除旧 topic part、不覆盖原始 Confluence、不提交凭据；真实 LLM 运行需用户授权。
- **Recovery owner**：build-code 执行者保留失败 batch state/report；修复后只恢复未完成来源。

### Engineering Risk Handoff

- **PLAN-RISK-001**：leaf/parent taxonomy 与旧结构
  - **Affected IDs**：SCOPE-002、AC-001、AC-006
  - **Trigger**：旧 KB 缺 taxonomy_version 或 topic_dir overlap
  - **Consequence**：分类错误或写入手写页
  - **Mitigation or STOP**：新空 KB 初始化完整 taxonomy；旧 KB fail-closed；父节点无 topic_dir；结构 fixture 不通过即 STOP
  - **Handling Stage**：`build-code`
  - **Verification**：taxonomy/old-structure/overlap tests
- **PLAN-RISK-002**：topic identity/path/collision
  - **Affected IDs**：SCOPE-001、SCOPE-005、AC-002～004
  - **Trigger**：新增来源、标题变化、同 slug 跨分类、topic merge
  - **Consequence**：路径漂移、重复 Claim、孤儿 part
  - **Mitigation or STOP**：topic-index 锁 source membership/category/path；冲突 needs-review；扫描全部叶目录
  - **Handling Stage**：`build-code`
  - **Verification**：identity/layout/collision tests
- **PLAN-RISK-003**：provider slow/malformed JSON
  - **Affected IDs**：FR-LLM-001～005、AC-005、AC-008
  - **Trigger**：qwen timeout、截断 JSON、模型身份不符
  - **Consequence**：全量归零或成本失控
  - **Mitigation or STOP**：复用单请求 publication object、max output、180s timeout、planned call ceiling、source-level recovery；DeepSeek 不 fallback
  - **Handling Stage**：`build-code` / `verify-code`
  - **Verification**：fake provider faults、dry-run budget、89-doc report
- **PLAN-RISK-004**：reader quality beyond machine gates
  - **Affected IDs**：AC-001、AC-002、AC-007
  - **Trigger**：结构通过但标题/入口仍难懂
  - **Consequence**：机械绿而读者退化
  - **Mitigation or STOP**：固定 sample manifest、usage_boundary_visible 和人工阅读时间；不以 Claim 数替代质量
  - **Handling Stage**：`verify-code`
  - **Verification**：Task1/Task2/CompanyBrain report

## 13. Test Strategy

- **Focused gates**：`uv run --frozen pytest -q tests/acceptance/test_task2_publication.py tests/acceptance/test_task2_batch_recovery.py tests/acceptance/test_task2_corpus_regression.py`。
- **Compatibility gates**：`uv run --frozen pytest -q tests/acceptance/test_publication_contract.py tests/acceptance/test_architecture_optimization.py tests/acceptance/test_phase25_llm.py`。
- **Final gate**：`uv run --frozen pytest -q`；只在 build-code/verify-code 最终阶段执行。
- **RED/GREEN**：每个行为 task 使用相同 focused command 和 oracle；RED 非零，GREEN 为 0。
- **Evidence**：`evidence/build-code/task2/<task-id>-<red|green>.txt`；语料报告/样本 manifest 另存 TaskHandle evidence，不把真实正文写进 Git。
- **Oracle**：`KD-T2-TAXONOMY`、`KD-T2-SEMANTIC`、`KD-T2-NAV`、`KD-T2-RECOVERY`、`KD-T2-CORPUS`。

## 14. Implementation Order

`Phase 1 contract/model → Phase 2 semantic provider → Phase 3 identity/layout/navigation → Phase 4 pipeline/writeback/batch → Phase 5 docs/corpus comparison`。

Phase 1 必须先确定 parent/leaf/pending、topic-index/source-index schema；Phase 2 复用既有 generator 并实现 publication/field_refs 与四段提示词合同；Phase 3 消费 validated metadata 和完整 topic universe；Phase 4 才能写回；Phase 5 依赖全部产物。所有 RED/GREEN 对串行；没有安全的跨 Phase 并行分支。

## 14.1 Independent Review Fact

- **Review**：真实 `wh-review` build-plan 初审，结果 `pass`；报告 `reviews/reports/f1e868bf-933a-4993-85fc-2989d6b5b921.md`，结果 `reviews/results/build-plan-default-08170e43fb2dbeff5e2240ca7820e977891189b3-f1e868bf-933a-4993-85fc-2989d6b5b921.json`。
- **Providers**：`kimi/k3`、`claude-code/opus` 完成；`cursor/grok` permission denied；`codex/terra` SAME_SOURCE，未计入有效 reviewer。有效 reviewer 2/1，未使用 DeepSeek。
- **Disposition**：审查中 provider 标为 `invalid_anchor`/`minor` 的发现没有被伪装成正式 actionable verdict；主代理按可复核代码边界修复了 taxonomy/index 单一职责、分类比例/Task1 无损门、导航委托、提示词/backend/cache/预算断言、source-index 序列化和 plan/tasks traceability。
- **Current revision**：当前材料改变了 review snapshot；WorkflowHub resolution `reviews/resolutions/e053a1d337043b192c0a97bd72a41263e8bba38858bc0fbb98a1b15f20dffd7b.json` 已验证绑定的结构性 response ledger，因旧结果无 actionable cluster 未再次调用 provider。当前计划不把旧 provider pass 包装成“新 provider verdict”。

## Phase 1：Taxonomy 与数据合同

### Goal

固定 parent/leaf/pending taxonomy、topic-index/source-index schema 和旧 KB fail-closed 边界；PublicationMetadata/field_refs 归 Phase 2 单一实现。

### Files

- **NEW**：`tests/acceptance/test_task2_publication.py`
- **MODIFY**：`src/knowledge_digest/kb_structure.py`、`tests/acceptance/test_publication_contract.py`
- **DO NOT TOUCH**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Tasks

- T001/T002：taxonomy、parent/leaf/pending 和旧 KB gate RED/GREEN。
- T003/T004：topic-index/source-index schema RED/GREEN；PublicationMetadata/field_refs 只在 Phase 2 实现。

### Verify

`KD-T2-TAXONOMY`；非法结构/overlap/缺 version/重复 entry 失败，合法新 KB 结构通过。

### Knowledge

`PublicationContract`/`inspect_structure` 是现有解析入口；父分类不占 topic_dir，叶分类独占目录。

### STOP

需要并行 taxonomy 文件、自动迁移旧 pending、或触碰 S1–S3。

### Done

结构、topic-index、source-index 合同可被后续模块读取；旧 publication tests 仍通过；source-index 使用固定 Markdown 表格序列化，不产生并行 JSON。

### Risks and rollback

- **Risk**：旧 parser 回归。
- **Prevention**：保留旧 fixture，RED 后最小扩展。
- **Rollback / recovery**：撤回扩展字段，旧 KB 不迁移。

## Phase 2：语义建议与回退

### Goal

让现有 generator 响应携带可选 publication object，并在 qwen allowlist/180s/max output 下通过字段级校验；不新增 provider 请求。

### Files

- **NEW**：`src/knowledge_digest/publication.py`
- **MODIFY**：`src/knowledge_digest/draft.py`、`src/knowledge_digest/llm.py`、`tests/acceptance/test_task2_publication.py`
- **DO NOT TOUCH**：`src/knowledge_digest/faithfulness.py`

### Tasks

- T005/T006：publication object/schema/field refs RED/GREEN。
- T007/T008：provider failure、malformed JSON、模型不允许、四段提示词、单一相似度 backend/cache key 和 deterministic fallback RED/GREEN。

### Verify

`KD-T2-SEMANTIC`；合法建议通过，非法字段回退，Claim/正文不丢；请求包含固定 `ROLE/EVIDENCE/ALLOWED TAXONOMY/OUTPUT SCHEMA` 四段；同一运行不混用 embedding/Jaccard；`--no-llm` 无请求。

### Knowledge

`llm.py` 当前已有 spawn/hard deadline 和 final_body/claims/coverage parser；本 Phase 只做向后兼容扩展。

### STOP

需要第二次 semantic call、DeepSeek fallback、或改变现有 Claim faithfulness 语义。

### Done

validated metadata 可供 layout 消费；失败来源为 needs-review，不影响成功来源。

### Risks and rollback

- **Risk**：输出截断或字段重复正文。
- **Prevention**：publication output cap、field_refs/数字回指、fake malformed tests。
- **Rollback / recovery**：禁用 publication object，保留 deterministic fields 和原 generator。

## Phase 3：Identity、布局和导航

### Goal

用 topic-index 锁 stable path/category，完成最终聚合分页、父/叶导航、Products product_slug 分组和 README/source-index records。

### Files

- **NEW**：`src/knowledge_digest/navigation.py`
- **MODIFY**：`src/knowledge_digest/identity.py`、`src/knowledge_digest/page_layout.py`、`tests/acceptance/test_task2_publication.py`
- **DO NOT TOUCH**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Tasks

- T009/T010：topic-index/ASCII slug/path collision/first-path lock RED/GREEN。
- T011/T012：final aggregate/paging/header consistency RED/GREEN。
- T013/T014：README/Home/parent/leaf/source-index/related-link navigation RED/GREEN；`page_layout.build_publication_navigation` 只保留到 `navigation.py` 的薄委托，确保单一导航生成来源。

### Verify

`KD-T2-NAV`；Home→parent→leaf→topic 最多三跳；20 或 min(20,n) 样本；页 ≤300 行；Claim 唯一 target；全叶目录 collision 检查；source-index 可回溯。

### Knowledge

`build_topic_layouts` 已有 aggregate/split，`build_publication_navigation` 已有基础 Home/category records；本 Phase 重用其 records 结构并拆出 reader rendering。

### STOP

需要删除旧 part、重复当前 Claim、改变 topic-index identity 或绕过 path/header checks。

### Done

主题页和导航 records 可被同批 writeback 接受，输出根 README 可解释目录用途。

### Risks and rollback

- **Risk**：标题变更导致路径漂移或同 slug 覆盖。
- **Prevention**：locked path、ASCII fallback、全叶目录扫描、collision tests。
- **Rollback / recovery**：保留旧路径/归档，导航回到旧 managed path。

## Phase 4：Pipeline、写回与批次恢复

### Goal

将 metadata/layout/navigation/source-index/provenance 接入同一安全写回；state v3 支持成功 checkpoint、split_from 和预算恢复。

### Files

- **NEW**：`tests/acceptance/test_task2_batch_recovery.py`
- **MODIFY**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/batch_run.py`、`src/knowledge_digest/provenance.py`
- **DO NOT TOUCH**：`src/knowledge_digest/ingest.py`、`src/knowledge_digest/cluster.py`、`src/knowledge_digest/retrieve.py`

### Tasks

- T015/T016：single-writer publication transaction/source-index failure RED/GREEN；pipeline 只消费 navigation records。
- T017/T018：state v3, backend/cache identity、planned-call/60-minute budget、source-level split/resume RED/GREEN。

### Verify

`KD-T2-RECOVERY`；provider/malformed failure 不影响成功批；resume 不重复成功来源；source-index 写失败旧 index 可恢复；manifest/taxonomy/model/topic plan 改变拒绝；planned-call 或 60 分钟墙钟预算超限均 fail-closed。

### Knowledge

`writeback.py` 现有 archive/safe-relative boundary；`batch_run.py` 当前 state v2，需显式升级并拒绝旧错配状态。

### STOP

需要数据库/调度器、删除旧 part、绕过 writeback 或修改 S1–S3。

### Done

CLI 可分批、恢复、报告调用/失败/重放/耗时/fallback；旧快照安全。

### Risks and rollback

- **Risk**：多文件部分写入留下孤儿导航。
- **Prevention**：staged source-index + archive-before-write failure injection。
- **Rollback / recovery**：旧 snapshot/archives 保留，重放未完成来源。

## Phase 5：文档、语料和对比报告

### Goal

让最终结果文件夹可解释，并用固定 sample manifest 对比 Task1、Task2 和 CompanyBrain 的读者质量与成本。

### Files

- **NEW**：`tests/acceptance/test_task2_corpus_regression.py`、`scripts/task2_publication_comparison.py`、`docs/reports/knowledge-digest-task2-publication-comparison.md`
- **MODIFY**：`AGENTS.md`
- **DO NOT TOUCH**：`/Users/Hugh/Downloads/confluence`、`/Users/Hugh/Downloads/KnowledgeDigest-offline-architecture-verified-5Ng5LpvP`、`docs/plans/universal-knowledge-digest-design.md`

### Tasks

- T019/T020：89 篇 no-LLM 隔离回归、无损/结构/导航 report RED/GREEN；读取 Task1 基线只做逐项 Claim/URI/fingerprint 比对，不写入。
- T021：AGENTS.md 与输出 README 说明同步，非行为 gate。
- T022/T023：sample manifest matching、CompanyBrain reader table、provider/budget report RED/GREEN。

### Verify

`KD-T2-CORPUS`；固定输入/空 KB/deterministic config 可重复；Task1 Claim/URI/fingerprint/定位/验证状态逐项匹配；Other≤20%、pending 单独报告、主题不全落单一 `pages/digest`；sample manifest 无人工换样；报告区分机器事实/人工判断且不含密钥/原文。

### Knowledge

Task1 baseline 只读；真实 89 篇运行必须复制到新隔离 KB；CompanyBrain 只作 reader-visible reference。

### STOP

需要覆盖 baseline、调用 DeepSeek、把 Claim 数当质量或无法保留原始目录 hash。

### Done

README/AGENTS 可解释入口和目录；报告包含样本、性能、调用、fallback、读者结论。

### Risks and rollback

- **Risk**：机器门通过但语义阅读退化。
- **Prevention**：人工抽样和 usage_boundary_visible；80% 标题理解度是显式结论。
- **Rollback / recovery**：保留 Task1/Task2 两套结果，先修 semantic metadata 再重跑。

## 15. Dependencies and Parallelism

```text
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
```

T001→T002→T003→T004→T005→T006→T007→T008→T009→T010→T011→T012→T013→T014→T015→T016→T017→T018→T019→T020→T021→T022→T023。RED/GREEN 对串行；没有安全的跨 Phase 并行分支。

## 16. Requirement and Verification Traceability

| Requirement | Task IDs | AC IDs | Phase | Gate / evidence |
| --- | --- | --- | --- | --- |
| SCOPE-001 | T005-T012 | AC-002, AC-003, AC-004 | 2-3 | `KD-T2-SEMANTIC`, `KD-T2-NAV` |
| SCOPE-002 | T001-T004 | AC-001, AC-006 | 1 | `KD-T2-TAXONOMY` |
| SCOPE-003 | T013-T014,T019-T023 | AC-001, AC-003, AC-006, AC-007, AC-008 | 3,5 | `KD-T2-NAV`, `KD-T2-RECOVERY`, `KD-T2-CORPUS` |
| FR-LLM-001 | T005-T006 | AC-002, AC-003 | 2 | semantic schema evidence |
| FR-LLM-002 | T005-T008 | AC-002, AC-003 | 2 | prompt/schema/field_refs evidence |
| FR-LLM-003 | T005-T008 | AC-003, AC-004, AC-008 | 2 | validator/fallback evidence |
| FR-LLM-004 | T007-T008,T017-T018 | AC-006, AC-008 | 2,4 | backend consistency/cache/wall-clock evidence |
| FR-LLM-005 | T007-T008,T017-T020 | AC-005, AC-006 | 2,4,5 | offline/recovery evidence |

所有 8 个 AC 均有 Task 和 gate：AC-001 T001/T013/T019/T020；AC-002 T005/T009/T022/T023；AC-003 T005/T011/T013；AC-004 T007/T011/T019/T020；AC-005 T017/T019；AC-006 T001/T017/T019；AC-007 T022/T023；AC-008 T007/T017/T023。

发布前验证：FR/Scope→Task→AC→gate 双向闭合；依赖无环；每个 Phase Files 与 tasks.md 逐字一致；没有 Task 触碰 DO NOT TOUCH 文件。
