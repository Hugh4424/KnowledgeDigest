# 任务清单：知识发布合同与离线可读输出

> 基于已接受规格和当前实施计划。每张行为任务卡先 RED 后 GREEN；所有命令均离线执行。

- **Input**：`specs/knowledge-digest-publication-contract/spec.md`、`specs/knowledge-digest-publication-contract/plan.md`
- **Status**：Draft
- **Template version**：`plan-task.v3`

## 1. 执行摘要

- **Goal**：交付可从根目录阅读、可安全每日更新的本地 Markdown 知识库。
- **Main boundary**：仅发布结构声明范围内的托管文件；不删除旧文件、不接管手写页、不调用外部智能服务。
- **Main risk**：导航、主题和历史分页未被作为一个正式写入集合处理，造成部分输出或数据破坏。
- **First executable task**：T001。

## 2. Global Constraints

- 只修改各 Phase 精确列出的文件；遇到未声明接口或必须改 `DO NOT TOUCH` 文件立即 STOP。
- 行为改动必须有真实 RED → GREEN；同一对使用相同 `gate_cmd` 和 oracle identity。
- 所有测试在临时 KB 中运行；不写入真实语料、既有基线或网络服务。
- `--no-llm`、Jaccard 运行不得探测 embedding 或创建 LLM 请求。
- 不删除旧 part；只从现行导航移除，旧字节保持不变。
- 完成区只有在实际改动、命令、证据、AC 结果和 Phase review 全部绑定后才可更新。

## Phase 1：发布声明与空库初始化

### Goal

新不存在或空 KB 在锁内生成默认发布声明与无主题读者入口；非空旧 KB 缺声明、路径冲突或结构错误时写前失败。

### Files

- **NEW**：`tests/acceptance/test_publication_contract.py`
- **MODIFY**：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/paths.py`、`src/knowledge_digest/lock.py`、`src/knowledge_digest/cli.py`、`src/knowledge_digest/pipeline.py`
- **DO NOT TOUCH**：`src/knowledge_digest/llm.py`、`src/knowledge_digest/embedding.py`、`src/knowledge_digest/batch_run.py`

### Tasks

#### T001 — RED：发布声明、初始化和空输入反例

- **ID**：T001
- **Phase**：Phase 1：发布声明与空库初始化
- **goal**：先用真实文件系统断言证明当前代码不能安全初始化新库、不能区分旧库空输入与无声明旧库。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-publication-contract/plan.md","hash":"57138508386227a07df888d3c511d291cbd8f729fd4c8b5aaede1fbba3ac6007","id":"knowledge-digest-publication-contract-plan"}]`
- **输入**：accepted spec FR-PUB-001/002/007；当前 `validate_paths` 和 `kb_lock` 行为。
- **依赖**：N/A — first task
- **并行**：否 — 先固定行为失败，GREEN 才能实现。
- **FR**：FR-PUB-001、FR-PUB-002、FR-PUB-007
- **AC**：AC-01、AC-02、AC-04、AC-08
- **动作**：新增新库、非空旧库、结构冲突和旧库空输入的离线 acceptance 反例。
- **精确文件**：`tests/acceptance/test_publication_contract.py`
- **boundary**：files: `tests/acceptance/test_publication_contract.py`; symbols/regions: publication structure fixtures and filesystem assertions
- **输出**：当前实现下可重复的 RED 失败，且失败原因是目标发布合同缺失。
- **Knowledge**：当前 paths/lock 都要求目标 KB 与 `kb.structure.md` 已存在；空输入管线仍会触发审计写入。
- **verification_role**：RED
- **paired_task**：T002
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "initialization or structure or empty_input"'`
- **expected_exit**：1
- **oracle**：KD-PUB-STRUCTURE：只有新空库可创建声明/导航；非空无声明或冲突旧库零正式写入；旧库空输入零变化。
- **evidence_path**：`evidence/publication-contract/t001-red.txt`
- **STOP**：测试失败源自 fixture、环境或外部服务，而非当前发布合同缺失。
- **recovery**：保留失败输出，最小化 fixture 后重跑；不先改生产代码掩盖问题。
- **task risk**：把 `_digest` 运行报告误当正式读者文件，造成错误的零变化断言。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增真实文件系统反例，覆盖新库初始化、现有无效声明、路径冲突、旧库空输入、dry-run 与 batch 参数副作用。
- **executed_commands**：RED gate exit 1；修复后同一 gate 9 passed / exit 0；`git diff --check` exit 0。
- **evidence_refs**：`[{"ref":"receipts/revisions/implementation/4b3a2ba6360c633196a984a9ddbeca6f4df6b0f31d945293e715d171d58d3406.json","sha256":"9fb044e8eb47791fd7e3eb0ed97e3631c258c0b784ae6f5584f14481a09baec2"},{"ref":"receipts/phase-1-green-repair-tests.json","sha256":"8dca92d86b76be2213c6539eb032007229612e157669de77278d72a3780394c9"},{"ref":"reviews/results/build-code-default-05153529f94778da90504c5530bc62e165ac9a01-efcda754-affe-4c5a-9066-9df33afb37b7.json","sha256":"018860c89ab34f3fc45bd5465a9033c3aa145879a95dca506fdc8033152f1fed"}]`
- **covered_ac**：AC-04、AC-08；AC-01 的完整读者可达性和 AC-02 的托管主题更新由后续 Phase 继续覆盖。
- **review_fact**：`reviews/results/build-code-default-05153529f94778da90504c5530bc62e165ac9a01-efcda754-affe-4c5a-9066-9df33afb37b7.json`
- **completed_at**：2026-07-30T12:27:44Z

#### T002 — GREEN：安全发布声明与新库初始化

- **ID**：T002
- **Phase**：Phase 1：发布声明与空库初始化
- **goal**：实现最小发布声明、锁内新空库初始化和旧库 fail-loud 边界，使 T001 全部通过。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-publication-contract/plan.md","hash":"57138508386227a07df888d3c511d291cbd8f729fd4c8b5aaede1fbba3ac6007","id":"knowledge-digest-publication-contract-plan"}]`
- **输入**：T001 RED、SIG-001 CLI、SIG-002 paths、发布声明合同。
- **依赖**：T001
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-PUB-001、FR-PUB-002、FR-PUB-007
- **AC**：AC-01、AC-02、AC-04、AC-08
- **动作**：扩展结构解析、路径/锁/CLI/管线，固定“只准备目录容器 → 取得锁 → 锁内重验空目录 → 写声明/导航”的顺序；非空旧库只验证不猜测。
- **精确文件**：`src/knowledge_digest/kb_structure.py`、`src/knowledge_digest/paths.py`、`src/knowledge_digest/lock.py`、`src/knowledge_digest/cli.py`、`src/knowledge_digest/pipeline.py`
- **boundary**：files: `src/knowledge_digest/kb_structure.py`, `src/knowledge_digest/paths.py`, `src/knowledge_digest/lock.py`, `src/knowledge_digest/cli.py`, `src/knowledge_digest/pipeline.py`; symbols/regions: PublicationContract parsing, target initialization, single-writer entry
- **输出**：安全声明范围和新/旧 KB 分支，供后续布局和写回消费。
- **Knowledge**：默认声明必须有 `Home.md`、`indexes` 和唯一 pending；Why/version 门继续存在。目录容器不是正式输出；锁内若发现 lock 之外任意字节则失败。
- **verification_role**：GREEN
- **paired_task**：T001
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "initialization or structure or empty_input"'`
- **expected_exit**：0
- **oracle**：KD-PUB-STRUCTURE：只有新空库可创建声明/导航；非空无声明或冲突旧库零正式写入；旧库空输入零变化。
- **evidence_path**：`evidence/publication-contract/t002-green.txt`
- **STOP**：需要猜测非空旧库结构、在 dry-run 写入、或放宽 Why/version 门。
- **recovery**：停止本次初始化，保留 run 报告；只移除本次拥有且尚未正式发布的文件。
- **task risk**：目录容器准备与锁内正式初始化混淆，导致并发或半初始化。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：实现发布声明解析与安全路径验证；仅不存在或真正空目录可锁内初始化默认 `kb.structure.md`、Home 和 pending 分类；任何已有无效声明、冲突路径或额外旧文件写前失败；参数冲突不遗留新目录。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "initialization or structure or empty_input"` → 9 passed / exit 0；`py_compile` 与 `git diff --check` → exit 0。
- **evidence_refs**：`[{"ref":"receipts/revisions/implementation/4b3a2ba6360c633196a984a9ddbeca6f4df6b0f31d945293e715d171d58d3406.json","sha256":"9fb044e8eb47791fd7e3eb0ed97e3631c258c0b784ae6f5584f14481a09baec2"},{"ref":"receipts/phase-1-green-repair-tests.json","sha256":"8dca92d86b76be2213c6539eb032007229612e157669de77278d72a3780394c9"},{"ref":"reviews/results/build-code-default-05153529f94778da90504c5530bc62e165ac9a01-efcda754-affe-4c5a-9066-9df33afb37b7.json","sha256":"018860c89ab34f3fc45bd5465a9033c3aa145879a95dca506fdc8033152f1fed"}]`
- **covered_ac**：AC-04、AC-08；AC-01/AC-02 的主题发布部分保持未关闭。
- **review_fact**：`reviews/results/build-code-default-05153529f94778da90504c5530bc62e165ac9a01-efcda754-affe-4c5a-9066-9df33afb37b7.json`
- **completed_at**：2026-07-30T12:27:44Z

### Verify

- **Target**：FR-PUB-001、FR-PUB-002、FR-PUB-007；AC-01、AC-02、AC-04、AC-08。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "initialization or structure or empty_input"'`
- **expected_exit**：0
- **evidence_path**：`evidence/publication-contract/phase-1-structure.txt`
- **display_cmd**：N/A — pytest 输出足够。
- **Oracle**：KD-PUB-STRUCTURE。

### Knowledge

- 复用既有 `ValidationError`、`DigestPaths` 和单写者；发布声明只补充当前缺失字段。

### STOP

- 无法在不猜测非空旧库的前提下区分新/旧状态。
- 需要改动 LLM、embedding、batch 或原始设计文件。

### Done

- T001 的反例在 GREEN 后全部通过，且初始化/错误/空输入的正式文件行为可审计。

### Risks and rollback

- **Risk**：新库留下半成品。
- **Prevention**：锁内判断、预检和复用后续正式写回。
- **Rollback / recovery**：清理本次 owned 的未发布输出，不修改旧库。

## Phase 2：稳定可读主题页与导航

### Goal

托管主题保留稳定 ID，但首次发布生成可读标题/路径；Home 和分类索引只链接现行主题页，离线运行零外部调用。

### Files

- **NEW**：N/A — no new production file
- **MODIFY**：`src/knowledge_digest/identity.py`、`src/knowledge_digest/draft.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_publication_contract.py`
- **DO NOT TOUCH**：`src/knowledge_digest/llm.py`、`src/knowledge_digest/embedding.py`、`src/knowledge_digest/retrieve.py`

### Tasks

#### T003 — RED：可读命名、路径锁定和导航反例

- **ID**：T003
- **Phase**：Phase 2：稳定可读主题页与导航
- **goal**：证明当前 hash 路径和审计索引不能满足可读标题、稳定链接、读者导航与离线零外部调用合同。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-publication-contract/plan.md","hash":"57138508386227a07df888d3c511d291cbd8f729fd4c8b5aaede1fbba3ac6007","id":"knowledge-digest-publication-contract-plan"}]`
- **输入**：T002 GREEN、FR-PUB-003/004/006、当前 identity/layout 渲染行为。
- **依赖**：T002
- **并行**：否 — 发布范围先于读者输出。
- **FR**：FR-PUB-003、FR-PUB-004、FR-PUB-006
- **AC**：AC-03、AC-06
- **动作**：补充标题优先级、同名短 ID、锁定路径、Home/category 链接与禁服务 spy 的离线反例。
- **精确文件**：`tests/acceptance/test_publication_contract.py`
- **boundary**：files: `tests/acceptance/test_publication_contract.py`; symbols/regions: title/path/navigation/offline scenarios
- **输出**：当前 hash 标题、路径漂移或审计入口会触发的 RED 失败。
- **Knowledge**：`ingest._source_for/_snapshot` 已传递 `source_meta`/`input_path`；`draft()` 的 `publication_title_candidates` 固定为 source metadata `title` → 首个 Markdown H1 → 文件名，layout 再以前序已托管 H1 优先；无法分类固定进入 pending。
- **verification_role**：RED
- **paired_task**：T004
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "title or published_path or navigation or offline"'`
- **expected_exit**：1
- **oracle**：KD-PUB-READER：Home→category→topic 不入 `_digest`；标题可读、锁定路径稳定，零外部调用。
- **evidence_path**：`evidence/publication-contract/t003-red.txt`
- **STOP**：测试不能通过本地 fixture/spy 证明问题，或需要真实模型作为判据。
- **recovery**：缩小为确定性 Markdown fixture，保留 red 结果，不修改服务配置。
- **task risk**：把标题变化误实现为文件移动，破坏既有链接。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增标题优先级、可读路径、路径锁定、同名消歧和导航候选的离线反例；RED 为 3 failed。
- **executed_commands**：`uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "title or published_path or navigation or offline"` → RED 3 failed；GREEN 4 passed / exit 0。
- **evidence_refs**：`[{"ref":"receipts/revisions/implementation/ed4196d88dbff5368df50ee60cad09b19e6fd275888a573a81fdae1edaad4a84.json","sha256":"df564323e325d3ff063908fcc0b24ad420b6270df831191a6b7341dd2cbdde36"},{"ref":"receipts/phase-2-green-final-tests.json","sha256":"2d61dd33dfce7159b157158032f6fe1e693d22bcd2cd676786a4a966fdadd028"},{"ref":"reviews/results/build-code-default-0e91298df89500dfea0a2f10565a81b1f7f56b04-16079632-d149-4924-b74c-16eb89140cc3.json","sha256":"a76d34673b104e93e65b6c5661d51fabc1b091358380a28ab9c253ab5831e6ad"}]`
- **covered_ac**：AC-03、AC-06。
- **review_fact**：`reviews/results/build-code-default-0e91298df89500dfea0a2f10565a81b1f7f56b04-16079632-d149-4924-b74c-16eb89140cc3.json`
- **completed_at**：2026-07-30T12:52:27Z

#### T004 — GREEN：稳定身份上的可读主题与读者导航

- **ID**：T004
- **Phase**：Phase 2：稳定可读主题页与导航
- **goal**：以稳定 topic ID 更新，以首次锁定的可读路径发布主题页、Home 和分类导航，使 T003 通过。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-publication-contract/plan.md","hash":"57138508386227a07df888d3c511d291cbd8f729fd4c8b5aaede1fbba3ac6007","id":"knowledge-digest-publication-contract-plan"}]`
- **输入**：T003 RED、A-003/A-004/A-008/A-009、SIG-005/SIG-006、已验证 PublicationContract。
- **依赖**：T003
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-PUB-003、FR-PUB-004、FR-PUB-006
- **AC**：AC-03、AC-06
- **动作**：扩展 identity/draft/layout/pipeline：从现有 raw item fields 生成 `publication_title_candidates`，layout 以前序已托管 H1/候选生成 slug，输出 topic 与显式 `publication_audit_scope: none` navigation 草稿。
- **精确文件**：`src/knowledge_digest/identity.py`、`src/knowledge_digest/draft.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`
- **boundary**：files: `src/knowledge_digest/identity.py`, `src/knowledge_digest/draft.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/pipeline.py`; symbols/regions: `draft()` title candidate propagation, topic path renderer, navigation Publish record producer
- **输出**：可读托管 topic/pages 与导航候选；后续写回只消费这些受管目标。
- **Knowledge**：topic ID 语义不变；每页继续限制 300 行，Summary/Evidence/Provenance 完整。
- **verification_role**：GREEN
- **paired_task**：T003
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "title or published_path or navigation or offline"'`
- **expected_exit**：0
- **oracle**：KD-PUB-READER：Home→category→topic 不入 `_digest`；标题可读、锁定路径稳定，零外部调用。
- **evidence_path**：`evidence/publication-contract/t004-green.txt`
- **STOP**：需要调用 LLM/embedding、改变 ingestion schema，或用标题重命名已有锁定路径。
- **recovery**：保持现有 topic ID 和归档，停止本次发布，返回计划处理未知 schema。
- **task risk**：Unicode/同名 slug 碰撞导致不同主题覆盖。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：实现本地标题候选、Unicode 可读 slug、同名稳定消歧、托管页头和首次路径锁定；生成 Home 与分类导航 run artifact，留给 Phase 3 统一写回。
- **executed_commands**：聚焦 gate 4 passed；`tests/acceptance/test_publication_contract.py` 13 passed；`git diff --check` exit 0。
- **evidence_refs**：`[{"ref":"receipts/revisions/implementation/ed4196d88dbff5368df50ee60cad09b19e6fd275888a573a81fdae1edaad4a84.json","sha256":"df564323e325d3ff063908fcc0b24ad420b6270df831191a6b7341dd2cbdde36"},{"ref":"receipts/phase-2-green-final-tests.json","sha256":"2d61dd33dfce7159b157158032f6fe1e693d22bcd2cd676786a4a966fdadd028"},{"ref":"reviews/results/build-code-default-0e91298df89500dfea0a2f10565a81b1f7f56b04-16079632-d149-4924-b74c-16eb89140cc3.json","sha256":"a76d34673b104e93e65b6c5661d51fabc1b091358380a28ab9c253ab5831e6ad"}]`
- **covered_ac**：AC-03、AC-06；Home/index 正式原子写入与旧主题导航保留由 Phase 3 关闭。
- **review_fact**：`reviews/results/build-code-default-0e91298df89500dfea0a2f10565a81b1f7f56b04-16079632-d149-4924-b74c-16eb89140cc3.json`
- **completed_at**：2026-07-30T12:52:27Z

### Verify

- **Target**：FR-PUB-003、FR-PUB-004、FR-PUB-006；AC-03、AC-06。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "title or published_path or navigation or offline"'`
- **expected_exit**：0
- **evidence_path**：`evidence/publication-contract/phase-2-reader-output.txt`
- **display_cmd**：N/A — pytest 输出足够。
- **Oracle**：KD-PUB-READER。

### Knowledge

- 只使用本地已声明内容；分类不能判定时进入 pending，而不是猜测语义。

### STOP

- 需要 LLM/embedding 或真实网络；无法保留稳定 topic ID 和锁定路径。

### Done

- T003 的本地 reader 反例全绿，首页和分类导航不复制正文且不引用审计目录。

### Risks and rollback

- **Risk**：标题/文件名冲突或路径漂移。
- **Prevention**：固定优先级、短稳定后缀、前后路径一致性断言。
- **Rollback / recovery**：保留已托管旧路径和归档，停止本次输出。

## Phase 3：托管边界与无删除发布事务

### Goal

只把受管、路径匹配的主题页作为候选；主题、Home 和分类索引原子发布；收缩分页不删除或改写旧 part。

### Files

- **NEW**：N/A — no new production file
- **MODIFY**：`src/knowledge_digest/retrieve.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`、`tests/acceptance/test_publication_contract.py`
- **DO NOT TOUCH**：`src/knowledge_digest/provenance.py`、`src/knowledge_digest/jsonl.py`、`src/knowledge_digest/batch_run.py`

### Tasks

#### T005 — RED：手写页保护、分页留存和事务失败反例

- **ID**：T005
- **Phase**：Phase 3：托管边界与无删除发布事务
- **goal**：证明当前全目录读取和 obsolete page 删除会破坏旧库托管边界与无删除合同。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-publication-contract/plan.md","hash":"57138508386227a07df888d3c511d291cbd8f729fd4c8b5aaede1fbba3ac6007","id":"knowledge-digest-publication-contract-plan"}]`
- **输入**：T004 GREEN、A-005/A-006、旧库 topic/Home/category fixtures。
- **依赖**：T004
- **并行**：否 — 可读输出稳定后才收紧更新边界。
- **FR**：FR-PUB-002、FR-PUB-004、FR-PUB-005
- **AC**：AC-02、AC-04、AC-05、AC-07
- **动作**：增加手写页/声明外页 byte 不变、伪造页头失败、写入失败回滚、分页收缩旧 part 留存，以及 Home/category 不复制正文/Claim/Evidence/Provenance、无 Claim history 的反例。
- **精确文件**：`tests/acceptance/test_publication_contract.py`
- **boundary**：files: `tests/acceptance/test_publication_contract.py`; symbols/regions: managed ownership, shrink, transaction and provenance scenarios
- **输出**：当前扫描/删除行为触发的 RED 失败和精确 byte 比较。
- **Knowledge**：`retrieve._page_records()` 扫描所有 Markdown；`writeback()` 的 `obsolete_target_paths` 会进入 remove path。
- **verification_role**：RED
- **paired_task**：T006
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "managed or handwritten or shrink or transaction or provenance"'`
- **expected_exit**：1
- **oracle**：KD-PUB-SAFE-WRITE：未托管页零变更；旧 part 原字节保留；失败无部分正式页；topic 保留质量段落和溯源；Home/category 只有链接且无 Provenance/Claim history。
- **evidence_path**：`evidence/publication-contract/t005-red.txt`
- **STOP**：不能用字节比较证明保护边界，或必须通过删除历史 part 才能让测试通过。
- **recovery**：保留 red 输出；缩小合成旧库 fixture，不接触真实 KB。
- **task risk**：测试只检查主题正文而遗漏 Home/category 的部分写。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：新增手写页保护、旧主题导航保留、分页收缩无删除、统一事务和 topic-only provenance/history 反例。
- **executed_commands**：聚焦 gate 初始 RED 4 failed / 2 passed；修复后 9 passed / exit 0。
- **evidence_refs**：`[{"ref":"receipts/revisions/implementation/ec9c26b11bf81aeaf1eec9c519ef1992b62c763cfa3fd8e783e9267eaf1705b2.json","sha256":"409123a93814f2bbb32d8a2bab1915bde9bf3c6353a39a8b84bc06766b1896ba"},{"ref":"receipts/phase-3-green-tests.json","sha256":"c24de36955daca2924ccb0961c3a6c58981572254cf02ba1354525404714cfb3"},{"ref":"reviews/results/build-code-default-c0f377c5bbdd81e3bdd2d2d4f3755d61b359768b-035213c6-dcbe-45dd-b89a-d500f1810136.json","sha256":"6d4d6a1c7b3395f48f5f995c6808d80c2b7903c84400a979c99e4cf16a0d39ce"}]`
- **covered_ac**：AC-02、AC-04、AC-05、AC-07。
- **review_fact**：`reviews/results/build-code-default-c0f377c5bbdd81e3bdd2d4f3755d61b359768b-035213c6-dcbe-45dd-b89a-d500f1810136.json`
- **review_fact**：`{"ref":"reviews/results/build-code-default-c0f377c5bbdd81e3bdd2d2d4f3755d61b359768b-035213c6-dcbe-45dd-b89a-d500f1810136.json"}`
- **completed_at**：2026-07-30T13:09:17Z

#### T006 — GREEN：托管候选过滤与无删除写回

- **ID**：T006
- **Phase**：Phase 3：托管边界与无删除发布事务
- **goal**：让 retrieve 只消费受管主题，并让 writeback 将所有正式读者输出预检、归档、原子写与回滚，保留旧 part。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-publication-contract/plan.md","hash":"57138508386227a07df888d3c511d291cbd8f729fd4c8b5aaede1fbba3ac6007","id":"knowledge-digest-publication-contract-plan"}]`
- **输入**：T005 RED、发布结构合同、当前导航草稿与 writeback rollback 行为。
- **依赖**：T005
- **并行**：否 — RED/GREEN 必须串行。
- **FR**：FR-PUB-002、FR-PUB-004、FR-PUB-005
- **AC**：AC-02、AC-04、AC-05、AC-07
- **动作**：扩展 retrieve/writeback/layout/pipeline，按 topic/navigation Publish record 预检、归档、原子写/回滚；navigation `layout_finalized: true`、`claims: []`、`publication_audit_scope: none`，不追加 Provenance、不传 audit/history；移除旧 part 删除分支。
- **精确文件**：`src/knowledge_digest/retrieve.py`、`src/knowledge_digest/writeback.py`、`src/knowledge_digest/page_layout.py`、`src/knowledge_digest/pipeline.py`
- **boundary**：files: `src/knowledge_digest/retrieve.py`, `src/knowledge_digest/writeback.py`, `src/knowledge_digest/page_layout.py`, `src/knowledge_digest/pipeline.py`; symbols/regions: page candidate filter, topic/navigation Publish record preflight, audit/history exclusion, obsolete part retention, navigation integration
- **输出**：只更新允许文件的正式发布批；旧 part 和手写页未改动。
- **Knowledge**：复用 `_archive` 和 `_digest/source-index.md`；后者继续审计，不替代读者导航。
- **verification_role**：GREEN
- **paired_task**：T005
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "managed or handwritten or shrink or transaction or provenance"'`
- **expected_exit**：0
- **oracle**：KD-PUB-SAFE-WRITE：未托管页零变更；旧 part 原字节保留；失败无部分正式页；现行页保留质量段落和溯源。
- **evidence_path**：`evidence/publication-contract/t006-green.txt`
- **STOP**：需要删除、接管手写文件、改 provenance/jsonl/batch，或不能预检全部正式目标。
- **recovery**：使用既有 archive/rollback 恢复已覆盖托管页；保留旧 part；返回计划处理边界扩大。
- **task risk**：只预检 topic 页或把导航误送 audit/history，导致半完成导航或伪造 Provenance。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：retrieve 与 embedding prefetch 仅消费声明内合法托管 topic；导航合并未更新旧主题并保留原分类；Home/category/topic 统一预检、归档、原子写和回滚；旧 part 不删除、不改写，只退出当前导航。
- **executed_commands**：Phase 3 gate 9 passed；publication contract 21 passed；embedding runtime 32 passed；compile 与 `git diff --check` exit 0。
- **evidence_refs**：`[{"ref":"receipts/revisions/implementation/ec9c26b11bf81aeaf1eec9c519ef1992b62c763cfa3fd8e783e9267eaf1705b2.json","sha256":"409123a93814f2bbb32d8a2bab1915bde9bf3c6353a39a8b84bc06766b1896ba"},{"ref":"receipts/phase-3-green-tests.json","sha256":"c24de36955daca2924ccb0961c3a6c58981572254cf02ba1354525404714cfb3"},{"ref":"reviews/results/build-code-default-c0f377c5bbdd81e3bdd2d2d4f3755d61b359768b-035213c6-dcbe-45dd-b89a-d500f1810136.json","sha256":"6d4d6a1c7b3395f48f5f995c6808d80c2b7903c84400a979c99e4cf16a0d39ce"}]`
- **covered_ac**：AC-02、AC-04、AC-05、AC-07。
- **review_fact**：`{"ref":"reviews/results/build-code-default-c0f377c5bbdd81e3bdd2d2d4f3755d61b359768b-035213c6-dcbe-45dd-b89a-d500f1810136.json"}`
- **completed_at**：2026-07-30T13:09:17Z

### Verify

- **Target**：FR-PUB-002、FR-PUB-004、FR-PUB-005；AC-02、AC-04、AC-05、AC-07。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py -k "managed or handwritten or shrink or transaction or provenance"'`
- **expected_exit**：0
- **evidence_path**：`evidence/publication-contract/phase-3-safe-write.txt`
- **display_cmd**：N/A — pytest 输出足够。
- **Oracle**：KD-PUB-SAFE-WRITE。

### Knowledge

- 每个正式目标先由同一批 preflight 验证；旧 part 仅退出现行导航，不能写入 remove path。

### STOP

- 必须删除旧文件、接管手写页或扩大到 provenance/jsonl/batch。
- 原子失败后无法证明所有正式文件恢复。

### Done

- T005 的保护、留存和事务反例全绿；每个现行主题页保持 Summary、Evidence、Provenance 和 300 行上限。

### Risks and rollback

- **Risk**：主题和导航不同步。
- **Prevention**：全部正式目标预检，覆盖先归档，失败走 rollback。
- **Rollback / recovery**：从本 run archive 恢复托管文件；不动历史 part 和手写页。

## Phase 4：契约回归与维护入口

### Goal

让测试和项目维护说明使用新发布合同，完整离线回归证明旧质量门未退化。

### Files

- **NEW**：N/A — non-behavior alignment only
- **MODIFY**：`tests/acceptance/test_architecture_optimization.py`、`AGENTS.md`、`CONTEXT.md`
- **DO NOT TOUCH**：`docs/plans/universal-knowledge-digest-design.md`、`config/knowledge-digest.json`、`pyproject.toml`

### Tasks

#### T007 — N/A：维护入口与历史回归对齐

- **ID**：T007
- **Phase**：Phase 4：契约回归与维护入口
- **goal**：将既有架构回归和维护文档对齐已实现的读者发布合同，并完成最终离线测试。
- **design_state**：ready
- **versioned_refs**：`[{"artifact_kind":"spec","ref":"specs/knowledge-digest-publication-contract/spec.md","hash":"8b50d8f84a94dba5d659b3a5b9333901b96cc29c069d71e02b39d1ce3f8771df","id":"knowledge-digest-publication-contract"},{"artifact_kind":"plan","ref":"specs/knowledge-digest-publication-contract/plan.md","hash":"57138508386227a07df888d3c511d291cbd8f729fd4c8b5aaede1fbba3ac6007","id":"knowledge-digest-publication-contract-plan"}]`
- **输入**：T006 GREEN、AGENTS 更新规则、当前架构回归假设。
- **依赖**：T006
- **并行**：否 — 仅在发布边界和最终文件名确定后同步。
- **FR**：FR-PUB-004（回归确认；主实现证据在 T004/T006）
- **AC**：AC-07（回归确认；主证据是 KD-PUB-SAFE-WRITE）
- **动作**：更新历史回归的公开路径断言与维护说明，不改变生产行为。
- **精确文件**：`tests/acceptance/test_architecture_optimization.py`、`AGENTS.md`、`CONTEXT.md`
- **boundary**：files: `tests/acceptance/test_architecture_optimization.py`, `AGENTS.md`, `CONTEXT.md`; symbols/regions: output-contract assertions, reader entry and update guidance
- **输出**：可维护的读者发布说明和覆盖新旧合同的全量离线回归证据。
- **Knowledge**：原始设计文件保留不改；`AGENTS.md` 要求输出/CLI/质量门改变时同步维护说明。
- **verification_role**：N/A — non-behavior change: documentation and historical regression alignment after behavior pairs are green
- **paired_task**：N/A — non-behavior change: no reciprocal implementation task
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py tests/acceptance/test_architecture_optimization.py && uv run --frozen pytest -q'`
- **expected_exit**：0
- **oracle**：KD-PUB-REGRESSION：发布合同与既有质量回归全绿，维护文档准确描述实际入口和边界。
- **evidence_path**：`evidence/publication-contract/t007-regression.txt`
- **STOP**：文档与实现无法一致，或完整回归需要 File Boundary 外的新生产改动。
- **recovery**：保留失败输出，回到导致偏差的 GREEN 任务；不通过改文案掩盖行为差异。
- **task risk**：历史测试仍只验证审计 hash 路径，漏掉读者导航退化。

##### 执行状态填写区（唯一完成权威）

- [x] **任务完成**
- **status**：`completed`
- **actual_changes**：更新 AGENTS/CONTEXT 的知识发布入口和无删除边界；架构回归改按声明目录与托管页头发现主题；迁移 7 组旧 acceptance fixture 到有效 publication 声明，未改变原测试业务断言。
- **executed_commands**：任务核心 31 passed；7 组历史回归 176 passed；任务 worktree 全量 275 passed；`git diff --check` exit 0。
- **evidence_refs**：`[{"ref":"receipts/revisions/implementation/a2f139ed0362a5bd613c458bc326fc243e0806395cec22b1b0dfa012e45fd55e.json","sha256":"b3f3cacfa3b25950427756418c8bbdd4757f1bf73de57a7617c8217b61c47f7f"},{"ref":"receipts/phase-4-green-bound-tests.json","sha256":"f81871425df24ce158988aee01848ac10af054af37e5daeb055078561642a240"},{"ref":"reviews/results/build-code-default-c97247f4a26a4e336196aa2770dc774a60bade9e-152a34f5-9440-47f3-8e49-561f81573589.json","sha256":"f593b626819b77c5dd71f0805bc5be8372dfc4328f2ca65c9d39b4be695b00d6"}]`
- **covered_ac**：AC-07 回归确认；主行为证据仍由 Phase 2/3 提供。
- **review_fact**：`{"ref":"reviews/results/build-code-default-c97247f4a26a4e336196aa2770dc774a60bade9e-152a34f5-9440-47f3-8e49-561f81573589.json"}`
- **completed_at**：2026-07-30T13:32:49Z

### Verify

- **Target**：FR-PUB-004、AC-07 的回归确认；主行为证据仍在 KD-PUB-READER / KD-PUB-SAFE-WRITE。
- **gate_cmd**：`bash -lc 'uv run --frozen pytest -q tests/acceptance/test_publication_contract.py tests/acceptance/test_architecture_optimization.py && uv run --frozen pytest -q'`
- **expected_exit**：0
- **evidence_path**：`evidence/publication-contract/final-regression.txt`
- **display_cmd**：N/A — pytest 输出足够。
- **Oracle**：KD-PUB-REGRESSION。

### Knowledge

- 文档只解释已有实现和已接受边界，不重写原始设计或扩大为 Task 2。

### STOP

- 新旧命令/输出无法在维护入口中诚实表达，或完整测试有未计划生产依赖。

### Done

- 文档、目标 acceptance 和全量 pytest 全绿；未声称 LLM 标题或旧库迁移已实现。

### Risks and rollback

- **Risk**：文档掩盖实际行为差异。
- **Prevention**：文档以 green 代码和最终离线命令为唯一事实源。
- **Rollback / recovery**：先修行为和测试，再同步文档；原始设计不变。

## 3. Dependency Graph

```text
T001 (RED) → T002 (GREEN) → T003 (RED) → T004 (GREEN) → T005 (RED) → T006 (GREEN) → T007 (N/A)
```

- 每个依赖均先于消费者，图无环。
- 本任务没有可安全并行的代码任务：后续阶段依赖前一阶段的发布合同与实际文件形状。

## 4. Requirement and Verification Traceability

| FR | Task IDs | AC IDs | Phase | Gate / evidence |
| --- | --- | --- | --- | --- |
| FR-PUB-001 | T001、T002 | AC-01、AC-08 | Phase 1 | KD-PUB-STRUCTURE |
| FR-PUB-002 | T001、T002、T005、T006 | AC-02、AC-04 | Phase 1、3 | KD-PUB-STRUCTURE / SAFE-WRITE |
| FR-PUB-003 | T003、T004 | AC-03 | Phase 2 | KD-PUB-READER |
| FR-PUB-004 | T003、T004、T005、T006；T007 仅回归确认 | AC-01、AC-02、AC-04、AC-07 | Phase 2、3；Phase 4 仅确认 | KD-PUB-READER / SAFE-WRITE（主证据） |
| FR-PUB-005 | T005、T006 | AC-05、AC-07 | Phase 3 | KD-PUB-SAFE-WRITE |
| FR-PUB-006 | T003、T004 | AC-06 | Phase 2 | KD-PUB-READER |
| FR-PUB-007 | T001、T002 | AC-01、AC-08 | Phase 1 | KD-PUB-STRUCTURE（主证据） |

## 5. Final Boundary Check

- [x] 每个 Phase 八段完整，且 Files 与 plan 逐字一致。
- [x] 每个 Task 只有一张权威卡，精确文件属于本 Phase NEW/MODIFY。
- [x] 每个行为变化都有真实 RED → GREEN，命令、oracle 和证据明确。
- [x] DAG 与 FR/Task/AC/gate 双向闭合。
- [x] Plan File Boundary 等于所有 Phase NEW/MODIFY 的并集。
- [x] 每个 Phase NEW/MODIFY 文件至少有一个 owning Task。
- [x] 每个 Task 的精确文件和 boundary 都是所属 Phase NEW/MODIFY 的子集。
- [x] 每个 Task 只有一个完成区，所有完成字段保持 pending。
- [x] 没有 host identity、固定 artifact root、无关项目规则或未声明文件。
