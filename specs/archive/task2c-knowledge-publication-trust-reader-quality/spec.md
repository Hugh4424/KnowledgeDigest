# 功能规格：Task 2-C 信任信号与小语料读者质量门

> 基于已接受的 Task 2-C 决策。本文件只定义读者可观察的行为、状态、边界和验收，不定义实现文件、工程命令或任务拆分。

- **功能名**：小语料 Reader Trust Signals 与 Agent 读者质量门
- **来源**：`R-001`～`R-005`、`D-001`～`D-006`、用户最终确认 `A`
- **状态**：已接受
- **内容 profile**：`spec-content.v3`

## 速读卡（30 秒）

- **一句话需求**：维护者运行 Task 2-C 后，读者能在打开正文前看到可信度、更新时间和生命周期信号，系统还能用 Agent 从 Reader Package 验证小语料问题是否真的答得上。
- **核心改动点**：
  - 从同一事实源投影 Reader 页头和索引信号。
  - 用 Agent 只读 Reader Package，执行冻结的小语料读者题集。
- **最大影响面**：Reader Package 的索引/页头、Audit/Archive 中的质量证据，以及 Task 3 的全量发布入口。
- **验收信号**：至少 8 个正向题全部命中、3 个负向题零误命中、答案和来源链都完整；Task 2-C 交付仍为 `not_released`。

## 来源与决策映射

| Source ID | Decision ID | FR / AC IDs | Status / affected scope | Unresolved / handoff |
| --- | --- | --- | --- | --- |
| R-001～R-003 | D-001～D-006 | FR-READER-001～FR-EXIT-001 / AC-01～AC-09 | current / 全部 Task 2-C | 仅由当前 Task 2-C 规格展开 |
| R-004 | D-001、D-003～D-006 | FR-SIGNAL-001～FR-STATUS-001、FR-RUN-001 / AC-01～AC-08 | current / 信号、状态、读者门、运行隔离 | 字段序列化交给 build-plan/build-code |
| R-005 | D-001、D-003 | FR-GATE-001、FR-EXIT-001 / AC-04、AC-09 | current / Task 2-B 出口到 Task 2-C | Task 2-B 证据在 detail 审查包外，build-spec 前再次核对 |
| D-002 | D-002 | FR-GATE-002、FR-GATE-003 / AC-05、AC-06 | current / Agent-only 仅限 Task 2-C | Task 3 是否继承，回到 Task 3 决策 |
| F-c877a7facb19、F-5cb7b2002207 | D-001～D-006 | 全部 FR / AC | current / 审查材料完整性 | 已修正并保留原 review 事实 |

## 1. 问题与紧迫性

现有机器检查可以证明文件结构、provider 调用和部分来源校验通过，但不能证明读者打开 Reader Package 后能回答实际问题。静态 `verified`、lint 或 provider 成功不能代替正文可用性；如果错误内容进入正式入口，读者会得到看似可信但无法使用或无法核查的知识。

Task 2-C 必须在 Task 2-B 小语料正文之后补上两件事：一是让读者在打开正文前看到可解释的信任、更新时间和生命周期信号；二是用受控小语料验证读者能不能从页面找到答案。这个阶段只证明进入 Task 3 的资格，不发布 89 条全量结果。

## 2. 背景、目标与范围

### 背景

Task 2-A/2-B 已固定 Reader Bundle、Concept 页面和正文编译边界。Task 2-C 消费这些结果，不改变 TopicIndex、页面类型、Evidence/Provenance 或既有 Reader Package 的身份。

### 目标

- 读者从根入口、产品/模块索引即可看到页面类型、描述、来源数量、生成时间、信任层级、生命周期状态和 stale 提示。
- Agent 像真实读者一样只从 Reader Package 完成冻结题集；答案、边界/版本和来源链必须同时成立。
- 失败结果留在 Audit/Archive，不能覆盖既有正式 Reader Package，也不能把小语料通过误报成全量发布。

### 范围内

- 小语料 Reader 信号投影、归一化、freshness/lifecycle 判断和导航过滤。
- 至少 8 个正向题、3 个负向题的题集派生和 Agent-only 读者质量证据。
- 逐题 scorecard、失败样本、状态报告和 Task 2-C exit manifest。

## 3. 用户场景与状态覆盖

### SCN-001：维护者启动小语料质量运行

- **角色**：维护者
- **Given**：Task 0 题集/状态合同、Task 1 TopicIndex、Task 2-A Reader Bundle 和 Task 2-B 正文出口可用。
- **When**：维护者启动 Task 2-C。
- **Then**：系统读取冻结输入，生成同一事实源的 Reader 信号投影和小语料质量记录；不改变既有正式 Reader Package。

### SCN-002：读者从入口查看信号

- **角色**：读者
- **Given**：Reader Package 中存在根入口、产品/模块索引和 concept 页面。
- **When**：读者从 Home 进入根索引、产品/模块索引。
- **Then**：不打开正文也能看到 type、description、来源数量、`generated.at`、derived trust tier、`status` 和 stale/deprecated 提示。

### SCN-003：Agent 从 Reader Package 回答题目

- **角色**：Agent 读者评审
- **Given**：已冻结正向和负向题集，Reader Package 可读。
- **When**：Agent 只读取 Home、索引和正文回答题目。
- **Then**：每题记录答案命中、边界/版本、来源回查和失败原因；Audit/Archive 不能补答案。

### SCN-004：样本不足或题目失败

- **角色**：维护者
- **Given**：可答正向题少于 8 个、覆盖不足、正向题未命中或负向题误命中。
- **When**：系统计算质量门。
- **Then**：Task 2-C 结果为 `not_released`，保留失败样本，不覆盖旧正式 Reader Package。

### SCN-005：信号或来源链失败

- **角色**：读者与维护者
- **Given**：必需信号投影不一致、来源回查断裂、机器门失败或正文/人工修改冲突。
- **When**：系统校验页面和质量证据。
- **Then**：相关页面为 `degraded`，不进入正式 Reader 导航；Audit/Archive 保留原因和恢复信息。

### SCN-006：普通信号提示

- **角色**：读者
- **Given**：页面缺少 `verified`、达到 `stale_after` 或声明 `status=deprecated`。
- **When**：读者查看索引或页面。
- **Then**：分别显示 `unverified`、stale 提示或隐藏 deprecated 默认入口；这些情况本身不自动把页面变成 `degraded`。

### SCN-007：运行失败、取消与恢复

- **角色**：维护者
- **Given**：provider/Agent 不可用、输入读取失败或维护者取消运行。
- **When**：运行未能完成。
- **Then**：不生成通过证据，不覆盖旧 Reader Package；下次运行从新的完整输入重新生成，失败原因可在 Audit/Archive 中追溯。

### SCN-008：重复运行或并发写入

- **角色**：维护者
- **Given**：同一知识库已有一次 Task 2-C 运行，或同时出现第二次写入请求。
- **When**：系统再次运行或检测到并发写入。
- **Then**：同一输入得到稳定的信号/题集投影；并发写入不得产生第二套事实源、覆盖旧正式包或伪造新的通过状态。

### 状态覆盖清单

- [x] **默认态**：SCN-002，正常 Reader Package 信号和导航。
- [x] **空态**：SCN-004，正向可答题不足 8 个时 `not_released`。
- [x] **错误态**：SCN-005、SCN-007，失败留 Audit，Reader 导航排除。
- [x] **加载态**：SCN-001，运行中只产生候选/审计过程，不宣称发布。
- [x] **取消态**：SCN-007，取消不覆盖旧正式包。
- [x] **边界态**：SCN-004、SCN-006，阈值、stale 和 deprecated 按固定规则处理。
- [ ] **权限态**：N/A — 本功能是本地人工触发工具，没有独立登录或角色权限产品面；文件不可读按 SCN-007 处理。
- [x] **竞态**：SCN-008，单写者和稳定投影约束保持。

## 4. 产品事实与假设（PFACT）

- **PFACT-001**：Task 2-C 依赖 Task 2-B 的小语料正文出口，Task 2-B 已完成本任务所需机器出口。
  - **status**：`verified`
  - **证据或来源**：Task 2-B commit `2369a853adb4bc70709036c563233cae361222be`；`apply/evidence/T013.semantic-run-task2b-provider-repair-v9-20260812.json` sha256 `c38aad3185bd534ee988766d55fc26ee68d5f8b2688f8e00ddb72d23dbbd17e4`，run `run-519d5c93591e45faab8e3ef56601a3f1`，12 concepts machine-passing，delivery `not_released`；`apply/evidence/T014.final-regression-task2b-provider-repair-v9-20260812.txt` sha256 `c202e04f2a2e208fd2e3b7cb3ad6372e57b38459ab69c9c423180e2cd59a852c`，49/264/518 regression facts verified. 原 detail review 包外限制已通过本次 build-spec handoff recheck 关闭。
  - **关联**：FR-READER-001、FR-GATE-001、AC-01、AC-04

- **PFACT-002**：Reader Package 和 Audit/Archive Package 是两个职责不同的包，Reader 是默认阅读入口。
  - **status**：`verified`
  - **证据或来源**：PRD §6.1、`R-004`、`D-004`
  - **关联**：FR-READER-001、FR-GATE-002、AC-01、AC-05

- **PFACT-003**：Task 2-C 只证明小语料质量，不能把交付标为 `released`。
  - **status**：`verified`
  - **证据或来源**：PRD Task 2-C/Task 3 边界、`D-003`
  - **关联**：FR-STATUS-001、FR-EXIT-001、AC-07、AC-09

- **PFACT-004**：本任务允许 Agent 替代独立人工评审，但不允许冒充 `human_reviewed` 或 `verified`。
  - **status**：`verified`
  - **证据或来源**：用户确认 `C` 和“确认修改原始门槛”、`D-002`、Grill 结果
  - **关联**：FR-GATE-002、FR-GATE-003、AC-05、AC-06

- **PFACT-005**：stale 是复核提示，deprecated 是生命周期提示；两者不自动删除页面或把交付改成 `released`。
  - **status**：`verified`
  - **证据或来源**：PRD §6.9、`D-006`
  - **关联**：FR-LIFE-001、FR-STATUS-001、AC-03、AC-07

- **PFACT-006**：具体字段序列化、scorecard 存储格式和 validator 错误分类尚未属于本规格的工程合同。
  - **status**：`inferred`
  - **证据或来源**：`DEFER-001`～`DEFER-003`；本规格只固定用户可观察字段和失败含义，不固定实现格式。
  - **关联**：FR-GATE-002、FR-EXIT-001、AC-05、AC-09

## 5. 功能需求

### Reader 信号投影（SIGNAL）

Task 2-C 必须把同一份审计事实/页面 frontmatter 投影成 Reader 页头和索引信号。Reader 侧不得维护第二套来源、信任或状态事实。

- **FR-SIGNAL-001**：根索引、产品索引和模块索引必须展示页面类型、描述、来源数量、生成时间、derived trust tier、生命周期状态和 stale/deprecated 提示。
  - **范围边界**：只展示 Reader 可读信号；不展示 provider 原始响应、审计现场或包级 release 状态。
  - **依据**：`R-004`、`D-004`、PFACT-002
  - **场景**：SCN-002
  - **验收**：AC-01

- **FR-SIGNAL-002**：`verified` 的 mapping 和 list 必须归一成相同结果；缺失验证显示 `unverified`；只有真实机器内容回查才可派生 machine-confirmed，真实人工事件才可派生 human-reviewed。
  - **范围边界**：Agent 读者门不产生任何 `verified`、trust tier、`machine-confirmed` 或 `human-reviewed` 事件；derived trust tier 只反映既有 Audit 事实，本任务新增的 Agent 评审记录通常仍为 `unverified`。
  - **依据**：`R-004`、`D-002`、PFACT-004
  - **场景**：SCN-002、SCN-006
  - **验收**：AC-02

### 生命周期与页面状态（LIFECYCLE）

- **FR-LIFE-001**：系统按绝对日期判断 stale；stale 只显示复核提示。`status=deprecated` 保留旧路径但默认入口隐藏。
  - **范围边界**：不猜 `stale_after`，不因 stale 或 deprecated 自动删除、改写或发布。
  - **依据**：`D-006`、PFACT-005
  - **场景**：SCN-006
  - **验收**：AC-03

- **FR-STATUS-001**：页面只有 `published`/`degraded`，Task 2-C 交付只有 `not_released`；明确的信号事实源失败、来源回查失败、机器门失败或内容冲突才触发 `degraded`。
  - **范围边界**：`unverified`、stale、deprecated 本身不触发 `degraded`；`released` 延期到 Task 3。
  - **依据**：`D-003`、`D-006`、PFACT-003、PFACT-005
  - **场景**：SCN-004、SCN-005、SCN-006
  - **验收**：AC-03、AC-07

### Agent 读者质量门（GATE）

- **FR-GATE-001**：系统必须使用 Task 0 冻结的来源标签和确定性规则派生可回答正向/负向子集，不得由编译器或评审人临时挑选；在此基础上至少有 8 个可回答正向题，覆盖至少 2 个产品/模块和至少 2 类页面，并保留 3 个负向题作为反误命中检查。Task 1 inventory 中实际存在的长文、表格/图片、双语、多源、失败/degraded 类别，必须各自进入正向样本，或有单独的 machine fixture 和排除理由；不能以“样本中碰巧没有”为理由忽略。
  - **范围边界**：不要求本阶段跑完整 17+3 题，也不跑 89 条全量；类别覆盖规则仍是硬门槛。
  - **依据**：`D-001`、PFACT-001
  - **场景**：SCN-001、SCN-004
  - **验收**：AC-04

- **FR-GATE-002**：Agent 评分输入只能来自 Reader Package；每题必须记录题目、入口、首次命中页、跳转记录、答案完整性、边界/版本结果、来源归因、评审人、评审日期、抽样 seed、`agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`、模型/提示/seed/hash、Reader 输入 hash、答案结果、来源回查结果、失败原因和评分表 hash。
  - **范围边界**：Audit/Archive 只能事后核对来源和保存失败证据，不能补读者答案；不得写 `human_reviewed`。
  - **依据**：`D-002`、`D-004`、D-005、PFACT-002、PFACT-004
  - **场景**：SCN-003、SCN-007
  - **验收**：AC-05、AC-06

- **FR-GATE-003**：只有正向题 100% 命中、3 个负向题 0 误命中、答案边界/版本准确且来源链完整时，Task 2-C 读者门才算通过；字段缺失、无法回放或来源断裂的题目失败。
  - **范围边界**：读者门通过不改变 Task 2-C 的 `not_released` 交付状态。
  - **依据**：`D-001`、`D-003`、`D-005`
  - **场景**：SCN-003、SCN-004、SCN-005
  - **验收**：AC-04、AC-05、AC-06、AC-07

### 读者入口与证据（READER）

- **FR-READER-001**：Reader 入口保持 Home → 唯一根 index → 产品/模块索引 → Task 2-B 冻结的 concept 页面；Task 2-C 不新增页面类型或第二套目录事实。
  - **范围边界**：失败或 degraded 页面不进入正式 Reader 导航；Audit/Archive 不作为读者入口。
  - **依据**：`R-004`、`D-001`、`D-004`
  - **场景**：SCN-002、SCN-005
  - **验收**：AC-01、AC-07

- **FR-READER-002**：每个通过题目的正文事实必须保留 source id → claim id/locator → Evidence 的回查链。
  - **范围边界**：信号投影不得复制或替代 Claim、Evidence、Provenance。
  - **依据**：`D-005`、PFACT-002
  - **场景**：SCN-003、SCN-005
  - **验收**：AC-06

### 出口与交接（EXIT）

- **FR-EXIT-001**：Task 2-C 退出证据必须冻结 Concept Contract、页面类型、信号字段、模板、题集派生规则、scorecard、`agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`、seed、阈值、实际 provider/config、调用预算（call budget）、wall-clock budget、凭据来源和 commit；交付状态仍为 `not_released`。
  - **范围边界**：Task 3 只能复用本出口，不能临时放宽阈值或把 Agent 证据改叫人工证据。
  - **依据**：`D-001`～`D-003`、PFACT-003、PFACT-006
  - **场景**：SCN-001、SCN-008
  - **验收**：AC-09

- **FR-RUN-001**：取消、失败重跑和并发写入必须以单写者边界处理：未完成运行不得覆盖旧正式 Reader Package，不得产生第二套事实源，不得写入通过状态；同一冻结输入的重跑必须得到稳定的信号和题集投影。
  - **范围边界**：本需求只定义可观察的隔离、恢复和稳定性，不定义锁、队列或存储实现。
  - **依据**：`R-004`、`D-001`、`D-003`、PFACT-003
  - **场景**：SCN-007、SCN-008
  - **验收**：AC-08

## 6. 模块划分

### Reader 信号与生命周期

- **负责什么**：把同一事实源转成读者可见信号，并判断 stale、deprecated、published/degraded。
- **对外提供什么**：稳定的页头/索引信号和默认入口过滤结果。
- **依赖谁**：Task 2-A Reader Bundle、Task 2-B concept 页面、Audit/Archive 事实。
- **测试边界**：信号归一、日期判断、生命周期过滤和单事实源一致性。

### Agent 读者质量门

- **负责什么**：从 Reader Package 执行冻结题集并保存逐题答案、来源回查和失败样本。
- **对外提供什么**：小语料质量门结果和可回放 scorecard。
- **依赖谁**：Task 0 题集/状态合同、Reader Package、Task 2-B 正文出口。
- **测试边界**：样本覆盖、正负向阈值、Agent-only 字段、答案/来源完整性和失败隔离。

### 运行隔离

- **负责什么**：隔离取消、失败重跑和并发写入，保护旧正式 Reader Package 和单一事实源。
- **对外提供什么**：稳定重跑、失败恢复和不提前写入通过状态的可观察结果。
- **依赖谁**：Reader Package、Task 2-C 运行状态和出口审计。
- **测试边界**：取消、重跑、并发写入、旧包保护和投影稳定性。

### 出口审计

- **负责什么**：冻结本次 Task 2-C 的合同和证据边界。
- **对外提供什么**：Task 3 可复用的 exit manifest，明确 `not_released`。
- **依赖谁**：信号验证结果和读者题集结果。
- **测试边界**：字段齐全、阈值不可漂移、失败不覆盖旧 Reader Package。

## 7. 关键实体

- **Reader Signal Projection**：读者入口上的 type、description、来源数、generated.at、trust tier、status、stale/deprecated 提示；必须由唯一事实源重算。
- **Reader Question Record**：一条冻结题目的 Agent-only 评审记录；至少包括题目、入口、首次命中页、跳转记录、答案完整性、边界/版本、来源归因、评审人、评审日期、抽样 seed、Reader 输入、`agent_assisted`、`review_mode`、`gate_actor`、模型/提示/seed/hash、答案结果、来源回查、失败原因和评分表 hash。
- **Quality Gate Result**：小语料的正向命中数、负向误命中数、产品/模块和页面类型覆盖、Task 1 inventory 类别覆盖、结果和 `not_released` 交付状态。
- **Exit Manifest**：Task 2-C 结束时冻结的 Concept Contract、信号、模板、题集、scorecard、`agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`、seed、阈值、provider/config、调用预算、wall-clock budget、凭据来源、commit 和结果状态。

## 8. 数据和生命周期

- **数据粒度**：一条 Reader Signal Projection 对应一个 Reader concept 或索引条目；一条 Reader Question Record 对应一道冻结题。
- **数据时效**：正文有意义变化时重新生成时间并重新验证；`stale_after` 只接受来源明确提供的绝对日期。
- **缺失或迟到**：题目不足、信号不完整、Agent/provider 失败或来源回查失败时，质量门不通过，失败证据进入 Audit，旧正式 Reader Package 保留。
- **预览与正式**：Task 2-C 产生候选/审计结果，交付级是 `not_released`；不得覆盖既有正式 Reader Package。
- **当前与历史**：当前 Reader 只展示通过机器门且未被默认过滤的页面；旧正式页面和失败运行历史保留在原有职责包中。
- **运行隔离**：取消、失败重跑和并发请求只产生候选/审计记录；旧正式 Reader Package 保持不变，稳定重跑不得产生第二事实源。
- **归属与清理**：Reader Package 供读者使用；Audit/Archive 供追溯和恢复；本阶段不清理历史来源、页面或审计证据。

## 9. 兼容性预留

- **既有消费方**：Home、根 index、产品/模块索引、三类 concept 页面、Claim/Evidence/Provenance 继续使用既有合同。
- **命名预留**：不把 `agent_assisted` 改名为 `human_reviewed`，并用 `review_mode=agent_only`、`gate_actor=agent` 表达本次范围修订。
- **容器预留**：Task 3 可以复用同一套题集、scorecard 和 exit manifest，但必须重新确认全量门。
- **状态预留**：保留 `published/degraded` 与 `released/not_released` 两层，不新增信任分数或第三套发布状态。
- **扩展边界**：Task 3 是否继承 Agent-only 评审是新的决策，不由本规格默认推导。

## 10. 明确不做与默认必须成立

### 明确不做

- 不做 89 条全量正文、全量题集或正式 `released`：`D-001`、`D-003`，延期到 Task 3。
- 不把 Agent-only 扩展成永久人工/Agent 队列：`D-001`、`D-002`，本阶段只产一次性小语料证据。
- 不引入 trust score、OKF reference agent/viewer、Attested Computation、数据库、图谱、向量库或调度器：`R-004`、PRD 非目标。
- 不改变 TopicIndex 身份、页面类型、Evidence/Provenance 权威或 Task 2-A Reader Bundle：`R-005`、`D-001`。
- 不用静态字段、lint、provider 成功、Claim 数、页数或 Agent 输出本身替代读者质量：`R-004`、`D-002`、`D-005`。

### 默认必须成立

- Reader 和 Audit/Archive 继续分包，且所有 Reader 信号来自单一事实源：FR-SIGNAL-001、FR-READER-002、AC-01、AC-06。
- Agent 输入只能来自 Reader Package，隐藏审计资料不能补答案：FR-GATE-002、AC-05。
- 失败、冲突、不可回放或来源断裂不覆盖旧正式 Reader Package：FR-STATUS-001、FR-RUN-001、AC-07、AC-08。
- Task 2-C 任何通过都不能自动变成 `released`：FR-EXIT-001、AC-09。

## 11. 验收标准

- [ ] **AC-01**：根、产品和模块索引在不打开正文时展示 type、description、来源数量、generated.at、trust tier、status 和 stale/deprecated 提示。
  - **需求**：FR-SIGNAL-001、FR-READER-001
  - **验证方法**：从 Reader Package 的入口按默认阅读路径检查索引和页头。
  - **通过条件**：所有必需信号可见，且与同一事实源重算结果一致。
  - **失败条件**：缺字段、索引与页面不一致、出现第二事实源或把审计信息当 Reader 字段。
  - **证据类型**：`evidence`

- [ ] **AC-02**：`verified` mapping/list、缺失验证、真实机器回查和真实人工事件得到确定且不混淆的 trust tier。
  - **需求**：FR-SIGNAL-002
  - **验证方法**：使用 mapping、list、缺失、既有机器事件和既有人工事件样本重放投影；另用 Agent 评审记录确认本任务不新增 trust tier 事件。
  - **通过条件**：mapping/list 同结果；缺失为 unverified；既有事件按规则投影；Agent 不生成 verified、machine-confirmed、human-reviewed 或新的 trust tier。
  - **失败条件**：lint/provider/Agent 伪造 verified 或 trust tier，或同一输入得到不同结果。
  - **证据类型**：`test`

- [ ] **AC-03**：stale 和 deprecated 行为可重放且不误降级。
  - **需求**：FR-LIFE-001、FR-STATUS-001
  - **验证方法**：使用未到期、到期、无 stale_after、deprecated 和普通 unverified 样本检查入口。
  - **通过条件**：stale 只告警，deprecated 旧路径保留但默认隐藏，三者本身不触发 degraded。
  - **失败条件**：猜测 stale 日期、删除旧路径、误把提示当 degraded 或改写 released 状态。
  - **证据类型**：`test`

- [ ] **AC-04**：题集满足小语料覆盖和门槛，且 Task 2-B 出口已在进入实现前完成回查。
  - **需求**：FR-GATE-001、FR-GATE-003
  - **验证方法**：先核对 Task 2-B 提交、T013/T014、页面类型和小语料正文出口，再检查冻结 seed 派生出的正向/负向题和覆盖矩阵。
  - **通过条件**：Task 2-B 证据回查完成；正向至少 8 题，覆盖至少 2 个产品/模块和 2 类页面；Task 1 inventory 中实际存在的每个类别均有正向题，或有 machine fixture 和明确排除理由；正向全命中，负向 0 误命中。
  - **失败条件**：Task 2-B 证据无法回查、少于 8 题、产品/模块或页面覆盖不足、实际存在的类别没有样本或 fixture/排除理由、以“样本中碰巧没有”跳过类别、任一正向未命中或任一负向误命中。
  - **证据类型**：`evidence`

- [ ] **AC-05**：每题 Agent 记录可证明评审主体、输入边界、读者路径和答案结果。
  - **需求**：FR-GATE-002
  - **验证方法**：逐题检查 scorecard、Reader 输入指纹、答案结果和来源回查记录。
  - **通过条件**：显式存在题目、入口、首次命中页、跳转、答案完整性、边界/版本、来源归因、评审人、评审日期、抽样 seed、`agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`、模型/提示/seed/hash、输入 hash、答案结果、来源回查结果、失败原因和 scorecard hash；输入不含 Audit/Archive 答案资料。
  - **失败条件**：任一上述字段缺失、主体冒充 human、无法回放，或 Agent 使用隐藏资料补答案。
  - **证据类型**：`evidence`

- [ ] **AC-06**：每道通过题答案和来源链同时成立。
  - **需求**：FR-GATE-003、FR-READER-002
  - **验证方法**：从题目答案回查 source id、claim id/locator 和 Evidence。
  - **通过条件**：答案命中、边界/版本准确、来源链完整且定位稳定。
  - **失败条件**：答案正确但来源断裂、边界/版本错误或只在 Audit 中找得到答案。
  - **证据类型**：`evidence`

- [ ] **AC-07**：失败页和失败交付不会进入正式 Reader 或覆盖旧包。
  - **需求**：FR-STATUS-001、FR-READER-001
  - **验证方法**：构造信号失败、来源失败、机器失败、内容冲突、题集失败和 provider 失败。
  - **通过条件**：页面按明确失败变为 degraded 并退出正式导航；交付保持 not_released；旧正式包不变。
  - **失败条件**：失败页进入默认入口、旧包被覆盖、或以 provider/lint 绿灯宣称读者门通过。
  - **证据类型**：`evidence`

- [ ] **AC-08**：取消、重跑和并发输入不会制造第二事实源或破坏旧正式包。
  - **需求**：FR-RUN-001
  - **验证方法**：检查取消、重复运行和并发写入场景的可观察结果。
  - **通过条件**：失败可恢复、历史保留、成功投影稳定、单写者边界有效。
  - **失败条件**：半成品覆盖旧包、同一信号出现两套来源、或并发运行产生不同入口事实。
  - **证据类型**：`test`

- [ ] **AC-09**：Task 2-C exit manifest 完整且不提前释放。
  - **需求**：FR-EXIT-001
  - **验证方法**：检查出口证据是否包含 Concept Contract、页面类型、信号字段、模板、题集派生、scorecard、Agent 字段、seed、阈值、provider/config、调用预算、wall-clock budget、凭据来源、commit 和状态。
  - **通过条件**：全部字段冻结，且显式存在 `agent_assisted=true`、`review_mode=agent_only`、`gate_actor=agent`；结果明确为 `not_released`，Task 3 可直接消费且不能临时放宽。
  - **失败条件**：任一字段缺失、预算缺失、阈值漂移、Agent 字段缺失或被写成人工、或出口误标 `released`。
  - **证据类型**：`evidence`

## 12. 风险、未决与交接

### Deferred handoff contract

这些延期项只记录 owner、触发、交接和关闭条件，不新增本任务功能：

- `DEFER-001`：字段序列化、模板和 validator 的具体工程合同；owner `build-spec/build-plan`；trigger 为实现合同设计；handoff 为只展开已接受 FR/AC；close condition 为 plan/tasks 给出精确接口和 oracle，且不改变产品范围。
- `DEFER-002`：小语料真实运行、机器回查和失败样本；owner `build-code`；trigger 为实现完成；handoff 为使用冻结题集和可回放 manifest；close condition 为 `verify-code` 记录真实结果或 `unavailable`。
- `DEFER-003`：本阶段 Agent-only 证据的长期继承及 Task 3 评审主体；owner `Task 3 make-decision`；trigger 为 Task 3 启动；handoff 为重新决定 Agent-only 或人工门；close condition 为 Task 3 明确确认。
- `DEFER-004`：89 条全量、17+3 完整题集和 Reader Package 发布；owner `Task 3`；trigger 为 Task 3 启动；handoff 为复用 Task 2-C 冻结门；close condition 为 Task 3 完成全量机器门、读者门和交付门。
- `DEFER-005`：README/AGENTS/CONTEXT 同步、清理和归档；owner `Task 3-Closeout`；trigger 为实现和最终输出稳定；handoff 为按正式 close 流程处理；close condition 为交付记录和清理证据齐全。

- **RISK-01：Agent 自评风险**
  - **受影响 ID**：PFACT-004、FR-GATE-002、AC-05、AC-06
  - **触发条件**：Agent 评分被当作普通人工或没有保存完整回放材料。
  - **后果**：模型可能漏掉自己生成内容的问题，读者门可信度下降。
  - **缓解或 STOP**：强制 Agent-only 字段、Reader-only 输入、逐题失败样本和可回放 hash；任一缺失则 STOP。
  - **处理 Stage**：`build-spec` / `build-code` / `verify-code`
  - **验证**：AC-05、AC-06、AC-09

- **RISK-02：Task 2-B 跨任务证据复核风险（已关闭）**
  - **受影响 ID**：PFACT-001、FR-READER-001、FR-GATE-001、AC-04
  - **触发条件**：下游无法重新读取 Task 2-B 真实出口证据。
  - **后果**：Task 2-C 可能在错误的正文基础上建立质量门。
  - **缓解或 STOP**：已在 build-spec handoff 核对 Task 2-B 提交、T013/T014、页面类型和小语料出口；若后续发现这些证据与当前基线不一致，停止进入实现。
  - **处理 Stage**：`build-spec` / `build-plan`
  - **验证**：本次 live handoff recheck；记录见 PFACT-001

- **RISK-03：小样本代表性不足**
  - **受影响 ID**：FR-GATE-001、FR-GATE-003、AC-04
  - **触发条件**：8 个正向题覆盖不到长文本、表格/图片、双语、多来源或失败场景。
  - **后果**：小语料通过不能代表全量读者质量。
  - **缓解或 STOP**：覆盖矩阵显式列出样本或排除理由；Task 3 重新做全量题集。
  - **处理 Stage**：`build-code` / `Task 3`
  - **验证**：AC-04、Task 3 全量验收

- **OPEN-01：Task 3 是否继承 Agent-only**
  - **受影响 ID**：PFACT-004、FR-GATE-002、FR-EXIT-001
  - **owner**：Task 3 make-decision 的用户和维护者
  - **影响**：可能改变全量发布的评审主体和正式发布门。
  - **处理 Stage**：Task 3 make-decision
  - **关闭条件或 STOP**：Task 3 明确确认继承或改回人工门；本规格不默认推导。

- **OPEN-02：Task 2-B 出口跨任务复核（已关闭）**
  - **受影响 ID**：PFACT-001、AC-04
  - **owner**：build-spec/build-plan 维护者
  - **影响**：已确认正文和页面类型基线；后续实现仍必须使用该冻结出口。
  - **处理 Stage**：build-spec handoff
  - **关闭条件或 STOP**：已读取并核对 Task 2-B T013/T014 与提交事实；若基线改变则 STOP。

## 13. 业务影响与回归范围

### Reader Package 阅读入口

- **既有行为**：读者从 Home、索引和正式主题页进入知识；Audit/Archive 不作为默认入口。
- **本需求影响**：索引和页头增加可解释的信任、时间和生命周期信号；失败页不进入正式导航。
- **回归路径**：Home → 根 index → 产品/模块索引 → concept 页面 → 来源回查。
- **验收**：AC-01、AC-03、AC-06、AC-07。

### 质量门与交付状态

- **既有行为**：机器门和页面发布状态与交付级发布状态分开。
- **本需求影响**：增加小语料 Agent-only 读者门和逐题证据，但 Task 2-C 仍是 `not_released`。
- **回归路径**：冻结题集 → Reader-only Agent 评分 → 失败样本/来源回查 → exit manifest。
- **验收**：AC-04～AC-09。

- **可能受冲击的业务规则**：Reader/Audit 分包、单一信号事实源、页级/交付级状态分离、失败不覆盖旧正式包。
- **明确无影响**：TopicIndex 身份、Task 2-A Reader Bundle 合同、Task 2-B 三类页面、Claim/Evidence/Provenance 权威和 Task 0–S6 保存底线。

## 14. build-spec 审查事实与处置

- **审查事实**：build-spec 审查 attempt `5e19f1a2-bf1a-4823-ad04-8d743603d463` 可用，异源 `opencode/v4flash` 提出 2 个主要问题和 4 个小问题；`pi/k3` 进程异常退出，`codex/luna` 因与 host 同源不计为独立审查。主要问题和小问题均已按原始需求修复：类别硬覆盖、Task 2-B 证据状态、运行隔离、预算、Agent 出口字段和逐题路径字段。
- **复核事实**：复核 attempt `03b4fa59-5115-4f6b-9999-01f0af0c4437` 可用，异源 `opencode/v4flash` 又指出 1 个主要问题和 2 个小问题；已修复为 Task 0 冻结规则确定性派生、既有信任事实只读投影、AC-05 字段完整对齐。
- **当前边界**：审查是质量事实和建议，不被写成 provider pass；Task 2-B 跨任务证据已按 `PFACT-001=verified` 完成 live handoff recheck，RISK-02/OPEN-02 已关闭；实现期间若基线改变仍须停止并复核。
