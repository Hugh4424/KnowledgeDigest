# KnowledgeDigest 效果差距与架构重置 · 规划 PRD

| 项 | 值 |
| --- | --- |
| 母任务 | KnowledgeDigest / task6-effect-gap-and-architecture-reset |
| 母决策 | `specs/task6-effect-gap-and-architecture-reset/decision-log.md` |
| decision_revision | `revision-19e398fccb83acbc61269f0321aedaf0e575edadf1dc1d8f653da9e2e669e619` |
| source_revision（源树快照） | `61ebd768b3d846d5ee255e4e724f49eccadd8bbf` |
| map_revision | `5bf0d07e010b20bb18ac7d37ae47945325b53a96a6e063abc65b486a25c5c6a5`（任务图草稿 v1，用户已确认） |
| prd_revision | 本文档字节 sha256（定稿确认时绑定） |
| UI applicability | **non_ui**（决策记录已冻结；本工作流无 UI 对象，按契约记录事实并跳过设计确认链） |
| 状态 | **final**（步骤 5 用户已确认定稿：human_approved=true，display_before_reply=true；确认时展示稿 hash `bf6c97c0809d…`） |

本 PRD 是规划交接物，供后续 4 个子任务开工读取；它不是第五份当前材料，不改写母任务四材料。每个子任务只消费自己的最小读取集；母任务与兄弟任务材料对其只读。

---

## 1. 共享定义（各卡引用，此处一次）

- **S1 语义层契约**：产物页与既有 CompanyBrain 同构——同一套 frontmatter（`title/type/page_model/scope/product/section/tier/trust/source_status/quality_status/generated_by/tags`）、同一套目录与命名、`[[wikilink]]` 双链；硬断言 `page_model=derived` 且带 `generated_by`（满足 `apply_formal_knowledge_metadata.py` 推导规则）。KD 溯源字段字面名由 K1 的 build-spec 阶段冻结，登记进 `CONTEXT.md` 与既有元数据脚本（OPEN-008）。
- **S2 冻结三样**（对照验收前提）：① 89 份 Confluence Markdown 输入清单 + 每份 sha256；② 改造前 release4 产物快照；③ CompanyBrain 冻结快照（记录其 ID）。缺一，对照验收结论无效。
- **S3 数据状态词表**：`ready / known_empty / duplicate_alias / audit_only / 资料未明确`；「资料未明确」不得写成结论、不得进入事实分母。
- **S4 证据零容忍**：每条 claim 必须带 `source_uri`、内容指纹、行定位；回不到原文的只进 `unknown` 并显式标注「原文未明确」，unknown 本身带检索证据；多 claim 句子逐条映射。
- **S5 发布安全**：staging 校验 → 原子切换 → last-known-good；负例（写入中断/取消/校验失败/越界写入）下读者与 gbrain 只见完整的新版本或完整的旧版本；失败运行的耗时/调用数/token 必须真实非 null。
- **S6 保留不变量**（瘦身时不得破坏）：300 行分页（`page_layout.py`）、分批与恢复（`batch_run.py`）、来源去重（`ingest/identity`）、失败不伪装成功、claim 级溯源。
- **S7 写权边界**：KD 本期只写自己声明的路径；不修改既有 CompanyBrain 正式页；不修改停摆的自动化流水线；接管旧 `synthesize_*` 主题与自动化规则登记移交「流水线修复任务」（owner=用户）。
- **S8 对照判定规则**：同一组问题逐题判定四结果（答案命中/定位有效/出处正确/对照未覆盖）；「对照未覆盖」不计我方优势；每题判定与汇总通过条件在 K1/K3 的 build-spec 冻结为可执行规则。

## 2. 需求覆盖与非目标

R-001→K1/K3；R-002→母任务已完成（F-001/F-004）；R-003→K3；R-004→K4/K3；R-005→**明确排除**（F-003 覆盖 41 候选无一占据产品位，仅留 3 个参考做法 D-009）；R-006→K1–K4；R-007/R-008/R-010/R-011→流程约束不立卡；R-009→K1（数据状态）/K2（页面范围）/K3（成功失败边界）。

非目标（NG-001…NG-010）：不做问答/RAG、不做前端、不引入向量库/图数据库/服务化、不做多格式输入、不修停摆流水线、不保留自证质量机器、不改既有 CB 正式页、不整体引入外部项目。

## 3. 任务卡

### K1 把知识做对（参考保真 + 语义层页面编译）

- **结果**：89 份 Confluence Markdown → 与 CompanyBrain 同构的知识页；参考型内容（表格/参数/枚举/字段字典/URL/报错文案）零丢失且逐块可回原文区间；叙述内容逐条带出处；`page_model=derived` 断言成立。
- **consumer**：读者（Obsidian 查产品知识）；下游技能/Agent/应用（gbrain 检索）。**owner**：子任务 K1。
- **scope**：只做 Confluence Markdown（89 份冻结语料）；输出为语义层页面 + 参考块清单；不做入口导航（K2）、不做发布通道（K3）、不删代码（K4）。
- **用户流程与状态转换**：投料（冻结语料入staging）→ 解析拆块（参考型/叙述型）→ 编译成页（带溯源）→ 结构校验 → 待发布（not_released）→ 交 K3 发布。

| FR | AC（含失败判据） | oracle |
| --- | --- | --- |
| FR-K1-1 参考块清单 | AC-K1-1 对 89 份输入生成参考块清单，每块带来源文件、行区间、内容 sha256；与冻结分层全量清单 100% 一致。**失败**：任一块缺失/错位/指纹不一致。 | 机器全量比对 + 人工抽 20 块复核 |
| FR-K1-2 参考内容保真 | AC-K1-2 产物中参考型内容与原文逐字一致、结构保留，不经模型改写。**失败**：任一处语义改写或字段丢失。 | 机器逐块 diff |
| FR-K1-3 同构页面编译 | AC-K1-3 产物页通过 10 页结构/元数据校验（frontmatter 12 字段、双链、命名）；`page_model=derived`+`generated_by` 断言成立；gbrain 按 slug 可检索。**失败**：任一字段不符/断言失败/检索不到。 | 校验脚本 + gbrain 检索 |
| FR-K1-4 claim 级溯源 | AC-K1-4 机械检查零「无出处结论」：每 claim 有 source_uri+指纹+行定位，或显式「原文未明确」（unknown 带检索证据）；多 claim 句子逐条映射。**失败**：无定位肯定句/错定位/未逐条映射。 | 解析器扫描零违规 |
| FR-K1-5 数据状态处置 | AC-K1-5 五类状态（ready/known_empty/duplicate_alias/audit_only/资料未明确）fixture 逐类核对：状态与正文一致；重复来源单页化；「资料未明确」不进分母。**失败**：重复来源发两页/未明确写成结论/进分母。 | 五类 fixture 逐类核对 |

- **依赖**：准备依赖=冻结语料清单+hash（S2①）、语义层契约读取（S1）；实现依赖=无（起点）；验收依赖=冻结参考块全量清单；合并依赖=经 K3 staging 发布通道上库（接口由 K3 提供，K1 只产出 staging 产物）。
- **来源与设计引用**：决策记录（revision-19e398）、F-001/F-004（效果与保真基线）、F-003 的 LangExtract 参考项（D-009）、E 报告契约事实；local risk：LLM 改写诱惑→用 AC-K1-2 逐字保真压制；deferred：溯源字段字面名（OPEN-008）。
- **最小读取集**：required=本卡 + S1–S4/S6 + 冻结语料；conditional=S2②③（对照口径参考）、F-003；normally-unused=母任务审查记录、兄弟卡 workspace。
- **五阶段开工说明**：以本 PRD 当前 revision + 母决策为输入，走 build-spec（冻结 FR/AC 细节与溯源字段名）→ build-plan → build-code → verify-code；本卡子任务自建四材料，母任务材料只读。

### K2 入口与导航

- **结果**：入口页 + 分类入口把每个已发布页接进入口；从入口可达每一页且入口描述对页面有区分度（对照基线：87/99 无入口、95/99 同质）。
- **consumer**：读者；下游（按入口浏览/检索）。**owner**：子任务 K2。
- **scope**：页面类型映射、入口/分类生成、孤儿页与同质入口判失败；不改编译（K1）、不改发布（K3）。
- **用户流程与状态转换**：接收 K1 页面清单 → 生成入口/分类 → 入口图自检（孤儿/同质）→ 修循环 → 达标待发布。

| FR | AC（含失败判据） | oracle |
| --- | --- | --- |
| FR-K2-1 入口可达性 | AC-K2-1 全量入口图检查：每个已发布页至少被一个入口/分类页链接可达。**失败**：任一孤儿页。 | 入口图遍历脚本零孤儿 |
| FR-K2-2 入口区分度 | AC-K2-2 入口描述两两不重复且非模板化问句；模板重复率低于 build-spec 冻结阈值（对照基线 95/99 同质）。**失败**：同质描述超阈值。 | 描述唯一性检查 |
| FR-K2-3 读者路径 | AC-K2-3 抽查 build-spec 冻结的 N 条真实查询路径 ≤3 跳。**失败**：任一路径超 3 跳。 | 路径测量 |

- **依赖**：实现依赖=K1 页面清单；验收依赖=K1 页面清单 + 入口图检查器；准备依赖=无；合并依赖=随 K3 发布（导航页同批原子切换）。
- **来源与设计引用**：决策记录、F-001 导航实测（87/99、95/99）；local risk：入口描述交由模型生成导致同质→AC-K2-2 阈值压制；deferred：无。
- **最小读取集**：required=本卡 + S1/S8 + K1 页面清单；conditional=K3 发布接口约定；normally-unused=母任务审查记录。
- **五阶段开工说明**：同 K1，输入为本卡 + K1 产物清单。

### K3 安全地交出去（发布安全 + 真实查询集验收）

- **结果**：① 发布具备 staging+原子切换+last-known-good+回滚，负例下只呈现完整版本，失败运行成本计数真实非 null；② 冻结快照+问题集+逐题判定记录可复跑，能给出通过与失败；③ 问题集在冻结 CB 快照上具备可区分度。
- **consumer**：读者与下游（稳定可查）；用户（验收结论）。**owner**：子任务 K3。
- **scope**：发布通道、失败显式化与成本度量、查询集/判定记录器、冻结快照管理；不改编译（K1）、不改导航（K2）、不删代码（K4）。
- **用户流程与状态转换**：staging 校验 → 原子切换 → （失败时）回滚 last-known-good；验收：出题 → 冻结 → 逐题判定 → 汇总通过与失败。

| FR | AC（含失败判据） | oracle |
| --- | --- | --- |
| FR-K3-1 原子发布与回滚 | AC-K3-1 负例注入（写入中断/取消/校验失败/越界写入）后，读者与 gbrain 只见完整新版本或完整旧版本；一条命令回滚且可查性不中断。**失败**：见半成品/混合版本/回滚失败。 | 四类负例机器验证 |
| FR-K3-2 失败显式化与成本度量 | AC-K3-2 失败运行的耗时/调用数/token 真实记录非 null（修复 `observed_calls=null` 缺陷）。**失败**：任一 null 或虚报。 | 注入失败运行读三项计数 |
| FR-K3-3 判定记录可复跑 | AC-K3-3 同一问题集+三份冻结物下逐题给出四结果判定，汇总通过条件可执行；机器重放逐题一致。**失败**：不可复跑/逐题缺失/汇总条件缺失。 | 判定记录机器重放 |
| FR-K3-4 问题集有效性 | AC-K3-4 问题集在冻结 CB 快照上具备可区分度（能区分好/坏产物，不惩罚正确结果）。**失败**：全过或全不过。 | 有效性检查脚本 |
| FR-K3-5 冻结物齐备 | AC-K3-5 三份冻结物存在且 hash 登记。**失败**：任一缺失。 | 齐备检查 |

- **依赖**：准备依赖=fixture 语料 + 冻结基线脚本；实现依赖=无（fixture 先行）；验收依赖=K1/K2 产物（全链路对照）、用户参与出题（OPEN-002）；合并依赖=作为 K1/K2/K4 合并后的全链路门禁。
- **来源与设计引用**：决策记录、F-002 的 `observed_calls=null` 缺陷与删除清单、S5/S8；local risk：全自动发布无人工闸门（RISK-005，用户已接受）→用 AC-K3-1/AC-K3-2 压制；deferred：停摆流水线接管登记（S7）。
- **最小读取集**：required=本卡 + S2/S5/S8 + fixture；conditional=K1/K2 产物（全链路验收时）；normally-unused=母任务审查记录。
- **五阶段开工说明**：同 K1；本卡可最先开工（fixture 不依赖 K1）。

### K4 瘦身且不丢能力

- **结果**：整体源码行数净下降 + 不可达模块数归零 + 零引用配置量下降；S6 保留能力回归全绿；旧自证质量路径（投影/五维比较/证书/verifier）删除或不可达。
- **consumer**：维护者；下游（不再被死代码与旧口径误导）。**owner**：子任务 K4。
- **scope**：历史分支/死代码删除、保留能力迁移、零引用配置清理、旧自证机器移除；不改编译语义（与 K1 协调）、不动发布通道（K3）。
- **用户流程与状态转换**：冻结基线与复算脚本 → 效果/能力回归（通过才允许删除）→ 分批删除 → 复算核对 → 合并主干（K3 门禁）。

| FR | AC（含失败判据） | oracle |
| --- | --- | --- |
| FR-K4-1 代码量净下降 | AC-K4-1 整体源码行数净下降 + 不可达模块数归零 + 零引用配置量下降；基线冻结、复算脚本可复算。**失败**：任一指标上升或基线不可复算。 | 复算脚本三项净下降 |
| FR-K4-2 保留能力回归 | AC-K4-2 S6 五项（300 行分页/分批恢复/去重/失败语义/溯源）回归测试全绿。**失败**：任一红。 | 回归测试套件 |
| FR-K4-3 旧自证路径移除 | AC-K4-3 投影/五维比较/证书/verifier 删除或不可达且断言不可达。**失败**：仍可执行。 | 不可达断言 |
| FR-K4-4 删除顺序门禁 | AC-K4-4 删除动作只在效果与核心能力回归通过后执行。**失败**：先删后验。 | 流水线顺序检查 |

- **依赖**：准备依赖=冻结基线快照+复算脚本；实现依赖=无（独立，与 K1–K3 并行）；验收依赖=保留能力回归；合并依赖=合并主干时以 K3 查询集验收为门禁。
- **来源与设计引用**：决策记录、F-002 删除清单与最小实现清单；local risk：误删真能力→AC-K4-2/AC-K4-4 门禁；deferred：无。
- **最小读取集**：required=本卡 + S6/S7 + 基线快照；conditional=K1 编译器接口（能力迁移时）；normally-unused=母任务审查记录。
- **五阶段开工说明**：同 K1；删除类任务先补回归测试再动手。

## 4. 延期与开放项（交接事实）

- OPEN-001 页面清单（K1/K2 的 build-spec 内冻结）；OPEN-002 查询集题目（K3，需用户参与）；OPEN-008 溯源字段字面名（K1 的 build-spec 冻结）。
- 停摆流水线修复：接管登记 owner=用户，触发=流水线恢复时（S7）。
- 结构性遗留：成本基线不可得（K3 的 AC-K3-2 补齐）；CompanyBrain 评测集仅 6 题且过松（K3 重建）。


## 6. 必要附件与版本（planning close 声明）

- **必要附件与版本**: [{"path":"docs/adr/0013-write-into-existing-semantic-layer.md","sha256":"b1cc2668a83c6e8382d9db197ffcceedfaea504a7a81e3083a96be67ce84d497"},{"path":"docs/adr/0014-real-query-set-acceptance.md","sha256":"a232c865178d67c6e5a993461dbd6ef00d0ef1c9e29bf97b23657bd4a0d68665"}]

## 5. 变更说明

- v1（草稿）：首次成稿，绑定 map_revision `5bf0d07e`；等待步骤 5 最终确认。
- v3（planning close 小修）：按 task-close planning 模式要求补「必要附件与版本」声明（2 个 ADR 附件及其 sha256）；不改变方向/权限/范围/验收，属管理性小修；本文档字节 hash 随之变化，以 close 计划绑定的当前字节为准。
- v2（final 标）：步骤 5 用户确认后按 spec-prd 契约标 final；确认绑定 decision_revision `revision-19e398fccb83`、source_revision `61ebd768b3d8`、map_revision `5bf0d07e`、prd_revision（确认时展示稿）`bf6c97c0809d`、displayed_draft_hash `bf6c97c0809d`。本文档字节 hash 标 final 后见 portable-workflow outcome 的 material_refs；确认稿与 final 标的差异仅限本状态行与变更说明。
