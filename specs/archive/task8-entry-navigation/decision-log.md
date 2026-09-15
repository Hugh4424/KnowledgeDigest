# 决策记录 · task8-entry-navigation

> 本文件是 make-decision 阶段唯一权威材料。OI 大纲只存在于本文件内，不另建需求账本、状态机或第五份材料。
> 当前阶段状态：**approved**（step 1–13 全部完成：load-context、triage-scope、Talk Round 1、
> 调研取证、Talk Round 2、direction-advice（真实执行，`available-with-failures`，F-1…F-8 已处置）、
> Talk Round 3、grill、决策草稿、detail-advice 两轮（真实执行，首轮 12 条/次轮 6 条 finding 全部处置）、
> 用户最终确认、stage-end 自检、发布。审查结果均如实记录为 available-with-failures，非 pass）。
> 标题层级说明：`## 原始需求`、`## 核心需求`、`## 核心目标`、`## 已选方向`、`## 验收标准`、`## 范围`、
> `## 完整用户旅程`、`## UI applicability`、`## 收敛检查` 是运行时读取的固定小节名，保持不带编号。

## 任务身份

| 项 | 值 |
| --- | --- |
| project | KnowledgeDigest |
| task_id | `task8-entry-navigation` |
| stage | make-decision |
| worktree | `/Users/Hugh/Hugh/Project/KnowledgeDigest-task8-entry-navigation` |
| branch | `task/KnowledgeDigest/task8-entry-navigation` |
| baseline_commit | `c5fb2b5d4dde7b00afdfe668303c31b032477d29` |
| task_path | `/Users/Hugh/Hugh/Knowledge/Projects/KnowledgeDigest/tasks/task8-entry-navigation` |
| created_at | 2026-09-13 |

- **任务类型**：普通任务（继承 K1 约定：允许追问实现细节，当细节答案会改变实现时即提问）。

**范围声明（triage-scope 初步，待 Talk Round 1 用户确认）**：本任务范围 = 母任务 PRD
（`specs/archive/task6-effect-gap-and-architecture-reset/prd.md`）中的 **K2 一张卡**（入口与导航），
不含 K1 语义层页面编译、K3 发布通道与查询集验收、K4 瘦身删码。
母任务与其兄弟任务材料对本任务只读；本任务自建 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 四份材料。

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 状态/处置 | 关联 OI |
| --- | --- | --- | --- | --- |
| R-001 | 按标准 WorkflowHub 从 make-decision 开始本任务，先创建 worktree | 用户原话 2026-09-13「先创建worktree，然后从 make-decision 开始」 | covered | 阶段执行记录 |
| R-002 | 不跳阶段 | 用户原话 2026-09-13「不要跳阶段」 | covered | 阶段执行记录 |
| R-003 | 不依赖 build-spec 补需求；先基于原始需求在 make-decision 内把需求梳理完整 | 用户原话 2026-09-13「不要依赖 build-spec 补需求」 | covered | 六类边界在本阶段收敛 |
| R-004 | 在 make-decision 过程中共同梳理六类边界 | 用户原话 2026-09-13「仔细梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项」 | covered | OI 大纲 Fixed categories 六类全覆盖 |
| R-005 | 注意主会话上下文控制与子代理派发 | 用户原话 2026-09-13 | covered | NG-002；`## 调研`（子代理失败改主会话直读，如实记录） |
| R-006 | Talk 与 grill 用大白话说明选项、后果和风险 | 用户原话 2026-09-13 | covered | `## Talk` 卡片格式 |
| R-007 | 任务范围 = 母任务 PRD 的 K2 卡 | 用户原话「我准备开始其中第 2个任务了」 | covered | Talk R1 Q0；OI-01 |
| R-008 | K2 结果 = 入口页 + 分类入口把每个已发布页接进入口；从入口可达每一页且入口描述对页面有区分度 | 母任务 PRD K2「结果」 | covered | OI-02, OI-03, OI-07 |
| R-009 | K2 的 3 条 FR/AC（FR-K2-1 入口可达性 / FR-K2-2 入口区分度 / FR-K2-3 读者路径） | 母任务 PRD K2 表 | covered | OI-07, OI-08, OI-09；AC-K2-1…3 |
| R-010 | K2 scope：页面类型映射、入口/分类生成、孤儿页与同质入口判失败；不改编译（K1）、不改发布（K3） | 母任务 PRD K2「scope」 | covered（detail D-M1 补声明：K2 语境"页面类型映射"=frontmatter product/section 两层挂载（OI-04），无第三分类维度；原 PRD 措辞的"页面类型"在本卡即挂载规则本身） | OI-03, OI-04, OI-10 |
| R-011 | K2 用户流程与状态转换：接收 K1 页面清单 → 生成入口/分类 → 入口图自检（孤儿/同质）→ 修循环 → 达标待发布 | 母任务 PRD K2「用户流程与状态转换」 | covered | OI-01, OI-02；`## 完整用户旅程` J1–J11 |
| R-012 | 对照基线：87/99 无入口、95/99 同质（F-001 导航实测） | 母任务 PRD K2「结果」与「来源与设计引用」 | covered | OI-08；RISK-K2-1 |
| R-013 | local risk：入口描述交由模型生成导致同质 → AC-K2-2 阈值压制 | 母任务 PRD K2「来源与设计引用」 | covered | OI-08；RISK-K2-1 |
| R-014 | 实现依赖 = K1 页面清单；验收依赖 = K1 页面清单 + 入口图检查器（本卡自建） | 母任务 PRD K2「依赖」 | covered | OI-01；OPEN-K2-3 |
| R-015 | S1 语义层契约：与 CompanyBrain 同构（frontmatter、目录与命名、wikilink 双链） | 母任务 PRD S1；K1 spec FR-PUB-001 已冻结 16 字段 | covered | OI-03；D-010 |
| R-016 | S3 数据状态词表：ready / known_empty / duplicate_alias / audit_only / 资料未明确 | 母任务 PRD S3；K1 spec FR-AUD-003 已冻结判定规则 | covered | OI-05 |
| R-017 | OPEN-001 页面清单由 K1/K2 的 build-spec 冻结；K2 的 N 条真实查询路径由 build-spec 冻结 | 母任务 PRD 第 4 节 | covered | OI-07, OI-11；DEF-K2-1/2/5 |

**未覆盖/待定**：无。R-001…R-017 全部落到 OI、D 条目、AC、非目标或延期项。

### 用户原话（逐字，未改写）

> 「请检查"/Users/Hugh/Hugh/Project/KnowledgeDigest/specs/archive/task6-effect-gap-and-architecture-reset/prd.md"，其中的K1任务已经设计完成准备开始研发了，同时我准备开始其中第 2个任务了。
> 我希望现在按标准 WorkflowHub 开始这个任务，先创建worktree，然后从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。先基于原始需求，在make-decision的过程中和我一起仔细梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。注意主会话上下文控制和子代理派发。Talk 和grill请用大白话说明选项、后果和风险」
>
> 补充材料指引（逐字）：「第一个任务的设计文档：/Users/Hugh/Hugh/Project/KnowledgeDigest-task7-semantic-layer-compiler/specs/task7-semantic-layer-compiler」
>
> 确认环节用户原话（逐字）：「请确认当前stage所有工作都完成了，仔细检查make-decision的要求，看看是否有遗漏」

## 阶段执行记录

- step 1 load-context：读母任务 PRD（archive/task6-effect-gap-and-architecture-reset/prd.md）K2 卡与共享定义 S1/S3/S8；
  读 K1 设计材料的接口事实（spec.md FR-PUB-001/002、FR-AUD-003/004、关键实体、兼容性预留、明确不做）；
  读 CompanyBrain 现有入口结构（Home.md tier 1 + 分类索引 + wikilink 双链）。主会话只读接口章节，大块材料不整卷吞入（R-005）。
- step 2 triage-scope：创建 worktree `/Users/Hugh/Hugh/Project/KnowledgeDigest-task8-entry-navigation`（分支
  `task/KnowledgeDigest/task8-entry-navigation`，baseline `c5fb2b5`）；初始化本决策日志；范围初步定为 K2 一张卡，待 Talk R1 用户确认。
- step 3 Talk Round 1：Q0–Q10 十项用户真实答复（范围/运行形态/入口位置/入口形态/分类维度/描述生成/阻塞口径/查询路径/自检处置/非目标/延期），见 `## Talk`。
- step 4 调研取证：CompanyBrain 产品索引页结构 + K1 接口事实（主会话直读，量小），见 `## 调研`。
- step 5 Talk Round 2：R2-Q1–R2-Q7 七项用户真实答复（三层结构/描述对象/查询建议/总览页位置/命名/结构组合/模块中文名），见 `## Talk`。
- step 6 direction-advice：**真实执行，`available-with-failures`（不是 pass）**；red/blue 六角色全部 completed；
  8 个实质 finding（2 blocking）逐条处置：F-1/F-3/F-4/F-5/F-6 本阶段修复、F-7 复议维持、F-8 登记 detail 材料义务、
  F-2 进 Talk Round 3；调用事实与处置见 `## 审查处置`。首次曾误判 executor_absent（查找遗漏 workflowhub 主安装），
  经用户指正修正并如实记录。
- step 7 Talk Round 3：Q-R3-1 用户裁决 F-2 = 「口径+默认值在本阶段冻结」：判据①规范化精确相等容忍 0、
  判据②句式骨架 ≥3 句、N=10 默认（题目用户确认后冻结）；DEF-K2-1 关闭、DEF-K2-2 部分关闭。见 `## Talk`。
- step 8 grill-with-docs：两个 accepted ADR + 术语 + 替代路径压力测试，见 `## grill`。
- step 9 决策草稿：D-001…D-012 + AC-K2-1…AC-K2-7 + 非目标/风险/延期/未决，见各固定小节。
- step 10 detail-advice：**两轮真实执行**（首轮因材料拼接缺陷修复后重跑），均 `available-with-failures`，
  findings 全部处置，见 `## 审查处置`。
- step 11 用户最终确认：**approved**（用户原话「确认，进入 stage-end 与发布（推荐）」）。
- step 12 stage-end-spec-analyze：无外部宿主，官方 outcome 记 `unavailable`；主会话结构自检 7 项全 PASS（见 `## 最终确认`）。
- step 13 publish-decision：本记录为 make-decision 唯一权威材料，发布。

## Talk

### Talk Round 1（2026-09-13）· 用途：核实 K1 接口事实与 CompanyBrain 入口事实，收敛 K2 的方向、边界与落地形态

| # | 问题 | 选项与后果（大白话） | 用户选择 |
| --- | --- | --- | --- |
| Q0 | 「第 2 个任务」是否就是 PRD 的 K2 卡 | A 是 K2 入口与导航（范围=入口+分类+孤儿/同质判失败）｜B 不是 | **A：是，就是 K2 入口与导航** |
| Q1 | 导航什么时候生成 | 同跑：一次 digest 全出，但 K1/K2 耦合、字节比对范围与半成品风险面扩大｜独立步骤：边界干净但多一步｜同跑+可单独重跑：省事但两条代码路径 | **同跑：跟 K1 同一次跑** |
| Q2 | 入口页写到哪 | 批次目录：自包含，但会有第二套入口结构，K3 需决定与 CompanyBrain 现有 Home.md 的合并/取代关系｜别处：不自包含、写权边界重划 | **写进批次目录** |
| Q3 | 入口形态 | 新增 Home.md 仿 CompanyBrain：体验一致，但与 README.md（批次说明）并存需分清职责｜README 升级成入口：单入口但冲击 K1 字节比对约束｜别的形态：偏离同构 | **新增 Home.md 仿 CompanyBrain** |
| Q4 | 分类维度 | product/section 两层：与路径天然对齐、机械可复算｜type/tags 等：更贴查法但需另造口径｜混合：信息多但规则复杂 | **按 frontmatter 的 product/section 两层** |
| Q5 | 描述生成 | 模型写+两两不重复硬校验：正对 95/99 同质基线，但要配超阈值显式失败/退化｜纯模板：零成本但可能名义达标实际没用｜模型+人工审：与全自动矛盾 | **模型写描述 + 两两不重复硬校验** |
| Q6 | 阻塞批次导航 | 只覆盖成功页+Home.md 显式标注：与 K1 部分成功口径一致｜有阻塞整批不生成：最保守但口径打架、可用性差 | **只覆盖成功页 + Home.md 显式标注** |
| Q7 | 查询路径来源 | K2 自定 N 条：不依赖 K3，风险是自出题放水（缓解：从真实查法选）｜等 K3：题目最真但 K2 被卡｜留 build-spec：方向问题不能留 | **K2 自己定 N 条典型查询路径** |
| Q8 | 自检失败处置 | 显式 blocked：孤儿=代码 bug 应报根因｜机器自动修：可能挂错且掩盖 bug | **显式失败 blocked，不产出导航** |
| Q9 | 非目标 | K2 只造入口/分类/自检，六条不做事项见 `## 非目标` | **确认** |
| Q10 | 延期项 | ①页面清单细节 ②同质阈值数值 ③N 条路径清单 ④与 CB 现有 Home.md 合并关系，均登记 `## 风险与延期交接` | **确认** |

Talk Round 1 关闭：Q0–Q10 共 10 项用户真实答复；K2 方向、入口形态、分类维度、描述生成、阻塞口径、查询路径、自检处置、非目标、延期项全部收敛。

## 调研

### 取证（主会话上下文控制，R-005）

- 取证零（派发失败如实记录）：首次按 R-005 派子代理提取 K1 四材料交接事实，**子代理在返回前失败、未留任何信息**；
  主会话不静默重试同一路径，改为按量分流——两块小体量取证（CB 索引页、K1 spec 接口章节）由主会话直读，
  大块材料仍不进主会话。失败事实记录于此，不伪装成"子代理已完成"。
- 取证一：CompanyBrain 产品索引页结构（主会话直接读，量小）：frontmatter（tier 1、page_model derived）+ 一段导语 +「优先入口」wikilink 列表 +「按能力查」文字分组 + 各产品子入口。多层结构为 Home.md → 分类索引 → 产品/文档总览 → 页面。
- 取证二：K1 接口事实（主会话读 K1 spec 接口章节）：page-manifest.json 含页面条目、来源台账、阻塞项、run_status/publish_status；frontmatter 16 字段冻结；批次目录 = README.md + products/ + _audit/ 五件；K1 明确不留入口（NG-003，本卡范围）。

### 调研结论对方向的影响

CompanyBrain 的「文档总览」模式与用户 R2-Q1 自定义答案一致：三层导航（Home → 知识索引 → 模块总览 → 页面）有成熟参照，不需要另造结构。

## Talk

### Talk Round 2（2026-09-13）· 用途：核实事实到位后，收敛实现层决策

| # | 问题 | 选项与后果（大白话） | 用户选择 |
| --- | --- | --- | --- |
| R2-Q1 | 导航层级 | 两层：2 跳到页面但索引会很长｜三层：仿 CB 但 3 跳压线｜一层：Home 膨胀 | **三层（用户自定义细化）：Home → 全局知识索引（不只是产品索引，是整个知识的索引，预留各种类型模块）→ 每个模块的总览索引页 → 页面。跳数=点击次数，Home→索引→总览→页面=3 跳，压线满足 FR-K2-3** |
| R2-Q2 | 描述对象 | 每页面一条描述句｜页面+节双描述｜整页描述 | **每个页面一条描述句** |
| R2-Q3 | 查询建议 | 模型写｜静态模板｜不要 | **要，模型写** |
| R2-Q4 | 总览页位置 | 单独 navigation/ 目录：与 K1 产物分离干净｜放进 products/ 模块目录：同目录可见但混入 K1 产物｜产品目录下：命名可能冲突 | **放进 products/ 模块目录里** |
| R2-Q5 | 索引页命名 | Index.md/navigation/<模块>.md：通用不绑定「产品」｜中文名：直观但 slug 不确定｜产品索引.md：用户已排除 | **Index.md / navigation/<模块>.md** |
| R2-Q6 | 三层结构组合 | 确认：Home.md（入口+批次标注+查询建议）→ Index.md（全局知识索引，按产品分节列模块总览）→ products/<产品>/<模块>/Index.md（模块总览：全页面+每页描述句）→ 页面 | **确认这个组合** |
| R2-Q7 | 模块中文名 | 从模块页面 title 机械推断：零模型调用、确定性可复算｜模型起：准但要缓存冻结｜现在不定：YAGNI | **从该模块页面 title 机械推断** |

Talk Round 2 关闭：R2-Q1–R2-Q7 共 7 项用户真实答复（含 1 项自定义细化）；三层结构、描述对象、查询建议、总览页位置、命名、模块中文名全部收敛。

### Talk Round 3（step 7，2026-09-13）· 用途：处理 direction-advice 的 blocking finding 与剩余风险

| # | 问题 | 选项与后果（大白话） | 用户选择 |
| --- | --- | --- | --- |
| Q-R3-1 | 同质阈值与 N 条路径归谁冻结（direction F-2，blocking） | B 冻结口径+默认值：当场可判、不依赖下游；风险=默认值可能需调（调要走阶段回滚）｜A 当场定死数值：最硬但描述未跑过可能大量撞车｜C 维持归 build-spec：最省事但留了"靠下游补"的口子 | **B：冻结口径+默认值** |

Talk Round 3 关闭：F-2 裁决为「口径+默认值在本阶段冻结」：
- **判据口径①**：描述句规范化（去首尾空白、全半角归一、去标点、小写）后**精确相等即判重复**；重复数容忍 = **0**（FR-K2-2「两两不重复」的直接机器化）。
- **判据口径②（模板化）**：描述句去掉实体词后的**句式骨架重复 ≥3 句**即判模板化成片（正对基线 95/99 的"模板句"形态）。
- **N 默认值 = 10 条**：题目从用户真实查法选取，**用户确认后冻结**；build-spec 只能引用执行、不得改动；
  若实现中确需调整，必须回到 make-decision 修订（不消耗新方向，只修订数值）。
- 以上取代 PRD 卡上「build-spec 冻结阈值/N」的措辞（PRD 措辞与"不依赖 build-spec 补需求"的冲突以本裁决为准）。

## 核心需求

1. **入口可达性（FR-K2-1）**：量化域=page-manifest 中 run_status=complete 批次的全部页面条目（发布前集合；发布归 K3）至少被一个入口/分类页链接可达；任一孤儿页=失败。
2. **入口区分度（FR-K2-2）**：入口描述两两不重复且非模板化问句；判据口径与默认值由 make-decision 冻结（Talk R3，对照基线 95/99 同质）；任一命中=失败。
3. **读者路径（FR-K2-3）**：N=10 条真实查询路径（默认值 Talk R3 冻结；题目从用户真实查法选取、用户确认后冻结清单）全部 ≤3 跳；任一路径超 3 跳=失败。

## 核心目标

把读者导航从基线 **87/99 无入口、95/99 同质模板** 做到：**零孤儿、描述两两不同质、典型查询 3 跳内到达**——
且全部由机器自检判定，不靠人翻页抽查。导航结构是"结构门"，不是知识可用性的最终证据（那是 K3 的真实查询集，ADR 0014）。

## 已选方向

- **运行形态**：与 K1 同一次 `digest` 运行产出；导航文件写进批次目录（Q1/Q2）。
- **三层结构**：`Home.md`（批次入口：批次状态显式标注 + 快速入口 + 模型写的查询建议）→ `Index.md`
  （全局知识索引：通用命名不绑定"产品"，按 product 分节列模块总览链接）→ `products/<产品>/<模块>/Index.md`
  （模块总览：该模块全部页面列表 + 每页一条模型写的描述句）→ K1 页面。跳数=点击次数，
  Home→Index→模块 Index→页面 = 3 跳，压线满足 FR-K2-3（R2-Q1 用户自定义细化 + R2-Q6 确认）。
- **分类维度**：frontmatter 的 product/section 两层（Q4）；模块总览页放进 products/ 模块目录内、命名 Index.md（R2-Q4/R2-Q5）。
- **描述生成**：模型写描述句 + 两两不重复硬校验，超阈值显式 blocked（Q5/Q8）；复用 K1 模型缓存机制保
  同输入同输出；模块中文名从模块页面 title 机械推断（R2-Q7），不花模型调用。
- **阻塞口径**：K1 部分成功批次 → 导航只覆盖成功页，Home.md 显式标注成功/阻塞计数（Q6）；
  K2 自检失败（孤儿/同质/跳数）→ 显式 blocked，不产出导航（Q8）。
- **查询路径**：K2 自定 N 条典型查询路径（N=10 默认已冻结；题目从用户真实查法选取、**用户确认后冻结清单**，
  不依赖 K3（Q7））；build-spec 只能引用执行，不得改动（Talk R3）。
- **同构**：导航页 frontmatter 服从层契约（S1）；Home/Index 为 tier 1，模块 Index 为 tier 2，均
  `page_model=derived` + `generated_by`（生成器命名归 build-plan）。

## 验收标准

| AC | 判据（含失败判据） | oracle |
| --- | --- | --- |
| AC-K2-1 零孤儿 | **量化域（direction F-1 钉死）**：page-manifest.json 中 run_status=complete 批次的全部页面条目（发布前集合；PRD 措辞"已发布页"在本卡指该集合——K1 恒 not_released，发布归 K3）。入口图遍历（**覆盖判定**：①页面条目集合 ⊆ 可达集合 ②链接目标存在 ③可达页面 ⊆ 页面条目；detail R2-B1 修正，不用数量等式）；任一违例=失败。**衔接**：K3 发布时以该集合的可达性为前置，K2 图检查失败的批次 K3 不得放行（读 navigation_status，见 AC-K2-5） | 入口图遍历脚本 |
| AC-K2-2 描述区分度 | 判据口径（Talk R3 冻结，取代"build-spec 冻结"）：①描述句规范化（去首尾空白/全半角归一/去标点/小写）后精确相等即重复，容忍=0；②句式骨架重复 ≥3 句即模板化成片——骨架最小算法（detail D-E1 冻结）：描述句移除该页 title 文本与 product/section 词、去标点小写后的剩余字符串；③疑问句式模板（"如何/什么是/怎么…？"骨架 ≥3 句，detail R2-B2 补，正对"非模板化问句"原文）；**判据④：任一描述句为空/空白即失败**（detail R2-B3：空描述不容忍、不豁免——模型不可用/部分页面空输出/全空统一 blocked 不产出导航，失败不伪装成功）；任一命中=失败 | 描述唯一性检查脚本 |
| AC-K2-3 查询路径 | N=10 条（Talk R3 默认值；题目从用户真实查法选取、用户确认后冻结）；逐条实测点击数 ≤3（Home→Index→模块 Index→页面）；任一路径 >3 跳=失败 | 路径测量脚本 |
| AC-K2-4 结构齐备 | 三层文件齐备：Home.md（含批次状态标注行、快速入口、**查询建议 ≥3 条且非空**（detail R2-B4 补 oracle，用户 R2-Q3 选择的模型产物必须有验收钩））、Index.md、每个含页面的模块目录均有 Index.md；frontmatter 字段集合与取值引用 K1 spec FR-PUB-001 表（16 字段），tier 按层取值（Home/Index=1、模块 Index=2），generated_by 值归 build-plan 命名（DEF-K2-4，**确认前 AC-K2-4 此子项 incomplete**，detail R2-B5 诚实标注）；缺件或字段不符=失败 | 结构校验脚本 |
| AC-K2-5 阻塞显式化与机读状态 | ①部分成功批次 Home.md 批次状态行显式标注成功页数与阻塞来源数，**计数字段契约（detail R2-B6 冻结）**：manifest 增写 `navigation` 节 `{success_pages: int, blocked_sources: int, navigation_status: generated_ok|blocked, blocked_reasons: [...]}`，计数公式=success_pages == 页面条目数、blocked_sources == K1 阻塞清单长度；Home.md 状态行展示值与 manifest 对账一致；②**不产出导航的情形全集**：K1 run_status=blocked/interrupted、K2 自检失败（两道门/路径抽查）、模型产物任一失败（描述或查询建议生成失败/空输出）、**run_status=complete 且零页面**——此时 **K1 run_status 不动**，manifest `navigation_status=blocked` + 阻塞项"零页面批次，无可导航对象"（detail R2-B7 修正：K2 不得改写 K1 冻结状态，OI-12 隔离字段）；③未标注、字段缺失或对账不符=失败 | 状态字段机器校验 |
| AC-K2-6 可重复 | 同输入连跑两次，全部导航文件字节一致（**模型产物全部走缓存：描述句 + Home 查询建议**（detail D-G1 扩 D-009）、模块中文名机械推断、时间戳不进导航文件）；任一导航文件抖动=失败 | 双跑字节比对 |
| AC-K2-7 写权边界 | 批次目录外零写入（CompanyBrain/gbrain/停摆流水线零触碰）；任一越界写=失败 | 写路径审计 |

## 范围

只做：批次目录内导航文件的生成（Home.md / Index.md / 模块 Index.md）+ 入口图自检 + 与 K1 运行同批产出。
输入：K1 产物（`page-manifest.json` 页面清单 + `products/` 页面 + frontmatter）。
不做：K1 编译的任何环节、发布通道、真实查询集验收、删码（见 `## 非目标`）。

### 数据状态与导航的映射（六类边界之三：数据状态，逐类梳理）

K2 不新造状态词表，全部消费 K1 已冻结的状态（FR-AUD-003/004）；映射关系逐类固定如下：

| 状态（K1 词表） | 层级 | K1 产物中的表现 | K2 的处置 |
| --- | --- | --- | --- |
| `ready` | 来源级 | 来源产生页面，进 page-manifest 页面条目 | **进导航**：页面被三层结构覆盖（AC-K2-1 的对象） |
| `known_empty` | 来源级 | 来源读得到但拆不出内容，无页面 | 无页面故不进导航；其存在由 K1 来源台账记录，K2 不展示 |
| `duplicate_alias` | 来源级 | 指纹重复，无新页面；别名登记 `alias_of` 指向 canonical | 无页面故不进导航；读者经 canonical 页面到达（K1 已保证内容承载在 canonical 页） |
| `audit_only` | 来源级 | 块零进 `products/`，无页面 | 无页面故不进导航 |
| `资料未明确`（运行内值「原文未明确」） | claim 级 | claim 无原文依据，显式标注，不进事实分母 | **不影响导航范围**（claim 不改变页面是否存在）；K2 不在导航中重复展示该状态——它是 K1 审计面的事 |
| `run_status=complete` | 批次级（K1 manifest） | 本批运行完成（可含阻塞项） | 导航正常产出；若有阻塞来源，Home.md 显式标注成功页数/阻塞来源数（Q6） |
| `run_status=blocked` | 批次级 | 对账失败等，页面条目可能为空 | **不产出导航**（无完整页面集可导） |
| `run_status=interrupted` | 批次级 | 写入中断，manifest 缺失/无效 | **不产出导航**（半成品状态不给读者入口） |
| `run_status=complete` 且零页面 | 批次级 | 全部来源无页面（极端情形：语料整体空/重复/审计态） | **不产出导航；K1 run_status 保持 complete 不动**，manifest `navigation_status=blocked` + 阻塞项"零页面批次，无可导航对象"（detail R2-B7：两道门无对象不可判，不能空跑通过；K2 不改写 K1 冻结状态，隔离字段归属 OI-12） |

### S8 消费口径（K2 最小读取集 required 项的处置）

K2 消费 S8（对照判定规则）的口径固定为：**仅借鉴其"逐题测量、汇总条件可执行"的方法论**做 N 条路径的
跳数测量（AC-K2-3）；不做四结果判定、不做"对照未覆盖"登记、不与冻结 CB 快照比对——那些是 K3 的
查询集验收（NG-005）。K2 的 N 条路径是**导航结构测量题**，测的是"入口到目标页几步"，不是"答案对不对"。

### 与既有入口的关系（direction F-5 显式定调）

CompanyBrain 现有四层链（Home → 分类索引 → 产品总览 → 页面）已占满 3 跳预算。K2 的取舍显式定调为
**并行自营**：批次目录内自建三层导航，不改写 CB 现有 Home/索引/tier-1 文件（写权边界不变）；
3 跳测量边界 = 批次内 Home 起算（不与 CB 四层链混测）。两套入口的合并/取代由 K3 发布时决定
（DEF-K2-3）——K3 若把 K1/K2 产物并入语义层，需同时解决"CB 现有入口 vs KD 新入口"的唯一生产者问题。
此张力已在 F-5 处置中登记，方向不变。

### 页面进导航的判定链

```
page-manifest.json 页面条目（run_status=complete 批次内）
  └─ 每条页面 → 取其 frontmatter 的 product / section
       └─ product → Index.md 的分节
       └─ section → products/<product>/<section>/Index.md 的条目（title + slug 链接 + 描述句）
  └─ 遍历核对（覆盖判定，detail R2-B1 修正：不用数量等式——遍历集合含 Home/Index 等
     导航节点，数量恒大于页面数，等式必失败）：
       ① 页面条目集合 ⊆ 遍历可达集合（每一页至少一条入口路径可达；任一不可达=孤儿，blocked）
       ② 遍历中每一条链接的目标存在（死链=blocked）
       ③ 遍历可达的页面节点 ⊆ 页面条目集合（导航不得指向 manifest 之外的页面，错链=blocked）
```

## 完整用户旅程

角色：**投料人**（跑 `digest`）、**读者**（Obsidian 里查产品知识）、**下游消费者**（按路径/slug 检索）、**维护者**。

| # | 阶段 | 谁做 | 发生什么 | 成功的样子 | 失败/中断的样子 |
| --- | --- | --- | --- | --- | --- |
| J1-J6 | 投料→编译 | 用户/系统 | K1 范围：语料对账、拆块、归组、编译、页面校验、写批次目录 | 同 K1（本卡不动） | 同 K1：blocked 批次 manifest 显式标记 |
| J7 | 导航生成 | 系统 | 读 page-manifest → 机械建三层结构 → 模型写描述句（走缓存）→ 写 Home.md/Index.md/模块 Index.md | 三层文件齐备；描述句全量生成；时间戳/批次名不进导航文件 | 模型不可用且无缓存、或模型可用但任一描述/查询建议输出为空：**产物生成失败，运行 blocked 不产出导航**（判据④，detail R2-B3——空描述不容忍不豁免，失败不伪装成功） |
| J8 | 导航自检 | 系统 | 两道门遍历（孤儿/同质）+ N 条路径跳数抽查 | 全绿，导航随批次同批保留 | 任一红：**修复循环轮数=0**（K2 不修——孤儿=生成代码 bug，静默修复掩盖根因，用户 Q8 已裁决）；终止处置=运行判 blocked、导航文件不产出、阻塞项进 manifest、人工修输入/代码后重跑 |
| J9 | 阅读 | 读者 | Home.md → Index.md（按产品分节）→ 模块 Index.md（看描述选页）→ 页面 | 3 跳内到达目标页；描述句帮读者分清该进哪页 | 死链=AC-K2-1 失败（链接目标存在性已并入遍历 oracle，detail D-L1）；「描述张冠李戴」不属 K2 机器判失败范围（结构门≠内容正确性），登记为 K3 查询集验收/人工阅读面的检查项 |
| J10 | 复跑 | 用户/系统 | 同输入再跑一次 | 导航字节一致 | 抖动：判失败 |
| J11 | 交付 | 系统 | 批次目录（含导航）以 not_released 交 K3 发布通道 | manifest 机读状态完整 | 无 |

**关键不变量**：结构门≠知识可用性（K2 的门只保证"找得到、分得清"，不保证"答得对"——那是 K3）；
不碰 K1 页面一个块/一条 claim；批次外零写入；同输入同输出。

## UI applicability

```json
{
  "result": "non_ui",
  "sources": {
    "raw_requirement": {"applicability": "non_ui", "fact": "K2 产物是批次目录内的 Markdown 导航文件，由 Obsidian 类编辑器打开；无浏览器界面、路由或交互组件"},
    "project_inventory": {"applicability": "non_ui", "fact": "KnowledgeDigest 是 Python CLI 工具；同 K1 已判定"},
    "planned_or_changed_frontend_fact": {"applicability": "non_ui", "fact": "本任务不新增或修改任何前端或界面实现"}
  },
  "reason": "三项来源一致为 non_ui：CLI + Markdown 产物"
}
```

## 收敛检查

| 维度 | 用户答案 | 事实/材料引用 | 可执行验收 |
| --- | --- | --- | --- |
| 目标 | Q0/Q5/Q7/Q8/R2-Q3：入口可达、描述不同质、3 跳、结构门定位 | PRD K2 结果与 FR-K2-1..3；基线 87/99、95/99 | AC-K2-1..AC-K2-3 全部满足；把结构门当可用性证据（失败） |
| 范围 | Q0/Q9/R2-Q1：K2 一张卡；三层结构；只写批次目录 | PRD K2 scope；Talk R1/R2 全部答复 | 产物目录内不出现 K1 编译改动/发布通道/查询集验收产物（通过）；越界（失败） |
| 方案 | Q1-Q4/R2-Q1-R2-Q7：同跑、批次目录、Home 仿 CB、product/section 两层、三层结构、Index.md 命名、title 推断模块名 | `## 已选方向` | 三层文件齐备（通过）；描述两两不重复（通过）；出现未登记的悬空决定（失败） |
| 验收 | Q5-Q8/R2-Q2：硬校验阈值压制、阻塞显式、blocked 不产导航、自查 N 路径 | `## 验收标准` AC-K2-1..AC-K2-7 | 场景：读者从 Home 按描述选页 3 跳内到达；通过=AC 全绿；失败=任一条 AC 失败判据命中或把 DEF 写成已完成 |

## OI 大纲（唯一当前版本 · outline_version = v1）

> 身份绑定：全部 OI 绑定 `task_id = task8-entry-navigation`、`outline_version = v1`。
> 状态取值只用 `open` / `confirmed` / `deferred` / `not_applicable`；本版全部收敛项均为 `confirmed`（无延期 OI，延期走 DEF 台账）。
> 文本含引号处一律用 YAML 字面块标量，避免解析失败（K1 P-1 教训）；不用「未知/缺失/待定」等占位关键词（K1 P-3 教训）。

### Framework nodes

| node_id | framework_node | oi_ids | empty | reason |
| --- | --- | --- | --- | --- |
| N-background | background | OI-05, OI-06 | false |  |
| N-problem | problem | OI-09 | false |  |
| N-goal | goal | OI-07 | false |  |
| N-solution | solution | OI-01, OI-02, OI-03, OI-04, OI-08, OI-12 | false |  |
| N-acceptance | acceptance | OI-07, OI-08, OI-09 | false | OI-07/08/09 同时属固定类别 success_failure_boundary（两维度交叉） |

### Fixed categories

| category | oi_ids | empty | reason |
| --- | --- | --- | --- |
| complete_user_flow | OI-01, OI-02, OI-12 | false |  |
| page_scope | OI-03, OI-04 | false |  |
| data_state | OI-05, OI-06 | false |  |
| success_failure_boundary | OI-07, OI-08, OI-09 | false |  |
| non_goals | OI-10 | false |  |
| deferred | OI-11 | false | 延期走 DEF 台账，OI-11 仅登记确认动作本身 |

### OI 记录（每项一个可独立处置的收敛项 · 全部 confirmed）

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-01
category: complete_user_flow
source: "R-001/R-002/R-011 · Talk R1 Q1/Q2"
question: |2-
  K2 的导航在什么时机、以什么运行形态产出，写到哪个目录？
status: confirmed
selected_disposition: |2-
  用户选择：与 K1 同一次 digest 运行产出；导航文件写进本次批次目录（与 K1 产物同批、随批次交付 K3）
evidence: |2-
  decision-log.md#Talk R1 Q1/Q2；K1 spec FR-PUB-002 批次目录契约
acceptance: |2-
  一次 digest 运行结束后批次目录内同时存在 K1 产物与三层导航文件；导航生成不单独成命令
counterexample: |2-
  若导航需要第二次独立命令才产出，或写到了批次目录之外，即判该决定未落实
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G2-运行形态"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-02
category: complete_user_flow
source: "R-008/R-011 · Talk R2 R2-Q1/R2-Q6"
question: |2-
  读者从批次入口到目标页面的完整路径是什么形态，几跳内到达？
status: confirmed
selected_disposition: |2-
  用户选择（自定义细化）：三层结构 Home.md → Index.md（全局知识索引，通用命名不绑定产品）
  → products/<产品>/<模块>/Index.md（模块总览）→ 页面；跳数=点击次数，上限 3 跳
evidence: |2-
  decision-log.md#Talk R2 R2-Q1（自定义答案）/R2-Q6（组合确认）；CompanyBrain 索引结构取证
acceptance: |2-
  Home→Index→模块 Index→页面 = 3 跳压线；冻结的 N 条查询路径逐条实测 ≤3（AC-K2-3）
counterexample: |2-
  若任一路径需点击 4 次及以上，或出现无入口可达的页面，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R2-G1-三层结构"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-03
category: page_scope
source: "R-008/R-010/R-015 · Talk R1 Q3/Q4 · Talk R2 R2-Q4/Q5/Q6"
question: |2-
  K2 自己产出哪些文件、什么命名、frontmatter 服从什么契约？
status: confirmed
selected_disposition: |2-
  三层四件套：Home.md（入口+批次标注+查询建议）、Index.md（全局知识索引）、
  每模块 products/<产品>/<模块>/Index.md（模块总览）；命名一律英文 Index.md 不绑定产品字眼；
  frontmatter 服从层契约 16 字段，Home/Index 为 tier 1、模块 Index 为 tier 2，page_model=derived + generated_by
evidence: |2-
  decision-log.md#Talk R1 Q3/Q4；Talk R2 R2-Q4/R2-Q5/R2-Q6；K1 spec FR-PUB-001；S1
acceptance: |2-
  三层文件齐备且命名合规（AC-K2-4）；frontmatter 校验通过；批次目录外零写入（AC-K2-7）
counterexample: |2-
  若出现中文文件名、缺任一层文件、或导航页 frontmatter 脱离 16 字段契约，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R2-G2-命名与契约"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-04
category: page_scope
source: "R-008/R-014 · Talk R1 Q4/Q6"
question: |2-
  哪些 K1 页面进导航、按什么分组规则挂载、量化域是什么？（direction F-1 后补量化域：run_status=complete 批次的全部页面条目）
status: confirmed
selected_disposition: |2-
  run_status=complete 批次内全部页面条目进导航；按 frontmatter product/section 两层挂载：
  product → Index.md 分节，section → 对应模块 Index.md 条目（title + slug 链接 + 描述句）
evidence: |2-
  decision-log.md#范围·页面进导航的判定链；Talk R1 Q4/Q6；K1 spec FR-AUD-004 页面条目
acceptance: |2-
  覆盖判定三件套成立：页面条目 ⊆ 可达集合、链接目标存在、可达页面 ⊆ 页面条目
  （detail R2-B1 修正，不用数量等式）；任一违例即孤儿或错链，blocked（AC-K2-1）
counterexample: |2-
  若任一 ready 页面不可达，或出现了 manifest 之外的页面条目，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G4-分类维度"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-05
category: data_state
source: "R-016 · 母任务 S3 · K1 spec FR-AUD-003"
question: |2-
  K1 来源级四态（机读 source_status）与 claim 级状态，对 K2 导航范围各有什么影响？
status: confirmed
selected_disposition: |2-
  逐类映射固定：ready 进导航；known_empty/duplicate_alias/audit_only 无页面故不进导航；
  claim 级「资料未明确」不影响导航范围（claim 不改变页面存在性）；K2 不新造状态词表
evidence: |2-
  decision-log.md#范围·数据状态与导航的映射；K1 spec FR-AUD-003/004
acceptance: |2-
  五类状态逐类可核对：导航只覆盖 ready 产生的页面；状态展示仍归 K1 审计面
counterexample: |2-
  若给不存在的页面造了导航条目，或把状态展示重复进导航，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "grill-登记+事实核实（未单独提问，来源=K1 冻结词表）"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-06
category: data_state
source: "R-011 · Talk R1 Q6 · K1 spec FR-AUD-004"
question: |2-
  K1 批次级 run_status（complete/blocked/interrupted）与部分成功批次，K2 各产出什么？
status: confirmed
selected_disposition: |2-
  complete（含部分成功）：导航正常产出，Home.md 显式标注成功页数/阻塞来源数；
  blocked 或 interrupted：不产出导航；
  complete 且零页面：不产出导航，navigation_status=blocked（R2-B7，不动 K1 run_status）
evidence: |2-
  decision-log.md#Talk R1 Q6；范围·数据状态与导航的映射；detail R2-B7
acceptance: |2-
  部分成功批次 Home.md 有标注（AC-K2-5）；blocked/interrupted 批次无导航文件（AC-K2-5）；
  零页面 complete 批次无导航且 manifest navigation_status=blocked（AC-K2-5）
counterexample: |2-
  若 blocked 批次产出了导航，或部分成功批次未标注阻塞，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G6-阻塞口径"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-07
category: success_failure_boundary
source: "R-009 · Talk R1 Q7/Q8 · PRD FR-K2-1/2/3"
question: |2-
  K2 的两道验收门（零孤儿/描述不同质）与一项路径跳数抽查，如何机器可执行？
status: confirmed
selected_disposition: |2-
  两道门+一项抽查的 oracle 全部机器化：入口图遍历脚本（AC-K2-1）、描述唯一性检查
  （AC-K2-2，判据口径与默认值 Talk R3 已冻结：规范化精确相等容忍 0、句式骨架 ≥3 句）、
  路径测量脚本（AC-K2-3，N=10 默认已冻结、题目用户确认后冻结清单）；
  检查器由本卡自建（PRD 验收依赖）；build-spec 只能引用执行、不得改动（Talk R3 取代
  PRD 卡上"build-spec 冻结"措辞）
evidence: |2-
  decision-log.md#验收标准；Talk R1 Q7/Q8；OPEN-K2-3
acceptance: |2-
  AC-K2-1/2/3 全部可机械判定；任一红即 blocked 不产出导航（Q8）
counterexample: |2-
  若任一门的判定需要人工翻页才能下结论，即判该门不可执行、本卡未达标
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G7-查询路径与自检"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-08
category: success_failure_boundary
source: "R-012/R-013 · Talk R1 Q5 · PRD local risk"
question: |2-
  描述句由模型生成，如何防止重蹈 95/99 同质基线？
status: confirmed
selected_disposition: |2-
  两两不重复硬校验 + 任一命中即 blocked（判据①②③④，④=任一描述为空即失败）；
  复用 K1 模型缓存（键含来源指纹+模型标识+提示模板版本）保同输入同输出；
  **模型产物失败（模型不可用且无缓存、或可用但任一输出为空）：运行 blocked 不产出导航**
  （detail D-K1/R2-B3：不留空标注——空描述与容忍=0 判据冲突，失败不伪装成功）
evidence: |2-
  decision-log.md#Talk R1 Q5；已选方向 D-005/D-009；RISK-K2-1
acceptance: |2-
  描述句集合两两不重复达标（AC-K2-2）；同输入双跑导航字节一致（AC-K2-6）
counterexample: |2-
  若描述成片模板句仍放行，或模型失败时导航里出现无标注的空描述，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G5-描述生成"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-09
category: success_failure_boundary
source: "ADR 0014 · grill 专项挑战二"
question: |2-
  K2 的两道门与路径抽查和「知识可用性验收」的边界如何划清，防止自证质量复发？
status: confirmed
selected_disposition: |2-
  显式声明：K2 的门是导航结构正确性门（找得到、分得清），不回答「答得对」；
  知识可用性的唯一被接受证据仍是 K3 的真实查询集验收（ADR 0014）；
  全部材料与 AC 不得把结构门写成可用性验收
evidence: |2-
  decision-log.md#grill 专项挑战二；核心目标；RISK-K2-4
acceptance: |2-
  验收标准与阶段末摘要中结构门定位一致；无「K2 通过即知识可用」字样的表述
counterexample: |2-
  若任何材料把 AC-K2-1..3 写成知识可用性证据，即判边界被突破
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "grill-登记（ADR 压力测试收敛，未单独提问）"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-10
category: non_goals
source: "R-010 · Talk R1 Q9"
question: |2-
  K2 明确不做的事项清单是什么？
status: confirmed
selected_disposition: |2-
  六项：不改 K1 编译；不做发布通道/原子切换/回滚；不做真实查询集对照验收；不删码；
  不引入向量库/前端/服务化/多格式；不碰 CB 既有页/流水线/gbrain；另有过程性两条
  （不靠 build-spec 补需求、主会话不重读取证）
evidence: |2-
  decision-log.md#Talk R1 Q9；## 非目标
acceptance: |2-
  产物目录内不出现非目标项；批次外零写入（AC-K2-7）
counterexample: |2-
  若交付物中混入任一非目标项，即判范围越界
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G8-非目标与延期"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-11
category: deferred
source: "R-017 · Talk R1 Q10 · Talk R3 Q-R3-1 · PRD 第 4 节"
question: |2-
  哪些事项本阶段不展开、各自的 owner 与触发条件是什么？
status: confirmed
selected_disposition: |2-
  五项延期登记 DEF-K2-1..5。其中 DEF-K2-1（同质判据）经 Talk R3 已关闭——口径与默认值
  在本阶段冻结；DEF-K2-2 的 N=10 已冻结、题目清单待用户确认；其余三项（CB 入口合并归 K3、
  generated_by 命名归 build-plan、page-manifest 对齐归 K1/K2 build-spec）维持原登记
evidence: |2-
  decision-log.md#Talk R1 Q10、Talk Round 3；## 风险与延期交接 DEF-K2-1..5
acceptance: |2-
  五项状态逐条可查：已关闭/待用户确认/归 K3/归 build-plan/归 build-spec；无悬空决定
counterexample: |2-
  若出现无登记的悬空决定，或已关闭项被重新打开而不走阶段回滚，即判失败
impact_dimensions: [ordinary_detail]
requires_user_decision: true
visible_group_id: "R1-G8-非目标与延期 + R3-G1-参数归属"
```

```yaml
task_id: task8-entry-navigation
outline_version: v1
oi_id: OI-12
category: complete_user_flow
source: "R-014 · Talk R1 Q1 · K1 spec FR-AUD-004"
question: |2-
  K2 与 K1 在同一次运行内的先后衔接与机读接口是什么？
status: confirmed
selected_disposition: |2-
  K1 页面写入与审计完成后，K2 读 page-manifest.json 的页面条目与 run_status 再生成导航；
  K2 失败（自检 blocked）不改写 K1 产物状态，但 manifest 增写机读导航状态字段
  navigation_status ∈ generated_ok | blocked（detail D-J1：K3 门禁读此字段，不能仅凭
  run_status=complete 放行无导航批次）；K2 阻塞项进同一 manifest 阻塞清单
evidence: |2-
  decision-log.md#已选方向 D-002/D-008；## 完整用户旅程 J7/J8
acceptance: |2-
  J1-J6 产物在 K2 blocked 时仍保持 K1 自身状态机可读；manifest 阻塞清单含 K2 自检失败项
counterexample: |2-
  若 K2 自检失败导致 K1 产物状态被改写或丢失，即判衔接破坏
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: "R1-G2-运行形态（衔接面随 Q1 一并确认）"
```

## grill

### Grill（2026-09-13）· 用现有 ADR、CONTEXT 术语与领域模型压力测试已选方案

**先核实、再提问**：检查全部读自本 worktree 文档与已核实事实；本轮不产生新的用户问题（理由见退出检查）。

#### 全需求覆盖矩阵（五类原始消息 → 决策轴 → 台账）

| # | 原始消息类 | 覆盖的决策轴 | 用户选择或事实依据 | 绑定 |
| --- | --- | --- | --- | --- |
| 1 | 目标 `goal` | 零孤儿/不同质/3 跳的定义与及格线 | 用户 Q5/Q7/Q8；PRD FR-K2-1..3 | OI-07, OI-08；AC-K2-1..3 |
| 2 | 旅程与页面/入口范围 `flow_or_surface` | 三层结构、入口位置、命名、分类维度、模块名来源 | 用户 Q1-Q4、R2-Q1/Q4/Q5/Q6/Q7 | OI-01…OI-04, OI-12；D-002..D-006 |
| 3 | 数据、状态与变化 `data_or_state` | 五类来源状态映射、run_status 三态衔接、阻塞批次口径 | 用户 Q6；K1 FR-AUD-003/004 状态词表 | OI-05, OI-06；AC-K2-5 |
| 4 | 成功/失败/验收边界 `success_failure_acceptance` | 自检失败处置、查询路径来源、结构门≠可用性、模型退化 | 用户 Q5/Q7/Q8/Q9；ADR 0014 | OI-07, OI-08, OI-09；AC-K2-5, RISK-K2-4 |
| 5 | 约束/非目标/延期 `constraint_non_goal_defer` | 非目标六项、五项延期归属 | 用户 Q9/Q10 | OI-10, OI-11；NG, DEF |

#### 专项挑战一：与 ADR 0013 的关系

| ADR 0013 的决定 | K2 已选方向 | 一致性判定 |
| --- | --- | --- |
| KD 输出是语义层内容，不是并行 bundle | K2 导航页写进批次目录（不是 CompanyBrain），上库归 K3 | 不冲突但需限定：同 K1，ADR 0013 的"写进语义层"由 K3 兑现；K2 材料不得把批次目录称为语义层 |
| 层契约/命名/链接风格是权威 | 导航页 frontmatter 服从 16 字段契约、wikilink 双链、英文 slug 目录 | 一致 |
| 同一主题唯一生产者 | K2 导航页路径在批次目录内，不与 CB 既有入口页路径冲突；与 CB 现有 Home.md 的合并/取代归 K3 | 一致（延期登记 DEF-K2-3） |
| 仅允许一个新的页面级溯源字段 | K2 导航页无需溯源字段（导航的"出处"= 对 page-manifest 的机器引用，逐条出处仍是 K1 旁路文件的事） | **授权仍悬空**：K1 未消费（G-001），K2 也不消费；K3 上库时需一并重新决定 |

#### 专项挑战二：与 ADR 0014 的关系（**必须显式声明的边界**）

ADR 0014 禁止"自证质量结果作为可用性证据"。K2 的两道门（零孤儿/描述不同质）与路径跳数抽查是**导航结构正确性检查**，
回答"找得到、分得清"，不回答"答得对"。**K2 交付时"知识是否可用"仍无唯一被接受的证据**（那是 K3 的真实
查询集验收，ADR 0014）。本卡全部材料与 AC 不得把结构门写成可用性验收，验收标准已按此口径书写。

#### 专项挑战三：术语一致性

| 术语 | K2 用法 | 判定 |
| --- | --- | --- |
| 批次目录 = 临时对照产物（非语义层） | 导航文件在批次目录内，同为临时对照产物 | 一致，材料中不得改称 |
| 数据状态词表（S3） | K2 不新造状态：K1 blocked 批次不产导航；K2 自检失败显式 blocked（运行级，复用 K1 run_status 词表） | 一致 |
| 唯一生产者 | 批次内导航页是新产品路径，不触碰 CB 既有页 | 一致 |
| wikilink 双链 | 导航到页面、索引到总览均用 `[[wikilink]]`（同 K1 FR-PUB-001 的可解析规则） | 一致 |

#### 专项挑战四：更小或更稳的替代路径

- 更小范围（只做 Home.md 直列页面）：已否决——页面量增长后 Home 膨胀，且无分类浏览体验（R2-Q1 已比较）。
- 已被拒绝的选项：两层结构、README 升级成入口、纯模板描述、机器自动修孤儿、等 K3 出题、中文文件名——逐项无新事实推翻。
- 无支撑长期能力：未引入；三层结构对当前 89 份语料即生效，"未来各种类型模块"由通用命名（Index.md/知识索引）承载，不建空壳抽象。
- 重复能力：旧 `navigation.py` 属旧 digest 行为（K1 已降级）；K2 三层结构为新形态，渲染工具函数是否复用归 build-plan 盘点（登记 OPEN）。

#### 四项退出检查

| 检查 | 结论 |
| --- | --- |
| 有会改变方向且 Agent 无法自答的剩余问题？ | **无**。授权悬空是记录义务（K3 处置）；结构门定位已在验收标准中写明 |
| 与任一 accepted ADR 冲突？ | 无直接冲突；两处记录义务（ADR 0013 授权悬空沿用 K1 G-001；ADR 0014 结构门边界声明） |
| 与既有领域术语冲突？ | 无；批次目录称呼限制沿用 |
| 引入无支撑长期能力或重复能力？ | 未引入；复用盘点归 build-plan |

#### 文档动作

- CONTEXT.md：本阶段不写入；K2 导航术语（模块总览页、入口描述句）属实现语义，由 build-spec 阶段一并登记（沿用母任务"溯源术语由 build-spec 登记"的安排，登记为 OPEN-K2-1）。
- ADR：不新增 ADR（无新的不可逆架构决定）；ADR 0013 授权悬空沿用 K1 G-001 记录。
- 规格/领域模型变更：本阶段不修改任何既有规格文件。

## 决定条目 D*

| # | 决定 | 依据 |
| --- | --- | --- |
| D-001 | 范围 = PRD K2 一张卡；改 K1 编译、发布通道、删码均不做 | Q0/Q9 |
| D-002 | 导航与 K1 同一次 digest 运行产出；写进批次目录 | Q1/Q2 |
| D-003 | 三层结构：Home.md → Index.md（全局知识索引）→ products/<产品>/<模块>/Index.md → 页面；跳数=点击次数，3 跳压线 | R2-Q1 自定义/R2-Q6 |
| D-004 | 分类维度 = frontmatter product/section 两层；Index.md 按 product 分节、节内列模块总览链接 | Q4 |
| D-005 | 模块总览 = 该模块全部页面 + 每页一条描述句；描述句模型生成、两两不重复硬校验、超阈值 blocked | R2-Q2/Q5/Q8 |
| D-006 | 模块总览页标题从模块页面 title 机械推断，零模型调用 | R2-Q7 |
| D-007 | Home.md = 批次状态显式标注（成功页数/阻塞来源数）+ 快速入口 + 模型写的查询建议 | Q6/R2-Q3 |
| D-008 | K1 blocked 批次不产导航；K2 自检失败（孤儿/同质/跳数）显式 blocked，不产出导航 | Q8 |
| D-009 | **全部模型产物**（描述句 + Home.md 查询建议，detail D-G1 扩）复用 K1 模型缓存机制（键含来源指纹+模型标识+提示模板版本，同输入同输出）；成本计入 run-metrics | Q5/R2-Q3 + K1 FR-CMP 缓存契约 |
| D-010 | 导航页 frontmatter 服从层契约：Home/Index tier 1、模块 Index tier 2、page_model=derived、带 generated_by（生成器命名归 build-plan） | S1 |
| D-011 | 与 CB 现有 Home.md 的合并/取代关系不在本卡，K3 发布时决定 | Q2 后果 + K1 DEF-008 同构 |
| D-012 | 写权：只写批次目录内导航文件；CB/gbrain/停摆流水线零写入 | NG-008 |

## 非目标

- NG-001 不依赖 build-spec 补齐需求（需求已在 make-decision 收敛）。
- NG-002 主会话不做重读量取证；取证按量分流（本次量小由主会话直读，原则保留）。
- NG-003 不改 K1 编译（块/claim/页面/frontmatter 零改动）。
- NG-004 不做发布通道、原子切换、回滚、last-known-good（K3）。
- NG-005 不做真实查询集对照验收、不做逐题四结果判定（K3）；K2 的 N 条路径是导航结构测量，不是查询集验收。
- NG-006 不做源码瘦身删码与三项度量（K4）。
- NG-007 不引入向量库/图数据库/服务化/前端/多格式输入。
- NG-008 不修改 CompanyBrain 既有正式页、不停摆流水线改动、gbrain 零触碰。

## 风险与延期交接

| risk/deferred_id | 内容 | 触发/后果 | 处理阶段/owner |
| --- | --- | --- | --- |
| RISK-K2-1 | 模型写的描述句仍可能成片同质（基线 95/99 即模型/模板同质造成） | 入口区分度名不副实 | 两两不重复硬校验 + 超阈值 blocked（D-005/AC-K2-2） |
| RISK-K2-2 | 模块中文名从页面 title 机械推断可能不准 | 导航可读性受损（不影响事实正确） | 验收抽查 + 必要时显式主题映射的人工修正通道（归 build-plan  OPEN） |
| RISK-K2-3 | K1 page-manifest 字段契约若漂移，K2 读取会断 | 导航生成失败或错链 | K1 build-spec 冻结后锁定；K2 build-spec 对齐（DEF-K2-5） |
| RISK-K2-4 | K2 结构门被误读为"知识可用"证据 | 重复旧项目的自证质量错误（ADR 0014 针对的正是这个） | 全部材料显式声明结构门≠可用性；grill 专项挑战二 |
| DEF-K2-1 | ~~同质判据与阈值数值~~ **已关闭（Talk R3）**：判据口径①规范化精确相等容忍 0、口径②句式骨架 ≥3 句判模板化，均已冻结；build-spec 只执行不改动 | AC-K2-2 的可执行性 | owner=build-spec 执行；改动须回 make-decision |
| DEF-K2-2 | N 条查询路径的题目清单：N=10 默认值已冻结（Talk R3）；**题目从用户真实查法选取、用户确认后冻结清单** | AC-K2-3 的可执行性 | owner=build-spec 收集题目 → 用户确认；确认前 AC-K2-3 记 incomplete |
| DEF-K2-3 | 批次内入口与 CB 现有 Home.md 的合并/取代关系（F-5 定调：本卡并行自营，合并归 K3） | K3 发布时的生产者/入口冲突 | owner=K3（同 K1 DEF-008） |
| DEF-K2-4 | 导航生成器 generated_by 命名、模块名推断规则细节 | D-006/D-010 的实现参数 | owner=K2 build-plan |
| DEF-K2-5 | K1 page-manifest 字段契约的最终对齐 | K1/K2 接口 | owner=K1 build-spec 冻结 → K2 build-spec 对齐 |

## 未决项

| id | 未决内容 | owner | 触发条件 | 关闭条件 |
| --- | --- | --- | --- | --- |
| OPEN-K2-1 | K2 导航术语（模块总览页、入口描述句、批次导航）登记进 CONTEXT.md | K2 build-spec | 冻结导航契约时 | CONTEXT.md 出现条目且与实现字段一致 |
| OPEN-K2-2 | 旧 navigation.py 的可复用盘点 | K2 build-plan | 设计导航实现时 | 复用清单与绕开清单产出 |
| OPEN-K2-3 | K2 自检指标的精确冻结形态（孤儿遍历链接集合、相似度算法、路径清单） | K2 build-spec | 写 spec 时 | 指标可机械执行，AC-K2-1..3 oracle 可跑 |

## 审查处置

### direction-advice（step 6，2026-09-13）

**调用事实**：`wh-review` direction track（CLI：`/Users/Hugh/Hugh/Project/workflowhub/skills/wh-review/scripts/wh-review-cli.mjs`，
首次查找时遗漏该路径，曾误判 executor_absent；经用户指正重新查找后 doctor `status=ok`，本轮为真实调用）。
pair_id `85e65a7d-41f3-40a5-a286-18640bafdf3d`，material_id `253b2dfe2869bad31940658c9a2c05582bef52bff0d4388f71d3f7b0900886dc`，
sink_ref `/Users/Hugh/.workflowhub/review-sink/608fd7aa4a60032ac53b270dd64fc02387eef107600ca0a2fff4165577b49403.json`。
red 三角色（kimi/coding、antigravity/flash、codex/luna）与 blue 三角色（同）全部 completed；
公共结果 **`available-with-failures`（不是 pass）**。输入材料 attempt 留存：
`quality/reviews/attempts/k2-direction-input.json`。

**材料边界遵守情况**：direction 为盲审；提交键 = `raw_requirement` / `objective_facts` / `convergence_outline`
（questions-only 投影，全部 `status: open`，无 answer/disposition/evidence）；未提交 decision_log、已选方案或 OI 终态。

**finding 逐条处置**（red/blue 同一实质问题合并为一条）：

| # | severity | finding 实质 | 处置 | 证据/落点 |
| --- | --- | --- | --- | --- |
| F-1 | **blocking**（codex red+blue；kimi/antigravity red 同类） | FR-K2-1 量化域"已发布页"与 K1 冻结接口冲突：publish_status 恒 not_released、发布归 K3，遍历集合为空会假阳性空跑通过 | **有效，已在本阶段修复**：量化域显式钉死为「page-manifest.json 中 run_status=complete 的全部页面条目」（发布前集合），并在 AC-K2-1 与 OI-04 写明与 K3 的衔接（K3 发布时该集合的可达性为前置，不可绕过 K2 失败状态放行） | AC-K2-1、OI-04、范围·判定链 |
| F-2 | **blocking**（codex red+blue；kimi red+blue 同类） | FR-K2-2 阈值与 FR-K2-3 的 N 归"build-spec 冻结"，与用户"不要依赖 build-spec 补需求"冲突；方向阶段不定参数，两道门本阶段不可判 | **有效，进入 Talk Round 3 请用户裁决参数归属**（见 `## Talk` Round 3）：make-decision 当场冻结参数方向，还是维持"build-spec 冻结数值、make-decision 只冻结口径"并显式声明这不构成"依赖 build-spec 补需求" | Talk Round 3 Q-R3-1 |
| F-3 | major（kimi red+blue；antigravity、codex red 同类） | 状态口径矛盾：材料写"五类来源级状态"但只枚举四类；机读 source_status 四态；S3 词表五项（含「资料未明确」）无机读承载；claim 级状态无定义 | **有效，已在本阶段修复**：统一口径为「来源级四态（机读）+ claim 级『原文未明确』（K1 运行内值，不影响导航范围）」；修正 OI-05 问题文本与数据状态映射表的措辞 | OI-05、范围·数据状态与导航的映射 |
| F-4 | major（kimi red+blue；antigravity、codex red 同类） | "修循环"无终止条件/升级路径，"达标待发布"成无出口判据 | **有效，已在本阶段修复**：显式写明修复循环轮数=0——K2 不修孤儿/同质（孤儿=生成代码 bug，静默修复会掩盖根因，Q8 用户已选 blocked 不产出）；终止处置=blocked + 阻塞项进 manifest + 人工修后重跑 | 完整用户旅程 J8、OI-07、D-008 |
| F-5 | major（kimi red+blue） | CB 现有 Home→分类索引→产品总览→页面四层链已耗尽 3 跳预算；K2 与 CB 现有入口是注入/替换/并行未显式决策，可能交付第二套互不通达的导航 | **有效，已在本阶段修复**：显式定调"并行自营"——K2 入口只在批次目录内（不动 CB tier-1 文件），3 跳测量边界=批次内 Home 起算；与 CB 现有入口的合并/取代归 K3（DEF-K2-3，已登记）。该张力与取舍在本记录显式声明 | 范围（S8 口径段后新增"与既有入口的关系"声明）、DEF-K2-3、grill 术语表 |
| F-6 | major（kimi blue） | "三道门"是投影自造的合成口径；PRD 原文只有"两道门"（孤儿/同质），FR-K2-3 是独立抽查项 | **有效，已修复措辞**：OI-07/OI-09 及全部材料统一为「两道门（零孤儿/描述不同质）+ 一项路径跳数抽查」，与 PRD 原文对齐 | OI-07、OI-09、验收标准表头 |
| F-7 | major（antigravity blue） | 质疑模型写描述的前提：可用 K1 冻结 frontmatter（中文 title/taxonomy）确定性聚合描述，消掉同质风险与修复循环 | **复议后维持用户选择，登记论证**：title 聚合确实零成本，但"入口描述"要的是「这页帮你解决什么」的区分句（FR-K2-2 防的正是 title 式同质）；纯聚合做不到区分度（K1 也论证过标题同名问题 RISK-004）。维持 Q5 选择（模型写+硬校验），本论证补入拒绝方案 | 拒绝方案、Talk R1 Q5 |
| F-8 | minor（kimi blue、codex blue） | questions-only 投影缺 task_id/source 逐条绑定 | **有效，已关闭**：detail r2 材料直接承载 decision-log 全文（task_id/来源在文内），该义务随材料重建关闭，不新增悬空登记号 | detail-advice r2 输入材料 |

**处置结果**：F-1/F-3/F-4/F-5/F-6 在本阶段修复（改条款与措辞）；F-7 复议后维持用户选择并登记论证；F-8 登记为 detail 阶段材料义务；F-2 进入 Talk Round 3 用户裁决。修复未改变任何已选方向，OI 集合不变（outline 仍为 v1，仅 OI-05/07/09 的问句与验收措辞修订），按合同不因措辞修订重复 direction review。

### detail-advice（step 10，2026-09-13，首轮）

**调用事实**：`wh-review` detail track（输入 `quality/reviews/attempts/k2-detail-input.json`），
pair_id `786c9310-2fa0-43ea-98e7-df8b644a9900`，material_id `d1de2db2e75d024c45e54b1f44a6a8a21f9e93c4ec99f030e48fe08918c290c4`，
sink_ref `/Users/Hugh/.workflowhub/review-sink/e1bba5c4deb200774cc7360004819ffc78726f9e44bb6f213a281007566407fa.json`。
公共结果 **`available-with-failures`（不是 pass）**：kimi/coding red+blue 均 `OUTPUT_INVALID`（不写成"没有问题"）；
pi/v4flash、antigravity/flash、codex/luna red+blue 均 completed。材料键按合同
`raw_requirement` / `approved_direction` / `draft_spec_or_acceptance` 提交。

**首轮 finding 逐条处置**（red/blue 同一实质合并；编号 D-x）：

| # | severity | finding 实质 | 处置 |
| --- | --- | --- | --- |
| D-A | major（pi red+blue） | OI-07 终态与核心需求/已选方向残留"build-spec 冻结/三门"旧口径，Talk R3 裁决未传导 | **有效，已修复**：OI-07 disposition、核心需求 2/3 条、已选方向·查询路径统一为 Talk R3 口径；grill/验收表同步 |
| D-B | major（pi red、codex blue） | draft 材料是重叠切片拼接（正则未锚定行首，匹配到头部说明里的伪标题），孤立标题+重复小节，非单一规范 | **有效，材料层修复**：切片正则锚定 `\n## `；重建 r2 材料（验收标准 2.6KB/范围 3.9KB/摘要 1.7KB）并重跑第二轮；如实登记不掩盖 |
| D-C | major（pi red） | 头部状态行仍记"step 6/10 unavailable（executor_absent）"，与 step 6 真实结果矛盾 | **有效，已修复**：头部状态行改为两项审查的真实状态 |
| D-D | minor（pi red） | F-8 落点 OPEN-K2-4 未定义 | **有效，已修复**：F-8 处置改记"detail 材料重建已修复"，不新增悬空登记号 |
| D-E | major（pi red、antigravity red、codex blue） | 空描述与容忍=0 冲突；口径②实体词/骨架算法未定义 | **有效，已修复（D-E1）**：骨架最小算法冻结（移除 title/product/section 词→去标点小写）；空描述消除——模型不可用改判 blocked 不产出导航（D-K1），AC-K2-2 加空描述豁免条款（恒空集） |
| D-F | major（codex blue） | AC-K2-5 oracle 含"人工抽读"，与全机器自检矛盾 | **有效，已修复（D-F1）**：oracle 改机器字段校验（Home 标注与 manifest 对账） |
| D-G | major（antigravity red、codex blue） | Home.md 查询建议未纳入缓存/验收，AC-K2-6 双跑抖动风险 | **有效，已修复（D-G1）**：D-009 扩为"全部模型产物（描述句+查询建议）走缓存"；AC-K2-6 同步 |
| D-H | minor（antigravity red） | R-010"页面类型映射"无对应规则却标 covered | **有效，已修复（D-M1）**：R-010 补声明——本卡"页面类型映射"=product/section 两层挂载（OI-04） |
| D-I | minor（antigravity red）+ major（codex blue） | K2 失败时 run_status 仍 complete、无导航，K3 无机读依据；且 run_status=complete 零页面批次行为未定义 | **有效，已修复（D-J1/D-I1）**：manifest 增 `navigation_status ∈ generated_ok\|blocked`（K3 门禁读它）；零页面 complete 批次改记 blocked"零页面批次" |
| D-J | blocking（codex blue） | 材料仍 pending_user_confirmation 就提交审查 | **流程事实，accepted_risk**：detail track 按合同本在方向草稿后、最终确认前执行（同 K1 先例）；该 finding 不改变任何条款 |
| D-K | major（pi red、antigravity blue） | J9"死链/张冠李戴判失败"无 oracle；模型不可用退化路径与判据冲突 | **有效（D-K1/D-L1）**：死链存在性并入 AC-K2-1 遍历 oracle；"张冠李戴"移出 K2 机器判失败（归 K3 查询集/人工面）；模型不可用=blocked |
| D-L | major（codex blue） | AC-K2-4 未列字段期望值、generated_by 归 build-plan；AC-K2-3 只冻结 N=10 未冻结十条路径 | **部分有效**：AC-K2-4 补字段引用（K1 FR-PUB-001 表+tier 分层+generated_by 归 DEF-K2-4）；十条路径题目清单维持 DEF-K2-2（用户确认后冻结，本来就是本卡登记的延期项，不属"靠 build-spec 补需求"——owner 是用户确认） |

**处置结果**：D-A…D-I/D-K/D-L 全部处置（条款修复或登记）；D-J 为流程事实 accepted_risk；D-B 材料缺陷已修复并重跑。
**首轮后不重复消费**：第二轮 detail 仅因材料缺陷（D-B）发起，条款未新增方向变化。

### detail-advice（step 10，2026-09-13，第二轮·材料修复后）

**调用事实**：`wh-review` detail track（输入 `quality/reviews/attempts/k2-detail-input-r2.json`），
pair_id `36a2ba31-b3bd-4f17-8a5c-721bcfb15179`，material_id `6e02c2e346f92626890272fcdbbe514ea907559cf06158c98e193b6cffd19bd1`，
sink_ref `/Users/Hugh/.workflowhub/review-sink/30b37c1c7dec749f5fd141b4a50d4d45e6af7c3895734b8c3a408ae0e0111ec2.json`。
red+blue 全部 8 个 provider 调用 completed（无 OUTPUT_INVALID）；公共结果 **`available-with-failures`（不是 pass）**。

**次轮 finding 逐条处置**（去重后；编号 R2-x）：

| # | severity | finding 实质 | 处置 |
| --- | --- | --- | --- |
| R2-A | major（kimi/pi/codex） | detail 执行状态四处矛盾（头部/摘要/step10/审查处置），且 D-* 处置表缺失 | **有效，本轮修复**：审查处置小节写全（首轮处置表+本轮结果），step 10 记录同步——矛盾源于"首轮处置表在次轮运行期间才写入"的时序，现消除 |
| R2-B1 | **blocking**（antigravity red） | 判定链/AC-K2-1 用"页面条目数 == 可达页面数"等式——遍历含 Index 节点，数量恒大于页面数，自检必失败 | **有效，已修复**：改为覆盖判定三件套（条目 ⊆ 可达 ∧ 链接存在 ∧ 可达页面 ⊆ 条目），判定链与 AC-K2-1 同步 |
| R2-B2 | major（antigravity red） | "非模板化问句"原文约束无机读判据 | **有效，已修复**：AC-K2-2 增判据③（疑问句式模板"如何/什么是/怎么…？"骨架 ≥3 句判失败） |
| R2-B3 | major（kimi/pi/antigravity/codex） | 空描述豁免留漏洞：模型可用但个别页面输出空串时豁免①②且不算生成失败，静默通过 | **有效，已修复**：删豁免，AC-K2-2 增判据④（任一描述为空/空白即失败）；J7/OI-08 同步——模型不可用/部分空/全空统一 blocked |
| R2-B4 | minor+major（antigravity red+blue） | 查询建议（用户 R2-Q3 选择）无验收 oracle；被指 scope creep | **oracle 已补，方向维持**：AC-K2-4 增"查询建议 ≥3 条且非空"。scope creep 论点登记但**用户 R2-Q3 明确选择"要，模型写"**，不推翻；缓存已含（D-009/G1） |
| R2-B5 | blocking（codex blue） | AC-K2-3 十条路径未冻结、AC-K2-4 generated_by 未冻结，声称七条可执行不实 | **部分有效，诚实标注**：测量方法与 N=10 已冻结；题目清单（DEF-K2-2）与 generated_by（DEF-K2-4）确认前，这两条子项记 **incomplete**（阶段末摘要已改，不声称全部可执行）。题目确认本来就是本卡登记的"用户参与"动作，不属依赖 build-spec 补需求 |
| R2-B6 | major（codex blue） | AC-K2-5 计数字段无 schema（字段名/类型/计数公式） | **有效，已修复**：manifest `navigation` 节字段契约冻结 `{success_pages, blocked_sources, navigation_status, blocked_reasons}` + 计数公式 + Home 状态行对账 |
| R2-B7 | major（antigravity/kimi/pi/codex） | 零页面"批次改记 blocked"=改写 K1 run_status，违反 OI-12 隔离 | **有效，已修复**：K1 run_status 不动，manifest `navigation_status=blocked`+阻塞项；OI-06 终态、数据状态映射表、AC-K2-5 同步 |
| R2-B8 | minor（pi red） | OI-06 终态未含零页面例外 | 随 R2-B7 修复同步 |
| R2-B9 | minor（kimi/pi red） | 阶段末摘要"两轮 Talk 17 项"漏第三轮且计数错（Q0–Q10 为 11 项） | **有效，已修复**：三轮 Talk 共 19 项（11+7+1） |

**处置结果**：R2-A…R2-B9 全部处置（条款修复或诚实标注）；**无 finding 被静默丢弃**。
两轮 detail 均为质量事实而非推进许可；本阶段据此修复后进入用户确认（step 11）。

## 拒绝方案

- 两层导航（索引页直接列页面）：跳数少但索引膨胀，放弃分类浏览（R2-Q1 被用户细化拒绝）。
- README.md 升级成入口：冲击 K1 AC-06 字节比对与 README 确定性模板约束（Q3）。
- 纯模板机械描述：基线 95/99 同质即模板/模型同质造成，名义达标实际没用（Q5）。
- 机器自动修孤儿：掩盖生成逻辑 bug（Q8）。
- 等 K3 的问题集：K2 被卡且方向错位（Q7）。
- 中文文件名：slug 归一化不确定性（R2-Q5）。
- 确定性聚合替代模型描述（direction F-7 复议）：antigravity 建议从 K1 冻结 frontmatter 机械聚合描述句，
  可消掉同质风险与修复循环；复议后维持 Q5 选择——聚合句是标题式复述，达不到 FR-K2-2 要的「这页解决什么」
  区分度（基线 95/99 同质正是标题/模板式描述造成；K1 RISK-004 亦证明同名主题机械推断会漂移）。
  模型写+两两不重复硬校验保留，本论证留档备查。

## 阶段末摘要（六项，交下游 build-spec）

1. **本阶段做了什么**：三轮 Talk（Q0–Q10、R2-Q1–R2-Q7、Q-R3-1 共 **19 项**用户真实答复）+ 一次 grill（ADR 0013/0014、术语、替代路径）+ K1 接口与 CompanyBrain 索引结构取证 + 12 条 OI 收敛（outline v1）+ 两轮真实异源审查（direction 8 findings、detail 首轮 12 条/次轮 6 条，全部处置）；方向、三层结构、描述生成、阻塞口径、查询路径、非目标、延期项全部收敛为 12 条决定条目（D-001…D-012）。
2. **覆盖到什么程度**：PRD K2 的 3 条 FR/AC 全部落到可执行判据（AC-K2-1…AC-K2-7）；六类边界全部有用户答复或事实依据，无 `empty` 占位；OI 12 条全部 `confirmed`。**诚实标注**：AC-K2-3 的十条路径题目清单待用户确认（DEF-K2-2），确认前该 AC 记 incomplete；AC-K2-4 的 generated_by 值归 build-plan（DEF-K2-4），确认前该子项 incomplete——不声称七条全部已可执行。
3. **与上游产物是否一致**：与 K1 设计接口一致（page-manifest、frontmatter 16 字段、批次目录结构、run_status 词表）；与 ADR 0013 一致（授权悬空沿用 K1 G-001）；与 ADR 0014 的边界显式声明（结构门≠可用性）。
4. **本阶段当场修复了什么**：grill 发现的"结构门易被误读为可用性验收"已在验收标准与 grill 中显式修正；ADR 0013 授权悬空沿用 K1 记录，不重复消费。
5. **剩余风险与未决**：RISK-K2-1…RISK-K2-4、DEF-K2-1（已关闭）…DEF-K2-5、OPEN-K2-1…OPEN-K2-3；
   外部异源审查：direction=`available-with-failures`（F-1…F-8 已处置）；detail 两轮均
   `available-with-failures`（首轮 12 条、次轮 6 条实质 finding，全部处置，见 `## 审查处置`）。
6. **下游可直接消费什么、不能猜什么**：build-spec 可直接消费 12 条决定条目与 7 条 AC；**不得**重新决定产品方向；**不得**把 DEF-K2-1…K2-5 当已完成；**不得**把结构门写成可用性验收；**不得**把 unavailable 的审查写成通过。

## 最终确认

- **状态**：`approved`（用户真实确认，2026-09-13）
- **确认方式**：宿主结构化问答（`ask_user_question`），按主题分组展示。
- **用户原文**（逐字）：「确认，进入 stage-end 与发布（推荐）」
- **确认覆盖范围**：本决策记录全部方向、边界、验收（含 detail 修复后的覆盖判定四判据/navigation 机读契约）、
  非目标、延期与风险；无保留、无部分确认。
- **确认前置的质量事实**：direction-advice 与 detail-advice 两轮均为真实执行的 `available-with-failures`
  （**均非 pass**），全部 findings 已逐条处置（见 `## 审查处置`）；用户确认时已知悉该性质。
- **诚实标注（确认时已知悉）**：AC-K2-3 的十条路径题目清单待用户确认（DEF-K2-2）、AC-K2-4 的
  generated_by 值归 build-plan（DEF-K2-4）——确认前这两项子项为 `incomplete`，不声称七条 AC 全部已可执行。
- **未确认/保留内容**：无。

### stage-end 自检与发布（step 12–13，2026-09-13）

**step 12 stage-end-spec-analyze**：本会话无外部 Stage Agent 宿主（同 K1 先例），官方 stage outcome 按合同记
`unavailable`（`stage_outcome_missing`），不伪造通过、不阻塞交接。主会话自行执行结构自检（对照 K1 P-1…P-3
教训的官方校验器核心项）：

| 检查项 | 结果 |
| --- | --- |
| OI 记录 YAML 可解析 | 12/12 PASS |
| visible_group_id 齐全 | 12/12 PASS |
| 占位关键词扫描（confirmed disposition 含未知/待定/TODO） | 0 hits PASS |
| Fixed categories 覆盖全部 OI | 12/12 PASS |
| R-001…R-017 覆盖 | 17/17 PASS |
| D-001…D-012 存在 | 12/12 PASS |
| AC-K2-1…AC-K2-7 存在 | 7/7 PASS |

**step 13 publish-decision**：本决策记录为 make-decision 阶段唯一权威材料；`spec.md`/`plan.md`/`tasks.md`
由后续阶段自建，本材料对其只读。两项 incomplete（DEF-K2-2 题目清单、DEF-K2-4 generated_by）按各自
owner 与触发条件跟踪关闭。
