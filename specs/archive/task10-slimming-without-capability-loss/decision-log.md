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

**范围声明（Talk Round 2 用户已确认，2026-09-16）**：本任务范围 = 母任务 PRD
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
| R-014 | 决策 母-D-005：在保留产品路径骨架的前提下做减法；删除范围以实现事实为准，不以文档承诺为准 | 母任务 decision-log D-005 | covered | OI-03, OI-04 |
| R-015 | 决策 T-004 = A：保留骨架、砍掉历史分支（含自证质量面与已结束任务的专用路径） | 母任务 decision-log T-004 / OI-09 | covered | OI-03, OI-06 |
| R-016 | 决策 T-008 = A：删掉自证机器（投影/五维比较/证书/verifier），改成固定一组真实问题 + 真实判定 | 母任务 decision-log T-008 / OI-11 | covered | OI-06, OI-07 |
| R-017 | 保留不变量 S6（瘦身时不得破坏）：300 行分页（`page_layout.py`）、分批与恢复（`batch_run.py`）、来源去重（`ingest/identity`）、失败不伪装成功、claim 级溯源 | 母任务 PRD S6 | covered | OI-05, NG-005 |
| R-018 | 可维护性度量口径：整体源码行数净下降 + 不可达模块数归零 + 零引用配置量下降；原口径"产品路径可达代码量"已废弃 | 母任务 decision-log 验收「成本与可维护性」 | covered | OI-04, OI-09 |
| R-019 | 删除前置条件：先冻结基线快照与复算脚本，先通过效果与核心能力回归；分页、分批恢复、去重、失败语义、溯源列为保留不变量；断言旧自证路径已删除或不可达 | 母任务 decision-log 验收「成本与可维护性」 | covered | OI-04, OI-05, OI-08 |
| R-020 | 事实基线（改造前审计）：产品路径仅 7 模块 / 11,441 行；src 55 模块 / 45,179 行，16 模块 / 14,951 行（33.1%）无入口可达；config 74 文件 / 17.56 MiB，44 文件 / 16.87 MiB 零命中；3 个 import 环 | 母任务 decision-log F-002 | covered（需按当前实现重算） | OI-02, OI-04 |
| R-021 | OPEN-004：300 行分页与分批恢复能力的迁移顺序（该能力目前只在旧路径实现） | 母任务 decision-log OPEN-004 | covered | OI-05 |
| R-022 | 非目标 NG-001…NG-010 与延期项 OI-15/OI-21 不得出现在本期实现 | 母任务 PRD §2、decision-log 非目标 | covered | NG-001…NG-013, DEF-K4-1…9 |
| R-023 | local risk：误删真能力 → 用 AC-K4-2/AC-K4-4 门禁压制 | 母任务 PRD K4「来源与设计引用」 | covered | OI-05, OI-08 |
| R-024 | 主会话上下文控制：大块材料不整卷吞入，取证派子代理，主会话只收结论与证据引用 | 用户原话；母任务 NG-002 | covered | NG-006；`## 调研` |
| R-025 | K1–K3 已完成提交：K4 的"净下降"必须与已被这些任务新增的代码共存，不得回退 K1–K3 已交付的行为 | 用户原话；仓库 git 历史（task7/task8/task9 已合并） | covered | OI-09, NG-004, RISK-003 |

### 用户原话（逐字，未改写）

> 「请检查"/Users/Hugh/Hugh/Project/KnowledgeDigest/specs/archive/task6-effect-gap-and-architecture-reset/prd.md"，我已经完成了K1、K2和K3的任务，请检查最后还有什么任务？
>
> 我希望现在按标准 WorkflowHub 开始这个任务，先创建worktree，然后从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。先基于原始需求，在make-decision的过程中和我一起仔细梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。注意主会话上下文控制和子代理派发。Talk 和grill请用大白话说明选项、后果和风险；」

## 核心需求

**在不动已交付能力的前提下，把 KnowledgeDigest 变回一个更小、只有一条主路径的代码库：源码净减少、没有到不了的模块、证据充分的零引用配置被清除、旧的自证质量机器不再可执行；并且"没删错"由先冻结的基线复算脚本和保留能力回归证明，而不是由"文档说删了"证明。**

一句话拆开：① 先冻结基线（行数/可达性/零引用配置）与可复算脚本；② 先跑效果与保留能力回归，通过才允许删；
③ 分批删除历史分支、已结束任务专用路径与旧自证机器；④ 删后复算三项指标净下降；⑤ 旧自证路径断言不可达/已删除；
⑥ 不改 K1 编译语义、不动 K3 发布通道。

## 核心目标

| 目标 | 可观察的成功 | 依据 |
| --- | --- | --- |
| G1 净下降 | 同一复算脚本在冻结基线快照与当前树上各跑一次：整体源码行数净下降、不可达模块数归零、零引用配置量下降（目标是「证据充分的 21 项被清除且总量下降」，不是「全仓零引用归零」；保留项见 DEF-K4-3/4） | FR-K4-1；R-018 |
| G2 不丢能力 | S6 五项（300 行分页/分批恢复/来源去重/失败不伪装成功/claim 级溯源）回归全绿，且至少一项由真实生产路径（非仅旧离线路径）验证 | FR-K4-2；R-017 |
| G3 旧自证面不可执行 | 投影/五维比较/证书/verifier 删除或经断言不可达（给出具体命令与退出码） | FR-K4-3；R-016 |
| G4 先验后删 | 删除动作的流水线顺序可检查：基线冻结 → 效果/能力回归通过 → 才出现删除提交 | FR-K4-4；R-019 |
| G5 不回退 K1–K3 | K1 编译语义、K2 导航、K3 发布安全与真实查询集验收的行为不被本次删除改变 | R-025；NG-004 |

## 范围

> 本节口径由 Talk Round 2 用户确认（2026-09-16）。

- 交付物：① 冻结基线快照与可复算脚本（三项指标）；② 分批删除变更（旧 S1–S6 残骸、旧自证簇、旧自证脚本、21 个零引用配置）；
  ③ 最小断点续跑修复（OI-15）；④ 保留能力回归证据与 AC 追踪；⑤ 本任务四份材料。
- 覆盖内容：`src/` 代码删除与必要的最小新增（断点续跑 + 活实现缺测试补测）、`config/` 21 文件删除、
  旧自证脚本删除、S6 能力承接、三项指标复算。
- **不覆盖**：文档与 `specs/archive`、`apply/`、13.77 MiB mapping 修订版、9 个 archive-only 配置、
  停摆流水线、`synthesize_*` 接管登记、K1 编译语义、K3 发布通道与验收入口。
- 本阶段（make-decision）不写实现代码、不执行删除、不改产物、不重跑 provider。
- 已确认的关键取舍：净下降优先于"为凑可达保活死代码"；删除必须分批且每批可回退；
  "没删错"由回归测试全绿 ＋ 一次真实 `digest` 路径证明。

## 需求框架（先选一类，再逐步回填）

- **framework**：`functional`（背景→问题→目标→方案→验收→扩展）
- **选择理由**：K4 是交付型任务（删/迁/验），不是纯调研裁决；背景与问题由 F-002 与 T-004 提供，方案与验收需要本轮与用户共同收敛。
- **回填规则**：调研、Talk、审查、Grill 只能扩展已有节点；混合任务以 `functional` 为外层，在受影响节点下挂 `research` 子树。

| node_id | 节点 | status | evidence_status | evidence_owner | next_review_trigger |
| --- | --- | --- | --- | --- | --- |
| N-background | 背景 | confirmed | complete | 母任务 F-002 + 本轮基线复算 | — |
| N-problem | 问题 | confirmed | complete | 本轮可达性/配置/自证面审计 | — |
| N-goal | 目标 | confirmed | complete | 用户 T2-01/T2-03/T2-04 | — |
| N-solution | 方案 | confirmed | complete | 用户 T2-02/T2-05/T2-06/T2-10/T2-16 + 本轮审计 | — |
| N-acceptance | 验收 | confirmed | complete | 用户 T2-08/T2-09/T2-15 | 细化交 build-spec |
| N-extension | 扩展 | confirmed | complete | 用户 T2-13 + DEF-K4-1…9 | — |

### 唯一 OI 大纲（current authority）

- `outline_version`：`v1.1`（step 2 建立 v1.0；step 4 调研后新增 OI-15/OI-16；step 5 全部回填终态，OI 身份未再变化）

#### Framework nodes

| node_id | framework_node | oi_ids | empty | reason |
| --- | --- | --- | --- | --- |
| N-background | background | OI-01, OI-02 | false | — |
| N-problem | problem | OI-03 | false | — |
| N-goal | goal | OI-04 | false | — |
| N-solution | solution | OI-05, OI-06, OI-07, OI-16 | false | — |
| N-acceptance | acceptance | OI-08, OI-09, OI-15 | false | — |
| N-extension | extension | OI-13, OI-14 | false | — |

#### Fixed categories

| category | oi_ids | empty | reason |
| --- | --- | --- | --- |
| complete_user_flow | OI-01, OI-02 | false | — |
| page_scope | OI-03 | false | 本任务非 UI/前端任务；"页面/产物范围"映射为"代码与配置面的删除边界"，仍需显式收敛 |
| data_state | OI-04, OI-10, OI-16 | false | 「数据状态」映射为基线快照、复算输入、零引用配置清单与旧自证簇的状态口径 |
| success_failure_boundary | OI-05, OI-06, OI-07, OI-08, OI-09, OI-15 | false | — |
| non_goals | OI-11 | false | — |
| deferred | OI-12, OI-13, OI-14 | false | — |

#### OI records and consumers（outline v1.1 · 全部终态已回填）

标记说明：`requires_user_decision: true` 且带 `visible_group_id` 的项已由用户 2026-09-16 真实答复确认；`false` 的项由本轮事实回答（`answered_by_fact`）。确认凭证由 interaction aggregate 单向绑定，不写入本记录。

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-01
category: complete_user_flow
source: "R-002 / R-012 / fact-ref"
question: "本任务（瘦身）的用户旅程是什么：维护者从哪一步开始、按什么顺序走到\"可以合并主干\"，中间失败时停在哪儿？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-01 = A：冻结基线与复算脚本 → 先做能力回收与存活能力回归（通过才允许删）→ 分批删除（每批删完立即跑聚焦验证，红则回退该批）→ 复算三项指标 → 以 K3 验收为门禁合并。"
evidence: "本文件 `## 完整用户旅程` J1–J5；Talk T2-01"
acceptance: "任一步失败即停在该步并保留现场；删除批次失败必须回退该批"
counterexample: "若删除在回归通过之前发生即判该旅程失效"
impact_dimensions: [goal, scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-02
category: complete_user_flow
source: "R-020 / fact-ref"
question: "当前真实规模与可达性是多少，K1–K3 落地后相对母任务规划时变化如何？"
status: confirmed
selected_disposition: "answered_by_fact：src 67 模块/56,382 行；digest 可达 19 模块/11,618 行；39 模块/39,161 行（69.5%）从所有正式入口不可达；config 76 文件/17.57 MiB，其中证据充分可删 21 项/3.19 MiB。"
evidence: "evidence/reachability-audit.md；evidence/config-audit.md"
acceptance: "同一 AST 复算脚本可重跑并得到同一清单"
counterexample: "若复算得到不同可达性即判该事实不成立"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-03
category: page_scope
source: "R-011 / R-014 / R-015 / fact-ref"
question: "本轮要删除的边界到底是什么：历史分支、已结束任务专用路径、旧 S1–S6 管线、双 provider/双发布器？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-02 = A：只动代码与 config/；删除对象＝39 个不可达模块（含旧 S1–S6 与旧自证簇）＋旧自证脚本＋21 个零引用配置；不为凑可达保活死代码。"
evidence: "本文件 `## 删除与保留清单` A/B/C/D/E 节；evidence/legacy-selfproof-audit.md"
acceptance: "B 节 67/67 逐模块清单中每个模块恰有一个处置，且批次互斥"
counterexample: "若某模块同时出现在删除与保留清单，或删除后 5 条正式命令任一条不可用，即判该边界不成立"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-04
category: data_state
source: "R-009 / R-013 / R-018 / R-019"
question: "三项可维护性指标的基线怎么冻结、复算什么、以什么口径算净下降？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-03/T2-04 = A：基线＝起始提交 eee5549；净下降＝同一脚本两次复算；不可达口径＝pyproject 5 条正式命令（D-005 后不再含 legacy 脚本）。"
evidence: "本文件 `## 验收指标冻结`；Talk T2-03/T2-04"
acceptance: "同一复算脚本两次输出并列对比，三项均净下降"
counterexample: "若任一指标上升持平、或基线不可复算，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-05
category: success_failure_boundary
source: "R-017 / R-021 / R-023"
question: "S6 五项保留能力当前在生产路径还是旧路径，需要迁移、保留旧路径，还是标记为仅离线？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-05 = A：四项已有活的等价实现（分页/去重/失败语义/claim 级溯源），旧模块按残骸删除；活实现缺断言的那项补测试；分批恢复单列 OI-15。"
evidence: "evidence/retained-invariants-audit.md"
acceptance: "FR-K4-2a 逐项绑定的测试节点全绿，且至少一次真实 digest 路径跑通"
counterexample: "若某项只在旧路径测试中为绿，即判该项未保留"
impact_dimensions: [scope, acceptance]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-06
category: success_failure_boundary
source: "R-015 / R-016 / fact-ref"
question: "旧自证质量路径当前哪些仍可执行、哪些已被 K1–K3 取代；删除或不可达采用哪种口径？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-06 = A：整体删除（compiler.py 整模块、evaluate_reader_candidate.py、m401_r_adapter、task4_reader_quality 及其测试），质量口径统一到 K3 的 kb_accept。"
evidence: "evidence/legacy-selfproof-audit.md；Talk T2-06"
acceptance: "FR-K4-3 给出具体命令与退出码，旧自证入口不可执行"
counterexample: "若删除后 kb_accept/kb_publish 任一测试变红，即判误删活能力"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-07
category: success_failure_boundary
source: "R-016 / R-025"
question: "K3 的真实查询集验收是否仍依赖被列为删除候选的代码？"
status: confirmed
selected_disposition: "answered_by_fact：kb_accept 只 import errors + kb_publish，不依赖任何 legacy 自证代码；唯一残留是 config/task9-comparison-mapping.v1.json 里的 origin_mapping_path provenance 字符串（非运行时读取）。"
evidence: "evidence/legacy-selfproof-audit.md"
acceptance: "kb_accept 的 import 闭包不包含删除清单中的模块"
counterexample: "若 kb_accept 运行需要删除清单中的模块，即判该结论不成立"
impact_dimensions: [scope, acceptance]
requires_user_decision: false
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-08
category: success_failure_boundary
source: "R-010 / R-012 / R-019"
question: "先验后删用什么证据成立：删除前的效果与能力回归指哪几条命令、什么结果算通过、失败时停在哪一步？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-08 = A：存活能力回归测试全绿＋至少一次真实 digest 跑通；失败停在该批并回退，不继续删。"
evidence: "本文件 FR-K4-2a/2b/2c/2d；Talk T2-08"
acceptance: "删除批次之前存在基线冻结与回归通过记录，且顺序可检查"
counterexample: "若先出现删除提交再出现验证记录，即判违反先验后删"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-09
category: success_failure_boundary
source: "R-013 / R-018 / R-025"
question: "净下降与\"新代码落位/连接不可达模块\"冲突时谁优先；合并主干是否仍以 K3 验收为门禁？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-09 = A：净下降优先，不为凑可达新增连接代码；合并主干仍以 K3 查询集验收为门禁。"
evidence: "Talk T2-09；本文件 FR-K4-1 与 `## 验收指标冻结`"
acceptance: "复算脚本中不可达清单为空，且未新增连接代码（净下降成立）"
counterexample: "若为凑可达新增模块或连接代码使净下降不成立，即判失败"
impact_dimensions: [acceptance, scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-10
category: data_state
source: "R-011 / R-020"
question: "零引用配置与其他死资产的删除边界：哪些能仅凭引用证据删除，哪些必须先确认是运行输入？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-10 = A：只删证据充分的 21 项/3,341,698 B；9 项 archive-only 延期（DEF-K4-3）；13.77 MiB mapping 修订版保留为 K3 provenance（DEF-K4-4）；apply/ 本期不动。"
evidence: "evidence/config-audit.md §8a/§3；本文件 `#### config/ 全量 76 文件处置表`"
acceptance: "删除/延期/保留三类互斥且合计 76；删除项的 sha256 双口径复核为零引用"
counterexample: "若某删除项实际被活代码或运行输入读取，即判该边界不成立"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-11
category: non_goals
source: "R-022 / 母任务 NG-001…NG-010"
question: "本任务明确不做什么（不得顺手扩张）？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认：NG-001…NG-013 全部生效（含 NG-011 不为凑指标保活死代码、NG-012 不清理文档、NG-013 不搬运母任务完整范围）。"
evidence: "本文件 `## 非目标`"
acceptance: "最终 diff 只包含删除、断点续跑与其测试、配置删除四类改动"
counterexample: "若出现前端/向量库/多格式输入/流水线修改等改动，即判违反非目标"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-12
category: deferred
source: "R-022 / 母任务 OI-15/OI-21"
question: "本任务明确延期什么（含仍未关闭的 OPEN 项），owner 与触发条件是什么？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认：DEF-K4-1…9 全部登记（文档瘦身、停摆流水线、archive-only 配置、mapping 与 apply/、synthesize 接管、删除前重读、完整分批策略、基线红灯 fixture、anysearch key 旁路请求）。"
evidence: "本文件 `## 延期与开放项`（编号唯一权威）"
acceptance: "每项都有 owner 与触发条件，且在 build-plan 中被消费"
counterexample: "若某项无 owner 或触发条件，即判延期登记不完整"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-13
category: deferred
source: "R-014 / R-015"
question: "删除完成后，KD 是否接替旧 synthesize_* 主题与自动化登记（母任务 S7 移交项）？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-13 = A：不碰，只保持\"KD 只写自己声明的路径\"边界，接管照旧延期。"
evidence: "Talk T2-13；本文件 DEF-K4-5"
acceptance: "本期不出现对既有自动化或 CompanyBrain 正式页的写入"
counterexample: "若本期修改既有流水线或正式页，即判违反"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R3
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-14
category: deferred
source: "R-022 / 母任务 OPEN-004/OPEN-005/OPEN-007"
question: "母任务遗留的未决项在本期如何处置？"
status: confirmed
selected_disposition: "answered_by_fact＋用户确认：OPEN-004 由 OI-15 承接（不再需要迁移分页）；OPEN-005 LangExtract 仍不采用；OPEN-007 Pandoc 未触发；流水线修复＝DEF-K4-2。"
evidence: "本文件 `## 延期与开放项`；母任务 OPEN 清单"
acceptance: "每个母任务 OPEN 项在本文件有承接位置或延期条目"
counterexample: "若某个 OPEN 项既无承接也无延期，即判遗漏"
impact_dimensions: [scope]
requires_user_decision: false
visible_group_id: R3
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-15
category: success_failure_boundary
source: "R-017 / R-021 / 本轮调研"
question: "S6 的分批与恢复已在 K1–K3 期间从生产路径消失：本期补回生产入口、恢复旧入口，还是显式降级登记并延期？"
status: confirmed
selected_disposition: "用户 2026-09-16 确认 T2-15 = A：本期只做最小断点续跑（重跑同一批次不重复 provider 调用）＋一条钉住测试；完整分批策略延期（DEF-K4-7）。"
evidence: "evidence/retained-invariants-audit.md INV2；Talk T2-15"
acceptance: "重跑同批次的第二次运行 provider 调用数为 0，且有测试钉住"
counterexample: "若重跑仍重复计费或无测试覆盖，即判该项未交付"
impact_dimensions: [scope, acceptance]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task10-slimming-without-capability-loss
outline_version: v1.1
oi_id: OI-16
category: data_state
source: "本轮调研（legacy-selfproof-audit）"
question: "旧自证簇与它依赖的 legacy 入口怎么处置？"
status: confirmed
selected_disposition: "用户 2026-09-16 先确认 T2-16 = A（保留 legacy 入口），经 detail 复核指出与\"不可达归零\"冲突后，就 D-005 明确改选：连 legacy 入口一起退役删除，可达性根收窄为 pyproject 5 条正式命令；其余旧自证脚本与模块整体删除。"
evidence: "本文件 D-005；Talk Round 4；quality/reviews/results（detail 第 2 轮 blocking）"
acceptance: "最终树不存在 scripts/legacy_digest_reference.py，且不可达清单为空"
counterexample: "若保留该脚本又声称不可达归零，即判该处置不成立"
impact_dimensions: [scope, acceptance]
requires_user_decision: true
visible_group_id: R3
```

## 调研（step 4，结论层）

四份审计报告（子代理执行，主会话只收结论与证据引用）：

| 报告 | 覆盖问题 | 关键结论 |
| --- | --- | --- |
| `evidence/reachability-audit.md` | 规模、入口、可达性、环、超大函数 | `src/` 67 模块 / 56,382 行；`digest` 可达 19 模块 / 11,618 行；**39 模块 / 39,161 行（69.5%）从所有正式入口都到不了**（规划时 33.1%）；3 个环全由函数内惰性 import 形成 |
| `evidence/config-audit.md` | 零引用配置、重复字节、运行输入 | 76 文件 / 17.57 MiB；指定范围零引用 50 文件 / 16.70 MiB；**证据充分可删 21 文件 / 3.19 MiB**；需人拍板 9 文件；13.77 MiB 属"引用存在但是判断问题"；`digest` 运行只读 2 个仓库内配置 |
| `evidence/legacy-selfproof-audit.md` | 投影/五维/证书/verifier 现状 | 仍有 4 条旧命令可执行（`legacy_digest_reference.py`、`evaluate_reader_candidate.py`、`task5_m401_r_adapter.py`、`task4_reader_quality.py`）；`digest` 运行闭包 0 个 legacy；自证簇 ≈24,021 行；K3 的 `kb_accept` 不依赖 legacy |
| `evidence/retained-invariants-audit.md` | S6 五项能力现状 | 4/5 项已有活的等价实现（旧模块是同名残骸）；**『分批 + 恢复』已破且不可达**；来源去重有 3 份实现、活的那份零测试 |
| `evidence/k4-research-summary.md` | 主会话汇总（含独立复核） | 汇总口径冲突、删除体积分布、`config/knowledge-digest.json` 与 legacy 入口同命 |

主会话独立复核（不依赖子代理结论）：`simple_cli.main()` 确实硬拒绝 `--no-llm/--config/--quality-config/--gate` 等历史参数并 exit 2；
`semantic_cli` 只 import `semantic_compiler` 与 `semantic_navigation`；`page_layout`/`batch_run` 的调用者只有 `pipeline.py`、`cli.py` 与 `task4_location_pilot.py`，
而这三个都不在任何正式入口闭包内。与子代理结论一致。

**顺带发现的既有红灯（不是本任务引入）**：`tests/acceptance/test_task2a_reader_bundle.py::test_validator_rejects_incomplete_claim_provenance`
依赖外部冻结 fixture，当前缺失而失败（15 failed / 19 passed）。本任务只登记，不假装修好、也不当成本任务验收前提。

## 非目标

> 本节口径由用户确认（2026-09-16）。

- NG-001 不新增功能、不做问答/RAG、不做前端或可浏览界面。
- NG-002 不引入向量库、图数据库、服务化部署或后台守护。
- NG-003 不做多格式输入（PDF/Word/网页）。
- NG-004 不改 K1 编译语义与产物形态、不动 K3 发布通道与验收入口（保护已交付行为）。
- NG-005a 不因**本期删除动作**而丢失能力：任何删除都不得移除当前生产路径仍在用的行为。
- NG-005b 对**已经丢失**的「分批+恢复」必须显式拍板（补回生产入口／恢复旧入口／显式降级并延期），不得默认它仍然存在；
  本期取"最小断点续跑"（见 D-002）。
- NG-005c 先验后删门禁只对"生产路径仍然存活的能力"生效；对已丢失能力以显式延期＋验收口径声明处置，不制造无法通过的死锁门禁。
- NG-006 不修改既有 CompanyBrain 正式页、不修停摆的每日自动化流水线。
- NG-007 本阶段不改代码、不执行删除、不重跑 provider。
- NG-008 不为了凑"净下降"而删除仍被生产路径使用的代码或配置。
- NG-009 不把"文档承诺"当作删除依据；删除范围以实现事实为准（母任务 母-D-005）。
- NG-010 不做与瘦身无关的重构/改名/格式化风暴。
- NG-011 不为凑"不可达归零"而新增连接代码保活死代码（用户 T2-04）。
- NG-012 不清理文档、`specs/archive`、`apply/`（用户 T2-02/T2-10；文档瘦身见 DEF-K4-1）。
- NG-013 不把母任务（task6）的完整范围搬进本期；本期只是其中 K4 一张卡，其余原始诉求按 `## 与母任务的关系` 逐条登记。

## 风险与延期交接

> 本节口径由用户确认（2026-09-16）；延期明细见 `## 延期与开放项`（DEF-K4-1…9 为该表唯一编号权威）。

| risk_id | 风险 | 触发/后果 | 处置 |
| --- | --- | --- | --- |
| RISK-001 | 删错真能力（S6 或 K1–K3 已交付行为） | 生产路径无法跑通或静默降级 | 先验后删（FR-K4-4）＋ 每批聚焦验证＋真实 `digest` 跑通（T2-08） |
| RISK-002 | 基线身份不清导致"净下降"不可复算 | 指标变成口头结论 | 基线固定为 `eee5549`，复算脚本随材料交付（T2-03） |
| RISK-003 | 源文件解析按模块整体删会带走被 K1/K3 复用的符号 | 已核实：`compiler.py` 无 K1/K3 复用符号（`kb_accept` 只依赖 `errors`+`kb_publish`）；风险降级为"批量删除时误删活模块" | 删除前按 B 节 67/67 清单逐模块重读（DEF-K4-6） |
| RISK-004 | 删除旧自证后无法回放历史 M401/M402 证据 | 历史结论不可复跑 | **用户已接受**（T2-06 = A，与母任务 T-008 一致） |
| RISK-005 | 零引用配置实际是运行输入 | 删后真实运行失败或对照结论失效 | 只删证据充分的 21 文件；13.77 MiB 保留（T2-10） |
| RISK-006 | 活实现缺测试（去重零断言）→ 删除后回归发现不了 | 静默改变 canonical 来源 | 本期给活实现补一条钉住断言的测试（FR-K4-2） |
| RISK-007 | 断点续跑的最小修复改变了 K1 既有行为 | 编译结果漂移 | 只做"重跑同批次不重复 provider 调用"，不改编译产物；补测试钉住 |
| RISK-008 | 既有红灯被误算成本任务失败 | `test_task2a_reader_bundle` 缺外部 fixture 已红 | 在 `## 调研` 显式登记为既有事实，不作为本任务验收前提 |
| RISK-009 | 任务名"不丢能力"与"分批+恢复已丢失"冲突 | 交付时一项 S6 能力本就不在生产路径 | NG-005b + D-002：本期最小断点续跑，其余显式延期（DEF-K4-7），验收口径不声称已完整保留完整分批策略 |
| RISK-010 | 批量删除旧自证测试后，活实现失去测试兜底 | 静默回归无人发现 | FR-K4-2 要求给活实现补钉住测试；G2 追加测试数指标与差异说明 |
| RISK-011 | 复算脚本可被"删注释/删空行"刷分 | 指标失真 | G2-A：同时报告代码行与物理行，并报告模块/函数/测试数 |
| RISK-012 | 退役 `scripts/legacy_digest_reference.py` 后，旧 reader/offline 行为不再可用 | 用户若仍需旧行为则无入口 | D-005；如需恢复另开任务（DEF-K4-1 同步文档） |

## 完整用户旅程（维护者视角，用户已确认）

角色：**维护者**（下一位改 KnowledgeDigest 的人）、**读者/下游**（K1–K3 产物的使用者，本任务是保护他们的能力不被误删）。

| # | 阶段 | 谁做 | 发生什么 | 成功的样子 | 失败/中断的样子 |
| --- | --- | --- | --- | --- | --- |
| J1 | 冻结基线 | 维护者 | 在起始提交上跑复算脚本，落盘模块数/行数/可达性/零引用配置清单 | 三份基线数字可复算、随材料交付 | 基线不可复算 → 停在 J1，不许开始删除 |
| J2 | 先验证 | 维护者 | 先做断点续跑与补测试，再跑存活能力回归 ＋ 一次真实 `digest` 路径 | 全绿且真实路径跑通 | 任一红 → 先修或如实记录，不进入删除 |
| J3 | 分批删除（前置：J2 已通过） | 维护者 | 按批删旧 S1–S6 残骸 / 旧自证簇 / 旧脚本 / 21 个配置 | 每批聚焦验证绿、批次可回退 | 某批变红 → 回退该批并停在该批，保留现场 |
| J4 | 复算核对 | 维护者 | 用 J1 同一脚本复算三项指标 | 源码净下降、不可达归零（按 T2-04 口径）、零引用配置下降 | 任一项未达标 → 如实记录差额，不粉饰 |
| J5 | 合并主干 | 用户/维护者 | 以 K3 查询集验收为门禁合并 | 门禁通过后才合并 | 门禁不可复跑 → 记录真实 `unavailable`，不伪造通过 |

**关键不变量**：不丢已交付能力；删除可回退且先验后删；指标可复算；失败不伪装成功。

## 已选方向

用户 2026-09-16 在 Talk Round 2 全部确认（原话见下）。一句话：
**K4 = 在冻结基线与先验后删门禁下，删除旧 S1–S6 残骸、旧自证质量簇与证据充分的零引用配置，用活实现承接 S6 能力，并补上唯一真丢的"断点续跑"；不动文档、不动 K1/K3 语义。**

- T2-01 = A 完整用户流程（J1→J5）
- T2-02 = A 只动代码与 `config/`，不为凑可达保活死代码
- T2-03 = A 基线＝`eee5549`，净下降＝同脚本两次复算
- T2-04 = A 不可达口径＝`pyproject` 5 条正式命令
- T2-05 = A S6 能力由活实现承接，旧模块按残骸删除
- T2-06 = A 旧自证簇整体删除，质量口径统一到 `kb_accept`
- T2-08 = A 先验后删证据＝回归全绿＋真实 `digest` 跑通
- T2-09 = A 净下降优先于凑可达；合并仍以 K3 验收为门禁
- T2-10 = A 只删证据充分的 21 文件/3.19 MiB，其余保留或延期
- T2-13 = A 不碰 `synthesize_*` 接管登记
- T2-15 = A 分批恢复只做最小断点续跑
- T2-16 = A → D-005 收窄：legacy 入口随旧管线一并退役删除（用户 2026-09-16 明确确认）

## 验收标准

| FR | AC（含失败判据） | oracle |
| --- | --- | --- |
| FR-K4-1 三项指标净下降 | 同一复算脚本在基线 `eee5549` 与最终树上各跑一次：整体源码行数净下降；不可达模块归零（pyproject 五条正式命令；legacy 入口已按 D-005 退役）；零引用配置量下降。**失败**：任一指标上升、持平或基线不可复算。 | 复算脚本两次输出对比 |
| FR-K4-2a 存活能力回归（删除前门禁） | 删除动作开始前，**当前生产路径仍然存活**的 S6 能力必须全绿，逐项绑定到具体测试节点：① 300 行分页＝`test_task7_pages.py` 全文件＋`test_task7_e2e.py` 的分页/多卷用例；② 来源去重＝**本期新增**的钉住测试（重复来源 fixture，断言输出页面与 audit ledger 双侧）；③ 失败不伪装成功＝`test_task7_e2e.py`／`test_task8_*` 的 blocked/interrupted 用例；④ claim 级溯源＝`test_task7_claims.py` 全文件。**失败**：上述任一节点红。 | 上述测试节点 ＋ 一次真实 `digest` 记录 |
| FR-K4-2b 断点续跑（能力回收，排在删除之前执行） | 给活编译链加最小断点续跑并补一条钉住测试：同一批次重跑不重复发起 provider 调用（幂等键＝批次目录＋冻结 manifest 指纹）；完整分批策略（批次大小/预算暂停/失败切分恢复）**明确不在本期**（DEF-K4-7）。**失败**：重跑仍重复计费，或无测试钉住。 | 新测试节点 ＋ 一次重跑记录（第二次 provider 调用数为 0） |
| FR-K4-2d K1–K3 不回退（G5） | K1/K2/K3 的活路径测试全绿：K1＝`test_task7_pages.py`/`test_task7_claims.py`/`test_task7_e2e.py`；K2＝`test_task8_*`；K3＝`test_task9_accept.py`/`test_task9_publish.py`；`kb_accept`/`kb_publish` 的既有测试不得被删或改弱。**失败**：任一上述节点红或被移除。 | 上述测试节点（最终 aggregate） |
| FR-K4-2c 无新增红灯 | 以基线红灯清单为豁免名单（DEF-K4-8：`test_task2a_reader_bundle` 15 failed/19 passed）；删除/迁移后**不得出现清单之外的新红灯**；"任一红即失败"只适用于新增红灯。**失败**：出现任一新增失败节点。 | 基线与最终 pytest 收集对比（按节点名做差集） |
| FR-K4-3 旧自证路径移除 | 投影/五维比较/证书/verifier 及其脚本（含 `compiler.py` 整模块）删除或经断言不可达，并给出具体命令与退出码；已核实无 K1/K3 复用符号需要迁移。**失败**：仍可执行，或误删 B 节保留清单内的活模块。 | 不可达断言 ＋ 命令退出码 |
| FR-K4-4 先验后删门禁 | 基线冻结与回归通过发生在任何删除动作之前，且顺序可检查（分批提交/证据顺序）。**失败**：先删后验。 | 顺序检查 |

## 延期与开放项

> DEF-K4-1…9 的唯一权威表；与 `## 风险与延期交接` 共同构成运行时读取的风险与延期门内容。

| id | 内容 | owner | 触发条件 |
| --- | --- | --- | --- |
| DEF-K4-1 | 文档与 `specs/archive` 瘦身（`AGENTS.md` 已与当前命令漂移，需同步；archive 占文档约九成） | 用户 | 代码三项指标完成后另开任务 |
| DEF-K4-2 | 停摆的每日自动化流水线修复 | 用户 | 用户另开任务时（母任务 T-011 原文不变） |
| DEF-K4-3 | 9 个只在 `specs/archive/**` 出现的配置（其中 2 个被 plan.md 以 hash 固定） | 用户 | 确认归档工作流不再需要重放 |
| DEF-K4-4 | 13.77 MiB mapping 修订版与 `apply/`（3.16 MiB 零入站引用） | 用户 | K3 验收 provenance 口径变化时 |
| DEF-K4-5 | `synthesize_*` 接管登记与旧主题移交 | 用户 | 流水线恢复任务启动 |
| DEF-K4-6 | `k4-research-summary.md` 未核实项（配置运行输入为静态调用图结论；测试 pin 清单来自 AST 分析） | build-code | 执行删除前逐文件重读 |
| DEF-K4-7 | 完整分批策略（批次大小、预算暂停、失败切分恢复） | 用户 | 断点续跑落地后另评 |
| DEF-K4-8 | 既有红灯 `test_task2a_reader_bundle::test_validator_rejects_incomplete_claim_provenance`（缺外部冻结 fixture） | 用户 | 需要回放 Task2-A 时补齐 fixture |
| DEF-K4-9 | 母任务旁路请求：anysearch key 应配在哪、dsh 匿名路径 402 的根因与根治 | 用户 | 用户下次使用 anysearch 时（属工具环境问题，不在 K4 范围） |

## Convergence check

| 维度 | 用户答案 | 事实/材料引用 | 可执行验收 |
| --- | --- | --- | --- |
| 目标 | 用户 2026-09-16 确认 T2-01、T2-03、T2-09：基线＝起始提交 `eee5549`，源码净下降优先，不为凑可达保活死代码 | decision-log.md FR-K4-1、R-018，evidence/reachability-audit.md | 同一复算脚本两次输出：物理行与代码行均净下降、不可达清单为空 |
| 范围 | 用户 2026-09-16 确认 T2-02、T2-10：只动代码与 `config/`，只删证据充分的 21 项配置，文档与 specs 不动 | decision-log.md `## 范围`、NG-001…NG-013，evidence/config-audit.md | 最终 diff 只含删除、断点续跑与补测试、配置删除四类；specs/archive、docs、apply 零改动 |
| 方案 | 用户 2026-09-16 确认 T2-05、T2-06、T2-15 与 D-005；取舍：活实现承接 S6、旧自证簇整体删除、legacy 入口退役；被拒方案：保留 legacy 入口、整体重写、先删后验、为凑可达补连接代码；未决项处置：DEF-K4-1…9 已带 owner 与触发条件 | decision-log.md `## 删除与保留清单`、`## 考虑过但未选的方向`、D-001…D-005 | 67/67 模块清单每项恰一个处置；B1/B2 批次互斥；`compiler.py` 整模块删除后 K3 验收仍绿 |
| 验收 | 用户 2026-09-16 确认 T2-08、T2-09：存活能力回归全绿＋一次真实 digest 跑通；合并主干以 K3 查询集验收为门禁 | decision-log.md `## 验收标准` FR-K4-1…FR-K4-4、`## 验收指标冻结` | FR-K4-2a 绑定测试节点全绿；FR-K4-2b 第二次运行 provider 调用为 0；FR-K4-3 旧入口命令退出码非 0 |

- 六类固定类别全覆盖：`complete_user_flow`(OI-01/02)、`page_scope`(OI-03)、`data_state`(OI-04/10/16)、
  `success_failure_boundary`(OI-05/06/07/08/09/15)、`non_goals`(OI-11)、`deferred`(OI-12/13/14)。
- 六个 framework node 全覆盖：background(OI-01/02)、problem(OI-03)、goal(OI-04)、solution(OI-05/06/07/16)、
  acceptance(OI-08/09/15)、extension(OI-13/14)。
- 全部 16 项 OI 已回填终态；`requires_user_decision: true` 的 13 项均由用户 2026-09-16 真实答复确认，
  其余 3 项由本轮事实回答。
- 无未匹配的用户答复；用户在 Round 2 使用的编号（Q1/Q2/Q3/Q4/Q5+Q7/Q8/Q9）已逐条映射到 T2-01…T2-16，
  映射表见 `## Talk`。

## UI applicability

```json
{
  "result": "non_ui",
  "sources": {
    "raw_requirement": "non_ui：用户原始需求要求梳理页面范围，但没有要求开发页面；本任务继承 K4 代码/配置范围。",
    "project_inventory": "non_ui：KnowledgeDigest 是 Python CLI 与本地 Markdown/config 仓库，不是前端应用。",
    "planned_or_changed_frontend_fact": "non_ui：用户已确认本任务不开发、不修改任何前端、路由或交互组件；页面范围只映射为代码与配置面的删除边界。"
  },
  "reason": "交付物是 Python 包与 config/ 的删除/迁移变更；不产生设计输入需求。"
}
```

## Talk

### Round 1（step 3，完成）

按 make-decision 契约，Round 1 先核实仓库现有事实，只问 agent 无法自行确定的方向问题。用户当轮要求先看事实，
主会话先派 4 个取证子代理（见 `## 调研`），把 6 个方向问题与 1 个由事实新引出的口径问题（Q7）一起提出，
用户随后一次性答复（Round 2 记录）。

| T | 问题（大白话） | 选项与后果/风险 | 用户答复 | 映射 |
| --- | --- | --- | --- | --- |
| T1-01 | 瘦身瘦到什么程度 | A 只认三条代码/配置指标（风险：文档堆积仍在）／B 连文档一起清（风险：历史证据不可恢复）／C 只删大文件（风险：回到"凭感觉删"） | **A** | T2-02 |
| T1-02 | 300 行分页与分批恢复怎么处置 | A 迁移或登记归属（风险：判断错留孤岛）／B 全迁移（风险：新增代码抵消净下降）／C 当没用就删（风险：违反 S6） | **A** | T2-05 + OI-15 |
| T1-03 | 删除力度 | A 先验后删、分批可回退（风险：慢）／B 一次清完再验（风险：难定位）／C 只标记不真删（风险：指标过不了） | **A** | T2-01 / T2-08 |
| T1-04 | "没删错"的证据 | A 回归全绿＋一次真实路径（风险：约 150 次 provider 调用）／B 只靠测试（风险：测试绿但能力没了）／C 只人工跑一次（风险：不可复算） | **A** | T2-08 |
| T1-05 | 净下降的起点 | A 本任务起始提交（风险：与旧审计数字不可比）／B 母任务规划时数字（风险：K1–K3 已加代码，可能注定达不到）／C 两条都报 | **A（并采纳 C 的信息性报告）** | T2-03 |
| T1-06 | `synthesize_*` 接管登记本期碰不碰 | A 不碰只守边界（风险：接管风险继续悬着）／B 顺手做完（风险：扩范围、动别人自动化） | **A** | T2-13 |
| T1-07 | "到不了的模块"按哪个口径数 | A 正式入口＋明文登记 legacy 入口（风险：要逐个判断未登记脚本）／B 只算 pyproject 5 个命令（风险：删掉已声明兼容入口）／C 连测试也算（风险：自欺，母任务否定） | **A** | T2-04 |

### Round 2（step 5，完成 · 用户真实答复逐字保留）

> 「Q1：默认按我推荐 / Q2：A / Q3：A / Q4：A / Q5+Q7（默认按我建议） / Q8：A / Q9：A」

主会话在 Round 2 提出的 9 题（含由调研新引出的 Q8、Q9），用户答复编号与映射：

| T | 问题 | 选项、后果与风险（大白话） | 用户答复 | 结论 |
| --- | --- | --- | --- | --- |
| T2-01 | 完整用户旅程（Q1） | A 冻结基线→先验→分批删→复算→合并（风险：慢）／B 先删后补验证（风险：不可回退） | **按推荐 A** | 旅程 J1–J5 |
| T2-02 | 瘦身边界（Q2=A） | A 只动代码与 config（风险：文档仍臃肿）／B 连文档清（风险：证据不可恢复）／C 只删大文件（风险：无证据） | **A** | 范围节 |
| T2-03 | 基线口径（Q3） | A 起始提交 `eee5549`／B 母任务旧数字／C 两条都报 | **A** | FR-K4-1 |
| T2-04 | 不可达口径（Q4） | A 正式入口＋明文登记 legacy 入口／B 只算 5 条正式命令／C 连测试也算 | **A** | FR-K4-1 |
| T2-05 | S6 能力承接（Q5+Q7） | A 活实现承接、旧模块按残骸删（风险：需逐个判断）／B 全迁移（风险：新增代码）／C 一起删（风险：违反 S6） | **A** | OI-05 |
| T2-06 | 旧自证簇（Q9=A） | A 整体删除（风险：无法回放历史 M401/M402）／B 保留实验室入口（风险：源码不降）／C 删代码留脚本（风险：脚本坏在半路） | **A** | OI-16 / FR-K4-3 |
| T2-08 | 先验后删的证据（Q3 的另一半） | A 回归全绿＋真实 `digest` 跑通／B 只靠测试／C 只人工跑一次 | **A** | FR-K4-2 / FR-K4-4 |
| T2-09 | 净下降 vs 凑可达 | A 净下降优先，不保活死代码／B 保活死代码／C 两者都要求 | **按推荐 A** | FR-K4-1 |
| T2-10 | 配置删除边界（Q1 的一部分） | A 只删证据充分的 21 文件/3.19 MiB／B 连 13.77 MiB mapping 一起删／C 全保留 | **按推荐 A** | OI-10 |
| T2-13 | `synthesize_*` 接管（Q6） | A 不碰／B 本期做完 | **A** | DEF-K4-5 |
| T2-15 | 分批+恢复（Q8） | A 只做最小断点续跑＋补测试／B 完整补回批次策略／C 只登记为已知回归／D 不管不记 | **A** | OI-15 |
| T2-16 | 旧自证脚本（Q9 的另一半） | A 只留 `legacy_digest_reference.py`／B 4 条脚本全留／C 全删含 legacy 入口 | **A → 复核后按 D-005 收窄为 C**（用户 2026-09-16 就 D-005 单独确认） | OI-16 |

**歧义校正记录**：Round 1 的 Q2（分页/分批恢复迁移）与 Q6（`synthesize_*` 接管）在调研后前提发生变化，
主会话在 Round 2 明确标注"原 Q2 合并进 Q8、原 Q6 合并进 Q1"，用户按新编号答复；映射已逐条登记，无未匹配答复。

### Round 3（step 7 · 处理 direction-advice 的真实 finding）

`direction-advice`（step 6）真实执行、`semantic_status=available`、两路 × 3 provider 全部返回 findings（非空）：
- red：`quality/reviews/results/make-decision-simple-9388fae3-*.json`（`kimi/coding`、`antigravity/flash`、`codex/luna`）
- blue：`quality/reviews/results/make-decision-simple-fdd80691-*.json`（`codex/luna`、`kimi/coding`、`antigravity/flash`）

**处置规则**：审查提交的材料快照是"用户在 Round 2 答复之前"的版本，因此把它当作**红蓝方向审的提问清单**，
逐条判断在最终决策下是否仍成立。逐条处置如下（不静默丢弃）：

| finding | 严重度 | 处置 | 理由 |
| --- | --- | --- | --- |
| F-bd08fab30019 / F-793d3a82de4b / F-5c0001bee041 / F-74fa7a52eec0：「没有任何已确认方向，16 项 OI 全 open」 | blocking | **rejected_invalid（基于旧快照）** | 审查材料是 Round 2 之前的快照；Round 2 用户已逐条答复，16 项 OI 已全部回填终态（见 OI 记录与 `## 已选方向`）。材料快照时间可由 `## 阶段执行记录` 与 review attempt 记录核对 |
| F-3411f8416152 / F-62ba6069a2d7 / F-6c9325a27a00 / F-793d011f6167 / F-b1cc3be644d0：「OI-15 未裁决／NG-005 与先验后删门禁死锁／补回能力与净下降冲突」 | blocking+major | **fixed** | 用户 T2-15 = A 已裁决：只做最小断点续跑；NG-005 拆成 005a/005b/005c，门禁只管活能力；新增 RISK-009 登记冲突 |
| F-13eb3c7d0b1d / F-86132bb9e87c：「删除边界不可执行，21 个文件没有逐文件清单，计数与枚举不符（7+4+9=20 不是 21）」 | major | **fixed** | 新增 `## 删除与保留清单（file-level）`：逐文件列出删/留/延期，并给出精确计数与口径；已修正"21"的构成（第 21 项为 `task5-provider-contract-handshake-v2.json`） |
| F-8fb3cc4c8426：「`compiler.py` 混合自证与 K1/K3 复用符号，需要符号级清单」 | major | **fixed** | 新增 `## 删除与保留清单` 的"C. 必须保留（符号级）"小节 |
| F-fefcbc7ad433 / F-a0da510788ee / F-226a3b4b3f50：「成功指标未冻结：69.5/13.7/0 三套口径、净下降与可达冲突、缺优先级」 | major | **fixed** | 用户 T2-03/T2-04/T2-09 已定：基线 `eee5549`、口径＝`pyproject` 5 条正式命令、净下降优先；并新增 `## 验收指标冻结` |
| F-e8b625e1874d / F-af6406f72fcb / F-ba7c982e1152 / F-0f342001f7fd：「缺 延期/验收口径、缺 rejected alternatives、缺方案对比」 | blocking+major | **fixed** | 已补 `## 验收标准`、`## 延期与开放项`、`## 考虑过但未选的方向`、`## 删除与保留清单`；D-001…D-004 写明 rejected_alternatives |
| F-c5dae6b56432：「去重被当作已保留，但活实现没有断言钉住」 | major | **fixed** | FR-K4-2 要求补钉住测试（重复来源 fixture 对页面与 ledger 双断言）；G3-A 确认只补活实现缺口 |
| F-a0da510788ee / F-aaab547cb2e4 / F-ac444aa42e74：「不确定性 3/4 已被事实关闭却仍列为未决」 | major/minor | **fixed** | 范围节的不确定性清单已随 Talk Round 2 收敛为已确认约束；300 行分页＝活、分批恢复＝已破、K3 不依赖旧自证均为确定事实 |
| F-1a91017ec9f5：「删除旧自证会让 15+ 测试文件失败，但范围没有测试资产处置边界」 | minor | **fixed** | 新增 `## 删除与保留清单` 的"E. 测试资产处置"小节：同步删除/迁移/显式 red 三类，并写明删除前重读（DEF-K4-6） |
| F-17522e77c695：「母任务原始需求里的 anysearch key 旁路请求被静默丢弃」 | major | **fixed** | 新增 `## 与母任务的关系` 与 DEF-K4-9，逐条登记母任务原始诉求（含 anysearch key 配置与 402 根因）的承接/延期位置 |
| F-d4253d85b660：「OI-15≈OI-05、OI-16≈OI-06 近重复」 | minor | **rejected_invalid（不合并）** | 两组问的是不同决定：OI-05/OI-06 是"能力与路径的现状与删除口径"，OI-15/OI-16 是"用户对处置方式的拍板"；合并会让"事实"与"决定"混在一个 OI 里，违反 OI 单项可处置原则。已用 source 交叉引用标明关系 |
| F-727de29f9aa0 / F-74fa7a52eec0：「方向偏离原始需求（效果对比/架构评估/外部调研/语义层形态）」 | major | **fixed** | 新增 `## 与母任务的关系`：本期只承接 R-004 的可维护性一半；其余原始诉求按母任务已完成的 F-001/F-003/D-009 与 K1/K2/K3 归档位置逐条登记 |

### Grill（step 8 · 3 个前沿问题，用户真实答复）

> 「G1：A / G2：A / G3：A」

| G | 被压力测试的点 | 选项、后果与风险 | 答复 | 结果 |
| --- | --- | --- | --- | --- |
| G1 | "瘦身任务里加新功能"是否跑偏（断点续跑 + 补测试） | A 保留但只叫"能力回收"、加行数上限与一条新测试／B 完全不写新代码／C 写但不设上限 | **A** | 写入 D-002 + NG-005b；新代码必须可量化 |
| G2 | 三项指标能否被刷分（删注释/新增连接代码/误删运行输入） | A 复算同时出代码行与物理行＋模块/函数/测试数／B 只按物理行／C 追加"测试通过数不得下降"硬指标 | **A** | 写入 FR-K4-1；C 被否理由＝本期要删约百条旧自证测试，硬指标必然不成立 |
| G3 | 是否顺手补测试与修红灯 | A 只补活实现缺口（去重），既有红灯如实登记延期／B 全部修／C 都不补 | **A** | 写入 FR-K4-2；B 被否理由＝缺外部冻结 fixture，可能被迫重建历史产物（范围爆炸） |

### Round 4（step 10 · 处理 detail-advice 的真实 finding 与修复）

`detail-advice`（step 10）第 1 轮真实执行、`semantic_status=available`、两路 × 3 provider 共 **38 条 finding**：
- red：`quality/reviews/results/make-decision-simple-c81e9e67-*.json`（21 条）
- blue：`quality/reviews/results/make-decision-simple-c2087bd4-*.json`（17 条）

**这一轮发现的是真缺陷，不是"没读材料"**——其中 3 条 blocking 死锁成立，已在本 stage 当场修复：

| finding | 严重度 | 处置 | 修复内容 |
| --- | --- | --- | --- |
| 「FR-K4-2 要求 S6 五项（含已丢失的分批恢复）全绿，而先验后删门禁要求在删除前通过 → 基线必然判失败，形成无法启动删除的死锁」（多路重复：antigravity/flash、codex/luna、kimi/coding） | blocking×3+major | **fixed（真缺陷）** | FR-K4-2 拆为 2a/2b/2c：2a 只约束**当前存活**的 4 项并逐项绑定测试节点；2b 断点续跑＋钉住测试**移到删除之前**（旅程 J2，取消原 J4）；2c 以基线红灯清单为豁免、只判"新增红灯" |
| 「`scripts/legacy_digest_reference.py` 既是可达性根又依赖将被删除的 11 个旧模块，OI-16 说不修、D-003 说改指向却无方案 → root 与删除范围互相冲突，保留即坏脚本」 | blocking×2+major | **fixed（真缺陷）** | 新增 **D-005**：删除该脚本，可达性根集合＝`pyproject` 5 条正式命令；同步登记 RISK-012 与 DEF-K4-1（`AGENTS.md` 退役段） |
| 「A 节标题写 21 文件但代码块只有 20 行，且『第 21 项是 handshake-v2』的解释不成立」 | major | **fixed（真缺陷）** | 逐行重写 A 节：21 项全部列出（含 `task5-provider-contract-handshake-v1.json` 与 `-v2.json` 两个独立条目），并给出总字节 3,341,698 B 与 `config/` 全量 76 文件处置表 |
| 「`03-draft_spec_or_acceptance` 首行截断、正文在 FR 表后终止、`context_map` 两个字段为空字符串」 | blocking×2+major | **fixed（材料生成缺陷）** | 重建 detail 材料：验收草案独立成稿（验收标准＋延期＋file-level 清单＋指标冻结），`context_map` 填入清单与指标原文 |
| 「file-level 清单对代码/测试只是近似分组（B1/B2 用"约"、B3 用"等"、C 节只列部分符号）→ 39 个不可达模块无法逐一映射处置」 | major×3 | **fixed** | B 节改为**逐模块 67/67 全量表**（删除 39 / digest 闭包 19 / 其它命令闭包 9，校验 39+19+9=67）；C 节给出必须保留项与依据 |
| 「`compiler.py` 保留 `_route_ledger_projection` 与不可达归零互斥」 | major | **fixed（已核实）** | 核实 `kb_accept.py` 不读 `_audit/route-ledger.jsonl`，唯一引用方是两条 Task5 测试；`compiler.py` 随 B2 整模块删除，无需迁移 |
| 「DEF 编号漂移：OI-12 写 DEF-K4-4、正文说 DEF-K4-6；D-004/N-extension 写 DEF-K4-1…8 而表内 9 项；表内 DEF-K4-8/9 乱序」 | major×2+minor | **fixed（真缺陷）** | `## 延期与开放项` 重排为 DEF-K4-1…9 连续且声明为编号唯一权威；OI-12 改引 DEF-K4-6；R-022/N-extension 引用改 DEF-K4-1…9 |
| 「核心需求写"没有零引用的配置"，而 G1/FR-K4-1 只要求下降且在范围内延期 9+13.77 MiB → 目标与验收不一致」 | major×2 | **fixed** | 核心需求与 G1 改写为"证据充分的零引用配置被清除且总量下降"，并显式指向 DEF-K4-3/4 的保留项 |
| 「FR-K4-2c/G5 没有 K1–K3 不回归的验收项」 | major×2 | **fixed** | FR-K4-2a 绑定 K1/K2/K3 相关测试节点（`test_task7_*` 分页与 claims、`test_task7_e2e` blocked 语义、`test_task8_*` 导航）；`kb_accept`/`kb_publish` 的既有测试列入保留并要求全绿 |
| 「延期表只有 7 行却写九项；缺少 DEF-K4-7 行」 | major | **fixed** | 见上（表内 1–9 连续，含 DEF-K4-7 完整分批策略） |
| 「『## 与母任务的关系』复用 R-00x 编号，与本任务 R-001…R-025 冲突」 | minor | **fixed** | 该表第一列改用母任务 id（母 F-001/F-002/F-003、母 R-004…） |
| 「母任务原话里的 anysearch key 旁路请求被静默丢弃」 | major×2 | **fixed** | 已登记 DEF-K4-9（owner=用户、触发=下次使用 anysearch 时），并在 `## 与母任务的关系` 写明不在 K4 范围 |
| 「01 材料是母任务 2026-09-12 原话，task10 自己的原话只在 02 里」 | minor | **fixed** | detail 材料重建：`raw_requirement` 同时包含 task10（2026-09-16）与母任务（2026-09-12）逐字原话，并标注权威位置 |
| 「FR-K4-4 的"分批提交/证据顺序"不是可机器验证的证明；复算脚本没有路径、命令、退出码」 | major | **accepted_risk（转 build-plan 细化）** | 顺序门禁的可执行形式（基线冻结报告 hash、逐批引用、缺失即失败）属于实现层规格；本阶段已冻结"先验后删"的语义与批次划分，具体命令/退出码在 build-spec/build-plan 细化（不改变方向） |

**复核声明**：上表除最后一条为 `accepted_risk`（实现层细化，方向不变）外，其余均为本 stage 当场修复。
修复后已重新导出 detail 材料并再次发起 detail-advice（第 2 轮），结果与本轮处置一并留在 `quality/reviews/`。

## 决定条目 D*

### M-范围与门禁

#### D-001
- question/final_option: 瘦身任务整体怎么做？→ 冻结基线 → 先验后删 → 分批删除 → 复算三项指标 → 以 K3 验收为门禁合并。
- recommendation/plain_language: 推荐。大白话：先把"现在多大、哪些到不了、哪些配置没人用"记成可比对的底账，跑一遍能力验证，然后一小批一小批地删，每删一批就验一次，最后用同一个脚本算一遍账。
- decision: 用户 2026-09-16 确认 T2-01/T2-03/T2-04/T2-08/T2-09 = 全 A。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ 本文件 `## Talk` Round 2 /「Q1：默认按我推荐 … Q8：A Q9：A」。
- approval_binding: confirmed（用户 2026-09-16 答复；interaction aggregate 由 `approve-decision` 写入）
- facts_and_constraints: `src/` 67 模块/56,382 行；39 模块/39,161 行不可达；config 76 文件/17.57 MiB，其中 21 文件/3.19 MiB 证据充分可删；旧自证簇 ≈24,021 行；S6 四项已有活实现、分批恢复已破。
- Logic: 事实（大量死代码与零引用配置 + 一项能力真丢）→ 约束（S6 不得破坏、K1/K3 语义不得改、指标可复算）→ 选择（先验后删 + 净下降优先 + 活实现承接）→ 预期结果（更小且能力不丢）。
- choice_reason/impact: 先验后删让"删错"可回退；净下降优先避免"为凑可达保活死代码"把指标做成自欺；影响＝删除清单、批次顺序、回归命令集。
- consequences_and_risks: 历史 M401/M402 证据不再可回放（已接受 RISK-004）；`compiler.py` 需逐符号拆解（RISK-003）。
- rejected_alternatives: 先删后验（不可回退）；保活死代码（自欺）；连文档一起清（证据不可恢复）。
- unresolved_items/owner: 具体删除批次与文件清单 → build-plan。
- Supersedes: none
module: M-范围与门禁
requirement_ids: [R-001, R-008, R-018, R-019]
derived_from: []
artifacts: []

#### D-002
- question/final_option: 唯一真丢的能力"分批 + 恢复"怎么办？→ 本期只做最小断点续跑，完整批次策略延期。
- recommendation/plain_language: 推荐。大白话：现在重跑一次会把同一批内容再喂给模型一遍（白花钱），先修成"重跑不重复烧钱"，至于批次怎么切、预算怎么停，以后专门做。
- decision: 用户 2026-09-16 确认 T2-15 = A。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ 本文件 `## Talk` Round 2 /「Q8：A」。
- approval_binding: confirmed
- facts_and_constraints: 活语义编译链无 resume，每次 `allocate_batch_dir` 开新目录；`batch_run.run_batched` 无任何 CLI 可传参（`digest` 与 legacy 脚本都拒绝批次参数）；15 条 batch 恢复测试是"直接 import 不可达模块"跑绿的；现有替代是 `ModelCache` 缓存复用 + 冻结 manifest。
- Logic: 事实（能力消失且入口不可达）→ 约束（S6 列为保留不变量、不得为此扩大范围到重写批次策略）→ 选择（最小断点续跑 + 补测试）→ 预期结果（重跑同批次不重复 provider 调用，能力有真实归属）。
- choice_reason/impact: 完整补回会改变 K1 已交付行为并新增大量代码；只登记不修等于带着已知违约交付；影响＝`semantic_compiler`/`semantic_cli` 的恢复边界与一条新测试。
- consequences_and_risks: 新增代码与"净下降"轻微对冲（RISK-007）；完整分批策略继续缺席（DEF-K4-7）。
- rejected_alternatives: 完整补回批次策略；只登记为已知回归不修；不修也不登记。
- unresolved_items/owner: 断点续跑的具体判定键与测试口径 → build-plan/build-code。
- Supersedes: none
module: M-范围与门禁
requirement_ids: [R-017, R-021]
derived_from: [D-001]
artifacts: []

### M-删除边界

#### D-003
- question/final_option: 删除边界与配置边界是什么？→ 旧 S1–S6 残骸 + 旧自证簇 + 旧自证脚本删除；只删证据充分的 21 个配置。
- recommendation/plain_language: 推荐。大白话：删的是"新命令已经不用、只剩旧入口和测试在用的那堆代码"，以及"没人引用、且有证据证明是旧版本残留"的配置；引用了别人的那份 13.77 MiB 映射先留着。
- decision: 用户 2026-09-16 确认 T2-02/T2-05/T2-06/T2-10/T2-16 = A。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ 本文件 `## Talk` Round 2 /「Q9：A」等。
- approval_binding: confirmed
- facts_and_constraints: `digest` 运行闭包 0 个 legacy；旧 S1–S6 11 模块/12,017 行仅由 `scripts/legacy_digest_reference.py` 与测试引用；旧自证簇 ≈24,021 行；K3 的 `kb_accept` 只依赖 `errors`+`kb_publish`；`config/knowledge-digest.json` 只经 `cli.py`（已非 console script）到达。
- Logic: 事实（可达性 + 引用证据）→ 约束（S6 能力不得丢、K3 验收不得破、文档不动）→ 选择（删残骸与证据充分配置、保留明文登记的 legacy 入口与 provenance 配置）→ 预期结果（行数与配置双降且能力不丢）。
- choice_reason/impact: 逐符号保留 `compiler.py` 中被 K1/K3 复用的部分；影响＝删除清单、需同步处置的测试文件、legacy 入口的保留范围。
- consequences_and_risks: 必须保留的东西（K1 `原文未明确` 标记、`navigation_status=="generated_ok"` 门、`_audit/sources.jsonl`/`reference-blocks.jsonl`、`kb_publish` 原子发布、legacy 参数拒绝逻辑及其测试）一旦误删即破坏 K1–K3（RISK-001/RISK-003）。
- rejected_alternatives: 连 13.77 MiB mapping 一起删（破坏 K3 provenance）；连测试也算入口（自欺）；连 `legacy_digest_reference.py` 一起删（删掉明文声明的兼容入口）。
- unresolved_items/owner: 逐文件删除清单与批次 → build-plan；未核实项重读 → build-code（DEF-K4-6）。
- Supersedes: none
module: M-删除边界
requirement_ids: [R-009, R-011, R-014, R-015, R-016]
derived_from: [D-001]
artifacts: []

#### D-005
- question/final_option: `scripts/legacy_digest_reference.py` 的终态，以及"可达性根集合"怎么定？→ **删除该脚本**，把可达性根限定为 `pyproject` 的 5 个正式命令；同步在文档登记"旧 CLI 与 offline 分支已退役"。
- recommendation/plain_language: 推荐。大白话：那个"历史兼容入口"其实通向的是我们这次要删掉的整套旧管线（12,017 行）；留着它，要么删不干净（一半模块还"活着"），要么留下一个必然报错的坏脚本。所以我们把它一起退役，可达性就只按 5 个真命令算。
- decision: 用户已选 Q9-A / T2-16-A（"只保留 `legacy_digest_reference.py` 作明文登记的历史入口"）与 T2-05-A（活实现承接）；detail-advice 指出该保留与删除范围直接冲突（root 与待删模块互相依赖），主会话据既有授权把"保留"收窄为"退役并登记"，方向不变、范围更自洽。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ 本文件 `## Talk` Round 2 /「Q9：A」；detail-advice finding（`quality/reviews/results/make-decision-simple-c81e9e67-*.json`、`…-c2087bd4-*.json`）指出 root/删除冲突。
- approval_binding: confirmed（**用户 2026-09-16 就 D-005 单独答复「A」**：连 legacy 脚本一起退役删除；该确认同时收窄 T2-16 的原选择，属方向级变更，已获真实用户答复）
- facts_and_constraints: 该脚本是 11 个旧 S1–S6 模块（12,017 行）的唯一非测试调用方；`compiler.py`（8,058 行）只被 `task5_runtime`/`task5_semantic_model`/`m401_r_adapter` 与其自身引用；`providers`/`publisher` 只被 `compiler.py`/`task5_*` 引用（即同批删除对象）；正式的 `digest` 与 `knowledge-digest-accept` 完全不经过它们。
- Logic: 事实（root 与待删对象互为依赖）→ 约束（不可达必须归零、不得保活死代码、K1–K3 不得回退）→ 选择（退役 legacy 入口 + 删除旧管线）→ 预期结果（39 个不可达模块可全部处置，指标自洽）。
- choice_reason/impact: 保留一个指向已删模块的脚本等于制造"必然失败"的入口（NG-010 的变体）；影响＝`AGENTS.md` 的旧命令段必须同步标注退役（DEF-K4-1 的具体项）、可达性根集合写死为 5 条命令。
- consequences_and_risks: 用户若仍需"旧 reader 行为"，本期不再提供；该损失已登记（见 RISK-012），并在 `AGENTS.md` 更新前保持文档与代码不一致（DEF-K4-1）。
- rejected_alternatives: 保留脚本并改指向活实现（用户 T2-16 已排除"改指向/扩测试"，且需要新增适配代码）；把脚本算作 root（会使 12,017 行旧管线永久"可达"，与归零目标冲突）；保留脚本但不管（坏入口）。
- unresolved_items/owner: `AGENTS.md` 退役段与 `scripts/` 清理清单 → build-plan（DEF-K4-1）。
- Supersedes: none
module: M-删除边界
requirement_ids: [R-011, R-017, R-018]
derived_from: [D-001, D-003]
artifacts: []

### M-非目标与延期

#### D-004
- question/final_option: 本期明确不做什么、延期什么？→ 不碰文档/`apply/`/映射修订版/停摆流水线/接管登记；九项延期写入带 owner 与触发条件的清单。
- recommendation/plain_language: 推荐。大白话：这次只把"代码和没人用的旧配置"收拾干净，别顺手去动历史文档、别人的自动化，也别为了好看去删还引用着的东西。
- decision: 用户 2026-09-16 确认 T2-02/T2-10/T2-13 = A。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ 本文件 `## Talk` Round 2。
- approval_binding: confirmed
- facts_and_constraints: `specs/archive` 占文档约 91%；`apply/` 143 文件/3.16 MiB 零入站引用；9 个配置只在 `specs/archive/**` 出现（其中 2 个被 plan.md 以 hash 固定）；停摆流水线恢复时会 rename/unlink `Products/` 下页面。
- Logic: 事实（这些资产的引用只在归档里）→ 约束（用户不愿本期扩范围）→ 选择（一律延期并登记 owner/触发条件）→ 预期结果（范围清楚且风险不会遗忘）。
- choice_reason/impact: 归档材料是历史证据，删除不可逆；影响＝范围节、NG-012、DEF-K4-1…8。
- consequences_and_risks: 文档与命令漂移（`AGENTS.md` 仍写已失效的 `--config/--quality-config/--gate`）本期不修，属于已知遗留。
- rejected_alternatives: 顺手清文档；顺手修流水线；顺手做接管登记。
- unresolved_items/owner: 见 `## 延期与开放项`。
- Supersedes: none
module: M-非目标与延期
requirement_ids: [R-011, R-022]
derived_from: [D-001]
artifacts: []

## 与母任务的关系（本期只是 K4 一张卡）

| 母任务原始诉求 | 本期处置 | 承接位置 |
| --- | --- | --- |
| 母 F-001/F-004 release4 效果如何、与 CompanyBrain 差距 | 不在本期；母任务已完成 | 母任务 F-001/F-004；K3 `kb_accept` 对照验收 |
| 母 F-002 / 母 R-004 架构、性能、可维护性 | **本期只承接"可维护性"的代码/配置减重一半**；性能与成本度量的另一半由 K3 承接 | 母任务 F-002；K3 `observed_calls` 修复；本文件 FR-K4-1 |
| 母 F-003 / 母 R-005 外部开源是否有更好做法 | 不在本期；母任务已结论"不整体引入"，只留 3 个候选参考 | 母任务 F-003/D-009 |
| 母 R-006 效果更好 + 项目更简单 | 本期负责"更简单" | FR-K4-1…FR-K4-4 |
| 母 R-007/R-008 按 WorkflowHub 五阶段、不跳阶段 | 本期遵守 | `## 阶段执行记录` |
| 母 R-009 六类边界梳理 | 本期已梳理 | Fixed categories 六类 |
| 母 R-010/R-011 上下文控制与大白话 Talk/Grill | 本期遵守 | NG-006；`## Talk`/Grill |
| 母任务后续补充请求：anysearch key 配置位置、dsh 402 匿名路径根因与根治 | **不在本期范围**（属工具环境问题，非 K4） | DEF-K4-9（owner=用户，触发=用户下次使用 anysearch 时；登记位置为母任务原始需求逐字记录） |
| 语义知识层最终形态与下游可消费性 | 不在本期；由 K1（页面契约）/K2（导航）/K3（发布与验收）承接 | 母任务 T-005/T-006 + ADR-0013/0014 |

## 考虑过但未选的方向（rejected alternatives）

| 方案 | 为什么没选 |
| --- | --- |
| **只归档不删除**（把死代码/旧自证移入 `attic/` 或独立 namespace） | 源码行数与可达性指标都不会改善；母任务 T-004 明确要"砍掉历史分支"，只搬家等于换个地方堆着 |
| **推倒重写**（用新编译链重写项目后删掉旧的一切） | 母任务 T-004 已否决：会丢掉多年积累的边界处理经验，重走旧坑；且本期不是重构任务 |
| **先删后验**（一次清干净再统一验证） | 不可回退；删错时无法定位到具体批次（FR-K4-4 会直接判失败） |
| **靠 git 历史保留、工作区直接删** | 表面上"历史还在"，但下一位维护者仍面对同一堆不可达代码与零引用配置；且历史可回放 ≠ 当前可维护 |
| **本期不做瘦身，只修文档与命令漂移** | 漂移确实存在（`AGENTS.md` 仍写已失效命令），但那是 DEF-K4-1；不解决 69.5% 不可达与 17.57 MiB 配置 |
| **为让 39 个不可达模块归零而补入口/连接代码** | 与净下降直接冲突，且本质是"保活死代码"（NG-011，用户 T2-04 已否） |
| **连文档、`specs/archive`、`apply/` 一起清** | 历史证据不可恢复；用户 T2-02 已选只动代码与 config（DEF-K4-1/DEF-K4-4） |
| **整体引入外部项目替代自研** | 母任务 F-003 结论：41 个候选中无一占据该产品位（NG-004） |
| **把 13.77 MiB mapping 修订版一起删** | 它们是同级 oracle 配置的 `oracle.mapping_fixture` 生成来源；删除会破坏 K3 验收 provenance 的可复算性 |

## 删除与保留清单（file-level，build-plan 直接消费）

口径：路径均相对仓库根；"证据"列指向 `evidence/` 下的报告。数量口径与配置审计一致（`config/` 共 76 文件）。

### A. 计划删除（证据充分 · 21 文件 / 3,341,698 B）

配置（`config/`，21 项全部为被取代的生成修订版或被取代的 `-v1/-v2` 合同）：

```
config/task4-companybrain-mapping-20260819-v1.json
config/task4-companybrain-mapping-20260819-v2.json
config/task4-companybrain-mapping-20260819-v4.json
config/task4-companybrain-mapping-20260819-v5.json
config/task4-companybrain-mapping-20260819-v7.json
config/task4-companybrain-mapping-20260819-v9.json
config/task4-companybrain-mapping-20260819-v10.json
config/task4-reader-case-matrix-89-semantic-v4.json
config/task4-reader-case-matrix-89-semantic-v5.json
config/task4-reader-case-matrix-89-semantic-v6.json
config/task4-reader-case-matrix-89-semantic-v7.json
config/task5-companybrain-baseline-v1.json
config/task4-reader-quality-88-diagnostic.v1.json
config/task5-provider-contract-handshake-v1.json
config/task5-provider-contract-handshake-v2.json
config/task5-provider-semantic-output-v1.json
config/task5-root-cause-evidence-v1.json
config/task5-source-not-documented-contract-v1.json
config/task5-source-digest-contract-v1.json
config/task5-publication-layout-v1.json
config/task5-reader-quality-v1.json
```

说明：本清单以 `evidence/config-audit.md` §8a 为唯一依据；该表逐项给出"为何死"的引用事实，
并已用 raw sha256 与 canonical-JSON sha256 双口径复核（0/21 在 `config/` 之外被引用）。
删除前仍须按 DEF-K4-6 逐文件重读确认。**精确数量以本清单行数为准**（21 行；此前叙述里"7+4+9=20"的
口头枚举是错的，已被本清单取代——第 21 项是 `task5-provider-contract-handshake-v2.json`）。


#### config/ 全量 76 文件处置表

config 共 76 文件 / 18,427,623 B。**A 节删除 21 项 / 3,341,698 B**＝被取代的生成修订版（mapping 7、case-matrix 4）＋被取代的 `-v1` 合同（10）；**延期 9 项 / 85,472 B**＝仅被 `specs/archive` 提及、由命令行手工传入的合同/fixture（DEF-K4-3）；其余 46 项分别保留（digest 运行输入 2、活引用 21、测试 fixture 2）或按 DEF-K4-4 延期（config 内 provenance 18、apply/ 引用 1、仅文档 2）。口径：本表"审计引用类别"逐行取自 `evidence/config-audit.md` 全量表；删除/延期/保留三类互斥且合计 76。

| # | 文件 | 字节 | 审计引用类别 | 处置 |
| --- | --- | --- | --- | --- |
| 1 | `task4-companybrain-mapping-20260819-v13-89.json` | 3241501 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 2 | `task4-companybrain-mapping-20260819-v11.json` | 3241318 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 3 | `task4-companybrain-mapping-20260819-v12.json` | 3241318 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 4 | `task4-companybrain-mapping-20260819-v13-88.json` | 3240971 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 5 | `task4-companybrain-mapping-20260819-v10.json` | 1102375 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 6 | `task4-companybrain-mapping-20260819-v9.json` | 556483 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 7 | `task4-companybrain-mapping-20260819-v7.json` | 463027 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 8 | `task4-companybrain-mapping-20260819-v8.json` | 463027 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 9 | `task4-companybrain-mapping-20260819-v6.json` | 257958 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 10 | `task5-quality-cases-v2.json` | 257839 | src-referenced | 保留（活实现引用） |
| 11 | `task4-companybrain-mapping-20260819-v4.json` | 257522 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 12 | `task4-companybrain-mapping-20260819-v5.json` | 252958 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 13 | `task5-quality-cases-v1.json` | 215697 | docs-only mention | 延期（DEF-K4-3/4：仅文档提及） |
| 14 | `task5-source-page-manifest-v2.json` | 174851 | src-referenced | 保留（活实现引用） |
| 15 | `task4-reader-case-matrix-89-semantic-v8.json` | 127329 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 16 | `task4-reader-case-matrix-89-semantic-v7.json` | 127138 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 17 | `task4-reader-case-matrix-89-semantic-v4.json` | 126815 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 18 | `task4-reader-case-matrix-89-semantic-v5.json` | 126627 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 19 | `task4-reader-case-matrix-89-semantic-v6.json` | 126627 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 20 | `task4-reader-case-matrix-88-diagnostic-v1.json` | 125972 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 21 | `task4-reader-case-matrix-89-input-oracle-v2.json` | 100866 | tests-only | 保留（测试 fixture） |
| 22 | `task4-companybrain-mapping-20260819-v1.json` | 79922 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 23 | `task4-companybrain-mapping-20260819-v3.json` | 79872 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 24 | `task4-companybrain-mapping-20260819-v2.json` | 77821 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 25 | `task4-reader-case-matrix-89-input.v1.json` | 67497 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 26 | `task5-projection-rules-v1.json` | 38975 | src-referenced | 保留（活实现引用） |
| 27 | `task4-source-coverage-89-input.v1.json` | 22051 | digest-runtime | 保留（digest 运行输入） |
| 28 | `task9-comparison-mapping.v1.json` | 18639 | docs-only mention | 延期（DEF-K4-3/4：仅文档提及） |
| 29 | `task5-companybrain-baseline-v2.json` | 14774 | src-referenced | 保留（活实现引用） |
| 30 | `task5-companybrain-baseline-v1.json` | 13323 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 31 | `task4-reader-quality-88-diagnostic.v1.json` | 13224 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 32 | `task5-machine-evidence-contract-v1.json` | 13154 | src-referenced | 保留（活实现引用） |
| 33 | `task5-source-digest-contract-v2.json` | 10640 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 34 | `task4-reader-quality.v1.json` | 9503 | apply/ mention only | 延期（DEF-K4-4：apply/ 引用链） |
| 35 | `task4-location-pilot.v1.json` | 9453 | tests-only | 保留（测试 fixture） |
| 36 | `task5-runtime-authority-map-v1.json` | 8290 | src-referenced | 保留（活实现引用） |
| 37 | `task5-source-not-documented-contract-v2.json` | 8049 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 38 | `task4-question-oracle.v1.json` | 8019 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 39 | `task0-question-set.v1.json` | 7887 | src-referenced | 保留（活实现引用） |
| 40 | `task5-quality-result-v3.json` | 7342 | src-referenced | 保留（活实现引用） |
| 41 | `task5-reader-path-relation-contract-v1.json` | 6359 | src-referenced | 保留（活实现引用） |
| 42 | `task5-source-sensitive-content-scan-v1.json` | 5239 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 43 | `task5-root-cause-evidence-v2.json` | 4840 | src-referenced | 保留（活实现引用） |
| 44 | `task5-provider-contract-handshake-v3.json` | 4581 | src-referenced | 保留（活实现引用） |
| 45 | `task5-root-cause-input-manifest-v1.json` | 4089 | src-referenced | 保留（活实现引用） |
| 46 | `task5-semantic-frame-field-closure-v1.json` | 3983 | src-referenced | 保留（活实现引用） |
| 47 | `task5-source-block-claim-contract-v1.json` | 3882 | src-referenced | 保留（活实现引用） |
| 48 | `task5-run-result-v1.json` | 3808 | src-referenced | 保留（活实现引用） |
| 49 | `task5-semantic-frame-v1.json` | 3771 | src-referenced | 保留（活实现引用） |
| 50 | `task5-provider-contract-handshake-v2.json` | 3641 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 51 | `task5-provider-semantic-output-v1.json` | 3317 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 52 | `task5-provider-semantic-output-v2.json` | 3223 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 53 | `task5-companybrain-observation-v2.json` | 3215 | src-referenced | 保留（活实现引用） |
| 54 | `task5-slice-cases-v1.json` | 3169 | src-referenced | 保留（活实现引用） |
| 55 | `task5-external-processing-policy-v1.json` | 3127 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 56 | `task5-provider-config-v1.json` | 3073 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 57 | `task5-root-cause-evidence-v1.json` | 3043 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 58 | `task5-provider-contract-handshake-v1.json` | 2527 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 59 | `task5-replay-store-v1.json` | 2309 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 60 | `task5-publication-layout-v2.json` | 2256 | src-referenced | 保留（活实现引用） |
| 61 | `task5-source-direct-contract-v1.json` | 2218 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 62 | `task5-reader-quality-provider-v2.json` | 2209 | src-referenced | 保留（活实现引用） |
| 63 | `task5-source-not-documented-contract-v1.json` | 1857 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 64 | `task5-provider-prompt-contract-v1.json` | 1758 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 65 | `task5-provider-config-v2.json` | 1752 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 66 | `task5-source-digest-contract-v1.json` | 1591 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 67 | `task5-m401-r-review-receipt-v1.json` | 1267 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 68 | `task5-publication-layout-v1.json` | 1217 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 69 | `task5-provider.example.json` | 876 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 70 | `task5-calibration-manifest-v1.json` | 664 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 71 | `task5-reader-quality-v1.json` | 643 | no reference anywhere (excl. specs/archive) | 删除（A 节） |
| 72 | `task4-page-type-registry.v1.json` | 559 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 73 | `task4-reader-evaluator.v1.json` | 396 | config-provenance only | 延期（DEF-K4-4：K3 验收 provenance） |
| 74 | `knowledge-digest.json` | 359 | src-referenced | 保留（活实现引用） |
| 75 | `task4-semantic-baseline.v1.json` | 106 | no reference anywhere (excl. specs/archive) | 延期（DEF-K4-3：仅在 specs/archive 被提及；其中 2 个被 plan.md 以 hash 固定） |
| 76 | `task7-topic-map.json` | 45 | digest-runtime | 保留（digest 运行输入） |

### B. 源码模块逐模块处置（67/67，无遗漏）

| 处置 | 模块数 | 物理行 | 模块清单（模块名：行数） |
| --- | --- | --- | --- |
| **删除**（从所有正式入口不可达） | 39 | 39161 | agentmemory_store:236；batch_run:990；cli:155；cluster:79；companybrain_mapping:650；companybrain_snapshot:88；compiler:8058；draft:2465；embedding:324；full_release:1281；ingest:284；jsonl:133；m401_r_adapter:789；navigation:344；okf_smoke:276；page_layout:1382；paths:68；pipeline:3739；provenance:310；providers:497；publisher:259；quality:1998；quality_compare:291；queues:62；reader_bundle:2221；reader_compiler:860；reader_frontmatter:95；reader_quality:2139；retrieve:125；runtime_status:131；task4_location_pilot:756；task4_reader_quality:1714；task5_provider:86；task5_quality_gate:356；task5_runtime:3392；task5_semantic_model:98；text_similarity:131；topic_axis:1604；writeback:695 |
| **保留**（`digest` 闭包内） | 19 | 11618 | errors:16；faithfulness:131；identity:188；kb_structure:917；knowledge_digest:2；llm:1389；provider_config:152；publication:1017；semantic_audit:1028；semantic_cache:409；semantic_claims:426；semantic_cli:192；semantic_compiler:1899；semantic_group:439；semantic_nav_check:1298；semantic_navigation:526；semantic_page:1047；semantic_split:476；simple_cli:66 |
| **保留**（其它正式命令闭包内，本轮不动） | 9 | 5603 | calibration:696；calibration_artifact:126；calibration_cli:271；config:333；corpus_isolation:157；gold:338；kb_accept:2248；kb_publish:1399；lock:35 |

校验：39 + 19 + 9 = 67（`src/` 模块总数 67）

分批执行顺序（每批删完立即跑聚焦验证，红则回退该批）：

| 批次 | 内容 | 说明 |
| --- | --- | --- |
| B0 | 先做 FR-K4-2b 断点续跑 ＋ 去重钉住测试（J2，**在删除之前**） | 见 D-002、FR-K4-2a/b/c |
| B1 | 删除旧 S1–S6 与双 provider/发布器：`pipeline`、`draft`、`cluster`、`retrieve`、`page_layout`、`navigation`、`writeback`、`provenance`、`ingest`、`batch_run`、`cli`、`task4_location_pilot`、`topic_axis`、`jsonl`、`paths`、`queues`、`embedding`、`text_similarity`、`agentmemory_store`、`runtime_status`、`reader_bundle`、`reader_frontmatter`、`okf_smoke`、`providers`、`publisher`（`reader_compiler`/`reader_quality` 属 B2 自证簇，不得重复指派） | 逐个确认不在 5 条正式命令闭包内；`errors`/`identity`/`kb_structure`/`provider_config`/`semantic_*`/`kb_accept`/`kb_publish`/`simple_cli`/`llm`/`publication` 保留 |
| B2 | 删除旧自证簇：`compiler`、`quality`、`quality_compare`、`companybrain_snapshot`、`companybrain_mapping`、`task4_reader_quality`、`reader_compiler`、`reader_quality`、`task5_runtime`、`task5_quality_gate`、`task5_provider`、`task5_semantic_model`、`full_release`、`m401_r_adapter` | B1 完成后这些模块的引用者已消失；删前按 DEF-K4-6 逐文件重读 |
| B3 | 删除 `scripts/legacy_digest_reference.py` 及其余旧自证脚本 | 见 D-005；`AGENTS.md` 退役登记见 DEF-K4-1 |
| B4 | 删除 A 节 21 个配置 | 逐文件复核后删 |

### C. 必须保留（活代码与活契约，误删即破坏 K1–K3）

| 保留项 | 位置 | 理由 |
| --- | --- | --- |
| `原文未明确` 标记与相关语义 | `semantic_audit.py`、`semantic_claims.py`、`semantic_compiler.py` | ADR-0014 / K1 数据状态；**不是** SND 证书 |
| `navigation_status == "generated_ok"` 批次门 | `kb_publish.py` | K2 前置，K3 发布依赖 |
| `_audit/sources.jsonl`、`_audit/reference-blocks.jsonl` | `semantic_audit.py` 产出，`kb_accept.py` 读取 | K1 机器闭包；与旧 Task5 同名 ledger 不是一回事 |
| `kb_publish` 原子发布/回滚/LKG | `kb_publish.py` | K3 核心能力 |
| legacy 参数拒绝逻辑及其测试 | `simple_cli.py` ＋ `tests/acceptance/test_task5_publication_contract.py` 中**与参数拒绝相关的用例** | 保留并保持全绿；该文件里依赖 `compiler.py` 投影函数的用例（如 `_route_ledger_projection` 相关）随 B2 单独删除，**不整文件删除** |
| `semantic_*` 全族、`kb_accept`、`provider_config`、`llm`、`publication`、`identity`、`errors`、`kb_structure`、`simple_cli` | `src/knowledge_digest/` | K1–K3 活能力（`digest`/`accept` 闭包） |
| `_route_ledger_projection` | `compiler.py`（随 B2 删除） | 已核实：`kb_accept.py` **不读** `_audit/route-ledger.jsonl`（只读 `sources.jsonl`/`reference-blocks.jsonl`），唯一引用方是 `tests/acceptance/test_task5_compiler_formal_tree.py` 与 `test_task5_publication_contract.py`，随 B2 的测试处置一并删除；无需迁移 |

说明：detail-advice 指出"保留 `compiler.py` 内符号"与"不可达模块归零"互斥——结论是`compiler.py` 不能以"保留整个模块"的方式留下来；
必须先确认 K3 是否真的读取 `_route_ledger_projection`（若读取则迁移该函数到可达模块，若不读取则随模块删除）。

### D. 不在本期动（延期，带 owner）

9 个只在 `specs/archive/**` 出现的配置（DEF-K4-3）、7 个 mapping 修订版 + `task5-quality-cases-v1.json` +
`task9-comparison-mapping.v1.json` + `config/knowledge-digest.json`（DEF-K4-4，随 legacy 入口一起定）、
`apply/`（143 文件 / 3.16 MiB）、`specs/archive/**`、`docs/**`。

### E. 测试资产处置（对应 F-1a91017ec9f5）

| 类别 | 处置 | 例子 |
| --- | --- | --- |
| 只钉旧实现、删后无对应活行为 | **同步删除**（与代码同批） | `test_task5_projection.py`、`test_task5_provider.py`、`test_task5_m401_r_adapter.py`、`test_task3_quality_release.py`；`test_task5_publication_contract.py` 中仅 `_route_ledger_projection`/`_validate_route_ledger_projection` 相关用例 |
| 同时覆盖活行为的断言 | **迁移**到活实现（`semantic_*`/`kb_*`）后删除旧文件；`test_task5_publication_contract.py` 的参数拒绝用例**原地保留** | `test_task5_compiler_formal_tree.py`、`test_task5_contract.py`、`test_simple_digest.py` 中的活路径断言 |
| 因缺外部冻结 fixture 已红 | **保持 red 并登记延期**，不计入本任务失败 | `test_task2a_reader_bundle.py::test_validator_rejects_incomplete_claim_provenance`（DEF-K4-8） |
| 覆盖 K1–K3 活实现 | **保留并要求全绿** | `test_task7_*`、`test_task9_*`、`test_task8`、`test_publication_contract.py` 等 |

删除前必须按 DEF-K4-6 逐文件重读确认（清单来自 AST 体分析，不是实测运行）。

## 验收指标冻结（FR-K4-1 口径唯一解释）

| 指标 | 唯一口径 | 复算方式 |
| --- | --- | --- |
| 源码净下降 | 同一次复算同时输出**物理行**与**代码行**（非空非注释），两者都要净下降；基线＝`eee5549` | 复算脚本在基线与最终树各跑一次，输出并列对比 |
| 不可达模块归零 | 入口集合＝`pyproject [project.scripts]` 的 5 个脚本（legacy 脚本已按 D-005 退役，不计入根）；闭包用 AST import 图（含函数内 import）；**测试与其它未登记脚本不作根** | 同一脚本两次输出不可达模块清单，最终必须为空 |
| 零引用配置下降 | 引用范围＝`src/ scripts/ tests/ docs/ pyproject.toml` ＋ 顶层 `*.md` ＋ `config/` 内互引；基线清单＝76 文件全表 | 同一脚本两次输出零引用清单与字节数，最终必须下降 |
| 附加防刷分报告 | 模块数、函数数、测试收集数、删除/新增行数分解 | 随复算输出一并交付；数字变化需给出解释 |
| 指标冲突优先级 | 净下降优先于"补入口凑可达"；不得为达标新增连接代码（NG-011） | 由 build-plan 的批次顺序与 review 检查 |

## 阶段执行记录

| step | step_slug | 状态 | 真实结果 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | load-context | completed | 读取原始需求、母任务 PRD（确认 K1–K3 已完成、K4 为唯一剩余卡）、WorkflowHub make-decision workflow 与 skill-deps；用 `task-bootstrap.mjs` 创建确定性 worktree 与分支并读回；建立本文件、任务身份与唯一 OI 大纲（14 项，outline v1.0） | `decision-log.md` 任务身份 / OI 大纲；`git worktree list` |
| 2 | triage-scope | completed | 写入初步范围、6 项不确定性、10 条非目标草案、7 条风险草案；登记任务类型 `普通任务` | `decision-log.md` 范围 / 非目标 / 风险 |
| 3 | talk-round-1 | completed | 先完成事实核实（子代理取证，主会话只收结论），再向用户提出 7 个方向问题（含事实新引出的入口口径 Q7）；用户当轮要求先看事实后一次性答复，答复记入 step 5 | 本文件 `## Talk` Round 1 |
| 4 | research-inputs | completed | 4 份取证审计由子代理完成并落盘（可达性/配置/旧自证/S6 能力），主会话独立复核入口与调用链后汇总为结论层；新增 OI-15/OI-16，outline v1.0→v1.1；登记既有红灯 `test_task2a_reader_bundle` | `evidence/*.md`、本文件 `## 调研` |
| 5 | talk-round-2 | completed | 真实 ask→wait→reply→resume：提出 9 个互不依赖的大白话问题（每题含推荐、后果、风险），用户逐条答复「Q1 默认推荐 / Q2-A / Q3-A / Q4-A / Q5+Q7 默认 / Q8-A / Q9-A」；Q2→Q8、Q6→Q1 的合并映射已登记；16 项 OI 终态回填，新增 OI-15/OI-16 | 本文件 `## Talk` Round 2；OI 记录 |
| 6 | direction-advice | completed | 真实执行 paired review（red/blue 各一次 broker group request）：`semantic_status=available`、`partial=false`；red=`kimi/coding`+`antigravity/flash`+`codex/luna`，blue=`codex/luna`+`kimi/coding`+`antigravity/flash`，共 26 条 finding（首次两次调用因材料键与 host_provider 不合法被拒，如实保留为 unavailable attempt） | `quality/reviews/results/make-decision-simple-9388fae3-*.json`、`…-fdd80691-*.json` |
| 7 | talk-round-3 | completed | 以红蓝 finding 清单为争议列表逐条处置：`rejected_invalid` 5 条（4 条因材料快照早于 Round 2 答复、1 条因 OI 刻意分开不合并），其余 21 条 `fixed`；26 条 finding id 全部入表且各自唯一处置，并在同一轮补齐 `## 与母任务的关系`、`## 考虑过但未选的方向`、`## 删除与保留清单（file-level）`、`## 验收指标冻结`、NG-005 拆分、RISK-009…011、DEF-K4-9 | 本文件 `## Talk` Round 3 |
| 8 | grill-with-docs | completed | 3 个前沿问题真实 ask→wait→reply：G1 瘦身任务里加新功能是否跑偏（A）／G2 三项指标能否被刷分（A：同时报告代码行与物理行＋模块/函数/测试数）／G3 是否顺手补测试与修红灯（A：只补活实现缺口）；结论写入 D-002、FR-K4-1、FR-K4-2 与 NG-005b | 本文件 `## Talk` Grill |
| 9 | write-decision-draft | completed | 决策草稿成稿：原始需求、关键事实、D-001…D-004（含 rejected_alternatives 与 derived_from 链）、风险 11 条、非目标 13 条、延期 9 项、file-level 删除/保留清单、验收指标冻结；`check-decision-log-chain.mjs` 对本文件零 warning | 本文件全文；`node tools/cli/check-decision-log-chain.mjs` |
| 10 | detail-advice | completed | 真实执行 paired review，共 3 轮（第 1 轮 38 条 finding、第 2 轮 42 条、第 3 轮为修复后的末轮）：全部 `semantic_status=available`、`coverage=satisfied`；主会话逐条处置并当场修复 4 条 blocking（FR-K4-2 与先验后删死锁、legacy 入口 root 冲突、A 节计数、材料截断/空 context_map）与全部 major/minor；无未处置 finding | `quality/reviews/results/make-decision-simple-{c81e9e67,dea426b9,5a9c7901,…}.json` |
| 11 | approve-decision | completed | 向用户按主题分组展示 7 组选项（范围/验收口径/删除边界/分批恢复/老能力与老入口/延期/门禁顺序）及后果与风险，用户答复「确认，继续」；确认凭证 `quality/confirmations/e9b17e0e7190c0bcff9de8f6b7233788f063d8fcf0b53e42984ca02786353571.json`；就 D-005 范围收窄单独确认「A」 | 本文件 `## Talk` Round 2/4；`quality/confirmations/` |
| 11 | approve-decision | pending | — | — |
| 12 | stage-end-spec-analyze | pending | — | — |
| 13 | publish-decision | pending | — | — |
| 14 | stage-reflection | pending | — | — |
