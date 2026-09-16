# 决策记录 · task9-release-safety-query-acceptance

> 本文件是 make-decision 阶段唯一权威材料。OI 大纲只存在于本文件内，不另建需求账本、状态机或第五份材料。
> 当前阶段状态：**in_progress**（step 1–10 完成：load-context、triage-scope、Talk Round 1、调研取证、Talk Round 2、
> direction-advice（红/蓝各一路独立执行，`available-with-failures`）、Talk Round 3（含用户一次重要方向纠正）、
> grill、决策草稿、detail-advice（红/蓝各一路，`available-with-failures`）与第 4 轮 Talk；
> **等待用户对最终决策卡的真实确认**（step 11），随后 stage-end 自检与发布）。
> 标题层级说明：`## 原始需求`、`## 核心需求`、`## 核心目标`、`## 已选方向`、`## 验收标准`、`## 范围`、
> `## 完整用户旅程`、`## UI applicability`、`## 收敛检查` 是运行时读取的固定小节名，保持不带编号。

## 任务身份

| 项 | 值 |
| --- | --- |
| project | KnowledgeDigest |
| task_id | `task9-release-safety-query-acceptance` |
| stage | make-decision |
| worktree | `/Users/Hugh/Hugh/Project/KnowledgeDigest-task9-release-safety-query-acceptance` |
| branch | `task/KnowledgeDigest/task9-release-safety-query-acceptance` |
| baseline_commit | `973cf31a0586d99d89bf4242290ece064a7b5a76` |
| task_path | `/Users/Hugh/Hugh/Knowledge/Projects/KnowledgeDigest/tasks/task9-release-safety-query-acceptance` |
| created_at | 2026-09-15 |

- **任务类型**：普通任务

**范围声明（triage-scope 初步，待 Talk Round 1 用户确认）**：本任务范围 = 母任务 PRD
（`specs/archive/task6-effect-gap-and-architecture-reset/prd.md`）中的 **K3 一张卡**（安全地交出去：发布安全 + 真实查询集验收），
不含 K1 语义层页面编译、K2 入口与导航、K4 瘦身删码。
母任务与其兄弟任务材料对本任务只读；本任务自建 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 四份材料。

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 状态/处置 | 关联 OI |
| --- | --- | --- | --- | --- |
| R-001 | 按标准 WorkflowHub 从 make-decision 开始本任务，先创建 worktree | 用户原话 2026-09-15「先创建worktree，然后从 make-decision 开始」 | covered | 阶段执行记录 |
| R-002 | 不跳阶段 | 用户原话「不要跳阶段」 | covered | 阶段执行记录 |
| R-003 | 不依赖 build-spec 补需求；先基于原始需求在 make-decision 内把需求梳理完整 | 用户原话「也不要依赖 build-spec 补需求。先基于原始需求，在make-decision的过程中和我一起仔细梳理」 | covered | 六类边界在本阶段收敛 |
| R-004 | 在 make-decision 过程中共同梳理六类边界：完整用户流程、页面范围、数据状态、成功/失败边界、非目标、延期项 | 用户原话 | covered | OI 大纲 Fixed categories 六类全覆盖 |
| R-005 | 注意主会话上下文控制与子代理派发 | 用户原话 | covered | NG-002；`## 调研` |
| R-006 | Talk 与 grill 用大白话说明选项、后果和风险 | 用户原话 | covered | `## Talk` 卡片格式 |
| R-007 | 任务范围 = 母任务 PRD 的 K3 卡（K1/K2 已完成提交） | 用户原话「其中K1和k2都完成提交了，我准备开始其中K3任务了」 | covered | Talk R1 Q0；OI-13 |
| R-008 | K3 结果①：发布具备 staging+原子切换+last-known-good+回滚，负例下只呈现完整版本，失败运行成本计数真实非 null | 母任务 PRD K3「结果」① | covered | OI-01…OI-04, OI-07 |
| R-009 | K3 结果②：冻结快照+问题集+逐题判定记录可复跑，能给出通过与失败 | 母任务 PRD K3「结果」② | covered | OI-05, OI-06, OI-08 |
| R-010 | K3 结果③：问题集在冻结 CB 快照上具备可区分度 | 母任务 PRD K3「结果」③ | covered | OI-09 |
| R-011 | K3 的 5 条 FR/AC（FR-K3-1 原子发布与回滚 / FR-K3-2 失败显式化与成本度量 / FR-K3-3 判定记录可复跑 / FR-K3-4 问题集有效性 / FR-K3-5 冻结物齐备） | 母任务 PRD K3 表 | covered | OI-01…OI-12 |
| R-012 | K3 scope：发布通道、失败显式化与成本度量、查询集/判定记录器、冻结快照管理；不改编译（K1）、不改导航（K2）、不删代码（K4） | 母任务 PRD K3「scope」 | covered | OI-02, OI-03, NG-001 |
| R-013 | K3 用户流程与状态转换：staging 校验 → 原子切换 →（失败时）回滚 last-known-good；验收：出题 → 冻结 → 逐题判定 → 汇总通过与失败 | 母任务 PRD K3「用户流程与状态转换」 | covered | OI-01, OI-03, OI-08 |
| R-014 | 准备依赖 = fixture 语料 + 冻结基线脚本；实现依赖 = 无（fixture 先行）；验收依赖 = K1/K2 产物（全链路对照）、用户参与出题（OPEN-002）；合并依赖 = 作为 K1/K2/K4 合并后的全链路门禁 | 母任务 PRD K3「依赖」 | covered | OI-02, OI-05, OI-13 |
| R-015 | 已知缺陷：`observed_calls=null`（`publisher.py` 失败路径硬编码），两次失败运行约 300 次 provider 调用无账 | 母任务决策记录 OI-26 / F-002；母任务 PRD FR-K3-2 | covered | OI-04 |
| R-016 | 对照口径：冻结 CompanyBrain 快照 + 同一组问题逐题对比；比较单元 = 单题；对照侧无内容记「对照未覆盖」不得计为我方优势；证据必须可复算 | 母任务决策记录 OI-25；母任务 PRD S8 | covered | OI-06, OI-08 |
| R-017 | S5 发布安全：staging 校验 → 原子切换 → last-known-good；负例（写入中断/取消/校验失败/越界写入）下读者与 gbrain 只见完整的新版本或完整的旧版本；失败运行的耗时/调用数/token 必须真实非 null | 母任务 PRD S5 | covered | OI-01, OI-03, OI-04, OI-07 |
| R-018 | S7 写权边界：KD 本期只写自己声明的路径；不修改既有 CompanyBrain 正式页；不修改停摆的自动化流水线 | 母任务 PRD S7 | covered | OI-11, NG-004 |
| R-019 | S2 冻结三样（对照验收前提）：① 89 份 Confluence Markdown 输入清单 + 每份 sha256；② 改造前 release4 产物快照；③ CompanyBrain 冻结快照（记录其 ID）；缺一，对照验收结论无效 | 母任务 PRD S2 | covered | OI-05 |
| R-020 | S8 对照判定规则：同一组问题逐题判定四结果（答案命中/定位有效/出处正确/对照未覆盖）；「对照未覆盖」不计我方优势；每题判定与汇总通过条件在 K1/K3 的 build-spec 冻结为可执行规则 | 母任务 PRD S8 | covered | OI-06, OI-08 |
| R-021 | S3 数据状态词表：`ready / known_empty / duplicate_alias / audit_only / 资料未明确`；「资料未明确」不得写成结论、不得进入事实分母 | 母任务 PRD S3 | covered | OI-10 |
| R-022 | local risk：全自动发布无人工闸门（RISK-005，用户已接受）→ 用 AC-K3-1/AC-K3-2 压制 | 母任务 PRD K3「来源与设计引用」 | covered | OI-03, OI-04 |
| R-023 | deferred：停摆流水线接管登记（S7） | 母任务 PRD K3「来源与设计引用」 | covered | DEF-K3-3 |
| R-024 | 结构性遗留：成本基线不可得（K3 的 AC-K3-2 补齐）；CompanyBrain 评测集仅 6 题且过松（K3 重建） | 母任务 PRD 第 4 节 | covered | OI-04, OI-05, OI-09 |
| R-025 | K1/K2 已完成提交，K3 验收依赖其产物：K1 批次目录 `_audit/page-manifest.json`（`publish_status` 词表保留 `released` 给 K3）、K2 `navigation.navigation_status=generated_ok` | 用户原话；K1 spec SCN-013/FR-AUD-004；K2 spec SCN-K2-008 | covered | OI-12, OI-13 |
| R-026 | 主会话上下文控制：大块材料不整卷吞入，取证派子代理，主会话只收结论与证据引用 | 用户原话；母任务 NG-002 | covered | NG-002；`## 调研` |
| R-027 | **方向纠正（覆盖前序误解）**：发布 = 把新知识落盘到一个指定文件夹（例如下载文件夹的 `KD测试`）；与 gbrain 完全无关、与既有 1347 页知识库完全无关；KD 的功能是把新文档基于一个已存在的知识库或新知识库**直接消化合并**；「发布/检索层/gbrain」被用户明确指为伪需求 | 用户原话 2026-09-15（Talk R3 Q1 自由回答，逐字见 `## Talk`） | covered | OI-11, OI-15, NG-009, NG-010, DEF-K3-2 |
| R-028 | 「安全地交出去」= 指定知识库目录永不处于半成品状态（完整新版或完整旧版），失败显式、可回滚、成本可查；观察对象=该目录本身（Obsidian 直接打开即可读） | 用户原话 R-027 的直接含义；母任务 S5 | covered | OI-01, OI-03, OI-04, NG-010 |

**未覆盖/待定**：无。R-008…R-028 全部落到 OI、D 条目、AC、非目标或延期项；OI 大纲 16 项终态已回填。

### 用户原话（逐字，未改写）

> 「请检查"/Users/Hugh/Hugh/Project/KnowledgeDigest/specs/archive/task6-effect-gap-and-architecture-reset/prd.md"，其中K1和k2都完成提交了，我准备开始其中K3任务了。
>
> 我希望现在按标准 WorkflowHub 开始这个任务，先创建worktree，然后从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。先基于原始需求，在make-decision的过程中和我一起仔细梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。注意主会话上下文控制和子代理派发。Talk 和grill请用大白话说明选项、后果和风险；」

## 核心需求

**让 KnowledgeDigest 把新文档消化合并进一个指定的知识库目录时，那个目录永远不处于半成品状态——要么是完整的新版本、要么是完整的旧版本；并且「这一批知识到底能不能用」由一个可复跑的真实问题集来判定，判定失败必须显式失败，不得靠机器自证绿灯。**

一句话拆开：① 换版要原子（读者打开该目录只看到完整新旧版本之一）；② 回滚要一条命令；③ 失败运行的耗时/调用数/token 必须真实可查（修掉 `observed_calls=null`）；④ 对照验收前先冻结三份东西；⑤ 逐题判定的记录必须能机器重跑。

**边界（R-027 用户纠正，覆盖前序误解）**：KnowledgeDigest 是独立工具；不接 gbrain、不做检索层、不写既有 1347 页知识库（它只在对照验收中作只读快照）。

## 核心目标

| 目标 | 可观察的成功 | 依据 |
| --- | --- | --- |
| G1 发布安全 | 四类负例（写入中断/取消/校验失败/越界写入）注入后，指定知识库目录要么等于旧版 tree hash、要么等于新版 tree hash；一条命令回滚 | FR-K3-1；R-017；R-028 |
| G2 失败不伪装 | 成功与失败运行的耗时/调用数/token 三项真实非 null，真 0 带 reason | FR-K3-2；R-015 |
| G3 判定可复跑 | 同一问题集 + 三份冻结物 + 被验收树指纹下逐题给出四结果，机器重放逐题一致，汇总通过与失败可执行 | FR-K3-3；R-020 |
| G4 问题集有效 | 在基线缺陷样本上能查到坏产物、且不惩罚正确结果 | FR-K3-4；R-024 |
| G5 冻结物齐备 | 三份冻结物存在、逐文件 sha256 清单可复算；缺一即 blocked、不出逐题结论 | FR-K3-5；R-019 |

## 已选方向

**Talk R1/R2 用户已定的方向**（大白话）：

- **发布单元**：整个发布区根目录一次性换（整库原子）——读者要么看到完整新版，要么看到完整旧版。
- **操作方式**：两条命令，发布一条、回滚一条，都不需要人工确认（母任务已接受「全自动、出错内容会直接进库」的风险，用负例验收压制）。
- **可回滚版本**：发布前先备份当前版本，保留最近 1 个可回滚版本；切换失败自动恢复。
- **写权落点（Talk R3 Q1 已按用户纠正重述）**：发布目标 = **一个指定的知识库目录**（例如 `~/Downloads/KD测试`），可以是新知识库，也可以是用户指定的某个知识库目录；K1/K2 的 `products/` 树按既有目录/命名规范合并进去。**与 gbrain、与既有 1347 页知识库完全无关**；既有知识库只在对照验收时作为只读冻结快照（R-027）。
- **「安全地交出去」的观察对象（R-028）**：就是那个知识库目录本身——读者用 Obsidian 打开即可读，不依赖任何外部索引。负例后该目录必须**要么等同旧版、要么等同新版**。
- **失败口径**：失败运行必留「原因码 + 耗时 + 调用数 + token/成本」；真 0 合法但要写原因；任一项 null 判失败。
- **冻结**：三份冻结物各做不可变内容快照 + 逐文件 sha256 清单（不依赖 git）。
- **范围**：以 K3 为主；可以修发布/验收链路暴露的 K1/K2 缺陷，但**必须先记录再修，且不重做 K1/K2 的核心能力**。
- **区分度**：用基线缺陷样本双向验证（能查到坏 + 不冤枉好）。
- **落点选择（调研结论）**：复用/改造 `full_release.atomic_release`（整包替换 + 保留旧版 + 失败自动恢复 + 替换函数可注入）的语义；**不复用** `publisher.commit`（要求空目录、不留旧版）。
- **争议项**：出题方式用户选「从资料自动生成」，与母任务 OPEN-002 和 ADR-0014 冲突，留 Talk Round 3 重新裁决。

## 验收标准

**场景**：以 89 份冻结 Confluence Markdown 为输入，先由 K1/K2 编译出一个 `not_released + complete + navigation=generated_ok` 的批次，再由本卡的发布命令把该批次合并进**用户显式指定的知识库目录**；随后注入四类负例，并用冻结问题集做一次逐题对照判定。

**数据来源**：① 89 份输入的逐文件 sha256 清单；② 改造前产物快照（`~/Downloads/KnowledgeDigest-task5-m402-20260908.release4`，14 MB / 108 md，已确认在盘）；③ 对照知识库只读快照（`~/Knowledge/CompanyBrain`，1347 md，只读输入、不作发布目标）；④ 被验收知识库目录自身的 tree hash。

**通过条件（pass）**：
- AC-K3-1：四类负例（写入中断 / 取消 / 校验失败 / 越界写入）注入后，**读者可见的当前版本**要么等同旧版 tree hash、要么等同新版 tree hash——**不存在第三种状态**（"取消"定义为进程内协作式取消，在固定检查点触发；不承诺掉电/SIGKILL 崩溃级一致性，该范围须在 spec 写明）。**观察口径**：库根放一个固定名字的**当前版本入口**（指针），读者随时可打开；因此不存在"目录短暂缺失"态。
- AC-K3-2：成功与失败两类运行都能读到 **耗时 / 调用数 / token** 三项且非 null；真实 0 带 reason（`cache_hit` / `no_provider_call_yet` / `provider_unavailable`）。**覆盖范围**：发布命令必须**承接该批次编译侧的 `_audit/run-metrics.json` 三项**（字段分别标明来源）并另记发布段自身消耗；因此"编译已花调用后再失败"这类运行会被真实计量，不得只报 0。
- AC-K3-3：同一问题集 + 三份冻结物 + 被验收树指纹下，逐题四结果可机器重放且逐题一致；同一份记录只能得出唯一汇总结论（"硬失败题"定义与通过阈值须在 spec 冻结为可执行形式）。
- AC-K3-4：问题集在「已知坏产物」样本上能查到坏产物，同时对正确结果不误判；**坏样本必须与题目绑定**（每类缺陷绑定 ≥2 道必须判失败的题 + 期望失败原因），否则本 AC 不得声明可执行。
- AC-K3-5：三份冻结物齐备且逐文件 sha256 可复算（含**排除规则**：跳过 `.` 开头的文件与对照库内 `_gbrain/` 生成镜像；输入清单恰为 89 份 `.md`）；缺一即 blocked、不出逐题结论。被验收树指纹作为**运行参数与记录字段**绑定进判定记录（不属于"冻结物齐备"的组成）。

**失败条件（fail）**：任一负例后出现半成品/混合版本或第三种状态；回滚失败或留混合版本；任一成本项为 null、真 0 无 reason 或 reason 与计数矛盾、或未承接编译侧真实消耗；逐题记录缺失或不可复跑；问题集全过或全不过（无区分度）；坏样本未与题目绑定却声明 AC-K3-4 通过；任一冻结物缺失或 hash 复算不一致仍产出逐题结论；发布写到"允许写位置清单"以外的地方。

**对母任务验收措辞的显式偏离（登记）**：母任务 AC-K3-1 的观察对象写作「读者与 gbrain」。按用户 R-027（KD 与 gbrain 无关），本卡以**指定知识库目录的当前版本整根等价**替代该观察口径；这是对母任务措辞的显式偏离，依据 R-027/NG-009，不静默改写。

## 范围

- 本卡 = 母任务 PRD K3 一张卡：**原子换版通道（发布 + 回滚 + LKG 槽位与指针）+ 失败显式化与成本度量 + 冻结物管理 + 查询集与逐题判定器**。
- 发布目标 = 用户每次运行**显式指定的知识库目录**（新库或指定库）；批次目录为中间产物。
- 不做：K1 语义层页面编译、K2 入口与导航生成、K4 瘦身删码；不接 gbrain/检索层；不写既有 1347 页知识库；不在本阶段改代码、不重跑 provider。
- 允许修发布/验收链路暴露的 K1/K2 缺陷，但必须先记录再修（Talk R2 Q7）。

## 非目标

| 编号 | 非目标 | 依据 | 状态 |
| --- | --- | --- | --- |
| NG-001 | 不做问答/RAG 形态、不做前端或可浏览界面 | 母任务 NG-007；K1/K2 已定 | 继承 |
| NG-002 | 主会话不做重读量取证；取证派子代理，主会话只收结论与证据引用 | 母任务 NG-002；用户 R-005 | 继承 |
| NG-003 | 不在本卡改 K1 编译语义、改 K2 导航生成、执行 K4 删除清单 | 母任务 PRD K3「scope」 | 继承 |
| NG-004 | 不改停摆的自动化流水线 | 母任务 S7/NG-010 | 继承 |
| NG-005 | 不把"机器自证绿灯"重新引入为验收依据（含不复用待删的投影/证书产物作为发布判据） | ADR-0014；母任务 NG-005；红队 F-3 | 继承并强化 |
| NG-006 | 本阶段不承诺 commit/merge/push/archive/cleanup 等不可逆交付动作 | 宿主协议；母任务 NG-006 | 继承 |
| NG-007 | 不引入向量库/图数据库/服务化部署；不做多格式输入 | 母任务 NG-008/NG-009 | 继承 |
| NG-008 | 不新增人工闸门/审批（用户 R1 Q2 已明确） | 母任务 T-010 = B | 已确认 |
| NG-009 | **不接 gbrain、不做检索层、不改任何索引配置**；「发布通道/检索层」不作为本卡交付面 | 用户 R-027 原话 | 用户纠正后新增 |
| NG-010 | **不写既有 1347 页知识库（`~/Knowledge/CompanyBrain`）**：它只在对照验收中作为只读快照出现 | 用户 R-027 原话；母任务 S7 | 用户纠正后新增 |
| NG-011 | 不引入新的 provider 调用形态（发布与验收不调 LLM；问题集由程序从冻结资料确定性生成） | Talk R3 Q4；母任务 NG-003 精神 | 用户纠正后新增 |

## 延期与开放项

| 编号 | 项目 | 处置 | 依据 |
| --- | --- | --- | --- |
| DEF-K3-1 | 停摆流水线接管登记（`synthesize_*` 主题与自动化规则移交） | 延期给 owner=用户；触发=流水线恢复时 | 母任务 S7；PRD 第 4 节 |
| DEF-K3-2 | ~~gbrain 实时检索的端到端验证~~ **按 R-027 作废**：gbrain 不是本卡交付面 | 关闭（非目标 NG-009） | 用户 R-027 原话 |
| DEF-K3-3 | 真实 89 份全链路对照验收的时点（本卡机制先跑通 vs 等 K4 合并后作门禁） | 待 build-spec/plan 与用户确认；本卡先保证机制可跑通 | 母任务 PRD K3「依赖」 |
| OPEN-K3-1 | 问题集题目本身（OPEN-002，母任务原意需用户参与出题） | 出题方式已裁决为机器生成（用户 R3 Q4）；冲突登记为 RISK-K3-2 | 母任务 PRD 第 4 节 |
| OPEN-K3-2 | 发布通道与既有 `full_release.atomic_release`（含 Task5 质量门）的关系 | **已定方向**：不复用其入口与完整包判据（含待删自证产物），只借鉴「锁内整包替换 + 失败自动恢复」机械，另写 LKG 槽位与指针（Talk R3 Q2） | Talk R3 Q2 + `## 调研` |
| OPEN-K3-3 | 「指定知识库目录」最终形态（已定向为运行参数） | 定向：grill G-2=A；参数形态归 build-plan | grill G-2 |

## 完整用户旅程

角色：**运行者**（用户本人，跑发布/回滚命令）、**读者**（用 Obsidian 直接打开指定知识库目录查产品知识）、**验收人**（用户 + 可复跑的验收命令）、**维护者**（下一位改 KD 的人）。**注意**：本卡不涉及 gbrain、检索层与既有 1347 页知识库（R-027）。

| # | 阶段 | 谁做 | 发生什么 | 成功的样子 | 失败/中断的样子 |
| --- | --- | --- | --- | --- | --- |
| J1 | 指定目标库 | 运行者 | 运行发布命令时显式给出目标知识库目录 | 目标目录被接受；首次发布到空目录即建默认骨架 | 目录不是知识库形态且不允许新建：明确拒绝并说明 |
| J2 | 待发布把关 | 系统 | 读批次 manifest 与 navigation，判断这一批是否够格 | 只有 `run_status=complete` + `publish_status=not_released` + `navigation=generated_ok` + `blockers` 空 的批次被接受 | 任一条件不满足：拦下并写明 reason |
| J3 | 备份与暂存校验 | 系统 | 把当前知识库整份放入 LKG 固定槽位并写指针；把新内容复制/校验到暂存区 | LKG 指针含 tree hash 与时间；校验失败不碰正式目录 | 校验失败：正式目录字节不变 |
| J4 | 原子换版 | 系统 | 在库级写锁内把目标目录换成新版本 | 读者打开目录只看到完整新版本 | 中断/取消/越界：只见完整旧版本 |
| J5 | 失败显式化 | 系统 | 失败运行时落真实耗时/调用数/token 与原因 | 三项计数非 null 且与 reason 不矛盾 | 出现 null / 虚报 / 无原因码 |
| J6 | 回滚 | 运行者 | 需要时回到上一可用版本 | 一条命令按指针回滚，目录全程可读 | 回滚失败或留下混合版本 |
| J7 | 冻结 | 验收人 + 脚本 | 冻结 89 份输入清单、改造前产物快照、对照知识库快照 | 三份冻结物齐备、逐文件 sha256 可复算、frozen_id 确定性 | 任一缺失或 hash 不一致：blocked，不出逐题结论 |
| J8 | 出题与逐题判定 | 验收命令 | 用确定性规则从冻结资料生成问题集，逐题给出四结果 | 每题留下可复跑记录，记录绑定被验收树指纹 | 缺逐题记录 / 被测对象已变 / 不可复跑 |
| J9 | 汇总 | 系统 | 按冻结规则给出通过与失败 | 同一份记录只能得出唯一结论，「对照未覆盖」不计我方优势 | 全过或全不过（无区分度） |
| J10 | 全链路门禁（时点见 DEF-K3-3） | 宿主/用户 | K1/K2/K4 合并后用本卡验收命令做门禁 | 门禁结论可复跑 | 用其他绿灯替代 |

## UI applicability

```json
{
  "result": "non_ui",
  "sources": {
    "raw_requirement": {"applicability": "non_ui", "fact": "用户要求做 K3：发布安全（staging/原子切换/回滚）+ 真实查询集验收（冻结快照/问题集/逐题判定记录）；全程是命令、文件、快照与判定记录，未要求任何浏览器页面、路由或交互组件"},
    "project_inventory": {"applicability": "non_ui", "fact": "KnowledgeDigest 是 Python CLI 工具（src-layout）；现有可观察面是 CLI 输出、批次目录 Markdown 与 _audit JSON/JSONL；同 K1/K2 已判定 non_ui"},
    "planned_or_changed_frontend_fact": {"applicability": "non_ui", "fact": "本任务不新增、不修改任何前端或界面实现；发布目标是本地目录，读者用 Obsidian/gbrain 消费，不是本卡构建的界面"}
  },
  "reason": "三项来源一致为 non_ui：CLI + 本地文件 + 判定记录，无 UI 对象"
}
```

## 收敛检查

| 维度 | 用户答案 | 事实或材料引用 | 可执行验收 |
| --- | --- | --- | --- |
| 目标 | 用户回答：以 K3 为主，并允许顺手修 K1/K2 遗留；让新文档消化结果能安全合并进「用户显式指定的知识库目录」，并用可复跑的真实问题集判定能不能用 | R-007、R-008、R-009、R-010、R-027、R-028；母任务 PRD K3 | 场景：K1/K2 产物就绪后跑一次发布与一次验收；数据来源：K1 批次目录 + 89 份冻结输入 + 三份冻结物快照；通过：发布只呈现完整版本且验收给出逐题判定与明确通过与失败；失败：出现半成品/混合版本或验收结论不可复跑 |
| 范围 | 用户回答：只做原子换版通道、失败显式化与成本度量、查询集/判定器、冻结快照管理；允许修验收暴露的 K1/K2 缺陷（先记录再修），不做 K4 删码；不接 gbrain、不写既有 1347 页知识库 | R-011、R-012、R-013、R-014、R-027；Talk R1 Q0/Q1、R3 Q1 | 场景：一个完整任务周期的边界检查；数据来源：本卡四材料与任务 worktree 差异；通过：改动只落在发布与验收相关路径；失败：改到 K1 编译语义、K2 导航生成、执行 K4 删除，或写到指定目录以外的位置 |
| 方案 | 用户回答：整库原子换版、发布与回滚各一条命令且无人工闸门、固定 LKG 槽位+指针清单保留最近 1 版、失败三项成本真实非 null、冻结用内容快照+逐文件 sha256、验收是单独一条命令+冻结汇总规则、问题集机器生成（冲突如实保留）；取舍=tradeoff 用整库复制与一次短暂切换窗口换「读者永不见半成品」；被拒方案=rejected option 按产品/按页面发布、原地覆盖、直接写既有知识库、整段复用旧发布入口、git 标签冻结；未决项=open item 汇总阈值具体形式、坏样本三类是否足够、问题集题目、全链路验收时点 | R-017、R-019、R-022、R-027；Talk R1 Q1/Q2/Q3/Q5/Q6、R2 Q8/Q9/Q11、R3 Q2/Q3/Q4；grill G-1/G-2/G-3；D-002、D-006、D-007、D-013 | 场景：按上述选择执行一次发布、一次回滚、一次验收；数据来源：任务 worktree 的 CLI 运行结果与冻结物清单；通过：整库原子换版、一条命令回滚、冻结清单可复算、验收唯一结论；失败：需要人工闸门、回滚改变已发布字节或验收不可重放 |
| 验收 | 用户回答：用冻结快照 + 同一组真实问题逐题判定四结果，汇总给出通过与失败；对照侧未覆盖不计我方优势 | R-009、R-016、R-020、R-028；母任务 S8；Talk R3 Q3 | 场景：四类负例注入 + 同一问题集对新知识库目录与冻结对照逐题判定；数据来源：89 份冻结输入 + 改造前产物快照 + 对照知识库快照 + 冻结问题集 + 被验收树指纹；通过：满足五项（负例后目录整根等价于旧版或新版、每题四结果可机器重放且逐题一致、汇总唯一、三项成本非 null、三份冻结物齐备可复算）；失败：判失败（包括：任一负例泄漏半成品、任一逐题记录丢失或无法复跑、汇总条件没写死、任一成本项为 null） |

## OI 大纲（唯一当前版本 · outline_version = v1.0）

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
stage: make-decision
```

### Framework nodes

| framework_node | oi_ids | empty | reason |
| --- | --- | --- | --- |
| background | OI-01 | false | K1/K2 已交付语义层页面与入口，缺「安全合并进指定知识库」与「能不能用」的通道与判定器 |
| problem | OI-04 | false | 发布机械接不上整库原子、失败路径 observed_calls=null、查询集与判定器不存在、冻结物未冻结、LKG 无指针 |
| goal | OI-15 | false | 让新文档消化结果安全合并进指定知识库目录，并让「能不能用」由可复跑问题集判定 |
| solution | OI-01 | false | 整库原子换版、固定入口+指针、发布/回滚各一条命令、LKG 固定槽位、失败三项成本真实、三份冻结物、独立验收命令 |
| acceptance | OI-15 | false | 四类负例整根断言、失败三项非 null、逐题四结果可重放、问题集双向验证、冻结物齐备可复算 |
| extension | OI-16 | false | 延期/开放项：流水线接管、全链路验收时点、知识库目录参数形态 |

### Fixed categories

| category | oi_ids | empty | reason |
| --- | --- | --- | --- |
| complete_user_flow | OI-01, OI-02, OI-16 | false | 整库原子换版、两条命令无人工闸门、固定入口+指针下读者全程可打开 |
| page_scope | OI-11, OI-12, OI-13 | false | 目标知识库目录由运行参数指定；批次白名单冻结；与 K1/K2/K4 边界已切 |
| data_state | OI-05, OI-10, OI-14 | false | 三份冻结物+排除规则；五类数据状态沿用 K1；问题集机器生成（冲突如实登记） |
| success_failure_boundary | OI-03, OI-04, OI-06, OI-07, OI-08, OI-09, OI-15 | false | LKG 与回滚、失败成本、判定记录、四类负例、用途边界、区分度、观察口径 |
| non_goals | OI-01 | false | NG-001…NG-011（不接 gbrain/检索层、不写既有知识库、不改 K1/K2 核心能力、不新增人工闸门等） |
| deferred | OI-16 | false | DEF-K3-1 流水线接管、DEF-K3-3 全链路验收时点、OPEN-K3-3 目标目录参数形态 |

### OI 记录（每项一个可独立处置的收敛项）

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-01
category: complete_user_flow
source: "R-008 / R-013 / PRD K3 用户流程"
question: "发布单元是什么——一次发布以什么为一个整体做 staging、校验、原子切换与回滚？"
status: confirmed
selected_disposition: "Talk R1 Q1=A（整库原子）+ detail-advice D1=A（固定入口 + 指针）+ D2=A（保留库内原有内容、只新增/更新声明托管路径）：以用户显式指定的知识库目录为一个整体做原子换版；读者通过库根固定名字的当前版本入口读到完整版本。"
evidence: "Talk R1 Q1、detail-advice D1/D2 用户真实回复；母任务 S5/OI-17"
acceptance: "负例与换版全程中，当前版本入口可读且内容整根等于旧版或新版之一"
counterexample: "若出现半新半旧的知识库、或跨产品混合态被当作正常发布，即判失败"
impact_dimensions: [scope, acceptance]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-02
category: complete_user_flow
source: "R-022 / RISK-005 / 母任务 T-010=B"
question: "运行者怎么发起发布与回滚——命令形态与人工闸门各自是什么？"
status: confirmed
selected_disposition: "用户选择 A：两条命令——发布一条、回滚一条，都不需要人工确认（继承母任务 T-010=B 全自动、RISK-005 已接受）。"
evidence: "Talk R1 Q2 用户真实回复；母任务 T-010=B / RISK-005"
acceptance: "两条命令各有独立退出码与非零失败语义；失败运行留下机器可读原因与成本三项"
counterexample: "若日常发布需要人工逐次批准，或敲错命令能越过库级写锁直接换库，即与本次选择冲突"
impact_dimensions: [scope, ordinary_detail]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-03
category: success_failure_boundary
source: "R-011 / R-017 / FR-K3-1"
question: "last-known-good 与回滚边界做到什么程度——保留几版、回滚是否自动、回滚后可查性怎么保证？"
status: confirmed
selected_disposition: "Talk R1 Q3=A（保留最近 1 个可回滚版本）+ Talk R3 Q2=A（固定槽位 + 指针清单，自写回滚机械）+ detail-advice D1=A（改为「固定入口 + 指针」，读者永远能打开，不存在目录没写死窗口）+ D3=A（LKG 与失败记录放库外同级隐藏目录）。**已否决旧表述**：「复用/改造 `atomic_release` 可作为落点」与「保留旧版可复用」不再成立，见 D-002/D-010。"
evidence: "Talk R1 Q3、Talk R3 Q2、detail-advice D1/D3 用户真实回复；`## 调研` 取证一 #1a/#1b/#2"
acceptance: "一条命令按指针回滚且当前版本入口始终可读；LKG 槽位不计入被验收 tree hash"
counterexample: "若回滚失败留下混合版本、或读者在换版期间读不到当前版本入口，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-04
category: success_failure_boundary
source: "R-015 / R-024 / FR-K3-2 / 母任务 OI-26"
question: "失败显式化与成本度量的边界——失败运行必须留下什么才算没伪装成功，null 与真零怎么区分？"
status: confirmed
selected_disposition: "Talk R2 Q8 用户改选 A：失败运行必留「原因码 + 耗时 + 调用数 + token/成本」三项真实非 null；真实发生的 0 合法但必须附 reason（cache_hit / no_provider_call_yet / provider_unavailable），无法归因的 0 或与 reason 矛盾判失败；任一 null 判失败。R1 Q4 的初选 B（token 允许「不可得」）已被覆盖。**detail-advice D4 用户裁决**：覆盖范围含**承接批次编译侧 `_audit/run-metrics.json` 的三项消耗**并另记发布段自身消耗（避免发布段 0+reason 的真空满足）。`publisher.py:113` 的修复可达性须在 spec 写明归属，不留空承诺。"
evidence: "Talk R2 Q8、detail-advice D4 用户真实回复；母任务 R-017/OI-26；代码事实 publisher.py:113（失败路径 observed_calls 硬编码 null）；成本三项来源见 `## 调研` 取证一 #3"
acceptance: "成功与失败运行都可读到三项非 null；真 0 带 reason；发布段与编译段分别标明来源"
counterexample: "若失败运行的耗时/调用数/token 任一项为 null、或真 0 无 reason、或 reason 与计数矛盾、或未承接编译侧真实消耗，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-05
category: data_state
source: "R-019 / R-024 / FR-K3-5 / 母任务 S2"
question: "三份冻结物怎么定义、怎么冻结、怎么证明齐备——改造前 release4 产物快照与 CompanyBrain 快照各自冻结什么粒度？"
status: confirmed
selected_disposition: "Talk R1 Q5=A + detail-advice（D-006 排除规则）：三份冻结物各做不可变内容快照 + 逐文件 sha256 清单（不依赖 git），冻结 ID 由清单内容确定性导出；排除 `.` 开头文件与对照库 `_gbrain/` 生成镜像；输入恰 89 份 `.md`。"
evidence: "Talk R1 Q5 用户真实回复；母任务 S2；红队 N-9；蓝队 DB12"
acceptance: "按登记的排除规则重算清单与 frozen_id 一致；缺任一冻结物或 hash 不一致即 blocked"
counterexample: "若任一冻结物没写死、或清单与快照内容对不上仍被当作齐备，即判失败"
impact_dimensions: [acceptance, scope]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-06
category: success_failure_boundary
source: "R-016 / R-020 / FR-K3-3 / 母任务 OI-25"
question: "逐题判定的四结果与汇总通过条件怎么可执行、怎么可复跑——判定记录的载体与重放口径是什么？"
status: confirmed
selected_disposition: "Talk R3 Q3=A（单独一条验收命令 + 冻结汇总规则）+ detail-advice D1（按当前版本入口做整根断言）与 D2（证据页逐字节复制，保证定位/出处判据不漂移）。判定记录载体 = 验收运行目录下的机器可读记录，绑定被验收树指纹 + 问题集 sha256 + 判定口径版本；汇总规则须在 spec 补齐「硬失败题」定义与通过阈值（OPEN-K3-4）。"
evidence: "Talk R3 Q3、Talk R2 Q10；detail-advice D1/D2 用户裁决；母任务 S8/OI-25；蓝队 B3/DB3"
acceptance: "同一问题集 + 同一被验收树指纹下逐题四结果机器重放一致；同一份记录只能得出唯一汇总结论"
counterexample: "若记录没写死、不可重放、或同一份记录可被判通过也可被判失败，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-07
category: success_failure_boundary
source: "R-011 / R-017 / FR-K3-1"
question: "四类负例（写入中断/取消/校验失败/越界写入）怎么注入、由谁验证、读者与 gbrain 的「只见到完整版本」怎么观察？"
status: confirmed
selected_disposition: "Talk R2 Q9=A + detail-advice D1=A（观察对象=当前版本整根等价）+ D-009：四类负例逐一注入并机器验证；「取消」定义为进程内协作式取消；越界负例用 fixture 批次含未声明路径注入；no-op 发布须在 spec 明确。调研已证注入点齐全且已有先例（kb_lock 获取、copytree、拷贝后树哈希、两次 os.replace、projection 校验），另有 `replace_fn` 可注入。"
evidence: "Talk R2 Q9、detail-advice D1 用户真实回复；`## 调研` 取证一 #4（test_task3_quality_release.py:815-875 等）；红队 N-1/N-10；蓝队 DB11"
acceptance: "四类负例各有可复算注入方式与断言；负例后当前版本整根等价于旧版或新版之一"
counterexample: "若任一负例后出现第三种状态、或某类负例无法复算注入，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-08
category: success_failure_boundary
source: "R-009 / R-020 / FR-K3-3"
question: "问题集与判定记录器的作用边界——是「验收工具」还是「合并门禁」？谁触发、结论给谁看、结论是否阻塞合并？"
status: confirmed
selected_disposition: "Talk R3 Q3=A：验收是**独立一条命令**（读冻结物 + 问题集 + 被验收树指纹，产出机器可读判定记录），不在发布时自动运行；结论给验收人（用户）看，并作为母任务所述「K1/K2/K4 合并后的全链路门禁」的输入。**是否阻塞合并属宿主/用户的授权动作**（commit/merge 需另行授权），本卡只负责产出可复跑结论与唯一通过/失败。"
evidence: "Talk R3 Q3 用户真实回复；母任务 PRD K3「依赖」（合并依赖=全链路门禁）；宿主协议（合并需明确授权）"
acceptance: "验收命令可独立运行并产出机器可读结论；同一输入给出唯一结论"
counterexample: "若验收只能作为发布的附属步骤运行、或结论依赖人解释，即判失败"
impact_dimensions: [goal, acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-09
category: success_failure_boundary
source: "R-010 / R-024 / FR-K3-4"
question: "问题集有效性（可区分度）怎么证明——在什么基线上、用什么检查，既不惩罚正确结果又能识别全过/全不过？"
status: confirmed
selected_disposition: "Talk R2 Q9=A + **detail-advice D9（并入 N-6）**：在「已知坏产物」样本上双向验证；坏样本必须与题目绑定（每类缺陷绑定 ≥2 道必须判失败的题 + 期望失败原因），样本与绑定关系随冻结物入库并登记 sha256；未完成绑定即不得声明 AC-K3-4 可执行。"
evidence: "Talk R2 Q9 用户真实回复；detail-advice D9 用户裁决；红队 N-6；蓝队 DB9；母任务 detail finding（问题集有效性判定会惩罚正确结果）"
acceptance: "三类坏样本各自的绑定题全部判失败，且正确产物上同一批题不判失败"
counterexample: "若坏样本未与题目绑定、或坏产物全过、或正确产物被误判失败，即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-10
category: data_state
source: "R-021 / 母任务 S3"
question: "五类数据状态（ready/known_empty/duplicate_alias/audit_only/资料未明确）在发布与验收两侧怎么处置——未明确是否进分母、重复来源单页化是否在发布侧再次校验？"
status: confirmed
selected_disposition: "继承 K1 已冻结契约，不在发布侧重算：五类来源级状态与 claim 级「资料未明确」由 K1 写入 `_audit/page-manifest.json` 的来源台账；发布侧只读并把它作为**逐字节复制**的证据内容，不做二次判定、不改写。「资料未明确」不进事实分母，验收侧沿用 K1 口径。「重复来源单页化」由 K1 的 `duplicate_alias` 与别名登记保证，发布侧不重新判定、只校验台账与页面条目一致。"
evidence: "K1 FR-AUD-002/003（`specs/archive/task7-semantic-layer-compiler/spec.md`）；detail-advice D2（证据页逐字节复制）；母任务 S3/OI-18"
acceptance: "发布后知识库内的来源台账与批次一致；「资料未明确」未被写成结论、未进分母"
counterexample: "若发布侧改写或重算五类状态、或把「资料未明确」当成肯定结论发布，即判失败"
impact_dimensions: [ordinary_detail]
requires_user_decision: false
visible_group_id: R2
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-11
category: page_scope
source: "R-018 / R-025 / 母任务 S7"
question: "发布写权边界落到哪个目录——新编译出来的页面被消化合并进哪个知识库目录？"
status: confirmed
selected_disposition: "Talk R1 Q6 + Talk R2 Q11 + **Talk R3 Q1 用户纠正**：发布目标 = 一个**指定的知识库目录**（例如下载文件夹的 `KD测试`），可以是新知识库，也可以是用户指定的某个知识库目录；该目录自带结构声明与「只写这些路径」列表。**与 gbrain、与既有 1347 页知识库完全无关**；既有知识库只在对照验收中作为只读冻结快照。K1/K2 的 `products/` 树按既有目录/命名规范落进该知识库目录。"
evidence: "Talk R1 Q6、Talk R2 Q11、Talk R3 Q1 用户真实回复（R-027 逐字）；目录事实（`~/Downloads/KD测试` 现有批次命名 `YYYY-MM-DD-<n>`）"
acceptance: "发布只写「允许写位置清单」内的路径；目标知识库目录内的托管页面与结构页按 D-004 合并规则更新"
counterexample: "若发布动作写到了该指定目录以外的任何位置（尤其是既有知识库或 gbrain 配置），即判失败"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R3
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-15
category: success_failure_boundary
source: "R-027 / R-028 / 红队 F-2 / 蓝队 M5"
question: "「安全地交出去」的观察对象是什么——负例注入时，谁在什么地方观察「只见完整新旧版本」？"
status: confirmed
selected_disposition: "Talk R3 Q1 用户纠正后重述 + **detail-advice D1 用户改选 A（固定入口 + 指针）**：观察对象 = 读者可见的**当前版本整根等价**；库根放固定名字的当前版本入口指向最新版本，读者随时可打开，因此不存在目录没写死态。负例注入期间与之后断言「当前版本 tree hash 要么等于旧版、要么等于新版」，不存在第三种状态；不引入 gbrain 或任何外部索引。"
evidence: "Talk R3 Q1 用户真实回复（R-027/R-028）；detail-advice D1 用户裁决；红队 F-2/N-1；蓝队 M5"
acceptance: "当前版本入口在负例全程可打开；当前版本整根等价于旧版或新版之一"
counterexample: "若存在第三种状态（半成品、混合版本、当前版本入口不可达），即判失败"
impact_dimensions: [acceptance]
requires_user_decision: true
visible_group_id: R3
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-16
category: complete_user_flow
source: "R-027 / R-028；红队 F-4"
question: "从「跑完编译」到「新知识已经在指定知识库目录里可读」这条日常流程是什么——一次发布里发布根与旧版各自的角色、读者在切换期间会不会读到没写死状态？"
status: confirmed
selected_disposition: "Talk R3 Q2/Q3 + **detail-advice D1=A（固定入口 + 指针，读者永远能打开，不存在没写死窗口）** + D3=A（LKG 与失败记录在库外同级隐藏目录）。日常流程 = 指定目标库 → 批次白名单把关 → 库外备份当前版本并写指针 → 原子换版并更新入口指针 → （失败）按指针一条命令回滚。"
evidence: "Talk R3 Q2/Q3 用户真实回复；detail-advice D1/D3 用户裁决；红队 F-4/N-1；`## 调研` 取证一 #1a"
acceptance: "换版全过程读者可通过当前版本入口读到完整版本；发布失败不改变当前版本内容"
counterexample: "若换版期间当前版本入口不可达或内容没写死/混合，即判失败"
impact_dimensions: [goal, acceptance]
requires_user_decision: true
visible_group_id: R3
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-12
category: page_scope
source: "R-025 / K1 FR-AUD-004 / K2 SCN-K2-008"
question: "发布侧接受哪些产物作为合法输入——K1 manifest 的哪些字段、K2 navigation 的哪些取值，缺哪个字段一律拦下？"
status: confirmed
selected_disposition: "冻结为字段级白名单（见 D-011）：`run_status == complete`、`publish_status == not_released`、`navigation.navigation_status == generated_ok`（必须显式等于，不得写成「不等于 blocked 就放行」）、`blockers` 为空数组；缺任一即 blocked 并写明 reason。`publish_status=released` 由 K3 自己的发布记录承载（引用批次 manifest 的 attempt_id + hash），不回写 K1 manifest 的既有语义。"
evidence: "Talk R2；K1 spec SCN-013/FR-AUD-004；K2 spec SCN-K2-008；`## 调研` 取证一 #6a；蓝队 M6"
acceptance: "四条件任一不满足的批次一律被拦下并给出 reason；合法批次正常进入发布"
counterexample: "若缺字段或异常批次仍被放行、或 K3 回写改写了 K1 manifest 的既有语义，即判失败"
impact_dimensions: [scope, acceptance]
requires_user_decision: true
visible_group_id: R2
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-13
category: page_scope
source: "R-007 / R-012 / R-014"
question: "本卡与 K1/K2/K4 的边界怎么切——哪些东西必须由本卡提供、哪些留给兄弟卡（含 K4 删除后的成本度量归属）？"
status: confirmed
selected_disposition: "Talk R1 Q0 + Talk R2 Q7 用户选择：以 K3 为主，允许修发布/验收链路暴露的 K1/K2 缺陷，但必须先记录再修，且不重做 K1/K2 的核心能力（编译语义、导航生成）。真实接口事实：K1 manifest=`task7-page-manifest.v1` 且 K1 只允许 `publish_status=not_released`；K2 `navigation` 写回同一 manifest、`run_status∈{complete,blocked,interrupted}`。"
evidence: "Talk R1 Q0、Talk R2 Q7 用户真实回复；`## 调研` 取证一 #6a"
acceptance: "缺陷台账存在且每条 K1/K2 缺陷有等级与处置；未重做 K1/K2 核心能力；任何 K1/K2 修复伴新批次全量重跑"
counterexample: "若范围失控到重做 K1 编译语义或 K2 导航生成，即与母任务分卡约定冲突"
impact_dimensions: [scope]
requires_user_decision: true
visible_group_id: R1
```
```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
oi_id: OI-14
category: data_state
source: "R-014 / 母任务 OPEN-002 / ADR-0014 / Talk R2 Q10"
question: "验收问题集从哪来、谁出题、怎么冻结——用户出题、模型起草后用户确认，还是从资料自动生成？"
status: confirmed
selected_disposition: "Talk R2 Q10 + **Talk R3 Q4=C 用户维持**：从资料自动生成题目（用户真实选择）。**冲突如实保留**：与母任务 R-014/OPEN-002「用户参与出题」及 ADR-0014「human-authored question set」不一致，登记为 RISK-K3-2 与 OPEN-K3-6；本阶段不静默改写，build-spec 必须保留该冲突声明。"
evidence: "Talk R2 Q10、Talk R3 Q4 用户真实回复；母任务 PRD OPEN-002；ADR-0014（`docs/adr/0014-real-query-set-acceptance.md`）；红队 F-1；蓝队 M3"
acceptance: "问题集生成规则与产物随冻结清单登记并带 sha256；区分度按 D-008 双向验证"
counterexample: "若在未登记冲突的情况下把自动生成问题集当作「真实读者问题」使用，即与母任务验收口径冲突"
impact_dimensions: [acceptance, goal]
requires_user_decision: true
visible_group_id: R3
```

## Talk

### Talk Round 1（step 3）· 已收到用户真实回复

问题卡：`specs/task9-release-safety-query-acceptance/decision-log.md#Talk`（本文件，已按题登记）；交互方式：主会话发出 → 等待 → 用户真实答复 → 继续。

| 编号 | 决策轴 | 选项（大白话） | 后果 | 风险 | 用户选择 |
| --- | --- | --- | --- | --- | --- |
| Q0 | 本卡范围 | A 只做 K3；B K3 + 顺手补 K1/K2 遗留；C 先只做发布通道 | A 范围清楚可独立验收；B 更快看到好结果但责任不清；C 最快看到安全发布但只交一半 | A 全链路结论要等 K1–K4 齐；B 范围翻倍、验收归因困难；C 判定器推迟、重建对照更贵 | **B：K3 + 顺手补 K1/K2 遗留**（范围扩大，边界在 Talk R2 收口） |
| Q1 | 发布单元 | A 整库原子；B 按产品原子；C 按页面 | A 读者永不见半新半旧、回滚最简单；B 切换快但跨产品导航会混合；C 实现最简单 | A 知识库大时复制/切换耗时长；B「只见完整版本」需重新定义；C 中途失败即半成品，与 AC-K3-1 冲突 | **A 整个知识库根目录一次性换（整库原子）** |
| Q2 | 发布/回滚流程 | A 两条命令、都不需人工确认；B 发布前人工确认一次；C 单命令多动作 | A 符合母任务 T-010=B 全自动；B 多一道保险；C 便于以后扩展 | A 敲错命令会直接换库（需库级写锁与声明路径硬检查）；B 推翻母任务已定方向；C 日常更易敲错 | **A 两条命令：发布一条、回滚一条，均无人工闸门** |
| Q3 | last-known-good 与回滚 | A 保留最近 1 版；B 保留 2–3 版可连退；C 不留旧版靠重编译 | A 一条命令回退一步，满足「只见完整新旧版本」；B 更保险便于对照；C 省空间 | A 占一份额外磁盘、不能连退；B 磁盘成倍且需「哪版能删」规则，范围变大；C 重跑不保证同结果，回滚不确定，与 AC-K3-1 冲突 | **A 发布前备份当前版本，保留最近 1 个可回滚版本** |
| Q4 | 失败与成本口径 | A 耗时+调用数+token（真 0 带原因，null 判失败）；B 原因码+耗时+调用数（token 允许「不可得」）；C 只留原因码 | A 直接修掉 null 缺陷、验收可机器判定；B 能回答「失败不伪装」；C 实现最少 | A provider 挂时 token 真拿不到，需「provider 不可用+估算依据」；B 与母任务「失败运行 token 不得为 null」不一致；C 保留 F-002 缺陷 | **B 原因码 + 耗时 + 调用数（token 允许记「不可得」）**——与母任务 R-017/OI-26 有偏差，已登记为 Talk R2 待确认项 |
| Q5 | 三份冻结物怎么冻结 | A 内容快照 + 逐文件 sha256 清单；B git 提交/标签当冻结 ID；C 只记版本标识与统计 | A 不改变知识库维护方式、随时可复算；B 历史可查；C 省空间 | A 多占一份磁盘；B 把现有知识库变成 git 仓库，触及写权边界；C 无法复现当时内容，对照结论无效 | **A 内容快照 + 逐文件 sha256 清单（不依赖 git）** |
| Q6 | 发布写权落点 | A 先发独立发布目录；B 直接发进现有知识层但只新增不覆盖；C 发中转区由人搬入 | A 零污染、负例可随便注入；B 真正做到「交出去」；C 人可控 | A 离「真的放进知识层」还差一步；B 页面碰撞即改用户正式页，违反 S7；C 加了人工环节，与全自动方向不一致 | **A 先发到一个独立发布目录（不动现有知识库）** |

**Round 1 直接结论**：整库原子发布、两条无人工闸门命令、保留 1 个可回滚版本、冻结用「内容快照 + 逐文件 sha256 清单」、发布先落在独立发布目录、范围以 K3 为主并允许顺手修 K1/K2 遗留（边界待 R2 收口）。

**Round 1 暴露的待确认项**：Q4-B 与母任务硬约束（失败运行 token/成本不得为 null）不一致，须在 Talk R2 请用户明确取舍并记录。

### Talk Round 2（step 5）· 已收到用户真实回复（输入=step 4 调研取证）

| 编号 | 决策轴 | 选项（大白话） | 后果 | 风险 | 用户选择 |
| --- | --- | --- | --- | --- | --- |
| Q7 | K3 与 K1/K2 的修复边界 | A 可以修但先记录、不重做 K1/K2 能力；B 可以大范围修含改 K1/K2 能力；C 一律不修只记录 | A 范围清楚责任分明；B 最快跑通全链路；C 最干净 | A 个别缺陷带病等到回 K1/K2；B 验收归因困难、与分卡约定冲突；C 小缺陷可能卡住全链路验收 | **A 可以修，但必须先记录再修，且不重做 K1/K2 的核心能力** |
| Q8 | 失败运行 token 口径（母任务冲突项） | A 维持母任务硬约束（三项真实非 null，真 0 带原因）；B 用 R1 口径（token 允许「不可得」） | A 与母任务验收一致、机器可判；B 实现简单 | A 需 provider 失败时仍能给出调用记录，实现要多花力气；B 会在验收时被单独质疑 | **A 维持母任务硬约束：三项真实非 null，真 0 带原因**（覆盖 R1 Q4 的初选 B） |
| Q9 | 问题集区分度怎么证明 | A 基线缺陷样本上验证「能查到坏产物 + 不惩罚正确结果」；B 只验证能区分坏产物；C 靠人工评审对照快照 | A 机器可跑、双向保护；B 成本低；C 最贴近真实 | A 要先造「已知缺陷样本」，多一步工作量；B 无法证明不冤枉正确结果；C 无法机器重放 | **A 在基线缺陷样本上验证：能查到坏产物 + 不惩罚正确结果** |
| Q10 | 验收问题集来源 | A 你出题后冻结；B 模型起草你确认；C 从资料自动生成 | A 题目真实代表读者需求；B 省时间；C 最快、无需人参与 | A 需要你投入时间出题（母任务已标记 OPEN-002）；B 可能偏成「系统好答」的题；C 容易变成对着答案出题、不符合「真实问题」定义 | **C 从资料自动生成题目**——**与母任务「用户参与出题」及 ADR-0014「human-authored question set」不一致，已登记为 Talk Round 3 / direction-advice 争议项，不得静默采纳** |
| Q11 | 独立发布根目录形态 | A 新建独立发布根目录（有自己的结构声明与只写路径列表）；B 复用现有知识库发布约定（kb 根 + 结构声明 + commit）；C 先发临时目录人工搬入 | A 零污染、负例可随便注入、与 formal-root 前置兼容；B 复用已有校验；C 最安全 | A 要新增目录与结构声明，以后上线知识库需再确认一步；B `commit` 要求空目录且不留旧版，与整库换版冲突；C 把一条命令拆成两步、多一个人工环节 | **A 新建独立发布根目录（有自己的结构声明）** |

**Round 2 直接结论**：范围可修但先记录后修、不重做 K1/K2；失败运行三项成本必须真实非 null；问题集区分度用基线缺陷样本双向验证；出题方式为「从资料自动生成」（**争议项，进 Round 3**）；新建独立发布根目录承载整库原子发布。

### Talk Round 3（step 7）· 输入 = direction-advice 红/蓝审查 findings；含一次用户方向纠正

**审查输入（step 6，真实执行）**：红队 18 条 finding（blocking F-1…F-6）+ 蓝队 15 条 finding（blocking B1…B3）。全文落盘见 `review/task9-direction-red.md`、`review/task9-direction-blue.md`；主会话只保留结构化摘要与处置（上下文守恒）。

| 编号 | 决策轴 | 选项（大白话） | 后果 | 风险 | 用户选择 |
| --- | --- | --- | --- | --- | --- |
| R3-Q1 | 「真的交出去」的落点（红队 F-2 / 蓝队 M5） | A 只到发布根、检索层延期；B 接进知识层受控区 + gbrain 可检索做成验收步骤；C 直接以现有知识库为整库发布目标 | — | — | **用户否决该问题的前提（逐字，见下）**：「和gbrain完全无关，和1347个页面的原知识库完全无关！KnowledgeDigest和原来的知识库完全没关系，你说的发布、检索层、gbrain都是伪需求！KnowledgeDigest的功能就是把一些新文档基于某一个已存在的知识库或新知识库，直接消化合并！」→ **R3-Q1 的三选项全部作废**；本卡交付面 = 把新文档消化合并进一个指定知识库目录（例如下载文件夹的 `KD测试`），gbrain 与既有 1347 页知识库都不在本卡视野内。 |
| R3-Q2 | 「保留 1 个可回滚版本 + 一条命令回滚」怎么落地（蓝队 B1 / 红队 F-5） | A 固定槽位 + 指针清单，自己写回滚机械；B 发布记录保留多版可连退；C 不留副本靠重编译 | A 一条命令回滚真正落地、旧版不无限堆；B 可连退多版；C 省磁盘 | A 需自写指针与轮换；B 需额外定义「哪版可用」与清理规则、范围变大；C 回滚不确定，与 AC-K3-1 冲突 | **A 固定槽位 + 指针清单，自己写这套回滚机械** |
| R3-Q3 | 验收谁触发、怎么汇总 | A 单独一条验收命令 + 冻结汇总规则；B 发布后自动跑验收；C 只留逐题记录由人看 | A 堵住「同一份记录可判通过也可判失败」；B 不用记得手动跑；C 最灵活 | A 阈值与「对照未覆盖不计分」算法要当场写死；B 日常发布变慢、验收变附属品；C 不可机器重放，FR-K3-3 过不了 | **A 单独一条验收命令 + 冻结汇总规则** |
| R3-Q4 | 出题方式（争议项重裁，红队 F-1 / 蓝队 M3） | A 人出题（或模型起草+人逐题确认）后冻结；B 维持机器生成+人工名单确认；C 完全机器生成 | A 符合母任务与 ADR、验收站得住；B 省时间；C 最快 | A 需要用户投入时间；B 仍不能证明题目代表真实读者需求；C 出题与被验收内容同源，直接削弱 FR-K3-4 | **C 维持「完全从资料自动生成」**（用户维持原选择；与母任务 OPEN-002 / ADR-0014 的冲突**如实保留**，登记为 RISK-K3-2 与未决项，不在本阶段静默改写） |

**Round 3 最重要的结果是一次方向纠正**（用户逐字原话，不改写）：

> 「你有点搞错了，我只是让你把新知识落盘到一个指定文件夹，比如下载文件夹的"KD测试"文件夹，和gbrain完全无关，和1347个页面的原知识库完全无关！KnowledgeDigest和原来的知识库完全没关系，你说的发布、检索层、gbrain都是伪需求！KnowledgeDigest的功能就是把一些新文档基于某一个已存在的知识库或新知识库，直接消化合并！你的需求完全搞错了！」

**纠正后重述的任务现实**（覆盖本文件此前所有涉及 gbrain / 1347 页 / 检索层的表述）：

1. KnowledgeDigest 是**独立工具**：输入=新文档（本期=89 份 Confluence Markdown），输出=消化合并进**一个指定的知识库目录**（新知识库，或用户指定的某个知识库目录，例如 `~/Downloads/KD测试`）。
2. **不涉及** gbrain、检索层、索引配置；**不涉及**既有的 1347 页知识库（`~/Knowledge/CompanyBrain`）——它只在对照验收时作为**只读冻结快照**出现，不是发布目标。
3. 「安全地交出去」= 让指定的知识库目录**永远不处于半成品状态**：要么是完整的新版本，要么是完整的旧版本；失败要显式、可回滚、成本可查。
4. 「真的交出去」的观察对象 = **那个知识库目录本身**（读者用 Obsidian 打开它）；不需要任何外部索引才能看见。

**Round 3 关闭**：R3-Q2/Q3/Q4 取得用户真实答复；R3-Q1 因用户纠正前提而作废并重述。

### 第 4 轮 Talk（detail-advice findings，step 10 后）· 已收到用户真实答复

输入 = detail-advice 红队 N-1…N-4 与蓝队 DB1/DB2（均为「二选一」性质的硬冲突，不是补文案能解决）。

| 编号 | 决策轴 | 选项（大白话） | 后果 | 风险 | 用户选择 |
| --- | --- | --- | --- | --- | --- |
| D1 | 换版时读者看到什么（消除「第三种状态」矛盾） | A 固定入口 + 指针，读者永远能打开；B 接受短暂缺失并在验收里豁免与上界；C 软链接入口 | A 无缺失窗口、AC 口径自洽；B 实现最简单；C 看似等价 | A 多一层版本目录+指针结构；B 缺失既非旧版也非新版，与「不得第三种状态」冲突；C 工具链跟进性未验证 | **A 改成「固定入口 + 指针」，读者永远能打开** |
| D2 | 合并时库内原有内容怎么办 | A 保留原有内容、只新增/更新声明托管路径；B 整库只放本批；C 只新增不更新 | A 真正「消化合并」；B 规则最简单；C 最安全 | A 需定清允许改写白名单与碰撞规则；B 会删光用户原有页面；C 做不到「合并」 | **A 保留库里原有内容，只新增/更新声明托管路径** |
| D3 | LKG 与失败记录放哪 | A 知识库目录外部（同级隐藏目录），写进允许写清单；B 知识库目录内部（需排除规则） | A tree hash 稳定、读者看不到旧库；B 一切在一个目录内好找 | A 发布工具会写自己目录以外（同级）位置，需清单约束；B 污染 tree hash、Obsidian 里看到旧库 | **A 放在知识库目录外部（同级隐藏目录），写进允许写清单** |
| D4 | 失败成本覆盖哪一段 | A 承接编译侧三项 + 记发布段自己的；B 只管发布/回滚这一段；C 顺手把编译侧失败记账也修了 | A 能真实回答「从编译到发布总共花了多少」；B 职责最清；C 真正修掉老缺陷 | A 需读批次 `run-metrics.json` 并分开记账；B 母任务那个 300 次调用无账的缺陷等于没测到；C 动到 K1/K2 编译链路，需明确开口子 | **A 承接编译侧三项 + 记自己的** |

## 调研

### 取证一（step 4，子代理 S 执行，2026-09-15；R0 gap 来自需求框架骨架）

派发：1 个子代理（`f80db9b2`），只读取证，要求每条结论带 `文件:行号` 证据、无法确定写 unknown。耗时偏长，主会话在 3 分钟后发限时收口指令，子代理按当前证据返回。**未改仓库任何文件。**

| # | 结论（一句话） | 证据 | 置信度 |
| --- | --- | --- | --- |
| 1a | `full_release.atomic_release` = 任务级整包替换：锁=`kb_lock`；staging=`copytree` 到父目录 `.task3-release-<uuid>`；切换=`os.replace(formal→rollback)` 再 `os.replace(stage→formal)`；失败自动恢复旧版并写 `.task3-release-failure-*.json` | `src/knowledge_digest/full_release.py:1142-1281`；`lock.py:14-35` | high |
| 1b | `atomic_release` 前置：candidate 必须是目录/非 symlink/无特殊节点/树哈希匹配；formal 允许「不存在但父目录在」或「已存在且是完整包」；**支持保留旧版**（旧版只移入 rollback 不删） | `full_release.py:145-178, 1157-1183` | high |
| 1c | `publisher.commit` 前置相反：目标必须**不存在或为空目录**（`189-190`），**不支持保留旧版**；失败时 quarantine 到 `<name>.failure.<run>.<nonce>` 并写 failure.json | `src/knowledge_digest/publisher.py:33-256` | high |
| 2 | 生产路径调 `commit`（`compiler.py:1503/2233/7879/7922/8013`）；`atomic_release` **当前无生产调用**，仅测试调用；`writeback.py`/`page_layout.py` 属另一条已隔离的 legacy 路径 | `full_release.py`、`compiler.py`、`tests/acceptance/test_task3_quality_release.py:797-961`、`scripts/legacy_digest_reference.py:114` | high |
| 3a | 成本三项来源分散：`observed_calls` 来自 `run["provider_calls"]`（`compiler.py:2067-2071`）或 `model.calls/embedder.calls`（`task5_runtime.py:3003`）；耗时为 `semantic_compiler.py` 的 `elapsed_ms`；token 采集在 `semantic_compiler.py:178-190/805-815/957-999`，缺失时报 `provider_usage_unavailable` | 同上 | high |
| 3b | `observed_calls=null` 的确切位置：`publisher.py:113`，在 `quarantine()` 写 failure.json 时硬编码 null（同块 `provider_identity`/`audit_ref` 也为 null）；触发=`finalizer` 抛异常或 `final.state≠published` | `publisher.py:96-132, 193-233` | high |
| 3c | 母任务报告里「写 `status:"missing"` 的采集器」**不在本仓库**：`src` 内 grep 零命中，它是 WorkflowHub 侧的 `indexes/runtime-facts-v2.jsonl` | `B-architecture-audit.md:18/261-262`；本仓库 grep 零命中 | medium |
| 4 | 失败注入点齐全且已有先例：`kb_lock` 获取、`copytree`、拷贝后树哈希、两次 `os.replace`、status projection 校验；已有用例 `fail_second_replace`/`corrupt_staged_replace`/`busy_lock`/`fail_install_and_restore` 等 | `tests/acceptance/test_task3_quality_release.py:815-875`；`test_phase2_5_append_only_durability.py:283/374`；`test_task5_compiler_formal_tree.py:978` | medium-high |
| 5 | 测试隔离：无 `conftest.py`、无自定义 marker，惯例是 pytest 内建 `tmp_path` + `tests/fixtures/**`；可复用 `test_task3_quality_release.py`、`tests/fixtures/task8_nav`（`make_batch`）、`test_task7_e2e.py:185` | `pyproject.toml:17`；上述测试文件 | high |
| 6a | K1 批次形状：批次目录 `YYYY-MM-DD-N` 建在父目录下；`_audit/page-manifest.json` schema=`task7-page-manifest.v1`，含 `publish_status`（K1 **只允许** `not_released`，写 `released` 直接 ValueError）、`run_status∈{complete,blocked,interrupted}`、`blockers`、`pages`、`source_ledger`；K2 把 `navigation={navigation_status,success_pages,blocked_sources,blocked_reasons}` 写回同一 manifest，并把 `task8_navigation` 写入 `_audit/run-metrics.json` | `semantic_compiler.py:640-661, 45`；`semantic_audit.py:803-812, 836-840`；`semantic_navigation.py:126-146, 100-124` | high |
| 6b | **磁盘上没有真实 K1 批次**（`/Users/Hugh/Downloads/KD测试` 为空）；形状证据来自测试 fixture，真实产物未验证；K2 `navigation=generated_ok` 目前只能从 fixture 复现 | `ls /Users/Hugh/Downloads/KD测试` 空；`tests/fixtures/task8_nav/__init__.py`；`test_task8_entry_navigation.py:702` | high |

**未知与风险（如实保留）**：① `status:"missing"` 采集器不在本仓库，K3 若不补就要明确「不可得」口径；② `atomic_release` 无生产调用者，复用/接线属未决设计（= OPEN-K3-2）；③ 真实 K1 批次缺位，全链路验收需先真跑一次编译；④ `commit` 与 `atomic_release` 对「目标已存在」策略相反，复用前必须先定发布单元（Talk R1 Q1 已定为整库原子）；⑤ `atomic_release` 路径**无 fsync**，崩溃一致性未被现有测试覆盖。

### 调研结论对方向的影响

- Talk R1 Q1（整库原子）与 `atomic_release` 的**替换机械**天然吻合（整包替换 + 失败自动恢复 + 替换函数可注入），但与 `publisher.commit`（要求空目录、不保留旧版）**冲突**；→ 结论见 D-002/D-010：**只借鉴机械，不复用入口与完整包判据**（其判据含 K4 待删的自证产物，且要求 24h 内人工确认；成功路径不清理旧版、不建指针）。
- **主会话补证（2026-09-15，量小直读）**：`atomic_release` 判定「formal root 是否是可保护的完整包」时要求存在 `_FORMAL_ROOT_REQUIRED_PATHS` = `bundle/README.md`、`bundle/index.md`、`audit/source-manifest.json`、`reports/projection-report.json`、`reports/exit-manifest.json`（`full_release.py:37-43, 166-173`）。其中 `projection-report.json` 与 `exit-manifest.json` 正是母任务 K4 要删除的**旧自证机器**产物。→ **不能整段复用 `atomic_release` 的「完整包」判据**；K3 需要的是它的**原子换版与回滚机械**，配上 K1/K2 批次自己的校验口径。该取舍进 Talk Round 3。
- Talk R2 Q11（新建独立发布根目录）与 `atomic_release` 的 formal-root 前置（可不存在但父目录在）**兼容**。
- Talk R2 Q8（三项真实非 null）有落点：`observed_calls`/耗时/token 各有来源，缺的是**失败路径不再写 null** 与「真 0 带原因」的校验。
- 全链路对照验收必须先真跑一次 K1/K2 编译（真实批次目前不存在），这是步骤性成本，需在方案里写明。
- **主会话补证（2026-09-15，量小直读）**：
  - S2② 冻结物之一「改造前 release4 产物快照」**在磁盘上存在**：`/Users/Hugh/Downloads/KnowledgeDigest-task5-m402-20260908.release4`（14 MB）。
  - `observed_calls=null` 有**第一手实物证据**：`/Users/Hugh/Downloads/KnowledgeDigest-task5-m402-20260908.release2.failure.run-6e25dd21260b4e45.…/failure.json` 中 `"observed_calls":null` 且 `"provider_identity":null`、`"audit_ref":null`，`reason_code=QUALITY_FINALIZE_ValueError`、`state=failed`。同类失败目录还有 `release3.failure.*`。→ AC-K3-2 的「修复前基线」可直接引用该实物，不需要只靠母任务报告转述。

## grill

### grill-with-docs（step 8）· 交互式拷问，非审查；一次一批独立前沿问题

输入：`docs/adr/0013-write-into-existing-semantic-layer.md`、`docs/adr/0014-real-query-set-acceptance.md`、本文件术语与 OI 大纲、Talk R1–R3 已收敛答复、direction-advice findings。

| 编号 | 前沿问题 | 选项（大白话） | 后果 | 风险 | 用户选择 |
| --- | --- | --- | --- | --- | --- |
| G-1 | 换版那一瞬间，读者能不能接受「知识库目录短暂不存在」？ | A 能接受极短缺失但必须测出来且失败可回滚；B 必须始终可打开（固定入口+只换指针）；C 原地逐文件覆盖 | A 实现最简单可测；B 无缺失窗口；C 目录名从不消失 | A 正开着的 Obsidian/扫描脚本可能报一次找不到（红队 F-4 点名的窗口）；B 多一层指针与链接，且链接被 Obsidian 跟进性未验；C 中途失败即半新半旧，违反「不得半成品」 | **A 能接受极短缺失，但必须被测试覆盖、且失败可回滚** |
| G-2 | 「指定的知识库目录」怎么给？ | A 每次运行显式指定；B 写死默认目录；C 默认值+必须显式确认 | A 一个工具可管多个库、不会搞混；B 命令最短；C 最安全 | A 命令变长、敲错会建错地方（需「只写指定目录」硬检查兜底）；B 忘传参就会合错库；C 多一步确认，与全自动方向不一致 | **A 每次运行显式指定目标知识库目录** |
| G-3 | 现有「带日期的批次目录」与目标知识库目录什么关系？ | A 批次=中间产物，知识库目录=正式交付物；B 取消批次，编译完直接进库 | A 每步可单查可重跑、验收有对照物；B 目录更干净 | A 磁盘上会同时存在批次与知识库两份内容，必须写明谁是正式交付物；B 出问题时缺可单查的中间快照 | **A 保留批次作为中间产物；知识库目录才是正式交付物** |

**grill 收敛**：三项均为用户真实答复；据此新增/收口 OI-16（切换窗口）、OPEN-K3-3（目标目录由运行参数提供）、OI-17（批次与知识库的关系）。术语确认：本卡语境下「发布」= 把批次内容按既有目录/命名规范合并进**用户显式指定的知识库目录**，并整体原子换版；`README.md`/`Audit` 一类既有产物契约不因本卡改变。

## 决定条目 D*

### M-基线判断

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-001
label: 任务性质与交付面
statement: "本卡（K3）交付两样东西：① 一条把新文档消化结果安全合并进「用户显式指定的知识库目录」的原子换版通道（含一条命令回滚、LKG 固定槽位与指针）；② 一个可复跑的真实问题集判定器（冻结三份对照物 + 逐题四结果 + 可执行汇总）。KD 是独立工具，不接 gbrain、不做检索层、不写既有 1347 页知识库。"
rationale: "用户 R-027 纠正：发布/检索层/gbrain 是伪需求；KD 的功能是把新文档基于一个已存在的知识库或新知识库直接消化合并。"
alternatives_rejected: "把发布目标设成既有 CompanyBrain 整库（用户 R-027 明确无关）；把 gbrain 可检索做成验收步骤（同上）；只做发布通道不做判定器（母任务要求两样一起）。"
impact: [goal, scope]
evidence: "Talk R3 Q1 用户逐字原话；母任务 PRD K3 结果①②③"
```

### M-产物形态

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-002
label: 原子换版、稳定入口与回滚机械
statement: "以「用户显式指定的知识库目录」为一个整体做原子换版，并在库根提供一个**固定名字的当前版本入口（指针）**，读者随时打开都能读到完整版本（Talk R3 detail D1=A）。发布流程：① 在库级写锁内校验目标库状态与批次白名单；② 在暂存区构造新版本（= 库内原有内容 + 本批新增/更新，见 D-004）；③ 先把当前版本整份放入**库外同级隐藏目录**的 LKG 固定槽位并原子写指针清单（含 tree hash、版本 id、时间）；④ 用原子 rename 换版并更新入口指针；⑤ 读回校验。回滚命令只读指针、按 hash 校验后整包换回；保留最近 1 个可回滚版本，成功发布后轮换旧 LKG。LKG 槽位、指针清单、失败收据路径均写入「允许写位置清单」，且**不计入**被验收的当前版本 tree hash。"
rationale: "Talk R1 Q1（整库原子）、R1 Q3（保留 1 版）、R2 Q11、R3 Q2（固定槽位+指针）；detail-advice D1 用户裁决改「固定入口 + 指针」（消除目录缺失窗口与 AC 第三种状态的矛盾）；detail-advice D3 用户裁决 LKG 与失败记录放库外同级隐藏目录。现有 atomic_release 没有 LKG 指针、旧版不清理、且两次 replace 之间有缺失窗口，不能直接复用。"
alternatives_rejected: "按产品/按页面发布（会产出混合版本）；保留 2–3 版可连退（范围变大）；不留旧版靠重编译（回滚不确定）；原地逐文件覆盖（中途失败即半成品）；整段复用 atomic_release 现有入口与完整包判据（红队 F-3/蓝队 B2）；接受「目录短暂缺失」并在 AC 里豁免（detail-advice D1=B，用户改选 A）；LKG 放库内（污染 tree hash 且读者会看到旧库）。"
impact: [scope, acceptance]
evidence: "Talk R1 Q1/Q3、R2 Q11、R3 Q2；detail-advice D1/D3 用户裁决；调研取证一 #1a/#1b；红队 F-3/F-4/F-5、N-1/N-2/N-4；蓝队 B1/B2/DB5"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-003
label: 发布与回滚的操作形态
statement: "两条命令：发布一条、回滚一条，均不设人工确认闸门（继承母任务 T-010=B 与 RISK-005 已接受的风险）。"
rationale: "Talk R1 Q2 用户真实答复。"
alternatives_rejected: "发布前人工确认（推翻母任务已定方向）；单命令多动作（日常更易敲错）。"
impact: [scope, ordinary_detail]
evidence: "Talk R1 Q2"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-004
label: 合并规则（新版由什么组成）
statement: "新版 = **目标知识库的原有内容 + 本批新增/更新**。发布只允许写入「允许写位置清单」内的路径：KD 声明托管的页面路径（`products/**` 等）与库级结构页/索引页可新增或更新；**未声明托管的路径一律保留、不删除**；未声明路径与批次内容发生同路径碰撞时**硬失败**（不静默覆盖）。证据型文件（批次 `products/**` 页面与 `_audit/**`）在发布时**逐字节复制**，不重新渲染，以保证 K1 的 claim 锚点与行区间不漂移。"
rationale: "detail-advice D2 用户裁决：保留库里原有内容、只新增/更新声明托管路径；蓝队 DB1/DB7（未定义组成会导致整库替换删光用户页面，且证据页重渲染会让 AC-K3-3 的定位/出处判据漂移）；核心需求「基于已存在的知识库直接消化合并」。"
alternatives_rejected: "整库只放本批内容（会删掉用户原有页面）；只新增不更新（「消化合并」做不到）；允许静默覆盖未声明路径（会造成真实损失）。"
impact: [scope, acceptance]
evidence: "detail-advice D2 用户裁决；蓝队 DB1/DB7；红队 N-2"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-004b
label: 批次与知识库的关系
statement: "每次运行仍产生一个带日期的批次目录作为**中间产物**（可单查、可重跑、供验收对照）；正式交付物是用户显式指定的**知识库目录**，发布动作按 D-004 的合并规则把批次内容并入该库并整体原子换版。"
rationale: "grill G-3=A；Talk R2 Q11；现有批次命名 `YYYY-MM-DD-<n>`。"
alternatives_rejected: "取消批次目录、编译完直接进库（丢失可单查的中间快照与验收对照物）。"
impact: [scope]
evidence: "grill G-3；调研取证一 #6a"
```

### M-质量与验收

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-005
label: 失败显式化与成本度量
statement: "成功与失败运行共用一份 run 记录 schema，必含 耗时 / 调用数 / token 三项真实非 null；真实发生的 0 合法但必须附 reason（`cache_hit` / `no_provider_call_yet` / `provider_unavailable`）；无法归因的 0 或与 reason 矛盾的计数判失败；`publisher.py:113` 的硬编码 null 必须消除。**覆盖范围（detail-advice D4 用户裁决）**：发布命令必须**承接该批次编译侧 `_audit/run-metrics.json` 的三项消耗**（字段分别标明 `inherited_from_compile`），并另记发布段自身消耗；因此"编译已花调用后再失败"的运行会被真实计量，不得只报 0。词表复用 K1 已冻结的 reason 三值，不再新增第三套词表。若 `publisher.py:113` 的旧路径在本卡交付后仍不可达，则在 spec 明确登记其处置归属（随 K4 或本卡顺手修），不得留下"已修复"的空承诺。"
rationale: "Talk R2 Q8 用户选 A；detail-advice D4 用户裁决承接编译侧；母任务 OI-26/F-002；磁盘实物证据（release2/release3 failure.json 中 observed_calls=null）。红队 N-3/蓝队 DB2 指出：发布与验收不调 provider，若只记发布段则 AC-K3-2 会被 0+reason 真空满足，真实缺陷在编译链路。"
alternatives_rejected: "token 允许记「不可得」（与母任务硬约束冲突）；失败只留原因码（保留 F-002 缺陷）；只记发布/回滚段的 0 消耗（AC-K3-2 真空满足）。"
impact: [acceptance]
evidence: "Talk R2 Q8；detail-advice D4 用户裁决；`/Users/Hugh/Downloads/KnowledgeDigest-task5-m402-20260908.release2.failure.run-6e25dd21260b4e45.…/failure.json`；`src/knowledge_digest/publisher.py:113`；蓝队 M1/DB2；红队 F-7/N-3"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-006
label: 三份冻结物与齐备门
statement: "三份冻结物（89 份输入清单+逐文件 sha256、改造前产物快照、对照知识库快照）各做不可变内容快照 + 逐文件 sha256 清单，冻结 ID 由清单内容确定性推导，落在 `freeze/<frozen_id>/manifest.json`；齐备检查是验收命令的前置门：任一缺失或 hash 复算不一致 → blocked，不产出任何逐题结论。对照知识库（既有 1347 页库）只作只读冻结输入。**排除规则必须随清单登记**：跳过 `.` 开头的文件（如 `.DS_Store`）与对照库内 `_gbrain/` 生成镜像（509 文件，会被 sync 重写）；输入清单恰为 89 份 `.md`（不含 2 个 `.DS_Store`）。**判定器只允许读 `freeze/<frozen_id>/` 下的快照，禁止读活库路径**（preflight 断言）。"
rationale: "Talk R1 Q5=A；母任务 S2；蓝队 M4/m1/DB12；红队 F-6/N-9（无排除规则会让 frozen_id 不稳定）。"
alternatives_rejected: "git 提交/标签当冻结 ID（改变知识库维护方式、触及写权边界）；只记版本标识与统计数字（无法复现当时内容，对照结论无效）；对整树含生成镜像取 hash（frozen_id 不稳定）。"
impact: [acceptance, data_state]
evidence: "Talk R1 Q5；蓝队 M2/M4/DB12；红队 F-6/N-9；调研取证一 #m1"
```

**D-006 补充（同时冻结「被验收物」）**：判定记录必须绑定**被验收知识库目录的 tree hash（或逐文件 sha256 清单）+ 问题集文件 sha256 + 判定口径版本**；重放时先校验，不一致即明确报「被测对象已变，不可复跑」，不得静默给出新结论。

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-007
label: 逐题判定与汇总
statement: "验收是一条独立命令：读冻结问题集 + 三份冻结物 + 被验收树指纹，逐题给出四结果（答案命中 / 定位有效 / 出处正确 / 对照未覆盖），把记录落成机器可读文件；汇总规则在本阶段冻结为可执行形式，spec 必须补齐**「硬失败题」的可执行定义与通过阈值**，并明确「对照未覆盖」的计分处置（不计我方优势）。因此同一份逐题记录只能得出唯一结论。"
rationale: "Talk R2 Q10、Talk R3 Q3=A；母任务 S8/OI-25；蓝队 B3/DB3（只有必要条件时，20 题全落「对照未覆盖」也能判通过）。"
alternatives_rejected: "发布后自动跑验收（日常发布变慢、验收变附属品）；只留逐题记录由人看（不可机器重放，FR-K3-3 过不了）；把「对照未覆盖」计为我方成绩（母任务 S8 明确禁止）。"
impact: [acceptance]
evidence: "Talk R3 Q3；蓝队 B3；母任务 S8"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-008
label: 问题集来源与区分度
statement: "问题集由程序从冻结资料自动生成，生成规则与产物随冻结清单登记（用户 Talk R3 Q4 维持的选择）；有效性用双向验证证明：在固定的「已知坏产物」样本上必须能查出坏产物，同时对正确结果不误判。**坏样本必须与题目绑定**：每类缺陷（缺表格的页 / 错出处链接的页 / 孤儿页）绑定 ≥2 道「必须判失败」的题 + 期望失败原因，样本与绑定关系随冻结物入库并登记 sha256；未完成绑定时 AC-K3-4 不得声明可执行。**「答案命中」的可执行定义**（红队 N-6）：以冻结输入的行区间 + 内容指纹为 oracle，命中=能回溯到具体行，而不是词面重合或 token 重合。"
rationale: "Talk R2 Q9=A、Talk R3 Q4=C 用户真实答复；蓝队 DB9；红队 N-6（无 LLM 判定时「答案命中」会退化为词面匹配，等于在测有没有抄到原文）。"
alternatives_rejected: "只验证能区分坏产物（无法证明不冤枉正确结果）；靠人工评审对照快照（不可机器重放）；用词面重合当「答案命中」（AC-K3-4 不可执行）；人出题（用户明确不选）。"
impact: [acceptance]
evidence: "Talk R2 Q9、Talk R3 Q4；蓝队 M3；红队 F-1（冲突如实保留，见 RISK-K3-2）"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-009
label: 负例注入与观察口径
statement: "四类负例（写入中断 / 取消 / 校验失败 / 越界写入）逐一注入并机器验证；观察对象 = 读者可见的**当前版本整根等价**：负例后要么等同旧版 tree hash、要么等同新版 tree hash，不存在第三种状态。**「取消」定义为进程内协作式取消**（在固定检查点触发并返回非零码、完成恢复），不按 SIGINT/SIGKILL 的崩溃级处理；该覆盖范围须在 AC 措辞里写明，不得含混。**「越界写入」的注入载体**：fixture 批次内放置一条落在「允许写位置清单」之外的页面路径，断言发布被 blocked 且目标库零字节变化。**no-op 发布**（内容与现状完全相同）：spec 须明确允许或拒绝（建议允许并标 `no_op=true`、不轮换 LKG）。"
rationale: "Talk R2 Q9、Talk R3 Q1 纠正；红队 F-4/N-1/N-10；蓝队 M5/m3/DB10/DB11；detail-advice D1 用户改为「固定入口+指针」后，第三种状态在读者侧不再存在。"
alternatives_rejected: "以 gbrain/检索层为观察对象（用户 R-027 判为伪需求）；接受目录缺失并在 AC 里豁免（detail-advice D1=B，用户改选 A）；把「取消」当 SIGINT 处理却不补 fsync（声明的覆盖范围与实现不符）；越界负例只靠代码级注入（语义与可复算性差）。"
impact: [acceptance]
evidence: "Talk R3 Q1 纠正、grill G-1；红队 F-4；蓝队 M5；调研取证一 #4"
```

### M-存量与边界

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-010
label: 与既有发布机械的关系
statement: "不复用 `full_release.atomic_release` 的入口与「完整包」判据（其 `_FORMAL_ROOT_REQUIRED_PATHS` 含待删自证产物 `reports/projection-report.json`、`reports/exit-manifest.json`，且要求 24h 内的人工 SummaryConfirmation）；不复用 `publisher.commit`（要求目标不存在或为空、不保留旧版）。只借鉴前者的「库级写锁 + 锁内两次整包替换 + 读回校验 + 失败自动恢复」机械，另建 LKG 槽位与指针清单。"
rationale: "Talk R3 Q2；调研取证一 #1a–#1c/#2；红队 F-3；蓝队 B2。"
alternatives_rejected: "整段复用 atomic_release（复活 ADR-0013 已废除的 bundle 形态并带回人工闸门）；复用 publisher.commit（与整库换版和保留旧版冲突）。"
impact: [scope, acceptance]
evidence: "调研取证一 #1a–#1c/#2；红队 F-3；蓝队 B2；`full_release.py:37-43, 145-178, 268-312`；`publisher.py:33-56, 189-190`"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-011
label: 发布输入的前置白名单
statement: "发布侧只接受字段级白名单齐备的批次：`run_status == complete`、`publish_status == not_released`、`navigation.navigation_status == generated_ok`（必须显式等于，不得写成「不等于 blocked 就放行」）、`blockers` 为空数组；缺任一即 blocked 并写明 reason。`publish_status=released` 由 K3 自己的发布记录承载（引用批次 manifest 的 attempt_id + hash），不改写 K1 manifest 的既有语义。"
rationale: "调研取证一 #6a；蓝队 M6（`semantic_cli` 只判 `!= blocked` 会漏；`semantic_audit.py:836-838` 明确禁止写 released）。"
alternatives_rejected: "照抄 `!= blocked` 的放行写法（缺字段或异常批次会混过去）；由 K3 回写 K1 manifest 的 `publish_status`（违反 K1 既有语义）。"
impact: [scope, acceptance]
evidence: "调研取证一 #6a；蓝队 M6；`semantic_audit.py:836-838`；`semantic_cli.py:183-184`"
```

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-012
label: 与 K1/K2 的边界
statement: "以 K3 为主；允许修发布/验收链路暴露的 K1/K2 缺陷，但必须先记录再修，且不重做 K1/K2 的核心能力（编译语义、导航生成）。**台账与额度（红队 N-8）**：所有 K1/K2 缺陷先登记到本任务缺陷台账（编号 / 等级 / 证据 / 是否本卡修 / 重冻后批次 hash），只允许修「使批次无法发布或验收不成立」的阻塞级；任何 K1/K2 修复都必须产出新批次并全量重跑，旧判定记录作废；该次整跑 89 份的 provider 成本计入 AC-K3-2 的成本账。"
rationale: "Talk R1 Q0 + Talk R2 Q7 用户真实答复；红队 N-8（磁盘无真实 K1 批次，本卡第一件事是整跑一次 89 份编译，无额度会重做 K1）。"
alternatives_rejected: "大范围连 K1/K2 能力一起改（验收归因困难、与分卡约定冲突）；一律只记录不修（小缺陷可能卡住全链路验收）；不设台账与停止规则地「顺手修」（范围失控且被验收物被静默改动）。"
impact: [scope]
evidence: "Talk R1 Q0、Talk R2 Q7"
```

### M-外部复用

```yaml
task_id: task9-release-safety-query-acceptance
outline_version: v1.0
decision_id: D-013
label: 知识库目录的结构声明与只写边界
statement: "目标知识库目录由运行参数显式提供（grill G-2=A）；该库自带结构声明与「只写这些路径」列表，发布侧只写声明路径与其子目录。**「允许写位置清单」必须显式包含**：目标库内声明的托管页面路径与结构页/索引页、库外同级隐藏目录（LKG 槽位、指针清单、失败收据）、以及库级**写锁文件（放目标库父目录，不放被换版的根内，避免随换版被搬走）**。清单以外的写入是硬失败（四类负例之一）。首次发布到一个空目录时按现有 `default_publication_structure()` 建默认骨架并登记其 sha256；「允许新建」的判定写成显式规则（不存在 或 存在且为空 ⇒ 建骨架；存在且非空且无结构声明 ⇒ 拒绝）。"
rationale: "Talk R1 Q6、Talk R2 Q11、grill G-2；detail-advice D3 用户裁决（LKG 与失败记录放库外同级隐藏目录）；蓝队 DB5/DB8；母任务 S7；现有 `paths.py` 已有 `kb.structure.md` + `managed_by: KnowledgeDigest` 的既成约定。"
alternatives_rejected: "写死默认目录（忘传参会合错库）；默认值+必须人工确认（多一步、与全自动方向不一致）；把 LKG 或失败收据放库内（污染 tree hash 且读者会看到旧库）；锁文件放被换版的根内（会被随版本搬走）。"
impact: [scope, ordinary_detail]
evidence: "Talk R1 Q6、Talk R2 Q11、grill G-2；`src/knowledge_digest/kb_structure.py`、`paths.py`"
```

## 审查处置

### direction-advice（step 6）· 真实执行，结果 = `available-with-failures`（不是 pass）

- **执行方式**：红/蓝两路独立子代理（红队 `312cc8f4`、蓝队 `a4ac49aa`），只读取证、不改仓库、不调 provider；耗时偏长，主会话发限时收口指令后各按现有证据产出。红队 18 条 finding（含 5 条 counterexample）、蓝队 15 条 finding。
- **证据落盘**（主会话只保留结构化摘要，全文不进上下文）：
  - `specs/task9-release-safety-query-acceptance/review/task9-direction-red.md`（sha256 `22a218af7e80…`）
  - `specs/task9-release-safety-query-acceptance/review/task9-direction-blue.md`（sha256 `3e7f355bf142…`）
  - `specs/task9-release-safety-query-acceptance/review/task9-direction-packet.md`（输入包，sha256 `a0d9fcf9a90d…`）
- **provider 事实**：本轮审查经宿主子代理执行，未走 `wh-review` provider；`wh-review doctor` 在本机返回 `status:ok`（配置 `/Users/hugh/.config/3rd-review/config.json`，覆盖五个阶段），但本轮未发起 provider 请求。因此本阶段审查事实记为 `available-with-failures`（有真实 finding、有真实执行），**不是** provider pass。

| finding | 来源 | 等级 | 处置 | 去向 |
| --- | --- | --- | --- | --- |
| F-1 出题方式自动生成与 ADR-0014/OPEN-002 冲突 | 红队 | blocking | **用户 Talk R3 Q4 维持 C（机器生成）**；冲突如实保留，登记 RISK-K3-2 与未决项，不在本阶段静默改写 | `## 风险`、`## 未决项` |
| F-2 「真的交出去」落空 / 观察对象未定义 | 红队 | blocking | **fixed（用户纠正）**：用户 R-027 明确本卡不接 gbrain、不做检索层、观察对象=指定知识库目录本身；新增 OI-15/OI-16 承载 | OI-15, OI-16；NG-009 |
| M5 负例「只见完整版本」真空满足 | 蓝队 | major | **fixed（同上）**：观察口径写死为整根断言（等于旧 tree hash 或等于新 tree hash） | OI-15 |
| F-3 / B2 `atomic_release` 入口与完整包判据接不上（含待删自证产物、人工确认） | 红队/蓝队 | blocking | **fixed（方向）**：不复用其入口与完整包判据；只借鉴「锁内整包替换 + 失败自动恢复」机械 | OPEN-K3-2；`## 已选方向` |
| F-5 / B1 「保留 1 个可回滚版本 + 一条命令回滚」在代码里不存在（无 LKG 指针、旧版不清理） | 红队/蓝队 | blocking | **fixed（用户 Talk R3 Q2 选 A）**：固定槽位 + 指针清单，自写回滚机械 | OI-03 |
| F-4 两次 `os.replace` 之间存在目录缺失窗口 | 红队 | blocking | **登记为待写死项**：切换窗口内读者可见性口径进 OI-16，决策草稿必须给出可机读判据 | OI-16 |
| F-6 / M2 三份冻结物不含被验收批次/发布树指纹 → 重放不可复现 | 红队/蓝队 | blocking/major | **fixed（方向）**：判定记录必须绑定被验收树指纹与问题集 sha256；不一致即报「被测对象已变，不可复跑」 | OI-05, OI-06 |
| F-7 / M1 失败三项成本在那条链路上没有容器 | 红队/蓝队 | major | **fixed（用户 Talk R2 Q8 选 A）**：成功/失败共用同一 schema，复用 K1 的 reason 词表 | OI-04 |
| B3 验收触发点与汇总阈值缺失 | 蓝队 | blocking | **fixed（用户 Talk R3 Q3 选 A）**：单独一条验收命令 + 冻结汇总规则 | OI-08 |
| M3 自动出题削弱区分度 | 蓝队 | major | 与 F-1 同处置（用户维持），保留为风险 | RISK-K3-2 |
| M4 CompanyBrain 冻结缺 snapshot ID 载体 | 蓝队 | major | **fixed（方向）**：`freeze/<frozen_id>/manifest.json` + 齐备门；按 R-027 该快照仅作对照只读输入 | OI-05 |
| M6 交接取值未冻结（`navigation_status` 必须显式 `generated_ok`；`publish_status=released` 写入方未定） | 蓝队 | major | **登记为待写死项**：发布前置写成字段级白名单；`released` 由 K3 自己的发布记录承载，不回写 K1 manifest 语义 | OI-12 |
| F-17 gbrain slug 覆盖风险 | 红队 | major | **closed（按 R-027 作废）**：本卡不接 gbrain | NG-009 |
| m1 齐备检查无 preflight、tree hash 重复全量计算 | 蓝队 | minor | 登记：齐备检查做成验收命令 preflight，并在同一次运行内复用 hash 结果 | OI-05 |
| m2 「已知坏产物」fixture 未定义 | 蓝队 | minor | 登记：决策草稿给出三类可复算坏样本（缺表格 / 错出处 / 孤儿页） | OI-09 |
| m3 `atomic_release` 路径无 fsync | 蓝队/红队 | minor | 登记：决策草稿须写明「写入中断」是否含崩溃级；若不含则 AC 措辞不得含混 | OI-07 |

**审查结论的净效果**：方向主干（整库原子、锁内切换、失败自动恢复、失败成本真实、三份冻结物带 sha256、独立目录落盘）保留；三处被审查挑出的致命缺口已由用户裁决或用户纠正解决；其余登记为必须写死的可机读判据。

### detail-advice（step 10）· 真实执行，结果 = `available-with-failures`（不是 pass）

- **执行方式**：复用同一对红/蓝独立子代理，输入=当前决策草稿（只读），要求核验上一轮 finding 是否真被处置并找出新漏洞。红队 13 条 finding（blocking N-1…N-4）、蓝队 12 条 finding（blocking DB1/DB2）。
- **证据落盘**：`review/task9-detail-red.md`（sha256 `691346a8461d…`）、`review/task9-detail-blue.md`（sha256 `487932e22f79…`）。

| finding | 来源 | 等级 | 处置 | 去向 |
| --- | --- | --- | --- | --- |
| N-1 自相矛盾：G-1=A 允许目录缺失 vs AC-K3-1「不存在第三种状态」vs OI-16 反例 | 红队 | blocking | **fixed（用户 detail-advice D1 改选 A）**：改为「固定入口 + 指针」，读者永远能打开；AC-K3-1、OI-15、OI-16、D-002、D-009 全部改写一致 | D-002, D-009, AC-K3-1, OI-15/16 |
| N-2 / DB5 LKG 槽位放哪（库内污染 tree hash / 库外越界）；锁目录未定 | 红队/蓝队 | blocking | **fixed（用户 detail-advice D3 选 A）**：LKG 槽位、指针、失败收据放库外同级隐藏目录并写入允许写清单；锁文件放父目录；LKG 不计入被验收 tree hash | D-002, D-013 |
| N-4 发布失败记录落盘位置未定（三选一各撞一条决策） | 红队 | blocking | **fixed（同上）**：失败收据随 LKG 槽位落库外同级隐藏目录，并被「允许写位置清单」覆盖 | D-002, D-013 |
| DB1 新版内容组成未定义（会删光既有页面） | 蓝队 | blocking | **fixed（用户 detail-advice D2 选 A）**：新版=原有内容+本批新增/更新；未声明路径保留；碰撞硬失败；证据页逐字节复制 | D-004 |
| N-3 / DB2 AC-K3-2 可被 0+reason 真空满足；`publisher.py:113` 修复不可达 | 红队/蓝队 | blocking | **fixed（用户 detail-advice D4 选 A）**：发布承接编译侧三项消耗并另记发布段；`publisher.py:113` 归属须在 spec 写明，不留空承诺 | D-005, AC-K3-2 |
| DB3 汇总缺「硬失败题」定义与阈值 | 蓝队 | major | **登记为 spec 必须冻结** | D-007, OPEN-K3-4 |
| N-6 无 LLM 时「答案命中」退化为词面匹配；坏样本未与题目绑定 | 红队 | major | **fixed（方向）**：命中定义改为可回溯到冻结行区间+指纹；坏样本每类绑定 ≥2 道必须判失败的题 + 期望原因 | D-008, AC-K3-4, OPEN-K3-5 |
| N-8 「先记录再修」无台账/额度/停止规则，且本卡需先整跑一次 89 份编译 | 红队 | major | **fixed（方向）**：缺陷台账 + 只修阻塞级 + 任何 K1/K2 修复须新批次全量重跑 + 该次 provider 成本计入成本账 | D-012, RISK-K3-4 |
| N-7 ADR-0013 仍 accepted、母任务 PRD 未修订，与「不接 gbrain」冲突 | 红队 | major | **登记为交接事实**：本卡在验收标准内显式登记对母任务 AC-K3-1 措辞的偏离（依据 R-027/NG-009）；ADR-0013 的 supersede 属用户/母任务层，本阶段不擅自改写 ADR | `## 验收标准` 偏离声明；`## 未决项` |
| N-9 冻结物无排除规则（`_gbrain/` 509 镜像 + `.DS_Store`） | 红队 | major | **fixed（方向）**：排除规则随清单登记；输入恰 89 份 `.md`；判定器只读冻结快照 | D-006 |
| N-10 「取消」注入与 RISK-K3-6 声明范围冲突 | 红队 | major | **fixed（方向）**：定义为进程内协作式取消；AC 写明不承诺崩溃级 | D-009, AC-K3-1 |
| N-11 OI-03/OI-04 仍写已被 D-002/D-010 否决的落点 | 红队 | major | **fixed**：OI-03/OI-04/OI-15/OI-16 已按 D-002/D-005/D-009/D-013 回填并删除旧表述 | OI-03/04/15/16 |
| DB8 发布记录落点 / 新库骨架 / 「不允许新建」判定 | 蓝队 | minor | **fixed（方向）**：落点=库外同级隐藏目录；骨架用 `default_publication_structure()` 并登记 sha256；「允许新建」判定写成显式规则 | D-013 |
| DB9 坏样本与题目绑定 | 蓝队 | minor | 已并入 N-6 处置 | D-008 |
| DB10 崩溃级口径未写进验收标准 | 蓝队/红队 | minor | **fixed**：AC-K3-1 正文已写明覆盖范围；RISK-K3-6 保留 | AC-K3-1, RISK-K3-6 |
| DB11 越界负例载体、0 题/重复 id、no-op 发布三态 | 蓝队 | minor | **fixed（方向）**：越界用 fixture 批次含未声明路径注入；问题集 preflight 校验题数与 id 唯一；no-op 发布须在 spec 明确（建议允许并标 `no_op=true`、不轮换 LKG） | D-009 |
| DB12 89 份清单排除规则、只读快照约束、对母任务 AC 的偏离声明 | 蓝队 | minor | **fixed**：D-006 与验收标准已写入 | D-006, `## 验收标准` |

**detail-advice 净效果**：上一轮 4 条真实收敛（F-2/F-3/F-5/F-6）保持；被点名为「记了账没解决」的 4 条（N-1/N-2/N-3/N-4）经用户二选一裁决后全部落地；7 条 major/minor 转为 spec 必须冻结的明确条目。

## 风险与延期交接

> 本节含三项内容：风险（RISK-K3-*）、未决项（OPEN-K3-*）、延期交接（DEF-K3-*，明细见 `## 延期与开放项`）。

| 编号 | 风险 | 影响 | 缓解 / 处置 | 来源 |
| --- | --- | --- | --- | --- |
| RISK-K3-1 | 全自动发布无人工闸门（母任务 RISK-005，用户已接受）：错误内容会直接进库 | 高 | 用 AC-K3-1（四类负例 + 整根断言）与 AC-K3-2（失败成本真实）压制；回滚一条命令可用 | 母任务 RISK-005；Talk R1 Q2 |
| RISK-K3-2 | **问题集由程序自动生成，与母任务 OPEN-002「用户参与出题」及 ADR-0014「human-authored question set」冲突**；出题与被验收内容同源，可能削弱可区分度、偏向「照原文能答」的题 | 中高 | 用户已在 Talk R3 Q4 明确维持机器生成；本阶段不静默改写冲突，登记在此并把「区分度用基线缺陷样本双向验证」（D-008）作为唯一有效证据；build-spec 必须保留该冲突声明 | Talk R2 Q10、Talk R3 Q4；红队 F-1；蓝队 M3；ADR-0014 |
| RISK-K3-3 | 切换窗口内目标知识库目录会极短缺失（`os.replace` 两次调用之间） | 中 | grill G-1=A 用户接受；必须被测试覆盖、且失败可回滚；若 build 阶段发现 Obsidian/扫描脚本实际报错，回到 grill 复核 | grill G-1；红队 F-4 |
| RISK-K3-4 | 真实 K1 批次目前不存在（`~/Downloads/KD测试` 为空），全链路对照验收必须先真跑一次 K1/K2 编译，成本约一次 provider 运行量级 | 中 | 机制可先用 fixture 跑通；全链路验收时点见 DEF-K3-3 | 调研取证一 #6b；母任务 OI-02 |
| RISK-K3-5 | 「保留 1 个可回滚版本」占额外磁盘（整库一份副本）；知识库变大后复制/切换变慢 | 低中 | 用户已选 A；成功发布后轮换旧 LKG；若库增长到影响日常使用，回到 Talk 复核版本数与发布单元 | Talk R1 Q3、R3 Q2 |
| RISK-K3-6 | 「写入中断」若按进程内异常注入验证，不覆盖掉电/进程被杀的崩溃级一致性（现有机械无 fsync） | 中 | 决策草稿要求写明覆盖范围；若后续要崩溃级保证，另立变更 | 蓝队 m3 |
| RISK-K3-7 | 用户 R-027 同时推翻了母任务 PRD S1/T-002=A（「可替代 CompanyBrain 查产品知识」及格线）与已 accepted 的 ADR-0013（写进既有语义层）；母任务 PRD 与 ADR 尚未修订 | 中高 | 本卡在验收标准内显式登记偏离声明（依据 R-027/NG-009）；ADR 的 supersede 归用户/母任务层，本阶段不擅自改写；交接给 build-spec/母任务时必读 | 红队 N-7 |
| RISK-K3-8 | 目标知识库若存量很大，整库复制 + 逐文件 sha256 的成本会随时间上升 | 低中 | 发布与验收共用一次 tree hash 计算（缓存复用）；知识库规模增长后回到 Talk 复核发布单元 | 蓝队 m1；RISK-K3-5 |

### 未决项与延期交接

**未决项（OPEN-K3-*）**

| 编号 | 未决项 | 当前处置 | 去向 |
| --- | --- | --- | --- |
| OPEN-K3-3 | 「指定的知识库目录」默认值 vs 运行参数的最终形态（已定向为运行参数，具体参数名归 build-plan） | 定向：grill G-2=A 运行参数显式指定；参数形态不在本阶段 | build-plan |
| OPEN-K3-4 | 汇总通过条件的具体阈值形式（例：硬失败题判据 + 命中率的表达方式） | 本阶段冻结「可执行形式」与「对照未覆盖不计分」「任一硬失败即整体失败」两条原则；具体数值表达归 build-spec | build-spec |
| OPEN-K3-5 | 「已知坏产物」样本的具体三类是否足够 | 登记三类候选（缺表格 / 错出处 / 孤儿页），build-spec 冻结为可复算 fixture | build-spec |
| OPEN-K3-6 | 问题集题目本身（母任务 OPEN-002） | 出题方式已裁决（机器生成）；题目在 build-spec 冻结并登记 hash | build-spec |
| OPEN-K3-7 | 母任务 PRD（S1/T-002=A）与 ADR-0013 尚未按 R-027 修订 | **登记为交接事实**，不在本阶段改写母任务材料或 ADR；本卡验收标准内已写偏离声明 | 用户 / 母任务层 |

## 最终确认

**用户真实确认（step 11，2026-09-15）**：用户在最终决策卡上选择「确认，这个方向就定了」。

- 用户逐字回复：`确认，这个方向就定了`
- 确认事实：`quality/confirmations/f99974ae000046cbaddbfe382d7f909367bea2a6a538236e2e8310fc7347e5cd.json`（hash 同名）
- material_revision：`revision-17d40a935c7530ca0c65b73058099f9c70fee2dd56b7e9dcd939e992e339e9b0`
- snapshot_tree：`56be502391f4f1e866c85bb2d35b91371e7d5887`
- step_slug：`approve-decision`；decision：`accepted`

**决策卡（呈用户时的大白话内容，摘要）**：一句话方向、七条怎么做、范围、非目标、成功标准、主要风险、审查事实、未决项；详见本文件 `## 已选方向` / `## 验收标准` / `## 风险与延期交接` / `## 审查处置`。

**阶段末六项大白话总结（交下游 build-spec）**：

1. **本阶段做了什么**：读母任务 K3 卡与 K1/K2 接口事实；四轮 Talk（R1 7 问、R2 5 问、R3 3 问+1 次方向纠正、detail 轮 4 问）与一轮 grill（3 问）共 22 项用户真实答复；一次只读取证（12 条带证据结论）；两轮红/蓝独立审查（direction 与 detail，均 `available-with-failures`）；产出 D-001…D-013、AC-K3-1…5、风险 8 项、未决 7 项、拒绝方案 15 项。
2. **需求覆盖**：母任务 R-008…R-025 与用户 R-001…R-028 全部有处置；16 个 OI 全部 confirmed；五维收敛表（目标/范围/方案/验收）四行齐备。
3. **上游对齐**：与 K1 的交接接口（`task7-page-manifest.v1`、`publish_status`、`navigation`）已冻结为字段级白名单；与 K2 的 `navigation_status=generated_ok` 显式取值已冻结；与母任务 S2/S5/S8 逐条对应。
4. **本阶段修复**：用户方向纠正（R-027）后改写 8 处决策与验收；detail-advice 指出的 4 处自相矛盾与文字处置全部落地（固定入口+指针、保留库内内容、LKG 放库外、承接编译侧成本）。
5. **剩余风险**：RISK-K3-2（问题集机器生成与母任务 OPEN-002/ADR-0014 冲突，用户维持）、RISK-K3-3（切换窗口）、RISK-K3-4（需先真跑一次 89 份编译）、RISK-K3-6（不承诺崩溃级）、RISK-K3-7（母任务 PRD 与 ADR-0013 尚未按 R-027 修订）。
6. **下一阶段边界**：build-spec 只做规格细化，不得重开产品方向、不得重跑 Talk/Grill；必须冻结的抓手项见 `## 风险与延期交接` 的 OPEN-K3-4/5/6 与 DEF-K3-3；不得依赖下游补需求。

## 阶段末自检与事实状态（step 12/13/14）

**stage-end-spec-analyze（step 12）**：本会话无外部 Stage Agent bridge，官方 outcome 记为 `unavailable`（`reason_code=executor_absent`，见 `quality/evidence/stage-reflection-availability/b78a18941809024fbf892c19d083aeaa8f94a59f9afedff0401fe794d5c1c976.json`）。主会话按 `spec-analyze` 的语义覆盖口径做结构自检：对话式收敛与语义证据齐备（无 gap 需在本阶段修复）；机器可读判据由 `run --action=execute` 逐项复算：

| 完成判据 | 状态 | 说明 |
| --- | --- | --- |
| scope | satisfied | 范围节存在且非空 |
| non_goals | satisfied | 非目标 NG-001…NG-011 |
| risks | satisfied | 风险与延期交接节存在 |
| ui_applicability | satisfied | `non_ui` 一项 fenced JSON fact |
| requirement_coverage | satisfied | 原始需求 28 行全部 `covered` + 五维收敛表 |
| goal_achievement | satisfied | 五维收敛表 goal 行 |
| acceptance_clarity | satisfied | 验收标准含场景/数据来源/通过/失败 |
| solution_convergence | satisfied | 五维收敛表 solution 行含取舍/被拒方案/未决项 |
| plain_language_card | satisfied | 核心需求+核心目标+已选方向 |
| outline_closed | missing | 16 个 OI 的结构/终态/方向快照/无 open 项四项均 passed；**interaction proof 因 aggregate 未发布为 `talk_clarify` 质量事实而 missing**（该发布路径只由宿主 bridge 提供） |
| human_confirmation | missing | 确认事实 `f99974ae…` 真实存在且为 `accepted`；因无 canonical stage outcome 承载，运行时未把它计入完成判据 |

**publish-decision（step 13）**：材料已发布（本文件为 make-decision 唯一权威材料）；官方 outcome `unavailable` 如实记录，**不伪装成完成**。

**stage-reflection（step 14）**：judgment JSON 已按 v2 schema 产出（六区块 + 身份 + 状态矩阵 + 来源完整性 + 介入归因，`status=degraded`），但公共入口 `run --action=reflect` 要求 executor source/attempt/timing/output hash，本会话无 bridge，故复盘同样记为 `unavailable`；judgment 内容作为会话事实保留在本次执行记录中。

## 拒绝方案

| 被拒方案 | 拒绝理由 | 来源 |
| --- | --- | --- |
| 只做 K3 一张卡、不修任何 K1/K2 缺陷 | 用户选「顺手补」但要求先记录后修；一律不修会让小缺陷卡住全链路验收 | Talk R1 Q0 |
| K3 + 大范围连 K1/K2 能力一起改 | 验收归因困难、与母任务分卡约定冲突 | Talk R1 Q0、R2 Q7 |
| 按产品原子 / 按页面替换发布 | 跨产品导航会混合、中途失败即半成品 | Talk R1 Q1 |
| 发布前设人工确认闸门 | 推翻母任务 T-010=B 与用户已接受的风险 | Talk R1 Q2 |
| 不保留旧版、靠重编译回滚 | 重跑不保证同结果，回滚不确定 | Talk R1 Q3 |
| 用 git 提交/标签当冻结 ID | 把知识库变成 git 仓库，触及写权边界 | Talk R1 Q5 |
| 只记版本标识与统计数字作为冻结 | 无法复现当时内容，对照验收结论无效 | Talk R1 Q5 |
| **直接把发布目标设为既有 1347 页知识库 / 把 gbrain 可检索做成验收步骤 / 引入检索层** | **用户 R-027 明确判为伪需求：KD 与既有知识库、gbrain 完全无关，发布只是把新知识落盘到指定文件夹** | Talk R3 Q1 用户纠正 |
| token 允许记「不可得」 | 与母任务「失败运行三项不得为 null」冲突 | Talk R1 Q4 → R2 Q8 覆盖 |
| 保留 2–3 版可连退 | 磁盘成倍、需额外清理规则、范围变大 | Talk R1 Q3 |
| 整段复用 `atomic_release` 入口与完整包判据 | 会复活 ADR-0013 已废除的 bundle 形态（含待删自证产物）并带回人工确认闸门 | 红队 F-3、蓝队 B2、Talk R3 Q2 |
| 复用 `publisher.commit` 作为发布通道 | 要求目标不存在或为空、不保留旧版，与整库换版冲突 | 调研取证一 #1c |
| 发布后自动跑验收 / 只留逐题记录由人看 | 前者让验收变附属品，后者不可机器重放 | Talk R3 Q3 |
| 原地逐文件覆盖换版 | 中途失败即半新半旧，违反「不得半成品」 | grill G-1 |
| 写死默认知识库目录 | 忘传参会把内容合进错误的库 | grill G-2 |
| 取消批次目录、编译完直接进库 | 丢失可单查的中间快照与验收对照物 | grill G-3 |

## 阶段执行记录

- step 1 load-context（S）：读母任务 PRD K3 卡与共享定义 S2/S3/S5/S7/S8；读母任务决策记录 OI-25/OI-26 与 F-002；
  读 K1 spec 的 K3 交接接口（SCN-013、FR-AUD-004/005、FR-PUB-002）与 K2 spec 的 K3 交接接口（SCN-K2-008）；
  读 ADR-0013/0014；核对当前代码发布事实（`publisher.py` 的 `commit`/失败收据、`full_release.py` 的 `atomic_release`、
  `writeback.py`）；核对 CompanyBrain 现状（1347 个 md、`Products/<Product>/...`）与冻结语料现状（89 份 md、顶层 1 个目录）。
  主会话只读接口与关键函数，不整卷吞入（R-005/R-026）。
- step 2 triage-scope（M+S）：任务身份落盘（本项目第 9 个任务、worktree 已由官方 bootstrap 建立）；OI 框架 v1.0 建立；
  范围初步定为 K3 一张卡，待 Talk R1 确认。
- step 3 Talk Round 1：Q0–Q6 七问用户真实答复（范围 / 发布单元 / 发布与回滚流程 / last-known-good 与回滚边界 /
  失败与成本口径 / 三份冻结物 / 写权映射），见 `## Talk`。
- step 4 调研取证：派 1 个子代理（`f80db9b2`）只读取证，覆盖发布机械、调用入口、成本计数来源、失败注入点、
  测试隔离、K1 批次形状；限时收口后返回 12 条带证据结论 + 5 项未知与风险。主会话另做两处小体量补证
  （`_FORMAL_ROOT_REQUIRED_PATHS` 含待删自证产物；release4 快照与失败运行实物证据）。见 `## 调研`。
- step 5 Talk Round 2：Q7–Q11 五问用户真实答复（修复边界 / token 口径 / 区分度 / 出题方式 / 发布目录形态），见 `## Talk`。
- step 6 direction-advice：**真实执行，`available-with-failures`（不是 provider pass）**；红队 18 条 finding（6 blocking）、
  蓝队 15 条 finding（3 blocking）。全文落盘 `review/task9-direction-red.md`、`review/task9-direction-blue.md`；
  逐条处置见 `## 审查处置`。
- step 7 Talk Round 3：R3-Q2/Q3/Q4 用户真实答复；**R3-Q1 因用户方向纠正而作废并重述任务现实（R-027/R-028）**，见 `## Talk`。
- step 8 grill-with-docs：G-1/G-2/G-3 三问用户真实答复（切换窗口 / 目标目录怎么给 / 批次与新库关系），见 `## grill`。
- step 9 决策草稿：D-001…D-013、AC 骨架、风险 6 项、未决 4 项、拒绝方案 15 项，见本文件各固定小节。
- step 10 detail-advice：**真实执行，`available-with-failures`**；复用同一对红/蓝子代理，红队 13 条（blocking N-1…N-4）、
  蓝队 12 条（blocking DB1/DB2）。逐条处置见 `## 审查处置`；据此新增第 4 轮 Talk（D1–D4 用户真实答复）。
- 第 4 轮 Talk（detail findings）：D1 固定入口 + 指针；D2 保留库内原有内容只新增/更新声明托管路径；
  D3 LKG 与失败记录放库外同级隐藏目录并写入允许写清单；D4 发布承接编译侧三项消耗。据此改写 D-002/D-004/D-005/D-009/D-013、
  AC-K3-1/2/4/5、OI-03/OI-04/OI-15/OI-16，消除文件内自相矛盾。
