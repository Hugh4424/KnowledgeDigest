# 任务清单：task8 入口与导航（K2）

> 输入权威 = decision-log.md（approved）+ spec.md（frozen）+ plan.md（本文件姊妹篇）。
> RED/GREEN 纪律：每对同一 gate_cmd 与 oracle identity；RED 预期失败先行提交，GREEN 修到 exit 0。
> 权威执行命令 = `uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k <gate>`
> （gate 为各卡 gate_cmd 的 -k 选择子；全量回归 = `uv run --frozen pytest -q`）。
> **build-code 开工 gate（spec 第 12 节 F-4 处置，STOP 条件）**：**build-code 的第一个任务卡（T001）
> 开工前，DEF-K2-2（十条查询路径题目经用户确认）必须关闭**。DEF-K2-4 已由 build-plan DEC-K2-004
> 冻结关闭（四项参数），gate 只剩 DEF-K2-2 一项。review 指出本文件曾将 gate 降级为"仅真实批次任务"——
> 已纠正：fixture 离线开发也属于 build-code 实现工作，同样受 gate 前置。

## 材料导航

| Phase | 内容 | 任务 |
| --- | --- | --- |
| P1 | 输入对账与 fixture | T001–T004 |
| P2 | 机械生成（无模型） | T005–T008 |
| P3 | 模型产物（缓存/描述/建议） | T009–T012 |
| P4 | 自检、状态增写、端到端 | T013–T021 |

## Phase P1 — 输入对账与 fixture

### Goal

manifest 输入校验（fail-closed）与页面集双向路径对账可用；fixture 构造器把 K1 冻结 schema 固化为代码。

### Files

- `tests/fixtures/task8_nav/__init__.py`（`make_batch(root, pages, blocked=[]) -> Path`：写 manifest/
  products 页面（16 字段 frontmatter）/README/_audit 骨架）
- `tests/fixtures/task8_nav/manifest_sample.json`（冻结样例）
- `src/knowledge_digest/semantic_navigation.py`（本 Phase 落：load_and_validate + reconcile_pages）

### Tasks

- T001【RED→GREEN】`test_reconcile_happy` — 正常批次（3 页面/2 product/2 section）对账通过，
  页面集精确等于 manifest 条目集；gate：`-k reconcile_happy`
- T002【RED→GREEN】`test_reconcile_manifest_missing_field` — manifest 缺 `run_status`/`阻塞项`/
  `来源台账` 任一 → blocked，reason 含精确字段名（SCN-K2-003 fail-closed）；gate：`-k reconcile_missing_field`
- T003【RED→GREEN】`test_reconcile_bidirectional` — 条目有文件无 / 文件有条目无 / slug=`Index` 冲突
  三态各自 blocked 且 reason 精确（`nav-page-manifest-mismatch`）；gate：`-k reconcile_bidirectional`
- T004【GREEN-only】`test_fixture_determinism` — fixture 构造器两次构造同输入 → 全字节一致
  （frontmatter created/updated 固定值）；gate：`-k fixture_determinism`

### Verify

`uv run --frozen pytest -q tests/acceptance/test_task8_entry_navigation.py -k "reconcile or fixture"` 全绿；
RED 快照留 git 历史。

### Knowledge

manifest 样例严格按 K1 FR-AUD-004 + 本卡 FR-AUD-001（navigation 节由 K2 增写、不在输入 fixture 中）。
K1 页面条目冻结字段 = `page_path`（DEF-K2-5）。

### STOP

发现需修改 K1 冻结 schema 才能继续 → 停止并回 make-decision；fixture 中出现真实语料路径 → 停止。

### Done

对账层四行为有测试钉住；NavigationResult 骨架类型存在。

### Risks and rollback

删本 Phase 新增函数与测试即回滚；fixture 与 K1 真实 schema 不符的风险 = RISK-K2-5，P4 Knowledge 记录对照计划。

## Phase P2 — 机械生成（无模型）

### Goal

三层导航的机械层确定性生成：Index/模块 Index（挂载+frontmatter+模块名推断）与 Home 机械段。

### Files

- `src/knowledge_digest/semantic_navigation.py`（build_index + build_module_indexes + build_home 机械段）

### Tasks

- T005【RED→GREEN】`test_build_mount_tree` — Index.md 按 product 分节、节内按 section 升序列模块总览链接；
  模块 Index 条目含每页 wikilink+占位描述槽（描述在 P3 注入）；gate：`-k build_mount_tree`
- T006【RED→GREEN】`test_build_frontmatter_contract` — 三件套 frontmatter 16 字段精确断言：
  tier 分层（Home/Index=1、模块=2）、title（Home="批次入口"/Index="知识索引"/模块=推断值）、
  `source: batch`、`created/updated`=页面值最早/最晚、`tags:[company,navigation]`、
  `generated_by: knowledge_digest_semantic_navigation.py`；gate：`-k build_frontmatter`
- T007【RED→GREEN】`test_module_title_inference` — 词频最高/并列字典序最小/单页模块三态；
  同输入两次推断结果一致（确定性）；gate：`-k module_title`
- T008【RED→GREEN】`test_home_mechanical_sections` — Home.md 批次状态行（`nav: success_pages=N
  blocked_sources=M`）+ 快速入口（Index 链接+product 锚）+ 使用边界段（临时对照产物声明）齐备；
  查询建议槽存在但 P3 前为空标记；无时间戳/批次名；gate：`-k home_mechanical`

### Verify

同目录 `-k "build or module_title or home_mechanical"` 全绿；字节级快照（snapshot 文件随测试入库）。

### Knowledge

确定性模板 = f-string 固定布局；任何"看起来聪明"的排序都禁用（只 section slug 升序）。模块名切分
正则 `[^0-9A-Za-z\u4e00-\u9fff]+`（保留中文字符为词）。

### STOP

需要新增第 17 个 frontmatter 字段 → 停止（spec FR-NAV-005 硬边界）；需要对页面文件写任何内容 → 停止。

### Done

无模型时三件套可生成且字节确定（T008 的 GREEN 即 SCN-K2-001 机械半段）。

### Risks and rollback

删生成函数即回滚；快照格式变更=测试变更，不动产物契约。

## Phase P3 — 模型产物（缓存/描述/建议）

### Goal

描述句与查询建议的生成管线：缓存协议对接、拒绝词表、非空校验、预算记账。

### Files

- `src/knowledge_digest/semantic_navigation.py`（generate_model_outputs：键构造/调用/过滤/校验）

### Tasks

- T009【RED→GREEN】`test_cache_key_contract` — 键构成 = spec FR-GEN-003 五要素（任务标识/输入内容指纹/
  模型标识/提示模板版本/主题映射版本）逐项断言；改页面一字节 → 键变（负例）；批次目录名/运行时刻不进键；
  gate：`-k cache_key`
- T010【RED→GREEN】`test_cache_hit_no_call` — DictCache 预置命中 → gateway 零调用、输出=缓存值；
  miss → 调用一次并写回；第二次运行同输入零调用（AC-K2-6 的调用面）；gate：`-k cache_hit`
- T011【RED→GREEN】`test_model_output_validation` — FakeGateway 三态：正常 / 空串 / 拒绝词
  （"最佳"）——空与拒绝词 → blocked（reason=`model-output-missing`/`model-output-rejected`）；
  无重试（一次即决）；gate：`-k model_output`
- T012【RED→GREEN】`test_suggestion_count_and_metrics` — 建议 ≥3 且非空（上限不加——spec review F-5 已删）；run-metrics 补记
  K2 调用数（计划=页面数+1，实际含拒绝后不再重试 ≤ 计划）；gate：`-k suggestion_metrics`

### Verify

同目录 `-k "cache or model_output or suggestion"` 全绿；FakeGateway 三态脚本在 fixture 模块内。

### Knowledge

真实 gateway 解析 `~/.config/knowledge-digest/config.json`（与 K1 同约定）；测试零网络。拒绝词表=
模块常量（DEC-K2-004），变更=代码变更。提示模板版本 = 本模块内常量 `PROMPT_VERSION`（变更即失效全量缓存）。

### STOP

需要发真实网络请求才能 GREEN → 停止（改 FakeGateway）；需要改 K1 缓存文件 → 停止（K1 未落地，
只按 Protocol 对接）。

### Done

模型产物在离线环境全链路可验；四判据的输入前置（非空/词表）在此层完成，P4 只验跨页面判据。

### Risks and rollback

删 generate_model_outputs 即回滚；缓存键构成变更 = spec 变更，须回 make-decision 修订 FR-GEN-003。

## Phase P4 — 自检、状态增写、端到端

### Goal

覆盖判定三件套 + 描述四判据 + N=10 路径抽查 + 暂存清理 + manifest 增写 + 端到端七 AC 闭环。

### Files

- `src/knowledge_digest/semantic_navigation.py`（self_check + commit_or_block）
- `tests/fixtures/task8_nav/query_fixture_sample.json`（题目清单样例 10 题，格式
  `[{id, query, target_slug}]`；真实清单经用户确认替换，DEF-K2-2）

### Tasks

- T013【RED→GREEN】`test_check_coverage_three` — 三件套：①漏挂一页（孤儿）②死链（模块 Index 手工塞
  坏链接，fixture 直接写暂存文件模拟）③导航指向 manifest 外页面；各reason 精确；gate：`-k check_coverage`
- T014【RED→GREEN】`test_check_description_criteria` — 四判据逐条：重复=0（两篇同描述）/骨架≥3/
  问句模板≥3/空描述（FakeGateway 返回空已 P3 blocked——本条验"暂存区残留空槽被检出"路径）；
  gate：`-k check_description`
- T015【RED→GREEN】`test_path_sample_and_gate` — 题目清单 10 题：目标可达且 ≤3 跳；
  一题超 3 跳构造 → blocked；清单缺失（fixture=None）→ AC-K2-3 记 incomplete 不失败（gate 语义）；
  gate：`-k path_sample`
- T016【RED→GREEN】`test_e2e_manifest_and_cleanup` — 端到端：happy → ①三文件落盘 ②run-metrics 补记 ③manifest navigation 节
  最后写出（commit 顺序断言：导航先于 manifest——review B-13 fail-closed，manifest 缺/不一致即被 K3 拦截）
  {generated_ok, success_pages, blocked_sources:0, blocked_reasons:[]} + 暂存区清空；
  任一自检红 → 导航零落盘 + navigation_status=blocked + reasons + manifest 未触及字段语义相等
  （解析后比对冻结字段值——review B-6：JSON 重序列化不保字节级，字节稳定归 K1 真实批次集成检查点）+ 暂存区清空；SCN-K2-006 零页面 → blocked+`zero-page-batch`；SCN-K2-003 interrupted（manifest 损坏）
  → 不写 manifest、显式报告；gate：`-k e2e`

### Verify

`-k "check or path or e2e or rerun or audit or partial or blocked"` 全绿 → 全量 `uv run --frozen pytest -q`：
新增文件全绿 + 16 个基线失败节点 ID 集合不变（K1 AC-10 口径借用）。

### Knowledge

真实批次人工冒烟（K1 落地后）：跑一次 `/Users/Hugh/Downloads/KD测试` 真实批次，对照 fixture 行为，
结果记录在案（RISK-K2-5 关闭动作）。

### STOP

自检需要人工翻页判定 → 停止；blocked 情形 manifest 无法写出 → 停止（interrupted 除外，其契约=不写）。

### Done

七 AC 全部有机器 oracle 且端到端可验；NavigationResult 返回面闭合。

### Risks and rollback

删 self_check/commit_or_block 即回滚；清单样例 ≠ 用户确认清单时，P4 仅 T015 记 incomplete（gate 生效）。

### Tasks（P4 续）

- T017【RED→GREEN】`test_e2e_rerun_bytes` — 同输入双跑：三导航文件字节完全一致（AC-K2-6；FakeGateway
  脚本化相同输出 + DictCache 保证第二次零调用）；gate：`-k rerun`
- T018【RED→GREEN】`test_e2e_write_audit` — 写路径审计（AC-K2-7）：测试桩记录运行期全部写操作 →
  批次目录外零写入；批次目录内仅白名单六项（PFACT-K2-001）；暂存区在终态必被清空；gate：`-k audit`
- T019【RED→GREEN】`test_e2e_partial_success` — SCN-K2-002：fixture blocked=[2 个来源] → Home 状态行
  `blocked_sources=2`、navigation 节三数对账（success_pages==页面集、blocked_sources==K1 阻塞清单长度、
  Home 行==manifest）；gate：`-k partial`
- T020【RED→GREEN】`test_e2e_blocked_matrix` — blocked 态契约参数化（review B-12）：模型不可用/
  空输出/拒绝词/K1 run_status=blocked/对账违例/frontmatter 缺字段/零页面 七种情形，逐一断言
  navigation_status=blocked、reasons 精确、导航零落盘、暂存清空、未触及 manifest 字段语义相等；
  gate：`-k blocked`
- T021【RED→GREEN】`test_production_wiring` — 生产接线（review B-2）：按 DEC-K2-003 从用户 config
  构造真实 ModelGateway（构造期零网络请求）、按 DEC-K2-002 构造 CacheProtocol 适配点、K1 集成调用面
  签名断言（cache/gateway/query_fixture 三依赖显式注入、无默认 Null/None）；gate：`-k wiring`

## 跨 Phase 事实

- test tier（test-routing 预判，step 7）：全部 `feature`（Python 模块级行为，无 UI/网络/DB/部署）。
- 当前状态：P1–P4 均已规划未执行（build-code 阶段按 RED→GREEN 逐卡执行；开工前置 = DEF-K2-2 gate）。
- 执行事实字段（build-code 填）：attempt/gate stdout/exit/receipt。
