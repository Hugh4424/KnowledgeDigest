# Task 3 Decision Log — 全量导航、发布和对比验收

状态：`confirmed`。Talk Round 1–3、调研输入、Grill、方向审查和细节审查已完成；细节发现已逐条处置，用户已最终确认当前决策。

## 原始需求

| source_id | 原始需求/约束 | 来源 | 当前处理 |
| --- | --- | --- | --- |
| R-001 | 查看 `docs/plans/knowledge-digest-knowledge-publication-prd.md`；Task 2-C 已完成，判断是否进入 Task 3。 | 用户原话 | 以 PRD 和 Task 2-C 真实交接事实核对；不把用户判断直接当作 release 通过。 |
| R-002 | 按标准 WorkflowHub 从 `make-decision` 开始，不跳阶段，不依赖 `build-spec` 补产品需求。 | 用户原话 | 已先完成 `make-decision`；`spec.md`、`plan.md`、`tasks.md` 只承载已确认决策和 PRD，不补产品取舍。 |
| R-003 | Talk 用大白话说明选项、后果和风险；`decision-log.md` 记录原始需求、关键事实、选择、理由和延期交接。 | 用户原话 | 已完成 Talk；本日志保留原始回答、关键事实、选择、理由、风险和延期交接。 |
| R-004 | 先梳理完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。 | 用户原话 | 已在本日志和 `spec.md` 固化完整流程、页面范围、状态、边界、非目标和延期项。 |
| R-005 | Task 3 做全量导航、发布和对比验收，不重新承担主题探索或正文设计。 | PRD §7 Task 3 | 已由 Talk 收敛为：机器/自动评审完成质量验收，人工只确认一页汇总；不新增主题探索或正文设计。 |

## 关键事实

- PRD v1.7 的路线是 `Task 2-C → Task 3 → Task 3-Closeout`；Task 3 依赖 Task 0、Task 1、Task 2-A、Task 2-B、Task 2-C 全部通过（PRD §7，Task 3）。
- Task 2-C 只能形成小语料质量证据，交付级仍是 `not_released`；Task 3 才判断全量 `released`。Task 2-C 的题集、Concept Contract v1、信号、评分表、provider/config、预算和门槛只能复用，不能在 Task 3 临时改门。
- Task 3 的全量对象是 89 篇输入对应的 OKF-compatible Reader Bundle 与 Audit/Archive Package，不等于必须生成 89 个 Reader 页面。旧 `Reader Package` 只表示历史布局。
- 当前页级状态只有 `published`/`degraded`；交付级状态只有 `released`/`not_released`。`machine_pass`、`agent_assisted`、`human_reviewed` 分开记录。
- `--no-llm + Jaccard` 只能作为离线基线；不能冒充 semantic Reader Bundle 或 `released`。
- 当前业务仓 `main` 工作树干净；本任务使用独立 CandidateWorkspace，不直接改 `main`。
- Task 2-C 归档交接显示全量 89 篇、完整 17+3 题集、Task 3 发布和是否继承 Agent-only 评审主体均是 Task 3 的交接/决策范围；本轮必须重新确认，不能从旧记录静默继承。

## 用户流程

1. 冻结 89 篇输入 manifest、TopicIndex/ProductGazetteer、Concept Contract v1、三类模板、provider/model/config、参数、预算和当前 commit。
2. 从同一 TopicIndex 和 audit records 生成 canonical `index.md`、产品索引、模块索引、主题页导航；`Home.md` 只做兼容入口，不维护第二套事实。
3. 执行全量编译；成功页面进入 Reader，失败、冲突、无归属或缺证据内容进入 Audit/Archive 的 degraded 记录。
4. 生成有结构依据的双向 Related links；没有关系就省略。
5. 生成 Task2 旧结果、CompanyBrain 和新结果的固定对比报告，分开说明保存完整性、机器质量、读者可读性、信任/新鲜度、失败、耗时、成本和局限。
6. 自动流程用冻结的 17 个正向问题和 3 个负向问题做全量读者验收，记录入口、首次命中页、答案、边界/版本、来源链、实际评审主体和失败原因；用户不逐题打开页面、不检查来源链，只看最后一页汇总。
7. 按 TopicIndex 的 `old_path_mapping` 生成旧路径 alias 或 deprecated 映射。
8. 失败或中断只重放未完成的 affected source/topic；保留成功批次、旧 formal 和审计现场。
9. Task 3 结束后把最终结果、风险和延期项交给 Task 3-Closeout；Closeout 只做文档同步、清理、归档和恢复演练。

## 页面范围

### Reader Bundle

- `README.md`、兼容 `Home.md`、唯一 canonical 根 `index.md`；
- 产品索引、模块索引、正式主题/concept 页面；
- `references/` 来源入口和 `log.md`；
- 只有允许进入正式导航的页面，不放 `_digest`、`_archive`、provider 日志或审计现场。

### Audit/Archive Package

- 89 条输入的 manifest、snapshot、audit ledger；
- Claim/Evidence、原文、失败/冲突/降级原因、旧页面和运行报告；
- 可回放的 provider/model/config/模板/词典/commit hash 与质量证据。

## 数据状态

- 页级：`published` 表示通过页级机器门，可进入候选 Reader；`degraded` 表示失败、冲突、无归属、缺必需证据或质量门失败，不进入正式导航。
- 交付级：`released` 只表示机器硬门、自动读者题集、交付门和汇总确认全部通过；任何硬门未通过、结果不可判定或缺少汇总确认都是 `not_released`，不得覆盖上一次已 released 的包。
- 证据身份：`machine_pass`、`agent_assisted`、`human_reviewed` 独立记录；Agent 结果不能冒充人工验收。
- 生命周期：`status=deprecated` 保留旧路径但默认隐藏；stale 只提示复核，不自动删除、降级或改变 release 判定。
- 旧路径：必须指向新 canonical 页面，或明确标为 deprecated/alias 并写原因。

## 范围

当前范围包括 89 条全量 Reader Bundle、Audit/Archive Package、canonical 导航、Related links、固定对比报告、旧路径映射、失败重放、自动机器硬门、完整 17+3 读者题集和一页汇总确认。页面细目见“页面范围”，流程细目见“用户流程”。

## 成功边界

Task 3 只有同时满足以下条件，才可把整包标为 `released`；其中机器、自动读者和交付边界沿用 PRD，新增的人工动作只有一页汇总确认：

- 机器硬门、自动读者门、交付门和汇总确认全部通过；
- 17 个正向问题首次命中至少 15 个，3 个负向问题误命中为 0；
- 标题脱离路径可理解率至少 90%，产品/模块归属准确率至少 90%，评分人、规则、样本量和 seed 可追溯；
- 页面正文最多 120 行，整页最多 300 行；无空分类、泛占位、hash 主路径、断链和空壳入口；
- 89 条来源都能在 manifest、snapshot、audit ledger 定位；失败来源与无关已发布页隔离；
- 旧 formal path 全部能解析到 canonical 页面，或有真实 alias/deprecated 映射；
- 对比报告同时覆盖保存完整性、机器质量、正文/导航可读性、信任/新鲜度、失败、性能、成本和局限。

## 失败边界

- 任一质量门、读者门、交付门失败：整包保持 `not_released`，旧 released 包不被覆盖。
- provider 失败、截断 JSON、fallback、超预算、重复失败、来源冲突、无归属、缺必需证据或降级页进入 Audit/Archive，不进正式 Reader 导航。
- 只完成离线基线、写入成功、页数/Claim 数增加或测试绿色，均不能声称知识发布成功。
- 失败重放只处理未完成 affected source/topic；不能删除成功批次、旧 formal 或失败证据。
- 任何改变主题身份、页面类型、Concept Contract、题集或质量门的要求，停止当前实现并回到 owning decision/PRD scope revision；不能在 `build-spec` 偷补。

## 非目标

- 不新增页面类型，不重新定义 TopicIndex/主题身份，不调整 Task 2-C 已冻结质量门。
- 不把页数、Claim 数、速度、provider 成功或写回成功当作读者质量。
- 不维护第二套 Home/导航/来源事实，不把 89 篇输入机械变成 89 个页面。
- 不删除或静默覆盖失败证据、旧 formal、来源历史或 Audit/Archive。
- 不引入数据库、图数据库、向量数据库、CAS、调度器、后台守护、永久人工队列或 AgentMemory 正式接入。
- 不在 Task 3-Closeout 重新定义业务范围；Closeout 只做文档、清理、归档和恢复演练。

## 延期交接

| deferred_id | 内容 | 交接阶段 | 完成条件 |
| --- | --- | --- | --- |
| DEFER-001 | 根 `AGENTS.md`、`CONTEXT.md`、`README.md`、`docs/plans/README.md` 同步 | Task 3-Closeout | 文档与最终代码、命令、状态、目录一致 |
| DEFER-002 | 仓库 inventory、引用扫描、归档、清理和恢复演练 | Task 3-Closeout | 有分类、hash、旧路径映射和可恢复证据；不确定项保留 |
| DEFER-003 | Task 3 自动读者题集由自动评审执行，人工不做正文验收 | 已解决于本轮 make-decision | 保留 `agent_only`/自动评审事实；人工只做汇总确认，不写 `human_reviewed` |
| DEFER-004 | provider/model/config、完整题集评分表、归属抽样规则、对比字段的最终技术选择 | 本轮 Talk 后的 downstream materials | 只展开已确认方向；不由 build-spec 补产品取舍 |
| DEFER-005 | 全量真实运行、全量读者评分、正式 `released` 或诚实 `not_released` | Task 3 build-code/verify-code | 真实运行、失败证据、读者评分和交付门齐全 |

## 风险与延期交接

主要风险是自动读者验收可能漏掉细微阅读问题，且已知普通警告可以随 `released` 保留。控制方式是固定题集、机器硬门、完整来源审计、未知结果阻断和旧正式包保护。真实 89 条编译、完整 17+3 运行、汇总字段落点及最终文档同步按上表交给 Task 3 build-code、verify-code 和 Task 3-Closeout；下游不得借延期项改变已确认的发布含义。

## Talk

### Round 1：全量读者门的评审主体

初始范围已由 PRD 和 Task 2-C 交接事实回答；当前仍有一个会改变 Task 3 方向的高影响问题：全量 17+3 读者门由谁实际执行。

当前队列：1 个会改变方向的问题。回答后重新排序；不把旧 Task 2-C 的 Agent-only 记录当作本轮答案。

## 调研重点

待 Round 1 真实回答后判断是否需要外部调研。若 provider、题集格式或外部 OKF 消费者的真实接口会改变方向，再做定向核实；否则记录跳过理由。研究结果不能代替用户选择。

## Grill

已在 Talk Round 3 后执行。四项退出检查、CONTEXT/ADR 处置和冲突处理见后文“Grill：核实结果与处置”；早期“尚未执行”文字已被该记录取代。

## 独立审查与处置

方向审查和第一轮细节审查均已执行；真实传输、结果和逐条处置见后文对应章节。早期“尚未执行”文字已被后文记录取代；不把审查结果写成阶段通过。

## 当前确认

历史记录：本节写于最终确认之前，已被文末“最终确认”取代。当前决定已确认，`make-decision` 已正式完成。

## Talk Round 1：真实回复与重新排序

用户真实回复：`C，但是我不想逐题检查页面和来源链，希望人工验收更简单一些`。

该回复确认两点：保留 Agent 预审；保留独立人工参与。该回复没有接受“人工逐题检查页面和来源链”这一原始 C 方案，因此人工门的最小职责仍是方向性未决项，不能代用户补成“已确认”。

当前仍有 1 个会改变方向的问题：人工是否对完整 17+3 题逐题做简化的读者体验判断，还是只抽查/只看汇总。来源链、命令、版本和 Claim 保真可以继续由机器门与 Agent 证据负责；这项职责分工须由用户明确选择。

## Talk Round 1：方向变更

用户最新回复：`C`。

本轮语境中的 `C`：删除整包 `released/not_released` 状态与交付门禁，而不是改名或只隐藏给读者。

关键事实：`not_released` 不是本轮临时创造的概念；它已写入 PRD、项目上下文、源码和验收测试。它表达的是“输出包已生成，但没有通过全部正式质量门，因此不能替换上一份正式包”，与单页 `published/degraded` 状态不是一回事。

该选择会改变 Task 3 的产品合同：成功/失败边界、旧正式包保护、Reader/Audit/Archive 分层、Task 3 的 released 条件、失败重放和现有测试都需要重新定义。它是方向变更，尚未作为最终决策确认，也不能由 build-spec 补齐。

当前仍有 1 个会改变方向的问题：删除整包状态/门禁后，未完成或失败的输出如何处理。需要在“保留旧正式包保护但不暴露整包状态”和“写入即视为正式发布”之间明确选择；两者的失败风险和范围影响不同。

## Talk Round 1：撤回误解后的方向变更

用户最新回复：`撤回 released/not_released 的删除决定吧，你没说明白导致我搞混了。`

处置：撤回上一节“删除整包 `released/not_released` 状态与交付门禁”的方向选择。该选择不作为 Task 3 的当前决策，也不触发 PRD、源码、测试或交付合同修改。

原因：上一轮没有先用大白话区分“WorkflowHub 任务状态”“单个知识页状态”和“整套生成结果的交付状态”，导致用户无法在充分理解后作出有效选择。原有 `released/not_released` 合同暂时保持不变；后续如果仍需调整，必须先重新解释对象、影响和风险，再单独取得明确选择。

当前 Talk 方向：回到原始 Task 3 合同，继续只讨论人工读者验收如何简化；不把简化人工验收误解为删除整包交付状态，也不要求用户逐题检查来源链。

## Talk Round 2：简化人工读者验收

用户最新回复：`好的，继续吧，但是我不希望必须由人工仔细验收知识结果才能released，这太麻烦了，需要简化流程`。

本轮确认：保留 `released/not_released` 作为整套结果的交付状态；用户反对把“人工逐页、逐题、逐来源链仔细检查”设为 `released` 的必需条件。来源链、Claim、结构、完整性和失败隔离继续由机器门负责；人工读者门需要重新确定最小职责。

当前唯一开放决策轴：人工读者验收的最低强度。候选方向是“取消人工读者门、由机器和 Agent 自动完成”“人工只看汇总，不逐页检查”或“人工做极小的读者冒烟抽查”；不得在 build-spec 阶段替用户选择。

## Talk Round 2：真实回复与选择

用户真实回复：`B`。

选择：人工只看自动检查的一页结果汇总，不打开知识页、不逐题检查、不检查来源链。完整固定读者题集由自动流程执行；来源、Claim、结构、完整性、失败隔离和读者题集的通过/失败由机器或自动评审记录。

`released` 的含义随本选择明确为：机器门通过、自动读者题集通过、汇总没有阻断失败，并由人工确认“这次自动检查确实完成且结果可接受”。它不再暗示人工读过正文，也不能把这种确认写成 `human_reviewed` 内容核验。

主要收益：发布流程不再要求人工逐页验收，人工只需看一页汇总。主要风险：自动评审可能漏掉人工更容易发现的表达问题；固定题集、机器保真门、失败隔离和汇总中的阻断项仍作为防线。

## 调研输入

本轮不需要外部调研。当前取舍只涉及本项目已经冻结的发布合同、Task 2-C 交接事实和人工操作负担；没有外部消费者接口或实时 provider 事实会改变这个方向。外部调研跳过理由已记录，不把跳过当作通过。

## 方向建议

建议采纳 B 作为 Task 3 的方向：保留交付级 `released/not_released`，把人工职责从“验证知识内容”收窄为“确认自动验收汇总”。后续细节必须明确汇总中的阻断条件、人工确认记录和自动评审的可信边界；不能在 build-spec 偷补。

当前进入 Talk Round 3 的唯一问题：如果汇总里有非阻断警告，人工确认时是否仍允许 `released`。这决定失败边界，不涉及页面或来源链的人工检查。

## Talk Round 3：真实回复与失败边界

用户真实回复：`A`。

选择：非阻断警告不阻止 `released`；只有明确失败才阻止。警告必须继续显示在自动验收汇总和 Audit 记录中，不能被隐藏或改写成通过。

当前失败边界：机器硬门失败、自动读者题集未达到已确认阈值、来源/Claim/结构/完整性失败、运行未完成、汇总缺失或结果无法判定，均不能 `released`。人工只确认汇总完整且没有明确阻断项；不对正文和来源链做人工复核。

Talk Round 3 已收敛：保留 `released/not_released`；自动检查承担内容与来源质量；人工只确认汇总；非阻断警告可随包发布但必须留痕。

## Grill：核实结果与处置

### 已核实的四项退出检查

1. **外部接口：pass**。本次方向不改变 provider、OKF 消费者或外部服务接口；只改变本地 Task 3 的人工确认职责。现有 Reader 质量输出、固定题集和本地 Reader/Audit 分包合同可作为事实基础。
2. **规范名称：pass**。`published/degraded` 继续表示单页状态；`released/not_released` 继续表示整套交付结果；`human_reviewed` 继续表示人工内容核验，不能拿来表示本选择。新增领域术语“汇总确认”已写入候选 `CONTEXT.md`；具体序列化字段和回执格式延期到下游材料，不能复用 `human_reviewed`。
3. **失败语义：pass**。机器硬门失败、自动读者题集未达阈值、来源/Claim/结构/完整性失败、运行未完成、汇总缺失或结果不可判定，均阻断 `released`。stale、deprecated 等已定义的非阻断警告可以随包发布，但必须在汇总和 Audit 留痕。
4. **范围边界：pass**。Task 3 做 89 条全量 Reader 发布、自动固定读者题集和一页汇总确认；不做逐页人工验收、逐来源链人工检查、永久人工队列、第二套状态或新的页面类型。

### 文档与冲突处置

- `CONTEXT.md`：**changed**。在候选工作树中补充“汇总确认”的领域定义和交付边界；理由是该词已成为本轮确认后的正式业务含义，不能只留在口头对话。
- ADR：**created**，候选文件 `docs/adr/0008-task3-summary-confirmation-release-gate.md`。三项判据均为真：发布门难以反转；没有背景时“released 但没有人工读正文”会令人意外；这是人工负担与自动评审风险之间的真实取舍。ADR 仍标记为 pending final make-decision confirmation。
- 与现有 `CONTEXT.md`/PRD 的冲突：现行主线仍写“人工读者门”，这是预期的待确认合同差异；没有直接改主线 PRD，也没有把候选方向伪装成已发布合同。Task 2-C 的 Agent-only ADR 仍只约束 Task 2-C，不被本次 Task 3 方向覆盖。

### 开放问题与延期交接

- `汇总确认` 的具体序列化字段名、回执形状和存放位置：交接给 Task 3 downstream materials；Task 3 本身必须保留最小确认事实（汇总可判定、无硬失败、确认人和确认时间/运行绑定），且不能产生 `human_reviewed`。
- 非阻断警告的完整展示样式：交接给 Task 3 downstream materials；Task 3 本身必须完成最小分类和展示，未知或无法分类的信号按硬失败处理。
- 自动读者题集的最终运行实现和全量 17+3 真实结果：交接给 Task 3 build-code/verify-code；完成条件是完整题集、阈值、失败原因和可重放报告齐全。

最终确认后的状态修正：ADR 0008 已改为 `accepted`。上方 pending 文字只保留当时历史，不再表示当前状态。

### 对现行 PRD 旧人工门的取代关系

本次用户确认明确取代 PRD Task 3 中“完整 17+3 逐题做人审、记录 `human_reviewed`、人工执行归属准确率评分”的旧人工职责。17+3、15/17、0/3、90% 标题/归属、来源链和可重放要求本身继续有效，但改由自动流程执行并如实记录实际评审主体；人工只做汇总确认。该取代关系只适用于 Task 3 人工职责，不改变其他机器门、页面合同、旧包保护或 Task 2-C 历史证据。

自动流程可以组合确定性检查与 Agent 评审；具体组合由工程设计选择，不是新的产品方向。无论组合如何，都必须只读取允许的 Reader 输入、记录真实 actor/model/rule/seed/hash，不得写 `human_reviewed`，缺失或不可判定结果按硬失败处理。

## 独立方向审查：事实与处置

方向审查真实结果：available；1 个异源审查器返回结果，另一个同源路由被排除。审查不是通过门，也不替用户决定方向。结果保存在：

- `quality/reviews/results/make-decision-direction-44cfcf2b822597008616a7be4492248ff747e4a0-5de13928-888f-4c57-b67b-f17603472ed0.json`
- `quality/reviews/reports/5de13928-888f-4c57-b67b-f17603472ed0.md`

处置如下：

- **硬失败/非阻断警告边界：已修正**。硬失败包括机器硬门失败、自动读者题集未达阈值、来源/Claim/结构/完整性失败、运行未完成、汇总缺失或结果不可判定；stale、deprecated 等已有的非阻断信号只进汇总和 Audit，不阻断 `released`。这条边界已写入本日志、候选 `CONTEXT.md` 和 ADR。
- **汇总确认与 `human_reviewed` 的关系：已修正**。人工只做“汇总确认”，不做内容核验；不设置 `human_reviewed`、`verified` 或人工内容信任等级。`agent_only` 只描述自动读者评审主体，不被改写成人工评审。
- **自动门可靠性与汇总覆盖：接受为已知风险，延期验证**。当前不声称自动门已经被 Task 3 全量证明；build-code/verify-code 必须用真实 89 条输入、完整 17+3 题集、明确阈值、硬失败清单和可重放报告证明它们足以承担阻断职责。若自动结果缺失或不可判定，仍然 `not_released`。
- **影响范围与生效时机：已补齐**。本方向只改变 Task 3 的交付确认方式；不回写 Task 2-C，不改变既有单页 `published/degraded` 语义，不让失败运行覆盖上一份正式包；可重放交付和旧包保护继续保留。
- **“可重放材料”范围发现：不采纳**。它不是本轮新增的检查项，而是 PRD 既有的 Task 3 可重放交付要求（见 PRD:914）；因此保留在交付范围内，不构成 scope creep。
- **阈值来源发现：已补齐**。89 条全量、17+3 固定题集、正向至少 15/17、负向 0/3 均沿用 PRD Task 3 的既有门槛（见 PRD:902），不是本轮临时创造的数字。

所有方向审查发现均已逐条处置；没有把审查结果改写成 provider pass，也没有新增用户未确认的产品方向。

## 权威依据与未改动项

- PRD 的页级/交付级状态分离见 `docs/plans/knowledge-digest-knowledge-publication-prd.md:198`；Task 3 的 `released/not_released` 交付边界见 `:315`。
- 全量读者门的 17 个正向、3 个负向、15/17 和 0/3 阈值见 PRD `:902`；本轮沿用，不降低、不新增、不改写。
- 标题脱离路径可理解率 90%、产品/模块归属准确率 90%以及评分人/规则/样本量/seed 可追溯要求见 PRD `:904`；本轮沿用，不降低、不新增、不改写。
- 可重放交付、旧 formal 保护和“写入成功不等于知识发布成功”见 PRD `:914`；本轮沿用。
- 被拒方向：删除 `released/not_released`、取消旧包保护、人工逐页/逐题/逐来源链验收、把非阻断警告变成硬失败；均不作为当前方向。

## 决策草案

### 方向

Task 3 继续生成 89 条全量 Reader Bundle 和 Audit/Archive Package，保留整套结果的 `released/not_released` 状态。

`released` 不再要求人工逐页阅读、逐题判断或逐条检查来源链。发布前由机器完成来源、Claim、结构、完整性、失败隔离等硬门，并自动运行完整固定读者题集；人工只看一页自动验收汇总，确认汇总完整、可判定且没有明确阻断失败。

### 用户流程

1. 用户启动一次 Task 3 全量发布。
2. 系统冻结 89 条来源、TopicIndex、ProductGazetteer、Concept Contract v1、三类模板、provider/model/config、参数、预算和当前 commit。
3. 系统从同一 TopicIndex 和 audit records 生成 canonical `index.md`、产品/模块索引、主题页导航；`Home.md` 只做兼容入口，不维护第二套事实。
4. 系统生成 Reader Bundle，同时生成 Audit/Archive Package 和自动验收汇总；成功页进入 Reader，失败、冲突、无归属或缺证据内容进入 Audit/Archive 的 degraded 记录。
5. 系统生成有结构依据的双向 Related links；没有关系就省略。
6. 系统生成 Task 2 旧结果、CompanyBrain 和新结果的固定对比报告，覆盖保存完整性、机器质量、正文/导航可读性、信任/新鲜度、失败、耗时、成本和局限。
7. 机器检查来源、Claim、结构、完整性、页面导航、失败隔离和可重放材料；“可重放材料”沿用 PRD 的既有 Task 3 交付要求，不是本轮新增的产品方向。
8. 自动流程运行完整 17 个正向问题和 3 个负向问题，检查入口、首次命中页、答案、边界/版本、来源链、首次命中率和负向误命中。
9. 系统按 TopicIndex 的 `old_path_mapping` 生成旧路径 alias 或 deprecated 映射；失败或中断只重放未完成的 affected source/topic，保留成功批次、旧 formal 和审计现场。
10. 用户只打开一页汇总：看完成情况、硬失败列表、非阻断警告列表、关键计数和运行绑定；不打开知识页，不逐题，不查来源链。没有硬失败且用户完成汇总确认：整套结果可标为 `released`；有硬失败、汇总缺失或不可判定：保持 `not_released`，旧正式包不被覆盖。
11. Task 3 结束后，把最终结果、风险和延期项交给 Task 3-Closeout；Closeout 只做文档同步、清理、归档和恢复演练。

### 页面和数据范围

- Reader：`README.md`、兼容 `Home.md`、唯一 canonical 根 `index.md`、产品/模块索引、正式主题/concept 页面、`references/` 来源入口和 `log.md`；不放 `_digest`、`_archive`、provider 日志或审计现场。
- Audit/Archive：89 条输入的 manifest、snapshot、audit ledger、Claim、Evidence、原文、失败/冲突/降级原因、旧页面、运行报告，以及可回放的 provider/model/config/模板/词典/commit hash 和质量证据；不作为日常阅读入口。
- 单页状态仍只有 `published/degraded`；整套结果状态仍只有 `released/not_released`。
- “汇总确认”是独立的人工动作，不等于 `human_reviewed`。

### 成功边界

- 机器硬门全部通过。
- 自动完整读者题集达到既定阈值：正向首次命中至少 15/17，负向误命中 0/3。
- 标题脱离路径可理解率至少 90%，产品/模块归属准确率至少 90%；评分人、规则、样本量和 seed 可追溯。
- 页面正文最多 120 行，整页最多 300 行；无空分类、泛占位、hash 主路径、断链和空壳入口。
- 89 条来源都能在 manifest、snapshot、audit ledger 定位；失败来源与无关已发布页隔离。
- 旧 formal path 全部能解析到 canonical 页面，或有真实 alias/deprecated 映射。
- 对比报告同时覆盖保存完整性、机器质量、正文/导航可读性、信任/新鲜度、失败、性能、成本和局限。
- Reader、Audit/Archive、manifest、报告和恢复材料齐全且可重放。
- 汇总完整、可判定；人工完成汇总确认。
- 非阻断警告已展示并留痕，但不阻断发布。
- 汇总至少能区分硬失败、非阻断警告和“无法判定”；无法分类的信号按硬失败处理。

### 失败边界

- 来源、Claim、结构、完整性、导航、人工修改冲突或失败隔离硬门失败。
- 自动读者题集未达阈值，或自动结果缺失、格式错误、运行超时、无法判定。
- 汇总缺失，或汇总没有明确区分硬失败与非阻断警告。
- 出现未知、未分类或无法解释的质量信号。
- provider 失败、截断 JSON、fallback、超预算、重复失败、来源冲突、无归属、缺必需证据或降级页进入 Audit/Archive，不进正式 Reader 导航。
- 任一失败：不覆盖旧正式包，保留 Audit/Archive 失败证据，并保持 `not_released`。

### 非目标

- 不要求人工逐页验收、逐题验收或逐来源链检查。
- 不把“汇总确认”写成 `human_reviewed`。
- 不删除 `released/not_released`，不改变 Task 2-C 的 Agent-only 范围。
- 不新增页面类型、永久人工队列、调度器、数据库或第二套发布状态。

### 仍延期

- 汇总确认的具体序列化字段、回执形状和存放位置；最小确认事实本身属于 Task 3 范围。
- 非阻断警告的完整展示样式；最小“硬失败/警告/无法判定”分类属于 Task 3 范围。
- 89 条真实编译、完整 17+3 自动读者运行、硬门验证和失败重放：Task 3 build-code/verify-code。
- 主 PRD、根 `AGENTS.md`、主 `CONTEXT.md`、根 `README.md` 的最终同步：最终决策确认后按 Task 3-Closeout 处理。

## 独立细节审查：事实与处置

细节审查真实结果：available；1 个异源审查器返回结果，另一个同源路由被排除。结果保存在：

- `quality/reviews/results/make-decision-detail-4cbd2c44f4a32e717096ad88b846686d4f8298b1-d115dad8-ff02-457d-ae51-9efdf2c12b05.json`
- `quality/reviews/reports/d115dad8-ff02-457d-ae51-9efdf2c12b05.md`

逐条处置：

- **初版决策草案遗漏 Related links、固定对比报告、旧路径映射、失败重放、90%/120-300 行/来源定位门和对比覆盖项：已修正**。这些原始 Task 3 范围继续保留，并已逐项写回当前用户流程、页面范围和成功边界。
- **细节审查记录缺失：已修正**。本节补充了真实结果、结果引用和处置；之前的状态行和“尚未执行”文字已标为被后文取代。
- **90% 标题/归属门缺少来源：已修正**。阈值和可追溯评分要求沿用 PRD `:904`，不是本轮新增。
- **Task 3-Closeout 交接遗漏：已修正**。用户流程新增最终交接步骤；Closeout 仍只做文档同步、清理、归档和恢复演练，不重新定义范围。
- **无法分类的信号是否按硬失败：已由后文用户回复确认**。在用户回复前，该问题曾保持开放；不能由审查意见或 Agent 默认决定。

细节审查当时的剩余开放问题只有最后一项；该问题已由后文用户回复闭合，没有把可用审查结果改写成 provider pass。

## 最终确认前的唯一开放决策

如果自动结果既不能证明是硬失败，也不能证明只是普通警告，如何处理：

- **A（建议）**：阻止 `released`，保持 `not_released`；不要求人工临时判断。这样最不容易把未知问题发布出去，但会让少数模糊结果多跑一次。
- B：按普通警告处理，允许 `released`；流程最顺，但可能把未知问题带入正式结果。
- C：每次交给人工单独裁决；风险可控，但会重新制造你不想要的人工判断负担。

## 最终确认前开放决策：真实回复与收敛

用户真实回复：`A`。

选择：自动结果无法明确归类为硬失败或非阻断警告时，阻止 `released`，保持 `not_released`；系统应自动重跑或进入失败处理，不要求用户临时人工裁决。该选择不改变“已知的非阻断警告不阻止发布”，只规定“未知或无法判定”不能被当成警告放行。

细节审查的最后一个发现已处置；当前没有未解决的方向性问题。

## 最终确认

- 用户真实回复：`确认，继续`。
- 确认含义：接受本日志中的 Task 3 方向、范围、成功/失败边界、非目标、风险与延期交接；授权标准 WorkflowHub 进入下一阶段，不授权跳过阶段或由下游补造产品需求。
- Approval binding：宿主当前会话中的最终确认原话；正式确认 fact 和不可变交互 aggregate 由 `make-decision` 收尾绑定。
- 未解决的方向性问题：无。

## 2026-08-13 正式交付边界修复记录

- 原始需求：继续处理正式交付边界的四个问题；用户不想逐题、逐页或逐来源链人工验收，只看一页机器汇总；失败时不能覆盖旧正式包，重放不能整库重跑。
- 关键事实：当前真实候选 `run-a21c831619c44834` 的质量门和交付硬门已通过，但没有可安全绑定的 formal root，也没有当前运行的真实 summary confirmation；底层 `affected_set`/`run_batched` 已有，但缺少一个能明确列出“只重放未完成 affected 项”的回放计划；WorkflowHub doctor 的真实失败是 `mini_task` 路由 mode 配置不符合 `wh-review` 合同。
- 选择：formal root 必须显式提供；已有根先检查完整包形状、软链接和整包 hash，首次发布允许明确的空目标；旧包保护从预检事实推导，不再信任调用方布尔标记。affected replay 只做既有 batch ledger 的只读投影，合同变化直接停止。summary confirmation 仍只绑定 `run_id + summary_sha256 + actor + confirmed_at`，含义是“汇总完整可判断”，不代表人工内容审核。
- 理由：这样能把“没有目标”“目标不完整”“目标在等待期间变了”都 fail-closed，同时不另造恢复状态机、不增加人工验收负担，也不把配置修复或本地测试冒充 provider review pass。
- 延期交接：真实候选仍需绑定实际 formal root，用户仍需对一页汇总作一次明确确认；之后才可做 locked readback。WorkflowHub mode 配置已修正并通过 `doctor`，但当前快照是否能形成可信的异源 provider review 仍需按真实 task/workspace 运行验证；没有可信终态就保持 unavailable/incomplete。

## 2026-08-13 正式边界复审追加记录

- **原始需求**：修复四个正式交付边界问题后继续测试和审查，直到没有已知实现问题再停下汇报。
- **关键事实**：独立复审发现批次拆分会把“父批次失败、子批次成功”误判为未完成；非法旧 formal tree hash 会让 replay 继续；首次空 formal 目标只有预检测试，没有真实安装后的 readback 测试。
- **选择**：把成功拆分子批次视为该来源已完成；旧 hash 非法直接停止 replay；补首次空目标的真实 locked install/readback acceptance 测试。
- **理由**：避免重复处理已成功内容，避免在旧正式包事实不可信时继续恢复，并让首次发布边界有端到端证据。
- **延期交接**：真实候选仍缺实际 formal root，真实 provider 失败运行上的 affected replay 尚未演练；WorkflowHub 当前 TaskHandle 仍没有 workspace identity，因此 fresh review 仍是 `incomplete`，不改写成通过。

## 阶段结束大白话摘要

Task 3 可以继续。机器负责完整硬门和固定读者题集，人只看一页自动汇总并确认“结果完整、能判断、没有硬失败”；已知普通警告可带着发布，未知或无法分类的结果必须停在 `not_released`。不要求人工逐页、逐题或逐来源链验收，也不把这次确认写成 `human_reviewed`。下游只能落实已经确认的范围；具体字段和存放位置可以设计，但不能改变这里的发布含义。
