# 实现计划：知识发布合同与离线可读输出

> 基于已接受规格，采用现有 Python 模块的最小纵切扩展；不把审计目录改造成第二套知识库。

- **Input**：`specs/knowledge-digest-publication-contract/spec.md`
- **Status**：Draft
- **Template version**：`plan-task.v3`

## 1. Quick Read

- **Goal**：让新库首次离线运行直接生成可读入口；让旧库只新增或更新明确托管的知识页。
- **Non-goals**：不做 LLM/embedding 命名、自动语义分类、未托管旧页迁移、删除、数据库、调度器或 AgentMemory；来源：accepted spec 第 10 节。
- **Before**：正式页固定写入 `pages/digest/topic-<hash>.md`，读者只能使用 `_digest/source-index.md`；读取会纳入所有 Markdown，分页收缩会移除旧文件。
- **After**：根 `Home.md` → 分类索引 → 带可读标题的托管主题页；审计仍留在 `_digest`，手写和声明外文件不被读取为候选或写入。
- **Main risk**：导航、主题页和归档在同一发布操作中不同步，或旧分页被误删。
- **Next step**：先用 filesystem acceptance test 固定新库/旧库的发布边界，再逐层实现。

## 2. Technical Context

- **Language / runtime**：Python 3.11+；`uv` 管理项目环境。
- **Primary dependencies**：仅标准库与现有项目代码；测试使用 pytest，不新增第三方包。
- **Storage / state**：Markdown 知识库；`_digest` 保存审计和来源索引，`_archive` 保存覆盖前快照，`_queues` 保持既有用途。
- **Testing**：离线 acceptance tests 使用临时目录、`--no-llm` 和 Jaccard；不得向模型、embedding 或网络发请求。
- **Target environment**：本地 macOS/Linux 文件系统；路径和软链接保护沿用现有写入合同。
- **Project type**：人工触发的本地 CLI 知识消化工具。
- **Performance goals**：N/A — 本期改变读者结构与写入安全，不增加索引或后台处理。
- **Scale / scope**：10 个生产模块、3 个既有文档/测试文件和 1 个新增 acceptance 文件。
- **Relevant ADR / context**：`docs/adr/0004-reader-publication-separate-from-audit.md`、`CONTEXT.md`、`AGENTS.md`。
- **Unresolved facts**：已核对：`ingest._source_for/_snapshot` 将 `source_meta` 与 `input_path` 传入 raw item，`draft(draft.py:913)` 持有完整 `raw_items`；T004 只在现有字段上生成标题候选，不改变 ingestion schema。

### Global Constraints

- 新空库可以初始化；非空旧库缺有效声明必须在正式写前失败。
- 只管理 `kb.structure.md` 声明目录内、页头标为 `managed_by: KnowledgeDigest` 的文件。
- 主题 ID 是更新键；首次可读路径锁进 `digest_published_path`，之后标题变化不改路径。
- 仅新增/更新，绝不删除旧文件；分页收缩只从当前导航移除旧 part。
- Summary、Evidence、Provenance、Claim 溯源、写前归档、原子写、单写者和每页 300 行必须保留。
- 未托管或路径冲突的旧内容一律明确失败，禁止猜测或接管。
- 本期不得调用 LLM、embedding 或外部网络；默认 LLM 命名属于后续 Task 2。

## 3. Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"CONSTITUTION.md","hash":"a4c63f0c3865fdc2ea83b1f2aea0a824608f65512a27a21e05a58e2d80e16001","id":"workflowhub-constitution","version":"1.5.0","clause_count":21}`

### Framework Principles

- [x] F1：只扩展现有解析、布局、写回和管线模块，不新增平台核心。
- [x] F2：发布结构、主题身份、导航和写入保护保持窄数据合同。
- [x] F3：结构或托管身份不对即在写前失败，四份材料只用于推进。
- [x] F4：计划接受独立 `wh-review` 与最终人工确认，不把 review 当编码入口。
- [x] F5：仅为已发生的审计页不可读、旧页误读和分页删除问题增加测试。
- [x] F6：WorkflowHub 外置保存阶段证据，不将运行路径写进产品合同。
- [x] F7：本阶段仅请求计划确认；提交、合并和清理另行授权。
- [x] F8：复用文件型 KB、现有原子写和来源索引，不引入数据库或框架。
- [x] F9：路径、所有权、空输入和事务失败均有可失败的文件系统断言。
- [x] F10：只增加一个真实回归测试文件，复用 pytest 与现有 CLI。

### Quality Principles

- [x] Q1：RED/GREEN、完整测试和独立审查是完成质量证据，不是开始工作的门槛。
- [x] Q2：发布结构预检与阶段接受分开；没有测试/AC 证据不宣称完成。
- [x] Q3：本计划在冻结 spec/plan/tasks 上运行异源 `wh-review`，最终由维护者确认。

### Skill Principles

- [x] S1：复用 WorkflowHub 与项目已有模块，不造通用发布框架。
- [x] S2：无需引入或修改外部技能。
- [x] S3：本期不新增第三方技能或依赖，后续 Task 2 再评估 LLM 能力。
- [x] S4：不新增自定义技能；运行报告继续由现有流程产生。
- [x] S5：任务按窄模块和测试边界拆分，方便独立实现和复核。
- [x] S6：已有原始设计、ADR 和独立架构审查作为方案来源。
- [x] S7：继续使用 WorkflowHub 的阶段技能和任务目录，不新增工作流。
- [x] S8：产品仍是本地 `digest` CLI，不绑定特定服务或宿主。

**Result**：21/21 addressed；无宪法 blocker。

## 4. Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| Project rules | `AGENTS.md`、`CONTEXT.md` | change | T007 | 输出和维护合同改变 |
| Workflow contracts | N/A | no change | N/A | 不改 WorkflowHub |
| Review contracts | N/A | no change | N/A | 使用既有 wh-review |
| Schemas and events | N/A | no change | N/A | 无服务协议 |
| Runtime configuration | N/A | no change | N/A | 不新增依赖或配置 |
| Knowledge and docs | `AGENTS.md`、`CONTEXT.md` | change | T007 | 维护入口同步 |
| Automation gates | `tests/acceptance/test_publication_contract.py` | change | T001–T006 | 真实发布回归 |

## 5. Technical Decisions

### DEC-PUB-001 — 发布声明是唯一写入边界

- **Problem**：当前 roots 只表达审计目录，无法区分读者入口、可写主题目录和手写页。
- **Options**：继续按 `pages` 全量扫描；新增数据库 schema；扩展 `kb.structure.md`。
- **Selected**：extend `kb_structure.py` 的现有结构合同。
- **Reason**：一个声明同时约束初始化、读取候选和写入目标，符合原始设计的结构约定。
- **Consequence / risk**：旧未声明 KB 将停止而非自动迁移。
- **Fallback**：维护者新建发布库，或在独立后续任务中显式设计迁移。

### DEC-PUB-002 — 稳定主题 ID 与展示路径分离

- **Problem**：哈希路径可更新却无法阅读，标题变化又不能破坏旧链接。
- **Options**：继续 hash 命名；用标题直接覆盖路径；保留 ID、首次锁路径。
- **Selected**：extend `identity.py`、`draft.py` 与 `page_layout.py`；`draft()` 生成确定性标题候选，`page_layout` 保留 `digest_topic_id` 并锁定首次路径。
- **Reason**：更新只依赖稳定 ID，读者只面对可读标题和文件名；固定顺序是已有托管 H1 → source metadata `title` → 首个 Markdown H1 → 输入文件名。
- **Consequence / risk**：离线标题质量受来源元数据限制。
- **Fallback**：使用固定 title/H1/文件名顺序和 pending 分类；LLM 命名以后单独定义。

### DEC-PUB-003 — 导航和主题页同批发布，旧分页只退出现行导航

- **Problem**：单独写导航会造成死链；`unlink()` 与无删除合同冲突。
- **Options**：导航独立写；物理删除旧分页；复用现有写回事务统一预检和原子写。
- **Selected**：extend `writeback.py` 的预检/归档/回滚路径，并为导航记录定义零 Claim、审计豁免合同；不增加新事务框架。
- **Reason**：用同一失败模型保护主题页、Home 和分类索引；导航仍可归档覆盖，但不会被追加 Provenance 或送入 Claim history；旧 part 保留原字节。
- **Consequence / risk**：历史文件会累积。
- **Fallback**：当前导航仅指向现行 part；清理策略留给独立生命周期任务。

## 6. Solution Design

### Overview

先让 `kb.structure.md` 从“roots + Why/version”升级为最小发布合同。不存在或空的目标库在单写者锁内生成默认声明、Home 和 pending 分类索引；非空旧库仍必须已经有有效声明。

再让主题布局使用稳定 `digest_topic_id` 查找已托管页、读取锁定路径，并在首次发布时从本地标题候选生成可读 slug。所有无法按声明分类的主题落到 pending，不做语义猜测。

最后把主题页、Home 和分类索引作为一个正式发布批次预检和写入。读取候选只限受管主题；任何手写页、未声明路径、伪造页头或写入失败都在写入前终止。分页收缩只更新现行导航，旧 part 原字节留存。

### Module responsibilities

#### 发布结构合同

- **Responsibility**：解析、验证和初始化发布声明。
- **Consumes**：`kb.structure.md` 或一个不存在/空的 KB 目录。
- **Produces**：安全的 home/index/category/topic 目录范围与默认 pending 分类。
- **Must not decide**：标题语义、LLM 调用、手写页迁移。

#### 主题发布布局

- **Responsibility**：为每个稳定主题选择首次展示路径、页头和当前分页。
- **Consumes**：主题 ID、来源标题候选、已托管页和结构合同。
- **Produces**：可读主题页草稿及现行导航条目。
- **Must not decide**：是否接管未托管页，或删除历史 part。

#### 托管写入与导航

- **Responsibility**：预检所有正式目标、归档覆盖内容、原子发布主题和导航。
- **Consumes**：已验证发布草稿、现有 KB 文件和 run 目录。
- **Produces**：完整写回记录、首页、分类索引和审计来源索引。
- **Must not decide**：分类语义或外部服务调用。

### Conditional contracts

- **UI**：N/A — 本期是本地 CLI 和 Markdown 输出。
- **Externally maintained code**：N/A — 不修改外部维护代码。

## 7. Modules, Interfaces, and Data Contracts

- `PublicationContract`：保留 roots/Why/version，并新增 `home_path`、`index_root`、唯一 pending 分类和安全、互不重叠的写入范围。
- 托管 topic frontmatter：`managed_by: KnowledgeDigest`、`digest_kind: topic`、`digest_topic_id`、`digest_published_path`、`digest_part`；实际相对路径必须等于锁定路径。
- 导航 frontmatter：`managed_by: KnowledgeDigest` 与 `digest_kind: home|category`；仅保存链接和简短说明。
- `publication_title_candidates`（draft record）：`draft()` 以 Claim/source 顺序收集、去重：非空 `source_meta.title` → 每个 `item["text"]` 的首个 Markdown H1 → `Path(item["input_path"]).stem`。`page_layout` 先采用同一 `digest_topic_id` 的已托管 H1，否则取首个候选；`identity` 生成安全 slug，同名追加短 topic ID。
- Publish record：topic 记录必须有 `digest_kind: topic`、`layout_finalized: true`、完整 `rendered_content`、Claim/Provenance，且参与 `audit_provenance` 与 Claim history；navigation 记录必须有 `digest_kind: home|category`、`layout_finalized: true`、完整 `rendered_content`、`claims: []`、`publication_audit_scope: none`。导航仍进入预检、归档、原子写/回滚，但 `writeback` 不追加 `## Provenance`，`pipeline` 不把它们传给审计或 Claim history。
- 读取候选合同：仅结构声明主题目录内、前述 topic 字段完整且路径匹配的页可参与 revise/merge；Home/category 永不作为候选。
- 发布批合同：主题、Home、分类索引全部预检；任一失败时不留下新的或部分更新的正式读者页。

## 8. File Boundary

### NEW

- `tests/acceptance/test_publication_contract.py`

### MODIFY

- `src/knowledge_digest/kb_structure.py`
- `src/knowledge_digest/paths.py`
- `src/knowledge_digest/lock.py`
- `src/knowledge_digest/cli.py`
- `src/knowledge_digest/pipeline.py`
- `src/knowledge_digest/identity.py`
- `src/knowledge_digest/draft.py`
- `src/knowledge_digest/page_layout.py`
- `src/knowledge_digest/retrieve.py`
- `src/knowledge_digest/writeback.py`
- `tests/acceptance/test_architecture_optimization.py`
- `AGENTS.md`
- `CONTEXT.md`

### DO NOT TOUCH

- `docs/plans/universal-knowledge-digest-design.md`
- `src/knowledge_digest/llm.py`
- `src/knowledge_digest/embedding.py`
- `src/knowledge_digest/calibration.py`
- `src/knowledge_digest/agentmemory_store.py`
- `src/knowledge_digest/batch_run.py`

## 9. Data Flow and Integration

```text
KB 目录容器准备 → 单写者锁内 PublicationContract 预检/初始化 → ingest raw metadata → draft 标题候选 → topic ID + 可读主题布局 → topic/navigation 发布记录 → 托管写入批 → Home/分类索引 + _digest 审计
```

- **Existing modules / packages / services**：复用 `validate_paths`、`kb_lock`、`audit_run`、`build_topic_layouts`、`writeback` 和 pytest。
- **Integration points**：CLI/paths 只创建缺失的空 KB 目录容器，再取得 `kb_lock`；锁内重新判定“仅 lock 文件”为空并初始化声明/Home/category。目录创建不是正式读者输出；pipeline 把已验证发布合同传入 retrieve/layout/writeback，并只把 topic 记录送审计/history。
- **Compatibility boundaries**：S1–S6、Claim history、来源索引、归档和现有 `digest` 参数继续存在。
- **Fail-loud behavior**：路径越界、分类冲突、未托管旧页、锁定路径不匹配和批次写失败必须停止。

## 10. Code Anchors

### Versioned identity and context projection

- **Spec binding**：`{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"}`
- **read_now**：`kb_structure.py:parse_roots/inspect_structure`、`paths.py:validate_paths`、`identity.py:topic_part_path`、`retrieve.py:_page_records`、`page_layout.py:_render_page/build_topic_layouts`、`writeback.py:writeback`、`pipeline.py:_write_source_index/_audit_run_locked`。
- **must_read_before_task**：`lock.py:kb_lock`、现有 acceptance fixtures；标题元数据与 draft shape 已由 A-008/A-009、SIG-005/SIG-006 锁定。
- **Context mode**：Full — 一个发布合同跨读取、布局、写入和导航，不能只局部猜测。

### Verified anchors

| Anchor | Path and symbol | Current responsibility | Intended use | Forbidden change |
| --- | --- | --- | --- | --- |
| A-001 | `kb_structure.py:inspect_structure` | roots 与 Why/version 门 | extend | 不删除 Why/version 门 |
| A-002 | `paths.py:validate_paths` | 要求 KB 与结构文件存在 | extend | 不绕过来源 items 校验 |
| A-003 | `identity.py:topic_part_path` | 固定 hash digest 路径 | extend | 不改变 topic ID 语义 |
| A-004 | `page_layout.py:_render_page` | 渲染标题、段落、页头 | extend | 不丢 Evidence/Provenance |
| A-005 | `retrieve.py:_page_records` | 枚举候选 Markdown | extend | 不读取手写页为候选 |
| A-006 | `writeback.py:writeback` | 预检、归档、原子写、回滚 | extend | 不物理删除旧 part |
| A-007 | `pipeline.py:_write_source_index` | 生成审计来源索引 | reuse | 不将其作为读者入口 |
| A-008 | `ingest.py:_source_for/_snapshot` | raw item 传递 `source_meta`、`input_path` | reuse | 不改 ingestion schema |
| A-009 | `draft.py:draft`（913–958、1289–1320） | 从 raw items 生成 draft record | extend | 不调用 LLM/embedding 取标题 |

### Reuse → Extend → New

| Capability | Decision | Existing candidates | Reason |
| --- | --- | --- | --- |
| 发布结构解析 | extend | A-001 | 不引入第二份 schema |
| 路径/标题锁定 | extend | A-003、A-004 | topic ID 已稳定可复用 |
| 读者导航 | extend | A-004、A-006、A-007 | 复用 Markdown、写回与审计层 |
| 旧库保护 | extend | A-005、A-006 | 读取和写入使用同一托管边界 |
| 回归覆盖 | new | pytest acceptance | 已有真实故障需一组窄测试 |

### Existing interface signatures

| Signature ID | Object | Verified current signature/schema | Source anchor |
| --- | --- | --- | --- |
| SIG-001 | CLI | `digest NEW_DIR KB_DIR [--no-llm]` | `cli.py:build_parser` |
| SIG-002 | paths | `validate_paths(new_dir: Path, kb_dir: Path) -> DigestPaths` | A-002 |
| SIG-003 | writeback | `writeback(drafts, run_dir, paths, roots) -> list[dict]` | A-006 |
| SIG-004 | layout | `build_topic_layouts(drafts, paths, roots, max_lines)` | `page_layout.py:build_topic_layouts` |
| SIG-005 | ingest raw item | `raw_item["source_meta"]`、`raw_item["input_path"]` | A-008 |
| SIG-006 | draft | `draft(decisions, clusters, raw_items, run_dir, settings, *, generator=None, dry_run=False) -> list[dict]` | A-009 |

## 11. Rollback and Recovery

- **Global recovery rule**：保留成功前旧字节和现有 `_archive`；失败只回滚本次拥有的新正式输出，不接管手写文件。
- **Irreversible boundaries**：本期不删除文件；提交、推送、合并和清理需另行授权。
- **Recovery owner**：实现者停止当前写入、保存 run 审计和失败测试，返回 build-plan 处理新接口或范围。

### Engineering Risk Handoff

- **PLAN-RISK-001**：主题页、导航和旧分页的原子一致性。
  - **Affected IDs**：FR-PUB-002、FR-PUB-004、FR-PUB-005、AC-04、AC-05、AC-07。
  - **Trigger**：任意一个正式目标预检或原子替换失败。
  - **Consequence**：可能出现死链、部分读者入口或误删旧页。
  - **Mitigation or STOP**：所有目标先预检；复用 rollback；禁止 `unlink()` 旧 part；无法覆盖时 STOP。
  - **Handling Stage**：build-code。
  - **Verification**：手写页 byte 不变、失败无部分写、分页收缩旧 part byte 不变的 acceptance tests。

## 12. Test Strategy

- **Target**：新库初始化、旧库范围、空输入和声明错误。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "initialization or structure or empty_input"'`
- **expected_exit**：RED=1，GREEN=0。
- **evidence_path**：`evidence/publication-contract/phase-1-structure.txt`
- **display_cmd**：N/A — pytest 输出是直接证据。
- **Oracle ID and result**：KD-PUB-STRUCTURE；只在允许的初始化条件生成声明和导航，旧库错误零正式变更。

- **Target**：可读标题、锁定路径和离线零外部调用。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "title or published_path or navigation or offline"'`
- **expected_exit**：RED=1，GREEN=0。
- **evidence_path**：`evidence/publication-contract/phase-2-reader-output.txt`
- **display_cmd**：N/A — pytest 输出是直接证据。
- **Oracle ID and result**：KD-PUB-READER；读者导航不入审计目录，标题可读、路径稳定、零外部调用。

- **Target**：托管边界、分页收缩和发布事务。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "managed or handwritten or shrink or transaction or provenance"'`
- **expected_exit**：RED=1，GREEN=0。
- **evidence_path**：`evidence/publication-contract/phase-3-safe-write.txt`
- **display_cmd**：N/A — pytest 输出是直接证据。
- **Oracle ID and result**：KD-PUB-SAFE-WRITE；未托管页不变、旧分页留存、失败无部分写、质量段落完整。

- **Target**：最终契约回归与维护文档。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py tests/acceptance/test_architecture_optimization.py && uv run --frozen pytest -q'`
- **expected_exit**：0。
- **evidence_path**：`evidence/publication-contract/final-regression.txt`
- **display_cmd**：N/A — pytest 输出是直接证据。
- **Oracle ID and result**：KD-PUB-REGRESSION；全部发布合同和既有架构回归通过，维护文档与实际 CLI/文件边界一致。

## 13. Implementation Order

Phase 1 先生成可验证的发布结构，避免后续模块自己猜目录。Phase 2 只在已验证结构上产生稳定身份与读者页。Phase 3 再把读取范围和写入事务收紧，防止 Phase 2 的输出覆盖旧库。Phase 4 最后同步维护文档并跑全量回归。每个行为改动都先 RED 再 GREEN，阶段间串行。

## 14. Dependencies and Parallelism

```text
Phase 1: T001 → T002
Phase 2: T002 → T003 → T004
Phase 3: T004 → T005 → T006
Phase 4: T006 → T007
```

- Phase 1 是所有发布路径的 producer，不能并行。
- Phase 2 依赖声明范围；Phase 3 依赖可读布局输出。
- T007 只在行为和最终文件边界稳定后执行；不与写入模块并行。

## 15. Requirement and Verification Traceability

| FR | Task IDs | AC IDs | Phase | Gate / evidence |
| --- | --- | --- | --- | --- |
| FR-PUB-001 | T001、T002 | AC-01、AC-08 | Phase 1 | KD-PUB-STRUCTURE |
| FR-PUB-002 | T001、T002、T005、T006 | AC-02、AC-04 | Phase 1、3 | KD-PUB-STRUCTURE / SAFE-WRITE |
| FR-PUB-003 | T003、T004 | AC-03 | Phase 2 | KD-PUB-READER |
| FR-PUB-004 | T003、T004、T005、T006；T007 仅回归确认 | AC-01、AC-02、AC-04、AC-07 | Phase 2、3；Phase 4 仅确认 | KD-PUB-READER / SAFE-WRITE（主证据） |
| FR-PUB-005 | T005、T006 | AC-05、AC-07 | Phase 3 | KD-PUB-SAFE-WRITE |
| FR-PUB-006 | T003、T004 | AC-06 | Phase 2 | KD-PUB-READER |
| FR-PUB-007 | T001、T002 | AC-01、AC-08 | Phase 1 | KD-PUB-STRUCTURE（主证据） |

## 16. Governance Synchronization Matrix

第 4 节矩阵是唯一治理同步权威；本节不重复列第二份矩阵。

## 17. Complexity Trade-offs

- 选择扩展现有 Markdown、结构解析和写回，而非数据库或新发布服务：实现面小，仍能 fail-loud。
- 选择唯一 pending 分类而不是离线语义分类：可重复、零模型成本；分类质量的升级留给 Task 2。
- 选择保留旧分页而不是删除或跳转页：文件会累积，但严格符合“旧库不删除”的数据安全边界。

## Phase 1：发布声明与空库初始化

### Goal

新不存在或空 KB 在锁内生成默认发布声明与无主题读者入口；非空旧 KB 缺声明、路径冲突或结构错误时写前失败。

### Files

- **NEW**：`tests/acceptance/test_publication_contract.py`
- **MODIFY**：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/paths.py`、`src/knowledge_digest/lock.py`、`src/knowledge_digest/cli.py`、`src/knowledge_digest/pipeline.py`
- **DO NOT TOUCH**：`src/knowledge_digest/llm.py`、`src/knowledge_digest/embedding.py`、`src/knowledge_digest/batch_run.py`

### Tasks

- T001 RED：固定初始化、非空旧库拒绝和空输入不改动的文件系统反例。
- T002 GREEN：实现安全声明解析/初始化与 CLI、锁、管线接入。

### Verify

KD-PUB-STRUCTURE，Phase 1 gate；RED 退出非零，GREEN 退出 0。

### Knowledge

现有 `validate_paths` 要求 KB 和结构文件存在；`kb_lock` 也假设目录存在。T002 固定顺序：CLI/paths 用 `mkdir(parents=True, exist_ok=True)` 只准备缺失目录容器 → `kb_lock` → 锁内重新检查目录只含 lock 文件才允许初始化声明/Home/category；已有其他字节立即失败。目录容器本身不是正式发布文件，失败只可移除本次创建且仍为空的目录。

### STOP

若初始化需要猜测非空旧 KB 的目录含义，或无法保证 dry-run 零写入，停止并回到规格。

### Done

空新库有唯一安全声明、Home 和 pending 索引；错误旧库所有正式文件保持字节不变。

### Risks and rollback

- **Risk**：初始化时留下半个 KB。
- **Prevention**：先准备空目录容器、取得锁、锁内重验目录状态；声明/导航复用写入预检。
- **Rollback / recovery**：仅移除本次创建且尚未正式发布的 owned 文件，保留 run 报告。

## Phase 2：稳定可读主题页与导航

### Goal

托管主题保留稳定 ID，但首次发布生成可读标题/路径；Home 和分类索引只链接现行主题页，离线运行零外部调用。

### Files

- **NEW**：N/A — no new production file
- **MODIFY**：`src/knowledge_digest/identity.py`、`src/knowledge_digest/draft.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_publication_contract.py`
- **DO NOT TOUCH**：`src/knowledge_digest/llm.py`、`src/knowledge_digest/embedding.py`、`src/knowledge_digest/retrieve.py`

### Tasks

- T003 RED：固定标题优先级、同名后缀、路径锁定、导航和零外部调用反例。
- T004 GREEN：实现本地标题候选、托管页头、可读路径和导航草稿。

### Verify

KD-PUB-READER，Phase 2 gate；RED 退出非零，GREEN 退出 0。

### Knowledge

`ingest._source_for/_snapshot` 已提供 `source_meta`/`input_path`，`draft()` 已持有 raw items；T004 生成 `publication_title_candidates`，`page_layout` 是唯一消费者与路径锁定点。

### STOP

若现有 `source_meta.title`、Markdown H1 或 `input_path` 均为空且不能生成安全 fallback，停止该主题发布；不得改 ingestion schema 或调用模型补名。

### Done

首次路径可读且锁定，标题变化不改链接，读者路径从 Home 到分类再到主题，不进入 `_digest`。

### Risks and rollback

- **Risk**：同名主题覆盖或后续标题变化破坏链接。
- **Prevention**：短稳定 ID 后缀和 `digest_published_path` 实际路径校验。
- **Rollback / recovery**：保留已有托管页与归档，停止当前发布而不重命名旧页。

## Phase 3：托管边界与无删除发布事务

### Goal

只把受管、路径匹配的主题页作为候选；主题、Home 和分类索引原子发布；收缩分页不删除或改写旧 part。

### Files

- **NEW**：N/A — no new production file
- **MODIFY**：`src/knowledge_digest/retrieve.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_publication_contract.py`
- **DO NOT TOUCH**：`src/knowledge_digest/provenance.py`、`src/knowledge_digest/jsonl.py`、`src/knowledge_digest/batch_run.py`

### Tasks

- T005 RED：固定手写页保护、路径冲突、事务失败和分页收缩的反例。
- T006 GREEN：实现托管候选过滤、topic/navigation Publish record 预检/归档/回滚；导航审计豁免，旧 part 留存。

### Verify

KD-PUB-SAFE-WRITE，Phase 3 gate；RED 退出非零，GREEN 退出 0。

### Knowledge

`retrieve._page_records()` 当前读取所有 Markdown；`writeback()` 当前会处理 `obsolete_target_paths` 并移除文件，也会在非 finalized 页面追加 Provenance；必须以 Publish record 合同明确替换这两处行为。

### STOP

若实现要删除旧文件、接管手写页，或无法保证所有正式目标预检后才写，停止并回到本计划。

### Done

未托管/声明外内容字节不变；旧分页存在且不在当前导航；Home/category 仅链接、无正文/Claim/Evidence/Provenance，且无 Claim history；任何失败不留下部分正式结果。

### Risks and rollback

- **Risk**：导航写成功但主题写失败，或反之。
- **Prevention**：构建统一正式目标集，预检和归档后才原子替换，失败走现有 rollback。
- **Rollback / recovery**：从本 run 的归档恢复被覆盖托管文件；绝不触碰手写或历史 part。

## Phase 4：契约回归与维护入口

### Goal

让测试和项目维护说明使用新发布合同，完整离线回归证明旧质量门未退化。

### Files

- **NEW**：N/A — non-behavior alignment only
- **MODIFY**：`tests/acceptance/test_architecture_optimization.py`、`AGENTS.md`、`CONTEXT.md`
- **DO NOT TOUCH**：`docs/plans/universal-knowledge-digest-design.md`、`config/knowledge-digest.json`、`pyproject.toml`

### Tasks

- T007 N/A：同步既有回归预期与维护入口，并执行完整离线验证。

### Verify

KD-PUB-REGRESSION，完整目标测试和全量 pytest 均退出 0。

### Knowledge

`AGENTS.md` 要求输出合同和开发命令改变时同步更新；原始设计保留为历史权威，不在本任务改写。

### STOP

如果文档与实现不能一致，或全量回归暴露超出 File Boundary 的依赖，停止并回到本计划。

### Done

维护者可从 `AGENTS.md` 和 `CONTEXT.md` 理解新旧库规则、读者入口和不可管理范围；全量离线测试通过。

### Risks and rollback

- **Risk**：历史架构测试仍硬编码 hash audit 页，掩盖读者合同回归。
- **Prevention**：将其断言改为公开托管页与导航合同，并保留审计来源索引断言。
- **Rollback / recovery**：只回退本次文档/测试对齐，不回退已验收的数据保护测试。
