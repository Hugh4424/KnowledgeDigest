# 实现计划 · task9-release-safety-query-acceptance（K3）

> 本文件把 `decision-log.md`（approved）与 `spec.md`（frozen）落成可执行工程计划；不改方向、不改规格口径。下一棒：build-code。

## 材料导航

| 锚点 | 用途 | 读取时机 |
| --- | --- | --- |
| `decision-log.md#已选方向` / `#验收标准` | 方向与 AC 原文 | 判边界时 |
| `spec.md#5. 功能需求` | 29 条 FR 精确契约 | 实现逐条 FR 时 |
| `spec.md#11. 验收标准` | AC oracle/通过/失败 | 写 gate 与 oracle 时 |
| 本文 `Solution Design` / `File Boundary` / `Technical Decisions` | 工程方案唯一权威 | build-code 全程 |
| `tasks.md` | plan-task.v4 卡与执行事实区 | 逐卡执行 |

## Quick Read

- **建什么**：三个新 CLI（`knowledge-digest-publish` / `-rollback` / `-accept`）+ 两个新模块（`kb_publish.py` 发布通道、`kb_accept.py` 验收判定器）+ 一套 fixture。
- **核心机制**：库外同级隐藏目录（sidecar）承载 versions/staging/LKG/记录/收据；库根 `current` 符号链接作固定入口（rename 原子换指针）；tree hash 按 spec FR-PUB-008 新写；批次白名单四字段显式判定；验收纯离线（不调 LLM）。
- **不动什么**：digest 现有 argparse、semantic_*.py、full_release.py、publisher.py、lock.py（仅 import 复用）、K1/K2 全部测试。
- **怎么证**：pytest RED/GREEN 成对；六阶段 21 对 RED/GREEN + 1 聚合卡；负例注入覆盖四类；区分度三类样本。

## Technical Context

### Global Constraints

- Python src-layout（`src/knowledge_digest/`）；`uv run --frozen pytest tests/ -q` 为唯一权威测试命令；无 conftest、无 pytest 配置（house 惯例）。
- 本卡全部行为**离线**：发布/验收零 provider 调用（NG-011）；K1/K2 编译不在本卡执行（verify-code 才真跑 89 份）。
- macOS POSIX 文件语义（fcntl.flock、rename 原子、符号链接可用）。
- 现有测试 49 个文件零回归；新测试文件自含 sys.path 插入（仿 `test_task8_entry_navigation.py:16-19`）。

## Code Anchors

### Reuse → Extend → New

| 需求 | 决定 | 理由（F10） |
| --- | --- | --- |
| 库级锁 | **Reuse**：`lock.py` `kb_lock`（fcntl LOCK_EX，`:13-35`） | 语义已合；K3 用法是锁目标库**父目录**（先例 `full_release.py:1172-1174`、`reader_quality.py:1825`），不改动 lock.py |
| 批次 manifest 读取 | **New**：`kb_publish.py` 自写白名单读取 | `semantic_nav_check.load_and_validate`（`:620-625`）是 K2 的严格校验，语义不同；import 其内部函数会跨边界耦合 |
| tree hash | **New**：按 FR-PUB-008 冻结算法新写 | `full_release._tree_hash`（`:122-129`）是流式单 sha256、Path 排序、无排除——与冻结算法不符且含 bundle 语义（取证 #7） |
| 新库骨架 | **Reuse**：`kb_structure.default_publication_structure()`（`:395-414`） | spec FR-PUB-003 点名；旧 `initialize_default_publication` 只写 2 文件，K3 首发布后由批次覆盖 Home.md，骨架仅提供结构声明 |
| 批次 fixture | **Extend**：仿 `tests/fixtures/task8_nav/__init__.py:77 make_batch` 新造 `task9_publish` fixture | 需要带 `navigation=generated_ok` 键与可控 blockers/pages 的 K1 形批次 |
| 造运行记录 | **Reuse**：K1 `_audit/run-metrics.json` 字段名（elapsed_ms/provider_calls/provider_tokens/reasons，`semantic_audit.py:697-742`） | FR-COST-002 承接需要同名字段 |

### 关键既有事实（build-plan 取证，step 2）

1. `digest` 入口 = `simple_cli:main` → 委托 `semantic_cli.main`（`pyproject.toml:12-14`、`simple_cli.py:31-59`）；semantic_cli 是**无子命令**单 argparse（`semantic_cli.py:79-122`）→ 新入口只能走**新脚本**，挂不进去也不该挂。
2. manifest 字段与写盘顺序：`semantic_audit.py:768-812`（schema v1）、`:986-1011`（原子最后替换）。
3. K2 写回 navigation：`semantic_navigation.py:139-145`。
4. `kb_lock` 无陈旧处理（进程释放即清，残留无害）→ 崩溃恢复靠 receipt/tree-hash 对账，不靠锁（取证未知项 d）。
5. `default_publication_structure()` 返回 roots=[pages,_archive,_queues] 旧分类；**K3 托管路径集 = 骨架声明 ∪ 本批 manifest 页面集**（见 DEC-K3-002），不逐字套用旧 roots。
6. 测试范式两套：`task8_nav.make_batch`（文件级fixture）与 `task7_e2e`（假 provider）；K3 用前者。

## Solution Design

### Overview

```
批次目录(K1/K2)          目标知识库目录                sidecar(<KB>.kd/)
 ├ _audit/page-manifest ──► kb_publish: publish ──► KB/current ──symlink──► versions/<vid>/
 └ _audit/run-metrics  ──►  (白名单/合并/LKG/入口)        (固定入口,rename原子换)   staging/<run>/
                                                          未托管用户文件原样保留        lkg/<vid>/ + pointer.json
                                                                                    releases/<vid>.json  receipts/<run>.json
freeze/ ──► kb_accept: accept ──► 逐题四结果+verdict        ledger.jsonl
 (三份冻结物+题集)             (preflight/判定/绑定)
```

### Module responsibilities

- **`kb_publish.py`**（目标 ≤600 行，超出拆 `kb_publish_io.py`）：白名单读取、合并构造（staging）、tree hash（FR-PUB-008）、sidecar 布局、LKG/指针/入口原子换版、no-op、失败收据、回滚、缺陷台账。`publish()` / `rollback()` 两个公开入口 + 纯函数层（可测）。
- **`kb_accept.py`**（目标 ≤500 行）：冻结齐备 preflight、问题集生成器（纯函数）、四结果判定器（纯函数）、汇总阈值、判定记录绑定/重放、区分度检查。`accept()` 公开入口。
- **CLI 薄壳**：三个 `__main__` 风格入口函数放各自模块（`main(argv)`），pyproject 注册脚本；只解析参数、调入口、打印机器 JSON、返回退出码。
- 复用边界：只用 `kb_lock`（lock.py）、`default_publication_structure`（kb_structure.py）、json/pathlib 标准库；**不 import** semantic_* 模块。

### Interfaces, data, and lifecycle

- **publish 入口**：输入=批次目录路径 + 目标 KB 路径 + 可选 `cancel` 回调；输出=release 记录 JSON（stdout）+ 退出码。副作用仅限 sidecar + KB 根 `current` 链接。CLI 把 SIGINT 转 cancel 标志（协作式取消，完成恢复后非零退出，FR-NEG-002 范围）。
- **accept 入口**：双模式——`--freeze`：输入=三份冻结源（89 份清单源/改造前产物目录/对照库目录）+ 输出 freeze 目录与 frozen_id（FR-FRZ-001…003 的可执行形态，红队 blocking-2 处置；三入口冻结不变）；默认模式：输入=frozen_id + 目标 KB 路径，输出=verdict JSON。锁内读树指纹；对照只读冻结快照。
- **version_id 格式**：`<UTC yyyyMMdd-HHMMSS>-<seq:03d>`（seq=sidecar 内当日序号扫描确定，仿 K1 批次命名）。
- **入口链接格式**：`current` 为**相对**符号链接，目标 `../.<KB名>.kd/versions/<version_id>`（相对目标保证 KB 目录整体移动后仍可用；Obsidian 跟随相对软链为本方案成立前提，T019R 以真实链接断言覆盖）。
- **运行记录（run record）**：字段 `{run_id, command, target_kb_tree_hash, batch_attempt_id, elapsed_ms, provider_calls, provider_tokens, compile:{elapsed_ms,provider_calls,provider_tokens,inherited_from_compile:true}, reasons, reason_code?, exit_code}`；收据=失败时的同 schema + `receipt:true`。

## File Boundary

### NEW

- `src/knowledge_digest/kb_publish.py`（发布通道全职责）
- `src/knowledge_digest/kb_accept.py`（验收判定器）
- `tests/acceptance/test_task9_publish.py`
- `tests/acceptance/test_task9_accept.py`
- `tests/fixtures/task9_publish/__init__.py`（make_batch_with_nav/make_kb/freeze 构造器）

### MODIFY

- `pyproject.toml`：+3 个脚本入口（`knowledge-digest-publish/-rollback/-accept`）。仅此一行区块。

### DO NOT TOUCH

- `semantic_cli.py` / `simple_cli.py` / `cli.py`（digest 入口零改动）
- `semantic_*.py`（K1/K2 全部）、`full_release.py`、`publisher.py`、`lock.py`、`kb_structure.py`（仅 import）
- 既有全部测试文件、`tests/fixtures/task7_e2e|task8_nav`（只读复用）
- `CONTEXT.md`、docs/、CompanyBrain、gbrain、真实语料目录

## Technical Decisions

### DEC-K3-001 — 新脚本入口，digest argparse 零接触

新增 `knowledge-digest-publish/-rollback/-accept` 三个 top-level 脚本，各自 `模块:main`。digest 现有单 argparse 无子命令模式，且 K1 的 FR-CLI-001 限制 digest 不新增子命令；独立脚本同时满足"DO NOT TOUCH digest"与"三入口"。备选（digest 加子命令/复用 semantic_cli 参数）被否：触碰 DO NOT TOUCH 边界。

### DEC-K3-002 — 判定只对照 kb.structure.md；本批 manifest 页面集先登记进声明

spec FR-PUB-002 的判定权威单一：目标库 `kb.structure.md` 声明的托管路径。实现顺序：发布前把本批 manifest 的页面集与库级结构页（Home.md/Index.md/navigation/）**append-only 登记**进 `kb.structure.md` 的 managed 列表（登记动作本身写声明文件，声明文件本就属于 KD 可写面），随后越界写入/路径碰撞判定**只对照声明**。空库首发布：写默认骨架（提供初始声明），再登记本批页面集。旧骨架 roots（pages/_archive/_queues）与语义层 products/ 布局不冲突：products/ 经登记成为声明路径。spec 口径零变更（红队 blocking-1 按此收窄处置）。

### DEC-K3-003 — 库根固定入口 = `current` 符号链接，rename 原子换指针

符号链接方案：新版本目录在 sidecar/versions 落盘后，创建临时链接 `current.tmp` 再 `os.replace` 成 `current`——POSIX 下 rename 原子，读者无缺失窗口（detail D1=A 的落法）。版本目录含完整 KB 内容（托管+未托管文件快照），回滚=整目录换回，未托管文件随之回到旧态（与"读者只见完整新旧版本"一致）。拒选：真实目录 rename 换（有缺失窗口，红队 N-1 已否决）；入口放 sidecar（读者不可见，失去固定入口意义）。保留名冲突（库根已存在名为 `current` 的文件）→ 首发布 blocked。

### DEC-K3-004 — tree hash 新写，按 FR-PUB-008 逐字节实现

`kb_tree_hash(root)`：rglob 常规文件→相对 posix 路径字典序（UTF-8）→逐文件 sha256→`path:hash\n` 拼接→整体 sha256；符号链接/缺失文件→ValidationError。与 `full_release._tree_hash` 并存不混用（旧算法服务旧路径，K4 处置）。

### DEC-K3-005 — sidecar 布局与命名冻结

`<KB父目录>/.<KB名>.kd/`：`versions/<version_id>/`、`staging/<run_id>/`（finally 清理，崩溃残留由下次发布检测清理）、`lkg/<version_id>/`+`lkg/pointer.json`、`releases/<version_id>.json`、`receipts/<run_id>.json`、`ledger.jsonl`、`freeze/<frozen_id>/`（验收侧）。全部属于"允许写位置清单"；KB 根仅 `current` 链接可写。命名改动=plan 级变更，不回 spec。

### DEC-K3-006 — 验收判定器纯函数分层

`generate_questions(manifest_pages, module_rule)` / `judge(question, kb_pages, frozen_sources)` / `summarize(results)` 三层纯函数，stdin 可复算；`accept()` 只负责 IO（锁、preflight、读文件、写记录）。判定口径版本字段 `judge_rules_version`（默认 `k3-v1`）绑定进记录。

### DEC-K3-007 — 测试全离线；fixture 新造 task9_publish

发布/验收测试用文件级 fixture（task8_nav 范式扩展）：三页批次 + 可控 navigation/blockers + 假 run-metrics；负例注入用 monkeypatch 边界点（copy 中途抛错/指针写入失败/取消检查点）。不造 provider。

### DEC-K3-008 — 回滚即发布：同一套"备份当前→换版→轮换"

rollback() 复用 publish 的内部管线：把"当前版本"存入 lkg（被换下者成新 LKG），指针与入口随换版更新——保证任意次回滚后状态机一致（红队 N-5 落地）。

## Test Strategy

- **路由判类**（test-routing-advisor 输出合同）：`routing_tier=feature`——Python 模块级单功能域（发布+验收两模块），目标单测+邻接集成（fixture 端到端）；无跨端/并发/数据库变更；changed_files=2 生产模块+3 测试/fixture 文件；phase_count=6 同功能域不升级。
- **三层**：① 纯函数单测（tree hash/合并/阈值/生成器）；② 模块集成（fixture 批次→发布→验收端到端）；③ 负例注入（monkeypatch 边界）。全部 `tests/acceptance/test_task9_*.py`。
- **RED/GREEN**：每行为对同一 `gate_cmd`（`uv run --frozen pytest tests/acceptance/test_task9_publish.py -q -k <id>` / `_accept` 同构）；RED expected_exit 非零，GREEN 修到 0。
- **oracle 身份**：tree hash 值、verdict JSON、发布记录字段、 receipts 存在性+字段——全部机器可比对；区分度检查自带样本期望。
- **覆盖限制**：不测试 lock.py 本身、不测 K1/K2 行为、不测真实 provider；崩溃级一致性不测（FR-NEG-002）。

## Rollback and Recovery

- 计划级：本卡只新增文件+pyproject 三行；回滚=删除新文件+还原 pyproject（git 层面）。
- 产品级（本卡交付的能力）：回滚命令 restore 上一版本；失败收据+tree hash 对账支持人工恢复（锁不提供陈旧保证，DEC 见 Code Anchors #4）。

## Implementation Order

P1 基础（tree hash/锁/sidecar 布局/白名单读取/fixture）→ P2 发布（合并/LKG/入口/no-op/碰撞/收据/回滚）→ P3 成本（run record+承接）→ P4 冻结（freeze/preflight）→ P5 验收（生成/判定/汇总/绑定/区分度）→ P6 负例与聚合（注入/台账/E2E）。P3 可与 P2 后半并行（文件不相交）；P4/P5 顺序依赖（preflight 先于判定）。

## Dependencies and Parallelism

- 外部：无 provider 依赖；pytest 已有。
- 内部并行：P3（成本记录）∥ P2 后半（LKG/回滚）——kb_publish.py 内顺序执行但卡片可并行编写；P5 内部生成器∥判定器。
- 顺序硬依赖：P1→P2→P4→P5→P6；P3 在 P2 的收据卡之后收口。

## Requirement and Verification Traceability

| 决策/FR | AC | 任务卡（tasks.md） | oracle |
| --- | --- | --- | --- |
| DEC-K3-001/FR-CLI-001 三入口 | — | T001R/G | 脚本可执行+JSON 输出 |
| FR-PUB-008/DEC-K3-004 tree hash | AC-K3-1/3 | T002R/G | 手算期望值逐字节一致 |
| D-011/FR-PUB-001 白名单 | AC-K3-1 | T003R/G | blocked+reason 唯一对 |
| D-010 不复用旧发布路径 | AC-K3-1 | T007R/G（主流程自写） | 代码审查+行为绿 |
| D-004/D-002/FR-PUB-002 合并（含 FR-STA-001 逐字节） | AC-K3-1/3 | T005R/G、T006R/G | staging 树+字节相等 |
| FR-PUB-003 骨架 | AC-K3-5 | T006R/G | 骨架文件集+sha256 登记 |
| D-002/D-001/FR-PUB-004/005 入口/LKG | AC-K3-1 | T007R/G、T010R/G（回滚） | 入口解析 hash 链 |
| FR-PUB-006 no-op | AC-K3-1 | T008R/G | no_op=true+指针不变 |
| FR-PUB-007/FR-COST-001/003 收据与成本 | AC-K3-2 | T009R/G、T011R/G（F-002 实物对照在 verify-code 阶段引用） | 三项非 null+承接字段 |
| FR-FRZ-001…005 冻结/preflight | AC-K3-5 | T012R/G（accept --freeze）、T013R/G | frozen_id 复算+只读断言 |
| FR-ACC-001 独立验收命令 | AC-K3-3 | T017R/G（accept 编排） | verdict JSON 落盘可重读 |
| FR-ACC-002 题集生成 | AC-K3-3 | T014R/G | 同输入同 sha256 |
| FR-ACC-003/004 判定与汇总（含 FR-STA-001 分母口径） | AC-K3-3 | T015R/G、T016R/G | verdict 唯一解 |
| FR-ACC-005/008/006 绑定/preflight/取锁互斥 | AC-K3-3 | T013R/G、T017R/G（并发取锁断言） | 指纹不符拒判+持锁不读中间态 |
| FR-ACC-007 区分度 | AC-K3-4 | T018R/G | 三类绑定题全红/正确产物全绿 |
| FR-NEG-001/002 负例 | AC-K3-1 | T019R/G（四类注入） | 整根等价/零字节差分 |
| FR-LED-001 台账 | AC-K3-2/3 | T020R/G（依赖 T017 void 机制） | 台账字段+void 语义 |
| D-001/D-003/D-007/D-013 全链 | AC-K3-1…5 | T021R/G（聚合，source_refs 显式全列） | 全链 JSON 可解析 |

## 阶段执行记录（build-plan）

- step 1 read-current-materials：decision-log（approved）+ spec（frozen）通读；提取 29 FR/5 AC/11 NG。
- step 2 conditional-spec-research：**执行**——8 条实现锚点取证（CLI 接线/落盘/锁/骨架/测试/tree hash/manifest 读取），结论入 Code Anchors；无 unknown 阻塞。
- step 3 testing-system-blueprint：Test Strategy 节（三层/RED-GREEN/oracle/覆盖限制）。
- step 4 spec-plan：本文。
- step 5/6 simplicity-guard / plan-eng-review：主会话内检——复用优先（锁/骨架/字段名全复用）、新写仅限 tree hash 与两模块；无双重方案。
- step 7 test-routing-advisor：routing_tier=feature（输出合同见 Test Strategy）。
- step 8 spec-tasks：tasks.md（26 对 RED/GREEN + 聚合卡）。
- step 9 review-plan / step 10 处置：见 tasks.md 末尾审查记录（红/蓝独立子代理）。
- step 11 final-spec-analyze：主会话一致性复算（traceability 卡号与 tasks 逐卡核对、FR 全覆盖、依赖链无死锁）通过。
- step 12 publish-plan-result：用户已确认（2026-09-15，回复"确认，继续…"）；human-confirmation.v3 落盘 `quality/confirmations/ae2498d23756…json`（build-plan，revision-977ef314…）；同回复以 append-only 人工对齐事实记入 tasks.md 执行状态区。官方 stage outcome 依赖宿主 bridge → `unavailable（executor_absent）`，不伪装。
- step 13 stage-reflection：公共入口要求 executor source/timing/output hash，本会话无 bridge → `unavailable`；复盘要点：两轮审查均抓出 traceability 断链与口径漂移，修复后复算通过；取证一次到位（8 锚点全绿）。
