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

把 89 条 Confluence 原始资料消化成简洁、可读、可回查的知识包：不添外部知识、不漏资料、不串产品；读者先按问题和场景进入，再按产品、模块、对象、场景、边界和五类页面类型找到业务答案。

## 目标

实现真实 qwen3.8 与 jina-embeddings 参与的 Reader/Audit 闭环，并证明五项质量逐场景严格高于 CompanyBrain；实现、来源、质量和发布证据全部闭合后才允许完成发布。

## 范围

必须覆盖垂直切片和 89 条全量，包含 GoInsight、EMM for Android、EMM for iOS、Merchant System 四个产品。流程是：读取 raw → 固定来源和产品归属 → 垂直切片 → 89 条全量 → 写入 `/Users/Hugh/Downloads` → Home 按问题/场景路由 → Reader 阅读 → Audit 回查 → 五项逐格对比 → 全部门禁通过后发布。

## 用户流程与边界

- 成功：89 条进入来源审计闭包，四产品归属正确，Reader 可读，Audit 可回查，真实 provider 可核验，所有适用质量行均为 `KD_WIN`。
- 失败：来源缺失、产品串线、正文不可读、证据不可回查、provider 未调用/失败、五项有未知/缺行/非 `KD_WIN`，只能保持 `not_released` 或 `blocked`。
- 空白原始页只留 Audit，不凭空补正文。

## 非目标

不读取或补充外部知识；不改 raw 或 CompanyBrain；不新增任务；不恢复 `modules`、`boundaries`、`knowledge`、`audit` 公共目录；不把数据库、向量库、调度器或 agentmemory 变成正式功能；不以文件数、平均分、旧候选、旧 review 或绿测试冒充通过。

## 决定

采用唯一生产链：`digest CLI → compiler.digest → providers(qwen3.8/jina-embeddings) → quality.py → publisher.commit`。公开结果只保留 `bundle/README.md`、`Home.md`、`products/<product>/<page_type>/*.md`、`Audit.md` 和 `_audit` 机器证据。设计 terminal-clean 仅作 advisory；implementation review、M401/M401-R/M402 和五项真实质量仍是硬门。

## 需求→决定

| 原始需求类别 | 当前决定与证据 | 状态 |
| --- | --- | --- |
| goal | 89 条、四产品、五项逐场景严格胜出；见「目标」和 `spec.md` | covered |
| flow_or_surface | 垂直切片→全量→Downloads bundle→Home→Reader/Audit；见「范围」 | covered |
| data_or_state | 只读 raw，保留来源闭包、归属、provider 和发布状态；见 `plan.md` | covered |
| success_failure_acceptance | 适用行全 `KD_WIN`，缺失/未知/失败 fail-closed；见「验收标准」 | covered |
| constraint_non_goal_defer | qwen3.8、config.json、无外部知识、无新增任务、未完成不 released；见「非目标」 | covered |

## 验收标准

可验证条件：场景是 raw-only 垂直切片和 89 条全量；数据来源是 `/Users/Hugh/Downloads/confluence 原始数据`、当前 CompanyBrain 快照和 `/Users/Hugh/.config/knowledge-digest/config.json`；通过是来源、归属、真实 qwen3.8/Jina、Reader/Audit 和五项逐格全闭合且适用行全 `KD_WIN`；失败是任一身份、调用、审查、矩阵或发布证据不闭合，结果为 `not_released`/`blocked`。

## 风险与延期交接

当前未决：implementation review 尚无可用语义结果，M401-R、M402 和 released 尚未成立。下一步只重新生成当前 snapshot/material 绑定的实现证据，再依次闭合 M401、M401-R、M402；review/provider 不可用就原样记录并保持 `not_released`。

## 三轮 talk

旧复杂目录会继续造成入口和归属混乱，拒绝；只做离线脚本整理没有真实语义生成和质量保证，拒绝；采用单一生产链、真实 provider、简洁 Reader 和可回查 Audit，代价是门禁更严格，采用。

## 调研

已核对当前工作树、WorkflowHub 材料、raw 89 条、CompanyBrain、qwen3.8/Jina 配置约定和真实候选；当前 active section 是唯一执行口径，历史只作回查。

## grill

五项不能由平均分推出；真实运行不能替代实现审查；来源闭包不能由 Reader 文件数推出；简洁目录不能牺牲 Audit。当前方案保留这四条限制。

## 审查处置

设计 terminal-clean 降为 advisory；当前 implementation review 无语义结果，未把超时、旧 review 或静态 JSON 当通过。下一轮只接受绑定当前材料的 authenticated 结果。

## 最终确认

用户最近的“继续”只表示继续执行，不等于发布确认；实现审查、M401-R、M402 和五项真实结果闭合前，最终发布确认未完成。

## 拒绝方案

拒绝旧 V37/V50 临时目录、无 LLM 离线整理、复杂公共目录、跨产品猜测、静态对照和用平均分替代逐场景比较。

## 未决项

当前 implementation review、M401 packet、M401-R receipt、M402 真实 run receipt 和最终发布状态仍未闭合；不以伪造证据解决。

## Supersedes

本 active section 取代 archive 后的旧 Task2/Task3/Task4 口径；D-163 取代旧 qwen3.6 和设计 terminal-clean 硬阻断；D-164 至 D-167 取代旧实现和证据身份口径。

## 文档结果

当前四份 WorkflowHub 材料已对齐 Task5 v4.7；archive 后内容只作历史回查，不参与当前判断。

## Exit checks

当前只确认材料和部分真实质量事实；实现审查、M401-R、M402 未完成，状态仍为 `release_pending/not_released`，不能宣布 `released` 或 `close`。

## UI applicability

```json
{
  "result": "non_ui",
  "sources": {
    "raw_requirement": {"result": "non_ui", "description": "交付本地 Markdown 知识包和 CLI 结果，不改页面或前端交互"},
    "project_inventory": {"result": "non_ui", "description": "项目范围是本地知识消化、质量和文件发布"},
    "planned_or_changed_frontend_fact": {"result": "non_ui", "description": "没有计划或变更 frontend component、page、interaction 或 browser surface"}
  },
  "reason": "请求只改变知识消化管线和 Markdown 产物，不改变 UI",
  "handoff": "make-decision 已记录；不适用浏览器页面验收"
}
```

## 收敛检查

| 维度 | 用户答案 | 事实/材料 | 可执行验收 |
| --- | --- | --- | --- |
| 目标 | 用户已确认继续当前目标；取舍：质量优先于快速 close；被拒方案：只整理文件；未决项：正式门禁未闭合 | `decision-log.md`「原始需求」「目标」 | 场景：89 条全量；数据来源：raw；通过：四产品和五项闭合；失败：任一缺失不发布 |
| 范围 | 用户已确认垂直切片和 89 条全量；取舍：一次闭合全量；被拒方案：拆后续任务；未决项：无范围新增 | `decision-log.md`「范围」 | 场景：四产品；数据来源：raw；通过：89 条入闭包；失败：漏条或串产品 |
| 方案 | 用户已确认继续单一生产链；取舍：真实 provider 换质量可证；被拒方案：离线规则冒充 LLM；未决项：implementation review/M401-R/M402 | `spec.md` v4.7、`plan.md` M401/M402 | 场景：真实运行；数据来源：config.json；通过：qwen3.8/Jina、Reader/Audit、五项全胜；失败：任一调用或身份不可证 |
| 验收 | 用户已确认五项必须全部高于 CompanyBrain；取舍：不接受平均分；被拒方案：机械总分；未决项：正式 M402 未闭合 | `tasks.md` M402 | 场景：projection×dimension；数据来源：raw/CompanyBrain；通过：适用行全 `KD_WIN`；失败：缺行、未胜出或证据不闭合 |

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

## ARCHIVE-NON-ACTIVE: 历史决策记录（非生效）

## D-109：收敛 v45 审查暴露的合同歧义（2026-09-02）

### 原始需求

同一 Task5 必须完成切片和 89 条全量；Reader 入口按问题/场景路由，分类按产品/模块/对象/场景/边界，正文按业务答案，页面按定位/概念/操作/诊断/经验，Reader 可见且 Audit 可回查；五项必须逐 case 高于 CompanyBrain 才能 released/close。

### 关键事实

v45 两路独立审查仍为 `revise`。有效缺口集中在公共 snapshot schema/identity 双名、跨产品 `shared` 规则、page surface 到 route/evidence 的选取规则、Audit 锚点、source manifest/observation schema、C0 22 文件清单、M401 run-root、ROOT-CAUSE 路径边界、Qwen local/global 失败和 host-only receipt 未定义。

### 选择与理由

唯一 public snapshot schema 改为 `knowledge-digest-companybrain-route-snapshot.v1`，唯一身份字段为 `companybrain_snapshot_id`；明确 shared 只代表跨产品 selected closure；固定八类 render surface 和 page/route 的首个 evidence binding 规则；Audit 使用 `Audit.md#evidence-<evidence_id>`；定义 89-row source manifest 与 observation row canonical hash；列出 C0 的 1+17+4 清单；M401 产生隔离 bundle，M401-R 只审查；ROOT-CAUSE 独立 receipt；host path 只进 authenticated host-only receipt；Qwen 按 local/global 失败分类。

这些修改没有增加用户功能，而是把已确认的质量目标改成唯一可执行、可重算、可回查的合同；在设计审查通过前不进入 M401。

### 延期交接

v46 设计审查若仍有 finding，只修当前 active contract 和对应实现/测试；不得调用真实 provider。设计通过后才执行 authenticated DESIGN-CURRENT → M401 → M401-R → M402。

## D-110：v53 设计修复的唯一解释（2026-09-02）

### 关键事实

v51 仍为 `revise`，不是设计通过。剩余问题不是用户范围变化，而是审查包中的 active 边界、route identity、slot 分隔字节、M401-R receipt 来源和 attempt 的 `run_root` 字段没有做到可直接重算。

### 选择与理由

1. 四份材料只把唯一归档分隔线之前的内容交给当前审查；D-102 及更早记录只作历史回查，不能继续成为执行合同。
2. route contract 直接列出五个冻结 `ROUTE_QUERIES`、`page_identity` 的唯一取值规则和 route row 的 identity 字段；不再使用“参见其他段落”的隐式引用。
3. `unit_id` 明确按 UTF-8 bytes 拼接三个实际 `0x00` 分隔 byte；M401/M402/quality.py 共用同一规则。
4. M401-R 的 attempt-local receipt 是唯一来源，顶层 receipt 只是原样 promotion view；attempt.json 自身包含 `run_root_ref` 字段，不存在第三个 run_root 文件。

### 延期交接

当前仍为 `design_repair_required / not_released`。先用 v53 当前四份材料取得两路 terminal-clean design review；通过前不执行 M401、M401-R、M402，不把 focused pytest 或旧 receipt 当作放行证据。

## D-111：v53 审查处置边界（2026-09-02）

v53 的 `pi/coding` 为 pass，但 `opencode/v4flash` 仍为 revise。有效缺口是 Home.route 主目标不唯一、quality 行字段和 `kd_ref` 不够固定、full/slice 的 R 派生未写成公式、失败 evidence 的 bundle 外边界未说明、M402 的 scanner 与 Reader 生成顺序不唯一，以及所有隔离 run-root attempt 的 `run_root_ref` 范围不完整。上述都是当前实现合同缺口，不是新增用户范围。

当前继续保持 `design_repair_required / not_released`。先修 active 四份材料和对应实现/测试，再用 v54 当前小包重新取得两路 terminal-clean review；不得执行 M401、M401-R、M402，也不得把 v53 的单路 pass 当作放行证据。

## D-112：v4.2 合同与 review packet 版本映射（2026-09-02）

`v4.2` 是四份材料的当前合同版本；`v53` 是上一轮设计审查 packet，结论为 revise；`v54` 是本轮修复后的审查 packet，结论仍为 revise；本次再修订后的 packet 统一标记为 `v55`。packet 版本只标识审查材料身份，不改变用户已确认的切片、89 条全量、Qwen/Jina、四产品和五维全胜范围。

当前状态仍为 `design_repair_required / not_released`。v55 review 通过前不进入 M401、M401-R 或 M402。

## D-113：v55 审查材料完整性与本轮修复（2026-09-02）

v54 的审查包错误地用固定行号截断了 decision-log 的 active section，因此 reviewer 看到的不是当前完整合同；这属于 packet projection error，不能拿来否定或证明源文件本身。v55 必须按唯一归档分隔标题动态截取四份材料，并把该标题行保留在包内；包外只保留三件 triad 文件和输入 manifest，不把 raw、CompanyBrain 或 provider key 放入审查材料。

本轮把未定义的 `other` source status 改为封闭枚举和布尔 `source_digest_eligible` 计数；补齐 route row 的 `home_target_page_identity` 固定字段；明确 C3 是独立 fake/no-network 隔离 attempt；明确 `quality_rows` 是 projection×dimension 行、case 只能由冻结 projection 映射唯一派生，避免重复 case 字段漂移。focused regression 为 50 passed，但它只证明当前代码合同，不替代 v55 review、M401 或真实 M402。

当前状态仍为 `design_repair_required / not_released`。v55 必须两路 terminal-clean 且所有 finding 有处置后，才允许绑定 DESIGN-CURRENT 并进入 M401。

## D-114：v55 finding 处置与 v56 交接（2026-09-02）

v55 的 packet triad 和材料 hash 校验通过；两路 reviewer 均已返回，但结论仍为 `revise`。有效问题是 C3/c3 路径大小写、`projection_key`/`projection_id` 未统一、verdict/聚合门未在 active 唯一合同中收口、source status/`source_digest_eligible` 未落到 source-row 合同、`observation_digests` 未定义；pi/coding 另报告其无法从 file-only 入口读取期望文件名，这条属于 provider 读取能力问题，不能当作设计通过。

本轮已将所有设计缺口改入 active spec/plan/tasks，并把四份材料重新按 archive marker 生成。下一审查 packet 统一为 v56；在 v56 两路结果为 terminal-clean/pass 且 findings 全部处置前，仍不得进入 M401、M401-R 或 M402。

## D-115：v56 finding 处置与 v57 交接（2026-09-02）

v56 两路 reviewer 均完成且材料 hash 可回查；`pi/coding` 判定 `pass` 但提出 slot wording minor，`opencode/v4flash` 判定 `revise`。剩余问题为 `kd_completion_digest` 仍缺少完整输入/排序/hash 定义、plan 中误写 `blank`、IMPLEMENT 的 run-root 责任未收口、`advantage_basis` 固定字段未枚举，以及 tasks 的 C3 路径大小写残留。它们都是当前合同缺口，不是新增需求。

本轮已在 active spec/plan/tasks 补齐：固定 digest 输入对象和算法、统一 `known_empty`、声明 IMPLEMENT 不写 run-root、列出 advantage_basis 全字段与嵌套 authority、统一 C3 大写目录。下一审查 packet 统一为 v57；v57 通过前仍保持 `design_repair_required / not_released`，不得进入 M401。

## D-116：v57 finding 处置与 v58 交接（2026-09-02）

v57 两路 reviewer 都完成，结论均为 `revise`。有效问题是 C0–C3 仍共用一行执行表、非 Home answer route 的 selected page 基数未定、section/answer_body unit 重叠未定、plan/decision-log 仍出现 `blank`、IMPLEMENT 与 `<card>` 路径表述未完全收口、CompanyBrain 单 row digest 与 N/A 聚合未定义、`#surface` 引用不唯一、三类 unit/block/support hash 未定义，以及 quality-result schema 输入未列入 C0 清单。

本轮已把 C0/C1/C2/C3 拆成独立卡片和路径，固定 answer route 单页、section/answer_body 两 unit、known_empty 语义、IMPLEMENT 无 run-root、单 row digest、N/A 适用条件、只允许 `page_path#unit_id`、hash 算法，并把 `config/archive/task5/task5-quality-result-v3.json`登记为第 23 个 gate-specific 输入。下一审查 packet 统一为 v58；v58 通过前仍不得进入 M401。

## D-117：v58 minor finding 处置与 v59 交接（2026-09-02）

v58 的 `opencode/v4flash` 返回 `pass` 但指出三项可执行性缺口，`pi/coding` 因 provider 没有成功 final assistant message 而失败，不能视为双路通过。三项缺口是：同 route 同 Home 目标的 unit 碰撞未明示、CompanyBrain observation row 的 status 未封闭、`qwen_payload_sha256` 的输入字节未定义。

选择在 active spec/plan 增加三条规则，并在 compiler 渲染器加同 route/同目标的确定性失败和回归测试：Home.route 以 `(route_name, home_target_page_identity)` 唯一化；observation status 固定为 `present|absent|unknown|forbidden` 并明确与 `CB_MISSING/UNKNOWN/N/A` 的关系；Qwen hash 固定绑定实际 `model.generate` payload 的 UTF-8 bytes。这样不扩大用户范围，只消除 reviewer/实现/回查之间的多义解释。v59 重新取得两路 terminal-clean review 前，仍保持 `design_repair_required / not_released`，不得进入 M401。

## D-118：v59 finding 处置与 v60 交接（2026-09-02）

v59 的 `opencode/v4flash` 返回 `pass` 但指出四项 minor 边界，`pi/coding` 再次因没有成功 final assistant message 而失败，仍不能算双路 terminal-clean。四项是 OUTPUT-001 不应使用 `.json*` 通配符、plan 的 `_digest` 失败范围需限定为本次产出、`sources.jsonl` 的 11 字段需固定、M402 表格必须写完整 released 谓词。

选择把这四项分别补入 active spec/plan/tasks，保持六个机器文件的精确清单、仓库历史资料与本次产出的范围区分、sources 行 schema 与八字段 hash projection 的关系，以及 applicable/N/A/无缺行聚合门。v60 取得两路 terminal-clean review 前仍不得进入 M401，当前继续 `design_repair_required / not_released`。

## D-119：v60 finding 处置与 v61 交接（2026-09-02）

v60 的 `pi/coding` 返回 `pass` 但指出 surface 字段是否带 `Reader.` 前缀的记号歧义；`opencode/v4flash` 返回 `revise`，指出 M402 正文仍残留“五项全 KD_WIN”简写，以及 C0 的“14/12 旧数字”与当前 `P=12` 的单位/范围不清。v60 的两路材料 hash 均已验证，但仍不能作为设计放行。

选择在 active spec/plan/tasks 明确：`surface` 存储完整 `Reader.*|Home.*` 枚举，`slot` 才使用不带前缀的固定字面量；M402 只能使用 applicable/KD_WIN、非适用/N/A、无缺重额外行的完整谓词；C0 只阻断当前生效字段中的旧 slice `14 case/12 path` 口径，合法的 `P=12`、11 case、27 path 不触发。v61 通过前仍保持 `design_repair_required / not_released`。

## D-120：v62 finding 处置与 v63 交接（2026-09-02）

### 关键事实

v62 的 packet triad 已通过：`material_manifest_hash=2eeb6a2a63fc17b2c7019bbb31e86edaaf19406a211259f21688cecde93ae037`、`packet_hash=27013031a46a136ef6635f7d29644250fa6466f54f8f2fbfee7fbfcca5e22f20`；WorkflowHub runtime=`e55f2768-1989-4cc8-a47a-c8341cddfd42`，`pi/coding` 与 `opencode/v4flash` 均 terminal completed，但结论均为 `revise`。

### 选择与理由

本轮只修当前合同的可计算边界，不增加用户范围：补齐 tree/companybrain tree 的文件列表 hash 和 snapshot-id 派生公式；把 M402 通过条件写成 applicable 行逐行规则；把 R_full 的 87 ready 与另外 2 条非 ready 写清；固定 sources.jsonl 不允许额外字段；在 M401-R/M402 卡片内补齐 source receipt 字段和 host-only receipt；把 Qwen payload hash 收敛为最终传给 `model.generate` 的唯一字符串字节规则。

### 审查 finding 对照

- v62 pi/coding：D-120 记录 packet identity/status；M401-R 字段全集；M402 host-only receipt；Qwen payload 单一序列化规则。
- v62 opencode/v4flash：tree/companybrain tree/snapshot-id 字节公式；applicable 行完整 released 谓词；R_full 的 87+2 语义；sources.jsonl 固定 11 字段。

当前状态仍为 `design_repair_required / not_released`。下一步使用修订后的 active 四份材料生成 v63 packet，只有两路 current terminal-clean 且所有 finding 已处置，才允许绑定 design stage outcome 并进入 ROOT-CAUSE/M401；不得复用 v62 review。

## D-121：v63 finding 处置与 v64 交接（2026-09-02）

### 关键事实

v63 packet triad 已通过：`material_manifest_hash=1bbc64d06776e05c46679d40d0a39318fc7204a9e38307e66d963ab2b9c3eb0b`、`packet_hash=b2e76c64c267efee4e3a8e86afcd11cd2be5b8ec8dfe981bf262649f7d4bca74`；runtime=`e4e4554f-b796-4e14-aa42-d5e049ec06f2`，两路 provider 均 terminal completed。`pi/coding` 返回 `revise`（1 blocking、3 major、5 minor），`opencode/v4flash` 返回 `pass` 但仍列 4 minor；因此 v63 不能作为 design pass。

### 选择与理由

本轮只修当前合同，不增加用户范围：将 M401 source path 统一为 `quality/evidence/task5/repair-gates/attempts/<id>/M401/`；在 spec/plan 定义唯一 canonical UTF-8 JSON（含 `ensure_ascii=false`/`allow_nan=false`）；放宽 `task5-*` 到 repair-gate/failure/host-only evidence schema 但继续禁止 public bundle；明确 C0/C1/C2 只读且不写 inverse.patch；固定 M401-R 15 字段；补齐 scanner→quality→public snapshot 的执行顺序、CompanyBrain snapshot-id 与 tree 的同一字节来源、sources.jsonl 映射和 section heading 实际 slot；把 C0–C2 命令写成可直接执行的完整命令，并修正 plan §4.1–§4.3 编号及 applicable 行失败谓词。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步基于上述修订重新生成 v64 packet；只有两路 current terminal-clean、`overall=pass` 且所有 finding 都有当前材料处置，才允许绑定 design stage outcome，随后才可执行 ROOT-CAUSE、C0–C3、IMPLEMENT、M401、M401-R 和 M402。v63/v62 仅作审计回查，不得复用。

## D-122：v64 finding 处置与 v65 交接（2026-09-02）

### 关键事实

v64 packet triad 已通过：`material_manifest_hash=5993f3329e5b94d0efe0a58f446b64c1e5f0414fc5b5fe572f76eba978ab0b86`、`packet_hash=8f4cb7ddf45377902ee6fcb745751bb95816cabbaee8ef94a8d4daf35b3563f6`；runtime=`3883bcda-222d-49ea-b277-2ef4bbeba7d8`，两路 provider 均 terminal completed，`pi/coding` 与 `opencode/v4flash` 均为 `revise`。

### 选择与理由

本轮只修合同与执行入口，不增加用户范围：IMPLEMENT 生产链补回 `quality.py`；C3 改为可直接执行的完整 pytest 命令；M401 固定 focused/full 文件集合和 packet writer 命令；observation rows 固定按 `case_id`、`projection_id`、`dimension_id` 的 UTF-8 bytes 排序；同步修正 plan §4.1–§4.3、section heading 实际 slot、canonical JSON、M401 path、source mapping 和 15 字段 receipt。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步基于当前 active 四份材料生成 v65 packet；v64 及以前审查只能回查，不能作为 design pass 或真实运行授权。

## D-124：v65 finding 处置与 v66 交接（2026-09-02）

### 关键事实

v65 packet triad 已通过：`material_manifest_hash=3ad8d29cdc842f045d931c4a735ce8baf4dfa91eabfcc8f754e3df3d37f986eb`、`packet_hash=7c21d1b9b54a58c5ff4cbd01b06f03b551519c39b55e227f1f8f3789d174e2cd`；runtime=`27218fcd-a79c-42f3-a6d8-e70dd7cf3d02`。两路 provider 均 terminal completed 且均为 `revise`：pi/coding 发现第二入口及 C0/M401 覆盖问题，opencode/v4flash 发现 M401 packet/C3 inverse/行为测试映射/text-support hash/M402 命令问题。

### 选择与理由

本轮只修当前合同，不增加用户范围：M401 packet writer 固定为同一 `digest --gate M401` 证据模式；attempt packet 固定文件名/schema/source bytes；C0 增加独立 `test_task5_contract.py` authority owner；C3 补 inverse；M401 focused/full 显式纳入 source semantic、C0 contract 和四个行为 owner；M402 改为完整参数化 digest 命令；text/support hash、observation 行序和 M401-R 读取边界全部收口。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步基于当前 active 四份材料生成 v66 packet；v65 及以前审查只能回查，不能作为 design pass 或真实运行授权。

## D-125：v66 finding 处置与 v67 交接（2026-09-02）

### 关键事实

v66 packet triad 已通过：`material_manifest_hash=32412179b10a060486cabb974e867893ae4eac24e99b18ee4f523ffcdbec9227`、`packet_hash=a82a7fc00708dcada3a82abc90480c2115f841cafad485e96021d37a95449ec2`；runtime=`d6d615e8-0ae8-4125-8e3e-7d7d7e9b6990`。`opencode/v4flash` terminal completed 且返回 `revise`；`pi/coding` 未产生成功的 final assistant message，状态为 `failed/PROVIDER_OUTPUT_INVALID`，因此本轮不能算双路设计通过。

### 选择与理由

本轮只修当前合同，不增加用户范围：M402 改为 `<provider_config>` 占位符，真实配置路径只允许进入 host-only receipt；M401 packet writer 显式引用通过 C3 的不可变 fixture bundle，并要求 runner 复核 manifest/tree/material identity；删除与 D-124 重复的 D-123 条目，保证 v65 审查只有一个处置记录。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步基于当前 active 四份材料生成 v67 packet；v66 及以前审查只能回查，不能作为 design pass 或真实运行授权。若 reviewer provider 再次失败，保留 `unavailable`，不得把单路完成当作通过。

## D-126：v67 finding 处置与 v68 交接（2026-09-02）

### 关键事实

v67 packet triad 已通过：`material_manifest_hash=b784c134c5b0ccf7182362c3f8e81646bbd3b5fc6fa646e9a19dfe68cb750d17`、`packet_hash=d091afd0bdbb81e8e868715169ed3381428ffe00256cda701ae0d12a344dc8d2`；runtime=`4754367e-706d-462d-946d-3bc9ec6e642a`。两路 provider 均 terminal completed；`pi/coding` 返回 `revise`，`opencode/v4flash` 返回 `pass` 但仍有 4 个 minor finding。

### 选择与理由

本轮只修当前合同，不增加用户范围：统一 M402 为 `--gate M402` 并定义 `--config`/`--provider-config` 语义；把 M401 的 fixture、attempt、run-root 参数写入 spec/plan；固定 M401 attempt receipt 文件并纳入 M401-R 读取边界；把 AC-v4-01…13 的七字段 trace 明确放入 packet；补齐 M401 inverse 路径、IMPLEMENT owner 测试和 full-run owner；统一 Home.route slot 的文档记号和禁止自由 `<gate>` 路径。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步基于当前 active 四份材料生成 v68 packet；v67 及以前审查只能回查，不能作为 design pass 或真实运行授权。

## D-127：v68 reviewer 失效与 v69 交接（2026-09-02）

### 关键事实

v68 packet triad 已通过：`material_manifest_hash=5abcda02a019796ce86ef78a4cf1b9f75e2062f28bd0709a3d7d86c81a3bf603`、`packet_hash=1e7e1a83845d538f2583b3b7d6ed6b403601cc7f68ceb69399aa482bf8b58092`；runtime=`df85344e-36b1-4496-b337-dd9853c51979`。`opencode/v4flash` terminal completed 但缺失必需 `overall` 字段，输出不合格；`pi/coding` 长时间无进度后由用户侧本次执行取消。因此 v68 没有有效双路设计结论。

### 选择与理由

不把无效 reviewer 输出当作通过，也不继续扩大合同范围；保留 v68 原始 receipt 和失败状态，下一轮仅针对当前 active 四份材料重新运行双路审查，确认 M402 gate、M401 CLI/receipt、AC trace、入口唯一性和 owner 映射的实际一致性。

### 延期交接

当前仍为 `design_repair_required / not_released`。v69 packet 已生成并正在进行双路 3rd-review；v68 及以前审查只能回查，不能授权实现、M401 或真实运行。

## D-128：v69 双路审查与 v70 交接（2026-09-02）

### 关键事实

v69 packet triad 已通过：`material_manifest_hash=01196fa32310eb00bf95829d8e37c13c3a1e7c5299fad8eb35785b7d73b56ae2`、`packet_hash=82370e506afea5a3f43d7e3957cf8aafbb5f9b8e17e8a7fef6764ecda4cd40b1`、runtime=`3b8f7654-4628-4658-aa14-eae23435c6ba`。两路 reviewer 都 terminal completed，但 `pi/coding` 为 `revise`（5 条 finding），`opencode/v4flash` 为 `revise`（3 条 finding）；证据见 `quality/evidence/3rd-review-design-v69-20260902.json`。意见包括 M401-R review-result artifact/哈希、C3 publication-contract owner、预算复用解释、packet canonical hash 精确定义、active/archive 分隔线在审查包内保留、M401-R 读写 allowlist 分离，以及 C2 不应读取真实 provider config。

### 选择与理由

不把 v69 视为 design pass。已在当前 active 合同中补齐 review-result 的唯一字节对象与 SHA 规则、M401 packet 自身字段排除规则、C3 owner、预算复用规则、C2 fake/no-network 边界和 M401-R 读写边界；下一审查包必须保留唯一 `ARCHIVE-NON-ACTIVE` 分隔标题。这样只收口现有可执行性，不扩大用户范围。

### 延期交接

当前仍为 `design_repair_required / not_released`。v70 packet 已由当前 active sections 生成并正在接受双路独立审查；在两路均 terminal-clean、`overall=pass` 且无未处置 finding 前，不得进入 IMPLEMENT、M401、M401-R 或 M402。该状态是当前执行状态，不是待审查的合同缺口。

## D-129：v70 finding 处置与 v71 交接（2026-09-02）

### 关键事实

v70 packet triad 已通过：`material_manifest_hash=111be230b294739f8c53041d95a40a23097fd918b330d380d12951375b1c50ce`、`packet_hash=16fc474698cd25229155abc9df40cec8406ed299145b239c31e022ca2b8dc4a9`、runtime=`eda04077-bf91-4515-8a16-1bc5b473948a`。两路均 terminal completed，但 `pi/coding` 为 `revise`（3 条 finding），`opencode/v4flash` 为 `revise`（其原始输出结构包含合并字段，仍记录为 1 条可识别 finding）；证据见 `quality/evidence/3rd-review-design-v70-20260902.json`。v70 packet 生成早于本次处置，因此其中关于 pending v70、旧 C2 措辞和旧 allowlist 的意见按当前 active 材料复核。

### 选择与理由

当前 active 合同已补齐 source page 的唯一 `page_id/page_identity` 公式、M401-R review-result 的 card 输出与四项写入/回滚集合、CompanyBrain snapshot-id 的完整 hash 输入；plan 顶部已声明 IMPLEMENT-CURRENT 的独立顺序和真实 provider 仅由 M402 调用，C2 行也已同步。v70 不构成设计通过，不能授权下游执行。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v71 packet，重新进行双路独立审查；只有两路均返回结构合法的 terminal-clean `overall=pass` 且无未处置 finding，才进入 DESIGN-CURRENT handoff 后的 ROOT-CAUSE/实现闸门。

## D-130：v71 finding 处置与 v72 交接（2026-09-02）

### 关键事实

v71 packet triad 已通过：`material_manifest_hash=ff3e17726705023cb67d11779a5ef8450cae37d700292d85a89b026403714821`、`packet_hash=21aed260affa4bf5edb3b9da9951717333bd27dedb205345ebb0b8997958e039`、runtime=`d997dab4-a5d3-4541-8b35-bafd69040c11`。`pi/coding` 输出为 fenced JSON，缺少可接受的结构化 final（`invalid`）；`opencode/v4flash` 为 `revise`（4 条 finding）；证据见 `quality/evidence/3rd-review-design-v71-20260902.json`。v71 packet 生成早于本次修正，不能作为通过依据。

### 选择与理由

本次只收口 active 合同：统一 source/answer page identity、M401 packet 的“schema 文件”措辞、M401-R 四项写入/回滚集合、C0/C1/C2 只读 attempt schema，以及 `runtime_contract_hash` 的 22 文件输入。plan 顶部已声明 IMPLEMENT-CURRENT 独立顺序，并明确真实 provider 只在 M402 调用；不存在新增产品范围。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v72 packet；只有双路返回结构合法、terminal-clean、`overall=pass` 且 findings 为空，才允许进入 WorkflowHub DESIGN-CURRENT handoff 后的 ROOT-CAUSE 和实现卡。

## D-131：v72 finding 处置与 v73 交接（2026-09-02）

### 关键事实

v72 packet triad 已通过：`material_manifest_hash=8ffb86defc6216b26c47ee637e437bbd43ef06ca82ec19b663eab3eb5e6dc322`、`packet_hash=f946fd1ffb36f6e193e0a15ecc0255b146bfdf9a5cf9fe9793d3d0285ac69d60`、runtime=`494e57be-8495-4980-bdcc-0b91e898d577`。`opencode/v4flash` 返回 `revise`（4 条 finding）；`pi/coding` 无有效 final，已按 `unavailable` 取消；证据见 `quality/evidence/3rd-review-design-v72-20260902.json`。因此 v72 没有双路设计结论。

### 选择与理由

本次已统一 plan/spec 的 M401-R 四项 allowlist、C0/C1/C2 `run_root_ref=null`、M401 `attempt.json` 与 `attempt-receipt.json` 的职责、M401 promotion/ref 目标，并在 source/answer identity 与 runtime contract 两处保留同一可重算规则。当前只修合同，不进入实现。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v73 packet 并重跑双路；任一路无结构化 final、overall 非 `pass` 或存在 finding，均不能授权下游。

## D-132：v73 finding 处置与 v74 交接（2026-09-02）

### 关键事实

v73 packet triad 已通过：`material_manifest_hash=ba603ac2d9ff4857b651efee4dcee0fb305dfd7570678011921797ee65349c38`、`packet_hash=a042eb75b761789a45ee97c0e01766e63693278730b269c68075ea9b885ff616`、runtime=`e54792ad-94af-4092-8faf-f7dc5c7412e2`。`opencode/v4flash` 返回 `revise`（3 条 finding）；`pi/coding` 因无有效 final 被取消，不能形成双路结论；证据见 `quality/evidence/3rd-review-design-v73-20260902.json`。

### 选择与理由

已统一 M401-R 的四项读取 allowlist、`source_receipt_ref` 指向 M401 attempt receipt、M401 packet promotion source 记录位置、provider 配置错误的 global failure 归类，并把 M401 两类 receipt 的职责写成不同 schema。该轮仍只修合同，不执行下游。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v74 packet；两路均须返回结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 WorkflowHub DESIGN-CURRENT handoff 和实现闸门。

## D-133：v74 finding 处置与 v75 交接（2026-09-02）

### 原始需求

继续同一 Task5 的设计收敛；只有当前合同经过双路独立审查并形成 terminal-clean、无 finding 的设计结论，才允许进入实现和真实知识消化。不得用单路 reviewer、旧 receipt、pytest 绿或临时产物旁路。

### 关键事实

v74 packet triad 已通过：`material_manifest_hash=66812311f66f4dd40336e5d901cdee2f32d40717847263306f4739bce923ffb7`、`packet_hash=5d969bdad5cc04a8533b765069a3e19dafaa1a8517f7b2beda1112c36a9c5509`、runtime=`be35d38c-e9ea-4563-b407-806a3afe9541`。`opencode/v4flash` 返回 `revise`（4 条 finding）；`pi/coding` 无有效 final，已取消；证据见 `quality/evidence/3rd-review-design-v74-20260902.json`。v74 仍未形成双路设计通过。

### 选择与理由

已修正四类合同问题：M401 promotion view 只原样提升 packet bytes，来源 ref/SHA 只在 M401 attempt receipt；新增封闭的运行/attempt status、reason_code 和 terminal_status；逐字段固定 `task5-m401-attempt-receipt.v1`；补齐 `snapshot_tree`、`material_id`、`input_snapshot`、`scores`、`embedding_receipt`、`failure` 的机器定义，并同步 plan。仍不执行实现或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v75 packet；两路均须返回结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-134：v75 finding 处置与 v76 交接（2026-09-02）

### 关键事实

v75 packet triad 已通过：`material_manifest_hash=1363a39bcd7c146cb10cc639bfec32570b033ee1ea75beadf0c0a1ca390b0f1c`、`packet_hash=619e68dc6a5546852a90f54f218db41e9db0fd5d93ca1f2ad7e273391087958f`、runtime=`6ddff8ca-388f-45c7-b75b-9beb6950ec2c`。`pi/coding` 返回 fenced `pass` 但内容无 finding；`opencode/v4flash` 返回 `revise`（4 条 finding）；证据见 `quality/evidence/3rd-review-design-v75-20260902.json`。因此 v75 仍未形成双路设计通过。

### 选择与理由

本次补齐 route row `status` 封闭枚举及映射；固定 CompanyBrain observation rows 的 host-only 路径和 `task5-companybrain-observation.v1` 字段；把 C0–C3 任务卡失败结果映射到封闭 attempt status；把 `task5-repair-gate-attempt.v1` 改成完整字段集，并统一 C3/M401 非空、IMPLEMENT/M401-R 为 `run_root_ref=null`。仍只修合同，不执行实现或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v76 packet；两路均须返回结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-135：v76 finding 处置与 v77 交接（2026-09-02）

### 关键事实

v76 packet triad 已通过：`material_manifest_hash=414f970f897ca9b7ac6d0391b862c6af7d3b5758b159fa3989969016ffd9a416`、`packet_hash=d7ff6af5d5d70342c3e13efa3add326e6cc6503eb9b1cf5b04fb81138cf1441d`、runtime=`ba9ce40d-c1b0-4795-a345-025794c5f69c`。`opencode/v4flash` 返回 `revise`（3 条 finding）；`pi/coding` 超过合理等待后无有效 final，已取消；证据见 `quality/evidence/3rd-review-design-v76-20260902.json`。因此 v76 仍未形成双路设计通过。

### 选择与理由

本轮待修三处：统一 observation rows 与 `observation_sha256` 的输入字节；把 `source_receipt_ref` 的指代改成明确的 `attempt-receipt.json`；统一 host-only receipt 的 schema namespace。仍不执行实现或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v77 packet；两路均须返回结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-136：v77 复核说明（2026-09-02）

### 关键事实

v77 用于复核 v76 的三项合同修正：observation hash 输入唯一化、M401-R source receipt 的明确指向、host-only schema namespace 统一。当前 v76 证据见 `quality/evidence/3rd-review-design-v76-20260902.json`，v76 未形成双路设计通过；v77 的三元 hash 和 reviewer 结果只在实际运行后回填，不预填占位值。

### 选择与理由

只允许在 v77 双路 terminal-clean、结构合法、`overall=pass` 且 findings 为空后进入 WorkflowHub DESIGN-CURRENT handoff；若仍有任何合同问题，继续修 active 段并生成新审查包，不进入实现、M401 或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。v77 审查结果和三元 hash 完成后必须回填本节；在此之前不得把设计阶段标记为通过。

## D-137：v77 finding 处置与 v78 交接（2026-09-02）

### 关键事实

v77 packet triad 已通过：`material_manifest_hash=f9b309039bec660344bfb3a904398143b683b81b8ca322da6689a965e1311283`、`packet_hash=dd7fc8d97b4fdd4dd0eece5ed30b02d9799ec27e8366e57a4735038949020331`、runtime=`885323c6-8bab-4658-a286-f96903728a52`。`opencode/v4flash` 返回 `pass` 但仍有 4 条 finding；`pi/coding` 超过合理等待后无有效 final，已取消；证据见 `quality/evidence/3rd-review-design-v77-20260902.json`。因此 v77 仍未形成双路设计通过。

### 选择与理由

已补齐 `authority_manifest_sha256` 与 `runtime_contract_hash` 的唯一绑定；将 `patch_sha256` 改为可由 `changed_paths` 重算且不增加 forward patch artifact；封闭 `review_kind`、`cb_gap_type`、observation `score` 并声明 WorkflowHub review-result schema；把预算文字改为每个失败 projection 固定 compile+repair 两档。仍不执行实现或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v78 packet；两路均须返回结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-138：v78 finding 处置与 v79 交接（2026-09-02）

### 关键事实

v78 packet triad 已通过：`material_manifest_hash=92ac62fe7f237790bb1060c3545628e5dc38d426f9a87a39b31d0f20a7f90e77`、`packet_hash=780bf076e990d03d1d4b12b82044a38f90f57e379e629b6a555a29f6aec74b49`、runtime=`aa67f2ab-ac48-4f8b-906c-cff2ed442d74`。`opencode/v4flash` 返回 `revise`（1 条 major、4 条 minor）；`pi/coding` 因无有效 final 被终止；证据见 `quality/evidence/3rd-review-design-v78-20260902.json`。因此 v78 仍未形成双路设计通过。

### 选择与理由

本轮已修正五处合同缺口：声明 `RunManifest` 的唯一 schema/顶层字段和 receipt manifest hash；明确 absent/N/A observation 的 `score=null`；将 M401 receipt command 固定为 packet-writer 命令并把 pytest 命令留在 AC trace；固定 C0–C2 的完整 attempt 父路径；把 D-136 标题改为复核说明以消除重复交接标题。仍不执行实现或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v79 packet；两路必须结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-139：v79 finding 处置与 v80 交接（2026-09-02）

### 关键事实

v79 packet triad 已通过：`material_manifest_hash=7cab19b6c970aceac3b26e0e282e68c7dfece201a24a199c29ef540bc88d5e7e`、`packet_hash=4910b11c472c4114a33ba65a437ede496199eb6e308b98826d69c806767659a6`、runtime=`e96e16a8-8c4a-45a9-a376-d1dc86a5ad05`。`opencode/v4flash` 返回 `revise`（1 条 major、2 条 minor）；`pi/coding` 因无有效 final 被终止；证据见 `quality/evidence/3rd-review-design-v79-20260902.json`。因此 v79 仍未形成双路设计通过。

### 选择与理由

本轮已修正三处合同缺口：固定 `knowledge-digest-page-row.v1` 的字段集和 Reader path/slug/冲突后缀字节公式，并同步 spec/plan/tasks；显式映射 M401-R 的 `available/needs_human/partial/unavailable` 到唯一 reason/status/terminal 组合；固定 M401 `fixture_bundle_sha256=fixture tree_sha256`、`fixture_manifest_sha256=fixture run-result.manifest` 的两类输入字节。仍不执行实现或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v80 packet；两路必须结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-140：v80 finding 处置与 v81 交接（2026-09-02）

### 关键事实

v80 packet triad 已通过：`material_manifest_hash=e6cde5d0c685335fd5e6c0a90982fb682fa1918c21c88d454c4c5b430d7a0279`、`packet_hash=0c8a032d5be8cc94edf8e4002e03d4b55562017eba0f59ac0ad5783cf94a1c00`、runtime=`19958285-af97-4d71-921c-59d4403c4314`。`opencode/v4flash` 返回 `revise`（2 条 major、1 条 blocking）；`pi/coding` 因无有效 final 被终止；证据见 `quality/evidence/3rd-review-design-v80-20260902.json`。因此 v80 仍未形成双路设计通过。

### 选择与理由

本轮已把 page row schema/path/slug/surface hash 定义写入 spec active 段，并把 M401-R 的 `status/reason_code` 加入固定 receipt 字段；已同步 plan/tasks。M401 fixture tree/manifest hash 规则也已在四份材料中统一。仍不执行实现或真实 provider。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v81 packet；两路必须结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-141：v81 finding 处置与 v82 交接（2026-09-02）

### 关键事实

v81 packet triad 已通过：`material_manifest_hash=cf8c9e14eb7d775c3df6c6690d58c9aa8ba9c32c3264c7284747763259127bb4`、`packet_hash=797d4f1579fa4256272f2fbb840e9b538fbc68c8f112a14376023ed1ef4b6ba6`、runtime=`a99b264e-5c4f-4751-9ae1-0bb0854014ac`。`opencode/v4flash` 返回 `revise`（2 条 major、3 条 minor）；`pi/coding` 在无有效 final 且无进度等待后被取消，不能算第二路通过；证据见 `quality/evidence/3rd-review-design-v81-20260902.json`。因此 v81 仍未形成双路设计通过。

### 选择与理由

本轮只修当前 active 合同，不增加用户范围：统一 slice→full provider budget 的唯一公式，明确无复用为 140、完美复用为 115，删除 133 硬门；把 89 行约束限定为 M402 真实输入并放宽 C3/M401 受控 fixture 的行数；在 spec/plan/tasks 显式列出五个英文 page_type 及 DIM-04 映射；删除 published page 的未知产品/general 兜底，未知一级目录固定为 unclassified/unsupported 且不生成 Reader；逐字段固定 RunManifest 的 sources/routes/pages 排序键。下一审查包为 v82，仍不执行 M401、M401-R、M402。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v82 packet；两路必须结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-142：v82 finding 处置与 v83 交接（2026-09-02）

### 关键事实

v82 packet triad 已通过：`material_manifest_hash=941d65419e62c7a547fe7fa7934dcebbef0841f40a5230c2c88dcdf9a3861ef0`、`packet_hash=82b4855a5a6202b5fe974b48e4a951003276c9b8384d41acb878e731ed866cd4`、runtime=`0512062e-324b-4ff1-8c84-612d92cf5662`。`opencode/v4flash` 返回 `revise`（2 条 major、4 条 minor）；`pi/coding` 在无有效 final 且长时间无进度后被取消，不能算第二路通过；证据见 `quality/evidence/3rd-review-design-v82-20260902.json`。因此 v82 仍未形成双路设计通过。

### 选择与理由

本轮只修当前 active 合同，不增加用户范围：定义 `run_root_sha256` 的 tree-hash 字节；固定 title slug 使用 Unicode Letter+Nd、空 slug 为 `untitled`、空 title 失败；统一 C3/M401 字段名为 `fixture_source_count`；固定失败索引 basename 为 `bundle`；固定空 body section 不渲染且不生成 unit；明确所有 manifest route row 都是 Home.route row，目标恰好一项且不允许 null 分类。同步 spec/plan/tasks，并保留 v82 revise 证据。下一审查包为 v83，仍不执行 M401、M401-R、M402。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v83 packet；两路必须结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-143：v83 finding 处置与 v84 交接（2026-09-02）

### 关键事实

v83 packet triad 已通过：`material_manifest_hash=06234966b32b462014c1fbf94ee4c4c60db398ca440db6c3898881d58c270be6`、`packet_hash=c3090695a1b200677ab64c5260e22c3bfd0b836205af83f26117d9c711eef753`、runtime=`708bf46d-dda7-40b7-8429-d3c21fcdb8f7`。`opencode/v4flash` 返回 `revise`（2 条 major、5 条 minor）；`pi/coding` 被取消且无有效 final，不能算第二路通过；证据见 `quality/evidence/3rd-review-design-v83-20260902.json`。

### 选择与理由

本轮只修当前 active 合同，不增加用户范围：直接改写旧 route 分类规则，定义 M401 packet 的完整文件字节 hash，声明 `fixture_source_count` 只是 fixture `RunManifest.source_count` 的校验名称，把 v4.3.1/2/3 放到唯一归档分隔线前，保留送审材料中的 `ARCHIVE-NON-ACTIVE` 边界，封闭 slug `-N` 冲突和截断规则，并固定 M401-R `needs_human|partial` 的 `terminal_status=semantic`。下一审查包为 v84，仍不执行 M401、M401-R、M402。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v84 packet；两路必须结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-144：v84 finding 处置与 v85 交接（2026-09-02）

### 关键事实

v84 packet triad 已通过：`material_manifest_hash=147224488a025c4f75e0d33b10ac8f1755d4a429537c7eaf216c43aa358df326`、`packet_hash=55364b10be380843ea429a4c6696ed6ad80a899153f54b91f1bc0faed725b37b`、runtime=`e669429f-425e-4053-b0d3-81b8fbc84026`。`opencode/v4flash` 返回结构合法的 `overall=pass`，但带 1 条 minor finding；`pi/coding` 被取消且无有效 final，不能算第二路通过；证据见 `quality/evidence/3rd-review-design-v84-20260902.json`。

### 选择与理由

本轮只修当前 active 合同，不增加用户范围：把 slug 分配从同 `base_slug` 组内唯一改为同 `(product_key,page_type)` 目录内全局占用集合，按稳定排序选择第一个未占用的 `base_slug`/`base_slug-N`，保留长度截断规则，并同步 spec/plan/tasks。下一审查包为 v85，仍不执行 M401、M401-R、M402。

### 延期交接

当前仍为 `design_repair_required / not_released`。下一步生成 v85 packet；两路必须结构合法、terminal-clean、`overall=pass` 且 findings 为空，才能进入 authenticated WorkflowHub DESIGN-CURRENT handoff、ROOT-CAUSE 和实现闸门。

## D-145：v85 双路设计审查通过与实现闸门交接（2026-09-02）

### 关键事实

v85 packet triad 已通过：`material_manifest_hash=dd09f1de28fc041fa20cf6c90ce49c128dbc389c35c4894d75062c021afd4210`、`packet_hash=a1c0c5713f3598e2062bd39268359a476faac66ee4f5f17234052e62efa26b8d`。同一 packet 上，`pi/coding`（runtime=`1650e38f-f1a5-4c3d-b9de-13e00f71e46b`）和 `opencode/v4flash`（runtime=`957e9313-0841-427b-b127-464ba97acefc`）均为 terminal completed、严格 JSON、`overall=pass`、`findings=[]`；证据见 `quality/evidence/3rd-review-design-v85-20260902.json`。v85 的材料仍是 docs-only 设计审查，尚未证明实现、真实 89 条运行或五项胜过 CompanyBrain。

### 选择与理由

设计合同通过，可以进入 authenticated WorkflowHub `DESIGN-CURRENT` handoff；随后必须按顺序执行 `ROOT-CAUSE → C0 → C1 → C2 → C3 → IMPLEMENT-CURRENT → M401 → M401-R → M402`。设计通过只解除“合同未收口”阻塞，不把实现、测试、真实 provider 或 release 提前算通过。

### 延期交接

状态更新为 `design_passed / not_released`。下一步只建立当前 task/worktree/snapshot/material 绑定并执行 WorkflowHub DESIGN-CURRENT；任何绑定漂移、审查证据不可回查或 successor 未由 authenticated adapter 生成，都停在实现闸门前。

## D-146：provider 配置路径与 key 优先级补齐（2026-09-02）

### 原始需求

KnowledgeDigest 必须实际调用 Qwen/Jina；用户把本地 provider 配置和明文 key 放在 `/Users/Hugh/.config/knowledge-digest/config.json`，真实运行不应依赖临时目录或凭空生成配置。

### 关键事实

实现已经支持默认读取 `~/.config/knowledge-digest/config.json`、显式 `--provider-config`、Qwen endpoint/model allowlist、Jina endpoint/model allowlist，以及 section `api_key` 优先、`api_key_env` 兼容回退和根级 `api_key` 迁移兼容；但当前 active spec/plan/tasks 只写了泛化的 provider-config，没有把这些可执行事实完整写入当前合同。

### 选择与理由

把默认路径、显式覆盖关系、批准 endpoint/model、实际模型必须原样留证、直接 key 优先级、首请求前的 zero-call 失败和 secret/path 的 receipt 边界同步写入 active spec/plan/tasks。这样审查器能按当前用户配置要求检查实现，且不改变 Qwen/Jina、四产品、89 条全量、五维全胜或 Downloads 输出范围。

### 延期交接

当前仍保持 `design_repair_required / not_released`；重新取得 authenticated 当前材料的设计审查并处置全部 finding 后，才继续 ROOT-CAUSE、C0–C3、IMPLEMENT、M401、M401-R 和 M402。真实 provider 在此之前不调用。

## D-147：V50 历史阻塞不再阻断当前 raw-only 发布（2026-09-02）

### 原始需求

继续同一个 Task5，只使用 `/Users/Hugh/Downloads/confluence 原始数据` 做垂直切片和 89 条全量，真实调用当前配置中的 Qwen/Jina，按问题/场景、五轴分类、业务答案、五类页面、Reader/Audit 五项严格比较 CompanyBrain；五项和全部来源闭包未通过，不能 released。不要因为丢失的临时历史产物让当前真实知识生成再次停住。

### 关键事实

- 精确 `RC-USER-V50` 路径不可回查，D0-H 已真实留下 `blocked/calls=0`，不能伪造、替换或 promotion。
- 当前 raw 89 条和四产品 source-scope 已能独立闭合；健康的 v10 候选已证明 Qwen/Jina 可以真实生成可读 Reader，但它仍只是 candidate，不能替代正式 M402。
- 当前质量目标依赖本次 CompanyBrain snapshot、五项逐格结果和 Reader/Audit 闭包，不需要把历史 V50 当作语义输入。
- SND 的“错误”命中来自 GoInsight 方案优缺点描述，当前 trigger-only 规则把它错误视为 ambiguous。

### 选择与理由

1. 保留 D0-H 的不可回查事实，但把它从当前 raw-only M401/M402 的硬前置降为历史限制；当前基线改为 M402 当次 CompanyBrain snapshot。
2. 继续要求 89 条来源、四产品、slice→full、Qwen/Jina、五项严格 `KD_WIN`、Reader/Audit 和 Downloads 结果全部闭合；只移除一个与当前语义质量无关的历史输入阻塞。
3. 将 SND 规则收紧为“动作词=规则；明确描述/否定语境中的触发词=no_rule；其余 trigger-only=ambiguous”，并由 deterministic verifier 使用同一规则复算。

### 失败边界、非目标与延期交接

V50 不可回查仍不得写成根因已证实，也不允许复制其他候选补洞；当前任何 provider、身份、来源、五项质量或 Reader/Audit 失败仍保持 `blocked/not_released`。本次只修当前合同和误判，不增加产品范围、不增加 successor task、不修改 raw、CompanyBrain、旧产物或 main。由于当前四份材料发生了合同修订，旧 design/implementation handoff 不能直接冒充新材料身份；如需正式 M402 release，应在一次新的 authenticated handoff 中绑定本修订后的 material。

### 交接

立即执行：更新 SND contract/authority hash 和 M401 可选历史输入处理，跑 focused/full 回归，再用新 Downloads 目录做一次真实 slice→89 full。结果只按实际五项和闭包决定，不因候选 evaluator 结果提前 released。

## D-148：真实候选暴露的长文与漏证据恢复边界（2026-09-02）

### 原始需求

继续同一 Task5：只用 `/Users/Hugh/Downloads/confluence 原始数据`，完成垂直切片和 89 条全量；真实使用当前配置中的 Qwen/Jina；Reader 按问题/场景、五轴和五类页面组织，正文必须是业务化答案，Audit 必须可回查；五项逐格都高于 CompanyBrain 前不得 released。

### 关键事实

- 全量真实候选已闭合 89 条来源、四个产品和 Downloads 输出树，但 v12 仍是 `not_released`：9 条来源因 provider 504/输入过长失败，Q-CON-01 因漏掉 VPN 配置证据组失败。
- 根因不是“没有调用模型”：实际调用了 Qwen/Jina；问题是长表格被展开成重复 JSON 证据，输入变大，以及质量页首轮失败后没有重新生成。
- 质量页必须由 Qwen 重新写完整页面，不能由 Python 把缺失正文或证据硬拼回去；provider adapter 的 HTTP retry 仍固定为 0。

### 选择与理由

- 长 source prompt 超过阈值时改为“每行一次 + evidence_id/行号标记”的紧凑证据包，保留原文行和可回查身份，减少重复 JSON。
- source compile 增加固定的全局 recovery pool：最多 12 次，单 source 最多追加 3 次；quality projection 结构/证据校验失败最多重新发 1 次完整 Qwen 页面。所有 recovery 写入 trace、hash 和 call plan。
- 这是一条有限、可审计的恢复路径，不是无限重试；耗尽后仍保留 Audit-only/not_released，绝不降低五项质量门槛。

### 失败边界、非目标和延期交接

不把 provider 失败源从 89 条分母删除，不把原文或 CompanyBrain 代替 Qwen 正文，不放宽五项比较，不修改 raw、CompanyBrain、main 或旧产物；M401/M401-R/M402 的 authenticated receipt 仍需由 WorkflowHub 真实生成，不能手写。下一步只做全量回归和一次新的 Downloads 真实候选，按 v4.4 当前合同审查；没有通过全部硬门就保持 `not_released`。

## D-149：质量校验改为单页请求（2026-09-02）

### 关键事实

v14 的 89 条来源已闭合，87 条可处理来源全部生成页面，12 个质量页也生成；剩余阻塞不是来源遗漏，而是质量事实校验的多页 batch 返回了错误的 page 数/身份，另外指标诊断页的修复仍保留了证据不支持的两句操作描述。

### 选择与理由

质量页事实校验改为一页一请求，并在修复提示中明确要求逐句回看对应 evidence block；unsupported 且找不到直接或不改变条件的同义证据时必须删除或写“原始资料未明确”。这增加少量可预测请求，但不增加无限重试，也不允许 Python 拼接正文；每页最多一次完整修复，失败继续 Audit-only/not_released。

### 交接

下一次只生成一个新的 Downloads 候选并检查：89 条来源状态、12 个 quality projection、单页 verifier trace、五项逐格结果和 Reader/Audit 闭包。任何 provider 或质量失败都按真实原因保留，未满足五项全胜不得 released。

## D-150：显式 UNKNOWN 占位不冒充事实血缘（2026-09-02）

### 原始需求

真实资料不足时必须显示“原始资料未明确”，不能编造来源；同时所有真实 Reader 事实必须完整回查。

### 关键事实

v15 的 `evidence.jsonl` 有 1777 行，其中 1763 行是真实绑定；另外 14 行是 `Reader.answer_body`/`Reader.section` 的精确 UNKNOWN 占位，均无 evidence。这不是漏绑事实，但旧计算把它们计入分母，导致显示 `1763/1777=99.21%`。

### 选择与理由

保留这 14 行，新增 `unknown_units` 单独统计；`quality.py` 只把事实 unit 纳入 `rendered_units` 和 `lineage_coverage`，要求事实 unit 仍为 100%。不给 UNKNOWN 补 raw binding，避免把“没有明确资料”伪装成某一段原文支持。

### 交接

重新生成候选并核对 `unknown_units`、事实血缘 100%、五项独立对照和正式 M401/M401-R/M402 状态；任何非 UNKNOWN unit 的无绑定仍阻断发布。

## D-151：v16 真实候选结果与正式发布边界（2026-09-03）

### 关键事实

使用用户配置文件和 `/Users/Hugh/Downloads/confluence 原始数据` 完成新的 slice→full 真实运行，结果在 `/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-compiler-real-20260902-v16`。89 条来源闭合为 `87 ready + 1 known_empty + 1 duplicate_alias`，生成 87 个来源页、12 个质量页、99 个 Reader 页；Qwen 141 次、Jina 18 次；事实 RenderLedger 为 `1771/1771=100%`，另有 12 个显式 UNKNOWN 缺口占位。

独立 evaluator 使用两轮模型判断，12 个 projection × 5 个维度 × 2 轮共 120 格均为 `KD_WIN`，但该结果没有生成正式 `quality-result` 的逐格 advantage basis，不能单独变成 released。

### 选择与边界

保留 v16 作为最新真实候选和复核材料；正式状态仍是 `candidate/not_released`。当前仓库缺少 authenticated M401 packet、M401-R promoted receipt、WorkflowHub implementation handoff 和 actual-run promotion，因此不能把 v16 的 evaluator 输出或 bundle 内 candidate quality.json 当作 M402 release 证据，也不手写这些证据补洞。

### 交接

下一步只沿现有顺序补齐 authenticated DESIGN-CURRENT → C0–C3/IMPLEMENT → M401 → M401-R → M402；若任一正式逐格观察、来源闭包、provider receipt 或发布树校验失败，继续保持 `not_released`。

## D-152：C1 边界与 provider 预算纠偏（2026-09-03）

### 关键事实

本轮 `mini_task.design` 的 provider 返回了原始 JSON，但 WorkflowHub 没有生成 canonical evidence，不能作为 design pass。原始审查内容直接发现两处合同冲突：C1 同时被写成“离线合同门”和“读取真实 raw/生成 host receipt”；预算计划固定写成 `140/133`，与 v16 实际观察到的 Qwen `141`、Jina `18` 不一致。

### 选择

C1 固定为离线 manifest/fixture 合同门，不读取真实 raw、不调用 provider、不生成 host-run-receipt；真实 raw、host identity 和运行 receipt 只由 M402 的 `compiler.digest` 生成。预算改为由 `compiler._provider_call_plan` 按真实调用点动态计算，不再以 `140/133` 作为放行依据；source recovery、逐页质量事实校验、质量修复和 embedding 批次都必须显式计入计划。provider v2 的 `180` 只作为配置上限。

### 结果与交接

raw D0-R 已通过；design review 仍为 unavailable/blocked。当前不进入 M401/M401-R/M402，不伪造 handoff 或 release。下一步先完成回归；只有取得 authenticated design handoff，才继续正式 M401/M402。

本轮尝试用 TaskHandle 适配真实 `mini_task.design` 时，provider 进程在 `opencode/pax3.8` 等待约 3 分钟后无输出，已主动终止；没有生成 canonical review result，也没有写入任何 KnowledgeDigest 产物。该结果按 transport unavailable 保留，不重试、不改写成通过。

## D-153：恢复 qwen3.6 单一身份并修复实现审查材料（2026-09-03）

### 原始需求

本 Task5 只允许在 `https://dashscope.in.whatspos.cn/v1` 使用 Qwen `qwen3.6`，并从用户的 `/Users/Hugh/.config/knowledge-digest/config.json` 读取 provider key；必须真实调用 Qwen/Jina，但配置或模型身份不符合合同时不能偷偷替换。实现审查还必须能直接检查测试结果、用户结果和 AC-v4-01…AC-v4-13，不能只给不可读的引用。

### 关键事实

当前实现审查发现 active spec/plan/tasks、provider allowlist 和示例配置把非 `qwen3.6` 模型错误加入了 Task5 合同；本机配置当前也不是 `qwen3.6`，因此按修正后的合同，下一次真实运行应在首个请求前阻断并记录 `provider_calls=0`，直到用户把配置改成 `qwen3.6`。同一审查还发现送审材料只有 test/user result 的 ref/hash，且 AC 只提交了一个泛化条目，审查器无法验证本次实现的真实覆盖。

### 选择与理由

1. 将 Task5 的代码、配置、示例、测试和当前生效文档统一收敛为唯一 Qwen 身份 `qwen3.6`；其他模型仅在历史归档中保留，不作为兼容放行项。这样“真实使用模型”与用户原始要求一致，模型不可用时会明确失败，而不会再次生成身份不符合要求的候选。
2. mini-task implementation review 材料增加不含密钥的 test receipt 关键字段（退出码、快照、输出引用/哈希）和 user result 关键字段（状态、场景、预期、实际、判定）；实现审查的 AC trace 必须逐项提供 AC-v4-01…AC-v4-13。引用仍保留，用于完整回查。

### 失败边界与交接

本轮不修改 raw、CompanyBrain 或旧候选，不把不合规候选升级为正式结果。当前已有 C3/M401/实现审查证据因代码与合同身份变化而失效，必须在新的当前 snapshot/material 上重新执行 DESIGN-CURRENT；设计审查未取得 terminal-clean 的 authenticated 结果前，不得重跑 M401-R 或 M402。

## D-154：设计审查发现的 successor 合同缺口（2026-09-03）

### 关键事实

基于当前 snapshot/material 发起的一次真实 `mini_task.design` 尝试中，`kimi/coding` 返回了四项可执行 finding：active tasks 没有定义 WorkflowHub successor 的可计算 schema/hash/三方 identity；active plan 仍写 retired `fixture_count`；M401-R 的 `needs_human|partial` 没有固定 `terminal_status`；D-151 使用 retired `blank`。`opencode/pax3.8` 在有界等待内未返回 terminal result，外层运行已停止；本次没有 canonical design result，因此不能视为设计通过。

### 选择与理由

只修当前合同和真实 M402 前置校验：active spec 明确定义 `workflowhub-implementation-successor.v1` 的顶层/嵌套字段、canonical self-excluding `handoff_sha256`、受控 ref/hash 和三方 identity；plan/tasks/spec 统一 `fixture_source_count` 与 M401-R 状态映射；`compiler.py` 在读取 raw、CompanyBrain 或发 provider 前拒绝非 canonical、缺字段、越界 ref/hash、身份不等或非 authenticated 的 handoff。这样不能再用“handoff 文件存在”替代真实审查证明。

### 交接

新增 handoff 负例后 Task5 focused 测试为 `93 passed`，`git diff --check` 通过。由于当前设计审查仍无 terminal-clean canonical result，继续保持 `not_released`，不生成 M401-R successor，不执行 M402；下一次 DESIGN-CURRENT 必须绑定本次合同修订后的新 snapshot/material。

## D-155：按用户决定切换 qwen3.8，并取消设计审查硬阻断（2026-09-03）

### 原始需求

继续完成同一 Task5 的垂直切片和 89 条全量；真实消化必须使用用户配置中的 LLM/embedding；只有五项质量逐项胜过 CompanyBrain、来源闭包和发布证据都通过，才允许 released。用户明确指定以后使用 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`，并明确不要求 3rd-review 产出可认证的 terminal-clean 设计结果才能继续。

### 关键事实

- 用户配置 `/Users/Hugh/.config/knowledge-digest/config.json` 的 LLM model 已是 `qwen3.8`，批准 endpoint 的 live `/v1/models` 返回 `qwen3.8`；原合同仍把生产 allowlist、示例、测试和若干机器 schema 写成 `qwen3.6`，会在真实运行前错误阻断。
- 最近的 `mini_task.design` 没有在有界等待内产生可认证 canonical terminal result；这只能证明审查证据不可用，不能证明当前代码、真实 raw 或真实质量结果已经通过。

### 选择与理由

1. 当前 Task5 生产 provider、Task5 provider identity、provider v2 schema、示例、run-result identity、README/CONTEXT/active spec/plan/tasks 和对应回归统一为唯一 `qwen3.8`。旧 Task2/Task3 历史实现和归档材料保留原值，不作为 Task5 运行入口。
2. `DESIGN-ADVISORY` 改为可选事实记录：有结果就记录，没有结果、partial 或 unavailable 就记录风险并继续；不伪造 design pass。`parent_design_review=null` 合法，WorkflowHub successor 仍必须由 authenticated implementation adapter 写入；M401/M402 仍保留当前代码、测试、M401 packet、M401-R implementation review、真实 raw/CompanyBrain、五项逐格结果和 Reader/Audit 闭包硬门。

### 失败边界与交接

本次只改变模型身份和设计审查的前置性质，没有降低五项质量标准，也没有把旧 review、绿色 pytest 或没有结果的设计审查当作通过。下一步重新跑 C0–C3/IMPLEMENT/M401；再取得 authenticated `mini_task.implementation` 后执行真实 M402 slice→89 条 full。若 qwen3.8/Jina、来源闭包、Reader/Audit、任一逐格比较或发布树失败，保持 `not_released`/`blocked`，不 close。

## D-156：qwen3.8 真实 slice→89 运行与质量结果（2026-09-03）

### 原始需求

按 D-155 继续同一 Task5：只读取 `/Users/Hugh/Downloads/confluence 原始数据`，真实使用用户配置中的 Qwen/Jina，完成垂直切片和 89 条全量；Reader 按问题/场景进入，按四产品和五轴组织，正文业务化，Audit 可回查；五项质量全部严格胜过 CompanyBrain 才能把知识结果标为 released。3rd-review 的 terminal-clean design 结果不再是继续执行的硬前置。

### 关键事实

- 用户配置实际使用 `https://dashscope.in.whatspos.cn/v1` / `qwen3.8` 和 `https://llm.paxszapp.com/v1` / `jina-embeddings`；live `/v1/models` 返回 `qwen3.8`，没有切换旧模型。
- 真实产物写入 Downloads：`/Users/Hugh/Downloads/KnowledgeDigest-task5-qwen38-real-20260903`；slice 和 full 均由同一入口执行。
- 89 条来源全部入 Audit：87 条 `ready`、1 条原始空白页 `known_empty`、1 条重复别名 `duplicate_alias`；四个产品来源计数为 EMM for Android 27、GoInsight 22、EMM for iOS 20、Merchant System 20。
- 产出 99 个 Reader 文件（87 个来源页、12 个质量投影页）和 5 个产品/跨产品索引；Reader 路径无跨产品闭包错放，Home→Reader→Audit 的路由闭包检查通过，lineage coverage 为 100%。正文未出现“五轴分类”、整段原文复制或乱码文件名。
- `_audit/quality.json` 的 12 个质量投影 × 5 个维度共 60 行全部为 `KD_WIN`；CompanyBrain snapshot、Reader/Audit 引用和 provider trace 均已绑定。真实调用统计为 LLM 146、embedding 18。
- 代码回归：聚焦测试 20 passed；全量测试 855 passed、3 skipped；`git diff --check` 通过。

### 选择与理由

把该目录记录为“真实运行且五项质量通过的候选结果”，允许用户直接检查，不再等待 terminal-clean design review。设计审查缺失只作为 advisory 记录，不降低实现、来源闭包、Provider 真实消费、Reader/Audit 和五项质量门槛。

本记录不把 WorkflowHub 的实现审查、M401/M401-R/M402 物理闭环伪装成已完成；因此任务级状态保持 `release_pending`，而不是把 CLI 的单次 `released` 输出扩大解释为全部工程收尾。

### 延期交接

如果继续做正式任务收尾，只执行当前实现审查及其 M401/M401-R/M402 绑定，复用本次 Downloads 产物和当前 qwen3.8 合同；不再重新做设计 terminal-clean 审查，不修改 raw、CompanyBrain 或本次真实 bundle。

## D-157：把设计审查缺失落实到运行校验（2026-09-03）

### 原始需求

用户再次确认：Task5 以后固定使用 qwen3.8；3rd-review 不需要产出可认证的 terminal-clean design 结果，缺失时继续推进。

### 关键事实

虽然 compiler 的 successor 校验已允许 `parent_design_review=null`，但 `task5_runtime._identity_from_handoff()` 仍把设计 review 当成必填对象；这会让同一份新合同在正式实现 handoff 路径再次被旧代码阻断。

### 选择与理由

保留 authenticated `mini_task.implementation`、当前 snapshot/material、M401/M401-R 和五项质量硬门；只把 parent design binding 改为“null 或完整对象”。存在时继续严格校验，不存在时记录为 advisory 缺失并继续。新增回归测试覆盖 null parent 的运行校验。

### 结果与交接

聚焦测试 `21 passed`，全量测试 `856 passed, 3 skipped`，`git diff --check` 通过。当前真实 Downloads bundle 仍是已完成的 qwen3.8 运行结果；任务级 release_pending 只待 implementation review/M401/M401-R/M402 证据，不能再因为缺失 design terminal-clean 结果停住。

## D-158：执行器同步为设计可选、实现审查硬门（2026-09-03）

用户再次明确：以后统一使用 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`；3rd-review 不必产出可认证的 terminal-clean `mini_task.design`，只要能继续推进就继续。该选择不降低真实知识质量、89 条来源闭包、Reader/Audit、五项严格胜过 CompanyBrain、实现审查、M401/M401-R/M402 的门槛。

已同步当前执行器：WorkflowHub mini-task close 不再把缺失、不可用或过期的设计 advisory 当作硬阻断；只校验当前 implementation review、测试 receipt、AC trace、用户结果和后续 M401/M401-R/M402。实现审查送审材料同时内嵌本次测试 receipt 与 output 内容，避免 reviewer 只能看到外部路径和哈希。该修改属于已有用户合同的执行落实，不新增功能范围。

## D-159：当前默认语义入口统一 qwen3.8（2026-09-03）

用户要求以后统一使用 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`。本轮把仍会影响后续默认运行的 publication LLM 常量、无思考控制、身份校验提示、Task3 语义脚本默认回退、运行审计 provider 标识和当前 v1 兼容 provider 配置统一切换为 `qwen3.8`，并同步回归测试与上下文说明。旧 Task2/Task3 运行 receipt、历史合同和归档证据中的 `qwen3.6` 只作为历史事实保留，不作为当前 Task5 或未来默认入口。

这次只改变默认模型身份，不降低五项质量、89 条来源、四产品、Reader/Audit、实现审查、M401/M401-R/M402 任何门槛；设计审查 terminal-clean 仍是可选 advisory，不恢复为硬阻断。

## D-160：完成当前快照 C3/M401，保留真实发布门槛（2026-09-03）

### 原始需求

继续使用 `https://dashscope.in.whatspos.cn/v1` 的 `qwen3.8`，不再等待可认证的 design terminal-clean 结果；但五项严格胜过 CompanyBrain、89 条来源、四产品、Reader/Audit 和真实 provider 证据仍必须全部成立后才能 released。

### 关键事实

- 当前配置和 active 合同均为 Qwen `qwen3.8` 与 Jina `jina-embeddings`；active 文档、代码和测试不再把 `qwen3.6` 作为未来默认入口。
- C3 已在当前 WorkflowHub 快照 `e3b3175fb8829ef6ec9d64f6f6e60bc96600baf2`、材料身份 `cb6db04813749ba0d5068b69a240e81c8fa353be240ec245878d5a8ae81cbefa` 下重新生成，71 项 C3 owner 测试通过；C3 仍只是 fake/no-network fixture，不证明真实质量。
- M401 attempt `m401-qwen38-20260903-03` 已通过，focused 104、full 121，且 packet 的 snapshot/material 与当前 C3 一致。

### 选择与理由

不再重跑没有结果的 design review，也不把它写成通过；继续沿当前顺序推进 implementation review/M401-R/M402。这样满足用户“能继续就继续”的要求，同时不降低真正的发布门槛。

### 延期交接

当前仍为 `release_pending / not_released`：最新 authenticated implementation review 尚未形成可绑定结果，因此没有 M401-R promotion，也不能执行真实 M402。已生成的真实 Qwen3.8 产物仍可供最终五项质量和 Reader/Audit 审计，不能用 C3/M401 或绿色回归替代该审计。

## D-161：纠正当前 C3/M401 证据身份（2026-09-03）

### 原始需求

继续推进，不重跑 design terminal-clean；但当前实现、C3、M401 和后续审查不能引用过期身份或不一致的测试结果。

### 关键事实

- D-160 引用的 `e3b3175fb8829ef6ec9d64f6f6e60bc96600baf2` / `cb6db04813749ba0d5068b69a240e81c8fa353be240ec245878d5a8ae81cbefa` 是历史 C3/M401 身份，不再作为 current evidence。
- 当前代码快照是 `b2e49d7130d060a847006fcb1fec064065f4cf36`，当前材料身份为 `revision-0aec5433cf3bb54ac41a8567688dbf3d144606d26bd21d3d88cc2e126ab71a6a`；旧的 `74cd18cf...` / `4db50a...` 只保留为历史 evidence，不能继续作为 current implementation identity。
- 当前完整回归实际输出是 `857 passed, 3 skipped in 61.03s (0:01:01)`；新的 receipt 是 `quality/tests/task5-implementation-current-20260903-v6.json`，新的 AC trace 是 `quality/evidence/mini-task-ac-current/e060850b2c1944d53c56b95dd9a25cda1e5721de5d08ae555c6b81d5f0803b9a-trace-v3.json`。此前 AC trace 中的 `73.30s` 和 `100.62s` 都不是本次 current receipt 的摘要，不能继续引用。
- M401 attempt `m401-qwen38-20260903-04` 仍绑定旧 current identity，因此在新 receipt/材料身份下不能直接晋级；其 packet 只能作为历史 attempt，必须重新生成或明确保持未晋级。
- `c3-qwen38-20260903-05` 有当前 bundle 和测试输出，但缺少正式 `C3/attempt.json`，所以它还不能被说成完整 current C3 attempt。

### 选择与理由

新增当前身份记录，明确旧记录只作历史审计；修正 AC trace 的真实测试摘要并重新绑定哈希。由于当前代码没有正式 C3 writer，不能拿旧 fixture 或兼容 M401 入口冒充 current C3；后续只有补齐真实 C3 运行/证据写者后，才能生成绑定新 identity 的 M401 attempt。这样 reviewer 看到的是同一 current snapshot/material/fixture 链，而不是靠文字解释旧证据。

### 延期交接

本条不把 C3/M401 自动改成通过：正式 implementation review、M401-R 和 M402 仍未完成。design terminal-clean 继续是 advisory，不是阻塞条件；任何身份、哈希或测试摘要不一致都保持 `not_released`。

## ARCHIVE-NON-ACTIVE: 历史决策记录（非生效）

## D-102：收敛一条可执行合同

### 原始需求

同一个 Task5 只用 `/Users/Hugh/Downloads/confluence 原始数据` 完成垂直切片和 89 条全量；恢复 Qwen/Jina；按问题/场景路由、产品/模块/对象/场景/边界分类、业务答案正文、五类页面、Reader/Audit 五项逐项严格胜过 CompanyBrain；五项、证据、WorkflowHub 和发布全部通过后才能 release/close。工具要简洁、可维护，不能继续堆脚本和补丁。

### 关键事实

- 当前 raw 预检证明 89 条、4 个产品、87 条普通非空、1 条已知空源、1 条重复别名；这只证明输入闭包。
- 精确用户 V50 路径不可回查，D0-H 必须保持 blocked，不能用 v49/v47 或任何候选替代。
- 当前代码已有 `digest → compiler → providers → publisher` 和 fake regression，但 M401、M401-R、M402、真实 Downloads 产物和五项真实 artifact 都缺失。
- 当前 slice JSON 实际由 11 case 派生 27 unique source paths；旧材料仍有 14/12。
- 本轮 3rd-review 发现旧/新架构、输出树、semantic schema、authority hash 和 RunManifest 规则互相冲突。

### 选择与理由

1. 四份材料顶部 active sections 是唯一生效合同；旧内容只作历史归档。
2. 生产只保留 `digest → compiler.digest → providers → publisher.commit`；旧 runtime 暂不删除，但零生产 import。
3. slice 数量只从 JSON 派生，当前记录 11/27，不再硬编码 14/12。
4. Qwen 使用已实现、可严格校验的 `task5-semantic-output.v2`；page/question/run identities 由 compiler 派生。
5. 输出树采用 `README + Home + Audit + products + bundle/_audit`，不生成 `_digest`、modules/boundaries/knowledge/hash-only 文件；CompanyBrain public snapshot、run-result receipt 也进入同一固定 `_audit` 清单。
6. provider/语义/质量/发布失败真实落盘并保持 `not_released`；不使用 raw fallback、overlay、静态 verdict、平均分或旧 receipt。

这些选择只消除内部矛盾，不增加用户功能需求；代价是真实 provider 不可用或五项不全胜时会继续失败，但不会再把垃圾包装成完成。

### 延期交接

不延期 slice 或 89 条 full；只延期 release/close。顺序为 C0 合同一致性 → C1 source closure → C2 Qwen/Jina → C3 Reader/quality → M401 → authenticated M401-R → M402 slice→full。材料更新后必须用当前 snapshot/material 重新取得 terminal-clean design review，不能复用旧 review。

## 本轮 3rd-review 处置

实际送审的四份材料未包含 raw、CompanyBrain 或 secret。review 的 blocking/major findings 证明根因是合同并存，不是缺一个补丁；active sections 已收敛架构、输出、schema、slice 派生和 hash 责任。尚未重新取得 current terminal-clean review，所以当前仍不能进入真实 M402 或 close。

## D-103：处理当前 design review findings（2026-09-01）

### 事实

- review 仍发现 active sections 缺少生效 AC、v4 文件修改/回滚边界、空源/重复别名闭包、C3 的真实/假 provider 边界和可计算预算。
- 用户已经明确同一 Task5 必须做切片和 89 条 full；因此“缩成一个小切片、把 full 延后”不是可接受修复。
- 当前实际 slice 是 11 case、27 unique path，其中 25 个 ready、1 个 blank、1 个 duplicate alias；full 是 87 个 ready、1 个 blank、1 个 duplicate alias；质量配置实际有 12 个 projection。
- 当前 slice 唯一 authority 是 `config/archive/task5/task5-slice-cases-v1.json`，actual SHA-256=`62703a6cc06c006ea90c7be28f392cab7fd4f9918f2da384179548ca42c89cef`、canonical SHA-256=`f346b9b2bd67cf48a0fd37654e41780ed7c3f0c870ad5c9dddc04df7be80cef8`；规则是按 `cases[*].source_paths` 首次出现去重，当前派生 11 case/27 unique path/25 ready/1 blank/1 duplicate_alias。旧 14/13/12 和旧 hash 只在历史归档中保留，不得作为当前运行或 review 输入。
- 旧 V50 仍不可回查；它不能被替代，也不能作为本轮 M402 输入。

### 选择与理由

1. 保留用户确认的完整范围，并把“完整 mini-task”作为明确 accepted risk；不把范围裁小来换取形式上的 mini-task clean。
2. 在 active spec 增加 AC-v4-01…AC-v4-13，M401 只能逐条提供当前命令、输入/输出 hash、ref 和结果；历史 AC 不再是 trace 目标。
3. 在 active plan 固定生产文件 allowlist、只读边界和 inverse patch 回滚合同；没有 before/after/inverse hash 就不能把 gate 标为通过。
4. C3 只做 fake/no-network 算法验证并写 repair-gate attempt；M402 才读取 raw、CompanyBrain 和真实 provider，防止把测试 fixture 冒充真实知识。
5. M402 使用一个共享 run context，复用 slice 已有且 identity 完全相等的 source-digest receipt。按当前 25/87 ready 和 12 projection 计算，LLM 上限 115、Jina 上限 18、合计 133，retry=0；超过上限直接 blocked/calls=0。
6. known_empty 和 duplicate_alias 只有在 manifest、hash、locator、RunManifest、Audit、canonical link 全部闭合时才是可接受状态，否则 not_released；不再由实现自行解释。

### 结果与交接

上述改动只补齐已有需求的机器合同，没有增加用户功能。它们尚未通过新的 current terminal-clean design review；因此本记录状态仍是 `design_repair_required`。下一步必须用新 snapshot/material 重新做 authenticated design review；review clean 后才能继续 M401、M401-R、M402。不得因 review 的 recommendation 要求缩小范围而跳过 89 条 full。

## D-104：当前审查与 WorkflowHub 状态（2026-09-01）

最新一次独立 3rd-review 的 runtime=`3f3cc6a8-4e6c-4c86-8c67-2a4a8d12ee7f`、material_id=`f272d07b8001dea524d89d8e8ae9baba1baa2e86adc0564e6b54c47967d81e93`，结果为 `partial`：`codex/luna` 返回了 1 个 scope major、1 个 implementation-card blocking、1 个 rollback major；`pi/coding` 失败，`opencode/pax3.8` 没有 terminal result，所以该结果不是 terminal-clean 绑定证据。scope finding 按用户已确认的同一 Task5 覆盖切片、89 条、provider、五项质量和真实运行记录为 accepted risk；当前 active `tasks.md` 已补 IMPLEMENT-CURRENT，当前 active `plan.md` 已补逆补丁路径、schema、writer、命令和 reverse-apply 校验。审查完成后材料仍有修改，因此上述 material_id 不能复用。

当前 WorkflowHub `status:begin` 事实仍是 `build-code.work_status=ready`、`quality_status=in_progress`、缺 `risk_tests_fresh`、`acceptance_criteria`、`stage_end_spec_analyze`、`finding_dispositions`、`integration_review`；release 仍为 `not_released`，且 `make-decision/build-spec/build-plan/build-code/verify-code` 的旧完成记录均未绑定当前 task/worktree。没有当前 authenticated `make-decision design_preflight` handoff，就不能执行 DESIGN-CURRENT、M401、M401-R 或 M402；不能用这次 partial 3rd-review、绿色 pytest 或旧事实旁路。

## D-105：2026-09-02 设计缺口修复与重审边界

### 新的独立审查事实

- 用 3rd-review 的真实 `opencode/pax3.8` provider 送审当前设计摘要，发现四个问题：正式入口与 Task5 runtime 没有机器验收绑定；CompanyBrain observation 没有明确绑定本次 raw manifest/当前快照；Reader 逐句 raw 血缘没有 100% 的发布硬门；首次摘要包没有附四份当前材料，不能证明材料一致性。
- 随后用完整 `decision-log.md`、`spec.md`、`plan.md`、`tasks.md` 组成 hash/size 校验通过的审查包，真实 provider runtime=`b5cec36e-0d05-42b0-a54b-5bda4b71f5b9`、material=`b156dd265cd2acff7f4642d5d43ccc7519157493129e55c47743eb943d3bcde9`；provider 运行 326 秒后无终态，由人工显式取消，结果为 `cancelled`，不计设计通过。

### 选择与理由

1. 保留 `simple_cli.main` 作为唯一 public `digest` 薄适配层；用 `ENTRY-001` 证明它只能进入 `compiler.digest`，不再为“是否存在另一个 Task5 CLI”保留歧义。
2. 把正式结果统一为 Downloads run root 下唯一 `bundle/`，机器运行结果统一为 `bundle/_audit/run-result.json`；`_digest` 只留仓库历史/测试资料，避免用户同时面对两套结果树。
3. M402 每次重新生成 CompanyBrain snapshot/observation，并与同一次 raw `source_manifest_sha256`、run id、tree hash 绑定；静态 baseline 只能作为 schema/期望输入，不能直接制造 `KD_WIN`。
4. 将 Reader 每个可见业务句、五轴、页面类型、section 和 Home route 都纳入 RenderLedger，要求 100% `raw_source → block → claim → locator → Audit` 闭合；任何一条缺血缘就不发布。
5. 把四项修复直接写成 M401 的 `ENTRY-001`、`OUTPUT-001`、`BASELINE-001`、`LINEAGE-001`，先用 fake/no-network 反例证明，再接受 M401-R 和 M402；不把测试绿或 provider transport completion 当质量胜出。

### 延期交接

当前状态仍是 `design_repair_required / not_released`。完整设计审查因 provider 停滞被取消，不能进入 M401；下一步是修正后的当前四份材料重新取得 terminal-clean `mini_task.design`，再按原顺序执行 ROOT-CAUSE、C0–C3、M401、M401-R、M402。真实 slice、89 条 full、五项 CompanyBrain 对照和 Downloads 产物均不延期，也不新增 successor task。

---

## D-106：当前设计审查结果与 v4.2 收敛（2026-09-02）

### 事实

- 当前四份材料送入真实 `3rd-review` provider，runtime=`67c1c112-4cc4-45a1-b126-900debafb7c5`，material=`9517a04ffcfec797aeb04beb026cecfc5485d1344e6ede31f21bcb899267b641`；两路 provider 均返回 `overall=revise`，不能当设计通过。
- 审查明确指出：`_digest` 与 `_audit` 双路径并存；RenderLedger 有两套互斥字段且漏页面类型；CompanyBrain gap 语义不唯一；public snapshot 不在固定输出清单；`sources.jsonl` 没有行 schema；active plan/tasks 的生效边界和 fake/M402 Downloads 边界含糊；C0 authority 少列 runtime map，provider 文件名/schema 也不一致；外部 receipt 路径未定义。

### 选择与理由

1. 把 `spec.md`、`plan.md`、`tasks.md` 顶部统一升级为 v4.2，明确只有顶部当前修订生效，以下旧合同只作历史审计。
2. 唯一机器树固定为 `bundle/_audit/{run-result,run-result.receipt,evidence,sources,quality,companybrain-route-snapshot}`；`run-result` 的 schema、receipt 字段、tree 排除规则和 `sources.jsonl` 逐行序列化规则写入当前合同。
3. RenderLedger 只保留一个 `knowledge-digest-render-unit.v1`，每个 `unit_id + page_path` 恰好一行，新增 `Reader.page_type` surface；CompanyBrain 缺失统一为 `CB_MISSING/UNKNOWN`，不允许用 gap 反向制造 `KD_WIN`。
4. C3/M401 只在隔离目录做 fake/no-network；真实 Downloads 只归 M402，避免测试产物污染用户目录。

### 交接

这些修复尚未重新取得 terminal-clean `mini_task.design`，因此仍停在 `design_repair_required / not_released`。重新生成当前四份材料 packet、完成两路 terminal-clean design review 后，才允许继续 M401；M402 仍必须真实读取原始 89 条和 CompanyBrain，不能用这次审查或绿色测试替代。

## D-107：v43 审查处置与合同收敛（2026-09-02）

### 关键事实

- 当前四份材料再次由两路真实 reviewer 审查，runtime=`a8f7eac6-aef3-4c4e-b48a-8d124174f5d7`，material=`0f1dd241307e96057bf904b8bb916c13761a8ca1022b3c681e24702e0e4342d2`，结果仍为 `revise`；原始证据见 `quality/evidence/3rd-review-design-v43-20260902.json`。
- 有效缺口集中在：active spec 缺少逐条 AC trace；四产品映射、五维机器枚举、派生 surface 血缘、authority 身份、README/Audit 模板边界、CompanyBrain tree 命名、退出码和 M401-R/M402 卡片边界没有唯一写法。

### 选择与理由

1. 在 active spec 增加 AC-v4-01…AC-v4-13 的动作/证据映射，并把四个 raw 一级目录映射为稳定 `product_key/product_label`；这样 89 条闭包和产品归属可以从真实字节复算。
2. 固定 `DIM-01.route` 到 `DIM-05.reader-audit`，CompanyBrain 公共快照使用 `companybrain_tree_sha256`；这样五项比较和两棵树不会共用含义不明的字段。
3. 规定 axis/page_type/Home.route 只能引用 route ledger 的 raw `evidence_bindings`；README/Audit/Home 非 route 只能是 machine evidence 的固定模板；这样逐句血缘没有模板旁路。
4. 拆开 M401-R 与 M402，并固定 fake run root、六种退出码和唯一质量结果写者；这样实现审查、真实运行和质量裁决各自有明确责任。

### 交接

以上只是对 v43 findings 的合同修复，尚未构成 design pass。必须重新生成当前四份材料并取得 terminal-clean `mini_task.design`；在此之前不运行 M401、M401-R、M402，不把绿色 pytest 或本次 review 当成 release。

## D-108：v44 审查处置与执行边界收口（2026-09-02）

### 关键事实

- v44 只审查四份材料的 active sections，runtime=`5a39c965-e0dd-438d-825a-7ad9f92829c6`，material=`965c280256233c91d442075b458142b4e038ef6f699a0889836a9a0813483525`；两路 provider 都完成，但结果仍为 `revise`，证据见 `quality/evidence/3rd-review-design-v44-20260902.json`。
- 新 finding 不是业务范围变化：active 段里的 AC/产品表此前实际仍在历史段；fake 与 Downloads 运行根、route ledger、CompanyBrain observation hash、M401/M401-R attempt 和 host path 责任仍未唯一化。

### 选择与理由

1. 把 AC 与四产品映射放入 active spec，并把 RunManifest source row、route ledger、DIM-01…DIM-05 和 observation hash 算法写成机器合同，避免审查只看到数量口号。
2. 把 `publisher.commit` 改为接收显式 `run_root`，C3/M401 使用隔离 run root，M402 才使用 Downloads；M401/M401-R 各自保留 attempt/inverse 与 promotion view。
3. 将 raw/CompanyBrain/Downloads 的绝对路径降为 authenticated runner 的实际参数与 host receipt，合同只规定绑定、快照和脱敏规则；这保留用户指定输入，同时不把宿主路径伪装成跨环境 schema。
4. 把 Reader 标题和问题也纳入 RenderLedger，并让 manifest route rows 携带 raw evidence bindings；这样模板和派生字段不能绕过逐句血缘门。

### 交接

这些修复已通过 focused `71 passed`，但仍未取得新的 terminal-clean `mini_task.design`。下一步只重建 v45 active packet 并重审；设计通过后仍须按 DESIGN-CURRENT→ROOT-CAUSE/C0–C3→M401→M401-R→M402 顺序执行。

### 早期历史决策（非生效）

## 原始需求

本任务来自用户对 Task4/旧 Task5 结果的否定，不继承旧任务的“完成”结论。用户要求：

1. 复查原始需求、方案、实现和最终知识产物，查清为什么结果比 CompanyBrain 差。
2. 重新设计知识消化方案；目标是知识结果真正更好，不是用机械评分包装结果。
3. 评价入口必须按 CompanyBrain 的问题/场景路由；评价分类必须覆盖产品、模块、对象、场景、边界；正文必须是业务化答案页；页面类型覆盖定位、概念、操作、诊断、经验；每项都要同时检查 Reader 可见和 Audit 可回查。五项均未严格高于 CompanyBrain，就不能声称方案更好。
4. 使用标准 WorkflowHub，从 make-decision 开始，不跳阶段，不由 build-spec 补需求；Talk 用大白话讲清选项、后果和风险；decision-log 记录原始需求、事实、选择、理由和延期交接。
5. 当前任务必须在同一任务内完成垂直切片和 89 条全量，不新增后续需求或任务。
6. 经 WorkflowHub mini-task 设计审查、实现、测试和 implementation review 全部通过后，才允许使用 `/Users/Hugh/Downloads/confluence 原始数据` 做真实测试；不得凭空补知识。
7. 修复必须恢复原有 LLM 与 embedding 能力，并支持用户在 `~/.config/knowledge-digest/config.json` 配置；批准 provider 是 qwen3.6（`https://dashscope.in.whatspos.cn/v1`）和 jina-embeddings（`https://llm.paxszapp.com/v1`），v2 直接读取 `api_key`，`api_key_env` 仅作兼容回退。

## 当前纠偏记录（2026-08-21）

v28–v33 只能算 `not_released`，v34 为用户暂停后的 `cancelled`；旧报告不能证明质量或作为最终产物。D-016/D-017：KD/CompanyBrain 用同一可观察分数，Claim/Audit/RenderLedger 是前置证据；provider 缺必答内容时不得由编译器补标签或模板。D-018/D-019：先冻结合同、重算 hash、跑离线聚焦测试，再切片→同任务 89 条全量；slice-local failure 留 `not_released` 后继续，身份/预算/输入/锁/发布等 global fatal 停止 full。

Talk 已确认：独立新任务（A）、切片和 89 条全量同任务完成（A）、采用语义中间层（A）；后续为 `A、A、A`，最终 `A、B、A`。共同含义是 provider-backed 编译、五维逐 case 严格门禁、失败不伪装成功。

## 2. 关键事实（事实、推断、未知分开）

### 2.1 输入与旧结果

- 原始目录 `/Users/Hugh/Downloads/confluence 原始数据` 有 89 个 Markdown；其中 `emm for android /AE - AirViewer厂商管理.md` 为空白，仍必须在清单中出现并得到 empty/blocked 审计状态。
- 用户实际检查过的 V50 路径是 `/private/tmp/task5-reader-quality-real-v50/staging/run-c176c1a764c9616742f302e9/attempt-2d149140466c408ba6271ab7f53854de/candidate-bundle`；结果放在临时目录，且没有真实 provider/model 证据。
- 下载目录中的旧候选也不能当本任务最终结果：`/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-compiler-real-20260820-candidate-bundle`、`...-v2-candidate-bundle`。
- V50 记录了 89 条来源但运行是 `not_released`，存在 G-EMPTY-89、G-COVERAGE-89、G-SLICE-RISK 阻断；大量文件名 hash 化，modules/boundaries 主要是结构性占位，full-source/raw overlap，不能证明 Reader 质量。

### 2.2 根因假设（设计阶段未关闭）

下面的内容是基于旧结果和用户复核现象形成的根因假设，不是已经完成证据回放后的发布事实。每个假设只有在 R1/M101 绑定实际输入字节、snapshot/tree/manifest SHA、相对 locator、对应的 CompanyBrain `case × projection × dimension` 观察、合同缺口和本轮修复后，才可以从“待验证”变成“已证实”。设计审查只检查这个证据闭环是否被设计出来，不把这几行 prose 当作已完成的根因证据。

在 design terminal-clean successor 产生前，必须先执行无 provider 的 `replay_root_cause()`，并将通过的 `task5-root-cause-evidence.v2` promotion 到 `quality/evidence/task5/root-cause/root-cause-evidence.json`。每条 blocking/major observation 缺少输入 ref/SHA、locator、case/projection/dimension 配对、合同缺口或 repair mapping，或者回放结果与当前假设不一致时，当前设计保持 `not_released/blocked`；不得进入实现、M401 或真实 provider，必须新建 design snapshot/material 并重新审查。M101 后续只复核同一份 promoted evidence，不把 M101 当成第一次发现根因的地方。

- **H-001（待验证）**：旧 Task4 把可处理内容当成全量输入：88 条仍被报告 completed；空源没有成为显式状态。
- **H-002（待验证）**：抽取行直接标记为 `verified`，默认所有页面是 `procedure`，没有 Claim、KnowledgeUnit、对象/场景/边界关系的可验证中间层。
- **H-003（待验证）**：链接、图片和 locator 被清洗；混源合并没有 Claim ownership；Reader 页面正文无法逐条回查。
- **H-004（待验证）**：比较器用关键词包含、来源标题和聚合分数；大量 `N/A` 掏空分母，unknown/invalid/CB missing 没有 fail-closed，因此旧的 `better_than_companybrain` 不可信。
- **H-005（待验证）**：CompanyBrain 的可借鉴核心是 `问题/场景入口 → 产品/模块/对象 → 业务答案页 → 来源线索`、对象/关系/场景链和类型化正文；不是目录数量、人工事实字典或文件名。
- **H-006（待验证）**：当前代码仍有可复用的 `src/knowledge_digest/llm.py`、`embedding.py`、Qwen 常量和 calibration 能力；旧 Task5 方案绕开了它们，这是本次修复必须纠正的实现方向。

### 2.3 未知与证据边界

- 真实 provider 是否可用、模型是否返回合约 JSON、embedding 是否实际参与 route，只能由真实运行 receipt 证明；设计阶段不能预先声称成功。
- 不能把测试绿、目录数量、页面数量、文件存在、模型调用次数或平均分当作 Reader 质量通过。
- CompanyBrain 不是完美真值；它只提供冻结的业务入口/答案基线和对照 atoms，不能让 KnowledgeDigest 凭空补事实。

### 2.4 当前无 provider 预检事实（2026-08-25）

- 精确的 `RC-USER-V50` canonical ref `/private/tmp/task5-reader-quality-real-v50/staging/run-c176c1a764c9616742f302e9/attempt-2d149140466c408ba6271ab7f53854de/candidate-bundle` 当前只能读到 0 个普通文件（只剩空的 `audit/`、`products/` 目录）；冻结输入清单要求的是 652 个文件、111865500 bytes、snapshot=`e376886d6f6fff114c875908b5cca4fc195311fb4b38848d1bb858c66d7e5895`。因此 V50 输入已发生漂移/丢失，不能用 v49、v47、Downloads v33/v34 或研究 Markdown 替代。
- 这不是“V50 内容为空”的结论，而是“当前无法回查原 V50 内容”的事实。根因回放必须写失败 attempt、`calls=0`，不得 promotion `task5-root-cause-evidence.v2`，不得把 H-001–H-006 升格为已证实。
- raw 目录和 CompanyBrain 仍可只读访问；它们可以继续做预检和路由支持盘点，但不能补齐缺失的 V50 观察。

## 目标

目标是让真实生成的知识结果在五个用户可感知维度上逐 case 严格高于 CompanyBrain；评分只是证据，不是目标。结果必须可读、可路由、可回查，证据不足时明确不发布。

## 范围

范围是本任务内的垂直切片、89 条原始 Markdown 全量、provider-backed 语义编译、五类页面投影、Reader/Audit 发布和五维 CompanyBrain 对照。旧 Task4/Task5 只读，不改 raw corpus、CompanyBrain 或旧产物。

## 成功/失败边界

成功必须同时具备切片和全量闭包、真实 provider receipt、Reader/Audit lineage、逐 case 五维严格胜出和发布状态 `released`。缺源、空源隐藏或与冻结 manifest 不匹配、provider/embedding 不可用、证据不全、任一维非 `KD_WIN` 或输出路径不安全，均为 `not_released`/`blocked`，不能宣称完成。与 manifest 精确匹配且 Audit 闭合的已知空源记为 `known_empty`：保留在 89 条闭包中、不生成 Reader，但不单独阻断包级发布。

## 冻结的产品流程与边界

### 3.1 生成流程

`89 条 raw + 垂直切片 → 快照/来源清单 → Block 保真 → Claim → KnowledgeUnit → 产品/模块/对象/场景/边界与关系 → PagePlan → 五类页面投影 → Reader 路由 → Audit 回查 → 五维逐 case 比较 → released/not_released`。

切片是同一任务内的早期闸门；切片失败不能缩小 89 条全量范围。全量必须逐源闭包，空源、失败源和无证据状态必须保留。

### 3.2 读者流程与页面范围

`Home → 问题/场景入口 → 产品 → 模块/对象 → 场景/边界 → 业务答案页 → Reader 证据 → Audit 精确来源块`。

页面范围固定为 README、Home、产品路径下的五类业务答案页、来源状态和 Audit。产品/模块/对象/场景/边界仍是必须可见、可回放的逻辑分类，但 v1 不把它们拆成 `modules/`、`boundaries/`、`knowledge/` 或其他公开目录：Home route table 是唯一公开轴索引，Reader 路径只使用 `products/<product>/<page-type>/<readable-title>.md`。原始来源不能默认直接成为 Reader 页面；每条 Reader 事实必须有 Claim、Block、hash、locator 和公开 `audit_ref`。

### 3.3 状态与失败边界

- 运行：`declared → snapshotted → inventoried → modeled → compiled → evidence_checked → route_checked → candidate → released`；终态包括 `blocked/failed/not_released/cancelled/unavailable`。
- Claim：`extracted → normalized → linked → supported`；异常为 `conflict/unsupported/ambiguous/empty`。
- source、quality、publication 三种状态分开；`candidate` 不等于 `released`。
- 以下任一项都只能不发布：来源少于 89；空源被隐藏；关键 Claim 无精确 locator；混源 ownership 不清；页面类型未知；Reader 不可达；正文只是原文/关键词包装；provider/embedding 不可用；任一 case/dimension 为 `UNKNOWN/INVALID/TIE/CB_WIN/CB_MISSING`；guard 未通过。
- provider required 模式不得用 raw/full-source Reader 兜底；语义编译失败只进 Audit，不改写成成功页面。

### 非目标与延期

本任务不复制 CompanyBrain 事实，不修改 raw corpus、CompanyBrain、旧 Task4/Task5 产物，不以页数/行数/关键词/总分证明质量，不补原始资料外事实。数据库、向量库、后台调度、编辑工作台、在线搜索、增量同步、多语言、规模性能和生产晋级延期。

## 4. 已确认的设计选择与理由

| id | 选择 | 理由与后果 |
| --- | --- | --- |
| D-001 | 建立独立 Task5 | 防止旧任务错误完成结论污染当前真相；旧任务只读。 |
| D-002 | 同一任务做切片+89 全量 | 先用切片暴露路线问题，再完成全量；不把缺失工作延期。 |
| D-003 | `Source → Block → Claim → KnowledgeUnit → Relation → PageProjection` | 先保留事实和证据，再按问题/场景投影，避免 source→page 丢语义。 |
| D-004 | provider-backed 编译 | Qwen 只返回 typed JSON，不能直接写 Markdown；embedding 必须实际参与问题路由。 |
| D-005 | 五维逐 case 严格对照 | 维度是路由、分类、业务正文、页面类型、Reader/Audit；任一不胜出都不发布。 |
| D-006 | 显式 Audit-only source-direct；普通全量走 source-digest | 89 条逐源覆盖仍必须完整保留，但非空来源默认经 Qwen 生成 Reader；source-direct 只在明确选择审计路线时使用，不绕过任何 Reader/证据门禁。 |
| D-007 | evidence-only oracle | QualityCase、CompanyBrain baseline、source manifest、slice fixture、rollback baseline 是冻结输入；结果从真实输出重算，禁止静态答案和静态 verdict。 |
| D-008 | fail-closed | unknown、未声明/不匹配 empty、conflict、unsupported、provider failure 和 output path 不安全都必须明确失败；精确闭合的 `known_empty` 只进入 Audit，不伪造业务页，也不从 89 条分母删除。 |
| D-009 | 输出到 Downloads 新目录 | 结果可找到、可检查；realpath/软链接/输入重叠/非空复用在写入或 provider call 前拒绝。 |

## 5. 质量合同

六个 QualityCase 的每个独立 projection 都必须逐项比较 CompanyBrain：

1. 问题/场景是否能路由到正确答案。
2. 产品、模块、对象、场景、边界是否分类正确。
3. 正文是否给出业务化答案，而非大段原文。
4. 页面是否符合定位、概念、操作、诊断、经验类型合同。
5. Reader 是否可读，Audit 是否能逐条回查来源块。

每个维度使用冻结的 `atom_forms`、required claim/boundary/source refs 和独立 projection closure；KD 与 CompanyBrain 使用同一原子语义裁决。任何 `TIE`、`UNKNOWN`、`INVALID`、`CB_MISSING` 或 guard 失败都阻断发布，不能靠总分抵消。 `GENERATED_BY/generated_by` 只属于 Audit 元数据，不能作为 Reader 正文质量要求。

## 6. 当前 mini-task 设计审查状态

- 用户已明确授权 mini-task；当前阶段仍是 design review，尚未实现、测试或真实运行。
- `accepted_risk=true`：用户明确要求 provider 配置、LLM、embedding、五维评估、垂直切片、89 条全量和 Downloads 真实运行留在同一个任务内，不拆后续任务。风险补偿是 R1–R4 内部证据闸门、正式 design review、focused/full 测试、固定 M401 packet 和 terminal implementation review；这不放宽任何质量或失败门禁。
- WorkflowHub 阶段链必须可验证：`make-decision` receipt 要有 `stage/result/attempt ref+SHA/material revision/writer attestation`，并记录原始需求与 Talk 确认；`mini_task.design` 在任何 provider 前必须先消费同一 task/worktree 的 authenticated `workflowhub-identity.v1` `design_preflight` handoff，且该 handoff 必须以 make-decision receipt 为 parent。缺失、漂移、由 `build-spec` 补入的需求或未完成 preflight 都让 design review 立即 blocked，不能先审查后补链。design terminal clean 后，WorkflowHub 才能生成带 design-review refs 的 successor handoff，供 M101/M401/M402 使用；不存在把 design review 结果预先写进其自身 parent handoff 的循环依赖。
- 早期 review 已覆盖范围、provider、Claim/Block、embedding、source-direct、回滚、slice、状态码、文件边界和 M401 依赖；有效 finding 已同步到当前 v2 fixture/spec/plan/tasks，完整记录保留在 `quality/reviews/`。
- 最近一轮有效 finding 已处置：Claim-level `co_support/conflict`、duplicate alias、authenticated identity、publication-layout exact-tree/Home/禁路径；仍须用新快照重新取得 terminal clean。

### 6.1 当前处置规则

完整 finding/report/receipt 保留在 `quality/reviews/`；材料超 330 KiB 的 unavailable 不算通过。`fixed` 必须下轮 review 重验，不代表代码通过；`rejected_invalid` 只用于明确无效 anchor；`accepted_risk` 只保留用户冻结的同一 mini-task 范围，不放宽质量门。当前仍必须取得 terminal-clean design review；任何 unavailable、未处置 finding 或 snapshot/material 漂移都不能进入实现。

本节状态只描述设计 finding 处置，不代表实现、测试或真实 89 条运行成功。

## 7. 交接与退出条件

### 7.1 2026-08-21 用户复核后的当前修正

- **D-020/D-024：逐源与预算**。87 个普通 present source 各走一次 `source-digest`；1 个 SND 用确定性 replacement、不发第二次请求；source-direct 只显式审计，失败不回退 raw。多意图/证据/冲突失败只进 Audit，QualityCase 才能多投影。
- **D-021/D-027：公开入口**。Downloads 只暴露 `bundle/`、Home/Reader/Audit；Home 同时按问题和场景路由到 `product → module → object → scene → boundary → reader_path`，禁止 staging/attempt/modules/boundaries/knowledge/hash 名。
- **D-022/D-023：版本化**。semantic/source/layout/provider v2 authority 变化必须重算 hash、离线门禁和 design/implementation identity；旧 v1 只作历史。
- **D-025/D-026：材料与留痕**。design packet 只审四份材料与 contract/skill；R1/R3/M302 重算外部 authority。每次 typed response 进入 semantic ledger，绑定 request/source/contract/response-normalized hash/secret scan/projection/failure sink，才能证明 LLM 参与和可重放。
- **D-028/D-029：状态与身份**。candidate 只是中间态，质量失败统一 `not_released`；可验证 handoff 绑定 parent、snapshot/material、contract、writer，design clean 后才生成 successor，scalar identity 拒绝。

机器输入合同：审查包 host evidence 必须携带 `workflowhub-identity.v1`、parent result/attempt ref+SHA、snapshot/material、contract/semantic hashes、writer attestation 和 validation receipt；parent 还绑定原始需求与 Talk。host 先重算，缺失/漂移即 `blocked`、calls=`0`、exit=`2`。

design review 必须有 canonical terminal-clean record 和逐 finding disposition；之后按 R1–R4、focused/full、M401、implementation review 执行，全部通过才允许 M402 真实读取 raw/CompanyBrain 并写 Downloads 结果。

当前状态：`pending/design-review`。没有实现完成、测试通过、真实 provider 成功或质量高于 CompanyBrain 的结论。

## 8. 本轮 design review 纠偏记录（2026-08-24）

- **D-030**：slice 顺序固定 `preflight→execution→quality→full`；预期缺源=`not_evaluable`，local failure 留证后继续，global failure 阻断 released。
- **D-031/D-032**：单源和多源都必须有非空 `selected_source_closure_sha256`；identity/Block drift 不 replay；source-digest 过 semantic-frame/rewrite gates，`copy|unknown` 只进 Audit。
- **D-033**：3rd-review/WorkflowHub material-id 均排除 `manifest.json`/`canonical-evidence.json`，已补测试；当前仍 `pending/design-review`。
- **D-034/D-035/D-036**：runtime authority 不再靠 prose 计数，改由 `config/archive/task5/task5-runtime-authority-map-v1.json` 的 17 项纳入项和 5 项排除项作为唯一机器清单。当前 map actual=`15930a59…`、canonical=`d39c6003…`，派生 runtime contract=`8e71e2c1…`；其中 reader-quality-provider=`c0b6107a…`、provider-handshake-v3=`c15c0612…`、provider-prompt=`1e8888cb…`、source-block-claim=`02898de0…`、reader-path-relation=`c3f12166…`、machine-evidence=`6e98488a…`、publication-layout-v2=`79a4176a…`、root-cause-inputs=`387cb083…`、root-cause-evidence=`3847c679…`、semantic-output=`630d7757…`、semantic-frame=`e864fd5f…`、semantic-frame-field-closure=`d2a560e7…`、source-digest=`fc9ceeb4…`、source-not-documented=`553e71bb…`。provider-config schema 仍不计入 runtime map；identity 绑定非空 closure/source/query/prompt，预算 `115+17=132`、retry=0。
- **D-037/D-038/D-039**：slice `not_evaluable` 留证后继续 full；SND 是独立 `source-not-documented-status` diagnosis projection，使用 `snd-status-v1` 五段，不套普通 diagnosis 的 cause/action/escalation，且无 KD_WIN，guard 完整才可独立放行；external policy 缺证明则 `SOURCE_POLICY_UNVERIFIED`。
- **D-040/D-041/D-042**：`_audit` 七文件（含 public CompanyBrain snapshot）、单写者/create-only replay；material 绑定 parent full/compact/raw/Talk；embedding `top_k=7`，候选/closure/排序异常阻断。
- **D-043/D-044/D-045**：CompanyBrain host/public 分离；replay ledger owner-only 且不存 prompt/key/raw；WorkflowHub 与 Task5 contracts 分层并三方 equality。
- **D-046/D-047**：raw/Talk/worktree 进入 authenticated parent；SND 替换原 entry、不增 Qwen 请求，预算仍 `115+17=132`。
- **D-048**：design validation 必须是 task-record canonical receipt，绑定 handoff/snapshot/material/input hashes/命令/result SHA/exit=0/calls=0/writer；缺失或漂移即 blocked。
- **D-049**：M401 no-network 固定 sandbox-exec deny profile+三条负探针；runtime 另做 approved pre-socket allowlist；隔离不可用只能 calls=0。
- **D-050**：SND identity 为 `guard.source-not-documented.<source_id>`，不进 8×5；Q-DIA-01 是独立 quality projection，可共源但不合并。
- **D-051**：Repair boundary 列明 R1–R4 MODIFY、owner、before SHA、attempt/promotion/M401 ADD；未列路径、raw、CompanyBrain、旧产物和其他仓库均 STOP/read-only。
- **D-052**：M401 packet 只绑定已存在的 R1–R4/test/AC 前置；M401-R 下游消费 packet SHA 后生成 receipt，M402/implementation handoff 再绑定其 promoted ref/hash，消除循环哈希依赖。
- **D-053**：replay 不是普通内容缓存；只有真实 provider 成功 receipt、恰好一次 HTTP attempt、原始 run、source closure、compiler/parser snapshot 全部精确命中，才允许新运行 `provider_calls=0`；fake/缺证据/漂移一律 blocked。
- **D-054**：source-sensitive scanner 独立成冻结 authority，包含 raw+NFKC 双视图、完整规则、match digest 和 `SOURCE_SENSITIVE_CONTENT/SOURCE_POLICY_UNVERIFIED` 处置，并进入 runtime identity。
- **D-055**：Reader 前新增 ClaimSemanticFrame；Qwen 只产 typed page，编译器逐 Claim 生成 frame，业务化连接词可新增但主体/关系/客体/顺序/数量/条件/否定/范围必须逐字段闭合。concrete 字段必须有 raw-coordinate support span；unknown/not_applicable 使用 `{value, support_span: [], evidence_state}` 的显式空证据形状，不能满足 Reader 必答字段。
- **D-056**：`config/archive/task5/task5-reader-quality-provider-v2.json` 是 M402 运行参数 authority，actual SHA=`c0b6107a…`、canonical SHA=`48598164…`；它绑定 quality/baseline/result/observation/source-block-claim/path-relation/handshake/layout/machine-evidence/root-cause/semantic-frame-field-closure identity，并和 runtime authority map 一起进入 runtime contract，避免 M402 参数漂移。
- **D-057**：M401 packet 不反向写 M401-R；M402 固定入口另收 `M401-R-review-receipt.json`，首个 raw/provider 前校验 receipt SHA、M401 packet SHA、snapshot/material 和三方 contract identity。
- **D-058**：`relation_facts` 明确为编译器派生 ledger 字段，Qwen response 不得携带；关系 parser 的证据和负例由 R2/R3 生成、回查和评分。
- **D-059**：validation identity 分开记录 parent material hashes 与 provider-visible material hashes；requirements 文件和合同/lens 的 provider 字节必须按相对路径列 SHA，不能用 parent hash 冒充 provider projection hash。
- **D-060**：source_id 唯一采用 §10.3.1a 的 URI+snapshot+content 算法；path-only 值改名 `source_path_key`，不得混入运行/Reader/Audit/replay identity。包级 released 只由 §10.4.2a 谓词产生：87 个 source-digest Reader、1 个符合 `snd-status-v1` 的 SND diagnosis-status Reader、1 个精确 known_empty Audit 例外和全部 Reader/Audit/lineage/replay/五维/guard 硬门必须同时闭合，其他 present 缺 Reader 一律 not_released。
- **D-061**：用户 Audit 与 failure sink 分开；Audit 只留 source/block/hash/relative locator/closure/ref，sink 只留状态、reason、ledger/Audit ref/hash 和 block identity。两者都不留 raw bytes、prompt/response、凭据或 host path；Audit 未落盘时 `audit_ref=null`。
- **D-062**：有限 scanner 的 `zero_match` 不是“没有规则”证明。SND Reader 必须另有逐 Block、100% 覆盖且绑定 analyzer/source snapshot/hash 的 `semantic_zero_match_certificate.v1`；无证书只能 `unknown/Audit-only/not_released`。
- **D-063**：五维严格优势按 required atom 比较：每个 projection×dimension 必须有 atom rows、gap refs、strict improvement 和 non-regression；至少一项 CB=`absent`→KD=`present`，其他 atom 不回退；缺行/复用/漂移/unknown/forbidden 为 UNKNOWN，分数只作诊断。相关 schema/runtime hash 已重算。
- **D-064**：Source→Block→Claim 不再隐含依赖旧 parser；由 `task5-source-block-claim-contract.v1` 冻结结构块边界、完整覆盖、raw 坐标、稳定 identity 和 Claim 一对一不变量，hash 纳入 runtime/request identity。
- **D-065**：公开机器 CompanyBrain snapshot 唯一路径为 `bundle/_audit/companybrain-route-snapshot.json`；`Audit.md` 始终是人读入口，不能把 Audit 同时当文件和目录。
- **D-066**：slice 逐 projection 保存状态；聚合优先级固定为意外 local failed > 预期 not_evaluable > passed，global fatal 独立停止。两类 slice 证据同时出现时聚合为 failed，但保留两者并继续允许的 full 清单。
- **D-067**：`config/archive/task5/task5-provider-contract-handshake-v3.json` 是唯一当前 provider feasibility authority，枚举 `source-digest`、`quality-reader`、`source-direct-audit` 三类 LLM route，并单独列出 embedding route、eligible/negative/no-network cases；R1 fake LLM 必须覆盖全部三类 LLM route，R3 fake embedding 必须覆盖 `quality-reader`，未被 handshake 覆盖的 route、success 或 rejection case 都让 gate blocked。v1/v2 只保留历史，不能作为 M102/M202/M302/M401-R 输入。
- **D-068**：canonical evidence 的 provider-visible binding 必须包含最小 `workflowhub-authenticated-parent-projection.v1`：parent receipt/result/attempt ref+SHA、make-decision snapshot/material/attestation、原始需求 ref+SHA、三轮 Talk 的 choices/selection SHA、`accepted_risk` 授权依据和 writer attestation；它与当前 handoff/snapshot/material/contract identity 一起校验。只保留 parent/Talk 引用而不提供可独立核验的投影，不得视为已认证。
- **D-069**：机器证据统一受 `config/archive/task5/task5-machine-evidence-contract-v1.json`（actual=`6e98488a…`、canonical=`252118b9…`）约束。S0/S1 先写 repository evidence root 的 `task5-preflight-result.v1`；只有安全创建 output/staging 后才写 `bundle/_audit/run-result.json`（`task5-run-result.v1`）。preflight 失败不能为了写结果创建不安全目录；已创建 output 但缺失、损坏或与真实退出码不一致的 run-result 必须按 failed 处理。CompanyBrain host/public snapshot、SND zero-match certificate、raw-coordinate-map、output-lock、directory-manifest、failure-evidence、root-cause evidence 和 WorkflowHub implementation successor 均按冻结 schema、字段白名单和绑定 hash 回查，不能用“文件存在”或 prose 证明替代。
- **D-070**：本轮 design review 的语义 finding 统一处置：`bounded-lexical-v1`/`claim-lineage-v1` 只能作诊断，Reader acceptance 必须是 `semantic-frame-field-closure-v1` 的逐字段等价，不能用 `0.80` 词面覆盖率放行；unknown/not_applicable 必须使用显式空 span 结构。SND 证书只能证明“在 SND-RULE-001 的扫描范围内未发现匹配”，Reader 必须把规则版本、覆盖范围和局限性写出来，不能表达系统不存在异常。设计包不复制全部 authority 原始字节；外部 authority 的存在/schema/SHA 由 M101 baseline preflight 逐项核验，缺失或漂移在首个 provider 请求前 blocked；该 minor 风险已记录，不放宽后续 gate。
- **D-071**：外部 authority appendix 只作设计引用清单，不声称审查包已携带或验证这些文件的实际字节。M101 baseline preflight 必须逐项读取 authority path，验证存在性、schema、actual/canonical SHA、摘要和交叉引用，并在 provider/embedding/R1/M102 前以 `task5-baseline-preflight.v1` 证明；不能验证就保持 `blocked/calls=0`，不得以设计 terminal clean 替代。
- **D-072**：本轮 design review 指出三处可执行性缺口，现作硬修正而非文字解释。第一，`scripts/task5_reader_quality.py` 从 R4 owner 移入 R1，R1 负责 baseline-preflight/gate/M401/M402 CLI，R4 只能调用；因此 M101 的首个 preflight 有明确 owner 和可执行路径，R4 不再依赖一个尚未获授权的文件。第二，`raw-coordinate-map.v1`、`semantic_zero_match_certificate.v1` 和 `task5-run-result.v1` 固定落在 `bundle/_audit/`，各自写入阶段、manifest entry、消费者和十份 expected machine paths 已写入 machine-evidence/layout authority；缺失或未绑定即 blocked/not_released。第三，运行级 JSON 只认 `bundle/_audit/run-result.json`，`Audit.md` 只做人读入口，消除 Audit 文件/目录双义。上述 authority 改动必须先重算 actual/canonical/runtime hashes，再重新跑 design review；在此之前不进入实现或 provider。
- **D-073**：实现硬约束：R1/M101 先读取旧 Task4、用户 V50、当前 baseline、raw、CompanyBrain，生成并 promotion `task5-root-cause-evidence.v2`，逐行绑定“旧结果观察事实→CompanyBrain 的 case/projection/dimension 配对差异→合同缺口→修复”；`gap_atom_mapping` 必须绑定 observation/result；真实 Qwen/Jina 只经 `Task5ProviderTransport.call_once` 留 transport receipt，DNS/TLS/connect/read-timeout 等无 HTTP 响应也必须留下 create-only failure receipt；M401/M402 必须做 Home/Reader/Audit/媒体链接 surface QA；M401-R 通过后只能由 authenticated WorkflowHub adapter 生成完整 `workflowhub-implementation-successor.v1`，Task5 只读消费；闭合 `duplicate_alias` 只能继承 canonical Reader link。缺根因证据、不可比较、alias 闭包、无响应 receipt、successor 身份或上述 QA 均 STOP，规则已写入 spec/plan/tasks，尚未实现。
- **D-074**：设计审查发现 RED 预期失败和 GREEN gate failed 共用 `failed` 状态会错误阻断后续实现。现分为 `task5-red-test-receipt.v1/status=expected_failed` 与 `task5-repair-gate-attempt.v1/status=passed|failed`；GREEN 必须绑定对应 RED ref+SHA，M101 baseline-preflight 另由三步无 provider bootstrap 生成，不能互相冒充。
- **D-075**：M401 的 fake candidate surface QA 不能证明 M402 的真实 Downloads 产物。M402 在真实 staging candidate 形成后、run-result/发布前追加 R1-owned surface QA，绑定 actual candidate、R4 attempt、pre-publish/final directory manifest/tree、渲染后的入口/链接/媒体/Reader/Audit 和 cleanup；receipt 由 run-result 的 `artifact_manifest.surface_qa` 回指，缺失或漂移只能 not_released。SND 同时改成独立 `snd-status-v1` 五段，cause/action/escalation 显式 not_applicable，不要求普通 diagnosis 事实。
- **D-076**：本轮 provider 发现根因证据改版后留下了未重算占位符，并且 semantic-frame-field-closure 只有 prose 名称没有独立 authority。现已新增 `config/archive/task5/task5-semantic-frame-field-closure-v1.json`，冻结逐字段比较、允许的 Unicode normalizer、阻断 reason code 和六个负例；runtime map 从 16 项升为 17 项，root-cause v2、machine-evidence、reader-quality-provider、runtime map 和四份材料的 actual/canonical/derived hash 已重算。任何 hash 再漂移都必须重新生成 design packet，不能手改摘要。
- **D-077**：设计审查包的 provider material projection 必须由同一次 `buildReviewMaterials` 生成的实际 provider bytes 派生；parent/provider 的每个 `{key, parent_ref, parent_bytes, parent_sha256, provider_ref, provider_bytes, provider_sha256, transforms}` 必须和当前 bundle manifest 一致。临时 harness 不得复制另一套 compact 规则；若 projection 与 manifest 不一致，canonical evidence 判为 blocked，不能把 provider 的阻断误当成质量 finding。
- **D-078**：针对设计审查指出的 route 语义缺口，`task5-reader-path-relation-contract-v1` 新增 `route-descriptor.v1`。Jina 发送前必须逐字段验证 title/question/page_type 都有当前 raw Block/Claim 或 authenticated CompanyBrain observation 的 support ref，并重算 source/block/claim/closure/support hash；路径和 manifest hash 闭合但字段支撑错误、跨源或 stale locator 时 route=`unknown`、embedding calls=`0`、不得 KD_WIN。该 authority 的 actual=`c3f12166…`、canonical=`16de1b3c…`，并已级联更新 provider/runtime map/runtime contract。
- **D-079**：SND 的 producer certificate 不再被视为自证。`task5-source-not-documented-contract-v2` 新增独立 deterministic verifier，必须用当前 source snapshot 逐 Block 重算并比对 classification、hash、locator、coverage 和 result digest；SND promotion、M401 finalize、M402 release predicate 三处都必须有 verifier receipt，任何 mismatch 只能 `UNKNOWN/Audit-only/not_released`。SND authority actual=`553e71bb…`、canonical=`158de8c6…`。
- **D-080**：M101 bootstrap 改为不可跳过的机器前置。固定 `BASELINE_BOOTSTRAP` 先串联 `validate_baseline_contract()`→`replay_root_cause()`→`write_baseline_preflight()`；M101 RED、M102 GREEN 和 promotion 必须显式接收同一 baseline-preflight ref/SHA、promoted root-cause ref/SHA、snapshot/material，缺失或漂移时 calls=`0`、不写 gate receipt。该绑定已同步到 spec/plan/tasks 的命令和负例测试。
- **D-081**：本轮 design review 发现两处证据不能唯一回查：provider-visible parent projection 没有独立 `attempt_id`，且 R1 没把 runtime authority map 的完整 17-key 集合和 `source_block_claim`/`publication_layout` 明确纳入固定命令与 receipt。选择修复而不是接受风险：WorkflowHub binding 现在投影并校验 `authenticated_parent.attempt_id`、`parent.attempt_id`、handoff/validation receipt 的 `parent_attempt_id`；M102 固定命令显式带 map、source-block-claim、publication-layout、map actual/canonical SHA 和 derived runtime hash，R1 receipt 必须记录 included/excluded 集合 exact equality 与逐项 hash。M401-R schema identity 改为使用 canonical SHA `74584b624c2c672e6aa4f6d76ca98165f2a06e2fb5c40fca36b39f1807990d1a`，不再引用格式化文件 actual SHA。修复后必须重新生成 design packet；旧 review 结果只保留为审计证据，不能直接推进实现。
- **D-082**：新一轮 design review 又发现三处 gate 命令没有把既有强制 authority 传入：M102 漏 calibration manifest/artifact，M202 漏 semantic-frame-field-closure，M252 漏 quality-result-v3/source-direct-contract；同时 M402 的真实入口没有显式闭合 runtime map 的全部 authority，runtime hash 和 WorkflowHub semantic hash 也缺可复算规则。选择补齐命令和身份算法：M102/M202/M252 现在逐项传 path+actual/canonical SHA，M402 显式传 17 项 authority；runtime hash 按 map 的完整七字段、UTF-8 排序 canonical JSON+LF 派生，WorkflowHub semantic hash 只按 `buildSemanticProjection()` 的 `mini-task/design` projection 重算。未重新生成 packet 并取得新的 design review 结果前，不进入实现或真实 provider。
- **D-084**：针对最新 design review 的四个问题继续硬修正。① 删除 M102/M202/M252/M402 的手写缩减 authority 命令，统一使用 `AUTHORITY_ARGS = GENERATED_RUNTIME_AUTHORITY_ARGS(config/archive/task5/task5-runtime-authority-map-v1.json)`；runner 生成并逐项校验 17 个 included、5 个 excluded、path/schema/actual/canonical SHA、map actual/canonical 和 derived runtime，gate-specific 输入不得伪装成 runtime authority。② baseline 身份唯一从 `root_cause_inputs.RC-CURRENT-BASELINE` 派生，当前 baseline actual=`6d9098d4…`、canonical=`410182a9…`、manifest actual=`2909de6d…`、canonical=`52e86dd5…`；M101/M102/M401/M402 都必须消费同一 identity，不再各自硬编码一份 baseline。③ 冻结 source-sensitive scanner v1 的最终 LLM wire payload scope：`Task5ProviderTransport.call_once` 组装最终 JSON 后、socket 前递归枚举所有 text-bearing JSON pointer，逐字段绑定 source/block/claim、scanner SHA、payload digest 和 match digest；只扫描 Block 或中间 prompt、字段漏扫、payload 漂移都为 `SOURCE_POLICY_UNVERIFIED/calls=0`。scanner 更新后的 actual=`1253ab1e…`、canonical=`5836aa46…`，runtime map actual=`6260b361…`、canonical=`8bfb5b90…`，derived runtime=`d065b889…`。④ 设计 docs/spec/tasks/handoff harness 已同步新 identity；必须重新取得两路 terminal-clean design review，旧 review 仍只作审计，不得推进实现、M401 或真实 provider。
- **D-085**：针对本轮审查补齐多来源安全边界和 provider 可见决策留痕。`quality-reader` 的 selected-source projection 是一个原子请求：任一选中来源命中 `SOURCE_SENSITIVE_CONTENT`，或任一字段扫描不完整/漂移，整个 projection 在 socket 前失败，禁止删源、改 closure、重算身份后重试、发送部分 payload；只有不相关 route/projection 才能继续。WorkflowHub 的 decision-log provider projection 必须保留原始需求、关键事实（含未知）、Talk/设计选择及理由、成功/失败边界、非目标/延期和交接退出条件，并绑定完整父级 decision-log 的 ref/SHA；当前 review corrections 只能追加，不能替代这些业务记录。修复后必须重新生成 packet 并取得两路 terminal-clean design review。
- **D-086**：最新 review 又发现两条闭环缺口。① `source-digest` 的 manifest question/title/page type/五轴关系只能是候选，新增 source-digest route verifier：每个 Qwen 请求前从当前 Block/Claim/semantic-frame ledger 重算字段 support、单源 closure 和唯一主意图；字段无支持、歧义或漂移只进 Audit、calls=0，不生成 Reader/quality/publication。② R3 evaluator 新增唯一 actual quality-result artifact：attempt 先写 `quality/evidence/task5/actual-run/attempts/<attempt_id>/quality-result.json`，通过后 promotion 到固定 `quality/evidence/task5/actual-run/quality-result.json`；它恰好闭合六 case×八 projection×五 dimension、全部证据 ref/SHA 和最终 candidate/published tree。run-result、release predicate、surface QA、manifest 只能消费同一 promoted ref+SHA。修复后继续重跑两路 design review，未清零不得实现。
- **D-087**：本轮修复把 `source-digest-route-verifier.v1` 的机器字段、推导规则、support ref、closure/support hash、唯一主意图和六类失败码正式写入 `config/archive/task5/task5-source-digest-contract-v2.json`；当前 source-digest actual=`247fbc8f91a0e956274683fa7ef6ceba33ed306c5350a2894cd8360a34492c9d`、canonical=`5449076d85b412153b48049f13aa05796b73408c94b7a240d648cd8cb420bf03`，runtime map actual=`d7138767bcdb86128a2c7a4531def31b5a19f4a933676e9a0440a5ee4b8f40ae`、canonical=`7acc85b54b3a8402bcb0fd6a4958eeee83507d726fb628bc370aa633dfb1d649`，派生 runtime=`1e92994756ffff80a97b2e40f06e6970904e148653fb0b6f3dc7f62666cf4849`。D-086 中旧 hash 只保留为历史审计值，当前设计/runner/handoff 只接受本次重算值。质量结果也改成“candidate attempt → 原子 rename → post-rename finalize attempt → fixed promotion”的两段确认；rename/finalize/rollback 任一失败都只能 `not_released`，不能把 candidate 结果当 released。
- **D-088**：把根因回放从 M101 内部移成设计审查前的独立 `D0/root-cause-preflight`。D0 先逐项验证五个冻结输入及当前 task material；只有 `task5-root-cause-evidence.v2` 的 passed attempt 完成 promotion，`mini_task.design` 才有资格 terminal clean。M101 只消费并复核 promoted ref/SHA，不再第一次发现根因；任一输入漂移（当前已确认的 V50 漂移也包括在内）都生成 blocked attempt、`calls=0`，不改写旧 manifest、不替换输入、不进入实现。
- **D-089**：87 条普通来源必须逐条“尝试 source-digest”，但 manifest 的 question/title/page_type/五轴关系不等于语义支持。D0/R2 必须对全部 87 条生成当前 raw→Block→Claim→semantic-frame 的 `pre_provider_route_support_ledger`；只有 87/87 具备单源、唯一主意图、逐字段 support ref 才能进入成功发布谓词。缺支持的来源保留 Audit-only 并允许本次 run 真实落为 `not_released`，不得为了凑 87 个 Reader 使用文件名、目录、段落位置、整篇原文或模型猜测补路由。
- **D-090**：D0 还必须先检查当前 repair baseline 的所有 before hash。现有 `quality/evidence/task5/repair-gates/attempts/m101-preflight-20260821-01/baseline-preflight.json` 已记录 `config/archive/task5/task5-provider.example.json` 的 expected=`0140571d…`、observed=`5e782e47…`；本次无 provider 复查该路径当前实际又是 `a3f506759552c510c4572023e3cc6adaf95250f732ff4d9243304c8f50c00eb9`。这说明 baseline 证据链已漂移，不能通过“重新写一个摘要”修复；必须保留 blocked receipt，不能擅自恢复/覆盖用户文件，也不能进入 M101/实现/provider。
- **D-091**：按 D-088/D-090 直接执行 D0 命令时，当前 CLI 只注册 `run`，实际返回 `invalid choice: 'root-cause-preflight'`、exit `2`，没有生成 D0 attempt；同时运行时此前默认读取 source-digest/layout v1。本轮已补齐 provider-free `root-cause-preflight` writer，并把运行时默认合同切换为 v2，同时保留 v1 兼容读取；旧的“命令缺失”事实只保留为审计历史，不再作为当前状态。
- **D-092**：D0 writer 已按同一命令真实执行，attempt=`quality/evidence/task5/root-cause/attempts/d0-7c8d446ceddc470d8fd9bcf90d78f4ab/root-cause-evidence.json`，attempt SHA=`416862bb6a5c2904bf9836797f09dc2aebc28fa46fea09b10bf94daae3f68a88`，`status=failed`、`outcome=blocked`、provider/embedding calls=`0`。当前 raw 目录与 CompanyBrain 的文件数/字节数可回读（raw 91 个文件/1306911 bytes，CompanyBrain 1417 个文件/11883852 bytes），精确 V50 只有 0 个普通文件而冻结清单要求 652 个；baseline 的 12 个 before hash 也已漂移。D0 没有伪造 observations、没有生成 route support ledger、没有 promotion；当前不能进入 design successor/provider/released。
- **D-093**：D-089 的“provider 前先证明 87/87 五轴 route support”被本次复核正式废止。原因很简单：这会把原文没有显式标签误判成没有知识，反而挡住 Qwen 真正要做的语义消化。新顺序固定为：D0 只生成 89 条 source-scope ledger；每条可读普通来源必须尝试一次 Qwen typed compile；Qwen 之后再由 route verifier 绑定 question/title/page type/五轴到 Claim/frame/locator 和单源 closure。缺 route 支持的来源只进 Audit，87/87 仍是发布门槛而不是 provider 前门槛；V50 历史输入仍保持 blocked，不能把历史根因证据伪造成通过，也不阻塞只用当前 raw 生成一个 `not_released` 候选。
- **D-094**：合同改成 source-scope 两阶段后重新执行 D0，attempt=`quality/evidence/task5/root-cause/attempts/d0-19068ff21ded4e33890cab5ddafc7dd4/root-cause-evidence.json`，attempt SHA=`47d0b3253784c191a5c28bd440078910fec1195d3b38a85b151217126b15dcab`，仍为 `status=failed`、`outcome=blocked`、provider/embedding calls=`0`。raw 与 CompanyBrain 当前数量/字节数仍与 manifest 一致；阻塞仅来自精确 V50 的 0 文件/0 bytes 和当前 baseline 12 个 before hash 漂移。该 attempt 使用 `coverage.source_scope`，没有伪造 route 语义或 observations；它阻断历史根因 promotion，但不阻断 raw-only 的当前候选运行。
- **D-095**：真实 provider capability check 读取用户配置并请求批准 LLM endpoint 的 `/v1/models`：当前账号只返回 `qwen3.8`，`qwen3.6` 返回 HTTP 400 `Invalid model name`。选择不伪造 model identity：用户配置的 `llm.model` 改为 `qwen3.8`，代码允许的集合明确为 `qwen3.6|qwen3.8`，receipt 记录实际 model；在 qwen3.6 重新可用前，不把 qwen3.8 运行说成 qwen3.6。
- **D-096**：r4 真实 raw-only 运行证明 Qwen3.8 和 Jina 都实际被调用，输出位于 `/Users/Hugh/Downloads/KnowledgeDigest-task5-reader-quality-provider-real-20260825-r4`；91 个 Qwen 请求中 89 个成功、2 个失败，embedding 6 条 route 中 2 条通过、4 条未通过，Reader 源页已脱离整篇原文复制，但质量投影未完整、五维结果为 UNKNOWN，终态 `not_released`。因此真实调用事实不能替代五项严格胜出门槛。
- **D-097**：修复 embedding 消费边界：Jina 的 `top_k` 只做候选排序；冻结 quality case 的 `required_source_paths` 在 route 后按排名完整并入 Qwen，只有不属于冻结闭包的 top-k 候选才是 route-only。编译器现在消费 route ledger 的 `selected_source_paths`，不再从候选行的 `selected=true` 反推闭包；新增多源 closure 超出 top-k 的回归测试。对应合同把当前 `top_k=8` 定义为排序上限，required closure 不因 top-k 截断而丢失。

## 9. 当前纠偏：历史 V50 回放与 raw-only 候选分门（D-098）

### 原始需求

用户要求继续完成同一 Task5：只使用 `/Users/Hugh/Downloads/confluence 原始数据` 生成真实知识，必须使用当前配置里的 LLM/embedding，垂直切片与 89 条全量都要执行；只有五项质量全部高于 CompanyBrain、Reader 可读、Audit 可回查、Downloads 产物完整时才能宣布 released。不能因为历史候选缺失而静默改用另一个产物，也不能继续用一个缺少真实运行和质量证据的结果宣称完成。

### 关键事实

1. 冻结 `RC-USER-V50` 当前实际只有空的 `audit/`、`products/` 目录，普通文件数和字节数为 `0/0`，与冻结清单 `652` 文件、`111865500` bytes、snapshot=`e376886d6f6fff114c875908b5cca4fc195311fb4b38848d1bb858c66d7e5895` 不一致。它不能被当作“空产物”，也不能被 v47/v49/Downloads 其他目录替换。
2. `RC-CURRENT-BASELINE` 的旧 before-hash 与当前工作树存在漂移；历史 D0 attempt `d0-19068ff21ded4e33890cab5ddafc7dd4` 已真实记录 `outcome=blocked`、`provider_calls=0`、`embedding_calls=0`。因此历史根因观察尚未 promotion，不能把 H-### 假设写成已证实事实。
3. D-093/D-094 已纠正 D-088/D-090 的过宽前门：D0 只负责当前 source-scope ledger 时，不应要求 raw 原文预先有问题、page type、五轴标签；普通来源必须先尝试 Qwen，之后再由 verifier 做 route closure。历史 V50/root-cause 仍 blocked，但不阻断只基于当前 raw 89 条生成新的 `not_released` 候选。
4. 当前用户配置的 LLM endpoint 为 `https://dashscope.in.whatspos.cn/v1`，实际可用模型为 `qwen3.8`；此前 capability check 对 `qwen3.6` 返回 HTTP 400 `Invalid model name`。本轮不得把 qwen3.8 冒充 qwen3.6；实际 model、调用数和失败原因必须进入 receipt。embedding 仍按配置使用 `jina-embeddings`，密钥值不写入任何结果。
5. Downloads 中的 r30 候选确实含有 Qwen3.8/Jina 相关收据和较可读的中文 Reader 页面，但独立机器复核只发现固定 `_audit` 机器文件 `2/11`，缺 9 个；根目录、bundle README、quality.json 的 released/not_released 字段互相矛盾。静态 `KD_WIN` 数组不能替代从实际 Reader/Audit 与 CompanyBrain 重新计算的五项质量结论。

### 选择

采用“双门、同任务、同原始输入”的继续路径：

- 历史门 `D0-H`：继续保留 blocked attempt；只允许证明 V50/旧 baseline 当前不可回查，provider/embedding calls 固定为 `0`，不 promotion。
- 当前候选门 `D0-R`：只读取当前 raw 89 条、CompanyBrain 只读快照和当前实现/运行合同，生成新的 source-scope/input identity；通过后按 87 个普通可读来源逐条尝试 Qwen typed compile，并按实际 route 再使用 embedding 排序/选取。来源失败只进 Audit/failure sink，不能用目录、文件名或整篇原文补齐；任何五维非全 `KD_WIN` 仍为 `not_released`。
- 真实产物必须写入 Downloads 的新目录；不覆盖 r30 或其他既有目录。历史 V50、当前 raw-only candidate、CompanyBrain baseline 三者在 receipt 中保持不同 identity。

### 理由与后果

这样既不篡改历史证据，也不把一个已经确认丢失的 V50 当成当前 raw-only 工作的 provider 前门。后果是：历史根因报告暂时不能闭合；但当前任务可以继续做真实 LLM/embedding 编译和五项质量验证。只要实际运行、来源闭包、机器证据或任一质量维度不通过，结果就必须留下可回查的 `blocked`/`not_released`，不能为了 close 降低门槛。

### 失败边界、非目标与延期交接

- 不恢复、复制、覆盖 V50；不修改 raw、CompanyBrain、Task4 或既有 Downloads 产物。
- 不把 qwen3.8 记录成 qwen3.6；不把 provider receipt、注册可见性或绿色测试当作语义质量证明。
- 当前 raw-only 运行前仍必须补齐 source-scope/input identity、当前实现门禁、五维严格比较、Reader/Audit lineage、固定 `_audit` 机器文件和 surface QA；M401/M401-R/WorkflowHub 相关事实仍需按实际结果记录，不能假造。
- 交接给 build-code：新增 `raw-preflight`/等价 provider-free 入口并写当前 raw ledger；修复质量比较器对 CompanyBrain 缺失项的误判；补齐 11 个机器证据文件和真实 run-result；之后才在新 Downloads 目录重新跑 slice→89 full。历史 D0-H 的 blocked receipt继续保留，不作为当前候选的失败理由。

### Supersedes

本记录只在“是否允许基于当前 raw 89 条继续一个新的候选运行”这一窄范围内 supersede D-088、D-090 及其在 spec/plan/tasks 中“V50 缺失即阻断所有 provider”的表述；D-088/D-090 对历史 V50/root-cause 不可回查、不得替换输入、不得 promotion 的约束继续有效。D-093、D-094、D-095、D-096、D-097 继续有效。

## 10. 当前质量比较器纠偏与 r32 前置（D-099，2026-08-25）

### 原始需求

真实 raw-only 产物必须按“问题/场景路由、产品/模块/对象/场景/边界分类、业务化答案页、五类页面类型、Reader 可见与 Audit 可回查”五项逐格比较 CompanyBrain；五项全部严格 `KD_WIN`、LLM 和 embedding 都有真实调用证据、89 条清单与垂直切片闭合后，才允许 close/released。

### 本轮关键事实

1. r31 的真实 Qwen3.8/Jina 运行确实生成了可读 Reader，但旧质量结果不能作为最终结论：它没有 embedding 成功 HTTP batch 计数，且把“CompanyBrain 尚未被完整扫描证明”与“CompanyBrain 明确缺少 Reader 表面”混成了同一种未知状态。
2. CompanyBrain EMM 定位页确实有产品线、入口和边界语义；它没有在 Reader 正文呈现本案例要求的“相邻产品边界”表面。现改为：`meaning_status` 保留自然语义观察，taxonomy 的 `status` 只评价可见五轴分类面，business 的 `status=absent` 只在完整快照和 source-bound stage 共同证明后产生。
3. Q-POS 的候选摘要是实际答案，不是“这页用于……”目的句。现把 `decision` 作为 source-backed `direct_answer` 检查；Q-CON 同样要求直接回答，不能只靠页面用途句拿到业务答案分。
4. CompanyBrain source-bound stage 比较改为同一可见行/句的至少两个非泛化 token；只凭页面各处都出现“EMM/设备/详情”等泛词不能证明 AirViewer 边界已经被表达。新增回归测试锁住该负例。
5. 当前模拟重算（仍使用 r31 的已落盘 Reader/Audit，仅用于验证新 evaluator）得到 6 cases × 5 dimensions 全部 `KD_WIN`；这不是新真实运行，也不是 released 证据。r31 本身仍 `not_released`，因为旧 embedding ledger 缺 live transport evidence。

### 选择与后果

- 选择继续修正 evaluator 和证据合同，不用“数字高于 CompanyBrain”掩盖 `UNKNOWN`、缺调用证据或未完成的独立审查。
- 新真实运行使用新的 Downloads 目录 `...-r32`，重新调用当前 config 的实际模型（当前账号可用的是 Qwen3.8，不冒充 Qwen3.6）和 Jina；r31 不覆盖。
- 只要 r32 任一维度不是严格 `KD_WIN`、embedding/live ledger 不完整、Reader/Audit/89 条闭包或 WorkflowHub/M401/M401-R 证据不完整，仍保持 `not_released`。

### 交接

交给下一步执行：先跑 focused/full 回归，再执行 r32 slice→full；检查 `quality.json` 的六组五维 verdict、`G-EMBEDDING-LIVE`、完整 `_audit`、Reader/Audit 实际页面和 Downloads surface。之后才处理当前 WorkflowHub 缺失的 authenticated material_id、最新 phase cards、M401/M401-R 与独立 review；这些不能由 r32 的质量分数代替。

## 11. 极简架构第二次纠偏（D-100，2026-08-31）

### 原始需求

用户要求 KnowledgeDigest 最终是简洁、好维护的知识消化工具，不是继续叠加 Task5 专用脚本和补丁；真实知识必须只来自 `/Users/Hugh/Downloads/confluence 原始数据`，并且垂直切片与 89 条全量都在当前任务内完成。质量目标仍是五项全部严格胜过 CompanyBrain，不能用机械总分替代真实 Reader 质量。

### 关键事实

1. 当前工作树不是一个编译器：`digest`、Task5 runtime、Task5 provider、旧 evaluator 各走不同路径。
2. `task5_provider.py` 的 projection-specific overlay 已经承担了业务文案生成；继续添加“通用重生成”仍会保留同一种暗门。
3. v50 虽有 Qwen/Jina 调用记录，但状态仍是 `not_released`；Audit 巨大、锚点碰撞、来源集合错配、Home 结构错误、编号断裂和原文堆砌都说明“调用成功”不等于“知识质量完成”。
4. 第一轮新 3rd-review 明确指出：新方案还缺旧栈退役边界、89 条运行闭包、Jina 的真实消费者、页面身份/缺失状态和可执行迁移顺序。

### 选择

- 生产只保留 `digest → compiler → providers → publisher` 一条写入链；旧 Task5 路径不得继续作为真实入口。
- 语义权威只保留 `Evidence` 与 `ReaderPage`；增加 `RunManifest` 仅做 89 条来源、页面、路由和失败闭包，不生成业务正文。
- Jina 的 selected closure 必须进入 Qwen 业务请求，并与 Home route、ReaderPage source closure 一起落在 `RunManifest`；只记录调用不算消费。
- 取消 renderer 内部的语义重生成和所有 overlay；Qwen typed JSON 不合格就 Audit-only/not_released，重新运行由用户显式触发。
- 固定 `page_key`、来源终态和 Home sitemap，避免页面重复、缺页和失败源被空模板掩盖。

### 理由与后果

这会减少“规则越补越大”的风险，并把每个事实的责任固定在一个地方：Evidence 负责来源事实，Qwen 负责业务表达，ReaderPage 负责答案，RunManifest 负责闭包，renderer 负责排版，publisher 负责原子写入。代价是模型输出不合格时不能靠代码强行修好，真实运行可能保持 `not_released`；这是可接受的真实失败，不再把垃圾结果包装成完成。

### 3rd-review 结论与处置

本轮 3rd-review 使用 `pi/coding` 与 `opencode/v4flash`，两者均完成。共同阻断点已逐项写入 `simplified-architecture-v1.md`：旧栈退役、RunManifest、固定 page_key/缺失状态、Jina selected closure、无语义重生成、五步真实迁移。审查没有验证代码实现，因此当前仍是 `design_conditional`，不是实现通过、真实运行通过或 released。

### 交接

## D-101：3rd-review 补齐身份、清单与迁移终态（2026-08-31）

### 原始需求

在不继续增加脚本和补丁的前提下，完成同一任务：真实 raw-only 消化、垂直切片、89 条全量、Qwen/Jina 真实消费、Reader/Audit 闭环，并按五项标准严格比较 CompanyBrain；全胜前不得 release。

### 关键事实

- 第二轮 3rd-review 认为方向可行，但缺少确定迁移终态、RunManifest 严格字段、question/page/payload 哈希定义、Jina descriptor 来源约束、source state precedence 和 89 条预期枚举。
- 没有这些定义，测试无法证明“同一条来源/同一条路由/同一份 Qwen 输入”，也无法证明路由真正影响生成。

### 选择

- 迁移完成后从工作树删除旧 Task5 生产模块，不保留可导入 legacy 兼容层。
- 采用严格 `RunManifest` 作为唯一运行闭包索引；Evidence 和 ReaderPage 仍是唯一语义权威。
- 固定规范化哈希和 `source:...` / `answer:...` 页面身份；明确五种 source 状态及优先级。
- Jina descriptor 只来自 raw/Evidence，selected closure 必须逐字进入实际 Qwen payload；renderer 不再语义重生成。

### 理由

这些选择直接消除第二轮审查指出的不可验证歧义，同时不新增产品层概念：它们都是运行闭包、身份和失败边界的机器约束。代价是非法模型输出会真实失败，必须重新运行；这比把错误正文隐藏在修补器里更可维护、更诚实。

### 延期交接

不延期 89 条全量或垂直切片；只延期 release/close，直到代码、固定 Adapter 测试、真实 Downloads 产物和五项逐格比较全部有字节证据。任何字段缺失、旧模块 import、Jina 未改变 payload、Reader/Audit/source closure 不一致，均维持 `not_released`。

下一步先修改真实 CLI 入口和最小 compiler/provider/publisher 三模块，再用固定 Adapter 做单页端到端测试；测试证明新入口真实消费 Evidence、Jina selected closure 和 Qwen typed JSON 后，才继续 89 条全量与 Downloads 真实运行。任何旧模块被 import、route receipt 悬空、Reader/Audit 断链、source closure 不完整或五维非全 `KD_WIN`，都保持 `not_released`。
