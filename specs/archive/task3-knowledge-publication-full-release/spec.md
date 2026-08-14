# 功能规格：Task 3 全量知识发布与简化确认

> 基于已确认的 Task 3 决策。本文件只定义用户可观察行为、状态、边界和验收，不定义代码文件、工程命令或任务拆分。

- **功能名**：全量 Reader 发布、自动质量门与一页汇总确认
- **来源**：`R-001`～`R-005`、Task 3 decision-log 最终确认、PRD Task 3
- **状态**：已接受方向的规格草案
- **内容 profile**：`spec-content.v3`

## 速读卡（30 秒）

- **一句话需求**：维护者对 89 条冻结来源执行一次全量知识发布，机器完成内容、来源和读者质量验收，人只看一页汇总决定是否确认发布。
- **核心改动点**：生成完整 Reader/Audit 包；运行固定 17+3 自动题集；用清楚的硬失败、警告和无法判定分类决定整包状态。
- **最大影响面**：全量 Reader 导航、Audit/Archive、旧路径、正式包切换和 Task 3-Closeout 交接。
- **验收信号**：硬门和自动题集通过、汇总完整可判定、人工完成汇总确认后才可 `released`；任何未知结果保持 `not_released`。

## 来源与决策映射

| Source ID | Decision | FR / AC | Status | Handoff |
| --- | --- | --- | --- | --- |
| R-001 | 进入 Task 3 | 全部 FR/AC | current | 真实全量验证 |
| R-002 | 不由规格补需求 | 全部 FR/AC | current | 缺方向即退回 |
| R-003 | 决策可追溯 | FR-SUMMARY-001 | current | 保留确认事实 |
| R-004 | 完整范围与边界 | 全部 SCN/FR | current | 十维已覆盖 |
| R-005 | 全量发布与对比 | FR-PUBLISH-001～FR-CLOSE-001 | current | Closeout 收尾 |
| 用户 B/A/A | 汇总确认与失败边界 | FR-QUALITY-001～FR-RELEASE-003 | current | 不写 human_reviewed |
| DEFER-001～005 | 延期交接 | RISK-003～005 | 见下方逐项矩阵 | 按 owner 关闭 |

## 延期项逐项交接矩阵

下面五项沿用 decision-log 的原始含义。这里补齐 owner、trigger、handoff 和 close condition，避免下游自行猜测；这些字段不改变当前产品方向。

- **DEFER-001**
  - **状态**：deferred
  - **Owner**：Task 3-Closeout
  - **Trigger**：Task 3 的最终状态已经由 verify-code readback
  - **Handoff**：同步根 `AGENTS.md`、`CONTEXT.md`、`README.md`、`docs/plans/README.md`
  - **Close condition**：文档与最终代码、命令、状态和目录一致
- **DEFER-002**
  - **状态**：deferred
  - **Owner**：Task 3-Closeout
  - **Trigger**：Task 3 最终 artifact/hash 齐全
  - **Handoff**：完成仓库 inventory、引用扫描、归档、清理和恢复演练
  - **Close condition**：分类、hash、旧路径映射和可恢复证据齐全；不确定项保留
- **DEFER-003**
  - **状态**：resolved in make-decision
  - **Owner**：make-decision（已关闭）
  - **Trigger**：用户最终确认“人工只看一页汇总，不逐页、逐题、逐来源链验收”
  - **Handoff**：下游实现固定 17+3 自动题集和一页汇总确认；不得写 `human_reviewed`
  - **Close condition**：FR-SUMMARY-001、FR-RELEASE-001～003 保持 `agent_only`/自动评审事实与汇总确认语义
- **DEFER-004**
  - **状态**：deferred to downstream materials
  - **Owner**：build-plan、build-code、verify-code，按各自阶段落地
  - **Trigger**：实现需要冻结 provider/model/config、完整题集评分表、归属抽样规则或对比字段时
  - **Handoff**：只在 plan/tasks 和真实 verify-code 证据中记录已确认技术细节；不得由 build-spec 补产品取舍
  - **Close condition**：实际运行记录 provider/model/config、题集评分、归属抽样和对比字段；任何方向变化退回 owning decision
- **DEFER-005**
  - **状态**：deferred to build-code/verify-code
  - **Owner**：build-code、verify-code
  - **Trigger**：Task 3 实现完成并开始全量真实验收
  - **Handoff**：完成全量真实运行、全量读者评分、汇总确认和正式 release readback
  - **Close condition**：以真实证据诚实给出正式 `released` 或 `not_released`，并保留失败与未决原因

`spec-research`：`skipped`。当前产品行为可由已确认 decision-log、PRD、Task 2-C 交接和现有领域合同精确定义；外部实时事实不会改变本规格方向。provider 的真实调用和配置值由 build-plan 核实，不在本规格猜测。

`spec-clarify`：`trigger=false`。用户流程、页面范围、状态、成功/失败、角色、外部影响、非目标、延期和验收证据均已锁定；没有会改变范围、接口、数据、安全或运维的规格歧义。

## 1. 问题与紧迫性

Task 2-C 已证明小语料信号和自动读者门可以运行，但整包仍是 `not_released`。用户真正需要的是把 89 条来源生成一套可读、可追溯、能恢复的正式知识包，同时不承担逐页、逐题、逐来源链的人工验收负担。

现在必须完成 Task 3，因为只有这一阶段能把全量 Reader、Audit/Archive、旧路径兼容、固定对比和全量读者题集放进同一次诚实发布判断。只看文件写入成功、测试绿色或页面数量增加，都不能替代正式发布结果。

## 2. 背景、目标与范围

### 背景

Task 0～Task 2-C 已冻结来源清单、TopicIndex、ProductGazetteer、Concept Contract v1、三类页面、读者信号、题集规则和小语料质量边界。Task 3 复用这些合同做全量投影，不重新探索主题、不重新设计正文，也不临时放宽门槛。当前布局使用 Task 2-A 起的 OKF-compatible `Reader Bundle`；旧 `Reader Package` 只表示历史布局，不作为本期输出名称。

### 目标

- 生成一套读者日常使用的 Reader Bundle 和一套审计、失败恢复使用的 Audit/Archive Package。
- 让机器自动完成来源、Claim、结构、完整性、导航和固定读者题集验收。
- 让维护者只看一页汇总，确认自动结果完整、可判定且没有硬失败。
- 失败不覆盖上一份 `released` 包，成功和失败都能追溯、对比和重放。

### 范围内

- 89 条冻结来源的全量语义发布和离线基线区分。
- canonical 根、产品/模块索引、正式 concept 页面、来源入口和运行日志。
- Audit/Archive、Related links、旧路径映射、固定对比报告和 affected replay。
- 自动机器硬门、完整 17+3 读者题集、一页汇总确认和整包 `released/not_released` 判定。

## 3. 用户场景与状态覆盖

### SCN-001：启动全量发布

- **角色**：维护者
- **Given**：Task 0～Task 2-C 出口可读，89 条来源和全部冻结合同可定位。
- **When**：维护者启动一次 Task 3 全量发布。
- **Then**：系统冻结本次输入和运行身份，生成候选 Reader、Audit/Archive、质量结果和汇总；运行中不切换正式包。

### SCN-002：读者从 canonical 导航找知识

- **角色**：读者
- **Given**：候选包中的页面通过页级机器门。
- **When**：读者从兼容 Home 进入唯一根索引，再进入产品、模块和 concept 页面。
- **Then**：读者得到可读标题、完整正文、来源入口和有事实依据的 Related links；失败页和审计现场不进入日常导航。

### SCN-003：自动完成全量质量验收

- **角色**：自动评审
- **Given**：Reader Bundle、冻结题集和机器质量合同齐全。
- **When**：系统执行机器硬门、17 个正向题、3 个负向题和标题/归属检查。
- **Then**：每项都有可回放结果、评分主体、规则、样本、seed 和失败原因；自动评审不产生 `human_reviewed`。

### SCN-004：维护者确认一页汇总

- **角色**：维护者
- **Given**：自动运行完成，汇总明确区分硬失败、非阻断警告和无法判定。
- **When**：维护者只查看汇总并确认其完整、可判定且没有硬失败。
- **Then**：确认事实绑定当前运行；无需打开知识页、逐题检查或核对来源链。

### SCN-005：硬失败或未知结果

- **角色**：维护者
- **Given**：任一硬门失败、自动题集未达阈值、汇总缺失，或结果无法分类。
- **When**：系统计算整包交付状态。
- **Then**：候选包保持 `not_released`，旧 `released` 包不变，失败原因和现场进入 Audit/Archive。

### SCN-006：只有已知非阻断警告

- **角色**：维护者与读者
- **Given**：全部硬门通过，但存在 stale、deprecated 等已定义警告。
- **When**：系统生成汇总并完成确认。
- **Then**：警告继续可见且留痕，但不阻止整包 `released`；不得把警告隐藏或改写成无问题。

### SCN-007：取消、超时、失败后恢复

- **角色**：维护者
- **Given**：运行被取消、超预算、provider 失败或部分 source/topic 未完成。
- **When**：维护者重试同一合同下的运行。
- **Then**：只重放未完成 affected source/topic，保留成功批次、旧正式包和失败现场；合同变化则停止重放并返回范围修订。

### SCN-008：并发运行或旧路径访问

- **角色**：维护者与既有读者
- **Given**：已有正式包、旧书签或第二个写入请求。
- **When**：新运行发布或读者访问旧路径。
- **Then**：单写者边界避免部分切换；旧路径解析到 canonical 页面，或明确显示 alias/deprecated 说明。

### SCN-009：只完成离线基线

- **角色**：维护者
- **Given**：本次只执行 `--no-llm` 与 Jaccard，或语义运行发生 fallback。
- **When**：系统生成结果和汇总。
- **Then**：结果明确标为 offline baseline 或 semantic limitation，整包不得冒充语义 `released`。

### 状态覆盖清单

- [x] **默认态**：SCN-001～004，完整生成、自动验收、汇总确认和发布。
- [x] **空态**：SCN-005，空 Reader、空分类、缺页或缺汇总属于硬失败。
- [x] **错误态**：SCN-005、007、009，失败留痕且旧正式包不变。
- [x] **加载态**：SCN-001，运行中只有候选状态，不对外宣称发布。
- [x] **取消态**：SCN-007，取消不产生通过证据或正式切换。
- [x] **边界态**：SCN-005、006、009，阈值、警告、未知和离线基线分开处理。
- [ ] **权限态**：N/A — 本产品是本地人工触发工具，没有独立登录或角色权限面；输入不可读按硬失败处理。
- [x] **竞态**：SCN-008，并发写入不能产生部分正式包或第二套事实源。

## 4. 产品事实与假设（PFACT）

- **PFACT-001**：Task 2-C 已冻结小语料 Agent-only 读者门，交付仍为 `not_released`。
  - **status**：`verified`
  - **证据或来源**：Task 2-C 归档规格、实现交接和当前 decision-log 关键事实。
  - **关联**：FR-QUALITY-002、FR-RELEASE-001、AC-05、AC-08

- **PFACT-002**：页级状态与整包交付状态是两个不同概念。
  - **status**：`verified`
  - **证据或来源**：PRD 状态合同、当前 CONTEXT 和 decision-log 最终确认。
  - **关联**：FR-PUBLISH-002、FR-RELEASE-001、AC-02、AC-08

- **PFACT-003**：人工职责只是一页汇总确认，不是知识内容审核。
  - **status**：`verified`
  - **证据或来源**：用户选择 B 及最终回复“确认，继续”。
  - **关联**：FR-SUMMARY-001、FR-RELEASE-002、AC-07、AC-09

- **PFACT-004**：完整读者门固定为 17 个正向和 3 个负向，门槛为首次命中至少 15/17、误命中 0/3。
  - **status**：`verified`
  - **证据或来源**：PRD Task 3 和已确认 decision-log 成功边界。
  - **关联**：FR-QUALITY-002、AC-05

- **PFACT-005**：Reader Bundle 是日常阅读入口，Audit/Archive 只用于追溯、失败恢复和排错。
  - **status**：`verified`
  - **证据或来源**：PRD Reader/Audit 合同、CONTEXT 和 ADR 0004。
  - **关联**：FR-PUBLISH-001、FR-NAV-001、AC-01、AC-03

- **PFACT-006**：汇总确认的字段名、回执形状和存放位置不改变用户可观察行为。
  - **status**：`inferred`
  - **证据或来源**：decision-log 延期项只延期序列化选择，同时锁定最小确认事实；限制是下游不得改变确认含义。
  - **关联**：FR-SUMMARY-001、FR-RELEASE-002、AC-07、AC-09

- **PFACT-007**：本阶段不需要外部产品调研或交互界面设计审查。
  - **status**：`not_applicable`
  - **不适用理由**：产品面是本地命令生成的 Markdown 包和静态汇总；外部实时事实与响应式、键盘、焦点等 UI 设计不改变本规格。信息架构和可读状态已由场景与 AC 覆盖。
  - **关联**：FR-NAV-001、FR-SUMMARY-001、AC-03、AC-07

## 5. 功能需求

### 全量输入与发布包（PUBLISH）

- **FR-PUBLISH-001**：每次 Task 3 必须冻结 89 条来源、TopicIndex、ProductGazetteer、Concept Contract、模板、题集、provider/model/config、预算和当前版本身份，并从同一冻结输入生成 Reader 与 Audit/Archive。
  - **范围边界**：不因 89 条来源机械生成 89 个页面；不在本阶段修改主题身份、页面类型或正文合同。
  - **依据**：R-001、R-005、PFACT-001、PFACT-005
  - **场景**：SCN-001、SCN-007
  - **验收**：AC-01、AC-10

- **FR-PUBLISH-002**：页级只使用 `published/degraded`；通过页级机器门的页面才可进入候选 Reader，失败、冲突、无归属或缺证据内容进入 Audit/Archive。
  - **范围边界**：stale、deprecated 等普通提示本身不自动变成 `degraded`。
  - **依据**：R-004、PFACT-002、PFACT-005
  - **场景**：SCN-002、SCN-005、SCN-006
  - **验收**：AC-02

### 导航、关系与兼容（NAV）

- **FR-NAV-001**：Reader Bundle 必须提供 `README.md`、兼容 Home、唯一 canonical 根、产品/模块索引、正式 concept 页面、来源入口和运行日志；所有导航由同一 TopicIndex 与审计事实投影。
  - **范围边界**：不维护第二套 Home、分类、来源或页面身份事实；Audit/Archive 不作为日常入口。
  - **依据**：R-005、PFACT-005
  - **场景**：SCN-002
  - **验收**：AC-03

- **FR-NAV-002**：Related links 只有在同产品、同模块、共享来源或原文明示互引时才生成双向链接；没有关系就省略。
  - **范围边界**：不得只凭相似词或模型猜测关系。
  - **依据**：R-005、decision-log 用户流程
  - **场景**：SCN-002
  - **验收**：AC-04

- **FR-NAV-003**：TopicIndex 中的旧路径必须解析到当前 canonical 页面，或明确标为 alias/deprecated 并说明原因。
  - **范围边界**：旧文件可以保留，但不能让书签落到无说明的旧正文。
  - **依据**：R-005、decision-log 成功边界
  - **场景**：SCN-008
  - **验收**：AC-11

### 自动质量验收（QUALITY）

- **FR-QUALITY-001**：系统必须自动检查来源、Claim、结构、完整性、页面长度、导航、失败隔离和可重放交付；任何硬门失败或结果无法判定都阻止 `released`。
  - **范围边界**：写入成功、测试绿色、页面数或 Claim 数增加、速度/耗时或 provider 成功都不能代替这些结果，也不能单独作为读者质量或发布证据。
  - **依据**：R-004、用户 A、PFACT-002
  - **场景**：SCN-003、SCN-005
  - **验收**：AC-05、AC-06

- **FR-QUALITY-002**：自动评审必须执行冻结的 17+3 完整题集，记录入口、首次命中页、答案、边界/版本、来源链、评审主体、规则、seed、结果和失败原因。自动流程可以组合确定性检查与 Agent 评审，但必须记录实际 actor/model/rule/seed/hash，并且评分输入只来自 Reader Bundle。
  - **范围边界**：正向首次命中至少 15/17，负向误命中必须 0/3；自动记录不得产生 `human_reviewed`。
  - **依据**：用户 B、PFACT-001、PFACT-004
  - **场景**：SCN-003、SCN-005
  - **验收**：AC-05

- **FR-QUALITY-003**：系统必须自动验证标题脱离路径可理解率至少 90%、产品/模块归属准确率至少 90%，并保留评分主体、规则、样本量和 seed。
  - **范围边界**：人工不逐页抽样；无法自动得出可判定结果时按硬失败处理。
  - **依据**：decision-log 成功边界、PRD Task 3
  - **场景**：SCN-003、SCN-005
  - **验收**：AC-06

### 一页汇总与发布状态（SUMMARY / RELEASE）

- **FR-SUMMARY-001**：系统必须生成一页可独立判断的自动验收汇总，至少显示运行身份、完成情况、关键计数、硬失败、非阻断警告、无法判定项、17+3 结果、90% 检查结果、离线/语义模式和旧包保护结论。
  - **范围边界**：汇总提供结果和定位入口，不要求人工打开页面、逐题或逐来源链核验。
  - **依据**：用户 B、PFACT-003、PFACT-006
  - **场景**：SCN-004～006、SCN-009
  - **验收**：AC-07

- **FR-RELEASE-001**：整包只使用 `released/not_released`；只有机器硬门、自动读者门、交付完整性和汇总确认全部满足时才可 `released`。
  - **范围边界**：`released` 不表示人工读过知识内容，也不产生 `human_reviewed`。
  - **依据**：用户撤回删除状态、用户 B、PFACT-002、PFACT-003
  - **场景**：SCN-004、SCN-005
  - **验收**：AC-08、AC-09

- **FR-RELEASE-002**：汇总确认必须绑定当前运行，并记录确认主体和时间；确认只表示汇总完整、可判定且无硬失败。
  - **范围边界**：具体字段和存放位置由工程设计决定，但不能省略运行绑定或改名为 `human_reviewed`。
  - **依据**：用户 B、PFACT-003、PFACT-006
  - **场景**：SCN-004
  - **验收**：AC-09

- **FR-RELEASE-003**：已知非阻断警告不阻止 `released`，但必须在汇总和 Audit 留痕；未知、未分类、矛盾或无法解释的信号一律阻止发布。
  - **范围边界**：不允许临时交给人工逐项裁决，也不允许把未知自动降为警告。
  - **依据**：用户 A、用户最终失败边界 A
  - **场景**：SCN-005、SCN-006
  - **验收**：AC-08

### 对比、恢复与收尾（COMPARE / RECOVER / CLOSE）

- **FR-COMPARE-001**：系统必须生成 Task 2 旧结果、CompanyBrain 和新结果的固定对比，分别说明可比对象、保存完整性、机器质量、正文/导航可读性、信任/新鲜度、失败、耗时、成本和局限。
  - **范围边界**：不可比维度标 `N/A`，不能用主观印象或单一通过/失败代替。
  - **依据**：R-005、decision-log 用户流程
  - **场景**：SCN-003、SCN-004
  - **验收**：AC-12

- **FR-RECOVER-001**：取消、失败、超时或重复运行只重放未完成 affected source/topic，保留成功批次、旧正式包和审计现场。
  - **范围边界**：合同变化停止重放；不以 fallback、离线基线或写入成功改写状态。
  - **依据**：R-005、decision-log 失败边界
  - **场景**：SCN-007～009
  - **验收**：AC-10

- **FR-CLOSE-001**：Task 3 必须把最终实际结果、状态、风险和延期项交给 Task 3-Closeout。
  - **范围边界**：Closeout 只同步文档、清理、归档和演练恢复，不重新定义页面、主题、质量门或发布含义。
  - **依据**：R-005、DEFER-001、DEFER-002
  - **场景**：SCN-004、SCN-005
  - **验收**：AC-13

## 6. 模块划分

### 全量发布

- **负责什么**：冻结输入并生成 Reader 与 Audit/Archive 候选包。
- **对外提供什么**：可读页面、完整审计事实和候选交付身份。
- **依赖谁**：Task 0～Task 2-C 冻结合同。
- **测试边界**：89 条来源定位、页面状态、分包和原子切换。

### 导航与兼容

- **负责什么**：投影 canonical 导航、Related links 和旧路径映射。
- **对外提供什么**：唯一日常入口和可解释旧链接。
- **依赖谁**：TopicIndex、ProductGazetteer 和审计事实。
- **测试边界**：导航完整、关系有依据、无断链和无第二事实源。

### 自动验收与汇总

- **负责什么**：执行机器门、读者题集、标题/归属检查并生成一页汇总。
- **对外提供什么**：硬失败、警告、未知和可确认结果。
- **依赖谁**：Reader Bundle、冻结题集和质量合同。
- **测试边界**：阈值、可回放字段、分类和无人工内容审核。

### 发布与恢复

- **负责什么**：绑定汇总确认、决定整包状态并保护旧正式包。
- **对外提供什么**：真实 `released/not_released`、失败证据和 affected replay。
- **依赖谁**：全部自动结果、候选包和当前正式包。
- **测试边界**：确认绑定、警告放行、未知阻断、取消/竞态和旧包保护。

## 7. 关键实体

- **Publication Input Snapshot**：一次运行冻结的 89 条来源和 TopicIndex、词典、合同、模板、题集、provider/config、预算、版本身份。
- **Reader Bundle**：Task 2-A 起的 OKF-compatible 读者交付形态，包含 `README.md`、canonical 导航、正式页面、来源入口和运行日志，不包含审计现场。
- **Audit/Archive Package**：manifest、snapshot、Claim/Evidence、原文、失败原因、旧页面、运行和质量证据。
- **Automatic Quality Result**：机器硬门、17+3、标题/归属检查的可回放结果及分类。
- **Release Summary**：人只需查看的一页结果，明确硬失败、警告和无法判定。
- **Summary Confirmation**：绑定当前运行的人工汇总确认，不代表内容审核。
- **Delivery Package**：候选或正式整包，交付状态只有 `released/not_released`。
- **Path Mapping**：旧路径到 canonical 页面或 deprecated 说明的映射。
- **Comparison Report**：三组结果按固定维度和可比性生成的对比。

## 8. 数据和生命周期

- **数据粒度**：来源、Claim、页面、题目结果、警告/失败、确认和整包状态分别记录，不能相互冒充。
- **数据时效**：每次运行绑定冻结输入与版本；来源或合同变化必须形成新的运行身份。
- **缺失或迟到**：任何必需输入、结果或确认缺失都保持 `not_released`；迟到结果不能补写到已结束运行。
- **预览与正式**：运行中和未确认结果都是候选；只有全部条件满足后才原子切换为正式 `released` 包。
- **正式根前置条件**：发布必须显式提供 formal root。已有 formal root 必须先通过完整包形状、无软链接和整包 hash 预检；首次发布可以指向一个明确的空目标，但不能把“没有目标”当成已保护。
- **当前与历史**：新正式包不静默删除旧页面、旧路径、失败运行或审计历史；当前导航只指向当前 canonical 页面。
- **归属与清理**：Reader 归读者入口，Audit/Archive 归追溯恢复；历史清理由 Task 3-Closeout 依据引用和恢复规则处理。

状态转换：`运行中候选 → not_released` 是默认路径；只有“自动硬门通过 + 自动读者门通过 + 交付齐全 + 汇总确认”才能变为 `released`。任何失败、取消、未知、缺确认或离线限制都停在 `not_released`。页级 `published/degraded` 不自动决定整包状态。

## 9. 兼容性预留

- **既有消费方**：兼容 Home 和旧书签继续可用，但最终指向唯一 canonical 导航。
- **命名预留**：保留 `published/degraded`、`released/not_released`、`agent_assisted` 和 `human_reviewed` 的既有含义；新增动作只叫“汇总确认”。
- **容器预留**：沿用现有 Reader/Audit 包和 Task 2-C 质量记录，不新增第二套发布系统。
- **状态预留**：本期不增加第三种页级或交付级状态；未知通过失败分类表达，不新增状态值。
- **扩展边界**：未来改变页面类型、主题身份、题集或质量门必须重新做方向决策；本期不预建通用调度或数据库能力。

## 10. 明确不做与默认必须成立

### 明确不做

- 不要求人工逐页、逐题或逐来源链验收；来源为用户 B。
- 不把汇总确认写成 `human_reviewed`、`verified` 或人工内容信任等级；来源为用户 B。
- 不删除 `released/not_released`，不改变 Task 2-C 的 Agent-only 历史范围；来源为撤回决定和最终确认。
- 不新增页面类型，不重新定义 TopicIndex、主题身份、Concept Contract 或正文结构；来源为 R-005。
- 不维护第二套 Home、导航、来源或发布状态事实；来源为 R-005 和 simplicity 边界。
- 不引入数据库、图数据库、向量数据库、CAS、调度器、后台守护、永久人工队列或 AgentMemory 正式接入；来源为 decision-log 非目标。
- 不在 Task 3-Closeout 修改业务范围或发布门；来源为 DEFER-001、DEFER-002。

### 默认必须成立

- `--no-llm` 不发出 LLM 或 embedding 请求，Jaccard 与语义分数不在同一次运行混用：FR-RECOVER-001、AC-10。
- 正文最多 120 行，整页最多 300 行；旧分页不进入当前导航但不静默删除：FR-QUALITY-001、AC-06。
- 每条有效 Claim 保持唯一目标页和可回查来源链：FR-QUALITY-001、AC-06。
- 失败不覆盖旧正式包，成功也必须保留本次可重放证据：FR-RELEASE-001、FR-RECOVER-001、AC-08、AC-10。

## 11. 验收标准

- [ ] **AC-01**：全量输入和双包完整冻结。
  - **需求**：FR-PUBLISH-001
  验证：核对运行 manifest 与 Reader/Audit 产物清单。
  - **通过条件**：89 条来源及全部合同、题集、配置、预算和版本身份可定位，Reader 与 Audit 来自同一冻结输入。
  - **失败条件**：输入缺失、hash/版本不一致或双包来源不一致。
  - **证据类型**：`evidence`

- [ ] **AC-02**：页面状态和分包边界正确。
  - **需求**：FR-PUBLISH-002
  验证：覆盖正常、失败、冲突、无归属、缺证据、stale 和 deprecated 样例。
  - **通过条件**：明确失败页为 degraded 且不进 Reader；普通警告不被误降级。
  - **失败条件**：失败页进入正式导航，或 stale/deprecated 被错误当硬失败。
  - **证据类型**：`test`

- [ ] **AC-03**：canonical 导航完整且只有一个事实源。
  - **需求**：FR-NAV-001
  验证：从 Home 走到根、产品、模块、页面和来源入口。
  - **通过条件**：所有正式页面可达，无空分类、空壳入口、hash 主路径、断链或第二套导航事实。
  - **失败条件**：正式页不可达、导航事实冲突或 Audit 成为日常入口。
  - **证据类型**：`test`

- [ ] **AC-04**：Related links 只表达有证据关系。
  - **需求**：FR-NAV-002
  验证：检查正向关系和无关系样例的双向链接。
  - **通过条件**：每条链接有允许依据且双向一致；无关系样例不生成链接。
  - **失败条件**：单向、无依据、仅词面相似或缺失应有互引。
  - **证据类型**：`test`

- [ ] **AC-05**：完整自动读者题集达到阈值。
  - **需求**：FR-QUALITY-001、FR-QUALITY-002
  验证：自动运行冻结 17+3 并读取逐题记录。
  - **通过条件**：正向首次命中至少 15/17、负向误命中 0/3；答案、边界/版本、来源链和评审字段完整。
  - **失败条件**：未达阈值、题目缺失、来源断裂、结果不可回放或出现 `human_reviewed` 伪记录。
  - **证据类型**：`evidence`

- [ ] **AC-06**：机器质量和标题/归属门全部可判定。
  - **需求**：FR-QUALITY-001、FR-QUALITY-003
  验证：读取机器报告、失败样本和评分记录。
  - **通过条件**：来源/Claim/结构/完整性/页面长度/导航门通过，标题可理解率和归属准确率均至少 90%，评分主体、规则、样本量和 seed 齐全。
  - **失败条件**：任一硬门失败、页面超限、Claim 丢失/重复、评分低于阈值或结果不可判定。
  - **证据类型**：`evidence`

- [ ] **AC-07**：一页汇总足以做确认。
  - **需求**：FR-SUMMARY-001
  验证：只读取汇总，不打开知识页或逐题记录。
  - **通过条件**：当前运行、完成情况、关键计数、硬失败、警告、未知、17+3、90% 检查、运行模式和旧包保护结论齐全且不矛盾。
  - **失败条件**：必须翻页或查来源链才能判断，或分类缺失、矛盾、模糊。
  - **证据类型**：`manual`

- [ ] **AC-08**：整包状态诚实且未知阻断。
  - **需求**：FR-RELEASE-001、FR-RELEASE-003
  验证：覆盖全通过、硬失败、普通警告、未知和缺确认组合。
  - **通过条件**：仅全通过且已确认的当前运行可 released；普通警告可留痕放行；硬失败和未知均 not_released。
  - **失败条件**：未知被当警告、硬失败仍发布、或失败覆盖旧正式包。
  - **证据类型**：`test`

- [ ] **AC-09**：汇总确认不冒充内容审核。
  - **需求**：FR-RELEASE-001、FR-RELEASE-002
  验证：核对确认记录与当前运行和交付状态。
  - **通过条件**：确认主体、时间、运行绑定和确认含义齐全；没有新增 `human_reviewed`、`verified` 或人工 trust tier。
  - **失败条件**：确认未绑定运行、可跨运行复用，或被记录为人工内容审核。
  - **证据类型**：`evidence`

- [ ] **AC-10**：取消、失败、重放和离线边界保护旧包。
  - **需求**：FR-PUBLISH-001、FR-RECOVER-001
  验证：覆盖取消、provider 失败、超时、部分完成、重复失败、离线和 fallback。
  - **通过条件**：只重放未完成 affected 项；成功批次和旧正式包保留；离线/fallback 明示且不冒充 semantic released。
  - **失败条件**：整库无差别重跑、成功证据丢失、旧包被覆盖或离线结果被误发布。
  - **证据类型**：`test`

- [ ] **AC-11**：全部旧路径有明确结果。
  - **需求**：FR-NAV-003
  验证：遍历冻结 old path mapping 并解析目标。
  - **通过条件**：每条旧路径可点击到 canonical 页面，或显示真实 alias/deprecated 说明。
  - **失败条件**：旧书签落到无说明旧正文、断链或错误主题。
  - **证据类型**：`test`

- [ ] **AC-12**：固定对比报告完整且不伪造可比性。
  - **需求**：FR-COMPARE-001
  验证：检查三组结果和全部固定维度。
  - **通过条件**：每个维度标明 comparable 或 N/A，并覆盖完整性、质量、可读性、信任、失败、性能、成本和局限。
  - **失败条件**：只给总分/结论、缺维度，或用主观值补不可比数据。
  - **证据类型**：`evidence`

- [ ] **AC-13**：Task 3 交接不重新开需求。
  - **需求**：FR-CLOSE-001
  验证：核对最终交接中的结果、状态、风险和延期 owner。
  - **通过条件**：Closeout 只接收同步、清理、归档和恢复演练事项；Task 3 真实状态不被改写。
  - **失败条件**：Closeout 新增页面、主题、质量门或把 not_released 写成 released。
  - **证据类型**：`evidence`

## 12. 风险、未决与交接

- **RISK-001**：自动评审漏掉细微表达问题。
  - **受影响 ID**：PFACT-003、FR-QUALITY-002、FR-QUALITY-003、AC-05、AC-06
  - **触发条件**：固定题集和自动评分未覆盖真实读者的新问题。
  - **后果**：整包可能 released，但仍有局部可读性瑕疵。
  - **缓解或 STOP**：固定完整题集、来源硬门、失败样本和可重放报告；未知结果必须 STOP。
  - **处理 Stage**：`verify-code`
  - **验证**：真实 89 条和 17+3 运行后检查失败与局限报告。

- **RISK-002**：已知警告随 released 保留。
  - **受影响 ID**：FR-RELEASE-003、FR-SUMMARY-001、AC-07、AC-08
  - **触发条件**：全部硬门通过但存在 stale/deprecated 等警告。
  - **后果**：读者可能看到需要复核或历史兼容内容。
  - **缓解或 STOP**：汇总和 Audit 必须显示；任何无法分类信号升级为硬失败。
  - **处理 Stage**：`build-code`
  - **验证**：警告组合验收与 Audit 回查。

- **RISK-003**：全量语义运行超过 provider 或时间预算。
  - **受影响 ID**：FR-PUBLISH-001、FR-RECOVER-001、AC-01、AC-10
  - **触发条件**：provider 失败、超时、截断、超预算或 fallback。
  - **后果**：本次只能 not_released 或交付离线基线。
  - **缓解或 STOP**：冻结实际预算和重放边界；不切 provider 偷渡，不把 fallback 当发布成功。
  - **处理 Stage**：`build-code`
  - **验证**：真实运行报告和失败恢复证据。

- **RISK-004**：汇总确认的工程形状偏离已确认含义。
  - **受影响 ID**：PFACT-006、FR-SUMMARY-001、FR-RELEASE-002、AC-07、AC-09
  - **触发条件**：下游把确认设计成内容审核、可跨运行复用或缺主体/时间。
  - **后果**：人工负担回升或发布证据失真。
  - **缓解或 STOP**：build-plan 只能选择字段与存放位置，不得改变最小确认事实。
  - **处理 Stage**：`build-plan`
  - **验证**：计划和实现对 AC-07/09 的逐项映射。

- **RISK-005**：最终文档与真实运行状态不同步。
  - **受影响 ID**：FR-CLOSE-001、AC-13
  - **触发条件**：Task 3-Closeout 使用计划状态替代最终产物状态。
  - **后果**：维护者误把 not_released 当正式发布或使用错误命令。
  - **缓解或 STOP**：Closeout 只读取最终实现和运行证据；不重新决定业务语义。
  - **处理 Stage**：`verify-code`
  - **验证**：最终交接明确真实状态和延期项。

未决问题：无会改变当前产品方向的 OPEN。provider 调用方式、确认字段名、文件落点和精确测试命令由 build-plan 核实并设计；若它们要求改变本规格语义，必须停止并返回 make-decision/build-spec owner。

延期交接：真实 89 条编译、完整 17+3、正式状态和失败重放交给 build-code/verify-code；根文档同步、仓库 inventory、归档清理和恢复演练交给 Task 3-Closeout。

## 13. 业务影响与回归范围

### Task 2-C 质量出口

- **既有行为**：小语料 Agent-only 读者门通过也保持 `not_released`。
- **本需求影响**：Task 3 复用冻结门并扩大到 89 条与完整题集，但不改写 Task 2-C 历史证据。
- **回归路径**：小语料信号、Agent-only 字段、来源链和 not_released 出口继续成立。
- **验收**：AC-05、AC-09

### Reader/Audit 分包与导航

- **既有行为**：Reader 是阅读入口，Audit/Archive 负责追溯和失败恢复。
- **本需求影响**：全量投影 canonical 导航、Related links 和旧路径兼容。
- **回归路径**：Home、根索引、产品/模块、concept、来源入口和失败页隔离全部走通。
- **验收**：AC-02～04、AC-11

### 发布与失败保护

- **既有行为**：Task 0～Task 2-C 只产生 not_released 候选或样本包。
- **本需求影响**：Task 3 首次允许在全部门和汇总确认后 released。
- **回归路径**：取消、硬失败、警告、未知、离线、fallback、重放和并发组合。
- **验收**：AC-07～10

### 固定对比与项目交接

- **既有行为**：已有 Task 2、Task 1 和 CompanyBrain 的不同基线材料。
- **本需求影响**：形成不伪造可比性的固定报告，并把真实状态交给 Closeout。
- **回归路径**：全部固定维度、N/A、性能/成本、局限和最终状态一致性。
- **验收**：AC-12、AC-13

- **可能受冲击的业务规则**：主题身份、三类页面、Claim 唯一归属、Reader/Audit 分工、单写者、旧包保护、离线/语义分离和状态命名。
- **明确无影响**：Task 2-C 历史证据、现有页面类型、TopicIndex 身份规则、正式 pipeline 之外的数据库/调度/AgentMemory 能力。
