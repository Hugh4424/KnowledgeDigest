# Task5 当前生效决策记录 v4.7（2026-09-04）

<!-- ACTIVE-DECISIONS: 从文件开头到唯一归档分隔标题之前为当前可消费决策；标题之后仅作历史回查。 -->

## 当前状态

`real_run_quality_passed` / `release_pending`。本记录不把当前代码、绿色测试、旧候选、旧 review 或 raw preflight 当成完成证据；本次真实 bundle 的质量通过也不替代实现审查和正式 M401/M401-R/M402 闭环。

## D-167：处理最新实现审查的真实发现（2026-09-04）

### 关键事实

最新 authenticated `mini_task.implementation` 结果发现：active spec 的机器可读修订标记仍为 v4.6；送审 AC trace 的临时输入使用了旧式 `AC-001…AC-013` 且 AC-002 锚点覆盖了 AC-009；user result 把尚未完成的实现审查写入 oracle。

### 选择与理由

已把 active spec 标记同步为 v4.7。下一次实现审查输入统一使用合同规定的 `AC-v4-01…AC-v4-13`，每条只引用不重叠的函数级锚点，并把 user result 的 oracle 限定为已存在的 canonical receipt/trace 校验；这修复的是审查证据身份，不把审查结果误写成 M401-R 或 M402 通过。

### 状态

本次结果保留为 `actionable` 记录；修复后必须重新生成当前 snapshot/material 证据。当前仍是 `release_pending/not_released`。

本记录以最新决策为准：D-163 已取代此前关于旧模型和“设计审查 terminal-clean 才能继续”的冲突表述；旧模型和旧阻断条件只保留为历史事实，不再作为当前执行条件。

## 原始需求

- 只使用 `/Users/Hugh/Downloads/confluence 原始数据` 做知识消化，不凭空补充外部知识；保留全部 89 条原始资料和四个产品的正确归属。
- 必须先做垂直切片，再做 89 条全量；真实知识生成要调用用户配置中的 LLM 和 embedding，LLM 固定为 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`，配置从 `/Users/Hugh/.config/knowledge-digest/config.json` 读取。
- 读者入口按问题和场景路由；分类按产品、模块、对象、场景、边界；正文按业务答案组织；页面类型覆盖定位、概念、操作、诊断、经验。
- 产物必须放在 `/Users/Hugh/Downloads` 的可识别目录，路径、文件名、文件夹和正文都要简洁可读；Reader 可直接阅读，Audit 能回查到原始来源、证据和定位。
- 五项质量必须逐项、逐场景严格高于 CompanyBrain，不能用平均分、文件数量或机械打分替代；任何缺失、未知、失败或无法回查都不能伪装成通过。
- 只有来源闭包、真实 provider 消费、Reader/Audit、五项严格胜出和必要实现证据全部成立，才允许宣布 `released` 或 `close`。

## 核心需求

把 89 条 Confluence 原始资料消化成一个简洁、可读、可回查的知识包：不添外部知识、不漏原始资料、不串产品；读者先按问题和场景进入，再按产品、模块、对象、场景、边界和五类页面类型找到业务答案。

## 目标

实现一个能由真实 qwen3.8 与 jina-embeddings 参与生成的 Reader/Audit 闭环，并证明五项质量逐场景严格高于 CompanyBrain；只有当前实现、来源、质量和发布证据都闭合，才允许完成发布。

## 范围

本次必须覆盖垂直切片和 89 条全量，包含四个产品：GoInsight、EMM for Android、EMM for iOS、Merchant System。用户流程是：读取原始目录 → 固定来源与产品归属 → 垂直切片验证 → 89 条全量消化 → 写入 `/Users/Hugh/Downloads` 可识别目录 → 从 `Home.md` 按问题/场景阅读 → 从 `Audit.md` 回查来源、证据和定位 → 五项逐格对比 → 通过全部门禁后再发布。

## 用户流程与边界

- 成功：89 条都在来源审计闭包中，四个产品归属正确，Reader 页面可读，Audit 可回查，真实 provider 调用可核验，五项每个适用场景均为 `KD_WIN`。
- 失败：任何来源缺失、产品串线、正文无法阅读、证据无法回查、provider 未调用或失败、五项出现非 `KD_WIN`/未知/缺行，都只能保留 `not_released` 或 `blocked`。
- 空白原始页只能保留在 Audit，不凭空补正文；它不能掩盖其它来源的失败。

## 非目标

不读取或补充外部知识；不改 raw 或 CompanyBrain；不新增任务、不拆成后续需求；不把复杂的 `modules`、`boundaries`、`knowledge`、`audit` 公共目录重新引入；不把 embedding、数据库、向量库、调度器或 agentmemory 变成正式产品功能；不以文件数量、平均分、旧候选、旧 review 或绿色测试冒充质量通过。

## 决定

采用一条生产链：`digest CLI → compiler.digest → providers(qwen3.8/jina-embeddings) → quality.py → publisher.commit`。公开结果只保留 `bundle/README.md`、`Home.md`、`products/<product>/<page_type>/*.md`、`Audit.md` 和 `_audit` 机器证据；五项质量按问题路由、五轴分类、业务答案、五类页面、Reader/Audit 五个维度逐场景比较 CompanyBrain。设计审查 terminal-clean 是可选记录；实现审查、M401/M401-R/M402 和真实质量结果仍是硬门。

## 需求→决定

| 原始需求类别 | 当前决定与证据 | 状态 |
| --- | --- | --- |
| goal | 全量 89 条、四产品、五项逐场景严格胜出；见本记录「目标」和 `spec.md` | covered |
| flow_or_surface | 垂直切片→全量→Downloads bundle→Home 路由→Reader/Audit；见「用户流程与边界」 | covered |
| data_or_state | 只读 raw，保留 89 条来源闭包、产品归属、provider 与发布状态；见 `plan.md` | covered |
| success_failure_acceptance | 五项适用行全为 `KD_WIN`；缺失/未知/失败 fail-closed；见「验收标准」 | covered |
| constraint_non_goal_defer | qwen3.8、config.json、无外部知识、无新增任务、未完成前不 released；见「非目标」和「风险与延期交接」 | covered |

## 验收标准

可验证条件：场景为当前 raw-only 的垂直切片和 89 条全量；数据来源为 `/Users/Hugh/Downloads/confluence 原始数据`、当前 CompanyBrain 快照、`/Users/Hugh/.config/knowledge-digest/config.json`；通过条件是来源闭包、四产品归属、真实 qwen3.8/Jina、Reader/Audit 和五项逐格全部成立且每个适用行 `KD_WIN`；失败条件是任一来源、定位、provider、审查、矩阵或发布身份不闭合，结果必须是 `not_released`/`blocked`。

## 风险与延期交接

当前未决项是：官方当前 implementation review 尚未返回可用语义结果；因此 M401-R、M402 和正式 released 尚未成立。交接给下一步：不再重复设计审查，先重新生成当前 snapshot/material 绑定的实现证据，再依次闭合 M401、M401-R、M402；若 review/provider 不可用，原样记录并保持 `not_released`。

## 三轮 talk

第一轮选择：直接沿用旧复杂目录，后果是读者入口和产品归属继续混乱，拒绝。第二轮选择：只做脚本整理或离线规则，后果是没有真实语义生成和质量保证，拒绝。第三轮选择：保留单一生产链、真实 provider、简洁 Reader 和可回查 Audit，代价是门禁更严格、provider 不可用时不能假装成功，采用。

## 调研

已核对当前工作树、WorkflowHub 根材料、原始 89 条、CompanyBrain、当前 qwen3.8/Jina 配置约定和真实候选；事实与方案以当前四份材料的 active section 为准，历史内容只用于回查。

## grill

已识别的反对意见：五项全胜不能由平均分推导；真实运行不能替代实现审查；89 条闭包不能用 Reader 文件数推导；简洁目录不能牺牲 Audit。当前方案逐项保留这些限制。

## 审查处置

设计 terminal-clean 按用户决定降为 advisory；当前 implementation review 请求在无语义结果后终止，未把超时、旧 review 或静态 JSON 当作通过。下一轮只接受绑定当前材料的 authenticated 结果。

## 最终确认

用户最近的“继续”只确认继续执行，不等于五项质量发布确认；在实现审查、M401-R、M402 和五项真实逐格结果闭合前，最终发布确认保持未完成。

## 拒绝方案

拒绝旧 V37/V50 临时目录、无 LLM 的离线整理、复杂公共目录、跨产品猜测、静态 CompanyBrain 对照和任何用平均分替代逐场景比较的方案。

## 未决项

implementation review 的当前 authenticated 结果、M401 packet、M401-R receipt、M402 真实 run receipt 及最终发布状态仍未闭合；这些是当前阻塞，不通过伪造解决。

## Supersedes

本 active section 取代 archive 之前的旧 Task2/Task3/Task4 根材料；D-163 取代旧 qwen3.6 和设计 terminal-clean 硬阻断；D-164 至 D-167 取代此前实现、血缘和证据身份口径。

## 文档结果

本文件、`spec.md`、`plan.md`、`tasks.md` 根材料已对齐 Task5 v4.7；旧内容保留在 `ARCHIVE-NON-ACTIVE` 后，仅作历史回查，不参与当前判断。

## Exit checks

当前只通过了材料对齐和部分真实质量事实；`quality_status=in_progress`、`product_release_status=not_released`。未完成项保持显式缺失，不能宣布 `released` 或 `close`。

## UI applicability

```json
{
  "result": "non_ui",
  "sources": {
    "raw_requirement": {"result": "non_ui", "description": "本任务交付本地 Markdown 知识包和 CLI 运行结果，不改页面或前端交互"},
    "project_inventory": {"result": "non_ui", "description": "当前项目是本地知识消化与发布工具，范围是编译、质量和文件发布"},
    "planned_or_changed_frontend_fact": {"result": "non_ui", "description": "没有计划或变更 frontend component、page、interaction 或 browser surface"}
  },
  "reason": "当前请求只改变知识消化管线和 Markdown 产物，不改变 UI",
  "handoff": "make-decision 已记录；不适用浏览器页面验收"
}
```

## 收敛检查

| 维度 | 用户答案 | 事实/材料 | 可执行验收 |
| --- | --- | --- | --- |
| 目标 | 用户已确认继续当前目标；取舍：质量优先于快速 close；被拒方案：只整理文件；未决项：正式门禁尚未闭合 | `decision-log.md`「原始需求」「目标」 | 场景：89 条全量；数据来源：raw；通过：四产品与五项闭合；失败：任一缺失即不发布 |
| 范围 | 用户已确认必须做垂直切片和 89 条全量；取舍：一次闭合全量；被拒方案：拆后续任务；未决项：无范围新增 | `decision-log.md`「范围」「用户流程与边界」 | 场景：四产品；数据来源：raw；通过：89 条进入闭包；失败：漏条或串产品 |
| 方案 | 用户已确认继续单一生产链；取舍：真实 provider 换取质量可证；被拒方案：离线规则冒充 LLM；未决项：implementation review/M401-R/M402 | `spec.md` 当前修订 v4.7、`plan.md` 当前 M401/M402 | 场景：真实运行；数据来源：config.json；通过：qwen3.8/Jina、Reader/Audit、五项全胜；失败：任何身份或调用不可证 |
| 验收 | 用户已确认五项必须全部高于 CompanyBrain；取舍：不接受平均分；被拒方案：机械总分；未决项：正式 M402 尚未闭合 | `decision-log.md`「验收标准」、`tasks.md` M402 | 场景：每个 projection×dimension；数据来源：当前 raw/CompanyBrain；通过：适用行全 `KD_WIN`；失败：缺行、未知、非胜出 |

## D-163：统一 qwen3.8，取消设计 terminal-clean 硬阻断（2026-09-03）

### 原始需求

用户明确要求以后统一使用 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`，并确认没有必要等待或产出可认证的 `mini_task.design` `terminal-clean` 结果；只要当前实现和真实质量链能继续，就继续推进。

### 关键事实

- 当前代码、用户配置约定、provider authority 和真实候选都已经使用 qwen3.8；旧模型只存在于历史归档或旧回归材料，不是当前 Task5 的允许模型。
- 当前 successor 校验已经允许 `parent_design_review=null`；真正仍需要的是 authenticated `mini_task.implementation`、当前 snapshot/material、M401/M401-R、真实 qwen3.8/Jina 运行、Reader/Audit 闭包和五项逐格胜出。
- 缺失设计审查结果不会证明质量通过，也不会替代实现审查；它只是 advisory 缺口。

### 选择与理由

把 active spec、plan、tasks 的模型合同统一为 qwen3.8；把 DESIGN-ADVISORY 明确为可选、非阻断记录，保留实现审查和全部真实质量硬门。这样去掉无价值的设计审查等待，但不把 provider 调用、绿色测试或旧结果当成 released。

### 延期交接

不再运行设计 terminal-clean review。继续从当前实现审查/M401-R 的真实身份闭合推进；若实现审查或后续真实运行缺证据，仍保持 `release_pending/not_released`，直到五项全部严格高于 CompanyBrain。

## D-164：修复当前实现审计发现的三个真实断点（2026-09-03）

### 关键事实

当前只读审计发现：formal Task5 若指定自定义 source manifest，compiler 和 formal Audit 仍可能各自读取仓库默认 manifest；formal Audit 会链接到随后被移除的临时 ledger；provider 预算不足在 formal runtime 外层会被归类成失败并返回 3，掩盖“暂时不可用/未执行”的事实。

### 选择与理由

增加 `DigestRequest.source_manifest_path` 并让 formal run、compiler、Audit 共用同一输入；正式 Audit 去掉已不发布的 `_audit/sources.jsonl`/`_audit/evidence.jsonl` 死链接；provider/config 不可用统一记录为 `blocked`、exit 2，保留真正的 `failed`、exit 3 给实现或发布错误。以上只修复身份、可读回查和失败语义，不改变 raw 内容、四产品归属或五项质量规则。

### 验证与延期交接

新增两项回归测试；Task5 相关 targeted tests 为 `124 passed`，完整回归为 `860 passed, 3 skipped`。实现审查曾因 provider 超时未产生可用结果，不能算通过；设计 terminal-clean 已按 D-163 放弃等待。M401-R/M402 和五项真实严格胜出仍未完成，因此当前仍为 `release_pending/not_released`。

## D-165：修正实现审查暴露的证据伪覆盖与占位行歧义（2026-09-04）

### 关键事实

当前快照完整回归为 `860 passed, 3 skipped`，但实现审查发现：不能用一张未区分责任的全量 pytest receipt 给 `AC-v4-01…13` 逐项填“已证明”；另外，active spec 原先同时写了“缺口占一行 RenderLedger”和“每个 section 生成两行”，导致 `unknown_units`、`rendered_units` 与 Reader 可见标题/正文的口径不一致。

### 选择与理由

AC trace 改为只接受当前快照、逐 AC 有明确 owner 的聚焦 receipt；没有直接证据的 AC 保持 unknown，不再用总回归数量冒充。占位 section 明确生成 `Reader.section` 与 `Reader.answer_body` 两行 Audit ledger，二者只计 `unknown_units`，不进入事实 lineage 分母；非占位 section 的两行才共享首个 raw binding。同步更新 spec/plan/tasks 和回归测试，避免实现、质量计算和审查包各自解释。

### 验证与延期交接

修正后相关血缘/语义/合同测试为 `22 passed`。本轮实现审查仍不能作为 M401-R 通过证据：旧 C3/M401 仍绑定旧 snapshot/material，新的逐 AC receipt 和当前 M401 fixture 尚待 authenticated gate 生成；M402 仍必须重新绑定当前 raw、CompanyBrain、qwen3.8/Jina 和五项逐格结果。状态保持 `release_pending/not_released`。

## D-166：让 AC trace 的测试归属与实际 owner 一致（2026-09-04）

### 关键事实

当前快照实现审查确认逐 AC receipt 已存在，但部分 implementation anchor 只是宽泛地落在 `tests/test_simple_digest.py`，而任务卡把四个 gate owner 规定在 acceptance 文件中；这会让 reviewer 无法区分“gate 必须覆盖的 owner”和“某一 AC 的具体行为测试”。此外，spec/plan/tasks 的修订标题仍停在 v4.6，和 D-165 不一致。

### 选择与理由

保留四个 gate owner 不变，同时明确：逐 AC anchor 必须指向实际覆盖该 AC 的具体测试函数；必要时可引用相邻回归文件，但不替代 gate owner。将三份 active 合同统一升为 v4.7，避免审查包按旧 revision 解释当前内容。后续 AC trace 使用不重叠的函数级 anchor，不再用同文件大段范围复用归属。

### 延期交接

当前实现审查的上一份结果仍需由这次身份一致的材料重新生成并由 authenticated adapter 记录；实现审查通过也只解锁 M401，不代表 M401-R、M402 或五项真实胜出已完成。

## D-162：真实候选的独立五维复核（2026-09-03）

### 关键事实

对 `/Users/Hugh/Downloads/KnowledgeDigest-task5-qwen38-real-20260903-v3` 做了独立黑盒复核：只使用当前 89 条 raw、当前 CompanyBrain 和固定 12 个质量投影；候选实际包含 89 条来源闭包、99 个 Reader 页，真实运行记录为 qwen3.8 与 jina-embeddings。首次复核发现评估器把合同允许的 `known_empty` 误判为失败，且定位页的一轮 qwen 输出因理由过长而截断；这不是候选知识内容通过的证据。

### 选择与理由

评估器已修正为：精确闭合的 `known_empty` 只要求没有 Reader 页、保留 Audit，不作为失败；独立评审提示将每个理由限制为短句并固定五个键，模型输出不完整仍保持 `not_released`。修复后重新执行独立复核，12 个投影的两轮、五个维度全部为 `KD_WIN`，无 judge error、无 hard blocker；新增回归测试验证 `known_empty` 的 Audit-only 闭包。

### 当前结论

当前真实候选满足“质量复核通过”这一项，但这不等于正式发布：完整回归为 `858 passed, 3 skipped`；authenticated implementation successor、M401-R 和 M402 仍未形成当前身份一致的正式证据，因此总状态仍为 `release_pending`，不得 close/released。

### 当前证据身份

最新全量回归、AC trace、用户结果和独立质量证据都必须由 WorkflowHub canonical record 自身绑定当次 snapshot/material；本记录不重复抄写会随补充记录变化的 hash，避免“记录证据引用又改变被引用快照”的循环。当前这些记录只证明当前回归和真实候选质量结论，不宣称实现审查、M401-R 或 M402 已完成。

### 延期交接

不再重复设计审查，也不把缺少 `terminal-clean` 的 DESIGN-ADVISORY 当阻断。下一步只处理当前实现审查/M401-R 的身份闭合；若无法取得当前 authenticated review，必须明确保持 `not_released`，不能用旧 review、静态质量 JSON 或独立黑盒结果替代。

## ARCHIVE-NON-ACTIVE: previous root material

# Decision Log

## 原始需求

| source_id | 原始需求/约束 | 来源引用/原文摘录 | 关联 D/处理状态 |
| --- | --- | --- | --- |
| R-001 | Task 2-B 必须按标准 WorkflowHub 从 `make-decision` 开始，不跳阶段，不让 `build-spec` 补产品决策。 | 用户原话："请按标准 WorkflowHub 从 make-decision 开始，不要跳阶段，也不要依赖 build-spec 补需求。" | D-001–D-003；已覆盖 |
| R-002 | Talk 说清选项、后果、风险；decision-log 保留原始需求、事实、选择、理由和延期交接。 | 用户原话："Talk 请用大白话说明选项、后果和风险；decision-log 记录原始需求、关键事实、选择、理由和延期交接。" | T-001–T-003、G-001；已覆盖 |
| R-003 | 先冻结完整用户流程、页面范围、数据状态、成功/失败边界、非目标和延期项。 | 用户原话；PRD §Task 2-B，lines 627–699 | 本文「流程与边界」；已覆盖 |
| R-004 | 交付小语料类型化正文编译闭环：Normalizer → TopicIndex → PageDraft → OKF Concept Compiler → Publication Gate；三类 page type；正文与 Evidence/archive 分离；失败 fail-closed。 | PRD lines 651–668、686–699 | D-001–D-004；已覆盖 |
| R-005 | Task 2-A 已正式完成，其缺口已在其他会话处理并合并到 `main`。 | 当前用户原话："我已经把task 2-A正式完成了，差的这几项都在其他会话搞定了，也合并到main了" | Task 2-A handoff；按当前用户事实接收，不在本任务重开 |

## 目标

- 让小语料页面真正回答读者问题，而不是把 Evidence 原文堆进正文。
- 保留 Task 2-A 已冻结的 Reader Bundle、frontmatter、index/log、source/claim footnote 合同。
- 在机器门内证明正文可编译、可归因、可回查、可失败；不把机器结果说成人工读者质量。

## 流程与边界

### 用户流程

1. 运行读取 Task 0/Task 1 的冻结输入、TopicIndex、样本覆盖记录和 Task 2-A Reader Bundle 合同。
2. Structure Normalizer 将父子页、标题/H1、FAQ、表格、图片、双语、版本和噪声块变成可追溯结构。
3. TopicIndex 确定主题身份、产品/模块关系和 page type；未映射、冲突或证据不闭合的项进入 Audit。
4. PageDraft 生成受控 section 草稿；provider 只填写受控正文内容，不能自行增加 page type、section 或来源字段。
5. OKF Concept Compiler 将正文、页内 source id、claim id footnote、frontmatter 和索引投影写入样本包。
6. Publication Gate 检查必需 section、100% 事实归因、数字/标识符/版本、命令/端口/配置、表格/图片、近重复、golden-negative 和页面边界。
7. 通过的页进入 Reader 导航；失败页保留 Audit/Archive 原因、输入指纹和恢复路径，整包保持 `not_released`。

### 页面范围

- Reader concept page：`product_overview`、`module_or_capability`、`procedure_or_rule`。
- Reader navigation：根、产品、模块和主题索引；`index.md` 是唯一 canonical navigation。
- Audit/Archive：失败、冲突、缺证据、旧正文和完整 Claim/Evidence/原文；不是读者入口。

### 数据状态

- 页级：`published` 或 `degraded`；`degraded` 不进入正式导航。
- 交付级：Task 2-B 只能是 `not_released`，不能声称 `released`。
- 内容信号：`generated`、`digest_machine_pass`、`verified`、`stale_after` 按 Task 2-A/PRD 合同分开；内容变化使旧验证事件失效。section 另记录 `documented` 或 `source_not_documented`；后者只允许用于 `procedure_or_rule.exceptions`，不是页级状态，也不等于“没有异常”。
- 增量更新：section 只有在依赖集合、版本、结构关系和归因都可证明未变时才能复用；影响关系不确定时扩大到整页重编。

### 成功边界

- 至少 6 个 machine-passing concept。
- 三类 page type 各至少 1 个；`procedure_or_rule` 在 `exceptions` 经过确定性来源审计并标为 `source_not_documented` 时，仍可计入 page-type 覆盖，但不能声称异常处理规则已被回答。覆盖 Task 1 inventory 中实际存在的长文、表格/图片、双语、多源类别；不存在的类别必须有 machine fixture 或排除理由。
- 使用 Task 0/Task 1 已冻结的 12–20 篇代表样本，不由编译器临时挑选；样本来源和覆盖以 `quality/evidence/task2-entry/task2-entry-sample-coverage.v1.json` 为准。
- 至少一次冻结 provider/model/预算的真实语义运行完成并留存结果。

### 机器验收底线（下游不能降低）

- 语义出口必须同时满足：`machine-passing concept >= 6`；三类 page type 各至少 1 个；实际 inventory 中存在的长文、表格/图片、双语、多源类别均被覆盖；inventory 中不存在的类别必须有 machine fixture 或明确排除理由。
- 必须至少完成一次冻结 provider/model/预算的真实语义运行并留存运行结果、失败项和归因信息；未完成、fallback、Jaccard-only 或语义证据不足时，交付级保持 `not_released`。
- 这三条是 Task 2-B 的机器成功底线，不由 `build-spec`、临时样本或单次结构测试下调。
- `procedure_or_rule.exceptions` 是唯一例外：若确定性来源审计证明冻结来源没有明确异常触发、处理、分支或恢复规则，section 必须存在并写入 `source_not_documented` 状态；它不生成领域 Claim，异常专属问题记为 `not_answerable`，但不因此阻断该页 Reader/机器通过。其他必需 section 仍须完整、可归因并通过既有门禁；来源含糊、provider 映射失败或审计不确定时仍按失败处理。

### 失败边界

- 必需证据缺失、归因不闭合、版本冲突、事实保真失败、provider 失败、截断 JSON、fallback、golden-negative 未失败或近重复命中：页为 `degraded`，不进正式导航；唯一例外是通过确定性来源审计确认的 `procedure_or_rule.exceptions=source_not_documented`，其状态进入页内审计且不被写成领域事实。
- provider 只能生成受控 section；任何无法解析为唯一 `claim_id + source URI + content hash + fragment_locator` 的事实不得进入正式正文。
- 影响关系无法证明时整页重编；整页重编失败时整页 `degraded`，旧 Reader 页不被失败结果覆盖。
- Jaccard/离线结果只能作结构基线，不能满足语义 exit；Task 2-B 不形成人工读者质量通过。

## 范围

- 当前范围：小语料、三类 page contract、Normalizer、受控 PageDraft、OKF concept 编译、claim/source 回指、保真与降级门、样本索引和语义运行证据。
- 当前 contract revision 预算：`1/1`（本轮 C1 变更已占用唯一额度，待用户确认）。改变 section 集合、模板、必需/可选字段或 page type 映射消耗唯一一次修订；只修复既有合同的行为 bug 不消耗；后续不得再用实现缺陷修复偷改本规则。
- 影响闭包定义：section 的直接 source/claim/版本/结构依赖，以及由其变化传递影响的关联 section；无法证明不受影响即纳入整页重编。

## 非目标

- 全量 89 篇正文编译和正式 `released`。
- Task 2-C 的人工读者门、人工评分、`human:*` 信号和最终信任判断。
- Task 3 的完整 17+3 题集、全量交付门和发布。
- 新增 page type、数据库、图谱、永久 candidate 队列、无人维护的人工复核系统。
- 用全局正文复制率作为硬门；不把 provider 成功、写回成功或结构 lint 当成读者质量通过。

## 决定

### D-001

- question/final_option: 正文由谁控制结构？最终选择 A：固定页面骨架，provider 只填写受控 section。
- recommendation/plain_language: 推荐；代码先定页面该回答什么，模型只补具体说法。
- decision: 必需/可选 section、page type、来源字段和校验边界由确定性代码控制；provider 输出不得改变这些合同。
- source_type/reference/exact_excerpt: user_talk / Talk Round 2 / T-001 / "A"；PRD lines 653–655、686–690。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: Evidence 不适合作为读者正文；正文必须可读且每条事实可回查；provider 失败只能 degraded/not_released。
- Logic: Evidence dump 是已知问题 -> 需要可读正文但不能放松归因 -> 由固定骨架限制模型输出 -> 必需 section、来源和失败边界稳定可验。
- choice_reason/impact: 可预测、容易回查、不会让模型扩张页面合同；影响 `PageDraft`、compiler、validator、provider prompt 和 semantic sample runner。
- consequences_and_risks: 文风可能更模板化；受控 section 的内容矩阵必须足够清楚，否则会得到空泛答案。
- rejected_alternatives: B（provider 生成完整 PageDraft）风险是漏 section、无证据断言和截断；C（纯规则拼接）不能满足语义正文 exit。
- unresolved_items/owner: 各 page type 的最终 section 内容和样本级提示词在后续规格/实现材料中落地，但不得改变本决定的骨架边界；owner=Task 2-B。
- Supersedes: none。

### D-002

- question/final_option: 来源更新时是否整页重编？最终选择 B：只重编受影响 section，但先计算影响范围。
- recommendation/plain_language: 用户选择 B；它减少无关内容抖动，同时保留旧正文稳定性。
- decision: 每个 section 必须记录 source/claim/版本/结构依赖；只有依赖集合和归因全部未变才能复用旧 section；新旧内容不能直接拼接。
- source_type/reference/exact_excerpt: user_talk / Talk Round 2 / "我想选B，但是需要注意，虽然只改受影响的section，但是需要评估哪些section受影响，尽量不要出现“旧 section 可能残留过期说法”的问题"。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: PRD line 656 要求 `old_target_body` 真正进入 revise 上下文；PRD lines 442–443 规定内容变化使旧验证失效；PRD lines 895–896 要求 affected set 外正文和路径字节不变。
- Logic: 更新只影响部分证据 -> 需要减少无关 section 变化 -> 用依赖闭包判断受影响范围 -> 只复用可证明安全的 section，避免旧说法残留。
- choice_reason/impact: 页面稳定性和更新安全之间取平衡；影响 revise context、section dependency manifest、content hash、verified invalidation、writeback 和回归测试。
- consequences_and_risks: 需要维护反向依赖和影响诊断；漏记依赖会产生旧内容风险，因此 D-003 规定保守兜底。
- rejected_alternatives: A（每次整页重编）成本和页面抖动较大；C（新旧正文并存）会污染 Reader，且不能证明当前答案。
- unresolved_items/owner: 依赖字段的具体序列化格式属于实现合同，必须在本任务内冻结；owner=Task 2-B。
- Supersedes: none。

### D-003

- question/final_option: 影响范围算不清时怎么办？最终选择 A：扩大到整页重编。
- recommendation/plain_language: 推荐；不确定就多做一点，不能拿旧内容冒险。
- decision: 影响关系不完整、版本/结构关系不确定或归因无法证明时，整页重编；整页重编失败则整页 `degraded`，旧 Reader 正式页不覆盖。
- source_type/reference/exact_excerpt: user_talk / Talk Round 3 / "A"；Grill G-001。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: 项目已有页级 `published/degraded` 与交付级 `not_released`；PRD lines 657–668 要求失败显式降级、旧正式结果不被失败样本覆盖。
- Logic: 影响不确定 -> 不能证明旧 section 安全 -> 整页重编取得一致上下文 -> 重编失败保持 degraded/not_released，避免静默残留或覆盖。
- choice_reason/impact: 把“增量更新”限制在可证明安全的情况；影响 Publication Gate、atomic writeback、失败 manifest 和旧页保护。
- consequences_and_risks: provider 调用和页面变化可能增加；但风险是可见、可回放，不会伪装成成功。
- rejected_alternatives: B（只降级不确定 section）可能留下新旧不一致；C（旧 Reader 永久保留、新结果只进 Audit）会让更新不生效。
- unresolved_items/owner: 影响闭包的具体依赖图和诊断错误码在实现阶段定义；owner=Task 2-B。
- Supersedes: none。

### D-004

- question/final_option: 小语料、抽样蕴含和契约修订怎么受约束？最终选择沿用已冻结合同，不新增临时门。
- recommendation/plain_language: 直接复用 Task 0/Task 1/PRD 已有事实，避免下一阶段重新拍脑袋。
- decision: 使用冻结的 12–20 篇样本和其 source/type/answerability 覆盖记录；抽样蕴含记录固定 seed、样本数、判定阈值、检测器/模型和失败项；Task 2-B 只做机器诊断；在 D-005 修订前 body/section contract revision 为 `0/1`，现已被 D-005 占用，当前为 `1/1`（待用户确认）。只有改变 section 集合、模板、字段或 page type 映射才消耗；D-005 的这次受控修订已耗尽额度。
- source_type/reference/exact_excerpt: PRD lines 432、437、440–442、479、653、657、665、697；Task 0/Task 1 frozen evidence refs in PRD line 574。
- approval_binding: accepted；用户最终决策卡原文“接受”；当前 host-visible acceptance 由 WorkflowHub confirmation 与 interaction aggregate 绑定本决策 hash。
- facts_and_constraints: 样本不能由编译器临时挑选；`sampled_entailment` 是机器 verified 白名单事件；Task 2-C 才是人工读者门；fallback/Jaccard 不能满足 semantic exit。
- Logic: 样本和质量门已有上游冻结事实 -> 不允许 build-spec/实现者重新解释 -> 当前记录边界和来源 -> 后续只实现和回放，不扩大合同。
- choice_reason/impact: 解决 direction review 的四项 minor 缺口，保持任务边界可追溯；影响 sample manifest、semantic run、quality oracle 和 contract revision 记录。
- consequences_and_risks: 当前日志不替代真实样本 manifest、阈值和运行证据；如果上游 manifest 缺失或无法回读，必须 `not_released`，不能用新 fixture 冒充。
- rejected_alternatives: 临时按 page type 自由挑样本、临时降低阈值、把人工读者门前置，都会改变已冻结阶段边界。
- unresolved_items/owner: 实际样本逐项清单、检测器版本和运行预算仍需从冻结 manifest/config 回读并写入 Task 2-B 运行证据；不存在的 inventory 类别必须有 machine fixture 或明确排除理由；owner=Task 2-B，不能由 `build-spec` 补产品决策。
- Supersedes: none。

### D-005

- question/final_option: 冻结来源没有异常处理规则时，`procedure_or_rule.exceptions` 是否必须让整页失败？用户先选 C：保留 section，但明确标记“来源没有说明”，不编造领域事实；随后选 C1：其他 section 通过时，允许该页进入 Reader 和机器通过，但异常专属问题仍记为 `not_answerable`。
- recommendation/plain_language: 推荐 C1；它把“来源没写”与“系统判断没有异常”分开，读者仍能看到有用的步骤/规则内容，同时不让编译器拿别的段落凑异常处理。代价是页面可能通过机器门，但异常问题本身仍没有答案，必须在状态和审计里说清楚。
- decision: `procedure_or_rule.exceptions` 仍是固定 section，不能省略。仅当确定性来源审计证明当前冻结来源没有明确异常触发条件、处理步骤、分支规则或恢复动作时，才写 `source_not_documented`；该状态不是领域 Claim，不填“暂无异常”等正文占位，不从“缺点”“信息不足”或其他主题来源推导异常规则。所有其他必需 section 和现有机器门必须通过后，该页可以标为页级 `published`、进入 Reader 候选并计入 `procedure_or_rule` 覆盖；异常专属问题保持 `not_answerable`，不得宣称异常处理已覆盖。来源存在但表述含糊、审计无法确定、provider 映射失败或归因失败时，不得使用该特殊状态，仍按既有 `degraded`/`not_released` 处理。
- source_type/reference/exact_excerpt: user_talk / make-decision bounded revision / “C”；“C1”。
- approval_binding: pending；本条必须由用户对最终决策卡再次明确接受后，才能替换当前 decision hash 并生成 interaction aggregate。
- facts_and_constraints: 当前真实 T013 来源审计确认 `17 智能搭建` 唯一来源只比较三种方案、优缺点和影响范围，没有异常触发/处理/分支/恢复规则；PRD 原规则要求必需 section 缺证据即 `degraded`，因此本条是唯一一次正文/section contract revision，而不是把现有实现缺陷说成 bug。页级状态仍只有 `published/degraded`，交付级仍保持 `not_released` 规则。
- Logic: 事实确实缺失 -> 继续强行写异常会编造 -> 继续整页失败会丢掉同页已有可用答案 -> 用可审计的 section 状态表达缺口 -> 只对这个可证明的来源缺口放行，其他不确定情况继续 fail-closed。
- choice_reason/impact: 保留真实可读内容，避免“来源没写”被误读为“没有异常”，同时不降低其他 section 的归因、保真、版本、近重复和语义门；影响 `procedure_or_rule` 的 section schema、正文渲染、异常题目的 answerability、Publication Gate、semantic evidence 和审计记录。
- consequences_and_risks: 机器通过不等于异常问题已回答；若来源审计规则过宽，会把 provider 映射失败伪装成来源缺失；若状态没有稳定绑定 source URI、content hash、locator/审计版本，会失去回放能力；若 Reader 文案不清楚，读者可能误以为系统保证没有异常。
- rejected_alternatives: A（保持严格缺证据即 degraded）会让同页其他已证实内容无法进入 Reader；C2（只展示/仍 degraded）不满足用户希望保留可用正文的方向；C3（Reader 可进但不计 page-type 机器覆盖）会让页面状态与语义覆盖统计分裂；把“缺点”或其他主题的异常段落拼进来会制造跨主题 Claim，违反来源边界。
- unresolved_items/owner: `source_not_documented` 的确定性审计算法、状态落盘字段、Reader 显示文案、validator 与 semantic evidence 的序列化由 Task 2-B 的 build-spec/build-plan 冻结；不得改变本条的放行边界；owner=Task 2-B。
- downstream_invariants: 后续规格必须原样保留四条硬约束：不生成“暂无异常”等正文占位；不从“缺点”“信息不足”或其他主题来源推导异常规则；`source_not_documented` 必须绑定 source URI、content hash、可回查 locator（如适用）和审计版本；无法证明来源缺失而只是映射失败、含糊或审计不完整时，仍为 `degraded`/`not_released`。这些是 D-005 的产品边界，不是实现阶段可自由删减的字段建议。
- Supersedes: D-004 仅关于“必需 section 缺证据一律 degraded”的窄规则；D-004 的样本、抽样蕴含、Task 2-C/Task 3 边界和不得临时降门槛的其余部分继续有效。

## Talk 协议和初始队列

本次对话保留用户真实回答，不改写原始话术。第一张 Talk 卡之前已经先向用户展示了问题、用户流程、页面、状态、成功/失败边界、非目标和延期范围；外部调研是否会改变方向也已按 PRD 和 Task 2-A 事实关闭。为满足 WorkflowHub 的可追溯要求，初始候选队列补录如下：

- Q-001（问题/成功标准/调研）：正文不能继续是 Evidence dump；小语料、三类页面、机器门和人工门分工均由 PRD 已回答，无需另造问题。
- Q-002（方向）：正文结构由固定骨架还是 provider 自由生成控制；由 T-001 回答。
- Q-003（范围/取舍）：来源更新采用整页还是 section 增量；由 T-002 回答。
- Q-004（失败风险）：影响关系算不清时的保守边界；由 T-003 回答。
- Q-005（延期事实）：样本、抽样蕴含和 contract revision 复用上游冻结合同；保留为 D-004/OPEN-001/OPEN-002，不临时发明数值。

Round 1 关闭 Q-001 的事实/调研轴；Round 2 收敛方向、范围和取舍；Round 3 收敛影响不确定、盲审风险和剩余延期项。原对话中的“第 1/2/3 轮”是面向用户的卡片编号，下面按 WorkflowHub 职责补齐映射；不把没有发生的用户回答写成发生过。

## 三轮 talk

| talk_id | 问题/选项 | 后果/风险 | 用户选择/原文 | 队列变化 | source/evidence |
| --- | --- | --- | --- | --- | --- |
| T-001 | Round 2 方向轴：正文采用固定骨架+受控 section、完整 PageDraft、还是纯规则拼接？ | A 稳定可验但更模板化；B 更自然但漏字段/截断风险；C 安全但不能语义 exit。 | A；用户原文："A" | Q-002 关闭；Q-003 重新成为最高未决轴。 | Talk Round 2；PRD 653–655 |
| T-002 | Round 2 范围/取舍轴：来源更新时整页重编、受影响 section 增量重编、还是新旧并存？ | A 干净但抖动；B 稳定但必须识别影响；C Reader 会混乱且更新不生效。 | B；用户原文："我想选B，但是需要注意，虽然只改受影响的section，但是需要评估哪些section受影响，尽量不要出现“旧 section 可能残留过期说法”的问题" | Q-003 关闭；Q-004 成为最高未决轴。 | Talk Round 2 |
| T-003 | Round 3 风险轴：影响范围算不清时整页重编、只降级 section、还是旧页留在 Reader？ | A 最安全但成本高；B 可能新旧不一致；C 更新不生效。 | A；用户原文："A" | Q-004 关闭；Grill/review 后无新的 high/medium 用户问题，剩余项显式进入 OPEN/RISK。 | Talk Round 3；Grill G-001 |

### 本轮规则修订 Talk（仍属于 make-decision）

本轮不是跳到下一阶段，而是针对真实来源缺口回到当前 make-decision，修订一次正文 contract。用户回答只记录原文，不把解释性文字伪装成用户回答。

| talk_id | 问题/选项 | 后果/风险 | 用户选择/原文 | 队列变化 | source/evidence |
| --- | --- | --- | --- | --- | --- |
| T-004 | `procedure_or_rule.exceptions` 没有来源证据时：A 继续整页失败；B 让它变成可选；C 保留 section 并标记来源未说明，不编造事实。 | A 丢掉同页已有可用内容；B 会掩盖结构缺口；C 需要稳定状态和审计，否则可能被误解成“没有异常”。 | C；用户原文："C" | 进入状态/机器门的第二个问题。 | make-decision Talk revision |
| T-005 | 选择 C 后，该页能否进入 Reader/机器通过：C1 其他 section 通过即可，但异常题仍 `not_answerable`；C2 只展示并保持 degraded；C3 Reader 可进但不计 page-type 机器覆盖。 | C1 保留可用内容但机器通过不代表异常已回答；C2 最保守但会丢掉同页答案；C3 会让覆盖统计和页面状态分裂。 | C1；用户原文："C1" | 方向改变问题关闭；待最终决策卡确认。 | make-decision Talk revision |

当前修订后的 clarify：`open_direction_changing_questions=0`；仍需用户对完整最终决策卡明确接受，才能完成本阶段确认绑定。

## 调研

| research_id/source | 调研重点 | 关键事实 | 处理状态 | 关联 D |
| --- | --- | --- | --- | --- |
| F-001 / PRD + Task 2-A archive | 是否需要外部调研改变方向？ | PRD 已冻结三类 page type、12–20 样本、失败状态、一次 contract revision、Task 2-C/3 延期边界；Task 2-A 已冻结 Reader Bundle contract。 | 跳过外部调研：没有发现会改变本轮方向的未知外部事实；实现阶段仍需核实真实 provider/model 和样本 manifest。 | D-001–D-004 |
| F-002 / `CONTEXT.md` + current main | 术语和现有边界是否冲突？ | Claim、fragment_locator、Reader/Audit、`published/degraded/not_released` 和信号失效已有唯一解释；本决定新增的“影响闭包”是 Task 2-B 实现术语。 | 已核对；无术语冲突。 | D-002–D-003 |
| F-003 / 冻结 Task 1 source audit + T013 v23 | `17 智能搭建` 只有一个来源，内容是三种方案的优缺点/影响范围，没有异常触发、处理、分支或恢复规则；不能跨主题拼接其他 GoInsight 文档。 | 继续按旧规则会让 procedure 页整体 degraded；放宽成“可选”又会隐藏固定 section 缺口。 | 已核对；事实支持只增加 `source_not_documented` 特殊 section 状态，不增加领域 Claim。外部调研跳过：外部事实不会改变这条本地来源边界。 | D-005 |

## grill

| grill_id | CONTEXT/冲突 | 结论 | ADR/四项退出 | source/evidence |
| --- | --- | --- | --- | --- |
| G-001 | B 的增量复用若没有 section 依赖闭包，会把旧正文、旧版本或旧归因残留到当前页面；provider 若新增无来源事实，也会绕过 claim 回查。 | 每个 section 维护依赖集合；只复用可证明未受影响的 section；影响不确定就整页重编；整页失败则 `degraded` 且旧正式页不覆盖；provider 只能在受控 section 内生成并接受 claim/source gate。 | `CONTEXT.md`: no-change；ADR: created，见 `docs/adr/0005-task2b-controlled-section-recompile.md`；hard to reverse=是，surprising without context=是，genuine trade-off=是；四项退出：上下文一致=通过，owner/接口一致=通过，失败语义明确=通过，范围/延期明确=通过。 | Grill-with-docs；`CONTEXT.md`；ADR-0005；PRD 432、443、668 |
| G-002 | C1 可能把“来源没有记录”误当成“异常不存在”，也可能让 provider 映射失败借特殊状态绕过门禁；同时现有 PRD 禁止通用“来源未说明”占位句。 | 只有确定性 source audit 命中完整的“无异常规则证据”条件时才允许 `source_not_documented`；状态绑定来源指纹和审计版本；异常题保持 `not_answerable`；所有其他缺口仍 `degraded`。这是一项 section contract revision，需消耗 `1/1`，不降低其它语义底线。 | `CONTEXT.md`: update，补充“来源未说明”与“没有异常”的区别；ADR: created，见 `docs/adr/0006-procedure-source-not-documented.md`；hard to reverse=是，surprising without context=是，genuine trade-off=是；四项退出：上下文一致=通过，owner/接口一致=通过，失败语义明确=通过，范围/延期明确=通过。 | Grill-with-docs；`CONTEXT.md`；ADR-0006；PRD 655、663、665、688；T013 v23 来源审计 |

## 审查处置

| finding_id | 原始事实/来源 | 后果 | status | next_action/evidence_ref | owner/consumer/retain_or_delete |
| --- | --- | --- | --- | --- | --- |
| F-1443ba03dc96 | detail review：Grill 三项 ADR 条件均为“是”，但记录成 `not-needed`。 | 决策日志内部矛盾，后续无法知道是否应保留该取舍。 | fixed | 已创建 `docs/adr/0005-task2b-controlled-section-recompile.md`，并将 G-001 改为 `ADR: created`。 | owner=make-decision；consumer=Task 2-B；retain=保留 |
| F-1bee0c33c4b0 | detail review：三轮 Talk 的职责和初始队列未按合同呈现。 | 审查者无法确认问题/方向/风险分别收敛。 | fixed | 补录初始候选队列和 Round 1/2/3 职责映射；保留原始用户回答，不伪造回答。 | owner=make-decision；consumer=interaction aggregate；retain=保留 |
| F-5f436ba75403 | direction review：原始材料没有完整页面清单、状态枚举和 Task 2-A 交接项。 | 后续可能漏边界或重复验收。 | fixed | 已在本文「流程与边界」「延期交接」和 R-005 补齐；保留 review ref。 | owner=make-decision；consumer=build-spec/Task 2-B；retain=保留 |
| F-7a9cd9f799fd | direction review：小语料构成未在 review packet 展开。 | 可能由后续阶段临时挑样本。 | fixed | D-004 固定 12–20 篇和上游 sample coverage manifest；实际逐项清单仍须回读，不能新选。 | owner=Task 2-B；consumer=sample runner；retain=保留 |
| F-df4dceaac28b | direction review：抽样蕴含的抽样、判定和通过边界未在 packet 展开。 | 可能被重新解释为人工门或任意阈值。 | fixed | D-004 固定 seed、样本数、阈值、检测器/模型和失败项；当前只作机器诊断，详细运行值进入语义 evidence。 | owner=Task 2-B；consumer=Publication Gate/Task 2-C；retain=保留 |
| F-e9f77d51ff71 | direction review：一次 contract revision 的触发条件未写清。 | 可能静默消耗唯一修订额度。 | fixed | D-004 记录当前 `0/1` 和四类触发条件；行为 bug 不消耗。 | owner=Task 2-B；consumer=Task 2-C；retain=保留 |
| F-90de7ffefcfa | detail review：验收草案漏写“inventory 不存在的类别要有 machine fixture 或排除理由”。 | 覆盖门不够可判定。 | fixed | 已在成功边界、D-004 和本文「机器验收底线」中补上；后续验收草案必须逐字承载。 | owner=Task 2-B；consumer=semantic exit；retain=保留 |
| F-b41db5c6e091 | 当前快照 detail review：临时验收草案漏掉 `>=6`、缺类 fixture/排除理由和至少一次真实语义运行，低于已批准成功线。 | 下游可能在不足 6 个 concept、没有真实语义运行或未处理缺类时放行。 | fixed | 已将三条不可下调机器底线写入本文；后续 draft/spec 只能展开验证方法，不能降低门槛；保留当前 review ref。 | owner=make-decision；consumer=build-spec/Task 2-B semantic exit；retain=保留 |
| F-bbc7ad467844 | detail review：当前没有实现运行 evidence。 | 不能把决策阶段材料说成语义运行通过。 | accepted_risk | 这是阶段边界；实际 sample/semantic evidence 延期到 Task 2-B 运行，缺失时保持 `not_released`。 | owner=Task 2-B；consumer=semantic exit；retain=保留 |
| F-db15fea821ac | detail review：审查时最终确认仍是 pending。 | 用户若修改决定，当前材料必须重算。 | accepted_risk | 用户已接受；当前决策 hash 由 WorkflowHub confirmation 与 interaction aggregate 重新绑定。 | owner=make-decision；consumer=downstream stages；retain=保留 |
| F-e0e6107b0b27 | detail review：provider packet 无法独立验证跨仓 PRD 行号。 | review 不能把外部引用当作 packet 内证据。 | accepted_risk | 保留精确来源作为 provenance；不把 provider 未核验说成 provider 已核验，后续仍以当前仓库 PRD 为准。 | owner=downstream stage；consumer=build-spec；retain=保留 |
| REVIEW-DETAIL-RECHECK | 当前 decision-log 修订后的 detail review：`pass`；1 个异源 provider 返回有效结果，另 1 个 provider 返回 `OUTPUT_INVALID`，未把它冒充为通过。 | 当前材料已有一份真实独立 review 事实；用户确认后只需绑定当前 decision hash，不重复调用未变材料。 | fixed | 保留 attempt/result/report refs；由当前 confirmation 与 interaction aggregate 绑定当前决策。 | owner=make-decision；consumer=interaction aggregate；retain=保留 |
| F-43b46fcb7dbe | 本轮 detail review：验收草案没有逐字承载“不生成正文占位、不跨主题推导异常、状态绑定来源指纹和审计版本”三条防滥用边界。 | 下游可能把 provider 映射失败或占位文本伪装成 `source_not_documented`。 | fixed | 已在 D-005 增加 `downstream_invariants`，明确这些是产品边界；后续 spec/plan 必须原样继承；保留本轮 review report/ref，不重复审查。 | owner=make-decision；consumer=build-spec/build-plan；retain=保留 |
| F-7b63034233e7 | 本轮 detail review：D-004 的 contract revision 字段仍写 `0/1`，与当前 `1/1` 冲突。 | 下游可能误以为还剩一次修订额度。 | fixed | 已回写 D-004 为“D-005 前为 `0/1`，现已占用，当前 `1/1`（待用户确认）”；保留本轮 review report/ref，不重复审查。 | owner=make-decision；consumer=build-spec/build-plan；retain=保留 |
| REVIEW-DETAIL-C1-20260811 | 当前 C1 修订的唯一异源审查：`status=available`、`terminal_status=semantic`；有效异源 reviewer 为 `opencode/v4flash`，发现 2 个 minor，均已 fixed。`antigravity/flash` 为 `AUTHENTICATION_FAILED`，`codex/luna` 为 `SAME_SOURCE`，均按真实传输事实保留。 | 这是一份当前材料的独立质量建议，不是“所有 provider 通过”，也不要求重复审查。 | fixed | attempt=`quality/reviews/attempts/8c6c7df8-7f3d-48d2-8d40-69c489761bd9/attempt.json`；result=`quality/reviews/results/make-decision-detail-95828981cdf945f76518b0fa65fb9ccb50f093a9-8c6c7df8-7f3d-48d2-8d40-69c489761bd9.json`；report=`quality/reviews/reports/8c6c7df8-7f3d-48d2-8d40-69c489761bd9.md`；本轮后不重复。 | owner=make-decision；consumer=当前确认/interaction aggregate；retain=保留 |

## 历史确认（D-001–D-004）

- 状态：accepted
- 用户原文与 host-visible 绑定：用户最终决策卡原文“接受”；WorkflowHub confirmation 与 interaction aggregate 绑定当前 decision-log 的快照、引用和 hash。
- 未确认内容：无。OPEN-001–OPEN-003 仍是已明确延期的实现项，不是本次方向确认的缺口。

## 当前最终确认（D-005）

- 状态：pending；用户已选择 C、C1，但尚未对包含 Grill、审查事实和交接边界的完整当前决策卡再次回复“接受”。
- 当前确认范围：仅确认 `source_not_documented` 的产品方向；不提前确认具体字段名以外的实现算法、测试步骤或语义运行结果。
- interaction aggregate：待当前决策确认后，按当前四份材料和 decision hash 只生成一次；在此之前不得声称 make-decision 完成或进入 build-spec。

## 拒绝方案

| 选项 | 拒绝理由 | 关联 D |
| --- | --- | --- |
| provider 自由生成完整 PageDraft | 容易漏必需 section、增加无来源断言和截断风险 | D-001 |
| 每次来源变化都整页重编 | 页面抖动和 provider 成本较高，未充分利用未受影响 section | D-002 |
| 新旧正文并存或只把结果放 Audit | Reader 会混入过期答案，更新不真正生效 | D-002–D-003 |
| 影响不确定时只降级单个 section | 可能留下新旧 section 不一致 | D-003 |
| 临时挑样本、临时降低阈值、用 Jaccard 代替语义 exit | 违反上游冻结事实和 Task 2-B 语义边界 | D-004 |
| 把 `exceptions` 变成可选或把“缺点”改写成异常 | 隐藏固定问题或制造无来源 Claim | D-005 |
| 只展示并保持整页 degraded | 最安全，但会丢掉同页其他已经证实的可用答案 | D-005 |
| Reader 可进但不计 `procedure_or_rule` 覆盖 | 页面状态与机器覆盖统计不一致，无法形成完整样本闭环 | D-005 |

## 风险与延期交接

| risk/deferred_id | 风险或延期内容 | 触发/后果 | 处理阶段/owner |
| --- | --- | --- | --- |
| RISK-001 | section 依赖登记不完整 | 可能误复用旧正文；触发时扩大整页重编，失败则 degraded | Task 2-B / compiler + gate |
| RISK-002 | provider 生成无来源事实或截断 | 机器门拒绝，页不进 Reader；保留 Audit/Archive | Task 2-B / publication gate |
| RISK-003 | 上游 sample coverage 或实际运行 manifest 无法回读 | 不得用新 fixture 冒充，语义 exit 保持 `not_released` | Task 2-B / run evidence |
| RISK-004 | `source_not_documented` 审计过宽或 Reader 文案含糊 | 可能把“来源没写”误读成“没有异常”，或让 provider 映射失败绕过门禁 | Task 2-B / spec + compiler + gate |
| DEFER-001 | 人工读者质量门、3 个负向题、人工信号 | 本阶段不声称 reader quality | Task 2-C |
| DEFER-002 | 完整 17+3 题集、全量 89 篇、正式 released | 本阶段只做样本和机器诊断 | Task 3 |
| DEFER-003 | 文档同步、清理和归档 | 不重新打开前面任务的业务决策 | Task 3-Closeout |

## 质量边界

- 质量事实：当前有 PRD/Task 2-A 合同、三轮 Talk、规则修订 Talk、Grill、旧 direction/detail review 事实，以及 C1 修订后的唯一异源 detail review；C1 review 有 1 个有效异源 reviewer、2 个 minor finding，均已修正，并保留 `AUTHENTICATION_FAILED` 与 `SAME_SOURCE` 传输事实。任何这些事实都不等于代码已实现或语义 exit 已通过。
- 推进资格：本阶段只在用户接受当前 decision card 后生成 interaction aggregate；之后下游只能把决定转成规格/计划，不能重新发明方向。
- 完成判据：Talk/Clarify resolved、必要调研有跳过理由、Grill 完成、decision-log 当前、review findings 有处置、用户明确接受、content-addressed aggregate 写入并绑定当前 decision hash。
- 不可逆授权边界：当前不写实现、不提交代码、不合并、不发布；Task 2-B semantic exit 仍必须在实现后单独验证。

## 未决项

| item_id | 未决内容 | 原因 | 谁在何时解决 |
| --- | --- | --- | --- |
| OPEN-001 | 冻结 sample coverage manifest 的逐项 source/topic/page-type 清单和实际篇数分布 | 本文只固定上游来源和 12–20 范围，不重新选择样本 | Task 2-B 进入 build-plan/build-code 前回读，不由 build-spec 发明 |
| OPEN-002 | 具体 sampled-entailment detector/version/threshold/run budget | PRD 固定必须记录这些字段，但当前阶段不伪造运行值 | Task 2-B semantic run 前冻结并写 manifest |
| OPEN-003 | 各 page type 的具体 section 依赖字段序列化 | 这是实现合同，不改变当前方向 | Task 2-B specification/implementation |
| OPEN-004 | `source_not_documented` 的确定性审计输入、证据结构、状态投影和 Reader 文案 | 当前只冻结放行边界，不在 make-decision 发明实现字段；必须防止把映射失败伪装成来源缺失 | Task 2-B build-spec/build-plan；不能降低 D-005 |

## Supersedes

- D-004 的“必需 section 缺证据一律 degraded”仅在 `procedure_or_rule.exceptions` 的 D-005 特殊状态范围内被窄化；D-004 的样本、抽样蕴含、Task 2-C/Task 3 边界和不得临时降门槛的其余部分继续有效。Task 2-A 的 Reader Bundle contract 继续有效；本任务已使用 PRD 允许的一次正文/section contract revision，当前为 `1/1`，待用户确认。

## 文档结果

- CONTEXT.md：updated；新增 `source_not_documented` 的唯一解释，明确它不是“没有异常”、不生成 Claim，且只适用于 `procedure_or_rule.exceptions`。
- ADR：created；`docs/adr/0005-task2b-controlled-section-recompile.md` 记录 section 增量更新和整页保守兜底；`docs/adr/0006-procedure-source-not-documented.md` 记录本轮唯一的来源缺口放行规则；两份状态均为 proposed，最终接受绑定仍由本阶段决定。
- ADR criteria：hard to reverse=是；surprising without context=是；genuine trade-off=是；三项均成立，因此已创建 ADR。
- 术语/ADR 冲突及处理：旧 PRD/决策曾禁止“来源未说明”正文占位，本轮没有把它写成正文占位，而是新增 section 状态并明确不生成 Claim；Task 2-A 的结构合同与本任务的正文更新策略正交，旧 Reader/Audit 分离 ADR 继续适用。
- 不复制 spec 的边界：本文只保留需求索引、决策理由、边界、风险和交接；页面字段、测试步骤和实现任务留给后续正式规格/计划。

## Exit checks

- 上下文一致：通过；与 `CONTEXT.md`、PRD v1.7 和 Task 2-A Reader Bundle contract 一致。
- owner/接口一致：通过；Task 2-B 负责正文编译和机器门，Task 2-C 负责人工读者门，Task 3 负责全量和 released。
- 失败语义明确：通过；不确定影响整页重编，失败 degraded，旧 formal 不覆盖，整包 not_released。
- 范围与延期明确：通过；全量、人工门、正式 release、数据库/图谱和永久人工系统均明确延期或不做。
- 当前修订确认：待用户确认 D-005；确认前不生成 interaction aggregate，不进入 build-spec。

## Scope revision：SR-20260811-task2b-procedure-source-gap

- **状态**：`in_progress`；沿用当前 task，不创建 successor task、不重跑完整五阶段、不改写历史 receipt。
- **触发阶段 / 返回阶段**：`verify-code` → 受影响的 `build-code`。原因是这次新增的是已实现正文合同的产品行为，既影响 spec/plan/tasks，也影响 compiler、validator、测试和语义出口；不从头回到 Task 2-A 或重新规划无关内容。
- **原始需求**：Task 2-B 要让三类主题页正文可读、可回查、失败明确降级，并避免来源更新后旧 section 残留过期说法。
- **为什么现在修订**：T013 v23 的真实来源审计证明 `procedure_or_rule.exceptions` 的缺口来自冻结材料本身，不是 provider mapping bug；继续强行填异常会编造事实，继续整页失败又会丢掉同页已有可用内容。
- **本次新增方向**：沿用 D-005/C1：固定保留 `exceptions` section；仅在确定性来源审计证明来源没有异常触发、处理、分支或恢复规则时使用 `source_not_documented`；不生成 Claim、不写占位句、不跨主题推导；异常题保持 `not_answerable`；其他 section 和现有机器底线通过时，页面可进入 Reader/机器覆盖统计；含糊、审计不完整、provider 映射或归因失败仍 `degraded/not_released`。
- **受影响 ID**：`PFACT-007`、`R-004`、`D-004`、`D-005`、`FR-DRAFT-001`、`FR-DRAFT-004`、`FR-PUBLISH-002`、`FR-PUBLISH-003`、`FR-PUBLISH-006`、`FR-SEM-003`、`AC-02`、`AC-07`、`AC-09`、`AC-11`、`AC-12`、`AC-13`、`T009`、`T010`、`T013`、`T014`、`T015`、`T016`。
- **影响评估**：用户流程增加“来源审计 → exceptions 特殊状态/失败”的分支；数据状态增加 section-level `source_not_documented` 与题目 `not_answerable` 的组合；成功边界只放宽这一来源缺口，不降低 `>=6`、三类 page type、归因、保真、版本、重复和交付 `not_released` 门；失败边界继续 fail-closed；实现/测试/审查/交付都必须绑定来源 URI、content hash、locator（如适用）和审计版本。
- **四份材料变更**：`decision-log.md` 追加本记录并保留 Talk/Grill/审查原始事实；`spec.md` 只补受影响的场景、状态、FR、AC、风险和 revision note；`plan.md` 只补受影响设计、测试、返回阶段和 traceability；`tasks.md` 只追加受影响的 T015/T016 执行、测试和证据卡，不重开 T001–T014。
- **非目标与延期**：不新增 page type、Reader Bundle、CLI、provider、数据库、人工读者门、Task 3 released 或新的永久状态机；完整样本覆盖、真实语义出口和人工确认继续按原有边界记录，不因本修订伪造通过。
- **沟通事实**：Talk/Clarify/Grill 由主代理完成；用户原始选择为 `C`、`C1`，本次用户指令为“请用scope_revision流程增加需求，不要从头开始！”。不把 review verdict 或实现结果当作用户确认。
- **宪法检查**：同一 task、四份材料一致、只改受影响范围、旧事实只读保留、失败不伪造成功、不新增控制面、不泄露凭据；均保持。
- **审查状态**：当前 main 的 `wh-review` 明确不再接受 `materials.scope_revision`，旧专用 route 已被移除；不能伪造专用 review。现有 C1 detail review 只作为相邻质量事实，不冒充 scope_revision review；专用审查缺失继续记录为 `incomplete/unavailable`，不阻止同 task 材料修订，但不能声称 scope revision 已正式闭合。
- **返回交接**：材料修订完成后回到 `build-code`，只执行 T015 的受影响 `procedure_or_rule.exceptions` 状态、gate、测试，再由 T016 更新 T013/T014 证据；不重跑已完成的无关卡片，不调用 `close`。

---

# mini-task decision-log：Reader 质量整合

## 原始需求

基于 `/Users/Hugh/Downloads/confluence 原始数据` 再次运行 KnowledgeDigest，并与 `/Users/Hugh/Hugh/Knowledge/CompanyBrain` 对比。当前结果只有约 5 分：产品和原则平铺、没有产品/模块索引和边界、Reader 暴露哈希及内部字符串、正文像原始资料堆放。目标是至少 80 分，且人工只看一页汇总，不逐页、逐题、逐来源链验收。

## 关键事实

- 当前 Task3 已有 Reader Bundle、Audit/Archive、17+3 自动题集和一页汇总确认合同，但真实候选仍缺产品 overview、来源级完整落点和干净 Reader。
- 真实输入有 89 条可读资料，顶层目录可识别为 `GoInsight`、`emm for android`、`emm for ios`、`merchant system`，这是当前最可靠的产品归属事实。
- CompanyBrain 的可读性来自产品目录、产品总览、模块索引、场景/经验/规范分层；哈希和审计字段不在日常正文。
- 哈希、topic id、指纹和运行证据必须保留，但应只放 Audit。`released/not_released` 是整包交付状态，不是正文状态。

## 选择与理由

本 mini-task 只做一个结果：把 Task3 真实发布入口接到 Reader 编译器，输出“产品→模块→知识页”的 Reader Bundle，并把审计元数据移到 Audit。

1. 每条有效来源保留一个知识页，避免聚类/降级后消失。
2. 产品按来源顶层目录确定；无法确定时落入 `unclassified/general`，页面标 `degraded`，原因进 Audit，不让来源消失。模块优先用冻结 TopicIndex，缺失时用清理后的标题/文件名并标 `inferred`，不伪造产品边界。
3. 每个产品生成 `index.md`、`overview.md`、`modules/index.md`；每个模块生成 `index.md`，知识页放 `knowledge/`。
4. Reader 只放标题、摘要、正文、导航和简短来源入口；id、hash、fingerprint、生成器、验证事件和配置只放 Audit。
5. 正文做保真清理和重排：删除 frontmatter、内部字段、哈希脚注、重复 H1 和空段，保留事实、表格、代码和链接；不把清理冒充模型归纳。
6. 有合法语义候选时优先使用候选正文；没有时可以生成保真整理 candidate，但报告必须标明 semantic unavailable/degraded。
7. 发布仍默认 `not_released`；既有质量门、汇总确认和 readback 全通过才可改变整包状态。

## 风险与延期

- 同一产品的大小写/空格变体统一 slug，但保留显示名并记录归并。
- 文件名推断模块可能过度分类，标 `inferred`，不生成虚假边界结论。
- 清理只删除明确内部元数据，逐页保留来源入口、行数和链接检查。
- 逐条模型重写、经验/规范/场景本体、人工产品边界词表、CompanyBrain 修改延期；merge/push/archive/cleanup 交给 Closeout。

## 设计审查处理

- **已修复**：无法归属来源现在有 `unclassified/general` 兜底落点；超 300 行页面拆成带上一页/下一页链接的知识片段，不截断、不让来源消失。
- **已补齐**：80 分改成可复算的代理分：结构 20、来源覆盖 20、产品入口 15、Reader 清洁 15、内容保真 20、溯源入口 10；达到 80 只表示本 mini-task 的机器代理门通过，不等于人工宣称与 CompanyBrain 等质。
- **已补齐**：冻结最小接口：source manifest 使用 `source_id/source_uri/relative_path/title/content_fingerprint/line_count/validation_status`；语义候选使用 `source_uri/content_fingerprint/title/summary/body/module/semantic_status`；Audit 映射使用 `source_id/reader_paths/product/module/mapping_reason/content_fingerprint/semantic_status`。
- **实现修正**：真实对比确认仅有“产品→模块”仍不足以承接 CompanyBrain 的阅读方式，因此增加产品下的知识类型投影（产品定位与边界、模块手册、技术实现、经验与坑、规范与资产）。它只生成索引并链接唯一知识页，不新增事实、不复制正文。
- **不采纳但记录**：审查包里的 `planning_artifacts.json` 是 wh-review 生成的过程元数据，不是项目四份材料；其 null/pending 不改变本 mini-task 的冻结材料，正式结果以四份材料和审查回执为准。
