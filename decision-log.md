# 决策记录 · task10-slimming-without-capability-loss

> 本文件是 make-decision 阶段唯一权威材料。OI 大纲只存在于本文件内，不另建需求账本、状态机或第五份材料。
> 当前阶段状态：**in_progress**（step 1 load-context、step 2 triage-scope 完成；下一步步骤 3 Talk Round 1）。
> 标题层级说明：`## 原始需求`、`## 核心需求`、`## 核心目标`、`## 已选方向`、`## 验收标准`、`## 范围`、
> `## 完整用户旅程`、`## UI applicability`、`## 收敛检查` 是运行时读取的固定小节名，保持不带编号。

## 任务身份

| 项 | 值 |
| --- | --- |
| project | KnowledgeDigest |
| task_id | `task10-slimming-without-capability-loss` |
| stage | make-decision |
| worktree | `/Users/Hugh/Hugh/Project/KnowledgeDigest-task10-slimming-without-capability-loss` |
| branch | `task/KnowledgeDigest/task10-slimming-without-capability-loss` |
| baseline_commit | `eee55492517bc86e3aad4838fe215bb23d84e8a4` |
| task_path | `/Users/Hugh/Hugh/Knowledge/Projects/KnowledgeDigest/tasks/task10-slimming-without-capability-loss` |
| storage_root | `/Users/Hugh/Hugh/Knowledge` |
| created_at | 2026-09-16 |

- **任务类型**：普通任务

**范围声明（triage-scope 初步，待 Talk Round 1 用户确认）**：本任务范围 = 母任务 PRD
（`specs/archive/task6-effect-gap-and-architecture-reset/prd.md`）中的 **K4 一张卡**（瘦身且不丢能力），
不含 K1 语义层页面编译、K2 入口与导航、K3 发布安全与真实查询集验收（三张卡均已完成提交）。
母任务与其兄弟任务材料对本任务只读；本任务自建 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 四份材料。

**任务类型选择理由**：K4 不是新功能方向选择，而是在已确认方向（T-004 = A 保留骨架、砍掉历史分支）下
确定"删什么、按什么顺序删、什么必须保留、用什么证据证明没删错"的交付任务。它仍有需要用户拍板的方向层
选择（能力迁移与否、删除边界、验收门禁），但不涉及全新产品形态，故按 `普通任务` 提问粒度执行，
同时把六类边界（完整用户流程/页面范围/数据状态/成功失败边界/非目标/延期）全部显式覆盖。

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 状态/处置 | 关联 OI |
| --- | --- | --- | --- | --- |
| R-001 | 检查母任务 PRD，确认 K1–K3 完成之后还剩哪张卡 | 用户原话 2026-09-16「我已经完成了K1、K2和K3的任务，请检查最后还有什么任务？」 | covered | 范围声明 |
| R-002 | 按标准 WorkflowHub 开始该任务，先创建 worktree，再从 make-decision 开始 | 用户原话「我希望现在按标准 WorkflowHub 开始这个任务，先创建worktree，然后从 make-decision 开始」 | covered | 阶段执行记录 step 1 |
| R-003 | 不跳阶段 | 用户原话「不要跳阶段」 | covered | 阶段执行记录 |
| R-004 | 不依赖 build-spec 补需求；先基于原始需求在 make-decision 内把需求梳理完整 | 用户原话「也不要依赖 build-spec 补需求。先基于原始需求，在make-decision的过程中和我一起仔细梳理…」 | covered | 六类边界在本阶段收敛 |
| R-005 | 在 make-decision 过程中共同梳理六类边界：完整用户流程、页面范围、数据状态、成功/失败边界、非目标、延期项 | 用户原话 | covered | OI 大纲 Fixed categories 六类全覆盖 |
| R-006 | 注意主会话上下文控制与子代理派发 | 用户原话 | covered | NG-006；`## 调研` |
| R-007 | Talk 与 grill 用大白话说明选项、后果和风险 | 用户原话 | covered | `## Talk` 卡片格式 |
| R-008 | 任务范围 = 母任务 PRD 的 K4 卡（瘦身且不丢能力）；K1/K2/K3 已完成提交 | 用户原话 + PRD §3 K4 | covered | OI-01…OI-14 |
| R-009 | K4 结果：整体源码行数净下降 + 不可达模块数归零 + 零引用配置量下降；S6 保留能力回归全绿；旧自证质量路径（投影/五维比较/证书/verifier）删除或不可达 | 母任务 PRD K4「结果」 | covered | OI-04, OI-05, OI-06, OI-07 |
| R-010 | K4 的 4 条 FR/AC：FR-K4-1 代码量净下降（基线冻结、复算脚本可复算）/ FR-K4-2 保留能力回归（S6 五项）/ FR-K4-3 旧自证路径移除 / FR-K4-4 删除顺序门禁（先验后删） | 母任务 PRD K4 表 | covered | OI-04, OI-06, OI-07, OI-08 |
| R-011 | K4 scope：历史分支/死代码删除、保留能力迁移、零引用配置清理、旧自证机器移除；不改编译语义（与 K1 协调）、不动发布通道（K3） | 母任务 PRD K4「scope」 | covered | OI-03, OI-04, NG-004 |
| R-012 | K4 用户流程与状态转换：冻结基线与复算脚本 → 效果/能力回归（通过才允许删除）→ 分批删除 → 复算核对 → 合并主干（K3 门禁） | 母任务 PRD K4「用户流程与状态转换」 | covered | OI-01, OI-04, OI-08 |
| R-013 | K4 依赖：准备依赖 = 冻结基线快照 + 复算脚本；实现依赖 = 无（独立，与 K1–K3 并行）；验收依赖 = 保留能力回归；合并依赖 = 合并主干时以 K3 查询集验收为门禁 | 母任务 PRD K4「依赖」 | covered | OI-04, OI-05, OI-09 |
| R-014 | 决策 D-005：在保留产品路径骨架的前提下做减法；删除范围以实现事实为准，不以文档承诺为准 | 母任务 decision-log D-005 | covered | OI-03, OI-04 |
| R-015 | 决策 T-004 = A：保留骨架、砍掉历史分支（含自证质量面与已结束任务的专用路径） | 母任务 decision-log T-004 / OI-09 | covered | OI-03, OI-06 |
| R-016 | 决策 T-008 = A：删掉自证机器（投影/五维比较/证书/verifier），改成固定一组真实问题 + 真实判定 | 母任务 decision-log T-008 / OI-11 | covered | OI-06, OI-07 |
| R-017 | 保留不变量 S6（瘦身时不得破坏）：300 行分页（`page_layout.py`）、分批与恢复（`batch_run.py`）、来源去重（`ingest/identity`）、失败不伪装成功、claim 级溯源 | 母任务 PRD S6 | covered | OI-05, NG-005 |
| R-018 | 可维护性度量口径：整体源码行数净下降 + 不可达模块数归零 + 零引用配置量下降；原口径"产品路径可达代码量"已废弃 | 母任务 decision-log 验收「成本与可维护性」 | covered | OI-04, OI-09 |
| R-019 | 删除前置条件：先冻结基线快照与复算脚本，先通过效果与核心能力回归；分页、分批恢复、去重、失败语义、溯源列为保留不变量；断言旧自证路径已删除或不可达 | 母任务 decision-log 验收「成本与可维护性」 | covered | OI-04, OI-05, OI-08 |
| R-020 | 事实基线（改造前审计）：产品路径仅 7 模块 / 11,441 行；src 55 模块 / 45,179 行，16 模块 / 14,951 行（33.1%）无入口可达；config 74 文件 / 17.56 MiB，44 文件 / 16.87 MiB 零命中；3 个 import 环 | 母任务 decision-log F-002 | covered（需按当前实现重算） | OI-02, OI-04 |
| R-021 | OPEN-004：300 行分页与分批恢复能力的迁移顺序（该能力目前只在旧路径实现） | 母任务 decision-log OPEN-004 | covered | OI-05 |
| R-022 | 非目标 NG-001…NG-010 与延期项 OI-15/OI-21 不得出现在本期实现 | 母任务 PRD §2、decision-log 非目标 | covered | NG-001…NG-010, DEF-K4-1…4 |
| R-023 | local risk：误删真能力 → 用 AC-K4-2/AC-K4-4 门禁压制 | 母任务 PRD K4「来源与设计引用」 | covered | OI-05, OI-08 |
| R-024 | 主会话上下文控制：大块材料不整卷吞入，取证派子代理，主会话只收结论与证据引用 | 用户原话；母任务 NG-002 | covered | NG-006；`## 调研` |
| R-025 | K1–K3 已完成提交：K4 的"净下降"必须与已被这些任务新增的代码共存，不得回退 K1–K3 已交付的行为 | 用户原话；仓库 git 历史（task7/task8/task9 已合并） | covered | OI-09, NG-004, RISK-003 |

### 用户原话（逐字，未改写）

> 「请检查"/Users/Hugh/Hugh/Project/KnowledgeDigest/specs/archive/task6-effect-gap-and-architecture-reset/prd.md"，我已经完成了K1、K2和K3的任务，请检查最后还有什么任务？
>
> 我希望现在按标准 WorkflowHub 开始这个任务，先创建worktree，然后从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。先基于原始需求，在make-decision的过程中和我一起仔细梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。注意主会话上下文控制和子代理派发。Talk 和grill请用大白话说明选项、后果和风险；」

## 核心需求

**在不动已交付能力的前提下，把 KnowledgeDigest 变回一个更小、只有一条主路径的代码库：源码净减少、没有到不了的模块、没有零引用的配置、旧的自证质量机器不再可执行；并且"没删错"由先冻结的基线复算脚本和保留能力回归证明，而不是由"文档说删了"证明。**

一句话拆开：① 先冻结基线（行数/可达性/零引用配置）与可复算脚本；② 先跑效果与保留能力回归，通过才允许删；
③ 分批删除历史分支、已结束任务专用路径与旧自证机器；④ 删后复算三项指标净下降；⑤ 旧自证路径断言不可达/已删除；
⑥ 不改 K1 编译语义、不动 K3 发布通道。

## 核心目标

| 目标 | 可观察的成功 | 依据 |
| --- | --- | --- |
| G1 净下降 | 同一复算脚本在冻结基线快照与当前树上各跑一次：整体源码行数净下降、不可达模块数归零、零引用配置量下降 | FR-K4-1；R-018 |
| G2 不丢能力 | S6 五项（300 行分页/分批恢复/来源去重/失败不伪装成功/claim 级溯源）回归全绿，且至少一项由真实生产路径（非仅旧离线路径）验证 | FR-K4-2；R-017 |
| G3 旧自证面不可执行 | 投影/五维比较/证书/verifier 删除或经断言不可达（给出具体命令与退出码） | FR-K4-3；R-016 |
| G4 先验后删 | 删除动作的流水线顺序可检查：基线冻结 → 效果/能力回归通过 → 才出现删除提交 | FR-K4-4；R-019 |
| G5 不回退 K1–K3 | K1 编译语义、K2 导航、K3 发布安全与真实查询集验收的行为不被本次删除改变 | R-025；NG-004 |

## 范围（triage-scope 初步）

- 交付物（本阶段）：本份 `decision-log.md`（方向、取舍、风险、非目标、延期、验收口径）与阶段事实。
- 交付物（后续阶段，本阶段只定边界）：实现层删除/迁移变更、冻结基线快照与复算脚本、保留能力回归证据、AC 追踪。
- 覆盖内容：三项可维护性指标的当前真值与冻结口径、删除候选清单的当前真值、S6 能力的当前归属与迁移决策、
  旧自证路径的当前可执行性、删除顺序与门禁、K1–K3 已交付行为的保护边界。
- 本阶段不写实现代码、不执行删除、不改产物、不重跑 provider。
- 当前不确定性（进 Talk/调研前如实登记）：
  1. "整体源码行数净下降"的基线身份——是相对本任务基线提交 `eee5549`，还是相对母任务规划时的 F-002 数字？K1–K3 已新增大量代码，两种口径的结论可能不同。
  2. "不可达模块数归零"的范围——是 `src/` 全量可达，还是仅"被判定删除的模块"离开可达图？
  3. 300 行分页与分批恢复当前是否仍在生产路径、还是只剩旧离线路径；迁移还是保留旧路径作为唯一边界。
  4. 旧自证路径中，哪些是 K3 正式验收仍需要的（删除范围必须排除）。
  5. "能力等价"的证明方式：回归测试全绿是否足够，还是需要真实运行证据。
  6. 净下降与"新代码落位"冲突时（例如为让模块可达而新增连接代码）的优先级。

## 需求框架（先选一类，再逐步回填）

- **framework**：`functional`（背景→问题→目标→方案→验收→扩展）
- **选择理由**：K4 是交付型任务（删/迁/验），不是纯调研裁决；背景与问题由 F-002 与 T-004 提供，方案与验收需要本轮与用户共同收敛。
- **回填规则**：调研、Talk、审查、Grill 只能扩展已有节点；混合任务以 `functional` 为外层，在受影响节点下挂 `research` 子树。

| node_id | 节点 | status | evidence_status | evidence_owner | next_review_trigger |
| --- | --- | --- | --- | --- | --- |
| N-background | 背景 | confirmed | complete | 母任务 F-002 + 本轮基线复算 | — |
| N-problem | 问题 | confirmed | complete | 本轮可达性/配置/自证面审计 | — |
| N-goal | 目标 | open | pending | 用户（Talk R2） | Talk R2 答复 |
| N-solution | 方案 | open | pending | 用户（Talk R2/R3）+ 本轮审计 | Talk R2/R3 答复 |
| N-acceptance | 验收 | open | pending | 用户（Talk R2）+ build-spec 细化 | Talk R2 答复 |
| N-extension | 扩展 | open | pending | 用户（Talk R3）+ Grill | Grill 结论 |

### 唯一 OI 大纲（current authority）

- `outline_version`：`v1.0`（step 2 建立，含调研前预置项；Talk 轮次只在本表回填）

#### Framework nodes

| node_id | framework_node | oi_ids | empty | reason |
| --- | --- | --- | --- | --- |
| N-background | background | OI-01, OI-02 | false | — |
| N-problem | problem | OI-03 | false | — |
| N-goal | goal | OI-04 | false | — |
| N-solution | solution | OI-05, OI-06, OI-07 | false | — |
| N-acceptance | acceptance | OI-08, OI-09 | false | — |
| N-extension | extension | OI-13, OI-14 | false | — |

#### Fixed categories

| category | oi_ids | empty | reason |
| --- | --- | --- | --- |
| complete_user_flow | OI-01, OI-02 | false | — |
| page_scope | OI-03 | false | 本任务非 UI/前端任务；"页面/产物范围"映射为"代码与配置面的删除边界"，仍需显式收敛 |
| data_state | OI-04, OI-10 | false | 「数据状态」映射为基线快照、复算输入与零引用配置清单的状态口径 |
| success_failure_boundary | OI-05, OI-06, OI-07, OI-08, OI-09 | false | — |
| non_goals | OI-11 | false | — |
| deferred | OI-12, OI-13, OI-14 | false | — |

#### OI records and consumers

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-01
category: complete_user_flow
source: R-002 / R-012 / fact-ref
question: "本任务（瘦身）的用户旅程是什么——维护者从哪一步开始、按什么顺序走到'可以合并主干'，中间失败时停在哪儿？"
status: open
impact_dimensions: [goal, scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-02
category: complete_user_flow
source: R-020 / fact-ref
question: "当前真实规模与可达性到底是多少（相对母任务规划时的 7 模块/11,441 行可达、33.1% 不可达、16.87 MiB 零引用配置），K1–K3 落地后变化如何？"
status: open
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-03
category: page_scope
source: R-011 / R-014 / R-015 / fact-ref
question: "本轮要删除的边界到底是什么：历史分支、已结束任务（Task1–Task5）专用路径、旧 S1–S6 管线、双 provider/双发布器，各自当前是否已不可达？"
status: open
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-04
category: data_state
source: R-009 / R-013 / R-018 / R-019
question: "三项可维护性指标（源码净下降/不可达归零/零引用配置下降）的基线怎么冻结、复算什么、以什么口径算净下降？"
status: open
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-05
category: success_failure_boundary
source: R-017 / R-021 / R-023
question: "S6 五项保留能力（300 行分页/分批恢复/去重/失败语义/claim 级溯源）当前在生产路径还是旧路径；需要迁移、保留旧路径，还是允许标记为'仅离线'？"
status: open
impact_dimensions: [scope, acceptance]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-06
category: success_failure_boundary
source: R-015 / R-016 / fact-ref
question: "旧自证质量路径（投影/五维比较/证书/verifier）当前哪些仍可执行、哪些已被 K1–K3 取代；'删除或不可达'采用哪种口径？"
status: open
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-07
category: success_failure_boundary
source: R-016 / R-025
question: "K3 的真实查询集验收是否仍依赖被列为删除候选的代码？删除范围如何与 K3 的验收入口共存？"
status: open
impact_dimensions: [scope, acceptance]
requires_user_decision: false
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-08
category: success_failure_boundary
source: R-010 / R-012 / R-019
question: "'先验后删'用什么证据成立：删除前的效果与能力回归指哪几条命令、什么结果算通过、失败时停在哪一步？"
status: open
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-09
category: success_failure_boundary
source: R-013 / R-018 / R-025
question: "净下降与'新代码落位/连接不可达模块'冲突时谁优先；K4 合并主干是否仍以 K3 查询集验收为门禁？"
status: open
impact_dimensions: [acceptance, scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-10
category: data_state
source: R-011 / R-020
question: "零引用配置与其他死资产的删除边界：哪些能仅凭引用证据删除，哪些必须先确认是运行输入（例如对照基线、fixture、映射表）？"
status: open
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-11
category: non_goals
source: R-022 / 母任务 NG-001…NG-010
question: "本任务明确不做什么（不得顺手扩张）？"
status: open
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-12
category: deferred
source: R-022 / 母任务 OI-15/OI-21
question: "本任务明确延期什么（含仍未关闭的 OPEN 项），owner 与触发条件是什么？"
status: open
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-13
category: deferred
source: R-014 / R-015
question: "删除完成后，KD 是否接替旧 synthesize_* 主题与自动化登记（母任务 S7 移交项）；本期只做代码瘦身还是要碰这条移交线？"
status: open
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R3
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.0
oi_id: OI-14
category: deferred
source: R-022 / 母任务 OPEN-004/OPEN-005/OPEN-007
question: "母任务遗留的未决项（能力迁移顺序、LangExtract 采用、Pandoc GPL、流水线修复）在本期如何处置？"
status: open
impact_dimensions: [scope]
requires_user_decision: false
```

## 非目标（step 2 初步草案，待 Talk/Grill 收敛）

- NG-001 不新增功能、不做问答/RAG、不做前端或可浏览界面。
- NG-002 不引入向量库、图数据库、服务化部署或后台守护。
- NG-003 不做多格式输入（PDF/Word/网页）。
- NG-004 不改 K1 编译语义与产物形态、不动 K3 发布通道与验收入口（保护已交付行为）。
- NG-005 不删除 S6 五项保留能力（除非先迁移并证明等价）。
- NG-006 不修改既有 CompanyBrain 正式页、不修停摆的每日自动化流水线。
- NG-007 本阶段不改代码、不执行删除、不重跑 provider。
- NG-008 不为了凑"净下降"而删除仍被生产路径使用的代码或配置。
- NG-009 不把"文档承诺"当作删除依据；删除范围以实现事实为准（D-005）。
- NG-010 不做与瘦身无关的重构/改名/格式化风暴。

## 风险（step 2 初步草案）

| risk_id | 风险 | 触发/后果 | 当前处置 |
| --- | --- | --- | --- |
| RISK-001 | 删错真能力（S6 或 K1–K3 已交付行为） | 删除后生产路径无法跑通或静默降级 | OI-05/OI-08；先验后删门禁 |
| RISK-002 | 基线身份不清导致"净下降"不可复算或可被绕过 | 指标变成口头结论 | OI-04；冻结基线 + 复算脚本 |
| RISK-003 | K1–K3 新增代码使"净下降"相对旧基线不成立 | 任务目标无法达成或被解释成"未完成" | OI-04；Talk R2 确认基线口径 |
| RISK-004 | 旧自证路径被 K3 验收部分引用，删除后验收不可复跑 | 破坏已完成任务的验收能力 | OI-07；删除范围排除 K3 依赖 |
| RISK-005 | 零引用配置实际是运行输入（对照基线/fixture/映射） | 删后真实运行失败或对照结论失效 | OI-10；引用证据 + 运行输入确认 |
| RISK-006 | 为让模块可达而新增连接代码，抵消净下降 | 指标互相冲突 | OI-09；优先级由用户拍板 |
| RISK-007 | 删除动作先于回归验证 | FR-K4-4 判失败 | OI-08；顺序门禁 |

## 阶段执行记录

| step | step_slug | 状态 | 真实结果 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | load-context | completed | 读取原始需求、母任务 PRD（确认 K1–K3 已完成、K4 为唯一剩余卡）、WorkflowHub make-decision workflow 与 skill-deps；用 `task-bootstrap.mjs` 创建确定性 worktree 与分支并读回；建立本文件、任务身份与唯一 OI 大纲（14 项，outline v1.0） | `decision-log.md` 任务身份 / OI 大纲；`git worktree list` |
| 2 | triage-scope | completed | 写入初步范围、6 项不确定性、10 条非目标草案、7 条风险草案；登记任务类型 `普通任务` | `decision-log.md` 范围 / 非目标 / 风险 |
| 3 | talk-round-1 | pending | — | — |
| 4 | research-inputs | pending | — | — |
| 5 | talk-round-2 | pending | — | — |
| 6 | direction-advice | pending | — | — |
| 7 | talk-round-3 | pending | — | — |
| 8 | grill-with-docs | pending | — | — |
| 9 | write-decision-draft | pending | — | — |
| 10 | detail-advice | pending | — | — |
| 11 | approve-decision | pending | — | — |
| 12 | stage-end-spec-analyze | pending | — | — |
| 13 | publish-decision | pending | — | — |
| 14 | stage-reflection | pending | — | — |
