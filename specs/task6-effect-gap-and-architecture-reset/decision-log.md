# 决策记录 · task6-effect-gap-and-architecture-reset

> 本文件是 make-decision 阶段唯一权威材料。OI 大纲只存在于本文件内，不另建需求账本、状态机或第五份材料。
> 当前阶段状态：**in_progress**（step 1–10 已完成：load-context、triage-scope、Talk 三轮、调研与独立复核、direction-advice、Grill、决策草稿、detail-advice；等待 approve-decision 的用户真实确认）。
> 标题层级说明：`## 原始需求`、`## 核心需求`、`## 核心目标`、`## 已选方向`、`## 验收标准`、`## 范围`、
> `## 非目标`、`## 风险与延期交接`、`## UI applicability`、`## 收敛检查` 是运行时读取的固定小节名，保持不带编号。

## 任务身份

| 项 | 值 |
| --- | --- |
| project | KnowledgeDigest |
| task_id | `task6-effect-gap-and-architecture-reset` |
| stage | make-decision |
| worktree | `/Users/Hugh/Hugh/Project/KnowledgeDigest-task6-effect-gap-and-architecture-reset` |
| branch | `task/KnowledgeDigest/task6-effect-gap-and-architecture-reset` |
| baseline_commit | `420946427af7ee06d4e3c58bd1e27748d4d00ad2` |
| task_path | `/Users/Hugh/Hugh/Knowledge/Projects/KnowledgeDigest/tasks/task6-effect-gap-and-architecture-reset` |
| created_at | 2026-09-12 |

- **任务类型**：规划任务

`规划任务`只问方向层问题；本文件在 step 3 起的提问只覆盖用户可见行为与结果、任务类型范围、
工作流、完成/失败条件、不变量、约束、非目标与延期项；不提问文件路径与文件面、函数名、字段名、
算法、schema 形状、命令形态、入口参数形态、行号、代码片段、测试记录与实测记录。

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 状态/处置 | 关联 D/OI |
| --- | --- | --- | --- | --- |
| R-001 | 判断当前效果确有实质问题，不是感觉问题 | 用户原话第 1 句「我感觉还是有很大的问题」 | covered | OI-03, D-001 |
| R-002 | 对 release4 产物做仔细的效果分析 | 用户原话第 1 句「需要你帮我仔细分析一下效果如何」 | covered | OI-03, F-001, D-001 |
| R-003 | 与 CompanyBrain 逐项比较差距 | 用户原话第 1 句「和我原来的知识库…相比，有什么差距」 | covered | OI-07, F-002, D-002 |
| R-004 | 审计当前架构、性能、可维护性 | 用户原话第 2 句「架构、性能、可维护性到底如何」 | covered | OI-04, F-003, D-003 |
| R-005 | 调研外部开源项目/可复用代码，是否存在更好做法 | 用户原话第 2 句「市面上有没有类似的开源项目…效果更好的？」 | covered | OI-10, F-004, D-004 |
| R-006 | 给出改造方向：效果更好 + 项目更简单优雅 | 用户原话第 2 句「还应该如何改造才能保证效果更好，项目更简单优雅？」 | covered | OI-06, OI-09, D-005 |
| R-007 | 按标准 WorkflowHub 五阶段执行，先建 worktree，从 make-decision 开始 | 用户原话第 3 句 | covered | 阶段执行记录 |
| R-008 | 不跳阶段；不依赖 build-prd 补需求 | 用户原话第 3 句 | covered | 非目标 NG-001 |
| R-009 | make-decision 内共同梳理六类边界（用户流程/页面范围/数据状态/成功失败边界/非目标/延期） | 用户原话第 3 句 | covered | OI-16…OI-21 |
| R-010 | 主会话上下文控制 + 子代理派发 | 用户原话第 4 句 | covered | 非目标 NG-002 |
| R-011 | Talk 与 Grill 用大白话说明选项、后果、风险 | 用户原话第 5 句 | covered | Talk 表；Talk 卡格式 |

**未覆盖/待定**：无。R-001…R-011 全部落到 OI 或执行约束；无 `accepted_omission` 条目。

### 需求框架预设（先于研究/Talk 选定）

- **framework**：`functional`（背景 → 问题 → 目标 → 方案 → 验收 → 扩展），并在 `problem` 与 `solution` 节点下挂 `research` 子树（本任务是"先取证再定方向"的证据驱动决策）。
- **选择理由**：任务主体是"决定 KnowledgeDigest 下一步怎么做"，属行为/结构改动；但方向判断依赖对 release4 产物、现有代码、外部项目三组证据的核对，因此以 `functional` 为外层骨架，把证据核对挂在受影响节点下，而不是另开一套 research 框架。
- **回填规则**：Talk、调研、审查、Grill 只更新本文件的 OI 表与 D* 条目，不新建第二张表、不新建需求账本。

### 用户原话（逐字，未改写）

> 当前的KnowledgeDigest项目我感觉还是有很大的问题，最新的测试结果是基于"'/Users/Hugh/Downloads/confluence 原始数据'"作为原材料，生成了"/Users/Hugh/Downloads/KnowledgeDigest-task5-m402-20260908.release4"，需要你帮我仔细分析一下效果如何，和我原来的知识库"/Users/Hugh/Hugh/Knowledge/CompanyBrain"相比，有什么差距。
>
> 以及当前KnowledgeDigest项目的架构、性能、可维护性到底如何，市面上有没有类似的开源项目或其他项目中的部分代码，可以做到比我的KnowledgeDigest效果更好的？当前KnowledgeDigest还应该如何改造才能保证效果更好，项目更简单优雅？
>
> 请按标准 WorkflowHub 开始这个规划任务吧，先创建worktree，然后从 make-decision 开始，不要跳阶段，也不要依赖 build-prd补需求。先基于原始需求，在make-decision的过程中和我一起仔细调研外部项目、梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。注意主会话上下文控制和子代理派发。Talk 和grill请用大白话说明选项、后果和风险；

## 核心需求

KnowledgeDigest 现在生成的"知识库"读起来不像知识库：产物与用户手写维护的 CompanyBrain 差距明显，
而项目自己的质量报告却宣称"全部达标、已发布"。用户需要先看清真实差距与项目真实状态（效果、架构、
性能、可维护性、外部可选做法），再决定下一步怎么改，让效果更好、项目更简单优雅。

## 核心目标

**目标（Talk Round 1 用户已定，T-001 = A）**：先把读者效果做对，再删复杂度。

- 第一判据（效果）：让产物对指定读者问题**可确认可用**——读者能在产物里直接找到答案，并能回到原文出处；
  及格线以 CompanyBrain 为对标（T-002 = A：要能替代 CompanyBrain 查产品知识）。
- 第二判据（简单）：在效果成立的前提下，把不产生读者价值的复杂度净削掉，使项目可被人继续改动。
- 补充目标（T-005 用户原话引入）：产物要能作为**语义知识层**，方便他人在其上建立技能层、Agent 层与应用层（OI-22/OI-23）。
- 当前证据状态：`evidence_status: confirmed`（Round 1–3 用户答复 + 调研落地），`evidence_owner`: 主会话，
  `next_review_trigger`: 无（目标与判据已收敛，后续细化属 spec/plan）。

## 已选方向

**选定方向（Talk Round 1 + Round 2 用户已定）**：

- 目标排序：**先把读者效果做对，再删复杂度**（T-001 = A）。
- 及格线：**要能替代 CompanyBrain 查产品知识**（T-002 = A）。
- 形态：**保持"离线编译成本地 Markdown 知识库"**，重做"读什么、怎么组织、怎么保证可信"这条主线（T-003 = A）。
- 最终呈现形式：**KD 直接产出用户既有语义层的页面**——同一套 frontmatter（`type/page_model/tier/trust/source_status/quality_status/scope/product/section/generated_by/tags`）、
  同一套目录与命名规范、`[[wikilink]]` 双链，使 `gbrain` 与下游技能层/Agent 层/应用层可直接消费（T-006 = A，含重问后的具体产物样例）。
- 参考型内容：**逐字保留**表格、参数、枚举、字段字典、URL、报错文案，只对叙述性段落做语义合成（T-007 = A）。
- 存量处置：**保留骨架、砍掉历史分支**（含自证质量机器与已结束任务的专用路径）（T-004 = A）；
  写权边界写死，**不修**停摆的每日流水线，该修复另开任务（T-011 = A）。
- 质量验收：**删掉自证机器，改成真实查询集 + 真实判定**（T-008 = A）。
- 输入范围：**本期只做 Confluence Markdown**（T-009 = A）。
- 人工环节：**全自动，不设人工确认**（T-010 = B，用户明确选择并已接受"错误内容会直接进库"的风险）。
- 交付面：**生成页面算一等交付面**，按读者路径验收（T-005 = A）。
- 被拒方案：问答/RAG 为主、两者并存（T-003）；推倒重写、只做增量修补（T-004）；保留自有格式另加导出层、先不定（T-006）；模型重写参考内容、参考数据单独成字典页（T-007）；精简为少量硬事实、保留全部自证机器（T-008）；同时接多格式、只留接口（T-009）；设人工确认、全量人工审校（T-010）；把流水线修复纳入本任务（T-011）。
- 事实约束（F-002 已核实）：文档承诺的"每页 ≤300 行"在当前产品路径**没有实现**；既有语义层契约的执行者是 `tools/apply_formal_knowledge_metadata.py`；
  两套产物契约（`page_type`/`digest_*`/相对链接 vs `type`/`[[wikilink]]`）目前直接对撞，改造必须由 KD 侧对齐。

## 验收标准

**及格线已定（T-002 = A：要能替代 CompanyBrain 查产品知识）；判定规则与失败条件在 detail-advice 后被补齐（见下）。**

### 对照判定规则（T-012 + detail findings）
- 冻结三样东西：89 份输入 Markdown 的清单与 hash、改造前 release4 产物快照、CompanyBrain 快照（记录 snapshot ID）。三者缺一，验收结论无效。
- 逐题判定四个结果：**答案命中**（能定位到回答该问题的页面与段落）、**定位有效**（该段落有 claim 级原文位置）、**出处正确**（回到原文核对一致）、**对照未覆盖**（对照快照中本来没有对应内容，不计为我方优势）。
- 每题的答案判定、定位判定、出处判定与汇总通过条件必须在 build-spec 冻结为可执行规则；只写"不劣于"不算达标。
- 失败条件：找不到；只能找到原文堆积；找到的内容与原文不符（改动语义或凭空编造）；"优于对照"的结论依赖对照侧未覆盖。

### 读者路径（T-005 = A + detail findings）
- 从入口页出发必须能到达**每一个**已发布页面；入口描述对页面必须有区分度。
- 失败条件：存在没有入口的已发布页；或入口描述对多页同质（本次基线实测：87/99 页无首页入口、95/99 页正文同一模板问句、首页导航表仅 12 行）。

### 数据状态（OI-18 + detail findings）
- 对 ready / known_empty / duplicate_alias / audit_only / 资料未明确 逐类构造样例输入，核对状态与正文一致。
- 失败条件：重复来源被发成两页（本次基线实测有同源两页语义矛盾）；"资料未明确"被写成结论或进入事实分母；增量更新删除旧页。

### 参考型内容（T-007 = A + detail findings）
- 冻结分层全量清单（表格 / 参数 / 枚举 / 字段字典 / URL / 报错文案），带来源区间与 hash，逐块与产物比较；抽样只能作为补充，不能作为唯一证据。
- 无法保留结构必须显式标注；多来源互相矛盾时必须保留各自定位并显式标注冲突，静默择一即判失败。

### 证据零容忍（T-014 = A + detail findings）
- claim 的边界与引用语法（来源 ID、不可变快照、行或字符区间、一对多映射）由 build-spec 冻结为可解析契约；"原文未明确"也有明确的标记语义。
- 失败条件：存在既无原文定位、也无显式标注的结论行；出现错定位；多 claim 句子未逐条映射；无定位内容被写成肯定句。无定位内容只能进入 unknown 状态，且该状态本身要带检索证据。

### 发布安全（T-010 = B 全自动的替代控制 + detail findings）
- 发布必须是"先 staging 校验、再原子切换"，并保留 last-known-good 版本。
- 必须构造并通过负例：写入中断、取消、校验失败、越界写入（硬失败）、引用不可达；读者与 gbrain 只能看到完整的新版本或旧版本，不得看到半成品。
- 必须能回滚到上一可用版本，并在回滚后保留真实错误与调用计数。

### 成本与可维护性（T-013 = A + detail findings）
- 成本沿用现有量级（一次运行约 150 次 provider 调用）为可接受基线；但耗时、调用数、token/成本三项必须对成功与失败两类运行都真实记录（失败运行的计数不得为 null）。
- 可维护性度量修正为：**整体源码行数净下降 + 不可达模块数归零 + 零引用配置量下降**（原口径"产品路径可达代码量"会被"只删不可达代码"绕过，已废弃）。
- 删除前置条件：先冻结基线快照与复算脚本，先通过效果与核心能力回归；分页、分批恢复、去重、失败语义、溯源列为**保留不变量**；并断言投影/五维比较/证书/verifier 等旧自证路径已删除或不可达。

### 结构契约与写权（T-003/T-006 + Grill G-001/G-002）
- 产物 frontmatter 必须与既有语义层契约一致；断言 `page_model = derived` 且带 `generated_by`（否则可能被既有流水线当作 `source` 清理）。
- 本期 KD 只写自己声明的路径，不改既有 CompanyBrain 正式页，也不修改停摆的自动化流水线；接管旧 `synthesize_*` 主题与在自动化规则中登记，移交流水线修复任务。
- 抽 10 页做结构与元数据校验，并让 gbrain 索引后按 slug 可检索；下游查询路径必须能定位答案与出处（按 slug 检索通过不等于下游可用）。

### 非目标负向检查
- 逐条核对 NG-001…NG-010 与延期项（OI-15/OI-21）未出现在本期实现中：不新增向量库/图数据库/服务化/前端/多格式输入，不保留自证质量机器，不修停摆流水线。

## 范围

本次是**规划任务**，当前范围是"把下一步改造方向与验收口径确认下来"：

- 交付物：本份 `decision-log.md`（方向、取舍、风险、非目标、延期、验收口径）与阶段事实。
- 覆盖内容：release4 产物效果与差距、项目架构/性能/可维护性审计、外部可复用做法调研、改造方向与简化取舍、
  **语义层的最终呈现形式与下游可消费性**（T-005 引入）。
- 用户流程/结果只记索引和验收影响，细节进入后续 spec；本阶段不写实现代码、不改产物、不重跑 provider。
- 已定方向（Round 1 + Round 2）：见「已选方向」；六类边界（用户流程/页面范围/数据状态/成功失败边界/非目标/延期）已全部收到用户真实答复或由事实回答，终态记录在 OI 大纲。
- 当前不确定性：仅剩实现层细节（页面清单、查询集题目、删除顺序），按用户选择留给 spec/plan 阶段，不属于方向未决。
- 非目标与延期见下两节。

## 完整用户旅程（build-prd 规划标准要求；本阶段补齐）

角色：**投料人**（用户本人，把 Confluence 导出的 Markdown 放进来）、**读者**（你自己或同事，在 Obsidian 里查产品知识）、**下游消费者**（技能层 / Agent 层 / 应用层，通过 `gbrain` 与语义层契约检索）、**维护者**（下一位改 KnowledgeDigest 的人）。

| # | 阶段 | 谁做 | 发生什么 | 成功的样子 | 失败/中断的样子 |
| --- | --- | --- | --- | --- | --- |
| J1 | 投料 | 用户 | 把 89 份 Confluence Markdown 放进输入目录，运行一条命令 | 命令接受输入并打印/写入本次运行的计划与预算 | 输入不是 Markdown：明确拒绝并说明；缺文件或空文件：记为已知状态而不是崩 |
| J2 | 读取与保真 | 系统 | 解析每份来源，拆出参考型区块（表格/参数/枚举/字段字典/URL/报错文案）与叙述型段落 | 每个区块带来源、指纹与行区间；参考型内容零丢失 | 无法解析的结构：显式标注，不静默降级为散文 |
| J3 | 语义编译 | 系统 | 生成页面：对齐既有 frontmatter 契约与命名，`[[wikilink]]` 双链，每条结论带原文定位 | 页面与既有 CompanyBrain 页同构；不存在无出处的结论 | 回不到原文：写成"原文未明确"并保留占位，失败不伪装成功 |
| J4 | 组织与导航 | 系统 | 生成入口页与分类入口，把每个已发布页接进入口 | 从入口页可达**每一个**已发布页，入口描述对页面有区分度 | 有页无入口或入口同质：判失败 |
| J5 | 发布 | 系统 | staging 校验 → 原子切换到语义层目录，保留上一可用版本 | 读者与 gbrain 只看到完整的新版本或完整旧版本 | 中断/取消/校验失败/越界写入：不留半成品，错误与调用计数保留 |
| J6 | 回滚 | 用户/系统 | 需要时把上一次发布撤回 | 一条命令回到上一可用版本，可查性不中断 | 回滚失败或留下混合版本：判失败 |
| J7 | 阅读与查询 | 读者 / 下游 | 在 Obsidian 里按入口找答案；下游通过 gbrain 检索页面 | 能定位到直接回答问题的页面并回到原文出处 | 只能找到原文堆积、内容与原文不符、或对比结论靠"对照未覆盖"：判失败 |
| J8 | 验收 | 用户 + 系统 | 用冻结快照 + 同一组真实问题逐题判定 | 留下可复跑的判定记录，能给出通过与失败 | 缺快照/缺问题集/缺逐题结果：验收结论无效 |
| J9 | 维护 | 维护者 | 改编译规则、加页面类型、修失败 | 整体源码行数净下降、不可达模块归零、产品路径仍跑通 | 需要同时改多套历史实现、或度量仍为 null：判失败 |

**旅程中的关键不变量**：不丢内容（参考型零丢失）、不伪装成功（无出处不得写成结论、失败必须显式）、可重复运行（同输入同结果）、可回滚（原子发布 + last-known-good）、单一生产者（同一主题只有一个生成器）。

## 非目标

- NG-001 不依赖 build-prd 补齐需求；需求收敛在本阶段完成。
- NG-002 主会话不做重读量取证；取证派子代理，主会话只收结论与证据引用（上下文守恒）。
- NG-003 不在本阶段改代码、改已发布产物、重跑 LLM/embedding provider。
- NG-004 不为了"看起来自研"而拒绝成熟开源做法；反之也不为引入而引入（**结论**：不整体引入任何外部项目，只把 LangExtract 的源字符区间对齐、GraphRAG 社区报告 prompt、RAGFlow 收缩拒绝与双链规范化列为候选参考）。
- NG-005 不把"机器自证绿灯"当作交付成功的证明（**结论**：删除投影/五维比较/证书/verifier，改为真实查询集判定）。
- NG-006 不在本阶段承诺 commit/merge/push/worktree cleanup 等不可逆交付动作。
- NG-007 不做问答/RAG 形态，不做前端或可浏览界面（用户 T-003/T-005 已选）。
- NG-008 不在本期引入向量库、图数据库或服务化部署（用户 T-003 = A 的直接含义；F-003 结论支持）。
- NG-009 不做多格式输入（PDF/Word/网页/GitLab）（用户 T-009 = A）。
- NG-010 不修停摆的每日自动化流水线、不改既有 CompanyBrain 正式页（用户 T-011 = A）；KD 只写自己声明的路径。

## 子任务规划建议（**建议，交 build-prd 冻结；用户已选 4 张方案**）

> 说明：make-decision 不产出 `tasks.md`。本节是给 build-prd 用的结果导向候选卡，每张卡写清「交付物 / 独立验收口径 / 依赖 / 最小读取集」。
> **粒度决定（用户真实回复）**：在 6 张（每张一个独立 oracle）与 4 张（合并）之间，用户选择 **4 张**。合并带来的取舍已登记为 RISK-009：①③ 两张的验收面变大、单张周期变长，"半张交付"不可验收。

| 卡 | 交付物 | 独立验收口径（不依赖别的卡完成） | 依赖 | 最小读取集 |
| --- | --- | --- | --- | --- |
| **K1 把知识做对**（参考保真 + 语义层页面） | ① 机器可读的「参考块清单」（表格/参数/枚举/字段字典/URL/报错文案 + 来源 + 行区间 + hash）；② 生成好的语义层知识页（既有契约 frontmatter、`[[wikilink]]` 双链、每条结论带原文定位） | 冻结全量清单逐块与原文比对零丢失；结构/元数据校验通过；**零"无出处结论"**；`page_model=derived` 断言；抽 3 页通读；越界写入负例 | 无（起点） | 本记录 T-003/T-006/T-007/T-014、D-003/D-004/D-009、F-001、F-004、E 报告契约事实、`CONTEXT.md` |
| **K2 入口与导航** | 入口页 + 分类入口，把每个已发布页接进入口 | 全量入口图：**零孤儿页** + 入口描述互不重复（对照基线：87/99 页无入口、入口同质） | K1 | 本记录 T-005/OI-17、F-001 导航实测、K1 的页面清单 |
| **K3 安全地交出去**（发布安全 + 真实查询集验收） | ① 原子发布 + 上一可用版本 + 失败可查（含失败运行的成本计数）；② 冻结快照 + 问题集 + 逐题判定记录 + 真实耗时/调用/token | 注入中断/取消/校验失败/越界四类负例；读者与 gbrain 只见到完整版本；回滚可用；判定记录可复跑且能给出通过与失败；三份冻结物齐备 | 无（可用 fixture / 冻结基线先跑通机制；对照验收需 K1/K2 产物） | 本记录 T-010/T-012/T-013/OI-19/OI-25/OI-26、F-002 的 `observed_calls=null` 缺陷 |
| **K4 瘦身且不丢能力** | 更小的代码库 + 能力迁移完成 | 整体源码净下降 + 不可达模块归零 + 零引用配置下降；保留能力（300 行分页、分批恢复、去重、失败语义、溯源）回归通过；旧自证路径已删除或不可达 | 独立（可与 K1–K3 并行；删除前置条件见验收「可维护性」节） | 本记录 T-004/D-005、F-002 的删除清单与最小实现清单、验收「可维护性」节 |

**串行链**：只有 **K1 → K2** 是硬串行；K3、K4 可并行或提前启动。
**写权边界**：不单独成卡——已在验收「结构契约与写权」节写成 K1 必须满足的硬断言（`page_model=derived`、写入 allowlist、越界负例）；接管旧 `synthesize_*` 主题与在既有自动化规则中登记，移交流水线修复任务（T-011）。

**需求→卡覆盖检查**：

| 原始需求 | 负责卡 / 处置 |
| --- | --- |
| R-001 效果确有实质问题 | K1、K3（用判定记录证伪或证实） |
| R-002 分析 release4 效果 | 已在本阶段完成（F-001/F-004） |
| R-003 与 CompanyBrain 比差距 | K3；差距结论已由 F-001 给出 |
| R-004 架构/性能/可维护性 | K4（结构与维护面）、K3（性能与度量） |
| R-005 外部开源是否有更好做法 | **明确排除**：F-003 覆盖 41 个候选，无一占据该产品位；只保留 3 个候选参考做法（D-009），不单独立卡 |
| R-006 改造方向：效果更好 + 更简单 | K1–K4 全体 |
| R-007 按 WorkflowHub 五阶段执行 | 流程约束，不立卡 |
| R-008 不跳阶段 / 不依赖 build-prd 补需求 | 流程约束（本阶段已完成需求收敛），不立卡 |
| R-009 六类边界梳理 | K2（页面范围）、K1（数据状态）、K3（成功失败边界）、非目标与延期已在本记录冻结 |
| R-010 上下文控制与子代理派发 | 流程约束，不立卡 |
| R-011 大白话 Talk/Grill | 流程约束，已在 T-001…T-014 与 G-001/G-002 执行，不立卡 |

## 风险与延期交接

| risk/deferred_id | 风险或延期内容 | 触发/后果 | 处理阶段/owner |
| --- | --- | --- | --- |
| RISK-001 | 不做架构收敛、继续在多套历史路径上叠加质量门，维护成本继续上升 | 每次改动继续牵动多套路径，改错与回归概率上升 | 后续 build-plan / 用户 |
| RISK-002 | 只追求"更简单"而砍掉可追溯能力，产物退化为不可信摘要 | 读者无法回到原文，知识库失去审计价值 | 本阶段约束 / 用户 |
| RISK-003 | 用少量样本得出"效果很好/很差"的结论 | 方向判断建立在抽样偏差上 | 本阶段调研方法 / 主会话 |
| RISK-004 | 外部项目调研停在链接与二手转述，未读原文 | 引入方案时才发现不匹配 | 调研步骤 R1–R3 / 主会话（已缓解：关键两条经 anysearch 一手复核） |
| RISK-005 | **用户选择全自动发布（T-010 = B）**：错误或有损内容会直接进入语义层并被下游技能/Agent/应用引用 | 一旦发生，错误知识会被下游放大；无人工闸门拦截 | 用户已明确接受；build-spec/plan 必须把"可回滚 + 可审计 + 失败不伪装成功"作为替代控制手段 |
| RISK-006 | 既有语义层流水线恢复时会 rename/unlink `Products/` 下页面；本期只定写权边界不修它 | KD 产物若写入同一棵树，恢复当日可能被改名或删除 | 写权边界（build-spec）+ 用户另开修复任务时同步检查 |
| RISK-007 | 对齐既有语义层契约意味着 KD 的输出受 `apply_formal_knowledge_metadata.py` 的规则支配（含 `page_model: source` 会被删） | 若 KD 产物被判成 `source` 类型，可能被既有流水线清理 | build-spec 必须显式声明产物的 `page_model` 与可写目录（已在验收标准写成硬断言） |
| RISK-009 | 子任务合并为 4 张后，K1 与 K3 的验收面变大、单张周期变长 | "半张交付"不可验收；出问题较难定位到具体能力 | 每张卡在 build-prd 里必须再拆出内部阶段与逐项 oracle（不增加卡数） |
| RISK-008 | **规划缺口（用户指出后已补）**：本决策记录在补写前没有「完整用户旅程」，也没有任何子任务分解，按 build-prd 的规划标准不合格 | 下游无法据此排卡与分工，方向再好也落不了地 | 已补「完整用户旅程」与「子任务规划建议」两节；最终拆卡由 build-prd 与用户确认 |

### 质量边界

- 质量事实：当前 `in_progress`；`stage-runtime status` 报告 12 项质量谓词缺失，均为真实待办。
- 推进资格：可以继续在本任务内 Talk、调研、起草与修复。
- 完成判据：Talk 三轮 + 调研 + Grill + 两次独立审查 + 用户真实确认 + interaction aggregate。
- 不可逆授权边界：本阶段不产生 commit/merge/push/cleanup 授权。

## UI applicability

三个输入事实按证据合并（不按调用方标签）。**用户在 Talk Round 1（T-005）确认生成页面是一等交付面**，
但明确的是"内容与结构层面的交付契约"，不是浏览器界面：本项目交付的是 Python 命令行工具与本地 Markdown
知识文件，读者界面由第三方编辑器（Obsidian 类）提供，本任务不开发也不修改任何前端、路由或交互组件。
因此三项来源一致收敛为 `non_ui`；页面/阅读面的一等地位记录在 OI-17 与 OI-22，并由 `## 范围` 与
`## 验收标准` 以内容契约方式约束，不因此产生前端设计合同。若用户后续要求可浏览的应用界面，则重算本事实。

```json
{
  "result": "non_ui",
  "sources": {
    "raw_requirement": {
      "applicability": "non_ui",
      "fact": "用户 T-005 确认生成的页面算一等交付面，并要求梳理完整用户流程、页面范围与最终呈现形式；该要求指向内容与结构契约，未要求开发或修改任何浏览器界面、路由或交互组件"
    },
    "project_inventory": {
      "applicability": "non_ui",
      "fact": "KnowledgeDigest 是 Python 命令行工具：无前端技术栈、无路由、无交互组件；用户可见产物是写入本地知识库的 Markdown 文件，由外部编辑器打开"
    },
    "planned_or_changed_frontend_fact": {
      "applicability": "non_ui",
      "fact": "当前已接受方向为规划任务：产出决策与验收口径，不改任何前端或界面实现"
    }
  },
  "reason": "三项来源一致为 non_ui：产品是 CLI + Markdown 产物，读者界面由第三方编辑器提供"
}
```

## 收敛检查

| 维度 | 用户答案 | 事实/材料引用 | 可执行验收 |
| --- | --- | --- | --- |
| goal | 用户回答 T-001：先把读者效果做对，再删复杂度 | decision-log.md#核心目标 / R-006 | 验收时分别测两件事：效果判据先达成（问题集可答且有出处），复杂度净下降可测（可达代码量与配置量下降） |
| scope | 用户回答 T-009/T-010/T-011：只做 Confluence Markdown、全自动发布不设人工确认、只定写权边界不修每日流水线 | decision-log.md#范围 / R-009 | 验收：接口只接受 Markdown 输入；一次运行无需人工介入；写入范围可被检查且不溢出到已声明路径之外 |
| solution | 用户回答 T-003/T-004/T-006：保持离线编译形态、保留骨架砍掉历史分支、KD 直接产出语义层页面；取舍：接受既有语义层的 frontmatter/命名/wikilink 约束，以换取产物可被 gbrain 与下游 Agent 直接消费；被拒方案：问答/RAG 为主、两者并存、推倒重写、只做增量修补、保留自有格式另加导出层；未决项：具体页面清单留到 spec 阶段 | decision-log.md#已选方向 / R-006 | 验收：抽 10 页产物做结构与元数据校验通过，gbrain 索引后按 slug 可检索；同一次运行内不含被拒方案或导出层 |
| acceptance | 用户回答 T-002/T-008/T-009/T-012/T-013/T-014：及格线=能替代 CompanyBrain 查产品知识；验收方式=冻结快照 + 同题逐题对比；成本沿用现有量级但度量必须补齐；证据零容忍（无出处不得写成结论） | decision-log.md#验收标准 / R-003 | 场景：目标读者带一组真实产品问题分别查两套产物；数据来源：89 份 Confluence Markdown 原始资料 + CompanyBrain 冻结快照；通过：能定位到直接回答问题的页面并能回到原文出处，且不存在无出处的结论；失败：找不到、只找到原文堆积、内容与原文不符、或对照结论依赖"对照未覆盖" |

## OI 大纲（唯一当前版本 · outline_version = v1.2 · Round 2 后加入 direction-advice 修补项）

> 身份绑定：全部 OI 绑定 `task_id = task6-effect-gap-and-architecture-reset`、`outline_version = v1.2`（v1 为研究前初建版本，Round 1 后升 v1.1，Round 3 后升 v1.2；当前有效版本以本节标题与每条 OI 记录内的 `outline_version` 为准）。
> 状态取值只用 `open` / `confirmed` / `deferred` / `not_applicable`。本表在 step 1/2 建立时全部为 `open`；
> Talk 结束后回填终态字段（`selected_disposition`、`impact_dimensions`、`requires_user_decision`、`visible_group_id`）。
> `requires_user_decision` 语义：该 OI 是否必须由用户裁决。由仓库事实或已确认证据直接回答的记 `false`。

### Framework nodes

| node_id | framework_node | oi_ids | empty | reason |
| --- | --- | --- | --- | --- |
| N-background | background | OI-01, OI-02 | false |  |
| N-problem | problem | OI-03, OI-04, OI-05 | false |  |
| N-goal | goal | OI-06, OI-07 | false |  |
| N-solution | solution | OI-08, OI-09, OI-10, OI-11, OI-22, OI-24 | false |  |
| N-acceptance | acceptance | OI-12, OI-13, OI-23, OI-25, OI-26, OI-27 | false |  |
| N-extension | extension | OI-14, OI-15 | false |  |

### Fixed categories

| category | oi_ids | empty | reason |
| --- | --- | --- | --- |
| complete_user_flow | OI-16 | false |  |
| page_scope | OI-17, OI-22 | false |  |
| data_state | OI-18, OI-24 | false |  |
| success_failure_boundary | OI-19, OI-23, OI-25, OI-26, OI-27 | false |  |
| non_goals | OI-20 | false |  |
| deferred | OI-21 | false |  |

### OI 记录（每项一个可独立处置的收敛项 · 终态已回填）

```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-01
category: complete_user_flow
source: "R-002 / fact-ref"
question: "release4 这次真实运行到底产出了什么（来源数、页面数、页面类型、审计面）？"
status: confirmed
selected_disposition: "answered_by_fact: 89 来源 → 99 Reader 页（87 来源页 + 12 投影页）+ Audit，页面类型 positioning/operation/concept/diagnosis/experience"
evidence: "quality/evidence/research/drafts/A-effect-comparison.md"
acceptance: "可复核：bundle/_audit/directory-manifest.json 与 products/** 的页数、类型分布逐项对账一致"
counterexample: "若某页类型或来源数与 manifest 不符即判该事实不成立"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-02
category: data_state
source: "R-004 / fact-ref"
question: "KnowledgeDigest 当前真实规模有多大，一次真实运行的真实成本是多少？"
status: confirmed
selected_disposition: "answered_by_fact: 产品路径 7 模块/11,441 行；src 45,179 行、33.1% 无入口；配置 17.56 MiB 中约 16.87 MiB 零引用；一次运行 150 次 provider 调用（0 重试），耗时/token 不可得"
evidence: "quality/evidence/research/drafts/B-architecture-audit.md"
acceptance: "可复核：AST 可达性与五通道配置扫描可重跑；provider_calls 可从 run-result.json 读取"
counterexample: "若重跑得到不同的可达性或调用计数即判该事实不成立"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-03
category: success_failure_boundary
source: "R-001 / R-002"
question: "release4 产物对读者是「能用的知识库」还是「有损的摘抄」，差距的性质是什么？"
status: confirmed
selected_disposition: "answered_by_fact: 产物类型不同——是「89 篇文档的场景化摘要索引」，不是「面向检索的知识库」；参考型内容（表格 2,943→0、URL 708→1、截图 326→0）整体丢失，但行号溯源真实"
evidence: "quality/evidence/research/drafts/A-effect-comparison.md"
acceptance: "可复核：对同一问题集分别查 bundle 与 CompanyBrain，看能否定位到答案与出处"
counterexample: "若能在 bundle 中查到参考型答案（表格/参数/URL）即判该结论被推翻"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-04
category: page_scope
source: "R-004"
question: "现有架构与代码里，哪些复杂度是交付必需的，哪些是可以直接删除的？"
status: confirmed
selected_disposition: "answered_by_fact: 必需约 4,000–6,000 行（读/指纹/分组/抽证据/分页/导航/原子写/溯源）；可删：task5_runtime 3,392 行、Task2/3/4 reader 栈约 8,586 行、惰性配置 16.85 MiB、近重复 specs"
evidence: "quality/evidence/research/drafts/B-architecture-audit.md"
acceptance: "可复核：删除后产品路径仍能跑通同一次 digest，且离线能力（300 行分页/分批恢复）有明确归属"
counterexample: "若删除导致产品路径无法运行或丢失仅有实现的能力即判该结论不成立"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-05
category: success_failure_boundary
source: "R-001 / fact-ref"
question: "项目自评「全部比较原子 KD_WIN、released」与实际读者效果是否矛盾？"
status: confirmed
selected_disposition: "answered_by_fact: 不矛盾但解释范围有限——技术层零水分（指纹/坐标可复算），自述层低（规格记 not_released、产物记 released 且无追认；77.9% 原子只是 non_regression，比较只引用 CompanyBrain 17 个页面）"
evidence: "quality/evidence/research/drafts/D-coverage-fidelity.md"
acceptance: "可复核：重算 60 条 quality_rows 的 KD_WIN 分布与所引 CompanyBrain 页面集合"
counterexample: "若存在被漏记的 strict_improvement 证据或未披露的比较范围即判该结论不成立"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-06
category: complete_user_flow
source: "T-001（用户真实回复）/ R-006"
question: "这次改造的第一目标是什么——读者效果优先、项目瘦身优先，还是两者同时但要分先后？"
status: confirmed
selected_disposition: "用户选择 A：先把读者效果做对，再删复杂度"
evidence: "decision-log.md#Talk T-001（host 问答工具真实回复）"
acceptance: "验收时能证明「效果判据先达成、复杂度净下降随后」，两项分别可测"
counterexample: "若改造以牺牲效果换复杂度下降，即违反本决定"
impact_dimensions: [goal]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-07
category: success_failure_boundary
source: "T-002（用户真实回复）/ R-003"
question: "成功判据是什么——产物要能替代 CompanyBrain 用于查公司产品知识，还是只做补充？"
status: confirmed
selected_disposition: "用户选择 A：要能替代 CompanyBrain 查产品知识（及格线）"
evidence: "decision-log.md#Talk T-002"
acceptance: "在同一组真实产品问题上，产物可查性不劣于 CompanyBrain 且能回到原文出处"
counterexample: "若在约定问题集上产物明显劣于 CompanyBrain 即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-08
category: page_scope
source: "T-003 + T-006（用户真实回复）/ R-006"
question: "产品形态与最终产物形态是什么？"
status: confirmed
selected_disposition: "用户选择 A + A：保持「离线编译成 Markdown 知识库」的形态；且 KD 直接产出用户既有语义层的页面（同一套 frontmatter、目录命名与 [[wikilink]]）"
evidence: "decision-log.md#Talk T-003、T-006"
acceptance: "产物落在语义层目录树、frontmatter 通过既有元数据规则校验、gbrain 能索引到这些页"
counterexample: "若产物需要额外转换层才能被语义层消费，即违背本决定"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-09
category: complete_user_flow
source: "T-004 + T-011（用户真实回复）/ R-006"
question: "旧架构怎么处置，已发布的知识页与托管合同哪些必须不破？"
status: confirmed
selected_disposition: "用户选择 A + A：保留骨架、砍掉历史分支（含自证质量面与已结束任务的专用路径）；本任务只把「谁写哪棵树」的写权边界写死，不修停摆的每日流水线；Grill G-001 进一步定死：同一主题只允许一个生产者，KD 逐步接替旧 synthesize_* 脚本，接管前先只读对比并在自动化规则中登记"
evidence: "decision-log.md#Talk T-004、T-011"
acceptance: "删除后产品路径可运行；写权边界成文且可检查（KD 只写声明路径，不写既有 CompanyBrain 正式目录）"
counterexample: "若删除破坏了仍在用的真能力，或 KD 写入范围溢出到未声明路径，即判失败"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-10
category: deferred
source: "R-005 / F-003"
question: "外部开源项目里，哪些做法与模块值得引入，哪些会引入新的复杂度而不值得？"
status: confirmed
selected_disposition: "answered_by_fact: 不整体引入任何外部项目（无一占据该产品位）；只把 3 个具体做法列为候选参考——LangExtract 的源字符区间对齐、GraphRAG 社区报告的合成 prompt、RAGFlow 的收缩拒绝与双链规范化；向量库/图数据库/chat-only 形态明确不引入"
evidence: "quality/evidence/research/drafts/C-oss-landscape.md；主会话经 anysearch 复核 RAGFlow 与 LangExtract 两条一手来源"
acceptance: "若采纳任一做法，需能指出它替换掉自研的哪一块并有对应验收；不引入项不得出现在实现里"
counterexample: "若为引入而引入（新增服务/数据库依赖且无对应验收）即判违背本决定"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-11
category: success_failure_boundary
source: "T-008（用户真实回复）/ R-009"
question: "质量控制面怎么改——保留自证门、精简，还是改成真实评测？"
status: confirmed
selected_disposition: "用户选择 A：删掉自证机器（投影/五维比较/证书/verifier），改成固定一组真实问题 + 真实判定"
evidence: "decision-log.md#Talk T-008"
acceptance: "存在一份可复跑的查询集与判定记录，且它能对产物给出通过与失败"
counterexample: "若验收仍依赖机器自评绿灯而无法对读者效果给出判断，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-12
category: success_failure_boundary
source: "T-008 + T-009（用户真实回复）/ R-009"
question: "用什么场景和语料验收这次改造？"
status: confirmed
selected_disposition: "用户选择：以真实查询集验收（问题集在 build-spec 由用户出题共建）；语料限定为 89 份 Confluence Markdown（实测 89 份 .md，另有 2 个 .DS_Store 不计入）这一批，并绑定冻结清单与 hash"
evidence: "decision-log.md#Talk T-008、T-009"
acceptance: "同一问题集在改造前后各跑一次，逐题记录能否定位答案与出处"
counterexample: "若问题集无法区分改造前后（全过或全不过）即判验收无效"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-13
category: success_failure_boundary
source: "R-009 / F-001"
question: "什么情况必须判定失败（不伪装成功），失败之后怎么恢复？"
status: confirmed
selected_disposition: "answered_by_fact: 缺来源/缺证据/引用不可达/超出声明写入边界/资料未明确被写成结论——都必须判失败或显式标注；恢复方式是按来源重跑并在状态中说明，不用绿灯掩盖"
evidence: "quality/evidence/research/drafts/D-coverage-fidelity.md"
acceptance: "构造一个缺来源或越界的输入，运行必须以失败或显式标注收场"
counterexample: "若同类输入被静默发布成正常结果即判失败"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-14
category: data_state
source: "T-009（用户真实回复）/ R-009"
question: "输入范围只服务 Confluence 导出的 Markdown，还是要吃 PDF/Word/网页等？"
status: confirmed
selected_disposition: "用户选择 A：本期只做 Confluence Markdown 这一条路"
evidence: "decision-log.md#Talk T-009"
acceptance: "接口与实现只接受 Markdown 输入；遇到其它格式明确拒绝并说明"
counterexample: "若为兼容多格式而在本期引入抽取层分支即判超出范围"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-15
category: deferred
source: "R-009 / T-011"
question: "哪些能力明确延期，触发条件是什么？"
status: confirmed
selected_disposition: "answered_by_fact: 延期项为多格式输入、图形/浏览界面、问答入口、每日自动化流水线修复、gbrain 评测集扩容；触发条件分别是主线验收通过、或用户另开任务"
evidence: "decision-log.md#Talk T-009、T-011"
acceptance: "每项延期在后续阶段有 owner 与触发条件，且本期实现不出现其半成品"
counterexample: "若延期项以「顺手做了」的形式进入本期实现即判违背本决定"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-16
category: complete_user_flow
source: "T-010（用户真实回复）/ R-009"
question: "完整用户旅程是什么，要不要保留人工确认环节？"
status: confirmed
selected_disposition: "用户选择 B：全自动，不设人工确认（已接受风险：错误内容会直接进入知识库并被下游引用）"
evidence: "decision-log.md#Talk T-010"
acceptance: "整条链路从投料到发布无需人工介入即可完成一次运行"
counterexample: "若发布流程被单点人工确认阻塞，即与用户选择不符（这是用户已接受的风险，不作为缺陷，但必须在此登记）"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-17
category: page_scope
source: "T-005（用户真实回复）/ R-009"
question: "页面范围指什么——读者入口在哪、生成页面的阅读面算不算一等交付面？"
status: confirmed
selected_disposition: "用户选择 A：生成页面算一等交付面，要按读者路径验收"
evidence: "decision-log.md#Talk T-005"
acceptance: "存在可执行的读者路径检查：从入口页能到达每一个已发布页，且入口对页面有区分度"
counterexample: "若仍有已发布页没有入口，或入口描述对多页同质，即判失败"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-18
category: data_state
source: "R-009 / F-001"
question: "数据来源与状态怎么定义——来源状态、重复来源、内容为空、资料未明确、增量更新各自算什么状态？"
status: confirmed
selected_disposition: "answered_by_fact: 沿用并收紧现有语义——ready/known_empty/duplicate_alias/audit_only 是合法状态；「资料未明确」必须显式标注且不得进入事实分母；增量更新只新增或更新，不删除旧页"
evidence: "quality/evidence/research/drafts/A-effect-comparison.md、D-coverage-fidelity.md"
acceptance: "对每类状态构造样例输入，产物中状态与正文一致"
counterexample: "若「资料未明确」被写成结论、或重复来源被发成两页，即判失败"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-19
category: success_failure_boundary
source: "R-009 / F-002"
question: "成功/失败/取消/重试/恢复的边界是什么，中断后重跑会不会产生半个知识库？"
status: confirmed
selected_disposition: "answered_by_fact: 成功=整包发布且状态可查；失败/取消必须保留真实错误与调用计数（现 publisher.py:113 把失败调用数写成 null，属于要修的缺陷）；恢复=按来源重跑且不叠加半成品"
evidence: "quality/evidence/research/drafts/B-architecture-audit.md"
acceptance: "中断一次运行，检查状态文件与知识库不出现半成品且失败计数不为 null"
counterexample: "若失败运行仍显示成功、或失败调用计数被写成 null，即判失败"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-20
category: non_goals
source: "R-008 / R-009 + T-009/T-010/T-011"
question: "明确不做什么（非目标）？"
status: confirmed
selected_disposition: "answered_by_fact + 用户选择：不做问答/RAG 形态、不做前端界面、不引入向量库或图数据库、不做多格式输入、不修每日流水线、不保留自证质量机器（见非目标 NG-001…NG-010）"
evidence: "decision-log.md#非目标"
acceptance: "评审本次实现时逐条核对非目标未被触碰"
counterexample: "若任一非目标能力出现在本期实现中即判范围失控"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-21
category: deferred
source: "T-011（用户真实回复）"
question: "明确延期做什么，owner 与触发条件是什么？"
status: confirmed
selected_disposition: "用户选择 A：停摆的每日语义层流水线只定写权边界，修复另开任务"
evidence: "decision-log.md#Talk T-011"
acceptance: "写权边界成文；另开任务的触发条件被登记（需要恢复每日导入时）"
counterexample: "若本期直接改动该流水线或其既有页面，即判越界"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-22
category: page_scope
source: "T-006（用户真实回复）/ R-006"
question: "产物的最终呈现形式是什么——只给人读，还是同时作为语义知识层被下游技能/Agent/应用消费？"
status: confirmed
selected_disposition: "用户选择 A：KD 直接产出语义层的页面——同一套 frontmatter（type/page_model/tier/trust/source_status/quality_status/scope/product/section/generated_by/tags）、同一套目录与命名、[[wikilink]] 双链，使 gbrain 与下游 agent 可直接消费；Grill G-002 补充：允许新增一个溯源字段，但必须在既有元数据权威中登记，字面名与取值形状由 build-spec 定（OPEN-008）"
evidence: "decision-log.md#Talk T-006（含重问后的具体产物样例）"
acceptance: "抽 10 页产物做结构与元数据校验，并让 gbrain 索引后按 slug 可检索"
counterexample: "若产物需要额外转换层才能被语义层或 gbrain 消费，即判违背本决定"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-23
category: success_failure_boundary
source: "T-005 / T-006（用户真实回复）"
question: "怎么验证「语义层对下游好用」——用什么下游消费者、什么任务、什么证据算通过或失败？"
status: confirmed
selected_disposition: "answered_by_fact + 用户选择：以「下游能检索并回答问题」为验收——查询集由用户出题，判定记录逐题给出能否定位答案与出处；不用机器自评替代"
evidence: "decision-log.md#Talk T-006、T-008"
acceptance: "同一问题集在改造前后各跑一次并留下可复跑的判定记录"
counterexample: "若验收只给出绿灯而无法回答「读者/下游能不能用」即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-24
category: data_state
source: "T-007（用户真实回复）/ direction-advice blocking finding"
question: "参考型内容（表格/参数/枚举/字段字典/URL）在产物中如何保留、退化与判失败？"
status: confirmed
selected_disposition: "用户选择 A：逐字保留并按原文结构落页，只对叙述性段落做语义合成；退化（无法保留结构）必须显式标注而不是静默降级为散文"
evidence: "decision-log.md#Talk T-007；A 报告实测原始表格行 2,943 → 产物内容型表格 0"
acceptance: "抽 10 页含参考型内容的产物，表格/参数/URL 与原文逐项一致且可溯源；无法解析时必须显式标注"
counterexample: "若产物把表格改写成散文、或静默丢弃参考型内容而不标注，即判失败"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R2
```

```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-25
category: success_failure_boundary
source: "T-012（用户真实回复）/ direction-advice finding F-416a6e48b076"
question: "与 CompanyBrain 的比较口径与及格阈值怎么定——用哪个冻结基线、比较单元、分母、对照侧没有内容时怎么算？"
status: confirmed
selected_disposition: "用户选择 A：冻结 CompanyBrain 快照 + 同一组问题逐题对比；比较单元=单题；对照侧本来没有对应内容时记「对照未覆盖」，不得计为我方优势；比较证据必须可复算"
evidence: "decision-log.md#Talk T-012；F-001 复核已证明旧口径把 50 个 strict_improvement 全部建立在对照侧 absent 之上"
acceptance: "存在一份冻结快照 ID + 查询集 + 逐题对照记录；任何「优于对照」的结论都能指出对照侧对应内容或明确标注未覆盖"
counterexample: "若比较结论依赖对照侧 absent、或没有冻结快照导致不可复算，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R3
```

```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-26
category: success_failure_boundary
source: "T-013（用户真实回复）/ direction-advice finding F-d832b4b4f366"
question: "架构/性能/可维护性的基线与最低目标怎么定——端到端耗时、调用与重试次数、可接受成本上限、可维护面目标？"
status: confirmed
selected_disposition: "用户选择 A：沿用现有量级（一次运行约 150 次 provider 调用）作为可接受基线，不设更严上限；但必须把耗时、调用数、token/成本真实记录（含失败运行），不得再出现 null"
evidence: "decision-log.md#Talk T-013；F-002 实测 run-result.json 的 provider_calls=150，而 publisher.py:113 在失败路径把 observed_calls 硬编码为 null"
acceptance: "成功与失败两类运行都能读到耗时/调用数/token 三个字段；可维护面以「产品路径可达代码量与零引用配置量下降」度量"
counterexample: "若失败运行的度量仍为 null、或新增了无法度量成本的能力，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R3
```

```yaml
task_id: task6-effect-gap-and-architecture-reset
outline_version: v1.2
oi_id: OI-27
category: success_failure_boundary
source: "T-014（用户真实回复）/ direction-advice finding F-9f502e3d950b"
question: "证据完整性下限怎么定——claim 级溯源覆盖率、来源为空或无法定位时必须判失败还是显式标注？"
status: confirmed
selected_disposition: "用户选择 A：零容忍——每一条结论都必须能回到原文具体位置；回不到就不许写成结论，改为显式标注「原文未明确」并保留占位；不采用百分比门槛"
evidence: "decision-log.md#Talk T-014；D 报告实测 73.4% 的 claim 没有 claim 级行号，而页面里同时存在 72 处「原始资料未明确」标注"
acceptance: "对产物做一次机械检查：不存在既没有原文定位、也没有显式「原文未明确」标注的结论行；构造一条无法定位的输入必须以标注或失败收场"
counterexample: "若出现无出处的结论句、或把无法定位的内容改写成肯定句，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R3
```

## Talk

| talk_id | 问题/选项 | 后果/风险 | 用户选择/原文 | 队列变化 | source/evidence |
| --- | --- | --- | --- | --- | --- |
| T-001 | Q1 目标排序：A 先效果后瘦身 / B 先瘦身后效果 / C 只要效果 | A：改动集中在主线；风险瘦身延后。B：项目快速变简单；风险丢真能力。C：短期改动小；风险继续在多套路径里改 | **A 先把读者效果做对，再删复杂度** | 队列 4 项 → 已答 1，剩 3 | host 问答工具真实回复（本轮 ask→wait→reply→resume） |
| T-002 | Q2 成功判据：A 替代 CompanyBrain 查产品知识 / B 做补充索引层 / C 只比现在好 | A：标准最硬；风险要多轮迭代。B：容易先赢；风险停在半成品。C：最易通过；风险重复「自评全胜、实际没用」 | **A 要能替代 CompanyBrain 查产品知识** | 剩 2 | 同上 |
| T-003 | Q3 产品形态：A 离线编译 Markdown / B 问答 RAG 为主 / C 两者都要 | A：延续资产与阅读习惯；风险不解决即时提问。B：查询最直接；风险引入向量库与服务化。C：覆盖广；风险两头不精 | **A 保持离线编译成 Markdown 知识库** | 剩 1 | 同上 |
| T-004 | Q4 旧架构处置：A 保留骨架砍历史分支 / B 推倒重写 / C 只做增量修补 | A：可控且可复用；风险删错伤真能力。B：最简洁；风险重走边界坑。C：风险最低；风险复杂度继续上升 | **A 保留骨架、砍掉历史分支** | 剩 0，Round 1 结束 | 同上 |
| T-005 | Q5 页面阅读面：A 算一等交付面要逐页验收 / B 只当文本输出 / C 算但清单后置 | A：可按「读者能否找到」判成败；风险验收工作量大。B：进度快；风险重演「内容在但找不到」。C：先定原则；风险方向与页面形态脱节 | **A（页面算一等交付面）**，并补充真实需求：「原始文档属于数据层，我现在建的属于语义知识层，往后其他的人会在我的语义知识层上面建立技能和 agent 层和应用层，所以为了让企业的 skill、agent 和应用更方便，现在的 KnowledgeDigest 到底应该如何改？最终结果应该是怎样的呈现形式？有没有类似的开源项目可以减少开发工作提高我的最终产物质量？」 | **新增 OI-22 / OI-23**，outline v1 → v1.1；Round 2 恢复后重排 | 同上（用户原话逐字保留） |

| T-006 | Q6 产物归属：A KD 直接产出语义层页面 / B 保留自有格式+导出层 / C 先不定 | A：下游立即可用；风险接受既有契约约束。B：KD 内部自由；风险两套格式漂移。C：快速；风险核心问题无人拍板 | 用户首次回复："这个问题我不懂，需要你重新解释后果，主要是最终产物会变成什么样？" → 主会话按歧义校正规则补充**具体产物样例**（同一段资料在 A/B 下各长什么样、落在哪个目录、谁能消费）后重问 → **用户选择 A：KD 直接产出语义层的页面** | 新增/关闭 OI-22 的核心轴；队列重排 | host 问答工具真实回复（两轮） |
| T-007 | Q7 参考型内容：A 逐字保留+只合成叙述 / B 模型重写但强制不丢字段 / C 参考数据单独成字典页 | A：补上查参数能力；风险页面变长。B：好读；风险已实测会丢。C：正文干净；风险多跳一次 | **A 参考内容逐字保留，只对叙述做合成** | — | 同上 |
| T-008 | Q8 质量验收：A 自证机器换真实查询集 / B 精简为硬事实 / C 全部保留 | A：直接对效果；风险需用户出题。B：成本降；风险仍不证明可用。C：不动；风险重复"全胜但没用" | **A 自证机器换成真实查询集验收** | — | 同上 |
| T-009 | Q9 输入范围：A 只做 Confluence Markdown / B 同时接多格式 / C 只留接口 | A：集中火力；风险暂不支持其它格式。B：覆盖广；风险抽取层拖垮主线。C：主线轻；风险空抽象 | **A 先只做 Confluence Markdown** | — | 同上 |
| T-010 | Q10 人工环节：A 低风险自动+高风险人工 / B 全自动 / C 全量人工 | A：兼顾速度与安全；风险需人看队列。B：最省人力；风险错误直接进库被下游引用。C：最可控；风险用户成瓶颈 | **B 全自动，不设确认**（与主会话推荐不同，属用户明确选择；风险已登记 RISK-005） | — | 同上 |
| T-011 | Q11 停摆流水线：A 只定写权边界，修复另开任务 / B 纳入本任务一起修 / C 暂不处理 | A：范围清楚；风险风险被推迟。B：一次协同好；风险范围变大。C：范围最小；风险继续基于过期数据做判断 | **A 只定写权边界，修复另开任务** | — | 同上 |

| T-012 | Q12 对照口径：A 冻结快照+同题逐题对比 / B 只做自己前后对比 / C 只做人工总评 | A：可复算、可被打破；风险要出题与记录。B：省事；风险重复自证路线。C：快；风险结论不可复算 | **A 冻结快照 + 同题逐题对比** | 新增 OI-25 并收敛 | host 问答工具真实回复 |
| T-013 | Q13 成本底线：A 沿用现有量级但补齐度量 / B 设硬上限超了判失败 / C 成本不重要 | A：不阻塞且首次有成本账；风险短期不省钱。B：防失控；风险长批次直接失败。C：效果优先；风险每改一次付同样的钱 | **A 沿用现有量级，但把度量补齐** | 新增 OI-26 并收敛 | 同上 |
| T-014 | Q14 证据下限：A 零容忍无出处不得写成结论 / B 设覆盖率下限 / C 只要页面级出处 | A：一句话可判定；风险页面多出"原文未明确"标注。B：可量化；风险少写结论即可抬比例。C：最省事；风险放弃可核对性 | **A 零容忍：无出处不得写成结论** | 新增 OI-27 并收敛 | 同上 |

Talk 生命周期（每轮独立回放 `ask → wait → reply → resume → re-rank`）：

| round | 状态 | 问题卡 | 等待 | 用户回复 | 恢复 |
| --- | --- | --- | --- | --- | --- |
| 1 | completed | Q1–Q5 独立问题批次（每题一个决策轴，2–3 互斥选项 + 推荐 + 后果 + 风险） | 已暂停等待 | T-001…T-005 真实回复（Q5 为选项 A + 自由文本） | 已 resume，重排出含语义层轴的 Round 2 队列 |
| 2 | completed | Q6–Q11 独立问题批次（产物归属/参考内容/质量验收/输入范围/人工环节/既有流水线） | 已暂停等待 | T-006…T-011 真实回复；其中 T-006 用户表示"不懂、要重新解释后果" | 已按歧义校正规则重问 T-006（附具体产物样例）并收到真实回复 A，再 resume |
| 3 | completed | Q12–Q14 独立问题批次（对照口径/成本底线/证据下限），输入含红蓝 findings 争议清单 | 已暂停等待 | T-012…T-014 真实回复 | 已 resume；本轮无 high/medium 待答方向问题，Round 3 收敛 |

Round 2 之后的剩余队列：无 high/medium 待答方向问题（六类边界与四个方向轴均已收敛）；Round 3 只用于处理方向建议（direction-advice）产生的红/蓝争议与剩余风险。

## 调研

| research_id/source | 调研重点 | 关键事实 | 处理状态 | 关联 D |
| --- | --- | --- | --- | --- |
| F-001 | release4 产物 vs CompanyBrain 的效果差距（子代理 A，报告 406 行） | 差距分级=**差距明显**。①参考型内容全灭：原始表格行 2,943→**0**、截图 326→**0**、唯一 URL 708→**1**；②溯源"真但不可携带"：2,280/2,280 行号引用有效、14 条抽样全对，但 `Audit.md` 22,546 行（占全包 73.5%）只给行号+sha256，0 个原文引用、0 个来源 URL、包内无原始文件；③`README.md:11` 指向不存在的 `_audit/sources.jsonl`/`evidence.jsonl`；④导航无区分度：95/99 页正文是同一模板问句，`products/goinsight/index.md:9-23` 15 行描述全同；⑤人工报告「120/120 KD_WIN」只引用 CompanyBrain 的 17 个页面（快照 1,347 文件），50 个 strict_improvement 全依赖 `cb_status=absent`，DIM-05 判断与实测方向相反；⑥同知识多页矛盾（`应用添加与订阅操作指南.md:35` vs `应用添加与订阅管理.md:35`，源文件去图相似度 0.986 未被判重）。公平项：known_empty、duplicate_alias 声明属实，断链 0、超长页 0、空页 0、锚点完整 | completed（报告：`quality/evidence/research/drafts/A-effect-comparison.md`） | D-001, D-002 |
| F-002 | 当前代码/配置/运行成本审计（子代理 B，报告 417 行） | ①产品路径仅 7 模块 / 11,441 行；`src/` 共 55 模块 / 45,179 行，其中 **16 模块 / 14,951 行（33.1%）无入口可达**；②两套完整实现并存：旧 S1–S6（`pipeline.py`，仅 `--no-llm` 可达）vs `compiler.py` 8,058 行（`_build_bundle` 单函数 790 行 / CC 186）；③「每页 ≤300 行」在新产品路径零实现（`compiler.py`/`quality.py`/`publisher.py` 无 300），仅旧 `page_layout.py` 有；④`config/` 74 文件 17.56 MiB，44 个 / 16.87 MiB 零命中，37 个全惰性，`task4-companybrain-mapping-*` 14 文件 15.79 MiB（v11 与 v12 字节相同）；⑤3 个 import 环；⑥文档 38,552 行 = src 的 0.853×，`specs/archive` 占 91.19%；⑦`publisher.py:113` 把 failure 收据 `observed_calls` 硬编码为 null，两次失败运行约 300 次 provider 调用无账；⑧真实运行：150 次 provider 调用（137 LLM + 13 embedding），预算 300、计划 177、重试 0；耗时/token/成本**结构性缺失**（自有采集器写 `status:"missing"`） | completed（报告：`quality/evidence/research/drafts/B-architecture-audit.md`） | D-003 |
| F-003 | 外部开源项目与可复用部分（子代理 C，报告 438 行） | 覆盖 41 个候选（表内 62 行 / 65 个仓库条目）：**没有任何项目直接占据「原始文档→可读+可追溯+可导航 Markdown 知识页」这个产品位**；唯一真做页面编译的 RAGFlow 在 prompt 中明文禁止页内引用（主会话经 anysearch 读一手源码确认）；最值得借的是 LangExtract 的「输出→源字符区间」对齐（Apache-2.0，但默认把定位失败项标为 `char_interval=None` 并建议调用方过滤，采用时必须升级为硬门禁） | completed（报告：`quality/evidence/research/drafts/C-oss-landscape.md`） | D-009 |
| F-004 | 来源覆盖/保真 + 历史「声称 vs 事实」（子代理 D，报告 361 行） | 磁盘实为 **89 份 .md**（另 2 个 .DS_Store）；与产物 source-status 双向差集 0/0、无重复；89/89 raw_hash 与行数、10,349 条 Audit 坐标 sha256 全部独立复算通过；15 页 212 条 claim 无改写、无幻觉；但 73.4% 的 claim 没有 claim 级行号，10 份文件 1,072 条可操作行中 46% 在产物无对应；**3 条声称与产物直接矛盾**（README 指向不存在的文件、`actual-run/quality-result.json` 引用无法从产物目录解析、规格记 not_released 而产物记 released 且无追认）；自评可信度：技术层高、自述层低、综合中 | completed（报告：`quality/evidence/research/drafts/D-coverage-fidelity.md`） | D-002, D-007 |
| F-005 | **用户自有的「语义知识层」工具链现状**（主会话发现 + 子代理 E 核查中）：`/Users/Hugh/Hugh/Knowledge/` 下已有 `CompanyBrain/`（1,417 文件，frontmatter 契约：`title/type/page_model/scope/product/section/tier/trust/source_status/quality_status/generated_by/tags/source`，`type` 实测分布 concept 385 / operation 57 / product-copy 40 / reference 29 / rule 22 / solution 9 / index 6 …，`page_model = source|derived|curated`）、`tools/` 82 个脚本约 38,000 行（含 `import_inbox.py`、`digest_knowledge_confluence_space.py`、`synthesize_*`、`audit_*`、`evaluate_gbrain_queries.py`）、每日 launchd 流水线 `automation/run_daily_import.sh`、已安装的 `gbrain` 检索/图谱 CLI、`_gbrain/query-rules.md` 的 agent 查询契约、以及查询评测集 `BrainInbox/_rules/gbrain-query-eval.json` | completed（报告：`quality/evidence/research/drafts/E-existing-semantic-layer.md`，479 行；`page_model` 推导与 `manual_only` 保护规则由主会话在代码中二次核实） | D-003, D-006 |

| F-006 | DSH 应用内 anysearch 通道 402 的根因与修复（子代理 F，报告 506 行） | 根因：DSH 内 anysearch 是 profile 插件 `@anysearch/anysearch-dsh@0.1.4`，只经 `ctx.credentials.resolve('ANYSEARCH_API_KEY')` 取 key，仅认 4 层（进程 env / `~/.dsh/.credentials.yaml` / `<cwd>/.env` / `~/.dsh/.env`），事故时四层全空 → anonymous → 402；skill 目录 `.env` 从不在 DSH 读取层。已修复：权威 key 收敛到 `~/.config/anysearch/.env`（600），`~/.claude/skills/anysearch/.env` 与 `~/.dsh/.env` 改为软链接，备份在 `~/.config/anysearch/backups/`；CLI 路径实测可用，应用内工具需重启 DSH 后生效 | completed（报告：`quality/evidence/research/drafts/F-anysearch-key-binding.md`） | — |

研究缺口问题（R0，从需求框架生成，先于检索登记）：

| gap_id | 决策轴 | 缺口问题 | 可能改变的方向 | 当前证据 |
| --- | --- | --- | --- | --- |
| G-1 | OI-03/OI-07 | release4 产物对读者的真实可用性到什么程度 | 决定是否需要重置主线 | F-001 已答（差距明显，参考型内容 0 保留） |
| G-2 | OI-04/OI-09 | 现有代码里多少复杂度可删而不损失真能力 | 决定重写 vs 精简 | F-002 已答（33.1% 不可达、两代实现并存、配置 16.87 MiB 零命中） |
| G-3 | OI-10 | 是否存在能直接复用/替代的开源做法 | 决定自研边界 | F-003 已答（无现成替代；3 个可借做法） |
| G-4 | OI-05/OI-11 | 自证质量门是否与真实效果脱钩 | 决定质量面去留 | F-001 已给初步证据（只引用 CB 17 页、依赖 cb_status=absent），待 F-004 补全 |
| G-5 | OI-14/OI-17 | 同类知识库产品如何组织页面与入口 | 决定页面范围 | F-003 已答（候选项目均不产出可读知识页；入口设计须自建） |
| G-6 | OI-22/OI-23 | 「语义知识层」的成熟呈现形式与下游消费接口 | 决定最终产物形态与是否引入外部实现 | F-003 已答（无成熟外部实现；采用用户既有语义层契约，T-006 = A） |

### 主会话独立抽检（不依赖子代理结论，本轮实测）

| 抽检项 | 子代理结论 | 主会话实测 | 判定 |
| --- | --- | --- | --- |
| 参考型内容丢失 | 原始表格行 2,943 → bundle **0** | 原始素材 `^\s*\|` 行数 = **2,943**；bundle 全库 `^\s*\|` = **14 行，全部在 `Home.md:9-22` 的导航表内**（12 个投影页入口），**内容型表格 0 行** | 属实（精确口径：bundle 唯一的表是首页导航表） |
| README 指向不存在的文件 | `README.md:11` 引用 `_audit/sources.jsonl`、`_audit/evidence.jsonl` | `ls` 两个文件均 **No such file or directory**；README 正文仍写"保存逐条来源元数据/证据与页面绑定" | 属实 |
| 300 行上限未实现 | 新产品路径零实现，仅旧 `page_layout.py` 有 | `grep '\b300\b'` 在 `compiler.py`/`quality.py`/`publisher.py` **零命中**；`page_layout.py:241,344,372` 有真实校验；配置键 `reader_max_lines` 在 `src/`、`scripts/` **零消费者** | 属实 |
| 首页导航覆盖 | 95/99 页正文为同一模板问句 | `Home.md` 导航表仅 12 行 = 12 个投影页；87 个来源页无首页入口 | 属实 |

### 落盘的研究报告与独立复核

- `research-report.v1`：`quality/evidence/research/c744c341a1d35bf7cf7692bfe7dad4282a132941666299175095ceb8f7c69921.json`（提交 run 时按当前 snapshot/material revision 重新组装，见任务目录 `compose-research-report.mjs`）。
- R5 独立复核：由独立上下文子代理执行，结论回填报告的 `review` 字段与本节。

## grill

Grill（`grill-with-docs`）在 Talk Round 3 之后执行，先核实代码事实、再只问两条会改变方向的 frontier 问题（两条互相独立，同批提出）。
核实到的关键事实（决定了问题的形状）：
`tools/apply_formal_knowledge_metadata.py:94-103` 的 `page_model_for()` 把任何带 `generated_by` 的页判为 `derived`（因此 KD 产物不会被当作 `source` 清理）；
`tools/normalize_product_note_names.py:25-27` 只保护 `manual_only: true` 或 `page_model: curated` 的页，第 129-131 行对非 manual-only 的同名目标页是「先覆盖再 unlink 源文件」——即 KD 的 `derived` 页在既有流水线恢复后没有豁免权。

需求覆盖矩阵（五类原始消息 → 决策轴 → 用户选择/事实）：

| message_class | 决策轴 | 覆盖方式 | 绑定 |
| --- | --- | --- | --- |
| goal | 目标排序与及格线 | 用户选择 T-001/T-002 | OI-06, OI-07 |
| flow_or_surface | 用户旅程、页面范围、最终呈现形式 | 用户选择 T-003/T-005/T-006 + Grill Q15 | OI-08, OI-16, OI-17, OI-22 |
| data_or_state | 输入范围、来源状态、参考型内容保留 | 用户选择 T-007/T-009 + 事实 | OI-14, OI-18, OI-24 |
| success_failure_acceptance | 对照口径、成本度量、证据下限、失败与恢复 | 用户选择 T-008/T-012/T-013/T-014 + 事实 | OI-11, OI-12, OI-13, OI-19, OI-21, OI-23, OI-25, OI-26, OI-27 |
| constraint_non_goal_defer | 非目标、延期、既有流水线边界 | 用户选择 T-010/T-011 + Grill Q15/Q16 | OI-09, OI-15, OI-20, OI-21 |

| grill_id | CONTEXT/冲突 | 结论 | ADR/四项退出 | source/evidence |
| --- | --- | --- | --- | --- |
| G-001 | 同一主题在既有语义层已可能由 `tools/synthesize_*` 脚本产出；KD 若直接写同一路径会出现两个生产者 | 用户选择 A：同一主题只允许一个生产者，KD 逐步接替旧脚本；接管前先做只读对比证明不劣化，并在自动化规则中登记 | ADR-0013 created；退出检查 external_interfaces=pass | Grill 真实回复（host 问答工具） |
| G-002 | 既有 frontmatter 契约由 `apply_formal_knowledge_metadata.py` 执行，新增字段可能被既有脚本重写或丢弃 | 用户选择 B：允许新增**一个**溯源字段，但必须在既有元数据权威里登记；字段字面名与取值形状留给 build-spec | 退出检查 canonical_names=pass（唯一权威=CONTEXT.md；字面名列入 OPEN-008） | 同上 |
| G-003 | 术语冲突：`CONTEXT.md` 里"知识库/发布"等词指旧 bundle 体系，与新决定的"语义知识层"混用 | 已在 `CONTEXT.md` 新增 4 条术语：语义知识层、唯一生产者（同一主题）、真实查询集验收、证据零容忍 | CONTEXT.md changed（见「文档结果」） | `CONTEXT.md` 末尾新增节 |

**四项客观退出检查（逐项）**：

- `external_interfaces`：**pass**。既有语义层契约按代码核实（`apply_formal_knowledge_metadata.py:94-103`、`normalize_product_note_names.py:25-27,129-131`）；`gbrain` 按 CLI 与 `get <slug>` 返回 frontmatter 核实；两条外部开源论断经 anysearch 读一手原文（RAGFlow `wiki.py` 原文、LangExtract README）。
- `canonical_names`：**pass**。本轮涉及的字段/路径命名唯一权威钉死为 `CONTEXT.md`（新增术语节）；新增溯源字段的字面名与取值形状属实现层，作为 OPEN-008 交 build-spec，不影响方向。
- `failure_semantics`：**pass**。OI-13/OI-19/OI-27 定义：缺来源、引用不可达、越界写入、资料未明确被写成结论都必须判失败或显式标注；失败运行必须保留真实错误与调用计数，恢复按来源重跑且不叠加半成品。
- `scope_boundaries`：**pass**。NG-001…NG-010 写死"不做什么"；OI-14（只做 Markdown）、OI-20（非目标）、OI-21（延期与 owner）与 Grill Q15/Q16 的生产者/词表边界共同封闭隐性扩大。

## 决定条目 D*

### M-基线判断

#### D-001
- question/final_option: 现状是否需要重置主线？→ 需要：把"产物类型"从"89 篇文档的场景化摘要索引"改成"面向检索、可被下游消费的知识页"。
- recommendation/plain_language: 推荐。用大白话说：现在这套东西生成的是"把每篇文档缩写成一段话"的索引，不是"能查参数、能查步骤、能查出处"的知识库。
- decision: 采纳"效果差距=产物类型不同"的判断，并以此作为后续所有改造的前提。
- source_type/reference/exact_excerpt: research / `quality/evidence/research/drafts/A-effect-comparison.md` /「差距不是"少写了若干细节"，而是产物类型不同：Bundle 是"89 篇输入文档的情景化摘要索引"，CompanyBrain 是"面向检索的产品知识库"」。
- approval_binding: pending（待最终确认）
- facts_and_constraints: 表格行 2,943→0（实测口径：产物仅剩首页导航表 14 行）；唯一 URL 708→1；87/99 页无首页入口；README 指向不存在的文件；溯源本身真实（10,349 条坐标可复算）。
- Logic: 实测事实（参考型内容整体丢失 + 导航不可达）→ 约束（用户要"能替代 CompanyBrain 查产品知识"）→ 选择（承认产物类型错位而非补丁）→ 预期结果（改造聚焦"生产什么页、怎么组织"而非继续调摘要 prompt）。
- choice_reason/impact: 只有承认类型错位，才能解释为什么"机器自评全胜"与"实际不可用"能同时成立；影响范围=整个编译目标与验收方式。
- consequences_and_risks: 后果=主线要重做而不是修补；风险=重做期可能短期产出更少页面（RISK-003 抽样偏差风险由多源复核缓解）。
- rejected_alternatives: 「只是细节不够，继续调 prompt 补齐」——被"参考型内容 100% 丢失且同源两页互相矛盾"的直接证据否决。
- unresolved_items/owner: 无。
- Supersedes: none
module: M-基线判断
requirement_ids: [R-001, R-002]
derived_from: []
artifacts: []

#### D-002
- question/final_option: 项目自评能不能当作交付成功的依据？→ 不能：技术层可信、自述层不可信，验收必须换成真实判定。
- recommendation/plain_language: 推荐。大白话：它的指纹、行号、哈希这部分是老实可靠的；但它给自己打的"全部达标"是不算数的。
- decision: 自评结论不得作为改造效果或发布成功的依据；只保留可复算的硬事实。
- source_type/reference/exact_excerpt: research / `quality/evidence/research/drafts/D-coverage-fidelity.md` /「不是系统性自欺，但存在『用机器绿灯替代语义自检』的结构性盲区」；「120/120 KD_WIN 里 77.9% 是 non_regression」。
- approval_binding: pending（待最终确认）
- facts_and_constraints: 89/89 指纹可复算、10,349/10,349 坐标 sha256 通过、212 条 claim 无幻觉；同时存在 3 条与产物直接矛盾的声称（README 指向不存在文件、引用不可解析、规格记 not_released 而产物记 released）。
- Logic: 事实（技术层零水分 + 自述层 3 处矛盾）→ 约束（用户要"失败不伪装成功"）→ 选择（分账：保留硬事实、废除自我裁决）→ 预期结果（验收不再可能被绿灯糊弄）。
- choice_reason/impact: 自评与效果脱钩是本轮最贵的教训；影响=质量面与验收方式的全部设计。
- consequences_and_risks: 后果=需要重建验收（D-006）；风险=短期内没有"自动化通过凭证"，需要用户参与判定。
- rejected_alternatives: 「相信评审报告的 strict_all_kd_win」——被"50 个 strict_improvement 全部依赖对照侧 absent"证伪其解释范围。
- unresolved_items/owner: gbrain 查询评测集需扩容（build-spec）。
- Supersedes: none
module: M-基线判断
requirement_ids: [R-001, R-004]
derived_from: [D-001]
artifacts: []

### M-产物形态

#### D-003
- question/final_option: KD 的最终产物长什么样？→ 直接产出用户既有语义层的页面（同一套 frontmatter、目录命名与 `[[wikilink]]`）。
- recommendation/plain_language: 推荐。大白话：让它生成的文件就是放进你现有知识库、和你手写的页面长一样的那种文件，而不是另起一套、还得再翻译一遍。
- decision: KD 的输出契约对齐 `/Users/Hugh/Hugh/Knowledge/` 现有语义层；KD 定位为该层的编译器。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ `decision-log.md#Talk` T-006 /「A KD 直接产出语义层的页面」（用户在看到两种具体产物样例后重新选择）。
- approval_binding: pending（待最终确认，visible_group=R2）
- facts_and_constraints: 既有契约执行者 `tools/apply_formal_knowledge_metadata.py`；`gbrain` 只读 `type` 与 frontmatter；现有 2274 处 `[[wikilink]]`；KD 现用 `page_type`/`digest_*`/相对链接，且 `page_model: source` 会被既有流水线删除。
- Logic: 事实（下游消费方只认既有契约）→ 约束（用户要求产物作为语义知识层供技能/Agent/应用层消费）→ 选择（KD 侧对齐契约）→ 预期结果（产物零转换即可被 gbrain 检索与 agent 引用）。
- choice_reason/impact: 对齐契约比维护导出层更简单，且直接满足"下游好用"；影响=页面模板、元数据、链接格式、目录写入位置全部要改。
- consequences_and_risks: 后果=接受既有命名与类型词表约束；风险=既有流水线恢复时会 rename/unlink 同目录页面（RISK-006），且产物若被判为 `page_model: source` 可能被清理（RISK-007）。
- rejected_alternatives: 「保留自有格式 + 另写导出层」（两套格式漂移、导出层本身是新复杂度）；「先不定」（把核心呈现形式推到下游）。
- unresolved_items/owner: 产物写哪棵子树与 `page_model` 取值 → build-spec 定死。
- Supersedes: none
module: M-产物形态
requirement_ids: [R-003, R-006]
derived_from: [D-001]
artifacts: []

#### D-004
- question/final_option: 参考型内容（表格/参数/枚举/URL/字段字典/报错文案）怎么进产物？→ 逐字保留，只对叙述性段落做语义合成。
- recommendation/plain_language: 推荐。大白话：查参数、查字段、查链接这类内容原样搬进去；只有"讲道理"的段落才让模型重写。
- decision: 参考型内容按原文结构逐字保留并可溯源；语义合成只作用于叙述性内容。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ `decision-log.md#Talk` T-007 /「A 参考内容逐字保留，只对叙述做合成」。
- approval_binding: pending（待最终确认，visible_group=R2）
- facts_and_constraints: 原始素材行首表格 2,943 行、唯一 URL 708 个、截图引用 326 处；现产物内容型表格 0、URL 1；用户及格线是"能替代 CompanyBrain 查产品知识"，而参考型内容正是"查参数"的主战场。
- Logic: 事实（参考型内容整体丢失）→ 约束（及格线要求可查参数/字段）→ 选择（逐字保留 + 仅合成叙述）→ 预期结果（补上现产物的能力空洞，同时维持可读性）。
- choice_reason/impact: "不丢内容"与"可读"冲突时，本轮选择把可读性让给叙述层、把保真让给参考层；影响=页面结构（需要参考区块/独立页）与分页策略。
- consequences_and_risks: 后果=页面变长、需要分页或参考页；风险=逐字保留可能带入过时或互相冲突的原文（必须显式标注冲突，不能静默择一）。
- rejected_alternatives: 「仍由模型重写但强制不丢字段」（已实测会丢，且"不丢"难验证）；「参考数据单独成字典页」（读者多跳一次，且要先定义什么算参考数据）。
- unresolved_items/owner: 参考区块的页内结构与分页阈值 → build-spec。
- Supersedes: none
module: M-产物形态
requirement_ids: [R-002, R-006]
derived_from: [D-001, D-003]
artifacts: []

### M-存量与边界

#### D-005
- question/final_option: 旧代码与已发布合同怎么处置？→ 保留骨架、砍掉历史分支（含自证质量机器与已结束任务的专用路径）。
- recommendation/plain_language: 推荐。大白话：把还能用的主干留下，把过去几轮任务留下的分支、没人调用的代码和自证机器删掉。
- decision: 在保留产品路径骨架的前提下做减法；删除范围以实现事实为准，不以文档承诺为准。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ `decision-log.md#Talk` T-004 /「A 保留骨架、砍掉历史分支」。
- approval_binding: pending（待最终确认，visible_group=R1/R2）
- facts_and_constraints: 产品路径仅 7 模块/11,441 行；33.1% 源码无入口可达；存在两套完整实现与双 provider/双发布器；16.85 MiB 配置零引用；"每页 ≤300 行"在新路径没有实现、只有旧路径有真实校验。
- Logic: 事实（大量代码与配置不在产品路径上）→ 约束（用户要求第一目标之后把项目变简单，且不能再丢真能力）→ 选择（保留骨架 + 定向删除）→ 预期结果（维护面显著缩小而不丢离线分页/分批恢复等真实能力）。
- choice_reason/impact: 推倒重写会丢掉几年积累的边界处理经验；只做增量修补会让复杂度继续上升；影响=删除清单、能力迁移顺序、测试收敛。
- consequences_and_risks: 后果=需要逐项确认"已结束任务专用"与"仍被产品路径使用"；风险=删错会伤真能力（RISK-001 的反面），必须先迁移 300 行分页与分批恢复能力。
- rejected_alternatives: 「推倒重写」（丢边界经验、重走坑）；「只做增量修补」（复杂度继续上升，且证据显示问题不在补丁层）。
- unresolved_items/owner: 具体删除顺序与能力迁移清单 → build-plan。
- Supersedes: none
module: M-存量与边界
requirement_ids: [R-004, R-006]
derived_from: [D-001]
artifacts: []

#### D-006
- question/final_option: 与用户既有自动化流水线的写权边界怎么定？→ 本任务只把写权边界写死，不修那条停摆的流水线（另开任务）。
- recommendation/plain_language: 推荐。大白话：先说清楚"谁能写哪些目录"，但这次不去动那套已经停了 109 天的每日任务。
- decision: KD 只写自己声明的路径；既有 CompanyBrain 正式页不在本期写入范围；停摆流水线的修复另开任务。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ `decision-log.md#Talk` T-011 /「A 只定写权边界，修复另开任务」。
- approval_binding: pending（待最终确认，visible_group=R2）
- facts_and_constraints: 既有流水线 `run_daily_import.sh:2` 的 `set -euo pipefail` 使其自 2026-05-26 起整体不执行；恢复时会执行 `normalize_product_note_names.py:131,135`（rename/unlink）与 `prune_low_value_formal_sources.py:39`（unlink）；KD 当前对 CompanyBrain 只读。
- Logic: 事实（对方流水线会改名/删页 + KD 需写入同一语义层）→ 约束（用户不愿本期扩大范围）→ 选择（先定边界、修流水线另开任务）→ 预期结果（本期边界清楚，协同风险被显式登记而不是遗忘）。
- choice_reason/impact: 把风险写进记录比顺手改别人的流水线安全；影响=写入目录与 `page_model` 取值必须在 spec 里显式声明。
- consequences_and_risks: 后果=风险被推迟而非消除（RISK-006/RISK-007）；风险=流水线恢复当日可能改名或删除 KD 产物。
- rejected_alternatives: 「纳入本任务一起修」（范围明显变大）；「暂不处理」（继续基于过期数据做判断）。
- unresolved_items/owner: 写入目录清单与 `page_model` 声明 → build-spec；流水线修复 → 用户另开任务。
- Supersedes: none
module: M-存量与边界
requirement_ids: [R-006, R-009]
derived_from: [D-003]
artifacts: []

### M-质量与验收

#### D-007
- question/final_option: 交付质量怎么验收？→ 删掉自证机器，改成"真实查询集 + 真实判定"。
- recommendation/plain_language: 推荐。大白话：不再让程序给自己发奖状，改成拿一组真实问题去考它，答不上就是答不上。
- decision: 废除投影/五维比较/证书/verifier 一类自证机制；验收以固定查询集的可定位性与可溯源为准。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ `decision-log.md#Talk` T-008 /「A 自证机器换成真实查询集验收」。
- approval_binding: pending（待最终确认，visible_group=R2）
- facts_and_constraints: 自评"120/120 KD_WIN"与实际不可用并存；gbrain 现有评测集仅 6 个用例且预言机过松（失效 slug 仍报 pass）。
- Logic: 事实（自证与效果脱钩）→ 约束（及格线=可替代 CompanyBrain 查知识）→ 选择（用真实问题判定）→ 预期结果（验收结论无法被机器绿灯替代）。
- choice_reason/impact: 只有真实问题能同时检验"内容在不在、能不能找到、出处对不对"；影响=测试与验收体系重建，查询集需用户出题。
- consequences_and_risks: 后果=需要用户参与出题与判定；风险=查询集本身可能不具代表性（需覆盖 4 个产品与各页面类型）。
- rejected_alternatives: 「精简为少量硬事实」（硬事实仍证明不了可用）；「全部保留」（重复已验证的失败模式）。
- unresolved_items/owner: 查询集题目与判定规则 → build-spec 与用户共建。
- Supersedes: none
module: M-质量与验收
requirement_ids: [R-001, R-006]
derived_from: [D-002]
artifacts: []

#### D-008
- question/final_option: 本期输入范围与发布方式？→ 只做 Confluence Markdown；全自动发布，不设人工确认。
- recommendation/plain_language: 不完全是推荐项。输入范围是推荐（先集中火力）；全自动发布与主会话推荐相反，是用户明确选择，代价已写明。
- decision: 本期只接受 Markdown 输入；运行到发布全自动，不设人工闸门。
- source_type/reference/exact_excerpt: Talk（用户真实回复）/ `decision-log.md#Talk` T-009 与 T-010 /「A 先只做 Confluence Markdown」；「B 全自动，不设确认」。
- approval_binding: pending（待最终确认，visible_group=R2）
- facts_and_constraints: 既有语义层支持 9 种格式，但用户选择先集中一条；用户选择全自动意味着错误内容会直接进入语义层并被下游技能/Agent/应用引用（RISK-005）。
- Logic: 事实（多格式抽取会拖垮主线 + 用户要省人力）→ 约束（及格线要求可用，且要求"失败不伪装成功"）→ 选择（单一输入 + 全自动）→ 预期结果（主线快速可用，但必须靠可回滚与可审计兜底）。
- choice_reason/impact: 用户以人工环节换取速度；影响=必须有可回滚发布、可审计来源与失败显式化（否则违背"失败不伪装成功"）。
- consequences_and_risks: 后果=无人工拦截；风险=错误知识被下游放大（用户已明确接受，替代控制手段必须在 spec 中落实）。
- rejected_alternatives: 输入侧：「同时接多格式」（抽取层拖垮主线）、「只留接口」（空抽象）；发布侧：「低风险自动+高风险人工」、「全量人工审校」。
- unresolved_items/owner: 可回滚发布与失败显式化的具体机制 → build-spec。
- Supersedes: none
module: M-质量与验收
requirement_ids: [R-006, R-009]
derived_from: [D-007]
artifacts: []

### M-外部复用

#### D-009
- question/final_option: 外部开源项目与做法怎么用？→ 不整体引入任何项目；只把 3 个具体做法列为候选参考。
- recommendation/plain_language: 推荐。大白话：没有哪个现成项目能替你干这件事，所以别整套搬；但有 3 个具体做法值得借。
- decision: 不引入外部项目作为依赖或替代；候选参考为 LangExtract 的"输出→源字符区间对齐"、GraphRAG 的社区报告合成 prompt、RAGFlow 的"收缩拒绝 + 双链规范化"；向量库/图数据库/chat-only 形态明确不引入。
- source_type/reference/exact_excerpt: research / `quality/evidence/research/drafts/C-oss-landscape.md`、`https://github.com/google/langextract`（一手）、`https://github.com/infiniflow/ragflow/blob/main/rag/advanced_rag/knowlege_compile/wiki.py`（一手）。
- approval_binding: pending（待最终确认）
- facts_and_constraints: 覆盖 41 个候选，无一占据该产品位；RAGFlow 明文禁止页面内引用；LangExtract 需把 `char_interval=None` 从"自行过滤"升级为硬门禁；Pandoc 的 GPL 边界属法律判断（未核实）。
- Logic: 事实（无现成替代 + 两个可借的具体机制）→ 约束（用户要求更简单、不引入新复杂度）→ 选择（不引入依赖，只借做法）→ 预期结果（借鉴单点能力而不背上平台级复杂度）。
- choice_reason/impact: 引入 RAGFlow/Graphiti 一类会带来容器、向量库或图数据库；影响=抽取层的对齐实现与页面合成 prompt 设计。
- consequences_and_risks: 后果=关键能力要自研；风险=自研对齐逻辑有实现成本（但 LangExtract 已提供 Apache-2.0 参考实现）。
- rejected_alternatives: 「直接采用 RAGFlow 作为编译引擎」（页面内无引用、需 ES）；「引入 GraphRAG/Graphiti」（Parquet/Neo4j，产物不是可读页面）。
- unresolved_items/owner: 是否采用 LangExtract 的具体模块 → build-spec 评估。
- Supersedes: none
module: M-外部复用
requirement_ids: [R-005, R-006]
derived_from: [D-001]
artifacts: []

## 审查处置

direction-advice（wh-review，stage=make-decision track=direction，红/蓝各一次）结果：
pair `d31de7bc-e2dc-4173-bc68-3c6b735403cb`，两角色均 `semantic_status=available`、`coverage=satisfied`、`partial=true`；
红 7 条 findings（blocking 1 / major 5 / minor 1）、蓝 10 条（blocking 1 / major 7 / minor 2）。
旧结果按合同不改写，处置如下（`fixed` 表示已在本文件/材料中修复；`rejected_invalid` 表示该 finding 不成立或与用户真实答复冲突，且写明理由）。

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| F-5665d679dfa8（blocking，红） | 投影的 `source` 字段带入 T-001…T-011 与"用户真实回复"字样，违反 direction 材料禁止 interaction_ref | 审查材料污染，可能锚定方向 | fixed | 已修 `build-direction-review-input.mjs`：提交给 provider 的投影把 source 归一为"用户 Talk 答复（内容不进入本投影）"或"本地事实"，不再出现 T-id；本文件 OI 的 source 保持不变（detail 审查需要真实来源） | 主会话 / 下一次 direction 运行 |
| blue[1]（blocking，蓝） | 收敛大纲未定义结构化表格的保留与失败判定（原始 2,943 行表格 100% 丢失） | 方向可能继续无视参考型内容 | fixed | 已新增 **OI-24**（data_state，用户答复 T-007 = A：逐字保留 + 显式退化标注），并写入 D-004 | 主会话 / spec |
| F-416a6e48b076 + blue[2]（major） | 与 CompanyBrain 的比较未绑定为任务级基线（冻结快照、比较单元、分母、对照侧缺失处理、阈值） | 验收可能继续靠"不退化"汇总指标 | fixed（新增待用户回答项） | 已新增 **OI-25**，进入 Talk Round 3 提问 | 用户 + 主会话 |
| F-d832b4b4f366 + blue[5]（major） | 架构/性能/可维护性没有基线与最低目标 | 瘦身或重写可能凭感觉 | fixed（新增待用户回答项） | 已新增 **OI-26**，进入 Talk Round 3 提问 | 用户 + 主会话 |
| F-9f502e3d950b + blue[7]（major） | 未独立定义证据完整性边界（claim 级溯源覆盖率、来源缺失/歧义/无法定位的判失败） | 有损但不判失败 | fixed（新增待用户回答项） | 已新增 **OI-27**，进入 Talk Round 3 提问 | 用户 + 主会话 |
| F-42ab733678f8（major，红） | 材料 Section A 把执行/沟通约束写成"原始需求自带非目标"，成品级非目标未定义 | 可能造成范围蔓延 | rejected_invalid（部分采纳措辞修正） | 本文件已有成品级非目标 NG-007…NG-010；审查材料刻意不含决定派生非目标以避免方向锚定，属材料分层而非缺口。已修材料小节标题为"原始需求自带的执行约束" | 主会话 / 材料生成器 |
| F-606626f1794a + blue[8]（major） | OI-22/OI-23 属范围蔓延，应把下游 Agent/技能消费列为非目标 | 方向失焦 | rejected_invalid | 与用户真实答复直接冲突：T-005/T-006 明确要求产物作为语义知识层供下游消费，且 T-006 = A 正是审查者建议的"对齐既有 CompanyBrain 契约"。保真优先由 T-001（效果优先）与新增 OI-24 承接 | 用户（已裁决）/ 保留 |
| blue[0]（major） | OI-14 拟扩散到 PDF/Word/网页，范围失控 | 主线失焦 | rejected_invalid（基于冻结材料） | 用户在 T-009 已选 A（只做 Confluence Markdown），本文件 NG-009 已写死；投影按合同必须保持 open 展示 | 保留 |
| blue[6]（major） | 未决定停摆的 Confluence/launchd 自动化是否属于修复范围 | 协同风险 | rejected_invalid（基于冻结材料） | 用户 T-011 已选 A（只定写权边界，修复另开任务），OI-21 已 confirmed，RISK-006/007 已登记 | 保留 |
| F-ad076dedeb40 + blue[3]（minor） | OI-01/02/05 属已核实事实，不应作为 open 决策项 | 交互效率 | fixed | 三条 OI 已改为 `confirmed` + `answered_by_fact` 终态，事实作为基线而非问题 | 保留 |
| blue[9]（minor） | OI-15 与 OI-21 重复（都问延期与触发条件） | 同一问题答两次 | fixed | 已在 OI 记录中区分：OI-15 = 能力延期清单；OI-21 = 停摆流水线修复的 owner 与触发条件 | 保留 |
| blue[4]（major） | 投影里多处 OI 的 source 写「用户真实回复 T-xxx」，而材料称六类边界尚无用户答复，两者冲突 | 可能默默锚定方向 | fixed | 与 blocking F-5665d679dfa8 同源：已在 `build-direction-review-input.mjs` 中把提交给 provider 的投影 source 归一化，不再出现 T-id；本文件 OI 记录保留真实来源供 detail 对账 | 保留 |

### detail-advice 结果与处置（第二轮独立审查）

detail-advice（wh-review，`review_track=detail`）pair `6852080e-f0da-4a1a-b848-13651a25769c`，红 21 条 / 蓝 22 条，两角色均 `semantic_status=available`、`coverage=satisfied`。
findings 只涉及两件事：**（a）我提交的 direction 材料状态行过期；（b）验收草案缺项**。没有任何一条改变用户已确认的方向，因此按 make-decision 的规则不需要启动 Talk Round 4，由主会话在本阶段直接修复并登记处置。

| finding 组 | 代表 finding | 处置 | 证据 |
| --- | --- | --- | --- |
| 材料状态与版本不一致（blocking ×2） | red[3]、blue[16]、red[5]、blue[4]/blue[12]、red[20] | **fixed**：本文件头、调研行 F-003/F-004/F-005、G-3/G-5/G-6、核心目标/验收标准 的 `next_review_trigger` 全部刷新为当前态；OI 大纲「身份绑定」行由 v1 改为 v1.2 并说明版本沿革；`Fixed categories` 表按 OI 记录的 `category` 逐条对齐 | 本文件对应行；`check-decision-log-chain` 0 warning |
| blue[4] 缺处置行 | blue[4] | **fixed**：补处置行（见上） | 本条 |
| 读者路径验收缺位 | red[1]/red[14]、blue[2]/blue[6]/blue[11]/blue[15] | **fixed**：验收标准新增「读者路径」一节（入口页可达全部已发布页 + 入口对页面有区分度，有页无入口或入口同质即判失败） | 本文件「验收标准」 |
| 数据状态验收缺位 | red[0]/red[17]、blue[20]/blue[21] | **fixed**：验收标准新增「数据状态」一节（ready/known_empty/duplicate_alias/audit_only 逐类样例；重复来源发成两页判失败；增量不删旧页；资料未明确不进分母） | 同上 |
| 回滚与原子发布不可验证 | red[10]/red[12]/red[19]、blue[0]/blue[13] | **fixed**：验收标准新增「发布安全」一节（staging + 原子切换 + last-known-good + 中断/取消/回滚负例） | 同上 |
| 参考型内容只抽样 | red[2]、blue[1] | **fixed**：验收标准改为「冻结分层全量清单 + 逐块比较 + 多来源冲突必须显式标注」 | 同上 |
| 对照评分与阈值缺位 | red[13]、blue[3]/blue[9]/blue[10]、red[8]/blue[7] | **fixed**：验收标准新增「对照判定规则」与「语料冻结」：每题的答案/定位/出处/未覆盖判定 + 汇总通过条件；语料单一数字化为 89 并绑定清单与 hash；改造前 release4 产物一并冻结 | 同上 |
| 证据零容忍不可机械执行 | red[16]/red[18]、blue[8] | **fixed**：验收标准写明「claim 边界与引用语法由 build-spec 冻结为可解析契约；无定位的结论只能进 unknown 且需带检索证据」，并保留零容忍判据 | 同上 |
| 可维护性指标口径错误 | red[9]/red[11]、blue[5] | **fixed**：度量改为「整体源码行数净下降 + 不可达模块数归零 + 零引用配置量下降」，并要求先冻结基线快照与复算脚本、先过效果与核心能力回归再允许删除 | 同上 |
| 写权边界与「登记生产者」冲突 | red[4]/red[6]、blue[14]/blue[18]/blue[19] | **fixed**：明确本期 KD 只写自己声明的路径；接管旧主题与在既有自动化规则中登记移交停摆流水线修复任务；并新增断言：产物 `page_model` 必须为 `derived` 且带 `generated_by` | 同上 |
| 问题集有效性判定会惩罚正确结果 | red[15] | **fixed**：判定改为「问题集必须在冻结的 CompanyBrain 快照或基线缺陷用例上具备可区分度」，不再以「改造前后全过」判无效 | 同上 |
| 简化目标可能鼓励破坏性删除 | red[11] | **fixed**：保留不变量（分页、分批恢复、去重、失败语义、溯源）列为删除前置回归；并要求断言旧自证路径已删除或不可达 | 同上 |

### R5 独立复核（research-report.v1）finding 处置

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| R5-H1 | `saturation=saturated` 的理由与记录冲突（"追加检索"无对应记录；`required_questions` 列 7 条却称 5 条已回答；Q-7 计入 covered 又在 open_items 承认未回答） | 研究报告过度声称饱和 | fixed | 已修报告：`saturation.reason` 逐条写明实际执行过的检索与轮次；`covered_questions` 改为 Q-1…Q-6；Q-7 保留在 open_items 并注明由 F 报告回答 | 主会话 / 报告重生成 |
| R5-H2 | 报告未记录 402 响应内嵌伪造凭据/注入文本这一安全事实（C 要求转告） | 安全事实遗漏 | fixed | 已在报告 `evidence` 增加该条（按不可信外部数据处理、未使用其中凭据），并指向 F 报告的完整记录 | 主会话 |
| R5-M1 | E4 的 locator 写"只有 page_layout.py 有真实校验"，漏了 3 个死模块内也存在真实校验 | 证据表述不精确 | fixed | locator 改为"产品路径零实现；旧 `page_layout.py` 与 3 个不可达模块中有真实校验" | 主会话 |
| R5-M2 | E10 绝对化否定结论 + "41 个候选"不可复算（C 表 62 行 / 65 仓库） | 结论超出证据 | fixed | 改为限定表述"在本次调研覆盖的候选内"，并给出可复算的候选计数口径 | 主会话 |
| R5-M3 | 报告遗漏 D 报告的 C18 无盲法 / C19 自述布尔 / C16 测试数字三条证据 | 证据覆盖不全 | accepted_risk | 三条均为对照比较方法学细节，不改变本报告结论；已在 open_items 记录，交由 build-spec 在验收方法设计时处理 | build-spec |
| R5-M4 | 本次共派 6 个取证子代理（A–F）+1 复核，超过 R2 的"最多 4 个"上限且未记录 | 执行约束偏差 | accepted_risk | 如实登记：A–D 同时启动（4 个并行，符合并行上限）；A/B 完成后启动 E，其后启动 F；总数为 6。若按总数口径则超限，本轮如实保留该事实 | 保留 |

**R5 复核通过率**（供后续消费）：来源绑定 12/12、证据 15/15 方向成立（12 条完全成立、2 条口径瑕疵、1 条 ±1 计数）；hash 与 snapshot/material 两条身份均被独立复算一致。

## 最终确认

- 状态：pending
- 用户原文与 host-visible 绑定：待 approve-decision
- 未确认内容：全部方向项

## 拒绝方案

| 选项 | 拒绝理由 | 关联 D |
| --- | --- | --- |
| 只调摘要 prompt、不承认产物类型错位 | 参考型内容 100% 丢失、同源两页互相矛盾，属类型问题而非细节问题 | D-001 |
| 相信"120/120 KD_WIN"作为交付依据 | 77.9% 只是 non_regression，50 个 strict_improvement 全依赖对照侧 absent，比较只引用 17 个对照页 | D-002 |
| 保留自有产物格式 + 另写导出层 | 两套格式会漂移，导出层本身是新复杂度，且 gbrain 在转换前搜不到 | D-003 |
| 参考型内容仍由模型重写、"强制不丢字段" | 已实测会丢（内容型表格 0），且"不丢"难验证 | D-004 |
| 参考数据单独成字典页 | 读者多跳一次，且需先定义什么算参考数据 | D-004 |
| 推倒重写 | 会丢掉已验证的边界处理经验（指纹/去重/增量/失败语义），坑要重走 | D-005 |
| 只做增量修补 | 复杂度继续上升，且证据显示问题不在补丁层 | D-005 |
| 把停摆流水线的修复纳入本任务 | 范围明显变大，且会与本期主线争资源 | D-006 |
| 质量面精简为少量硬事实 | 硬事实（指纹/引用可达）仍无法证明"读者能用" | D-007 |
| 全部保留自证质量机器 | 重复已被实测证伪的失败模式 | D-007 |
| 同时接 PDF/Word/网页等多种格式 | 抽取质量与格式边界会拖垮主线 | D-008 |
| 只留多格式接口、本期不实现 | 易变成没有消费者的空抽象 | D-008 |
| 低风险自动 + 高风险人工确认 / 全量人工审校 | 用户明确选择全自动（T-010 = B）；风险已登记 RISK-005 | D-008 |
| 直接采用 RAGFlow 作为编译引擎 | 其 prompt 明文禁止页面内引用，页面存 ES 无本地 .md | D-009 |
| 引入 GraphRAG / Graphiti | 产物是 Parquet / 需要 Neo4j，不是可读知识页 | D-009 |

## 未决项

| item_id | 未决内容 | 原因 | 谁在何时解决 |
| --- | --- | --- | --- |
| OPEN-001 | 产物的具体页面清单与页面类型映射 | 属实现层细节，用户明确留给后续阶段 | build-spec（用户可参与） |
| OPEN-002 | 真实查询集的题目与判定规则 | 用户选择"真实查询集验收"，题目需用户出 | build-spec，与用户共建 |
| OPEN-003 | 写入目录清单与 `page_model` 取值（避免被判为 source 而被既有流水线清理） | 依赖既有语义层契约细节 | build-spec（RISK-007） |
| OPEN-004 | 300 行分页与分批恢复能力的迁移顺序 | 该能力目前只在旧路径实现 | build-plan |
| OPEN-005 | 是否采用 LangExtract 的具体模块做字符区间对齐 | 需评估实现成本与中文分词适配 | build-spec 评估 |
| OPEN-006 | 停摆的每日自动化流水线何时恢复 | 用户选择另开任务 | 用户（另有任务）+ 恢复前需干跑 |
| OPEN-007 | Pandoc 以子进程使用是否构成 GPL 衍生 | 属法律判断，未核实 | 用户裁定（若采用 Pandoc） |
| OPEN-008 | 新增溯源字段的字面名与取值形状 | Grill 退出检查允许：唯一权威已定为 `CONTEXT.md`，字面名属实现层 | build-spec，并同步登记进既有元数据脚本 |

## Supersedes

无（本任务首份决策记录）。

## 文档结果

- CONTEXT.md：**changed**。文件引用 `CONTEXT.md`（`task6-effect-gap-and-architecture-reset` worktree）。新增 4 条术语：**语义知识层**、**唯一生产者（同一主题）**、**真实查询集验收**、**证据零容忍**，各带 `_Avoid_` 反例，用于消除"bundle 就是知识库"与"绿灯就是可用"两类旧用法。
- ADR：**created**，两条，文件引用 `docs/adr/0013-write-into-existing-semantic-layer.md`、`docs/adr/0014-real-query-set-acceptance.md`。
- ADR criteria（逐条）：ADR-0013 —— hard to reverse **真**（产物写进用户在用知识层并接替旧脚本，回退需迁移页面）；surprising without context **真**（一个独立工具为何直接写 CompanyBrain 且要接管旧脚本）；genuine trade-off **真**（对齐既有契约换下游可消费 vs 保持自有格式换内部自由）。ADR-0014 —— hard to reverse **真**（删除自证机器后重建成本高）；surprising **真**（项目历史几乎全是加质量门）；genuine trade-off **真**（真实判定换掉自动化绿灯与免人工）。
- 术语/ADR 冲突及处理：`CONTEXT.md` 旧术语把"发布/released/知识库"绑定在 bundle 体系上，与新决定的"语义知识层"冲突；处理方式是不改写旧术语（历史材料仍引用它们），新增一节限定新决定的用法，并在 ADR-0013/0014 中显式写明取代关系。
- 不复制 spec 的边界：本节只记录术语与 ADR 层面的决定，页面清单、字段字面名、分页阈值、查询集题目均留给 spec/plan。

## 阶段执行记录

本文件内的真实 step 结果（执行事实，不代替下游材料）：

| step | step_slug | 状态 | 真实结果 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | load-context | completed | 读取原始需求、make-decision 工作流与其依赖契约；建立本文件、任务身份与唯一 OI 大纲（21 项） | 本文件 任务身份 / OI 大纲 |
| 2 | triage-scope | completed | 写入初始范围、不确定性、非目标草案与风险草案 | 本文件 范围 / 非目标 / 风险与延期交接 |
| 3 | talk-round-1 | completed | 真实 ask→wait→reply→resume：5 个独立方向问题（目标排序/成功判据/产品形态/旧架构处置/页面交付面），用户全部作答（A/A/A/A + Q5 选项 A 与补充语义层需求）；重排后 Round 2 候选 7 项 | 本文件 Talk 节 T-001…T-005 |
| 4 | research-inputs | completed | 6 个取证子代理全部回传并落盘（A 效果对比 406 行、B 架构审计 417 行、C 开源调研 438 行、D 覆盖保真 361 行、E 既有语义层 479 行、F anysearch 根因与修复 506 行）；主会话对 A/B 的 4 条关键结论独立复算；对外 2 条关键论断经 anysearch 首方复核；`research-report.v1` 已生成并通过运行时 schema 校验；R5 独立复核进行中 | `quality/evidence/research/drafts/*.md`、`quality/evidence/research/c744c341….json` |
| 5 | talk-round-2 | completed | 真实 ask→wait→reply→resume：6 个独立问题（产物归属/参考内容/质量验收/输入范围/人工环节/停摆流水线）；T-006 用户表示不懂，按歧义校正规则补充具体产物样例后重问并收到真实回复 | 本文件 Talk 节 T-006…T-011 |
| 14 | stage-reflection | pending | — | — |
