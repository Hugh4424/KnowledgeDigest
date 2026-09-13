# 实现计划：task8 入口与导航（K2）

> 输入权威 = `decision-log.md`（approved）+ `spec.md`（frozen）。本计划不重新决定产品方向。
> 状态：draft（review-plan 处置后标 frozen）
> stage_outcome：`quality/evidence/stage-outcomes/build-plan/` 无外部宿主，按合同全程记
> `unavailable`（stage_outcome_missing / executor_absent），不伪造、不阻塞（同 K1/build-spec 先例）。

## 材料导航

| 章节 / 材料锚点 | 职责与摘要 | M/S/B/P 读取时机 |
| --- | --- | --- |
| `## Quick Read` | 30 秒了解 | M：开工前必读 |
| `## Code Anchors` + `## File Boundary` | 复用什么/不动什么 | S：build-code 首卡前读 |
| `## Solution Design` + `## Technical Decisions` | 怎么实现 | M：实现对应职责块时读 |
| `## Test Strategy` | 怎么测（blueprint） | M：写卡时读；B：回归时读 |
| `## Phase P1…P4`（本文件） | Phase 工程边界概要（细节在 tasks.md） | M：按 Phase 推进时读 |
| `tasks.md`（Phase P1–P4，40 卡） | 可执行 RED/GREEN 卡与执行事实区 | M：逐卡执行时读 |

## Quick Read

- **做什么**：新增 `semantic_navigation.py` 单模块——批次导航编译器（页面集收集/对账 → 三层导航生成 →
  模型描述与建议（走 K1 缓存契约）→ 四件套自检 → 全绿落盘 + manifest `navigation` 节增写；blocked 清暂存）。
- **挂接方式**：对外只暴露一个入口 `compile_batch_navigation(batch_dir: Path) -> NavigationResult`；
  K1 的 `semantic_compiler.py` 在 manifest 落盘后调用（**K1 侧集成动作，归 K1 build-code 任务**；
  K2 不修改/不新建 K1 文件，契约编程 + fixture 端到端先行——RISK-K2-5）。
- **改动面**：NEW 2 文件（模块 + 测试），MODIFY 0，DO NOT TOUCH 见 File Boundary。
- **最大风险**：K1 未研发完（fixture 先行，联调核验归 K1 集成任务 + 本计划 P4 端到端）。

## Technical Context

### Global Constraints

- Python 3.11+ / uv 管理 / src-layout；测试 `uv run --frozen pytest -q`（49 文件现状，无 conftest）。
- 基线 `c5fb2b5`：16 个既有失败（test_task2a_reader_bundle.py，K1 AC-10 口径：节点 ID 与原因逐一不变）；
  本卡新增测试不得新增失败。
- 模型通道只走项目配置约定的 Qwen（qwen3.8）与缓存契约（spec FR-GEN-003）；离线回归不得发任何网络请求。
- 批次父目录 `/Users/Hugh/Downloads/KD测试` 冻结；本卡测试一律用 `tmp_path` fixture 构造迷你批次，不碰真实目录。
- 写权白名单（spec PFACT-K2-001 六项）= 本计划唯一允许写入路径集。

## Code Anchors

### Reuse → Extend → New

| 能力 | 处置 | 锚点 |
| --- | --- | --- |
| 模型缓存 | **Reuse（契约）** | K1 `semantic_cache.py` 将冻结的接口形态（spec PFACT-K2-005：任务级固定位置、键=内容指纹+模型标识+提示模板版本+主题映射版本）。K1 未研发 ⇒ 按契约定义 Protocol 对接 + fixture 假实现；K1 落地后换真实现仅需改一处构造（DEC-003） |
| frontmatter 读写 | **Reuse** | PyYAML（项目已在用，K1 FR-PUB-001 同依赖）；不引入新依赖 |
| wikilink 解析 | **New（纯函数）** | 无既有实现服务批次内 wikilink 图遍历 |
| 批次导航生成/自检 | **New** | 旧 `navigation.py`（344 行）服务旧分类轴，结构不同，不复用（spec PFACT-K2-007；OPEN-K2-2 盘点事实） |
| manifest 读写 | **New（窄）** | 只读 K1 冻结字段 + 增写 `navigation` 节；不依赖 K1 代码 |

### 关键既有事实（build-plan 取证，step 2）

- K1 文件边界（K1 plan.md）：新链路七模块 `semantic_*.py` 全为 NEW；`simple_cli.py` 由 K1 MODIFY。
  K2 的唯一集成面 = `semantic_compiler.py` 完成产物写出后调用本卡入口（K1 侧任务）。
- K1 缓存键构成（spec FR-GEN-003 已冻结）：K2 侧实现同构键。
- 旧 `navigation.py` 函数面：`build_publication_navigation`/`_expanded_navigation`/`_topic_rows`/
  `build_topic_part_navigation`/`_validate_existing_navigation`——全部围绕旧 KB 分类轴，无一批次导航可复用单元。

## Solution Design

### Overview

```
compile_batch_navigation(batch_dir)
  ├─ load_and_validate        # manifest 必需字段校验（K1 冻结字段缺失 → blocked fail-closed）
  ├─ reconcile_pages          # 双向路径对账（spec FR-NAV-002）→ 页面集
  ├─ build_index + build_module_indexes   # 机械层（无模型）：Index.md/模块 Index + frontmatter
  ├─ generate_model_outputs   # 描述句/查询建议（缓存 → 调用 → 拒绝词表 → 非空校验）
  ├─ build_home               # Home.md（状态行+入口+建议+边界段）
  ├─ self_check               # 覆盖判定三件套 + 描述四判据 + N=10 路径抽查
  ├─ commit_or_block          # 全绿：暂存→落盘 + manifest navigation 节 + run-metrics 补记
  │                           # 任一红：清暂存 + manifest navigation_status=blocked
  └─ return NavigationResult  # 机读结果（status/计数/reasons），供 K1 汇总与测试断言
```

### Module responsibilities（单模块 `semantic_navigation.py`，目标 ≤450 行，超出拆 `semantic_nav_check.py`）

| 职责块 | 内容 | 对应 FR |
| --- | --- | --- |
| 输入与对账 | manifest 字段校验/页面集收集/双向路径对账/frontmatter 读取 | FR-NAV-002、FR 9. |
| 机械生成 | Index.md、模块 Index.md（挂载+frontmatter+模块名推断）、Home.md 机械段 | FR-NAV-001/003/004、FR-GEN-004 |
| 模型产物 | 描述句/查询建议（缓存键构造、调用、拒绝词表、非空校验） | FR-GEN-001/002/003 |
| 自检 | 图遍历覆盖判定、描述四判据、路径抽查、失败聚合 | FR-CHK-001/002/003 |
| 提交 | 暂存区管理、落盘、manifest 增写、run-metrics 补记、结果返回 | FR-NAV-001、FR-AUD-001/002、FR-CHK-004 |

### Interfaces, data, and lifecycle

- **对外**：`compile_batch_navigation(batch_dir: Path, *, cache: CacheProtocol | None = None, query_fixture: Path | None = None) -> NavigationResult`。
  `CacheProtocol` = 结构化鸭子类型（`get(key)->str|None` / `set(key, value)`），K1 缓存落地后适配。
  `query_fixture` = N=10 题目清单路径（DEF-K2-2）；None 时 AC-K2-3 oracle 记 incomplete（不失败——gate 语义）。
- **暂存区**：`batch_dir/_audit/nav-staging/`；运行开始先整体删除再重建；blocked 时整体删除。
- **manifest 二次落盘**：读取原 JSON → 增写 `navigation` 节 → 写回（保留其余节字节级不动？JSON 重写会重排格式——
  冻结：重写时 `sort_keys=False` + `indent=2` + `ensure_ascii=False`，与原格式约定一致（K1 同格式写出）；
  若解析失败（interrupted）→ SCN-K2-003 路径，不写）。
- **NavigationResult**：`{navigation_status, success_pages, blocked_sources, blocked_reasons, nav_files: [...]}`。

## File Boundary

### NEW

- `src/knowledge_digest/semantic_navigation.py`（本卡唯一实现模块）
- `tests/acceptance/test_task8_entry_navigation.py`（验收测试，RED/GREEN 七对 + 端到端）
- `tests/fixtures/task8_nav/`（迷你批次 fixture 构造器模块 + 冻结样例：含 manifest（K1 schema）、
  3-4 个 products 页面（16 字段 frontmatter）、题目清单样例）

### MODIFY

- 无。

### DO NOT TOUCH

- K1 全部规划文件（`semantic_*.py` 尚不存在；K2 侧零集成代码——挂接归 K1 build-code）。
- `src/knowledge_digest/navigation.py`（旧分类轴，K4 再评估）。
- `CONTEXT.md`/`docs/adr/`（术语登记 build-spec 已完成；不改 ADR）。
- CompanyBrain/gbrain/停摆流水线/真实语料目录。
- 既有 49 个测试文件与 16 个基线失败（节点 ID 与原因逐一不变）。

## Technical Decisions

### DEC-K2-001 — 单模块 + 契约挂接：K2 不集成 K1，K1 集成 K2

- **Problem**：K1 未研发（无 `semantic_compiler.py` 可挂），但 K2 必须与 K1 同批产出（decision-log D-002/Q1）。
- **Options**：A K2 新建自己的 CLI 入口（违反 Q1 已决方向）；B K2 写 K1 的集成代码（文件不存在，无法编译验证）；
  C **契约挂接**：K2 只暴露库入口 + 文档化挂接点，K1 build-code 在 compiler 落盘后调用（K1 侧一行集成）。
- **Selected**：C。K2 全部验收用 fixture 批次端到端（七 AC 均可离线验）；K1 集成后真实联调登记为 K1 侧任务 +
  本计划 P4 Knowledge。
- **Consequence/risk**：RISK-K2-5（fixture≠真实 K1 产物）；缓解 = manifest/page frontmatter 均按 K1 冻结 schema
  构造 fixture，且 P1 的对账层会 fail-closed 拒绝 schema 漂移。
- **Fallback**：若 K1 最终接口与本契约不符，改 `compile_batch_navigation` 的输入适配层（单点）。

### DEC-K2-002 — 缓存按 Protocol 对接，键构造同构 K1

- **Problem**：K1 缓存未实现，但描述必须可缓存（AC-K2-6）。
- **Selected**：`CacheProtocol` 鸭子类型；默认 `NullCache`（测试用假实现 `DictCache`）；键 = spec FR-GEN-003
  冻结构成（任务标识+输入内容指纹（页面字节 sha256）+模型标识+提示模板版本+主题映射版本）。
- **Consequence**：K1 落地后写薄适配（~10 行）；无 K1 时测试确定性全绿。
- **删除条件**：若 K1 缓存接口与本 Protocol 不兼容且适配层 >50 行，重开 DEC（plan-eng-review 检查点）。

### DEC-K2-003 — 模型通道经既有 provider 配置；测试全离线

- **Problem**：描述/建议生成要真实模型，但验收测试不能发网络（项目约束）。
- **Selected**：模型调用封装为 `ModelGateway` 注入接口；测试注入 `FakeGateway`（脚本化输出+空输出+坏输出三态）；
  真实 gateway 读 `~/.config/knowledge-digest/config.json`（与 K1 FR-CMP 同约定，实现时复用其读取器——
  K1 未落地前本卡自带等价只读解析，K1 落地后收敛到 K1 实现）。
- **Consequence**：离线全绿；真实调用仅人工冒烟（P4 Knowledge 记录）。

### DEC-K2-004 — DEF-K2-4 四项实现参数在本阶段冻结

- 模块文件名 `semantic_navigation.py`（同 K1 `semantic_*.py` 命名族）。
- `generated_by` 值 = `knowledge_digest_semantic_navigation.py`（同 K1 生成器命名习惯）。
- 拒绝词表 = 模块常量 `REJECTION_WORDS = {"最佳", "推荐", "最强", "完美", "绝对", "领先"}`（命中即 blocked；
  变更=代码变更；测试覆盖）。
- 正文行数 N = 30（FR-GEN-001 输入窗口）；模块名推断 = title 按非字母数字切分 → 词频最高 → 并列取字典序
  最小（FR-GEN-004 规则落地）。

## Test Strategy

（testing-system-blueprint，step 3：每 phase 风险维度/scenario/oracle/命令/evidence）

| Phase | 风险维度 | 场景（scenario） | oracle（可打破断言） | 命令 | evidence/coverage limits |
| --- | --- | --- | --- | --- | --- |
| P1 对账 | 输入 schema 漂移撕裂目录 | 正常对账/manifest 缺字段/条目↔文件双向缺失/slug=Index 冲突 | 对账通过=页面集精确；任一违例=blocked 且 reason 精确 | `pytest tests/acceptance/test_task8_entry_navigation.py -k "reconcile or fixture"` | 4 对 RED/GREEN；limits：不测 K1 真实写出（fixture） |
| P2 机械生成 | 挂载错/frontmatter 违契约/模块名推断不确定 | 挂载树/frontmatter 16 字段/模块名并列/空模块 | 三件套字节快照（确定性模板）；frontmatter 字段断言 | `-k "build or module_title or home_mechanical"` | 快照+字段断言；limits：不验模型产物 |
| P3 模型产物 | 缓存键错/空输出/拒绝词/超预算 | 缓存命中免调/缓存写回/空输出 blocked/拒绝词 blocked/双跑一致 | 缓存键构成断言；四判据输入前置（非空/词表） | `-k "cache or model_output or suggestion"` | FakeGateway 三态；limits：不测真实网络 |
| P4 自检端到端 | 漏孤儿/描述同质/路径超跳/blocked 清场 | 覆盖判定三件套/四判据逐条/10 题抽查/manifest 增写/暂存清理 | 每对 RED 精确失败信息 + GREEN 0；NavigationResult 断言 | `-k e2e` + 全量 `pytest -q` | 七对 RED/GREEN + 16 基线失败不变断言 |

- RED/GREEN 纪律：每对同一 gate 命令、同一 oracle identity；RED 在 GREEN 前提交（同 K1）。
- 基线守卫：全量跑含 `--deselect` 无关项，断言 16 失败节点 ID 集合不变（借 K1 AC-10 口径）。

## Rollback and Recovery

- 本计划零 MODIFY、零删除 ⇒ 回滚 = 删 3 个 NEW 路径 + 还原 git。
- 每 Phase 独立可回滚（文件不跨 Phase 重叠）。
- **Engineering Risk Handoff**：
  - RISK-K2-5（K1 未落地）→ P1 fixture 构造器把 K1 schema 冻结为代码常量；K1 落地后跑一次真实批次对照
    （人工冒烟，记录在 P4 Knowledge）。
  - DEC-K2-002 适配层超 50 行 → 重开决策（plan-eng-review 检查点）。
  - DEF-K2-2（题目清单）未关闭 → build-code STOP（gate，spec 第 12 节）。

## Implementation Order

P1 → P2 → P3 → P4 严格串行（同模块内职责块依数据流：对账→生成→模型→自检）。

## Dependencies and Parallelism

- 无并行：单模块单文件，四个 Phase 顺序执行。
- 外部依赖：K1 冻结 schema（spec PFACT-K2-002/003，已冻结）；题目清单（用户确认，gate）；
  K1 缓存/模型 gateway（DEC-K2-002/003 已解耦）。

## Requirement and Verification Traceability

| FR | Phase | 测试 | AC |
| --- | --- | --- | --- |
| FR-NAV-001/002 | P1/P2/P4 | reconcile_*、e2e_happy | AC-K2-1/4/5 |
| FR-NAV-003/004/005 | P2/P3 | build_home、frontmatter_* | AC-K2-4/5/6 |
| FR-GEN-001/002/003 | P3/P4 | gen_*、e2e_rerun_bytes | AC-K2-2/6 |
| FR-GEN-004 | P2 | module_title_* | AC-K2-4 |
| FR-CHK-001/002/003/004 | P4 | check_*、e2e_block_* | AC-K2-1/2/3/5 |
| FR-AUD-001/002 | P4 | e2e_manifest_nav、metrics_* | AC-K2-5/6 |
| 写权白名单 | P4 | e2e_write_audit | AC-K2-7 |

双向闭合：13 FR 簇 → 4 Phase → 7 AC，无悬空。

## Governance Synchronization Matrix

| 项 | 状态 |
| --- | --- |
| decision-log 12 D 条目 | 全部落 spec/plan，零重开 |
| spec 13 FR 簇 | 全部落 Phase/测试 |
| AC-K2-1…7 | 全部有 oracle；2 子项 gate 诚实标注 |
| NG-001…008 | 零违反（File Boundary DO NOT TOUCH 对齐） |
| DEF-K2-1 关闭（术语登记） | build-spec 已完成（CONTEXT.md 四术语） |
| DEF-K2-2/4 | 本计划冻结 4 项参数（DEC-K2-004）+ 题目清单 gate 待用户 |
| DEF-K2-3（CB 入口合并） | 归 K3，本计划不触碰 |
| DEF-K2-5（K1 manifest page_path） | P1 fixture 按冻结 schema 构造；K1 侧对齐登记 K1 build-code |

## Constitution Check

- 不丢内容/可追溯/失败不伪装：blocked 必产 manifest 记录 + 显式 reason（FR-CHK-004）✓
- 写权受限：六项白名单 + 测试写路径审计（AC-K2-7）✓
- 可重复：缓存键不含运行级字段；双跑字节一致有 oracle ✓
- 同构：16 字段零新增；ADR 0013 授权不消费 ✓
- 无投机能力：无调度/向量库/服务化；单模块给出行数拆分条件 ✓

## Phase P1 — 输入对账与 fixture

Goal：manifest 输入校验 fail-closed + 双向路径对账可用；fixture 把 K1 冻结 schema 固化为代码。
工程边界：仅 `semantic_navigation.py` 的对账职责块 + fixtures 包；测试先行（T001–T006）。
依赖：无（首 Phase）。细节与 RED/GREEN 卡见 tasks.md。

## Phase P2 — 机械生成（无模型）

Goal：三件套机械层确定性生成（Index/模块 Index/Home 机械段 + frontmatter 契约 + 模块名推断）。
工程边界：仅生成职责块；零模型调用；快照断言。依赖：P1 页面集。细节见 tasks.md。

## Phase P3 — 模型产物（缓存/描述/建议）

Goal：缓存协议对接、描述/建议生成、拒绝词表与非空校验、预算记账。
工程边界：仅 model 职责块；FakeGateway/DictCache 离线全链。依赖：P2 生成槽位。细节见 tasks.md。

## Phase P4 — 自检、状态增写、端到端

Goal：覆盖判定三件套 + 四判据 + 路径抽查 + blocked 矩阵 + commit fail-closed 顺序 + 生产接线。
工程边界：自检职责块 + commit_or_block；全 AC 闭环。依赖：P1–P3。细节见 tasks.md。

## 阶段执行记录（build-plan）

### read-current-materials（step 1）

已读 decision-log.md（approved）+ spec.md（frozen）+ K1 plan.md 文件边界/技术决策（挂接契约来源）。

### conditional-spec-research 执行记录（step 2）

主会话直读（量小）：K1 File Boundary/NEW 清单与 DEC-001（K2 挂接面 = semantic_compiler.py 落盘后调用）；
旧 navigation.py 函数面（不复用确认）；测试布局（49 文件/无 conftest/16 基线失败口径）。事实固化进
Code Anchors 与 Global Constraints。正式 research receipt 无 build-plan 公共发布通道（同 build-spec 先例），
记未供给，不影响本计划。

### testing-system-blueprint（step 3）

见 `## Test Strategy` 表：4 Phase ×（风险维度/场景/oracle/命令/evidence/limits）齐备；
无测试执行在本阶段发生。

### spec-plan（step 4）

本计划主体（Solution Design/File Boundary/DEC/Order/Dependencies/Traceability）即本步骤产物。

### simplicity-guard 四阶梯（step 5）

- 导航生成/自检：P3 新建（无既有覆盖；旧 navigation.py P1 不复用）。
- 缓存/模型 gateway：P2 契约复用（DEC-K2-002/003 Protocol 对接，K1 落地后薄适配）。
- 分批/原子发布/向量库/前端：P0 不成立（spec NG）。
- 查询建议：P3——decision R2-Q3 用户显式选择，非发散；oracle 已补（AC-K2-4）。
- 结论：无 scope creep；三处新增均给删除条件（模块拆分条件/适配层 50 行线/DEC 重开条件）。

### plan-eng-review 执行记录（step 6）

- 需求→任务：13 FR 簇 → P1-P4 → 七 AC，Traceability 双向闭合。
- 模块归属：单模块四职责块，Phase 依数据流串行；文件零重叠。
- 接口锚点：CacheProtocol/ModelGateway/NavigationResult 三接口签名冻结于 DEC-K2-002/003 + Solution Design。
- 状态/失败路径：SCN-K2-003 分态（blocked 可写/interrupted 不写）在 P1+P4 覆盖；零页面在 P1 对账层。
- 依赖序：P1→P2→P3→P4 无环；零并行声明。
- RED/GREEN：七对同命令同 oracle，RED 非零/GREEN 0（写卡时逐对落实）。
- 回滚：删 3 NEW 路径即回滚；不可逆操作无。
- 实现效果：消费方 = K1 semantic_compiler（一行挂接，K1 侧任务）+ 测试直调。

### test-routing 预判（step 7）

全部任务 = Python 模块级行为（无 UI/网络接口/数据库/部署），按 test-routing-advisor 判类标准预判
`feature`；独立顾问正式判类结果回填任务卡 test tier 字段。

### spec-tasks（step 8）

见 `tasks.md`（Phase P1–P4 任务卡，含 blueprint/route/status/执行事实字段与 build-code STOP gate）。

### review-plan（step 9）

wh-review build-plan surface 真实调用一轮：公共结果 `available`（outcome=completed；pi/v4flash
OUTPUT_INVALID 按事实记录；有效 = kimi/coding、antigravity/flash、codex/luna）。18 条 finding，
2 blocking + 14 major + 2 minor，全部 actionable。逐条处置（去重后 13 项），全部 `fixed`，零静默丢弃：

| finding | 处置落点 |
| --- | --- |
| B-1（blocking：gate 被降级为"仅真实批次"，spec F-4 要求首任务卡前置） | tasks.md 头部 gate 恢复为 T001 开工前置（DEF-K2-4 已由 DEC-K2-004 关闭，gate 只剩 DEF-K2-2） |
| B-2（blocking：生产接线不可执行——默认 NullCache/None fixture/K1 集成未定义） | Quick Read 接线契约冻结（三依赖显式注入无默认）+ 新增 T021 生产接线测试 + K1 集成任务明确定义 |
| B-3（major：plan 概览 navigation.status 旧命名残留） | 统一 navigation_status |
| B-4（major：AC-K2-6/7 测试卡 e2e_rerun_bytes/e2e_write_audit 只在追溯表） | 新增 T017（双跑字节）/T018（写路径审计） |
| B-5（major：SCN-K2-002 部分成功 M>0 无任务卡） | 新增 T019（三数对账） |
| B-6（major：T016"manifest 字节不变"与 JSON 重序列化矛盾） | oracle 改语义相等（冻结字段值比对）；字节稳定归 K1 真实批次集成检查点 |
| B-7（major：T012 ≤8 上限复活，F-5 已删） | 删 ≤8，对齐"≥3 非空" |
| B-8（minor：模块行数 450 vs spec 500 不一致） | 对齐 spec 500，拆分文件名登记为计划细节 |
| B-9（minor：Quick Read NEW 2 文件/七对 RED 与正文不符） | 同步为 3 路径/15 对 |
| B-10（major：Test Strategy `-k gen`/`-k build` 无匹配选择子） | 改为实际选择子（`cache or model_output or suggestion` 等） |
| B-11（major：复合 -k 表达式未加引号） | 全部加引号 |
| B-12（major：blocked 态端到端覆盖不全） | 新增 T020 blocked 矩阵（七情形参数化） |
| B-13（major：commit 运行时写失败无恢复定义） | commit 顺序冻结 fail-closed：导航→metrics→manifest 最后；写失败不写 manifest，K3 凭缺节拦截 |

### main-agent-disposes-findings（step 10）

上表 13 项全部 fixed 并回写 plan.md/tasks.md（本轮提交为最后修订）。本步骤是最后作者修订：此后
plan/tasks 仅由 build-code 按卡执行更新执行事实字段，不再改设计。

### final-spec-analyze（step 11）

外部 strict report-only analyzer 无宿主（stage_outcome 根因同前），主会话对当前五输入 packet
（decision-log / spec / plan / tasks / AC 表）做最终一致性核对：

- 命名一致性：navigation_status 全链一致（spec/plan/tasks 逐文件 grep 零残留 navigation.status）。
- gate 一致性：spec §12 F-4（两 DEF gate）→ DEF-K2-4 关闭证据 = plan DEC-K2-004 → tasks 头部
  gate = DEF-K2-2 单一项 + T001 前置。三层一致。
- 追溯闭合：13 FR 簇 → P1–P4 → 21 任务卡 → 7 AC；review 新增的 T017–T021 已入追溯
  （AC-K2-6/7/5 各有 ≥1 机器 oracle）。
- 命令有效性：tasks 全部 -k 选择子有对应测试名（T001–T021 逐一核对）；复合表达式带引号。
- 无"做完仍不能交付"缺口：blocked 全场景有 T020 矩阵；部分成功有 T019；生产接线有 T021。

结论：plan/tasks 可进入发布。

### publish-plan-result（step 12）

（大白话交接与 confirmation 见会话发布动作 + `quality/confirmations/`。）

### stage-reflection（step 13）

无 authenticated stage outcome 原件（step 11 stage_outcome 即 unavailable），reflect 缺判断输入，
按合同记 `unavailable`，不复盘不伪造；原 stage 状态保留。

### main-agent-disposes-findings / final-spec-analyze / publish-plan-result / stage-reflection（steps 10–13）

（回填处。）
