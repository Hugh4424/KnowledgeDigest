# 实现计划：Task 2-C 信任信号与小语料 Agent 读者质量门

- **Input**：`specs/task2c-knowledge-publication-trust-reader-quality/decision-log.md`、`specs/task2c-knowledge-publication-trust-reader-quality/spec.md`
- **Template version**：`plan-task.v3`

## Quick Read

- **Goal**：在既有 Reader Bundle 上投影单一事实源的读者信号，并用冻结小题集做 Reader-only Agent 质量门；结果可回放，整包仍为 `not_released`。
- **Non-goals**：不做 89 条全量读者门、不改 Task 2-A/2-B 正文合同、不做正式 `released`、人工评审队列、trust score、数据库、向量库、CLI/调度器（来源：D-001、D-003～D-006；spec §10）。
- **Before**：`reader_bundle.py` 已生成 `generated`、`digest_machine_pass`、`verified`、`stale_after` 和 Audit 信号文件，并以原子提交保护 Reader Bundle；还没有 Task 2-C 的信号索引投影、冻结题集派生、Agent scorecard 和完整 exit manifest。
- **After**：入口索引和页头能看到 type/description/source count/generated/trust/lifecycle；质量门只读 Reader Package，正向至少 8 题全命中、3 个负向零误命中，答案和来源链同时成立；失败不覆盖旧包。
- **Main risk**：Agent 自评可能把自己生成的正文误判为可读；必须保存 Agent-only 标记、Reader 输入指纹、提示/模型/seed/hash、失败样本和来源回查结果（RISK-01）。
- **Next step**：按 P1 顺序执行 T001→T006，再执行一次 T007 聚合验证；build-code 不得临时补需求或扩大文件边界。

## Technical Context

### Global Constraints

- **Verified facts**：Task 2-B 已交付 commit `2369a853adb4bc70709036c563233cae361222be`，与 `origin/main` 一致；真实 `qwen3.6` 语义出口有 12 个 concept `machine-passing`，delivery `not_released`；Task1 focused、消费者和全量回归及 diff check 均已有记录。详情与 hash 已记录在 spec PFACT-001 和 decision-log handoff。
- **Language / runtime**：Python `src-layout`；命令使用 `uv run --frozen`；测试使用 pytest；时间写入 UTC ISO-8601，stale 使用 `YYYY-MM-DD`。
- **Primary dependencies**：复用 `reader_bundle.py` 的结构投影、原子提交和验证；复用 `reader_frontmatter.py` 的解析/序列化/hash；复用 `llm.py:call_llm` 及既有 qwen3.6 常量。Task 2-C 不改 provider 常量或凭据读取。
- **Storage / state**：Reader Bundle 写入 `bundle/`；逐题、scorecard、失败原因和 exit manifest 写入 Audit/Reports；通过临时 staging 和单写者锁保护已有正式包。无数据库或新持久化服务。
- **Testing**：测试是本地 acceptance slice；Agent provider 在测试中用可控 fake `call_llm`，不发送凭据或真实正文到外部服务；最终命令覆盖 Task2C 与 Task2A Reader Bundle 回归。路由顾问实测输出 `fullstack`，原因是 `src/` 与 `tests/` 跨顶层边界；实际不涉及 HTTP/DB。
- **Target environment**：macOS 本地 KnowledgeDigest 仓库；真实语义运行只允许项目既定 `qwen3.6`/approved endpoint，凭据仅来自环境变量；离线测试不得探测 provider。
- **Scale / scope**：一次性小语料，正向至少 8、负向 3；至少 2 个 product/module、2 类 page type；Task1 inventory 的 long/table-image/bilingual/multi-source/failed-degraded 类别逐项覆盖或记录 machine fixture+排除理由。
- **Unresolved facts**：Task 3 是否继承 Agent-only 未决，由 Task 3 `make-decision` 决定；本计划不推导。provider 的真实网络重跑不属于本阶段 acceptance gate，若需要在 verify-code 另行记录真实可用性。

## Code Anchors

- **Verified anchors**：`src/knowledge_digest/reader_bundle.py:project_reader_bundle` 负责 staging、页面、索引、Audit 和 exit；`validate_reader_bundle` 负责 fail-closed 验证；`_trust_events`、`_validate_trust_signals` 负责现有机器信号；`_atomic_commit` 负责三面原子提交。`src/knowledge_digest/reader_frontmatter.py:parse_concept_document`、`serialize_concept_document`、`managed_content_hash` 是页面事实边界。`src/knowledge_digest/llm.py:call_llm` 是已有模型调用窄接口。`src/knowledge_digest/lock.py:kb_lock` 是现有单写者锁。
- **Existing interfaces**：`BundleArtifactPaths.from_root(Path)`、`project_reader_bundle(inputs, artifacts) -> CommittedBundleRun`、`validate_reader_bundle(artifacts, expected) -> BundleValidationReport`；`call_llm(prompt, api_format, base_url, api_key, model, timeout=..., max_tokens=...) -> str`。新模块只接受 Reader Bundle 路径、冻结题集路径和窄配置，不把 Audit 内容传给 Agent。
- **Read now**：`reader_bundle.py` 的数据类、页面/索引写入段、trust 校验段；`reader_frontmatter.py`；`llm.py` provider contract；Task2A acceptance fixture/helper；`config/task0-question-set.v1.json` 与 Task0 runtime audit。
- **Must read before task**：执行 T002 前读取 T001 失败输出和上述实现锚点；执行 T004/T006 前读取 paired RED 的字段缺口；如实际签名、页面结构或 Task0 schema 不符，STOP 回 plan/spec，不在 build-code 猜测。
- **Context mode**：Full — 任务同时跨 Reader Bundle、质量证据和回归测试，但限定在一个 Phase 与三组 producer/consumer。

### Reuse → Extend → New

| Capability | Decision | Existing anchor | Reason / removal condition |
| --- | --- | --- | --- |
| Reader 页面/索引投影 | extend | `reader_bundle.py:project_reader_bundle` | 保持单一事实源；若另建投影会产生第二套导航事实，禁止。 |
| 机器信号与来源回查 | reuse | `reader_bundle.py:_trust_events`, `validate_reader_bundle` | 已有 fingerprint、locator、Audit 校验；只补读者可见映射，不复制权威。 |
| 页面解析与 hash | reuse | `reader_frontmatter.py` | 保持现有 managed hash 和兼容边界。 |
| Agent 题集/scorecard | new | `reader_quality.py`（本任务新 consumer） | Task2C 需要 Reader-only 输入隔离、逐题回放和门结果；若 Task3 不复用，仅保留可独立删除模块。 |
| 模型调用 | reuse | `llm.py:call_llm` | 不修改 provider、key 读取或模型常量；测试用注入 fake。 |
| 质量门 acceptance | new | `tests/acceptance/test_task2c_reader_quality.py` | 需要覆盖小样本、Reader-only、防伪造字段、来源链、失败隔离和 replay。 |

## Solution Design

### Overview

P1 先在现有 `project_reader_bundle` 的页面/索引写入链中补齐信号投影：页面已有的 `generated`、机器验证事件、来源 fingerprint、stale 和 page status 作为事实；由同一投影函数派生可读 trust/lifecycle 文本，写入入口索引及页头可见区域。`unverified`、stale、deprecated 只分别提示，不自行变成 `degraded`；必需事实源不一致、来源链断裂或机器门失败才降级并退出导航。

随后 `reader_quality.py` 从 Task0 冻结题集按确定性规则选出 Task2C 小样本，检查 product/module、page type 和 Task1 inventory 覆盖。Agent 只接收 Reader Package 的 Home、索引和 concept 正文，并返回结构化答案判断；程序保存题目、首命中页、跳转、答案、边界/版本、来源回查、失败原因、输入 hash、模型/提示/seed/hash 和三项 Agent-only 标记。Audit/Archive 只用于事后验证，不进入 Agent prompt。

最后质量门一次性写入 scorecard、失败记录、门结果和 exit manifest；任何字段缺失、题集不足、正向未命中、负向误命中、来源断裂、不可回放或 provider 失败都保持 `not_released`，并通过单写者/临时 staging 不覆盖旧 Reader Bundle。

### Module responsibilities

#### Reader signal projection

- **Responsibility**：从已有 Reader/Audit 事实派生入口可见的 type、description、source count、generated.at、trust tier、status、stale/deprecated 提示，并过滤明确 degraded 页面。
- **Consumes**：`ReaderBundleInputs`、已生成 frontmatter、trust Audit 和 page body。
- **Produces**：同一 Bundle 内的索引/页头投影、可重算的 projection fields、明确 `published/degraded` 导航结果。
- **Must not decide**：不决定 Claim/Evidence/Provenance、不创建 Agent/human trust event、不把 Task2C 通过变成 `released`。

#### Agent reader quality gate

- **Responsibility**：从冻结 Task0 题集确定性派生小样本，隔离 Reader-only 输入，执行 Agent 评分并计算门结果。
- **Consumes**：Reader Package 文件、Task0 题集标签/规则、固定 seed/阈值、环境 provider 配置。
- **Produces**：逐题 `ReaderQuestionRecord`、scorecard、失败样本、`QualityGateResult` 和 exit manifest 输入。
- **Must not decide**：不从 Audit/Archive 找答案，不修改 Reader 正文，不写 `human_reviewed`、`verified`、`machine-confirmed` 或新的 trust tier。

#### Runtime isolation and exit

- **Responsibility**：保证取消、重跑、并发和失败不会覆盖旧包，并冻结 Task2C 出口状态。
- **Consumes**：已有 staging/atomic commit/lock 能力和质量门结果。
- **Produces**：稳定 replay projection、`not_released` exit manifest、失败可恢复的 Audit/Reports。
- **Must not decide**：不做后台调度、不创建第二事实源、不绕过现有页面验证。

### Interfaces, data, and lifecycle

- **Interfaces / schemas**：新增模块提供 `derive_task2c_questions(question_set_path, reader_manifest, *, seed) -> tuple[ReaderQuestion, ...]` 和 `run_reader_quality_gate(bundle_dir, question_set_path, output_dir, *, config, llm_call=None) -> QualityGateResult`；内部记录必须包含 spec FR-GATE-002 的全部字段和 `agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`。现有页面 frontmatter/Reader Bundle schema 保持兼容。
- **Data flow / state**：冻结题集 → 确定性覆盖检查 → Reader-only snapshot/hash → Agent 逐题结果 → 来源回查 → scorecard → `passed/not_released` 或 `failed/not_released` exit；写入失败回滚 staging，旧包不变。
- **API contract**：N/A — 这是本地 Python programmatic API，不新增 HTTP/CLI endpoint；Task 3 如需 CLI 需重新决策。
- **UI / external code**：无 UI；Reader Markdown 入口需在不打开正文时显示信号。可访问性沿用普通 Markdown 标题和链接，不引入客户端 hook。
- **Fail-loud behavior**：题集 schema、覆盖、Reader-only 边界、Agent JSON、字段、来源链、输入 hash、预算或 replay 任一无效即明确失败；不得用 provider 成功、lint 或模型自由文本伪装通过。

## File Boundary

### NEW

- `src/knowledge_digest/reader_quality.py`
- `tests/acceptance/test_task2c_reader_quality.py`

### MODIFY

- `src/knowledge_digest/reader_bundle.py`

### DO NOT TOUCH

- `src/knowledge_digest/pipeline.py`、`src/knowledge_digest/cli.py`、`src/knowledge_digest/publication.py`：本任务是隔离的 Reader Bundle quality slice，不扩大到正式 S1-S6/CLI。
- `src/knowledge_digest/identity.py`、`src/knowledge_digest/topic_axis.py`：不改变 TopicIndex 身份和 Task1 事实。
- `src/knowledge_digest/reader_frontmatter.py`、`src/knowledge_digest/llm.py`、`src/knowledge_digest/lock.py`：已有窄接口足够，避免无必要 schema/provider/锁改动。
- `config/task0-question-set.v1.json`：冻结输入只读，不临时改题。
- `tests/acceptance/test_task2a_reader_bundle.py` 及 `tests/fixtures/task2a_reader_bundle/`：保留 Task2A 回归基线。
- `apply/evidence/`、Task2B commit/evidence：只读交接事实，不重新生成或篡改。

## Technical Decisions

### DEC-001 — 在既有 Reader Bundle 中扩展信号投影

- **Problem**：读者需要在入口看到信任与生命周期，但新增独立投影会制造第二事实源。
- **Options**：A 复用并扩展 `reader_bundle.py`；B 在新模块复制页面/索引写入；C 只写 Audit 不给读者看。
- **Selected**：A，extend。
- **Reason**：最小改动，保留已有 page/Audit/hash/atomic commit 事实链。
- **Consequence / risk**：一个文件职责变重；用窄内部 helper 和 acceptance seam 限制影响。
- **Fallback**：信号无法重算则 fail-closed/degraded，不降级为静态猜测。
- **F10 real threat**：新独立投影重复序列化、校验和导航事实。
- **F10 existing cover**：现有 `project_reader_bundle`、`validate_reader_bundle` 已覆盖生成/验证/提交。
- **F10 bypassable**：通过单独函数覆盖新增字段，不需要第二 pipeline。
- **F10 maintenance cost**：低于复制一套 Bundle writer。
- **F10 disposition**：`keep`

### DEC-002 — 新增独立 Agent 质量门模块，但不接正式 pipeline/CLI

- **Problem**：Task2C 需要逐题可回放、Reader-only 和 Agent-only 证据，现有 Bundle writer 没有这个职责。
- **Options**：A 新建 `reader_quality.py` programmatic slice；B 把题集和 Agent 逻辑塞进 `reader_bundle.py`；C 扩大正式 pipeline/CLI。
- **Selected**：A，new。
- **Reason**：职责窄、可注入 fake、可独立删除/由 Task3 决定是否复用，不改变正式发布链。
- **Consequence / risk**：新增一个模块和公共入口，需避免变成第二状态机；所有写入只从一个 quality result 进入 exit。
- **Fallback**：provider/解析/来源回查失败统一 `not_released`，保留失败记录。
- **F10 real threat**：模块如果复制 Claim/Evidence 逻辑会产生维护分叉。
- **F10 existing cover**：复用 Reader Bundle 的页面读法、frontmatter parser 和既有 source/claim 链。
- **F10 bypassable**：新模块只做题集、prompt 隔离、scorecard，不重写正文编译。
- **F10 maintenance cost**：中等；由 Task3 决定继承或删除，不引入长期服务。
- **F10 disposition**：`keep`

### DEC-003 — 测试使用 fake provider，真实 provider 只留给受控运行

- **Problem**：测试必须证明输入隔离和失败边界，不能依赖网络、密钥或模型偶然输出。
- **Options**：A 注入 fake `call_llm` 做 acceptance；B 每次测试调用真实 qwen3.6；C 不测 Agent，只测静态字段。
- **Selected**：A，reuse interface + test seam。
- **Reason**：可确定复现，同时保留真实运行时使用 approved provider 的契约。
- **Consequence / risk**：fake 不能证明模型本身质量；该风险在 verify-code/Task3 继续单独记录，不假装已关闭。
- **Fallback**：fake 返回非 JSON、缺字段、补充 Audit 答案等负例，门必须失败。
- **F10 real threat**：为测试引入 provider mock framework 或持久服务。
- **F10 existing cover**：普通 callable 注入即可。
- **F10 bypassable**：不改 `llm.py`，不新增依赖。
- **F10 maintenance cost**：低。
- **F10 disposition**：`keep`

## Test Strategy

设计 RED/GREEN，不在 build-plan 执行命令。路由顾问当前实测为 `fullstack`；执行时使用 `fullstack-slice-testing` 语义，但测试仍是本地 acceptance，不启动 HTTP/DB。

| Target | Task | Role | gate_cmd / expected_exit | Oracle / evidence_path |
| --- | --- | --- | --- | --- |
| FR-SIGNAL-001/002、FR-LIFE-001、FR-STATUS-001、AC-01～03、AC-07 | T001/T002 | RED/GREEN | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` / RED 非零、GREEN 0 | `ORACLE-SIGNAL-LIFECYCLE`：入口信号齐全、事件不伪造、stale/deprecated 不误降级、失败页退出导航；`quality/evidence/T001-signal-lifecycle-red.txt` + `quality/evidence/T002-signal-lifecycle-green.txt` |
| FR-GATE-001～003、FR-READER-002、AC-04～06 | T003/T004 | RED/GREEN | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` / RED 非零、GREEN 0 | `ORACLE-AGENT-READER-GATE`：覆盖矩阵、Reader-only、三字段、正负门槛、答案+来源链；`quality/evidence/T003-agent-reader-gate-red.txt` + `quality/evidence/T004-agent-reader-gate-green.txt` |
| FR-RUN-001、FR-EXIT-001、AC-07～09 | T005/T006 | RED/GREEN | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` / RED 非零、GREEN 0 | `ORACLE-ISOLATION-EXIT`：失败/取消/重跑/并发不覆盖旧包，exit 完整且 `not_released`；`quality/evidence/T005-isolation-exit-red.txt` + `quality/evidence/T006-isolation-exit-green.txt` |
| 全部适用 AC 与 Task2A seam | T007 | FINAL | `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q'` / 0 | `ORACLE-FINAL`：当前快照聚合事实、Task2A 回归、覆盖边界；`quality/evidence/T007-final-current-snapshot.json` |

## Rollback and Recovery

- **Global recovery rule**：只回滚当前 Task2C 实现文件，保留 decision-log/spec/plan/tasks、review 和历史质量事实；失败结果留在 Audit/Reports，不把失败包安装成正式入口。
- **Irreversible boundaries**：commit、push、merge、archive、cleanup 需另行明确授权；本计划不授权任何不可逆 Git/文件操作。
- **Recovery owner**：build-code 执行者按 paired task STOP；先保留原始测试输出，修对应模块/测试；若需改变 FR、阈值、Agent-only 或文件边界，返回 build-spec/make-decision。

### Engineering Risk Handoff

- **PLAN-RISK-001**：Agent 自评与小样本代表性
  - **Affected IDs**：D-002、RISK-01、RISK-03、FR-GATE-001～003、AC-04～06、T003～T004
  - **Trigger**：Agent prompt 含 Audit/Archive、字段缺失、coverage matrix 省略类别、或 fake 通过但来源回查不完整。
  - **Consequence**：读者门看似通过但实际不可核查，或把小样本误当全量质量。
  - **Mitigation or STOP**：强制 Reader-only 文件 allowlist、逐题全字段、Task1 类别逐项覆盖/排除理由、答案与来源链双门；任一缺失 STOP。
  - **Handling Stage**：build-code / verify-code / Task 3
  - **Verification**：ORACLE-AGENT-READER-GATE、ORACLE-ISOLATION-EXIT；真实 provider 质量不因 fake acceptance 被宣称已证明。

- **PLAN-RISK-002**：Task2B 基线漂移
  - **Affected IDs**：PFACT-001、RISK-02、AC-04、T003～T004
- **Trigger**：Task2B commit、语义出口/回归证据 hash 或当前 Reader Bundle 不一致。
  - **Consequence**：题集建立在错误正文出口上。
  - **Mitigation or STOP**：build-code 开始前重新读取主线 `apply/evidence` 和 commit；变化即 STOP 返回 build-plan/spec。
  - **Handling Stage**：build-code preflight / verify-code
  - **Verification**：T003 记录 live baseline refs；不改旧 evidence。

## Implementation Order

P1 串行 producer-before-consumer：T001 先固定信号失败事实；T002 扩展 Bundle 投影。T003 再固定题集/Agent/来源链失败；T004 实现质量门。T005 固定隔离/出口失败；T006 接入原子写入和完整 manifest。T007 最后只读聚合。三组必须串行，因为后组消费前组的字段和 hash，且不能用临时适配器掩盖缺口。

## Dependencies and Parallelism

- **Dependencies**：`reader_bundle.py` 现有 projection/validation → 信号 helpers → `reader_quality.py` Reader snapshot → scorecard/exit；T001→T002→T003→T004→T005→T006→T007。
- **Parallel work**：无可安全并行的写任务；两份既有子代理只做了独立只读建议，最终计划由主任务统一落盘。
- **External dependencies**：Task0 frozen JSON、Task2B `apply/evidence` 和现有 qwen3.6 contract；没有新增服务。缺失 provider 环境只允许报告 unavailable/not_released，不能切换模型或把 fake 结果称为真实语义质量。

## Requirement and Verification Traceability

| Source / decision | FR | AC | Phase / Task | Depends on | Exact files | Command / oracle |
| --- | --- | --- | --- | --- | --- | --- |
| R-001～R-004 / D-004、D-006 | FR-SIGNAL-001/002、FR-LIFE-001、FR-STATUS-001 | AC-01～03、AC-07 | P1/T001→T002 | existing Bundle | `reader_bundle.py`; T2C acceptance; `ORACLE-SIGNAL-LIFECYCLE` |
| R-001、R-003 / D-001、D-002、D-005 | FR-GATE-001～003、FR-READER-002 | AC-04～06 | P1/T003→T004 | T002 | `reader_quality.py`, T2C acceptance; `ORACLE-AGENT-READER-GATE` |
| R-002～R-005 / D-003～D-006 | FR-RUN-001、FR-EXIT-001 | AC-07～09 | P1/T005→T006 | T004 | `reader_quality.py`, `reader_bundle.py`, T2C acceptance; `ORACLE-ISOLATION-EXIT` |
| 全部 R/D、spec §11 | 全部 | AC-01～09 | P1/T007 | T006 | T2C + Task2A acceptance; `ORACLE-FINAL` |

Exact traceability anchors: `FR-READER-001` → P1/T001→T002 → AC-01 → `ORACLE-SIGNAL-LIFECYCLE`; `FR-READER-002` → P1/T003→T004 → AC-05/AC-06 → `ORACLE-AGENT-READER-GATE`; `FR-SIGNAL-001` → P1/T001→T002 → AC-01; `FR-SIGNAL-002` → P1/T001→T002 → AC-02; `FR-LIFE-001` → P1/T001→T002 → AC-03; `FR-STATUS-001` → P1/T001→T002/T005→T006 → AC-03/AC-07; `FR-GATE-001` → P1/T003→T004 → AC-04; `FR-GATE-002` → P1/T003→T004 → AC-05; `FR-GATE-003` → P1/T003→T004 → AC-04/AC-06; `FR-EXIT-001` → P1/T005→T006 → AC-09; `FR-RUN-001` → P1/T005→T006 → AC-08. Exact acceptance anchors: `AC-01`/`AC-02`/`AC-03` → T001/T002; `AC-04`/`AC-05`/`AC-06` → T003/T004; `AC-07`/`AC-08`/`AC-09` → T005/T006; all AC → T007.

## Deferred and Open Handoff

- `DEFER-001`：字段序列化、模板、validator 的具体工程合同；owner build-spec/build-plan；trigger 为实现合同设计；handoff 为只展开已接受 FR/AC；close condition 为 plan/tasks 给出精确接口和 oracle，不改产品范围。
- `DEFER-002`：小语料真实运行、机器回查、失败样本；owner build-code；trigger 为实现完成；handoff 为使用冻结题集和可回放 manifest；close condition 为 verify-code 记录真实结果或 unavailable。
- `DEFER-003`：本阶段 Agent-only 证据的长期继承及 Task3 评审主体；owner Task3 make-decision；trigger 为 Task3 启动；handoff 为重新决定 Agent-only 或人工门；close condition 为 Task3 明确确认。
- `DEFER-004`：89 条全量、17+3 完整题集和 Reader Package 发布；owner Task3；trigger 为 Task3 启动；handoff 为复用 Task2C 冻结门；close condition 为 Task3 完成全量机器门、读者门和交付门。
- `DEFER-005`：README/AGENTS/CONTEXT 同步、清理和归档；owner Task3-Closeout；trigger 为实现和最终输出稳定；handoff 为按正式 close 流程处理；close condition 为交付记录和清理证据齐全。
- `OPEN-01`：Task3 是否继承 Agent-only；owner Task3 用户和维护者；trigger 为 Task3 make-decision；handoff 为重新确认评审主体和发布门；close condition 为 Task3 明确继承或改回人工。
- `OPEN-02`：Task2B baseline 继续保持一致；owner build-code/verify-code；trigger 为实现前 preflight；handoff 为读取 commit `2369a85`、语义出口/回归证据和 hash；close condition 为 live recheck 一致，否则 STOP。

## Governance Synchronization Matrix

| Governance surface | Actual files | Change / no change | Task IDs | Reason |
| --- | --- | --- | --- | --- |
| 原始需求/决策 | `docs/plans/knowledge-digest-knowledge-publication-prd.md`, `specs/.../decision-log.md` | no change | all | 需求和选择已在 make-decision 固化；build-plan 不重写方向。 |
| 功能规格 | `specs/.../spec.md` | no change | all | 只按已接受 FR/AC 执行，不用 build-code 补需求。 |
| 实现计划/任务 | `specs/.../plan.md`, `specs/.../tasks.md` | change | all | 本阶段唯一新增治理材料。 |
| 宪法/WorkflowHub | `/Users/Hugh/Hugh/Project/workflowhub/constitution-checklist.md`, `workflows/build-plan/SKILL.md` | no change | all | 只读取并留下逐条事实，不修改上游治理。 |
| 测试/证据 | `tests/acceptance/test_task2c_reader_quality.py`, `quality/evidence/` | change later | T001～T007 | build-code 才产生实际实现测试证据；build-plan 只定义路径。 |

## Constitution Check

- **Constitution binding**：`{"artifact_kind":"constitution","ref":"/Users/Hugh/Hugh/Project/workflowhub/constitution-checklist.md","hash":"368817c2910a36e63d3ab4642c30270abdecef15dee7caf8050e778f095919ca","id":"CONSTITUTION","version":"current-checklist-2026-08-03","clause_count":21}`
- **F1**：核心只扩展 Reader Bundle 和一个质量 slice；不接正式 pipeline/CLI。
- **F2**：复用 `project_reader_bundle`、`validate_reader_bundle`、`call_llm` 窄接口；新模块只暴露题集/质量门入口。
- **F3**：四材料与 Task2B live handoff 只决定可继续；写入仍由现有 validation/atomic commit 控制，Task2C 保持 `not_released`。
- **F4**：build-plan 独立 review 只记录 advice/finding；修复或接受风险，不把 provider/review 变成 pass gate。
- **F5**：只保留三组行为 oracle；不新增服务或重复 gate。
- **F6**：测试/质量写入留在 TaskHandle quality/evidence；不把旧身份或 dirty state 当 release gate。
- **F7**：本计划不授权 commit/push/merge/archive/cleanup；build-plan/build-code/verify-code 确认边界分开。
- **F8**：优先复用现有 Bundle、frontmatter、LLM、lock，不复制 runner/replacement 链。
- **F9**：所有无效输入、缺字段、来源断裂、不可回放 fail-loud；失败不覆盖旧包。
- **F10**：DEC-001～003 逐项记录新机制收益、既有覆盖和维护成本；无数据库/服务基建。
- **Q1**：review/test/evidence 是事实，不是完成许可证；缺事实保持未完成或 not_released。
- **Q2**：质量门、页级状态、交付级状态分离；Task2C 通过也不发布。
- **Q3**：Agent-only 是用户确认的本阶段范围修订，不能冒充 human review；独立 review 仍由 WorkflowHub 留痕。
- **S1**：复用项目既有模块和 WorkflowHub testing/wh-review 技能，不造通用 runner。
- **S2**：没有修改外部技能；实现遵守其窄边界与 fail-loud 约束。
- **S3**：本计划使用当前仓库已核实的 skill/template/route 事实；若执行时接口变化立即 STOP。
- **S4**：新 `reader_quality.py` 的指标是题集覆盖、正负门槛、来源链和回放完整性，统一写入质量证据。
- **S5**：入口是窄 programmatic function，测试可注入 fake，便于子代理按卡执行。
- **S6**：复用既有 Reader Bundle/pytest/WorkflowHub 合同，不新增闭门流程。
- **S7**：当前只实现 build-code 阶段文件，不新增 WorkflowHub stage/skill 文件夹。
- **S8**：模块只依赖项目公开 Python 接口、路径和环境变量，不绑死服务进程。

## Phase P1 — Reader 信号、Agent 读者门与隔离出口

### Goal

完成 Task2C 的单一事实源信号投影、小语料 Agent-only 读者门、失败隔离和 `not_released` exit manifest；不改变正式 S1-S6 或 CLI。

### Files

- **NEW**：`src/knowledge_digest/reader_quality.py`、`tests/acceptance/test_task2c_reader_quality.py`
- **MODIFY**：`src/knowledge_digest/reader_bundle.py`
- **DO NOT TOUCH**：`src/knowledge_digest/pipeline.py`、`src/knowledge_digest/cli.py`、`src/knowledge_digest/publication.py`：本任务是隔离的 Reader Bundle quality slice，不扩大到正式 S1-S6/CLI。
- **DO NOT TOUCH**：`src/knowledge_digest/identity.py`、`src/knowledge_digest/topic_axis.py`：不改变 TopicIndex 身份和 Task1 事实。
- **DO NOT TOUCH**：`src/knowledge_digest/reader_frontmatter.py`、`src/knowledge_digest/llm.py`、`src/knowledge_digest/lock.py`：已有窄接口足够，避免无必要 schema/provider/锁改动。
- **DO NOT TOUCH**：`config/task0-question-set.v1.json`：冻结输入只读，不临时改题。
- **DO NOT TOUCH**：`tests/acceptance/test_task2a_reader_bundle.py` 及 `tests/fixtures/task2a_reader_bundle/`：保留 Task2A 回归基线。
- **DO NOT TOUCH**：`apply/evidence/`、Task2B commit/evidence：只读交接事实，不重新生成或篡改。

### Tasks

- `T001/T002`：固定并实现 Reader signal/lifecycle projection 与导航过滤，含失败页退出默认导航（AC-07）。
- `T003/T004`：固定并实现 Task0 小题集、Reader-only Agent scorecard 和答案+来源链门。
- `T005/T006`：固定并实现失败隔离、重跑/并发边界和完整 `not_released` exit manifest。
- `T007`：只读聚合 Task2C 与 Task2A 回归。

### Verify

ORACLE-SIGNAL-LIFECYCLE / ORACLE-AGENT-READER-GATE / ORACLE-ISOLATION-EXIT / ORACLE-FINAL

每组 RED/GREEN 使用 `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py -q'` 和同一 oracle；P1 完成后执行 `bash -lc 'uv run --frozen pytest tests/acceptance/test_task2c_reader_quality.py tests/acceptance/test_task2a_reader_bundle.py -q'`，预期 0，证据写入 `quality/evidence/T007-final-current-snapshot.json`。本 Phase Verify 对齐 `ORACLE-SIGNAL-LIFECYCLE`、`ORACLE-AGENT-READER-GATE`、`ORACLE-ISOLATION-EXIT`、`ORACLE-FINAL`。不在 build-plan 执行测试。

### Knowledge

下一阶段 build-code 已知：Task2B baseline refs 已现场回查；Task2C 只能修改本 Phase 三个文件；真实 provider 不是 acceptance fake 的替代品；Task3 继承 Agent-only 未决。

### STOP

任何需要改 FR/AC、放宽 8/3 门槛、让 Agent 读取 Audit、写 human/verified、接 CLI/pipeline、改 Task2A/Task2B 合同或扩大文件边界的情况，返回 spec/decision-log；不在 build-code 临时决定。

### Done

只有当 T001～T007 的命令、退出码、oracle、AC 覆盖和 review/analysis 事实真实记录后，才能报告 P1 build-code 可交接；本 Phase 不包含 commit、push、merge、cleanup 或 formal release。

### Risks and rollback

主要风险是 Agent 自评、小样本代表性和 Task2B baseline 漂移；对应 PLAN-RISK-001/002。回滚只移除当前 Task2C 实现修改，保留四材料与质量事实，旧 Reader Bundle 不被覆盖。

## Build-plan review facts and dispositions

- Initial build-spec/review history is retained in the TaskHandle. For this build-plan, the required independent `wh-review` is to inspect the complete current plan/tasks packet after both files are authored.
- Findings must be recorded here with actual attempt/result/report refs and one of `fixed`, `rejected_invalid`, `accepted_risk`, or `needs_human`; no prose claim may replace the runner result.
- `wh-review` attempt `7f9c9bf3-1975-440a-9ddf-25ce7f647d75` was `available`; report `quality/reviews/reports/7f9c9bf3-1975-440a-9ddf-25ce7f647d75.md`, result `quality/reviews/results/build-plan-default-10444c5532adf00af6b91f33b867097b90cddc01-7f9c9bf3-1975-440a-9ddf-25ce7f647d75.json`, snapshot `10444c5532adf00af6b91f33b867097b90cddc01`. `opencode/v4flash` returned 3 minor findings; `pi/k3` exited nonzero after the stuck child was terminated; `codex/luna` was SAME_SOURCE. The earlier attempt `a82c94d7-7413-42e9-92b7-f5569f7ef3b3` was `unavailable` because an invalid string `context_map` was supplied; it was not a semantic finding.
- Dispositions: `F-6cae2e217729` fixed by aligning plan evidence paths with every T001–T006 task card; `F-92c3f5f45ecf` fixed by enumerating long/table-image/bilingual/multi-source/failed-degraded inventory coverage and the machine-fixture+explicit-exclusion rule in T003/T004 scenarios and oracle; `F-9bdaff1a3fe2` fixed by assigning AC-07 to T001/T002 and explicitly testing failed-page navigation exclusion. All are nonblocking minor, repaired in this build-plan task.
- The final `spec-analyze` is report-only and must run after the last plan/tasks edit. Its actual result and any findings are recorded in the TaskHandle `quality/evidence/` path, not as a fifth material and not as a pass gate.
